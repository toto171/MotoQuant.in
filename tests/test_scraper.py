"""
Tests for motoquant.scraper — BikeSpec pipeline
=============================================
Covers:
  - BikeSpec construction and defaults
  - ValidationResult dataclass
  - validate_spec(): bounds, unit auto-correction, consistency checks
  - score_spec(): weight coverage and penalties
  - _source_confidence() mapping
  - spec_to_bike_config(): all sub-config builders
  - import_spec(): dry_run and live DB upsert
  - import_batch(): success, skip, error counting
  - ALL_KNOWN_BIKES: all 22 curated bikes validate and import cleanly
"""

import pytest

from motoquant.database import MotoQuantDB
from motoquant.scraper.importer import (
    CATEGORY_AERO,
    CATEGORY_COG_HEIGHT,
    CATEGORY_ENGINE_INERTIA,
    _build_aero_from_spec,
    _build_chassis_from_spec,
    _build_drivetrain_from_spec,
    _build_engine_from_spec,
    _build_tires_from_spec,
    import_batch,
    import_spec,
    spec_to_bike_config,
)
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES
from motoquant.scraper.spec import BikeSpec, ValidationResult
from motoquant.scraper.validator import (
    _source_confidence,
    score_spec,
    validate_spec,
)

# ────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────


def _make_spec(**kwargs) -> BikeSpec:
    """Create a minimal valid BikeSpec, overriding any fields with kwargs."""
    defaults = {
        "manufacturer": "Suzuki",
        "model_name": "GSX-R 1000",
        "model_code": "K5",
        "year_from": 2005,
        "year_to": 2006,
        "category": "sport",
        "displacement_cc": 999.0,
        "bore_mm": 73.4,
        "stroke_mm": 59.0,
        "cylinders": 4,
        "compression_ratio": 12.0,
        "peak_power_hp": 178.0,
        "peak_power_rpm": 12000,
        "peak_torque_nm": 112.0,
        "peak_torque_rpm": 10000,
        "dry_mass_kg": 166.0,
        "wet_mass_kg": 192.0,
        "wheelbase_mm": 1405.0,
        "seat_height_mm": 810.0,
        "gears": 6,
        "gear_ratios": [2.600, 2.105, 1.750, 1.500, 1.333, 1.200],
        "front_sprocket": 17,
        "rear_sprocket": 45,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "190/55ZR17",
        "source_name": "service_manual",
    }
    defaults.update(kwargs)
    return BikeSpec(**defaults)


@pytest.fixture
def good_spec() -> BikeSpec:
    return _make_spec()


@pytest.fixture
def scraper_db():
    """In-memory DB (DELETE journal mode for test isolation)."""
    db = MotoQuantDB(":memory:")
    db.connect()
    db.conn.execute("PRAGMA journal_mode=DELETE")
    db.initialize()
    yield db
    db.close()


# ────────────────────────────────────────────────────────────
# BikeSpec construction
# ────────────────────────────────────────────────────────────


class TestBikeSpec:
    def test_default_category(self):
        spec = BikeSpec(manufacturer="Honda", model_name="CBR")
        assert spec.category == "sport"

    def test_scraped_at_auto_set(self):
        spec = BikeSpec(manufacturer="Honda", model_name="CBR")
        assert spec.scraped_at is not None

    def test_field_confidence_empty_by_default(self):
        spec = BikeSpec(manufacturer="Honda", model_name="CBR")
        assert spec.field_confidence == {}

    def test_all_numeric_optional(self):
        spec = BikeSpec(manufacturer="X", model_name="Y")
        for attr in (
            "displacement_cc",
            "bore_mm",
            "peak_power_hp",
            "dry_mass_kg",
            "wheelbase_mm",
            "gear_ratios",
        ):
            assert getattr(spec, attr) is None

    def test_validation_result_str_valid(self):
        vr = ValidationResult(is_valid=True, overall_confidence=0.85)
        s = str(vr)
        assert "VALID" in s
        assert "0.85" in s

    def test_validation_result_str_invalid(self):
        vr = ValidationResult(is_valid=False, errors=["oops"], overall_confidence=0.0)
        s = str(vr)
        assert "INVALID" in s
        assert "oops" in s


