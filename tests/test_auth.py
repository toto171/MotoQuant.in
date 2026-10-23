"""
MotoQuant — Auth module tests
=============================
Tests for the OPTIONAL-accounts layer: magic-link issuance, JWT lifecycle,
the JWT signing-secret policy (ephemeral secret on deployed hosts), password
auth, and rate limiting. Accounts carry no tiers — every feature is free.
All tests use in-memory SQLite — no network calls, no file system I/O beyond /tmp.
Section 4b spawns short-lived subprocesses (the boot guard is import-time code,
so the only honest way to exercise it is a fresh interpreter).

Run with:
    python -m pytest tests/test_auth.py -v
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import sqlite3
import subprocess
import sys
import unittest
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent.parent

# motoquant.auth imports fastapi at module scope, so the email-backend tests
# below can only run where it is installed (CI has it; a bare checkout may not).
try:
    from fastapi import HTTPException

    _FASTAPI_OK = True
except ImportError:  # pragma: no cover — mirrors the gating other classes use
    HTTPException = Exception
    _FASTAPI_OK = False

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
        self.assertEqual(user["is_active"], 1)

    def test_fresh_schema_has_no_monetization_columns(self):
        """New DBs must not grow the retired tier / payment-customer columns
        (open-source pivot, 2026-10-23)."""
        cols = {r[1] for r in self.conn.execute("PRAGMA table_info(users)")}
        for dead in ("tier", "razorpay_customer_id", "stripe_customer_id"):
            self.assertNotIn(dead, cols)
        for live in ("email", "is_active", "password_hash", "email_verified"):
            self.assertIn(live, cols)

    def test_get_or_create_idempotent(self):
        u1 = users_repo.get_or_create_user(self.conn, "rider@test.in")
        u2 = users_repo.get_or_create_user(self.conn, "rider@test.in")
        self.assertEqual(u1["id"], u2["id"])

    def test_email_normalised_to_lowercase(self):
        users_repo.get_or_create_user(self.conn, "Rider@Test.IN")
        user = users_repo.get_user_by_email(self.conn, "rider@test.in")
        self.assertIsNotNone(user)

    def test_deactivate_user(self):
        user = users_repo.get_or_create_user(self.conn, "rider@test.in")
        users_repo.deactivate_user(self.conn, user["id"])
        updated = users_repo.get_user_by_id(self.conn, user["id"])
        self.assertEqual(updated["is_active"], 0)


class TestLegacyUsersSchemaStillWorks(unittest.TestCase):
    """Databases created before the open-source pivot still carry
    ``users.tier`` (NOT NULL DEFAULT 'free', CHECK free/pro/studio) and the two
    payment-customer columns until the drop-monetization patch runs. The
    INSERTs no longer name ``tier``, so they must lean on the column DEFAULT —
    this pins that such a DB keeps accepting sign-ups and sign-ins."""

    def setUp(self):
        self.conn = _mem_conn()
        # The exact pre-pivot DDL (users_repo.ensure_tables before 2026-10-23).
        self.conn.executescript(
            """
            CREATE TABLE users (
                id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                email                   TEXT    NOT NULL UNIQUE,
                tier                    TEXT    NOT NULL DEFAULT 'free'
                                                CHECK(tier IN ('free','pro','studio')),
                is_active               INTEGER NOT NULL DEFAULT 1,
                razorpay_customer_id    TEXT,
                stripe_customer_id      TEXT,
                password_hash           TEXT,
                email_verified          INTEGER NOT NULL DEFAULT 0,
                created_at              TEXT    DEFAULT (datetime('now','utc')),
                updated_at              TEXT    DEFAULT (datetime('now','utc'))
            );
            """
        )
        _bootstrap(self.conn)  # ensure_tables is idempotent over the old table

    def tearDown(self):
        self.conn.close()

    def test_magic_link_signup_on_legacy_schema(self):
        user = users_repo.get_or_create_user(self.conn, "old@test.in")
        self.assertEqual(user["email"], "old@test.in")
        self.assertEqual(user["tier"], "free")  # filled by the column DEFAULT

    def test_password_signup_on_legacy_schema(self):
        user = users_repo.create_user_with_password(
            self.conn, "oldpw@test.in", "scrypt$1$1$1$00$00"
        )
        self.assertEqual(user["email"], "oldpw@test.in")
        self.assertEqual(user["is_active"], 1)


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
        # Force dev fallback (no JWT lib) for deterministic testing
        import motoquant.auth as auth_mod

        self._orig_jwt = auth_mod._JWT_AVAILABLE
        auth_mod._JWT_AVAILABLE = False

    def tearDown(self):
        import motoquant.auth as auth_mod

        auth_mod._JWT_AVAILABLE = self._orig_jwt

    def test_make_and_decode_access_token(self):
        import motoquant.auth as auth_mod

        token = auth_mod._make_access_token(42, "x@y.com", "jti-123")
        payload = auth_mod._decode_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["sub"], "42")
        self.assertEqual(payload["type"], "access")
        self.assertNotIn("tier", payload)

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
# 4b. JWT signing-secret policy  (docs/INVARIANTS.md I7, AGENTS.md §4)
# ══════════════════════════════════════════════════════════════════════════════
# `motoquant/auth.py` resolves its signing secret at import time:
#   * a real JWT_SECRET → used as-is;
#   * a DEPLOYED host (RENDER / RENDER_EXTERNAL_URL / MOTOQUANT_DEPLOYED=1)
#     without one → an EPHEMERAL per-process random secret + a loud warning
#     (tokens unforgeable; sign-ins reset on restart; never a hard failure);
#   * local dev / tests → the documented public dev default, with a warning.
# Before the open-source pivot (2026-10-23) this guard was keyed on the deleted
# billing switch and the shipped deploy (billing off, no JWT_SECRET) signed
# with the PUBLIC default — anyone could forge a token for any account.
#
# The policy is *module-level* code, so it cannot be exercised by patching the
# already-imported module — that would test a re-implementation. Each case
# boots a fresh interpreter with the real environment and asserts on the real
# outcome, including that a token forged with the public default is REJECTED.
# `importlib.reload` is deliberately NOT used: it would rebuild `auth.router`
# under the running FastAPI app that already holds a reference to the old one.

_BOOT_PROBE = """
import hashlib, json
from datetime import datetime, timedelta, timezone
import jwt
import motoquant.auth as a
forged = jwt.encode(
    {"sub": "1", "jti": "x", "type": "access",
     "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
    a.DEV_DEFAULT_JWT_SECRET, algorithm="HS256")
print("PROBE " + json.dumps({
    "deployed": a.IN_DEPLOYED_ENV,
    "is_default": a.JWT_SECRET == a.DEV_DEFAULT_JWT_SECRET,
    "ephemeral": a.JWT_SECRET_IS_EPHEMERAL,
    "secret_len": len(a.JWT_SECRET),
    "secret_sha": hashlib.sha256(a.JWT_SECRET.encode()).hexdigest()[:16],
    "forged_accepted": a._decode_token(forged) is not None,
}))
"""
_DEFAULT_JWT_SECRET = "dev-insecure-secret-change-me"
_DEPLOY_ENV_VARS = ("RENDER", "RENDER_EXTERNAL_URL", "MOTOQUANT_DEPLOYED")


def _boot_auth(*, jwt_secret=None, **deploy_env):
    """Import `motoquant.auth` in a fresh interpreter under the given env.

    Every JWT / deployment variable starts UNSET (a fresh clone, every CI
    job); ``jwt_secret`` and ``deploy_env`` (RENDER=..., MOTOQUANT_DEPLOYED=...)
    then set exactly what the case needs. Returns (CompletedProcess, probe dict
    or None)."""
    env = dict(os.environ)
    env.pop("JWT_SECRET", None)
    for var in _DEPLOY_ENV_VARS:
        env.pop(var, None)
    if jwt_secret is not None:
        env["JWT_SECRET"] = jwt_secret
    env.update(deploy_env)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(REPO_ROOT), env.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    proc = subprocess.run(
        [sys.executable, "-c", _BOOT_PROBE],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        env=env,
        timeout=120,
    )
    probe = None
    for line in proc.stdout.splitlines():
        if line.startswith("PROBE "):
            probe = json.loads(line[len("PROBE ") :])
    return proc, probe


@unittest.skipIf(
    importlib.util.find_spec("fastapi") is None
    or importlib.util.find_spec("jwt") is None,
    "fastapi/PyJWT not installed — motoquant.auth cannot sign real tokens",
)
class TestJwtSecretPolicy(unittest.TestCase):
    def _assert_booted(self, proc, probe):
        self.assertEqual(proc.returncode, 0, proc.stderr[-1500:])
        self.assertIsNotNone(probe, proc.stdout)
        return probe

    def test_deployed_without_secret_uses_ephemeral_secret(self):
        """The shipped Render deploy sets no JWT_SECRET. It must boot (never
        hard-fail) AND must not sign with the public default."""
        proc, probe = _boot_auth(RENDER="true")
        probe = self._assert_booted(proc, probe)
        self.assertTrue(probe["deployed"])
        self.assertFalse(probe["is_default"])
        self.assertTrue(probe["ephemeral"])
        self.assertGreaterEqual(probe["secret_len"], 64)  # token_hex(32)
        self.assertIn("EPHEMERAL", proc.stderr)
        self.assertFalse(
            probe["forged_accepted"],
            "a token signed with the PUBLIC default secret was accepted on a "
            "deployed host — anyone can forge a session for any account",
        )

    def test_deployed_with_default_secret_set_explicitly_is_ephemeral(self):
        """Key on the VALUE, not on "was the env var absent": an operator who
        copies the documented placeholder into their dashboard is in exactly
        the same danger as one who never set it."""
        proc, probe = _boot_auth(
            jwt_secret=_DEFAULT_JWT_SECRET, RENDER_EXTERNAL_URL="https://x"
        )
        probe = self._assert_booted(proc, probe)
        self.assertTrue(probe["ephemeral"])
        self.assertFalse(probe["is_default"])
        self.assertFalse(probe["forged_accepted"])

    def test_every_deployed_spelling_arms_the_policy(self):
        """RENDER, RENDER_EXTERNAL_URL and every truthy MOTOQUANT_DEPLOYED
        spelling must count as deployed, or that spelling silently signs with
        the public default."""
        cases = [{"RENDER": "true"}, {"RENDER_EXTERNAL_URL": "https://mq.example"}]
        cases += [
            {"MOTOQUANT_DEPLOYED": v} for v in ("1", "true", "TRUE", " yes ", "on")
        ]
        for env in cases:
            with self.subTest(env=env):
                proc, probe = _boot_auth(**env)
                probe = self._assert_booted(proc, probe)
                self.assertTrue(probe["deployed"], env)
                self.assertTrue(probe["ephemeral"], env)
                self.assertFalse(probe["forged_accepted"], env)

    def test_falsy_deployed_flag_is_local_dev(self):
        for value in ("0", "false", "no", ""):
            with self.subTest(MOTOQUANT_DEPLOYED=value):
                proc, probe = _boot_auth(MOTOQUANT_DEPLOYED=value)
                probe = self._assert_booted(proc, probe)
                self.assertFalse(probe["deployed"])
                self.assertTrue(probe["is_default"])

    def test_ephemeral_secret_differs_per_process(self):
        """Per-PROCESS random: two boots must not share a secret (a constant
        "ephemeral" value would just be a second public default)."""
        _, p1 = _boot_auth(RENDER="true")
        _, p2 = _boot_auth(RENDER="true")
        self.assertIsNotNone(p1)
        self.assertIsNotNone(p2)
        self.assertNotEqual(p1["secret_sha"], p2["secret_sha"])

    def test_real_secret_is_used_on_a_deployed_host(self):
        """The policy must not override a properly configured deployment —
        sessions have to survive restarts there."""
        real = "a" * 64  # stands in for 32+ random bytes, hex-encoded
        proc, probe = _boot_auth(jwt_secret=real, RENDER="true")
        probe = self._assert_booted(proc, probe)
        self.assertFalse(probe["ephemeral"])
        self.assertEqual(
            probe["secret_sha"], hashlib.sha256(real.encode()).hexdigest()[:16]
        )
        self.assertNotIn("EPHEMERAL", proc.stderr)

    def test_local_dev_keeps_the_documented_default(self):
        """Neither variable set — a fresh clone, and every CI job. Dev keeps
        the default so tokens survive `uvicorn --reload`, but says so."""
        proc, probe = _boot_auth()
        probe = self._assert_booted(proc, probe)
        self.assertFalse(probe["deployed"])
        self.assertTrue(probe["is_default"])
        self.assertFalse(probe["ephemeral"])
        self.assertIn("insecure public dev default", proc.stderr)


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

        # Deployed with no email backend: 503, and critically no token in the
        # body. (This used to answer 200 "Sign-in link sent" while sending
        # nothing — see TestEmailBackendResolution for why that changed.)
        conn = _mem_conn()
        _bootstrap(conn)
        with (
            self._patch_conn(conn),
            patch.object(auth_mod, "IN_DEPLOYED_ENV", True),
            patch.object(auth_mod, "EMAIL_BACKEND", "stdout"),
        ):
            r = self.client.post(
                "/api/auth/magic-link", json={"email": "deployed@test.in"}
            )
        conn.close()
        self.assertEqual(r.status_code, 503)
        self.assertIsNone(r.json().get("dev_token"))

        # Deployed WITH a working backend: 200, still no token echoed.
        conn3 = _mem_conn()
        _bootstrap(conn3)
        with (
            self._patch_conn(conn3),
            patch.object(auth_mod, "IN_DEPLOYED_ENV", True),
            patch.object(auth_mod, "EMAIL_BACKEND", "resend"),
            patch.object(auth_mod, "_send_via_resend", lambda *a, **k: None),
        ):
            r3 = self.client.post(
                "/api/auth/magic-link", json={"email": "deployed2@test.in"}
            )
        conn3.close()
        self.assertEqual(r3.status_code, 200)
        self.assertIsNone(r3.json().get("dev_token"))

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


@unittest.skipUnless(_FASTAPI_OK, "fastapi not installed")
class TestEmailBackendResolution(unittest.TestCase):
    """The magic-link transport must follow from what the operator configured.

    Regression cover for a silent production bug: MOTOQUANT_EMAIL_BACKEND
    defaulted to "stdout" and the send guard read
    ``if EMAIL_BACKEND == "stdout" or not SMTP_HOST``, so the first clause
    short-circuited true unconditionally. Following the setup doc exactly
    (set SMTP_HOST/PORT/USER/PASS/FROM — the only vars that doc named)
    sent no mail at all, while the API still answered "Sign-in link sent."
    Resend was documented in three places and had no implementation whatsoever.
    """

    _EMAIL_VARS = ("MOTOQUANT_EMAIL_BACKEND", "RESEND_API_KEY", "SMTP_HOST")

    def _resolve(self, **env):
        import motoquant.auth as auth_mod

        cleaned = {k: v for k, v in env.items() if v is not None}
        with patch.dict(os.environ, cleaned, clear=False):
            for var in self._EMAIL_VARS:
                if var not in cleaned:
                    os.environ.pop(var, None)
            return auth_mod._resolve_email_backend()

    def test_nothing_configured_is_stdout(self):
        self.assertEqual(self._resolve(), "stdout")

    def test_smtp_host_alone_selects_smtp(self):
        """THE regression: SMTP_HOST alone used to leave the backend on stdout."""
        self.assertEqual(self._resolve(SMTP_HOST="smtp.example.com"), "smtp")

    def test_resend_key_alone_selects_resend(self):
        self.assertEqual(self._resolve(RESEND_API_KEY="re_test"), "resend")

    def test_resend_outranks_smtp(self):
        self.assertEqual(
            self._resolve(RESEND_API_KEY="re_test", SMTP_HOST="smtp.example.com"),
            "resend",
        )

    def test_explicit_override_wins(self):
        self.assertEqual(
            self._resolve(
                MOTOQUANT_EMAIL_BACKEND="stdout",
                RESEND_API_KEY="re_test",
                SMTP_HOST="smtp.example.com",
            ),
            "stdout",
        )

    def test_override_is_case_insensitive(self):
        self.assertEqual(self._resolve(MOTOQUANT_EMAIL_BACKEND="  ReSend "), "resend")


@unittest.skipUnless(_FASTAPI_OK, "fastapi not installed")
class TestResendTransport(unittest.TestCase):
    """The Resend path builds a correct API request and reports failures."""

    def _capture_request(self):
        import motoquant.auth as auth_mod

        captured = {}

        class _Resp:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def fake_urlopen(req, timeout=None):
            captured["url"] = req.full_url
            captured["method"] = req.get_method()
            captured["headers"] = {k.lower(): v for k, v in req.headers.items()}
            captured["body"] = json.loads(req.data.decode("utf-8"))
            captured["timeout"] = timeout
            return _Resp()

        with (
            patch.dict(
                os.environ,
                {"RESEND_API_KEY": "re_test_key", "SMTP_FROM": "no-reply@motoquant.in"},
                clear=False,
            ),
            patch.object(auth_mod.urllib.request, "urlopen", fake_urlopen),
        ):
            auth_mod._send_via_resend("rider@example.com", "Subject line", "<p>hi</p>")
        return captured

    def test_posts_to_resend_api(self):
        cap = self._capture_request()
        self.assertEqual(cap["url"], "https://api.resend.com/emails")
        self.assertEqual(cap["method"], "POST")

    def test_sends_bearer_token_and_json(self):
        cap = self._capture_request()
        self.assertEqual(cap["headers"]["authorization"], "Bearer re_test_key")
        self.assertEqual(cap["headers"]["content-type"], "application/json")

    def test_payload_shape(self):
        cap = self._capture_request()
        self.assertEqual(cap["body"]["to"], ["rider@example.com"])
        self.assertEqual(cap["body"]["from"], "no-reply@motoquant.in")
        self.assertEqual(cap["body"]["subject"], "Subject line")
        self.assertEqual(cap["body"]["html"], "<p>hi</p>")

    def test_request_is_bounded_by_timeout(self):
        # An unbounded call would hang a worker on the 0.5-CPU instance.
        self.assertIsNotNone(self._capture_request()["timeout"])

    def test_http_error_surfaces_resend_detail(self):
        """Resend names the real cause (unverified domain, bad key) in the body."""
        import motoquant.auth as auth_mod

        err = urllib.error.HTTPError(
            "https://api.resend.com/emails",
            403,
            "Forbidden",
            {},
            io.BytesIO(b'{"message":"domain is not verified"}'),
        )

        def boom(req, timeout=None):
            raise err

        with (
            patch.dict(os.environ, {"RESEND_API_KEY": "re_bad"}, clear=False),
            patch.object(auth_mod.urllib.request, "urlopen", boom),
            self.assertRaises(RuntimeError) as ctx,
        ):
            auth_mod._send_via_resend("a@b.in", "s", "<p>h</p>")
        self.assertIn("domain is not verified", str(ctx.exception))


@unittest.skipUnless(_FASTAPI_OK, "fastapi not installed")
class TestMagicLinkDispatch(unittest.TestCase):
    """_send_magic_link_email routes to the resolved transport."""

    def test_resend_backend_calls_resend(self):
        import motoquant.auth as auth_mod

        calls = []
        with (
            patch.object(auth_mod, "EMAIL_BACKEND", "resend"),
            patch.object(auth_mod, "_send_via_resend", lambda *a, **k: calls.append(a)),
        ):
            auth_mod._send_magic_link_email("rider@example.com", "tok123")
        self.assertEqual(len(calls), 1)
        self.assertIn("tok123", calls[0][2])  # link embedded in the html body

    def test_smtp_backend_calls_smtp(self):
        import motoquant.auth as auth_mod

        calls = []
        with (
            patch.object(auth_mod, "EMAIL_BACKEND", "smtp"),
            patch.object(auth_mod, "_send_via_smtp", lambda *a, **k: calls.append(a)),
        ):
            auth_mod._send_magic_link_email("rider@example.com", "tok456")
        self.assertEqual(len(calls), 1)

    def test_transport_failure_becomes_503(self):
        import motoquant.auth as auth_mod

        def boom(*a, **k):
            raise RuntimeError("smtp exploded")

        with (
            patch.object(auth_mod, "EMAIL_BACKEND", "smtp"),
            patch.object(auth_mod, "_send_via_smtp", boom),
            self.assertRaises(HTTPException) as ctx,
        ):
            auth_mod._send_magic_link_email("rider@example.com", "tok")
        self.assertEqual(ctx.exception.status_code, 503)

    def test_unknown_backend_is_503_not_silent(self):
        import motoquant.auth as auth_mod

        with (
            patch.object(auth_mod, "EMAIL_BACKEND", "sendgrid"),
            self.assertRaises(HTTPException) as ctx,
        ):
            auth_mod._send_magic_link_email("rider@example.com", "tok")
        self.assertEqual(ctx.exception.status_code, 503)

    def test_deployed_without_backend_raises_rather_than_lying(self):
        import motoquant.auth as auth_mod

        with (
            patch.object(auth_mod, "EMAIL_BACKEND", "stdout"),
            patch.object(auth_mod, "IN_DEPLOYED_ENV", True),
            self.assertRaises(HTTPException) as ctx,
        ):
            auth_mod._send_magic_link_email("rider@example.com", "tok")
        self.assertEqual(ctx.exception.status_code, 503)

    def test_local_dev_still_prints_the_link(self):
        import motoquant.auth as auth_mod

        with (
            patch.object(auth_mod, "EMAIL_BACKEND", "stdout"),
            patch.object(auth_mod, "IN_DEPLOYED_ENV", False),
            patch("sys.stdout", new_callable=io.StringIO) as out,
        ):
            auth_mod._send_magic_link_email("rider@example.com", "tok789")
        self.assertIn("tok789", out.getvalue())


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


# ══════════════════════════════════════════════════════════════════════════════
# 6b. get_optional_user — attribution on routes that accept anonymous callers
# ══════════════════════════════════════════════════════════════════════════════


@unittest.skipUnless(_FASTAPI_OK, "fastapi not installed")
class TestGetOptionalUser(unittest.TestCase):
    """POST /api/simulate/save uses get_optional_user: anonymous callers get
    None (never 401), a valid token attaches the user for garage attribution,
    and a garbage token is treated as anonymous rather than erroring."""

    @classmethod
    def setUpClass(cls):
        from fastapi import Depends as _Depends, FastAPI
        from fastapi.testclient import TestClient

        from motoquant.auth import get_optional_user

        app = FastAPI()

        @app.get("/attributed")
        def attributed(user: dict | None = _Depends(get_optional_user)):
            return {"ok": True, "user_id": user["id"] if user else None}

        cls.client = TestClient(app, raise_server_exceptions=False)

    def test_anonymous_is_none(self):
        res = self.client.get("/attributed")
        self.assertEqual(res.status_code, 200)
        self.assertIsNone(res.json()["user_id"])

    def test_valid_token_attaches_user(self):
        import motoquant.auth as auth_mod

        token = auth_mod._make_access_token(7, "rider@t.in", "jti-opt")
        fake_user = {"id": 7, "email": "rider@t.in", "is_active": 1}
        with (
            patch("motoquant.auth._users.is_session_valid", return_value=True),
            patch("motoquant.auth._users.get_user_by_id", return_value=fake_user),
        ):
            res = self.client.get(
                "/attributed", headers={"Authorization": f"Bearer {token}"}
            )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["user_id"], 7)

    def test_invalid_token_is_anonymous_not_an_error(self):
        res = self.client.get(
            "/attributed", headers={"Authorization": "Bearer garbage"}
        )
        self.assertEqual(res.status_code, 200)
        self.assertIsNone(res.json()["user_id"])


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
        self.assertNotIn("tier", body)

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

    def test_me_returns_account_fields_only(self):
        """/me is a plain profile now — no tier, subscription or license keys."""
        reg = self._register().json()
        res = self.client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {reg['access_token']}"}
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["email"], "rider@test.in")
        self.assertTrue(body["has_password"])
        for dead in ("tier", "subscription_status", "license_keys"):
            self.assertNotIn(dead, body)

    def test_magic_link_verify_marks_email_verified(self):
        from motoquant.database import users_repo

        token = users_repo.create_magic_link(self.conn, "verifyme@test.in")
        self.client.post("/api/auth/verify", json={"token": token})
        user = users_repo.get_user_by_email(self.conn, "verifyme@test.in")
        self.assertEqual(user["email_verified"], 1)


if __name__ == "__main__":
    unittest.main()
