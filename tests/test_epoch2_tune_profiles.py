"""2026-10 epoch, ROUND 2 retune — CategoryProfile knob values, the 599 cc
supersport routing fix, physical bounds, the mass-monotonicity gate and
production-path liveness.

The values were selected by scripts/tune_epoch2_2026_10_29.py (joint
ET + 0.01 x trap objective, per-row timing convention, grouped 5-fold CV,
one-standard-error rule toward neutral, HARD mass-monotonicity gate) and are
recorded in reports/acc_epoch2_2026_10_29.json. Changing any of them is a
deliberate recalibration: re-run the tune, regenerate the report, and update
``ROUND2_KNOBS`` here (tests/test_epoch2_tune_report.py pins report == code).
"""

from __future__ import annotations

import copy
import importlib.util
import os
from pathlib import Path

import pytest

from motoquant import category_profiles as cp, engine_select
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8
from motoquant.engine_select import make_engine
from motoquant.scraper.importer import spec_to_bike_config
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

ROOT = Path(__file__).resolve().parent.parent

_NEUTRAL = {
    "over_clutch_factor": 0.0,
    "max_engine_decel_rads2": 0.0,
    "launch_floor_factor": 0.0,
    "mu_peak_override": None,
    "mu_peak_scale": 1.0,
    "parasitic_mult": 1.0,
    "launch_rpm_factor": None,
    "cd_floor": 0.25,
}

#: tag -> the knobs that differ from _NEUTRAL (everything else neutral).
ROUND2_KNOBS = {
    cp.CATEGORY_LITRE_SPORT_195P: {"mu_peak_scale": 1.05, "launch_rpm_factor": 0.475},
    cp.CATEGORY_LITRE_SPORT_600_1000: {
        "mu_peak_scale": 0.95,
        "launch_rpm_factor": 0.50,
    },
    cp.CATEGORY_SPORT_TWIN_600_1300: {
        "mu_peak_scale": 0.95,
        "launch_rpm_factor": 0.475,
    },
    cp.CATEGORY_OTHER: {"mu_peak_scale": 0.95},
    cp.CATEGORY_CRUISER_1300P: {},  # thin; donor "other" rejected (worse)
    cp.CATEGORY_MID_TWIN_500_700: {},  # thin after the routing fix: neutral
    cp.CATEGORY_SMALL_I4_SCREAMER: {},
    cp.CATEGORY_SINGLE_300_500: {},
    cp.CATEGORY_MID_TWIN_300_500: {},
    cp.CATEGORY_ENTRY_200_300: {},
    cp.CATEGORY_ENTRY_150_200: {},
    cp.CATEGORY_TWO_STROKE: {},
    cp.CATEGORY_REFERENCE_LITRE_195P: {
        "mu_peak_scale": 0.95,
        "launch_rpm_factor": 0.45,
    },
    cp.CATEGORY_UNKNOWN: {},  # back-compat anchor, untouched
}

#: The physical search bounds of the round-2 retune.
MU_BOUNDS = (0.95, 1.15)
LR_BOUNDS = (0.45, 0.75)


@pytest.mark.parametrize("tag", sorted(ROUND2_KNOBS))
def test_round2_knob_values(tag):
    prof = cp.get_profile(tag)
    assert prof.name == tag
    want = {**_NEUTRAL, **ROUND2_KNOBS[tag]}
    got = {k: getattr(prof, k) for k in want}
    assert got == want, tag


def test_every_registered_profile_is_pinned():
    assert set(cp._PROFILES) == set(ROUND2_KNOBS)


@pytest.mark.parametrize("tag", sorted(ROUND2_KNOBS))
def test_knobs_inside_the_physical_bounds(tag):
    """Grip within -5/+15 % of rated rubber; launch rpm None or 0.45-0.75 x
    redline; no class rubber override and no over-clutch / launch-floor /
    parasitic fudge anywhere (none is live in round 2)."""
    p = cp.get_profile(tag)
    assert MU_BOUNDS[0] <= p.mu_peak_scale <= MU_BOUNDS[1]
    assert p.launch_rpm_factor is None or (
        LR_BOUNDS[0] <= p.launch_rpm_factor <= LR_BOUNDS[1]
    )
    assert p.mu_peak_override is None
    assert p.over_clutch_factor == 0.0 and p.max_engine_decel_rads2 == 0.0
    assert p.launch_floor_factor == 0.0
    assert p.parasitic_mult == 1.0
    assert p.cd_floor == 0.25


def test_two_stroke_launches_on_its_pipe():
    assert cp.get_profile(cp.CATEGORY_TWO_STROKE).launch_rpm_factor is None


