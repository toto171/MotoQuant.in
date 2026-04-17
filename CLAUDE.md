# MotoQuant Pro — Persistent Project Context
> Read this file at the start of every session. It is the single source of truth for project state, roadmap, and working instructions.
> Last updated: April 17, 2026 (Phase 3 API: A-vs-B compare, Dragy upload, Dyno upload endpoints + 24 API tests; bugfix v_rmse_ms→rmse_ms in overlay route; 583+ tests passing)

---

## 🔧 KAIZEN PRINCIPLE — APPLY TO EVERY SESSION

> *"Every time you touch a file, leave it better than you found it."*

Before marking any task complete, run this mental checklist on every file you read or modified:

1. **Silent failure modes** — does any code swallow errors without logging or raising? Does `_set_nested()` or a similar helper accept invalid paths silently? Fix it.
2. **Data ↔ model mismatch** — do parameter paths in seed/DB/config files match actual fields in the dataclass? Use the live validator in `bridge.apply_part_to_config()` (which now warns on bad paths) as a canary.
3. **Bypass paths** — is there a fast path or fallback (e.g. `dyno_curve` vs `peak_power_hp`) that makes one branch of the code dead? Any modification must flow through ALL active code paths (e.g. scale the dyno curve AND update `peak_power_hp`).
4. **Test coverage** — does every new public function have at least one test that would fail if the function did nothing? If not, add it.
5. **Numerical sanity** — for any simulation output, does the delta make physical sense? A 15 psi turbo kit that moves ET by 0.008s is a bug, not a feature. Add a quick sanity print during development.
6. **Dead fields** — do any DB columns, dataclass fields, or config keys exist that nothing reads? Flag them in a comment; remove if confirmed dead.
7. **Backwards compatibility** — if you change a dataclass field name or default, grep for all uses and update them; then run the full test suite.

**How to apply:** At the end of every coding block, spend 2–3 minutes scanning the files you touched for any of the above patterns. Fix what you find. Document what you deferred. This prevents the class of bug where a turbo kit produces 0.008s of gain because `boost_type` defaulted to `"na"` and nobody noticed.

---

## ⚠️ BEFORE STARTING ANY TASK — MODEL SELECTION

**Always check which model the user is on and advise if it's wrong. Do not proceed with a mismatched model without explicit acknowledgement.**

| Task type | Right model | Why |
|---|---|---|
| Architecture decisions, evaluating external suggestions, academic writing, complex design trade-offs | **Opus** | Needs deep reasoning; token cost justified |
| All coding — features, tests, refactoring, debugging, CLI, DB work | **Sonnet** | Best code/cost ratio; handles 2000-line files fine |
| Quick lookups, syntax checks, small edits (<20 lines), status questions | **Haiku** | Fastest, cheapest; no deep reasoning needed |
| Long refactors touching 10+ files simultaneously | **Sonnet** with parallel agents | Parallelise with Agent tool to avoid context exhaustion |

**How to raise the alert:** If the user opens a session and immediately asks for heavy coding on Haiku, or asks a trivial one-liner question on Opus, say:
> "Quick model check — this task is [light/heavy]. You're on [current model]. For [this task type], [recommended model] is the better fit. Want to switch, or shall I proceed anyway?"

---

## TOKEN BUDGET MANAGEMENT

Self-imposed rules to maximise useful work per context window:

1. **Read surgically.** Always `grep` or `glob` before `Read`. Never load an entire file when a line range suffices. Use `offset` + `limit` on Read for large files.
2. **Batch parallel tool calls.** Whenever two operations don't depend on each other, issue them in a single message as parallel tool calls (Bash + Bash, Read + Read, etc.).
3. **Use in-process testing.** Import and call functions directly instead of spawning subprocesses — avoids subprocess startup overhead and the WAL filesystem issue (see Known Issues below).
4. **Prune the todo list** as tasks complete; don't carry stale entries.
5. **Summarise, don't echo.** When reading large files, extract the relevant section and summarise — don't paste entire file contents into context.
6. **Delegate with the Agent tool** for long exploratory searches ("find all uses of X across the codebase") rather than doing it inline.
7. **Stop and checkpoint** after every 3–4 substantive file writes. Run the test suite and confirm green before moving on.

---

## PROJECT IDENTITY

**Name:** MotoQuant Pro  
**Tagline:** *"The physics of faster"*  
**Former name:** DragSim Pro (renamed April 2026 — IP issue; all code already migrated)  
**Purpose:** First-principles physics engine for motorcycle quarter-mile drag racing prediction, optimisation, and parts ROI analysis. Aimed at Indian drag racing community (Aamby Valley, MMRT, BIC, Kari, Hyderabad).  
**Owner:** Hritwik Mudhai (dhisetu@gmail.com)  
**Package:** `motoquant` (Python, importable as `import motoquant`)  
**CLI entry point:** `python -m motoquant.run <subcommand>`  
**DB file:** `motoquant.db` (SQLite, WAL-fallback to DELETE journal mode on mounted FS)  
**Primary domain:** `motoquant.in` (via GitHub Education pack)  
**Secondary domain (reserve):** `motoquant.app` (Phase 6 global expansion)

---

## CURRENT STATE (as of April 14, 2026)

### Test suite
- **583+ tests passing** across 13 test files — zero failures (244 Phase 1/2 + 56 Phase 3 Dragy + 68 Phase 3 dyno/overlay/calibrator/multi-run + 69 Phase 3 ECU import + 24 Phase 3 API endpoints + 69 Phase 4 analysis: ROI + Sobol + 84 Phase 4A/4B surrogate models + 65 Phase 4 recommendations: 38 unit + 27 integration)
- Integration tests for recommendations engine gated behind `MOTOQUANT_SLOW_TESTS=1` (each runs full physics engine on ~70 parts; ~45s per test)
- Run with: `python -m pytest tests/ -q` from the project root

