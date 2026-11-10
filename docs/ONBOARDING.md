# MotoQuant — Contributor Onboarding

Welcome to the project — MotoQuant is open source under the [MIT license](../LICENSE). This doc is the "day one" brief — read it end-to-end, then you should have enough context to pick up work without 20 rounds of back-and-forth.

**Read order on day one:**
1. This file (10 min).
2. `docs/ARCHITECTURE.md` — the module map + data-flow diagram. Answers "where does X live, and how does a bike spec become a simulated ET?" before you open any code (10 min).
3. `CLAUDE.md` — the live status document, single source of truth for project state. It is a long single-paragraph changelog: read the **top** entry for the latest session and skim the trailing evergreen sections (architecture, workflow, physics reference). Don't try to read it end-to-end (20 min).
4. `CONTRIBUTING.md` — dev workflow, branch conventions, Kaizen rule (10 min).
5. `docs/ROADMAP.md` — the live prioritized backlog + the operator-only actions (10 min).
   *(`reports/ROADMAP_2026_07_03.md` is a dated snapshot, kept as history only —
   sessions have repeatedly re-scoped already-finished work out of it.)*
6. Skim `motoquant/physics.py`, one sub-model like `motoquant/submodels/tire.py`, and `docs/CHAT_AGENT.md` to get a feel for the code style and the newest subsystem (15 min).

After that, get the test suite green locally (see `CONTRIBUTING.md` §2) and you're ready to open your first PR.

---

## 1. What MotoQuant is (in one paragraph)

A first-principles physics engine for predicting and optimising motorcycle quarter-mile drag racing times, aimed first at the Indian drag racing community (Aamby Valley, MMRT, BIC, Kari, Hyderabad) and now expanding to the international market (US/EU/JP/CN drag scenes). It's a Python package with a CLI, a FastAPI backend (live on Render), a Next.js web frontend (live at motoquant.in), and an agentic AI chat that can run the whole product (sims, comparisons, the build optimizer, outlaw-class builds, web lookup, estimated sims for unknown bikes). Under the hood: 15 physics sub-models integrated with RK4 at 1 ms, validated against 250 published benchmarks — weighted mean |Δ| ≈ 0.26 s corpus-wide, ±0.007 s across the 10 cleanest validated runs. The whole product is free and open source (see `docs/adr/0006-open-source-mit.md`); optional accounts exist only to save runs.

**Tagline:** *"The physics of faster."*

---

## 2. Current state snapshot (July 2026)

| Metric | Value |
|---|---|
| Status | Free and open source (MIT); hosted at motoquant.in, no paid tiers or quota |
| Tests | full pytest suite green (runs ~25–35 min; focused subsets in `CONTRIBUTING.md` §4) |
| Bikes in catalog | 534 across 30+ manufacturers (India, SE Asia, US, EU, JP, CN) |
| Tires | 254 (incl. drag radials/slicks + cruiser rubber), 1,765 fitments |
| Parts | 546 across 19 categories (incl. lowering kits, air shifters, lockup clutches) |
| Venues | 20 (India + international drag strips) |
| Benchmarks | 250 ET rows + 86 top-speed rows; weighted sweep 273 matched, |Δ| 0.262 s, bias +0.009 s |
| Reference baselines | K5 9.9331 / R1 10.1436 / Hayabusa 10.3633 — pinned **bit-identical**, CI-gated |
| Chat AI | multi-step tool-calling agent (`motoquant/llm/agent.py`, `docs/CHAT_AGENT.md`) |
| Deployed | API: Render free tier (`motoquant-api.onrender.com`); web: Vercel (`motoquant.in`) — both auto-deploy from `main` |

The code is not the bottleneck. The main open items are production DB durability (a Render persistent disk — maintainer action) and data (instrumented Dragy timeslips for small-cc bikes). See `docs/ROADMAP.md`.

---

## 3. What's live vs. what's pending

### Live and working
- CLI (`python -m motoquant.run --help`) — db/bikes/sim/venues/tires/parts/weather/import/analysis/chat and more.
- FastAPI backend: sims (quick/full/top-speed/compare), jobs API with real progress + cancel, build optimizer (surrogate-accelerated knapsack), ECU autotune, the composed outlaw pipeline, agentic chat (`/api/chat`, `/api/jobs/chat`), optional accounts (saved runs), Dragy/dyno/ECU calibration uploads, leaderboard, shareable timeslips.
- Next.js web app: cockpit-themed landing + simulator workbench + optimizer/autotune pages + transcript chat UI + docs/blog.
- Tauri desktop app: DISCONTINUED (July 2026) — the hosted web app is the product. The `desktop/` scaffold remains in-tree for reference; no binaries will be built.
- Physics: 15 sub-models, adaptive RK4, calibration pipeline, numpy surrogate v2.7 (regenerate after ANY physics/DB reseed — standing contract in `artifacts/surrogate/README.md`).

