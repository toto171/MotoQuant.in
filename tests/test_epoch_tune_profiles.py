"""2026-10 epoch retune — CategoryProfile knob values, taxonomy routing of the
big singles, thin-cluster donors and production-path liveness.

The values were selected by scripts/tune_epoch_2026_10_24.py (joint
ET + 0.01 x trap objective, grouped 5-fold CV, one-standard-error rule toward
the simplest knob set) and are recorded in reports/acc_epoch_2026_10_24.json.
Changing any of them is a deliberate recalibration: re-run the tune, update
the report, and update ``EPOCH_KNOBS`` here.
"""

from __future__ import annotations

import pytest

from motoquant import category_profiles as cp
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
}

#: tag -> the knobs that differ from _NEUTRAL (everything else neutral).
EPOCH_KNOBS = {
    cp.CATEGORY_LITRE_SPORT_195P: {"mu_peak_scale": 0.94, "launch_rpm_factor": 0.80},
    cp.CATEGORY_LITRE_SPORT_600_1000: {"mu_peak_scale": 0.93},
    cp.CATEGORY_SPORT_TWIN_600_1300: {"mu_peak_scale": 0.91},
    cp.CATEGORY_MID_TWIN_500_700: {"mu_peak_override": 1.26},
    cp.CATEGORY_SMALL_I4_SCREAMER: {},
    cp.CATEGORY_SINGLE_300_500: {},
    cp.CATEGORY_MID_TWIN_300_500: {},
    cp.CATEGORY_ENTRY_200_300: {},
    cp.CATEGORY_ENTRY_150_200: {},
    cp.CATEGORY_TWO_STROKE: {},
    cp.CATEGORY_CRUISER_1300P: {},
    cp.CATEGORY_OTHER: {},
    cp.CATEGORY_REFERENCE_LITRE_195P: {"mu_peak_scale": 0.906},
    cp.CATEGORY_UNKNOWN: {},  # back-compat anchor, untouched
}


@pytest.mark.parametrize("tag", sorted(EPOCH_KNOBS))
def test_epoch_knob_values(tag):
    prof = cp.get_profile(tag)
    assert prof.name == tag
    want = {**_NEUTRAL, **EPOCH_KNOBS[tag]}
    got = {k: getattr(prof, k) for k in want}
    assert got == want, tag


def test_every_registered_profile_is_pinned():
    assert set(cp._PROFILES) == set(EPOCH_KNOBS)


def test_cd_floor_stays_a_no_op_guard():
    for tag, prof in cp._PROFILES.items():
        assert prof.cd_floor == 0.25, tag


def test_thin_cluster_shares_its_donor_knobs():
    """cruiser_1300p is too thin to fit (n=4 benchmark rows): it carries the
    selected knobs of its documented donor 'other'."""
    knobs = (
        "over_clutch_factor",
        "max_engine_decel_rads2",
        "launch_floor_factor",
        "mu_peak_override",
        "mu_peak_scale",
        "parasitic_mult",
        "launch_rpm_factor",
    )
    a = cp.get_profile(cp.CATEGORY_CRUISER_1300P)
    b = cp.get_profile(cp.CATEGORY_OTHER)
    assert {k: getattr(a, k) for k in knobs} == {k: getattr(b, k) for k in knobs}


# ── taxonomy: 4T singles >= 300 cc route to the singles profile ─────────────

_BIG_SINGLES = [
    ("KTM", "690 Duke R", 690.0, 75.0, "naked"),
    ("Husqvarna", "701 Supermoto", 692.7, 74.0, "naked"),
    ("Husqvarna", "Vitpilen 701", 693.0, 75.0, "naked"),
    ("Kawasaki", "KLR 650 (2022-2024)", 651.0, 40.0, "adventure"),
]


@pytest.mark.parametrize("mfr,model,cc,hp,cat", _BIG_SINGLES)
def test_big_singles_route_to_singles_profile(mfr, model, cc, hp, cat):
    kw = {
        "manufacturer": mfr,
        "model_name": model,
        "displacement_cc": cc,
        "peak_power_hp": hp,
        "stroke_type": 4,
        "category": cat,
    }
    assert cp.derive_category_tag(**kw, cylinders=1) == cp.CATEGORY_SINGLE_300_500
    # cylinders=None reproduces the July-3 taxonomy exactly (no cylinder
    # branch can fire): 600-1100 cc sport/naked -> litre_sport_600_1000,
    # 500-700 cc anything else -> mid_twin_500_700.
    legacy = cp.derive_category_tag(**kw, cylinders=None)
    expect = (
        cp.CATEGORY_LITRE_SPORT_600_1000
        if cat in ("sport", "naked") and 600 <= cc < 1100
        else cp.CATEGORY_MID_TWIN_500_700
    )
    assert legacy == expect


