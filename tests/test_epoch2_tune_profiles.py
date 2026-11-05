"""2026-10 epoch, ROUND 2 — the 599 cc supersport routing fix, the physical
bounds, the mass-monotonicity gate and the litre traction audit, checked on
the SHIPPED profiles.

Round 2's knob VALUES were superseded by round 3 (reports/acc_epoch3_2026_11_03.json,
scripts/tune_epoch3_2026_11_03.py); the knob pins, their liveness checks and
round 3's bounds live in tests/test_epoch3_tune_profiles.py. What stays here
is everything round 2 established that must still hold: the routing, and the
HARD dry-mass gate (zero inversions, zero tolerance) on the bikes that were
mass-inverted under neutral knobs.
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


# ── helpers ─────────────────────────────────────────────────────────────────


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
        # the two bikes that are mass-inverted under NEUTRAL knobs (2nd-gear
        # wheelie threshold / traction). Round 3 selected sport_twin_600_1300
        # over the gate-feasible points, so the 1199 Panigale is monotone.
        # For litre_sport_195p the OWNER DECISION of 2026-11-05 shipped the
        # CV choice (wheelie_margin 0.69, 'alt_litre195_margin') over the
        # gate escape, ACCEPTING the HP4 Race inversion (-10 kg 9.8 ms
        # slower; it inverts at neutral too) — bounded, not hidden, by
        # tests/test_epoch3_tune_profiles.py::
        # test_litre195_accepted_mass_inversions_stay_small.
        pytest.param(
            "BMW",
            "HP4 Race",
            None,
            marks=pytest.mark.xfail(
                strict=True,
                reason="accepted residual of the owner-chosen litre_sport_195p "
                "knobs (2026-11-05): -10 kg 9.8 ms slower",
            ),
        ),
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
    reports no inversions with the shipped knobs EXCEPT the two accepted with
    the owner's litre_sport_195p choice of 2026-11-05 (HP4 Race 9.8 ms,
    Panigale V4R 2.5 ms; reports/acc_epoch3_2026_11_03.json
    tuning.clusters.litre_sport_195p.owner_decision)."""
    mono = _mono()
    rows = mono.probe_catalog(
        neutral=False, workers=1, with_fractions=False, probes=("dry",)
    )
    summ = mono.summarize_catalog(rows)
    assert summ["errors"] == 0
    inverted = {r["name"] for r in rows if r.get("inversions")}
    assert inverted == {"BMW HP4 Race", "Ducati Panigale V4R"}, inverted
    assert summ["inversions"] == 2


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