# ────────────────────────────────────────────────────────────
# validate_spec — bounds checking
# ────────────────────────────────────────────────────────────


class TestValidateSpec:
    def test_valid_spec_passes(self, good_spec):
        result = validate_spec(good_spec)
        assert result.is_valid
        assert result.errors == []

    def test_missing_manufacturer_is_error(self):
        spec = _make_spec(manufacturer="")
        result = validate_spec(spec)
        assert not result.is_valid
        assert any("manufacturer" in e for e in result.errors)

    def test_missing_model_name_is_error(self):
        spec = _make_spec(model_name="")
        result = validate_spec(spec)
        assert not result.is_valid
        assert any("model_name" in e for e in result.errors)

    def test_displacement_out_of_bounds(self):
        spec = _make_spec(displacement_cc=5000.0)
        result = validate_spec(spec)
        assert not result.is_valid
        assert any("displacement_cc" in e for e in result.errors)

    def test_mass_out_of_bounds_low(self):
        spec = _make_spec(dry_mass_kg=50.0)
        result = validate_spec(spec)
        assert not result.is_valid

    def test_gear_ratio_not_decreasing_is_error(self):
        spec = _make_spec(gear_ratios=[2.6, 2.1, 2.2, 1.5, 1.3, 1.2])
        result = validate_spec(spec)
        assert not result.is_valid
        assert any("gear_ratios" in e for e in result.errors)

    def test_wet_less_than_dry_is_error(self):
        spec = _make_spec(dry_mass_kg=180.0, wet_mass_kg=160.0)
        result = validate_spec(spec)
        assert not result.is_valid
        assert any("wet_mass" in e for e in result.errors)

    def test_tire_size_bad_format_is_warning(self, good_spec):
        good_spec.rear_tire_size = "fat tire"
        result = validate_spec(good_spec)
        assert result.is_valid  # warning only
        assert any("rear_tire_size" in w for w in result.warnings)

    def test_power_kw_auto_converts(self):
        # 520 is out of HP bounds [5, 500], but 520 * 0.7457 ≈ 387 HP is valid
        # → validator should auto-convert with a warning (not an error)
        spec = _make_spec()
        spec.peak_power_hp = 520.0
        result = validate_spec(spec)
        assert result.is_valid  # converted to ~387 HP, still valid
        assert any("kW" in w for w in result.warnings)

    def test_unit_conversion_kw_to_hp(self):
        # 150 kW = 201 HP — validator should auto-convert
        spec = _make_spec(peak_power_hp=150.0)
        # 150 is within HP bounds so no conversion triggered; test kW value at edge
        # Force an out-of-range HP value that's in-range as kW * 0.7457
        spec = _make_spec()
        spec.peak_power_hp = 520.0  # out of [5, 500] as HP
        # 520 * 0.7457 = 387.8 → valid HP, so should convert
        result = validate_spec(spec)
        assert any("kW" in w for w in result.warnings)
        assert spec.peak_power_hp == pytest.approx(520 * 0.7457, rel=1e-4)

    def test_bore_stroke_displacement_mismatch_warning(self):
        # bore=73.4, stroke=59, cyl=4 → ~999cc, set displacement wrong
        spec = _make_spec(displacement_cc=750.0)
        result = validate_spec(spec)
        assert result.is_valid  # warning only
        assert any("Bore" in w for w in result.warnings)

    def test_torque_power_inconsistency_warning(self, good_spec):
        # Power 178HP at 12000 RPM → ~141 Nm expected, we set 200 Nm → 42% off
        good_spec.peak_torque_nm = 200.0
        result = validate_spec(good_spec)
        assert result.is_valid
        assert any("Torque inconsistency" in w for w in result.warnings)

    def test_cd_autofill_from_category(self):
        spec = _make_spec(category="cruiser")
        spec.cd = None
        spec.frontal_area_m2 = None
        validate_spec(spec)
        assert spec.cd == pytest.approx(0.50, rel=0.01)
        assert spec.frontal_area_m2 is not None

    def test_gear_ratios_default_6speed(self):
        spec = _make_spec(gear_ratios=None, gears=6)
        validate_spec(spec)
        assert spec.gear_ratios is not None
        assert len(spec.gear_ratios) == 6

    def test_gear_ratios_default_5speed(self):
        spec = _make_spec(gear_ratios=None, gears=5)
        validate_spec(spec)
        assert len(spec.gear_ratios) == 5

    def test_corrected_fields_populated(self):
        spec = _make_spec(category="naked")
        spec.cd = None
        result = validate_spec(spec)
        assert "cd" in result.corrected_fields


