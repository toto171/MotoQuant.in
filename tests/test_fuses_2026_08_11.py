"""
Regression tests for the August-11-2026 DoS-fuse batch (api.py hardening).

What is pinned here (each test fails if its production fix is reverted):

1. Rate-limit fuses on the cost-bearing sim routes:
   - /api/simulate/quick        bucket "quick_sim"        30/60s
   - /api/simulate (+ jobs)     bucket "simulate"         30/60s SHARED
   - /api/simulate/top-speed (+ jobs)  bucket "topspeed"  30/60s SHARED
   - /api/calibrate/dragy + /dyno      bucket "calibrate_upload" 6/60s SHARED
   - /api/simulate/distance     bucket "distance"         10/60s (added in the
     2026-10-23 open-source pivot: the retired sim-quota meter had been its
     ONLY fuse, and it is the heaviest sim route — up to 300 s of sim time)
   The job routes deliberately share their sync twin's bucket (the web
   client falls back between the two — a split bucket would double the
   effective limit), so the tests drive BOTH routes against ONE window.

2. ``part_ids`` request caps (``max_length=30``) on quick / top-speed /
   distance / compare (both ``a_part_ids`` and ``b_part_ids``) — an
   unbounded list was a free CPU/DB amplifier.

3. ``max_time_s`` ceilings: top-speed ``le=120`` (le=300 preallocated
   ~43 MB of numpy per request on the 512 MB instance) while the distance
   route DELIBERATELY keeps ``le=300`` for 20 km LSR courses.

4. GZipMiddleware(minimum_size=1024): large JSON (openapi) compresses,
   tiny responses (/api/health) stay uncompressed.

All bursts use an unknown ``bike_preset`` — _build_config 404s BEFORE any
RK4 work, but the route-level rate_limit dependency has already counted the
hit, so the fuse is exercised without running a single sim.
"""

import os
import sys
import tempfile
import unittest

from motoquant import ratelimit

# ---------------------------------------------------------------------------
# Isolated DB -- the routes exercised here (/api/simulate,
# /api/simulate/top-speed, /api/simulate/distance, /api/simulate/compare and
# the /api/jobs twins) run through the real app, and connect() falls back to
# the repo's tracked motoquant.db when MOTOQUANT_DB is unset -- so any
# route-level writer would leave residue in the SHIPPED catalog (the retired
# sim-quota meter once committed three such rows on main this way). Same
# pattern as test_hardening_2026_07_13.py / test_api.py.
# ---------------------------------------------------------------------------
_tmp_db_file = tempfile.NamedTemporaryFile(
    prefix="motoquant_fuses_test_", suffix=".db", delete=False
)
_tmp_db_file.close()
_TMP_DB_PATH = _tmp_db_file.name
_IMPORT_PRIOR_MOTOQUANT_DB = os.environ.get("MOTOQUANT_DB")
_PRIOR_MOTOQUANT_DB = _IMPORT_PRIOR_MOTOQUANT_DB
os.environ["MOTOQUANT_DB"] = _TMP_DB_PATH


def setUpModule():
    """Re-assert this module's tmp DB right before its tests run.

    Module-level overrides execute at COLLECTION time, so a sibling module
    imported later leaves MOTOQUANT_DB pointing at ITS tmp DB by the time
    these tests actually run. Re-asserting here makes collection order
    irrelevant. The restore value is captured HERE (run time), not at
    import, so we never restore a sibling's since-deleted tmp path.
    """
    global _PRIOR_MOTOQUANT_DB
    current = os.environ.get("MOTOQUANT_DB")
    if current != _TMP_DB_PATH:
        _PRIOR_MOTOQUANT_DB = current
    os.environ["MOTOQUANT_DB"] = _TMP_DB_PATH


def tearDownModule():
    """Drop the tmp DB and restore MOTOQUANT_DB after all tests finish."""
    _api_mod = sys.modules.get("motoquant.api")
    if _api_mod is not None and getattr(_api_mod, "_db_conn", None) is not None:
        try:
            _api_mod._db_conn.close()
        except Exception:  # noqa: BLE001
            pass
        _api_mod._db_conn = None
    try:
        os.unlink(_TMP_DB_PATH)
    except OSError:
        pass
    if _PRIOR_MOTOQUANT_DB is None:
        os.environ.pop("MOTOQUANT_DB", None)
    else:
        os.environ["MOTOQUANT_DB"] = _PRIOR_MOTOQUANT_DB


