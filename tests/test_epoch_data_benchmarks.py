"""2026-10 data epoch — benchmark corpus, source classifier and binding rule.

Pins:

* source weights for the problem strings (estimates, platform/baseline
  substitutions, second-hand Consumer News, a 'Cycle World' token inside an
  estimate's citation);
* the RZV500R row is rebound to the RD500LC export spec;
* the epoch binding rule (``sweep_lib.bind_benchmark_for_record``,
  ``policy="epoch"``): highest-weight in-range entry wins; out-of-year
  fallbacks only through ``SAME_PLATFORM_FALLBACKS``. The ``"legacy"`` rule
  stays available (it reproduces the published 2026-08-08 headline), so a
  metric change is always reportable under both rules.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES  # noqa: E402
from scripts.sweep_lib import (  # noqa: E402
    SAME_PLATFORM_FALLBACKS,
    bind_benchmark_for_record,
    build_bench_map,
    find_spec_for_benchmark,
    source_quality,
    source_quality_legacy,
    source_weight,
)
from scripts.validation_sweep import BENCHMARKS  # noqa: E402


def _row(mfr, model, year):
    hits = [b for b in BENCHMARKS if (b[0], b[1], b[2]) == (mfr, model, year)]
    assert len(hits) == 1, (mfr, model, year, len(hits))
    return hits[0]


# ── classifier ────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "src,weight,label",
    [
        # estimates — whatever outlet the citation names
        ("MotorBikeCatalog (estimated 1991 MC21)", 0.1, "estimate"),
        ("MotorBikeCatalog 1998 (estimated)", 0.1, "estimate"),
        ("Cycle World estimate from dyno figures", 0.1, "estimate"),
        # platform / baseline substitutions are indirect evidence -> <= 0.5
        (
            "MotoStatz (Dragy, RC 390 platform; Gen3 399cc engine)",
            0.5,
            "platform_substitution",
        ),
        (
            "MotoStatz (Dragy, Multistrada V4 1158 platform; RS lighter)",
            0.5,
            "platform_substitution",
        ),
        (
            "Duke 390 baseline (Motorcycle Consumer News, RC adds ~−0.15s for fairing)",
            0.5,
            "platform_substitution",
        ),
        (
            "GSX-S1000 platform 10.6s (Sport Rider); GT sport-tourer, 150hp I4",
            0.5,
            "platform_substitution",
        ),
        # a substitution never RAISES a weight
        ("Versys 1000 platform (1043 I4, owner timeslip)", 0.3, "forum_or_timeslip"),
        # second-hand Consumer News (hyphenated label) is magazine tier, explicitly
        (
            "Motorcycle Consumer-News stock QM test via Wikipedia VRSC (magazine)",
            0.7,
            "magazine",
        ),
        (
            "Motorcycle Consumer-News data quoted by zeroto60times (magazine)",
            0.7,
            "magazine",
        ),
        # unchanged tiers
        ("Motorcycle Consumer News 2012", 1.0, "instrumented"),
        ("MotoStatz 2021 (Dragy, stock instrumented)", 1.0, "instrumented"),
        ("DERIVED (0-100 ~9-10s x1.6 2V VBox, IndianAutosBlog)", 0.1, "derived"),
        ("Cycle World 2022", 0.7, "magazine"),
        ("MotoStatz 2020", 0.5, "aggregator"),
        ("HDForums timeslip 2021", 0.3, "forum_or_timeslip"),
    ],
)
def test_source_quality(src, weight, label):
    assert source_quality(src) == (weight, label)
    assert source_weight(src) == weight


def test_legacy_classifier_reproduces_the_pre_epoch_misfires():
    """``source_quality_legacy`` is the frozen pre-epoch rule (used only to
    report the headline under both rules)."""
    assert source_quality_legacy("MotorBikeCatalog 1998 (estimated)")[0] == 0.5
    assert (
        source_quality_legacy("MotoStatz (Dragy, RC 390 platform; Gen3 399cc engine)")[
            0
        ]
        == 1.0
    )
    assert (
        source_quality_legacy(
            "Corner Speed 2026 (Cycle World dyno-referenced, low-12s @ 110 mph)"
        )[0]
        == 0.7
    )


def test_zx4rr_row_is_an_estimate():
    _, _, _, et, _, src = _row("Kawasaki", "Ninja ZX-4RR", 2023)
    assert et == 12.00
    assert source_quality(src) == (0.1, "estimate")


def test_daytona_675_row_scores_as_the_aggregator_figure_it_is():
    _, _, _, et, _, src = _row("Triumph", "Daytona 675", 2013)
    assert et == 10.70
    assert source_weight(src) == 0.5


def test_corpus_weight_changes_are_exactly_the_reviewed_set():
    """Every corpus row whose weight differs between the legacy and epoch
    classifiers (so the headline metric drift is fully accounted for). The
    Daytona 675 and ZX-4RR LABELS were also corrected (data fixes, pinned
    above); the ZX-4RR one still differs under the legacy classifier."""
    changed = {
        (b[0], b[1], b[2])
        for b in BENCHMARKS
        if source_quality(b[5])[0] != source_quality_legacy(b[5])[0]
    }
    assert changed == {
        ("Honda", "NSR250R", 1990),
        ("Aprilia", "RS250", 1996),
        ("Kawasaki", "Ninja ZX-4RR", 2023),
        ("KTM", "RC 390", 2017),
        ("KTM", "RC 390 Gen 3", 2024),
        ("Kawasaki", "Z650RS", 2022),
        ("Yamaha", "XSR900 GP", 2024),
        ("Ducati", "Streetfighter V4S", 2024),
        ("Ducati", "Streetfighter V4 SP", 2022),
        ("Aprilia", "Tuono 660 Factory", 2022),
        ("Triumph", "Street Triple 765 R", 2023),
        ("Ducati", "Multistrada V4 RS", 2024),
        ("KTM", "890 SMT", 2023),
        ("MV Agusta", "F3 RR", 2024),
        ("Suzuki", "GSX-S1000GT", 2022),
    }


# ── corpus rebinding ──────────────────────────────────────────────────────


def test_rzv500r_benchmark_rebound_to_rd500lc():
    assert not [b for b in BENCHMARKS if "RZV500R" in b[1]]
    b = _row("Yamaha", "RD500LC", 1985)
    spec = find_spec_for_benchmark(b[0], b[1], b[2], ALL_KNOWN_BIKES)
    assert spec is not None and spec.model_name == "RD500LC"
    assert spec.peak_power_hp >= 85  # the export engine, not the 64 hp RZV


# ── binding rule ──────────────────────────────────────────────────────────


def _bm(rows):
    return build_bench_map(rows)


def test_highest_weight_in_range_entry_wins():
    rows = [
        ("Testco", "Racer 1", 2000, 10.50, 230, "Sport Rider 2000"),  # 0.7
        ("Testco", "Racer 1", 2003, 10.62, 220, "MotoStatz 2025 (Dragy, stock)"),  # 1.0
    ]
    epoch = bind_benchmark_for_record("Testco", "Racer 1", 2000, 2003, _bm(rows))
    legacy = bind_benchmark_for_record(
        "Testco", "Racer 1", 2000, 2003, _bm(rows), policy="legacy"
    )
    assert epoch[0] == 10.62
    assert legacy[0] == 10.50  # first in-range entry


def test_out_of_year_fallback_needs_the_allowlist():
    rows = [("Testco", "Racer 1", 2005, 10.0, 230, "Cycle World 2005")]
    assert bind_benchmark_for_record("Testco", "Racer 1", 2015, 2018, _bm(rows)) is None
    legacy = bind_benchmark_for_record(
        "Testco", "Racer 1", 2015, 2018, _bm(rows), policy="legacy", with_meta=True
    )
    assert legacy[:2] == (10.0, 230) and legacy[4] is False


def test_unknown_policy_rejected():
    with pytest.raises(ValueError):
        bind_benchmark_for_record("a", "b", 2000, 2001, {}, policy="nearest")


def test_real_corpus_bindings():
    bm = build_bench_map(BENCHMARKS)

    def bind(mfr, model, policy="epoch", year=None):
        s = [
            x
            for x in ALL_KNOWN_BIKES
            if x.manufacturer == mfr
            and x.model_name == model
            and (year is None or x.year_from == year)
        ]
        assert len(s) == 1, (mfr, model, len(s))
        s = s[0]
        return bind_benchmark_for_record(
            mfr, model, s.year_from, s.year_to, bm, policy=policy, with_meta=True
        )

    # ZX-9R 2000-03: the instrumented 2003 row now beats the 0.7 2000 row
    assert bind("Kawasaki", "Ninja ZX-9R")[0] == 10.62
    assert bind("Kawasaki", "Ninja ZX-9R", "legacy")[0] == 10.50
    # Hayabusa 25th (a Gen3): allowlisted onto the 2021 Gen3 row, not 2008 Gen2
    assert bind("Suzuki", "Hayabusa 25th Anniversary")[3] == 2021
    assert bind("Suzuki", "Hayabusa 25th Anniversary", "legacy")[3] == 2008
    # different machines are now unmatched
    for mfr, model in [
        ("BMW", "R 12 nineT"),
        ("Ducati", "Panigale V2 (2025-2026)"),
        ("Indian", "101 Scout (2025-2026)"),
        ("Triumph", "Rocket 3 Storm R (2024-2026)"),
    ]:
        assert bind(mfr, model) is None, (mfr, model)
        assert bind(mfr, model, "legacy") is not None, (mfr, model)
    # Gen1 Duke 390 (2013-16) no longer borrows the 2019 Gen2 test
    assert bind("KTM", "Duke 390", year=2013) is None
    assert bind("KTM", "Duke 390", "legacy", year=2013)[3] == 2019
    # allowlisted same-platform variants keep their fallback
    assert bind("Aprilia", "RS 660 Extrema")[0] == 11.24
    assert bind("Kawasaki", "Ninja H2 SX SE+")[3] == 2018


def test_allowlist_entries_resolve():
    """Every SAME_PLATFORM_FALLBACKS key names a real catalog bike and every
    allowed (model, year) exists in BENCHMARKS — guards against typos that
    would silently unmatch a bike."""
    bench = {(b[0].lower(), b[1].lower(), b[2]) for b in BENCHMARKS}
    import re

    names = {
        (
            s.manufacturer.lower(),
            re.sub(r"\s*\(\d{4}(?:-\d{4})?\)\s*$", "", s.model_name).lower(),
        )
        for s in ALL_KNOWN_BIKES
    }
    for (mfr, model), allowed in SAME_PLATFORM_FALLBACKS.items():
        assert (mfr, model) in names, (mfr, model)
        for bmodel, byear in allowed:
            assert (mfr, bmodel, byear) in bench, (mfr, bmodel, byear)
