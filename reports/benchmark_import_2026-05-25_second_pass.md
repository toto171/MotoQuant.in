# Benchmark Import — 2026-05-25 (Second Pass)

Agent: benchmark-import
Session: 1779690641-692

---

## Summary

Added **4 new instrumented quarter-mile benchmarks** to
`scripts/validation_sweep.py::BENCHMARKS`. All four come from the
Cycle World / Sport Rider `sportbike-performance-numbers` archive
(`cycleworld.com/sport-rider/tech/sportbike-performance-numbers/`),
which is the same authoritative timing-strip table already cited by
the existing GSX-S1000, Daytona 675, and several CBR/YZF entries.

Reference baselines unchanged: K5 10.0334s / R1 10.2859s /
Hayabusa 10.4712s — all Δ=+0.0000.

---

## Benchmarks Added

| # | Bike | Year | ET (s) | Trap | Source |
|---|------|------|--------|------|--------|
| 1 | Suzuki GSX-R 600 (K6) | 2006 | 10.641 | 132.71 mph / 214 km/h | Sport Rider timing-strip |
| 2 | Honda CBR 600RR (PC40) | 2007 | 10.844 | 127.68 mph / 206 km/h | Sport Rider timing-strip |
| 3 | Yamaha YZF-R6 (2C0) | 2007 | 10.854 | 127.44 mph / 205 km/h | Sport Rider timing-strip |
| 4 | Aprilia Tuono V4 1100 Factory | 2021* | 10.30 | 139.2 mph / 224 km/h | Sport Rider / Cycle World 2016 Factory |

*The Tuono V4 1100 catalog entry covers 2021-2024; the Cycle World test
is the 2016 Factory which runs the same 1077 cc 175 hp V4 architecture
(the 2021 facelift was electronics/aero/brakes, no engine change).
Year_hint=2021 routes cleanly to the catalog entry.

All four catalog entries verified to match year-hint via `find_spec()`.

---

## Source Verification

**Cycle World sportbike-performance-numbers archive** (fetched directly
this session via WebFetch):

> Suzuki GSX-R600 ('06): 10.641 @ 132.71 mph
> Suzuki GSX-R600 ('07): 10.979 @ 126.57 mph
> Honda CBR600RR ('07): 10.844 @ 127.68 mph
> Yamaha YZF-R6 ('07): 10.854 @ 127.44 mph
> Aprilia Tuono V4 1100 Factory ('16): 10.30 @ 139.2 mph

For the GSX-R 600 I took the K6 (10.641) over the K7 (10.979) — same
engine generation; the K6 is the cleaner pass at higher trap.

---

## Candidates Searched But Rejected

| Bike | Reason |
|------|--------|
| Triumph Speed Triple 1200 RS | AccelerationTimes data is FastestLaps-derived (calculated), not Dragy/Vbox/timing-strip. No primary instrumented source found behind the CW 2022 review paywall. Queued for `[research]`. |
| Tuono V4 1100 (2021-2024 facelift) | Only ProfessCars/MotorBikeCatalog calculated estimates (10.2s @ 0-100 multiplier). Used the 2016 Factory Sport Rider instrumented number instead — same engine architecture. |
| Ducati Diavel V4 (2023+) | No primary instrumented source found this session. Queued for future research. |
| MV Agusta Brutale 800 Dragster | No primary instrumented source found this session. Queued. |
| Yamaha XSR900 (2022+, CP3 890cc) | No primary instrumented source found this session. Queued. |

---

## Sweep Results (post-add)

```
python3 scripts/sweep_with_clusters.py reports/sweep_et_2026-05-25_postimport.json
```

| Metric | Value |
|---|---|
| BENCHMARKS rows | 93 → 97 |
| Matched-N | 122 → **129** |
| Overall mean\|Δ\| | 0.359s |
| Overall bias | +0.069s |
| Within ±0.10s | 28 (22%) |
| Within ±0.20s | 60 (47%) |
| Within ±0.50s | 106 (82%) |
| Within ±1.00s | 121 (94%) |
| Top-10 mean\|Δ\| | 0.0140s |
| K5 baseline | 10.0334s (Δ +0.0000) |
| R1 baseline | 10.2859s (Δ +0.0000) |
| Hayabusa baseline | 10.4712s (Δ +0.0000) |
| Catalog | 490 bikes, 0 errors, 0 DNF |

### Cluster bias

| Cluster | N | mean\|Δ\| | bias |
|---|---|---|---|
| litre-sport-195+ | 28 | 0.171s | -0.015s |
| litre-sport-600-1000 | **49** | 0.210s | -0.076s |
| mid-twin-500-700 | 8 | 0.213s | +0.213s |
| entry-200-300 | 6 | 0.533s | +0.214s |
| mid-twin-300-500 | 16 | 0.507s | -0.137s |
| cruiser-1300+ | 2 | 0.407s | +0.407s |
| two-stroke | 5 | 0.683s | +0.338s |
| entry-150-200 | 8 | 1.387s | +0.895s |
| other | 7 | 0.412s | +0.363s |

The four new 600cc supersport entries land in `litre-sport-600-1000`
and the Tuono in `litre-sport-195+`. The litre-sport-600-1000 cluster
(N=49) is the most populous bucket and remains near zero bias.

---

## Files Modified

- `scripts/validation_sweep.py` — 4 new BENCHMARKS entries appended
  (lines ~384-460, after the 2026-05-25 R nineT entry)
- `scripts/sweep_with_clusters.py` — no edit needed, it imports
  `BENCHMARKS` from `validation_sweep.py`

## Sweep Output

- `reports/sweep_et_2026-05-25_postimport.json` (493 rows)

## Suggested commit message

```
benchmark: add 4 instrumented Sport Rider entries (GSX-R 600, CBR 600RR, YZF-R6, Tuono V4 1100)
```
