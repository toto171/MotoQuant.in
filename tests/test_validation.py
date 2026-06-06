"""
MotoQuant Pro — Validation Test Suite
=====================================
Regression tests ensuring simulation accuracy against published benchmarks.

Run with:  python -m pytest tests/ -v
"""

import numpy as np

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

# ═══════════════════════════════════════════
# QUARTER-MILE VALIDATION TARGETS
# ═══════════════════════════════════════════
# Published data ± acceptable tolerance
# Sources: Cycle World, Sport Rider, Hayabusa Owners Group forums


class TestQuarterMileValidation:
    """Validate simulated ETs against published quarter-mile data."""

    def _run(self, config):
        engine = MotoQuantEngine(config, dt=0.001)
        return engine.run(distance=QUARTER_MILE_M, max_time=15.0)

    def test_k5_quarter_mile_et(self):
        """K5 ET within ±0.10s of published 9.97s (Sport Rider)."""
        r = self._run(gsxr1000_k5())
        assert abs(r.time_quarter - 9.97) < 0.10, (
            f"K5 ET {r.time_quarter:.3f}s deviates >0.10s from 9.97s"
        )

    def test_k5_trap_speed(self):
        """K5 trap speed within ±10 km/h of published 233 km/h."""
        r = self._run(gsxr1000_k5())
        trap_kmh = r.speed_quarter * 3.6
        assert abs(trap_kmh - 233.0) < 10.0, (
            f"K5 trap {trap_kmh:.1f} km/h deviates >10 km/h from 233"
        )

    def test_r1_quarter_mile_et(self):
        """R1 ET within ±0.10s of published ~10.3s."""
        r = self._run(yzfr1_4c8())
        assert abs(r.time_quarter - 10.3) < 0.10, (
            f"R1 ET {r.time_quarter:.3f}s deviates >0.10s from 10.3s"
        )

    def test_busa_quarter_mile_et(self):
        """Busa ET within typical owner range (10.2-10.5s)."""
        r = self._run(hayabusa_gen1())
        assert 10.1 < r.time_quarter < 10.7, (
            f"Busa ET {r.time_quarter:.3f}s outside typical stock range 10.1-10.7s"
        )

    def test_busa_trap_speed(self):
        """Busa trap speed within ±10 km/h of typical 235 km/h."""
        r = self._run(hayabusa_gen1())
        trap_kmh = r.speed_quarter * 3.6
        assert abs(trap_kmh - 235.0) < 10.0, (
            f"Busa trap {trap_kmh:.1f} km/h deviates >10 km/h from 235"
        )

    def test_k5_sixty_foot(self):
        """K5 60-ft time within realistic range (1.8-2.1s)."""
        r = self._run(gsxr1000_k5())
        assert 1.8 < r.time_60ft < 2.1, (
            f"K5 60-ft {r.time_60ft:.3f}s outside realistic range"
        )

    def test_relative_order(self):
        """K5 should be faster than R1, which should be faster than Busa (stock launch)."""
        r_k5 = self._run(gsxr1000_k5())
        r_r1 = self._run(yzfr1_4c8())
        r_busa = self._run(hayabusa_gen1())
        assert r_k5.time_quarter < r_r1.time_quarter, (
            f"K5 ({r_k5.time_quarter:.3f}) should be faster than R1 ({r_r1.time_quarter:.3f})"
        )
        assert r_r1.time_quarter < r_busa.time_quarter, (
            f"R1 ({r_r1.time_quarter:.3f}) should be faster than Busa ({r_busa.time_quarter:.3f})"
        )


# ═══════════════════════════════════════════
# ENVIRONMENTAL CORRECTION TESTS
# ═══════════════════════════════════════════


