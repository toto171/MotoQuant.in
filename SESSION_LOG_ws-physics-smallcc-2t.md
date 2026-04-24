# Stream `ws/physics-smallcc-2t` — Small-cc 4T + 2-stroke Calibration

**Branch:** `ws/physics-smallcc-2t` (off `main` @ `f7bfd5f`)
**Workstream owner:** physics-smallcc-2t
**Goal:** Close the four worst-cluster ET biases without breaking K5/R1/Hayabusa references.

Pre-fix bias landscape (from CLAUDE.md Apr 24 PM):

| Cluster                          | Pre-fix bias | Post-fix bias | Reduction |
|----------------------------------|-------------:|--------------:|----------:|
| 300–500 cc twin                  |      +1.06 s |  **+0.41 s**  |  **61 %** ✓ |
| 200–300 cc entry                 |      +2.53 s |  **+1.41 s**  |  **44 %** ✓ |
| 150–200 cc entry                 |      +2.86 s |  **+1.84 s**  |  **36 %** (partial) |
| 2-stroke                         |      +2.70 s |  **+1.85 s**  |  **31 %** (partial) |

Reference baselines (hand-built in `defaults.py` — MUST be preserved):

| Bike       | Target     | Post-fix   | Δ            |
|------------|-----------:|-----------:|-------------:|
| K5         | 10.0334 s  | 10.0334 s  |  **+0.0000 s** ✓ |
| R1 (4C8)   | 10.2859 s  | 10.2859 s  |  **+0.0000 s** ✓ |
| Hayabusa   | 10.4712 s  | 10.4712 s  |  **+0.0000 s** ✓ |

Overall validation (N=79 benchmarks, word-boundary matched):

| Metric              | Pre-fix | Post-fix | Δ              |
|---------------------|--------:|---------:|---------------:|
| mean \|Δ\|          | 0.726 s | **0.562 s** | **−23 %**       |
| median \|Δ\|        | 0.240 s | 0.208 s  |  −13 %         |
| bias (sim − real)   | +0.550 s| +0.340 s | 38 % smaller   |
| within ±0.10 s      | 15 (20 %)| 17 (22 %)| +2 pp          |
| within ±0.20 s      | 30 (40 %)| 38 (48 %)| +8 pp          |
| within ±0.50 s      | 54 (73 %)| 58 (73 %)| ~same          |
| within ±1.00 s      | 58 (78 %)| 65 (82 %)| +4 pp          |
| top-10 mean \|Δ\|   | ±0.032 s| **±0.027 s** | 15 % tighter    |

**Clean clusters (already healthy, not regressed):**

| Cluster                          | Pre-fix bias | Post-fix bias |
|----------------------------------|-------------:|--------------:|
| Litre sport ≥195 hp              |    −0.11 s   |  **−0.01 s**  |
| 600–1000 cc sport                |    +0.15 s   |  **−0.11 s**  |

---

## 1. Hypothesis (going in)

Previous session flagged "small-cc sim is gear-1-limited" but never
investigated. Working hypotheses (rank-ordered by suspected impact, per
orchestrator):
- (a) Clutch slip held too long / engagement model wrong
- (b) Tire mu_peak too low (traction-limited cap)
- (c) Weight-transfer staging (cog_height_mm wrong)
- (d) 2T expansion-chamber Gaussian too narrow for piston-port low-rev 2T
- (e) Launch RPM ceiling above peak torque

## 2. Diagnosis

Quick timeseries dump on three representative sufferers (R15 V3 for
150–200 cc entry, Pulsar NS200 for 200–300 cc entry, CBR500R for
300–500 cc twin) plus 2T canaries (RX100, RD350).

### 2.1 4T small-cc findings

Sample timeseries for **R15 V3** (pre-fix sim ET = 19.50 s; real ≈ 16.0 s):

```
 t(s)   x(m)  v(km/h)  rpm  gear  accel(g)  trac%
 1.00    1.2     8.7  8500    1    0.25    52.3
 5.00   30.1    43.3  8500    1    0.24    48.0
 7.50   67.6    64.4  8506    1    0.24    48.3    ← clutch lockup
10.00  119.1    83.5 11031    1    0.19    42.4
13.00  195.7    99.5  8695    2    0.14    33.9
```

Key observations:
- R15 V3 spends **60 %** of the quarter in gear 1.
- Acceleration capped at **0.25 g during the full 7.5 s clutch-slip phase**.
- Traction is **48 %** — *not* tire-limited.
- Wheelie ceiling is 1.42 g — way above observed accel.

Hand calculation against the slip-phase numbers:

| quantity              | value          |
|-----------------------|----------------|
| `T_e` at 8500 rpm     | 14.7 Nm (peak) |
| `i_total` (gear 1)    | 15.63          |
| `eta_dt`              | 0.926          |
| `r_eff`               | 0.314 m        |
| `F_drive`             | **678 N**      |
| Observed `a`          | 0.243 g = 2.38 m/s² |
| Observed effective m  | 678 / 2.38 = **285 kg** |

