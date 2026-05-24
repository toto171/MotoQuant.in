# Physics Calibration Report — 2026-05-24

## Session summary

**Outcome:** No changes shipped — null-improvement session with structural research finding.
**All 4 available knobs** were probed exhaustively across the two highest-error clusters
(`two_stroke` mean|Δ|=0.743s, `mid_twin_300_500` mean|Δ|=0.600s).
No knob change exceeded the 50 ms improvement gate. Reference baselines unchanged.

---

## Reference baselines (verified unchanged throughout)

| Bike     | Target ET | Sim ET   | Δ       |
| -------- | --------- | -------- | ------- |
| K5       | 10.0334s  | 10.0334s | +0.0000 |
| R1       | 10.2859s  | 10.2859s | +0.0000 |
| Hayabusa | 10.4712s  | 10.4712s | +0.0000 |

---

## Cluster bias map (unchanged before / after)

| Cluster              | N  | mean\|Δ\| | bias     |
| -------------------- | -- | --------- | -------- |
| litre-sport-195+     | 27 | 0.155s    | -0.038s  |
| litre-sport-600-1000 | 30 | 0.200s    | -0.123s  |
| cruiser-1300+        |  2 | 0.407s    | +0.407s  |
| entry-150-200        |  8 | 1.387s    | +0.895s  |
| entry-200-300        |  6 | 0.533s    | +0.214s  |
| mid-twin-300-500     | 16 | 0.600s    | -0.270s  |
| mid-twin-500-700     |  0 | —         | —        |
| two-stroke           |  5 | 0.743s    | +0.243s  |
| other                |  5 | 0.462s    | +0.394s  |

Overall: N=99, mean|Δ|=0.413s, bias=+0.034s, top-10 mean|Δ|=0.0186s.

---

## Target 1: two_stroke (N=5, mean|Δ|=0.743s)

### Per-bike state

| Bike            | Bench | Sim    | Delta   | Source                          |
| --------------- | ----- | ------ | ------- | ------------------------------- |
| Yamaha RD350    | 14.00 | 15.055 | +1.055  | Cycle World 1973 (instrumented) |
| Yamaha RD400F   | 14.18 | 14.134 | -0.046  | Cycle World 1979 (instrumented) |
| Suzuki RG500    | 11.60 | 10.867 | -0.733  | Cycle World 1985                |
| Honda NSR250R   | 13.40 | 14.810 | +1.410  | MotorBikeCatalog (estimated)    |
| Aprilia RS250   | 13.40 | 12.929 | -0.471  | MotorBikeCatalog (estimated)    |

**Pattern:** Bimodal — RD350/NSR250R sim-slow, RG500/RS250 sim-fast.
Any single knob accelerating the slow pair also accelerates the fast pair.

### Knob probes

| Knob                    | Range tested      | Best mean\|Δ\| | Change vs baseline (0.743) |
| ----------------------- | ----------------- | -------------- | -------------------------- |
| `over_clutch_factor`    | 0.40–0.80         | 0.7429         | 0.0000 (zero effect)       |
| `max_engine_decel_rads2`| 800–3000          | 0.726 @ 3000   | -0.017s (< 50ms gate)      |
| `launch_floor_factor`   | 0.80–1.10         | 0.743 @ 1.00   | 0.0000 (already at optimum)|

### Root cause: dead-knob discovery

All 2T benchmark bikes (RD350, RG500, NSR250R, RS250, RD400) carry
`dyno_curve.is_at_wheel=True`. The physics loop at `motoquant/physics.py:477-479`
gates parasitic deduction on `dyno_curve is None or not is_at_wheel`, so:

- `parasitic_mult` is bypassed entirely for all 5 benchmarked 2T bikes.
- `over_clutch_factor` controls `over_clutch_extra = min(headroom * ocf, max_back_torque)`
  where `max_back_torque = max_engine_decel_rads2 * I_e_local`. With tiny 2T engine
  inertia (~0.006-0.012 kg·m²), even at 800 rad/s² the max extra is only 6-10 Nm on
  a 36-45 Nm engine — the knob is already making its full physical contribution.
- The **only effective knob** is `max_engine_decel_rads2`, which was raised 380→800 on
  2026-05-20. Further raises hit diminishing returns because RG500 and RS250 (already
  sim-fast) drag the mean back as RD350 and NSR250R improve.

### Maximum achievable improvement at cluster level

At max_decel=3000 (physically speculative for 2T cranktrains):
- RD350: +1.055 → +0.207
- NSR250R: +1.410 → +1.086
- RG500: -0.733 → -1.121 (worsens)
- RS250: -0.471 → -0.783 (worsens)
- mean|Δ|: 0.743 → 0.726 (-17ms, under 50ms gate)

**Not shipped.** Any value above 800 rad/s² makes the already-fast
RG500/RS250 predictions worse by more than the improvement on RD350/NSR250R.

---

## Target 2: mid_twin_300_500 (N=16, mean|Δ|=0.600s)

### Knob probes (building on 2026-05-20 late session findings)

| Knob                     | Range tested       | Best mean\|Δ\| | Change |
| ------------------------ | ------------------ | -------------- | ------ |
| `over_clutch_factor`     | 0.00–0.30          | 0.578 @ 0.00   | -0.000 (< 1ms) |
| `chain_efficiency_override` | 0.85–0.97       | unchanged      | 0.000  |
| `max_engine_decel_rads2` | 0–300              | 0.576 @ 150    | -1.8ms |

