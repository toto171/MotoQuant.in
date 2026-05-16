"""
MotoQuant Pro — Smart Recommendations Engine Tests
=====================================================
Tests for the build recommender, upgrade path generator, and
compatibility/synergy detection.

Test philosophy
---------------
- Uses the same in-memory DB pattern as test_analysis.py (seed_all in /tmp).
- Focuses on structural correctness, data types, and business logic
  (synergy detection, profile filtering, tier ordering) rather than
  exact numerical values (which depend on the physics engine).
- Lightweight: runs the physics engine only where necessary, caches
  baseline ET aggressively.
"""

import json
import math
import os
import sys
import unittest

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motoquant.analysis.recommendations import (
    _PROFILE_CATEGORIES,
    EXCLUSIVE_GROUPS,
    SOFT_DEPENDENCIES,
    SYNERGIES,
    BuildProfile,
    BuildRecommendation,
    BuildTier,
    CompatibilityWarning,
    NextUpgrade,
    SynergyNote,
    UpgradePath,
    _detect_synergies,
    _detect_warnings,
    _filter_parts_by_profile,
    generate_upgrade_path,
    get_category_upgrade_order,
    recommend_build,
)
from motoquant.analysis.roi import BuildROIResult, PartROIResult
from motoquant.database.connection import MotoQuantDB
from motoquant.defaults import gsxr1000_k5

# Shared seeded-DB singleton (process-scoped, WAL-fallback to DELETE for /tmp).
# See tests/_helpers.py for the canonical definition.
from tests._helpers import SeededTestDB as _TestDB  # noqa: E402


# ─────────────────────────────────────────────────────────────────
# 1. BuildProfile enum tests
# ─────────────────────────────────────────────────────────────────


class TestBuildProfile(unittest.TestCase):
    """Build profile enum and values."""

    def test_all_profiles_exist(self):
        profiles = [
            BuildProfile.ALL,
            BuildProfile.STREET_LEGAL,
            BuildProfile.DRAG_PREP,
            BuildProfile.FULL_RACE,
        ]
        self.assertEqual(len(profiles), 4)

    def test_profile_values(self):
        self.assertEqual(BuildProfile.ALL.value, "all")
        self.assertEqual(BuildProfile.STREET_LEGAL.value, "street_legal")
        self.assertEqual(BuildProfile.DRAG_PREP.value, "drag_prep")
        self.assertEqual(BuildProfile.FULL_RACE.value, "full_race")

    def test_profile_categories_defined(self):
        """Every non-ALL profile must have a category set."""
        for profile in BuildProfile:
            if profile == BuildProfile.ALL:
                continue
            self.assertIn(profile, _PROFILE_CATEGORIES)
            self.assertIsInstance(_PROFILE_CATEGORIES[profile], set)
            self.assertTrue(len(_PROFILE_CATEGORIES[profile]) > 0)

    def test_street_legal_excludes_boost(self):
        """Street-legal profile must NOT include turbo/boost kits."""
        street = _PROFILE_CATEGORIES[BuildProfile.STREET_LEGAL]
        self.assertNotIn("boost_kit", street)
        self.assertNotIn("nitrous", street)
        self.assertNotIn("wheelie_bar", street)

    def test_drag_prep_includes_wheelie_bar(self):
        drag = _PROFILE_CATEGORIES[BuildProfile.DRAG_PREP]
        self.assertIn("wheelie_bar", drag)
        self.assertIn("swingarm_ext", drag)

    def test_full_race_superset_of_drag_prep(self):
        """Full race profile should include everything drag prep does."""
        drag = _PROFILE_CATEGORIES[BuildProfile.DRAG_PREP]
        race = _PROFILE_CATEGORIES[BuildProfile.FULL_RACE]
        self.assertTrue(drag.issubset(race))


# ─────────────────────────────────────────────────────────────────
# 2. Profile filtering tests
# ─────────────────────────────────────────────────────────────────