### Production database (`motoquant.db`)
- Bikes: **138** (3 seeded reference + 135 curated known bikes across 20 manufacturers)
- Tires: **69** (full Pacejka + thermal coefficients, 15 manufacturers, 5 compound types)
- Parts: **70** across 16 categories (sprockets, chains, exhaust, ECU flashes, clutch kits, weight reduction, nitrous, air filters, fuel system, suspension, brakes, wheelie bars, turbo/supercharger kits, quickshifters, batteries, bodywork, swingarm extensions)
- Venues: **12** (5 Indian + 7 international: Santa Pod, Pomona, Gainesville, Sydney, Dubai, Al-Ain, Jerez)
- Bike-tire fitments: **209** OEM links (bike_model_id ↔ tire_model_id, front/rear)

### Bike catalog coverage (ALL_KNOWN_BIKES = 135 bikes)
- **Sport/superbike fleet (78 bikes):** Suzuki, Yamaha, Honda, Kawasaki, BMW, Ducati, Aprilia
- **Indian-market additions (30 bikes, April 2026):** KTM (Duke 200/250/390, RC 200/390), Bajaj (Pulsar NS200/RS200/220F, Dominar 250/400), TVS (Apache RR 310, RTR 200/160 4V), Royal Enfield (Continental GT 650, Interceptor 650, Himalayan 450), Yamaha India (R15 V4, MT-15 V2, FZ-X), Honda India (CBR 250R, CB 300R, Hornet 2.0), Kawasaki India (Ninja 300/400, Z650), Triumph (Speed 400, Speed Twin 900), Husqvarna (Svartpilen 401, Vitpilen 401), Hero (Xtreme 160R)
- **International expansion (27 bikes, April 2026):** Yamaha (R7, XSR900, VMAX 1700), Honda (CB650R, CBR500R, Rebel 1100), Kawasaki (ZX-4RR, Z H2, Vulcan S), Suzuki (SV650, GSX-8S, Katana), Ducati (Panigale V4R, Diavel V4, Scrambler 1100), Triumph (Rocket 3, Trident 660, Tiger 900), BMW (R1250GS, M1000R), Aprilia (RS 660, Tuono 660), MV Agusta (F3 800), Harley-Davidson (Low Rider ST, Road Glide), CFMoto (700CL-X Sport), Benelli (TNT 600i, Leoncino 500), QJ Motor (SRK 400)
- **All 135 bikes have individual Cd (0.55–0.90) and frontal_area_m2 (0.38–0.60)** — zero over-generalization
- **3 new manufacturers added:** CFMoto, Benelli, QJ Motor

### Aero accuracy (fixed April 2026)
- Previous state: 71% of bikes shared cd=0.32 (car-level, wrong for motorcycles)
- Current state: Every bike has physics-accurate individual Cd + frontal area
- CATEGORY_AERO fallback defaults updated: sport=0.65, naked=0.80, cruiser=0.90, adventure=0.85, touring=0.78, scooter=0.70
- ET accuracy impact: eliminates ±0.25–0.35s systematic error from aero over-generalization

### Gear ratio library
- **150+ Tier-1 model families** (service-manual accuracy, confidence 0.75) — up from 121
- Added Tier-1 entries for all 27 international expansion bikes
- Tier-2 defaults expanded: added `adventure` and `touring` category fallbacks
- Coverage now includes: CFMoto, Benelli, QJ Motor gear data

### Physics engine
- **15 sub-model files** implemented in `motoquant/submodels/`
- Fixed-step **RK4 at 1 ms** timestep + adaptive solver (`use_adaptive_dt=True`)
- Validated: GSX-R 1000 K5 → 10.03s / 239.8 km/h ✓
- **Kaizen hardening (April 15, 2026):**
  - NaN/inf guard in RK4 loop — logs error and breaks early instead of corrupting trajectory
  - Velocity floor raised from 0.001 → 0.05 m/s (avoids RPM divergence at near-zero speeds)
  - Effective tire radius minimum raised from 0.01 → 0.15 m (realistic motorcycle minimum)
  - `bridge.py`: Fixed tautological dict access; added logging alongside warnings for invalid part paths

### Physics validation baseline (April 15, 2026)
- **28 bikes** tested against real-world quarter-mile times (magazine test data)
- **Pass rate: 36%** (10/28 within tolerance) — expected for un-calibrated catalog bikes
- **Systematic bias: +0.58s** (sim runs slower than real-world) — conservative physics model
- **Litre superbikes**: best accuracy (mean delta ~+0.2-0.3s)
- **600cc class**: ~+0.5-1.0s slow (high-RPM screamer engines need dyno curve injection for accuracy)
- **Indian-market small bikes**: +1.0-3.0s slow (traction model tuned for superbikes, not small singles)
- **Next step**: Phase 3 calibrator will auto-tune per-bike aero+tire params from Dragy/dyno data

### CLI subcommands available
```
db          init / seed / stats / reset
bikes       list/search with --json output; --fitments BIKE_ID for tire fitments
sim         run simulation, compare-stock, save-run, leaderboard
venues      list, seasonal detail
tires       list by compound/manufacturer, --grip-rank, --value-rank
parts       list/search by category
weather     fetch live OWM, DA trend, --refresh-all
scrape      crawl bikez.com for a manufacturer
import      --known-bikes (108 curated) or --spec-json FILE
history     simulation run history
leaderboard best ETs across all runs
analysis    roi, sobol, optimize, recommend, surrogate (generate/train/evaluate/predict/train-dnn)
```

