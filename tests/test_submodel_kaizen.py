"""
Regression tests for the April 21, 2026 Kaizen audit of the 15 physics sub-models.

Three silent-failure bugs were identified and fixed:

  1. ``ClutchModel.torque()`` silently treated ``CLUTCH_SLIPPER`` as lockup
     because the slipper branch didn't exist — fell through to the default
     ``return 1e6, 0.0``.  Fixed with a dedicated SLIPPER branch that limits
     back-torque by ``slipper_ratio``.

  2. ``TireModel.thermal_rate()`` computed road-conduction heat loss as
     ``k × A × (T_tire − (T_tire − 5)) / 0.005`` which simplifies to a
     constant 5 K ΔT regardless of actual tire temperature.  Fixed to use
     a proper road-surface temperature (``cfg.env.track_temp_c`` if
     present, otherwise ``T_ambient + 5``).

  3. ``BrakingModel.max_decel()`` hardcoded ``mu_front = 1.2``, ``mu_rear = 1.0``
     ignoring ``cfg.tires.mu_peak`` entirely — so a CEAT Zoom Rad (mu≈1.05)
     and a Pirelli Diablo Supercorsa (mu≈1.45) produced identical braking
     deceleration.  Fixed to use ``cfg.tires.mu_peak`` with realistic
     front/rear load-distribution factors.

These tests also double-check that the fixes don't regress the validated
reference-bike quarter-mile baselines (K5, R1, Hayabusa).
"""

import unittest

import motoquant
from motoquant.models import CLUTCH_LOCKUP, CLUTCH_SLIPPER
from motoquant.submodels.braking import BrakingModel
from motoquant.submodels.clutch import ClutchModel
from motoquant.submodels.tire import TireModel


class TestClutchSlipperBranch(unittest.TestCase):
    """Slipper clutches must limit back-torque; fall-through bug is gone."""

    def _engine_torque_stub(self, rpm, t):
        return 120.0  # typical litrebike crank torque at cruise

    def test_slipper_drive_direction_equals_lockup(self):
        """Drive direction (slip > 0): slipper ≈ lockup at max torque."""
        cfg = motoquant.gsxr1000_k5()
        cfg.clutch.clutch_type = CLUTCH_SLIPPER
        cfg.clutch.slipper_ratio = 0.4
        model = ClutchModel(cfg, self._engine_torque_stub)
        T_max = cfg.clutch.max_torque()
        # slip > 0 → drive direction
        T, Q = model.torque(omega_e=1000.0, omega_input=500.0, T_clutch_temp=50.0, t=0.5)
        self.assertAlmostEqual(T, T_max, delta=1.0,
                               msg="Slipper in drive direction should pass full T_max")
        self.assertGreater(Q, 0.0, "Heat generated while slipping")

    def test_slipper_overrun_caps_backtorque(self):
        """Overrun (slip < 0, engine slower than input): back-torque ≤ slipper_ratio × T_max."""
        cfg = motoquant.gsxr1000_k5()
        cfg.clutch.clutch_type = CLUTCH_SLIPPER
        cfg.clutch.slipper_ratio = 0.4
        model = ClutchModel(cfg, self._engine_torque_stub)
        T_max = cfg.clutch.max_torque()
        # Engine slower than input → slip < 0 → overrun
        T, Q = model.torque(omega_e=500.0, omega_input=1000.0, T_clutch_temp=50.0, t=0.5)
        # Magnitude of back-torque should be ≤ slipper_ratio × T_max (plus tiny tolerance)
        self.assertLess(abs(T), T_max,
                        msg="Overrun back-torque must be limited below T_max")
        self.assertAlmostEqual(abs(T), T_max * 0.4, delta=1.0,
                               msg="Overrun back-torque should equal slipper_ratio × T_max")
        self.assertLess(T, 0.0, msg="Back-torque should be negative (opposing direction)")

    def test_slipper_no_silent_fallthrough(self):
        """
        Before the fix, a slipper clutch fell through to `return 1e6, 0.0`
        which masquerades as a perfect lockup.  That means Q_clutch would be
        zero — no heat — which is physically wrong while slipping.
        """
        cfg = motoquant.gsxr1000_k5()
        cfg.clutch.clutch_type = CLUTCH_SLIPPER
        model = ClutchModel(cfg, self._engine_torque_stub)
        # Slipping in drive direction — must produce heat
        _, Q = model.torque(omega_e=1200.0, omega_input=400.0, T_clutch_temp=60.0, t=0.3)
        self.assertGreater(Q, 0.0,
                           "Slipper clutch while slipping MUST produce heat "
                           "(previous fallthrough silently said Q=0)")

    def test_unknown_clutch_type_does_not_crash(self):
        """Unknown clutch_type still falls back to lockup (with a warning, not crash)."""
        cfg = motoquant.gsxr1000_k5()
        cfg.clutch.clutch_type = "some_future_clutch_type"
        model = ClutchModel(cfg, self._engine_torque_stub)
        T, Q = model.torque(omega_e=1000.0, omega_input=1000.1, T_clutch_temp=50.0, t=0.5)
        # Near-zero slip → returns the lockup-style 1e6
        self.assertGreater(T, 0.0)


