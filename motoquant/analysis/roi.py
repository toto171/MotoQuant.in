"""
MotoQuant — Parts ROI Engine
============================
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

The selected build is then applied in a canonical order (NA parts
cheapest-first, forced induction last — ``apply_order_ids``) and re-scored as a
whole by ``refine_build``, so interaction effects (sprocket pairs, absolute
overrides erasing each other, power parts after a boost kit) are captured.

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
import json
import logging
import math
import re
import warnings
from dataclasses import dataclass

import numpy as np

from .. import engine_select
from ..models import BikeConfig

# Candidate-discovery cap for every optimizer / recommender pass. The catalog
# holds ~600 parts and some bikes have 205 compatible ones, so the old
# limit=200 (applied after the brand-ordered compatibility filter) silently
# dropped the alphabetically-last parts (ZEX nitrous, Öhlins suspension...) from
# every build. A plain integer, not None: an unfiltered search binds it into
# SQL ``LIMIT ?`` and SQLite rejects NULL there.
CANDIDATE_LIMIT = 100_000


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
# Nitrous shares the forced-induction slot with turbo/SC kits: both write the
# single forced_induction.boost_type scalar, so whichever is applied last
# silently erases the other (a ₹95k nitrous kit "selected" next to a
# supercharger contributed exactly 0.000 s — October 2026 audit).
_EXCLUSIVE_CATEGORY_ALIASES: dict[str, str] = {
    "lockup_clutch": "clutch_kit",
    "air_shifter": "quickshifter",
    "nitrous": "boost_kit",
}

# Categories whose parts flip the engine to forced induction. They are
# applied AFTER every naturally-aspirated part. The old
# bridge.apply_part_to_config only scaled the dyno curve for NA power mods
# while the engine was still NA, so a PCVI applied after a turbo kit added
# 0 hp (turbo+PCVI == turbo alone). The bridge now decides curve scaling per
# part, so builds are order-independent; this order is kept as the single
# deterministic convention every consumer shares (applied_part_ids).
_BOOST_CATEGORIES: frozenset[str] = frozenset({"boost_kit", "nitrous"})


def _apply_order(parts: list[PartROIResult]) -> list[PartROIResult]:
    """Canonical order to apply a selected build: NA parts first, then boost.

    Within each tier parts go cheapest-first (the historical price-ascending
    order). Every consumer that materialises a build — find_best_build,
    optimize_build, the outlaw pipeline — must use this order so the bike that
    is priced is the bike that is tuned and verified.
    """
    return sorted(
        parts,
        key=lambda r: (
            1 if (r.category or "").lower() in _BOOST_CATEGORIES else 0,
            r.price_inr or 0.0,
        ),
    )


def apply_order_ids(parts: list[PartROIResult]) -> list[int]:
    """Part ids of ``parts`` in the canonical application order."""
    return [r.part_id for r in _apply_order(parts)]


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
            continue
        # Last resort: the part's own override says which sprocket it swaps.
        pos = _sprocket_position_from_paths(part)
        if pos:
            out[pid] = pos
    return out


def _json_field(part: dict, key: str) -> dict:
    """A part row's JSON-object column as a dict ({} when absent/malformed)."""
    raw = part.get(key) if isinstance(part, dict) else None
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (ValueError, TypeError):
            return {}
    return raw if isinstance(raw, dict) else {}


def _written_paths(part: dict) -> tuple[set[str], set[str]]:
    """(absolute-override paths, every path) a part row writes."""
    overrides = set(_json_field(part, "param_overrides"))
    written = (
        overrides
        | set(_json_field(part, "param_deltas"))
        | set(_json_field(part, "param_multipliers"))
    )
    return overrides, written


def _sprocket_position_from_paths(part: dict) -> str | None:
    """'front'/'rear' from which sprocket-teeth path the part writes."""
    _, written = _written_paths(part)
    front = "drivetrain.front_sprocket" in written
    rear = "drivetrain.rear_sprocket" in written
    if front and not rear:
        return "front"
    if rear and not front:
        return "rear"
    return None


