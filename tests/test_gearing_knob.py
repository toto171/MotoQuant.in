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
        "K5": (gsxr1000_k5, 9.9331),
        "R1": (yzfr1_4c8, 10.1436),
        "Hayabusa": (hayabusa_gen1, 10.3633),
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


# ─────────────────────────────────────────────────────────────────────────
# July 3, 2026 — shaft/belt sprocket-sentinel fix (production spec path)
# ─────────────────────────────────────────────────────────────────────────
# BikeSpec uses front/rear_sprocket == 0 as the documented shaft/belt
# sentinel. _build_drivetrain_from_spec's `or`-chains treated 0 as missing
# and fabricated chain gearing (K5 17/42 → final 2.471, or Tier-2 category
# sprockets) for all 20 shaft/belt specs. The fix keeps the sprockets at 0
# and resolves the real ratio from importer._SHAFT_BELT_FINAL_DRIVE.


def _sentinel_specs():
    from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

    return [s for s in ALL_KNOWN_BIKES if s.front_sprocket == 0 or s.rear_sprocket == 0]


def test_shaft_belt_sentinel_specs_exist():
    """The catalog carries shaft/belt sentinel specs (BMW R/K, FJR1300,
    V-Rod, ...) — if this drops to zero the tests below silently vacuously
    pass, so pin the population."""
    assert len(_sentinel_specs()) >= 15


def test_shaft_belt_specs_keep_zero_sprockets_and_table_ratio():
    """Production spec path: every 0-sprocket (shaft/belt) spec must come
    out of spec_to_bike_config with sprockets still 0 and final_ratio from
    the researched table — never the fabricated K5 chain gearing."""
    from motoquant.scraper.importer import (
        _shaft_belt_final_drive,
        spec_to_bike_config,
    )

    k5_fabrication = 42.0 / 17.0  # 2.4706 — the old fallthrough value
    for spec in _sentinel_specs():
        cfg = spec_to_bike_config(spec)
        d = cfg.drivetrain
        assert d.front_sprocket == 0 and d.rear_sprocket == 0, (
            f"{spec.model_name}: sentinel sprockets were overwritten "
            f"({d.front_sprocket}/{d.rear_sprocket})"
        )
        want = _shaft_belt_final_drive(spec)
        assert d.final_ratio == pytest.approx(want), (
            f"{spec.model_name}: final_ratio {d.final_ratio:.4f} != table {want}"
        )
        assert d.final_ratio != pytest.approx(k5_fabrication, abs=1e-3), (
            f"{spec.model_name}: still carries the fabricated K5 2.471 gearing"
        )


def test_r1250gs_gets_real_bevel_ratio():
    """The flagship case: BMW R 1250 GS (Tier-1 lookup returns 0/0 shaft)
    must run its real ~2.91 bevel, not K5's 2.471 chain fabrication."""
    from motoquant.scraper.importer import spec_to_bike_config
    from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

    spec = next(
        s
        for s in ALL_KNOWN_BIKES
        if s.manufacturer == "BMW" and s.model_name == "R 1250 GS"
    )
    cfg = spec_to_bike_config(spec)
    assert cfg.drivetrain.final_ratio == pytest.approx(2.91)


def test_chain_bikes_unaffected_by_sentinel_fix():
    """None-vs-0 semantics: chain bikes (real or looked-up tooth counts)
    must keep sprocket-derived gearing exactly as before."""
    from motoquant.scraper.importer import spec_to_bike_config
    from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

    spec = next(s for s in ALL_KNOWN_BIKES if s.model_name == "YZF-R15 V4")
    cfg = spec_to_bike_config(spec)
    d = cfg.drivetrain
    assert d.front_sprocket > 0 and d.rear_sprocket > 0
    assert d.final_ratio == pytest.approx(d.rear_sprocket / d.front_sprocket)
