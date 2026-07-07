# ADR-0001: Desktop architecture — Tauri UI shell + bundled Python sidecar

**Status:** Superseded by [ADR-0005](0005-desktop-discontinued.md) (2026-07-06)
**Date:** 2026-04-22
**Deciders:** Hritwik Mudhai
**Phase:** Phase 5 (Desktop Application v1.0)

> ⚠️ **Superseded.** The desktop app was discontinued in July 2026 — the hosted
> web app is the product. This ADR is kept for the historical record; the
> `desktop/` scaffold remains in-tree for reference only. See ADR-0005.

## Context

MotoQuant Pro needs a desktop application for the v1.0 release. The existing
backend is ~18k lines of Python — 15 physics sub-models, SQLite catalog of
290 bikes / 465 parts, calibration pipeline (Dragy/dyno/ECU), Sobol analysis,
XGBoost+PyTorch surrogates, BoTorch optimiser, FastAPI server. Rewriting
this in Rust or Go for a desktop shell would take 3-6 months with zero
user-visible benefit.

Three architectures were considered:

**A. Tauri UI shell + bundled Python sidecar (FastAPI subprocess)**
   Tauri (Rust + WebView) boots the app; on startup a supervisor thread in
   the Rust side spawns PyInstaller-packaged Python as a child process
   listening on `127.0.0.1:$EPHEMERAL_PORT`; the React frontend talks to
   that via HTTP; on app close, Rust SIGTERMs the child.

**B. Pure Electron + Python over HTTP**
   Same Python sidecar pattern, but Electron as the shell. Bigger binary
   (Chromium embedded, ~160 MB extra), higher memory, inferior OS
   integration.

**C. Rust rewrite of physics + Tauri native IPC**
   Pure-Rust backend with no Python runtime. Smallest installer (~30 MB),
   fastest startup, no IPC overhead. But the physics engine is the
   product's moat — 15 sub-models, benchmark-calibrated to K5 10.033 s /
   R1 10.286 s / Hayabusa 10.471 s — and reimplementing it in Rust
   creates a 3-6 month validation problem where we'd re-prove every delta.

## Decision

**Choose A: Tauri 2.0 shell + bundled Python sidecar via PyInstaller.**

This matches the standard Python-GUI desktop pattern used by many
production apps (data-science notebooks, LLM UIs, dev tools). It
preserves 100 % of the physics + calibration work and ships in weeks.

## Consequences

### Positive
- Zero physics rewrite. Ship Phase 5 in 3-4 weeks, not 3-6 months.
- Reuse FastAPI endpoints already built (`/api/simulate`, `/api/bikes`,
  `/api/parts`, `/api/simulate/compare`, calibration uploads).
- All validation work (55 benchmarks, 335 tests) remains valid.
- SQLite catalog ships with the app — offline-capable.
- PyInstaller is mature on Windows/macOS/Linux; cross-build works.

### Negative
- Installer ~80-120 MB (Python 3.11 + numpy + scipy + FastAPI + our code).
  Mitigation: use `python -OO`, prune unused site-packages, consider
  `python-build-standalone` + `uv` for smaller footprint.
- Cold start ~1-2 s while Python boots. Mitigation: splash screen; warm
  the import tree in the background before the UI is ready.
- Code signing needed for macOS (Gatekeeper) and Windows (SmartScreen).
  Mitigation: Apple Developer ID ($99/y) + EV cert for Windows ($300/y)
  are both cheap relative to reaching the Pro-tier audience.
- Port discovery: the sidecar must bind a free ephemeral port and write
  it to a file the frontend reads at boot. Standard technique.

### Neutral
- Frontend: Vite + React 19 + TypeScript (Tauri's recommended stack
  for 2.0). Use recharts for v(t)/RPM(t) plots (already a dependency
  of the Next.js site, so we have design alignment).
- State: React Query for API caching + loading/error; Zustand for UI
  state (build composer, selected bike).
- Database: SQLite stays as-is; bundled `motoquant.db` read-only at
  first launch, copy-on-write to `$APPDATA/motoquant/motoquant.db` for
  user runs/history.

## References

- `motoquant/api.py` — existing FastAPI server (already deployed-ready
  via Procfile, nixpacks.toml, vercel.json for the web launch)
- `CLAUDE.md` > Phase 5 — roadmap entry
- Tauri 2.0 sidecar docs: https://v2.tauri.app/develop/sidecar/
- PyInstaller onefile: https://pyinstaller.org/en/stable/usage.html

## Rollback

If installer size or startup latency proves unacceptable for B2C
adoption (measure: >200 MB or >3 s cold boot), we consider:
1. Port only the quarter-mile physics hot loop to Rust (1-2 weeks, the
   rest stays Python)
2. Use `python-build-standalone` + astral's `uv` for a leaner runtime

We do NOT rewrite the full catalog-management + calibration layer in
Rust — those are low-frequency, high-complexity surfaces where Python
is the right tool.
