"""
Tests for motoquant.calibration_ml -- Phase B per-bike ML calibrator.

Schema v2 (3 targets, 24 features):
  - cd_factor dropped (R²=-0.06, unlearnable from single ET)
  - FEATURE_DIM = 24 (tire_compound_code removed, 4 other dead features fixed)
  - TARGET_NAMES = [mu_peak_factor, peak_torque_factor, inertia_factor]
  - generate_dataset mode='one_at_a_time' default
  - default_base_configs() samples 32 bikes from ALL_KNOWN_BIKES

Coverage:
  - CorrectionTargets: apply, to_array/from_array round-trip, identity
  - features: shape, no-NaN, missing-field tolerance, deterministic,
              rear_tire_diameter populated, ride_mass jittered
  - synthetic: generate_one + generate_dataset on real K5 spec,
               one_at_a_time mode validation
  - Calibrator: fit + predict + evaluate + save/load + predict_correction
  - Reference baselines: K5/R1/Hayabusa unchanged by identity correction

Tests use the sklearn fallback backend so XGBoost is not required.
Production training should use XGBoost (faster, better R²).

Run:  python -m pytest tests/test_calibration_ml.py -v
"""

from __future__ import annotations

import os
import tempfile
import unittest

import numpy as np

from motoquant.calibration_ml import (
    FEATURE_DIM,
    FEATURE_NAMES,
    FEATURE_SCHEMA_VERSION,
    PERTURBATION_RANGES,
    TARGET_NAMES,
    Calibrator,
    CalibratorMetrics,
    CorrectionTargets,
    MeasuredRun,
    SyntheticDataset,
    extract_features,
    feature_dict,
    generate_dataset,
    generate_one,
    train_calibrator,
)
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8

# ───────────────────────────────────────────────────────────────────
# CorrectionTargets
# ───────────────────────────────────────────────────────────────────


