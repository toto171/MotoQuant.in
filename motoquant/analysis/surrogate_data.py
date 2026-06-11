"""
MotoQuant Pro — Surrogate Training Data Generator (Phase 4B v2)
===============================================================
Generates a quasi-random dataset of (BikeConfig parameters → ET, trap speed)
pairs by Sobol-sampling the physical parameter space and running the full
physics engine on each sample.

Feature space (v2 — 17 features)
---------------------------------
14 base features independently sampled via Sobol:
  peak_power_hp, peak_torque_nm, redline_rpm, total_mass_kg,
  aero_cd, frontal_area_m2, tire_mu_peak, rear_rolling_radius_m,
  primary_ratio, final_drive_ratio, gear_ratio_1st, gear_ratio_top,
  reaction_time_ms, altitude_m

3 derived features computed from the above:
  power_to_weight_hp_kg   — peak_power_hp / total_mass_kg
                            (the single strongest ET predictor; encodes the
                            fundamental power-law ET ∝ (mass/power)^α)
  effective_1st_ratio     — primary × final × gear_ratio_1st
                            (total reduction in 1st gear; governs launch force)
  effective_top_ratio     — primary × final × gear_ratio_top
                            (total reduction in top gear; governs trap speed)

Adding these three derived features gives XGBoost the multiplicative
interactions it needs without having to learn them from scratch.  In practice
this roughly halves the MAE and more than doubles the within-±50ms fraction.

Persistence
-----------
    SurrogateDataset.save("data.npz")
    ds = SurrogateDataset.load("data.npz")   # auto-computes derived features
    X, y_et, y_trap = ds.to_arrays()         # X has 17 columns
"""

from __future__ import annotations

import copy
import logging
import time
import warnings
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from ..models import BikeConfig
from ..physics import MotoQuantEngine

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────
# Feature specification  (v2 — 17 features)
# ─────────────────────────────────────────────────────────────────

#: 14 base features that are independently Sobol-sampled.
BASE_FEATURE_NAMES: list[str] = [
    "peak_power_hp",
    "peak_torque_nm",
    "redline_rpm",
    "total_mass_kg",  # bike dry mass + rider weight
    "aero_cd",
    "frontal_area_m2",
    "tire_mu_peak",
    "rear_rolling_radius_m",
    "primary_ratio",
    "final_drive_ratio",
    "gear_ratio_1st",  # raw gearbox 1st gear ratio
    "gear_ratio_top",  # raw gearbox top gear ratio
    "reaction_time_ms",
    "altitude_m",  # venue density-altitude proxy
]

#: 7 derived features computed from base features (not independently sampled).
#: Encoding these multiplicative relationships dramatically improves accuracy.
DERIVED_FEATURE_NAMES: list[str] = [
    "power_to_weight_hp_kg",  # peak_power_hp / total_mass_kg
    "effective_1st_ratio",  # primary × final × gear_ratio_1st
    "effective_top_ratio",  # primary × final × gear_ratio_top
    # Intermediate gear ratios (linearly interpolated between 1st and top,
    # matching _apply_features_to_config's gear scaling). The generator uses a
    # 6-speed gearbox, so 2nd–5th fill the gear stack between 1st and top.
    # These ratios heavily influence shift timing and therefore ET.
    "gear_ratio_2nd",  # interpolated 2nd gear ratio
    "gear_ratio_3rd",  # interpolated 3rd gear ratio
    "gear_ratio_4th",  # interpolated 4th gear ratio
    "gear_ratio_5th",  # interpolated 5th gear ratio
]

