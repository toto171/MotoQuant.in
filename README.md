# MotoQuant

> *The physics of faster.* A free, open-source motorcycle drag-racing simulator.

[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![CI](https://github.com/da25mem5s02-debug/MotoQuant_v1/actions/workflows/ci.yml/badge.svg)](https://github.com/da25mem5s02-debug/MotoQuant_v1/actions/workflows/ci.yml)
[![Web](https://img.shields.io/badge/web-motoquant.in-orange)](https://www.motoquant.in)

MotoQuant predicts a motorcycle's quarter-mile ET, trap speed and top speed
from first principles. It integrates engine torque, clutch slip, tire grip and
temperature, weight transfer, wheelies, aerodynamics and air density at
1 ms, and then uses that physics to answer the questions tuners actually ask:
*what does this sprocket, exhaust or tire do to my 60-foot, and what is the
cheapest tenth?*

It was built for the Indian drag-racing community (Aamby Valley, MMRT, BIC,
Kari, Hyderabad) and works for any bike and any strip. Use it in your
browser at **[motoquant.in](https://www.motoquant.in)**, or run your own copy.
Everything here (engine, catalog, web app, chat agent) is free under the
[Apache License 2.0](LICENSE).

## What's in the box

- **Physics engine**: RK4 integrator plus 15 sub-models (engine,
  forced induction, clutch, tire Pacejka + thermal, aero, rider tuck, weight
  transfer, wheelie, chain, parasitic losses, staging, environment, …), in
  pure Python + NumPy. An optional [Rust core](docs/RUST_CORE.md) is
  bit-identical to the Python reference and can run the same simulation
  natively or in the browser via WebAssembly.
- **Catalog**: 541 bikes, 254 tires, 593 parts, 20 venues, and
  1,783 bike-tire fitments in a seeded SQLite file (`motoquant.db`), with a
  compatibility engine so a part only shows up for the bikes it fits.
- **Analysis**: parts ROI (ET gained per rupee), a budget-constrained build
  optimizer, ECU/gearing autotune, Sobol sensitivity, Bayesian optimization,
  and a fast surrogate model.
- **Calibration**: import Dragy GPS runs, dyno sheets (with SAE J1349
  correction) and ECU logs, overlay them on the simulation, and fit the model
  to your own bike.
- **Interfaces**: a CLI, a FastAPI backend, the Next.js web app, an agentic
  chat assistant, and an [MCP server](docs/MCP.md) so other AI tools can use
  MotoQuant.

## Accuracy

**Validated against 250 published benchmarks** (magazine road tests,
instrumented GPS/timing-system runs and timeslips), weighted by source
quality. Across the **276 matched runs** the weighted mean |Δ| is
**0.263 s** and the weighted mean bias is **+0.007 s**
(`reports/acc_final_2026_08_08.json`). The full residual breakdown is on
[motoquant.in/validation](https://www.motoquant.in/validation).

Three reference bikes are pinned bit-identical and gated in CI:
**GSX-R 1000 K5 → 9.9331 s**, **YZF-R1 4C8 → 10.1436 s**,
**Hayabusa Gen1 → 10.3633 s** (see [docs/INVARIANTS.md](docs/INVARIANTS.md) I1).
Every benchmark keeps its source label. If you have an instrumented run that
disagrees, please [file it](https://github.com/da25mem5s02-debug/MotoQuant_v1/issues/new/choose);
that is the fastest way to make the model better.

## Quick start

Requirements: Python 3.10+ and, for the web app, Node 18+.

```bash
git clone https://github.com/da25mem5s02-debug/MotoQuant_v1.git
cd MotoQuant_v1

make install          # deps + editable motoquant package
make check            # lint + format + baseline gate + fast tests (~3 min)
make                  # list every target
```

Run the product locally:

```bash
make api              # FastAPI backend on http://localhost:8000 (OpenAPI UI at /docs)
make web-install      # once
make web-dev          # Next.js app on http://localhost:3000, against the local API
```

Or use the CLI directly. The repo ships a seeded `motoquant.db`, so there is
no setup step:

```bash
python -m motoquant.run sim --bike-id 1 --venue-id 1          # K5 at Aamby Valley
python -m motoquant.run parts --bike-id 3 --impact 56         # what does this part do?
python -m motoquant.run analysis recommend --bike-id 1 --budget 150000
python -m motoquant.run nl "optimize my Hayabusa for 35C at Aamby Valley"   # keyless NL
```

To host your own instance on Render + Vercel or any Docker host, including
the optional settings (accounts, email, LLM keys for chat, persistent disk),
follow **[docs/SELF_HOSTING.md](docs/SELF_HOSTING.md)**.

**Use MotoQuant from your AI:** `python -m motoquant.mcp_server` is a stdio MCP
server that exposes sims, catalog search and sprocket/part what-ifs as tools
([docs/MCP.md](docs/MCP.md)). There is also a Claude skill under
`skills/motoquant/`.

## Architecture

```
motoquant/            Python package
  ├── physics.py          RK4 integrator (fixed 1 ms + adaptive dt)
  ├── submodels/          15 independent physics sub-models
  ├── category_profiles.py per-class physics knobs (taxonomy v2)
  ├── database/           SQLite schema, seed, repositories, bridge
  ├── scraper/            curated bike catalog + importer (spec → config)
  ├── calibration/        Dragy / dyno / ECU import, overlay, calibrator
  ├── analysis/           ROI, build optimizer, autotune, Sobol, surrogate
  ├── llm/                agentic chat (tool calling, 5 LLM providers)
  ├── api.py              FastAPI backend
  └── run.py              CLI (python -m motoquant.run)
web/                  Next.js app (motoquant.in)
rust/                 optional Rust physics core (PyO3 + wasm32)
tests/                pytest suite
scripts/              sweeps, baseline gate, idempotent DB patches, audits
docs/                 architecture, invariants, ADRs, self-hosting, …
reports/              validation sweeps and session write-ups
```

Start with **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** (module map +
data-flow diagram) for "where does X live?". Settled decisions are recorded
in [docs/adr/](docs/adr/), and what must never break is in
[docs/INVARIANTS.md](docs/INVARIANTS.md). The docs index is
[docs/README.md](docs/README.md).

## Contributing

Contributions are welcome: code, bug reports, and especially **data**
(instrumented quarter-mile runs, dyno sheets, service-manual gear ratios,
missing bikes).

- Read **[AGENTS.md](AGENTS.md)** first. It is the one-page working contract
  for every contributor, human or AI: the prime directive, the
  `make check` → `make test` loop, and the non-negotiable rules.
- Then **[CONTRIBUTING.md](CONTRIBUTING.md)** for setup, testing and the PR
  workflow, and [docs/ONBOARDING.md](docs/ONBOARDING.md) for a day-one tour.
- Please follow the [Code of Conduct](CODE_OF_CONDUCT.md). Report
  security issues privately as described in [SECURITY.md](SECURITY.md).

### Repo files you can ignore

A few root files belong to the maintainer's private automation, not to the
product or the dev workflow:

| File(s) | What it is |
|---|---|
| `CLAUDE.md` | A long session-by-session changelog for AI maintainers. Skim only its top entry; `AGENTS.md` is the contract. |
| `DISPATCH_INBOX.md` / `DISPATCH_OUTBOX.md`, `STATUS.md` | The async queue and dashboard for the (paused) autonomous maintenance sessions. Scripts read them, so **do not move or rename** them. |
| `AUTONOMOUS_PAUSED` | Flag file that keeps those sessions paused. Its presence is intentional. |

Retired documents, including the old commercial plans, live in
[docs/archive/](docs/archive/).

## License

MotoQuant is licensed under the **Apache License, Version 2.0**. See
[LICENSE](LICENSE) and [NOTICE](NOTICE). Motorcycle, tire and parts names
are trademarks of their respective owners and are used only to identify the
products being modelled. Benchmark figures are cited facts from their
published sources.

Copyright 2026 Hritwik Mudhai and the MotoQuant contributors.
