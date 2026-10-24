"""
MotoQuant — Auto-Calibration Loop
=================================
Fit physics parameters (aero.cd, tires.mu_peak, and optionally others)
from real GPS run data (DragRunData) by minimising the overlay cost function.

Algorithm
---------
Uses scipy.optimize.differential_evolution (global, derivative-free) for the
first coarse pass, followed by scipy.optimize.minimize(method='Nelder-Mead')
for local refinement.  Both stages honour each spec's declared ``bounds``
(the refinement is bounded Nelder-Mead; a start point outside the bounds is
clipped onto them). Total wall time is ~5–30 s depending on parameter count
and the simulation's RK4 integration cost. Simulations run on the engine
``motoquant.engine_select`` picks (the Rust core when available).

Typical use
-----------
    from motoquant.calibration.calibrator import calibrate, CalibrationResult
    from motoquant.calibration.dragy import parse_dragy_file, best_run

    real_run = best_run(parse_dragy_file("myrun.csv"))
    result   = calibrate(config, real_run)

    print(result)
    optimised_config = result.apply(config)     # returns modified BikeConfig copy
    new_sim = engine_select.make_engine(optimised_config).run()

Parameter specification
-----------------------
params_to_fit is a list of param specs. Each spec is a dict:
    {
        "path": "aero.cd",          # dotted path into BikeConfig sub-dataclass
        "bounds": (0.45, 0.95),     # search bounds
        "initial": 0.70,            # starting guess (used if known)
    }

Predefined presets are available:
    PRESET_AERO_TIRE  : fit cd + mu_peak  (default, recommended)
    PRESET_AERO_ONLY  : fit cd only       (when tire data is trusted)
    PRESET_TIRE_ONLY  : fit mu_peak only  (when aero is well characterised)
    PRESET_FULL       : cd + mu_peak + drivetrain.chain_efficiency

Every ``path`` must name a real numeric dataclass field (validated before
any simulation runs); an unknown path raises CalibrationError instead of
being written as a phantom attribute nothing reads.
"""

import copy
import dataclasses
import logging
import math
import time
from dataclasses import dataclass, field

import numpy as np

try:
    from scipy.optimize import differential_evolution, minimize

    _SCIPY_AVAILABLE = True
except ImportError:
    _SCIPY_AVAILABLE = False

from .. import engine_select
from ..models import BikeConfig
from .dragy import DragRunData
from .overlay import RunComparison, compare_runs, compute_cost

log = logging.getLogger(__name__)

# ─── Error ────────────────────────────────────────────────────────────────


class CalibrationError(Exception):
    """Raised when calibration cannot be completed."""


# ─── Parameter presets ────────────────────────────────────────────────────

PRESET_AERO_TIRE: list[dict] = [
    {"path": "aero.cd", "bounds": (0.45, 0.95), "initial": None},
    {"path": "tires.mu_peak", "bounds": (1.0, 1.8), "initial": None},
]

PRESET_AERO_ONLY: list[dict] = [
    {"path": "aero.cd", "bounds": (0.45, 0.95), "initial": None},
]

PRESET_TIRE_ONLY: list[dict] = [
    {"path": "tires.mu_peak", "bounds": (1.0, 1.8), "initial": None},
]

# drivetrain.chain_efficiency: DrivetrainParams has no 'efficiency' field
# (overall efficiency is the drivetrain_efficiency() product of the primary /
# per-mesh / chain terms), so the old 'drivetrain.efficiency' path crashed
# every PRESET_FULL run with AttributeError. Note the chain term is only
# weakly live on bikes whose dyno curve is measured AT THE WHEEL (the K5
# reference among them) — see the core audit's at-wheel-efficiency finding.
PRESET_FULL: list[dict] = [
    {"path": "aero.cd", "bounds": (0.45, 0.95), "initial": None},
    {"path": "tires.mu_peak", "bounds": (1.0, 1.8), "initial": None},
    {"path": "drivetrain.chain_efficiency", "bounds": (0.90, 0.99), "initial": None},
]


# ─── Result container ─────────────────────────────────────────────────────