class TestProfileFiltering(unittest.TestCase):
    """Test _filter_parts_by_profile."""

    def _make_parts(self):
        return [
            {"id": 1, "category_name": "exhaust"},
            {"id": 2, "category_name": "boost_kit"},
            {"id": 3, "category_name": "ecu"},
            {"id": 4, "category_name": "wheelie_bar"},
            {"id": 5, "category_name": "tire"},
        ]

    def test_all_profile_returns_all(self):
        parts = self._make_parts()
        result = _filter_parts_by_profile(parts, BuildProfile.ALL)
        self.assertEqual(len(result), 5)

    def test_street_legal_filters_boost_and_wheelie(self):
        parts = self._make_parts()
        result = _filter_parts_by_profile(parts, BuildProfile.STREET_LEGAL)
        cats = [p["category_name"] for p in result]
        self.assertNotIn("boost_kit", cats)
        self.assertNotIn("wheelie_bar", cats)
        self.assertIn("exhaust", cats)
        self.assertIn("ecu", cats)
        self.assertIn("tire", cats)

    def test_drag_prep_includes_wheelie_bar(self):
        parts = self._make_parts()
        result = _filter_parts_by_profile(parts, BuildProfile.DRAG_PREP)
        cats = [p["category_name"] for p in result]
        self.assertIn("wheelie_bar", cats)

    def test_empty_parts_list(self):
        result = _filter_parts_by_profile([], BuildProfile.STREET_LEGAL)
        self.assertEqual(result, [])


# ─────────────────────────────────────────────────────────────────
# 3. Synergy detection tests
# ─────────────────────────────────────────────────────────────────


class TestSynergyDetection(unittest.TestCase):
    """Test _detect_synergies."""

    def _make_roi(self, category: str) -> PartROIResult:
        return PartROIResult(
            part_id=1,
            part_name="Test",
            brand="Test",
            category=category,
            category_display=category.title(),
            price_inr=1000,
            price_usd=None,
            base_et_s=10.0,
            modified_et_s=9.9,
            delta_et_s=0.1,
            delta_trap_ms=1.0,
            roi_score=1.0,
            cost_per_tenth_inr=10000,
            is_compatible=True,
            availability="in_stock",
        )

    def test_exhaust_ecu_synergy(self):
        parts = [self._make_roi("exhaust"), self._make_roi("ecu")]
        synergies = _detect_synergies(parts)
        cats = [(s.category_a, s.category_b) for s in synergies]
        self.assertIn(("exhaust", "ecu"), cats)

    def test_no_synergy_for_unrelated_parts(self):
        parts = [self._make_roi("battery"), self._make_roi("brakes")]
        synergies = _detect_synergies(parts)
        self.assertEqual(len(synergies), 0)

    def test_boost_fuel_synergy(self):
        parts = [self._make_roi("boost_kit"), self._make_roi("fuel_system")]
        synergies = _detect_synergies(parts)
        cats = [(s.category_a, s.category_b) for s in synergies]
        self.assertIn(("boost_kit", "fuel_system"), cats)

    def test_multiple_synergies(self):
        parts = [
            self._make_roi("exhaust"),
            self._make_roi("ecu"),
            self._make_roi("air_filter"),
        ]
        synergies = _detect_synergies(parts)
        # exhaust+ecu AND exhaust+air_filter
        self.assertGreaterEqual(len(synergies), 2)

    def test_empty_parts(self):
        self.assertEqual(_detect_synergies([]), [])

    def test_synergy_note_fields(self):
        parts = [self._make_roi("exhaust"), self._make_roi("ecu")]
        synergies = _detect_synergies(parts)
        s = synergies[0]
        self.assertIsInstance(s, SynergyNote)
        self.assertIsInstance(s.multiplier, float)
        self.assertGreater(s.multiplier, 1.0)
        self.assertTrue(len(s.description) > 10)


# ─────────────────────────────────────────────────────────────────
# 4. Warning detection tests
# ─────────────────────────────────────────────────────────────────


