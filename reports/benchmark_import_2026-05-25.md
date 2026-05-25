# Benchmark Import Session — 2026-05-25

## Overview

This session addressed the DISPATCH_INBOX `[urgent]` item: a matcher specificity bug
where shorter benchmark model keys (e.g. "Ninja H2") shadow longer ones ("Ninja H2 SX")
via first-match-wins iteration. After fixing the bug, one new high-confidence instrumented
benchmark was added (Kawasaki Ninja H2 SX 2018), and 13 regression tests were added to
`tests/test_validation.py`.

---

## Matcher Specificity Bug

### Root cause

`scripts/validation_sweep.py::run_sweep` iterated `BENCHMARKS` linearly for each catalog
spec. `_model_match` uses token-subset semantics: every pattern token must appear in the
spec string. Because `{ninja, h2} subset {ninja, h2, sx}`, the "Ninja H2" (2015, 9.62s)
benchmark matched "Ninja H2 SX (2018-2023)" catalog rows before any H2 SX-specific entry.

`scripts/sweep_with_clusters.py::run_sweep` had the same issue: `bench_map.items()` was
iterated in arbitrary dict-insertion order; the H2 key was inserted before H2 SX.

### Fix applied

Both files now sort benchmark candidates by model-token-count descending before iterating:

- `scripts/validation_sweep.py`: `_benchmarks_sorted` built from `sorted(BENCHMARKS, key=...)` 
  inserted at the top of `run_sweep`; the inner loop uses `_benchmarks_sorted`.
- `scripts/sweep_with_clusters.py`: `bench_map_sorted` built from 
  `sorted(bench_map.items(), key=..., reverse=True)` after `bench_map` is built;
  the outer loop uses `bench_map_sorted`.

Effect: "Ninja H2 SX" (3 tokens) is now tried before "Ninja H2" (2 tokens).
"Ninja H2 SX (2018-2023)" catalog rows bind to the new H2 SX 10.04s benchmark.
"Ninja H2 (2015-2022)" catalog rows still bind to the original 9.62s benchmark.
"Z H2 (2020-2025)" catalog rows bind to the Z H2 9.95s benchmark (unchanged).

---

## New Benchmarks Added

### Kawasaki Ninja H2 SX 2018 — Cycle World 10.04s @ 144 mph (231.7 km/h)

- **Source:** Cycle World 2018 "Best Open-Class Streetbike" feature
- **URL:** https://www.cycleworld.com/best-open-class-streetbike-2018-kawasaki-ninja-h2-sx-se/
- **Method:** Timing strip at a licensed drag strip (same Cycle World methodology as
  the Ninja H2, Z H2, ZX-14R, S 1000 RR, and other entries already in BENCHMARKS)
- **Stock:** Yes — stock 998 cc supercharged I4, detuned vs track H2 (150 hp vs 200 hp)
- **Year range match:** Catalog entry `Kawasaki Ninja H2 SX (2018-2023)` — year_hint=2018
  matches cleanly
- **Consistency:** 10.04s for the detuned sport-tourer vs 9.62s for the full-power
  track H2 is physically consistent with the ~50 hp power delta and heavier chassis

---

## Regression Tests Added

`tests/test_validation.py` — new `TestMatcherSpecificity` class (13 tests).
Tests pin correct binding for Z H2 / Ninja H2 / Ninja H2 SX / Ninja H2R collision pairs.

All 44 tests in `test_validation.py` pass (31 pre-existing + 13 new).

---

## Files Touched

- `scripts/validation_sweep.py` — matcher specificity sort + new H2 SX benchmark in BENCHMARKS
- `scripts/sweep_with_clusters.py` — matcher specificity sort (parallel fix)
- `tests/test_validation.py` — 13 new TestMatcherSpecificity regression tests
- `reports/benchmark_import_2026-05-25.md` — this report
