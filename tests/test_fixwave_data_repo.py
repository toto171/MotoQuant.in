"""
tests/test_fixwave_data_repo.py
===============================
October 2026 core-audit fix wave — BikeRepository / derived-copy integrity.

Pinned findings (reports/audit_core_2026_10_23_partial.md):
  * ``BikeRepository.to_config`` overrode every config's engine_params curve
    with a stale ``dyno_curves`` row, so CLI / chat / NL sims disagreed with
    /api/simulate for 508 of 541 bikes (MT-15-class -1.99 s, YZF-R15 V3
    -2.28 s). Fixed at the source; the table is also re-synced by
    scripts/patch_2026_10_24_config_sync.py.
  * The reseed refreshed only displacement/hp/torque/mass headline columns,
    so 9 bikes listed rpm/bore/stroke/wheelbase the physics does not use.
  * ``create_config``'s idempotency guard compared raw JSON bytes (dead keys
    / last-ULP noise minted phantom versions on every ``db seed``) and ignored
    ``category_tag`` (a re-derived taxonomy never persisted via import).
"""

from __future__ import annotations

import copy
import importlib.util
import json
import logging
import os
import shutil
import tempfile
from pathlib import Path

import numpy as np
import pytest

from motoquant.database.bridge import db_row_to_config, extract_headline_specs
from motoquant.database.connection import MotoQuantDB
from motoquant.defaults import hayabusa_gen1
from motoquant.engine_select import run_quarter
from tests._helpers import live_db_copy

_REPO = Path(__file__).resolve().parent.parent
# These tests assert properties of the SHIPPED catalog, so copy the repo's
# motoquant.db explicitly: live_db_copy() alone prefers $MOTOQUANT_DB, which
# other test modules redirect to a bare temp DB at import time.
_SHIPPED_DB = _REPO / "motoquant.db"
_SYNC_PATCH = _REPO / "scripts" / "patch_2026_10_24_config_sync.py"


@pytest.fixture(scope="module")
def db():
    d = live_db_copy(_SHIPPED_DB)
    if d is None:
        pytest.skip("motoquant.db not available")
    yield d
    path = str(d.path)
    d.close()
    os.unlink(path)


def _current_rows(db):
    return [
        dict(r)
        for r in db.conn.execute(
            "SELECT * FROM bike_configs WHERE is_current = 1 AND config_name = 'stock'"
        )
    ]


class TestToConfigMatchesApiPath:
    def test_every_current_config_loads_the_same_curve_as_the_api(self, db):
        mismatched = []
        for row in _current_rows(db):
            via_repo = db.bikes.to_config(row["id"]).engine.dyno_curve
            via_api = db_row_to_config(row).engine.dyno_curve
            if not (
                np.array_equal(via_repo.rpm, via_api.rpm)
                and np.array_equal(via_repo.torque_nm, via_api.torque_nm)
                and via_repo.is_at_wheel == via_api.is_at_wheel
            ):
                mismatched.append(row["bike_model_id"])
        assert mismatched == []

    @pytest.mark.parametrize("bike_id", [4093, 151, 348, 217, 3])
    def test_et_matches_api_path(self, db, bike_id):
        """The audit's worst cases: 4093 -1.987 s, 151 -2.276 s, 348 +0.764 s."""
        row = next(r for r in _current_rows(db) if r["bike_model_id"] == bike_id)
        et_repo = run_quarter(db.bikes.to_config(row["id"])).time_quarter
        et_api = run_quarter(db_row_to_config(row)).time_quarter
        assert et_repo == et_api

    def test_stale_table_row_cannot_override_the_blob(self, db):
        """Even with a deliberately wrong dyno_curves row the blob wins."""
        row = next(r for r in _current_rows(db) if r["bike_model_id"] == 3)
        db.conn.execute(
            "INSERT INTO dyno_curves (bike_config_id, curve_type, is_at_wheel,"
            " rpm_points, torque_values, num_points, source, confidence)"
            " VALUES (?, 'torque', 1, '[1000, 12000]', '[1, 1]', 2, 'x', 1.0)",
            (row["id"],),
        )
        try:
            cfg = db.bikes.to_config(row["id"])
            assert len(cfg.engine.dyno_curve.rpm) > 2
            assert len(db.bikes.get_dyno_curve(row["id"]).rpm) > 2
        finally:
            db.conn.execute(
                "DELETE FROM dyno_curves WHERE bike_config_id = ? AND source = 'x'",
                (row["id"],),
            )
            db.conn.commit()


