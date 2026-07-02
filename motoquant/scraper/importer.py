"""
MotoQuant Pro — Spec Importer
=============================
Converts validated BikeSpec → BikeConfig and upserts into MotoQuantDB.

Mapping strategy:
  - Known fields map directly to BikeConfig sub-dataclasses
  - Unknown fields fall back to category-appropriate defaults
  - Per-field confidence from BikeSpec flows through to data_provenance table
  - Compression ratio → engine.compression_ratio
  - Tire sizes → TireParams (front/rear size strings only, not Pacejka)
  - Gear ratios → DrivetrainParams (direct list assignment)
  - Power/torque: if dyno_curve not available, synthetic curve is generated
    from peak_power_hp + peak_torque_nm using defaults._synthetic_torque_curve
"""

import logging

from ..defaults import gsxr1000_k5  # used to get default sub-configs
from ..models import (
    AeroParams,
    BikeConfig,
    ChassisParams,
    DrivetrainParams,
    EngineParams,
    TireParams,
)
from .gear_ratios import lookup_gear_ratios
from .spec import BikeSpec, ValidationResult
from .validator import score_spec, validate_spec

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────
# Category-based aerodynamic defaults
# ────────────────────────────────────────────────────────

CATEGORY_AERO = {
    "sport": {"cd": 0.65, "frontal_area_m2": 0.45, "wheelie_tendency": 1.2},
    "naked": {"cd": 0.80, "frontal_area_m2": 0.54, "wheelie_tendency": 0.8},
    "cruiser": {"cd": 0.90, "frontal_area_m2": 0.62, "wheelie_tendency": 0.4},
    "adventure": {"cd": 0.85, "frontal_area_m2": 0.58, "wheelie_tendency": 0.6},
    "touring": {"cd": 0.78, "frontal_area_m2": 0.65, "wheelie_tendency": 0.3},
    "scooter": {"cd": 0.70, "frontal_area_m2": 0.42, "wheelie_tendency": 0.2},
}

# Category-based inertia FALLBACK for engine rotating mass (crankshaft +
# primary drive + clutch basket). Retained only for specs with missing
# cylinder_count or displacement_cc — first choice is the
# displacement-scaled formula below (`_engine_inertia_from_spec`).
#
# These values are sized for K5-class litre I4s and were the ONLY available
# inertia estimate prior to the April 24, 2026 physics fix; applying 0.040
# uniformly to a 155 cc single overstated rotational mass by ~6× and was
# the root cause of the documented small-cc ET bias (+4.73 s avg on the
# 150-300 cc cluster). Historical: validation_sweep 2026-04-22.
CATEGORY_ENGINE_INERTIA = {
    "sport": 0.040,
    "naked": 0.042,
    "cruiser": 0.060,
    "adventure": 0.045,
    "touring": 0.055,
}


def _engine_inertia_from_spec(spec: "BikeSpec") -> float:
    """Displacement-scaled engine rotational inertia, category-modulated.

    Physics derivation
    ------------------
    Crankshaft rotational inertia on a reciprocating IC engine is driven by:
      • Per-cylinder rotating mass (throws, rods, bearings): scales with
        ``bore × stroke`` per cyl, ≈ linear in displacement-per-cyl.
      • Flywheel + primary + clutch basket: sized to the engine's peak
        torque envelope, ≈ linear in total displacement.
      • Engine-character bias: sport bikes use light flywheels so they
        can rev quickly (low rotational inertia is sought after, even at
        the cost of throttle-response smoothness); cruisers and muscle
        bikes deliberately specify HEAVY flywheels for low-rev character
        and smoothness, sometimes 30-50 % more crank-assembly inertia
        than a sport bike of the same displacement.

    Two-term linear decomposition + category factor:

        I = (a · N_cyl + b · V_disp) · k_category

    Fit constants
    -------------
    a = 0.002, b = 0.024, calibrated against published Hayabusa 1340cc I4
    crank-assembly inertia of 0.040 kg·m² (sport factor 1.0):
        Hayabusa 1340cc 4cyl, sport: (0.008 + 0.024·1.340) · 1.0 = 0.040 ✓
        K5 1000cc 4cyl, sport:        (0.008 + 0.024)         · 1.0 = 0.032

    Note K5 catalog value drops from the historical 0.040 → 0.032; the
    `defaults.gsxr1000_k5()` reference function still hardcodes 0.040 for
    the K5 reference benchmark, so K5 ref ET stays at 10.033 s. The
    catalog K5 entry (importer-built) gets the slightly lower value,
    closer to actual measured K5 crankshaft inertia per Suzuki service
    documentation.

    Pre-Apr-24-PM the displacement coefficient was 0.030 (calibrated
    against a stale 0.040 K5 baseline); the resulting formula
    over-counted inertia for ≥1300cc bikes by 15-30 %, slowing the
    catalog Hayabusa 2021, ZX-14R, ZZR1400, and Z H2 sims by 0.2-0.6 s
    relative to their Cycle World / MCN benchmarks.

    Category multiplier k_category
    -------------------------------
    Sport, naked, adventure: 1.00 (baseline)
    Cruiser:                 1.35 (heavy flywheel for low-rev character —
                                   VMAX 1700 V4, Triumph Rocket 3 I3,
                                   Harley Big Twin / M-8)
    Touring:                 1.10 (slightly heavier flywheel for cruise
                                   smoothness)
    Scooter:                 0.70 (CVT primary takes the role of flywheel)

    For two-strokes (piston-port or powervalve) the 0.60× multiplier is
    preserved — no valvetrain, no cams, and typically a lighter flywheel
    because these engines rev quickly and brake-light inertia is desirable.

    Clipped to [0.005, 0.090] kg·m² so a malformed spec can't push the
    coefficient to an absurd value (e.g. 0 cc listing → 0 inertia →
    infinite theoretical acceleration). Upper bound widened from 0.080
    to 0.090 to accommodate 2.5 L cruisers (Rocket 3) with the cruiser
    multiplier.
    """
    cyl = int(spec.cylinders) if spec.cylinders else 1
    disp_cc = float(spec.displacement_cc) if spec.displacement_cc else 0.0
    base = 0.002 * cyl + 0.024 * (disp_cc / 1000.0)

    # Category multiplier — captures engine-character flywheel weighting.
    # Defaults to sport factor (1.0) when category is missing or unknown.
    cat = (spec.category or "sport").lower()
    k_cat = {
        "sport": 1.00,
        "naked": 1.00,
        "adventure": 1.00,
        "touring": 1.10,
        "cruiser": 1.35,
        "scooter": 0.70,
    }.get(cat, 1.00)

    inertia = base * k_cat
    return max(0.005, min(0.090, inertia))


