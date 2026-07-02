"""
MotoQuant Pro — Bayesian Optimization Engine for Build Tuning
==============================================================
Multi-variable budget-constrained motorcycle build optimization using BoTorch.

Unlike the knapsack DP in ``roi.py`` which picks discrete parts, the Bayesian
optimizer explores continuous parameter perturbations (power delta, mass delta,
aero delta, gearing adjustments, etc.) and uses a Gaussian Process surrogate
to guide the search towards ET-optimal configurations within a budget.

Core approach
-------------
1. Define a continuous parameter space from part effects (power_hp, mass_kg, etc.)
2. Use BoTorch's SingleTaskGP + Expected Improvement to select promising trials
3. Run the physics engine at each trial to get true ET (the oracle)
4. Respect budget constraint via a penalty term in the acquisition function
5. Return the best build found (predicted ET + estimated cost)

When to use Bayesian vs knapsack
---------------------------------
  **Knapsack (roi.py)**: Discrete parts, small catalogs (<100 parts), all parts
    must sum to a valid configuration. Fast, exact optimal solution.

  **Bayesian (this module)**: Continuous parameter space, explores interactions
    between parameters (e.g. power + gearing synergy), useful for fine-tuning
    an existing build or discovering non-obvious combinations. Slower, approximate.

Parameters tuned
----------------
  power_delta_hp        : peak engine power adjustment (±50 hp)
  mass_delta_kg         : dry chassis mass adjustment (±10 kg, lighter = faster)
  cd_delta              : aerodynamic drag coefficient change (±0.1)
  frontal_area_delta_m2 : frontal area adjustment (±0.05 m²)
  tire_mu_delta         : tire peak friction (μ_peak) adjustment (±0.25)
  rear_pressure_delta   : rear tire pressure adjustment (±2 psi)
  gearing_ratio_delta   : final drive ratio adjustment (±10%, mult factor 0.9–1.1)

Budget constraint
-----------------
Parts implied by the parameter perturbations are mapped back to the parts
catalog (e.g. power_delta=+20 hp → ECU flash + intake → estimated ₹15k).
A hard budget penalty is applied if total cost exceeds the limit.

Usage
-----
    from motoquant.analysis.bayesian_opt import optimize_build
    from motoquant.defaults import gsxr1000_k5

    config = gsxr1000_k5()
    result = optimize_build(
        base_config=config,
        budget_inr=100_000,
        n_iterations=50,
        verbose=True,
    )
    print(result.summary())
"""

from __future__ import annotations

import copy
import warnings
from dataclasses import dataclass

import numpy as np

from ..models import BikeConfig
from ..physics import MotoQuantEngine

# ─────────────────────────────────────────────────────────────────
# Result dataclass
# ─────────────────────────────────────────────────────────────────