class TestWarningDetection(unittest.TestCase):
    """Test _detect_warnings."""

    def _make_roi(self, category: str, part_id: int = 1) -> PartROIResult:
        return PartROIResult(
            part_id=part_id,
            part_name="Test",
            brand="Test",
            category=category,
            category_display=category.title(),
            price_inr=1000,
            price_usd=None,
            base_et_s=10.0,
            modified_et_s=9.9,
            delta_et_s=0.1,
            delta_trap_ms=1.0,
            roi_score=1.0,
            cost_per_tenth_inr=10000,
            is_compatible=True,
            availability="in_stock",
        )

    def test_boost_without_fuel_warns(self):
        """Turbo without fuel system upgrade should warn."""
        parts = [self._make_roi("boost_kit")]
        warns = _detect_warnings(parts)
        messages = [w.message for w in warns]
        self.assertTrue(any("fuel" in m.lower() for m in messages))

    def test_boost_with_fuel_no_fuel_warning(self):
        """Turbo WITH fuel system should not warn about fuel."""
        parts = [self._make_roi("boost_kit"), self._make_roi("fuel_system")]
        warns = _detect_warnings(parts)
        fuel_warns = [
            w
            for w in warns
            if "fuel" in w.message.lower() and w.category_a == "boost_kit"
        ]
        self.assertEqual(len(fuel_warns), 0)

    def test_nitrous_without_ecu_warns(self):
        parts = [self._make_roi("nitrous")]
        warns = _detect_warnings(parts)
        messages = [w.message for w in warns]
        has_ecu_warn = any("ecu" in m.lower() for m in messages)
        self.assertTrue(has_ecu_warn)

    def test_duplicate_exhaust_critical(self):
        """Two exhausts should trigger a critical warning."""
        parts = [self._make_roi("exhaust", 1), self._make_roi("exhaust", 2)]
        warns = _detect_warnings(parts)
        critical = [w for w in warns if w.severity == "critical"]
        self.assertTrue(len(critical) > 0)
        self.assertTrue(any("exhaust" in w.message.lower() for w in critical))

    def test_no_warnings_for_clean_build(self):
        parts = [self._make_roi("exhaust"), self._make_roi("ecu")]
        warns = _detect_warnings(parts)
        # No duplicate, no missing dependency
        self.assertEqual(len(warns), 0)

    def test_warning_severity_values(self):
        parts = [self._make_roi("boost_kit")]
        warns = _detect_warnings(parts)
        for w in warns:
            self.assertIn(w.severity, ("info", "warning", "critical"))

    def test_empty_parts(self):
        self.assertEqual(_detect_warnings([]), [])


# ─────────────────────────────────────────────────────────────────
# 5. Compatibility rules integrity
# ─────────────────────────────────────────────────────────────────


class TestCompatibilityRules(unittest.TestCase):
    """Verify the static compatibility data is well-formed."""

    def test_exclusive_groups_are_sets(self):
        for group in EXCLUSIVE_GROUPS:
            self.assertIsInstance(group, set)
            for cat in group:
                self.assertIsInstance(cat, str)

    def test_synergies_format(self):
        for item in SYNERGIES:
            self.assertEqual(len(item), 4)
            cat_a, cat_b, mult, desc = item
            self.assertIsInstance(cat_a, str)
            self.assertIsInstance(cat_b, str)
            self.assertIsInstance(mult, float)
            self.assertGreater(mult, 1.0)
            self.assertIsInstance(desc, str)

    def test_soft_dependencies_format(self):
        for item in SOFT_DEPENDENCIES:
            self.assertEqual(len(item), 3)
            req_by, dep_on, msg = item
            self.assertIsInstance(req_by, str)
            self.assertIsInstance(dep_on, str)
            self.assertIsInstance(msg, str)

    def test_no_self_synergy(self):
        """A category should not synergize with itself."""
        for cat_a, cat_b, _, _ in SYNERGIES:
            self.assertNotEqual(cat_a, cat_b)

    def test_no_self_dependency(self):
        for req, dep, _ in SOFT_DEPENDENCIES:
            self.assertNotEqual(req, dep)


# ─────────────────────────────────────────────────────────────────
# 6. Data class tests
# ─────────────────────────────────────────────────────────────────