# ─────────────────────────────────────────────────────────────────
# Brake / suspension slot classification (position-aware exclusivity)
# ─────────────────────────────────────────────────────────────────
#
# Brakes and suspension are NOT single-slot like an exhaust. A valid brake
# build carries front pads + rear pads + steel lines + a rotor together; a
# valid suspension build carries a fork mod + a rear shock together. What
# must be prevented is TWO parts fighting for the SAME physical slot (two
# front-pad sets, two rear rotors, two forks, two rear shocks). So the
# exclusivity key is (category, subtype, position) — mirroring the sprocket
# (category, position) treatment — NOT a blunt whole-category lock.
#
# CRITICAL SAFETY RULE: if a part's slot can't be confidently determined it
# is left NON-exclusive (its own singleton group). We never wrongly exclude a
# part we can't classify — the worst case of an unknown part is that it can
# co-exist with something it maybe shouldn't, which is far safer than silently
# dropping a legitimate complementary part from every build.

# specifications.type -> canonical brake slot subtype. Only subtypes that map
# to one physical brake slot are listed; generic 'brake_component', 'fluid',
# hydraulic clutch masters, etc. are intentionally absent -> non-exclusive.
_BRAKE_SUBTYPE: dict[str, str] = {
    "brake_pads": "pad",
    "pads": "pad",
    "pad": "pad",
    "rotor": "rotor",
    "brake_rotor": "rotor",
    "disc": "rotor",
    "rotor_and_pads": "rotor_and_pads",
    "caliper": "caliper",
    "radial_caliper": "caliper",
    "master_cylinder": "master_cylinder",
    "line": "line",
    "brake_hose": "line",
    "hose": "line",
}

# specifications.type -> physical suspension slot. Forks always live at the
# front, shocks at the rear, so the subtype alone fixes the slot. Ambiguous
# types (bare 'spring'/'spring_kit', 'coilover', steering 'damper', fork
# 'brace', 'lowering_kit') are intentionally absent -> non-exclusive.
_SUSP_SLOT: dict[str, str] = {
    "fork": "fork",
    "fork_internals": "fork",
    "fork_cartridge": "fork",
    "fork_springs": "fork",
    "cartridge": "fork",
    "rear_shock": "shock",
    "shock": "shock",
    "monoshock": "shock",
}

# Name-regex fallbacks (used only when specifications.type is missing/unknown).
# The optional trailing 's' matches the plural forms real part names use
# ("Brake Pads", "Steel Lines", "Wave Rotors").
_BRAKE_SUBTYPE_NAME_RE = re.compile(
    r"\b(pad|rotor|disc|line|hose|caliper|master)s?\b", re.IGNORECASE
)
_BRAKE_NAME_SUBTYPE = {
    "pad": "pad",
    "rotor": "rotor",
    "disc": "rotor",
    "line": "line",
    "hose": "line",
    "caliper": "caliper",
    "master": "master_cylinder",
}
_POS_FRONT_RE = re.compile(r"\bfront\b", re.IGNORECASE)
_POS_REAR_RE = re.compile(r"\brear\b", re.IGNORECASE)
_SUSP_FORK_NAME_RE = re.compile(r"\b(fork|cartridge)s?\b", re.IGNORECASE)
_SUSP_SHOCK_NAME_RE = re.compile(r"\b(shock|monoshock)s?\b", re.IGNORECASE)


def _brake_susp_slot(
    category: str | None, specs: dict | None, model_name: str | None
) -> str | None:
    """Classify a brakes/suspension part into a physical-slot key.

    Returns a slot key like ``'brakes:pad:front'`` or ``'suspension:fork'``
    when the slot can be confidently determined, else ``None`` (caller must
    treat None as NON-exclusive). Reads ``specifications`` first, then falls
    back to a name regex. Never raises.
    """
    cat = (category or "").lower()
    name = str(model_name or "")
    specs = specs if isinstance(specs, dict) else {}
    stype = str(specs.get("type") or "").lower()

    if cat == "suspension":
        slot = _SUSP_SLOT.get(stype)
        if slot is None:
            has_fork = bool(_SUSP_FORK_NAME_RE.search(name))
            has_shock = bool(_SUSP_SHOCK_NAME_RE.search(name))
            if has_fork and not has_shock:
                slot = "fork"
            elif has_shock and not has_fork:
                slot = "shock"
        if slot in ("fork", "shock"):
            return f"suspension:{slot}"
        return None

    if cat == "brakes":
        subtype = _BRAKE_SUBTYPE.get(stype)
        if subtype is None:
            m = _BRAKE_SUBTYPE_NAME_RE.search(name)
            if m:
                subtype = _BRAKE_NAME_SUBTYPE.get(m.group(1).lower())
        if subtype is None:
            return None
        pos = str(specs.get("position") or "").lower()
        if pos not in ("front", "rear", "front_rear"):
            has_f = bool(_POS_FRONT_RE.search(name))
            has_r = bool(_POS_REAR_RE.search(name))
            if has_f and has_r:
                pos = "front_rear"
            elif has_f:
                pos = "front"
            elif has_r:
                pos = "rear"
            else:
                pos = ""
        if pos not in ("front", "rear", "front_rear"):
            # Subtype known but no confident position -> non-exclusive.
            return None
        return f"brakes:{subtype}:{pos}"

    return None


