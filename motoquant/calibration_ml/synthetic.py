"""
Synthetic training-data generator for the calibrator.

Pipeline per sample:
  1. Pick a base BikeConfig (rotated through the supplied list, or sampled
     from 30 random ALL_KNOWN_BIKES configs when base_configs is None)
  2. Perturb the environment slightly (DA, temp, track_temp, RH variation)
  3. Jitter rider_mass_kg (65-95 kg Gaussian) -- was always 75.0 in v1
  4. Sample correction factors from CorrectionTargets within PERTURBATION_RANGES
     - mode='joint' (default): perturb all 3 factors simultaneously
     - mode='one_at_a_time': perturb ONLY ONE factor (others held at 1.0)
       This breaks the ill-posed inverse problem: the model can learn what
       each factor independently predicts without aliasing.
  5. Apply the correction to a deep copy of the config
  6. Run MotoQuantEngine on the perturbed config -> measured ET/trap/60ft
  7. Build the feature vector from the UNPERTURBED config + measurement.

The model learns the inverse mapping: given the spec we know about and
the outcome we measured, predict the perturbation that produced it.

Schema v2: 3 targets (cd_factor dropped), inertia_factor range [0.85, 1.20].
"""

from __future__ import annotations

import copy
import warnings
from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np

from .features import FEATURE_DIM, MeasuredRun, extract_features
from .targets import CorrectionTargets

__all__ = [
    "PERTURBATION_RANGES",
    "ENV_PERTURBATION",
    "SyntheticDataset",
    "generate_one",
    "generate_dataset",
    "default_base_configs",
]


# Plausible ranges for each correction factor.
# cd_factor removed (R²=-0.06, unlearnable from single ET measurement).
# inertia_factor tightened 0.6-1.8 -> 0.85-1.20 (audit feedback: too wide
# caused bias toward fast-bike corrections).
PERTURBATION_RANGES: dict[str, tuple[float, float]] = {
    "mu_peak_factor": (0.88, 1.12),
    "peak_torque_factor": (0.88, 1.12),
    "inertia_factor": (0.85, 1.20),
}

# Environment jitter -- one stddev each. Clipped to physical bounds.
# track_temp_c added (was missing in v1, causing zero-variance feature).
ENV_PERTURBATION = {
    "ambient_temp_c": dict(sigma=5.0, lo=5.0, hi=45.0),
    "track_temp_c": dict(sigma=5.0, lo=5.0, hi=60.0),
    "humidity_pct": dict(sigma=15.0, lo=10.0, hi=95.0),
    "altitude_m": dict(sigma=200.0, lo=0.0, hi=3000.0),
}

# Rider mass jitter (was always 75.0 in v1 -- zero variance).
_RIDER_MASS_MU = 75.0
_RIDER_MASS_SIGMA = 8.0
_RIDER_MASS_LO = 55.0
_RIDER_MASS_HI = 110.0


@dataclass
class SyntheticDataset:
    """Training data for the calibrator.

    X: (N, FEATURE_DIM) float32 -- predictor matrix
    Y: (N, 3)           float32 -- correction-factor labels (schema v2)
    n: int                       -- effective row count (= len(X))
    """

    X: np.ndarray
    Y: np.ndarray
    n: int

    def save(self, path: str) -> None:
        np.savez_compressed(path, X=self.X, Y=self.Y, n=np.array(self.n))

    @classmethod
    def load(cls, path: str) -> "SyntheticDataset":
        d = np.load(path, allow_pickle=False)
        X = d["X"]
        Y = d["Y"]
        # 'n' key is optional — older saves (chunked pipeline) omit it.
        n = int(d["n"]) if "n" in d.files else len(X)
        return cls(X=X, Y=Y, n=n)


# Map our internal short name -> the BikeConfig.environment attribute name.
_ENV_ATTR_MAP = {
    "ambient_temp_c": "ambient_temp_c",
    "track_temp_c": "track_temp_c",
    "humidity_pct": "relative_humidity_pct",
    "altitude_m": "altitude_m",
}


