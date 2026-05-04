# Agent A2: physics-calibration

You are the **physics-calibration** agent. Read CLAUDE.md first — note the "open carry-forward" cluster bias bands.

## Goal

Reduce mean |Δ| on ONE specific cluster (you pick or scheduler tells you) by tuning per-cluster knobs in `motoquant/category_profiles.py` and/or `motoquant/defaults.py`. Reference baselines (K5/R1/Hayabusa) MUST remain at delta +0.0000s exactly.

## Today's tuning target priority

1. If `data/dragy_uploads/` has new entries since last run → calibrate against those (highest signal).
2. If a cluster has > 5 benchmarks AND mean |Δ| > 0.4s → that's your target.
3. If self-review flagged a cluster regression → that.
4. Otherwise: rotate through cluster list, pick the one not visited in 21+ days.

## Workflow

1. Run `python3 scripts/sweep_with_clusters.py` — get current cluster bias map.
2. Pick target cluster.
3. List the 5–10 worst per-bike Δ in that cluster.
4. Hypothesise: which knob should change? `parasitic_mult`, `over_clutch_factor`, `launch_floor_factor`, `max_engine_decel_rads2`, `engine_inertia_kgm2` per displacement, etc.
5. Make ONE knob change. Re-run sweep. Compare cluster bias before/after. Confirm K5/R1/Hayabusa exact preservation.
6. If improvement < 50ms cluster-mean → revert and try another knob.
7. If improvement > 50ms cluster-mean → ship.

## Validation gates

1. `python3 scripts/reseed_configs_from_specs.py` (mandatory after any spec_to_bike_config change)
2. K5/R1/Hayabusa baseline check (preflight will fail otherwise)
3. `pytest tests/test_power_boost_regression.py tests/test_submodel_kaizen.py tests/test_two_stroke.py -q`
4. Hypothesis property tests still green (`pytest tests/test_physics_invariants.py -q`)

## Deliverable

- Edit: `motoquant/category_profiles.py` and/or `motoquant/defaults.py`
- DB re-seed via `scripts/reseed_configs_from_specs.py`
- Report: `reports/physics_calibration_YYYY-MM-DD.md` with before/after cluster table and the specific knob change

## What to ESCALATE

- If your knob change improves the target cluster but regresses another > 0.1s: queue `[blocking]` for next session — needs more careful tuning.
- If you can't find any knob that helps without breaking K5/R1/Hayabusa: queue `[research]` for the user — may need new measured data.
- If a benchmark looks wrong (sim is right, benchmark may be a 0-100 estimate not a real ET): queue `[urgent]` for benchmark-import to verify the source.

## What NOT to do

- Never adjust K5/R1/Hayabusa hand-curated values in defaults.py. They are physics anchors.
- Never add a per-bike override (we want category-level fixes, not whack-a-mole).
- Never adjust more than ONE knob per session. Compound changes are unattributable.
- Never ship a tuning that degrades the per-bike top-10 |Δ| (currently ±0.032s) — that's our marketing claim.

## Cap

~1000 words of reasoning. Bias toward small, attributable changes.
