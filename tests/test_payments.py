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

    def test_missing_secret_fails_closed(self):
        # 2026-07-02 security fix: an unset webhook secret must REJECT every
        # event (fail closed), not accept them — otherwise forged events can
        # upgrade any account for free while checkout is live but the secret
        # is unconfigured.
        self.assertFalse(self.verify(self.payload, "anything", ""))


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

    def setUp(self):
        # The duplicate-subscription guard reads the subscriptions table, so
        # every checkout request now touches a DB — pin it to an in-memory one
        # (the route must NEVER reach the tracked motoquant.db from tests).
        self.conn = _mem_conn()
        _bootstrap(self.conn)
        self._patcher = patch(
            "motoquant.payments._get_conn", return_value=_NoCloseConn(self.conn)
        )
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()
        self.conn.close()

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

    def test_active_subscription_blocks_second_checkout(self):
        """2026-08-11 audit: every extra checkout minted a NEW provider
        subscription while /status and /cancel only ever saw the newest row —
        the older ones kept billing invisibly. A user with an active sub must
        get a 409 pointing at cancel-first, before any provider is called."""
        from motoquant.database import subscriptions_repo as sr

        sr.upsert_subscription(
            self.conn,
            user_id=1,
            razorpay_subscription_id="sub_active_dup",
            tier="pro",
            status="active",
            plan_id="plan_x",
            billing_cycle="monthly",
        )
        with patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_x"}):
            res = self._post({"tier": "studio", "provider": "stripe"})
        self.assertEqual(res.status_code, 409)
        self.assertIn("already have an active pro subscription", res.json()["detail"])


