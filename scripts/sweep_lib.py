"""sweep_lib.py — shared model-matching helpers for the sweep drivers.

Single source of truth for the word-boundary token matcher, the
specificity score, and the directional benchmark<->spec pickers used by
``validation_sweep.py``, ``sweep_with_clusters.py``, ``benchmark_sweep.py``
and ``topspeed_sweep.py``. Before this module each driver carried its own
copy with drifted semantics (case-sensitivity, dot-splitting,
first-match-wins vs most-specific).

Two intentionally distinct year policies coexist and are both preserved:

* ``best_benchmark_match`` (validation_sweep policy) — STRICT year-range
  filter; a spec with no in-range benchmark gets no match at all
  (conservative-no-match, pinned by
  ``tests/test_validation.py::TestProductionMatcherSpecificity``).
* ``bind_benchmark_for_record`` (sweep_with_clusters policy) — prefers an
  in-range benchmark year but falls back to the group's first entry when
  none is in range, so cluster summaries keep older-generation targets.
"""

from __future__ import annotations

import re

__all__ = [
    "wb_match",
    "model_specificity_score",
    "best_benchmark_match",
    "build_bench_map",
    "bind_benchmark_for_record",
    "find_spec_for_benchmark",
    "source_quality",
]

_SPLIT_RE = re.compile(r"[\s\-\.]+")


def wb_match(pattern: str, text: str) -> bool:
    """Word-boundary token-set match, case-insensitive.

    Splits both strings on space / hyphen / dot and checks every pattern
    token appears as a standalone token in ``text``. Avoids the YZF-R1 vs
    YZF-R15 substring collision: ``r1`` is not a token of ``YZF-R15``.
    """
    tokens = [t for t in _SPLIT_RE.split(pattern.lower()) if t]
    text_tokens = {t for t in _SPLIT_RE.split(text.lower()) if t}
    return all(t in text_tokens for t in tokens)


def model_specificity_score(pattern: str) -> int:
    """Number of distinct tokens in pattern after splitting on space /
    hyphen / dot. Higher = more specific: ``"Ninja H2 SX"`` (3) outranks
    ``"Ninja H2"`` (2), so an H2 SX catalog row binds to the H2 SX
    benchmark rather than the plain H2 one.
    """
    return len([t for t in _SPLIT_RE.split(pattern) if t])


def best_benchmark_match(spec, benchmarks):
    """Among all benchmarks matching ``spec`` (manufacturer equality +
    word-boundary model tokens + STRICT year-range filter), return the
    most-specific one (highest token-count in the benchmark model).
    Ties broken by first occurrence. Returns the matching tuple
    ``(bmfr, bmodel, byear, tgt_et, tgt_trap, src)`` or ``None``.

    Score-and-pick instead of sort-then-first-match, so the matcher is
    robust against benchmark insertion-order (DISPATCH_INBOX 2026-05-25
    Option 2).
    """
    best = None
    best_score = -1
    spec_mfr = spec.manufacturer.lower()
    for entry in benchmarks:
        bmfr, bmodel, byear, _tgt_et, _tgt_trap, _src = entry
        if spec_mfr != bmfr.lower():
            continue
        if not wb_match(bmodel, spec.model_name):
            continue
        if byear < spec.year_from or byear > (spec.year_to or spec.year_from + 3):
            continue
        score = model_specificity_score(bmodel)
        if score > best_score:
            best = entry
            best_score = score
    return best


def build_bench_map(benchmarks) -> dict:
    """Group BENCHMARKS rows by lowercase (manufacturer, model) for
    ``bind_benchmark_for_record``."""
    bench_map: dict = {}
    for bmfr, bmodel, byear, tgt_et, tgt_trap, src in benchmarks:
        bench_map.setdefault((bmfr.lower(), bmodel.lower()), []).append(
            (byear, tgt_et, tgt_trap, src)
        )
    return bench_map


def bind_benchmark_for_record(manufacturer, model, year_from, year_to, bench_map):
    """sweep_with_clusters binding policy: scan every benchmark group that
    passes manufacturer + word-boundary model filters, prefer entries whose
    year falls inside [year_from, year_to] (falling back to the group's
    first entry otherwise), and pick the most-specific model pattern.
    In-range matches always beat out-of-range fallbacks regardless of
    specificity. Returns ``(tgt_et, tgt_trap, src)`` or ``None``.
    """
    m_lo = (manufacturer or "").lower()
    mod_lo = (model or "").lower()
    yf = year_from or 0
    yt = year_to or yf

    best_match = None
    best_score = -1
    best_in_range = False
    for (bm, bmod), entries in bench_map.items():
        if not (wb_match(bm, m_lo) and wb_match(bmod, mod_lo)):
            continue
        in_range_entry = None
        for byear, tgt_et, tgt_trap, src in entries:
            if yf <= byear <= yt or (not yt and yf == byear):
                in_range_entry = (tgt_et, tgt_trap, src)
                break
        fallback_entry = (entries[0][1], entries[0][2], entries[0][3])
        chosen_entry = in_range_entry if in_range_entry is not None else fallback_entry
        entry_in_range = in_range_entry is not None
        score = model_specificity_score(bmod)

        if entry_in_range and not best_in_range:
            best_match = chosen_entry
            best_score = score
            best_in_range = True
        elif entry_in_range == best_in_range and score > best_score:
            best_match = chosen_entry
            best_score = score
    return best_match


def find_spec_for_benchmark(mfr: str, model: str, year: int, specs):
    """Locate the spec in ``specs`` that best matches a benchmark row:
    manufacturer equality (case-insensitive) + word-boundary model tokens +
    year-range filter, then pick the TIGHTEST fit — the spec whose model
    name carries the fewest tokens beyond the benchmark pattern (an exact
    token-set match wins). Ties broken by first occurrence.

    Replaces the old first-match-wins scan, where a short benchmark
    pattern could bind to whichever superset-named spec happened to come
    first in catalog order.
    """
    mfr_lo = mfr.lower()
    pattern_score = model_specificity_score(model)
    best = None
    best_surplus = None
    for spec in specs:
        if spec.manufacturer.lower() != mfr_lo:
            continue
        if not wb_match(model, spec.model_name):
            continue
        if year < spec.year_from or year > (spec.year_to or spec.year_from + 3):
            continue
        surplus = model_specificity_score(spec.model_name) - pattern_score
        if best is None or surplus < best_surplus:
            best = spec
            best_surplus = surplus
    return best


# Source-quality weights (April 30 decision: weighted by source quality).
# Heuristic keyword parse of the benchmark source string; anything
# containing "DERIVED" / "0-100" / "estimated" is heuristically-derived.
def source_quality(src: str) -> tuple[float, str]:
    """Return (weight, label) for a benchmark source string."""
    s = src.lower()
    if "derived" in s or "0-100" in s or "estimated" in s:
        return (0.1, "derived")
    if "forum" in s or "community" in s or "logged" in s or "timeslip" in s:
        # Owner timeslip / forum claim — better than derived but not lab
        return (0.3, "forum_or_timeslip")
    if any(k in s for k in ("instrumented", "motostatz", "dragy", "vbox")):
        return (1.0, "instrumented")
    if any(k in s for k in ("cycle world", "sport rider", "mcn", "consumer news")):
        return (0.7, "magazine")
    if any(
        k in s
        for k in ("fastestlaps", "motorbikecatalog", "bikewale", "accelerationtimes")
    ):
        return (0.5, "aggregator")
    return (0.4, "unknown")
