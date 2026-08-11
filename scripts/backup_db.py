#!/usr/bin/env python3
"""Hot-backup the production SQLite DB, gzip it, and rotate old snapshots.

Launch blocker B7 in docs/COMMERCIAL_LAUNCH.md: once real users and
subscription rows live on a persistent disk, losing that file loses paying
customers' accounts while the payment processor keeps charging them.

Why the sqlite3 backup API and not `cp`
---------------------------------------
`cp` of a live SQLite file can capture a torn page mid-write, and in WAL mode
it silently omits the -wal sidecar, so the copy is missing every committed
transaction that has not yet checkpointed. ``Connection.backup()`` is the
online-backup API: it takes a read lock per step, copes with concurrent
writers, and produces a fully-checkpointed standalone file.

Off-box copies
--------------
By default snapshots land next to the DB (same disk), which protects against
application-level damage — a bad migration, an errant DELETE, a corrupt patch
run — but NOT against losing the disk itself. Set MOTOQUANT_BACKUP_UPLOAD_CMD
to ship each snapshot somewhere else; ``{path}`` is substituted with the
snapshot's absolute path. Deliberately a shell hook rather than a bundled S3
client: it works with whatever the operator already has (rclone, aws, b2,
rsync, scp) and keeps this script dependency-free and testable.

    MOTOQUANT_BACKUP_UPLOAD_CMD='rclone copy {path} r2:motoquant-backups/'

Usage
-----
    python scripts/backup_db.py                       # back up $MOTOQUANT_DB
    python scripts/backup_db.py --db /data/motoquant.db --keep 14
    python scripts/backup_db.py --dry-run

Exit codes: 0 ok · 1 backup failed · 2 backup ok but upload failed.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import gzip
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

# Tables whose presence proves the snapshot is a real MotoQuant DB and not a
# truncated/empty file. Catalog tables only — the durable user tables are
# created lazily on first use and are legitimately absent on a fresh deploy.
_SENTINEL_TABLES = ("bike_models", "bike_configs", "parts", "tire_models")

DEFAULT_KEEP = 14
SNAPSHOT_PREFIX = "motoquant-"
SNAPSHOT_SUFFIX = ".db.gz"


def _log(msg: str) -> None:
    print(f"[backup] {msg}", flush=True)


def hot_backup(src: Path, dest: Path) -> None:
    """Copy a live SQLite DB to `dest` using the online-backup API."""
    src_conn = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
    try:
        dest_conn = sqlite3.connect(str(dest))
        try:
            src_conn.backup(dest_conn)
        finally:
            dest_conn.close()
    finally:
        src_conn.close()


def verify(path: Path) -> int:
    """Integrity-check a snapshot and return its bike_models row count.

    Raises RuntimeError if the file is not a usable MotoQuant database — a
    backup that cannot be restored is worse than no backup, because it buys
    false confidence.
    """
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        status = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if status != "ok":
            raise RuntimeError(f"integrity_check failed: {status}")
        present = {
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        missing = [t for t in _SENTINEL_TABLES if t not in present]
        if missing:
            raise RuntimeError(
                f"snapshot is missing expected tables: {', '.join(missing)}"
            )
        return int(conn.execute("SELECT COUNT(*) FROM bike_models").fetchone()[0])
    finally:
        conn.close()


def prune(backup_dir: Path, keep: int) -> list[Path]:
    """Delete all but the `keep` newest snapshots. Returns what was removed."""
    snapshots = sorted(
        backup_dir.glob(f"{SNAPSHOT_PREFIX}*{SNAPSHOT_SUFFIX}"),
        key=lambda p: p.name,  # timestamped names sort chronologically
        reverse=True,
    )
    removed = []
    for stale in snapshots[keep:]:
        stale.unlink()
        removed.append(stale)
    return removed


def upload(path: Path, template: str) -> None:
    """Run the operator's upload hook for one snapshot."""
    cmd = template.replace("{path}", str(path))
    _log(f"uploading: {cmd}")
    subprocess.run(cmd, shell=True, check=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--db",
        default=os.environ.get("MOTOQUANT_DB", "motoquant.db"),
        help="Path to the live DB (default: $MOTOQUANT_DB or ./motoquant.db)",
    )
    parser.add_argument(
        "--out",
        default=os.environ.get("MOTOQUANT_BACKUP_DIR"),
        help="Snapshot directory (default: <db-dir>/backups)",
    )
    parser.add_argument(
        "--keep",
        type=int,
        default=int(os.environ.get("MOTOQUANT_BACKUP_KEEP", DEFAULT_KEEP)),
        help=f"How many snapshots to retain (default: {DEFAULT_KEEP})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would happen, change nothing",
    )
    args = parser.parse_args(argv)

    src = Path(args.db).resolve()
    if not src.is_file():
        _log(f"ERROR: no database at {src}")
        return 1

    backup_dir = Path(args.out).resolve() if args.out else src.parent / "backups"
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    final = backup_dir / f"{SNAPSHOT_PREFIX}{stamp}{SNAPSHOT_SUFFIX}"

    if args.dry_run:
        _log(f"DRY RUN — would back up {src} ({src.stat().st_size / 1e6:.1f} MB)")
        _log(f"DRY RUN — would write {final}")
        _log(f"DRY RUN — would keep the {args.keep} newest snapshots in {backup_dir}")
        return 0

    backup_dir.mkdir(parents=True, exist_ok=True)

    # Snapshot to a temp file first, verify it, and only then gzip into place —
    # so a partially-written file never appears under the snapshot glob and
    # gets mistaken for a good backup by prune() or by a human restoring.
    with tempfile.TemporaryDirectory(dir=backup_dir) as tmpdir:
        staged = Path(tmpdir) / "snapshot.db"
        try:
            hot_backup(src, staged)
            bikes = verify(staged)
        except Exception as exc:  # noqa: BLE001 — report any failure the same way
            _log(f"ERROR: backup failed: {exc}")
            return 1

        with staged.open("rb") as raw, gzip.open(final, "wb", compresslevel=6) as gz:
            shutil.copyfileobj(raw, gz)

    _log(f"wrote {final.name} ({final.stat().st_size / 1e6:.1f} MB, {bikes} bikes)")

    for removed in prune(backup_dir, args.keep):
        _log(f"pruned {removed.name}")

    upload_cmd = os.environ.get("MOTOQUANT_BACKUP_UPLOAD_CMD", "").strip()
    if upload_cmd:
        try:
            upload(final, upload_cmd)
        except subprocess.CalledProcessError as exc:
            # The local snapshot is good; only the off-box copy failed. Distinct
            # exit code so a cron can alert without implying data was lost.
            _log(
                f"ERROR: upload hook failed (exit {exc.returncode}) — local snapshot kept"
            )
            return 2
    else:
        _log(
            "no MOTOQUANT_BACKUP_UPLOAD_CMD set — snapshot is on the same disk as the DB"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
