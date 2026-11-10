"""
MotoQuant — Build Optimizer
===========================
Product-facing parts-build optimizer (Track B).

Given a bike + budget (₹) + goal, return the best parts combination with
per-part ROI and the predicted ET / trap delta.

Scoring (October 2026):
  * Rust core active (``engine_select.native_active()``) — every candidate is
    scored with the full physics sim (exact, ~5 ms/sim) and any surrogate is
    ignored; ``scoring_stats["surrogate_skipped"]`` says so.
  * Python engine only — candidates are scored through the surrogate when one
    is loaded and the config sits inside its training envelope AND carries no
    change the 26 features cannot see (feature-blind / boosted configs are
    full-simmed); the selected parts are then re-verified with full sims.
  * Either way the REPORTED build (optimized ET/trap, delta, cost-per-tenth)
    is a full physics sim of the exact part list, applied in
    ``applied_part_ids`` order (NA parts before boost), after a joint gearing
    re-choice and a drop-one pass (``roi.refine_build``).

Consolidation (not reinvention)
-------------------------------
  * ``roi.compute_parts_roi``  — per-part ROI (extended here with an injectable
    ``et_fn`` scorer so scoring can go through the surrogate).
  * ``roi.rank_categories``    — category priority.
  * ``recommendations``        — profile filtering, synergy detection,
    compatibility warnings, next-upgrade suggestion, ``EXCLUSIVE_GROUPS``.
  * ``PartsRepository.search(bike_model_id=...)`` — compatibility filtering, so
    the optimizer never proposes an incompatible part.

The selection step is a *multiple-choice* 0/1 knapsack (MCKP): the plain
``roi.find_best_build`` knapsack can stack two exhausts / four air-filters,
which is not a buildable combination.  MCKP enforces "at most one part per
exclusive category" while still maximising the chosen objective under budget.

Public API
----------
    predictor = make_predictor(surrogate, source)          # surrogate-agnostic scorer
    result    = optimize_build(config, budget, parts_repo, goal="min_et", ...)
    result.to_dict()                                       # JSON-ready for the API
"""

from __future__ import annotations

import logging
import time
import warnings
from dataclasses import asdict, dataclass, field

import numpy as np

from .. import engine_select
from ..models import BikeConfig
from .recommendations import (
    EXCLUSIVE_GROUPS,
    BuildProfile,
    NextUpgrade,
    _detect_synergies,
    _detect_warnings,
    _filter_parts_by_profile,
    _find_next_upgrade,
)
from .roi import (
    CANDIDATE_LIMIT,
    PartROIResult,
    _grouped_knapsack,
    _knapsack_group_key,
    _objective_gain,
    _run_et,
    apply_order_ids,
    compute_parts_roi,
    noise_floored_metrics,
    part_slots,
    passes_noise_floor,
    rank_categories,
    refine_build,
    score_build,
)

__all__ = [
    "SurrogatePredictor",
    "make_predictor",
    "OptimizedPart",
    "OptimizedBuild",
    "optimize_build",
    "VALID_GOALS",
]

VALID_GOALS = ("min_et", "max_trap")

# Trap speeds for a quarter-mile bike are well under 120 m/s (≈432 km/h); a
# predicted trap above this must be in km/h, so we normalise back to m/s to
# keep the (et_s, trap_ms) contract identical to roi._run_et.
_TRAP_MS_CEILING = 120.0

# Flatten the project's exclusive-category taxonomy once.
_EXCLUSIVE_CATEGORIES = set().union(*EXCLUSIVE_GROUPS) if EXCLUSIVE_GROUPS else set()


