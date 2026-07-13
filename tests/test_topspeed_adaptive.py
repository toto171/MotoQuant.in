"""
Regression tests for the adaptive-dt simulation path (top-speed mode).

Two July-10-2026 fixes, both production-path per docs/INVARIANTS.md I8:

1. run_top_speed() plateau detection must measure its window in SIMULATED
   TIME, not sample counts. Adaptive dt makes samples non-uniform (0.5-5 ms)
   and SimResult.dt only records the final step size, so a count-based
   window shrank to ~0.15 s wherever dt had adapted down — a single slow
   gearshift (torque cut => ~zero net accel across hundreds of fine-grained
   samples) then satisfied the "plateau" and /api/simulate/topspeed reported
   terminal velocity a few seconds into the run.

2. run(use_adaptive_dt=True) must not silently truncate when adaptive dt
   halves below the constructor dt the output arrays were sized from. A run
   dominated by clutch slip (e.g. a clutch that never locks) exhausted the
   step budget at exactly max_time/2 and returned a truncated result with
   no warning.

Neither test touches the fixed-dt quarter-mile path, so the pinned
K5/R1/Hayabusa baselines are unaffected by construction.
"""

import unittest

from motoquant import MotoQuantEngine, gsxr1000_k5


class TestPlateauDetectionTimeBased(unittest.TestCase):
    """Gearshifts must not register as the terminal-velocity plateau."""

    def test_slow_gearshift_is_not_terminal(self):
        # 160 ms shifts: at the adaptive 0.5 ms floor a single shift spans
        # ~320 zero-accel samples — more than the old count-based window
        # (1.5 s / 5 ms final dt = 300 samples). Pre-fix this reported
        # terminal velocity at the first shift (~4.2 s / ~84 m).
        cfg = gsxr1000_k5()
        cfg.drivetrain.total_shift_time_ms = 160.0
        ts = MotoQuantEngine(cfg).run_top_speed(max_time=60.0)
        self.assertGreater(
            ts.time_to_terminal_s,
            20.0,
            "plateau detected during a gearshift, not at the aero plateau",
        )
        self.assertGreater(ts.distance_to_terminal_m, 1000.0)
        # The headline number (peak velocity) is unaffected either way.
        self.assertGreater(ts.terminal_velocity_kmh, 250.0)

    def test_shift_time_does_not_move_terminal_detection(self):
        # The detected plateau time must be a property of the bike's aero
        # power balance, not of how many fine-grained samples a shift emits.
        times = []
        for shift_ms in (100.0, 200.0):
            cfg = gsxr1000_k5()
            cfg.drivetrain.total_shift_time_ms = shift_ms
            ts = MotoQuantEngine(cfg).run_top_speed(max_time=60.0)
            times.append(ts.time_to_terminal_s)
        self.assertLess(
            abs(times[0] - times[1]),
            5.0,
            f"terminal-time detection swung with shift time: {times}",
        )


class TestAdaptiveStepBudget(unittest.TestCase):
    """Adaptive runs must reach max_time even when dt stays at the floor."""

    def test_never_locking_clutch_runs_to_max_time(self):
        # A clutch with no clamp force never locks, so adaptive dt stays at
        # the 0.5 ms floor for the whole run — twice the steps the arrays
        # were sized for. Pre-fix this truncated at exactly max_time/2.
        cfg = gsxr1000_k5()
        cfg.clutch.spring_preload_n = 1.0
        r = MotoQuantEngine(cfg).run(
            distance=20000.0, max_time=5.0, use_adaptive_dt=True
        )
        self.assertGreaterEqual(
            r.elapsed_time_s,
            5.0 - 0.01,
            "adaptive run truncated before max_time (step budget exhausted)",
        )


if __name__ == "__main__":
    unittest.main()
