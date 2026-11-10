#!/usr/bin/env python3
"""patch_2026_11_09_remove_billing.py -- drop the retired billing schema.

MotoQuant is open source: there are no tiers, subscriptions, license keys or
free-tier quota. Fresh databases no longer create any of that, but databases
that pre-date the change still carry it. This patch removes:

  tables   subscriptions, license_keys, payment_events, sim_usage
  columns  users.tier, users.razorpay_customer_id, users.stripe_customer_id

Accounts, sessions, magic links and saved runs are untouched.

SQLite cannot drop a column that an index covers, so any index on a doomed
column is dropped first. ``ALTER TABLE ... DROP COLUMN`` needs SQLite >= 3.35.

Idempotent: a second run finds nothing to do and reports 0 changes.

Usage:
    python scripts/patch_2026_11_09_remove_billing.py [path/to/motoquant.db]
    (defaults to $MOTOQUANT_DB, then ./motoquant.db)
"""

from __future__ import annotations

import os
import re
import sqlite3
import sys

DROP_TABLES = ("subscriptions", "license_keys", "payment_events", "sim_usage")
DROP_USER_COLUMNS = ("tier", "razorpay_customer_id", "stripe_customer_id")


def _tables(conn: sqlite3.Connection) -> set[str]:
    return {
        r[0]
        for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }


def _indexes_on(conn: sqlite3.Connection, table: str, column: str) -> list[str]:
    """Explicit (non-autoindex) indexes on ``table`` that cover ``column``."""
    out = []
    for row in conn.execute(f'PRAGMA index_list("{table}")').fetchall():
        name = row[1]
        if name.startswith("sqlite_autoindex"):
            continue
        cols = [c[2] for c in conn.execute(f'PRAGMA index_info("{name}")').fetchall()]
        if column in cols:
            out.append(name)
    return out


def apply(db_path: str, verbose: bool = False) -> dict:
    """Apply the patch to ``db_path``. Returns a summary dict."""
    if sqlite3.sqlite_version_info < (3, 35, 0):
        raise RuntimeError(
            f"SQLite {sqlite3.sqlite_version} cannot DROP COLUMN (need >= 3.35)"
        )
    conn = sqlite3.connect(db_path)
    dropped_tables: list[str] = []
    dropped_columns: list[str] = []
    dropped_indexes: list[str] = []
    try:
        for table in DROP_TABLES:
            if table in _tables(conn):
                conn.execute(f'DROP TABLE "{table}"')
                dropped_tables.append(table)
                if verbose:
                    print(f"  DROP TABLE  {table}")

        if "users" in _tables(conn):
            have = {r[1] for r in conn.execute('PRAGMA table_info("users")')}
            for col in DROP_USER_COLUMNS:
                if col not in have:
                    continue
                if not re.fullmatch(r"[a-z_]+", col):  # constants, belt and braces
                    raise ValueError(col)
                for idx in _indexes_on(conn, "users", col):
                    conn.execute(f'DROP INDEX "{idx}"')
                    dropped_indexes.append(idx)
                    if verbose:
                        print(f"  DROP INDEX  {idx}")
                conn.execute(f'ALTER TABLE "users" DROP COLUMN "{col}"')
                dropped_columns.append(f"users.{col}")
                if verbose:
                    print(f"  DROP COLUMN users.{col}")
        conn.commit()
    finally:
        conn.close()

    return {
        "dropped_tables": dropped_tables,
        "dropped_columns": dropped_columns,
        "dropped_indexes": dropped_indexes,
        "changes": len(dropped_tables) + len(dropped_columns) + len(dropped_indexes),
    }


if __name__ == "__main__":
    db = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.environ.get("MOTOQUANT_DB", "motoquant.db")
    )
    print(f"remove-billing patch on {db}:")
    summary = apply(db, verbose=True)
    print(f"  {summary}")
    print(f"  {summary['changes']} change(s)")
