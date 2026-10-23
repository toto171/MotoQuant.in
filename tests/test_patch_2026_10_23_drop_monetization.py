"""
Tests for scripts/patch_2026_10_23_drop_monetization.py.

Each test builds the PRE-patch state itself (the exact pre-pivot DDL for
users + the four billing tables, plus catalog-like tables carrying rows), then
drives the real ``apply()``. A test that only re-ran the patch on an
already-patched shipped DB would pass even if ``apply()`` did nothing.
"""

from __future__ import annotations

import importlib.util
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

_SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "patch_2026_10_23_drop_monetization.py"
)
_spec = importlib.util.spec_from_file_location("drop_monetization", _SCRIPT)
patch_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(patch_mod)

_PRE_PIVOT_DDL = """
CREATE TABLE manufacturers (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE bike_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manufacturer_id INTEGER NOT NULL REFERENCES manufacturers(id),
    model_name TEXT NOT NULL
);
CREATE TABLE sim_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    et_quarter_s REAL,
    user_id INTEGER
);
CREATE TABLE users (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    email                   TEXT    NOT NULL UNIQUE,
    tier                    TEXT    NOT NULL DEFAULT 'free'
                                    CHECK(tier IN ('free','pro','studio')),
    is_active               INTEGER NOT NULL DEFAULT 1,
    razorpay_customer_id    TEXT,
    stripe_customer_id      TEXT,
    password_hash           TEXT,
    email_verified          INTEGER NOT NULL DEFAULT 0,
    created_at              TEXT    DEFAULT (datetime('now','utc')),
    updated_at              TEXT    DEFAULT (datetime('now','utc'))
);
CREATE INDEX idx_users_email ON users(email);
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    jwt_id TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    revoked INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    razorpay_subscription_id TEXT NOT NULL UNIQUE,
    tier TEXT NOT NULL,
    status TEXT NOT NULL
);
CREATE INDEX idx_subs_user ON subscriptions(user_id);
CREATE TABLE license_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash TEXT NOT NULL UNIQUE
);
CREATE TABLE payment_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    event_id TEXT NOT NULL,
    UNIQUE(provider, event_id)
);
CREATE TABLE sim_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    identity TEXT NOT NULL,
    day TEXT NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    UNIQUE(identity, day)
);
"""


def _build_pre_pivot_db(path: str) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(_PRE_PIVOT_DDL)
    conn.execute("INSERT INTO manufacturers VALUES (1, 'Suzuki'), (2, 'Yamaha')")
    conn.executemany(
        "INSERT INTO bike_models (manufacturer_id, model_name) VALUES (?, ?)",
        [(1, "GSX-R1000 K5"), (2, "YZF-R1"), (1, "Hayabusa")],
    )
    conn.execute(
        "INSERT INTO users (email, tier, password_hash) VALUES ('a@t.in', 'pro', 'x')"
    )
    conn.execute("INSERT INTO users (email) VALUES ('b@t.in')")
    conn.execute(
        "INSERT INTO sessions (user_id, jwt_id, expires_at) "
        "VALUES (1, 'jti-1', '2099-01-01 00:00:00')"
    )
    conn.execute("INSERT INTO sim_runs (et_quarter_s, user_id) VALUES (9.93, 1)")
    conn.execute(
        "INSERT INTO subscriptions (user_id, razorpay_subscription_id, tier, status) "
        "VALUES (1, 'sub_1', 'pro', 'active')"
    )
    conn.execute("INSERT INTO license_keys (user_id, key_hash) VALUES (1, 'h')")
    conn.execute("INSERT INTO payment_events (provider, event_id) VALUES ('rzp', 'e')")
    conn.execute(
        "INSERT INTO sim_usage (identity, day) VALUES ('anon:x', '2026-10-01')"
    )
    conn.commit()
    conn.close()


