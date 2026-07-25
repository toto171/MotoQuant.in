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

import hashlib
import hmac
import logging
import os
import secrets
import smtplib
import sqlite3
import time
import uuid
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field

# database imports are lazy (inside _get_conn) so auth.py can be imported
# by tests without needing a real DB file or the connection module available.
from .database import users_repo as _users
from .ratelimit import rate_limit

log = logging.getLogger("motoquant.auth")

# ─── JWT (PyJWT optional; falls back to stdlib hmac if absent) ────────────────

try:
    import jwt as _pyjwt  # type: ignore

    _JWT_AVAILABLE = True
except ImportError:  # pragma: no cover
    _JWT_AVAILABLE = False
    log.warning("PyJWT not installed — JWT issuing disabled (tests use mock)")

# ─── Config from env ──────────────────────────────────────────────────────────

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-insecure-secret-change-me")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_TTL_S = 15 * 60  # 15 minutes
REFRESH_TOKEN_TTL_S = 30 * 24 * 3600  # 30 days

MOTOQUANT_BASE_URL = os.environ.get("MOTOQUANT_BASE_URL", "https://www.motoquant.in")
EMAIL_BACKEND = os.environ.get("MOTOQUANT_EMAIL_BACKEND", "stdout")

# "Am I running on the deployed host?" Render always sets these. Used to make
# sure the dev-convenience magic-link echo NEVER fires in production (see
# request_magic_link) — echoing the token in the HTTP response on a prod box
# without SMTP configured is an account-takeover vector.
IN_DEPLOYED_ENV = bool(
    os.environ.get("RENDER") or os.environ.get("RENDER_EXTERNAL_URL")
)

# Rate-limit: one magic link per email per 60 s
MAGIC_LINK_COOLDOWN_S = 60

# ─── Billing enforcement (freemium-beta switch) ───────────────────────────────
# When FALSE (the default — open-beta posture), require_tier() lets every
# request through: authenticated users are attached for attribution, anonymous
# users get an empty dict. Tier checks only bite when MOTOQUANT_BILLING_ENFORCE
# is truthy — flip it in the Render dashboard at commercial rollout.
# Tests patch motoquant.auth.BILLING_ENFORCE directly (read at request time).
BILLING_ENFORCE = os.environ.get(
    "MOTOQUANT_BILLING_ENFORCE", "false"
).strip().lower() in ("1", "true", "yes", "on")

# Guard against shipping the public default JWT secret. When billing is
# enforced (real commercial mode), forgeable tokens = free paid upgrades and
# cross-account reads, so refuse to start rather than sign with a known key.
# During the open beta (BILLING_ENFORCE off) auth is advisory, so we only warn
# loudly — hard-failing here would take down the live beta if the operator
# hasn't set JWT_SECRET yet (it's a documented pre-commercial TODO).
_JWT_SECRET_IS_DEFAULT = JWT_SECRET == "dev-insecure-secret-change-me"
if _JWT_SECRET_IS_DEFAULT:
    if BILLING_ENFORCE:
        raise RuntimeError(
            "JWT_SECRET is the public default while MOTOQUANT_BILLING_ENFORCE is on. "
            "Set JWT_SECRET to 32+ random bytes before enabling billing — the default "
            "lets anyone forge access tokens and upgrade themselves for free."
        )
    log.warning(
        "JWT_SECRET is the insecure public default — acceptable only for dev/test. "
        "Set a real JWT_SECRET before any real deployment; tokens are forgeable."
    )

# Password auth — stdlib scrypt (RFC 7914), zero external hashing deps.
_SCRYPT_N = 16384
_SCRYPT_R = 8
_SCRYPT_P = 1
PASSWORD_MIN_LEN = 8
PASSWORD_MAX_LEN = 128

# In-process failed-login limiter: max 8 failures / 15 min / email.
# Prod runs a single uvicorn worker, so in-memory state is sufficient;
# swap for a DB-backed counter if workers ever scale out.
_LOGIN_FAIL_WINDOW_S = 900
_LOGIN_FAIL_MAX = 8
_failed_logins: dict[str, list[float]] = {}

# ─── Router ───────────────────────────────────────────────────────────────────

router = APIRouter(tags=["auth"])
_bearer = HTTPBearer(auto_error=False)

# ─── Pydantic schemas ─────────────────────────────────────────────────────────


class MagicLinkRequest(BaseModel):
    email: EmailStr


