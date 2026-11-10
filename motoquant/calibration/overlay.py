"""
MotoQuant — Sim vs Real Overlay
===============================
Compare a simulation run (SimResult) against a real GPS run (DragRunData).
Produces residuals, RMSE, and a rich comparison report.

This is the core feedback loop for Phase 3 calibration:
  1. Import real run with parse_dragy_file()
  2. Simulate with MotoQuantEngine.run()
  3. Call compare_runs() to get a RunComparison
  4. Inspect residuals to guide calibrator.py parameter fitting

Design
------
The real data is 10 Hz GPS; the simulation is 1 ms (1000 Hz).
compare_runs() resamples the simulation v(t) down to the real data's time axis
using linear interpolation — cheaper and more honest than upsampling GPS.

All arrays in the RunComparison are on the *real data's time axis* unless
suffixed with _sim or _real.
"""

from dataclasses import dataclass, field

import numpy as np

from ..physics import SimResult
from .dragy import DragRunData

# ─── Error ────────────────────────────────────────────────────────────────


class OverlayError(Exception):
    """Raised when comparison cannot be performed."""


# ─── Data model ───────────────────────────────────────────────────────────


@dataclass
class RunComparison:
    """
    Scalar and time-series comparison between one simulation and one real run.

    Signed convention: positive error = sim is LARGER (slower/faster) than real.
    """

    # ── Inputs ─────────────────────────────────────────────────────────────
    real: DragRunData
    sim_et: float  # sim quarter-mile ET [s]
    sim_trap_ms: float  # sim trap speed [m/s]

    # ── Scalar errors ──────────────────────────────────────────────────────
    et_error_s: float  # sim_ET − real_ET [s]  (+→sim slower)
    et_error_pct: float  # relative to real_ET [%]
    trap_error_ms: float  # sim_trap − real_trap [m/s]  (+→sim faster)
    trap_error_pct: float  # relative to real_trap [%]

    # ── v(t) comparison on the real data's time axis ───────────────────────
    t_common: np.ndarray  # shared time axis (real timestamps)
    v_real: np.ndarray  # real velocity [m/s]
    v_sim: np.ndarray  # sim velocity interpolated to t_common [m/s]
    residuals_ms: np.ndarray  # v_sim − v_real [m/s]

    # ── Aggregate statistics ───────────────────────────────────────────────
    rmse_ms: float  # RMSE of v(t) residuals [m/s]
    mae_ms: float  # Mean Absolute Error [m/s]
    max_residual_ms: float  # Worst-case point error [m/s] (abs)
    t_max_residual: float  # Time of worst-case error [s]

    # ── Split-by-split comparison ──────────────────────────────────────────
    split_errors: dict[str, float] = field(default_factory=dict)
    # {'60ft': +0.05, '330ft': -0.02, ...} — sim_split − real_split [s]

    @property
    def sim_trap_kmh(self) -> float:
        return self.sim_trap_ms * 3.6

    @property
    def real_trap_kmh(self) -> float:
        return self.real.trap_speed_kmh

    def print_report(self) -> None:
        """Human-readable comparison report."""
        print("\n  ─── Sim vs Real Comparison ───────────────────────────────")
        print(f"  Source file  : {self.real.source_file}")
        print("\n  ET (1/4 mile)")
        print(f"    Real       : {self.real.et_quarter:.4f} s")
        print(f"    Sim        : {self.sim_et:.4f} s")
        print(f"    Error      : {self.et_error_s:+.4f} s  ({self.et_error_pct:+.2f}%)")
        print("\n  Trap Speed")
        print(f"    Real       : {self.real.trap_speed_kmh:.1f} km/h")
        print(f"    Sim        : {self.sim_trap_kmh:.1f} km/h")
        print(
            f"    Error      : {self.trap_error_ms:+.2f} m/s  ({self.trap_error_pct:+.2f}%)"
        )
        print(f"\n  v(t) RMSE    : {self.rmse_ms:.3f} m/s")
        print(f"  v(t) MAE     : {self.mae_ms:.3f} m/s")
        print(
            f"  Max residual : {self.max_residual_ms:.3f} m/s at t={self.t_max_residual:.2f} s"
        )
        if self.split_errors:
            print("\n  Split errors (sim − real):")
            for name, err in self.split_errors.items():
                print(f"    {name:>6} : {err:+.4f} s")
        print()

    def to_dict(self) -> dict:
        return {
            "et_real_s": round(self.real.et_quarter, 4),
            "et_sim_s": round(self.sim_et, 4),
            "et_error_s": round(self.et_error_s, 4),
            "et_error_pct": round(self.et_error_pct, 3),
            "trap_real_kmh": round(self.real.trap_speed_kmh, 2),
            "trap_sim_kmh": round(self.sim_trap_kmh, 2),
            "trap_error_ms": round(self.trap_error_ms, 3),
            "trap_error_pct": round(self.trap_error_pct, 3),
            "rmse_ms": round(self.rmse_ms, 4),
            "mae_ms": round(self.mae_ms, 4),
            "max_residual_ms": round(self.max_residual_ms, 4),
            "t_max_residual": round(self.t_max_residual, 3),
            "split_errors": {k: round(v, 4) for k, v in self.split_errors.items()},
        }