def test_two_stroke_singles_stay_two_stroke():
    tag = cp.derive_category_tag(
        manufacturer="Honda",
        model_name="CR500R",
        displacement_cc=491,
        peak_power_hp=60,
        stroke_type=2,
        category="sport",
        cylinders=1,
    )
    assert tag == cp.CATEGORY_TWO_STROKE


def test_catalog_big_singles_carry_the_singles_tag():
    big = [
        s
        for s in ALL_KNOWN_BIKES
        if s.cylinders == 1
        and (s.stroke_type or 4) != 2
        and s.displacement_cc
        and s.displacement_cc >= 500
    ]
    assert len(big) >= 5
    for s in big:
        assert spec_to_bike_config(s).category_tag == cp.CATEGORY_SINGLE_300_500, (
            s.model_name
        )


def test_reference_tag_is_never_derived():
    for s in ALL_KNOWN_BIKES:
        assert spec_to_bike_config(s).category_tag != cp.CATEGORY_REFERENCE_LITRE_195P


# ── production-path liveness of the armed knobs ─────────────────────────────


def _spec(mfr, model):
    hits = [
        s
        for s in ALL_KNOWN_BIKES
        if s.manufacturer == mfr and s.model_name.startswith(model)
    ]
    assert hits, (mfr, model)
    return hits[0]


def _run(cfg):
    return make_engine(cfg).run(max_time=26.0).time_quarter


def _swap(tag, **knobs):
    prof = cp._PROFILES[tag]
    saved = {k: getattr(prof, k) for k in knobs}
    for k, v in knobs.items():
        setattr(prof, k, v)
    return prof, saved


def _restore(prof, saved):
    for k, v in saved.items():
        setattr(prof, k, v)


def test_litre_launch_rpm_factor_is_live_on_the_catalog_path():
    """The 0.80 launch rpm moves a V4 whose rated peak-torque rpm sits low in
    its rev range (Streetfighter V4: 8750 / 14025) by ~0.19 s."""
    cfg = spec_to_bike_config(_spec("Ducati", "Streetfighter V4"))
    assert cfg.category_tag == cp.CATEGORY_LITRE_SPORT_195P
    armed = _run(cfg)
    prof, saved = _swap(cp.CATEGORY_LITRE_SPORT_195P, launch_rpm_factor=None)
    try:
        unarmed = _run(cfg)
    finally:
        _restore(prof, saved)
    assert unarmed - armed > 0.10


def test_mid_twin_rubber_override_is_live_on_the_catalog_path():
    """The 1.26 class grip speeds up the ADV twin (rated 1.15) by > 0.1 s."""
    cfg = spec_to_bike_config(_spec("Suzuki", "V-Strom 650"))
    assert cfg.category_tag == cp.CATEGORY_MID_TWIN_500_700
    armed = _run(cfg)
    prof, saved = _swap(cp.CATEGORY_MID_TWIN_500_700, mu_peak_override=None)
    try:
        unarmed = _run(cfg)
    finally:
        _restore(prof, saved)
    assert unarmed - armed > 0.10


@pytest.mark.parametrize(
    "tag,mfr,model",
    [
        (cp.CATEGORY_LITRE_SPORT_600_1000, "Honda", "CBR1000RR"),
        (cp.CATEGORY_SPORT_TWIN_600_1300, "Ducati", "1199 Panigale"),
    ],
)
def test_grip_scale_is_live_on_the_catalog_path(tag, mfr, model):
    cfg = spec_to_bike_config(_spec(mfr, model))
    assert cfg.category_tag == tag
    armed = _run(cfg)
    prof, saved = _swap(tag, mu_peak_scale=1.0)
    try:
        rated = _run(cfg)
    finally:
        _restore(prof, saved)
    # less launch grip -> slower; the epoch scale is worth > 0.1 s here
    assert armed - rated > 0.10
