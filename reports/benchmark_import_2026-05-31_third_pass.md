# Benchmark Import — 2026-05-31 (third pass)

**Agent:** benchmark-import
**Session:** mq-session-1780194644-643
**Working branch:** main (clone in /tmp/mq-session-1780194644-643/repo)

## Summary

- **5 new instrumented benchmarks added** to `scripts/validation_sweep.py::BENCHMARKS`. All sourced from the Cycle World / Sport Rider sportbike-performance-numbers archive (https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/) — the same canonical timing-strip table backing 25+ existing entries in the BENCHMARKS list.
- **1 urgent inbox item resolved**: Rocket 3 R 2020 trap-speed transcription error fixed (226 km/h → 203 km/h, ET 10.50 → 10.56). See DISPATCH_INBOX.md DONE entry.
- **Reference baselines preserved EXACTLY**: K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s, Δ +0.0000s on all three.
- **Overall metrics improved**: bias closer to zero (+0.045 → +0.037s), mean|Δ| slightly improved (0.323 → 0.321s), matched-N grew 162 → 167.

## New benchmarks

| # | Manufacturer | Model | Year | ET (s) | Trap (km/h) | Catalog row bound | Source |
|---|---|---|---|---|---|---|---|
| 1 | Buell | 1125R | 2008 | 10.45 | 215 | 1125R (2008-2010) | Cycle World 2008, timing-strip (133.9 mph) |
| 2 | MV Agusta | F3 800 | 2014 | 10.62 | 216 | F3 800 (2014-2025) | Cycle World 2014, timing-strip (134.5 mph) |
| 3 | KTM | 1190 RC8 R | 2010 | 10.06 | 231 | 1190 RC8 R (2009-2013) | Cycle World 2010, timing-strip (143.36 mph) |
| 4 | Kawasaki | Ninja 1000 | 2011 | 11.30 | 199 | Ninja 1000 (Z1000SX) (2011-2019) | Cycle World 2011, timing-strip (123.46 mph) |
| 5 | Yamaha | FZ6 | 2004 | 11.53 | 189 | FZ6 Fazer (2004-2009) | Cycle World 2004, timing-strip (117.4 mph) |

Source URL (single canonical citation for all five):
https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/

Each entry verified via:
1. Existence check against current BENCHMARKS list — no collisions with existing entries.
2. Catalog binding probe via `_model_match()` + year-range filter — every entry binds to exactly one catalog row.
3. mph→km/h conversion rounded to nearest integer for trap.
4. Inline citation comment explains generation, source URL, and cluster-fit reasoning.

## Inbox item resolved: Rocket 3 R 2020 transcription fix

**Old (line 123):** `("Triumph", "Rocket 3 R", 2020, 10.50, 226, "Cycle World 2020")`
**New:** `("Triumph", "Rocket 3 R", 2020, 10.56, 203, "Cycle World 2020 (Gadson 17-pass tuned at Silver Dollar Motorsport Park)")`

**Verified sources:**
- Cycle World "Rickey Gadson and the Triumph Rocket 3 R" feature: 10.562s @ 126.41 mph = 203.4 km/h
  URL: https://www.cycleworld.com/story/motorcycle-racing/rickey-gadson-and-the-triumph-rocket-3-r/
- MCN 2020 R3R airfield road-test: 11.07s @ 126.06 mph = 202.9 km/h
  URL: https://www.motorcyclenews.com/bike-reviews/triumph/rocket-iii/2020/

Both reputable independent instrumented sources agree on the 126 mph trap. The old 226 km/h value (= 140.4 mph) was an internally-inconsistent transcription error.

Inbox status updated: `## INSTRUCTION` → `## DONE` with full result block.

## Sweep delta — before vs after

```
                                     BEFORE              AFTER
  N (matched benchmarks)             162                 167  (+5)
  mean|Δ|                            0.323s              0.321s  (-0.002s)
  median|Δ|                          0.204s              0.205s  (~flat)
  bias                               +0.045s             +0.037s  (closer to zero)
  within ±0.10s                      39 (24%)            39 (23%)
  within ±0.20s                      79 (49%)            81 (49%)  (+2)
  within ±0.50s                      136 (84%)           140 (84%)  (+4)
  within ±1.00s                      156 (96%)           161 (96%)  (+5)
  top-10 mean|Δ|                     0.0094s             0.0094s  (unchanged)

  REFERENCE BASELINES (must be exact):
    K5         10.0334s              10.0334s  (Δ +0.0000)
    R1         10.2859s              10.2859s  (Δ +0.0000)
    Hayabusa   10.4712s              10.4712s  (Δ +0.0000)
```

### Cluster moves (before → after)

```
  litre-sport-195+       N=28→28  bias -0.012 → -0.012  (unchanged)
  litre-sport-600-1000   N=76→79  (+3)  bias -0.050 → -0.057  (negligible)
  mid-twin-500-700       N= 8→ 8  bias +0.015 → +0.015  (unchanged)
  mid-twin-300-500       N=16→16  bias -0.137 → -0.137  (unchanged)
  cruiser-1300+          N= 3→ 3  bias +0.488 → +0.488  (unchanged; Rocket 3 R
                                   already in cluster — fix swapped trap not ET
                                   delta direction; sim Rocket 3 R was already
                                   in the +0.4–0.5s delta band for this cluster)
  other                  N=12→14  (+2)  bias +0.233 → +0.170  (improved -0.063s)
  two-stroke             N= 5→ 5  unchanged
  entry-150-200          N= 8→ 8  unchanged
  entry-200-300          N= 6→ 6  unchanged
```

