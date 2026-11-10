# Epoch 2026-11-10 — duplicate bikes shipped, gearing change NOT shipped

Evidence-gated accuracy change (ADR-0002). Two candidate changes were measured
against the published corpus; one passed its gate and shipped, the other failed
and was reverted.

| Change | Decision | Why |
|---|---|---|
| Step 1 — collapse 7 duplicate bikes, make the Fireblade SP generations disjoint, fix kerb-as-dry masses | **GO (shipped)** | every gate criterion passes |
| Step 2 — inferred primary ratios for small bikes, sibling gearing, Tier-1 matcher fix (+ Step 3 retune) | **NO-GO (reverted)** | high-confidence sub-400 cc accuracy gets worse and no physically plausible retune recovers it |

Pinned references are bit-identical at every step: K5 9.9331 / R1 10.1436 /
Hayabusa 10.3633 (`scripts/check_baselines.py`, Δ = 0.00e+00).

Machine-readable evidence: `reports/epoch_2026_11_10_evidence.json` (every
stage's aggregates, the per-bike Step-2 table, the retune grids).
Authoritative sweep: `reports/acc_final_2026_11_10.json`.

All numbers below are the spec path, `run(use_adaptive_dt=False, max_time=26.0)`,
matched and weighted exactly as `scripts/phys_weighted_sweep.py` does
(instrumented 1.0 / magazine 0.7 / aggregator 0.5 / forum 0.3 / DERIVED 0.1).
"High-confidence" = weight ≥ 0.7.

## Step 0 — the published baseline reproduces

| | published (`acc_final_2026_08_08.json`) | reproduced on the tree |
|---|---|---|
| benchmarks / matched | 250 / 276 | 250 / 276 |
| weighted mean \|Δ\| | 0.2629 s | 0.2629 s |
| weighted bias | +0.0073 s | +0.0073 s |
| high-confidence (n=200) \|Δ\| / bias | — | 0.2287 / +0.0316 |
| high-confidence, sub-400 cc (n=26) | — | 0.3912 / +0.0475 |
| low-confidence (n=76) | — | 0.5722 / −0.2129 |
| top speed: matched / mean \|Δ\| / bias | 83 / 28.1 / +24.3 km/h | 83 / 28.1 / +24.3 km/h |
| top speed, sub-400 cc (n=29) | — | 35.5 / +35.5 km/h |
| gearing-gate flags | 152 of 538 (117 generic-primary) | 152 of 538 (117) |

Every per-cluster row equals the August report.

## Step 1 — duplicate bikes (shipped)

Eight overlapping-year pairs (audit finding F1). Seven were the same motorcycle
entered twice; the Fireblade SP is two real generations whose ranges overlapped
on 2024.

**Which row survived.** One rule for every pair: the *later, source-cited*
entry survives (the one with a dated adjudication note or citation block; the
Tier-1-backed row where neither has one), and the values the adjudication
(`duplicate_adjudication.md`) marks as sourced are applied on top. Fields it
marks as unsourced — sprockets, cassettes, tyre sizes, Cd, frontal area, valve
gear, the contested Fireblade power — keep the surviving row's existing value;
nothing was picked between two unsourced numbers.

| Bike | Survivor (removed) | Sourced values applied | Kept from survivor, unsourced |
|---|---|---|---|
| RE Continental GT 650 | 2018-2024 row, geometry adjudicated 2026-08-08 (2020-2024 row removed) | dry 202 → **182 kg** (202 was a kerb figure), wheelbase 1412 → **1398**, cooling liquid → air/oil | cassette, F17/R45, tyres, Cd 0.85 |
| RE Interceptor 650 | 2018-2024 row (2020-2024 removed) | dry 202 → **181 kg**, wheelbase → **1398**, cooling → air/oil | cassette, F17/R45, tyres, Cd 0.86 |
| RE Super Meteor 650 | 2023-2026 cited entry (2023-2024 removed) | `dry 230` → **`wet 241`** (published kerb; importer derives dry = wet − 25 = 216) | cassette, F15/R40, 150/80-16 rear |
| Honda Hornet 2.0 | 2020 row, Tier-1-backed, now **2020-2026** (2024-2025 removed) | `dry 142` → **`wet 142`** (142 is the Honda India kerb weight → dry 117) | cassette, F16/R46, 520 chain, DOHC label, tyres |
| Aprilia Tuono 457 | 2025-2026 cited entry, 47.6 hp (2024-2026 removed) | — (dry 159 already correct) | wheelbase 1370 (sources say 1349-1354; no single value given) |
| TVS Raider 125 | 2021-2026 cited entry (2022-2024 removed) | rear tyre 100/80-17 → **100/90-17** (TVS) | dry 115 kg (kerb 123; not a kerb-as-dry entry) |
| Suzuki V-Strom SX 250 | 2022-2026 cited entry, dry 155 (2022-2024, kerb-as-dry 167, removed) | — | Cd, frontal area |
| Honda CBR1000RR-R Fireblade SP | both kept; **2020-2023** and **2024-2025** | 2024 row: `dry 201` → **`wet 201`** (kerb), wheelbase 1405 → **1455** | power 217 / 215, 2024 row has no 299 km/h limiter (unsourced) |

A first pass kept the other RE row (the 2020-2024 entries that already carried
the dry-convention mass). It was replaced by the rule above before any further
work because the rule is the one the task states; both variants were measured
and are in the evidence file (variant A: overall 0.2635, GT 650 −0.64 s against
its 0.5-weight benchmark; shipped variant: 0.2620, GT 650 −0.12 s, Super Meteor
−0.19 s against a DERIVED row where variant A had +0.12 s).

**Per-bike ET (spec path):**

| Bike | old rows | new | benchmark |
|---|---|---|---|
| Continental GT 650 | 13.928 / 13.261 | 13.777 | 13.90 (aggregator, w 0.5) → −0.123 |
| Interceptor 650 | 13.951 / 13.426 | 13.795 | 13.80 (DERIVED, w 0.1) → −0.005 |
| Super Meteor 650 | 14.017 / 13.823 | 13.708 | 13.90 (DERIVED, w 0.1) → −0.192 |
| Hornet 2.0 | 17.959 / 17.854 | 17.359 | none |
| Fireblade SP 2024-2025 | 9.796 | 9.837 | 9.95 (Cycle World, w 0.7) → −0.113 |
| Fireblade SP 2020-2023 | 10.137 | 10.137 | 9.95 → +0.187 (unchanged) |
| Raider 125 | 19.348 / 19.301 | 19.343 | none |
| V-Strom SX 250 | 16.188 / 16.152 | 16.152 | none |
| Tuono 457 | 13.276 / 13.008 | 13.008 | none |

No other bike's ET moved (per-bike comparison of all 531 specs against the
Step-0 sweep).

