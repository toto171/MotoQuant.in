"""
MotoQuant Pro — Build Optimizer
===============================
Product-facing parts-build optimizer (Track B).

Given a bike + budget (₹) + goal, return the best parts combination with
per-part ROI and the predicted ET / trap delta.  It is *surrogate-accelerated*:
candidate builds are scored through a fast surrogate model when one is
available and the candidate sits inside the surrogate's training envelope;
otherwise it transparently falls back to the full RK4 physics sim, so the
optimizer always returns a correct answer regardless of whether a surrogate
pickle is present on the backend.

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

import copy
import logging
import warnings
from dataclasses import asdict, dataclass, field

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
from .roi import PartROIResult, _run_et, compute_parts_roi, rank_categories

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
def _check_envelope(fvec) -> tuple[bool, list[str]]:
    """Mirror api._check_envelope: each BASE feature vs FEATURE_BOUNDS."""
    try:
        from .surrogate_data import FEATURE_BOUNDS, FEATURE_NAMES

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

    def __call__(self, config: BikeConfig) -> tuple[float, float]:
        if self.surrogate is None:
            self.n_fallback += 1
            return _run_et(config)
        try:
            from .surrogate_data import config_to_feature_vector

            fvec = config_to_feature_vector(config)
            ok, _violations = _check_envelope(fvec)
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
    delta_et_s: float  # standalone ET gain (positive = faster)
    delta_trap_ms: float  # standalone trap gain (m/s, positive = faster)
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
            delta_et_s=round(r.delta_et_s, 4),
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
    delta_et_s: float
    delta_trap_kmh: float
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
) -> list[PartROIResult]:
    """
    Pick the affordable subset maximising the goal metric, with at most one part
    from each exclusive category (exhaust / ecu / clutch_kit / air_filter /
    quickshifter / battery).  Free parts (price 0) cost no budget.
    """
    gain = (
        (lambda r: r.delta_trap_ms) if goal == "max_trap" else (lambda r: r.delta_et_s)
    )

    candidates = [
        r
        for r in individual
        if (allow_negative or gain(r) > 0) and r.price_inr <= budget_inr
    ]
    if not candidates:
        return []

    def group_key(r: PartROIResult):
        cat = (r.category or "").lower()
        return cat if cat in _EXCLUSIVE_CATEGORIES else ("__solo__", r.part_id)

    groups: dict = {}
    for r in candidates:
        groups.setdefault(group_key(r), []).append(r)

    BUCKET = 100
    SCALE = 1000  # ms / (mm/s) precision for integer DP
    W = int(budget_inr // BUCKET) if budget_inr > 0 else 0

    dp = [0] * (W + 1)
    choice: list[list[PartROIResult]] = [[] for _ in range(W + 1)]

    # Process each exclusive group as a "choose at most one" block; singleton
    # solo-groups reduce to ordinary 0/1 items.  Reading from the pre-group dp
    # for every item in a group enforces mutual exclusivity within the group.
    for items in groups.values():
        new_dp = dp[:]
        new_choice = [c[:] for c in choice]
        for r in items:
            v = int(round(gain(r) * SCALE))
            if v <= 0:
                continue
            w = max(0, int(r.price_inr // BUCKET))
            if w > W:
                continue
            for cap in range(W, w - 1, -1):
                cand = dp[cap - w] + v
                if cand > new_dp[cap]:
                    new_dp[cap] = cand
                    new_choice[cap] = choice[cap - w] + [r]
        dp = new_dp
        choice = new_choice

    return choice[W]


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
    base_config, base_et_s, base_trap_ms, goal, budget_inr, profile_value, predictor
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
        scoring_stats=predictor.stats(),
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
) -> OptimizedBuild:
    """
    Find the best on-budget parts build for ``base_config``.

    goal            "min_et" (maximise ET gain) or "max_trap" (maximise trap gain).
    profile         BuildProfile or its string value (all/street_legal/drag_prep/full_race).
    bike_model_id   DB bike_models.id — drives real compatibility filtering.
    surrogate       Optional loaded surrogate; None -> full-sim scoring (always correct).
    max_candidates  Cap the candidate pool (handy for fast tests / latency bounds).
    """
    goal = goal if goal in VALID_GOALS else "min_et"
    profile_enum = _coerce_profile(profile)
    predictor = make_predictor(surrogate, surrogate_source)

    # Base run (warm-up + absolute trap so we can report km/h).
    base_et_s, base_trap_ms = predictor(base_config)

    # Compatible, profile-filtered candidate parts.
    all_parts = parts_repo.search(bike_model_id=bike_model_id, limit=200)
    filtered = _filter_parts_by_profile(all_parts, profile_enum)
    candidate_ids = [p["id"] for p in filtered]
    if max_candidates is not None:
        candidate_ids = candidate_ids[:max_candidates]
    if not candidate_ids:
        return _empty_build(
            base_config,
            base_et_s,
            base_trap_ms,
            goal,
            budget_inr,
            profile_enum.value,
            predictor,
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

    gain = (
        (lambda r: r.delta_trap_ms) if goal == "max_trap" else (lambda r: r.delta_et_s)
    )
    selected = _select_build(individual, float(budget_inr), goal)

    # Combined sim of the selected build (captures part interactions).
    build_cfg = copy.deepcopy(base_config)
    ordered_for_apply = sorted(selected, key=lambda r: r.price_inr)
    if ordered_for_apply:
        try:
            build_cfg = parts_repo.apply_multiple(
                [r.part_id for r in ordered_for_apply], build_cfg
            )
            combined_et, combined_trap_ms = predictor(build_cfg)
        except Exception as exc:
            warnings.warn(
                f"optimize_build: combined sim failed ({exc}); reporting stock"
            )
            selected, combined_et, combined_trap_ms = [], base_et_s, base_trap_ms
    else:
        combined_et, combined_trap_ms = base_et_s, base_trap_ms

    total_cost = sum(r.price_inr for r in selected)
    delta_et = base_et_s - combined_et
    delta_trap_ms = combined_trap_ms - base_trap_ms
    cost_per_tenth = (
        round(total_cost / (delta_et * 10.0), 2)
        if (goal == "min_et" and delta_et > 1e-4)
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
        selected_ids = {r.part_id for r in selected}
        next_up = _next_upgrade_to_dict(
            _find_next_upgrade(base_config, combined_et, selected_ids, individual)
        )

    return OptimizedBuild(
        bike_name=base_config.name,
        goal=goal,
        budget_inr=float(budget_inr),
        profile=profile_enum.value,
        base_et_s=round(base_et_s, 4),
        base_trap_kmh=round(base_trap_ms * 3.6, 2),
        optimized_et_s=round(combined_et, 4),
        optimized_trap_kmh=round(combined_trap_ms * 3.6, 2),
        delta_et_s=round(delta_et, 4),
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
        scoring_stats=predictor.stats(),
    )
