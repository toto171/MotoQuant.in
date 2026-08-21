"""
MotoQuant Pro — Unified Payments Layer
=======================================
Provider-agnostic checkout + webhook surface across Razorpay (India: UPI,
cards, netbanking, wallets), Stripe (international cards), and a PayPal
placeholder. Zero new Python dependencies: Stripe is driven through stdlib
urllib; webhook signatures verified with stdlib hmac. The Razorpay path
delegates to the existing motoquant.subscriptions module (razorpay SDK is
already a production dependency).

Endpoints
---------
GET  /api/payments/config           Public — provider status, prices, beta flag
POST /api/payments/checkout         Auth — unified checkout (provider="auto")
POST /api/payments/webhook/stripe   Stripe events (signature-verified, idempotent)
POST /api/payments/webhook/paypal   Placeholder (501 until PayPal onboarding)

Provider env vars
-----------------
Razorpay (see motoquant/subscriptions.py):
    RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, RAZORPAY_WEBHOOK_SECRET,
    PLAN_ID_{PRO|STUDIO}_{MONTHLY|YEARLY}
Stripe:
    STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET,
    STRIPE_PRICE_{PRO|STUDIO}_{MONTHLY|YEARLY}   (price_... ids from dashboard)
PayPal (planned, not yet implemented):
    PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET

None of these are required for the server to boot — every unset provider
simply reports configured=false in /api/payments/config and returns a
friendly 503 from checkout. Linking real merchant accounts later is purely
an env-var exercise in the Render dashboard.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from . import auth as _auth, subscriptions as _rzp
from .auth import get_current_user
from .database import subscriptions_repo as _subs, users_repo as _users

log = logging.getLogger("motoquant.payments")

router = APIRouter(tags=["payments"])

MOTOQUANT_BASE_URL = os.environ.get("MOTOQUANT_BASE_URL", "https://motoquant.in")

# ─── Canonical price book (display + checkout metadata) ───────────────────────
# INR prices are the source of truth (Razorpay plans must match). USD prices
# are display anchors for the Stripe path — actual Stripe charges come from
# the dashboard price objects referenced by STRIPE_PRICE_* env vars.

PRICES_INR = {
    "pro": {"monthly": 499, "yearly": 4999},
    "studio": {"monthly": 1999, "yearly": 19990},
}
PRICES_USD_DISPLAY = {
    "pro": {"monthly": 5.99, "yearly": 59.0},
    "studio": {"monthly": 23.99, "yearly": 239.0},
}

VALID_TIERS = ("pro", "studio")
VALID_CYCLES = ("monthly", "yearly")
VALID_PROVIDERS = ("auto", "razorpay", "stripe", "paypal")

STRIPE_API_BASE = "https://api.stripe.com"
STRIPE_SIG_TOLERANCE_S = 300


# ─── Provider availability ────────────────────────────────────────────────────


def _stripe_secret_key() -> str:
    return os.environ.get("STRIPE_SECRET_KEY", "")


def _stripe_webhook_secret() -> str:
    return os.environ.get("STRIPE_WEBHOOK_SECRET", "")


def _stripe_price_id(tier: str, cycle: str) -> str:
    return os.environ.get(f"STRIPE_PRICE_{tier.upper()}_{cycle.upper()}", "")


def _razorpay_configured() -> bool:
    return bool(_rzp._RAZORPAY_AVAILABLE and _rzp.RZP_KEY_ID and _rzp.RZP_KEY_SECRET)


def _stripe_configured() -> bool:
    return bool(_stripe_secret_key())


def _paypal_configured() -> bool:
    return bool(
        os.environ.get("PAYPAL_CLIENT_ID") and os.environ.get("PAYPAL_CLIENT_SECRET")
    )


def _get_conn() -> sqlite3.Connection:
    from .database.connection import row_conn  # noqa: PLC0415

    return row_conn()


# ─── Schemas ──────────────────────────────────────────────────────────────────


class UnifiedCheckoutRequest(BaseModel):
    tier: str  # "pro" | "studio"
    billing_cycle: str = "monthly"  # "monthly" | "yearly"
    provider: str = "auto"  # "auto" | "razorpay" | "stripe" | "paypal"


class UnifiedCheckoutResponse(BaseModel):
    provider: str
    checkout_url: str
    provider_subscription_id: str | None = None
    tier: str
    billing_cycle: str


# ─── Public config (consumed by the pricing page) ─────────────────────────────


@router.get("/config")
def payments_config() -> dict:
    """Public provider/pricing status. No secrets — booleans only."""
    razorpay_ok = _razorpay_configured()
    stripe_ok = _stripe_configured()
    return {
        "billing_enforced": _auth.BILLING_ENFORCE,
        "beta": not _auth.BILLING_ENFORCE,
        "currency": "INR",
        "gst_note": (
            "No GST is charged — the listed price is the total payable. "
            "MotoQuant Pro is operated by an unregistered sole proprietorship "
            "below the Rs.20 lakh GST registration threshold for services."
        ),
        "prices_inr": PRICES_INR,
        "prices_usd_display": PRICES_USD_DISPLAY,
        "providers": {
            "razorpay": {
                "configured": razorpay_ok,
                "region": "India",
                "methods": ["upi", "cards", "netbanking", "wallets"],
            },
            "stripe": {
                "configured": stripe_ok,
                "region": "International",
                "methods": ["cards"],
            },
            "paypal": {
                "configured": False,
                "status": "planned",
                "region": "International",
                "methods": ["paypal"],
            },
        },
        "checkout_available": razorpay_ok or stripe_ok,
    }


# ─── Unified checkout ─────────────────────────────────────────────────────────


@router.post("/checkout", response_model=UnifiedCheckoutResponse)
def unified_checkout(
    body: UnifiedCheckoutRequest,
    user: dict = Depends(get_current_user),  # noqa: B008
) -> UnifiedCheckoutResponse:
    """
    Create a hosted-checkout session with the chosen (or auto-picked) provider.
    Razorpay is preferred for Indian users (UPI + cards + netbanking);
    Stripe covers international cards. Tier upgrades land via webhooks.
    """
    if body.tier not in VALID_TIERS:
        raise HTTPException(400, "tier must be 'pro' or 'studio'")
    if body.billing_cycle not in VALID_CYCLES:
        raise HTTPException(400, "billing_cycle must be 'monthly' or 'yearly'")
    if body.provider not in VALID_PROVIDERS:
        raise HTTPException(400, f"provider must be one of {VALID_PROVIDERS}")

    # Per-user checkout lock: two simultaneous requests from the same account
    # must not both pass the guards below and mint two provider subscriptions.
    # The lock is an RLock because the Razorpay branch calls into
    # _rzp.create_checkout on the same thread, which re-acquires it.
    with _rzp.acquire_checkout_lock(user.get("id") or 0):
        # One active subscription per account, provider-agnostic. Without
        # this, every extra checkout minted a new provider subscription that
        # /status and /cancel could never see — invisible double billing
        # (2026-08-11 audit). The Razorpay path re-checks inside
        # create_checkout; this covers Stripe and keeps the failure mode
        # consistent across providers.
        if user.get("id"):
            conn = _get_conn()
            try:
                _subs.ensure_tables(conn)
                existing = _subs.get_active_subscription(conn, user["id"])
                pending = _subs.get_recent_created_subscription(conn, user["id"])
            finally:
                conn.close()
            if existing:
                raise HTTPException(
                    409,
                    f"You already have an active {existing['tier']} subscription. "
                    "Cancel it from your account page first (access continues to "
                    "the end of the paid period), then subscribe to the new plan.",
                )
            # Time-boxed: an open checkout (status "created", < 30 min old)
            # must complete or expire before another one is minted.
            if pending:
                raise HTTPException(409, _rzp._CHECKOUT_PENDING_MSG)

        provider = body.provider
        if provider == "auto":
            if _razorpay_configured():
                provider = "razorpay"
            elif _stripe_configured():
                provider = "stripe"
            else:
                raise HTTPException(
                    503,
                    "Payments aren't live yet — everything is free during the "
                    "open beta. Subscriptions open at commercial launch.",
                )

        if provider == "razorpay":
            rzp_resp = _rzp.create_checkout(
                _rzp.CheckoutRequest(tier=body.tier, billing_cycle=body.billing_cycle),
                user,
            )
            return UnifiedCheckoutResponse(
                provider="razorpay",
                checkout_url=rzp_resp.checkout_url,
                provider_subscription_id=rzp_resp.razorpay_subscription_id,
                tier=body.tier,
                billing_cycle=body.billing_cycle,
            )

        if provider == "stripe":
            sess = _create_stripe_checkout(user, body.tier, body.billing_cycle)
            # Persist a placeholder row so the 30-min guard above sees this
            # open checkout. The cs_… session id is parked in the (legacy-
            # named) razorpay_subscription_id column; checkout.session.completed
            # deletes it via resolve_created_checkout once the real sub_… row
            # exists.
            if user.get("id") and sess.get("id"):
                conn = _get_conn()
                try:
                    _subs.upsert_subscription(
                        conn,
                        user_id=user["id"],
                        razorpay_subscription_id=sess["id"],
                        tier=body.tier,
                        status="created",
                        billing_cycle=body.billing_cycle,
                        provider="stripe",
                    )
                finally:
                    conn.close()
            return UnifiedCheckoutResponse(
                provider="stripe",
                checkout_url=sess["url"],
                provider_subscription_id=sess.get("id"),
                tier=body.tier,
                billing_cycle=body.billing_cycle,
            )

        # paypal
        raise HTTPException(
            503,
            "PayPal support is planned — use Razorpay (UPI/cards/netbanking) or "
            "Stripe (international cards) for now.",
        )


# ─── Stripe (stdlib HTTP client) ──────────────────────────────────────────────


def _stripe_api_post(path: str, fields: dict) -> dict:
    """POST form-encoded fields to the Stripe API. Raises HTTPException on error."""
    key = _stripe_secret_key()
    if not key:
        raise HTTPException(503, "Stripe is not configured on this server.")
    data = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(
        STRIPE_API_BASE + path,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        try:
            err = json.loads(exc.read()).get("error", {})
            msg = err.get("message", str(exc))
        except Exception:
            msg = str(exc)
        log.error("Stripe API error on %s: %s", path, msg)
        raise HTTPException(502, f"Stripe error: {msg}") from exc
    except urllib.error.URLError as exc:
        log.error("Stripe API unreachable: %s", exc)
        raise HTTPException(502, "Stripe API unreachable — try again shortly.") from exc


def stripe_cancel_subscription(sub_id: str) -> None:
    """Cancel a Stripe subscription at period end (mirrors the Razorpay
    cancel_at_cycle_end behaviour). Called by subscriptions.cancel_subscription
    when the stored subscription's provider is 'stripe' — that route was
    hardwired to the Razorpay SDK, leaving Stripe subscribers unable to cancel
    (2026-08-11 audit). Raises HTTPException(502/503) on API failure."""
    _stripe_api_post(f"/v1/subscriptions/{sub_id}", {"cancel_at_period_end": "true"})


def _create_stripe_checkout(user: dict, tier: str, cycle: str) -> dict:
    price_id = _stripe_price_id(tier, cycle)
    if not price_id:
        raise HTTPException(
            503,
            f"Stripe price not configured for {tier}/{cycle}. "
            "Contact support: motoquant@gmail.com",
        )

    fields = {
        "mode": "subscription",
        "line_items[0][price]": price_id,
        "line_items[0][quantity]": "1",
        "success_url": f"{MOTOQUANT_BASE_URL}/account?checkout=success&provider=stripe",
        "cancel_url": f"{MOTOQUANT_BASE_URL}/pricing?checkout=cancelled",
        "client_reference_id": str(user["id"]),
        "metadata[user_id]": str(user["id"]),
        "metadata[tier]": tier,
        "metadata[billing_cycle]": cycle,
        # Mirror onto the subscription object so lifecycle events carry it too.
        "subscription_data[metadata][user_id]": str(user["id"]),
        "subscription_data[metadata][tier]": tier,
        "subscription_data[metadata][billing_cycle]": cycle,
    }
    if user.get("stripe_customer_id"):
        fields["customer"] = user["stripe_customer_id"]
    else:
        fields["customer_email"] = user["email"]

    sess = _stripe_api_post("/v1/checkout/sessions", fields)
    if not sess.get("url"):
        raise HTTPException(502, "Stripe did not return a checkout URL.")
    return sess


def _verify_stripe_signature(
    payload: bytes,
    sig_header: str,
    secret: str,
    tolerance_s: int = STRIPE_SIG_TOLERANCE_S,
) -> bool:
    """
    Verify a Stripe-Signature header: 't=<ts>,v1=<hmac>,...'.
    HMAC-SHA256 over '{t}.{payload}' with the webhook signing secret.
    """
    if not secret:
        # Fail CLOSED: an unset webhook secret means we cannot trust any
        # incoming event, so reject them all. The previous "return True"
        # dev-convenience let anyone forge a checkout.session.completed and
        # upgrade any account to Studio for free while STRIPE_SECRET_KEY was
        # set (checkout live) but the webhook secret hadn't been configured
        # yet -- the exact partial-config state PAYMENTS_SETUP.md walks
        # through. To test the webhook locally, set a dummy secret and sign
        # with it (see tests).
        log.error("STRIPE_WEBHOOK_SECRET not set — rejecting webhook (fail closed)")
        return False
    try:
        parts = dict(kv.split("=", 1) for kv in sig_header.split(",") if "=" in kv)
        ts = int(parts.get("t", "0"))
        v1_sigs = [
            kv.split("=", 1)[1] for kv in sig_header.split(",") if kv.startswith("v1=")
        ]
    except Exception:
        return False
    if not v1_sigs or abs(time.time() - ts) > tolerance_s:
        return False
    signed = f"{ts}.".encode() + payload
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, sig) for sig in v1_sigs)


def _iso_from_ts(ts: int | None) -> str | None:
    if not ts:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _stripe_period_end_ts(obj: dict) -> int | None:
    """Extract current_period_end from a Stripe subscription object. On
    current Stripe API versions the field lives on the subscription ITEMS,
    not the subscription object — fall back to items.data[0]."""
    ts = obj.get("current_period_end")
    if ts:
        return ts
    items = (obj.get("items") or {}).get("data") or []
    if items:
        return items[0].get("current_period_end")
    return None


def _resolve_stripe_user(
    conn: sqlite3.Connection, obj: dict, sub_row: dict | None
) -> int | None:
    """Resolve our user id from a Stripe object: existing sub row → metadata →
    client_reference_id → stripe customer id."""
    if sub_row:
        return sub_row["user_id"]
    meta = obj.get("metadata") or {}
    for candidate in (meta.get("user_id"), obj.get("client_reference_id")):
        if candidate and str(candidate).isdigit():
            return int(candidate)
    customer = obj.get("customer")
    if customer:
        user = _users.get_user_by_stripe_customer(conn, customer)
        if user:
            return user["id"]
    return None


# Stripe subscription.status → our subscription status vocabulary
_STRIPE_STATUS_MAP = {
    "active": "active",
    "trialing": "active",
    "past_due": "past_due",
    "unpaid": "halted",
    "canceled": "cancelled",
    "incomplete": "created",
    "incomplete_expired": "expired",
    "paused": "halted",
}


def _handle_stripe_event(conn: sqlite3.Connection, etype: str, event: dict) -> dict:
    obj = event.get("data", {}).get("object", {}) or {}

    if etype == "checkout.session.completed":
        user_id = _resolve_stripe_user(conn, obj, None)
        if user_id is None:
            # Retryable: the outer stripe_webhook handler catches this,
            # deletes the ledger row and re-raises, so Stripe redelivers
            # after the operator links the customer. The old 200 +
            # "user_not_found" left the ledger row committed — Stripe never
            # retried and the paid upgrade was lost forever.
            log.error("Stripe checkout.session.completed: cannot resolve user")
            raise HTTPException(
                400,
                "No MotoQuant user for this checkout session — link the "
                "Stripe customer to a user (users.stripe_customer_id), then "
                "redeliver the event.",
            )
        meta = obj.get("metadata") or {}
        tier = meta.get("tier")
        if tier not in VALID_TIERS:
            # NEVER default to "pro". Non-retryable ON PURPOSE (ledger row
            # kept, HTTP 200): the event payload is immutable, so redelivery
            # can never add the missing metadata — a dashboard-created
            # payment link lands here and must be reconciled manually.
            log.error(
                "Stripe checkout.session.completed %s: metadata tier %r "
                "missing/invalid — NOT granting any tier; reconcile manually",
                obj.get("id"),
                tier,
            )
            return {"status": "ignored_no_tier", "event": etype}
        cycle = meta.get("billing_cycle", "monthly")
        sub_id = obj.get("subscription") or f"cs_{obj.get('id', 'unknown')}"
        if obj.get("subscription") and obj.get("id"):
            # The real sub_… id exists — clear the checkout placeholder row
            # keyed on the cs_… session id (30-min duplicate-checkout guard).
            _subs.resolve_created_checkout(conn, obj["id"])
        if obj.get("customer"):
            _users.set_stripe_customer(conn, user_id, obj["customer"])
        _subs.upsert_subscription(
            conn,
            user_id=user_id,
            razorpay_subscription_id=sub_id,
            tier=tier,
            status="active",
            billing_cycle=cycle,
            provider="stripe",
        )
        _users.set_user_tier(conn, user_id, tier)
        log.info("User %d upgraded to %s via Stripe checkout", user_id, tier)
        return {"status": "ok", "event": etype}

    if etype in ("customer.subscription.updated", "customer.subscription.deleted"):
        sub_id = obj.get("id", "")
        if not sub_id:
            return {"status": "ignored"}
        sub_row = _subs.get_subscription_by_rzp_id(conn, sub_id)
        user_id = _resolve_stripe_user(conn, obj, sub_row)
        if user_id is None:
            # Retryable (see checkout.session.completed above): the outer
            # handler un-records the ledger row so Stripe's redelivery gets a
            # fresh attempt once the customer is linked.
            log.error("Stripe %s: cannot resolve user for %s", etype, sub_id)
            raise HTTPException(
                400,
                f"No MotoQuant user for Stripe subscription {sub_id} — link "
                "the Stripe customer to a user (users.stripe_customer_id), "
                "then redeliver the event.",
            )
        meta = obj.get("metadata") or {}
        # Tier ladder: our own subscription row → validated metadata tier.
        # NEVER default to "pro" — an event for a subscription we've never
        # seen, with no usable metadata, must not grant (or revoke) anything.
        tier = (sub_row or {}).get("tier") or (
            meta.get("tier") if meta.get("tier") in VALID_TIERS else None
        )
        if tier is None:
            log.error(
                "Stripe %s for unknown subscription %s with no usable tier "
                "metadata — ignoring (no upsert, no tier change)",
                etype,
                sub_id,
            )
            return {"status": "ignored_unknown_subscription", "event": etype}
        cycle = (sub_row or {}).get("billing_cycle") or meta.get(
            "billing_cycle", "monthly"
        )
        stripe_status = obj.get("status", "")
        if etype.endswith("deleted") or stripe_status == "canceled":
            status, new_tier = "cancelled", "free"
        else:
            status = _STRIPE_STATUS_MAP.get(stripe_status, "created")
            new_tier = tier if status == "active" else None
        _subs.upsert_subscription(
            conn,
            user_id=user_id,
            razorpay_subscription_id=sub_id,
            tier=tier,
            status=status,
            current_period_end=_iso_from_ts(_stripe_period_end_ts(obj)),
            billing_cycle=cycle,
            provider="stripe",
        )
        if new_tier == "free":
            # Mirror the Razorpay late-cancel guard (subscriptions.py): an
            # out-of-order deleted/canceled event for an OLD subscription
            # must not downgrade a user whose NEWER subscription is still
            # active — the upsert above already moved THIS sub out of the
            # active set.
            still_active = _subs.get_active_subscription(conn, user_id)
            if still_active and (still_active["razorpay_subscription_id"] != sub_id):
                log.info(
                    "User %d keeps tier: stripe %s is for old sub %s, newer "
                    "sub %s is still active",
                    user_id,
                    etype,
                    sub_id,
                    still_active["razorpay_subscription_id"],
                )
            else:
                _users.set_user_tier(conn, user_id, "free")
                log.info("User %d downgraded to free (stripe %s)", user_id, etype)
        elif new_tier in VALID_TIERS:
            _users.set_user_tier(conn, user_id, new_tier)
        return {"status": "ok", "event": etype}

    if etype == "invoice.payment_failed":
        sub_id = (
            obj.get("subscription")
            or (obj.get("parent") or {})
            .get("subscription_details", {})
            .get("subscription")
            or ""
        )
        sub_row = _subs.get_subscription_by_rzp_id(conn, sub_id) if sub_id else None
        if not sub_row:
            return {"status": "ignored"}
        _subs.upsert_subscription(
            conn,
            user_id=sub_row["user_id"],
            razorpay_subscription_id=sub_id,
            tier=sub_row["tier"],
            status="past_due",
            billing_cycle=sub_row.get("billing_cycle") or "monthly",
            provider="stripe",
        )
        log.info("Subscription %s marked past_due (payment failed)", sub_id)
        return {"status": "ok", "event": etype}

    log.debug("Unhandled Stripe event: %s", etype)
    return {"status": "unhandled_event", "event": etype}


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request) -> dict:
    """
    Stripe sends events here (server-to-server, unauthenticated). Signature
    is verified against STRIPE_WEBHOOK_SECRET; deliveries are idempotent via
    the payment_events ledger.
    """
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    if not _verify_stripe_signature(payload, sig, _stripe_webhook_secret()):
        log.warning("Stripe webhook signature verification failed")
        raise HTTPException(400, "Invalid webhook signature")

    try:
        event = json.loads(payload)
    except Exception:
        raise HTTPException(400, "Malformed JSON payload")

    event_id = event.get("id", "")
    etype = event.get("type", "")

    conn = _get_conn()
    try:
        _users.ensure_tables(conn)
        _subs.ensure_tables(conn)
        if event_id and not _subs.record_payment_event(
            conn, "stripe", event_id, etype, payload.decode(errors="replace")
        ):
            log.info("Duplicate Stripe event %s ignored", event_id)
            return {"status": "duplicate", "event": etype}
        try:
            return _handle_stripe_event(conn, etype, event)
        except Exception:
            # The ledger row above already committed; un-record it so Stripe's
            # retry gets a fresh attempt instead of a "duplicate" swallow
            # (2026-08-11 audit — mid-apply failure lost the event forever).
            if event_id:
                _subs.delete_payment_event(conn, "stripe", event_id)
            raise
    finally:
        conn.close()


# ─── PayPal placeholder ───────────────────────────────────────────────────────


@router.post("/webhook/paypal")
async def paypal_webhook(request: Request) -> dict:
    """Placeholder: PayPal onboarding is planned but not yet enabled."""
    _ = await request.body()
    log.info("PayPal webhook hit but provider is not enabled")
    raise HTTPException(501, "PayPal integration is planned but not yet enabled.")
