# MotoQuant Pro

> *The physics of faster.*

First-principles Python physics engine for motorcycle quarter-mile drag racing
prediction, optimisation, and parts ROI analysis. Aimed at the Indian drag
racing community (Aamby Valley, MMRT, BIC, Kari, Hyderabad) with 270
production bikes modelled, a 424-part catalog, and 739+ tests.

Reference baselines: **GSX-R 1000 K5 → 10.034 s**, **YZF-R1 4C8 → 10.286 s**,
**Hayabusa Gen1 → 10.472 s**.

## Quickstart

```bash
# Install
pip install -e .

# Boot the Streamlit UI
streamlit run app.py

# Or use the CLI
python -m motoquant.run db init
python -m motoquant.run import --known-bikes
python -m motoquant.run sim --bike-id 1 --venue-id 1
```

## Repo layout

```
motoquant/          Python package -- physics engine, DB layer, calibration,
                    analysis, scraper, CLI.
  ├── physics.py        RK4 integrator (599 lines)
  ├── submodels/        15 independent sub-models (engine, tire, aero, ...)
  ├── database/         SQLite schema + seed + repos
  ├── calibration/      Dragy + dyno + ECU import, overlay, calibrator
  ├── analysis/         ROI, Sobol, Bayesian opt, surrogate, recommendations
  ├── scraper/          bikez.com crawler + known-bike catalog
  └── api.py            FastAPI web server

tests/              pytest suite (run: `pytest tests/`)
desktop/            Tauri 2 + React 19 MVP (Phase 5, in development)
web/                Next.js 14 marketing + simulator (motoquant.in)
scripts/            Validation harnesses + one-off automation
artifacts/          ML model outputs (surrogate .pkl, training data)
reports/            Validation JSON reports (one per sweep)
docs/               All non-deploy documentation
  ├── adr/          Architecture decision records
  ├── changelog/    Release notes, fix summaries
  └── papers/       Reference papers, project plans, validation reports
```

Deployment configs (`Dockerfile`, `Procfile`, `railway.toml`, `nixpacks.toml`,
`vercel.json`, `requirements-api.txt`) and launch runbooks
(`DEPLOY-NOW.md`, `DEPLOYMENT.md`, `RUNBOOK_LAUNCH.md`,
`LAUNCH-STEPS-FOR-YOU.md`, `SOFT-LAUNCH-CHECKLIST.md`) live at the repo root.

`CLAUDE.md` is the persistent project-context file read at the start of every
Claude session -- consult it for the full state-of-the-world, known issues,
and phase roadmap.

## Project state (Apr 2026)

- **Phase 1 -- Core Physics:** complete. 15 sub-models, adaptive RK4.
- **Phase 2 -- Database & Ingestion:** complete. 270 bikes, 159 tires,
  424 parts, 20 venues, 209 OEM bike-tire fitments.
- **Phase 3 -- Validation & Calibration:** in progress. Dragy + dyno + ECU
  import done; FastAPI + Next.js frontend live at motoquant.in.
- **Phase 4 -- AI / Optimisation:** in progress. ROI, Sobol, Bayesian opt,
  XGBoost + DNN surrogates, smart recommendations -- all shipping.
- **Phase 5 -- Desktop App:** scaffolded. Tauri 2 + React 19 + Vite 5 MVP.
- **Phase 6 -- Commercial Launch:** future.

Contribute: see [CONTRIBUTING.md](CONTRIBUTING.md). Getting-started walkthrough:
[docs/ONBOARDING.md](docs/ONBOARDING.md).