def _perturb_environment(env: Any, rng: np.random.Generator) -> None:
    """Add small Gaussian jitter to env in place. Clipped to physical bounds."""
    if env is None:
        return
    for short_name, spec in ENV_PERTURBATION.items():
        env_attr = _ENV_ATTR_MAP.get(short_name, short_name)
        current = getattr(env, env_attr, None)
        if current is None:
            continue
        try:
            new = float(current) + float(rng.normal(0.0, spec["sigma"]))
            new = float(np.clip(new, spec["lo"], spec["hi"]))
            setattr(env, env_attr, new)
        except (TypeError, ValueError):
            continue


def _sample_correction(
    rng: np.random.Generator, mode: str = "joint"
) -> CorrectionTargets:
    """Sample correction factors within PERTURBATION_RANGES.

    mode='joint'          all 3 factors sampled independently (default)
    mode='one_at_a_time'  exactly ONE factor perturbed; others stay at 1.0.
                          Breaks the ill-posed inverse problem by ensuring
                          each training sample has an unambiguous signal source.
    """
    if mode == "one_at_a_time":
        target_names = list(PERTURBATION_RANGES.keys())
        chosen = target_names[int(rng.integers(0, len(target_names)))]
        factors = {k: 1.0 for k in target_names}
        lo, hi = PERTURBATION_RANGES[chosen]
        # Draw from (lo, 0.97) union (1.03, hi) to avoid near-identity samples
        # that carry zero training signal.
        lo_gap, hi_gap = min(0.97, lo + 0.02), max(1.03, hi - 0.02)
        if rng.random() < 0.5 and lo < lo_gap:
            factors[chosen] = float(rng.uniform(lo, lo_gap))
        else:
            factors[chosen] = float(rng.uniform(hi_gap, hi))
        return CorrectionTargets(
            mu_peak_factor=factors["mu_peak_factor"],
            peak_torque_factor=factors["peak_torque_factor"],
            inertia_factor=factors["inertia_factor"],
        )
    else:  # 'joint'
        return CorrectionTargets(
            mu_peak_factor=float(rng.uniform(*PERTURBATION_RANGES["mu_peak_factor"])),
            peak_torque_factor=float(
                rng.uniform(*PERTURBATION_RANGES["peak_torque_factor"])
            ),
            inertia_factor=float(rng.uniform(*PERTURBATION_RANGES["inertia_factor"])),
        )


def default_base_configs(n: int = 32, seed: int = 42) -> list[Any]:
    """Return up to `n` BikeConfig objects sampled from ALL_KNOWN_BIKES.

    Falls back gracefully: bikes that fail spec_to_bike_config are skipped
    silently. Always includes K5/R1/Hayabusa so reference baselines are
    in the training distribution.
    """
    from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8
    from motoquant.scraper.importer import spec_to_bike_config
    from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

    rng = np.random.default_rng(seed)
    reference = [gsxr1000_k5(), yzfr1_4c8(), hayabusa_gen1()]

    # Shuffle and try to build configs until we have n-3 more
    all_specs = list(ALL_KNOWN_BIKES)
    rng.shuffle(all_specs)

    configs = []
    for spec in all_specs:
        if len(configs) >= n - 3:
            break
        try:
            cfg = spec_to_bike_config(spec)
            if cfg is not None:
                configs.append(cfg)
        except Exception:
            continue  # skip un-buildable specs silently

    return reference + configs


