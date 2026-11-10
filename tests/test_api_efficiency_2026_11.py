"""
API efficiency / robustness regressions (Nov 2026 audit lane "api").

Every test drives the production path: HTTP through ``TestClient`` for route
behaviour, the public registry/compat functions for library behaviour. Each
one fails on the pre-fix code.

F1/F8  job registry bounds retained result BYTES; cancelled jobs expire
F6     top-speed timeseries payload is bounded + rounded; scalars untouched
F3     quick-sim stock baseline is memoised (result-identical)
F2     catalog GETs are served from a generation-keyed cache with ETag/304
DP-F6  fitment rules are parsed once per distinct rules string
F4     NaN/Infinity request bodies give a JSON-safe 422, not a 500
F5     out-of-range integer ids give 404/422, not a 500
F7     unknown venue/tyre ids 404 on every sim route; unknown part ids are
       reported in ``parts_skipped``
"""

import json
import os
import random
import shutil
import tempfile
import time
import unittest
from datetime import datetime, timezone

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

_REPO_DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "motoquant.db")

_TMP_DIR = None
_PRIOR_DB_ENV = None
api = None
client = None
HUGE = 10**20


def setUpModule():
    global _TMP_DIR, _PRIOR_DB_ENV, api, client
    _TMP_DIR = tempfile.mkdtemp(prefix="mq_api_eff_")
    db_copy = os.path.join(_TMP_DIR, "motoquant.db")
    shutil.copyfile(_REPO_DB, db_copy)
    _PRIOR_DB_ENV = os.environ.get("MOTOQUANT_DB")
    os.environ["MOTOQUANT_DB"] = db_copy
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


def _sql_counter():
    """Install a trace callback on the API connection; returns (list, remove)."""
    conn = api._get_db()
    seen: list[str] = []
    conn.set_trace_callback(seen.append)
    return seen, lambda: conn.set_trace_callback(None)


def _sim_counter():
    """Count full RK4 runs through the API's engine."""
    calls = {"n": 0}
    orig = api.MotoQuantEngine.run

    def counting(self, *a, **k):
        calls["n"] += 1
        return orig(self, *a, **k)

    api.MotoQuantEngine.run = counting
    return calls, lambda: setattr(api.MotoQuantEngine, "run", orig)


def _effective_parts(bike_id, n=2):
    """Compatible part ids that actually change the config."""
    r = client.get(
        "/api/parts", params={"bike_id": bike_id, "limit": 400, "include_rules": "true"}
    )
    assert r.status_code == 200
    out = []
    for p in r.json()["parts"]:
        if (p.get("param_deltas") or p.get("param_overrides")) and not p.get(
            "param_multipliers"
        ):
            if p["category_name"] in ("exhaust", "air_filter", "ecu", "sprocket"):
                out.append(p["id"])
        if len(out) == n:
            break
    assert len(out) == n, "need real parts for the stock-cache tests"
    return out


# --------------------------------------------------------------------------
# F1 / F8 — job registry memory
# --------------------------------------------------------------------------


