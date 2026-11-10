#!/usr/bin/env python3
"""patch_2026_11_10_remove_accounts.py — remove the account and submission schema.

MotoQuant has no accounts and no anonymous writes to its catalog database
(2026-11-10). Saved runs live in the visitor's browser; shared timeslips carry
their setup in the link and are re-simulated on view; bike suggestions and
spec corrections go through the public issue tracker. This patch drops the
storage those features left behind (all empty in the shipped catalog):

    tables   sessions, magic_links, users, spec_corrections
    columns  sim_runs.user_id

The ``sim_runs`` table itself stays: the command-line tool still records local
runs there (``sim --save-run``, ``history``, ``leaderboard``).

Safety
------
* Idempotent: ``DROP TABLE IF EXISTS`` and a column is dropped only when
  ``PRAGMA table_info`` still lists it. A second run reports zero changes.
* All changes happen in ONE transaction. The script refuses to commit if
  ``PRAGMA integrity_check`` / ``foreign_key_check`` fail or ANY surviving
  table's row count changed, and rolls back instead.
* No VACUUM (it would rewrite every page of the catalog and may renumber
  implicit rowids); freed pages join the freelist.
* WAL-aware: after the commit the WAL is checkpointed (TRUNCATE) so the
  change lives in the main ``.db`` file that git tracks.
* SQLite older than 3.35 cannot drop a column; the column is then left in
  place and reported. Nothing reads it.

Usage
-----
    python scripts/patch_2026_11_10_remove_accounts.py            # $MOTOQUANT_DB or motoquant.db
    python scripts/patch_2026_11_10_remove_accounts.py --dry-run  # report only
    python scripts/patch_2026_11_10_remove_accounts.py --db path/to/other.db
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys

# Children before parents: sessions and magic_links reference users.
DEAD_TABLES = ("sessions", "magic_links", "users", "spec_corrections")
DEAD_COLUMNS = (("sim_runs", "user_id"),)


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
    columns = [
        (t, c) for t, c in DEAD_COLUMNS if t in present and c in _columns(conn, t)
    ]
    return {"tables": tables, "columns": columns}


def apply(db_path: str, *, dry_run: bool = False, verbose: bool = True) -> dict:
    """Drop the account and submission schema from ``db_path``.

    Returns a summary dict: dropped_tables, dropped_columns ("table.column"),
    dropped_indexes, skipped_columns, integrity ("ok") and rows_checked.
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
            "dropped_indexes": [],
            "skipped_columns": [],
            "integrity": None,
            "rows_checked": 0,
            "dry_run": dry_run,
        }
        if verbose:
            print(f"remove-accounts patch on {db_path}:")
            print(f"  tables to drop : {todo['tables'] or 'none'}")
            cols = [f"{t}.{c}" for t, c in todo["columns"]]
            print(f"  columns to drop: {cols or 'none'}")
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
            can_drop_column = sqlite3.sqlite_version_info >= (3, 35, 0)
            for table, col in todo["columns"]:
                label = f"{table}.{col}"
                if not can_drop_column:
                    summary["skipped_columns"].append(
                        f"{label} (SQLite {sqlite3.sqlite_version} has no DROP COLUMN)"
                    )
                    continue
                for idx in _indexes_on(conn, table, col):
                    conn.execute(f'DROP INDEX "{idx}"')
                    summary["dropped_indexes"].append(idx)
                try:
                    conn.execute(f'ALTER TABLE "{table}" DROP COLUMN "{col}"')
                    summary["dropped_columns"].append(label)
                except sqlite3.OperationalError as exc:
                    summary["skipped_columns"].append(f"{label} ({exc})")

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

        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        summary["integrity"] = integrity
        summary["rows_checked"] = len(after)
        if verbose:
            print(f"  dropped tables : {summary['dropped_tables']}")
            print(f"  dropped columns: {summary['dropped_columns']}")
            if summary["dropped_indexes"]:
                print(f"  dropped indexes: {summary['dropped_indexes']}")
            if summary["skipped_columns"]:
                print(f"  SKIPPED columns: {summary['skipped_columns']}")
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
