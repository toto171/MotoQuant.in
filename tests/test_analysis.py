"""
MotoQuant Pro — Phase 4 Analysis Tests
========================================
Tests for the Parts ROI engine and Sobol sensitivity analysis.

Test philosophy
---------------
- ROI tests use the in-memory DB seeded with real catalog data so that
  part→param mappings are exercised end-to-end.
- Sobol tests use n_samples=32 (fast) and verify index properties
  (bounds, ordering, reproducibility) rather than numeric precision.
- All DB connections use the WAL-fallback to DELETE mode via /tmp/.
"""

import copy
import json
import math
import os
import sys
import tempfile
import unittest
from io import StringIO
from unittest.mock import patch

import numpy as np

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motoquant.analysis.roi import (
    BuildROIResult,
    PartROIResult,
    _roi_metrics,
    _run_et as roi_run_et,
    compute_parts_roi,
    find_best_build,
    rank_categories,
)
from motoquant.analysis.sobol import (
    DEFAULT_PARAM_BOUNDS,
    SobolParamSpec,
    SobolResult,
    _apply_sample_row,
    _get_nested,
    _set_nested,
    compute_sobol_indices,
    compute_sobol_subset,
)
from motoquant.database.connection import MotoQuantDB
from motoquant.database.parts_repo import PartsRepository
from motoquant.defaults import gsxr1000_k5

# ─────────────────────────────────────────────────────────────────
# Shared fixture: seeded DB in /tmp (WAL-safe)
# ─────────────────────────────────────────────────────────────────


class _TestDB:
    """Creates a temporary DB in /tmp, seeds it, and caches the MotoQuantDB."""

    _db_path = None
    _mdb = None

    @classmethod
    def get_mdb(cls) -> MotoQuantDB:
        if cls._mdb is None:
            tmp = tempfile.NamedTemporaryFile(suffix=".db", dir="/tmp", delete=False)
            cls._db_path = tmp.name
            tmp.close()
            mdb = MotoQuantDB(cls._db_path)
            mdb.connect()
            mdb.conn.execute("PRAGMA journal_mode=DELETE")
            mdb.initialize()
            # Run full catalog seed (tires, parts, bikes, fitments)
            from motoquant.database.seed import seed_all

            seed_all(mdb)
            cls._mdb = mdb
        return cls._mdb

    @classmethod
    def get_conn(cls):
        return cls.get_mdb().conn


def _seed_mdb() -> MotoQuantDB:
    """Ensure the shared seeded DB is ready and return its MotoQuantDB."""
    return _TestDB.get_mdb()


def _parts_repo() -> PartsRepository:
    """Return a PartsRepository on the seeded DB."""
    return PartsRepository(_TestDB.get_conn())


# ═══════════════════════════════════════════
# ROI — Unit tests (no DB)
# ═══════════════════════════════════════════


