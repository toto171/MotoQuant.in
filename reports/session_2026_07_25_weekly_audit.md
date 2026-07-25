# Weekly audit — 2026-07-25

**Scope:** the tree as of `cccce54` (post PR #114 + #116). Multi-agent sweep
across 12 dimensions with adversarial verification, plus independent
verification by the session of everything acted on.

**Also verified clean, rigorously** (DB/catalog dimension): INVARIANT I2 — all
538 spec-matched `bike_configs` rebuilt from source and deep-diffed across all
13 JSON blobs, **byte-identical**, with only the 3 deliberately-excluded
reference bikes unmatched. INVARIANT I3 — the full 541x593 matrix evaluated
through the production `is_compatible` engine (**53,141 pairs**): every match
satisfies every declared constraint, 0 parts with no compatible bike, 0 bikes
without an exhaust. The reseed chain is a fixed point (identical content md5
across base + two passes, every script reporting 0 changes). T15/speed-limiter
round-trip lossless, with exactly the 10 annotated specs carrying 299.0.

**Branch:** `claude/weekly-audit-yvwyyt` → **PR #118** (draft).

---

## 0. The one-paragraph version

The engine is healthy: baselines bit-identical, full suite green (**4112
passed / 91 skipped / 0 failed** across 63 modules), and an independent
542-bike re-sweep reproduces the published accuracy headline **byte for byte**.
The problems are all *around* the engine — and the two most serious are
**silent infrastructure death**: GitHub Actions has assigned **no runner to any
job since 2026-07-13**, and `session_preflight.sh` has aborted **every**
autonomous session since the same week on a false physics-drift error. Both PR
#114 and #116 merged with zero CI verification. Beyond that, the audit found a
**data-honesty bug that made the public accuracy page understate the engine by
7x on trap speed**, and a set of pre-revenue hardening gaps.

Ten commits of safe fixes are on PR #118. The findings that would move the
pinned baselines are written up below and deliberately **not** touched.

---

## 1. Verified healthy (worth recording)

| Check | Result |
|---|---|
| Pinned baselines | K5 9.9330563825 / R1 10.1435897157 / Hayabusa 10.3633450813 — **Δ +0.00e+00** |
| Full suite | **4112 passed / 91 skipped / 0 failed** (63 modules, run individually) |
| `make health` | HEALTHY — 0 fail, 0 warn (after the fixes below) |
| ruff | `check` + `format --check` clean, 228 files |
| Web build | `npx next build` ✓ 76/76 static pages; `verify-web` clean on 178 files |
| Accuracy headline | Re-swept from scratch: 277 matched / w\|Δ\| 0.2721 / bias −0.0047 / raw 0.3758 — **identical** to `acc_final_2026_07_17.json` |
| `/validation` data | overall, distribution, cluster and reference blocks all in sync with the sweep |
| Security posture | Every AGENTS.md §4 guarantee re-verified and **holding**: webhooks fail closed on both providers with a UNIQUE(provider,event_id) ledger; PyJWT migration sound (algorithms pinned, no `none`/alg-confusion path, `exp` verified, `jti` bound to `sub`, `dev.` branch correctly gated on the library-absent case); magic-link consumption atomic; scrypt N=16384/r=8/p=1 with a constant-time dummy-hash path |
| Job cancellation | Clean — `JobCancelled` is a `BaseException`, and there is no `except BaseException` or bare `except:` anywhere in `motoquant/`, so Stop always propagates |
| `/api/jobs/*` gating | The July-17 `/api/jobs/outlaw` class of bug is **closed** — every job route now carries the same tier gate + rate limit as its sync twin (checked pairwise) |
| Web internals | 0 broken internal links; all 65 static sitemap URLs resolve; every one of the 24 components is imported |

---

## 2. Fixed in PR #118

### 2.1 — Eleven benchmark trap speeds were mph in a km/h column `[data, HIGH]`

The trap column is km/h. Eleven rows carried the source's mph figure
un-converted. Found by an assumption-free physical bound rather than by eye:

> for a monotonically accelerating vehicle, trap speed must exceed the average
> speed over the quarter (`402.336 m / ET`).

That flagged **exactly 11 rows out of 250 and nothing else**, each by
6.8–11.9 km/h, and ×1.609344 makes every one consistent.

**Why it mattered.** The public `/validation` explorer exports these as
`real_trap` against a km/h `sim_trap`:

| Bike | published "real" | sim | error shown | corrected | real error |
|---|---|---|---|---|---|
| Harley Sportster S 2021 | 122 | 201.3 | **+79.3** | 196.3 | +5.0 |
| Kawasaki Ninja 650 2020 | 111 | 199.3 | **+88.3** | 178.6 | +20.7 |
| Yamaha MT-03 2020 | 92 | 154.7 | **+62.7** | 148.1 | +6.6 |
| *(8 more)* | | | | | |
| **mean \|trap error\|** | | | **75.2 km/h** | | **10.8 km/h** |

The accuracy page — the product's differentiator — was defaming its own engine.

This closes the *"trap-column mph-vs-kmh audit (~9 suspect April-era rows
flagged)"* item queued in CLAUDE.md, and the deferral comment already sitting
on the Ninja 400 row. It is the same defect and the same fix as the YZF-R7 2022
correction of 2026-05-31.