_UNKNOWN = {"bike_preset": "no_such_bike_fuses_2026_08_11"}
_TINY_CSV = b"time,speed\n0.0,0.0\n0.1,1.0\n"


class _FuseTestBase(unittest.TestCase):
    """Shared TestClient + limiter hygiene.

    The limiter window table is process-global and TestClient always
    presents the same client host ("testclient"), so every test resets it
    (tests/conftest.py's autouse fixture does too, but the reset here keeps
    the module self-sufficient under bare ``python -m unittest``). The
    kill-switch flag is forced ON for the duration of each test so a stray
    MOTOQUANT_RATE_LIMIT=0 in the environment can't silently skip the fuse
    assertions.
    """

    @classmethod
    def setUpClass(cls):
        try:
            from fastapi.testclient import TestClient

            from motoquant.api import app

            cls.client = TestClient(app)
        except Exception:  # noqa: BLE001
            cls.client = None

    def setUp(self):
        if self.client is None:
            self.skipTest("fastapi not installed")
        self._prior_enabled = ratelimit.RATE_LIMIT_ENABLED
        ratelimit.RATE_LIMIT_ENABLED = True
        ratelimit.reset()

    def tearDown(self):
        ratelimit.RATE_LIMIT_ENABLED = self._prior_enabled
        ratelimit.reset()

    # -- helpers ----------------------------------------------------------
    def assert_rate_limited(self, r):
        """The response is the limiter's own 429, not some other error."""
        self.assertEqual(r.status_code, 429, r.text)
        detail = r.json()["detail"]
        self.assertEqual(detail["error"], "rate_limited")
        self.assertIn("Retry-After", r.headers)
        return detail

    def assert_field_too_long_422(self, r, field_name):
        """422 whose validation error names the offending list field."""
        self.assertEqual(r.status_code, 422, r.text)
        errors = r.json()["detail"]
        self.assertTrue(
            any(field_name in err.get("loc", ()) for err in errors),
            f"422 did not name {field_name!r}: {errors}",
        )

    def assert_validates_as_unknown_preset_404(self, r):
        """Validation passed — the request died on the CHEAP 404 instead."""
        self.assertEqual(r.status_code, 404, r.text)
        self.assertIn("Unknown bike_preset", r.json()["detail"])


class TestQuickSimFuse(_FuseTestBase):
    """/api/simulate/quick previously had NO fuse at all (unmetered by
    pinned design + unlimited): each call is a full RK4 pass, two with
    part_ids. Bucket "quick_sim", 30/60s."""

    def test_burst_31_is_429_with_rate_limited_detail_and_retry_after(self):
        for i in range(30):
            r = self.client.post("/api/simulate/quick", json=_UNKNOWN)
            # Cheap 404 — counts against the fuse without running a sim.
            self.assert_validates_as_unknown_preset_404(r)
            self.assertNotEqual(r.status_code, 429, f"fuse tripped early at {i + 1}")
        detail = self.assert_rate_limited(
            self.client.post("/api/simulate/quick", json=_UNKNOWN)
        )
        self.assertIn("quick_sim", detail["message"])

    def test_429_comes_from_the_real_limiter_window(self):
        """Revert-sensitivity proof: the 429 is the limiter's window state.

        (a) after the burst, the limiter table holds a "quick_sim:*" bucket
        key (pins the bucket NAME, not just some 429); (b) the Retry-After
        header equals the body's retry_after_s, both in the limiter's
        [1, window+1] range; (c) ratelimit.reset() makes the SAME burst pass
        again — so the test measures the limiter, not an accident of some
        other 429 source.
        """
        for _ in range(31):
            r = self.client.post("/api/simulate/quick", json=_UNKNOWN)
        detail = self.assert_rate_limited(r)
        self.assertTrue(
            any(k.startswith("quick_sim:") for k in ratelimit._WINDOWS),
            f"no quick_sim bucket in limiter table: {list(ratelimit._WINDOWS)}",
        )
        retry_after = detail["retry_after_s"]
        self.assertEqual(r.headers["Retry-After"], str(retry_after))
        self.assertGreaterEqual(retry_after, 1)
        self.assertLessEqual(retry_after, 61)
        # Clearing the limiter un-trips the fuse: the identical burst passes.
        ratelimit.reset()
        for _ in range(30):
            r = self.client.post("/api/simulate/quick", json=_UNKNOWN)
            self.assertEqual(r.status_code, 404, r.text)


