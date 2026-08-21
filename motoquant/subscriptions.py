"""
MotoQuant Pro — Subscriptions Module (Razorpay)
================================================
Handles Razorpay subscription checkout, webhooks, and desktop license keys.

Endpoints
---------
POST /api/subscriptions/checkout             Create Razorpay subscription link
POST /api/subscriptions/webhook              Razorpay event webhook (unauthenticated)
POST /api/subscriptions/license-key          Generate desktop license key (pro/studio)
POST /api/subscriptions/license-key/validate Desktop app startup validation (no auth)
POST /api/subscriptions/license-key/revoke   Revoke a specific key by id
POST /api/subscriptions/cancel               Cancel subscription at period end
GET  /api/subscriptions/status               Current subscription status

Razorpay env vars required (prod)
----------------------------------
    RAZORPAY_KEY_ID
    RAZORPAY_KEY_SECRET
    RAZORPAY_WEBHOOK_SECRET
    PLAN_ID_PRO_MONTHLY
    PLAN_ID_PRO_YEARLY
    PLAN_ID_STUDIO_MONTHLY
    PLAN_ID_STUDIO_YEARLY

Webhook events handled
-----------------------
    subscription.activated   → set user tier, subscription.status = active
    subscription.charged     → renew current_period_end
    subscription.halted      → mark past_due (too many retries)
    subscription.cancelled   → downgrade user to free
    subscription.completed   → downgrade user to free
    subscription.paused      → no tier change (paused = still entitled until period end)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from .auth import get_current_user, require_tier
from .database import subscriptions_repo as _subs, users_repo as _users
from .ratelimit import rate_limit

log = logging.getLogger("motoquant.subscriptions")

router = APIRouter(tags=["subscriptions"])

# ─── Razorpay SDK (optional — gracefully disabled without the package) ────────

try:
    import razorpay as _rzp_sdk  # type: ignore

    _RAZORPAY_AVAILABLE = True
except ImportError:
    _RAZORPAY_AVAILABLE = False
    log.warning("razorpay SDK not installed — checkout disabled (tests use mock)")

# ─── Config ───────────────────────────────────────────────────────────────────

RZP_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RZP_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
RZP_WEBHOOK_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")
MOTOQUANT_BASE_URL = os.environ.get("MOTOQUANT_BASE_URL", "https://motoquant.in")

PLAN_IDS = {
    "pro": {
        "monthly": os.environ.get("PLAN_ID_PRO_MONTHLY", ""),
        "yearly": os.environ.get("PLAN_ID_PRO_YEARLY", ""),
    },
    "studio": {
        "monthly": os.environ.get("PLAN_ID_STUDIO_MONTHLY", ""),
        "yearly": os.environ.get("PLAN_ID_STUDIO_YEARLY", ""),
    },
}

# ─── Helpers ──────────────────────────────────────────────────────────────────


def _get_conn() -> sqlite3.Connection:
    from .database.connection import row_conn  # noqa: PLC0415

    return row_conn()


def _rzp_client():
    if not _RAZORPAY_AVAILABLE:
        raise HTTPException(
            503,
            "Razorpay SDK not installed on this server. "
            "Contact support: motoquant@gmail.com",
        )
    if not RZP_KEY_ID or not RZP_KEY_SECRET:
        raise HTTPException(
            503,
            "Razorpay credentials not configured. Contact support: motoquant@gmail.com",
        )
    return _rzp_sdk.Client(auth=(RZP_KEY_ID, RZP_KEY_SECRET))


def _verify_webhook_signature(payload_bytes: bytes, signature: str) -> bool:
    if not RZP_WEBHOOK_SECRET:
        # Fail CLOSED (see the matching note in payments.py): an unset
        # secret must reject every webhook, not accept every webhook.
        # Otherwise a forged subscription.charged event upgrades any
        # account for free while checkout is live but the secret is unset.
        log.error("RAZORPAY_WEBHOOK_SECRET not set — rejecting webhook (fail closed)")
        return False
    expected = hmac.new(
        RZP_WEBHOOK_SECRET.encode(), payload_bytes, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def _tier_from_plan(plan_id: str) -> str | None:
    """Infer tier from the Razorpay plan_id. Returns None when the plan id is
    unknown — the old silent "pro" fallback meant a mistyped/unset PLAN_ID_*
    env granted pro to ANY plan; callers must treat None as unresolvable."""
    if not plan_id:
        # Guard: with PLAN_ID_* env unset every cycles.values() is "" and an
        # empty plan_id would spuriously match the first tier.
        return None
    for tier, cycles in PLAN_IDS.items():
        if plan_id in cycles.values():
            return tier
    return None


# ─── Per-user checkout lock (concurrency guard) ───────────────────────────────
# Two simultaneous checkout requests from the same account could both pass the
# duplicate-subscription guard and mint TWO provider subscriptions. RLock (not
# Lock) is load-bearing: payments.unified_checkout holds the lock and then
# calls create_checkout below on the same thread, which re-acquires it.

_CHECKOUT_LOCKS: dict[int, threading.RLock] = {}
_CHECKOUT_LOCKS_GUARD = threading.Lock()

_CHECKOUT_PENDING_MSG = (
    "A checkout you started in the last 30 minutes is still open — "
    "complete it, or wait a few minutes and try again."
)


def checkout_lock(user_id: int) -> threading.RLock:
    """Return the (lazily created) per-user re-entrant checkout lock."""
    with _CHECKOUT_LOCKS_GUARD:
        lock = _CHECKOUT_LOCKS.get(user_id)
        if lock is None:
            lock = _CHECKOUT_LOCKS[user_id] = threading.RLock()
        return lock


@contextmanager
def acquire_checkout_lock(user_id: int, timeout_s: float = 30.0):
    """Bounded acquire of the per-user checkout lock. The lock is held across
    provider network calls, so a hung provider connection would otherwise park
    every later checkout request from that user on an unbounded acquire —
    a threadpool-exhaustion hazard on the 0.5-CPU prod tier. Re-entrant on the
    same thread (RLock), so the payments-layer wrapper composing with
    create_checkout's own acquire is fine."""
    lock = checkout_lock(user_id)
    if not lock.acquire(timeout=timeout_s):
        raise HTTPException(
            503,
            "Another checkout for this account is still being processed — "
            "try again in a minute.",
        )
    try:
        yield
    finally:
        lock.release()