**Provably headline-neutral:** `phys_weighted_sweep` scores `d = sim_et - te`
only — the trap element is unpacked but never scored. A full 542-bike re-sweep
on the corrected corpus reproduced the published figures byte-identically
(`reports/acc_verify_2026_07_25.json`), and regenerating `accuracy_data.json`
changed exactly **11 cells, all `real_trap`**.

**Corroboration these are unit errors, not bad measurements:** the Continental
GT 650 appears twice with the *same* ET (13.90) — once at trap 155 (km/h) and
once at 97 (mph = 156.1 km/h). One measurement recorded in two units.

`tests/test_benchmark_units.py` now pins the bound against the real corpus.

### 2.2 — `session_preflight.sh` aborted every autonomous session `[ops, CRITICAL]`

It carried its own inline copy of the baselines, stale since the July-13 epoch,
at ±0.005 s tolerance. Measured on the current tree:

```
K5    sim=9.9331  target=10.0334  delta=-0.1003  FAIL
R1    sim=10.1436 target=10.2859  delta=-0.1423  FAIL
Busa  sim=10.3633 target=10.4712  delta=-0.1079  FAIL
```

Step 5 hard-failed on a healthy tree and exited 3 before any work could begin.
`session_postflight.sh` had the identical bug and was fixed 2026-07-17 — its
comment even names these exact values — but the twin was missed. **The
autonomous session harness has therefore been dead since the epoch**, the same
week CI stopped getting runners. Now delegates to `check_baselines.py`.

### 2.3 — Test metering rows are committed in the shipped database `[test, HIGH]`

`tests/test_hardening_2026_07_13.py` POSTs to metered routes without
redirecting `MOTOQUANT_DB`, so `_meter_full_sim` wrote `sim_usage` rows into
the repo's tracked `motoquant.db`. Not hypothetical — **three rows are
committed on `main`** (2026-07-02, -03, -06, all under the TestClient's fixed
key `anon:846488f1dc5c07b4`) and ship to Render in every image. Fixed with the
`test_jobs_api` isolation pattern; proven red on revert.

*The three already-committed rows are left in place* — purging them is a data
change to the shipped catalog and belongs in its own commit.

### 2.4 — README published retired baselines; both gates that should have caught it were broken `[docs, CRITICAL]`

The repo's front page stated the pre-epoch pins (10.034 / 10.286 / 10.472) as
the current contract, and the bug-report template asked reporters to confirm
"K5 sim is within 10.034s ± 0.07" — a box no healthy tree can tick. Then:

1. `audit_headline_stats.py` scoped **every** baseline pattern to
   `web/app/**`, while `INVARIANTS.md` I6 claims it enforces the stats "quoted
   in web pages, README, and docs".
2. `health_check.py` invoked it **without `--fail-on-drift`** and then treated
   `rc == 0` as proof of sync. That script always exits 0 without the flag, so
   the `... or rc == 0` short-circuit made the drift row report "in sync"
   **unconditionally** — a gate that could never fire.

All three fixed; both gates proven to fire on a reintroduced retired pin.

### 2.5 — Duplicate `part_ids` fabricated faster ETs `[api, HIGH]`

