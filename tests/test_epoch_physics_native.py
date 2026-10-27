"""
test_epoch_physics_native.py
============================
2026-10 physics epoch, item 9: the Rust core (rust/motoquant-core) mirrors
every epoch change bit-for-bit. Skipped when the extension is not built
(``make native``); ``MOTOQUANT_REQUIRE_NATIVE=1`` turns the skip into a
failure, like tests/test_native_engine.py.

Covers the mechanisms whose Rust transliteration is new: rollout timing
(default, 0, custom; validation), slip-phase effective mass, the soft-cut
limiter (slip-clip launch + top-gear plateau), continuous slip ratio, the
intercooler-less penalty and the energy-consistent launch floor.
"""

from __future__ import annotations

import copy
import dataclasses
import os

import numpy as np
import pytest

import motoquant
from motoquant import category_profiles as cp, native
from motoquant.constants import ROLLOUT_M
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1

if not native.available():
    if os.environ.get("MOTOQUANT_REQUIRE_NATIVE") == "1":
        pytest.fail("motoquant_core not built (MOTOQUANT_REQUIRE_NATIVE=1)")
    pytest.skip("motoquant_core not built (make native)", allow_module_level=True)

CHANNELS = (
    "t", "x", "v", "a", "rpm", "gear", "slip", "traction_pct", "N_front",
    "N_rear", "F_drive", "F_drag", "F_rr", "T_tire", "T_clutch", "P_boost",
    "power_kw", "r_eff",
)  # fmt: skip
SPLITS = (
    "time_60ft", "speed_60ft", "time_330ft", "speed_330ft", "time_eighth",
    "speed_eighth", "time_1000ft", "speed_1000ft", "time_quarter",
    "speed_quarter", "finished_quarter", "max_distance_m", "elapsed_time_s",
    "rollout_m",
)  # fmt: skip


def _identical(rp, rn):
    assert len(rp.t) == len(rn.t)
    for ch in CHANNELS:
        assert np.array_equal(getattr(rp, ch), getattr(rn, ch)), ch
    for k in SPLITS:
        assert getattr(rp, k) == getattr(rn, k), k


def _turbo_none_weak_clutch():
    cfg = hayabusa_gen1()
    fi = cfg.forced_induction
    fi.boost_type = "turbo"
    fi.target_boost_bar = 1.5
    fi.intercooler_type = "none"
    cfg.clutch.spring_preload_n = 400.0
    return cfg


CASES = {
    "k5 default rollout": (gsxr1000_k5, {}),
    "k5 rollout 0": (gsxr1000_k5, {"rollout_m": 0.0}),
    "k5 rollout 0.35 adaptive": (
        gsxr1000_k5,
        {"rollout_m": 0.35, "use_adaptive_dt": True},
    ),
    "busa turbo none, slip clip": (_turbo_none_weak_clutch, {}),
    "busa turbo none, slip clip adaptive": (
        _turbo_none_weak_clutch,
        {"use_adaptive_dt": True},
    ),
}


@pytest.mark.parametrize("name", list(CASES))
def test_native_bit_identical(name):
    factory, kw = CASES[name]
    rp = motoquant.MotoQuantEngine(copy.deepcopy(factory())).run(**kw)
    rn = native.NativeEngine(copy.deepcopy(factory())).run(**kw)
    _identical(rp, rn)


def test_native_energy_consistent_floor_both_regimes():
    tag = "test_epoch_native_floor"
    for knobs in (
        {
            "launch_floor_factor": 1.0,
            "over_clutch_factor": 0.6,
            "max_engine_decel_rads2": 3000.0,
        },
        {
            "launch_floor_factor": 1.0,
            "launch_rpm_factor": 0.9,
            "over_clutch_factor": 0.6,
            "max_engine_decel_rads2": 3000.0,
        },
        {
            "launch_floor_factor": 0.8,
            "launch_rpm_factor": 0.75,
            "over_clutch_factor": 0.6,
            "max_engine_decel_rads2": 3000.0,
        },
    ):
        cp._PROFILES[tag] = dataclasses.replace(
            cp.get_profile(cp.CATEGORY_REFERENCE_LITRE_195P), name=tag, **knobs
        )
        try:
            cfg = hayabusa_gen1()
            cfg.category_tag = tag
            rp = motoquant.MotoQuantEngine(copy.deepcopy(cfg)).run()
            rn = native.NativeEngine(copy.deepcopy(cfg)).run()
            _identical(rp, rn)
        finally:
            cp._PROFILES.pop(tag, None)


def test_native_top_gear_limiter_plateau():
    cfg = gsxr1000_k5()
    cfg.drivetrain.rear_sprocket = 70
    tp = motoquant.MotoQuantEngine(copy.deepcopy(cfg)).run_top_speed()
    tn = native.NativeEngine(copy.deepcopy(cfg)).run_top_speed()
    assert tp.reached_plateau and tn.reached_plateau
    assert tp.time_to_terminal_s == tn.time_to_terminal_s
    assert tp.lsr_splits == tn.lsr_splits
    _identical(tp.full_sim, tn.full_sim)


def test_native_summary_carries_the_rollout():
    cfg = gsxr1000_k5()
    s = native.summary_native(cfg)
    r = motoquant.MotoQuantEngine(gsxr1000_k5()).run()
    assert s["rollout_m"] == ROLLOUT_M
    assert s["time_quarter"] == r.time_quarter
    assert s["max_distance_m"] == r.max_distance_m
    s0 = native.summary_native(cfg, rollout_m=0.0)
    r0 = motoquant.MotoQuantEngine(gsxr1000_k5()).run(rollout_m=0.0)
    assert s0["rollout_m"] == 0.0 and s0["time_quarter"] == r0.time_quarter


@pytest.mark.parametrize("bad", (-0.1, float("nan"), float("inf")))
def test_native_rejects_invalid_rollout_like_python(bad):
    with pytest.raises(ValueError):
        native.NativeEngine(gsxr1000_k5()).run(rollout_m=bad)
