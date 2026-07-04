"""Regression tests for the canonical benchmark source-quality classifier.

Roadmap A4-27 consolidated two divergent source-quality functions
(``scripts/sweep_lib.source_quality`` and a local
``scripts/phys_weighted_sweep.source_weight``) onto a single implementation
hosted in ``scripts/sweep_lib``. These tests pin:

* the canonical weight for representative source strings,
* that ``phys_weighted_sweep`` now shares the exact same implementation, and
* zero headline drift — the canonical scalar weight reproduces the OLD
  ``phys_weighted_sweep.source_weight`` for every source string in the live
  ``BENCHMARKS`` corpus (the published authoritative sweep,
  ``reports/acc_final_2026_07_03.json``, was produced with that logic).
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts import phys_weighted_sweep as pw
from scripts.sweep_lib import source_quality, source_weight
from scripts.validation_sweep import BENCHMARKS


# Verbatim copy of the PRE-consolidation phys_weighted_sweep.source_weight.
# This is the logic that produced the published authoritative sweep; the
# canonical function must agree with it on every live source string.
def _old_phys_weighted_source_weight(src: str) -> float:
    s = (src or "").lower()
    if "derived" in s or "0-100" in s:
        return 0.1
    if any(k in s for k in ("forum", "timeslip", "hdforums")):
        return 0.3
    if any(
        k in s
        for k in (
            "timing-strip",
            "instrumented",
            "dragy",
            "consumer news",
            "mcn",
            "don canet",
            "carlsbad",
        )
    ):
        return 1.0
    if any(
        k in s
        for k in (
            "fastestlaps",
            "motorbikecatalog",
            "motorbike catalog",
            "accelerationtimes",
            "bikewale",
            "motostatz",
        )
    ):
        return 0.5
    if any(k in s for k in ("cycle world", "sport rider", "motorcyclist", "magazine")):
        return 0.7
    return 0.5


class TestCanonicalWeights(unittest.TestCase):
    def test_motostatz_is_aggregator(self):
        # Bare 'motostatz' token is an aggregator DB, not a first-party lab.
        self.assertEqual(source_weight("MotoStatz 2020"), 0.5)
        self.assertEqual(source_quality("MotoStatz aggregate"), (0.5, "aggregator"))

    def test_motostatz_dragy_is_instrumented(self):
        # The near-universal 'MotoStatz (Dragy, ... instrumented)' rows carry
        # the dragy/instrumented token and score at the instrumented tier.
        self.assertEqual(
            source_weight("MotoStatz 2021 (Dragy, stock instrumented)"), 1.0
        )

    def test_instrumented_keyword_is_one(self):
        self.assertEqual(source_weight("Dragy GPS 2021 (stock instrumented)"), 1.0)
        self.assertEqual(source_quality("instrumented lab test")[0], 1.0)

    def test_derived_keyword_is_low(self):
        self.assertEqual(source_weight("DERIVED (0-100 x 1.6)"), 0.1)

    def test_magazine_keyword(self):
        self.assertEqual(source_weight("Cycle World 2015"), 0.7)

    def test_unknown_source_is_canonical_default(self):
        # Canonical default (phys_weighted_sweep semantics) is 0.5, NOT the old
        # sweep_lib 0.4.
        self.assertEqual(source_weight("Some Random Blog 2024"), 0.5)
        self.assertEqual(source_quality("Some Random Blog 2024"), (0.5, "unknown"))

    def test_estimated_not_folded_as_derived(self):
        # 'estimated' MUST NOT demote aggregator rows to derived (would drift
        # the published headline).
        self.assertEqual(source_weight("MotorBikeCatalog 1998 (estimated)"), 0.5)


class TestSharedImplementation(unittest.TestCase):
    def test_phys_weighted_uses_canonical(self):
        # phys_weighted_sweep imports the canonical scalar weight; it is the
        # very same function object, not a re-implementation.
        self.assertIs(pw.source_weight, source_weight)

    def test_source_quality_and_source_weight_agree(self):
        for probe in [
            "MotoStatz 2020",
            "MotoStatz (Dragy, stock instrumented)",
            "Cycle World 2005 (timing-strip)",
            "Sport Rider 2004",
            "DERIVED (0-100 x 1.6)",
            "HDForums timeslip 2021",
            "Some Random Blog 2024",
        ]:
            self.assertEqual(source_quality(probe)[0], source_weight(probe), probe)

    def test_phys_and_lib_return_same_weight(self):
        for probe in [
            "MotoStatz 2018",
            "MCN 2011 (Bruce Dunn instrumented)",
            "FastestLaps 2020",
            "Motorcyclist 2002",
        ]:
            self.assertEqual(pw.source_weight(probe), source_weight(probe), probe)


class TestZeroHeadlineDrift(unittest.TestCase):
    def test_no_drift_vs_published_logic(self):
        srcs = {row[5] for row in BENCHMARKS}
        self.assertGreater(len(srcs), 100)  # sanity: the corpus is populated
        mismatches = [
            (s, _old_phys_weighted_source_weight(s), source_weight(s))
            for s in srcs
            if _old_phys_weighted_source_weight(s) != source_weight(s)
        ]
        self.assertEqual(
            mismatches,
            [],
            f"Headline drift on {len(mismatches)} source(s): {mismatches[:5]}",
        )


if __name__ == "__main__":
    unittest.main()
