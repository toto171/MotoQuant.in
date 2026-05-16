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
"""

from __future__ import annotations

import sqlite3
import tempfile
from typing import Optional

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

    _db_path: Optional[str] = None
    _mdb: Optional[MotoQuantDB] = None

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