`_apply_parts_to_config` iterated the list verbatim, so `[56, 56, 56]` applied
one Akrapovic full system three times (+36 hp, −20.4 kg from a single exhaust)
and returned the fabricated result as a 200. Measured on the K5: **ET 9.7327 s
stacked vs 9.8611 s correct — a 0.128 s gain invented from one repeated
integer**, with a 3× build cost. De-duplicated; proven red on revert.

### 2.6 — Impossible environment input returned ET 0.0 as a success `[api, MEDIUM]`

`ambient_temp_c` / `track_temp_c` / `humidity_pct` / `headwind_kmh` had no
bounds on any of the five sim request models — the exact failure the in-file
comment above them says the bounds prevent, and which `AutotuneRequest` has
bounded correctly from the start. `humidity_pct: 1e9` returned **200 with
`et_quarter_s: 0.0`**. Now bounded consistently.

### 2.7 — Auth routes had no rate limit `[security, HIGH]`

The only brake, `_login_locked`, keys on the **submitted email**, so rotating
it defeats the throttle entirely while every request still pays a full scrypt
(~53 ms here, more on 0.5 CPU) — `verify_password` deliberately runs one even
for a non-existent account. Measured pre-fix: **14 logins with a rotating email
returned `[401 ×14]` with no throttle at any point.** `/magic-link` also sends
an email per call.

Added per-IP limits (login/verify/password-change 10/60 s, register and
magic-link 5/60 s). `/me`, `/refresh`, `/logout` deliberately left unlimited —
a signed-in client polls them — and that exclusion is pinned by a test.

### 2.8 — Unauthenticated upload OOM lever `[security, HIGH]`

Both calibration routes did a bare `await file.read()` with no ceiling, then
wrote to a second temp file — a few hundred MB is an OOM kill plus disk fill on
the 512 MB instance. The `require_tier("studio")` gate does **not** stop it:
`require_tier` passes anonymous callers through whenever
`MOTOQUANT_BILLING_ENFORCE` is falsy, which `render.yaml` ships as the default.

Capped at 25 MB, read in chunks. *Testing the fix surfaced a second bug:* the
enclosing `except Exception` remasked the 413 as a generic 400 — fixed with an
explicit pass-through.

### 2.9 — Flagship page contradicted itself `[web, MEDIUM]`

`/validation`'s hero tiles were literals carrying July-13 counts (74 / 137)
while the distribution tiles one section below read 75 / 138 from
`accuracy_data.json` — the same page stating two values for one metric. Hero
now **derives** from the data file, so it cannot drift again. `/features`
separately quoted the July-13 `0.253 s` where every other surface says `0.272`.

### 2.10 — Dead patch section emitted 8 false "part not found" warnings `[LOW]`

The E-section of `patch_2026_07_06_catalog_integrity.py` looked parts up by
`brand='ClutchCo'`, but the July-13 honesty rename moved all 8 SKUs to
`brand='Generic'` and folded the band into the SKU name at the seed source. So
every run of a mandatory reseed-chain step emitted 8 `WARN: part not found`
lines **indistinguishable from a real missing-part signal** — false alarms in
the exact channel you need to trust when a patch genuinely fails.

Verified before removal: all 8 SKUs (ids 129–136) exist under `Generic` and
already carry their banded rules, and the step's counts are unchanged after
removal (`111 already applied` both before and after, twice), so it was
contributing nothing but noise.

### 2.12 — A ₹450,000 catalog part 422'd every simulation `[catalog, HIGH]`

Part 340 declared `boost_type: "supercharger"`, not a member of
`VALID_BOOST_TYPES`. The July-13 T16 hardening correctly made the engine raise
on unknown values, but **the catalog data was never migrated to match**, so the
row has hard-failed ever since — verified live: part 340 → HTTP 422, valid
sibling part 138 → HTTP 200. It was also silently dropped from every
ROI/optimizer result, and it is the only bad value among 20 forced-induction
SKUs.

Corrected to `sc_roots` (its own specs declare a **Lysholm screw** compressor —
positive-displacement, not centrifugal) with `target_boost_bar` derived from
its own declared 5.0 psi. No number invented. Post-fix: HTTP 200, 9.9331 →
9.5498 s. `tests/test_catalog_enum_integrity.py` guards the class.

### 2.11 — Doc set, `make install`, and a live CI landmine

