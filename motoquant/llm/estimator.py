"""
Unknown-bike estimation for the MotoQuant chat agent.

Turns an LLM-supplied spec dict (from model knowledge and/or web lookup)
into a runnable BikeConfig WITHOUT touching the curated database, runs the
physics, and returns a clearly-labelled ESTIMATED result:

    spec dict → bikez.spec_from_dict → validator.validate_spec (physical
    bounds + unit auto-correction; hard errors reject) →
    importer.spec_to_bike_config (pure in-memory: Tier-1/Tier-2 gearing,
    category aero/parasitic defaults, synthetic torque curve) →
    engine_select.make_engine(config).run / run_top_speed.

The result carries the validator's confidence score and every assumption the
pipeline made, so the agent can present the number honestly ("estimated, not
catalog-validated"). Catalog misses are logged to the bike_suggestions table
so demand for missing bikes is visible to the catalog team.
"""

from __future__ import annotations

import logging
from typing import Any

from ..constants import MS_TO_KMH, MS_TO_MPH

logger = logging.getLogger(__name__)

# Fields the LLM must supply for a meaningful estimate. Everything else
# falls back to importer category defaults (documented in `assumptions`).
REQUIRED_FIELDS = (
    "manufacturer",
    "model_name",
    "displacement_cc",
    "peak_power_hp",
    "dry_mass_kg",
)

# Fields that meaningfully sharpen the estimate when present.
QUALITY_FIELDS = (
    "peak_power_rpm",
    "peak_torque_nm",
    "peak_torque_rpm",
    "cylinders",
    "category",
    "gears",
    "gear_ratios",
    "front_sprocket",
    "rear_sprocket",
    "bore_mm",
    "stroke_mm",
    "compression_ratio",
    "cd",
    "frontal_area_m2",
    "rear_tire_size",
    "wheelbase_mm",
    "year_from",
)