class MagicLinkResponse(BaseModel):
    message: str
    # In dev/test mode the token is echoed back for convenience.
    dev_token: str | None = None


class VerifyRequest(BaseModel):
    token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    tier: str


class RefreshRequest(BaseModel):
    refresh_token: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN_LEN, max_length=PASSWORD_MAX_LEN)


class PasswordLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=PASSWORD_MAX_LEN)


class ChangePasswordRequest(BaseModel):
    current_password: str | None = None
    new_password: str = Field(min_length=PASSWORD_MIN_LEN, max_length=PASSWORD_MAX_LEN)


class MeResponse(BaseModel):
    id: int
    email: str
    tier: str
    is_active: bool
    email_verified: bool = False
    has_password: bool = False
    subscription_status: str | None = None
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
    if _JWT_AVAILABLE:
        return _pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    # Fallback: base64-encoded JSON (dev/test only — NOT secure for production)
    import base64
    import json

    payload["exp"] = payload["exp"].isoformat()
    return "dev." + base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def _make_refresh_token(user_id: int, jti: str) -> str:
    payload = {
        "sub": str(user_id),
        "jti": jti,
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(seconds=REFRESH_TOKEN_TTL_S),
    }
    if _JWT_AVAILABLE:
        return _pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    import base64
    import json

    payload["exp"] = payload["exp"].isoformat()
    return "dev." + base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def _decode_token(token: str) -> dict | None:
    """Decode and verify a JWT. Returns the payload dict or None on failure."""
    # The unsigned "dev." token format is ONLY honoured when the JWT library
    # is unavailable (the same condition under which it is issued). Before
    # 2026-07-02 this branch ran unconditionally, so in production (JWT lib
    # present) an attacker could hand-craft a "dev." token with an
    # arbitrary payload and skip signature verification entirely.
    if token.startswith("dev.") and not _JWT_AVAILABLE:
        import base64
        import json

        try:
            data = json.loads(base64.urlsafe_b64decode(token[4:] + "=="))
            exp = datetime.fromisoformat(data["exp"])
            if exp < datetime.now(timezone.utc):
                return None
            return data
        except Exception:
            return None
    if not _JWT_AVAILABLE:
        return None
    try:
        return _pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except _pyjwt.PyJWTError:
        return None


def _issue_token_pair(user: dict, conn: sqlite3.Connection) -> dict:
    """Create a session row and return the access + refresh token strings."""
    jti = str(uuid.uuid4())
    _users.create_session(conn, user["id"], jti)
    access = _make_access_token(user["id"], user["email"], user["tier"], jti)
    refresh = _make_refresh_token(user["id"], jti)
    return {"access_token": access, "refresh_token": refresh}


# ─── Password hashing (stdlib scrypt) ─────────────────────────────────────────


def hash_password(password: str) -> str:
    """Hash a password with scrypt. Format: scrypt$N$r$p$salt_hex$hash_hex."""
    salt = secrets.token_bytes(16)
    dk = hashlib.scrypt(
        password.encode(),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=64,
    )
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${salt.hex()}${dk.hex()}"


_DUMMY_PASSWORD_HASH: str | None = None


def _dummy_hash() -> str:
    """A well-formed scrypt hash used to burn equivalent CPU when the target
    account doesn't exist, so login timing can't enumerate registered emails.
    Computed once, lazily (one scrypt), then cached."""
    global _DUMMY_PASSWORD_HASH
    if _DUMMY_PASSWORD_HASH is None:
        _DUMMY_PASSWORD_HASH = hash_password("mq-constant-time-equalizer")
    return _DUMMY_PASSWORD_HASH


def verify_password(password: str, stored: str | None) -> bool:
    """Constant-time scrypt verification. False on any malformed input.

    Always runs exactly one scrypt — against a dummy hash when ``stored`` is
    absent/malformed — so a non-existent (or password-less) account is
    indistinguishable from a wrong password by response timing. Only a real,
    well-formed stored hash can ever return True.
    """
    valid_stored = bool(stored) and stored.startswith("scrypt$")
    target = stored if valid_stored else _dummy_hash()
    try:
        _, n, r, p_, salt_hex, hash_hex = target.split("$")
        dk = hashlib.scrypt(
            password.encode(),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p_),
            dklen=len(hash_hex) // 2,
        )
        match = hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False
    return match and valid_stored