class TestJobRegistryBytes(unittest.TestCase):
    def setUp(self):
        from motoquant import jobs

        self.jobs = jobs
        with jobs._LOCK:
            jobs._JOBS.clear()

    def tearDown(self):
        with self.jobs._LOCK:
            self.jobs._JOBS.clear()

    def _run(self, result):
        job = self.jobs.create_job("unittest", lambda progress: result)
        deadline = time.time() + 20
        while time.time() < deadline:
            got = self.jobs.get_job(job.id)
            if got is None or got.status in ("done", "error", "cancelled"):
                return got
            time.sleep(0.01)
        raise AssertionError("job did not finish")

    def test_retained_result_bytes_stay_under_budget(self):
        rng = random.Random(7)
        payload = {"series": [rng.random() * 1000 for _ in range(60_000)]}
        budget = 6 * 1024 * 1024
        old = self.jobs.MAX_RESULT_BYTES_TOTAL
        self.jobs.MAX_RESULT_BYTES_TOTAL = budget
        try:
            last = None
            for _ in range(40):  # ~0.5 MB compressed each -> ~20 MB offered
                last = self._run(payload)
            with self.jobs._LOCK:
                retained = sum(j.result_bytes for j in self.jobs._JOBS.values())
                n_jobs = len(self.jobs._JOBS)
            self.assertLessEqual(retained, budget)
            self.assertLess(n_jobs, 40, "oldest finished jobs must be evicted")
            # The most recent result is still pollable.
            self.assertIsNotNone(self.jobs.get_job(last.id))
        finally:
            self.jobs.MAX_RESULT_BYTES_TOTAL = old

    def test_default_budget_bounds_worst_case_memory(self):
        # 200 finished jobs can never retain more than the budget (compressed
        # bytes), far under the 512 MB instance limit.
        self.assertLessEqual(self.jobs.MAX_RESULT_BYTES_TOTAL, 64 * 1024 * 1024)

    def test_running_jobs_are_never_evicted_by_the_budget(self):
        old = self.jobs.MAX_RESULT_BYTES_TOTAL
        self.jobs.MAX_RESULT_BYTES_TOTAL = 1
        try:
            running = self.jobs.Job("busy")
            running.status = "running"
            with self.jobs._LOCK:
                self.jobs._JOBS[running.id] = running
            self._run({"x": list(range(1000))})
            self.assertIn(running.id, self.jobs._JOBS)
        finally:
            self.jobs.MAX_RESULT_BYTES_TOTAL = old

    def test_result_round_trips_through_the_poll_route(self):
        req = api.TopSpeedRequest(bike_preset="gsxr1000_k5", include_timeseries=True)
        expected = json.loads(json.dumps(api._topspeed_impl(req)))
        r = client.post(
            "/api/jobs/topspeed",
            json={"bike_preset": "gsxr1000_k5", "include_timeseries": True},
        )
        self.assertEqual(r.status_code, 202)
        job_id = r.json()["job_id"]
        body = None
        deadline = time.time() + 60
        while time.time() < deadline:
            body = client.get(f"/api/jobs/{job_id}").json()
            if body["status"] in ("done", "error"):
                break
            time.sleep(0.05)
        self.assertEqual(body["status"], "done")
        self.assertEqual(
            set(body), {"job_id", "kind", "status", "progress", "stage", "result"}
        )
        self.assertEqual(body["result"], expected)
        # polling twice returns the same content
        self.assertEqual(client.get(f"/api/jobs/{job_id}").json()["result"], expected)

    def test_poll_envelope_for_non_done_states_is_unchanged(self):
        self.assertEqual(client.get("/api/jobs/does-not-exist").status_code, 404)
        j = self.jobs.Job("unittest")
        j.status = "error"
        j.error = "boom"
        with self.jobs._LOCK:
            self.jobs._JOBS[j.id] = j
        body = client.get(f"/api/jobs/{j.id}").json()
        self.assertEqual(body["status"], "error")
        self.assertEqual(body["error"], "boom")
        self.assertNotIn("result", body)

    def test_non_finite_result_values_stay_valid_json(self):
        got = self._run({"a": float("nan"), "b": [1.0, float("inf")]})
        self.assertEqual(got.result, {"a": None, "b": [1.0, None]})

    def test_cancelled_jobs_expire(self):
        now = time.time()
        j = self.jobs.Job("unittest")
        j.status = "cancelled"
        j.updated_at = now - self.jobs.JOB_TTL_S - 5
        done = self.jobs.Job("unittest")
        done.status = "done"
        done.updated_at = now - self.jobs.JOB_TTL_S - 5
        with self.jobs._LOCK:
            self.jobs._JOBS[j.id] = j
            self.jobs._JOBS[done.id] = done
            self.jobs._evict_locked(now)
            self.assertNotIn(done.id, self.jobs._JOBS)
            self.assertNotIn(j.id, self.jobs._JOBS)


# --------------------------------------------------------------------------
# F6 — top-speed timeseries payload
# --------------------------------------------------------------------------


class TestTopSpeedPayload(unittest.TestCase):
    BODY = {"bike_preset": "hayabusa_gen1"}

    def test_timeseries_is_bounded_rounded_and_keeps_keys(self):
        r = client.post(
            "/api/simulate/top-speed", json={**self.BODY, "include_timeseries": True}
        )
        self.assertEqual(r.status_code, 200)
        ts = r.json()["timeseries"]
        self.assertEqual(
            set(ts), {"t", "v_ms", "v_kmh", "rpm", "gear", "power_kw", "x_m"}
        )
        n = len(ts["t"])
        self.assertLessEqual(n, api.TOPSPEED_MAX_SERIES_POINTS)
        for k, v in ts.items():
            self.assertEqual(len(v), n, k)
        # Raw payload well under the 1.6 MB the unbounded series produced.
        self.assertLess(len(r.content), 300_000)
        # 17-digit floats are gone.
        self.assertTrue(all(len(repr(x)) <= 12 for x in ts["t"]))
        self.assertTrue(all(len(repr(x)) <= 12 for x in ts["v_kmh"]))

    def test_scalars_come_from_the_full_resolution_run(self):
        with_ts = client.post(
            "/api/simulate/top-speed", json={**self.BODY, "include_timeseries": True}
        ).json()
        without = client.post("/api/simulate/top-speed", json=self.BODY).json()
        series = with_ts.pop("timeseries")
        self.assertEqual(with_ts, without)

        # ...and they are exactly what the engine reports for the full run.
        cfg = api._build_config(None, "hayabusa_gen1", 0.0, 0.0, 75.0, None, None, None)
        full = api.MotoQuantEngine(cfg).run_top_speed(max_time=120.0)
        self.assertEqual(
            without["terminal_velocity_kmh"], round(full.terminal_velocity_kmh, 1)
        )
        self.assertEqual(
            without["time_to_terminal_s"], round(full.time_to_terminal_s, 2)
        )
        self.assertEqual(
            without["distance_to_terminal_m"], round(full.distance_to_terminal_m, 1)
        )
        # The decimated series still spans the run: first sample, last sample
        # and the peak speed are all preserved.
        sim = full.full_sim
        stride = max(1, int(0.01 / max(sim.dt, 0.0001)))
        t_full = sim.t[::stride]
        v_full = sim.v[::stride]
        self.assertEqual(series["t"][0], round(float(t_full[0]), 3))
        self.assertEqual(series["t"][-1], round(float(t_full[-1]), 3))
        self.assertEqual(max(series["v_ms"]), round(float(v_full.max()), 3))
        self.assertTrue(all(b > a for a, b in zip(series["t"], series["t"][1:])))


