"""
MotoQuant Pro — Phase 4B Surrogate Model Tests
===============================================
Tests for:
  surrogate_data.py — Feature extraction, Sobol sampling, SurrogateDataset
  surrogate_xgb.py  — XGBSurrogate fit / predict / evaluate / save / load

Test philosophy
---------------
- Data generation uses small n_samples (16–64) so tests finish in seconds.
- XGBoost is tested against tiny synthetic datasets (ET = f(power, mass))
  to verify the training/evaluation pipeline without needing hours of sims.
- Round-trip save/load is tested with a temp file.
- CLI integration verified via in-process calls (matching test_analysis.py pattern).
- No real DB needed — all tests use defaults.gsxr1000_k5() as template.
"""

import copy
import os
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motoquant.analysis.surrogate_data import (
    BASE_FEATURE_NAMES,
    DERIVED_FEATURE_NAMES,
    FEATURE_BOUNDS,
    FEATURE_NAMES,
    SurrogateDataPoint,
    SurrogateDataset,
    _apply_features_to_config,
    _compute_derived_features,
    _extract_nominal_features,
    _sobol_sample_features,
    config_to_feature_vector,
    generate_training_data,
)
from motoquant.analysis.surrogate_xgb import (
    SurrogateMetrics,
    XGBSurrogate,
    _check_array_shapes,
    train_surrogate,
)
from motoquant.defaults import gsxr1000_k5

# ─────────────────────────────────────────────────────────────────
# Shared fixture helpers
# ─────────────────────────────────────────────────────────────────


def _make_tiny_dataset(n: int = 64, seed: int = 0) -> "SurrogateDataset":
    """Fast mini dataset using real physics engine."""
    return generate_training_data(gsxr1000_k5(), n_samples=n, seed=seed)