def _brake_susp_slots(parts_repo, part_ids) -> dict[int, str]:
    """Map part_id -> slot key for brakes/suspension parts (from the repo).

    Mirrors ``_sprocket_positions``: lets the knapsack treat different brake
    slots (front pad vs rear pad vs steel line vs rotor) and suspension slots
    (fork vs rear shock) as separate exclusive groups, so complementary parts
    coexist but two parts fighting for one slot cannot both be selected.
    Parts whose slot can't be classified are simply omitted (-> non-exclusive).
    """
    import json as _json

    out: dict[int, str] = {}
    getter = getattr(parts_repo, "get", None)
    if getter is None:
        return out
    for pid in part_ids:
        try:
            part = getter(pid)
        except Exception:
            continue
        if not part or part.get("category_name") not in ("brakes", "suspension"):
            continue
        specs = part.get("specifications")
        if isinstance(specs, str):
            try:
                specs = _json.loads(specs)
            except (ValueError, TypeError):
                specs = None
        slot = _brake_susp_slot(
            part.get("category_name"), specs, part.get("model_name")
        )
        if slot:
            out[pid] = slot
    return out


# ─────────────────────────────────────────────────────────────────
# Physical-slot classification for the knapsack (October 2026)
# ─────────────────────────────────────────────────────────────────
#
# ``_brake_susp_slot`` above is the conservative pure classifier (it returns
# None whenever it cannot place a part). ``part_slot`` layers the catalog
# realities the knapsack needs on top of it, because "None -> freely
# stackable" let the no-limit outlaw build buy 6 complete fairing kits,
# 13 fuel-system parts (4 "Advanced Fuel System" units, two injector sets, a
# standalone ECU, three fuel controllers, two pumps), 3 caliper kits and
# 7 pad sets (October 2026 audit). The rules:
#
#   * functional slot first — a part whose overrides only drive the shift
#     actuator IS a quickshifter whatever its category (HealTech's QS module
#     is filed under 'ecu' and stacked with a real QS, the later absolute
#     override erasing the better shift time);
#   * a part that writes forced_induction.boost_type / wheelie.wheelie_bar /
#     chassis.swingarm_extension_mm owns that single scalar slot;
#   * brakes: an aftermarket brake part with no stated axle is a FRONT part
#     (performance calipers, radial masters, wave rotors and race pads are
#     front-axle items); a front+rear set occupies the front slot;
#   * suspension: a coilover kit is the rear shock, a lowering kit/linkage
#     shares the lowering_kit slot, spring kits are fork springs;
#   * fuel_system / bodywork: one part per functional slot (fuel controller,
#     injectors, pump, regulator, carb/jetting...; fairing set, screen...).

# Paths that only drive the shift actuator (plus incidental mass).
_SHIFT_ACTUATOR_PATHS = frozenset(
    {
        "drivetrain.quickshifter",
        "drivetrain.air_shifter",
        "drivetrain.total_shift_time_ms",
        "drivetrain.shift_cut_duration_ms",
        "drivetrain.post_shift_retard_ms",
    }
)
_INCIDENTAL_PATHS = frozenset({"chassis.dry_mass_kg"})

# One physical scalar = one slot: two parts writing these cannot coexist.
_SCALAR_SLOT_PATHS: dict[str, str] = {
    "forced_induction.boost_type": "boost_kit",
    "wheelie.wheelie_bar": "wheelie_bar",
    "chassis.swingarm_extension_mm": "swingarm_ext",
}

