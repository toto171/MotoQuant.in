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

# Category-based inertia estimates for engine rotating mass
CATEGORY_ENGINE_INERTIA = {
    "sport": 0.040,
    "naked": 0.042,
    "cruiser": 0.060,
    "adventure": 0.045,
    "touring": 0.055,
}

# Category-based CoG height estimate (mm)
CATEGORY_COG_HEIGHT = {
    "sport": 540,
    "naked": 560,
    "cruiser": 620,
    "adventure": 580,
    "touring": 600,
}


# ────────────────────────────────────────────────────────
# Cylinder-config inference for parts-compatibility fitment
# ────────────────────────────────────────────────────────
# Manufacturers whose 2-cylinder engines are V-twins (90° or 45°/60° V)
# rather than parallel twins. Used when a spec lists cylinders=2 without
# an explicit engine_config.
_V_TWIN_2CYL_MAKES = {
    "Ducati", "Harley-Davidson", "Harley Davidson", "Harley", "HD",
    "Indian Motorcycle", "Indian",  # DB stores as plain "Indian"
    "Moto Guzzi", "Buell", "Victory", "Hyosung",
}

# Specific 2-cylinder bikes whose manufacturer isn't exclusively V-twin but
# the named model is (e.g. Suzuki SV650, Honda's Shadow line, KTM's LC8 series).
_V_TWIN_MODEL_TOKENS = {
    "SV650", "SV1000", "Shadow", "VT750", "VT1100", "VT1300",
    "1190", "1290", "LC8", "RC8", "Ducati",  # Ducati as fallback
    "V7", "V9", "California",  # Moto Guzzi (also covered by make)
}