# ─────────────────────────────────────────────────────────────────────────
# Surrogate-agnostic scorer
# ─────────────────────────────────────────────────────────────────────────
def _check_envelope(fvec, surrogate=None) -> tuple[bool, list[str]]:
    """Mirror api._check_envelope.

    A v2 surrogate embeds its own per-feature training envelope (min/max over
    the catalog-wide training set) — prefer that, checking EVERY feature the
    model knows. Models without one (v1 numpy artifact, XGB/DNN pickles) fall
    back to the static FEATURE_BOUNDS table over the 14 base features.
    """
    try:
        from .surrogate_data import FEATURE_BOUNDS, FEATURE_NAMES

        env = getattr(surrogate, "envelope", None)
        if env is not None:
            env_min, env_max = env
            names = getattr(surrogate, "feature_names", FEATURE_NAMES)
            violations = [
                str(names[i])
                for i in range(min(len(fvec), len(env_min)))
                if not (env_min[i] <= float(fvec[i]) <= env_max[i])
            ]
            return len(violations) == 0, violations

        violations: list[str] = []
        for i, name in enumerate(FEATURE_NAMES):
            if name not in FEATURE_BOUNDS:
                continue
            lo, hi = FEATURE_BOUNDS[name]
            if float(fvec[i]) < lo or float(fvec[i]) > hi:
                violations.append(name)
        return len(violations) == 0, violations
    except Exception:
        # Fail SAFE: if the envelope check itself breaks, claim OUT of
        # envelope so scoring falls back to the full physics sim instead of
        # silently trusting the surrogate outside its training data.
        logging.getLogger(__name__).warning(
            "surrogate envelope check unavailable — falling back to full sim",
            exc_info=True,
        )
        return False, ["envelope_check_failed"]


def _blind_relevant_signature(config) -> tuple:
    """Hashable snapshot of every ET-relevant config field the 26-feature
    vector CANNOT see.

    Parts that only touch these (quickshifters, clutch kits, nitrous/boost,
    swingarm extensions, wheelie bars, launch electronics, mid-stack gearset
    swaps, dyno-curve reshapes...) leave the feature vector bit-identical to
    stock, so the surrogate would score them as exactly zero gain. Comparing
    this signature against the baseline's lets the predictor full-sim only
    the feature-blind candidates that can actually move the ET — pure-null
    parts (brake pads, fork springs, chain links, bodywork) keep the cheap
    surrogate zero.
    """
    import dataclasses as _dc

    dt = config.drivetrain
    ch = config.chassis
    eng = config.engine
    curve = eng.dyno_curve
    return (
        _dc.astuple(config.clutch),
        _dc.astuple(config.forced_induction),
        _dc.astuple(config.wheelie) if hasattr(config, "wheelie") else (),
        _dc.astuple(config.staging),
        dt.quickshifter,
        dt.air_shifter,
        dt.total_shift_time_ms,
        dt.shift_cut_duration_ms,
        dt.post_shift_retard_ms,
        dt.chain_efficiency,
        dt.primary_efficiency,
        dt.trans_efficiency_per_mesh,
        dt.shaft_efficiency,
        tuple(
            dt.gear_ratios or ()
        ),  # mid-stack ratio swaps don't move g1/gtop features
        ch.swingarm_extension_mm if hasattr(ch, "swingarm_extension_mm") else None,
        getattr(ch, "cog_height_mm", None),
        getattr(ch, "wheelbase_mm", None),
        getattr(eng, "engine_inertia_kgm2", None),
        # dyno-curve SHAPE (a reshape at constant peaks is feature-invisible).
        # Normalised by the curve's peak so a uniform scale — what every NA
        # power part does, and what the peak-torque/power features already
        # see — is NOT a blind change; only a genuine reshape is.
        _curve_shape(curve),
    )


def _curve_shape(curve) -> tuple | None:
    """Peak-normalised torque-curve shape (None without a curve)."""
    if curve is None:
        return None
    torque = np.asarray(curve.torque_nm, dtype=float)
    peak = float(np.max(np.abs(torque))) if torque.size else 0.0
    if peak <= 0.0:
        return tuple(np.round(torque, 6).tolist())
    return tuple(np.round(torque / peak, 6).tolist())