def _tables(path: str) -> set[str]:
    conn = sqlite3.connect(path)
    try:
        return {
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    finally:
        conn.close()


class TestDropMonetization(unittest.TestCase):
    def setUp(self):
        fd, self.db = tempfile.mkstemp(prefix="mq_dropmon_", suffix=".db")
        os.close(fd)
        os.unlink(self.db)
        _build_pre_pivot_db(self.db)

    def tearDown(self):
        for suffix in ("", "-wal", "-shm"):
            try:
                os.unlink(self.db + suffix)
            except OSError:
                pass

    def test_drops_tables_and_columns(self):
        summary = patch_mod.apply(self.db, verbose=False)
        self.assertEqual(
            sorted(summary["dropped_tables"]), sorted(patch_mod.DEAD_TABLES)
        )
        self.assertEqual(summary["dropped_columns"], list(patch_mod.DEAD_USER_COLUMNS))
        self.assertEqual(summary["integrity"], "ok")
        tables = _tables(self.db)
        for dead in patch_mod.DEAD_TABLES:
            self.assertNotIn(dead, tables)
        conn = sqlite3.connect(self.db)
        try:
            cols = {r[1] for r in conn.execute("PRAGMA table_info(users)")}
            seq = dict(conn.execute("SELECT name, seq FROM sqlite_sequence"))
        finally:
            conn.close()
        for dead in patch_mod.DEAD_USER_COLUMNS:
            self.assertNotIn(dead, cols)
        self.assertTrue({"email", "is_active", "password_hash"} <= cols)
        for dead in patch_mod.DEAD_TABLES:
            self.assertNotIn(dead, seq)

    def test_every_surviving_row_is_kept(self):
        conn = sqlite3.connect(self.db)
        before = {
            t: conn.execute(f"SELECT * FROM {t} ORDER BY id").fetchall()
            for t in ("manufacturers", "bike_models", "sim_runs", "sessions")
        }
        users_before = conn.execute(
            "SELECT id, email, is_active, password_hash FROM users ORDER BY id"
        ).fetchall()
        conn.close()
        patch_mod.apply(self.db, verbose=False)
        conn = sqlite3.connect(self.db)
        try:
            for t, rows in before.items():
                self.assertEqual(
                    conn.execute(f"SELECT * FROM {t} ORDER BY id").fetchall(), rows, t
                )
            self.assertEqual(
                conn.execute(
                    "SELECT id, email, is_active, password_hash FROM users ORDER BY id"
                ).fetchall(),
                users_before,
            )
        finally:
            conn.close()

    def test_second_run_is_a_no_op(self):
        patch_mod.apply(self.db, verbose=False)
        again = patch_mod.apply(self.db, verbose=False)
        self.assertEqual(again["dropped_tables"], [])
        self.assertEqual(again["dropped_columns"], [])
        self.assertEqual(again["integrity"], "ok")

    def test_dry_run_writes_nothing(self):
        summary = patch_mod.apply(self.db, dry_run=True, verbose=False)
        self.assertTrue(summary["dry_run"])
        self.assertEqual(summary["dropped_tables"], [])
        self.assertTrue(set(patch_mod.DEAD_TABLES) <= _tables(self.db))

    def test_patched_users_table_still_accepts_signups(self):
        """The live INSERTs (users_repo) must work on the patched schema."""
        from motoquant.database import users_repo

        patch_mod.apply(self.db, verbose=False)
        conn = sqlite3.connect(self.db)
        conn.row_factory = sqlite3.Row
        try:
            users_repo.ensure_tables(conn)
            u = users_repo.get_or_create_user(conn, "new@t.in")
            p = users_repo.create_user_with_password(conn, "pw@t.in", "scrypt$x")
        finally:
            conn.close()
        self.assertEqual(u["email"], "new@t.in")
        self.assertEqual(p["email"], "pw@t.in")
        self.assertNotIn("tier", u)

    def test_failed_post_condition_rolls_back(self):
        """If verification fails, NOTHING is committed."""
        original = patch_mod._row_counts
        calls = {"n": 0}

        def corrupt_after(conn, skip):
            calls["n"] += 1
            counts = original(conn, skip)
            if calls["n"] == 2:  # the post-change snapshot
                counts["manufacturers"] = -1
            return counts

        patch_mod._row_counts = corrupt_after
        try:
            with self.assertRaises(RuntimeError):
                patch_mod.apply(self.db, verbose=False)
        finally:
            patch_mod._row_counts = original
        self.assertTrue(set(patch_mod.DEAD_TABLES) <= _tables(self.db))
        conn = sqlite3.connect(self.db)
        try:
            cols = {r[1] for r in conn.execute("PRAGMA table_info(users)")}
        finally:
            conn.close()
        self.assertIn("tier", cols)

    def test_missing_db_is_an_error_not_a_new_file(self):
        missing = self.db + ".nope"
        with self.assertRaises(FileNotFoundError):
            patch_mod.apply(missing, verbose=False)
        self.assertFalse(os.path.exists(missing))


class TestShippedDatabase(unittest.TestCase):
    """The tracked catalog must already be patched (read-only check)."""

    def test_shipped_db_has_no_billing_schema(self):
        shipped = Path(__file__).resolve().parent.parent / "motoquant.db"
        if not shipped.exists():
            self.skipTest("motoquant.db not present in this checkout")
        conn = sqlite3.connect(f"file:{shipped}?mode=ro", uri=True)
        try:
            todo = patch_mod.plan(conn)
        finally:
            conn.close()
        self.assertEqual(
            todo,
            {"tables": [], "columns": []},
            "motoquant.db still ships billing tables/columns — run "
            "scripts/patch_2026_10_23_drop_monetization.py",
        )


if __name__ == "__main__":
    unittest.main()
