"""Regression tests for the canonical benchmark source-quality classifier.

Roadmap A4-27 consolidated two divergent source-quality functions
(``scripts/sweep_lib.source_quality`` and a local
``scripts/phys_weighted_sweep.source_weight``) onto a single implementation
hosted in ``scripts/sweep_lib``. These tests pin:

* the canonical weight for representative source strings,
* that ``phys_weighted_sweep`` now shares the exact same implementation, and
* no unintended drift — the canonical scalar weight reproduces the OLD
  ``phys_weighted_sweep.source_weight`` for every source string in the live
  ``BENCHMARKS`` corpus except the 14 the 2026-10 epoch reclassified on
  purpose (``EPOCH_REWEIGHTED``).
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

    def test_estimated_scores_as_estimate(self):
        # 2026-10 epoch: an '(estimated)' figure is an estimate whatever site
        # hosts it, so it carries the derived/estimate weight (was 0.5).
        self.assertEqual(source_weight("MotorBikeCatalog 1998 (estimated)"), 0.1)


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


# The 2026-10 epoch reclassified exactly these corpus sources on purpose
# (estimates -> 0.1; a figure measured on a sibling platform and bound to this
# bike -> capped at 0.5). Any OTHER weight change is unintended drift.
EPOCH_REWEIGHTED = {
    "Corner Speed 2026 prose estimate (low-12s @ 110 mph; Cycle-World-dyno-referenced, not a timed run)": (
        0.5,
        0.1,
    ),
    "Cycle World (F3 800 platform 10.5s; RR up-spec 147hp)": (0.7, 0.5),
    "Duke 390 baseline (Motorcycle Consumer News, RC adds ~\u22120.15s for fairing)": (
        1.0,
        0.5,
    ),
    "GSX-S1000 platform 10.6s (Sport Rider); GT sport-tourer, 150hp I4": (0.7, 0.5),
    "MotoStatz (Dragy, 890 LC8c platform; SMT heavier supermoto-tourer)": (1.0, 0.5),
    "MotoStatz (Dragy, Multistrada V4 1158 platform; RS lighter)": (1.0, 0.5),
    "MotoStatz (Dragy, RC 390 platform; Gen3 399cc engine)": (1.0, 0.5),
    "MotoStatz (Dragy, Street Triple 765 RS platform; R ~10hp down)": (1.0, 0.5),
    "MotoStatz (Dragy, Streetfighter V4 1103 platform, 149 mph trap)": (1.0, 0.5),
    "MotoStatz (Dragy, Tuono 660 platform, 120 mph trap)": (1.0, 0.5),
    "MotoStatz 2022 (Dragy, XSR900 CP3 platform, 125.5 mph trap)": (1.0, 0.5),
    "MotoStatz 2022 (Dragy, Z650 platform, 105 mph trap)": (1.0, 0.5),
    "MotorBikeCatalog (estimated 1991 MC21)": (0.5, 0.1),
    "MotorBikeCatalog 1998 (estimated)": (0.5, 0.1),
}


class TestZeroHeadlineDrift(unittest.TestCase):
    def test_only_the_epoch_reclassification_drifts(self):
        srcs = {row[5] for row in BENCHMARKS}
        self.assertGreater(len(srcs), 100)  # sanity: the corpus is populated
        mismatches = {
            s: (_old_phys_weighted_source_weight(s), source_weight(s))
            for s in srcs
            if _old_phys_weighted_source_weight(s) != source_weight(s)
        }
        self.assertEqual(mismatches, EPOCH_REWEIGHTED)


if __name__ == "__main__":
    unittest.main()
