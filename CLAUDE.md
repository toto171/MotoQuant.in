# MotoQuant Pro — Persistent Project Context
> Read this file at the start of every session. It is the single source of truth for project state, roadmap, and working instructions.
> Last updated: April 2026

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

## CURRENT STATE (as of April 2026)

### Test suite
- **245 tests passing** across 6 test files — zero failures
- Run with: `python -m pytest tests/ -q` from the project root

### Production database (`motoquant.db`)
- Bikes: **81** (3 seeded reference + 78 curated known bikes across 15 manufacturers)
- Tires: **29** (full Pacejka + thermal coefficients, 9 manufacturers)
- Parts: **58** (sprocket matrix, chains, exhaust, ECU flashes, clutch kits, weight reduction, nitrous)
- Venues: **12** (5 Indian + 7 international: Santa Pod, Pomona, Gainesville, Sydney, Dubai, Al-Ain, Jerez)

### Physics engine
- **12 sub-model files** implemented in `motoquant/submodels/`
- Fixed-step **RK4 at 1 ms** timestep (adaptive RK45 is a planned upgrade — see Phase 1 Remaining)
- Validated: GSX-R 1000 K5 → 10.04s / 239.8 km/h ✓

### CLI subcommands available
```
db          init / seed / stats / reset
bikes       list/search with --json output
sim         run simulation, compare-stock, save-run, leaderboard
venues      list, seasonal detail
tires       list by compound/manufacturer
parts       list/search by category
weather     fetch live OWM, DA trend, --refresh-all
scrape      crawl bikez.com for a manufacturer
import      --known-bikes (53 curated) or --spec-json FILE
history     simulation run history
leaderboard best ETs across all runs
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
│   ├── run.py                   ← CLI (1536 lines) — all subcommands
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
│   └── scraper/
│       ├── spec.py              ← BikeSpec, ValidationResult dataclasses
│       ├── validator.py         ← physical bounds, unit auto-correction, confidence scoring
│       ├── bikez.py             ← bikez.com crawler (stdlib-only, no BS4)
│       ├── importer.py          ← spec_to_bike_config(), import_batch() — uses gear_ratios
│       ├── known_bikes.py       ← ALL_KNOWN_BIKES (53 curated, service-manual accuracy)
│       ├── catalog.py           ← SCRAPE_CATALOG — 17 manufacturers, categories, year ranges
│       ├── gear_ratios.py       ← Tier-1 named-model lookup (50+ families) + Tier-2 defaults
│       └── bulk_scrape.py       ← BulkScrapeOrchestrator — checkpoint/resume/dedup
└── tests/
    ├── test_validation.py       ← physics conservation, ET accuracy (run_tests.py style)
    ├── test_database.py         ← DB schema, seed, bike/tire/parts repos
    ├── test_cli.py              ← all CLI subcommands, in-process via redirect_stdout
    ├── test_scraper.py          ← BikeSpec, validate_spec, import_batch, ALL_KNOWN_BIKES
    └── test_weather_refresh.py  ← _is_stale, refresh_all_venues, CLI --refresh-all
```

---

## PARAMETER GENERALIZATION AUDIT (April 2026)

### Critical Finding: Aero Parameter Over-Generalization
Currently, **71% of bikes (58/81)** share identical drag coefficient (Cd=0.32) and **73% (59/81)** share frontal area (0.45 m²). This violates the "physics-first, minimal generalization" design principle:

- **Cd range:** 0.32 to 0.72 (2.25× multiplier in drag force)
- **Frontal area range:** 0.44 to 0.55 m² (1.25× multiplier)
- **Combined drag variance:** 2.6× across fleet → **±0.25–0.35s ET swing**
- **Physics impact:** Aero drag is 35–40% of total resistance; this over-generalization swamps tuning effects users are testing

**Status:** Unacceptable. Requires bike-specific Cd + frontal area for all 81 models (16 hours research + entry).

### Tire Library Gap
Current: 29 tires (heavily skewed toward Suzuki). Missing:
- **OEM fitments:** Dunlop (Harley, historical Yamaha R1), Michelin, Pirelli, Bridgestone (ZZR1400, CBR)
- **Drag compounds:** DOT drag (Dunlop ET Street, Michelin Sport Comp), R-compound, slicks
- **Regional variants:** Indian market (TVS, Bajaj, RE compound options)

**Target expansion:** 120–150 unique tire specs (priority: 40–50 OEM + drag tires this week).

### Tire Selector Implementation
**Scope:** Allow users to swap front/rear tires and see ET impact in real-time
- App: sidebar dropdowns filtered by compound (stock, DOT drag, R-compound, slick)
- CLI: `--front-tire` / `--rear-tire` flags + `--tire-set` preset groups
- Database: link bike_configs → tire_models (1-to-many); store OEM pair as default
- **Effort:** 4 hours total (UI + DB linking)