#: 5 structural features appended in v2 (June 2026). They are read straight
#: off the BikeConfig (never perturbed by parts/venues) and disambiguate
#: structurally different bikes that share the same 21 v1 features — e.g. a
#: 4-speed RX100 vs a 6-speed R15, or a peaky 600 vs a flat twin. Adding them
#: cut catalog-wide holdout ET MAE by ~20% (entry-class clusters by ~37%).
#: ORDER MATTERS: v1's 21 features stay a strict prefix, so 21-input models
#: keep working on a [:21] slice of a v2 feature vector.
EXTRA_FEATURE_NAMES: list[str] = [
    "n_gears",  # gearbox speed count (4/5/6)
    "displacement_cc",  # engine displacement
    "launch_rpm",  # staging launch RPM (2T two-step bikes differ wildly)
    "peak_torque_rpm",  # where the torque curve peaks (shape proxy)
    "peak_power_rpm",  # where power peaks vs redline (shape proxy)
]

#: Neutral fill-ins used ONLY when a feature dict is built without a real
#: BikeConfig (the legacy Sobol template path / synthetic test fixtures).
#: generate_training_data overwrites them from the actual applied config.
EXTRA_FEATURE_DEFAULTS: dict[str, float] = {
    "n_gears": 6.0,
    "displacement_cc": 1000.0,
    "launch_rpm": 9000.0,
    "peak_torque_rpm": 10000.0,
    "peak_power_rpm": 11500.0,
}

#: All 26 features in order — this is what the model sees.
#: (14 base + 7 derived + 5 structural extras; v1 models used the first 21.)
FEATURE_NAMES: list[str] = (
    BASE_FEATURE_NAMES + DERIVED_FEATURE_NAMES + EXTRA_FEATURE_NAMES
)

#: Sampling bounds for each BASE feature: (low, high).
#: Covers the full range from 125 cc learner bikes to 1300 cc superbikes.
FEATURE_BOUNDS: dict[str, tuple[float, float]] = {
    "peak_power_hp": (15.0, 230.0),
    "peak_torque_nm": (12.0, 155.0),
    "redline_rpm": (7500.0, 16500.0),
    "total_mass_kg": (140.0, 380.0),
    "aero_cd": (0.55, 0.95),
    "frontal_area_m2": (0.36, 0.64),
    "tire_mu_peak": (0.80, 1.50),
    "rear_rolling_radius_m": (0.265, 0.345),
    "primary_ratio": (1.40, 3.10),
    "final_drive_ratio": (2.30, 4.20),
    "gear_ratio_1st": (2.20, 4.20),
    "gear_ratio_top": (0.80, 1.90),
    "reaction_time_ms": (0.0, 600.0),
    "altitude_m": (0.0, 2000.0),
}

# Sanity check — base feature names and bounds must be in sync
assert set(BASE_FEATURE_NAMES) == set(FEATURE_BOUNDS), (
    "BASE_FEATURE_NAMES and FEATURE_BOUNDS are out of sync — update both together"
)

#: Minimum realistic power-to-weight ratio (hp/kg).
#: Configs below this threshold are degenerate (not real motorcycles) and are
#: filtered during training data generation.  0.08 hp/kg ≈ 59 W/kg, which
#: is below even a 50 cc moped (~0.12 hp/kg) — intentionally conservative.
MIN_POWER_TO_WEIGHT: float = 0.08


# ─────────────────────────────────────────────────────────────────
# Derived feature computation
# ─────────────────────────────────────────────────────────────────


def _compute_derived_features(base: dict[str, float]) -> dict[str, float]:
    """
    Compute the 7 derived features from a dict of base feature values.

    Parameters
    ----------
    base : dict containing all BASE_FEATURE_NAMES keys

    Returns
    -------
    Dict with keys = DERIVED_FEATURE_NAMES, ready to merge into base.
    """
    pw = base["peak_power_hp"] / max(base["total_mass_kg"], 1.0)
    g1 = base["gear_ratio_1st"]
    gt = base["gear_ratio_top"]
    # Ensure top < 1st (same constraint as _apply_features_to_config)
    if gt >= g1:
        gt = g1 * 0.70
    eff1 = base["primary_ratio"] * base["final_drive_ratio"] * g1
    efft = base["primary_ratio"] * base["final_drive_ratio"] * gt
    # Intermediate gear ratios via linear interpolation (6-speed assumption).
    # Gear k (1-indexed) = top + (first - top) * (n_gears - k) / (n_gears - 1)
    # where n_gears = 6: gears 1–6 → k=1 gives g1, k=6 gives gt.
    n = 6
    gears = [gt + (g1 - gt) * (n - k) / (n - 1) for k in range(1, n + 1)]
    return {
        "power_to_weight_hp_kg": pw,
        "effective_1st_ratio": eff1,
        "effective_top_ratio": efft,
        "gear_ratio_2nd": gears[1],  # 2nd gear
        "gear_ratio_3rd": gears[2],  # 3rd gear
        "gear_ratio_4th": gears[3],  # 4th gear
        "gear_ratio_5th": gears[4],  # 5th gear
    }