ROADMAP listed six hardening items as deferred that **all landed in PR #114**
(two flagged "do before charging money"); ONBOARDING pointed day-one readers at
the backlog file ROADMAP itself calls stale; CHANGELOG was two merges behind;
ARCHITECTURE's module map omitted four live modules; KNOWN_TRAPS/INVARIANTS/ADR
cited a CI job name that doesn't exist and listed done work as pending.

`requirements-dev.txt` was missing **ruff**, so `make check` — the very next
command in the documented loop — died on a fresh checkout, plus pytest-cov,
SALib and scikit-learn (so `make test` silently skipped tests CI runs).
`release.yml` built `desktop/sidecar/`, deleted six weeks ago, and hard-failed
four runners on any `v*` tag; trigger narrowed to manual.

---

## 3. Found and NOT fixed — needs a deliberate pass

These are real and evidenced, but each moves pinned baselines, published
numbers, or the catalog. They do not belong in an audit PR.

### 3.1 — `parasitic_mult` is a dead knob for 100 % of the catalog `[HIGH]`

`CategoryProfile.parasitic_mult` is in `tests/test_profile_knobs.LIVE_PROFILE_KNOBS`
— *the exact set that exists to stop dead knobs accumulating* (KNOWN_TRAPS
T11) — and carries calibrated non-1.0 values (two-stroke 0.20, cruiser 0.65,
entry 0.85). But **542/542 catalog configs ship `dyno_curve.is_at_wheel=True`**,
which bypasses the parasitic subtraction entirely.

Measured on the Ninja 400 through the production path:

```
5x ALL parasitic wattages (alt 80→400 W, oil 199.5→997.5, valvetrain 99.75→498.75)
    ET delta = 0.0000 s
chain_efficiency 0.95 → 0.76 (−20 %)
    ET delta = +0.0012 s
```

Root cause: `_synthetic_torque_curve` builds torque to produce the spec's rated
**crank** power, then returns it flagged `is_at_wheel=True`, so `EngineModel`
divides by `eta_dt` (undoing the loss) and physics skips the parasitic term.
Every catalog bike therefore delivers full rated crank power at the rear wheel.

**This blocks the queued cluster retune.** You cannot meaningfully retune
cluster knobs while one of them is unreachable for every bike in the catalog.

### 3.2 — Four speed-limiter bikes can never reach their limiter `[HIGH]`

Hayabusa Gen2/Gen3, ZX-14R and ZZR1400 are annotated `speed_limiter_kmh=299`
but their catalog top-gear ratio is ~21–25 % too short, so they hit the **rev**
limiter first at 264–289 km/h. The annotation is structurally inert.

This is decidable without any external source — it is an internal
contradiction in our own data: *we annotate a 299 km/h limiter on a bike our
own gearing says tops out at 264.* Hayabusa Gen2 top gear is listed as 1.304
(not overdriven); the real GSX1300R 6th is ~1.04. Tellingly, the Hayabusa 25th
Anniversary spec in the same file carries a **correct** overdriven cassette
(6th = 0.871).

**A test whitelist is actively protecting the bug:** `tests/test_gearing_sanity.py`
line 53 exempts `("suzuki", "hayabusa")` with the comment *"Gen1/2/3: 6th =
1.304 (confirmed service manual)"*. Fixing the data means removing that
whitelist entry, re-seeding, re-sweeping and re-syncing stats — a coordinated
pass. **Do this before any broader limiter-annotation work**, or the annotation
is inert on exactly the bikes it targets.

### 3.3 — Duplicate catalog entries, and the two regen paths disagree `[HIGH]`

`ALL_KNOWN_BIKES` holds **542 entries for 541 bikes**. Four are exact-key
duplicates — same manufacturer, model *and* year range — because
`known_bikes_extended` re-defines bikes already in the base list with
materially different mass/gearing/aero:

```
('royal enfield','hunter 350',2022,2026)   ('yezdi','roadster',2022,2026)
('yezdi','adventure',2022,2026)            ('kawasaki','versys 650',2015,2024)
```

**The two documented DB-regen steps pick different winners**, so a bike's
stored physics depends on whether `import --known-bikes` or
`reseed_configs_from_specs.py` ran last — flipping catalog ET by up to
**0.38 s**. That is a reproducibility hole in the regen chain, not just
untidy data.

A wider set (~9) overlaps rather than matching exactly, with contradictory
geometry: **V-Strom SX 250** (bore×stroke 67×70.5 vs 76×54.9 — different
engines), **RE Continental GT 650** and **Interceptor 650** (84×58 vs 78×67.8;
the real 648 cc twin is 78×67.8). The Continental GT duplication is the same
one that produced the two-unit benchmark row in §2.1.

