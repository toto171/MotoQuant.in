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

import logging
import copy
import math
import warnings
from dataclasses import dataclass

from ..models import BikeConfig
from ..physics import MotoQuantEngine

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
            part.get("id") or part.get("part_id"), seed_price, exc_info=True,
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

    for pid in part_ids:
        part = parts_repo.get(pid)
        if part is None:
            continue

        # Compatibility check — default open (assume compatible unless proven otherwise)
        is_compat = True
        if bike_model_id is not None:
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

    # Evaluate each part independently to get individual ROI
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

    # Filter to parts that improve ET and have a finite price ≤ budget
    candidates = [
        r
        for r in individual
        if (allow_negative_parts or gain_of(r) >= 0) and r.price_inr <= budget_inr
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

    # ── Separate free parts — always include them regardless of budget ───
    # Free parts (price_inr == 0) don't consume budget, so they're always
    # beneficial to include if they improve ET.  Keeping them out of the DP
    # (which uses min 1 bucket per item) avoids a correctness edge case at
    # budget = ₹0.
    free_candidates = [r for r in candidates if r.is_free and gain_of(r) > 0]
    paid_candidates = [r for r in candidates if not r.is_free]

    # ── Knapsack DP on paid parts ─────────────────────────────────────
    # Discretise budget to buckets of ₹100 to keep DP tractable.
    # For budgets ≤ ₹5,00,000 and prices quantised to ₹100, the DP
    # table has 5000 × len(candidates) cells — very fast in Python.
    BUCKET = 100
    W = int(budget_inr // BUCKET)  # capacity in buckets

    # Weight per item (buckets), value per item (seconds × 1000 for int DP)
    SCALE = 1_000  # ms precision

    items: list[tuple[int, int, int]] = []  # (weight_buckets, value_ms, index)
    for i, r in enumerate(paid_candidates):
        w = max(1, int(r.price_inr // BUCKET))  # at least 1 bucket
        v = max(0, int(gain_of(r) * SCALE))
        if w <= W and v > 0:
            items.append((w, v, i))

    if not items:
        # No paid parts fit or have positive gain — only take free parts
        selected = list(free_candidates)
    else:
        # Standard 0/1 knapsack via 1D DP (rolling array)
        dp = [0] * (W + 1)
        choice = [[] for _ in range(W + 1)]  # track chosen item indices

        for w_item, v_item, idx in items:
            # Traverse backwards to avoid using same item twice
            for cap in range(W, w_item - 1, -1):
                new_val = dp[cap - w_item] + v_item
                if new_val > dp[cap]:
                    dp[cap] = new_val
                    choice[cap] = choice[cap - w_item] + [idx]

        chosen_paid = [paid_candidates[i] for i in choice[W]]
        selected = free_candidates + chosen_paid

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
        avg_cpt = sum(valid_cpt) / len(valid_cpt) if valid_cpt else float("inf")
        summary.append(
            {
                "category": cat,
                "best_roi": round(best_roi, 4),
                "best_et_gain_s": round(best_gain, 4),
                "avg_cost_per_tenth": round(avg_cpt, 0),
                "part_count": len(parts),
                "improving_count": len(improving),
            }
        )

    summary.sort(key=lambda d: -d["best_roi"])
    return summary