class SurrogatePredictor:
    """
    Callable scorer mapping ``BikeConfig -> (et_s, trap_ms)``.

    Uses ``surrogate`` when supplied and the config is within the training
    envelope; otherwise falls back to the full physics sim (``roi._run_et``).
    Records how many calls took each path so callers can report the effective
    scoring method.
    """

    def __init__(
        self, surrogate=None, source: str = "full_sim", *, allow_fallback: bool = True
    ):
        self.surrogate = surrogate
        self.source = source if surrogate is not None else "full_sim"
        self.allow_fallback = allow_fallback
        self.n_surrogate = 0
        self.n_fallback = 0
        self.n_out_of_envelope = 0
        self.n_feature_blind = 0
        # Feature vector + blind-signature of the FIRST scored config
        # (optimize_build / ROI scorers always evaluate the stock baseline
        # first). Any later config whose blind-signature moved carries an
        # ET-relevant change the surrogate cannot see (quickshifter, clutch,
        # nitrous, swingarm, a reshaped curve...) — whether or not its visible
        # features also moved — and is full-simmed instead of being scored as
        # if the blind change did not exist. Configs whose blind-signature is
        # unchanged (mass, power scaling, gearing, brake pads...) stay on the
        # surrogate.
        self._ref_fvec = None
        self._ref_sig = None
        # True-frame anchor: the first scored config (the stock baseline) is
        # ALSO full-simmed once, and every surrogate prediction afterwards is
        # shifted by (sim_base - surr_base). Per-part deltas keep the smooth
        # surrogate differences, while every reported ET lives in the real
        # physics frame (the surrogate's absolute offset on this bike cancels).
        self._anchor_offset = None  # (et_shift_s, trap_shift_ms)
        self.n_anchor_sims = 0
        # Feature-blind fallback results keyed by blind-signature: a dozen
        # quickshifter SKUs that all set the same shift time produce the SAME
        # config as far as the sim cares — one sim covers them all.
        self._blind_cache: dict = {}
        self.on_predict = None  # optional progress hook (jobs API)

    def __call__(self, config: BikeConfig) -> tuple[float, float]:
        out = self._predict(config)
        if self.on_predict is not None:
            try:
                self.on_predict()
            except Exception:  # progress reporting must never break scoring
                pass
        return out

    def _predict(self, config: BikeConfig) -> tuple[float, float]:
        if self.surrogate is None:
            self.n_fallback += 1
            return _run_et(config)
        try:
            from .surrogate_data import config_to_feature_vector

            fvec = config_to_feature_vector(config)
            first_call = self._ref_fvec is None
            if first_call:
                self._ref_fvec = fvec.copy()
                self._ref_sig = _blind_relevant_signature(config)
            elif self.allow_fallback:
                # ANY config whose feature-invisible fields moved is full-
                # simmed — not only configs whose feature vector is bit-
                # identical to stock. A model-specific quickshifter changes
                # the shift time (blind) AND adds 0.15 kg (visible); the old
                # bit-identical gate sent it to the surrogate, which scored a
                # real -0.05 s part as +0.001 s, so it was never selected
                # (October 2026 audit: 39 such parts).
                sig = _blind_relevant_signature(config)
                if sig != self._ref_sig:
                    self.n_feature_blind += 1
                    try:
                        key = (sig, fvec.tobytes())
                        cached = self._blind_cache.get(key)
                    except TypeError:  # unhashable corner — just sim it
                        cached = None
                        key = None
                    if cached is not None:
                        return cached
                    self.n_fallback += 1
                    out = _run_et(config)
                    if key is not None:
                        self._blind_cache[key] = out
                    return out
            ok, _violations = _check_envelope(fvec, self.surrogate)
            # Forced induction is INVISIBLE to the feature vector: boost/nitrous
            # parts flip forced_induction.* via param_overrides without moving a
            # single feature, so the surrogate would confidently return the
            # naturally-aspirated ET (the June-2026 Hayabusa proof run scored a
            # 60 HP nitrous kit at ~0.0s gain this way). Boosted configs must
            # always be scored by the full physics sim.
            if getattr(getattr(config, "forced_induction", None), "is_boosted", False):
                ok = False
                _violations = ["forced_induction_active"]
            if not ok and self.allow_fallback:
                self.n_out_of_envelope += 1
                self.n_fallback += 1
                return _run_et(config)

            et_arr, trap_arr = self.surrogate.predict(fvec.reshape(1, -1))
            et = float(et_arr[0]) if hasattr(et_arr, "__len__") else float(et_arr)
            trap = (
                float(trap_arr[0]) if hasattr(trap_arr, "__len__") else float(trap_arr)
            )
            if trap > _TRAP_MS_CEILING:  # model returned km/h — normalise to m/s
                trap /= 3.6
            self.n_surrogate += 1
            if first_call and self.allow_fallback:
                true_et, true_trap = _run_et(config)
                self.n_anchor_sims += 1
                self._anchor_offset = (true_et - et, true_trap - trap)
                return true_et, true_trap
            if self._anchor_offset is not None:
                et += self._anchor_offset[0]
                trap += self._anchor_offset[1]
            return et, trap
        except Exception as exc:  # pragma: no cover (needs a loaded surrogate)
            if not self.allow_fallback:
                raise
            warnings.warn(
                f"build_optimizer: surrogate scoring failed ({exc}); using full sim"
            )
            self.n_fallback += 1
            return _run_et(config)

    @property
    def method(self) -> str:
        if self.surrogate is None:
            return "full_sim"
        if self.n_surrogate and self.n_fallback:
            return f"surrogate({self.source})+fallback"
        if self.n_surrogate:
            return f"surrogate({self.source})"
        return "full_sim"

    def stats(self) -> dict:
        return {
            "method": self.method,
            "source": self.source,
            "surrogate_calls": self.n_surrogate,
            "fallback_calls": self.n_fallback,
            "out_of_envelope": self.n_out_of_envelope,
            "feature_blind": self.n_feature_blind,
            "anchor_sims": self.n_anchor_sims,
        }


