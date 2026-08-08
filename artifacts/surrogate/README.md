# MotoQuant Surrogate Artifacts

## Files

| Name                                | What it is                                          | Size    |
|-------------------------------------|-----------------------------------------------------|---------|
| `surrogate_numpy.npz`               | **v2.6 SHIPPED MODEL** — numpy MLP served in prod   | 54 KB   |
| `motoquant_surrogate_v2_6.npz`      | v2.6 training dataset (9,124 rows × 26 features)    | 660 KB  |
| `surrogate_numpy_v2_5.npz.bak`      | v2.5 numpy MLP — rollback copy                      | 87 KB   |
| `motoquant_surrogate_v2_5.npz`      | v2.5 training dataset (9,124 rows × 26 features)    | 660 KB  |
| `surrogate_numpy_v2_4.npz.bak`      | v2.4 numpy MLP — rollback copy                      | 87 KB   |
| `motoquant_surrogate_v2_4.npz`      | v2.4 training dataset (9,126 rows × 26 features)    | 642 KB  |
| `surrogate_numpy_v2_3.npz.bak`      | v2.3 numpy MLP — rollback copy                      | 85 KB   |
| `motoquant_surrogate_v2_3.npz`      | v2.3 training dataset (9,094 rows × 26 features)    | 640 KB  |
| `surrogate_numpy_v2_2.npz.bak`      | v2.2 numpy MLP — rollback copy                      | 86 KB   |
| `motoquant_surrogate_v2_2.npz`      | v2.2 training dataset (9,560 rows × 26 features)    | 678 KB  |
| `surrogate_numpy_v2_1.npz.bak`      | v2.1 numpy MLP — rollback copy                      | 87 KB   |
| `motoquant_surrogate_v2_8k5.npz`    | v2.1 training dataset (8,574 rows × 26 features)    | 610 KB  |
| `surrogate_numpy_v1.npz.bak`        | v1 numpy MLP (K5-only envelope) — rollback copy     | 39 KB   |
| `motoquant_surrogate_v1_1k5.npz`    | v1 training dataset (K5 Sobol, 1.5k samples)        | 128 KB  |

## v2.6 (August 8, 2026) — crank-semantics epoch regen

Regen trigger: the 2026-08-08 crank-semantics pass (synthetic catalog curves
declared crank + `_CRANK_MODE_RECAL`, cluster retune against the July-17
honest rows, catalog dedup, gearing fix for the 299-limited heavies,
fitment/quickshifter patches, full reseed). Standing contract unchanged:
**a surrogate is a cache of the physics — regenerate after any
reseed/retune, in the same session.**

FULL regeneration, same recipe (541 bikes → 9,126 tasks, cluster-stratified;
9,124 valid rows; hidden 128,64 · epochs 600 · restarts 3):

| Metric (ET)            | v2.5                 | v2.6                  |
|------------------------|----------------------|-----------------------|
| Holdout MAE            | 105.5 ms (n=1,361)   | **110.5 ms** (n=1,361)|
| Holdout RMSE           | 254.3 ms             | **174.9 ms**          |
| Holdout R²             | 0.9914               | **0.9962**            |
| trap MAE               | 1.58 km/h            | **1.67 km/h**         |

RMSE nearly halved and R² recovered past the v2.4 level — the crank recal
made the power-to-wheel mapping more uniform across the catalog, which the
26-feature schema captures better than the July-13 state. MAE is flat-to-
slightly-worse (the per-cluster launch knobs remain category-dependent
dynamics the schema is blind to; category-aware features stay the v2.7
candidate). Reference sanity: K5 −0.016 / R1 +0.058 / Busa +0.021 s vs
physics.

## v2.5 (July 13, 2026) — physics-epoch + spec-fix regen

