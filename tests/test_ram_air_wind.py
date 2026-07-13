"""
Regression tests pinning the July-10-2026 ram-air airspeed fix (40cf813).

drag()/lift() always used airspeed (v + headwind); ram_air_power_mult used
GROUND speed until the fix — a headwind charged the drag penalty while
withholding the ram benefit. These tests pin the airspeed contract through
the production seams (MotoQuantEngine.ram_air_power_mult is the exact hook
the RK4 loop calls; the integration test runs full sims). The fix shipped
without a pinning test — reverting motoquant/submodels/aero.py left the
entire suite green (found in the July-11 PR-105/106 validation pass).

Zero-wind configs are bit-identical by construction (v + 0.0 == v), so the
pinned K5/R1/Hayabusa baselines are untouched by both the fix and these
tests.
"""

import unittest

from motoquant import MotoQuantEngine
from motoquant.defaults import hayabusa_gen1


def _busa(wind_ms: float = 0.0, ram_eta: float | None = None):
    cfg = hayabusa_gen1()  # ram_air_efficiency 0.70 — ram air is live
    cfg.environment.wind_speed_ms = wind_ms
    cfg.environment.wind_direction_deg = 0.0  # 0 = headwind
    if ram_eta is not None:
        cfg.aero.ram_air_efficiency = ram_eta
    return cfg


class TestRamAirUsesAirspeed(unittest.TestCase):
    """Ram intake pressure is a dynamic-pressure effect: airspeed, not v."""

    def test_headwind_equals_higher_ground_speed(self):
        # 50 m/s ground speed into a 10 m/s headwind must produce exactly
        # the ram multiplier of 60 m/s in still air: same rho, same
        # airspeed, and 50.0 + 10.0 == 60.0 is exact in IEEE 754. Pre-fix
        # the wind term was dropped, so this equalled the 50 m/s still-air
        # value instead.
        m_wind = MotoQuantEngine(_busa(wind_ms=10.0)).ram_air_power_mult(50.0)
        calm = MotoQuantEngine(_busa(wind_ms=0.0))
        self.assertEqual(m_wind, calm.ram_air_power_mult(60.0))
        self.assertGreater(m_wind, calm.ram_air_power_mult(50.0))

    def test_zero_wind_is_bit_identical(self):
        # The baseline-safety contract of the fix: v + 0.0 == v, so a
        # zero-wind config must produce the identical multiplier at every
        # speed (this is what keeps the pinned references unmoved).
        explicit_zero = MotoQuantEngine(_busa(wind_ms=0.0))
        untouched = MotoQuantEngine(hayabusa_gen1())
        for v in (5.0, 19.9, 20.0, 40.0, 75.0, 90.0):
            self.assertEqual(
                explicit_zero.ram_air_power_mult(v),
                untouched.ram_air_power_mult(v),
            )

    def test_strong_tailwind_gates_to_unity(self):
        # Tailwind beyond ground speed → negative airspeed. The < 20 m/s
        # gate must return exactly 1.0 rather than let a squared negative
        # airspeed fabricate phantom intake pressure from behind.
        cfg = _busa(wind_ms=30.0)
        cfg.environment.wind_direction_deg = 180.0  # tailwind
        eng = MotoQuantEngine(cfg)
        self.assertEqual(eng.ram_air_power_mult(15.0), 1.0)


class TestHeadwindRamBenefitEndToEnd(unittest.TestCase):
    """Full-sim pin: a headwind must RAISE the ram-air benefit."""

    def test_ram_benefit_grows_with_headwind(self):
        # Ram benefit = ET(ram off) − ET(ram on), same wind. Under a
        # 10 m/s headwind the intake sees more dynamic pressure, so the
        # benefit must clearly exceed the still-air benefit. Measured on
        # the Hayabusa reference: calm benefit 7.2 ms in both trees;
        # headwind benefit 10.8 ms post-fix vs 7.3 ms pre-fix (ground
        # speed left the ram term almost blind to wind). The +2 ms margin
        # sits between the pre-fix gap (+0.1 ms, within solver noise) and
        # the post-fix gap (+3.6 ms), so this fails on revert without
        # pinning a magic ET constant.
        def et(wind_ms, eta):
            cfg = _busa(wind_ms=wind_ms, ram_eta=eta)
            return MotoQuantEngine(cfg).run(max_time=26.0).time_quarter

        benefit_calm = et(0.0, 0.0) - et(0.0, None)
        benefit_wind = et(10.0, 0.0) - et(10.0, None)
        self.assertGreater(
            benefit_wind - benefit_calm,
            0.002,
            "headwind must increase the ram-air benefit (airspeed, not "
            f"ground speed): calm={benefit_calm:.4f}s wind={benefit_wind:.4f}s",
        )


if __name__ == "__main__":
    unittest.main()
