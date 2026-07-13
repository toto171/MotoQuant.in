# July 13, 2026 — physics epoch + scrape-consumption + hardening (the "all 3 things" pass)

Operator instruction: *"do all 3 things, verify it works and then ship it
when ready, also update the website numbers and benchmarks accordingly"* —
the three passes scoped in `reports/session_2026_07_11_pr105_106_validation.md`:

1. **Data batch** — consume the 2026-07-10 scrape corpus (benchmarks, spec
   fixes, parts prices, tire flags).
2. **Physics epoch** — the four confirmed-but-epoch-gated model fixes from
   the July-10 review, with the deliberate rebaseline they require.
3. **Hardening batch** — boost_type validation, API `max_time_s` floor,
   dead-knob removal.

Shipped in the same window (separate instruction): PR #108 (validation
report) and PR #107 (STAGED v4 website redesign) merged to main.

## Headline (the new published numbers)

| Stat | July-6 published | This epoch | Note |
|---|---|---|---|
| Benchmark corpus | 221 unique / 246 matched | **250 unique / 277 matched** | +29 rows from the scrape triage |
| Weighted mean \|Δ\| | 0.2165 s | **0.2533 s** | see decomposition below |
| Weighted bias | +0.0212 s | **+0.0166 s** | better centered |
| Within ±0.10 s / ±0.20 s | 82 / 137 | 74 / 137 | of 277 (was of 246) |
| Top-10 mean error | ±0.006 s | **±0.009 s** | |
| References (K5 / R1 / Hayabusa) | 10.0334 / 10.2859 / 10.4712 | **9.9331 / 10.1436 / 10.3633** | vs real-world 9.97 / 10.30 / 10.40 — K5 and Hayabusa now track CLOSER than the old pins |
| Top-speed sweep (83 matched) | — | mean \|Δ\| 35.0 km/h, bias +28.5 | unchanged by the epoch (see finding below) |

**Honest decomposition of the |Δ| move (measured, not estimated):**

| Step | corpus | w\|Δ\| | bias |
|---|---|---|---|
| July-6 published (old physics, old corpus) | 246 | 0.2166 | +0.0212 |
| + data batch only (old physics, new corpus + spec fixes) | 277 | 0.2404 | +0.0184 |
| + physics epoch, pre-retune | 277 | 0.4618 | +0.3818 |
| + per-cluster knob retune (final) | 277 | **0.2533** | **+0.0166** |