class TestDataClasses(unittest.TestCase):
    """Test that data classes are well-formed and produce output."""

    def _make_roi(self, **overrides) -> PartROIResult:
        defaults = {
            "part_id": 1,
            "part_name": "Test Part",
            "brand": "Test",
            "category": "exhaust",
            "category_display": "Exhaust System",
            "price_inr": 5000,
            "price_usd": None,
            "base_et_s": 10.0,
            "modified_et_s": 9.9,
            "delta_et_s": 0.1,
            "delta_trap_ms": 1.0,
            "roi_score": 2.0,
            "cost_per_tenth_inr": 5000,
            "is_compatible": True,
            "availability": "in_stock",
        }
        defaults.update(overrides)
        return PartROIResult(**defaults)

    def test_synergy_note_creation(self):
        s = SynergyNote("exhaust", "ecu", 1.10, "Test synergy")
        self.assertEqual(s.category_a, "exhaust")
        self.assertEqual(s.multiplier, 1.10)

    def test_compatibility_warning_creation(self):
        w = CompatibilityWarning("warning", "boost_kit", "fuel_system", "Need fuel")
        self.assertEqual(w.severity, "warning")

    def test_next_upgrade_creation(self):
        part = self._make_roi()
        nu = NextUpgrade(part, 0.05, 3000, 1.67, "Good value")
        self.assertEqual(nu.marginal_et_gain_s, 0.05)
        self.assertEqual(nu.reason, "Good value")

    def test_build_tier_summary(self):
        build = BuildROIResult(
            selected_parts=[self._make_roi()],
            total_cost_inr=5000,
            budget_inr=10000,
            base_et_s=10.0,
            modified_et_s=9.9,
            delta_et_s=0.1,
            delta_trap_ms=1.0,
            parts_evaluated=5,
            parts_skipped_incompatible=0,
            parts_skipped_no_gain=1,
        )
        tier = BuildTier("Budget", 10000, build)
        summary = tier.summary()
        self.assertIn("Budget", summary)
        self.assertIn("10,000", summary)

    def test_build_recommendation_summary(self):
        build = BuildROIResult(
            selected_parts=[self._make_roi()],
            total_cost_inr=5000,
            budget_inr=50000,
            base_et_s=10.0,
            modified_et_s=9.9,
            delta_et_s=0.1,
            delta_trap_ms=1.0,
            parts_evaluated=10,
            parts_skipped_incompatible=0,
            parts_skipped_no_gain=2,
        )
        rec = BuildRecommendation(
            bike_name="GSX-R 1000 K5",
            profile=BuildProfile.ALL,
            budget_inr=50000,
            build=build,
            category_priority=[{"category": "Exhaust", "best_et_gain_s": 0.1}],
        )
        summary = rec.summary()
        self.assertIn("GSX-R 1000 K5", summary)
        self.assertIn("50,000", summary)

    def test_build_recommendation_to_dict(self):
        build = BuildROIResult(
            selected_parts=[self._make_roi()],
            total_cost_inr=5000,
            budget_inr=50000,
            base_et_s=10.0,
            modified_et_s=9.9,
            delta_et_s=0.1,
            delta_trap_ms=1.0,
            parts_evaluated=10,
            parts_skipped_incompatible=0,
            parts_skipped_no_gain=2,
        )
        rec = BuildRecommendation(
            bike_name="Test",
            profile=BuildProfile.DRAG_PREP,
            budget_inr=50000,
            build=build,
            category_priority=[],
        )
        d = rec.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["profile"], "drag_prep")
        self.assertEqual(d["budget_inr"], 50000)
        self.assertIn("parts_selected", d)
        self.assertIn("synergies", d)
        self.assertIn("warnings", d)

    def test_to_dict_with_next_upgrade(self):
        part = self._make_roi()
        nu = NextUpgrade(part, 0.05, 3000, 1.67, "Best value")
        build = BuildROIResult(
            selected_parts=[],
            total_cost_inr=0,
            budget_inr=50000,
            base_et_s=10.0,
            modified_et_s=10.0,
            delta_et_s=0.0,
            delta_trap_ms=0.0,
            parts_evaluated=5,
            parts_skipped_incompatible=0,
            parts_skipped_no_gain=5,
        )
        rec = BuildRecommendation(
            bike_name="Test",
            profile=BuildProfile.ALL,
            budget_inr=50000,
            build=build,
            category_priority=[],
            next_upgrade=nu,
        )
        d = rec.to_dict()
        self.assertIn("next_upgrade", d)
        self.assertEqual(d["next_upgrade"]["part_name"], "Test Part")

    def test_to_dict_handles_inf_roi(self):
        part = self._make_roi(roi_score=float("inf"), price_inr=0, is_free=True)
        build = BuildROIResult(
            selected_parts=[part],
            total_cost_inr=0,
            budget_inr=10000,
            base_et_s=10.0,
            modified_et_s=9.9,
            delta_et_s=0.1,
            delta_trap_ms=1.0,
            parts_evaluated=1,
            parts_skipped_incompatible=0,
            parts_skipped_no_gain=0,
        )
        rec = BuildRecommendation(
            bike_name="Test",
            profile=BuildProfile.ALL,
            budget_inr=10000,
            build=build,
            category_priority=[],
        )
        d = rec.to_dict()
        # inf ROI should be serialized as None (JSON doesn't support inf)
        self.assertIsNone(d["parts_selected"][0]["roi_score"])

    def test_upgrade_path_summary(self):
        build = BuildROIResult(
            selected_parts=[],
            total_cost_inr=0,
            budget_inr=10000,
            base_et_s=10.0,
            modified_et_s=10.0,
            delta_et_s=0.0,
            delta_trap_ms=0.0,
            parts_evaluated=0,
            parts_skipped_incompatible=0,
            parts_skipped_no_gain=0,
        )
        tier = BuildTier("Budget", 10000, build)
        path = UpgradePath("Test Bike", [tier])
        summary = path.summary()
        self.assertIn("Test Bike", summary)
        self.assertIn("Budget", summary)

    def test_upgrade_path_to_dict(self):
        build = BuildROIResult(
            selected_parts=[],
            total_cost_inr=0,
            budget_inr=10000,
            base_et_s=10.0,
            modified_et_s=10.0,
            delta_et_s=0.0,
            delta_trap_ms=0.0,
            parts_evaluated=0,
            parts_skipped_incompatible=0,
            parts_skipped_no_gain=0,
        )
        tier = BuildTier("Budget", 10000, build)
        path = UpgradePath("Test Bike", [tier])
        d = path.to_dict()
        self.assertEqual(d["bike_name"], "Test Bike")
        self.assertEqual(len(d["tiers"]), 1)
        self.assertEqual(d["tiers"][0]["tier_name"], "Budget")


