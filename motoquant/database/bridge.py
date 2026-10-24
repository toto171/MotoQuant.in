"""
MotoQuant — BikeConfig ↔ Database Bridge
========================================
Lossless conversion between the in-memory dataclass hierarchy (BikeConfig)
and the relational database representation.

Guarantees:
  - config → DB → config round-trip is bit-exact for all scalar params
  - Dyno curves preserved to full float64 precision
  - Gear ratios preserved as ordered lists
  - Environment params handled separately (venue + weather records)
"""

import dataclasses
import json
from typing import Any

import numpy as np
from typing_extensions import TypedDict  # py<3.12-safe with pydantic

from ..config_io import dataclass_to_dict, dyno_from_dict
from ..models import (
    BOOST_N2O,
    BOOST_SC_CENTRIFUGAL,
    BOOST_SC_ROOTS,
    BOOST_TURBO,
    AeroParams,
    BikeConfig,
    BrakingParams,
    ChassisParams,
    ClutchParams,
    DrivetrainParams,
    DynoCurve,
    EngineParams,
    EnvironmentParams,
    ForcedInductionParams,
    ParasiticParams,
    RiderParams,
    StagingParams,
    SuspensionParams,
    TireParams,
    WheelieParams,
)

# Section name → dataclass class (excludes environment — that comes from venue/weather)
PARAM_SECTIONS = {
    "chassis": ChassisParams,
    "engine": EngineParams,
    "forced_induction": ForcedInductionParams,
    "drivetrain": DrivetrainParams,
    "clutch": ClutchParams,
    "tires": TireParams,
    "aero": AeroParams,
    "suspension": SuspensionParams,
    "braking": BrakingParams,
    "wheelie": WheelieParams,
    "rider": RiderParams,
    "parasitic": ParasiticParams,
    "staging": StagingParams,
}

# DB column name → PARAM_SECTIONS key
DB_COLUMN_TO_SECTION = {
    "chassis_params": "chassis",
    "engine_params": "engine",
    "forced_induction_params": "forced_induction",
    "drivetrain_params": "drivetrain",
    "clutch_params": "clutch",
    "tire_params": "tires",
    "aero_params": "aero",
    "suspension_params": "suspension",
    "braking_params": "braking",
    "wheelie_params": "wheelie",
    "rider_params": "rider",
    "parasitic_params": "parasitic",
    "staging_params": "staging",
}


def _serialize_section(section_obj) -> str:
    """Serialize a dataclass section to JSON string, handling DynoCurve + numpy."""
    d = dataclass_to_dict(section_obj)
    return json.dumps(d, default=_json_default)


