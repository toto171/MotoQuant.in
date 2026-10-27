"""Regression tests: the forced-induction density-altitude floor must apply
only to boost that actually compensates for thin air.

Audit finding (2026-10-23, motoquant/submodels/environmental.py): ANY
non-NA ``boost_type`` floored the base engine's density correction at 0.97.
Nitrous carries its own oxidiser and does nothing for the base engine's air
charge, and a turbo / supercharger with zero target boost compensates
nothing, yet both gained the floor: on the K5 at the default Aamby
conditions a zero-shot N2O config simmed 0.015 s faster than the identical
NA bike, and 0.089 s faster on a hot day. Every nitrous kit's advertised
gain was inflated by that artifact.

The fix keys the floor on (turbo or SC) AND target_boost_bar > 0. The NA
branch is untouched, so the pinned baselines and the all-NA stock catalog
are bit-identical by construction. The sims run through
``engine_select.run_quarter`` (the Rust core when available); the Rust core
consumes ``power_correction`` resolved by this Python model, so both engines
see the fix.
"""

from __future__ import annotations

import copy

import pytest

from motoquant import gsxr1000_k5
from motoquant.engine_select import make_engine, run_quarter
from motoquant.submodels.environmental import EnvironmentalModel

_RHO_STD = 1.2250


def _hot_aamby():
    cfg = gsxr1000_k5()
    cfg.environment.ambient_temp_c = 36.0
    cfg.environment.relative_humidity_pct = 60.0
    return cfg


def _with_fi(cfg, **fields):
    c = copy.deepcopy(cfg)
    for k, v in fields.items():
        setattr(c.forced_induction, k, v)
    return c


NON_COMPENSATING = [
    pytest.param(
        {"boost_type": "n2o", "n2o_hp_per_stage": 0.0, "n2o_stages": 0}, id="n2o-0hp"
    ),
    pytest.param(
        {"boost_type": "n2o", "n2o_hp_per_stage": 50.0, "n2o_stages": 0},
        id="n2o-kit-without-stages",
    ),
    pytest.param({"boost_type": "turbo", "target_boost_bar": 0.0}, id="turbo-0bar"),
    pytest.param({"boost_type": "sc_roots", "target_boost_bar": 0.0}, id="roots-0bar"),
    pytest.param(
        {"boost_type": "sc_centrifugal", "target_boost_bar": 0.0}, id="centrifugal-0bar"
    ),
]


@pytest.mark.parametrize("make_cfg", [gsxr1000_k5, _hot_aamby], ids=["aamby", "hot"])
@pytest.mark.parametrize("fi", NON_COMPENSATING)
def test_non_compensating_fi_sims_exactly_like_na(make_cfg, fi):
    base = make_cfg()
    na_et = run_quarter(base).time_quarter
    et = run_quarter(_with_fi(base, **fi)).time_quarter
    assert et == na_et, (
        f"{fi} moved ET {et - na_et:+.4f} s with zero effective boost — "
        "the density floor is leaking"
    )


@pytest.mark.parametrize("fi", NON_COMPENSATING)
def test_non_compensating_fi_gets_plain_density_correction(fi):
    cfg = _with_fi(_hot_aamby(), **fi)
    env = EnvironmentalModel(cfg)
    assert env.power_correction == env.rho / _RHO_STD
    assert env.power_correction < 0.97  # i.e. the floor would have bitten
    assert make_engine(cfg).power_correction == env.power_correction


@pytest.mark.parametrize(
    "fi",
    [
        {"boost_type": "turbo", "target_boost_bar": 1.0},
        {"boost_type": "sc_roots", "target_boost_bar": 0.6},
        {"boost_type": "sc_centrifugal", "target_boost_bar": 0.8},
    ],
)
def test_real_boost_keeps_the_floor(fi):
    cfg = _with_fi(_hot_aamby(), **fi)
    env = EnvironmentalModel(cfg)
    assert env.power_correction == max(0.97, env.rho / _RHO_STD) == 0.97


def test_na_correction_is_bit_identical():
    cfg = gsxr1000_k5()
    env = EnvironmentalModel(cfg)
    assert env.power_correction == cfg.environment.air_density() / _RHO_STD


def test_turbo_with_boost_still_beats_na():
    base = _hot_aamby()
    na = run_quarter(base).time_quarter
    turbo = run_quarter(_with_fi(base, boost_type="turbo", target_boost_bar=1.0))
    assert turbo.time_quarter < na - 0.2