But `chassis.total_mass_kg` is only 231 kg. The extra 54 kg is the
rotational inertia reflected to the wheel:
- `m_rot_engine` = `(I_engine + I_basket) × (i_total / r_w)²` = `(0.00572 + 0.010) × (15.63/0.314)²` = **39.0 kg**
- `m_rot_rear`  = `0.55 / 0.314²` = 5.6 kg
- `m_rot_front` = `0.35 / 0.314²` = 3.6 kg

**Two real chassis+clutch bugs jumped out:**

**Bug 1 — `chassis.fluid_mass_kg` is K5-default (17 kg) for every bike.**
Real R15 V3 fuel + oil + coolant payload is ~9 kg. The K5's 17 kg is
for a 17.5 L tank, 4 L oil, 2 L coolant. Phantom mass: 8 kg per bike,
invisible to large-cc bikes but a real ET penalty on commuters.

**Bug 2 — `clutch.basket_inertia_kgm2` is K5-default (0.010) for every bike.**
Real R15 V3 basket I ≈ 0.0015. The basket inertia multiplies through
`(i_total/r_w)²` = 2478 in gear 1. So the 0.010 → 0.0015 over-estimate
costs **21 kg** of phantom rotational mass on the wheel — ~9 % of
effective mass in gear 1.

### 2.2 2-stroke findings

Sample sweep across all 20 2T bikes (pre-fix):

```
RX100, RX135, RXZ135                   DNF (stuck in gear 1, max RPM 8483)
Aprilia RS125 (33 hp PV)               19.26 s   trap 121 km/h
RD350 (39 hp 2-cyl PP)                 17.03 s   trap 140 km/h
```

**Bug 3 — synthetic 2T curve too narrow for sub-200 cc piston-port singles.**
Apr-21 calibration narrowed the Gaussian band to `band_lo=0.12,
band_hi=0.08, baseline=0.12` for *all* single-cyl piston-port 2Ts. That
is correct for race singles like KTM 250 SX, wrong for production
commuter singles (RX100/RX135/RXZ135, Suzuki AX100 class). Sampled
RX100 torque on the pre-fix curve:

```
rpm=5361   T=1.25 Nm (baseline)
rpm=7141   T=8.23 Nm  (~peak)
rpm=8850   T=1.25 Nm (baseline)
```

Real RX100 dyno shows ~70 % of peak at 5500 rpm, ~50 % at 8500 rpm —
the sim collapsed both. With torque <2 Nm above 8100 rpm, F_drive in
gear 1 fell below drag and the bike asymptoted well below shift_rpm —
**never shifting**.

**Bug 4 — 2T launch_rpm = 0.92 × tuned_rpm is below peak torque.**
For RX100: `tuned_rpm = 7500`, launch = 6900. But `peak_torque_rpm =
6500` and the Gaussian peak is at 7500 — 6900 rpm is on the rising
edge at ~half torque.

---

## 3. Implementation

All fixes are surgical edits to `motoquant/scraper/importer.py`,
`motoquant/defaults.py`, and `motoquant/models.py`. **Zero edits to
`physics.py`, `drivetrain.py`, or any sub-model.** This guarantees
K5/R1/Hayabusa references (hand-built in `defaults.py`, do *not* flow
through `spec_to_bike_config`) are untouched — and the sweep confirmed
them at ±0.0000 s.

| # | File          | Change                                                   |
|---|---------------|----------------------------------------------------------|
| 1 | `importer.py` | New `_fluid_mass_from_spec(spec)` — clip(8.0 + 0.009×disp_cc, 7.0, 22.0) |
| 2 | `importer.py` | New `_basket_inertia_from_spec(spec)` — clip(0.00001×disp_cc, 0.0010, 0.020) |
| 3 | `importer.py` | `_build_chassis_from_spec` uses scaled fluid + fuel mass  |
| 4 | `importer.py` | `spec_to_bike_config` overrides `clutch.basket_inertia_kgm2` |
| 5 | `importer.py` | 2T `staging.launch_rpm = max(peak_tq_rpm, tuned_rpm)`, capped at 0.96×redline |
| 6 | `importer.py` | Passes `displacement_cc` into `_synthetic_2stroke_torque_curve` |
| 7 | `defaults.py` | `_synthetic_2stroke_torque_curve` new `displacement_cc` kwarg + small-commuter-single branch (band_lo=0.35, band_hi=0.25, baseline=0.35) |
| 8 | `models.py`   | `EngineParams._two_stroke_torque` same small-commuter-single branch (kept in sync) |

Every formula is calibrated so **1000 cc land on the K5 reference
value** — 17.0 kg fluid and 0.010 kg·m² basket inertia. This preserves
all bikes at and above K5 displacement and only scales *down* for
smaller bikes.

### Why these fixes are physically motivated, not magic multipliers

- **Fluid mas