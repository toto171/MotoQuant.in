"""2026-10 data epoch — importer aero + drivetrain conventions.

Pins, through the production ``spec_to_bike_config`` path:

* the sport-category Cd ×0.55 "tuck normalisation" is gone — every curated
  spec's Cd / frontal area reaches the sim verbatim, on the same scale as the
  hand-curated references in ``motoquant/defaults.py``;
* ``DrivetrainParams.drive_type`` is set (shaft / belt / chain) from the
  spec's declaration or the manufacturer heuristic, and the shaft path of
  ``DrivetrainParams.drivetrain_efficiency()`` is what shaft bikes get;
* a curated spec's ``final_drive`` / ``chain_pitch`` is honoured instead of
  being discarded for the displacement heuristic.

Each test fails if the corresponding importer change is reverted.
"""

from __future__ import annotations

import logging
import statistics

import pytest

from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8
from motoquant.models import DRIVE_BELT, DRIVE_CHAIN, DRIVE_SHAFT
from motoquant.scraper.importer import (
    _infer_chain_pitch,
    _infer_drive_type,
    spec_to_bike_config,
)
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES
from motoquant.scraper.spec import BikeSpec

logging.getLogger("motoquant").setLevel(logging.ERROR)


def _spec(mfr, model, year=None):
    hits = [
        s
        for s in ALL_KNOWN_BIKES
        if s.manufacturer == mfr
        and s.model_name == model
        and (year is None or s.year_from == year)
    ]
    assert len(hits) == 1, (mfr, model, year, len(hits))
    return hits[0]


# ── Aero: no sport Cd ×0.55 ───────────────────────────────────────────────


def test_every_catalog_cd_reaches_the_sim_verbatim():
    """No catalog spec's Cd is rescaled — in particular no faired sport bike
    gets the removed ``max(0.30, cd*0.55)`` treatment."""
    sport = 0
    for s in ALL_KNOWN_BIKES:
        a = spec_to_bike_config(s).aero
        assert a.cd == s.cd, (s.manufacturer, s.model_name, s.cd, a.cd)
        assert a.frontal_area_m2 == s.frontal_area_m2, (s.manufacturer, s.model_name)
        if s.category == "sport" and s.cd > 0.45:
            sport += 1
    # The removed rule used to hit every one of these (132 matched in the
    # 2026-08-08 sweep); make sure the population still exists.
    assert sport > 150


def test_sport_spec_with_upright_scale_cd_is_not_rescaled():
    s = BikeSpec(
        manufacturer="Testmoto",
        model_name="Faired 1000",
        category="sport",
        displacement_cc=998,
        peak_power_hp=180.0,
        peak_power_rpm=12000,
        peak_torque_nm=112.0,
        peak_torque_rpm=10000,
        cylinders=4,
        dry_mass_kg=180.0,
        cd=0.70,
        frontal_area_m2=0.45,
    )
    a = spec_to_bike_config(s).aero
    assert a.cd == pytest.approx(0.70)  # pre-epoch: 0.385
    assert a.cd * a.frontal_area_m2 == pytest.approx(0.315)


def test_catalog_cda_is_on_the_reference_scale():
    """Catalog faired-sport Cd·A sits on the scale of the references the
    pins are built on (K5 0.315 / R1 0.317 / Hayabusa 0.310 m²), not at the
    ~0.16 m² the ×0.55 rescale produced."""
    refs = [
        c.aero.cd * c.aero.frontal_area_m2
        for c in (gsxr1000_k5(), yzfr1_4c8(), hayabusa_gen1())
    ]
    ref = statistics.mean(refs)
    assert ref == pytest.approx(0.314, abs=0.005)
    cda = []
    for s in ALL_KNOWN_BIKES:
        if s.category == "sport" and (s.displacement_cc or 0) >= 600:
            a = spec_to_bike_config(s).aero
            cda.append(a.cd * a.frontal_area_m2)
    med = statistics.median(cda)
    assert 0.8 * ref <= med <= 1.2 * ref, (med, ref)


# ── Drivetrain: drive_type ────────────────────────────────────────────────

SHAFT = [
    ("BMW", "R 1250 GS"),
    ("BMW", "R1200GS"),
    ("BMW", "R nineT"),
    ("BMW", "R 12 nineT"),
    ("BMW", "K1300S"),
    ("BMW", "K1600 GT"),
    ("BMW", "R 18"),
    ("BMW", "R 1300 GS"),
    ("Yamaha", "FJR1300"),
    ("Yamaha", "Super Tenere XT1200Z"),
    ("Yamaha", "VMAX 1700"),
    ("Yamaha", "VMAX 1200 (1985-2007)"),
    ("Triumph", "Rocket 3 R"),
    ("Triumph", "Rocket 3 Storm R (2024-2026)"),
    ("Triumph", "Tiger 1200 GT Pro"),
    ("Moto Guzzi", "V85 TT"),
    ("Moto Guzzi", "V100 Mandello S"),
]
BELT = [
    ("Harley-Davidson", "Sportster S"),
    ("Harley-Davidson", "V-Rod Muscle"),
    ("Harley-Davidson", "VRSCA V-Rod"),
    ("Harley-Davidson", "Nightster"),
    ("Harley-Davidson", "Road Glide"),
    ("Indian", "Scout"),
    ("Indian", "Chief Dark Horse"),
    ("Indian Motorcycle", "Pursuit Dark Horse"),
    ("Buell", "1125R"),
    ("Yamaha", "Aerox 155 (SE Asia)"),
    ("TVS", "NTorq 125 Race XP"),
]
CHAIN_EXCEPTIONS = [
    # chain bikes the old heuristic (or an old spec) typed as belt/shaft
    ("Harley-Davidson", "Pan America 1250"),  # H-D spec sheet: chain 19/48
    ("Honda", "CB1100"),  # #530 O-ring chain
    ("Indian", "FTR 1200 S"),
    ("Bimota", "Tesi 1D"),  # Ducati 851 platform, chain
]


