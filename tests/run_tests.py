#!/usr/bin/env python3
"""
MotoQuant Pro — Standalone Test Runner
======================================
Uses unittest (stdlib) so no pip install needed.
Also importable by pytest if available.

Run: python tests/run_tests.py
"""

import os
import sys
import tempfile
import unittest

import numpy as np

# Ensure package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from motoquant.config_io import (
    config_from_dict,
    config_to_dict,
    load_config,
    save_config,
)
from motoquant.defaults import (
    aamby_valley_summer,
    aamby_valley_winter,
    gsxr1000_k5,
    hayabusa_gen1,
    yzfr1_4c8,
)
from motoquant.physics import QUARTER_MILE_M, G, MotoQuantEngine


def _run(config, distance=QUARTER_MILE_M):
    return MotoQuantEngine(config, dt=0.001).run(distance=distance, max_time=15.0)


# ═══════════════════════════════════════════
# QUARTER-MILE VALIDATION
# ═══════════════════════════════════════════


class TestQuarterMileValidation(unittest.TestCase):
    def test_k5_et(self):
        """K5 within ±0.10s of 9.97s."""
        r = _run(gsxr1000_k5())
        self.assertAlmostEqual(
            r.time_quarter, 9.97, delta=0.10, msg=f"K5 ET {r.time_quarter:.3f}s"
        )

    def test_k5_trap_speed(self):
        """K5 trap within ±10 km/h of 233."""
        r = _run(gsxr1000_k5())
        self.assertAlmostEqual(r.speed_quarter * 3.6, 233.0, delta=10.0)

    def test_r1_et(self):
        """R1 within ±0.10s of 10.3s."""
        r = _run(yzfr1_4c8())
        self.assertAlmostEqual(
            r.time_quarter, 10.3, delta=0.10, msg=f"R1 ET {r.time_quarter:.3f}s"
        )

    def test_busa_et_in_typical_range(self):
        """Busa within typical owner range 10.1-10.7s."""
        r = _run(hayabusa_gen1())
        self.assertGreater(r.time_quarter, 10.1)
        self.assertLess(r.time_quarter, 10.7, f"Busa ET {r.time_quarter:.3f}s")

    def test_k5_sixty_foot(self):
        """K5 60-ft within 1.8-2.1s."""
        r = _run(gsxr1000_k5())
        self.assertGreater(r.time_60ft, 1.8)
        self.assertLess(r.time_60ft, 2.1)

    def test_relative_order(self):
        """K5 < R1 < Busa in stock launch ET."""
        r_k5 = _run(gsxr1000_k5())
        r_r1 = _run(yzfr1_4c8())
        r_busa = _run(hayabusa_gen1())
        self.assertLess(r_k5.time_quarter, r_r1.time_quarter)
        self.assertLess(r_r1.time_quarter, r_busa.time_quarter)


# ═══════════════════════════════════════════
# ENVIRONMENTAL CORRECTION
# ═══════════════════════════════════════════


class TestEnvironment(unittest.TestCase):
    def test_aamby_winter_penalty(self):
        """Winter Aamby adds 0.05-0.25s penalty."""
        cfg_sl = gsxr1000_k5()
        cfg_aw = gsxr1000_k5()
        aamby_valley_winter(cfg_aw)
        penalty = _run(cfg_aw).time_quarter - _run(cfg_sl).time_quarter
        self.assertGreater(penalty, 0.05)
        self.assertLess(penalty, 0.25)

    def test_summer_worse_than_winter(self):
        """Summer hotter/humid → slower."""
        cfg_w = gsxr1000_k5()
        aamby_valley_winter(cfg_w)
        cfg_s = gsxr1000_k5()
        aamby_valley_summer(cfg_s)
        self.assertGreater(_run(cfg_s).time_quarter, _run(cfg_w).time_quarter)

    def test_altitude_reduces_power(self):
        """1500m altitude loses 3-20% power for NA engine."""
        cfg_sl = gsxr1000_k5()
        cfg_alt = gsxr1000_k5()
        cfg_alt.environment.altitude_m = 1500.0
        p_sl = np.max(_run(cfg_sl).power_kw)
        p_alt = np.max(_run(cfg_alt).power_kw)
        loss = (1 - p_alt / p_sl) * 100
        self.assertGreater(loss, 3)
        self.assertLess(loss, 20)


# ═══════════════════════════════════════════
# PHYSICS CONSERVATION & SANITY
# ═══════════════════════════════════════════