@dataclass
class OptimizationResult:
    """Outcome of Bayesian build optimization."""

    base_et_s: float  # Stock quarter-mile time
    best_et_s: float  # Best ET found by optimizer
    et_improvement_s: float  # base - best (positive = faster)

    estimated_cost_inr: float  # Estimated cost of best config
    budget_inr: float  # Budget constraint
    remaining_budget_inr: float  # budget - cost

    # Best configuration params found
    best_power_delta_hp: float
    best_mass_delta_kg: float
    best_cd_delta: float
    best_frontal_area_delta_m2: float
    best_tire_mu_delta: float
    best_rear_pressure_delta: float
    best_gearing_ratio_delta: float

    # Optimization diagnostics
    n_iterations: int
    iterations_completed: int
    best_iteration: int  # iteration number where best was found

    def summary(self) -> str:
        """One-liner summary for CLI output."""
        lines = [
            f"Base ET:          {self.base_et_s:.3f}s",
            f"Best ET found:    {self.best_et_s:.3f}s  ({self.et_improvement_s:+.3f}s)",
            f"Estimated cost:   ₹{self.estimated_cost_inr:,.0f} / ₹{self.budget_inr:,.0f}",
            f"Remaining budget: ₹{self.remaining_budget_inr:,.0f}",
            "",
            "Optimal parameter deltas:",
            f"  Power:          {self.best_power_delta_hp:+.1f} hp",
            f"  Mass:           {self.best_mass_delta_kg:+.2f} kg",
            f"  Drag coeff:     {self.best_cd_delta:+.3f}",
            f"  Frontal area:   {self.best_frontal_area_delta_m2:+.4f} m²",
            f"  Tire grip (μ):  {self.best_tire_mu_delta:+.3f}",
            f"  Rear pressure:  {self.best_rear_pressure_delta:+.2f} psi",
            f"  Gearing ratio:  {self.best_gearing_ratio_delta:+.2%}",
            "",
            f"Optimization completed in {self.iterations_completed}/{self.n_iterations} iterations",
            f"(best found at iteration {self.best_iteration})",
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serialisable dict for JSON/CLI output."""
        return {
            "base_et_s": round(self.base_et_s, 4),
            "best_et_s": round(self.best_et_s, 4),
            "et_improvement_s": round(self.et_improvement_s, 4),
            "estimated_cost_inr": round(self.estimated_cost_inr, 0),
            "budget_inr": round(self.budget_inr, 0),
            "remaining_budget_inr": round(self.remaining_budget_inr, 0),
            "best_power_delta_hp": round(self.best_power_delta_hp, 2),
            "best_mass_delta_kg": round(self.best_mass_delta_kg, 2),
            "best_cd_delta": round(self.best_cd_delta, 4),
            "best_frontal_area_delta_m2": round(self.best_frontal_area_delta_m2, 4),
            "best_tire_mu_delta": round(self.best_tire_mu_delta, 3),
            "best_rear_pressure_delta": round(self.best_rear_pressure_delta, 2),
            "best_gearing_ratio_delta": round(self.best_gearing_ratio_delta, 4),
            "n_iterations": self.n_iterations,
            "iterations_completed": self.iterations_completed,
            "best_iteration": self.best_iteration,
        }


# ─────────────────────────────────────────────────────────────────
# Bayesian optimizer
# ─────────────────────────────────────────────────────────────────


class BayesianBuildOptimizer:
    """
    Bayesian optimization for motorcycle build tuning.

    Uses BoTorch's SingleTaskGP + Expected Improvement (EI) to find
    the best continuous parameter configuration within a budget.
    """

    # Parameter bounds (min, max) for each tunable dimension
    PARAM_BOUNDS = {
        "power_delta_hp": (-30.0, 50.0),
        "mass_delta_kg": (-15.0, 5.0),  # negative = weight reduction
        "cd_delta": (-0.10, 0.10),
        "frontal_area_delta_m2": (-0.05, 0.05),
        "tire_mu_delta": (-0.15, 0.30),  # tire compound/grip improvement
        "rear_pressure_delta": (-2.0, 3.0),  # psi (pressure fine-tuning)
        "gearing_ratio_delta": (-0.10, 0.10),  # multiplicative factor
    }

    # Approximate cost per unit change (INR)
    # Used to estimate total build cost and apply budget penalty
    COST_PER_UNIT = {
        "power_delta_hp": 800.0,  # ₹800 per hp (ECU flash, intake, exhaust)
        "mass_delta_kg": -1500.0,  # negative: weight reduction costs money
        "cd_delta": 0.0,  # aero mods estimated via part costs
        "frontal_area_delta_m2": 0.0,
        "tire_mu_delta": 3000.0,  # tire compound/upgrade cost
        "rear_pressure_delta": 0.0,  # pressure tuning is free (just air)
        "gearing_ratio_delta": 5000.0,  # sprocket/chain kit
    }

    def __init__(
        self,
        base_config: BikeConfig,
        budget_inr: float = 100_000,
        n_iterations: int = 50,
        verbose: bool = False,
    ):
        """
        Initialize the optimizer.

        Parameters
        ----------
        base_config
            Stock BikeConfig (unmodified baseline).
        budget_inr
            Maximum spend in rupees.
        n_iterations
            Number of BO iterations (trials). Each trial runs one physics sim.
        verbose
            If True, print progress to stdout.
        """
        self.base_config = copy.deepcopy(base_config)
        self.budget_inr = budget_inr
        self.n_iterations = n_iterations
        self.verbose = verbose

        # Get baseline ET
        try:
            engine = MotoQuantEngine(self.base_config)
            result = engine.run()
            self.base_et_s = result.time_quarter
        except Exception as exc:
            warnings.warn(f"BayesianBuildOptimizer: baseline sim failed — {exc}")
            self.base_et_s = float("nan")

        # Storage for BO iterations
        self.X_samples: list[np.ndarray] = []  # parameter vectors
        self.Y_samples: list[float] = []  # ET values (lower = better, so we minimize)
        self.costs: list[float] = []  # estimated build costs

        self.best_et_s = float("inf")
        self.best_idx = -1

    def _estimate_cost(self, params: dict[str, float]) -> float:
        """Estimate build cost from parameter deltas."""
        cost = 0.0
        for key, delta in params.items():
            unit_cost = self.COST_PER_UNIT.get(key, 0.0)
            cost += abs(delta) * unit_cost
        return max(0.0, cost)

    def _apply_params_to_config(
        self,
        params: dict[str, float],
    ) -> BikeConfig:
        """Apply parameter deltas to a copy of the base config."""
        cfg = copy.deepcopy(self.base_config)

        # Power
        cfg.engine.peak_power_hp += params.get("power_delta_hp", 0.0)
        cfg.engine.peak_power_hp = max(1.0, cfg.engine.peak_power_hp)

        # Mass (dry mass reduction)
        cfg.chassis.dry_mass_kg += params.get("mass_delta_kg", 0.0)
        cfg.chassis.dry_mass_kg = max(10.0, cfg.chassis.dry_mass_kg)

        # Aero
        cfg.aero.cd += params.get("cd_delta", 0.0)
        cfg.aero.cd = np.clip(cfg.aero.cd, 0.30, 1.50)

        cfg.aero.frontal_area_m2 += params.get("frontal_area_delta_m2", 0.0)
        cfg.aero.frontal_area_m2 = np.clip(cfg.aero.frontal_area_m2, 0.25, 0.75)

        # Tires
        cfg.tires.mu_peak += params.get("tire_mu_delta", 0.0)
        cfg.tires.mu_peak = np.clip(cfg.tires.mu_peak, 0.70, 1.80)

        cfg.tires.rear_pressure_psi += params.get("rear_pressure_delta", 0.0)
        cfg.tires.rear_pressure_psi = np.clip(cfg.tires.rear_pressure_psi, 20.0, 50.0)

        # Gearing: apply as a multiplicative factor to the EFFECTIVE final
        # drive. Reading/writing final_drive_ratio directly is a no-op for
        # chain bikes (final_ratio prefers sprocket teeth), so scale final_ratio
        # and push it through set_effective_final_drive so the sim actually sees
        # the change. delta=0 reproduces the baseline exactly.
        ratio_delta = params.get("gearing_ratio_delta", 0.0)
        new_ratio = float(
            np.clip(cfg.drivetrain.final_ratio * (1.0 + ratio_delta), 1.5, 6.5)
        )
        cfg.drivetrain.set_effective_final_drive(new_ratio)

        return cfg

    def _run_et(self, config: BikeConfig) -> float:
        """Run a simulation and return quarter-mile ET in seconds."""
        try:
            engine = MotoQuantEngine(config)
            result = engine.run()
            return result.time_quarter
        except Exception as exc:
            warnings.warn(f"BayesianBuildOptimizer: sim failed — {exc}")
            return float("nan")

    def _objective_with_penalty(
        self,
        params: dict[str, float],
    ) -> tuple[float, float]:
        """
        Evaluate objective: ET with budget penalty.

        Returns (ET_with_penalty, cost).
        Penalty is applied if cost > budget.
        """
        cost = self._estimate_cost(params)
        cfg = self._apply_params_to_config(params)
        et = self._run_et(cfg)

        # Apply budget penalty: if cost > budget, add a large penalty to ET
        if cost > self.budget_inr:
            overage = cost - self.budget_inr
            penalty = 0.5 * (
                overage / self.budget_inr
            )  # 50% penalty per budget overrun
            et_penalised = et + penalty
        else:
            et_penalised = et

        return et_penalised, cost

    def optimize(self) -> OptimizationResult:
        """
        Run Bayesian optimization.

        Explores the parameter space using Latin Hypercube initial sampling,
        then BoTorch's Expected Improvement acquisition function.

        Returns
        -------
        OptimizationResult with the best configuration found.
        """
        try:
            import torch
            from botorch.fit import fit_gpytorch_mll
            from botorch.models import SingleTaskGP
            from botorch.optim import optimize_acqf
            from botorch.utils.sampling import draw_sobol_samples
            from gpytorch.mlls import ExactMarginalLogLikelihood
        except ImportError as exc:
            raise ImportError(
                "BoTorch is required for Bayesian optimization: "
                "pip install botorch gpytorch --break-system-packages"
            ) from exc

        param_names = list(self.PARAM_BOUNDS.keys())
        bounds = torch.tensor(
            [
                [self.PARAM_BOUNDS[k][0] for k in param_names],
                [self.PARAM_BOUNDS[k][1] for k in param_names],
            ],
            dtype=torch.float32,
        )

        if self.verbose:
            print(f"BoTorch Bayesian Optimization: {self.n_iterations} iterations")
            print(f"Parameter space: {len(param_names)} dimensions")
            print(f"Budget: ₹{self.budget_inr:,.0f}")

        # Latin Hypercube initial sampling for diversity
        n_init = min(4, max(2, self.n_iterations // 10))
        if self.verbose:
            print(f"Initial sampling: {n_init} configurations...")

        for i in range(n_init):
            # Draw random sample within bounds
            X_init = draw_sobol_samples(
                bounds=bounds,
                n=1,
                q=1,
                seed=i,
            ).squeeze(0)

            params = {k: float(X_init[j].item()) for j, k in enumerate(param_names)}
            et_p, cost = self._objective_with_penalty(params)

            self.X_samples.append(X_init.numpy())
            self.Y_samples.append(et_p)
            self.costs.append(cost)

            if et_p < self.best_et_s:
                self.best_et_s = et_p
                self.best_idx = len(self.X_samples) - 1

            if self.verbose and (i + 1) % max(1, n_init // 3) == 0:
                print(
                    f"  {i + 1}/{n_init} initial samples: best ET={self.best_et_s:.3f}s"
                )

        # BO loop: fit GP, sample next point via EI
        for iteration in range(n_init, self.n_iterations):
            # Convert to torch tensors
            X_tensor = torch.tensor(np.array(self.X_samples), dtype=torch.float32)
            Y_tensor = torch.tensor(
                np.array(self.Y_samples).reshape(-1, 1), dtype=torch.float32
            )

            # Fit SingleTaskGP
            model = SingleTaskGP(X_tensor, Y_tensor)
            mll = ExactMarginalLogLikelihood(model.likelihood, model)
            fit_gpytorch_mll(mll)

            # Generate next candidate via Expected Improvement
            from botorch.acquisition import ExpectedImprovement

            ei = ExpectedImprovement(model, best_f=Y_tensor.min())
            candidates, _ = optimize_acqf(
                acq_function=ei,
                bounds=bounds,
                q=1,
                num_restarts=8,
                raw_samples=64,
            )
            X_next = candidates[0]

            # Evaluate
            params = {k: float(X_next[j].item()) for j, k in enumerate(param_names)}
            et_p, cost = self._objective_with_penalty(params)

            self.X_samples.append(X_next.numpy())
            self.Y_samples.append(et_p)
            self.costs.append(cost)

            if et_p < self.best_et_s:
                self.best_et_s = et_p
                self.best_idx = len(self.X_samples) - 1

            if self.verbose and (iteration + 1) % max(1, self.n_iterations // 10) == 0:
                pct = 100 * (iteration + 1) / self.n_iterations
                print(
                    f"  {pct:5.1f}%  ({iteration + 1}/{self.n_iterations} iters): "
                    f"best ET={self.best_et_s:.3f}s"
                )

        if self.verbose:
            print("  100.0%  done — compilation of results...")

        # Extract best result
        best_params_arr = self.X_samples[self.best_idx]
        best_params = {k: float(best_params_arr[j]) for j, k in enumerate(param_names)}
        best_cost = self.costs[self.best_idx]

        return OptimizationResult(
            base_et_s=self.base_et_s,
            best_et_s=self.best_et_s,
            et_improvement_s=self.base_et_s - self.best_et_s,
            estimated_cost_inr=best_cost,
            budget_inr=self.budget_inr,
            remaining_budget_inr=self.budget_inr - best_cost,
            best_power_delta_hp=best_params["power_delta_hp"],
            best_mass_delta_kg=best_params["mass_delta_kg"],
            best_cd_delta=best_params["cd_delta"],
            best_frontal_area_delta_m2=best_params["frontal_area_delta_m2"],
            best_tire_mu_delta=best_params["tire_mu_delta"],
            best_rear_pressure_delta=best_params["rear_pressure_delta"],
            best_gearing_ratio_delta=best_params["gearing_ratio_delta"],
            n_iterations=self.n_iterations,
            iterations_completed=len(self.X_samples),
            best_iteration=self.best_idx + 1,
        )


# ─────────────────────────────────────────────────────────────────
# Public convenience function
# ─────────────────────────────────────────────────────────────────


def optimize_build(
    config: BikeConfig,
    budget_inr: float = 100_000,
    n_iterations: int = 50,
    verbose: bool = False,
) -> OptimizationResult:
    """
    One-shot Bayesian build optimizer.

    Parameters
    ----------
    config
        Stock BikeConfig (baseline).
    budget_inr
        Maximum build cost in rupees.
    n_iterations
        Number of BO trials (each runs one physics simulation).
        Default 50 → ~15–30 minutes on a laptop.
    verbose
        If True, print progress to stdout.

    Returns
    -------
    OptimizationResult with best ET and estimated cost.

    Raises
    ------
    ImportError
        If BoTorch is not installed.

    Example
    -------
    >>> from motoquant.defaults import gsxr1000_k5
    >>> from motoquant.analysis.bayesian_opt import optimize_build
    >>> config = gsxr1000_k5()
    >>> result = optimize_build(config, budget_inr=150_000, n_iterations=30)
    >>> print(result.summary())
    """
    optimizer = BayesianBuildOptimizer(
        base_config=config,
        budget_inr=budget_inr,
        n_iterations=n_iterations,
        verbose=verbose,
    )
    return optimizer.optimize()
