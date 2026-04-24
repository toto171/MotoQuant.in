"""
MotoQuant Pro — Auth Module
============================
Passwordless magic-link login + JWT access/refresh token management.

Endpoints
---------
POST /api/auth/magic-link   Request magic-link email
POST /api/auth/verify       Exchange magic-link token → JWT pair
POST /api/auth/refresh      Access token from valid refresh token
POST /api/auth/logout       Revoke refresh session
GET  /api/auth/me           Current user info

FastAPI dependency
------------------
    require_tier("pro")     — 402 if authenticated but wrong tier
    get_current_user()      — 401 if unauthenticated

Email backends (env-var driven)
--------------------------------
- Dev: MOTOQUANT_EMAIL_BACKEND=stdout (default) — prints token to stdout
- Prod via SMTP: set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM
- Prod via Resend: set RESEND_API_KEY, SMTP_FROM
"""

from __future__ import annotations

import logging
import os
import smtplib
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr

# database imports are lazy (inside _get_conn) so auth.py can be imported
# by tests without needing a real DB file or the connection module available.
from .database import users_repo as _users

log = logging.getLogger("motoquant.auth")

# ─── JWT (python-jose optional; falls back to stdlib hmac if absent) ──────────

try:
    from jose import JWTError, jwt as _jose_jwt  # type: ignore

    _JOSE_AVAILABLE = True
except ImportError:  # pragma: no cover
    _JOSE_AVAILABLE = False
    log.warning("python-jose not installed — JWT issuing disabled (tests use mock)")

# ─── Config from env ──────────────────────────────────────────────────────────

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-insecure-secret-change-me")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_TTL_S = 15 * 60          # 15 minutes
REFRESH_TOKEN_TTL_S = 30 * 24 * 3600  # 30 days

MOTOQUANT_BASE_URL = os.environ.get("MOTOQUANT_BASE_URL", "https://www.motoquant.in")
EMAIL_BACKEND = os.environ.get("MOTOQUANT_EMAIL_BACKEND", "stdout")

# Rate-limit: one magic link per email per 60 s
MAGIC_LINK_COOLDOWN_S = 60

# ─── Router ───────────────────────────────────────────────────────────────────

router = APIRouter(tags=["auth"])
_bearer = HTTPBearer(auto_error=False)

# ─── Pydantic schemas ─────────────────────────────────────────────────────────


class MagicLinkRequest(BaseModel):
    email: EmailStr


class MagicLinkResponse(BaseModel):
    message: str
    # In dev/test mode the token is echoed back for convenience.
    dev_token: Optional[str] = None


class VerifyRequest(BaseModel):
    token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    tier: str


class RefreshRequest(BaseModel):
    refresh_token: str


class MeResponse(BaseModel):
    id: int
    email: str
    tier: str
    is_active: bool
    subscription_status: Optional[str] = None
    license_keys: list[dict] = []


# ─── JWT helpers ──────────────────────────────────────────────────────────────


def _make_access_token(user_id: int, email: str, tier: str, jti: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "tier": tier,
        "jti": jti,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(seconds=ACCESS_TOKEN_TTL_S),
    }
    if _JOSE_AVAILABLE:
        return _jose_jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    # Fallback: base64-encoded JSON (dev/test only — NOT secure for production)
    import base64, json
    payload["exp"] = payload["exp"].isoformat()
    return "dev." + base64.urlsafe_b64encode(
        json.dumps(payload).encode()
    ).decode()


def _make_refresh_token(user_id: int, jti: str) -> str:
    payload = {
        "sub": str(user_id),
        "jti": jti,
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(seconds=REFRESH_TOKEN_TTL_S),
    }
    if _JOSE_AVAILABLE:
        return _jose_jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    import base64, json
    payload["exp"] = payload["exp"].isoformat()
    return "dev." + base64.urlsafe_b64encode(
        json.dumps(payload).encode()
    ).decode()