class TestTireConduction(unittest.TestCase):
    """Tire Q_cond must depend on actual tire temperature, not a constant."""

    def test_hot_tire_loses_more_heat_than_cool_tire(self):
        """
        The old formula produced the SAME conduction for a 40 °C tire as
        for a 100 °C tire (both give ΔT = 5, always).  With the fix, a
        hotter tire must shed more heat to the road.
        """
        cfg = motoquant.gsxr1000_k5()
        cfg.environment.track_temp_c = 30.0  # typical Indian drag strip
        model = TireModel(cfg, mu_prep=1.0, T_tire_ref_K=298.15)
        # Zero slip, zero velocity — isolate conduction term
        dT_cool = model.thermal_rate(F_x=0.0, v=0.0, slip_ratio=0.0,
                                     T_tire=40.0, T_ambient=25.0)
        dT_hot = model.thermal_rate(F_x=0.0, v=0.0, slip_ratio=0.0,
                                    T_tire=100.0, T_ambient=25.0)
        # Hot tire loses more heat → dT more negative than cool tire
        self.assertLess(dT_hot, dT_cool,
                        "Hotter tire must cool faster than cooler tire "
                        "(conduction + convection both temperature-dependent)")

    def test_tire_at_road_temp_has_zero_conduction(self):
        """
        When T_tire == T_road, Q_cond must be exactly zero.  (The old buggy
        formula gave a constant non-zero Q_cond here.)
        """
        cfg = motoquant.gsxr1000_k5()
        cfg.environment.track_temp_c = 45.0
        model = TireModel(cfg, mu_prep=1.0, T_tire_ref_K=298.15)
        # We can't inspect Q_cond directly, so we rely on dT.  If conduction
        # ≈ 0 and convection is also zero (set T_tire = T_ambient), and no
        # friction heat, then dT should be zero.
        cfg.environment.track_temp_c = 45.0
        dT = model.thermal_rate(F_x=0.0, v=0.0, slip_ratio=0.0,
                                T_tire=45.0, T_ambient=45.0)
        # Road temp = tire temp = ambient temp → all three heat fluxes zero
        self.assertAlmostEqual(dT, 0.0, places=4,
                               msg="Tire at equilibrium with road and air must have dT≈0")


class TestBrakingUsesActualMu(unittest.TestCase):
    """BrakingModel must honour cfg.tires.mu_peak, not hardcoded defaults."""

    def test_sticky_tire_outperforms_touring_tire(self):
        """
        A bike with mu_peak=1.5 (drag slick) must achieve stronger braking
        than the same bike with mu_peak=0.9 (touring tire).  The old code
        returned identical deceleration for both because mu was hardcoded.
        """
        cfg = motoquant.gsxr1000_k5()
        m_total = cfg.chassis.total_mass_kg
        N_f_static = m_total * 9.81 * 0.5
        N_r_static = m_total * 9.81 * 0.5

        cfg.tires.mu_peak = 0.9
        touring_decel = BrakingModel(cfg, N_f_static, N_r_static).max_decel(30.0, m_total)

        cfg.tires.mu_peak = 1.5
        slick_decel = BrakingModel(cfg, N_f_static, N_r_static).max_decel(30.0, m_total)

        self.assertGreater(slick_decel, touring_decel,
                           "Stickier tire must give more braking deceleration "
                           "(hardcoded mu bug would make them equal)")
        # Ballpark: slick should be ~1.5/0.9 ≈ 1.67× the touring number
        ratio = slick_decel / max(1e-3, touring_decel)
        self.assertGreater(ratio, 1.3,
                           f"Slick/touring braking ratio {ratio:.2f} too low — "
                           "mu_peak may not be flowing through")

    def test_braking_scales_with_mu_peak(self):
        """Monotonic: doubling mu_peak roughly doubles peak braking force."""
        cfg = motoquant.gsxr1000_k5()
        m_total = cfg.chassis.total_mass_kg
        N_f = m_total * 9.81 * 0.5
        N_r = m_total * 9.81 * 0.5

        cfg.tires.mu_peak = 0.8
        a_low = BrakingModel(cfg, N_f, N_r).max_decel(25.0, m_total)

        cfg.tires.mu_peak = 1.6
        a_high = BrakingModel(cfg, N_f, N_r).max_decel(25.0, m_total)

        ratio = a_high / max(1e-3, a_low)
        self.assertGreater(ratio, 1.5,
                           f"2× mu_peak should give ~2× braking, got {ratio:.2f}×")


class TestReferenceBaselinesIntact(unittest.TestCase):
    """After Kaizen fixes, validated reference ETs must still match within 0.050 s."""

    def test_k5_baseline(self):
        r = motoquant.MotoQuantEngine(motoquant.gsxr1000_k5()).run()
        self.assertAlmostEqual(r.time_quarter, 10.03, delta=0.05,
                               msg=f"K5 drifted: {r.time_quarter:.3f}s vs 10.03s target")

    def test_r1_baseline(self):
        r = motoquant.MotoQuantEngine(motoquant.yzfr1_4c8()).run()
        self.assertAlmostEqual(r.time_quarter, 10.30, delta=0.05,
                               msg=f"R1 drifted: {r.time_quarter:.3f}s vs 10.30s target")

    def test_hayabusa_baseline(self):
        r = motoquant.MotoQuantEngine(motoquant.hayabusa_gen1()).run()
        self.assertAlmostEqual(r.time_quarter, 10.47, delta=0.05,
                               msg=f"Hayabusa drifted: {r.time_quarter:.3f}s vs 10.47s target")


if __name__ == "__main__":
    unittest.main()
