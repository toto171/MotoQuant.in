# Session Report — 2026-07-02 — Codebase audit + launch hardening

Multi-agent audit (14 subsystem finders → adversarial verification of every
critical) across physics, importer, database, parts, API, auth/payments,
analysis, calibration, LLM/chat, desktop, web, and DB data quality. Findings
were fixed in batches, each verified against the reference baselines
(**K5 10.0334 / R1 10.2859 / Hayabusa 10.4712, Δ+0.0000**) and the affected
test suites. Shipped on `claude/motoquant-audit-release-u4jmug`, PR #89 (draft).

## Commits

1. `a574c58` — physics accuracy + API/security hardening + launch features (batch 1)
2. `763be40` — ruff-clean the sweep/patch scripts (pre-existing lint, fixes the CI "Python tests + lint" check)
3. `2c597da` — ci.yml web-build npm cache path fix (`web/pack` → `web/package-lock.json`)
4. `a3c5d31` — id-preserving upsert in tire_repo/parts_repo (batch 2a)
5. `a7c7951` — year-aware reseed matcher, stop collapsing multi-generation bikes (batch 2b)

## Confirmed criticals fixed

| # | File | Defect | Fix |
|---|------|--------|-----|
| C1 | database/{schema,connection,bridge,bike_repo}.py | `category_tag` dropped on DB round-trip → 44 bikes ran a different cluster profile on `/api/simulate` than the sweep | schema v6 column + migration + bridge round-trip + reseed |
| C2 | scraper/gear_ratios.py | `yzf-r1` substring-leaked its litre primary onto R15 V1/V2 + R125 | digit-boundary matcher guard + explicit Tier-1 entries; de-duped 4 shadowed overlapping-year entries |
| C3 | database/tire_repo.py + parts_repo.py | `INSERT OR REPLACE` deletes+re-inserts → FK crash on 2nd `seed_all()` w/ fitments; wipes part_prices | id-preserving SELECT-then-UPDATE-or-INSERT |
| C4 | payments.py + subscriptions.py | Stripe/Razorpay webhooks fail OPEN on unset secret → forged tier-upgrades while checkout live | fail CLOSED; tests updated |
| C5 | auth.py + users_repo.py | unsigned `dev.` token bypass reachable in prod; sessions not bound to token subject | gate `dev.` to jose-absent; bind session to `sub` |
| C6 | api.py | unbounded `max_time_s` memory-bomb on top-speed/distance | `Field(le=300)` |
| C7 | seed_catalogs/indian_retailer_depth.py | 5 sprockets used additive `param_deltas` (16T→33 teeth); 3 fuel pumps had a dead param path (pure mass penalty) | absolute `param_overrides` for sprockets; conservative valid delta for pumps |
| C8 | scripts/reseed_configs_from_specs.py | 25 base models collapsed all generations to the last spec; asymmetric year-strip mis-bound siblings | year-aware `_pick_generation` by year-range overlap; re-seeded (498 configs) |

## Accuracy (full 502-bike weighted sweep)

- HEAD baseline: weighted |Δ| **0.2623 s**, bias −0.015 s (236 matched).
- This PR: weighted |Δ| **0.2486 s** (−5.2%), bias −0.027 s (236 matched). Per-cluster: `other` 0.383→0.309, `cruiser-1300+` 0.312→0.234, `litre-sport-600-1000` 0.201→0.197 (data-limited clusters entry-150-200 / mid-twin-300-500 / two-stroke unchanged — model at ceiling, gated on Dragy data per prior sessions).
- High-power cruiser/ADV grip gate (≥165 hp on sport radials): Diavel V4 +0.80→+0.19 s; Multistrada V4/RS, Rocket 3 Storm R, S1000XR.
- Kerb→dry mass: Multistrada V4 243→218, Diavel V4 223→211, CB1100 248→237.
- Benchmark corrections: Ninja 1000 '11 11.30→10.40, Daytona 675 10.32→10.70.
- Rear-tire rim regex: 32 non-17" bikes (Sportster S, Rocket 3, VMAX, ADVs) no longer default to a 17" rim.
- Multi-generation configs now distinct (GSX-R 1000 178/185/183/202 hp across gens instead of one collapsed value).
- A graduated sport-tuck experiment REGRESSED small-cc clusters on the full sweep and was rejected (kept flat ×0.55).

## Commercial-launch features (see docs/COMMERCIAL_LAUNCH.md)

