"""
MotoQuant Pro — Two-Stroke Physics + Parts Tests
================================================
Covers:
  - 2-stroke bike specs validate and convert to sim-ready BikeConfig
  - 2T synthetic torque curve has Gaussian expansion-chamber shape
  - 2T catalog parts fit only 2T bikes (no 4T leaks)
  - stroke_type filter in FitmentMatch prevents 2T/4T cross-matches
  - engine importer sets stroke_type=2, reed_valve, powervalve, tuned_rpm,
    expansion_chamber fields on the resulting EngineParams
  - Staging (launch_rpm override) and Parasitic (no valvetrain, water pump)
    are adjusted for 2T
"""

import json
import pytest

from motoquant.scraper.importer import spec_to_bike_config, import_batch
from motoquant.scraper.known_bikes import (
    ALL_KNOWN_BIKES,
    YAMAHA_RD350_1974,
    YAMAHA_RX100_1985,
    APRILIA_RS125_2006,
    KTM_300_EXC_2020,
    HONDA_CR500R_1996,
)
from motoquant.scraper.validator import validate_spec
from motoquant.database.connection import MotoQuantDB
from motoquant.database.seed import seed_all
from motoquant.database.parts_repo import _enrich_bike_row_for_fitment
from motoquant.parts.compatibility import (
    FitmentMatch,
    FitmentRules,
    FitmentTier,
    is_compatible,
)


# ════════════════════════════════════════════════════════════════════════
# Fixtures
# ════════════════════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def seeded_db(tmp_path_factory):
    """A fully-seeded DB with all known bikes imported — module-scoped."""
    db_path = tmp_path_factory.mktemp("two_stroke") / "ts.db"
    db = MotoQuantDB(str(db_path))
    db.initialize()
    seed_all(db)
    import_batch(db, ALL_KNOWN_BIKES)
    yield db
    db.close()


# ════════════════════════════════════════════════════════════════════════
# Spec validation
# ════════════════════════════════════════════════════════════════════════


class TestTwoStrokeSpecs:
    """2-stroke BikeSpec objects parse, validate, and hydrate correctly."""

    @pytest.mark.parametrize(
        "spec",
        [YAMAHA_RD350_1974, YAMAHA_RX100_1985, APRILIA_RS125_2006,
         KTM_300_EXC_2020, HONDA_CR500R_1996],
    )
    def test_is_two_stroke(self, spec):
        assert spec.stroke_type == 2

    @pytest.mark.parametrize(
        "spec",
        [YAMAHA_RD350_1974, YAMAHA_RX100_1985, APRILIA_RS125_2006,
         KTM_300_EXC_2020, HONDA_CR500R_1996],
    )
    def test_validates(self, spec):
        result = validate_spec(spec)
        assert result.is_valid, f"{spec.model_name}: {result.errors}"

    def test_all_2t_bikes_in_catalog(self):
        ts_count = sum(1 for s in ALL_KNOWN_BIKES if s.stroke_type == 2)
        assert ts_count >= 20, f"Expected ≥20 2T bikes, found {ts_count}"

    def test_rx100_is_4_speed(self):
        """RX100 1V1 is historically a 4-speed, not padded to 5."""
        assert len(YAMAHA_RX100_1985.gear_ratios) == 4


# ════════════════════════════════════════════════════════════════════════
# Importer: 2T branching in _build_engine_from_spec + spec_to_bike_config
# ════════════════════════════════════════════════════════════════════════


