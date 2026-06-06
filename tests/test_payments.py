"""
MotoQuant Pro — Payments layer tests
=====================================
Unified checkout, provider config, Stripe webhook lifecycle + signatures,
and the payment_events idempotency ledger.

Run with:
    python -m pytest tests/test_payments.py -v
"""

from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import time
import unittest
from unittest.mock import patch

# ─── helpers (mirror tests/test_auth.py conventions) ─────────────────────────


def _mem_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _bootstrap(conn: sqlite3.Connection):
    from motoquant.database.subscriptions_repo import ensure_tables as _s_tables
    from motoquant.database.users_repo import ensure_tables as _u_tables

    _u_tables(conn)
    _s_tables(conn)


class _NoCloseConn:
    def __init__(self, conn):
        self._conn = conn

    def close(self):
        pass

    def __getattr__(self, name):
        return getattr(self._conn, name)


def _stripe_sig(payload: bytes, secret: str, ts: int | None = None) -> str:
    ts = ts or int(time.time())
    mac = hmac.new(secret.encode(), f"{ts}.".encode() + payload, hashlib.sha256)
    return f"t={ts},v1={mac.hexdigest()}"


# ══════════════════════════════════════════════════════════════════════════════
# 1. Stripe signature verification (pure unit)
# ══════════════════════════════════════════════════════════════════════════════


class TestStripeSignature(unittest.TestCase):
    def setUp(self):
        from motoquant.payments import _verify_stripe_signature

        self.verify = _verify_stripe_signature
        self.payload = b'{"id":"evt_1","type":"ping"}'
        self.secret = "whsec_test"

    def test_valid_signature_passes(self):
        sig = _stripe_sig(self.payload, self.secret)
        self.assertTrue(self.verify(self.payload, sig, self.secret))

    def test_tampered_payload_fails(self):
        sig = _stripe_sig(self.payload, self.secret)
        self.assertFalse(self.verify(b'{"id":"evt_EVIL"}', sig, self.secret))

    def test_wrong_secret_fails(self):
        sig = _stripe_sig(self.payload, "whsec_other")
        self.assertFalse(self.verify(self.payload, sig, self.secret))

    def test_expired_timestamp_fails(self):
        sig = _stripe_sig(self.payload, self.secret, ts=int(time.time()) - 9999)
        self.assertFalse(self.verify(self.payload, sig, self.secret))

    def test_malformed_header_fails(self):
        self.assertFalse(self.verify(self.payload, "not-a-header", self.secret))
        self.assertFalse(self.verify(self.payload, "", self.secret))

    def test_missing_secret_skips_verification(self):
        # dev convenience — mirrors the Razorpay webhook behaviour
        self.assertTrue(self.verify(self.payload, "anything", ""))


# ══════════════════════════════════════════════════════════════════════════════
# 2. /api/payments/config
# ══════════════════════════════════════════════════════════════════════════════


def _make_app():
    from fastapi import FastAPI

    from motoquant.payments import router as payments_router

    app = FastAPI()
    app.include_router(payments_router, prefix="/api/payments")
    return app


