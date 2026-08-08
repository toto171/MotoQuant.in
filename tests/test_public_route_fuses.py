"""
Pre-revenue gaps on the unauthenticated public routes (2026-07-25 audit §3.4).

Four routes that anyone on the internet can drive, each of which spent
something real without a ceiling:

1. ``/api/simulate/compare`` runs TWO full RK4 passes and metered nothing, so
   it was the cheapest way to bypass the free-tier sim quota entirely. Now
   charged 2 units. ``/api/simulate/quick`` stays unmetered *by design* — the
   slider UI auto-runs it on every drag — and the last test in that class pins
   that exclusion so a future "meter everything" pass cannot break the UX.
2. ``/api/telemetry/event`` writes the funnel numbers the roadmap reads
   (``signup_completed``, ``sim_run_success``) with no auth, no rate limit and
   no body cap; once ``POSTHOG_API_KEY`` is set each beacon also spawned an
   UNBOUNDED thread.
3. ``/api/simulate/save`` is effectively anonymous during the beta, trusts the
   client-supplied ET, and took an unbounded ``notes`` string — twenty calls
   own the public leaderboard.
4. ``/api/pricing/refresh/{id}?force=true`` bypassed the freshness cache, so a
   repeat loop aimed the 44 s worst-case outbound fetch at one retailer URL
   forever.

Everything is driven through the real routes (docs/INVARIANTS.md I8) and each
test fails if its fix is reverted. MOTOQUANT_DB is redirected at import and
re-asserted at run time because the metered routes write ``sim_usage`` rows —
see the comment in tests/test_jobs_api.py for why that matters.
"""

from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

_tmp_db_file = tempfile.NamedTemporaryFile(
    prefix="motoquant_route_fuses_", suffix=".db", delete=False
)
_tmp_db_file.close()
_TMP_DB_PATH = _tmp_db_file.name
_IMPORT_PRIOR_MOTOQUANT_DB = os.environ.get("MOTOQUANT_DB")
_PRIOR_MOTOQUANT_DB = _IMPORT_PRIOR_MOTOQUANT_DB
os.environ["MOTOQUANT_DB"] = _TMP_DB_PATH


def setUpModule():
    global _PRIOR_MOTOQUANT_DB
    current = os.environ.get("MOTOQUANT_DB")
    if current != _TMP_DB_PATH:
        _PRIOR_MOTOQUANT_DB = current
    os.environ["MOTOQUANT_DB"] = _TMP_DB_PATH
    _api_mod = sys.modules.get("motoquant.api")
    if _api_mod is not None:
        _api_mod._db_conn = None
        _api_mod._db_facade = None
    _init_schema()


def tearDownModule():
    _api_mod = sys.modules.get("motoquant.api")
    if _api_mod is not None and getattr(_api_mod, "_db_conn", None) is not None:
        try:
            _api_mod._db_conn.close()
        except Exception:  # noqa: BLE001
            pass
        _api_mod._db_conn = None
        _api_mod._db_facade = None
    try:
        os.unlink(_TMP_DB_PATH)
    except OSError:
        pass
    if _PRIOR_MOTOQUANT_DB is None:
        os.environ.pop("MOTOQUANT_DB", None)
    else:
        os.environ["MOTOQUANT_DB"] = _PRIOR_MOTOQUANT_DB


def _init_schema():
    """Create the catalog schema + one priced part for the pricing tests."""
    from motoquant.database.connection import MotoQuantDB

    db = MotoQuantDB(_TMP_DB_PATH)
    db.initialize()
    conn = db._conn
    conn.execute(
        "INSERT OR IGNORE INTO parts_categories (id, name, display_name) "
        "VALUES (1, 'exhaust', 'Exhaust')"
    )
    conn.execute(
        "INSERT OR REPLACE INTO parts "
        "(id, category_id, brand, model_name, specifications, price_inr, "
        " retailer, retailer_url) "
        "VALUES (?, 1, 'Akrapovic', 'Test Slip-On', '{}', 50000, "
        "'TestRetailer', 'https://example.invalid/part')",
        (_PRICED_PART_ID,),
    )
    conn.commit()
    db.close()