# ─── Pydantic schemas ─────────────────────────────────────────────────────────


class CheckoutRequest(BaseModel):
    tier: str  # "pro" | "studio"
    billing_cycle: str = "monthly"  # "monthly" | "yearly"


class CheckoutResponse(BaseModel):
    razorpay_subscription_id: str
    checkout_url: str
    plan_id: str
    tier: str
    billing_cycle: str


class LicenseKeyResponse(BaseModel):
    key: str
    message: str


class ValidateKeyRequest(BaseModel):
    key: str
    device_id: str | None = None


class ValidateKeyResponse(BaseModel):
    valid: bool
    tier: str | None = None
    message: str


class RevokeKeyRequest(BaseModel):
    key_id: int


class StatusResponse(BaseModel):
    tier: str
    subscription_status: str | None = None
    current_period_end: str | None = None
    billing_cycle: str | None = None
    license_key_count: int


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/checkout", response_model=CheckoutResponse)
def create_checkout(
    body: CheckoutRequest,
    user: dict = Depends(get_current_user),
) -> CheckoutResponse:
    """
    Create a Razorpay subscription and return the hosted payment URL.
    The user is redirected to Razorpay's checkout page to complete payment.
    On success, Razorpay sends a webhook which upgrades the user's tier.
    """
    if body.tier not in ("pro", "studio"):
        raise HTTPException(400, "tier must be 'pro' or 'studio'")
    if body.billing_cycle not in ("monthly", "yearly"):
        raise HTTPException(400, "billing_cycle must be 'monthly' or 'yearly'")

    plan_id = PLAN_IDS[body.tier][body.billing_cycle]
    if not plan_id:
        raise HTTPException(
            503,
            f"Plan not configured for {body.tier}/{body.billing_cycle}. "
            "Contact support: motoquant@gmail.com",
        )

    client = _rzp_client()

    # Ensure Razorpay customer exists for this user. The per-user lock makes
    # guard-check → provider-create → row-persist atomic against a concurrent
    # checkout from the same account (conn opens BEFORE acquire so an open
    # failure can never leave the lock held).
    conn = _get_conn()
    lock = checkout_lock(user["id"])
    if not lock.acquire(timeout=30.0):
        conn.close()
        raise HTTPException(
            503,
            "Another checkout for this account is still being processed — "
            "try again in a minute.",
        )
    try:
        # One active subscription per account. Without this guard every extra
        # checkout minted a NEW provider subscription while /status and
        # /cancel only ever see the newest row — the older ones kept billing
        # invisibly (2026-08-11 audit, confirmed). Upgrades go through
        # cancel-then-resubscribe until proration is built.
        _subs.ensure_tables(conn)
        existing = _subs.get_active_subscription(conn, user["id"])
        if existing:
            raise HTTPException(
                409,
                f"You already have an active {existing['tier']} subscription. "
                "Cancel it from your account page first (access continues to the "
                "end of the paid period), then subscribe to the new plan.",
            )

        # Time-boxed guard: a still-open checkout (status "created", younger
        # than 30 min) must finish or expire before another provider
        # subscription is minted for the same account.
        pending = _subs.get_recent_created_subscription(conn, user["id"])
        if pending:
            raise HTTPException(409, _CHECKOUT_PENDING_MSG)

        db_user = _users.get_user_by_id(conn, user["id"])
        rzp_customer_id = db_user.get("razorpay_customer_id") if db_user else None

        if not rzp_customer_id:
            customer = client.customer.create(
                {
                    "email": user["email"],
                    "name": user["email"].split("@")[0],
                    "notes": {"user_id": str(user["id"])},
                }
            )
            rzp_customer_id = customer["id"]
            _users.set_razorpay_customer(conn, user["id"], rzp_customer_id)

        # Create subscription
        sub = client.subscription.create(
            {
                "plan_id": plan_id,
                "customer_id": rzp_customer_id,
                # total_count = number of BILLING CYCLES, not years: a yearly
                # plan with total_count=1 bills ONCE and then fires
                # subscription.completed, silently downgrading the user at
                # their first renewal. 10 yearly cycles / 120 monthly cycles
                # both mean "renew for ~10 years".
                "total_count": 10 if body.billing_cycle == "yearly" else 120,
                "quantity": 1,
                "customer_notify": 1,
                "notes": {
                    "user_id": str(user["id"]),
                    "tier": body.tier,
                    "billing_cycle": body.billing_cycle,
                },
                "notify_info": {
                    "notify_email": user["email"],
                },
            }
        )

        rzp_sub_id = sub["id"]
        # The hosted authorization link comes back on the create response as
        # short_url (rzp.io/i/<code>). The old code FABRICATED
        # f"https://rzp.io/l/{sub_id}" — the Payment-Links namespace with a
        # subscription id in it, a dead URL — so the in-app redirect 404'd on
        # every real checkout (2026-08-11 audit, confirmed; recoverable only
        # because customer_notify emails the correct link out-of-band).
        checkout_url = sub.get("short_url") or ""
        if not checkout_url:
            log.error(
                "Razorpay subscription.create response for %s carried no "
                "short_url — cannot hand the user a checkout link",
                rzp_sub_id,
            )
            raise HTTPException(
                502,
                "Razorpay did not return a checkout link. No charge was made — "
                "please try again or contact support.",
            )

        # Persist subscription record (status = created)
        _subs.ensure_tables(conn)
        _subs.upsert_subscription(
            conn,
            user_id=user["id"],
            razorpay_subscription_id=rzp_sub_id,
            tier=body.tier,
            status="created",
            plan_id=plan_id,
            billing_cycle=body.billing_cycle,
        )
    finally:
        conn.close()
        lock.release()

    return CheckoutResponse(
        razorpay_subscription_id=rzp_sub_id,
        checkout_url=checkout_url,
        plan_id=plan_id,
        tier=body.tier,
        billing_cycle=body.billing_cycle,
    )