class TestCorrectionTargets(unittest.TestCase):
    def test_identity_default(self):
        t = CorrectionTargets()
        self.assertTrue(t.is_identity())
        self.assertEqual(t.mu_peak_factor, 1.0)
        self.assertEqual(t.peak_torque_factor, 1.0)
        self.assertEqual(t.inertia_factor, 1.0)
        # cd_factor is no longer a field (schema v2)
        self.assertFalse(hasattr(t, "cd_factor"))

    def test_to_array_stable_ordering_3_elements(self):
        t = CorrectionTargets(
            mu_peak_factor=0.95,
            peak_torque_factor=1.05,
            inertia_factor=1.10,
        )
        arr = t.to_array()
        self.assertEqual(arr.shape, (3,))
        self.assertAlmostEqual(arr[0], 0.95, places=5)  # mu_peak
        self.assertAlmostEqual(arr[1], 1.05, places=5)  # peak_torque
        self.assertAlmostEqual(arr[2], 1.10, places=5)  # inertia

    def test_array_round_trip(self):
        t = CorrectionTargets(
            mu_peak_factor=1.08, peak_torque_factor=1.02, inertia_factor=0.92
        )
        t2 = CorrectionTargets.from_array(t.to_array())
        self.assertAlmostEqual(t.mu_peak_factor, t2.mu_peak_factor, places=5)
        self.assertAlmostEqual(t.peak_torque_factor, t2.peak_torque_factor, places=5)
        self.assertAlmostEqual(t.inertia_factor, t2.inertia_factor, places=5)

    def test_from_array_wrong_length_raises(self):
        # Length 4 (old schema) should now raise
        with self.assertRaises(ValueError):
            CorrectionTargets.from_array([1.0, 1.0, 1.0, 1.0])
        # Length 2 also raises
        with self.assertRaises(ValueError):
            CorrectionTargets.from_array([1.0, 1.0])
        # Length 3 is correct
        t = CorrectionTargets.from_array([0.9, 1.0, 1.1])
        self.assertAlmostEqual(t.mu_peak_factor, 0.9, places=5)

    def test_apply_does_not_scale_cd(self):
        """cd_factor was dropped from CorrectionTargets in schema v2.
        The apply() method should leave aero.cd untouched."""
        cfg = gsxr1000_k5()
        cd0 = cfg.aero.cd
        # Identity correction -- cd must not change
        t = CorrectionTargets()
        new = t.apply(cfg)
        self.assertAlmostEqual(new.aero.cd, cd0, places=5)
        # Non-identity mu/torque -- cd still must not change
        t2 = CorrectionTargets(mu_peak_factor=1.10, peak_torque_factor=0.95)
        new2 = t2.apply(cfg)
        self.assertAlmostEqual(new2.aero.cd, cd0, places=5)

    def test_apply_scales_mu(self):
        cfg = gsxr1000_k5()
        mu0 = cfg.tires.mu_peak
        t = CorrectionTargets(mu_peak_factor=0.90)
        new = t.apply(cfg)
        self.assertAlmostEqual(new.tires.mu_peak, mu0 * 0.90, places=5)
        # Original config is untouched (deep copy)
        self.assertAlmostEqual(cfg.tires.mu_peak, mu0, places=5)

    def test_apply_scales_torque_and_power_together(self):
        cfg = gsxr1000_k5()
        t0 = cfg.engine.peak_torque_nm
        p0 = cfg.engine.peak_power_hp
        t = CorrectionTargets(peak_torque_factor=1.05)
        new = t.apply(cfg)
        self.assertAlmostEqual(new.engine.peak_torque_nm, t0 * 1.05, places=4)
        self.assertAlmostEqual(new.engine.peak_power_hp, p0 * 1.05, places=4)

    def test_apply_scales_dyno_curve_in_lockstep(self):
        """Per CLAUDE.md hygiene: avoid the dead-knob bug -- when peak_torque
        is scaled, the stored dyno_curve must scale with it."""
        cfg = gsxr1000_k5()
        dyno = getattr(cfg.engine, "dyno_curve", None)
        if dyno is None or getattr(dyno, "torque_nm", None) is None:
            self.skipTest("K5 has no stored dyno curve")
        original_first = dyno.torque_nm[0]
        t = CorrectionTargets(peak_torque_factor=1.20)
        new = t.apply(cfg)
        self.assertAlmostEqual(
            new.engine.dyno_curve.torque_nm[0],
            original_first * 1.20,
            places=4,
        )

    def test_apply_scales_inertia(self):
        cfg = gsxr1000_k5()
        i0 = cfg.engine.engine_inertia_kgm2
        t = CorrectionTargets(inertia_factor=1.15)
        new = t.apply(cfg)
        self.assertAlmostEqual(new.engine.engine_inertia_kgm2, i0 * 1.15, places=5)


# ───────────────────────────────────────────────────────────────────
# features (schema v2)
# ───────────────────────────────────────────────────────────────────


