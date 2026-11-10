"""
test_epoch_physics_power_cap.py
===============================
2026-10 physics epoch, item 8: synthetic torque curves.

* 4-stroke crank-mode recal 1.08 → 1.00 (``defaults._CRANK_MODE_RECAL``);
  the 2-stroke recal stays 1.08 as its own constant
  (``defaults._CRANK_MODE_RECAL_2T``).
* Rated-power cap: a synthetic 4T curve never makes more than its rated power
  (× the small-cc ladder × recal). The post-peak-power falloff starts with
  zero slope, so power used to keep rising past peak_power_rpm — +16 % on the
  33 catalog bikes in the 50-70 Nm plateau band (MT-07 74 → 92.8 hp at
  redline), 3-5 % on ~200 more.

The catalog test runs every curated spec through the production importer
(``spec_to_bike_config``) and checks the curve the simulator actually gets.
"""

from __future__ import annotations

import logging
import warnings

import numpy as np
import pytest

from motoquant import defaults

HP_W = 745.7


def _ladder(hp: float, cylinders) -> float:
    if hp < 22.0:
        return defaults._CLAIM_LADDER_LT22
    if hp < 30.0:
        return defaults._CLAIM_LADDER_LT30
    if hp < 60.0:
        return defaults._CLAIM_LADDER_LT60_MULTI if cylinders != 1 else 1.0
    return 1.0


def _max_power_hp(curve) -> float:
    rpm = np.asarray(curve.rpm, float)
    tq = np.asarray(curve.torque_nm, float)
    return float(np.max(tq * rpm * 2.0 * np.pi / 60.0) / HP_W)


def test_recal_constants():
    assert defaults._CRANK_MODE_RECAL == 1.00
    assert defaults._CRANK_MODE_RECAL_2T == 1.08


def test_two_stroke_crank_curve_keeps_its_own_recal():
    kw = {
        "peak_torque_nm": 37.0,
        "tuned_rpm": 7500.0,
        "redline_rpm": 8500.0,
        "idle_rpm": 1500.0,
        "peak_power_hp": 39.0,
        "peak_power_rpm": 7500.0,
        "cylinders": 2,
        "displacement_cc": 347.0,
    }
    wheel = defaults._synthetic_2stroke_torque_curve(is_at_wheel=True, **kw)
    crank = defaults._synthetic_2stroke_torque_curve(is_at_wheel=False, **kw)
    assert np.allclose(
        np.asarray(crank.torque_nm),
        np.asarray(wheel.torque_nm) * 1.08,
        rtol=0,
        atol=1e-12,
    )


@pytest.mark.parametrize(
    "spec",
    [
        # MT-07-like plateau band (the 0.88 falloff): 68 Nm @ 6500, 74 hp @ 9000
        {
            "peak_torque_nm": 68.0,
            "peak_rpm": 6500,
            "redline_rpm": 11880,
            "peak_power_hp": 74.0,
            "peak_power_rpm": 9000,
            "cylinders": 2,
        },
        # Interceptor 650-like: 52 Nm @ 5250, 47 hp @ 7150
        {
            "peak_torque_nm": 52.0,
            "peak_rpm": 5250,
            "redline_rpm": 9438,
            "peak_power_hp": 47.0,
            "peak_power_rpm": 7150,
            "cylinders": 2,
        },
        # litre I4 (0.48 falloff) and the K5 reference inputs (0.55 falloff)
        {
            "peak_torque_nm": 113.0,
            "peak_rpm": 11000,
            "redline_rpm": 14500,
            "peak_power_hp": 200.0,
            "peak_power_rpm": 13000,
            "cylinders": 4,
        },
        {
            "peak_torque_nm": 115.0,
            "peak_rpm": 9500,
            "redline_rpm": 13000,
            "peak_power_hp": 160.0,
            "peak_power_rpm": 11500,
            "cylinders": 4,
            "idle_rpm": 1200,
        },
        # small-cc single (0.75 falloff, ladder 1.13)
        {
            "peak_torque_nm": 14.2,
            "peak_rpm": 7500,
            "redline_rpm": 11000,
            "peak_power_hp": 18.4,
            "peak_power_rpm": 10000,
            "cylinders": 1,
        },
    ],
    ids=["plateau_68Nm", "plateau_52Nm", "litre_I4", "k5_ref_inputs", "small_single"],
)
@pytest.mark.parametrize("at_wheel", [True, False], ids=["at_wheel", "crank"])
def test_synthetic_curve_never_exceeds_rated_power(spec, at_wheel):
    curve = defaults._synthetic_torque_curve(is_at_wheel=at_wheel, **spec)
    hp = spec["peak_power_hp"]
    cap = (
        hp
        * _ladder(hp, spec["cylinders"])
        * (1.0 if at_wheel else defaults._CRANK_MODE_RECAL)
    )
    assert _max_power_hp(curve) <= cap * (1 + 1e-12)
    # and it still reaches (essentially) the rated figure — the cap is a
    # ceiling, not a derating
    assert _max_power_hp(curve) >= cap * 0.98


def test_every_catalog_synthetic_curve_respects_rated_power():
    from motoquant.scraper.importer import spec_to_bike_config
    from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

    logging.disable(logging.WARNING)
    checked = band = 0
    worst = 0.0
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for spec in ALL_KNOWN_BIKES:
                if (spec.stroke_type or 4) == 2 or not spec.peak_power_hp:
                    continue
                curve = spec_to_bike_config(spec).engine.dyno_curve
                if curve is None or curve.is_at_wheel:
                    continue  # measured library curves are at-wheel
                hp = float(spec.peak_power_hp)
                cap = hp * _ladder(hp, spec.cylinders) * defaults._CRANK_MODE_RECAL
                ratio = _max_power_hp(curve) / cap
                worst = max(worst, ratio)
                checked += 1
                band += 50 <= float(spec.peak_torque_nm or 0) < 70
    finally:
        logging.disable(logging.NOTSET)
    assert checked > 400
    assert band >= 33  # the plateau-band bikes the audit flagged are covered
    assert worst <= 1 + 1e-12, worst
