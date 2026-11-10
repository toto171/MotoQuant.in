"""
Review-fix regressions, backend lane (Nov 2026).

Every test drives the production path (HTTP through TestClient, the CLI entry
point, or the public function) and fails on the pre-fix code.
"""

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REPO_DB = os.path.join(_REPO, "motoquant.db")

_TMP_DIR = None
_PRIOR_DB_ENV = None
api = None
client = None


def setUpModule():
    global _TMP_DIR, _PRIOR_DB_ENV, api, client
    _TMP_DIR = tempfile.mkdtemp(prefix="mq_review_be_")
    shutil.copyfile(_REPO_DB, os.path.join(_TMP_DIR, "motoquant.db"))
    _PRIOR_DB_ENV = os.environ.get("MOTOQUANT_DB")
    os.environ["MOTOQUANT_DB"] = os.path.join(_TMP_DIR, "motoquant.db")
    import motoquant.api as _api

    api = _api
    _close_api_db()
    client = TestClient(api.app)


def tearDownModule():
    _close_api_db()
    if _PRIOR_DB_ENV is None:
        os.environ.pop("MOTOQUANT_DB", None)
    else:
        os.environ["MOTOQUANT_DB"] = _PRIOR_DB_ENV
    shutil.rmtree(_TMP_DIR, ignore_errors=True)


def _close_api_db():
    if getattr(api, "_db_conn", None) is not None:
        try:
            api._db_conn.close()
        except Exception:
            pass
        api._db_conn = None


def _db_path():
    return os.environ["MOTOQUANT_DB"]


# ── api-1: catalog / stock caches must not go stale after repeated writes ────


class TestCatalogCacheFreshness(unittest.TestCase):
    def test_repeated_identical_writes_each_refresh_venues(self):
        conn = api._get_db()
        client.get("/api/venues")  # warm
        for i in range(4):
            conn.execute("UPDATE venues SET name = name || ? WHERE id = 1", (str(i),))
            conn.commit()
            db_name = conn.execute("SELECT name FROM venues WHERE id=1").fetchone()[0]
            body = client.get("/api/venues").json()
            rows = body["venues"] if isinstance(body, dict) else body
            api_name = next(v["name"] for v in rows if v["id"] == 1)
            self.assertEqual(api_name, db_name, f"stale after write #{i}")

    def test_etag_revalidation_sees_every_write(self):
        conn = api._get_db()
        r = client.get("/api/venues")
        etag = r.headers["etag"]
        for i in range(3):
            conn.execute("UPDATE venues SET name = name || 'z' WHERE id = 1")
            conn.commit()
            r2 = client.get("/api/venues", headers={"If-None-Match": etag})
            self.assertEqual(r2.status_code, 200, f"304 on stale ETag after write {i}")
            etag = r2.headers["etag"]
            self.assertEqual(
                client.get("/api/venues", headers={"If-None-Match": etag}).status_code,
                304,
            )

    def test_write_from_a_second_connection_is_seen(self):
        api._get_db()
        before = client.get("/api/venues").json()
        rows = before["venues"] if isinstance(before, dict) else before
        other = sqlite3.connect(_db_path())
        other.execute("UPDATE venues SET name = 'OTHER-CONN' WHERE id = 1")
        other.commit()
        other.close()
        after = client.get("/api/venues").json()
        rows = after["venues"] if isinstance(after, dict) else after
        self.assertEqual(next(v["name"] for v in rows if v["id"] == 1), "OTHER-CONN")

    def test_price_refresh_twice_then_parts_fresh(self):
        from datetime import datetime, timezone

        from motoquant.database import retail_adapters

        conn = api._get_db()
        pid = conn.execute(
            "SELECT id FROM parts WHERE price_inr IS NOT NULL LIMIT 1"
        ).fetchone()[0]
        conn.execute(
            "UPDATE parts SET retailer='tester', retailer_url='http://x.invalid/p' "
            "WHERE id=?",
            (pid,),
        )
        conn.commit()
        orig = retail_adapters.fetch_price
        try:
            for price in (1111.0, 2222.0):
                retail_adapters.fetch_price = lambda url, p=price: (
                    retail_adapters.PriceResult(
                        price_inr=p,
                        in_stock=True,
                        fetched_at=datetime.now(timezone.utc),
                        source_url=url,
                        retailer="tester",
                    )
                )
                conn.execute(
                    "UPDATE part_prices SET fetched_at='2000-01-01T00:00:00+00:00' "
                    "WHERE part_id=?",
                    (pid,),
                )
                conn.commit()  # outside the one-hour force floor
                r = client.post(f"/api/pricing/refresh/{pid}?force=true")
                self.assertEqual(r.status_code, 200, r.text)
                live = conn.execute(
                    "SELECT price_inr FROM part_prices WHERE part_id=? AND retailer='tester'",
                    (pid,),
                ).fetchone()[0]
                self.assertEqual(live, price)
                # the catalog byte cache must be rebuilt after each refresh
                before = api.catalog_cache_stats["misses"]
                client.get("/api/parts?limit=5")
                self.assertEqual(api.catalog_cache_stats["misses"], before + 1)
        finally:
            retail_adapters.fetch_price = orig

    def test_stock_baseline_follows_a_catalog_write(self):
        conn = api._get_db()
        part = client.get("/api/parts?bike_id=192&limit=1").json()["parts"][0]["id"]
        body = {"bike_id": 192, "venue_id": 1, "part_ids": [part]}
        base_alt = conn.execute("SELECT altitude_m FROM venues WHERE id=1").fetchone()[
            0
        ]
        stocks = []
        # identical UPDATE text each time: the second and third used to be
        # invisible to the generation counter
        for alt in (base_alt + 1500.0, base_alt + 3000.0, base_alt + 4500.0):
            conn.execute("UPDATE venues SET altitude_m = ? WHERE id = 1", (alt,))
            conn.commit()
            r = client.post("/api/simulate/quick", json=body).json()
            plain = client.post(
                "/api/simulate/quick", json={"bike_id": 192, "venue_id": 1}
            ).json()
            self.assertEqual(r["stock_et_s"], plain["et_quarter_s"])
            stocks.append(r["stock_et_s"])
        self.assertEqual(len(set(stocks)), 3, stocks)


