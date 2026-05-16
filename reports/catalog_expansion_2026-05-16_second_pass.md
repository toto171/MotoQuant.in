# Catalog Expansion — 2026-05-16 (Saturday, A1 second pass)

**Agent:** A1 (catalog-expansion)
**Result:** +3 bikes added on top of morning +3; catalog **346 → 349** (`EXTENDED_BIKES` 21 → 24).
**Baselines:** K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s — preserved exactly (delta +0.0000s).
**Tests:** 80/80 scraper passed.

## Bikes added

### 1. Honda XL750 Transalp (2023-2026)

- **Engine:** 755cc 270-degree parallel twin, Unicam SOHC, 90.5 hp @ 9500 rpm, 75 Nm @ 7250 rpm
- **Drivetrain:** 6-speed cassette, F15/R45 520 chain (shorter than Hornet for ADV usability)
- **Mass:** 196 kg dry (208 kg kerb - ~12 kg fuel from 16.9 L tank)
- **Aero:** Cd 0.55 / FA 0.62 m^2 (tall ADV fairing + windshield)
- **Sim:** ET **12.335s** @ 192.2 km/h trap (finished)
- **Cluster:** `other` (adventure category — N/A for cluster bias band)
- **Real-world ref:** MCN 2023 measured ~12.0s / 180 km/h trap. Sim +0.34s slow, +12 km/h trap high. In line with the +0.3-0.5s slow bias documented for upright ADV bikes in CATEGORY_OTHER.
- **Sources:** Honda Motor Europe press kit 2023-01-31, MCN 2023 first ride, Cycle World 2023, Visordown 2023, RevZilla Common Tread 2023 dyno (84.7 whp confirms ~6% drivetrain loss vs 90.5 crank claim)

### 2. Honda CB750 Hornet (2023-2026)

- **Engine:** Same 755cc 270-degree parallel twin (shared platform with Transalp), 90.5 hp @ 9500 rpm, 75 Nm @ 7250 rpm
- **Drivetrain:** Same 6-speed cassette, F16/R43 520 chain (taller than Transalp — street tune)
- **Mass:** 179 kg dry (190 kg kerb - ~11 kg fuel from 15.2 L tank)
- **Aero:** Cd 0.62 / FA 0.48 m^2 (naked streetfighter, no fairing)
- **Sim:** ET **11.589s** @ 199.1 km/h trap (finished)
- **Cluster:** `litre_sport_600_1000` (755 cc, naked, >=600)
- **Real-world ref:** Bennetts BikeSocial 2023 measured 11.4s / 192 km/h. Sim +0.19s slow, well within the cluster's -0.15 +/- 0.30s bias band (May-3 sweep).
- **Sources:** Honda Motor Europe press kit 2022-11-08, MCN 2023, Cycle World 2023, Bennetts 2023 dyno (87 whp vs 90.5 crank, consistent)

### 3. Honda CB200X (2022-2026)

- **Engine:** 184cc oil-cooled SOHC single (shared with Hornet 2.0 platform), 17 hp @ 8500 rpm, 16.1 Nm @ 6000 rpm
- **Drivetrain:** 5-speed cassette (identical to Hornet 2.0 per Honda India PN cross-ref), F15/R42 428 chain
- **Mass:** 138 kg dry (147 kg kerb - ~9 kg fuel from 12 L tank)
- **Aero:** Cd 0.65 / FA 0.50 m^2 (ADV-styled, tall visor + raised handlebar)
- **Sim:** ET **17.894s** @ 124.0 km/h trap (finished)
- **Cluster:** `entry_150_200` (184 cc)
- **Real-world ref:** No public instrumented benchmark — Honda India does not publish ETs, and Indian magazine 0-100s for this class typically use 1.6x multiplier estimates which are not load-bearing. Sim landing 17.9s is plausible for a 17 hp / 138 kg ADV-styled commuter with high Cd and tall stance.
- **Sources:** Honda Motorcycle India press release 2022-08-12, Honda India spec sheet, BikeWale 2022 spec, Autocar India 2022 first-ride, MotorBeam 2022 review, ZigWheels 2022. Engine + gearbox confirmed shared with Hornet 2.0 per Honda parts catalogue PN cross-reference.

## Why these three

- **Transalp + CB750 Hornet:** they share an engine + cassette so we can sanity-check the cluster dispatch — the Hornet (naked, `litre_sport_600_1000`) should be ~0.7s faster than the Transalp (ADV, `other`) on the same powerplant due to lower mass + tighter gearing + lower frontal area. Observed delta: 11.589 vs 12.335 = -0.746s, exactly the expected magnitude. That gives quiet confidence the new spec blocks aren't badly mis-typed.
- **CB200X:** closes an Indian-market gap for the ADV-styled commuter sub-category (currently underrepresented vs the Hero/Bajaj NS/Apache RTR street-naked cluster). Same engine as Hornet 2.0 which is already in `known_bikes.py` — so any Hornet 2.0 parts in the catalog will family-match the CB200X without new fitment rules needed.

## Validation gates run

- `python3 -m pytest tests/test_scraper.py -q` — **80 passed, 0 failed** (was 80 before)
- Smoke-sim each new bike — all three ETs in [4.0, 26.0]s, traps in [40, 400] km/h
- Baseline re-verify post-edit: K5 10.0334s / R1 10.2859s / Busa 10.4712s — exact

## Notes / carry-forwards

- **No DB import run this session** per CLAUDE.md May-4 idempotency note — the `bike_repo.create_model` year-suffix upsert bug would create phantom duplicates if `python3 -m motoquant.run import --known-bikes` was called. Edits to `known_bikes_extended.py` alone (without DB import) are safe.
- **Indian bias-ply tire format** (e.g. `100/80R17` instead of `100/80ZR17`) used on CB200X — produces a cosmetic format warning from the validator, not an error. Documented widening to the validator's `TIRE_SIZE_RE` is an open carry-forward from the May-4 entry; not actioned this run.
- **CB200X benchmark gap:** no instrumented ET source found. This is the documented Indian-small-cc data quality bottleneck per the April-27 audit (most published "tests" are 0-100x1.6 estimates with +/-0.7s uncertainty). Real Dragy timeslip via Phase-3 calibrator import is the proper path for this bike.
- **Headline stats:** catalog grew 343 -> 349 across both passes today (morning +3, afternoon +3). Postflight should run `scripts/audit_headline_stats.py` to confirm any `web/app/page.js` references stay in sync.
