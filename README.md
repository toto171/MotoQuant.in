# MotoQuant Pro

> *The physics of faster.*

[![CI](https://github.com/da25mem5s02-debug/MotoQuant_v1/actions/workflows/ci.yml/badge.svg)](https://github.com/da25mem5s02-debug/MotoQuant_v1/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/da25mem5s02-debug/MotoQuant_v1?label=desktop%20release)](https://github.com/da25mem5s02-debug/MotoQuant_v1/releases/latest)
[![Web](https://img.shields.io/badge/web-motoquant.in-orange)](https://www.motoquant.in)

First-principles Python physics engine for motorcycle quarter-mile drag racing
prediction, optimisation, and parts ROI analysis. Aimed at the Indian drag
racing community (Aamby Valley, MMRT, BIC, Kari, Hyderabad) with 270
production bikes modelled, a 424-part catalog, and 739+ tests.

Reference baselines: **GSX-R 1000 K5 → 10.034 s**, **YZF-R1 4C8 → 10.286 s**,
**Hayabusa Gen1 → 10.472 s**.

## Download (Desktop App)

> Desktop builds are produced by CI on every tagged release. Until `v0.1.0`
> is tagged the links below resolve to a 404 — follow the
> [release runbook](docs/RELEASE.md) to cut the first release.

| Platform | Installer |
|----------|-----------|
| **Windows 10/11 x64** | [`.exe` (NSIS)](https://github.com/da25mem5s02-debug/MotoQuant_v1/releases/latest/download/MotoQuant-Pro-setup.exe) · [`.msi`](https://github.com/da25mem5s02-debug/MotoQuant_v1/releases/latest/download/MotoQuant-Pro.msi) |
| **macOS Apple Silicon (M1+)** | [`.dmg` (arm64)](https://github.com/da25mem5s02-debug/MotoQuant_v1/releases/latest/download/MotoQuant-Pro_aarch64.dmg) |
| **macOS Intel** | [`.dmg` (x64)](https://github.com/da25mem5s02-debug/MotoQuant_v1/releases/latest/download/MotoQuant-Pro_x64.dmg) |
| **Linux x64** | [`.AppImage`](https://github.com/da25mem5s02-debug/MotoQuant_v1/releases/latest/download/MotoQuant-Pro.AppImage) · [`.deb`](https://github.com/da25mem5s02-debug/MotoQuant_v1/releases/latest/download/MotoQuant-Pro.deb) |

See [docs/INSTALL.md](docs/INSTALL.md) for platform-specific notes (SmartScreen
bypass on Windows, Gatekeeper bypass on macOS, FUSE requirement on Linux).

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
web/                Next.js 14 marketing + sim