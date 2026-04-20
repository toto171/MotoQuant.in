# Contributing to MotoQuant Pro

Welcome. This guide gets you from a fresh clone to a green test suite in under 10 minutes, then covers the day-to-day workflow.

If you're a new collaborator joining for the first time, also read `ONBOARDING.md` — it has the current project state, the "what to pick up first" list, and the Kaizen/token-budget rules the project runs by.

---

## 1. Repository

- **GitHub:** https://github.com/da25mem5s02-debug/MotoQuant_v1
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
pip install -e .                    # editable install of the motoquant package

# 4. Initialise + seed a fresh dev database
python -m motoquant.run --db /tmp/motoquant-dev.db db init
python -m motoquant.run --db /tmp/motoquant-dev.db import --known-bikes
python -m motoquant.run --db /tmp/motoquant-dev.db db seed

# 5. Run the test suite — expect 583+ passing, 0 failing
python -m pytest tests/ -q
```

If step 5 is green, you're set.

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

### 3b. Streamlit UI

```bash
streamlit run app.py
```

Opens on http://localhost:8501. Requires the seeded `motoquant.db` in the repo root.

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
4. Physics regressions: if you touch `motoquant/physics.py` or any `submodels/*.py`, the three benchmark ETs must still match: K5 = 10.04 ± 0.07s, R1 = 10.3 ± 0.10s, Hayabusa = 10.1–10.7s range.

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

**PR requirements:**
- Tests pass locally (`python -m pytest tests/ -q`).
- Ruff clean (`ruff check . && ruff format --check .`).
- For physics changes: include the benchmark ET deltas in the PR description.
- For schema changes: include the migration path (even if manual) and update `CLAUDE.md` → "Current State" section.
- Both co-owners can merge their own PRs after self-review. For any change touching `motoquant/physics.py`, `submodels/`, or DB schema: request a review before merging.

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

- Commit secrets, API keys, or `.env` files. `.gitignore` catches the common ones; double-check before `git add -A`.
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

Deployment is Phase 3 remaining work. Current state:
- Railway (API): configured via `nixpacks.toml` + `Procfile`, not yet deployed.
- Vercel (web): configured via `vercel.json`, not yet deployed.
- Domain: `motoquant.in` (primary), `motoquant.app` (reserve).

See `DEPLOYMENT.md` and `DEPLOY-NOW.md` for the current checklist. Do not deploy without coordinating — we only have one set of credentials.
