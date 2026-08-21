"""Anonymous free-sim quota identity via X-MQ-Client-Id (2026-08-21).

CGNAT on Indian mobile carriers (Jio/Airtel) puts thousands of users behind
one IP, so keying the anonymous free-sim bucket on IP alone made them share
a single 30/day quota. The metering identity now accepts an optional
client-generated id header. These tests pin:

- a valid id gets its own "cid:"-namespaced bucket (disjoint from IP hashes)
- invalid / missing ids fall back to the IP path unchanged
- the header flows through the REAL metered route into sim_usage rows
"""

import os
import sys
import tempfile
import unittest

from motoquant.usage import anon_identity

try:  # route tests are gated on fastapi being installed (CI always has it)
    from fastapi.testclient import TestClient
    from starlette.requests import Request

    HAS_FASTAPI = True
except ImportError:  # pragma: no cover
    HAS_FASTAPI = False

# ---------------------------------------------------------------------------
# Isolated DB -- the metered route records sim_usage rows via connect(), which
# falls back to the repo's tracked motoquant.db when MOTOQUANT_DB is unset.
# Point it at a throwaway tmp DB so a suite run never dirties the working tree
# (same setUpModule pattern as tests/test_jobs_api.py — see the ordering notes
# there). No seeding needed: bike_presets only, and record_and_check creates
# the sim_usage table on demand.
# ---------------------------------------------------------------------------
_tmp_db_file = tempfile.NamedTemporaryFile(
    prefix="motoquant_cid_test_", suffix=".db", delete=False
)
_tmp_db_file.close()
_TMP_DB_PATH = _tmp_db_file.name
_IMPORT_PRIOR_MOTOQUANT_DB = os.environ.get("MOTOQUANT_DB")
_PRIOR_MOTOQUANT_DB = _IMPORT_PRIOR_MOTOQUANT_DB
os.environ["MOTOQUANT_DB"] = _TMP_DB_PATH


def setUpModule():
    """Re-assert this module's tmp DB right before its tests run (a sibling
    module imported later may have re-pointed MOTOQUANT_DB at ITS tmp DB by
    the time these tests execute — ordering notes in test_jobs_api.py)."""
    global _PRIOR_MOTOQUANT_DB
    current = os.environ.get("MOTOQUANT_DB")
    if current != _TMP_DB_PATH:
        _PRIOR_MOTOQUANT_DB = current
    os.environ["MOTOQUANT_DB"] = _TMP_DB_PATH


def tearDownModule():
    """Remove the tmp DB and restore MOTOQUANT_DB after all tests finish."""
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


def _make_request(headers=None, ip="203.0.113.9"):
    """Bare starlette Request — enough scope for header + client-IP reads."""
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/simulate",
        "headers": [
            (k.lower().encode("latin-1"), v.encode("latin-1"))
            for k, v in (headers or {}).items()
        ],
        "client": (ip, 51234),
        "query_string": b"",
        "scheme": "http",
        "server": ("testserver", 80),
    }
    return Request(scope)


