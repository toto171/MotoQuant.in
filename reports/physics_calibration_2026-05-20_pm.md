# Physics Calibration — 2026-05-20 (PM session)

**Status:** RESEARCH NOTE (no code change shipped, all per-cluster tunings reverted).

**Agent:** physics-calibration

**Note:** A prior session on 2026-05-20 already shipped the two-stroke `max_engine_decel_rads2` 380→800 calibration (see `reports/physics_calibration_2026-05-20.md`). This PM session ran independently and targeted the remaining non-two-stroke clusters.

## TL;DR

Investigated four candidate clusters (mid-twin-300-500, two-stroke, cruiser-1300+, entry-200-300) for >=50ms mean|Δ| improvement via single-knob category-level tuning. **No knob change cleared the 50ms gate** because every cluster with N>5 benchmarks shows a bimodal Δ distribution that no single-direction category knob can correct. Reverted to baseline. Reference baselines K5/R1/Hayabusa preserved exactly to 4 decimals.

## Current cluster bias map (sweep at HEAD)

| Cluster                | Bikes | N  | mean\|Δ\| | bias    |
|------------------------|-------|----|-----------|---------|
| cruiser-1300+          |   8   |  2 | 0.407s    | +0.407s |
| entry-150-200          |  34   |  6 | 1.483s    | +1.142s |
| entry-200-300          |  38   |  6 | 0.533s    | +0.214s |
| litre-sport-195+       |  36   | 25 | 0.162s    | -0.036s |
| litre-sport-600-1000   | 119   | 29 | 0.206s    | -0.129s |
| mid-twin-300-500       |  67   | 15 | 0.577s    | -0.225s |
| mid-twin-500-700       |  18   |  0 | (no benchmarks) |  |
| other                  |  87   |  5 | 0.462s    | +0.394s |
| two-stroke             |  21   |  5 | 0.743s    | +0.243s |

References: K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s (Δ +0.0000 each).
Overall: N=93, mean|Δ|=0.404s, bias=+0.045s. Top-10 |Δ|=±0.0226s.

## Attempt 1: mid-twin-300-500 — over_clutch_factor 0.30 → 0.20

**Hypothesis.** Cluster runs sim-fast (-0.225s bias). KTM 390 family (5 entries) all cluster at sim ~13.2-13.4s vs bench 14.0s (-0.55 to -0.83). Reducing over-clutching should slow them by ~0.3s by extracting less engine-inertia energy at launch, aligning with mid_twin_500_700's 0.20.

**Result.** Zero effect on sweep results, identical to 4 decimals.

- KTM Duke 390 sim=13.4233s (unchanged), RC 390 sim=13.0157s (unchanged), 390 Duke Gen 3 sim=13.2330s (unchanged).
- Cluster mean|Δ| = 0.577s before, **0.577s after** — no improvement.

**Diagnosis.** The over-clutch formula is `over_clutch_extra = min(headroom * factor, max_back_torque)` where `headroom = max(0, T_clutch_max - abs(T_e_crank))`. For the mid-twin-300-500 bikes the **clutch saturates at launch** (T_clutch_max <= T_e_crank), so `headroom = 0` and the factor knob has no purchase. The over-clutch tunable is dead for this cluster — same symptom class as the entry_200_300 inbox note flagging "11 of 12 knobs had zero effect". Reverted.

## Why no other cluster qualified

Every candidate cluster with N>5 AND mean|Δ| > 0.4s shows a **bimodal Δ distribution** that single-direction knob tuning cannot fix:

### mid-twin-300-500 (N=15) — bimodal

- "Sim-too-fast" tail (5 KTM 390 variants Δ -0.55 to -0.83, Apache RR 310 -0.98, Benelli 302R -0.93). Needs slow-down.
- "Sim-too-slow" tail (CB350RS +1.50 outlier, Pulsar NS400Z +0.47, MT-03 +0.43, Ninja 400 +0.25). Needs speed-up.
- Any knob that slows the cluster (parasitic up, chain_eff down, mass up via inertia up) will worsen the +bias tail by the same magnitude — net mean|Δ| improvement near zero.

### two-stroke (N=5) — bimodal

- "Sim-too-slow" small-cc 2T (NSR250R +1.41, RD350 +1.06). Needs speed-up.
- "Sim-too-fast" big-cc 2T (RG500 Gamma -0.73, RS250 -0.47). Needs slow-down.
- The 2026-05-20 max_engine_decel_rads2 380→800 bump just closed half of this; residual is per-bike. A single-knob category fix is structurally unable to resolve.

### entry-200-300 (N=6) — quality-bound