def make_predictor(
    surrogate=None, source: str = "full_sim", *, allow_fallback: bool = True
) -> SurrogatePredictor:
    """Build a surrogate-agnostic ``BikeConfig -> (et_s, trap_ms)`` scorer."""
    return SurrogatePredictor(surrogate, source, allow_fallback=allow_fallback)


# ─────────────────────────────────────────────────────────────────────────
# Result types
# ─────────────────────────────────────────────────────────────────────────
def _round_or_none(x, nd):
    if x is None or x == float("inf"):
        return None
    return round(x, nd)


@dataclass
class OptimizedPart:
    part_id: int
    name: str
    brand: str
    category: str
    category_display: str
    price_inr: float
    # ET CHANGE vs base (after - before): NEGATIVE = faster. Unified July 6,
    # 2026 — this field used to carry the internal ROI gain (positive =
    # faster), the opposite sign of /api/simulate/quick's et_delta_s, and
    # the web UI rendered improvements as "+0.134s". Every public delta_et_s
    # now reads as a time change; internal ROI/knapsack math still uses
    # positive-gain semantics (PartROIResult is untouched).
    delta_et_s: float
    delta_trap_ms: float  # trap change (after - before, m/s): positive = faster
    roi_score: float | None
    cost_per_tenth_inr: float | None
    is_compatible: bool

    @classmethod
    def from_roi(cls, r: PartROIResult, *, is_compatible: bool = True) -> OptimizedPart:
        return cls(
            part_id=r.part_id,
            name=r.part_name,
            brand=r.brand,
            category=r.category,
            category_display=r.category_display,
            price_inr=round(r.price_inr, 2),
            # PartROIResult.delta_et_s is a positive-good GAIN (scoring
            # convention); negate to the public after-minus-before delta.
            delta_et_s=round(-r.delta_et_s, 4) + 0.0,  # +0.0 normalizes -0.0
            delta_trap_ms=round(r.delta_trap_ms, 4),
            roi_score=_round_or_none(r.roi_score, 4),
            cost_per_tenth_inr=_round_or_none(r.cost_per_tenth_inr, 2),
            is_compatible=is_compatible,
        )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class OptimizedBuild:
    bike_name: str
    goal: str
    budget_inr: float
    profile: str
    base_et_s: float
    base_trap_kmh: float
    optimized_et_s: float
    optimized_trap_kmh: float
    delta_et_s: float  # optimized - base: NEGATIVE = faster (July 6, 2026)
    delta_trap_kmh: float  # optimized - base: positive = faster
    total_cost_inr: float
    budget_used_pct: float
    cost_per_tenth_inr: float | None
    parts: list = field(default_factory=list)  # list[OptimizedPart]
    synergies: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    next_upgrade: dict | None = None
    category_priority: list = field(default_factory=list)
    parts_evaluated: int = 0
    parts_skipped_incompatible: int = 0
    parts_skipped_no_gain: int = 0
    scoring_method: str = "full_sim"
    scoring_stats: dict = field(default_factory=dict)
    # Part ids in the order they were APPLIED to build the verified bike (NA
    # parts first, then boost — roi._apply_order). Consumers that rebuild the
    # bike (the outlaw pipeline) must apply in this order, not display order.
    applied_part_ids: list = field(default_factory=list)

    def summary(self) -> str:
        verb = "ET" if self.goal == "min_et" else "trap"
        lines = [
            f"{self.bike_name} — optimize for {verb} @ ₹{self.budget_inr:,.0f} ({self.profile})",
            f"  base   {self.base_et_s:.3f}s / {self.base_trap_kmh:.1f} km/h",
            f"  tuned  {self.optimized_et_s:.3f}s / {self.optimized_trap_kmh:.1f} km/h  "
            f"(Δ {self.delta_et_s:+.3f}s, {self.delta_trap_kmh:+.1f} km/h)",
            f"  spend  ₹{self.total_cost_inr:,.0f} of ₹{self.budget_inr:,.0f} "
            f"({self.budget_used_pct:.0f}%), {len(self.parts)} parts  [{self.scoring_method}]",
        ]
        for p in self.parts:
            lines.append(
                f"    • {p.name} (₹{p.price_inr:,.0f}, Δ {p.delta_et_s:+.3f}s)"
            )
        return "\n".join(lines)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["parts"] = [p if isinstance(p, dict) else p.to_dict() for p in self.parts]
        return d


