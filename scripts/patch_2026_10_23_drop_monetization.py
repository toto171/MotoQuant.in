#!/usr/bin/env python3
"""patch_2026_10_23_drop_monetization.py — remove the retired billing schema.

MotoQuant became a free, open-source project on 2026-10-23: payments,
subscriptions, license keys, tier gating and the free-tier sim-quota meter
were deleted from the code. Their storage outlived them in the shipped
``motoquant.db`` (all empty — 0 rows each — but still shipped, and the old
startup hook re-created them on every boot):

    tables   subscriptions, license_keys, payment_events, sim_usage
    columns  users.tier, users.razorpay_customer_id, users.stripe_customer_id

This patch drops all of it. Nothing else is touched: the optional-accounts
tables (users / sessions / magic_links), sim_runs and the whole catalog keep
every row, which the script verifies before it reports success.

Safety
------
* Idempotent: ``DROP TABLE IF EXISTS`` and a column is dropped only when
  ``PRAGMA table_info`` still lists it. A second run reports zero changes.
* All changes happen in ONE transaction. The script refuses to commit if
  ``PRAGMA integrity_check`` / ``foreign_key_check`` fail or ANY surviving
  table's row count changed, and rolls back instead.
* No VACUUM: it would rewrite every page of the 18 MB catalog (a huge binary
  diff) and may renumber implicit rowids. The freed pages simply join the
  freelist and are reused by future writes.
* WAL-aware: after the commit the WAL is checkpointed (TRUNCATE) so the
  change lives in the main ``.db`` file that git tracks.
* Old SQLite without ``ALTER TABLE ... DROP COLUMN`` (< 3.35): the columns are
  left in place and reported. That is harmless — no code reads them, and
  ``users.tier`` is ``NOT NULL DEFAULT 'free'`` so INSERTs that omit it still
  succeed (pinned by tests/test_auth.py::TestLegacyUsersSchemaStillWorks).

Usage
-----
    python scripts/patch_2026_10_23_drop_monetization.py            # $MOTOQUANT_DB or motoquant.db
    python scripts/patch_2026_10_23_drop_monetization.py --dry-run  # report only
    python scripts/patch_2026_10_23_drop_monetization.py --db path/to/other.db
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys

DEAD_TABLES = ("subscriptions", "license_keys", "payment_events", "sim_usage")
DEAD_USER_COLUMNS = ("tier", "razorpay_customer_id", "stripe_customer_id")


def _tables(conn: sqlite3.Connection) -> list[str]:
    return [
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]


def _columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')]


def _row_counts(conn: sqlite3.Connection, skip: tuple[str, ...]) -> dict[str, int]:
    counts = {
        t: conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        for t in _tables(conn)
        if t not in skip
    }
    # AUTOINCREMENT bookkeeping for SURVIVING tables must not move either
    # (SQLite deletes the dropped tables' own sqlite_sequence rows itself).
    try:
        for name, seq in conn.execute("SELECT name, seq FROM sqlite_sequence"):
            if name not in skip:
                counts[f"sqlite_sequence[{name}]"] = seq
    except sqlite3.OperationalError:
        pass  # no AUTOINCREMENT table in this DB
    return counts


def plan(conn: sqlite3.Connection) -> dict:
    """What this patch WOULD change on ``conn`` (no writes)."""
    present = set(_tables(conn))
    tables = [t for t in DEAD_TABLES if t in present]
    columns = []
    if "users" in present:
        user_cols = _columns(conn, "users")
        columns = [c for c in DEAD_USER_COLUMNS if c in user_cols]
    return {"tables": tables, "columns": columns}


def apply(db_path: str, *, dry_run: bool = False, verbose: bool = True) -> dict:
    """Drop the monetization schema from ``db_path``.

    Returns a summary dict:
      dropped_tables / dropped_columns — what actually changed this run;
      skipped_columns — columns this SQLite build could not drop;
      integrity — PRAGMA integrity_check result ("ok");
      rows_checked — number of surviving tables (+ sequences) verified.
    Raises RuntimeError (after a rollback) if any post-condition fails.
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(db_path)
    conn = sqlite3.connect(db_path, isolation_level=None)
    try:
        conn.execute("PRAGMA busy_timeout = 10000")
        todo = plan(conn)
        summary = {
            "db": db_path,
            "dropped_tables": [],
            "dropped_columns": [],
            "skipped_columns": [],
            "integrity": None,
            "rows_checked": 0,
            "dry_run": dry_run,
        }
        if verbose:
            print(f"drop-monetization patch on {db_path}:")
            print(f"  tables to drop : {todo['tables'] or 'none'}")
            print(f"  users columns  : {todo['columns'] or 'none'}")
        if dry_run or not (todo["tables"] or todo["columns"]):
            summary["integrity"] = conn.execute("PRAGMA integrity_check").fetchone()[0]
            if verbose:
                print("  nothing to do." if not dry_run else "  dry run — no writes.")
            return summary

        before = _row_counts(conn, skip=DEAD_TABLES)
        conn.execute("BEGIN IMMEDIATE")
        try:
            for table in todo["tables"]:
                conn.execute(f'DROP TABLE IF EXISTS "{table}"')
                summary["dropped_tables"].append(table)
            for col in todo["columns"]:
                try:
                    conn.execute(f'ALTER TABLE users DROP COLUMN "{col}"')
                    summary["dropped_columns"].append(col)
                except sqlite3.OperationalError as exc:
                    # SQLite < 3.35 has no DROP COLUMN — harmless leftover.
                    summary["skipped_columns"].append(f"{col} ({exc})")

            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
            after = _row_counts(conn, skip=DEAD_TABLES)
            problems = []
            if integrity != "ok":
                problems.append(f"integrity_check={integrity!r}")
            if fk_violations:
                problems.append(f"foreign_key_check={fk_violations[:5]!r}")
            if before != after:
                diff = {
                    k: (before.get(k), after.get(k))
                    for k in sorted(set(before) | set(after))
                    if before.get(k) != after.get(k)
                }
                problems.append(f"surviving row counts changed: {diff}")
            if problems:
                raise RuntimeError("; ".join(problems))
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise

        # Fold the WAL into the main file so git sees the change.
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        summary["integrity"] = integrity
        summary["rows_checked"] = len(after)
        if verbose:
            print(f"  dropped tables : {summary['dropped_tables']}")
            print(f"  dropped columns: {summary['dropped_columns']}")
            if summary["skipped_columns"]:
                print(f"  SKIPPED columns (old SQLite): {summary['skipped_columns']}")
            print(
                f"  integrity_check: {integrity}; "
                f"{len(after)} surviving tables/sequences unchanged"
            )
        return summary
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 2)[1])
    ap.add_argument(
        "--db",
        default=os.environ.get("MOTOQUANT_DB", "motoquant.db"),
        help="database to patch (default: $MOTOQUANT_DB or motoquant.db)",
    )
    ap.add_argument("--dry-run", action="store_true", help="report only, no writes")
    args = ap.parse_args(argv)
    try:
        apply(args.db, dry_run=args.dry_run)
    except (FileNotFoundError, RuntimeError, sqlite3.Error) as exc:
        print(f"PATCH FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
