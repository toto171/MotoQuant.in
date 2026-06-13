# Physics sub-model audit & accuracy pass — 2026-06-13

Continuation of the interrupted "Motoquant project overhaul" session. Goal:
audit the physics sub-models, close per-class delta where genuinely possible,
preserve the K5/R1/Hayabusa reference baselines exactly.

## Method
New tool `scripts/phys_weighted_sweep.py` — resumable, chunked (sandbox 45 s
cap) sweep of all 502 catalog bikes, matched to `BENCHMARKS` with the same
score-and-pick logic as `sweep_with_clusters`, then scored with **source
weighting** so unreliable benchmarks stop dominating the metric:

| source tier | weight |
|---|---|
| instrumented (Dragy / timing-strip / MCN / Consumer News) | 1.0 |
| magazine (Cycle World / Sport Rider) | 0.7 |
| aggregator (FastestLaps / MotoStatz / Bikewale) | 0.5 |
| forum / timeslip | 0.3 |
| DERIVED (0-100 × multiplier estimates) | 0.1 |

## Current-main baseline (HEAD 04e0ef5, 236 matched benchmarks)
**Overall weighted mean|Δ| = 0.263 s, weighted bias = −0.014 s** (essentially
zero-centred). Reference baselines exact: K5 10.0334 / R1 10.2859 / Hayabusa
10.4712 (Δ +0.0000 ×3).

| cluster | n | w_mean|Δ| | w_bias | raw_mean|Δ| |
|---|---|---|---|---|
| litre-sport-195+ | 31 | 0.137 | −0.015 | 0.138 |
| mid-twin-500-700 | 12 | 0.141 | +0.059 | 0.144 |
| litre-sport-600-1000 | 99 | 0.201 | −0.072 | 0.204 |
| entry-200-300 | 15 | 0.343 | +0.071 | 0.580 |
| cruiser-1300+ | 3 | 0.355 | +0.355 | 0.355 |
| other | 35 | 0.383 | +0.124 | 0.389 |
| mid-twin-300-500 | 23 | 0.516 | −0.086 | **1.052** |
| two-stroke | 6 | 0.584 | +0.153 | 0.589 |
| entry-150-200 | 12 | 0.820 | +0.018 | **1.642** |

## Key finding: the residual is data-quality-limited, not model-limited
The two worst clusters by raw error collapse when restricted to
**high-confidence (weight ≥ 0.5)** benchmarks:

* entry-150-200: raw 1.642 → weighted **0.383** (bias +0.031)
* mid-twin-300-500: raw 1.052 → weighted **0.381** (bias +0.012)

i.e. the big numbers come from low-confidence DERIVED/forum rows (0-100 ×
multiplier estimates, ±0.7 s declared uncertainty), not from systematic model
error. The high-confidence subsets are near-centred. This matches the
conclusion reached repeatedly in prior sessions: *the simulator is centred at
zero bias and structurally correct; further gains are bottlenecked by
benchmark data quality, not model fidelity.*

## Genuine model errors (high-confidence misses, |Δ| ≥ 0.4, weight ≥ 0.7)
26 rows. Two real, actionable patterns (the rest are tails around already-good
cluster means):

1. **Heavy ADV/tourer V4s sim slow** (the "other" +0.124 bias): Ducati Diavel
   V4 +0.80, Multistrada V4 +0.64 / RS +0.53, Kawasaki H2 SX SE+ +0.71, Suzuki
   GSF1250 +0.68, Honda CB1100 +0.49 — while sporty V-twins sim fast (Buell
   1125R −0.50, Monster 1200 −0.44). The cluster is **heterogeneous**; the
   06-11 grid-search already found oc 0.30/decel 800 is the sweet spot and that
   pushing harder degrades the fast sporty side. Not chased further (would
   over-fit one half at the other's expense).
2. **Kawasaki ZX-4RR +1.14** (399 cc I4 screamer): slow ET + high trap
   (192 vs ~175 km/h) ⇒ geared ~12 % too tall (1st gear tops 84 km/h @ redline
   vs real ~70–76). Root cause is a per-bike **gearing data gap**
   (primary_ratio 2.045), NOT the launch model — verified by swapping its
   launch profile (ET moved only 13.143→13.168). Needs verified service-manual
   gearing to fix correctly; flagged for a data pass, not guessed at here.

## Change shipped this pass
**cruiser-1300+ over-clutch bump** (`category_profiles.py`): oc 0.30 → 0.45,
decel 800 → 900. The cluster's 3 benchmarks (VMAX 1700, Rocket 3 R, Rocket 3
Storm R) sim uniformly slow (same-direction bias +0.355) — heavy muscle bikes
slip-launch harder than the shared "other" default models. Result: cluster
w_mean|Δ| 0.355 → **0.312**, bias +0.355 → +0.312, still conservative (no
over-shoot). Same-direction N=3 ⇒ low regression risk. Profiles are looked up
at runtime from `category_tag` (physics.py:220 `get_profile`), so no DB reseed
is required and the live `/api/simulate` path picks the values up directly.

Reference baselines re-verified exact after the change (Δ +0.0000 ×3).
Focused suite green: test_category_dispatch + test_power_boost_regression +
test_validation + test_submodel_kaizen + test_two_stroke + test_scraper.

## Deliberately NOT done (over-fitting guard)
* No aggressive cluster-knob tuning to chase thin/noisy benchmarks — prior
  sessions already grid-searched these (documented 05-20 / 05-30 / 05-31 /
  06-11) and the launch knobs are near their useful leverage ceiling (cruiser
  ET moves only ~0.05 s even at oc 0.75).
* Did **not** apply the interrupted session's stale-base physics commits
  (single-cyl falloff + an older over-clutch set built on ac0f7ad): current
  main is already tuned past them, and the single-cyl falloff would *worsen*
  the now-centred entry clusters.

## Honest path to closing the gap further
More **high-confidence** (instrumented / magazine) benchmarks for the thin
clusters (cruiser N=3, two-stroke N=6) and verified service-manual gearing for
the high-rev small multis (ZX-4RR / ZX-25R). Model tuning is at its ceiling;
data is the lever.
