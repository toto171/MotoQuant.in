# MotoQuant Pro — Co-Developer Onboarding

Welcome to the project. This doc is the "day one" brief — read it end-to-end, then you should have enough context to pick up work without 20 rounds of back-and-forth.

**Read order on day one:**
1. This file (10 min).
2. `CLAUDE.md` — the live status document, single source of truth for project state (15 min).
3. `CONTRIBUTING.md` — dev workflow, branch conventions, Kaizen rule (10 min).
4. Skim `motoquant/physics.py` and one sub-model like `motoquant/submodels/tire.py` to get a feel for the code style (15 min).

After that, get the test suite green locally (see `CONTRIBUTING.md` §2) and you're ready to open your first PR.

---

## 1. What MotoQuant is (in one paragraph)

A first-principles physics engine for predicting and optimising motorcycle quarter-mile drag racing times, aimed at the Indian drag racing community (Aamby Valley, MMRT, BIC, Kari, Hyderabad). It's a Python package with a CLI, a FastAPI web backend, a Streamlit desktop UI, and a Next.js marketing + simulator frontend. Under the hood: 15 independent physics sub-models integrated with adaptive RK4 at 1 ms, validated against real magazine test data to within ±0.07s on calibrated bikes. Built for B2B (Pune/Narhe tuning shops, racing teams) and B2C (enthusiasts running their own builds) with a tiered licensing plan — see `MotoQuant_Monetisation_Plan.pdf`.

**Tagline:** *"The physics of faster."*

---

## 2. Current state snapshot (April 2026)

| Metric | Value |
|---|---|
| Phase | 3 (Validation & Calibration) — code complete, deploy pending |
| Tests passing | 583+ across 13 test files, zero failing |
| Bikes in catalog | 138 (3 reference + 135 curated) across 20 manufacturers |
| Tires in catalog | 69 across 15 manufacturers, 5 compound types |
| Parts in catalog | 70 across 16 categories |
| Venues | 12 (5 Indian + 7 international) |
| OEM tire fitments seeded | 209 |
| Physics validation | 36% pass on 28-bike magazine benchmark, mean bias +0.58s (conservative) |

The project is healthy. The code is not the bottleneck — deployment, data (more dyno curves, more real Dragy runs), and the AI/optimisation layer are.

---

## 3. What's actually live vs. what's pending

### Live and working
- CLI with 11 subcommands (`db`, `bikes`, `sim`, `venues`, `tires`, `parts`, `weather`, `scrape`, `import`, `history`, `leaderboard`, `analysis`).
- FastAPI web server with 10 endpoints (simulate, compare A-vs-B, Dragy upload, dyno upload, bikes, tires, venues, leaderboard, health).
- Streamlit desktop simulator (`app.py`) with Basic/Advanced build modes and tire swap dropdowns.
- 15/15 physics sub-models, adaptive RK4, full calibration pipeline (Dragy + dyno + ECU log import, auto-calibration via differential evolution + Nelder-Mead).
- Parts ROI engine (knapsack optimiser), Sobol sensitivity analysis, BoTorch Bayesian optimisation, XGBoost + DNN surrogate models, Smart Recommendations engine with synergy detection.
- Next.js landing + live simulator widget in `web/`.

### Deployed
- Render API backend (`motoquant-api.onrender.com`) — Docker deploy via `render.yaml`; see `docs/RENDER_MIGRATION.md`.
- Vercel frontend (`motoquant.in`) — `vercel.json`; the browser reaches the API through the `/api/*` rewrite.

### Not started
- Phase 5: Tauri 2.0 desktop app with React 19 / TS frontend (replaces Streamlit for v1.0 release).
- Phase 6: B2C freemium + B2B Pro licensing, PPO RL for launch control, PostgreSQL cloud sync.

See `CLAUDE.md` → "Full project roadmap" for the authoritative list.

---

## 4. Good first issues (pick one of these to start)

Ranked by isolation (least cross-cutting first), so you can ship a PR without learning the whole codebase.

### A. Expand the dyno curve library (data work — half a day)
Currently 25/135 bikes have real dyno curves injected via `motoquant/scraper/dyno_curves.py`. The other 110 use synthetic curves, which is the main cause of the +0.5–1.0s bias on 600cc bikes (see `CLAUDE.md` → "Physics validation baseline"). Pick 5–10 bikes, find published dyno charts (Cycle World, MCN, 2WheelTuner), transcribe the curves, add entries. One PR per manufacturer is fine. Every real dyno curve moves the validation pass rate up.

### B. Fix 600cc class accuracy (physics work — 1–2 days)
Our benchmark shows 600cc screamers run +0.5–1.0s slow. Likely cause: the RPM-to-torque model's drop-off above peak power is too aggressive for high-revving engines. Pick one bike (e.g. Yamaha YZF-R6), enable verbose logging in `motoquant/submodels/engine.py`, and compare the sim's torque-vs-RPM trace against a real dyno. File the bug or ship the fix.