_FUEL_TYPE_SLOT: dict[str, str] = {
    "fuel_controller": "controller",
    "fuel_management": "controller",
    "tuning_computer": "controller",
    "fuel_map_ecu": "controller",
    "fuel_quickshift": "controller",
    "piggyback_fuel": "controller",
    "fuel_injector": "injector",
    "injector": "injector",
    "in_tank": "pump",
    "fuel_pump": "pump",
    "pump": "pump",
    "regulator": "regulator",
    "fuel_regulator": "regulator",
    "fuel_rail": "rail",
    "fuel_line": "line",
    "surge_tank": "surge_tank",
    "jet_kit": "carb",
    "carburetor": "carb",
    "carburetor_set": "carb",
}
_FUEL_NAME_SLOTS: tuple[tuple[re.Pattern, str], ...] = (
    (re.compile(r"\binjectors?\b|\bID\d{3,4}", re.IGNORECASE), "injector"),
    (re.compile(r"\bregulator\b", re.IGNORECASE), "regulator"),
    (re.compile(r"\bsurge\b", re.IGNORECASE), "surge_tank"),
    (re.compile(r"\bpump\b", re.IGNORECASE), "pump"),
    (re.compile(r"\brail\b", re.IGNORECASE), "rail"),
    (re.compile(r"\b(jet|carb|carburett?or)s?\b", re.IGNORECASE), "carb"),
    (re.compile(r"\bfuel\s+line\b", re.IGNORECASE), "line"),
    (
        re.compile(
            r"\b(fuel\s+(system|management|controller|map)|controller|"
            r"standalone|infinity)\b",
            re.IGNORECASE,
        ),
        "controller",
    ),
)

_BODY_TYPE_SLOT: dict[str, str] = {
    "fairing": "fairing",
    "fairing_kit": "fairing",
    "windscreen": "windscreen",
    "screen": "windscreen",
    "clip_on": "clip_ons",
    "clip_ons": "clip_ons",
    "rearsets": "rearsets",
    "winglets": "winglets",
    "mirror_delete": "mirror_delete",
    "skid_plate": "skid_plate",
    "frame_sliders": "frame_sliders",
}
_BODY_NAME_SLOTS: tuple[tuple[re.Pattern, str], ...] = (
    (re.compile(r"\bfairings?\b", re.IGNORECASE), "fairing"),
    (re.compile(r"\b(wind)?screen\b", re.IGNORECASE), "windscreen"),
    (re.compile(r"\bclip[- ]?ons?\b", re.IGNORECASE), "clip_ons"),
    (re.compile(r"\brear\s*sets?\b", re.IGNORECASE), "rearsets"),
    (re.compile(r"\bwinglets?\b", re.IGNORECASE), "winglets"),
    (re.compile(r"\bmirror\b", re.IGNORECASE), "mirror_delete"),
    (re.compile(r"\bskid\s*plate\b", re.IGNORECASE), "skid_plate"),
    (re.compile(r"\b(frame\s+)?sliders?\b", re.IGNORECASE), "frame_sliders"),
)

_SUSP_FALLBACK_SLOT: dict[str, str] = {
    "coilover": "suspension:shock",
    "spring_kit": "suspension:fork",
    "spring": "suspension:fork",
    "lowering_kit": "lowering_kit",
    "lowering_linkage": "lowering_kit",
}
_LOWERING_NAME_RE = re.compile(r"\blowering\b", re.IGNORECASE)
_COILOVER_NAME_RE = re.compile(r"\bcoil[- ]?over\b", re.IGNORECASE)


def _first_name_slot(name: str, table) -> str | None:
    for pattern, slot in table:
        if pattern.search(name):
            return slot
    return None


