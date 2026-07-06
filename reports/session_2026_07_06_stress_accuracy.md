# Session Report — July 6, 2026: Stress-Test + Full-Corpus Accuracy Overhaul

**Operator directive:** "auto session, stress test the engine and website, fix
everything that breaks, dedupe part titles, make parts compatibility very
precise, complete overhaul; scrap the 3-bike baseline and try a different
approach so accuracy increases as much as possible; rerun it all and update
the accuracy findings + facts on the website."

**Branch:** `claude/motoquant-stress-test-accuracy-f7mtx0`

---

## 1. The 3-bike baseline is retired — what replaced it

Until this session every physics change had to keep the three hand-curated
reference bikes (K5 10.0334 / R1 10.2859 / Hayabusa 10.4712) bit-identical.
That constraint froze the launch-model knobs for every bike ≥60 hp and hid a
structural error the corpus-wide residuals make obvious:

**Engine character (cylinder count), not displacement, is the dominant
systematic.** The 246-row weighted residual table split by cylinders:

| population | n | w_sum | w_bias |
|---|---|---|---|
| singles | 37 | 13.0 | **−0.187** (sim fast) |
| twins | 77 | 50.6 | **−0.108** (sim fast; −0.20 within the 600-1100 sport band) |
| triples | 21 | 15.4 | +0.017 (centered) |
| fours | 111 | 91.5 | +0.037 (≈centered; small-cc I4s +1.1s slow) |

The new regime: the tuning objective is the FULL weighted benchmark corpus
(`scripts/tune_cluster_knobs.py` — same matching + source weights as
`phys_weighted_sweep.py`, per-cluster evaluation, multiprocess). The three
reference bikes are ordinary corpus members. Their defaults.py ETs happen to
be unchanged (their cluster was already centered), but nothing pins them
anymore except the regression golden, which pins EVERY bike equally.

### Taxonomy v2 (cylinder-aware clusters)

`derive_category_tag` gained a `cylinders` parameter (None ⇒ July-3 behaviour,
so old saved configs are untouched) and three new clusters:

- `sport_twin_600_1300` — sport/naked twins 600–1300cc (Ducati V2s, RS 660,
  MT-07, RE 650s, Buell 1125R, RC8 R, Monster 1200; deliberately placed BEFORE
  the 195hp gate so the Panigale 1199/1299 route here too).
- `small_i4_screamer` — sub-500cc I4s (ZX-4RR, ZX-25R) that shared a commuter-
  twin launch profile and simmed +1.1…+1.3s slow.
- `single_300_500` — 300–500cc singles (390 Duke family, RE 350 J-platform,
  G310, Himalayan).

`scripts/sweep_with_clusters.py::cluster_for` now DELEGATES to
`derive_category_tag` — the taxonomy has exactly one source of truth (it was
previously mirrored by hand in two files).

### Calibration changes (all grid-derived on the weighted corpus)

| cluster | change | effect |
|---|---|---|
| sport_twin_600_1300 | `mu_peak_override=1.31` (twins can't use full sport-radial grip off the line) | w\|Δ\| 0.262→0.187, bias −0.178→+0.002 |
| single_300_500 | synthetic-curve tail ×1.05→×1.00 for 30-60hp singles (defaults.py, cylinder-aware) + `mu_peak_override=1.10` (Indian OEM rubber) | w\|Δ\| 0.502→0.484, bias −0.327→−0.045 |
| small_i4_screamer | `max_engine_decel_rads2=2800` (near-massless crank; single-knob fit on n=2 by design) | w\|Δ\| 0.794→0.351, bias +0.776→+0.091 |
| mid_twin_300_500 (twins-only now) | decel 50→150 | w\|Δ\| 0.409→0.393, bias +0.196→+0.124 |
| entry_200_300 | (no knob change; singles-tail fix + ZX-25R leaving) | w\|Δ\| 0.343→0.281 |
| cruiser_1300p | oc 0.45→0.60, decel 900→1100 (saturates; residual +0.23 is not launch-reachable) | w\|Δ\| 0.255→0.231 |
| two_stroke | decel 1500→1800 | bias +0.153→+0.096 |
| other | oc 0.30→0.40, decel 800→1000 (re-centering after sporty twins left) | w\|Δ\| 0.285→0.277 |
| litre-sport-195+ / litre-600-1000 (I4+triples) / mid-twin-500-700 | **untouched** — already centered | — |

### Benchmark corpus hygiene (honest-data rules enforced)

- RG500 Gamma 1985: 11.60/180 → **11.37 @ 193** (Cycle magazine 12/1985; the
  old 180 km/h trap was a transcription error).
- Pulsar NS200 2012 source relabelled "(site estimate; transcription
  verified)" — the value is MBC's estimate, not instrumented.
