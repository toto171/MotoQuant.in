"""
tests/test_fixwave_data_seed.py
===============================
October 2026 core-audit fix wave — ``db seed`` / ``make db`` on the shipped
catalog must not revert curated patch data.

Before the fix, ``seed_all()`` on a copy of the shipped motoquant.db rewrote
468 part rows (prices, brand-doubled names, 'discontinued' -> 'in_stock',
fitment rules, mass deltas), stamped last_price_check=today on all 593 parts,
reverted 38 tires (24 discontinued flags), superseded 32 curated OEM fitments
and minted 3 phantom reference-config versions — data no seed source carries.
The production path is exercised end to end: the CLI ``db seed`` handler.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import logging
import os
import sqlite3
import tempfile
from pathlib import Path

import pytest

from motoquant.database.connection import MotoQuantDB
from motoquant.database.seed import seed_all
from tests._helpers import live_db_copy

# These tests assert properties of the SHIPPED catalog, so copy the repo's
# motoquant.db explicitly: live_db_copy() alone prefers $MOTOQUANT_DB, which
# other test modules redirect to a bare temp DB at import time.
_SHIPPED_DB = Path(__file__).resolve().parent.parent / "motoquant.db"

_FROZEN = ("parts", "tire_models", "bike_configs", "dyno_curves", "data_provenance")


def _snap(path, tables):
    c = sqlite3.connect(path)
    out = {t: c.execute(f"SELECT * FROM {t} ORDER BY id").fetchall() for t in tables}
    c.close()
    return out


def _oem(path):
    c = sqlite3.connect(path)
    rows = c.execute(
        "SELECT id, bike_model_id, tire_model_id, position, fitment_type, is_default"
        " FROM bike_tire_fitments"
    ).fetchall()
    c.close()
    return {r[0]: r[1:] for r in rows}


@pytest.fixture
def shipped_copy():
    d = live_db_copy(_SHIPPED_DB)
    if d is None:
        pytest.skip("motoquant.db not available")
    path = str(d.path)
    d.close()
    yield path
    for suffix in ("", "-wal", "-shm"):
        if os.path.exists(path + suffix):
            os.unlink(path + suffix)


def _cli_db_seed(path):
    from motoquant.run import cmd_db

    args = argparse.Namespace(db_action="seed", db=path)
    logging.disable(logging.CRITICAL)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_db(args)
    finally:
        logging.disable(logging.NOTSET)


class TestSeedPreservesShippedCatalog:
    def test_cli_db_seed_leaves_curated_rows_untouched(self, shipped_copy):
        before = _snap(shipped_copy, _FROZEN)
        fits_before = _oem(shipped_copy)
        _cli_db_seed(shipped_copy)
        after = _snap(shipped_copy, _FROZEN)
        for table in _FROZEN:
            assert after[table] == before[table], f"{table} was rewritten by db seed"
        fits_after = _oem(shipped_copy)
        # Existing fitment rows are never removed or changed; a re-seed may
        # only ADD rows for slots/tires that have none (additive backfill).
        assert {k: fits_after.get(k) for k in fits_before} == fits_before

    def test_second_seed_is_a_fixpoint(self, shipped_copy):
        _cli_db_seed(shipped_copy)
        tables = _FROZEN + ("bike_tire_fitments", "bike_models", "manufacturers")
        once = _snap(shipped_copy, tables)
        _cli_db_seed(shipped_copy)
        assert _snap(shipped_copy, tables) == once

    def test_overwrite_existing_restores_seed_source_wins(self, shipped_copy):
        """The old behaviour is still available, explicitly."""
        db = MotoQuantDB(shipped_copy)
        db.connect()
        logging.disable(logging.CRITICAL)
        try:
            seed_all(db, overwrite_existing=True)
        finally:
            logging.disable(logging.NOTSET)
        changed = db.conn.execute(
            "SELECT COUNT(*) FROM parts WHERE model_name LIKE brand || ' %'"
        ).fetchone()[0]
        db.close()
        assert changed > 0  # brand-doubled seed names written back


class TestFreshSeedUnchanged:
    def test_fresh_seed_still_populates_everything(self):
        db = MotoQuantDB(":memory:")
        db.initialize()
        logging.disable(logging.CRITICAL)
        try:
            summary = seed_all(db)
        finally:
            logging.disable(logging.NOTSET)
        assert summary["parts"] >= 590
        assert db.conn.execute("SELECT COUNT(*) FROM tire_models").fetchone()[0] > 150
        assert db.parts.protect_ids_upto is None  # protection is released
        assert db.tires.protect_ids_upto is None
        db.close()


class TestRepoUpsertModes:
    @pytest.fixture
    def fresh(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        d = MotoQuantDB(tmp.name)
        d.initialize()
        yield d
        d.close()
        os.unlink(tmp.name)

    def test_update_existing_false_keeps_the_row(self, fresh):
        pid = fresh.parts.create(
            "exhaust",
            "Akrapovic",
            "Slip-On",
            {"x": 1},
            part_number="AK-X",
            price_inr=1000.0,
        )
        assert (
            fresh.parts.create(
                "exhaust",
                "Akrapovic",
                "Renamed",
                {"x": 2},
                part_number="AK-X",
                price_inr=9.0,
                update_existing=False,
            )
            == pid
        )
        row = fresh.parts.get(pid)
        assert (row["model_name"], row["price_inr"]) == ("Slip-On", 1000.0)

    def test_check_date_moves_only_when_the_price_changes(self, fresh):
        pid = fresh.parts.create(
            "exhaust", "Akrapovic", "Slip-On", {}, part_number="AK-Y", price_inr=1000.0
        )
        fresh.conn.execute(
            "UPDATE parts SET last_price_check = '2020-01-01' WHERE id = ?", (pid,)
        )
        fresh.parts.create(
            "exhaust",
            "Akrapovic",
            "Slip-On v2",
            {},
            part_number="AK-Y",
            price_inr=1000.0,
        )
        assert fresh.parts.get(pid)["last_price_check"] == "2020-01-01"
        fresh.parts.create(
            "exhaust",
            "Akrapovic",
            "Slip-On v2",
            {},
            part_number="AK-Y",
            price_inr=1200.0,
        )
        assert fresh.parts.get(pid)["last_price_check"] != "2020-01-01"

    def test_tire_update_existing_false_keeps_the_row(self, fresh):
        tid = fresh.tires.create("MRF", "Zapper Q", "100/80-17", "sport", mu_peak=1.1)
        fresh.tires.create(
            "MRF", "Zapper Q", "100/80-17", "sport", mu_peak=1.9, update_existing=False
        )
        assert fresh.tires.get(tid)["mu_peak"] == pytest.approx(1.1)
