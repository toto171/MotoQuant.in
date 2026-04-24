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
from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Request
from pydantic import BaseModel

from .auth import get_current_user, require_tier
from .database import subscriptions_repo as _subs
from .database import users_repo as _users

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
MOTOQUANT_BASE_URL = os.environ.get("MOTOQUANT_BASE_URL", "https://www.motoquant.in")

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
    from .database.connection import connect as _db_connect  # noqa: PLC0415
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    return conn


def _rzp_client():
    if not _RAZORPAY_AVAILABLE:
        raise HTTPException(
            503,
            "Razorpay SDK not installed on this server. "
            "Contact support: hello@motoquant.in",
        )
    if not RZP_KEY_ID or not RZP_KEY_SECRET:
        raise HTTPException(
            503,
            "Razorpay credentials not configured. Contact support: hello@motoquant.in",
        )
    return _rzp_sdk.Client(auth=(RZP_KEY_ID, RZP_KEY_SECRET))


def _verify_webhook_signature(payload_bytes: bytes, signature: str) -> bool:
    if not RZP_WEBHOOK_SECRET:
        log.warning("RAZORPAY_WEBHOOK_SECRET not set — skipping signature verification")
        return True  # allow in dev; deny in prod via env
    expected = hmac.new(
        RZP_WEBHOOK_SECRET.encode(), payload_bytes, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def _tier_from_plan(plan_id: str) -> str:
    """Infer tier from the Razorpay plan_id."""
    for tier, cycles in PLAN_IDS.items():
        if plan_id in cycles.values():
            return tier
    # Fallback — check tier embedded in the subscription notes or items
    return "pro"


# ─── Pydantic schemas ─────────────────────────────────────────────────────────


class CheckoutRequest(BaseModel):
    tier: str   # "pro" | "studio"
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
    device_id: Optional[str] = None


class ValidateKeyResponse(BaseModel):
    valid: bool
    tier: Optional[str] = None
    message: str


class RevokeKeyRequest(BaseModel):
    key_id: int


class StatusResponse(BaseModel):
    tier: str
    subscription_status: Optional[str] = None
    current_period_end: Optional[str] = None
    billing_cycle: Optional[str] = None
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
            "Contact support: hello@motoquant.in",
        )

    client = _rzp_client()

    # Ensure Razorpay customer exists for this user
    conn = _get_conn()
    try:
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
                "total_count": 1 if body.billing_cycle == "yearly" else 120,
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
        checkout_url = f"https://rzp.io/l/{rzp_sub_id}"

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
    Idempotent: upserting the same subscription row is safe.
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
    tier = notes.get("tier") or _tier_from_plan(plan_id)

    conn = _get_conn()
    try:
        _users.ensure_tables(conn)
        _subs.ensure_tables(conn)

        # Resolve user_id — prefer DB lookup to avoid note-tampering
        existing_sub = _subs.get_subscription_by_rzp_id(conn, rzp_sub_id)
        if existing_sub:
            user_id = existing_sub["user_id"]
        elif user_id_str.isdigit():
            user_id = int(user_id_str)
        else:
            log.warning("Webhook: cannot resolve user for sub %s", rzp_sub_id)
            return {"status": "user_not_found"}

        # Parse period end
        current_end_ts = entity.get("current_end")
        current_period_end = (
            datetime.fromtimestamp(current_end_ts, tz=timezone.utc).isoformat()
            if current_end_ts
            else None
        )

        STATUS_MAP = {
            "subscription.activated":  ("active",    tier),
            "subscription.charged":    ("active",    None),   # keep existing tier
            "subscription.halted":     ("halted",    None),
            "subscription.cancelled":  ("cancelled", "free"),
            "subscription.completed":  ("completed", "free"),
            "subscription.paused":     ("halted",    None),
            "subscription.authenticated": ("authenticated", tier),
        }

        if event_type not in STATUS_MAP:
            log.debug("Unhandled webhook event: %s", event_type)
            return {"status": "unhandled_event"}

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
            _users.set_user_tier(conn, user_id, "free")
            log.info("User %d downgraded to free (event: %s)", user_id, event_type)
        elif new_tier in ("pro", "studio"):
            _users.set_user_tier(conn, user_id, new_tier)
            log.info("User %d upgraded to %s (event: %s)", user_id, new_tier, event_type)

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


@router.post("/license-key/validate", response_model=ValidateKeyResponse)
def validate_license_key(body: ValidateKeyRequest) -> ValidateKeyResponse:
    """
    Desktop app startup validation. No auth header required.
    Verifies key_hash, updates last_seen_at, returns tier.
    """
    conn = _get_conn()
    try:
        row = _subs.validate_license_key(conn, body.key, body.device_id)
    finally:
        conn.close()

    if not row:
        return ValidateKeyResponse(valid=False, message="Invalid or revoked license key.")
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

    client = _rzp_client()
    try:
        client.subscription.cancel(sub["razorpay_subscription_id"], {"cancel_at_cycle_end": 1})
    except Exception as exc:
        log.error("Failed to cancel Razorpay subscription: %s", exc)
        raise HTTPException(502, f"Razorpay error: {exc}") from exc

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
   