"""2026-10 data epoch — library dyno curves vs published power.

* The fabricated Kawasaki Ninja H2 table (243 Nm flat, 295 hp, ~1.8x the
  measured wheel torque) is gone; the H2 builds within published bounds.
* No library (chassis-dyno) curve the importer accepts implies more than
  1.10x the bike's rated crank power — the plausibility gate in
  ``importer._library_curve_plausible``.
"""

from __future__ import annotations

import logging

import numpy as np
import pytest

from motoquant.scraper import importer
from motoquant.scraper.dyno_curves import KNOWN_DYNO_CURVES, get_dyno_curve
from motoquant.scraper.importer import spec_to_bike_config
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

logging.getLogger("motoquant").setLevel(logging.ERROR)

# Kawasaki 2015 Ninja H2 rated figures (iamabiker 2014 spec sheet) and
# Cycle World's Nov-2015 rear-wheel dyno of the same bike.
H2_RATED_HP = 207.0  # 210 PS with ram air @ 11,000 rpm
H2_RATED_NM = 133.5  # @ 10,500 rpm
H2_CW_WHEEL_HP = 189.8
H2_CW_WHEEL_NM = 123.7


def _peak_hp(curve):
    rpm = np.asarray(curve.rpm, dtype=float)
    tq = np.asarray(curve.torque_nm, dtype=float)
    return float((tq * rpm * 2 * np.pi / 60 / 745.7).max())


def _h2():
    hits = [
        s
        for s in ALL_KNOWN_BIKES
        if s.manufacturer == "Kawasaki" and s.model_name == "Ninja H2"
    ]
    assert len(hits) == 1
    return hits[0]


def test_h2_library_curve_removed():
    assert get_dyno_curve("Kawasaki", "Ninja H2", 2015) is None
    assert not any(k[1] == "ninja h2" for k in KNOWN_DYNO_CURVES)


def test_h2_spec_carries_the_2015_rating():
    s = _h2()
    assert s.year_from == 2015
    assert s.peak_power_hp == pytest.approx(H2_RATED_HP)
    assert s.peak_torque_nm == pytest.approx(H2_RATED_NM)


def test_h2_engine_curve_within_published_bounds():
    """The H2 the sim sees is no longer the 243 Nm table: its curve's peak
    torque and power sit near the rated crank figures (whatever crank
    recalibration the synthetic path applies), and the implied wheel power
    is within reach of Cycle World's measured 189.8 hp."""
    cfg = spec_to_bike_config(_h2())
    dc = cfg.engine.dyno_curve
    assert max(dc.torque_nm) <= 1.25 * H2_RATED_NM  # was 243 Nm = 1.82x
    pk = _peak_hp(dc)
    assert 0.85 * H2_RATED_HP <= pk <= 1.25 * H2_RATED_HP
    wheel = pk * (1.0 if dc.is_at_wheel else cfg.drivetrain.drivetrain_efficiency())
    assert wheel <= 1.30 * H2_CW_WHEEL_HP  # was 294.9 whp = 1.55x


def test_no_accepted_library_curve_implies_more_than_110pct_of_rating():
    for s in ALL_KNOWN_BIKES:
        lib = get_dyno_curve(s.manufacturer, s.model_name, s.year_from, s.model_code)
        if lib is None:
            continue
        cfg = spec_to_bike_config(s)
        used_library = cfg.engine.dyno_curve.is_at_wheel and len(
            cfg.engine.dyno_curve.rpm
        ) == len(lib.rpm)
        implied = _peak_hp(lib) / importer._CLEAN_CHAIN_ETA / s.peak_power_hp
        if used_library:
            assert implied <= importer._LIBRARY_CURVE_MAX_IMPLIED_RATIO, (
                s.model_name,
                s.year_from,
                implied,
            )
        else:
            assert implied > importer._LIBRARY_CURVE_MAX_IMPLIED_RATIO, (
                s.model_name,
                s.year_from,
                implied,
            )


@pytest.mark.parametrize(
    "model,year",
    [("Ninja ZX-10R", 2004), ("GSX-S1000", 2021), ("GSX-R 1000", 2003)],
)
def test_gate_rejects_documented_over_rated_curves(model, year):
    hits = [s for s in ALL_KNOWN_BIKES if s.model_name == model and s.year_from == year]
    assert len(hits) == 1
    s = hits[0]
    lib = get_dyno_curve(s.manufacturer, s.model_name, s.year_from, s.model_code)
    assert lib is not None
    assert not importer._library_curve_plausible(lib, s)
    dc = spec_to_bike_config(s).engine.dyno_curve
    assert dc.is_at_wheel is False  # synthetic crank curve took over
