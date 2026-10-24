"""
tests/test_fixwave_data_parts.py
================================
October 2026 core-audit fix wave — parts data + the part-application bridge.

Every test drives the production path: parts are read from the shipped
``motoquant.db`` (a temp copy), applied with ``bridge.apply_part_to_config``
(the function the API quick-sim, optimizer, outlaw pipeline and CLI
``parts --impact`` all call) and simulated on the selected engine.

Pinned findings (reports/audit_core_2026_10_23_partial.md):
  * 10 of 20 forced-induction parts delivered zero forced-induction power
    (n2o_stages missing; turbo kits with no target_boost_bar whose hp deltas
    the bridge discarded) — and NA parts applied after a boost part were dead.
  * Expansion-chamber tuned_rpm overrides only moved the 2T launch-floor clamp,
    making pipe 'upgrades' up to 0.7 s slower.
  * Turbo/SC/nitrous kits were compatible with the factory-supercharged H2s.
  * Rapid Bike EVO switched the two-step on with no launch_rpm (8000 default).
  * The Trask turbo 1950 cc cap never reached the shipped DB.
  * parts_repo.search failed open for an unknown bike id.
"""

from __future__ import annotations

import importlib.util
import json
import logging
import os
import shutil
import sqlite3
import tempfile
import warnings
from pathlib import Path

import numpy as np
import pytest

from motoquant.database.bridge import apply_part_to_config, db_row_to_config
from motoquant.database.parts_repo import enrich_bike_row_for_fitment
from motoquant.engine_select import run_quarter
from motoquant.models import EnvironmentParams
from motoquant.parts.compatibility import is_compatible, is_factory_boosted
from tests._helpers import live_db_copy

_REPO = Path(__file__).resolve().parent.parent
# These tests assert properties of the SHIPPED catalog, so copy the repo's
# motoquant.db explicitly: live_db_copy() alone prefers $MOTOQUANT_DB, which
# other test modules redirect to a bare temp DB at import time.
_SHIPPED_DB = _REPO / "motoquant.db"
_PATCH = _REPO / "scripts" / "patch_2026_10_24_parts_data.py"

# rho == rho_SL_STD, so the boosted density-altitude floor max(0.97, rho/rho0)
# grants nothing: any ET gain here is real boost / nitrous / power.
_SEA_LEVEL_STD = {
    "venue_name": "Sea level ISA",
    "altitude_m": 0.0,
    "ambient_temp_c": 15.0,
    "barometric_pressure_hpa": 1013.25,
    "relative_humidity_pct": 0.0,
}


@pytest.fixture(scope="module")
def db():
    d = live_db_copy(_SHIPPED_DB)
    if d is None:
        pytest.skip("motoquant.db not available")
    yield d
    path = str(d.path)
    d.close()
    os.unlink(path)