class TestROIMetrics(unittest.TestCase):
    """Unit tests for the _roi_metrics helper."""

    def test_no_improvement_returns_zero_roi(self):
        roi, cpt = _roi_metrics(price_inr=10_000, delta_et_s=0.0)
        self.assertEqual(roi, 0.0)
        self.assertEqual(cpt, float("inf"))

    def test_negative_improvement_returns_zero_roi(self):
        roi, cpt = _roi_metrics(price_inr=10_000, delta_et_s=-0.05)
        self.assertEqual(roi, 0.0)
        self.assertEqual(cpt, float("inf"))

    def test_free_part_with_improvement_returns_inf_roi(self):
        roi, cpt = _roi_metrics(price_inr=0.0, delta_et_s=0.10)
        self.assertEqual(roi, float("inf"))
        self.assertEqual(cpt, 0.0)

    def test_paid_part_roi_formula(self):
        # 0.1 s gain @ ₹10,000: roi = (0.1 / 10_000) * 10_000 * 10 = 1.0
        roi, cpt = _roi_metrics(price_inr=10_000, delta_et_s=0.1)
        self.assertAlmostEqual(roi, 1.0, places=6)
        # cost_per_tenth = 10_000 / (0.1 * 10) = 10_000 / 1 = 10_000
        self.assertAlmostEqual(cpt, 10_000.0, places=6)

    def test_higher_price_lower_roi(self):
        roi_cheap, _ = _roi_metrics(price_inr=5_000, delta_et_s=0.1)
        roi_expensive, _ = _roi_metrics(price_inr=20_000, delta_et_s=0.1)
        self.assertGreater(roi_cheap, roi_expensive)

    def test_larger_gain_higher_roi(self):
        roi_small, _ = _roi_metrics(price_inr=10_000, delta_et_s=0.05)
        roi_large, _ = _roi_metrics(price_inr=10_000, delta_et_s=0.20)
        self.assertGreater(roi_large, roi_small)

    def test_none_price_treated_as_zero(self):
        roi, cpt = _roi_metrics(price_inr=None, delta_et_s=0.1)
        self.assertEqual(roi, float("inf"))


class TestRunET(unittest.TestCase):
    """Verify that the _run_et helper produces physically sane values."""

    def test_gsxr1000_et_in_range(self):
        config = gsxr1000_k5()
        et, trap = roi_run_et(config)
        self.assertGreater(et, 9.0)
        self.assertLess(et, 12.0)
        # trap speed is in m/s — K5 does ~66 m/s (239 km/h)
        self.assertGreater(trap, 55.0)
        self.assertLess(trap, 90.0)

    def test_heavier_bike_slower(self):
        light = gsxr1000_k5()
        heavy = copy.deepcopy(light)
        heavy.chassis.dry_mass_kg += 30
        et_l, _ = roi_run_et(light)
        et_h, _ = roi_run_et(heavy)
        self.assertGreater(et_h, et_l)

    def test_more_power_faster(self):
        base = gsxr1000_k5()
        faster = copy.deepcopy(base)
        # Scale the dyno curve to actually deliver more power
        # (setting peak_power_hp alone has no effect when a dyno curve is present)
        faster.engine.peak_power_hp += 30
        if faster.engine.dyno_curve is not None:
            from motoquant.models import DynoCurve

            dc = faster.engine.dyno_curve
            ratio = faster.engine.peak_power_hp / base.engine.peak_power_hp
            faster.engine.dyno_curve = DynoCurve(
                rpm=dc.rpm.copy(),
                torque_nm=dc.torque_nm * ratio,
                is_at_wheel=dc.is_at_wheel,
            )
        et_b, _ = roi_run_et(base)
        et_f, _ = roi_run_et(faster)
        self.assertLess(et_f, et_b)


# ═══════════════════════════════════════════
# ROI — Integration tests (real DB)
# ═══════════════════════════════════════════


