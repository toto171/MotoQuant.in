"""2026-10 epoch retune (round 1) — taxonomy routing of the big singles and the
frozen reference tag.

ROUND 1's knob values (reports/acc_epoch_2026_10_24.json) were REJECTED and
re-selected in round 2 (scripts/tune_epoch2_2026_10_29.py,
reports/acc_epoch2_2026_10_29.json); the knob-value, thin-cluster and
liveness pins now live in tests/test_epoch2_tune_profiles.py. What stays
here is the part of round 1 that round 2 kept: every 4T single >= 300 cc
routes to single_300_500, and the reference tag is never derived.
"""

from __future__ import annotations

import pytest

from motoquant import category_profiles as cp
from motoquant.scraper.importer import spec_to_bike_config
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES


def test_cd_floor_stays_a_no_op_guard():
    for tag, prof in cp._PROFILES.items():
        assert prof.cd_floor == 0.25, tag


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