class TestFullSimSharedBuckets(_FuseTestBase):
    """Sync route and its /api/jobs twin must drain ONE window each —
    fails if either route's decorator OR the bucket-sharing is reverted."""

    def test_simulate_burst_429_and_job_route_shares_the_bucket(self):
        for _ in range(30):
            r = self.client.post("/api/simulate", json=_UNKNOWN)
            self.assert_validates_as_unknown_preset_404(r)
        self.assert_rate_limited(self.client.post("/api/simulate", json=_UNKNOWN))
        # The job route 429s IMMEDIATELY off the shared "simulate" bucket.
        # A split bucket (or a dropped decorator) would answer 202 here.
        self.assert_rate_limited(self.client.post("/api/jobs/simulate", json=_UNKNOWN))

    def test_topspeed_burst_429_and_job_route_shares_the_bucket(self):
        for _ in range(30):
            r = self.client.post("/api/simulate/top-speed", json=_UNKNOWN)
            self.assert_validates_as_unknown_preset_404(r)
        self.assert_rate_limited(
            self.client.post("/api/simulate/top-speed", json=_UNKNOWN)
        )
        self.assert_rate_limited(self.client.post("/api/jobs/topspeed", json=_UNKNOWN))


class TestDistanceFuse(_FuseTestBase):
    """/api/simulate/distance runs up to 20 km / 300 s of sim time per call.
    Its only protection used to be the sim-quota meter; it now has its own,
    tighter bucket ("distance", 10/60s). No job twin exists to share with."""

    _BODY = {"bike_preset": "no_such_preset", "distance_m": 1609.344}

    def test_eleventh_call_is_429(self):
        for i in range(10):
            r = self.client.post("/api/simulate/distance", json=self._BODY)
            self.assert_validates_as_unknown_preset_404(r)
            self.assertNotEqual(r.status_code, 429, f"fuse tripped early at {i + 1}")
        detail = self.assert_rate_limited(
            self.client.post("/api/simulate/distance", json=self._BODY)
        )
        self.assertIn("distance", detail["message"])
        self.assertTrue(
            any(k.startswith("distance:") for k in ratelimit._WINDOWS),
            f"no distance bucket in limiter table: {list(ratelimit._WINDOWS)}",
        )

    def test_bucket_is_not_shared_with_topspeed(self):
        """A dedicated bucket: draining distance must not fuse top-speed."""
        for _ in range(11):
            self.client.post("/api/simulate/distance", json=self._BODY)
        r = self.client.post("/api/simulate/top-speed", json=_UNKNOWN)
        self.assert_validates_as_unknown_preset_404(r)


class TestCalibrateUploadFuse(_FuseTestBase):
    """Both calibration uploads are anonymous and parse up to 25 MB in
    memory — bucket "calibrate_upload", 6/60s, SHARED so alternating
    dragy/dyno doesn't double the effective limit."""

    def _dragy(self):
        return self.client.post(
            "/api/calibrate/dragy",
            files={"file": ("run.csv", _TINY_CSV, "text/csv")},
        )

    def _dyno(self):
        return self.client.post(
            "/api/calibrate/dyno",
            files={"file": ("dyno.csv", _TINY_CSV, "text/csv")},
        )

    def test_seventh_upload_429_and_dyno_shares_the_bucket(self):
        for i in range(6):
            r = self._dragy()
            # Tiny CSV — the response itself doesn't matter (parse failures
            # count too); only that the fuse hasn't tripped yet.
            self.assertNotEqual(r.status_code, 429, f"fuse tripped early at {i + 1}")
        self.assert_rate_limited(self._dragy())
        # Dyno 429s off the SAME window — proves both the dyno decorator
        # and the shared bucket name.
        self.assert_rate_limited(self._dyno())