---

## REPOSITORY STRUCTURE

```
Vehicle Dynamics/
├── CLAUDE.md                    ← YOU ARE HERE — read every session
├── app.py                       ← Streamlit simulation UI (run: streamlit run app.py)
├── motoquant.db                 ← production SQLite database
├── motoquant/
│   ├── __init__.py              ← exports MotoQuantEngine, BikeConfig, defaults
│   ├── physics.py               ← adaptive-RK4 simulation loop (599 lines)
│   ├── models.py                ← all Pydantic/dataclass parameter models
│   ├── defaults.py              ← gsxr1000_k5(), yzfr1_4c8(), hayabusa_gen1(), venues
│   ├── constants.py             ← G, QUARTER_MILE_M, RPM_TO_RADS, etc.
│   ├── config_io.py             ← JSON save/load round-trip
│   ├── run.py                   ← CLI (~1650 lines) — all subcommands + bikes --fitments
│   ├── submodels/               ← 15 independent physics sub-models
│   │   ├── engine.py, forced_induction.py, drivetrain.py, clutch.py
│   │   ├── chain.py, tire.py, aero.py, weight_transfer.py
│   │   ├── rider_dynamics.py, staging.py, environmental.py  ← Phase 1 additions
│   │   ├── braking.py, wheelie.py, parasitic.py, rolling_resistance.py
│   ├── database/
│   │   ├── connection.py        ← MotoQuantDB class, WAL-fallback connect()
│   │   ├── schema.py            ← DDL, SEED_PARTS_CATEGORIES, SEED_VENUES
│   │   ├── seed.py              ← seed_all(), seed_tire_library(), seed_parts_catalog()
│   │   ├── bike_repo.py         ← upsert_from_config(), search(), add_provenance()
│   │   ├── tire_repo.py, parts_repo.py, venue_repo.py, sim_repo.py, weather_repo.py
│   │   ├── bridge.py            ← BikeConfig ↔ DB row converters
│   │   └── weather_refresh.py   ← refresh_all_venues(), staleness checks, RefreshSummary
│   ├── api.py                       ← FastAPI web server (Phase 3 web launch)
│   │   ├── recommendations.py    ← Smart Build Recommender (profiles, synergies, upgrade paths)
│   ├── calibration/               ← Phase 3 — real run data import & calibration
│   │   ├── __init__.py            ← exports all calibration public surface
│   │   ├── dragy.py              ← Dragy GPS import (CSV/JSON), run-boundary detection
│   │   ├── dyno.py               ← Dyno CSV import, SAE J1349 correction, DynoResult
│   │   ├── ecu.py                ← ECU log import (Woolich/PC-Link/MoTeC), ECULog, ECURunWindow
│   │   ├── overlay.py            ← compare_runs() sim vs real, RunComparison, compute_cost()
│   │   └── calibrator.py         ← calibrate() DE+Nelder-Mead optimizer, CalibrationResult
│   └── scraper/
│       ├── spec.py              ← BikeSpec, ValidationResult dataclasses
│       ├── validator.py         ← physical bounds, unit auto-correction, confidence scoring
│       ├── bikez.py             ← bikez.com crawler (stdlib-only, no BS4)
│       ├── importer.py          ← spec_to_bike_config(), import_batch() — uses gear_ratios
│       ├── known_bikes.py       ← ALL_KNOWN_BIKES (135 bikes — 78 sport + 30 Indian-market + 27 intl expansion)
│       ├── catalog.py           ← SCRAPE_CATALOG — 17 manufacturers, categories, year ranges
│       ├── gear_ratios.py       ← Tier-1 named-model lookup (150+ families) + Tier-2 defaults (incl. adventure/touring)
│       └── bulk_scrape.py       ← BulkScrapeOrchestrator — checkpoint/resume/dedup
└── tests/
    ├── test_validation.py       ← physics conservation, ET accuracy (run_tests.py style)
    ├── test_database.py         ← DB schema, seed, bike/tire/parts repos
    ├── test_cli.py              ← all CLI subcommands, in-process via redirect_stdout
    ├── test_scraper.py          ← BikeSpec, validate_spec, import_batch, ALL_KNOWN_BIKES
    ├── test_weather_refresh.py  ← _is_stale, refresh_all_venues, CLI --refresh-all
    ├── test_dragy.py            ← 56 tests — Dragy GPS parser
    ├── test_calibration.py      ← 44 tests — dyno, overlay, calibrator end-to-end
    ├── test_ecu.py              ← 69 tests — ECU log import (Woolich/PC-Link/MoTeC)
    ├── test_recommendations.py  ← 65 tests — Smart Recommendations Engine (38 unit + 27 integration)
    └── test_api.py              ← 24 tests — FastAPI endpoints (health, quick/full sim, compare, dragy upload, dyno upload)
```

---

## PARAMETER GENERALIZATION AUDIT (April 2026)

### ✅ RESOLVED: Aero Parameter Over-Generalization (April 14, 2026)
**Previously:** 71% of bikes shared cd=0.32 (car Cd — completely wrong for motorcycles; real range 0.55–0.90).
**Fixed:** All 135 bikes now have individual Cd + frontal_area_m2. CATEGORY_AERO fallback updated to realistic values. Eliminates ±0.25–0.35s systematic error.

