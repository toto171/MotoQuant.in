"""
MotoQuant — Spec Validator
==========================
Physical-bounds checking and confidence scoring for scraped BikeSpec objects.

Validation checks:
  - Displacement vs bore/stroke consistency
  - Power/displacement ratio (sanity: 0.05–0.33 HP/cc 4T, x1.8 for 2T)
  - Power at the torque peak <= rated power; torque at the power peak <= rated torque
  - Torque/power relationship (peak torque = peak power × 5252 / RPM)
  - Mass range (100–500 kg)
  - Gear ratio ordering (each gear must be lower than previous)
  - Tire size format
  - Compression ratio range (8.0–16.0 for 4-stroke)
  - Year range sanity (1970–current+1)

Confidence scoring (0.0–1.0):
  - manufacturer_spec  → 0.90
  - scraped_confirmed  → 0.70  (cross-referenced with second source)
  - scraped            → 0.55  (single source, HTML parse)
  - estimated          → 0.40  (derived/extrapolated)
  - default_fallback   → 0.25  (BikeConfig default used)
"""

import math
import re
from datetime import datetime

from .spec import BikeSpec, ValidationResult

# ────────────────────────────────────────────────────────
# Physical bounds
# ────────────────────────────────────────────────────────

BOUNDS = {
    "displacement_cc": (50, 3000),
    "bore_mm": (35, 120),
    "stroke_mm": (30, 120),  # Harley Milwaukee-Eight is 111.1mm
    # compression_ratio: 4T range 8.5–16.5 (car/bike gasoline). 2-strokes run
    # much lower corrected (trapped) CR — 6.0–8.5 is realistic (RD350=6.6,
    # RGV250=7.5, RS125=12.5 uncorrected / ~7.8 corrected). We widen the
    # lower bound to 6.0 so 2T bikes import cleanly; 2T-specific sanity is
    # handled after the core bounds pass.
    "compression_ratio": (6.0, 16.5),
    "peak_power_hp": (5, 500),
    "peak_power_rpm": (3000, 18000),
    "peak_torque_nm": (5, 400),
    "peak_torque_rpm": (
        2000,
        15000,
    ),  # upper raised April 2026 for Kawasaki ZX-25R (I4, 14500 rpm peak torque, ~17k redline)
    "dry_mass_kg": (80, 500),
    "wet_mass_kg": (90, 550),
    "wheelbase_mm": (1000, 2000),
    "seat_height_mm": (600, 1100),
    "fuel_capacity_l": (
        3,
        60,
    ),  # lowered — small-cc 2T like RD350 carry ~16L but racers carry 4–6L
    "year_from": (1965, datetime.now().year + 2),
    "gears": (4, 7),
    "front_sprocket": (
        0,
        38,
    ),  # 0 = shaft/belt drive; chain 12-22; belt pulley up to 38
    "rear_sprocket": (0, 80),  # 0 = shaft/belt drive; chain 30-60; belt pulley up to 80
    "frontal_area_m2": (0.25, 0.90),
    "stroke_type": (2, 4),
    "tuned_rpm": (3000, 18000),
    # Factory electronic top-speed limiter. Lower bound 120 covers restricted
    # A2/learner-market variants; upper 340 is above every known street
    # limiter (299 gentleman's agreement, H2's ~337 derestricted ceiling).
    # Presence carries NO confidence penalty — it is a curated annotation,
    # not a scraped physical spec (deliberately absent from score_spec's
    # CRITICAL list).
    "speed_limiter_kmh": (120, 340),
}

# HP per cc sanity range. The ceiling is for a 4-stroke street engine: the
# hottest catalog entry is the supercharged Ninja H2R at 0.31 hp/cc and the
# best NA superbikes sit near 0.22-0.25 (it was 3.0 — ~10x too loose, so a
# 599 cc / 450 hp typo validated with no warning at all). 2-strokes get
# HP_PER_CC_2T_FACTOR on top (a power stroke every revolution). Above the
# ceiling is a warning; above HP_PER_CC_ERROR_FACTOR x the ceiling is an error
# (no production engine, boosted or not, gets there — a units/typo problem).
HP_PER_CC_MIN = 0.05  # lawnmower / scooter
HP_PER_CC_MAX = 0.33
HP_PER_CC_2T_FACTOR = 1.8
HP_PER_CC_ERROR_FACTOR = 2.0

