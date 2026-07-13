# MotoQuant Pro — Co-Developer Onboarding

Welcome to the project. This doc is the "day one" brief — read it end-to-end, then you should have enough context to pick up work without 20 rounds of back-and-forth.

**Read order on day one:**
1. This file (10 min).
2. `docs/ARCHITECTURE.md` — the module map + data-flow diagram. Answers "where does X live, and how does a bike spec become a simulated ET?" before you open any code (10 min).
3. `CLAUDE.md` — the live status document, single source of truth for project state. It is a long single-paragraph changelog: read the **top** entry for the latest session and skim the trailing evergreen sections (architecture, workflow, physics reference). Don't try to read it end-to-end (20 min).
4. `CONTRIBUTING.md` — dev workflow, branch conventions, Kaizen rule (10 min).
5. `reports/ROADMAP_2026_07_03.md` — the complete prioritized backlog + the list of operator-only actions (10 min).
6. Skim `motoquant/physics.py`, one sub-model like `motoquant/submodels/tire.py`, and `docs/CHAT_AGENT.md` to get a feel for the code style and the newest subsystem (15 min).

After that, get the test suite green locally (see `CONTRIBUTING.md` §2) and you're ready to open your first PR.

---

## 1. What MotoQuant is (in one paragraph)

A first-principles physics engine for predicting and optimising motorcycle quarter-mile drag racing times, aimed first at the Indian drag racing community (Aamby Valley, MMRT, BIC, Kari, Hyderabad) and now expanding to the international market (US/EU/JP/CN drag scenes). It's a Python package with a CLI, a FastAPI backend (live on Render), a Next.js web frontend (live at motoquant.in), and an agentic AI chat that can run the whole product (sims, comparisons, the build optimizer, outlaw-class builds, web lookup, estimated sims for unknown bikes). Under the hood: 15 physics sub-models integrated with RK4 at 1 ms, validated against 221 published benchmarks — weighted mean |Δ| ≈ 0.22 s corpus-wide, ±0.006 s across the 10 cleanest validated runs. Commercial plan: B2C freemium + B2B Pro Studio, currently in open beta — see `docs/COMMERCIAL_LAUNCH.md`.

**Tagline:** *"The physics of faster."*

---

## 2. Current state snapshot (July 2026)

| Metric | Value |
|---|---|
| Phase | 6 (commercial launch) — open beta live; payments code-complete, providers not yet configured |
| Tests | full pytest suite green (runs ~25–35 min; focused subsets in `CONTRIBUTING.md` §4) |
| Bikes in catalog | 541 across 30+ manufacturers (India, SE Asia, US, EU, JP, CN) |
| Tires | 254 (incl. drag radials/slicks + cruiser rubber), 1,860 fitments |
| Parts | 593 across 19 categories (incl. lowering kits, air shifters, lockup clutches) |
| Venues | 20 (India + international drag strips) |
| Benchmarks | 221 ET rows + 74 top-speed rows; weighted sweep 246 matched, |Δ| 0.217 s, bias +0.021 s |
| Reference baselines | K5 9.9331 / R1 10.1436 / Hayabusa 10.3633 — pinned **bit-identical**, CI-gated |
| Chat AI | multi-step tool-calling agent (`motoquant/llm/agent.py`, `docs/CHAT_AGENT.md`) |
| Deployed | API: Render free tier (`motoquant-api.onrender.com`); web: Vercel (`motoquant.in`) — both auto-deploy from `main` |

The code is not the bottleneck. Revenue-launch blockers are operator actions (Render persistent disk, payment-provider setup) and data (instrumented Dragy timeslips for small-cc bikes). See `reports/ROADMAP_2026_07_03.md` §B.

---

## 3. What's live vs. what's pending

### Live and working
- CLI (`python -m motoquant.run --help`) — db/bikes/sim/venues/tires/parts/weather/import/analysis/chat and more.
- FastAPI backend: sims (quick/full/top-speed/compare), jobs API with real progress + cancel, build optimizer (surrogate-accelerated knapsack), ECU autotune, the composed outlaw pipeline, agentic chat (`/api/chat`, `/api/jobs/chat`), auth + subscriptions (beta mode), Dragy/dyno/ECU calibration uploads, leaderboard, shareable timeslips.
- Next.js web app: cockpit-themed landing + simulator workbench + optimizer/autotune pages + transcript chat UI + docs/blog/pricing.
- Tauri desktop app: DISCONTINUED (July 2026) — the hosted web app is the product. The `desktop/` scaffold remains in-tree for reference; no binaries will be built.
- Physics: 15 sub-models, adaptive RK4, calibration pipeline, numpy surrogate v2.2 (regenerate after ANY physics/DB reseed — standing contract in `artifacts/surrogate/README.md`).

### Pending / known gaps (the honest list)
- Payments: code-complete, providers unconfigured (`docs/PAYMENTS_SETUP.md` — operator).
- Prod DB durability: SQLite is baked into the Docker image; every deploy wipes user accounts until the Render persistent-disk flip (operator, ~$7/mo).
- Small-cc accuracy floor is data-limited, not model-limited — needs real Dragy timeslips.
- Epoch-gated physics work (do NOT wire casually — moves the pinned baselines): Pacejka slip model, 4-branch clutch dispatch, staging rollout/dead-time. See the July 3 session report.
- Full backlog: `reports/ROADMAP_2026_07_03.md`.

---

## 4. Good first issues (pick one to start)

Ranked by isolation (least cross-cutting first). All of these are in `reports/ROADMAP_2026_07_03.md` with more detail.

