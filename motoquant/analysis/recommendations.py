"""
MotoQuant — Smart Build Recommender (Phase 4)
=============================================
Intelligent part selection and build planning that goes beyond raw ROI
ranking.  Adds compatibility rules, synergy detection, tiered build
generation, and human-readable upgrade paths.

How it differs from ``roi.py``
------------------------------
  ``roi.py``     — evaluates every part independently, then runs a knapsack
                   DP to find the cheapest combination that maximises ET gain.
  ``this module`` — wraps the ROI engine with domain knowledge:
    1. **Compatibility rules**: detects conflicts (two exhausts) and
       synergies (exhaust + ECU flash unlock more together than apart).
    2. **Build profiles**: predefined filters for "street-legal", "drag-prep",
       "full-race" that restrict which categories are eligible.
    3. **Tiered builds**: auto-generates budget / mid-range / full builds
       so the user sees a natural upgrade path.
    4. **Category priority**: data-driven ordering of which upgrades to
       buy first, based on the bike's existing config and ROI data.
    5. **Next-upgrade analysis**: given a current build, identifies the
       single best part to add next, including the marginal budget needed.

Usage
-----
    from motoquant.analysis.recommendations import (
        recommend_build, generate_upgrade_path, BuildProfile,
    )
    from motoquant.defaults import gsxr1000_k5

    config = gsxr1000_k5()
    rec = recommend_build(config, budget_inr=50_000, parts_repo=db.parts)
    print(rec.summary())

    path = generate_upgrade_path(config, parts_repo=db.parts, n_tiers=3)
    for tier in path.tiers:
        print(tier.summary())
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

from ..models import BikeConfig
from .roi import (
    EXCLUSIVE_CATEGORIES,
    BuildROIResult,
    PartROIResult,
    _run_et,
    compute_parts_roi,
    find_best_build,
    rank_categories,
)

# ─────────────────────────────────────────────────────────────────
# Build profiles — restrict which part categories are eligible
# ─────────────────────────────────────────────────────────────────


class BuildProfile(Enum):
    """Predefined part-selection profiles."""

    ALL = "all"
    STREET_LEGAL = "street_legal"
    DRAG_PREP = "drag_prep"
    FULL_RACE = "full_race"


# Categories allowed per profile.  If a profile key is not present in
# _PROFILE_CATEGORIES, ALL categories are allowed.
_PROFILE_CATEGORIES: dict[BuildProfile, set[str]] = {
    BuildProfile.STREET_LEGAL: {
        "exhaust",
        "ecu",
        "air_filter",
        "sprocket",
        "chain",
        "clutch_kit",
        "quickshifter",
        "battery",
        "bodywork",
        "suspension",
        "brakes",
        "tire",
    },
    BuildProfile.DRAG_PREP: {
        "exhaust",
        "ecu",
        "air_filter",
        "sprocket",
        "chain",
        "clutch_kit",
        "quickshifter",
        "wheelie_bar",
        "swingarm_ext",
        "battery",
        "bodywork",
        "tire",
        "nitrous",
        "fuel_system",
    },
    BuildProfile.FULL_RACE: {
        "exhaust",
        "ecu",
        "air_filter",
        "sprocket",
        "chain",
        "clutch_kit",
        "quickshifter",
        "wheelie_bar",
        "swingarm_ext",
        "battery",
        "bodywork",
        "tire",
        "nitrous",
        "fuel_system",
        "boost_kit",
        "suspension",
        "brakes",
    },
}


# ─────────────────────────────────────────────────────────────────
# Compatibility rules — conflicts and synergies between categories
# ─────────────────────────────────────────────────────────────────


# Only one part per exclusive-group can be selected. The taxonomy lives in
# roi.EXCLUSIVE_CATEGORIES (single source of truth — roi.py cannot import
# this module without a cycle); this list is the historical shape consumed
# by build_optimizer and the test-suite. June 2026: chain / boost_kit /
# nitrous / wheelie_bar / swingarm_ext added — a build can no more carry
# two chains or two turbo kits than two exhausts. Sprockets are handled
# position-aware (one front + one rear) inside the knapsack itself.
EXCLUSIVE_GROUPS: list[set[str]] = [{cat} for cat in sorted(EXCLUSIVE_CATEGORIES)]

# Synergy pairs: categories that gain more when combined.
# The multiplier is applied to the *combined* delta_et prediction
# in the tiered build output (informational, not used in DP).
SYNERGIES: list[tuple[str, str, float, str]] = [
    (
        "exhaust",
        "ecu",
        1.10,
        "Full exhaust + ECU flash unlocks ~10% more power than either alone",
    ),
    (
        "exhaust",
        "air_filter",
        1.05,
        "Better breathing: exhaust + high-flow filter complement each other",
    ),
    (
        "boost_kit",
        "fuel_system",
        1.15,
        "Forced induction demands upgraded fuel delivery",
    ),
    (
        "boost_kit",
        "clutch_kit",
        1.05,
        "Extra power benefits from a lock-up or slipper clutch upgrade",
    ),
    (
        "sprocket",
        "chain",
        1.02,
        "Matched gearing + chain ensures drivetrain reliability",
    ),
    (
        "wheelie_bar",
        "swingarm_ext",
        1.03,
        "Combined launch stability: bar + extended swingarm",
    ),
    (
        "nitrous",
        "fuel_system",
        1.12,
        "Nitrous requires adequate fuel flow to avoid lean detonation",
    ),
]

# Dependency rules: if you install A, you SHOULD also install B.
# These are soft warnings, not hard blocks.
SOFT_DEPENDENCIES: list[tuple[str, str, str]] = [
    (
        "boost_kit",
        "fuel_system",
        "Turbo/SC kit strongly recommends upgraded fuel system to avoid lean conditions",
    ),
    ("nitrous", "fuel_system", "Nitrous kit strongly recommends upgraded fuel system"),
    (
        "boost_kit",
        "ecu",
        "Forced induction needs an ECU retune to be safe and effective",
    ),
    (
        "nitrous",
        "ecu",
        "Nitrous benefits greatly from ECU flash for ignition timing adjustment",
    ),
]


# ─────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────


@dataclass
class CompatibilityWarning:
    """A warning about a potential issue in the selected build."""

    severity: str  # "info", "warning", "critical"
    category_a: str
    category_b: str | None
    message: str


@dataclass
class SynergyNote:
    """An informational note about positive interaction between parts."""

    category_a: str
    category_b: str
    multiplier: float
    description: str


@dataclass
class NextUpgrade:
    """The single best part to add next to an existing build."""

    part: PartROIResult
    marginal_et_gain_s: float  # additional ET improvement over current build
    marginal_cost_inr: float  # price of this part
    marginal_roi: float  # seconds per ₹10k for this upgrade
    reason: str  # human-readable reasoning


@dataclass
class BuildTier:
    """One tier in a multi-tier upgrade path."""

    tier_name: str  # "Budget", "Mid-Range", "Full Send"
    budget_inr: float
    build: BuildROIResult
    active_synergies: list[SynergyNote] = field(default_factory=list)
    warnings: list[CompatibilityWarning] = field(default_factory=list)

    def summary(self) -> str:
        """Human-readable tier summary."""
        lines = [
            f"── {self.tier_name} (budget: ₹{self.budget_inr:,.0f}) ──",
            f"  ET: {self.build.base_et_s:.3f}s → {self.build.modified_et_s:.3f}s "
            f"({self.build.delta_et_s:+.3f}s)",
            f"  Cost: ₹{self.build.total_cost_inr:,.0f}  "
            f"({len(self.build.selected_parts)} parts)",
        ]
        if self.active_synergies:
            lines.append("  Synergies:")
            for s in self.active_synergies:
                lines.append(f"    + {s.description}")
        if self.warnings:
            lines.append("  Warnings:")
            for w in self.warnings:
                lines.append(f"    ⚠ {w.message}")
        return "\n".join(lines)


@dataclass
class BuildRecommendation:
    """Complete recommendation output from recommend_build()."""

    bike_name: str
    profile: BuildProfile
    budget_inr: float

    # Core results
    build: BuildROIResult
    category_priority: list[dict]  # from rank_categories()

    # Intelligence layers
    active_synergies: list[SynergyNote] = field(default_factory=list)
    warnings: list[CompatibilityWarning] = field(default_factory=list)
    next_upgrade: NextUpgrade | None = None

    def summary(self) -> str:
        """Human-readable recommendation summary."""
        lines = [
            "═══ MotoQuant Smart Build Recommendation ═══",
            f"Bike: {self.bike_name}",
            f"Profile: {self.profile.value}",
            f"Budget: ₹{self.budget_inr:,.0f}",
            "",
            self.build.summary(),
        ]

        if self.active_synergies:
            lines.append("\nSynergies in this build:")
            for s in self.active_synergies:
                lines.append(f"  + {s.description}")

        if self.warnings:
            lines.append("\nWarnings:")
            for w in self.warnings:
                lines.append(f"  ⚠ [{w.severity.upper()}] {w.message}")

        if self.category_priority:
            lines.append("\nCategory priority (best ROI first):")
            for i, cat in enumerate(self.category_priority[:5], 1):
                lines.append(
                    f"  {i}. {cat['category']} — best gain: "
                    f"{cat['best_et_gain_s']:.3f}s"
                )

        if self.next_upgrade:
            nu = self.next_upgrade
            lines.append(f"\nNext upgrade: {nu.part.part_name}")
            lines.append(
                f"  +{nu.marginal_et_gain_s:.3f}s for ₹{nu.marginal_cost_inr:,.0f} — {nu.reason}"
            )

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """JSON-serialisable dict for CLI --json output."""
        result = {
            "bike_name": self.bike_name,
            "profile": self.profile.value,
            "budget_inr": self.budget_inr,
            "base_et_s": self.build.base_et_s,
            "modified_et_s": self.build.modified_et_s,
            "delta_et_s": round(self.build.delta_et_s, 4),
            "total_cost_inr": self.build.total_cost_inr,
            "parts_selected": [
                {
                    "id": p.part_id,
                    "name": p.part_name,
                    "category": p.category,
                    "price_inr": p.price_inr,
                    "delta_et_s": round(p.delta_et_s, 4),
                    "roi_score": round(p.roi_score, 4)
                    if not math.isinf(p.roi_score)
                    else None,
                }
                for p in self.build.selected_parts
            ],
            "synergies": [
                {
                    "categories": [s.category_a, s.category_b],
                    "multiplier": s.multiplier,
                    "description": s.description,
                }
                for s in self.active_synergies
            ],
            "warnings": [
                {
                    "severity": w.severity,
                    "message": w.message,
                }
                for w in self.warnings
            ],
            "category_priority": self.category_priority[:5],
        }
        if self.next_upgrade:
            nu = self.next_upgrade
            result["next_upgrade"] = {
                "part_id": nu.part.part_id,
                "part_name": nu.part.part_name,
                "marginal_et_gain_s": round(nu.marginal_et_gain_s, 4),
                "marginal_cost_inr": nu.marginal_cost_inr,
                "marginal_roi": round(nu.marginal_roi, 4),
                "reason": nu.reason,
            }
        return result


@dataclass
class UpgradePath:
    """Multi-tier upgrade path from stock to fully built."""

    bike_name: str
    tiers: list[BuildTier]

    def summary(self) -> str:
        lines = [
            f"═══ MotoQuant Upgrade Path: {self.bike_name} ═══",
        ]
        for tier in self.tiers:
            lines.append("")
            lines.append(tier.summary())
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "bike_name": self.bike_name,
            "tiers": [
                {
                    "tier_name": t.tier_name,
                    "budget_inr": t.budget_inr,
                    "base_et_s": t.build.base_et_s,
                    "modified_et_s": t.build.modified_et_s,
                    "delta_et_s": round(t.build.delta_et_s, 4),
                    "total_cost_inr": t.build.total_cost_inr,
                    "parts_count": len(t.build.selected_parts),
                    "parts": [
                        {"id": p.part_id, "name": p.part_name, "price_inr": p.price_inr}
                        for p in t.build.selected_parts
                    ],
                    "synergies": len(t.active_synergies),
                    "warnings": len(t.warnings),
                }
                for t in self.tiers
            ],
        }


# ─────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────


def _filter_parts_by_profile(
    parts: list[dict],
    profile: BuildProfile,
) -> list[dict]:
    """Filter parts list to those allowed by the build profile."""
    if profile == BuildProfile.ALL:
        return parts
    allowed = _PROFILE_CATEGORIES.get(profile)
    if allowed is None:
        return parts
    return [p for p in parts if p.get("category_name") in allowed]


def _detect_synergies(selected_parts: list[PartROIResult]) -> list[SynergyNote]:
    """Find active synergies in a parts selection."""
    cats = {p.category for p in selected_parts}
    active = []
    for cat_a, cat_b, mult, desc in SYNERGIES:
        if cat_a in cats and cat_b in cats:
            active.append(SynergyNote(cat_a, cat_b, mult, desc))
    return active


def _detect_warnings(selected_parts: list[PartROIResult]) -> list[CompatibilityWarning]:
    """Detect compatibility issues in a parts selection."""
    warns = []
    cats = {p.category for p in selected_parts}

    # Check soft dependencies
    for required_by, depends_on, msg in SOFT_DEPENDENCIES:
        if required_by in cats and depends_on not in cats:
            warns.append(
                CompatibilityWarning(
                    severity="warning",
                    category_a=required_by,
                    category_b=depends_on,
                    message=msg,
                )
            )

    # Check for duplicate categories (more than one part in an exclusive group)
    cat_counts: dict[str, int] = {}
    for p in selected_parts:
        cat_counts[p.category] = cat_counts.get(p.category, 0) + 1

    for group in EXCLUSIVE_GROUPS:
        for cat in group:
            if cat_counts.get(cat, 0) > 1:
                warns.append(
                    CompatibilityWarning(
                        severity="critical",
                        category_a=cat,
                        category_b=None,
                        message=f"Multiple {cat} parts selected — only one can be installed at a time",
                    )
                )

    return warns


def _find_next_upgrade(
    selected_part_ids: set[int],
    all_roi: list[PartROIResult],
) -> NextUpgrade | None:
    """
    Find the single best part to add next, excluding already-selected parts.

    Rather than re-simulating, uses the individual ROI results as estimates.
    The marginal gain is approximate (ignores interactions with existing parts)
    but is fast and directionally correct.
    """
    candidates = [
        r
        for r in all_roi
        if r.part_id not in selected_part_ids
        and r.delta_et_s > 0.005  # at least 5 ms gain
        and r.price_inr > 0
    ]

    if not candidates:
        return None

    # Sort by ROI (best bang-for-buck first)
    candidates.sort(
        key=lambda r: (
            0 if math.isinf(r.roi_score) else 1,
            -r.roi_score,
        )
    )

    best = candidates[0]
    marginal_roi, _ = (
        (best.delta_et_s / best.price_inr * 100_000, None)
        if best.price_inr > 0
        else (float("inf"), None)
    )

    # Generate reason
    if best.roi_score > 1.0:
        reason = f"Excellent ROI — {best.category_display or best.category} upgrade"
    elif best.delta_et_s > 0.1:
        reason = f"Large ET gain ({best.delta_et_s:.3f}s) — {best.category_display or best.category}"
    else:
        reason = f"Best remaining value in {best.category_display or best.category}"

    return NextUpgrade(
        part=best,
        marginal_et_gain_s=best.delta_et_s,
        marginal_cost_inr=best.price_inr,
        marginal_roi=marginal_roi,
        reason=reason,
    )


# ─────────────────────────────────────────────────────────────────
# Primary public functions
# ─────────────────────────────────────────────────────────────────


def recommend_build(
    base_config: BikeConfig,
    budget_inr: float,
    parts_repo,
    profile: BuildProfile = BuildProfile.ALL,
    bike_model_id: int | None = None,
    include_next_upgrade: bool = True,
) -> BuildRecommendation:
    """
    Generate a smart build recommendation for a bike within a budget.

    Wraps ``find_best_build()`` with compatibility analysis, synergy
    detection, category priority ordering, and next-upgrade suggestion.

    Parameters
    ----------
    base_config
        Stock BikeConfig.
    budget_inr
        Maximum spend in rupees.
    parts_repo
        ``PartsRepository`` instance.
    profile
        Build profile filter (street_legal, drag_prep, full_race, or all).
    bike_model_id
        DB bike_model_id for compatibility filtering.
    include_next_upgrade
        If True, also finds the best single part to add above the budget.

    Returns
    -------
    BuildRecommendation with full analysis.
    """
    # Get all candidate parts, filtered by profile
    all_parts = parts_repo.search(
        bike_model_id=bike_model_id,
        limit=200,
    )
    filtered_parts = _filter_parts_by_profile(all_parts, profile)
    filtered_ids = [p["id"] for p in filtered_parts]

    if not filtered_ids:
        base_et, _ = _run_et(base_config)
        empty_build = BuildROIResult(
            selected_parts=[],
            total_cost_inr=0.0,
            budget_inr=budget_inr,
            base_et_s=base_et,
            modified_et_s=base_et,
            delta_et_s=0.0,
            delta_trap_ms=0.0,
            parts_evaluated=0,
            parts_skipped_incompatible=0,
            parts_skipped_no_gain=0,
        )
        return BuildRecommendation(
            bike_name=base_config.name,
            profile=profile,
            budget_inr=budget_inr,
            build=empty_build,
            category_priority=[],
        )

    # Compute individual ROI for all candidate parts
    all_roi = compute_parts_roi(
        base_config=base_config,
        part_ids=filtered_ids,
        parts_repo=parts_repo,
        bike_model_id=bike_model_id,
    )

    # Run knapsack optimizer, reusing the ROI pass above (previously this
    # re-simulated every candidate a second time).
    build = find_best_build(
        base_config=base_config,
        budget_inr=budget_inr,
        parts_repo=parts_repo,
        part_ids=filtered_ids,
        bike_model_id=bike_model_id,
        precomputed_individual=all_roi,
    )

    # Detect synergies and warnings in the selected build
    synergies = _detect_synergies(build.selected_parts)
    warnings_list = _detect_warnings(build.selected_parts)

    # Category priority
    cat_priority = rank_categories(all_roi)

    # Next upgrade
    next_up = None
    if include_next_upgrade:
        selected_ids = {p.part_id for p in build.selected_parts}
        next_up = _find_next_upgrade(
            selected_part_ids=selected_ids,
            all_roi=all_roi,
        )

    return BuildRecommendation(
        bike_name=base_config.name,
        profile=profile,
        budget_inr=budget_inr,
        build=build,
        category_priority=cat_priority,
        active_synergies=synergies,
        warnings=warnings_list,
        next_upgrade=next_up,
    )


def generate_upgrade_path(
    base_config: BikeConfig,
    parts_repo,
    profile: BuildProfile = BuildProfile.ALL,
    bike_model_id: int | None = None,
    n_tiers: int = 3,
    budget_tiers: list[float] | None = None,
) -> UpgradePath:
    """
    Generate a multi-tier upgrade path from stock to fully built.

    If ``budget_tiers`` is not provided, auto-generates tiers based on
    the catalog price range:
      - Tier 1 ("Budget"):     25th percentile of total catalog value
      - Tier 2 ("Mid-Range"):  50th percentile
      - Tier 3 ("Full Send"):  total catalog value (or 75th pctile for 4+ tiers)

    Parameters
    ----------
    base_config
        Stock BikeConfig.
    parts_repo
        ``PartsRepository`` instance.
    profile
        Build profile filter.
    bike_model_id
        DB bike_model_id for compatibility filtering.
    n_tiers
        Number of tiers to generate (2–5).
    budget_tiers
        Explicit budgets per tier (ascending).  If None, auto-calculated.

    Returns
    -------
    UpgradePath with one BuildTier per tier.
    """
    n_tiers = max(2, min(5, n_tiers))

    # Discover available parts
    all_parts = parts_repo.search(bike_model_id=bike_model_id, limit=200)
    filtered_parts = _filter_parts_by_profile(all_parts, profile)

    if not filtered_parts:
        return UpgradePath(bike_name=base_config.name, tiers=[])

    # Auto-generate budget tiers from catalog prices
    if budget_tiers is None:
        prices = sorted(
            [
                p.get("price_inr", 0) or 0
                for p in filtered_parts
                if (p.get("price_inr") or 0) > 0
            ]
        )
        if not prices:
            return UpgradePath(bike_name=base_config.name, tiers=[])

        total_value = sum(prices)
        # Generate percentile breakpoints
        fractions = [(i + 1) / n_tiers for i in range(n_tiers)]
        budget_tiers = [max(min(prices), total_value * frac) for frac in fractions]

    # Tier names
    _TIER_NAMES = ["Budget", "Mid-Range", "Performance", "Full Send", "No Limits"]
    tier_names = _TIER_NAMES[: len(budget_tiers)]

    filtered_ids = [p["id"] for p in filtered_parts]
    tiers: list[BuildTier] = []

    for i, (budget, name) in enumerate(zip(budget_tiers, tier_names)):
        build = find_best_build(
            base_config=base_config,
            budget_inr=budget,
            parts_repo=parts_repo,
            part_ids=filtered_ids,
            bike_model_id=bike_model_id,
        )
        synergies = _detect_synergies(build.selected_parts)
        warns = _detect_warnings(build.selected_parts)

        tiers.append(
            BuildTier(
                tier_name=name,
                budget_inr=budget,
                build=build,
                active_synergies=synergies,
                warnings=warns,
            )
        )

    return UpgradePath(
        bike_name=base_config.name,
        tiers=tiers,
    )


def get_category_upgrade_order(
    base_config: BikeConfig,
    parts_repo,
    profile: BuildProfile = BuildProfile.ALL,
    bike_model_id: int | None = None,
) -> list[dict]:
    """
    Return the optimal order to upgrade categories, ranked by ROI.

    Each entry includes:
      - category: str
      - best_part: PartROIResult (the single best part in this category)
      - reason: str (human-readable explanation)

    Useful for building a "what to buy first" guide.
    """
    all_parts = parts_repo.search(bike_model_id=bike_model_id, limit=200)
    filtered_parts = _filter_parts_by_profile(all_parts, profile)
    filtered_ids = [p["id"] for p in filtered_parts]

    if not filtered_ids:
        return []

    all_roi = compute_parts_roi(
        base_config=base_config,
        part_ids=filtered_ids,
        parts_repo=parts_repo,
        bike_model_id=bike_model_id,
    )

    # Group by category, pick best per category
    cat_best: dict[str, PartROIResult] = {}
    for r in all_roi:
        if r.delta_et_s <= 0:
            continue
        key = r.category_display or r.category
        if key not in cat_best or r.roi_score > cat_best[key].roi_score:
            cat_best[key] = r

    # Sort by ROI descending
    ordered = sorted(
        cat_best.items(),
        key=lambda kv: (0 if math.isinf(kv[1].roi_score) else 1, -kv[1].roi_score),
    )

    result = []
    for rank, (cat, part) in enumerate(ordered, 1):
        if math.isinf(part.roi_score):
            reason = f"Free upgrade — {part.delta_et_s:.3f}s gain for ₹0"
        elif part.roi_score > 1.0:
            reason = f"High ROI: {part.delta_et_s:.3f}s gain for ₹{part.price_inr:,.0f}"
        elif part.delta_et_s > 0.1:
            reason = f"Large gain: {part.delta_et_s:.3f}s (₹{part.cost_per_tenth_inr:,.0f}/tenth)"
        else:
            reason = f"Moderate gain: {part.delta_et_s:.3f}s for ₹{part.price_inr:,.0f}"

        result.append(
            {
                "rank": rank,
                "category": cat,
                "best_part": part,
                "et_gain_s": round(part.delta_et_s, 4),
                "price_inr": part.price_inr,
                "roi_score": part.roi_score,
                "reason": reason,
            }
        )

    return result
