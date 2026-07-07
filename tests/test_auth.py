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

    def setUp(self):
        # These tests exercise ENFORCED billing; the module default is the
        # freemium-beta passthrough (False) since June 2026.
        import motoquant.auth as auth_mod

        self._orig_enforce = auth_mod.BILLING_ENFORCE
        auth_mod.BILLING_ENFORCE = True

    def tearDown(self):
        import motoquant.auth as auth_mod

        auth_mod.BILLING_ENFORCE = self._orig_enforce

    def _make_token(self, tier: str) -> str:
        """Create an access token for a fake user.

        Uses the current jose state so the issue and decode paths agree —
        forcing jose off here (as this helper used to) would mint an
        unsigned "dev." token that the 2026-07-02 security fix now rejects
        whenever jose is actually installed (which it is in CI).
        """
        import motoquant.auth as auth_mod

        return auth_mod._make_access_token(999, "t@t.in", tier, "jti-test")

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

    def test_no_dev_token_leak_in_deployed_env(self):
        """PR #100: the magic-link token must NEVER be echoed in the HTTP
        response on a deployed host — doing so without SMTP configured is an
        account-takeover vector. Locally (dev) the echo is a convenience."""
        import motoquant.auth as auth_mod

        # Deployed: no dev_token in the body regardless of SMTP config.
        conn = _mem_conn()
        _bootstrap(conn)
        with self._patch_conn(conn), patch.object(auth_mod, "IN_DEPLOYED_ENV", True):
            r = self.client.post(
                "/api/auth/magic-link", json={"email": "deployed@test.in"}
            )
        conn.close()
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(r.json().get("dev_token"))

        # Local dev (default EMAIL_BACKEND=stdout, not deployed): echo is on.
        conn2 = _mem_conn()
        _bootstrap(conn2)
        with (
            self._patch_conn(conn2),
            patch.object(auth_mod, "IN_DEPLOYED_ENV", False),
            patch.object(auth_mod, "EMAIL_BACKEND", "stdout"),
        ):
            r2 = self.client.post(
                "/api/auth/magic-link", json={"email": "localdev@test.in"}
            )
        conn2.close()
        self.assertEqual(r2.status_code, 200)
        self.assertTrue(r2.json().get("dev_token"))


class TestMagicLinkSingleUse(unittest.TestCase):
    """PR #100: consuming a magic-link token is atomic single-use — a second
    (or concurrent) verification of the same token must fail, so one sign-in
    link can never mint two JWT pairs."""

    def test_consume_is_single_use(self):
        conn = _mem_conn()
        from motoquant.database import users_repo as u

        u.ensure_tables(conn)
        token = u.create_magic_link(conn, "single@use.in")
        self.assertEqual(u.consume_magic_link(conn, token), "single@use.in")
        self.assertIsNone(u.consume_magic_link(conn, token))
        conn.close()


if __name__ == "__main__":
    unittest.main()


# ══════════════════════════════════════════════════════════════════════════════
# 6. Freemium-beta passthrough (BILLING_ENFORCE = False — the default)
# ══════════════════════════════════════════════════════════════════════════════