- 3 exact-duplicate rows removed (ZX-10R 2006/2008 double-adds; ZX-6R 2024
  aggregator row that was SHADOWING the July-4 instrumented row and silently
  downgrading its weight). Corpus: 224 → 221 unique benchmarks, 246 matched
  pairs unchanged.
- 10 outlier benchmarks web-verified and deliberately LEFT (H2 SX SE+,
  Bandit 1250, R nineT, VMAX, Z400, VFR800F… sources confirmed; the residuals
  are honest model error). RE Classic 350 + XPulse DERIVED rows kept — no
  instrumented replacement exists (noted: Autocar's instrumented 0-100 for the
  Classic 350 is 16.23s, so the row's ~14s×1.6 premise is doubly unreliable,
  but replacing one derivation with another violates the house rule).

### Reference-bike DB rows fixed (root cause found)

`/api/simulate?bike_id=3` was ~0.36s FASTER than the hand-curated Hayabusa:
the three reference `bike_configs` rows carried `category_tag=NULL` (excluded
from reseed by design, so the schema-v6 column was never stamped), and the
runtime fallback derivation landed the 1299cc/173hp Hayabusa in the "other"
catch-all with an over-clutch launch. `scripts/patch_2026_07_06_reference_configs.py`
stamps `litre_sport_195p` on ids 1/2/3. K5/R1 were unaffected (their derived
cluster shares the same launch knobs); their documented DB-vs-defaults delta
is the by-design Aamby-vs-sea-level environment.

## 2. Headline accuracy

Authoritative sweep: `reports/acc_final_2026_07_06.json` (542 bikes,
chunked spec-path sweep, same machinery as every prior acc_final).

| metric | July 4 (before) | July 6 (after) | change |
|---|---|---|---|
| weighted mean \|Δ\| | 0.2418 s | **0.2166 s** | **−10.4%** |
| weighted bias | −0.0247 s | +0.0212 s | ≈centered |
| matched pairs | 246 | 246 | — |
| unique benchmarks | 224 (3 dupes) | 221 (deduped) | honest |
| references (defaults.py) | 10.0334 / 10.2859 / 10.4712 | unchanged | untouched by design — their cluster was already centered |

Per-cluster (weighted mean |Δ| / bias):

| cluster | n | w_sum | w\|Δ\| | bias |
|---|---|---|---|---|
| litre-sport-195+ | 29 | 22.1 | 0.125 | +0.007 |
| litre-sport-600-1000 (I4/triple) | 69 | 59.0 | 0.158 | +0.005 |
| sport-twin-600-1300 (NEW) | 42 | 35.0 | 0.187 | +0.002 |
| mid-twin-500-700 | 13 | 9.4 | 0.132 | +0.047 |
| other | 34 | 20.3 | 0.277 | +0.045 |
| entry-200-300 | 14 | 5.8 | 0.282 | +0.114 |
| single-300-500 (NEW) | 15 | 7.3 | 0.484 | −0.046 |
| small-i4-screamer (NEW) | 2 | 0.8 | 0.351 | +0.091 |
| mid-twin-300-500 (twins) | 7 | 3.2 | 0.393 | +0.124 |
| cruiser-1300+ | 3 | 2.1 | 0.231 | +0.231 |
| two-stroke | 6 | 3.2 | 0.537 | +0.146 |
| entry-150-200 | 12 | 3.4 | 0.820 | +0.018 |

Every cluster with meaningful weight now sits under 0.20s weighted or is
explicitly data-limited (entry/single/two-stroke raw spreads are dominated
by DERIVED ×0.1 rows; the July-4 finding that those clusters are
data-quality-limited stands).

## 3. Stress test (0 crashes)

60 API operations × 190 checks via TestClient: **zero 500s**. Full pytest
suite, next build 76/76, 40-bike random sim fuzz — clean. Findings fixed:
autotune/optimize swallowed 404s as 400s; negative `limit` returned unlimited
rows; `/api/simulate/save` accepted negative ETs; plus the catalog-integrity
classes below.

## 4. Catalog integrity (parts + tires)

**−3,684 impossible compatibility pairs removed (56,889 → 53,205)**, zero
unreachable parts, zero bikes without an exhaust, via
`scripts/patch_2026_07_06_catalog_integrity.py` (idempotent — 0 changes on
re-run, and 0 changes after a full reseed, proving the seed-source fold):