def part_slot(part: dict) -> str | None:
    """Physical-slot key for a part row, or None (= freely stackable).

    Returns a key such as ``'sprocket:rear'``, ``'brakes:pad:front'``,
    ``'fuel_system:injector'``, ``'bodywork:fairing'`` or an exclusive
    category name (``'quickshifter'``, ``'boost_kit'``...) when the part's
    function puts it in that slot. Never raises.
    """
    if not isinstance(part, dict):
        return None
    try:
        cat = str(part.get("category_name") or "").lower()
        name = str(part.get("model_name") or "")
        specs = _json_field(part, "specifications")
        stype = str(specs.get("type") or "").lower()
        overrides, written = _written_paths(part)

        # 1. single-scalar slots (the scalar can hold only one part's value)
        for path, slot in _SCALAR_SLOT_PATHS.items():
            if path in overrides:
                return slot

        # 2. functional shift-actuator slot, whatever the filing category
        shift = written & _SHIFT_ACTUATOR_PATHS
        if shift and written <= (_SHIFT_ACTUATOR_PATHS | _INCIDENTAL_PATHS):
            return "quickshifter"

        if cat == "sprocket":
            pos = specs.get("position")
            if pos not in ("front", "rear"):
                m = _SPROCKET_POS_RE.search(name)
                pos = m.group(1).lower() if m else _sprocket_position_from_paths(part)
            return f"sprocket:{pos}" if pos in ("front", "rear") else None

        if cat == "brakes":
            slot = _brake_susp_slot(cat, specs, name)
            if slot is None:
                # Subtype known but no stated axle -> front-axle part.
                subtype = _BRAKE_SUBTYPE.get(stype)
                if subtype is None:
                    m = _BRAKE_SUBTYPE_NAME_RE.search(name)
                    subtype = _BRAKE_NAME_SUBTYPE.get(m.group(1).lower()) if m else None
                if subtype is None:
                    return None
                slot = f"brakes:{subtype}:front"
            # A combined front+rear set occupies the front slot; a
            # rotor-and-pads kit is the rotor upgrade.
            slot = slot.replace(":front_rear", ":front")
            return slot.replace("brakes:rotor_and_pads:", "brakes:rotor:")

        if cat == "suspension":
            slot = _brake_susp_slot(cat, specs, name)
            if slot is not None:
                return slot
            if stype in _SUSP_FALLBACK_SLOT:
                return _SUSP_FALLBACK_SLOT[stype]
            if _LOWERING_NAME_RE.search(name):
                return "lowering_kit"
            if _COILOVER_NAME_RE.search(name):
                return "suspension:shock"
            return None

        if cat == "fuel_system":
            sub = _FUEL_TYPE_SLOT.get(stype) or _first_name_slot(name, _FUEL_NAME_SLOTS)
            if sub is None and {"flow_cc_min"} & set(specs):
                sub = "injector"
            return f"fuel_system:{sub}" if sub else None

        if cat == "bodywork":
            sub = _BODY_TYPE_SLOT.get(stype) or _first_name_slot(name, _BODY_NAME_SLOTS)
            return f"bodywork:{sub}" if sub else None
    except Exception:  # noqa: BLE001 — classification must never break a build
        logging.getLogger(__name__).debug("part_slot failed", exc_info=True)
    return None


def part_slots(parts) -> dict[int, str]:
    """``part_slot`` over an iterable of part rows -> {part_id: slot}."""
    out: dict[int, str] = {}
    for p in parts or ():
        if not isinstance(p, dict) or p.get("id") is None:
            continue
        slot = part_slot(p)
        if slot:
            out[p["id"]] = slot
    return out


def _part_slots_from_repo(parts_repo, part_ids) -> dict[int, str]:
    """``part_slots`` for ids looked up through ``parts_repo.get``."""
    getter = getattr(parts_repo, "get", None)
    if getter is None:
        return {}
    rows = []
    for pid in part_ids:
        try:
            row = getter(pid)
        except Exception:  # noqa: BLE001 — unknown id: just skip it
            continue
        if isinstance(row, dict):
            rows.append({**row, "id": row.get("id", pid)})
    return part_slots(rows)


def _knapsack_group_key(
    r: PartROIResult,
    position_of: dict[int, str] | None = None,
    slot_of: dict[int, str] | None = None,
):
    """Exclusivity group for the multiple-choice knapsack.

    - sprockets -> one group per position (front/rear) when known;
    - any part with a physical slot in ``slot_of`` (see ``part_slot``:
      brake/suspension slots, fuel-system and bodywork slots, a quickshifter
      filed under another category...) -> one group per slot;
    - exclusive categories -> one shared group per category (nitrous shares
      the forced-induction group with turbo/SC kits);
    - everything else (incl. unclassifiable brake/suspension parts) -> its own
      singleton group (plain 0/1 item, freely selectable).
    """
    cat = (r.category or "").lower()
    slot = (slot_of or {}).get(r.part_id)
    if cat == "sprocket":
        pos = (position_of or {}).get(r.part_id)
        if pos in ("front", "rear"):
            return f"sprocket:{pos}"
        if slot and slot.startswith("sprocket:"):
            return slot
        return ("__solo__", r.part_id)
    if slot:
        return _EXCLUSIVE_CATEGORY_ALIASES.get(slot, slot)
    if cat in ("brakes", "suspension"):
        return ("__solo__", r.part_id)
    if cat in EXCLUSIVE_CATEGORIES:
        return _EXCLUSIVE_CATEGORY_ALIASES.get(cat, cat)
    return ("__solo__", r.part_id)


_KNAPSACK_BUCKET_INR = 100
_KNAPSACK_SCALE = 1_000  # ms / (mm/s) precision for the integer DP


