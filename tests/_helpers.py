"""
MotoQuant Pro — Shared test helpers
=====================================
Common fixtures used across multiple test modules.

Why this exists
---------------
`tests/test_analysis.py` and `tests/test_recommendations.py` previously
each defined an identical `_TestDB` class-method-cached singleton that
creates a temp DB in /tmp, sets `PRAGMA journal_mode=DELETE` (WAL-fallback
for FUSE-mounted filesystems), and runs `seed_all(mdb)` exactly once per
process. The two copies drifted independently and bloated each test file
by ~30 lines. They now share `SeededTestDB` here.

`tests/test_cli.py` uses a related-but-distinct pattern — a `MotoQuantDB`
subclass that overrides `.connect()` so a pytest module-scoped fixture
can manage DB lifecycle around CLI command tests. That subclass is
`WalDisabledDB` below.

`tests/test_power_boost_regression.py` and `tests/test_chat_resolver.py`
both need read access to the *live* `motoquant.db` (catalog seed) but
can't open it in-place under the FUSE sandbox because WAL/journal pragmas
fail. They share `live_db_copy()` below, which copies the live DB into
/tmp and opens it via MotoQuantDB.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import tempfile
from pathlib import Path

from motoquant.database.connection import MotoQuantDB


class WalDisabledDB(MotoQuantDB):
    """MotoQuantDB subclass that forces DELETE journal mode.

    Used by tests whose DB lives on a filesystem (or sandbox mount) that
    rejects WAL pragmas. Mirrors `MotoQuantDB.connect()` byte-for-byte
    except for the `PRAGMA journal_mode` value.
    """

    def connect(self):
        if self._conn is not None:
            return self._conn
        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=DELETE")
        self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn


class SeededTestDB:
    """Process-scoped seeded MotoQuantDB cached as a class singleton.

    The DB is created in /tmp (always a real filesystem — avoids FUSE
    WAL-rejection by switching to DELETE journal mode), initialised, and
    fully seeded via ``seed_all`` on first access. Subsequent calls reuse
    the same MotoQuantDB instance.

    Public surface mirrors what the original `_TestDB` classes exposed:

    * ``SeededTestDB.get_mdb()`` -> MotoQuantDB
    * ``SeededTestDB.get_conn()`` -> sqlite3.Connection
    * ``SeededTestDB._db_path``   -> str (the on-disk path; used by CLI
                                          tests that pass ``--db`` to the
                                          run.py entry point)
    """

    _db_path: str | None = None
    _mdb: MotoQuantDB | None = None

    @classmethod
    def get_mdb(cls) -> MotoQuantDB:
        if cls._mdb is None:
            tmp = tempfile.NamedTemporaryFile(suffix=".db", dir="/tmp", delete=False)
            cls._db_path = tmp.name
            tmp.close()
            mdb = MotoQuantDB(cls._db_path)
            mdb.connect()
            mdb.conn.execute("PRAGMA journal_mode=DELETE")
            mdb.initialize()
            # Run full catalog seed (tires, parts, bikes, fitments)
            from motoquant.database.seed import seed_all

            seed_all(mdb)
            cls._mdb = mdb
        return cls._mdb

    @classmethod
    def get_conn(cls):
        return cls.get_mdb().conn


def live_db_copy(src_path: str | os.PathLike | None = None) -> MotoQuantDB | None:
    """Copy the live `motoquant.db` to /tmp and open it via MotoQuantDB.

    Used by tests that need read access to the real seeded catalog but
    cannot open the file in-place because the FUSE sandbox rejects
    sqlite WAL/journal pragmas on the workspace mount.

    Parameters
    ----------
    src_path:
        Optional override for the source DB path. When ``None`` the helper
        falls back to ``$MOTOQUANT_DB``, then to ``motoquant.db`` (CWD),
        then to ``<repo-root>/motoquant.db`` relative to this file.

    Returns
    -------
    MotoQuantDB | None
        Connected DB instance, or ``None`` if no source DB was found.
        Callers should ``unittest.skipTest`` (or equivalent) on ``None``.
    """
    candidates: list[str] = []
    if src_path is not None:
        candidates.append(str(src_path))
    env_path = os.environ.get("MOTOQUANT_DB")
    if env_path:
        candidates.append(env_path)
    candidates.append("motoquant.db")
    candidates.append(str(Path(__file__).resolve().parent.parent / "motoquant.db"))

    resolved = next((c for c in candidates if c and os.path.exists(c)), None)
    if resolved is None:
        return None

    tmp = tempfile.NamedTemporaryFile(suffix=".db", dir="/tmp", delete=False)
    tmp.close()
    shutil.copy(resolved, tmp.name)
    db = MotoQuantDB(db_path=tmp.name)
    db.connect()
    return db