# ─────────────────────────────────────────────────────────────────────────
# Selection (multiple-choice 0/1 knapsack — at most one part per exclusive category)
# ─────────────────────────────────────────────────────────────────────────
def _select_build(
    individual: list[PartROIResult],
    budget_inr: float,
    goal: str,
    *,
    allow_negative: bool = False,
    position_of: dict[int, str] | None = None,
    slot_of: dict[int, str] | None = None,
    min_delta_et_ms: float = 5.0,
) -> list[PartROIResult]:
    """
    Pick the affordable subset maximising the goal metric, with at most one
    part from each exclusive category (see roi.EXCLUSIVE_CATEGORIES), at most
    one sprocket per position when ``position_of`` maps part_id ->
    'front'/'rear', and at most one part per physical slot when ``slot_of``
    maps part_id -> a slot key (roi.part_slot: 'brakes:pad:front',
    'suspension:fork', 'fuel_system:injector', 'bodywork:fairing', ...).
    Complementary slots (front + rear pads, fork + shock) stay independently
    selectable. Free parts (price 0) cost no budget. Parts whose gain is below
    the ``min_delta_et_ms`` noise floor (thousandths of the objective unit)
    are never bought.
    Delegates to roi._grouped_knapsack, which rounds bucket weights UP so the
    selected build can never exceed the stated budget (the old floor division
    let every part under-weigh by up to ₹99 — sub-₹100 parts were free).
    """
    gain = _objective_gain(goal)

    candidates = [
        r
        for r in individual
        if (allow_negative or passes_noise_floor(gain(r), min_delta_et_ms))
        and r.price_inr <= budget_inr
    ]
    if not candidates:
        return []

    return _grouped_knapsack(
        candidates,
        budget_inr,
        gain,
        lambda r: _knapsack_group_key(r, position_of, slot_of),
    )


# ─────────────────────────────────────────────────────────────────────────
# Optimizer
# ─────────────────────────────────────────────────────────────────────────
def _coerce_profile(profile) -> BuildProfile:
    if isinstance(profile, BuildProfile):
        return profile
    try:
        return BuildProfile(str(profile).lower())
    except ValueError:
        return BuildProfile.ALL


def _next_upgrade_to_dict(nu: NextUpgrade | None) -> dict | None:
    if nu is None:
        return None
    return {
        "part": OptimizedPart.from_roi(nu.part).to_dict(),
        "marginal_et_gain_s": round(nu.marginal_et_gain_s, 4),
        "marginal_cost_inr": round(nu.marginal_cost_inr, 2),
        "marginal_roi": _round_or_none(nu.marginal_roi, 4),
        "reason": nu.reason,
    }


def _empty_build(
    base_config,
    base_et_s,
    base_trap_ms,
    goal,
    budget_inr,
    profile_value,
    predictor,
    extra_stats=None,
) -> OptimizedBuild:
    kmh = round(base_trap_ms * 3.6, 2)
    return OptimizedBuild(
        bike_name=base_config.name,
        goal=goal,
        budget_inr=float(budget_inr),
        profile=profile_value,
        base_et_s=round(base_et_s, 4),
        base_trap_kmh=kmh,
        optimized_et_s=round(base_et_s, 4),
        optimized_trap_kmh=kmh,
        delta_et_s=0.0,
        delta_trap_kmh=0.0,
        total_cost_inr=0.0,
        budget_used_pct=0.0,
        cost_per_tenth_inr=None,
        scoring_method=predictor.method,
        scoring_stats={**predictor.stats(), **(extra_stats or {})},
    )


