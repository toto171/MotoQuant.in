# Physics Calibration — 2026-05-26

**Agent:** physics-calibration
**Session:** 1779762631-622
**Outcome:** NULL SESSION — no knob changes shipped. All 4 wired knobs produce zero effect on the only cluster meeting priority-1 criteria.

---

## Cluster bias map (session start, no changes shipped)

| Cluster              | bikes | N  | mean\|Δ\| | bias    |
| -------------------- | ----- | -- | --------- | ------- |
| litre-sport-195+     |  39   | 28 | 0.138s    | -0.012s |
| litre-sport-600-1000 | 134   | 63 | 0.209s    | -0.076s |
| mid-twin-500-700     |  22   |  8 | 0.214s    | +0.211s |
| mid-twin-300-500     |  73   | 16 | 0.507s    | -0.137s |
| entry-200-300        |  44   |  6 | 0.533s    | +0.214s |
| entry-150-200        |  40   |  8 | 1.387s    | +0.895s |
| two-stroke           |  21   |  5 | 0.683s    | +0.338s |
| cruiser-1300+        |  10   |  2 | 0.407s    | +0.407s |
| other                | 107   |  9 | 0.310s    | +0.247s |

Overall: N=145, mean|Δ|=0.332s, bias=+0.052s, top-10 mean|Δ|=0.0114s.

---

## Target Selection — Rationale

Priority-1 criterion: N>5 AND mean|Δ|>0.4s. Candidates this session:

1. **`entry-150-200`** — N=8, mean|Δ|=1.387s. QUALIFIES on metric, but **6/8 benchmarks are DERIVED** (0-100 × 1.6 multiplier, ±0.7s declared uncertainty). Only 2 are instrumented (MotoStatz R15 V3/V4).
2. **`mid-twin-300-500`** — N=16, mean|Δ|=0.507s. QUALIFIES on metric, but was just tuned in the 2026-05-25 session (mu_peak change reduced mean|Δ| 0.600 → 0.507s).
3. **`two-stroke`** — N=5 (does NOT qualify, threshold is >5), mean|Δ|=0.683s. The 2026-05-24 report explicitly documented that all 4 wired knobs are exhausted for this cluster.

`mid-twin-300-500` is disqualified by the "not visited in 21+ days" rotation rule. `two-stroke` is disqualified by N=5 not exceeding 5. **Target: `entry-150-200`** by elimination.

---

## Worst Per-Bike Deltas in entry-150-200

| Bike                  | sim    | bench | Δ        | source                          |
| --------------------- | ------ | ----- | -------- | ------------------------------- |
| TVS Apache RTR 200 4V | 19.303 | 15.90 | +3.403   | DERIVED (0-100 × 1.6, ±0.7s)    |
| Yamaha MT-15 V2       | 19.145 | 15.80 | +3.345   | DERIVED                         |
| Yamaha MT-15 V1       | 17.051 | 15.80 | +1.251   | DERIVED                         |
| Bajaj Pulsar NS200 BS6| 15.952 | 16.90 | -0.948   | MotorBikeCatalog 2012 (verified)|
| Yamaha YZF-R15 V4     | 18.504 | 17.62 | +0.884   | MotoStatz 2021 (instrumented)   |
| Yamaha YZF-R15 V3     | 16.997 | 17.62 | -0.623   | MotoStatz 2020 (instrumented)   |
| Bajaj Pulsar NS200    | 16.501 | 16.90 | -0.399   | MotorBikeCatalog 2012 (verified)|
| Bajaj Pulsar RS 200   | 15.944 | 15.70 | +0.244   | DERIVED                         |

**Restricted to verified/instrumented benchmarks (4 of 8):**

| Bike                  | Δ        |
| --------------------- | -------- |
| Pulsar NS200 BS6      | -0.948   |
| Pulsar NS200          | -0.399   |
| YZF-R15 V3            | -0.623   |
| YZF-R15 V4            | +0.884   |

Verified-only mean|Δ|=0.713s, bias=-0.272s — sim is actually **slightly fast** on average against the verified subset. The +0.895s positive bias is DERIVED-driven.

---

## Hypothesis Tested

The cluster mean|Δ|=1.387 is dominated by two outliers (RTR 200 4V at +3.403, MT-15 V2 at +3.345), both DERIVED. If their benchmarks were correct, a knob speeding sim up would help. But the 3 verified bikes already sim too fast (NS200 BS6 -0.948, NS200 -0.399, R15 V3 -0.623), so speeding sim up would worsen them.

**The bias signal is unattributable to the physics model**; it reflects benchmark-data inflation. Confirmed by knob probe:

| Bike (sim ET) | base   | parasitic_mult |              |              | over_clutch_factor |              | max_engine_decel_rads2 |              |
|---------------|--------|----------------|--------------|--------------|--------------------|--------------|-----------------------|--------------|
|               |        | 0.95           | 0.70         | 0.55         | 0.60               | 0.70         | 500                   | 700          |
| R15 V3        | 17.440 | 17.440         | 17.440       | 17.440       | 17.440             | 17.440       | 17.440                | 17.440       |
| R15 V4        | 18.955 | 18.955         | 18.955       | 18.955       | 18.955             | 18.955       | 18.955                | 18.955       |
| Pulsar NS200  | 16.867 | 16.867         | 16.867       | 16.867       | 16.867             | 16.867       | 16.867                | 16.867       |
| RTR 200 4V    | 19.728 | 19.728         | 19.728       | 19.728       | 19.728             | 19.728       | 19.728                | 19.728       |
| MT-15 V2      | 19.573 | 19.573         | 19.573       | 19.573       | 19.573             | 19.573       | 19.573                | 19.573       |

**All 4 wired knobs produce zero delta on every bike in the cluster.** Same dead-knob pattern documented in the 2026-05-24 session for `mid_twin_300_500`: the launch isn't headroom-limited (over_clutch_factor inert), engines aren't deceleration-limited (max_engine_decel_rads2 inert), and parasitic_mult is bypassed because the bikes have `dyno_curve.is_at_wheel=True`.

---

## REVERT Decision

The REVERT GATE applies: cluster-mean improvement < 50ms is unattainable with current wired knobs, AND the bias signal cannot be cleanly attributed to a physics-model defect (it's data-quality driven). Per CLAUDE.md hygiene "honest physics validation > apparent accuracy", a null session is the correct outcome.

**No code changes shipped.**

---

## K5/R1/Hayabusa Preservation Check

```
K5=10.0334  R1=10.2859  Busa=10.4712
All baselines exact to 4 decimals (the documented precision).
```

No physics changes were made; baselines naturally unchanged.

---

## Top-10 |Δ| Check

`top-10 mean|Δ| = 0.0114s` from the current sweep — well within the ±0.032s marketing-claim ceiling. No change from session start.

---

## Test Results

```
tests/test_power_boost_regression.py
tests/test_submodel_kaizen.py
tests/test_two_stroke.py
tests/test_physics_invariants.py    (1 SKIPPED — hypothesis not installed)

51 passed, 1 skipped, 0 failed in 7.64s
```

---

## DB Reseed

Skipped — no spec_to_bike_config changes were made.

---

## Recommendations for Future Sessions

1. **Resolve the dead-knob situation structurally.** The 2026-05-24 session explicitly recommended wiring `mu_peak_override` into `submodels/tire.py` and `chain_efficiency_override` into `submodels/drivetrain.py`. These are 15-30 line changes that would unlock new calibration levers for clusters that are currently dead to all 4 wired knobs (`entry_150_200`, `mid_twin_300_500`, `two_stroke` — i.e., the 3 worst-bias clusters). This is the next high-ROI session.

2. **Audit `entry-150-200` benchmarks before tuning physics.** Of the 8 benchmarks, 6 are DERIVED (0-100 × 1.6 with ±0.7s uncertainty). The two extreme outliers (RTR 200 4V at +3.403, MT-15 V2 at +3.345) drive 47% of the cluster mean|Δ|. If those DERIVED benchmarks are inflated 0-100 multiples (likely — real RTR 200 4V 0-100 is ~12s, would give ET ~19.2s closer to sim 19.3s), the actual ET targets should be revised upward and the cluster bias would collapse without any physics change.

3. **`mid-twin-500-700` is a clean signal.** N=8, all instrumented (Sport Rider, MotoStatz), all sim slow by +0.03 to +0.48s, bias +0.211s, mean|Δ|=0.214s. Below the 0.4s priority-1 threshold today, but if N grows to 12+ or mean|Δ| crosses 0.3s it becomes the cleanest next target. All 8 are inline-4 600cc sportbikes (GSX-R 600, R6, CBR600RR) sitting in the 500-700cc cluster — the profile currently has `over_clutch_factor=0.20`, `max_engine_decel_rads2=150`, `parasitic_mult=1.0`. Worth a single bump of `parasitic_mult` 1.0→0.92 next session.

4. **`two-stroke` requires `mu_peak_override` wiring before any further physics work.** The bimodal signal (RD350/NSR250R sim-slow vs RG500/RS250 sim-fast) cannot be resolved with a single global knob — the vintage bias-ply grip difference is the documented hypothesis (5/24) and needs a code-level wire.

---

## Session-end state

- Files edited: **none**
- DB unchanged
- Reference baselines: K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s (unchanged)
- Test suite: 51 passed / 1 skipped / 0 failed
