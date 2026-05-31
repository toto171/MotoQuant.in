# Benchmark Import Report — 2026-05-31 (pass 8)

**Agent:** A3 (benchmark-import)
**Session:** 1780245046-669
**Scope:** Add 2-5 high-confidence instrumented quarter-mile benchmarks to
`scripts/validation_sweep.py::BENCHMARKS`. Cite source per entry.

## Result

2 high-confidence entries added (no third candidate cleared the project
"explicit instrumented device citation" bar this pass).

| metric | pre-add | post-add | Δ |
|---|---|---|---|
| BENCHMARKS list length | 148 | 150 | +2 |
| matched-N (catalog rows binding to ≥1 benchmark) | 145 | 147 | +2 |
| reference K5 ET | 10.0334s | 10.0334s | +0.0000s |
| reference R1 ET | 10.2859s | 10.2859s | +0.0000s |
| reference Hayabusa ET | 10.4712s | 10.4712s | +0.0000s |

Each new entry binds to exactly one previously-unbenchmarked catalog row
(pre-add `_best_benchmark_match` probe confirmed `None` on both). No
shadowing of existing benchmarks. Both new entries land inside the
documented litre-sport bias band (CLAUDE.md April-27 PM metrics: cluster
mean|Δ|=0.225s, bias -0.147s).

## Added entries

### 1. Yamaha FZR1000 EXUP (1989-1995) — Cycle World Feb 1989

| field | value |
|---|---|
| catalog row | YAMAHA_FZR1000_EXUP, `FZR1000 EXUP`, 1002 cc 145 hp I4 sport |
| benchmark | 10.39s @ 217 km/h (134.52 mph) |
| source | Cycle World February 1989 cover test, instrumented timing strip |
| URL | <https://magazine.cycleworld.com/article/1989/2/1/fzr1000> |
| sim Δ | sim 10.599s vs bench 10.39s → +0.209s (within cluster band) |
| trap Δ | sim 231.8 km/h vs bench 217 km/h → +14.8 km/h |
| year_hint | 1989 → year_from match clean |

**Rationale.** CW Feb 1989 declared the FZR1000 EXUP "the quickest time
Cycle World has ever achieved on a stock motorcycle" at the time of
publication. The 10.39s @ 134.52 mph is the canonical published result
from that test issue. Cluster-consistency: 10.39 @ 134.5 mph slots
between the contemporary Kawasaki ZX-11 (10.25s @ 137 mph, CW 1990) and
the GSX-R 1100 (10.45 @ 130.2 mph, SR 1997) — heavier chassis + softer
initial cam timing on the European-spec test unit explain the spread vs
the ZX-11.

**Caveat documented in inline comment:** the CW test unit was a
pre-production European-spec model. CW themselves noted production
units could be quicker. This caveat does NOT disqualify the entry —
the test was instrumented, the figure is the magazine's published
canonical result, and the spec gap to production is sub-0.1s per CW's
own commentary.

**Specificity check.** `FZR1000 EXUP` is a 2-token pattern unique in the
catalog (only one FZR1000 entry exists). No collision risk.

### 2. Kawasaki ZX-9R Ninja B-model (1994-1997) — Cycle World May 1994

| field | value |
|---|---|
| catalog row | KAWASAKI_ZX9R_NINJA, `ZX-9R Ninja`, 899 cc 147 hp I4 sport |
| benchmark | 10.65s @ 211 km/h (131.38 mph) |
| source | Cycle World May 1994 (B1 49-state instrumented test) |
| URL | <https://magazine.cycleworld.com/article/1994/5/1/rocet-rides> |
| sim Δ | sim 10.606s vs bench 10.65s → -0.044s (excellent agreement) |
| trap Δ | sim 232.5 km/h vs bench 211 km/h → +21.5 km/h |
| year_hint | 1994 → 1994 ≤ year ≤ 1997 cleanly separates from F-gen 2000-2003 |

