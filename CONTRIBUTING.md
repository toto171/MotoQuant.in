# Contributing to MotoQuant

Welcome, and thank you. MotoQuant is free and open source under the
[Apache License 2.0](LICENSE). Contributions of every size are welcome:
fixes, features, docs, and especially **data** (instrumented quarter-mile
runs, dyno sheets, service-manual gear ratios, missing bikes).

This guide gets you from a fresh clone to a green test suite in under 10 minutes, then covers the day-to-day workflow.

Read **[AGENTS.md](AGENTS.md)** first. It is the one-page working contract
(the prime directive and the non-negotiable rules), and it applies to humans
and AI tools alike. Then read [docs/ONBOARDING.md](docs/ONBOARDING.md) for the
current project state and a list of good first issues. Please follow the
[Code of Conduct](CODE_OF_CONDUCT.md).

## 0. Licensing of contributions

- Contributions are licensed under the project's **Apache License 2.0**.
  This is "inbound = outbound", as Section 5 of the License describes: by
  submitting a pull request you agree that your contribution is licensed
  under the same terms. There is no CLA. A DCO sign-off (`git commit -s`) is
  welcome but not required.
- Only submit work you have the right to license. Do not paste code from
  projects with incompatible licences. For data, every spec, price or
  benchmark must come from a citable public source and carry its source
  label; we never accept fabricated numbers.
- New source files don't need a per-file licence header. The repo-root
  `LICENSE` and `NOTICE` cover them.

## Ways to contribute

You do not need to touch the physics to help. In rough order of value:

1. **Instrumented timeslips and benchmarks.** Dragy / VBox / Racelogic runs of
   *stock* bikes, with a source (magazine test, video, timeslip photo, Dragy
   export). Small-displacement and two-stroke accuracy is limited mostly by
   data. Open a "bike / benchmark data" issue or a PR.
2. **Bike, part and tire data.** New bikes (`motoquant/scraper/known_bikes*.py`),
   corrections to existing specs, gear cassettes and primary ratios from
   service manuals, OEM tire fitments, parts and fitment rules.
3. **Bug reports and fixes.** Use the bug-report issue template; include the
   bike, venue, inputs and the number you expected.
4. **Docs, tests, tooling, web UI.** Anything that makes the above easier.

### The honest-data rule

Every spec, benchmark, price and gear ratio needs a **citable source** (service
manual, manufacturer spec sheet, magazine test, instrumented timeslip, retailer
page). **No fabricated numbers.** If you cannot source a value, leave it out
and say so: an honest gap beats apparent completeness. Estimates must be
labelled as estimates and must not be presented as measurements. Data PRs
without sources will be closed.

---

## 1. Repository

- **GitHub:** https://github.com/toto171/MotoQuant.in
- **Package name:** `motoquant` (formerly `dragsim` — do not reintroduce that string anywhere)
- **Python:** 3.10 or newer (tested on 3.10, 3.11, 3.12)
- **Primary DB:** SQLite (`motoquant.db`). It stays until a real scaling trigger ([ADR-0004](docs/adr/0004-sqlite-until-scale.md)).

---

## 2. One-time setup

Short version (the `Makefile` runs the same commands as CI):

```bash
make install   # pip install -e ".[dev]"
make health    # state of the world: baselines, lint, catalog, headline drift, secret scan
# ...work...
make check     # fast pre-PR gate (~3 min): lint + format + baselines + fast tests
make test      # full suite (~25 min), required before opening a PR
```

Longer version:

```bash
# 1. Fork on GitHub (or clone directly if you have write access)
git clone https://github.com/<you>/MotoQuant.in.git
cd MotoQuant.in
git remote add upstream https://github.com/toto171/MotoQuant.in.git

# 2. Virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate            # Windows PowerShell

# 3. Install the package, its runtime dependencies (requirements-api.txt) and
#    the dev extra (requirements-dev.txt: pytest, ruff, hypothesis, ...)
pip install -e ".[dev]"

# 4. (Optional) a scratch database. The repo already ships motoquant.db, the
#    full curated catalog; use that (read-only) for normal development.
#    `db init` + `db seed` build a STARTER database: the three reference bikes
#    (ids 1-3: K5, R1, Hayabusa) plus the tire library, parts and venues.
#    Seed FIRST so those three keep ids 1-3, then (optionally) import the
#    curated bike catalog on top. `make db` does the first two steps.
python -m motoquant.run --db /tmp/motoquant-dev.db db init
python -m motoquant.run --db /tmp/motoquant-dev.db db seed
python -m motoquant.run --db /tmp/motoquant-dev.db import --known-bikes   # optional

# 5. Run the focused test subset first (~3 min) — expect 0 failures
python -m pytest tests/test_validation.py tests/test_scraper.py \
    tests/test_database.py tests/test_agent.py -q

# The FULL suite is ~3k tests and takes 25-35 minutes; run it before any PR:
python -m pytest tests/ -q
```

If those are green, you're set.

A scratch database is **not** the shipped catalog, so its counts and some ETs
will not match the published ones. The shipped `motoquant.db` is produced by
maintainers: `import --known-bikes` on top of a seeded DB, then the idempotent
re-seed chain (`scripts/reseed_configs_from_specs.py` followed by the dated
`scripts/patch_*.py` scripts, in the order written out under "Re-seed chain"
in `CLAUDE.md`; see [docs/KNOWN_TRAPS.md](docs/KNOWN_TRAPS.md) T3 and T17),
then regenerating the regression snapshot and the surrogate. Run that chain only if you are changing
physics or importer behaviour.

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

Every subcommand has `--help` (`python -m motoquant.run <subcommand> --help`).

### 3b. Web frontend (the primary product UI)

