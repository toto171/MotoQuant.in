"""
Per-IP rate limits on the credential-burning auth routes (2026-07-25 audit).

Before this, the auth router was mounted with no throttle whatsoever. The only
existing brake, ``auth._login_locked``, keys on the *submitted email*, so an
attacker rotating the address defeats it entirely — while every request still
pays a full scrypt, because ``verify_password`` deliberately runs one even for
a non-existent account (correct for timing-safety, but it makes an
unauthenticated flood a cheap CPU-exhaustion lever against the whole API on a
0.5-CPU instance). ``/magic-link`` additionally sends an email per call.

These drive the real mounted routes so the dependency cannot be silently
dropped. ``/me``, ``/refresh`` and ``/logout`` are deliberately unlimited — a
signed-in client polls them — and the last test pins that intent so nobody
"tightens" them and breaks the UI.
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

_tmp = tempfile.NamedTemporaryFile(
    prefix="motoquant_auth_rl_", suffix=".db", delete=False
)
_tmp.close()
_TMP_DB_PATH = _tmp.name
_PRIOR_MOTOQUANT_DB = os.environ.get("MOTOQUANT_DB")
os.environ["MOTOQUANT_DB"] = _TMP_DB_PATH


def setUpModule():
    global _PRIOR_MOTOQUANT_DB
    current = os.environ.get("MOTOQUANT_DB")
    if current != _TMP_DB_PATH:
        _PRIOR_MOTOQUANT_DB = current
    os.environ["MOTOQUANT_DB"] = _TMP_DB_PATH


def tearDownModule():
    api_mod = sys.modules.get("motoquant.api")
    if api_mod is not None and getattr(api_mod, "_db_conn", None) is not None:
        try:
            api_mod._db_conn.close()
        except Exception:  # noqa: BLE001
            pass
        api_mod._db_conn = None
    try:
        os.unlink(_TMP_DB_PATH)
    except OSError:
        pass
    if _PRIOR_MOTOQUANT_DB is None:
        os.environ.pop("MOTOQUANT_DB", None)
    else:
        os.environ["MOTOQUANT_DB"] = _PRIOR_MOTOQUANT_DB


class TestAuthRateLimits(unittest.TestCase):
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
            self.skipTest("fastapi / auth router not available")
        # Clear the shared limiter state so ordering between tests cannot
        # bleed a spent budget into the next case.
        from motoquant import ratelimit

        try:
            ratelimit.reset()
        except AttributeError:  # pragma: no cover — older signature
            ratelimit._BUCKETS.clear()  # type: ignore[attr-defined]

    def _flood(self, url, body, n):
        """POST n times; return the list of status codes."""
        return [self.client.post(url, json=body).status_code for _ in range(n)]

    def test_login_is_rate_limited(self):
        """A login flood must hit 429 — it is the scrypt CPU-burn lever."""
        codes = self._flood(
            "/api/auth/login", {"email": "nobody@example.com", "password": "x"}, 14
        )
        self.assertIn(429, codes, f"login never rate-limited: {codes}")

    def test_register_is_rate_limited(self):
        codes = self._flood(
            "/api/auth/register", {"email": "a@example.com", "password": "hunter2xx"}, 9
        )
        self.assertIn(429, codes, f"register never rate-limited: {codes}")

    def test_magic_link_is_rate_limited(self):
        """Each call sends an email, so this is the tightest budget."""
        codes = self._flood("/api/auth/magic-link", {"email": "spam@example.com"}, 9)
        self.assertIn(429, codes, f"magic-link never rate-limited: {codes}")

    def test_rotating_the_email_does_not_defeat_the_limit(self):
        """The whole point: the pre-existing brake keyed on email, not IP."""
        codes = [
            self.client.post(
                "/api/auth/login",
                json={"email": f"user{i}@example.com", "password": "x"},
            ).status_code
            for i in range(14)
        ]
        self.assertIn(
            429,
            codes,
            "rotating the submitted email still bypasses the throttle — the "
            "limit is not keyed on the client IP",
        )

    def test_read_routes_stay_unlimited(self):
        """/me must NOT be throttled — a signed-in client polls it.

        Pins the deliberate exclusion so a future 'tighten everything' pass
        cannot quietly break the web UI.
        """
        codes = [self.client.get("/api/auth/me").status_code for _ in range(25)]
        self.assertNotIn(
            429, codes, "/api/auth/me is rate-limited; it is meant to be exempt"
        )


if __name__ == "__main__":
    unittest.main()
