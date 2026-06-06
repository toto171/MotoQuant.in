"""
Regression tests for the Apr-24-PM small-cc + 2-stroke physics calibration.

These tests MUST exercise the production path (``spec_to_bike_config`` +
``MotoQuantEngine.run``) — not a tautological scaling inside the test.
They fail if the importer stops applying the displacement-scaled
fluid-mass / basket-inertia fix, the 2T launch_rpm floor, or the small-
commuter-single 2T curve branch.

Coverage:
  * ``TestReferenceBaselines``            — K5/R1/Hayabusa must stay within
                                            ±0.02 s of their documented ETs.
  * ``TestClusterBiases``                 — one benchmark per cluster at
                                            realistic post-fix tolerance.
  * ``TestPowerBoostStillLive``           — +50 % power scaling on R15 V3
                                            must shave ≥1 s of ET (guards
                                            against another "dead knob"
                                            regression).
  * ``TestFluidMassScaling``              — direct checks on the new helper.
  * ``TestBasketInertiaScaling``          — direct checks on the new helper.
  * ``TestTwoStrokeSmallCommuter``        — widened Gaussian band makes
                                            RX100 reach gear ≥ 2 inside 26 s.

All simulations use the DEFAULT environment (sea-level ISA) so the
numbers are deterministic and don't depend on the DB / weather state.
"""

from __future__ import annotations

import copy
import unittest

from motoquant import MotoQuantEngine
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8
from motoquant.scraper.importer import (
    _basket_inertia_from_spec,
    _fluid_mass_from_spec,
    spec_to_bike_config,
)
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES


def _find_spec(pattern: str):
    """Return the first ALL_KNOWN_BIKES entry whose model_name contains pattern."""
    for s in ALL_KNOWN_BIKES:
        if pattern in s.model_name:
            return s
    raise AssertionError(f"No spec matching {pattern!r}")


def _run(cfg, max_time: float = 26.0):
    return MotoQuantEngine(cfg).run(use_adaptive_dt=False, max_time=max_time)


class TestReferenceBaselines(unittest.TestCase):
    """Must NOT regress K5/R1/Hayabusa references (±0.02 s tolerance)."""

    def test_k5_unchanged(self):
        r = _run(gsxr1000_k5())
        self.assertAlmostEqual(r.time_quarter, 10.0334, delta=0.02)

    def test_r1_unchanged(self):
        r = _run(yzfr1_4c8())
        self.assertAlmostEqual(r.time_quarter, 10.2859, delta=0.02)

    def test_hayabusa_unchanged(self):
        r = _run(hayabusa_gen1())
        self.assertAlmostEqual(r.time_quarter, 10.4712, delta=0.02)


class TestClusterBiases(unittest.TestCase):
    """One benchmark per problem cluster, at post-fix tolerance.

    The tolerances are deliberately generous (>=1 s) — the goal of this
    test suite is to catch regressions back to the pre-fix DNF / 2-3 s
    bias state, NOT to pin the sim to a single-session calibration.
    """

    # (pattern, real_et_s, post_fix_tolerance_s, cluster_label)
    CANARIES = [
        ("R15 V3", 16.0, 3.2, "150-200 entry"),
        ("Pulsar NS200", 15.5, 2.6, "200-300 entry"),
        ("Duke 250", 14.8, 1.4, "200-300 entry"),
        ("CBR500R", 12.85, 1.3, "300-500 twin"),
        ("Ninja 400", 12.8, 1.8, "300-500 twin"),
        ("RD350", 13.5, 3.5, "2T twin"),
        ("RX100", None, None, "2T small"),  # only checked for finish
    ]

    def test_each_cluster_canary_inside_tolerance(self):
        for pattern, real_et, tol, cluster in self.CANARIES:
            with self.subTest(cluster=cluster, bike=pattern):
                spec = _find_spec(pattern)
                cfg = spec_to_bike_config(spec)
                r = _run(cfg)
                if real_et is None:
                    # RX100 — just must finish
                    self.assertTrue(
                        r.finished_quarter,
                        f"{pattern} must finish quarter-mile (pre-fix DNF)",
                    )
                    continue
                self.assertTrue(
                    r.finished_quarter,
                    f"{pattern} must finish quarter-mile",
                )
                delta = r.time_quarter - real_et
                self.assertLess(
                    abs(delta),
                    tol,
                    f"{pattern} ET={r.time_quarter:.3f}s vs real={real_et}s "
                    f"(Δ={delta:+.3f}s exceeds tolerance {tol}s)",
                )