### Pending / known gaps (the honest list)
- Prod DB durability: SQLite is baked into the Docker image; every deploy wipes user accounts/saved runs until the Render persistent-disk flip (maintainer, ~$7/mo).
- Small-cc is the weakest class: partly data-limited (needs real Dragy timeslips), partly a known gearing limitation (generic primary ratios; see `reports/session_2026_11_10_epoch.md`).
- Epoch-gated physics work (do NOT wire casually — moves the pinned baselines): Pacejka slip model, 4-branch clutch dispatch, staging rollout/dead-time. See the July 3 session report.
- Full backlog: `docs/ROADMAP.md`.

---

## 4. Good first issues (pick one to start)

Ranked by isolation (least cross-cutting first). All of these are in `docs/ROADMAP.md` with more detail.

### A. Catalog data passes (data work — hours, high value)
Add well-sourced bikes/parts/tires following the July-2026 pattern: sibling spec modules (`motoquant/scraper/known_bikes_2026_*.py`) with cited sources, explicit gear cassettes, individual aero values, and instrumented benchmark rows where they exist. The project rule is absolute: **no fabricated specs, prices, or benchmarks — skip and document instead**. Open targets: vintage-2T OEM tire fitments, sub-500cc drag hardware (needs real products), pricing follow-ups.

### B. Instrumented benchmark rows (data — hours)
Add Dragy / VBox / Racelogic stock-bike timeslips with a citable source to the benchmark corpus. This is the single most valuable contribution for small-cc accuracy.

### C. Web PDF timeslip/build export (web — 1–2 days)
A one-pager with ET/trap/splits/build/charts, extending the print-friendly `/r/[id]` timeslip page.

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

- **Discussion:** async, via GitHub Issues and Discussions.
- **Planning:** backlog lives in `docs/ROADMAP.md`.
- **Reviews:** all PRs need green CI + one approving review; CODEOWNER approval auto-requested on physics/schema/API/infra paths; no self-merge. Turnaround target 48 h.
- **AI assistants:** much of this codebase is built by Claude sessions operating under `CLAUDE.md`'s rules. If you use AI tooling, hold it to the same gates (baselines, Kaizen, no-fabrication) — the rules exist because each one was broken once and cost real time.

---

## 7. People and credentials

| Role | Owner | Notes |
|---|---|---|
| Project lead / founder | Hritwik Mudhai (dhisetu@gmail.com) | Original author, primary account holder |
| Co-founder | Ritwik Singh | See about page |
| Contributors | *(you)* | Fork, branch, PR — no hosting access needed |

Hosting and provider credentials (Render, Vercel, the `motoquant.in` registrar, LLM provider keys, OpenWeatherMap) are held by the maintainers and are never committed. You do not need any of them to develop or test.

---

## 8. How to ask for help

1. `grep -i <keyword> CLAUDE.md` — most "is this implemented?" questions are answered there.
2. `python -m motoquant.run --help`, then `<subcommand> --help`.
3. Read the test file for the module you're touching — tests are the executable spec.
4. Open a GitHub Issue (preferred over DMs — searchable later).

---

## 9. First-week checklist

- [ ] Fork or clone the repo (https://github.com/toto171/MotoQuant.in) and create a branch.
- [ ] Get the test suite green locally (`CONTRIBUTING.md` §2 — use the focused subset first, the full run takes ~30 min).
- [ ] Run a sim: `python -m motoquant.run sim --bike-id 1 --venue-id 1` → ≈ 10.04 s for the K5 on the shipped `motoquant.db` (bike id 1 at venue 1; the pinned sea-level reference is 9.9331 s via `motoquant.gsxr1000_k5()`). A fresh `db init` + `db seed` database also has the K5 as id 1 but only the three reference bikes — use the shipped DB.
- [ ] Boot the API (`uvicorn motoquant.api:app --reload`) and the web app (`cd web && npm install && npm run dev`), click through the simulator and the chat.
- [ ] Read `CLAUDE.md`'s latest session entry + the trailing evergreen sections.
- [ ] Pick one §4 good-first-issue, scope it as a GitHub Issue, then ship a PR — however small. Proving the workflow end-to-end on day one beats a big first contribution.

Welcome aboard.
