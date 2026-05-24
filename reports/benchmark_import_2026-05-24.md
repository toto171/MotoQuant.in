# Benchmark Import — 2026-05-24

Two high-confidence instrumented quarter-mile benchmarks added to
`scripts/validation_sweep.py::BENCHMARKS` (also consumed by
`scripts/sweep_with_clusters.py`, which imports the same list).
BENCHMARKS count: **82 → 84**. No existing entries touched; no reference
baselines (K5/R1/Hayabusa) altered.

## Additions

### 1. Kawasaki Z900 (2017+ 948cc I4 naked)
- Tuple: `("Kawasaki", "Z900", 2020, 10.95, 198, "Cycle World 2017 middleweight-naked comparison (timing-strip)")`
- **ET:** 10.95 s
- **Trap:** ~198 km/h (estimated; CW snippet did not surface the exact
  number, but zeroto60times cluster reports the same press-kit run at
  "low 11s at ~125 mph" so 198 km/h ≈ 123 mph is the conservative
  central estimate — flagged for trap-confirmation pass)
- **Source:** Cycle World 2017 middleweight-naked comparison
  (Z900 vs Triumph Street Triple R vs Yamaha FZ-09), timing-strip data
- **URL:** https://www.cycleworld.com/kawasaki-z900-vs-triumph-street-triple-r-vs-yamaha-fz-09-comparison-motorcycle-review/
- **Catalog match:** `KAWASAKI_Z900_2020` (948 cc, I4, naked, 2020-2024
  model run — same engine architecture as the 2017 CW test bike,
  no changes 2017→2024)
- **Why it meets the bar:** Cycle World is on the project's accepted-
  source list and the article is an explicit timing-strip comparison
  test (not a 0-100 multiplier). Confirmed via two independent
  WebSearches surfacing the same 10.95 s figure.

### 2. Yamaha MT-07 / FZ-07 (689cc CP2 parallel-twin naked)
- Tuple: `("Yamaha", "MT-07", 2018, 12.13, 173, "Motorcycle Consumer News (stock instrumented, FZ-07/MT-07 CP2)")`
- **ET:** 12.13 s
- **Trap:** 173 km/h (107.70 mph rounded to whole km/h, matching the
  existing list's precision convention for cluster-style entries)
- **Source:** Motorcycle Consumer News — stock instrumented test of the
  FZ-07 (US name for the pre-2017 MT-07; same 689 cc CP2 engine)
- **URL:** Search surface — accelerationtimes.com aggregates the MCN
  figure; original MCN print issue not directly linkable
- **Catalog match:** `YAMAHA_MT07_2018` (689 cc CP2, 2018-2024 — same
  engine the MCN test exercised)
- **Why it meets the bar:** MCN is already cited in the existing
  BENCHMARKS list (e.g. the Ducati 1199 Panigale entry at
  `scripts/validation_sweep.py:86`) — same credentialed publication,
  same instrumented-test methodology. Stock bike confirmed (separately
  from the MotoStatz 11.97 s outlier figure, which is for a
  decat-exhaust + ECU-flash bike and was deliberately rejected).

## Rejected during research (audit trail)

- **Yamaha YZF-R7 instrumented stock ET** — existing entry already in
  list as DERIVED (line 192); searched for replacement, only MotoStatz
  (DERIVED) and accelerationtimes (calc-from-0-100) surfaced. No
  upgrade made.
- **Aprilia Tuono V4 1100 Factory 10.2 s** — appears consistently across
  MotorBikeCatalog 2018-2021 "Full performance review" pages, but those
  reviews are explicitly calculated from 0-100 × 1.6 multiplier (not
  instrumented). Rejected per CLAUDE.md instrumented-only bar.
- **MT-07 11.97 s @ 115.8 mph (MotoStatz)** — described in the source as
  achieved with a decat exhaust + ECU flash + lightweight rider. Not a
  stock measurement; rejected.
- **Yamaha FZ-09 2017 (10.66 s @ 125.24 mph, Cycle World)** — best
  data point of the day, but catalog has only the 2021 890 cc CP3
  `YAMAHA_MT09_2021` entry. The 2017 test bike is the older 847 cc CP3
  (different gen). Adding a year_hint=2017 row would either fall
  through to the entries[0] fallback and silently match the wrong
  generation, or miss-match the cluster. Skipped pending a future
  catalog entry for the 2014-2020 847 cc gen.
- **Triumph Street Triple R 2017 (11.15 s @ 122.28 mph, Cycle World)** —
  same comparison-test article. No Street Triple in the catalog
  (`grep`ed `known_bikes.py` + `known_bikes_extended.py`, no hit).
  Per the briefing's "do not add a benchmark for a bike not already in
  the catalog" rule.
- **Honda Africa Twin CRF1100L** — searched for MCN/CW timing-strip
  data. Only handling-route reviews returned; no instrumented quarter-
  mile data published. Skipped.
- **BMW S 1000 R (naked) 10.41 s @ 144 mph** — surfaced via search but
  no concrete publication+year attribution in the snippet. Rejected
  pending tighter sourcing.
- **Suzuki GSX-S750 11.24 s @ 124 mph** — likely from a Cycle World
  comparison vs FZ-09 but the source attribution chain (probably
  MotoStatz) was ambiguous in the search snippet. Rejected to keep the
  "2 high-confidence > 3 maybes" bar.

## Sweep impact (predicted)

These additions land in the mid-cluster bands the May-3 sweep flagged
as under-validated:

- Z900 → **litre-sport-600-1000 cluster** (already N≈29) — adds a naked
  data point to a cluster currently dominated by faired sport (R1,
  ZX-10R, S1000RR, Panigale V4). May surface a category-flavoured
  physics gap if the Z900 sim ET deviates from the 10.95 s target by
  more than the cluster's current 0.225 s mean|Δ|.
- MT-07 → **mid-twin-500-700 cluster** (currently N≈14, mean|Δ|=0.615
  per the May-2 sweep). Adding a well-validated naked twin will pull
  the cluster's signal-to-noise up — the current cluster is dominated
  by SV650/Ninja 650/Z650/Trident 660 with mixed source confidence.

Both additions can be expected to round-trip cleanly via the
`sweep_with_clusters.py` matcher because year_hint falls inside the
catalog spec's year range (2020 ∈ 2020-2024 for Z900; 2018 ∈
2018-2024 for MT-07). No fallback path used.

## Files touched
- `scripts/validation_sweep.py` — 2 entries appended at end of
  `BENCHMARKS` list, preserving the file's commentary style and the
  prior session's section dividers
- `reports/benchmark_import_2026-05-24.md` — this report

## Escalations / carry-forward
- The FZ-09 2017 Cycle World data (10.66 s @ 125.24 mph) and Street
  Triple R 2017 (11.15 s @ 122.28 mph) are both INSTRUMENTED and
  high-quality but unusable today. Either queue a catalog-expansion
  pass for the 2014-2020 847 cc MT-09/FZ-09 + the 765 cc Triumph
  Street Triple R, or flag them so the next catalog-expansion agent
  picks them up automatically.
- Z900 trap speed (198 km/h) is a defensible central estimate from
  adjacent press-kit data, but a future audit pass that surfaces the
  exact Cycle World 2017 article body should overwrite it with the
  published number.
