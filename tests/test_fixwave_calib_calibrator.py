"""
Fix-wave regressions — auto-calibration (motoquant/calibration/calibrator.py).

Drives the public calibrate() / calibrate_multi_run() / CalibrationResult
API. Every test fails on the pre-fix code:

* the Nelder-Mead refinement ran UNBOUNDED, returning values outside the
  spec's declared bounds (a K5 fit gave cd 0.30 for bounds 0.45-0.95);
* PRESET_FULL named a nonexistent 'drivetrain.efficiency' (AttributeError
  on every call), and _set_param silently wrote phantom attributes;
* simulations bypassed motoquant.engine_select (never used the Rust core).
"""

import copy

import numpy as np
import pytest

from motoquant import engine_select
from motoquant.calibration import calibrator
from motoquant.calibration.calibrator import (
    PRESET_AERO_ONLY,
    PRESET_FULL,
    CalibrationError,
    CalibrationResult,
    calibrate,
    calibrate_multi_run,
)
from motoquant.calibration.dragy import (
    DragRunData,
    _compute_acceleration,
    _integrate_distance,
)
from motoquant.defaults import gsxr1000_k5


def _sim_as_gps_run(cfg) -> DragRunData:
    """A noiseless 10 Hz 'GPS run' produced by simulating cfg."""
    r = engine_select.make_engine(cfg).run()
    t = np.asarray(r.t)[::100]
    v = np.asarray(r.v)[::100]
    return DragRunData(
        timestamps=t,
        velocity_ms=v,
        distance_m=_integrate_distance(t, v),
        acceleration_ms2=_compute_acceleration(t, v),
        et_quarter=r.time_quarter,
        trap_speed_ms=r.speed_quarter,
        sample_rate_hz=10.0,
        source_file="synthetic",
    )


@pytest.fixture(scope="module")
def low_cd_case():
    """Truth has cd 0.30, below PRESET_AERO_ONLY's (0.45, 0.95) bounds; the
    starting config already sits at the (out-of-bounds) optimum."""
    base = gsxr1000_k5()
    truth = copy.deepcopy(base)
    truth.aero.cd = 0.30
    start = copy.deepcopy(base)
    start.aero.cd = 0.30
    return start, _sim_as_gps_run(truth)


# ─── 1. Bounds are honoured end to end ────────────────────────────────────


def test_local_refinement_stays_inside_declared_bounds(low_cd_case):
    start, real = low_cd_case
    lo, hi = PRESET_AERO_ONLY[0]["bounds"]
    res = calibrate(start, real, PRESET_AERO_ONLY, global_search=False, local_maxiter=8)
    fitted = res.fitted_params["aero.cd"]
    assert lo <= fitted <= hi, fitted  # old: 0.30
    applied = res.apply(start)
    assert lo <= applied.aero.cd <= hi


@pytest.mark.skipif(
    not engine_select.native_active(),
    reason="multi-run DE is ~200 sims per run; affordable on the Rust core only",
)
def test_multi_run_refinement_stays_inside_bounds(low_cd_case):
    start, real = low_cd_case
    lo, hi = PRESET_AERO_ONLY[0]["bounds"]
    res = calibrate_multi_run(start, [real, real], PRESET_AERO_ONLY)
    assert lo <= res.fitted_params["aero.cd"] <= hi


# ─── 2. Parameter paths are real fields ───────────────────────────────────


def test_preset_full_targets_real_fields():
    cfg = gsxr1000_k5()
    for spec in PRESET_FULL:
        calibrator._get_param(cfg, spec["path"])  # old: AttributeError
    paths = [s["path"] for s in PRESET_FULL]
    assert "drivetrain.chain_efficiency" in paths


def test_preset_full_calibration_runs(low_cd_case):
    start, real = low_cd_case
    res = calibrate(start, real, PRESET_FULL, global_search=False, local_maxiter=2)
    assert isinstance(res, CalibrationResult)
    for spec in PRESET_FULL:
        lo, hi = spec["bounds"]
        assert lo <= res.fitted_params[spec["path"]] <= hi


@pytest.mark.parametrize(
    "path", ["drivetrain.efficiency", "aero.cdd", "aero", "nosuch.cd", "aero.cd.x"]
)
def test_unknown_paths_raise_instead_of_writing_phantoms(path):
    cfg = gsxr1000_k5()
    with pytest.raises(CalibrationError):
        calibrator._set_param(cfg, path, 0.82)
    with pytest.raises(CalibrationError):
        calibrator._get_param(cfg, path)
    assert not hasattr(cfg.drivetrain, "efficiency")


def test_calibrate_rejects_unknown_path_before_simulating(low_cd_case, monkeypatch):
    start, real = low_cd_case
    calls = {"n": 0}
    real_make = engine_select.make_engine

    def counting(cfg, dt=0.001):
        calls["n"] += 1
        return real_make(cfg, dt=dt)

    monkeypatch.setattr(engine_select, "make_engine", counting)
    with pytest.raises(CalibrationError, match="unknown parameter path"):
        calibrate(
            start,
            real,
            [{"path": "drivetrain.efficiency", "bounds": (0.8, 0.97)}],
            global_search=False,
        )
    assert calls["n"] == 0


def test_non_numeric_field_is_rejected():
    cfg = gsxr1000_k5()
    with pytest.raises(CalibrationError, match="not numeric"):
        calibrator._get_param(cfg, "drivetrain.chain_pitch")


# ─── 3. Simulations go through engine_select ──────────────────────────────


def test_calibration_sims_use_engine_select(low_cd_case, monkeypatch):
    start, real = low_cd_case
    calls = {"n": 0}
    real_make = engine_select.make_engine

    def counting(cfg, dt=0.001):
        calls["n"] += 1
        return real_make(cfg, dt=dt)

    monkeypatch.setattr(engine_select, "make_engine", counting)
    res = calibrate(start, real, PRESET_AERO_ONLY, global_search=False, local_maxiter=2)
    assert calls["n"] == res.iterations + 1  # every objective eval + final sim