# Category-based CoG height estimate (mm)
CATEGORY_COG_HEIGHT = {
    "sport": 540,
    "naked": 560,
    "cruiser": 620,
    "adventure": 580,
    "touring": 600,
}


def _fluid_mass_from_spec(spec: "BikeSpec") -> float:
    """Displacement-scaled fluid payload (fuel + oil + coolant) in kg.

    Apr-24-PM kaizen: pre-fix ``_build_chassis_from_spec`` hardcoded
    ``fluid_mass_kg = 17.0`` (K5 reference) for every spec'd bike. For
    small-cc commuters whose real fuel+oil+coolant payload is 8-10 kg,
    that added 7-9 kg of phantom chassis mass, visible as a ~0.5 s ET
    penalty on 19 s small-cc sims. Reference K5/R1/Hayabusa are hand-
    built in ``defaults.py`` and NOT affected by this function.

    Formula: ``clip(8.0 + 0.009 x disp_cc, 7.0, 22.0)`` -- calibrated so
    1000 cc -> 17.0 kg (matches K5) and 155 cc -> 9.4 kg (matches real
    R15 V3 fuel + oil + coolant payload).
    """
    disp_cc = float(spec.displacement_cc) if spec.displacement_cc else 1000.0
    fluid = 8.0 + 0.009 * disp_cc
    return max(7.0, min(22.0, fluid))


def _basket_inertia_from_spec(spec: "BikeSpec") -> float:
    """Displacement-scaled clutch-basket rotational inertia (kg.m^2).

    Apr-24-PM kaizen: pre-fix ``spec_to_bike_config`` inherited K5's
    ``basket_inertia_kgm2 = 0.010`` for every bike via
    ``base_config.clutch``. The basket inertia is reflected to the
    wheel by ``(i_total / r_w)^2``. For R15 V3 in gear 1 that factor
    is 2478, so the 0.010->0.0015 over-estimate becomes ~21 kg of
    phantom rotational mass on the wheel -- ~9 % of effective mass in
    gear 1, a real ~0.5 s ET penalty. Reference K5/R1/Hayabusa hand-
    built configs in ``defaults.py`` keep their own basket_inertia
    values and are unaffected.

    Formula: ``clip(0.00001 x disp_cc, 0.0010, 0.020)``. Calibrated so
    1000 cc -> 0.010 kg.m^2 (matches K5 hand-built).
    """
    disp_cc = float(spec.displacement_cc) if spec.displacement_cc else 1000.0
    inertia = 0.00001 * disp_cc
    return max(0.0010, min(0.020, inertia))


# ────────────────────────────────────────────────────────
# Cylinder-config inference for parts-compatibility fitment
# ────────────────────────────────────────────────────────
# Manufacturers whose 2-cylinder engines are V-twins (90° or 45°/60° V)
# rather than parallel twins. Used when a spec lists cylinders=2 without
# an explicit engine_config.
_V_TWIN_2CYL_MAKES = {
    "Ducati",
    "Harley-Davidson",
    "Harley Davidson",
    "Harley",
    "HD",
    "Indian Motorcycle",
    "Indian",  # DB stores as plain "Indian"
    "Moto Guzzi",
    "Buell",
    "Victory",
    "Hyosung",
}

# Specific 2-cylinder bikes whose manufacturer isn't exclusively V-twin but
# the named model is (e.g. Suzuki SV650, Honda's Shadow line, KTM's LC8 series).
_V_TWIN_MODEL_TOKENS = {
    "SV650",
    "SV1000",
    "Shadow",
    "VT750",
    "VT1100",
    "VT1300",
    "1190",
    "1290",
    "LC8",
    "RC8",
    "Ducati",  # Ducati as fallback
    "V7",
    "V9",
    "California",  # Moto Guzzi (also covered by make)
    "VTR",  # Honda VTR250/VTR1000F/VTR1000 SP1/SP2 are all 90-deg V-twins
    "RC51",  # US name for the VTR1000 SP1/SP2 RC51 homologation V-twin
}

# 4-cylinder V4 models (rest are assumed I4).
_V4_MODEL_TOKENS = {
    "Panigale V4",
    "Streetfighter V4",
    "Multistrada V4",
    "Diavel V4",
    "RSV4",
    "Tuono V4",
    "VFR1200",
    "VFR800",
    "RC213V",  # Honda RC213V-S — MotoGP-derived 90-deg V4
    "RC8",
}


def _infer_cylinder_config(spec: "BikeSpec") -> str | None:
    """
    Infer the cylinder configuration (I4/V4/V2/I2/I1/I3/I6) from a BikeSpec.

    Used to populate EngineParams.cylinder_config at import time so the
    parts-compatibility engine can filter fitment by engine family.
    Returns None if the cylinder count isn't known — callers should leave
    the field unset rather than guess.
    """
    cyls = spec.cylinders
    if cyls is None:
        return None

    make = (spec.manufacturer or "").strip()
    model = spec.model_name or ""

    if cyls == 1:
        return "I1"
    if cyls == 2:
        # V-twin vs parallel twin discrimination
        if make in _V_TWIN_2CYL_MAKES:
            return "V2"
        for tok in _V_TWIN_MODEL_TOKENS:
            if tok in model:
                return "V2"
        return "I2"
    if cyls == 3:
        return "I3"
    if cyls == 4:
        for tok in _V4_MODEL_TOKENS:
            if tok in model:
                return "V4"
        return "I4"
    if cyls == 6:
        # Honda Gold Wing / BMW K1600 are flat-6 / I6 respectively;
        # not critical for drag compatibility, best-guess I6.
        if make == "Honda" and "Gold Wing" in model:
            return "flat_6"
        return "I6"
    return None


# ────────────────────────────────────────────────────────
# Chain pitch inference (428 / 520 / 525 / 530 / None=belt/shaft)
# ────────────────────────────────────────────────────────

# Makes that predominantly ship belt on larger models (whole-fleet exclusion)
_BELT_DRIVE_MAKES = {"Indian Motorcycle", "Victory"}
# Harley-Davidson is belt drive EXCEPT for Bajaj-built single-cylinder X440 (chain)
# and Buell uses belt.
_HD_CHAIN_MODELS = {"X440"}

# BMW-specific: R-series boxer and K-series inline-4 are shaft drive;
# S1000/F-series parallel-twin/G-series are chain drive.
_BMW_SHAFT_MODELS = {
    "R 1250",
    "R1250",
    "R 1200",
    "R1200",
    "R nineT",
    "K 1600",
    "K1600",
    "K 1300",
    "K1300",
}
# Moto Guzzi V-twins are shaft drive
_MG_SHAFT_MODELS = {"V7", "V9", "V85", "California", "Griso", "Stelvio"}

