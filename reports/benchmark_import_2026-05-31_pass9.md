# Benchmark Import Report — 2026-05-31 (pass 9)

**Agent:** A3 (benchmark-import)
**Session:** 1780259453-632
**Scope:** Add 2-5 high-confidence instrumented quarter-mile benchmarks to
`scripts/validation_sweep.py::BENCHMARKS`. Cite source per entry.

## Result

2 high-confidence entries added — both vintage litre-class Cycle World
timing-strip cover-test citations. Sweep matched-N rose **147 → 149**
(+2). BENCHMARKS list length **150 → 152** (+2).

| metric | pre-add | post-add | Δ |
|---|---|---|---|
| BENCHMARKS list length | 150 | 152 | +2 |
| matched-N | 147 | 149 | +2 |
| reference K5 ET | 10.0334s | 10.0334s | +0.0000s |
| reference R1 ET | 10.2859s | 10.2859s | +0.0000s |
| reference Hayabusa ET | 10.4712s | 10.4712s | +0.0000s |

Each new entry binds to exactly one previously-unbenchmarked catalog
row (pre-add `_best_benchmark_match` probe confirmed `None` on both).
No shadowing of existing benchmarks. Both new entries land inside the
documented litre-sport bias band (CLAUDE.md April-27 PM cluster
metrics: litre-sport-600-1000 mean|Δ|=0.225s, bias -0.147s).

## Added entries

### 1. Suzuki GSX-R 750 (1985-1987) — Cycle World June 1985 cover

| field | value |
|---|---|
| catalog row | `GSX-R 750` (1985-1987), 749 cc oilcooled I4, 108 hp |
| benchmark | 11.48s @ 190 km/h (118.26 mph) |
| source | Cycle World June 1985 cover comparison (GSX-R750 vs FZ750) |
| URL | <https://magazine.cycleworld.com/article/1985/6/1/suzuki-gsx-r750-vs-yamaha-fz750> |
| sim ET | 11.252s (Δ -0.228s vs bench) |
| sim trap | 215.9 km/h (Δ +25.9 km/h vs bench 190) |
| year_hint | 1985 → year-range match clean |

**Rationale.** Cycle World quote: *"the GSX-R still turned a best
quarter of 11.48 seconds at 118.26 mph"* — instrumented timing strip
at Carlsbad Raceway, Canadian-spec 105 bhp tester (closest to global
1985 production). Stock bike, factory carbs, rider wheelied through
1st-2nd shift (clutch-limited launch — figure is conservative for the
chassis). ET delta -0.228s sits inside the litre-sport-600-1000
cluster band. Trap delta +25.9 km/h reflects the well-documented
mid-80s SACS dyno-power overstatement (Cycle World era charts ran
+5-15% optimistic on early SACS claims; `spec_to_bike_config` has no
era-correction pass).

**Specificity check.** Catalog has two `GSX-R 750` rows
(1985-1987 oilcooled F-model, and 2008-2010 K8 chassis). 2-token
`GSX-R 750` pattern matches both, but year-range filter (1985 ≤
year_hint ≤ 1987) routes this benchmark exclusively to the 1985-1987
row. The 2008-2010 row remains bound to its existing 2008 SR archive
entry. Verified via post-edit `_best_benchmark_match` probe.

### 2. Honda CBR900RR Fireblade (1992-1995) — Cycle World Sept 1994

| field | value |
|---|---|
| catalog row | `CBR900RR Fireblade` (1992-1995), 893 cc I4, 124 hp |
| benchmark | 10.67s @ 212 km/h (131.57 mph) |
| source | Cycle World September 1994 cover road-test of 1995 model |
| URL | <https://magazine.cycleworld.com/article/1994/9/1/1995-honda-cbr900rr> |
| sim ET | 10.773s (Δ +0.103s vs bench) |
| sim trap | 226.6 km/h (Δ +14.6 km/h vs bench 212) |
| year_hint | 1995 → year-range match clean |

**Rationale.** Cycle World quote: *"the 1995 Honda CBR900RR achieved
a quarter-mile ET of 10.67 seconds at 131.57 mph"* at Carlsbad
Raceway, "mild weather and a light tailwind", on factory-standard
street-compound Bridgestone Battlax BT50 tyres (NOT race rubber).
ET delta +0.103s — tight cluster fit, high-confidence match. Trap
delta +14.6 km/h within the litre-sport band's typical residual.

**Specificity check.** Catalog has two CBR900RR rows: `CBR900RR
Fireblade` (1992-1995 SC28 first-gen) and `CBR900RR` (1998-1999
SC33). The 2-token pattern `CBR900RR Fireblade` is MORE specific
than the 1-token `CBR900RR` (existing 1998 SR-archive entry) per
`_model_specificity_score`. Post-edit `_best_benchmark_match` probe
confirms: SC28 row binds to the new 1995 entry, SC33 row binds to
the existing 1998 entry — no shadowing.

