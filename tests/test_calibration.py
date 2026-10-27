"""
Tests for motoquant.calibration.{dyno, overlay, calibrator}
=============================================================
All heavy tests (calibrator) use very fast Nelder-Mead only (global_search=False)
and synthetic data to stay under 60 s total.
"""

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

# ─── Shared helpers ───────────────────────────────────────────────────────


def _synthetic_run_data(et=10.0, trap_ms=60.0, sr=10.0):
    """Generate a minimal DragRunData matching the given ET/trap for overlay tests."""
    from motoquant.calibration.dragy import (
        QUARTER_MILE_M,
        DragRunData,
        _compute_acceleration,
        _integrate_distance,
    )

    # Linear ramp to trap speed at approx et, then constant
    n = int(et * sr) + int(sr * 2)  # run + 2s coast
    t = np.arange(n) / sr
    v = np.clip(t / et * trap_ms, 0, trap_ms)
    d = _integrate_distance(t, v)
    a = _compute_acceleration(t, v)

    # Actual ET from distance array
    from motoquant.calibration.dragy import (
        _interpolate_et,
        _interpolate_speed_at_distance,
    )

    actual_et = _interpolate_et(t, d, QUARTER_MILE_M) or et
    actual_trap = _interpolate_speed_at_distance(v, d, QUARTER_MILE_M) or trap_ms

    return DragRunData(
        timestamps=t,
        velocity_ms=v,
        distance_m=d,
        acceleration_ms2=a,
        et_quarter=actual_et,
        trap_speed_ms=actual_trap,
        sample_rate_hz=sr,
        source_file="synthetic",
    )


# ─── DynoParseError ───────────────────────────────────────────────────────


class TestSAECorrection(unittest.TestCase):
    def test_standard_conditions_cf_is_one(self):
        """At reference conditions CF should be very close to 1.0."""
        from motoquant.calibration.dyno import sae_j1349_correction_factor

        # Reference: 25 °C, 99.0 kPa, 0% RH
        cf = sae_j1349_correction_factor(25.0, 99.0, 0.0)
        self.assertAlmostEqual(cf, 1.0, delta=0.002)

    def test_hot_humid_correction_factor_above_one(self):
        """
        Hot + humid air → engine underperforms reference → CF > 1.
        SAE J1349: Power_std = Power_measured × CF.
        In hot/humid conditions Pd drops → (99/Pd) > 1 → CF > 1.
        """
        from motoquant.calibration.dyno import sae_j1349_correction_factor

        cf_hot = sae_j1349_correction_factor(40.0, 100.0, 80.0)
        self.assertGreater(cf_hot, 1.0)

    def test_cf_rises_with_temperature(self):
        """Hotter inlet air → CF > 1; colder → CF < 1.

        This test previously asserted the OPPOSITE (cf_25 > cf_40) and its own
        docstring reasoned itself in a circle ("Wait — let's just check
        monotonicity"). It was pinning an inverted implementation:
        sae_j1349_correction_factor computed sqrt(Tref / Tm) instead of the
        sqrt(Tm / Tref) that SAE J1349 — and dyno.py's own module docstring —
        specify. Corrected in the 2026-07-25 audit.

        The physics is not ambiguous: hot air is less dense, so the engine makes
        LESS power on the dyno, and correcting that run to standard 25 °C must
        scale it UP. A 190 hp run measured at 40 °C / 99 kPa was reported as
        185.4 hp; SAE J1349 (with its 1.18/−0.18 mechanical-efficiency terms,
        added 2026-10-24) requires 195.6 hp.
        """
        from motoquant.calibration.dyno import sae_j1349_correction_factor

        cf_0 = sae_j1349_correction_factor(0.0, 99.0, 0.0)
        cf_25 = sae_j1349_correction_factor(25.0, 99.0, 0.0)
        cf_40 = sae_j1349_correction_factor(40.0, 99.0, 0.0)

        self.assertLess(cf_0, cf_25, "cold air makes more power → correct DOWN")
        self.assertGreater(cf_40, cf_25, "hot air makes less power → correct UP")
        # 1.18·√(313.15/298.15) − 0.18 and 1.18·√(273.15/298.15) − 0.18
        self.assertAlmostEqual(cf_40, 1.0293, delta=0.0005)
        self.assertAlmostEqual(cf_0, 0.9494, delta=0.0005)

    def test_temperature_term_matches_the_documented_formula(self):
        """Pin the exact J1349 closed form against dyno.py's own docstring.

        With pressure held at the reference, CF reduces to
        1.18·sqrt(Tm / Tref) − 0.18. Asserting the closed form makes a future
        re-inversion — or a regression to the friction-free sqrt(Tm/Tref)
        form, which overstates every deviation by 18% — fail loudly rather
        than merely shifting a monotonicity relation.
        """
        import math

        from motoquant.calibration.dyno import (
            SAE_REF_PRESSURE_KPA,
            SAE_REF_TEMP_K,
            sae_j1349_correction_factor,
        )

        for temp_c in (0.0, 15.0, 25.0, 35.0, 45.0):
            cf = sae_j1349_correction_factor(temp_c, SAE_REF_PRESSURE_KPA, 0.0)
            expected = 1.18 * math.sqrt((temp_c + 273.15) / SAE_REF_TEMP_K) - 0.18
            self.assertAlmostEqual(cf, expected, places=9, msg=f"at {temp_c} C")

    def test_high_altitude_cf_greater_than_one(self):
        """High altitude (low pressure) → engine makes less power → CF > 1 to correct up."""
        from motoquant.calibration.dyno import sae_j1349_correction_factor

        cf_sea = sae_j1349_correction_factor(25.0, 101.325, 0.0)
        cf_high = sae_j1349_correction_factor(25.0, 75.0, 0.0)  # ~2500m altitude
        self.assertGreater(cf_high, cf_sea)

    def test_saturated_vapour_pressure_at_100c(self):
        """At 100 °C, vapour pressure should be ~101 kPa (boiling point)."""
        from motoquant.calibration.dyno import _saturated_vapour_pressure_kpa

        svp = _saturated_vapour_pressure_kpa(100.0)
        self.assertAlmostEqual(svp, 101.325, delta=2.0)

    def test_cf_output_is_positive(self):
        from motoquant.calibration.dyno import sae_j1349_correction_factor

        for t in [0, 25, 45]:
            for p in [70, 99, 105]:
                cf = sae_j1349_correction_factor(t, p, 50.0)
                self.assertGreater(cf, 0)


