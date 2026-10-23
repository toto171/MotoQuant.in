# MotoQuant v1 — Phase-Wise Engineering + AI Work Plan

> Source: MotoQuant v1 Phase Plan (April 2026, Arya Desai).
> This is the 28-week strategic roadmap. Week-by-week task issues on GitHub
> reference this doc for the sub-task prompts.
>
> **Dated plan (April 2026).** Read it as history: the desktop phase was
> discontinued (ADR-0005; `desktop/` deleted 2026-10-23) and monetization was
> scrapped in favour of open source (ADR-0006). The live backlog is
> [ROADMAP.md](ROADMAP.md).

## Executive summary

MotoQuant v1 is a motorcycle drag-racing simulation platform with a mature
physics core (15 submodels, Pacejka tyre model, RK4 integrator at 1 ms
resolution), a catalog of 290 bikes + 69 tyres, and a deployed web + API
stack. This plan outlines the expansion from a drag-only simulator into a
comprehensive tuning platform with cornering physics, AI-powered optimization,
and professional-grade tooling.

**Key finding from the codebase audit:** the previous plan included rebuilding
Pacejka, RK4, aero, engine, drivetrain, and clutch models — all of which
already exist and are validated against 290 bikes. This revised plan eliminates
redundant work and focuses on the three real gaps: production surrogate
(undertrained at 1.5k samples), cornering physics (zero code exists), and
AI tuning intelligence (new capability).

## Timeline

| Phase   | Focus                                     | Duration   | Priority                                   |
|---------|-------------------------------------------|------------|--------------------------------------------|
| Phase 1 | Surrogate model → production grade        | Wk 1–4     | Highest — unblocks all AI features         |
| Phase 2 | Cornering + lateral dynamics (greenfield) | Wk 5–12    | Highest — biggest engineering lift         |
| Phase 3 | Weather + surface + time-of-day           | Wk 13–16   | Medium — builds on existing code           |
| Phase 4 | AI tuning intelligence layer              | Wk 17–22   | High — the product differentiator          |
| Phase 5 | Frontend + platform hardening             | Wk 23–28   | Medium — polish and production             |

## Critical process — the reseed trap

Every physics change must run `scripts/reseed_configs_from_specs.py`
afterwards, or the web/desktop sim silently diverges from CLI by 2–5 seconds.
This must be in every PR checklist and eventually automated in CI.

## Phase 1 — Surrogate model → production grade (Wk 1–4)

Current: XGBoost surrogate at R²=0.95, MAE 535 ms on 1.5k Sobol samples.
Target: MAE <50 ms on ET, <1.5 km/h on trap, <5 ms inference, served via
`/api/surrogate/predict`.

Sub-tasks:
1. **1.1 Training data sweep (1.5k → 50k Sobol samples).** Use existing
   `surrogate_data.py` + `sweep_chunked.py` parallelism. Save to Parquet
   (not npz). ~5.5 hours compute.
2. **1.2 XGBoost retrain + Optuna hyperparam search.** 100 trials, minimize
   ET MAE on 5k holdout. Target MAE <50 ms.
3. **1.3 DNN ensemble member.** Retrain existing DNN on same 50k dataset,
   ensemble XGB + DNN predictions.
4. **1.4 Deploy `/api/surrogate/predict` + `/sensitivity` routes.** Load
   ensemble at FastAPI startup, target inference <5 ms, behind a per-IP
   `rate_limit(...)` fuse (there are no tiers since the 2026-10-23
   open-source pivot).

## Phase 2 — Cornering + lateral dynamics (Wk 5–12)

Greenfield. Zero cornering code exists. Existing Pacejka only evaluates
longitudinal slip (κ).

Sub-tasks:
1. **2.1 State vector expansion (8 → 13 states).** Add `[y, v_lat, ψ, ψ̇, φ]`.
   RK4 handles both drag-only and full-track modes.
2. **2.2 New submodels:**
   - Lateral Pacejka branch (`F_y(α)`)
   - Combined-slip friction ellipse (Milliken or Sakai)
   - Rider lean + steering model (counter-steer → roll rate → lean angle)
   - Braking + corner-entry model (trail braking, lateral weight transfer)