def test_thin_clusters_run_neutral():
    """cruiser_1300p (n=4), mid_twin_500_700 (n=7 after the routing fix) and
    small_i4_screamer (n=2) are too thin to fit. The cruiser's pre-registered
    donor ('other', grip 0.95) was rejected because it makes the cruiser rows
    worse than neutral (report tuning record 'donor_rejected')."""
    for tag in (
        cp.CATEGORY_CRUISER_1300P,
        cp.CATEGORY_MID_TWIN_500_700,
        cp.CATEGORY_SMALL_I4_SCREAMER,
    ):
        p = cp.get_profile(tag)
        assert {k: getattr(p, k) for k in _NEUTRAL} == _NEUTRAL, tag


# ── routing: the 599 cc supersports leave mid_twin_500_700 ──────────────────

_SUPERSPORTS = [
    ("Yamaha", "YZF-R6", 599, 118, "sport", 4),
    ("Suzuki", "GSX-R 600", 599, 125, "sport", 4),
    ("Honda", "CBR 600RR", 599, 118, "sport", 4),
    ("Kawasaki", "Ninja ZX-6R", 599, 123, "sport", 4),
    ("Honda", "CB600F Hornet", 599, 100, "naked", 4),
    ("Triumph", "Daytona 600", 599, 110, "sport", 3),
]


@pytest.mark.parametrize("mfr,model,cc,hp,cat,cyl", _SUPERSPORTS)
def test_599cc_supersports_route_with_the_600_class(mfr, model, cc, hp, cat, cyl):
    kw = {
        "manufacturer": mfr,
        "model_name": model,
        "displacement_cc": cc,
        "peak_power_hp": hp,
        "stroke_type": 4,
        "category": cat,
    }
    assert (
        cp.derive_category_tag(**kw, cylinders=cyl) == cp.CATEGORY_LITRE_SPORT_600_1000
    )
    # cylinders=None (old saved configs) reproduces the previous taxonomy
    assert cp.derive_category_tag(**kw, cylinders=None) == cp.CATEGORY_MID_TWIN_500_700


@pytest.mark.parametrize(
    "model,cc,cat,cyl",
    [
        ("Tiger Sport 660", 660, "touring", 3),
        ("703F", 699, "adventure", 3),
        ("LFC 700", 676, "cruiser", 4),
        ("Vulcan S", 649, "cruiser", 2),
        ("Leoncino 500", 500, "naked", 2),
    ],
)
def test_non_sport_multis_and_twins_keep_their_routing(model, cc, cat, cyl):
    tag = cp.derive_category_tag(
        manufacturer="X",
        model_name=model,
        displacement_cc=cc,
        peak_power_hp=80,
        stroke_type=4,
        category=cat,
        cylinders=cyl,
    )
    assert tag == cp.CATEGORY_MID_TWIN_500_700


def test_catalog_membership_change_is_exactly_the_599_supersports():
    """Every catalog bike whose tag the round-2 routing branch can change is a
    500-599 cc inline-3/4 sport/naked bike, and all eleven of them now carry
    the litre_sport_600_1000 tag on the production spec path."""
    moved = []
    for s in ALL_KNOWN_BIKES:
        kw = {
            "manufacturer": s.manufacturer,
            "model_name": s.model_name,
            "displacement_cc": s.displacement_cc,
            "peak_power_hp": s.peak_power_hp,
            "stroke_type": s.stroke_type or 4,
            "category": s.category,
        }
        cyl_tag = cp.derive_category_tag(**kw, cylinders=s.cylinders)
        if (
            s.cylinders
            and s.cylinders >= 3
            and s.displacement_cc
            and 500 <= s.displacement_cc < 600
            and (s.category or "sport").lower() in ("sport", "naked")
            and (s.stroke_type or 4) != 2
        ):
            moved.append(s)
            assert cyl_tag == cp.CATEGORY_LITRE_SPORT_600_1000, s.model_name
            assert spec_to_bike_config(s).category_tag == cyl_tag
    assert len(moved) == 11
    assert {s.manufacturer for s in moved} == {"Honda", "Kawasaki", "Suzuki", "Yamaha"}


# ── production-path liveness of the armed knobs ─────────────────────────────


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
    return make_engine(cfg).run(max_time=26.0).time_quarter


def _with(tag, **knobs):
    prof = cp._PROFILES[tag]
    saved = {k: getattr(prof, k) for k in knobs}
    for k, v in knobs.items():
        setattr(prof, k, v)
    return prof, saved


def _restore(prof, saved):
    for k, v in saved.items():
        setattr(prof, k, v)


