"""2026-10 data epoch — curated spec corrections.

* Every ALL_KNOWN_BIKES spec passes the validator's power/torque physical
  consistency check, except the one documented case whose MANUFACTURER
  figures are themselves inconsistent (Yamaha RD400 Daytona: 44 bhp @ 7000
  with 41.1 Nm @ 6500 — Wikipedia; Motoplanete quotes 40 ch / 4.2 mkg).
* The cited corrections stay in place (values + sources in the spec
  comments in known_bikes*.py).
"""

from __future__ import annotations

import logging

import pytest

from motoquant.scraper.importer import spec_to_bike_config
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES
from motoquant.scraper.validator import INCONSISTENT_TAG, validate_spec

logging.getLogger("motoquant").setLevel(logging.ERROR)

DOCUMENTED_INCONSISTENT = {("Yamaha", "RD400 Daytona")}


def _spec(mfr, model):
    hits = [
        s for s in ALL_KNOWN_BIKES if s.manufacturer == mfr and s.model_name == model
    ]
    assert len(hits) == 1, (mfr, model, len(hits))
    return hits[0]


def test_no_physically_inconsistent_catalog_specs():
    bad = []
    for s in ALL_KNOWN_BIKES:
        r = validate_spec(s)
        msgs = [m for m in r.warnings + r.errors if INCONSISTENT_TAG in m]
        if r.errors or msgs:
            bad.append(((s.manufacturer, s.model_name), r.errors + msgs))
    assert {k for k, _ in bad} == DOCUMENTED_INCONSISTENT, bad


@pytest.mark.parametrize(
    "mfr,model,hp,hp_rpm,nm,nm_rpm",
    [
        ("Yamaha", "YZF-R9", 117.4, 10000, 93.0, 7000),
        ("Honda", "RC213V-S", 156.8, 11000, 102.0, 10500),
        ("Triumph", "Daytona 955i", 147.0, 10700, 100.0, 8200),
        ("Bimota", "Tesi 1D", 102.0, 9500, 83.0, 8500),
        ("KTM", "890 Duke", 115.0, 9000, 92.0, 8000),
        ("KTM", "Duke 200", 24.7, 10000, 19.3, 8000),
        ("KTM", "RC 200", 24.7, 10000, 19.2, 8000),
        ("KTM", "Duke 250", 29.6, 9000, 24.0, 7500),
        ("Yamaha", "FZ-X", 12.2, 7250, 13.3, 5500),
        ("Kawasaki", "Ninja 300", 38.5, 11000, 27.0, 10000),
        ("Jawa", "Jawa 42", 26.96, 6800, 27.02, 5000),
        ("Honda", "NS400R", 71.0, 9500, 53.0, 8500),
        ("Honda", "CB400X (2023-2026)", 45.4, 9000, 38.0, 7500),
        ("Kawasaki", "Ninja H2", 207.0, 11000, 133.5, 10500),
    ],
)
def test_cited_power_torque_corrections(mfr, model, hp, hp_rpm, nm, nm_rpm):
    s = _spec(mfr, model)
    assert (s.peak_power_hp, s.peak_power_rpm, s.peak_torque_nm, s.peak_torque_rpm) == (
        pytest.approx(hp),
        hp_rpm,
        pytest.approx(nm),
        nm_rpm,
    )


def test_tesi_1d_is_the_851_engined_bike():
    s = _spec("Bimota", "Tesi 1D")
    assert s.displacement_cc == 851
    assert (s.bore_mm, s.stroke_mm) == (92.0, 64.0)
    assert s.dry_mass_kg == 188.0


def test_vrsc_pair_harmonised():
    """V-Rod Muscle (VRSCF) and VRSCA: one platform, cruiser tyre class,
    the Muscle is the heavier bike, and the Revolution 1250 is 105 x 72."""
    muscle = _spec("Harley-Davidson", "V-Rod Muscle")
    vrsca = _spec("Harley-Davidson", "VRSCA V-Rod")
    assert muscle.category == vrsca.category == "cruiser"
    assert muscle.dry_mass_kg > vrsca.dry_mass_kg
    assert (muscle.bore_mm, muscle.stroke_mm) == (105.0, 72.0)
    assert muscle.peak_torque_nm == pytest.approx(115.0)
    mu_m = spec_to_bike_config(muscle).tires.mu_peak
    mu_a = spec_to_bike_config(vrsca).tires.mu_peak
    assert mu_m == pytest.approx(mu_a)


def test_pan_america_gearing_from_hd_spec_sheet():
    """H-D 2022 RA1250 sheet: primary 89/49, chain 19/48, overall 1st 13.11
    and 6th 4.436."""
    cfg = spec_to_bike_config(_spec("Harley-Davidson", "Pan America 1250"))
    d = cfg.drivetrain
    assert (d.front_sprocket, d.rear_sprocket) == (19, 48)
    assert d.overall_ratio(0) == pytest.approx(13.11, rel=2e-3)
    assert d.overall_ratio(5) == pytest.approx(4.436, rel=2e-3)


def test_pursuit_dark_horse_belt_final_drive():
    d = spec_to_bike_config(_spec("Indian Motorcycle", "Pursuit Dark Horse")).drivetrain
    assert d.drive_type == "belt"
    assert d.final_ratio == pytest.approx(2.379)