# ─── Core comparison ──────────────────────────────────────────────────────


def compare_runs(
    real: DragRunData,
    sim: SimResult,
) -> RunComparison:
    """
    Compare a simulation result against a real GPS drag run.

    The sim v(t) is interpolated DOWN to the real data's (coarser) time axis.
    Both runs must start at t=0 (launch). The real run is assumed to have been
    trimmed by parse_dragy_file() so timestamps[0] == 0.

    Parameters
    ----------
    real : DragRunData  — from parse_dragy_file()
    sim  : SimResult    — from MotoQuantEngine.run()

    Returns
    -------
    RunComparison with all scalar and time-series metrics populated.

    Raises
    ------
    OverlayError  if the data is too short or incompatible.
    """
    if len(real.timestamps) < 3:
        raise OverlayError("Real run has fewer than 3 samples.")
    if len(sim.t) < 3:
        raise OverlayError("Sim result has fewer than 3 timesteps.")

    # ── Scalar ET and trap speed ───────────────────────────────────────────
    sim_et = float(sim.time_quarter)
    sim_trap = float(sim.speed_quarter)  # already in m/s

    et_error_s = sim_et - real.et_quarter
    et_error_pct = 100.0 * et_error_s / real.et_quarter if real.et_quarter > 0 else 0.0

    trap_error_ms = sim_trap - real.trap_speed_ms
    trap_error_pct = (
        100.0 * trap_error_ms / real.trap_speed_ms if real.trap_speed_ms > 0 else 0.0
    )

    # ── v(t) overlay ──────────────────────────────────────────────────────
    # Use real timestamps as the common axis — clamp to the shorter of the two runs
    t_end = min(float(real.timestamps[-1]), float(sim.t[-1]))
    mask = real.timestamps <= t_end
    t_common = real.timestamps[mask]
    v_real = real.velocity_ms[mask]

    # Interpolate sim v onto the real time axis
    v_sim = np.interp(t_common, sim.t, sim.v, left=0.0, right=float(sim.v[-1]))

    # Residuals (signed: sim − real)
    residuals = v_sim - v_real

    rmse = float(np.sqrt(np.mean(residuals**2)))
    mae = float(np.mean(np.abs(residuals)))
    abs_res = np.abs(residuals)
    max_res_idx = int(np.argmax(abs_res))
    max_res = float(abs_res[max_res_idx])
    t_max_res = float(t_common[max_res_idx])

    # ── Split-by-split errors ─────────────────────────────────────────────
    real_splits = real.splits()
    sim_splits = _sim_splits(sim)
    split_errors = {}
    for name in real_splits:
        if name in sim_splits:
            split_errors[name] = round(sim_splits[name] - real_splits[name], 4)

    return RunComparison(
        real=real,
        sim_et=sim_et,
        sim_trap_ms=sim_trap,
        et_error_s=et_error_s,
        et_error_pct=et_error_pct,
        trap_error_ms=trap_error_ms,
        trap_error_pct=trap_error_pct,
        t_common=t_common,
        v_real=v_real,
        v_sim=v_sim,
        residuals_ms=residuals,
        rmse_ms=rmse,
        mae_ms=mae,
        max_residual_ms=max_res,
        t_max_residual=t_max_res,
        split_errors=split_errors,
    )