class TestRequireTierBetaMode(unittest.TestCase):
    """With billing enforcement OFF (open-beta default), require_tier lets
    anonymous requests through with {} and attaches users when a valid
    token is present — never 401/402."""

    @classmethod
    def setUpClass(cls):
        from fastapi import Depends as _Depends, FastAPI
        from fastapi.testclient import TestClient

        from motoquant.auth import require_tier

        app = FastAPI()

        @app.get("/pro-feature")
        def pro_only(auth: dict = _Depends(require_tier("pro"))):
            return {"ok": True, "attributed": bool(auth.get("id"))}

        cls.client = TestClient(app, raise_server_exceptions=False)

    def setUp(self):
        import motoquant.auth as auth_mod

        self._orig = auth_mod.BILLING_ENFORCE
        auth_mod.BILLING_ENFORCE = False

    def tearDown(self):
        import motoquant.auth as auth_mod

        auth_mod.BILLING_ENFORCE = self._orig

    def test_anonymous_passes_in_beta(self):
        res = self.client.get("/pro-feature")
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.json()["attributed"])

    def test_authenticated_user_attached_in_beta(self):
        import motoquant.auth as auth_mod

        # Use the real jose state so issue/decode agree (see _make_token note).
        token = auth_mod._make_access_token(7, "beta@t.in", "free", "jti-beta")
        fake_user = {"id": 7, "email": "beta@t.in", "tier": "free", "is_active": 1}
        with (
            patch("motoquant.auth._users.is_session_valid", return_value=True),
            patch("motoquant.auth._users.get_user_by_id", return_value=fake_user),
        ):
            res = self.client.get(
                "/pro-feature", headers={"Authorization": f"Bearer {token}"}
            )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["attributed"])

    def test_invalid_token_does_not_error_in_beta(self):
        res = self.client.get(
            "/pro-feature", headers={"Authorization": "Bearer garbage"}
        )
        self.assertEqual(res.status_code, 200)


# ══════════════════════════════════════════════════════════════════════════════
# 7. Password auth — scrypt hashing + register/login/change routes
# ══════════════════════════════════════════════════════════════════════════════


class TestPasswordHashing(unittest.TestCase):
    def test_round_trip(self):
        from motoquant.auth import hash_password, verify_password

        h = hash_password("quarter-mile-9s")
        self.assertTrue(h.startswith("scrypt$"))
        self.assertTrue(verify_password("quarter-mile-9s", h))
        self.assertFalse(verify_password("quarter-mile-10s", h))

    def test_salt_is_random(self):
        from motoquant.auth import hash_password

        self.assertNotEqual(hash_password("same"), hash_password("same"))

    def test_malformed_stored_hash_rejected(self):
        from motoquant.auth import verify_password

        for bad in (None, "", "garbage", "scrypt$broken", "bcrypt$something"):
            self.assertFalse(verify_password("x", bad))


