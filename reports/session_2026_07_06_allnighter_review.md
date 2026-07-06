# All-nighter codebase review — 2026-07-06

**Model:** claude-fable-5 (remote session). **Branch:**
`claude/motoquant-review-optimize-tf4w0e`. **Goal:** find/fix bugs and
vulnerabilities, and make the repo navigable for a new human/LLM.

Method: a 7-dimension review workflow (security, api-robustness,
physics-analysis, database, async-llm, perf-memory, structure) — each
dimension reviewed then every finding adversarially verified by an
independent skeptic. 44 raw findings → 20 refuted → **24 survived** (1 high,
3 medium, 20 low). Plus an independent security pass on auth/payments/CORS/SSRF.

Reference baselines held **bit-identical** throughout: K5 10.0334 / R1 10.2859
/ Hayabusa 10.4712.

## Fixed (6 commits, each test-verified)

| # | Area | What | Severity |
|---|---|---|---|
| 1 | `llm/webtools.py` | **SSRF** — `web_fetch` followed 3xx redirects unchecked; an allowed public page could 302 to cloud-metadata / localhost / RFC-1918. Now re-validates every hop, bounds the chain to one total timeout, and closes the leaked `stream=True` response. +11 tests. | high |
| 2 | `api.py` | `/api/leaderboard` + `/api/me/runs` `limit=-1` → SQLite unbounded table dump (added `ge=1`); Simulate/QuickSim/TopSpeed/Distance/Compare accepted impossible power/mass/rider values → `ET=0.0` as 200 (bounded to match paid routes); free-quota identity switched to rightmost XFF hop. +9 tests. | medium |
| 3 | `ratelimit.py`, `auth.py` | Rate-limiter keyed on the spoofable **leftmost** XFF hop → trivially bypassable cost fuse (billing/service DoS); now uses the rightmost hop. JWT: refuse to boot on the public default secret when billing is enforced (warn otherwise). | high |
| 4 | `jobs.py` | Hung worker held a `MAX_RUNNING` slot forever → 6 hangs 503 everyone. Jobs past `MAX_JOB_RUNTIME_S` stop counting toward the pool + get cancel-requested. +2 tests. | high (async) |
| 5 | `analysis/roi.py` | Documented why `compute_parts_roi` routes per-part apply through the repo seam (an earlier "optimisation" broke the injectable-repo contract — caught by `test_parts_integrity`). | — |
| 6 | docs | `docs/ARCHITECTURE.md` (module map + data-flow diagram + "where to change X" + baseline invariant), `docs/README.md` index, README "root files you can ignore" table, ONBOARDING read-order fix. | structure |

## Deferred (with rationale — for the operator / next session)

Real but intentionally not changed in an all-nighter:

- **`database/connection.py:57` / `api.py:134` — single SQLite connection shared
  across request + job-worker threads** (`check_same_thread=False`). CONFIRMED
  contention hazard under concurrency. Bounded today by the single-worker Render
  deploy; the jobs.py fix reduces concurrent pressure. A proper fix (per-thread
  connections or a small pool) is an architectural change — do it before scaling
  to multiple workers. **Medium/high.**
- **`database/bike_repo.py:199` (also venue_repo, tire_repo) — `cur.lastrowid == 0`
  misread after `INSERT OR IGNORE`.** CONFIRMED. Import/seed path only, guarded by
  a dedup pre-check and idempotency tests; no runtime-request impact. Prefer
  `cur.rowcount == 0` as the "was ignored" signal. Touch carefully — it's the
  recurring catalog-idempotency code. **Medium.**
- **`database/users_repo.py:131` `consume_magic_link` + `:48` `get_or_create_user`
  — check-then-act races.** Low likelihood on the shared single connection; a
  clean fix wants a transaction / `INSERT ... RETURNING`. **Low.**
- **`subscriptions_repo.py:197` — license device-binding skipped when `device_id`
  omitted.** Latent (license keys inert during the billing-off beta). Reject or
  bind-on-first-use before commercial launch. **Low.**
- **`ratelimit.py` `_MAX_KEYS` overflow fails OPEN (`_WINDOWS.clear()`)** — a
  distinct-key flood wipes legitimate counts. Consider fail-closed. **Low.**
- **`category_profiles.py` dead knobs** (`chain_efficiency_override`,
  `cd_ceiling`, `engine_inertia_mult`, `pacejka_C`, `load_sensitivity_k`,
  `tuck_transition_time_s`) — written, never read. Matches the CLAUDE.md
  epoch-gated list; wiring them moves the pinned baselines, so leave gated. **Low.**
- **Perf (all low, all skipped to protect the bit-identical baselines / because the
  hot cost is elsewhere):** `physics.py:748` reads `total_mass_kg` property each
  RK4 step; `:496` over-allocates output arrays under adaptive dt; `:952`
  O(n·window) plateau scan; `importer.py:1070` builds the K5 reference config 6×
  per import (seed path); `sobol.py:291` deepcopies the full config per sample.
- **`api.py:1476` `simulate_distance`** — `max(sim.v)` / `sim.t[idx]` unguarded
  against an empty solver result (would 500 not 4xx). PLAUSIBLE, low. Quick guard
  worth adding.
- **`agent.py:1256` — no per-step tool-call cap.** Mitigated by the executor's
  sim/heavy budgets + the 30s LLM timeout + web_fetch's total timeout. **Low.**

Refuted (false positives worth recording): `sim_repo.leaderboard`'s
`HAVING = MIN()` is **correct** — SQLite's documented bare-column min/max
optimisation makes it return the min-ET row (empirically verified).

## Verification
- Full pytest suite green (serial, matching CI). Note: under `pytest -n` (xdist)
  ~15 DB-backed "Live" tests flake from shared-DB/env parallelism — a
  pre-existing suite property, not these changes; all pass serially.
- ruff check clean across `motoquant/` and `tests/`.
- Baselines K5/R1/Hayabusa bit-identical after every change.
- `motoquant.db` reverted to HEAD (only SQLite page churn from test opens — no
  content change).
