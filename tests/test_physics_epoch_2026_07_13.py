"""
Behaviour pins for the July-13-2026 physics epoch (deliberate rebaseline).

The four model fixes (July-10 review, epoch-gated items 1-4) all move the
pinned references, so the primary regression guard for this epoch is the
COORDINATED pin update: scripts/check_baselines.py targets + the golden
snapshot. These tests additionally pin each fix's *mechanism* through the
production engine so a partial revert cannot hide behind a matching
whole-run ET.

1. a_net clamp: deceleration is real once the clutch locks — gearshift
   torque cuts must produce negative acceleration samples (drag + RR act).
2. Slip-phase parasitic: parasitic losses now act during the pure-slip
   launch window, not only after lock-up.
3. Iterated weight-transfer/traction cap: the cap is converged against the
   CLAMPED acceleration, so surface grip now propagates honestly — wet
   must cost more time than it did through the single-pass cap (ordering
   sanity, exact magnitude pinned by the golden).
4. Front-wheel inertia uses the FRONT rolling radius in effective mass.
"""

import copy
import unittest

import numpy as np

from motoquant import MotoQuantEngine
from motoquant.defaults import gsxr1000_k5


class TestDecelDuringShifts(unittest.TestCase):
    def test_negative_accel_samples_exist_after_lock(self):
        # Pre-epoch, a_net = max(0, .) made deceleration impossible: every
        # accel sample was >= 0 for the whole run. With drag acting through
        # gearshift torque cuts, the K5 must show negative-accel samples.
        r = MotoQuantEngine(gsxr1000_k5()).run(max_time=26.0)
        self.assertLess(
            float(np.min(r.a)),
            0.0,
            "no negative acceleration anywhere — shift-window drag loss "
            "is not being applied (a_net clamp regressed)",
        )

    def test_launch_anti_rollback_survives(self):
        # The clamp must still hold during clutch slip: velocity never goes
        # backwards at launch.
        r = MotoQuantEngine(gsxr1000_k5()).run(max_time=26.0)
        first_second = r.v[r.t <= 1.0]
        self.assertGreaterEqual(float(np.min(np.diff(first_second))), -1e-9)


class TestSlipPhaseParasitic(unittest.TestCase):
    def test_parasitic_acts_during_pure_slip(self):
        # The K5 launches clutch-capacity-capped, so a NORMAL parasitic load
        # is invisible at t=0.5 s (min(crank, cap) == cap either way — this
        # is why zeroing parasitics doesn't discriminate). A parasitic load
        # big enough to pull crank torque BELOW the clutch cap must slow the
        # pure-slip phase — pre-epoch the slip branch used the raw curve, so
        # even an absurd parasitic draw changed nothing before lock-up.
        # The stock K5 curve is at-wheel (parasitic correctly gated OFF for
        # it), so the mechanism is probed on a crank-curve variant.
        base = gsxr1000_k5()
        base.engine.dyno_curve.is_at_wheel = False
        loaded = copy.deepcopy(base)
        loaded.parasitic.alternator_power_w = 8000.0  # deliberately absurd

        def v_at_half_second(cfg):
            r = MotoQuantEngine(cfg).run(max_time=3.0)
            i = int(np.searchsorted(r.t, 0.5))
            return float(r.v[min(i, len(r.v) - 1)])

        v_base = v_at_half_second(base)
        v_loaded = v_at_half_second(loaded)
        self.assertLess(
            v_loaded,
            v_base,
            "a large parasitic load did not slow the pure-slip phase "
            "— the slip branch is back on raw curve torque",
        )


class TestSurfaceGripOrdering(unittest.TestCase):
    def test_wet_costs_more_than_dry(self):
        dry = gsxr1000_k5()
        wet = gsxr1000_k5()
        wet.environment.track_surface = "wet"
        et_dry = MotoQuantEngine(dry).run(max_time=26.0).time_quarter
        et_wet = MotoQuantEngine(wet).run(max_time=26.0).time_quarter
        self.assertGreater(et_wet, et_dry + 0.5)


class TestFrontWheelInertiaRadius(unittest.TestCase):
    def test_front_radius_moves_effective_mass(self):
        # The CLI front-tire override writes front_rolling_radius_m
        # expecting an effect; pre-epoch the front-wheel term divided by
        # the REAR radius, so this knob was dead in effective_mass.
        cfg = gsxr1000_k5()
        eng = MotoQuantEngine(cfg)
        m1 = eng.effective_mass(1)
        cfg2 = copy.deepcopy(cfg)
        cfg2.tires.front_rolling_radius_m *= 1.2
        m2 = MotoQuantEngine(cfg2).effective_mass(1)
        self.assertNotEqual(m1, m2)
        self.assertLess(m2, m1)  # bigger radius -> less reflected inertia


if __name__ == "__main__":
    unittest.main()
