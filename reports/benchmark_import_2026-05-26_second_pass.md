# Benchmark import — 2026-05-26 (second pass)

**Agent:** A3 / benchmark-import
**Working tree:** `/tmp/mq-session-1779769842-658/repo`
**Files touched:**
- `scripts/validation_sweep.py` — appended 2 entries to BENCHMARKS list (now 114, was 112)
- `reports/benchmark_import_2026-05-26_second_pass.md` — this report

## Summary

Two high-confidence instrumented quarter-mile benchmarks added to BENCHMARKS list.
Both bind via `_best_benchmark_match` to the intended catalog row with no
specificity collisions. Reference baselines preserved exact
(K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s, Δ +0.0000s on all three).

## Adds

### 1. Honda CBR954RR Fireblade (2002–2003)
- **ET:** 10.49s
- **Trap:** 139 mph (224 km/h)
- **Source:** Cycle World — "Honda CBR954RR vs Suzuki GSX-R1000 vs Yamaha YZF-R1
  Comparison Test" (timing-strip at sanctioned drag strip)
- **URL:** https://www.cycleworld.com/honda-cbr954rr-vs-suzuki-gsx-r1000-vs-yamaha-yzf-r1-comparison-test-review/
- **Why trusted:** Cycle World is the top-priority source on this project's
  accepted list — already cited for the ZX-14R, S1000RR 2015/2019, M1000RR,
  Z H2, Z1000, Panigale V4 and Hayabusa benchmarks. Same comparison-test
  format and same publication that produced the YZF-R1 2004 (10.30s @ 238 km/h)
  and ZX-10R 2004 (10.30s @ 240 km/h) entries already in the list.
- **Cluster fit:** 10.49s @ 224 km/h vs same-era R1 (10.30 @ 238) — the 0.19s
  / -14 km/h gap is consistent with CBR954's claimed 154 hp vs R1's 172 hp
  (CW article: "runs out of rpm in third right up to the quarter-mile line so
  requires a gear change which hurts its time").
- **Catalog bind:** `HONDA_CBR954RR_2002` (model_name "CBR954RR Fireblade",
  2002-2003 SC50). Unique 4-token model pattern; no collision risk.
- **Sim sanity:** sim 10.174s vs bench 10.490s — Δ −0.316s. Within
  litre-sport cluster bias band; the under-prediction is consistent with the
  Cycle World note about the gear-change handicap not being modelled here.

### 2. Ducati Monster 1200 (2014–2021)
- **ET:** 10.57s
- **Trap:** 135 mph (217 km/h)
- **Source:** MotoStatz Dragy instrumented test on Monster 1200 S variant
  (which shares the 1198 cc Testastretta 11° L-twin with the base 1200)
- **URL:** https://motostatz.com/ducati-monster-1200s-acceleration-top-speed-review/
- **Methodology URL:** https://motostatz.com/how-we-test-motorcycles/
- **Why trusted:** Same MotoStatz/Dragy source bar already established for
  Street Triple 765 RS, Panigale V2, RS 660, 890 Duke R, 790 Duke, XSR900,
  CBR 600RR PC40B, Ninja 1000SX, BMW S1000R, CBR650R, Monster 937, Tracer 9
  GT, ZX-9R F-gen, VFR800F Interceptor, Tuono 660, and FTR 1200 S entries
  already in the list. MotoStatz "How We Test" page explicitly names Dragy GPS
  as the standard measurement device.
- **Variant note:** Monster 1200 S adds Öhlins suspension + Brembo M50
  brakes vs base 1200 — non-engine deltas that do not move drag-strip ET
  measurably. The data binds cleanly to the base `DUCATI_MONSTER_1200_2014`
  catalog row. Monster 1200 R variant (160 hp) is a distinct chassis NOT in
  catalog — this benchmark explicitly excludes the R.
- **Catalog bind:** `DUCATI_MONSTER_1200_2014` (model_name "Monster 1200",
  2014-2021 M9). Unique 2-token model pattern; no collision risk with the
  Monster 937 (already benchmarked) or Monster 821.
- **Sim sanity:** sim 10.376s vs bench 10.570s — Δ −0.194s. Clean fit
  within the litre-naked sub-cluster band.

## Rejected this pass (logged for audit trail)

- **BMW M 1000 R** — MotoStatz lists an article but DOES NOT explicitly name
  Dragy in the snippets found. MCN review article mentions tested 0-60/0-100/
  0-140 figures but no quarter-mile time. ProfessCars 9.8s figure is a
  calculated estimate, not instrumented. **Fails project bar.**
- **Suzuki GSX-8S** — No MotoStatz Dragy article found. Only FastestLaps
  and AccelerationTimes calculated estimates surface. Honest search yielded
  no Cycle World / Sport Rider / MCN instrumented test.
- **Honda CB1000R** — Only ProfessCars and Superbike Magazine 2008 estimates;
  no instrumented Cycle World / MotoStatz / MCN data located.
- **Triumph Speed Triple 1200 RS** — No instrumented test found in this pass
  (same as prior 2026-05-25 fourth-pass rejection).
- **Honda VTR1000 SP2 (RC51)** — MotoStatz Dragy data exists for SP1
  (2000-2001) at 10.67s @ 133 mph, but the catalog only contains the SP2
  (2002-2006 RC51). SP1 and SP2 share the 999 cc V-twin but the SP2 has
  Showa upside-down forks + updated injection mapping; per CLAUDE.md
  "honest > apparent accuracy" the SP1 figure should not be applied to the
  SP2 entry. Either: (a) add the VTR1000 SP1 to the catalog first via
  catalog-expansion agent, then re-pass; or (b) find an instrumented SP2
  test. **Escalation flag:** SP1 catalog add is a worthwhile catalog-
  expansion target.
- **Kawasaki Z750 / Z800** — No instrumented Cycle World / Sport Rider /
  MotoStatz Dragy data found for either; only motorbikecatalog estimates and
  MCN qualitative reviews.

## Validation

- BENCHMARKS list: 112 → 114 entries (+2)
- `validation_sweep.py` parses + imports cleanly
- `_best_benchmark_match()` binds both new entries to the intended catalog
  rows verified via in-process check
- Reference baselines: **K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s, all
  Δ +0.0000s — exact preservation**
- No existing BENCHMARKS entries modified; only appended

## Commit message

`feat(benchmarks): add 2 instrumented quarter-mile entries (CBR954RR / Monster 1200)`