# ── SEC-3: anonymous DB-writing routes are rate limited and queue-capped ─────


class TestAnonymousWritersAreFused(unittest.TestCase):
    def setUp(self):
        from motoquant import ratelimit

        ratelimit.reset()

    def test_suggest_is_rate_limited(self):
        codes = [
            client.post(
                "/api/bikes/suggest", json={"make": "Test", "model": f"M{i}"}
            ).status_code
            for i in range(8)
        ]
        self.assertEqual(codes[:5], [201] * 5)
        self.assertIn(429, codes[5:])

    def test_spec_correct_is_rate_limited_in_its_own_bucket(self):
        body = {"bike_id": 192, "field_name": "peak_power_hp", "proposed_value": "50"}
        codes = [
            client.post("/api/specs/correct", json=body).status_code for _ in range(8)
        ]
        self.assertEqual(codes[:5], [201] * 5, codes)
        self.assertIn(429, codes[5:])

    def test_surrogate_routes_are_rate_limited(self):
        codes = [
            client.post("/api/surrogate/predict", json={}).status_code
            for _ in range(70)
        ]
        self.assertIn(429, codes)

    def test_queue_cap_stops_unbounded_growth(self):
        conn = api._get_db()
        old = api.MAX_PENDING_SUBMISSIONS
        n = conn.execute("SELECT COUNT(*) FROM bike_suggestions").fetchone()[0]
        api.MAX_PENDING_SUBMISSIONS = n
        try:
            r = client.post("/api/bikes/suggest", json={"make": "Cap", "model": "Full"})
        finally:
            api.MAX_PENDING_SUBMISSIONS = old
        self.assertEqual(r.status_code, 503)
        self.assertEqual(
            conn.execute("SELECT COUNT(*) FROM bike_suggestions").fetchone()[0], n
        )


# ── WB-4: every sim route accepts the shared conditions fields ───────────────


def _wait_job(job_id, timeout_s=240.0):
    import time

    t0 = time.time()
    while time.time() - t0 < timeout_s:
        j = client.get(f"/api/jobs/{job_id}").json()
        if j["status"] in ("done", "error", "cancelled"):
            return j
        time.sleep(0.05)
    raise AssertionError("job timeout")


