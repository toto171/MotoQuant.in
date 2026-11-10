"""scripts/patch_2026_11_10_remove_accounts.py — drops the account schema.

Built on a copy of the shipped catalog with the old account storage put back
(the shipped database has already been patched), so each test exercises the
patch exactly as it ran on the real file.
"""

from __future__ import annotations

import importlib.util
import shutil
import sqlite3
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "patch_remove_accounts",
    _REPO / "scripts" / "patch_2026_11_10_remove_accounts.py",
)
patch_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(patch_mod)

_OLD_SCHEMA = """
CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE);
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id));
CREATE TABLE magic_links (
    id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id));
CREATE TABLE spec_corrections (
    id INTEGER PRIMARY KEY AUTOINCREMENT, bike_model_id INTEGER,
    field_name TEXT, proposed_value TEXT, submitter_email TEXT);
ALTER TABLE sim_runs ADD COLUMN user_id INTEGER;
CREATE INDEX idx_runs_user ON sim_runs(user_id);
INSERT INTO users (email) VALUES ('rider@example.com');
INSERT INTO sessions (user_id) VALUES (1);
INSERT INTO spec_corrections (bike_model_id, field_name, proposed_value)
    VALUES (3, 'peak_power_hp', '180');
INSERT INTO sim_runs (bike_config_id, et_quarter_s, trap_speed_kmh, user_id)
    VALUES (1, 10.5, 230.0, 1);
"""


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "old.db"
    shutil.copyfile(_REPO / "motoquant.db", path)
    conn = sqlite3.connect(path)
    conn.executescript(_OLD_SCHEMA)
    conn.commit()
    conn.close()
    return str(path)


def _tables(path):
    conn = sqlite3.connect(path)
    try:
        return {
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    finally:
        conn.close()


def test_drops_account_tables_and_column_keeps_runs(db):
    summary = patch_mod.apply(db, verbose=False)
    assert summary["dropped_tables"] == list(patch_mod.DEAD_TABLES)
    assert summary["dropped_columns"] == ["sim_runs.user_id"]
    assert summary["dropped_indexes"] == ["idx_runs_user"]
    assert summary["integrity"] == "ok"
    tables = _tables(db)
    for dead in patch_mod.DEAD_TABLES:
        assert dead not in tables
    conn = sqlite3.connect(db)
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(sim_runs)")}
        runs = conn.execute("SELECT COUNT(*) FROM sim_runs").fetchone()[0]
        bikes = conn.execute("SELECT COUNT(*) FROM bike_models").fetchone()[0]
    finally:
        conn.close()
    assert "user_id" not in cols
    assert runs == 1
    assert bikes == 534


def test_second_run_changes_nothing(db):
    patch_mod.apply(db, verbose=False)
    again = patch_mod.apply(db, verbose=False)
    assert again["dropped_tables"] == []
    assert again["dropped_columns"] == []


def test_dry_run_writes_nothing(db):
    before = _tables(db)
    summary = patch_mod.apply(db, dry_run=True, verbose=False)
    assert summary["dry_run"] is True
    assert _tables(db) == before


def test_failed_post_condition_rolls_back(db, monkeypatch):
    original = patch_mod._row_counts
    calls = {"n": 0}

    def corrupt_after(conn, skip):
        calls["n"] += 1
        counts = original(conn, skip)
        if calls["n"] == 2:
            counts["bike_models"] = -1
        return counts

    monkeypatch.setattr(patch_mod, "_row_counts", corrupt_after)
    with pytest.raises(RuntimeError):
        patch_mod.apply(db, verbose=False)
    assert "users" in _tables(db)


def test_shipped_catalog_is_already_patched():
    plan = patch_mod.plan(sqlite3.connect(_REPO / "motoquant.db"))
    assert plan == {"tables": [], "columns": []}
