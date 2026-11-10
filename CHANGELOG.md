# Changelog

Notable changes, newest first. Investigation write-ups that entries cite are
in `reports/`. Format loosely follows [Keep a Changelog](https://keepachangelog.com).

## [2.0.0] — 2026-11-10 — Open source, no accounts, Rust core, accuracy epoch, plain-language site

MotoQuant 2.0 is the first release as free, open-source software under the
**Apache License 2.0** ([LICENSE](LICENSE), [NOTICE](NOTICE),
[ADR-0006](docs/adr/0006-open-source-pivot.md)). Copyright 2026 Hritwik Mudhai
and the MotoQuant contributors. Source: <https://github.com/toto171/MotoQuant.in>.
Monetization is scrapped; no payment was ever taken and the billing switch was
never enabled.

The release combines two lines of work that were developed in parallel and then
merged: PR #126 (open-source pivot, Rust physics core, accuracy epoch, audit
fixes) and PR #127 (site redesign, a second audit, catalog clean-up). Their
write-ups are `reports/session_2026_11_05_handoff.md`,
`reports/session_2026_11_10_v2.md` and `reports/session_2026_11_10_epoch.md`.

**Numbers on the released tree.** Catalog: 534 bikes, 546 parts, 254 tyres,
1,765 tyre fitments, 20 venues. Accuracy (`reports/acc_final_2026_11_10.json`):
250 published benchmarks and 263 bike-to-benchmark matches, weighted mean error
0.2495 s, bias +0.0226 s, 72 within 0.10 s and 130 within 0.20 s; trap-speed
bias +3.5 km/h. Top speed (`reports/sweep_topspeed_2026-11-10.json`): 83
matched, mean error 12.7 km/h, bias +6.8 km/h.

