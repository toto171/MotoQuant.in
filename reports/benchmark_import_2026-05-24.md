# Benchmark Import Research — 2026-05-24

**Result: 0 high-confidence benchmarks added.**

This is a negative-finding research artifact per CLAUDE.md Kaizen policy.

---

## Pre-research state

- `BENCHMARKS` list: 79 entries (65 non-DERIVED, 14 DERIVED)
- Benchmarks with matching catalog spec: **75 / 79**
- Reference baselines (K5 / R1 / Hayabusa): **+0.0000s delta on all three** (verified)

---

## Candidates investigated

The following bikes were identified as having zero benchmarks in the BENCHMARKS list and as being in the current 487-bike catalog. They were prioritised by expected data availability (litre-class and mid-class bikes most likely to appear in Cycle World / MCN / Sport Rider archives).

| Bike | Year range in catalog | Research outcome |
|---|---|---|
| KTM 1390 Super Duke R EVO | 2024–2026 | No instrumented quarter-mile found — Cycle World published a first-ride and dyno test (190 hp verified), but no drag-strip ET |
| Kawasaki Z900RS | 2018–2026 | MotoStatz reports 11.35s @ 120.7 mph; methodology undisclosed — rejected |
| Triumph Street Triple 765 RS | 2020–2024 | DragTimes timeslips from 2017 RS found (10.720 @ 126.940 mph at Santa Pod); year mismatch with catalog spec — see note |
| Triumph Street Triple 765 R | 2023–2026 | No instrumented quarter-mile found in any source |
| Harley-Davidson Nightster RH975 | 2022–2026 | Cycle World published dyno test (78.5 hp at wheel); no drag-strip ET found |
| KTM 125 Duke | 2017–2026 | No quarter-mile instrumented data found (125cc class rarely drag-tested) |
| Husqvarna Svartpilen 250 | 2024–2026 | No quarter-mile instrumented data found |
| Honda CB125R | 2018–2026 | No quarter-mile instrumented data found (125cc class) |

---

## Detailed findings per candidate

### KTM 1390 Super Duke R EVO (2024–2026)

Sources checked: Cycle World first-ride review (2024), Cycle World buyer's guide, Cycle News review (2024), RevZilla road and track test, MotoStatz, AccelerationTimes, FastestLaps.

- **Cycle World** published "2024 KTM 1390 Super Duke R Evo First Ride Review" and a dyno test but no drag-strip quarter-mile figures.
- MotoStatz has the older **KTM 1290 Super Duke R** at 10.21s @ 144.8 mph — already in BENCHMARKS (Cycle World 2022: 10.15s @ 230 km/h).
- The 1390 is derived from the 1290 EVO platform per KTM press kit; its ET should be in the 9.95–10.10s range, but no publication has published an instrumented drag test as of May 2026.
- **Decision: no addition.**

### Kawasaki Z900RS (2018–2026)

Sources checked: Cycle World Z900RS Café review (2018), Cycle News full test (2018), MCN 2026 review, Rider Magazine 2018, MotoStatz, AccelerationTimes (via FastestLaps), z900rs.co.uk forum thread.

- **MotoStatz** consistently reports 11.35s @ 120.7 mph (194.3 km/h) but the methodology page does not disclose whether this is GPS, Vbox, Dragy, or a timing strip. The site presents results as factual without citing the test event.
- **AccelerationTimes** (via FastestLaps) shows 13.0s @ 116 mph — clearly an error; too slow for a 125 hp naked.
- No Cycle World, Sport Rider, or MCN instrumented test with a named measurement device was found.
- The related Z900 (non-RS) has a Cycle World figure of 10.95s cited in secondary sources (including a Bay Area Riders Forum thread confirming the Cycle World source), but that bike is already catalogued separately and not newly added.
- **Decision: no addition. MotoStatz methodology undisclosed — fails the "named measurement device" gate.**

### Triumph Street Triple 765 RS — year-mismatch case

Sources checked: DragTimes.com timeslips (two entries), Sport Rider performance numbers archive (Cycle World website), MCN 2023 review, Cycle News 2018 full test, MotoStatz, AccelerationTimes, FastestLaps.