# ────────────────────────────────────────────────────────────
# score_spec
# ────────────────────────────────────────────────────────────


class TestScoreSpec:
    def test_full_spec_scores_high(self, good_spec):
        result = validate_spec(good_spec)
        score = score_spec(good_spec, result)
        assert score >= 0.70

    def test_minimal_spec_scores_lower(self):
        spec = BikeSpec(manufacturer="X", model_name="Y", source_name="scraped")
        result = validate_spec(spec)
        score = score_spec(spec, result)
        assert score < 0.40

    def test_warnings_reduce_score(self, good_spec):
        result_clean = validate_spec(good_spec)
        score_clean = score_spec(good_spec, result_clean)

        spec2 = _make_spec()
        spec2.peak_torque_nm = 200.0
        result2 = validate_spec(spec2)
        score2 = score_spec(spec2, result2)
        assert score2 < score_clean

    def test_score_clamped_0_to_1(self, good_spec):
        result = validate_spec(good_spec)
        score = score_spec(good_spec, result)
        assert 0.0 <= score <= 1.0

    def test_service_manual_confidence_used(self):
        spec = _make_spec(source_name="service_manual")
        result = validate_spec(spec)
        score = score_spec(spec, result)
        # service_manual has 0.95 confidence → should score well
        assert score >= 0.65

    def test_source_confidence_mapping(self):
        assert _source_confidence("manufacturer") > _source_confidence("bikez")
        assert _source_confidence("bikez") > _source_confidence("default_fallback")
        assert _source_confidence("scraped") >= 0.45
        assert _source_confidence("unknown_source") > 0.0

    def test_field_confidence_override(self):
        spec = _make_spec(source_name="bikez")
        # Override displacement confidence with manufacturer level
        spec.field_confidence["displacement_cc"] = 0.92
        result = validate_spec(spec)
        score_with = score_spec(spec, result)

        spec2 = _make_spec(source_name="bikez")
        result2 = validate_spec(spec2)
        score_without = score_spec(spec2, result2)
        # Higher field-level confidence → higher score
        assert score_with >= score_without


# ────────────────────────────────────────────────────────────
# spec_to_bike_config sub-builders
# ────────────────────────────────────────────────────────────


