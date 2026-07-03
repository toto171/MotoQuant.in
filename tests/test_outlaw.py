"""
Tests for the composed outlaw/open-class pipeline (motoquant/analysis/outlaw.py)
and the unlimited-budget semantics on the optimizer API.

Run with:  python -m pytest tests/test_outlaw.py -v
"""

from __future__ import annotations

import math
import os
import shutil
import tempfile
import unittest

_REPO_DB = os.path.join(os.path.dirname(__file__), "..", "motoquant.db")
_tmp = tempfile.NamedTemporaryFile(prefix="mq_outlaw_test_", suffix=".db", delete=False)
_tmp.close()
shutil.copyfile(_REPO_DB, _tmp.name)
# Env is asserted in setUpModule (run time), NOT at import/collection time —
# import-time writes poison sibling modules' _PRIOR captures and cascade
# deleted-tmp paths through the suite (July-3 lesson).
_OLD_ENV_DB = None

from motoquant.analysis.outlaw import (  # noqa: E402
    UNLIMITED_BUDGET_INR,
    _finite,
    _span,
    optimize_outlaw,
)
from motoquant.database.connection import MotoQuantDB  # noqa: E402
from motoquant.database.parts_repo import PartsRepository  # noqa: E402
from motoquant.database.tire_repo import TireRepository  # noqa: E402

_HAYABUSA_GEN2_ID = 11  # Suzuki Hayabusa (2008-2012) in the shipped catalog