class TestTwoStrokeImporter:
    """spec_to_bike_config branches correctly on stroke_type."""

    def test_engine_params_stroke_type_is_2(self):
        cfg = spec_to_bike_config(YAMAHA_RD350_1974)
        assert cfg.engine.stroke_type == 2

    def test_engine_params_carries_2t_flags(self):
        # RD350 spec sets reed_valve=True, expansion_chamber=False, powervalve=False
        cfg = spec_to_bike_config(YAMAHA_RD350_1974)
        assert cfg.engine.reed_valve == YAMAHA_RD350_1974.reed_valve
        assert cfg.engine.expansion_chamber == YAMAHA_RD350_1974.expansion_chamber
        assert cfg.engine.powervalve == YAMAHA_RD350_1974.powervalve

    def test_engine_params_sets_tuned_rpm(self):
        """2T bikes without explicit tuned_rpm get peak_power_rpm as default."""
        cfg = spec_to_bike_config(YAMAHA_RD350_1974)
        assert cfg.engine.tuned_rpm is not None
        assert 5000 <= cfg.engine.tuned_rpm <= 15000

    def test_engine_inertia_scaled_for_2t(self):
        """2T bikes should have ~0.60× the engine inertia of comparable 4T (no valvetrain)."""
        cfg = spec_to_bike_config(YAMAHA_RD350_1974)
        # 0.60 × naked-category baseline (0.042) = 0.0252
        assert 0.020 <= cfg.engine.engine_inertia_kgm2 <= 0.035

    def test_staging_launch_rpm_override_for_2t(self):
        """2T launch RPM should be set near tuned_rpm × 0.92 (drag-launch point)."""
        cfg = spec_to_bike_config(KTM_300_EXC_2020)
        assert cfg.staging.two_step is True
        # KTM 300 EXC tuned_rpm ~ peak_power_rpm ~ 8000; launch ≈ 7360
        assert 6000 <= cfg.staging.launch_rpm <= 10000

    def test_parasitic_no_valvetrain_for_2t(self):
        """2T engines have no valvetrain — parasitic_valve_train_power_w=0."""
        cfg = spec_to_bike_config(YAMAHA_RD350_1974)
        assert cfg.parasitic.valve_train_power_w == 0.0

    def test_air_cooled_2t_no_water_pump(self):
        """Air-cooled 2T (RD350, RX100) → water_pump_electric=True (zero drag)."""
        cfg = spec_to_bike_config(YAMAHA_RD350_1974)
        assert cfg.parasitic.water_pump_electric is True

    def test_dyno_curve_is_synthetic_2t(self):
        """spec_to_bike_config injects a 2T-flavoured synthetic torque curve."""
        cfg = spec_to_bike_config(YAMAHA_RD350_1974)
        assert cfg.engine.dyno_curve is not None
        # 2T curve peaks sharply around tuned_rpm (Gaussian), not parabolic.
        rpms = cfg.engine.dyno_curve.rpm
        torques = cfg.engine.dyno_curve.torque_nm
        peak_idx = max(range(len(torques)), key=lambda i: torques[i])
        peak_rpm = rpms[peak_idx]
        # RD350 peak_power_rpm = 7500; Gaussian 2T curve should peak nearby.
        assert 5000 <= peak_rpm <= 9500


# ════════════════════════════════════════════════════════════════════════
# FitmentMatch.stroke_type constraint
# ════════════════════════════════════════════════════════════════════════


class TestStrokeTypeFilter:
    """stroke_type constraint on FitmentMatch correctly gates compat."""

    def test_2t_part_rejects_4t_bike(self):
        """A 2T-only part should NOT match a 4T bike of same config/disp."""
        part = {
            "fitment_rules": json.dumps({
                "tier": "family",
                "match": {
                    "engine_configs": ["I1"],
                    "displacement_min_cc": 200,
                    "displacement_max_cc": 400,
                    "stroke_type": 2,
                },
            }),
        }
        four_stroke_bike = {
            "id": 1, "manufacturer": "KTM", "displacement_cc": 250,
            "cylinder_config": "I1", "stroke_type": 4,
        }
        ok, reason = is_compatible(part, four_stroke_bike)
        assert ok is False
        assert "stroke_type" in reason

    def test_2t_part_matches_2t_bike(self):
        part = {
            "fitment_rules": json.dumps({
                "tier": "family",
                "match": {
                    "engine_configs": ["I1"],
                    "displacement_min_cc": 200,
                    "displacement_max_cc": 400,
                    "stroke_type": 2,
                },
            }),
        }
        two_stroke_bike = {
            "id": 2, "manufacturer": "KTM", "displacement_cc": 293,
            "cylinder_config": "I1", "stroke_type": 2,
        }
        ok, _ = is_compatible(part, two_stroke_bike)
        assert ok is True

    def test_missing_stroke_type_defaults_to_4t(self):
        """A bike row without stroke_type is treated as 4T for backwards compat."""
        part = {
            "fitment_rules": json.dumps({
                "tier": "family",
                "match": {
                    "engine_configs": ["I1"],
                    "stroke_type": 4,
                },
            }),
        }
        legacy_bike = {
            "id": 3, "manufacturer": "Honda", "displacement_cc": 300,
            "cylinder_config": "I1",
            # no stroke_type — defaults to 4
        }
        ok, _ = is_compatible(part, legacy_bike)
        assert ok is True

    def test_fitment_match_round_trip(self):
        """FitmentMatch.to_dict() / from_dict() preserves stroke_type."""
        m = FitmentMatch(stroke_type=2, engine_configs=["I2"])
        d = m.to_dict()
        assert d["stroke_type"] == 2
        m2 = FitmentMatch.from_dict(d)
        assert m2.stroke_type == 2


# ════════════════════════════════════════════════════════════════════════
# Catalog integration — no 2T-part leaks to 4T bikes, every 2T bike covered
# ════════════════════════════════════════════════════════════════════════