**Rationale.** First B-model (1994-1997) ZX-9R benchmark on the list.
Distinct from the previously-benchmarked F-gen (2000-2003) which has
two existing entries: SR 2000 10.50s and MotoStatz 2025 Dragy 10.62s
(2003 F-gen). The B-model was Kawasaki's first ZX-9R, built on a
different chassis generation entirely (conventional cassette-box
gearing, ~10 kg heavier curb weight, lower-redline I4).

**Specificity check.** Catalog model_name is `ZX-9R Ninja` (Ninja AFTER
ZX-9R). The `_model_match` tokeniser splits on whitespace + hyphen, so
the 2-token pattern matches the catalog row regardless of order. The
F-gen catalog row is `Ninja ZX-9R` (Ninja first) with year range
2000-2003 — year-range gating cleanly filters the new B-model benchmark
away from the F-gen catalog row. Confirmed via `_best_benchmark_match`
probe: F-gen 2000 row still binds to the existing SR 2000 entry, B-model
1994 row binds to the new entry. No shadowing.

## Rejected this pass (logged so future passes don't re-investigate)

| candidate | source attempted | reject reason |
|---|---|---|
| Honda CB1000R | MCN / CW / Dragy search | No instrumented quarter-mile data; only forum estimates. |
| Honda RC30 (VFR750R) | CW 1990 archive | Only an unsourced 11.8s figure surfaces; no CW timing-strip citation located. |
| Kawasaki Z800 | MCN / CW / MotoStatz | No instrumented data; consistent with pass-7 outcome on similar naked targets. |
| Triumph Daytona 660 | MCN 2024 review | MCN reviewed but did NOT publish a quarter-mile timing strip; no MotoStatz article. |
| Triumph Rocket 3 R 2020 | MCN 2020 review | MCN reports "11.07s @ 126.06 mph" but article body does NOT name the device. Same bar as pass-7 Z900RS/Streetfighter V4 rejections. |
| Triumph Speed Triple 1200 RS / RR | MotoStatz / MCN / CW | No dedicated 1200-class MotoStatz Dragy article exists. |
| MV Agusta F4 RC, Bimota Tesi 1D, MV Agusta Brutale 800 | MotoStatz / CW / SR | No instrumented quarter-mile data found in honest search. |
| Honda CBR1100XX Super Blackbird | CW/SR 1997 (10.27 @ 136 mph) | Clean instrumented data available BUT model NOT in catalog. Queued for catalog-expansion agent per pass-7 carry-forward. |
| Kawasaki ZX-9R F-gen 2002 (CW April 2002) | CW April 2002 dyno test | Article in CW archive but no ET in CW excerpt — only dyno power. Existing 2000 + 2003 F-gen entries already cover the F-gen. |

## Files touched

- `scripts/validation_sweep.py` — 2 new tuples appended inside a
  `# ── 2026-05-31 pass 8 ──` block after the pass-7 closing marker.

`scripts/sweep_with_clusters.py` is NOT touched — it imports
`BENCHMARKS` from `validation_sweep.py` (single source of truth verified
at session start).

## Sources

- <https://magazine.cycleworld.com/article/1989/2/1/fzr1000> (Yamaha FZR1000 EXUP)
- <https://magazine.cycleworld.com/article/1994/5/1/rocet-rides> (Kawasaki ZX-9R B-model)
- Cross-references in search-result excerpts: zx-9r.net forum review
  thread of CW May 1994 B1 49-state test; multiple FastestLaps /
  AccelerationTimes mirror pages of the CW Feb 1989 FZR1000 article.

## Incidents / escalations

None. No conflicts with existing entries, no urgent audit triggered.

**Catalog-expansion queue (carry-forward for catalog-expansion agent):**
The Honda CBR1100XX Super Blackbird gap remains open from pass-7 — CW/SR
1997 has clean instrumented data (10.27 @ 136 mph, with parallel
10.30/10.31s back-to-back runs) ready to add as soon as the model lands
in `motoquant/scraper/known_bikes.py` or `known_bikes_extended.py`.