def simulate_estimated_bike(
    spec: dict[str, Any],
    *,
    db: Any = None,
    venue_id: int | None = None,
    env_overrides: dict[str, float] | None = None,
    rider_mass_kg: float | None = None,
    include_top_speed: bool = True,
    log_suggestion: bool = True,
) -> dict[str, Any]:
    """Run a moderate-accuracy sim from a raw spec dict.

    Returns a dict with ``estimated=True`` and ET/trap/top-speed on success,
    or ``{"error": ...}`` on validation failure. Never raises.
    """
    from ..scraper.bikez import spec_from_dict
    from ..scraper.importer import spec_to_bike_config
    from ..scraper.validator import score_spec, validate_spec

    spec = dict(spec or {})
    missing = [f for f in REQUIRED_FIELDS if not spec.get(f)]
    if missing:
        return {
            "error": f"missing required spec fields: {', '.join(missing)}",
            "required_fields": list(REQUIRED_FIELDS),
            "quality_fields": list(QUALITY_FIELDS),
        }

    # Reasonable derived defaults the validator would otherwise reject on.
    if not spec.get("year_from"):
        spec["year_from"] = 2020
    if not spec.get("category"):
        spec["category"] = "naked"

    try:
        bike_spec = spec_from_dict(spec, source_name="llm_estimate")
    except Exception as e:  # noqa: BLE001
        return {"error": f"spec construction failed: {type(e).__name__}: {e}"}

    try:
        validation = validate_spec(bike_spec)
    except Exception as e:  # noqa: BLE001
        return {"error": f"validation crashed: {type(e).__name__}: {e}"}
    if validation.errors:
        return {
            "error": "spec failed physical-bounds validation",
            "validation_errors": list(validation.errors),
            "hint": (
                "check units: power in HP (not kW), torque in Nm (not lb-ft), "
                "mass in kg (not lbs) — the validator auto-corrects obvious "
                "unit confusion but rejects out-of-range values"
            ),
        }

    # LLM-recalled specs are less trustworthy than curated spec sheets:
    # cap per-field confidence below the 0.88 "manually curated" default
    # that spec_from_dict stamps, so score_spec reports an honest number.
    try:
        for fname, conf in list(bike_spec.field_confidence.items()):
            bike_spec.field_confidence[fname] = min(float(conf), 0.60)
    except Exception:  # noqa: BLE001
        pass
    try:
        confidence = float(score_spec(bike_spec, validation))
    except Exception:  # noqa: BLE001
        confidence = 0.0

    assumptions: list[str] = []
    if not spec.get("gear_ratios"):
        assumptions.append(
            "gearbox ratios not supplied — using MotoQuant category-default "
            "gearing (Tier-2), the largest single source of estimate error"
        )
    if not spec.get("peak_torque_nm"):
        assumptions.append("torque curve synthesized from power figure alone")
    if not spec.get("cd") or not spec.get("frontal_area_m2"):
        assumptions.append("aero (Cd / frontal area) from category defaults")
    if not spec.get("cylinders"):
        assumptions.append("cylinder count/config inferred from name+displacement")

    try:
        config = spec_to_bike_config(bike_spec)
    except Exception as e:  # noqa: BLE001
        return {"error": f"config build failed: {type(e).__name__}: {e}"}

    # Venue / environment
    if db is not None and venue_id is not None:
        try:
            from datetime import datetime

            env = db.venues.to_environment(venue_id, month=datetime.now().month)
            if env is not None:
                config.environment = env
        except Exception:  # noqa: BLE001
            assumptions.append("venue environment lookup failed — ISA conditions")
    for key, attr in (
        ("ambient_temp_c", "ambient_temp_c"),
        ("humidity_pct", "relative_humidity_pct"),
        ("altitude_m", "altitude_m"),
    ):
        val = (env_overrides or {}).get(key)
        if val is not None:
            setattr(config.environment, attr, float(val))
    if rider_mass_kg:
        config.rider.mass_kg = float(rider_mass_kg)
        config.chassis.rider_mass_kg = float(rider_mass_kg)

    # engine_select picks the Rust core when it is available (same numbers,
    # ~50x faster), else the Python reference engine.
    from ..engine_select import make_engine

    try:
        engine = make_engine(config)
        sim = engine.run()
    except Exception as e:  # noqa: BLE001
        return {"error": f"simulation failed: {type(e).__name__}: {e}"}

    out: dict[str, Any] = {
        "estimated": True,
        "bike_name": f"{bike_spec.manufacturer} {bike_spec.model_name}",
        "confidence": round(confidence, 2),
        "validation_warnings": list(validation.warnings or []),
        "assumptions": assumptions,
        "finished_quarter": bool(getattr(sim, "finished_quarter", True)),
    }
    if getattr(sim, "time_quarter", None):
        out["et_quarter_s"] = round(float(sim.time_quarter), 3)
        out["trap_speed_kmh"] = round(float(sim.speed_quarter) * MS_TO_KMH, 1)
        out["trap_speed_mph"] = round(float(sim.speed_quarter) * MS_TO_MPH, 1)
    if getattr(sim, "time_60ft", None):
        out["et_60ft_s"] = round(float(sim.time_60ft), 3)
    if getattr(sim, "time_eighth", None):
        out["et_eighth_s"] = round(float(sim.time_eighth), 3)

    if include_top_speed:
        try:
            ts = engine.run_top_speed()
            v = getattr(ts, "terminal_velocity_ms", None)
            if v:
                out["top_speed_kmh"] = round(float(v) * MS_TO_KMH, 1)
                out["top_speed_is_plateau"] = bool(
                    getattr(ts, "reached_plateau", False)
                )
        except Exception as e:  # noqa: BLE001
            out["top_speed_error"] = f"{type(e).__name__}: {e}"

    # Log catalog demand — never let this break the sim result.
    if log_suggestion and db is not None:
        try:
            db.bike_suggestions.create(
                bike_spec.manufacturer,
                bike_spec.model_name,
                year=spec.get("year_from"),
                displacement_cc=spec.get("displacement_cc"),
                peak_power_hp=spec.get("peak_power_hp"),
                dry_mass_kg=spec.get("dry_mass_kg"),
                category=spec.get("category"),
                notes="chat-agent estimated sim (bike not in catalog)",
            )
        except Exception:  # noqa: BLE001
            logger.debug("bike_suggestions log failed", exc_info=True)

    return out
