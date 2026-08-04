# Changelog

Notable changes, newest first. This is the human-readable milestone history;
the exhaustive session-by-session log lives in `CLAUDE.md` (top entry = latest)
and `reports/`. Format loosely follows [Keep a Changelog](https://keepachangelog.com).

## [PR #118] — 2026-07-26 — Weekly audit: trap units, dead gates, doc + CI truth

A 39-agent, 12-dimension audit with adversarial verification of every
high/critical finding. 82 raw findings; 16 survived a verifier instructed to
refute them.

### Fixed
- **SAE J1349 dyno correction had its temperature ratio inverted**, so every
  imported dyno curve was corrected in the wrong direction.
- **11 benchmark trap speeds were transcribed in mph but stored as km/h**;
  `tests/test_benchmark_units.py` now guards the whole class against the real
  pre-fix row.
- Catalog part 340 shipped an invalid `boost_type` that 422'd every simulation
  it was applied to.
- Two unauthenticated cost-bearing routes fused: `/api/venues/resolve` (spends
  the OpenWeatherMap key) and `/api/pricing/refresh/{id}` are now rate-limited.
- Calibration uploads are size-capped (an unauthenticated OOM lever).
- Per-IP rate limits on the credential-burning auth routes.
- `/api/simulate` rejects impossible environment input and no longer stacks
  duplicate `part_ids`.
- Preflight aborted every autonomous session on a false physics-drift reading.
- `/validation` hero tiles derive from the data; `/features` |Δ| synced.
- Tests no longer write metering rows into the tracked `motoquant.db`.

### Changed
- Pre-epoch baselines retired from the gates that had missed them; the durable
  doc set resynced to the tree; CI `make install` made sufficient and the
  retired release workflow defused.

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