# 4-cylinder V4 models (rest are assumed I4).
_V4_MODEL_TOKENS = {
    "Panigale V4", "Streetfighter V4", "Multistrada V4",
    "Diavel V4", "RSV4", "Tuono V4",
    "VFR1200", "VFR800",
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
    model = (spec.model_name or "")

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
    "R 1250", "R1250", "R 1200", "R1200", "R nineT",
    "K 1600", "K1600", "K 1300", "K1300",
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
    "RS150R", "Winner X", "Supra GTR", "Sonic 150R",
    "Y15ZR", "Exciter 150", "Exciter 155",
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
    model = (spec.model_name or "")
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
    """
    from ..defaults import _synthetic_torque_curve
    from .dyno_curves import get_dyno_curve

    # Start with K5 defaults as a base (reasonable sport bike values)
    base = gsxr1000_k5().engine

    # Peak power and torque
    peak_hp = spec.peak_power_hp or base.peak_power_hp
    peak_tq = spec.peak_torque_nm or base.peak_torque_nm
    peak_hp_rpm = spec.peak_power_rpm or base.peak_power_rpm
    peak_tq_rpm = spec.peak_torque_rpm or base.peak_torque_rpm
    if spec.peak_power_rpm:
        # Peak power RPM is not the redline; engines continue to rev above it.
        # The headroom varies strongly with engine type:
        #   Large inline-4 / V4 / L-twin (1000cc+): peak at ~93% of redline → ×1.08
        #   600cc inline-4 (R6, CBR600, ZX-6R): peak at ~88% → ×1.14
        #   Mid-size parallel twin (<700cc, 2-cyl): peak at ~82% → ×1.22
        #   Small parallel twin / single (<500cc, ≤2-cyl): peak at ~77% → ×1.30
        # This replaces the previous flat 1.08 factor which caused severe redline
        # under-estimation for small-displacement bikes (e.g. Ninja 400 → 10 800 rpm
        # instead of the real ~13 000 rpm, trapping at 119 km/h instead of 150+ km/h).
        cc = spec.displacement_cc or 1000
        cyls = spec.cylinders or 4
        if cc < 500 and cyls <= 2:
            redline_factor = 1.30   # small singles / parallel twins
        elif cc < 700 and cyls <= 2:
            redline_factor = 1.22   # mid-size twins (MT-07, Z650, Dominar 400)
        elif cc < 700:
            redline_factor = 1.14   # 600cc-class inline-4 (R6, CBR600RR, ZX-6R)
        else:
            redline_factor = 1.10   # large inline-4, V4, L-twin (≥ 1000cc class)
        redline = int(peak_hp_rpm * redline_factor)
    else:
        redline = base.redline_rpm
    idle = 1200

    # Try to find a known dyno curve for this bike
    dyno = get_dyno_curve(
        manufacturer=spec.manufacturer,
        model=spec.model_name,
        year=spec.year_from,
        model_code=spec.model_code,
    )

    # If no known curve found, generate a synthetic one based on peak power/torque
    if dyno is None:
        dyno = _synthetic_torque_curve(
            peak_torque_nm=float(peak_tq),
            peak_rpm=float(peak_tq_rpm),
            redline_rpm=float(redline),
            idle_rpm=float(idle),
            peak_power_hp=float(peak_hp),
            peak_power_rpm=float(peak_hp_rpm),
            points=100,
        )

    return EngineParams(
        dyno_curve=dyno,
        peak_power_hp=float(peak_hp),
        peak_torque_nm=float(peak_tq),
        peak_power_rpm=int(peak_hp_rpm),
        peak_torque_rpm=int(peak_tq_rpm),
        redline_rpm=int(redline),
        launch_rpm=int(redline * 0.55),  # ~55% of redline as launch RPM estimate
        idle_rpm=idle,
        displacement_cc=spec.displacement_cc or base.displacement_cc,
        bore_mm=spec.bore_mm or base.bore_mm,
        stroke_mm=spec.stroke_mm or base.stroke_mm,
        compression_ratio=spec.compression_ratio or base.compression_ratio,
        engine_inertia_kgm2=CATEGORY_ENGINE_INERTIA.get(spec.category, 0.042),
        cylinder_count=spec.cylinders,
        cylinder_config=_infer_cylinder_config(spec),
    )


def _build_chassis_from_spec(spec: BikeSpec) -> ChassisParams:
    """Build ChassisParams from a BikeSpec."""
    base = gsxr1000_k5().chassis

    dry_mass = spec.dry_mass_kg or spec.wet_mass_kg or base.dry_mass_kg
    # If only wet mass available, estimate dry as wet - 25 kg (fluids)
    if spec.dry_mass_kg is None and spec.wet_mass_kg:
        dry_mass = spec.wet_mass_kg - 25.0

    return ChassisParams(
        dry_mass_kg=float(dry_mass),
        rider_mass_kg=75.0,
        fluid_mass_kg=17.0,
        fuel_mass_kg=18.0 if not spec.fuel_capacity_l else spec.fuel_capacity_l * 0.74,
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

    if not ratios:
        # Use the gear-ratio lookup library (much better than a single fallback)
        lu_ratios, lu_front, lu_rear, lu_primary, _conf = lookup_gear_ratios(
            manufacturer=spec.manufacturer,
            model_name=spec.model_name,
            year=spec.year_from,
            category=spec.category,
            displacement_cc=spec.displacement_cc,
            gears=spec.gears,
        )
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

    return DrivetrainParams(
        gear_ratios=list(ratios),
        final_drive_ratio=float(rear) / float(front),
        front_sprocket=int(front),
        rear_sprocket=int(rear),
        chain_pitch_mm=chain_pitch_mm,
        chain_pitch=pitch,
        chain_links=base.chain_links,
        primary_ratio=float(primary),
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
    elif cat in ("sport", "naked") and disp >= 300:
        mu = 1.30  # middleweight sport (Ninja 400, R3, RC 390)
    elif cat in ("sport", "naked") and disp < 300:
        mu = 1.15  # entry-level budget tires (R15, Duke 200, Pulsar)
    elif cat == "cruiser":
        mu = 1.20  # touring compound, heavier loads
    elif cat == "adventure":
        mu = 1.15  # knobby/trail rubber
    elif cat == "touring":
        mu = 1.18  # touring compound
    else:
        mu = base.mu_peak  # fallback to K5 default

    result = TireParams(
        front_size=spec.front_tire_size or base.front_size,
        rear_size=spec.rear_tire_size or base.rear_size,
        mu_peak=mu,
        pacejka_B=base.pacejka_B,
        pacejka_C=base.pacejka_C,
        pacejka_D=base.pacejka_D,
        pacejka_E=base.pacejka_E,
        optimal_temp_c=base.optimal_temp_c,
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
            # Match rim diameter: e.g. "ZR17" or "R17" at end of size string
            rim_m = re.search(r"[ZRB]R(\d{2})\b", spec.rear_tire_size, re.IGNORECASE)
            if not rim_m:
                rim_m = re.search(r"-(\d{2})\b", spec.rear_tire_size)
            rim_half = (int(rim_m.group(1)) * 25.4 / 2) if rim_m else 215.9
            result.rear_rolling_radius_m = (rim_half + sidewall) / 1000.0

    return result


def _build_aero_from_spec(spec: BikeSpec) -> AeroParams:
    """Build AeroParams from spec or category defaults."""
    aero_defaults = CATEGORY_AERO.get(spec.category, CATEGORY_AERO["sport"])
    base = gsxr1000_k5().aero

    return AeroParams(
        cd=spec.cd or aero_defaults["cd"],
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

    # Compose model name
    year_tag = ""
    if spec.year_from:
        year_tag = f" ({spec.year_from})"
        if spec.year_to and spec.year_to != spec.year_from:
            year_tag = f" ({spec.year_from}-{spec.year_to})"

    name = f"{spec.manufacturer} {spec.model_name}{year_tag}"

    return BikeConfig(
        name=name,
        engine=engine,
        chassis=chassis,
        drivetrain=drivetrain,
        tires=tires,
        aero=aero,
        # Retain all other sub-configs at defaults
        forced_induction=base_config.forced_induction,
        clutch=base_config.clutch,
        suspension=base_config.suspension,
        braking=base_config.braking,
        wheelie=base_config.wheelie,
        rider=base_config.rider,
        parasitic=base_config.parasitic,
        staging=base_config.staging,
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