# Individual chain-drive-excluded models from chain-drive makes (edge cases)
_NON_CHAIN_MODELS = {
    "VMAX",  # Yamaha VMAX 1700 — shaft drive
    "Gold Wing",  # Honda Gold Wing — shaft drive
    "1125R",  # Buell 1125R — belt drive
    "CB1100",  # Honda CB1100 — shaft drive (the retro 4)
}
# Models with explicit 530 pitch (mostly 1300cc+ drag platforms, older litre sport)
_530_PITCH_MODELS = {"Hayabusa", "ZX-14R", "ZZR1400", "ZRX1200"}
# Models with explicit 428 pitch (SE Asia cubs / underbones / <150cc)
_428_PITCH_MODELS = {
    "RS150R",
    "Winner X",
    "Supra GTR",
    "Sonic 150R",
    "Y15ZR",
    "Exciter 150",
    "Exciter 155",
    "Xpulse 200",  # Hero Xpulse uses 428 stock
}


def _infer_chain_pitch(spec: "BikeSpec") -> str | None:
    """
    Infer the standard chain pitch code (428 / 520 / 525 / 530) from a BikeSpec.

    Returns None for belt or shaft drive bikes, and for bikes with unknown
    displacement. Chain pitch is needed by the parts compatibility engine so
    sprocket/chain fitment rules can target the correct bikes.

    Rules (coarse but accurate for drag-relevant catalogs):
      • Belt/shaft drive makes → None (Harley, Indian, BMW boxer, Moto Guzzi)
      • Explicit model hits (Hayabusa/ZX-14R → "530"; SE Asia 150s → "428")
      • ≤165cc → "428" (most Indian/SE Asia small-cc)
      • 166–499cc → "520"
      • 500–999cc → "520" (modern sport) / "525" (older litre)
      • 1000–1299cc → "525"
      • ≥1300cc → "530"
    """
    make = (spec.manufacturer or "").strip()
    model = spec.model_name or ""
    cc = spec.displacement_cc

    # Belt / shaft drive exclusions
    if make in _BELT_DRIVE_MAKES:
        return None
    if make == "Harley-Davidson":
        # Harley is belt drive except chain-drive exceptions (Bajaj-built X440)
        if not any(tok in model for tok in _HD_CHAIN_MODELS):
            return None
    if make == "Buell":
        return None  # Buell is belt drive
    if make == "BMW":
        for tok in _BMW_SHAFT_MODELS:
            if tok in model:
                return None
        # BMW chain-drive fleet (S1000/F/G/M series) falls through to disp rules
    if make == "Moto Guzzi":
        for tok in _MG_SHAFT_MODELS:
            if tok in model:
                return None
    for tok in _NON_CHAIN_MODELS:
        if tok in model:
            return None

    # Explicit model overrides
    for tok in _530_PITCH_MODELS:
        if tok in model:
            return "530"
    for tok in _428_PITCH_MODELS:
        if tok in model:
            return "428"

    if cc is None:
        return None

    # Displacement-based rules
    if cc <= 165:
        return "428"
    if cc < 500:
        return "520"
    if cc < 1000:
        # Most modern 600–1000cc sport bikes use 520; older litre 525
        if spec.year_from is not None and spec.year_from < 2005 and cc >= 900:
            return "525"
        return "520"
    if cc < 1300:
        return "525"
    return "530"


# ────────────────────────────────────────────────────────
# Synthetic torque curve builder
# ────────────────────────────────────────────────────────


