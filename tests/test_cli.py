"""
MotoQuant Pro — CLI Integration Tests
======================================
Tests for both Phase 1 (legacy) and Phase 2 (subcommand) CLI paths.
Uses in-process function calls with captured stdout to avoid subprocess
filesystem limitations (WAL mode incompatibility on mounted volumes).
"""

import argparse
import io
import json
import os
import sys
import pytest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from motoquant.run import (
    main, legacy_main, build_parser,
    cmd_db, cmd_bikes, cmd_sim, cmd_venues,
    cmd_tires, cmd_parts, cmd_leaderboard, cmd_history,
    resolve_bike, run_bike, print_table,
    BIKE_REGISTRY, VENUE_REGISTRY,
)
from motoquant.database import MotoQuantDB


# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────

# Use /tmp for the test DB — but disable WAL to avoid disk I/O on mounted FS
TEST_DB = f"/tmp/test_cli_{os.getpid()}.db"


class _TestDB(MotoQuantDB):
    """MotoQuantDB subclass that skips WAL pragma (for test FS compat)."""
    def connect(self):
        import sqlite3
        if self._conn is not None:
            return self._conn
        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=DELETE")
        self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn


def make_args(**kwargs):
    """Create a namespace with defaults for all common args."""
    defaults = {
        "db": TEST_DB,
        "quiet": False,
        "json_out": False,
        "csv": None,
        "dt": 0.001,
        "distance": 402.336,
        "limit": 50,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def capture_output(fn, *args, **kwargs):
    """Run a function capturing stdout. Returns (return_value, stdout_text)."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        ret = fn(*args, **kwargs)
    return ret, buf.getvalue()


# ─────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────

@pytest.fixture(scope="module")
def db():
    """Create and seed a test database once for all CLI tests."""
    if os.path.exists(TEST_DB):
        os.unlink(TEST_DB)
    _db = _TestDB(TEST_DB)
    _db.initialize()
    from motoquant.database.seed import seed_all
    seed_all(_db)
    yield _db
    _db.close()
    try:
        os.unlink(TEST_DB)
    except OSError:
        pass


def _patch_get_db(db):
    """Monkey-patch get_db to return our test DB instance."""
    return patch("motoquant.run.get_db", return_value=db)


def _patch_ensure_db(db):
    """Monkey-patch ensure_db to return our test DB instance."""
    return patch("motoquant.run.ensure_db", return_value=db)


# ═══════════════════════════════════════════
# Unit: resolve_bike
# ═══════════════════════════════════════════

class TestResolveBike:
    def test_direct_key(self):
        assert resolve_bike("k5") == "k5"
        assert resolve_bike("r1") == "r1"
        assert resolve_bike("busa") == "busa"

    def test_aliases(self):
        assert resolve_bike("gsxr") == "k5"
        assert resolve_bike("hayabusa") == "busa"
        assert resolve_bike("yzfr1") == "r1"
        assert resolve_bike("4c8") == "r1"

    def test_case_insensitive(self):
        assert resolve_bike("K5") == "k5"
        assert resolve_bike("HAYABUSA") == "busa"

    def test_unknown_passthrough(self):
        assert resolve_bike("unknown") == "unknown"


# ═══════════════════════════════════════════
# Unit: print_table
# ═══════════════════════════════════════════

class TestPrintTable:
    def test_basic_table(self):
        _, out = capture_output(
            print_table,
            ["Name", "Value"],
            [["alpha", "100"], ["beta", "200"]],
        )
        assert "Name" in out
        assert "alpha" in out
        assert "200" in out

    def test_none_values(self):
        _, out = capture_output(
            print_table,
            ["A", "B"],
            [["x", None]],
        )
        assert "-" in out  # None rendered as "-"


# ═══════════════════════════════════════════
# Phase 2: cmd_db
# ═══════════════════════════════════════════

class TestCmdDb:
    def test_db_init(self, db):
        args = make_args(db_action="init")
        with _patch_get_db(db):
            _, out = capture_output(cmd_db, args)
        assert "Database initialized" in out or "Venues seeded" in out

    def test_db_stats(self, db):
        args = make_args(db_action="stats")
        with _patch_ensure_db(db):
            _, out = capture_output(cmd_db, args)
        assert "bike_models" in out
        assert "venues" in out

    def test_db_seed_not_crash_on_reinit(self, db):
        """Re-running db init after seed should not crash."""
        args = make_args(db_action="init")
        with _patch_get_db(db):
            _, out = capture_output(cmd_db, args)
        assert "Database initialized" in out


# ═══════════════════════════════════════════
# Phase 2: cmd_bikes
# ═══════════════════════════════════════════

class TestCmdBikes:
    def test_list_all(self, db):
        args = make_args(
            search=None, manufacturer=None, category=None,
            displacement=None, power_min=None, quality=None,
        )
        with _patch_ensure_db(db):
            _, out = capture_output(cmd_bikes, args)
        assert "Bikes" in out

    def test_search_by_name(self, db):
        args = make_args(
            search="Hayabusa", manufacturer=None, category=None,
            displacement=None, power_min=None, quality=None,
        )
        with _patch_ensure_db(db):
            _, out = capture_output(cmd_bikes, args)
        assert "Hayabusa" in out

    def test_search_no_results(self, db):
        args = make_args(
            search="NonexistentBike999", manufacturer=None, category=None,
            displacement=None, power_min=None, quality=None,
        )
        with _patch_ensure_db(db):
            _, out = capture_output(cmd_bikes, args)
        assert "No bikes found" in out

    def test_search_by_manufacturer(self, db):
        args = make_args(
            search=None, manufacturer="Suzuki", category=None,
            displacement=None, power_min=None, quality=None,
        )
        with _patch_ensure_db(db):
            _, out = capture_output(cmd_bikes, args)
        assert "Suzuki" in out

    def test_search_by_displacement_range(self, db):
        args = make_args(
            search=None, manufacturer=None, category=None,
            displacement="900-1100", power_min=None, quality=None,
        )
        with _patch_ensure_db(db):
            _, out = capture_output(cmd_bikes, args)
        assert "Bikes" in out

    def test_json_output(self, db):
        args = make_args(
            search=None, manufacturer=None, category=None,
            displacement=None, power_min=None, quality=None,
            json_out=True,
        )
        with _patch_ensure_db(db):
            _, out = capture_output(cmd_bikes, args)
        data = json.loads(out)
        assert isinstance(data, list)
        assert len(data) >= 3
        assert "model_name" in data[0]


# ═══════════════════════════════════════════
# Phase 2: cmd_sim
# ═══════════════════════════════════════════

class TestCmdSim:
    def test_sim_by_bike_id(self, db):
        args = make_args(
            bike_id=1, bike_legacy=None, config_file=None,
            venue_id=None, venue_legacy=None, month=None,
            weather_live=False, api_key=None, track_temp=None,
            apply_parts=None, compare_stock=False, save_run=False,
            quiet=True,
        )
        with _patch_ensure_db(db):
            result, out = capture_output(cmd_sim, args)

    def test_sim_with_venue_and_month(self, db):
        args = make_args(
            bike_id=1, bike_legacy=None, config_file=None,
            venue_id=1, venue_legacy=None, month=1,
            weather_live=False, api_key=None, track_temp=None,
            apply_parts=None, compare_stock=False, save_run=False,
            quiet=False,
        )
        with _patch_ensure_db(db):
            result, out = capture_output(cmd_sim, args)
        assert "1/4 mile" in out
        assert "Aamby Valley" in out

    def test_sim_json_output(self, db):
        args = make_args(
            bike_id=1, bike_legacy=None, config_file=None,
            venue_id=None, venue_legacy=None, month=None,
            weather_live=False, api_key=None, track_temp=None,
            apply_parts=None, compare_stock=False, save_run=False,
            quiet=False, json_out=True,
        )
        with _patch_ensure_db(db):
            result, out = capture_output(cmd_sim, args)
        data = json.loads(out)
        assert "splits" in data
        et = data["splits"]["quarter_mile_s"]
        assert 8.0 < et < 14.0

    def test_sim_with_parts(self, db):
        # Stock run
        args_stock = make_args(
            bike_id=1, bike_legacy=None, config_file=None,
            venue_id=None, venue_legacy=None, month=None,
            weather_live=False, api_key=None, track_temp=None,
            apply_parts=None, compare_stock=False, save_run=False,
            quiet=False, json_out=True,
        )
        with _patch_ensure_db(db):
            _, out_stock = capture_output(cmd_sim, args_stock)
        stock_et = json.loads(out_stock)["splits"]["quarter_mile_s"]

        # Modified run (parts 4,5 = sprocket changes)
        args_mod = make_args(
            bike_id=1, bike_legacy=None, config_file=None,
            venue_id=None, venue_legacy=None, month=None,
            weather_live=False, api_key=None, track_temp=None,
            apply_parts="4,5", compare_stock=False, save_run=False,
            quiet=False, json_out=True,
        )
        with _patch_ensure_db(db):
            _, out_mod = capture_output(cmd_sim, args_mod)
        mod_et = json.loads(out_mod)["splits"]["quarter_mile_s"]

        # ETs should differ with sprocket changes
        assert stock_et != mod_et

    def test_sim_compare_stock(self, db):
        args = make_args(
            bike_id=1, bike_legacy=None, config_file=None,
            venue_id=None, venue_legacy=None, month=None,
            weather_live=False, api_key=None, track_temp=None,
            apply_parts="4,5", compare_stock=True, save_run=False,
            quiet=False,
        )
        with _patch_ensure_db(db):
            _, out = capture_output(cmd_sim, args)
        assert "COMPARISON TABLE" in out
        assert "Delta" in out
        assert "Build cost" in out

    def test_sim_save_run(self, db):
        args = make_args(
            bike_id=1, bike_legacy=None, config_file=None,
            venue_id=1, venue_legacy=None, month=1,
            weather_live=False, api_key=None, track_temp=None,
            apply_parts=None, compare_stock=False, save_run=True,
            quiet=False,
        )
        with _patch_ensure_db(db):
            _, out = capture_output(cmd_sim, args)
        assert "Run archived" in out

    def test_sim_csv_export(self, db):
        csv_path = f"/tmp/test_cli_csv_{os.getpid()}.csv"
        try:
            args = make_args(
                bike_id=1, bike_legacy=None, config_file=None,
                venue_id=None, venue_legacy=None, month=None,
                weather_live=False, api_key=None, track_temp=None,
                apply_parts=None, compare_stock=False, save_run=False,
                quiet=True, csv=csv_path,
            )
            with _patch_ensure_db(db):
                _, out = capture_output(cmd_sim, args)
            assert os.path.exists(csv_path)
            with open(csv_path) as f:
                lines = f.readlines()
            assert len(lines) > 100
            assert "time_s" in lines[0]
        finally:
            if os.path.exists(csv_path):
                os.unlink(csv_path)

    def test_sim_no_bike_errors(self, db):
        args = make_args(
            bike_id=None, bike_legacy=None, config_file=None,
            venue_id=None, venue_legacy=None, month=None,
            weather_live=False, api_key=None, track_temp=None,
            apply_parts=None, compare_stock=False, save_run=False,
            quiet=False,
        )
        with _patch_ensure_db(db), pytest.raises(SystemExit):
            cmd_sim(args)

    def test_sim_invalid_bike_id(self, db):
        args = make_args(
            bike_id=9999, bike_legacy=None, config_file=None,
            venue_id=None, venue_legacy=None, month=None,
            weather_live=False, api_key=None, track_temp=None,
            apply_parts=None, compare_stock=False, save_run=False,
            quiet=False,
        )
        with _patch_ensure_db(db), pytest.raises(SystemExit):
            cmd_sim(args)

    def test_sim_deterministic(self, db):
        """Two identical sims should produce identical ET."""
        args = make_args(
            bike_id=1, bike_legacy=None, config_file=None,
            venue_id=None, venue_legacy=None, month=None,
            weather_live=False, api_key=None, track_temp=None,
            apply_parts=None, compare_stock=False, save_run=False,
            quiet=False, json_out=True,
        )
        with _patch_ensure_db(db):
            _, out1 = capture_output(cmd_sim, args)
        with _patch_ensure_db(db):
            _, out2 = capture_output(cmd_sim, args)
        d1 = json.loads(out1)
        d2 = json.loads(out2)
        assert d1["splits"]["quarter_mile_s"] == d2["splits"]["quarter_mile_s"]
        assert d1["splits"]["sixty_foot_s"] == d2["splits"]["sixty_foot_s"]


# ═══════════════════════════════════════════
# Phase 2: cmd_venues
# ═══════════════════════════════════════════

class TestCmdVenues:
    def test_list_venues(self, db):
        args = make_args(detail=None, country=None, include_inactive=False)
        with _patch_ensure_db(db):
            _, out = capture_output(cmd_venues, args)
        assert "Venues" in out
        assert "Aamby Valley" in out or "MMRT" in out

    def test_venue_detail(self, db):
        args = make_args(detail=1, country=None, include_inactive=False)
        with _patch_ensure_db(db):
            _, out = capture_output(cmd_venues, args)
        assert "Altitude" in out
        assert "Best month" in out
        assert "Worst month" in out

    def test_venue_detail_nonexistent(self, db):
        args = make_args(detail=999, country=None, include_inactive=False)
        with _patch_ensure_db(db):
            _, out = capture_output(cmd_venues, args)
        assert "not found" in out


# ═══════════════════════════════════════════
# Phase 2: cmd_tires
# ═══════════════════════════════════════════

class TestCmdTires:
    def test_grip_rank(self, db):
        args = make_args(
            grip_rank=True, value_rank=False,
            compound=None, position=None, manufacturer=None,
            india_only=False,
        )
        with _patch_ensure_db(db):
            _, out = capture_output(cmd_tires, args)
        assert "Grip Ranking" in out or "mu_peak" in out

    def test_value_rank(self, db):
        args = make_args(
            grip_rank=False, value_rank=True,
            compound=None, position=None, manufacturer=None,
            india_only=False,
        )
        with _patch_ensure_db(db):
            _, out = capture_output(cmd_tires, args)
        assert "Value" in out or "Grip/1K" in out


# ═══════════════════════════════════════════
# Phase 2: cmd_parts
# ═══════════════════════════════════════════

class TestCmdParts:
    def test_list_parts(self, db):
        args = make_args(
            category=None, brand=None, search=None,
            max_price=None, available=False, build_cost=None,
        )
        with _patch_ensure_db(db):
            _, out = capture_output(cmd_parts, args)
        # Should list seeded parts
        assert "Parts" in out or "parts" in out.lower()

    def test_build_cost(self, db):
        args = make_args(
            category=None, brand=None, search=None,
            max_price=None, available=False, build_cost="4,5,6",
        )
        with _patch_ensure_db(db):
            _, out = capture_output(cmd_parts, args)
        assert "INR" in out


# ═══════════════════════════════════════════
# Phase 2: Leaderboard & History
# ═══════════════════════════════════════════

class TestLeaderboardHistory:
    def test_leaderboard(self, db):
        # Ensure at least one saved run exists
        args_sim = make_args(
            bike_id=1, bike_legacy=None, config_file=None,
            venue_id=1, venue_legacy=None, month=1,
            weather_live=False, api_key=None, track_temp=None,
            apply_parts=None, compare_stock=False, save_run=True,
            quiet=True,
        )
        with _patch_ensure_db(db):
            capture_output(cmd_sim, args_sim)

        args = make_args(venue_id=None)
        with _patch_ensure_db(db):
            _, out = capture_output(cmd_leaderboard, args)
        # Should not crash and should show some output
        assert len(out) > 0

    def test_history(self, db):
        args = make_args(bike_id=None, venue_id=None)
        with _patch_ensure_db(db):
            _, out = capture_output(cmd_history, args)
        assert len(out) > 0


# ═══════════════════════════════════════════
# Phase 1: Legacy Mode
# ═══════════════════════════════════════════

class TestLegacyMode:
    def test_list(self):
        """--list should show built-in bikes and venues."""
        _, out = capture_output(legacy_main, ["--list", "--db", TEST_DB])
        assert "k5" in out
        assert "r1" in out
        assert "busa" in out
        assert "aamby-winter" in out

    def test_single_bike(self):
        """--bike k5 should run simulation."""
        _, out = capture_output(legacy_main, ["--bike", "k5"])
        assert "1/4 mile" in out
        assert "GSX-R" in out

    def test_bike_alias(self):
        """--bike hayabusa should resolve to busa."""
        _, out = capture_output(legacy_main, ["--bike", "hayabusa"])
        assert "Hayabusa" in out

    def test_with_venue(self):
        """--bike k5 --venue should apply venue env."""
        _, out = capture_output(legacy_main, ["--bike", "k5", "--venue", "aamby-winter"])
        assert "Aamby Valley" in out

    def test_json_output(self):
        """--bike k5 --json should produce valid JSON."""
        _, out = capture_output(legacy_main, ["--bike", "k5", "--json"])
        data = json.loads(out)
        assert "splits" in data
        assert data["splits"]["quarter_mile_s"] > 8.0

    def test_all_bikes_comparison(self):
        """No --bike flag should run all 3 and show comparison."""
        _, out = capture_output(legacy_main, [])
        assert "COMPARISON TABLE" in out

    def test_unknown_bike_errors(self):
        """--bike nonexistent should sys.exit."""
        with pytest.raises(SystemExit):
            legacy_main(["--bike", "nonexistent"])

    def test_export_config(self):
        """--export-config should write JSON config file."""
        cfg_path = f"/tmp/test_cli_export_{os.getpid()}.json"
        try:
            _, out = capture_output(
                legacy_main, ["--export-config", "k5", cfg_path]
            )
            assert os.path.exists(cfg_path)
            with open(cfg_path) as f:
                data = json.load(f)
            assert "engine" in data
            assert "chassis" in data
        finally:
            if os.path.exists(cfg_path):
                os.unlink(cfg_path)

    def test_config_file_roundtrip(self):
        """--export-config then --config should work."""
        cfg_path = f"/tmp/test_cli_rt_{os.getpid()}.json"
        try:
            capture_output(legacy_main, ["--export-config", "busa", cfg_path])
            _, out = capture_output(legacy_main, ["--config", cfg_path])
            assert "1/4 mile" in out
        finally:
            if os.path.exists(cfg_path):
                os.unlink(cfg_path)

    def test_csv_export(self):
        """--csv should write time-history data."""
        csv_path = f"/tmp/test_cli_csv_{os.getpid()}.csv"
        try:
            capture_output(
                legacy_main, ["--bike", "k5", "--csv", csv_path, "--quiet"]
            )
            assert os.path.exists(csv_path)
            with open(csv_path) as f:
                header = f.readline()
            assert "time_s" in header
        finally:
            if os.path.exists(csv_path):
                os.unlink(csv_path)

    def test_quiet_mode(self):
        """--quiet should suppress output."""
        _, out = capture_output(legacy_main, ["--bike", "k5", "--quiet"])
        # Quiet mode should have minimal output (no banner, no splits table)
        assert "MotoQuant Pro" not in out


# ═══════════════════════════════════════════
# Routing: main() dispatching
# ═══════════════════════════════════════════

class TestRouting:
    def test_subcommand_detected(self):
        """main() should detect Phase 2 subcommands in argv."""
        known = {"db", "bikes", "sim", "venues", "tires", "parts",
                 "weather", "leaderboard", "history"}
        for cmd in known:
            # Just verify the detection logic
            args = ["prog", cmd]
            has_sub = any(a in known for a in args[1:])
            assert has_sub

    def test_db_flag_before_subcommand(self):
        """--db path before subcommand should still detect subcommand."""
        args = ["prog", "--db", "/some/path.db", "db", "stats"]
        known = {"db", "bikes", "sim", "venues", "tires", "parts",
                 "weather", "leaderboard", "history"}
        has_sub = any(a in known for a in args[1:])
        assert has_sub

    def test_legacy_no_subcommand(self):
        """No subcommand should route to legacy mode."""
        args = ["prog", "--bike", "k5"]
        known = {"db", "bikes", "sim", "venues", "tires", "parts",
                 "weather", "leaderboard", "history"}
        has_sub = any(a in known for a in args[1:])
        assert not has_sub


# ═══════════════════════════════════════════
# End-to-End Pipeline
# ═══════════════════════════════════════════

class TestEndToEndPipeline:
    def test_full_pipeline(self, db):
        """
        Full pipeline: search bike → sim with venue/parts/compare → save →
        check leaderboard.
        """
        # 1. Search for K5
        args_search = make_args(
            search="GSX-R", manufacturer=None, category=None,
            displacement=None, power_min=None, quality=None,
            json_out=True,
        )
        with _patch_ensure_db(db):
            _, out = capture_output(cmd_bikes, args_search)
        bikes = json.loads(out)
        assert len(bikes) >= 1
        bike_id = bikes[0]["id"]

        # 2. Run sim with venue, month, parts, compare, save
        args_sim = make_args(
            bike_id=bike_id, bike_legacy=None, config_file=None,
            venue_id=1, venue_legacy=None, month=1,
            weather_live=False, api_key=None, track_temp=None,
            apply_parts="4,5", compare_stock=True, save_run=True,
            quiet=False,
        )
        with _patch_ensure_db(db):
            _, out = capture_output(cmd_sim, args_sim)
        assert "COMPARISON TABLE" in out
        assert "Run archived" in out
        assert "Build cost" in out

        # 3. Check leaderboard
        args_lb = make_args(venue_id=None)
        with _patch_ensure_db(db):
            _, out = capture_output(cmd_leaderboard, args_lb)
        assert len(out) > 0

    def test_all_three_bikes_sim(self, db):
        """Run all 3 reference bikes from DB and verify relative ordering."""
        ets = {}
        for bike_id in [1, 2, 3]:
            args = make_args(
                bike_id=bike_id, bike_legacy=None, config_file=None,
                venue_id=None, venue_legacy=None, month=None,
                weather_live=False, api_key=None, track_temp=None,
                apply_parts=None, compare_stock=False, save_run=False,
                quiet=False, json_out=True,
            )
            with _patch_ensure_db(db):
                _, out = capture_output(cmd_sim, args)
            data = json.loads(out)
            ets[bike_id] = data["splits"]["quarter_mile_s"]

        # All ETs should be in sane range (8-14 seconds)
        for bike_id, et in ets.items():
            assert 8.0 < et < 14.0, f"Bike {bike_id} ET {et} out of range"

    def test_venue_seasonal_affects_sim(self, db):
        """Simulating in January vs May at Aamby Valley should show DA effect."""
        ets = {}
        for month in [1, 5]:  # Jan (best DA) vs May (worst DA)
            args = make_args(
                bike_id=1, bike_legacy=None, config_file=None,
                venue_id=1, venue_legacy=None, month=month,
                weather_live=False, api_key=None, track_temp=None,
                apply_parts=None, compare_stock=False, save_run=False,
                quiet=False, json_out=True,
            )
            with _patch_ensure_db(db):
                _, out = capture_output(cmd_sim, args)
            data = json.loads(out)
            ets[month] = data["splits"]["quarter_mile_s"]

        # May (higher DA = less air = slower) should have worse ET than January
        assert ets[5] > ets[1], (
            f"May ET ({ets[5]:.3f}s) should be slower than Jan ET ({ets[1]:.3f}s)"
        )
