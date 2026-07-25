"""
Unit-sanity guard for the benchmark corpora (added 2026-07-25 audit).

The trap column of ``scripts/validation_sweep.BENCHMARKS`` is km/h. Rows have
repeatedly been entered carrying the source's *mph* figure instead — the
YZF-R7 2022 row (fixed 2026-05-31) and eleven more found in the 2026-07-25
trap-column audit. Every one of them was caught by the same assumption-free
physical bound, so it is worth enforcing rather than re-auditing by hand:

    For a monotonically accelerating vehicle, the speed at the trap must
    exceed the average speed held over the quarter mile.

        trap_kmh  >  402.336 m / ET  (converted to km/h)

A row that violates this is not a "slightly optimistic" datapoint — it is
arithmetically impossible, so the guard needs no tolerance band to be fair.
The mph/km/h ratio is 1.609, and the trap/average ratio for real motorcycles
sits around 1.25–1.65, so an un-converted mph value lands *below* the average
essentially every time. That is precisely why this bound catches the bug.

These tests drive the real corpus (docs/INVARIANTS.md I8) — they fail if a
future edit reintroduces an mph value in the km/h column.
"""

from __future__ import annotations

import unittest

QUARTER_MILE_M = 402.336
MPH_TO_KMH = 1.609344


def _corpus():
    from scripts.validation_sweep import BENCHMARKS

    return BENCHMARKS


class TestTrapSpeedExceedsAverageSpeed(unittest.TestCase):
    """No ET-corpus row may claim a trap below its own average speed."""

    def test_every_row_is_physically_possible(self):
        offenders = []
        for row in _corpus():
            mfr, model, year, et, trap, src = (
                row[0],
                row[1],
                row[2],
                row[3],
                row[4],
                row[5],
            )
            if not et or not trap or trap <= 0:
                continue  # 0.0 is the documented "trap not published" sentinel
            avg_kmh = QUARTER_MILE_M / et * 3.6
            if trap < avg_kmh:
                offenders.append(
                    f"{mfr} {model} {year}: ET {et}s needs an average of "
                    f"{avg_kmh:.1f} km/h but trap is {trap} km/h "
                    f"(= {trap * MPH_TO_KMH:.1f} km/h if the source figure was mph) "
                    f"— src: {src}"
                )
        self.assertEqual(
            offenders,
            [],
            "Benchmark row(s) claim a trap speed below the average speed the bike "
            "must have held to cover 402.336 m in the stated ET. That is impossible "
            "for an accelerating vehicle and almost always means an mph figure was "
            "entered in the km/h trap column:\n  " + "\n  ".join(offenders),
        )

    def test_the_bound_actually_bites(self):
        """Guard the guard: an mph value must trip the assertion.

        Without this, a future refactor could neuter the check above (e.g. by
        skipping rows) and the suite would stay green while the corpus rots.
        """
        et, trap_mph = 12.98, 102  # the real pre-fix Ninja 400 2018 row
        avg_kmh = QUARTER_MILE_M / et * 3.6
        self.assertLess(trap_mph, avg_kmh, "the mph value must violate the bound")
        self.assertGreater(
            trap_mph * MPH_TO_KMH, avg_kmh, "the converted value must satisfy it"
        )


class TestTrapSpeedUpperSanity(unittest.TestCase):
    """A trap far above the average is equally suspect (double-converted, typo)."""

    def test_no_row_has_an_absurd_trap_to_average_ratio(self):
        offenders = []
        for row in _corpus():
            mfr, model, year, et, trap = row[0], row[1], row[2], row[3], row[4]
            if not et or not trap or trap <= 0:
                continue
            ratio = trap / (QUARTER_MILE_M / et * 3.6)
            # Real quarter-mile runs sit ~1.25-1.65. 2.0 allows generous headroom
            # while still catching a km/h value that was converted a second time.
            if ratio > 2.0:
                offenders.append(
                    f"{mfr} {model} {year}: trap {trap} km/h is {ratio:.2f}x its "
                    f"average speed — suspect double conversion or typo"
                )
        self.assertEqual(offenders, [], "\n  " + "\n  ".join(offenders))


if __name__ == "__main__":
    unittest.main()