class TestPaymentsConfig(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient

        cls.client = TestClient(_make_app(), raise_server_exceptions=False)

    def test_config_shape_and_beta_default(self):
        import motoquant.auth as auth_mod

        with patch.object(auth_mod, "BILLING_ENFORCE", False):
            res = self.client.get("/api/payments/config")
        self.assertEqual(res.status_code, 200)
        cfg = res.json()
        self.assertTrue(cfg["beta"])
        self.assertFalse(cfg["billing_enforced"])
        self.assertEqual(cfg["prices_inr"]["pro"]["monthly"], 499)
        self.assertEqual(cfg["prices_inr"]["studio"]["monthly"], 1999)
        self.assertEqual(set(cfg["providers"].keys()), {"razorpay", "stripe", "paypal"})
        self.assertIn("upi", cfg["providers"]["razorpay"]["methods"])
        self.assertEqual(cfg["providers"]["paypal"]["status"], "planned")

    def test_config_reflects_enforcement(self):
        import motoquant.auth as auth_mod

        with patch.object(auth_mod, "BILLING_ENFORCE", True):
            res = self.client.get("/api/payments/config")
        self.assertFalse(res.json()["beta"])
        self.assertTrue(res.json()["billing_enforced"])

    def test_stripe_configured_flag_follows_env(self):
        with patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_x"}):
            res = self.client.get("/api/payments/config")
        self.assertTrue(res.json()["providers"]["stripe"]["configured"])
        self.assertTrue(res.json()["checkout_available"])


# ══════════════════════════════════════════════════════════════════════════════
# 3. Unified checkout routing
# ══════════════════════════════════════════════════════════════════════════════


class TestUnifiedCheckout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient

        from motoquant.auth import get_current_user

        cls.app = _make_app()
        cls.app.dependency_overrides[get_current_user] = lambda: {
            "id": 1,
            "email": "rider@test.in",
            "tier": "free",
        }
        cls.client = TestClient(cls.app, raise_server_exceptions=False)

    def _post(self, body):
        return self.client.post("/api/payments/checkout", json=body)

    def test_invalid_tier_400(self):
        res = self._post({"tier": "platinum"})
        self.assertEqual(res.status_code, 400)

    def test_invalid_provider_400(self):
        res = self._post({"tier": "pro", "provider": "bitcoin"})
        self.assertEqual(res.status_code, 400)

    def test_auto_with_nothing_configured_503_beta_message(self):
        res = self._post({"tier": "pro"})
        self.assertEqual(res.status_code, 503)
        self.assertIn("beta", res.json()["detail"])

    def test_stripe_without_price_id_503(self):
        with patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_x"}):
            res = self._post({"tier": "pro", "provider": "stripe"})
        self.assertEqual(res.status_code, 503)
        self.assertIn("price not configured", res.json()["detail"])

    def test_paypal_503_planned(self):
        res = self._post({"tier": "pro", "provider": "paypal"})
        self.assertEqual(res.status_code, 503)
        self.assertIn("planned", res.json()["detail"])

    def test_checkout_requires_auth(self):
        from fastapi.testclient import TestClient

        bare = TestClient(_make_app(), raise_server_exceptions=False)
        res = bare.post("/api/payments/checkout", json={"tier": "pro"})
        self.assertEqual(res.status_code, 401)


# ══════════════════════════════════════════════════════════════════════════════
# 4. Stripe webhook lifecycle (in-memory DB end-to-end)
# ══════════════════════════════════════════════════════════════════════════════


class TestStripeWebhook(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient

        cls.client = TestClient(_make_app(), raise_server_exceptions=False)

    def setUp(self):
        from motoquant.database import users_repo

        self.conn = _mem_conn()
        _bootstrap(self.conn)
        self.user = users_repo.get_or_create_user(self.conn, "stripe@test.in")
        self._patcher = patch(
            "motoquant.payments._get_conn", return_value=_NoCloseConn(self.conn)
        )
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()
        self.conn.close()

    def _send(self, event: dict):
        return self.client.post(
            "/api/payments/webhook/stripe", content=json.dumps(event)
        )

    def _checkout_completed(self, event_id="evt_1", sub_id="sub_abc"):
        return {
            "id": event_id,
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_1",
                    "subscription": sub_id,
                    "customer": "cus_42",
                    "client_reference_id": str(self.user["id"]),
                    "metadata": {
                        "user_id": str(self.user["id"]),
                        "tier": "pro",
                        "billing_cycle": "monthly",
                    },
                }
            },
        }

    def test_checkout_completed_upgrades_tier(self):
        from motoquant.database import users_repo

        res = self._send(self._checkout_completed())
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "ok")
        user = users_repo.get_user_by_id(self.conn, self.user["id"])
        self.assertEqual(user["tier"], "pro")
        self.assertEqual(user["stripe_customer_id"], "cus_42")
        row = self.conn.execute(
            "SELECT * FROM subscriptions WHERE razorpay_subscription_id='sub_abc'"
        ).fetchone()
        self.assertEqual(row["provider"], "stripe")
        self.assertEqual(row["status"], "active")

    def test_duplicate_event_is_idempotent(self):
        self._send(self._checkout_completed())
        res = self._send(self._checkout_completed())
        self.assertEqual(res.json()["status"], "duplicate")

    def test_subscription_deleted_downgrades(self):
        from motoquant.database import users_repo

        self._send(self._checkout_completed())
        res = self._send(
            {
                "id": "evt_2",
                "type": "customer.subscription.deleted",
                "data": {"object": {"id": "sub_abc", "status": "canceled"}},
            }
        )
        self.assertEqual(res.json()["status"], "ok")
        user = users_repo.get_user_by_id(self.conn, self.user["id"])
        self.assertEqual(user["tier"], "free")

    def test_payment_failed_marks_past_due(self):
        self._send(self._checkout_completed())
        res = self._send(
            {
                "id": "evt_3",
                "type": "invoice.payment_failed",
                "data": {"object": {"subscription": "sub_abc"}},
            }
        )
        self.assertEqual(res.json()["status"], "ok")
        row = self.conn.execute(
            "SELECT status FROM subscriptions WHERE razorpay_subscription_id='sub_abc'"
        ).fetchone()
        self.assertEqual(row["status"], "past_due")

    def test_unresolvable_user_reported(self):
        res = self._send(
            {
                "id": "evt_4",
                "type": "checkout.session.completed",
                "data": {"object": {"id": "cs_x", "metadata": {}}},
            }
        )
        self.assertEqual(res.json()["status"], "user_not_found")

    def test_unhandled_event_acknowledged(self):
        res = self._send(
            {"id": "evt_5", "type": "customer.created", "data": {"object": {}}}
        )
        self.assertEqual(res.json()["status"], "unhandled_event")

    def test_malformed_json_400(self):
        res = self.client.post("/api/payments/webhook/stripe", content="not-json{")
        self.assertEqual(res.status_code, 400)

    def test_bad_signature_400_when_secret_set(self):
        body = json.dumps(self._checkout_completed("evt_6"))
        with patch.dict("os.environ", {"STRIPE_WEBHOOK_SECRET": "whsec_x"}):
            res = self.client.post(
                "/api/payments/webhook/stripe",
                content=body,
                headers={"stripe-signature": "t=1,v1=bad"},
            )
        self.assertEqual(res.status_code, 400)

    def test_good_signature_passes_when_secret_set(self):
        body = json.dumps(self._checkout_completed("evt_7")).encode()
        with patch.dict("os.environ", {"STRIPE_WEBHOOK_SECRET": "whsec_x"}):
            res = self.client.post(
                "/api/payments/webhook/stripe",
                content=body,
                headers={"stripe-signature": _stripe_sig(body, "whsec_x")},
            )
        self.assertEqual(res.status_code, 200)

    def test_paypal_webhook_501(self):
        res = self.client.post("/api/payments/webhook/paypal", content="{}")
        self.assertEqual(res.status_code, 501)


# ══════════════════════════════════════════════════════════════════════════════
# 5. payment_events ledger (repo-level)
# ══════════════════════════════════════════════════════════════════════════════


class TestPaymentEventLedger(unittest.TestCase):
    def setUp(self):
        self.conn = _mem_conn()
        _bootstrap(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_first_event_recorded(self):
        from motoquant.database import subscriptions_repo as subs

        self.assertTrue(
            subs.record_payment_event(self.conn, "stripe", "evt_a", "ping", "{}")
        )

    def test_duplicate_event_rejected(self):
        from motoquant.database import subscriptions_repo as subs

        subs.record_payment_event(self.conn, "stripe", "evt_a", "ping", "{}")
        self.assertFalse(
            subs.record_payment_event(self.conn, "stripe", "evt_a", "ping", "{}")
        )

    def test_same_event_id_different_provider_ok(self):
        from motoquant.database import subscriptions_repo as subs

        subs.record_payment_event(self.conn, "stripe", "evt_a", "ping", "{}")
        self.assertTrue(
            subs.record_payment_event(self.conn, "razorpay", "evt_a", "ping", "{}")
        )


if __name__ == "__main__":
    unittest.main()
