# MotoQuant — Useful Skills, Repos & Tooling

A curated, opinionated list. Each item has a one-line **"why for MotoQuant"** so you can filter fast.

> **Status legend (project-specific filtering — see CLAUDE.md "TOOLKIT REFERENCE" section for the canonical version):**
> - **✓** = already in the codebase
> - **★** = adopt this quarter
> - **◇** = adopt later (Phase 6 / scale gate)
> - **✗** = explicitly rejected for MotoQuant
> - *unmarked* = good to know about, no decision yet

Project context: first-principles 1/4-mile motorcycle solver, Bayesian build opt, Dragy GPS calibration, dyno + ECU log ingest, FastAPI backend, 334-bike validation set, Tauri/React desktop, Next.js web on `motoquant.in`, Indian market focus.

---

## 1. Vehicle dynamics & tire physics (your core)

There's no existing "motorcycle drag-race solver" library — that's why MotoQuant exists. But the building blocks are mostly solved problems.

- **✓ OpenTire / OpenTirePython** — `OpenTire/OpenTirePython`. Reference Python implementation of the Pacejka 2002 Magic Formula. **Already implemented**: full B/C/D/E + thermal coefficients across 232 tires in MotoQuant. OpenTirePython kept as a *reference*, not a runtime dependency.
- **EricCabrol/VehicleDynamics** — Jupyter notebooks that walk through Pacejka from the original 1987 SAE 870421 paper. Use for understanding parameter intent before tuning coefficients for sport-bike rear tires.
- **JyNing04/Pacejka-tire-model** — A `.TIR` file parser. Useful if FSAE TTC-style tire test data ever shows up, or if MotoQuant publishes bike tire profiles in a standard format.
- **andresmendes/Vehicle-Dynamics-Lateral** (MATLAB/Octave) — Reference for the equations even without MATLAB. The longitudinal weight-transfer derivation is exactly what's needed for wheelie-limited launch.

**Domain references that beat any library** (the actual moat):
- Vittore Cossalter, *Motorcycle Dynamics* — the canonical text. Wheelie limit, tire normal force under acceleration, chain force on the swingarm, anti-squat geometry. If MotoQuant claims first-principles, this book has to be on the desk.
- Tony Foale, *Motorcycle Handling and Chassis Design* — practical complement to Cossalter.
- Hans Pacejka, *Tire and Vehicle Dynamics* — the Magic Formula bible.

## 2. Engine / powertrain modeling

- **✗ Cantera** — `Cantera/cantera`. Open-source thermodynamics + chemical kinetics. Combustion-kinetics overkill; empirical torque maps + dyno injection cover the use case end-to-end. *Discarded for MotoQuant.*
- **engine-sim** — AngeTheGreat's real-time ICE simulator. **Do not use for physics** (the README explicitly says it's not engineering-grade), but the **interaction model** — sliders, real-time response, audio feedback — is a great UX reference for what an "engine builder" interface can feel like. Steal the vibe, not the numbers.
- **Heywood, *Internal Combustion Engine Fundamentals*** — the reference. Two-zone combustion, friction MEP, scavenging for two-strokes if MotoQuant goes there (already partially does for RD350 / NSR250R class).
- **✓ SAE J1349 / DIN 70020 / ISO 1585** — dyno correction standards. **Already implemented** in `motoquant/calibration/dyno.py` (SAE J1349 only). Critical for normalizing user dyno uploads (Dynojet defaults to STP, others use SAE).

## 3. Bayesian build optimization

This is your differentiator and you should not roll your own optimizer.

- **✓ BoTorch** — `pytorch/botorch`. Meta's gradient-based BO library. **Already wired** into `motoquant/analysis/bayesian_opt.py` (Phase 4). Best-in-class for continuous + mixed search spaces.
- **◇ Ax** — `facebook/Ax`. Wraps BoTorch with experiment tracking, multi-objective handling, and constraints. Adopt when "optimize for ET subject to budget ≤ ₹X and street-legal=true" becomes a product feature.
- **★ Optuna** — `optuna/optuna`. Simpler API, great pruning, works well when sweeps are cheap. **Adopt this quarter** for offline tuning of the per-cluster `CategoryProfile` knobs in `motoquant/category_profiles.py` against the weighted-benchmark cost function. Faster iteration than the manual 1.00→0.65 parasitic-mult tweaks done by hand on April 30.
- **scikit-optimize** — older, simpler, fine for a v0. Optuna supersedes for new work.