class TestComputePartsROI(unittest.TestCase):
    """compute_parts_roi against the seeded catalog.

    All tests share a single compute_parts_roi call from setUpClass to avoid
    re-running 15 simulations per test method.
    """

    @classmethod
    def setUpClass(cls):
        _seed_mdb()
        cls.parts_repo = _parts_repo()
        cls.config = gsxr1000_k5()
        # 15 parts × 0.3 s ≈ 4.5 s — acceptable for setUpClass
        all_parts = cls.parts_repo.search(limit=15)
        cls.part_ids = [p["id"] for p in all_parts]
        cls.results = compute_parts_roi(cls.config, cls.part_ids, cls.parts_repo)

    def test_returns_list_of_roi_results(self):
        self.assertIsInstance(self.results, list)
        for r in self.results:
            self.assertIsInstance(r, PartROIResult)

    def test_all_parts_evaluated(self):
        returned_ids = {r.part_id for r in self.results}
        for pid in self.part_ids:
            if self.parts_repo.get(pid) is not None:
                self.assertIn(pid, returned_ids)

    def test_base_et_consistent_across_results(self):
        if len(self.results) < 2:
            self.skipTest("Not enough parts to compare")
        base_ets = {r.base_et_s for r in self.results}
        self.assertEqual(len(base_ets), 1)

    def test_improving_parts_have_positive_delta(self):
        for r in self.results:
            if r.roi_score > 0:
                self.assertGreater(r.delta_et_s, 0)

    def test_sorted_by_roi_score_descending(self):
        scores = [r.roi_score for r in self.results]
        finite = [s for s in scores if not math.isinf(s)]
        self.assertEqual(finite, sorted(finite, reverse=True))

    def test_cost_per_tenth_infinite_when_no_gain(self):
        for r in self.results:
            if r.delta_et_s <= 0:
                self.assertEqual(r.cost_per_tenth_inr, float("inf"))

    def test_empty_part_ids_returns_empty_list(self):
        results = compute_parts_roi(self.config, [], self.parts_repo)
        self.assertEqual(results, [])

    def test_invalid_part_id_silently_skipped(self):
        results = compute_parts_roi(self.config, [999_999], self.parts_repo)
        self.assertEqual(results, [])

    def test_summary_line_string(self):
        if not self.results:
            self.skipTest("No parts returned")
        line = self.results[0].summary_line()
        self.assertIsInstance(line, str)
        self.assertGreater(len(line), 20)


class TestFindBestBuild(unittest.TestCase):
    """find_best_build knapsack DP.

    All tests share results pre-computed in setUpClass to avoid re-running
    the full part catalog simulation (~70 parts × 0.3 s) per test method.
    """

    BUDGET = 100_000  # rupees

    @classmethod
    def setUpClass(cls):
        _seed_mdb()
        cls.parts_repo = _parts_repo()
        cls.config = gsxr1000_k5()
        # Use a small part slice to keep setUpClass fast (~10 parts × 0.3s + 1 build sim)
        all_parts = cls.parts_repo.search(limit=12)
        cls.part_ids = [p["id"] for p in all_parts]
        # Pre-compute the reference build
        cls.build = find_best_build(
            cls.config,
            budget_inr=cls.BUDGET,
            parts_repo=cls.parts_repo,
            part_ids=cls.part_ids,
        )
        # Zero-budget build (all free-only)
        cls.zero_build = find_best_build(
            cls.config,
            budget_inr=0,
            parts_repo=cls.parts_repo,
            part_ids=cls.part_ids,
        )

    def test_returns_build_roi_result(self):
        self.assertIsInstance(self.build, BuildROIResult)

    def test_total_cost_within_budget(self):
        self.assertLessEqual(self.build.total_cost_inr, self.BUDGET + 1)

    def test_zero_budget_selects_nothing_or_free_only(self):
        for p in self.zero_build.selected_parts:
            self.assertLessEqual(p.price_inr, 0)

    def test_modified_et_le_base_et(self):
        self.assertLessEqual(self.build.modified_et_s, self.build.base_et_s + 0.01)

    def test_delta_et_consistent(self):
        expected_delta = self.build.base_et_s - self.build.modified_et_s
        self.assertAlmostEqual(self.build.delta_et_s, expected_delta, places=4)

    def test_summary_string(self):
        s = self.build.summary()
        self.assertIn("Budget", s)
        self.assertIn("Base ET", s)

    def test_result_has_evaluated_count(self):
        self.assertGreaterEqual(self.build.parts_evaluated, 0)

    def test_parts_evaluated_matches_input(self):
        self.assertEqual(self.build.parts_evaluated, len(self.part_ids))


