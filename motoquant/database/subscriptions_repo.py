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


def _sqlite_utc_now() -> str:
    # SQLite's own "YYYY-MM-DD HH:MM:SS" (UTC) format, so string comparison
    # against datetime('now', ...) is exact. The schema's legacy column default
    # datetime('now','utc') DOUBLE-shifts on non-UTC hosts ('now' is already
    # UTC; the modifier re-interprets it as localtime), so time-window queries
    # must never rely on the default — write created_at explicitly with this.
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


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
    provider: str = "razorpay",
) -> dict:
    """Insert or update a subscription row, idempotent on the provider's
    subscription id. NOTE: the razorpay_subscription_id column is legacy-named
    but stores the subscription id for ANY provider (razorpay sub_…, stripe
    sub_…); the provider column disambiguates."""
    assert provider in ("razorpay", "stripe", "paypal")
    assert tier in ("pro", "studio")
    assert status in (
        "created",
        "authenticated",
        "active",
        "past_due",
        "halted",
        "cancelled",
        "completed",
        "expired",
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
                   plan_id=?, billing_cycle=?, provider=?, updated_at=?
               WHERE razorpay_subscription_id=?""",
            (
                user_id,
                tier,
                status,
                current_period_end,
                plan_id,
                billing_cycle,
                provider,
                now,
                razorpay_subscription_id,
            ),
        )
    else:
        conn.execute(
            """INSERT INTO subscriptions
               (user_id, razorpay_subscription_id, tier, status,
                current_period_end, plan_id, billing_cycle, provider,
                created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                razorpay_subscription_id,
                tier,
                status,
                current_period_end,
                plan_id,
                billing_cycle,
                provider,
                _sqlite_utc_now(),
            ),
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


def get_active_subscription(conn: sqlite3.Connection, user_id: int) -> dict | None:
    """Return the most-recent active subscription for this user."""
    row = conn.execute(
        """SELECT * FROM subscriptions
           WHERE user_id = ? AND status IN ('active','authenticated')
           ORDER BY created_at DESC LIMIT 1""",
        (user_id,),
    ).fetchone()
    return dict(row) if row else None


def get_recent_created_subscription(
    conn: sqlite3.Connection, user_id: int, max_age_min: int = 30
) -> dict | None:
    """Return the newest still-open checkout placeholder (status "created")
    younger than max_age_min minutes, or None. created_at is written
    explicitly by upsert_subscription via _sqlite_utc_now() (true Python UTC
    in SQLite's space-separated format) — NOT the column default, whose
    datetime('now','utc') double-shifts on non-UTC hosts — so comparing it
    against datetime('now', ...) (always UTC in SQLite) is host-TZ-safe.
    Used by the checkout routes to time-box the "one open checkout at a
    time" 409 guard."""
    row = conn.execute(
        """SELECT * FROM subscriptions
           WHERE user_id = ? AND status = 'created'
             AND created_at >= datetime('now', ?)
           ORDER BY created_at DESC LIMIT 1""",
        (user_id, f"-{int(max_age_min)} minutes"),
    ).fetchone()
    return dict(row) if row else None


def resolve_created_checkout(conn: sqlite3.Connection, session_id: str) -> None:
    """Delete the Stripe checkout placeholder row (the cs_… session id was
    parked in the razorpay_subscription_id column at checkout time) once
    checkout.session.completed has upserted the REAL subscription row.
    Status-scoped so a real subscription row can never be deleted."""
    conn.execute(
        "DELETE FROM subscriptions "
        "WHERE razorpay_subscription_id = ? AND status = 'created'",
        (session_id,),
    )
    conn.commit()


def list_subscriptions_for_user(conn: sqlite3.Connection, user_id: int) -> list[dict]:
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


class DeviceMismatchError(Exception):
    """A license key already activated on one device was presented from a
    different device_id. The reset path is revoke + regenerate."""


def validate_license_key(
    conn: sqlite3.Connection, plaintext_key: str, device_id: str | None = None
) -> dict | None:
    """
    Validate a license key. Updates last_seen_at and optionally binds device_id.
    Returns the license_keys row dict on success, None on invalid/revoked.

    Device binding is ENFORCED (July 2026 — was write-only before): once a
    key is bound, EVERY validate must present the bound device_id — a
    different id AND an omitted id both raise DeviceMismatchError, leaving
    the row untouched (no last_seen bump). The omit-device_id tolerance
    existed for pre-device-reporting desktop builds; the desktop app was
    scrapped July 6 2026 (ADR-0005), so an id-less call against a bound key
    is a shared/scripted key, not a legacy client. A never-bound key
    (device_id NULL) still validates without one — binding happens on the
    first device-carrying call. Reset path: revoke + regenerate.
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

    if row["device_id"] and device_id != row["device_id"]:
        raise DeviceMismatchError("License key is already activated on another device")

    # Refuse keys whose owning account has been deactivated — BEFORE the
    # last-seen bump / device bind, so an invalid key leaves the row untouched
    # exactly like the revoked path does. (2026-08-11 audit: a banned/closed
    # account's device-bound keys kept validating forever, because only the
    # key's own revoked flag was checked.)
    user_row = conn.execute(
        "SELECT tier, is_active FROM users WHERE id = ?", (row["user_id"],)
    ).fetchone()
    if user_row is not None and not user_row["is_active"]:
        return None

    # Refuse keys whose owner no longer holds a paid tier — a cancelled-and-
    # downgraded subscriber must stop validating (the public /refunds page
    # promises invalidation within 24h). Like the is_active check above, this
    # runs BEFORE the last-seen bump / device bind so the row stays untouched.
    if user_row is not None and user_row["tier"] not in ("pro", "studio"):
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
    row["tier"] = user_row["tier"] if user_row else "free"
    row["last_seen_at"] = _now_utc()
    return row


def revoke_license_key(conn: sqlite3.Connection, key_id: int, user_id: int) -> bool:
    """Revoke a key. Returns True if found and owned by user, False otherwise."""
    row = conn.execute(
        "SELECT id FROM license_keys WHERE id = ? AND user_id = ?",
        (key_id, user_id),
    ).fetchone()
    if not row:
        return False
    conn.execute("UPDATE license_keys SET revoked = 1 WHERE id = ?", (key_id,))
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
            provider                    TEXT    NOT NULL DEFAULT 'razorpay',
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

        CREATE TABLE IF NOT EXISTS payment_events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            provider    TEXT    NOT NULL,
            event_id    TEXT    NOT NULL,
            event_type  TEXT,
            payload     TEXT,
            received_at TEXT    DEFAULT (datetime('now','utc')),
            UNIQUE(provider, event_id)
        );
        CREATE INDEX IF NOT EXISTS idx_payevents_provider ON payment_events(provider, event_id);
        """
    )
    conn.commit()

    # ── guarded ALTER for subscriptions tables created before June 2026 ──
    try:
        conn.execute(
            "ALTER TABLE subscriptions ADD COLUMN provider TEXT NOT NULL DEFAULT 'razorpay'"
        )
        conn.commit()
    except sqlite3.OperationalError as exc:
        # Only swallow the expected "column already exists" — anything else
        # (locked DB, disk error, malformed schema) should surface, not be
        # silently eaten as a no-op migration.
        if "duplicate column" not in str(exc).lower():
            raise


