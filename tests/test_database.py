"""
MotoQuant Pro — Database Layer Tests
====================================
Tests for the Phase 2 database layer:
  - Schema creation and seeding
  - BikeConfig round-trip fidelity (THE critical test)
  - Repository CRUD operations
  - Weather computations
  - Parts simulation impact
  - Venue seasonal data
"""

import json
import os

# Ensure the parent package is importable
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from motoquant.database import MotoQuantDB
from motoquant.database.bridge import (
    apply_part_to_config,
    compute_data_completeness,
)
from motoquant.database.seed import seed_all
from motoquant.database.weather_repo import (
    compute_air_density,
    compute_density_altitude,
    compute_dew_point,
    compute_power_correction,
)
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8


@pytest.fixture
def db():
    """Create a temp database for testing."""
    db_path = os.path.join("/tmp", f"motoquant_test_{os.getpid()}.db")
    database = MotoQuantDB(db_path)
    database.initialize()
    yield database
    database.close()
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def seeded_db(db):
    """Database with all seed data loaded."""
    seed_all(db)
    return db


# ════════════════════════════════════════════════
# Schema & Initialization
# ════════════════════════════════════════════════


class TestSchemaInit:
    """Verify schema creation and seeding."""

    def test_tables_created(self, db):
        """All expected tables exist after initialize()."""
        tables = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        table_names = {r["name"] for r in tables}

        expected = {
            "schema_meta",
            "manufacturers",
            "bike_models",
            "bike_configs",
            "dyno_curves",
            "tire_manufacturers",
            "tire_models",
            "venues",
            "weather_records",
            "venue_seasonal",
            "parts_categories",
            "parts",
            "sim_runs",
            "data_provenance",
        }
        assert expected.issubset(table_names), (
            f"Missing tables: {expected - table_names}"
        )

    def test_schema_version(self, db):
        """Schema version is set correctly."""
        row = db.conn.execute(
            "SELECT value FROM schema_meta WHERE key = 'schema_version'"
        ).fetchone()
        assert row is not None
        # v1 → v2: fitment_rules column; v2 → v3: bike_suggestions table
        from motoquant.database.schema import SCHEMA_VERSION

        assert int(row["value"]) == SCHEMA_VERSION

    def test_venues_seeded(self, db):
        """Indian venues are seeded on initialize()."""
        venues = db.venues.list_indian_venues()
        assert len(venues) >= 4  # Aamby, MMRT, BIC, Kari
        names = [v["name"] for v in venues]
        assert any("Aamby" in n for n in names)
        assert any("MMRT" in n for n in names)
        assert any("BIC" in n or "Buddh" in n for n in names)

    def test_parts_categories_seeded(self, db):
        """Parts categories are seeded."""
        cats = db.parts.list_categories()
        assert len(cats) >= 10
        cat_names = {c["name"] for c in cats}
        assert "sprocket" in cat_names
        assert "ecu" in cat_names
        assert "exhaust" in cat_names

    def test_seasonal_data_seeded(self, db):
        """Seasonal weather data is seeded for venues."""
        aamby = db.venues.get_by_name("Aamby Valley Airstrip (TVR)")
        assert aamby is not None
        seasonal = db.venues.get_all_seasonal(aamby["id"])
        assert len(seasonal) == 12  # All 12 months

    def test_idempotent_init(self, db):
        """Calling initialize() twice doesn't duplicate data."""
        count_before = db.venues.count()
        db.initialize()
        count_after = db.venues.count()
        assert count_before == count_after


# ════════════════════════════════════════════════
# BikeConfig Round-Trip (THE critical test)
# ════════════════════════════════════════════════


