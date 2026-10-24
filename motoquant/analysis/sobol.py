"""
MotoQuant — Sobol Sensitivity Analysis
======================================
Global sensitivity analysis (GSA) for the quarter-mile simulation.

Identifies which bike/setup parameters drive the most variance in
quarter-mile elapsed time.  Uses the Saltelli quasi-random sampling
scheme and the Jansen estimator for first-order (S1) and total-order
(ST) Sobol indices via the SALib library.

Interpretation
--------------
S1  (first-order) ≈ fraction of ET variance explained by this
    parameter *alone*, holding all others fixed.

ST  (total-order) ≈ fraction of ET variance attributable to this
    parameter *including all its interactions* with other params.

A high (ST - S1) means the parameter interacts strongly with others.
The sum of all S1 values ≈ 1 for an additive model; > 1 indicates
significant interaction effects.

Parameter specification
-----------------------
Each parameter is described by a ``SobolParamSpec``:
  - ``path``         : dotted BikeConfig path (e.g. "tires.mu_peak")
  - ``low``, ``high``: absolute bounds for sampling
  - ``kind``         : "absolute" (use value directly) or
                       "relative" (multiply nominal value by sampled factor)
  - ``description``  : human-readable label

``DEFAULT_PARAM_BOUNDS`` covers the 10 most influential drag-racing
parameters based on physical intuition.  Users can extend or replace it.

Usage
-----
    from motoquant.analysis.sobol import compute_sobol_indices, DEFAULT_PARAM_BOUNDS
    from motoquant.defaults import gsxr1000_k5

    config  = gsxr1000_k5()
    result  = compute_sobol_indices(config, n_samples=256)
    result.print_table()
"""

from __future__ import annotations

import copy
import warnings
from dataclasses import dataclass

import numpy as np

from .. import engine_select
from ..models import BikeConfig

# ─────────────────────────────────────────────────────────────────
# Parameter specification
# ─────────────────────────────────────────────────────────────────


@dataclass
class SobolParamSpec:
    """Specification for one uncertain parameter in the sensitivity sweep."""

    path: str  # dotted BikeConfig path, e.g. "tires.mu_peak"
    low: float  # lower bound  (absolute value or relative factor)
    high: float  # upper bound  (absolute value or relative factor)
    kind: str = "absolute"  # "absolute" | "relative"
    description: str = ""  # label for tables/plots

    def __post_init__(self):
        if self.kind not in ("absolute", "relative"):
            raise ValueError(
                f"SobolParamSpec.kind must be 'absolute' or 'relative', got {self.kind!r}"
            )
        if self.low >= self.high:
            raise ValueError(
                f"SobolParamSpec: low ({self.low}) must be < high ({self.high}) for path {self.path!r}"
            )


# Ten parameters that physically dominate drag-strip ET variance.
# Bounds are deliberately wide to capture the full operating envelope
# of road-legal and light-prep motorcycles.
#
# Bike-geometry parameters (Cd, frontal area, rolling radius) are RELATIVE to
# the bike's own nominal value (October 2026): the old absolute windows
# (Cd 0.55-0.95, area 0.38-0.62 m², radius 0.28-0.33 m) excluded the nominal
# Cd of 36% of catalog bikes (catalog Cd spans 0.30-0.92), so for those bikes
# every sample used a Cd the bike never has and the indices described a
# different machine than base_et_s.
DEFAULT_PARAM_BOUNDS: dict[str, SobolParamSpec] = {
    "peak_power": SobolParamSpec(
        path="engine.peak_power_hp",
        low=0.80,
        high=1.20,
        kind="relative",
        description="Peak power (±20% of nominal)",
    ),
    "dry_mass": SobolParamSpec(
        path="chassis.dry_mass_kg",
        low=0.90,
        high=1.10,
        kind="relative",
        description="Dry mass (±10% of nominal)",
    ),
    "aero_cd": SobolParamSpec(
        path="aero.cd",
        low=0.85,
        high=1.15,
        kind="relative",
        description="Drag coefficient Cd (±15% of nominal)",
    ),
    "frontal_area": SobolParamSpec(
        path="aero.frontal_area_m2",
        low=0.85,
        high=1.15,
        kind="relative",
        description="Frontal area (±15% of nominal)",
    ),
    "tire_mu": SobolParamSpec(
        path="tires.mu_peak",
        low=0.85,
        high=1.45,
        kind="absolute",
        description="Peak tire friction (μ_peak)",
    ),
    "rolling_radius": SobolParamSpec(
        path="tires.rear_rolling_radius_m",
        low=0.95,
        high=1.05,
        kind="relative",
        description="Rear rolling radius (±5% of nominal)",
    ),
    "reaction_time": SobolParamSpec(
        path="staging.reaction_time_ms",
        low=0.0,
        high=500.0,
        kind="absolute",
        description="Reaction time (ms)",
    ),
    "redline_rpm": SobolParamSpec(
        path="engine.redline_rpm",
        low=0.90,
        high=1.05,
        kind="relative",
        description="Redline RPM (±5–10% of nominal)",
    ),
    "primary_ratio": SobolParamSpec(
        path="drivetrain.primary_ratio",
        low=0.90,
        high=1.10,
        kind="relative",
        description="Primary drive ratio (±10%)",
    ),
    "final_drive_ratio": SobolParamSpec(
        path="drivetrain.final_drive_ratio",
        low=0.90,
        high=1.10,
        kind="relative",
        description="Final drive ratio (±10%)",
    ),
}


