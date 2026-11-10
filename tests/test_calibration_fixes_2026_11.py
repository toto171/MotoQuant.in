"""Calibration fixes (November 2026): GPS/ECU motion-onset timing, ECU speed
units, calibrator presets and multi-run simulation count."""

import copy
import functools
import os
import tempfile

import numpy as np
import pytest

from motoquant.calibration import calibrator as cal
from motoquant.calibration.calibrator import (
    PRESET_AERO_ONLY,
    PRESET_AERO_TIRE,
    PRESET_FULL,
    PRESET_TIRE_ONLY,
    _get_param,
    _Objective,
    _set_param,
    calibrate_multi_run,
)
from motoquant.calibration.dragy import (
    DragRunData,
    _build_run_list,
    _compute_acceleration,
    _integrate_distance,
    parse_dragy_file,
)
from motoquant.calibration.ecu import _map_column, parse_ecu_file
from motoquant.constants import QUARTER_MILE_M
from motoquant.defaults import gsxr1000_k5
from motoquant.physics import MotoQuantEngine
from motoquant.scraper.importer import spec_to_bike_config
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

MPH = 0.44704


@pytest.fixture(scope="module")
def k5_sim():
    return MotoQuantEngine(gsxr1000_k5()).run()


def _sampled_run(t_sim, v_sim, hz, lead_in_s=2.0, tail_s=1.0, noise=0.0, seed=0):
    """Sample the sim's v(t) at ``hz`` after a stationary lead-in."""
    dt = 1.0 / hz
    t_move = np.arange(0.0, float(t_sim[-1]) + tail_s, dt)
    v_move = np.interp(t_move, t_sim, v_sim)
    v_move[0] = 0.0
    n_lead = int(round(lead_in_s * hz))
    t = np.concatenate([np.arange(-n_lead, 0) * dt, t_move]) + lead_in_s
    v = np.concatenate([np.zeros(n_lead), v_move])
    if noise:
        v = np.clip(
            v + np.random.default_rng(seed).normal(0.0, noise, len(v)), 0.0, None
        )
    return t, v


def _gps_et(t, v):
    runs = _build_run_list(t, v, None, "synthetic", {})
    assert len(runs) == 1
    return runs[0].et_quarter


# ── GPS run timing ───────────────────────────────────────────────────────


@pytest.mark.parametrize("hz", [10.0, 25.0])
def test_dragy_et_matches_sim_origin(k5_sim, hz):
    t, v = _sampled_run(k5_sim.t, k5_sim.v, hz)
    assert abs(_gps_et(t, v) - k5_sim.time_quarter) < 0.03


@pytest.mark.parametrize("hz", [10.0, 25.0])
def test_dragy_et_with_gps_noise(k5_sim, hz):
    errs = []
    for seed in range(12):
        t, v = _sampled_run(k5_sim.t, k5_sim.v, hz, noise=0.05, seed=seed)
        errs.append(_gps_et(t, v) - k5_sim.time_quarter)
    assert abs(float(np.mean(errs))) < 0.03
    assert max(abs(e) for e in errs) < 0.06


@pytest.mark.parametrize("hz", [10.0, 25.0])
def test_dragy_constant_acceleration(hz):
    a = 8.0
    t = np.arange(0.0, 12.0, 1.0 / hz)
    v = np.minimum(a * t, 90.0)
    t = np.concatenate([np.arange(-20, 0) / hz, t]) + 2.0
    v = np.concatenate([np.zeros(20), v])
    true_et = float(np.sqrt(2 * QUARTER_MILE_M / a))
    assert abs(_gps_et(t, v) - true_et) < 0.01


def test_dragy_run_starts_from_rest(k5_sim):
    t, v = _sampled_run(k5_sim.t, k5_sim.v, 10.0)
    run = _build_run_list(t, v, None, "synthetic", {})[0]
    assert run.timestamps[0] == 0.0
    assert run.velocity_ms[0] == 0.0
    assert run.distance_m[0] == 0.0


