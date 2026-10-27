"""
test_epoch_physics_rollout.py
=============================
2026-10 physics epoch, item 5: drag-strip rollout timing convention.

Published ETs are timed from the moment the front tyre clears the staging
beam, ~1 ft (constants.ROLLOUT_M = 0.3048 m) after the bike starts moving.
run() integrates from rest and reports every split as
    time_D  = t(x = rollout + D) - t(x = rollout)
    speed_D = v(x = rollout + D)
run(rollout_m=0.0) is the "from first motion" convention (pre-epoch splits).
"""

from __future__ import annotations

import numpy as np
import pytest

import motoquant
from motoquant.constants import (
    EIGHTH_MILE_M,
    QUARTER_MILE_M,
    ROLLOUT_M,
    SIXTY_FOOT_M,
)
from motoquant.defaults import gsxr1000_k5, yzfr1_4c8


def _interp(r, d):
    """Independent re-implementation: (t, v) at absolute position d."""
    return float(np.interp(d, r.x, r.t)), float(np.interp(d, r.x, r.v))


def test_rollout_constant_is_one_foot():
    assert ROLLOUT_M == 0.3048


def test_default_run_uses_the_one_foot_rollout():
    r = motoquant.MotoQuantEngine(gsxr1000_k5()).run()
    assert r.rollout_m == ROLLOUT_M
    # the run continues to the finish line 1 ft further from rest
    assert r.x[-1] >= QUARTER_MILE_M + ROLLOUT_M
    assert r.x[-2] < QUARTER_MILE_M + ROLLOUT_M


@pytest.mark.parametrize("factory", (gsxr1000_k5, yzfr1_4c8), ids=lambda f: f.__name__)
def test_splits_are_timed_from_the_start_beam(factory):
    r = motoquant.MotoQuantEngine(factory()).run()
    t_beam, _ = _interp(r, ROLLOUT_M)
    for d, t_attr, s_attr in (
        (SIXTY_FOOT_M, "time_60ft", "speed_60ft"),
        (EIGHTH_MILE_M, "time_eighth", "speed_eighth"),
        (QUARTER_MILE_M, "time_quarter", "speed_quarter"),
    ):
        t_fin, v_fin = _interp(r, ROLLOUT_M + d)
        assert abs(getattr(r, t_attr) - (t_fin - t_beam)) < 1e-9
        assert abs(getattr(r, s_attr) - v_fin) < 1e-9
    # the beam is cleared a fraction of a second after launch
    assert 0.1 < t_beam < 0.5


def test_rollout_zero_reproduces_from_rest_timing_on_the_same_trajectory():
    """The integration itself is independent of the rollout: a rollout-0 run
    to the same finish line traces the identical trajectory, and the default
    ET equals t(x = r + 402.336) - t(x = r) read off it."""
    eng = motoquant.MotoQuantEngine(gsxr1000_k5())
    default = eng.run()
    plain = eng.run(distance=QUARTER_MILE_M + ROLLOUT_M, rollout_m=0.0)
    assert np.array_equal(default.t, plain.t)
    assert np.array_equal(default.x, plain.x)
    assert np.array_equal(default.v, plain.v)
    beam = plain.time_speed_at(ROLLOUT_M)
    fin = plain.time_speed_at(QUARTER_MILE_M + ROLLOUT_M)
    assert default.time_quarter == fin[0] - beam[0]
    assert default.speed_quarter == fin[1]
    # from-first-motion timing on a quarter-mile run
    zero = eng.run(rollout_m=0.0)
    assert zero.rollout_m == 0.0
    assert zero.time_quarter == pytest.approx(
        _interp(zero, QUARTER_MILE_M)[0], abs=1e-9
    )
    assert default.time_quarter < zero.time_quarter - 0.1
    assert abs(default.speed_quarter - zero.speed_quarter) < 0.1  # trap ~unchanged


def test_max_distance_is_measured_past_the_beam():
    r = motoquant.MotoQuantEngine(gsxr1000_k5()).run(max_time=3.0)
    assert not r.finished_quarter
    assert r.max_distance_m == pytest.approx(r.x[-1] - ROLLOUT_M, abs=1e-12)
    assert r.elapsed_time_s == r.t[-1]  # raw sim clock, not rollout-adjusted


@pytest.mark.parametrize("bad", (-0.1, float("nan"), float("inf")))
def test_invalid_rollout_raises(bad):
    with pytest.raises(ValueError):
        motoquant.MotoQuantEngine(gsxr1000_k5()).run(rollout_m=bad)


def test_top_speed_lsr_quarter_matches_the_quarter_mile_et():
    eng = motoquant.MotoQuantEngine(gsxr1000_k5())
    ts = eng.run_top_speed()
    q = eng.run(use_adaptive_dt=True)
    assert ts.lsr_splits["quarter_mile"]["time_s"] == pytest.approx(
        q.time_quarter, abs=1e-12
    )


def test_run_distance_split_at_uses_the_convention():
    eng = motoquant.MotoQuantEngine(gsxr1000_k5())
    r = eng.run_distance(1000.0, max_time=60.0)
    t, v = r.split_at(1000.0)
    t_beam, _ = _interp(r, ROLLOUT_M)
    t_fin, v_fin = _interp(r, ROLLOUT_M + 1000.0)
    assert t == pytest.approx(t_fin - t_beam, abs=1e-9)
    assert v == pytest.approx(v_fin, abs=1e-9)
