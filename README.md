# MotoQuant Pro

> *The physics of faster.*

[![CI](https://github.com/da25mem5s02-debug/MotoQuant_v1/actions/workflows/ci.yml/badge.svg)](https://github.com/da25mem5s02-debug/MotoQuant_v1/actions/workflows/ci.yml)
[![Web](https://img.shields.io/badge/web-motoquant.in-orange)](https://www.motoquant.in)

First-principles Python physics engine for motorcycle quarter-mile drag racing
prediction, optimisation, and parts ROI analysis. Aimed at the Indian drag
racing community (Aamby Valley, MMRT, BIC, Kari, Hyderabad) with
541 bikes, 254 tires, 593 parts, and 20 venues modelled, validated
against 250 published benchmarks (weighted mean |Δ| 0.272 s, bias −0.005 s
across 277 matched runs) by a ~4,400-test pytest suite.

Reference baselines: **GSX-R 1000 K5 → 9.9331 s**, **YZF-R1 4C8 → 10.1436 s**,
**Hayabusa Gen1 → 10.3633 s** (pinned bit-identical; see
[docs/INVARIANTS.md](docs/INVARIANTS.md) I1).

## Quickstart

```bash
make install          # deps + editable package
make health           # state of the world (baselines, lint, catalog, secrets)
make check            # fast pre-PR gate: lint + format + baselines + fast tests
make                  # list every target

# Run the product
make api              # FastAPI backend on :8000
make web-dev          # Next.js frontend against the local API

# Or use the CLI directly (the repo ships a seeded motoquant.db)
python -m motoquant.run sim --bike-id 1 --venue-id 1
python -m motoquant.run chat "how fast is a hayabusa at Aamby Valley?"
```

> **Contributing (human or AI):** read **[AGENTS.md](AGENTS.md)** first — the
> one-page working contract (the prime directive, the loop, the non-negotiable
> rules). New collaborators then read [docs/ONBOARDING.md](docs/ONBOARDING.md)
> (day-one brief) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) (module map +
> data-flow — *where does X live?*). What must never break lives in
> [docs/INVARIANTS.md](docs/INVARIANTS.md); the bugs that keep coming back are in
> [docs/KNOWN_TRAPS.md](docs/KNOWN_TRAPS.md).

## Repo layout

```
motoquant/          Python package -- physics engine, DB layer, calibration,
                    analysis, scraper, CLI.
  ├── physics.py        RK4 integrator (637 lines)
  ├── submodels/        15 independent sub-models (engine, tire, aero, ...)
  ├── database/         SQLite schema + seed + repos
  ├── calibration/      Dragy + dyno + ECU import, overlay, calibrator
  ├── analysis/         ROI, Sobol, Bayesian opt, surrogate, recommendations
  ├── scraper/          bikez.com crawler + known-bike catalog
  └── api.py            FastAPI web server

tests/              pytest suite (run: `pytest tests/`)
desktop/            Tauri 2 + React 19 MVP (Phase 5 — DISCONTINUED July 2026; hosted web app is the product)
web/                Next.js 14 marketing + simulator (motoquant.in)
scripts/            Validation harnesses + one-off automation
artifacts/          ML model outputs (surrogate .pkl, training data)
reports/            Validation JSON reports (one per sweep)
docs/               All non-deploy documentation
  ├── adr/          Architecture decision records
  ├── changelog/    Release notes, fix summaries
  └── papers/       Reference papers, project plans, validation reports
```

Deployment configs (`render.yaml`, `Dockerfile`, `vercel.json`,
`requirements-api.txt`) live at the repo root. The API runs on Render
(`motoquant-api.onrender.com`, Docker via `render.yaml`); the frontend is on
Vercel (`motoquant.in`) with a `/api/*` rewrite to Render. See
`docs/RENDER_MIGRATION.md` for the cutover + rollback runbook.

`CLAUDE.md` is the persistent project-context file read at the start of every
Claude session -- consult it for the full state-of-the-world, known issues,
and phase roadmap. It is a long, single-paragraph changelog; skim the *top*
entry for the latest state and don't try to read it end-to-end.

### Root files you can ignore while developing

Several root files are **autonomous-operations plumbing**, not part of the
product or the dev workflow. A newcomer can safely ignore them:

| File(s) | What it is |
|---|---|
| `DISPATCH_INBOX.md` / `DISPATCH_OUTBOX.md` / `DISPATCH_*.md` | Async message queue between the operator and unattended Claude sessions (`docs/DISPATCH_PROTOCOL.md`). Read/written by `scripts/session_*flight.sh` — **do not move or rename** them. |
| `NEXT_SESSION.md`, `STATUS.md` | Session-handoff scratch notes. |
| `AUTONOMOUS_PAUSED` | A flag file that pauses the scheduled autonomous runs (`scripts/START.sh`). Its presence is intentional. |

Everything you actually need to build, test, and run the product is covered by
`README.md`, `docs/ONBOARDING.md`, `docs/ARCHITECTURE.md`, and `CONTRIBUTING.md`.

## Project state (Jun 2026)

- **Phase 1 -- Core Physics:** complete. 15 sub-models, adaptive RK4.
- **Phase 2 -- Database & Ingestion:** complete. 541 bikes, 254 tires,
  593 parts, 20 venues, 1860 OEM bike-tire fitments.
- **Phase 3 -- Validation & Calibration:** in progress. Dragy + dyno + ECU
  import done; FastAPI + Next.js frontend live at motoquant.in.
- **Phase 4 -- AI / Optimisation:** in progress. ROI, Sobol, Bayesian opt,
  XGBoost + DNN surrogates, smart recommendations -- all shipping.
- **Phase 5 -- Desktop App:** discontinued (July 2026). The hosted web app
  at motoquant.in is the product; the `desktop/` scaffold remains in-tree
  for reference only and ships nothing.
- **Phase 6 -- Commercial Launch:** in progress. Accounts, Razorpay + Stripe
  payments, freemium beta live.

Contribute: see [CONTRIBUTING.md](CONTRIBUTING.md). Getting-started walkthrough:
[docs/ONBOARDING.md](docs/ONBOARDING.md).
