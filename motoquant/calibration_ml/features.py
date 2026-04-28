"""
Feature extraction for the calibrator.

Inputs:
  bike_config (BikeConfig): the structural spec we want to calibrate
  measured_run (MeasuredRun): the real-world telemetry we collected

Output:
  np.ndarray of shape (FEATURE_DIM,) -- the predictor for the 3 XGB models

Schema v2 (FEATURE_SCHEMA_VERSION=2):
  - Fixed 5 dead/zero-variance features from v1:
      track_temp_c       now jittered via ENV_PERTURBATION in synthetic.py
      rider_mass_kg      now jittered 65-95 kg in generate_one
      rear_tire_diameter_mm  fixed: was reading non-existent 'rear_diameter_mm';
                             now uses rear_rolling_radius_m * 2000.0
      tire_compound_code REMOVED (TireParams has no 'compound' field; always 0)
      drive_type_code    fixed: was reading non-existent 'belt_drive'/'shaft_drive';
                         now 0=chain (chain_pitch present), 1=non-chain
  - FEATURE_DIM dropped from 25 -> 24 (tire_compound_code removed)

Schema is APPEND-ONLY going forward. Adding a feature: append at end + bump
FEATURE_SCHEMA_VERSION. Existing trained models become incompatible -- also
bump Calibrator.version + retrain.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

__all__ = [
    "FEATURE_DIM",
    "FEATURE_NAMES",
    "FEATURE_SCHEMA_VERSION",
    "MeasuredRun",
    "extract_features",
    "feature_dict",
]


# ── Schema ──────────────────────────────────────────────────────────

FEATURE_SCHEMA_VERSION: int = 2

FEATURE_NAMES: list[str] = [
    # Bike spec (10)
    "displacement_cc",
    "peak_power_hp",
    "peak_torque_nm",
    "peak_torque_rpm",
    "redline_rpm",
    "dry_mass_kg",
    "wheelbase_mm",
    "front_sprocket",
    "rear_sprocket",
    "primary_ratio",
    # Environment (5)
    "ambient_temp_c",
    "track_temp_c",          # jittered via ENV_PERTURBATION (fixed v2)
    "humidity_pct",
    "altitude_m",
    "density_altitude_ft",
    # Measured run (6)
    "measured_et_s",
    "measured_trap_kmh",
    "measured_60ft_s",
    "measured_330ft_s",      # 0 if unavailable
    "measured_eighth_s",     # 0 if unavailable
    "rider_mass_kg",         # jittered 65-95 kg in synthetic (fixed v2)
    # Misc bike codes (3)  -- tire_compound_code removed in v2 (no attr exists)
    "rear_tire_diameter_mm", # fixed v2: rear_rolling_radius_m * 2000
    "drive_type_code",       # fixed v2: 0=chain, 1=non-chain
    "stroke_type",           # 2 for 2T, 4 for 4T
]
FEATURE_DIM = len(FEATURE_NAMES)  # 24


@dataclass
class MeasuredRun:
    """Real-world measurement of a single quarter-mile pass."""

    et_s: float
    trap_kmh: float
    sixty_ft_s: float
    rider_mass_kg: float = 75.0
    three_thirty_s: float | None = None
    eighth_s: float | None = None


# ── Extraction ──────────────────────────────────────────────────────


def _safe_float(obj: Any, attr: str, default: float = 0.0) -> float:
    """Read obj.attr as float; tolerate None / missing attribute."""
    val = getattr(obj, attr, None) if obj is not None else None
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _density_altitude_ft(env: Any) -> float:
    """Call env.density_altitude_ft() if available; else 0."""
    if env is None:
        return 0.0
    fn = getattr(env, "density_altitude_ft", None)
    if not callable(fn):
        return 0.0
    try:
        return float(fn())
    except Exception:
        return 0.0


def _drive_type_code(d: Any) -> int:
    """0=chain (chain_pitch set), 1=non-chain (belt/shaft/unknown).

    DrivetrainParams exposes chain_pitch (str like '530') or None for
    non-chain-drive bikes. belt_drive / shaft_drive are NOT fields on
    DrivetrainParams so the v1 belt/shaft checks were always zero-variance.
    """
    if d is None:
        return 1
    cp = getattr(d, "chain_pitch", None)
    return 0 if cp else 1


def extract_features(bike_config: Any, measured: MeasuredRun) -> np.ndarray:
    """Build the FEATURE_DIM feature vector for the calibrator.

    Tolerant of missing attributes -- returns 0 for any field that can't
    be resolved. Never raises on a partially-populated BikeConfig.
    """
    e = getattr(bike_config, "engine", None)
    c = getattr(bike_config, "chassis", None)
    d = getattr(bike_config, "drivetrain", None)
    t = getattr(bike_config, "tires", None)
    env = getattr(bike_config, "environment", None)

    vec = np.zeros(FEATURE_DIM, dtype=np.float32)

    # Bike spec (0..9)
    vec[0] = _safe_float(e, "displacement_cc")
    vec[1] = _safe_float(e, "peak_power_hp")
    vec[2] = _safe_float(e, "peak_torque_nm")
    vec[3] = _safe_float(e, "peak_torque_rpm")
    vec[4] = _safe_float(e, "redline_rpm")
    vec[5] = _safe_float(c, "dry_mass_kg")
    vec[6] = _safe_float(c, "wheelbase_mm")
    vec[7] = _safe_float(d, "front_sprocket")
    vec[8] = _safe_float(d, "rear_sprocket")
    vec[9] = _safe_float(d, "primary_ratio")

    # Environment (10..14)
    vec[10] = _safe_float(env, "ambient_temp_c", 25.0)
    vec[11] = _safe_float(env, "track_temp_c", 30.0)    # v2: real attr, now jittered
    vec[12] = _safe_float(env, "relative_humidity_pct", 50.0)
    vec[13] = _safe_float(env, "altitude_m")
    vec[14] = _density_altitude_ft(env)

    # Measured run (15..20)
    vec[15] = float(measured.et_s)
    vec[16] = float(measured.trap_kmh)
    vec[17] = float(measured.sixty_ft_s)
    vec[18] = float(measured.three_thirty_s or 0.0)
    vec[19] = float(measured.eighth_s or 0.0)
    vec[20] = float(measured.rider_mass_kg)

    # Misc codes (21..23)
    # rear_tire_diameter_mm: v2 fix -- was 'rear_diameter_mm' (doesn't exist);
    # correct attr is rear_rolling_radius_m; multiply by 2000 for mm diameter.
    rear_radius_m = _safe_float(t, "rear_rolling_radius_m")
    vec[21] = rear_radius_m * 2000.0  # ~580-620mm for typical sport bikes
    vec[22] = float(_drive_type_code(d))
    vec[23] = _safe_float(e, "stroke_type", 4.0)

    return vec


def feature_dict(bike_config: Any, measured: MeasuredRun) -> dict[str, float]:
    """Same as extract_features but returns a {name: value} dict (for debugging)."""
    return dict(zip(FEATURE_NAMES, extract_features(bike_config, measured).tolist()))