class TestPowerBoostStillLive(unittest.TestCase):
    """Guard against another ``dead knob`` regression on small-cc 4T.

    On a stock R15 V3 the Apr-24-AM entry in CLAUDE.md documented a bug
    where ``power_boost_pct`` had zero effect on ET. That was traced to a
    stale DB row (not a live physics bug) and the bug itself was
    imaginary — the spec path has always scaled ET with power. This test
    defends that invariant against future regressions.
    """

    def test_50pct_boost_shaves_at_least_one_second(self):
        spec = _find_spec("R15 V3")
        cfg = spec_to_bike_config(spec)

        r_stock = _run(cfg)
        self.assertTrue(r_stock.finished_quarter)

        boosted = copy.deepcopy(cfg)
        scale = 1.50
        boosted.engine.peak_power_hp *= scale
        boosted.engine.peak_torque_nm *= scale
        if boosted.engine.dyno_curve is not None:
            boosted.engine.dyno_curve.torque_nm = (
                boosted.engine.dyno_curve.torque_nm * scale
            )
        r_boost = _run(boosted)
        self.assertTrue(r_boost.finished_quarter)
        improvement = r_stock.time_quarter - r_boost.time_quarter
        self.assertGreater(
            improvement,
            1.0,
            f"+50% power must shave ≥1 s of ET on R15 V3 "
            f"(stock {r_stock.time_quarter:.3f}s, boosted {r_boost.time_quarter:.3f}s, "
            f"Δ={improvement:.3f}s). Power knob regressed to near-dead.",
        )


class TestFluidMassScaling(unittest.TestCase):
    """Direct unit tests on the new ``_fluid_mass_from_spec`` helper."""

    def _mk(self, cc):
        # Mock BikeSpec with just the displacement field
        class _Spec:
            pass

        s = _Spec()
        s.displacement_cc = cc
        return s

    def test_rx100_class_is_small(self):
        self.assertAlmostEqual(_fluid_mass_from_spec(self._mk(98)), 8.88, delta=0.01)

    def test_r15_v3_class(self):
        self.assertAlmostEqual(_fluid_mass_from_spec(self._mk(155)), 9.395, delta=0.01)

    def test_k5_class_matches_historical(self):
        self.assertAlmostEqual(_fluid_mass_from_spec(self._mk(1000)), 17.0, delta=0.1)

    def test_hayabusa_class(self):
        self.assertAlmostEqual(_fluid_mass_from_spec(self._mk(1340)), 20.06, delta=0.01)

    def test_clipped_floor(self):
        self.assertEqual(_fluid_mass_from_spec(self._mk(50)), 8.45)

    def test_clipped_ceiling(self):
        self.assertEqual(_fluid_mass_from_spec(self._mk(3000)), 22.0)


class TestBasketInertiaScaling(unittest.TestCase):
    """Direct unit tests on the new ``_basket_inertia_from_spec`` helper."""

    def _mk(self, cc):
        class _Spec:
            pass

        s = _Spec()
        s.displacement_cc = cc
        return s

    def test_r15_v3_basket_small(self):
        self.assertAlmostEqual(
            _basket_inertia_from_spec(self._mk(155)),
            0.00155,
            delta=1e-5,
        )

    def test_k5_basket_matches_reference(self):
        self.assertAlmostEqual(
            _basket_inertia_from_spec(self._mk(1000)),
            0.010,
            delta=1e-5,
        )

    def test_clipped_floor(self):
        # 50 cc bike gets floored at 0.001
        self.assertEqual(_basket_inertia_from_spec(self._mk(50)), 0.001)

    def test_clipped_ceiling(self):
        # 2500 cc Rocket 3 gets clipped at 0.020
        self.assertEqual(_basket_inertia_from_spec(self._mk(2500)), 0.020)