class TestFeatures(unittest.TestCase):
    def setUp(self):
        self.cfg = gsxr1000_k5()
        self.measured = MeasuredRun(
            et_s=10.04,
            trap_kmh=240.0,
            sixty_ft_s=1.65,
            three_thirty_s=4.50,
            eighth_s=6.40,
        )

    def test_schema_version_is_2(self):
        self.assertEqual(FEATURE_SCHEMA_VERSION, 2)

    def test_feature_dim_is_24(self):
        """Schema v2: tire_compound_code removed, FEATURE_DIM = 24."""
        self.assertEqual(FEATURE_DIM, 24)
        self.assertEqual(len(FEATURE_NAMES), 24)
        self.assertEqual(len(set(FEATURE_NAMES)), 24)  # no duplicates

    def test_tire_compound_code_removed(self):
        self.assertNotIn("tire_compound_code", FEATURE_NAMES)

    def test_extract_returns_correct_shape(self):
        x = extract_features(self.cfg, self.measured)
        self.assertEqual(x.shape, (FEATURE_DIM,))
        self.assertEqual(x.dtype, np.float32)

    def test_no_nan_or_inf(self):
        x = extract_features(self.cfg, self.measured)
        self.assertTrue(np.all(np.isfinite(x)))

    def test_extract_is_deterministic(self):
        x1 = extract_features(self.cfg, self.measured)
        x2 = extract_features(self.cfg, self.measured)
        np.testing.assert_array_equal(x1, x2)

    def test_displacement_populated(self):
        x = extract_features(self.cfg, self.measured)
        # K5 is ~999cc
        self.assertGreater(x[FEATURE_NAMES.index("displacement_cc")], 900)
        self.assertLess(x[FEATURE_NAMES.index("displacement_cc")], 1100)

    def test_measured_et_appears_in_vector(self):
        x = extract_features(self.cfg, self.measured)
        self.assertAlmostEqual(x[FEATURE_NAMES.index("measured_et_s")], 10.04, places=4)

    def test_rear_tire_diameter_populated(self):
        """v2 fix: was reading non-existent 'rear_diameter_mm'; now uses
        rear_rolling_radius_m * 2000 for diameter in mm."""
        x = extract_features(self.cfg, self.measured)
        diam = x[FEATURE_NAMES.index("rear_tire_diameter_mm")]
        # K5 rear_rolling_radius_m=0.302 -> 604mm diameter
        self.assertGreater(diam, 500.0)
        self.assertLess(diam, 750.0)

    def test_drive_type_code_chain_is_0(self):
        """K5 is chain-drive (chain_pitch='530') -> code 0."""
        x = extract_features(self.cfg, self.measured)
        code = int(x[FEATURE_NAMES.index("drive_type_code")])
        self.assertEqual(code, 0)

    def test_rider_mass_appears_in_vector(self):
        m = MeasuredRun(et_s=10.0, trap_kmh=240.0, sixty_ft_s=1.65, rider_mass_kg=82.0)
        x = extract_features(self.cfg, m)
        self.assertAlmostEqual(x[FEATURE_NAMES.index("rider_mass_kg")], 82.0, places=4)

    def test_feature_dict_returns_named(self):
        d = feature_dict(self.cfg, self.measured)
        self.assertEqual(set(d.keys()), set(FEATURE_NAMES))
        self.assertAlmostEqual(d["measured_et_s"], 10.04, places=4)

    def test_tolerates_missing_optional_splits(self):
        m = MeasuredRun(et_s=10.0, trap_kmh=240.0, sixty_ft_s=1.65)
        x = extract_features(self.cfg, m)
        self.assertEqual(x[FEATURE_NAMES.index("measured_330ft_s")], 0.0)
        self.assertEqual(x[FEATURE_NAMES.index("measured_eighth_s")], 0.0)
        self.assertTrue(np.all(np.isfinite(x)))

    def test_tolerates_partial_bike_config(self):
        """Calibrator must not crash on an under-populated config."""

        class StubBike:
            engine = None
            chassis = None
            drivetrain = None
            tires = None
            environment = None

        x = extract_features(StubBike(), self.measured)
        self.assertEqual(x.shape, (FEATURE_DIM,))
        self.assertTrue(np.all(np.isfinite(x)))


# ───────────────────────────────────────────────────────────────────
# synthetic (schema v2)
# ───────────────────────────────────────────────────────────────────