@router.post("/webhook")
async def razorpay_webhook(request: Request) -> dict:
    """
    Razorpay sends events here. We verify the signature, then update tier.
    This endpoint is unauthenticated (Razorpay calls it server-to-server).
    Deliveries are idempotent via the payment_events ledger (mirrors the
    Stripe webhook in payments.py) — a REPLAYED subscription.cancelled must
    not downgrade a re-activated user.
    """
    payload_bytes = await request.body()
    signature = request.headers.get("x-razorpay-signature", "")

    if not _verify_webhook_signature(payload_bytes, signature):
        log.warning("Webhook signature verification failed")
        raise HTTPException(400, "Invalid webhook signature")

    try:
        event = json.loads(payload_bytes)
    except Exception:
        raise HTTPException(400, "Malformed JSON payload")

    # Razorpay stamps every delivery with a unique x-razorpay-event-id and
    # replays reuse it. If a proxy strips the header, fall back to a digest
    # of the raw body so replayed deliveries still dedupe.
    event_id = request.headers.get("x-razorpay-event-id", "").strip()
    if not event_id:
        event_id = hashlib.sha256(payload_bytes).hexdigest()

    event_type: str = event.get("event", "")
    entity = event.get("payload", {}).get("subscription", {}).get("entity", {})
    rzp_sub_id: str = entity.get("id", "")
    plan_id: str = entity.get("plan_id", "")

    if not rzp_sub_id:
        log.info("Webhook event %s has no subscription entity — ignoring", event_type)
        return {"status": "ignored"}

    # Read user_id from subscription notes or from our DB
    notes = entity.get("notes", {})
    user_id_str = notes.get("user_id", "")
    billing_cycle = notes.get("billing_cycle", "monthly")
    notes_tier = notes.get("tier") if notes.get("tier") in ("pro", "studio") else None

    conn = _get_conn()
    try:
        _users.ensure_tables(conn)
        _subs.ensure_tables(conn)

        if not _subs.record_payment_event(
            conn,
            "razorpay",
            event_id,
            event_type,
            payload_bytes.decode(errors="replace"),
        ):
            log.info("Duplicate Razorpay event %s ignored", event_id)
            return {"status": "duplicate", "event": event_type}

        # From here on, a failure must NOT leave the event marked as
        # processed — the ledger row above already committed, so a provider
        # retry would be swallowed as "duplicate" and the event lost forever
        # (2026-08-11 audit, confirmed). Compensate: delete the ledger row on
        # any failure and answer non-2xx so Razorpay redelivers.
        try:
            # Resolve user_id — prefer DB lookup to avoid note-tampering
            existing_sub = _subs.get_subscription_by_rzp_id(conn, rzp_sub_id)
            if existing_sub:
                user_id = existing_sub["user_id"]
            elif user_id_str.isdigit():
                user_id = int(user_id_str)
            else:
                # error-level on purpose: this is the operator's launch-week
                # log signal for webhook/user linkage problems.
                log.error("Webhook: cannot resolve user for sub %s", rzp_sub_id)
                _subs.delete_payment_event(conn, "razorpay", event_id)
                raise HTTPException(
                    400,
                    f"No MotoQuant user for subscription {rzp_sub_id} — "
                    "redeliver after linking (dashboard-created subscription?).",
                )

            # Tier resolution ladder: our own subscription row → validated
            # notes tier → plan-id lookup. No silent "pro" default — an
            # unrecognised plan must never grant a tier.
            tier = (
                (existing_sub or {}).get("tier")
                or notes_tier
                or _tier_from_plan(plan_id)
            )

            # Parse period end
            current_end_ts = entity.get("current_end")
            current_period_end = (
                datetime.fromtimestamp(current_end_ts, tz=timezone.utc).isoformat()
                if current_end_ts
                else None
            )

            STATUS_MAP = {
                "subscription.activated": ("active", tier),
                "subscription.charged": ("active", None),  # keep existing tier
                "subscription.halted": ("halted", None),
                "subscription.cancelled": ("cancelled", "free"),
                "subscription.completed": ("completed", "free"),
                "subscription.paused": ("halted", None),
                # authenticated = mandate authorized, money NOT captured yet.
                # Was ("authenticated", tier) — granting the paid tier before
                # any charge (2026-08-11 audit, confirmed). Tier now arrives
                # on activated/charged only; status is still recorded.
                "subscription.authenticated": ("authenticated", None),
            }

            if event_type not in STATUS_MAP:
                log.debug("Unhandled webhook event: %s", event_type)
                return {"status": "unhandled_event", "event": event_type}

            if tier is None:
                # Retryable: the operator fixes PLAN_ID_* env and Razorpay
                # redelivers. The `except HTTPException: raise` below BYPASSES
                # the generic compensation path, so the ledger row must be
                # deleted HERE or the redelivery is swallowed as a duplicate.
                _subs.delete_payment_event(conn, "razorpay", event_id)
                # log.error is the operator's launch-week signal (the 400
                # detail goes back to Razorpay, not into the Render logs).
                log.error(
                    "Razorpay webhook: unknown plan_id %r for subscription %s "
                    "and no tier in notes — PLAN_ID_* env missing or typo'd; "
                    "returning 400 so Razorpay redelivers after the fix.",
                    plan_id,
                    rzp_sub_id,
                )
                raise HTTPException(
                    400,
                    f"Unknown Razorpay plan_id '{plan_id}' for subscription "
                    f"{rzp_sub_id} and no tier in notes — set PLAN_ID_* env "
                    "and redeliver.",
                )

            new_status, new_tier = STATUS_MAP[event_type]

            # Update subscription row
            _subs.upsert_subscription(
                conn,
                user_id=user_id,
                razorpay_subscription_id=rzp_sub_id,
                tier=tier,
                status=new_status,
                current_period_end=current_period_end,
                plan_id=plan_id,
                billing_cycle=billing_cycle,
            )

            # Upgrade / downgrade user tier
            if new_tier == "free":
                # Late/out-of-order cancellation events for an OLD subscription
                # must not clobber a newer active one (2026-08-11 audit): only
                # downgrade when no OTHER subscription is still active — the
                # upsert above already moved THIS one out of the active set.
                still_active = _subs.get_active_subscription(conn, user_id)
                if still_active and (
                    still_active["razorpay_subscription_id"] != rzp_sub_id
                ):
                    log.info(
                        "User %d keeps tier: %s is for old sub %s, newer sub %s "
                        "is still active",
                        user_id,
                        event_type,
                        rzp_sub_id,
                        still_active["razorpay_subscription_id"],
                    )
                else:
                    _users.set_user_tier(conn, user_id, "free")
                    log.info(
                        "User %d downgraded to free (event: %s)", user_id, event_type
                    )
            elif new_tier in ("pro", "studio"):
                _users.set_user_tier(conn, user_id, new_tier)
                log.info(
                    "User %d upgraded to %s (event: %s)", user_id, new_tier, event_type
                )
        except HTTPException:
            raise
        except Exception:
            # Unexpected failure mid-apply: un-record the event so the
            # provider's retry gets a fresh attempt instead of "duplicate".
            _subs.delete_payment_event(conn, "razorpay", event_id)
            raise

    finally:
        conn.close()

    return {"status": "ok", "event": event_type}