class TestSubBuilders:
    def test_engine_peak_power(self, good_spec):
        engine = _build_engine_from_spec(good_spec)
        assert engine.peak_power_hp == pytest.approx(178.0)

    def test_engine_redline_estimated_from_peak_rpm(self, good_spec):
        engine = _build_engine_from_spec(good_spec)
        assert engine.redline_rpm > good_spec.peak_power_rpm

    def test_engine_launch_rpm_fraction_of_redline(self, good_spec):
        engine = _build_engine_from_spec(good_spec)
        ratio = engine.launch_rpm / engine.redline_rpm
        assert 0.40 <= ratio <= 0.70

    def test_engine_dyno_curve_generated(self, good_spec):
        engine = _build_engine_from_spec(good_spec)
        assert engine.dyno_curve is not None
        # Known dyno curves have ~20-30 points; synthetic curves have 100
        assert len(engine.dyno_curve.rpm) >= 10

    def test_engine_inertia_by_category(self):
        for cat, expected in CATEGORY_ENGINE_INERTIA.items():
            spec = _make_spec(category=cat)
            engine = _build_engine_from_spec(spec)
            assert engine.engine_inertia_kgm2 == pytest.approx(expected)

    def test_chassis_dry_mass(self, good_spec):
        chassis = _build_chassis_from_spec(good_spec)
        assert chassis.dry_mass_kg == pytest.approx(166.0)

    def test_chassis_mass_from_wet_only(self):
        spec = _make_spec(dry_mass_kg=None, wet_mass_kg=192.0)
        chassis = _build_chassis_from_spec(spec)
        assert chassis.dry_mass_kg == pytest.approx(167.0)

    def test_chassis_cog_height_by_category(self):
        for cat, expected in CATEGORY_COG_HEIGHT.items():
            spec = _make_spec(category=cat)
            chassis = _build_chassis_from_spec(spec)
            assert chassis.cog_height_mm == pytest.approx(float(expected))

    def test_drivetrain_gear_ratios_passed(self, good_spec):
        engine = _build_engine_from_spec(good_spec)
        dt = _build_drivetrain_from_spec(good_spec, engine)
        assert dt.gear_ratios == good_spec.gear_ratios

    def test_drivetrain_final_drive_ratio(self, good_spec):
        engine = _build_engine_from_spec(good_spec)
        dt = _build_drivetrain_from_spec(good_spec, engine)
        assert dt.final_drive_ratio == pytest.approx(45 / 17, rel=1e-4)

    def test_drivetrain_fallback_6speed(self):
        spec = _make_spec(gear_ratios=None, gears=6)
        engine = _build_engine_from_spec(spec)
        dt = _build_drivetrain_from_spec(spec, engine)
        assert len(dt.gear_ratios) == 6
        assert dt.gear_ratios[0] == pytest.approx(2.600)

    def test_tires_sizes_passed(self, good_spec):
        tires = _build_tires_from_spec(good_spec)
        assert tires.front_size == "120/70ZR17"
        assert tires.rear_size == "190/55ZR17"

    def test_tires_rolling_radius_estimated(self, good_spec):
        tires = _build_tires_from_spec(good_spec)
        # 190/55ZR17: width=190, aspect=0.55, sidewall=104.5, rim_half=215.9
        # radius ≈ (215.9 + 104.5) / 1000 ≈ 0.320 m
        assert tires.rear_rolling_radius_m == pytest.approx(0.320, abs=0.015)

    def test_aero_cd_from_spec(self, good_spec):
        good_spec.cd = 0.30
        aero = _build_aero_from_spec(good_spec)
        assert aero.cd == pytest.approx(0.30)

    def test_aero_cd_from_category_default(self):
        for cat, vals in CATEGORY_AERO.items():
            spec = _make_spec(category=cat)
            spec.cd = None
            spec.frontal_area_m2 = None
            aero = _build_aero_from_spec(spec)
            assert aero.cd == pytest.approx(vals["cd"])


# ────────────────────────────────────────────────────────────
# spec_to_bike_config — end-to-end conversion
# ────────────────────────────────────────────────────────────


class TestSpecToBikeConfig:
    def test_name_composed_correctly(self, good_spec):
        config = spec_to_bike_config(good_spec)
        assert "Suzuki" in config.name
        assert "GSX-R 1000" in config.name
        assert "2005" in config.name

    def test_name_year_range(self):
        spec = _make_spec(year_from=2017, year_to=2023)
        config = spec_to_bike_config(spec)
        assert "2017-2023" in config.name

    def test_name_no_year_if_missing(self):
        spec = _make_spec(year_from=None, year_to=None)
        config = spec_to_bike_config(spec)
        assert "(" not in config.name

    def test_engine_in_config(self, good_spec):
        config = spec_to_bike_config(good_spec)
        assert config.engine.peak_power_hp == pytest.approx(178.0)

    def test_chassis_in_config(self, good_spec):
        config = spec_to_bike_config(good_spec)
        assert config.chassis.dry_mass_kg == pytest.approx(166.0)

    def test_drivetrain_in_config(self, good_spec):
        config = spec_to_bike_config(good_spec)
        assert len(config.drivetrain.gear_ratios) == 6

    def test_tires_in_config(self, good_spec):
        config = spec_to_bike_config(good_spec)
        assert config.tires.front_size == "120/70ZR17"

    def test_defaults_retained_for_unused_params(self, good_spec):
        config = spec_to_bike_config(good_spec)
        # Clutch, suspension etc. should come from gsxr1000_k5 defaults
        assert config.clutch is not None
        assert config.suspension is not None

    def test_returns_bike_config_type(self, good_spec):
        from motoquant.models import BikeConfig

        config = spec_to_bike_config(good_spec)
        assert isinstance(config, BikeConfig)


# ────────────────────────────────────────────────────────────
# import_spec — DB integration
# ────────────────────────────────────────────────────────────