**Roadmap advancement:**
- Phase 2 "Remaining" → unblocks user calibration workflows
- Moves validation accuracy from ±0.5s to ±0.1–0.15s range once aero params added

---

## FULL PROJECT ROADMAP

### ✅ Phase 1 — Core Physics Engine (COMPLETE)
- **15/15 sub-models** implemented (rider_dynamics, staging, environmental added April 2026)
- Proper RK4 with aero midpoint re-evaluation + adaptive dt (`use_adaptive_dt=True`)
- Validated within ±0.07s on K5, R1, Hayabusa Gen1
- 245 passing tests

**Phase 1 — Remaining:** ✅ ALL DONE (April 2026)
- [x] `submodels/rider_dynamics.py` — rider CoG shift (longitudinal + height), Cd*A tuck transition
- [x] `submodels/staging.py` — rollout, reaction time, two-step / peak-torque omega_e init
- [x] `submodels/environmental.py` — ρ, DA, power correction, surface grip/RR multipliers, wind
- [x] Adaptive step-size solver: `run(use_adaptive_dt=True)` — dt_min=0.5 ms, dt_max=5 ms, RK4 with aero midpoint re-evaluation. Fixed 1 ms mode kept as default for backward compat.

### ✅ Phase 2 — Database & Ingestion (SUBSTANTIALLY COMPLETE)
- SQLite with WAL-fallback; full schema; weather/venues/tires/parts seeded
- Bike scraper pipeline (bikez.com crawler + 53 curated known bikes + CLI import)
- Note: bikez.com migrated to JS rendering (April 2026) — scraper blocked; known_bikes.py is the active seed path
- Tire library: 29 tires, full Pacejka + thermal (9 manufacturers)
- Parts catalog: 58 parts (sprockets, chains, exhaust, ECU, clutch, weight-reduction, nitrous)
- Weather scheduled refresh (`weather --refresh-all`, staleness-gated)
- `motoquant` rename complete

**Phase 2 — Remaining:**
- [ ] Run `scrape --bulk --priority 1` to populate Japanese Big 4, then `--priority 2` for European/American. Target 400+ bikes.
- [ ] Spot-check gear ratios on imported bikes vs service manuals; add missing model families to `gear_ratios.py`
- [ ] Extend `known_bikes.py` with ~30 more hand-curated bikes (Indian-market focus; Pulsar 200NS, Dominar 250, Hero Xtreme 160R, KTM Duke 200, etc.)
- [ ] Expand venue DB: add international strips (Santa Pod, Pomona, Gainesville, Sydney Dragway, Al-Ain)

### 🔲 Phase 3 — Validation & Calibration Pipeline
- Dragy GPS import (CSV/JSON, 10 Hz v(t) telemetry) with auto run-boundary detection
- Dyno curve import (torque CSV, SAE J1349 correction)
- ECU log import: Woolich Racing / Power Commander / MoTeC (100 Hz, 50+ channels)
- GP auto-calibration loop: fit tire friction + aero Cd from real run data
- v(t) overlay: sim vs. real on same chart
- Residual analysis with confidence intervals
- Multi-run statistical model (mean, std, best-of-N)

**Phase 3 — Web Launch Milestone (at completion):**
- Landing page + documentation site on `motoquant.in` (Vercel)
- Basic web simulator (FastAPI wrapper around CLI, hosted on Railway/DigitalOcean)
- Public leaderboard (real runs, anonymized builder data)
- Marketing to Narhe/Pune tuning shops with "free simulator" + "get Pro license for full tooling"
- Database migration: SQLite → Supabase PostgreSQL
- **This is the credibility milestone before Phase 4 AI/optimization**

### 🔲 Phase 4 — AI & Optimisation Engine
- Bayesian optimisation (BoTorch): multi-variable build tuning within budget constraints
- Sobol sensitivity indices: global parameter importance ranking
- Smart recommendations engine: parts ROI, Indian market pricing
- **Ollama natural-language tuning** (new — from Gemini review): thin LLM wrapper on top of BoTorch; lets users say "optimise my Hayabusa for 35°C at Aamby Valley" and have it translate to parameter overrides
- PINN (Physics-Informed Neural Network): approximate simulation in <1 ms for real-time tuning UI sliders (train on Mac Studio 128 GB RAM)

### 🔲 Phase 5 — Desktop Application (v1.0 Release)
- Tauri 2.0 shell + React 19 / TypeScript frontend
- Simulation output charts: v(t), RPM(t), gear(t), tire temp(t), traction%(t)
- Comparison mode: A vs B overlay (stock vs. modified build)
- Interactive parameter sliders with live PINN preview
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
- Indian market context: parts pricing in INR, venues are Indian drag strips, target audience is Indian drag racers and tuning shops in Pune/Narhe.
- Mac Studio (128 GB RAM) is the development machine — PINN training and BoTorch runs can be memory-hungry; this hardware is an asset for Phase 4+.
- **This document evolves:** You and I both update `CLAUDE.md` as the project grows. It's the source of truth, not a static plan.