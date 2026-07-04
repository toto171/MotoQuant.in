# Contributing to MotoQuant Pro

Welcome. This guide gets you from a fresh clone to a green test suite in under 10 minutes, then covers the day-to-day workflow.

If you're a new collaborator joining for the first time, also read `ONBOARDING.md` — it has the current project state, the "what to pick up first" list, and the Kaizen/token-budget rules the project runs by.

---

## 1. Repository

- **GitHub:** https://github.com/da25mem5s02-debug/MotoQuant_v1
  - Planned move: once the GitHub Organization `motoquant-labs` is created (see `docs/TEAM_SCALING.md`), the repo transfers to `github.com/motoquant-labs/motoquant`. Update your remote with `git remote set-url origin <new-url>` after the transfer.
- **Package name:** `motoquant` (formerly `dragsim` — do not reintroduce that string anywhere)
- **Python:** 3.10 or newer (tested on 3.10, 3.11, 3.12)
- **Primary DB:** SQLite (`motoquant.db`) — Supabase PostgreSQL is deferred to Phase 6

---

## 2. One-time setup

```bash
# 1. Clone
git clone https://github.com/da25mem5s02-debug/MotoQuant_v1.git
cd MotoQuant_v1

# 2. Virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate            # Windows PowerShell

# 3. Install dependencies
pip install -r requirements-api.txt
pip install -r requirements-dev.txt # pytest + hypothesis (test-only deps)
pip install -e .                    # editable install of the motoquant package

# 4. Initialise + seed a fresh dev database
python -m motoquant.run --db /tmp/motoquant-dev.db db init
python -m motoquant.run --db /tmp/motoquant-dev.db import --known-bikes
python -m motoquant.run --db /tmp/motoquant-dev.db db seed

# 5. Run the focused test subset first (~3 min) — expect 0 failures
python -m pytest tests/test_validation.py tests/test_scraper.py \
    tests/test_database.py tests/test_agent.py -q

# The FULL suite is ~3k tests and takes 25-35 minutes; run it before any PR:
python -m pytest tests/ -q
```

If those are green, you're set.

The committed `motoquant.db` in the repo root is the production seeded DB. Do not run migrations against it during dev — always use a `/tmp/` path like above, or `:memory:` for tests.

---

## 3. Running the three entry points

### 3a. CLI

```bash
python -m motoquant.run --help
python -m motoquant.run bikes
python -m motoquant.run sim --bike-id 1 --venue-id 1
python -m motoquant.run analysis recommend --bike-id 1 --budget 150000
```

Full subcommand list is in `CLAUDE.md` → "CLI subcommands available".

### 3b. Web frontend (the primary product UI)

```bash
cd web && npm install && npm run dev     # http://localhost:3000
```

Point it at a local API with `NEXT_PUBLIC_API_URL=http://localhost:8000` (else it
proxies to the production Render API). Before committing anything under `web/`,
run `npx next build` — it is exactly what Vercel runs and catches the
App-Router prerender class of failure (see `web/CONTRIBUTING.md`).

The desktop app lives in `desktop/` (Tauri 2 + React; hosted-only client):
`cd desktop && npm install && npx tsc --noEmit && npx vitest run` for the
JS-side checks. The Rust shell needs a local cargo toolchain (see
`desktop/RELEASE.md`).

The legacy Streamlit UI (`app.py`) has been removed. The web app (`web/`)
and the desktop app (`desktop/`) are the supported user interfaces.

### 3c. FastAPI web server

```bash
uvicorn motoquant.api:app --reload --port 8000
```

Then hit http://localhost:8000/docs for the OpenAPI UI. The Next.js frontend in `web/` calls this API.

---

## 4. Testing

```bash
# Full suite (fast path — skips slow integration tests)
python -m pytest tests/ -q

# Single file
python -m pytest tests/test_api.py -v

# Run slow integration tests (recommendations engine, full physics on ~70 parts)
MOTOQUANT_SLOW_TESTS=1 python -m pytest tests/test_recommendations.py -v

# Single test by name
python -m pytest tests/test_physics.py::test_gsxr1000_k5_benchmark -v
```

**Rules:**
1. Every new public function needs at least one test that would fail if the function did nothing.
2. Tests must use `:memory:` or `/tmp/` SQLite paths — never the production `motoquant.db`.
3. CLI tests import command handlers directly via `redirect_stdout` + `unittest.mock.patch` — do not spawn subprocesses (WAL journal mode fails on the mounted dev filesystem).
4. Physics regressions: the three reference baselines are pinned to 4 decimals — K5 **10.0334**, R1 **10.2859**, Hayabusa **10.4712** — and the expectation for refactors is **bit-identical** (Δ +0.0000). If you touch `motoquant/physics.py`, any `submodels/*.py`, `defaults.py`, or `motoquant/scraper/importer.py`: run the baseline check, `tests/test_regression_snapshot.py`, and put the delta table in your PR. A deliberate accuracy change needs the full weighted sweep (`scripts/phys_weighted_sweep.py`) as justification.
5. After changing `spec_to_bike_config` (importer physics, gear ratios, aero rules): run `MOTOQUANT_DB=motoquant.db python scripts/reseed_configs_from_specs.py`, then regenerate the surrogate (`artifacts/surrogate/README.md` — standing contract).
6. After any catalog/count change: `python scripts/audit_headline_stats.py --fix` so the site's stat tiles stay truthful.