### Added — open source
- `LICENSE` (Apache-2.0, unmodified), `NOTICE` (copyright; third-party
  trademarks; cited benchmark figures; public-source catalog specs; bundled
  fonts), `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1), `SECURITY.md`
  (private reporting via GitHub Security Advisories), an open-source README
  and CONTRIBUTING (inbound = outbound, no CLA; the honest-data rule), issue
  and PR templates.
- `docs/SELF_HOSTING.md`: run the API and the site locally, on Render and
  Vercel or on any Docker host, with the optional keys for chat, live
  weather, Sentry and PostHog.
- One version number, `motoquant.__version__` (2.0.0), read by
  `pyproject.toml`. `pip install -e ".[dev]"` installs the package with its
  runtime dependencies (`requirements-api.txt`) and the developer tools
  (`requirements-dev.txt`); `make install` runs exactly that.
- Abuse fuses where the sim quota had been the only protection: per-IP rate
  limits on every compute-heavy route, plus a per-IP daily chat cap
  (`MOTOQUANT_CHAT_DAILY_LIMIT`, default 200; `0` disables) as an LLM-bill
  fuse.
- Gates: `tests/test_docs_truth_2026_11.py` (links, `make` targets, CLI
  subcommands, CODEOWNERS patterns, packaging metadata, licence and retired
  wording in the live docs); the CI secret scan; `scripts/check_gearing_plausibility.py`
  with a committed baseline.

### Added — Rust physics core
- `rust/motoquant-core` ([ADR-0007](docs/adr/0007-rust-physics-core.md),
  [docs/RUST_CORE.md](docs/RUST_CORE.md)): a second implementation of the
  integrator, **bit-identical** to the Python reference on every catalog bike
  (fixed step, adaptive step and top speed) and on the stress set; the parity
  record is the newest `reports/native_parity_*.json`. Python stays the
  reference: policy (category dispatch, defaults, parts, environment) is
  resolved in Python and only the loop is ported.
- `motoquant/engine_select.py` runs every simulation on the Rust core when it
  is installed, current and exact on the host, and on the Python engine
  otherwise (`MOTOQUANT_ENGINE=auto|python|native`; `/api/health` reports
  which engine is live and why). The Docker image builds the core in a first
  stage; `pip install -e .` does not need a Rust toolchain (`make native`
  builds the optional extension).
- The same core compiled to WebAssembly (`web/public/engine/`, loaded by
  `web/lib/engine.js`), with parity proven under node (`make wasm`).
- `make native`, `native-test`, `native-parity`, `native-parity-quick`,
  `wasm`, and the `Native core` CI workflow that gates parity.

### Changed — physics: the 2026-10/11 accuracy epoch (pins moved)
A deliberate epoch under [ADR-0002](docs/adr/0002-pinned-reference-baselines.md),
with the full weighted sweep as evidence (`reports/acc_final_2026_11_05.json`;
tuning record `reports/acc_epoch3_2026_11_03.json`).

- **Timing.** Every split is now clocked from the 1-ft stage beam:
  ET = t(402.336 m) − t(0.3048 m), the convention of timeslips, North American
  magazine tests and Dragy. Benchmark rows timed from first motion are scored
  against a first-motion sim. The finish line is `distance`; `distance <=
  rollout_m` or a non-finite rollout raises `ValueError` on both engines.
- **Launch physics.** The wheelie limit uses the combined bike + rider centre
  of mass (rider shift included); the aerodynamic drag pitch moment enters the
  load transfer; the tyre runs a heat balance (rolling-loss heating, partition,
  convection). 599 cc inline-four supersports route with the 600–1000 class.
- **One new knob,** `CategoryProfile.wheelie_margin`: the share of the wheelie
  ceiling the rider holds from rest to the 60-ft line (1.0 = bit-identical
  no-op). Every cluster was re-selected from neutral (grouped 5-fold CV, 1-SE
  rule, hard dry-mass gate) and the class grip correctors are retired: every
  cluster runs rated rubber. `litre_sport_195p` ships the CV choice (margin
  0.69) by owner decision 2026-11-05, accepting two millisecond-level dry-mass
  inversions.
- **New pins: K5 10.0436 s, R1 10.1092 s, Hayabusa 10.1100 s** (were 9.9331 /
  10.1436 / 10.3633). K5 60 ft is 1.896 s from the beam (2.184 s from first
  motion). Two earlier retunes in this epoch were measured and rejected
  (round 1 left catalog bikes dry-mass-inverted; round 2's physics was kept
  but its retune was not accepted on ET).
- **Hot- and cold-day power correction** follows the standard dyno correction
  formula, anchored so the reference day is bit-identical: it changes results
  only away from the reference conditions (tens of milliseconds on a very hot
  day), and the pins did not move.
- **Measured and not shipped:** corrected gearing for small bikes. Many
  small bikes fall back to a litre-bike primary ratio. An inferred rule made
  measured accuracy worse (`reports/session_2026_11_10_epoch.md`), and so did
  manufacturer-documented gearing for 53 bikes (weighted error 0.2495 →
  0.2525 s), because the small-bike class settings were tuned against the
  tall gearing. The sourced figures are recorded with the experiment in
  `reports/gearing_experiment_2026_11_10.md`; applying them needs a re-tune
  of those classes. A plausibility baseline stops the list growing.

### Changed — the site (design system v6, `web/DESIGN.md`)
- Light and dark themes; one plain vocabulary ("quarter-mile time",
  "Upgrades", "Race-day setup"); a glossary with in-place explanations of
  every term.
- The landing page is built around a ten-second calculator. The simulator has
  a **Simple** mode (bike, rider, place) and an **Advanced** mode with
  everything that existed before. Upgrades and Race-day setup are step-by-step
  tools.
- Every result states the conditions it was computed for.
- Fonts are self-hosted (`web/app/fonts/`, SIL OFL), so the site builds
  without network access.
- `/pricing` and `/refunds` are permanent redirects; `/contact` is a community
  page.

### Changed — API
- Conditions (`location`, `venue_id`, `lat`/`lon`, `altitude_m`, air and track
  temperature, humidity, pressure) are accepted by every simulation, upgrade,
  race-day-setup and outlaw route, and every result carries an `environment`
  block naming the conditions actually simulated and where they came from.
- `part_ids` on the full simulation route; `parts_skipped` reports part ids
  that were ignored instead of dropping them silently; `/api/parts?fields=id`
  answers "which parts fit this bike" without re-sending the catalog.
- Catalog responses are cached and invalidated by a database change token;
  background job results are stored compressed under a memory budget; a
  stock-run cache removes the second simulation from part comparisons.
- Parts apply in one canonical order, so the same parts give the same time
  in any order and the simulator agrees with the upgrade planner; a tyre for
  the wrong wheel is refused; an air temperature without a track temperature
  sets the track 7 °C warmer; a venue named by text keeps its own surface;
  weather lookups are cached for ten minutes.
- Rate limits key on the client IP for the trusted proxy hops only
  (`MOTOQUANT_TRUSTED_PROXY_HOPS`), never the spoofable leftmost
  `X-Forwarded-For` hop; each bucket expires on its own window, so a 60 s
  bucket can no longer evict the daily chat counters.
- PostHog forwarding is opt-in: off unless the operator sets
  `POSTHOG_API_KEY`.

### Fixed — two independent audits
- **Advice tools** (optimizer, autotune, outlaw): the defects found by both
  audits. The upgrade tool verifies its chosen build with real simulations
  and never recommends a part it has not simulated; the race-day tool reports
  launch RPM as not adjustable when the launch is not RPM-sensitive instead of
  inventing a number; a combined setup can no longer be slower than its own
  best single change.
- **Calibration imports and CLI**: Dragy and ECU-log imports timed a run from
  the wrong instant when the log did not start from a stop; ECU speed columns
  are unit-aware and unrecognised units are refused; the auto-calibrator's
  full preset no longer fits a parameter the engine does not read, and bad
  parameter paths raise instead of being ignored; CLI happy paths exit 0.
- **Plain-English parser**: a model number or a year is never read as a
  budget; when it cannot tell, it says so instead of guessing.
- **Security**: the chat agent's web fetch re-checks the SSRF guard on every
  redirect hop and covers shared/carrier-grade NAT ranges.
- **Chat**: tool-argument hygiene (ported from PRs #117 and #119).
- **Data**: `scripts/patch_2026_11_05_reference_rows.py` refreshes the three
  reference bikes' DB rows (ids 1–3) from `defaults.py`, so `db seed` no
  longer mints a new config version for each of them.
- `make db` printed its summary through an unterminated shell quote and
  exited 2 after building the database; fixed.
- **Documentation and site copy**: the whitepaper, the accuracy pages and
  the blog quoted the July accuracy figures and the old reference times;
  they now match the November sweep. The whitepaper, the physics page and
  the FAQ described a Pacejka slip-force tyre model; the engine uses the
  peak friction coefficient (with load, temperature, pressure and track
  preparation), and the slip curve is coded but not called, so the copy now
  says that. Aero, chain and parasitic-loss ranges on the physics page are
  taken from the catalog. The accuracy page's methodology gave the
  benchmark conditions as ISA 15 °C and 0 % humidity; the sweep runs at sea
  level, 25 °C and 50 %.

### Changed — catalog
- Invented placeholder parts that carried real brand names are removed, and
  fabricated wheelie bars with made-up brand names are labelled "Generic".
- Bikes that were the same motorcycle entered twice are merged, applying the
  sourced values (several kerb weights had been entered as dry weights).
- Headline specification columns that had silently inherited the GSX-R1000's
  values are now the bike's own or empty.
- Parts, catalog-data and fitment defects found by the audit
  (`scripts/patch_2026_10_24_parts_data.py`,
  `scripts/patch_2026_10_24_config_sync.py`).

### Removed
- Payments (Razorpay/Stripe checkout and webhooks), subscriptions, license
  keys, `require_tier` / `MOTOQUANT_BILLING_ENFORCE` tier gating, 402
  `upgrade_required` / `upgrade_url`, the `X-Sims-Remaining` sim quota
  (`usage.py`), and the chat agent's "pro tools" gate.
- Dead billing schema from the shipped `motoquant.db`: tables
  `subscriptions`, `license_keys`, `payment_events`, `sim_usage`, and columns
  `users.tier` / `razorpay_customer_id` / `stripe_customer_id`
  (`scripts/patch_2026_10_23_drop_monetization.py`, idempotent). Older DBs
  that still carry `users.tier` keep working.
- Web: pricing and refunds pages, tier badges, upgrade prompts, checkout
  calls, every Pro/Studio price and every "free during beta" claim.
- The scrapped `desktop/` tree and the retired desktop `release.yml`
  workflow.
- The name "MotoQuant Pro": the project is **MotoQuant** on user-facing
  surfaces, docs, API titles and CLI help. Historical entries below are left
  as written.

### Removed — accounts and anonymous writes
- Sign-in (magic link and password), sessions, the account page and the
  server-side saved-run store, with their tables
  (`scripts/patch_2026_11_10_remove_accounts.py`). The old save route
  trusted the time a browser sent and published free-text notes.
- Public routes that stored visitor input: bike suggestions, spec
  corrections and price refresh. Every POST route is now on a tested
  allow-list, and no route accepts PUT, PATCH or DELETE.
- The chat assistant no longer logs an estimated bike that is missing from
  the catalog; the server now writes nothing a visitor sends to its
  database.

### Added — runs, timeslips and contributions without accounts
- Saved runs live in the browser (`/runs`). A timeslip link carries the
  setup and the exact conditions, and `/timeslip` re-runs it through the
  physics, so a shared time cannot be typed in; every change from stock is
  printed on the slip.
- The leaderboard ranks every catalog bike by its simulated stock time
  (`scripts/gen_stock_leaderboard.py`, checked by a staleness test).
- Issue forms for submitting a timeslip, suggesting a bike and sending a
  dyno sheet; the bike page and the simulator's Dragy comparison open them
  prefilled.
- `make reseed` (the catalog chain, in order) and `make regen` (everything
  that caches the physics).
- A launch post, "MotoQuant 2.0 is open source, including where it is
  wrong", and a contact page that links the data forms and the private
  security route.
- Opening a timeslip in the simulator keeps the altitude and pressure of a
  run at a place that is not a catalog venue, so the simulator shows the
  slip's time. "Save and share" still gives the link when the browser will
  not store the run, and rider weight is shown as a condition, not as a
  change to the bike.

### Kept (not monetization)
Part INR prices and cost-per-tenth, `budget_inr`, per-IP rate limiting, chat
per-turn budgets, build stages, and env-gated Sentry.

### Known residuals (documented, not fixed)
Details and figures: `reports/session_2026_11_05_handoff.md`.
- Two accepted millisecond-level dry-mass inversions (BMW HP4 Race, Ducati
  Panigale V4R): wheelie-ballast physics. More litre bikes invert at sea
  level.
- The reference spread is compressed: the three simulate within 0.07 s of
  each other (10.04 / 10.11 / 10.11 s) against 0.43 s in the published
  tests (9.97 / 10.30 / 10.40 s). The order is right; the R1 and Hayabusa
  come out 0.19 s and 0.29 s quick.
- Class bias remains on entry 200–300 cc, singles 300–500 cc and two-strokes;
  small bikes are the weakest class.
- Litre bikes are nearly mass-insensitive at launch.

### Regenerated
`motoquant.db` re-seed chain, the regression golden (fast and full-catalog
tiers), the surrogate and its web export, the wasm engine fixtures, the
`/validation` data, the stock leaderboard, sitewide accuracy copy and the OG
card. Instant-estimate model v2.8: 9,035 rows, holdout ET mean error 76.6 ms,
RMSE 117.1 ms, R² 0.9985 (`artifacts/surrogate/README.md`).

### Moved
- The repository is now <https://github.com/toto171/MotoQuant.in>.
- Removed from the tree when the repository went public (still in the git
  history): internal planning documents, maintenance automation, session
  write-ups not cited by code or docs, and the brand kit.

## [PR #116] — 2026-07-19 — Scrapling dev-side scraping toolkit

Dev-only scraping toolkit; **nothing in it writes `motoquant.db`** — scraped
specs are unverified adjudication inputs.

### Added
- `motoquant/scraper/fetcher.py` — `PoliteFetcher`: disk cache → robots.txt
  (protego) → per-domain rate limit → tier escalation (basic → curl_cffi →
  browser/Playwright → stealth/Camoufox, stealth opt-in only). Scrapling is
  soft-imported with a typed `ScraplingNotInstalled`; it lives in a new
  dev-only `requirements-scrape.txt`, never `requirements-api.txt`.
- `scripts/scrape_bike_specs.py` — bikez scrape → `validate_spec` gate →
  import-ready JSON, plus a triage report that surfaces unmapped spec-table
  rows as the site-drift signal. `docs/SCRAPING.md` is the runbook.
- `tests/test_scrapling_fetcher.py` (22 tests, zero network via a
  `fetch_fns` injection seam; parser pinned on a committed fixture).

### Fixed
- `bikez.py` URL-slug year detection took the FIRST 4-digit token, so
  `gsx-r_1000_2005` parsed as model "GSX R", year 1000. Year is now the
  trailing plausible-year segment only. Public `parse_bikez_detail()`
  extracted so scrape and parse share one source of truth.

## [PR #114] — 2026-07-17 — Orchestrated run: scope + full execution

New authoritative sweep: **250 benchmarks / 277 matched / weighted |Δ|
0.2721 / bias −0.0047** (`reports/acc_final_2026_07_17.json`). The |Δ| rise
from 0.2533 is deliberate honesty, not regression — optimistic DERIVED rows
were replaced with slower instrumented truth (12 rows, including five new
Indonesian Racelogic/GPS measurements), and bias is now essentially zero.

### Added
- **Factory speed limiter** — `DrivetrainParams.speed_limiter_kmh`, clamped
  at all four RK4 stage velocities, validated 120–340, round-tripped through
  the bridge and `config_io`. Ten specs annotated at 299 km/h. Top-speed
  sweep: mean |Δ| 35.0 → 32.0 km/h, bias +28.5 → +25.4. Shipped NON-epoch —
  baselines stay bit-identical (`None` = unrestricted).
- Growth funnel on the existing `track()` pipeline (`sim_run_success`,
  `signup_completed`, `upgrade_clicked`), a timeslip CTA on bike pages, and
  a zero-dependency print-PDF timeslip on `/r/[id]`.

### Security / hardening (the "before charging money" bundle)
- Bound license keys reject `device_id`-omitting validates;
  `/license-key/validate` rate-limited (10/60 s).
- Razorpay webhook idempotency ledger (header id + sha256-body fallback).
- `/api/jobs/outlaw` pro-gate closed; `python-jose` → `PyJWT`; non-root
  `USER app` in the Dockerfile (verified against a real Docker build);
  `lastrowid` → `rowcount` in the bike/venue repos.

### Changed
- Six dead `CategoryProfile` knobs deleted; the live-knob inventory is now
  pinned as an exact set.
- CI reworked to a python-only, path-filtered workflow: ~3 min PR fast tier
  vs full suite + coverage on main pushes.

## [PR #109] — 2026-07-13 — Physics epoch + scrape-consumption + hardening

The operator-ordered "all 3 things" pass over the July-11 validation
scope-out. **The pinned reference baselines moved** (deliberate epoch per
ADR-0002): K5 10.0334 → **9.9331 s**, R1 10.2859 → **10.1436 s**, Hayabusa
10.4712 → **10.3633 s** — now tracking their real-world figures (9.97 /
10.30 / 10.40) closer than the old pins did.

### Changed — physics (epoch items 1–4 from the July-10 review)
- Deceleration is real once the clutch locks (`a_net` clamp now
  slip-only): drag/RR act through gearshift torque cuts.
- Weight-transfer→traction cap converged via fixed-point refinement — wet/
  salt venue penalties are now honest (the single pass overstated clipped
  rear load by up to 46% of static).
- Slip + lock-transition torque now mirrors the locked branch (ram-air ×
  FI − parasitic).
- Front-wheel inertia over the FRONT rolling radius in effective mass.
- New `CategoryProfile.mu_peak_scale` recalibration knob, grid-tuned per
  cluster against the 277-match corpus (guard + liveness pinned).

### Added — data (scrape-consumption pass)
- ET benchmark corpus 221 → **250 unique rows** (277 matched); 6
  conflicting finds adjudicated and rejected with web verification.
  Top-speed corpus 77 → 86.
- 56 high-confidence spec fixes applied to the `known_bikes*.py` sources
  (R9 117.4 hp, RC213V-S 159 hp street, Z H2 SE 197.3 hp, GSX-R K1/K3
  160/164 hp, 23 kerb masses …).
- `scripts/patch_2026_07_13_scrape_data.py` (idempotent): 282 part
  reprices from live listings (72 INR direct + 210 USD landed-cost),
  6 discontinued units flagged, 25 fictional-brand SKUs renamed to honest
  class names (folded into `seed.py` so a fresh seed can't resurrect
  them), 24 discontinued/not-found tire families flagged, 19 tire prices.
- New authoritative sweep `reports/acc_final_2026_07_13.json`: weighted
  |Δ| **0.2533 s** / bias **+0.0166 s** (honest decomposition in
  `reports/session_2026_07_13_epoch_data_hardening.md`: 0.2166 → 0.2404
  corpus expansion, → 0.2533 physics epoch after retune).

### Fixed
- `config_io` save/load dropped `category_tag` — loaded configs silently
  ran the "unknown" physics profile (file-based twin of the July-2 bridge
  bug; exposed by the epoch's cluster grip knobs).
- Unknown `boost_type` strings now raise at engine construction (were
  silently granted the ×0.97 boosted-DA floor with zero boost); API
  returns 422 naming the offending part.
- `max_time_s` request floor (`ge=0.1`) — sub-dt values crashed the
  engine with an unhandled ValueError.

### Removed
- Dead knobs: `AeroParams.headwind_ms`/`crosswind_ms`; the never-called
  `RiderDynamicsModel.cog_shift`/`wheelbase_weight_split` pair.

### Docs / site
- Golden + surrogate regenerated; `/validation` data + sitewide stats
  synced to the new sweep on the STAGED v4 design; new pins in
  `AGENTS.md`, `docs/INVARIANTS.md`, `scripts/check_baselines.py`.
- Finding: the litre top-speed overshoot is a missing factory
  speed-limiter model, NOT the decel clamp (A/B-proven; scoped for a
  future pass).

## [PR #108] — 2026-07-11 — PR #105/#106 post-merge validation & measurement

Full validation pass over the two July-10 auto-session merges (operator
request). Verdict: **merged properly, nothing broken, published accuracy
numbers unchanged and re-proven.**

### Verified
- Fresh full weighted sweep **byte-identical** to `acc_final_2026_07_06.json`
  (246 matched / weighted |Δ| 0.2165 s / bias +0.0212 s) — committed as
  `reports/acc_verify_2026_07_11.json`; `/validation` viz data regenerates
  identically. PR #105 is thereby proven NA-bit-identical across the whole
  catalog, not just the three pinned references.
- Full suite 4,472 ran / 0 failed / 91 skipped (twice); slow-tier
  full-catalog golden regression green; `make health` HEALTHY.
- PR #105 improvements measured A/B vs pre-merge main: boosted builds gain
  −0.23 to −0.38 s ET that was previously lost in the clutch-slip phase
  (real Schnitzer turbo part: advertised gain −0.900 → −1.191 s); top-speed
  plateau and adaptive-truncation repros fixed; all 541 stock configs
  verified unaffected. PR #106 scrape corpus recounted line-item against
  `motoquant.db` — no fabrication tells, all headline claims reproduce.

### Added
- `tests/test_ram_air_wind.py` — the ram-air airspeed fix (40cf813) had
  shipped with **no pinning test** (reverting it left the suite green);
  4 new production-path tests, 2 verified to fail on revert.
- `reports/session_2026_07_11_pr105_106_validation.md` — full report incl.
  the benchmark-consumption triage (4 new instrumented + 11 magazine + 15
  lower-weight finds, 6 conflicts to adjudicate, 31 corroborating
  duplicates) and the scope-out for the next data-update pass.

## [PR #107] — 2026-07-10 — STAGED v4: ground-up website redesign

Operator-directed full redesign ("completely new website, full creative
freedom, simpler interface, full functionality"). New design language:
**STAGED — the digital timeslip.** Night-asphalt surfaces, one volt-green
accent (the green light), Barlow Condensed display type, mono tabular
numbers, and the printed timeslip as the signature result artifact.

### Added
- **`web/DESIGN.md`** — the v4 design authority (supersedes `REDESIGN.md`).
- **`design/staged/`** — 13 design-system preview cards (also synced to the
  owner's Claude Design project via claude.ai/design).
- New CSS vocabulary: `.timeslip`, `.chip-*`, `.delta-down/.delta-up`,
  `.centerline`; `StageDots` signature component (pre-stage · stage · GO).

### Changed
- Every page + chrome re-skinned; landing page rewritten at half its length
  around a live quick-sim hero. Tool pages unified on a two-pane workbench.
  `/r/[id]` and `/leaderboard` are now full timeslip artifacts.
- Tailwind tokens: `asphalt-*` / `accent` (volt) / `signal-*` / `mint`, with
  `ink-*`/`brand-*` kept as compatibility aliases so ~50 untouched blog
  pages re-skin automatically.
- Brand assets regenerated (volt icon set, webmanifest, OG card); the OG
  renderer in `scripts/audit_headline_stats.py` re-paletted.

### Removed
- Cockpit-era decoration: BootSequence, HudFrame, TronGrid, ManifestoScrub,
  PhysicsDial, ChristmasTree, LaunchControl, TelemetryHUD, SectionRail
  (seven-segment ScoreboardDigits survives as clean mono digits behind the
  same API).

### Unchanged (by contract)
- All functionality: job-backed sims with progress/Stop, save→leaderboard→
  share loop, auth/billing flows, chat agent UI, experiments, SEO/JSON-LD,
  `lib/api.js` polling resilience; every headline stat token byte-identical
  (audit in sync).

## [PR #100] — 2026-07-06 — Durability milestone

The 100th pull request. Focus: make the codebase keep improving across
model/human handoffs, plus a final security sweep.

### Added — durability systems (survive any contributor switch)
- **`AGENTS.md`** — the one-page, model-agnostic working contract (prime
  directive, the loop, non-negotiable rules). The canonical entry point for any
  AI tool or human.
- **`Makefile`** — the universal entry point; targets mirror CI (`make check`,
  `make test`, `make health`, `make baselines`, …).
- **`scripts/check_baselines.py`** — executable guard for the K5/R1/Hayabusa
  bit-identical invariant (exit 1 on drift). Wired into `make`, pre-commit, CI.
- **`scripts/health_check.py`** — one-command state-of-the-world (baselines,
  lint, catalog, headline drift, git, secret scan); `--secrets-only` fast mode.
- **`docs/INVARIANTS.md`** — what must never break + the gate that enforces each.
- **`docs/KNOWN_TRAPS.md`** — the recurring-bug "don't step here" map.
- **`docs/ROADMAP.md`** — honest, prioritized path to the $1M/$10M goal, tied to
  real blockers.
- **`.pre-commit-config.yaml`** — local enforcement (ruff, baseline guard on
  physics files, secret scan, large-file guard).
- **ADRs 0002–0005** — pinned baselines, no-Numba, SQLite-until-scale, desktop
  discontinued (supersedes ADR-0001). The "do not re-litigate" decisions.

### Added — CI
- **Secret-scan gate** in the Python CI job (stdlib-only, fails fast).

### Security
- Final adversarial security sweep across backend, web frontend, DB write-races,
  supply-chain/config, and a re-triage of the deferred findings. Confirmed
  low-risk fixes landed; the rest catalogued in `docs/ROADMAP.md` P1 with
  rationale. *(See the PR #100 review report in `reports/`.)*

## [PR #99] — 2026-07-06 — Security & navigability review

- **SSRF** fix in the chat agent's `web_fetch` (redirect revalidation on every
  hop + total-timeout bound + connection-leak close).
- **Rate-limit / free-quota bypass** fixed (rightmost `X-Forwarded-For` hop
  instead of the spoofable leftmost).
- **JWT default-secret** boot guard under billing enforcement.
- **Job slot-exhaustion DoS** — hung workers released past a runtime deadline.
- **API input validation** — bounded sim params; `limit=-1` table-dump on
  `/api/leaderboard` + `/api/me/runs`.
- **`docs/ARCHITECTURE.md`** — module map + data-flow diagram + docs index +
  repo-navigation guidance.
- Full suite 4324 passed; baselines bit-identical; +22 regression tests.

## Earlier

The project's full history (physics engine, 541-bike catalog, calibration
pipeline, surrogate models, agentic chat, commercial launch, the Render
migration, and dozens of accuracy/hardening passes) is recorded session-by-session
in `CLAUDE.md` and `reports/`. Highlights:

- **Agentic chat** — multi-step tool-calling agent over the whole product.
- **Taxonomy v2 accuracy retune** — full-corpus weighted sweep; per-cluster knobs.
- **Catalog** — 541 bikes / 593 parts / 254 tires / 20 venues / 221 benchmarks.
- **Surrogate models** — learned cache of the physics for the optimizer.
- **Commercial launch** — accounts, magic-link + password auth, Stripe/Razorpay,
  freemium beta, shareable timeslips.
- **Reference baselines** pinned bit-identical since the engine was validated.
