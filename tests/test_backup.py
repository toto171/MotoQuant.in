"""motoquant.backup — importable hot-backup core + in-app scheduler (2026-08-21).

The backup core moved out of scripts/backup_db.py into motoquant/backup.py so
the in-process scheduler can reach the Render persistent disk (scripts/ is not
COPYd into the Docker image; motoquant/ is). These tests pin:

- run_backup round-trip: snapshot → verify → gzip → restorable copy
- verify() rejects a DB missing the sentinel tables (no false confidence)
- prune() keeps exactly the N newest snapshots and never touches other files
- upload-hook failure keeps the local snapshot and reports it distinctly
- start_backup_scheduler() is a hard no-op without MOTOQUANT_BACKUP_ENABLE
- the scripts/backup_db.py CLI wrapper preserves its exit-code contract
  (0 ok / 1 backup failed / 2 backup ok but upload failed)

Everything runs on throwaway tmp SQLite files — the tracked motoquant.db is
never opened, let alone written.
"""

import asyncio
import gzip
import importlib.util
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from motoquant import backup as backup_mod


def _make_source_db(path: Path, bikes: int = 3) -> None:
    """A minimal DB carrying all four sentinel tables + some bike rows."""
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(
            """
            CREATE TABLE bike_models (id INTEGER PRIMARY KEY, name TEXT);
            CREATE TABLE bike_configs (id INTEGER PRIMARY KEY);
            CREATE TABLE parts (id INTEGER PRIMARY KEY);
            CREATE TABLE tire_models (id INTEGER PRIMARY KEY);
            """
        )
        conn.executemany(
            "INSERT INTO bike_models (name) VALUES (?)",
            [(f"Bike {i}",) for i in range(bikes)],
        )
        conn.commit()
    finally:
        conn.close()