```bash
cd web && npm install && npm run dev     # http://localhost:3000
```

Point it at a local API with `NEXT_PUBLIC_API_URL=http://localhost:8000` (else it
proxies to the production Render API); `make web-dev` does this for you. Before
committing anything under `web/`, run `make web-build` (= `npx next build`). It
is exactly what Vercel runs and catches the App-Router prerender class of
failure (see `web/CONTRIBUTING.md`).

The web app (`web/`) is the supported user interface. The legacy Streamlit UI
(`app.py`) and the discontinued desktop app (`desktop/`, ADR-0005) have both
been removed.

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
python -m pytest tests/test_validation.py::TestQuarterMileValidation::test_k5_quarter_mile_et -v
```

**Rules:**
1. Every new public function needs at least one test that would fail if the function did nothing.
2. Tests must use `:memory:` or `/tmp/` SQLite paths — never the production `motoquant.db`.
3. CLI tests import command handlers directly via `redirect_stdout` + `unittest.mock.patch` — do not spawn subprocesses (WAL journal mode fails on the mounted dev filesystem).
4. Physics regressions: the three reference baselines are pinned to 4 decimals — K5 **10.0436**, R1 **10.1092**, Hayabusa **10.1100** — and the expectation for refactors is **bit-identical** (Δ +0.0000). If you touch `motoquant/physics.py`, any `submodels/*.py`, `defaults.py`, or `motoquant/scraper/importer.py`: run the baseline check, `tests/test_regression_snapshot.py`, and put the delta table in your PR. A deliberate accuracy change needs the full weighted sweep (`scripts/phys_weighted_sweep.py`) as justification.
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
# 1. Start from an up-to-date main (fork: sync from upstream)
git checkout main && git pull upstream main     # or `git pull` if you cloned directly

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

# 4. Push to your fork + open a PR against toto171/MotoQuant.in:main
git push -u origin feature/<short-name>
```

Open PRs as **draft** until `make check` and `make test` are green, and fill in the
PR template (it has the baseline-delta table for physics-adjacent changes).

**PR requirements (strict — enforced by branch protection on `main`):**
- Tests pass locally (`python -m pytest tests/ -q`).
- Ruff clean (`ruff check . && ruff format --check .`).
- CI workflow green on the PR (pytest + ruff + baseline gate; the Next.js build for `web/` changes).
- **At least one approving review** from someone other than the PR author.
- For files owned via `.github/CODEOWNERS` (physics, schema, calibration, API, infra): the listed **CODEOWNER's approval is required** — GitHub will auto-request it.
- For physics changes: include the benchmark ET deltas in the PR description (template has a table for this).
- For schema changes: include the migration path. Existing DBs must keep working; ship an idempotent `scripts/patch_*.py` for the shipped `motoquant.db`. Update `docs/ARCHITECTURE.md` if the data model's shape changed.
- **No self-merge.** Even maintainers go through review on anything touching a CODEOWNER-protected path.
- `main` is protected: no direct pushes, no force-push, no deletion.
- Once merged, a successful CI run on `main` triggers the Vercel production deploy (`.github/workflows/deploy.yml`). A red CI never reaches Vercel.

**Commit message style** (look at `git log --oneline` for examples):
- Imperative mood, present tense: "Add …", "Fix …", "Refactor …"
- Subject line ≤ 72 chars, no trailing period.
- Body explains why, not what — the diff shows the what.

---

## 7. The Kaizen rule (read this before you PR)

*Every time you touch a file, leave it better than you found it.* Before marking a task complete, scan the files you modified for:

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
- Replace SQLite with PostgreSQL without a real scaling trigger ([ADR-0004](docs/adr/0004-sqlite-until-scale.md)). The WAL-fallback code is load-bearing on Windows / mounted FS.
- Reintroduce paywalls, tier gates, usage quotas or licence keys. MotoQuant is free ([ADR-0006](docs/adr/0006-open-source-pivot.md)). Protect expensive routes with per-IP rate limits instead (`motoquant/ratelimit.py`).
- Add BeautifulSoup / lxml to the scraper — `motoquant/scraper/bikez.py` is stdlib-only by design.
- Introduce `requirements.txt` separate from `requirements-api.txt` without discussing first. One dependency file avoids drift.

---

## 9. Where to ask questions

- GitHub Issues for bugs, data corrections and scoped work (they leave a trail).
- GitHub Discussions for questions and ideas.
- [docs/ONBOARDING.md](docs/ONBOARDING.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) first: most "where does X live?" questions are answered there.
- Before asking "is X done yet?", check `CHANGELOG.md` and `docs/ROADMAP.md`. (`CLAUDE.md` holds the exhaustive session log if you need to dig.)
- Security issues: report privately, see [SECURITY.md](SECURITY.md).

---

## 10. Release / deploy

The public instance is live: the API on Render (`motoquant-api.onrender.com`,
Docker via `render.yaml`) and the web app on Vercel (`motoquant.in`, with the
`/api/*` rewrite in `web/next.config.js` + `vercel.json` pointing at Render).

Merging to `main` IS the production deploy of the public instance. Render
rebuilds the API when the diff touches the backend (`motoquant/**`,
`motoquant.db`, the requirements files, the Docker files, `render.yaml` or the
Rust core under `rust/`; the exact list is the `buildFilter` in `render.yaml`,
so web-only merges do not restart the API),
and Vercel deploys the frontend on every merge. Hosting accounts belong to the
maintainers, so contributors never need credentials. To run your own copy,
follow [docs/SELF_HOSTING.md](docs/SELF_HOSTING.md). The historical Railway →
Render runbook is `docs/RENDER_MIGRATION.md`.
