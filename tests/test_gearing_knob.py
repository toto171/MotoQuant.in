"""
test_gearing_knob.py
====================
Pins the analysis-layer final-drive dead-knob fix (July 2 2026).

``DrivetrainParams.final_ratio`` prefers sprocket teeth (rear/front) over the
``final_drive_ratio`` field, so for every chain-drive bike (~all of them)
assigning ``final_drive_ratio`` was a silent no-op. The Sobol sensitivity tool
and the Bayesian build optimizer both perturbed exactly that field, so their
"gearing" knob had zero effect and the reported sensitivity / best gearing was
meaningless. The fix routes gearing through ``set_effective_final_drive``.
"""

from __future__ import annotations

import pytest

import motoquant
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8


def _et(cfg) -> float:
    return motoquant.MotoQuantEngine(cfg).run().time_quarter


def test_direct_final_drive_write_is_a_noop_for_chain_bikes():
    """Documents the trap: writing final_drive_ratio while sprockets are set
    does nothing (final_ratio reads the sprockets)."""
    base = gsxr1000_k5()
    et0 = _et(base)
    cfg = gsxr1000_k5()
    cfg.drivetrain.final_drive_ratio *= 1.10  # the old dead path
    assert abs(_et(cfg) - et0) < 1e-9


def test_set_effective_final_drive_changes_et():
    """The helper must make the gearing change actually reach the sim."""
    base = gsxr1000_k5()
    et0 = _et(base)
    cfg = gsxr1000_k5()
    cfg.drivetrain.set_effective_final_drive(base.drivetrain.final_ratio * 1.10)
    assert abs(_et(cfg) - et0) > 0.01, "taller gearing must move ET"


def test_set_effective_final_drive_identity_preserves_baseline():
    """Setting the effective ratio to its current value must not move ET."""
    base = gsxr1000_k5()
    et0 = _et(base)
    cfg = gsxr1000_k5()
    cfg.drivetrain.set_effective_final_drive(base.drivetrain.final_ratio)
    assert abs(_et(cfg) - et0) < 1e-9


def test_bayesian_gearing_knob_is_live():
    """The Bayesian optimizer's gearing_ratio_delta must change final_ratio,
    and delta=0 must reproduce the baseline effective ratio exactly."""
    from motoquant.analysis.bayesian_opt import BayesianBuildOptimizer

    base_ratio = gsxr1000_k5().drivetrain.final_ratio
    opt = BayesianBuildOptimizer(gsxr1000_k5(), budget_inr=100_000)
    up = opt._apply_params_to_config({"gearing_ratio_delta": 0.10})
    zero = opt._apply_params_to_config({"gearing_ratio_delta": 0.0})
    assert up.drivetrain.final_ratio > base_ratio * 1.05
    assert abs(zero.drivetrain.final_ratio - base_ratio) < 1e-6


def test_reference_baselines_unchanged():
    for name, (fn, target) in {
        "K5": (gsxr1000_k5, 10.0334),
        "R1": (yzfr1_4c8, 10.2859),
        "Hayabusa": (hayabusa_gen1, 10.4712),
    }.items():
        assert abs(_et(fn()) - target) < 1e-4, name


def test_sobol_gearing_sensitivity_nonzero():
    """With the normalisation, a Sobol sweep over final_drive_ratio must
    produce non-zero output variance (previously the knob was dead)."""
    pytest.importorskip("SALib")
    from motoquant.analysis.sobol import SobolParamSpec, compute_sobol_indices

    specs = {
        "final_drive_ratio": SobolParamSpec(
            path="drivetrain.final_drive_ratio",
            low=0.90,
            high=1.10,
            kind="relative",
            description="final drive",
        ),
        "chassis_mass": SobolParamSpec(
            path="chassis.dry_mass_kg",
            low=0.95,
            high=1.05,
            kind="relative",
            description="mass",
        ),
    }
    res = compute_sobol_indices(gsxr1000_k5(), param_specs=specs, n_samples=16, seed=1)
    assert res.to_dict()["et_std"] > 1e-3, "gearing sweep produced no ET variance"
