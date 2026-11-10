"""2026-10 epoch, ROUND 3 retune — the shipped CategoryProfile knob values,
their physical bounds, the selection gate and production-path liveness.

Selected by scripts/tune_epoch3_2026_11_03.py (from NEUTRAL over
mu_peak_scale 0.97-1.10 x wheelie_margin 0.65-1.00, launch_rpm_factor only in
the 'margin+lr' family under the 1-SE rule or in the gate escape; joint
ET + 0.01 x trap objective, per-row timing, grouped 5-fold CV, 1-SE rule;
selection gate = HARD dry-mass monotonicity + rider-mass / sea-level probes
below 10 ms) and recorded in reports/acc_epoch3_2026_11_03.json
(tests/test_epoch3_tune_report.py pins report == code). Changing any value is
a deliberate recalibration: re-run the tune, regenerate the report, update
``ROUND3_KNOBS`` here.
"""

from __future__ import annotations

import copy
import dataclasses

import pytest

from motoquant import category_profiles as cp
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8
from motoquant.engine_select import make_engine
from motoquant.scraper.importer import spec_to_bike_config
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

_NEUTRAL = {
    "over_clutch_factor": 0.0,
    "max_engine_decel_rads2": 0.0,
    "launch_floor_factor": 0.0,
    "mu_peak_override": None,
    "mu_peak_scale": 1.0,
    "parasitic_mult": 1.0,
    "launch_rpm_factor": None,
    "cd_floor": 0.25,
    "wheelie_margin": 1.0,
}

#: tag -> the knobs that differ from _NEUTRAL.
ROUND3_KNOBS = {
    # OWNER DECISION 2026-11-05: the CV choice 'alt_litre195_margin' (margin
    # 0.69 at rated rubber, launch_rpm_factor retired) ships instead of the
    # tuner's gate escape (grip 1.05 / margin 0.97 / clutch dump 0.475 x
    # redline), which cleared ms-level dry-mass inversions on two bikes at
    # the price of re-introducing per-bike launch-rpm scatter. Accepted
    # residuals: HP4 Race -10 kg 9.8 ms slower, Panigale V4R 2.5 ms (see
    # test_litre195_accepted_mass_inversions_stay_small).
    cp.CATEGORY_LITRE_SPORT_195P: {"wheelie_margin": 0.69},
    cp.CATEGORY_LITRE_SPORT_600_1000: {"wheelie_margin": 0.72},
    # gate-constrained 'margin+lr'
    cp.CATEGORY_SPORT_TWIN_600_1300: {
        "launch_rpm_factor": 0.50,
        "wheelie_margin": 0.75,
    },
    # gate-constrained (rider-mass probe) margin
    cp.CATEGORY_OTHER: {"wheelie_margin": 0.66},
    cp.CATEGORY_TWO_STROKE: {"wheelie_margin": 0.66},
    cp.CATEGORY_REFERENCE_LITRE_195P: {"wheelie_margin": 0.72},
    cp.CATEGORY_CRUISER_1300P: {},
    cp.CATEGORY_MID_TWIN_500_700: {},
    cp.CATEGORY_SMALL_I4_SCREAMER: {},
    cp.CATEGORY_SINGLE_300_500: {},
    cp.CATEGORY_MID_TWIN_300_500: {},
    cp.CATEGORY_ENTRY_200_300: {},
    cp.CATEGORY_ENTRY_150_200: {},
    cp.CATEGORY_UNKNOWN: {},
}

MU_BOUNDS = (0.97, 1.10)
WM_BOUNDS = (0.65, 1.00)
LR_BOUNDS = (0.45, 0.75)


@pytest.mark.parametrize("tag", sorted(ROUND3_KNOBS))
def test_round3_knob_values(tag):
    prof = cp.get_profile(tag)
    assert prof.name == tag
    want = {**_NEUTRAL, **ROUND3_KNOBS[tag]}
    assert {k: getattr(prof, k) for k in want} == want, tag


def test_every_registered_profile_is_pinned():
    assert set(cp._PROFILES) == set(ROUND3_KNOBS)


@pytest.mark.parametrize("tag", sorted(ROUND3_KNOBS))
def test_knobs_inside_the_round3_bounds(tag):
    p = cp.get_profile(tag)
    assert MU_BOUNDS[0] <= p.mu_peak_scale <= MU_BOUNDS[1]
    assert WM_BOUNDS[0] <= p.wheelie_margin <= WM_BOUNDS[1]
    assert p.launch_rpm_factor is None or (
        LR_BOUNDS[0] <= p.launch_rpm_factor <= LR_BOUNDS[1]
    )
    assert p.mu_peak_override is None
    assert p.over_clutch_factor == 0.0 and p.max_engine_decel_rads2 == 0.0
    assert p.launch_floor_factor == 0.0 and p.parasitic_mult == 1.0


def test_two_stroke_launches_on_its_pipe():
    assert cp.get_profile(cp.CATEGORY_TWO_STROKE).launch_rpm_factor is None


# ── production-path liveness of the armed margin ────────────────────────────


def _spec(mfr, model, year=None):
    hits = [
        s
        for s in ALL_KNOWN_BIKES
        if s.manufacturer == mfr
        and s.model_name == model
        and (year is None or s.year_from == year)
    ]
    assert hits, (mfr, model, year)
    return hits[0]


def _et(cfg):
    return float(make_engine(cfg).run(max_time=26.0).time_quarter)


def _swap(tag, **knobs):
    saved = cp._PROFILES[tag]
    cp._PROFILES[tag] = dataclasses.replace(saved, **knobs)
    return saved