@router.post("/license-key", response_model=LicenseKeyResponse)
def generate_license_key(
    user: dict = Depends(require_tier("pro")),
) -> LicenseKeyResponse:
    """
    Generate a new desktop license key for the current user.
    The plaintext key is returned ONCE — store it securely.
    Quota: pro=1 key, studio=5 keys.
    """
    # require_tier passes anonymous callers through as {} while the open beta
    # runs (MOTOQUANT_BILLING_ENFORCE=false) so the sim routes stay open — but
    # a license key MUST belong to an account. Guard explicitly or the
    # user["id"] below 500s on anonymous requests.
    if not user.get("id"):
        raise HTTPException(401, "Sign in to generate a license key.")
    conn = _get_conn()
    try:
        _subs.ensure_tables(conn)
        plaintext = _subs.create_license_key(conn, user["id"], user["tier"])
    finally:
        conn.close()

    if plaintext is None:
        max_keys = _subs.MAX_KEYS.get(user["tier"], 0)
        raise HTTPException(
            409,
            f"License key quota reached ({max_keys} key(s) allowed for {user['tier']} tier). "
            "Revoke an existing key first.",
        )

    return LicenseKeyResponse(
        key=plaintext,
        message="Save this key — it will not be shown again.",
    )


@router.post(
    "/license-key/validate",
    response_model=ValidateKeyResponse,
    # Unauthenticated route — the license bucket fuses key-guessing and
    # scripted hammering (July 2026 hardening; same pattern as api.py's
    # chat/optimize/autotune fuses).
    dependencies=[Depends(rate_limit("license", 10, 60.0))],
)
def validate_license_key(body: ValidateKeyRequest) -> ValidateKeyResponse:
    """
    Client startup validation. No auth header required.
    Verifies key_hash, updates last_seen_at, returns tier.
    """
    conn = _get_conn()
    try:
        row = _subs.validate_license_key(conn, body.key, body.device_id)
    except _subs.DeviceMismatchError:
        return ValidateKeyResponse(
            valid=False,
            message=(
                "This license key is already activated on another device. "
                "Revoke it from your account page and generate a new one."
            ),
        )
    finally:
        conn.close()

    if not row:
        return ValidateKeyResponse(
            valid=False, message="Invalid or revoked license key."
        )
    return ValidateKeyResponse(valid=True, tier=row["tier"], message="License valid.")


