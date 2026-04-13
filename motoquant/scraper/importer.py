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
from typing import List, Optional, Tuple, Dict

from .spec import BikeSpec, ValidationResult
from .validator import validate_spec, score_spec, _source_confidence
from .gear_ratios import lookup_gear_ratios
from ..models import (
    BikeConfig, EngineParams, ChassisParams, DrivetrainParams,
    TireParams, AeroParams, EnvironmentParams, StagingParams,
)
from ..defaults import gsxr1000_k5  # used to get default sub-configs

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────
# Category-based aerodynamic defaults
# ────────────────────────────────────────────────────────

CATEGORY_AERO = {
    "sport":     {"cd": 0.32, "frontal_area_m2": 0.45, "wheelie_tendency": 1.2},
    "naked":     {"cd": 0.40, "frontal_area_m2": 0.52, "wheelie_tendency": 0.8},
    "cruiser":   {"cd": 0.50, "frontal_area_m2": 0.58, "wheelie_tendency": 0.4},
    "adventure": {"cd": 0.46, "frontal_area_m2": 0.55, "wheelie_tendency": 0.6},
    "touring":   {"cd": 0.52, "frontal_area_m2": 0.60, "wheelie_tendency": 0.3},
    "scooter":   {"cd": 0.44, "frontal_area_m2": 0.38, "wheelie_tendency": 0.2},
}

# Category-based inertia estimates for engine rotating mass
CATEGORY_ENGINE_INERTIA = {
    "sport": 0.040, "naked": 0.042, "cruiser": 0.060,
    "adventure": 0.045, "touring": 0.055,
}

# Category-based CoG height estimate (mm)
CATEGORY_COG_HEIGHT = {
    "sport": 540, "naked": 560, "cruiser": 620,
    "adventure": 580, "touring": 600,
}


# ────────────────────────────────────────────────────────
# Synthetic torque curve builder
# ────────────────────────────────────────────────────────

def _build_engine_from_spec(spec: BikeSpec) -> EngineParams:
    """
    Build an EngineParams from a BikeSpec.
    Uses _synthetic_torque_curve for the dyno curve when no dyno data is available.
    """
    from ..defaults import _synthetic_torque_curve

    # Start with K5 defaults as a base (reasonable sport bike values)
    base = gsxr1000_k5().engine

    # Peak power and torque
    peak_hp = spec.peak_power_hp or base.peak_power_hp
    peak_tq = spec.peak_torque_nm or base.peak_torque_nm
    peak_hp_rpm = spec.peak_power_rpm or base.peak_power_rpm
    peak_tq_rpm = spec.peak_torque_rpm or base.peak_torque_rpm
    redline = int(peak_hp_rpm * 1.08) if spec.peak_power_rpm else base.redline_rpm
    idle = 1200

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


def _build_drivetrain_from_spec(spec: BikeSpec, engine: EngineParams) -> DrivetrainParams:
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
    rear  = spec.rear_sprocket
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
        ratios  = lu_ratios
        front   = front or lu_front
        rear    = rear  or lu_rear
        primary = primary or lu_primary

    front   = front   or base.front_sprocket
    rear    = rear    or base.rear_sprocket
    primary = primary or base.primary_ratio

    return DrivetrainParams(
        gear_ratios=list(ratios),
        final_drive_ratio=float(rear) / float(front),
        front_sprocket=int(front),
        rear_sprocket=int(rear),
        chain_links=base.chain_links,
        primary_ratio=float(primary),
    )


def _build_tires_from_spec(spec: BikeSpec) -> TireParams:
    """Build basic TireParams from tire size strings."""
    base = gsxr1000_k5().tires

    result = TireParams(
        front_size=spec.front_tire_size or base.front_size,
        rear_size=spec.rear_tire_size or base.rear_size,
        # Keep all friction params at defaults — these are not scraped
        mu_peak=base.mu_peak,
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
    db,          # MotoQuantDB
    spec: BikeSpec,
    validation_result: Optional[ValidationResult] = None,
    dry_run: bool = False,
) -> Optional[Tuple[int, int]]:
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
        logger.error(
            f"Import failed for {spec.manufacturer} {spec.model_name}: {e}"
        )
        return None


def import_batch(
    db,
    specs: List[BikeSpec],
    dry_run: bool = False,
    stop_on_error: bool = False,
) -> Dict[str, int]:
    """
    Import a list of BikeSpec objects into the database.

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

        ret = import_spec(db, spec, result, dry_run=dry_run)
        if ret is None and not dry_run:
            errors += 1
            if stop_on_error:
                break
        else:
            imported += 1

    return {
        "imported": imported,
        "skipped_invalid": skipped,
        "errors": errors,
        "dry_run": dry_run,
    }