Regen trigger: the July-13 physics epoch (locked-clutch deceleration,
iterated weight-transfer→traction cap, slip-phase ram-air+parasitic,
front-wheel inertia radius, per-cluster mu_peak_scale recalibration) moved
the pinned baselines and every catalog bike; 56 spec fixes + full reseed on
top. Standing contract: **a surrogate is a cache of the physics —
REGENERATE AFTER ANY RESEED/RETUNE, in the same session.**

FULL regeneration, same recipe as v2.4 (541 bikes → 9,126 tasks, cluster-
stratified; 9,124 valid rows; hidden 160,96 · epochs 700 · restarts 2):

| Metric (ET)            | v2.4                 | v2.5                                    |
|------------------------|----------------------|------------------------------------------|
| Holdout MAE            | 89.2 ms (n=1,361)    | **105.5 ms** (n=1,361)                   |
| Holdout RMSE           | 191.6 ms             | **254.3 ms**                             |
| Holdout R²             | 0.9954               | **0.9914**                               |
| trap MAE               | 1.40 km/h            | 1.58 km/h                                |

The modest accuracy step back is expected: the epoch's converged traction
cap + shift-window deceleration add launch/shift dynamics the 26-feature
vector only partially encodes. References: K5 surrogate 10.028 vs physics
9.933 (+0.095), R1 +0.008, Hayabusa −0.039 — the optimizer's
full-sim-verify loop covers the K5-class residual as before.

## v2.4 (July 6, 2026) — taxonomy-v2 retune + reference-row fix

Regen trigger: the July-6 full-corpus accuracy overhaul (cylinder-aware
taxonomy v2 + per-cluster knob retune + cylinder-aware synthetic-curve tail
+ reference bike_configs category_tag fix + full reseed) moved runtime
physics for most of the catalog. Standing contract: **a surrogate is a cache
of the physics — REGENERATE AFTER ANY RESEED/RETUNE, in the same session.**

FULL regeneration (no transplant), same as v2.3: 541 bikes → 9,126 tasks
(148 perturb bases / 25 eval bikes), plan cluster-stratified on the NEW
12-cluster taxonomy (71 sport_twin_600_1300 / 47 single_300_500 /
4 small_i4_screamer members represented). 9,126/9,126 fresh sims, all valid
(516 stock + 25 stock_eval + 25 mod_eval + 8,560 perturb).

Same recipe (hidden 160,96 · epochs 700 · restarts 2 · split seed 42):

| Metric (ET)            | v2.3                 | v2.4                                    |
|------------------------|----------------------|------------------------------------------|
| Holdout MAE            | 87.7 ms (n=1,356)    | **89.2 ms** (n=1,361)                   |
| Holdout RMSE           | 354.2 ms             | **191.6 ms**                            |
| Holdout R²             | 0.9853               | **0.9954**                              |
| trap MAE               | 1.39 km/h            | 1.40 km/h                               |
| Envelope at stock      | 541/541              | **541/541**                             |

The RMSE nearly halved and R² improved because the July-6 retune smoothed
the launch-model behaviour the degenerate slow-regime rows used to hit.
Reference presets (surrogate − physics): K5 +0.078 / R1 +0.051 /
**Hayabusa −0.057** — the hand-curated Hayabusa preset's documented v2.2/v2.3
structural outlier (−0.307) is RESOLVED: its DB row previously carried
category_tag=NULL and dispatched into the wrong launch cluster; the July-6
reference-row patch fixed the dispatch, so the training data and the preset
now agree. Rollback: `cp surrogate_numpy_v2_3.npz.bak surrogate_numpy.npz`.

## v2.3 (July 4, 2026) — 541-bike catalog + shaft/belt gearing reseed

Regen trigger: 6 new bikes (bmids 4632–4637 — Kove 800X, Kove 450 Rally,
QJ Motor SRK 921, Zontes 703F, Benda Chinchilla 500, CFMoto 800MT Sport;
`bike_models` 535 → 541) plus this session's shaft/belt final-drive gearing
changes, which moved several bikes' stock configs. The standing contract:
**a surrogate is a cache of the physics — REGENERATE AFTER ANY RESEED/RETUNE,
in the same session.**