@router.post("/license-key/revoke")
def revoke_license_key(
    body: RevokeKeyRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    """Revoke one of the current user's license keys by id."""
    conn = _get_conn()
    try:
        ok = _subs.revoke_license_key(conn, body.key_id, user["id"])
    finally:
        conn.close()
    if not ok:
        raise HTTPException(404, "Key not found or does not belong to this account.")
    return {"message": f"License key {body.key_id} revoked."}


@router.post("/cancel")
def cancel_subscription(user: dict = Depends(get_current_user)) -> dict:
    """
    Cancel the active Razorpay subscription at the end of the current period.
    The user keeps access until current_period_end; tier downgrades on
    the subscription.cancelled webhook delivery.
    """
    conn = _get_conn()
    try:
        sub = _subs.get_active_subscription(conn, user["id"])
    finally:
        conn.close()

    if not sub:
        raise HTTPException(404, "No active subscription found.")

    # The subscriptions table stores ANY provider's sub id (the column name is
    # legacy); route the cancel to the provider that owns it. This route was
    # hardwired to the Razorpay SDK, so Stripe subscribers could not cancel at
    # all — their sub id was fed to Razorpay, which 400s (2026-08-11 audit).
    provider = sub.get("provider") or "razorpay"
    provider_sub_id = sub["razorpay_subscription_id"]
    cancelled_immediately = False

    if provider == "stripe":
        # Lazy import — payments.py imports this module at top level, so the
        # reverse import must stay function-local to avoid a cycle.
        from .payments import stripe_cancel_subscription  # noqa: PLC0415

        stripe_cancel_subscription(provider_sub_id)  # raises HTTPException on error
    elif provider == "razorpay":
        client = _rzp_client()
        # "authenticated" = mandate authorized, nothing captured yet.
        # cancel_at_cycle_end is undefined pre-activation (there is no cycle),
        # so cancel immediately — and clear the local row NOW so the one-
        # active-subscription 409 on checkout lifts without waiting for the
        # webhook (the later subscription.cancelled delivery upserts the same
        # state, so this is idempotent with it).
        stuck_authenticated = cancelled_immediately = (
            sub.get("status") == "authenticated"
        )
        try:
            client.subscription.cancel(
                provider_sub_id,
                {"cancel_at_cycle_end": 0 if stuck_authenticated else 1},
            )
        except Exception as exc:
            log.error("Failed to cancel Razorpay subscription: %s", exc)
            raise HTTPException(502, f"Razorpay error: {exc}") from exc
        if stuck_authenticated:
            conn = _get_conn()
            try:
                _subs.upsert_subscription(
                    conn,
                    user_id=sub["user_id"],
                    razorpay_subscription_id=provider_sub_id,
                    tier=sub["tier"],
                    status="cancelled",
                    current_period_end=sub.get("current_period_end"),
                    plan_id=sub.get("plan_id"),
                    billing_cycle=sub.get("billing_cycle") or "monthly",
                    provider="razorpay",
                )
            finally:
                conn.close()
    else:
        raise HTTPException(
            502,
            f"Subscription {provider_sub_id} belongs to unsupported provider "
            f"'{provider}' — contact support.",
        )

    if cancelled_immediately:
        # Never-activated mandate: there is no billing period to run out.
        return {
            "message": "Pending subscription cancelled — you can start a new checkout now.",
            "current_period_end": None,
        }
    return {
        "message": "Subscription will be cancelled at the end of the current billing period.",
        "current_period_end": sub.get("current_period_end"),
    }


@router.get("/status", response_model=StatusResponse)
def subscription_status(user: dict = Depends(get_current_user)) -> StatusResponse:
    """Return the current user's subscription + license-key summary."""
    conn = _get_conn()
    try:
        _subs.ensure_tables(conn)
        sub = _subs.get_active_subscription(conn, user["id"])
        key_count = _subs.count_active_keys(conn, user["id"])
    finally:
        conn.close()

    return StatusResponse(
        tier=user["tier"],
        subscription_status=sub["status"] if sub else None,
        current_period_end=sub["current_period_end"] if sub else None,
        billing_cycle=sub["billing_cycle"] if sub else None,
        license_key_count=key_count,
    )
