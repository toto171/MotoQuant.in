# Session 2026-10-23: open-source pivot + Rust core (handoff)

The operator stopped the run early (usage budget). This file says what is
done, what is verified, and what to pick up next.

## Done and committed

1. **Open-source pivot.** Monetization is removed end to end:
   - backend: payments, subscriptions, usage metering, tier gates, license
     keys;
   - web: /pricing and /refunds now redirect; /contact, /account, /terms and
     /privacy are rewritten;
   - docs: README, CONTRIBUTING, NOTICE, CODE_OF_CONDUCT, SECURITY,
     SELF_HOSTING and ADR-0006;
   - deleted outright: desktop/ (scrapped app), outreach/ (guessed
     third-party contacts) and the monetisation plan.

   The code is now Apache-2.0. Abuse fuses replace the quotas: rate limits on
   distance/compare/jobs-compare, a per-IP daily chat cap, and a fix to
   rate-limit window eviction. The JWT default-secret guard was re-keyed (an
   ephemeral secret on deployed hosts). The dead tables were dropped from
   motoquant.db by `scripts/patch_2026_10_23_drop_monetization.py`, which is
   idempotent.
2. **Rust physics core** in `rust/motoquant-core`:
   - a PyO3 extension plus a raw-ABI wasm32 build at
     `web/public/engine/motoquant_core.wasm`;
   - Python resolves the config and Rust integrates it
     (`motoquant/native.py`);
   - full parity sweep: 1,874/1,874 cases bit-identical to Python (catalog
     fixed, adaptive and top-speed, plus 242 stress variants);
   - about 65× faster end to end;
   - not yet used by any route. Python is still the only engine in
     production paths.

   See `docs/RUST_CORE.md` and `reports/native_parity_2026-10-23.json`.

## Verified on the final tree

- `scripts/check_baselines.py`: all 3 references bit-identical (Δ = 0).
- `ruff check` and `ruff format --check` are clean.
- `next build` passes, 76/76 pages.
- Targeted pytest is green: auth, api, fuses, ratelimit, outlaw, agent, pivot,
  validation, mcp and cli.
- `tests/test_native_engine.py` passes 33/33; `cargo test` passes; quick
  native parity is 137/137 exact.
- The full 25-minute suite was **not** re-run after the pivot. Run
  `make test` first thing.

## Stopped mid-flight (not committed, redo next session)

- **Rust review fixes.** Reviewers found no physics divergence: 2,076
  parts-modified and 1,200 random configs matched. Their engineering findings
  are still open:
  - CI never builds or tests the Rust core: add a path-filtered cargo +
    maturin + parity job;
  - native reads `m_total` once at construction, while Python re-reads it
    every step;
  - no allocation cap on huge max_time/distance;
  - the wasm schema check is circular (it never reads the wasm's own
    export);
  - `make native-test` silently skips when the extension is missing or stale;
  - `make native-parity` defaults to 91 top-speed cases, not 541;
  - `loadEngine()` shares one promise across different URLs;
  - engine-parity.mjs ignores split/dt drift;
  - the maturin guard checks `import maturin`, not `python -m maturin`;
  - `.dockerignore` lacks `rust/target`.
- **Pivot completeness and regression critics** never ran. Grep the repo for
  pricing / subscription / license-key / BILLING / "MotoQuant Pro" leftovers.
- **Core audit:** `reports/audit_core_2026_10_23_partial.md` has 78
  findings. 7 were confirmed by two verifiers; the rest are unverified leads.
  Highest value:
  - **phantom engine inertia during clutch slip** (epoch; ~0.4-0.6 s per
    launch);
  - **N2O/boost density floor**;
  - **10 of 20 forced-induction parts deliver no FI power**;
  - **2T expansion-chamber parts make bikes slower**;
  - autotune launch-RPM sweep is a no-op for 4T bikes;
  - CLI `sim` exits 1 and dumps the repr;
  - SSRF backslash bypass;
  - Dragy parser is quadratic (a DoS).

## Next steps (in order)

1. `make test`, then fix anything red.
2. Wire native: one engine factory with Python fallback, a
   `MOTOQUANT_ENGINE` kill switch, and engine info in `/api/health`. Also a
   multi-stage Docker build and a CI parity gate. Rewrite the numpy knapsack
   (the outlaw pipeline spends 6.5 s in the Python DP).
3. Apply the verified safe audit fixes, each with a regression test.
4. Accuracy epoch, using the native engine for fast tuning (see the accuracy
   brief in this session's notes):
   - freeze a reference profile so the pins are safe;
   - clean up the benchmark data;
   - then one epoch: drop the sport Cd×0.55 normalisation, set the 4T crank
     recal to 1.00, add 1-ft rollout and remove the phantom slip inertia;
   - multi-knob per-cluster retune on a joint ET + trap objective.

   Expected outcome:
   - ET w|d| roughly flat to better (currently 0.2629 s);
   - trap bias +13.8 → about +4 km/h;
   - top-speed error about halved.

## Operator actions (cannot be done from a session)

- **Rotate the OpenWeatherMap API key.** `/api/venues/resolve` echoes it in
  upstream error messages (fix pending; a fix exists in PR #119).
- **Before making the repo public:** fix or delete
  `.github/workflows/deploy.yml`. Its `workflow_run` trigger runs untrusted
  fork code with `VERCEL_TOKEN` (a pwn-request pattern).
- Decide what happens to open PRs: #124 (commercial launch, now
  contradictory) and #125 (release prep — its LICENSE-DATA/CITATION.cff/
  DATA_PROVENANCE files are worth cherry-picking).
- Flip repo visibility when ready. The history secret scan was clean, but
  commit metadata exposes author emails.