@pytest.mark.parametrize("mfr,model", SHAFT)
def test_shaft_bikes_run_shaft_drive(mfr, model):
    d = spec_to_bike_config(_spec(mfr, model)).drivetrain
    assert d.drive_type == DRIVE_SHAFT
    assert d.chain_pitch is None
    assert d.drivetrain_efficiency() == pytest.approx(
        d.primary_efficiency * d.trans_efficiency_per_mesh * d.shaft_efficiency
    )


@pytest.mark.parametrize("mfr,model", BELT)
def test_belt_bikes_run_belt_drive(mfr, model):
    d = spec_to_bike_config(_spec(mfr, model)).drivetrain
    assert d.drive_type == DRIVE_BELT
    assert d.chain_pitch is None


@pytest.mark.parametrize("mfr,model", CHAIN_EXCEPTIONS)
def test_chain_exceptions_run_chain_drive(mfr, model):
    d = spec_to_bike_config(_spec(mfr, model)).drivetrain
    assert d.drive_type == DRIVE_CHAIN
    assert d.chain_pitch is not None


def test_zero_sprocket_sentinel_specs_are_non_chain_except_documented():
    """The 0/0 sprocket pair is the documented shaft/belt sentinel; the only
    chain bike carrying it (Tesi 1D) declares final_drive='chain'."""
    for s in ALL_KNOWN_BIKES:
        if s.front_sprocket == 0 or s.rear_sprocket == 0:
            d = spec_to_bike_config(s).drivetrain
            if (s.manufacturer, s.model_name) == ("Bimota", "Tesi 1D"):
                assert d.drive_type == DRIVE_CHAIN
            else:
                assert d.drive_type != DRIVE_CHAIN, (s.manufacturer, s.model_name)


def test_declared_drive_type_beats_heuristic():
    # final_drive on a chain make
    s = BikeSpec(
        manufacturer="Kawasaki",
        model_name="Concours",
        final_drive="shaft",
        displacement_cc=1352,
    )
    assert _infer_drive_type(s) == DRIVE_SHAFT
    assert _infer_chain_pitch(s) is None
    # a pitch code on a belt make (the Pan America case)
    s = BikeSpec(
        manufacturer="Harley-Davidson",
        model_name="Test ADV",
        chain_pitch="525",
        displacement_cc=1252,
    )
    assert _infer_drive_type(s) == DRIVE_CHAIN
    assert _infer_chain_pitch(s) == "525"
    # silent spec -> heuristic
    s = BikeSpec(
        manufacturer="Harley-Davidson", model_name="Street Bob", displacement_cc=1868
    )
    assert _infer_drive_type(s) == DRIVE_BELT
    s = BikeSpec(manufacturer="Honda", model_name="CB1100", displacement_cc=1140)
    assert _infer_drive_type(s) == DRIVE_CHAIN  # was in the shaft list


def test_drive_type_is_live_in_the_sim():
    """The stamped drive_type changes the result (guards against it becoming
    a dead field between the importer and the loop)."""
    from motoquant.physics import MotoQuantEngine

    cfg = spec_to_bike_config(_spec("Yamaha", "FJR1300"))
    assert cfg.drivetrain.drive_type == DRIVE_SHAFT
    et_shaft = (
        MotoQuantEngine(cfg).run(use_adaptive_dt=False, max_time=26.0).time_quarter
    )
    cfg.drivetrain.drive_type = DRIVE_CHAIN
    et_chain = (
        MotoQuantEngine(cfg).run(use_adaptive_dt=False, max_time=26.0).time_quarter
    )
    assert et_shaft != et_chain


# ── Drivetrain: spec chain_pitch / final_drive honoured ──────────────────


def test_curated_chain_pitch_is_honoured():
    n = 0
    for s in ALL_KNOWN_BIKES:
        cp = (s.chain_pitch or "").strip()
        if cp in {"420", "428", "520", "525", "530", "532"}:
            d = spec_to_bike_config(s).drivetrain
            if d.drive_type == DRIVE_CHAIN:
                assert d.chain_pitch == cp, (
                    s.manufacturer,
                    s.model_name,
                    cp,
                    d.chain_pitch,
                )
                n += 1
    assert n > 400


def test_curated_final_drive_is_honoured():
    words = {"chain": DRIVE_CHAIN, "belt": DRIVE_BELT, "shaft": DRIVE_SHAFT}
    n = 0
    for s in ALL_KNOWN_BIKES:
        fd = (s.final_drive or "").strip().lower()
        if fd in words:
            assert spec_to_bike_config(s).drivetrain.drive_type == words[fd], (
                s.manufacturer,
                s.model_name,
            )
            n += 1
    assert n >= 15


def test_420_pitch_maps_to_half_inch():
    d = spec_to_bike_config(_spec("Honda", "Grom MSX125")).drivetrain
    assert d.chain_pitch == "420"
    assert d.chain_pitch_mm == pytest.approx(12.7)