- Free-tier sim metering: `motoquant/usage.py` + `sim_usage` table; records always, blocks only when `MOTOQUANT_BILLING_ENFORCE`; `X-Sims-Remaining` header.
- Per-IP rate limiting: `motoquant/ratelimit.py` on `/api/chat`, `/api/optimize/build`, `/api/autotune/ecu` (LLM-token + CPU cost fuse).
- Public shareable run pages: `GET /api/runs/{id}` + `/r/[id]` timeslip with OG/WhatsApp share cards.
- Venue-filtered leaderboard: `GET /api/leaderboard?venue_id` + `/leaderboard` page.
- PostHog telemetry forwarding (env-gated; no behavior change without key).

New tests: `test_usage` (14), `test_ratelimit` (8), `test_parts_integrity` (9), `test_accuracy_2026_07_02`. Fixed a pre-existing `test_api.py` `MOTOQUANT_DB` env leak that poisoned later modules; conftest resets the rate limiter between tests.

## Deferred confirmed/high findings (follow-ups, NOT fixed this session)

Documented so nothing is lost. Rationale per item:

- **environmental.py `track_surface` dead knob** (accuracy): grip/rr multipliers computed but never applied to the sim, so wet/salt/prepped surfaces produce identical ET. Fix wires `total_grip_multiplier()` into `TireModel.friction_coeff()`. Deferred: needs careful multi-bike validation to keep the baselines pinned. Also a second dead knob: `api.py` sets `surface_grip_multiplier` on a field `EnvironmentParams` doesn't define.
- **recommendations/roi sprocket exclusivity** for 14 parts missing `specifications.position`, and **brakes/suspension** not in `EXCLUSIVE_CATEGORIES`. Deferred: a correct fix needs part sub-typing (data project); for a drag-ET optimizer these parts are near-ET-neutral so stacking is rarely triggered. Blanket category exclusivity would wrongly forbid legitimate component combos (caliper + pads).
- **importer `_build_drivetrain` shaft/belt sentinel**: `front_sprocket=0/rear_sprocket=0` (documented shaft/belt marker) is treated as "missing" and a chain final-drive is fabricated for BMW R/K, Indian, HD, Moto Guzzi. Use `is not None` checks.
- **physics dead knobs** (documented model choices, not regressions): `pacejka_force()` unused (hard-clip traction), clutch-type dispatch bypassed (inline SLIDER only), `staging` dead-time/rollout not applied, 9/13 `CategoryProfile` knobs unread, wheel-dyno curve treated as gear-independent.
- **LLM/chat**: `nlp._extract_bike` truncates multi-word names (regex ≤2 words); `resolver` tokenizer doesn't split letter/digit (RC200/ZX10R); `choose_bike` `prefer_indian` references stale 'Indian Motorcycle'; `ChatResult.to_dict()` drops `choose_bike_result`.
- **desktop HistoryPage** shows **every user's** saved runs, not the signed-in user's own — a privacy leak worth fixing before launch (desktop session territory).
- **web** (parallel session territory): `SimulatorWidget` stale hardcoded bike-id fallback; `EcuAutotune` drops resolved altitude/pressure/lat-lon.
- **auth**: license-key device binding is write-only (records first device, never checks on re-validate); unbounded failed-login map keyed by attacker email; password-login timing side-channel (email enumeration).
- **analysis/sweep tooling**: `sobol.final_drive_ratio` + `bayesian_opt.gearing_ratio_delta` are dead knobs (charged budget); `topspeed_sweep` matcher binds wrong variant; `source_weight()` disagrees with `sweep_lib.source_quality()` on 27% of sources.

Full finder output: workflow `wf_9437340b-355` journal. 54 high/medium/low findings total (25 high).

## Pre-existing CI failures — need OPERATOR action (not regressions from this PR)

- **deploy-preview** (GH Actions): `Error: --token missing a value` — `VERCEL_*` secrets not configured on the repo. Vercel's own GitHub integration deploys fine (preview "Ready"). Either add the secrets or drop this redundant GH-Actions deploy job.
- **Sidecar smoke test (Linux)**: `desktop/sidecar/requirements-sidecar.txt` not found — the sidecar was removed by the hosted-only re-architecture (b52f4b5) but `ci.yml` still runs the job. Restore the sidecar (per priority #3) or gate/remove the job. Left in place because CLAUDE.md priorities intend to restore the sidecar.

Both fail identically on `main`.

## Verification

- Baselines K5/R1/Hayabusa Δ+0.0000 after every batch (×many).
- Affected battery: 3125 passed / 0 failed (physics, catalog, api, jobs, auth, payments, subscriptions, usage, ratelimit, parts_integrity, accuracy, recommendations, build_optimizer, ecu_autotune, database, catalog_integration).
- `ruff check .` + `ruff format --check .` clean repo-wide.
- `audit_headline_stats.py` in sync.
- DB regen order (all idempotent): `reseed_configs_from_specs.py` → `patch_2026_06_13_merge_manufacturers.py` → `patch_2026_06_11_parts_fitment.py`.