class TestRankCategories(unittest.TestCase):
    """rank_categories aggregation helper."""

    def _make_roi_result(self, cat, cat_display, delta_et, price):
        roi, cpt = _roi_metrics(price, delta_et)
        return PartROIResult(
            part_id=1,
            part_name="Test Part",
            brand="Test",
            category=cat,
            category_display=cat_display,
            price_inr=price,
            price_usd=None,
            base_et_s=10.0,
            modified_et_s=10.0 - delta_et,
            delta_et_s=delta_et,
            delta_trap_ms=0.0,
            roi_score=roi,
            cost_per_tenth_inr=cpt,
            is_compatible=True,
            availability="in_stock",
        )

    def test_categories_sorted_by_best_roi(self):
        results = [
            self._make_roi_result("exhaust", "Exhaust", 0.05, 10_000),
            self._make_roi_result("ecu_flash", "ECU Flash", 0.20, 5_000),
            self._make_roi_result("exhaust", "Exhaust", 0.08, 12_000),
        ]
        cats = rank_categories(results)
        self.assertEqual(cats[0]["category"], "ECU Flash")  # higher ROI

    def test_no_improvement_parts_excluded_from_summary(self):
        results = [
            self._make_roi_result("exhaust", "Exhaust", 0.0, 10_000),
        ]
        cats = rank_categories(results)
        self.assertEqual(len(cats), 0)

    def test_improving_count_correct(self):
        results = [
            self._make_roi_result("exhaust", "Exhaust", 0.05, 10_000),
            self._make_roi_result("exhaust", "Exhaust", -0.01, 8_000),
        ]
        cats = rank_categories(results)
        self.assertEqual(cats[0]["improving_count"], 1)
        self.assertEqual(cats[0]["part_count"], 2)


# ═══════════════════════════════════════════
# Sobol — Unit tests
# ═══════════════════════════════════════════


class TestSobolParamSpec(unittest.TestCase):
    """SobolParamSpec validation."""

    def test_valid_spec(self):
        spec = SobolParamSpec("tires.mu_peak", 0.8, 1.4, "absolute", "μ_peak")
        self.assertEqual(spec.path, "tires.mu_peak")
        self.assertEqual(spec.kind, "absolute")

    def test_invalid_kind_raises(self):
        with self.assertRaises(ValueError):
            SobolParamSpec("tires.mu_peak", 0.8, 1.4, "banana")

    def test_low_ge_high_raises(self):
        with self.assertRaises(ValueError):
            SobolParamSpec("tires.mu_peak", 1.4, 0.8, "absolute")

    def test_low_equals_high_raises(self):
        with self.assertRaises(ValueError):
            SobolParamSpec("tires.mu_peak", 1.0, 1.0, "absolute")


class TestNestedHelpers(unittest.TestCase):
    """_get_nested and _set_nested helpers."""

    def test_get_nested_two_levels(self):
        cfg = gsxr1000_k5()
        val = _get_nested(cfg, "tires.mu_peak")
        self.assertIsInstance(val, float)
        self.assertGreater(val, 0)

    def test_set_nested_two_levels(self):
        cfg = copy.deepcopy(gsxr1000_k5())
        ok = _set_nested(cfg, "tires.mu_peak", 1.25)
        self.assertTrue(ok)
        self.assertAlmostEqual(cfg.tires.mu_peak, 1.25)

    def test_set_nested_invalid_path_returns_false(self):
        cfg = copy.deepcopy(gsxr1000_k5())
        ok = _set_nested(cfg, "tires.nonexistent_field", 1.0)
        self.assertFalse(ok)

    def test_set_nested_three_levels_not_typical(self):
        # Verify it at least doesn't crash on valid 2-level paths
        cfg = copy.deepcopy(gsxr1000_k5())
        ok = _set_nested(cfg, "engine.peak_power_hp", 200.0)
        self.assertTrue(ok)
        self.assertAlmostEqual(cfg.engine.peak_power_hp, 200.0)