# --------------------------------------------------------------------------
# F3 — stock baseline memoisation
# --------------------------------------------------------------------------


class TestQuickSimStockCache(unittest.TestCase):
    BIKE = 192

    def setUp(self):
        api._stock_cache.clear()
        self.parts = _effective_parts(self.BIKE, 2)
        self.sims, self._undo = _sim_counter()

    def tearDown(self):
        self._undo()
        api._stock_cache.clear()

    def _quick(self, **kw):
        body = {"bike_id": self.BIKE, "part_ids": self.parts, **kw}
        r = client.post("/api/simulate/quick", json=body)
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def test_second_request_skips_the_stock_run_and_is_identical(self):
        cold = self._quick()
        self.assertEqual(self.sims["n"], 2)
        self.sims["n"] = 0
        warm = self._quick()
        self.assertEqual(self.sims["n"], 1)
        self.assertEqual(cold, warm)
        self.assertIsNotNone(cold["stock_et_s"])
        self.assertEqual(
            cold["et_delta_s"], round(cold["et_quarter_s"] - cold["stock_et_s"], 4)
        )

    def test_no_parts_run_seeds_the_cache_with_the_same_number(self):
        plain = self._quick(part_ids=[])
        self.assertEqual(self.sims["n"], 1)
        self.sims["n"] = 0
        withp = self._quick()
        self.assertEqual(self.sims["n"], 1)
        self.assertEqual(withp["stock_et_s"], plain["et_quarter_s"])
        # identical to an uncached computation
        api._stock_cache.clear()
        self.sims["n"] = 0
        uncached = self._quick()
        self.assertEqual(self.sims["n"], 2)
        self.assertEqual(uncached["stock_et_s"], withp["stock_et_s"])
        self.assertEqual(uncached["et_delta_s"], withp["et_delta_s"])

    def test_changing_any_keyed_input_misses(self):
        self._quick()
        variants = [
            {"rider_mass_kg": 80.0},
            {"power_boost_pct": 3.0},
            {"mass_delta_kg": -2.0},
            {"ambient_temp_c": 30.0},
            {"track_temp_c": 45.0},
            {"humidity_pct": 70.0},
            {"headwind_kmh": 5.0},
            {"venue_id": 1},
        ]
        for v in variants:
            self.sims["n"] = 0
            self._quick(**v)
            self.assertEqual(self.sims["n"], 2, v)

    def test_catalog_generation_bump_invalidates(self):
        from motoquant.database.connection import bump_catalog_generation

        self._quick()
        bump_catalog_generation()
        self.sims["n"] = 0
        self._quick()
        self.assertEqual(self.sims["n"], 2)

    def test_identical_compare_runs_one_sim(self):
        body = {
            "a_bike_id": self.BIKE,
            "b_bike_id": self.BIKE,
            "a_part_ids": self.parts,
            "b_part_ids": self.parts,
        }
        r = client.post("/api/simulate/compare", json=body)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.sims["n"], 1)
        j = r.json()
        self.assertEqual(j["delta"]["et_s"], 0.0)
        self.assertEqual(j["delta"]["faster"], "tie")
        self.assertEqual(j["a"]["et_quarter_s"], j["b"]["et_quarter_s"])
        # different builds still run both
        self.sims["n"] = 0
        body["b_part_ids"] = []
        client.post("/api/simulate/compare", json=body)
        self.assertEqual(self.sims["n"], 2)


# --------------------------------------------------------------------------
# F2 — catalog response cache
# --------------------------------------------------------------------------

CATALOG_URLS = [
    "/api/bikes?limit=2000",
    "/api/bikes/192",
    "/api/parts?limit=2000",
    "/api/parts?bike_id=192&compatible_only=false&limit=2000",
    "/api/parts/categories",
    "/api/tires?limit=2000",
    "/api/venues",
]


