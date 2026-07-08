"""Tests for the Local Lab launcher helpers (local_lab/entry.py).

These pin the copy-once DB seeding semantics (the same contract
docker-entrypoint.sh implements for the Render persistent disk) and the
env wiring the packaged binary depends on. The full boot path (static UI
mount + engine) is exercised end-to-end by the CI smoke test in
.github/workflows/local-lab.yml.
"""

import os
import socket
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from local_lab.entry import build_env, pick_port, prepare_database, resolve_ui_dir


class TestPrepareDatabase(unittest.TestCase):
    def _seed(self, tmp: Path, content: bytes = b"seed-catalog") -> Path:
        seed = tmp / "seed.db"
        seed.write_bytes(content)
        return seed

    def test_first_boot_copies_seed(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            seed = self._seed(tmp_path)
            data_dir = tmp_path / "data"
            target = prepare_database(seed, data_dir)
            self.assertEqual(target, data_dir / "motoquant.db")
            self.assertEqual(target.read_bytes(), b"seed-catalog")

    def test_existing_db_never_overwritten(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            seed = self._seed(tmp_path)
            data_dir = tmp_path / "data"
            first = prepare_database(seed, data_dir)
            # Simulate accumulated user data (saved runs), then a new seed
            # shipping in an upgraded binary: the live DB must be preserved.
            first.write_bytes(b"user-data-with-saved-runs")
            seed.write_bytes(b"newer-seed-catalog")
            second = prepare_database(seed, data_dir)
            self.assertEqual(second.read_bytes(), b"user-data-with-saved-runs")

    def test_fresh_flag_reseeds(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            seed = self._seed(tmp_path)
            data_dir = tmp_path / "data"
            target = prepare_database(seed, data_dir)
            target.write_bytes(b"user-data")
            reseeded = prepare_database(seed, data_dir, fresh=True)
            self.assertEqual(reseeded.read_bytes(), b"seed-catalog")

    def test_missing_seed_raises(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            with self.assertRaises(FileNotFoundError):
                prepare_database(tmp_path / "nope.db", tmp_path / "data")


class TestBuildEnv(unittest.TestCase):
    def _restore(self, snapshot):
        for key, value in snapshot.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_sets_engine_env_and_scrubs_keepwarm(self):
        keys = (
            "MOTOQUANT_DB",
            "MOTOQUANT_RATE_LIMIT",
            "MOTOQUANT_LOCAL_UI",
            "RENDER_EXTERNAL_URL",
            "MOTOQUANT_KEEPWARM_URL",
        )
        snapshot = {k: os.environ.get(k) for k in keys}
        try:
            os.environ["RENDER_EXTERNAL_URL"] = "https://stale.example"
            os.environ["MOTOQUANT_KEEPWARM_URL"] = "https://stale.example"
            os.environ.pop("MOTOQUANT_RATE_LIMIT", None)
            with TemporaryDirectory() as tmp:
                ui_dir = Path(tmp) / "ui"
                ui_dir.mkdir()
                db = Path(tmp) / "motoquant.db"
                env = build_env(db, ui_dir)
            self.assertEqual(os.environ["MOTOQUANT_DB"], str(db))
            self.assertEqual(os.environ["MOTOQUANT_RATE_LIMIT"], "false")
            self.assertEqual(os.environ["MOTOQUANT_LOCAL_UI"], str(ui_dir))
            self.assertNotIn("RENDER_EXTERNAL_URL", os.environ)
            self.assertNotIn("MOTOQUANT_KEEPWARM_URL", os.environ)
            self.assertEqual(env["MOTOQUANT_DB"], str(db))
        finally:
            self._restore(snapshot)

    def test_missing_ui_dir_not_exported(self):
        keys = ("MOTOQUANT_DB", "MOTOQUANT_RATE_LIMIT", "MOTOQUANT_LOCAL_UI")
        snapshot = {k: os.environ.get(k) for k in keys}
        try:
            os.environ.pop("MOTOQUANT_LOCAL_UI", None)
            with TemporaryDirectory() as tmp:
                env = build_env(Path(tmp) / "db.sqlite", Path(tmp) / "no-ui")
            self.assertNotIn("MOTOQUANT_LOCAL_UI", env)
            self.assertNotIn("MOTOQUANT_LOCAL_UI", os.environ)
        finally:
            self._restore(snapshot)


class TestResolveUiDir(unittest.TestCase):
    def test_prefers_bundled_ui(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ui").mkdir()
            (root / "desktop" / "dist").mkdir(parents=True)
            self.assertEqual(resolve_ui_dir(root), root / "ui")

    def test_falls_back_to_dev_vite_build(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(resolve_ui_dir(root), root / "desktop" / "dist")


class TestPickPort(unittest.TestCase):
    def test_free_preferred_port_is_kept(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(("127.0.0.1", 0))
            free_port = probe.getsockname()[1]
        # Port was just released; on any sane CI box it is still free.
        self.assertEqual(pick_port(free_port), free_port)

    def test_busy_preferred_port_falls_back(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as holder:
            holder.bind(("127.0.0.1", 0))
            holder.listen(1)
            busy_port = holder.getsockname()[1]
            fallback = pick_port(busy_port)
            self.assertNotEqual(fallback, busy_port)
            self.assertGreater(fallback, 0)


if __name__ == "__main__":
    unittest.main()