# Power/torque consistency. With peak torque T_pk at rpm n_T and peak power
# P_pk at rpm n_P, a real curve must satisfy T_pk*w(n_T) <= P_pk (the torque
# peak cannot already out-power the power peak) and P_pk/w(n_P) <= T_pk (the
# torque at the power peak cannot exceed the peak torque). Rated figures come
# from different test standards, so a few % of slack is normal; above
# POWER_TORQUE_SLACK it is a physically inconsistent spec (confidence-gated:
# warning + an extra score penalty), above POWER_TORQUE_ERROR it is an error.
# The YZF-R9 entry (93 Nm @ 11500 = 150 hp > its rated 117.4 hp, 1.28x)
# validated with one soft warning and simmed 0.38 s fast.
POWER_TORQUE_SLACK = 1.05
POWER_TORQUE_ERROR = 1.50
INCONSISTENT_TAG = "Physically inconsistent"
INCONSISTENT_PENALTY = 0.07  # on top of the per-warning penalty

# Unit auto-correction. Only in the physically meaningful direction, and only
# when the converted value lands inside the bounds: a value entered in the
# smaller unit (kW for hp, lb-ft for Nm) reads LOW; a mass entered in lbs
# reads HIGH. (The old code multiplied an implausibly HIGH hp by 0.7457 —
# hp->kW, the inverse of the fix it claimed — and turned 450 "Nm" into 610 Nm,
# accepting both out-of-bounds results.)
#   field: (side the wrong-unit value falls on, factor, wrong unit, right unit)
UNIT_CORRECTIONS = {
    "peak_power_hp": ("low", 1.341, "kW", "HP"),
    "peak_torque_nm": ("low", 1.356, "ft-lb", "Nm"),
    "dry_mass_kg": ("high", 0.4536, "lbs", "kg"),
    "wet_mass_kg": ("high", 0.4536, "lbs", "kg"),
}

# Expected torque at peak-power RPM: T_Nm = HP × 9550 / RPM
# Allow 30% tolerance (cam timing, measurement variation)
TORQUE_CONSISTENCY_TOLERANCE = 0.30

# Accepts radial notation (120/70ZR17, 110/70R17) AND Indian commuter bias-ply
# dash notation where a dash replaces the radial code (100/80-17, 90/90-18).
TIRE_SIZE_RE = re.compile(
    r"^\d{2,3}[/\\]\d{2,3}(?:[ZR]?R?|-)\d{2}[WH]?$", re.IGNORECASE
)


# ────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────


def _in_bounds(val, lo, hi) -> bool:
    return lo <= val <= hi


def _power_to_torque_nm(hp: float, rpm: int) -> float:
    """Convert peak power to expected torque at that RPM."""
    return (hp * 745.7) / (rpm * 2 * math.pi / 60)


def _bore_stroke_to_cc(bore_mm: float, stroke_mm: float, cylinders: int = 4) -> float:
    return (math.pi / 4) * (bore_mm / 1000) ** 2 * (stroke_mm / 1000) * cylinders * 1e6


# ────────────────────────────────────────────────────────
# Main validator
# ────────────────────────────────────────────────────────