# ─────────────────────────────────────────────────────────────────
# Result dataclass
# ─────────────────────────────────────────────────────────────────


@dataclass
class SobolResult:
    """
    Sobol global sensitivity analysis results.

    Arrays are parallel — index i corresponds to ``parameters[i]``.
    """

    parameters: list[str]  # parameter keys (from spec dict)
    descriptions: list[str]  # human-readable labels
    S1: np.ndarray  # first-order indices
    ST: np.ndarray  # total-order indices
    S1_conf: np.ndarray  # 95 % CI half-widths for S1
    ST_conf: np.ndarray  # 95 % CI half-widths for ST

    n_samples: int  # base sample size N
    n_simulations: int  # actual number of sim runs = N*(k+2)
    base_et_s: float  # ET of the nominal (unperturbed) config
    et_mean: float  # mean ET over the sample
    et_std: float  # std ET over the sample
    et_range: tuple[float, float]  # (min, max) observed ET

    def print_table(self, top_n: int | None = None) -> None:
        """Print a ranked sensitivity table to stdout."""
        order = np.argsort(self.ST)[::-1]
        if top_n is not None:
            order = order[:top_n]

        header = (
            f"\n{'Parameter':<36} {'S1':>7} {'±':>6} {'ST':>7} {'±':>6}  "
            f"{'Interact':>8}\n" + "─" * 78
        )
        print(header)
        for i in order:
            interact = self.ST[i] - self.S1[i]
            row = (
                f"{self.descriptions[i]:<36} "
                f"{self.S1[i]:>7.4f} {self.S1_conf[i]:>6.4f} "
                f"{self.ST[i]:>7.4f} {self.ST_conf[i]:>6.4f}  "
                f"{interact:>8.4f}"
            )
            print(row)
        print("─" * 78)
        print(
            f"Base ET: {self.base_et_s:.3f}s  "
            f"Sample ET: {self.et_mean:.3f}±{self.et_std:.3f}s  "
            f"Range: [{self.et_range[0]:.3f}, {self.et_range[1]:.3f}]s  "
            f"N={self.n_samples} ({self.n_simulations} sims)"
        )

    def to_dict(self) -> dict:
        """Serialisable dict for JSON/CLI output."""
        indices = []
        order = np.argsort(self.ST)[::-1]
        for i in order:
            indices.append(
                {
                    "parameter": self.parameters[i],
                    "description": self.descriptions[i],
                    "S1": round(float(self.S1[i]), 6),
                    "S1_conf": round(float(self.S1_conf[i]), 6),
                    "ST": round(float(self.ST[i]), 6),
                    "ST_conf": round(float(self.ST_conf[i]), 6),
                    "interaction": round(float(self.ST[i] - self.S1[i]), 6),
                }
            )
        return {
            "indices": indices,
            "n_samples": self.n_samples,
            "n_simulations": self.n_simulations,
            "base_et_s": round(self.base_et_s, 6),
            "et_mean": round(self.et_mean, 6),
            "et_std": round(self.et_std, 6),
            "et_min": round(self.et_range[0], 6),
            "et_max": round(self.et_range[1], 6),
        }


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────


def _get_nested(obj, path: str):
    for part in path.split("."):
        obj = getattr(obj, part)
    return obj