def optimize_build(
    base_config: BikeConfig,
    budget_inr: float,
    parts_repo,
    *,
    goal: str = "min_et",
    profile=BuildProfile.ALL,
    bike_model_id: int | None = None,
    surrogate=None,
    surrogate_source: str = "full_sim",
    include_next_upgrade: bool = True,
    max_candidates: int | None = None,
    use_live_pricing: bool = False,
    db_conn=None,
    progress_cb=None,
    full_physics: bool | None = None,
) -> OptimizedBuild:
    """
    Find the best on-budget parts build for ``base_config``.

    goal            "min_et" (maximise ET gain) or "max_trap" (maximise trap gain).
    profile         BuildProfile or its string value (all/street_legal/drag_prep/full_race).
    bike_model_id   DB bike_models.id — drives real compatibility filtering.
    surrogate       Optional loaded surrogate; None -> full-sim scoring (always correct).
    max_candidates  Cap the candidate pool (handy for fast tests / latency bounds).
    full_physics    Score every candidate with the full physics sim and ignore
                    ``surrogate``. ``None`` (default) = automatic: on when the
                    Rust core is active (exact results at ~5 ms/sim make the
                    surrogate pointless), off on the Python-only engine where
                    the surrogate keeps big catalogs tractable.

    Whatever scored the candidates, the reported build (optimized ET/trap,
    delta, cost-per-tenth) always comes from a full physics sim of the exact
    part list, applied in ``applied_part_ids`` order, after a joint gearing
    re-choice and a drop-one pass (roi.refine_build). ``scoring_stats`` says
    which engine ran and whether the surrogate was skipped.
    """
    goal = goal if goal in VALID_GOALS else "min_et"
    profile_enum = _coerce_profile(profile)

    native = engine_select.native_active()
    engine_name = "native" if native else "python"
    if full_physics is None:
        full_physics = native
    extra_stats: dict = {"engine": engine_name, "final_build": "full_sim"}
    if full_physics and surrogate is not None:
        extra_stats["surrogate_skipped"] = (
            f"{engine_name} engine active — every candidate scored with exact physics"
            if native
            else "full physics requested — every candidate scored with exact physics"
        )
        surrogate = None
    predictor = make_predictor(surrogate, surrogate_source)

    n_final_sims = [0]

    def full_et(cfg: BikeConfig) -> tuple[float, float]:
        n_final_sims[0] += 1
        out = _run_et(cfg)
        if not native:
            # The Python engine holds the GIL through these back-to-back
            # verification sims; yield so the /api/jobs status poll can
            # respond on a 0.5-CPU host (the browser declared "connection
            # lost" at 97% otherwise — QC 2026-06-13). The Rust core releases
            # the GIL, so no yield is needed there.
            time.sleep(0.02)
        return out

    # Base run (warm-up + absolute trap so we can report km/h). With a
    # surrogate the predictor's first call is the full-sim anchor, so the
    # baseline is real physics either way.
    base_et_s, base_trap_ms = predictor(base_config)
    if progress_cb is not None:
        progress_cb(0.02, "Baseline run")

    # Compatible, profile-filtered candidate parts (no 200-row cap).
    all_parts = parts_repo.search(bike_model_id=bike_model_id, limit=CANDIDATE_LIMIT)
    filtered = _filter_parts_by_profile(all_parts, profile_enum)
    candidate_ids = [p["id"] for p in filtered]
    if max_candidates is not None:
        candidate_ids = candidate_ids[:max_candidates]
    if progress_cb is not None and candidate_ids:
        # Tick the bar once per scorer call (per-part ROI). Capped below the
        # verification/refinement band — the jobs layer snaps to 100% on
        # completion.
        _total = len(candidate_ids) + 2
        _done = [0]

        def _on_predict():
            _done[0] += 1
            progress_cb(
                min(0.90, 0.02 + 0.88 * _done[0] / _total),
                "Scoring candidate parts",
            )

        predictor.on_predict = _on_predict
    if not candidate_ids:
        return _empty_build(
            base_config,
            base_et_s,
            base_trap_ms,
            goal,
            budget_inr,
            profile_enum.value,
            predictor,
            extra_stats,
        )

    # Per-part ROI through the (surrogate-agnostic) scorer.  Candidates are
    # already compatibility-filtered by search(), so they are all fitment-valid.
    individual = compute_parts_roi(
        base_config=base_config,
        part_ids=candidate_ids,
        parts_repo=parts_repo,
        use_live_pricing=use_live_pricing,
        db_conn=db_conn,
        et_fn=predictor,
    )

    gain = _objective_gain(goal)
    # Physical-slot map (roi.part_slot) so the knapsack holds one front AND one
    # rear sprocket, complementary brake/suspension parts, one part per
    # fuel-system / bodywork slot — never two parts fighting for one slot.
    rows_by_id = {p["id"]: p for p in filtered}
    slot_of = part_slots(rows_by_id[i] for i in candidate_ids if i in rows_by_id)
    position_of = {
        pid: slot.split(":", 1)[1]
        for pid, slot in slot_of.items()
        if slot.startswith("sprocket:")
    }

    def group_key(r: PartROIResult):
        return _knapsack_group_key(r, position_of, slot_of)

    selected = _select_build(
        individual, float(budget_inr), goal, position_of=position_of, slot_of=slot_of
    )

    roi_by_id = {r.part_id: r for r in individual}
    verified: dict[int, tuple[float, float]] = {}
    surrogate_mode = predictor.surrogate is not None and predictor.allow_fallback

    def _verify(pids, lo: float, hi: float, stage: str) -> int:
        """Full-sim each part's individual delta and write it back (with
        ROI metrics recomputed from the verified delta)."""
        n = 0
        total = max(1, len(pids))
        for i, pid in enumerate(pids):
            if progress_cb is not None:
                progress_cb(min(0.99, lo + (hi - lo) * i / total), stage)
            r = roi_by_id.get(pid)
            if r is None or pid in verified:
                continue
            try:
                part_cfg = parts_repo.apply_multiple([pid], base_config)
                part_et, part_trap = full_et(part_cfg)
                d_et, d_trap = base_et_s - part_et, part_trap - base_trap_ms
                n += 1
            except Exception:  # noqa: BLE001 — keep the surrogate score
                d_et, d_trap = r.delta_et_s, r.delta_trap_ms
            verified[pid] = (d_et, d_trap)
            r.delta_et_s = round(d_et, 4)
            r.delta_trap_ms = round(d_trap, 4)
            r.modified_et_s = base_et_s - r.delta_et_s
            # The ROI numbers must follow the verified delta (they used to
            # keep the surrogate's: cost-per-tenth ₹40,780 next to a delta
            # that implied ₹21,065 — October 2026 audit).
            r.roi_score, r.cost_per_tenth_inr = noise_floored_metrics(
                r.price_inr, r.delta_et_s
            )
        return n

    # Surrogate-scored runs: re-verify the SELECTED parts with the full sim
    # and re-select until the pick stabilises (≤3 rounds). Surrogate delta
    # noise on a single part (±0.03-0.10s) is harmless for ranking the bulk
    # of the catalog but can promote a phantom pick into the build or hold a
    # real gain out of it; simming just the winners (10-20 sims) pins every
    # part that actually spends budget to its true physics delta.
    n_verify_sims = 0
    if surrogate_mode and selected:
        for _round in range(3):
            todo = [r.part_id for r in selected if r.part_id not in verified]
            if not todo:
                break
            n_verify_sims += _verify(
                todo, 0.90, 0.95, "Verifying selected parts (full sim)"
            )
            reselected = _select_build(
                individual,
                float(budget_inr),
                goal,
                position_of=position_of,
                slot_of=slot_of,
            )
            if {r.part_id for r in reselected} == {r.part_id for r in selected}:
                selected = reselected
                break
            selected = reselected

    # Combined build — ALWAYS the full physics sim of the exact part list
    # (the surrogate cannot see quickshifters, chains or clutch kits; scoring
    # the combined build through it under-reported a real -0.324 s build as
    # -0.180 s). refine_build re-chooses gearing jointly and drops any part
    # whose removal makes the build faster.
    _ref_done = [0]

    def _on_ref_sim():
        _ref_done[0] += 1
        if progress_cb is not None:
            progress_cb(
                min(0.99, 0.95 + 0.04 * (1.0 - 1.0 / (1.0 + _ref_done[0] / 10.0))),
                "Verifying combined build (full sim)",
            )

    pool = [r for r in individual if r.price_inr <= float(budget_inr)]
    refinement = None
    try:
        refinement = refine_build(
            base_config,
            selected,
            pool,
            float(budget_inr),
            parts_repo,
            full_et,
            objective=goal,
            group_key=group_key,
            on_sim=_on_ref_sim,
        )
        selected = refinement.selected
        combined_et, combined_trap_ms = refinement.et_s, refinement.trap_ms
    except Exception as exc:  # noqa: BLE001 — report stock, never a fiction
        warnings.warn(f"optimize_build: combined sim failed ({exc}); reporting stock")
        selected, combined_et, combined_trap_ms = [], base_et_s, base_trap_ms

    if surrogate_mode and selected:
        # Parts the gearing re-choice brought in get their full-sim delta too.
        n_verify_sims += _verify(
            [r.part_id for r in selected if r.part_id not in verified],
            0.98,
            0.99,
            "Verifying selected parts (full sim)",
        )

    total_cost = sum(r.price_inr for r in selected)
    # Public convention (July 6, 2026): delta_et_s = optimized - base, so an
    # improvement is NEGATIVE (time dropped) — same sign language as
    # /api/simulate/quick's et_delta_s. Cost-per-tenth still divides by the
    # magnitude of the improvement.
    delta_et = combined_et - base_et_s
    delta_trap_ms = combined_trap_ms - base_trap_ms
    cost_per_tenth = (
        round(total_cost / (-delta_et * 10.0), 2)
        if (goal == "min_et" and delta_et < -1e-4)
        else None
    )

    # Display order: best contributor for the chosen objective first.
    display = sorted(selected, key=lambda r: -gain(r))
    parts = [OptimizedPart.from_roi(r, is_compatible=True) for r in display]

    synergies = [asdict(s) for s in _detect_synergies(selected)]
    warns = [asdict(w) for w in _detect_warnings(selected)]
    cat_priority = rank_categories(individual)
    next_up = None
    if include_next_upgrade:
        build_parts = list(selected)

        def _marginal(r: PartROIResult) -> float:
            et, _trap = score_build(base_config, build_parts + [r], parts_repo, full_et)
            return combined_et - et

        next_up = _next_upgrade_to_dict(
            _find_next_upgrade(
                {r.part_id for r in selected},
                individual,
                group_key=group_key,
                occupied_groups={group_key(r) for r in selected},
                marginal_fn=_marginal,
            )
        )

    stats = {**predictor.stats(), **extra_stats, "verify_sims": n_verify_sims}
    stats["final_sims"] = n_final_sims[0]
    if refinement is not None:
        stats["gearing_rechosen"] = refinement.gearing_changed
        stats["dropped_part_ids"] = [r.part_id for r in refinement.dropped]

    return OptimizedBuild(
        bike_name=base_config.name,
        goal=goal,
        budget_inr=float(budget_inr),
        profile=profile_enum.value,
        base_et_s=round(base_et_s, 4),
        base_trap_kmh=round(base_trap_ms * 3.6, 2),
        optimized_et_s=round(combined_et, 4),
        optimized_trap_kmh=round(combined_trap_ms * 3.6, 2),
        delta_et_s=round(delta_et, 4) + 0.0,  # +0.0 normalizes -0.0
        delta_trap_kmh=round(delta_trap_ms * 3.6, 2),
        total_cost_inr=round(total_cost, 2),
        budget_used_pct=(
            round(100.0 * total_cost / budget_inr, 1) if budget_inr > 0 else 0.0
        ),
        cost_per_tenth_inr=cost_per_tenth,
        parts=parts,
        synergies=synergies,
        warnings=warns,
        next_upgrade=next_up,
        category_priority=cat_priority,
        parts_evaluated=len(individual),
        parts_skipped_incompatible=0,  # candidate pool is compatibility-filtered upstream
        parts_skipped_no_gain=sum(1 for r in individual if gain(r) <= 0),
        scoring_method=predictor.method,
        scoring_stats=stats,
        applied_part_ids=apply_order_ids(selected),
    )