Distribution of the 5 new entries across clusters:
- 3 → litre-sport-600-1000 (Buell 1125R, MV Agusta F3 800, KTM RC8 R, Kawasaki Ninja 1000) — wait, that's 4. Let me recount: Buell 1125R is 1125cc V-twin → likely "other" cluster; KTM 1190 RC8 R is 1148cc V-twin → "other"; MV Agusta F3 800 is 798cc I3 → litre-sport-600-1000; Kawasaki Ninja 1000 is 1043cc I4 sport-tourer → litre-sport-600-1000; Yamaha FZ6 is 600cc I4 naked → litre-sport-600-1000. So 3 litre-sport-600-1000 (+3 = 79), 2 other (+2 = 14). Matches the observed cluster N moves.

## Tests

`tests/test_validation.py`: 57/57 passed in 6.89s. No matcher specificity regressions; no benchmark schema breaks.

## Search/research methodology

1. Counted current BENCHMARKS (131 entries, 112 unique mfr/model pairs) and ran baseline sweep (N=162 matched, took 183s).
2. Enumerated catalog bikes from `motoquant.scraper.known_bikes.ALL_KNOWN_BIKES` + `known_bikes_extended.EXTENDED_BIKES` filtered to bikes with `peak_power_hp > 0` and NO matching benchmark in BENCHMARKS. Result: 68 litre-class unmatched + 164 mid-class unmatched.
3. WebFetched the canonical Cycle World / Sport Rider sportbike-performance-numbers archive with prompts targeting the unmatched bike list. Extracted ~30 candidate entries.
4. Filtered each candidate through three gates: (a) catalog row exists with year-range overlap, (b) `_model_match()` returns True against the catalog model_name, (c) no existing benchmark already covers (mfr, mdl) — to avoid breaking matcher specificity tests.
5. Selected the 5 cleanest binds. Skipped candidates where the catalog row's year_from was AFTER the benchmark year (Honda CB1000R '11 vs catalog 2021-2024), where pattern tokens didn't match catalog model_name (Suzuki SV1000S — no catalog row exists), or where an existing benchmark already covered the same model.
6. Composed inline citation comments matching the precedent set in the 2026-05-30 third-pass and 2026-05-31 pass 1 sections (generation context, displacement, hp, weight, cluster-fit reasoning).

## Candidates considered but NOT added (flagged for catalog-expansion)

- Suzuki SV1000S 2003 (CW 10.82 @ 127.1 mph) — no catalog row exists for SV1000.
- Suzuki B-King 2008 — existing benchmark already covers it (9.99 @ 223).
- Honda CBR954RR 2002 — existing benchmark already covers it (10.49 @ 224).
- Kawasaki ZX-11 1997, ZX-12R 2001 — no catalog rows.
- Honda CBR1100XX Blackbird '97/'99 — no catalog row.
- Honda CB1000R 2011, Honda CBR600F4i 2001, Yamaha YZF600R 1998, Yamaha FZ1 '07/'11 — either no matching year-range row or existing benchmark in conflict.
- Triumph Daytona 675R 2011 (CW 10.69 @ 130.7 mph) — catalog Daytona 675 covers 2013-2017 only; 2011 year fails year-range filter. (Daytona 675 2013 already has 10.32 @ 219 entry.)

These will be addressed by catalog-expansion (which produces matching `*KNOWN_BIKES` entries) and a subsequent benchmark-import run.

## Files touched

- `scripts/validation_sweep.py` — 5 new benchmarks appended in section dated `2026-05-31 benchmark-import agent pass 3`; Rocket 3 R 2020 entry updated with fixed trap + ET + extended source citation.
- `DISPATCH_INBOX.md` — Rocket 3 R urgent instruction marked `## DONE` with result block (original INSTRUCTION block archived underneath for audit).
- `reports/benchmark_import_2026-05-31_third_pass.md` — this report.

## Commit suggestion

```
data(benchmarks): +5 instrumented adds (CW) + fix Rocket 3 R 2020 trap

Bind 5 new Cycle World / Sport Rider timing-strip benchmarks to previously
unbenchmarked catalog rows: Buell 1125R '08, MV Agusta F3 800 '14, KTM 1190
RC8 R '10, Kawasaki Ninja 1000 '11, Yamaha FZ6 '04. Each verified for clean
year-range + token-match catalog binding, no collisions with existing entries.

Urgent inbox fix: Triumph Rocket 3 R 2020 trap-speed transcription corrected
from 226 km/h to 203 km/h and ET from 10.50 to 10.56 to match the Cycle World
Rickey-Gadson 17-pass best at Silver Dollar Motorsport Park, with MCN airfield
corroboration on the 126 mph trap.

Sweep: N 162→167 (+5), bias +0.045→+0.037s (closer to zero), mean|Δ|
0.323→0.321s. Reference baselines K5/R1/Hayabusa preserved exactly.
57/57 validation tests pass.
```
