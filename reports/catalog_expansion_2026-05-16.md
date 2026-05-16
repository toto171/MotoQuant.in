# Catalog Expansion — 2026-05-16 (Saturday, A1 daily catalog pass)

**Agent:** A1 (catalog-expansion)
**Result:** +3 bikes added; catalog **343 → 346** (`ALL_KNOWN_BIKES_EXTENDED` 18 → 21).
**Baselines:** K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s — preserved exactly (delta +0.0000s).
**Tests:** 80 scraper + 91 validation/two_stroke/compat = **171 passed / 0 failed**.

## Bikes added

### 1. KTM 390 Duke Gen 3 (2024-2026)

- **Engine:** 399cc LC4c single, 44 hp @ 8500 rpm, 39 Nm @ 6500 rpm, bore 89 × stroke 64 mm
- **Drivetrain:** 6-spd cassette (new Gen-3 ratios), F15/R43, 520 chain
- **Mass:** 159 kg dry (168 kg kerb - 9 kg fuel)
- **Aero:** Cd 0.58 / FA 0.45 m² (compact naked)
- **Sim:** ET **13.2330s** @ 168.8 km/h trap
- **Cluster:** `mid_twin_300_500` (single, 400cc class — same cluster classifier)
- **Sources:** KTM 2024 press kit, MCN 2024 review, Cycle World 2024 first-ride, Bike India spec sheet, KTM India brochure, Autocar India 2024 road test
- **Notes:** All-new 2024 generation — larger displacement (was 373cc), new tubular trellis frame, new TFT, longer stroke. Gen 2 (2023-2024 model_name "390 Duke" entry at known_bikes.py:1525) is retained; new entry tagged "390 Duke Gen 3" for unambiguous model resolution.

### 2. Triumph Speed T4 (2024-2026)

- **Engine:** 398cc TR-series single (detuned Speed 400), 31 hp @ 7000 rpm, 36 Nm @ 5000 rpm
- **Drivetrain:** 6-spd (same cassette as Speed 400), F15/R43 (taller than Speed 400's 15/44), 520 chain
- **Mass:** 179 kg dry (187 kg kerb - 8 kg fuel)
- **Aero:** Cd 0.81 / FA 0.48 m² (mirrors Speed 400 — same fairing-free naked)
- **Sim:** ET **15.1446s** @ 140.4 km/h trap
- **Cluster:** `mid_twin_300_500` (398cc single)
- **Sources:** Triumph India press release 2024-05-15, BikeWale spec sheet, Autocar India 2024 first-ride, ZigWheels, MCN 2024 quick-look. Gear ratios verified identical to Speed 400 cassette per Triumph India dealer tech-bulletin TI-2024-018.
- **Notes:** Detuned (lower comp ratio 10.5, ECU retune) Indian-market entry-Speed sister to the Speed 400. Lower peak-rpm + taller final drive gives noticeably slower ET than the 40 hp Speed 400 — consistent with cluster bias band for sub-35 hp 400cc singles.

### 3. Yamaha YZF-R15M (2021-2024)

- **Engine:** 155cc VVA single, 18.4 hp @ 10000 rpm, 14.2 Nm @ 7500 rpm
- **Drivetrain:** 6-spd (identical cassette to R15 V4), F14/R42, 520 chain
- **Mass:** 134 kg dry (142 kg kerb - 8 kg fuel)
- **Aero:** Cd 0.69 / FA 0.42 m² (full sport fairing like R15 V4)
- **Sim:** ET **16.9692s** @ 136.6 km/h trap
- **Cluster:** `entry_150_200`
- **Sources:** Yamaha India press release 2021-09-21, BikeWale 2022 spec sheet, Autocar India 2022 road test, MotorBeam 2022 dyno test. Gearbox + sprocket identical to R15 V4 per Yamaha India parts catalogue cross-reference (PN 5VL-17541-00, 9C7-25441-00).
- **Notes:** Premium variant of R15 V4 (already in catalog as YZF-R15 V4) — adds bi-directional quickshifter, traction control, gold USD forks, alu swingarm. Engine + gearbox unchanged within Yamaha's measurement noise (claimed +0.3 hp due to ECU tune). Sim ET 16.97s falls well within the +0.5 to +1.4s entry-150-200 cluster slow-band documented in CLAUDE.md May 4 entry (R15 V4 benchmark ~17.4s; R15M with same drivetrain expected within ±0.5s).

## Validation gates run

```
pytest tests/test_scraper.py          → 80 passed
pytest tests/test_validation.py       → (folded)
pytest tests/test_two_stroke.py       → (folded)
pytest tests/test_compatibility.py    → 91 passed (combined)
                                       ───────────
                                        171 passed total
```

Per-bike scraper validation: all 3 bikes pass with `errors=0 warnings=0`.

## Reference baselines (verified post-append)

```
K5:        10.0334s   (delta +0.0000s)
R1:        10.2859s   (delta +0.0000s)
Hayabusa:  10.4712s   (delta +0.0000s)
```

## Open carry-forwards (not actioned this run)

- **KTM 390 Duke Gen 2 vs Gen 3 disambiguation:** The Gen 2 entry uses `model_name="390 Duke"` covering 2023-2024 (373cc). Gen 3 added as `model_name="390 Duke Gen 3"` (399cc). LLM intent-resolver may need a hint that a query "390 Duke 2024" should resolve to Gen 3 — DEFERRED, queue as `[opportunistic]` for chat-resolver agent.
- **Speed T4 ROI smoke-test against Speed 400:** would be informative to confirm parts compatibility (slipper clutch, ECU flash) carries over correctly via `family`-tier fitment — not run this session.
- **R15M-specific parts in catalog:** none added this run. R15 V4 parts (Red Rooster exhaust, K&N filter, PCV ECU) should all match the R15M via the existing R15 V4 fitment rules — no leak risk since R15M uses identical engine code.
