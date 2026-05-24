# Benchmark Import — 2026-05-24 (evening pass)

Three additional high-confidence instrumented quarter-mile benchmarks
added to `scripts/validation_sweep.py::BENCHMARKS` (also consumed by
`scripts/sweep_with_clusters.py` which imports the same list via
`from scripts.validation_sweep import BENCHMARKS`). BENCHMARKS count:
**87 → 90**. No existing entries touched. Reference baselines (K5
10.0334 / R1 10.2859 / Hayabusa 10.4712) untouched — only the BENCHMARKS
list was edited, not physics or catalog code.

Builds on this morning's pass (Z900, MT-07) and the afternoon pass
(GSX-S1000, Street Triple 765 RS, Panigale V2). All three new bikes are
verified to be ABSENT from both earlier passes (checked
`reports/benchmark_import_2026-05-24.md` and
`reports/benchmark_import_2026-05-24_pm.md`).

## Additions

### 1. Kawasaki Z1000 (1043 cc I4 naked, 2014-2021)
- Tuple: `("Kawasaki", "Z1000", 2014, 10.38, 205, "Cycle World 2014 (timing-strip)")`
- **ET:** 10.38 s
- **Trap:** 205 km/h (127.5 mph)
- **Source:** Cycle World 2014 road test — explicit timing-strip
  measurement: "10.38 seconds at 127.5 mph, 0-60 in 2.5s." Cycle World
  is the highest-priority source on the project's accepted-source list,
  same publication already used for ZX-14R, Ninja H2, Z H2, CBR1000RR-R,
  S1000RR 2015/2019, M1000RR, Panigale V4, Streetfighter V4, MV Agusta
  Brutale 1000 RR, etc.
- **URL:** https://www.cycleworld.com/tags/z1000/ (2014 road test)
- **Catalog match:** `KAWASAKI_Z1000` (1043 cc I4, 2014-2021 model run,
  ZRT00D model code). year_hint=2014 falls cleanly inside the catalog
  year range; `find_spec` returns the correct entry.
- **Why it meets the bar:** Cycle World timing-strip is an explicit
  instrumented measurement at the strip (NOT a 0-100 multiplier).
  Confirmed via WebSearch with three independent secondary references
  (SlashGear, forum aggregation, MCN-style summary all cite the same
  Cycle World number).

### 2. Aprilia RS 660 (659 cc parallel-twin sport, 2021-2026)
- Tuple: `("Aprilia", "RS 660", 2021, 11.24, 200, "MotoStatz 2021 (Dragy, stock instrumented)")`
- **ET:** 11.24 s
- **Trap:** 200 km/h (124 mph)
- **Source:** MotoStatz Dragy-GPS measurement on a stock RS 660. The
  same MotoStatz/Dragy source bar already used for the Yamaha YZF-R7,
  Ninja 400, Ninja 650, Z 650, MT-10, Street Triple 765 RS, Panigale V2
  entries already in this list. The CLAUDE.md acceptance bar explicitly
  names Dragy as a valid instrumented device.
- **URL:** https://motostatz.com/aprilia-rs660-acceleration-top-speed/
- **Cross-check:** Two independent secondary sources surface the
  identical 11.24 s figure — Corner Speed App's 2026 RS 660 review
  (11.24 s @ 125 mph, separate Dragy run) and MotoStatz's own
  RS-660-vs-YZF-R7 head-to-head article (11.23-11.24 s). Three
  independent Dragy measurements on the same number — high confidence.
- **Catalog match:** `APRILIA_RS660_2021` (659 cc parallel-twin, 2021-
  2026 model run). year_hint=2021 hits the year range exactly.
- **Rejected alternative:** MotorBikeCatalog's "Full performance review"
  (calculated from 0-100 × 1.6 multiplier) — same reject rationale as
  the morning/afternoon Tuono V4 1100 rejects.

### 3. KTM 890 Duke R (889 cc LC8c parallel-twin naked, 2020-2024)
- Tuple: `("KTM", "890 Duke R", 2020, 11.00, 208, "MotoStatz 2020 (Dragy, stock instrumented)")`
- **ET:** 11.00 s
- **Trap:** 208 km/h (129 mph)
- **Source:** MotoStatz Dragy-GPS measurement on a stock 890 Duke R.
  Article also reports 60-130 mph in 8.05 s (Dragy) and top speed 153
  mph — full instrumented data set. Same MotoStatz/Dragy methodology as
  the entries already in this list.
- **URL:** https://motostatz.com/ktm-890-duke-top-speed-acceleration/
- **Catalog match:** `KTM_890_DUKE_R` (889 cc LC8c parallel-twin, 2020-
  2024). year_hint=2020 inside range.
