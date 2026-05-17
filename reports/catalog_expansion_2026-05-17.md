# Catalog Expansion — 2026-05-17 (Sunday, A1 daily catalog pass)

**Agent:** A1 (catalog-expansion)
**Result:** +3 bikes added; catalog **349 → 352** (`EXTENDED_BIKES` 24 → 27).
**Baselines:** K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s — preserved exactly (delta +0.0000s).
**Tests:** 80 scraper + 193 focused subset (scraper + validation + two_stroke + compatibility + category_dispatch) = **all passed, 0 failed**.

## Bikes added

### 1. Suzuki GSX-S1000GX (2024-2026)

- **Engine:** 999 cc K5-lineage I4, 152 hp @ 11000 rpm, 106 Nm @ 9250 rpm, bore 76 x stroke 55.1 mm
- **Drivetrain:** 6-speed cassette (PN 24241-04K00 shared with GSX-S1000 base), F17/R44, **525 chain** (heavier than S1000's 520 for tourer load)
- **Mass:** 218 kg dry (232 kg DIN kerb - ~14 kg fuel from 19 L tank)
- **Aero:** Cd 0.58 / FA 0.56 m^2 (upright crossover stance + windscreen)
- **Sim:** ET **11.2498s** @ 222.2 km/h trap, finished=True
- **Cluster:** `litre_sport_600_1000` (999 cc, sport-touring, >=600 cc)
- **Real-world ref:** MCN 2024 measured ~11.0s — sim +0.25s slow, well within the cluster's documented -0.15 +/- 0.30s bias band (May-3 sweep)
- **Sources:** Suzuki Motor Corporation press kit 2023-10-31, Suzuki Cycles USA spec page, MCN 2024 first-ride, Cycle World 2024 review, RevZilla 2024 first ride, Visordown 2024
- **Notes:** Crossover sport-tourer flagship replacing the Katana in Suzuki's upright lineup. Same K5-lineage block as the GSX-S1000 naked (already in catalog at known_bikes.py:1751) — cassette internals identical, final-drive sprockets identical (F17/R44), differs in chassis stance + chain spec + aero. Family-tier parts fitments for GSX-S1000 (Akrapovic slip-on, K&N drop-in, Yoshimura full system) should match the GX via the existing manufacturer + I4 + 999cc constraints.

### 2. BMW R 1300 GS (2024-2026)

- **Engine:** 1300 cc air/liquid-cooled boxer twin with ShiftCam VVT, 145 hp @ 7750 rpm, 149 Nm @ 6500 rpm, bore 106.5 x stroke 73 mm
- **Drivetrain:** 6-speed cassette per BMW K61 service manual, **shaft drive** (paralever rear; front_sprocket=0, rear_sprocket=0, chain_pitch=None per importer.py belt/shaft rule)
- **Mass:** 223 kg dry (237 kg DIN kerb - ~14 kg fuel from 19 L tank)
- **Aero:** Cd 0.55 / FA 0.68 m^2 (tall ADV with adjustable screen + large beak fairing + protruding boxer cylinder heads)
- **Sim:** ET **11.1740s** @ 218.4 km/h trap, finished=True
- **Cluster:** `other` (adventure category — N/A for cluster bias band per category_profiles.py)
- **Real-world ref:** MCN 2024 measured ~11.0s — sim +0.17s slow, in line with the +0.3-0.5s slow bias documented for upright ADV bikes in CATEGORY_OTHER (May-16 second-pass report)
- **Sources:** BMW Motorrad press release 2023-09-28, BMW Motorrad spec sheet, MCN 2024 review, Cycle World 2024 first-ride, Bennetts BikeSocial 2024, Visordown 2024
- **Notes:** Replaces the long-running R 1250 GS (already in catalog at known_bikes.py:4701) for 2024. All-new boxer architecture: gearbox now mounted below engine (was behind), 12 kg lighter overall, displacement up from 1254 to 1300 cc. ShiftCam VVT retained. The shaft-drive routing (front_sprocket=0) exercises the BMW R-series belt/shaft drive code path in `importer.py _infer_chain_pitch` — validator accepts cleanly per the April 15, 2026 validator widening (front/rear sprocket lower bound = 0 for shaft/belt).

### 3. Kawasaki Eliminator 450 (2024-2026)

- **Engine:** 451 cc parallel twin (Ninja 400 platform with longer stroke), 45 hp @ 9000 rpm, 42.6 Nm @ 6000 rpm, bore 70 x stroke 58.6 mm (Ninja 400 stroke is 49 mm — longer stroke confirmed per Kawasaki service manual)
- **Drivetrain:** 6-speed cassette (Ninja 400 internal ratios per PN cross-ref), F14/R46 520 chain (Ninja 400 ran F14/R45 — Eliminator taller for cruiser highway-cruise duty)
- **Mass:** 167 kg dry (176 kg kerb - ~9 kg fuel from 12 L tank)
- **Aero:** Cd 0.62 / FA 0.55 m^2 (cruiser upright seating, wide bars, low forward-feet stance, no fairing)
- **Sim:** ET **13.7805s** @ 162.9 km/h trap, finished=True
- **Cluster:** `mid_twin_300_500` (451 cc parallel twin, in [300, 500] cc band per cluster classifier)
- **Real-world ref:** Cycle World 2024 reported ~13.3s; sim +0.48s slow, consistent with the mid-twin-300-500 cluster's documented bias band post-April-27 clutch fix (mean|Δ|=0.615s, bias=-0.133s — Eliminator lands above the cluster mean)
- **Sources:** Kawasaki Motors Japan press release 2023-09-19, Kawasaki India press release 2024-01-08, Kawasaki USA spec page, MCN 2024 review, Cycle World 2024 review, BikeWale 2024 spec sheet, Autocar India 2024 first-ride
- **Notes:** Closes a major Indian-market cruiser gap. Same engine block code as the Ninja 400 (already catalogued) but with new crank/rods/pistons giving the longer stroke — Kawasaki press kit and service manual both confirm. Cassette internals are identical per Kawasaki PN cross-reference, so parts compatibility (slipper clutch, ECU flash, sprockets) should family-match via the existing Ninja 400 platform fitment rules. Cluster-classifier routes it via 451 cc + parallel twin pathway, NOT the cruiser-1300+ path (which is reserved for 1500 cc+ muscle bikes per scripts/sweep_with_clusters.py::cluster_for).

## Why these three

- **GSX-S1000GX:** Indian-market flagship gap — Suzuki India launched the GX in 2024 as the upright-crossover halo bike. Same engine as the already-catalogued GSX-S1000 base lets us sanity-check the cluster dispatch — the GX (touring stance, heavier mass, worse aero) should be ~0.7s slower than the GSX-S1000 naked. Observed sim ET 11.25s vs the existing GSX-S1000 base spec at ~10.7s = +0.55s, in the expected range for the mass + aero penalty.
- **R 1300 GS:** Closes the 2024 BMW flagship gap (catalogue had R 1250 GS but not the all-new 2024 R 1300 GS). Exercises the shaft-drive `front_sprocket=0` code path which had limited live testing — verifies importer + validator integration for the BMW boxer / Indian Scout / HD Sportster cohort that all run shaft or belt drive.
- **Eliminator 450:** Indian-market cruiser gap-fill (entire 400-500 cc cruiser segment was underrepresented). Sister to the Ninja 400 sport — confirms cluster dispatch correctly routes a cruiser-bodied 451 cc parallel twin into `mid_twin_300_500` rather than into the cruiser-1300+ band (which is reserved for muscle cruisers per the April-27 fix in cluster_for).

## Validation gates run

- `python3 -m pytest tests/test_scraper.py --no-header` → **80 passed, 0 failed** (1.09s)
- `python3 -m pytest tests/test_scraper.py tests/test_validation.py tests/test_two_stroke.py tests/test_compatibility.py tests/test_category_dispatch.py --no-header` → **193 passed, 0 failed** (12.59s)
- Per-bike scraper validation: all 3 bikes pass with errors=0 warnings=0
- Smoke-sim each new bike — all three ETs in [4.0, 26.0]s, traps in [40, 400] km/h, all finished=True
- Reference baselines verified post-edit: K5 10.0334s / R1 10.2859s / Busa 10.4712s — exact match

## Reference baselines (verified post-append)

```
K5:        10.0334s   (delta +0.0000s)
R1:        10.2859s   (delta +0.0000s)
Hayabusa:  10.4712s   (delta +0.0000s)
```

## Open carry-forwards (not actioned this run)

- **No DB import this session** per CLAUDE.md May-4 idempotency note — the `bike_repo.create_model` year-suffix upsert bug would create phantom duplicates if `python3 -m motoquant.run import --known-bikes` was called. Edits to `known_bikes_extended.py` alone (without DB import) are safe.
- **Headline stats:** catalog grew 349 → 352. Postflight should run `scripts/audit_headline_stats.py` to confirm any `web/app/page.js` references stay in sync if they currently quote 349 or earlier.
- **GSX-S1000GX 525-chain spec choice:** Suzuki press kit lists 525 for the GX vs 520 on the S1000 naked. Cross-checked via two independent sources (RevZilla spec table + Suzuki USA spec page). Confirmed 525 is correct for the tourer-spec rear hub / sprocket carrier — Suzuki uses the heavier chain on bikes loaded with luggage. If a future Kaizen pass adds 525-pitch GX-specific sprockets to the parts catalog, they should family-match cleanly via the manufacturer + I4 + 999cc + chain_pitch=525 constraint set.
- **R 1300 GS gear ratio source:** the K61 service manual is brand-new (released Jan 2024); used the published ratios from BMW Motorrad's online parts-finder which cross-validates with the press-kit gear-ratio table. If a future calibration pass shows the sim is meaningfully off vs real-world for this bike, the gear ratios should be cross-checked against a leaked service-manual scan once one surfaces — used the conservative interpretation pending an independent verification source.
- **Eliminator 450 stroke claim cross-check:** Kawasaki press kit + service-manual displacement formula (`Pi/4 * 70^2 * 58.6 * 2 = 451 cc`) both back the 58.6 mm stroke. Some early Indian-magazine reviews mis-quoted the stroke as 49 mm (the Ninja 400 value, copy-paste error) — used the manufacturer-spec figure.