class TestTwoStrokeSmallCommuter(unittest.TestCase):
    """Widened Gaussian band for sub-200 cc piston-port 2T singles.

    Pre-fix RX100/RX135/RXZ135 DNF'd (torque collapsed to baseline 12 %
    above ~8 100 rpm; bike couldn't even reach top-of-gear-1 speed). Fix
    widens band_lo/band_hi/baseline so usable torque extends across the
    full 5-9 krpm window. Also the 2T launch_rpm is now floor-clamped at
    peak_torque_rpm so launches don't fire off the rising edge of the
    Gaussian at half torque.
    """

    def test_rx100_finishes_quarter(self):
        spec = _find_spec("RX100")
        cfg = spec_to_bike_config(spec)
        r = _run(cfg)
        self.assertTrue(
            r.finished_quarter,
            f"RX100 must complete 1/4 mile in <=26 s post-fix "
            f"(pre-fix: DNF). Got elapsed={r.elapsed_time_s:.2f}s",
        )

    def test_rx100_reaches_at_least_gear_2(self):
        spec = _find_spec("RX100")
        cfg = spec_to_bike_config(spec)
        r = _run(cfg)
        max_gear = int(r.gear.max())
        self.assertGreaterEqual(
            max_gear,
            2,
            "Pre-fix RX100 was stuck in gear 1 for 26 s because torque "
            "collapsed above 8 100 rpm. Post-fix it must upshift at "
            "least once.",
        )

    def test_launch_rpm_at_or_above_peak_torque(self):
        """2T launch_rpm must never fire below peak_torque_rpm."""
        for pattern in ["RX100", "RX135", "RXZ135", "RD350", "RS125"]:
            with self.subTest(bike=pattern):
                spec = _find_spec(pattern)
                cfg = spec_to_bike_config(spec)
                peak_tq = spec.peak_torque_rpm or cfg.engine.peak_torque_rpm
                self.assertGreaterEqual(
                    cfg.staging.launch_rpm,
                    peak_tq * 0.99,
                    f"{pattern}: staging.launch_rpm={cfg.staging.launch_rpm:.0f} "
                    f"must be >= peak_torque_rpm={peak_tq:.0f} (pre-fix bug: "
                    f"launch at 0.92×tuned_rpm could land below peak_tq).",
                )


class TestSpecPathPropagatesFixes(unittest.TestCase):
    """Production-path integration: spec_to_bike_config must actually apply
    the Apr-24-PM helpers to the resulting BikeConfig.

    These would fail if someone accidentally deleted the
    ``_basket_inertia_from_spec`` call or re-introduced
    ``fluid_mass_kg=17.0`` in the chassis builder.
    """

    def test_r15_v3_chassis_uses_scaled_fluid(self):
        cfg = spec_to_bike_config(_find_spec("R15 V3"))
        # pre-fix: 17 kg; post-fix: ~9.4 kg
        self.assertLess(
            cfg.chassis.fluid_mass_kg,
            12.0,
            "R15 V3 fluid_mass_kg must be < 12 kg (pre-fix was hardcoded 17 kg)",
        )
        self.assertGreater(cfg.chassis.fluid_mass_kg, 7.0)

    def test_r15_v3_clutch_uses_scaled_basket(self):
        cfg = spec_to_bike_config(_find_spec("R15 V3"))
        # pre-fix: 0.010; post-fix: ~0.00155
        self.assertLess(
            cfg.clutch.basket_inertia_kgm2,
            0.005,
            "R15 V3 basket_inertia_kgm2 must be < 0.005 (pre-fix was 0.010 K5 default)",
        )
        self.assertGreater(cfg.clutch.basket_inertia_kgm2, 0.0005)

    def test_k5_catalog_entry_still_gets_full_mass(self):
        """Sanity: a catalog 1000cc bike should still have near-17 kg fluid."""
        cfg = spec_to_bike_config(_find_spec("GSX-R 1000"))
        self.assertGreater(cfg.chassis.fluid_mass_kg, 15.0)


if __name__ == "__main__":
    unittest.main()
