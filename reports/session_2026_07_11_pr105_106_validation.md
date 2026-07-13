# PR #105 / #106 post-merge validation & measurement — 2026-07-11

Operator request: *"evaluate all the changes, measure all the improvements,
ensure everything is merged properly and nothing is broken, run all benchmark
and validation tests on all bikes, parts, tyres — so we can update accuracy
and other numbers for the next website update (PR #107)."*

Method: full gate re-run on merged main (`da0a08e`) + fresh full-catalog
weighted sweep + A/B quantification against a pre-merge worktree (`af58d3c`)
+ a multi-agent adversarial review of the PR #105 physics diff + line-item
recount of every claim in the PR #106 scrape corpus against `motoquant.db`.

## Verdict up front

**Both PRs are merged properly and nothing is broken.** The branch tip equals
`origin/main` (`da0a08e`); PR #105 merged 07:28 UTC, PR #106 07:30 UTC.
All gates green; the published accuracy numbers are **unchanged and
re-verified** (PR #105 is proven NA-bit-identical across the entire catalog,
and PR #106 shipped data files only). One gap found and fixed in this pass:
the ram-air fix had no pinning test (reverting it left the suite green) —
NEW `tests/test_ram_air_wind.py` closes it (4 tests; 2 fail on revert,
verified in the pre-fix worktree).

## Gates (merged main, this session)

| Gate | Result |
|---|---|
| `make health` | HEALTHY — baselines bit-identical, lint clean, catalog 541/593/254/20/1860, headline stats in sync, secret scan clean |
| `scripts/check_baselines.py` | K5 10.0334049358 / R1 10.2859306491 / Hayabusa 10.4712019198 — Δ +0.00e+00 ×3 |
| Full suite (run twice) | **4,472 ran / 0 failed / 0 errors / 91 skipped** (756 s; junitxml-counted; both runs exit 0) |
| Slow tier (`MOTOQUANT_SLOW_TESTS=1` — full-catalog golden re-sim via `db_row_to_config` + recommendations integration) | **73 passed / 0 failed** |
| Full weighted sweep (542 specs vs 221-benchmark corpus) | **byte-identical to `acc_final_2026_07_06.json`** — committed as `reports/acc_verify_2026_07_11.json` |
| `/validation` viz data regen (`gen_accuracy_viz_data.py`) | identical in every data field to the committed `accuracy_data.json` (only the `--stamp` label differs) |

The scratch env needed `pip install --force-reinstall cffi` before
`tests/test_api.py` would collect (broken `_cffi_backend` — environment
issue, not repo).

## Verified numbers for the PR #107 website update

Everything the site currently claims remains correct after both merges —
**no accuracy or catalog number needs to change**:

| Stat | Value | Status |
|---|---|---|
| Bikes / parts / tires / fitments / venues | 541 / 593 / 254 / 1,860 / 20 | unchanged, re-counted from DB |
| Benchmarks / matched | 221 unique / 246 matched | unchanged |
| Weighted mean \|Δ\| | **0.2165 s** (raw JSON 0.2166) | re-verified byte-identical |
| Weighted bias | **+0.0212 s** | re-verified |
| Within ±0.10 s / ±0.20 s | 82 / 137 | re-verified |
| Top-10 mean error | ±0.006 s | unchanged (viz data identical) |
| Reference baselines | K5 10.0334 / R1 10.2859 / Hayabusa 10.4712 | Δ +0.0000 ×3 |
| Tests | 4,472 ran / 0 failed (was quoted ~4,324) | may be bumped if #107 quotes a count |

Note for the #107 session: its branch (`claude/new-website-design-ok8fzv`)
is based on `af58d3c` — **pre**-#105/#106 main. Merge main in before landing
(no web/ overlap expected; `CHANGELOG.md` may conflict trivially).

## PR #105 — measured improvements (A/B vs pre-merge `af58d3c`)

Every stock (NA) scenario is **bit-identical** pre/post — spec path, DB
path, and the whole weighted sweep. The fixes only change what they claim
to change:

### 1. Forced induction now live during clutch slip (all four boost types)

Hayabusa Gen1 reference + synthetic boost (spec path):

| Scenario | pre-105 ET | post-105 ET | ΔET | Δ60ft |
|---|---|---|---|---|
| Turbo, steady 1.0 bar | 9.6881 | 9.3129 | **−0.375 s** | −0.297 s |
| Roots SC, 0.7 bar | 9.8046 | 9.4602 | **−0.344 s** | −0.227 s |
| Centrifugal SC, 0.7 bar | 9.8985 | 9.5985 | **−0.300 s** | −0.140 s |
| N2O, 50 hp single stage | 10.0489 | 9.8155 | **−0.233 s** | −0.097 s |
| Zero-boost control (`sc_roots` @ 0.0 bar) | 10.4460 | 10.4460 | +0.0000 | +0.0000 |

Production parts path (DB Hayabusa Gen1, `apply_part_to_config`, part 96
Schnitzer Turbo Kit 0.827 bar): advertised gain was **−0.900 s pre-fix,
−1.191 s post-fix** — every boosted build's ROI was understated by ~0.3 s
(~32% of this part's true gain). This flows to `/api/simulate` with boost
parts, the build optimizer, boost-part cost-per-tenth, and the outlaw
pipeline.

### 2. Top-speed plateau detection (time-based)

K5 with 160 ms shifts, `run_top_speed()`: pre-fix reported terminal at
**4.24 s / 84 m** (a gearshift misread as the aero plateau); post-fix
**34.16 s / 2,315 m**. Terminal *velocity* is unchanged either way.
Catalog exposure audit: every stock config carries 100–140 ms shifts, under
the old ~150 ms misdetection threshold — verified K5/R1/Hayabusa stock
top-speed outputs bit-identical pre/post, so **no published top-speed
number moved**; the bug hit modified builds and custom API calls.

### 3. Adaptive step-budget growth

Never-locking clutch (`spring_preload_n=1`), `run(max_time=5,
use_adaptive_dt=True)`: pre-fix silently truncated at **exactly 2.4995 s**
(= max_time/2); post-fix runs the full 5.0000 s. Reviewer stress-proved the
growth is bounded: at the API's 300 s cap the worst case is 600,001 samples
(~200 MB peak RSS), no runaway.

### 4. Ram-air uses airspeed

Hayabusa @ 10 m/s headwind: ET 10.6807 → 10.6772 (**−3.5 ms**), exactly as
the commit documents; 60ft unchanged (ram gate is 20 m/s airspeed).
Bit-identical at zero wind (IEEE `v + 0.0 == v`), proven empirically.

### Adversarial review verdict (3 independent reviewers, full findings in the session workspace)

- **FI slip fix**: correct on all four audit axes — multiplier applied
  exactly once per branch (locked / lock-transition / slip), NA path is a
  literal `1.0` early-return (bit-exactness is structural), the slip-branch
  torque cache is applied-at-use (never caches the multiplier), P_boost
  units consistent. Two **pre-existing** FI blind spots noted for the
  epoch-gated list: precomputed shift points ignore the FI multiplier
  (cancels exactly for steady turbo/SC, slightly off for N2O/mid-spool),
  and `ClutchModel`'s slider cap reads raw torque (dead code in the sim path).
- **Top-speed/adaptive fix**: correct; plateau edge-detection is
  index-correct, catches end-of-array plateaus the old code missed, and is
  shift-time invariant (50/160/300 ms → 33.6/34.2/34.9 s). All 18 output
  arrays grow together (list-diffed). Fixed-dt path byte-identical (md5
  over all 18 channels). Pre-existing nit: `/api` allows `max_time_s < dt`
  → unhandled ValueError (hardening candidate); stale "17 arrays" comment
  in api.py.
- **Ram-air fix**: correct — wind sign convention consistent with
  drag/lift, tailwind edge safe (the `< 20` gate returns 1.0 for negative
  airspeed; no phantom boost from behind), zero-wind bit-identity proven at
  the bit level. **Real gap (fixed this session): shipped with no pinning
  test** — with `aero.py` reverted the entire suite stayed green. NEW
  `tests/test_ram_air_wind.py` (4 tests, 2 fail on revert) closes it.
- All 5 new PR-105 tests verified **fail-on-revert** in the pre-fix
  worktree (4 failures) and pass on main — genuine production-path
  regression tests per INVARIANTS I8.

## PR #106 — scrape corpus integrity (line-item recount vs `motoquant.db`)

**No fabrication tells anywhere; every headline claim recounts, most
exactly.** All three JSONs form perfect id-bijections with the DB (541
bikes, 593 parts, 254 tire rows via 120 families; 0 phantom ids, 0 missed
rows), every embedded DB value matches the live DB bit-exactly, and 100%
of spec checks/benchmarks/tire prices carry http sources (one exception
below).

Exact recounts: 214 spec discrepancies / 168 bikes / 60 high-confidence /
field split 70-64-49-23-8 ✓; 103 benchmarks = 67 QM (20 instrumented + 24
magazine + 18 aggregator + 5 forum) + 13 top-speed + 23 zero-to-100 ✓;
parts 289 priced (72 INR + 217 USD) / 54 movers >15% / 191 `sku_exists:
low` (brand concentration matches exactly) / 6 discontinued (ids
51/95/116/146/407/504) ✓; tires 95 current / 8 discontinued / 16 not-found
/ 1 unknown, 62 priced families / 95 price points ✓. The report's 25-row
price-move table verified row-by-row against JSON **and** current DB
prices (0 mismatches; the −46% JT sprocket row is a correct 3-way tie
break).

Honest-data nits for the consumption pass (none invalidates the corpus):

1. Coverage is really **540/541** — id 279 (RGV250 Gamma) is honestly
   `researched: false`; the report headline rounds up.
2. 2 of the 214 "discrepancies" have `web_value == db_value` (ids 243,
   772 — wet/dry mislabel flags); strict numeric count is **212**.
3. **Benchmark value keys are inconsistent** (`et_s` vs `value` vs
   `speed_kmh`) — an importer reading only `et_s` silently drops 3 QM + 2
   zero-to-100 rows. Coalesce both keys.
4. Part id 368 (Galfer DF rotor) is priced with **no source URL**; 6 more
   priced rows are honest *proxy* prices on `found: false` SKUs (ids 140,
   262, 309, 470, 477, 506) — route through the low-sku honesty triage,
   not direct repricing. Strictly-verifiable priced count: 283 + 6 proxy.
5. DB availability for the 6 discontinued parts is not yet flagged
   (expected — scrape was read-only), so the optimizer/ROI still treats
   discontinued Bazzaz/AEM units as purchasable until the update pass.

## New quarter-mile benchmark triage (consumption-pass work order)

The 67 scraped QM finds vs the existing 221-row corpus (word-boundary
matching + year overlap, same matcher as the sweep):

- **4 NEW instrumented** (weight 1.0 — highest value): KTM Duke 200 16.10,
  Kawasaki Vulcan S 13.03, BMW M 1000 R 9.80 (MCN dragstrip), Honda CB500F
  13.36.
- **11 NEW magazine** (0.7): Indian Scout 11.93, Hyosung GT650R 12.84,
  FJR1300 10.98 & 10.68, V-Strom 650 12.54, RZV500R 11.77, 750 H2 Mach IV
  12.00, KTM 990 RC R 11.20, NS400R 13.03, K1600 GT 10.86, Fat Bob 114 12.76.
- **15 NEW aggregator/forum** (0.5/0.3): Scrambler 1100, Versys 650, W800,
  R1200GS, S1000XR, Thruxton R, 690 Duke R, Vitpilen 701, RC30, SR400,
  V-Strom 800DE, Grom, SV650X, Scout Bobber, 701 Supermoto.
- **6 CONFLICTS (>0.3 s vs existing — adjudicate, don't blind-add)**:
  Hayabusa Gen3 8.97 (MCN launch test) vs 9.75 (Sport Rider); R1 04-06
  9.90 vs 10.31 (note: the *instrumented* MotoStatz 10.31 duplicate
  corroborates the EXISTING row); 848 EVO 11.40 vs 10.75; 1098 10.90 vs
  10.40; Duke 390 13.30 (MotoStatz) vs 14.00 (MCN instrumented); K1300S
  10.62 vs 10.22.
- **31 duplicates** — the scraper independently re-found existing corpus
  rows (strong corroboration; several confirm DERIVED rows, e.g. V-Rod
  Muscle 11.88 instrumented vs DERIVED 11.8 — upgrade that row's source
  weight when consuming).

## Scope-out (recommended next passes, in order)

1. **Scrape-consumption pass** (data-only, deliberate):
   benchmarks per the triage above (+13 top-speed + 23 zero-to-100 finds
   for the future 0-100 corpus); 60 high-confidence spec fixes →
   `known_bikes*.py` → full reseed chain → golden + surrogate regen →
   fresh authoritative sweep (spec fixes WILL move matched-bike ETs — that
   is the point); 72 INR part reprices + 217 USD landed-cost + 6
   discontinued flags + 191 low-sku honesty triage; 8 discontinued + 16
   not-found tire families flagged (incl. Avon "Roadrunner"→"Roadrider"
   naming fix), 95 tire price points.
2. **Epoch-gated physics rebaseline** (items 1–4 of the July-10 report:
   `a_net≥0` no-deceleration clamp, iterated weight-transfer/traction cap,
   slip-phase ram-air+parasitic, front-wheel inertia radius) + re-run
   topspeed sweep + stat sync. Add from this session's review: FI-aware
   shift points (N2O/mid-spool only).
3. **Small hardening items**: validate `boost_type` strings (an invalid
   string silently gets the boosted DA floor ×0.97 but zero boost — found
   during A/B); API `max_time_s < dt` ValueError → 422; remove or wire the
   dead `AeroParams.headwind_ms`/`crosswind_ms` knobs; stale "17 arrays"
   comment.

## Artifacts

- `reports/acc_verify_2026_07_11.json` — fresh sweep, byte-identical to
  `acc_final_2026_07_06.json` (the no-drift proof).
- `tests/test_ram_air_wind.py` — NEW pinning tests for 40cf813.
- This report.

## Addendum — slow-tier result

`MOTOQUANT_SLOW_TESTS=1` full-catalog golden regression
(`tests/test_regression_snapshot.py`, re-sims every current bike via
`db_row_to_config` against the golden snapshots) + the recommendations
integration tier (`tests/test_recommendations.py`): **73 passed / 0 failed
/ exit 0** (~75 min serial). The DB simulation path for all 541 bikes is
drift-free post-merge.