def _build_engine_from_spec(spec: BikeSpec) -> EngineParams:
    """
    Build an EngineParams from a BikeSpec.
    First checks for a known dyno curve from the dyno_curves library.
    Falls back to synthetic curve generation if no known curve exists.

    For 2-stroke bikes (spec.stroke_type == 2), uses the expansion-chamber
    resonance synthetic curve so the characteristic narrow powerband around
    tuned_rpm is preserved — a 4-stroke parabolic curve would massively
    over-predict low-RPM torque on a 2T.
    """
    from ..defaults import _synthetic_2stroke_torque_curve, _synthetic_torque_curve
    from .dyno_curves import get_dyno_curve

    is_two_stroke = spec.stroke_type == 2

    # Start with K5 defaults as a base (reasonable sport bike values)
    base = gsxr1000_k5().engine

    # Peak power and torque
    #
    # Convention: spec.peak_power_hp is interpreted as WHEEL power (the
    # value the synthetic dyno curve is constrained against). This is
    # the implicit assumption the rest of the physics — particularly the
    # chain efficiency, parasitic loss model, and tire-grip thresholds —
    # has been calibrated around since the original K5 reference baseline
    # was set. Apr-24 experiment with applying a 12 % wheel-loss factor
    # to all catalog crank/marketing values made cluster averages
    # uniformly WORSE (litre +0.14, twin +0.67, 150-300cc +3.49) — the
    # other physics layers were already accounting for drivetrain losses
    # implicitly. Reverted; logged as a potential follow-up if a
    # full physics-stack re-calibration is undertaken.
    peak_hp = spec.peak_power_hp or base.peak_power_hp
    peak_hp_rpm = spec.peak_power_rpm or base.peak_power_rpm

    # Derive peak torque from power if available; else use spec or fallback
    if spec.peak_torque_nm:
        peak_tq = spec.peak_torque_nm
    elif spec.peak_power_hp and spec.peak_power_rpm:
        # T = P / ω, where ω = RPM × 2π / 60
        import math

        peak_tq = (
            spec.peak_power_hp * 745.7 / (spec.peak_power_rpm * 2.0 * math.pi / 60.0)
        )
    else:
        peak_tq = base.peak_torque_nm

    peak_tq_rpm = spec.peak_torque_rpm or base.peak_torque_rpm
    cc = spec.displacement_cc or 1000
    cyls = spec.cylinders or 4

    if spec.peak_power_rpm:
        # Peak power RPM is not the redline; engines continue to rev above it.
        # The headroom varies strongly with engine type:
        #   Large inline-4 / V4 / L-twin (1000cc+): peak at ~93% of redline → ×1.08
        #   600cc inline-4 (R6, CBR600, ZX-6R): peak at ~88% → ×1.14
        #   Mid-size parallel twin (<700cc, 2-cyl): peak at ~82% → ×1.22
        #   Small parallel twin / single (<500cc, ≤2-cyl): peak at ~77% → ×1.30
        #   Two-stroke: peak at ~90–92% of redline → ×1.10 (narrow band; over-rev
        #     kills power fast once out of expansion-chamber resonance)
        # This replaces the previous flat 1.08 factor which caused severe redline
        # under-estimation for small-displacement bikes (e.g. Ninja 400 → 10 800 rpm
        # instead of the real ~13 000 rpm, trapping at 119 km/h instead of 150+ km/h).
        if is_two_stroke:
            # 2T over-rev varies strongly with powervalve presence. Power-
            # valved bikes (YPVS/RAVE/HPP/KIPS) have more usable band above
            # peak (NSR250 peak 9500 → redline 12000 = 1.26); naked-pipe bikes
            # fall off fast (RD350 peak 7500 → redline 9500 = 1.27 but
            # power-wise falls into noise by 8500). We split the difference.
            redline_factor = 1.26 if (spec.powervalve) else 1.18
        elif cc < 500 and cyls <= 2:
            redline_factor = 1.30  # small singles / parallel twins
        elif cc < 700 and cyls <= 2:
            # April 22, 2026: raised 1.22 → 1.32 to close systematic slowness
            # bias on 500-700cc parallel twins (SV650, Z650, Ninja 650, MT-07,
            # CB650R, Trident 660, YZF-R7, RS 457, TNT 600i). Real redlines on
            # this class sit at 10 500 – 11 000 rpm with peak power at 8 000–
            # 8 500 rpm, giving a ratio of ~1.30–1.35. The old 1.22 under-
            # estimated top-gear pull and forced premature upshifts that
            # truncated trap-speed and pushed validation deltas +0.5 to +1.25 s.
            redline_factor = 1.32  # mid-size twins (MT-07, Z650, Dominar 400)
        elif cc < 700:
            redline_factor = 1.14  # 600cc-class inline-4 (R6, CBR600RR, ZX-6R)
        elif spec.category in ("cruiser", "touring", "muscle"):
            # Big-bore V-twins and muscled-up engines (VMAX 1700, Rocket 3, etc)
            # peak power at ~60% of redline — strong off-boost character
            if cc >= 1400:
                redline_factor = 1.30  # VMAX 1700, Rocket 3 — peak power lower
            elif cc >= 1200:
                redline_factor = 1.22  # Panigale V4, larger cruiser V-twins
            else:
                redline_factor = 1.10  # fallback
        else:
            redline_factor = 1.10  # large inline-4, V4, L-twin (≥ 1000cc class)
        redline = int(peak_hp_rpm * redline_factor)
    else:
        redline = base.redline_rpm
    # 2-strokes idle higher (needs transfer port gas velocity to sustain firing)
    idle = 1800 if is_two_stroke else 1200

    # Tuned RPM for 2T: prefer explicit, else compute from peak_power_rpm
    # Expansion chambers peak below peak-power RPM (~0.82 factor)
    if spec.tuned_rpm:
        tuned_rpm = spec.tuned_rpm
    elif is_two_stroke and spec.peak_power_rpm:
        tuned_rpm = int(spec.peak_power_rpm * 0.82)
    else:
        tuned_rpm = peak_hp_rpm if is_two_stroke else None

    # Try to find a known dyno curve for this bike
    dyno = get_dyno_curve(
        manufacturer=spec.manufacturer,
        model=spec.model_name,
        year=spec.year_from,
        model_code=spec.model_code,
    )

    # If no known curve found, generate a synthetic one based on peak power/torque
    if dyno is None:
        if is_two_stroke:
            dyno = _synthetic_2stroke_torque_curve(
                peak_torque_nm=float(peak_tq),
                tuned_rpm=float(tuned_rpm or peak_hp_rpm),
                redline_rpm=float(redline),
                idle_rpm=float(idle),
                powervalve=bool(spec.powervalve),
                peak_power_hp=float(peak_hp),
                peak_power_rpm=float(peak_hp_rpm),
                cylinders=int(cyls or 1),
                displacement_cc=float(cc),
                points=100,
            )
        else:
            dyno = _synthetic_torque_curve(
                peak_torque_nm=float(peak_tq),
                peak_rpm=float(peak_tq_rpm),
                redline_rpm=float(redline),
                idle_rpm=float(idle),
                peak_power_hp=float(peak_hp),
                peak_power_rpm=float(peak_hp_rpm),
                points=100,
            )

    # 2-strokes have much lower rotating inertia (no valvetrain, lighter crank)
    # — use ~60% of the category default, which changes launch RPM-drop behaviour.
    # Displacement-scaled engine rotational inertia — physics-derived
    # two-term formula (see `_engine_inertia_from_spec` docstring). The
    # legacy CATEGORY_ENGINE_INERTIA lookup remains as fallback if the
    # spec doesn't carry displacement info; the new formula always wins
    # when displacement_cc is populated (which is true for every entry in
    # ALL_KNOWN_BIKES after the April 20 catalog expansion).
    base_inertia = (
        _engine_inertia_from_spec(spec)
        if (spec.cylinders and spec.displacement_cc)
        else CATEGORY_ENGINE_INERTIA.get(spec.category, 0.042)
    )
    engine_inertia = base_inertia * 0.60 if is_two_stroke else base_inertia

    return EngineParams(
        dyno_curve=dyno,
        peak_power_hp=float(peak_hp),
        peak_torque_nm=float(peak_tq),
        peak_power_rpm=int(peak_hp_rpm),
        peak_torque_rpm=int(peak_tq_rpm),
        redline_rpm=int(redline),
        launch_rpm=int(peak_tq_rpm)
        if spec.displacement_cc and spec.displacement_cc < 400
        else int(
            redline * 0.55
        ),  # Apr-27: <400cc launches at peak_torque_rpm (max torque available); >400cc at 55% of redline
        idle_rpm=idle,
        displacement_cc=spec.displacement_cc or base.displacement_cc,
        bore_mm=spec.bore_mm or base.bore_mm,
        stroke_mm=spec.stroke_mm or base.stroke_mm,
        compression_ratio=spec.compression_ratio or base.compression_ratio,
        engine_inertia_kgm2=engine_inertia,
        cylinder_count=spec.cylinders,
        cylinder_config=_infer_cylinder_config(spec),
        stroke_type=(2 if is_two_stroke else 4),
        tuned_rpm=(float(tuned_rpm) if tuned_rpm else None),
        expansion_chamber=bool(spec.expansion_chamber),
        reed_valve=bool(spec.reed_valve),
        powervalve=bool(spec.powervalve),
    )