3. **2.3 Track geometry schema.** `TrackSegment` + `TrackLayout` dataclasses.
   Pre-build 5–10 real circuits. Backward-compatible with drag strips.

Hard constraint: 287-bike drag validation baseline must still pass
within ±0.001 s.

## Phase 3 — Weather + surface + time-of-day (Wk 13–16)

Builds on existing `environmental.py` + tyre thermal model.

Sub-tasks:
1. **3.1 Surface evolution over passes.** `μ_surface(n) = μ_base + Δμ_rubber × (1 − exp(−k·n))`.
2. **3.2 Track temp → tyre temp coupling.** Solar-angle-driven track temp as tyre warm-up heat source.
3. **3.3 Humidity-dependent grip.** Dew-point penalty, aquaplaning threshold, damp-surface degradation.
4. **3.4 Wind gust model.** Gaussian noise on steady wind. Crosswind as lateral disturbance for track mode.
5. **3.5 Real-time weather API.** Open-Meteo integration, 30-min cache.

## Phase 4 — AI tuning intelligence (Wk 17–22)

Three pillars: Bayesian optimization, local LLM reasoning, semantic search.

Sub-tasks:
1. **4.1 Bayesian tuning optimizer.** Optuna + surrogate. Top-5 configs + confidence bounds.
   Supports constraints ("only change gearing" / "NHRA Pro Stock rules").
2. **4.2 Ollama local-model integration.**
   - `deepseek-r1:14b` (~9 GB) — tuning advisor, chain-of-thought
   - `llama3.2:3b` (~2 GB) — fast in-UI chat
   - `codellama:13b` (~7 GB) — auto-generate bike-spec entries
   - `nomic-embed-text` (~274 MB) — embeddings
3. **4.3 Session vector database.** ChromaDB. Every run embedded as
   config + weather + result + delta.
4. **4.4 SHAP explainability.** Tornado-chart feature importance + per-param
   sensitivity sweeps.

All AI features degrade gracefully without Ollama.

## Phase 5 — Frontend + platform hardening (Wk 23–28)

Sub-tasks:
1. **5.1a `/build` instant surrogate feedback.** Wire BuildPage to surrogate. <5 ms slider response.
2. **5.1b `/simulator` live telemetry stream.** WebSocket, real-time velocity/RPM/slip/tyre-temp charts.
3. **5.2a `/tuner` — AI command center (new).** Chat panel, optimizer, SHAP chart, sensitivity sweeps.
4. **5.2b `/compare` — run analysis (new).** A-vs-B overlay, delta table, session-history search.
5. **5.2c `/track` — geometry editor (new).** Visual drag-drop track layout.
6. **5.3 Desktop Tauri ↔ Python handshake** verified and fixed. Offline-mode bundle.
7. **5.4 CI/CD reseed-trap automation.** PR-gate: physics change → reseed → sweep → fail if >0.001 s drift.
8. **5.5 First desktop release `v0.1.0`.** Real Ed25519 keypair, real icons, signed binaries.

## Tech additions (beyond existing stack)

| Package             | Purpose                                                                   | Phase    |
|---------------------|---------------------------------------------------------------------------|----------|
| `optuna`            | Hyperparam search (surrogate) + Bayesian tuning optimizer                 | P1, P4   |
| `shap`              | Feature-importance explainability                                         | P4       |
| `chromadb`          | Session semantic search                                                    | P4       |
| `httpx`             | Async client for Ollama                                                    | P4       |
| `pyarrow`           | Parquet for 50k+ training rows                                             | P1       |
| `websockets`        | Real-time sim telemetry                                                    | P5       |

## Ollama models to install

```bash
ollama pull deepseek-r1:14b    # ~9 GB — tuning reasoning
ollama pull llama3.2:3b        # ~2 GB — fast chat
ollama pull codellama:13b      # ~7 GB — spec auto-gen
ollama pull nomic-embed-text   # ~274 MB — embeddings
```
