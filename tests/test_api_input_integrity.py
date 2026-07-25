"""
API input-integrity regressions (2026-07-25 audit).

Two defects, both of which returned a physically meaningless answer as an
HTTP 200 success rather than rejecting the input:

1. **Duplicate `part_ids` stacked.** ``_apply_parts_to_config`` iterated the
   list verbatim, so ``[56, 56, 56]`` applied one Akrapovic full system three
   times (+36 hp and −20.4 kg from a single exhaust) and reported the
   fabricated ET and a 3x build cost as a normal result.

2. **Unbounded environment overrides.** ``ambient_temp_c`` / ``track_temp_c`` /
   ``humidity_pct`` / ``headwind_kmh`` carried no ge/le bounds on
   SimulateRequest, QuickSimRequest, TopSpeedRequest, DistanceRunRequest or
   CompareRequest — the exact failure the in-file comment above them says the
   bounds prevent, and which ``AutotuneRequest`` had bounded from the start.
   ``humidity_pct: 1e9`` returned ``et_quarter_s: 0.0``.

Both are driven through the real routes per docs/INVARIANTS.md I8. The module
redirects MOTOQUANT_DB at import (and re-asserts at run time) because the
metered sim routes record ``sim_usage`` rows — see the comment in
tests/test_jobs_api.py.
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

_tmp_db_file = tempfile.NamedTemporaryFile(
    prefix="motoquant_input_integrity_", suffix=".db", delete=False
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


def tearDownModule():
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


def _client():
    try:
        from fastapi.testclient import TestClient

        from motoquant.api import app

        return TestClient(app)
    except Exception:  # noqa: BLE001
        return None


class TestEnvironmentOverrideBounds(unittest.TestCase):
    """Out-of-range environment input must be a 422, never a 200 with ET 0.0."""

    @classmethod
    def setUpClass(cls):
        cls.client = _client()

    def _post(self, url, body):
        if self.client is None:
            self.skipTest("fastapi not installed")
        return self.client.post(url, json=body)

    def test_absurd_humidity_is_rejected_not_silently_zeroed(self):
        r = self._post(
            "/api/simulate", {"bike_preset": "gsxr1000_k5", "humidity_pct": 1e9}
        )
        self.assertEqual(r.status_code, 422, r.text)

    def test_absurd_ambient_temp_is_rejected(self):
        r = self._post(
            "/api/simulate", {"bike_preset": "gsxr1000_k5", "ambient_temp_c": 500}
        )
        self.assertEqual(r.status_code, 422, r.text)

    def test_bounds_apply_to_every_sim_request_model(self):
        """QuickSim / TopSpeed / Distance / Compare, not just /api/simulate."""
        cases = [
            ("/api/simulate/quick", {"bike_preset": "gsxr1000_k5"}),
            ("/api/simulate/top-speed", {"bike_preset": "gsxr1000_k5"}),
            (
                "/api/simulate/distance",
                {"bike_preset": "gsxr1000_k5", "distance_m": 402.336},
            ),
            (
                "/api/simulate/compare",
                {"a_bike_preset": "gsxr1000_k5", "b_bike_preset": "gsxr1000_k5"},
            ),
        ]
        for url, base in cases:
            with self.subTest(url=url):
                body = dict(base)
                body["humidity_pct"] = 1e9
                self.assertEqual(self._post(url, body).status_code, 422)

    def test_legitimate_values_still_accepted(self):
        """The bounds must not reject real-world conditions."""
        r = self._post(
            "/api/simulate",
            {
                "bike_preset": "gsxr1000_k5",
                "ambient_temp_c": 42.0,
                "track_temp_c": 55.0,
                "humidity_pct": 85.0,
                "headwind_kmh": -12.0,
            },
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertGreater(r.json()["et_quarter_s"], 0.0)


class TestCalibrationUploadCap(unittest.TestCase):
    """Oversized uploads must 413, not be buffered whole into memory.

    Both calibration routes did a bare ``await file.read()``, materialising the
    entire body as one bytes object with no ceiling and then writing it to a
    second temp file — an unauthenticated OOM + disk-fill lever on the 512 MB
    Render instance. The ``require_tier("studio")`` gate does not stop it:
    require_tier passes anonymous callers through whenever
    MOTOQUANT_BILLING_ENFORCE is falsy, which render.yaml ships as the default.
    """

    @classmethod
    def setUpClass(cls):
        cls.client = _client()

    def _upload(self, url, payload, name="x.csv"):
        import io

        if self.client is None:
            self.skipTest("fastapi not installed")
        return self.client.post(
            url, files={"file": (name, io.BytesIO(payload), "text/csv")}
        )

    def test_oversized_upload_is_413(self):
        from motoquant.api import MAX_UPLOAD_BYTES

        payload = b"a,b,c\n" * ((MAX_UPLOAD_BYTES // 6) + 200_000)
        self.assertGreater(len(payload), MAX_UPLOAD_BYTES)
        for url in ("/api/calibrate/dragy", "/api/calibrate/dyno"):
            with self.subTest(url=url):
                r = self._upload(url, payload)
                self.assertEqual(r.status_code, 413, r.text)
                self.assertEqual(r.json()["detail"]["error"], "upload_too_large")

    def test_413_is_not_remasked_as_400(self):
        """The enclosing `except Exception` must let the 413 through.

        Both routes wrap the read in `try: ... except Exception: raise
        HTTPException(400, ...)`. HTTPException is an Exception, so without an
        explicit pass-through the size rejection surfaced as a generic
        "Failed to read upload" 400 and hid the real reason.
        """
        from motoquant.api import MAX_UPLOAD_BYTES

        payload = b"x" * (MAX_UPLOAD_BYTES + 4096)
        r = self._upload("/api/calibrate/dragy", payload)
        self.assertNotEqual(r.status_code, 400, "413 was remasked as a 400")
        self.assertEqual(r.status_code, 413)

    def test_normal_sized_upload_reaches_the_parser(self):
        """The cap must not block real files — a small CSV gets past it."""
        r = self._upload("/api/calibrate/dragy", b"time,speed\n0,0\n1,10\n")
        # 422 = the parser ran and rejected the content, i.e. the cap allowed it.
        self.assertIn(r.status_code, (200, 422), r.text)


class TestDuplicatePartIdsAreNotStacked(unittest.TestCase):
    """A repeated part id must be applied once, not once per occurrence.

    This class needs a real parts catalog, so it runs against a COPY of the
    tracked motoquant.db — never the tracked file itself (AGENTS.md rule 2).
    ``/api/simulate/quick`` is not metered, so no rows are written either way,
    but the copy keeps that true regardless of future route changes.
    """

    @classmethod
    def setUpClass(cls):
        import shutil

        cls.client = None
        cls._catalog_copy = None
        cls._prior_db = os.environ.get("MOTOQUANT_DB")
        if not os.path.exists("motoquant.db"):
            return
        fh = tempfile.NamedTemporaryFile(
            prefix="motoquant_catalog_copy_", suffix=".db", delete=False
        )
        fh.close()
        cls._catalog_copy = fh.name
        shutil.copy("motoquant.db", cls._catalog_copy)
        os.environ["MOTOQUANT_DB"] = cls._catalog_copy
        cls._reset_api_conn()
        cls.client = _client()

    @staticmethod
    def _reset_api_conn():
        """Drop the api module's cached connection so it re-resolves the env."""
        api_mod = sys.modules.get("motoquant.api")
        if api_mod is not None and getattr(api_mod, "_db_conn", None) is not None:
            try:
                api_mod._db_conn.close()
            except Exception:  # noqa: BLE001
                pass
            api_mod._db_conn = None

    @classmethod
    def tearDownClass(cls):
        cls._reset_api_conn()
        if cls._prior_db is None:
            os.environ.pop("MOTOQUANT_DB", None)
        else:
            os.environ["MOTOQUANT_DB"] = cls._prior_db
        if cls._catalog_copy:
            try:
                os.unlink(cls._catalog_copy)
            except OSError:
                pass

    def _quick(self, part_ids):
        if self.client is None:
            self.skipTest("fastapi or seeded catalog unavailable")
        r = self.client.post(
            "/api/simulate/quick",
            json={"bike_preset": "gsxr1000_k5", "part_ids": part_ids},
        )
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def _first_real_part_id(self):
        """A part that actually changes ET; skip rather than pass on no data."""
        import sqlite3

        if self._catalog_copy is None:
            self.skipTest("no seeded catalog available")
        conn = sqlite3.connect(self._catalog_copy)
        try:
            row = conn.execute(
                "SELECT id FROM parts WHERE param_deltas LIKE '%peak_power_hp%' "
                "ORDER BY id LIMIT 1"
            ).fetchone()
        except sqlite3.Error:
            self.skipTest("no parts table")
        finally:
            conn.close()
        if not row:
            self.skipTest("no power-adding part in the catalog")
        return int(row[0])

    def test_repeated_id_matches_single_id(self):
        pid = self._first_real_part_id()
        once = self._quick([pid])
        thrice = self._quick([pid, pid, pid])
        self.assertAlmostEqual(
            once["et_quarter_s"],
            thrice["et_quarter_s"],
            places=6,
            msg="repeating a part id changed ET — the part is being stacked",
        )

    def test_repeated_id_is_reported_and_costed_once(self):
        pid = self._first_real_part_id()
        thrice = self._quick([pid, pid, pid])
        once = self._quick([pid])
        applied = thrice.get("parts_applied")
        if applied is not None:
            self.assertEqual(
                len(applied), 1, "the same part was reported as applied more than once"
            )
        if once.get("build_cost_inr") is not None:
            self.assertEqual(thrice.get("build_cost_inr"), once.get("build_cost_inr"))