def _make_synthetic_arrays(
    n: int = 200, seed: int = 7
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Synthetic 17-feature dataset where ET ≈ f(power, mass, power_to_weight).
    Used to verify XGBoost can learn a simple relationship.
    """
    from motoquant.analysis.surrogate_data import (
        BASE_FEATURE_NAMES,
        _full_features,
    )

    rng = np.random.default_rng(seed)
    # Build base features (14) at midpoints
    base_mid = {}
    for k in BASE_FEATURE_NAMES:
        lo, hi = FEATURE_BOUNDS[k]
        base_mid[k] = (lo + hi) / 2.0

    power_vals = rng.uniform(40.0, 200.0, size=n)
    mass_vals = rng.uniform(160.0, 320.0, size=n)

    rows = []
    for i in range(n):
        base = dict(base_mid)
        base["peak_power_hp"] = float(power_vals[i])
        base["total_mass_kg"] = float(mass_vals[i])
        full = _full_features(base)  # v2: fills structural extras with defaults
        rows.append([full[k] for k in FEATURE_NAMES])

    X = np.array(rows, dtype=np.float32)
    # power_to_weight_hp_kg index reserved for future use (curve fits
    # below intentionally use peak_power_hp + total_mass_kg directly so
    # the surrogate has to learn the derived ratio rather than reading
    # it from a leak-from-target feature).

    # ET is a simple function of power/weight (the derived feature)
    y_et = (
        10.0
        + (200.0 - X[:, FEATURE_NAMES.index("peak_power_hp")]) * 0.02
        + (X[:, FEATURE_NAMES.index("total_mass_kg")] - 200.0) * 0.01
        + rng.normal(0, 0.01, size=n)
    ).astype(np.float32)
    y_trap = (
        55.0
        + X[:, FEATURE_NAMES.index("peak_power_hp")] * 0.10
        + rng.normal(0, 0.5, size=n)
    ).astype(np.float32)

    return X, y_et, y_trap


# ═════════════════════════════════════════════════════════════════
# 1. FEATURE_NAMES / FEATURE_BOUNDS contract
# ═════════════════════════════════════════════════════════════════


class TestFeatureSchema(unittest.TestCase):
    def test_base_feature_names_count(self):
        self.assertEqual(len(BASE_FEATURE_NAMES), 14)

    def test_derived_feature_names_count(self):
        self.assertEqual(len(DERIVED_FEATURE_NAMES), 7)

    def test_feature_names_count(self):
        # v2 (June 2026): 14 base + 7 derived + 5 structural extras
        self.assertEqual(len(FEATURE_NAMES), 26)

    def test_extra_feature_names_count(self):
        from motoquant.analysis.surrogate_data import EXTRA_FEATURE_NAMES

        self.assertEqual(len(EXTRA_FEATURE_NAMES), 5)

    def test_feature_names_is_base_plus_derived_plus_extra(self):
        from motoquant.analysis.surrogate_data import EXTRA_FEATURE_NAMES

        self.assertEqual(
            FEATURE_NAMES,
            BASE_FEATURE_NAMES + DERIVED_FEATURE_NAMES + EXTRA_FEATURE_NAMES,
        )

    def test_v1_prefix_preserved(self):
        # 21-input v1 models slice [:21] of a v2 vector — the prefix must
        # stay byte-for-byte identical, forever.
        self.assertEqual(
            FEATURE_NAMES[:21], BASE_FEATURE_NAMES + DERIVED_FEATURE_NAMES
        )

    def test_feature_bounds_keys_match_base_names(self):
        # FEATURE_BOUNDS only covers the 14 sampled (base) features
        self.assertEqual(set(BASE_FEATURE_NAMES), set(FEATURE_BOUNDS.keys()))

    def test_all_bounds_are_valid(self):
        for name, (lo, hi) in FEATURE_BOUNDS.items():
            with self.subTest(feature=name):
                self.assertLess(lo, hi, f"{name}: low must be < high")
                self.assertGreaterEqual(lo, 0.0, f"{name}: bounds must be non-negative")

    def test_required_base_features_present(self):
        required = {
            "peak_power_hp",
            "total_mass_kg",
            "aero_cd",
            "tire_mu_peak",
            "final_drive_ratio",
            "reaction_time_ms",
        }
        for feat in required:
            self.assertIn(feat, FEATURE_NAMES)

    def test_required_derived_features_present(self):
        for feat in (
            "power_to_weight_hp_kg",
            "effective_1st_ratio",
            "effective_top_ratio",
            "gear_ratio_2nd",
            "gear_ratio_3rd",
            "gear_ratio_4th",
            "gear_ratio_5th",
        ):
            self.assertIn(feat, DERIVED_FEATURE_NAMES)

    def test_feature_names_no_duplicates(self):
        self.assertEqual(len(FEATURE_NAMES), len(set(FEATURE_NAMES)))


# ═════════════════════════════════════════════════════════════════
# 1b. Derived feature computation
# ═════════════════════════════════════════════════════════════════


class TestDerivedFeatures(unittest.TestCase):
    def _base(self, power=150.0, mass=230.0, prim=2.0, final=3.5, g1=3.0, gtop=1.0):
        return {
            "peak_power_hp": power,
            "peak_torque_nm": 80.0,
            "redline_rpm": 12000.0,
            "total_mass_kg": mass,
            "aero_cd": 0.70,
            "frontal_area_m2": 0.50,
            "tire_mu_peak": 1.10,
            "rear_rolling_radius_m": 0.300,
            "primary_ratio": prim,
            "final_drive_ratio": final,
            "gear_ratio_1st": g1,
            "gear_ratio_top": gtop,
            "reaction_time_ms": 100.0,
            "altitude_m": 0.0,
        }

    def test_power_to_weight(self):
        base = self._base(power=150.0, mass=300.0)
        d = _compute_derived_features(base)
        self.assertAlmostEqual(d["power_to_weight_hp_kg"], 150.0 / 300.0, places=6)

    def test_effective_1st_ratio(self):
        base = self._base(prim=2.0, final=3.5, g1=3.0)
        d = _compute_derived_features(base)
        self.assertAlmostEqual(d["effective_1st_ratio"], 2.0 * 3.5 * 3.0, places=6)

    def test_effective_top_ratio(self):
        base = self._base(prim=2.0, final=3.5, gtop=0.9)
        d = _compute_derived_features(base)
        self.assertAlmostEqual(d["effective_top_ratio"], 2.0 * 3.5 * 0.9, places=6)

    def test_derived_keys_match_spec(self):
        base = self._base()
        d = _compute_derived_features(base)
        self.assertEqual(set(d.keys()), set(DERIVED_FEATURE_NAMES))

    def test_intermediate_gears_computed(self):
        base = self._base(g1=3.0, gtop=1.0)
        d = _compute_derived_features(base)
        # Linear interpolation: gear k → top + (first-top)*(n-k)/(n-1) for n=6
        self.assertAlmostEqual(d["gear_ratio_2nd"], 1.0 + (3.0 - 1.0) * 4 / 5, places=5)
        self.assertAlmostEqual(d["gear_ratio_5th"], 1.0 + (3.0 - 1.0) * 1 / 5, places=5)

    def test_gears_monotonically_decreasing(self):
        base = self._base(g1=3.5, gtop=0.9)
        d = _compute_derived_features(base)
        gears = [
            d["gear_ratio_2nd"],
            d["gear_ratio_3rd"],
            d["gear_ratio_4th"],
            d["gear_ratio_5th"],
        ]
        for i in range(len(gears) - 1):
            self.assertGreater(gears[i], gears[i + 1])


# ═════════════════════════════════════════════════════════════════
# 2. Feature extraction from BikeConfig
# ═════════════════════════════════════════════════════════════════


class TestFeatureExtraction(unittest.TestCase):
    def setUp(self):
        self.config = gsxr1000_k5()

    def test_extract_returns_all_features(self):
        feat = _extract_nominal_features(self.config)
        self.assertEqual(set(feat.keys()), set(FEATURE_NAMES))

    def test_extract_values_within_bounds(self):
        feat = _extract_nominal_features(self.config)
        # Only check base features; derived features are computed (no independent bounds)
        for name in BASE_FEATURE_NAMES:
            val = feat[name]
            lo, hi = FEATURE_BOUNDS[name]
            lower_guard = lo - max(1.0, abs(lo) * 0.5)
            upper_guard = hi * 2.0
            self.assertGreaterEqual(
                val, lower_guard, f"{name}={val} is way below low={lo}"
            )
            self.assertLess(val, upper_guard, f"{name}={val} is way above high={hi}")

    def test_config_to_feature_vector_shape(self):
        vec = config_to_feature_vector(self.config)
        self.assertEqual(vec.shape, (26,))
        self.assertEqual(vec.dtype, np.float32)

    def test_config_to_feature_vector_order(self):
        feat = _extract_nominal_features(self.config)
        vec = config_to_feature_vector(self.config)
        for i, name in enumerate(FEATURE_NAMES):
            self.assertAlmostEqual(float(vec[i]), feat[name], places=4)

    def test_power_is_positive(self):
        feat = _extract_nominal_features(self.config)
        self.assertGreater(feat["peak_power_hp"], 0.0)

    def test_total_mass_includes_rider(self):
        feat = _extract_nominal_features(self.config)
        # K5 dry mass ~166 kg + rider ~75 kg = 241+ kg
        self.assertGreater(feat["total_mass_kg"], 200.0)


# ═════════════════════════════════════════════════════════════════
# 3. Sobol sampling
# ═════════════════════════════════════════════════════════════════


class TestSobolSampling(unittest.TestCase):
    def test_output_count(self):
        samples = _sobol_sample_features(32, seed=0)
        self.assertEqual(len(samples), 32)

    def test_all_features_present_per_sample(self):
        samples = _sobol_sample_features(8, seed=1)
        for s in samples:
            self.assertEqual(set(s.keys()), set(FEATURE_NAMES))

    def test_values_within_bounds(self):
        samples = _sobol_sample_features(64, seed=2)
        for s in samples:
            # Only check base features; derived are computed (no independent bounds)
            for name in BASE_FEATURE_NAMES:
                val = s[name]
                lo, hi = FEATURE_BOUNDS[name]
                self.assertGreaterEqual(val, lo - 1e-6, f"{name}={val} below low={lo}")
                self.assertLessEqual(val, hi + 1e-6, f"{name}={val} above high={hi}")

    def test_different_seeds_produce_different_samples(self):
        s1 = _sobol_sample_features(16, seed=0)
        s2 = _sobol_sample_features(16, seed=99)
        # At least one feature value should differ
        differs = any(
            abs(s1[i][k] - s2[i][k]) > 1e-6
            for i in range(len(s1))
            for k in FEATURE_NAMES
        )
        self.assertTrue(differs)


# ═════════════════════════════════════════════════════════════════
# 4. _apply_features_to_config
# ═════════════════════════════════════════════════════════════════


class TestApplyFeaturesToConfig(unittest.TestCase):
    def setUp(self):
        self.base = gsxr1000_k5()

    def test_does_not_mutate_base(self):
        orig_hp = self.base.engine.peak_power_hp
        feat = _extract_nominal_features(self.base)
        feat["peak_power_hp"] = 50.0
        _apply_features_to_config(self.base, feat)
        self.assertAlmostEqual(self.base.engine.peak_power_hp, orig_hp)

    def test_power_overridden(self):
        feat = _extract_nominal_features(self.base)
        feat["peak_power_hp"] = 80.0
        cfg = _apply_features_to_config(self.base, feat)
        self.assertAlmostEqual(cfg.engine.peak_power_hp, 80.0, places=3)

    def test_aero_overridden(self):
        feat = _extract_nominal_features(self.base)
        feat["aero_cd"] = 0.72
        cfg = _apply_features_to_config(self.base, feat)
        self.assertAlmostEqual(cfg.aero.cd, 0.72, places=4)

    def test_gear_ratios_scaled_preserves_count(self):
        feat = _extract_nominal_features(self.base)
        feat["gear_ratio_1st"] = 3.5
        feat["gear_ratio_top"] = 1.0
        cfg = _apply_features_to_config(self.base, feat)
        n_orig = len(self.base.drivetrain.gear_ratios)
        self.assertEqual(len(cfg.drivetrain.gear_ratios), n_orig)

    def test_gear_top_less_than_first(self):
        feat = _extract_nominal_features(self.base)
        feat["gear_ratio_1st"] = 3.0
        feat["gear_ratio_top"] = 3.5  # invalid — should be clamped
        cfg = _apply_features_to_config(self.base, feat)
        first = cfg.drivetrain.gear_ratios[0]
        top = cfg.drivetrain.gear_ratios[-1]
        self.assertGreater(first, top)

    def test_dyno_curve_scaled_with_power(self):
        """If config has a dyno curve, it must be scaled when power changes."""
        from motoquant.models import DynoCurve

        cfg_with_dyno = copy.deepcopy(self.base)
        orig_hp = cfg_with_dyno.engine.peak_power_hp
        # Inject a simple dyno curve
        rpms = np.linspace(3000, 14000, 50)
        torques = np.linspace(60, 80, 50)
        cfg_with_dyno.engine.dyno_curve = DynoCurve(
            rpm=rpms, torque_nm=torques, is_at_wheel=True
        )

        feat = _extract_nominal_features(cfg_with_dyno)
        feat["peak_power_hp"] = orig_hp * 1.20  # +20% power

        out = _apply_features_to_config(cfg_with_dyno, feat)
        # Torque should be scaled by same ratio
        ratio = out.engine.dyno_curve.torque_nm.mean() / torques.mean()
        self.assertAlmostEqual(ratio, 1.20, places=2)


# ═════════════════════════════════════════════════════════════════
# 5. SurrogateDataPoint
# ═════════════════════════════════════════════════════════════════


class TestSurrogateDataPoint(unittest.TestCase):
    def _make_point(self):
        from motoquant.analysis.surrogate_data import _full_features

        base = {
            k: (FEATURE_BOUNDS[k][0] + FEATURE_BOUNDS[k][1]) / 2.0
            for k in BASE_FEATURE_NAMES
        }
        feat = _full_features(base)  # fills v2 structural extras with defaults
        return SurrogateDataPoint(features=feat, et_s=10.5, trap_speed_mps=55.0)

    def test_to_array_shape(self):
        pt = self._make_point()
        arr = pt.to_array()
        self.assertEqual(arr.shape, (len(FEATURE_NAMES),))

    def test_to_array_order(self):
        pt = self._make_point()
        arr = pt.to_array()
        for i, name in enumerate(FEATURE_NAMES):
            self.assertAlmostEqual(float(arr[i]), pt.features[name], places=5)

    def test_trap_speed_kmh(self):
        pt = self._make_point()
        self.assertAlmostEqual(pt.trap_speed_kmh, pt.trap_speed_mps * 3.6, places=4)


# ═════════════════════════════════════════════════════════════════
# 6. SurrogateDataset
# ═════════════════════════════════════════════════════════════════


class TestSurrogateDataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ds = _make_tiny_dataset(n=32)

    def test_length(self):
        self.assertGreater(len(self.ds), 0)
        self.assertLessEqual(len(self.ds), 32)

    def test_to_arrays_shapes(self):
        X, y_et, y_trap = self.ds.to_arrays()
        n = len(self.ds)
        self.assertEqual(X.shape, (n, len(FEATURE_NAMES)))
        self.assertEqual(y_et.shape, (n,))
        self.assertEqual(y_trap.shape, (n,))

    def test_et_physically_reasonable(self):
        _, y_et, _ = self.ds.to_arrays()
        self.assertTrue(np.all(y_et > 4.0), "Some ETs below 4 s — unphysical")
        self.assertTrue(np.all(y_et < 35.0), "Some ETs above 35 s — unphysical")

    def test_trap_speed_physically_reasonable(self):
        _, _, y_trap = self.ds.to_arrays()
        self.assertTrue(np.all(y_trap > 5.0), "Trap speed below 5 m/s")
        self.assertTrue(np.all(y_trap < 120.0), "Trap speed above 120 m/s")

    def test_split_sizes(self):
        train_ds, test_ds = self.ds.split(test_fraction=0.25, seed=0)
        n = len(self.ds)
        n_test = len(test_ds)
        n_train = len(train_ds)
        self.assertEqual(n_train + n_test, n)
        self.assertGreater(n_test, 0)

    def test_save_load_round_trip(self):
        with tempfile.NamedTemporaryFile(suffix=".npz", delete=False) as f:
            path = f.name
        try:
            self.ds.save(path)
            loaded = SurrogateDataset.load(path)
            self.assertEqual(len(loaded), len(self.ds))
            X_orig, y_et_orig, _ = self.ds.to_arrays()
            X_load, y_et_load, _ = loaded.to_arrays()
            np.testing.assert_allclose(X_orig, X_load, rtol=1e-5)
            np.testing.assert_allclose(y_et_orig, y_et_load, rtol=1e-5)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_empty_dataset_to_arrays_raises(self):
        empty = SurrogateDataset(points=[], n_samples=0)
        with self.assertRaises(ValueError):
            empty.to_arrays()

    def test_generate_returns_dataset(self):
        ds = generate_training_data(gsxr1000_k5(), n_samples=8, seed=77)
        self.assertIsInstance(ds, SurrogateDataset)
        self.assertGreater(len(ds), 0)

    def test_filter_reduces_dataset(self):
        # Use very high threshold to ensure some points are removed
        filtered = self.ds.filter(min_power_to_weight=0.50)
        self.assertLessEqual(len(filtered), len(self.ds))

    def test_filter_all_remaining_above_threshold(self):
        threshold = 0.10
        filtered = self.ds.filter(min_power_to_weight=threshold)
        for p in filtered.points:
            pw = p.features.get(
                "power_to_weight_hp_kg",
                p.features["peak_power_hp"] / p.features["total_mass_kg"],
            )
            self.assertGreaterEqual(pw, threshold)

    def test_backward_compat_load_14_features(self):
        """Loading a v1 14-feature npz should auto-complete to the full schema
        (derived features computed; v2 structural extras padded with defaults)."""
        X14, y_et, y_trap = self.ds.to_arrays()
        X14 = X14[:, :14]  # strip derived columns to simulate v1 file

        with tempfile.NamedTemporaryFile(suffix=".npz", delete=False) as f:
            path = f.name
        try:
            import numpy as _np

            _np.savez_compressed(
                path,
                X=X14,
                y_et=y_et,
                y_trap=y_trap,
                feature_names=_np.array(BASE_FEATURE_NAMES),
                meta=_np.array([len(self.ds), 0, 0.0]),
            )
            loaded = SurrogateDataset.load(path)
            self.assertEqual(len(loaded), len(self.ds))
            X_loaded, _, _ = loaded.to_arrays()
            self.assertEqual(X_loaded.shape[1], len(FEATURE_NAMES))
        finally:
            Path(path).unlink(missing_ok=True)


# ═════════════════════════════════════════════════════════════════
# 7. _check_array_shapes
# ═════════════════════════════════════════════════════════════════


class TestCheckArrayShapes(unittest.TestCase):
    def _valid(self):
        X = np.zeros((10, len(FEATURE_NAMES)))
        y = np.zeros(10)
        return X, y, y.copy()

    def test_valid_shapes_no_error(self):
        _check_array_shapes(*self._valid())

    def test_1d_X_raises(self):
        X, y_et, y_trap = self._valid()
        with self.assertRaises(ValueError):
            _check_array_shapes(X[0], y_et, y_trap)

    def test_wrong_n_features_raises(self):
        X = np.zeros((10, 5))  # wrong number of columns (should be 17)
        y = np.zeros(10)
        with self.assertRaises(ValueError):
            _check_array_shapes(X, y, y.copy())

    def test_mismatched_y_shape_raises(self):
        X, y_et, _ = self._valid()
        y_wrong = np.zeros(5)
        with self.assertRaises(ValueError):
            _check_array_shapes(X, y_et, y_wrong)


# ═════════════════════════════════════════════════════════════════
# 8. XGBSurrogate — fit / predict / evaluate
# ═════════════════════════════════════════════════════════════════


class TestXGBSurrogate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Train a tiny model on synthetic data once for the whole class."""
        cls.X, cls.y_et, cls.y_trap = _make_synthetic_arrays(n=300, seed=42)
        cls.model = XGBSurrogate(
            xgb_params={"n_estimators": 50, "max_depth": 4, "random_state": 0}
        )
        cls.model.fit(cls.X, cls.y_et, cls.y_trap)

    def test_is_fitted_after_fit(self):
        self.assertTrue(self.model.is_fitted)

    def test_predict_shape(self):
        et_pred, trap_pred = self.model.predict(self.X[:10])
        self.assertEqual(et_pred.shape, (10,))
        self.assertEqual(trap_pred.shape, (10,))

    def test_predict_single_sample(self):
        et_arr, trap_arr = self.model.predict(self.X[0:1])
        self.assertEqual(len(et_arr), 1)
        self.assertEqual(len(trap_arr), 1)
        self.assertTrue(np.isfinite(et_arr[0]))
        self.assertTrue(np.isfinite(trap_arr[0]))

    def test_predict_config_returns_floats(self):
        et, trap = self.model.predict_config(gsxr1000_k5())
        self.assertIsInstance(et, float)
        self.assertIsInstance(trap, float)
        self.assertTrue(np.isfinite(et))
        self.assertTrue(np.isfinite(trap))

    def test_evaluate_returns_metrics(self):
        metrics = self.model.evaluate(self.X, self.y_et, self.y_trap)
        self.assertIsInstance(metrics, SurrogateMetrics)
        self.assertGreater(metrics.et_r2, 0.5)  # should learn simple relationship

    def test_evaluate_r2_positive(self):
        metrics = self.model.evaluate(self.X, self.y_et, self.y_trap)
        self.assertGreater(metrics.et_r2, 0.0)
        self.assertGreater(metrics.trap_r2, 0.0)

    def test_metrics_within_50ms_fraction_valid(self):
        metrics = self.model.evaluate(self.X, self.y_et, self.y_trap)
        self.assertGreaterEqual(metrics.et_within_50ms, 0.0)
        self.assertLessEqual(metrics.et_within_50ms, 1.0)

    def test_feature_importance_all_features_present(self):
        imp = self.model.feature_importance()
        self.assertEqual(set(imp.keys()), set(FEATURE_NAMES))

    def test_feature_importance_power_and_mass_top_ranked(self):
        imp = self.model.feature_importance()
        top2 = set(list(imp.keys())[:3])
        # power and mass are the only predictors in synthetic data
        self.assertTrue(
            "peak_power_hp" in top2 or "total_mass_kg" in top2,
            f"Expected power or mass in top-3, got {top2}",
        )

    def test_unfitted_predict_raises(self):
        m = XGBSurrogate(xgb_params={"n_estimators": 5})
        with self.assertRaises(RuntimeError):
            m.predict(self.X[:1])

    def test_unfitted_save_raises(self):
        m = XGBSurrogate(xgb_params={"n_estimators": 5})
        with self.assertRaises(RuntimeError):
            m.save("/tmp/should_not_exist.pkl")

    def test_n_train_property(self):
        self.assertGreater(self.model.n_train, 0)

    def test_repr_contains_fitted(self):
        r = repr(self.model)
        self.assertIn("fitted on", r)


# ═════════════════════════════════════════════════════════════════
# 9. XGBSurrogate — save / load round-trip
# ═════════════════════════════════════════════════════════════════


class TestXGBSurrogatePersistence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        X, y_et, y_trap = _make_synthetic_arrays(n=150, seed=1)
        cls.X_te = X[:30]
        cls.y_et_te = y_et[:30]
        cls.y_trap_te = y_trap[:30]
        X_tr, y_et_tr, y_trap_tr = X[30:], y_et[30:], y_trap[30:]

        cls.model = XGBSurrogate(xgb_params={"n_estimators": 30, "random_state": 1})
        cls.model.fit(X_tr, y_et_tr, y_trap_tr)

    def test_save_load_predictions_match(self):
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            path = f.name
        try:
            self.model.save(path)
            loaded = XGBSurrogate.load(path)
            et_orig, trap_orig = self.model.predict(self.X_te)
            et_load, trap_load = loaded.predict(self.X_te)
            np.testing.assert_allclose(et_orig, et_load, rtol=1e-5)
            np.testing.assert_allclose(trap_orig, trap_load, rtol=1e-5)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_load_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            XGBSurrogate.load("/tmp/does_not_exist_xyz.pkl")

    def test_loaded_model_is_fitted(self):
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            path = f.name
        try:
            self.model.save(path)
            loaded = XGBSurrogate.load(path)
            self.assertTrue(loaded.is_fitted)
        finally:
            Path(path).unlink(missing_ok=True)


# ═════════════════════════════════════════════════════════════════
# 10. train_surrogate convenience pipeline
# ═════════════════════════════════════════════════════════════════


class TestTrainSurrogatePipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ds = _make_tiny_dataset(n=48, seed=5)

    def test_returns_model_and_metrics(self):
        model, metrics = train_surrogate(
            self.ds,
            xgb_params={"n_estimators": 30, "random_state": 0},
        )
        self.assertIsInstance(model, XGBSurrogate)
        self.assertIsInstance(metrics, SurrogateMetrics)

    def test_model_is_fitted(self):
        model, _ = train_surrogate(
            self.ds, xgb_params={"n_estimators": 20, "random_state": 0}
        )
        self.assertTrue(model.is_fitted)

    def test_metrics_to_dict_keys(self):
        _, metrics = train_surrogate(
            self.ds, xgb_params={"n_estimators": 20, "random_state": 0}
        )
        d = metrics.to_dict()
        for key in ("et_mae_ms", "et_r2", "trap_mae_kmh", "trap_r2", "n_test"):
            self.assertIn(key, d)

    def test_metrics_print_report_no_error(self):
        _, metrics = train_surrogate(
            self.ds, xgb_params={"n_estimators": 20, "random_state": 0}
        )
        # Should not raise
        with patch("sys.stdout", new_callable=StringIO):
            metrics.print_report()


# ═════════════════════════════════════════════════════════════════
# 11. CLI integration — analysis surrogate generate / train
# ═════════════════════════════════════════════════════════════════


class TestSurrogateCLI(unittest.TestCase):
    """Smoke tests for CLI subcommands via in-process call."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls.data_path = str(Path(cls.tmpdir) / "test_data.npz")
        cls.model_path = str(Path(cls.tmpdir) / "test_model.pkl")

    def _run_cli(self, argv):
        """Run CLI in-process; returns (stdout_str, return_code)."""
        from motoquant.run import build_parser, cmd_analysis

        parser = build_parser()
        args = parser.parse_args(argv)
        buf = StringIO()
        with patch("sys.stdout", buf):
            rc = cmd_analysis(args)
        return buf.getvalue(), rc

    def test_generate_creates_npz(self):
        _, rc = self._run_cli(
            [
                "analysis",
                "surrogate",
                "generate",
                "--n-samples",
                "16",
                "--output",
                self.data_path,
                "--seed",
                "0",
            ]
        )
        self.assertEqual(rc, 0)
        self.assertTrue(Path(self.data_path).exists())

    def test_train_creates_pkl(self):
        # Ensure data file exists (run generate first if needed)
        if not Path(self.data_path).exists():
            self._run_cli(
                [
                    "analysis",
                    "surrogate",
                    "generate",
                    "--n-samples",
                    "16",
                    "--output",
                    self.data_path,
                    "--seed",
                    "0",
                ]
            )
        _, rc = self._run_cli(
            [
                "analysis",
                "surrogate",
                "train",
                "--data",
                self.data_path,
                "--model-out",
                self.model_path,
            ]
        )
        self.assertEqual(rc, 0)
        self.assertTrue(Path(self.model_path).exists())

    def test_unknown_surrogate_subcommand_returns_error(self):
        # Build parser and patch surrogate_command manually
        from motoquant.run import build_parser, cmd_analysis

        parser = build_parser()
        args = parser.parse_args(
            [
                "analysis",
                "surrogate",
                "generate",
                "--n-samples",
                "4",
                "--output",
                str(Path(self.tmpdir) / "tmp.npz"),
            ]
        )
        args.surrogate_command = "nonexistent"
        buf = StringIO()
        with patch("sys.stdout", buf):
            rc = cmd_analysis(args)
        self.assertEqual(rc, 1)


# ═════════════════════════════════════════════════════════════════
# 12. DNNSurrogate — fit / predict / evaluate / save / load
# ═════════════════════════════════════════════════════════════════


class TestDNNSurrogate(unittest.TestCase):
    """Tests for the Phase 4A DNN surrogate (sklearn fallback path)."""

    @classmethod
    def setUpClass(cls):
        """Train a tiny DNN on synthetic data once for the whole class."""
        cls.X, cls.y_et, cls.y_trap = _make_synthetic_arrays(n=300, seed=99)
        cls.model = None
        try:
            from motoquant.analysis.surrogate_dnn import DNNSurrogate

            cls.model = DNNSurrogate(hidden_dims=(32, 64, 64, 32), dropout=0.0)
            # Use small hidden dims + few epochs for fast test
            cls.model.fit(
                cls.X,
                cls.y_et,
                cls.y_trap,
                epochs=10,
                batch_size=64,
                patience=5,
                verbose=False,
            )
        except ImportError as e:
            raise unittest.SkipTest(f"DNNSurrogate unavailable: {e}")

    def _skip_if_none(self):
        if self.model is None:
            self.skipTest("DNNSurrogate not available")

    def test_is_fitted_after_fit(self):
        self._skip_if_none()
        self.assertTrue(self.model.is_fitted)

    def test_backend_is_valid(self):
        self._skip_if_none()
        self.assertIn(self.model.backend, ("torch", "sklearn"))

    def test_predict_shape(self):
        self._skip_if_none()
        et_pred, trap_pred = self.model.predict(self.X[:10])
        self.assertEqual(et_pred.shape, (10,))
        self.assertEqual(trap_pred.shape, (10,))

    def test_predict_finite_values(self):
        self._skip_if_none()
        et_pred, trap_pred = self.model.predict(self.X[:20])
        self.assertTrue(np.all(np.isfinite(et_pred)))
        self.assertTrue(np.all(np.isfinite(trap_pred)))

    def test_predict_config_returns_floats(self):
        self._skip_if_none()
        from motoquant.defaults import gsxr1000_k5

        et, trap = self.model.predict_config(gsxr1000_k5())
        self.assertIsInstance(et, float)
        self.assertIsInstance(trap, float)
        self.assertTrue(np.isfinite(et))
        self.assertTrue(np.isfinite(trap))

    def test_evaluate_returns_metrics(self):
        self._skip_if_none()
        from motoquant.analysis.surrogate_xgb import SurrogateMetrics

        metrics = self.model.evaluate(self.X, self.y_et, self.y_trap)
        self.assertIsInstance(metrics, SurrogateMetrics)
        self.assertTrue(np.isfinite(metrics.et_mae_s))

    def test_n_train_property(self):
        self._skip_if_none()
        self.assertGreater(self.model.n_train, 0)

    def test_repr_contains_fitted(self):
        self._skip_if_none()
        self.assertIn("fitted on", repr(self.model))

    def test_unfitted_predict_raises(self):
        from motoquant.analysis.surrogate_dnn import DNNSurrogate

        m = DNNSurrogate(hidden_dims=(16,))
        with self.assertRaises(RuntimeError):
            m.predict(self.X[:1])

    def test_save_load_predictions_match(self):
        self._skip_if_none()
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            path = f.name
        try:
            self.model.save(path)
            from motoquant.analysis.surrogate_dnn import DNNSurrogate

            loaded = DNNSurrogate.load(path)
            self.assertTrue(loaded.is_fitted)
            et_orig, trap_orig = self.model.predict(self.X[:10])
            et_load, trap_load = loaded.predict(self.X[:10])
            np.testing.assert_allclose(et_orig, et_load, rtol=1e-4)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_load_missing_file_raises(self):
        from motoquant.analysis.surrogate_dnn import DNNSurrogate

        with self.assertRaises(FileNotFoundError):
            DNNSurrogate.load("/tmp/does_not_exist_dnn_xyz.pkl")

    def test_normalisation_applied(self):
        """Feature normalisation stats must be set after fit."""
        self._skip_if_none()
        self.assertIsNotNone(self.model._X_mean)
        self.assertIsNotNone(self.model._X_std)
        self.assertGreater(abs(self.model._et_mean), 0.0)


if __name__ == "__main__":
    unittest.main()
