# Benchmark Import — 2026-05-24 (afternoon pass)

Three additional high-confidence instrumented quarter-mile benchmarks added to
`scripts/validation_sweep.py::BENCHMARKS` (also consumed by
`scripts/sweep_with_clusters.py`, which imports the same list).
BENCHMARKS count: **84 → 87**. No existing entries touched; no reference
baselines (K5/R1/Hayabusa) altered. This is the afternoon pass on top of
the morning Z900/MT-07 work documented in
`reports/benchmark_import_2026-05-24.md`.

## Additions

### 1. Suzuki GSX-S1000 (2021-2024, 999 cc I4 naked)
- Tuple: `("Suzuki", "GSX-S1000", 2022, 10.60, 214, "Sport Rider (Cycle World sportbike-performance-numbers, timing-strip)")`
- **ET:** 10.60 s
- **Trap:** 214 km/h (133 mph)
- **Source:** Sport Rider's published sportbike-performance-numbers table
  at cycleworld.com/sport-rider/tech/sportbike-performance-numbers
  (Sport Rider's timing-strip results). Sport Rider is already the cited
  source for the GSX-R 1000 K7/K9/L7 / ZX-10R 2004/2011 / R1 2004/2009 /
  CBR1000RR 2008 / 1098 entries above — same publication, same
  instrumented-test methodology.
- **Catalog match:** `SUZUKI_GSXS1000_2022` (999 cc I4, 152 hp, naked,
  2021-2024 model run). year_hint=2022 falls cleanly inside the range.
- **Why it meets the bar:** Sport Rider is on the project's accepted
  source list. The published number is from the timing-strip
  performance-numbers table, not a 0-100 multiplier or marketing claim.

### 2. Triumph Street Triple 765 RS (2020-2024, 765 cc triple naked)
- Tuple: `("Triumph", "Street Triple 765 RS", 2021, 10.79, 212, "MotoStatz 2021 (Dragy, stock instrumented)")`
- **ET:** 10.79 s
- **Trap:** 212 km/h (132 mph)
- **Source:** MotoStatz Dragy-GPS-measured stock run. MotoStatz is the
  same source bar already used in the existing BENCHMARKS list for the
  Yamaha YZF-R7, Ninja 400, Ninja 650, Z 650, MT-10 entries (all
  MotoStatz figures in this list are Dragy-measured).
- **Catalog match:** `TRIUMPH_STREET_TRIPLE_765RS_2020` (765 cc triple,
  123 hp, naked, 2020-2024 model run).
- **Why it meets the bar:** Dragy is one of the named instrumented
  measurement devices in the CLAUDE.md acceptance bar; the figure
  cross-checks across FastestLaps + AccelerationTimes at the same
  10.79 s value. Confirmed via two independent WebSearches.

### 3. Ducati Panigale V2 (2020-2024, 955 cc Superquadro V2 sport)
- Tuple: `("Ducati", "Panigale V2", 2022, 10.44, 228, "MotoStatz 2022 (Dragy, stock instrumented)")`
- **ET:** 10.44 s
- **Trap:** 228 km/h (142 mph)
- **Source:** MotoStatz Dragy stock instrumented run.
- **Catalog match:** `DUCATI_PANIGALE_V2_2020` (955 cc Superquadro V2,
  155 hp, sport, 2020-2024 model run). This is distinct from the
  existing 1199 Panigale (2012), 1299 Panigale (2015), and 959 Panigale
  (2016-2019) catalog entries; the V2 is the 2020+ Superquadro refresh,
  not a typo for V4.
- **Why it meets the bar:** Same MotoStatz/Dragy source bar described
  above. Catalog entry has zero existing benchmark — this adds the first
  data point for the 955 cc Superquadro mid-cluster.

## Rejected during research (audit trail)

- **Kawasaki Ninja H2R 9.64 s @ 164 mph (MotoStatz)** — H2R is track-only
  and unable to compete in sanctioned drag events; the MotoStatz figure
  may be a calculated extrapolation rather than a Dragy stock run.
  Source-bar ambiguous, rejected. The morning pass did not add an H2R
  entry either; the existing Cycle World H2 9.62 s figure remains the
  canonical hyperbike anchor.
- **Aprilia Tuono V4 1100 Factory 10.2 s** — appears across
  AccelerationTimes and MotorBikeCatalog "Full performance review" pages
  (years 2016-2021), but the underlying figure is calculated via
  ProfessCars from 0-100 × multiplier rather than instrumented. Same
  rejection logic as the morning pass's MotorBikeCatalog reject list.
- **Honda CBR650R / CB650R** — searched for instrumented Sport Rider /
  Cycle World data. Found AccelerationTimes derived figures only.
  Skipped to avoid inflating matched-N with calculated entries.
- **BMW S 1000 R (naked) 10.41 s @ 144 mph** — surfaced via search but
  no concrete publication+year attribution. Rejected pending tighter
  sourcing (consistent with the morning pass's BMW S 1000 R reject).
- **BMW M 1000 R / S1000R** — MCN review reads as a road-test, no
  timing-strip data surfaced. Skipped.

## Sweep impact (predicted)

These three additions land in clusters that the May-3 sweep flagged as
having a relatively low N relative to cluster importance:

- GSX-S1000 → **litre-sport-600-1000** cluster (N≈29). Adds another
  naked-bike data point alongside the morning's Z900 entry, helping
  resolve any category-flavoured physics drift that gets averaged out
  by the fairing-dominated portion of the cluster.
- Street Triple 765 RS → **litre-sport-600-1000** cluster. The 765 cc
  triple is uniquely positioned between the 600 cc I4 sport and the 850-
  1000 cc naked classes — its real-world ET is a useful anchor for the
  category-flavoured physics dispatch's `litre_sport_600_1000` profile.
- Panigale V2 → **litre-sport-600-1000** cluster. Closes the 955 cc
  Superquadro V2 generation gap left between the 1199/1299 Panigale
  entries and the V4/V4R entries.

All three round-trip cleanly via the `sweep_with_clusters.py` matcher:
each new tuple matches exactly one catalog entry (verified via the
`_wb_match` word-boundary token-set check), and the year_hint falls
inside the catalog spec's year range, so the year-match path is taken
(no fallback to entries[0]).

## Files touched
- `/tmp/mq-session-1779654637-632/repo/scripts/validation_sweep.py` —
  three entries appended at the end of the `BENCHMARKS` list, with a
  new `# ── 2026-05-24 benchmark-import agent (afternoon pass)` divider
  preserving the file's chronological commentary convention.
- `/tmp/mq-session-1779654637-632/repo/reports/benchmark_import_2026-05-24_pm.md` —
  this report.

## Escalations / carry-forward
- None. All rejected candidates either lacked a credentialed source or
  had a calculated-not-measured figure. No urgent inbox items raised.
- The Panigale V2 entry could later be cross-checked against a Cycle
  World comparison-test article if one surfaces (the 2022 V2 Bayliss
  CW first-ride did not include a timing-strip number per the snippet);
  this would shore up trap-speed precision.