def _grouped_knapsack(
    candidates: list[PartROIResult],
    budget_inr: float,
    gain,
    group_key,
) -> list[PartROIResult]:
    """Multiple-choice 0/1 knapsack: maximise sum(gain) subject to
    sum(price) <= budget and at most one part per exclusivity group.
    Free parts weigh 0 buckets, so they are picked whenever gain > 0
    (including at budget 0) while still honouring group exclusivity.

    Implementation (October 2026): a NumPy DP over ₹100 buckets with one
    back-pointer array per group, replacing the pure-Python DP that copied a
    choice list per bucket per group (~80 s of GIL-held CPU and ~47 MB at the
    outlaw ₹5M budget, up to 4 runs per request). Picks are IDENTICAL to the
    legacy algorithm — same item values/weights, same group order, same
    strict-improvement tie-breaking (first item in group order wins a tie),
    same returned order (group order); tests/test_fixwave_analysis_knapsack.py
    pins it against a verbatim copy of the old implementation.

    Exact fast path: when the budget covers the heaviest affordable positive
    item of EVERY group at once, the DP optimum is simply each group's
    highest-value item (first on ties) — no DP needed.
    """
    BUCKET = _KNAPSACK_BUCKET_INR
    SCALE = _KNAPSACK_SCALE
    W = int(budget_inr // BUCKET) if budget_inr > 0 else 0

    groups: dict = {}
    for r in candidates:
        groups.setdefault(group_key(r), []).append(r)

    # (part, value, weight) per group, keeping exactly the items the legacy DP
    # considered (it skipped non-positive values and parts heavier than W).
    blocks: list[list[tuple[PartROIResult, int, int]]] = []
    for items in groups.values():
        block = []
        for r in items:
            v = int(round(gain(r) * SCALE))
            if v <= 0:
                continue
            w = _bucket_weight(r.price_inr, BUCKET)
            if w > W:
                continue
            block.append((r, v, w))
        if block:
            blocks.append(block)
    if not blocks:
        return []

    if sum(max(w for _r, _v, w in b) for b in blocks) <= W:
        picks = []
        for b in blocks:
            best = b[0]
            for item in b[1:]:
                if item[1] > best[1]:
                    best = item
            picks.append(best[0])
        return picks

    dp = np.zeros(W + 1, dtype=np.int64)
    back: list[np.ndarray] = []
    for b in blocks:
        new_dp = dp.copy()
        choice = np.full(W + 1, -1, dtype=np.int32)
        for idx, (_r, v, w) in enumerate(b):
            # cand[k] is the value at capacity w+k from the PRE-group dp, so
            # each group contributes at most one item (MCKP exclusivity).
            cand = dp[: W + 1 - w] + v
            tgt = new_dp[w:]
            better = cand > tgt
            if better.any():
                tgt[better] = cand[better]
                choice[w:][better] = idx
        dp = new_dp
        back.append(choice)

    picks = []
    cap = W
    for b, choice in zip(reversed(blocks), reversed(back)):
        idx = int(choice[cap])
        if idx >= 0:
            r, _v, w = b[idx]
            picks.append(r)
            cap -= w
    picks.reverse()
    return picks


def _run_et(config: BikeConfig) -> tuple[float, float]:
    """Run a full physics simulation and return (ET_s, trap_speed_ms).

    Routed through ``engine_select.make_engine`` so the Rust core is used when
    it is active (bit-identical results, ~60x faster); the Python reference
    engine otherwise.
    """
    result = engine_select.make_engine(config).run()
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


def noise_floored_metrics(
    price_inr: float, delta_et_s: float, min_delta_et_ms: float = 5.0
) -> tuple[float, float]:
    """``_roi_metrics`` after the same noise floor ``compute_parts_roi`` uses
    (a gain below ``min_delta_et_ms`` scores like no gain)."""
    effective = delta_et_s if delta_et_s * 1000 >= min_delta_et_ms else 0.0
    return _roi_metrics(price_inr, effective)


def _objective_gain(objective: str):
    """Positive-is-better per-part gain for the knapsack objective."""
    if objective == "max_trap":
        return lambda r: r.delta_trap_ms
    return lambda r: r.delta_et_s


def passes_noise_floor(gain_value: float, min_delta_et_ms: float) -> bool:
    """True when a part's gain clears the selection noise floor.

    The floor is expressed in thousandths of the objective unit (ms of ET for
    min_et, mm/s of trap for max_trap). Until October 2026 the floor only
    zeroed ``roi_score``: the knapsack still bought parts below it (e.g.
    ₹11,990 brake lines for 1.5 ms in no-limit outlaw builds).
    """
    return gain_value * 1000.0 >= min_delta_et_ms and gain_value > 0


def score_build(
    base_config: BikeConfig, parts: list[PartROIResult], parts_repo, et_fn
) -> tuple[float, float]:
    """Score ``parts`` applied together to ``base_config`` (canonical order)."""
    ids = apply_order_ids(parts)
    if not ids:
        return et_fn(base_config)
    cfg = parts_repo.apply_multiple(ids, copy.deepcopy(base_config))
    return et_fn(cfg)


@dataclass
class BuildRefinement:
    """Outcome of ``refine_build`` (all numbers from the supplied scorer)."""

    selected: list[PartROIResult]
    et_s: float
    trap_ms: float
    sims: int
    gearing_changed: bool
    dropped: list[PartROIResult]


def _is_sprocket_key(key) -> bool:
    return isinstance(key, str) and key.startswith("sprocket:")


def refine_build(
    base_config: BikeConfig,
    selected: list[PartROIResult],
    pool: list[PartROIResult],
    budget_inr: float,
    parts_repo,
    et_fn,
    *,
    objective: str = "min_et",
    group_key=None,
    top_k: int = 4,
    max_drop_rounds: int = 4,
    on_sim=None,
) -> BuildRefinement:
    """Re-check a knapsack pick on the COMBINED build with real scores.

    The knapsack adds per-part gains measured on the STOCK bike, which is
    wrong for interacting parts. Two passes fix the failures the October 2026
    audit found:

    1. Gearing — front and rear sprockets were picked independently (each
       ~-0.11 s alone) and together gave 15/50 (+39% final drive): the
       ₹25.6 L outlaw build verified 0.72 s SLOWER than its own turbo alone.
       The sprocket slot(s) are re-chosen jointly on top of the rest of the
       build: none / one front / one rear / a front+rear pair, from the top
       ``top_k`` sprockets per position (by individual gain), within budget.
    2. Drop-one — any selected part whose removal improves the combined
       objective is removed (greedy, best removal first, up to
       ``max_drop_rounds``), so a build can never be worse than a subset of
       itself (e.g. a QS-module override that erases a better quickshifter).
    """
    group_key = group_key or (lambda r: _knapsack_group_key(r))
    cache: dict = {}
    sims = [0]

    def value(et: float, trap: float) -> float:
        return trap if objective == "max_trap" else -et

    tol = 1e-3 if objective == "max_trap" else 1e-4

    def score(parts: list[PartROIResult]) -> tuple[float, float]:
        key = tuple(sorted(r.part_id for r in parts))
        if key not in cache:
            cache[key] = score_build(base_config, parts, parts_repo, et_fn)
            sims[0] += 1
            if on_sim is not None:
                on_sim()
        return cache[key]

    current = list(selected)
    cur_et, cur_trap = score(current)
    gearing_changed = False

    # ── 1. joint gearing choice ─────────────────────────────────────────
    spr_pool = [r for r in pool if _is_sprocket_key(group_key(r)) and r.is_compatible]
    if spr_pool:
        gain = _objective_gain(objective)
        rest = [r for r in current if not _is_sprocket_key(group_key(r))]
        room = budget_inr - sum(r.price_inr or 0.0 for r in rest)
        cur_spr = [r for r in current if _is_sprocket_key(group_key(r))]

        def top(position: str) -> list[PartROIResult]:
            cands = [
                r
                for r in spr_pool
                if group_key(r) == f"sprocket:{position}"
                and (r.price_inr or 0.0) <= room
            ]
            cands.sort(key=lambda r: -gain(r))
            out = cands[:top_k]
            for r in cur_spr:
                if group_key(r) == f"sprocket:{position}" and r not in out:
                    out.append(r)
            return out

        fronts, rears = top("front"), top("rear")
        options: list[tuple[PartROIResult, ...]] = [()]
        options += [(f,) for f in fronts] + [(r,) for r in rears]
        options += [
            (f, r)
            for f in fronts
            for r in rears
            if (f.price_inr or 0.0) + (r.price_inr or 0.0) <= room
        ]
        best_parts, best_val = current, value(cur_et, cur_trap)
        best_score = (cur_et, cur_trap)
        for opt in options:
            parts = rest + list(opt)
            et_o, trap_o = score(parts)
            if value(et_o, trap_o) > best_val + tol:
                best_parts, best_val, best_score = (
                    parts,
                    value(et_o, trap_o),
                    (et_o, trap_o),
                )
        if best_parts is not current:
            gearing_changed = {r.part_id for r in best_parts} != {
                r.part_id for r in current
            }
            current = list(best_parts)
            cur_et, cur_trap = best_score

    # ── 2. drop-one ─────────────────────────────────────────────────────
    dropped: list[PartROIResult] = []
    for _round in range(max(0, max_drop_rounds)):
        if not current:
            break
        best_idx, best_val, best_score = None, value(cur_et, cur_trap) + tol, None
        for i in range(len(current)):
            trial = current[:i] + current[i + 1 :]
            et_t, trap_t = score(trial)
            if value(et_t, trap_t) > best_val:
                best_idx, best_val, best_score = i, value(et_t, trap_t), (et_t, trap_t)
        if best_idx is None:
            break
        dropped.append(current.pop(best_idx))
        cur_et, cur_trap = best_score

    return BuildRefinement(
        selected=current,
        et_s=cur_et,
        trap_ms=cur_trap,
        sims=sims[0],
        gearing_changed=gearing_changed,
        dropped=dropped,
    )


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

        # Apply part and simulate. NOTE: route through parts_repo.apply_to_config
        # (not the concrete bridge.apply_part_to_config) so an injected repo /
        # test stub keeps control of how a part mutates the config. The extra
        # get(pid) inside apply_to_config is a cheap indexed lookup, dwarfed by
        # the RK4 sim below — not worth breaking the repo-injection seam for.
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

    Uses an exact multiple-choice knapsack DP (budget in ₹100 buckets, one
    part per physical slot — see ``part_slot``), then re-scores the combined
    build with ``refine_build`` (joint gearing choice + drop-one), so the
    reported ``modified_et_s`` is the scorer's verdict on the exact part list.

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
    gain_of = _objective_gain(objective)

    # Discover candidate part IDs (no 200-row cap — see CANDIDATE_LIMIT).
    if part_ids is None:
        raw = parts_repo.search(
            category=category_filter,
            bike_model_id=bike_model_id,
            limit=CANDIDATE_LIMIT,
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

    # Filter to parts that clear the noise floor, fit the budget, and are
    # actually compatible (is_compatible reflects the production fitment
    # engine; incompatible parts are counted, never built).
    candidates = [
        r
        for r in individual
        if (allow_negative_parts or passes_noise_floor(gain_of(r), min_delta_et_ms))
        and r.price_inr <= budget_inr
        and r.is_compatible
    ]

    n_evaluated = len(individual)
    n_incompat = sum(1 for r in individual if not r.is_compatible)
    n_no_gain = sum(1 for r in individual if gain_of(r) <= 0)

    base_et, base_trap = _et(base_config)
    if not candidates:
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

    # ── Multiple-choice knapsack with physical-slot exclusivity ───────
    # _grouped_knapsack enforces at-most-one part per exclusive category,
    # sprocket position and physical slot (part_slot), rounds weights UP so
    # the budget can never be exceeded, and handles free parts uniformly.
    _cand_ids = [r.part_id for r in candidates]
    position_of = _sprocket_positions(parts_repo, _cand_ids)
    pool = [r for r in individual if r.is_compatible and r.price_inr <= budget_inr]
    slot_of = _part_slots_from_repo(parts_repo, [r.part_id for r in pool])

    def group_key(r):
        return _knapsack_group_key(r, position_of, slot_of)

    selected = _grouped_knapsack(candidates, budget_inr, gain_of, group_key)

    # ── Combined build: joint gearing + drop-one, then the final score ─
    # The knapsack adds stock-bike gains; refine_build re-scores the actual
    # combined build so interacting parts (sprocket pairs, overrides that
    # erase each other) can't make it worse than a subset of itself.
    try:
        refined = refine_build(
            base_config,
            selected,
            pool,
            budget_inr,
            parts_repo,
            _et,
            objective=objective,
            group_key=group_key,
        )
        selected = refined.selected
        build_et, build_trap = refined.et_s, refined.trap_ms
    except Exception as exc:  # noqa: BLE001 — report stock, never a fiction
        warnings.warn(f"find_best_build: combined sim failed ({exc}); reporting stock")
        selected, build_et, build_trap = [], base_et, base_trap

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
       "avg_cost_per_tenth": float | None, "part_count": int}
    sorted by best_roi descending. avg_cost_per_tenth is None when no
    improving part in the category has a finite cost-per-tenth.
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