class TestPasswordRoutes(unittest.TestCase):
    """End-to-end register → login → change-password through the router."""

    @classmethod
    def setUpClass(cls):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from motoquant.auth import router as auth_router

        app = FastAPI()
        app.include_router(auth_router, prefix="/api/auth")
        cls.client = TestClient(app, raise_server_exceptions=False)

    def setUp(self):
        import motoquant.auth as auth_mod

        self.conn = _mem_conn()
        _bootstrap(self.conn)
        self._conn_patcher = patch(
            "motoquant.auth._get_conn", return_value=_NoCloseConn(self.conn)
        )
        self._conn_patcher.start()
        auth_mod._failed_logins.clear()

    def tearDown(self):
        self._conn_patcher.stop()
        self.conn.close()

    def _register(self, email="rider@test.in", password="lights-out-9s"):
        return self.client.post(
            "/api/auth/register", json={"email": email, "password": password}
        )

    def test_register_returns_tokens(self):
        res = self._register()
        self.assertEqual(res.status_code, 201)
        body = res.json()
        self.assertIn("access_token", body)
        self.assertEqual(body["tier"], "free")

    def test_register_duplicate_email_409(self):
        self._register()
        res = self._register(password="another-pass-1")
        self.assertEqual(res.status_code, 409)

    def test_register_short_password_422(self):
        res = self._register(password="short")
        self.assertEqual(res.status_code, 422)

    def test_login_success(self):
        self._register()
        res = self.client.post(
            "/api/auth/login",
            json={"email": "rider@test.in", "password": "lights-out-9s"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("refresh_token", res.json())

    def test_login_wrong_password_401(self):
        self._register()
        res = self.client.post(
            "/api/auth/login",
            json={"email": "rider@test.in", "password": "wrong-password"},
        )
        self.assertEqual(res.status_code, 401)

    def test_login_unknown_email_401_no_enumeration(self):
        res = self.client.post(
            "/api/auth/login",
            json={"email": "ghost@test.in", "password": "whatever-123"},
        )
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["detail"], "Invalid email or password.")

    def test_login_rate_limited_after_8_failures(self):
        self._register()
        for _ in range(8):
            self.client.post(
                "/api/auth/login",
                json={"email": "rider@test.in", "password": "wrong-password"},
            )
        res = self.client.post(
            "/api/auth/login",
            json={"email": "rider@test.in", "password": "lights-out-9s"},
        )
        self.assertEqual(res.status_code, 429)

    def test_magic_link_user_can_set_first_password(self):
        from motoquant.database import users_repo

        users_repo.get_or_create_user(self.conn, "linkonly@test.in")
        # sign in via magic link
        token = users_repo.create_magic_link(self.conn, "linkonly@test.in")
        res = self.client.post("/api/auth/verify", json={"token": token})
        self.assertEqual(res.status_code, 200)
        access = res.json()["access_token"]
        # set first password without current_password
        res = self.client.post(
            "/api/auth/password/change",
            json={"new_password": "first-password-1"},
            headers={"Authorization": f"Bearer {access}"},
        )
        self.assertEqual(res.status_code, 200)
        # password login now works
        res = self.client.post(
            "/api/auth/login",
            json={"email": "linkonly@test.in", "password": "first-password-1"},
        )
        self.assertEqual(res.status_code, 200)

    def test_change_password_requires_current_when_set(self):
        reg = self._register().json()
        headers = {"Authorization": f"Bearer {reg['access_token']}"}
        res = self.client.post(
            "/api/auth/password/change",
            json={"new_password": "new-password-22"},
            headers=headers,
        )
        self.assertEqual(res.status_code, 403)
        res = self.client.post(
            "/api/auth/password/change",
            json={
                "current_password": "lights-out-9s",
                "new_password": "new-password-22",
            },
            headers=headers,
        )
        self.assertEqual(res.status_code, 200)
        res = self.client.post(
            "/api/auth/login",
            json={"email": "rider@test.in", "password": "new-password-22"},
        )
        self.assertEqual(res.status_code, 200)

    def test_magic_link_verify_marks_email_verified(self):
        from motoquant.database import users_repo

        token = users_repo.create_magic_link(self.conn, "verifyme@test.in")
        self.client.post("/api/auth/verify", json={"token": token})
        user = users_repo.get_user_by_email(self.conn, "verifyme@test.in")
        self.assertEqual(user["email_verified"], 1)


# ══════════════════════════════════════════════════════════════════════════════
# 8. Paid-tooling tier gate — /api/optimize/* + /api/autotune/* (roadmap A1-1)
# ══════════════════════════════════════════════════════════════════════════════


class TestPaidToolingTierGate(unittest.TestCase):
    """The build optimiser + ECU autotune surface (sync + job variants) is
    pro-tier gated via Depends(require_tier("pro")).

    The gate is INERT until MOTOQUANT_BILLING_ENFORCE is truthy:
      * billing OFF (freemium-beta default) → anonymous requests pass the gate
        exactly as before (no 401/402 regression);
      * billing ON + no token             → 401 (authentication required);
      * billing ON + authenticated free   → 402 (upgrade_required — genuine
        payment-required path, mirroring /api/simulate/save).

    Only the auth gate is under test here, so the request bodies are kept
    minimal (a preset bike) and responses are checked for the gate status,
    not the downstream simulation result.  TestClient is built with
    raise_server_exceptions=False so a downstream 5xx surfaces as a response
    rather than bubbling out of the client (the gate assertions never depend
    on the body running).
    """

    # Every route gated in this change, with a minimal valid JSON body.
    ROUTES = (
        ("/api/optimize/build", {"bike_preset": "gsxr1000_k5", "budget_inr": 60000}),
        (
            "/api/autotune/ecu",
            {"bike_preset": "gsxr1000_k5", "gear_span": 1, "launch_steps": 2},
        ),
        ("/api/jobs/optimize", {"bike_preset": "gsxr1000_k5", "budget_inr": 60000}),
        (
            "/api/jobs/autotune",
            {"bike_preset": "gsxr1000_k5", "gear_span": 1, "launch_steps": 2},
        ),
    )

    @classmethod
    def setUpClass(cls):
        try:
            from fastapi.testclient import TestClient

            from motoquant.api import app
        except ImportError:
            raise unittest.SkipTest("fastapi not installed")
        cls.client = TestClient(app, raise_server_exceptions=False)

    def setUp(self):
        import motoquant.auth as auth_mod

        self._orig_enforce = auth_mod.BILLING_ENFORCE

    def tearDown(self):
        import motoquant.auth as auth_mod

        auth_mod.BILLING_ENFORCE = self._orig_enforce

    def _set_enforce(self, value: bool):
        import motoquant.auth as auth_mod

        auth_mod.BILLING_ENFORCE = value

    def _make_token(self, tier: str) -> str:
        import motoquant.auth as auth_mod

        return auth_mod._make_access_token(999, "t@t.in", tier, "jti-tooling")

    # (1) NO REGRESSION: billing OFF (default) → gate is inert, anonymous passes.
    def test_billing_off_routes_pass_anonymously(self):
        self._set_enforce(False)
        for path, body in self.ROUTES:
            with self.subTest(route=path):
                res = self.client.post(path, json=body)
                self.assertNotIn(
                    res.status_code,
                    (401, 402),
                    f"{path} unexpectedly auth-blocked with billing OFF: "
                    f"{res.status_code} {res.text[:200]}",
                )

    # (2a) billing ON + no token → 401 (require_tier's unauthenticated branch).
    def test_billing_on_no_token_gets_401(self):
        self._set_enforce(True)
        for path, body in self.ROUTES:
            with self.subTest(route=path):
                res = self.client.post(path, json=body)
                self.assertEqual(
                    res.status_code,
                    401,
                    f"{path}: expected 401 with billing ON + no token, "
                    f"got {res.status_code} {res.text[:200]}",
                )

    # (2b) billing ON + authenticated free-tier user → 402 payment required.
    def test_billing_on_free_user_gets_402(self):
        self._set_enforce(True)
        token = self._make_token("free")
        fake_user = {"id": 999, "email": "t@t.in", "tier": "free", "is_active": 1}
        for path, body in self.ROUTES:
            with self.subTest(route=path):
                with (
                    patch("motoquant.auth._users.is_session_valid", return_value=True),
                    patch(
                        "motoquant.auth._users.get_user_by_id", return_value=fake_user
                    ),
                ):
                    res = self.client.post(
                        path,
                        json=body,
                        headers={"Authorization": f"Bearer {token}"},
                    )
                self.assertEqual(
                    res.status_code,
                    402,
                    f"{path}: expected 402 for free-tier user, "
                    f"got {res.status_code} {res.text[:200]}",
                )
                self.assertEqual(res.json()["detail"]["error"], "upgrade_required")

    # billing ON + authenticated pro-tier user → gate passes (not 401/402).
    def test_billing_on_pro_user_passes_gate(self):
        self._set_enforce(True)
        token = self._make_token("pro")
        fake_user = {"id": 999, "email": "t@t.in", "tier": "pro", "is_active": 1}
        for path, body in self.ROUTES:
            with self.subTest(route=path):
                with (
                    patch("motoquant.auth._users.is_session_valid", return_value=True),
                    patch(
                        "motoquant.auth._users.get_user_by_id", return_value=fake_user
                    ),
                ):
                    res = self.client.post(
                        path,
                        json=body,
                        headers={"Authorization": f"Bearer {token}"},
                    )
                self.assertNotIn(
                    res.status_code,
                    (401, 402),
                    f"{path}: pro user unexpectedly gate-blocked "
                    f"{res.status_code} {res.text[:200]}",
                )