class TestStripeCancel(unittest.TestCase):
    """The /api/subscriptions/cancel route must route by provider — it was
    hardwired to the Razorpay SDK, so Stripe subscribers could not cancel at
    all (their Stripe sub id was fed to Razorpay). 2026-08-11 audit."""

    def _mini(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        import motoquant.subscriptions as sub_mod

        app = FastAPI()
        app.include_router(sub_mod.router, prefix="/api/subscriptions")
        app.dependency_overrides[sub_mod.get_current_user] = lambda: {
            "id": 1,
            "email": "s@test.in",
            "tier": "pro",
        }
        return TestClient(app, raise_server_exceptions=False), sub_mod

    def test_stripe_subscription_cancels_via_stripe(self):
        from motoquant.database import subscriptions_repo as sr

        conn = _mem_conn()
        _bootstrap(conn)
        sr.upsert_subscription(
            conn,
            user_id=1,
            razorpay_subscription_id="sub_stripe_123",
            tier="pro",
            status="active",
            plan_id="price_x",
            billing_cycle="monthly",
            provider="stripe",
        )
        client, sub_mod = self._mini()
        stripe_calls = []
        with (
            patch(
                "motoquant.subscriptions._get_conn",
                return_value=_NoCloseConn(conn),
            ),
            patch(
                "motoquant.payments.stripe_cancel_subscription",
                side_effect=lambda sid: stripe_calls.append(sid),
            ),
            # The Razorpay SDK must NOT be touched on the Stripe path — a
            # call here means the pre-fix hardwiring is back.
            patch.object(
                sub_mod,
                "_rzp_client",
                side_effect=AssertionError("Razorpay SDK called for a Stripe sub"),
            ),
        ):
            res = client.post("/api/subscriptions/cancel")
        conn.close()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(stripe_calls, ["sub_stripe_123"])

    def test_stripe_cancel_helper_hits_cancel_endpoint(self):
        from motoquant import payments

        seen = {}

        def fake_post(path, fields):
            seen["path"], seen["fields"] = path, fields
            return {"id": "sub_x", "cancel_at_period_end": True}

        with patch.object(payments, "_stripe_api_post", side_effect=fake_post):
            payments.stripe_cancel_subscription("sub_x")
        self.assertEqual(seen["path"], "/v1/subscriptions/sub_x")
        self.assertEqual(seen["fields"], {"cancel_at_period_end": "true"})


class TestStripeWebhookCompensation(unittest.TestCase):
    """A mid-apply failure must un-record the ledger row so Stripe's retry is
    processed instead of swallowed as 'duplicate' (2026-08-11 audit)."""

    def test_failed_apply_allows_retry(self):
        import hashlib
        import hmac as hmac_mod
        import time as time_mod

        from fastapi.testclient import TestClient

        conn = _mem_conn()
        _bootstrap(conn)
        client = TestClient(_make_app(), raise_server_exceptions=False)
        secret = "whsec_comp_test"
        body = json.dumps(
            {"id": "evt_comp_1", "type": "customer.subscription.updated", "data": {}}
        ).encode()
        ts = str(int(time_mod.time()))
        sig = hmac_mod.new(
            secret.encode(), f"{ts}.".encode() + body, hashlib.sha256
        ).hexdigest()
        headers = {"stripe-signature": f"t={ts},v1={sig}"}

        calls = {"n": 0}

        def flaky_handler(conn_, etype, event):
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("transient DB hiccup")
            return {"status": "ok", "event": etype}

        with (
            patch.dict("os.environ", {"STRIPE_WEBHOOK_SECRET": secret}),
            patch("motoquant.payments._get_conn", return_value=_NoCloseConn(conn)),
            patch("motoquant.payments._handle_stripe_event", side_effect=flaky_handler),
        ):
            first = client.post(
                "/api/payments/webhook/stripe", content=body, headers=headers
            )
            # First delivery fails mid-apply → 500, and the ledger row must be
            # gone so the retry is NOT treated as a duplicate.
            self.assertEqual(first.status_code, 500)
            retry = client.post(
                "/api/payments/webhook/stripe", content=body, headers=headers
            )
        conn.close()
        self.assertEqual(retry.status_code, 200)
        self.assertEqual(retry.json()["status"], "ok")
        self.assertEqual(calls["n"], 2, "retry must reach the handler again")


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

    _WEBHOOK_SECRET = "whsec_test_lifecycle"

    def _send(self, event: dict):
        # 2026-07-02: the webhook now fails closed on an unset secret, so
        # lifecycle events must be signed with a configured secret (this is
        # exactly the production path, not a test-only shortcut).
        body = json.dumps(event).encode()
        with patch.dict("os.environ", {"STRIPE_WEBHOOK_SECRET": self._WEBHOOK_SECRET}):
            return self.client.post(
                "/api/payments/webhook/stripe",
                content=body,
                headers={"stripe-signature": _stripe_sig(body, self._WEBHOOK_SECRET)},
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


# ══════════════════════════════════════════════════════════════════════════════
# 6. Razorpay webhook idempotency (replay protection, July 2026)
# ══════════════════════════════════════════════════════════════════════════════


def _make_subs_app():
    from fastapi import FastAPI

    from motoquant.subscriptions import router as subs_router

    app = FastAPI()
    app.include_router(subs_router, prefix="/api/subscriptions")
    return app


def _rzp_sig(payload: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


class TestRazorpayWebhookIdempotency(unittest.TestCase):
    """Mirror of TestStripeWebhook's duplicate-drop coverage for the Razorpay
    handler: before July 2026 the signature was verified but events were
    never ledgered, so a REPLAYED subscription.cancelled could downgrade a
    re-activated user."""

    _WEBHOOK_SECRET = "rzp_whsec_test"

    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient

        cls.client = TestClient(_make_subs_app(), raise_server_exceptions=False)

    def setUp(self):
        from motoquant.database import users_repo

        self.conn = _mem_conn()
        _bootstrap(self.conn)
        self.user = users_repo.get_or_create_user(self.conn, "rzp@test.in")
        self._patchers = [
            patch(
                "motoquant.subscriptions._get_conn",
                return_value=_NoCloseConn(self.conn),
            ),
            patch("motoquant.subscriptions.RZP_WEBHOOK_SECRET", self._WEBHOOK_SECRET),
        ]
        for p in self._patchers:
            p.start()

    def tearDown(self):
        for p in self._patchers:
            p.stop()
        self.conn.close()

    def _event(self, event_type: str, sub_id: str, tier: str = "pro") -> bytes:
        return json.dumps(
            {
                "event": event_type,
                "payload": {
                    "subscription": {
                        "entity": {
                            "id": sub_id,
                            "plan_id": "plan_test",
                            "notes": {
                                "user_id": str(self.user["id"]),
                                "tier": tier,
                                "billing_cycle": "monthly",
                            },
                        }
                    }
                },
            }
        ).encode()

    def _send(self, body: bytes, event_id: str | None = None):
        headers = {"x-razorpay-signature": _rzp_sig(body, self._WEBHOOK_SECRET)}
        if event_id:
            headers["x-razorpay-event-id"] = event_id
        return self.client.post(
            "/api/subscriptions/webhook", content=body, headers=headers
        )

    def test_duplicate_event_id_is_dropped(self):
        body = self._event("subscription.activated", "sub_rzp_1")
        res1 = self._send(body, event_id="evt_rzp_1")
        self.assertEqual(res1.json()["status"], "ok")
        res2 = self._send(body, event_id="evt_rzp_1")
        self.assertEqual(res2.json()["status"], "duplicate")

    def test_replayed_cancellation_cannot_downgrade_reactivated_user(self):
        from motoquant.database import users_repo

        self._send(self._event("subscription.activated", "sub_rzp_2"), "evt_act_1")
        cancel_body = self._event("subscription.cancelled", "sub_rzp_2")
        self._send(cancel_body, "evt_cancel_1")
        self.assertEqual(
            users_repo.get_user_by_id(self.conn, self.user["id"])["tier"], "free"
        )
        # Re-activation carries a FRESH event id (same body as the first
        # activation — proves the header id wins over the body-hash fallback).
        self._send(self._event("subscription.activated", "sub_rzp_2"), "evt_act_2")
        self.assertEqual(
            users_repo.get_user_by_id(self.conn, self.user["id"])["tier"], "pro"
        )
        res = self._send(cancel_body, "evt_cancel_1")
        self.assertEqual(res.json()["status"], "duplicate")
        self.assertEqual(
            users_repo.get_user_by_id(self.conn, self.user["id"])["tier"],
            "pro",
            "replayed cancellation must not downgrade a re-activated user",
        )

    def test_missing_event_id_header_dedupes_on_body_hash(self):
        body = self._event("subscription.activated", "sub_rzp_3")
        res1 = self._send(body)
        self.assertEqual(res1.json()["status"], "ok")
        res2 = self._send(body)
        self.assertEqual(res2.json()["status"], "duplicate")


if __name__ == "__main__":
    unittest.main()