class TestSimRoutesAcceptConditions(unittest.TestCase):
    BASE = {"bike_preset": "gsxr1000_k5"}

    def setUp(self):
        from motoquant import ratelimit

        ratelimit.reset()

    def _run(self, path, extra=None, base=None):
        body = dict(base or self.BASE)
        body.update(extra or {})
        r = client.post(path, json=body)
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def _check(self, path, et_key, base=None):
        plain = self._run(path, base=base)
        high = self._run(path, {"altitude_m": 3000.0}, base=base)
        env = high["environment"]
        self.assertEqual(env["altitude_m"], 3000.0)
        self.assertEqual(env["source"], "manual")
        self.assertEqual(plain["environment"]["source"], "default")
        self.assertNotEqual(plain[et_key], high[et_key])
        # pressure alone is also a manual condition
        p = self._run(path, {"pressure_hpa": 900.0}, base=base)
        self.assertEqual(p["environment"]["pressure_hpa"], 900.0)
        self.assertEqual(p["environment"]["source"], "manual")

    def test_quick(self):
        self._check("/api/simulate/quick", "et_quarter_s")

    def test_full(self):
        self._check("/api/simulate", "et_quarter_s")

    def test_topspeed(self):
        self._check(
            "/api/simulate/top-speed",
            "terminal_velocity_kmh",
            base={**self.BASE, "max_time_s": 30},
        )

    def test_distance(self):
        self._check(
            "/api/simulate/distance",
            "time_s",
            base={**self.BASE, "distance_m": 500.0},
        )

    def test_compare(self):
        base = {"a_bike_preset": "gsxr1000_k5", "b_bike_preset": "yzfr1_4c8"}
        plain = self._run("/api/simulate/compare", base=base)
        high = self._run("/api/simulate/compare", {"altitude_m": 3000.0}, base=base)
        self.assertEqual(high["environment"]["altitude_m"], 3000.0)
        self.assertEqual(high["environment"]["source"], "manual")
        self.assertNotEqual(plain["a"]["et_quarter_s"], high["a"]["et_quarter_s"])
        self.assertNotEqual(plain["b"]["et_quarter_s"], high["b"]["et_quarter_s"])

    def test_job_variants(self):
        for path, extra in (
            ("/api/jobs/simulate", {}),
            ("/api/jobs/topspeed", {"max_time_s": 30}),
            (
                "/api/jobs/compare",
                {"a_bike_preset": "gsxr1000_k5", "b_bike_preset": "yzfr1_4c8"},
            ),
        ):
            body = {**extra} if "compare" in path else {**self.BASE, **extra}
            body["altitude_m"] = 3000.0
            r = client.post(path, json=body)
            self.assertEqual(r.status_code, 202, r.text)
            j = _wait_job(r.json()["job_id"])
            self.assertEqual(j["status"], "done", j)
            env = j["result"]["environment"]
            self.assertEqual(env["altitude_m"], 3000.0, path)
            self.assertEqual(env["source"], "manual", path)

    def test_stock_baseline_cache_key_includes_altitude(self):
        part = client.get("/api/parts?bike_id=192&limit=1").json()["parts"][0]["id"]
        body = {"bike_id": 192, "part_ids": [part]}
        a = client.post("/api/simulate/quick", json=body).json()
        b = client.post(
            "/api/simulate/quick", json={**body, "altitude_m": 4000.0}
        ).json()
        self.assertNotEqual(a["stock_et_s"], b["stock_et_s"])

    def test_out_of_range_altitude_is_422(self):
        r = client.post(
            "/api/simulate/quick", json={**self.BASE, "altitude_m": 99999.0}
        )
        self.assertEqual(r.status_code, 422)

    def test_echo_always_names_the_surface_simulated(self):
        r = self._run("/api/simulate/quick", {"venue_id": 13}, base={"bike_id": 192})
        self.assertEqual(r["environment"]["track_surface"], "salt")
        r = self._run("/api/simulate/quick")
        self.assertEqual(r["environment"]["track_surface"], "asphalt")

    def test_venues_list_exposes_track_surface(self):
        body = client.get("/api/venues").json()
        rows = body["venues"] if isinstance(body, dict) else body
        by_id = {v["id"]: v for v in rows}
        self.assertIn("track_surface", by_id[13])
        self.assertEqual(by_id[13]["track_surface"], "salt")


# ── physics-calibration F3: ECU speed headers ────────────────────────────────

_ECU_FACTOR = {"kmh": 1 / 3.6, "mph": 0.44704, "ms": 1.0}


@pytest.mark.parametrize(
    "header,unit",
    [
        ("GPS Speed", "kmh"),
        ("GPS Speed (mph)", "mph"),
        ("GPS Speed (km/h)", "kmh"),
        ("SPEED KPH", "kmh"),
        ("SpeedKPH", "kmh"),
        ("SpeedMPH", "mph"),
        ("Speed kph", "kmh"),
        ("Veh Spd", "kmh"),
        ("Veh Spd (mph)", "mph"),
        ("Veh Speed (km/h)", "kmh"),
        ("Speed (kph)", "kmh"),
        ("Speed [mph]", "mph"),
        ("Vehicle Speed [mi/h]", "mph"),
        ("speed_kmh", "kmh"),
        ("Speed [m/s]", "ms"),
        ("VSS (mph)", "mph"),
    ],
)
def test_ecu_speed_header_spellings(header, unit):
    from motoquant.calibration.ecu import _map_column

    std, conv = _map_column(header)
    assert std == "vehicle_speed_ms", header
    got = 1.0 if conv is None else float(conv)
    assert got == pytest.approx(_ECU_FACTOR[unit])