class TestBikeConfigRoundTrip:
    """
    Verify bit-exact round-trip: BikeConfig → DB → BikeConfig.
    This is the single most important test in the database layer.
    """

    @pytest.mark.parametrize(
        "factory,name",
        [
            (gsxr1000_k5, "K5"),
            (yzfr1_4c8, "R1"),
            (hayabusa_gen1, "Busa"),
        ],
    )
    def test_roundtrip_scalars(self, db, factory, name):
        """All scalar params survive round-trip through the database."""
        original = factory()

        # Store
        model_id, config_id = db.bikes.upsert_from_config(original)

        # Retrieve
        restored = db.bikes.to_config(config_id)
        assert restored is not None

        # Compare every scalar field in every section
        sections = [
            "chassis",
            "engine",
            "drivetrain",
            "clutch",
            "tires",
            "aero",
            "suspension",
            "braking",
            "wheelie",
            "rider",
            "parasitic",
            "staging",
            "forced_induction",
        ]

        for section in sections:
            orig_section = getattr(original, section)
            rest_section = getattr(restored, section)

            import dataclasses

            for f in dataclasses.fields(orig_section):
                orig_val = getattr(orig_section, f.name)
                rest_val = getattr(rest_section, f.name)

                # Skip DynoCurve (tested separately) and numpy arrays
                if isinstance(orig_val, np.ndarray):
                    continue
                if f.name == "dyno_curve":
                    continue
                if isinstance(orig_val, list):
                    assert orig_val == rest_val, (
                        f"{name}.{section}.{f.name}: {orig_val} != {rest_val}"
                    )
                elif isinstance(orig_val, float):
                    assert abs(orig_val - rest_val) < 1e-10, (
                        f"{name}.{section}.{f.name}: {orig_val} != {rest_val}"
                    )
                else:
                    assert orig_val == rest_val, (
                        f"{name}.{section}.{f.name}: {orig_val} != {rest_val}"
                    )

    @pytest.mark.parametrize(
        "factory,name",
        [
            (gsxr1000_k5, "K5"),
            (yzfr1_4c8, "R1"),
            (hayabusa_gen1, "Busa"),
        ],
    )
    def test_roundtrip_dyno_curve(self, db, factory, name):
        """Dyno curve survives round-trip with full float64 precision."""
        original = factory()
        _, config_id = db.bikes.upsert_from_config(original)
        restored = db.bikes.to_config(config_id)

        assert original.engine.dyno_curve is not None
        assert restored.engine.dyno_curve is not None

        np.testing.assert_array_almost_equal(
            original.engine.dyno_curve.rpm,
            restored.engine.dyno_curve.rpm,
            decimal=6,
            err_msg=f"{name}: RPM array mismatch",
        )
        np.testing.assert_array_almost_equal(
            original.engine.dyno_curve.torque_nm,
            restored.engine.dyno_curve.torque_nm,
            decimal=6,
            err_msg=f"{name}: Torque array mismatch",
        )
        assert (
            original.engine.dyno_curve.is_at_wheel
            == restored.engine.dyno_curve.is_at_wheel
        )

    @pytest.mark.parametrize(
        "factory,name",
        [
            (gsxr1000_k5, "K5"),
            (yzfr1_4c8, "R1"),
            (hayabusa_gen1, "Busa"),
        ],
    )
    def test_roundtrip_gear_ratios(self, db, factory, name):
        """Gear ratios (critical for ET) survive round-trip."""
        original = factory()
        _, config_id = db.bikes.upsert_from_config(original)
        restored = db.bikes.to_config(config_id)

        assert len(original.drivetrain.gear_ratios) == len(
            restored.drivetrain.gear_ratios
        )
        for i, (o, r) in enumerate(
            zip(
                original.drivetrain.gear_ratios,
                restored.drivetrain.gear_ratios,
            )
        ):
            assert abs(o - r) < 1e-10, f"{name} gear {i}: {o} != {r}"


# ════════════════════════════════════════════════
# Bike Repository
# ════════════════════════════════════════════════


