"""
API port regressions (Nov 2026): PR #127's API contract on top of PR #126.

The two pull requests changed ``motoquant/api.py`` independently. These tests
pin the places where the two meet, so neither side's behaviour can be lost
without a failure:

* #127's conditions / environment echo / part_ids contract runs on #126's
  engine selection (``engine_select``) and rollout-timed splits;
* #127's stock-baseline cache keys on the engine #126 selects;
* #127's lifespan startup still runs #126's physics-engine probe;
* #126's daily chat cap and #127's classic-mode chat fuse both apply;
* the web client's 404 recovery (``Venue N not found`` / ``Tire N not found``)
  works on the job routes it actually calls;
* the CLI rejects a ``--distance`` inside #126's 1 ft rollout the way #127
  rejects a non-positive one.

Every test drives the production path (HTTP through ``TestClient``, or the CLI
entry point) on a COPY of the catalog and fails if the ported change is
reverted.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import types
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
    _TMP_DIR = tempfile.mkdtemp(prefix="mq_api_port_")
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
    if hasattr(api, "_db_facade"):
        api._db_facade = None


def _reset_limits():
    from motoquant import ratelimit

    ratelimit.reset()


def _wait_job(job_id, timeout_s=300.0):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        j = client.get(f"/api/jobs/{job_id}").json()
        if j["status"] in ("done", "error", "cancelled"):
            return j
        time.sleep(0.05)
    raise AssertionError("job timeout")


def _bike_id(search):
    rows = client.get("/api/bikes", params={"search": search, "limit": 5}).json()
    assert rows["bikes"], search
    return rows["bikes"][0]["id"]


ENV_KEYS = {
    "name",
    "is_default",
    "source",
    "altitude_m",
    "ambient_temp_c",
    "track_temp_c",
    "humidity_pct",
    "pressure_hpa",
    "headwind_kmh",
    "track_surface",
}


# ── the environment block: exact shape on every route ───────────────────────


class TestEnvironmentBlockShape(unittest.TestCase):
    """The site words every result's conditions from this block
    (web/components/ConditionsLine.js); its key set is the contract."""

    def setUp(self):
        _reset_limits()

    def _env(self, path, body):
        r = client.post(path, json=body)
        self.assertEqual(r.status_code, 200, r.text[:300])
        return r.json()["environment"]

    def test_block_has_exactly_the_documented_keys_on_every_sync_sim_route(self):
        k5 = {"bike_preset": "gsxr1000_k5"}
        for path, body in (
            ("/api/simulate/quick", k5),
            ("/api/simulate", k5),
            ("/api/simulate/top-speed", {**k5, "max_time_s": 20}),
            ("/api/simulate/distance", {**k5, "distance_m": 200.0}),
            (
                "/api/simulate/compare",
                {"a_bike_preset": "gsxr1000_k5", "b_bike_preset": "yzfr1_4c8"},
            ),
        ):
            env = self._env(path, body)
            self.assertEqual(set(env), ENV_KEYS, path)
            self.assertEqual(env["source"], "default", path)
            self.assertIs(env["is_default"], True, path)
            self.assertEqual(env["name"], api.DEFAULT_CONDITIONS_NAME, path)

    def test_numbers_are_read_off_the_config_that_ran(self):
        env = self._env(
            "/api/simulate/quick",
            {
                "bike_preset": "gsxr1000_k5",
                "altitude_m": 1500.0,
                "ambient_temp_c": 31.0,
                "track_temp_c": 44.0,
                "humidity_pct": 65.0,
                "pressure_hpa": 950.0,
                "headwind_kmh": -12.0,
            },
        )
        self.assertEqual(env["source"], "manual")
        self.assertIs(env["is_default"], False)
        self.assertEqual(env["name"], api.CUSTOM_CONDITIONS_NAME)
        self.assertEqual(env["altitude_m"], 1500.0)
        self.assertEqual(env["ambient_temp_c"], 31.0)
        self.assertEqual(env["track_temp_c"], 44.0)
        self.assertEqual(env["humidity_pct"], 65.0)
        self.assertEqual(env["pressure_hpa"], 950.0)
        self.assertEqual(env["headwind_kmh"], -12.0)  # negative = tailwind
        self.assertEqual(env["track_surface"], "asphalt")

    def test_venue_wins_the_name_and_explicit_values_still_override(self):
        venue = client.get("/api/venues").json()["venues"][0]
        env = self._env(
            "/api/simulate/quick",
            {"bike_preset": "gsxr1000_k5", "venue_id": venue["id"]},
        )
        self.assertEqual(env["source"], "venue")
        self.assertEqual(env["name"], venue["name"])
        self.assertEqual(env["altitude_m"], float(venue["altitude_m"]))
        self.assertEqual(env["track_surface"], venue["track_surface"])
        over = self._env(
            "/api/simulate/quick",
            {
                "bike_preset": "gsxr1000_k5",
                "venue_id": venue["id"],
                "altitude_m": 2222.0,
            },
        )
        self.assertEqual(over["source"], "venue")
        self.assertEqual(over["altitude_m"], 2222.0)

    def test_a_resolved_place_simulates_the_altitude_it_was_sent_with(self):
        """What the site sends for a place that is not a known venue
        (useSimulatorState.placeFields): name + coordinates + altitude. With
        no weather provider configured the resolver is unavailable; the
        altitude must still be the one simulated and echoed."""
        plain = client.post(
            "/api/simulate/quick", json={"bike_preset": "gsxr1000_k5"}
        ).json()
        r = client.post(
            "/api/simulate/quick",
            json={
                "bike_preset": "gsxr1000_k5",
                "location": "Nowhere-In-The-Catalog Hill Station",
                "lat": 34.15,
                "lon": 77.57,
                "altitude_m": 3500.0,
            },
        )
        self.assertEqual(r.status_code, 200, r.text[:300])
        body = r.json()
        self.assertEqual(body["environment"]["altitude_m"], 3500.0)
        self.assertIs(body["environment"]["is_default"], False)
        self.assertGreater(body["et_quarter_s"], plain["et_quarter_s"])


# ── #127's contract on #126's engine and rollout timing ─────────────────────


class TestContractOnTheNewEngine(unittest.TestCase):
    def setUp(self):
        _reset_limits()

    def test_preset_quick_sim_is_the_pinned_reference(self):
        """Conditions plumbing must not move the pinned K5 (10.0436 s since the
        rollout-timing epoch): no conditions sent means the preset's own."""
        r = client.post("/api/simulate/quick", json={"bike_preset": "gsxr1000_k5"})
        self.assertEqual(r.status_code, 200)
        self.assertAlmostEqual(r.json()["et_quarter_s"], 10.0436, places=4)

    def test_health_still_reports_the_engine(self):
        info = client.get("/api/health").json()
        self.assertIn(info["engine"]["engine"], ("python", "native"))

    def test_distance_keeps_the_rollout_floor_and_gains_the_echo(self):
        body = {"bike_preset": "gsxr1000_k5", "distance_m": api.ROLLOUT_M}
        self.assertEqual(
            client.post("/api/simulate/distance", json=body).status_code, 422
        )
        r = client.post(
            "/api/simulate/distance",
            json={"bike_preset": "gsxr1000_k5", "distance_m": 100.0},
        )
        self.assertEqual(r.status_code, 200, r.text[:300])
        out = r.json()
        self.assertEqual(set(out["environment"]), ENV_KEYS)
        self.assertEqual(out["parts_skipped"], [])
        # timed from the start beam (SimResult.split_at), as every other split
        from motoquant import engine_select

        cfg = api._build_config(None, "gsxr1000_k5", 0.0, 0.0, 75.0, None, None, None)
        sim = engine_select.make_engine(cfg).run_distance(100.0, max_time=120.0)
        hit = sim.split_at(100.0)
        self.assertEqual(out["time_s"], round(float(hit[0]), 3))
        # ...which is NOT the raw sample time from rest
        self.assertLess(out["time_s"], float(sim.t[-1]))

    def test_full_sim_with_parts_agrees_with_quick_on_the_selected_engine(self):
        bike = _bike_id("hayabusa")
        ids = client.get(
            "/api/parts", params={"bike_id": bike, "fields": "id", "limit": 5000}
        ).json()["part_ids"]
        self.assertTrue(ids)
        body = {"bike_id": bike, "part_ids": ids[:3]}
        quick = client.post("/api/simulate/quick", json=body).json()
        full = client.post("/api/simulate", json=body).json()
        self.assertEqual(full["et_quarter_s"], quick["et_quarter_s"])
        self.assertEqual(
            [p["id"] for p in full["parts_applied"]],
            [p["id"] for p in quick["parts_applied"]],
        )
        self.assertEqual(full["parts_skipped"], quick["parts_skipped"])
        self.assertEqual(full["splits"]["1320ft_s"], full["et_quarter_s"])

    def test_topspeed_series_never_exceeds_the_cap(self):
        """The decimated series reserves a slot for the peak-speed sample;
        without that a run whose peak is off the even grid returned 2,001
        points for a 2,000-point cap (catalog Hayabusa, default run)."""
        r = client.post(
            "/api/simulate/top-speed",
            json={"bike_id": _bike_id("hayabusa"), "include_timeseries": True},
        )
        self.assertEqual(r.status_code, 200, r.text[:300])
        out = r.json()
        ts = out["timeseries"]
        self.assertLessEqual(len(ts["t"]), api.TOPSPEED_MAX_SERIES_POINTS)
        self.assertGreater(len(ts["t"]), api.TOPSPEED_MAX_SERIES_POINTS // 2)
        # the peak is still in the series
        self.assertAlmostEqual(
            max(ts["v_kmh"]), out["terminal_velocity_kmh"], delta=1.0
        )


class TestStockCacheKeysOnTheEngine(unittest.TestCase):
    """A cached stock baseline may only be compared with a run from the same
    integrator: ``MOTOQUANT_ENGINE`` is read per call."""

    def test_engine_tag_is_part_of_the_key_and_follows_the_selector(self):
        from motoquant import engine_select

        req = api.QuickSimRequest(bike_preset="gsxr1000_k5")
        orig = engine_select.native_active
        try:
            engine_select.native_active = lambda: False
            self.assertEqual(api._engine_tag(), "python")
            key_python = api._stock_key(req)
            engine_select.native_active = lambda: True
            self.assertEqual(api._engine_tag(), "native")
            key_native = api._stock_key(req)

            def boom():
                raise RuntimeError("MOTOQUANT_ENGINE=native but the core is missing")

            engine_select.native_active = boom
            self.assertEqual(api._engine_tag(), "unavailable")
        finally:
            engine_select.native_active = orig
        self.assertNotEqual(key_python, key_native)
        self.assertIn("python", key_python)
        self.assertIn("native", key_native)

    def test_a_baseline_cached_for_one_engine_is_not_served_to_the_other(self):
        from motoquant import engine_select

        req = api.QuickSimRequest(bike_preset="gsxr1000_k5")
        orig = engine_select.native_active
        api._stock_cache.clear()
        try:
            engine_select.native_active = lambda: False
            api._stock_cache_put(api._stock_key(req), 12.3456)
            self.assertEqual(api._stock_cache_get(api._stock_key(req)), 12.3456)
            engine_select.native_active = lambda: True
            self.assertIsNone(api._stock_cache_get(api._stock_key(req)))
        finally:
            engine_select.native_active = orig
            api._stock_cache.clear()


# ── the web client's 404 recovery on the routes it calls ────────────────────


class TestSharedLinkRecovery(unittest.TestCase):
    """web/components/sim/useSimulatorState.js (withRefRecovery) matches
    ``^(Venue|Tire) (\\d+) not found`` on a 404 and retries without that id.
    The full sim, top speed and compare run through /api/jobs/*, so the 404
    has to arrive when the job is POSTed, not as a failed job on first poll."""

    RX = re.compile(r"^(Venue|Tire) (\d+) not found")

    def setUp(self):
        _reset_limits()

    def _assert_ref_404(self, path, body, kind, ident):
        r = client.post(path, json=body)
        self.assertEqual(r.status_code, 404, f"{path}: {r.status_code} {r.text[:200]}")
        m = self.RX.match(r.json()["detail"])
        self.assertIsNotNone(m, r.text)
        self.assertEqual((m.group(1), int(m.group(2))), (kind, ident))

    def test_every_sim_entry_point_names_the_missing_reference(self):
        k5 = {"bike_preset": "gsxr1000_k5"}
        for path in (
            "/api/simulate/quick",
            "/api/simulate",
            "/api/jobs/simulate",
            "/api/simulate/top-speed",
            "/api/jobs/topspeed",
        ):
            self._assert_ref_404(path, {**k5, "venue_id": 987654}, "Venue", 987654)
            self._assert_ref_404(path, {**k5, "rear_tire_id": 987653}, "Tire", 987653)
            self._assert_ref_404(path, {**k5, "front_tire_id": 987652}, "Tire", 987652)
        cmp_body = {"a_bike_preset": "gsxr1000_k5", "b_bike_preset": "yzfr1_4c8"}
        for path in ("/api/simulate/compare", "/api/jobs/compare"):
            self._assert_ref_404(
                path, {**cmp_body, "venue_id": 987654}, "Venue", 987654
            )
            self._assert_ref_404(
                path, {**cmp_body, "b_rear_tire_id": 987651}, "Tire", 987651
            )

    def test_tool_jobs_reject_unknown_references_at_post_time(self):
        for path in ("/api/jobs/optimize", "/api/jobs/autotune", "/api/jobs/outlaw"):
            _reset_limits()
            r = client.post(
                path, json={"bike_preset": "gsxr1000_k5", "venue_id": 987654}
            )
            self.assertEqual(r.status_code, 404, f"{path}: {r.text[:200]}")
            self.assertIn("Venue 987654 not found", r.json()["detail"])
            r = client.post(path, json={"bike_id": 987654})
            self.assertEqual(r.status_code, 404, f"{path}: {r.text[:200]}")
            r = client.post(path, json={"bike_preset": "no_such_preset"})
            self.assertEqual(r.status_code, 404, f"{path}: {r.text[:200]}")

    def test_a_valid_job_still_starts_and_finishes(self):
        r = client.post(
            "/api/jobs/simulate", json={"bike_preset": "gsxr1000_k5", "altitude_m": 0}
        )
        self.assertEqual(r.status_code, 202, r.text[:200])
        j = _wait_job(r.json()["job_id"])
        self.assertEqual(j["status"], "done", j.get("error"))
        self.assertEqual(j["result"]["environment"]["source"], "manual")
        self.assertEqual(set(j["result"]["environment"]), ENV_KEYS)


# ── both chat fuses apply (#126 daily cap + #127 classic-mode bucket) ───────


class TestChatFusesCoexist(unittest.TestCase):
    def setUp(self):
        _reset_limits()
        self._prior_limit = api.CHAT_DAILY_LIMIT
        stub = types.SimpleNamespace(is_configured=False, provider="stub")
        api.app.dependency_overrides[api.get_llm_client] = lambda: stub

    def tearDown(self):
        api.CHAT_DAILY_LIMIT = self._prior_limit
        api.app.dependency_overrides.pop(api.get_llm_client, None)
        _reset_limits()

    def _chat(self, path="/api/chat", mode=None):
        body = {"query": "how fast is a K5"}
        if mode:
            body["mode"] = mode
            body["run_summary"] = False
        return client.post(path, json=body)

    def test_classic_mode_trips_its_own_bucket_on_both_routes(self):
        codes = [self._chat(mode="classic").status_code for _ in range(4)]
        self.assertNotIn(429, codes, codes)
        r = self._chat(mode="classic")
        self.assertEqual(r.status_code, 429)
        self.assertIn("chat_classic", r.json()["detail"]["message"])
        r = self._chat(path="/api/jobs/chat", mode="classic")
        self.assertEqual(r.status_code, 429)
        self.assertIn("chat_classic", r.json()["detail"]["message"])
        # agent mode is not subject to the classic bucket
        self.assertEqual(self._chat().status_code, 200)

    def test_daily_cap_still_trips_first_when_it_is_lower(self):
        api.CHAT_DAILY_LIMIT = 2
        self.assertEqual(self._chat().status_code, 200)
        self.assertEqual(self._chat(mode="classic").status_code, 200)
        r = self._chat(mode="classic")
        self.assertEqual(r.status_code, 429)
        self.assertIn("chat_day", r.json()["detail"]["message"])

    def test_the_agent_is_handed_a_gate_on_the_callers_optimize_bucket(self):
        """Each heavy agent tool spends one hit of the caller's per-IP
        ``optimize`` bucket, the one the direct optimizer routes use."""
        from motoquant import ratelimit
        from motoquant.llm import agent as agent_mod

        seen = {}
        result = types.SimpleNamespace(
            raw_query="q",
            blocks=[],
            tool_trace=[],
            sims_run=0,
            reply="ok",
            error=None,
            error_detail=None,
            last_block=lambda _t: None,
        )

        def fake_agent(query, db, **kwargs):
            seen.update(kwargs)
            return result

        orig = agent_mod.run_agent_chat
        try:
            agent_mod.run_agent_chat = fake_agent
            self.assertEqual(self._chat().status_code, 200)
        finally:
            agent_mod.run_agent_chat = orig
        gate = seen["heavy_gate"]
        self.assertTrue(callable(gate))
        self.assertEqual([gate() for _ in range(7)], [True] * 6 + [False])
        self.assertTrue(
            any(k.startswith("optimize:") for k in ratelimit._WINDOWS),
            list(ratelimit._WINDOWS),
        )
        # ...and the direct route now refuses the same client
        r = client.post("/api/optimize/build", json={"bike_preset": "nope"})
        self.assertEqual(r.status_code, 429)


# ── fitment: a part that does not fit the bike is never applied ─────────────


def _misfit_part(bike_id):
    """(compatible_ids, id of a catalog part that does NOT fit ``bike_id`` and
    would change the result if it were applied)."""
    fits = set(
        client.get(
            "/api/parts", params={"bike_id": bike_id, "fields": "id", "limit": 5000}
        ).json()["part_ids"]
    )
    for part in client.get("/api/parts", params={"limit": 5000}).json()["parts"]:
        if part["id"] in fits or part["category_name"] != "exhaust":
            continue
        deltas = part.get("param_deltas") or {}
        if isinstance(deltas, dict) and deltas.get("engine.peak_power_hp"):
            return fits, part["id"]
    raise AssertionError("no incompatible power-adding exhaust in the catalog")


class TestPartsThatDoNotFitAreNotApplied(unittest.TestCase):
    """``GET /api/parts?bike_id=N`` and the sim routes share one compatibility
    engine. Before this, ``part_ids`` from a hand-written request were applied
    whatever the bike (a Hayabusa-only exhaust on the K5) with
    ``parts_skipped: []``."""

    BIKE = 1  # GSX-R 1000 K5/K6 catalog row (also the gsxr1000_k5 preset's row)

    @classmethod
    def setUpClass(cls):
        _reset_limits()
        cls.fits, cls.misfit = _misfit_part(cls.BIKE)
        cls.good = next(iter(sorted(cls.fits)))

    def setUp(self):
        _reset_limits()

    def _assert_skipped(self, block, where):
        self.assertEqual(block["parts_skipped"], [self.misfit], where)
        self.assertEqual(len(block["parts_skipped_detail"]), 1, where)
        why = block["parts_skipped_detail"][0]
        self.assertEqual(why["id"], self.misfit, where)
        self.assertEqual(why["reason"], api.SKIP_DOES_NOT_FIT, where)
        self.assertIn("does not fit this bike", why["detail"], where)
        if "parts_applied" in block:
            self.assertNotIn(
                self.misfit, [p["id"] for p in block["parts_applied"]], where
            )

    def test_quick_sim_skips_reports_and_matches_the_stock_run(self):
        plain = client.post("/api/simulate/quick", json={"bike_id": self.BIKE}).json()
        r = client.post(
            "/api/simulate/quick",
            json={"bike_id": self.BIKE, "part_ids": [self.misfit]},
        )
        self.assertEqual(r.status_code, 200, r.text[:300])
        out = r.json()
        self._assert_skipped(out, "quick")
        self.assertEqual(out["parts_applied"], [])
        self.assertEqual(out["et_quarter_s"], plain["et_quarter_s"])
        self.assertEqual(out["peak_power_hp"], plain["peak_power_hp"])
        self.assertEqual(out["build_cost_inr"], 0)
        self.assertEqual(plain["parts_skipped_detail"], [])

    def test_the_same_part_is_applied_to_a_bike_it_fits(self):
        """The check is per bike, not a blanket refusal."""
        rows = client.get(
            "/api/parts", params={"limit": 5000, "include_rules": "true"}
        ).json()["parts"]
        row = next(p for p in rows if p["id"] == self.misfit)
        for bike in client.get("/api/bikes", params={"limit": 5000}).json()["bikes"]:
            ids = client.get(
                "/api/parts", params={"bike_id": bike["id"], "fields": "id"}
            ).json()["part_ids"]
            if self.misfit in ids:
                out = client.post(
                    "/api/simulate/quick",
                    json={"bike_id": bike["id"], "part_ids": [self.misfit]},
                ).json()
                self.assertEqual(
                    [p["id"] for p in out["parts_applied"]], [self.misfit], row
                )
                self.assertEqual(out["parts_skipped"], [])
                return
            _reset_limits()
        self.fail(f"part {self.misfit} fits no catalog bike: {row['model_name']}")

    def test_mixed_request_applies_what_fits_and_names_each_skip(self):
        r = client.post(
            "/api/simulate/quick",
            json={
                "bike_id": self.BIKE,
                "part_ids": [self.good, self.misfit, 987654, self.misfit],
            },
        )
        out = r.json()
        self.assertEqual([p["id"] for p in out["parts_applied"]], [self.good])
        self.assertEqual(out["parts_skipped"], [self.misfit, 987654])
        self.assertEqual(
            [(d["id"], d["reason"]) for d in out["parts_skipped_detail"]],
            [(self.misfit, api.SKIP_DOES_NOT_FIT), (987654, api.SKIP_UNKNOWN)],
        )
        # the baseline is the bike without parts, so the delta is the fitted
        # part's alone
        only_good = client.post(
            "/api/simulate/quick",
            json={"bike_id": self.BIKE, "part_ids": [self.good]},
        ).json()
        self.assertEqual(out["et_quarter_s"], only_good["et_quarter_s"])
        self.assertEqual(out["et_delta_s"], only_good["et_delta_s"])

    def test_every_sync_sim_route(self):
        body = {"bike_id": self.BIKE, "part_ids": [self.misfit]}
        for path, extra in (
            ("/api/simulate", {}),
            ("/api/simulate/top-speed", {"max_time_s": 20}),
            ("/api/simulate/distance", {"distance_m": 200.0}),
        ):
            r = client.post(path, json={**body, **extra})
            self.assertEqual(r.status_code, 200, f"{path}: {r.text[:200]}")
            self._assert_skipped(r.json(), path)
            plain = client.post(path, json={"bike_id": self.BIKE, **extra}).json()
            for key in ("et_quarter_s", "terminal_velocity_kmh", "time_s"):
                if key in plain:
                    self.assertEqual(r.json()[key], plain[key], (path, key))

    def test_preset_requests_are_checked_against_the_presets_catalog_row(self):
        r = client.post(
            "/api/simulate/quick",
            json={"bike_preset": "gsxr1000_k5", "part_ids": [self.misfit]},
        )
        self.assertEqual(r.status_code, 200, r.text[:300])
        self._assert_skipped(r.json(), "preset")
        self.assertAlmostEqual(r.json()["et_quarter_s"], 10.0436, places=4)

    def test_parts_list_accepts_a_preset_and_agrees_with_the_sim_routes(self):
        """A preset stands for its catalog row on both sides: the parts list
        (``?bike_preset=``) and the fitment check of a preset sim request. A
        gearing what-if on a preset therefore has fitting sprockets to use."""
        by_preset = client.get(
            "/api/parts",
            params={"bike_preset": "gsxr1000_k5", "fields": "id", "limit": 5000},
        )
        self.assertEqual(by_preset.status_code, 200, by_preset.text[:200])
        self.assertEqual(sorted(by_preset.json()["part_ids"]), sorted(self.fits))
        self.assertEqual(by_preset.json()["bike_id"], self.BIKE)
        self.assertIs(by_preset.json()["compatible_only"], True)
        self.assertEqual(
            client.get("/api/parts", params={"bike_preset": "nope"}).status_code, 404
        )

        front, rear = {}, {}
        rows = client.get(
            "/api/parts",
            params={"bike_preset": "gsxr1000_k5", "category": "sprocket", "limit": 500},
        ).json()["parts"]
        for part in rows:
            over = part.get("param_overrides") or {}
            if "drivetrain.front_sprocket" in over:
                front.setdefault(int(over["drivetrain.front_sprocket"]), part["id"])
            if "drivetrain.rear_sprocket" in over:
                rear.setdefault(int(over["drivetrain.rear_sprocket"]), part["id"])
        self.assertTrue({16, 17} <= set(front) and {42, 45} <= set(rear), (front, rear))
        r = client.post(
            "/api/simulate/compare",
            json={
                "a_bike_preset": "gsxr1000_k5",
                "b_bike_preset": "gsxr1000_k5",
                "a_part_ids": [front[17], rear[42]],
                "b_part_ids": [front[16], rear[45]],
            },
        )
        self.assertEqual(r.status_code, 200, r.text[:300])
        out = r.json()
        self.assertEqual(out["a"]["parts_skipped"], [])
        self.assertEqual(out["b"]["parts_skipped"], [])
        self.assertNotEqual(out["a"]["et_quarter_s"], out["b"]["et_quarter_s"])
        # 17/42 is the K5's stock gearing: fitting it changes nothing
        self.assertAlmostEqual(out["a"]["et_quarter_s"], 10.0436, places=4)

    def test_compare_checks_each_build_against_its_own_bike(self):
        r = client.post(
            "/api/simulate/compare",
            json={
                "a_bike_id": self.BIKE,
                "a_part_ids": [self.misfit],
                "b_bike_id": self.BIKE,
                "b_part_ids": [],
            },
        )
        self.assertEqual(r.status_code, 200, r.text[:300])
        out = r.json()
        self._assert_skipped(out["a"], "compare a")
        self.assertEqual(out["b"]["parts_skipped"], [])
        self.assertEqual(out["b"]["parts_skipped_detail"], [])
        self.assertEqual(out["delta"]["et_s"], 0.0)

    def test_job_variants(self):
        for kind, body, pick in (
            ("simulate", {"bike_id": self.BIKE, "part_ids": [self.misfit]}, None),
            (
                "topspeed",
                {"bike_id": self.BIKE, "part_ids": [self.misfit], "max_time_s": 20},
                None,
            ),
            (
                "compare",
                {
                    "a_bike_id": self.BIKE,
                    "a_part_ids": [self.misfit],
                    "b_bike_id": self.BIKE,
                },
                "a",
            ),
        ):
            _reset_limits()
            r = client.post(f"/api/jobs/{kind}", json=body)
            self.assertEqual(r.status_code, 202, f"{kind}: {r.text[:200]}")
            j = _wait_job(r.json()["job_id"])
            self.assertEqual(j["status"], "done", j.get("error"))
            block = j["result"][pick] if pick else j["result"]
            self._assert_skipped(block, f"job {kind}")

    def test_optimizer_and_outlaw_only_pick_parts_that_fit(self):
        bike = _bike_id("hayabusa")
        fits = set(
            client.get(
                "/api/parts", params={"bike_id": bike, "fields": "id", "limit": 5000}
            ).json()["part_ids"]
        )
        r = client.post(
            "/api/optimize/build",
            json={"bike_id": bike, "budget_inr": 150000, "max_candidates": 12},
        )
        self.assertEqual(r.status_code, 200, r.text[:300])
        picked = [p["part_id"] for p in r.json()["parts"]]
        self.assertTrue(picked)
        self.assertEqual([p for p in picked if p not in fits], [])

        _reset_limits()
        r = client.post("/api/jobs/outlaw", json={"bike_id": bike, "max_candidates": 6})
        self.assertEqual(r.status_code, 202, r.text[:300])
        j = _wait_job(r.json()["job_id"], timeout_s=600.0)
        self.assertEqual(j["status"], "done", j.get("error"))
        picked = [p["part_id"] for p in j["result"]["build"]["parts"]]
        self.assertTrue(picked)
        self.assertEqual([p for p in picked if p not in fits], [])


# ── the API reports the package version ─────────────────────────────────────


class TestApiVersionIsThePackageVersion(unittest.TestCase):
    def test_root_and_openapi_carry_dunder_version(self):
        import motoquant

        self.assertEqual(client.get("/").json()["version"], motoquant.__version__)
        spec = client.get("/openapi.json").json()
        self.assertEqual(spec["info"]["version"], motoquant.__version__)
        self.assertEqual(api.app.version, motoquant.__version__)


# ── opening an initialised database writes nothing ──────────────────────────


def _sha(path):
    import hashlib

    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


class TestOpeningAnInitialisedDatabaseWritesNothing(unittest.TestCase):
    """``initialize()`` re-ran ``INSERT OR IGNORE`` into AUTOINCREMENT tables
    on every open; SQLite advances ``sqlite_sequence`` even for an ignored
    row, so any read-only CLI command against the tracked motoquant.db left
    it modified in git."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="mq_db_open_")
        self.db = os.path.join(self.dir, "motoquant.db")
        shutil.copyfile(_REPO_DB, self.db)
        self.before = _sha(self.db)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "motoquant.run", "--db", self.db, *args],
            capture_output=True,
            text=True,
            cwd=_REPO,
            timeout=300,
        )

    def test_initialize_is_byte_for_byte_a_no_op(self):
        from motoquant.database.connection import MotoQuantDB

        for _ in range(3):
            db = MotoQuantDB(self.db)
            db.initialize()
            db.close()
        self.assertEqual(_sha(self.db), self.before)
        self.assertEqual(sorted(os.listdir(self.dir)), ["motoquant.db"])

    def test_read_only_cli_commands_leave_the_file_untouched(self):
        for args in (
            ("venues",),
            ("bikes", "--fitments", "3"),
            ("parts", "--bike-id", "1"),
            ("sim", "--bike-id", "1", "-q"),
            ("leaderboard",),
        ):
            r = self._cli(*args)
            self.assertEqual(r.returncode, 0, (args, r.stderr[-300:]))
            self.assertEqual(_sha(self.db), self.before, args)

    def test_a_new_database_is_still_seeded_once(self):
        from motoquant.database.connection import MotoQuantDB
        from motoquant.database.schema import (
            SEED_PARTS_CATEGORIES,
            SEED_SEASONAL_DATA,
            SEED_VENUES,
        )

        fresh = os.path.join(self.dir, "fresh.db")
        db = MotoQuantDB(fresh)
        db.initialize()
        counts = {
            t: db.conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            for t in ("parts_categories", "venues", "venue_seasonal")
        }
        db.close()
        self.assertEqual(counts["parts_categories"], len(SEED_PARTS_CATEGORIES))
        self.assertEqual(counts["venues"], len(SEED_VENUES))
        self.assertEqual(
            counts["venue_seasonal"], sum(len(m) for m in SEED_SEASONAL_DATA.values())
        )
        seeded = _sha(fresh)
        db = MotoQuantDB(fresh)
        db.initialize()
        db.close()
        self.assertEqual(_sha(fresh), seeded)

    def test_a_missing_seed_row_is_still_restored(self):
        """The guard skips rows that exist; it must not stop seeding ones
        that do not."""
        import sqlite3

        from motoquant.database.connection import MotoQuantDB
        from motoquant.database.schema import SEED_PARTS_CATEGORIES

        name = SEED_PARTS_CATEGORIES[-1][0]
        fresh = os.path.join(self.dir, "fresh2.db")
        db = MotoQuantDB(fresh)
        db.initialize()
        db.close()
        raw = sqlite3.connect(fresh)
        raw.execute("DELETE FROM parts_categories WHERE name = ?", (name,))
        raw.execute("DELETE FROM venue_seasonal WHERE month = 6")
        raw.commit()
        raw.close()
        db = MotoQuantDB(fresh)
        db.initialize()
        n_cat = db.conn.execute(
            "SELECT COUNT(*) FROM parts_categories WHERE name = ?", (name,)
        ).fetchone()[0]
        n_june = db.conn.execute(
            "SELECT COUNT(*) FROM venue_seasonal WHERE month = 6"
        ).fetchone()[0]
        db.close()
        self.assertEqual(n_cat, 1)
        self.assertGreater(n_june, 0)


# ── CLI: --distance and #126's rollout ──────────────────────────────────────


def _cli(*args, timeout=300):
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "motoquant.run",
            "--db",
            os.environ["MOTOQUANT_DB"],
            *args,
        ],
        capture_output=True,
        text=True,
        cwd=_REPO,
        timeout=timeout,
    )


class TestCliDistanceInsideTheRollout(unittest.TestCase):
    def test_a_target_at_or_inside_the_rollout_is_a_usage_error(self):
        for bad in ("0.1", "0.3048"):
            r = _cli("sim", "--bike-id", "1", "--distance", bad, "-q")
            self.assertEqual(r.returncode, 2, (bad, r.stderr[-300:]))
            self.assertNotIn("Traceback", r.stderr, bad)
            self.assertIn("--distance", r.stderr)
            self.assertIn("rollout", r.stderr)

    def test_a_short_but_valid_distance_runs(self):
        r = _cli("sim", "--bike-id", "1", "--distance", "50", "-q")
        self.assertEqual(r.returncode, 0, r.stderr[-300:])

    def test_sobol_help_lists_exactly_the_parameters_that_exist(self):
        """``--params`` help once advertised ``reaction_time``, which the
        analysis removed (it has no effect on ET) and now rejects."""
        from motoquant.analysis.sobol import DEFAULT_PARAM_BOUNDS

        r = _cli("analysis", "sobol", "--help")
        self.assertEqual(r.returncode, 0, r.stderr[-300:])
        text = " ".join(r.stdout.split())
        listed = text.split("Valid keys:", 1)[1].split("--json", 1)[0]
        keys = [k.strip(" ,.") for k in listed.split(",")]
        keys = [k.split()[0] for k in keys if k]
        self.assertEqual(sorted(keys), sorted(DEFAULT_PARAM_BOUNDS))
        self.assertNotIn("reaction_time", text)

    def test_roi_json_signs_and_fields(self):
        """delta_et_s is after minus before (negative = quicker) with the
        positive et_gain_s beside it, as on the API."""
        import json

        r = _cli("analysis", "roi", "--bike-id", "3", "--category", "exhaust", "--json")
        self.assertEqual(r.returncode, 0, r.stderr[-400:])
        d = json.loads(r.stdout)
        self.assertIs(d["compatible_only"], True)
        self.assertTrue(d["parts"])
        for p in d["parts"]:
            self.assertEqual(p["delta_et_s"], -p["et_gain_s"] + 0.0)
            self.assertEqual(p["delta_trap_mps"], p["delta_trap_ms"])
            self.assertIs(p["compatible"], True)
        self.assertTrue(any(p["delta_et_s"] < 0 for p in d["parts"]))


if __name__ == "__main__":
    unittest.main()