class TestCatalogCache(unittest.TestCase):
    def test_second_identical_request_hits_the_cache(self):
        for url in CATALOG_URLS:
            with self.subTest(url=url):
                first = client.get(url)
                self.assertEqual(first.status_code, 200)
                seen, undo = _sql_counter()
                try:
                    second = client.get(url)
                finally:
                    undo()
                self.assertEqual(second.content, first.content)
                self.assertEqual(
                    [s for s in seen if not s.startswith("SELECT 1")],
                    [],
                    "cache hit must not touch the catalog tables",
                )

    def test_cache_headers_and_conditional_get(self):
        r = client.get("/api/parts?limit=50")
        etag = r.headers["etag"]
        self.assertTrue(etag.startswith('W/"'))
        self.assertEqual(
            r.headers["cache-control"],
            "public, max-age=300, stale-while-revalidate=3600",
        )
        again = client.get("/api/parts?limit=50", headers={"If-None-Match": etag})
        self.assertEqual(again.status_code, 304)
        self.assertEqual(again.content, b"")
        self.assertEqual(again.headers["etag"], etag)
        stale = client.get("/api/parts?limit=50", headers={"If-None-Match": 'W/"nope"'})
        self.assertEqual(stale.status_code, 200)
        self.assertEqual(stale.headers["etag"], etag)

    def test_errors_are_not_cached_or_given_cache_headers(self):
        r = client.get("/api/bikes/999999")
        self.assertEqual(r.status_code, 404)
        self.assertNotIn("etag", r.headers)

    def test_variants_do_not_collide(self):
        a = client.get("/api/parts?limit=5").json()
        b = client.get("/api/parts?limit=9").json()
        self.assertEqual(len(a["parts"]), 5)
        self.assertEqual(len(b["parts"]), 9)
        o0 = client.get("/api/bikes?limit=3&offset=0").json()["bikes"]
        o1 = client.get("/api/bikes?limit=3&offset=3").json()["bikes"]
        self.assertNotEqual([x["id"] for x in o0], [x["id"] for x in o1])
        c1 = client.get("/api/parts?bike_id=192&compatible_only=true&limit=2000").json()
        c2 = client.get(
            "/api/parts?bike_id=192&compatible_only=false&limit=2000"
        ).json()
        self.assertLess(len(c1["parts"]), len(c2["parts"]))
        e1 = client.get("/api/parts?category=exhaust&limit=2000").json()
        e2 = client.get("/api/parts?category=air_filter&limit=2000").json()
        self.assertNotEqual(e1["total"], e2["total"])
        s1 = client.get("/api/tires?compound=sport&limit=2000").json()
        s2 = client.get("/api/tires?limit=2000").json()
        self.assertLess(len(s1["tires"]), len(s2["tires"]))

    def test_price_refresh_invalidates(self):
        from motoquant.database import retail_adapters
        from motoquant.database.connection import catalog_generation

        conn = api._get_db()
        part_id = conn.execute(
            "SELECT id FROM parts WHERE price_inr IS NOT NULL LIMIT 1"
        ).fetchone()[0]
        conn.execute(
            "UPDATE parts SET retailer='tester', retailer_url='http://x.invalid/p' "
            "WHERE id=?",
            (part_id,),
        )
        conn.commit()
        client.get("/api/parts?limit=5")  # warm
        gen = catalog_generation()
        orig = retail_adapters.fetch_price
        retail_adapters.fetch_price = lambda url: retail_adapters.PriceResult(
            price_inr=1234.0,
            in_stock=True,
            fetched_at=datetime.now(timezone.utc),
            source_url=url,
            retailer="tester",
        )
        try:
            r = client.post(f"/api/pricing/refresh/{part_id}?force=true")
        finally:
            retail_adapters.fetch_price = orig
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["status"], "refreshed")
        self.assertGreater(catalog_generation(), gen)
        seen, undo = _sql_counter()
        try:
            client.get("/api/parts?limit=5")
        finally:
            undo()
        self.assertTrue(any("FROM parts" in s for s in seen), "must re-query")

    def test_runtime_write_to_a_catalog_table_invalidates(self):
        from motoquant.database.connection import catalog_generation

        conn = api._get_db()
        gen = catalog_generation()
        conn.execute("UPDATE venues SET name = name WHERE id = 1")
        conn.commit()
        self.assertGreater(catalog_generation(), gen)
        gen = catalog_generation()
        conn.execute("SELECT * FROM venues").fetchall()
        self.assertEqual(catalog_generation(), gen, "reads must not bump")

    def test_non_catalog_writes_do_not_invalidate(self):
        from motoquant.database.connection import catalog_generation

        client.get("/api/venues")
        gen = catalog_generation()
        r = client.post(
            "/api/simulate/save",
            json={"bike_id": 192, "et_quarter_s": 13.5, "trap_speed_kmh": 160.0},
        )
        self.assertIn(r.status_code, (200, 201), r.text)
        self.assertEqual(catalog_generation(), gen)

    def test_parts_list_omits_heavy_rule_fields_unless_asked(self):
        plain = client.get("/api/parts?bike_id=192&limit=50").json()["parts"][0]
        self.assertNotIn("fitment_rules", plain)
        self.assertNotIn("specifications", plain)
        self.assertIn("compatible", plain)
        full = client.get("/api/parts?bike_id=192&limit=50&include_rules=true").json()[
            "parts"
        ][0]
        self.assertIn("fitment_rules", full)
        self.assertIn("specifications", full)
        detail_free = client.get("/api/parts?limit=5").json()["parts"][0]
        self.assertNotIn("fitment_rules", detail_free)

    def test_ids_only_mode(self):
        full = client.get(
            "/api/parts?bike_id=192&compatible_only=true&limit=5000"
        ).json()
        ids = client.get(
            "/api/parts?bike_id=192&compatible_only=true&limit=5000&fields=id"
        )
        self.assertEqual(ids.status_code, 200)
        body = ids.json()
        self.assertEqual(body["part_ids"], [p["id"] for p in full["parts"]])
        self.assertEqual(body["total"], full["total"])
        self.assertEqual(body["bike_id"], 192)
        self.assertTrue(body["compatible_only"])
        self.assertNotIn("parts", body)
        self.assertLess(
            len(ids.content),
            len(
                client.get(
                    "/api/parts?bike_id=192&compatible_only=true&limit=5000"
                ).content
            )
            // 5,
        )
        self.assertEqual(client.get("/api/parts?fields=bogus").status_code, 422)

    def test_direct_function_call_still_returns_a_plain_dict(self):
        # The MCP local backend calls route functions directly, without a
        # request; they must keep returning dicts.
        out = api.list_bikes(
            search=None, manufacturer=None, category=None, limit=3, offset=0
        )
        self.assertEqual(len(out["bikes"]), 3)
        self.assertIsInstance(api.get_bike(192), dict)
        self.assertIsInstance(api.list_venues(), dict)