_PRICED_PART_ID = 4242


def _usage_total() -> int:
    """Total metered sim units recorded in the isolated DB."""
    conn = sqlite3.connect(_TMP_DB_PATH)
    try:
        row = conn.execute("SELECT COALESCE(SUM(count), 0) FROM sim_usage").fetchone()
        return int(row[0]) if row else 0
    except sqlite3.OperationalError:  # table not created yet == nothing metered
        return 0
    finally:
        conn.close()


class _RouteTest(unittest.TestCase):
    """Shared TestClient + limiter reset."""

    @classmethod
    def setUpClass(cls):
        try:
            from fastapi.testclient import TestClient

            from motoquant.api import app

            cls.app = app
            cls.client = TestClient(app, raise_server_exceptions=False)
        except Exception:  # noqa: BLE001
            cls.client = None

    def setUp(self):
        if self.client is None:
            self.skipTest("fastapi not installed")
        from motoquant import ratelimit

        ratelimit.reset()


# ───────────────────────────────────────────────────────────────────
# 1. /api/simulate/compare quota bypass
# ───────────────────────────────────────────────────────────────────


class TestCompareIsMetered(_RouteTest):
    _COMPARE_BODY = {
        "a_bike_preset": "gsxr1000_k5",
        "b_bike_preset": "hayabusa_gen1",
    }

    def test_compare_charges_two_sim_units(self):
        """Two RK4 runs must cost two quota units, not zero."""
        before = _usage_total()
        r = self.client.post("/api/simulate/compare", json=self._COMPARE_BODY)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(
            _usage_total() - before,
            2,
            "compare did not charge exactly 2 sim units — the meter "
            "dependency is missing or charging the wrong count",
        )

    def test_compare_exposes_remaining_header(self):
        r = self.client.post("/api/simulate/compare", json=self._COMPARE_BODY)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertIn("X-Sims-Remaining", r.headers)
        self.assertIn("X-Sims-Limit", r.headers)

    def test_job_compare_is_metered_too(self):
        """The job twin must match the sync route (deploy-skew contract)."""
        before = _usage_total()
        r = self.client.post("/api/jobs/compare", json=self._COMPARE_BODY)
        self.assertEqual(r.status_code, 202, r.text)
        self.assertEqual(_usage_total() - before, 2)

    def test_quick_sim_stays_unmetered_by_design(self):
        """Pins the deliberate exclusion: the slider UI auto-runs quick."""
        before = _usage_total()
        r = self.client.post("/api/simulate/quick", json={"bike_preset": "gsxr1000_k5"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(
            _usage_total(),
            before,
            "/api/simulate/quick became metered — it must not be, the web "
            "UI fires it on every slider move",
        )


# ───────────────────────────────────────────────────────────────────
# 2. /api/telemetry/event — forgeable funnel writer
# ───────────────────────────────────────────────────────────────────


class TestTelemetryFuses(_RouteTest):
    def test_event_still_accepted(self):
        r = self.client.post(
            "/api/telemetry/event",
            json={"event": "sim_run_success", "session_id": "abc", "path": "/"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["ok"])

    def test_is_rate_limited(self):
        codes = [
            self.client.post(
                "/api/telemetry/event", json={"event": "signup_completed"}
            ).status_code
            for _ in range(70)
        ]
        self.assertIn(
            429,
            codes,
            "telemetry never rate-limited — anyone can manufacture the "
            f"funnel numbers: {set(codes)}",
        )
        self.assertEqual(codes[-1], 429, "the fuse must bite on later calls")

    def test_oversized_body_is_dropped_not_parsed(self):
        from motoquant.api import TELEMETRY_MAX_BODY_BYTES

        r = self.client.post(
            "/api/telemetry/event",
            json={
                "event": "x",
                "props": {"blob": "A" * (TELEMETRY_MAX_BODY_BYTES + 10)},
            },
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json().get("dropped"), "payload_too_large")

    def test_malformed_body_is_a_200_drop(self):
        r = self.client.post(
            "/api/telemetry/event",
            content=b"{not json",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json().get("dropped"), "malformed")

    def test_props_are_capped(self):
        """Field count is bounded, so a beacon cannot be a log bomb."""
        import motoquant.api as api_mod

        seen = {}

        def _spy(event, session_id, path, props):
            seen["props"] = props
            return "disabled"

        original = api_mod._forward_telemetry_posthog
        api_mod._forward_telemetry_posthog = _spy
        try:
            r = self.client.post(
                "/api/telemetry/event",
                json={
                    "event": "e",
                    "props": {f"k{i}": i for i in range(200)},
                },
            )
        finally:
            api_mod._forward_telemetry_posthog = original
        self.assertEqual(r.status_code, 200)
        self.assertLessEqual(len(seen["props"]), api_mod.TELEMETRY_MAX_PROPS)

    def test_forwarding_concurrency_is_bounded(self):
        """With a key set, beacons past the in-flight ceiling are DROPPED.

        The pre-fix code called threading.Thread(...).start() per beacon with
        no ceiling at all, so this test's exhausted-semaphore state could
        never have produced a drop.
        """
        import motoquant.api as api_mod

        os.environ["POSTHOG_API_KEY"] = "phc_test_key"
        acquired = 0
        try:
            # Exhaust every forwarding slot.
            while api_mod._telemetry_slots.acquire(blocking=False):
                acquired += 1
            self.assertEqual(acquired, api_mod.TELEMETRY_MAX_INFLIGHT)
            verdict = api_mod._forward_telemetry_posthog("e", "s", "/", {})
            self.assertEqual(verdict, "dropped_backpressure")
        finally:
            for _ in range(acquired):
                api_mod._telemetry_slots.release()
            os.environ.pop("POSTHOG_API_KEY", None)

    def test_no_key_means_no_forward(self):
        import motoquant.api as api_mod

        os.environ.pop("POSTHOG_API_KEY", None)
        self.assertEqual(
            api_mod._forward_telemetry_posthog("e", "s", "/", {}), "disabled"
        )


# ───────────────────────────────────────────────────────────────────
# 3. /api/simulate/save — anonymous leaderboard writer
# ───────────────────────────────────────────────────────────────────


class TestSaveRunFuses(_RouteTest):
    _GOOD = {"bike_id": 1, "et_quarter_s": 10.5, "trap_speed_kmh": 220.0}

    def test_unbounded_notes_rejected(self):
        r = self.client.post(
            "/api/simulate/save", json={**self._GOOD, "notes": "x" * 5000}
        )
        self.assertEqual(
            r.status_code, 422, "unbounded notes still accepted on a public writer"
        )

    def test_reasonable_notes_still_accepted(self):
        """The bound must not break the real use case."""
        r = self.client.post(
            "/api/simulate/save",
            json={**self._GOOD, "notes": "K5, 32C, street tyres, 2nd run"},
        )
        # 404 (no bike_config in this bare DB) proves validation passed and
        # the handler ran — the assertion here is "not a 422".
        self.assertNotEqual(r.status_code, 422, r.text)

    def test_is_rate_limited(self):
        codes = [
            self.client.post("/api/simulate/save", json=self._GOOD).status_code
            for _ in range(14)
        ]
        self.assertIn(
            429,
            codes,
            f"save-run never rate-limited — 20 calls own the leaderboard: {set(codes)}",
        )

    def test_field_bounds_from_2026_07_06_survive(self):
        """Guards the older ET/trap bounds against accidental removal."""
        self.assertEqual(
            self.client.post(
                "/api/simulate/save", json={**self._GOOD, "et_quarter_s": -3.0}
            ).status_code,
            422,
        )
        self.assertEqual(
            self.client.post(
                "/api/simulate/save", json={**self._GOOD, "trap_speed_kmh": 1200.0}
            ).status_code,
            422,
        )


# ───────────────────────────────────────────────────────────────────
# 4. /api/pricing/refresh — force=true bypassed the cache
# ───────────────────────────────────────────────────────────────────


class TestPricingForceFloor(_RouteTest):
    def _set_last_fetch(self, when: datetime):
        conn = sqlite3.connect(_TMP_DB_PATH)
        try:
            conn.execute(
                "DELETE FROM part_prices WHERE part_id = ?", (_PRICED_PART_ID,)
            )
            conn.execute(
                "INSERT INTO part_prices "
                "(part_id, retailer, source_url, price_inr, in_stock, fetched_at) "
                "VALUES (?, 'TestRetailer', 'https://example.invalid/part', "
                "49000, 1, ?)",
                (_PRICED_PART_ID, when.isoformat()),
            )
            conn.commit()
        finally:
            conn.close()

    def _refresh(self, force=True):
        return self.client.post(
            f"/api/pricing/refresh/{_PRICED_PART_ID}?force={'true' if force else 'false'}"
        )

    def test_force_within_the_hour_does_not_refetch(self):
        """The whole point: force must not be an unlimited outbound lever."""
        self._set_last_fetch(datetime.now(timezone.utc) - timedelta(minutes=5))

        import motoquant.database.pricing_refresh as pr_mod

        calls = []
        original = pr_mod.fetch_live_price
        pr_mod.fetch_live_price = lambda *a, **k: calls.append(1)
        try:
            r = self._refresh(force=True)
        finally:
            pr_mod.fetch_live_price = original

        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(
            body["status"],
            "floor_cached",
            "force=true re-fetched a price checked 5 minutes ago",
        )
        self.assertEqual(calls, [], "an outbound fetch was made despite the floor")
        # The floor must be documented in the response, not silent.
        self.assertIsNotNone(body.get("note"))
        self.assertIn("minute", body["note"])
        # And the cached price is returned rather than a null.
        self.assertEqual(body["price_inr"], 49000)

    def test_force_outside_the_floor_still_refetches(self):
        """The floor is one hour, not a permanent cache."""
        self._set_last_fetch(datetime.now(timezone.utc) - timedelta(hours=3))

        import motoquant.database.pricing_refresh as pr_mod

        calls = []
        original = pr_mod.fetch_live_price

        def _fake(*a, **k):
            calls.append(k.get("force"))
            return None  # "fetch_failed" path — no network in tests

        pr_mod.fetch_live_price = _fake
        try:
            r = self._refresh(force=True)
        finally:
            pr_mod.fetch_live_price = original

        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["status"], "fetch_failed")
        self.assertEqual(calls, [True], "force=true no longer reaches the fetcher")

    def test_floor_only_applies_to_force(self):
        """force=false keeps its own 14-day logic inside fetch_live_price."""
        self._set_last_fetch(datetime.now(timezone.utc) - timedelta(minutes=5))

        import motoquant.database.pricing_refresh as pr_mod

        calls = []
        original = pr_mod.fetch_live_price

        def _fake(*a, **k):
            calls.append(k.get("force"))
            return None

        pr_mod.fetch_live_price = _fake
        try:
            r = self._refresh(force=False)
        finally:
            pr_mod.fetch_live_price = original

        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(calls, [False])

    def test_naive_timestamps_are_treated_as_utc(self):
        """fetched_at is written by isoformat(); older rows carry no tz."""
        naive = (datetime.now(timezone.utc) - timedelta(minutes=5)).replace(tzinfo=None)
        self._set_last_fetch_naive(naive)
        r = self._refresh(force=True)
        self.assertEqual(r.json()["status"], "floor_cached")

    def _set_last_fetch_naive(self, when: datetime):
        conn = sqlite3.connect(_TMP_DB_PATH)
        try:
            conn.execute(
                "DELETE FROM part_prices WHERE part_id = ?", (_PRICED_PART_ID,)
            )
            conn.execute(
                "INSERT INTO part_prices "
                "(part_id, retailer, source_url, price_inr, in_stock, fetched_at) "
                "VALUES (?, 'TestRetailer', 'u', 49000, 1, ?)",
                (_PRICED_PART_ID, when.isoformat()),
            )
            conn.commit()
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