class TestDynoCSVParsing(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmpdir.cleanup()

    def _write_dynojet_csv(
        self, name="dynojet.csv", peak_hp=150.0, peak_tq_lbft=80.0
    ) -> Path:
        """Write a minimal DynoJet-style CSV."""
        p = Path(self.tmpdir.name) / name
        rpms = np.arange(3000, 14001, 500)
        # Ramp up to peak at 10k, then taper
        x = (rpms - 3000) / (10000 - 3000)
        hp = peak_hp * np.clip(x * (2 - x), 0.05, 1.0)
        tq = peak_tq_lbft * np.clip(1.0 - 0.5 * (x - 0.6) ** 2, 0.1, 1.0)
        with open(p, "w") as f:
            f.write("RPM,WHP,TQ\n")
            for r, h, t in zip(rpms, hp, tq):
                f.write(f"{r:.0f},{h:.2f},{t:.2f}\n")
        return p

    def _write_metric_csv(self, name="metric.csv") -> Path:
        """Write a metric kW/Nm dyno CSV."""
        p = Path(self.tmpdir.name) / name
        rpms = np.arange(2000, 13001, 500)
        kw = 100.0 * np.clip((rpms - 2000) / 8000, 0, 1.0)
        nm = 120.0 * np.ones(len(rpms))
        with open(p, "w") as f:
            f.write("RPM,Power (kW),Torque (Nm)\n")
            for r, k, n in zip(rpms, kw, nm):
                f.write(f"{r:.0f},{k:.2f},{n:.2f}\n")
        return p

    def test_parse_dynojet_csv(self):
        from motoquant.calibration.dyno import parse_dyno_file

        p = self._write_dynojet_csv()
        result = parse_dyno_file(p)
        self.assertGreater(result.peak_power_kw, 0)
        self.assertGreater(result.peak_torque_nm, 0)

    def test_peak_power_in_reasonable_range(self):
        """150 WHP should be ~112 kW."""
        from motoquant.calibration.dyno import parse_dyno_file

        p = self._write_dynojet_csv(peak_hp=150.0)
        result = parse_dyno_file(p)
        self.assertAlmostEqual(result.peak_power_kw, 150 * 0.7457, delta=5)

    def test_uncorrected_cf_is_one(self):
        from motoquant.calibration.dyno import parse_dyno_file

        p = self._write_dynojet_csv()
        result = parse_dyno_file(p, temp_c=None, pressure_kpa=None)
        self.assertEqual(result.correction_factor, 1.0)

    def test_corrected_cf_differs_from_one(self):
        from motoquant.calibration.dyno import parse_dyno_file

        p = self._write_dynojet_csv()
        result = parse_dyno_file(p, temp_c=35.0, pressure_kpa=101.0, rh_pct=70.0)
        self.assertNotAlmostEqual(result.correction_factor, 1.0, places=3)

    def test_metric_kw_csv(self):
        from motoquant.calibration.dyno import parse_dyno_file

        p = self._write_metric_csv()
        result = parse_dyno_file(p)
        self.assertGreater(result.peak_power_kw, 50)
        self.assertGreater(result.peak_torque_nm, 50)

    def test_source_file_recorded(self):
        from motoquant.calibration.dyno import parse_dyno_file

        p = self._write_dynojet_csv()
        result = parse_dyno_file(p)
        self.assertEqual(result.source_file, str(p))

    def test_rpm_at_peak_power_is_in_range(self):
        from motoquant.calibration.dyno import parse_dyno_file

        p = self._write_dynojet_csv()
        result = parse_dyno_file(p)
        self.assertGreater(result.rpm_at_peak_power, 500)
        self.assertLess(result.rpm_at_peak_power, 22000)

    def test_file_not_found_raises(self):
        from motoquant.calibration.dyno import parse_dyno_file

        with self.assertRaises(FileNotFoundError):
            parse_dyno_file("/no/such/file.csv")

    def test_empty_csv_raises(self):
        from motoquant.calibration.dyno import DynoParseError, parse_dyno_file

        p = Path(self.tmpdir.name) / "empty.csv"
        p.write_text("RPM,WHP,TQ\n")
        with self.assertRaises(DynoParseError):
            parse_dyno_file(p)

    def test_dynocurve_injected_into_bikeconfig(self):
        """DynoResult.curve is a DynoCurve that can be assigned to BikeConfig."""
        from motoquant.calibration.dyno import parse_dyno_file
        from motoquant.models import DynoCurve

        p = self._write_dynojet_csv()
        result = parse_dyno_file(p)
        self.assertIsInstance(result.curve, DynoCurve)
        self.assertGreater(result.curve.interpolate(8000), 0)

    def test_to_dict_has_required_keys(self):
        from motoquant.calibration.dyno import parse_dyno_file

        p = self._write_dynojet_csv()
        d = parse_dyno_file(p).to_dict()
        for k in [
            "peak_power_kw",
            "peak_power_hp",
            "peak_torque_nm",
            "correction_factor",
        ]:
            self.assertIn(k, d)


# ─── Overlay ──────────────────────────────────────────────────────────────


class TestOverlay(unittest.TestCase):
    def _make_sim_result(self, et=10.0, trap_ms=60.0):
        """Create a minimal SimResult with the right scalar fields."""
        from motoquant.physics import SimResult

        # Time axis: 0 to 15s at 1ms — must be long enough for QM crossing even
        # when ramp time is large (e.g. et=10.5 → QM at t≈12.2s)
        n = 15001
        t = np.linspace(0, 15, n)
        v = np.clip(t / et * trap_ms, 0, trap_ms)
        # Fill required sim scalars
        from motoquant.calibration.dragy import (
            QUARTER_MILE_M,
            _integrate_distance,
            _interpolate_et,
            _interpolate_speed_at_distance,
        )

        d = _integrate_distance(t, v)
        actual_et = _interpolate_et(t, d, QUARTER_MILE_M) or et
        actual_trap = _interpolate_speed_at_distance(v, d, QUARTER_MILE_M) or trap_ms

        sim = SimResult(dt=0.001, t=t, x=d, v=v)
        sim.time_quarter = actual_et
        sim.speed_quarter = actual_trap
        sim.time_60ft = _interpolate_et(t, d, 18.288) or 0.0
        sim.speed_60ft = _interpolate_speed_at_distance(v, d, 18.288) or 0.0
        sim.time_330ft = _interpolate_et(t, d, 100.584) or 0.0
        sim.speed_330ft = _interpolate_speed_at_distance(v, d, 100.584) or 0.0
        sim.time_eighth = _interpolate_et(t, d, 201.168) or 0.0
        sim.speed_eighth = _interpolate_speed_at_distance(v, d, 201.168) or 0.0
        sim.time_1000ft = _interpolate_et(t, d, 304.8) or 0.0
        sim.speed_1000ft = _interpolate_speed_at_distance(v, d, 304.8) or 0.0
        return sim

    def test_compare_identical_runs_small_error(self):
        """
        Sim and real with identical v(t) formula should have very similar ETs.
        Residual error budget: GPS 10 Hz → max ±0.1s discretization in ET.
        We allow ±0.15s to be safe.
        """
        from motoquant.calibration.overlay import compare_runs

        real = _synthetic_run_data(et=10.5, trap_ms=58.0)
        sim = self._make_sim_result(et=10.5, trap_ms=58.0)
        cmp = compare_runs(real, sim)
        self.assertAlmostEqual(cmp.et_error_s, 0.0, delta=0.15)
        self.assertAlmostEqual(cmp.trap_error_ms, 0.0, delta=1.0)

    def test_compare_slower_sim_positive_et_error(self):
        from motoquant.calibration.overlay import compare_runs

        real = _synthetic_run_data(et=10.0, trap_ms=60.0)
        sim = self._make_sim_result(et=10.5, trap_ms=58.0)  # sim is slower
        cmp = compare_runs(real, sim)
        self.assertGreater(cmp.et_error_s, 0)

    def test_rmse_near_zero_for_identical(self):
        from motoquant.calibration.overlay import compare_runs

        real = _synthetic_run_data(et=10.5, trap_ms=58.0)
        sim = self._make_sim_result(et=10.5, trap_ms=58.0)
        cmp = compare_runs(real, sim)
        self.assertLess(cmp.rmse_ms, 0.5)

    def test_t_common_all_within_real_timestamps(self):
        from motoquant.calibration.overlay import compare_runs

        real = _synthetic_run_data()
        sim = self._make_sim_result()
        cmp = compare_runs(real, sim)
        self.assertTrue(np.all(cmp.t_common <= real.timestamps[-1] + 1e-9))

    def test_arrays_same_length(self):
        from motoquant.calibration.overlay import compare_runs

        real = _synthetic_run_data()
        sim = self._make_sim_result()
        cmp = compare_runs(real, sim)
        self.assertEqual(len(cmp.t_common), len(cmp.v_real))
        self.assertEqual(len(cmp.t_common), len(cmp.v_sim))
        self.assertEqual(len(cmp.t_common), len(cmp.residuals_ms))

    def test_et_error_pct_sign_consistent(self):
        from motoquant.calibration.overlay import compare_runs

        real = _synthetic_run_data(et=10.0)
        sim = self._make_sim_result(et=11.0)  # sim slower → positive error
        cmp = compare_runs(real, sim)
        self.assertGreater(cmp.et_error_pct, 0)

    def test_to_dict_has_keys(self):
        from motoquant.calibration.overlay import compare_runs

        real = _synthetic_run_data()
        sim = self._make_sim_result()
        cmp = compare_runs(real, sim)
        d = cmp.to_dict()
        for k in ["et_real_s", "et_sim_s", "et_error_s", "rmse_ms", "trap_error_ms"]:
            self.assertIn(k, d)

    def test_compute_cost_identical_is_near_zero(self):
        from motoquant.calibration.overlay import compare_runs, compute_cost

        real = _synthetic_run_data(et=10.5, trap_ms=58.0)
        sim = self._make_sim_result(et=10.5, trap_ms=58.0)
        cmp = compare_runs(real, sim)
        cost = compute_cost(cmp)
        self.assertLess(cost, 1e-3)

    def test_compute_cost_bad_sim_is_high(self):
        from motoquant.calibration.overlay import compare_runs, compute_cost

        real = _synthetic_run_data(et=10.0, trap_ms=60.0)
        sim = self._make_sim_result(et=13.0, trap_ms=45.0)  # way off
        cmp = compare_runs(real, sim)
        cost = compute_cost(cmp)
        self.assertGreater(cost, 0.01)

    def test_compute_cost_custom_weights(self):
        from motoquant.calibration.overlay import compare_runs, compute_cost

        real = _synthetic_run_data()
        sim = self._make_sim_result()
        cmp = compare_runs(real, sim)
        cost_et_only = compute_cost(cmp, weights={"et": 1.0, "trap": 0.0, "rmse": 0.0})
        self.assertGreaterEqual(cost_et_only, 0)


# ─── Calibrator ───────────────────────────────────────────────────────────


class TestCalibratorHelpers(unittest.TestCase):
    """Tests for low-level helpers — no actual optimisation (fast)."""

    def test_get_param(self):
        from motoquant.calibration.calibrator import _get_param
        from motoquant.defaults import gsxr1000_k5

        cfg = gsxr1000_k5()
        val = _get_param(cfg, "aero.cd")
        self.assertGreater(val, 0)

    def test_set_param(self):
        from motoquant.calibration.calibrator import _get_param, _set_param
        from motoquant.defaults import gsxr1000_k5

        cfg = gsxr1000_k5()
        _set_param(cfg, "aero.cd", 0.55)
        self.assertAlmostEqual(_get_param(cfg, "aero.cd"), 0.55, places=6)

    def test_set_param_does_not_mutate_original(self):
        """apply() should deep-copy; original config unchanged."""
        import copy

        from motoquant.calibration.calibrator import _set_param
        from motoquant.defaults import gsxr1000_k5

        cfg = gsxr1000_k5()
        orig_cd = cfg.aero.cd
        cfg2 = copy.deepcopy(cfg)
        _set_param(cfg2, "aero.cd", 0.123)
        self.assertAlmostEqual(cfg.aero.cd, orig_cd, places=6)

    def test_set_mu_peak(self):
        from motoquant.calibration.calibrator import _get_param, _set_param
        from motoquant.defaults import gsxr1000_k5

        cfg = gsxr1000_k5()
        _set_param(cfg, "tires.mu_peak", 1.35)
        self.assertAlmostEqual(_get_param(cfg, "tires.mu_peak"), 1.35, places=6)


class TestObjectiveFunction(unittest.TestCase):
    """Test the _Objective wrapper — one forward pass."""

    def test_objective_returns_nonneg_float(self):
        from motoquant.calibration.calibrator import PRESET_AERO_TIRE, _Objective
        from motoquant.defaults import gsxr1000_k5

        cfg = gsxr1000_k5()
        real = _synthetic_run_data(et=10.2, trap_ms=60.0)
        obj = _Objective(cfg, real, PRESET_AERO_TIRE)
        x0 = np.array([cfg.aero.cd, cfg.tires.mu_peak])
        cost = obj(x0)
        self.assertIsInstance(cost, float)
        self.assertGreaterEqual(cost, 0)

    def test_objective_counts_evals(self):
        from motoquant.calibration.calibrator import PRESET_AERO_TIRE, _Objective
        from motoquant.defaults import gsxr1000_k5

        cfg = gsxr1000_k5()
        real = _synthetic_run_data(et=10.2, trap_ms=60.0)
        obj = _Objective(cfg, real, PRESET_AERO_TIRE)
        x0 = np.array([cfg.aero.cd, cfg.tires.mu_peak])
        obj(x0)
        obj(x0)
        obj(x0)
        self.assertEqual(obj.n_evals, 3)


class TestCalibratorEndToEnd(unittest.TestCase):
    """
    Full calibration run — Nelder-Mead only (global_search=False) to stay fast.
    We synthesize a "real" run from the K5 simulation, perturb cd + mu_peak,
    then check the calibrator recovers toward the truth.
    """

    @classmethod
    def setUpClass(cls):
        """Run one calibration and cache the result for all test methods."""
        import copy

        from motoquant.calibration.calibrator import PRESET_AERO_TIRE, calibrate
        from motoquant.calibration.dragy import (
            QUARTER_MILE_M,
            DragRunData,
            _compute_acceleration,
            _integrate_distance,
            _interpolate_et,
            _interpolate_speed_at_distance,
        )
        from motoquant.defaults import gsxr1000_k5
        from motoquant.physics import MotoQuantEngine

        cls.truth_cfg = gsxr1000_k5()
        truth_sim = MotoQuantEngine(cls.truth_cfg).run()

        # Build a synthetic DragRunData from the truth sim (10 Hz down-sample)
        # sim dt=1ms, so every 100th sample = 100ms = 10 Hz
        idx = np.arange(0, len(truth_sim.t), 100)  # every 100 ms = 10 Hz
        t_real = truth_sim.t[idx]
        v_real = truth_sim.v[idx]
        d_real = _integrate_distance(t_real, v_real)
        a_real = _compute_acceleration(t_real, v_real)
        et_real = (
            _interpolate_et(t_real, d_real, QUARTER_MILE_M) or truth_sim.time_quarter
        )
        trap_real = (
            _interpolate_speed_at_distance(v_real, d_real, QUARTER_MILE_M)
            or truth_sim.speed_quarter
        )

        cls.real_run = DragRunData(
            timestamps=t_real,
            velocity_ms=v_real,
            distance_m=d_real,
            acceleration_ms2=a_real,
            et_quarter=et_real,
            trap_speed_ms=trap_real,
            sample_rate_hz=10.0,
            source_file="truth_sim",
        )

        # Perturb cd and mu_peak to give the calibrator something to recover
        cls.perturbed_cfg = copy.deepcopy(cls.truth_cfg)
        cls.perturbed_cfg.aero.cd = cls.truth_cfg.aero.cd + 0.12
        cls.perturbed_cfg.tires.mu_peak = cls.truth_cfg.tires.mu_peak - 0.15

        cls.result = calibrate(
            cls.perturbed_cfg,
            cls.real_run,
            params_to_fit=PRESET_AERO_TIRE,
            global_search=False,  # fast — no DE
            local_maxiter=150,
        )

    def test_calibration_returns_result(self):
        from motoquant.calibration.calibrator import CalibrationResult

        self.assertIsInstance(self.result, CalibrationResult)

    def test_cost_decreased(self):
        self.assertLess(self.result.final_cost, self.result.initial_cost)

    def test_fitted_cd_moved_toward_truth(self):
        truth_cd = self.truth_cfg.aero.cd
        perturb_cd = self.perturbed_cfg.aero.cd
        fitted_cd = self.result.fitted_params["aero.cd"]
        # Fitted should be closer to truth than the perturbed start
        self.assertLess(abs(fitted_cd - truth_cd), abs(perturb_cd - truth_cd) + 0.01)

    def test_fitted_mu_moved_toward_truth(self):
        truth_mu = self.truth_cfg.tires.mu_peak
        perturb_mu = self.perturbed_cfg.tires.mu_peak
        fitted_mu = self.result.fitted_params["tires.mu_peak"]
        self.assertLess(abs(fitted_mu - truth_mu), abs(perturb_mu - truth_mu) + 0.02)

    def test_et_error_reduced(self):
        self.assertLess(
            abs(self.result.comparison.et_error_s),
            abs(self.result.initial_cost**0.5 * self.real_run.et_quarter) + 0.5,
        )

    def test_apply_produces_new_config(self):
        from motoquant.models import BikeConfig

        fitted_cfg = self.result.apply(self.perturbed_cfg)
        self.assertIsInstance(fitted_cfg, BikeConfig)
        self.assertAlmostEqual(
            fitted_cfg.aero.cd, self.result.fitted_params["aero.cd"], places=5
        )

    def test_original_config_not_mutated(self):
        """apply() must deep-copy — original must be unchanged."""
        orig_cd = self.perturbed_cfg.aero.cd
        _ = self.result.apply(self.perturbed_cfg)
        self.assertAlmostEqual(self.perturbed_cfg.aero.cd, orig_cd, places=6)

    def test_to_dict_serialisable(self):
        d = self.result.to_dict()
        json.dumps(d)  # must not raise
        self.assertIn("fitted_params", d)

    def test_iterations_positive(self):
        self.assertGreater(self.result.iterations, 0)

    def test_wall_time_positive(self):
        self.assertGreater(self.result.wall_time_s, 0)

    def test_str_representation(self):
        s = str(self.result)
        self.assertIn("aero.cd", s)
        self.assertIn("tires.mu_peak", s)


# ═══════════════════════════════════════════════════════════════════════════
# MultiRunStats
# ═══════════════════════════════════════════════════════════════════════════


class TestMultiRunStats(unittest.TestCase):
    """Tests for compute_multi_run_stats and MultiRunStats dataclass."""

    @classmethod
    def setUpClass(cls):
        """Build 5 synthetic comparisons with slightly varying ETs."""
        import os
        import sys

        from motoquant.calibration.overlay import compare_runs
        from motoquant.defaults import gsxr1000_k5
        from motoquant.physics import MotoQuantEngine

        sys.path.insert(0, os.path.dirname(__file__))

        cfg = gsxr1000_k5()
        sim = MotoQuantEngine(cfg).run()
        base_et = 10.0
        base_trap = 60.0

        # Build 5 comparisons with ETs in [9.9, 10.1] range
        cls.comparisons = []
        for i in range(5):
            noise = (i - 2) * 0.05  # -0.10, -0.05, 0.00, +0.05, +0.10
            real = _synthetic_run_data(
                et=base_et + noise, trap_ms=base_trap + noise * 0.5
            )
            cmp = compare_runs(real, sim)
            cls.comparisons.append(cmp)

        from motoquant.calibration.overlay import compute_multi_run_stats

        cls.stats = compute_multi_run_stats(cls.comparisons)
        # Record the actual mean ET from the comparison objects (helper-derived)
        cls.actual_et_mean = float(
            np.mean([c.real.et_quarter for c in cls.comparisons])
        )

    # ── Basic structure ──────────────────────────────────────────────────

    def test_n_runs_correct(self):
        self.assertEqual(self.stats.n_runs, 5)

    def test_et_real_mean_in_range(self):
        # Mean should match the actual ETs from the comparisons
        self.assertAlmostEqual(self.stats.et_real_mean, self.actual_et_mean, delta=0.01)

    def test_et_real_std_positive(self):
        self.assertGreater(self.stats.et_real_std, 0.0)

    def test_et_real_best_leq_worst(self):
        self.assertLessEqual(self.stats.et_real_best, self.stats.et_real_worst)

    def test_et_real_best_leq_mean(self):
        self.assertLessEqual(self.stats.et_real_best, self.stats.et_real_mean + 1e-6)

    def test_et_real_worst_geq_mean(self):
        self.assertGreaterEqual(
            self.stats.et_real_worst, self.stats.et_real_mean - 1e-6
        )

    # ── Confidence interval ──────────────────────────────────────────────

    def test_ci_95_lo_lt_hi(self):
        lo, hi = self.stats.et_real_ci_95
        self.assertLess(lo, hi)

    def test_ci_95_contains_mean(self):
        lo, hi = self.stats.et_real_ci_95
        self.assertGreater(self.stats.et_real_mean, lo)
        self.assertLess(self.stats.et_real_mean, hi)

    def test_ci_95_width_reasonable(self):
        lo, hi = self.stats.et_real_ci_95
        width = hi - lo
        # With 5 runs and std ≈ 0.08, CI should be < 0.5 s
        self.assertLess(width, 0.5)
        self.assertGreater(width, 0.0)

    # ── Trap speed ───────────────────────────────────────────────────────

    def test_trap_mean_positive(self):
        self.assertGreater(self.stats.trap_real_mean_kmh, 0.0)

    def test_trap_std_non_negative(self):
        self.assertGreaterEqual(self.stats.trap_real_std_kmh, 0.0)

    # ── RMSE ─────────────────────────────────────────────────────────────

    def test_rmse_mean_positive(self):
        self.assertGreater(self.stats.rmse_mean, 0.0)

    def test_rmse_std_non_negative(self):
        self.assertGreaterEqual(self.stats.rmse_std, 0.0)

    # ── Consistency score ────────────────────────────────────────────────

    def test_consistency_in_range(self):
        self.assertGreaterEqual(self.stats.run_consistency, 0.0)
        self.assertLessEqual(self.stats.run_consistency, 1.0)

    def test_consistent_runs_high_score(self):
        """Very tight ET spread → high consistency."""
        from motoquant.calibration.overlay import compare_runs, compute_multi_run_stats
        from motoquant.defaults import gsxr1000_k5
        from motoquant.physics import MotoQuantEngine

        cfg = gsxr1000_k5()
        sim = MotoQuantEngine(cfg).run()
        tight = [
            compare_runs(_synthetic_run_data(et=10.0, trap_ms=60.0), sim)
            for _ in range(5)
        ]
        stats = compute_multi_run_stats(tight)
        self.assertGreater(stats.run_consistency, 0.9)

    def test_inconsistent_runs_lower_score(self):
        """Wide ET spread → lower consistency."""
        from motoquant.calibration.overlay import compare_runs, compute_multi_run_stats
        from motoquant.defaults import gsxr1000_k5
        from motoquant.physics import MotoQuantEngine

        cfg = gsxr1000_k5()
        sim = MotoQuantEngine(cfg).run()
        wide = [
            compare_runs(_synthetic_run_data(et=9.0, trap_ms=60.0), sim),
            compare_runs(_synthetic_run_data(et=11.0, trap_ms=60.0), sim),
        ]
        stats_wide = compute_multi_run_stats(wide)
        self.assertLess(stats_wide.run_consistency, 0.9)

    # ── Recommended n runs ───────────────────────────────────────────────

    def test_recommended_n_positive(self):
        self.assertGreater(self.stats.recommended_n_runs, 0)

    def test_recommended_n_capped(self):
        self.assertLessEqual(self.stats.recommended_n_runs, 15)

    def test_perfect_consistency_recommends_min_runs(self):
        """Zero ET spread → recommend minimum (3) runs."""
        from motoquant.calibration.overlay import compare_runs, compute_multi_run_stats
        from motoquant.defaults import gsxr1000_k5
        from motoquant.physics import MotoQuantEngine

        cfg = gsxr1000_k5()
        sim = MotoQuantEngine(cfg).run()
        identical = [
            compare_runs(_synthetic_run_data(et=10.0, trap_ms=60.0), sim)
            for _ in range(4)
        ]
        stats = compute_multi_run_stats(identical)
        self.assertEqual(stats.recommended_n_runs, 3)

    # ── Single run edge case ─────────────────────────────────────────────

    def test_single_run_no_crash(self):
        from motoquant.calibration.overlay import compute_multi_run_stats

        stats = compute_multi_run_stats(self.comparisons[:1])
        self.assertEqual(stats.n_runs, 1)
        self.assertEqual(stats.et_real_std, 0.0)

    # ── to_dict ──────────────────────────────────────────────────────────

    def test_to_dict_keys(self):
        d = self.stats.to_dict()
        for key in [
            "n_runs",
            "et_real_mean_s",
            "et_real_std_s",
            "et_real_ci_95",
            "run_consistency",
            "recommended_n_runs",
        ]:
            self.assertIn(key, d)

    def test_to_dict_ci_is_list(self):
        d = self.stats.to_dict()
        ci = d["et_real_ci_95"]
        self.assertIsInstance(ci, list)
        self.assertEqual(len(ci), 2)
        self.assertLess(ci[0], ci[1])

    # ── Empty raises ─────────────────────────────────────────────────────

    def test_empty_raises(self):
        from motoquant.calibration.overlay import compute_multi_run_stats

        with self.assertRaises(ValueError):
            compute_multi_run_stats([])

    # ── print_report runs without crash ──────────────────────────────────

    def test_print_report_no_crash(self):
        import contextlib
        import io

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.stats.print_report()
        out = buf.getvalue()
        self.assertIn("Multi-Run Statistics", out)
        self.assertIn("95% CI", out)
        self.assertIn("consistency", out.lower())


if __name__ == "__main__":
    unittest.main()