class TestApplySampleRow(unittest.TestCase):
    """_apply_sample_row correctly modifies config."""

    def setUp(self):
        self.base = gsxr1000_k5()
        self.spec_abs = SobolParamSpec("tires.mu_peak", 0.8, 1.4, "absolute")
        self.spec_rel = SobolParamSpec("engine.peak_power_hp", 0.8, 1.2, "relative")
        self.nominal = [
            _get_nested(self.base, "tires.mu_peak"),
            _get_nested(self.base, "engine.peak_power_hp"),
        ]

    def test_absolute_spec_sets_value_directly(self):
        row = np.array([1.1, 1.0])
        cfg = _apply_sample_row(
            self.base, [self.spec_abs, self.spec_rel], self.nominal, row
        )
        self.assertAlmostEqual(cfg.tires.mu_peak, 1.1)

    def test_relative_spec_scales_nominal(self):
        row = np.array([1.0, 1.10])  # 10% power boost
        cfg = _apply_sample_row(
            self.base, [self.spec_abs, self.spec_rel], self.nominal, row
        )
        expect = self.nominal[1] * 1.10
        self.assertAlmostEqual(cfg.engine.peak_power_hp, expect, places=4)

    def test_base_config_not_mutated(self):
        orig_mu = self.base.tires.mu_peak
        row = np.array([0.85, 1.0])
        _apply_sample_row(self.base, [self.spec_abs, self.spec_rel], self.nominal, row)
        self.assertAlmostEqual(self.base.tires.mu_peak, orig_mu)


class TestDefaultParamBounds(unittest.TestCase):
    """DEFAULT_PARAM_BOUNDS validity checks."""

    def test_all_paths_exist_in_config(self):
        cfg = gsxr1000_k5()
        for key, spec in DEFAULT_PARAM_BOUNDS.items():
            val = _get_nested(cfg, spec.path)
            self.assertIsNotNone(val, msg=f"Path {spec.path!r} not found in BikeConfig")

    def test_all_specs_valid(self):
        for key, spec in DEFAULT_PARAM_BOUNDS.items():
            self.assertIn(spec.kind, ("absolute", "relative"))
            self.assertLess(spec.low, spec.high)
            self.assertGreater(len(spec.description), 0)

    def test_contains_expected_keys(self):
        expected = {
            "peak_power",
            "dry_mass",
            "aero_cd",
            "frontal_area",
            "tire_mu",
            "rolling_radius",
            "reaction_time",
            "redline_rpm",
            "primary_ratio",
            "final_drive_ratio",
        }
        self.assertTrue(expected.issubset(DEFAULT_PARAM_BOUNDS.keys()))


# ═══════════════════════════════════════════
# Sobol — Integration tests (small N for speed)
# ═══════════════════════════════════════════