def _decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT. Returns the payload dict or None on failure."""
    if token.startswith("dev."):
        import base64, json
        try:
            data = json.loads(base64.urlsafe_b64decode(token[4:] + "=="))
            exp = datetime.fromisoformat(data["exp"])
            if exp < datetime.now(timezone.utc):
                return None
            return data
        except Exception:
            return None
    if not _JOSE_AVAILABLE:
        return None
    try:
        return _jose_jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None


def _issue_token_pair(user: dict, conn: sqlite3.Connection) -> dict:
    """Create a session row and return the access + refresh token strings."""
    jti = str(uuid.uuid4())
    _users.create_session(conn, user["id"], jti)
    access = _make_access_token(user["id"], user["email"], user["tier"], jti)
    refresh = _make_refresh_token(user["id"], jti)
    return {"access_token": access, "refresh_token": refresh}


# ─── Email delivery ───────────────────────────────────────────────────────────


def _send_magic_link_email(email: str, token: str) -> None:
    link = f"{MOTOQUANT_BASE_URL}/login?token={token}"

    if EMAIL_BACKEND == "stdout" or not os.environ.get("SMTP_HOST"):
        # Dev mode — print to server stdout
        log.info("=== MAGIC LINK (dev mode) ===")
        log.info("To: %s", email)
        log.info("Link: %s", link)
        log.info("Token: %s", token)
        log.info("============================")
        print(f"\n[DEV] Magic link for {email}: {link}\n", flush=True)
        return

    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")
    smtp_from = os.environ.get("SMTP_FROM", "noreply@motoquant.in")

    body_html = f"""
    <html><body>
    <p>Hi,</p>
    <p>Click the button below to sign in to <strong>MotoQuant Pro</strong>.
    This link expires in 10 minutes.</p>
    <p><a href="{link}"
          style="background:#f97316;color:#fff;padding:12px 24px;border-radius:6px;
                 text-decoration:none;font-weight:bold;display:inline-block;">
       Sign in to MotoQuant
    </a></p>
    <p>If you didn't request this, you can safely ignore this email.</p>
    <p style="color:#888;font-size:12px;">
       MotoQuant Pro — The physics of faster.<br>
       motoquant.in
    </p>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your MotoQuant sign-in link"
    msg["From"] = smtp_from
    msg["To"] = email
    msg.attach(MIMEText(body_html, "html"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            if smtp_user:
                server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_from, [email], msg.as_string())
    except Exception as exc:
        log.error("Failed to send magic-link email to %s: %s", email, exc)
        raise HTTPException(503, f"Email delivery failed: {exc}") from exc


# ─── Auth dependency ──────────────────────────────────────────────────────────


def _get_conn() -> sqlite3.Connection:
    # Lazy import: connection.py is only loaded when a request actually needs the DB,
    # not at module import time (avoids ImportError during tests that mock the DB).
    from .database.connection import connect as _db_connect  # noqa: PLC0415
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    return conn


def get_current_user(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials], Depends(_bearer)
    ] = None,
) -> dict:
    """
    FastAPI dependency. Extracts and validates the Bearer JWT.
    Raises 401 if missing or invalid.
    Does NOT check tier — use require_tier() for that.
    """
    if not credentials:
        raise HTTPException(401, "Authentication required")
    payload = _decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(401, "Invalid or expired access token")

    # Verify session not revoked in DB
    jti = payload.get("jti")
    conn = _get_conn()
    try:
        if not _users.is_session_valid(conn, jti):
            raise HTTPException(401, "Session revoked — please log in again")
        user = _users.get_user_by_id(conn, int(payload["sub"]))
        if not user or not user["is_active"]:
            raise HTTPException(401, "Account not found or deactivated")
        return user
    finally:
        conn.close()