class TestPartIdsCap(_FuseTestBase):
    """part_ids lists are capped at 30 (each id is a DB lookup + config
    mutation; the list was previously unbounded)."""

    _31_IDS = list(range(1, 32))

    def test_quick_sim_31_part_ids_is_422(self):
        r = self.client.post(
            "/api/simulate/quick", json={**_UNKNOWN, "part_ids": self._31_IDS}
        )
        self.assert_field_too_long_422(r, "part_ids")

    def test_topspeed_31_part_ids_is_422(self):
        r = self.client.post(
            "/api/simulate/top-speed", json={**_UNKNOWN, "part_ids": self._31_IDS}
        )
        self.assert_field_too_long_422(r, "part_ids")

    def test_distance_31_part_ids_is_422(self):
        r = self.client.post(
            "/api/simulate/distance",
            json={**_UNKNOWN, "distance_m": 1000.0, "part_ids": self._31_IDS},
        )
        self.assert_field_too_long_422(r, "part_ids")

    def test_compare_31_a_part_ids_is_422(self):
        r = self.client.post(
            "/api/simulate/compare",
            json={
                "a_bike_preset": "gsxr1000_k5",
                "b_bike_preset": "gsxr1000_k5",
                "a_part_ids": self._31_IDS,
            },
        )
        self.assert_field_too_long_422(r, "a_part_ids")

    def test_compare_31_b_part_ids_is_422(self):
        r = self.client.post(
            "/api/simulate/compare",
            json={
                "a_bike_preset": "gsxr1000_k5",
                "b_bike_preset": "gsxr1000_k5",
                "b_part_ids": self._31_IDS,
            },
        )
        self.assert_field_too_long_422(r, "b_part_ids")

    def test_exactly_30_part_ids_still_validates(self):
        """The cap is >30, not >=30 — 30 ids pass validation. The unknown
        preset 404 proves it cheaply without simming a 30-part build."""
        r = self.client.post(
            "/api/simulate/quick", json={**_UNKNOWN, "part_ids": list(range(1, 31))}
        )
        self.assert_validates_as_unknown_preset_404(r)


class TestMaxTimeCeilings(_FuseTestBase):
    """n_max preallocates 18 float64 arrays of max_time_s/dt slots — the
    ceiling is a memory fuse. Top-speed dropped le=300 → le=120; the
    distance route DELIBERATELY keeps le=300 (20 km LSR runs need it)."""

    def test_topspeed_121_is_422_and_120_validates(self):
        r = self.client.post(
            "/api/simulate/top-speed", json={**_UNKNOWN, "max_time_s": 121.0}
        )
        self.assertEqual(r.status_code, 422, r.text)
        self.assertTrue(
            any("max_time_s" in err.get("loc", ()) for err in r.json()["detail"])
        )
        r = self.client.post(
            "/api/simulate/top-speed", json={**_UNKNOWN, "max_time_s": 120.0}
        )
        self.assert_validates_as_unknown_preset_404(r)

    def test_distance_300_validates_and_301_is_422(self):
        """Pins the DELIBERATE keep: le=300 on the distance route."""
        r = self.client.post(
            "/api/simulate/distance",
            json={**_UNKNOWN, "distance_m": 20000.0, "max_time_s": 300.0},
        )
        self.assert_validates_as_unknown_preset_404(r)
        r = self.client.post(
            "/api/simulate/distance",
            json={**_UNKNOWN, "distance_m": 20000.0, "max_time_s": 301.0},
        )
        self.assertEqual(r.status_code, 422, r.text)
        self.assertTrue(
            any("max_time_s" in err.get("loc", ()) for err in r.json()["detail"])
        )


class TestGzipCompression(_FuseTestBase):
    """GZipMiddleware(minimum_size=1024): the origin serves 50-600 KB JSON
    payloads — compressing them is the egress fuse; tiny responses stay
    uncompressed (gzip overhead > win below minimum_size)."""

    def test_large_json_is_gzipped(self):
        r = self.client.get("/openapi.json", headers={"Accept-Encoding": "gzip"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers.get("content-encoding"), "gzip")

    def test_health_stays_uncompressed(self):
        r = self.client.get("/api/health", headers={"Accept-Encoding": "gzip"})
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("content-encoding", r.headers)
        # Sanity: it really is below the middleware's minimum_size.
        self.assertLess(len(r.content), 1024)


if __name__ == "__main__":
    unittest.main()
