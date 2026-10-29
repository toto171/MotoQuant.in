"""2026-10 epoch, round 2 — corrected specs and benchmark rows.

Every value pinned here was changed from an unsourced / mislabelled figure to
a cited one (the citation is next to the value in the spec / corpus file);
see the round-2 data report. Production path: the specs go through
``spec_to_bike_config`` (what every sweep and the importer run) and the
benchmark rows through ``sweep_lib``'s classifiers.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motoquant.scraper.importer import spec_to_bike_config  # noqa: E402
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES  # noqa: E402
from motoquant.scraper.validator import validate_spec  # noqa: E402
from scripts import sweep_lib as SL  # noqa: E402
from scripts.validation_sweep import BENCHMARKS  # noqa: E402


def _spec(model):
    hits = [s for s in ALL_KNOWN_BIKES if s.model_name == model]
    assert len(hits) == 1, (model, len(hits))
    return hits[0]


def _row(mfr, model, year):
    hits = [b for b in BENCHMARKS if (b[0], b[1], b[2]) == (mfr, model, year)]
    assert len(hits) == 1, (mfr, model, year, len(hits))
    return hits[0]


# model -> (primary, gear_ratios, front, rear) after round 2
GEARING = {
    "Ninja ZX-25R (Indonesia)": (
        2.900,
        [2.929, 2.056, 1.619, 1.333, 1.154, 1.037],
        14,
        48,
    ),
    "Ninja 400": (2.219, [2.929, 2.056, 1.619, 1.333, 1.154, 1.037], 14, 41),
    "690 Duke R": (2.194, [2.500, 1.750, 1.333, 1.095, 0.957, 0.870], 16, 40),
    "RD500LC": (2.226, [2.250, 1.685, 1.363, 1.166, 1.043, 0.960], 15, 38),
}

# model -> primary only (cassette left as-is, documented open)
PRIMARY_ONLY = {
    "Vitpilen 701": 2.194,
    "701 Supermoto": 2.194,
    "RD350": 3.490,
    "750 H2 Mach IV": 2.085,
}


@pytest.mark.parametrize("model", sorted(GEARING))
def test_gearing_corrections_reach_the_config(model):
    primary, ratios, front, rear = GEARING[model]
    spec = _spec(model)
    assert spec.primary_ratio == primary
    assert spec.gear_ratios == ratios
    d = spec_to_bike_config(spec).drivetrain
    assert d.primary_ratio == pytest.approx(primary)
    assert list(d.gear_ratios) == pytest.approx(ratios)
    assert (d.front_sprocket, d.rear_sprocket) == (front, rear)
    assert d.final_ratio == pytest.approx(rear / front)


@pytest.mark.parametrize("model", sorted(PRIMARY_ONLY))
def test_primary_no_longer_the_tier2_default(model):
    d = spec_to_bike_config(_spec(model)).drivetrain
    assert d.primary_ratio == pytest.approx(PRIMARY_ONLY[model])


@pytest.mark.parametrize(
    "model,published_overall_1st,tol",
    [
        # Kawasaki official: 2.900 x 2.929 x 48/14
        ("Ninja ZX-25R (Indonesia)", 2.900 * 2.929 * 48 / 14, 1e-9),
        # Kawasaki official: 2.219 x 2.929 x 2.929
        ("Ninja 400", 2.219 * 2.929 * 41 / 14, 1e-9),
        # period road-test overall ratios (motorcyclespecs)
        ("RD350", 19.86, 0.005),
        ("750 H2 Mach IV", 12.75, 0.005),
    ],
)
def test_overall_first_gear_matches_the_published_figure(
    model, published_overall_1st, tol
):
    d = spec_to_bike_config(_spec(model)).drivetrain
    overall = d.primary_ratio * d.gear_ratios[0] * d.final_ratio
    assert overall == pytest.approx(published_overall_1st, rel=tol)


#: the round-2 curb conversions subtract the full fuel tank only (oil and
#: coolant volumes are not published), so the dry entry still carries them —
#: at most a few kg for these engines.
OIL_COOLANT_ALLOWANCE_KG = 4.0


@pytest.mark.parametrize(
    "model,curb_kg,fuel_l",
    [
        # published curb / wet mass (full fluids) and tank capacity
        ("Ninja ZX-25R (Indonesia)", 182.0, 15.0),
        ("Ninja 400", 166.0, 14.0),
        ("CB500F", 189.0, 17.1),
        ("YZF-R25 (Indonesia)", 166.0, 14.3),
        ("CBR250RR (Indonesia)", 165.0, 14.5),
        ("RD350", 155.0, 15.5),
    ],
)
def test_dry_entry_is_curb_minus_fuel(model, curb_kg, fuel_l):
    """The old entries put the CURB mass in the dry field and the importer
    then added its own fluid payload on top. Now: dry = curb - fuel, and the
    importer's running mass (dry + its fluid payload) sits within the
    oil/coolant allowance of the published curb mass."""
    spec = _spec(model)
    assert spec.dry_mass_kg == pytest.approx(curb_kg - fuel_l * 0.74, abs=0.06)
    c = spec_to_bike_config(spec).chassis
    running = c.dry_mass_kg + c.fluid_mass_kg
    assert curb_kg - 5.0 <= running <= curb_kg + OIL_COOLANT_ALLOWANCE_KG


def test_rated_power_and_torque_corrections():
    n4 = _spec("Ninja 400")
    assert (n4.peak_power_hp, n4.peak_torque_nm) == (48.3, 38.0)
    duke = _spec("690 Duke R")
    assert (duke.peak_power_hp, duke.peak_power_rpm) == (70.0, 7500)
    assert (duke.peak_torque_nm, duke.peak_torque_rpm) == (69.8, 6550)
    assert _spec("YZF-R25 (Indonesia)").peak_torque_nm == 22.6


def test_corrected_specs_validate_clean():
    for model in [
        "Ninja ZX-25R (Indonesia)",
        "Ninja 400",
        "CB500F",
        "RD350",
        "RD500LC",
        "750 H2 Mach IV",
        "690 Duke R",
        "Vitpilen 701",
        "701 Supermoto",
        "YZF-R25 (Indonesia)",
        "CBR250RR (Indonesia)",
    ]:
        r = validate_spec(_spec(model))
        assert r.is_valid and not r.errors, (model, r.errors)


# ── benchmark rows ────────────────────────────────────────────────────────


def test_rd350_row_is_cycle_worlds_published_figure():
    _, _, _, et, trap, src = _row("Yamaha", "RD350", 1973)
    assert (et, trap) == (14.30, 144.5)
    assert "RD Days" in src
    assert SL.source_quality(src) == (0.7, "magazine")
    assert SL.timing_convention_meta(src) == (SL.TIMING_ROLLOUT_1FT, "na_magazine")


def test_mt15_row_names_its_racelogic_device():
    _, _, _, et, _, src = _row("Yamaha", "MT-15", 2019)
    assert et == 19.60
    assert "Racelogic" in src
    assert SL.source_quality(src) == (1.0, "instrumented")
    assert SL.timing_convention(src) == SL.TIMING_FIRST_MOTION


def test_zx25r_row_cites_the_outlet_that_published_it():
    _, _, _, et, trap, src = _row("Kawasaki", "Ninja ZX-25R", 2020)
    assert (et, trap) == (14.10, 153.6)
    assert "TMCBlog" not in src and "Otomotifnet" in src
    assert SL.source_quality(src) == (1.0, "instrumented")
    assert SL.timing_convention(src) == SL.TIMING_FIRST_MOTION


def test_label_corrections_do_not_move_any_weight():
    """The three relabelled rows keep their weight under both classifiers, so
    tests/test_epoch_data_benchmarks.py's reviewed weight-change set stands."""
    for key in [
        ("Yamaha", "RD350", 1973),
        ("Yamaha", "MT-15", 2019),
        ("Kawasaki", "Ninja ZX-25R", 2020),
    ]:
        src = _row(*key)[5]
        assert SL.source_quality(src)[0] == SL.source_quality_legacy(src)[0]