def _build_chassis_from_spec(spec: BikeSpec) -> ChassisParams:
    """Build ChassisParams from a BikeSpec.

    Apr-24-PM kaizen: ``fluid_mass_kg`` and ``fuel_mass_kg`` were both
    K5-default constants (17 and 18 kg) applied to every bike regardless
    of size. That overcharged ~7-9 kg of phantom mass to every <300 cc
    commuter, a real ET penalty of ~0.5 s on a 19 s small-cc sim. Both
    now scale with displacement via ``_fluid_mass_from_spec``.
    K5/R1/Hayabusa reference baselines are hand-built in ``defaults.py``
    and unaffected.
    """
    base = gsxr1000_k5().chassis

    dry_mass = spec.dry_mass_kg or spec.wet_mass_kg or base.dry_mass_kg
    # If only wet mass available, estimate dry as wet - 25 kg (fluids)
    if spec.dry_mass_kg is None and spec.wet_mass_kg:
        dry_mass = spec.wet_mass_kg - 25.0

    fluid_mass = _fluid_mass_from_spec(spec)
    # fuel_mass_kg is a decorative field (the live consumed mass during
    # the sim is tracked separately via fuel_consumption_gs); keep it in
    # rough sync with fluid_mass so UIs showing "fuel weight" don't lie.
    # Use spec value when given, else displacement-scaled estimate.
    if spec.fuel_capacity_l:
        fuel_mass = float(spec.fuel_capacity_l) * 0.74
    else:
        disp = float(spec.displacement_cc) if spec.displacement_cc else 1000.0
        fuel_l = max(7.0, min(22.0, 7.0 + 0.011 * disp))
        fuel_mass = fuel_l * 0.74

    return ChassisParams(
        dry_mass_kg=float(dry_mass),
        rider_mass_kg=75.0,
        fluid_mass_kg=float(fluid_mass),
        fuel_mass_kg=float(fuel_mass),
        wheelbase_mm=float(spec.wheelbase_mm or base.wheelbase_mm),
        cog_height_mm=float(CATEGORY_COG_HEIGHT.get(spec.category, 540)),
        seat_height_mm=float(spec.seat_height_mm or base.seat_height_mm),
    )


def _build_drivetrain_from_spec(
    spec: BikeSpec, engine: EngineParams
) -> DrivetrainParams:
    """
    Build DrivetrainParams from BikeSpec.

    Priority:
      1. Service-manual ratios on the spec (gear_ratios list, front/rear sprockets)
      2. gear_ratios.lookup_gear_ratios() — Tier 1 named-model lookup (conf 0.75)
         then Tier 2 category+displacement defaults (conf 0.30–0.45)
      3. Legacy gsxr1000_k5 base defaults (last resort)
    """
    base = gsxr1000_k5().drivetrain

    ratios = spec.gear_ratios
    front = spec.front_sprocket
    rear = spec.rear_sprocket
    primary = spec.primary_ratio

    # ALWAYS run the gear-ratio lookup — not just when ratios are missing.
    # A bike can ship real service-manual gear ratios but no primary_ratio
    # field, in which case falling back to the K5 base primary (1.553) is
    # catastrophic for non-superbikes: CB650R's real 2.176 primary becomes
    # 1.553, which makes gear 1 top-out at ~145 km/h instead of ~95 km/h
    # and the sim lugs the entire quarter in first gear. See the April 22
    # mid-range audit (CLAUDE.md) for the full diagnosis.
    lu_ratios, lu_front, lu_rear, lu_primary, _conf = lookup_gear_ratios(
        manufacturer=spec.manufacturer,
        model_name=spec.model_name,
        year=spec.year_from,
        category=spec.category,
        displacement_cc=spec.displacement_cc,
        gears=spec.gears,
    )
    if not ratios:
        ratios = lu_ratios
    front = front or lu_front
    rear = rear or lu_rear
    primary = primary or lu_primary

    front = front or base.front_sprocket
    rear = rear or base.rear_sprocket
    primary = primary or base.primary_ratio

    pitch = _infer_chain_pitch(spec)
    # Pitch in mm: 428 = 12.7, 520 = 15.875, 525 = 15.875, 530 = 15.875.
    # Only the nominal roller width differs materially for mass/drag — map to
    # the most common mm values so sim consumers that read chain_pitch_mm stay
    # accurate. Use 12.7 for 428, 15.875 for 520/525/530 (the differences are
    # roller width, not pitch).
    chain_pitch_mm = 12.7 if pitch == "428" else base.chain_pitch_mm

    # Naked bikes across 500-700cc have thinner chains and efficiency losses
    # similar to small-cc despite larger displacement
    cc = spec.displacement_cc or 1000
    if cc < 700 and (spec.category or "sport").lower() in ("sport", "naked"):
        chain_eff = 0.95  # aggressive for small/mid naked bikes
    else:
        chain_eff = base.chain_efficiency  # full-size default (0.97)

    return DrivetrainParams(
        gear_ratios=list(ratios),
        final_drive_ratio=float(rear) / float(front),
        front_sprocket=int(front),
        rear_sprocket=int(rear),
        chain_pitch_mm=chain_pitch_mm,
        chain_pitch=pitch,
        chain_links=base.chain_links,
        primary_ratio=float(primary),
        chain_efficiency=chain_eff,
    )