**Step-1 gate (vs Step 0):**

| # | Criterion | Baseline | Step 1 | |
|---|---|---|---|---|
| 1 | pinned references bit-identical | — | Δ 0 | pass |
| 2 | weighted \|Δ\| ≤ 0.2649, \|bias\| ≤ 0.02 | 0.2629 / +0.0073 | **0.2620 / +0.0087** (273 matched) | pass |
| 3 | high-confidence \|Δ\| not worse by > 0.005; sub-400 hi-conf not worse | 0.2287 ; 0.3912 | 0.2285 ; 0.3912 | pass |
| 4 | no cluster (n ≥ 10) worse by > 0.03 | — | largest: mid-twin-500-700 +0.0011 | pass |
| 5 | top-speed mean \|Δ\| not worse | 28.1 km/h | 27.8 km/h | pass |
| 6 | generic-primary flags halve | n/a for Step 1 | 117 → 114 | n/a |
| 7 | knob changes physical | — | no knob changed | pass |

Matched benchmarks fall 276 → 273 only because three removed rows no longer
double-count a benchmark. Gearing-gate flags: 152 of 538 → **148 of 531**.

## Step 2 — gearing (measured, NOT shipped)

Built on the spec/importer path exactly as specified:

* **(a) class primary.** For a geared 4-stroke with ≤ 2 cylinders and < 700 cc
  that would otherwise take the Tier-2 litre-bike primary: interpolate by
  displacement between the four primaries the repo carries *with a
  service-manual citation* — 155 cc 3.042 (Yamaha R15 family, 73/24), 296 cc
  3.087 (Ninja 300), 399 cc 2.073 (Ninja 400, 85/41), 649 cc 2.095 (Ninja 650);
  flat outside. A smooth rule instead of the verifier's three buckets because
  the buckets put a cliff at 250 cc (3.04 → 2.18) that the verified data does
  not support; no separate single/twin values because the only verified small
  single is the Yamaha 155. Two-strokes and CVT scooters excluded (no sourced
  primary of either kind exists in the repo).