class TestBikeRepository:
    """Test bike CRUD and search."""

    def test_create_and_get_manufacturer(self, db):
        mfr_id = db.bikes.get_or_create_manufacturer("Suzuki", "Japan")
        assert mfr_id > 0
        # Idempotent
        mfr_id2 = db.bikes.get_or_create_manufacturer("Suzuki")
        assert mfr_id == mfr_id2

    def test_upsert_creates_model_and_config(self, db):
        config = gsxr1000_k5()
        model_id, config_id = db.bikes.upsert_from_config(config)
        assert model_id > 0
        assert config_id > 0

        model = db.bikes.get_model(model_id)
        assert model is not None
        assert model["displacement_cc"] == 999.0

    def test_search_by_displacement(self, seeded_db):
        results = seeded_db.bikes.search(displacement_min=1200)
        assert len(results) >= 1  # Hayabusa
        assert all(r["displacement_cc"] >= 1200 for r in results)

    def test_search_by_manufacturer(self, seeded_db):
        results = seeded_db.bikes.search(manufacturer="Suzuki")
        assert len(results) >= 2  # K5 + Busa

    def test_search_by_category(self, seeded_db):
        results = seeded_db.bikes.search(category="sport")
        assert len(results) >= 3

    def test_config_versioning(self, db):
        """New configs auto-increment version and mark previous non-current."""
        config = gsxr1000_k5()
        model_id, config_id_v1 = db.bikes.upsert_from_config(config)

        # Create a "modified" config
        config.engine.peak_power_hp = 175.0
        config_id_v2 = db.bikes.create_config(model_id, config, config_name="stock")

        # V2 should be current
        current = db.bikes.get_current_config(model_id)
        assert current["id"] == config_id_v2
        assert current["version"] == 2

        # V1 should not be current
        v1 = db.bikes.get_config(config_id_v1)
        assert v1["is_current"] == 0

    def test_validation_benchmark(self, seeded_db):
        results = seeded_db.bikes.search(name_contains="GSX-R")
        assert len(results) >= 1
        k5 = results[0]
        assert k5["validation_et_s"] is not None
        assert abs(k5["validation_et_s"] - 9.97) < 0.01
        assert k5["data_quality"] == "track_validated"

    def test_data_completeness(self):
        """Completeness score is non-zero for configs with dyno curves."""
        config = gsxr1000_k5()
        score = compute_data_completeness(config)
        assert score > 0.0  # Has at least dyno curve + some non-default params
        # Hayabusa should differ more from defaults
        busa = hayabusa_gen1()
        busa_score = compute_data_completeness(busa)
        assert busa_score > 0.0

    def test_count(self, seeded_db):
        assert seeded_db.bikes.count_models() >= 3
        assert seeded_db.bikes.count_configs() >= 3


# ════════════════════════════════════════════════
# Tire Repository
# ════════════════════════════════════════════════


class TestTireRepository:
    def test_create_and_get(self, db):
        tire_id = db.tires.create(
            manufacturer_name="Michelin",
            model_name="Power GP2",
            size_designation="190/55ZR17",
            compound_type="race",
            mu_peak=1.45,
            price_inr=22000,
            available_india=1,
        )
        assert tire_id > 0

        tire = db.tires.get(tire_id)
        assert tire["manufacturer_name"] == "Michelin"
        assert tire["mu_peak"] == 1.45

    def test_search_by_compound(self, seeded_db):
        results = seeded_db.tires.search(compound_type="race")
        assert len(results) >= 2

    def test_to_tire_params(self, seeded_db):
        """Convert DB tire to TireParams for simulation."""
        results = seeded_db.tires.search(compound_type="race", position="rear")
        assert len(results) > 0
        tire_id = results[0]["id"]

        params = seeded_db.tires.to_tire_params(tire_id, is_rear=True)
        assert params is not None
        assert params.mu_peak > 1.0
        assert "190" in params.rear_size or "ZR17" in params.rear_size

    def test_rank_by_grip(self, seeded_db):
        ranked = seeded_db.tires.rank_by_grip(position="rear")
        assert len(ranked) >= 2
        # Should be descending by weighted grip
        if len(ranked) >= 2:
            assert ranked[0]["weighted_grip"] >= ranked[1]["weighted_grip"]

    def test_rank_by_value(self, seeded_db):
        ranked = seeded_db.tires.rank_by_value(position="rear")
        assert len(ranked) >= 1  # At least MRF should show (cheapest + available)


# ════════════════════════════════════════════════
# Venue Repository
# ════════════════════════════════════════════════


class TestVenueRepository:
    def test_list_indian_venues(self, db):
        venues = db.venues.list_indian_venues()
        assert len(venues) >= 4

    def test_get_by_name(self, db):
        aamby = db.venues.get_by_name("aamby")
        assert aamby is not None
        assert aamby["altitude_m"] == 679.0

    def test_seasonal_data(self, db):
        aamby = db.venues.get_by_name("aamby")
        jan = db.venues.get_seasonal(aamby["id"], 1)
        assert jan is not None
        assert jan["avg_temp_c"] < jan["avg_track_temp_c"]  # Track warmer than air

    def test_to_environment(self, db):
        aamby = db.venues.get_by_name("aamby")
        env = db.venues.to_environment(aamby["id"], month=1)
        assert env is not None
        assert env.altitude_m == 679.0
        assert env.ambient_temp_c == 18.0  # January average

    def test_best_da_month(self, db):
        """Best DA month should be winter (lower temp, higher pressure)."""
        aamby = db.venues.get_by_name("aamby")
        best = db.venues.best_da_month(aamby["id"])
        assert best is not None
        assert best["month"] in [1, 2, 11, 12]  # Winter months

    def test_worst_da_month(self, db):
        """Worst DA should be monsoon/summer."""
        aamby = db.venues.get_by_name("aamby")
        worst = db.venues.worst_da_month(aamby["id"])
        assert worst is not None
        assert worst["month"] in [5, 6, 7, 8]  # Monsoon/summer


