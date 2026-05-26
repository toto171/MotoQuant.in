# Benchmark Import — 2026-05-26

## Summary

Added **3 high-confidence instrumented benchmarks** to `scripts/validation_sweep.py::BENCHMARKS`. All three are from the Cycle World / Sport Rider sportbike-performance-numbers archive (the authoritative Sport Rider timing-strip table) — the same publication and methodology bar already accepted for the GSX-S1000, Daytona 675, GSX-R 600 K6, CBR 600RR 2007 PC40, YZF-R6 2C0 and Tuono V4 1100 entries.

**BENCHMARKS count:** 109 → **112** (+3)
**Matched benchmarks:** 108/112 (vs 105/109 before)
**Mean |Δ|:** 0.312 s
**Bias:** +0.092 s (near-zero)
**Median |Δ|:** 0.185 s

## Adds (all `[verified]`, instrumented)

| Spec | Year | Bench ET | Bench Trap | Sim ET | Δ | Source |
|---|---|---|---|---|---|---|
| Yamaha YZF-R6 (13S) | 2011 | 10.87 s | 128.5 mph (207 km/h) | 10.861 s | **−0.009 s** | Sport Rider 8/11 archive |
| Ducati 848 EVO | 2011 | 10.75 s | 130.77 mph (210 km/h) | 10.290 s | −0.460 s | Sport Rider 1/11 archive |
| MV Agusta F4 1000 R | 2010 | 10.21 s | 149.38 mph (240 km/h) | 10.006 s | −0.204 s | Sport Rider 9/10 archive |

Source URL for all three: `https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/`

### YZF-R6 (13S) — Δ = −0.009 s (essentially perfect)
The 13S generation is the un-benchmarked 2008-2016 catalog row (the 2C0 generation 2006-2007 already has an entry). Used the explicit `"YZF-R6 (13S)"` model pattern to future-proof against the matcher specificity bug filed at `DISPATCH_INBOX.md` (2026-05-25). The tokens `{YZF, R6, (13S)}` cleanly bind to the 2008-2016 row without falling back to the 2C0 entry via subset matching.

### 848 EVO — Δ = −0.460 s (acceptable, cluster-typical)
The 848 EVO is famously hard to launch on its 180-section rear tire with peaky 90° L-twin cam timing. Sport Rider's professional tester pulled 10.75s. Catalog has two `848 EVO` entries (2008-2013 and 2011-2013) with identical specs — `find_spec()` binds to the 2008-2013 entry first via iteration order. Both rows have `disp=849cc, hp=140`, so the binding is benign.

### F4 1000 R — Δ = −0.204 s (within cluster band)
The 2010 F4 1000 R refresh produced ~186 hp claimed. Sport Rider's 149.38 mph trap fits the litre-sport upper cluster alongside the CBR1000RR 2010 (also in this archive at 9.67/150.3 — already benched) and S 1000 RR 2015 (CW 9.90/240 km/h — already benched). The 10.21s ET is slightly slow vs the cluster average because the F4's peak power at ~12,500 rpm is harder to harness off the line than CBR/S1000RR's torque-broad designs.

## Other candidates investigated and rejected

| Candidate | Reason for rejection |
|---|---|
| Ducati Diavel V4 (1158cc) | MotoStatz article tests 1198cc Testastretta variant, not the V4 in catalog (engine mismatch — same as the seventh-pass rejection) |
| Ducati Multistrada V4 (1158cc) | MotoStatz article describes 1258cc engine (the new V4 RS), not the 1158cc V4 in catalog; also does not name Dragy |
| Ducati Streetfighter V4 | MotoStatz article does not explicitly name Dragy (fails post-eighth-pass methodology bar) |
| Triumph Speed Triple 1200 RS | No Cycle World / Sport Rider / MCN instrumented test found; only AccelerationTimes & FastestLaps (calculated) |
| Honda CB1000R 2021-2024 catalog row | Sport Rider archive has CB1000R 2011 but catalog only has 2021-2024 row (architecture mismatch) |
| MotoStatz Kawasaki Z900RS | Article does not name Dragy explicitly (already rejected in sixth pass) |
| MotoStatz MT-09 / FZ-09 | Same as Z900RS — no Dragy mention in body. Existing CW 2021 entry already covers same engine. |
| MotoStatz Versys 1000 / Africa Twin | No MotoStatz article found |
| MotoStatz Triumph Tiger / Suzuki V-Strom | No MotoStatz article found |
| MotoStatz Pan America 1250 | No MotoStatz article found |
| Sport Rider archive CBR1000RR 2010, ZX-10R 2010-12, CBR 600RR 2013 | All bind to already-benchmarked catalog rows |
| Sport Rider archive GSX-R 600 2013, ZX-6R 2013, GSX-R 1000 2012 | No matching catalog row (later L1 generations not in catalog at those year ranges) |
| Sport Rider archive YZF-R1 2012 | Catalog row already benchmarked |
| Sport Rider archive CBR1000RR SP 2014 | No matching catalog row (catalog has CBR 1000RR Fireblade SP 2017 only) |
| Sport Rider archive Aprilia RSV4 Factory 2010 / RSV4 R 2010 | No matching catalog row (catalog has RSV4 1000 2009-2014 — benched; RSV4 Factory 2021-2024 — benched) |
| Sport Rider archive Ducati 1198 2009 | No matching catalog row |
| Sport Rider archive Triumph Daytona 675 2006 | No matching catalog row (catalog has 2013-2017 generation only) |

## Anti-fabrication compliance

- All three adds bind to existing catalog rows (verified via `find_spec()` before edit).
- All three adds pass the production sim path and produce physically-plausible Δ values (none exceeding 0.5s).
- All three sources are from Cycle World's curated Sport Rider archive table — not a 0-100 multiplier estimate, forum claim, or marketing kit.
- No DERIVED-tier entries were added or swapped. The inbox `[research]` request to verify Apache RTR 200 4V / MT-15 V2 DERIVED entries (2026-05-20) was investigated but no instrumented replacement data was found in this session's search budget.

## What was NOT done

- The matcher specificity bug (DISPATCH_INBOX 2026-05-25 `[urgent]`) was read but not touched per agent scope. Note: the bug does not affect the three adds in this pass — `YZF-R6 (13S)` uses the explicit suffix, and `848 EVO` + `F4 1000 R` have no token-subset collisions with other catalog rows.
- DERIVED entry replacement for Apache RTR 200 4V / MT-15 V2 — no Indian Autos Mag / BikeWale / Dragy timeslip data found in honest searching.

## Files touched

- `scripts/validation_sweep.py` — appended 3 entries inside the tenth pass section (lines after existing ninth-pass FTR 1200 S row).
- `reports/benchmark_import_2026-05-26.md` — this report.
