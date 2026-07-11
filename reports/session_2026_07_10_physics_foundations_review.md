# Physics & Foundations Review — July 10, 2026

Operator directive: *"long reasoning and analysis session to evaluate and
potentially make improvements to the whole repo, especially the physics
engines and other foundational structures."*
Branch: `claude/physics-foundations-review-ex2heb`.

## Method & honest coverage

Two layers:

1. **Inline deep-read** of the full physics core (`physics.py`, `models.py`,
   all 15 `submodels/`, `defaults.py` synthetic-curve machinery,
   `category_profiles.py`, importer `spec_to_bike_config`) plus targeted
   empirical probes (every claim below that says "verified" was reproduced
   by running the engine in this session).
2. **Multi-agent audit workflow** (7 finder dimensions + adversarial
   verifier per finding). The `submodels-physical` finder completed with 7
   quantified findings; the other 6 finders (`physics-numerics`,
   `config-pipeline`, `db-bridge`, `analysis-layer`, `api-jobs`,
   `test-quality`) and all verifier agents were cut off by a subagent
   session limit. **Every applied fix was therefore verified by the main
   session directly** (independent reproduction before and after the
   change), and the inline layer had already covered `physics-numerics`,
   the bridge round-trip, and golden-guard coverage by hand.

**Not audited this session** (be honest, don't infer): `analysis/`
(roi/knapsack/optimizer/autotune/outlaw/sobol internals), `api.py` route
bounds, `jobs.py` races, and llm/. A follow-up pass can resume the workflow
from its cached run (`wf_c22821d6-459`).

Gates at every step: `scripts/check_baselines.py` (Δ = +0.00e+00 ×3, tol
1e-9), golden snapshot fast tier, `make check`, full `make test`.

## Fixes applied (all baseline-bit-identical, all regression-tested)

### 1. Forced induction was dead during the entire clutch-slip phase — HIGH

`physics.py` slip branch rebuilt crank torque from the RAW curve
(`T_e_crank = T_e_curve`), so turbo/supercharger/N2O multipliers
contributed **zero drive force and zero engine spin-up** for the whole
launch-slip window (~3 s / 0–110 km/h on a litre bike). Reproduced: a
steady-1-bar turbo Hayabusa vs the physically-equivalent config with the
same boost ratio baked into its curve — **60 ft +0.294 s, ET +0.367 s**,
matching trap speeds (proving the whole gap was slip-phase). Reached users
through every boosted build on `/api/simulate`, the build optimizer's
boost-part ROI (systematically understated vs post-lock parts like
exhausts), and the flagship outlaw (turbo Hayabusa) pipeline.

**Fix:** multiply the slip-branch (and lock-transition-step) crank torque
by `forced_induction_torque_mult`. For NA configs the multiplier is exactly
1.0 and `x*1.0` is bit-exact in IEEE 754 → K5/R1/Hayabusa unchanged **by
construction** (and verified). Post-fix the turbo twin matches its
baked-curve equivalent within 8 ms (was 367 ms).
**Deliberately NOT folded in:** ram-air and the parasitic subtraction in
the slip branch — both are non-1.0 for NA bikes, so they move the pinned
baselines and belong to a coordinated rebaseline (see epoch-gated list).
**Test:** `tests/test_fi_slip_phase.py` (2 production-path tests: prespooled
turbo must beat NA to the 60-ft; turbo path must match its baked-curve
twin within 50 ms).

### 2. Top-speed "terminal velocity" could be reported at the first gearshift

`run_top_speed()` measured its plateau window in **sample counts**
(`plateau_window_s / sim.dt`), but the adaptive integrator makes samples
non-uniform (0.5–5 ms) and `SimResult.dt` records only the final step
size. A slow gearshift (torque cut → ~zero net accel across ~300
fine-grained samples) satisfied the window: with 160 ms shifts, a
300 km/h K5 reported **"terminal reached at 4.24 s / 84 m"** through
`/api/simulate/topspeed`. Peak-velocity itself (the headline number) was
unaffected.

**Fix:** the plateau is now the first run of below-threshold samples
spanning `plateau_window_s` of **simulated time** on `sim.t`.
Quarter-mile fixed-dt path untouched. Detection is now shift-time
invariant (~34 s on K5 regardless of 100/160/200 ms shifts).
**Test:** `tests/test_topspeed_adaptive.py::TestPlateauDetectionTimeBased`.

### 3. Adaptive runs silently truncated at half the requested time

`n_max` sizes the output arrays from the constructor dt (1 ms), but
adaptive mode halves dt to 0.5 ms during slip/shift. A slip-dominated run
(verified with a never-locking clutch) exhausted the step budget and
stopped at **exactly `max_time/2`** with no warning — indistinguishable
from a legitimate timeout in `/api/simulate/topspeed` / `/distance`.

**Fix:** output arrays grow (double) when the budget is nearly spent,
gated on `use_adaptive_dt` — the fixed-dt path cannot enter the branch, so
baselines and the golden are untouched by construction. Growth is bounded
(dt ≥ 0.5 ms ⇒ ≤ 2× the original sizing).
**Test:** `tests/test_topspeed_adaptive.py::TestAdaptiveStepBudget`.

### 4. Ram-air used ground speed while drag/lift use airspeed

`AeroModel.ram_air_power_mult` computed dynamic pressure from `v`, while
`drag()`/`lift()` correctly use `v + v_wind` — in a headwind the sim
charged the drag penalty but withheld the ram benefit (measured −3.5 ms
ET / +0.43 km/h top speed on a Hayabusa at 10 m/s headwind). Now uses
airspeed. Bit-identical for all zero-wind configs (`v + 0.0 == v`) —
baselines and the windless golden are unmoved (verified).

Also: corrected the stale sync-contract docstring in
`models.py::_two_stroke_torque` (defaults.py now applies calibration tail
factors ×1.10/×1.07 the continuous fallback doesn't; acceptable because
541/541 current bike_configs carry generated dyno curves — verified against
the live DB — so the fallback only serves hand-built test configs).

## Confirmed, quantified — but epoch-gated (fixes move the pinned baselines)

These are real model errors verified this session. Per ADR-0002 and the
roadmap's epoch-gated rule, each needs a deliberate rebaseline + full
weighted sweep, NOT a casual fix. Ranked by expected accuracy value:

1. **`a_net = max(0, ·)` forbids all deceleration** (`physics.py` RK4
   stages). Bikes lose zero speed during gearshifts (0.755 m/s of
   unapplied drag loss on the K5 baseline itself — ~722 N of drag
   suppressed at the last shift) and, in top-speed mode, a bike that
   overshoots into a gear it can't sustain **holds the inflated speed
   forever** (a = 0 also falsely reads as "plateau"). This is a plausible
   mechanism behind the documented +20–40 km/h litre-bike top-speed
   overshoot (April 24 sweep). Fix sketch: clamp only while
   `not clutch_locked` (anti-rollback), let drag decelerate otherwise.
   Baseline movement: certain (all three references shift 5 times mid-run).
   Fixing this would also require re-running `scripts/topspeed_sweep.py`
   and re-syncing published top-speed accuracy stats.
2. **Single-pass weight-transfer → traction cap** uses `N_rear` computed
   from the *unclamped* acceleration estimate. When traction-limited, the
   rear load fed to the cap is overstated (wet-surface K5: +488 N mean /
   +557 N max over the first 2 s ≈ 46 % of static rear load) — the
   wet/salt/venue-grip feature wired July 2 is systematically
   under-penalized. Dry K5 is clipped on 41 % of steps → fix is
   baseline-moving. Fix sketch: 2–3 fixed-point passes of
   (weight transfer ↔ traction clamp).
3. **Slip-phase ram-air + parasitic omission** (the deliberately-unfixed
   remainder of fix #1): during clutch slip NA bikes get no ram-air and pay
   no parasitic drag on the transmitted torque. Small optimistic bias for
   every bike; fold into the same rebaseline as (1)/(2).
4. **Front-wheel rotational inertia divided by the REAR rolling radius**
   (`submodels/drivetrain.py::effective_mass`). Measured −1.2 ms on each
   reference if fixed. `front_rolling_radius_m` exists and the CLI
   front-tire override writes it expecting an effect. Batch with the next
   rebaseline.
5. **Two divergent rider-CoG implementations**:
   `RiderDynamicsModel.cog_shift()` (sine-eased, with CoG-height delta) and
   `wheelbase_weight_split()` have **zero callers** — the live path is the
   simpler linear `RiderParams.cog_offset()` consumed by
   WeightTransfer/Wheelie, with a *fixed* CoG height. Rider CoG-height
   params are populated but never affect physics. Either delete the dead
   pair or wire them (wiring = rebaseline).

## Verified healthy (checked, no action needed)

- **Bridge round-trip fidelity**: `config_to_db_row` → `db_row_to_config`
  preserves every physics-read field (recursive dataclass diff on K5 +
  Hayabusa + a 2T config incl. dyno-curve arrays, tuned_rpm, powervalve,
  reed_valve, category_tag). Environment intentionally comes from the
  venue, not the bike row.
- **Golden guard architecture**: fast tier pins the 3 references at 1e-6
  *plus* a 35-bike stratified sample through the production DB path
  (`db_row_to_config`); slow tier re-sims the full catalog. A bridge field
  drop or missed reseed WOULD be caught. Baseline pin is full-precision
  (10.033404935811529 etc., tol 1e-9).
- **Taxonomy single-source-of-truth** holds: `cluster_for` delegates to
  `derive_category_tag`; the v2 cylinder-aware gates are ordered as
  documented (twins before the 195-hp gate).
- **2T synthetic-curve band constants** are in sync between `models.py`
  and `defaults.py` (all five branches).
- Refuted by the audit (checked and fine): anti-squat multiplier behaviour
  over the catalog range; tire thermal conduction sign + reversion
  continuity; suspected `engage_rpm` data→model mismatch (physics reads
  `clutch.engage_rpm`, parts write `clutch.engage_rpm`;
  `DrivetrainParams.clutch_engage_rpm` is an unread field — tracked
  dead-field deferral); `total_grip_multiplier` non-consumption is the
  documented anti-double-count decision.
- Calibration parsers (`calibration/dyno.py`) guard the rpm→torque
  conversions (`rpm > 50` floor) — no divide-by-zero path.

## Dead-knob inventory (precision for the tracked roadmap item)

`CategoryProfile` knobs with **zero consumers** anywhere in `motoquant/`:
`tuck_transition_time_s`, `cd_ceiling`, `pacejka_C`, `load_sensitivity_k`,
`engine_inertia_mult`, `chain_efficiency_override`. Live knobs:
`over_clutch_factor`, `max_engine_decel_rads2`, `launch_floor_factor`,
`mu_peak_override`, `launch_rpm_factor`, `cd_floor` (physics.py) and
`parasitic_mult` (ParasiticModel). Note the dead ones carry
calibration-looking values (e.g. two_stroke `engine_inertia_mult=0.60`)
that are actually applied elsewhere (importer) — misleading to future
tuners; "wire or delete" remains the right call and `derive`-time knobs
like `cd_ceiling` would be importer-side, not sim-side.

## Deltas table (contract for physics-adjacent PRs)

| Reference | Before | After | Δ |
|---|---|---|---|
| GSX-R 1000 K5 | 10.033404935811529 | 10.033404935811529 | +0.0000 |
| YZF-R1 4C8 | 10.285930649053409 | 10.285930649053409 | +0.0000 |
| Hayabusa Gen1 | 10.471201919790467 | 10.471201919790467 | +0.0000 |

Golden snapshot fast tier: green. `make check`: green. Full `make test`:
green (run pre-fix exit 0, re-run post-fix — see PR).

## Follow-ups queued

- Resume the audit workflow for the 6 uncovered dimensions (cached run id
  `wf_c22821d6-459`; finders for analysis-layer / api-jobs / test-quality
  are the highest-value remaining).
- The epoch-gated list above is now the concrete work order for the next
  deliberate accuracy pass (items 1–4 together, one rebaseline + weighted
  sweep + topspeed sweep + stat sync).
- `SimResult.dt` under adaptive mode still reports the loop-final step
  size; after the plateau fix nothing consumes it as a sampling interval
  (grepped), but storing the constructor dt would be cleaner — cosmetic.