@pytest.mark.parametrize(
    "tag,mfr,model,knob,neutral,min_gain",
    [
        # the 0.50 x redline clutch dump costs the CBR1000RR ~0.16 s
        (
            cp.CATEGORY_LITRE_SPORT_600_1000,
            "Honda",
            "CBR1000RR",
            "launch_rpm_factor",
            None,
            0.10,
        ),
        # ... and the 1199 Panigale ~0.24 s at 0.475
        (
            cp.CATEGORY_SPORT_TWIN_600_1300,
            "Ducati",
            "1199 Panigale",
            "launch_rpm_factor",
            None,
            0.15,
        ),
        # the heavy ADV bikes' 1st-gear launch is traction-limited: grip 0.95
        # costs the R 1250 GS ~0.25 s
        (cp.CATEGORY_OTHER, "BMW", "R 1250 GS", "mu_peak_scale", 1.0, 0.15),
    ],
)
def test_round2_knob_is_live_on_the_catalog_path(
    tag, mfr, model, knob, neutral, min_gain
):
    cfg = spec_to_bike_config(_spec(mfr, model))
    assert cfg.category_tag == tag
    armed = _et(cfg)
    prof, saved = _with(tag, **{knob: neutral})
    try:
        unarmed = _et(cfg)
    finally:
        _restore(prof, saved)
    assert armed - unarmed > min_gain  # the knob slows the bike


def test_reference_launch_rpm_is_live():
    armed = _et(gsxr1000_k5())
    prof, saved = _with(cp.CATEGORY_REFERENCE_LITRE_195P, launch_rpm_factor=None)
    try:
        unarmed = _et(gsxr1000_k5())
    finally:
        _restore(prof, saved)
    assert armed - unarmed > 0.2


# ── the HARD mass-monotonicity gate ─────────────────────────────────────────


def _mono():
    spec = importlib.util.spec_from_file_location(
        "_t_epoch2_mono", ROOT / "scripts" / "check_mass_monotonicity.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("fn", [gsxr1000_k5, yzfr1_4c8, hayabusa_gen1])
def test_references_mass_monotone(fn):
    base = fn()
    ets = []
    for dm in (-20.0, -10.0, 0.0, 10.0, 20.0):
        c = copy.deepcopy(base)
        c.chassis.dry_mass_kg += dm
        ets.append(_et(c))
    assert all(b > a for a, b in zip(ets, ets[1:])), ets


def _monotone(cfg):
    out = []
    for dm in (-10.0, 0.0, 10.0):
        c = copy.deepcopy(cfg)
        c.chassis.dry_mass_kg += dm
        out.append(_et(c))
    return out


@pytest.mark.parametrize(
    "mfr,model,year",
    [
        # the two bikes that were mass-inverted under NEUTRAL knobs (2nd-gear
        # wheelie threshold) — the selected knob sets make both monotone
        ("BMW", "HP4 Race", None),
        ("Ducati", "1199 Panigale", None),
        ("Honda", "CBR1000RR", None),
        ("Kawasaki", "Ninja ZX-10R", 2021),
        ("BMW", "R 1250 GS", None),
    ],
)
def test_selected_knobs_keep_bikes_mass_monotone(mfr, model, year):
    """Zero tolerance: ET(-10 kg) <= ET(0) <= ET(+10 kg)."""
    ets = _monotone(spec_to_bike_config(_spec(mfr, model, year)))
    assert ets[0] <= ets[1] <= ets[2], ets


@pytest.mark.skipif(
    not engine_select.native_active() and os.environ.get("MOTOQUANT_SLOW_TESTS") != "1",
    reason="full-catalog gate needs the Rust core (seconds) or MOTOQUANT_SLOW_TESTS=1",
)
def test_whole_catalog_mass_monotone():
    """scripts/check_mass_monotonicity.py's catalog probe (spec path, +-10 kg)
    reports ZERO inversions with the shipped knobs."""
    mono = _mono()
    rows = mono.probe_catalog(neutral=False, workers=1, with_fractions=False)
    summ = mono.summarize_catalog(rows)
    assert summ["errors"] == 0
    assert summ["inversions"] == 0, [r["name"] for r in rows if r.get("inversions")]


@pytest.mark.parametrize(
    "mfr,model,year",
    [
        ("BMW", "HP4 Race", None),
        ("Honda", "CBR1000RR", None),
        ("Kawasaki", "Ninja ZX-10R", 2021),
    ],
)
def test_litre_bikes_not_traction_limited_above_second_gear(mfr, model, year):
    mono = _mono()
    cfg = spec_to_bike_config(_spec(mfr, model, year))
    lim = mono.run_one(cfg, with_fractions=True)["limiters"]
    for g, v in lim.items():
        if g != "all" and int(g) >= 3:
            assert v["traction_frac"] == 0.0, (g, v)