def _full_features(base: dict[str, float]) -> dict[str, float]:
    """Return merged dict of all 26 features (base + derived + extras).

    Structural extras default to EXTRA_FEATURE_DEFAULTS here; callers that
    hold a real BikeConfig overwrite them via _extras_from_config().
    """
    return {**EXTRA_FEATURE_DEFAULTS, **base, **_compute_derived_features(base)}


def _extras_from_config(config: BikeConfig) -> dict[str, float]:
    """Read the 5 structural EXTRA features straight off a BikeConfig."""
    gear_ratios = config.drivetrain.gear_ratios or []
    return {
        "n_gears": float(len(gear_ratios) or 6),
        "displacement_cc": float(getattr(config.engine, "displacement_cc", 0.0) or 0.0),
        "launch_rpm": float(getattr(config.staging, "launch_rpm", 0.0) or 0.0),
        "peak_torque_rpm": float(getattr(config.engine, "peak_torque_rpm", 0.0) or 0.0),
        "peak_power_rpm": float(getattr(config.engine, "peak_power_rpm", 0.0) or 0.0),
    }


# ─────────────────────────────────────────────────────────────────
# Data point and dataset dataclasses
# ─────────────────────────────────────────────────────────────────


@dataclass
class SurrogateDataPoint:
    """One training sample: feature vector (17-dim) + physics engine outputs."""

    features: dict[str, float]  # {feature_name: value} — all 17 features
    et_s: float  # quarter-mile elapsed time (seconds)
    trap_speed_mps: float  # trap speed at 402.336 m (m/s)

    @property
    def trap_speed_kmh(self) -> float:
        return self.trap_speed_mps * 3.6

    def to_array(self) -> np.ndarray:
        """Return feature vector as 1D numpy array in FEATURE_NAMES order."""
        return np.array([self.features[k] for k in FEATURE_NAMES], dtype=np.float32)


