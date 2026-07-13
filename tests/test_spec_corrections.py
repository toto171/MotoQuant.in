"""
tests/test_spec_corrections.py
==============================
Tests for the data-quality + spec-correction submission feature.

Covers:
  - Schema migration (fresh DB and existing v3 DB)
  - SpecCorrectionsRepository CRUD
  - Status transitions (approve / reject)
  - Invalid-field and missing-bike validation
  - FastAPI endpoints: POST /api/specs/correct, GET /api/specs/correction-fields
  - Reference baseline preservation (K5 / R1 / Hayabusa)
"""

import os
import sys
import tempfile
import unittest

# ── Make sure the project root is on sys.path ─────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _fresh_db_path():
    """Return a path to a *new* temp file (deleted when the test is done)."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.unlink(path)  # MotoQuantDB will recreate it
    return path


def _open_mq_db(path):
    """Open and fully initialize a MotoQuantDB (DELETE journal for FUSE compat)."""
    from motoquant.database.connection import MotoQuantDB

    db = MotoQuantDB(path)
    # Force DELETE journal mode before initialize() touches the DB.
    # connect() is called lazily; we call it explicitly first so we can flip the
    # journal mode before executescript() runs inside initialize().
    conn = db.connect()
    try:
        conn.execute("PRAGMA journal_mode=DELETE")
    except Exception:
        pass
    db.initialize()
    return db


def _seed_one_bike(db, model_name="TestBike"):
    """Insert a minimal bike_model row so FK constraints can be satisfied.

    Pass a distinct ``model_name`` to seed multiple test bikes that don't
    collide on the SELECT-by-name lookup at the end.
    """
    conn = db.conn
    # Ensure a manufacturer exists
    conn.execute("INSERT OR IGNORE INTO manufacturers (name) VALUES ('TestMaker')")
    mfr_id = conn.execute(
        "SELECT id FROM manufacturers WHERE name = 'TestMaker'"
    ).fetchone()[0]
    conn.execute(
        """INSERT INTO bike_models
               (manufacturer_id, model_name, year_from, category)
           VALUES (?, ?, 2020, 'sport')""",
        (mfr_id, model_name),
    )
    conn.commit()
    return conn.execute(
        "SELECT id FROM bike_models WHERE model_name = ? ORDER BY id DESC LIMIT 1",
        (model_name,),
    ).fetchone()[0]


# ─────────────────────────────────────────────────────────────────────────────
# 1. Schema migration — fresh DB
# ─────────────────────────────────────────────────────────────────────────────


class TestSchemaMigrationFresh(unittest.TestCase):
    """On a brand-new DB the schema must include spec_corrections + data_source."""

    def setUp(self):
        self.db_path = _fresh_db_path()
        self.db = _open_mq_db(self.db_path)

    def tearDown(self):
        self.db.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_spec_corrections_table_exists(self):
        row = self.db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='spec_corrections'"
        ).fetchone()
        self.assertIsNotNone(row, "spec_corrections table should exist on fresh DB")

    def test_spec_corrections_columns(self):
        cols = {
            r[1] for r in self.db.conn.execute("PRAGMA table_info(spec_corrections)")
        }
        required = {
            "id",
            "bike_model_id",
            "field_name",
            "current_value",
            "proposed_value",
            "source_url",
            "submitter_email",
            "notes",
            "status",
            "created_at",
            "reviewed_at",
        }
        self.assertTrue(required.issubset(cols), f"Missing columns: {required - cols}")

    def test_bike_models_has_data_source_column(self):
        cols = {r[1] for r in self.db.conn.execute("PRAGMA table_info(bike_models)")}
        self.assertIn("data_source", cols, "bike_models must have data_source column")

    def test_data_source_default_is_estimated(self):
        self.db.conn.execute("INSERT OR IGNORE INTO manufacturers (name) VALUES ('X')")
        mfr_id = self.db.conn.execute(
            "SELECT id FROM manufacturers WHERE name='X'"
        ).fetchone()[0]
        self.db.conn.execute(
            "INSERT INTO bike_models (manufacturer_id, model_name) VALUES (?, 'Y')",
            (mfr_id,),
        )
        self.db.conn.commit()
        val = self.db.conn.execute(
            "SELECT data_source FROM bike_models WHERE model_name='Y'"
        ).fetchone()[0]
        self.assertEqual(val, "estimated")

    def test_spec_corrections_indexes_exist(self):
        indexes = {
            r[1]
            for r in self.db.conn.execute(
                "SELECT * FROM sqlite_master WHERE type='index' AND tbl_name='spec_corrections'"
            )
        }
        self.assertIn("idx_spec_corr_bike", indexes)
        self.assertIn("idx_spec_corr_status", indexes)
        self.assertIn("idx_spec_corr_field", indexes)

    def test_schema_version_is_current(self):
        from motoquant.database.schema import SCHEMA_VERSION

        row = self.db.conn.execute(
            "SELECT value FROM schema_meta WHERE key = 'schema_version'"
        ).fetchone()
        self.assertIsNotNone(row, "schema_meta should have a schema_version entry")
        self.assertEqual(
            int(row[0]),
            SCHEMA_VERSION,
            f"DB schema_version should match motoquant.database.schema.SCHEMA_VERSION ({SCHEMA_VERSION}) after fresh init",
        )


# ─────────────────────────────────────────────────────────────────────────────
# 2. Schema migration — existing v3 DB (idempotency)
# ─────────────────────────────────────────────────────────────────────────────


class TestSchemaMigrationExistingV3(unittest.TestCase):
    """Simulate upgrading a DB that was at version 3 (no spec_corrections yet)."""

    def setUp(self):
        self.db_path = _fresh_db_path()
        # ── First: open via MotoQuantDB to get a fully initialized v4 schema,
        #   then downgrade the recorded version to 3 so the migration re-runs.
        #   This is simpler than hand-crafting a raw v3 schema (which would need
        #   every v1-v3 table to be present for initialize() to not crash).
        db_bootstrap = _open_mq_db(self.db_path)
        # Remove spec_corrections table and data_source column to simulate v3 state
        db_bootstrap.conn.execute("DROP TABLE IF EXISTS spec_corrections")
        try:
            # SQLite can't DROP columns; instead we recreate bike_models without it.
            db_bootstrap.conn.executescript("""
                CREATE TABLE bike_models_v3_tmp AS
                    SELECT id, manufacturer_id, model_name, year_from, category,
                           data_quality, data_quality_score, data_source_notes,
                           peak_power_hp, peak_torque_nm, peak_power_rpm, peak_torque_rpm,
                           displacement_cc, bore_mm, stroke_mm, compression_ratio,
                           dry_mass_kg, wet_mass_kg, cylinder_count, cylinder_config,
                           wheelbase_mm, seat_height_mm, fuel_capacity_l,
                           is_active, created_at, updated_at
                    FROM bike_models;
                DROP TABLE bike_models;
                ALTER TABLE bike_models_v3_tmp RENAME TO bike_models;
            """)
        except Exception:
            pass  # If data_source column doesn't exist yet, that's fine
        # Record version 3 in schema_meta
        db_bootstrap.conn.execute(
            "INSERT OR REPLACE INTO schema_meta (key, value) VALUES ('schema_version', '3')"
        )
        db_bootstrap.conn.commit()
        db_bootstrap.close()

        # Now open through MotoQuantDB — should trigger v3→v4 migration
        self.db = _open_mq_db(self.db_path)

    def tearDown(self):
        self.db.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_spec_corrections_table_created(self):
        row = self.db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='spec_corrections'"
        ).fetchone()
        self.assertIsNotNone(row)

    def test_data_source_column_added(self):
        cols = {r[1] for r in self.db.conn.execute("PRAGMA table_info(bike_models)")}
        self.assertIn("data_source", cols)

    def test_migration_is_idempotent(self):
        """Re-opening should not raise even if columns/tables already exist."""
        self.db.close()
        db2 = _open_mq_db(self.db_path)
        # Should get here without exceptions
        db2.close()


# ─────────────────────────────────────────────────────────────────────────────
# 3. SpecCorrectionsRepository — CRUD
# ─────────────────────────────────────────────────────────────────────────────


class TestSpecCorrectionsRepo(unittest.TestCase):
    def setUp(self):
        self.db_path = _fresh_db_path()
        self.db = _open_mq_db(self.db_path)
        # Seed the full catalog so FK constraints work cleanly
        from motoquant.database.seed import seed_all

        seed_all(self.db)
        self.bike_id = _seed_one_bike(self.db)
        self.repo = self.db.spec_corrections

    def tearDown(self):
        self.db.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    # ── create ────────────────────────────────────────────────────────────────

    def test_create_happy_path(self):
        result = self.repo.create(
            bike_model_id=self.bike_id,
            field_name="peak_power_hp",
            proposed_value="19.5",
            source_url="https://example.com/dyno",
            submitter_email="tuner@example.com",
            notes="Wheel-dyno corrected value",
        )
        self.assertIn("id", result)
        self.assertEqual(result["status"], "pending")
        self.assertIsInstance(result["id"], int)

    def test_create_with_current_value_snapshot(self):
        result = self.repo.create(
            bike_model_id=self.bike_id,
            field_name="dry_mass_kg",
            proposed_value="138",
            current_value="142",
        )
        # Verify the current_value was stored
        row = self.db.conn.execute(
            "SELECT current_value FROM spec_corrections WHERE id = ?", (result["id"],)
        ).fetchone()
        self.assertEqual(row[0], "142")

    def test_create_minimal_required_fields_only(self):
        """Only bike_model_id, field_name, proposed_value are required."""
        result = self.repo.create(
            bike_model_id=self.bike_id,
            field_name="bore_mm",
            proposed_value="62.0",
        )
        self.assertEqual(result["status"], "pending")

    def test_create_invalid_field_name_raises(self):
        with self.assertRaises(ValueError) as ctx:
            self.repo.create(
                bike_model_id=self.bike_id,
                field_name="not_a_real_field",
                proposed_value="123",
            )
        self.assertIn("not_a_real_field", str(ctx.exception))

    def test_create_missing_bike_raises(self):
        with self.assertRaises(ValueError) as ctx:
            self.repo.create(
                bike_model_id=999999,
                field_name="peak_power_hp",
                proposed_value="100",
            )
        self.assertIn("999999", str(ctx.exception))

    def test_create_empty_proposed_value_raises(self):
        with self.assertRaises(ValueError):
            self.repo.create(
                bike_model_id=self.bike_id,
                field_name="peak_power_hp",
                proposed_value="   ",
            )

    # ── list_pending ──────────────────────────────────────────────────────────

    def test_list_pending_returns_only_pending(self):
        r1 = self.repo.create(self.bike_id, "peak_power_hp", "20")
        r2 = self.repo.create(self.bike_id, "dry_mass_kg", "139")
        # Approve r1 so it leaves the pending queue
        self.repo.approve(r1["id"])

        pending = self.repo.list_pending()
        ids = [p["id"] for p in pending]
        self.assertNotIn(
            r1["id"], ids, "Approved correction should not be in pending list"
        )
        self.assertIn(r2["id"], ids)

    def test_list_pending_filter_by_bike(self):
        other_id = _seed_one_bike(self.db, model_name="OtherBike")
        assert other_id != self.bike_id, "second seed must yield a different bike id"

        self.repo.create(self.bike_id, "peak_power_hp", "20")
        self.repo.create(other_id, "dry_mass_kg", "200")

        pending_mine = self.repo.list_pending(bike_model_id=self.bike_id)
        self.assertEqual(len(pending_mine), 1)
        self.assertEqual(pending_mine[0]["bike_model_id"], self.bike_id)

    def test_list_pending_empty_when_none(self):
        result = self.repo.list_pending()
        self.assertEqual(result, [])

    # ── list (general) ────────────────────────────────────────────────────────

    def test_list_filter_by_status(self):
        r = self.repo.create(self.bike_id, "peak_power_hp", "20")
        self.repo.approve(r["id"])

        approved = self.repo.list(status="approved")
        self.assertTrue(all(x["status"] == "approved" for x in approved))
        ids = [x["id"] for x in approved]
        self.assertIn(r["id"], ids)

    def test_list_filter_by_field(self):
        self.repo.create(self.bike_id, "peak_power_hp", "20")
        self.repo.create(self.bike_id, "dry_mass_kg", "138")

        rows = self.repo.list(field_name="peak_power_hp")
        self.assertTrue(all(r["field_name"] == "peak_power_hp" for r in rows))

    def test_list_invalid_status_raises(self):
        with self.assertRaises(ValueError):
            self.repo.list(status="not_a_status")

    # ── count ─────────────────────────────────────────────────────────────────

    def test_count_all(self):
        self.repo.create(self.bike_id, "peak_power_hp", "20")
        self.repo.create(self.bike_id, "dry_mass_kg", "138")
        self.assertGreaterEqual(self.repo.count(), 2)

    def test_count_by_status(self):
        r = self.repo.create(self.bike_id, "peak_power_hp", "20")
        self.repo.create(self.bike_id, "dry_mass_kg", "138")
        self.repo.approve(r["id"])
        self.assertEqual(self.repo.count(status="approved"), 1)
        self.assertEqual(self.repo.count(status="pending"), 1)

    # ── approve / reject ──────────────────────────────────────────────────────

    def test_approve_sets_status(self):
        r = self.repo.create(self.bike_id, "peak_power_hp", "20")
        found = self.repo.approve(r["id"])
        self.assertTrue(found)
        row = self.db.conn.execute(
            "SELECT status FROM spec_corrections WHERE id=?", (r["id"],)
        ).fetchone()
        self.assertEqual(row[0], "approved")

    def test_reject_sets_status(self):
        r = self.repo.create(self.bike_id, "peak_power_hp", "20")
        found = self.repo.reject(r["id"])
        self.assertTrue(found)
        row = self.db.conn.execute(
            "SELECT status FROM spec_corrections WHERE id=?", (r["id"],)
        ).fetchone()
        self.assertEqual(row[0], "rejected")

    def test_approve_sets_reviewed_at(self):
        r = self.repo.create(self.bike_id, "peak_power_hp", "20")
        self.repo.approve(r["id"])
        row = self.db.conn.execute(
            "SELECT reviewed_at FROM spec_corrections WHERE id=?", (r["id"],)
        ).fetchone()
        self.assertIsNotNone(row[0], "reviewed_at should be set after approve()")

    def test_approve_missing_id_returns_false(self):
        result = self.repo.approve(999999)
        self.assertFalse(result)

    def test_reject_missing_id_returns_false(self):
        result = self.repo.reject(999999)
        self.assertFalse(result)

    # ── get ───────────────────────────────────────────────────────────────────

    def test_get_returns_correct_row(self):
        r = self.repo.create(
            self.bike_id, "compression_ratio", "11.5", notes="from service manual"
        )
        fetched = self.repo.get(r["id"])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["field_name"], "compression_ratio")
        self.assertEqual(fetched["proposed_value"], "11.5")

    def test_get_missing_returns_none(self):
        self.assertIsNone(self.repo.get(999999))


# ─────────────────────────────────────────────────────────────────────────────
# 4. bike_repo.update_data_source
# ─────────────────────────────────────────────────────────────────────────────


class TestUpdateDataSource(unittest.TestCase):
    def setUp(self):
        self.db_path = _fresh_db_path()
        self.db = _open_mq_db(self.db_path)
        from motoquant.database.seed import seed_all

        seed_all(self.db)
        self.bike_id = _seed_one_bike(self.db)

    def tearDown(self):
        self.db.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_update_to_valid_value(self):
        result = self.db.bikes.update_data_source(
            self.bike_id, "verified_service_manual"
        )
        self.assertTrue(result)
        val = self.db.conn.execute(
            "SELECT data_source FROM bike_models WHERE id=?", (self.bike_id,)
        ).fetchone()[0]
        self.assertEqual(val, "verified_service_manual")

    def test_update_invalid_value_raises(self):
        with self.assertRaises(ValueError):
            self.db.bikes.update_data_source(self.bike_id, "bad_value")

    def test_update_missing_bike_returns_false(self):
        result = self.db.bikes.update_data_source(999999, "estimated")
        self.assertFalse(result)

    def test_all_valid_data_source_values_accepted(self):
        valid_values = [
            "verified_service_manual",
            "magazine_test",
            "estimated",
            "user_submitted_pending",
            "user_submitted_verified",
        ]
        for val in valid_values:
            with self.subTest(val=val):
                self.assertTrue(self.db.bikes.update_data_source(self.bike_id, val))


# ─────────────────────────────────────────────────────────────────────────────
# 5. FastAPI endpoints
# ─────────────────────────────────────────────────────────────────────────────


class TestSpecCorrectionsAPI(unittest.TestCase):
    """Integration tests against the FastAPI app using TestClient."""

    @classmethod
    def setUpClass(cls):
        try:
            from fastapi.testclient import TestClient
        except ImportError:
            raise unittest.SkipTest("fastapi not installed — skipping API tests")

        cls.db_path = _fresh_db_path()
        db = _open_mq_db(cls.db_path)
        from motoquant.database.seed import seed_all

        seed_all(db)
        # Get a real bike_id from the seeded catalog
        row = db.conn.execute("SELECT id FROM bike_models LIMIT 1").fetchone()
        cls.bike_id = row[0] if row else None
        db.close()

        cls._prior_env_db = os.environ.get("MOTOQUANT_DB")
        os.environ["MOTOQUANT_DB"] = cls.db_path

        # Null the api singletons: a sibling module's TestClient may have
        # cached a connection to ITS (possibly deleted) tmp DB — without the
        # reset these tests silently talk to the wrong database (the class
        # of ordering failure fixed for test_api on July 2).
        import motoquant.api as _api_mod

        _api_mod._db_conn = None
        _api_mod._db_facade = None
        cls.client = TestClient(_api_mod.app)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.db_path):
            os.unlink(cls.db_path)
        if cls._prior_env_db is None:
            os.environ.pop("MOTOQUANT_DB", None)
        else:
            os.environ["MOTOQUANT_DB"] = cls._prior_env_db
        import motoquant.api as _api_mod

        _api_mod._db_conn = None
        _api_mod._db_facade = None

    # ── GET /api/specs/correction-fields ─────────────────────────────────────

    def test_correction_fields_returns_list(self):
        resp = self.client.get("/api/specs/correction-fields")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_correction_fields_have_value_and_label(self):
        resp = self.client.get("/api/specs/correction-fields")
        fields = resp.json()
        for f in fields:
            self.assertIn("value", f)
            self.assertIn("label", f)

    def test_correction_fields_includes_peak_power(self):
        resp = self.client.get("/api/specs/correction-fields")
        values = [f["value"] for f in resp.json()]
        self.assertIn("peak_power_hp", values)

    # ── POST /api/specs/correct ──────────────────────────────────────────────

    def test_submit_correction_happy_path(self):
        if not self.bike_id:
            self.skipTest("No bike in DB")
        resp = self.client.post(
            "/api/specs/correct",
            json={
                "bike_id": self.bike_id,
                "field_name": "peak_power_hp",
                "proposed_value": "19.5",
                "source_url": "https://example.com/dyno",
                "submitter_email": "rider@example.com",
                "notes": "Measured on a Dynojet 250i",
            },
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertIn("id", data)
        self.assertEqual(data["status"], "pending")
        self.assertIsInstance(data["id"], int)

    def test_submit_correction_minimal_fields(self):
        """Only required fields — no optional ones."""
        if not self.bike_id:
            self.skipTest("No bike in DB")
        resp = self.client.post(
            "/api/specs/correct",
            json={
                "bike_id": self.bike_id,
                "field_name": "dry_mass_kg",
                "proposed_value": "140",
            },
        )
        self.assertEqual(resp.status_code, 201)

    def test_submit_correction_invalid_field_name(self):
        if not self.bike_id:
            self.skipTest("No bike in DB")
        resp = self.client.post(
            "/api/specs/correct",
            json={
                "bike_id": self.bike_id,
                "field_name": "not_a_valid_field",
                "proposed_value": "42",
            },
        )
        self.assertEqual(resp.status_code, 422)

    def test_submit_correction_missing_bike(self):
        resp = self.client.post(
            "/api/specs/correct",
            json={
                "bike_id": 999999,
                "field_name": "peak_power_hp",
                "proposed_value": "100",
            },
        )
        self.assertEqual(resp.status_code, 404)

    def test_submit_correction_empty_proposed_value(self):
        if not self.bike_id:
            self.skipTest("No bike in DB")
        resp = self.client.post(
            "/api/specs/correct",
            json={
                "bike_id": self.bike_id,
                "field_name": "peak_power_hp",
                "proposed_value": "   ",
            },
        )
        # Empty/blank proposed_value must be rejected
        self.assertIn(resp.status_code, (400, 422))

    def test_submit_correction_returns_message(self):
        if not self.bike_id:
            self.skipTest("No bike in DB")
        resp = self.client.post(
            "/api/specs/correct",
            json={
                "bike_id": self.bike_id,
                "field_name": "bore_mm",
                "proposed_value": "62.0",
            },
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertIn("message", data)

    def test_submit_data_source_correction(self):
        """data_source is a valid correctable field."""
        if not self.bike_id:
            self.skipTest("No bike in DB")
        resp = self.client.post(
            "/api/specs/correct",
            json={
                "bike_id": self.bike_id,
                "field_name": "data_source",
                "proposed_value": "verified_service_manual",
                "notes": "Have the OEM service manual",
            },
        )
        self.assertEqual(resp.status_code, 201)


# ─────────────────────────────────────────────────────────────────────────────
# 6. VALID_CORRECTION_FIELDS whitelist integrity
# ─────────────────────────────────────────────────────────────────────────────


class TestValidCorrectionFields(unittest.TestCase):
    def test_whitelist_is_frozenset(self):
        from motoquant.database.spec_corrections_repo import VALID_CORRECTION_FIELDS

        self.assertIsInstance(VALID_CORRECTION_FIELDS, frozenset)

    def test_whitelist_contains_expected_fields(self):
        from motoquant.database.spec_corrections_repo import VALID_CORRECTION_FIELDS

        expected = {
            "peak_power_hp",
            "peak_torque_nm",
            "displacement_cc",
            "dry_mass_kg",
            "wet_mass_kg",
            "bore_mm",
            "stroke_mm",
            "compression_ratio",
            "cylinder_count",
            "wheelbase_mm",
            "seat_height_mm",
            "fuel_capacity_l",
            "front_sprocket",
            "rear_sprocket",
            "gear_ratios",
            "redline_rpm",
            "cd",
            "frontal_area_m2",
            "data_source",
        }
        missing = expected - VALID_CORRECTION_FIELDS
        self.assertEqual(missing, set(), f"Missing from whitelist: {missing}")

    def test_field_labels_covers_all_whitelist(self):
        from motoquant.database.spec_corrections_repo import (
            FIELD_LABELS,
            VALID_CORRECTION_FIELDS,
        )

        for field in VALID_CORRECTION_FIELDS:
            self.assertIn(
                field,
                FIELD_LABELS,
                f"FIELD_LABELS missing entry for '{field}'",
            )


# ─────────────────────────────────────────────────────────────────────────────
# 7. Reference baselines preserved
# ─────────────────────────────────────────────────────────────────────────────


class TestReferenceBaselinesPreserved(unittest.TestCase):
    """Ensure the spec-corrections feature did not perturb K5/R1/Hayabusa ETs."""

    TOLERANCE_S = 0.02  # ±20 ms — same as CLAUDE.md validation criterion

    BASELINES = [
        ("gsxr1000_k5", 9.9331),
        ("yzfr1_4c8", 10.1436),
        ("hayabusa_gen1", 10.3633),
    ]

    def _run_et(self, config_fn_name):
        import motoquant

        config_fn = getattr(motoquant, config_fn_name)
        cfg = config_fn()
        engine = motoquant.MotoQuantEngine(cfg)
        result = engine.run()
        return result.time_quarter

    def test_k5_baseline(self):
        et = self._run_et("gsxr1000_k5")
        self.assertAlmostEqual(
            et,
            9.9331,
            delta=self.TOLERANCE_S,
            msg=f"K5 ET {et:.4f}s drifted from baseline 9.9331s",
        )

    def test_r1_baseline(self):
        et = self._run_et("yzfr1_4c8")
        self.assertAlmostEqual(
            et,
            10.1436,
            delta=self.TOLERANCE_S,
            msg=f"R1 ET {et:.4f}s drifted from baseline 10.1436s",
        )

    def test_hayabusa_baseline(self):
        et = self._run_et("hayabusa_gen1")
        self.assertAlmostEqual(
            et,
            10.3633,
            delta=self.TOLERANCE_S,
            msg=f"Hayabusa ET {et:.4f}s drifted from baseline 10.3633s",
        )


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
    unittest.main(verbosity=2)