* **(b) siblings.** Same manufacturer, bore × stroke, cylinder count and stroke
  cycle as a catalog bike with a spec / Tier-1 primary → take that primary
  (verified donors first, else the most common value). 23 bikes.
* **(c) matcher.** Whole-token Tier-1 matching with an explicit glued-variant
  allowlist (R1M, Z900RS, ZX-10RR …) and a neutral-token allowlist; CBR250RR and
  the two Apache RTR 160 engines stop inheriting another bike's entry. Eight
  Tier-1 primaries on flagged small bikes with top-gear-at-peak > 1.25 × terminal
  (Hornet 2.0, Apache RR 310, Pulsar 220F, FZ-X, Xtreme 160R, Speed 400, CB 300R,
  Himalayan 450) were ignored in favour of the class value; three more marked
  unverified.

180 primaries changed; pinned references unaffected.

**What it did (no retune, vs Step 1):**

| | Step 1 | Step 2 | Step 3 (best plausible retune) |
|---|---|---|---|
| weighted \|Δ\| / bias (273) | 0.2620 / +0.0087 | 0.2762 / −0.0076 | 0.2722 / +0.0012 |
| high-confidence (200) | 0.2285 | 0.2453 | 0.2405 |
| high-confidence sub-400 cc (26) | 0.3912 | 0.5179 | 0.4835 |
| entry-200-300 (n=14) | 0.2311 / −0.018 | 0.5804 / −0.435 | 0.4698 / −0.194 |
| entry-150-200 (n=13) | 0.7015 / −0.011 | 0.7362 / −0.062 | 0.7362 / −0.062 |
| mid-twin-300-500 (n=8) | 0.3614 | 0.3953 | 0.3953 |
| single-300-500 (n=16) | 0.5086 | 0.5090 | 0.5090 |
| top speed, all (83) | 27.8 / +24.0 km/h | 25.8 / +22.0 | 25.8 / +21.9 |
| top speed, sub-400 cc (29) | 35.5 / +35.5 | 29.7 / +29.6 | 29.7 / +29.5 |
| gearing flags (generic-primary) | 148 (114) | 46 (8) | 47 (8) |

ET moved on 178 bikes, median −0.29 s; largest: KLX300 **+1.87 s** (its
dirt-bike cassette plus the inferred primary is far too short — the rule also
creates errors), G310GS −1.32, Hunk 160R −1.29, G310R −1.14, 250 Adventure
−1.07, Apache RTR 165 RP −1.01, CB200X −0.98, Apache RTR 180 −0.93, Pulsar N160
−0.90, X-Blade 160 −0.86, **YZF-R25 −0.84** (instrumented benchmark), Karizma R
−0.81, **CBR250RR −0.81** (instrumented benchmark), SP 160 −0.80, Karizma XMR
210 −0.78.

**Step 3 — retune.** Grids toward neutral only (`scripts/tune_cluster_knobs.py`
objective, 3 workers; all in the evidence file):

* entry_200_300 — the cluster the change displaced. With over-clutch, decel,
  parasitic and grip scale ALL at their neutral values the cluster is still
  0.497 (high-confidence 0.493); the best plausible setting (grip scale 1.12 →
  1.00, parasitic 0.85 → 1.00, launch knobs unchanged) gives 0.470. The four
  re-geared instrumented bikes stay 0.4-0.7 s fast (R25, MT-25, CBR250RR,
  CBR300R) while the Ninja 300 — whose gearing was already service-manual
  verified and did not change — is pushed from +0.20 to +0.55 s. No knob can
  separate those two groups, because what separates them is not physics: the
  Indonesian instrumented tests run 1-2 s slower than MotoStatz for equivalent
  machines (the same R15/MT-15 powertrain is 17.62 s in one and 19.60 s in the
  other). The old tall gearing happened to line the sim up with the slower
  tests.