def _build_tires_from_spec(spec: BikeSpec) -> TireParams:
    """Build basic TireParams from tire size strings.

    Uses category-aware mu_peak defaults:
    - Sport/superbike race tires: mu_peak=1.40 (Pirelli SC / Michelin Power GP)
    - Naked/streetfighter: mu_peak=1.35 (sport-touring compounds)
    - Indian-market entry-level (<300cc): mu_peak=1.15 (MRF/CEAT budget rubber)
    - Indian-market mid (300-500cc): mu_peak=1.25 (MRF Zapper-C / Pirelli Angel)
    - Cruiser: mu_peak=1.20 (touring compounds, heavier)
    - Adventure: mu_peak=1.15 (knobby/trail rubber)
    """
    base = gsxr1000_k5().tires

    # Category + displacement-aware mu_peak selection
    # Sport superbikes keep the K5 default (1.4) — validated against real data.
    # Only lower mu for genuinely lower-compound tires.
    disp = spec.displacement_cc or 1000
    cat = (spec.category or "sport").lower()

    if cat in ("sport", "naked") and disp >= 600:
        mu = base.mu_peak  # 1.4 — race/sport compound (validated for superbikes)
    elif cat in ("sport", "naked") and disp >= 500:
        mu = 1.30  # 500-600cc sport/naked (SV650, Z650, MT-07 class) — verified sticky radials
    elif cat in ("sport", "naked") and disp >= 300:
        mu = 1.15  # 300-500cc middleweight sport (Ninja 400, R3, RC 390, Duke 390)
        # 2026-05-25 calibration: lowered from 1.30 to 1.15 — benchmark sweep on
        # 13 matched mid-twin-300-500 bikes showed mu=1.30 made KTM/RC 390, RS 457
        # ~0.6-0.9s too fast. Real bikes run stock Metzeler Sportec M5 / MRF Revz /
        # Pirelli Diablo Street (NOT superbike-grade race rubber). mu=1.15 reduces
        # cluster mean|Δ| from 0.564s → 0.499s (-65ms, crosses 50ms improvement gate).
    elif cat in ("sport", "naked") and disp < 300:
        mu = 1.15  # entry-level budget tires (R15, Duke 200, Pulsar)
    elif cat in ("cruiser", "adventure") and (spec.peak_power_hp or 0.0) >= 165:
        # Sport-derived muscle cruisers / crossover ADVs (Diavel V4, Rocket 3
        # Storm R, Multistrada V4/RS, S1000XR) ship on sport / sport-touring
        # radials (Diablo Rosso III, Scorpion Trail II, 240-section rears) --
        # NOT the touring/knobby compounds the category defaults assume.
        # 2026-07-02 forensics: category-default grip left these rear-traction
        # starved at launch (60ft 2.1s+ vs real ~1.65s), uniformly +0.5..+0.8s
        # slow vs instrumented benchmarks. Gate at 165hp so genuine ADVs on
        # trail rubber (1290 SAR 160hp, Pan America 150hp) keep the default.
        mu = 1.40 if cat == "cruiser" else 1.32
    elif cat == "cruiser":
        mu = 1.20  # touring compound, heavier loads
    elif cat == "adventure":
        mu = 1.15  # knobby/trail rubber
    elif cat == "touring":
        mu = 1.18  # touring compound
    else:
        mu = base.mu_peak  # fallback to K5 default

    # Small-cc bikes have higher rolling resistance (skinnier tires, higher pressure)
    # 500-700cc naked bikes also need elevated rolling resistance (not as much as <500 though)
    crr = base.crr_base  # base is 0.012
    if disp < 500:
        crr = 0.013  # small-cc aggressive bump
    elif disp < 700 and cat in ("sport", "naked"):
        crr = 0.0135  # 500-700cc naked/sport: higher CRR (fatter tires at lower pressures)

    result = TireParams(
        front_size=spec.front_tire_size or base.front_size,
        rear_size=spec.rear_tire_size or base.rear_size,
        mu_peak=mu,
        pacejka_B=base.pacejka_B,
        pacejka_C=base.pacejka_C,
        pacejka_D=base.pacejka_D,
        pacejka_E=base.pacejka_E,
        optimal_temp_c=base.optimal_temp_c,
        crr_base=crr,
    )

    # Estimate rolling radius from rear tire size
    if spec.rear_tire_size:
        import re

        m = re.match(r"(\d{3})/(\d{2})", spec.rear_tire_size)
        if m:
            width_mm = float(m.group(1))
            aspect = float(m.group(2)) / 100.0
            sidewall = width_mm * aspect
            # Rim diameter: last 2 digits × 25.4 / 2
            # Match rim diameter: e.g. "ZR17", plain "R17"/"B16"
            # (150/80R16, 240/40R18 -- the single-letter radial/bias code
            # used across the cruiser catalog), or hyphenated "-17".
            # 2026-07-02: the old [ZRB]R pattern required TWO letters, so
            # 32 bikes on non-17" rims (Sportster S 16", Rocket 3 16",
            # Boulevard M109R 18", ...) silently fell to the 17" default.
            rim_m = re.search(r"[ZRB]R(\d{2})\b", spec.rear_tire_size, re.IGNORECASE)
            if not rim_m:
                rim_m = re.search(r"[RB](\d{2})\b", spec.rear_tire_size, re.IGNORECASE)
            if not rim_m:
                rim_m = re.search(r"-(\d{2})\b", spec.rear_tire_size)
            rim_half = (int(rim_m.group(1)) * 25.4 / 2) if rim_m else 215.9
            result.rear_rolling_radius_m = (rim_half + sidewall) / 1000.0

    return result


def _build_aero_from_spec(spec: BikeSpec) -> AeroParams:
    """Build AeroParams from spec or category defaults.

    Critical convention: ``spec.cd`` is the **rider-tuck Cd** (the value the
    bike+rider system presents during a high-speed run with the rider
    tucked behind the fairing, knees against the tank, chin on the tank).
    The rider_dynamics submodel multiplies by 1.18× for the upright launch
    position and interpolates back down to ``spec.cd`` over
    ``tuck_transition_time_s``.

    Reference tuck Cds in the catalog (all faired sport bikes):
      Suzuki GSX-R 1000 K5     0.32
      Yamaha YZF-R1 (4C8)      0.33
      Suzuki Hayabusa Gen1     0.31
      Kawasaki ZX-10R modern   0.34

    These match published wind-tunnel data for full-fairing sport bikes
    in tuck position. Cd is dominated by fairing GEOMETRY, not engine
    displacement — a properly-faired R15 in the same rider position has
    Cd around 0.40 (slightly higher than K5 because rider is closer to
    the size of the bike, exposing more of their back to the airstream).

    Pre-April-24 the sub-500cc ``sport`` defaults here were `cd=0.72` —
    that's an UPRIGHT Cd. Combined with the rider_dynamics 1.18× upright
    multiplier, the launch-phase effective Cd was 0.85, ~2.6× what a
    K5-class bike sees. This single error contributed about 1-1.5 s to
    the small-cc-class ET bias (validated by perturbation: scaling Cd
    by 0.5 on R15 V3 dropped ET by 0.33 s in earlier sensitivity sweep,
    and the proper tuck value is roughly 0.55× the upright spec value).

    Fix: enforce a tuck-Cd ceiling of 0.45 for sport-class bikes
    regardless of displacement. The sub-500cc default drops from 0.72
    (upright) to 0.42 (tuck). Per-spec values from known_bikes.py that
    look like upright Cds (>0.45 for sport class) are normalized down to
    the tuck range using a 0.55× scale factor (calibrated from the
    upright/tuck ratio measured on K5-class bikes).
    """
    aero_defaults = CATEGORY_AERO.get(spec.category, CATEGORY_AERO["sport"])
    base = gsxr1000_k5().aero
    cc = spec.displacement_cc or 1000

    # Small-cc sub-gate: tighter sport-tuck Cd for sub-500cc faired bikes.
    # Naked bikes don't have a fairing to tuck behind — keep their drag
    # numbers as-is (sitting upright is their physical reality regardless
    # of what the rider does).
    if cc < 500:
        if spec.category == "naked":
            aero_defaults = {
                "cd": 0.86,
                "frontal_area_m2": 0.55,
                "wheelie_tendency": 0.8,
            }
        elif spec.category == "sport":
            # Tuck Cd for a faired small-cc sport bike — slightly higher
            # than K5's 0.32 because the smaller fairing leaves more of
            # the rider exposed.
            aero_defaults = {
                "cd": 0.42,
                "frontal_area_m2": 0.46,
                "wheelie_tendency": 1.2,
            }

    cd = spec.cd if spec.cd is not None else aero_defaults["cd"]

    # Tuck-Cd normalization for sport-class bikes: spec.cd values from
    # the known_bikes catalog were inadvertently populated with upright
    # values for several sub-500cc sport bikes (R15 V3 0.56, RC 390
    # 0.68, etc.). Normalize them back to the tuck regime so the rider-
    # dynamics 1.18× upright multiplier doesn't double-inflate drag
    # during the launch phase.
    if spec.category == "sport" and cd > 0.45:
        cd_normalized = max(0.30, cd * 0.55)
        cd = cd_normalized

    return AeroParams(
        cd=cd,
        frontal_area_m2=spec.frontal_area_m2 or aero_defaults["frontal_area_m2"],
        # All other aero params stay at base defaults
        cl=base.cl,
        rider_position=base.rider_position,
        belly_pan=base.belly_pan,
        ram_air_efficiency=base.ram_air_efficiency,
        ram_air_area_cm2=base.ram_air_area_cm2,
        headwind_ms=base.headwind_ms,
        crosswind_ms=base.crosswind_ms,
    )