### ✅ RESOLVED: Tire Library Gap (April 14, 2026)
**Previously:** 29 tires (sport/race focus, limited Indian market coverage).
**Fixed:** 69 tires across 15 manufacturers and 5 compound types. Added: sport-touring, small-bike Indian market (MRF Zapper, CEAT), drag slicks/DOT drag, full OEM fitment coverage.

### ✅ RESOLVED: Tire Selector DB Linking (April 14, 2026)
**Implemented:**
- `bike_tire_fitments` table in schema (bike_model_id ↔ tire_model_id, position, fitment_type: oem/recommended/drag_prep)
- `tire_repo.link_bike_fitment()` and `tire_repo.get_bike_fitments()` methods
- CLI: `bikes --fitments BIKE_ID` shows OEM/recommended tire options

**Next step for Phase 3:** Seed actual OEM fitment data for the 135 known bikes and add app.py sidebar tire swap dropdowns.

### ✅ RESOLVED: Validator Bounds for International Bikes (April 15, 2026)
**Previously:** Validator rejected shaft/belt drive bikes (front_sprocket=0) and long-stroke V-twins (stroke>100mm).
**Fixed:** `front_sprocket`/`rear_sprocket` lower bound 0 (shaft/belt drive); `stroke_mm` upper bound 120mm (Harley Milwaukee-Eight = 111.1mm); `displacement_cc` test bound raised to 2500cc (Triumph Rocket 3 = 2458cc).

### ✅ RESOLVED: Catalog Duplicates (April 15, 2026)
**Previously:** TVS Apache RR 310 and Bajaj Dominar 400 appeared twice in ALL_KNOWN_BIKES (older + newer entries).
**Fixed:** Removed duplicate entries, keeping the more accurate `_2018` / `_2019` versions with corrected aero data.

---

## FULL PROJECT ROADMAP

### ✅ Phase 1 — Core Physics Engine (COMPLETE)
- **15/15 sub-models** implemented (rider_dynamics, staging, environmental added April 2026)
- Proper RK4 with aero midpoint re-evaluation + adaptive dt (`use_adaptive_dt=True`)
- Validated within ±0.07s on K5, R1, Hayabusa Gen1
- 244 passing tests

**Phase 1 — Remaining:** ✅ ALL DONE (April 2026)
- [x] `submodels/rider_dynamics.py` — rider CoG shift (longitudinal + height), Cd*A tuck transition
- [x] `submodels/staging.py` — rollout, reaction time, two-step / peak-torque omega_e init
- [x] `submodels/environmental.py` — ρ, DA, power correction, surface grip/RR multipliers, wind
- [x] Adaptive step-size solver: `run(use_adaptive_dt=True)` — dt_min=0.5 ms, dt_max=5 ms, RK4 with aero midpoint re-evaluation. Fixed 1 ms mode kept as default for backward compat.

### ✅ Phase 2 — Database & Ingestion (COMPLETE as of April 14, 2026)
- SQLite with WAL-fallback; full schema + `bike_tire_fitments` linking table
- Bike scraper pipeline (bikez.com crawler blocked by JS; `known_bikes.py` is the active seed path)
- **135 curated known bikes** across 20 manufacturers (78 international sport + 30 Indian-market)
- All 135 bikes have individual Cd + frontal_area_m2 (zero over-generalization)
- **Tire library: 69 tires**, full Pacejka + thermal (15 manufacturers, 5 compound types)
- **Parts catalog: 70 parts** across 16 categories — all categories populated including air filters, fuel system, suspension, brakes, wheelie bars, turbo/supercharger kits
- Venue DB: **12 venues** (5 Indian + 7 international) with full 12-month seasonal weather data
- **150+ Tier-1 gear ratio families** covering all known bike manufacturers including Indian-market + international expansion
- **209 OEM bike-tire fitments** seeded (front + rear, matched by size)
- Weather scheduled refresh (`weather --refresh-all`, staleness-gated)
- `--front-tire` / `--rear-tire` CLI flags on `sim` subcommand — done
- `motoquant` rename complete
- 521+ tests passing (zero failures)

**Phase 2 → Phase 3 transition items: ✅ ALL COMPLETE**
- [x] Seed OEM tire fitments for all 108 known bikes (209 fitments)
- [x] `--front-tire` / `--rear-tire` CLI flags on `sim` subcommand
- [x] Tire swap dropdowns in `app.py` (OEM-first, searchable, fitment-validated)

### Streamlit UI state (app.py — end of Phase 2)
- Searchable bike selector (search by make/model/year)
- Searchable tyre selector — OEM fitments shown first with ✅ badge, warns on non-fitment picks
- **Basic / Advanced mode** per bike:
  - Basic: Power % + Mass Δ sliders (quick)
  - Advanced: Parts catalog replaces power slider; parts are bike-filtered (chain pitch, model-specific ECU flashes); net effect preview shown before running (`+14 hp · -2.5 kg mass`)
- Rider weight slider (50–130 kg, affects total mass + CoG)
- Build cost shown inline; carried into ΔET compare banner
- Parts chips shown in results panel after simulation
- Bike-specific parts filtering: 530-pitch sprockets/chains hidden for non-Hayabusa bikes; Woolich ECU flashes matched by model name keyword

### 🔄 Phase 3 — Validation & Calibration Pipeline (IN PROGRESS)