# ─────────────────────────────────────────────────────────────────
# 7. Integration tests with seeded DB + physics engine
# ─────────────────────────────────────────────────────────────────


_RUN_SLOW = os.environ.get("MOTOQUANT_SLOW_TESTS", "0") == "1"


@unittest.skipUnless(
    _RUN_SLOW, "Set MOTOQUANT_SLOW_TESTS=1 to run physics-engine integration tests"
)
class TestRecommendBuild(unittest.TestCase):
    """End-to-end recommend_build() with real DB and physics engine."""

    @classmethod
    def setUpClass(cls):
        cls.mdb = _TestDB.get_mdb()
        cls.config = gsxr1000_k5()

    def test_basic_recommendation(self):
        """recommend_build with a reasonable budget produces a result."""
        rec = recommend_build(
            self.config,
            budget_inr=50_000,
            parts_repo=self.mdb.parts,
        )
        self.assertIsInstance(rec, BuildRecommendation)
        self.assertEqual(rec.bike_name, self.config.name)
        self.assertEqual(rec.budget_inr, 50_000)
        self.assertGreaterEqual(rec.build.delta_et_s, 0.0)

    def test_recommendation_respects_budget(self):
        rec = recommend_build(
            self.config,
            budget_inr=50_000,
            parts_repo=self.mdb.parts,
        )
        self.assertLessEqual(rec.build.total_cost_inr, 50_000)

    def test_recommendation_with_profile(self):
        rec = recommend_build(
            self.config,
            budget_inr=100_000,
            parts_repo=self.mdb.parts,
            profile=BuildProfile.STREET_LEGAL,
        )
        self.assertEqual(rec.profile, BuildProfile.STREET_LEGAL)
        # No boost/nitrous/wheelie parts should be in the build
        for part in rec.build.selected_parts:
            self.assertNotIn(part.category, ("boost_kit", "nitrous", "wheelie_bar"))

    def test_zero_budget_returns_free_parts_only(self):
        rec = recommend_build(
            self.config,
            budget_inr=0,
            parts_repo=self.mdb.parts,
        )
        for part in rec.build.selected_parts:
            self.assertEqual(part.price_inr, 0)

    def test_recommendation_includes_category_priority(self):
        rec = recommend_build(
            self.config,
            budget_inr=50_000,
            parts_repo=self.mdb.parts,
        )
        self.assertIsInstance(rec.category_priority, list)

    def test_recommendation_includes_next_upgrade(self):
        rec = recommend_build(
            self.config,
            budget_inr=10_000,
            parts_repo=self.mdb.parts,
            include_next_upgrade=True,
        )
        # With a small budget, there should be a next upgrade suggestion
        # (unless all parts fit, which is unlikely at ₹10k)
        if len(rec.build.selected_parts) < 5:
            self.assertIsNotNone(rec.next_upgrade)

    def test_no_next_upgrade_when_disabled(self):
        rec = recommend_build(
            self.config,
            budget_inr=50_000,
            parts_repo=self.mdb.parts,
            include_next_upgrade=False,
        )
        self.assertIsNone(rec.next_upgrade)

    def test_summary_is_string(self):
        rec = recommend_build(
            self.config,
            budget_inr=50_000,
            parts_repo=self.mdb.parts,
        )
        summary = rec.summary()
        self.assertIsInstance(summary, str)
        self.assertTrue(len(summary) > 50)

    def test_to_dict_is_json_serializable(self):
        rec = recommend_build(
            self.config,
            budget_inr=50_000,
            parts_repo=self.mdb.parts,
        )
        d = rec.to_dict()
        # Should be JSON-serializable (no inf/nan)
        json_str = json.dumps(d)
        self.assertIsInstance(json_str, str)

    def test_larger_budget_improves_et(self):
        """Larger budget should produce equal or better ET."""
        rec_small = recommend_build(
            self.config,
            budget_inr=10_000,
            parts_repo=self.mdb.parts,
        )
        rec_large = recommend_build(
            self.config,
            budget_inr=200_000,
            parts_repo=self.mdb.parts,
        )
        self.assertGreaterEqual(
            rec_large.build.delta_et_s,
            rec_small.build.delta_et_s - 0.001,  # tiny tolerance for floating point
        )


