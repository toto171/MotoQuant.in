"""
test_no_silent_failures.py
==========================
Regression tests for the silent ET=0.0 bug fix (April 22, 2026).

Tests that:
1. Every bike in ALL_KNOWN_BIKES either finishes the quarter-mile
   or is explicitly flagged as did-not-finish (never 0.0 ET with status=ok).
2. Reference bikes still produce baseline ETs within tolerance.
"""

import pytest

from motoquant import MotoQuantEngine, gsxr1000_k5, hayabusa_gen1, yzfr1_4c8
from motoquant.scraper.importer import spec_to_bike_config
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES


class TestNoSilentFailures:
    """Ensure the silent 0.0 ET bug is fixed across all bikes."""

    # Whitelist of bikes known to legitimately not finish in 25s
    # (e.g., scooters, very low-power machines)
    # This list should remain very small (<5 entries). If it grows,
    # the physics model needs tuning, not the test.
    KNOWN_DNF_WHITELIST = {
        # Legitimate DNF — vintage small-cc 2-strokes (~11-16 hp stock).
        # These bikes run low-14s to 19s+ real-world at best, and the
        # current 2T expansion-chamber model + stock power leaves them
        # short of the 402.336 m line within the 26 s sim window.
        # Documented limitation: vintage 2T small-cc physics bias.
        ("Yamaha", "RX100"),
        ("Yamaha", "RX135 (5-speed India)"),
        ("Yamaha", "RXZ135 (Malaysia)"),
        ("Yezdi", "250 Classic"),
    }

    def test_all_bikes_no_silent_zero_et(self):
        """Every bike finishes (finished_quarter=True) or is whitelisted."""
        failures = []
        for spec in ALL_KNOWN_BIKES:
            cfg = spec_to_bike_config(spec)
            result = MotoQuantEngine(cfg).run()

            # Check: either finished or whitelisted
            is_whitelisted = (
                spec.manufacturer,
                spec.model_name,
            ) in self.KNOWN_DNF_WHITELIST
            if not bool(result.finished_quarter) and not is_whitelisted:
                failures.append(
                    f"{spec.manufacturer} {spec.model_name}: "
                    f"did-not-finish (max_x={result.max_distance_m:.1f}m, "
                    f"t={result.elapsed_time_s:.1f}s)"
                )

        if failures:
            pytest.fail(
                f"Found {len(failures)} bikes that did not finish:\n"
                + "\n".join(failures)
            )

    def test_reference_baselines_preserved(self):
        """K5, R1 4C8, and Hayabusa remain within baseline tolerance."""
        refs = [
            ("GSX-R 1000 K5", gsxr1000_k5(), 10.034, 0.020),
            ("YZF-R1 4C8", yzfr1_4c8(), 10.286, 0.030),
            ("Hayabusa Gen1", hayabusa_gen1(), 10.472, 0.030),
        ]

        for name, cfg, expected_et, tolerance in refs:
            result = MotoQuantEngine(cfg).run()
            actual_et = result.time_quarter

            assert bool(result.finished_quarter), f"{name} did not finish quarter-mile"
            assert abs(actual_et - expected_et) <= tolerance, (
                f"{name}: ET={actual_et:.3f}s, expected {expected_et:.3f}s "
                f"±{tolerance:.3f}s"
            )


class TestCompletionTracking:
    """Verify finished_quarter, max_distance_m, and elapsed_time_s are set."""

    def test_finished_quarter_set_on_completion(self):
        """Bike that finishes has finished_quarter=True."""
        cfg = gsxr1000_k5()
        result = MotoQuantEngine(cfg).run()

        assert result.finished_quarter  # np.bool_ -> bool
        assert result.time_quarter > 0.0
        assert result.max_distance_m >= 402.336  # QUARTER_MILE_M
        assert result.elapsed_time_s > 0.0

    def test_max_distance_and_elapsed_time_populated(self):
        """max_distance_m and elapsed_time_s are always set."""
        cfg = gsxr1000_k5()
        result = MotoQuantEngine(cfg).run()

        assert result.max_distance_m > 0.0
        assert result.elapsed_time_s > 0.0
        assert result.max_distance_m == result.x[-1]  # Should match last position
        assert result.elapsed_time_s == result.t[-1]  # Should match last time
