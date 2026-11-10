"""
test_epoch2_physics_rollout.py
==============================
2026-10 physics epoch, round 2: one rollout convention.

The track distance is measured from the start line the bike stages on, the
clock starts at the start beam ~1 ft (constants.ROLLOUT_M) later, and the
finish line is at x = D:

    ET = t(x = D) - t(x = rollout),   trap = v(x = D),   D > rollout

(the strip's beam-to-beam timing; the GPS rule "subtract the time to cover
the first foot" is the same thing). Round 1 ran on to x = rollout + D (+4.8 ms
ET, +16 ms 60 ft on the references), and StagingParams carried a third,
never-read convention (``rollout_distance_mm`` / ``StagingModel.
start_position_m()``) — removed here.
"""

from __future__ import annotations

import dataclasses
import json

import numpy as np
import pytest

import motoquant
from motoquant import native
from motoquant.config_io import config_from_dict, config_to_dict
from motoquant.constants import QUARTER_MILE_M, ROLLOUT_M, SIXTY_FOOT_M
from motoquant.database.bridge import config_to_db_row, db_row_to_config
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1
from motoquant.models import StagingParams
from motoquant.submodels.staging import StagingModel


def _t_at(r, d):
    return float(np.interp(d, r.x, r.t))


def test_finish_line_is_the_distance_from_rest():
    r = motoquant.MotoQuantEngine(gsxr1000_k5()).run()
    assert r.x[-2] < QUARTER_MILE_M <= r.x[-1]
    assert r.max_distance_m == r.x[-1]
    et = _t_at(r, QUARTER_MILE_M) - _t_at(r, ROLLOUT_M)
    assert r.time_quarter == pytest.approx(et, abs=1e-9)
    t60 = _t_at(r, SIXTY_FOOT_M) - _t_at(r, ROLLOUT_M)
    assert r.time_60ft == pytest.approx(t60, abs=1e-9)
    assert r.speed_quarter == pytest.approx(
        float(np.interp(QUARTER_MILE_M, r.x, r.v)), abs=1e-9
    )


def test_rollout_does_not_change_the_trajectory():
    eng = motoquant.MotoQuantEngine(hayabusa_gen1())
    a = eng.run(rollout_m=0.0)
    b = eng.run()
    c = eng.run(rollout_m=1.0)
    for r in (b, c):
        assert np.array_equal(a.x, r.x) and np.array_equal(a.v, r.v)
        assert r.speed_quarter == a.speed_quarter
    # the clock starts later -> shorter ET, by exactly t(rollout)
    assert b.time_quarter == pytest.approx(
        a.time_quarter - _t_at(a, ROLLOUT_M), abs=1e-9
    )
    assert c.time_quarter < b.time_quarter < a.time_quarter


def test_round_one_convention_was_longer_by_the_last_foot():
    """Old finish at rollout + D: the extra foot at ~66 m/s is ~4.6 ms."""
    eng = motoquant.MotoQuantEngine(gsxr1000_k5())
    long = eng.run(distance=QUARTER_MILE_M + ROLLOUT_M)
    old_et = _t_at(long, QUARTER_MILE_M + ROLLOUT_M) - _t_at(long, ROLLOUT_M)
    new = eng.run()
    d = old_et - new.time_quarter
    assert d == pytest.approx(ROLLOUT_M / new.speed_quarter, rel=0.02)
    assert 0.003 < d < 0.007


def test_split_before_the_beam_is_undefined():
    r = motoquant.MotoQuantEngine(gsxr1000_k5()).run()
    assert r.split_at(ROLLOUT_M) is None
    assert r.split_at(0.1) is None
    assert r.split_at(QUARTER_MILE_M) == (r.time_quarter, r.speed_quarter)
    assert r.split_at(1e6) is None  # never reached


@pytest.mark.parametrize(
    "kw",
    (
        {"distance": float("nan")},
        {"distance": 0.0},
        {"distance": -5.0},
        {"distance": ROLLOUT_M},
        {"distance": 0.0, "rollout_m": 0.0},
        {"distance": 1.0, "rollout_m": 1.5},
    ),
    ids=("nan", "zero", "negative", "at_beam", "zero_no_rollout", "before_beam"),
)
def test_distance_must_lie_beyond_the_beam(kw):
    msgs = []
    engines = [motoquant.MotoQuantEngine]
    if native.available():
        engines.append(native.NativeEngine)
    for cls in engines:
        with pytest.raises(ValueError, match="distance must be > rollout_m") as ei:
            cls(gsxr1000_k5()).run(**kw)
        msgs.append(str(ei.value))
    assert len(set(msgs)) == 1, msgs  # same message on both engines


def test_just_past_the_beam_is_a_valid_run():
    r = motoquant.MotoQuantEngine(gsxr1000_k5()).run(distance=0.31)
    assert r.x[-1] >= 0.31 and not r.finished_quarter


def test_api_distance_route_refuses_targets_inside_the_rollout():
    pydantic = pytest.importorskip("pydantic")
    api = pytest.importorskip("motoquant.api")
    with pytest.raises(pydantic.ValidationError):
        api.DistanceRunRequest(bike_preset="k5", distance_m=0.2)
    assert (
        api.DistanceRunRequest(bike_preset="k5", distance_m=1000.0).distance_m == 1000.0
    )


# ── removed StagingParams rollout fields ───────────────────────────────────


def test_staging_rollout_fields_are_gone():
    names = {f.name for f in dataclasses.fields(StagingParams)}
    assert "rollout_distance_mm" not in names
    assert not hasattr(StagingParams(), "rollout_m")
    model = StagingModel(gsxr1000_k5())
    assert not hasattr(model, "start_position_m")
    assert not hasattr(model, "rollout_m")


def test_old_db_blob_with_rollout_field_still_loads():
    row = config_to_db_row(gsxr1000_k5())
    staging = json.loads(row["staging_params"])
    assert "rollout_distance_mm" not in staging
    staging["rollout_distance_mm"] = 350.0  # what pre-round-2 blobs carry
    row["staging_params"] = json.dumps(staging)
    cfg = db_row_to_config(row)
    assert cfg.staging.launch_rpm == gsxr1000_k5().staging.launch_rpm
    assert not hasattr(cfg.staging, "rollout_distance_mm")


def test_old_saved_config_file_with_rollout_field_still_loads():
    d = config_to_dict(gsxr1000_k5())
    d["staging"]["rollout_distance_mm"] = 350.0
    cfg = config_from_dict(d)
    assert cfg.staging == gsxr1000_k5().staging