---

## 5. Code style

Ruff enforces lint + format. Config is in `pyproject.toml`.

```bash
ruff check .                        # lint
ruff check . --fix                  # auto-fix safe issues
ruff format .                       # format
```

Conventions:
- Line length 88 (handled by `ruff format`).
- Imports: sorted by isort rules; `motoquant.*` is first-party.
- No `print()` in library code — use `logging`. CLI handlers can print to stdout.
- Type-hint all new public functions. Existing untyped code is fair game to type as you touch it (Kaizen rule).
- Docstrings: triple-quoted, first line summary, blank line, then details. Follow the style already in `motoquant/physics.py`.

---

## 6. Branch + PR workflow

We use a simple trunk-based flow. `main` is always deployable (tests green, API boots, CLI smoke test passes).

```bash
# 1. Start from updated main
git checkout main && git pull

# 2. Branch
git checkout -b feature/<short-name>        # e.g. feature/pinn-surrogate
# or
git checkout -b fix/<short-name>            # e.g. fix/overlay-rmse-key
# or
git checkout -b data/<short-name>           # e.g. data/ktm-rc390-dyno

# 3. Commit in logical chunks
git add <files>
git commit -m "Short imperative subject line"
# Longer body if the why is non-obvious.

# 4. Push + open PR on GitHub
git push -u origin feature/<short-name>
```

**PR requirements (strict — enforced by branch protection on `main`):**
- Tests pass locally (`python -m pytest tests/ -q`).
- Ruff clean (`ruff check . && ruff format --check .`).
- CI workflow green on the PR (pytest + ruff + desktop tsc/vite build + web Next.js build).
- **At least one approving review** from someone other than the PR author.
- For files owned via `.github/CODEOWNERS` (physics, schema, calibration, API, infra): the listed **CODEOWNER's approval is required** — GitHub will auto-request it.
- For physics changes: include the benchmark ET deltas in the PR description (template has a table for this).
- For schema changes: include the migration path (even if manual) and update `CLAUDE.md` → "Current State" section.
- **No self-merge.** Even the repo owner goes through review on anything touching a CODEOWNER-protected path.
- `main` is protected: no direct pushes, no force-push, no deletion.
- Once merged, a successful CI run on `main` triggers the Vercel production deploy (`.github/workflows/deploy.yml`). A red CI never reaches Vercel.

**Commit message style** (look at `git log --oneline` for examples):
- Imperative mood, present tense: "Add …", "Fix …", "Refactor …"
- Subject line ≤ 72 chars, no trailing period.
- Body explains why, not what — the diff shows the what.

---

## 7. The Kaizen rule (read this before you PR)

Lifted from `CLAUDE.md`: *every time you touch a file, leave it better than you found it.* Before marking a task complete, scan the files you modified for:

1. Silent failure modes (swallowed exceptions, helpers that accept invalid paths without logging).
2. Data ↔ model mismatch (parameter paths in seed/DB/config that don't match dataclass fields).
3. Bypass paths / dead fallbacks (fast paths that make a branch dead; modifications must flow through all active paths).
4. Missing tests on new public functions.
5. Numerical sanity (simulation deltas must make physical sense — a 15 psi turbo kit moving ET by 0.008s is a bug).
6. Dead fields (unused DB columns / config keys — flag or remove).
7. Backwards-compatibility for renamed fields (grep all uses, update, run full suite).

This is not optional. The current clean state of the codebase is the result of applying this consistently.

---

## 8. Things you cannot do

- Commit secrets, API keys, or `.env` files.
- Run `git add -A` / `git add .` — **ever**. Stage explicit file lists; the working tree routinely carries unrelated WIP and generated artifacts.
- Force-push to `main`. Use `feature/*` branches and PRs.
- Rename the package away from `motoquant`. The 2026 rename from `dragsim` is final.
- Replace SQLite with PostgreSQL before Phase 6. The WAL-fallback code is load-bearing on Windows / mounted FS.
- Add BeautifulSoup / lxml to the scraper — `motoquant/scraper/bikez.py` is stdlib-only by design.
- Introduce `requirements.txt` separate from `requirements-api.txt` without discussing first. One dependency file avoids drift.

---

## 9. Where to ask questions

- GitHub Issues on the repo (preferred — leaves a trail).
- Direct message to the other co-owner for quick synchronous stuff.
- `CLAUDE.md` is the always-current project status document — check it first before asking "is X done yet?"

---

## 10. Release / deploy

Live since April 2026; backend migrated Railway → Render on May 31, 2026:
- Render (API): `motoquant-api.onrender.com` — Docker deploy via `render.yaml` (free tier, Singapore).
- Vercel (web): `motoquant.in` — `vercel.json` + the `/api/*` rewrite in `web/next.config.js` point at Render.
- Domain: `motoquant.in` (primary), `motoquant.app` (reserve).

Merging to `main` IS the production deploy: Render rebuilds the API when the
diff touches `motoquant/**`, `motoquant.db`, `requirements-api.txt`, `Dockerfile`
or `render.yaml` (the `buildFilter` — web-only merges do not restart the API),
and Vercel deploys the frontend on every merge. See `docs/RENDER_MIGRATION.md`
for the runbook + rollback. Do not touch hosting settings without coordinating —
we only have one set of credentials.
