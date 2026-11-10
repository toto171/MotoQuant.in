"""
MotoQuant — Configuration Import/Export
=======================================
JSON serialization for BikeConfig and all sub-parameter dataclasses.
Enables saving, loading, and sharing bike configurations.
"""

import dataclasses
import json
from pathlib import Path

import numpy as np

from .models import (
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

# Map of section name → dataclass type
_SECTION_MAP = {
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
    "environment": EnvironmentParams,
}


class _NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy arrays and types."""

    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        return super().default(obj)


def _dyno_to_dict(dyno: DynoCurve) -> dict:
    """Serialize a DynoCurve to a JSON-safe dict."""
    return {
        "rpm": dyno.rpm.tolist()
        if isinstance(dyno.rpm, np.ndarray)
        else list(dyno.rpm),
        "torque_nm": dyno.torque_nm.tolist()
        if isinstance(dyno.torque_nm, np.ndarray)
        else list(dyno.torque_nm),
        "is_at_wheel": dyno.is_at_wheel,
    }


def dyno_from_dict(d: dict) -> DynoCurve:
    """Deserialize a DynoCurve from a dict."""
    return DynoCurve(
        rpm=np.array(d["rpm"]),
        torque_nm=np.array(d["torque_nm"]),
        is_at_wheel=d.get("is_at_wheel", True),
    )


def dataclass_to_dict(obj) -> dict:
    """Recursively convert a dataclass to dict, handling DynoCurve and numpy."""
    result = {}
    for f in dataclasses.fields(obj):
        val = getattr(obj, f.name)
        if isinstance(val, DynoCurve):
            result[f.name] = _dyno_to_dict(val)
        elif isinstance(val, np.ndarray):
            result[f.name] = val.tolist()
        elif dataclasses.is_dataclass(val):
            result[f.name] = dataclass_to_dict(val)
        else:
            result[f.name] = val
    return result


def config_to_dict(config: BikeConfig) -> dict:
    """Convert a BikeConfig to a JSON-serializable dict."""
    d = {"name": config.name, "_version": "0.2.0"}
    # category_tag selects the CategoryProfile physics dispatch — dropping
    # it on a save/load round trip silently changes the loaded bike's
    # cluster to "unknown" (the file-based twin of the July-2 DB-bridge
    # bug; exposed July 13 when the epoch armed per-cluster grip knobs).
    d["category_tag"] = config.category_tag
    for section_name, _ in _SECTION_MAP.items():
        section_obj = getattr(config, section_name)
        d[section_name] = dataclass_to_dict(section_obj)
    return d


def config_from_dict(d: dict) -> BikeConfig:
    """Reconstruct a BikeConfig from a dict (e.g., loaded from JSON)."""
    name = d.get("name", "Custom Bike")
    kwargs = {"name": name, "category_tag": d.get("category_tag")}

    for section_name, cls in _SECTION_MAP.items():
        if section_name not in d:
            kwargs[section_name] = cls()  # Use defaults
            continue

        section_data = dict(d[section_name])

        # Handle DynoCurve fields specially
        if section_name == "engine" and "dyno_curve" in section_data:
            dc = section_data.pop("dyno_curve")
            if dc is not None:
                section_data["dyno_curve"] = dyno_from_dict(dc)

        # Filter to only known fields (ignore computed properties)
        field_names = {f.name for f in dataclasses.fields(cls)}
        filtered = {k: v for k, v in section_data.items() if k in field_names}

        try:
            kwargs[section_name] = cls(**filtered)
        except TypeError as e:
            print(f"Warning: error loading {section_name}: {e}")
            kwargs[section_name] = cls()

    return BikeConfig(**kwargs)


def save_config(config: BikeConfig, path: str | Path) -> Path:
    """Save a BikeConfig to a JSON file."""
    path = Path(path)
    d = config_to_dict(config)
    with open(path, "w") as f:
        json.dump(d, f, indent=2, cls=_NumpyEncoder)
    return path


def load_config(path: str | Path) -> BikeConfig:
    """Load a BikeConfig from a JSON file."""
    path = Path(path)
    with open(path) as f:
        d = json.load(f)
    return config_from_dict(d)