@dataclass
class CalibrationResult:
    """
    Result of one calibration run.

    fitted_params  : dict mapping param path → fitted value
    initial_params : dict mapping param path → value before fitting
    final_cost     : cost at the fitted parameters
    initial_cost   : cost before fitting
    comparison     : RunComparison at the fitted parameters
    converged      : True if the optimiser reported success
    iterations     : total function evaluations
    wall_time_s    : seconds elapsed
    """

    fitted_params: dict[str, float]
    initial_params: dict[str, float]
    final_cost: float
    initial_cost: float
    comparison: RunComparison
    converged: bool
    iterations: int
    wall_time_s: float
    source_file: str = ""
    cost_weights: dict = field(default_factory=dict)

    def __str__(self) -> str:
        lines = [
            "\n  ─── Calibration Result ───────────────────────────────────",
            f"  Source file  : {self.source_file}",
            f"  Converged    : {'YES ✓' if self.converged else 'NO (partial)'}",
            f"  Evaluations  : {self.iterations}",
            f"  Wall time    : {self.wall_time_s:.1f} s",
            "\n  Parameter    Initial → Fitted",
        ]
        for path in self.fitted_params:
            init = self.initial_params.get(path, "?")
            fit = self.fitted_params[path]
            lines.append(f"    {path:<36} {init!r:>8} → {fit:.6f}")
        lines += [
            f"\n  Cost  : {self.initial_cost:.6f} → {self.final_cost:.6f}  "
            f"({'improved' if self.final_cost < self.initial_cost else 'not improved'})",
        ]
        return "\n".join(lines)

    def apply(self, config: BikeConfig) -> BikeConfig:
        """Return a deep-copy of config with fitted parameters applied."""
        cfg = copy.deepcopy(config)
        for path, value in self.fitted_params.items():
            _set_param(cfg, path, value)
        return cfg

    def to_dict(self) -> dict:
        return {
            "fitted_params": {k: round(v, 6) for k, v in self.fitted_params.items()},
            "initial_params": {
                k: round(float(v), 6) for k, v in self.initial_params.items()
            },
            "final_cost": round(self.final_cost, 8),
            "initial_cost": round(self.initial_cost, 8),
            "converged": self.converged,
            "iterations": self.iterations,
            "wall_time_s": round(self.wall_time_s, 2),
            "et_error_after_s": round(self.comparison.et_error_s, 4),
            "trap_error_after_ms": round(self.comparison.trap_error_ms, 3),
            "rmse_after_ms": round(self.comparison.rmse_ms, 4),
        }


# ─── Parameter injection helpers ──────────────────────────────────────────


def _resolve_param(config: BikeConfig, path: str) -> tuple[object, str]:
    """(owner object, field name) for a dotted path, validating every segment.

    Each segment must be a declared dataclass field of the object it is
    looked up on. A bare setattr() used to accept ANY path: a typo (or
    PRESET_FULL's old 'drivetrain.efficiency') was written as a phantom
    attribute the physics never reads, so the fit "succeeded" on a dead knob.
    """
    parts = path.split(".") if isinstance(path, str) else []
    if len(parts) < 2 or not all(parts):
        raise CalibrationError(
            f"parameter path {path!r} must be dotted, e.g. 'aero.cd'"
        )
    obj: object = config
    for i, part in enumerate(parts):
        if not dataclasses.is_dataclass(obj) or part not in {
            f.name for f in dataclasses.fields(obj)
        }:
            raise CalibrationError(
                f"unknown parameter path {path!r}: {type(obj).__name__} has no "
                f"field {part!r}"
            )
        if i < len(parts) - 1:
            obj = getattr(obj, part)
    return obj, parts[-1]


def _get_param(config: BikeConfig, path: str) -> float:
    """Get a value from BikeConfig via dotted path, e.g. 'aero.cd'."""
    obj, name = _resolve_param(config, path)
    value = getattr(obj, name)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CalibrationError(
            f"parameter {path!r} is not numeric (value {value!r}); only float "
            "fields can be calibrated"
        )
    return float(value)


def _set_param(config: BikeConfig, path: str, value: float) -> None:
    """Set a value in BikeConfig via dotted path, e.g. 'aero.cd' = 0.65."""
    obj, name = _resolve_param(config, path)
    setattr(obj, name, float(value))


def _prepare_specs(
    config: BikeConfig, params_to_fit: list[dict]
) -> tuple[np.ndarray, list[tuple[float, float]], dict[str, float]]:
    """Validate specs; return (x0 clipped into bounds, bounds, initial_params)."""
    x0: list[float] = []
    bounds: list[tuple[float, float]] = []
    initial_params: dict[str, float] = {}
    for spec in params_to_fit:
        path = spec["path"]
        current = _get_param(config, path)  # validates the path up front
        try:
            lo, hi = (float(b) for b in spec["bounds"])
        except (KeyError, TypeError, ValueError) as exc:
            raise CalibrationError(
                f"spec {path!r} needs bounds=(low, high): {exc}"
            ) from exc
        if not (math.isfinite(lo) and math.isfinite(hi) and lo < hi):
            raise CalibrationError(f"spec {path!r} has invalid bounds ({lo}, {hi})")
        init = spec.get("initial")
        start = current if init is None else float(init)
        if not lo <= start <= hi:
            clipped = min(max(start, lo), hi)
            log.info(
                "calibrate: start %s=%g is outside bounds (%g, %g); starting from %g",
                path,
                start,
                lo,
                hi,
                clipped,
            )
            start = clipped
        x0.append(start)
        bounds.append((lo, hi))
        initial_params[path] = current
    return np.array(x0), bounds, initial_params