def _load_patch():
    spec = importlib.util.spec_from_file_location("patch_parts_data", _PATCH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _cfg(db, bike_id, env=None):
    row = db.conn.execute(
        "SELECT * FROM bike_configs WHERE bike_model_id = ? AND is_current = 1",
        (bike_id,),
    ).fetchone()
    assert row is not None, f"no current config for bike {bike_id}"
    return db_row_to_config(dict(row), environment=env)


def _bike_rows(db):
    rows = []
    for r in db.conn.execute(
        "SELECT bm.*, m.name AS manufacturer FROM bike_models bm "
        "JOIN manufacturers m ON m.id = bm.manufacturer_id ORDER BY bm.id"
    ):
        rows.append(enrich_bike_row_for_fitment(db.conn, dict(r)))
    return rows


def _parts_where(db, where, params=()):
    return [
        dict(r)
        for r in db.conn.execute(
            "SELECT p.*, pc.name AS category_name FROM parts p "
            "JOIN parts_categories pc ON pc.id = p.category_id "
            f"WHERE {where} ORDER BY p.id",
            params,
        )
    ]


def _apply(cfg, part):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return apply_part_to_config(cfg, part)


def _et(cfg):
    return run_quarter(cfg).time_quarter


# ─────────────────────────────────────────────────────────────────────────────
# Forced-induction liveness
# ─────────────────────────────────────────────────────────────────────────────


class TestForcedInductionPartsAreLive:
    def test_every_boost_and_nitrous_part_makes_its_bike_faster_at_sea_level(self, db):
        """At ISA sea level the boosted DA floor is worth 0 s, so a kit that
        only flips boost_type (0 bar / 0 stages) is +mass = SLOWER on every
        bike it fits. Old DB: 7 turbo kits +0.017..+0.031 s, 3 nitrous kits
        exactly 0.000 s.

        'Faster on at least one compatible bike' rather than 'on every bike':
        a separate PHYSICS defect (the slip-phase redline clip freezes the
        sim when boost spins the engine past redline — audit finding 'In
        clutch slip the engine clips to redline*1.02') makes a few boosted
        (part, bike) pairs absurdly slow, e.g. C-1 / HKS / Garrett-V4 on some
        litre bikes. That is not a data defect and is owned by physics.py.
        """
        logging.disable(logging.CRITICAL)
        try:
            env = EnvironmentParams(**_SEA_LEVEL_STD)
            bikes = _bike_rows(db)
            parts = _parts_where(db, "pc.name IN ('boost_kit', 'nitrous')")
            assert len(parts) >= 20
            failures = []
            for part in parts:
                fits = [b for b in bikes if is_compatible(part, b)[0]][:6]
                if not fits:
                    continue  # unreachable parts are another test's job
                deltas = []
                for bike in fits:
                    base = _cfg(db, bike["id"], env)
                    deltas.append(_et(_apply(base, part)) - _et(base))
                if not min(deltas) < -0.05:
                    failures.append((part["id"], part["model_name"], deltas))
            assert failures == [], f"dead forced-induction parts: {failures}"
        finally:
            logging.disable(logging.NOTSET)

    def test_patched_rows_carry_real_boost(self, db):
        rows = {(r["brand"], r["part_number"]): r for r in _parts_where(db, "1=1")}
        patch = _load_patch()
        for key, target in patch.FI_PARTS.items():
            ov = json.loads(rows[key]["param_overrides"])
            dl = json.loads(rows[key]["param_deltas"] or "{}")
            assert ov == target["param_overrides"], key
            assert "engine.peak_power_hp" not in dl, key
            if ov["forced_induction.boost_type"] == "n2o":
                assert ov["forced_induction.n2o_stages"] >= 1
            else:
                assert ov["forced_induction.target_boost_bar"] > 0

    def test_boost_bar_matches_each_kits_declared_psi(self, db):
        patch = _load_patch()
        rows = {(r["brand"], r["part_number"]): r for r in _parts_where(db, "1=1")}
        for key, target in patch.FI_PARTS.items():
            bar = target["param_overrides"].get("forced_induction.target_boost_bar")
            if bar is None:
                continue
            psi = json.loads(rows[key]["specifications"])["boost_psi"]
            assert bar == pytest.approx(psi * 0.0689476, abs=6e-4), key

    def test_patch_values_equal_the_fresh_seed(self):
        """Seed-source fold rule: the patch is never the only carrier."""
        from motoquant.database.connection import MotoQuantDB
        from motoquant.database.seed import seed_all

        logging.disable(logging.CRITICAL)
        try:
            fresh = MotoQuantDB(":memory:")
            fresh.initialize()
            seed_all(fresh)
            seeded = {
                (r["brand"], r["part_number"]): r
                for r in fresh.conn.execute("SELECT * FROM parts")
            }
            patch = _load_patch()
            for key, target in patch.FI_PARTS.items():
                row = seeded[key]
                assert json.loads(row["param_overrides"]) == target["param_overrides"]
                assert json.loads(row["param_deltas"] or "null") == target.get(
                    "param_deltas"
                )
            trask = json.loads(seeded[patch.TRASK_KEY]["fitment_rules"])
            assert trask["match"]["displacement_max_cc"] == patch.TRASK_MAX_CC
            assert trask["description"] == patch.TRASK_DESCRIPTION
            fresh.close()
        finally:
            logging.disable(logging.NOTSET)

    def test_patch_is_idempotent_and_fixes_an_unpatched_copy(self, db):
        patch = _load_patch()
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        try:
            shutil.copy(db.path, tmp.name)
            c = sqlite3.connect(tmp.name)
            # Re-create the pre-patch state of two rows.
            c.execute(
                "UPDATE parts SET param_overrides = ? WHERE part_number = ?",
                (
                    json.dumps(
                        {
                            "forced_induction.boost_type": "n2o",
                            "forced_induction.n2o_hp_per_stage": 35.0,
                        }
                    ),
                    "ZEX-35-UNI",
                ),
            )
            c.execute(
                "UPDATE parts SET param_overrides = ?, param_deltas = ? "
                "WHERE part_number = ?",
                (
                    json.dumps({"forced_induction.boost_type": "turbo"}),
                    json.dumps(
                        {
                            "engine.peak_power_hp": 180,
                            "engine.peak_torque_nm": 150,
                            "chassis.dry_mass_kg": 15.0,
                        }
                    ),
                    "ORP-TT-GSXR-DRAG",
                ),
            )
            c.commit()
            c.close()
            first = patch.apply(tmp.name)
            second = patch.apply(tmp.name)
            assert first["fi_parts_updated"] == 2
            assert second == {
                "fi_parts_updated": 0,
                "trask_rule_updated": 0,
                "missing": [],
            }
        finally:
            os.unlink(tmp.name)


# ─────────────────────────────────────────────────────────────────────────────
# Bridge: per-part curve scaling
# ─────────────────────────────────────────────────────────────────────────────


class TestBridgePerPartScaling:
    def _exhaust_and_turbo(self, db):
        exhaust = _parts_where(
            db, "p.brand = 'Akrapovic' AND p.part_number = ?", ("AK-HAYA-FS-TI",)
        )[0]
        turbo = _parts_where(db, "p.part_number = 'VT-STAGE1-GSXR'")[0]
        return exhaust, turbo

    def test_build_et_does_not_depend_on_part_order(self, db):
        """Old bridge: an exhaust applied AFTER a turbo was a dead knob
        (exhaust->turbo 10.2137 vs turbo->exhaust 10.3266 on DB Hayabusa)."""
        exhaust, turbo = self._exhaust_and_turbo(db)
        base = _cfg(db, 3)
        a = _apply(_apply(base, exhaust), turbo)
        b = _apply(_apply(base, turbo), exhaust)
        np.testing.assert_allclose(
            a.engine.dyno_curve.torque_nm, b.engine.dyno_curve.torque_nm, rtol=1e-12
        )
        assert _et(a) == pytest.approx(_et(b), abs=1e-9)
        assert _et(b) < _et(_apply(base, turbo)) - 0.01  # exhaust is live

    def test_forced_induction_hp_delta_is_ignored_with_a_warning(self, db):
        base = _cfg(db, 3)
        part = {
            "model_name": "legacy turbo",
            "param_overrides": {
                "forced_induction.boost_type": "turbo",
                "forced_induction.target_boost_bar": 0.5,
            },
            "param_deltas": {"engine.peak_power_hp": 100},
        }
        with pytest.warns(UserWarning, match="peak_power_hp"):
            out = apply_part_to_config(base, part)
        assert out.engine.peak_power_hp == base.engine.peak_power_hp
        np.testing.assert_array_equal(
            out.engine.dyno_curve.torque_nm, base.engine.dyno_curve.torque_nm
        )

    @pytest.mark.parametrize(
        "overrides, match",
        [
            ({"forced_induction.boost_type": "turbo"}, "no boost"),
            (
                {
                    "forced_induction.boost_type": "n2o",
                    "forced_induction.n2o_hp_per_stage": 35.0,
                },
                "0 hp",
            ),
        ],
    )
    def test_dead_forced_induction_part_warns(self, db, overrides, match):
        base = _cfg(db, 3)
        with pytest.warns(UserWarning, match=match):
            apply_part_to_config(
                base, {"model_name": "dead", "param_overrides": overrides}
            )


# ─────────────────────────────────────────────────────────────────────────────
# 2-stroke expansion chambers
# ─────────────────────────────────────────────────────────────────────────────


class TestExpansionChambers:
    def _pipe_pairs(self, db):
        bikes = _bike_rows(db)
        pipes = _parts_where(db, "p.param_overrides LIKE '%engine.tuned_rpm%'")
        assert len(pipes) >= 14
        return [(p, b) for p in pipes for b in bikes if is_compatible(p, b)[0]]

    def test_every_pipe_makes_every_compatible_2t_faster(self, db):
        """Old bridge: NSR250R + Arrow +0.702 s, TZR250 + Tyga +0.705 s,
        RD400 + JL +0.141 s — the override only moved the launch floor."""
        logging.disable(logging.CRITICAL)
        try:
            slower = []
            pairs = self._pipe_pairs(db)
            assert len(pairs) >= 20
            for pipe, bike in pairs:
                base = _cfg(db, bike["id"])
                d_et = _et(_apply(base, pipe)) - _et(base)
                if not d_et < -0.05:
                    slower.append((pipe["id"], bike["id"], round(d_et, 3)))
            assert slower == []
        finally:
            logging.disable(logging.NOTSET)

    def test_reshape_delivers_the_parts_power_and_a_sane_resonance(self, db):
        for pipe, bike in self._pipe_pairs(db):
            base = _cfg(db, bike["id"])
            out = _apply(base, pipe)
            dc0, dc1 = base.engine.dyno_curve, out.engine.dyno_curve
            p0 = float(np.max(dc0.torque_nm * dc0.rpm))
            p1 = float(np.max(dc1.torque_nm * dc1.rpm))
            ratio = out.engine.peak_power_hp / base.engine.peak_power_hp
            assert p1 / p0 == pytest.approx(ratio, rel=1e-6), (pipe["id"], bike["id"])
            # tuned_rpm now points at the reshaped curve's torque peak and can
            # never pin the launch floor above redline (Yezdi pipe asked 7500
            # on a 6490 rpm engine).
            assert out.engine.tuned_rpm <= out.engine.redline_rpm
            assert out.engine.tuned_rpm == pytest.approx(
                float(dc1.rpm[np.argmax(dc1.torque_nm)])
            )


# ─────────────────────────────────────────────────────────────────────────────
# Two-step without a hold rpm (Rapid Bike EVO)
# ─────────────────────────────────────────────────────────────────────────────


class TestTwoStepHoldRpm:
    def test_rapid_bike_evo_does_not_launch_a_twin_at_its_redline(self, db):
        evo = _parts_where(db, "p.part_number = 'RB-EVO-UNIV'")[0]
        bike_id = db.conn.execute(
            "SELECT id FROM bike_models WHERE model_name LIKE 'Thruxton 1200 R%'"
        ).fetchone()[0]
        base = _cfg(db, bike_id)
        out = _apply(base, evo)
        assert out.staging.two_step is True
        assert out.staging.launch_rpm == pytest.approx(base.engine.peak_torque_rpm)
        # Old: launch_rpm stayed the 8000 dataclass default (> 7425 redline)
        # and the "upgrade" ran +1.798 s.
        assert _et(out) - _et(base) < 0.01

    def test_part_with_its_own_launch_rpm_keeps_it(self, db):
        flash = _parts_where(
            db,
            "p.param_overrides LIKE '%staging.launch_rpm%' "
            "AND p.param_overrides LIKE '%two_step%'",
        )[0]
        out = _apply(_cfg(db, 1), flash)
        assert (
            out.staging.launch_rpm
            == json.loads(flash["param_overrides"])["staging.launch_rpm"]
        )


# ─────────────────────────────────────────────────────────────────────────────
# Compatibility: factory forced induction, Trask cap, fail-closed search
# ─────────────────────────────────────────────────────────────────────────────


class TestFitment:
    def test_no_forced_induction_kit_fits_a_factory_supercharged_h2(self, db):
        h2 = [b["id"] for b in _bike_rows(db) if is_factory_boosted(b)]
        assert set(h2) >= {45, 328}
        for bike_id in h2:
            fits = db.parts.list_compatible_for_bike(bike_id)
            fi = [
                p["model_name"]
                for p in fits
                if p["category_name"] in ("boost_kit", "nitrous")
            ]
            assert fi == [], (bike_id, fi)
            assert fits, f"bike {bike_id} lost every part"

    def test_na_h2_mach_iv_and_hayabusa_are_not_factory_boosted(self, db):
        rows = {b["id"]: b for b in _bike_rows(db)}
        mach_iv = next(b for b in rows.values() if "Mach IV" in b["model_name"])
        assert not is_factory_boosted(mach_iv)
        assert not is_factory_boosted(rows[3])
        cats = {p["category_name"] for p in db.parts.list_compatible_for_bike(3)}
        assert "boost_kit" in cats

    def test_trask_turbo_reaches_m8_and_thunderstroke_big_twins(self, db):
        trask = _parts_where(db, "p.part_number = 'TRASK-VT-TURBO'")[0]
        big = [
            b
            for b in _bike_rows(db)
            if b["manufacturer"] in ("Harley-Davidson", "Indian")
            and b["cylinder_config"] == "V2"
            and 1750 < (b["displacement_cc"] or 0) <= 1950
        ]
        assert len(big) >= 12
        assert all(is_compatible(trask, b)[0] for b in big)

    def test_search_for_unknown_bike_returns_nothing(self, db):
        """Old: the whole catalog (593 parts) came back as 'compatible'."""
        assert db.parts.search(bike_model_id=999_999, limit=1000) == []
        assert len(db.parts.search(bike_model_id=3, limit=1000)) > 0
