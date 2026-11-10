# MotoQuant contributor onboarding

MotoQuant is free and open source (Apache-2.0), and anyone can contribute. This is the day-one brief. Read it end to end and you should have enough context to pick up work without 20 rounds of back-and-forth.

Read these on day one, in this order:

0. `AGENTS.md`: the one-page working contract (5 min).
1. This file (10 min).
2. `docs/ARCHITECTURE.md`: the module map and data-flow diagram. It answers "where does X live, and how does a bike spec become a simulated ET?" before you open any code (10 min).
3. `CHANGELOG.md`: the milestone history (read the top few entries).
4. `CONTRIBUTING.md`: dev workflow, branch conventions and the Kaizen rule (10 min).
5. `docs/ROADMAP.md`: the prioritized backlog (10 min).
6. Skim `motoquant/physics.py`, one sub-model such as `motoquant/submodels/tire.py`, and `docs/CHAT_AGENT.md` for the code style and the newest subsystem (15 min).

Then get the test suite green locally (see `CONTRIBUTING.md` §2). After that you can open your first PR.

---

## 1. What MotoQuant is

MotoQuant is a first-principles physics engine that predicts and optimises motorcycle quarter-mile drag racing times. It is aimed first at the Indian drag racing community (Aamby Valley, MMRT, BIC, Kari, Hyderabad) and is now expanding to the international drag scenes (US/EU/JP/CN). It is a Python package with a CLI, a FastAPI backend (live on Render), a Next.js web frontend (live at motoquant.in), and an AI chat agent that can run the whole product (sims, comparisons, the build optimizer, outlaw-class builds, web lookup, estimated sims for unknown bikes). The engine integrates 15 physics sub-models with RK4 at 1 ms. It is validated against a source-labelled corpus of published benchmarks; the measured accuracy is in the README and on [motoquant.in/validation](https://www.motoquant.in/validation). It is free and open source under Apache-2.0 with no paid tiers ([ADR-0006](adr/0006-open-source-pivot.md)), and you can run your own copy ([SELF_HOSTING.md](SELF_HOSTING.md)).

The tagline is *"The physics of faster."*

---

## 2. Current state (November 2026, release 2.0.0)

| Metric | Value |
|---|---|
| Status | Free & open source (Apache-2.0) since 2026-10-23. No paid tiers and no accounts |
| Tests | full pytest suite green (runs ~25–35 min; focused subsets in `CONTRIBUTING.md` §4) |
| Catalog | Bikes across 30+ manufacturers (India, SE Asia, US, EU, JP, CN), tires incl. drag radials/slicks, parts across 19 categories, 20 venues. Current counts: the README (kept in sync by `make audit`) |
| Benchmarks | Published ET and top-speed rows, each with a source label and a weight; the weighted sweep result is the newest `reports/acc_final_*.json` |
| Reference baselines | K5 10.0436 / R1 10.1092 / Hayabusa 10.1100, pinned **bit-identical**, CI-gated |
| Chat AI | multi-step tool-calling agent (`motoquant/llm/agent.py`, `docs/CHAT_AGENT.md`) |
| Deployed | API: Render free tier (`motoquant-api.onrender.com`); web: Vercel (`motoquant.in`); both auto-deploy from `main`. Self-hosting: `docs/SELF_HOSTING.md` |
| Engines | Python reference + Rust physics core, bit-identical to it; the server uses the Rust core when it is installed (`docs/RUST_CORE.md`) |
| Version | 2.0.0, one number: `motoquant.__version__` |

The main limits are data (instrumented Dragy timeslips and sourced gear ratios for small-cc bikes) and open-source logistics (repo visibility, contributor on-ramps). The code is not the bottleneck. See `docs/ROADMAP.md`.

---

## 3. What is live and what is pending

### Live
- CLI (`python -m motoquant.run --help`): db/bikes/sim/venues/tires/parts/weather/import/analysis/chat and more.
- FastAPI backend: sims (quick/full/top-speed/compare), a jobs API with real progress and cancel, the build optimizer (surrogate-accelerated knapsack), ECU autotune, the composed outlaw pipeline, agentic chat (`/api/chat`, `/api/jobs/chat`), and Dragy/dyno/ECU calibration uploads. There are no accounts: saved runs live in the browser, timeslips re-simulate the setup in their link, and the leaderboard is generated from the physics. Per-IP rate limits protect the compute-heavy routes.
- Next.js web app (design system v6, `web/DESIGN.md`): light and dark themes, a landing page built around a ten-second calculator, a simulator with Simple and Advanced modes, step-by-step Upgrades (the build optimizer) and Race-day setup (autotune) tools, the chat UI, a glossary, and docs/blog/validation explorer. Fonts are self-hosted (`web/app/fonts/`), so the build needs no network.
- The Tauri desktop app was discontinued in July 2026 and its scaffold deleted in October (ADR-0005).
- Physics: 15 sub-models, fixed and adaptive RK4, ET timed from the 1-ft stage beam, a calibration pipeline, and a numpy surrogate. The surrogate is the instant-estimate model. Regenerate it after any physics/DB reseed; the standing contract and current version are in `artifacts/surrogate/README.md`.

### Pending and known gaps
- Small bikes are the weakest class. Part of the cause is data: the class needs real Dragy timeslips. Part is the catalog: many small bikes run a generic primary gear ratio. Manufacturer gearing for 53 of them is sourced and measured, but applying it needs a re-tune of the small-bike classes first (`reports/gearing_experiment_2026_11_10.md`).
- Class bias remains on entry 200–300 cc, 300–500 cc singles and two-strokes. The spread of the three reference bikes is compressed, and two litre bikes carry millisecond-level dry-mass inversions. `reports/session_2026_11_05_handoff.md` documents all of these.
- Top speed is weaker than ET.
- Catalog bikes simulate at their stored default venue conditions, while the three reference presets run at sea level. Every result states its conditions, but the two defaults differ.
- Exact full simulations in the browser: the Rust core is compiled to WebAssembly and parity-proven, but the simulator UI still runs full sims on the server.
- Epoch-gated physics work: Pacejka slip force, 4-branch clutch dispatch, staging dead time. Do not wire these in casually; each one moves the pinned baselines.
- Full backlog: `docs/ROADMAP.md`.

---

## 4. Good first issues

These are ranked by isolation, least cross-cutting first. Each has more detail in `docs/ROADMAP.md`.

### A. Catalog data (data work, hours, high value)
Add well-sourced bikes, parts and tires following the July-2026 pattern: sibling spec modules (`motoquant/scraper/known_bikes_2026_*.py`) with cited sources, explicit gear cassettes, individual aero values, and instrumented benchmark rows where they exist. The rule has no exceptions: **no fabricated specs, prices or benchmarks; skip and document instead**. Open targets: vintage-2T OEM tire fitments, sub-500cc drag hardware (needs real products), pricing follow-ups.

### B. Benchmark submissions (data and small web/backend work)
Accuracy depends on instrumented runs, so submitting one should be easy. Tighten the `calibration_data` issue template, document the source-labelling weights (instrumented 1.0 … DERIVED 0.1) in `docs/`, and add a path for reviewed rows into the sweep corpus. Every benchmark needs a citable source; no fabricated rows.

### C. Build-sheet export (web, 1–2 days)
The shareable timeslip on `/timeslip` already prints to PDF. Extend it to a one-page build sheet with ET/trap/splits, the parts list with costs, and charts.

### D. Chat-agent follow-ups (LLM layer, scoped pieces)
The agent shipped July 3 (`motoquant/llm/agent.py`). Scoped follow-ups: resolver letter/digit tokenization ("ZX10R" → weak match), a `mode=agent` path for the CLI `chat` subcommand, and streaming responses. All of it can be tested offline through the `_call_override` seam; `tests/test_agent.py` shows the pattern.

### E. Coverage floor (tooling, half a day)
CI already uploads a coverage XML on pushes to `main` (non-blocking). Turn it into a ratchet: pick a floor for `motoquant/physics.py` + `submodels/` and fail CI if coverage drops below it.

---

## 5. Conventions that block a PR

A PR that breaks any of these is rejected, even if the code works.

1. The package is `motoquant`, never `dragsim`. The 2026 rename is final.
2. SQLite stays until a real scaling trigger ([ADR-0004](adr/0004-sqlite-until-scale.md)). The WAL fallback in `motoquant/database/connection.py` is load-bearing.
3. CLI tests call handlers directly, not subprocesses. See `tests/test_cli.py`.
4. The scraper is stdlib-only. No BeautifulSoup or lxml.
5. Physics baselines are pinned bit-identical: K5 10.0436 / R1 10.1092 / Hayabusa 10.1100. If you touch `physics.py`, `submodels/*`, `defaults.py`, or the importer, run the baseline check and `tests/test_regression_snapshot.py`, and put the deltas in your PR (the template has the table). The expectation is "±0.0000 at 4 decimals"; anything else needs a full weighted-sweep justification.
6. After any `spec_to_bike_config` change, reseed the DB (`make reseed`). Otherwise `/api/simulate?bike_id=N` silently diverges from the spec path. Then regenerate the surrogate (standing contract).
7. After any catalog change, run `python scripts/audit_headline_stats.py --fix`. The site's stat tiles and OG cards must match the DB.
8. Never `git add -A`. Stage explicit file lists, because the tree often carries unrelated WIP.
9. No fabricated data. An honest gap beats apparent completeness; several postmortems record this.
10. Run a Kaizen scan before every commit (`CONTRIBUTING.md` §7): leave every file you touch better than you found it. Put substantive write-ups in the PR description or `reports/`.

---

## 6. How the project runs

- Discussion happens in GitHub Issues (and Discussions once enabled), async by default.
- The backlog lives in `docs/ROADMAP.md`.
- Every PR needs green CI and one approving review. CODEOWNER approval is requested automatically on physics, schema, API and infra paths, and nobody merges their own PR. The turnaround target is 48 h.
- Much of this codebase was built by AI coding sessions working under `AGENTS.md`. If you use AI tools, hold them to the same gates (baselines, Kaizen, no fabrication). Each rule exists because someone broke it once and it cost real time.

---

## 7. Maintainers and licensing

| Role | Who |
|---|---|
| Project lead / original author | Hritwik Mudhai |
| Co-founder | Ritwik Singh |
| Contributors | Everyone in the git history. Add yourself by opening a PR. |

Contributions are accepted under the project licence (Apache-2.0, see
`LICENSE` / `NOTICE`); by opening a PR you agree your contribution is
licensed that way. No CLA is required. Hosting credentials for the public
instance (Render, Vercel, the `motoquant.in` domain, LLM keys) belong to the
maintainers and are never committed. To run your own instance, see
`docs/SELF_HOSTING.md`. Security issues: `SECURITY.md`.

---

## 8. How to ask for help

1. `docs/ARCHITECTURE.md` and `docs/README.md` (the docs index). For "is this implemented?", `grep -i <keyword> CHANGELOG.md` usually answers it.
2. `python -m motoquant.run --help`, then `<subcommand> --help`.
3. Read the test file for the module you're touching. The tests are the executable spec.
4. Open a GitHub Issue. Issues are searchable later, so prefer them to private messages.

---

## 9. First-week checklist

- [ ] Fork (or clone) the repo: <https://github.com/toto171/MotoQuant.in>.
- [ ] Get the test suite green locally (`CONTRIBUTING.md` §2). Start with the focused subset; the full run takes ~30 min.
- [ ] Run a sim: `python -m motoquant.run sim --bike-id 1 --venue-id 1` runs the K5 at Aamby Valley on the shipped `motoquant.db` (≈ 10.1 s; the 10.0436 s pin is the sea-level reference config, `make baselines`). A scratch `db init` + `db seed` database also has the K5 as id 1 but holds only the three reference bikes.
- [ ] Boot the API (`make api`) and the web app (`make web-install && make web-dev`), and click through the simulator and the chat.
- [ ] Read `AGENTS.md` and the top of `CHANGELOG.md`.
- [ ] Pick one good first issue from §4, scope it as a GitHub Issue, then ship a PR, however small. Proving the workflow end to end on day one is worth more than a big first contribution.