## 4. Telemetry & log ingest (Dragy, dyno, ECU)

This is where most engineering time will go and where there's the least off-the-shelf help.

- **✗ asammdf** — `danielhrisca/asammdf`. The Python library for MDF/MF4 (Vector measurement files). Pro-team CAN bus is too far out for the Indian drag scene; revisit only on a B2B Pro Studio request.
- **✗ cantools** — `cantools/cantools`. DBC file parsing, CAN message decoding. Same reasoning as asammdf — defer until pro-team data shows up.
- **✗ python-can** — `hardbyte/python-can`. CAN bus interface library. Defer until pro-team data.
- **gpxpy** — `tkrajina/gpxpy`. GPX parser, in case generic GPS exports need to be accepted alongside Dragy CSVs. Low priority.
- **Dragy file format** — there's no library; just CSV with header metadata. **Already implemented** in `motoquant/calibration/dragy.py` (CSV imperial mph/ft + metric km/h/m, JSON Dragy app exports, run-boundary detection). Same custom-parser story for Dynojet, Mainline, Power Commander, Bazzaz, Woolich, FTECU — all in `motoquant/calibration/`.

**Already executed:** the `LogIngest` adapter pattern recommended in the original toolkit lives in `motoquant/calibration/` — Dragy / Dyno / ECU each normalise to a common `Run`-shape via `DragRunData` / `DynoResult` / `ECULog` dataclasses.

## 5. Signal processing (GPS + dyno smoothing)

- **★ filterpy** — `rlabbe/filterpy`. Kalman filters, IMM, particle filters. Dragy GPS is noisy enough that a Kalman pass before differentiation gives much cleaner ET / trap speed estimates. **Adopt this quarter, gated behind real Dragy upload volume** — once users start submitting timeslips, GPS noise smoothing meaningfully improves the calibrator's signal-to-noise. Roger Labbe's free Kalman book is the best intro on the internet.
- **✓ scipy.signal** — Already in the stack. Savitzky–Golay for dyno curve smoothing without losing peaks. Use SG over moving averages for power curves; the peak preservation matters.
- **pyproj** — `pyproj4/pyproj`. Geodetic transforms (lat/lon → local ENU). Necessary because integrating velocity from raw GPS without proper projection introduces meters of drift over a quarter mile. Adopt alongside filterpy.
- **★ NumPy + Numba** — for the inner solver loop. **Adopt this quarter.** JIT-compiled time stepping is 50–100× pure Python and lets the 334-bike validation suite run in seconds instead of the current ~30 s/chunk. Highest perf-per-line-of-code change in the codebase.

## 6. API & backend

You're on FastAPI — good choice for this. Adjacent picks:

- **✓ Pydantic v2** — already in via FastAPI. v2 is ~5× faster than v1.
- **◇ Polars over pandas** — only if pandas shows up in the hot path. Currently it doesn't (sweep is pure numpy).
- **SQLModel** or **SQLAlchemy 2.0 (typed)** — for storing runs, builds, leaderboard entries. Currently raw SQLite via the `motoquant/database/` repos. Worth a layer before Phase 6 PostgreSQL migration.
- **✗ Litestar** — alternative to FastAPI worth knowing, slightly faster and better DI. **Not worth migrating to** — no measured perf bottleneck in the FastAPI surface.
- **◇ Logfire** — `pydantic/logfire`. Observability from the Pydantic team, drops into FastAPI in two lines, much nicer DX than raw OpenTelemetry. Free tier is generous. Adopt after Sentry — Sentry catches errors, Logfire traces requests; both have value at different scales.

## 7. Validation infrastructure (your moat)

You market "validated against published 1/4 mile times." That claim is only as strong as your regression suite. Spend here.