class TestEnvironmentalCorrection:
    """Verify altitude/temperature corrections produce expected penalties."""

    def _run(self, config):
        engine = MotoQuantEngine(config, dt=0.001)
        return engine.run(distance=QUARTER_MILE_M, max_time=15.0)

    def test_aamby_winter_penalty(self):
        """Aamby Valley winter should add 0.05-0.25s to sea-level ET."""
        cfg_sl = gsxr1000_k5()
        cfg_aw = gsxr1000_k5()
        aamby_valley_winter(cfg_aw)
        r_sl = self._run(cfg_sl)
        r_aw = self._run(cfg_aw)
        penalty = r_aw.time_quarter - r_sl.time_quarter
        assert 0.05 < penalty < 0.25, (
            f"Aamby winter penalty {penalty:.3f}s outside expected 0.05-0.25s"
        )

    def test_aamby_summer_worse_than_winter(self):
        """Aamby summer (hotter, more humid) should be slower than winter."""
        cfg_w = gsxr1000_k5()
        cfg_s = gsxr1000_k5()
        aamby_valley_winter(cfg_w)
        aamby_valley_summer(cfg_s)
        r_w = self._run(cfg_w)
        r_s = self._run(cfg_s)
        assert r_s.time_quarter > r_w.time_quarter, (
            "Aamby summer should be slower than winter"
        )

    def test_altitude_reduces_power(self):
        """Higher altitude → less power for NA engine."""
        cfg_sl = gsxr1000_k5()
        cfg_alt = gsxr1000_k5()
        cfg_alt.environment.altitude_m = 1500.0  # ~5000 ft
        r_sl = self._run(cfg_sl)
        r_alt = self._run(cfg_alt)
        p_sl = np.max(r_sl.power_kw)
        p_alt = np.max(r_alt.power_kw)
        assert p_alt < p_sl, "Altitude should reduce peak power"
        loss_pct = (1 - p_alt / p_sl) * 100
        assert 3 < loss_pct < 20, (
            f"Power loss at 1500m: {loss_pct:.1f}% (expected 3-20%)"
        )


# ═══════════════════════════════════════════
# PHYSICS CONSERVATION & SANITY TESTS
# ═══════════════════════════════════════════


class TestPhysicsSanity:
    """Verify fundamental physics laws and sub-model behavior."""

    def _run(self, config):
        engine = MotoQuantEngine(config, dt=0.001)
        return engine.run(distance=QUARTER_MILE_M, max_time=15.0)

    def test_monotonic_position(self):
        """Position should be monotonically increasing (bike never goes backward)."""
        r = self._run(gsxr1000_k5())
        dx = np.diff(r.x)
        assert np.all(dx >= 0), "Position should never decrease"

    def test_monotonic_velocity_initial(self):
        """Velocity should be increasing in the first 2 seconds (launch phase)."""
        r = self._run(gsxr1000_k5())
        # First 2000 steps (2 seconds)
        n = min(2000, len(r.v) - 1)
        dv = np.diff(r.v[:n])
        negative = np.sum(dv < -0.01)
        assert negative < 10, (
            f"Velocity should be mostly increasing in launch phase (found {negative} decreasing steps)"
        )

    def test_acceleration_bounded(self):
        """Acceleration should never exceed 2g (impossible for non-wheelie-bar bike)."""
        r = self._run(gsxr1000_k5())
        assert np.max(r.a) < 2.0, (
            f"Peak acceleration {np.max(r.a):.2f}g exceeds physical limit"
        )

    def test_tire_temp_bounded(self):
        """Tire temperature should stay within 20-150°C during a drag pass."""
        r = self._run(gsxr1000_k5())
        assert np.min(r.T_tire) > 20.0, "Tire too cold"
        assert np.max(r.T_tire) < 150.0, "Tire too hot (unrealistic)"

    def test_rpm_bounded(self):
        """RPM should never exceed redline * 1.05."""
        cfg = gsxr1000_k5()
        r = self._run(cfg)
        max_rpm = cfg.engine.redline_rpm * 1.05
        assert np.max(r.rpm) < max_rpm, (
            f"RPM {np.max(r.rpm):.0f} exceeds redline ({cfg.engine.redline_rpm}) + 5%"
        )

    def test_quarter_mile_distance(self):
        """Final position should be at or beyond the quarter-mile mark."""
        r = self._run(gsxr1000_k5())
        assert r.x[-1] >= QUARTER_MILE_M - 0.5, (
            f"Final position {r.x[-1]:.1f}m short of quarter-mile ({QUARTER_MILE_M:.1f}m)"
        )

    def test_gear_progression(self):
        """Gears should only go up (no downshifts during acceleration)."""
        r = self._run(gsxr1000_k5())
        dg = np.diff(r.gear)
        downshifts = np.sum(dg < 0)
        assert downshifts == 0, f"Found {downshifts} downshifts during acceleration"

    def test_front_load_non_negative(self):
        """Front wheel load should not go negative (would mean wheelie not caught)."""
        r = self._run(gsxr1000_k5())
        assert np.min(r.N_front) >= 0, (
            f"Negative front load {np.min(r.N_front):.1f}N — wheelie not controlled"
        )

    def test_weight_conservation(self):
        """Sum of front + rear loads should approximately equal total weight ± aero lift."""
        cfg = gsxr1000_k5()
        r = self._run(cfg)
        total_weight = cfg.chassis.total_mass_kg * G
        # At low speed (first 100 steps), aero is negligible
        N_total_start = r.N_front[50] + r.N_rear[50]
        assert abs(N_total_start - total_weight) < total_weight * 0.05, (
            f"Weight not conserved: N_f+N_r={N_total_start:.1f} vs mg={total_weight:.1f}"
        )

    def test_effective_mass_decreases_with_gear(self):
        """Effective mass should decrease in higher gears (lower gear ratio → less rotational inertia)."""
        cfg = gsxr1000_k5()
        eng = MotoQuantEngine(cfg)
        m_eff = [eng.effective_mass(g) for g in range(cfg.drivetrain.num_gears)]
        for i in range(len(m_eff) - 1):
            assert m_eff[i] > m_eff[i + 1], (
                f"m_eff should decrease: gear {i + 1}={m_eff[i]:.1f} vs gear {i + 2}={m_eff[i + 1]:.1f}"
            )