@unittest.skipUnless(
    _RUN_SLOW, "Set MOTOQUANT_SLOW_TESTS=1 to run physics-engine integration tests"
)
class TestGenerateUpgradePath(unittest.TestCase):
    """End-to-end generate_upgrade_path() tests."""

    @classmethod
    def setUpClass(cls):
        cls.mdb = _TestDB.get_mdb()
        cls.config = gsxr1000_k5()

    def test_basic_upgrade_path(self):
        path = generate_upgrade_path(
            self.config,
            parts_repo=self.mdb.parts,
            n_tiers=3,
        )
        self.assertIsInstance(path, UpgradePath)
        self.assertEqual(path.bike_name, self.config.name)
        self.assertEqual(len(path.tiers), 3)

    def test_tiers_have_increasing_budgets(self):
        path = generate_upgrade_path(
            self.config,
            parts_repo=self.mdb.parts,
            n_tiers=3,
        )
        budgets = [t.budget_inr for t in path.tiers]
        for i in range(1, len(budgets)):
            self.assertGreaterEqual(budgets[i], budgets[i - 1])

    def test_tier_names(self):
        path = generate_upgrade_path(
            self.config,
            parts_repo=self.mdb.parts,
            n_tiers=3,
        )
        names = [t.tier_name for t in path.tiers]
        self.assertEqual(names, ["Budget", "Mid-Range", "Performance"])

    def test_custom_budget_tiers(self):
        path = generate_upgrade_path(
            self.config,
            parts_repo=self.mdb.parts,
            budget_tiers=[10_000, 50_000],
        )
        self.assertEqual(len(path.tiers), 2)
        self.assertEqual(path.tiers[0].budget_inr, 10_000)
        self.assertEqual(path.tiers[1].budget_inr, 50_000)

    def test_higher_tier_has_more_or_equal_parts(self):
        path = generate_upgrade_path(
            self.config,
            parts_repo=self.mdb.parts,
            n_tiers=3,
        )
        counts = [len(t.build.selected_parts) for t in path.tiers]
        for i in range(1, len(counts)):
            self.assertGreaterEqual(counts[i], counts[i - 1])

    def test_higher_tier_better_or_equal_et(self):
        path = generate_upgrade_path(
            self.config,
            parts_repo=self.mdb.parts,
            n_tiers=3,
        )
        ets = [t.build.delta_et_s for t in path.tiers]
        for i in range(1, len(ets)):
            self.assertGreaterEqual(ets[i], ets[i - 1] - 0.001)

    def test_two_tier_path(self):
        path = generate_upgrade_path(
            self.config,
            parts_repo=self.mdb.parts,
            n_tiers=2,
        )
        self.assertEqual(len(path.tiers), 2)

    def test_upgrade_path_with_profile(self):
        path = generate_upgrade_path(
            self.config,
            parts_repo=self.mdb.parts,
            profile=BuildProfile.STREET_LEGAL,
            n_tiers=2,
        )
        for tier in path.tiers:
            for part in tier.build.selected_parts:
                self.assertNotIn(part.category, ("boost_kit", "nitrous"))

    def test_summary_is_string(self):
        path = generate_upgrade_path(
            self.config,
            parts_repo=self.mdb.parts,
            n_tiers=2,
        )
        summary = path.summary()
        self.assertIsInstance(summary, str)
        self.assertIn("Upgrade Path", summary)

    def test_to_dict_is_json_serializable(self):
        path = generate_upgrade_path(
            self.config,
            parts_repo=self.mdb.parts,
            n_tiers=2,
        )
        d = path.to_dict()
        json_str = json.dumps(d)
        self.assertIsInstance(json_str, str)

    def test_n_tiers_clamped(self):
        """n_tiers below 2 should be clamped to 2."""
        path = generate_upgrade_path(
            self.config,
            parts_repo=self.mdb.parts,
            n_tiers=1,
        )
        self.assertEqual(len(path.tiers), 2)


