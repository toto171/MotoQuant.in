# Invariants: what must never break

The guarantees the rest of the code depends on. Each has a **why** and an
**enforcement**, the automated gate that catches a violation. If you change an
invariant on purpose, change its enforcement and this doc in the same PR.

## I1: Reference baselines are bit-identical

**What.** `GSX-R 1000 K5 = 10.0436 s`, `YZF-R1 4C8 = 10.1092 s`,
`Hayabusa Gen1 = 10.1100 s` (full precision in `scripts/check_baselines.py`).
A refactor must produce Δ = 0.0000. The deliberate 2026-10/11 accuracy epoch
re-pinned them on 2026-11-05 (previous pins 9.9331 / 10.1436 / 10.3633;
evidence in `reports/acc_final_2026_11_05.json`). Since that epoch, ET is
timed from the 1-ft beam rollout: ET = t(402.336 m) − t(0.3048 m).

**Why.** These three are the only hand-curated, human-validated configs, and
the whole physics model is trusted against them. If a "harmless" refactor
moves them, it changed the physics without anyone noticing.

**Enforcement.** `make baselines` / `scripts/check_baselines.py` (exit 1 on
drift), the `Physics baselines — bit-identical gate` CI step, and
`tests/test_regression_snapshot.py`. A deliberate accuracy change is allowed,
but it must ship the full weighted sweep (`scripts/phys_weighted_sweep.py`) as
evidence and update the pinned values everywhere at once.

## I2: The DB is a cache of the specs and must not drift from them

**What.** `bike_configs` JSON blobs must equal the current output of
`spec_to_bike_config`. `/api/simulate?bike_id=N` (DB path) must match the sweep
(spec path).

**Why.** When `importer.py` or the physics change, stored blobs go stale and
the DB path silently drifts by seconds per bike. Nobody sees it until someone
diffs.

**Enforcement.** Re-run `scripts/reseed_configs_from_specs.py` after any
change to the specs, the importer or the physics.
`tests/test_db_gearing_integrity.py` and the regression snapshot guard the
contract. The 3 reference bikes are excluded from the reseed on purpose,
because they come from `defaults.py`.

## I3: Parts never leak across brands or segments

**What.** A part fits only the bikes its fitment rule allows (manufacturer +
engine config + displacement + chain pitch + stroke type). No RE-650 exhaust on
an RE 350; no Hayabusa system on a Panigale.

**Why.** Correct compatibility is the product. A single leak makes the whole
recommender untrustworthy.

**Enforcement.** `tests/test_catalog_integration.py`, `test_compatibility.py`,
`test_parts_integrity.py` (leak scans across the full catalog).

## I4: The analysis layer honours the injectable-repo seam

**What.** `compute_parts_roi` / `find_best_build` apply parts through the
`parts_repo` they are given, so a test stub or alternate repo controls how a
part changes a config. Do **not** shortcut to the concrete
`bridge.apply_part_to_config`.

**Why.** The seam makes the optimizer testable and swappable. Bypassing it
broke `test_parts_integrity` in PR #99, and the change was reverted.

**Enforcement.** `tests/test_parts_integrity.py::TestSprocketPositionExclusivity`.

## I5: The surrogate is a cache of the physics; regenerate it after any reseed

**What.** After a reseed or retune, regenerate the numpy surrogate
(`artifacts/surrogate/`) in the same change. A stale surrogate lies.

**Why.** The build optimizer scores in-envelope candidates through the
surrogate, so a stale one silently returns wrong ETs.

**Enforcement.** The standing contract in `artifacts/surrogate/README.md` and
the surrogate envelope tests. CI does not fully automate this; it relies on
discipline.

## I6: Headline stats agree across the site

**What.** Bike, part, tire, fitment and benchmark counts quoted in web pages,
README and docs match the DB and `BENCHMARKS`.

**Why.** Inconsistent public numbers cost credibility and confuse
contributors.

