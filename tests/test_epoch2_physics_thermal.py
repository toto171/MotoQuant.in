"""
test_epoch2_physics_thermal.py
==============================
2026-10 physics epoch, round 2: the tyre heat balance has a physical steady
state (submodels/tire.py, constants.py "TYRE HEAT BALANCE").

Round 1 put ALL the contact-patch slip heat into the tread and cooled it with
h = 10 + 0.5 v over a fixed 0.15 m2: a K5 top-speed run heated its tyre to
~410 C, a low-grip run to ~570 C, and the reversion penalty then collapsed
grip. Round 2: Blok heat partition (the road takes most of the flash heat),
McAdams forced convection over the tread band, and the rear tyre's share of
the rolling-resistance work as a heat source (energy conservation).
"""

from __future__ import annotations

import copy
import math

import numpy as np
import pytest

import motoquant
from motoquant.constants import (
    DEFAULT_TREAD_WIDTH_M,
    ROAD_THERMAL_EFFUSIVITY,
    TREAD_RUBBER_DENSITY_KGM3,
)
from motoquant.defaults import gsxr1000_k5
from motoquant.submodels.tire import tread_heat_partition, tread_section_width_m


def test_heat_partition_is_the_blok_effusivity_share():
    e_t = math.sqrt(0.2 * TREAD_RUBBER_DENSITY_KGM3 * 1500.0)
    beta = tread_heat_partition(0.2, 1500.0)
    assert beta == pytest.approx(e_t / (e_t + ROAD_THERMAL_EFFUSIVITY))
    assert 0.2 < beta < 0.35  # most of the flash heat goes into the road
    assert tread_heat_partition(0.4, 1500.0) > beta  # better-conducting tread


@pytest.mark.parametrize(
    "size,width",
    (
        ("190/50-17", 0.190),
        ("180/55ZR17", 0.180),
        ("100/80-17", 0.100),
        ("4.00-18", 4.00 * 0.0254),
        ("3.50-18", 3.50 * 0.0254),
        ("slick", DEFAULT_TREAD_WIDTH_M),
        (None, DEFAULT_TREAD_WIDTH_M),
    ),
)
def test_section_width_parser(size, width):
    assert tread_section_width_m(size) == pytest.approx(width)


def test_convection_follows_mcadams_and_the_tread_band_area():
    eng = motoquant.MotoQuantEngine(gsxr1000_k5())
    tm = eng._tire
    assert tm.conv_area_m2 == pytest.approx(2 * math.pi * 0.302 * 0.190)
    tp = tm.cfg.tires
    T, Ta = 90.0, 25.0
    T_road = eng.cfg.environment.track_temp_c
    for v, h in (
        (0.0, 5.7),
        (0.5, 5.7),
        (2.0, 7.2 * 2**0.78),
        (30.0, 7.2 * 30**0.78),
        (80.0, 7.2 * 80**0.78),
    ):
        q = (
            -tm.thermal_rate(0.0, v, 0.0, T, Ta)
            * tp.tread_mass_kg
            * tp.specific_heat_rubber
        )
        q_cond = (
            tp.thermal_conductivity * tp.contact_patch_cm2 * 1e-4 * (T - T_road) / 0.005
        )
        assert q - q_cond == pytest.approx(h * tm.conv_area_m2 * (T - Ta), rel=1e-9)
    # continuous and monotone in speed
    hs = [max(5.7, 7.2 * v**0.78) for v in np.linspace(0.0, 90.0, 9001)]
    assert np.all(np.diff(hs) >= 0.0) and max(np.diff(hs)) < 0.1


def test_rolling_loss_heat_enters_the_heat_balance():
    tm = motoquant.MotoQuantEngine(gsxr1000_k5())._tire
    base = tm.thermal_rate(1500.0, 50.0, 0.03, 70.0, 25.0)
    more = tm.thermal_rate(1500.0, 50.0, 0.03, 70.0, 25.0, Q_rolling=1500.0)
    assert more - base == pytest.approx(1500.0 / (1.0 * 1500.0), rel=1e-12)
    # slip heat enters at the partition share
    hot = tm.thermal_rate(3000.0, 50.0, 0.03, 70.0, 25.0)
    assert hot - base == pytest.approx(
        tm.heat_partition * 1500.0 * 50.0 * 0.03 / 1500.0, rel=1e-9
    )


@pytest.mark.parametrize("mu_scale", (1.0, 0.75), ids=("stock", "low_grip"))
def test_no_thermal_runaway_holding_top_speed(mu_scale):
    """A long full-throttle run at ~300 km/h (traction-limited too, on low
    grip): the tread settles to a steady state near 100 C — rolling loss and
    slip heat balanced by convection — instead of the round-1 410-570 C."""
    cfg = gsxr1000_k5()
    cfg.tires.mu_peak *= mu_scale
    ts = motoquant.MotoQuantEngine(cfg).run_top_speed(max_time=90.0)
    s = ts.full_sim
    T = s.T_tire
    assert T.max() < 120.0, T.max()
    # plateau: < 1.5 K over the last 20 s (time constant ~20 s at 300 km/h)
    late = s.t >= s.t[-1] - 20.0
    assert T[late][-1] - T[late][0] < 1.5


def test_quarter_mile_temperature_change_is_tens_of_degrees_at_most():
    for factory in (gsxr1000_k5,):
        r = motoquant.MotoQuantEngine(copy.deepcopy(factory())).run()
        assert np.ptp(r.T_tire) < 30.0