def _set_nested(obj, path: str, value) -> bool:
    """Set a nested attribute via dotted path. Returns False if path invalid."""
    parts = path.split(".")
    for p in parts[:-1]:
        if not hasattr(obj, p):
            return False
        obj = getattr(obj, p)
    if not hasattr(obj, parts[-1]):
        return False
    setattr(obj, parts[-1], value)
    return True


def _apply_sample_row(
    base_config: BikeConfig,
    specs: list[SobolParamSpec],
    nominal_values: list[float],
    row: np.ndarray,
) -> BikeConfig:
    """
    Apply one Saltelli sample row to a deep copy of base_config.

    Parameters
    ----------
    base_config     : original (unmodified) config
    specs           : ordered list of SobolParamSpec
    nominal_values  : nominal value for each spec (pre-read)
    row             : 1D array of sampled values, one per spec

    Notes
    -----
    When ``engine.peak_power_hp`` is perturbed *and* the config has a stored
    dyno curve, the dyno curve's torque array is scaled by the same ratio.
    Without this, the physics engine ignores the ``peak_power_hp`` field (it
    uses the dyno curve directly), making the power sensitivity appear as zero.
    """
    from ..models import DynoCurve  # lazy import to avoid circular dependency

    cfg = copy.deepcopy(base_config)
    nominal_hp = base_config.engine.peak_power_hp  # capture before any mutations

    for spec, nominal, sampled in zip(specs, nominal_values, row):
        if spec.kind == "relative":
            value = nominal * sampled
        else:
            value = sampled
        ok = _set_nested(cfg, spec.path, value)
        if not ok:
            warnings.warn(f"Sobol: invalid path '{spec.path}' in config — skipped")

    # Dyno curve scaling: if peak_power_hp was perturbed and the config has a
    # dyno curve, scale the torque array so the physics engine sees the change.
    new_hp = cfg.engine.peak_power_hp
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

    return cfg


def _run_et(config: BikeConfig) -> float:
    """Run a simulation and return quarter-mile ET in seconds."""
    try:
        engine = engine_select.make_engine(config)
        result = engine.run()
        return result.time_quarter
    except Exception as exc:
        warnings.warn(f"Sobol: simulation failed — {exc}")
        return float("nan")


# ─────────────────────────────────────────────────────────────────
# Primary public function
# ─────────────────────────────────────────────────────────────────


