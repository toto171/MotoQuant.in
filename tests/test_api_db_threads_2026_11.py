"""
Concurrent DB access through the API must not deadlock (docs/KNOWN_TRAPS.md T14).

Until November 2026 ``api._get_db()`` handed every request thread and every
job worker the same ``sqlite3`` connection, and that connection carried a
Python authorizer. SQLite calls the authorizer while it holds the
connection's mutex, and the callback needs the GIL; another thread that holds
the GIL and binds a parameter on the same connection waits for that mutex.
Neither can move, and the whole server hangs for good.

The regression test drives the production path (docs/INVARIANTS.md I8):
several threads call ``api._build_config`` (the sim routes' DB loader) and
the assistant's ``_get_db_facade()`` at the same time. It runs in a
subprocess because the failure mode is a hang, not an exception; on the old
code it never finishes and the timeout fails the test.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import threading
import unittest

import pytest

pytest.importorskip("fastapi")

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REPO_DB = os.path.join(_REPO, "motoquant.db")

# Generous: the fixed code finishes in a few seconds; the old code never does.
_TIMEOUT_S = 90

_LOAD_SCRIPT = textwrap.dedent(
    """
    import sys, threading
    from motoquant import api

    N_THREADS, ROUNDS = 8, 15
    errors = []
    start = threading.Barrier(N_THREADS)

    def work(i):
        try:
            start.wait()
            for _ in range(ROUNDS):
                api._build_config(
                    bike_id=11 + i,
                    bike_preset=None,
                    power_boost_pct=0,
                    mass_delta_kg=0,
                    rider_mass_kg=75,
                )
                api._catalog_token()
                if i % 2:
                    api._get_db_facade().venues.list_all()
        except Exception as e:  # noqa: BLE001
            errors.append(repr(e))

    threads = [threading.Thread(target=work, args=(i,)) for i in range(N_THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    if errors:
        print("\\n".join(errors))
        sys.exit(1)
    print("ok")
    """
)


class TestConcurrentApiDbAccess(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="mq_db_threads_")
        self.db = os.path.join(self.tmp, "motoquant.db")
        shutil.copyfile(_REPO_DB, self.db)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_parallel_build_config_does_not_hang(self):
        env = dict(os.environ, MOTOQUANT_DB=self.db, MOTOQUANT_RATE_LIMIT="false")
        try:
            proc = subprocess.run(
                [sys.executable, "-c", _LOAD_SCRIPT],
                cwd=_REPO,
                env=env,
                capture_output=True,
                text=True,
                timeout=_TIMEOUT_S,
            )
        except subprocess.TimeoutExpired:
            self.fail(
                f"{_TIMEOUT_S}s and still running: concurrent _build_config "
                "deadlocked on a shared SQLite connection (KNOWN_TRAPS T14)"
            )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("ok", proc.stdout)


class TestPerThreadConnections(unittest.TestCase):
    """The connection-handling contract the fix relies on, in process."""

    @classmethod
    def setUpClass(cls):
        from motoquant import api

        cls.api = api
        cls.tmp = tempfile.mkdtemp(prefix="mq_db_threads_")
        cls.db = os.path.join(cls.tmp, "motoquant.db")
        shutil.copyfile(_REPO_DB, cls.db)
        cls.prior_env = os.environ.get("MOTOQUANT_DB")
        os.environ["MOTOQUANT_DB"] = cls.db
        cls._reset()

    @classmethod
    def tearDownClass(cls):
        cls._reset()
        if cls.prior_env is None:
            os.environ.pop("MOTOQUANT_DB", None)
        else:
            os.environ["MOTOQUANT_DB"] = cls.prior_env
        shutil.rmtree(cls.tmp, ignore_errors=True)

    @classmethod
    def _reset(cls):
        if cls.api._db_conn is not None:
            cls.api._db_conn.close()
        cls.api._db_conn = None

    def _in_thread(self, fn):
        out = []
        t = threading.Thread(target=lambda: out.append(fn()))
        t.start()
        t.join(30)
        self.assertFalse(t.is_alive())
        return out[0]

    def test_each_thread_gets_its_own_connection(self):
        api = self.api
        mine = api._get_db()
        self.assertIs(api._get_db(), mine, "one connection per thread, reused")
        self.assertIs(api._get_db_facade().conn, mine)
        other = self._in_thread(api._get_db)
        self.assertIsNot(other, mine)
        self.assertIsNot(mine, api._db_conn, "the token connection is not shared out")

    def test_a_write_from_any_api_thread_invalidates_the_catalog_token(self):
        api = self.api
        api._get_db()
        before = api._catalog_token()

        def write():
            conn = api._get_db()
            conn.execute("UPDATE venues SET name = name WHERE id = 1")
            conn.commit()

        self._in_thread(write)
        self.assertNotEqual(api._catalog_token(), before)
        after = api._catalog_token()
        self._in_thread(
            lambda: api._get_db().execute("SELECT * FROM venues").fetchall()
        )
        self.assertEqual(api._catalog_token(), after, "reads must not invalidate")

    def test_resetting_the_shared_handle_reopens_every_thread(self):
        api = self.api
        old = api._get_db()
        self._reset()
        new = api._get_db()
        self.assertIsNot(new, old)
        self.assertEqual(new.execute("SELECT 1").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
