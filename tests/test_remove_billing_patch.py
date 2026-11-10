"""scripts/patch_2026_11_09_remove_billing.py on a temp DB.

Builds a legacy-shaped database (users table with billing columns + an index
on one of them, plus the four retired tables), applies the patch, and checks
the billing schema is gone, accounts survive, and a second run is a no-op.
Never touches the tracked motoquant.db.
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
    / "patch_2026_11_09_remove_billing.py"
)
_spec = importlib.util.spec_from_file_location("patch_remove_billing", _SCRIPT)
patch_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(patch_mod)

_LEGACY = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    tier TEXT NOT NULL DEFAULT 'free' CHECK(tier IN ('free','pro','studio')),
    is_active INTEGER NOT NULL DEFAULT 1,
    razorpay_customer_id TEXT,
    stripe_customer_id TEXT,
    password_hash TEXT,
    email_verified INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_users_stripe ON users(stripe_customer_id);
CREATE TABLE subscriptions (id INTEGER PRIMARY KEY, user_id INTEGER);
CREATE TABLE license_keys (id INTEGER PRIMARY KEY, user_id INTEGER);
CREATE TABLE payment_events (id INTEGER PRIMARY KEY);
CREATE TABLE sim_usage (id INTEGER PRIMARY KEY, identity TEXT, day TEXT, count INT);
INSERT INTO users (email, tier, password_hash) VALUES ('a@b.in', 'pro', 'scrypt$x');
INSERT INTO sim_usage (identity, day, count) VALUES ('anon:x', '2026-01-01', 3);
"""


class TestRemoveBillingPatch(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(prefix="mq_rmbilling_", suffix=".db")
        os.close(fd)
        conn = sqlite3.connect(self.path)
        conn.executescript(_LEGACY)
        conn.commit()
        conn.close()

    def tearDown(self):
        os.unlink(self.path)

    def _schema(self):
        conn = sqlite3.connect(self.path)
        try:
            tables = {
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            cols = {r[1] for r in conn.execute("PRAGMA table_info(users)")}
            indexes = {
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='index'"
                )
            }
            return tables, cols, indexes
        finally:
            conn.close()

    def test_drops_billing_schema_and_keeps_accounts(self):
        summary = patch_mod.apply(self.path)
        tables, cols, indexes = self._schema()
        for t in patch_mod.DROP_TABLES:
            self.assertNotIn(t, tables)
        for c in patch_mod.DROP_USER_COLUMNS:
            self.assertNotIn(c, cols)
        self.assertNotIn("idx_users_stripe", indexes)
        self.assertIn("users", tables)
        self.assertLessEqual({"id", "email", "password_hash", "is_active"}, cols)
        conn = sqlite3.connect(self.path)
        row = conn.execute("SELECT email, password_hash FROM users").fetchone()
        conn.close()
        self.assertEqual(row, ("a@b.in", "scrypt$x"))
        self.assertEqual(summary["changes"], 4 + 3 + 1)

    def test_second_run_reports_zero_changes(self):
        patch_mod.apply(self.path)
        again = patch_mod.apply(self.path)
        self.assertEqual(again["changes"], 0, again)

    def test_users_inserts_work_after_patch(self):
        """The runtime's INSERTs (no tier column) must work on a patched DB."""
        patch_mod.apply(self.path)
        conn = sqlite3.connect(self.path)
        conn.execute("INSERT INTO users (email, is_active) VALUES ('c@d.in', 1)")
        conn.commit()
        conn.close()

    def test_runtime_works_on_an_unpatched_legacy_db(self):
        """Existing DBs keep the NOT NULL tier column; inserts without it
        must still succeed via its default."""
        from motoquant.database import users_repo

        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        user = users_repo.get_or_create_user(conn, "new@legacy.in")
        self.assertEqual(user["email"], "new@legacy.in")
        users_repo.ensure_tables(conn)
        conn.close()

    def test_fresh_schema_has_no_billing_columns(self):
        from motoquant.database import users_repo

        conn = sqlite3.connect(":memory:")
        users_repo.ensure_tables(conn)
        cols = {r[1] for r in conn.execute("PRAGMA table_info(users)")}
        tables = {
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        conn.close()
        self.assertTrue(cols.isdisjoint(patch_mod.DROP_USER_COLUMNS), cols)
        self.assertTrue(tables.isdisjoint(patch_mod.DROP_TABLES), tables)


if __name__ == "__main__":
    unittest.main()