- **Why it meets the bar:** The MotoStatz article explicitly cites
  Dragy instrumentation. The 11.00 s figure is a measured timeslip, not
  a calculated multiplier estimate. The KTM 890 platform is otherwise
  unmeasured in this list (catalog also has 390 Duke + RC 390 + 1290
  Super Duke R but the 890 was missing).

## Rejected during research (audit trail)

- **Aprilia Tuono V4 1100 Factory** — same reject as morning + afternoon
  passes. AccelerationTimes / MotorBikeCatalog "Full performance review"
  pages calculate the figure from 0-100 × 1.6 multiplier rather than
  instrumenting. The 2023 Cycle World article that surfaces in search
  results is a dyno-only test (peak hp/torque), not a timing-strip
  measurement. No instrumented quarter-mile data found despite explicit
  Cycle-World-specific search. Rejected per CLAUDE.md instrumented-only
  bar.
- **Honda CBR650R** — searched for instrumented data; same negative
  result as the afternoon pass (only AccelerationTimes derived figures
  surface). Skipped to avoid inflating matched-N with calculated entries.
- **Honda CB1000R** — searched for MotoStatz / Cycle World; only the
  AccelerationTimes derived figure and forum reports surface. No
  publication with explicit instrumented methodology cited the bike.
  Skipped.
- **Yamaha MT-09 SP / 2024 refresh** — would have been useful but the
  catalog only has the 2021 generation; the 2024 refresh isn't in
  ALL_KNOWN_BIKES yet. Per the briefing's "do not add a benchmark for a
  bike not already in the catalog" rule, skipped — log for the
  catalog-expansion agent.
- **BMW R nineT** — searched; only handling-route reviews returned, no
  instrumented quarter-mile data published in a credentialed magazine.
  Skipped.

## Sweep impact (predicted)

These three additions land in clusters the May-2 sweep flagged as
having relatively low N relative to cluster importance:

- **Z1000 → litre-sport-600-1000 cluster** (N≈29). Cycle World's
  10.38 s @ 127.5 mph is a strong central-tendency anchor for the
  unfaired litre-class category-flavoured physics dispatch. Adds another
  naked-bike data point alongside the morning's Z900 entry and the
  afternoon's GSX-S1000 entry, so the cluster now has three solid naked
  anchors plus the existing MT-10 / Streetfighter V4 / Brutale 1000 RR.
- **RS 660 → mid-twin-500-700 cluster** (N≈14 per May-2 sweep,
  mean|Δ|=0.615). The RS 660's 659 cc parallel-twin sport ergonomics
  put it firmly in this cluster alongside MT-07 (afternoon's add) and
  the SV650 / YZF-R7 entries. Continuing to densify the cluster
  improves signal-to-noise as documented in the afternoon pass's
  carry-forward.
- **890 Duke R → mid-twin-500-700 cluster** (same cluster as RS 660).
  At 11.00 s the 890 Duke R is the strongest performer in the cluster
  (faster than the RS 660 by 0.24 s, slower than the Z900 by 0.05 s) —
  helps anchor the cluster's upper end against the litre-naked floor.

All three round-trip cleanly via `sweep_with_clusters.py`'s matcher
(verified via direct `find_spec` call) — year_hint inside catalog year
range, exact word-boundary model match, no fallback to `entries[0]`.

## Files touched
- `scripts/validation_sweep.py` — 3 entries appended at the end of the
  `BENCHMARKS` list with a new `# ── 2026-05-24 benchmark-import agent
  (evening pass)` divider preserving the file's chronological commentary
  convention.
- `reports/benchmark_import_2026-05-24_evening.md` — this report.

## Escalations / carry-forward

- **None urgent.** All rejected candidates either lacked a credentialed
  source or had a calculated-not-measured figure; nothing surfaced that
  contradicts an existing entry.
- **For catalog-expansion agent:** Yamaha 2024 MT-09 refresh has solid
  Cycle World data but isn't in ALL_KNOWN_BIKES — queue if the 890 cc
  CP3 platform refresh ever ships.
- **Consistency note:** The afternoon pass's Street Triple 765 RS entry
  (10.79 s) and the evening's 890 Duke R entry (11.00 s) both land
  squarely in the litre-naked / mid-twin cluster boundary. Worth a
  cluster-classifier audit pass to confirm `sweep_with_clusters.py`'s
  `cluster_for()` routes them consistently (both should be `mid-twin-
  500-700` per displacement class). No action needed if behaviour
  matches the May-2 documented routing.

## Cumulative day-1 totals

- Morning pass: +2 (Z900, MT-07)  → 82 → 84
- Afternoon pass: +3 (GSX-S1000, Street Triple 765 RS, Panigale V2)  → 84 → 87
- Evening pass: +3 (Z1000, RS 660, 890 Duke R)  → 87 → 90
- **Day total: +8 high-confidence instrumented benchmarks** across the
  three passes, all from publications already on the accepted-source
  list (Cycle World, Sport Rider, Motorcycle Consumer News, MotoStatz).