# --------------------------------------------------------------------------
# data-pipeline F6 — fitment rule parse cache
# --------------------------------------------------------------------------


class TestCompatibilityParseCache(unittest.TestCase):
    def test_cached_and_uncached_verdicts_are_identical(self):
        from motoquant.database.parts_repo import enrich_bike_row_for_fitment
        from motoquant.parts import compatibility as compat

        conn = api._get_db()
        parts = [dict(r) for r in conn.execute("SELECT * FROM parts").fetchall()]
        bikes = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM bike_models ORDER BY id LIMIT 4000"
            ).fetchall()
        ][::13][:40]
        self.assertEqual(len(bikes), 40)
        for b in bikes:
            enrich_bike_row_for_fitment(conn, b)

        compat._parse_rules.cache_clear()
        cached = [[compat.is_compatible(p, b) for p in parts] for b in bikes]
        info = compat._parse_rules.cache_info()
        self.assertGreater(info.hits, info.misses * 10)

        orig = compat._parse_rules
        compat._parse_rules = compat.FitmentRules.from_json  # uncached reference
        try:
            reference = [[compat.is_compatible(p, b) for p in parts] for b in bikes]
        finally:
            compat._parse_rules = orig
        self.assertEqual(cached, reference)

    def test_edited_rules_are_never_served_stale(self):
        from motoquant.parts import compatibility as compat

        rule_a = json.dumps({"tier": "exact", "bike_ids": [1]})
        rule_b = json.dumps({"tier": "exact", "bike_ids": [2]})
        bike = {"id": 1}
        self.assertTrue(compat.is_compatible({"fitment_rules": rule_a}, bike)[0])
        self.assertFalse(compat.is_compatible({"fitment_rules": rule_b}, bike)[0])


# --------------------------------------------------------------------------
# F4 / F5 / F7 — input validation
# --------------------------------------------------------------------------

NAN_BODIES = [
    ("/api/simulate", '{"bike_preset":"gsxr1000_k5","power_boost_pct":NaN}'),
    ("/api/simulate/quick", '{"bike_preset":"gsxr1000_k5","power_boost_pct":NaN}'),
    ("/api/simulate/quick", '{"bike_preset":"gsxr1000_k5","rider_mass_kg":Infinity}'),
    ("/api/jobs/simulate", '{"bike_preset":"gsxr1000_k5","mass_delta_kg":-Infinity}'),
    ("/api/simulate/top-speed", '{"bike_preset":"gsxr1000_k5","humidity_pct":NaN}'),
    ("/api/simulate/compare", '{"a_power_boost_pct":NaN}'),
    ("/api/optimize/build", '{"bike_preset":"gsxr1000_k5","rider_weight_kg":NaN}'),
]


class TestNonFiniteBodies(unittest.TestCase):
    def test_nan_and_infinity_give_a_json_safe_422(self):
        for path, raw in NAN_BODIES:
            with self.subTest(path=path, body=raw):
                r = client.post(
                    path, content=raw, headers={"Content-Type": "application/json"}
                )
                self.assertEqual(r.status_code, 422, r.text)

                def _no_constants(name):
                    raise AssertionError(f"non-JSON constant {name} in response")

                body = json.loads(r.text, parse_constant=_no_constants)
                self.assertTrue(body["detail"])
                self.assertIn("loc", body["detail"][0])

    def test_ordinary_validation_errors_keep_their_shape(self):
        r = client.post("/api/simulate/quick", json={"power_boost_pct": 9999})
        self.assertEqual(r.status_code, 422)
        d = r.json()["detail"][0]
        self.assertEqual(d["loc"], ["body", "power_boost_pct"])
        self.assertEqual(d["input"], 9999)


ID_CASES = [
    ("get", f"/api/runs/{HUGE}", None),
    ("get", f"/api/leaderboard?venue_id={HUGE}", None),
    ("get", f"/api/bikes/{HUGE}", None),
    ("get", f"/api/parts?bike_id={HUGE}", None),
    ("get", f"/api/parts?category_id={HUGE}", None),
    ("get", f"/api/pricing/part/{HUGE}", None),
    ("get", f"/api/pricing/bike/{HUGE}", None),
    ("post", f"/api/pricing/refresh/{HUGE}", None),
    ("post", "/api/simulate/quick", {"bike_id": 2**70}),
    ("post", "/api/simulate/quick", {"bike_preset": "gsxr1000_k5", "venue_id": HUGE}),
    ("post", "/api/simulate/quick", {"bike_preset": "gsxr1000_k5", "part_ids": [HUGE]}),
    (
        "post",
        "/api/simulate/quick",
        {"bike_preset": "gsxr1000_k5", "rear_tire_id": HUGE},
    ),
    ("post", "/api/simulate/compare", {"a_bike_id": HUGE}),
    (
        "post",
        "/api/simulate/save",
        {"bike_id": HUGE, "et_quarter_s": 11.0, "trap_speed_kmh": 200},
    ),
    ("post", "/api/jobs/simulate", {"bike_id": HUGE}),
    ("post", "/api/optimize/build", {"bike_id": HUGE}),
    ("post", "/api/autotune/ecu", {"bike_id": HUGE}),
]