def test_dragy_csv_end_to_end(k5_sim, tmp_path):
    t, v = _sampled_run(k5_sim.t, k5_sim.v, 25.0)
    path = tmp_path / "run.csv"
    with open(path, "w") as fh:
        fh.write("Time (s),Speed (mph)\n")
        for ti, vi in zip(t, v):
            fh.write(f"{ti:.3f},{vi / MPH:.4f}\n")
    (run,) = parse_dragy_file(path)
    assert abs(run.et_quarter - k5_sim.time_quarter) < 0.03


# ── ECU run timing ───────────────────────────────────────────────────────


def _ecu_csv(t, v_ms, speed_header="Speed", scale=3.6):
    fd, path = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w") as fh:
        fh.write(f"Time,RPM,TPS%,{speed_header}\n")
        for ti, vi in zip(t, v_ms):
            fh.write(f"{ti:.3f},5000,100.0,{vi * scale:.4f}\n")
    return path


@pytest.mark.parametrize("hz", [10.0, 25.0])
def test_ecu_et_matches_sim_origin(k5_sim, hz):
    t, v = _sampled_run(k5_sim.t, k5_sim.v, hz)
    path = _ecu_csv(t, v)
    try:
        log = parse_ecu_file(path)
    finally:
        os.unlink(path)
    assert len(log.runs) == 1
    run = log.runs[0]
    assert abs(run.et_quarter - k5_sim.time_quarter) < 0.03
    assert run.time_s[0] == 0.0
    assert run.onset_lead_s > 0.0
    assert abs(run.splits()["1320ft"] - run.et_quarter) < 1e-3


@pytest.mark.parametrize("hz", [10.0, 25.0])
def test_ecu_et_with_noise(k5_sim, hz):
    errs = []
    for seed in range(8):
        t, v = _sampled_run(k5_sim.t, k5_sim.v, hz, noise=0.05, seed=seed)
        path = _ecu_csv(t, v)
        try:
            runs = parse_ecu_file(path).runs
        finally:
            os.unlink(path)
        assert len(runs) == 1
        errs.append(runs[0].et_quarter - k5_sim.time_quarter)
    assert abs(float(np.mean(errs))) < 0.03


# ── ECU speed units ──────────────────────────────────────────────────────

_FACTOR = {"kmh": 1 / 3.6, "mph": MPH, "ms": 1.0}


@pytest.mark.parametrize(
    "header,unit",
    [
        ("Speed", "kmh"),
        ("Speed (km/h)", "kmh"),
        ("VSS(km/h)", "kmh"),
        ("Vehicle Speed (km/h)", "kmh"),
        ("Vehicle Speed", "kmh"),
        ("Wheel Speed (km/h)", "kmh"),
        ("Ground Speed (km/h)", "kmh"),
        ("Speed (mph)", "mph"),
        ("Vehicle Speed (mph)", "mph"),
        ("VSS mph", "mph"),
        ("Wheel Speed (mph)", "mph"),
        ("Ground Speed mph", "mph"),
        ("Vehicle Speed (mi/h)", "mph"),
        ("Vehicle Speed (m/s)", "ms"),
        ("Speed (m/s)", "ms"),
    ],
)
def test_ecu_speed_header_units(header, unit):
    std, conv = _map_column(header)
    assert std == "vehicle_speed_ms"
    got = 1.0 if conv is None else float(conv)
    assert got == pytest.approx(_FACTOR[unit])


def test_ecu_mph_log_trap_speed(k5_sim):
    t, v = _sampled_run(k5_sim.t, k5_sim.v, 25.0)
    path = _ecu_csv(t, v, speed_header="Vehicle Speed (mph)", scale=1.0 / MPH)
    try:
        (run,) = parse_ecu_file(path).runs
    finally:
        os.unlink(path)
    assert run.trap_speed_ms == pytest.approx(k5_sim.speed_quarter, abs=0.3)


# ── Calibrator presets ───────────────────────────────────────────────────


@pytest.fixture(scope="module")
def chain_cfg():
    cfg = spec_to_bike_config(ALL_KNOWN_BIKES[100])
    assert not cfg.engine.dyno_curve.is_at_wheel
    return cfg