class TestCliMatchesApi:
    def test_cli_sim_prints_the_api_et_even_with_a_stale_curve_row(self, tmp_path):
        """Production paths end to end: ``motoquant.run sim --bike-id`` (which
        builds its config through ``BikeRepository.to_config``) must print the
        stock ET that ``/api/simulate/quick`` returns for the same bike.

        The shipped DB had the CLI at 17.2186 s for bike 4093 (MT-15 V1) while
        the API — and the golden snapshot, the sweep and the website — gave
        19.2053 s, because to_config preferred a stale dyno_curves row. The
        row is re-staled here (the shipped shape: at-wheel flag set, a
        different curve), so this fails if to_config ever prefers the table
        again, even on a DB whose table was re-synced.
        """
        pytest.importorskip("fastapi")
        import sqlite3
        import subprocess
        import sys

        src = live_db_copy(_SHIPPED_DB)
        if src is None:
            pytest.skip("motoquant.db not available")
        path = tmp_path / "cli_vs_api.db"
        shutil.copy(src.path, path)
        src_path = str(src.path)
        src.close()
        os.unlink(src_path)

        conn = sqlite3.connect(str(path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cfg_id = conn.execute(
            "SELECT id FROM bike_configs WHERE bike_model_id = 4093"
            " AND is_current = 1 AND config_name = 'stock'"
        ).fetchone()[0]
        conn.execute(
            "UPDATE dyno_curves SET is_at_wheel = 1,"
            " torque_values = (SELECT json_group_array(value * 1.15)"
            "   FROM json_each(dyno_curves.torque_values))"
            " WHERE bike_config_id = ?",
            (cfg_id,),
        )
        conn.commit()

        out = subprocess.run(
            [sys.executable, "-m", "motoquant.run", "--db", str(path), "sim"]
            + ["--bike-id", "4093", "--json"],
            capture_output=True,
            text=True,
            cwd=_REPO,
            timeout=300,
        )
        cli_et = json.loads(out.stdout)["splits"]["quarter_mile_s"]

        from fastapi.testclient import TestClient

        import motoquant.api as api_mod

        orig = api_mod._get_db
        api_mod._get_db = lambda: conn
        try:
            r = TestClient(api_mod.app).post(
                "/api/simulate/quick", json={"bike_id": 4093}
            )
        finally:
            api_mod._get_db = orig
            conn.close()
        assert r.status_code == 200, r.text
        api_et = r.json()["et_quarter_s"]
        assert cli_et == pytest.approx(api_et, abs=1e-4)


class TestDerivedCopiesInSync:
    def test_dyno_curves_table_matches_blobs(self, db):
        stale = []
        for cfg in db.conn.execute("SELECT id, engine_params FROM bike_configs"):
            dc = json.loads(cfg["engine_params"]).get("dyno_curve")
            if dc is None:
                continue
            for r in db.conn.execute(
                "SELECT * FROM dyno_curves WHERE bike_config_id = ?", (cfg["id"],)
            ):
                if json.loads(r["torque_values"]) != dc["torque_nm"] or bool(
                    r["is_at_wheel"]
                ) != bool(dc.get("is_at_wheel")):
                    stale.append(cfg["id"])
        assert stale == []

    def test_headline_columns_match_physics_blobs(self, db):
        drift = []
        for row in _current_rows(db):
            model = db.bikes.get_model(row["bike_model_id"])
            for col, val in extract_headline_specs(db_row_to_config(row)).items():
                old = model[col]
                if isinstance(val, (int, float)) and isinstance(old, (int, float)):
                    if abs(float(old) - float(val)) > 1e-9:
                        drift.append((row["bike_model_id"], col, old, val))
                elif old != val:
                    drift.append((row["bike_model_id"], col, old, val))
        assert drift == []

    def test_sync_patch_repairs_and_is_idempotent(self, db):
        spec = importlib.util.spec_from_file_location("cfg_sync", _SYNC_PATCH)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            shutil.copy(db.path, tmp.name)
            other = MotoQuantDB(tmp.name)
            other.connect()
            # Re-create the shipped staleness on two rows.
            other.conn.execute(
                "UPDATE bike_models SET wheelbase_mm = 1355, peak_power_rpm = 8000"
                " WHERE id = 316"
            )
            other.conn.execute(
                "UPDATE dyno_curves SET is_at_wheel = 1, torque_values = '[1.0]'"
                " WHERE id = (SELECT MIN(id) FROM dyno_curves)"
            )
            other.conn.commit()
            other.close()
            first = mod.apply(tmp.name)
            second = mod.apply(tmp.name)
            assert first["dyno_curves_updated"] == 1
            assert first["headline_cells_updated"] == 2
            assert all(v == 0 for v in second.values())
        finally:
            for suffix in ("", "-wal", "-shm"):
                if os.path.exists(tmp.name + suffix):
                    os.unlink(tmp.name + suffix)


class TestCreateConfigGuard:
    @pytest.fixture
    def fresh(self):
        d = MotoQuantDB(":memory:")
        d.initialize()
        yield d
        d.close()

    def _versions(self, d, model_id):
        return d.conn.execute(
            "SELECT COUNT(*) FROM bike_configs WHERE bike_model_id = ?", (model_id,)
        ).fetchone()[0]

    def test_dead_keys_in_stored_blob_do_not_mint_a_version(self, fresh):
        cfg = hayabusa_gen1()
        model_id, config_id = fresh.bikes.upsert_from_config(
            cfg, manufacturer_name="Suzuki", model_code="Gen1"
        )
        aero = json.loads(
            fresh.conn.execute(
                "SELECT aero_params FROM bike_configs WHERE id = ?", (config_id,)
            ).fetchone()[0]
        )
        aero["headwind_ms"] = 0.0  # a since-removed AeroParams field
        fresh.conn.execute(
            "UPDATE bike_configs SET aero_params = ? WHERE id = ?",
            (json.dumps(aero), config_id),
        )
        assert fresh.bikes.create_config(model_id, cfg) == config_id
        assert self._versions(fresh, model_id) == 1

    def test_last_ulp_float_noise_does_not_mint_a_version(self, fresh):
        cfg = hayabusa_gen1()
        model_id, config_id = fresh.bikes.upsert_from_config(
            cfg, manufacturer_name="Suzuki", model_code="Gen1"
        )
        noisy = copy.deepcopy(cfg)
        t = noisy.engine.dyno_curve.torque_nm
        noisy.engine.dyno_curve.torque_nm = np.nextafter(t, t + 1.0)
        assert fresh.bikes.create_config(model_id, noisy) == config_id
        assert self._versions(fresh, model_id) == 1

    def test_real_change_still_mints_a_version(self, fresh):
        cfg = hayabusa_gen1()
        model_id, config_id = fresh.bikes.upsert_from_config(
            cfg, manufacturer_name="Suzuki", model_code="Gen1"
        )
        changed = copy.deepcopy(cfg)
        changed.chassis.dry_mass_kg += 1.0
        assert fresh.bikes.create_config(model_id, changed) != config_id
        assert self._versions(fresh, model_id) == 2

    def test_category_tag_change_persists_on_the_reused_row(self, fresh):
        cfg = hayabusa_gen1()
        model_id, config_id = fresh.bikes.upsert_from_config(
            cfg, manufacturer_name="Suzuki", model_code="Gen1"
        )
        retagged = copy.deepcopy(cfg)
        retagged.category_tag = "cruiser_1300p"
        assert fresh.bikes.create_config(model_id, retagged) == config_id
        tag = fresh.conn.execute(
            "SELECT category_tag FROM bike_configs WHERE id = ?", (config_id,)
        ).fetchone()[0]
        assert tag == "cruiser_1300p"
        assert self._versions(fresh, model_id) == 1
        # ... and it drives the physics through the production DB path.
        row = fresh.bikes.get_config(config_id)
        assert db_row_to_config(row).category_tag == "cruiser_1300p"

    def test_provenance_is_not_duplicated_by_a_reseed(self, fresh):
        logging.disable(logging.CRITICAL)
        try:
            from motoquant.database.seed import seed_reference_bikes

            seed_reference_bikes(fresh)
            n1 = fresh.conn.execute("SELECT COUNT(*) FROM data_provenance").fetchone()[
                0
            ]
            seed_reference_bikes(fresh)
            n2 = fresh.conn.execute("SELECT COUNT(*) FROM data_provenance").fetchone()[
                0
            ]
            assert n1 == n2 > 0
        finally:
            logging.disable(logging.NOTSET)