**Enforcement.** `scripts/audit_headline_stats.py` (`make audit`), the health
check, and the release checklist.

## I7: Security guarantees

- Everything is free, and per-IP fuses replace quotas. There are no tiers, no
  quota and no payment code (ADR-0006). Every compute-heavy public route
  carries a `rate_limit(...)` dependency, and chat also has a per-IP daily cap
  (`MOTOQUANT_CHAT_DAILY_LIMIT`, default 200; `0` disables), which is the fuse
  on the LLM bill. Rate-limit buckets expire on their own window, so a
  short-window call can never evict a daily counter. Enforced by
  `tests/test_public_route_fuses.py`, `tests/test_chat_fuses.py` (the chat
  agent's heavy tools draw on the optimize bucket; classic chat has its own
  tighter one), `tests/test_ratelimit.py::TestPerKeyWindows`,
  `tests/test_open_source_pivot.py::TestChatDailyCap`, and
  `tests/test_open_source_pivot.py::TestMonetizationIsGone` (no payment or
  subscription routes, no quota headers, no paywall can creep back).
- The client IP for rate limiting is the N-th `X-Forwarded-For` hop from the
  right, where N is the number of trusted proxy hops
  (`MOTOQUANT_TRUSTED_PROXY_HOPS`; unset means 1 on Render or behind a
  loopback/unix/private-network proxy, and 0 otherwise, which keys on the
  socket peer). The client can spoof the leftmost hop, so it is never used.
  `client_ip()` in `motoquant/ratelimit.py` implements this. Enforced by
  `tests/test_fixwave_sec_xff.py` (multi-hop selection, spoofing without a
  trusted proxy, invalid values failing closed) and
  `test_x_forwarded_for_distinguishes_clients` in `tests/test_ratelimit.py`.
- `web_fetch` re-checks the SSRF guard on every redirect hop and bounds the
  whole chain to one timeout. Any server-side fetch of a URL that a user or
  the LLM controls must do the same. Enforced by `tests/test_webtools_ssrf.py`.
- There are no accounts, and nothing a visitor sends is shown to other
  visitors. Saved runs stay in the browser; timeslips re-simulate the setup in
  their link, so a shared time is always one the physics produced. The POST
  routes are an explicit allow-list of computations, and no route accepts PUT,
  PATCH or DELETE. Enforced by `tests/test_open_source_pivot.py`
  (`TestNoAccounts`, `TestPublicWriteSurface`).
- SQL is always parameterized: no f-string or format into queries with user
  data.
- No secrets in tracked files. Enforced by the `scripts/health_check.py`
  secret scan, which also runs as the first step of the CI job.

## I8: Tests exercise the production path

**What.** A regression test must fail if you revert the real fix. It must
drive the actual code path (DB round-trip, HTTP request, CLI subcommand), not
re-implement the fix inside the test.

**Why.** A tautological test still passes after the bug returns.

**Enforcement.** Code review and this doc. When you add a regression test,
ask: would this fail on a `git revert` of the fix?

## I9: The docs do not promise what the tree does not have

**What.** In the live docs (README, CONTRIBUTING, AGENTS, SECURITY, the
`docs/` guides, the `skills/motoquant` reference): every relative link
resolves, every `make` target and CLI subcommand named exists, every
CODEOWNERS pattern matches a tracked file, the packaging metadata matches the
files it points at, the licence named is the one the repository uses
(Apache-2.0), there is one version number (`motoquant.__version__`), and the
retired product wording (paid tiers, the old "Pro" name, usage quotas) does
not appear.

**Why.** Each of these has drifted at least once: a setup recipe that
installed no dependencies, a `make` target that did not exist, a CODEOWNERS
path with no file behind it, two different licences named in two places.

**Enforcement.** `tests/test_docs_truth_2026_11.py` (in `make test-fast` and
the PR fast tier) and the `Docs truth` workflow, which runs it on docs-only
changes that the code-filtered CI would skip.