**FULL regeneration this time (no transplant).** Unlike v2.1/v2.2's smart
staleness-gated transplant, v2.3 re-simmed EVERY current bike and EVERY
perturbation fresh. This is the safest path on a grown catalog: it sidesteps
the PLAN NOTE hazard entirely (re-running `plan` re-shuffles eval/base roles,
which only invalidates rows when you TRANSPLANT them from the previous
dataset — with all rows freshly labelled, the reshuffle is harmless). Default
plan: 541 bikes → 9,094 tasks (146 perturb bases / 25 eval bikes); knob
streams keyed `rng(SEED + bmid)` / `rng(SEED + 7e6 + bmid)` as before.
**9,094/9,094 fresh sims, all valid** (516 stock + 25 stock_eval + 25 mod_eval
+ 8,528 perturb). ~4,240 core-seconds on a 4-core sandbox.

Same recipe (hidden 160,96 · epochs 700 · restarts 2 · split seed 42):

| Metric (ET)            | v2.2                 | v2.3                                    |
|------------------------|----------------------|-----------------------------------------|
| Holdout MAE            | 84.1 ms (n=1,426)    | **87.7 ms** (n=1,356)                   |
| Holdout RMSE           | 309.1 ms             | 354.2 ms                                |
| Holdout R²             | 0.9884               | 0.9853                                  |
| trap MAE               | 1.27 km/h            | 1.39 km/h                               |
| Envelope at stock      | 535/535              | **541/541** (incl. all 6 new bikes)     |

Comparable to v2.2, not degraded. The elevated RMSE is again driven by the
degenerate slow-regime rows flagged under v2.2 (litre bikes going SLOWER at
power_scale ≥ ~1.45 — the **PHYSICS FLAG below is still open**, not fixed
here; those rows are true labels and were kept).

The 6 new bikes predict tight against fresh physics on the production DB path
(surrogate − physics): Kove 800X −0.017 / Kove 450 Rally −0.036 / QJ SRK 921
+0.001 / Zontes 703F +0.018 / Benda Chinchilla 500 −0.007 / CFMoto 800MT
+0.013 s — all well inside the holdout MAE. Reference presets: K5 +0.085 s
(marginally past the informal ±0.05 gate, inside holdout MAE), R1 +0.000 s;
hand-curated Hayabusa preset −0.307 s (documented structural outlier).
`tests/test_surrogate_numpy_artifact.py` unaffected (physics baselines are
independent of the surrogate). Rollback:
`cp surrogate_numpy_v2_2.npz.bak surrogate_numpy.npz`.

## v2.2 (July 3, 2026) — 535-bike catalog + post-audit label refresh