# ─── Cost function ────────────────────────────────────────────────────────


def compute_cost(comparison: RunComparison, weights: dict | None = None) -> float:
    """
    Scalar cost combining ET error, trap speed error, and v(t) RMSE.

    Default weights: ET 50%, trap 30%, RMSE 20%.
    Used by calibrator.py as the objective to minimise.

    Parameters
    ----------
    comparison : RunComparison from compare_runs()
    weights    : dict with keys 'et', 'trap', 'rmse' (must sum to 1.0, or are normalised)

    Returns
    -------
    float : non-negative cost (0 = perfect match)
    """
    w = {"et": 0.50, "trap": 0.30, "rmse": 0.20}
    if weights:
        w.update(weights)

    # Normalise weights to sum to 1
    total = sum(w.values())
    if total > 0:
        w = {k: v / total for k, v in w.items()}

    # Each term is squared normalised error
    et_term = (comparison.et_error_s / max(comparison.real.et_quarter, 0.1)) ** 2
    trap_term = (
        comparison.trap_error_ms / max(comparison.real.trap_speed_ms, 1.0)
    ) ** 2
    # RMSE normalised by peak speed
    rmse_norm = comparison.rmse_ms / max(comparison.real.peak_speed_ms, 10.0)
    rmse_term = rmse_norm**2

    return float(w["et"] * et_term + w["trap"] * trap_term + w["rmse"] * rmse_term)


# ─── Helpers ──────────────────────────────────────────────────────────────


def _sim_splits(sim: SimResult) -> dict[str, float]:
    """Extract standard splits from a SimResult."""
    return {
        "60ft": sim.time_60ft,
        "330ft": sim.time_330ft,
        "660ft": sim.time_eighth,
        "1000ft": sim.time_1000ft,
        "1320ft": sim.time_quarter,
    }


def print_multi_run_stats(comparisons: list[RunComparison]) -> None:
    """Print aggregate statistics across multiple runs (e.g. 3-run average)."""
    if not comparisons:
        print("  No comparisons to summarise.")
        return
    stats = compute_multi_run_stats(comparisons)
    stats.print_report()


# ─── Multi-run statistical model ──────────────────────────────────────────