# ═══════════════════════════════════════════
# CONFIG I/O ROUND-TRIP TESTS
# ═══════════════════════════════════════════


class TestConfigIO:
    """Verify JSON config serialization and deserialization."""

    def test_round_trip_k5(self, tmp_path):
        """K5 config should survive save → load → run cycle."""
        cfg1 = gsxr1000_k5()
        path = tmp_path / "k5_test.json"
        save_config(cfg1, path)
        cfg2 = load_config(path)
        assert cfg2.name == cfg1.name
        assert cfg2.chassis.dry_mass_kg == cfg1.chassis.dry_mass_kg
        assert cfg2.engine.peak_power_hp == cfg1.engine.peak_power_hp
        assert cfg2.tires.mu_peak == cfg1.tires.mu_peak

    def test_round_trip_produces_same_result(self, tmp_path):
        """Loaded config should produce identical simulation results."""
        cfg1 = gsxr1000_k5()
        eng1 = MotoQuantEngine(cfg1, dt=0.001)
        r1 = eng1.run(distance=QUARTER_MILE_M, max_time=15.0)

        path = tmp_path / "k5_roundtrip.json"
        save_config(cfg1, path)
        cfg2 = load_config(path)
        eng2 = MotoQuantEngine(cfg2, dt=0.001)
        r2 = eng2.run(distance=QUARTER_MILE_M, max_time=15.0)

        assert abs(r1.time_quarter - r2.time_quarter) < 0.001, (
            f"Round-trip changed ET: {r1.time_quarter:.4f} vs {r2.time_quarter:.4f}"
        )

    def test_dict_round_trip(self):
        """config_to_dict → config_from_dict should preserve parameters."""
        cfg1 = hayabusa_gen1()
        d = config_to_dict(cfg1)
        cfg2 = config_from_dict(d)
        assert cfg2.chassis.dry_mass_kg == cfg1.chassis.dry_mass_kg
        assert cfg2.drivetrain.primary_ratio == cfg1.drivetrain.primary_ratio


# ═══════════════════════════════════════════
# SUB-MODEL UNIT TESTS
# ═══════════════════════════════════════════