@pytest.mark.parametrize(
    "tag,mfr,model,year,min_gain",
    [
        # margin 0.72 costs a 600-1000 supersport launch well over 0.1 s
        (cp.CATEGORY_LITRE_SPORT_600_1000, "Yamaha", "YZF-R6", 2017, 0.10),
        (cp.CATEGORY_OTHER, "Kawasaki", "Ninja H2 SX SE+", None, 0.10),
    ],
)
def test_wheelie_margin_is_live_on_the_catalog_path(tag, mfr, model, year, min_gain):
    cfg = spec_to_bike_config(_spec(mfr, model, year))
    if cfg.category_tag != tag:
        pytest.skip(f"{model} routes to {cfg.category_tag}")
    armed = _et(cfg)
    saved = _swap(tag, wheelie_margin=1.0)
    try:
        unarmed = _et(cfg)
    finally:
        cp._PROFILES[tag] = saved
    assert armed - unarmed > min_gain


def test_reference_margin_is_live():
    armed = _et(gsxr1000_k5())
    saved = _swap(cp.CATEGORY_REFERENCE_LITRE_195P, wheelie_margin=1.0)
    try:
        unarmed = _et(gsxr1000_k5())
    finally:
        cp._PROFILES[cp.CATEGORY_REFERENCE_LITRE_195P] = saved
    assert armed - unarmed > 0.3


# ── references: in band, monotone in every probe ───────────────────────────


@pytest.mark.parametrize(
    "fn,lo,hi",
    [
        (gsxr1000_k5, 9.87, 10.07),
        (yzfr1_4c8, 10.10, 10.50),
        (hayabusa_gen1, 10.10, 10.70),
    ],
)
def test_references_in_their_published_bands(fn, lo, hi):
    assert lo <= _et(fn()) <= hi


@pytest.mark.parametrize("fn", [gsxr1000_k5, yzfr1_4c8, hayabusa_gen1])
@pytest.mark.parametrize("field", ["dry_mass_kg", "rider_mass_kg"])
@pytest.mark.parametrize("sea_level", [False, True])
def test_references_mass_monotone_every_probe(fn, field, sea_level):
    base = fn()
    if sea_level:
        base.environment.altitude_m = 0.0
        base.environment.ambient_temp_c = 15.0
    ets = []
    for dm in (-10.0, 0.0, 10.0):
        c = copy.deepcopy(base)
        setattr(c.chassis, field, getattr(c.chassis, field) + dm)
        ets.append(_et(c))
    assert ets[0] < ets[1] < ets[2], ets


@pytest.mark.parametrize(
    "mfr,model,year",
    [
        pytest.param(
            "BMW",
            "HP4 Race",
            None,
            marks=pytest.mark.xfail(
                strict=True,
                reason=(
                    "accepted residual of the owner-chosen litre_sport_195p "
                    "margin 0.69 (2026-11-05): -10 kg is ~9.8 ms SLOWER "
                    "(2nd-gear wheelie limit; lower system CoG of the "
                    "heavier bike raises its ceiling). Bounded by "
                    "test_litre195_accepted_mass_inversions_stay_small."
                ),
            ),
        ),
        ("Ducati", "1199 Panigale", None),
        ("Kawasaki", "Ninja H2 SX SE+", None),
        ("KTM", "1290 Super Adventure R", None),
        ("Yamaha", "YZF-R6", 2017),
    ],
)
def test_gate_bikes_dry_mass_monotone(mfr, model, year):
    """Zero tolerance at the default environment: ET(-10) <= ET(0) <= ET(+10)."""
    cfg = spec_to_bike_config(_spec(mfr, model, year))
    ets = []
    for dm in (-10.0, 0.0, 10.0):
        c = copy.deepcopy(cfg)
        c.chassis.dry_mass_kg += dm
        ets.append(_et(c))
    assert ets[0] <= ets[1] <= ets[2], ets


@pytest.mark.parametrize(
    "mfr,model",
    [("Kawasaki", "Ninja H2 SX SE+"), ("KTM", "1290 Super Adventure R")],
)
def test_other_cluster_rider_mass_no_large_inversion(mfr, model):
    """The rider-mass probe picked 'other's margin: no inversion >= 10 ms."""
    cfg = spec_to_bike_config(_spec(mfr, model))
    ets = []
    for dm in (-10.0, 0.0, 10.0):
        c = copy.deepcopy(cfg)
        c.chassis.rider_mass_kg += dm
        ets.append(_et(c))
    assert ets[1] - ets[2] < 0.010 and ets[0] - ets[1] < 0.010, ets


@pytest.mark.parametrize(
    "mfr,model,bound_s",
    [("BMW", "HP4 Race", 0.012), ("Ducati", "Panigale V4R", 0.004)],
)
def test_litre195_accepted_mass_inversions_stay_small(mfr, model, bound_s):
    """The two dry-mass inversions accepted with the owner's litre_sport_195p
    choice must not grow. Measured 2026-11-05 at the default environment:
    HP4 Race -10 kg 9.8 ms slower (+10 kg monotone, +1.5 ms); Panigale V4R
    -10 kg 2.5 ms slower AND +10 kg 1.0 ms quicker (inverted on both steps).
    Every step's inversion stays below the bound."""
    cfg = spec_to_bike_config(_spec(mfr, model))
    if cfg.category_tag != cp.CATEGORY_LITRE_SPORT_195P:
        pytest.skip(f"{model} routes to {cfg.category_tag}")
    ets = []
    for dm in (-10.0, 0.0, 10.0):
        c = copy.deepcopy(cfg)
        c.chassis.dry_mass_kg += dm
        ets.append(_et(c))
    assert max(ets[0] - ets[1], ets[1] - ets[2]) < bound_s, ets