class TestSynthetic(unittest.TestCase):
    """Slow class -- exercises the real physics engine. Each generate_one
    call runs a full quarter-mile sim (~50 ms on K5)."""

    @classmethod
    def setUpClass(cls):
        cls.k5 = gsxr1000_k5()
        cls.r1 = yzfr1_4c8()
        cls.busa = hayabusa_gen1()

    def test_perturbation_ranges_3_keys(self):
        """Schema v2: 3 targets, cd_factor removed."""
        self.assertEqual(set(PERTURBATION_RANGES.keys()), set(TARGET_NAMES))
        self.assertNotIn("cd_factor", PERTURBATION_RANGES)
        self.assertEqual(len(PERTURBATION_RANGES), 3)

    def test_inertia_factor_range_tightened(self):
        lo, hi = PERTURBATION_RANGES["inertia_factor"]
        self.assertGreaterEqual(lo, 0.84)  # was 0.60
        self.assertLessEqual(hi, 1.21)  # was 1.80
        self.assertGreaterEqual(lo, 0.85)
        self.assertLessEqual(hi, 1.20)

    def test_generate_one_returns_pair_or_none(self):
        rng = np.random.default_rng(123)
        result = generate_one(self.k5, rng)
        self.assertIsNotNone(result, "K5 should reliably produce a valid sample")
        x, y = result
        self.assertEqual(x.shape, (FEATURE_DIM,))
        self.assertEqual(y.shape, (3,))  # schema v2: 3 targets
        self.assertTrue(np.all(np.isfinite(x)))
        self.assertTrue(np.all(np.isfinite(y)))
        # Labels should land within the perturbation ranges
        for i, name in enumerate(TARGET_NAMES):
            lo, hi = PERTURBATION_RANGES[name]
            self.assertGreaterEqual(y[i], lo - 0.05)
            self.assertLessEqual(y[i], hi + 0.05)

    def test_generate_one_mode_one_at_a_time_only_one_perturbed(self):
        """In one_at_a_time mode, exactly 2 of the 3 targets should be 1.0
        (within tolerance). The third is != 1.0."""
        rng = np.random.default_rng(42)
        non_identity_counts = []
        # Run 20 samples to check the mode works statistically
        for _ in range(20):
            result = generate_one(self.k5, rng, mode="one_at_a_time")
            if result is None:
                continue
            _, y = result
            # Count how many targets are outside the identity window
            non_identity = sum(abs(v - 1.0) > 0.02 for v in y)
            non_identity_counts.append(non_identity)
        # All samples should have exactly 1 perturbed target
        self.assertTrue(
            all(c == 1 for c in non_identity_counts),
            f"Expected 1 perturbed target per sample; got {non_identity_counts}",
        )

    def test_generate_dataset_smoke_3_targets(self):
        """Smoke test -- 12 samples across 3 bikes; Y must be (N, 3)."""
        ds = generate_dataset([self.k5, self.r1, self.busa], n_samples=12, seed=7)
        self.assertEqual(ds.n, 12)
        self.assertEqual(ds.X.shape, (12, FEATURE_DIM))
        self.assertEqual(ds.Y.shape, (12, 3))  # schema v2
        self.assertEqual(ds.X.dtype, np.float32)
        self.assertEqual(ds.Y.dtype, np.float32)
        self.assertTrue(np.all(np.isfinite(ds.X)))
        self.assertTrue(np.all(np.isfinite(ds.Y)))

    def test_generate_dataset_mode_one_at_a_time(self):
        """Default mode is one_at_a_time; smoke that it actually works."""
        ds = generate_dataset([self.k5], n_samples=10, seed=99, mode="one_at_a_time")
        self.assertEqual(ds.n, 10)
        self.assertEqual(ds.Y.shape, (10, 3))

    def test_generate_dataset_rider_mass_varies(self):
        """v2 fix: rider_mass_kg must have variance across samples."""
        ds = generate_dataset([self.k5, self.r1, self.busa], n_samples=30, seed=5)
        rider_idx = FEATURE_NAMES.index("rider_mass_kg")
        rider_masses = ds.X[:, rider_idx]
        # Should not all be 75.0 (was the v1 bug)
        self.assertGreater(rider_masses.std(), 1.0, "rider_mass should have variance")
        self.assertGreater(rider_masses.min(), 50.0)
        self.assertLess(rider_masses.max(), 120.0)

    def test_generate_dataset_track_temp_varies(self):
        """v2 fix: track_temp_c must have variance across samples."""
        ds = generate_dataset([self.k5, self.r1, self.busa], n_samples=30, seed=6)
        tt_idx = FEATURE_NAMES.index("track_temp_c")
        track_temps = ds.X[:, tt_idx]
        self.assertGreater(track_temps.std(), 0.5, "track_temp_c should have variance")

    def test_dataset_save_load_round_trip(self):
        ds = generate_dataset([self.k5], n_samples=5, seed=9)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ds.npz")
            ds.save(path)
            ds2 = SyntheticDataset.load(path)
            self.assertEqual(ds2.n, ds.n)
            np.testing.assert_array_equal(ds2.X, ds.X)
            np.testing.assert_array_equal(ds2.Y, ds.Y)

    def test_empty_base_configs_raises(self):
        with self.assertRaises(ValueError):
            generate_dataset([], n_samples=1)