class TestTwoStrokeCatalogIntegrity:
    """Ensures the 2T catalog is tight."""

    @pytest.fixture
    def ts_parts_and_bikes(self, seeded_db):
        with seeded_db.connect() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT id, brand, model_name, fitment_rules, specifications FROM parts"
            )
            all_parts = [dict(r) for r in cur.fetchall()]
            ts_parts = [
                p for p in all_parts
                if p["specifications"] and '"stroke_type": 2' in p["specifications"]
            ]
            cur.execute(
                """SELECT bm.id, mfr.name AS manufacturer, bm.model_name AS model,
                          bm.displacement_cc, bm.cylinder_count, bm.cylinder_config,
                          bm.category, bc.engine_params
                   FROM bike_models bm
                   JOIN manufacturers mfr ON mfr.id = bm.manufacturer_id
                   JOIN bike_configs bc ON bc.bike_model_id = bm.id
                   WHERE bc.is_current = 1"""
            )
            bikes = [dict(r) for r in cur.fetchall()]
        return ts_parts, bikes

    def test_two_stroke_catalog_has_parts(self, ts_parts_and_bikes):
        ts_parts, _ = ts_parts_and_bikes
        assert len(ts_parts) >= 35, f"Expected ≥35 2T parts, got {len(ts_parts)}"

    def test_no_two_stroke_part_leaks_to_4t_bike(self, seeded_db, ts_parts_and_bikes):
        """Every 2T part must have zero 4T-bike matches."""
        ts_parts, bikes = ts_parts_and_bikes
        leaks = []
        for p in ts_parts:
            for b in bikes:
                ep = json.loads(b["engine_params"])
                if ep.get("stroke_type", 4) == 2:
                    continue
                bike_row = dict(b)
                _enrich_bike_row_for_fitment(seeded_db._conn, bike_row)
                ok, _ = is_compatible(p, bike_row)
                if ok:
                    leaks.append((p["brand"], p["model_name"],
                                  b["manufacturer"], b["model"]))
        assert leaks == [], f"2T→4T leaks detected: {leaks[:10]}"

    def test_every_two_stroke_bike_has_at_least_one_part(
        self, seeded_db, ts_parts_and_bikes
    ):
        """Every 2T bike in the catalog must have ≥1 compatible 2T part."""
        ts_parts, bikes = ts_parts_and_bikes
        two_stroke_bikes = [
            b for b in bikes
            if json.loads(b["engine_params"]).get("stroke_type", 4) == 2
        ]
        uncovered = []
        for b in two_stroke_bikes:
            bike_row = dict(b)
            _enrich_bike_row_for_fitment(seeded_db._conn, bike_row)
            hits = sum(1 for p in ts_parts if is_compatible(p, bike_row)[0])
            if hits == 0:
                uncovered.append(f"{b['manufacturer']} {b['model']}")
        assert uncovered == [], f"Uncovered 2T bikes: {uncovered}"

    def test_exhaust_coverage_for_every_two_stroke_bike(
        self, seeded_db, ts_parts_and_bikes
    ):
        """Every 2T bike must match ≥1 exhaust (expansion chamber)."""
        ts_parts, bikes = ts_parts_and_bikes
        # The 2T parts tagged as exhausts (category 'exhaust') live in ts_parts
        # with 'expansion_chamber' in their specs. Simpler: re-query by category.
        with seeded_db.connect() as con:
            cur = con.cursor()
            cur.execute(
                """SELECT p.id, p.brand, p.model_name, p.fitment_rules,
                          p.specifications
                   FROM parts p
                   JOIN parts_categories pc ON pc.id = p.category_id
                   WHERE pc.name = 'exhaust'
                     AND p.specifications LIKE '%"stroke_type": 2%'"""
            )
            ts_exhausts = [dict(r) for r in cur.fetchall()]
        two_stroke_bikes = [
            b for b in bikes
            if json.loads(b["engine_params"]).get("stroke_type", 4) == 2
        ]
        uncovered = []
        for b in two_stroke_bikes:
            bike_row = dict(b)
            _enrich_bike_row_for_fitment(seeded_db._conn, bike_row)
            hits = sum(1 for p in ts_exhausts if is_compatible(p, bike_row)[0])
            if hits == 0:
                uncovered.append(f"{b['manufacturer']} {b['model']}")
        assert uncovered == [], (
            f"2T bikes with no matching exhaust: {uncovered}"
        )


# ════════════════════════════════════════════════════════════════════════
# Reference baselines preserved — adding 2T physics MUST NOT regress 4T
# ════════════════════════════════════════════════════════════════════════


class TestReferenceBaselinesPreserved:
    def test_k5_baseline(self):
        import motoquant
        e = motoquant.MotoQuantEngine(motoquant.gsxr1000_k5())
        r = e.run()
        # Allow ±0.010s drift from the canonical 10.034s baseline
        assert 10.02 <= r.time_quarter <= 10.05, (
            f"K5 regressed: {r.time_quarter:.3f}s (expected ~10.034)"
        )

    def test_hayabusa_baseline(self):
        import motoquant
        e = motoquant.MotoQuantEngine(motoquant.hayabusa_gen1())
        r = e.run()
        assert 10.45 <= r.time_quarter <= 10.50, (
            f"Hayabusa regressed: {r.time_quarter:.3f}s (expected ~10.472)"
        )