def generate_one(
    base_config: Any,
    rng: np.random.Generator,
    mode: str = "joint",
) -> tuple[np.ndarray, np.ndarray] | None:
    """Generate one synthetic (feature_vec, correction_array) pair.

    Args:
      base_config: BikeConfig to perturb
      rng:  NumPy Generator for reproducibility
      mode: 'joint' or 'one_at_a_time' (see _sample_correction)

    Returns None if the perturbed sim fails (DNF, exception, NaN). Caller
    should retry with a fresh draw.
    """
    from ..physics import MotoQuantEngine

    target = _sample_correction(rng, mode=mode)

    # Deep-copy + jitter environment + apply physics corrections
    spec_with_env = copy.deepcopy(base_config)
    _perturb_environment(getattr(spec_with_env, "environment", None), rng)

    # Jitter rider mass (was always 75 kg in v1 -- zero variance feature)
    rider_mass = float(
        np.clip(
            rng.normal(_RIDER_MASS_MU, _RIDER_MASS_SIGMA),
            _RIDER_MASS_LO,
            _RIDER_MASS_HI,
        )
    )

    perturbed = target.apply(spec_with_env)

    # Run sim on the perturbed config
    try:
        result = MotoQuantEngine(perturbed).run()
    except Exception:
        return None

    # Reject DNFs and over-time runs
    if not getattr(result, "finished_quarter", True):
        return None
    et = getattr(result, "time_quarter", None)
    if et is None or not np.isfinite(et) or et <= 0:
        return None

    trap = getattr(result, "speed_quarter", 0.0) * 3.6  # m/s -> km/h
    sixty = getattr(result, "time_60ft", 0.0)
    if not np.isfinite(trap) or not np.isfinite(sixty):
        return None

    measured = MeasuredRun(
        et_s=float(et),
        trap_kmh=float(trap),
        sixty_ft_s=float(sixty),
        rider_mass_kg=rider_mass,
    )
    val = getattr(result, "time_330ft", None)
    if val is not None and np.isfinite(val):
        measured.three_thirty_s = float(val)
    val = getattr(result, "time_eighth", None)
    if val is not None and np.isfinite(val):
        measured.eighth_s = float(val)

    # Feature vector uses spec_with_env (the spec we'd "know" before the
    # measurement -- env is included so the model can learn DA effects).
    x = extract_features(spec_with_env, measured)
    if not np.all(np.isfinite(x)):
        return None
    return x, target.to_array()


def generate_dataset(
    base_configs: Iterable[Any] | None = None,
    n_samples: int = 1000,
    *,
    seed: int = 42,
    mode: str = "one_at_a_time",
    verbose: bool = False,
    max_attempt_multiplier: int = 10,
) -> SyntheticDataset:
    """Generate N valid synthetic training samples.

    Args:
      base_configs: list of BikeConfig objects, rotated round-robin to
        balance the dataset. When None (default), 32 bikes are sampled
        from ALL_KNOWN_BIKES via spec_to_bike_config (includes K5/R1/Busa).
      n_samples: target number of valid samples.
      seed: RNG seed for reproducibility.
      mode: 'one_at_a_time' (default, recommended) or 'joint'.
        one_at_a_time perturbs exactly ONE correction factor per sample,
        breaking the ill-posed inverse problem. Joint perturbs all 3.
      verbose: print progress every 100 valid samples.
      max_attempt_multiplier: bail after n_samples * this many attempts.

    Returns:
      SyntheticDataset with Y of shape (N, 3) -- schema v2 (no cd_factor).
    """
    if base_configs is None:
        if verbose:
            print("  [generate_dataset] building default 32-bike catalog...")
        base_configs = default_base_configs(n=32, seed=seed)
        if verbose:
            print(f"  [generate_dataset] {len(base_configs)} bikes loaded")

    base_configs = list(base_configs)
    if not base_configs:
        raise ValueError("base_configs must be non-empty")

    rng = np.random.default_rng(seed)
    X_list: list[np.ndarray] = []
    Y_list: list[np.ndarray] = []
    attempts = 0
    max_attempts = max(n_samples * max_attempt_multiplier, n_samples + 100)
    n_targets = len(PERTURBATION_RANGES)  # 3

    while len(X_list) < n_samples and attempts < max_attempts:
        attempts += 1
        base = base_configs[attempts % len(base_configs)]
        result = generate_one(base, rng, mode=mode)
        if result is None:
            continue
        x, y = result
        X_list.append(x)
        Y_list.append(y)
        if verbose and len(X_list) % 100 == 0:
            print(f"  {len(X_list)}/{n_samples} samples ({attempts} attempts)")

    if verbose and len(X_list) < n_samples:
        print(
            f"  WARN: only {len(X_list)} valid samples after {attempts} attempts; "
            f"check base configs (may have unsim-able bikes)"
        )

    X = (
        np.array(X_list, dtype=np.float32)
        if X_list
        else np.zeros((0, FEATURE_DIM), dtype=np.float32)
    )
    Y = (
        np.array(Y_list, dtype=np.float32)
        if Y_list
        else np.zeros((0, n_targets), dtype=np.float32)
    )
    return SyntheticDataset(X=X, Y=Y, n=len(X_list))