class TestComputeSobolIndices(unittest.TestCase):
    """compute_sobol_indices with a 2-parameter subset for speed.

    All sims (including reproducibility check) precomputed in setUpClass so
    that individual test methods run fast (no re-computation).
    Total sim count: 2×[(2+2)×32] = 256 sims × 0.3 s ≈ 77 s.
    """

    @classmethod
    def setUpClass(cls):
        cls.config = gsxr1000_k5()
        # Use 2-param subset: (2+2)*32 = 128 sims ≈ 38 s per run
        cls.specs = {
            "peak_power": DEFAULT_PARAM_BOUNDS["peak_power"],
            "tire_mu": DEFAULT_PARAM_BOUNDS["tire_mu"],
        }
        # Primary result (seed=42)
        cls.result = compute_sobol_indices(
            cls.config, param_specs=cls.specs, n_samples=32, seed=42
        )
        # Second run with same seed (for reproducibility test)
        cls.result2 = compute_sobol_indices(
            cls.config, param_specs=cls.specs, n_samples=32, seed=42
        )

    def test_returns_sobol_result(self):
        self.assertIsInstance(self.result, SobolResult)

    def test_parameters_list_matches_specs(self):
        self.assertEqual(set(self.result.parameters), set(self.specs.keys()))
        self.assertEqual(len(self.result.parameters), 2)

    def test_array_lengths_match_parameters(self):
        k = len(self.specs)
        self.assertEqual(len(self.result.S1), k)
        self.assertEqual(len(self.result.ST), k)
        self.assertEqual(len(self.result.S1_conf), k)
        self.assertEqual(len(self.result.ST_conf), k)

    def test_st_ge_s1_for_all_params(self):
        # Total-order must be ≥ first-order (Saltelli, 2010, Theorem 1)
        # Allow small negative values due to estimator variance at small N
        for st, s1 in zip(self.result.ST, self.result.S1):
            self.assertGreaterEqual(
                st, s1 - 0.15, msg=f"ST ({st:.4f}) < S1 ({s1:.4f}) beyond tolerance"
            )

    def test_st_values_in_plausible_range(self):
        for st in self.result.ST:
            self.assertGreater(st, -0.3)
            self.assertLess(st, 1.5)

    def test_n_simulations_correct(self):
        k = len(self.specs)  # = 2
        # Saltelli/Sobol: N * (k + 2) without second-order
        expected = 32 * (k + 2)
        self.assertEqual(self.result.n_simulations, expected)

    def test_base_et_in_physical_range(self):
        self.assertGreater(self.result.base_et_s, 9.0)
        self.assertLess(self.result.base_et_s, 12.0)

    def test_et_range_is_plausible(self):
        lo, hi = self.result.et_range
        self.assertGreater(lo, 7.0)
        self.assertLess(hi, 20.0)
        self.assertLess(lo, hi)

    def test_reproducibility_with_same_seed(self):
        # result2 was precomputed in setUpClass with the same seed
        np.testing.assert_array_almost_equal(self.result.ST, self.result2.ST, decimal=6)

    def test_same_seed_gives_same_et_range(self):
        self.assertAlmostEqual(
            self.result.et_range[0], self.result2.et_range[0], places=4
        )
        self.assertAlmostEqual(
            self.result.et_range[1], self.result2.et_range[1], places=4
        )

    def test_to_dict_structure(self):
        d = self.result.to_dict()
        self.assertIn("indices", d)
        self.assertIn("n_simulations", d)
        self.assertIn("base_et_s", d)
        self.assertIn("et_mean", d)
        self.assertIn("et_std", d)
        for idx in d["indices"]:
            self.assertIn("parameter", idx)
            self.assertIn("S1", idx)
            self.assertIn("ST", idx)
            self.assertIn("interaction", idx)

    def test_to_dict_sorted_by_st_descending(self):
        d = self.result.to_dict()
        sts = [idx["ST"] for idx in d["indices"]]
        self.assertEqual(sts, sorted(sts, reverse=True))

    def test_print_table_runs_without_error(self):
        import io

        buf = io.StringIO()
        with patch("sys.stdout", buf):
            self.result.print_table()
        output = buf.getvalue()
        self.assertIn("S1", output)
        self.assertIn("ST", output)


class TestComputeSobolSubset(unittest.TestCase):
    """compute_sobol_subset convenience wrapper."""

    def test_valid_subset_runs(self):
        config = gsxr1000_k5()
        result = compute_sobol_subset(
            config, param_keys=["peak_power", "tire_mu"], n_samples=32, seed=0
        )
        self.assertEqual(len(result.parameters), 2)

    def test_invalid_key_raises(self):
        config = gsxr1000_k5()
        with self.assertRaises(ValueError):
            compute_sobol_subset(config, param_keys=["does_not_exist"], n_samples=32)

    def test_single_param_runs(self):
        config = gsxr1000_k5()
        result = compute_sobol_subset(
            config, param_keys=["tire_mu"], n_samples=32, seed=1
        )
        self.assertEqual(len(result.parameters), 1)
        # With one param, all variance is direct (no interactions)
        self.assertAlmostEqual(result.S1[0], result.ST[0], delta=0.2)