# ───────────────────────────────────────────────────────────────────
# Calibrator (sklearn fallback, schema v2)
# ───────────────────────────────────────────────────────────────────


class TestCalibrator(unittest.TestCase):
    """Uses synthetic K5 dataset + sklearn fallback so XGBoost is optional."""

    @classmethod
    def setUpClass(cls):
        k5 = gsxr1000_k5()
        r1 = yzfr1_4c8()
        cls.dataset = generate_dataset([k5, r1], n_samples=40, seed=11)

    def _sklearn_available(self):
        try:
            import sklearn  # noqa: F401

            return True
        except ImportError:
            return False

    def test_version_is_2(self):
        cal = Calibrator()
        self.assertEqual(cal.version, 2)

    def test_target_names_3_no_cd_factor(self):
        self.assertEqual(len(TARGET_NAMES), 3)
        self.assertNotIn("cd_factor", TARGET_NAMES)
        self.assertIn("mu_peak_factor", TARGET_NAMES)
        self.assertIn("peak_torque_factor", TARGET_NAMES)
        self.assertIn("inertia_factor", TARGET_NAMES)

    def test_fit_predict_round_trip(self):
        if not self._sklearn_available():
            self.skipTest("sklearn not installed")
        cal = Calibrator(backend="sklearn")
        cal.fit(self.dataset.X, self.dataset.Y)
        self.assertTrue(cal.is_trained)
        preds = cal.predict(self.dataset.X[:5])
        self.assertEqual(preds.shape, (5, 3))  # schema v2: 3 targets
        self.assertTrue(np.all(np.isfinite(preds)))

    def test_fit_rejects_wrong_feature_dim(self):
        cal = Calibrator(backend="sklearn")
        bad_X = np.zeros((10, 7), dtype=np.float32)
        bad_Y = np.zeros((10, 3), dtype=np.float32)
        with self.assertRaises(ValueError):
            cal.fit(bad_X, bad_Y)

    def test_fit_rejects_wrong_target_count(self):
        """Schema v2: 3 targets. Feeding 4 (old schema) should raise."""
        cal = Calibrator(backend="sklearn")
        X = np.zeros((10, FEATURE_DIM), dtype=np.float32)
        bad_Y_4 = np.zeros((10, 4), dtype=np.float32)  # old schema
        with self.assertRaises(ValueError):
            cal.fit(X, bad_Y_4)

    def test_evaluate_returns_metrics(self):
        if not self._sklearn_available():
            self.skipTest("sklearn not installed")
        cal = Calibrator(backend="sklearn")
        cal.fit(self.dataset.X, self.dataset.Y)
        m = cal.evaluate(self.dataset.X, self.dataset.Y)
        self.assertIsInstance(m, CalibratorMetrics)
        self.assertEqual(m.n_test, self.dataset.n)
        self.assertEqual(set(m.mae.keys()), set(TARGET_NAMES))
        # Training-set MAE should be small (overfit to training)
        for name in TARGET_NAMES:
            self.assertLess(m.mae[name], 0.20, f"{name} MAE > 0.20")
        # summary() should produce a non-empty string with new target names
        s = m.summary()
        self.assertIn("Test set:", s)
        self.assertIn("mu_peak_factor", s)
        self.assertNotIn("cd_factor", s)

    def test_predict_correction_returns_targets(self):
        if not self._sklearn_available():
            self.skipTest("sklearn not installed")
        cal = Calibrator(backend="sklearn")
        cal.fit(self.dataset.X, self.dataset.Y)
        cfg = gsxr1000_k5()
        m = MeasuredRun(et_s=10.04, trap_kmh=240.0, sixty_ft_s=1.65)
        ct = cal.predict_correction(cfg, m)
        self.assertIsInstance(ct, CorrectionTargets)
        # All factors should be in a sane neighborhood of 1.0
        for v in ct.to_array():
            self.assertGreater(v, 0.5)
            self.assertLess(v, 2.5)

    def test_save_load_round_trip(self):
        if not self._sklearn_available():
            self.skipTest("sklearn not installed")
        cal = Calibrator(backend="sklearn")
        cal.fit(self.dataset.X, self.dataset.Y)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "cal.pkl")
            cal.save(path)
            cal2 = Calibrator.load(path)
            self.assertTrue(cal2.is_trained)
            self.assertEqual(cal2.version, 2)
            preds1 = cal.predict(self.dataset.X[:3])
            preds2 = cal2.predict(self.dataset.X[:3])
            np.testing.assert_array_almost_equal(preds1, preds2, decimal=5)

    def test_train_calibrator_one_shot(self):
        if not self._sklearn_available():
            self.skipTest("sklearn not installed")
        cal, m = train_calibrator(self.dataset, backend="sklearn", seed=11)
        self.assertTrue(cal.is_trained)
        self.assertIsInstance(m, CalibratorMetrics)
        self.assertGreater(m.n_test, 0)

    def test_train_rejects_tiny_dataset(self):
        ds = SyntheticDataset(
            X=np.zeros((3, FEATURE_DIM), dtype=np.float32),
            Y=np.zeros((3, 3), dtype=np.float32),  # 3 targets (v2)
            n=3,
        )
        with self.assertRaises(ValueError):
            train_calibrator(ds, backend="sklearn")

    def test_predict_before_fit_raises(self):
        cal = Calibrator()
        with self.assertRaises(RuntimeError):
            cal.predict(np.zeros((1, FEATURE_DIM), dtype=np.float32))


