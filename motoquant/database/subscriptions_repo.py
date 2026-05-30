"""
MotoQuant Pro — Subscriptions & License-Key Repository
========================================================
DB layer for subscriptions and license_keys tables.
All methods accept a sqlite3.Connection so callers control transactions.
"""

from __future__ import annotations

import hashlib
import sqlite3
import uuid
from datetime import datetime, timezone

# ─── Tier ordering (used for comparison) ──────────────────────────────────────

TIER_RANK = {"free": 0, "pro": 1, "studio": 2}

# Max license keys per tier
MAX_KEYS = {"free": 0, "pro": 1, "studio": 5}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


# ─── SUBSCRIPTIONS ────────────────────────────────────────────────────────────

def upsert_subscription(
    conn: sqlite3.Connection,
    *,
    user_id: int,
    razorpay_subscription_id: str,
    tier: str,
    status: str,
    current_period_end: str | None = None,
    plan_id: str | None = None,
    billing_cycle: str = "monthly",
) -> dict:
    """Insert or update a subscription row. Idempotent on rzp subscription_id."""
    assert tier in ("pro", "studio")
    assert status in (
        "created", "authenticated", "active", "past_due",
        "halted", "cancelled", "completed", "expired",
    )
    existing = conn.execute(
        "SELECT id FROM subscriptions WHERE razorpay_subscription_id = ?",
        (razorpay_subscription_id,),
    ).fetchone()

    now = _now_utc()
    if existing:
        conn.execute(
            """UPDATE subscriptions
               SET user_id=?, tier=?, status=?, current_period_end=?,
                   plan_id=?, billing_cycle=?, updated_at=?
               WHERE razorpay_subscription_id=?""",
            (user_id, tier, status, current_period_end, plan_id, billing_cycle,
             now, razorpay_subscription_id),
        )
    else:
        conn.execute(
            """INSERT INTO subscriptions
               (user_id, razorpay_subscription_id, tier, status,
                current_period_end, plan_id, billing_cycle)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, razorpay_subscription_id, tier, status,
             current_period_end, plan_id, billing_cycle),
        )
    conn.commit()
    return get_subscription_by_rzp_id(conn, razorpay_subscription_id)


def get_subscription_by_rzp_id(
    conn: sqlite3.Connection, razorpay_subscription_id: str
) -> dict | None:
    row = conn.execute(
        "SELECT * FROM subscriptions WHERE razorpay_subscription_id = ?",
        (razorpay_subscription_id,),
    ).fetchone()
    return dict(row) if row else None


def get_active_subscription(
    conn: sqlite3.Connection, user_id: int
) -> dict | None:
    """Return the most-recent active subscription for this user."""
    row = conn.execute(
        """SELECT * FROM subscriptions
           WHERE user_id = ? AND status IN ('active','authenticated')
           ORDER BY created_at DESC LIMIT 1""",
        (user_id,),
    ).fetchone()
    return dict(row) if row else None


def list_subscriptions_for_user(
    conn: sqlite3.Connection, user_id: int
) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM subscriptions WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    return [dict(r) for r in rows]


# ─── LICENSE KEYS ─────────────────────────────────────────────────────────────

def count_active_keys(conn: sqlite3.Connection, user_id: int) -> int:
    row = conn.execute(
        "SELECT COUNT(*) FROM license_keys WHERE user_id = ? AND revoked = 0",
        (user_id,),
    ).fetchone()
    return row[0] if row else 0


def create_license_key(conn: sqlite3.Connection, user_id: int, tier: str) -> str | None:
    """
    Generate and persist a new license key for the user.
    Returns the plaintext key (UUID4), or None if the per-tier quota is reached.
    """
    max_keys = MAX_KEYS.get(tier, 0)
    if max_keys == 0:
        return None  # free tier cannot hold keys
    if count_active_keys(conn, user_id) >= max_keys:
        return None  # quota reached

    plaintext = str(uuid.uuid4())
    key_hash = _sha256(plaintext)
    conn.execute(
        "INSERT INTO license_keys (user_id, key_hash) VALUES (?, ?)",
        (user_id, key_hash),
    )
    conn.commit()
    return plaintext


def validate_license_key(
    conn: sqlite3.Connection, plaintext_key: str, device_id: str | None = None
) -> dict | None:
    """
    Validate a license key. Updates last_seen_at and optionally binds device_id.
    Returns the license_keys row dict on success, None on invalid/revoked.
    """
    key_hash = _sha256(plaintext_key)
    row = conn.execute(
        "SELECT * FROM license_keys WHERE key_hash = ?", (key_hash,)
    ).fetchone()
    if not row:
        return None
    row = dict(row)
    if row["revoked"]:
        return None

    updates: list = [_now_utc()]
    sql_set = "last_seen_at = ?"

    # Bind device_id on first activation
    if device_id and not row["device_id"]:
        sql_set += ", device_id = ?, activated_at = ?"
        updates.extend([device_id, _now_utc()])
    updates.append(row["id"])

    conn.execute(f"UPDATE license_keys SET {sql_set} WHERE id = ?", updates)
    conn.commit()

    # Attach tier from user
    user_row = conn.execute(
        "SELECT tier FROM users WHERE id = ?", (row["user_id"],)
    ).fetchone()
    row["tier"] = user_row["tier"] if user_row else "free"
    row["last_seen_at"] = _now_utc()
    return row


def revoke_license_key(
    conn: sqlite3.Connection, key_id: int, user_id: int
) -> bool:
    """Revoke a key. Returns True if found and owned by user, False otherwise."""
    row = conn.execute(
        "SELECT id FROM license_keys WHERE id = ? AND user_id = ?",
        (key_id, user_id),
    ).fetchone()
    if not row:
        return False
    conn.execute(
        "UPDATE license_keys SET revoked = 1 WHERE id = ?", (key_id,)
    )
    conn.commit()
    return True


def list_license_keys(conn: sqlite3.Connection, user_id: int) -> list[dict]:
    rows = conn.execute(
        """SELECT id, device_id, activated_at, last_seen_at, revoked, created_at
           FROM license_keys WHERE user_id = ?
           ORDER BY created_at DESC""",
        (user_id,),
    ).fetchall()
    return [dict(r) for r in rows]


# ─── ensure tables (belt-and-braces for pre-v4 DBs) ──────────────────────────

def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS subscriptions (
            id                          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id                     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            razorpay_subscription_id    TEXT    NOT NULL UNIQUE,
            tier                        TEXT    NOT NULL CHECK(tier IN ('pro','studio')),
            status                      TEXT    NOT NULL DEFAULT 'created',
            current_period_end          TEXT,
            plan_id                     TEXT,
            billing_cycle               TEXT    DEFAULT 'monthly',
            created_at                  TEXT    DEFAULT (datetime('now','utc')),
            updated_at                  TEXT    DEFAULT (datetime('now','utc'))
        );
        CREATE INDEX IF NOT EXISTS idx_subs_user   ON subscriptions(user_id);
        CREATE INDEX IF NOT EXISTS idx_subs_rzp    ON subscriptions(razorpay_subscription_id);
        CREATE INDEX IF NOT EXISTS idx_subs_status ON subscriptions(status);

        CREATE TABLE IF NOT EXISTS license_keys (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            key_hash        TEXT    NOT NULL UNIQUE,
            device_id       TEXT,
            activated_at    TEXT,
            last_seen_at    TEXT,
            revoked         INTEGER NOT NULL DEFAULT 0,
            created_at      TEXT    DEFAULT (datetime('now','utc'))
        );
        CREATE INDEX IF NOT EXISTS idx_license_user ON license_keys(user_id);
        CREATE INDEX IF NOT EXISTS idx_license_hash ON license_keys(key_hash);
        """
    )
    conn.commit()
