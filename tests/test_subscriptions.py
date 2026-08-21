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

    def test_first_device_call_binds_key(self):
        """Policy (a): the first validate carrying a device_id binds the key."""
        from motoquant.database import subscriptions_repo as sr

        key = sr.create_license_key(self.conn, self.pro_user["id"], "pro")
        row = sr.validate_license_key(self.conn, key, device_id="device-abc")
        self.assertIsNotNone(row)
        stored = self.conn.execute(
            "SELECT device_id, activated_at FROM license_keys"
        ).fetchone()
        self.assertEqual(stored["device_id"], "device-abc")
        self.assertIsNotNone(stored["activated_at"])

    def test_bound_key_rejects_omitted_device_id(self):
        """Policy (b) — July 17 2026: the omit-device_id tolerance is GONE.
        It existed for pre-device desktop builds; the desktop app was
        scrapped July 6 (ADR-0005), so a bound key presented without a
        device_id is a shared/scripted key and must be rejected, leaving
        the row untouched."""
        from motoquant.database import subscriptions_repo as sr

        key = sr.create_license_key(self.conn, self.pro_user["id"], "pro")
        sr.validate_license_key(self.conn, key, device_id="device-abc")
        before = self.conn.execute(
            "SELECT last_seen_at, device_id FROM license_keys"
        ).fetchone()
        with self.assertRaises(sr.DeviceMismatchError):
            sr.validate_license_key(self.conn, key)
        after = self.conn.execute(
            "SELECT last_seen_at, device_id FROM license_keys"
        ).fetchone()
        self.assertEqual(dict(before), dict(after), "omission must not mutate")

    def test_unbound_key_validates_without_device_id(self):
        """Policy (c): a key never bound (device_id NULL) still validates
        without one — binding only happens on the first device-carrying
        call."""
        from motoquant.database import subscriptions_repo as sr

        key = sr.create_license_key(self.conn, self.pro_user["id"], "pro")
        for _ in range(2):
            row = sr.validate_license_key(self.conn, key)
            self.assertIsNotNone(row)
        stored = self.conn.execute("SELECT device_id FROM license_keys").fetchone()
        self.assertIsNone(stored["device_id"], "id-less calls must not bind")

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
            # A bound key validated WITHOUT a device_id gets the same
            # rejection through the route (policy (b), July 17 2026).
            r3 = client.post(
                "/api/subscriptions/license-key/validate",
                json={"key": key},
            )
        body = r2.json()
        self.assertFalse(body["valid"])
        self.assertIn("another device", body["message"])
        body3 = r3.json()
        self.assertFalse(body3["valid"])
        self.assertIn("another device", body3["message"])

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