class TestIdBounds(unittest.TestCase):
    def test_absurd_ids_are_client_errors_not_500s(self):
        for method, url, body in ID_CASES:
            with self.subTest(method=method, url=url, body=body):
                r = (
                    client.get(url)
                    if method == "get"
                    else client.post(url, json=body or {})
                )
                self.assertIn(r.status_code, (404, 422), r.text)

    def test_non_positive_ids_are_rejected(self):
        self.assertEqual(client.get("/api/bikes/0").status_code, 422)
        self.assertEqual(client.get("/api/runs/-1").status_code, 422)


UNKNOWN_REF_ROUTES = [
    ("/api/simulate", {}),
    ("/api/simulate/quick", {}),
    ("/api/simulate/top-speed", {}),
    ("/api/simulate/distance", {"distance_m": 402.336}),
    ("/api/optimize/build", {}),
    ("/api/autotune/ecu", {}),
    ("/api/jobs/simulate", {}),
    ("/api/jobs/topspeed", {}),
    ("/api/jobs/optimize", {}),
    ("/api/jobs/autotune", {}),
    ("/api/jobs/outlaw", {}),
]


class TestUnknownReferences(unittest.TestCase):
    PRESET = {"bike_preset": "gsxr1000_k5"}

    def _post(self, path, extra, **ref):
        body = {**self.PRESET, **extra}
        # request models for optimize/autotune/outlaw name the rider weight
        # differently; unknown extras are ignored by pydantic.
        body.update(ref)
        return client.post(path, json=body)

    def test_unknown_venue_is_404_everywhere(self):
        for path, extra in UNKNOWN_REF_ROUTES:
            with self.subTest(path=path):
                r = self._post(path, extra, venue_id=987654)
                self.assertEqual(r.status_code, 404, r.text)
                self.assertIn("987654", r.text)

    def test_unknown_tyre_is_404_on_sim_routes(self):
        sim_routes = [
            r
            for r in UNKNOWN_REF_ROUTES
            if "optimize" not in r[0]
            and "autotune" not in r[0]
            and "outlaw" not in r[0]
        ]
        for path, extra in sim_routes:
            for field in ("rear_tire_id", "front_tire_id"):
                with self.subTest(path=path, field=field):
                    r = self._post(path, extra, **{field: 987654})
                    self.assertEqual(r.status_code, 404, r.text)
                    self.assertIn("987654", r.text)

    def test_compare_and_its_job_reject_unknown_ids(self):
        for path in ("/api/simulate/compare", "/api/jobs/compare"):
            for field in (
                "venue_id",
                "a_rear_tire_id",
                "b_front_tire_id",
                "b_bike_id",
            ):
                with self.subTest(path=path, field=field):
                    r = client.post(
                        path,
                        json={
                            "a_bike_preset": "gsxr1000_k5",
                            "b_bike_preset": "gsxr1000_k5",
                            field: 987654,
                        },
                    )
                    self.assertEqual(r.status_code, 404, r.text)

    def test_unknown_preset_on_job_routes_is_404_at_post_time(self):
        r = client.post("/api/jobs/simulate", json={"bike_preset": "nope"})
        self.assertEqual(r.status_code, 404)

    def test_valid_references_still_work(self):
        r = client.post(
            "/api/simulate/quick",
            json={**self.PRESET, "venue_id": 1, "rear_tire_id": 1, "front_tire_id": 1},
        )
        self.assertEqual(r.status_code, 200, r.text)

    def test_unknown_part_ids_are_reported_not_fatal(self):
        real = _effective_parts(192, 1)[0]
        r = client.post(
            "/api/simulate/quick",
            json={"bike_id": 192, "part_ids": [real, 999999, 999999, 888888]},
        )
        self.assertEqual(r.status_code, 200)
        j = r.json()
        self.assertEqual([p["id"] for p in j["parts_applied"]], [real])
        self.assertEqual(j["parts_skipped"], [999999, 888888])
        ok = client.post(
            "/api/simulate/quick", json={"bike_id": 192, "part_ids": [real]}
        ).json()
        self.assertEqual(ok["parts_skipped"], [])

        only_unknown = client.post(
            "/api/simulate/quick", json={"bike_id": 192, "part_ids": [999999]}
        ).json()
        self.assertEqual(only_unknown["parts_applied"], [])
        self.assertEqual(only_unknown["parts_skipped"], [999999])
        self.assertIsNone(only_unknown["stock_et_s"])

    def test_parts_skipped_on_topspeed_distance_and_compare(self):
        r = client.post(
            "/api/simulate/top-speed",
            json={"bike_preset": "gsxr1000_k5", "part_ids": [999999]},
        )
        self.assertEqual(r.json()["parts_skipped"], [999999])
        r = client.post(
            "/api/simulate/distance",
            json={
                "bike_preset": "gsxr1000_k5",
                "distance_m": 402.336,
                "part_ids": [999999],
            },
        )
        self.assertEqual(r.json()["parts_skipped"], [999999])
        r = client.post(
            "/api/simulate/compare",
            json={
                "a_bike_preset": "gsxr1000_k5",
                "b_bike_preset": "gsxr1000_k5",
                "b_part_ids": [999999],
            },
        ).json()
        self.assertEqual(r["a"]["parts_skipped"], [])
        self.assertEqual(r["b"]["parts_skipped"], [999999])


# --------------------------------------------------------------------------
# Conditions echo (location / default marker) and shared condition fields
# --------------------------------------------------------------------------


