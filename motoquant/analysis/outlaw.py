"""
Outlaw / open-class ("max effort") build pipeline.

Composes the three previously-disjoint engines into one no-budget-limit
drag build, in the order that matters physically:

  1. TIRES    — best drag_prep rear fitment (highest mu_peak) applied first,
                because optimal parts/gearing shift once launch grip changes.
  2. PARTS    — build_optimizer.optimize_build with profile "full_race"
                (which whitelists every real category in the catalog:
                exhaust/ECU/boost/nitrous/wheelie bar/swingarm ext/...).
                "Unlimited" budget resolves to the ₹5M API ceiling — the sum
                of every premium part for a litre bike is ~₹1.5-2.5M, so the
                cap is unreachable in practice while keeping the knapsack DP
                memory bounded (roi.py allocates one bucket per ₹100 and
                overflows on float('inf')).
  3. SETUP    — ecu_autotune.autotune on the MODIFIED config (gearing sweep +
                launch-RPM sweep + tyre pressure + fuel/timing guidance).
                Sprocket parts selected in stage 2 become the sweep center —
                autotune's rear-sprocket sweep owns the final gearing word.
  4. VERIFY   — autotune's combined verification sim (recommended gearing +
                launch RPM on the full build) is the headline number.

Progress is partitioned across the stages like /api/jobs/compare does:
tires 0-0.05, parts 0.05-0.68, autotune 0.68-0.97, wrap-up to 1.0.
"""

from __future__ import annotations

import logging
from typing import Any

from .roi import json_safe as _finite  # shared JSON-safety net (nulls inf/nan)

logger = logging.getLogger(__name__)


# The API-level knapsack ceiling (see OptimizeBuildRequest.budget_inr le=5M).
UNLIMITED_BUDGET_INR = 5_000_000.0


def _span(progress_cb, lo: float, hi: float):
    """Map a stage's 0..1 progress onto the [lo, hi] slice of the whole job."""
    if progress_cb is None:
        return None

    def tick(frac: float, stage: str | None = None) -> None:
        try:
            frac = max(0.0, min(1.0, float(frac)))
        except (TypeError, ValueError):
            frac = 0.0
        progress_cb(lo + frac * (hi - lo), stage)

    return tick


def _best_drag_tire(tire_repo, bike_model_id: int) -> dict[str, Any] | None:
    """Highest-grip rear drag_prep fitment for the bike, or None."""
    try:
        fitments = tire_repo.get_bike_fitments(
            bike_model_id, position="rear", fitment_type="drag_prep"
        )
    except Exception:  # noqa: BLE001
        logger.debug("drag_prep fitment lookup failed", exc_info=True)
        return None
    best = None
    for f in fitments:
        mu = f.get("mu_peak")
        if mu is None:
            continue
        if best is None or mu > best.get("mu_peak", 0):
            best = f
    return best


