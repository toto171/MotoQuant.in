"""
Regression test: forced induction must act during the clutch-slip phase.

July 10, 2026 fix. The clutch-slip branch rebuilt the crank torque from the
RAW curve, so turbo/supercharger/N2O multipliers contributed ZERO drive
force and ZERO engine spin-up for the entire launch-slip window (~3 s /
0-110 km/h on a litre bike). A steady-1-bar turbo Hayabusa simmed 0.29 s
slow to the 60-ft and 0.37 s slow on ET versus the physically-equivalent
config with the same boost ratio baked into its torque curve — and every
boost/nitrous part's ROI was correspondingly understated versus parts whose
gains act post-lock.

Production path per docs/INVARIANTS.md I8: these tests drive
MotoQuantEngine.run() itself (the code path /api/simulate and the build
optimizer execute), not a reimplementation. For NA configs the FI
multiplier is exactly 1.0 and x*1.0 is bit-exact, so the pinned
K5/R1/Hayabusa baselines are unchanged by construction (CI-gated
separately by scripts/check_baselines.py).
"""

import unittest

from motoquant import MotoQuantEngine, hayabusa_gen1


def _steady_turbo(cfg, bar=1.0):
    fi = cfg.forced_induction
    fi.boost_type = "turbo"
    fi.target_boost_bar = bar
    fi.prespool_boost_bar = bar  # boost present from the launch itself
    fi.turbo_spool_time_s = 0.05
    return cfg


class TestForcedInductionActsDuringSlip(unittest.TestCase):
    def test_prespooled_turbo_improves_the_60ft(self):
        # The 60-ft is covered entirely inside the clutch-slip window, so a
        # prespooled turbo MUST beat the NA twin there. Pre-fix the two
        # 60-ft times were within a millisecond of each other because the
        # slip branch dropped the boost multiplier entirely.
        na = MotoQuantEngine(hayabusa_gen1()).run()
        boosted = MotoQuantEngine(_steady_turbo(hayabusa_gen1())).run()
        self.assertLess(
            boosted.time_60ft,
            na.time_60ft - 0.05,
            f"boost is dead during clutch slip: 60ft NA {na.time_60ft:.4f} "
            f"vs turbo {boosted.time_60ft:.4f}",
        )

    def test_turbo_path_matches_equivalent_baked_curve(self):
        # A steady-boost turbo and an NA config whose curve carries the same
        # multiplier are the same physical engine; their ETs must agree
        # closely. Pre-fix they diverged by 0.37 s (all of it slip-phase).
        from motoquant.submodels.environmental import EnvironmentalModel

        turbo = _steady_turbo(hayabusa_gen1())
        baked = hayabusa_gen1()
        env = EnvironmentalModel(baked)
        p_atm = env.rho * 287.058 * (baked.environment.ambient_temp_c + 273.15)
        ratio = 1.0 + 1e5 / p_atm
        baked.engine.dyno_curve.torque_nm = baked.engine.dyno_curve.torque_nm * ratio
        baked.engine.peak_torque_nm *= ratio
        baked.engine.peak_power_hp *= ratio

        et_turbo = MotoQuantEngine(turbo).run().time_quarter
        et_baked = MotoQuantEngine(baked).run().time_quarter
        self.assertLess(
            abs(et_turbo - et_baked),
            0.05,
            f"turbo path diverged from its baked-curve twin: "
            f"{et_turbo:.4f} vs {et_baked:.4f}",
        )


if __name__ == "__main__":
    unittest.main()