def _venue(name_part):
    conn = api._get_db()
    row = conn.execute(
        "SELECT * FROM venues WHERE name LIKE ? OR city LIKE ?",
        (f"%{name_part}%", f"%{name_part}%"),
    ).fetchone()
    assert row is not None, name_part
    return dict(row)


class TestConditionsEcho(unittest.TestCase):
    def setUp(self):
        self.venue = _venue("Hyderabad")
        self.assertNotEqual(self.venue["id"], 1)

    def _assert_venue_echo(self, env):
        self.assertEqual(env["name"], self.venue["name"])
        self.assertFalse(env["is_default"])
        self.assertEqual(env["source"], "venue")
        self.assertEqual(env["altitude_m"], float(self.venue["altitude_m"]))
        self.assertNotIn("Aamby", env["name"])

    def test_autotune_echoes_the_requested_venue(self):
        r = client.post(
            "/api/autotune/ecu",
            json={
                "bike_preset": "gsxr1000_k5",
                "venue_id": self.venue["id"],
                "gear_span": 1,
                "launch_steps": 2,
            },
        )
        self.assertEqual(r.status_code, 200, r.text)
        env = r.json()["environment"]
        self.assertEqual(env["location"], self.venue["name"])
        self.assertEqual(env["altitude_m"], float(self.venue["altitude_m"]))
        self.assertEqual(env["name"], self.venue["name"])
        self.assertFalse(env["is_default"])

    def test_every_sim_route_echoes_the_simulated_conditions(self):
        base = {"bike_preset": "gsxr1000_k5", "venue_id": self.venue["id"]}
        for path, extra in (
            ("/api/simulate", {}),
            ("/api/simulate/quick", {}),
            ("/api/simulate/top-speed", {}),
            ("/api/simulate/distance", {"distance_m": 402.336}),
        ):
            with self.subTest(path=path):
                r = client.post(path, json={**base, **extra})
                self.assertEqual(r.status_code, 200, r.text)
                self._assert_venue_echo(r.json()["environment"])
        r = client.post(
            "/api/simulate/compare",
            json={
                "a_bike_preset": "gsxr1000_k5",
                "b_bike_preset": "gsxr1000_k5",
                "venue_id": self.venue["id"],
            },
        )
        self._assert_venue_echo(r.json()["environment"])

    def test_default_conditions_are_marked_explicitly(self):
        for path, body in (
            ("/api/simulate/quick", {"bike_preset": "gsxr1000_k5"}),
            ("/api/simulate", {"bike_preset": "gsxr1000_k5"}),
            ("/api/simulate/top-speed", {"bike_preset": "gsxr1000_k5"}),
        ):
            with self.subTest(path=path):
                env = client.post(path, json=body).json()["environment"]
                self.assertTrue(env["is_default"])
                self.assertEqual(env["source"], "default")
                self.assertEqual(env["name"], "Default conditions")
                # numbers are the bike config's own (preset: sea level 25 C)
                self.assertEqual(env["altitude_m"], 0.0)
                self.assertEqual(env["ambient_temp_c"], 25.0)
        db_bike = client.post("/api/simulate/quick", json={"bike_id": 192}).json()
        self.assertTrue(db_bike["environment"]["is_default"])
        self.assertEqual(db_bike["environment"]["altitude_m"], 679.0)

    def test_manual_values_without_a_venue_are_custom_not_default(self):
        env = client.post(
            "/api/simulate/quick",
            json={"bike_preset": "gsxr1000_k5", "ambient_temp_c": 35.0},
        ).json()["environment"]
        self.assertFalse(env["is_default"])
        self.assertEqual(env["source"], "manual")
        self.assertEqual(env["name"], "Custom conditions")
        self.assertEqual(env["ambient_temp_c"], 35.0)

    def test_autotune_default_and_manual_markers(self):
        body = {"bike_preset": "gsxr1000_k5", "gear_span": 1, "launch_steps": 2}
        env = client.post("/api/autotune/ecu", json=body).json()["environment"]
        self.assertTrue(env["is_default"])
        self.assertEqual(env["location"], "Default conditions")
        env = client.post(
            "/api/autotune/ecu", json={**body, "altitude_m": 2000, "ambient_temp_c": 33}
        ).json()["environment"]
        self.assertFalse(env["is_default"])
        self.assertEqual(env["source"], "manual")
        self.assertEqual(env["altitude_m"], 2000.0)
        self.assertEqual(env["temperature_c"], 33.0)

    def test_optimize_accepts_the_same_condition_fields_as_autotune(self):
        body = {
            "bike_preset": "gsxr1000_k5",
            "budget_inr": 20000,
            "max_candidates": 4,
            "altitude_m": 1800,
            "ambient_temp_c": 36,
            "humidity_pct": 60,
        }
        r = client.post("/api/optimize/build", json=body)
        self.assertEqual(r.status_code, 200, r.text)
        j = r.json()
        env = j["environment"]
        self.assertEqual(env["altitude_m"], 1800.0)
        self.assertEqual(env["ambient_temp_c"], 36.0)
        self.assertEqual(env["humidity_pct"], 60.0)
        self.assertEqual(env["source"], "manual")
        self.assertIn("environment_source", j)
        # conditions reach the model: thin air is slower than the default
        r0 = client.post(
            "/api/optimize/build",
            json={
                k: v
                for k, v in body.items()
                if k not in ("altitude_m", "ambient_temp_c", "humidity_pct")
            },
        ).json()
        self.assertTrue(r0["environment"]["is_default"])
        self.assertNotEqual(j["base_et_s"], r0["base_et_s"])

    def test_optimize_with_venue_echoes_it(self):
        r = client.post(
            "/api/optimize/build",
            json={
                "bike_preset": "gsxr1000_k5",
                "budget_inr": 20000,
                "max_candidates": 4,
                "venue_id": self.venue["id"],
            },
        )
        self.assertEqual(r.status_code, 200, r.text)
        self._assert_venue_echo(r.json()["environment"])

    def test_outlaw_accepts_conditions_and_echoes_them(self):
        r = client.post(
            "/api/jobs/outlaw",
            json={
                "bike_preset": "gsxr1000_k5",
                "budget_inr": 20000,
                "max_candidates": 4,
                "altitude_m": 1500,
            },
        )
        self.assertEqual(r.status_code, 202, r.text)
        job_id = r.json()["job_id"]
        body = None
        deadline = time.time() + 240
        while time.time() < deadline:
            body = client.get(f"/api/jobs/{job_id}").json()
            if body["status"] in ("done", "error"):
                break
            time.sleep(0.5)
        self.assertEqual(body["status"], "done", body)
        env = body["result"]["environment"]
        self.assertEqual(env["altitude_m"], 1500.0)
        self.assertEqual(env["source"], "manual")


