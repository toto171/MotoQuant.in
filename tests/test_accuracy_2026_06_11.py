"""Regression tests for the 2026-06-11 accuracy pass.

Pins (all via the PRODUCTION import path, not test-local reconstructions):
  1. R155-family gearing: the R15 V3 must never again inherit the R1's
     1.609 primary via the Tier-1 substring leak (it simulates with the
     service-manual 73/24 = 3.042 and the real cassette).
  2. R15 V3/V4 pair consistency: near-identical hardware must produce
     near-identical ETs (pre-fix the pair split 2.1 s against the SAME
     instrumented MotoStatz benchmark).
  3. The measured Indian Autos Mag wheel curve is injected for the V3
     generation (not just V4) — losing the dyno-curve key regresses the
     V3 trap speed by ~17 km/h.
  4. Flagship calibration pin: R15 V4 ET within +/-0.6 s of the 17.62 s
     MotoStatz instrumented benchmark.
  5. ZX-10R benchmarks are year-specific (2004 no longer shadows
     2006/2008) and the 2004 figure matches the Sport Rider archive.
  6. The CATEGORY_UNKNOWN legacy profile anchor is untouched.
  7. Reference baselines exact to 4 decimals.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from motoquant import MotoQuantEngine
from motoquant.category_profiles import CATEGORY_UNKNOWN, get_profile
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8
from motoquant.scraper.importer import spec_to_bike_config
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES


def _spec(model_name):
    s = next((x for x in ALL_KNOWN_BIKES if x.model_name == model_name), None)
    assert s is not None, f"{model_name} missing from ALL_KNOWN_BIKES"
    return s


def _run_et(cfg):
    r = MotoQuantEngine(cfg).run(use_adaptive_dt=False, max_time=26.0)
    assert r.finished_quarter, "did not finish the quarter"
    return float(r.time_quarter)


class TestR155Gearing:
    """Production-path gearing pins for the Yamaha R155 family."""

    @pytest.mark.parametrize("name", ["YZF-R15 V3", "YZF-R15 V4"])
    def test_primary_is_service_manual(self, name):
        cfg = spec_to_bike_config(_spec(name))
        # 73/24 = 3.042 per the Yamaha R15 V3/V4 service manual. The V3
        # used to inherit the YZF-R1's 1.609 via a Tier-1 substring leak.
        assert cfg.drivetrain.primary_ratio == pytest.approx(3.042, abs=1e-6)
        assert cfg.drivetrain.front_sprocket == 14
        assert cfg.drivetrain.rear_sprocket == 48

    def test_v3_v4_share_cassette(self):
        v3 = spec_to_bike_config(_spec("YZF-R15 V3"))
        v4 = spec_to_bike_config(_spec("YZF-R15 V4"))
        assert v3.drivetrain.gear_ratios == v4.drivetrain.gear_ratios

    def test_mt15_runs_52t(self):
        for name in ("MT-15 V1", "MT-15 V2"):
            cfg = spec_to_bike_config(_spec(name))
            assert cfg.drivetrain.rear_sprocket == 52, name
            assert cfg.drivetrain.primary_ratio == pytest.approx(3.042, abs=1e-6)


class TestR155MeasuredCurve:
    def test_v3_generation_gets_measured_wheel_curve(self):
        import numpy as np

        for name in ("YZF-R15 V3", "MT-15 V1"):
            cfg = spec_to_bike_config(_spec(name))
            dc = cfg.engine.dyno_curve
            assert dc is not None, name
            t7500 = float(
                np.interp(7500.0, np.asarray(dc.rpm), np.asarray(dc.torque_nm))
            )
            # Indian Autos Mag chassis dyno: 12.7 Nm wheel at 7500. The
            # synthetic <22hp curve produces ~15+ Nm here (x1.13 boost),
            # so this asserts the measured curve actually got injected.
            assert abs(t7500 - 12.7) < 0.05, f"{name}: T@7500={t7500}"


class TestR155Calibration:
    def test_pair_consistency(self):
        """V3 and V4 are near-identical hardware; the sim pair must not
        split by more than 0.4 s (pre-fix: 2.1 s split against the same
        instrumented benchmark)."""
        et3 = _run_et(spec_to_bike_config(_spec("YZF-R15 V3")))
        et4 = _run_et(spec_to_bike_config(_spec("YZF-R15 V4")))
        assert abs(et3 - et4) < 0.4, f"V3 {et3:.3f} vs V4 {et4:.3f}"

    def test_r15_v4_tracks_instrumented_benchmark(self):
        """MotoStatz instrumented: 17.62 s. Calibration pin at +/-0.6 s."""
        et = _run_et(spec_to_bike_config(_spec("YZF-R15 V4")))
        assert abs(et - 17.62) < 0.6, f"R15 V4 ET {et:.3f} vs 17.62"


class TestBenchmarkHygiene:
    def test_zx10r_rows_are_year_specific(self):
        from scripts.validation_sweep import BENCHMARKS

        zx = {
            y: (et, src)
            for (m, mod, y, et, trap, src) in BENCHMARKS
            if m == "Kawasaki" and mod == "Ninja ZX-10R"
        }
        # Sport Rider archive figures (cycleworld.com sportbike-performance-numbers)
        assert zx.get(2004, (None,))[0] == pytest.approx(9.92)
        assert 2006 in zx and zx[2006][0] == pytest.approx(9.764)
        assert 2008 in zx and zx[2008][0] == pytest.approx(9.93)


class TestLegacyAnchors:
    def test_unknown_profile_untouched(self):
        p = get_profile(None)
        assert p.name == CATEGORY_UNKNOWN
        assert p.over_clutch_factor == 0.0
        assert p.max_engine_decel_rads2 == 0.0
        assert p.launch_floor_factor == 0.0

    def test_reference_baselines_exact(self):
        for fn, tgt in (
            (gsxr1000_k5, 10.0334),
            (yzfr1_4c8, 10.2859),
            (hayabusa_gen1, 10.4712),
        ):
            r = MotoQuantEngine(fn()).run()
            assert abs(float(r.time_quarter) - tgt) < 5e-5