So: **+0.024 of the headline move is corpus expansion** (29 new benchmarks
deliberately target previously-unmeasured bikes — the uncovered tail is
naturally less-centered; adding them is honest coverage, not regression),
and **+0.013 is the net cost of physically-correct dynamics** after
recalibration. The epoch buys, in exchange: deceleration exists (drag/RR
act through gearshift torque cuts — 0.755 m/s of previously-suppressed
drag loss on the K5's own shifts; negative-g telemetry now realistic),
the weight-transfer→traction cap is converged instead of fed an inflated
rear load (wet/salt venue penalties are now honest — the old model
under-penalized wet by up to 46% of static rear load), ram-air+parasitic
act during clutch slip, and front-wheel inertia uses the front radius.

## Pass 2 — physics epoch detail

Fixes (July-10 review items 1–4, `motoquant/physics.py` +
`submodels/drivetrain.py`):

1. `a_net = max(0,·)` now applies **only while the clutch slips** (launch
   anti-rollback); locked-clutch deceleration is real. Same condition on
   all four RK4 stage clamps.
2. Traction cap fixed-point refinement: when clipped, 2 extra passes of
   (capped accel → weight transfer → cap). Unclipped steps never enter the
   branch (their float stream is untouched).
3. Slip + lock-transition branches now mirror the locked branch exactly:
   crank torque × ram-air × FI − parasitic (parasitic still gated off for
   at-wheel dyno curves).
4. `effective_mass` divides front-wheel inertia by the FRONT rolling
   radius (the CLI front-tire override finally has its documented effect).

Per-fix baseline movement (K5): fixes 3+4 −1.3 ms; fix 1 +19.3 ms;
fix 2 +251 ms (the traction cap was the big inflation).

**Recalibration:** new `CategoryProfile.mu_peak_scale` knob (multiplicative,
preserves per-bike rubber ordering, 1.0 = bit-identical no-op — liveness +
guard pinned in `tests/test_profile_knobs.py`). Grid-tuned per cluster via
`scripts/tune_cluster_knobs.py` against the 277-match corpus:

| cluster | knob | w\|Δ\| | bias |
|---|---|---|---|
| litre_sport_195p | scale 1.08 | 0.147 | +0.038 |
| litre_sport_600_1000 | scale 1.07 | 0.177 | +0.002 |
| sport_twin_600_1300 | scale 1.085 (× override 1.31) | 0.256 | −0.000 |
| mid_twin_500_700 | scale 1.14 | 0.152 | −0.014 |
| mid_twin_300_500 | scale 1.12 | 0.400 | +0.124 |
| single_300_500 | override 1.10 → 1.18 | 0.492 | −0.040 |
| entry_200_300 | (unchanged) | 0.295 | +0.137 |
| entry_150_200 | (unchanged) | 0.754 | −0.030 |
| two_stroke | scale 1.15 | 0.659 | +0.129 |
| cruiser_1300p | scale 1.20 | 0.210 | +0.050 |
| other | scale 1.15 | 0.302 | +0.024 |
| small_i4_screamer | scale 1.30 (n=2) | 0.417 | +0.032 |

Two clusters BEAT their old-physics accuracy outright (cruiser-1300+
0.267→0.210, mid-twin-300-500 0.448→0.400); sport-twin and single-300-500
carry the residual epoch cost (within-cluster reordering that a launch-grip
knob cannot chase — the epoch redistributes time mid-run).

**New finding — the litre top-speed overshoot is NOT the decel clamp.**
The July-10 report hypothesized `a_net≥0` as a plausible mechanism for the
documented +20–40 km/h top-speed overshoot. A/B disproves it: the full
top-speed sweep (83 matched) is IDENTICAL old-vs-new physics (mean |Δ|
35.0 km/h, bias +28.5 both) — sims approach drag equilibrium
asymptotically and never held an overshoot. The real cause is that the
model has **no factory speed-limiter** — litre bikes sim to their
aero-limited 320–340 km/h against 299-limited published figures. Fix
scoped for a future pass: a `speed_limiter_kmh` spec field consumed in
`run_top_speed` (many benchmark rows already say "factory-limited").

Baselines: new pins in `scripts/check_baselines.py` (bit-identical
contract re-established), `AGENTS.md`, `docs/INVARIANTS.md`, and 15 test
modules updated in the same commit. Historical documents (CLAUDE.md chain,
reports/, STATUS.md) deliberately NOT rewritten.

## Pass 1 — data batch detail

- **Benchmarks**: +29 quarter-mile rows (4 instrumented / 10 magazine / 15
  aggregator-forum; source labels worded so `sweep_lib.source_quality`
  assigns the scrape's honest source type — verified programmatically).
  All 6 conflicting finds adjudicated and REJECTED with web verification
  (Hayabusa Gen3 8.97 = Bruce Dunn best-case vs pro spread 8.97–10.03;
  Duke 390 13.3 = perfect-execution vs real stock passes 13.6–13.95; the
  4 others were lower-weight sources conflicting with existing
  instrumented rows). The FJR1300 2003-generation figure was skipped as
  period-incorrect for the 2013-2022 catalog row. ET corpus: 221 → 250
  unique rows. Top-speed corpus: 77 → 86 rows (+9 verified, Duke 200
  factory-claim row replaced by the instrumented 140.3; skipped as
  implausible/duplicate: Hayabusa-25th "312" vs the 299 limiter, G310R
  "160" speedo-indicated, LFC 700 duplicate).
- **Spec fixes**: 56 of the 60 high-confidence discrepancies applied to
  `known_bikes*.py` (agent-applied, validator-gated; 4 skipped with
  documented reasons — wet/dry mislabels and a race-kit-trim consistency
  hold). Notables: YZF-R9 168→117.4 hp, RC213V-S 215→159 hp (street mode),
  Z H2 SE 239→197.3 hp, GSX-R 1000 K1/K3 178/185→160/164 hp, 23 missing
  kerb masses filled.
- **Parts**: `scripts/patch_2026_07_13_scrape_data.py` (idempotent, proven
  ×2, tests in `tests/test_patch_2026_07_13.py`): 72 INR reprices from
  live listings + 210 USD-only through the landed-cost formula (7
  proxy/no-source rows excluded by policy), 6 discontinued Bazzaz/AEM
  units flagged, 25 fictional-brand SKUs renamed to honest class names
  (ClutchCo ×8, Regina Pro ×9, Sprocket Specialists ×8 → brand `Generic`).
- **Tires**: 24 families (48 rows) flagged discontinued/not-found via
  `available_india=0` + a data_source annotation; 19 unambiguous India
  price points applied (26 ambiguous/conflicting points skipped by the
  conservative rule and counted).

## Pass 3 — hardening detail

- Unknown `boost_type` strings now raise at engine construction (they
  previously simmed almost-like-NA while silently taking the ×0.97
  boosted-DA floor); the API parts path converts it to a 422 naming the
  offending part. `tests/test_hardening_2026_07_13.py`.
- `max_time_s` request floor `ge=0.1` on top-speed + distance routes (a
  sub-dt value used to raise an unhandled ValueError deep in the engine).
- Dead knobs removed: `AeroParams.headwind_ms`/`crosswind_ms` (never read;
  the live wind path is `EnvironmentParams.wind_speed_ms`+direction; old
  DB blobs are filtered by the bridge) and the never-called
  `RiderDynamicsModel.cog_shift`/`wheelbase_weight_split` pair (July-10
  item 5, "delete" option).
- Stale "17 arrays" comment corrected.

## Regen artifacts (same session, per the standing contracts)

- Full reseed chain run (reseed → reference patch → catalog integrity →
  tire dedup → scrape-data patch); counts stable at 541/593/254/1860/20.
- Golden regenerated (`tests/data/sweep_snapshot.json`) — fast tier green.
- Surrogate v2.5 regenerated (~8.5k sims + numpy retrain) — see commit.
- `/validation` viz data regenerated (277 matched, stamp 2026-07-13).
- Sitewide stat + accuracy-claim sync against the STAGED v4 redesign.

## Verification

See the PR body for the full gate table (make check, full suite, slow
tier, baselines, web build, audit).
