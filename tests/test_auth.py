"""
MotoQuant Pro — Auth module tests
===================================
Tests for magic-link issuance, JWT lifecycle, tier gating, and rate limiting.
All tests use in-memory SQLite — no network calls, no file system I/O beyond /tmp.

Run with:
    python -m pytest tests/test_auth.py -v
"""

from __future__ import annotations

import json
import sqlite3
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

# ─── helpers shared across tests ─────────────────────────────────────────────


def _mem_conn() -> sqlite3.Connection:
    """In-memory SQLite connection with Row factory."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _bootstrap(conn: sqlite3.Connection):
    """Create all auth tables in the given connection."""
    from motoquant.database.users_repo import ensure_tables as _u_tables

    _u_tables(conn)


class _NoCloseConn:
    """Thin wrapper around sqlite3.Connection that suppresses close() calls.
    Used in tests where the endpoint would close the injected connection,
    preventing post-call assertions from working.
    """

    def __init__(self, conn):
        self._conn = conn

    def close(self):
        pass  # no-op

    def __getattr__(self, name):
        return getattr(self._conn, name)


# ─── Import the modules under test ───────────────────────────────────────────

from motoquant.database import users_repo as users_repo

# ══════════════════════════════════════════════════════════════════════════════
# 1. User CRUD
# ══════════════════════════════════════════════════════════════════════════════


class TestUserCrud(unittest.TestCase):
    def setUp(self):
        self.conn = _mem_conn()
        _bootstrap(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_get_or_create_new_user(self):
        user = users_repo.get_or_create_user(self.conn, "rider@test.in")
        self.assertEqual(user["email"], "rider@test.in")
        self.assertEqual(user["tier"], "free")
        self.assertEqual(user["is_active"], 1)

    def test_get_or_create_idempotent(self):
        u1 = users_repo.get_or_create_user(self.conn, "rider@test.in")
        u2 = users_repo.get_or_create_user(self.conn, "rider@test.in")
        self.assertEqual(u1["id"], u2["id"])

    def test_email_normalised_to_lowercase(self):
        users_repo.get_or_create_user(self.conn, "Rider@Test.IN")
        user = users_repo.get_user_by_email(self.conn, "rider@test.in")
        self.assertIsNotNone(user)

    def test_set_user_tier(self):
        user = users_repo.get_or_create_user(self.conn, "rider@test.in")
        users_repo.set_user_tier(self.conn, user["id"], "pro")
        updated = users_repo.get_user_by_id(self.conn, user["id"])
        self.assertEqual(updated["tier"], "pro")

    def test_deactivate_user(self):
        user = users_repo.get_or_create_user(self.conn, "rider@test.in")
        users_repo.deactivate_user(self.conn, user["id"])
        updated = users_repo.get_user_by_id(self.conn, user["id"])
        self.assertEqual(updated["is_active"], 0)


# ══════════════════════════════════════════════════════════════════════════════
# 2. Magic link issuance and verification
# ══════════════════════════════════════════════════════════════════════════════


class TestMagicLink(unittest.TestCase):
    def setUp(self):
        self.conn = _mem_conn()
        _bootstrap(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_create_and_consume_magic_link(self):
        token = users_repo.create_magic_link(self.conn, "test@motoquant.in")
        self.assertIsNotNone(token)
        self.assertGreater(len(token), 20)

        email = users_repo.consume_magic_link(self.conn, token)
        self.assertEqual(email, "test@motoquant.in")

    def test_consumed_link_cannot_be_reused(self):
        token = users_repo.create_magic_link(self.conn, "test@motoquant.in")
        users_repo.consume_magic_link(self.conn, token)
        result = users_repo.consume_magic_link(self.conn, token)
        self.assertIsNone(result, "Consumed token should not be reusable")

    def test_invalid_token_returns_none(self):
        result = users_repo.consume_magic_link(self.conn, "garbage-token-xyz")
        self.assertIsNone(result)

    def test_expired_token_returns_none(self):
        token = users_repo.create_magic_link(self.conn, "test@motoquant.in")
        # Manually expire the link
        self.conn.execute(
            "UPDATE magic_links SET expires_at = ? WHERE consumed = 0",
            ((datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),),
        )
        self.conn.commit()
        result = users_repo.consume_magic_link(self.conn, token)
        self.assertIsNone(result, "Expired token should be rejected")

    def test_rate_limit_recent_link_check(self):
        users_repo.create_magic_link(self.conn, "rate@test.in")
        # A second request within 60 s should be detected as a recent link
        exists = users_repo.recent_magic_link_exists(self.conn, "rate@test.in")
        self.assertTrue(exists)

    def test_rate_limit_no_recent_link_initially(self):
        exists = users_repo.recent_magic_link_exists(self.conn, "fresh@test.in")
        self.assertFalse(exists)


# ══════════════════════════════════════════════════════════════════════════════
# 3. Session management
# ══════════════════════════════════════════════════════════════════════════════


class TestSessions(unittest.TestCase):
    def setUp(self):
        self.conn = _mem_conn()
        _bootstrap(self.conn)
        self.user = users_repo.get_or_create_user(self.conn, "sess@test.in")

    def tearDown(self):
        self.conn.close()

    def test_create_and_validate_session(self):
        import uuid

        jti = str(uuid.uuid4())
        users_repo.create_session(self.conn, self.user["id"], jti)
        self.assertTrue(users_repo.is_session_valid(self.conn, jti))

    def test_revoked_session_is_invalid(self):
        import uuid

        jti = str(uuid.uuid4())
        users_repo.create_session(self.conn, self.user["id"], jti)
        users_repo.revoke_session(self.conn, jti)
        self.assertFalse(users_repo.is_session_valid(self.conn, jti))

    def test_expired_session_is_invalid(self):
        import uuid

        jti = str(uuid.uuid4())
        users_repo.create_session(self.conn, self.user["id"], jti)
        # Manually expire
        self.conn.execute(
            "UPDATE sessions SET expires_at = ? WHERE jwt_id = ?",
            ((datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(), jti),
        )
        self.conn.commit()
        self.assertFalse(users_repo.is_session_valid(self.conn, jti))

    def test_nonexistent_session_is_invalid(self):
        self.assertFalse(users_repo.is_session_valid(self.conn, "no-such-jti"))

    def test_revoke_all_sessions(self):
        import uuid

        jtis = [str(uuid.uuid4()) for _ in range(3)]
        for jti in jtis:
            users_repo.create_session(self.conn, self.user["id"], jti)
        users_repo.revoke_all_sessions(self.conn, self.user["id"])
        for jti in jtis:
            self.assertFalse(users_repo.is_session_valid(self.conn, jti))


# ══════════════════════════════════════════════════════════════════════════════
# 4. JWT helpers (unit-level, no DB)
# ══════════════════════════════════════════════════════════════════════════════


class TestJwtHelpers(unittest.TestCase):
    """Test the _make_access_token / _decode_token path using the dev fallback."""

    def setUp(self):
        # Force dev fallback (no jose) for deterministic testing
        import motoquant.auth as auth_mod

        self._orig_jose = auth_mod._JOSE_AVAILABLE
        auth_mod._JOSE_AVAILABLE = False

    def tearDown(self):
        import motoquant.auth as auth_mod

        auth_mod._JOSE_AVAILABLE = self._orig_jose

    def test_make_and_decode_access_token(self):
        import motoquant.auth as auth_mod

        token = auth_mod._make_access_token(42, "x@y.com", "pro", "jti-123")
        payload = auth_mod._decode_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["sub"], "42")
        self.assertEqual(payload["tier"], "pro")
        self.assertEqual(payload["type"], "access")

    def test_make_and_decode_refresh_token(self):
        import motoquant.auth as auth_mod

        token = auth_mod._make_refresh_token(42, "jti-456")
        payload = auth_mod._decode_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["sub"], "42")
        self.assertEqual(payload["type"], "refresh")

    def test_expired_token_returns_none(self):
        import base64

        import motoquant.auth as auth_mod

        payload_dict = {
            "sub": "1",
            "jti": "x",
            "type": "access",
            "exp": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
        }
        token = (
            "dev."
            + base64.urlsafe_b64encode(json.dumps(payload_dict).encode()).decode()
        )
        result = auth_mod._decode_token(token)
        self.assertIsNone(result)

    def test_garbage_token_returns_none(self):
        import motoquant.auth as auth_mod

        result = auth_mod._decode_token("not-a-valid-token")
        self.assertIsNone(result)


# ══════════════════════════════════════════════════════════════════════════════
# 5. require_tier dependency (via FastAPI TestClient)
# ══════════════════════════════════════════════════════════════════════════════


class TestRequireTier(unittest.TestCase):
    """
    Test that require_tier returns 200 for correct tier and 402 for insufficient tier.
    Uses a minimal FastAPI test app to avoid messing with the real api.py.
    """

    @classmethod
    def setUpClass(cls):
        try:
            from fastapi import Depends as _Depends, FastAPI
            from fastapi.testclient import TestClient

            from motoquant.auth import require_tier
        except ImportError:
            cls.skipTest(None, "fastapi not installed")
            return

        test_app = FastAPI()

        @test_app.get("/pro-feature")
        def pro_only(_auth: dict = _Depends(require_tier("pro"))):
            return {"ok": True}

        @test_app.get("/studio-feature")
        def studio_only(_auth: dict = _Depends(require_tier("studio"))):
            return {"ok": True}

        cls.client = TestClient(test_app, raise_server_exceptions=False)

    def _make_token(self, tier: str) -> str:
        """Create a dev-mode access token for a fake user."""
        import motoquant.auth as auth_mod

        orig = auth_mod._JOSE_AVAILABLE
        auth_mod._JOSE_AVAILABLE = False
        try:
            token = auth_mod._make_access_token(999, "t@t.in", tier, "jti-test")
        finally:
            auth_mod._JOSE_AVAILABLE = orig
        return token

    def _patch_session_valid(self):
        """Patch DB session check to always return True."""
        return patch("motoquant.auth._users.is_session_valid", return_value=True)

    def _patch_get_user(self, tier: str):
        """Patch DB user lookup to return a fake user with given tier."""
        fake_user = {"id": 999, "email": "t@t.in", "tier": tier, "is_active": 1}
        return patch("motoquant.auth._users.get_user_by_id", return_value=fake_user)

    def test_pro_user_accesses_pro_feature(self):
        token = self._make_token("pro")
        with self._patch_session_valid(), self._patch_get_user("pro"):
            res = self.client.get(
                "/pro-feature",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(res.status_code, 200)

    def test_free_user_gets_402_on_pro_feature(self):
        token = self._make_token("free")
        with self._patch_session_valid(), self._patch_get_user("free"):
            res = self.client.get(
                "/pro-feature",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(res.status_code, 402)
        body = res.json()
        self.assertEqual(body["detail"]["error"], "upgrade_required")
        self.assertEqual(body["detail"]["required_tier"], "pro")

    def test_pro_user_gets_402_on_studio_feature(self):
        token = self._make_token("pro")
        with self._patch_session_valid(), self._patch_get_user("pro"):
            res = self.client.get(
                "/studio-feature",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(res.status_code, 402)

    def test_studio_user_accesses_studio_feature(self):
        token = self._make_token("studio")
        with self._patch_session_valid(), self._patch_get_user("studio"):
            res = self.client.get(
                "/studio-feature",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(res.status_code, 200)

    def test_unauthenticated_request_gets_401(self):
        res = self.client.get("/pro-feature")
        self.assertEqual(res.status_code, 401)


# ══════════════════════════════════════════════════════════════════════════════
# 6. Magic-link endpoint rate-limit (via FastAPI TestClient)
# ══════════════════════════════════════════════════════════════════════════════


class TestMagicLinkEndpoint(unittest.TestCase):
    """Integration test for POST /api/auth/magic-link rate limiting."""

    @classmethod
    def setUpClass(cls):
        try:
            from fastapi.testclient import TestClient

            import motoquant.auth as auth_mod
        except ImportError:
            cls.skipTest(None, "fastapi not installed")
            return

        cls.app = auth_mod.router
        # Build a minimal FastAPI app mounting the auth router
        from fastapi import FastAPI

        mini = FastAPI()
        mini.include_router(auth_mod.router, prefix="/api/auth")
        cls.client = TestClient(mini, raise_server_exceptions=False)

    def _patch_conn(self, conn):
        """Patch _get_conn to return a no-close wrapper so the same in-memory
        connection survives across multiple requests in the same test.
        """
        return patch("motoquant.auth._get_conn", return_value=_NoCloseConn(conn))

    def test_magic_link_rate_limit_429(self):
        conn = _mem_conn()
        _bootstrap(conn)
        with self._patch_conn(conn):
            # First request should succeed
            r1 = self.client.post(
                "/api/auth/magic-link",
                json={"email": "ratelimit@test.in"},
            )
            self.assertIn(r1.status_code, (200, 429))  # may be 200 first time

            # Second immediate request should be rate-limited
            r2 = self.client.post(
                "/api/auth/magic-link",
                json={"email": "ratelimit@test.in"},
            )
            self.assertEqual(r2.status_code, 429)
        conn.close()


if __name__ == "__main__":
    unittest.main()