class TestSubModels:
    """Unit tests for individual physics sub-models."""

    def _engine(self, config=None):
        if config is None:
            config = gsxr1000_k5()
        return MotoQuantEngine(config, dt=0.001)

    def test_engine_torque_positive_in_band(self):
        """Engine should produce positive torque between idle and redline."""
        eng = self._engine()
        cfg = eng.cfg
        for rpm in range(int(cfg.engine.idle_rpm), int(cfg.engine.redline_rpm), 500):
            T = eng.engine_torque(rpm, 0)
            assert T > 0, f"Zero or negative torque at {rpm} RPM"

    def test_engine_torque_zero_above_redline(self):
        """Engine should produce zero torque above redline + margin."""
        eng = self._engine()
        T = eng.engine_torque(eng.cfg.engine.redline_rpm * 1.05, 0)
        assert T == 0.0, "Should hit rev limiter above redline"

    def test_tire_friction_decreases_with_load(self):
        """Load sensitivity: mu should decrease with increasing normal load."""
        eng = self._engine()
        mu_low = eng.tire_friction_coeff(1000, 65, 0)
        mu_high = eng.tire_friction_coeff(3000, 65, 0)
        assert mu_low > mu_high, (
            f"Load sensitivity failed: mu@1000N={mu_low:.4f} should > mu@3000N={mu_high:.4f}"
        )

    def test_tire_friction_optimal_at_target_temp(self):
        """Tire grip should be highest near optimal temperature."""
        eng = self._engine()
        T_opt = eng.cfg.tires.optimal_temp_c
        mu_cold = eng.tire_friction_coeff(2000, T_opt - 30, 0)
        mu_opt = eng.tire_friction_coeff(2000, T_opt, 0)
        mu_hot = eng.tire_friction_coeff(2000, T_opt + 30, 0)
        assert mu_opt > mu_cold, "Grip should be higher at optimal temp than cold"
        assert mu_opt > mu_hot, "Grip should be higher at optimal temp than hot"

    def test_aero_drag_increases_with_speed(self):
        """Aero drag should increase with speed squared."""
        eng = self._engine()
        F_50 = eng.aero_drag(50 / 3.6)  # 50 km/h
        F_100 = eng.aero_drag(100 / 3.6)  # 100 km/h
        F_200 = eng.aero_drag(200 / 3.6)  # 200 km/h
        assert F_100 > F_50, "Drag should increase with speed"
        ratio = F_200 / F_50
        # v^2 law: (200/50)^2 = 16, but ram air and headwind can modify slightly
        assert 10 < ratio < 25, f"Drag ratio 200/50 km/h = {ratio:.1f} (expected ~16)"

    def test_weight_transfer_increases_with_accel(self):
        """Higher acceleration → more weight transfer to rear."""
        eng = self._engine()
        _, Nr_low = eng.weight_transfer(5.0, 0, 0)  # 0.5g
        _, Nr_high = eng.weight_transfer(10.0, 0, 0)  # 1.0g
        assert Nr_high > Nr_low, "More accel should put more weight on rear"

    def test_effective_radius_grows_with_speed(self):
        """Centrifugal tire growth: radius should increase at high omega."""
        eng = self._engine()
        r_slow = eng.tire_effective_radius(10.0)  # ~3 m/s
        r_fast = eng.tire_effective_radius(200.0)  # ~60 m/s
        assert r_fast >= r_slow, "Tire should grow at high speed"

    def test_wheel_torque_positive(self):
        """Wheel torque should be positive for positive engine torque."""
        eng = self._engine()
        T_w = eng.wheel_torque(100.0, 0)  # 100 Nm engine, 1st gear
        assert T_w > 0, "Wheel torque should be positive"
        # Check gear ratio multiplication
        i_total = eng.cfg.drivetrain.overall_ratio(0)
        eta = eng.eta_dt
        expected = 100.0 * i_total * eta
        assert abs(T_w - expected) < 1.0, (
            f"Wheel torque {T_w:.1f} doesn't match expected {expected:.1f}"
        )


# ═══════════════════════════════════════════
# BENCHMARK MATCHER SPECIFICITY TESTS
# ═══════════════════════════════════════════