# ─── PAYMENT EVENT LEDGER (webhook idempotency, June 2026) ────────────────────


def record_payment_event(
    conn: sqlite3.Connection,
    provider: str,
    event_id: str,
    event_type: str | None = None,
    payload: str | None = None,
) -> bool:
    """Insert a webhook event row. Returns True if this is the FIRST time the
    (provider, event_id) pair is seen, False on duplicate delivery — callers
    use this as the idempotency gate."""
    try:
        conn.execute(
            "INSERT INTO payment_events (provider, event_id, event_type, payload) "
            "VALUES (?, ?, ?, ?)",
            (provider, event_id, event_type, (payload or "")[:10_000]),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def delete_payment_event(
    conn: sqlite3.Connection, provider: str, event_id: str
) -> None:
    """Un-record a webhook event whose side effects FAILED to apply.

    The ledger insert commits before the handler runs, so without this
    compensation a mid-apply failure leaves the event marked processed and
    every provider retry is swallowed as "duplicate" — the event is lost
    forever (2026-08-11 audit). Callers delete the row and answer non-2xx so
    the provider redelivers onto a clean slate.
    """
    conn.execute(
        "DELETE FROM payment_events WHERE provider = ? AND event_id = ?",
        (provider, event_id),
    )
    conn.commit()