### A. Catalog data passes (data work — hours, high value)
Add well-sourced bikes/parts/tires following the July-2026 pattern: sibling spec modules (`motoquant/scraper/known_bikes_2026_*.py`) with cited sources, explicit gear cassettes, individual aero values, and instrumented benchmark rows where they exist. The project rule is absolute: **no fabricated specs, prices, or benchmarks — skip and document instead**. Open targets: vintage-2T OEM tire fitments, sub-500cc drag hardware (needs real products), pricing follow-ups.

### B. License-key device unbind route (backend — half a day)
Device binding is enforced but there's no way for a user who reinstalls to unbind — they're locked out until manual DB surgery. Authenticated unbind endpoint + account-page UI + tests.

### C. Web PDF timeslip/build export (web — 1–2 days)
Port the desktop jsPDF export to the web app as a Pro-tier feature: a one-pager with ET/trap/splits/build/charts.

### D. Chat-agent polish (LLM layer — scoped pieces)
The agent shipped July 3 (`motoquant/llm/agent.py`). Scoped follow-ups: resolver letter/digit tokenization ("ZX10R" → weak match), a `mode=agent` path for the CLI `chat` subcommand, streaming responses. Everything is offline-testable via the `_call_override` seam — see `tests/test_agent.py` for the pattern.

### E. Test-coverage signal in CI (tooling — half a day)
~3k tests but no branch-coverage truth. Add coverage.py + a CI artifact so "which physics branches are exercised" has an answer.

---

## 5. Non-negotiable conventions

These will cause a PR to be rejected even if the code works.

1. **Package is `motoquant`, never `dragsim`.** The 2026 rename is final.
2. **SQLite stays until Phase 6 cloud sync is genuinely needed.** The WAL-fallback in `motoquant/database/connection.py` is load-bearing.
3. **CLI tests call handlers directly, not subprocesses.** See `tests/test_cli.py`.
4. **Scraper is stdlib-only.** No BeautifulSoup/lxml.
5. **Physics baselines are pinned bit-identical**: K5 9.9331 / R1 10.1436 / Hayabusa 10.3633. If you touch `physics.py`, `submodels/*`, `defaults.py`, or the importer, run the baseline check + `tests/test_regression_snapshot.py` and put the deltas in your PR (template has the table). "±0.0000 at 4 decimals" is the expectation; anything else needs a full weighted-sweep justification.
6. **After any `spec_to_bike_config` change, reseed the DB** (`scripts/reseed_configs_from_specs.py`) — otherwise `/api/simulate?bike_id=N` silently diverges from the spec path. Then regenerate the surrogate (standing contract).
7. **After any catalog change, run `python scripts/audit_headline_stats.py --fix`** — the site's stat tiles/OG cards must match the DB.
8. **Never `git add -A`.** Stage explicit file lists; the tree often carries unrelated WIP.
9. **No fabricated data.** Honest gaps beat apparent completeness — this is written into multiple session postmortems.
10. **Kaizen scan before every commit** (`CLAUDE.md` → Kaizen Principle) and **update `CLAUDE.md` after substantive work** (surgical prepend of a session entry — never rewrite the file).

---

## 6. Project rhythms

- **Standup:** informal, async via GitHub Issues or DM.
- **Planning:** backlog lives in `reports/ROADMAP_2026_07_03.md`; roadmap phases in `CLAUDE.md`.
- **Reviews:** all PRs need green CI + one approving review; CODEOWNER approval auto-requested on physics/schema/API/infra paths; no self-merge. Turnaround target 48 h.
- **AI assistants:** much of this codebase is built by Claude sessions operating under `CLAUDE.md`'s rules. If you use AI tooling, hold it to the same gates (baselines, Kaizen, no-fabrication) — the rules exist because each one was broken once and cost real time.

---

## 7. People and credentials

| Role | Owner | Notes |
|---|---|---|
| Project lead / founder | Hritwik Mudhai (dhisetu@gmail.com) | Original author, primary account holder |
| Co-founder | Ritwik Singh | See about page |
| Co-developer | *(you — fill in)* | Coordinate on deployment credentials |

Shared credentials (never committed): Render (API hosting), Vercel (frontend), domain registrar (`motoquant.in`), LLM provider keys (Groq/Gemini — chat), OpenWeatherMap. Ask the project lead; when a second seat is needed on any platform, open an Issue.

---

## 8. How to ask for help

1. `grep -i <keyword> CLAUDE.md` — most "is this implemented?" questions are answered there.
2. `python -m motoquant.run --help`, then `<subcommand> --help`.
3. Read the test file for the module you're touching — tests are the executable spec.
4. Open a GitHub Issue (preferred over DMs — searchable later).

---

## 9. First-week checklist

- [ ] Accept the GitHub collaborator invite; clone; push a test branch to confirm write access.
- [ ] Get the test suite green locally (`CONTRIBUTING.md` §2 — use the focused subset first, the full run takes ~30 min).
- [ ] Run a sim: `python -m motoquant.run sim --bike-id 1 --venue-id 1` → ≈ 10.03 s for the K5.
- [ ] Boot the API (`uvicorn motoquant.api:app --reload`) and the web app (`cd web && npm install && npm run dev`), click through the simulator and the chat.
- [ ] Read `CLAUDE.md`'s latest session entry + the trailing evergreen sections.
- [ ] Pick one §4 good-first-issue, scope it as a GitHub Issue, then ship a PR — however small. Proving the workflow end-to-end on day one beats a big first contribution.

Welcome aboard.
