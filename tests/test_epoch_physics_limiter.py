"""
test_epoch_physics_limiter.py
=============================
2026-10 physics epoch, item 3: soft-cut rev limiter.

The old limiter returned zero torque above 1.02 × redline while the clutch-
slip phase clipped omega_e to exactly 1.02 × redline. The round trip
(omega → rpm) landed a hair ABOVE the cut, so a launch whose torque exceeded
the (faded) clutch capacity ran up to the clip and FROZE there: zero drive
force forever, the clutch never locked (ZX-10R + HKS turbo 10.36 → 25.57 s,
Panigale V4 + G25 turbo 24.3 s). In top gear the same cliff chattered at the
step rate, so run_top_speed never saw a plateau (Ninja 400 "terminal" at
111 s / 6.3 km instead of ~28 s).

Now: full torque to redline, a linear taper to a full cut at
REV_LIMITER_CUT_FACTOR × redline (1.04 — same integrated allowance as the old
hard cut at 1.02), and no second cliff inside the 2T fallback curve.
"""

from __future__ import annotations

import numpy as np

import motoquant
from motoquant.constants import REV_LIMITER_CUT_FACTOR
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1


def _turbo_weak_clutch():
    cfg = hayabusa_gen1()
    fi = cfg.forced_induction
    fi.boost_type = "turbo"
    fi.target_boost_bar = 1.5
    fi.intercooler_type = "none"
    cfg.clutch.spring_preload_n = 400.0  # ~1/3 of stock capacity
    return cfg


def test_torque_is_continuous_through_the_limiter():
    eng = motoquant.MotoQuantEngine(gsxr1000_k5())
    rl = eng.cfg.engine.redline_rpm
    cut = rl * REV_LIMITER_CUT_FACTOR
    t_at_rl = eng.engine_torque(rl, 1.0)
    assert t_at_rl > 0
    # just above redline: continuous (no step)
    assert abs(eng.engine_torque(rl + 1e-6, 1.0) - t_at_rl) < 1e-3
    # at the slip-phase clip (1.02 x redline) torque is still strictly positive
    t_clip = eng.engine_torque(rl * 1.02, 1.0)
    assert 0.3 * t_at_rl < t_clip < 0.7 * t_at_rl
    # full cut at/above the cut point, continuous approach to it
    assert eng.engine_torque(cut, 1.0) == 0.0
    assert eng.engine_torque(cut * 1.01, 1.0) == 0.0
    assert eng.engine_torque(cut - 1e-3, 1.0) < 1e-3
    # below redline the curve value is untouched (shift points are <= redline)
    for rpm in np.linspace(eng.cfg.engine.idle_rpm, rl, 25):
        e = eng.cfg.engine
        expect = e.get_torque(rpm)
        if e.dyno_curve is not None and e.dyno_curve.is_at_wheel:
            expect /= eng.eta_dt
        expect *= eng.power_correction
        assert abs(eng.engine_torque(rpm, 1.0) - expect) < 1e-9


def test_boosted_launch_over_clutch_capacity_never_freezes():
    cfg = _turbo_weak_clutch()
    eng = motoquant.MotoQuantEngine(cfg)
    r = eng.run()
    assert r.finished_quarter
    assert r.time_quarter < 12.0, r.time_quarter
    # the slip phase did reach the limiter region ...
    assert r.rpm.max() > cfg.engine.redline_rpm
    # ... but drive force never sits at zero for a sustained stretch (the old
    # freeze held F_drive == 0 in first gear for > 20 s). The only zero-drive
    # windows left are the gearshift torque cuts.
    zero = np.concatenate(([0], (r.F_drive <= 0.0).astype(np.int8), [0]))
    edges = np.diff(zero)
    longest = (np.flatnonzero(edges == -1) - np.flatnonzero(edges == 1)).max(initial=0)
    shift_s = cfg.drivetrain.total_shift_time_ms / 1000.0
    assert longest * r.dt <= shift_s + 0.01, (longest * r.dt, shift_s)


def test_top_gear_limiter_reaches_a_plateau():
    cfg = gsxr1000_k5()
    cfg.drivetrain.rear_sprocket = 70  # rev-limited in top gear long before aero
    ts = motoquant.MotoQuantEngine(cfg).run_top_speed()
    assert ts.reached_plateau
    assert ts.time_to_terminal_s < 20.0, ts.time_to_terminal_s
    assert ts.terminal_rpm > cfg.engine.redline_rpm  # settled inside the taper
    assert ts.terminal_rpm < cfg.engine.redline_rpm * REV_LIMITER_CUT_FACTOR
    # no chatter: the accel channel stops flipping sign once terminal
    sim = ts.full_sim
    tail = sim.a[sim.t > ts.time_to_terminal_s + 2.0]
    flips = np.count_nonzero(np.diff(np.sign(tail[np.abs(tail) > 1e-6])))
    assert flips < 5, flips


def test_two_stroke_fallback_curve_has_no_second_cliff():
    cfg = hayabusa_gen1()
    e = cfg.engine
    e.dyno_curve = None
    e.stroke_type = 2
    e.tuned_rpm = 9000.0
    e.cylinder_count = 2
    rl = e.redline_rpm
    # get_torque itself no longer zeroes above 1.02 x redline; the limiter
    # (EngineModel) is the single cut.
    assert e.get_torque(rl * 1.03) > 0.0
    eng = motoquant.MotoQuantEngine(cfg)
    assert eng.engine_torque(rl * 1.03, 1.0) > 0.0
    assert eng.engine_torque(rl * REV_LIMITER_CUT_FACTOR, 1.0) == 0.0