All three yield < 2ms improvement. Root cause confirmed from 2026-05-20
session: KTM 390 / RC 390 family (5 of 16 benchmarks, dominant outlier at
-0.5 to -0.95s) has `dyno_curve.is_at_wheel=True`, bypassing both
`parasitic_mult` and making `over_clutch_factor` effectively inert (zero headroom
between `T_e_crank` and `T_clutch_max` at the operating point). The
`chain_efficiency_override` field is defined in `CategoryProfile` but is
not read by any physics or submodel code (dead field).

### Benchmark quality note

CB350RS (+1.497s, `DERIVED 0-100 × 1.6`) and Pulsar NS400Z (+0.469s, `DERIVED`)
are estimated benchmarks with ±0.7s declared uncertainty — their contribution
to cluster mean|Δ| is noise-dominated, not model-bounded.

---

## Structural finding (key research output)

### Live profile knobs: only 4 of 11 defined knobs are wired

| Knob                        | Wired?  | Location                           |
| --------------------------- | ------- | ---------------------------------- |
| `over_clutch_factor`        | YES     | `physics.py:544`                   |
| `max_engine_decel_rads2`    | YES     | `physics.py:545`                   |
| `launch_floor_factor`       | YES     | `physics.py:564-571`               |
| `parasitic_mult`            | YES*    | `submodels/parasitic.py:31` (*bypassed for wheel-dyno bikes) |
| `chain_efficiency_override` | **NO**  | defined in profile, never read     |
| `tuck_transition_time_s`    | **NO**  | profile value defined, but `rider_dynamics.py` reads from `cfg.rider.tuck_transition_time_s` directly |
| `mu_peak_override`          | **NO**  | defined in profile, `tire.py` reads from `cfg.tires` directly |
| `pacejka_C`                 | **NO**  | defined in profile, `tire.py` reads from `cfg.tires.pacejka_C` directly |
| `load_sensitivity_k`        | **NO**  | defined in profile, `tire.py` reads from `cfg.tires.load_sensitivity_k` directly |
| `engine_inertia_mult`       | **NO**  | defined in profile, `importer.py` doesn't read it |
| `launch_rpm_factor`         | **NO**  | defined in profile, never read     |
| `cd_ceiling` / `cd_floor`   | **NO**  | defined in profile, never applied  |

The 4 wired knobs are already at their optimum for `two_stroke` and are
effectively neutralised for `mid_twin_300_500` by the wheel-dyno bypass.

### `other` cluster note: benchmark attribution error

`Kawasaki Ninja H2 SX SE+` (2024, 248 kg, `cat=touring`) is matching to the
`("Kawasaki", "Ninja H2", 2015, 9.62s)` benchmark via word-boundary matching
("Ninja H2" tokens appear in "Ninja H2 SX SE+"). The benchmark is for the
original **Ninja H2** naked (2015, ~232 kg) — a 16 kg lighter, shorter,
drag-oriented machine. The 1.233s gap is almost entirely explained by the
weight and gearing difference. This is not a physics model error.

---

## Escalation queue

### [research] Wire additional category profile knobs into physics sub-models

The 7 unwired knobs in `CategoryProfile` represent significant untapped
calibration budget. Highest-ROI wires:

1. **`chain_efficiency_override` → `ChainModel`**: Routing losses in
   small-cc bikes (428/520 thin chains) differ meaningfully from litre
   sportbikes (530 chain). Currently `ChainModel` reads from `cfg.drivetrain`
   only; adding a profile override would allow category-level detuning.

2. **`mu_peak_override` → `TireModel`**: The 2T vintage bias (RD350, NSR250R)
   may partly reflect overestimated grip from modern synthetic rubber
   modelling applied to 1970s bias-ply tires. A `mu_peak_override=1.10`
   for `two_stroke` (vs the current 1.20-1.40 sport defaults) would slow
   these bikes at launch without affecting over-clutching.

3. **`tuck_transition_time_s` → `RiderDynamicsModel`**: Already wired in
   `rider_dynamics.py` from `cfg.rider.tuck_transition_time_s`; needs
   `_precompute` to copy `prof.tuck_transition_time_s` into `cfg.rider`.

### [urgent] Benchmark review: Kawasaki Ninja H2 SX SE+

Benchmark `("Kawasaki", "Ninja H2", 2015, 9.62s, MCN 2015)` is matching
to the 2024 H2 SX SE+ touring variant (248 kg). Should be reassigned to the
correct "Ninja H2" naked spec. This removes the +1.233s outlier from `other`
and would reduce cluster mean|Δ| from 0.462s to ~0.269s. Action: add a more
specific benchmark key for the original H2 or add the H2 naked to the catalog.

### [research] Wheel-dyno bypass patch for category-level calibration

All KTM 390 / RC 390 / RD350 / RG500 / NSR250R bikes have
`dyno_curve.is_at_wheel=True`, which skips parasitic deduction. The physics
rationale is correct (wheel-dyno curves already include drivetrain losses).
However, this also nullifies `parasitic_mult` as a calibration lever for
these bikes. A targeted fix: instead of bypassing parasitic entirely, apply a
reduced multiplier `(1.0 - cfg.engine.dyno_curve.drivetrain_loss_fraction)`
so the category knob retains marginal effect for fine-tuning without
double-subtracting losses.

---

## Session outcome

No knob changes shipped. Cluster bias map and reference baselines unchanged from
session start. This report serves as a Kaizen research artifact documenting the
structural limits of the current 4-knob calibration system.

Next recommended action: implement `mu_peak_override` wiring in `TireModel`
(~15-line change in `submodels/tire.py`), which would unlock a new calibration
lever for the `two_stroke` and `entry_150_200` vintage-bias-ply bikes.
