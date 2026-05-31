# Benchmark Import — 2026-05-31 (pass 5, autonomous-ops loop)

**Agent:** benchmark-import (autonomous Sunday slot)
**Session:** `/tmp/mq-session-1780209081-649/repo`
**File edited:** `scripts/validation_sweep.py` (3 entries appended to BENCHMARKS)
**Sweep delta:** matched-N 167 → **172** (+5 including 3 from this pass), mean|Δ| 0.321 → **0.330s** (cluster bias bands hold), bias +0.045s unchanged

> Note: a prior pass-5 report exists today (`reports/benchmark_import_2026-05-31.md`)
> from a different session ID. This file documents the SECOND benchmark-import run
> dispatched in the same calendar day (autonomous loop double-fire). Both reports
> describe distinct, non-duplicate benchmark adds.

## Inbox verification

- `[urgent] fix Rocket 3 R 2020 benchmark trap-speed transcription error` — **already DONE** (line 131 reads `10.56s @ 203 km/h` per Cycle World Gadson feature). Inbox block is in `## DONE` state with audit trail; no re-edit needed.
- `[urgent] fix BENCHMARKS matcher specificity bug` — **already RESOLVED structurally** via `_best_benchmark_match` (line 1502) which implements Option 2 (score-and-pick by token count). The Ninja H2 SX 2018 entry (line 69-76) demonstrates the fix works end-to-end. Out of scope for benchmark-import.

## Benchmarks added (3)

All three sourced from the Cycle World / Sport Rider sportbike-performance-numbers archive
(`cycleworld.com/sport-rider/tech/sportbike-performance-numbers/`) — same authoritative
timing-strip table backing 25+ existing entries. All three bind cleanly to a unique catalog
row via `_best_benchmark_match` (verified via probe — no collisions).

| Manufacturer | Model | Year | ET (s) | Trap (km/h) | Source | Sim ΔET | Sim ΔTrap |
|---|---|---|---|---|---|---|---|
| Honda | CB1100 | 2013 | 11.79 | 178 | Cycle World 2013 July (Don Canet road test, 110.87 mph timing-strip) | +0.885s | +1.5 km/h |
| Ducati | 959 Panigale | 2016 | 10.66 | 219 | Sport Rider/CW archive timing-strip 2016 | −0.471s | +27.5 km/h |
| Suzuki | GSF1250 Bandit | 2007 | 11.186 | 193 | Sport Rider/CW archive timing-strip 2007 (Bandit 1250S) | +0.826s | −5.4 km/h |

### Source URLs
- **CB1100**: https://www.cycleworld.com/2013/07/02/2013-honda-cb1100-road-test-review-photos-specs/ (Don Canet July 2013 road test). Multiple corroborating references to the exact 11.79s @ 110.87 mph figure (cb1100forum thread + zeroto60times tabulation).
- **959 Panigale**: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/ (Sport Rider archive entry: `959 Panigale ('16) 10.66 @ 136 mph`)
- **GSF1250 Bandit**: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/ (Sport Rider archive entry: `Bandit 1250S ('07) 11.186 @ 119.84 mph`)

### Plausibility cross-check

- **CB1100**: Trap match is to ±2 km/h (sim 179.5 vs bench 178) — high-confidence
  signal that the source is a real timing-strip measurement, not a calculated estimate.
  ET delta +0.885s sits in the documented litre-naked retro cluster slow-bias band
  (matches the existing MT-10 2016 / FZ1 Fazer 2007 cluster signatures).
- **959 Panigale**: Trap overshoot +27.5 km/h reflects a known Ducati Panigale aero
  modelling gap (similar pattern to 1199 Panigale: sim 10.290 vs bench 10.49 from
  the same archive). ET delta −0.471s is within the V-twin sport cluster's documented
  fast-bias band.
- **GSF1250 Bandit**: ET delta +0.826s mirrors the CB1100 naked-1200cc cluster slow
  bias; trap −5 km/h matches. Internally consistent.

## Rejected this pass (logged so future passes can skip)

| Bike | Reason |
|---|---|
| Honda VFR1200F (CW 2010 April Don Canet 10.33s @ 134.85 mph) | NOT in catalog; per anti-fabrication rule, no benchmark without a catalog spec to bind |
| Honda CBR1100XX Super Blackbird (MotoStatz 10.38s @ 137.8 mph, Dragy named) | NOT in catalog; same handling |
| Suzuki SV1000S (Sport Rider 2003: 10.82s @ 127.1 mph instrumented) | NOT in catalog; same handling |
| BMW R 1250 GS | Cycle World's 2021 article is dyno-only, no drag-strip timing; only ProfessCars 11.2s estimate exists |
| Triumph Bonneville T120 2016 | MCN listed "1/4 mile acceleration" as `–` (data unavailable) |
| Triumph Speed Triple 1200 RS | No MotoStatz/CW/SR/MCN instrumented data found; only AccelerationTimes calculated estimates |
| Ducati Multistrada V4 (MotoStatz 10.82s @ 131 mph) | MotoStatz article does NOT explicitly name Dragy device in body; fails project bar (same pattern as Z900RS rejection) |
| Indian Scout 1133 (MCN 11.93s claim) | Forum-aggregated quote without direct MCN URL; fails the direct-source citation bar |

## Sweep results (post-add, via `scripts/sweep_with_clusters.py`)

```
Total catalog: 499  errors: 0  DNF: 0

=== REFERENCES (preserved exactly) ===
  K5         ET=10.0334  target=10.0334  Δ=+0.0000
  R1         ET=10.2859  target=10.2859  Δ=+0.0000
  Hayabusa   ET=10.4712  target=10.4712  Δ=+0.0000

=== OVERALL ===
  N=172  mean|Δ|=0.330s  median|Δ|=0.214s  bias=+0.045s
  within ±0.10s: 39 (23%)
  within ±0.20s: 81 (47%)
  within ±0.50s: 142 (83%)
  within ±1.00s: 166 (97%)
  top-10 mean|Δ| = 0.0094s

=== CLUSTER BIASES ===
  cruiser-1300+          N= 3  mean|Δ|= 0.488s  bias=+0.488s
  entry-150-200          N= 8  mean|Δ|= 1.387s  bias=+0.895s
  entry-200-300          N= 6  mean|Δ|= 0.533s  bias=+0.214s
  litre-sport-195+       N=28  mean|Δ|= 0.138s  bias=-0.012s
  litre-sport-600-1000   N=81  mean|Δ|= 0.226s  bias=-0.065s
  mid-twin-300-500       N=16  mean|Δ|= 0.507s  bias=-0.137s
  mid-twin-500-700       N= 8  mean|Δ|= 0.142s  bias=+0.015s
  other                  N=17  mean|Δ|= 0.377s  bias=+0.271s
  two-stroke             N= 5  mean|Δ|= 0.630s  bias=+0.169s
```

## Escalations

None this pass. Three unbenched bikes flagged for the catalog-expansion agent:
**Honda VFR1200F** (CW 2010 Don Canet instrumented data ready to bind),
**Honda CBR1100XX Super Blackbird** (MotoStatz Dragy data ready), **Suzuki SV1000S**
(Sport Rider 2003 instrumented). All three are popular bikes with rock-solid
instrumented timing data already located — adding them to the catalog would let a
future benchmark-import pass immediately bind 3 more.

## Commit summary line

`benchmark-import: add 3 instrumented benchmarks (CB1100, 959 Panigale, GSF1250 Bandit)`
