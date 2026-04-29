"""Regression: stale-DB-config divergence + power_boost liveness (Apr 24, 2026).

The bug originally filed as "power_boost dead knob on R15 V3 at 22.034 s"
was two bugs stacked:

1. REAL: bike_configs JSON held pre-kaizen defaults (engine_inertia
   0.040 vs 0.00572, parasitic 6.5x too high, aero.cd=0.56 vs 0.308,
   superbike gear cassette instead of R15 service-manual ratios).
   Caused 4.7 s slower ET via /api/simulate?bike_id=N path.
2. IMAGINED: "dead knob" - power scaling IS live on both paths.

Fix: scripts/reseed_configs_from_specs.py regenerates every
is_current=1 bike_configs JSON from current spec_to_bike_config output.
"""
from __future__ import annotations

import copy
import shutil
import tempfile
import unittest
from pathlib import Path

import motoquant
from motoquant.database import MotoQuantDB
from motoquant.database.bridge import db_row_to_config
from motoquant.models import DynoCurve
from motoquant.scraper.importer import spec_to_bike_config
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

_DB = Path(__file__).parent.parent / "motoquant.db"


def _open_db():
    """Open DB via writable-fs copy (dodges FUSE-mount sqlite I/O errors)."""
    if not _DB.exists():
        return None
    tmp = Path(tempfile.gettempdir()) / "motoquant_test_ro.db"
    shutil.copy(str(_DB), str(tmp))
    db = MotoQuantDB(db_path=str(tmp))
    db.connect()
    return db


def _load_db_r15_v3():
    db = _open_db()
    if db is None:
        return None
    try:
        r = db.conn.execute(
            "SELECT bm.id FROM bike_models bm WHERE bm.model_name LIKE '%R15 V3%' LIMIT 1"
        ).fetchone()
        if not r:
            return None
        mid = dict(r)["id"]
        row = dict(db.conn.execute(
            "SELECT * FROM bike_configs WHERE bike_model_id=? AND is_current=1 "
            "ORDER BY version DESC LIMIT 1", (mid,),
        ).fetchone())
        return db_row_to_config(row, name="R15 V3 DB")
    finally:
        db.close()


def _load_spec_r15_v3():
    spec = next((s for s in ALL_KNOWN_BIKES
                 if "R15" in s.model_name and "V3" in s.model_name), None)
    return spec_to_bike_config(spec) if spec else None


class TestDbMatchesSpec(unittest.TestCase):
    def setUp(self):
        self.db = _load_db_r15_v3()
        self.sp = _load_spec_r15_v3()
        if self.db is None or self.sp is None:
            self.skipTest("DB or R15 V3 spec unavailable")

    def test_engine_inertia(self):
        self.assertAlmostEqual(
            self.db.engine.engine_inertia_kgm2,
            self.sp.engine.engine_inertia_kgm2, delta=1e-4)

    def test_parasitic(self):
        for f in ("oil_pump_power_w", "valve_train_power_w", "alternator_power_w"):
            self.assertAlmostEqual(getattr(self.db.parasitic, f),
                                   getattr(self.sp.parasitic, f), delta=1.0)

    def test_aero_cd(self):
        self.assertAlmostEqual(self.db.aero.cd, self.sp.aero.cd, delta=0.01)

    def test_gear_ratios(self):
        self.assertEqual(list(self.db.drivetrain.gear_ratios),
                         list(self.sp.drivetrain.gear_ratios))
        self.assertEqual(self.db.drivetrain.front_sprocket,
                         self.sp.drivetrain.front_sprocket)
        self.assertEqual(self.db.drivetrain.rear_sprocket,
                         self.sp.drivetrain.rear_sprocket)

    def test_dyno_curve(self):
        dc = self.db.engine.dyno_curve
        self.assertIsNotNone(dc)
        self.assertIsInstance(dc, DynoCurve)

    def test_et_match(self):
        db_cfg = copy.deepcopy(self.db)
        db_cfg.environment = copy.deepcopy(self.sp.environment)
        et_db = motoquant.MotoQuantEngine(db_cfg).run(
            use_adaptive_dt=False, max_time=26.0).time_quarter
        et_sp = motoquant.MotoQuantEngine(self.sp).run(
            use_adaptive_dt=False, max_time=26.0).time_quarter
        self.assertLess(abs(et_db - et_sp), 0.5)


class TestPowerBoostIsLive(unittest.TestCase):
    def test_boost_drops_et(self):
        spec = next((s for s in ALL_KNOWN_BIKES
                     if "R15" in s.model_name and "V3" in s.model_name), None)
        self.assertIsNotNone(spec)
        cfg = spec_to_bike_config(spec)
        base = motoquant.MotoQuantEngine(copy.deepcopy(cfg)).run(
            use_adaptive_dt=False, max_time=26.0).time_quarter
        c2 = copy.deepcopy(cfg)
        s = 1.5
        c2.engine.peak_power_hp *= s
        c2.engine.peak_torque_nm *= s
        if c2.engine.dyno_curve is not None:
            c2.engine.dyno_curve.torque_nm = c2.engine.dyno_curve.torque_nm * s
        boosted = motoquant.MotoQuantEngine(c2).run(
            use_adaptive_dt=False, max_time=26.0).time_quarter
        self.assertGreater(base - boosted, 1.0)


class TestReferenceBaselines(unittest.TestCase):
    """
    Pinned baselines — golden-file equivalent for the three reference bikes.

    Tolerance is **0.001s** (NOT 0.02s) because per CLAUDE.md every recent
    physics-touching commit has preserved K5/R1/Hayabusa to 4 decimals exactly.
    Any future drift past 1ms is structurally interesting and should fail CI
    immediately so we catch the regression at PR-time, not at the next manual
    sweep.

    If you intentionally re-baseline (e.g. after a deliberate physics rewrite),
    update the constants below in the SAME commit and document the rationale
    in CLAUDE.md's session entry. Never widen the delta to "make the test pass".
    """
    K5_BASELINE_S       = 10.0334
    R1_BASELINE_S       = 10.2859
    HAYABUSA_BASELINE_S = 10.4712
    BASELINE_TOLERANCE  = 0.001  # 1 ms — sim is exact to 4 decimals

    def test_k5(self):
        from motoquant.defaults import gsxr1000_k5
        et = motoquant.MotoQuantEngine(gsxr1000_k5()).run().time_quarter
        self.assertAlmostEqual(et, self.K5_BASELINE_S, delta=self.BASELINE_TOLERANCE,
                               msg=f"K5 drifted: sim={et:.4f}s vs pinned {self.K5_BASELINE_S}s")

    def test_r1(self):
        from motoquant.defaults import yzfr1_4c8
        et = motoquant.MotoQuantEngine(yzfr1_4c8()).run().time_quarter
        self.assertAlmostEqual(et, self.R1_BASELINE_S, delta=self.BASELINE_TOLERANCE,
                               msg=f"R1 drifted: sim={et:.4f}s vs pinned {self.R1_BASELINE_S}s")

    def test_hayabusa(self):
        from motoquant.defaults import hayabusa_gen1
        et = motoquant.MotoQuantEngine(hayabusa_gen1()).run().time_quarter
        self.assertAlmostEqual(et, self.HAYABUSA_BASELINE_S, delta=self.BASELINE_TOLERANCE,
                               msg=f"Hayabusa drifted: sim={et:.4f}s vs pinned {self.HAYABUSA_BASELINE_S}s")


if __name__ == "__main__":
    unittest.main()