@unittest.skipUnless(
    _RUN_SLOW, "Set MOTOQUANT_SLOW_TESTS=1 to run physics-engine integration tests"
)
class TestCategoryUpgradeOrder(unittest.TestCase):
    """Test get_category_upgrade_order()."""

    @classmethod
    def setUpClass(cls):
        cls.mdb = _TestDB.get_mdb()
        cls.config = gsxr1000_k5()

    def test_returns_list(self):
        result = get_category_upgrade_order(
            self.config,
            parts_repo=self.mdb.parts,
        )
        self.assertIsInstance(result, list)

    def test_entries_have_required_fields(self):
        result = get_category_upgrade_order(
            self.config,
            parts_repo=self.mdb.parts,
        )
        if result:
            entry = result[0]
            self.assertIn("rank", entry)
            self.assertIn("category", entry)
            self.assertIn("best_part", entry)
            self.assertIn("et_gain_s", entry)
            self.assertIn("price_inr", entry)
            self.assertIn("roi_score", entry)
            self.assertIn("reason", entry)

    def test_sorted_by_roi(self):
        result = get_category_upgrade_order(
            self.config,
            parts_repo=self.mdb.parts,
        )
        for i in range(1, len(result)):
            prev_roi = result[i - 1]["roi_score"]
            curr_roi = result[i]["roi_score"]
            # inf > any finite, so this must hold
            if not math.isinf(prev_roi) and not math.isinf(curr_roi):
                self.assertGreaterEqual(prev_roi, curr_roi)

    def test_ranks_sequential(self):
        result = get_category_upgrade_order(
            self.config,
            parts_repo=self.mdb.parts,
        )
        ranks = [e["rank"] for e in result]
        self.assertEqual(ranks, list(range(1, len(result) + 1)))

    def test_reasons_are_non_empty(self):
        result = get_category_upgrade_order(
            self.config,
            parts_repo=self.mdb.parts,
        )
        for entry in result:
            self.assertTrue(len(entry["reason"]) > 5)

    def test_profile_filtering_applies(self):
        all_result = get_category_upgrade_order(
            self.config,
            parts_repo=self.mdb.parts,
            profile=BuildProfile.ALL,
        )
        street_result = get_category_upgrade_order(
            self.config,
            parts_repo=self.mdb.parts,
            profile=BuildProfile.STREET_LEGAL,
        )
        # Street-legal might have fewer categories
        self.assertGreaterEqual(len(all_result), len(street_result))


if __name__ == "__main__":
    unittest.main()
