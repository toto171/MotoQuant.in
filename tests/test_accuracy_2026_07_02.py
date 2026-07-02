"""Regression pins for the 2026-07-02 accuracy pass.

Two changes are pinned here, all via the PRODUCTION spec path
(spec_to_bike_config), so reverting the fix fails the test:

1. High-power cruiser/ADV tire-grip gate — >=165 hp cruiser/adventure
   bikes (Diavel V4, Multistrada V4/RS, Rocket 3 Storm R, S1000XR) ship
   on sport/sport-touring radials and get mu 1.40/1.32 instead of the
   touring/knobby category defaults that left them traction-starved
   (+0.5..+0.8s slow vs instrumented benchmarks).
2. Kerb-vs-dry mass corrections on Multistrada V4 / Diavel V4 / CB1100.

Reference baselines (K5/R1/Hayabusa) are hand-curated in defaults.py and
must be bit-identical before/after — pinned in their own test.
"""

import pytest

from motoquant.scraper.importer import spec_to_bike_config
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES


def _spec(substr, year_from=None):
    for s in ALL_KNOWN_BIKES:
        name = f"{s.manufacturer} {s.model_name}"
        if substr.lower() in name.lower() and (
            year_from is None or s.year_from == year_from
        ):
            return s
    raise AssertionError(f"spec not found: {substr}")


class TestHighPowerCruiserAdvGripGate:
    @pytest.mark.parametrize(
        "substr, expected_mu",
        [
            ("Diavel V4", 1.40),  # 168hp cruiser on Diablo Rosso III
            ("Rocket 3 Storm R", 1.40),  # 182hp cruiser
            ("Multistrada V4 RS", 1.32),  # 185hp ADV on sport-touring
            ("BMW S1000XR", 1.32),  # 165hp crossover
        ],
    )
    def test_sport_radial_muscle_bikes_get_real_grip(self, substr, expected_mu):
        cfg = spec_to_bike_config(_spec(substr))
        assert cfg.tires.mu_peak == pytest.approx(expected_mu), (
            f"{substr}: grip gate regressed — these bikes were uniformly "
            "+0.5..+0.8s slow vs instrumented benchmarks on category-default rubber"
        )

    def test_base_multistrada_v4_in_gate(self):
        cfg = spec_to_bike_config(_spec("Multistrada V4", year_from=2021))
        assert cfg.tires.mu_peak == pytest.approx(1.32)

    @pytest.mark.parametrize(
        "substr, expected_mu",
        [
            ("Pan America", 1.15),  # 150hp — below gate, trail rubber
            ("1290 Super Adventure R", 1.15),  # 160hp — below gate, knobbies
        ],
    )
    def test_genuine_adventure_bikes_keep_trail_grip(self, substr, expected_mu):
        cfg = spec_to_bike_config(_spec(substr))
        assert cfg.tires.mu_peak == pytest.approx(expected_mu), (
            f"{substr}: the gate must NOT capture genuine ADVs on trail rubber"
        )

    def test_ordinary_cruiser_keeps_touring_grip(self):
        # any sub-165hp cruiser must keep the 1.20 touring default
        for s in ALL_KNOWN_BIKES:
            cat = (s.category or "").lower()
            hp = s.peak_power_hp or 0
            if cat == "cruiser" and hp < 140:
                cfg = spec_to_bike_config(s)
                assert cfg.tires.mu_peak == pytest.approx(1.20), (
                    f"{s.manufacturer} {s.model_name}: sub-165hp cruiser "
                    "must keep the touring-compound default"
                )
                return
        pytest.skip("no sub-140hp cruiser in catalog")


class TestKerbVsDryMassCorrections:
    @pytest.mark.parametrize(
        "substr, year, expected_dry",
        [
            ("Multistrada V4", 2021, 218.0),
            ("Diavel V4", 2023, 211.0),
            ("CB1100", 2013, 237.0),
        ],
    )
    def test_dry_mass_is_manufacturer_dry_figure(self, substr, year, expected_dry):
        spec = _spec(substr, year_from=year)
        assert spec.dry_mass_kg == pytest.approx(expected_dry), (
            f"{substr}: kerb-weight regression — the old value double-counted "
            "fluids on top of chassis.fluid_mass_kg"
        )


class TestReferenceBaselinesUntouched:
    def test_k5_r1_hayabusa_exact(self):
        import motoquant
        from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8

        for fn, target in [
            (gsxr1000_k5, 10.0334),
            (yzfr1_4c8, 10.2859),
            (hayabusa_gen1, 10.4712),
        ]:
            r = motoquant.MotoQuantEngine(fn()).run()
            assert r.time_quarter == pytest.approx(target, abs=0.02)
