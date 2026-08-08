# Invariants — what must never break

The load-bearing guarantees of this codebase. Each has a **why** and an
**enforcement** (the automated gate that catches a violation). If you change an
invariant deliberately, change its enforcement and this doc in the same PR.

---

## I1 — Reference baselines are bit-identical

**What.** `GSX-R 1000 K5 = 9.9331 s`, `YZF-R1 4C8 = 10.1436 s`,
`Hayabusa Gen1 = 10.3633 s` (full precision in `scripts/check_baselines.py`).
Refactors must produce Δ = 0.0000.

**Why.** These three are the only hand-curated, human-validated configs. They
are the fixed point the whole physics model is trusted against. If a "harmless"
refactor moves them, it changed the physics — silently.

**Enforcement.** `make baselines` / `scripts/check_baselines.py` (exit 1 on
drift), the `Physics baselines — bit-identical gate` CI step, and
`tests/test_regression_snapshot.py`. A *deliberate* accuracy change is allowed
but must ship the full weighted sweep (`scripts/phys_weighted_sweep.py`) as
justification and update the pinned values everywhere at once.

## I2 — The DB is a cache of the specs, and must not drift from them

**What.** `bike_configs` JSON blobs must equal the current output of
`spec_to_bike_config`. `/api/simulate?bike_id=N` (DB path) must match the sweep
(spec path).

**Why.** When `importer.py`/physics change, stored blobs go stale and the DB
path silently diverges by seconds per bike — invisible until someone diffs.

**Enforcement.** Re-run `scripts/reseed_configs_from_specs.py` after any
spec/importer/physics change; `tests/test_db_gearing_integrity.py` and the
regression snapshot guard the contract. (The 3 reference bikes are intentionally
excluded from reseed — they come from `defaults.py`.)

## I3 — Parts never leak across brands/segments

**What.** A part fits only bikes its fitment rule allows (manufacturer +
engine config + displacement + chain pitch + stroke type). No RE-650 exhaust on
an RE 350; no Hayabusa system on a Panigale.

**Why.** Compatibility correctness is the product. A single leak makes the whole
recommender untrustworthy.

**Enforcement.** `tests/test_catalog_integration.py`, `test_compatibility.py`,
`test_parts_integrity.py` (leak scans across the full catalog).

## I4 — The analysis layer honours the injectable-repo seam

**What.** `compute_parts_roi` / `find_best_build` apply parts via the passed
`parts_repo` (so a test stub / alternate repo controls how a part mutates a
config). Do **not** shortcut to the concrete `bridge.apply_part_to_config`.

**Why.** The seam is what makes the optimizer testable and swappable. Bypassing
it broke `test_parts_integrity` in PR #99 (reverted).

**Enforcement.** `tests/test_parts_integrity.py::TestSprocketPositionExclusivity`.

## I5 — The surrogate is a cache of the physics; regenerate after any reseed

**What.** After a reseed / retune, regenerate the numpy surrogate
(`artifacts/surrogate/`) in the same session. A stale surrogate lies.

**Why.** The build optimizer scores candidates through the surrogate when
in-envelope; a stale one silently returns wrong ETs.

**Enforcement.** Standing contract in `artifacts/surrogate/README.md` +
surrogate envelope tests. (Not fully CI-automated — a discipline gate.)

## I6 — Headline stats are consistent sitewide

**What.** Bike/part/tire/fitment/benchmark counts quoted in web pages, README,
and docs match the DB and `BENCHMARKS`.

**Why.** Inconsistent public numbers erode credibility and confuse contributors.

**Enforcement.** `scripts/audit_headline_stats.py` (`make audit`), the health
check, and the release checklist.

## I7 — Security guarantees

**What / Why / Enforcement.**
- **Webhooks fail closed.** Unset signing secret ⇒ reject, never trust. (Stripe
  + Razorpay signature verification, constant-time.) — `tests/test_payments.py`.
- **Client IP for rate-limit/quota = rightmost `X-Forwarded-For` hop** (single
  trusted proxy). The leftmost is client-spoofable. Implemented in
  `client_ip()` (`motoquant/ratelimit.py`). **Partially enforced:**
  `test_x_forwarded_for_distinguishes_clients` in `tests/test_ratelimit.py`
  pins that the header is used for keying, but it sends a *single-hop* value,
  so it cannot tell rightmost from leftmost; nothing currently pins the hop
  selection, and `tests/test_api.py` (named here previously) has no
  `X-Forwarded-For` test at all. A multi-hop case is the missing pin.
- **`web_fetch` re-checks the SSRF guard on every redirect hop** and bounds the
  whole chain to one timeout. Any server-side fetch of a user/LLM-controlled URL
  must too. — `tests/test_webtools_ssrf.py`.
- **`motoquant.auth` refuses to *import* while `JWT_SECRET` is the public
  default and `MOTOQUANT_BILLING_ENFORCE` is truthy** — a forgeable signing key
  in commercial mode is a free self-upgrade to any paid tier. With billing off
  (the shipped open-beta posture) the same condition only logs a warning, since
  hard-failing there would take the live beta down over a documented
  pre-commercial TODO. The guard keys on the secret's *value*, not on whether
  the env var was set. — `tests/test_auth.py::TestJwtDefaultSecretBootGuard`
  (boots a fresh interpreter per case; the guard is module-level code, so
  reload/monkeypatch would test a re-implementation instead).
- **SQL is always parameterized.** No f-string/format into queries with user
  data.
- **No secrets in tracked files.** — `scripts/health_check.py` secret scan,
  which also runs as the first step of the CI job.

## I8 — Tests exercise the production path

**What.** A regression test must fail if you revert the real fix — i.e. it must
drive the actual code path (DB round-trip, HTTP request, CLI subcommand), not
re-implement the fix inside the test.

**Why.** Tautological tests pass even after the bug returns.

**Enforcement.** Code review + this doc. When adding a regression test, ask:
"would this fail on `git revert` of the fix?"
