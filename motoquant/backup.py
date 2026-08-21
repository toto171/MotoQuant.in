"""Hot-backup core + in-app backup scheduler for the production SQLite DB.

Launch blocker B7 in docs/COMMERCIAL_LAUNCH.md: once real users and
subscription rows live on a persistent disk, losing that file loses paying
customers' accounts while the payment processor keeps charging them.

This module holds the importable core (moved out of scripts/backup_db.py,
which remains the operator CLI wrapper) PLUS an asyncio scheduler wired into
the FastAPI startup hooks. Why in-process scheduling at all: the Render
persistent disk mounts to exactly ONE service and scripts/ is not COPYd into
the Docker image, so a cron job outside the web service can never reach the
disk — running inside the app is the only path that does, and this module
rides the existing ``COPY motoquant/`` Docker layer.

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
rsync, scp) and keeps this module dependency-free and testable.

    MOTOQUANT_BACKUP_UPLOAD_CMD='rclone copy {path} r2:motoquant-backups/'

Scheduler activation (mirrors the keepwarm pattern): only when
``MOTOQUANT_BACKUP_ENABLE`` is truthy. Interval from
``MOTOQUANT_BACKUP_INTERVAL_H`` (default 24 h, floor 1 h). Failures are
logged and swallowed — backups must never affect API availability.
"""

from __future__ import annotations

import asyncio
import datetime as _dt
import gzip
import logging
import os
import shutil
import sqlite3
import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("motoquant.backup")

# Tables whose presence proves the snapshot is a real MotoQuant DB and not a
# truncated/empty file. Catalog tables only — the durable user tables are
# created lazily on first use and are legitimately absent on a fresh deploy.
_SENTINEL_TABLES = ("bike_models", "bike_configs", "parts", "tire_models")

DEFAULT_KEEP = 14
SNAPSHOT_PREFIX = "motoquant-"
SNAPSHOT_SUFFIX = ".db.gz"

#: Scheduler knobs. The initial delay keeps a deploy-restart herd (several
#: boots in quick succession) from snapshotting on every single boot.
DEFAULT_INTERVAL_H = 24.0
INITIAL_DELAY_S = 300.0


@dataclass
class BackupResult:
    """Outcome of one ``run_backup`` call."""

    path: Path | None  # the written snapshot (None when the backup failed)
    ok: bool  # snapshot written AND verified
    uploaded: bool  # upload hook ran successfully (False when no hook set)
    error: str | None  # backup failure, or upload failure when ok=True
    pruned: list[Path] = field(default_factory=list)


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
    logger.info("uploading: %s", cmd)
    subprocess.run(cmd, shell=True, check=True)


def run_backup(
    db_path: str | Path,
    out_dir: str | Path | None = None,
    keep: int = DEFAULT_KEEP,
    upload_cmd: str | None = None,
    log: Callable[[str], None] | None = None,
) -> BackupResult:
    """Snapshot → verify → gzip → prune → (optional) upload. Never raises.

    ``log`` lets the CLI wrapper keep its exact stdout format; the scheduler
    leaves it unset and gets the module logger.
    """
    emit = log or (lambda msg: logger.info("%s", msg))
    src = Path(db_path).resolve()
    if not src.is_file():
        msg = f"no database at {src}"
        emit(f"ERROR: {msg}")
        return BackupResult(path=None, ok=False, uploaded=False, error=msg)

    backup_dir = Path(out_dir).resolve() if out_dir else src.parent / "backups"
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    final = backup_dir / f"{SNAPSHOT_PREFIX}{stamp}{SNAPSHOT_SUFFIX}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Snapshot to a temp file first, verify it, and only then gzip into place —
    # so a partially-written file never appears under the snapshot glob and
    # gets mistaken for a good backup by prune() or by a human restoring.
    with tempfile.TemporaryDirectory(dir=backup_dir) as tmpdir:
        staged = Path(tmpdir) / "snapshot.db"
        staged_gz = Path(tmpdir) / "snapshot.db.gz"
        try:
            hot_backup(src, staged)
            bikes = verify(staged)
            # Gzip inside the tempdir too, then atomically rename into place:
            # a disk-full mid-write (snapshots share the disk with the live
            # DB) must neither escape run_backup nor leave a truncated .gz
            # under the snapshot glob for prune()/restore to trust.
            with (
                staged.open("rb") as raw,
                gzip.open(staged_gz, "wb", compresslevel=6) as gz,
            ):
                shutil.copyfileobj(raw, gz)
            os.replace(staged_gz, final)
        except Exception as exc:  # noqa: BLE001 — report any failure the same way
            msg = f"backup failed: {exc}"
            emit(f"ERROR: {msg}")
            return BackupResult(path=None, ok=False, uploaded=False, error=msg)

    emit(f"wrote {final.name} ({final.stat().st_size / 1e6:.1f} MB, {bikes} bikes)")

    pruned = prune(backup_dir, keep)
    for removed in pruned:
        emit(f"pruned {removed.name}")

    uploaded = False
    error: str | None = None
    if upload_cmd and upload_cmd.strip():
        try:
            upload(final, upload_cmd.strip())
            uploaded = True
        except subprocess.CalledProcessError as exc:
            # The local snapshot is good; only the off-box copy failed.
            error = f"upload hook failed (exit {exc.returncode}) — local snapshot kept"
            emit(f"ERROR: {error}")

    return BackupResult(
        path=final, ok=True, uploaded=uploaded, error=error, pruned=pruned
    )