@pytest.mark.parametrize("header", ["Speed (knots)", "Speed (m/s2)", "Speed (kt)"])
def test_ecu_unknown_speed_unit_is_refused_with_a_warning(header):
    import warnings

    from motoquant.calibration.ecu import _map_column

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        assert _map_column(header) == (None, None)
    assert any("unrecognised speed unit" in str(x.message) for x in w)


def test_ecu_engine_speed_is_still_rpm():
    from motoquant.calibration.ecu import _map_column

    assert _map_column("Engine Speed")[0] == "rpm"


# ── analysis-nlp F7: autotune headline setup is the quickest verified one ────


class TestAutotuneHeadlineIsQuickest(unittest.TestCase):
    def test_combined_never_slower_than_either_single_knob(self):
        from motoquant.analysis.ecu_autotune import autotune
        from motoquant.database.connection import MotoQuantDB

        db = MotoQuantDB(_db_path())
        try:
            for bike_id in (3, 5):
                row = db.bikes.get_current_config(bike_id)
                cfg = db.bikes.to_config(row["id"])
                cfg.staging.two_step = True
                r = autotune(cfg).to_dict()
                comb = r["combined"]["delta_et_s"]
                for knob in ("gearing", "launch_rpm"):
                    self.assertLessEqual(
                        comb, r[knob]["delta_et_s"] + 1e-9, (bike_id, knob)
                    )
                # a knob that is not part of the winning setup is withdrawn
                if "launch_rpm" not in r["combined"]["knobs"]:
                    self.assertIsNone(r["launch_rpm"]["recommended_rpm"])
                    self.assertFalse(r["launch_rpm"]["adjustable"])
                if "gearing" not in r["combined"]["knobs"]:
                    self.assertEqual(
                        r["gearing"]["recommended_rear"], r["gearing"]["stock_rear"]
                    )
        finally:
            db.close()


# ── CLI through the real entry point (F2, F1, F5) ────────────────────────────


def _cli(*args, timeout=300):
    return subprocess.run(
        [sys.executable, "-m", "motoquant.run", "--db", _db_path(), *args],
        capture_output=True,
        text=True,
        cwd=_REPO,
        timeout=timeout,
    )


class TestCliHappyPaths(unittest.TestCase):
    def test_sim_exits_zero_and_prints_the_summary(self):
        r = _cli("sim", "--bike-id", "1", "--venue-id", "1")
        self.assertEqual(r.returncode, 0, r.stderr[-500:])
        self.assertIn("1/4 mile", r.stdout)
        self.assertNotIn("SimResult(", r.stderr)
        self.assertEqual(r.stderr.strip(), "")

    def test_sim_json_is_json_and_exits_zero(self):
        r = _cli("sim", "--bike-id", "1", "--json", "-q")
        self.assertEqual(r.returncode, 0, r.stderr[-500:])
        self.assertIn("bike", json.loads(r.stdout))

    def test_main_coerces_non_int_handler_results(self):
        from motoquant import run as run_mod

        sentinel = object()
        orig = run_mod.SUBCOMMAND_MAP["venues"]
        run_mod.SUBCOMMAND_MAP["venues"] = lambda a: sentinel
        try:
            self.assertEqual(run_mod.main(["--db", _db_path(), "venues"]), 0)
        finally:
            run_mod.SUBCOMMAND_MAP["venues"] = orig

    def test_non_positive_distance_is_a_clean_usage_error(self):
        for bad in ("-5", "0", "inf", "nan"):
            r = _cli("sim", "--bike-id", "1", "--distance", bad)
            self.assertEqual(r.returncode, 2, bad)
            self.assertNotIn("Traceback", r.stderr, bad)
            self.assertIn("--distance", r.stderr)

    def test_bikes_fitments_lists_and_json_parses(self):
        r = _cli("bikes", "--fitments", "3")
        self.assertEqual(r.returncode, 0, r.stderr[-500:])
        self.assertIn("Tire Fitments", r.stdout)
        j = _cli("bikes", "--fitments", "3", "--json")
        self.assertEqual(j.returncode, 0)
        self.assertIsInstance(json.loads(j.stdout), list)

    def test_analysis_roi_filters_to_compatible_parts(self):
        r = _cli(
            "analysis", "roi", "--bike-id", "66", "--category", "exhaust", "--json"
        )
        self.assertEqual(r.returncode, 0, r.stderr[-500:])
        d = json.loads(r.stdout)
        self.assertTrue(d["parts"])
        self.assertTrue(all(p["compatible"] for p in d["parts"]))
        names = " ".join(p["name"] for p in d["parts"])
        self.assertNotIn("RX100", names)
        self.assertNotIn("Aprilia RS125", names)
        self.assertGreater(d["parts_not_listed"], 0)

        allp = _cli(
            "analysis",
            "roi",
            "--bike-id",
            "66",
            "--category",
            "exhaust",
            "--include-incompatible",
            "--json",
        )
        da = json.loads(allp.stdout)
        self.assertGreater(len(da["parts"]), len(d["parts"]))
        self.assertTrue(any(not p["compatible"] for p in da["parts"]))