def validate_spec(spec: BikeSpec) -> ValidationResult:
    """
    Validate a BikeSpec and return a ValidationResult.

    Auto-corrects obvious unit mistakes in place (see ``UNIT_CORRECTIONS``;
    each is reported in ``corrected_fields`` and as a warning) and flags
    inconsistencies as warnings vs. errors.

    It does NOT fill in missing fields: a missing ``cd`` / ``gear_ratios`` is
    reported in ``defaulted_fields`` and left ``None`` so the importer's own
    defaults (category aero, the Tier-1 service-manual gear lookup) apply.
    Writing generic I4 ratios and a car-like Cd 0.32 into the spec here used
    to bypass those lookups — an R15 V4 lost its real cassette and 24 km/h of
    top speed, and the reseed path (which never validates) diverged from
    import.

    Errors → spec should not be imported.
    Warnings → spec can be imported with lower confidence.
    """
    errors = []
    warnings = []
    corrected = {}
    defaulted = {}

    # ── Required fields ────────────────────────────────────────────────
    if not spec.manufacturer:
        errors.append("manufacturer is required")
    if not spec.model_name:
        errors.append("model_name is required")

    # ── Numeric bounds ─────────────────────────────────────────────────
    for field_name, (lo, hi) in BOUNDS.items():
        val = getattr(spec, field_name, None)
        if val is None:
            continue
        if _in_bounds(val, lo, hi):
            continue
        fix = UNIT_CORRECTIONS.get(field_name)
        if fix is not None:
            side, factor, wrong_unit, right_unit = fix
            on_side = val < lo if side == "low" else val > hi
            fixed = val * factor
            if on_side and _in_bounds(fixed, lo, hi):
                corrected[field_name] = fixed
                setattr(spec, field_name, fixed)
                warnings.append(
                    f"{field_name}: {val} looks like {wrong_unit}, converted to "
                    f"{fixed:.1f} {right_unit}"
                )
                continue
        errors.append(f"{field_name}={val} out of bounds [{lo}, {hi}]")

    # ── Displacement consistency ───────────────────────────────────────
    if spec.bore_mm and spec.stroke_mm and spec.cylinders and spec.displacement_cc:
        calc_cc = _bore_stroke_to_cc(spec.bore_mm, spec.stroke_mm, spec.cylinders)
        if abs(calc_cc - spec.displacement_cc) / spec.displacement_cc > 0.05:
            warnings.append(
                f"Bore×Stroke×{spec.cylinders} yields {calc_cc:.0f}cc, "
                f"but displacement_cc={spec.displacement_cc:.0f} "
                f"(>5% discrepancy)"
            )

    # ── Power/displacement ratio ───────────────────────────────────────
    if spec.peak_power_hp and spec.displacement_cc:
        ratio = spec.peak_power_hp / spec.displacement_cc
        is_2t = spec.stroke_type == 2
        hp_cc_max = HP_PER_CC_MAX * (HP_PER_CC_2T_FACTOR if is_2t else 1.0)
        label = "2T" if is_2t else "4T"
        if ratio > hp_cc_max * HP_PER_CC_ERROR_FACTOR:
            errors.append(
                f"Power/displacement ratio {ratio:.2f} HP/cc is physically "
                f"implausible (> {hp_cc_max * HP_PER_CC_ERROR_FACTOR:.2f} for a "
                f"{label} engine) — check units / typo."
            )
        elif ratio > hp_cc_max:
            warnings.append(
                f"Power/displacement ratio {ratio:.2f} HP/cc is very high "
                f"(max ~{hp_cc_max:.2f} for {label}). Possibly forced induction?"
            )
        elif ratio < HP_PER_CC_MIN:
            warnings.append(f"Power/displacement ratio {ratio:.2f} HP/cc is very low")

    # ── Torque/power cross-check ───────────────────────────────────────
    if spec.peak_power_hp and spec.peak_power_rpm and spec.peak_torque_nm:
        expected_tq = _power_to_torque_nm(spec.peak_power_hp, spec.peak_power_rpm)
        diff_pct = abs(expected_tq - spec.peak_torque_nm) / expected_tq
        if diff_pct > TORQUE_CONSISTENCY_TOLERANCE:
            warnings.append(
                f"Torque inconsistency: at {spec.peak_power_rpm} RPM, "
                f"{spec.peak_power_hp:.0f} HP → expected ~{expected_tq:.0f} Nm "
                f"but got {spec.peak_torque_nm:.0f} Nm "
                f"({diff_pct * 100:.0f}% off). "
                f"Peak torque RPM may differ from peak power RPM."
            )

    # ── Power/torque physical consistency ──────────────────────────────
    _check_power_torque_consistency(spec, warnings, errors)

    # ── Mass sanity ────────────────────────────────────────────────────
    if spec.dry_mass_kg and spec.wet_mass_kg:
        if spec.wet_mass_kg < spec.dry_mass_kg:
            errors.append(
                f"wet_mass_kg ({spec.wet_mass_kg}) < dry_mass_kg ({spec.dry_mass_kg})"
            )
        elif spec.wet_mass_kg - spec.dry_mass_kg > 50:
            warnings.append(
                f"wet-dry mass difference is large: "
                f"{spec.wet_mass_kg - spec.dry_mass_kg:.0f} kg. Plausible?"
            )

    # ── Gear ratio ordering ────────────────────────────────────────────
    if spec.gear_ratios:
        for i in range(1, len(spec.gear_ratios)):
            if spec.gear_ratios[i] >= spec.gear_ratios[i - 1]:
                errors.append(
                    f"gear_ratios not strictly decreasing at index {i}: "
                    f"{spec.gear_ratios[i - 1]:.3f} → {spec.gear_ratios[i]:.3f}"
                )
                break

    # ── Tire size format ───────────────────────────────────────────────
    for attr in ("front_tire_size", "rear_tire_size"):
        size = getattr(spec, attr)
        if size and not TIRE_SIZE_RE.match(size.replace(" ", "")):
            warnings.append(
                f"{attr}='{size}' does not match standard format (e.g. 120/70ZR17)"
            )

    # ── Fields the importer will default (reported, never written) ─────
    if spec.cd is None:
        defaulted["cd"] = f"category aero default ({spec.category})"
    if spec.frontal_area_m2 is None:
        defaulted["frontal_area_m2"] = f"category aero default ({spec.category})"
    if spec.gear_ratios is None and spec.gears:
        defaulted["gear_ratios"] = f"Tier-1/Tier-2 gear lookup ({spec.gears}-speed)"

    is_valid = len(errors) == 0
    return ValidationResult(
        is_valid=is_valid,
        warnings=warnings,
        errors=errors,
        corrected_fields=corrected,
        defaulted_fields=defaulted,
    )


