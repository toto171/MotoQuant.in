"""The billing-schema removal patch on a legacy-shaped temp DB.

Two branches each wrote a script that drops the retired billing schema
(``patch_2026_10_23_drop_monetization.py`` and ``patch_2026_11_09_remove_
billing.py``). ONE script is kept: ``scripts/patch_2026_10_23_drop_monetization
.py``. These tests are the second branch's, re-pointed at the kept script, and
pin the two things that branch had and the kept script did not:

  * the union of what both dropped is dropped (same four tables, same three
    ``users`` columns - pinned literally here so neither list can shrink);
  * an index covering a doomed column does not block the ``DROP COLUMN``
    (SQLite refuses to drop an indexed column; the index goes first).

The kept script's own behaviour (transaction, row-count post-conditions, dry
run) is covered by tests/test_patch_2026_10_23_drop_monetization.py. Never
touches the tracked motoquant.db.
"""

from __future__ import annotations

import importlib.util
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
_SCRIPT = _SCRIPTS / "patch_2026_10_23_drop_monetization.py"
_spec = importlib.util.spec_from_file_location("patch_remove_billing", _SCRIPT)
patch_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(patch_mod)

# What the removed 2026-11-09 script dropped (its DROP_TABLES /
# DROP_USER_COLUMNS), written out so the union is pinned.
_UNION_TABLES = {"subscriptions", "license_keys", "payment_events", "sim_usage"}
_UNION_USER_COLUMNS = {"tier", "razorpay_customer_id", "stripe_customer_id"}

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
CREATE INDEX idx_users_email ON users(email);
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
        for suffix in ("", "-wal", "-shm"):
            try:
                os.unlink(self.path + suffix)
            except OSError:
                pass

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

    def test_one_script_and_it_drops_the_union(self):
        self.assertFalse(
            (_SCRIPTS / "patch_2026_11_09_remove_billing.py").exists(),
            "two billing-removal scripts again: keep only the 2026-10-23 one",
        )
        self.assertEqual(set(patch_mod.DEAD_TABLES), _UNION_TABLES)
        self.assertEqual(set(patch_mod.DEAD_USER_COLUMNS), _UNION_USER_COLUMNS)

    def test_drops_billing_schema_and_keeps_accounts(self):
        summary = patch_mod.apply(self.path, verbose=False)
        tables, cols, indexes = self._schema()
        for t in _UNION_TABLES:
            self.assertNotIn(t, tables)
        for c in _UNION_USER_COLUMNS:
            self.assertNotIn(c, cols)
        self.assertIn("users", tables)
        self.assertLessEqual({"id", "email", "password_hash", "is_active"}, cols)
        conn = sqlite3.connect(self.path)
        row = conn.execute("SELECT email, password_hash FROM users").fetchone()
        conn.close()
        self.assertEqual(row, ("a@b.in", "scrypt$x"))
        self.assertEqual(sorted(summary["dropped_tables"]), sorted(_UNION_TABLES))
        self.assertEqual(
            sorted(summary["dropped_columns"]), sorted(_UNION_USER_COLUMNS)
        )
        self.assertEqual(summary["skipped_columns"], [])

    def test_index_on_a_doomed_column_does_not_block_the_drop(self):
        """Without dropping idx_users_stripe first, SQLite raises "error in
        index idx_users_stripe after drop column" and the column survives."""
        summary = patch_mod.apply(self.path, verbose=False)
        _tables, cols, indexes = self._schema()
        self.assertNotIn("stripe_customer_id", cols)
        self.assertNotIn("idx_users_stripe", indexes)
        self.assertEqual(summary["dropped_indexes"], ["idx_users_stripe"])
        # an index on a surviving column is not touched
        self.assertIn("idx_users_email", indexes)

    def test_second_run_reports_zero_changes(self):
        patch_mod.apply(self.path, verbose=False)
        again = patch_mod.apply(self.path, verbose=False)
        self.assertEqual(
            (
                again["dropped_tables"],
                again["dropped_columns"],
                again["dropped_indexes"],
                again["skipped_columns"],
            ),
            ([], [], [], []),
            again,
        )

    def test_users_inserts_work_after_patch(self):
        """The runtime's INSERTs (no tier column) must work on a patched DB."""
        patch_mod.apply(self.path, verbose=False)
        conn = sqlite3.connect(self.path)
        conn.execute("INSERT INTO users (email, is_active) VALUES ('c@d.in', 1)")
        conn.commit()
        conn.close()


if __name__ == "__main__":
    unittest.main()
