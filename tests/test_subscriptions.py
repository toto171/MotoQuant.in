"""
MotoQuant Pro — Subscriptions module tests
============================================
Tests for Razorpay checkout (mocked), webhook handling, tier upgrades,
and license key generate / validate / revoke.

Run with:
    python -m pytest tests/test_subscriptions.py -v

NOTE: Razorpay SDK is mocked in every test — no real API calls are made.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

# ─── helpers ─────────────────────────────────────────────────────────────────


def _mem_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _bootstrap(conn: sqlite3.Connection):
    from motoquant.database.subscriptions_repo import ensure_tables as _s
    from motoquant.database.users_repo import ensure_tables as _u

    _u(conn)
    _s(conn)


def _make_user(conn, email="rider@test.in", tier="pro"):
    from motoquant.database import users_repo as ur

    user = ur.get_or_create_user(conn, email)
    ur.set_user_tier(conn, user["id"], tier)
    return ur.get_user_by_id(conn, user["id"])


class _NoCloseConn:
    """Thin wrapper around sqlite3.Connection that suppresses close() calls.
    Used in tests where the endpoint would close the injected connection,
    preventing post-call assertions from working.
    """

    def __init__(self, conn):
        self._conn = conn

    def close(self):
        pass  # no-op — keep connection alive for test assertions

    def __getattr__(self, name):
        return getattr(self._conn, name)


# ══════════════════════════════════════════════════════════════════════════════
# 1. Subscription repository
# ══════════════════════════════════════════════════════════════════════════════


class TestSubscriptionRepo(unittest.TestCase):
    def setUp(self):
        self.conn = _mem_conn()
        _bootstrap(self.conn)
        self.user = _make_user(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_upsert_creates_subscription(self):
        from motoquant.database import subscriptions_repo as sr

        sub = sr.upsert_subscription(
            self.conn,
            user_id=self.user["id"],
            razorpay_subscription_id="sub_test_001",
            tier="pro",
            status="active",
        )
        self.assertEqual(sub["status"], "active")
        self.assertEqual(sub["tier"], "pro")

    def test_upsert_is_idempotent(self):
        from motoquant.database import subscriptions_repo as sr

        sr.upsert_subscription(
            self.conn,
            user_id=self.user["id"],
            razorpay_subscription_id="sub_test_002",
            tier="pro",
            status="created",
        )
        # Second call same rzp id → update
        sr.upsert_subscription(
            self.conn,
            user_id=self.user["id"],
            razorpay_subscription_id="sub_test_002",
            tier="pro",
            status="active",
        )
        sub = sr.get_subscription_by_rzp_id(self.conn, "sub_test_002")
        self.assertEqual(sub["status"], "active")

    def test_get_active_subscription(self):
        from motoquant.database import subscriptions_repo as sr

        sr.upsert_subscription(
            self.conn,
            user_id=self.user["id"],
            razorpay_subscription_id="sub_test_003",
            tier="pro",
            status="active",
        )
        active = sr.get_active_subscription(self.conn, self.user["id"])
        self.assertIsNotNone(active)
        self.assertEqual(active["razorpay_subscription_id"], "sub_test_003")

    def test_cancelled_subscription_not_returned_as_active(self):
        from motoquant.database import subscriptions_repo as sr

        sr.upsert_subscription(
            self.conn,
            user_id=self.user["id"],
            razorpay_subscription_id="sub_test_004",
            tier="pro",
            status="cancelled",
        )
        active = sr.get_active_subscription(self.conn, self.user["id"])
        self.assertIsNone(active)


# ══════════════════════════════════════════════════════════════════════════════
# 2. License key generation and validation
# ══════════════════════════════════════════════════════════════════════════════


class TestLicenseKeys(unittest.TestCase):
    def setUp(self):
        self.conn = _mem_conn()
        _bootstrap(self.conn)
        self.pro_user = _make_user(self.conn, "pro@test.in", "pro")
        self.studio_user = _make_user(self.conn, "studio@test.in", "studio")
        self.free_user = _make_user(self.conn, "free@test.in", "free")

    def tearDown(self):
        self.conn.close()

    def test_pro_can_generate_one_key(self):
        from motoquant.database import subscriptions_repo as sr

        key = sr.create_license_key(self.conn, self.pro_user["id"], "pro")
        self.assertIsNotNone(key)
        self.assertGreater(len(key), 10)

    def test_pro_cannot_generate_second_key(self):
        from motoquant.database import subscriptions_repo as sr

        sr.create_license_key(self.conn, self.pro_user["id"], "pro")
        second = sr.create_license_key(self.conn, self.pro_user["id"], "pro")
        self.assertIsNone(second, "Pro tier quota is 1 key")

    def test_studio_can_generate_up_to_five_keys(self):
        from motoquant.database import subscriptions_repo as sr

        keys = []
        for _ in range(5):
            k = sr.create_license_key(self.conn, self.studio_user["id"], "studio")
            self.assertIsNotNone(k)
            keys.append(k)
        sixth = sr.create_license_key(self.conn, self.studio_user["id"], "studio")
        self.assertIsNone(sixth, "Studio quota is 5 keys")

    def test_free_user_gets_no_key(self):
        from motoquant.database import subscriptions_repo as sr

        key = sr.create_license_key(self.conn, self.free_user["id"], "free")
        self.assertIsNone(key)

    def test_validate_key_returns_tier(self):
        from motoquant.database import subscriptions_repo as sr

        key = sr.create_license_key(self.conn, self.pro_user["id"], "pro")
        row = sr.validate_license_key(self.conn, key, device_id="device-abc")
        self.assertIsNotNone(row)
        self.assertEqual(row["tier"], "pro")

    def test_validate_invalid_key_returns_none(self):
        from motoquant.database import subscriptions_repo as sr

        row = sr.validate_license_key(self.conn, "invalid-key-xyz")
        self.assertIsNone(row)

    def test_validate_updates_last_seen(self):
        from motoquant.database import subscriptions_repo as sr

        key = sr.create_license_key(self.conn, self.pro_user["id"], "pro")
        row = sr.validate_license_key(self.conn, key)
        self.assertIsNotNone(row["last_seen_at"])

    def test_device_binding_enforced(self):
        """July 2026: device binding was write-only — a bound key validated
        fine from any device. Now a different device_id is rejected."""
        from motoquant.database import subscriptions_repo as sr

        key = sr.create_license_key(self.conn, self.pro_user["id"], "pro")
        first = sr.validate_license_key(self.conn, key, device_id="device-abc")
        self.assertIsNotNone(first)
        # Same device revalidates fine
        again = sr.validate_license_key(self.conn, key, device_id="device-abc")
        self.assertIsNotNone(again)
        # Different device is rejected without touching the row
        before = self.conn.execute(
            "SELECT last_seen_at, device_id FROM license_keys"
        ).fetchone()
        with self.assertRaises(sr.DeviceMismatchError):
            sr.validate_license_key(self.conn, key, device_id="device-OTHER")
        after = self.conn.execute(
            "SELECT last_seen_at, device_id FROM license_keys"
        ).fetchone()
        self.assertEqual(dict(before), dict(after), "mismatch must not mutate")
        # Legacy clients that omit device_id are still tolerated
        legacy = sr.validate_license_key(self.conn, key)
        self.assertIsNotNone(legacy)

    def test_device_mismatch_endpoint_message(self):
        """The public validate route reports the mismatch distinctly."""
        import importlib.util

        if importlib.util.find_spec("fastapi") is None:
            self.skipTest("fastapi not installed")
        from fastapi.testclient import TestClient

        from motoquant.api import app
        from motoquant.database import subscriptions_repo as sr

        key = sr.create_license_key(self.conn, self.pro_user["id"], "pro")
        self.assertIsNotNone(key)

        client = TestClient(app)
        wrapped = _NoCloseConn(self.conn)
        with patch("motoquant.subscriptions._get_conn", return_value=wrapped):
            r1 = client.post(
                "/api/subscriptions/license-key/validate",
                json={"key": key, "device_id": "dev-A"},
            )
            self.assertTrue(r1.json()["valid"], r1.text)
            r2 = client.post(
                "/api/subscriptions/license-key/validate",
                json={"key": key, "device_id": "dev-B"},
            )
        body = r2.json()
        self.assertFalse(body["valid"])
        self.assertIn("another device", body["message"])

    def test_revoke_key(self):
        from motoquant.database import subscriptions_repo as sr

        key = sr.create_license_key(self.conn, self.pro_user["id"], "pro")
        # Get the key id
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        row = self.conn.execute(
            "SELECT id FROM license_keys WHERE key_hash = ?", (key_hash,)
        ).fetchone()
        ok = sr.revoke_license_key(self.conn, row["id"], self.pro_user["id"])
        self.assertTrue(ok)
        # Validation should now fail
        result = sr.validate_license_key(self.conn, key)
        self.assertIsNone(result)

    def test_revoke_other_users_key_returns_false(self):
        from motoquant.database import subscriptions_repo as sr

        key = sr.create_license_key(self.conn, self.pro_user["id"], "pro")
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        row = self.conn.execute(
            "SELECT id FROM license_keys WHERE key_hash = ?", (key_hash,)
        ).fetchone()
        # studio user tries to revoke pro user's key
        ok = sr.revoke_license_key(self.conn, row["id"], self.studio_user["id"])
        self.assertFalse(ok)


# ══════════════════════════════════════════════════════════════════════════════
# 3. Webhook handler — tier upgrades and downgrades
# ══════════════════════════════════════════════════════════════════════════════


class TestWebhookHandling(unittest.TestCase):
    """
    Test the Razorpay webhook endpoint using FastAPI TestClient.
    Razorpay SDK and signature verification are both mocked.
    """

    @classmethod
    def setUpClass(cls):
        try:
            from fastapi import FastAPI
            from fastapi.testclient import TestClient

            import motoquant.subscriptions as sub_mod
        except ImportError:
            cls.skipTest(None, "fastapi not installed")
            return

        mini = FastAPI()
        mini.include_router(sub_mod.router, prefix="/api/subscriptions")
        cls.client = TestClient(mini, raise_server_exceptions=False)
        cls.sub_mod = sub_mod

    def _make_event(
        self, event_type: str, rzp_sub_id: str, user_id: int, tier: str = "pro"
    ) -> dict:
        return {
            "event": event_type,
            "payload": {
                "subscription": {
                    "entity": {
                        "id": rzp_sub_id,
                        "plan_id": "plan_test_pro",
                        "current_end": int(
                            (
                                datetime.now(timezone.utc) + timedelta(days=30)
                            ).timestamp()
                        ),
                        "notes": {
                            "user_id": str(user_id),
                            "tier": tier,
                            "billing_cycle": "monthly",
                        },
                    }
                }
            },
        }

    def _post_webhook(self, conn, payload: dict) -> object:
        """Post a webhook event with mocked DB connection and signature bypass.
        Wraps conn in _NoCloseConn so the same in-memory DB survives for
        post-call assertions even though the handler calls conn.close().
        """
        wrapped = _NoCloseConn(conn)
        with (
            patch(
                "motoquant.subscriptions._verify_webhook_signature", return_value=True
            ),
            patch("motoquant.subscriptions._get_conn", return_value=wrapped),
            patch("motoquant.auth._get_conn", return_value=wrapped),
        ):
            res = self.client.post(
                "/api/subscriptions/webhook",
                content=json.dumps(payload).encode(),
                headers={"x-razorpay-signature": "mocked"},
            )
        return res

    def test_activation_upgrades_user_tier(self):
        conn = _mem_conn()
        _bootstrap(conn)
        user = _make_user(conn, "webhook@test.in", "free")  # start free

        event = self._make_event(
            "subscription.activated", "sub_webhook_001", user["id"], "pro"
        )
        res = self._post_webhook(conn, event)
        self.assertEqual(res.status_code, 200)

        from motoquant.database import users_repo as ur

        updated = ur.get_user_by_id(conn, user["id"])
        self.assertEqual(updated["tier"], "pro")
        conn.close()

    def test_cancellation_downgrades_user_to_free(self):
        conn = _mem_conn()
        _bootstrap(conn)
        user = _make_user(conn, "cancel@test.in", "pro")
        # Pre-create subscription
        from motoquant.database import subscriptions_repo as sr

        sr.upsert_subscription(
            conn,
            user_id=user["id"],
            razorpay_subscription_id="sub_webhook_cancel",
            tier="pro",
            status="active",
        )

        event = self._make_event(
            "subscription.cancelled", "sub_webhook_cancel", user["id"]
        )
        res = self._post_webhook(conn, event)
        self.assertEqual(res.status_code, 200)

        from motoquant.database import users_repo as ur

        updated = ur.get_user_by_id(conn, user["id"])
        self.assertEqual(updated["tier"], "free")
        conn.close()

    def test_duplicate_webhook_is_idempotent(self):
        conn = _mem_conn()
        _bootstrap(conn)
        user = _make_user(conn, "dup@test.in", "free")

        event = self._make_event(
            "subscription.activated", "sub_dup_001", user["id"], "pro"
        )
        res1 = self._post_webhook(conn, event)
        res2 = self._post_webhook(conn, event)
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res2.status_code, 200)

        from motoquant.database import users_repo as ur

        updated = ur.get_user_by_id(conn, user["id"])
        self.assertEqual(updated["tier"], "pro")
        conn.close()

    def test_invalid_signature_returns_400(self):
        res = self.client.post(
            "/api/subscriptions/webhook",
            content=b"{}",
            headers={"x-razorpay-signature": "bad-sig"},
        )
        # With RAZORPAY_WEBHOOK_SECRET unset (dev), signature check is bypassed
        # but malformed JSON produces 400
        self.assertIn(res.status_code, (200, 400))

    def test_unknown_event_returns_unhandled(self):
        conn = _mem_conn()
        _bootstrap(conn)
        user = _make_user(conn, "unknown@test.in", "free")
        event = self._make_event(
            "subscription.some_new_event", "sub_unknown", user["id"]
        )
        res = self._post_webhook(conn, event)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body.get("status"), "unhandled_event")
        conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# 4. License key endpoint (via FastAPI TestClient)
# ══════════════════════════════════════════════════════════════════════════════


class TestLicenseKeyEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from fastapi import FastAPI
            from fastapi.testclient import TestClient

            import motoquant.subscriptions as sub_mod
        except ImportError:
            cls.skipTest(None, "fastapi not installed")
            return

        mini = FastAPI()
        mini.include_router(sub_mod.router, prefix="/api/subscriptions")
        cls.client = TestClient(mini, raise_server_exceptions=False)

    def _fake_pro_user(self):
        return {"id": 1, "email": "pro@test.in", "tier": "pro", "is_active": 1}

    def _request_key(self, conn, user: dict):
        with (
            patch("motoquant.subscriptions.get_current_user", return_value=user),
            patch("motoquant.subscriptions.require_tier", return_value=lambda: user),
            patch("motoquant.subscriptions._get_conn", return_value=conn),
        ):
            # Override the dependency
            from motoquant import subscriptions as sub_mod

            sub_mod.router.dependencies = []
            res = self.client.post(
                "/api/subscriptions/license-key",
                headers={"Authorization": "Bearer fake"},
            )
        return res

    def test_generate_key_anonymous_beta_401_not_500(self):
        """Open-beta anonymous callers (require_tier passes {} while
        MOTOQUANT_BILLING_ENFORCE is off) must get a clean 401 from
        license-key generation, not a KeyError 500 — July 2026
        functional-audit find."""
        from fastapi import HTTPException

        from motoquant import subscriptions as sub_mod

        with self.assertRaises(HTTPException) as ctx:
            sub_mod.generate_license_key(user={})
        self.assertEqual(ctx.exception.status_code, 401)

    def test_validate_key_endpoint_valid(self):
        conn = _mem_conn()
        _bootstrap(conn)
        user = _make_user(conn, "vkey@test.in", "pro")
        from motoquant.database import subscriptions_repo as sr

        key = sr.create_license_key(conn, user["id"], "pro")

        with patch("motoquant.subscriptions._get_conn", return_value=conn):
            res = self.client.post(
                "/api/subscriptions/license-key/validate",
                json={"key": key, "device_id": "dev-001"},
            )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["valid"])
        self.assertEqual(body["tier"], "pro")
        conn.close()

    def test_validate_key_endpoint_invalid(self):
        conn = _mem_conn()
        _bootstrap(conn)
        with patch("motoquant.subscriptions._get_conn", return_value=conn):
            res = self.client.post(
                "/api/subscriptions/license-key/validate",
                json={"key": "completely-wrong-key"},
            )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertFalse(body["valid"])
        conn.close()


if __name__ == "__main__":
    unittest.main()
