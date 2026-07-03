"""
MotoQuant Pro — Parts ROI Engine
=================================
Quantifies the return-on-investment of each performance part in the catalog
relative to a baseline simulation.

Core metrics
------------
  delta_et_s        : ET improvement in seconds (positive = faster).
  cost_per_tenth    : INR per 0.1-second improvement (lower = better;
                      float('inf') when a part makes no improvement).
  roi_score         : seconds gained per ₹10,000 spent × 10  (higher = better).
                      Dimensionless; useful for ranking a mixed-budget list.

Build optimizer
---------------
``find_best_build()`` uses a knapsack DP to find the maximum cumulative
ET gain achievable within a budget.  For small part lists (≤ 20 parts)
and large budgets, greedy and DP give the same answer; DP is exact.

Parts are applied *incrementally* (cheapest-first within the DP) so that
interaction effects (e.g. a chain upgrade with a sprocket upgrade) are
captured.

Usage
-----
    from motoquant.analysis.roi import compute_parts_roi, find_best_build
    from motoquant.database.connection import MotoQuantDB

    db  = MotoQuantDB()
    db.connect()
    cfg = db.bikes.to_config(db.bikes.get_current_config(bike_model_id=1)["id"])

    results = compute_parts_roi(cfg, part_ids=[1, 2, 3, 4, 5], parts_repo=db.parts)
    build   = find_best_build(cfg, budget_inr=50_000, parts_repo=db.parts)
"""

from __future__ import annotations

import copy
import logging
import math
import re
import warnings
from dataclasses import dataclass

from ..models import BikeConfig
from ..physics import MotoQuantEngine


def json_safe(obj):
    """Recursively replace non-finite floats (inf / -inf / NaN) with None so
    the result survives a strict JSON encoder (FastAPI's default and the jobs
    route both reject bare inf/nan). Shared safety net for optimizer/outlaw
    responses, where cost-per-tenth ratios can legitimately be infinite."""
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [json_safe(v) for v in obj]
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    return obj


# ─────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────


@dataclass
class PartROIResult:
    """ROI summary for a single part applied to a baseline bike."""

    # Part identity
    part_id: int
    part_name: str  # "Brand Model"
    brand: str
    category: str  # e.g. "exhaust", "ecu_flash"
    category_display: str  # e.g. "Exhaust System", "ECU Flash"

    # Pricing
    price_inr: float
    price_usd: float | None

    # Simulation outcomes
    base_et_s: float  # stock quarter-mile time
    modified_et_s: float  # with this part applied
    delta_et_s: float  # positive = faster (base - modified)
    delta_trap_ms: float  # trap speed improvement m/s (positive = faster)

    # ROI metrics
    roi_score: float  # s gained per ₹10,000 × 10  (higher = better)
    cost_per_tenth_inr: float  # INR per 0.1 s improvement (lower = better)

    # Fit / availability
    is_compatible: bool
    availability: str  # "in_stock", "order", "discontinued"

    # Build flag
    is_free: bool = False  # True when price_inr == 0 (weight-reduction, etc.)

    def summary_line(self) -> str:
        """One-liner for CLI output."""
        sign = "▲" if self.delta_et_s > 0 else ("▼" if self.delta_et_s < 0 else "─")
        et_str = f"{abs(self.delta_et_s):.3f}s {sign}"
        roi_str = f"{self.roi_score:.3f}" if self.roi_score < 999 else "∞"
        cpt_str = (
            f"₹{self.cost_per_tenth_inr:,.0f}/tenth"
            if self.delta_et_s > 0
            else "no gain"
        )
        price_s = f"₹{self.price_inr:,.0f}" if self.price_inr else "free"
        return (
            f"[{self.part_id:>3}] {self.part_name:<35} "
            f"{et_str:<12} ROI={roi_str:<8} {cpt_str}  {price_s}"
        )