class TestRunBackup(unittest.TestCase):
    def test_round_trip_restores_identical_rows(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "live.db"
            out = Path(td) / "snaps"
            _make_source_db(src, bikes=5)

            result = backup_mod.run_backup(src, out_dir=out, keep=5)

            self.assertTrue(result.ok, result.error)
            self.assertIsNone(result.error)
            self.assertFalse(result.uploaded)  # no upload hook configured
            self.assertEqual(result.pruned, [])
            self.assertTrue(result.path.name.startswith(backup_mod.SNAPSHOT_PREFIX))
            self.assertTrue(result.path.name.endswith(backup_mod.SNAPSHOT_SUFFIX))

            # Restore round-trip: gunzip → open → sentinel rows intact.
            restored = Path(td) / "restored.db"
            with gzip.open(result.path, "rb") as gz, restored.open("wb") as f:
                f.write(gz.read())
            conn = sqlite3.connect(str(restored))
            try:
                n = conn.execute("SELECT COUNT(*) FROM bike_models").fetchone()[0]
                names = [
                    r[0]
                    for r in conn.execute(
                        "SELECT name FROM bike_models ORDER BY id"
                    ).fetchall()
                ]
            finally:
                conn.close()
            self.assertEqual(n, 5)
            self.assertEqual(names[0], "Bike 0")

    def test_missing_db_fails_cleanly(self):
        with tempfile.TemporaryDirectory() as td:
            result = backup_mod.run_backup(
                Path(td) / "absent.db", out_dir=Path(td) / "snaps"
            )
            self.assertFalse(result.ok)
            self.assertIsNone(result.path)
            self.assertIn("no database", result.error)

    def test_verify_rejects_missing_sentinels(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "notmq.db"
            conn = sqlite3.connect(str(src))
            conn.execute("CREATE TABLE something_else (id INTEGER)")
            conn.commit()
            conn.close()

            result = backup_mod.run_backup(src, out_dir=Path(td) / "snaps")

            self.assertFalse(result.ok)
            self.assertIn("missing expected tables", result.error)
            # No half-good file may appear under the snapshot glob.
            snaps = list((Path(td) / "snaps").glob(f"{backup_mod.SNAPSHOT_PREFIX}*"))
            self.assertEqual(snaps, [])

    def test_upload_failure_keeps_snapshot_and_reports(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "live.db"
            out = Path(td) / "snaps"
            _make_source_db(src)

            result = backup_mod.run_backup(
                src, out_dir=out, keep=5, upload_cmd="exit 7"
            )

            self.assertTrue(result.ok)  # local snapshot is good
            self.assertFalse(result.uploaded)
            self.assertIn("exit 7", result.error)
            self.assertTrue(result.path.is_file())

    def test_upload_success(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "live.db"
            out = Path(td) / "snaps"
            _make_source_db(src)
            marker = Path(td) / "uploaded.marker"

            result = backup_mod.run_backup(
                src, out_dir=out, keep=5, upload_cmd=f"cp {{path}} {marker}"
            )

            self.assertTrue(result.ok)
            self.assertTrue(result.uploaded)
            self.assertIsNone(result.error)
            self.assertTrue(marker.is_file())  # {path} substitution worked


class TestPrune(unittest.TestCase):
    def _touch_snapshots(self, d: Path, stamps):
        names = [
            f"{backup_mod.SNAPSHOT_PREFIX}{s}{backup_mod.SNAPSHOT_SUFFIX}"
            for s in stamps
        ]
        for n in names:
            (d / n).write_bytes(b"x")
        return names

    def test_prune_keeps_n_newest(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            names = self._touch_snapshots(
                d, [f"2026080{i}T000000Z" for i in range(1, 6)]
            )
            removed = backup_mod.prune(d, keep=2)
            kept = sorted(p.name for p in d.iterdir())
            self.assertEqual(kept, sorted(names[-2:]))
            self.assertEqual(sorted(p.name for p in removed), sorted(names[:3]))

    def test_prune_ignores_foreign_files(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            self._touch_snapshots(d, ["20260801T000000Z", "20260802T000000Z"])
            foreign = d / "restore-notes.txt"
            foreign.write_text("do not delete")
            backup_mod.prune(d, keep=0)  # nukes every snapshot...
            self.assertTrue(foreign.is_file())  # ...but never other files


class TestScheduler(unittest.TestCase):
    def setUp(self):
        self._prior = os.environ.pop("MOTOQUANT_BACKUP_ENABLE", None)

    def tearDown(self):
        if self._prior is None:
            os.environ.pop("MOTOQUANT_BACKUP_ENABLE", None)
        else:
            os.environ["MOTOQUANT_BACKUP_ENABLE"] = self._prior

    def test_disabled_without_env(self):
        self.assertIsNone(backup_mod.start_backup_scheduler())

    def test_disabled_on_falsy_values(self):
        for val in ("", "0", "false", "no", "off"):
            os.environ["MOTOQUANT_BACKUP_ENABLE"] = val
            self.assertIsNone(backup_mod.start_backup_scheduler(), val)

    def test_enabled_but_no_running_loop_returns_none(self):
        os.environ["MOTOQUANT_BACKUP_ENABLE"] = "1"
        self.assertIsNone(backup_mod.start_backup_scheduler())

    def test_enabled_inside_loop_creates_task(self):
        os.environ["MOTOQUANT_BACKUP_ENABLE"] = "1"

        async def go():
            task = backup_mod.start_backup_scheduler()
            self.assertIsNotNone(task)
            self.assertEqual(task.get_name(), "motoquant-backup")
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        asyncio.run(go())


class TestCliWrapper(unittest.TestCase):
    """scripts/backup_db.py stays a thin wrapper with the same exit codes."""

    @classmethod
    def setUpClass(cls):
        cli_path = Path(__file__).resolve().parent.parent / "scripts" / "backup_db.py"
        spec = importlib.util.spec_from_file_location("backup_db_cli", cli_path)
        cls.cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.cli)

    def test_exit_codes(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "live.db"
            out = str(Path(td) / "snaps")
            _make_source_db(src)

            # 0 — ok (no upload hook set)
            prior = os.environ.pop("MOTOQUANT_BACKUP_UPLOAD_CMD", None)
            try:
                self.assertEqual(self.cli.main(["--db", str(src), "--out", out]), 0)
                # 1 — backup failed (missing DB)
                self.assertEqual(
                    self.cli.main(["--db", str(Path(td) / "nope.db"), "--out", out]),
                    1,
                )
                # 2 — backup ok, upload hook failed
                os.environ["MOTOQUANT_BACKUP_UPLOAD_CMD"] = "exit 5"
                self.assertEqual(self.cli.main(["--db", str(src), "--out", out]), 2)
            finally:
                if prior is None:
                    os.environ.pop("MOTOQUANT_BACKUP_UPLOAD_CMD", None)
                else:
                    os.environ["MOTOQUANT_BACKUP_UPLOAD_CMD"] = prior

    def test_dry_run_changes_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "live.db"
            out = Path(td) / "snaps"
            _make_source_db(src)
            self.assertEqual(
                self.cli.main(["--db", str(src), "--out", str(out), "--dry-run"]), 0
            )
            self.assertFalse(out.exists())  # dry-run creates no directory/files


if __name__ == "__main__":
    unittest.main()