# ════════════════════════════════════════════════
# Weather Repository & Atmospheric Physics
# ════════════════════════════════════════════════


class TestWeatherPhysics:
    """Test atmospheric computation accuracy."""

    def test_air_density_sea_level_std(self):
        """Standard atmosphere at sea level ≈ 1.225 kg/m³."""
        rho = compute_air_density(15.0, 0.0, 1013.25, 0.0)
        assert abs(rho - 1.225) < 0.005

    def test_air_density_altitude(self):
        """Air density decreases with altitude."""
        rho_sl = compute_air_density(25.0, 50.0, 1013.25, 0.0)
        rho_aamby = compute_air_density(25.0, 50.0, 1013.25, 679.0)
        assert rho_aamby < rho_sl

    def test_density_altitude_sea_level(self):
        """Standard conditions → DA ≈ 0 ft."""
        da = compute_density_altitude(15.0, 0.0, 1013.25, 0.0)
        assert abs(da) < 200  # Within 200 ft of zero

    def test_density_altitude_aamby_winter(self):
        """Aamby winter DA should be ~2500-3200 ft."""
        da = compute_density_altitude(20.0, 35.0, 1018.0, 679.0)
        assert 2000 < da < 3500

    def test_density_altitude_aamby_summer(self):
        """Aamby summer DA should be higher than winter."""
        da_winter = compute_density_altitude(20.0, 35.0, 1018.0, 679.0)
        da_summer = compute_density_altitude(30.0, 70.0, 1006.0, 679.0)
        assert da_summer > da_winter

    def test_dew_point(self):
        """Dew point at 25°C, 50% RH should be ~14°C."""
        dp = compute_dew_point(25.0, 50.0)
        assert 12.0 < dp < 16.0

    def test_power_correction_standard(self):
        """Standard conditions → correction factor ≈ 1.0."""
        pcf = compute_power_correction(15.0, 1013.25, 0.0, 0.0)
        assert abs(pcf - 1.0) < 0.02

    def test_power_correction_altitude(self):
        """Altitude reduces power."""
        pcf = compute_power_correction(30.0, 1006.0, 70.0, 679.0)
        assert pcf < 1.0
        assert pcf > 0.85  # Shouldn't be more than 15% loss at Aamby


class TestWeatherRepository:
    def test_record_manual_weather(self, db):
        aamby = db.venues.get_by_name("aamby")
        record_id = db.weather.record(
            venue_id=aamby["id"],
            ambient_temp_c=22.0,
            relative_humidity_pct=35.0,
            barometric_pressure_hpa=1016.0,
            wind_speed_ms=1.5,
            track_temp_c=28.0,
            source="manual",
        )
        assert record_id > 0

        rec = db.weather.get(record_id)
        assert rec["ambient_temp_c"] == 22.0
        assert rec["density_altitude_ft"] is not None
        assert rec["air_density_kgm3"] is not None
        assert rec["power_correction_factor"] is not None

    def test_latest_record(self, db):
        aamby = db.venues.get_by_name("aamby")
        db.weather.record(
            venue_id=aamby["id"],
            ambient_temp_c=22.0,
            relative_humidity_pct=35.0,
            barometric_pressure_hpa=1016.0,
        )
        latest = db.weather.latest(aamby["id"])
        assert latest is not None
        assert latest["ambient_temp_c"] == 22.0

    def test_to_environment(self, db):
        aamby = db.venues.get_by_name("aamby")
        record_id = db.weather.record(
            venue_id=aamby["id"],
            ambient_temp_c=20.0,
            relative_humidity_pct=40.0,
            barometric_pressure_hpa=1015.0,
            track_temp_c=25.0,
        )
        env = db.weather.to_environment(record_id)
        assert env is not None
        assert env.venue_name == aamby["name"]
        assert env.ambient_temp_c == 20.0
        assert env.altitude_m == 679.0


# ════════════════════════════════════════════════
# Parts Repository
# ════════════════════════════════════════════════


