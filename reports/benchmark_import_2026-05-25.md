# Benchmark Import — 2026-05-25

Agent: benchmark-import  
Session date: 2026-05-25

---

## Summary

Added **3 new instrumented quarter-mile benchmarks** to `scripts/validation_sweep.py::BENCHMARKS`.
Matched-N increased from **90 → 122** (sweep counts all benchmark-vs-catalog matches; the jump reflects
both the 3 new entries and the expanded 490-bike catalog matching more existing benchmarks).

Reference baselines unchanged: K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s — all Δ=+0.0000.

---

## Benchmarks Added

### 1. Honda CBR 600RR (2017) — MotoStatz Dragy

| Field | Value |
|---|---|
| Manufacturer | Honda |
| Model substr | CBR 600RR |
| Year hint | 2017 |
| ET | 10.92 s |
| Trap | 211 km/h (131 mph) |
| Source | MotoStatz 2017 (Dragy, stock instrumented) |
| Catalog entry | HONDA_CBR600RR_PC40B_2013 (2013-2020) |

**Source verification:** MotoStatz page at `motostatz.com/honda-cbr600rr-acceleration-and-top-speed/`
explicitly states "10.92 seconds with a terminal speed of 131 mph" on a 2017 stock CBR600RR. The article
references a Dragy device for 60-130 mph acceleration runs; MotoStatz quarter-mile methodology is identical
to the Street Triple 765 RS / Panigale V2 / RS 660 / KTM 890 Duke R entries already in the list.

---

### 2. Triumph Daytona 675 (2013) — Sport Rider timing strip

| Field | Value |
|---|---|
| Manufacturer | Triumph |
| Model substr | Daytona 675 |
| Year hint | 2013 |
| ET | 10.32 s |
| Trap | 219 km/h (136.0 mph) |
| Source | Sport Rider (Cycle World sportbike-performance-numbers, timing-strip 2013) |
| Catalog entry | TRIUMPH_DAYTONA_675 (2013-2017) |

**Source verification:** The Cycle World sportbike-performance-numbers archive at
`cycleworld.com/sport-rider/tech/sportbike-performance-numbers/` is the Sport Rider timing-strip results
table covering every Sport Rider instrumented drag-strip test since 1996. The page was fetched directly
during this session; it returned "Daytona 675 ('13): 10.32 @ 136.0". This is the same source bar already
used for the Suzuki GSX-S1000 entry (10.60s @ 133 mph) in the existing list.

Context: The 2013 Daytona 675 received a +6 hp bump and ~3 kg weight reduction over the 2007-2012 variant.
The same table shows 2006: 10.533s and 2008: 10.53s; the 2013 improvement to 10.32 is physically
consistent with those changes at expert magazine-tester pace.

---

### 3. BMW R nineT (2014) — Cycle World timing strip

| Field | Value |
|---|---|
| Manufacturer | BMW |
| Model substr | R nineT |
| Year hint | 2014 |
| ET | 11.05 s |
| Trap | 193 km/h (120 mph) |
| Source | Cycle World 2014 (timing-strip, retro comparison test) |
| Catalog entry | BMW_RNINET_2014 (2014-2020) |

**Source verification:** Cycle World December 2014 comparison test (BMW R nineT vs Honda CB1100 vs
Indian Scout vs Moto Guzzi Griso) at
`cycleworld.com/2014/12/01/retro-motorcycles-comparison-test-review-with-photos-and-specifications/`.
Confirmed 11.05s @ 120 mph by three independent web searches; figure also cross-referenced against
the BMW NineT forum thread (ninetowners.com/threads/r9t-quarter-mile-times.62322/) where the Cycle
World figure is the most-cited magazine number. Cycle World is the highest-priority source on this
project's accepted publication list.

---

## Candidates Searched But Rejected

| Bike | Reason for rejection |
|---|---|
| Honda CB1000R (2019-2021) | No instrumented primary source found for the SC80 Neo Sports Cafe generation. MotorbikeCatalog figures are calculated estimates, not measured ETs. Queued for further research. |
| Triumph Speed Triple 1200 RS/RR | Only aggregator databases (AccelerationTimes, zeroto60times) show 10.7s; no primary instrumented source (Cycle World, Sport Rider, MotoStatz) found with named instrument and trap speed. Cycle World 2022 review exists but page content inaccessible (paywalled). |
| MotoStatz Triumph Daytona 675 10.70s @ 134 mph | Page explicitly states "our 675 was not stock" — fails stock-bike requirement. |
| MCN USA Daytona 675 11.17s @ 120 mph | Secondary-source re-quote (appeared in forums citing MCN); could not verify primary MCN USA article directly. Not used in favour of the directly-verified Sport Rider table entry. |
| AccelerationTimes Honda CB1000R 10.7s | Sourced from MotorbikeCatalog calculated estimates per the page footer. Fails instrumented bar. |
| AccelerationTimes BMW R nineT 12.1s | FastestLaps-sourced; conflicts with Cycle World 11.05s. FastestLaps source could be a different test or a consumer (not magazine) run. Used the primary Cycle World figure instead. |

---

## Sweep Results Before / After

| Metric | Before | After |
|---|---|---|
| BENCHMARKS rows | 90 | 93 |
| Matched-N (sweep) | ~90 (prior session) | 122 |
| Overall mean\|Δ\| | ~0.368s | 0.368s |
| Overall bias | ~+0.06s | +0.061s |
| K5 baseline | 10.0334s (Δ 0) | 10.0334s (Δ 0) |
| R1 baseline | 10.2859s (Δ 0) | 10.2859s (Δ 0) |
| Hayabusa baseline | 10.4712s (Δ 0) | 10.4712s (Δ 0) |

The jump from ~90 to 122 matched benchmarks reflects the expanded 490-bike catalog (up from ~336)
matching more existing benchmarks in addition to the 3 new entries.

---

## Files Modified

- `/tmp/mq-session-1779683449-749/repo/scripts/validation_sweep.py` — 3 new BENCHMARKS entries added
  at lines ~328-393 (after the KTM 890 Duke R entry)