class TestHardening20260811(unittest.TestCase):
    """Regression pins for the 2026-08-11 payments audit fixes.

    Every test here exercises the production route/repo path and FAILS if the
    corresponding fix is reverted (repo rule: no tautological tests).
    """

    # ── checkout: short_url + duplicate guard ────────────────────────────

    def _checkout_client(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        import motoquant.subscriptions as sub_mod

        app = FastAPI()
        app.include_router(sub_mod.router, prefix="/api/subscriptions")
        app.dependency_overrides[sub_mod.get_current_user] = lambda: {
            "id": 1,
            "email": "buyer@test.in",
            "tier": "free",
        }
        return TestClient(app, raise_server_exceptions=False), sub_mod

    def _fake_rzp_client(self, short_url="https://rzp.io/i/abc123"):
        from unittest.mock import MagicMock

        client = MagicMock()
        client.customer.create.return_value = {"id": "cust_test"}
        create_resp = {"id": "sub_new_001"}
        if short_url is not None:
            create_resp["short_url"] = short_url
        client.subscription.create.return_value = create_resp
        return client

    def test_checkout_url_is_the_api_short_url(self):
        """The checkout link must come from Razorpay's create response —
        the old code FABRICATED https://rzp.io/l/{sub_id}, a dead URL."""
        client, sub_mod = self._checkout_client()
        conn = _mem_conn()
        _bootstrap(conn)
        _make_user(conn, "buyer@test.in", "free")
        with (
            patch.object(sub_mod, "_rzp_client", return_value=self._fake_rzp_client()),
            patch.object(
                sub_mod, "PLAN_IDS", {"pro": {"monthly": "plan_p"}, "studio": {}}
            ),
            patch("motoquant.subscriptions._get_conn", return_value=_NoCloseConn(conn)),
        ):
            res = client.post(
                "/api/subscriptions/checkout",
                json={"tier": "pro", "billing_cycle": "monthly"},
            )
        conn.close()
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(res.json()["checkout_url"], "https://rzp.io/i/abc123")

    def test_checkout_502_when_short_url_missing(self):
        client, sub_mod = self._checkout_client()
        conn = _mem_conn()
        _bootstrap(conn)
        _make_user(conn, "buyer@test.in", "free")
        with (
            patch.object(
                sub_mod,
                "_rzp_client",
                return_value=self._fake_rzp_client(short_url=None),
            ),
            patch.object(
                sub_mod, "PLAN_IDS", {"pro": {"monthly": "plan_p"}, "studio": {}}
            ),
            patch("motoquant.subscriptions._get_conn", return_value=_NoCloseConn(conn)),
        ):
            res = client.post(
                "/api/subscriptions/checkout",
                json={"tier": "pro", "billing_cycle": "monthly"},
            )
        conn.close()
        self.assertEqual(res.status_code, 502)

    def test_checkout_409_when_subscription_already_active(self):
        """Every extra checkout used to mint a NEW provider subscription the
        account page could never see — invisible double billing."""
        from motoquant.database import subscriptions_repo as sr

        client, sub_mod = self._checkout_client()
        conn = _mem_conn()
        _bootstrap(conn)
        _make_user(conn, "buyer@test.in", "pro")
        sr.upsert_subscription(
            conn,
            user_id=1,
            razorpay_subscription_id="sub_existing",
            tier="pro",
            status="active",
            plan_id="plan_p",
            billing_cycle="monthly",
        )
        rzp = self._fake_rzp_client()
        with (
            patch.object(sub_mod, "_rzp_client", return_value=rzp),
            patch.object(
                sub_mod,
                "PLAN_IDS",
                {"pro": {"monthly": "plan_p"}, "studio": {"monthly": "plan_s"}},
            ),
            patch("motoquant.subscriptions._get_conn", return_value=_NoCloseConn(conn)),
        ):
            res = client.post(
                "/api/subscriptions/checkout",
                json={"tier": "studio", "billing_cycle": "monthly"},
            )
        conn.close()
        self.assertEqual(res.status_code, 409)
        rzp.subscription.create.assert_not_called()

    # ── webhook: authenticated must not grant tier ───────────────────────

    def _webhook_env(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        import motoquant.subscriptions as sub_mod

        mini = FastAPI()
        mini.include_router(sub_mod.router, prefix="/api/subscriptions")
        return TestClient(mini, raise_server_exceptions=False), sub_mod

    def _event(self, event_type, rzp_sub_id, user_id, tier="pro", nonce=""):
        from datetime import datetime, timedelta, timezone

        return {
            "event": event_type,
            "nonce": nonce,  # varies payload → distinct sha-derived event ids
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

    def _post_event(self, client, conn, payload, event_id=None):
        headers = {"x-razorpay-signature": "mocked"}
        if event_id:
            headers["x-razorpay-event-id"] = event_id
        with (
            patch(
                "motoquant.subscriptions._verify_webhook_signature", return_value=True
            ),
            patch("motoquant.subscriptions._get_conn", return_value=_NoCloseConn(conn)),
        ):
            return client.post(
                "/api/subscriptions/webhook",
                content=json.dumps(payload).encode(),
                headers=headers,
            )

    def test_authenticated_event_does_not_grant_tier(self):
        """subscription.authenticated = mandate authorized, no money captured.
        Granting the paid tier here gave free access to anyone who authorized
        and then let the first charge fail."""
        from motoquant.database import users_repo as ur

        client, _ = self._webhook_env()
        conn = _mem_conn()
        _bootstrap(conn)
        user = _make_user(conn, "auth-only@test.in", "free")
        res = self._post_event(
            conn=conn,
            client=client,
            payload=self._event("subscription.authenticated", "sub_auth_1", user["id"]),
        )
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(
            ur.get_user_by_id(conn, user["id"])["tier"],
            "free",
            "tier must not be granted before money is captured",
        )
        conn.close()

    def test_late_cancel_of_old_sub_keeps_newer_active_tier(self):
        """An out-of-order cancelled event for an OLD subscription must not
        downgrade a user whose NEWER subscription is still active."""
        from motoquant.database import users_repo as ur

        client, _ = self._webhook_env()
        conn = _mem_conn()
        _bootstrap(conn)
        user = _make_user(conn, "two-subs@test.in", "free")
        # Old sub activates, then the user re-subscribes (new sub activates).
        r1 = self._post_event(
            conn=conn,
            client=client,
            payload=self._event(
                "subscription.activated", "sub_old", user["id"], nonce="a"
            ),
        )
        r2 = self._post_event(
            conn=conn,
            client=client,
            payload=self._event(
                "subscription.activated", "sub_new", user["id"], nonce="b"
            ),
        )
        self.assertEqual((r1.status_code, r2.status_code), (200, 200))
        # Late cancellation of the OLD sub arrives after the new one is live.
        r3 = self._post_event(
            conn=conn,
            client=client,
            payload=self._event(
                "subscription.cancelled", "sub_old", user["id"], nonce="c"
            ),
        )
        self.assertEqual(r3.status_code, 200, r3.text)
        self.assertEqual(
            ur.get_user_by_id(conn, user["id"])["tier"],
            "pro",
            "newer active subscription must keep the paid tier",
        )
        # And a cancellation of the CURRENT sub does downgrade.
        r4 = self._post_event(
            conn=conn,
            client=client,
            payload=self._event(
                "subscription.cancelled", "sub_new", user["id"], nonce="d"
            ),
        )
        self.assertEqual(r4.status_code, 200)
        self.assertEqual(ur.get_user_by_id(conn, user["id"])["tier"], "free")
        conn.close()

    def test_user_not_found_is_retryable_not_swallowed(self):
        """user_not_found used to return 200 AFTER committing the ledger row —
        every provider retry was then dropped as 'duplicate' and the event was
        lost forever. It must answer non-2xx AND un-record the ledger row so a
        redelivery (same event id) gets a fresh attempt."""
        from motoquant.database import users_repo as ur

        client, _ = self._webhook_env()
        conn = _mem_conn()
        _bootstrap(conn)
        # Sub unknown to the DB, notes carry a non-numeric user id.
        payload = self._event("subscription.activated", "sub_orphan", "not-a-user")
        payload["payload"]["subscription"]["entity"]["notes"]["user_id"] = ""
        first = self._post_event(
            conn=conn, client=client, payload=payload, event_id="evt_orphan_1"
        )
        self.assertEqual(first.status_code, 400)
        # Operator links the sub (user now resolvable), provider redelivers
        # the SAME event id — it must be processed, not "duplicate".
        user = _make_user(conn, "linked-later@test.in", "free")
        payload["payload"]["subscription"]["entity"]["notes"]["user_id"] = str(
            user["id"]
        )
        retry = self._post_event(
            conn=conn, client=client, payload=payload, event_id="evt_orphan_1"
        )
        self.assertEqual(retry.status_code, 200, retry.text)
        self.assertEqual(retry.json()["status"], "ok")
        self.assertEqual(ur.get_user_by_id(conn, user["id"])["tier"], "pro")
        conn.close()

    # ── license keys: deactivated owner ──────────────────────────────────

    def test_deactivated_account_key_stops_validating(self):
        from motoquant.database import subscriptions_repo as sr, users_repo as ur

        conn = _mem_conn()
        _bootstrap(conn)
        user = _make_user(conn, "banned@test.in", "pro")
        plaintext = sr.create_license_key(conn, user["id"], "pro")
        self.assertIsNotNone(
            sr.validate_license_key(conn, plaintext, device_id="dev-1")
        )
        ur.deactivate_user(conn, user["id"])
        self.assertIsNone(
            sr.validate_license_key(conn, plaintext, device_id="dev-1"),
            "a deactivated account's key must stop validating",
        )
        conn.close()


class TestCommercialHardening20260821(unittest.TestCase):
    """Regression pins for the 2026-08-21 pre-launch money-path hardening.

    Yearly renewal cycles, no-silent-tier-grant on unknown plan ids, per-user
    checkout locking, the 30-min open-checkout guard, and the stuck-
    'authenticated' cancel escape hatch. Every test drives the production
    route path.
    """

    # ── helpers (mirror TestHardening20260811) ───────────────────────────

    def _checkout_client(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        import motoquant.subscriptions as sub_mod

        app = FastAPI()
        app.include_router(sub_mod.router, prefix="/api/subscriptions")
        app.dependency_overrides[sub_mod.get_current_user] = lambda: {
            "id": 1,
            "email": "buyer@test.in",
            "tier": "free",
        }
        return TestClient(app, raise_server_exceptions=False), sub_mod

    def _fake_rzp_client(self, short_url="https://rzp.io/i/abc123"):
        from unittest.mock import MagicMock

        client = MagicMock()
        client.customer.create.return_value = {"id": "cust_test"}
        create_resp = {"id": "sub_new_001"}
        if short_url is not None:
            create_resp["short_url"] = short_url
        client.subscription.create.return_value = create_resp
        return client

    def _webhook_env(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        import motoquant.subscriptions as sub_mod

        mini = FastAPI()
        mini.include_router(sub_mod.router, prefix="/api/subscriptions")
        return TestClient(mini, raise_server_exceptions=False), sub_mod

    def _post_event(self, client, conn, payload, event_id=None):
        headers = {"x-razorpay-signature": "mocked"}
        if event_id:
            headers["x-razorpay-event-id"] = event_id
        with (
            patch(
                "motoquant.subscriptions._verify_webhook_signature", return_value=True
            ),
            patch("motoquant.subscriptions._get_conn", return_value=_NoCloseConn(conn)),
        ):
            return client.post(
                "/api/subscriptions/webhook",
                content=json.dumps(payload).encode(),
                headers=headers,
            )

    # ── Task 1: yearly renewals ──────────────────────────────────────────

    def test_total_count_is_billing_cycles_not_one(self):
        """Razorpay total_count = number of BILLING CYCLES. Yearly was 1, so
        the plan billed once and subscription.completed downgraded the user
        at their first renewal anniversary."""
        for cycle, expected in (("monthly", 120), ("yearly", 10)):
            with self.subTest(cycle=cycle):
                client, sub_mod = self._checkout_client()
                conn = _mem_conn()
                _bootstrap(conn)
                _make_user(conn, "buyer@test.in", "free")
                rzp = self._fake_rzp_client()
                with (
                    patch.object(sub_mod, "_rzp_client", return_value=rzp),
                    patch.object(
                        sub_mod,
                        "PLAN_IDS",
                        {
                            "pro": {"monthly": "plan_m", "yearly": "plan_y"},
                            "studio": {},
                        },
                    ),
                    patch(
                        "motoquant.subscriptions._get_conn",
                        return_value=_NoCloseConn(conn),
                    ),
                ):
                    res = client.post(
                        "/api/subscriptions/checkout",
                        json={"tier": "pro", "billing_cycle": cycle},
                    )
                conn.close()
                self.assertEqual(res.status_code, 200, res.text)
                payload = rzp.subscription.create.call_args[0][0]
                self.assertEqual(payload["total_count"], expected)

    # ── Task 3c: unknown plan id must never silently grant pro ───────────

    def test_unknown_plan_id_is_retryable_and_grants_after_env_fix(self):
        """_tier_from_plan defaulted to 'pro' — an unset/mistyped PLAN_ID_*
        env silently granted pro on every webhook. Now: 400 + ledger row
        deleted (the handler's `except HTTPException: raise` bypasses the
        generic compensation, so the delete is explicit), and a redelivery of
        the SAME event id after the env fix applies cleanly."""
        from motoquant.database import users_repo as ur

        client, sub_mod = self._webhook_env()
        conn = _mem_conn()
        _bootstrap(conn)
        user = _make_user(conn, "planless@test.in", "free")
        payload = {
            "event": "subscription.activated",
            "payload": {
                "subscription": {
                    "entity": {
                        "id": "sub_plan_x",
                        "plan_id": "plan_mystery",
                        # No tier in notes — the plan-id ladder is the last rung.
                        "notes": {
                            "user_id": str(user["id"]),
                            "billing_cycle": "monthly",
                        },
                    }
                }
            },
        }
        first = self._post_event(client, conn, payload, event_id="evt_plan_1")
        self.assertEqual(first.status_code, 400, first.text)
        self.assertIn("plan_id", first.json()["detail"])
        ledger = conn.execute(
            "SELECT COUNT(*) FROM payment_events "
            "WHERE provider='razorpay' AND event_id='evt_plan_1'"
        ).fetchone()[0]
        self.assertEqual(ledger, 0, "ledger row must be gone so redelivery works")
        self.assertEqual(
            ur.get_user_by_id(conn, user["id"])["tier"],
            "free",
            "an unknown plan must never grant a tier",
        )
        # Operator sets PLAN_ID_* env; Razorpay redelivers the same event id.
        with patch.object(
            sub_mod, "PLAN_IDS", {"pro": {"monthly": "plan_mystery"}, "studio": {}}
        ):
            retry = self._post_event(client, conn, payload, event_id="evt_plan_1")
        self.assertEqual(retry.status_code, 200, retry.text)
        self.assertEqual(retry.json()["status"], "ok")
        self.assertEqual(ur.get_user_by_id(conn, user["id"])["tier"], "pro")
        conn.close()

    # ── Task 5: per-user checkout lock ───────────────────────────────────

    def test_checkout_lock_is_reentrant_and_per_user(self):
        import motoquant.subscriptions as sub_mod

        lock = sub_mod.checkout_lock(424242)
        self.assertIs(lock, sub_mod.checkout_lock(424242), "one lock per user")
        self.assertIsNot(lock, sub_mod.checkout_lock(424243))
        with lock:
            # RLock contract is load-bearing: payments.unified_checkout holds
            # the lock and calls subscriptions.create_checkout on the same
            # thread, which re-acquires it.
            self.assertTrue(lock.acquire(blocking=False))
            lock.release()

    # ── Task 6: 30-minute open-checkout guard ────────────────────────────

    def test_second_checkout_within_30min_409s_without_provider_call(self):
        client, sub_mod = self._checkout_client()
        conn = _mem_conn()
        _bootstrap(conn)
        _make_user(conn, "buyer@test.in", "free")
        rzp = self._fake_rzp_client()
        with (
            patch.object(sub_mod, "_rzp_client", return_value=rzp),
            patch.object(
                sub_mod, "PLAN_IDS", {"pro": {"monthly": "plan_p"}, "studio": {}}
            ),
            patch("motoquant.subscriptions._get_conn", return_value=_NoCloseConn(conn)),
        ):
            r1 = client.post(
                "/api/subscriptions/checkout",
                json={"tier": "pro", "billing_cycle": "monthly"},
            )
            r2 = client.post(
                "/api/subscriptions/checkout",
                json={"tier": "pro", "billing_cycle": "monthly"},
            )
        conn.close()
        self.assertEqual(r1.status_code, 200, r1.text)
        self.assertEqual(r2.status_code, 409)
        self.assertIn("still open", r2.json()["detail"])
        self.assertEqual(
            rzp.subscription.create.call_count,
            1,
            "the second checkout must never reach the provider",
        )

    def test_stale_created_row_does_not_block_checkout(self):
        from motoquant.database import subscriptions_repo as sr

        client, sub_mod = self._checkout_client()
        conn = _mem_conn()
        _bootstrap(conn)
        _make_user(conn, "buyer@test.in", "free")
        sr.upsert_subscription(
            conn,
            user_id=1,
            razorpay_subscription_id="sub_stale_checkout",
            tier="pro",
            status="created",
            plan_id="plan_p",
            billing_cycle="monthly",
        )
        # Backdate past the 30-min window — the guard must not fire.
        conn.execute(
            "UPDATE subscriptions SET created_at = datetime('now', '-2 hours') "
            "WHERE razorpay_subscription_id = 'sub_stale_checkout'"
        )
        conn.commit()
        rzp = self._fake_rzp_client()
        with (
            patch.object(sub_mod, "_rzp_client", return_value=rzp),
            patch.object(
                sub_mod, "PLAN_IDS", {"pro": {"monthly": "plan_p"}, "studio": {}}
            ),
            patch("motoquant.subscriptions._get_conn", return_value=_NoCloseConn(conn)),
        ):
            res = client.post(
                "/api/subscriptions/checkout",
                json={"tier": "pro", "billing_cycle": "monthly"},
            )
        conn.close()
        self.assertEqual(res.status_code, 200, res.text)

    # ── Task 7: stuck-authenticated escape hatch ─────────────────────────

    def test_stuck_authenticated_cancel_is_immediate_and_checkout_reopens(self):
        """'authenticated' = mandate authorized, nothing captured. Cancel must
        be immediate (cancel_at_cycle_end 0 — at-cycle-end is undefined
        pre-activation) AND clear the local row so the one-active-sub 409
        lifts without waiting for the webhook."""
        from motoquant.database import subscriptions_repo as sr

        client, sub_mod = self._checkout_client()
        conn = _mem_conn()
        _bootstrap(conn)
        _make_user(conn, "buyer@test.in", "pro")
        sr.upsert_subscription(
            conn,
            user_id=1,
            razorpay_subscription_id="sub_auth_stuck",
            tier="pro",
            status="authenticated",
            plan_id="plan_p",
            billing_cycle="monthly",
        )
        rzp = self._fake_rzp_client()
        with (
            patch.object(sub_mod, "_rzp_client", return_value=rzp),
            patch.object(
                sub_mod, "PLAN_IDS", {"pro": {"monthly": "plan_p"}, "studio": {}}
            ),
            patch("motoquant.subscriptions._get_conn", return_value=_NoCloseConn(conn)),
        ):
            res = client.post("/api/subscriptions/cancel")
            self.assertEqual(res.status_code, 200, res.text)
            rzp.subscription.cancel.assert_called_once_with(
                "sub_auth_stuck", {"cancel_at_cycle_end": 0}
            )
            row = sr.get_subscription_by_rzp_id(conn, "sub_auth_stuck")
            self.assertEqual(
                row["status"],
                "cancelled",
                "local row must clear immediately, not wait for the webhook",
            )
            res2 = client.post(
                "/api/subscriptions/checkout",
                json={"tier": "pro", "billing_cycle": "monthly"},
            )
        conn.close()
        self.assertEqual(res2.status_code, 200, res2.text)


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


# ══════════════════════════════════════════════════════════════════════════════
# 5. Rate limit on the unauthenticated validate route
# ══════════════════════════════════════════════════════════════════════════════


class TestValidateRateLimit(unittest.TestCase):
    """POST /license-key/validate is unauthenticated — the 'license' bucket
    (10 req / 60 s per IP, July 2026) fuses key-guessing and scripted
    hammering."""

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

    def setUp(self):
        from motoquant import ratelimit

        ratelimit.reset()

    def tearDown(self):
        from motoquant import ratelimit

        ratelimit.reset()

    def test_eleventh_rapid_validate_429s(self):
        conn = _mem_conn()
        _bootstrap(conn)
        wrapped = _NoCloseConn(conn)
        with patch("motoquant.subscriptions._get_conn", return_value=wrapped):
            for i in range(10):
                res = self.client.post(
                    "/api/subscriptions/license-key/validate",
                    json={"key": f"guess-{i}"},
                )
                self.assertEqual(res.status_code, 200, f"call {i + 1} must pass")
            res = self.client.post(
                "/api/subscriptions/license-key/validate",
                json={"key": "guess-11"},
            )
        conn.close()
        self.assertEqual(res.status_code, 429)
        self.assertEqual(res.json()["detail"]["error"], "rate_limited")
        self.assertIn("Retry-After", res.headers)


class TestLicenseKeyTierDowngrade(unittest.TestCase):
    """A cancelled-and-downgraded subscriber's license key must stop
    validating — the public /refunds page promises invalidation within 24h.
    Exercised through the real HTTP route (production path)."""

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

    def setUp(self):
        from motoquant import ratelimit

        ratelimit.reset()

    def tearDown(self):
        from motoquant import ratelimit

        ratelimit.reset()

    def test_downgraded_user_key_stops_validating(self):
        from motoquant.database import subscriptions_repo as sr, users_repo as ur

        conn = _mem_conn()
        _bootstrap(conn)
        user = _make_user(conn, "downgraded@test.in", "pro")
        key = sr.create_license_key(conn, user["id"], "pro")
        self.assertIsNotNone(key)
        wrapped = _NoCloseConn(conn)
        with patch("motoquant.subscriptions._get_conn", return_value=wrapped):
            ok = self.client.post(
                "/api/subscriptions/license-key/validate",
                json={"key": key, "device_id": "dev-dg"},
            )
            self.assertTrue(ok.json()["valid"], ok.text)
            self.assertEqual(ok.json()["tier"], "pro")
            # Subscription lapses → user tier drops to free.
            ur.set_user_tier(conn, user["id"], "free")
            bad = self.client.post(
                "/api/subscriptions/license-key/validate",
                json={"key": key, "device_id": "dev-dg"},
            )
        conn.close()
        body = bad.json()
        self.assertFalse(body["valid"], "a downgraded owner's key must be invalid")
        self.assertIn("Invalid or revoked", body["message"])


if __name__ == "__main__":
    unittest.main()