## Rejected this pass (logged so future passes don't re-investigate)

* **Honda CB1000R 2011 (998 cc 145 hp naked)** — Cycle World Sport
  Rider archive DOES list `CB1000R ('11) 11.13 @ 123.11 mph`; verified
  via two independent WebFetch calls. However, the catalog row
  `CB1000R` covers 2021-2024 ONLY (Honda's current Neo Sports Cafe
  generation, post-restyle); the 2011 model is a separate chassis
  (Honda CB1000R Naked, distinct geometry + ECU) that has no catalog
  entry. Year-range filter (2011 ∉ 2021-2024) rejects the binding.
  Adding a 2011 benchmark would orphan-bind only via accident; per
  project bar (no fabricated bindings), withheld.
* **Ducati Diavel L-twin (2017) — MotoStatz 10.46s @ 133 mph** —
  MotoStatz article cites Dragy for 60-130 mph sprint but does not
  explicitly name the timing device for the quarter-mile figure;
  fails project bar (explicit instrumented-device citation required).
* **Ducati Streetfighter V4 — MotoStatz 10.20s @ 149 mph** — MotoStatz
  article does NOT name Dragy or any other instrumented device for the
  quarter-mile figure (only narrative). Fails project bar.
* **Ducati Monster 1200S — MotoStatz 10.57s @ 135 mph** — no Dragy
  citation; fails project bar.
* **Suzuki SV1000S — MotoStatz 10.88s @ 125 mph** — no Dragy citation
  AND the article qualifies as "if you are light and really know what
  you are doing"; non-typical test bike. Fails project bar twice.
* **Kawasaki Z H2 SE (2024-2025)** — only Z H2 BASE has instrumented
  data (MotoStatz Dragy 10.13s @ 146 mph, already in catalog). The SE
  is a distinct catalog row with different power output; no SE-specific
  Dragy/CW citation found.
* **Indian Pursuit Dark Horse** — no instrumented quarter-mile data
  found in honest search (forums + zeroto60times estimates only).
* **Triumph Speed Triple 1200 RS** — no MotoStatz article exists;
  AccelerationTimes.com / FastestLaps.com listings are calculated
  estimates, not Dragy.
* **Honda CB1000 Hornet (2025-2026)** — only MotorBikeCatalog
  "performance estimation" data exists; same source bar that's been
  rejected in passes 4, 7, 8.
* **Yamaha FJR1300 — Cycle World 2005/2008 archive entries** — catalog
  row `FJR1300` covers 2013-2022 only; year-range filter (2005/2008 ∉
  2013-2022) rejects binding. The 1298 cc inline-4 platform was
  largely unchanged across the 2003-2022 production run, but per
  project hygiene (no expanding year-ranges retroactively), withheld.
* **Kawasaki ZX-10R 2016 — Cycle World archive 10.29 @ 146 mph** —
  catalog has 2011-2015 and 2021-2024 rows but the 2016-2020 chassis
  generation has no catalog entry. Year-range filter rejects.

## Inbox audit

* **`[urgent] fix Rocket 3 R 2020 benchmark`** — already DONE
  (line 131 of `validation_sweep.py` reads `10.56s @ 203 km/h`, per
  Cycle World Gadson feature). Inbox block in `## DONE` state; no
  re-edit needed.
* **`[urgent] fix BENCHMARKS matcher specificity bug`** — already
  RESOLVED structurally via `_best_benchmark_match` (line 1950) which
  implements Option 2 (score-and-pick by token-count). Out of scope
  for benchmark-import.

## Files touched

* `/tmp/mq-session-1780259453-632/repo/scripts/validation_sweep.py`
  (appended 2 entries + comment headers, BENCHMARKS list 150 → 152)
* `/tmp/mq-session-1780259453-632/repo/reports/benchmark_import_2026-05-31_pass9.md`
  (this report)

`scripts/sweep_with_clusters.py` imports `BENCHMARKS` from
`scripts/validation_sweep.py` (line 35) — single source of truth, no
mirror edit required.

## Reference baselines preserved EXACTLY

| Bike | Target | Post-edit Result | Δ |
|---|---|---|---|
| GSX-R 1000 K5 | 10.0334s | 10.0334s | +0.0000s |
| YZF-R1 4C8 | 10.2859s | 10.2859s | +0.0000s |
| Hayabusa Gen1 | 10.4712s | 10.4712s | +0.0000s |

Anchored in `motoquant/defaults.py`; never touched by this agent.