### C. Indian parts pricing auto-refresh (new feature — 2–3 days)
Parts catalog prices are hand-entered in INR and go stale. Build a scraper for 2–3 Indian retailers (Motorcycle Diaries, MotorSportz, Amazon.in) that refreshes `parts.price_inr` weekly. Same stdlib-only pattern as `motoquant/scraper/bikez.py`. CLI: `parts refresh-prices`.

### D. Phase 4C PINN surrogate (ML work — 1–2 weeks, conditional)
Only do this if you have PyTorch + physics-informed neural network experience AND the existing DNN surrogate (`surrogate_dnn.py`) shows poor extrapolation outside its training distribution. Bake physics constraints (e.g. power ≤ engine peak, tire slip bounded) into the loss function. Justify with DNN failure evidence in the PR description before building.

### E. Deployment ops on Render + Vercel (needs credentials)
Both are live and auto-deploy from `main` (backend rebuilds gated by the `buildFilter` in `render.yaml`). See `docs/RENDER_MIGRATION.md` for the runbook. Requires access to the shared hosting accounts — coordinate before touching.

---

## 5. Non-negotiable conventions

These are the things that will cause a PR to be rejected even if the code works.

1. **Package is `motoquant`, never `dragsim`.** Rename was April 2026. Any `dragsim` string anywhere is a regression.
2. **SQLite stays until Phase 6.** The WAL-fallback in `motoquant/database/connection.py` is load-bearing on mounted filesystems. Do not replace with PostgreSQL locally.
3. **CLI tests call handlers directly, not subprocesses.** See `tests/test_cli.py` for the pattern. Subprocess tests break on the mounted dev FS.
4. **Scraper is stdlib-only.** No BeautifulSoup, no lxml. Use regex + `html.parser`. See `motoquant/scraper/bikez.py`.
5. **Physics regressions blocked.** GSX-R 1000 K5 must stay at 10.04 ± 0.07s, R1 at 10.3 ± 0.10s, Hayabusa in 10.1–10.7s. If your change moves these, that's a regression — either roll back or justify with real-world data in the PR.
6. **Kaizen scan before every commit.** Read `CLAUDE.md` → "Kaizen Principle". This is the rule that keeps the codebase healthy; skipping it is how the turbo-kit-moves-ET-by-0.008s bug happened.
7. **`CLAUDE.md` is the project log.** If you finish a substantive piece of work, update "Current State" and the relevant phase checklist. Both co-owners do this.

---

## 6. Project rhythms

- **Standup:** informal, async via GitHub Issues or DM. The `engineering:standup` skill can generate one from recent commits.
- **Planning:** roadmap lives in `CLAUDE.md` → "Full project roadmap". Reprioritise quarterly.
- **Reviews:** all PRs require at least one approving review + green CI before merge — no self-merge, enforced by branch protection. Physics / schema / API / infra paths require CODEOWNER approval (auto-requested via `.github/CODEOWNERS`). Turnaround target is 48h; ping the other owner if a PR has been idle longer.
- **Model selection:** when using AI assistants (Claude, Cursor), follow `CLAUDE.md` → "Model Selection" rules. Sonnet for coding, Opus for architecture, Haiku for quick lookups.

---

## 7. People and credentials

| Role | Owner | Notes |
|---|---|---|
| Project lead / founder | Hritwik Mudhai (motoquant@gmail.com) | Original author, primary account holder |
| Co-developer | *(you — fill in)* | Equal admin on GitHub; coordinate on deployment credentials |

Shared credentials (do not commit):
- Render API hosting — single account, ask Hritwik.
- Vercel frontend hosting — single account.
- Domain registrar (`motoquant.in`) — via GitHub Education pack, single account.
- OpenWeatherMap API key — in `.env`, ask for a copy.

When a second set of credentials is needed for any of these, open an Issue and we'll add you as a team member on that platform.

---

## 8. How to ask for help

The project has a lot of surface area. When you're stuck:

1. Search `CLAUDE.md` with `grep -i <keyword> CLAUDE.md` — most "is this implemented?" questions are answered there.
2. Run `python -m motoquant.run --help` and then `<subcommand> --help` — CLI is well-documented inline.
3. Look at the test file for the module you're working on (`tests/test_<module>.py`) — tests are the best executable spec.
4. Open a GitHub Issue with the question. Prefer Issues over DMs so the answer is searchable later.

---

## 9. First-week checklist

- [ ] Accept GitHub collaborator invite; clone the repo; push a test branch to confirm write access.
- [ ] Get the full test suite green locally (583+ passing).
- [ ] Run a simulation: `python -m motoquant.run sim --bike-id 1 --venue-id 1` — should output ≈ 10.04s for the K5.
- [ ] Launch the Streamlit app and the FastAPI server, hit both in a browser.
- [ ] Read `CLAUDE.md` end-to-end; ask questions in GitHub Issues on anything unclear.
- [ ] Pick one item from §4 "Good first issues" and scope it as a GitHub Issue before opening a PR.
- [ ] Ship one PR, however small — a doc typo fix, a new test, a bike dyno curve. Proving the workflow end-to-end on day one is worth more than a big first contribution.

Welcome aboard.
