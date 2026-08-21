#!/usr/bin/env python3
"""Hot-backup the production SQLite DB, gzip it, and rotate old snapshots.

Thin CLI wrapper around :mod:`motoquant.backup` (the core moved there on
2026-08-21 so the in-app scheduler can reach the Render persistent disk —
scripts/ is not COPYd into the Docker image, motoquant/ is). All flags and
exit codes are unchanged; see motoquant/backup.py for the full rationale
(online-backup API vs `cp`, sentinel verification, the upload hook).

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
import os
import sys
from pathlib import Path

# Runnable as `python scripts/backup_db.py` from anywhere: put the repo root
# on sys.path so `import motoquant` resolves without installation.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from motoquant.backup import (  # noqa: E402
    DEFAULT_KEEP,
    SNAPSHOT_PREFIX,
    SNAPSHOT_SUFFIX,
    hot_backup,  # noqa: F401 — re-exported for callers of the old module API
    prune,  # noqa: F401
    run_backup,
    upload,  # noqa: F401
    verify,  # noqa: F401
)


def _log(msg: str) -> None:
    print(f"[backup] {msg}", flush=True)


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

    if args.dry_run:
        stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        final = backup_dir / f"{SNAPSHOT_PREFIX}{stamp}{SNAPSHOT_SUFFIX}"
        _log(f"DRY RUN — would back up {src} ({src.stat().st_size / 1e6:.1f} MB)")
        _log(f"DRY RUN — would write {final}")
        _log(f"DRY RUN — would keep the {args.keep} newest snapshots in {backup_dir}")
        return 0

    upload_cmd = os.environ.get("MOTOQUANT_BACKUP_UPLOAD_CMD", "").strip()
    result = run_backup(
        src,
        out_dir=backup_dir,
        keep=args.keep,
        upload_cmd=upload_cmd or None,
        log=_log,
    )
    if not result.ok:
        return 1
    if upload_cmd:
        if not result.uploaded:
            # The local snapshot is good; only the off-box copy failed. Distinct
            # exit code so a cron can alert without implying data was lost.
            return 2
    else:
        _log(
            "no MOTOQUANT_BACKUP_UPLOAD_CMD set — snapshot is on the same disk as the DB"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