def optimize_outlaw(
    base_config,
    parts_repo,
    tire_repo,
    *,
    bike_model_id: int | None = None,
    budget_inr: float | None = None,
    goal: str = "min_et",
    surrogate=None,
    surrogate_source: str = "none",
    max_candidates: int | None = None,
    gear_span: int = 3,
    launch_steps: int = 6,
    progress_cb=None,
) -> dict[str, Any]:
    """Run the composed outlaw/open-class pipeline. Returns a JSON-ready dict.

    ``budget_inr=None`` means "no limit" (resolved to the ₹5M internal cap —
    never pass float('inf') into the knapsack).
    """
    import copy

    from ..physics import MotoQuantEngine
    from .build_optimizer import optimize_build
    from .ecu_autotune import autotune

    resolved_budget = (
        UNLIMITED_BUDGET_INR
        if budget_inr is None or budget_inr <= 0
        else min(float(budget_inr), UNLIMITED_BUDGET_INR)
    )

    config = copy.deepcopy(base_config)
    if progress_cb:
        progress_cb(0.01, "Baseline run")

    baseline = MotoQuantEngine(copy.deepcopy(config)).run()
    baseline_et = float(baseline.time_quarter)
    baseline_trap_kmh = float(baseline.speed_quarter) * 3.6

    # ── Stage 1: drag rubber ────────────────────────────────────────────
    tire_stage: dict[str, Any] = {"applied": False}
    if tire_repo is not None and bike_model_id is not None:
        if progress_cb:
            progress_cb(0.02, "Selecting drag rubber")
        best = _best_drag_tire(tire_repo, bike_model_id)
        if best is not None:
            stock_mu = float(config.tires.mu_peak)
            new_mu = float(best["mu_peak"])
            if new_mu > stock_mu:
                config.tires.mu_peak = new_mu
                tire_stage = {
                    "applied": True,
                    "tire": f"{best.get('tire_manufacturer', '')} "
                    f"{best.get('model_name', '')}".strip(),
                    "size": best.get("size_designation"),
                    "mu_peak": new_mu,
                    "stock_mu_peak": stock_mu,
                    "price_inr": best.get("price_inr"),
                }
            else:
                tire_stage = {
                    "applied": False,
                    "note": "stock rubber already matches the best drag fitment",
                }
        else:
            tire_stage = {
                "applied": False,
                "note": "no drag_prep rear fitment in catalog for this bike",
            }

    # ── Stage 2: parts knapsack (full_race = every category eligible) ──
    build = optimize_build(
        config,
        resolved_budget,
        parts_repo,
        goal=goal,
        profile="full_race",
        bike_model_id=bike_model_id,
        surrogate=surrogate,
        surrogate_source=surrogate_source,
        max_candidates=max_candidates,
        progress_cb=_span(progress_cb, 0.05, 0.68),
    )
    build_dict = build.to_dict()
    selected_ids = [p["part_id"] for p in build_dict.get("parts", [])]

    # ── Stage 3: apply build + autotune the modified bike ──────────────
    if progress_cb:
        progress_cb(0.68, "Applying build")
    modified = copy.deepcopy(config)
    if selected_ids:
        try:
            modified = parts_repo.apply_multiple(selected_ids, modified)
        except Exception as e:  # noqa: BLE001
            logger.warning("apply_multiple failed on outlaw build: %s", e)

    setup = autotune(
        modified,
        gear_span=gear_span,
        launch_steps=launch_steps,
        include_combined=True,
        progress_cb=_span(progress_cb, 0.70, 0.97),
    )
    setup_dict = setup.to_dict()

    # ── Wrap-up: headline numbers ───────────────────────────────────────
    combined = setup_dict.get("combined") or {}
    final_et = combined.get("et_s") or build_dict.get("optimized_et_s")
    final_trap = combined.get("trap_kmh") or build_dict.get("optimized_trap_kmh")

    if progress_cb:
        progress_cb(1.0, "Done")

    return _finite(
        {
            "class_label": "outlaw",
            "goal": goal,
            "budget_inr": None if budget_inr is None else float(budget_inr),
            "budget_resolved_inr": resolved_budget,
            "budget_unlimited": budget_inr is None or budget_inr <= 0,
            "baseline_et_s": round(baseline_et, 4),
            "baseline_trap_kmh": round(baseline_trap_kmh, 1),
            "tire_stage": tire_stage,
            "build": build_dict,
            "setup": setup_dict,
            "final_et_s": round(float(final_et), 4) if final_et else None,
            "final_trap_kmh": round(float(final_trap), 1) if final_trap else None,
            "total_delta_s": (
                round(float(final_et) - baseline_et, 4) if final_et else None
            ),
            "total_cost_inr": build_dict.get("total_cost_inr"),
            "notes": [
                "Stage order: drag rubber → parts (full_race knapsack) → gearing/"
                "launch autotune on the modified bike → combined verification sim.",
                "Sprocket parts selected by the optimizer become the autotune "
                "gearing-sweep center; autotune owns the final gearing word.",
            ],
        }
    )
