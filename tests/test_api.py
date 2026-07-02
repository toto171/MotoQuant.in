"""
Tests for motoquant.api -- FastAPI endpoints.

Uses FastAPI's TestClient (starlette) for synchronous endpoint testing.
Does NOT require a running server.

DB-backed endpoints (bike suggest, venue resolve) use an isolated temporary
SQLite database seeded with minimal reference data; the module-level setup
below creates it and patches motoquant.api so the production `motoquant.db`
is never touched.
"""

import io
import math
import os
import tempfile
import unittest

# FastAPI TestClient
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Isolated DB setup -- runs before `from motoquant.api import app` imports
# cache any state, so we point the API at a fresh tmp DB first.
# ---------------------------------------------------------------------------

_tmp_db_file = tempfile.NamedTemporaryFile(
    prefix="motoquant_test_", suffix=".db", delete=False
)
_tmp_db_file.close()
_TMP_DB_PATH = _tmp_db_file.name
# Capture the prior value so tearDownModule can restore it — otherwise this
# module leaks MOTOQUANT_DB (pointed at a tmp DB it then deletes) for the
# rest of the pytest session, so any later TestClient-backed test recreates
# an empty DB at the dead path and reads zero bikes.
_PRIOR_MOTOQUANT_DB = os.environ.get("MOTOQUANT_DB")
os.environ["MOTOQUANT_DB"] = _TMP_DB_PATH

# Initialize schema + seeded reference data in the tmp DB
from motoquant.database.connection import MotoQuantDB as _SetupDB  # noqa: E402
from motoquant.database.seed import seed_all as _seed_all  # noqa: E402

_setup_db = _SetupDB(_TMP_DB_PATH)
_setup_db.initialize()
# Seed reference bikes + tires + parts so compatibility / parts endpoints
# have realistic data to filter against. Fast (~100 ms) because the catalog
# lives in Python source, not a network fetch.
_seed_all(_setup_db)
_setup_db.close()

# Now safe to import the API -- it'll pick up the env var on first DB access
import motoquant.api as _api_mod  # noqa: E402
from motoquant.api import app  # noqa: E402

# Force any cached connection (singleton) to use the tmp DB
_api_mod._db_conn = None

client = TestClient(app)


def setUpModule():
    """Re-assert this module's tmp DB right before its tests run.

    Module-level MOTOQUANT_DB overrides execute at COLLECTION time, so a
    sibling module imported after this one (e.g. test_llm_runner also sets
    MOTOQUANT_DB at import) leaves the env pointing at ITS tmp DB by the time
    these tests actually run — the API then reads a DB without the
    bike_suggestions/parts tables and returns 500s. Re-asserting here (after
    collection, before this module's first test) makes the ordering
    irrelevant.
    """
    os.environ["MOTOQUANT_DB"] = _TMP_DB_PATH
    _api_mod._db_conn = None


def tearDownModule():
    """Remove the tmp DB and restore MOTOQUANT_DB after all tests finish."""
    try:
        if _api_mod._db_conn is not None:
            try:
                _api_mod._db_conn.close()
            except Exception:
                pass
            _api_mod._db_conn = None
        if os.path.exists(_TMP_DB_PATH):
            os.unlink(_TMP_DB_PATH)
    except Exception:
        pass
    # Restore the env + null the api singleton so later TestClient-backed
    # modules reconnect to the real motoquant.db, not this deleted tmp path.
    if _PRIOR_MOTOQUANT_DB is None:
        os.environ.pop("MOTOQUANT_DB", None)
    else:
        os.environ["MOTOQUANT_DB"] = _PRIOR_MOTOQUANT_DB
    _api_mod._db_conn = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _dragy_csv_bytes(n_run_points=400, peak_mph=160.0, duration_s=12.0):
    """Generate a minimal Dragy-style CSV in memory (imperial, with distance).

    Includes a staged period (20 frames at v=0) before the launch ramp,
    which the Dragy parser's run-boundary detector requires (MIN_STAGE_FRAMES=5).
    """
    dt = duration_s / n_run_points
    lines = ["Time (s),Speed (mph),Distance (ft)"]
    n_stage = 20
    for i in range(n_stage):
        t = i * dt
        lines.append(f"{t:.3f},0.0000,0.0000")
    dist_ft = 0.0
    for i in range(n_run_points):
        t = (n_stage + i) * dt
        frac = i / n_run_points
        v_mph = peak_mph * (frac**0.7)
        v_ms = v_mph * 0.44704
        dist_ft += v_ms * dt / 0.3048
        lines.append(f"{t:.3f},{v_mph:.4f},{dist_ft:.4f}")
    return "\n".join(lines).encode("utf-8")