def spec_to_bike_config(spec: BikeSpec) -> BikeConfig:
    """
    Convert a validated BikeSpec to a BikeConfig.

    Uses category-appropriate defaults for any fields not present in the spec.
    Physics-critical fields (gear ratios, tire friction, aero) get defaults
    if not available from the scrape, with lower confidence.

    Returns a BikeConfig ready for simulation.
    """
    base_config = gsxr1000_k5()  # use as default template

    engine = _build_engine_from_spec(spec)
    chassis = _build_chassis_from_spec(spec)
    drivetrain = _build_drivetrain_from_spec(spec, engine)
    tires = _build_tires_from_spec(spec)
    aero = _build_aero_from_spec(spec)

    # ── Staging: override for 2-strokes ─────────────────────────────────
    # K5-default launch_rpm=7000 is fine for a litre I4 (peak torque ~10k,
    # 7k is a sensible clutch-dump RPM). For a 2-stroke it's a disaster —
    # RD350 at 7000 rpm is off-pipe (≈ 40% of peak torque) and the sim
    # simply cannot get the bike moving from the staging window. In real
    # drag racing, 2T riders launch with the clutch slipping at or above
    # the pipe's tuned RPM. We reproduce that by setting launch_rpm to
    # tuned_rpm × 0.92 (gives slight headroom before the pipe comes on).
    import copy

    staging = copy.deepcopy(base_config.staging)
    # Apr-27: Small-cc 4T launch optimization — launch at peak_torque_rpm where torque peaks,
    # not at 55% redline (which is for 1000cc superbikes). Small bikes are torque-limited.
    if spec.stroke_type != 2 and spec.displacement_cc and spec.displacement_cc < 400:
        staging.launch_rpm = float(engine.peak_torque_rpm)
    elif spec.stroke_type == 2:
        # Apr-24-PM kaizen: previous ``tuned * 0.92`` put commuter 2T
        # launches (RX100 peak_tq=6500, tuned=7500 -> launch=6900) BELOW
        # peak-torque RPM, firing off the rising edge of the Gaussian
        # band at half available torque. Fixed: clamp launch_rpm at the
        # maximum of (peak_torque_rpm, tuned_rpm), capped at 96 % of
        # redline so the rev-limiter doesn't fire at the staging beam.
        tuned = float(spec.tuned_rpm or spec.peak_power_rpm or engine.peak_power_rpm)
        peak_tq = float(spec.peak_torque_rpm or engine.peak_torque_rpm)
        launch = max(peak_tq, tuned)
        launch = min(launch, float(engine.redline_rpm) * 0.96)
        staging.launch_rpm = float(int(launch))
        staging.two_step = True  # 2T drag launches almost always use a limiter

    # Parasitic: 2-strokes have no valvetrain; pre-mix bikes have no oil
    # pump at all, oil-injected 2Ts have a tiny one. Collapse those losses.
    # Displacement-scaled parasitic losses.
    #
    # Oil-pump and valve-train power loss both scale ≈ linearly with
    # engine displacement: oil-pump volumetric flow ≈ Vd × N (pump
    # displacement per crank turn × rpm), valve-train friction ≈
    # cylinder count × valve count × spring force × peak velocity.
    # K5 baseline (1000cc I4) is the calibration point:
    #   oil_pump_power_w  = 500  → coefficient 0.50 W/cc
    #   valve_train_power = 250  → coefficient 0.25 W/cc
    # Alternator power is dominated by ELECTRICAL LOAD (lights, ECU,
    # ignition, accessories), not engine size — kept roughly flat
    # across displacement classes with a mild downscale for the
    # smallest commuter electrics (no quickshifter motor, no heated
    # grips, simpler ECU).
    #
    # Pre-fix the small-cc 4T branch hardcoded oil_pump=300, valve=150
    # — that's 60 % and 60 % of the K5 values applied to a 155 cc
    # engine that displaces 15 % of K5's volume. Net: parasitic
    # losses on a 155 cc R15 were 510 W out of 14 400 W peak power
    # (3.5 %), vs the physically-correct ~150 W (1.0 %). The extra
    # 360 W = 0.48 hp robbed from a small-cc bike's quarter-mile pull.
    parasitic = copy.deepcopy(base_config.parasitic)
    if spec.stroke_type == 2:
        # 2T: no valvetrain (port timing in cylinder walls), no oil
        # pump on Autolube/premix systems, possibly no water pump on
        # air-cooled vintage 2Ts.
        parasitic.valve_train_power_w = 0.0
        parasitic.oil_pump_power_w = 60.0  # micro premix pump
        if spec.cooling == "air":
            parasitic.water_pump_electric = True
    elif spec.displacement_cc:
        disp = float(spec.displacement_cc)
        # Linear scaling with K5 calibration. Floor at 30 / 20 W keeps
        # the smallest 100 cc cubs from having near-zero (which would
        # be physically wrong — an oil pump still has to overcome
        # spring + bearing drag at minimum).
        parasitic.oil_pump_power_w = max(30.0, 0.50 * disp)
        parasitic.valve_train_power_w = max(20.0, 0.25 * disp)
        # Alternator: K5 default 150 W. Small-cc commuters typically
        # 60-80 W, mid-size 80-120 W, litre and up 150 W.
        if disp < 300:
            parasitic.alternator_power_w = 60.0
        elif disp < 700:
            parasitic.alternator_power_w = 80.0
        elif disp < 1000:
            parasitic.alternator_power_w = 120.0
        # else: leave at K5 base default 150 W

    # ── Clutch: scale basket inertia with displacement ──────────────
    # Apr-24-PM kaizen: K5 default ``basket_inertia=0.010 kg.m^2`` is
    # a 1000 cc-I4 figure. Applied unchanged to a 155 cc R15 V3 single
    # it inflates effective mass at the wheel by ~21 kg in gear 1 --
    # a real ~0.5 s ET penalty. Reference K5/R1/Hayabusa hand-built
    # configs in ``defaults.py`` keep their original basket_inertia
    # values and are unaffected.
    clutch = copy.deepcopy(base_config.clutch)
    clutch.basket_inertia_kgm2 = _basket_inertia_from_spec(spec)

    # Compose model name
    year_tag = ""
    if spec.year_from:
        year_tag = f" ({spec.year_from})"
        if spec.year_to and spec.year_to != spec.year_from:
            year_tag = f" ({spec.year_from}-{spec.year_to})"

    name = f"{spec.manufacturer} {spec.model_name}{year_tag}"

    # Auto-derive the category_tag for cluster-flavoured physics dispatch.
    # See motoquant.category_profiles.derive_category_tag — mirrors
    # scripts/sweep_with_clusters.py::cluster_for so benchmark grouping and
    # physics dispatch share one taxonomy.
    from ..category_profiles import derive_category_tag

    category_tag = derive_category_tag(
        manufacturer=spec.manufacturer,
        model_name=spec.model_name,
        displacement_cc=spec.displacement_cc,
        peak_power_hp=spec.peak_power_hp,
        stroke_type=spec.stroke_type,
        category=spec.category,
    )

    return BikeConfig(
        name=name,
        category_tag=category_tag,
        engine=engine,
        chassis=chassis,
        drivetrain=drivetrain,
        tires=tires,
        aero=aero,
        # Retain all other sub-configs at defaults
        forced_induction=base_config.forced_induction,
        clutch=clutch,
        suspension=base_config.suspension,
        braking=base_config.braking,
        wheelie=base_config.wheelie,
        rider=base_config.rider,
        parasitic=parasitic,
        staging=staging,
        environment=base_config.environment,
    )


