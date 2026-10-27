# MotoQuant — Contributor Onboarding

Welcome to the project. MotoQuant is free and open source (Apache-2.0); anyone can contribute. This doc is the "day one" brief. Read it end-to-end and you should have enough context to pick up work without 20 rounds of back-and-forth.

**Read order on day one:**
0. `AGENTS.md`: the one-page working contract (5 min).
1. This file (10 min).
2. `docs/ARCHITECTURE.md` — the module map + data-flow diagram. Answers "where does X live, and how does a bike spec become a simulated ET?" before you open any code (10 min).
3. `CHANGELOG.md`: the milestone history (read the top few entries). *(`CLAUDE.md` is the AI maintainers' long session-by-session log. Optional: if you open it, read only the top entry.)*
4. `CONTRIBUTING.md` — dev workflow, branch conventions, Kaizen rule (10 min).
5. `docs/ROADMAP.md` — the live prioritized backlog + the maintainer-only actions (10 min).
   *(`reports/ROADMAP_2026_07_03.md` is a dated snapshot, kept as history only —
   sessions have repeatedly re-scoped already-finished work out of it.)*
6. Skim `motoquant/physics.py`, one sub-model like `motoquant/submodels/tire.py`, and `docs/CHAT_AGENT.md` to get a feel for the code style and the newest subsystem (15 min).

After that, get the test suite green locally (see `CONTRIBUTING.md` §2) and you're ready to open your first PR.

---

## 1. What MotoQuant is (in one paragraph)

A first-principles physics engine for predicting and optimising motorcycle quarter-mile drag racing times, aimed first at the Indian drag racing community (Aamby Valley, MMRT, BIC, Kari, Hyderabad) and now expanding to the international market (US/EU/JP/CN drag scenes). It's a Python package with a CLI, a FastAPI backend (live on Render), a Next.js web frontend (live at motoquant.in), and an agentic AI chat that can run the whole product (sims, comparisons, the build optimizer, outlaw-class builds, web lookup, estimated sims for unknown bikes). Under the hood: 15 physics sub-models integrated with RK4 at 1 ms, validated against 250 published benchmarks (276 matched runs, weighted mean |Δ| ≈ 0.26 s and bias +0.007 s corpus-wide). It is free and open source under Apache-2.0 with no paid tiers ([ADR-0006](adr/0006-open-source-pivot.md)), and you can run your own copy ([SELF_HOSTING.md](SELF_HOSTING.md)).

**Tagline:** *"The physics of faster."*

---

## 2. Current state snapshot (October 2026)

| Metric | Value |
|---|---|
| Status | Free & open source (Apache-2.0) since 2026-10-23. Monetization scrapped; optional accounts kept |
| Tests | full pytest suite green (runs ~25–35 min; focused subsets in `CONTRIBUTING.md` §4) |
| Bikes in catalog | 541 across 30+ manufacturers (India, SE Asia, US, EU, JP, CN) |
| Tires | 254 (incl. drag radials/slicks + cruiser rubber), 1,783 fitments |
| Parts | 593 across 19 categories (incl. lowering kits, air shifters, lockup clutches) |
| Venues | 20 (India + international drag strips) |
| Benchmarks | 250 ET rows + 86 top-speed rows; weighted sweep 276 matched, |Δ| 0.263 s, bias +0.007 s |
| Reference baselines | K5 9.9331 / R1 10.1436 / Hayabusa 10.3633 — pinned **bit-identical**, CI-gated |
| Chat AI | multi-step tool-calling agent (`motoquant/llm/agent.py`, `docs/CHAT_AGENT.md`) |
| Deployed | API: Render free tier (`motoquant-api.onrender.com`); web: Vercel (`motoquant.in`); both auto-deploy from `main`. Self-hosting: `docs/SELF_HOSTING.md` |
| Optional | Rust physics core, bit-identical to the Python reference (`docs/RUST_CORE.md`) |

The code is not the bottleneck. The main limits are data (instrumented Dragy timeslips for small-cc bikes) and open-source logistics (repo visibility, contributor on-ramps). See `docs/ROADMAP.md`.

---

## 3. What's live vs. what's pending

### Live and working
- CLI (`python -m motoquant.run --help`) — db/bikes/sim/venues/tires/parts/weather/import/analysis/chat and more.
- FastAPI backend: sims (quick/full/top-speed/compare), jobs API with real progress + cancel, build optimizer (surrogate-accelerated knapsack), ECU autotune, the composed outlaw pipeline, agentic chat (`/api/chat`, `/api/jobs/chat`), optional accounts (magic link + password; saved-run garage), Dragy/dyno/ECU calibration uploads, leaderboard, shareable timeslips. Everything is free and anonymous-capable; per-IP rate limits protect the compute-heavy routes.
- Next.js web app: cockpit-themed landing + simulator workbench + optimizer/autotune pages + transcript chat UI + docs/blog/validation explorer.
- (The Tauri desktop app was discontinued in July 2026 and its scaffold deleted in October; see ADR-0005.)
- Physics: 15 sub-models, adaptive RK4, calibration pipeline, numpy surrogate v2.5 (regenerate after ANY physics/DB reseed — standing contract in `artifacts/surrogate/README.md`).

### Pending / known gaps (the honest list)
- Hosted-instance DB durability: SQLite is baked into the Docker image, so every deploy wipes optional accounts and saved runs until a persistent disk is mounted (`docs/SELF_HOSTING.md` §3d).
- Small-cc accuracy floor is data-limited, not model-limited — needs real Dragy timeslips.
- Epoch-gated physics work (do NOT wire casually — moves the pinned baselines): Pacejka slip model, 4-branch clutch dispatch, staging rollout/dead-time. See the July 3 session report.
- Full backlog: `docs/ROADMAP.md`.

---

## 4. Good first issues (pick one to start)

Ranked by isolation (least cross-cutting first). All of these are in `docs/ROADMAP.md` with more detail.

### A. Catalog data passes (data work — hours, high value)
Add well-sourced bikes/parts/tires following the July-2026 pattern: sibling spec modules (`motoquant/scraper/known_bikes_2026_*.py`) with cited sources, explicit gear cassettes, individual aero values, and instrumented benchmark rows where they exist. The project rule is absolute: **no fabricated specs, prices, or benchmarks — skip and document instead**. Open targets: vintage-2T OEM tire fitments, sub-500cc drag hardware (needs real products), pricing follow-ups.

### B. Benchmark submissions (data + small web/backend work)
The accuracy story depends on instrumented runs. Make submitting one easy: tighten the `calibration_data` issue template, document the source-labelling weights (instrumented 1.0 … DERIVED 0.1) in `docs/`, and add a reviewed-row path into the sweep corpus. No fabricated rows: every benchmark needs a citable source.

### C. Build-sheet export (web — 1–2 days)
The shareable timeslip on `/r/[id]` already prints to PDF. Extend it to a one-page build sheet covering ET/trap/splits, the parts list with costs, and charts.

### D. Chat-agent polish (LLM layer — scoped pieces)
The agent shipped July 3 (`motoquant/llm/agent.py`). Scoped follow-ups: resolver letter/digit tokenization ("ZX10R" → weak match), a `mode=agent` path for the CLI `chat` subcommand, streaming responses. Everything is offline-testable via the `_call_override` seam — see `tests/test_agent.py` for the pattern.

### E. Coverage floor (tooling — half a day)
CI already uploads a coverage XML on pushes to `main` (non-blocking). Turn it into a ratchet: pick a floor for `motoquant/physics.py` + `submodels/` and fail CI if it drops.

---

## 5. Non-negotiable conventions

These will cause a PR to be rejected even if the code works.

1. **Package is `motoquant`, never `dragsim`.** The 2026 rename is final.
2. **SQLite stays until a real scaling trigger** ([ADR-0004](adr/0004-sqlite-until-scale.md)). The WAL-fallback in `motoquant/database/connection.py` is load-bearing.
3. **CLI tests call handlers directly, not subprocesses.** See `tests/test_cli.py`.
4. **Scraper is stdlib-only.** No BeautifulSoup/lxml.
5. **Physics baselines are pinned bit-identical**: K5 9.9331 / R1 10.1436 / Hayabusa 10.3633. If you touch `physics.py`, `submodels/*`, `defaults.py`, or the importer, run the baseline check + `tests/test_regression_snapshot.py` and put the deltas in your PR (template has the table). "±0.0000 at 4 decimals" is the expectation; anything else needs a full weighted-sweep justification.
6. **After any `spec_to_bike_config` change, reseed the DB** (`scripts/reseed_configs_from_specs.py`) — otherwise `/api/simulate?bike_id=N` silently diverges from the spec path. Then regenerate the surrogate (standing contract).
7. **After any catalog change, run `python scripts/audit_headline_stats.py --fix`** — the site's stat tiles/OG cards must match the DB.
8. **Never `git add -A`.** Stage explicit file lists; the tree often carries unrelated WIP.
9. **No fabricated data.** Honest gaps beat apparent completeness — this is written into multiple session postmortems.
10. **Kaizen scan before every commit** (`CONTRIBUTING.md` §7): leave every file you touch better than you found it. Put substantive write-ups in the PR description or `reports/`.

---

## 6. Project rhythms

- **Discussion:** GitHub Issues (and Discussions once enabled). Async by default.
- **Planning:** the backlog lives in `docs/ROADMAP.md`.
- **Reviews:** all PRs need green CI + one approving review; CODEOWNER approval auto-requested on physics/schema/API/infra paths; no self-merge. Turnaround target 48 h.
- **AI assistants:** much of this codebase was built by AI coding sessions working under `AGENTS.md`. If you use AI tooling, hold it to the same gates (baselines, Kaizen, no fabrication). The rules exist because each one was broken once and cost real time.

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

1. `docs/ARCHITECTURE.md` and `docs/README.md` (the docs index). For "is this implemented?", `grep -i <keyword> CHANGELOG.md CLAUDE.md` usually answers it.
2. `python -m motoquant.run --help`, then `<subcommand> --help`.
3. Read the test file for the module you're touching. Tests are the executable spec.
4. Open a GitHub Issue. Issues are searchable later, so prefer them to private messages.

---

## 9. First-week checklist

- [ ] Fork (or clone) the repo: <https://github.com/da25mem5s02-debug/MotoQuant_v1>.
- [ ] Get the test suite green locally (`CONTRIBUTING.md` §2 — use the focused subset first, the full run takes ~30 min).
- [ ] Run a sim: `python -m motoquant.run sim --bike-id 1 --venue-id 1` → the K5 at Aamby Valley (≈ 10.1 s; the 9.9331 s pin is the sea-level reference config, `make baselines`).
- [ ] Boot the API (`make api`) and the web app (`make web-install && make web-dev`), and click through the simulator and the chat.
- [ ] Read `AGENTS.md` and the top of `CHANGELOG.md`.
- [ ] Pick one §4 good-first-issue, scope it as a GitHub Issue, then ship a PR — however small. Proving the workflow end-to-end on day one beats a big first contribution.

Welcome aboard.
