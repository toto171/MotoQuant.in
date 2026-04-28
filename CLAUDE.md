# MotoQuant Pro — Persistent Project Context
> Read this file at the start of every session. It is the single source of truth for project state, roadmap, and working instructions.
> Last updated: April 28, 2026 — **Phase A LLM interface layer landed (`motoquant/llm/` + `chat` CLI + `POST /api/chat`).** **April 28, 2026 — Phase A LLM interface layer (Cowork session).** Built `motoquant/llm/` (5 files, 1,400+ lines): `client.py` wraps the Anthropic SDK with a `_call_override` test hook so CI never burns API tokens; `parse_query.py` defines a 12-field tool-use schema (`bike_name`, `venue_name`, `ambient_temp_c`, `humidity_pct`, `altitude_m`, `headwind_kmh`, `rider_mass_kg`, `power_boost_pct`, `mass_delta_kg`, `budget_inr`, `parts_categories`, `optimization_goal`, `notes`) and forces Claude to invoke it via `tool_choice`, then fuzzy-resolves bike_name → bike_id and venue_name → venue_id against the existing DB repos (keeps the prompt tiny — never dumps 327 rows into context); `summarize.py` renders a 2-4 sentence English summary with constrained system prompt (no markdown, INR for money, ends with one concrete suggestion when goal is set); `runner.py` is the SINGLE SOURCE OF TRUTH `run_chat_pipeline()` shared by both CLI (`motoquant chat "..."`) and HTTP (`POST /api/chat`) — pure data in, structured `ChatResult` out, no printing/no HTTP coupling. Bike-not-found returns top-N fuzzy suggestions (`Did you mean: Yamaha YZF-R1 (2009-2014)?`) instead of bare error so frontends can render clickable chips. All failure modes (`llm_not_configured`/`parse_failed`/`bike_not_found`/`sim_failed`) surface as typed strings in the response body — HTTP stays 200 for any user-recoverable error. **`motoquant/run.py` `cmd_chat`:** thin CLI wrapper around `run_chat_pipeline`. Loads `from .llm import run_chat_pipeline`, formats the result as a panel for terminal output. `--json` for machine output, `--verbose` for parser debug. **`motoquant/api.py` `POST /api/chat`:** ChatRequest (query: str, run_summary: bool=True) + ChatResponse Pydantic models, FastAPI `Depends(get_llm_client)` for client injection so tests use `app.dependency_overrides` (the standard pattern). New `_get_db_facade()` returns the MotoQuantDB facade alongside the existing `_get_db()` which returns a raw sqlite3.Connection — needed because the runner uses `db.bikes.search()`/`db.venues.to_environment()` repos. **`requirements-api.txt`:** `anthropic>=0.34.0` added so Railway picks it up on next deploy. **Tests:** `tests/test_llm.py` (22 tests across LLMClient/parse_query/summarize/schema sanity, all use `_call_override` hook — zero live API calls). `tests/test_llm_runner.py` (13 tests across runner pipeline with real DB+real physics + /api/chat via FastAPI TestClient with dependency_overrides). **Hygiene gotchas hit during build:** (a) **File-write tool truncated** `motoquant/llm/__init__.py` mid-string at line 50 (matches the documented hygiene note in this file); recovered via `cat > file << EOF` heredoc — every subsequent file rewrite in this session went through bash heredoc to avoid recurrence. (b) Same truncation hit **`motoquant/run.py`** during the parser additions; restored from git (3812 lines), reapplied via Python heredoc. Final file 3936 lines (3812 + 124 cmd_chat + parser block). (c) **FUSE `__pycache__` mtime issue:** Python loaded stale `__init__.cpython-310.pyc` from before runner.py existed; `from motoquant.llm import run_chat_pipeline` failed with `ImportError` even though the `.py` was correct. Worked around with `PYTHONPYCACHEPREFIX=/tmp/pyc-cache` for verification runs. Doesn't affect production — Railway has a real filesystem. (d) **Bound-method bug in test:** `cls.get_llm_client = func` made `self.get_llm_client` a bound method on instance access, breaking FastAPI's dependency-key lookup (`dependency_overrides[<bound method>]` doesn't match `Depends(get_llm_client)`). Fixed by storing the api MODULE as `cls.api` and accessing `self.api.get_llm_client` (returns the unbound function). **Verification:** 176 tests green across `test_llm + test_llm_runner + test_validation + test_scraper + test_two_stroke`. Reference baselines preserved EXACTLY to 4 decimals: K5 **10.0334s** (Δ +0.0000), R1 **10.2859s** (Δ +0.0000), Hayabusa **10.4712s** (Δ +0.0000). End-to-end smoke through FastAPI TestClient with mocked Claude: query 'how fast is my K5 in 35C heat at Aamby Valley?' → bike_id=1, venue_name='Aamby Valley', ET=10.288s, summary returned. **To go live in prod:** (1) `pip install anthropic --break-system-packages` locally; (2) `export ANTHROPIC_API_KEY=sk-ant-...` on Railway; (3) frontend (desktop SimulatePage / web SimulatorWidget) wires up `POST /api/chat` and renders bike_suggestions chips on `error == 'bike_not_found'`. **Next session: Phase B per-bike ML calibrator** — synthetic training data (perturb `aero.cd`/`tires.mu_peak`/`peak_torque_nm`/`engine_inertia_kgm2` across plausible ranges, learn the inverse mapping from measured ET/trap/60ft → correction factors), 4-target XGBoost regression, `calibration_runs` DB table for accumulating real Dragy uploads over time. **Previous:**
> **Standing tool note (Apr 24 PM):** whenever `spec_to_bike_config` changes (importer.py physics, new gear ratios, new parasitic/inertia/Cd rules), the `bike_configs` JSON blobs in `motoquant.db` go stale and `/api/simulate?bike_id=N` silently diverges from the sweep path. Run `MOTOQUANT_DB=motoquant.db python scripts/reseed_configs_from_specs.py` after any such change. Diagnostic: `scripts/diagnose_r15_db_path.py` does a side-by-side DB-vs-spec field diff + 3-point power sweep to confirm. Reference baselines (K5/R1/Hayabusa from `defaults.py`) are correctly skipped — they are hand-curated, not in ALL_KNOWN_BIKES.

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


## 🛡️ SESSION HYGIENE — GOTCHAS FROM PAST SESSIONS

> *"Fix the same mistake twice, and it is a rule. Fix it three times, and it is a section in CLAUDE.md."*

These rules exist because every one of them got broken at least once and cost meaningful time to unbreak. Treat them as load-bearing, not advisory.

### CLAUDE.md edits are surgical prepends, never rewrites
Line 3 holds a nested chain of every historical session wrapped in a single paragraph. When adding a new session entry, INSERT one new line at the top of that chain — do NOT regenerate the file. If you ever end up with a CLAUDE.md shorter than 670 lines, you lost the trailing sections (KEY ARCHITECTURAL / PHYSICS ENGINE / DEVELOPMENT WORKFLOW / GEMINI ROADMAP / NOTES FOR FUTURE SELF). Restore with `git show HEAD:CLAUDE.md > CLAUDE.md` and retry with an Edit/Python-insert, not a Write.

### Regression tests must exercise the production path
A test that applies the fix inside the test and then asserts the test is own scaling logic worked is tautological — it passes even after the real bug returns. Every regression test must hit the exact code path the bug hit: DB round-trip for `/api/simulate?bike_id=N`, CLI subcommand for CLI bugs, HTTP request for API bugs. Rule of thumb: the test must fail if you revert the production fix.

### Commits are staged by explicit file list
Never `git add -A` or `git add .` in this repo. The working tree routinely holds unrelated WIP from prior sessions (truncated files, CRLF artefacts, parallel-machine edits, scratch scripts). Pass explicit paths to `git add`. If you are not sure what to stage, `git status --short` first and decide file by file.

### Pull first, push early
Parallel sessions on multiple machines are common here. At session start: `git fetch && git log --oneline HEAD..origin/main`. If that is non-empty, pull/rebase BEFORE touching shared files (CLAUDE.md, importer.py, known_bikes.py, validation_sweep.py, web/app/page.js). At session end, push immediately — a 10-commit gap produces ugly rebase conflicts on exactly the files everyone edits.

### Suspect CRLF/LF drift on Windows
The repo uses CRLF for Python source (legacy from Windows editing). If `git diff --stat` shows thousands of delta lines on a file you barely touched, it is almost certainly line endings. Verify: `file <path>` shows LF vs CRLF; `diff <(git show HEAD:path) <(tr -d '\r' < path) | wc -l` shows real content diff. Do not normalise to LF mid-session — that will silently fail the rebase and hide actual changes.

### Verify agent work before trusting the summary
Agents (and humans mid-flow) sometimes declare "production ready" while: (a) rewriting CLAUDE.md destructively, (b) writing tautological tests, (c) skipping the sweep they claimed to run, (d) never testing the code path where the bug actually lives. Before trusting any agent summary: `git diff` the files it touched, `wc -l` to catch truncation, `cat` the test to confirm it drives real code, `ls reports/` for new JSON, and check whether the documented sweep metrics match what is committed.

### After `spec_to_bike_config` changes, re-seed the DB
See the standing-tool note at the top of this file. `scripts/reseed_configs_from_specs.py` propagates physics changes into `bike_configs`. Without it, `/api/simulate?bike_id=N` silently diverges from the sweep path by 2–5 seconds per bike — invisible until someone does a DB-vs-spec diff.

### File-write tools can truncate; verify length
The Cowork Write/Edit tools occasionally truncate at ~5-6 KB when rewriting existing files. After any Write/Edit on a Python source or CLAUDE.md, run `wc -l <path>` and eyeball `tail -3 <path>` to confirm the last line is what you intended. If truncated, re-write via `cat > file << EOF` in bash, which has no such limit.

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

## CURRENT STATE (as of April 22, 2026)

### Test suite
- **739+ tests passing** across 15 test files — 27 integration gated behind `MOTOQUANT_SLOW_TESTS=1`. Breakdown: 244 Phase 1/2 + 56 Phase 3 Dragy + 68 Phase 3 dyno/overlay/calibrator/multi-run + 69 Phase 3 ECU import + Phase 3 API endpoints (~34 with /api/bikes/suggest + /api/venues/resolve coverage) + 69 Phase 4 analysis: ROI + Sobol + 84 Phase 4A/4B surrogate models + 65 Phase 4 recommendations: 38 unit + 27 integration + 27 Phase 4 catalog integration + new Apr 20 web-launch tests (`/api/bikes/suggest`, `/api/venues/resolve`, `bike_suggestions` schema + repo) + test_compatibility + test_tire_fitments
- **April 20, 2026 web-launch additions:** POST `/api/bikes/suggest` (user-submitted bike requests → `bike_suggestions` table, plausibility-flagged), POST `/api/venues/resolve` (location → race-environment; seeded-venue match first, OWM live fallback with local ρ/DA/PCF compute), `BikeSuggestionsRepository`, `/bikes` Next.js browser (paginated with manufacturer/category filters + detail page with OEM tire fitments), `SuggestBikeForm` component, `LocationPicker` component (text + browser geolocation) wired into `SimulatorWidget` with matched-venue/live-weather status badge. New landing page "Intelligence Layer" section surfaces Phase 4 AI features. Stats strip updated: 267 bikes / 69 tires / 296 parts / 12 venues / 674 tests / 15 sub-models.
- Integration tests for recommendations engine gated behind `MOTOQUANT_SLOW_TESTS=1` (each runs full physics engine on ~70 parts; ~45s per test)
- `tests/test_catalog_integration.py` seeds full catalog + all 267 bikes in-memory and asserts: no RE 350 ↔ Harley/RE 650 leak, no Hayabusa ↔ Panigale/RSV4 leak, no Panigale V4 ↔ RSV4 leak, every bike has at least one exhaust, every bike has ≥20 parts, catalog ≥400 parts, `_enrich_bike_row_for_fitment` idempotent + hydrates manufacturer/chain_pitch, `_infer_cylinder_config` + `_infer_chain_pitch` produce expected values for representative specs
- Scraper + validator tests (78) cover the full 267-bike `ALL_KNOWN_BIKES` catalog end-to-end
- Run with: `python -m pytest tests/ -q` from the project root
- **Optional deps** for surrogate/sobol/roi: `pip install scikit-learn SALib --break-system-packages`

### Production database (`motoquant.db`)
- Bikes: **270** (3 seeded reference + 267 curated known bikes across 25+ manufacturers)
- Tires: **69** (full Pacejka + thermal coefficients, 15 manufacturers, 5 compound types)
- Parts: **424** across 17 categories with **bike-specific mod libraries** — min 24 / max 192 / avg 106.8 parts per bike. **91 exhausts** covering every seeded bike (ADV big-bore, cruiser/muscle V-twin, parallel twin, V4 litre, small-cc Indian + SE Asia). Catalog lives in `motoquant/database/seed.py` (core ~296) plus modular expansion in `motoquant/database/seed_catalogs/`:
  - `adv_cruiser_exhausts.py` — 32 parts (Akra / SC-Project / Arrow / Termignoni / LeoVince / HP Corse / Remus / S&S / Vance & Hines / Two Brothers / Cobra / Rinehart / Agency Power / Toce / Agostini) — closed 22-bike ADV/cruiser exhaust gap
  - `drag_specific.py` — 34 parts (7 nitrous / 6 boost kits / 5 clutch kits / 5 fuel system / 5 air filter / 6 quickshifter)
  - `premium_universal.py` — 62 parts (18 brakes / 18 suspension / 8 batteries / 10 ECU piggybacks / 4 wheelie bars / 4 bodywork)
  Small-cc Indian + SE Asia underbones still get full sprocket (428/520-pitch) / chain / ECU / filter / slipper / QS / platform-specific exhaust coverage. Fitment uses tight `family`-tier rules with `manufacturers` + `engine_configs` + displacement bounds + `chain_pitch` — verified no cross-brand or cross-segment leaks by 27 catalog-integration tests.
- Venues: **12** (5 Indian + 7 international: Santa Pod, Pomona, Gainesville, Sydney, Dubai, Al-Ain, Jerez)
- Bike-tire fitments: **209** OEM links (bike_model_id ↔ tire_model_id, front/rear) — needs extension for new 132 bikes

### Bike catalog coverage (ALL_KNOWN_BIKES = 267 bikes)
- **Sport/superbike fleet (78 bikes):** Suzuki, Yamaha, Honda, Kawasaki, BMW, Ducati, Aprilia
- **Indian-market additions (30 bikes, April 2026):** KTM (Duke 200/250/390, RC 200/390), Bajaj (Pulsar NS200/RS200/220F, Dominar 250/400), TVS (Apache RR 310, RTR 200/160 4V), Royal Enfield (Continental GT 650, Interceptor 650, Himalayan 450), Yamaha India (R15 V4, MT-15 V2, FZ-X), Honda India (CBR 250R, CB 300R, Hornet 2.0), Kawasaki India (Ninja 300/400, Z650), Triumph (Speed 400, Speed Twin 900), Husqvarna (Svartpilen 401, Vitpilen 401), Hero (Xtreme 160R)
- **International expansion (27 bikes, April 2026):** Yamaha (R7, XSR900, VMAX 1700), Honda (CB650R, CBR500R, Rebel 1100), Kawasaki (ZX-4RR, Z H2, Vulcan S), Suzuki (SV650, GSX-8S, Katana), Ducati (Panigale V4R, Diavel V4, Scrambler 1100), Triumph (Rocket 3, Trident 660, Tiger 900), BMW (R1250GS, M1000R), Aprilia (RS 660, Tuono 660), MV Agusta (F3 800), Harley-Davidson (Low Rider ST, Road Glide), CFMoto (700CL-X Sport), Benelli (TNT 600i, Leoncino 500), QJ Motor (SRK 400)
- **Phase 4+ Indian market 200cc+ expansion (57 bikes, April 20, 2026):** Bajaj (Pulsar 200/NS200/N250/F250/NS400Z, Avenger Cruise/Street 220), TVS (Apache RTR 200, Ronin 225), Yamaha India (FZ25, R15 V1/V2/V3, R3, MT-03), Honda India (CB350 H'ness, CB350RS, CB300F), Suzuki India (Gixxer SF 250, Gixxer 250, Intruder 250), Mahindra (Mojo XT300), Hyosung (GT250R, GT650R), Hero (Karizma R, Karizma XMR 210, XPulse 200), Royal Enfield (Classic 350 J, Meteor 350, Hunter 350, Thunderbird 350, Bullet 500, Himalayan 411, Scram 411, Shotgun 650, Guerrilla 450), Jawa (42, Perak), Yezdi (Roadster, Scrambler, Adventure), Benelli India (302R, TNT 300, Imperiale 400, 502C), CFMoto India (300NK, 450NK, 650NK, 300SR), BMW India (G310R, G310GS, G310RR), Harley India (X440), Aprilia India (RS457, Tuono 457), Triumph India (Scrambler 400X), KTM India (Duke 390 early, 390 Adventure)
- **Phase 4+ Worldwide 300cc+ expansion (45 bikes, April 20, 2026):** Broader Honda/Yamaha/Kawasaki/Suzuki/BMW/Ducati/Aprilia/Triumph/MV Agusta/Harley/Indian/KTM/Moto Guzzi/Husqvarna/Buell lineup covering previously-missed 300–1300cc platforms
- **Phase 4+ SE Asia small-cc drag bikes (15 bikes, April 20, 2026, ≥149cc):** Honda (RS150R, Winner X, Supra GTR 150, Sonic 150R, CB150R Streetfire, CBR150R, CBR250RR), Yamaha (Y15ZR, Y15ZR V2, Exciter 150, Exciter 155 VVA, Aerox 155, R25), Kawasaki (ZX-25R I4, Ninja RR Mono 250)
- **All 267 bikes have individual Cd (0.55–0.95) and frontal_area_m2 (0.35–0.68)** — zero over-generalization
- **New manufacturers added in April 2026:** CFMoto, Benelli, QJ Motor, Mahindra, Hyosung, Jawa, Yezdi, Indian Motorcycle, Moto Guzzi, Buell

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
parts       list/search by category; --bike-id N filters to bike-compatible only;
            --impact PART_ID --bike-id N shows ET/trap delta + cost-per-tenth + compat warning (supports --json)
weather     fetch live OWM, DA trend, --refresh-all
scrape      crawl bikez.com for a manufacturer
import      --known-bikes (108 curated) or --spec-json FILE
history     simulation run history
leaderboard best ETs across all runs
analysis    roi, sobol, optimize, recommend, surrogate (generate/train/evaluate/predict/train-dnn)
pricing     refresh / status / stale — Indian-market retailer URL seeding + coverage reports
            (GST 18 % + ₹250 courier + 30 % import duty landing-cost math)
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
│   │   ├── seed_catalogs/       ← Phase 4 modular expansion sub-package
│   │   │   ├── adv_cruiser_exhausts.py   ← 32 ADV + cruiser/muscle exhausts
│   │   │   ├── drag_specific.py          ← 34 nitrous / boost / clutch / fuel / filter / QS
│   │   │   └── premium_universal.py      ← 62 brakes / suspension / battery / ECU / wheelie / bodywork
│   │   ├── bike_repo.py         ← upsert_from_config(), search(), add_provenance()
│   │   ├── tire_repo.py, parts_repo.py, venue_repo.py, sim_repo.py, weather_repo.py
│   │   ├── bridge.py            ← BikeConfig ↔ DB row converters
│   │   ├── weather_refresh.py   ← refresh_all_venues(), staleness checks, RefreshSummary
│   │   └── pricing_refresh.py   ← retailer URL templates (~50 Indian + import retailers),
│   │                              estimate_landing_cost_inr (GST+courier+duty),
│   │                              refresh_retailer_urls, stale_parts, coverage_report
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
│       ├── known_bikes.py       ← ALL_KNOWN_BIKES (267 bikes — 78 sport + 30 Indian + 27 intl + 57 Indian 200cc+ + 45 worldwide 300cc+ + 15 SE Asia small-cc)
│       ├── catalog.py           ← SCRAPE_CATALOG — 17 manufacturers, categories, year ranges
│       ├── gear_ratios.py       ← Tier-1 named-model lookup (150+ families) + Tier-2 defaults (incl. adventure/touring)
│       └── bulk_scrape.py       ← BulkScrapeOrchestrator — checkpoint/resume/dedup
└── tests/
    ├── test_validation.py       ← physics conservation, ET accuracy (run_tests.py style)
    ├── test_database.py         ← DB schema, seed, bike/tire/parts repos
    ├── test_cli.py              ← all CLI subcommands, in-process via redirect_stdout
    ├── test_scraper.py          ← BikeSpec, validate_spec, import_batch, ALL_KNOWN_BIKES
    ├── test_weather_refresh.py  ← _is_stale, refresh_all_venues, CLI --refresh-all
    ├── test_pricing.py          ← 33 tests — URL templates, brand-dedup search,
    │                              landing-cost math, refresh idempotency, stale thresholds
    ├── test_dragy.py            ← 56 tests — Dragy GPS parser
    ├── test_calibration.py      ← 44 tests — dyno, overlay, calibrator end-to-end
    ├── test_ecu.py              ← 69 tests — ECU log import (Woolich/PC-Link/MoTeC)
    ├── test_recommendations.py  ← 65 tests — Smart Recommendations Engine (38 unit + 27 integration)
    ├── test_api.py              ← 24+ tests — FastAPI endpoints (health, quick/full sim, compare, dragy upload, dyno upload, bike suggest)
    └── test_catalog_integration.py  ← 27 tests — no cross-brand leaks, ≥400 parts, every bike has exhaust + ≥20 parts, enrich idempotent, infer helpers
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

### ✅ RESOLVED: Parts Catalog Bike-Specificity + Chain-Pitch Infrastructure (April 20, 2026)
**Previously:** Parts catalog had major compatibility leaks — "Arrow RE 650 Full System" matched RE Classic 350 (wrong; Arrow RE 650 is a parallel twin exhaust); "Akrapovic Full System Panigale" matched Hayabusa; many 200-400cc Indian commuters (Pulsar, Apache, R15, Duke, Hornet, Xtreme) had only 6-11 parts because family-tier rules using `engine_configs` and `chain_pitch` silently matched nothing — the compatibility engine's `manufacturers` check was a TODO no-op, `EngineParams` had no `cylinder_config` field, and `DrivetrainParams` had no `chain_pitch` string code (only `chain_pitch_mm`). Result: family-tier constraints never filtered and everything leaked.
**Fixed (three-layer fix):**
1. **Compatibility engine** (`parts/compatibility.py`): Implemented the `manufacturers` constraint with case-insensitive name match and warning-on-missing-field fallback.
2. **Data model + importer**:
   - Added `cylinder_count` + `cylinder_config` fields to `EngineParams`; added `chain_pitch` string field to `DrivetrainParams`.
   - Added `_infer_cylinder_config(spec)` in `importer.py` (V-twin makes, V4 model tokens, cyl-count fallback).
   - Added `_infer_chain_pitch(spec)` in `importer.py` (HD/Indian/Victory belt; BMW R/K-series + Moto Guzzi V-twins shaft; model tokens for Hayabusa/ZX-14R=530, SE Asia cubs=428; displacement-banded for 150-1300cc). Chain-drive bikes correctly get 428/520/525/530; 14 genuinely belt/shaft bikes get `None`.
   - `extract_headline_specs` now populates `cylinder_count`/`cylinder_config` on `bike_models`.
   - Reference bikes (GSX-R K5, YZF-R1 4C8, Hayabusa Gen1) in `defaults.py` now set `cylinder_count=4, cylinder_config="I4", chain_pitch="530"` explicitly.
3. **Parts catalog** (`seed.py`): 56 new bike-specific parts organized by segment (Indian 150-250 commuters, SE Asia 150cc cubs, Indian 250-400 mid-sport, cruiser small/mid, RE 650 twin, adventure, entry twins 300-500, scooter). Each uses tight `family`-tier `fitment_rules` with `manufacturers` + `engine_configs` + displacement bounds + `chain_pitch`. Existing exhaust fitment rules also tightened: RE 650 Arrow now requires I2 parallel twin (no leak to RE 350 single); Hayabusa Akra requires I4 1299-1341cc; Panigale V4 and RSV4 are separated with ordering-safe check.
**Leak scan:** All 45 exhausts scanned against 270 bikes — no cross-brand or cross-segment leaks.
**Coverage impact:** min 6 → 24 parts/bike, avg 70 → 95, max 133 → 152.

### ✅ RESOLVED: Validator Bound for High-Revving I4 (April 20, 2026)
**Previously:** Validator rejected Kawasaki ZX-25R (peak_torque_rpm=14500, redline ~17000) because `peak_torque_rpm` upper bound was 14000 rpm — tuned around inline-4 superbikes that peak torque ~10–12k rpm.
**Fixed:** `peak_torque_rpm` upper bound raised from 14000 → 15000 in `validator.py` line 42, enabling the SE Asia small-cc drag catalog expansion. No known production motorcycle peaks torque above 15000 rpm, so the envelope remains physically meaningful.

### ✅ RESOLVED: Bike Catalog Small-cc & Indian Coverage (April 20, 2026)
**Previously:** 135 bikes total, heavily weighted toward international 600cc+ sport; most Indian 200–400cc commuters and SE Asia small-cc underbones/cubs (active drag scene in Malaysia/Thailand) were missing.
**Fixed:** ALL_KNOWN_BIKES grew from 135 → 267 (+132) across three curated batches:
- **+57 Indian 200cc+ since 2000** — Bajaj/TVS/Yamaha India/Honda India/Suzuki India/Mahindra/Hyosung/Hero/RE/Jawa/Yezdi/Benelli India/CFMoto India/BMW India/Harley India/Aprilia India/Triumph India/KTM India full lineup
- **+45 worldwide 300cc+ since 2000** — completing Honda/Yamaha/Kawasaki/Suzuki/BMW/Ducati/Aprilia/Triumph/MV Agusta/Harley/Indian/KTM/Moto Guzzi/Husqvarna/Buell previously-missed platforms
- **+15 SE Asia enthusiast drag bikes (≥149cc)** — Honda underbones/cubs/Thai sport (RS150R, Winner X, Supra GTR, Sonic 150R, CB150R, CBR150R, CBR250RR), Yamaha (Y15ZR/V2, Exciter 150/155, Aerox 155, R25), Kawasaki (ZX-25R I4, Ninja RR Mono 250)
All 132 new bikes pass scraper/validator tests (78 tests). Indian-market small-cc sim ETs remain pre-existing `+1.0–3.0s slow` per documented traction model limitation — not a data-quality issue.

### ✅ RESOLVED: Catalog Coverage + Mod-Impact CLI + Integration Tests (April 20, 2026)
**Previously (after April 20 earlier work):** Catalog at 296 parts with 22 bikes (ADV/cruiser big-bore, Indian Motorcycle V-twins) still missing any exhaust match; no ergonomic way for a user to answer "what will *this* part do to *my* bike?"; zero automated guard against future cross-brand compatibility leaks.
**Fixed (three-phase):**
1. **Catalog expansion via `seed_catalogs/` sub-package** (+128 parts → **424 total**):
   - `adv_cruiser_exhausts.py` — 32 parts closed the ADV + cruiser/muscle exhaust gap; also widened FTR 1200 S fitment (accepts `cruiser`, `muscle`, `naked`, `sport`; disp 1190-1220cc). Importer `_V_TWIN_2CYL_MAKES` gained the bare short-form manufacturer names (`"Indian"`, `"Harley"`, `"HD"`, `"Harley Davidson"`) so DB-stored short names still infer V2.
   - `drag_specific.py` — 34 drag-oriented parts (7 nitrous, 6 boost kit, 5 clutch kit, 5 fuel system, 5 air filter, 6 quickshifter) with correctly mapped param paths: `drivetrain.total_shift_time_ms`, `forced_induction.boost_type`, `clutch.spring_preload_n`, scaled `engine.peak_power_hp` multipliers (1.45/2.0 replaced by physically-meaningful 1.03/1.04).
   - `premium_universal.py` — 62 universal premium options (Brembo/Accossato brakes, Öhlins/K-Tech/Bitubo suspension, Shorai/Antigravity batteries, Bazzaz/Dynojet/Rapid Bike ECUs, MPS/Brock's wheelie bars, Woodcraft/Sato/Puig bodywork) with corrected param paths (`chassis.cog_height_mm`, `wheelie.wheelie_bar`).
2. **Mod-impact CLI** — `parts --bike-id N --impact PART_ID [--json]` runs baseline + modified sims in-process, prints ET delta (s), trap delta (km/h), cost-per-tenth (₹), and compatibility warning if fitment fails. `parts --bike-id N` alone filters the list to parts compatible with that bike. Both surfaces use `getattr(args, "bike_id", None)` so older tests with partial Namespaces still work.
3. **Dedicated integration tests** — `tests/test_catalog_integration.py` (27 tests across 6 classes): TestNoLeaks (RE 350 / Hayabusa / Panigale V4 / RSV4 isolation), TestCoverage (every bike has exhaust, ≥20 parts/bike, ≥400 catalog parts), TestEnrichBikeRow (manufacturer join, chain_pitch fallback, idempotency), TestInferCylinderConfig (I1/I2/I3/I4/V2/V4 across Ducati/HD/Indian short/SV650/Panigale/RSV4), TestInferChainPitch (HD belt → None, Hayabusa → 530, sub-200cc → 428, mid-range → 520), TestFamilySeparation (RE 650 twin-only, Indian Scout V2).
**Coverage after:** 270 bikes × 424 parts, min 24 / avg 106.8 / max 192 parts per bike, 0 bikes missing exhaust, 0 invalid-param-path UserWarnings. K5 smoke test still 10.034s (validated baseline preserved).

### ✅ RESOLVED: Two-Stroke Expansion + Catalog + Compat Filter (April 21, 2026)
**Previously:** Catalog was 4-stroke only. Indian drag scene runs heavily on 2T (Yamaha RX100/RX135/RXZ, RD350/RD400, Yezdi 250, modern KTM 300 EXC). SE Asia drag includes RS125/RGV250. None of these bikes, their physics, or their parts were modelled. Additionally, the `FitmentMatch` constraint system had no stroke-cycle dimension — so any 2T parts added to the catalog would silently leak into 4T bikes of the same displacement/config.
**Fixed (four-phase):**
1. **20 two-stroke bikes added to `ALL_KNOWN_BIKES`** (267 → 287): Yamaha (RD350/400/500LC, RZV500R, RX100/RX135/RXZ135, TZR250 3MA), Suzuki (RGV250 VJ22, RG500 Gamma, GT750 'Water Buffalo'), Kawasaki (KR-1S, H2 Mach IV 750), Honda (NSR250R MC21, CR500R), Aprilia (RS125, RS250), KTM (300 EXC TPI, 250 SX), Yezdi (250 Classic). Each spec sets `stroke_type=2` plus `reed_valve` / `powervalve` / `expansion_chamber` / `tuned_rpm` where applicable.
2. **Importer physics branching** (`scraper/importer.py`):
   - `_build_engine_from_spec` branches on `stroke_type == 2` to: (a) generate a **Gaussian 2T expansion-chamber torque curve** via `_synthetic_2stroke_torque_curve()` in `defaults.py`/`models.py` (power band widens with powervalve), (b) scale `engine_inertia_kgm2` × 0.60 (no valvetrain), (c) set `tuned_rpm` (from spec or defaulting to `peak_power_rpm`), (d) propagate `reed_valve` / `expansion_chamber` / `powervalve` flags into `EngineParams`, (e) raise idle RPM to 1800.
   - `spec_to_bike_config` additionally overrides: `staging.launch_rpm = tuned_rpm × 0.92` + `staging.two_step = True` for 2T (proper drag launch point), `parasitic.valve_train_power_w = 0.0` + `parasitic.oil_pump_power_w = 60.0` (premix pump) + `parasitic.water_pump_electric = True` for air-cooled 2T.
3. **`seed_catalogs/two_stroke.py`** — **41 2T-specific parts** (424 → 465 total) across 7 sub-categories:
   - Expansion chambers: JL / Tyga / Jolly Moto / Arrow / DEP / Higgspeed / Moto Carrera / MAC / FMF for RD350/RD400/RD500/RX/RS/GP250/H2/GT750/KTM/CR500/TZR/Yezdi (13 pipes)
   - Reed valves: VForce 3/4, Boyesen RAD, Barikit (6 parts)
   - Powervalve controllers: Zeeltronic (YPVS/RAVE/RC Valve/KIPS), Nova SAPC (5 parts)
   - Jet kits: Dynojet Stage 2/3, JD Jetting, RD Stuff (5 parts)
   - Head mods: Mill-Tek, Wiseco, Athena, TM Racing (4 parts)
   - CDI/ignition: Vape, HPI Racing, Rex's (4 parts)
   - Flat-slide carbs: Keihin PWK 28/38, Mikuni TMX/VM (4 parts)
4. **`FitmentMatch.stroke_type` constraint** added to `motoquant/parts/compatibility.py` — matches bike `engine_params.stroke_type` (default 4T when unset for backwards compatibility). Every 2T part declares `"stroke_type": 2` in its fitment rule. `_enrich_bike_row_for_fitment` in `parts_repo.py` now hydrates `stroke_type` from `engine_params`. Leak scan: **0 2T parts leak to any of 270 4T bikes**.
**Coverage:** 20/20 2T bikes have ≥1 part match; every 2T bike has ≥1 exhaust option; min 1 / avg 3.3 / max 6 dedicated 2T parts per bike (plus universal sprockets/chains/brakes). Reference baselines preserved: K5 **10.034s**, R1 **10.286s**, Hayabusa **10.472s**.
**Validator widening:** `peak_torque_rpm` 14000 → 15000 (already done April 20 for ZX-25R; covers 2T too); `compression_ratio` window widened 6.0–16.5 for vintage low-compression 2T; new bound `tuned_rpm` 3000–18000 rpm.
**Tests:** new `tests/test_two_stroke.py` with 30 tests across 5 classes (TestTwoStrokeSpecs / Importer / StrokeTypeFilter / CatalogIntegrity / ReferenceBaselinesPreserved). `tests/test_scraper.py` gear-count minimum relaxed 5 → 4 (historical 4-speed RX100). `tests/test_scraper.py` displacement minimum relaxed 149 → 95cc (RX100 98cc, RS125 124cc). Fast suite 578 passing, full suite 748 passing.

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

**Phase 3 — Deployment: LIVE ✅ (verified April 23, 2026)**
- [x] Push repo to GitHub — `github.com/da25mem5s02-debug/MotoQuant_v1`, branch `main`, HEAD `4959cdf`
- [x] Railway project → connected → auto-deploys from `nixpacks.toml` on every push to `main`
  - Project: `proactive-adventure` (Railway auto-named; cosmetic rename to `motoquant-api` pending)
  - Service: `web` · region `us-west2` · 1 replica · status 🟢 Online
  - URL: **`https://web-production-de6eb.up.railway.app`**
  - Latest deploy: ✅ ACTIVE on commit `4959cdf`
- [x] ~~Set env var `MOTOQUANT_DB=/app/motoquant.db` on Railway + upload seeded DB~~ — **resolved implicitly**: `motoquant.db` is *tracked in git* (file was added before the `*.db` .gitignore rule; `git ls-files motoquant.db` confirms). Every Railway build ships the 5 MB seeded DB into `/app/motoquant.db`. API default in `motoquant/api.py:92` — `os.environ.get("MOTOQUANT_DB", "motoquant.db")` — resolves against the container WORKDIR. `/api/health` returns `{"status":"ok","database":"connected","bike_count":270}` confirming the seeded catalog is live. **Trade-off:** every `db seed` run dirties the tracked DB and shows up in `git status`, which slowly bloats the repo. Long-term: move to a Railway persistent volume + one-time seed script, or explicitly document "regenerate DB before release" in the release playbook.
- [x] Update `vercel.json` with actual Railway URL → deploy web/ to Vercel
  - Vercel project: `moto-quant-v1` (on Hobby plan, account `da25mem5s02-debugs-projects`)
  - Linked to GitHub `da25mem5s02-debug/MotoQuant_v1` branch `main`
  - Status Ready, 0% error rate over 6h window (265 edge requests / 27 function invocations)
  - Production Checklist 4/5 — only "Preview Deployment" unchecked (trivial, happens on first PR)
- [x] Point `motoquant.in` DNS → Vercel — `www.motoquant.in` attached and resolving
  - Also live: `moto-quant-v1.vercel.app`

**Phase 3 — Post-launch hygiene (non-blocking, user-action):**
- [ ] Delete orphan Vercel project `motoquant-web` (created Apr 15, never git-linked — sitting empty at `motoquant-web.vercel.app`)
- [ ] Upgrade Railway trial ($4.86 / 24 days left as of Apr 23) → Hobby or Pro before suspension
- [ ] Rename Railway project `proactive-adventure` → `motoquant-api` (cosmetic only)
- [ ] Long-term DB strategy decision: keep `motoquant.db` tracked in git (current — bloat risk) vs Railway persistent volume + seed script on first deploy

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
- [ ] **Indian market pricing API integration** — `motoquant/database/pricing_refresh.py` has the retailer URL templates (~50 Indian + import retailers) and GST 18 % + ₹250 courier + 30 % import-duty landing-cost math, but there's no live retailer-scraping layer yet. WIP edits to `pricing_refresh.py` sit in the working tree uncommitted as of Apr 22 — those likely start the per-retailer adapter work.
- [ ] **Live surrogate preview in desktop BuildPage** — BuildPage currently re-runs `/api/simulate/quick` on every toggle (~50 ms full sim). Adding a `/api/surrogate/predict` FastAPI route that loads `surrogate_dnn.pkl` or `surrogate.pkl` once at startup and scores one vector per call would drop BuildPage slider ticks to ~1 ms. Needs: API route + a `useSurrogate()` React Query hook + BuildPage wiring behind a toggle (so the user can still run the "real" sim on demand).
- **Surrogate model — status of all three phases:**
  - ✅ **Phase 4A — DNN surrogate:** COMPLETE (Apr 15, 2026). 4-layer MLP (21 → 256 → 512 → 512 → 256 → 2 heads) in `motoquant/analysis/surrogate_dnn.py`; PyTorch primary, sklearn fallback. CLI: `analysis surrogate train-dnn`. Huber loss + batch norm + dropout + feature/target normalisation baked in. Trained pickle ships in repo root as `surrogate_dnn.pkl` (10.8 MB).
  - ✅ **Phase 4B — BDT baseline:** COMPLETE (Apr 15, 2026). XGBoost surrogate in `motoquant/analysis/surrogate_xgb.py`. CLI: `analysis surrogate generate/train/evaluate`. Pickles: `surrogate.pkl` (4.4 MB) + `surrogate_v2.pkl` / `_v3.pkl` / `_sport.pkl` variants.
  - **Phase 4C — PINN:** Deferred. Physics-Informed Neural Network justified only when DNN shows poor extrapolation outside its training distribution. Bakes physics constraints into the loss function for edge-of-distribution generalisation. No measured DNN failure to justify the complexity yet — keep on the shelf.
- **No new Phase 4 code since Apr 16, 2026** (Smart Recommendations Engine) — logged so future-me doesn't re-add these items as "must do" without fresh evidence.

### 🔄 Phase 5 — Desktop Application (v1.0 Release) [IN PROGRESS]

**Phase 5 — Completed items:**
- [x] **Tauri 2 + React 19 + TypeScript 5.6 + Vite 5 scaffold** (Apr 22, 2026) — `desktop/` at repo root. Rust side (`desktop/src-tauri/src/lib.rs`): `pick_free_port()` binds a throw-away `TcpListener` to grab an ephemeral port, then `spawn_sidecar()` launches the PyInstaller binary with `--host 127.0.0.1 --port <N> --log-level info`; stdout/stderr piped into Rust's `log` crate. 8 s startup deadline with polling for `get_backend_url` Tauri command. `MOTOQUANT_DEV_BACKEND_URL` env-var override lets devs run `uvicorn --reload` manually instead of spawning the binary. CSP allows `http://127.0.0.1:*` so the React frontend can reach the sidecar. 1440×900 dark-theme window, resizable down to 1200×760.
- [x] **Typed API client** — `desktop/src/types/api.ts` (Pydantic mirrors for all endpoints incl. Bike/Venue/Tire/Part/Simulate/QuickSim/**Compare**/**Leaderboard**), `desktop/src/lib/api.ts` (typed fetch with `ApiRequestError` + Tauri-invoke base-URL resolution with VITE_API_URL + `http://127.0.0.1:8000` fallback), `desktop/src/hooks/useApi.ts` (React Query hooks: `useBikes`, `useBike`, `useVenues`, `usePartsCategories`, `useParts`, `useSimulate`, `useQuickSimulate`, **`useCompare`**, **`useLeaderboard`**).
- [x] **Shell components** (`desktop/src/components/`) — `Layout` + `Sidebar` (6 nav entries: Simulate · Bikes · Build · Compare · History · Settings) + `TopBar` (live engine-online chip polling `/api/health` every 15 s) + `BikePicker` (fuzzy-search 290-bike dropdown) + `StatTile` + `SimChart` (recharts, 4 default channels: speed/RPM/accel-g/power-kW with ET reference line).
- [x] **Pages — 6 complete:**
  - **SimulatePage** — bike + venue picker + rider/power/mass sliders + adaptive-dt toggle + 4-panel chart grid.
  - **BikesPage** — paginated search/filter table, 40 bikes per page.
  - **BuildPage** — bike + parts catalog composer with Map-keyed selection so filter changes don't drop parts; re-runs `/api/simulate/quick` on every toggle; build cost in ₹ + stock-vs-modded ET delta chip.
  - **ComparePage** (Apr 23, 2026) — *NEW*. Two bike pickers, shared venue + conditions, Run Compare button; side-by-side ET/trap/60ft/1-8-mile tiles with A-vs-B delta banner (winner pill + ΔET/ΔTrap/ΔCost strip); overlay v(t) chart that resamples both timeseries onto a common 160-point grid via linear interpolation. Uses `/api/simulate/compare`.
  - **HistoryPage** (Apr 23, 2026) — fleshed out from the Apr 22 stub. Live leaderboard table from `/api/leaderboard` with trophy badge on the fastest run, formatted timestamps, handles loading / error / empty states cleanly. Shows total-runs count in header when populated.
  - **SettingsPage** — read-only runtime info panel (backend URL, DB location, physics engine version + validated baselines, app version).
- [x] **Sidecar packaging scaffold** (Apr 23, 2026) — *NEW*. `desktop/sidecar/` with:
  - `sidecar_entry.py` — uvicorn launcher that auto-resolves the bundled DB via `sys._MEIPASS` at startup and sets `MOTOQUANT_DB` before importing `motoquant.api`, so no Tauri-side env plumbing is required.
  - `motoquant-backend.spec` — PyInstaller one-file spec with tight `excludes` list (matplotlib/torch/tensorflow/sklearn/xgboost/SALib/streamlit) to keep binary size down since those are only used by offline training/analysis flows. `datas` bundles `motoquant.db`. Collects all `motoquant.*` + `uvicorn.*` submodules as `hiddenimports`.
  - `build.sh` (Linux/macOS) + `build.ps1` (Windows) — venv bootstrap + dep install + clean build + smoke test that spawns the binary on an ephemeral port and hits `/api/health`.
  - `requirements-sidecar.txt` — runtime deps pinned in sync with `requirements-api.txt` plus `pyinstaller>=6.5.0`.
  - `README.md` — cross-platform build flow, target-triple naming table (what to rename to before dropping into `desktop/src-tauri/bin/`), DB-bundling trade-offs, dev-mode override guide, troubleshooting table.
- [x] **Build validation** — `npx tsc --noEmit` passes cleanly across all 17 TS/TSX files. Vite build (per Apr 22 entry) produces a 2433-module bundle at ~195 kB gzipped in 44 s.

**Phase 5 — Remaining:**
- [ ] **Actually build the PyInstaller binaries** on each target OS. Requires the Rust toolchain locally + running `desktop/sidecar/build.sh` once per target (Windows x64 / macOS arm64 / macOS x64 / Linux x64). User-driven (needs OS access + Rust installed).
- [ ] **Icon assets** — `desktop/src-tauri/icons/` is empty. Tauri needs 32×32, 128×128, 128×128@2x PNGs + `icon.icns` (macOS) + `icon.ico` (Windows). Requires graphic design (skip for now; use placeholder).
- [ ] **`cargo tauri dev` handshake confirmation** — prove the Rust spawn → Python sidecar → React `get_backend_url` loop actually works end-to-end on the host. User-driven.
- [ ] **CI sidecar-build matrix job** — add to `.github/workflows/ci.yml`: matrix of `{ubuntu-latest, windows-latest, macos-latest}` running `desktop/sidecar/build.sh|ps1`, uploading the binaries as workflow artifacts. Ties release builds to CI so shipping is `git tag` + download artifacts.
- [ ] **Live surrogate-model preview in BuildPage sliders** — see Phase 4 remaining (needs the `/api/surrogate/predict` route first).
- [ ] **3D bike visualisation** (Three.js) — nice-to-have.
- [ ] **PDF report export** — from a completed sim, render a 1-pager with ET/trap/splits/build/charts.
- [ ] **Closed beta with Pune/Narhe tuning garages** — validates the predictions against professional tuners before public release. User-driven outreach.

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