class TestEngineRunArgumentValidation(unittest.TestCase):
    def test_run_rejects_non_finite_and_absurd_arguments(self):
        from motoquant import MotoQuantEngine, gsxr1000_k5

        eng = MotoQuantEngine(gsxr1000_k5())
        for kw in (
            {"max_time": float("inf")},
            {"max_time": float("nan")},
            {"max_time": 1e9},
            {"max_time": 0.0},
            {"distance": float("inf")},
            {"distance": float("nan")},
            {"distance": -5.0},
            {"distance": 1e12},
        ):
            with self.assertRaises(ValueError, msg=str(kw)):
                eng.run(**kw)

    def test_valid_run_is_unchanged(self):
        from motoquant import MotoQuantEngine, gsxr1000_k5

        et = MotoQuantEngine(gsxr1000_k5()).run().time_quarter
        # The pinned K5 reference (scripts/check_baselines.py): 10.0436 since the
        # 2026-10 rollout-timing epoch (was 9.9331 before it).
        self.assertAlmostEqual(et, 10.0436, places=3)


# ── analysis-nlp F8: sub-noise parts are not recommended ─────────────────────


class TestNoSubNoiseRecommendations(unittest.TestCase):
    def test_find_best_build_skips_sub_noise_parts(self):
        import math

        from motoquant.analysis.roi import find_best_build
        from motoquant.database.connection import MotoQuantDB

        db = MotoQuantDB(_db_path())
        try:
            cfg = db.bikes.to_config(db.bikes.get_current_config(66)["id"])
            b = find_best_build(
                cfg, 40000.0, db.parts, bike_model_id=66, min_delta_et_ms=5.0
            )
            self.assertTrue(b.selected_parts)
            for p in b.selected_parts:
                self.assertGreaterEqual(p.delta_et_s * 1000.0, 5.0, p.part_name)
                self.assertTrue(math.isfinite(p.cost_per_tenth_inr), p.part_name)
        finally:
            db.close()

    def test_cli_recommend_never_prints_inf(self):
        r = _cli("analysis", "recommend", "--bike-id", "66", "--budget", "40000")
        self.assertEqual(r.returncode, 0, r.stderr[-500:])
        self.assertNotIn("inf", r.stdout.lower().replace("info", ""))
        self.assertNotIn("nan", r.stdout.lower())


# ── analysis-nlp F6: the optimizer never returns worse than its best single ──


class TestOptimizerNeverWorseThanBestSinglePart(unittest.TestCase):
    def test_swap_repair_falls_back_to_the_best_single_part(self):
        from motoquant.analysis import build_optimizer as bo
        from motoquant.analysis.roi import compute_parts_roi
        from motoquant.database.connection import MotoQuantDB

        db = MotoQuantDB(_db_path())
        try:
            cfg = db.bikes.to_config(db.bikes.get_current_config(3)["id"])
            pool = [139, 140, 333, 50, 348]
            ind = compute_parts_roi(cfg, pool, db.parts, bike_model_id=3)
            by = {r.part_id: r for r in ind}
            stacked = [by[i] for i in (140, 333, 50, 348)]
            pred = bo.SurrogatePredictor(None)
            out, _ = bo._swap_repair(
                cfg,
                stacked,
                ind,
                400000.0,
                "min_et",
                parts_repo=db.parts,
                predictor=pred,
                position_of={},
                slot_of={},
            )

            def build_et(parts):
                c = db.parts.apply_multiple([r.part_id for r in parts], cfg)
                return pred.full_sim(c)[0]

            best_single = min(build_et([r]) for r in ind if r.price_inr <= 400000.0)
            self.assertLessEqual(build_et(out), best_single + 1e-9)
        finally:
            db.close()