def _no_finite_violations(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            _no_finite_violations(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _no_finite_violations(v, f"{path}[{i}]")
    elif isinstance(obj, float):
        assert math.isfinite(obj), f"non-finite float at {path}"


class TestHelpers(unittest.TestCase):
    def test_span_maps_progress(self):
        seen = []
        tick = _span(lambda f, s: seen.append((round(f, 3), s)), 0.2, 0.6)
        tick(0.0, "start")
        tick(0.5, "mid")
        tick(1.0, "end")
        self.assertEqual(seen, [(0.2, "start"), (0.4, "mid"), (0.6, "end")])

    def test_span_none_progress(self):
        self.assertIsNone(_span(None, 0, 1))

    def test_finite_sanitizes(self):
        out = _finite({"a": float("inf"), "b": [1.0, float("nan")], "c": "x"})
        self.assertIsNone(out["a"])
        self.assertIsNone(out["b"][1])
        self.assertEqual(out["b"][0], 1.0)
        self.assertEqual(out["c"], "x")


class TestOutlawPipeline(unittest.TestCase):
    """One real end-to-end run (capped candidates for speed), assertions on
    structure + physics sanity. This exercises tire fitment → knapsack →
    apply → autotune → combined verify on the production data."""

    @classmethod
    def setUpClass(cls):
        db = MotoQuantDB(_tmp.name)
        cfg_row = db.bikes.get_current_config(_HAYABUSA_GEN2_ID)
        cls.config = db.bikes.to_config(cfg_row["id"])
        cls.db = db
        cls.result = optimize_outlaw(
            cls.config,
            PartsRepository(db.conn),
            TireRepository(db.conn),
            bike_model_id=_HAYABUSA_GEN2_ID,
            budget_inr=None,  # unlimited
            max_candidates=10,
            gear_span=2,
            launch_steps=3,
        )

    def test_structure(self):
        r = self.result
        for key in (
            "class_label",
            "baseline_et_s",
            "tire_stage",
            "build",
            "setup",
            "final_et_s",
            "total_delta_s",
        ):
            self.assertIn(key, r)
        self.assertEqual(r["class_label"], "outlaw")

    def test_unlimited_budget_resolution(self):
        self.assertTrue(self.result["budget_unlimited"])
        self.assertEqual(self.result["budget_resolved_inr"], UNLIMITED_BUDGET_INR)
        self.assertIsNone(self.result["budget_inr"])

    def test_final_faster_than_baseline(self):
        self.assertLess(self.result["final_et_s"], self.result["baseline_et_s"])
        self.assertLess(self.result["total_delta_s"], 0)
        # A no-limit Hayabusa build must find at least a few tenths.
        self.assertLess(self.result["total_delta_s"], -0.2)

    def test_baseline_sane(self):
        self.assertGreater(self.result["baseline_et_s"], 9.0)
        self.assertLess(self.result["baseline_et_s"], 11.5)

    def test_drag_tire_applied_when_available(self):
        # Hayabusa carries drag_prep fitments in the shipped catalog.
        self.assertTrue(self.result["tire_stage"]["applied"])
        self.assertGreater(
            self.result["tire_stage"]["mu_peak"],
            self.result["tire_stage"]["stock_mu_peak"],
        )

    def test_build_selected_parts(self):
        build = self.result["build"]
        self.assertGreater(len(build["parts"]), 0)
        self.assertEqual(build["profile"], "full_race")
        self.assertGreater(build["total_cost_inr"], 0)

    def test_setup_has_gearing_and_launch(self):
        setup = self.result["setup"]
        self.assertIn("gearing", setup)
        self.assertIn("launch_rpm", setup)
        self.assertIn("combined", setup)

    def test_json_safe(self):
        import json

        _no_finite_violations(self.result)
        json.dumps(self.result, allow_nan=False)  # must not raise

    def test_explicit_budget_capped(self):
        # Structure-only run with a tiny budget: pipeline still completes and
        # respects the cap.
        r = optimize_outlaw(
            self.config,
            PartsRepository(self.db.conn),
            TireRepository(self.db.conn),
            bike_model_id=_HAYABUSA_GEN2_ID,
            budget_inr=50_000,
            max_candidates=8,
            gear_span=1,
            launch_steps=2,
        )
        self.assertFalse(r["budget_unlimited"])
        self.assertEqual(r["budget_resolved_inr"], 50_000)
        self.assertLessEqual(r["build"]["total_cost_inr"], 50_000 * 1.01)


class TestOptimizerBudgetApi(unittest.TestCase):
    def test_budget_none_accepted_and_resolved(self):
        from motoquant.api import OptimizeBuildRequest

        req = OptimizeBuildRequest(bike_preset="gsxr1000_k5")
        self.assertIsNone(req.budget_inr)

    def test_budget_bounds_still_enforced(self):
        import pydantic

        from motoquant.api import OptimizeBuildRequest

        with self.assertRaises(pydantic.ValidationError):
            OptimizeBuildRequest(bike_preset="gsxr1000_k5", budget_inr=9e9)

    def test_outlaw_request_model(self):
        from motoquant.api import OutlawRequest

        req = OutlawRequest(bike_id=11)
        self.assertIsNone(req.budget_inr)
        self.assertEqual(req.goal, "min_et")


class TestJsonSafe(unittest.TestCase):
    """rank_categories can emit avg_cost_per_tenth=inf; bare inf/nan is not
    JSON-compliant and 500s the optimize route (July-3 full-API stress
    battery). json_safe is the shared source-level guard."""

    def test_json_safe_nulls_non_finite(self):
        import json

        from motoquant.analysis.roi import json_safe

        dirty = {
            "a": float("inf"),
            "b": float("-inf"),
            "c": float("nan"),
            "d": [1.0, float("inf"), {"e": float("nan")}],
            "ok": 12.5,
            "s": "x",
        }
        clean = json_safe(dirty)
        self.assertIsNone(clean["a"])
        self.assertIsNone(clean["b"])
        self.assertIsNone(clean["c"])
        self.assertIsNone(clean["d"][1])
        self.assertIsNone(clean["d"][2]["e"])
        self.assertEqual(clean["ok"], 12.5)
        self.assertEqual(clean["s"], "x")
        json.dumps(clean, allow_nan=False)  # must not raise

    def test_rank_categories_emits_null_not_inf(self):
        # A category whose only "improving" part has an infinite cost-per-tenth
        # must serialize avg_cost_per_tenth as null, never inf.
        import json

        from motoquant.analysis.roi import PartROIResult, rank_categories

        part = PartROIResult(
            part_id=1,
            part_name="p",
            brand="b",
            category="exhaust",
            category_display="Exhaust",
            price_inr=1000.0,
            price_usd=None,
            base_et_s=10.0,
            modified_et_s=9.95,
            delta_et_s=0.05,
            delta_trap_ms=0.1,
            roi_score=1.0,
            cost_per_tenth_inr=float("inf"),
            is_compatible=True,
            availability="in_stock",
        )
        summary = rank_categories([part])
        self.assertIsNone(summary[0]["avg_cost_per_tenth"])
        json.dumps(summary, allow_nan=False)


def setUpModule():
    global _OLD_ENV_DB
    _OLD_ENV_DB = os.environ.get("MOTOQUANT_DB")
    """Re-assert this module's tmp DB at run time (collection-order-proof —
    same pattern as tests/test_api.py)."""
    os.environ["MOTOQUANT_DB"] = _tmp.name


def tearDownModule():
    if _OLD_ENV_DB is None:
        os.environ.pop("MOTOQUANT_DB", None)
    else:
        os.environ["MOTOQUANT_DB"] = _OLD_ENV_DB
    try:
        os.unlink(_tmp.name)
    except OSError:
        pass


if __name__ == "__main__":
    unittest.main()