**Best data found:**
- DragTimes entry 30470: 2017 Triumph Street Triple 765 RS, stock, **10.976 @ 126.280 mph**, real drag strip
- DragTimes entry 31211: 2017 Triumph Street Triple 765 RS, stock, **10.720 @ 126.940 mph** at Santa Pod Raceway (RWYB event, timing-strip measurement, May 2020)

These are real timing-system measurements at sanctioned drag events. Consistency across two independent runs (both submitted as stock 2017 RS) supports their validity. They also corroborate the Sport Rider data for the older 675R (10.76s @ 124.4 mph in 2011).

**Why not added:** The catalog entries are "Triumph Street Triple 765 RS (2020–2024)" and "Triumph Street Triple 765 R (2023–2026)". The DragTimes data is from **2017 RS** (123 hp). The 2020+ RS has 130 hp, and byear=2017 would not fall within either spec's year_from–year_to range. Using byear=2020 with 2017 data would misrepresent the test year. The expected 2020+ RS time would be ~0.1–0.2s faster (≈10.55–10.75s) based on the 7 hp gain, but that would be a derived estimate — exactly the category CLAUDE.md asks to avoid.

**Archived for future use:** If a DragTimes or Dragy-documented timeslip surfaces from a 2020+ RS, it should yield ~10.5–10.7s @ 128–130 mph and can be added with the DragTimes / Dragy citation.

**Historical context for reference (not added):**
The Sport Rider performance archive (cycleworld.com/sport-rider/tech/sportbike-performance-numbers/) contains Street Triple data up to 2014:
- Street Triple R 2011 (675cc): 10.76s @ 124.4 mph — Sport Rider 10/11
- Street Triple R 2013 (675cc): 11.13s @ 123.7 mph — Sport Rider 5/13
- Street Triple R 2014 (675cc): 11.00s @ 121.9 mph — Sport Rider 5/14

These are for the older 675cc variant not currently in the catalog.

---

## Sources consulted and rejected

| Source | Bike | Figure | Rejection reason |
|---|---|---|---|
| MotoStatz | Z900RS | 11.35s @ 120.7 mph | Methodology undisclosed |
| AccelerationTimes (FastestLaps) | Z900RS | 13.0s @ 116 mph | Clearly erroneous (too slow for 125 hp) |
| DragTimes (2 entries) | Street Triple 765 RS 2017 | 10.720–10.976s @ 126 mph | Year mismatch with 2020–2024 catalog spec |
| MotoStatz | Street Triple 765 RS | 10.79s @ 132 mph | Methodology undisclosed |
| Forum secondary reference | Street Triple 765 R | 10.89s @ 125.74 mph (Cycle World 2017) | Source not directly verifiable; year outside catalog range |

---

## Recommended follow-up actions

1. **Street Triple 765 RS 2020+:** Search Dragy app leaderboards or YouTube dragy timeslip videos for 2020–2024 RS. The existing DragTimes 2017 data provides a validated floor; a 2020+ result should add one clean benchmark. Search query: `"Street Triple 765 RS" 2020 OR 2021 OR 2022 dragy timeslip 1/4 mile`.

2. **Z900RS:** Contact MotoStatz directly (or find their methodology documentation) to determine if the 11.35s figure is from a Vbox/Dragy instrumented test. If confirmed, it qualifies for addition as "MotoStatz (instrumented, methodology unspecified)" — consistent with existing BENCHMARKS entries like "MotoStatz 2020 (instrumented)" for R15 V3.

3. **KTM 1390:** Check Motorrad magazine (German) or Motorcyclist Online archives — European publications more frequently publish drag-strip performance figures for KTM models. The 1390 is the flagship naked-class target.

4. **OZx ZX-10R 2006 / 2008 follow-up:** CLAUDE.md flags these as needing year-specific Sport Rider tests to replace the generic 2004 figure applied to all years. Still unresolved per this session.

---

## Sweep state (post-research, no changes made)

- BENCHMARKS entries: **79** (unchanged)
- Matched to catalog spec: **75 / 79** (unchanged)
- K5 / R1 / Hayabusa baselines: **+0.0000s** on all three (verified)

No files were modified.