class TestMatcherSpecificity:
    """Regression tests for the benchmark matcher specificity fix.

    Before 2026-05-25, _wb_match used pure token-subset matching: every
    token in the pattern must appear in the spec string. This meant that
    "Ninja H2" (2 tokens) would match "Ninja H2 SX" (3 tokens) because
    {ninja, h2} ⊆ {ninja, h2, sx}. When iteration order was not sorted by
    token-count descending, the shorter pattern could shadow the longer one.

    Fix: callers sort candidates by model-token-count descending before
    iterating so "Ninja H2 SX" (3 tokens) is tried before "Ninja H2" (2 tokens).
    These tests pin the correct binding for the four collision pairs:
      - Z H2 (naked)    vs Ninja H2 (supersport)   vs Ninja H2 SX (tourer) vs Ninja H2R (track)
    """

    def _wb_match(self, pattern: str, spec_str: str) -> bool:
        """Inline copy of the production _wb_match for direct unit testing."""
        import re

        tokens = [t for t in re.split(r"[\s\-\.]+", pattern.lower()) if t]
        spec_tokens = {t for t in re.split(r"[\s\-\.]+", spec_str.lower()) if t}
        return all(t in spec_tokens for t in tokens)

    def _token_count(self, s: str) -> int:
        import re

        return len([t for t in re.split(r"[\s\-\.]+", s) if t])

    # ── Direct _wb_match logic tests ────────────────────────────────────────

    def test_ninja_h2_matches_ninja_h2(self):
        """'Ninja H2' should match spec 'Ninja H2 (2015-2022)'."""
        assert self._wb_match("Ninja H2", "Ninja H2 2015-2022") is True

    def test_ninja_h2_sx_matches_ninja_h2_sx(self):
        """'Ninja H2 SX' should match spec 'Ninja H2 SX (2018-2023)'."""
        assert self._wb_match("Ninja H2 SX", "Ninja H2 SX 2018-2023") is True

    def test_ninja_h2_also_matches_h2_sx_spec(self):
        """'Ninja H2' (2-token) DOES token-match 'Ninja H2 SX' — subset is true.
        This is the root-cause of the shadow bug; the fix is NOT to change this
        function but to ensure more-specific patterns are tried first by callers.
        """
        assert self._wb_match("Ninja H2", "Ninja H2 SX 2018-2023") is True

    def test_ninja_h2_does_not_match_z_h2(self):
        """'Ninja H2' should NOT match 'Z H2' — 'Ninja' token is absent."""
        assert self._wb_match("Ninja H2", "Z H2 2020-2025") is False

    def test_z_h2_does_not_match_ninja_h2(self):
        """'Z H2' should NOT match 'Ninja H2' — 'Z' token is absent."""
        assert self._wb_match("Z H2", "Ninja H2 2015-2022") is False

    def test_ninja_h2r_matches_ninja_h2r(self):
        """'Ninja H2R' should match spec 'Ninja H2R'."""
        assert self._wb_match("Ninja H2R", "Ninja H2R 2015-2022") is True

    def test_ninja_h2r_does_not_match_ninja_h2(self):
        """'Ninja H2R' (3 tokens) must NOT match 'Ninja H2 2015-2022'
        because 'H2R' is not in {ninja, h2, 2015-2022}."""
        assert self._wb_match("Ninja H2R", "Ninja H2 2015-2022") is False

    # ── Specificity-ordering tests ───────────────────────────────────────────

    def test_h2_sx_has_more_tokens_than_h2(self):
        """'Ninja H2 SX' should have more tokens than 'Ninja H2'
        — this is the invariant the sort relies on."""
        assert self._token_count("Ninja H2 SX") > self._token_count("Ninja H2")

    def test_h2r_same_token_count_as_h2(self):
        """'Ninja H2R' has the same token count as 'Ninja H2' (both 2 tokens:
        ['Ninja', 'H2R'] vs ['Ninja', 'H2']). H2R does NOT collide with H2
        because the token 'H2R' != 'H2', so no shadow bug exists between them.
        This test documents that the H2R collision risk is a non-issue."""
        assert self._token_count("Ninja H2R") == self._token_count("Ninja H2")

    def test_specificity_sort_orders_h2_sx_before_h2(self):
        """Sorting benchmark model keys by token-count descending puts
        'Ninja H2 SX' before 'Ninja H2', preventing the shadow bug."""
        import re

        patterns = ["Ninja H2", "Z H2", "Ninja H2 SX", "Ninja H2R"]

        def _tok(s):
            return len([t for t in re.split(r"[\s\-\.]+", s) if t])

        sorted_patterns = sorted(patterns, key=_tok, reverse=True)
        idx_h2 = sorted_patterns.index("Ninja H2")
        idx_h2_sx = sorted_patterns.index("Ninja H2 SX")
        # H2 SX (3 tokens) must appear before H2 (2 tokens); this is the
        # critical ordering for the shadow bug fix.
        # Note: H2R has the SAME token count as H2 (both 2: ['Ninja','H2R'] /
        # ['Ninja','H2']) — the sort key is equal; stable sort preserves their
        # relative position. H2R does NOT shadow H2 because 'H2R' != 'H2', so
        # no additional ordering constraint is needed for H2R.
        assert idx_h2_sx < idx_h2, (
            f"'Ninja H2 SX' (idx {idx_h2_sx}) should sort before 'Ninja H2' (idx {idx_h2})"
        )

    def test_after_sort_first_match_for_h2_sx_spec_is_h2_sx(self):
        """After sorting benchmark keys by specificity, iterating over the H2
        collision group should bind 'Ninja H2 SX 2018-2023' to the 'Ninja H2 SX'
        benchmark first (not the shorter 'Ninja H2' benchmark)."""
        import re

        # Simulate the production matcher with sorted iteration
        benchmark_models = ["Ninja H2", "Z H2", "Ninja H2 SX", "Ninja H2R"]

        def _tok(s):
            return len([t for t in re.split(r"[\s\-\.]+", s) if t])

        sorted_models = sorted(benchmark_models, key=_tok, reverse=True)
        spec_name = "Ninja H2 SX 2018-2023"

        first_match = None
        for bmodel in sorted_models:
            if self._wb_match(bmodel, spec_name):
                first_match = bmodel
                break

        assert first_match == "Ninja H2 SX", (
            f"Expected 'Ninja H2 SX' to match first, got '{first_match}'"
        )

    def test_after_sort_first_match_for_h2_spec_is_h2(self):
        """After sorting, 'Ninja H2 2015-2022' should still bind to 'Ninja H2',
        not 'Ninja H2 SX' (which won't match because 'sx' is absent)."""
        import re

        benchmark_models = ["Ninja H2", "Z H2", "Ninja H2 SX", "Ninja H2R"]

        def _tok(s):
            return len([t for t in re.split(r"[\s\-\.]+", s) if t])

        sorted_models = sorted(benchmark_models, key=_tok, reverse=True)
        spec_name = "Ninja H2 2015-2022"

        first_match = None
        for bmodel in sorted_models:
            if self._wb_match(bmodel, spec_name):
                first_match = bmodel
                break

        assert first_match == "Ninja H2", (
            f"Expected 'Ninja H2' to match first, got '{first_match}'"
        )

    def test_z_h2_spec_binds_to_z_h2_benchmark(self):
        """'Z H2 2020-2025' should bind to 'Z H2', never to 'Ninja H2' or 'Ninja H2 SX'."""
        import re

        benchmark_models = ["Ninja H2", "Z H2", "Ninja H2 SX", "Ninja H2R"]

        def _tok(s):
            return len([t for t in re.split(r"[\s\-\.]+", s) if t])

        sorted_models = sorted(benchmark_models, key=_tok, reverse=True)
        spec_name = "Z H2 2020-2025"

        first_match = None
        for bmodel in sorted_models:
            if self._wb_match(bmodel, spec_name):
                first_match = bmodel
                break

        assert first_match == "Z H2", (
            f"Expected 'Z H2' to match first, got '{first_match}'"
        )


