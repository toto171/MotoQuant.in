# Benchmark Import — 2026-05-25 (Ninth Pass)

**Agent:** benchmark-import
**Date:** 2026-05-25
**Delivery:** +1 high-confidence instrumented benchmark (target was 2-3; quality bar held over quantity).

## Summary

- BENCHMARKS count: 108 → **109**
- Files touched: `scripts/validation_sweep.py` (mirror in `sweep_with_clusters.py` is just `from scripts.validation_sweep import BENCHMARKS`, so a single edit propagates).
- New first-of-its-kind: first Indian-brand benchmark in the list; first FTR-family benchmark.

## Added benchmark

| Manufacturer | Model | Year | ET (s) | Trap (km/h) | Source |
|---|---|---|---|---|---|
| Indian | FTR 1200 S | 2020 | 11.20 | 193 | MotoStatz (Dragy, stock instrumented FTR 1200 S) |

**Source URL:** https://motostatz.com/indian-ftr-1200-acceleration-top-speed-review/
**Methodology URL:** https://motostatz.com/how-we-test-motorcycles/

### Verification chain
1. WebSearch returned the MotoStatz article on FTR 1200 acceleration & top speed.
2. WebFetch confirmed the article explicitly cites Dragy: *"The Dragy 60-130 mph time is a decent 9.86 seconds."*
3. WebFetch confirmed test bike is the FTR 1200 S: *"The FTR 1200 S is a drag bike for the road."*
4. WebFetch confirmed NO mention of aftermarket exhaust, ECU flash, or any modifications anywhere in the article body.
5. Article quotes: *"the FTR 1200 can blast through the quarter mile in low elevens with a best of 11.20 at 120 mph."*
6. `find_spec("Indian", "FTR 1200 S", 2020)` resolves cleanly to catalog row `Indian FTR 1200 S 2019-2024`.
7. Sanity-sim through `MotoQuantEngine`: ET 11.082s @ 211.1 km/h → ΔET **−0.118s** vs benchmark, Δtrap +18.1 km/h. ET delta well within the litre-naked cluster's documented mean|Δ| band (~0.225s per CLAUDE.md).

The minor trap discrepancy in the source article (120 mph in the prose vs 124 mph in one data-table mention) was resolved by taking the lower/more conservative 120 mph (193 km/h) prose figure — consistent with prior passes' conservatism policy.

## Rejected this pass (all candidates honestly checked)

Quality bar: **instrumented + named device + confirmed stock**. Failed candidates:

| Candidate | Source(s) checked | Rejection reason |
|---|---|---|
| Kawasaki Z900RS | motostatz.com/kawasaki-z900rs-top-speed-acceleration/ | MotoStatz article does NOT name Dragy or any GPS device — same rejection logic as fifth pass earlier today |
| Suzuki GSX-S750 | motostatz.com/suzuki-gsx-s750-acceleration-top-speed-review/ | MotoStatz article does NOT name Dragy or any GPS device |
| Honda CB1000R | Multiple searches | Only ProfessCars/MotorBikeCatalog calculated estimates; no Cycle World / Sport Rider / MotoStatz / MCN instrumented data exists |
| Yamaha XSR700 | motostatz.com/yamaha-xsr700-engine-and-straight-line-performance-review/ | Test bike runs a Mivv full exhaust system ("Our example was equipped with a Mivv full exhaust system, running with the baffle and no tune") — explicitly modified, fails stock bar |
| Ducati Diavel V4 | Multiple searches | No Cycle World/MotoStatz/MCN instrumented data found — only fastestlaps/accelerationtimes calc estimates |
| Honda Africa Twin (CRF1100L) | Multiple searches | Only ProfessCars estimates + forum hearsay; no credentialed instrumented data |
| Honda NC750X | Multiple searches | Only ProfessCars estimates (motorbikecatalog.com); no real instrumented data |
| Triumph Tiger 900 | Multiple searches | No MotoStatz/Cycle World instrumented data found |
| BMW R1250GS | Multiple searches | Only ProfessCars estimates; no MotoStatz/CW instrumented test located |
| Suzuki Katana 1000 | topspeed.com (10.86s @ 133.3 mph quoted) | TopSpeed.com names no source — no drag-strip cite, no Dragy, no Cycle World/MCN attribution. Fails anti-fabrication bar. |
| Kawasaki Z H2 (MotoStatz: 10.13 @ 146 mph, Dragy-named, stock) | motostatz.com/kawasaki-z-h2-acceleration-top-speed/ | Would duplicate the existing "Z H2 2020 Cycle World 9.95s @ 240" benchmark entry — article references base Z H2 not the Z H2 SE catalog row. Source priority (CW > MotoStatz per CLAUDE.md) favors the existing entry. |
| Yamaha MT-09 (MotoStatz: 10.69 @ 129 mph) | motostatz.com/yamaha-mt-09-acceleration/ | Duplicates existing "MT-09 2021 Cycle World 10.95s @ 204" entry |
| Indian FTR 1200 R Carbon | Not separately tested | MotoStatz article covers FTR 1200 S only; no instrumented R Carbon data found in searches |

## Methodology note

Nine benchmark passes have run today (passes 1-8 by earlier agents; pass 8 was a null delivery). Each previous pass mined the obvious MotoStatz/Cycle World wells; this ninth pass had to drill into less-obvious candidates with strict source verification. The 13 rejections logged above represent honest research that didn't meet the bar — preserved here so future passes can skip them and start from a clean candidate frontier.

## Sweep delta

- Before: BENCHMARKS = 108 entries.
- After: BENCHMARKS = 109 entries (+1, Indian FTR 1200 S 2020).

The new entry is the first Indian-brand benchmark and first FTR-family benchmark in the list — adds genuine cluster coverage (litre-muscle naked) rather than piling onto already-well-sampled families.

## Commit message

```
data(benchmarks): add Indian FTR 1200 S (11.20s @ 120 mph, MotoStatz Dragy)
```