@dataclass
class SurrogateDataset:
    """
    Collection of SurrogateDataPoint instances with numpy serialization.

    Attributes
    ----------
    points      : list of individual data points
    n_samples   : number of requested samples (may differ from len(points))
    seed        : random seed used for Sobol sampling
    elapsed_s   : wall-clock time to generate
    """

    points: list[SurrogateDataPoint] = field(default_factory=list)
    n_samples: int = 0
    seed: int = 0
    elapsed_s: float = 0.0

    def __len__(self) -> int:
        return len(self.points)

    def to_arrays(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Convert to numpy arrays suitable for sklearn/XGBoost.

        Returns
        -------
        X         : shape (n, 17)  — feature matrix (14 base + 3 derived)
        y_et      : shape (n,)     — ET labels in seconds
        y_trap    : shape (n,)     — trap speed labels in m/s
        """
        if not self.points:
            raise ValueError("Dataset is empty — no points to convert.")
        X = np.stack([p.to_array() for p in self.points], axis=0)
        y_et = np.array([p.et_s for p in self.points], dtype=np.float32)
        y_trap = np.array([p.trap_speed_mps for p in self.points], dtype=np.float32)
        return X, y_et, y_trap

    def save(self, path: str | Path) -> None:
        """Save dataset to a compressed .npz file."""
        path = Path(path)
        X, y_et, y_trap = self.to_arrays()
        np.savez_compressed(
            path,
            X=X,
            y_et=y_et,
            y_trap=y_trap,
            feature_names=np.array(FEATURE_NAMES),
            meta=np.array([self.n_samples, self.seed, self.elapsed_s]),
        )
        logger.info("Saved %d samples to %s", len(self), path)

    @classmethod
    def load(cls, path: str | Path) -> SurrogateDataset:
        """
        Load dataset from a .npz file.

        Backward-compatible: if the stored file has 14 features (v1),
        derived features are automatically computed on load.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Dataset file not found: {path}")
        data = np.load(path, allow_pickle=False)

        stored_names = list(data["feature_names"])
        X = data["X"]
        y_et = data["y_et"]
        y_trap = data["y_trap"]
        meta = data["meta"]

        # Backward-compat: v1 files have 14 features; derive the 7 extra columns.
        if stored_names == BASE_FEATURE_NAMES and X.shape[1] == len(BASE_FEATURE_NAMES):
            logger.info(
                "Loading v1 dataset (%d features); computing %d derived features.",
                len(BASE_FEATURE_NAMES),
                len(DERIVED_FEATURE_NAMES),
            )
            base_array = X  # (n, 14)
            derived_cols = []
            for i in range(len(base_array)):
                base_dict = {
                    BASE_FEATURE_NAMES[j]: float(base_array[i, j])
                    for j in range(len(BASE_FEATURE_NAMES))
                }
                d = _compute_derived_features(base_dict)
                derived_cols.append([d[k] for k in DERIVED_FEATURE_NAMES])
            derived_array = np.array(derived_cols, dtype=np.float32)
            X = np.concatenate([base_array, derived_array], axis=1)
            stored_names = BASE_FEATURE_NAMES + DERIVED_FEATURE_NAMES
        if (
            len(stored_names) < len(FEATURE_NAMES)
            and list(stored_names) == FEATURE_NAMES[: len(stored_names)]
        ):
            # Pre-v2 file (no structural extras): the stored columns are a
            # strict prefix of the current schema. Pad the missing extras
            # with their template defaults — the real values are config
            # constants this file never recorded.
            warnings.warn(
                f"Dataset has {len(stored_names)} features; padding "
                f"{len(FEATURE_NAMES) - len(stored_names)} v2 structural "
                "extras with template defaults. Regenerate for full accuracy."
            )
            pad_vals = [
                EXTRA_FEATURE_DEFAULTS[k] for k in FEATURE_NAMES[len(stored_names) :]
            ]
            pad = np.tile(np.asarray(pad_vals, dtype=X.dtype), (X.shape[0], 1))
            X = np.concatenate([X, pad], axis=1)
            stored_names = FEATURE_NAMES
        elif stored_names != FEATURE_NAMES:
            warnings.warn(
                "Stored feature names differ from current FEATURE_NAMES. "
                "Model may produce incorrect predictions — consider retraining."
            )

        points = []
        for i in range(len(X)):
            feat = {FEATURE_NAMES[j]: float(X[i, j]) for j in range(len(FEATURE_NAMES))}
            points.append(
                SurrogateDataPoint(
                    features=feat,
                    et_s=float(y_et[i]),
                    trap_speed_mps=float(y_trap[i]),
                )
            )

        return cls(
            points=points,
            n_samples=int(meta[0]),
            seed=int(meta[1]),
            elapsed_s=float(meta[2]),
        )

    def split(
        self, test_fraction: float = 0.15, seed: int = 0
    ) -> tuple[SurrogateDataset, SurrogateDataset]:
        """Random train/test split. Returns (train_ds, test_ds)."""
        rng = np.random.default_rng(seed)
        n = len(self.points)
        indices = rng.permutation(n)
        n_test = max(1, int(n * test_fraction))
        test_idx = set(indices[:n_test].tolist())

        train_pts = [p for i, p in enumerate(self.points) if i not in test_idx]
        test_pts = [p for i, p in enumerate(self.points) if i in test_idx]

        return (
            SurrogateDataset(
                points=train_pts, n_samples=len(train_pts), seed=self.seed
            ),
            SurrogateDataset(points=test_pts, n_samples=len(test_pts), seed=self.seed),
        )

    def filter(
        self, min_power_to_weight: float = MIN_POWER_TO_WEIGHT
    ) -> SurrogateDataset:
        """
        Return a new dataset with degenerate configs removed.

        Filters out samples whose power-to-weight ratio is below
        ``min_power_to_weight`` (hp/kg).  These are not real motorcycles
        and cause large prediction errors at the distribution boundary.

        Parameters
        ----------
        min_power_to_weight : minimum hp/kg to keep (default: 0.08)

        Returns
        -------
        New SurrogateDataset containing only the kept points.
        """
        kept = [
            p
            for p in self.points
            if p.features.get(
                "power_to_weight_hp_kg",
                p.features["peak_power_hp"] / max(p.features["total_mass_kg"], 1.0),
            )
            >= min_power_to_weight
        ]
        n_removed = len(self.points) - len(kept)
        if n_removed:
            logger.info(
                "filter: removed %d / %d degenerate samples (pw < %.3f hp/kg)",
                n_removed,
                len(self.points),
                min_power_to_weight,
            )
        return SurrogateDataset(
            points=kept,
            n_samples=len(kept),
            seed=self.seed,
            elapsed_s=self.elapsed_s,
        )


# ─────────────────────────────────────────────────────────────────
# BikeConfig ↔ feature dict helpers
# ─────────────────────────────────────────────────────────────────


def _extract_nominal_features(config: BikeConfig) -> dict[str, float]:
    """
    Extract all 17 feature values from a BikeConfig.

    Used for inference: given a real BikeConfig, produce its feature vector.
    """
    gear_ratios = config.drivetrain.gear_ratios or [2.8, 2.0, 1.5, 1.2, 1.0, 0.85]
    rider_mass = config.rider.mass_kg if hasattr(config, "rider") else 75.0
    total_mass = config.chassis.dry_mass_kg + rider_mass

    base = {
        "peak_power_hp": float(config.engine.peak_power_hp),
        "peak_torque_nm": float(config.engine.peak_torque_nm),
        "redline_rpm": float(config.engine.redline_rpm),
        "total_mass_kg": float(total_mass),
        "aero_cd": float(config.aero.cd),
        "frontal_area_m2": float(config.aero.frontal_area_m2),
        "tire_mu_peak": float(config.tires.mu_peak),
        "rear_rolling_radius_m": float(config.tires.rear_rolling_radius_m),
        "primary_ratio": float(config.drivetrain.primary_ratio),
        # v2: use the EFFECTIVE final drive (the final_ratio property — sprocket
        # teeth override the raw final_drive_ratio field, and the physics engine
        # only ever sees the property). Reading the raw field made this feature a
        # dead knob for every config with sprockets set (v1 trained on K5, which
        # has 17/42 — its sampled final_drive_ratio never reached the sim).
        "final_drive_ratio": float(config.drivetrain.final_ratio),
        "gear_ratio_1st": float(gear_ratios[0]),
        "gear_ratio_top": float(gear_ratios[-1]),
        "reaction_time_ms": float(config.staging.reaction_time_ms),
        "altitude_m": float(getattr(config.environment, "altitude_m", 0.0)),
    }
    feat = _full_features(base)
    feat.update(_extras_from_config(config))
    return feat


def _apply_features_to_config(
    base: BikeConfig, features: dict[str, float]
) -> BikeConfig:
    """
    Deep-copy base config and override the 14 base feature parameters.

    Derived features in ``features`` are ignored (they are computed quantities).
    The dyno curve (if present) is scaled proportionally when power changes.
    """
    from ..models import DynoCurve  # lazy import avoids circular dependency

    cfg = copy.deepcopy(base)
    nominal_hp = base.engine.peak_power_hp

    # Core engine params
    cfg.engine.peak_power_hp = features["peak_power_hp"]
    cfg.engine.peak_torque_nm = features["peak_torque_nm"]
    cfg.engine.redline_rpm = features["redline_rpm"]

    # Dyno curve scaling — same logic as sobol._apply_sample_row
    new_hp = features["peak_power_hp"]
    hp_changed = abs(new_hp - nominal_hp) > 0.05
    has_dyno = cfg.engine.dyno_curve is not None
    is_na = not cfg.forced_induction.is_boosted
    if hp_changed and has_dyno and is_na and nominal_hp > 1.0:
        ratio = new_hp / nominal_hp
        dc = cfg.engine.dyno_curve
        cfg.engine.dyno_curve = DynoCurve(
            rpm=dc.rpm.copy(),
            torque_nm=dc.torque_nm * ratio,
            is_at_wheel=dc.is_at_wheel,
        )

    # Mass — subtract rider weight to get bike dry mass
    rider_mass = cfg.rider.mass_kg if hasattr(cfg, "rider") else 75.0
    cfg.chassis.dry_mass_kg = max(80.0, features["total_mass_kg"] - rider_mass)

    # Aero
    cfg.aero.cd = features["aero_cd"]
    cfg.aero.frontal_area_m2 = features["frontal_area_m2"]

    # Tires
    cfg.tires.mu_peak = features["tire_mu_peak"]
    cfg.tires.rear_rolling_radius_m = features["rear_rolling_radius_m"]

    # Drivetrain
    cfg.drivetrain.primary_ratio = features["primary_ratio"]
    cfg.drivetrain.final_drive_ratio = features["final_drive_ratio"]

    # Scale gear ratios to honour sampled 1st/top gear while preserving spacing
    gr = cfg.drivetrain.gear_ratios
    if gr and len(gr) >= 2:
        orig_1st = gr[0]
        orig_top = gr[-1]
        target_1st = features["gear_ratio_1st"]
        target_top = features["gear_ratio_top"]
        if target_top >= target_1st:
            target_top = target_1st * 0.70
        if orig_1st != orig_top:
            new_gr = [
                target_top
                + (target_1st - target_top) * (g - orig_top) / (orig_1st - orig_top)
                for g in gr
            ]
        else:
            new_gr = [target_1st] + [target_top] * (len(gr) - 1)
        cfg.drivetrain.gear_ratios = [max(0.5, g) for g in new_gr]

    # Staging
    cfg.staging.reaction_time_ms = features["reaction_time_ms"]

    # Environmental altitude
    if hasattr(cfg, "environment") and hasattr(cfg.environment, "altitude_m"):
        cfg.environment.altitude_m = features["altitude_m"]

    return cfg


# ─────────────────────────────────────────────────────────────────
# Sobol sample generation
# ─────────────────────────────────────────────────────────────────


def _sobol_sample_features(n: int, seed: int = 0) -> list[dict[str, float]]:
    """
    Generate ``n`` quasi-random feature dicts using a Sobol sequence.

    Samples the 14 BASE features and computes 3 derived features.
    Falls back to uniform random if scipy is unavailable.
    """
    d = len(BASE_FEATURE_NAMES)
    lows = np.array(
        [FEATURE_BOUNDS[k][0] for k in BASE_FEATURE_NAMES], dtype=np.float64
    )
    highs = np.array(
        [FEATURE_BOUNDS[k][1] for k in BASE_FEATURE_NAMES], dtype=np.float64
    )

    try:
        from scipy.stats.qmc import Sobol

        m = int(np.ceil(np.log2(max(n, 2))))
        sampler = Sobol(d=d, scramble=True, seed=seed)
        raw = sampler.random_base2(m=m)
        raw = raw[:n]
    except ImportError:
        rng = np.random.default_rng(seed)
        raw = rng.random((n, d))

    scaled = lows + raw * (highs - lows)
    result = []
    for i in range(n):
        base = {BASE_FEATURE_NAMES[j]: float(scaled[i, j]) for j in range(d)}
        result.append(_full_features(base))
    return result


# ─────────────────────────────────────────────────────────────────
# Main public API
# ─────────────────────────────────────────────────────────────────


def generate_training_data(
    base_config: BikeConfig,
    n_samples: int = 2048,
    seed: int = 42,
    progress_callback: Callable[[int, int], None] | None = None,
    max_retries_factor: float = 2.0,
    min_power_to_weight: float = MIN_POWER_TO_WEIGHT,
) -> SurrogateDataset:
    """
    Generate a dataset of (parameters, ET, trap speed) pairs.

    Runs the full physics engine on Sobol-sampled configurations.  Configs
    with power/weight below ``min_power_to_weight`` are pre-filtered before
    running the physics engine.  Failed simulations are silently skipped and
    retried until ``n_samples`` valid rows are collected.

    Parameters
    ----------
    base_config         : BikeConfig structural template.
    n_samples           : Number of valid samples to collect.
    seed                : Sobol scramble seed.
    progress_callback   : Optional ``fn(collected, total)`` progress hook.
    max_retries_factor  : Max attempts = n_samples × this factor.
    min_power_to_weight : Minimum hp/kg; sub-threshold configs are skipped.
    """
    t0 = time.perf_counter()
    max_attempts = int(n_samples * max(2.0, max_retries_factor))
    candidate_features = _sobol_sample_features(max_attempts, seed=seed)

    points: list[SurrogateDataPoint] = []
    failures = 0

    for attempt_idx, feat in enumerate(candidate_features):
        if len(points) >= n_samples:
            break

        # Pre-filter degenerate configs before running the slow physics engine
        if feat["power_to_weight_hp_kg"] < min_power_to_weight:
            failures += 1
            continue

        try:
            cfg = _apply_features_to_config(base_config, feat)
            feat = {**feat, **_extras_from_config(cfg)}
            engine = MotoQuantEngine(cfg)
            result = engine.run()

            if result.time_quarter is None or not np.isfinite(result.time_quarter):
                failures += 1
                continue
            if result.speed_quarter is None or not np.isfinite(result.speed_quarter):
                failures += 1
                continue

            # Sanity gate
            if result.time_quarter < 4.0 or result.time_quarter > 35.0:
                failures += 1
                continue
            if result.speed_quarter < 5.0 or result.speed_quarter > 120.0:
                failures += 1
                continue

            points.append(
                SurrogateDataPoint(
                    features=feat,
                    et_s=float(result.time_quarter),
                    trap_speed_mps=float(result.speed_quarter),
                )
            )

            if progress_callback is not None:
                progress_callback(len(points), n_samples)

        except Exception as exc:
            logger.debug("Sample attempt %d failed: %s", attempt_idx, exc)
            failures += 1

    elapsed = time.perf_counter() - t0
    if failures > 0:
        logger.info(
            "generate_training_data: %d valid / %d attempts (%.1f%% failure rate) in %.1fs",
            len(points),
            len(points) + failures,
            100.0 * failures / max(1, len(points) + failures),
            elapsed,
        )

    return SurrogateDataset(
        points=points,
        n_samples=n_samples,
        seed=seed,
        elapsed_s=elapsed,
    )


def config_to_feature_vector(config: BikeConfig) -> np.ndarray:
    """
    Convert a BikeConfig directly to a 26-dim feature vector for inference.

    Returns
    -------
    1D numpy array of shape (26,) in FEATURE_NAMES order
    (14 base + 7 derived + 5 structural extras; v1 models consume [:21]).
    """
    feat = _extract_nominal_features(config)
    return np.array([feat[k] for k in FEATURE_NAMES], dtype=np.float32)