class TestProductionMatcherSpecificity:
    """Regression tests that exercise the *real* production helpers
    `_best_benchmark_match` and `_model_specificity_score` in
    `scripts/validation_sweep.py` (Option 2 fix from DISPATCH_INBOX
    2026-05-25). These would fail if the score-and-pick logic regressed
    to first-match-wins, regardless of any benchmark-list ordering.
    """

    @staticmethod
    def _make_spec(manufacturer, model_name, year_from, year_to=None):
        """Lightweight spec stand-in matching the BikeSpec attributes
        accessed by `_best_benchmark_match`."""
        from types import SimpleNamespace

        return SimpleNamespace(
            manufacturer=manufacturer,
            model_name=model_name,
            year_from=year_from,
            year_to=year_to or year_from,
        )

    def test_specificity_score_orders_h2_sx_above_h2(self):
        from scripts.validation_sweep import _model_specificity_score

        assert _model_specificity_score("Ninja H2 SX") > _model_specificity_score(
            "Ninja H2"
        )

    def test_specificity_score_handles_hyphen_and_dot(self):
        from scripts.validation_sweep import _model_specificity_score

        # YZF-R6 splits on hyphen → 2 tokens; "YZF-R6 13S" → 3 tokens
        assert _model_specificity_score("YZF-R6") == 2
        assert _model_specificity_score("YZF-R6 (13S)") >= 3

    def test_h2_sx_spec_binds_to_h2_sx_benchmark_via_production_helper(self):
        """The H2 SX 2018-2023 catalog row must bind to the 'Ninja H2 SX'
        benchmark, not the older 'Ninja H2' one — this is the canonical
        regression for the inbox-2026-05-25 ticket."""
        from scripts.validation_sweep import _best_benchmark_match

        benchmarks = [
            ("Kawasaki", "Ninja H2", 2015, 9.62, 247, "MCN 2015"),
            ("Kawasaki", "Ninja H2 SX", 2018, 10.04, 232, "Cycle World 2018"),
            ("Kawasaki", "Z H2", 2020, 9.95, 240, "Cycle World 2020"),
        ]
        spec = self._make_spec("Kawasaki", "Ninja H2 SX (2018-2023)", 2018, 2023)
        match = _best_benchmark_match(spec, benchmarks)
        assert match is not None, "H2 SX spec should bind to a benchmark"
        assert match[1] == "Ninja H2 SX", (
            f"Expected H2 SX benchmark, got {match[1]} ({match[3]}s)"
        )
        assert match[3] == 10.04

    def test_h2_spec_binds_to_h2_benchmark_not_h2_sx(self):
        """The plain Ninja H2 catalog row must bind to the 'Ninja H2'
        benchmark — the 3-token 'Ninja H2 SX' must NOT match an H2 spec
        because 'sx' is absent from spec tokens."""
        from scripts.validation_sweep import _best_benchmark_match

        benchmarks = [
            ("Kawasaki", "Ninja H2", 2015, 9.62, 247, "MCN 2015"),
            ("Kawasaki", "Ninja H2 SX", 2018, 10.04, 232, "Cycle World 2018"),
            ("Kawasaki", "Z H2", 2020, 9.95, 240, "Cycle World 2020"),
        ]
        spec = self._make_spec("Kawasaki", "Ninja H2", 2015, 2022)
        match = _best_benchmark_match(spec, benchmarks)
        assert match is not None
        assert match[1] == "Ninja H2", f"Expected 'Ninja H2', got {match[1]}"
        assert match[3] == 9.62

    def test_z_h2_spec_binds_to_z_h2_not_ninja_h2(self):
        """Z H2 (naked supercharged) must NOT shadow-bind to Ninja H2."""
        from scripts.validation_sweep import _best_benchmark_match

        benchmarks = [
            ("Kawasaki", "Ninja H2", 2015, 9.62, 247, "MCN 2015"),
            ("Kawasaki", "Z H2", 2020, 9.95, 240, "Cycle World 2020"),
        ]
        spec = self._make_spec("Kawasaki", "Z H2", 2020, 2025)
        match = _best_benchmark_match(spec, benchmarks)
        assert match is not None
        assert match[1] == "Z H2"

    def test_z_h2_se_spec_does_not_bind_to_out_of_range_z_h2(self):
        """Z H2 SE catalog row (2024-2025) must NOT bind to the 2020 Z H2
        benchmark — year-range filter correctly rejects it. Documents
        the conservative-no-match behaviour: better to leave delta
        unrecorded than to inflate matched-N with a year-mismatched bind.
        """
        from scripts.validation_sweep import _best_benchmark_match

        benchmarks = [
            ("Kawasaki", "Z H2", 2020, 9.95, 240, "Cycle World 2020"),
        ]
        spec = self._make_spec("Kawasaki", "Z H2 SE", 2024, 2025)
        match = _best_benchmark_match(spec, benchmarks)
        assert match is None, (
            f"Z H2 SE (2024-2025) must not bind to Z H2 (2020); got {match}"
        )

    def test_z_h2_se_spec_binds_to_z_h2_when_in_year_range(self):
        """If a Z H2 benchmark exists within the SE's year range, the SE
        spec correctly binds via word-boundary token-subset match."""
        from scripts.validation_sweep import _best_benchmark_match

        benchmarks = [
            ("Kawasaki", "Z H2", 2024, 10.10, 238, "Cycle World 2024 (synthetic)"),
        ]
        spec = self._make_spec("Kawasaki", "Z H2 SE", 2024, 2025)
        match = _best_benchmark_match(spec, benchmarks)
        assert match is not None
        assert match[1] == "Z H2"

    def test_h2r_does_not_bind_to_h2(self):
        """Ninja H2R (track-only, 2-token where token = 'H2R') has NO
        valid benchmark binding to the 'Ninja H2' entry — 'h2' != 'h2r'
        so the word-boundary check correctly rejects."""
        from scripts.validation_sweep import _best_benchmark_match

        benchmarks = [
            ("Kawasaki", "Ninja H2", 2015, 9.62, 247, "MCN 2015"),
        ]
        spec = self._make_spec("Kawasaki", "Ninja H2R", 2015, 2026)
        match = _best_benchmark_match(spec, benchmarks)
        assert match is None, (
            f"H2R must NOT bind to H2 benchmark; got {match[1] if match else None}"
        )

    def test_rsv4_factory_spec_binds_to_factory_not_plain_rsv4(self):
        """RSV4 Factory catalog row must bind to 'RSV4 Factory' benchmark,
        not the less-specific 'RSV4 1000' even though both pass
        word-boundary matching against the spec."""
        from scripts.validation_sweep import _best_benchmark_match

        benchmarks = [
            ("Aprilia", "RSV4 1000", 2009, 10.40, 230, "Sport Rider 2009"),
            ("Aprilia", "RSV4 Factory", 2021, 10.05, 238, "Cycle World 2021"),
        ]
        # The catalog has RSV4 Factory spans — pick a year that overlaps Factory
        spec = self._make_spec("Aprilia", "RSV4 Factory", 2021, 2023)
        match = _best_benchmark_match(spec, benchmarks)
        assert match is not None
        assert match[1] == "RSV4 Factory", f"Expected 'RSV4 Factory', got {match[1]}"

    def test_plain_rsv4_does_not_bind_to_factory(self):
        """Plain RSV4 spec (no 'Factory' token) must NOT bind to the
        more-specific 'RSV4 Factory' benchmark — Factory token is absent."""
        from scripts.validation_sweep import _best_benchmark_match

        benchmarks = [
            ("Aprilia", "RSV4 1000", 2009, 10.40, 230, "Sport Rider 2009"),
            ("Aprilia", "RSV4 Factory", 2021, 10.05, 238, "Cycle World 2021"),
        ]
        spec = self._make_spec("Aprilia", "RSV4 1000", 2009, 2014)
        match = _best_benchmark_match(spec, benchmarks)
        assert match is not None
        assert match[1] == "RSV4 1000"

    def test_r6_and_r6s_do_not_collide(self):
        """YZF-R6 vs YZF-R6S — 'R6' and 'R6S' are distinct tokens after
        split-on-hyphen so neither pattern should match the other's spec."""
        from scripts.validation_sweep import _best_benchmark_match, _model_match

        # Sanity-check the _model_match primitive first
        assert _model_match("YZF-R6", "YZF-R6S") is False
        assert _model_match("YZF-R6S", "YZF-R6") is False

        benchmarks = [
            ("Yamaha", "YZF-R6", 2007, 10.85, 220, "Cycle World 2007"),
        ]
        spec_r6s = self._make_spec("Yamaha", "YZF-R6S", 2006, 2009)
        assert _best_benchmark_match(spec_r6s, benchmarks) is None, (
            "R6S spec must not bind to R6 benchmark"
        )

    def test_year_range_filter_rejects_out_of_range_match(self):
        """If a more-specific benchmark exists but falls outside the spec's
        year range, validation_sweep correctly returns None for that
        candidate. The less-specific in-range benchmark is also rejected
        here because its year (2015) is below the SX spec's year_from
        (2018) — strict year-range filter prevents inflated matched-N."""
        from scripts.validation_sweep import _best_benchmark_match

        benchmarks = [
            ("Kawasaki", "Ninja H2", 2015, 9.62, 247, "MCN 2015"),
            ("Kawasaki", "Ninja H2 SX", 2030, 10.04, 232, "future"),  # out of range
        ]
        spec = self._make_spec("Kawasaki", "Ninja H2 SX (2018-2023)", 2018, 2023)
        match = _best_benchmark_match(spec, benchmarks)
        # H2 2015 is also out of range (2015 < 2018); H2 SX 2030 is out of
        # range; expect no match — conservative-no-match is the right call.
        assert match is None, (
            f"Both benchmarks out of range; expected None, got {match}"
        )

    def test_sweep_with_clusters_specificity_score_in_sync(self):
        """Both scripts must keep `_model_specificity_score` in lock-step
        so the matcher behaves identically between sweep paths."""
        from scripts.sweep_with_clusters import _model_specificity_score as score_b
        from scripts.validation_sweep import _model_specificity_score as score_a

        for s in [
            "Ninja H2",
            "Ninja H2 SX",
            "Z H2",
            "RSV4 Factory",
            "YZF-R6",
            "YZF-R6S",
            "Ninja H2R",
            "Street Triple 765 RS",
        ]:
            assert score_a(s) == score_b(s), (
                f"Specificity score diverged for {s!r}: {score_a(s)} vs {score_b(s)}"
            )