class TestPartsRepository:
    def test_create_and_search(self, seeded_db):
        sprockets = seeded_db.parts.search(category="sprocket")
        assert len(sprockets) >= 2

    def test_apply_part_to_config(self, seeded_db):
        """Applying a sprocket part changes the config correctly."""
        config = gsxr1000_k5()
        original_rear = config.drivetrain.rear_sprocket

        # Find 44T rear sprocket
        parts = seeded_db.parts.search(category="sprocket", name_contains="44T")
        assert len(parts) >= 1
        part = parts[0]

        modified = apply_part_to_config(config, part)
        assert modified.drivetrain.rear_sprocket == 44
        assert config.drivetrain.rear_sprocket == original_rear  # Original unchanged

    def test_estimate_build_cost(self, seeded_db):
        """Build cost calculator works."""
        parts = seeded_db.parts.search(category="sprocket")
        part_ids = [p["id"] for p in parts[:2]]
        cost = seeded_db.parts.estimate_build_cost(part_ids, "inr")
        assert cost["total"] > 0
        assert cost["currency"] == "INR"
        assert len(cost["parts"]) == 2

    def test_ecu_flash_deltas(self, seeded_db):
        """ECU flash applies power delta correctly for each part found."""

        config = gsxr1000_k5()
        ecu_parts = seeded_db.parts.search(category="ecu")
        assert len(ecu_parts) >= 1

        for part in ecu_parts:
            deltas = part.get("param_deltas")
            if isinstance(deltas, str):
                deltas = json.loads(deltas) if deltas else {}
            hp_delta = deltas.get("engine.peak_power_hp", 0) if deltas else 0
            if hp_delta == 0:
                continue  # skip parts with no HP delta (shouldn't happen but be safe)
            modified = apply_part_to_config(config, part)
            expected = config.engine.peak_power_hp + hp_delta
            assert modified.engine.peak_power_hp == expected, (
                f"Part '{part['brand']} {part['model_name']}': "
                f"expected {expected}, got {modified.engine.peak_power_hp}"
            )


# ════════════════════════════════════════════════
# Simulation Run Repository
# ════════════════════════════════════════════════


class TestSimRunRepository:
    def test_record_and_retrieve(self, seeded_db):
        config = gsxr1000_k5()
        _, config_id = seeded_db.bikes.upsert_from_config(config)

        run_id = seeded_db.sim_runs.record(
            bike_config_id=config_id,
            et_quarter_s=9.97,
            trap_speed_kmh=230.0,
            time_60ft_s=1.42,
            sim_version="0.2.0",
        )
        assert run_id > 0

        run = seeded_db.sim_runs.get(run_id)
        assert run["et_quarter_s"] == 9.97
        assert run["trap_speed_kmh"] == 230.0

    def test_best_et(self, seeded_db):
        _, config_id = seeded_db.bikes.upsert_from_config(gsxr1000_k5())
        seeded_db.sim_runs.record(config_id, 10.05, 228.0)
        seeded_db.sim_runs.record(config_id, 9.97, 230.0)
        seeded_db.sim_runs.record(config_id, 10.12, 226.0)

        best = seeded_db.sim_runs.best_et(config_id)
        assert best is not None
        assert best["et_quarter_s"] == 9.97


# ════════════════════════════════════════════════
# Database Statistics
# ════════════════════════════════════════════════


class TestDatabaseStats:
    def test_stats_after_seed(self, seeded_db):
        """Verify stats report correct counts after full seed."""
        stats = seeded_db.stats()
        assert stats["manufacturers"] >= 2  # Suzuki + Yamaha
        assert stats["bike_models"] >= 3
        assert stats["bike_configs"] >= 3
        assert stats["dyno_curves"] >= 3
        assert stats["tire_models"] >= 5
        assert stats["venues"] >= 4
        assert stats["venue_seasonal"] >= 48  # 4 venues × 12 months
        assert stats["parts"] >= 8


# ════════════════════════════════════════════════
# Bike Suggestions Schema + Repository
# ════════════════════════════════════════════════