if __name__ == "__main__":
    unittest.main()


class TestCostBearingRoutesAreFused(unittest.TestCase):
    """Per-IP fuses on the unauthenticated routes that spend real resources.

    Both survived adversarial verification in the 2026-07-25 audit:

    * ``/api/pricing/refresh/{id}`` is a SYNC route making a blocking outbound
      fetch, so each in-flight call holds one anyio threadpool worker (default
      40) for a measured worst case of 44.4 s. Unfused, a loop over the 72
      parts carrying a retailer_url starved every other sync route — including
      ``/api/health``, which is Render's healthCheckPath and the keep-alive
      target, so the instance would be marked unhealthy.
    * ``/api/venues/resolve`` falls through to a live OpenWeatherMap call on the
      operator's key when a venue misses, with no caching of the miss.
    """

    @classmethod
    def setUpClass(cls):
        # raise_server_exceptions=False: this module's tmp DB has no catalog
        # tables, so the pricing handler raises once the fuse lets a request
        # through. That is irrelevant here — the assertion is about the
        # dependency firing BEFORE the handler, so we observe status codes
        # (including 500s) rather than letting the handler abort the test.
        try:
            from fastapi.testclient import TestClient

            from motoquant.api import app

            cls.client = TestClient(app, raise_server_exceptions=False)
        except Exception:  # noqa: BLE001
            cls.client = None

    def setUp(self):
        if self.client is None:
            self.skipTest("fastapi not installed")
        from motoquant import ratelimit

        ratelimit.reset()

    def test_pricing_refresh_is_rate_limited(self):
        codes = [
            self.client.post("/api/pricing/refresh/8?force=true").status_code
            for _ in range(9)
        ]
        self.assertIn(429, codes, f"pricing refresh never rate-limited: {codes}")
        # The fuse must precede the handler, i.e. the 429s come at the tail.
        self.assertEqual(codes[-1], 429, f"limit not enforced on later calls: {codes}")

    def test_venue_resolve_is_rate_limited(self):
        codes = [
            self.client.post(
                "/api/venues/resolve", json={"lat": 18.5 + i * 0.01, "lon": 73.8}
            ).status_code
            for i in range(26)
        ]
        self.assertIn(429, codes, f"venue resolve never rate-limited: {codes}")