class TestFullSimParity(unittest.TestCase):
    BIKE = 192

    def test_full_sim_honours_part_ids_like_quick(self):
        parts = _effective_parts(self.BIKE, 2)
        body = {"bike_id": self.BIKE, "part_ids": parts + [999999]}
        quick = client.post("/api/simulate/quick", json=body).json()
        full = client.post("/api/simulate", json=body).json()
        self.assertEqual(full["et_quarter_s"], quick["et_quarter_s"])
        self.assertEqual(full["trap_speed_kmh"], quick["trap_speed_kmh"])
        self.assertEqual(
            [p["id"] for p in full["parts_applied"]],
            [p["id"] for p in quick["parts_applied"]],
        )
        self.assertEqual(full["parts_skipped"], [999999])
        self.assertEqual(full["build_cost_inr"], quick["build_cost_inr"])
        stock = client.post("/api/simulate", json={"bike_id": self.BIKE}).json()
        self.assertNotEqual(full["et_quarter_s"], stock["et_quarter_s"])
        self.assertEqual(stock["parts_applied"], [])
        self.assertEqual(stock["parts_skipped"], [])

    def test_job_variant_honours_part_ids(self):
        parts = _effective_parts(self.BIKE, 1)
        body = {"bike_id": self.BIKE, "part_ids": parts}
        quick = client.post("/api/simulate/quick", json=body).json()
        job_id = client.post("/api/jobs/simulate", json=body).json()["job_id"]
        out = None
        deadline = time.time() + 60
        while time.time() < deadline:
            out = client.get(f"/api/jobs/{job_id}").json()
            if out["status"] in ("done", "error"):
                break
            time.sleep(0.05)
        self.assertEqual(out["status"], "done", out)
        self.assertEqual(out["result"]["et_quarter_s"], quick["et_quarter_s"])
        self.assertEqual(len(out["result"]["parts_applied"]), 1)

    def test_part_ids_are_capped_at_thirty(self):
        r = client.post(
            "/api/simulate",
            json={"bike_preset": "gsxr1000_k5", "part_ids": list(range(1, 32))},
        )
        self.assertEqual(r.status_code, 422)

    def test_traction_pct_is_a_true_percentage(self):
        for path, body, key in (
            ("/api/simulate", {"bike_preset": "gsxr1000_k5"}, None),
        ):
            ts = client.post(path, json=body).json()["timeseries"]["traction_pct"]
            self.assertTrue(ts)
            self.assertLessEqual(max(ts), 100.0)
            self.assertGreaterEqual(min(ts), 0.0)
            # the launch is traction-limited: the series actually reaches ~100
            self.assertGreater(max(ts), 20.0)
        cmp_ = client.post(
            "/api/simulate/compare",
            json={"a_bike_preset": "gsxr1000_k5", "b_bike_preset": "hayabusa_gen1"},
        ).json()
        for side in ("a", "b"):
            tr = cmp_[side]["timeseries"]["traction_pct"]
            self.assertLessEqual(max(tr), 100.0)


# --------------------------------------------------------------------------
# deprecation cleanup (lifespan + model_config)
# --------------------------------------------------------------------------


class TestLifespanMigration(unittest.TestCase):
    def test_no_legacy_startup_handlers_and_hooks_still_run(self):
        self.assertEqual(api.app.router.on_startup, [])
        ran = []
        orig = api._ensure_account_schema

        async def spy():
            ran.append("schema")
            await orig()

        api._ensure_account_schema = spy
        try:
            with TestClient(api.app) as c:
                self.assertEqual(c.get("/api/health").status_code, 200)
        finally:
            api._ensure_account_schema = orig
        self.assertEqual(ran, ["schema"])

    def test_request_models_use_model_config(self):
        for model in (api.SimulateRequest, api.BikeSuggestionRequest):
            self.assertFalse(hasattr(model, "Config"), model)
            self.assertIn("json_schema_extra", model.model_config)


if __name__ == "__main__":
    unittest.main()
