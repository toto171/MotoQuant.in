"""
MotoQuant Pro -- Users Repository
=================================
CRUD layer for users, sessions, and magic_links tables.
All methods accept a sqlite3.Connection so callers control transactions.
"""

from __future__ import annotations

import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional


# --- helpers -------------------------------------------------------------------

def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _expires_iso(seconds: int) -> str:
    """Return UTC expiry in SQLite-compatible format (space separator, no tz suffix)."""
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


# --- USERS ---------------------------------------------------------------------

def get_user_by_email(conn: sqlite3.Connection, email: str) -> Optional[dict]:
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email.lower().strip(),)
    ).fetchone()
    return dict(row) if row else None


def get_user_by_id(conn: sqlite3.Connection, user_id: int) -> Optional[dict]:
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def get_or_create_user(conn: sqlite3.Connection, email: str) -> dict:
    """Return existing user or insert a new free-tier user."""
    email = email.lower().strip()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if row:
        return dict(row)
    conn.execute(
        "INSERT INTO users (email, tier, is_active) VALUES (?, 'free', 1)",
        (email,),
    )
    conn.commit()
    return dict(conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone())


def set_user_tier(conn: sqlite3.Connection, user_id: int, tier: str) -> None:
    assert tier in ("free", "pro", "studio")
    conn.execute(
        "UPDATE users SET tier = ?, updated_at = ? WHERE id = ?",
        (tier, _now_utc(), user_id),
    )
    conn.commit()


def set_razorpay_customer(conn: sqlite3.Connection, user_id: int, rzp_id: str) -> None:
    conn.execute(
        "UPDATE users SET razorpay_customer_id = ?, updated_at = ? WHERE id = ?",
        (rzp_id, _now_utc(), user_id),
    )
    conn.commit()


def deactivate_user(conn: sqlite3.Connection, user_id: int) -> None:
    conn.execute(
        "UPDATE users SET is_active = 0, updated_at = ? WHERE id = ?",
        (_now_utc(), user_id),
    )
    conn.commit()


# --- MAGIC LINKS ---------------------------------------------------------------

# Maximum one magic link issued per email per 60 seconds (rate-limit guard).
MAGIC_LINK_COOLDOWN_S = 60
# Token TTL -- 10 minutes.
MAGIC_LINK_TTL_S = 600