* entry_150_200 — insensitive (0.731-0.741 across the grid).
* mid_twin_300_500 — every move toward neutral makes it worse; current knobs
  are the optimum.
* single_300_500 — only a move AWAY from neutral (grip override up to 1.25)
  improves it; not permitted.

**Step-2/3 gate (vs Step 0):**

| # | Criterion | Baseline | Step 2 + best retune | |
|---|---|---|---|---|
| 1 | pinned references bit-identical | — | Δ 0 | pass |
| 2 | weighted \|Δ\| ≤ 0.2649, \|bias\| ≤ 0.02 | 0.2629 | 0.2722 / +0.0012 | **FAIL** |
| 3 | high-confidence ≤ +0.005; sub-400 hi-conf not worse | 0.2287 ; 0.3912 | 0.2405 ; 0.4835 | **FAIL** |
| 4 | no cluster (n ≥ 10) worse by > 0.03 | — | entry-200-300 +0.239, entry-150-200 +0.035 | **FAIL** |
| 5 | top-speed mean \|Δ\| not worse | 28.1 | 25.8 (sub-400: 35.5 → 29.7) | pass |
| 6 | generic-primary flags halve | 117 | 8 | pass |
| 7 | knob changes physical | — | both moved to neutral | pass |

**Decision: NO-GO.** `gear_ratios.py`, `importer.py` and
`scripts/check_gearing_plausibility.py` are back at their pre-epoch content; no
cluster knob changed. The matcher pins in
`tests/test_catalog_fixes_2026_11.py::KNOWN_MISMATCHES` still describe the
known-wrong resolutions and now say why.

A sibling-and-matcher-only variant (no class rule) was also measured: overall
0.2619, but high-confidence sub-400 cc 0.3969 (worse than 0.3912) and
entry-150-200 +0.039 — driven by the 2012 Pulsar NS200 taking 2.100 from its
BS6 sibling's unverified Tier-1 entry (−0.42 → −0.72 s on an instrumented row).
It also fails criteria 3, 4 and 6.

**What the evidence says.** The inferred gearing is physically closer to the
truth — small-bike top speeds improve by 6 km/h on average and several land on
their published figure (Gixxer 250 204 → 154 vs 151; Karizma R 165 → 133 vs 126;
W230 142 → 111 vs 113) — and it makes quarter-mile agreement worse, because the
small-bike ET corpus and the per-cluster launch knobs were fitted on top of the
wrong gearing. Fixing the gearing therefore needs, first:

1. sourced primaries (owner's / service manuals) for the benchmarked small bikes
   rather than a class value — the prototype diff is
   `reports/epoch_2026_11_10_step2_gearing_prototype.diff`;
2. a decision on the two conflicting instrumented test populations in the entry
   classes (they cannot both be matched by one model);
3. a sourced pass over small-bike mass and drag inputs. Several benchmarked
   small bikes look like they store a kerb figure as dry mass, as the duplicates
   did (not verified in this session), and sub-400 cc top speed still overshoots
   by +29.6 km/h with the corrected gearing - inputs the cluster knobs have also
   been absorbing.

## Not done, deliberately

* No Tier-1 primary was changed, marked or replaced (Step 2 reverted in full).
* The redline-inference factor was not touched.
* The Ducati "848 EVO" 2008-2013 / 2011-2013 overlap is two different bikes (the
  first is the plain 848, mis-named); it is a documented exception in the new
  overlap guard, not a merge.
* Tuono 457 wheelbase (sources give 1349-1354, the row says 1370) and the Super
  Meteor / RE 650 gearing were left: no single sourced value.
* Surviving RE 650 rows still top out at ~185 km/h against ~160 published; their
  unsourced Cd·A and gearing are the next thing to source.
* `litre_sport_195p` and everything the references read: untouched.

## Catalog counts (tracked `motoquant.db`)

| table | before | after |
|---|---|---|
| bike_models | 541 | **534** |
| bike_configs (current) | 553 (541) | **544 (534)** |
| parts | 584 | 584 |
| tire_models | 254 | 254 |
| bike_tire_fitments | 1780 | **1765** |
| venues | 20 | 20 |
| `ALL_KNOWN_BIKES` | 538 | **531** |

Full re-seed chain run twice on the tracked DB (second run: every step 0
changes); `PRAGMA integrity_check` ok, `foreign_key_check` empty; DB path equals
spec path on 68 bikes (max |ΔET| = 0).

## New headline accuracy numbers

250 benchmarks / **273 matched** / weighted |Δ| **0.2620 s** / bias **+0.0087 s**;
within ±0.05 s 42, ±0.10 s **74**, ±0.20 s **137**, ±0.50 s 222, ±1.00 s 253;
top-10 cleanest mean |Δ| 0.0064 s over all rows (0.0072 s over non-DERIVED rows —
the ten rows of the best-predictions table are unchanged).

Per-cluster rows (n / weighted |Δ| / weighted bias): litre-sport-600-1000
72 / 0.1755 / −0.0090; sport-twin-600-1300 46 / 0.2413 / +0.0134; other
42 / 0.3238 / +0.0191; litre-sport-195+ 30 / 0.1453 / +0.0283; mid-twin-500-700
16 / 0.1462 / −0.0008; single-300-500 16 / 0.5086 / +0.0298; entry-200-300
14 / 0.2311 / −0.0181; entry-150-200 13 / 0.7015 / −0.0105; two-stroke
9 / 0.6416 / +0.0774; mid-twin-300-500 8 / 0.3614 / −0.0383; cruiser-1300+
5 / 0.2091 / +0.0364; small-i4-screamer 2 / 0.9622 / +0.1335.

Top speed (unchanged tooling): 83 matched, mean |Δ| 27.8 km/h, bias +24.0 km/h.

## Derived artifacts regenerated (REGEN CONTRACT)

| Artifact | How | Result |
|---|---|---|
| `motoquant.db` | full re-seed chain ×2 (reseed → 07-06 ×3 → 07-13 → 08-08 ×2 → 11-09 → 11-10 catalog fixes → `patch_2026_11_10_epoch.py`) | counts above; second run 0 changes everywhere |
| `tests/data/sweep_snapshot.json` | `scripts/generate_regression_snapshot.py` (full) | 3 reference + 35 sample + 534 full; only the adjudicated bikes differ from the previous golden |
| `tests/data/gearing_plausibility_baseline.json` | `scripts/check_gearing_plausibility.py --write-baseline` | 152 → 148 flagged, 538 → 531 bikes |
| `artifacts/surrogate/*` | full regeneration, v2.6 recipe | **v2.7**: holdout MAE 108.8 ms, RMSE 211.4 ms, R² 0.9944, trap MAE 1.69 km/h (n=1,347); 534/534 in-envelope at stock. RMSE is worse than v2.6's 174.9 ms — see the README |
| `web/public/surrogate/{model,bikes}.json` | `make surrogate-web` | 534 bikes, 20 venues; parity tests green |
| `web/app/validation/accuracy_data.json` | `scripts/gen_accuracy_viz_data.py` on the final sweep | 273 matched rows |
| `reports/acc_final_2026_11_10.json` | `scripts/phys_weighted_sweep.py run/report` on the final tree | identical to the Step-1 measurement, bike for bike |

## Still to do outside this lane

* `CLAUDE.md` CURRENT STATE re-seed chain: append `patch_2026_11_09_remove_billing.py`
  → `patch_2026_11_10_catalog_fixes.py` → `patch_2026_11_10_epoch.py` (KNOWN_TRAPS T17).
* `web/data/bike-ids.json` is stale (541 ids vs 534): `python3 web/scripts/gen_bike_ids.py`.
* `scripts/audit_headline_stats.py`: 38 sites still say 541 bikes; the accuracy
  copy (276 matched, 0.263 s, +0.007 s, 75 / 138 within 0.10 / 0.20 s) is quoted in
  `web/app/page.js`, `web/app/validation/{page,layout}.js`,
  `web/app/docs/validation/page.js`, `web/app/whitepaper/page.js`, the
  physics-engine blog post, `README.md`, `docs/ONBOARDING.md`, `docs/MCP.md`,
  `skills/motoquant/SKILL.md`; `docs/ONBOARDING.md` also says 1,780 fitments
  (now 1,765). The OG image is flagged stale.