def _clip_to_bounds(x: np.ndarray, bounds: list[tuple[float, float]]) -> np.ndarray:
    lo = np.array([b[0] for b in bounds])
    hi = np.array([b[1] for b in bounds])
    return np.clip(np.asarray(x, dtype=float), lo, hi)


# ─── Objective function ───────────────────────────────────────────────────


class _Objective:
    """
    Stateful objective: wraps BikeConfig + DragRunData into a callable
    f(x: np.ndarray) → float for scipy.optimize.
    """

    def __init__(
        self,
        config: BikeConfig,
        real_run: DragRunData,
        param_specs: list[dict],
        weights: dict | None = None,
    ):
        self._base_config = config
        self._real_run = real_run
        self._specs = param_specs
        self._weights = weights or {}
        self.n_evals = 0
        self.n_crashes = 0

    def __call__(self, x: np.ndarray) -> float:
        self.n_evals += 1
        cfg = copy.deepcopy(self._base_config)
        for i, spec in enumerate(self._specs):
            _set_param(cfg, spec["path"], float(x[i]))

        try:
            sim = engine_select.make_engine(cfg).run()
        except Exception as exc:
            self.n_crashes += 1
            if self.n_crashes == 1:
                log.warning(
                    "calibrate: simulation failed at %s (%s: %s); penalising "
                    "such points",
                    {s["path"]: float(v) for s, v in zip(self._specs, x)},
                    type(exc).__name__,
                    exc,
                )
            return 1e6  # penalise crashes

        if sim.time_quarter <= 0 or sim.speed_quarter <= 0:
            return 1e6

        cmp = compare_runs(self._real_run, sim)
        return compute_cost(cmp, self._weights)


# ─── Public API ───────────────────────────────────────────────────────────


def calibrate(
    config: BikeConfig,
    real_run: DragRunData,
    params_to_fit: list[dict] | None = None,
    cost_weights: dict | None = None,
    global_search: bool = True,
    de_popsize: int = 8,
    de_maxiter: int = 30,
    local_maxiter: int = 200,
    verbose: bool = False,
) -> CalibrationResult:
    """
    Fit physics parameters to minimise the overlay cost between sim and GPS run.

    Parameters
    ----------
    config         : BikeConfig — starting point (NOT modified in place).
    real_run       : DragRunData from parse_dragy_file().
    params_to_fit  : List of param specs (see PRESET_* constants).
                     Defaults to PRESET_AERO_TIRE.
    cost_weights   : Passed to compute_cost(). Default: {'et':0.5,'trap':0.3,'rmse':0.2}
    global_search  : If True, run differential evolution before Nelder-Mead refinement.
                     If False, Nelder-Mead only from current config values.
    de_popsize     : Population multiplier for differential_evolution.
    de_maxiter     : Max generations for differential_evolution.
    local_maxiter  : Max iterations for Nelder-Mead local refinement.
    verbose        : Print progress to stdout.

    Returns
    -------
    CalibrationResult

    Raises
    ------
    CalibrationError  if scipy is not installed or config/run is invalid.
    """
    if not _SCIPY_AVAILABLE:
        raise CalibrationError(
            "scipy is required for calibration. Install with: pip install scipy"
        )

    if params_to_fit is None:
        params_to_fit = PRESET_AERO_TIRE

    if not params_to_fit:
        raise CalibrationError("params_to_fit is empty — nothing to optimise.")

    # Collect initial values and bounds (validates every path first)
    x0, bounds, initial_params = _prepare_specs(config, params_to_fit)

    obj = _Objective(config, real_run, params_to_fit, cost_weights)

    # Compute initial cost
    initial_cost = obj(x0)
    if verbose:
        print(f"  Initial cost: {initial_cost:.6f}  (params: {initial_params})")

    t_start = time.time()

    # ── Phase 1: global search (differential evolution) ───────────────────
    if global_search and len(params_to_fit) > 0:
        if verbose:
            print(
                f"  Differential evolution: popsize={de_popsize}, maxiter={de_maxiter}"
            )
        de_result = differential_evolution(
            obj,
            bounds=bounds,
            seed=42,
            popsize=de_popsize,
            maxiter=de_maxiter,
            tol=1e-5,
            mutation=(0.5, 1.0),
            recombination=0.7,
            polish=False,
            workers=1,  # disable multiprocessing (not safe with dataclasses)
        )
        x_best = de_result.x
        if verbose:
            print(f"  DE done. Best cost: {de_result.fun:.6f}  evals: {obj.n_evals}")
    else:
        x_best = x0

    # ── Phase 2: local refinement (Nelder-Mead) ───────────────────────────
    if verbose:
        print("  Nelder-Mead refinement...")
    # Bounded Nelder-Mead (scipy >= 1.7): the refinement used to run
    # unbounded, so it walked straight out of the declared bounds (a K5 fit
    # returned cd 0.30 for bounds (0.45, 0.95)) and noisy GPS data could
    # yield negative/absurd values that apply() wrote into the config.
    nm_result = minimize(
        obj,
        _clip_to_bounds(x_best, bounds),
        method="Nelder-Mead",
        bounds=bounds,
        options={"maxiter": local_maxiter, "xatol": 1e-5, "fatol": 1e-7, "disp": False},
    )
    x_final = _clip_to_bounds(nm_result.x, bounds)
    final_cost = float(nm_result.fun)

    wall_time = time.time() - t_start

    # Assemble fitted params dict
    fitted_params = {
        spec["path"]: float(x_final[i]) for i, spec in enumerate(params_to_fit)
    }

    # Compute final comparison with fitted parameters
    cfg_fitted = copy.deepcopy(config)
    for path, value in fitted_params.items():
        _set_param(cfg_fitted, path, value)
    sim_fitted = engine_select.make_engine(cfg_fitted).run()
    final_comparison = compare_runs(real_run, sim_fitted)

    converged = nm_result.success or (final_cost < initial_cost)

    return CalibrationResult(
        fitted_params=fitted_params,
        initial_params=initial_params,
        final_cost=final_cost,
        initial_cost=initial_cost,
        comparison=final_comparison,
        converged=converged,
        iterations=obj.n_evals,
        wall_time_s=wall_time,
        source_file=real_run.source_file,
        cost_weights=cost_weights or {},
    )