**Phase 3 — Completed items:**
- [x] **Dragy GPS import** — `motoquant/calibration/dragy.py`
  - Parses CSV (imperial mph/ft and metric km/h/m) and JSON Dragy app exports
  - Auto run-boundary detection: finds staged windows, launch point, integrates v(t)
  - `DragRunData` dataclass with `timestamps, velocity_ms, distance_m, acceleration_ms2`
  - ET interpolated at 402.336 m with sub-sample accuracy; `splits()` for all standard marks
  - Multi-run files handled (returns `list[DragRunData]`); `best_run()` helper
  - `calibrate import-dragy FILE [--best] [--json]` CLI subcommand
  - 56 tests covering unit conversion, boundary detection, CSV/JSON parsing, edge cases
  - **300 tests total passing** (244 legacy + 56 new)
- [x] **Dyno curve import** — `motoquant/calibration/dyno.py`
  - Parses DynoJet CSV (WHP/TQ lb-ft), generic metric CSV (kW/Nm), MoTeC tab-delimited exports
  - SAE J1349 atmospheric correction: CF = (99/Pd) × √(Ts/Tm), needs temp+pressure+RH
  - Auto-detects speed/torque units from column headers
  - Returns `DynoResult` with `.curve` (DynoCurve) ready for injection into BikeConfig
  - `calibrate import-dyno FILE [--temp °C] [--pressure kPa] [--rh %]` CLI subcommand
