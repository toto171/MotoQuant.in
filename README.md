# MotoQuant Pro

> *The physics of faster.*

[![CI](https://github.com/da25mem5s02-debug/MotoQuant_v1/actions/workflows/ci.yml/badge.svg)](https://github.com/da25mem5s02-debug/MotoQuant_v1/actions/workflows/ci.yml)
[![Web](https://img.shields.io/badge/web-motoquant.in-orange)](https://www.motoquant.in)
[![Code: Apache-2.0](https://img.shields.io/badge/code-Apache--2.0-blue)](LICENSE)
[![Data: ODbL 1.0](https://img.shields.io/badge/data-ODbL_1.0-blue)](LICENSE-DATA)
[![Docs: CC BY 4.0](https://img.shields.io/badge/docs-CC_BY_4.0-blue)](LICENSE-DOCS)

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

**Use MotoQuant from your AI:** the repo ships a stdio **MCP server**
(`python -m motoquant.mcp_server`) exposing sims, catalog search and
sprocket/part what-ifs as tools — wire-up in [docs/MCP.md](docs/MCP.md) —
plus a Claude skill under `skills/motoquant/`.

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
reports/            Validation JSON sweep artefacts + the July-2026 provenance scrape
docs/               All non-deploy documentation
  ├── adr/          Architecture decision records
  ├── DATA_PROVENANCE.md   What is measured, what is estimated, what is a placeholder
  └── OPEN_SOURCE_RELEASE.md   Licensing + the public-release runbook
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

### Licensing

MotoQuant Pro is open source. **Code** (`motoquant/`, `web/`, `scripts/`, `tests/`,
`e2e/`, `desktop/`) is licensed under the [Apache License 2.0](LICENSE). **Data**
(the bike spec catalog, the benchmark corpus, the parts/tire/fitment/venue tables,
`motoquant.db` and the JSON sweep artefacts) is licensed under the
[Open Database License 1.0](LICENSE-DATA). **Documentation**, the whitepaper and the
blog are [CC BY 4.0](LICENSE-DOCS). Read [docs/DATA_PROVENANCE.md](docs/DATA_PROVENANCE.md)
before relying on the data: it says which values are measured, which are
class-level estimates and which are placeholders. Contributions are accepted under
the same licences; there is no CLA. To cite the project see [CITATION.cff](CITATION.cff);
to report a vulnerability see [SECURITY.md](SECURITY.md).

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