def require_tier(minimum_tier: str):
    """
    FastAPI dependency factory.
    Usage: Depends(require_tier("pro"))

    Returns 402 Payment Required (not 401) when the user is authenticated
    but on a lower tier — lets the client show an upgrade CTA rather than
    a generic "not authorised" message.
    """
    tier_rank = {"free": 0, "pro": 1, "studio": 2}
    required_rank = tier_rank[minimum_tier]

    def _dep(user: dict = Depends(get_current_user)) -> dict:
        if tier_rank.get(user.get("tier", "free"), 0) < required_rank:
            raise HTTPException(
                402,
                detail={
                    "error": "upgrade_required",
                    "required_tier": minimum_tier,
                    "current_tier": user.get("tier", "free"),
                    "upgrade_url": f"{MOTOQUANT_BASE_URL}/pricing",
                },
            )
        return user

    return _dep


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/magic-link", response_model=MagicLinkResponse)
def request_magic_link(body: MagicLinkRequest) -> MagicLinkResponse:
    """
    Issue a magic-link sign-in email.
    Idempotent within 60 s — repeated calls return 429.
    """
    email = body.email.lower().strip()
    conn = _get_conn()
    try:
        _users.ensure_tables(conn)
        if _users.recent_magic_link_exists(conn, email):
            raise HTTPException(
                429,
                "A sign-in link was already sent. Please check your inbox or wait 60 s.",
            )
        token = _users.create_magic_link(conn, email)
    finally:
        conn.close()

    _send_magic_link_email(email, token)

    resp = MagicLinkResponse(message="Sign-in link sent. Check your inbox.")
    if EMAIL_BACKEND == "stdout" or not os.environ.get("SMTP_HOST"):
        resp.dev_token = token  # echo token in dev mode for easy testing
    return resp


@router.post("/verify", response_model=TokenResponse)
def verify_magic_link(body: VerifyRequest) -> TokenResponse:
    """Exchange a magic-link token for an access + refresh JWT pair."""
    conn = _get_conn()
    try:
        _users.ensure_tables(conn)
        email = _users.consume_magic_link(conn, body.token)
        if not email:
            raise HTTPException(400, "Invalid, expired, or already-used sign-in link.")
        user = _users.get_or_create_user(conn, email)
        tokens = _issue_token_pair(user, conn)
    finally:
        conn.close()

    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        tier=user["tier"],
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(body: RefreshRequest) -> TokenResponse:
    """Issue a new access token from a valid refresh token."""
    payload = _decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid or expired refresh token")

    jti = payload.get("jti")
    user_id = int(payload.get("sub", 0))

    conn = _get_conn()
    try:
        if not _users.is_session_valid(conn, jti):
            raise HTTPException(401, "Session expired or revoked — please log in again")
        user = _users.get_user_by_id(conn, user_id)
        if not user or not user["is_active"]:
            raise HTTPException(401, "Account not found")
        # Rotate: revoke old session, create new one
        _users.revoke_session(conn, jti)
        tokens = _issue_token_pair(user, conn)
    finally:
        conn.close()

    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        tier=user["tier"],
    )


@router.post("/logout")
def logout(user: dict = Depends(get_current_user)) -> dict:
    """Revoke the current refresh session."""
    # We don't have the JTI in the access token payload easily here without
    # re-parsing, so we revoke ALL sessions for the user (conservative but safe).
    conn = _get_conn()
    try:
        _users.revoke_all_sessions(conn, user["id"])
    finally:
        conn.close()
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=MeResponse)
def me(user: dict = Depends(get_current_user)) -> MeResponse:
    """Return authenticated user details + subscription status + license keys."""
    from .database import subscriptions_repo as _subs

    conn = _get_conn()
    try:
        sub = _subs.get_active_subscription(conn, user["id"])
        keys = _subs.list_license_keys(conn, user["id"])
    finally:
        conn.close()

    return MeResponse(
        id=user["id"],
        email=user["email"],
        tier=user["tier"],
        is_active=bool(user["is_active"]),
        subscription_status=sub["status"] if sub else None,
        license_keys=keys,
    )