def _check_power_torque_consistency(
    spec: BikeSpec, warnings: list[str], errors: list[str]
) -> None:
    """Power at the torque peak / torque at the power peak vs the rated peaks."""
    hp, n_p = spec.peak_power_hp, spec.peak_power_rpm
    tq, n_t = spec.peak_torque_nm, spec.peak_torque_rpm
    if not (hp and n_p and tq and n_t):
        return
    p_peak_w = hp * 745.7
    p_at_tq_peak = tq * n_t * 2 * math.pi / 60
    t_at_p_peak = p_peak_w / (n_p * 2 * math.pi / 60)
    worst = max(p_at_tq_peak / p_peak_w, t_at_p_peak / tq)
    detail = (
        f"{tq:.0f} Nm @ {n_t:.0f} rpm = {p_at_tq_peak / 745.7:.0f} hp at the "
        f"torque peak vs rated {hp:.0f} hp @ {n_p:.0f} rpm "
        f"(needs {t_at_p_peak:.0f} Nm there); worst ratio {worst:.2f}x"
    )
    if worst > POWER_TORQUE_ERROR:
        errors.append(f"{INCONSISTENT_TAG} power/torque: {detail}")
    elif worst > POWER_TORQUE_SLACK:
        warnings.append(f"{INCONSISTENT_TAG} power/torque: {detail}")
    if spec.stroke_type != 2 and n_t > n_p:
        # At the torque peak dP/dw = T > 0, so power is still rising: a
        # 4-stroke cannot peak in torque above its power peak.
        errors.append(
            f"peak_torque_rpm {n_t:.0f} > peak_power_rpm {n_p:.0f} is impossible "
            "for a 4-stroke (power is still rising at the torque peak)"
        )


def score_spec(spec: BikeSpec, result: ValidationResult) -> float:
    """
    Compute an overall confidence score (0.0–1.0) for a BikeSpec.

    Base score depends on how many critical fields are populated,
    then penalty for warnings, bonus for cross-referenced data.
    """
    # Critical fields and their weights
    CRITICAL = [
        ("displacement_cc", 0.15),
        ("peak_power_hp", 0.12),
        ("peak_torque_nm", 0.08),
        ("dry_mass_kg", 0.10),
        ("gear_ratios", 0.10),
        ("front_sprocket", 0.07),
        ("rear_sprocket", 0.07),
        ("gears", 0.05),
        ("bore_mm", 0.05),
        ("stroke_mm", 0.05),
        ("front_tire_size", 0.04),
        ("rear_tire_size", 0.04),
        ("wheelbase_mm", 0.04),
        ("compression_ratio", 0.04),
    ]

    base = 0.0
    for field_name, weight in CRITICAL:
        val = getattr(spec, field_name, None)
        if val is not None:
            # Use field-specific confidence if available, else source default
            field_conf = spec.field_confidence.get(
                field_name, _source_confidence(spec.source_name)
            )
            base += weight * field_conf

    # Penalty: 0.03 per warning, 0.10 per error (errors also block import).
    # A physically inconsistent power/torque pair is confidence-gated: it costs
    # INCONSISTENT_PENALTY on top of its warning.
    warning_penalty = len(result.warnings) * 0.03 + INCONSISTENT_PENALTY * sum(
        1 for w in result.warnings if w.startswith(INCONSISTENT_TAG)
    )
    error_penalty = len(result.errors) * 0.10

    # Bonus: verified from two sources → +0.10
    cross_ref_bonus = 0.10 if spec.source_name == "scraped_confirmed" else 0.0

    score = base - warning_penalty - error_penalty + cross_ref_bonus
    return max(0.0, min(1.0, score))


def _source_confidence(source_name: str) -> float:
    """Map source name to base confidence for any field from that source."""
    CONF = {
        "manufacturer": 0.92,
        "service_manual": 0.95,
        "spec_sheet": 0.88,
        "dyno_validated": 0.90,
        "scraped_confirmed": 0.70,
        "bikez": 0.58,
        "bikeswiki": 0.55,
        "wikispeed": 0.50,
        "scraped": 0.52,
        "estimated": 0.38,
        "default_fallback": 0.25,
    }
    return CONF.get(source_name, 0.50)