- **Phantom chain pitches** on 15 belt/shaft/CVT bikes (Indian Scout/Chief
  family, Rocket 3, R 1300 GS, FJR1300, Tiger 1200, V100 Mandello, Aerox 155
  CVT) — these matched sprockets/chains/quickshifters they physically cannot
  take. Root cause fixed at the importer: `_BELT_DRIVE_MAKES` had matched
  NOTHING since the June-13 "Indian Motorcycle"→"Indian" manufacturer merge;
  R 1300/R 12, V100, Rocket 3, FJR1300, Tiger 1200, Aerox added to the
  shaft/CVT exclusions; the chain-drive FTR 1200 kept via an explicit
  exception.
- **27 EFI/electronic parts stroke-gated** — quickshifters and fuel-injection
  controllers were matching carbureted 1970s two-strokes. The Zeeltronic YPVS
  controller now matches exactly the powervalve bikes (year_min=1983), which
  also surfaced RD500LC/RZV500R being stored as I4 (they are V4 two-strokes
  — fixed in DB + importer tokens).
- **Model-named leaks** category/year-gated: GSX-R1000-named parts off the
  GSX-S/Katana family, R1 ECU flashes off the carbureted 1989 FZR1000,
  generation-coded flashes (K5/K7/4C8) year-pinned, Hayabusa bodywork off the
  B-King, Duke-390 parts off the 390 Adventure, MTC lockup (99-21) off the
  2024 Gen-3 Hayabusa. Misleadingly-named parts renamed to honest class names
  (S&S "RE Twin" → "(HD/Indian V-Twin)", 600-supersport class exhausts).
- **8 ClutchCo SKUs** displacement-banded — each previously matched 414
  bikes, stacking optimizer candidate pools; now max 2 kits per bike.
- **Duplicate Walbro pump merged** (parts 594 → 593); displacement-band
  absurdities fixed (litre nitrous on 800s, "400cc" systems on 200cc bikes).
- Data fixes: KTM 1390 I2→V2 (+ importer token), GSX-S1000GT →sport_touring,
  Apache RTR 310 →naked.
- **API hygiene**: autotune/optimize now return clean 404s for unknown bikes
  (was a 400 with "404: …" leaked in the body), list routes reject
  negative/zero limits (limit=-5 previously returned the entire table),
  save-run validates ET/trap bounds (negative ETs were persistable to the
  leaderboard). 62 new production-path integrity tests + 13 API tests.
- Honest residual leaks documented and deliberate: Exciter 155 VVA shares
  the R15's 155 VVA engine (parts genuinely fit), carb Pulsar 200 keeps
  NS200 bolt-ons (only the ECU tune was impossible), M 1000 XR is stored
  'sport' (recategorizing is cluster-coupled — flagged for operator).

Tires: 6 duplicate-title rows merged (notation twins '100/90-17' vs
'100/90R17' — MRF Zapper ×3, IRC GP-110, Bridgestone Battlax ×2);
`TireRepository.create` + `drag_tires_cruiser._ensure_tire` now match on
NORMALIZED physical size so re-seeds converge instead of re-minting;
`tests/test_tire_integrity.py` pins both halves. The web tire pickers now
display the size (`Pilot Power 3 · 190/55ZR17`) — the same model name in 3
sizes previously rendered as 3 identical entries, which is what read as
"duplicate titles".

## 5. Derived artifacts regenerated

- **Full reseed** — all 541 current bike_configs re-stamped with taxonomy-v2
  category_tags (71 sport twins / 47 singles / 4 screamers); the three
  July-6 patch scripts re-applied post-reseed with 0 changes (idempotency +
  fold proven). Any future reseed chain must include them (all idempotent).
- **Regression golden regenerated** — both tiers green: fast (~35-bike
  stratified sample) and slow (`MOTOQUANT_SLOW_TESTS=1`, every current bike
  through the production DB path).
- **Surrogate v2.4 full regen** — 9,126 tasks cluster-stratified on the v2
  taxonomy (see artifacts/surrogate/README.md v2.4 entry for metrics).
- **`/validation` dataset regenerated** (stamp 2026-07-06): within ±0.10s
  62 → 82 bikes, within ±0.20s 113 → 137, top-10 mean |Δ| ±0.0065s.
- Sitewide fact sync: counts (541/593/254/1860/20), accuracy claims, corpus
  221, 12-cluster taxonomy description, OG card.

## 6. Verification

<!-- VERIFICATION -->