### 3.3b — OEM tire fitments record drag slicks as OEM `[MEDIUM]`

`seed_bike_tire_fitments`' fallback excludes `('race','drag_dot','drag_slick')`
but the catalog also carries 10 tires with compound `'drag'` (mu_peak 1.85, the
highest-grip rows). Since candidates are ordered by mu_peak DESC, those win the
±20 mm fallback — so **the shipped DB asserts a drag tire as the OEM fitment
for 24 bikes**, contradicting the function's own docstring ("never use
race/drag for OEM fitments").

Separately, `link_bike_fitment` uses `INSERT OR REPLACE` against a UNIQUE key
that *includes the tire*, so picking a different tire for the same
(bike, position) appends a second `is_default=1` row instead of superseding the
first. **77 (bike, position) groups across 65 bikes now carry two mutually
exclusive "default OEM" tires** (27 with different sizes), growing ~7 per seed
run — including the GSX-R 1000 K5 rear.

### 3.3c — `drivetrain.quickshifter` is a dead knob behind 8 priced parts `[HIGH]`

`DrivetrainParams.quickshifter` has **no reader in the physics engine** — the
sim reads only `total_shift_time_ms`. Eight shipped catalog parts priced
₹12,640–₹42,000 carry it as their **only** `param_override`, so selecting them
changes ET by exactly **0.000000 s**, while twelve functionally identical
sibling parts that also set `total_shift_time_ms` deliver −0.084 to −0.094 s.

This is the Kaizen checklist's own example made real ("a 15 psi turbo kit that
moves ET by 0.008 s is a bug, not a feature"). Fixing it is a data change
across 8 SKUs, so it wants its own pass.

### 3.3d — `venues.has_vht`: track prep is unreachable for the whole catalog `[HIGH]`

`venues.has_vht` is populated for 6 of 20 venues and **read by nothing** —
`venue_row_to_environment` never sets a track-prep field, and the physics prep
multiplier reads `cfg.tires.track_prep_type`, which is `'none'` for 550 of 553
configs. **Simulating at Santa Pod (VHT-prepped concrete) is bit-identical to
an unprepped strip.** Wiring it moves baselines, so it is epoch-gated.

Compounding it, `nlp.py` parses `VHT`/`PJ1` phrases correctly but assigns them
to `EnvironmentParams.track_prep`, a field with **zero readers** — the `nl` CLI
accepts and echoes a track-prep instruction worth 0.571 s that has no effect.
A second defect sits behind it: `_extract_track_prep` returns the literal
`'rubber'`, which does not equal the `TRACK_RUBBER` constant `'rubber_buildup'`,
so even after redirecting the write that branch stays inert.

### 3.3e — Dependency supply chain `[HIGH]`

- **Next.js is pinned to 14.2.35, an end-of-life major.** It reached EOL
  2025-10-26, took its last patch in December 2025, and `npm audit --omit=dev`
  reports **21 advisories** whose fixed ranges all terminate in 15.5.x/16.2.x —
  **there is no upgrade target inside 14.x**. The 15/16 migration is now a
  security requirement, not a nice-to-have.
- **All 13 production deps are `>=` with no upper bound, and there is no
  lockfile**, so two Docker builds of the *same git commit* at different times
  install different dependency sets. Three floors (`python-multipart`,
  `requests`, `sentry-sdk`) sit at or below versions with published CVEs —
  including the multipart parser reachable from the two upload endpoints.

*Verified clean here:* `pip-audit -r requirements-api.txt` reports no known
vulnerabilities **as resolved today**, and PR #116's scrapling isolation claim
holds under test — importing `motoquant.api` pulls 853 modules and **zero**
from `{scrapling, curl_cffi, playwright, camoufox, protego, lxml}`.

### 3.3f — Scrapling toolkit review (PR #116) `[HIGH]`

The honest-data claim **holds** (no path can write `motoquant.db`; verified by
transitive import trace), stealth is genuinely opt-in, and the URL-slug year
fix is correct across 20 constructed edge cases. The defects cluster in the two
advertised *safety gates*:

- **The validator gate fails open.** `parse_bikez_detail` always synthesises
  manufacturer/model/year from the URL slug and `validate_spec` only requires
  those to be non-empty, so a 404 / JS-shell / layout-drifted page becomes a
  "validator-clean", import-ready spec **with a clean drift signal** — exactly
  inverting the tool's purpose.
- **Cache poisoning.** `looks_blocked()` flags only 403/429/503, so 404/500/
  502/504 are treated as successful fetches, written to the disk cache with no
  TTL, and re-served forever. A 5xx also stops tier escalation dead.
- **Multi-word manufacturers split silently**: `manufacturer='Moto'`,
  `model='GUZZI V7 III'` — and it passes the validator. The legacy
  `crawl_bikez` repairs this; the new script never does.
- **robots.txt fails open on 5xx** (RFC 9309 §2.3.1.4 requires assuming
  complete disallow), and **Crawl-delay is never honoured**.
- **The robots layer has zero test coverage** — every test sets
  `respect_robots=False`, so deleting the layer `docs/SCRAPING.md` calls a
  "hard rule" leaves all 22 tests green.
- The stealth tier passes `solve_cloudflare=True` — i.e. it programmatically
  defeats an anti-bot interstitial — which no operator-facing doc discloses.

### 3.4 — Other confirmed-but-deferred

- **25 specs publish bore/stroke that cannot produce their own displacement**
  (Ninja 400 declares 399 cc with a geometry worth 633 cc); the validator only
  warns, and the wrong numbers render on the public spec sheet.
- **A weight-1.0 instrumented ZX-9R row is permanently shadowed** by a
  weight-0.7 magazine row, because binding takes the first in-range entry.
- **Platform-substituted figures scored at instrumented weight** because the
  classifier keys on the `dragy` token before any substitution test.
- **Quota bypass:** `/api/simulate/compare` (2 full RK4 runs) is unmetered.
  `/api/simulate/quick` is unmetered *by design* (the slider UI auto-runs it) —
  that one is correct; compare is the real gap. Inert until billing is enforced.
- **`/api/pricing/refresh/{id}`** — unauthenticated, unrate-limited outbound
  fetch (~66 s worst case, occupying a threadpool worker), and `force=true`
  bypasses the freshness cache.
- **`/api/venues/resolve`** spends the operator's OpenWeatherMap key with no
  auth or rate limit.
- **`/api/simulate/save`** is anonymous, unrate-limited, trusts the
  client-supplied ET and takes an unbounded `notes` string — twenty calls own
  the public leaderboard.
- **`rev limiter is a zero-hysteresis torque cliff`** — rev-limited bikes enter
  a limit cycle, so `run_top_speed`'s plateau detector never fires and the API
  reports e.g. 103 s / 7.2 km to terminal velocity.
- **`slip_ratio` is discontinuous at the traction limit** (~140× collapse at
  the moment the tire starts spinning), starving the tire thermal model.
- **Sport-category `Cd × 0.55` normalisation** halves the drag area of 192/193
  sport specs, leaving the catalog and the hand-curated references disagreeing
  by ~1.8× on Cd·A for the *same* motorcycle.
- **`test_patch_2026_07_13.py` is 16/17 vacuous** — it copies the shipped DB,
  which already has the patch applied, then asserts values that were already
  true, so it passes even if the patch's mutation logic is deleted.
- **The July-13 epoch's largest fix (fixed-point traction cap) has no
  revert-sensitive test.**
- **INVARIANTS I7 names `tests/test_auth.py` as enforcing the JWT
  default-secret boot guard — no such test exists.**
- **`public/robots.txt` shadows `app/robots.js`**, so the `Disallow` of
  `/account`, `/login`, `/signup` never reaches crawlers.
- **Sitemap's offline fallback assumes contiguous bike IDs 1..600**; real IDs
  are sparse up to 4637, so it omits 198 real pages and emits 257 phantoms.
- **`sim_run_start` / `sim_run_success` fire on disjoint modes**, so the funnel
  can never convert — and the default quick-sim path emits neither.

### 3.5 — The queued cluster retune is ill-posed as specified

`small_i4_screamer`'s −0.976 bias is **111 % attributable to a single
benchmark** (ZX-25R, −1.84 s) whose only cluster-mate (ZX-4RR) is already
+0.26 s the other way — any knob that fixes one worsens the other. Combined
with §3.1, the retune should not proceed as written.