# ────────────────────────────────────────────────────────
# DB import
# ────────────────────────────────────────────────────────


def import_spec(
    db,  # MotoQuantDB
    spec: BikeSpec,
    validation_result: ValidationResult | None = None,
    dry_run: bool = False,
) -> tuple[int, int] | None:
    """
    Import a BikeSpec into MotoQuantDB.

    Steps:
      1. Validate (if not already done)
      2. Convert to BikeConfig via spec_to_bike_config()
      3. Upsert manufacturer + model + config
      4. Write per-field provenance records
      5. Return (model_id, config_id) or None if invalid / dry_run

    Args:
        db:                MotoQuantDB instance (initialized)
        spec:              BikeSpec to import
        validation_result: Pre-computed result (skip re-validation if provided)
        dry_run:           If True, validate but don't write to DB

    Returns:
        (model_id, config_id) on success, None on failure.
    """
    if validation_result is None:
        validation_result = validate_spec(spec)

    confidence = score_spec(spec, validation_result)
    validation_result.overall_confidence = confidence

    if not validation_result.is_valid:
        logger.warning(
            f"Skipping invalid spec: {spec.manufacturer} {spec.model_name} — "
            + "; ".join(validation_result.errors)
        )
        return None

    if dry_run:
        logger.info(
            f"[DRY RUN] Would import: {spec.manufacturer} {spec.model_name} "
            f"(conf={confidence:.2f})"
        )
        return None

    try:
        config = spec_to_bike_config(spec)

        model_id, config_id = db.bikes.upsert_from_config(
            config=config,
            manufacturer_name=spec.manufacturer,
            model_code=spec.model_code,
            year_from=spec.year_from,
            year_to=spec.year_to,
            category=spec.category,
            source=spec.source_name,
            confidence=confidence,
        )

        # Write provenance records for each known field
        for field_name, field_conf in spec.field_confidence.items():
            try:
                db.bikes.add_provenance(
                    entity_id=config_id,
                    entity_type="bike_config",
                    field_path=f"scraped.{field_name}",
                    source_type=spec.source_name,
                    source_url=spec.source_url,
                    confidence=field_conf,
                    notes=f"Scraped at {spec.scraped_at}",
                )
            except Exception as e:
                logger.debug(f"Provenance write error for {field_name}: {e}")

        logger.info(
            f"Imported: {spec.manufacturer} {spec.model_name} "
            f"→ model_id={model_id}, config_id={config_id} "
            f"(conf={confidence:.2f})"
        )
        return model_id, config_id

    except Exception as e:
        logger.error(f"Import failed for {spec.manufacturer} {spec.model_name}: {e}")
        return None


def import_batch(
    db,
    specs: list[BikeSpec],
    dry_run: bool = False,
    stop_on_error: bool = False,
) -> dict[str, int]:
    """
    Import a list of BikeSpec objects into the database.

    Delegates each spec to import_spec() so that callers (and tests) can
    monkeypatch import_spec without needing to replace the whole batch function.

    Returns summary counts:
        {"imported": N, "skipped_invalid": N, "errors": N, "dry_run": bool}
    """
    imported = 0
    skipped = 0
    errors = 0

    for spec in specs:
        result = validate_spec(spec)
        score = score_spec(spec, result)
        result.overall_confidence = score

        if not result.is_valid:
            logger.warning(
                f"Invalid: {spec.manufacturer} {spec.model_name} — "
                + "; ".join(result.errors)
            )
            skipped += 1
            continue

        try:
            ids = import_spec(db, spec, result, dry_run)
            if ids is None and not dry_run:
                # import_spec returns None on failure (invalid spec or DB error)
                errors += 1
                if stop_on_error:
                    break
            else:
                imported += 1
        except Exception as e:
            logger.error(f"Error importing {spec.manufacturer} {spec.model_name}: {e}")
            errors += 1
            if stop_on_error:
                raise

    return {
        "imported": imported,
        "skipped_invalid": skipped,
        "errors": errors,
        "dry_run": dry_run,
    }
