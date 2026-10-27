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
* ``bind_benchmark_for_record`` (sweep_with_clusters policy). Two binding
  rules, selected with ``policy=``:

  - ``"epoch"`` (default since the 2026-10 data epoch): among a group's
    IN-RANGE entries the highest-weight one wins (ties: first listed); an
    out-of-range fallback binds ONLY through the explicit same-platform
    allowlist ``SAME_PLATFORM_FALLBACKS`` (catalog model -> the benchmark
    model + year it may borrow). Every other out-of-year bike is unmatched.
  - ``"legacy"``: the pre-epoch rule (first in-range entry wins; with none in
    range, the group's FIRST entry binds whatever its year/generation). This
    reproduces the published 2026-08-08 headline (276 matched) and is kept so
    a metric change can always be reported under both rules.
"""

from __future__ import annotations

import re

__all__ = [
    "SAME_PLATFORM_FALLBACKS",
    "wb_match",
    "model_specificity_score",
    "best_benchmark_match",
    "build_bench_map",
    "bind_benchmark_for_record",
    "find_spec_for_benchmark",
    "source_quality",
    "source_weight",
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


# Explicit same-platform out-of-year fallbacks (2026-10 data epoch). Key:
# (manufacturer, catalog model) lower-case; value: the (benchmark model,
# benchmark year) pairs the catalog bike may borrow when it has no in-range
# benchmark. "Same platform" = same engine (rated output within ~5 %) AND same
# frame generation — a trim/variant or emissions update, not a new machine.
# Reviewed 2026-10 over the 25 out-of-year fallbacks the legacy rule made;
# DELIBERATELY NOT LISTED (different machine -> now unmatched): KTM 390 Duke
# Gen3 2024 and Duke 390 Gen1 2013-16 (vs the 2019 Gen2 test), Panigale V4
# 2025 (new chassis generation), Panigale V2 2025 (890 cc vs the 955 cc 2022
# test), R 12 nineT 2024 (new frame vs the 2014 R nineT), Indian 101 Scout
# 2025 (1250 engine vs the 2015 1133), Rocket 3 Storm R 2024 (182 PS vs the
# 167 PS 2020 R), GSX-R 600 / GSX-R 750 L1 2011+ (new generation vs the K6 /
# K8 tests), Speed Triple 1050 2011-15 (new frame vs the 2005 test).
SAME_PLATFORM_FALLBACKS: dict[tuple[str, str], frozenset] = {
    # Same R155 VVA engine + Deltabox frame as the 2019 Indonesian MT-15.
    ("yamaha", "mt-15 v2"): frozenset({("mt-15", 2019)}),
    # 2019 launch bike == the 2020-24 entry (BS4 -> BS6 retune, 47 hp both).
    ("royal enfield", "interceptor 650"): frozenset({("interceptor 650", 2019)}),
    # SC82 2024 update: same 217.5 PS, same chassis family.
    ("honda", "cbr1000rr-r fireblade sp"): frozenset({("cbr1000rr-r", 2020)}),
    # Factory / Extrema = lighter-trim RS 660 (same 659 cc twin, same frame).
    ("aprilia", "rs 660 factory"): frozenset({("rs 660", 2021)}),
    ("aprilia", "rs 660 extrema"): frozenset({("rs 660", 2021)}),
    # Z H2 SE = Z H2 with Showa Skyhook + Brembo Stylema (same 998 cc SC).
    ("kawasaki", "z h2 se"): frozenset({("z h2", 2020)}),
    # The 25th Anniversary is a Gen3 (2021+) Hayabusa — borrow the 2021 Gen3
    # row, NOT the 2008 Gen2 row the legacy first-entry fallback picked.
    ("suzuki", "hayabusa 25th anniversary"): frozenset({("hayabusa", 2021)}),
    # Halcyon is a Classic 350 trim; the Goan is the Classic-350-based bobber
    # (same J-series 349 cc + frame). The bound row is DERIVED (w 0.1).
    ("royal enfield", "classic 350 halcyon"): frozenset({("classic 350", 2021)}),
    ("royal enfield", "goan classic 350"): frozenset({("classic 350", 2021)}),
    # Same 1099 cc V4 + chassis family as the 2021 RSV4 1100 Factory.
    ("aprilia", "rsv4 1100 factory fw1a"): frozenset({("rsv4 factory", 2021)}),
    # 2022 H2 SX update: same 200 PS supercharged 998 cc, same frame.
    ("kawasaki", "ninja h2 sx se+"): frozenset({("ninja h2 sx", 2018)}),
    # 2021 CP2 Euro-5 update (73.4 vs 74.8 PS), same frame; SP = trim.
    ("yamaha", "mt-07 sp"): frozenset({("mt-07", 2018)}),
    # 2022 CP4 update (166 vs 160 PS, +3.8 %), same frame; SP = trim.
    ("yamaha", "mt-10 sp"): frozenset({("mt-10", 2016)}),
    # E-Clutch = CBR650R + Honda E-Clutch actuator (same engine/frame).
    ("honda", "cbr650r e-clutch"): frozenset({("cbr650r", 2019)}),
    # Assen = Brutale 1000 RR special edition (same 998 cc I4, same frame).
    ("mv agusta", "brutale 1000 rr assen"): frozenset({("brutale 1000 rr", 2019)}),
}


def _strip_year_suffix(model: str) -> str:
    """'GSX-R 600 (2011-2024)' -> 'gsx-r 600' (lower-case)."""
    return re.sub(r"\s*\(\d{4}(?:-\d{4})?\)\s*$", "", model or "").strip().lower()


def bind_benchmark_for_record(
    manufacturer,
    model,
    year_from,
    year_to,
    bench_map,
    *,
    policy: str = "epoch",
    with_meta: bool = False,
    weight_fn=None,
):
    """Bind a catalog record to one benchmark (see the module docstring for
    the two ``policy`` rules).

    Candidate groups pass manufacturer + word-boundary model filters; an
    in-range binding always beats an out-of-range fallback, then the
    most-specific benchmark model pattern wins. Returns
    ``(tgt_et, tgt_trap, src)`` — or, with ``with_meta=True``,
    ``(tgt_et, tgt_trap, src, bench_year, in_range)`` — or ``None``.
    """
    if policy not in ("epoch", "legacy"):
        raise ValueError(f"unknown binding policy {policy!r}")
    wfn = weight_fn or source_weight
    m_lo = (manufacturer or "").lower()
    mod_lo = (model or "").lower()
    yf = year_from or 0
    yt = year_to or yf
    allowed = SAME_PLATFORM_FALLBACKS.get(
        (m_lo, _strip_year_suffix(model)), frozenset()
    )

    best_match = None
    best_score = -1
    best_in_range = False
    for (bm, bmod), entries in bench_map.items():
        if not (wb_match(bm, m_lo) and wb_match(bmod, mod_lo)):
            continue
        in_range = [e for e in entries if yf <= e[0] <= yt or (not yt and yf == e[0])]
        if in_range:
            if policy == "legacy":
                pick = in_range[0]
            else:  # highest weight wins; max() keeps the first on ties
                pick = max(in_range, key=lambda e: wfn(e[3]))
            entry_in_range = True
        elif policy == "legacy":
            pick = entries[0]
            entry_in_range = False
        else:
            fb = [e for e in entries if (bmod, e[0]) in allowed]
            if not fb:
                continue
            pick = max(fb, key=lambda e: wfn(e[3]))
            entry_in_range = False
        byear, tgt_et, tgt_trap, src = pick
        chosen_entry = (tgt_et, tgt_trap, src, byear, entry_in_range)
        score = model_specificity_score(bmod)

        if entry_in_range and not best_in_range:
            best_match = chosen_entry
            best_score = score
            best_in_range = True
        elif entry_in_range == best_in_range and score > best_score:
            best_match = chosen_entry
            best_score = score
    if best_match is None:
        return None
    return best_match if with_meta else best_match[:3]


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


# ── Canonical benchmark source-quality classifier ───────────────────────────
# Single source of truth shared by phys_weighted_sweep (which produces the
# PUBLISHED authoritative sweep) and benchmark_sweep:
#
#     instrumented 1.0 / magazine 0.7 / aggregator 0.5 / forum 0.3 / DERIVED 0.1
#     unknown -> 0.5 (aggregator-tier)
#
# 2026-10 data-epoch changes (headline reported under both old and new rules
# — see tests/test_epoch_data_benchmarks.py for the pinned strings):
#
# * ESTIMATES: a source that says "estimate"/"estimated" is an estimate, not a
#   measurement, whatever outlet it cites — weight 0.1 (derived tier). Before,
#   'MotorBikeCatalog (estimated)' stayed 0.5 and the ZX-4RR prose "low-12s"
#   row scored 0.7 because 'Cycle World' appeared inside its citation string.
# * PLATFORM SUBSTITUTION: a row whose timed bike is a sibling/platform-mate
#   ("... platform ...", "... baseline ...") is indirect evidence for this
#   catalog bike — capped at 0.5 (aggregator tier) even when the sibling run
#   was instrumented (e.g. 'MotoStatz (Dragy, RC 390 platform; Gen3 399cc)').
# * SECOND-HAND CONSUMER NEWS: 'Consumer-News' (hyphenated) is the corpus's
#   label for a Motorcycle Consumer News figure quoted second-hand (primary
#   article not located) — explicitly magazine tier 0.7. It used to land there
#   only because the hyphen missed the 'consumer news' token by accident.
#
# History (roadmap A4-27): bare 'motostatz' is aggregator-tier 0.5; the
# 'MotoStatz (Dragy, ... instrumented)' rows carry the 'dragy'/'instrumented'
# token and score 1.0. 'community'/'logged' (forum) and 'vbox' (instrumented)
# were folded in without changing any live source's weight.
_ESTIMATE_TOKENS = ("estimate",)  # matches estimate / estimated / estimates
_SUBSTITUTION_TOKENS = ("platform", "baseline")
_SUBSTITUTION_CAP = 0.5


def _base_tier(s: str) -> tuple[float, str]:
    """Outlet tier of a lower-cased source string (no estimate/substitution
    handling)."""
    # Owner timeslip / forum claim — better than derived but not lab
    if any(k in s for k in ("forum", "timeslip", "hdforums", "community", "logged")):
        return (0.3, "forum_or_timeslip")
    # Second-hand Consumer News citation (see header) — magazine tier.
    if "consumer-news" in s:
        return (0.7, "magazine")
    # Instrumented lab test (timing strip / Dragy / VBox / named test rigs)
    if any(
        k in s
        for k in (
            "timing-strip",
            "instrumented",
            "dragy",
            "vbox",
            "consumer news",
            "mcn",
            "don canet",
            "carlsbad",
        )
    ):
        return (1.0, "instrumented")
    # Aggregator database
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
        return (0.5, "aggregator")
    # Magazine road test (no explicit timing-strip)
    if any(k in s for k in ("cycle world", "sport rider", "motorcyclist", "magazine")):
        return (0.7, "magazine")
    return (0.5, "unknown")  # unknown -> aggregator-tier


def source_quality(src: str) -> tuple[float, str]:
    """Return ``(weight, label)`` for a benchmark source string.

    Ordering matters: derived/estimate signals are checked first (a
    'DERIVED (... VBox ...)' row scores 0.1, not 1.0 via its 'vbox' token),
    then forum/timeslip, then the outlet tiers; a platform/baseline
    substitution finally caps the weight at 0.5.
    """
    s = (src or "").lower()
    # 1. Heuristically-derived (0-100 x multiplier, ProfessCars estimates, ...)
    if "derived" in s or "0-100" in s:
        return (0.1, "derived")
    # 2. Explicit estimate (prose / aggregator estimate) — not a measurement
    if any(k in s for k in _ESTIMATE_TOKENS):
        return (0.1, "estimate")
    w, label = _base_tier(s)
    # 3. Platform / baseline substitution — indirect evidence for this bike
    if w > _SUBSTITUTION_CAP and any(k in s for k in _SUBSTITUTION_TOKENS):
        return (_SUBSTITUTION_CAP, "platform_substitution")
    return (w, label)


def source_quality_legacy(src: str) -> tuple[float, str]:
    """The pre-2026-10 classifier, verbatim — kept ONLY so the headline can
    be reported under both the old and the new weighting rules."""
    s = (src or "").lower()
    if "derived" in s or "0-100" in s:
        return (0.1, "derived")
    if any(k in s for k in ("forum", "timeslip", "hdforums", "community", "logged")):
        return (0.3, "forum_or_timeslip")
    if any(
        k in s
        for k in (
            "timing-strip",
            "instrumented",
            "dragy",
            "vbox",
            "consumer news",
            "mcn",
            "don canet",
            "carlsbad",
        )
    ):
        return (1.0, "instrumented")
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
        return (0.5, "aggregator")
    if any(k in s for k in ("cycle world", "sport rider", "motorcyclist", "magazine")):
        return (0.7, "magazine")
    return (0.5, "unknown")


def source_weight(src: str) -> float:
    """Canonical scalar source weight — ``source_quality(src)[0]``.

    This is the function phys_weighted_sweep imports; it produces the published
    authoritative sweep.
    """
    return source_quality(src)[0]