- **★ pytest-regressions** — golden-file testing. **Highest ROI item on this list.** Snapshot the ET prediction for each of the 334 bikes; any solver change that drifts a result triggers CI. The K5/R1/Hayabusa baselines (preserved exactly to 4 decimals across every session) are already de-facto golden files; formalising them stops physics drift in CI rather than at the next manual sweep. **Adopt this quarter.**
- **★ Hypothesis** — `HypothesisWorks/hypothesis`. Property-based testing. Use for invariants like "ET monotonically decreases as power increases, holding everything else constant," "wheelie limit reduces with longer wheelbase," "Cd reduction lowers ET by a non-zero amount." **Adopt this quarter** — would have caught the April 24 AM `power_boost_pct` dead-knob regression on the small-cc spec path before it hit the validation sweep.
- **◇ DVC** — `iterative/dvc`. Version control for the bike spec dataset and validation reference data. Worth it once benchmark counts cross 200+ and "v1.4.2 was validated against bike-set@a3f9c2" reproducibility matters.
- **pandera** — pandas/Polars schema validation. Use on every log ingest path so bad uploads fail fast with clear errors instead of producing nonsense ETs. Low priority until pandas/polars enters the hot path.
- **A public "validation report" page** — not a tool, a feature. The current `motoquant.in` landing page partially has this (top-10 table, cluster bias chips). Should auto-generate from the test suite, with error bars. This is the trust artifact for tuning shops considering the API.

## 8. Frontend (slider-heavy UI, leaderboards)

- **✓ Tailwind** — already in desktop and web.
- **◇ shadcn/ui** — drop-in components on top of Tailwind. Desktop is on plain Tailwind; shadcn would speed up the remaining HistoryPage / SettingsPage surfaces. Low urgency.
- **Plotly.js** or **Observable Plot** — for dyno curves and run traces. Plot is more elegant; Plotly is more battle-tested for interactive zoom/pan. Currently using Recharts in desktop — fine for now.
- **✓ TanStack Query** — already wired in desktop (`hooks/useApi.ts`). Mandatory if the UI does live re-runs as sliders move.
- **D3 for one custom thing** — the time-vs-distance run trace with shift markers. D3 is overkill for charts but right for one-of-a-kind visualizations.
- **★ anime.js** — `juliangarnier/anime`. Lightweight (~17 KB) JS animation library — CSS, SVG, DOM attrs, and JS object tweening with one consistent API. **Adopt this quarter** for: (a) landing-page hero on `motoquant.in` (the current static stats strip is the weakest visual on the page); (b) SimulatorWidget result-reveal — counting up ET / trap / 60-foot from 0 to final value as the run "completes" reads as physics actually happening rather than a number popping in; (c) BuildPage stock-vs-modded delta chip on desktop — animate the ET delta number when parts toggle so the cause-and-effect is visible at a glance; (d) shift-marker entrance on the v-vs-t run trace. Pairs well with Recharts (chart geometry) + anime.js (entrance + counter animations) — they don't conflict. Avoid using it for the chart axes themselves; that's Recharts' job.

## 9. Observability & product analytics

- **★ Sentry** — error tracking. Free tier is fine for current scale. **Adopt this quarter** on Railway + Vercel — catches the 500s and edge errors silently happening in production right now (the FastAPI ↔ Next.js rewrite chain is one fragile dependency).
- **◇ PostHog** — `PostHog/posthog`. Product analytics with a free self-host and a generous cloud free tier. Useful for understanding which sliders riders actually move and where they drop off — drives roadmap. Wait for paid users before instrumenting.
- **◇ Logfire** (mentioned above) — covers tracing.
- **★ Vercel Speed Insights / Lighthouse CI** — Core Web Vitals tracking on `motoquant.in`. SEO and conversion both depend on this; Vercel's built-in is already free. Adopt this quarter, zero effort.

## 10. Claude / Anthropic-specific tooling

This is the section the original question was really about.

- **★ `anthropics/skills` (official)** — start here, not with random community skills. Already using `docx/pdf/xlsx/pptx` for customer-facing reports. Other relevant ones:
  - `frontend-design` — actively counters the generic AI look in artifacts and UI work. Useful when Claude prototypes UI.
  - `mcp-builder` — for exposing MotoQuant as an MCP server (so Claude/ChatGPT/Cursor can call the solver directly). See below for why this is high-leverage.
  - `skill-creator` — for building the MotoQuant-specific skill (see below).