@dataclass
class BuildROIResult:
    """Outcome of budget-constrained multi-part optimization."""

    selected_parts: list[PartROIResult]
    total_cost_inr: float
    budget_inr: float
    base_et_s: float
    modified_et_s: float
    delta_et_s: float  # cumulative improvement (positive = faster)
    delta_trap_ms: float  # cumulative trap speed improvement

    # How many parts were evaluated
    parts_evaluated: int
    parts_skipped_incompatible: int
    parts_skipped_no_gain: int

    def summary(self) -> str:
        lines = [
            f"Budget: ₹{self.budget_inr:,.0f}   Spent: ₹{self.total_cost_inr:,.0f}",
            f"Base ET:     {self.base_et_s:.3f}s",
            f"Modified ET: {self.modified_et_s:.3f}s  ({self.delta_et_s:+.3f}s)",
            f"Parts selected ({len(self.selected_parts)}):",
        ]
        for p in self.selected_parts:
            lines.append(f"  {p.summary_line()}")
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────


# Categories where a build can physically carry at most ONE part. Single
# source of truth — recommendations.EXCLUSIVE_GROUPS re-exports this set
# (recommendations imports roi; the reverse would be circular).
# Sprockets are position-exclusive (one front + one rear) and are handled
# via _knapsack_group_key, not this set.
EXCLUSIVE_CATEGORIES: frozenset[str] = frozenset(
    {
        "exhaust",
        "ecu",
        "clutch_kit",
        "air_filter",
        "quickshifter",
        "battery",
        "chain",
        "boost_kit",
        "nitrous",
        "wheelie_bar",
        "swingarm_ext",
        # July 2026 drag-essentials categories
        "lowering_kit",
        "air_shifter",
        "lockup_clutch",
    }
)

# Cross-category exclusivity: these categories compete for the same physical
# slot on the bike, so they share one knapsack group with their sibling —
# a build can't run a lockup AND a street clutch kit, nor an air shifter AND
# a quickshifter (the air shifter replaces the shift actuator entirely).
_EXCLUSIVE_CATEGORY_ALIASES: dict[str, str] = {
    "lockup_clutch": "clutch_kit",
    "air_shifter": "quickshifter",
}