class TestPhysicsSanity(unittest.TestCase):
    def test_monotonic_position(self):
        r = _run(gsxr1000_k5())
        self.assertTrue(np.all(np.diff(r.x) >= 0), "Position must never decrease")

    def test_accel_bounded(self):
        r = _run(gsxr1000_k5())
        self.assertLess(np.max(r.a), 2.0, "Accel > 2g impossible without wheelie bar")

    def test_tire_temp_bounded(self):
        r = _run(gsxr1000_k5())
        self.assertGreater(np.min(r.T_tire), 20)
        self.assertLess(np.max(r.T_tire), 150)

    def test_rpm_bounded(self):
        cfg = gsxr1000_k5()
        r = _run(cfg)
        self.assertLess(np.max(r.rpm), cfg.engine.redline_rpm * 1.05)

    def test_reaches_quarter_mile(self):
        r = _run(gsxr1000_k5())
        self.assertGreaterEqual(r.x[-1], QUARTER_MILE_M - 0.5)

    def test_no_downshifts(self):
        r = _run(gsxr1000_k5())
        self.assertEqual(np.sum(np.diff(r.gear) < 0), 0)

    def test_front_load_non_negative(self):
        r = _run(gsxr1000_k5())
        self.assertGreaterEqual(np.min(r.N_front), 0)

    def test_weight_conservation(self):
        cfg = gsxr1000_k5()
        r = _run(cfg)
        mg = cfg.chassis.total_mass_kg * G
        N_total = r.N_front[50] + r.N_rear[50]
        self.assertAlmostEqual(N_total, mg, delta=mg * 0.05)

    def test_effective_mass_decreases_per_gear(self):
        cfg = gsxr1000_k5()
        eng = MotoQuantEngine(cfg)
        m = [eng.effective_mass(g) for g in range(cfg.drivetrain.num_gears)]
        for i in range(len(m) - 1):
            self.assertGreater(m[i], m[i + 1])


# ═══════════════════════════════════════════
# SUB-MODEL UNIT TESTS
# ═══════════════════════════════════════════


class TestSubModels(unittest.TestCase):
    def _eng(self):
        return MotoQuantEngine(gsxr1000_k5(), dt=0.001)

    def test_torque_positive_in_band(self):
        eng = self._eng()
        for rpm in range(
            int(eng.cfg.engine.idle_rpm), int(eng.cfg.engine.redline_rpm), 500
        ):
            self.assertGreater(
                eng.engine_torque(rpm, 0), 0, f"Zero torque at {rpm} RPM"
            )

    def test_torque_zero_above_limiter(self):
        eng = self._eng()
        self.assertEqual(eng.engine_torque(eng.cfg.engine.redline_rpm * 1.05, 0), 0.0)

    def test_load_sensitivity(self):
        eng = self._eng()
        mu_low = eng.tire_friction_coeff(1000, 65, 0)
        mu_high = eng.tire_friction_coeff(3000, 65, 0)
        self.assertGreater(mu_low, mu_high)

    def test_thermal_grip_optimum(self):
        eng = self._eng()
        T_opt = eng.cfg.tires.optimal_temp_c
        mu_cold = eng.tire_friction_coeff(2000, T_opt - 30, 0)
        mu_opt = eng.tire_friction_coeff(2000, T_opt, 0)
        mu_hot = eng.tire_friction_coeff(2000, T_opt + 30, 0)
        self.assertGreater(mu_opt, mu_cold)
        self.assertGreater(mu_opt, mu_hot)

    def test_aero_drag_v_squared(self):
        eng = self._eng()
        F_50 = eng.aero_drag(50 / 3.6)
        F_200 = eng.aero_drag(200 / 3.6)
        ratio = F_200 / F_50
        self.assertGreater(ratio, 10)  # v^2 law: (200/50)^2 = 16
        self.assertLess(ratio, 25)

    def test_weight_transfer_increases(self):
        eng = self._eng()
        _, Nr_low = eng.weight_transfer(5.0, 0, 0)
        _, Nr_high = eng.weight_transfer(10.0, 0, 0)
        self.assertGreater(Nr_high, Nr_low)

    def test_wheel_torque_ratio(self):
        eng = self._eng()
        T_w = eng.wheel_torque(100.0, 0)
        expected = 100.0 * eng.cfg.drivetrain.overall_ratio(0) * eng.eta_dt
        self.assertAlmostEqual(T_w, expected, delta=1.0)


# ═══════════════════════════════════════════
# CONFIG I/O ROUND-TRIP
# ═══════════════════════════════════════════


class TestConfigIO(unittest.TestCase):
    def test_json_round_trip(self):
        cfg1 = gsxr1000_k5()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            save_config(cfg1, path)
            cfg2 = load_config(path)
            self.assertEqual(cfg2.name, cfg1.name)
            self.assertEqual(cfg2.chassis.dry_mass_kg, cfg1.chassis.dry_mass_kg)
            self.assertEqual(cfg2.tires.mu_peak, cfg1.tires.mu_peak)
        finally:
            os.unlink(path)

    def test_round_trip_same_result(self):
        cfg1 = gsxr1000_k5()
        r1 = _run(cfg1)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            save_config(cfg1, path)
            cfg2 = load_config(path)
            r2 = _run(cfg2)
            self.assertAlmostEqual(r1.time_quarter, r2.time_quarter, places=3)
        finally:
            os.unlink(path)

    def test_dict_round_trip(self):
        cfg1 = hayabusa_gen1()
        d = config_to_dict(cfg1)
        cfg2 = config_from_dict(d)
        self.assertEqual(cfg2.chassis.dry_mass_kg, cfg1.chassis.dry_mass_kg)
        self.assertEqual(cfg2.drivetrain.primary_ratio, cfg1.drivetrain.primary_ratio)


# ═══════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════

if __name__ == "__main__":
    # Run with verbosity
    loader = unittest.TestLoader()
    suite = loader.discover(os.path.dirname(__file__), pattern="run_tests.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
