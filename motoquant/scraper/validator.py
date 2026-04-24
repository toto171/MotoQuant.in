"""
MotoQuant Pro — Spec Validator
==============================
Physical-bounds checking and confidence scoring for scraped BikeSpec objects.

Validation checks:
  - Displacement vs bore/stroke consistency
  - Power/displacement ratio (sanity: 0.3–3.0 HP/cc)
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
}

# HP per cc sanity range (naturally aspirated)
HP_PER_CC_MIN = 0.05  # lawnmower / scooter
HP_PER_CC_MAX = 3.0  # highly tuned race engine

# Expected torque at peak-power RPM: T_Nm = HP × 9550 / RPM
# Allow 30% tolerance (cam timing, measurement variation)
TORQUE_CONSISTENCY_TOLERANCE = 0.30

TIRE_SIZE_RE = re.compile(r"^\d{2,3}[/\\]\d{2,3}[ZR]?R?\d{2}[WH]?$", re.IGNORECASE)

CATEGORY_AERO_DEFAULTS = {
    "sport": (0.32, 0.45),
    "naked": (0.40, 0.52),
    "cruiser": (0.50, 0.55),
    "adventure": (0.45, 0.55),
    "touring": (0.52, 0.58),
    "scooter": (0.45, 0.35),
}

# Default gear ratios for inline-4 sport bikes (close-ratio)
DEFAULT_GEAR_RATIOS_6 = [2.600, 2.105, 1.750, 1.500, 1.333, 1.200]
DEFAULT_GEAR_RATIOS_5 = [2.600, 2.000, 1.650, 1.400, 1.250]

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


def _parse_tire_width(size: str) -> int | None:
    """Extract width from '190/55ZR17' → 190."""
    if not size:
        return None
    m = re.match(r"^(\d{2,3})", size.strip())
    return int(m.group(1)) if m else None


# ────────────────────────────────────────────────────────
# Main validator
# ────────────────────────────────────────────────────────


def validate_spec(spec: BikeSpec) -> ValidationResult:
    """
    Validate a BikeSpec and return a ValidationResult.

    Auto-corrects obvious issues (unit conversions) and flags
    inconsistencies as warnings vs. errors.

    Errors → spec should not be imported.
    Warnings → spec can be imported with lower confidence.
    """
    errors = []
    warnings = []
    corrected = {}

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
        if not _in_bounds(val, lo, hi):
            # Try unit correction before flagging error
            if field_name == "peak_power_hp" and 5 <= val * 0.7457 <= 500:
                # Looks like kW was entered as HP — convert
                corrected[field_name] = val * 0.7457
                setattr(spec, field_name, val * 0.7457)
                warnings.append(
                    f"{field_name}: {val} looks like kW, converted to "
                    f"{val * 0.7457:.1f} HP"
                )
            elif field_name == "peak_torque_nm" and 5 <= val * 0.7457 <= 400:
                # Looks like ft-lb was entered as Nm — convert
                corrected[field_name] = val * 1.356
                setattr(spec, field_name, val * 1.356)
                warnings.append(
                    f"{field_name}: {val} looks like ft-lb, converted to "
                    f"{val * 1.356:.1f} Nm"
                )
            elif field_name == "dry_mass_kg" and 80 <= val * 0.4536 <= 500:
                # Looks like lbs
                corrected[field_name] = val * 0.4536
                setattr(spec, field_name, val * 0.4536)
                warnings.append(
                    f"{field_name}: {val} looks like lbs, converted to "
                    f"{val * 0.4536:.1f} kg"
                )
            else:
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
        # 2-strokes make roughly 2× the power of same-displacement 4T (power
        # stroke every rev). Top-end race 2T (TZ250, RS125 GP) easily exceed
        # HP_PER_CC_MAX; widen the upper sanity bound for them.
        hp_cc_max = HP_PER_CC_MAX * (1.8 if spec.stroke_type == 2 else 1.0)
        if ratio > hp_cc_max:
            warnings.append(
                f"Power/displacement ratio {ratio:.2f} HP/cc is very high "
                f"(max ~{hp_cc_max} for "
                f"{'2T NA' if spec.stroke_type == 2 else '4T NA'}). "
                "Possibly forced induction?"
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

    # ── Auto-fill Cd from category if missing ──────────────────────────
    if spec.cd is None and spec.category in CATEGORY_AERO_DEFAULTS:
        cd, fa = CATEGORY_AERO_DEFAULTS[spec.category]
        spec.cd = cd
        if spec.frontal_area_m2 is None:
            spec.frontal_area_m2 = fa
        corrected["cd"] = cd
        corrected["frontal_area_m2"] = fa

    # ── Gear ratios default if missing ─────────────────────────────────
    if spec.gear_ratios is None and spec.gears:
        if spec.gears == 6:
            spec.gear_ratios = DEFAULT_GEAR_RATIOS_6[:]
            corrected["gear_ratios"] = "default_6speed"
        elif spec.gears == 5:
            spec.gear_ratios = DEFAULT_GEAR_RATIOS_5[:]
            corrected["gear_ratios"] = "default_5speed"

    is_valid = len(errors) == 0
    return ValidationResult(
        is_valid=is_valid,
        warnings=warnings,
        errors=errors,
        corrected_fields=corrected,
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

    # Penalty: 0.03 per warning, 0.10 per error (errors also block import)
    warning_penalty = len(result.warnings) * 0.03
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