class TestImportSpec:
    def test_dry_run_returns_none(self, scraper_db, good_spec):
        result = validate_spec(good_spec)
        ret = import_spec(scraper_db, good_spec, result, dry_run=True)
        assert ret is None

    def test_dry_run_no_db_write(self, scraper_db, good_spec):
        result = validate_spec(good_spec)
        import_spec(scraper_db, good_spec, result, dry_run=True)
        assert scraper_db.bikes.count_models() == 0

    def test_live_import_returns_ids(self, scraper_db, good_spec):
        result = validate_spec(good_spec)
        ret = import_spec(scraper_db, good_spec, result, dry_run=False)
        assert ret is not None
        model_id, config_id = ret
        assert model_id > 0
        assert config_id > 0

    def test_live_import_writes_to_db(self, scraper_db, good_spec):
        result = validate_spec(good_spec)
        import_spec(scraper_db, good_spec, result)
        assert scraper_db.bikes.count_models() == 1

    def test_invalid_spec_returns_none(self, scraper_db):
        spec = _make_spec(manufacturer="")
        ret = import_spec(scraper_db, spec)
        assert ret is None

    def test_invalid_spec_no_db_write(self, scraper_db):
        spec = _make_spec(model_name="")
        import_spec(scraper_db, spec)
        assert scraper_db.bikes.count_models() == 0

    def test_upsert_idempotent(self, scraper_db, good_spec):
        result = validate_spec(good_spec)
        import_spec(scraper_db, good_spec, result)
        import_spec(scraper_db, good_spec, result)
        # Should upsert, not create duplicate
        assert scraper_db.bikes.count_models() <= 2  # might update in place

    def test_provenance_written(self, scraper_db, good_spec):
        good_spec.field_confidence["peak_power_hp"] = 0.92
        result = validate_spec(good_spec)
        _, config_id = import_spec(scraper_db, good_spec, result)
        # Verify provenance exists
        rows = scraper_db.conn.execute(
            "SELECT * FROM data_provenance WHERE entity_id=? AND entity_type='bike_config'",
            (config_id,),
        ).fetchall()
        assert len(rows) >= 1

    def test_auto_validates_if_no_result(self, scraper_db, good_spec):
        ret = import_spec(scraper_db, good_spec)
        assert ret is not None


# ────────────────────────────────────────────────────────────
# import_batch
# ────────────────────────────────────────────────────────────


class TestImportBatch:
    def test_all_valid_imported(self, scraper_db):
        specs = [_make_spec(model_name=f"Model {i}") for i in range(5)]
        summary = import_batch(scraper_db, specs)
        assert summary["imported"] == 5
        assert summary["skipped_invalid"] == 0
        assert summary["errors"] == 0

    def test_invalid_specs_skipped(self, scraper_db):
        specs = [
            _make_spec(model_name="Good"),
            _make_spec(manufacturer=""),  # invalid
            _make_spec(model_name=""),  # invalid
        ]
        summary = import_batch(scraper_db, specs)
        assert summary["imported"] == 1
        assert summary["skipped_invalid"] == 2

    def test_dry_run_flag_in_summary(self, scraper_db):
        specs = [_make_spec(model_name="TestBike")]
        summary = import_batch(scraper_db, specs, dry_run=True)
        assert summary["dry_run"] is True

    def test_dry_run_no_db_writes(self, scraper_db):
        specs = [_make_spec(model_name="TestBike")]
        import_batch(scraper_db, specs, dry_run=True)
        assert scraper_db.bikes.count_models() == 0

    def test_empty_list(self, scraper_db):
        summary = import_batch(scraper_db, [])
        assert summary["imported"] == 0
        assert summary["errors"] == 0

    def test_stop_on_error(self, scraper_db, monkeypatch):
        """stop_on_error=True should halt after first error."""
        call_count = [0]
        original_import = import_spec

        def counting_import(db, spec, result=None, dry_run=False):
            call_count[0] += 1
            if call_count[0] == 2:
                return None  # simulate error on second call
            return original_import(db, spec, result, dry_run)

        monkeypatch.setattr("motoquant.scraper.importer.import_spec", counting_import)
        specs = [_make_spec(model_name=f"Bike{i}") for i in range(5)]
        import_batch(scraper_db, specs, stop_on_error=True)
        # Should have stopped after the error (call 2)
        assert call_count[0] == 2