def _json_default(obj):
    """JSON serializer for numpy types."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    raise TypeError(f"Not JSON serializable: {type(obj)}")


def _deserialize_section(json_str: str, section_name: str):
    """Deserialize JSON string back to the appropriate dataclass."""
    d = json.loads(json_str)
    cls = PARAM_SECTIONS[section_name]

    # Special handling: DynoCurve in engine params
    if section_name == "engine" and "dyno_curve" in d:
        dc = d.pop("dyno_curve")
        if dc is not None:
            d["dyno_curve"] = dyno_from_dict(dc)

    # Filter to known fields only
    field_names = {f.name for f in dataclasses.fields(cls)}
    filtered = {k: v for k, v in d.items() if k in field_names}

    return cls(**filtered)


# ────────────────────────────────────────────
# BikeConfig → DB row data
# ────────────────────────────────────────────


def config_to_db_row(config: BikeConfig) -> dict[str, Any]:
    """
    Convert a BikeConfig to a dict suitable for INSERT into bike_configs.

    Returns a dict with keys matching bike_configs columns:
      chassis_params, engine_params, ... staging_params  (all JSON strings)

    Does NOT include: bike_model_id, version, is_current, etc.
    Those are set by the repository.

    NOTE (env not persisted): there is no environment_params column, so the
    EnvironmentParams section is NOT serialized. On read-back, db_row_to_config
    reconstructs a DEFAULT environment (Aamby Valley, 679 m), NOT whatever the
    source config carried. Consequence: the DB/API path simulates at Aamby
    Valley by default, while the hand-curated defaults.py reference bikes use
    "Sea Level Reference" -- so /api/simulate?bike_id={1,2,3} returns the K5/R1/
    Hayabusa ET at altitude (~+0.15 s) rather than the sea-level 9.9331/10.1436/
    10.3633 headline baselines. This is by design (the API overrides the
    environment from the request venue) and is exactly why the reference bikes
    are excluded from reseed_configs_from_specs. Every other section round-trips
    byte-identical -- do NOT mistake this for a stale-config bug.
    """
    row = {}
    for db_col, section_key in DB_COLUMN_TO_SECTION.items():
        section_obj = getattr(config, section_key)
        row[db_col] = _serialize_section(section_obj)
    # Top-level (non-section) physics fields. category_tag drives the
    # per-cluster profile dispatch in physics.py -- dropping it made the
    # DB path re-derive a tag WITHOUT manufacturer/category context and
    # 44 bikes ran the wrong cluster profile in production.
    row["category_tag"] = config.category_tag
    return row


def extract_dyno_curve(config: BikeConfig) -> dict[str, Any] | None:
    """
    Extract dyno curve data from a BikeConfig for the dyno_curves table.

    Returns None if no dyno curve is present.
    """
    if config.engine.dyno_curve is None:
        return None
    dc = config.engine.dyno_curve
    return {
        "curve_type": "torque",
        "is_at_wheel": 1 if dc.is_at_wheel else 0,
        "rpm_points": json.dumps(dc.rpm.tolist()),
        "torque_values": json.dumps(dc.torque_nm.tolist()),
        "num_points": len(dc.rpm),
    }


class HeadlineSpecsDict(TypedDict):
    """Shape of the dict returned by :func:`extract_headline_specs`.

    Keys map 1:1 to ``bike_models`` columns that the parts-compatibility
    engine and search filters read directly (i.e. without cracking open
    the JSON ``engine_params`` blob). All fields are nullable because
    legacy seed rows may pre-date the spec-extraction work; ``None``
    propagates as SQL ``NULL``.
    """

    displacement_cc: float | None
    bore_mm: float | None
    stroke_mm: float | None
    compression_ratio: float | None
    peak_power_hp: float | None
    peak_power_rpm: float | None
    peak_torque_nm: float | None
    peak_torque_rpm: float | None
    cylinder_count: int | None
    cylinder_config: str | None
    dry_mass_kg: float | None
    wheelbase_mm: float | None
    seat_height_mm: float | None


def extract_headline_specs(config: BikeConfig) -> HeadlineSpecsDict:
    """
    Extract searchable headline specs from a BikeConfig
    for the bike_models table.

    Includes cylinder_count + cylinder_config so downstream consumers
    (e.g. parts compatibility engine) can filter on engine family without
    having to crack open the JSON engine_params blob.
    """
    return {
        "displacement_cc": config.engine.displacement_cc,
        "bore_mm": config.engine.bore_mm,
        "stroke_mm": config.engine.stroke_mm,
        "compression_ratio": config.engine.compression_ratio,
        "peak_power_hp": config.engine.peak_power_hp,
        "peak_power_rpm": config.engine.peak_power_rpm,
        "peak_torque_nm": config.engine.peak_torque_nm,
        "peak_torque_rpm": config.engine.peak_torque_rpm,
        "cylinder_count": getattr(config.engine, "cylinder_count", None),
        "cylinder_config": getattr(config.engine, "cylinder_config", None),
        "dry_mass_kg": config.chassis.dry_mass_kg,
        "wheelbase_mm": config.chassis.wheelbase_mm,
        "seat_height_mm": config.chassis.seat_height_mm,
    }


# ────────────────────────────────────────────
# DB row → BikeConfig
# ────────────────────────────────────────────


def db_row_to_config(
    row: dict,
    name: str = "DB Bike",
    environment: EnvironmentParams | None = None,
    dyno_override: DynoCurve | None = None,
) -> BikeConfig:
    """
    Reconstruct a BikeConfig from a bike_configs DB row.

    Parameters
    ----------
    row : dict
        A dict-like row from the bike_configs table.
    name : str
        Bike display name (from bike_models table).
    environment : EnvironmentParams, optional
        Environment to apply (from venue + weather). If None, uses defaults.
    dyno_override : DynoCurve, optional
        If provided, overrides the dyno curve stored in engine_params JSON.
        Useful when loading from the dedicated dyno_curves table.
    """
    kwargs = {"name": name}

    for db_col, section_key in DB_COLUMN_TO_SECTION.items():
        json_str = row.get(db_col) if hasattr(row, "get") else row[db_col]
        if json_str is None:
            continue  # skip missing optional sections
        section = _deserialize_section(json_str, section_key)
        kwargs[section_key] = section

    tag = row.get("category_tag") if hasattr(row, "get") else None
    if tag:
        kwargs["category_tag"] = tag

    # Override dyno curve if provided separately
    if dyno_override is not None:
        kwargs["engine"].dyno_curve = dyno_override

    # Apply environment
    if environment is not None:
        kwargs["environment"] = environment
    else:
        kwargs["environment"] = EnvironmentParams()

    return BikeConfig(**kwargs)


def venue_row_to_environment(
    venue_row: dict,
    weather_row: dict | None = None,
) -> EnvironmentParams:
    """
    Build an EnvironmentParams from a venues row + optional weather_records row.
    """
    env = EnvironmentParams(
        venue_name=venue_row["name"],
        altitude_m=venue_row["altitude_m"],
        track_surface=venue_row["surface_type"] or "asphalt",
        track_gradient_pct=venue_row["track_gradient_pct"] or 0.0,
        track_heading_deg=venue_row["track_heading_deg"] or 0.0,
    )

    if weather_row is not None:
        env.ambient_temp_c = weather_row["ambient_temp_c"] or 25.0
        env.relative_humidity_pct = weather_row["relative_humidity_pct"] or 50.0
        env.barometric_pressure_hpa = weather_row["barometric_pressure_hpa"] or 1013.25
        env.wind_speed_ms = weather_row["wind_speed_ms"] or 0.0
        env.wind_direction_deg = weather_row["wind_direction_deg"] or 0.0
        env.track_temp_c = weather_row["track_temp_c"] or 30.0

    return env


def seasonal_to_environment(
    venue_row: dict,
    seasonal_row: dict,
) -> EnvironmentParams:
    """
    Build EnvironmentParams from venue + seasonal average data.
    Used for offline what-if analysis.
    """
    return EnvironmentParams(
        venue_name=venue_row["name"],
        altitude_m=venue_row["altitude_m"],
        ambient_temp_c=seasonal_row["avg_temp_c"],
        relative_humidity_pct=seasonal_row["avg_humidity_pct"],
        barometric_pressure_hpa=seasonal_row["avg_pressure_hpa"],
        wind_speed_ms=seasonal_row["avg_wind_speed_ms"],
        wind_direction_deg=seasonal_row["prevailing_wind_deg"],
        track_temp_c=seasonal_row["avg_track_temp_c"],
        track_surface=venue_row["surface_type"] or "asphalt",
        track_gradient_pct=venue_row["track_gradient_pct"] or 0.0,
        track_heading_deg=venue_row["track_heading_deg"] or 0.0,
    )


# ────────────────────────────────────────────
# Parts → param modification
# ────────────────────────────────────────────


def apply_part_to_config(config: BikeConfig, part_row: dict) -> BikeConfig:
    """
    Apply a part's parameter modifications to a BikeConfig.

    Parts can specify:
      - param_overrides:   absolute values  {"drivetrain.rear_sprocket": 45}
      - param_deltas:      additive changes {"engine.peak_power_hp": 15}
      - param_multipliers: factors          {"tires.mu_peak": 1.08}

    Dyno curve scaling
    ------------------
    If a part changes engine.peak_power_hp (via delta or multiplier) and the
    config has a stored dyno curve, the dyno curve's torque array is scaled by
    the same power ratio. This ensures NA power mods (exhaust, air filter, ECU
    flash) work correctly for bikes that have measured dyno data.

    Forced-induction parts (turbo, SC, N2O) set forced_induction.* params
    directly. The physics model then applies the boost multiplier on top of the
    base dyno torque — no dyno scaling needed or applied for those. Whether a
    part is forced-induction is decided from the PART (does it write
    forced_induction.*?), never from the config's current boost state, so an
    exhaust scales the curve whether it is applied before or after a turbo.
    A forced-induction part that carries an hp delta, or that sets a boost
    type with zero boost / a zero nitrous shot, emits a warning.

    2-stroke expansion chambers (``engine.tuned_rpm`` overrides) on a config
    with a dyno curve reshape the curve around the pipe's resonance (see
    ``_reshape_curve_for_pipe``). The 2T flags ``expansion_chamber`` /
    ``reed_valve`` / ``powervalve`` only shape the SYNTHETIC 2T curve, so on a
    curve-carrying config (every catalog bike) they are informational; their
    gain must come through peak_power_hp deltas/multipliers.

    A part that switches ``staging.two_step`` on without its own
    ``staging.launch_rpm`` holds at the bike's peak-torque rpm instead of the
    8000 rpm dataclass default.

    Path validation
    ---------------
    Invalid dotted paths (e.g. typos, removed fields) emit a warnings.warn()
    rather than silently doing nothing. This makes bugs visible in the CLI/app
    output without crashing the simulation.

    Returns a NEW BikeConfig (does not mutate the original).
    """
    import copy
    import logging
    import warnings

    _log = logging.getLogger(__name__)
    new_config = copy.deepcopy(config)
    part_name = part_row.get("model_name", "unknown part")

    # Snapshot power / launch mode before any changes (for dyno curve scaling
    # and the two-step hold-rpm fill below).
    old_peak_hp = new_config.engine.peak_power_hp
    old_peak_tq = new_config.engine.peak_torque_nm
    old_two_step = bool(new_config.staging.two_step)

    def _set_nested(obj, path: str, value) -> bool:
        """Set a nested attribute via dotted path. Returns False if path is invalid."""
        parts = path.split(".")
        for part in parts[:-1]:
            if not hasattr(obj, part):
                msg = (
                    f"apply_part_to_config [{part_name}]: "
                    f"invalid param path '{path}' — no attribute '{part}'. Skipped."
                )
                _log.warning(msg)
                warnings.warn(msg)
                return False
            obj = getattr(obj, part)
        if not hasattr(obj, parts[-1]):
            msg = (
                f"apply_part_to_config [{part_name}]: "
                f"invalid param path '{path}' — no attribute '{parts[-1]}'. Skipped."
            )
            _log.warning(msg)
            warnings.warn(msg)
            return False
        setattr(obj, parts[-1], value)
        return True

    def _get_nested(obj, path: str):
        """Get a nested attribute via dotted path."""
        for part in path.split("."):
            obj = getattr(obj, part)
        return obj

    # Apply overrides (absolute set)
    overrides = part_row.get("param_overrides") or {}
    if isinstance(overrides, str):
        overrides = json.loads(overrides)
    for path, val in overrides.items():
        _set_nested(new_config, path, val)

    # Apply deltas (additive)
    deltas = part_row.get("param_deltas") or {}
    if isinstance(deltas, str):
        deltas = json.loads(deltas)
    for path, delta in deltas.items():
        try:
            current = _get_nested(new_config, path)
            _set_nested(new_config, path, current + delta)
        except AttributeError:
            warnings.warn(
                f"apply_part_to_config [{part_name}]: "
                f"invalid delta path '{path}'. Skipped."
            )

    # Apply multipliers (scale current value)
    multipliers = part_row.get("param_multipliers") or {}
    if isinstance(multipliers, str):
        multipliers = json.loads(multipliers)
    for path, factor in multipliers.items():
        try:
            current = _get_nested(new_config, path)
            _set_nested(new_config, path, current * factor)
        except AttributeError:
            warnings.warn(
                f"apply_part_to_config [{part_name}]: "
                f"invalid multiplier path '{path}'. Skipped."
            )

    def _warn(msg: str) -> None:
        msg = f"apply_part_to_config [{part_name}]: {msg}"
        _log.warning(msg)
        warnings.warn(msg)

    touched = set(overrides) | set(deltas) | set(multipliers)

    # ── Dyno curve scaling for power mods — decided PER PART ──────────────────
    # If this part changed engine.peak_power_hp AND the config has a dyno curve,
    # scale the curve's torque array by the same ratio so the physics engine
    # sees the power delta (every production config carries a baked curve, so
    # peak_power_hp alone is a display field there).
    #
    # The rule is keyed on whether THIS PART is a forced-induction part (it
    # writes forced_induction.*), not on the config's boost state after the
    # overrides. The old `is_na` gate made two classes of part dead:
    #   * turbo/SC kits whose gain was encoded as a peak_power_hp delta (the
    #     curve was never scaled and target_boost_bar stayed 0, so a '+180 hp'
    #     twin-turbo delivered zero power), and
    #   * any NA power part (exhaust, ECU) applied AFTER a boost part — the
    #     build's ET depended on the order the parts were applied in.
    # A forced-induction part gets its power from the boost model
    # (target_boost_bar / n2o_*), so an hp delta on one is ignored and flagged.
    new_peak_hp = new_config.engine.peak_power_hp
    hp_changed = abs(new_peak_hp - old_peak_hp) > 0.05
    has_dyno = new_config.engine.dyno_curve is not None
    part_is_fi = any(p.startswith("forced_induction.") for p in touched)
    reshapes_pipe = (
        "engine.tuned_rpm" in overrides
        and has_dyno
        and new_config.engine.stroke_type == 2
    )

    if part_is_fi:
        fi = new_config.forced_induction
        if hp_changed and has_dyno:
            # Ignored, and reverted: leaving the inflated peak_power_hp in
            # place would also shrink the curve-scaling ratio of every NA
            # part applied after this one (order-dependent builds again).
            _warn(
                "forced-induction part carries an engine.peak_power_hp change; "
                "the boost model supplies its power, so the change is ignored "
                "(encode the gain as target_boost_bar / n2o_* instead)."
            )
            new_config.engine.peak_power_hp = old_peak_hp
            new_config.engine.peak_torque_nm = old_peak_tq
        if fi.boost_type == BOOST_N2O and fi.n2o_hp_per_stage * fi.n2o_stages <= 0:
            _warn(
                "nitrous part delivers 0 hp "
                f"(n2o_hp_per_stage={fi.n2o_hp_per_stage}, "
                f"n2o_stages={fi.n2o_stages})."
            )
        elif fi.boost_type in _PRESSURE_BOOST_TYPES and fi.target_boost_bar <= 0:
            _warn(
                f"boost_type={fi.boost_type!r} with target_boost_bar="
                f"{fi.target_boost_bar} delivers no boost."
            )
    elif reshapes_pipe:
        # Expansion chamber on a 2-stroke whose torque comes from a baked dyno
        # curve. get_torque() never reads tuned_rpm when a curve is present, so
        # overriding it alone only moved the 2T launch-floor clamp in the slip
        # phase — pinning the engine at the pipe's rpm without moving any
        # torque, which made 'upgrades' up to 0.7 s SLOWER. Apply the pipe as
        # the curve change it is instead: a resonance-weighted torque gain
        # centred on the pipe's tuned rpm, sized so the curve's peak power
        # rises by the part's hp ratio, then point tuned_rpm at the reshaped
        # curve's actual torque peak (which is what tuned_rpm means on a
        # stock 2T config).
        ratio = new_peak_hp / old_peak_hp if old_peak_hp > 1.0 else 1.0
        dc, tuned = _reshape_curve_for_pipe(
            new_config.engine.dyno_curve,
            pipe_rpm=float(overrides["engine.tuned_rpm"]),
            power_ratio=ratio,
            redline_rpm=new_config.engine.redline_rpm,
        )
        new_config.engine.dyno_curve = dc
        new_config.engine.tuned_rpm = tuned
    elif hp_changed and has_dyno and old_peak_hp > 1.0:
        ratio = new_peak_hp / old_peak_hp
        dc = new_config.engine.dyno_curve
        new_config.engine.dyno_curve = DynoCurve(
            rpm=dc.rpm.copy(),
            torque_nm=dc.torque_nm * ratio,
            is_at_wheel=dc.is_at_wheel,
        )

    # ── Two-step enabled without a hold rpm ──────────────────────────────────
    # staging.launch_rpm on a config that never had a two-step is the
    # dataclass default (8000), not per-bike data. A part that switches the
    # two-step on without declaring its own hold rpm (e.g. a piggyback with
    # 'launch control') used to launch every compatible bike at 8000 rpm —
    # past redline on big twins (Thruxton 1200 R: +1.8 s). Hold at the rpm the
    # bike already launches at without a two-step (peak-torque rpm, clamped
    # to the engine's idle..redline window).
    if (
        new_config.staging.two_step
        and not old_two_step
        and "staging.launch_rpm" not in touched
    ):
        eng = new_config.engine
        new_config.staging.launch_rpm = float(
            min(max(eng.peak_torque_rpm, eng.idle_rpm), eng.redline_rpm)
        )

    return new_config


# Boost types whose power comes from target_boost_bar.
_PRESSURE_BOOST_TYPES = frozenset({BOOST_TURBO, BOOST_SC_ROOTS, BOOST_SC_CENTRIFUGAL})

# A bolt-on pipe moves a 2-stroke's resonance by at most this fraction of the
# stock curve's resonance; the reshape is a Gaussian of this relative width.
_PIPE_MAX_SHIFT = 0.15
_PIPE_SIGMA_FRAC = 0.20


def _reshape_curve_for_pipe(
    dc: DynoCurve,
    pipe_rpm: float,
    power_ratio: float,
    redline_rpm: float,
) -> tuple[DynoCurve, float]:
    """Apply an expansion-chamber part to a baked 2-stroke dyno curve.

    Multiplies the torque by ``1 + k * w(rpm)`` where ``w`` is a Gaussian
    centred on the pipe's tuned rpm (clamped to within ``_PIPE_MAX_SHIFT`` of
    the stock curve's resonance and below redline), with ``k`` chosen so the
    curve's peak power rises by ``power_ratio``. Ratios at or below 1 fall back
    to a uniform scale (a pipe that loses power has no resonance to add).

    Returns the new curve and its torque-peak rpm (the new ``tuned_rpm``,
    capped at redline).
    """
    rpm = np.asarray(dc.rpm, dtype=float)
    torque = np.asarray(dc.torque_nm, dtype=float)
    if power_ratio <= 1.0:
        new_t = torque * power_ratio
    else:
        stock_res = float(rpm[int(np.argmax(torque))])
        hi = min(stock_res * (1.0 + _PIPE_MAX_SHIFT), 0.97 * redline_rpm)
        lo = min(stock_res * (1.0 - _PIPE_MAX_SHIFT), hi)
        centre = min(max(pipe_rpm, lo), hi)
        w = np.exp(-0.5 * ((rpm - centre) / (_PIPE_SIGMA_FRAC * centre)) ** 2)
        power = torque * rpm
        target = float(power.max()) * power_ratio
        k_lo, k_hi = 0.0, 1.0
        while float((power * (1.0 + k_hi * w)).max()) < target and k_hi < 1e3:
            k_hi *= 2.0
        for _ in range(60):
            k = 0.5 * (k_lo + k_hi)
            if float((power * (1.0 + k * w)).max()) < target:
                k_lo = k
            else:
                k_hi = k
        new_t = torque * (1.0 + k_hi * w)
    tuned = float(min(rpm[int(np.argmax(new_t))], redline_rpm))
    return DynoCurve(rpm=rpm.copy(), torque_nm=new_t, is_at_wheel=dc.is_at_wheel), tuned


def compute_data_completeness(config: BikeConfig) -> float:
    """
    Compute what fraction of simulation-critical parameters are
    populated (non-default) in a BikeConfig.

    Returns 0.0–1.0.
    """
    # Critical fields for drag simulation accuracy
    critical_fields = [
        ("engine", "dyno_curve"),
        ("engine", "displacement_cc"),
        ("engine", "peak_power_hp"),
        ("engine", "peak_torque_nm"),
        ("engine", "redline_rpm"),
        ("chassis", "dry_mass_kg"),
        ("chassis", "wheelbase_mm"),
        ("chassis", "cog_height_mm"),
        ("chassis", "front_weight_pct"),
        ("drivetrain", "primary_ratio"),
        ("drivetrain", "gear_ratios"),
        ("drivetrain", "front_sprocket"),
        ("drivetrain", "rear_sprocket"),
        ("tires", "rear_rolling_radius_m"),
        ("tires", "mu_peak"),
        ("tires", "pacejka_B"),
        ("tires", "pacejka_C"),
        ("tires", "pacejka_D"),
        ("aero", "cd"),
        ("aero", "frontal_area_m2"),
    ]

    defaults = BikeConfig()
    filled = 0
    for section, field_name in critical_fields:
        current_val = getattr(getattr(config, section), field_name)
        default_val = getattr(getattr(defaults, section), field_name)
        if current_val != default_val:
            filled += 1
        elif field_name == "dyno_curve" and current_val is not None:
            filled += 1

    return filled / len(critical_fields)