@dataclass
class MultiRunStats:
    """
    Statistical summary across N drag runs compared against simulation.

    Use `compute_multi_run_stats(comparisons)` to build this.

    Signed convention: positive error = sim is LARGER than real.

    Attributes
    ----------
    n_runs              : number of real runs in the sample
    et_real_mean        : mean real ET across runs [s]
    et_real_std         : standard deviation of real ET [s]
    et_real_best        : best (lowest) real ET [s]
    et_real_worst       : worst (highest) real ET [s]
    et_real_ci_95       : (lo, hi) 95% confidence interval on mean real ET
    et_error_mean       : mean sim−real ET error [s]
    et_error_std        : std of ET error across runs [s]
    trap_real_mean_kmh  : mean real trap speed [km/h]
    trap_real_std_kmh   : std of real trap speed [km/h]
    trap_error_mean_ms  : mean sim−real trap speed error [m/s]
    trap_error_std_ms   : std of trap speed error [m/s]
    rmse_mean           : mean v(t) RMSE across runs [m/s]
    rmse_std            : std of v(t) RMSE [m/s]
    run_consistency     : 0–1 score (1=perfectly consistent ETs, 0=high scatter)
    recommended_n_runs  : runs needed to achieve ±0.02 s CI on mean ET
    """

    n_runs: int
    et_real_mean: float
    et_real_std: float
    et_real_best: float
    et_real_worst: float
    et_real_ci_95: tuple  # (lo, hi) 95% CI on mean real ET
    et_error_mean: float
    et_error_std: float
    trap_real_mean_kmh: float
    trap_real_std_kmh: float
    trap_error_mean_ms: float
    trap_error_std_ms: float
    rmse_mean: float
    rmse_std: float
    run_consistency: float  # 0–1
    recommended_n_runs: int

    def print_report(self) -> None:
        """Human-readable multi-run statistical report."""
        ci_lo, ci_hi = self.et_real_ci_95
        print(
            f"\n  ─── Multi-Run Statistics ({self.n_runs} runs) ──────────────────────"
        )
        print("\n  Real ET")
        print(f"    Mean         : {self.et_real_mean:.4f} s")
        print(f"    Std dev      : {self.et_real_std:.4f} s")
        print(
            f"    Best / Worst : {self.et_real_best:.4f} s  /  {self.et_real_worst:.4f} s"
        )
        print(f"    95% CI       : [{ci_lo:.4f}, {ci_hi:.4f}] s")
        print("\n  Sim error (sim − real)")
        print(
            f"    ET error     : {self.et_error_mean:+.4f} s  ±{self.et_error_std:.4f} s"
        )
        print(
            f"    Trap error   : {self.trap_error_mean_ms:+.3f} m/s  ±{self.trap_error_std_ms:.3f} m/s"
        )
        print(f"    v(t) RMSE    : {self.rmse_mean:.4f} m/s  ±{self.rmse_std:.4f} m/s")
        print("\n  Real trap speed")
        print(
            f"    Mean         : {self.trap_real_mean_kmh:.1f} km/h  ±{self.trap_real_std_kmh:.1f} km/h"
        )
        print(
            f"\n  Run consistency  : {self.run_consistency:.3f}  "
            f"({'excellent' if self.run_consistency > 0.95 else 'good' if self.run_consistency > 0.85 else 'fair' if self.run_consistency > 0.70 else 'poor'})"
        )
        print(
            f"  Recommended runs : {self.recommended_n_runs}  "
            f"(for ±0.02 s CI on mean ET)"
        )
        print()

    def to_dict(self) -> dict:
        ci_lo, ci_hi = self.et_real_ci_95
        return {
            "n_runs": self.n_runs,
            "et_real_mean_s": round(self.et_real_mean, 4),
            "et_real_std_s": round(self.et_real_std, 4),
            "et_real_best_s": round(self.et_real_best, 4),
            "et_real_worst_s": round(self.et_real_worst, 4),
            "et_real_ci_95": [round(ci_lo, 4), round(ci_hi, 4)],
            "et_error_mean_s": round(self.et_error_mean, 4),
            "et_error_std_s": round(self.et_error_std, 4),
            "trap_real_mean_kmh": round(self.trap_real_mean_kmh, 2),
            "trap_real_std_kmh": round(self.trap_real_std_kmh, 2),
            "trap_error_mean_ms": round(self.trap_error_mean_ms, 3),
            "trap_error_std_ms": round(self.trap_error_std_ms, 3),
            "rmse_mean_ms": round(self.rmse_mean, 4),
            "rmse_std_ms": round(self.rmse_std, 4),
            "run_consistency": round(self.run_consistency, 4),
            "recommended_n_runs": self.recommended_n_runs,
        }