def _login_locked(email: str) -> bool:
    now = time.time()
    attempts = [
        t for t in _failed_logins.get(email, []) if now - t < _LOGIN_FAIL_WINDOW_S
    ]
    _failed_logins[email] = attempts
    return len(attempts) >= _LOGIN_FAIL_MAX


# Bound the tracker so an attacker hammering distinct (never-succeeding)
# emails can't grow it without limit — keys are otherwise only removed on a
# successful login.
_MAX_TRACKED_EMAILS = 4096


def _register_login_failure(email: str) -> None:
    now = time.time()
    if len(_failed_logins) >= _MAX_TRACKED_EMAILS and email not in _failed_logins:
        # Drop fully-expired entries first; if the table is still full it's a
        # distinct-email flood, so clear it (correctness is unaffected — this
        # only forgets in-window failure counts under active abuse).
        for k in [
            k
            for k, v in _failed_logins.items()
            if not v or now - v[-1] > _LOGIN_FAIL_WINDOW_S
        ]:
            del _failed_logins[k]
        if len(_failed_logins) >= _MAX_TRACKED_EMAILS:
            _failed_logins.clear()
    _failed_logins.setdefault(email, []).append(now)


def _clear_login_failures(email: str) -> None:
    _failed_logins.pop(email, None)


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
    from .database.connection import row_conn  # noqa: PLC0415

    return row_conn()


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer)
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
        if not _users.is_session_valid(conn, jti, int(payload["sub"])):
            raise HTTPException(401, "Session revoked — please log in again")
        user = _users.get_user_by_id(conn, int(payload["sub"]))
        if not user or not user["is_active"]:
            raise HTTPException(401, "Account not found or deactivated")
        return user
    finally:
        conn.close()


def get_optional_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer)
    ] = None,
) -> dict | None:
    """
    FastAPI dependency. Like get_current_user but NEVER raises — returns the
    user dict when a valid Bearer token is present, None otherwise. Used for
    attribution on routes that stay open during the freemium beta.
    """
    if not credentials:
        return None
    payload = _decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        return None
    jti = payload.get("jti")
    try:
        conn = _get_conn()
    except Exception:
        return None
    try:
        if not _users.is_session_valid(conn, jti, int(payload["sub"])):
            return None
        user = _users.get_user_by_id(conn, int(payload["sub"]))
        if not user or not user["is_active"]:
            return None
        return user
    finally:
        conn.close()


def require_tier(minimum_tier: str):
    """
    FastAPI dependency factory.
    Usage: Depends(require_tier("pro"))

    Freemium-beta behaviour (BILLING_ENFORCE falsy — the default): every
    request passes. Authenticated users are returned for attribution;
    anonymous requests get an empty dict.

    Enforced behaviour (MOTOQUANT_BILLING_ENFORCE truthy): 401 when
    unauthenticated; 402 Payment Required (not 401) when authenticated but
    on a lower tier — lets the client show an upgrade CTA rather than a
    generic "not authorised" message.
    """
    tier_rank = {"free": 0, "pro": 1, "studio": 2}
    required_rank = tier_rank[minimum_tier]

    def _dep(user: dict | None = Depends(get_optional_user)) -> dict:
        if not BILLING_ENFORCE:
            return user or {}
        if user is None:
            raise HTTPException(401, "Authentication required")
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
#
# Per-IP rate limits on the credential-burning routes (2026-07-25 audit). The
# auth router was mounted with no throttle at all, and the only existing brake
# (_login_locked) keys on the SUBMITTED EMAIL, so rotating the address defeats
# it while every request still pays a full scrypt (~53 ms here, materially more
# on Render's 0.5-CPU free tier) — verify_password deliberately runs one even
# for a non-existent account, which is correct for timing-safety but makes an
# unauthenticated flood a cheap CPU-exhaustion lever against the whole API.
# /magic-link additionally SENDS AN EMAIL per call.
#
# Deliberately NOT limited: /me, /refresh and /logout. They are cheap, and a
# signed-in client polls them — throttling those would break the UI without
# closing an abuse channel. Limits follow the existing house convention
# (license-key/validate is 10/60 s).
_rl_login = rate_limit("auth_login", 10, 60.0)
_rl_register = rate_limit("auth_register", 5, 60.0)
_rl_magic = rate_limit("auth_magic_link", 5, 60.0)
_rl_verify = rate_limit("auth_verify", 10, 60.0)
_rl_pwchange = rate_limit("auth_password_change", 10, 60.0)


