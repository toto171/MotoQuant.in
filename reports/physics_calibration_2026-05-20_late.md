# Physics Calibration Run — 2026-05-20 (late)

**Outcome:** No changes shipped. Null-delta session with research note.

## TL;DR

Probed two category-level knobs on `mid_twin_300_500` (the cluster with the
largest residual negative bias). Both probes showed the cluster is
**effectively un-tunable** through `CategoryProfile` for the bikes that
dominate its residual error. Reverted both edits, reference baselines and
cluster bias map both unchanged from the pre-session snapshot.

## Reference baselines (preserved exactly)

| Bike     | Target ET | Sim ET    | Δ       |
| -------- | --------- | --------- | ------- |
| K5       | 10.0334s  | 10.0334s  | +0.0000 |
| R1       | 10.2859s  | 10.2859s  | +0.0000 |
| Hayabusa | 10.4712s  | 10.4712s  | +0.0000 |

## Cluster bias map (unchanged before / after)

| Cluster              | N  | mean|Δ| | bias    |
| -------------------- | -- | ------- | ------- |
| litre-sport-195+     | 25 | 0.162s  | -0.036s |
| litre-sport-600-1000 | 29 | 0.206s  | -0.129s |
| cruiser-1300+        |  2 | 0.407s  | +0.407s |
| entry-150-200        |  6 | 1.483s  | +1.142s |
| entry-200-300        |  6 | 0.533s  | +0.214s |
| mid-twin-300-500     | 15 | 0.577s  | -0.225s |
| two-stroke           |  5 | 0.743s  | +0.243s |
| other                |  5 | 0.462s  | +0.394s |

Overall: N=93, mean|Δ|=0.404s, bias=+0.045s, top-10 mean|Δ|=0.0226s.

## Target picked: mid_twin_300_500

Reasoning: bias is -0.225s (sim faster than benchmark — addressable in
principle by adding resistance) and the worst entries cluster on a single
data point — the KTM Duke/RC 390 family running 0.5-0.8s faster than the
Motorcycle Consumer News 14.00s anchor (5 of the 10 worst Δ). entry_150_200
and entry_200_300 are dominated by DERIVED 0-100×1.6 estimates (5/6 and 5/6
benchmarks respectively) — flagged repeatedly in prior carry-forwards as
data-bound, not knob-bound. two_stroke (N=5) splits evenly between sim-fast
(RG500, RS250) and sim-slow (NSR250R, RD350) — no single knob can pull both.

## Probe 1: parasitic_mult 1.0 → 1.15

**Hypothesis.** Add 15 % to parasitic loss to slow the KTM 390 family.

**Result.** Zero ET delta on full 93-benchmark sweep. Root cause: KTM
Duke/RC 390 specs ship `dyno_curve.is_at_wheel=True`, which in
`motoquant/physics.py:477-483` short-circuits the parasitic deduction
(the wheel-dyno value is already post-loss). Verified the multiplier
itself loads correctly (`ParasiticModel._mult=1.15`,
`loss@redline=816 W`) but the deduction site is bypassed. Reverted.

This is a structural finding worth tracking — every bike with a curated
wheel-dyno curve is invisible to `parasitic_mult`, which means the knob
is only effective on synthetic-curve bikes. The cluster's wheel-dyno
share needs to be measured before assigning the knob any meaningful
tuning budget.

## Probe 2: tuck_transition_time_s 2.0 → 2.8 → 3.5

**Hypothesis.** Slow the rider-to-tuck transition so the bike spends more
high-speed time in the +18 % drag upright posture, slowing trap.

**Result.** Max +0.04 s on KTM 390 (13.42 → 13.46 at tuck=3.5); zero
delta on Apache RR 310, MT-03, Benelli 302R (those bikes spend the
relevant high-speed window beyond the transition window regardless).
A 40 ms gain on 4 of the 15 cluster entries delivers maybe 10 ms
cluster-mean — well under the 50 ms gate. Not shipped.

## Probe 3: over_clutch_factor 0.30 → 0.50, 0.20, 0.10

**Hypothesis.** Reduce slip-phase over-clutching so launches are less
aggressive, raising ET.

**Result.** Zero delta on every cluster bike tested across {0.10, 0.15,
0.20, 0.30, 0.50}. The launch slip phase resolves in <100 ms for these
wheel-dyno bikes — the engine torque ramps fast enough that clutch
locks up before `prof.over_clutch_factor` matters. Effectively dead knob
for this cluster. Reverted.

## Audit of unwired knobs

While probing, noticed several `CategoryProfile` fields are declared but
never read by any sub-model: `cd_ceiling`, `cd_floor`, `pacejka_C`,
`engine_inertia_mult`, `chain_efficiency_override`, `launch_rpm_factor`,
`mu_peak_override`, `load_sensitivity_k`. Only `parasitic_mult`,
`tuck_transition_time_s`, `over_clutch_factor`, `max_engine_decel_rads2`,
and `launch_floor_factor` are actually consumed (grep for each token
across `motoquant/submodels/` + `motoquant/physics.py`). The five wired
knobs all gate behind launch-phase conditions (slip_speed > 0, or sub-1 s
rider-transition window) so for any bike that locks the clutch quickly
and finishes the run beyond the transition, the entire category-profile
toolkit is inert.

This is worth flagging because the system *looks* tuneable (eight knobs
named in `CategoryProfile`) but only two of them (`parasitic_mult` and
`tuck_transition_time_s`) actually affect cruise-phase physics, and
`parasitic_mult` is bypassed on wheel-dyno bikes. Real cruise-phase
levers (aero clamp, drivetrain efficiency, mu_peak) are declared but
not wired.

## Recommendation for next session

1. **Wire `chain_efficiency_override`** in `motoquant/submodels/drivetrain.py`
   so the field stops being dead config — this is the simplest unbroken
   lever on cruise-phase efficiency and would give every cluster a real
   knob. Then re-probe mid_twin_300_500 with `chain_efficiency_override`
   stepped from 0.95 → 0.93.
2. **Wire `cd_ceiling` / `cd_floor`** as a hard clamp in `aero.py` so
   catalog Cd outliers (Duke 390 at 0.81 vs cluster median ~0.60) can be
   pinned without per-bike edits.
3. Or: queue `[research]` for the user to ask a Pune/Narhe drag-tuning
   contact for instrumented stock-bike KTM 390 timeslips that could
   replace the MCN 14.00 s anchor (it may be a magazine ET on a hot day
   with an experienced rider; a 13.4 s stock 390 with full tuck is not
   physically implausible).

## Validation gates

- `python3 scripts/sweep_with_clusters.py` — references at Δ +0.0000 each.
- `pytest tests/test_power_boost_regression.py tests/test_submodel_kaizen.py
   tests/test_two_stroke.py tests/test_physics_invariants.py -q` — 51 / 51
   passed.

## Files touched

None (both probes reverted in place). Only this report added at
`reports/physics_calibration_2026-05-20_late.md`.