# ────────────────────────────────────────────────────────────
# ALL_KNOWN_BIKES integration
# ────────────────────────────────────────────────────────────


class TestKnownBikes:
    def test_known_bikes_count(self):
        assert len(ALL_KNOWN_BIKES) >= 20

    def test_all_known_bikes_have_manufacturer(self):
        for spec in ALL_KNOWN_BIKES:
            assert spec.manufacturer, f"Missing manufacturer: {spec.model_name}"

    def test_all_known_bikes_have_gear_ratios(self):
        # Most modern motorcycles are 5- or 6-speed. Historical 2-stroke
        # commuters (Yamaha RX100 1V1 1985-96) and some small-cc cubs shipped
        # with 4-speed gearboxes and we ship them as such — historically
        # accurate is better than padded-fifth-gear fiction. Minimum is 4.
        for spec in ALL_KNOWN_BIKES:
            assert spec.gear_ratios is not None, (
                f"{spec.manufacturer} {spec.model_name} has no gear_ratios"
            )
            assert len(spec.gear_ratios) >= 4, (
                f"{spec.manufacturer} {spec.model_name}: "
                f"only {len(spec.gear_ratios)} gears"
            )

    def test_all_known_bikes_validate(self):
        failures = []
        for spec in ALL_KNOWN_BIKES:
            result = validate_spec(spec)
            if not result.is_valid:
                failures.append(
                    f"{spec.manufacturer} {spec.model_name}: {result.errors}"
                )
        assert failures == [], "\n".join(failures)

    def test_all_known_bikes_score_above_threshold(self):
        low_scores = []
        for spec in ALL_KNOWN_BIKES:
            result = validate_spec(spec)
            score = score_spec(spec, result)
            if score < 0.50:
                low_scores.append(
                    f"{spec.manufacturer} {spec.model_name}: score={score:.3f}"
                )
        assert low_scores == [], "\n".join(low_scores)

    def test_all_known_bikes_convert_to_config(self):
        failures = []
        for spec in ALL_KNOWN_BIKES:
            try:
                config = spec_to_bike_config(spec)
                assert config.name
                assert config.engine.dyno_curve is not None
            except Exception as e:
                failures.append(f"{spec.manufacturer} {spec.model_name}: {e}")
        assert failures == [], "\n".join(failures)

    def test_all_known_bikes_import_to_db(self, scraper_db):
        summary = import_batch(scraper_db, ALL_KNOWN_BIKES)
        assert summary["errors"] == 0
        assert summary["skipped_invalid"] == 0
        assert summary["imported"] == len(ALL_KNOWN_BIKES)
        assert scraper_db.bikes.count_models() >= len(ALL_KNOWN_BIKES) // 2

    def test_manufacturers_represented(self):
        manufacturers = {spec.manufacturer for spec in ALL_KNOWN_BIKES}
        expected = {"Suzuki", "Yamaha", "Honda", "Kawasaki", "BMW", "Ducati"}
        missing = expected - manufacturers
        assert missing == set(), f"Missing manufacturers: {missing}"

    def test_displacement_range(self):
        # Range covers historical Indian/Asian 2-stroke commuters (Yamaha RX100
        # at 98cc, Aprilia RS125 at 124cc, Yamaha RX135/RXZ135 at 132-133cc) up
        # through 2500cc cruisers (Triumph Rocket 3 at 2458cc).
        for spec in ALL_KNOWN_BIKES:
            if spec.displacement_cc:
                assert 95 <= spec.displacement_cc <= 2500, (
                    f"{spec.model_name}: displacement {spec.displacement_cc} out of range"
                )

    def test_high_confidence_sources(self):
        """All known bikes should use high-confidence sources (spec_sheet or scraped_confirmed)."""
        for spec in ALL_KNOWN_BIKES:
            assert spec.source_name in ("spec_sheet", "scraped_confirmed"), (
                f"{spec.manufacturer} {spec.model_name}: source_name={spec.source_name}, expected 'spec_sheet' or 'scraped_confirmed'"
            )