def recent_magic_link_exists(conn: sqlite3.Connection, email: str) -> bool:
    """True if a non-consumed, non-expired link was issued within the last 60 s.

    Uses SQLite datetime() to normalise timestamps -- handles both Python isoformat
    ('2026-04-24T11:41:20+00:00') and SQLite space-format ('2026-04-24 11:41:20').
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(seconds=MAGIC_LINK_COOLDOWN_S)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    row = conn.execute(
        """SELECT id FROM magic_links
           WHERE email = ? AND consumed = 0
             AND datetime(created_at) > datetime(?)
           ORDER BY created_at DESC LIMIT 1""",
        (email.lower().strip(), cutoff),
    ).fetchone()
    return row is not None


def create_magic_link(conn: sqlite3.Connection, email: str) -> str:
    """Create and persist a magic-link token. Returns the plaintext token."""
    email = email.lower().strip()
    token = secrets.token_urlsafe(32)
    token_hash = _sha256(token)
    expires_at = _expires_iso(MAGIC_LINK_TTL_S)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO magic_links (email, token_hash, expires_at, created_at) VALUES (?, ?, ?, ?)",
        (email, token_hash, expires_at, now),
    )
    conn.commit()
    return token


def consume_magic_link(conn: sqlite3.Connection, token: str) -> Optional[str]:
    """
    Validate and consume a magic-link token.
    Returns the email on success, None on invalid/expired/already-used token.
    Expiry check uses SQLite datetime() to handle both timestamp formats.
    """
    token_hash = _sha256(token)
    row = conn.execute(
        """SELECT id, email, consumed
           FROM magic_links
           WHERE token_hash = ?
             AND datetime(expires_at) > datetime('now')""",
        (token_hash,),
    ).fetchone()
    if not row:
        return None
    row = dict(row)
    if row["consumed"]:
        return None
    conn.execute(
        "UPDATE magic_links SET consumed = 1 WHERE id = ?", (row["id"],)
    )
    conn.commit()
    return row["email"]


# --- SESSIONS -----------------------------------------------------------------

# Refresh token lives 30 days.
REFRESH_TOKEN_TTL_S = 30 * 24 * 3600


def create_session(conn: sqlite3.Connection, user_id: int, jwt_id: str) -> dict:
    expires_at = _expires_iso(REFRESH_TOKEN_TTL_S)
    conn.execute(
        "INSERT INTO sessions (user_id, jwt_id, expires_at) VALUES (?, ?, ?)",
        (user_id, jwt_id, expires_at),
    )
    conn.commit()
    return {
        "user_id": user_id,
        "jwt_id": jwt_id,
        "expires_at": expires_at,
    }


def get_session_by_jti(conn: sqlite3.Connection, jwt_id: str) -> Optional[dict]:
    row = conn.execute(
        "SELECT * FROM sessions WHERE jwt_id = ?", (jwt_id,)
    ).fetchone()
    return dict(row) if row else None


def revoke_session(conn: sqlite3.Connection, jwt_id: str) -> None:
    conn.execute("UPDATE sessions SET revoked = 1 WHERE jwt_id = ?", (jwt_id,))
    conn.commit()


def revoke_all_sessions(conn: sqlite3.Connection, user_id: int) -> None:
    conn.execute(
        "UPDATE sessions SET revoked = 1 WHERE user_id = ?", (user_id,)
    )
    conn.commit()


def is_session_valid(conn: sqlite3.Connection, jwt_id: str) -> bool:
    """Return True iff session exists, is not revoked, and has not expired.
    Uses SQLite datetime() for expiry check -- handles both timestamp formats.
    """
    row = conn.execute(
        """SELECT revoked FROM sessions
           WHERE jwt_id = ?
             AND datetime(expires_at) > datetime('now')""",
        (jwt_id,),
    ).fetchone()
    if not row:
        return False  # not found or expired
    if row["revoked"]:
        return False
    return True


# --- ensure tables exist (called by auth.py at startup) -----------------------

def ensure_tables(conn: sqlite3.Connection) -> None:
    """
    Idempotently create all auth tables.
    This is belt-and-braces in case the DB was initialised before schema v4.
    """
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            email                   TEXT    NOT NULL UNIQUE,
            tier                    TEXT    NOT NULL DEFAULT 'free'
                                            CHECK(tier IN ('free','pro','studio')),
            is_active               INTEGER NOT NULL DEFAULT 1,
            razorpay_customer_id    TEXT,
            stripe_customer_id      TEXT,
            created_at              TEXT    DEFAULT (datetime('now','utc')),
            updated_at              TEXT    DEFAULT (datetime('now','utc'))
        );
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            jwt_id      TEXT    NOT NULL UNIQUE,
            expires_at  TEXT    NOT NULL,
            revoked     INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT    DEFAULT (datetime('now','utc'))
        );
        CREATE INDEX IF NOT EXISTS idx_sessions_jti    ON sessions(jwt_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_user   ON sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON sessions(expires_at);

        CREATE TABLE IF NOT EXISTS magic_links (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email       TEXT    NOT NULL,
            token_hash  TEXT    NOT NULL UNIQUE,
            expires_at  TEXT    NOT NULL,
            consumed    INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT    DEFAULT (datetime('now','utc'))
        );
        CREATE INDEX IF NOT EXISTS idx_magic_links_email ON magic_links(email);
        CREATE INDEX IF NOT EXISTS idx_magic_links_hash  ON magic_links(token_hash);
        """
    )
    conn.commit()