# ═══════════════════════════════════════════
# CLI integration tests
# ═══════════════════════════════════════════


class TestAnalysisCLI(unittest.TestCase):
    """CLI analysis subcommand integration tests."""

    @classmethod
    def setUpClass(cls):
        _seed_mdb()
        cls.db_path = _TestDB._db_path

    def _run_cli(self, args_list):
        """Run the CLI in-process and capture stdout."""
        from motoquant.run import main

        buf = StringIO()
        with patch("sys.stdout", buf):
            ret = main(["--db", self.db_path] + args_list)
        return ret, buf.getvalue()

    def test_analysis_without_subcommand_shows_help(self):
        ret, output = self._run_cli(["analysis"])
        # Should exit gracefully (not crash)
        self.assertIn(ret, [0, 1, None])

    def test_roi_default_runs(self):
        """ROI on default bike (no --bike-id) with first 5 parts."""
        parts = _parts_repo().search(limit=5)
        if not parts:
            self.skipTest("No parts in DB")
        ids_str = ",".join(str(p["id"]) for p in parts)
        ret, output = self._run_cli(["analysis", "roi", "--part-ids", ids_str])
        self.assertEqual(ret, 0)
        self.assertIn("PARTS ROI", output)

    def test_roi_json_output(self):
        parts = _parts_repo().search(limit=3)
        if not parts:
            self.skipTest("No parts in DB")
        ids_str = ",".join(str(p["id"]) for p in parts)
        ret, output = self._run_cli(
            ["analysis", "roi", "--part-ids", ids_str, "--json"]
        )
        self.assertEqual(ret, 0)
        parsed = json.loads(output)
        self.assertIn("parts", parsed)
        self.assertIn("base_et", parsed)

    def test_roi_optimize_flag(self):
        ret, output = self._run_cli(
            ["analysis", "roi", "--optimize", "--budget", "50000"]
        )
        self.assertEqual(ret, 0)
        self.assertIn("BUILD OPTIMIZER", output)

    def test_roi_optimize_json(self):
        ret, output = self._run_cli(
            ["analysis", "roi", "--optimize", "--budget", "50000", "--json"]
        )
        self.assertEqual(ret, 0)
        parsed = json.loads(output)
        self.assertIn("selected_parts", parsed)
        self.assertIn("total_cost_inr", parsed)
        self.assertLessEqual(parsed["total_cost_inr"], 50_000 + 1)

    def test_roi_by_category(self):
        parts = _parts_repo().search(limit=10)
        if not parts:
            self.skipTest("No parts in DB")
        ids_str = ",".join(str(p["id"]) for p in parts)
        ret, output = self._run_cli(
            ["analysis", "roi", "--part-ids", ids_str, "--by-category"]
        )
        self.assertEqual(ret, 0)

    def test_sobol_small_n_runs(self):
        ret, output = self._run_cli(
            ["analysis", "sobol", "--n-samples", "32", "--params", "peak_power,tire_mu"]
        )
        self.assertEqual(ret, 0)
        self.assertIn("SOBOL SENSITIVITY", output)

    def test_sobol_json_output(self):
        ret, output = self._run_cli(
            [
                "analysis",
                "sobol",
                "--n-samples",
                "32",
                "--params",
                "peak_power,tire_mu",
                "--json",
            ]
        )
        self.assertEqual(ret, 0)
        parsed = json.loads(output)
        self.assertIn("indices", parsed)
        self.assertIn("n_simulations", parsed)
        self.assertGreater(len(parsed["indices"]), 0)

    def test_sobol_unknown_bike_id(self):
        ret, output = self._run_cli(
            [
                "analysis",
                "sobol",
                "--bike-id",
                "999999",
                "--n-samples",
                "32",
                "--params",
                "peak_power",
            ]
        )
        self.assertEqual(ret, 1)


if __name__ == "__main__":
    unittest.main()
