# MotoQuant Local Lab

Self-contained build of the **full MotoQuant engine + UI** for one machine:
the 541-bike catalog, the RK4 physics engine, the numpy surrogate, the
build optimizer / ECU autotune, and the desktop UI's static build — all in
a single executable that runs on `localhost`. No hosted API, no free-tier
CPU cap, no cold starts, no LB timeouts.

> **Internal operator tool — do not distribute.** The hosted web app at
> motoquant.in is the product (desktop app scrapped July 6, 2026). This
> exists so the operator can stress-test the engine's real capabilities at
> native CPU speed. The binary contains the full catalog DB and engine —
> exactly the IP the hosted-only architecture protects.

## Download (CI-built)

GitHub → **Actions** → **Local Lab build** → **Run workflow** (pick the
branch) → wait ~10 min → grab the artifact, or the `local-lab-r<N>`
prerelease it publishes. Windows: `MotoQuantLocalLab.exe`. Linux:
`MotoQuantLocalLab`.

## Run

Double-click (or from a terminal for flags):

```
MotoQuantLocalLab.exe [--port 8000] [--no-browser] [--fresh-db] [--data-dir PATH]
```

- Starts the engine on `http://127.0.0.1:8000` (falls back to a free port)
  and opens your browser. API docs at `/docs`.
- First boot copies the seeded catalog to a per-user data dir
  (`%LOCALAPPDATA%\MotoQuantLocalLab` on Windows) so saved runs persist
  across restarts and upgrades. `--fresh-db` resets it to the shipped
  catalog.
- Rate limiting is off by default locally (`MOTOQUANT_RATE_LIMIT=false`);
  sim metering records but never blocks (billing enforcement off).
- Chat is optional: export `GROQ_API_KEY` / `GEMINI_API_KEY` etc. before
  launching if you want the agent; everything else is fully offline.
- Windows SmartScreen will warn on the unsigned exe — "More info" → "Run
  anyway". Expected; we don't code-sign internal builds.

## Stress-test ideas

- **Optimizer, no limit**: Build page → pick a Hayabusa → "Outlaw — no
  limit" → Optimize. On Render's 0.5 CPU this took minutes; measure it on
  your hardware.
- **Full-sim hammering**: `POST /api/jobs/simulate` in a loop (see /docs) —
  no per-IP limiter, no 30-sims/day gate blocking, real RK4 every call.
- **Autotune sweeps**: Autotune page — gearing + launch-RPM sweeps are
  full-sim (surrogate is launch-RPM-blind by design).

## Build locally (instead of CI)

```bash
# 1. UI in Local Lab mode (same-origin API, auth gate off)
cd desktop && npm ci && VITE_LOCAL_LAB=1 npx vite build && cd ..
# 2. Freeze
pip install -r requirements-api.txt pyinstaller
pyinstaller local_lab/motoquant-local-lab.spec --clean --noconfirm
# -> dist/MotoQuantLocalLab(.exe)
```

PyInstaller does not cross-compile — build on the OS you'll run on. The CI
workflow (`.github/workflows/local-lab.yml`) does Windows + Linux.

## How it fits the codebase

- `local_lab/entry.py` — launcher: seeds the per-user DB (copy-once, same
  semantics as `docker-entrypoint.sh`), sets env, boots uvicorn.
- `motoquant/api.py` (tail) — env-gated static-UI mount: only active when
  `MOTOQUANT_LOCAL_UI` is set; production deploys are byte-identical in
  behavior.
- Desktop UI Local Lab mode — build-time flag `VITE_LOCAL_LAB=1`:
  same-origin API base, auth gate bypassed (no hosted license authority to
  ask), History reads the local leaderboard instead of the auth-gated
  `/api/me/runs`.