def compute_sobol_indices(
    config: BikeConfig,
    param_specs: dict[str, SobolParamSpec] | None = None,
    n_samples: int = 256,
    calc_second_order: bool = False,
    seed: int = 42,
    verbose: bool = False,
) -> SobolResult:
    """
    Compute first-order and total-order Sobol sensitivity indices.

    The total number of simulator calls is ``N × (k + 2)`` where N is
    ``n_samples`` and k is the number of parameters.  For the 10-parameter
    default set and N=256, this is 256 × 12 = 3 072 simulations.

    Each simulation runs in ~250–350 ms (fixed-step RK4 at 1 ms timestep),
    so the full sweep for N=256, k=10 takes roughly 13 minutes on a laptop.
    For interactive exploration, use N=32–64 with a 2–3 param subset first.

    Parameters
    ----------
    config
        Nominal BikeConfig (defines the centre of the parameter space).
    param_specs
        Dict mapping arbitrary string keys to ``SobolParamSpec`` objects.
        If None, ``DEFAULT_PARAM_BOUNDS`` is used.
    n_samples
        Base sample count N (must be a power of 2 for SALib's Saltelli
        sampler; 64, 128, 256, 512 are good choices).
        Total sim runs = N × (k+2).
    calc_second_order
        If True, also compute second-order (interaction) indices.
        Doubles the number of simulations.  Usually not needed.
    seed
        Random seed for reproducibility.
    verbose
        If True, prints progress to stdout.

    Returns
    -------
    SobolResult with ranked S1 / ST arrays and meta-statistics.
    """
    try:
        # Prefer the modern SALib.sample.sobol API (SALib ≥ 1.4.7).
        # Fall back to the legacy saltelli module if not present.
        try:
            from SALib.sample.sobol import sample as saltelli_sample
        except ImportError:
            from SALib.sample.saltelli import sample as saltelli_sample  # type: ignore
        from SALib.analyze import sobol as sobol_analyze
    except ImportError as exc:
        raise ImportError(
            "SALib is required for Sobol analysis: "
            "pip install SALib --break-system-packages"
        ) from exc

    if param_specs is None:
        param_specs = DEFAULT_PARAM_BOUNDS

    keys = list(param_specs.keys())
    specs = [param_specs[k] for k in keys]
    k = len(specs)

    # If any spec perturbs drivetrain.final_drive_ratio, normalise the config's
    # gearing onto that field. final_ratio prefers sprocket teeth over
    # final_drive_ratio for chain bikes, so without this the sampled ratio is
    # written but never read (the sensitivity would falsely read ~0). Setting
    # final_drive_ratio to the current *effective* ratio keeps the nominal
    # (all-centre) run bit-identical while making the knob live. Work on a copy
    # so the caller's config is untouched.
    if any(s.path == "drivetrain.final_drive_ratio" for s in specs):
        config = copy.deepcopy(config)
        config.drivetrain.set_effective_final_drive(config.drivetrain.final_ratio)

    # Read nominal values once (for relative-kind params)
    nominal_values: list[float] = []
    for spec in specs:
        try:
            nominal_values.append(float(_get_nested(config, spec.path)))
        except AttributeError:
            raise ValueError(
                f"Sobol: param path '{spec.path}' does not exist in BikeConfig"
            )

    # Build SALib problem dict
    problem = {
        "num_vars": k,
        "names": keys,
        "bounds": [[s.low, s.high] for s in specs],
    }

    # Generate Sobol quasi-random sample matrix: shape (N*(k+2), k)
    X = saltelli_sample(
        problem,
        n_samples,
        calc_second_order=calc_second_order,
        seed=seed,
    )
    n_runs = X.shape[0]

    if verbose:
        print(f"Sobol: {k} parameters, N={n_samples}, total simulations={n_runs}")

    # Evaluate the model (simulation) at each sample point
    Y = np.empty(n_runs)
    for i, row in enumerate(X):
        if verbose and i % max(1, n_runs // 10) == 0:
            pct = 100 * i / n_runs
            print(f"  {pct:5.1f}%  ({i}/{n_runs} runs)...")
        cfg = _apply_sample_row(config, specs, nominal_values, row)
        Y[i] = _run_et(cfg)

    # Replace NaN runs (sim failures) with mean to avoid polluting indices
    valid = ~np.isnan(Y)
    if not valid.all():
        n_failed = int((~valid).sum())
        warnings.warn(
            f"Sobol: {n_failed}/{n_runs} simulations produced NaN — "
            "replacing with sample mean.  Results may be less accurate."
        )
        Y[~valid] = Y[valid].mean()

    if verbose:
        print("  100.0%  done — computing Sobol indices...")

    # Analyse
    Si = sobol_analyze.analyze(
        problem,
        Y,
        calc_second_order=calc_second_order,
        print_to_console=False,
        seed=seed,  # SALib ≥ 1.4 accepts seed in analyze
    )

    # Run nominal config for base ET
    base_et = _run_et(config)

    descriptions = [s.description or s.path for s in specs]

    return SobolResult(
        parameters=keys,
        descriptions=descriptions,
        S1=np.array(Si["S1"]),
        ST=np.array(Si["ST"]),
        S1_conf=np.array(Si["S1_conf"]),
        ST_conf=np.array(Si["ST_conf"]),
        n_samples=n_samples,
        n_simulations=n_runs,
        base_et_s=base_et,
        et_mean=float(Y[valid].mean()),
        et_std=float(Y[valid].std()),
        et_range=(float(Y[valid].min()), float(Y[valid].max())),
    )


def compute_sobol_subset(
    config: BikeConfig,
    param_keys: list[str],
    n_samples: int = 256,
    seed: int = 42,
    verbose: bool = False,
) -> SobolResult:
    """
    Convenience wrapper: compute Sobol indices for a named subset of
    ``DEFAULT_PARAM_BOUNDS``.

    Parameters
    ----------
    param_keys
        List of keys from ``DEFAULT_PARAM_BOUNDS`` to include,
        e.g. ``["peak_power", "dry_mass", "tire_mu"]``.
    """
    unknown = [k for k in param_keys if k not in DEFAULT_PARAM_BOUNDS]
    if unknown:
        raise ValueError(
            f"Unknown param keys: {unknown}. Valid keys: {list(DEFAULT_PARAM_BOUNDS)}"
        )
    specs = {k: DEFAULT_PARAM_BOUNDS[k] for k in param_keys}
    return compute_sobol_indices(
        config,
        param_specs=specs,
        n_samples=n_samples,
        seed=seed,
        verbose=verbose,
    )