---

## 4. Production signals

- **Sentry — 2 open issues, both in the chat agent.**
  - `MOTOQUANT-API-1` (9 events, last 2026-07-21, a real user on an iPhone via
    the Instagram in-app browser): Groq rejects a tool call whose args are
    strings. **This is benign noise, not a broken chat** — the salvage path
    parses the exact prod payload correctly (verified against the verbatim
    `failed_generation`), but Sentry's OpenAI integration captures the 400 at
    the SDK boundary with `handled: no` before our `except` sees it. It is
    polluting a 2-issue error stream. Worth silencing, not "fixing".
  - `MOTOQUANT-API-2` is a genuine crash (`int('<result_of_search_bikes_function>')`).
    **PR #117 fixes this one.** Note it does **not** fix API-1 — that 400
    happens provider-side before our code runs.
- **PostHog — zero events in 90 days.** The funnel code shipped in PR #114 is
  real, but `POSTHOG_API_KEY` is unset (operator item O2), so every user-facing
  KPI is still unmeasurable.
- **Vercel** deploys the preview Ready on this branch — the web build is
  genuinely healthy.

---

## 5. Operator items (unchanged, all confirmed still blocking)

| # | Item | Evidence from this audit |
|---|---|---|
| **O1** | **Actions billing** | No runner assigned to any job since 2026-07-13. `runner_id: 0`, 1–3 s wall time, log download 404. PR #114 and #116 merged **unverified**. This is the highest-leverage item on the list. |
| **O2** | `POSTHOG_API_KEY` | PostHog has **0 events in 90 days**, confirmed by query. |
| O3 | Oracle steps 1–4 | Untouched (PR #102 still draft). |
| O4 | Vercel BLOCKED-deploy setting | Not verifiable from here. |
| O5 | PAT / `VERCEL_TOKEN` rotation | `deploy-preview` still no-ops on unset `VERCEL_TOKEN`. |

**PR disposition:**
- **#117** — real fix for a live crash (`MOTOQUANT-API-2`). Worth merging.
- **#88** — its content was re-implemented in PR #114; verify and close.
- **#102** — based on a pre-#114 `main`; needs a rebase before it is assessable.

---

## 6. Method note

**All 12 finder dimensions completed**, producing **82 raw findings**. The box
is 4-core, which caps agent concurrency at 2, so the last four dimensions (dead
code, DB/catalog, dependencies, PR #116 review) landed well after the first
eight; their findings are folded in above.

**Everything in §2 was independently re-verified by the session before being
acted on** — not taken from an agent's summary. Every fix was proven
*revert-sensitive* rather than merely green, per AGENTS.md rule 3.

---

## 7. Suggested next session, in order

1. **Next.js 15/16 migration** (§3.3e) — newly urgent: 14.x is end-of-life with
   21 advisories and **no fix path inside the major**. This is now the only
   finding with an external clock on it.
2. **Gearing data fix for the four heavies** (§3.2) — unblocks the whole
   speed-limiter annotation pass, and removes a test whitelist that is
   currently protecting a data bug.
3. **Decide the `is_at_wheel` question** (§3.1) — a prerequisite for any
   cluster retune, and an epoch-scale decision (ADR-0002). §3.3d (`has_vht`)
   is the same shape and should be decided in the same pass.
4. **Pin the production dependency set** (§3.3e) — `>=`-only with no lockfile
   means the Docker image is not reproducible from a git commit. Cheap to fix,
   and it is a prerequisite for trusting any future security audit.
5. **Catalog de-duplication** (§3.3) — mechanical, but touches the DB and
   headline counts, so it wants its own reseed + sweep + stat sync. Fix the
   `import` vs `reseed` winner disagreement at the same time.
6. **Harden the Scrapling safety gates** (§3.3f) — the validator gate failing
   open and the 404/5xx cache poisoning both undermine the toolkit's stated
   purpose; neither is hard to fix.
7. **The 8 quickshifter parts** (§3.3c) — priced SKUs that move ET by exactly
   zero.
8. **Close the remaining pre-revenue gaps** (§3.4 quota/rate-limit cluster)
   before `MOTOQUANT_BILLING_ENFORCE` is ever flipped.
9. **`test_patch_2026_07_13` vacuity** (§3.4) — it guards a mandatory link in
   the reseed chain and currently guards nothing.
