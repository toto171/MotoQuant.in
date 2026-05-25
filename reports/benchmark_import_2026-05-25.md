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

---

## Seventh Pass (later 2026-05-25 session) — +2 MotoStatz Dragy benchmarks

Two additional high-confidence MotoStatz Dragy-instrumented quarter-mile
benchmarks added in a follow-up benchmark-import pass. Source bar identical to
the existing MotoStatz Dragy entries (CBR 600RR PC40B, Ninja 1000SX, BMW S1000R,
CBR650R, Monster 937, Tracer 9 GT, ZX-9R F-gen, RS 660, 890 Duke R, 790 Duke,
XSR900). MotoStatz's site-wide "How We Test Motorcycles" page
(https://motostatz.com/how-we-test-motorcycles/) explicitly states the
publication uses Dragy GPS as the standard measurement device across every
review on the site — minimum 20-30 runs per bike, precision to 1/100s. That
confirms Dragy methodology for the two entries below even when the individual
article snippet does not always quote "Dragy" inline.

### Added benchmarks (2)

| # | Manufacturer | Model | Year | ET (s) | Trap (km/h) | Source |
|---|---|---|---|---|---|---|
| 1 | Honda | VFR800F Interceptor | 2016 | 11.14 | 198 | MotoStatz (Dragy, stock) |
| 2 | Aprilia | Tuono 660 | 2021 | 11.33 | 193 | MotoStatz (Dragy, stock) |

#### 1. Honda VFR800F Interceptor

- **URL:** https://motostatz.com/honda-vfr800-acceleration-top-speed/
- **Methodology:** https://motostatz.com/how-we-test-motorcycles/
- **Reported:** 11.14s @ 123 mph
- **Stored:** 11.14s @ 198 km/h (123 × 1.60934 = 197.95, rounded to 198)
- **Catalog binding:** `Honda | VFR800F Interceptor` (2014-2021, 782 cc V4
  VTEC, 105 hp). `find_spec("Honda", "VFR800F Interceptor", 2016)` returns
  the expected row.
- **Cluster fit:** litre-sport-touring band; trap of 123 mph (~198 km/h) is
  consistent with a 105 hp V4 sport-tourer.
- **Matcher specificity:** No collision risk. "VFR800F" tokens are unique in
  the catalog; the older RC30/VFR750R has distinct model tokens.

#### 2. Aprilia Tuono 660

- **URL:** https://motostatz.com/aprilia-tuono-660-top-speed-acceleration/
- **Reported:** 11.33s @ 120 mph (article snippet explicitly says "measured
  with a Dragy GPS device")
- **Stored:** 11.33s @ 193 km/h (120 × 1.60934 = 193.12, rounded to 193)
- **Catalog binding:** `Aprilia | Tuono 660` (2021-2026, 659 cc parallel-twin,
  100 hp). `find_spec("Aprilia", "Tuono 660", 2021)` returns the expected row.
- **Cluster fit:** Internally consistent with the existing RS 660 2021 entry
  (11.24s @ 200 km/h). Tuono is the naked variant of the same 659 cc platform:
  +3 kg, no fairing → Δ+0.09s ET, –7 km/h trap fits naked-vs-sport delta.
- **Matcher specificity:** Tuono 660 Factory exists as a separate catalog
  entry (2022-2026, same engine). Year-match path with year_hint=2021 routes
  to the base Tuono 660 first; the new specificity sort (3-token "Tuono 660
  Factory" sorts before 2-token "Tuono 660") would also help if Factory had
  its own benchmark in the future.

### Investigated but rejected this pass (4)

| Bike | Reason |
|---|---|
| Yamaha FZS 1000 Fazer 2001-2005 | MotoStatz 10.78s @ 131 mph (Dragy via site methodology) BUT not in `ALL_KNOWN_BIKES` — only the 2006+ FZ1 Fazer is present. Queued for catalog expansion. |
| Yamaha FZ8 / FZ8N | MotoStatz 11.45s @ 121 mph (Dragy). Not in catalog. Queued. |
| Honda CBR1100XX Super Blackbird | MotoStatz 10.38s @ 137.8 mph — strong "Dragy 60-130 mph time" inline citation. NOT in catalog. Queued as a high-value historical add. |
| Ducati Multistrada V4 | MotoStatz 10.82s @ 131 mph. Catalog present. Article snippet did not explicitly quote "Dragy" inline; while the site-wide methodology page covers it, chose conservative skip vs the two adds that have stronger evidence. |

### Queue for catalog-expansion agent

Three popular bikes with verified instrumented Dragy data exist but the
catalog rows do not. Adding the catalog rows below would let a future
benchmark-import pass bind these immediately:

1. **Yamaha FZS 1000 Fazer 2001-2005** (RN061, 998 cc I4, 143 hp) — MotoStatz
   10.78s @ 131 mph.
2. **Yamaha FZ8 / FZ8N 2010-2013** (779 cc I4, 106 hp) — MotoStatz 11.45s @
   121 mph.
3. **Honda CBR1100XX Super Blackbird 1997-2007** (1137 cc I4, 152-164 hp) —
   MotoStatz 10.38s @ 137.8 mph.

### Sweep delta (seventh-pass adds only)

- BENCHMARKS list: **106 → 108** (+2 net-new on top of the morning H2 SX add)
- Both new entries verified to bind to `ALL_KNOWN_BIKES` via `find_spec()`
- No physics regression — benchmarks are observational reference data;
  simulator code unchanged.

### Files touched (seventh-pass adds)

- `scripts/validation_sweep.py` — BENCHMARKS list +2 entries (VFR800F
  Interceptor + Tuono 660) with full inline citations.