def compute_multi_run_stats(comparisons: list[RunComparison]) -> MultiRunStats:
    """
    Compute statistical summary across N sim-vs-real comparisons.

    Gives ET mean/std/CI, trap speed stats, v(t) RMSE, run consistency
    score, and recommended number of runs for stable calibration.

    Parameters
    ----------
    comparisons : list of RunComparison from compare_runs()
                  Must have at least 1 entry.

    Returns
    -------
    MultiRunStats

    Raises
    ------
    ValueError  if comparisons is empty.
    """
    if not comparisons:
        raise ValueError("comparisons list is empty — nothing to summarise.")

    n = len(comparisons)

    # Real ET statistics
    real_ets = np.array([c.real.et_quarter for c in comparisons])
    et_errors = np.array([c.et_error_s for c in comparisons])

    # Real trap speed statistics (km/h)
    real_traps_kmh = np.array([c.real.trap_speed_kmh for c in comparisons])
    trap_errors = np.array([c.trap_error_ms for c in comparisons])

    # v(t) RMSE statistics
    rmses = np.array([c.rmse_ms for c in comparisons])

    # 95% confidence interval on mean real ET using t-distribution
    # For n >= 30 use z=1.96; for small n use t-critical (approximate)
    _T_CRIT = {
        1: 12.706,
        2: 4.303,
        3: 3.182,
        4: 2.776,
        5: 2.571,
        6: 2.447,
        7: 2.365,
        8: 2.306,
        9: 2.262,
        10: 2.228,
    }
    if n == 1:
        t_crit = 12.706
    elif n <= 10:
        t_crit = _T_CRIT[n - 1]
    elif n <= 30:
        t_crit = 2.093  # df=19 approx
    else:
        t_crit = 1.96  # z-score for large n

    sem = float(real_ets.std(ddof=1) / np.sqrt(n)) if n > 1 else float(real_ets.std())
    ci_lo = float(real_ets.mean()) - t_crit * sem
    ci_hi = float(real_ets.mean()) + t_crit * sem

    # Run consistency score: 1 − coefficient_of_variation (clamped 0–1)
    # CV = std / mean; a CV of 0.5% on a 10s ET = std 0.05s
    cv = float(real_ets.std(ddof=0) / real_ets.mean()) if real_ets.mean() > 0 else 1.0
    consistency = float(np.clip(1.0 - cv * 20.0, 0.0, 1.0))
    # Scale: CV=0 → 1.0, CV=0.05 (5%) → 0.0

    # Recommended number of runs to achieve ±0.02 s CI
    # From: n = (t_crit * std / margin)^2, iterating t_crit
    target_margin = 0.02
    std_est = float(real_ets.std(ddof=1)) if n > 1 else float(real_ets.std() + 0.05)
    if std_est < 0.001:
        rec_n = 3
    else:
        # Approximate with z=1.96 first, then refine
        rec_n = max(3, int(np.ceil((1.96 * std_est / target_margin) ** 2)))
        rec_n = min(rec_n, 15)  # cap at 15; beyond that you have bigger problems

    return MultiRunStats(
        n_runs=n,
        et_real_mean=float(real_ets.mean()),
        et_real_std=float(real_ets.std(ddof=1)) if n > 1 else 0.0,
        et_real_best=float(real_ets.min()),
        et_real_worst=float(real_ets.max()),
        et_real_ci_95=(ci_lo, ci_hi),
        et_error_mean=float(et_errors.mean()),
        et_error_std=float(et_errors.std(ddof=1)) if n > 1 else 0.0,
        trap_real_mean_kmh=float(real_traps_kmh.mean()),
        trap_real_std_kmh=float(real_traps_kmh.std(ddof=1)) if n > 1 else 0.0,
        trap_error_mean_ms=float(trap_errors.mean()),
        trap_error_std_ms=float(trap_errors.std(ddof=1)) if n > 1 else 0.0,
        rmse_mean=float(rmses.mean()),
        rmse_std=float(rmses.std(ddof=1)) if n > 1 else 0.0,
        run_consistency=consistency,
        recommended_n_runs=rec_n,
    )