# ─── In-app scheduler (keepwarm pattern) ─────────────────────────────────────


def _truthy(val: str | None) -> bool:
    return (val or "").strip().lower() in ("1", "true", "yes", "on")


async def _backup_loop(interval_s: float) -> None:
    logger.info(
        "backup scheduler started: every %.1f h (first run in %.0f s)",
        interval_s / 3600.0,
        INITIAL_DELAY_S,
    )
    # Deploy-restart herd guard: several boots in quick succession must not
    # each take a snapshot the moment they come up.
    await asyncio.sleep(INITIAL_DELAY_S)
    while True:
        try:
            db_path = os.environ.get("MOTOQUANT_DB", "motoquant.db")
            out_dir = os.environ.get("MOTOQUANT_BACKUP_DIR") or None
            try:
                keep = int(os.environ.get("MOTOQUANT_BACKUP_KEEP", DEFAULT_KEEP))
            except ValueError:
                keep = DEFAULT_KEEP
            upload_cmd = (
                os.environ.get("MOTOQUANT_BACKUP_UPLOAD_CMD", "").strip() or None
            )
            result = await asyncio.to_thread(
                run_backup, db_path, out_dir, keep, upload_cmd
            )
            if result.ok:
                logger.info(
                    "scheduled backup ok: %s (uploaded=%s, pruned=%d)",
                    result.path,
                    result.uploaded,
                    len(result.pruned),
                )
                if result.error:  # ok=True + error = upload-hook failure
                    logger.warning("scheduled backup upload failed: %s", result.error)
            else:
                logger.warning("scheduled backup FAILED: %s", result.error)
        except Exception:  # noqa: BLE001 — the loop must survive anything
            logger.warning("backup iteration failed", exc_info=True)
        await asyncio.sleep(interval_s)


def start_backup_scheduler() -> asyncio.Task[None] | None:
    """Start the background backup loop if configured. Safe to call always.

    Returns the task (so callers/tests can cancel it) or None when disabled.
    Must be called from within a running event loop (e.g. a FastAPI startup
    hook).
    """
    if not _truthy(os.environ.get("MOTOQUANT_BACKUP_ENABLE")):
        logger.info("in-app backups disabled (MOTOQUANT_BACKUP_ENABLE unset)")
        return None
    try:
        interval_h = float(
            os.environ.get("MOTOQUANT_BACKUP_INTERVAL_H", DEFAULT_INTERVAL_H)
        )
    except ValueError:
        interval_h = DEFAULT_INTERVAL_H
    interval_h = max(1.0, interval_h)  # floor: never snapshot more than hourly
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        logger.warning("backup scheduler not started: no running event loop")
        return None
    return loop.create_task(_backup_loop(interval_h * 3600.0), name="motoquant-backup")