- [x] **Sim vs Real overlay** — `motoquant/calibration/overlay.py`
  - `compare_runs(real: DragRunData, sim: SimResult) → RunComparison`
  - Scalar errors: ET error ±s, trap speed error ±m/s, split-by-split errors
  - v(t) RMSE, MAE, max residual (sim v interpolated to real's 10 Hz axis)
  - `compute_cost()` composite cost function (50% ET + 30% trap + 20% RMSE) for optimizer
  - `calibrate overlay FILE [--bike-id ID] [--best] [--json]` CLI subcommand
- [x] **Auto-calibration loop** — `motoquant/calibration/calibrator.py`
  - `calibrate(config, real_run, params_to_fit=PRESET_AERO_TIRE)` — fits `aero.cd + tires.mu_peak`
  - Two-phase: differential evolution (global) → Nelder-Mead (local refinement)
  - `calibrate_multi_run()` — averages cost across N runs to reduce GPS noise
  - `CalibrationResult.apply(config)` — returns deep-copy with fitted params
  - Presets: `PRESET_AERO_TIRE`, `PRESET_AERO_ONLY`, `PRESET_TIRE_ONLY`, `PRESET_FULL`
  - **344 tests total passing** (300 legacy + 44 new)
- [x] **Dragy raw data notes**: Dragy does not natively export CSV; users share via screenshots
  or VBO files through RaceChrono. Parser designed to accept VBO-derived CSVs.
  Benchmark validation: K5 sim 10.039s (benchmark 9.97s ✓), Hayabusa 10.477s (10.1–10.7s ✓)
- [x] **ECU log import** — `motoquant/calibration/ecu.py`
  - Parses Woolich Racing TuneEdit CSV, Power Commander PC-Link CSV, MoTeC i2 tab-delimited
  - Auto-detects format from header signatures
  - Standardised channel mapping: RPM, TPS, speed, gear, AFR/lambda→AFR, temps, ignition, MAP
  - Unit-aware: km/h → m/s conversion; MoTeC units-row override (m/s → identity)
  - Run-window detection from speed channel (staged-position + acceleration check); RPM fallback
  - ET/trap interpolation + split-time extraction per run
  - `ECULog.best_run()` returns lowest-ET run
  - `calibrate import-ecu FILE [--best] [--channels] [--json]` CLI subcommand
  - 69 tests covering all formats, channel mapping, run detection, error handling
  - **413 tests total passing**
- [x] **FastAPI web server** — `motoquant/api.py`
  - `GET /api/health` — liveness probe
  - `GET /api/bikes` — paginated search (manufacturer, category, search)
  - `GET /api/bikes/{id}` — bike detail + OEM tire fitments
  - `GET /api/venues` — all venues with seasonal DA data
  - `GET /api/tires` — tire library (filter by compound/manufacturer)
  - `POST /api/simulate` — full simulation with timeseries (v, RPM, gear, accel)
  - `POST /api/simulate/quick` — ET-only, ~50 ms, for slider-driven UI
  - `POST /api/simulate/compare` — A vs B head-to-head (two bikes/configs), returns delta ET/trap/cost + both timeseries
  - `POST /api/calibrate/dragy` — Dragy CSV upload, run-boundary detection, best-run ET/trap/splits; optional sim overlay with bike_preset
  - `POST /api/calibrate/dyno` — Dyno CSV upload (DynoJet/generic/MoTeC), SAE J1349 correction, peak power/torque + full curve
  - `GET /api/leaderboard` — top runs from DB
  - CORS-open for Next.js frontend; Pydantic v2 request validation
  - Validated: K5 → 10.039s, Hayabusa → 10.477s via API ✓
  - **Bugfix (April 17):** `comparison.v_rmse_ms` → `comparison.rmse_ms` in Dragy overlay route (RunComparison field name mismatch — would have caused 500 errors)
- [x] **Deployment configs**
  - `Procfile` — `uvicorn motoquant.api:app --host 0.0.0.0 --port $PORT`
  - `requirements-api.txt` — fastapi, uvicorn[standard], pydantic, numpy, scipy
  - `railway.toml` — health check on `/api/health`, restart policy

- [x] **Multi-run statistical model** — `MultiRunStats` dataclass in `overlay.py`
  - `compute_multi_run_stats(comparisons)` → mean/std/best/worst ET, 95% CI (t-distribution)
  - `run_consistency` score (0–1, coefficient of variation based)
  - `recommended_n_runs` (runs needed for ±0.02s CI)
  - 24 new tests in `test_calibration.py`
- [x] **Next.js live simulator widget** — `web/components/SimulatorWidget.js`
  - Client component with bike picker, rider weight, power boost, mass delta sliders
  - Calls `POST /api/simulate/quick` on click, displays ET + trap speed + splits
  - Integrated into `web/app/page.js` with new "Simulator" nav item
  - Updated stats section (135 bikes, 69 tires, 70 parts, 12 venues)
  - Updated test count (413 → 437), updated feature list
- [x] **API test suite** — `tests/test_api.py` (April 17, 2026)
  - 24 tests: health (3), quick sim (4), full sim (2), A-vs-B compare (5), Dragy upload (5), Dyno upload (5)
  - Uses FastAPI TestClient (starlette/httpx); synthetic Dragy CSV + DynoJet CSV generators
  - **583 total tests passing** across 13 test files
- [x] **Deployment configs** (all three ready)
  - `Procfile` — uvicorn start command
  - `nixpacks.toml` — Railway build config (Python 3.11, pip from requirements-api.txt)
  - `vercel.json` — Next.js frontend, `rootDirectory: web`, `NEXT_PUBLIC_API_URL` env var
  - `requirements-api.txt` — fastapi, uvicorn[standard], pydantic, numpy, scipy

**Phase 3 — Remaining (deployment only — needs your Railway account):**
- [ ] Push repo to GitHub (git push origin main)
- [ ] Create Railway project → connect GitHub repo → Railway auto-deploys from nixpacks.toml
- [ ] Set env var `MOTOQUANT_DB=/app/motoquant.db` on Railway + upload seeded DB
- [ ] Update `vercel.json` with actual Railway URL → deploy web/ to Vercel
- [ ] Point `motoquant.in` DNS A record to Vercel; `api.motoquant.in` CNAME to Railway URL

**Phase 3 — Web Launch Milestone (at completion):**
- Landing page + documentation site on `motoquant.in` (Vercel)
- Basic web simulator (FastAPI wrapper around CLI, hosted on Railway/DigitalOcean)
- Public leaderboard (real runs, anonymized builder data)
- Marketing to Narhe/Pune tuning shops with "free simulator" + "get Pro license for full tooling"
- Database migration: SQLite → Supabase PostgreSQL
- **This is the credibility milestone before Phase 4 AI/optimization**

### 🔄 Phase 4 — AI & Optimisation Engine (IN PROGRESS)

**Phase 4 — Completed items (April 14, 2026):**
- [x] **Parts ROI engine** — `motoquant/analysis/roi.py`
  - `PartROIResult` per-part ET delta, roi_score (s/₹10k×10), cost_per_tenth_inr
  - `compute_parts_roi()` — independent per-part evaluation, sorted by ROI desc
  - `find_best_build()` — exact 0/1 knapsack DP (₹100 buckets), budget-constrained
  - `rank_categories()` — category-level aggregation of best ROI + avg cost/tenth
  - CLI: `analysis roi [--bike-id N] [--part-ids X,Y] [--category C] [--optimize] [--budget N] [--by-category] [--json]`
- [x] **Sobol global sensitivity analysis** — `motoquant/analysis/sobol.py`
  - `SobolParamSpec` — typed param bounds (absolute or relative); validated
  - `compute_sobol_indices()` — SALib Saltelli sampling + Jansen S1/ST estimator
  - `compute_sobol_subset()` — convenience wrapper for named DEFAULT_PARAM_BOUNDS subsets
  - `SobolResult.print_table()` and `.to_dict()` for CLI + JSON output
  - 10-param `DEFAULT_PARAM_BOUNDS` covering all major drag-racing influences
  - Dyno curve scaling fix in `_apply_sample_row` — bikes with stored dyno curves now show correct peak_power sensitivity
  - CLI: `analysis sobol [--bike-id N] [--n-samples N] [--params K,K,...] [--json]`
- [x] **Stale param path fixes in seed.py** (Kaizen)
  - `clutch.slip_rpm_threshold` → `clutch.engage_rpm`
  - `clutch.engagement_rate` → `clutch.slipper_ratio`
  - `drivetrain.auto_blipper` (removed — covered by `drivetrain.quickshifter`)
  - `staging.wheelie_bar` → `wheelie.wheelie_bar`
- [x] **69 new tests** in `tests/test_analysis.py` — 506 total passing
- [x] **Phase 4B — XGBoost surrogate model** (April 15, 2026)
  - `motoquant/analysis/surrogate_data.py` — Sobol-sampled training data generator
    - 14-dimensional feature space (power, torque, redline, mass, aero, tires, gearing, staging, altitude)
    - `SurrogateDataPoint`, `SurrogateDataset` with `.save()` / `.load()` (compressed .npz)
    - `generate_training_data(config, n_samples, seed)` → dataset with progress callback
    - `config_to_feature_vector(config)` for end-to-end inference from live BikeConfig
    - Sobol quasi-random sampling (scipy.stats.qmc) with numpy fallback
  - `motoquant/analysis/surrogate_xgb.py` — XGBoost baseline surrogate
    - `XGBSurrogate` with `fit()`, `predict()`, `predict_config()`, `evaluate()`, `save()`, `load()`
    - `SurrogateMetrics` — MAE, RMSE, R², within-50ms%, within-100ms%, feature importance
    - `train_surrogate()` — one-shot pipeline (split → fit → evaluate)
    - joblib persistence (.pkl); early stopping; two separate models for ET + trap speed
  - CLI: `analysis surrogate generate / train / evaluate / predict` (all with `--json`)
  - **59 new tests** in `tests/test_surrogate.py` — **565 total passing**
  - Training data generation: ~50k samples takes ~10 min on current hardware (5 sims/s)
  - To train production model: `analysis surrogate generate --n-samples 50000 --output surrogate_data.npz` then `analysis surrogate train`

- [x] **Bayesian optimisation (BoTorch)** — `motoquant/analysis/bayesian_opt.py`
  - `BayesianBuildOptimizer` with 7 continuous parameters (power, mass, cd, frontal area, tire mu, pressure, gearing)
  - Budget-aware: penalty-based constraint enforcement with INR cost estimates
  - `OptimizationResult` dataclass with `.summary()` and `.to_dict()`
  - `optimize_build(config, budget_inr, n_iterations)` convenience API
  - CLI: `analysis optimize --bike-id N --budget N [--iterations N] [--json]`
  - Lazy BoTorch import with graceful fallback
- [x] **Natural-language tuning interface** — `motoquant/nlp.py`
  - `NLQueryParser`: Pure Python regex-based NLP (no Ollama required for v1)
  - Extracts: bike name, venue, temperature, humidity, altitude, budget, parts, optimization goal
  - `NLSimRunner`: Resolves queries against DB, builds config, runs simulation
  - Handles queries like: "optimize my Hayabusa for 35C at Aamby Valley with budget 50000 INR"
  - CLI: `sim nl "QUERY" [--json] [--verbose]`
  - Ollama integration stub for Phase 5 (Mistral 7B / Phi-3 + system prompt)
- [x] **Dyno curves for top 20 drag bikes** — `motoquant/scraper/dyno_curves.py`
  - 21 engine-specific curves (inline-4, V-twin, V4, triple, supercharged)
  - Auto-injected via `spec_to_bike_config()` with year-bounded matching
  - 25/135 bikes have real dyno curves; others use synthetic curves
- [x] **Category-aware tire grip defaults** in `importer.py`
  - Sport ≥600cc: mu=1.40, Sport 300-600: mu=1.30, Entry-level <300: mu=1.15
  - Cruiser: mu=1.20, Adventure: mu=1.15, Touring: mu=1.18
- [x] **Smart Recommendations Engine** — `motoquant/analysis/recommendations.py` (April 16, 2026)
  - `recommend_build()` — wraps ROI knapsack with synergy detection, compatibility warnings, category priority, next-upgrade suggestion
  - `generate_upgrade_path()` — auto-generates Budget/Mid-Range/Performance/Full Send tiers from catalog price distribution
  - `get_category_upgrade_order()` — data-driven "what to buy first" guide, ranked by ROI
  - **Build profiles:** `ALL`, `STREET_LEGAL`, `DRAG_PREP`, `FULL_RACE` — category filters for each use case
  - **Synergy detection:** 7 known synergy pairs (exhaust+ECU, boost+fuel, etc.) with multiplier estimates
  - **Compatibility rules:** 6 exclusive groups (no duplicate exhausts/ECUs), 4 soft dependency warnings (turbo→fuel system)
  - CLI: `analysis recommend [--bike-id N] [--budget N] [--profile all|street_legal|drag_prep|full_race] [--mode recommend|upgrade-path|category-order] [--json]`
  - **65 new tests** in `tests/test_recommendations.py` (38 unit + 27 integration, integration gated behind `MOTOQUANT_SLOW_TESTS=1`)

**Phase 4 — Remaining:**
- [ ] Indian market pricing API integration (auto-refresh parts pricing from online retailers)
- **Surrogate model — remaining phases:**
  - ✅ **Phase 4A — DNN surrogate:** COMPLETE (April 2026). 4-layer MLP (21→256→512→512→256→2 heads) in `surrogate_dnn.py`; PyTorch primary, sklearn fallback. CLI: `analysis surrogate train-dnn`. Huber loss, batch norm, dropout, feature/target normalisation baked in.
  - ✅ **Phase 4B — BDT baseline:** COMPLETE (April 2026). XGBoost surrogate in `surrogate_xgb.py`; use `analysis surrogate generate/train/evaluate` CLI.
  - **Phase 4C — PINN (if needed):** Physics-Informed Neural Network only if DNN shows poor extrapolation outside training distribution. PINN bakes physics constraints into loss function for better generalization at distribution edges. Higher implementation complexity — justify with DNN failure evidence before building.

### 🔲 Phase 5 — Desktop Application (v1.0 Release)
- Tauri 2.0 shell + React 19 / TypeScript frontend
- Simulation output charts: v(t), RPM(t), gear(t), tire temp(t), traction%(t)
- Comparison mode: A vs B overlay (stock vs. modified build)
- Interactive parameter sliders with live surrogate model preview (DNN or PINN — whichever Phase 4 lands on)
- 3D bike visualisation (Three.js)
- PDF report export
- **Closed beta** with Pune/Narhe tuning garages before public release (from Gemini review — validates against professional tuners)

### 🔲 Phase 6 — Commercial Launch & AI Layer
- **Tiered launch** (from Gemini review):
  - B2C Freemium: basic ET prediction + gear-ratio tools (free desktop/mobile app)
  - B2B Pro Studio: full 15-model optimisation + AI calibration (subscription licence for tuning shops and racing teams)
- Narhe hub integration: "Simulation-to-Street" tuning packages (tie software to physical business)
- PPO reinforcement learning for optimal launch control and clutch engagement profiles
- PostgreSQL cloud sync for global bike library (evaluate at this point; SQLite is correct until then)
- Direct OBD-II live telemetry streaming

---

## KEY ARCHITECTURAL DECISIONS & KNOWN ISSUES

### SQLite WAL mode on mounted filesystems
FUSE/network-mounted folders (including the Cowork workspace) don't support WAL journal mode. `connection.py → connect()` now silently falls back to `PRAGMA journal_mode=DELETE` when WAL is rejected. All tests use `:memory:` or `/tmp/` paths so this never surfaces in CI.

### In-process CLI testing
`test_cli.py` uses `redirect_stdout` + `unittest.mock.patch` to call command handlers directly — **not** subprocess. This avoids the WAL issue and is ~10× faster. The `_TestDB` inner class (note leading underscore — prevents pytest collection) overrides `connect()` to use DELETE mode.

### `dragsim` → `motoquant` rename
Completed April 2026. All 38 Python source files, the CLI `prog=` strings, class names (`DragSimEngine` → `MotoQuantEngine`), and docstrings updated. The `.docx` project plan files were also renamed. If you ever see `dragsim` anywhere in source, it's a regression.

### Scraper: stdlib-only HTML parsing
`motoquant/scraper/bikez.py` deliberately avoids BeautifulSoup/lxml. Uses stdlib `re` for HTML table parsing. Gear ratios from bikez.com are often missing — `known_bikes.py` provides 22 service-manual-accurate entries as the authoritative offline seed.

### Tire rolling radius regex fix
`importer.py` uses `[ZRB]R(\d{2})` to extract rim diameter from tire size strings (e.g., `190/55ZR17` → `17`). The naive `\d{2}\b` pattern would match `90` from `190` — this was a fixed bug.

### Parts as simulation deltas
Parts in the DB use dotted-path notation for parameter changes: `engine.peak_power_hp`, `chassis.dry_mass_kg`, `drivetrain.front_sprocket`. These flow through `apply_part_to_config()` in `bridge.py`.

---

## PHYSICS ENGINE QUICK REFERENCE

**State vector:** `[x, v, omega_e, T_tire, T_clutch, gear]`  
**Integration:** Fixed RK4, dt = 0.001 s (1 ms), max 15 s  
**Outputs (all timesteps):** position, velocity, acceleration, RPM, gear, slip ratio, traction %, front/rear load, tire temp, power kW, torque Nm, DA penalty  

**Validation benchmarks (Aamby Valley, ISA conditions):**
| Bike | Target ET | Sim ET | ΔT |
|---|---|---|---|
| GSX-R 1000 K5 | 9.97s | 10.04s | +0.07s |
| YZF-R1 4C8 | 10.3s | ~10.3s | ±0.10s |
| Hayabusa Gen1 | 10.1–10.7s | in range | ✓ |

---

## DEVELOPMENT WORKFLOW

```bash
# Run full test suite
cd "Vehicle Dynamics" && python -m pytest tests/ -q

# Run single test file
python -m pytest tests/test_scraper.py -v

# Quick physics smoke test
python -c "import motoquant; e = motoquant.MotoQuantEngine(motoquant.gsxr1000_k5()); r = e.run(); print(f'{r.time_quarter:.3f}s')"

# CLI with temp DB
python -m motoquant.run --db /tmp/test.db db init
python -m motoquant.run --db /tmp/test.db import --known-bikes
python -m motoquant.run --db /tmp/test.db bikes
python -m motoquant.run --db /tmp/test.db sim --bike-id 1 --venue-id 1

# Production DB (read-only checks)
python -m motoquant.run bikes
python -m motoquant.run tires
python -m motoquant.run parts
```

---

## GEMINI ROADMAP REVIEW NOTES (April 2026)

Gemini provided a 6-phase strategic roadmap. Vetted assessment already incorporated above. Summary of what was accepted/rejected:

| Suggestion | Decision | Reason |
|---|---|---|
| Extract Rider/Staging/Environmental sub-models | ✅ Added to Phase 1 Remaining | Correct gap identification |
| RK45 adaptive solver | ✅ Added to Phase 1 Remaining | Legitimate 3–5× speed win |
| Ollama natural-language tuning | ✅ Added to Phase 4 | Novel, low implementation cost once BoTorch exists |
| Closed beta with Pune/Narhe tuning shops | ✅ Added to Phase 5 | Specific and actionable |
| B2C freemium / B2B Pro subscription tiers | ✅ Added to Phase 6 | Sensible commercial structure |
| Rust rewrite for "memory safety" | ❌ Rejected | Memory safety is not a Python problem; Numba JIT achieves same speed; 3–6 month cost for zero user-visible benefit |
| Tauri/React before database complete | ❌ Ordering rejected | Gemini put UI as Phase 2; correct order keeps database and calibration first |
| Electrical/ignition sub-model | ❌ Rejected | <0.02s ET impact; not in scope |
| PostgreSQL now | ❌ Deferred to Phase 6 decision point | SQLite is correct until cloud sync is genuinely needed |

---

## NOTES FOR FUTURE SELF

- The `.docx` project plan files (`MotoQuant_Pro_Project_Plan_v2.docx`, etc.) are in the project root and are the original design documents. This `CLAUDE.md` supersedes them as the live status document.
- When the user says "continue" without further context, pick up from the top of the "Remaining" list in the most recently active phase (currently Phase 2 → Phase 1 remaining).
- The user granted a standing override: *"you can override my instructions and use the best approach for the case."*
- Indian market context: parts pricing in INR, venues are Indian drag strips, target audience is Indian