def calibrate_multi_run(
    config: BikeConfig,
    runs: list[DragRunData],
    params_to_fit: list[dict] | None = None,
    cost_weights: dict | None = None,
    verbose: bool = False,
) -> CalibrationResult:
    """
    Calibrate against the average of multiple runs (reduces GPS noise impact).

    Builds a combined objective that averages cost across all runs.
    Faster than fitting each run separately.
    """
    if not _SCIPY_AVAILABLE:
        raise CalibrationError("scipy is required for calibration.")
    if not runs:
        raise CalibrationError("No runs provided for multi-run calibration.")

    if params_to_fit is None:
        params_to_fit = PRESET_AERO_TIRE

    if not params_to_fit:
        raise CalibrationError("params_to_fit is empty — nothing to optimise.")
    x0, bounds, initial_params = _prepare_specs(config, params_to_fit)

    objs = [_Objective(config, run, params_to_fit, cost_weights) for run in runs]
    n_evals = [0]

    def combined_obj(x: np.ndarray) -> float:
        n_evals[0] += 1
        costs = [o(x) for o in objs]
        return float(np.mean(costs))

    initial_cost = combined_obj(x0)
    t_start = time.time()

    de_result = differential_evolution(
        combined_obj, bounds=bounds, seed=42, popsize=8, maxiter=25, polish=False
    )
    nm_result = minimize(
        combined_obj,
        _clip_to_bounds(de_result.x, bounds),
        method="Nelder-Mead",
        bounds=bounds,
        options={"maxiter": 200, "xatol": 1e-5, "fatol": 1e-7},
    )

    x_final = _clip_to_bounds(nm_result.x, bounds)
    final_cost = float(nm_result.fun)
    fitted_params = {
        spec["path"]: float(x_final[i]) for i, spec in enumerate(params_to_fit)
    }

    # Compute final comparison against the best run (lowest ET)
    from .dragy import best_run

    best = best_run(runs)
    cfg_fitted = copy.deepcopy(config)
    for path, value in fitted_params.items():
        _set_param(cfg_fitted, path, value)
    sim_fitted = engine_select.make_engine(cfg_fitted).run()
    final_comparison = compare_runs(best, sim_fitted)

    return CalibrationResult(
        fitted_params=fitted_params,
        initial_params=initial_params,
        final_cost=final_cost,
        initial_cost=initial_cost,
        comparison=final_comparison,
        converged=nm_result.success or (final_cost < initial_cost),
        iterations=n_evals[0],
        wall_time_s=time.time() - t_start,
        source_file=f"{len(runs)} runs from {runs[0].source_file}",
        cost_weights=cost_weights or {},
    )