- **`anthropics/claude-cookbooks`** — recipes for prompt caching, tool use, batch processing. The batch API is genuinely useful for running solver explanations across many builds cheaply.
- **★ Build your own MotoQuant skill** — a `motoquant.skill` that teaches Claude the solver's API surface, the bike spec schema, and the terminology (60-foot, MPH, ET, trap, two-step, anti-squat, slipper clutch, expansion chamber, anti-anti-squat). **Adopt this quarter** — way more leverage than any general AI dev assistant; gives any Claude session instant fluency in the domain. Lives at `skills/motoquant.skill/`.
- **★ Expose MotoQuant as an MCP server** — `api.motoquant.in` already has an OpenAPI spec at `/docs`. Wrapping it as MCP is a weekend project and immediately makes MotoQuant part of the Claude / Cursor / Cowork ecosystem. **Distribution channel + free marketing.** "Ask Claude what 16/45 vs 16/47 does to your 60-foot" is a marketing demo that writes itself.

---

## Project-specific additions (not in the original toolkit)

These are MotoQuant-specific tooling decisions that fell out of the project audit.

### Adopt this quarter (★)
- **ruff + uv** — modern Python lint/format and package manager. Drop-in replacements for black/flake8/isort/pip; both ~10–100× faster. Free perf with no behavioural change. Adopt alongside the pytest-regressions work.
- **Playwright** — end-to-end browser tests against `motoquant.in`. Catches the class of regression where the FastAPI ↔ Next.js rewrite chain breaks silently (the April 28 chat panel deploy was a near miss).

### Adopt later (◇)
- **Razorpay test mode + webhook simulator** — required gating for the Phase 6 subscription launch. Currently unblocked-but-untested per the S5 carry-forward list.
- **k6 / Locust** — load-test the FastAPI surface before public launch. Railway's free-tier instance degrades quickly under concurrent surrogate calls.
- **Codecov (or coverage.py + GitHub Actions artifact)** — currently no test-coverage signal in CI; the 739+ test count is impressive but says nothing about which physics branches are actually exercised.
- **Alembic** — needed for the SQLite → PostgreSQL migration if/when Phase 6 cloud sync goes live.

---

## What NOT to bother with (✗)

- **The llm-council pattern** — agreed with original toolkit author; the API spend and workflow drag are not justified for a physics-heavy product where the right answer is usually deterministic.
- **Generic "AI dev assistant" plugins** — most of them are prompt wrappers. Build your own MotoQuant skill instead.
- **MATLAB-only tire toolboxes (mfeval, etc.)** — useful as references, but don't introduce a MATLAB dependency into a Python stack.
- **Heavyweight CFD (OpenFOAM, SU2)** — drag coefficient is a 1-DOF lookup for a motorcycle in tucked position. Don't build a wind tunnel; user-measured Dragy data closes the gap better than any wind-tunnel sim.
- **Custom database — use Postgres** — no NoSQL adventure. Runs, builds, bikes, parts, users — all relational. Postgres + JSONB columns for variable telemetry payloads (Phase 6 migration).
- **Cantera, asammdf, cantools, python-can, Litestar, engine-sim (for physics)** — see individual entries above.

---

## Suggested order of attack (project-specific)

1. **★ pytest-regressions over the 334-bike sweep** — formalise the implicit baseline contract. Highest ROI; protects every future physics change.
2. **★ Numba JIT on the RK4 loop** — collapses sweep wall-time so #1's CI run is cheap.
3. **★ Optuna over `CategoryProfile`** — automate the per-cluster tuning loop that's currently manual.
4. **★ Sentry on Railway + Vercel** — catch the 500s and edge errors silently happening in production right now.
5. **★ Ship the MCP server** wrapping `api.motoquant.in`. Distribution channel + free marketing in the AI dev ecosystem. Weekend project.
6. **★ Write a MotoQuant skill** (`motoquant.skill`) using the official `skill-creator` skill. Instant Claude domain fluency for every future session.

---

*Original toolkit drafted as a strategic shortlist of libraries and references for MotoQuant. This finalised version layers project-specific filtering — see CLAUDE.md "TOOLKIT REFERENCE" section for the canonical short version with status markers.*