@unittest.skipUnless(HAS_FASTAPI, "fastapi not installed")
class TestClientIdIdentity(unittest.TestCase):
    """_sim_identity_and_tier unit behaviour on the anonymous branch."""

    def _identity(self, headers=None, ip="203.0.113.9"):
        from motoquant.api import _sim_identity_and_tier

        return _sim_identity_and_tier(_make_request(headers, ip))

    def test_valid_client_id_uses_cid_namespace(self):
        ident, tier = self._identity({"X-MQ-Client-Id": "abcdEF12-_34"})
        self.assertEqual(ident, anon_identity("cid:abcdEF12-_34"))
        self.assertEqual(tier, "free")

    def test_length_bounds_inclusive(self):
        for cid in ("a" * 8, "a" * 64):  # both boundary lengths accepted
            ident, _ = self._identity({"X-MQ-Client-Id": cid})
            self.assertEqual(ident, anon_identity("cid:" + cid), len(cid))

    def test_two_cids_same_ip_get_distinct_buckets(self):
        a, _ = self._identity({"X-MQ-Client-Id": "clientAAAA"})
        b, _ = self._identity({"X-MQ-Client-Id": "clientBBBB"})
        self.assertNotEqual(a, b)

    def test_missing_header_falls_back_to_ip(self):
        ident, tier = self._identity()
        self.assertEqual(ident, anon_identity("203.0.113.9"))
        self.assertEqual(tier, "free")

    def test_invalid_ids_fall_back_to_ip(self):
        ip_ident = anon_identity("203.0.113.9")
        bad_ids = (
            "",  # empty
            "short7c",  # 7 chars — below the 8-char floor
            "x" * 65,  # above the 64-char ceiling
            "has space678",  # whitespace
            "semi;colon99",  # punctuation outside [A-Za-z0-9_-]
            "203.0.113.99",  # dots — IP-shaped strings are never valid cids
            "ünicode-8chars",  # non-ASCII
        )
        for bad in bad_ids:
            ident, _ = self._identity({"X-MQ-Client-Id": bad})
            self.assertEqual(ident, ip_ident, f"cid {bad!r} must fall back to IP")

    def test_ip_fallback_unchanged_by_other_headers(self):
        # X-Forwarded-For derivation (rightmost hop) still applies on fallback.
        ident, _ = self._identity(
            {"X-Forwarded-For": "10.0.0.1, 198.51.100.7"}, ip="127.0.0.1"
        )
        self.assertEqual(ident, anon_identity("198.51.100.7"))


@unittest.skipUnless(HAS_FASTAPI, "fastapi not installed")
class TestClientIdMeteredRoute(unittest.TestCase):
    """The header flows through the REAL metered route into sim_usage."""

    @classmethod
    def setUpClass(cls):
        from motoquant.api import app

        cls.client = TestClient(app)

    def _run(self, cid):
        return self.client.post(
            "/api/simulate",
            json={"bike_preset": "gsxr1000_k5"},
            headers={"X-MQ-Client-Id": cid},
        )

    def test_distinct_cids_meter_independently(self):
        import sqlite3

        cid_a = "pytest-cid-AAAA0001"
        cid_b = "pytest-cid-BBBB0001"
        ra1 = self._run(cid_a)
        self.assertEqual(ra1.status_code, 200, ra1.text)
        rb1 = self._run(cid_b)
        self.assertEqual(rb1.status_code, 200, rb1.text)
        ra2 = self._run(cid_a)
        self.assertEqual(ra2.status_code, 200, ra2.text)

        # cid A charged twice, cid B once — separate buckets on one client IP.
        conn = sqlite3.connect(_TMP_DB_PATH)
        try:
            counts = dict(
                conn.execute("SELECT identity, count FROM sim_usage").fetchall()
            )
        finally:
            conn.close()
        self.assertEqual(counts.get(anon_identity("cid:" + cid_a)), 2)
        self.assertEqual(counts.get(anon_identity("cid:" + cid_b)), 1)

        # And the advisory quota headers decrement per-cid, not per-IP.
        rem_a1 = int(ra1.headers["X-Sims-Remaining"])
        rem_b1 = int(rb1.headers["X-Sims-Remaining"])
        rem_a2 = int(ra2.headers["X-Sims-Remaining"])
        self.assertEqual(rem_a1 - 1, rem_a2)
        self.assertEqual(rem_a1, rem_b1)

    def test_quota_headers_are_cors_exposed(self):
        # Task-2 companion: the browser can only read the quota headers if
        # they're CORS-exposed on cross-origin responses.
        r = self.client.post(
            "/api/simulate",
            json={"bike_preset": "gsxr1000_k5"},
            headers={
                "X-MQ-Client-Id": "pytest-cid-CORS0001",
                "Origin": "https://motoquant.in",
            },
        )
        self.assertEqual(r.status_code, 200, r.text)
        exposed = r.headers.get("access-control-expose-headers", "")
        for name in ("X-Sims-Limit", "X-Sims-Remaining", "Retry-After"):
            self.assertIn(name, exposed)


if __name__ == "__main__":
    unittest.main()