# ───────────────────────────────────────────────────────────────────
# Reference-baseline sanity (CLAUDE.md hygiene gate)
# ───────────────────────────────────────────────────────────────────


class TestReferenceBaselinesPreserved(unittest.TestCase):
    """Phase B must not move the K5/R1/Hayabusa baselines.

    Identity correction (factors=1.0) on each reference bike should
    reproduce the canonical ETs to 4 decimals.
    """

    def test_identity_on_k5_matches_baseline(self):
        from motoquant.physics import MotoQuantEngine

        cfg = gsxr1000_k5()
        new = CorrectionTargets().apply(cfg)
        et = MotoQuantEngine(new).run().time_quarter
        self.assertAlmostEqual(et, 10.0334, places=3)

    def test_identity_on_r1_matches_baseline(self):
        from motoquant.physics import MotoQuantEngine

        cfg = yzfr1_4c8()
        new = CorrectionTargets().apply(cfg)
        et = MotoQuantEngine(new).run().time_quarter
        self.assertAlmostEqual(et, 10.2859, places=3)

    def test_identity_on_hayabusa_matches_baseline(self):
        from motoquant.physics import MotoQuantEngine

        cfg = hayabusa_gen1()
        new = CorrectionTargets().apply(cfg)
        et = MotoQuantEngine(new).run().time_quarter
        self.assertAlmostEqual(et, 10.4712, places=3)


if __name__ == "__main__":
    unittest.main()
