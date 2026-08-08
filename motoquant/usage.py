"""Free-tier simulation metering — the freemium conversion lever.

Records one row per (identity, UTC day) in the ``sim_usage`` table and
answers "has this caller exceeded the free daily sim quota?".

Design constraints (mirrors the auth/payments house style):
- Pure stdlib + sqlite3. No FastAPI imports here — the HTTP dependency that
  wires this into /api/simulate* lives in api.py so this module stays
  unit-testable against a bare connection.
- Metering ALWAYS records (paid tiers included — the counts are the
  analytics feed), but only ever *blocks* free-tier callers, and only when
  MOTOQUANT_BILLING_ENFORCE is truthy. During the open beta the quota is
  advisory: the response can show "N free sims left today" without ever
  rejecting a request.
- Atomic increment via INSERT .. ON CONFLICT DO UPDATE so two concurrent
  requests can't lose a count.

Identity resolution (done by the caller in api.py):
  authenticated  -> "user:<id>"
  anonymous      -> "anon:<sha256(client session id or IP)[:16]>"
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import os
import sqlite3
from dataclasses import dataclass

# Quota knobs — env-overridable so ops can tune without a deploy.
FREE_DAILY_SIMS = int(os.environ.get("MOTOQUANT_FREE_DAILY_SIMS", "30"))

# Tiers that are never blocked. Counts are still recorded for analytics.
_UNLIMITED_TIERS = {"pro", "studio"}


@dataclass
class UsageStatus:
    """Result of one metered request."""

    count: int
    limit: int | None  # None == unlimited (paid tier)
    allowed: bool

    @property
    def remaining(self) -> int | None:
        if self.limit is None:
            return None
        return max(0, self.limit - self.count)


def anon_identity(raw: str) -> str:
    """Stable, non-reversible identity for anonymous callers.

    ``raw`` is whatever the transport layer has (client session id header,
    else the client IP). Hashed so raw IPs never land in the DB — keeps the
    privacy-page promise that we don't store IP addresses.
    """
    digest = hashlib.sha256((raw or "unknown").encode("utf-8")).hexdigest()[:16]
    return f"anon:{digest}"


def user_identity(user_id: int) -> str:
    return f"user:{int(user_id)}"


def ensure_table(conn: sqlite3.Connection) -> None:
    """Create the sim_usage table if missing (guarded, idempotent).

    Deliberately NOT memoized: id(conn)-keyed caches break when CPython
    reuses object ids after GC, and CREATE TABLE IF NOT EXISTS is cheap.
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sim_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            identity TEXT NOT NULL,
            day TEXT NOT NULL,
            count INTEGER NOT NULL DEFAULT 0,
            UNIQUE(identity, day)
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sim_usage_day ON sim_usage(day)")
    conn.commit()


def _today() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")


def record_and_check(
    conn: sqlite3.Connection,
    identity: str,
    tier: str = "free",
    day: str | None = None,
    n: int = 1,
) -> UsageStatus:
    """Charge ``n`` full sims to ``identity`` today and report quota state.

    ``n`` exists because several callers spend more than one RK4 run per
    request — /api/simulate/compare runs two, a chat turn's rank/choose
    dispatch runs up to 25, a heavy op (optimizer / autotune) costs a
    nominal batch. Charging them in ONE atomic statement keeps the increment
    lossless under concurrency (a Python-side loop would open the same race
    the ON CONFLICT clause exists to close) and costs one round trip
    instead of n.

    Never raises on quota — the caller decides whether ``allowed=False``
    becomes an HTTP 402 (enforced mode) or just a response header (beta).
    """
    ensure_table(conn)
    day = day or _today()
    n = max(1, int(n))
    row = conn.execute(
        """
        INSERT INTO sim_usage (identity, day, count) VALUES (?, ?, ?)
        ON CONFLICT(identity, day) DO UPDATE SET count = count + ?
        RETURNING count
        """,
        (identity, day, n, n),
    ).fetchone()
    conn.commit()
    count = int(row[0])

    if (tier or "free").lower() in _UNLIMITED_TIERS:
        return UsageStatus(count=count, limit=None, allowed=True)
    return UsageStatus(
        count=count, limit=FREE_DAILY_SIMS, allowed=count <= FREE_DAILY_SIMS
    )


def peek(conn: sqlite3.Connection, identity: str, day: str | None = None) -> int:
    """Current count without incrementing (for /api/me style displays)."""
    ensure_table(conn)
    day = day or _today()
    row = conn.execute(
        "SELECT count FROM sim_usage WHERE identity = ? AND day = ?",
        (identity, day),
    ).fetchone()
    return int(row[0]) if row else 0