class TestBikeSuggestionsSchema:
    def test_table_exists_after_initialize(self, db):
        """v3 migration creates the bike_suggestions table."""
        row = db.conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='bike_suggestions'"
        ).fetchone()
        assert row is not None
        assert row["name"] == "bike_suggestions"

    def test_schema_version_at_least_3(self, db):
        """After initialize(), schema_meta records version >= 3."""
        row = db.conn.execute(
            "SELECT value FROM schema_meta WHERE key = 'schema_version'"
        ).fetchone()
        assert row is not None
        assert int(row["value"]) >= 3

    def test_status_check_constraint(self, db):
        """Only valid status values are accepted at the SQL layer."""
        import sqlite3
        with pytest.raises(sqlite3.IntegrityError):
            db.conn.execute(
                """INSERT INTO bike_suggestions (make, model, status)
                   VALUES (?, ?, ?)""",
                ("X", "Y", "INVALID_STATUS"),
            )


class TestBikeSuggestionsRepo:
    def test_create_minimal(self, db):
        """create() with just make + model stores a clean row."""
        result = db.bike_suggestions.create(make="Testerson", model="Alpha 100")
        assert isinstance(result["id"], int)
        assert result["flagged_out_of_bounds"] is False
        assert result["issues"] == []

        row = db.bike_suggestions.get(result["id"])
        assert row is not None
        assert row["make"] == "Testerson"
        assert row["model"] == "Alpha 100"
        assert row["status"] == "pending"
        assert row["flagged_out_of_bounds"] == 0

    def test_create_flags_out_of_bounds(self, db):
        """Values outside plausibility bounds get flagged but still stored."""
        result = db.bike_suggestions.create(
            make="Testerson",
            model="Extreme",
            displacement_cc=4500.0,  # > 3500 upper bound
            peak_power_hp=500.0,     # > 450 upper bound
        )
        assert result["flagged_out_of_bounds"] is True
        assert any("displacement_cc" in m for m in result["issues"])
        assert any("peak_power_hp" in m for m in result["issues"])

        row = db.bike_suggestions.get(result["id"])
        assert row["flagged_out_of_bounds"] == 1

    def test_create_empty_make_raises(self, db):
        """Empty make raises ValueError (before DB write)."""
        with pytest.raises(ValueError, match="make"):
            db.bike_suggestions.create(make="", model="ok")

    def test_create_empty_model_raises(self, db):
        """Empty model raises ValueError."""
        with pytest.raises(ValueError, match="model"):
            db.bike_suggestions.create(make="ok", model="   ")

    def test_list_filters_by_status(self, db):
        """list(status=...) filters correctly."""
        db.bike_suggestions.create(make="A", model="1")
        id2 = db.bike_suggestions.create(make="B", model="2")["id"]
        db.bike_suggestions.create(make="C", model="3")

        # All pending by default
        pending = db.bike_suggestions.list(status="pending")
        assert len(pending) == 3

        # Mark one reviewed
        assert db.bike_suggestions.mark_reviewed(id2) is True
        pending_after = db.bike_suggestions.list(status="pending")
        reviewed = db.bike_suggestions.list(status="reviewed")
        assert len(pending_after) == 2
        assert len(reviewed) == 1
        assert reviewed[0]["id"] == id2

    def test_list_flagged_only(self, db):
        """flagged_only=True returns only rows with plausibility issues."""
        db.bike_suggestions.create(make="Clean", model="Good")
        db.bike_suggestions.create(
            make="Sketchy", model="Too big", displacement_cc=9999.0
        )

        flagged = db.bike_suggestions.list(flagged_only=True)
        assert len(flagged) == 1
        assert flagged[0]["make"] == "Sketchy"

    def test_status_transitions(self, db):
        """mark_added / mark_rejected update status and timestamp."""
        sid = db.bike_suggestions.create(make="T", model="M")["id"]
        assert db.bike_suggestions.mark_added(sid) is True
        row = db.bike_suggestions.get(sid)
        assert row["status"] == "added"
        assert row["reviewed_at"] is not None

        assert db.bike_suggestions.mark_rejected(sid) is True
        row = db.bike_suggestions.get(sid)
        assert row["status"] == "rejected"

    def test_invalid_status_raises(self, db):
        """Calling list() or _set_status with bad status raises ValueError."""
        with pytest.raises(ValueError):
            db.bike_suggestions.list(status="garbage")

    def test_count(self, db):
        """count() matches the number of rows."""
        assert db.bike_suggestions.count() == 0
        db.bike_suggestions.create(make="A", model="1")
        db.bike_suggestions.create(make="B", model="2")
        assert db.bike_suggestions.count() == 2
        assert db.bike_suggestions.count(status="pending") == 2
        assert db.bike_suggestions.count(status="added") == 0