def _et(cfg):
    return MotoQuantEngine(cfg).run().time_quarter


@pytest.mark.parametrize(
    "preset", [PRESET_AERO_TIRE, PRESET_AERO_ONLY, PRESET_TIRE_ONLY, PRESET_FULL]
)
def test_preset_paths_resolve_and_are_live(chain_cfg, preset):
    base = _et(chain_cfg)
    for spec in preset:
        value = _get_param(chain_cfg, spec["path"])  # raises if the path is bad
        lo, hi = spec["bounds"]
        moved = False
        for edge in (lo, hi):
            cfg = copy.deepcopy(chain_cfg)
            _set_param(cfg, spec["path"], edge)
            moved |= _et(cfg) != base
        assert moved, f"{spec['path']} (={value}) does not change ET"


def test_bad_param_path_raises_value_error(chain_cfg):
    with pytest.raises(ValueError, match="drivetrain.efficiency"):
        _get_param(chain_cfg, "drivetrain.efficiency")
    cfg = copy.deepcopy(chain_cfg)
    with pytest.raises(ValueError, match="drivetrain.efficiency"):
        _set_param(cfg, "drivetrain.efficiency", 0.9)
    assert not hasattr(cfg.drivetrain, "efficiency")
    with pytest.raises(ValueError, match="nonsense"):
        _set_param(cfg, "nonsense.cd", 0.5)


# ── Multi-run calibration simulates once per parameter vector ────────────


def _run_from_cfg(cfg, hz=10.0):
    sim = MotoQuantEngine(cfg).run()
    t, v = sim.t[:: int(round(1000 / hz))], sim.v[:: int(round(1000 / hz))]
    d = _integrate_distance(t, v)
    return DragRunData(
        timestamps=t,
        velocity_ms=v,
        distance_m=d,
        acceleration_ms2=_compute_acceleration(t, v),
        et_quarter=sim.time_quarter,
        trap_speed_ms=sim.speed_quarter,
        sample_rate_hz=hz,
        source_file="synthetic",
    )


def test_multi_run_simulates_once_per_evaluation(monkeypatch):
    truth = spec_to_bike_config(ALL_KNOWN_BIKES[100])
    runs = []
    for i, dcd in enumerate((-0.01, 0.0, 0.01)):
        c = copy.deepcopy(truth)
        c.aero.cd += dcd
        runs.append(_run_from_cfg(c))
    start = copy.deepcopy(truth)
    start.aero.cd += 0.08

    real_de, real_min = cal.differential_evolution, cal.minimize
    monkeypatch.setattr(
        cal,
        "differential_evolution",
        lambda f, bounds, **kw: real_de(
            f, bounds, **{**kw, "popsize": 4, "maxiter": 3}
        ),
    )
    monkeypatch.setattr(
        cal,
        "minimize",
        lambda f, x0, **kw: real_min(
            f, x0, **{**kw, "options": {**kw["options"], "maxiter": 10}}
        ),
    )

    calls = []
    real_run = MotoQuantEngine.run

    @functools.wraps(real_run)
    def counting_run(self, *a, **k):
        calls.append(1)
        return real_run(self, *a, **k)

    monkeypatch.setattr(MotoQuantEngine, "run", counting_run)
    res = calibrate_multi_run(start, runs, params_to_fit=PRESET_AERO_ONLY)
    monkeypatch.undo()

    # one sim per evaluation + the final comparison sim (was 3 per evaluation)
    assert len(calls) <= res.iterations + 2
    assert len(calls) < 1.5 * res.iterations

    # the combined cost is still the mean of the per-run costs at the fit
    specs = PRESET_AERO_ONLY
    x = np.array([res.fitted_params["aero.cd"]])
    per_run = [_Objective(start, r, specs)(x) for r in runs]
    assert res.final_cost == pytest.approx(float(np.mean(per_run)), rel=1e-12)
    assert abs(res.fitted_params["aero.cd"] - truth.aero.cd) < 0.08