def _bucket_weight(price_inr: float, bucket: int = 100) -> int:
    """Knapsack weight in budget buckets, rounded UP so the DP can never
    select a combination whose true price exceeds the budget (floor division
    under-weighed every part by up to bucket-1 rupees — June-11 audit)."""
    if price_inr is None or price_inr <= 0:
        return 0
    return int(-(-price_inr // bucket))


# Fallback position matcher for sprocket parts whose specifications blob
# lacks the 'position' key ('520 Front Sprocket 13T Pro', 'JT 530 Rear
# Sprocket 42T ...' — 14 seeded parts, July-3-2026 audit).
_SPROCKET_POS_RE = re.compile(r"\b(front|rear)\s+sprocket\b", re.IGNORECASE)


def _sprocket_positions(parts_repo, part_ids) -> dict[int, str]:
    """Map part_id -> 'front'/'rear' for sprocket parts (from specifications).
    Lets the knapsack treat front and rear sprockets as separate exclusive
    slots instead of allowing two rear sprockets in one build."""
    import json as _json

    out: dict[int, str] = {}
    getter = getattr(parts_repo, "get", None)
    if getter is None:
        return out
    for pid in part_ids:
        try:
            part = getter(pid)
        except Exception:
            # Unknown part id: skip it rather than failing the whole
            # gearing-hint scan.
            continue
        if not part or part.get("category_name") != "sprocket":
            continue
        specs = part.get("specifications")
        if isinstance(specs, str):
            try:
                specs = _json.loads(specs)
            except (ValueError, TypeError):
                specs = None
        if isinstance(specs, dict) and specs.get("position") in ("front", "rear"):
            out[pid] = specs["position"]
            continue
        # Belt-and-braces fallback (July 3, 2026): 14 seeded sprockets ship
        # without specifications.position but carry it verbatim in the model
        # name. Without this, each one falls into a ('__solo__', id)
        # singleton group and the knapsack can stack two front sprockets in
        # one build. scripts/patch_2026_07_03_sprocket_position.py stamps
        # the DB rows too; this regex protects fresh seeds / foreign DBs.
        m = _SPROCKET_POS_RE.search(str(part.get("model_name") or ""))
        if m:
            out[pid] = m.group(1).lower()
    return out


def _knapsack_group_key(r: PartROIResult, position_of: dict[int, str] | None = None):
    """Exclusivity group for the multiple-choice knapsack.

    - exclusive categories -> one shared group per category;
    - sprockets -> one group per position (front/rear) when known;
    - everything else -> its own singleton group (plain 0/1 item).
    """
    cat = (r.category or "").lower()
    if cat == "sprocket":
        pos = (position_of or {}).get(r.part_id)
        if pos in ("front", "rear"):
            return f"sprocket:{pos}"
        return ("__solo__", r.part_id)
    if cat in EXCLUSIVE_CATEGORIES:
        return _EXCLUSIVE_CATEGORY_ALIASES.get(cat, cat)
    return ("__solo__", r.part_id)


def _grouped_knapsack(
    candidates: list[PartROIResult],
    budget_inr: float,
    gain,
    group_key,
) -> list[PartROIResult]:
    """Multiple-choice 0/1 knapsack: maximise sum(gain) subject to
    sum(price) <= budget and at most one part per exclusivity group.
    Free parts weigh 0 buckets, so they are picked whenever gain > 0
    (including at budget 0) while still honouring group exclusivity."""
    BUCKET = 100
    SCALE = 1_000  # ms / (mm/s) precision for integer DP
    W = int(budget_inr // BUCKET) if budget_inr > 0 else 0

    groups: dict = {}
    for r in candidates:
        groups.setdefault(group_key(r), []).append(r)

    dp = [0] * (W + 1)
    choice: list[list] = [[] for _ in range(W + 1)]

    # Each group is a "choose at most one" block: reading from the pre-group
    # dp for every item in the group enforces mutual exclusivity within it.
    for items in groups.values():
        new_dp = dp[:]
        new_choice = [c[:] for c in choice]
        for r in items:
            v = int(round(gain(r) * SCALE))
            if v <= 0:
                continue
            w = _bucket_weight(r.price_inr, BUCKET)
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


def _run_et(config: BikeConfig) -> tuple[float, float]:
    """Run a quick simulation and return (ET_s, trap_speed_ms)."""
    engine = MotoQuantEngine(config)
    result = engine.run()
    return result.time_quarter, result.speed_quarter


def _roi_metrics(
    price_inr: float,
    delta_et_s: float,
) -> tuple[float, float]:
    """Compute roi_score and cost_per_tenth_inr from price + ET delta."""
    if price_inr is None:
        price_inr = 0.0

    if delta_et_s <= 0.0:
        # Part is neutral or makes it slower — no positive ROI
        return 0.0, float("inf")

    if price_inr <= 0.0:
        # Free modification (e.g. weight stripping with no cost entry)
        return float("inf"), 0.0

    # seconds gained per ₹10,000 spent × 10 for a more readable number
    roi_score = (delta_et_s / price_inr) * 10_000 * 10

    # INR per 0.1-second improvement
    cost_per_tenth = price_inr / (delta_et_s * 10)

    return roi_score, cost_per_tenth


# ─────────────────────────────────────────────────────────────────
# Primary public functions
# ─────────────────────────────────────────────────────────────────


def _resolve_price(part: dict, conn=None, *, use_live_pricing: bool = False) -> float:
    """
    Return the best available price for *part*.

    When *use_live_pricing* is True and *conn* is provided, we check the
    ``part_prices`` table for a live price that is:
      • fresher than the seed ``price_inr`` by >10 % (absolute INR difference), OR
      • present when the seed price is missing.
    Falls back to ``part["price_inr"]`` (seed value from catalog) otherwise.
    """
    seed_price = part.get("price_inr") or 0.0
    if not use_live_pricing or conn is None:
        return seed_price

    try:
        cur = conn.cursor()
        row = cur.execute(
            """
            SELECT price_inr, fetched_at FROM part_prices
             WHERE part_id = ?
               AND price_inr IS NOT NULL
               AND in_stock = 1
             ORDER BY price_inr ASC
             LIMIT 1
            """,
            (part.get("id") or part.get("part_id"),),
        ).fetchone()
        if row is None:
            return seed_price
        live_price = float(row["price_inr"])
        if seed_price <= 0:
            return live_price
        # Prefer live price only when it differs by >10% from seed (avoids noise)
        if abs(live_price - seed_price) / max(seed_price, 1.0) > 0.10:
            return live_price
        return seed_price
    except Exception:
        logging.getLogger(__name__).warning(
            "live price lookup failed for part %s — using seed price ₹%s",
            part.get("id") or part.get("part_id"),
            seed_price,
            exc_info=True,
        )
        return seed_price


def compute_parts_roi(
    base_config: BikeConfig,
    part_ids: list[int],
    parts_repo,  # PartsRepository — avoid circular import
    min_delta_et_ms: float = 5.0,  # ignore parts with <5 ms improvement (noise floor)
    require_compatible: bool = False,
    bike_model_id: int | None = None,
    use_live_pricing: bool = False,
    db_conn=None,  # sqlite3 connection for live price lookup
    et_fn=None,  # Callable[[BikeConfig], (et_s, trap_ms)]; defaults to full physics sim
) -> list[PartROIResult]:
    """
    Evaluate every supplied part against the baseline config.

    Each part is evaluated *independently* (applied to the stock config),
    so results are directly comparable.  Interaction effects are NOT
    captured here — use ``find_best_build()`` for combined builds.

    Parameters
    ----------
    base_config
        Stock BikeConfig (unmodified).
    part_ids
        IDs of parts to evaluate.
    parts_repo
        ``PartsRepository`` instance.
    min_delta_et_ms
        ET improvement floor in milliseconds.  Parts below this threshold
        still appear in the results but with roi_score = 0.
    require_compatible
        If True, skip parts not marked as compatible with ``bike_model_id``.
    bike_model_id
        DB bike_model_id used for compatibility filtering.

    Returns
    -------
    List[PartROIResult] sorted by roi_score descending (best ROI first).
    """
    import json

    _et = et_fn if et_fn is not None else _run_et
    base_et, base_trap = _et(base_config)
    results: list[PartROIResult] = []

    # Resolve the bike row ONCE for real fitment checks. Until June 2026 this
    # function only consulted the legacy compatible_bikes JSON list, so every
    # fitment_rules-based part was mislabelled incompatible (and the
    # parts_skipped_incompatible count upstream was fiction). When the repo
    # exposes a DB connection we now run the same is_compatible() engine the
    # part-picker UI uses; repo stubs without a connection fall back to the
    # legacy check.
    bike_row = None
    if bike_model_id is not None:
        conn = getattr(parts_repo, "_conn", None)
        if conn is not None:
            try:
                from ..database.parts_repo import enrich_bike_row_for_fitment

                raw = conn.execute(
                    "SELECT * FROM bike_models WHERE id = ?", (bike_model_id,)
                ).fetchone()
                if raw is not None:
                    bike_row = enrich_bike_row_for_fitment(conn, dict(raw))
            except Exception:
                bike_row = None

    if bike_row is not None:
        from ..parts.compatibility import is_compatible as _is_compatible_engine

    for pid in part_ids:
        part = parts_repo.get(pid)
        if part is None:
            continue

        # Compatibility check — production fitment engine when possible.
        is_compat = True
        if bike_model_id is not None:
            if bike_row is not None:
                is_compat = _is_compatible_engine(part, bike_row)[0]
            else:
                # Legacy fallback (no DB connection on the repo stub)
                compatible_bikes_raw = part.get("compatible_bikes")
                if compatible_bikes_raw:
                    try:
                        compatible_list = (
                            json.loads(compatible_bikes_raw)
                            if isinstance(compatible_bikes_raw, str)
                            else compatible_bikes_raw
                        )
                        is_compat = bike_model_id in compatible_list or part.get(
                            "fitment_universal", False
                        )
                    except (ValueError, TypeError):
                        is_compat = True
                else:
                    is_compat = part.get("fitment_universal", True)

        if require_compatible and not is_compat:
            continue

        # Apply part and simulate
        try:
            modified_config = parts_repo.apply_to_config(pid, base_config)
            mod_et, mod_trap = _et(modified_config)
        except Exception as exc:
            warnings.warn(
                f"ROI: skipping part {pid} ({part.get('model_name')}) — sim error: {exc}"
            )
            continue

        delta_et = base_et - mod_et  # positive = faster
        delta_trap = mod_trap - base_trap  # positive = faster

        # Apply noise floor
        effective_delta = delta_et if delta_et * 1000 >= min_delta_et_ms else 0.0
        price_inr = _resolve_price(part, db_conn, use_live_pricing=use_live_pricing)

        roi_score, cpt = _roi_metrics(price_inr, effective_delta)

        results.append(
            PartROIResult(
                part_id=pid,
                part_name=f"{part.get('brand', '')} {part.get('model_name', '')}".strip(),
                brand=part.get("brand", ""),
                category=part.get("category_name", ""),
                category_display=part.get("category_display", ""),
                price_inr=price_inr,
                price_usd=part.get("price_usd"),
                base_et_s=base_et,
                modified_et_s=mod_et,
                delta_et_s=delta_et,
                delta_trap_ms=delta_trap,
                roi_score=roi_score,
                cost_per_tenth_inr=cpt,
                is_compatible=is_compat,
                availability=part.get("availability", "unknown"),
                is_free=(price_inr == 0.0),
            )
        )

    # Sort: infinite ROI (free parts) at top, then by score descending
    results.sort(
        key=lambda r: (
            0 if math.isinf(r.roi_score) else 1,
            -r.roi_score,
        )
    )
    return results


def find_best_build(
    base_config: BikeConfig,
    budget_inr: float,
    parts_repo,
    part_ids: list[int] | None = None,
    category_filter: str | None = None,
    bike_model_id: int | None = None,
    allow_negative_parts: bool = False,
    min_delta_et_ms: float = 5.0,
    use_live_pricing: bool = False,
    db_conn=None,
    et_fn=None,  # injectable scorer (e.g. surrogate); defaults to full physics sim
    objective: str = "min_et",  # "min_et" (maximise ET gain) | "max_trap" (maximise trap gain)
    return_individual: bool = False,  # also return the per-part ROI list
    precomputed_individual: list[PartROIResult]
    | None = None,  # reuse caller's ROI pass
) -> BuildROIResult:
    """
    Find the combination of parts that maximises ET improvement within a budget.

    Uses an exact 0/1 knapsack DP with budget discretised to ₹100 buckets.
    This is exact for sets up to ~200 parts and budgets up to ₹5 lakh.

    Parameters
    ----------
    base_config
        Stock BikeConfig.
    budget_inr
        Maximum spend in rupees.
    parts_repo
        ``PartsRepository`` instance.
    part_ids
        Parts to consider.  If None, all parts in the catalog are evaluated.
    category_filter
        Optional category name to restrict candidates (e.g. "exhaust").
    bike_model_id
        If set, filters out incompatible parts.
    allow_negative_parts
        If True, includes parts that worsen ET (mass add-ons, etc.) in the pool.
        Normally False.
    min_delta_et_ms
        ET improvement floor in milliseconds.

    Returns
    -------
    BuildROIResult with selected parts, combined ET, and cost summary.
    """
    _et = et_fn if et_fn is not None else _run_et
    gain_of = (
        (lambda r: r.delta_trap_ms)
        if objective == "max_trap"
        else (lambda r: r.delta_et_s)
    )

    # Discover candidate part IDs
    if part_ids is None:
        raw = parts_repo.search(
            category=category_filter,
            bike_model_id=bike_model_id,
            limit=200,
        )
        part_ids = [p["id"] for p in raw]

    # Evaluate each part independently to get individual ROI (or reuse the
    # caller's already-computed list — recommend_build was previously running
    # this full sim pass twice per call).
    if precomputed_individual is not None:
        individual = precomputed_individual
    else:
        individual = compute_parts_roi(
            base_config=base_config,
            part_ids=part_ids,
            parts_repo=parts_repo,
            min_delta_et_ms=min_delta_et_ms,
            bike_model_id=bike_model_id,
            use_live_pricing=use_live_pricing,
            db_conn=db_conn,
            et_fn=et_fn,
        )

    # Filter to parts that improve the objective, fit the budget, and are
    # actually compatible (is_compatible now reflects the production fitment
    # engine; incompatible parts are counted, never built).
    candidates = [
        r
        for r in individual
        if (allow_negative_parts or gain_of(r) >= 0)
        and r.price_inr <= budget_inr
        and r.is_compatible
    ]

    n_evaluated = len(individual)
    n_incompat = sum(1 for r in individual if not r.is_compatible)
    n_no_gain = sum(1 for r in individual if gain_of(r) <= 0)

    if not candidates:
        base_et, base_trap = _et(base_config)
        _empty = BuildROIResult(
            selected_parts=[],
            total_cost_inr=0.0,
            budget_inr=budget_inr,
            base_et_s=base_et,
            modified_et_s=base_et,
            delta_et_s=0.0,
            delta_trap_ms=0.0,
            parts_evaluated=n_evaluated,
            parts_skipped_incompatible=n_incompat,
            parts_skipped_no_gain=n_no_gain,
        )
        return (_empty, individual) if return_individual else _empty

    # ── Multiple-choice knapsack with category exclusivity ────────────
    # The pre-June-2026 plain 0/1 DP could stack two exhausts / four air
    # filters (unbuildable) and floor-divided prices into buckets, letting
    # the "optimal" build exceed the stated budget by up to ₹99 per part.
    # _grouped_knapsack enforces at-most-one part per exclusive category
    # (and per sprocket position), rounds weights UP, and handles free
    # parts (weight 0) uniformly — including at budget ₹0.
    position_of = _sprocket_positions(parts_repo, [r.part_id for r in candidates])
    selected = _grouped_knapsack(
        candidates,
        budget_inr,
        gain_of,
        lambda r: _knapsack_group_key(r, position_of),
    )

    # ── Incremental simulation of selected build ──────────────────────
    # Apply parts in price-ascending order (smaller parts first so
    # they influence subsequent parts' interaction context accurately).
    selected_sorted = sorted(selected, key=lambda r: r.price_inr)
    build_config = copy.deepcopy(base_config)
    selected_ids = [r.part_id for r in selected_sorted]

    try:
        build_config = parts_repo.apply_multiple(selected_ids, build_config)
        build_et, build_trap = _et(build_config)
    except Exception as exc:
        warnings.warn(
            f"find_best_build: combined sim failed ({exc}); falling back to stock"
        )
        build_et, build_trap = _et(base_config)

    base_et, base_trap = _et(base_config)
    total_cost = sum(r.price_inr for r in selected)

    # Re-fetch ROI results in the sorted order for the output
    selected_roi = sorted(
        selected,
        key=lambda r: -(r.roi_score if objective == "min_et" else gain_of(r)),
    )

    _result = BuildROIResult(
        selected_parts=selected_roi,
        total_cost_inr=total_cost,
        budget_inr=budget_inr,
        base_et_s=base_et,
        modified_et_s=build_et,
        delta_et_s=base_et - build_et,
        delta_trap_ms=build_trap - base_trap,
        parts_evaluated=n_evaluated,
        parts_skipped_incompatible=n_incompat,
        parts_skipped_no_gain=n_no_gain,
    )
    return (_result, individual) if return_individual else _result


def rank_categories(
    roi_results: list[PartROIResult],
) -> list[dict]:
    """
    Aggregate ROI results by category.

    Returns a list of dicts:
      {"category": str, "best_roi": float, "best_et_gain": float,
       "avg_cost_per_tenth": float, "part_count": int}
    sorted by best_roi descending.
    """
    from collections import defaultdict

    buckets: dict[str, list[PartROIResult]] = defaultdict(list)
    for r in roi_results:
        buckets[r.category_display or r.category].append(r)

    summary = []
    for cat, parts in buckets.items():
        improving = [p for p in parts if p.delta_et_s > 0]
        if not improving:
            continue
        best_roi = max(p.roi_score for p in improving)
        best_gain = max(p.delta_et_s for p in improving)
        valid_cpt = [
            p.cost_per_tenth_inr
            for p in improving
            if not math.isinf(p.cost_per_tenth_inr)
        ]
        # None (→ JSON null) when no finite cost-per-tenth exists — a bare
        # float("inf") here is NOT JSON-compliant and 500s the optimize route
        # (caught by the full-API stress battery, July 3).
        avg_cpt = round(sum(valid_cpt) / len(valid_cpt), 0) if valid_cpt else None
        summary.append(
            {
                "category": cat,
                "best_roi": round(best_roi, 4),
                "best_et_gain_s": round(best_gain, 4),
                "avg_cost_per_tenth": avg_cpt,
                "part_count": len(parts),
                "improving_count": len(improving),
            }
        )

    summary.sort(key=lambda d: -d["best_roi"])
    return summary