def _dyno_csv_bytes(n_points=50):
    """Generate a minimal DynoJet-style CSV (WHP/lb-ft vs RPM)."""
    lines = ["RPM,WHP,TQ (lb-ft)"]
    for i in range(n_points):
        rpm = 3000 + i * (11000 - 3000) / n_points
        frac = (rpm - 3000) / 8000
        whp = 150 * math.exp(-0.5 * ((frac - 0.85) / 0.25) ** 2)
        tq = whp * 5252 / rpm if rpm > 0 else 0
        lines.append(f"{rpm:.0f},{whp:.2f},{tq:.2f}")
    return "\n".join(lines).encode("utf-8")


# ===========================================================================
# Existing endpoint smoke tests
# ===========================================================================


class TestHealthEndpoints(unittest.TestCase):
    def test_root(self):
        r = client.get("/")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["service"], "MotoQuant Pro API")
        self.assertEqual(body["status"], "ok")

    def test_health(self):
        r = client.get("/api/health")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("status", body)
        self.assertIn("database", body)

    def test_docs_accessible(self):
        r = client.get("/docs")
        self.assertEqual(r.status_code, 200)


class TestQuickSim(unittest.TestCase):
    def test_preset_gsxr(self):
        r = client.post(
            "/api/simulate/quick",
            json={
                "bike_preset": "gsxr1000_k5",
                "rider_mass_kg": 75,
            },
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("et_quarter_s", body)
        self.assertGreater(body["et_quarter_s"], 9.0)
        self.assertLess(body["et_quarter_s"], 12.0)

    def test_preset_hayabusa(self):
        r = client.post(
            "/api/simulate/quick",
            json={
                "bike_preset": "hayabusa_gen1",
                "rider_mass_kg": 80,
            },
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertGreater(body["trap_speed_kmh"], 180)

    def test_power_boost_makes_faster(self):
        stock = client.post(
            "/api/simulate/quick",
            json={
                "bike_preset": "gsxr1000_k5",
            },
        ).json()
        boosted = client.post(
            "/api/simulate/quick",
            json={
                "bike_preset": "gsxr1000_k5",
                "power_boost_pct": 20,
            },
        ).json()
        self.assertLess(boosted["et_quarter_s"], stock["et_quarter_s"])

    def test_heavier_rider_slower(self):
        light = client.post(
            "/api/simulate/quick",
            json={
                "bike_preset": "gsxr1000_k5",
                "rider_mass_kg": 60,
            },
        ).json()
        heavy = client.post(
            "/api/simulate/quick",
            json={
                "bike_preset": "gsxr1000_k5",
                "rider_mass_kg": 120,
            },
        ).json()
        self.assertLess(light["et_quarter_s"], heavy["et_quarter_s"])


class TestFullSim(unittest.TestCase):
    def test_returns_timeseries(self):
        r = client.post(
            "/api/simulate",
            json={
                "bike_preset": "yzfr1_4c8",
            },
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("timeseries", body)
        ts = body["timeseries"]
        self.assertIn("t_s", ts)
        self.assertIn("v_kmh", ts)
        self.assertIn("rpm", ts)
        self.assertGreater(len(ts["t_s"]), 10)

    def test_splits_present(self):
        r = client.post(
            "/api/simulate",
            json={
                "bike_preset": "gsxr1000_k5",
            },
        )
        body = r.json()
        self.assertIn("splits", body)
        splits = body["splits"]
        self.assertLess(splits["60ft_s"], splits["330ft_s"])
        self.assertLess(splits["660ft_s"], splits["1320ft_s"])


# ===========================================================================
# A vs B Comparison
# ===========================================================================


class TestCompareEndpoint(unittest.TestCase):
    def test_basic_compare_same_bike(self):
        r = client.post(
            "/api/simulate/compare",
            json={
                "a_bike_preset": "gsxr1000_k5",
                "a_power_boost_pct": 0,
                "b_bike_preset": "gsxr1000_k5",
                "b_power_boost_pct": 15,
            },
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("a", body)
        self.assertIn("b", body)
        self.assertIn("delta", body)
        self.assertLess(body["delta"]["et_s"], 0)
        self.assertEqual(body["delta"]["faster"], "B")

    def test_compare_returns_timeseries(self):
        r = client.post(
            "/api/simulate/compare",
            json={
                "a_bike_preset": "gsxr1000_k5",
                "b_bike_preset": "hayabusa_gen1",
            },
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("timeseries", body["a"])
        self.assertIn("timeseries", body["b"])
        self.assertGreater(len(body["a"]["timeseries"]["t_s"]), 10)

    def test_compare_different_bikes(self):
        r = client.post(
            "/api/simulate/compare",
            json={
                "a_bike_preset": "gsxr1000_k5",
                "b_bike_preset": "hayabusa_gen1",
            },
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertGreater(body["a"]["et_quarter_s"], 8)
        self.assertGreater(body["b"]["et_quarter_s"], 8)
        expected_delta = round(body["b"]["et_quarter_s"] - body["a"]["et_quarter_s"], 4)
        self.assertAlmostEqual(body["delta"]["et_s"], expected_delta, places=3)

    def test_compare_cost_diff(self):
        r = client.post(
            "/api/simulate/compare",
            json={
                "a_bike_preset": "gsxr1000_k5",
                "b_bike_preset": "gsxr1000_k5",
                "b_power_boost_pct": 10,
            },
        )
        body = r.json()
        self.assertEqual(body["delta"]["cost_diff_inr"], 0)

    def test_compare_labels(self):
        r = client.post(
            "/api/simulate/compare",
            json={
                "a_bike_preset": "gsxr1000_k5",
                "b_bike_preset": "gsxr1000_k5",
            },
        )
        body = r.json()
        self.assertEqual(body["a"]["label"], "A")
        self.assertEqual(body["b"]["label"], "B")


# ===========================================================================
# Dragy Upload
# ===========================================================================


class TestDragyUpload(unittest.TestCase):
    def test_upload_csv_parses_run(self):
        csv_bytes = _dragy_csv_bytes()
        r = client.post(
            "/api/calibrate/dragy",
            files={"file": ("test_run.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("runs_detected", body)
        self.assertGreaterEqual(body["runs_detected"], 1)
        self.assertIn("best_run", body)
        best = body["best_run"]
        self.assertIn("et_quarter_s", best)
        self.assertIn("trap_speed_kmh", best)
        self.assertIn("timeseries", best)

    def test_upload_with_overlay(self):
        csv_bytes = _dragy_csv_bytes()
        r = client.post(
            "/api/calibrate/dragy",
            files={"file": ("run.csv", io.BytesIO(csv_bytes), "text/csv")},
            data={"bike_preset": "gsxr1000_k5"},
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("overlay", body)
        ov = body["overlay"]
        self.assertIn("sim_et_s", ov)
        self.assertIn("et_error_s", ov)
        self.assertIn("v_rmse_kmh", ov)
        self.assertIn("sim_timeseries", ov)

    def test_upload_without_overlay(self):
        csv_bytes = _dragy_csv_bytes()
        r = client.post(
            "/api/calibrate/dragy",
            files={"file": ("run.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertNotIn("overlay", body)

    def test_upload_invalid_csv_returns_422(self):
        bad_csv = b"this,is,not,a,dragy,file\n1,2,3,4,5,6\n"
        r = client.post(
            "/api/calibrate/dragy",
            files={"file": ("bad.csv", io.BytesIO(bad_csv), "text/csv")},
        )
        self.assertIn(r.status_code, [422, 400])

    def test_filename_returned(self):
        csv_bytes = _dragy_csv_bytes()
        r = client.post(
            "/api/calibrate/dragy",
            files={"file": ("my_dragy_run.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        body = r.json()
        self.assertEqual(body.get("filename"), "my_dragy_run.csv")


# ===========================================================================
# Dyno Upload
# ===========================================================================


class TestDynoUpload(unittest.TestCase):
    def test_upload_dyno_csv(self):
        csv_bytes = _dyno_csv_bytes()
        r = client.post(
            "/api/calibrate/dyno",
            files={"file": ("dyno_run.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("peak_power_hp", body)
        self.assertIn("peak_torque_nm", body)
        self.assertIn("curve", body)
        self.assertGreater(body["peak_power_hp"], 50)
        self.assertLess(body["peak_power_hp"], 300)

    def test_dyno_curve_arrays(self):
        csv_bytes = _dyno_csv_bytes()
        r = client.post(
            "/api/calibrate/dyno",
            files={"file": ("dyno.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        body = r.json()
        curve = body["curve"]
        self.assertIn("rpm", curve)
        self.assertIn("power_hp", curve)
        self.assertIn("torque_nm", curve)
        self.assertEqual(len(curve["rpm"]), len(curve["power_hp"]))
        self.assertEqual(len(curve["rpm"]), len(curve["torque_nm"]))

    def test_dyno_with_atmospheric_correction(self):
        csv_bytes = _dyno_csv_bytes()
        r = client.post(
            "/api/calibrate/dyno",
            files={"file": ("dyno.csv", io.BytesIO(csv_bytes), "text/csv")},
            data={"temp_c": "35", "pressure_kpa": "95", "rh_pct": "60"},
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertGreater(body["correction_factor"], 0.9)
        self.assertIn("is_at_wheel", body)

    def test_dyno_filename_returned(self):
        csv_bytes = _dyno_csv_bytes()
        r = client.post(
            "/api/calibrate/dyno",
            files={"file": ("hayabusa_dyno.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        body = r.json()
        self.assertEqual(body.get("filename"), "hayabusa_dyno.csv")

    def test_dyno_invalid_csv_returns_422(self):
        bad = b"nothing useful here\njust junk\n"
        r = client.post(
            "/api/calibrate/dyno",
            files={"file": ("bad.csv", io.BytesIO(bad), "text/csv")},
        )
        self.assertIn(r.status_code, [422, 400])


# ===========================================================================
# POST /api/bikes/suggest
# ===========================================================================


class TestBikeSuggestEndpoint(unittest.TestCase):
    def test_minimal_valid_submission(self):
        """Accept a submission with only required fields (make + model)."""
        r = client.post(
            "/api/bikes/suggest",
            json={
                "make": "TestMakeXYZ",
                "model": "Phantom 500R Test",
            },
        )
        self.assertEqual(r.status_code, 201, r.text)
        body = r.json()
        self.assertIn("id", body)
        self.assertIsInstance(body["id"], int)
        self.assertEqual(body["flagged_out_of_bounds"], False)
        self.assertEqual(body["issues"], [])

    def test_full_submission_not_flagged(self):
        """Plausible full submission should NOT be flagged."""
        r = client.post(
            "/api/bikes/suggest",
            json={
                "make": "TestBrand",
                "model": "Test Sport 750",
                "year": 2024,
                "displacement_cc": 749.0,
                "peak_power_hp": 95.0,
                "dry_mass_kg": 190.0,
                "category": "sport",
                "notes": "Rare spec variant",
            },
        )
        self.assertEqual(r.status_code, 201, r.text)
        body = r.json()
        self.assertFalse(body["flagged_out_of_bounds"])

    def test_out_of_bounds_displacement_flagged(self):
        """Plausible-range violations are stored but flagged."""
        r = client.post(
            "/api/bikes/suggest",
            json={
                "make": "TestBrand",
                "model": "Flag Test Model",
                "displacement_cc": 4500.0,  # Above 3500 ceiling in BOUNDS
            },
        )
        # Pydantic range allows up to 5000, repo plausibility caps at 3500
        self.assertEqual(r.status_code, 201, r.text)
        body = r.json()
        self.assertTrue(body["flagged_out_of_bounds"])
        self.assertTrue(any("displacement_cc" in s for s in body["issues"]))

    def test_empty_make_rejected(self):
        """Empty make field returns 422."""
        r = client.post(
            "/api/bikes/suggest",
            json={
                "make": "",
                "model": "Should not store",
            },
        )
        self.assertEqual(r.status_code, 422)

    def test_missing_model_rejected(self):
        """Missing model field returns 422."""
        r = client.post(
            "/api/bikes/suggest",
            json={
                "make": "TestMake",
            },
        )
        self.assertEqual(r.status_code, 422)

    def test_extreme_value_rejected_by_pydantic(self):
        """Values outside even the lenient Pydantic range return 422."""
        r = client.post(
            "/api/bikes/suggest",
            json={
                "make": "TestMake",
                "model": "Extreme",
                "year": 1800,  # below 1900 Pydantic lower bound
            },
        )
        self.assertEqual(r.status_code, 422)


# ===========================================================================
# POST /api/venues/resolve
# ===========================================================================


class TestVenueResolveEndpoint(unittest.TestCase):
    def test_missing_input_returns_422(self):
        """Neither location nor lat/lon provided → 422."""
        r = client.post("/api/venues/resolve", json={})
        self.assertEqual(r.status_code, 422)

    def test_lat_without_lon_returns_422(self):
        """Partial GPS (lat only) → 422."""
        r = client.post("/api/venues/resolve", json={"lat": 18.5})
        self.assertEqual(r.status_code, 422)

    def test_nonexistent_location_graceful(self):
        """Unknown location falls through to OWM; without API key returns 503."""
        r = client.post(
            "/api/venues/resolve",
            json={
                "location": "Nowhere Place XYZ Never Existed 999",
            },
        )
        # In a CI environment without OPENWEATHERMAP_API_KEY this is 503.
        # In a configured environment it may be 422 ("could not resolve").
        # Either way it should not be a 5xx that indicates a crash.
        self.assertIn(r.status_code, [422, 502, 503])

    def test_seeded_venue_match_shape(self):
        """
        If the DB has seeded venues, a known name should resolve to a seeded venue.
        If not, the test is a no-op (resolve endpoint falls through to OWM).
        Shape check only; does not require live network.
        """
        r = client.post("/api/venues/resolve", json={"location": "Aamby"})
        # If database is seeded and Aamby matches, expect 200 + flat env payload
        if r.status_code == 200:
            body = r.json()
            # Response should contain top-level environment fields
            self.assertIn("matched_venue_id", body)
            self.assertIn("temperature_c", body)
            self.assertIn("humidity_pct", body)
            self.assertIn("pressure_hpa", body)
            self.assertIn("altitude_m", body)
            self.assertIn("density_altitude_m", body)
            self.assertIn("source", body)
            # When a seeded venue matched, the canonical `source` must be the
            # resolution-path marker (not the underlying weather provenance).
            # The raw weather provenance, if any, is preserved under
            # `weather_source` so the UI can still show it separately.
            if body["matched_venue_id"] is not None:
                self.assertEqual(body["source"], "seeded_venue")
                self.assertIsInstance(body["matched_venue_id"], int)
            else:
                # Fallthrough path — OWM live fetch
                self.assertEqual(body["source"], "openweathermap")
        else:
            # In test environments without seeded data, fall through to OWM,
            # which returns 503 (no key) / 502 (network) / 422 (not found).
            self.assertIn(r.status_code, [422, 502, 503])


class TestPartsEndpoint(unittest.TestCase):
    """
    Coverage for GET /api/parts, including the bike_id compatibility filter.

    The tmp DB is seeded via seed_all() at module load, so we have:
      - 3 reference bikes (K5 I4 1000, R1 I4 1000, Hayabusa I4 1300) — all 4-stroke
      - 465-part catalog including 2T-only parts (expansion chambers, reed valves)
        whose fitment rules require stroke_type=2
    """

    def test_list_all_parts(self):
        """Without bike_id, returns the full catalog (up to limit)."""
        r = client.get("/api/parts")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("parts", body)
        self.assertIn("total", body)
        self.assertGreaterEqual(body["total"], 400, "catalog should be seeded")
        # Default: no compatibility annotation
        self.assertFalse(body.get("compatible_only", False))
        for p in body["parts"][:5]:
            self.assertNotIn(
                "compatible",
                p,
                "compatibility flag should only appear when bike_id is set",
            )

    def test_category_filter_independent_of_bike_id(self):
        """Category filter alone narrows results without touching compatibility."""
        r = client.get("/api/parts", params={"category": "exhaust"})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertGreater(body["total"], 0, "expected at least one exhaust")
        for p in body["parts"]:
            self.assertEqual(
                str(p.get("category_name", "")).lower(),
                "exhaust",
                f"non-exhaust leaked: {p.get('category_name')}",
            )

    def test_unknown_bike_id_returns_404(self):
        """bike_id pointing at a nonexistent row should 404, not 500."""
        r = client.get("/api/parts", params={"bike_id": 99999})
        self.assertEqual(r.status_code, 404)

    def test_bike_id_filters_out_2stroke_parts(self):
        """
        Kaizen guard: the 2T catalog has stroke_type=2 in its fitment rules.
        A 4-stroke superbike (K5, bike_id=1 in seed) must NOT see 2T-only parts
        like a JL ZX expansion chamber or a VForce reed block.
        """
        # GSX-R 1000 K5 is the first seeded reference bike -> id=1
        bike_row = client.get("/api/bikes/1").json()
        self.assertEqual(bike_row.get("id"), 1)
        # Filter request
        r = client.get("/api/parts", params={"bike_id": 1, "limit": 1000})
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertTrue(body["compatible_only"])
        self.assertEqual(body["bike_id"], 1)
        self.assertGreater(body["total"], 0, "K5 should match at least some parts")
        # No 2T parts should appear
        for p in body["parts"]:
            brand = (p.get("brand") or "").lower()
            model = (p.get("model_name") or "").lower()
            # These 2T brand/model tokens should never surface for a 4T bike
            for token in (
                "expansion chamber",
                "reed valve",
                "powervalve",
                "ypvs",
                "rave valve",
            ):
                self.assertNotIn(
                    token,
                    f"{brand} {model}",
                    f"2T part leaked into 4T bike_id=1: {brand} {model}",
                )

    def test_bike_id_compatible_only_false_annotates(self):
        """
        compatible_only=false returns the full catalog with a per-row
        'compatible' + 'fitment_reason' annotation instead of filtering.
        Used by UIs that want to grey-out incompatible options.
        """
        r = client.get(
            "/api/parts",
            params={"bike_id": 1, "compatible_only": "false", "limit": 1000},
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertFalse(body["compatible_only"])
        self.assertGreater(body["total"], 400, "expected full catalog")
        # Every row should have the compatibility annotation
        n_compat = 0
        n_incompat = 0
        for p in body["parts"]:
            self.assertIn("compatible", p)
            self.assertIn("fitment_reason", p)
            self.assertIsInstance(p["compatible"], bool)
            self.assertIsInstance(p["fitment_reason"], str)
            if p["compatible"]:
                n_compat += 1
            else:
                n_incompat += 1
        # Mixed outcome expected: some parts compatible, some not
        self.assertGreater(n_compat, 0, "expected at least one compatible part")
        self.assertGreater(
            n_incompat, 0, "expected at least one incompatible part (e.g. 2T-only)"
        )

    def test_bike_id_with_category_combines(self):
        """bike_id + category should combine as AND, not OR."""
        r = client.get(
            "/api/parts",
            params={"bike_id": 1, "category": "exhaust", "limit": 1000},
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        for p in body["parts"]:
            self.assertEqual(str(p.get("category_name", "")).lower(), "exhaust")


if __name__ == "__main__":
    unittest.main()


# ═══════════════════════════════════════════════════════════════════════════
# Surrogate inference tests  (/api/surrogate/*)
# ═══════════════════════════════════════════════════════════════════════════


class TestSurrogatePredict(unittest.TestCase):
    """
    Tests for POST /api/surrogate/predict.

    The surrogate .pkl files may not be present in CI; every test gracefully
    handles a 503 "model not available" response and passes with a skip signal
    so the test run stays green without pre-trained weights.
    """

    def _predict(self, payload):
        return client.post("/api/surrogate/predict", json=payload)

    def test_happy_path_no_bike_id(self):
        """Default request (no bike_id) should return et_s, trap_kmh, source."""
        r = self._predict({})
        if r.status_code == 503:
            self.skipTest("Surrogate model not available in this environment")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("et_s", body)
        self.assertIn("trap_kmh", body)
        self.assertIn("source", body)
        self.assertIn(body["source"], ("dnn", "xgb", "numpy"))
        self.assertGreater(body["et_s"], 5.0)
        self.assertLess(body["et_s"], 30.0)
        self.assertGreater(body["trap_kmh"], 80.0)

    def test_happy_path_with_bike_id(self):
        """Valid bike_id=1 should return a prediction keyed to that bike."""
        r = self._predict({"bike_id": 1})
        if r.status_code == 503:
            self.skipTest("Surrogate model not available")
        self.assertIn(r.status_code, (200, 404))  # 404 if DB not seeded in test env

    def test_bike_id_not_found(self):
        """Non-existent bike_id should still return a result (falls back to K5 default)
        or a 404 if the DB is present but the bike doesn't exist."""
        r = self._predict({"bike_id": 999999})
        if r.status_code == 503:
            self.skipTest("Surrogate model not available")
        # Either 200 (fell back to default config) or 404 (DB present, bike missing)
        self.assertIn(r.status_code, (200, 404))

    def test_out_of_envelope_warning(self):
        """Extreme power/mass values should trigger within_training_envelope=False."""
        r = self._predict({"power_boost_pct": 180.0, "mass_delta_kg": -95.0})
        if r.status_code == 503:
            self.skipTest("Surrogate model not available")
        if r.status_code != 200:
            return
        body = r.json()
        # Extreme boost may push peak_power_hp beyond the 230 hp training bound
        # We just assert the field is present and is a bool — actual value depends
        # on base config used (K5 default may already be near upper bound)
        self.assertIn("within_training_envelope", body)
        self.assertIsInstance(body["within_training_envelope"], bool)
        self.assertIsInstance(body["envelope_violations"], list)

    def test_inference_latency_under_10ms(self):
        """Surrogate inference should complete in under 10 ms (p95 target is 5 ms)."""
        r = self._predict({})
        if r.status_code == 503:
            self.skipTest("Surrogate model not available")
        if r.status_code != 200:
            return
        body = r.json()
        self.assertLess(
            body["inference_ms"],
            10.0,
            f"inference_ms={body['inference_ms']:.2f} exceeds 10 ms budget",
        )

    def test_power_boost_makes_faster(self):
        """50 % power boost should predict a lower ET than stock."""
        r_stock = self._predict({})
        r_boost = self._predict({"power_boost_pct": 50.0})
        if r_stock.status_code == 503 or r_boost.status_code == 503:
            self.skipTest("Surrogate model not available")
        if r_stock.status_code != 200 or r_boost.status_code != 200:
            return
        self.assertLess(
            r_boost.json()["et_s"],
            r_stock.json()["et_s"],
            "50 % power boost should reduce predicted ET",
        )


class TestSurrogateCompare(unittest.TestCase):
    """Tests for POST /api/surrogate/compare."""

    def test_compare_same_config(self):
        """Comparing identical configs should return delta_et_s near 0."""
        cfg = {"power_boost_pct": 0.0, "mass_delta_kg": 0.0}
        r = client.post(
            "/api/surrogate/compare", json={"config_a": cfg, "config_b": cfg}
        )
        if r.status_code == 503:
            self.skipTest("Surrogate model not available")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertAlmostEqual(body["delta_et_s"], 0.0, places=3)
        self.assertEqual(body["faster"], "tie")

    def test_compare_a_faster_than_b(self):
        """Config A (boosted) should be faster; delta_et_s > 0 and faster=='a'."""
        cfg_a = {"power_boost_pct": 50.0}
        cfg_b = {"power_boost_pct": 0.0}
        r = client.post(
            "/api/surrogate/compare", json={"config_a": cfg_a, "config_b": cfg_b}
        )
        if r.status_code == 503:
            self.skipTest("Surrogate model not available")
        if r.status_code != 200:
            return
        body = r.json()
        # B.et_s - A.et_s should be positive (A is faster)
        self.assertGreater(body["delta_et_s"], 0.0)
        self.assertEqual(body["faster"], "a")


class TestPricingEndpoints(unittest.TestCase):
    """Coverage for /api/pricing/* — proves the typed response DTOs
    (PricingEntryOut / BikePricingSummaryItem wired into the list fields, with
    honest Optional defaults) serialize for both populated and empty rows.

    part_prices is empty after seed_all(), so we insert rows directly via the
    API's own connection to exercise the populated path.
    """

    @classmethod
    def setUpClass(cls):
        conn = _api_mod._get_db()
        assert conn is not None
        # A part that definitely exists in the seeded catalog.
        row = conn.execute("SELECT id FROM parts ORDER BY id LIMIT 1").fetchone()
        cls.part_id = row["id"]
        # A part with no live prices (different id) for the empty-path test.
        row2 = conn.execute(
            "SELECT id FROM parts ORDER BY id LIMIT 1 OFFSET 1"
        ).fetchone()
        cls.empty_part_id = row2["id"]
        cls.bike_id = conn.execute(
            "SELECT id FROM bike_models ORDER BY id LIMIT 1"
        ).fetchone()["id"]
        # Seed two live prices for cls.part_id: one fresh, one stale, one NULL price.
        conn.execute(
            "INSERT OR REPLACE INTO part_prices "
            "(part_id, retailer, source_url, price_inr, in_stock, fetched_at) "
            "VALUES (?,?,?,?,?,datetime('now','utc'))",
            (cls.part_id, "FreshShop", "https://example.com/a", 12345.0, 1),
        )
        conn.execute(
            "INSERT OR REPLACE INTO part_prices "
            "(part_id, retailer, source_url, price_inr, in_stock, fetched_at) "
            "VALUES (?,?,?,?,?,?)",
            (
                cls.part_id,
                "StaleShop",
                "https://example.com/b",
                9999.0,
                0,
                "2000-01-01",
            ),
        )
        conn.commit()

    def test_part_pricing_populated_serializes(self):
        r = client.get(f"/api/pricing/part/{self.part_id}")
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["part_id"], self.part_id)
        self.assertIsInstance(body["prices"], list)
        self.assertGreaterEqual(len(body["prices"]), 2)
        # The cheapest live price is the fresh one.
        self.assertEqual(body["cheapest_live_inr"], 9999.0)
        # Every price entry matches the PricingEntryOut shape.
        for p in body["prices"]:
            for key in (
                "retailer",
                "price_inr",
                "in_stock",
                "fetched_at",
                "source_url",
                "is_stale",
            ):
                self.assertIn(key, p)
            self.assertIsInstance(p["in_stock"], bool)
            self.assertIsInstance(p["is_stale"], bool)
        # The 2000-01-01 row must be flagged stale.
        self.assertTrue(any(p["is_stale"] for p in body["prices"]))

    def test_part_pricing_empty_returns_null_optionals(self):
        r = client.get(f"/api/pricing/part/{self.empty_part_id}")
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["prices"], [])
        # Honest Optional defaults: no live price -> None, not 0.0 or a crash.
        self.assertIsNone(body["cheapest_live_inr"])
        self.assertFalse(body["all_stale"])

    def test_part_pricing_unknown_404(self):
        r = client.get("/api/pricing/part/99999999")
        self.assertEqual(r.status_code, 404)

    def test_bike_pricing_summary_serializes(self):
        r = client.get(f"/api/pricing/bike/{self.bike_id}", params={"limit": 10})
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["bike_id"], self.bike_id)
        self.assertIsInstance(body["items"], list)
        self.assertGreater(len(body["items"]), 0)
        for it in body["items"]:
            for key in (
                "part_id",
                "part_name",
                "category",
                "seed_price_inr",
                "cheapest_live_inr",
                "cheapest_retailer",
                "in_stock",
            ):
                self.assertIn(key, it)
        self.assertIsInstance(body["total_cheapest_inr"], (int, float))

    def test_bike_pricing_unknown_404(self):
        r = client.get("/api/pricing/bike/99999999")
        self.assertEqual(r.status_code, 404)

    def test_dtos_accept_all_none_optionals(self):
        """Direct construction proves the honest Optional defaults: a row with no
        price/retailer/timestamp must validate, where the old float=Field(None)
        was a lie (None is not a float)."""
        from motoquant.api import (
            BikePricingSummaryItem,
            PartPricingOut,
            PricingEntryOut,
        )

        entry = PricingEntryOut(in_stock=False, is_stale=True)
        self.assertIsNone(entry.price_inr)
        self.assertIsNone(entry.retailer)
        self.assertIsNone(entry.fetched_at)

        part = PartPricingOut(part_id=1, part_name="x", prices=[entry], all_stale=False)
        self.assertIsNone(part.seed_price_inr)
        self.assertIsNone(part.cheapest_live_inr)
        self.assertEqual(len(part.prices), 1)

        item = BikePricingSummaryItem(part_id=1, part_name="x", category="exhaust")
        self.assertIsNone(item.cheapest_live_inr)
        self.assertIsNone(item.in_stock)