@router.post(
    "/magic-link",
    response_model=MagicLinkResponse,
    dependencies=[Depends(_rl_magic)],
)
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
    # Echo the token ONLY in a genuine local dev/test run — never on a deployed
    # host. Previously this also fired whenever SMTP_HOST was unset, so a prod
    # box with email not-yet-configured (the beta state) returned the sign-in
    # token straight to any caller: request a link for any address, read the
    # token back, verify it → full account takeover with no inbox access.
    if EMAIL_BACKEND == "stdout" and not IN_DEPLOYED_ENV:
        resp.dev_token = token
    return resp


@router.post(
    "/verify", response_model=TokenResponse, dependencies=[Depends(_rl_verify)]
)
def verify_magic_link(body: VerifyRequest) -> TokenResponse:
    """Exchange a magic-link token for an access + refresh JWT pair."""
    conn = _get_conn()
    try:
        _users.ensure_tables(conn)
        email = _users.consume_magic_link(conn, body.token)
        if not email:
            raise HTTPException(400, "Invalid, expired, or already-used sign-in link.")
        user = _users.get_or_create_user(conn, email)
        if not user.get("email_verified"):
            # Consuming a magic link proves inbox ownership.
            _users.mark_email_verified(conn, user["id"])
            user["email_verified"] = 1
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
        if not _users.is_session_valid(conn, jti, user_id):
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
        email_verified=bool(user.get("email_verified", 0)),
        has_password=bool(user.get("password_hash")),
        subscription_status=sub["status"] if sub else None,
        license_keys=keys,
    )


# ─── Password auth endpoints (Phase 6, June 2026) ─────────────────────────────


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    dependencies=[Depends(_rl_register)],
)
def register(body: RegisterRequest) -> TokenResponse:
    """
    Create an account with email + password and sign in immediately.

    Email ownership is NOT verified at registration (open-beta posture) —
    the email_verified flag flips to 1 the first time a magic link for the
    address is consumed. Existing accounts (including passwordless
    magic-link accounts) are never overwritten — 409.
    """
    email = body.email.lower().strip()
    conn = _get_conn()
    try:
        _users.ensure_tables(conn)
        if _users.get_user_by_email(conn, email):
            raise HTTPException(
                409,
                "An account with this email already exists. Sign in instead "
                "(use a magic link if you never set a password).",
            )
        user = _users.create_user_with_password(
            conn, email, hash_password(body.password)
        )
        tokens = _issue_token_pair(user, conn)
    finally:
        conn.close()

    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        tier=user["tier"],
    )


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(_rl_login)])
def password_login(body: PasswordLoginRequest) -> TokenResponse:
    """
    Email + password sign-in. Returns the same JWT pair as /verify.
    Deliberately generic 401 — no user-enumeration signal.
    """
    email = body.email.lower().strip()
    if _login_locked(email):
        raise HTTPException(
            429,
            "Too many failed sign-in attempts. Try again in 15 minutes "
            "or sign in with a magic link.",
        )

    conn = _get_conn()
    try:
        _users.ensure_tables(conn)
        user = _users.get_user_by_email(conn, email)
        # Always call verify_password (it runs one scrypt even for a missing
        # account) instead of short-circuiting on `user` — otherwise the fast
        # no-user path is timing-distinguishable from the slow wrong-password
        # path, enumerating registered emails.
        pw_ok = verify_password(
            body.password, user.get("password_hash") if user else None
        )
        ok = bool(user and user.get("is_active") and pw_ok)
        if not ok:
            _register_login_failure(email)
            raise HTTPException(401, "Invalid email or password.")
        _clear_login_failures(email)
        tokens = _issue_token_pair(user, conn)
    finally:
        conn.close()

    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        tier=user["tier"],
    )


@router.post("/password/change", dependencies=[Depends(_rl_pwchange)])
def change_password(
    body: ChangePasswordRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    """
    Set or change the account password.

    Accounts that already hold a password must supply the current one.
    Magic-link-only accounts set their first password directly — the bearer
    token already proves control of the inbox.
    """
    conn = _get_conn()
    try:
        db_user = _users.get_user_by_id(conn, user["id"]) or {}
        if db_user.get("password_hash"):
            if not body.current_password or not verify_password(
                body.current_password, db_user["password_hash"]
            ):
                raise HTTPException(403, "Current password is incorrect.")
        _users.set_password(conn, user["id"], hash_password(body.new_password))
    finally:
        conn.close()
    return {"message": "Password updated."}