- 3 of 6 benchmarks are DERIVED (0-100 × 1.6 with ±0.7s declared uncertainty): Pulsar N250 +1.02, FZ25 +0.93, Gixxer SF 250 -0.69 — benchmark uncertainty exceeds per-bike Δ. The 3 instrumented benchmarks (KTM Duke 250 -0.12, Ninja 300 +0.29, Gixxer 250 -0.15) average ~0.18s mean|Δ| — already at the limit. Inbox note also flags this cluster as model-bound dead because most bikes use synthetic dyno curves with `is_at_wheel=True`.

### entry-150-200 (N=6) — known data quality

- 4 of 6 benchmarks DERIVED. Apache RTR 200 4V +3.40 and MT-15 V2 +3.35 dominate; both DERIVED. R15 V3/V4 split (Δ -0.62 / +0.88) suggests stock vs modded benchmark confusion that no category knob will fix.

### cruiser-1300+ (N=2) — too few benchmarks

- VMAX 1700 +0.48, Rocket 3 R +0.34. Both biased positive with similar magnitude; parasitic_mult 0.65→0.50 or engine_inertia_mult 1.0→0.85 could plausibly close ~0.3s. **But N=2 is below the contract's N>5 threshold.** Deferred — needs more measured benchmarks (Triumph Rocket 3 GT, Indian Roadmaster, HD CVO Road Glide).

### other (N=5) — heterogeneous

- Ninja H2 SX SE+ +1.23, Hayabusa 2021 +0.55, Sportster S +0.19, ZZR1400 +0.17, 1290 Super Duke R -0.17. Mixed sport-touring/muscle/naked, no single knob can help symmetrically.

## What would actually move the needle

Per the contract's "What to ESCALATE" guidance, these are the items the next session(s) should pick up:

1. **[research] mid-twin-300-500 needs per-platform sub-tuning, not category-level.** The KTM 390 family (-0.6 to -0.8s) is consistently sim-fast across 5 entries — strong signal of a platform issue (gearing? mass? mu_peak? launch dyno curve injection?). Investigate the 5 KTM 390 specs in `known_bikes.py` / `known_bikes_extended.py` and the WP-43 fork mass distribution; this may be a chassis.fluid_mass_kg or chassis.dry_mass_kg drift pre-dating the April-24-PM bike_configs reseed. Run a `scripts/diagnose_r15_db_path.py`-equivalent on KTM 390 Duke to compare DB vs spec.

2. **[urgent] benchmark-import agent — flag DERIVED entries.** 3 of 6 entry_200_300 and 4 of 6 entry_150_200 benchmarks are DERIVED with ±0.7s declared uncertainty. The weighted-source policy (CLAUDE.md Apr 30 PM: instrumented=1.0 / DERIVED=0.1) exists but isn't applied per-cluster. Wiring weighted aggregation into `_summarize` in `sweep_with_clusters.py` would drop entry_200_300 mean|Δ| from 0.533 reported → ~0.27 real, and entry_150_200 from 1.483 → ~0.71 real — without changing any physics.

3. **[research] cruiser-1300+ wants attention but needs N>=5.** Source 3 more cruiser/muscle instrumented timeslips (Indian Roadmaster, HD CVO Limited, Triumph Rocket 3 GT) then a single `parasitic_mult` or `engine_inertia_mult` reduction is likely to close ~0.3s cluster-mean. Currently blocked on benchmark count.

4. **[blocking] over-clutch saturation diagnostic.** The "headroom = 0 when clutch saturates" path makes the `over_clutch_factor` and `max_engine_decel_rads2` knobs no-ops for any bike whose T_clutch_max < T_e_crank at launch. Add a one-line `print(headroom, T_clutch_max, T_e_crank, T_transmitted)` debug to `physics.py` and run on KTM 390 Duke to confirm. If confirmed, the fix is structural: either the clutch model needs a higher T_clutch_max for these bikes (slipper-clutch upgrade in spec), or the over-clutch dispatcher needs a "if headroom == 0, draw from engine-inertia anyway" path. Higher-stakes change than single-knob tune; scope separately.

## Files touched

None — all attempted edits reverted.

## Commit summary

```
research(physics): no shippable single-knob fix this cycle — mid-twin-300-500 clutch-saturated, other clusters bimodal or N<5
```

## Validation checks

- `python3 -c "from motoquant.category_profiles import get_profile, CATEGORY_MID_TWIN_300_500; print(get_profile(CATEGORY_MID_TWIN_300_500).over_clutch_factor)"` → 0.3 (baseline)
- K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s — exact to 4 decimals after revert.
- No DB reseed performed (no spec_to_bike_config change).
- Top-10 mean|Δ| unchanged at ±0.0226s.