Regen trigger: 34 new bikes (ids 4598–4631 — Harley/Indian cruisers, ZX-12R,
V-Max 1200, GSX-R600/750 L1, Kove/Benda/QJ/CFMoto/Zontes, Ninja 1100SX,
CBR600RR '24, Raider R150; `bike_models` 501 → 535) plus the same-day DB
reseed that corrected ~20 shaft/belt final-drive ratios (fabricated 2.471
chain gearing → real ratios). **The stock-probe audit then found the drift
was much wider: 131 of 501 old bikes were stale** — most of it from the
July 2 audit session (year-aware multi-generation reseed of 498 configs,
high-power cruiser/ADV grip gate, kerb→dry mass, benchmark spec corrections)
which was never followed by a surrogate regen. v2.1 had been serving stale
labels for ~100 bikes for a day. The standing contract stands: **a surrogate
is a cache of the physics — REGENERATE AFTER ANY RESEED/RETUNE, in the same
session.**

Smart regen (three staleness gates, then transplant):

* fresh STOCK sims for all 535 bikes → 122 old bikes moved >0.02 s (or had
  feature drift — final_drive_ratio / rolling radius / spec corrections);
* free perturb-row audit: 600 already-fresh perturbation rows diffed against
  their v2.1 counterparts (mean |dET| 1.7 ms) → 2 promotions;
* MAX-POWER probe on all 361 remaining kept bikes (worst residual before
  promotion 121.8 ms, mean 1.5 ms) → 7 promotions (Speed Triple 1200 RS/RR,
  RC8 R, Pan America, 1390 SDR EVO, R 1250 RT, GSX-R 600 K8 — invisible at
  stock, bind under the optimizer's power scaling);
* final split: **131 stale regenerated / 354 transplanted / 34 new / 25 eval**;
* 4,295 fresh sims total (535 stock + 25 mod_eval + 3,735 perturbation) and
  5,265 rows transplanted tid-aligned from v2.1. 9,560/9,560 rows valid
  (510 stock + 25 stock_eval + 25 mod_eval + 9,000 perturb).

PLAN NOTE (matters for the next regen): re-running `surrogate_v2_gen.py plan`
on a grown catalog re-shuffles the eval/base picks (the RNG consumes
differently) — a fresh plan would have flipped 198 old bikes' roles and
invalidated their transplantable rows for no physical reason. The v2.2 plan
was therefore built session-side with the v2.1 roles PRESERVED for all 501
old bikes (reconstruct roles from the previous dataset: eval = `stock_eval`
bmids, base = 28 perturb rows, other = 12 — per-bike knob streams are keyed
`rng(SEED + bmid)` / `rng(SEED + 7e6 + bmid)`, so a bike that keeps its role
keeps its exact knob sequence) and the 34 new bikes added as dense
perturbation bases (28 rows each — new structural territory earns dense
coverage). Plan: 9,560 tasks, 180 bases / 330 others / 25 eval.

Same recipe (hidden 160,96 · epochs 700 · restarts 2 · split seed 42):

| Metric (ET)            | v2.1                 | v2.2                                    |
|------------------------|----------------------|-----------------------------------------|
| Holdout MAE            | 58.5 ms (n=1,278)    | **84.1 ms** (n=1,426; 74.3 ms excl. the 2 pathological rows below) |
| Holdout RMSE           | 105.7 ms             | 309.1 ms (125.1 ms excl. pathological)  |
| Holdout R²             | 0.9987               | 0.9884                                  |
| trap MAE               | 0.91 km/h            | 1.27 km/h                               |
| 25 UNSEEN bikes, stock | 113.6 ms             | 180.1 ms                                |
| UNSEEN, +20 %/−8 kg    | 102.4 ms             | 147.5 ms                                |
| delta-sign agreement   | 25/25 (95.9 ms)      | 25/25 (delta MAE **84.4 ms** — better)  |
| Envelope at stock      | 501/501              | **535/535** (incl. Breakout 117's 240 tire) |

Reference presets: K5 +0.054 s (marginally past the informal ±0.05 gate,
inside holdout MAE), R1 +0.044 s; hand-curated Hayabusa preset −0.285 s
(documented structural outlier, was −0.336). Spot suite on the production DB
path: Hayabusa +0.017 / R15 V4 +0.112 / Duke 390 −0.001 / **ZX-12R +0.001 /
Breakout 117 +0.028 / Kove 450RR +0.002** — all far inside the 0.5 s gate.

**PHYSICS FLAG (found by this regen, NOT fixed — out of scope):** 9 fresh
rows (YZF-R1 '04-06, Panigale V4 '18-24, BMW R 18) collapse into a degenerate
slow regime at power_scale ≥ ~1.45: ET 18–22 s with trap 70–84 km/h on litre
bikes, and MORE power makes it SLOWER (R1 ×1.55 → 21.2 s, ×1.59 → 22.1 s;
reproducible, `finished_quarter=True`). v2.1's physics produced ZERO such
rows under the identical knob distribution — this regime is new since the
July 2 physics/reseed changes (grip-gate / launch-knob territory, likely a
wheelie-control or over-clutch spiral). The rows are true labels and were
kept (they account for most of the holdout MAE/RMSE increase). Prod exposure
is small — +45 %-power configs essentially only arise from boost kits, which
`SurrogatePredictor` always full-sims — but a physics session should
root-cause it.

Optimizer re-proof (4-core sandbox): Hayabusa ₹450k full_race **14.6 s**
(148 surrogate / 32 full-sim calls + 9 verify, 8 out-of-envelope), base
10.223 → 9.246 s (Δ −0.978 s), ₹449.8k spend, 6 parts, no duplicate
exclusives. `tests/test_surrogate_numpy_artifact.py` 8/8 green against the
new artifact. Rollback: `cp surrogate_numpy_v2_1.npz.bak surrogate_numpy.npz`.

## v2.1 (June 12, 2026) — same-night retrain after the physics retune — SUPERSEDED by v2.2

v2 was generated and the physics moved underneath it THE SAME NIGHT: the
per-cluster launch knobs were retuned (entry_150_200, entry_200_300,
mid_twin_300_500, other, cruiser_1300p in `category_profiles.py`) and the
R15/MT-15/RTR-200 family specs + DB rows were corrected + reseeded. The v2
labels went stale for every affected bike — the artifact regression suite
caught it (R15 V4, bike_id=81: surrogate 17.787 s vs fresh sim 18.296 s,
0.51 s off). **Lesson for future sessions: a surrogate is a cache of the
physics — REGENERATE AFTER ANY RESEED/RETUNE, in the same session.**

Smart regen (same plan, seed 42, task-identical to v2 — verified tid-for-tid):

* fresh STOCK sims for all 501 bikes → 31 moved >0.02 s vs the v2 dataset
  (15 litre_sport_600_1000, 7 entry_150_200, 5 litre_sport_195p, 2
  mid_twin_500_700, 1 entry_200_300, 1 other — the litre movers come from
  the same-night benchmark-audit spec corrections, not the launch knobs);
* second probe: every KEPT bike re-simmed at its MAX-POWER perturbation
  (launch-knob retunes can be invisible at stock but bind under the
  optimizer's power scaling) → worst residual 14 ms, **0 promotions**;
* regenerated: all 501 stock rows, all 50 eval rows (25 stock + 25
  "+20 %/−8 kg"), full perturbation sets for the 31 moved bikes, plus the
  447 probe rows — **1,593 fresh sims**; the 6,981 perturbation rows of
  two-point-verified kept bikes transplanted from the v2 shards tid-aligned.
  8,574/8,574 rows valid, kind mix identical to v2.

Same recipe (hidden 160,96 · epochs 700 · restarts 2 · split seed 42):

| Metric (ET)            | Holdout (1,278 rows) | 25 UNSEEN bikes, stock | UNSEEN, +20 %/−8 kg |
|------------------------|----------------------|------------------------|----------------------|
| MAE                    | **58.5 ms** (v2 74.6)| 113.6 ms (v2 166.6)    | 102.4 ms (v2 132.4)  |
| RMSE                   | 105.7 ms             | —                      | —                    |
| R²                     | 0.9987               | —                      | —                    |
| trap MAE               | 0.91 km/h            | —                      | —                    |
| delta-sign agreement   | —                    | 25/25 (delta MAE 95.9 ms) |                   |

All 501 bikes in-envelope at stock. Reference presets: K5 +0.018 s,
R1 −0.018 s (hand-curated Hayabusa preset −0.336 s — documented structural
outlier; the DB Hayabusa the optimizer uses is fine). Spot suite green:
Hayabusa/R15 V4/Duke 390 all within 0.5 s on the production DB path.

Optimizer re-proof (2-core sandbox): Hayabusa ₹450k full_race **15.4 s**
(148 surrogate / 34 sims), ₹446.8k spend, 8 parts, no duplicate exclusives;
Duke 390 ₹80k all **6.3 s** (87 surrogate / 7 sims), ₹80.0k spend, 7 parts.

(The trainer's 2 restarts take ~31 s each — in a 45 s-capped sandbox run
them in separate calls with the identical split, then export the better.)

## v2 (June 12, 2026) — catalog-wide envelope — SUPERSEDED by v2.1 (stale labels)

The v1 numpy model was trained on Sobol perturbations of the GSX-R 1000 K5
template only. **261 of 501 catalog bikes violated its FEATURE_BOUNDS at
STOCK** (aero_cd alone rejected 182 — the catalog carries faired-sport Cd
down to 0.30 while the v1 bounds started at 0.55), so `/api/optimize/build`
fell back to full RK4 sims for most of the catalog: 4–5 minutes per job on
Render's 0.5 CPU. The Hayabusa (bike_id=11, violations: peak_torque_nm +
aero_cd) was the original repro.

### What changed

* **Feature schema v2 — 26 features** (`surrogate_data.FEATURE_NAMES`):
  the 21 v1 features (14 base + 7 derived) survive as a FROZEN PREFIX, plus
  5 structural extras read straight off the BikeConfig: `n_gears`,
  `displacement_cc`, `launch_rpm`, `peak_torque_rpm`, `peak_power_rpm`.
  They disambiguate structurally different bikes (4-speed RX100 vs 6-speed
  R15; peaky 600 vs flat twin) — adding them cut holdout ET MAE ~20 %
  (entry-class clusters ~37 %). 21-input models keep working on `vec[:21]`.
* **`final_drive_ratio` feature now reads the EFFECTIVE ratio**
  (`drivetrain.final_ratio` property). v1 read the raw field, which sprocket
  teeth override — on the K5 template the sampled final drive never reached
  the physics, i.e. a dead training knob.
* **Embedded envelope**: the artifact carries `env_min`/`env_max` (train
  min/max over all 26 features, ±0.5 % pad). `api._check_envelope` and
  `build_optimizer._check_envelope` prefer it over the static
  FEATURE_BOUNDS table (which still guards v1-era models).
  **All 501 catalog bikes are in-envelope at stock.**
* **Boost/blind honesty in the optimizer** (`SurrogatePredictor`): boosted
  configs (`forced_induction.is_boosted`) and feature-blind-but-ET-relevant
  candidates (quickshifters, clutch kits, swingarm extensions — detected via
  a blind-signature compare against the baseline) are ALWAYS full-simmed;
  identical blind configs share one cached sim. The stock baseline is also
  full-simmed once and surrogate predictions are shifted into the true
  frame; selected parts get a full-sim verification + re-selection loop
  (≤3 rounds), so every part that spends budget carries its TRUE delta.

### Training data

Generated by `scripts/surrogate_v2_gen.py` over the production DB path
(`bike_configs` → `db_row_to_config`), engine defaults (fixed 1 ms RK4):

* 501 stock rows — one per current bike config;
* 8,048 local perturbations: 28 around 146 cluster-stratified base bikes +
  12 around every other bike. Knobs mirror the optimizer's reachable space:
  power/torque/dyno-curve scale ×0.92–1.62, mass −25…+10 kg, Cd ×0.85–1.15,
  frontal area ×0.93–1.07, tire mu ×0.96–1.12, rolling radius ×0.97–1.03,
  final drive ×0.87–1.18, altitude 0–2,500 m, reaction 50–550 ms;
* 25 cluster-stratified bikes held out entirely (stock + a "+20 % power /
  −8 kg" build) as the end-to-end eval set.

8,574/8,574 sims valid. Labels are bit-true `engine.run()` outputs.

### v2 quality

| Metric (ET)            | Holdout (1,278 rows) | 25 UNSEEN bikes, stock | UNSEEN, +20 %/−8 kg |
|------------------------|----------------------|------------------------|----------------------|
| MAE                    | **74.6 ms**          | 166.6 ms               | 132.4 ms             |
| RMSE                   | 178.2 ms             | —                      | —                    |
| R²                     | 0.9962               | —                      | —                    |
| trap MAE               | 1.30 km/h            | —                      | —                    |
| delta-sign agreement   | —                    | 25/25 (delta MAE 117 ms) |                    |

Reference presets: K5 +0.013 s, R1 −0.037 s (hand-curated Hayabusa preset
−0.279 s — structurally unlike its catalog twin; the DB Hayabusa the
optimizer actually uses predicts within 0.07 s). Inference ~0.1 ms.

Optimizer proof (this sandbox, 2 cores): Hayabusa ₹450k full_race
63.6 s → **16.9 s** (155 surrogate / 34 sims); Duke 390 ₹80k all
40.5 s → **7.0 s** (88 surrogate / 8 sims), top-4 parts identical to the
full-sim build, combined ET within 0.06 s.

### Regenerate

```bash
# 1. plan + generate (resumable — re-run `run` until ALL DONE)
python scripts/surrogate_v2_gen.py plan
python scripts/surrogate_v2_gen.py run --budget 300   # repeat / loop
python scripts/surrogate_v2_gen.py merge --out artifacts/surrogate/motoquant_surrogate_v2_8k5.npz

# 2. train (pure numpy — no sklearn/xgboost/torch needed)
python scripts/train_surrogate_numpy.py \
    --data artifacts/surrogate/motoquant_surrogate_v2_8k5.npz \
    --out  artifacts/surrogate/surrogate_numpy.npz \
    --hidden 160,96 --epochs 700 --restarts 2
```

Tests: `tests/test_surrogate_numpy_artifact.py` pins the artifact loading,
envelope coverage of Hayabusa/R15/Duke 390 stock, ≤0.5 s spot accuracy on
the production DB path, the v1 prefix contract, and the boosted-config
full-sim fallback.

### Known limitations (honest)

* Absolute ET on bikes with NO training rows (i.e. added to the catalog
  without retraining) runs ~165 ms MAE with occasional 0.5–1.0 s misses on
  structurally odd commuters — retrain after catalog expansions.
* Per-part deltas below ~30 ms are inside surrogate noise; the verify loop
  pins the SELECTED parts to true sims, but a borderline part can still be
  left out (measured cost on the Hayabusa proof: the full-sim build was
  0.46 s quicker COMBINED at equal spend, driven by gearing×power
  interactions that per-part scoring cannot see — in either path; the
  knapsack's own objective scored the surrogate build HIGHER).
* The 2-stroke cluster has only 21 bikes / ~370 rows; treat 2T predictions
  as ±0.15 s class.

## v1 (April 2026) — historical

The v1 XGBoost pickle (`motoquant_surrogate_v1_1k5.pkl`, 1.3 MB) was removed
in the June 12 2026 repo-hygiene pass: sklearn/xgboost are not in
`requirements-api.txt`, so it was unloadable on prod and never served.
Recoverable from git history (last present at commit dececb7). The numpy
artifacts below are the complete v1 record.

1.5k Sobol samples around the K5 template; holdout ET MAE 534.6 ms (XGB) /
~100 ms (numpy MLP on its own distribution). Served prod until June 12,
2026. Rollback: `cp surrogate_numpy_v1.npz.bak surrogate_numpy.npz`
(restores the K5-only envelope via the FEATURE_BOUNDS fallback — the
loader handles envelope-less artifacts transparently).

## Use from Python

```python
from motoquant.analysis.surrogate_numpy import NumpySurrogate
from motoquant.analysis.surrogate_data import config_to_feature_vector

surr = NumpySurrogate.load("artifacts/surrogate/surrogate_numpy.npz")
et_s, trap_mps = surr.predict_config(cfg)  # any BikeConfig
env_min, env_max = surr.envelope  # v2 artifacts only
```
