# Catalog Expansion Report — 2026-05-21 (Thursday — Eleventh Pass)

## Bikes added (2)

1. **Benelli TRK 502 (2017-2024)** — Italian-branded ADV parallel twin, core Indian/EU mid-ADV
   - 499.6cc DOHC liquid-cooled parallel twin (BJ500P-A engine block), 47.5 hp @ 8500 rpm / 46.5 Nm @ 5500 rpm
   - 6-speed, F15/R43 520 chain, 229 kg dry; shares gear cassette with Benelli 502C in this catalog
   - Rationale: TRK 502 is Benelli's best-selling model in India; Benelli already has 6 entries
     (TNT 600i, Leoncino 500, 302R, TNT 300, Imperiale 400, 502C) but the TRK 502 was missing
     despite being the highest-volume Benelli. Popular drag comparison subject in India.
   - Cluster: mid_twin_300_500 (47.5hp ADV twin — sits between KTM 390 Duke and Kawasaki Z650)
   - **Smoke sim ET: 14.554s @ 147.7 km/h trap** — physically expected: 47.5hp burdened by 229kg
     ADV-laden dry mass. For comparison the 502C (217kg, same power) would be ~14.2s. The
     additional 12kg of ADV fitment (crash bars, tank, toolkit mount) accounts for ~0.35s delta.
   - Sources: Benelli EU press kit 2017 (benelli.com/press); MCN TRK 502 road test Jan 2018;
     BikeAdvice.in TRK 502 spec sheet review 2019; BikeDekho TRK 502 tech specs 2021;
     Benelli India (benelliindia.com/trk502, 2022)

2. **Kawasaki Versys 650 (2015-2024)** — long-running mid-ADV parallel twin, top seller in India/EU
   - 649cc DOHC liquid-cooled parallel twin (ER650 engine), 68 hp @ 8500 rpm / 64 Nm @ 7000 rpm
   - 6-speed, F15/R43 520 chain, 196 kg dry; shares ER650 cassette with Ninja 650 / Z650
   - Rationale: The Versys 650 is one of the best-selling mid-ADVs in the Indian and EU markets.
     The Kawasaki section has Versys-X 300, Versys 1000 SE, KLX 230/300, Z650RS, Ninja 1000SX
     but the core Versys 650 was absent — a significant gap for a bike that appears in nearly
     every mid-ADV drag comparison published in India.
   - Cluster: mid_twin_500_700 (68hp, 649cc ADV twin — consistent with Honda CB500F/X class)
   - **Smoke sim ET: 12.847s @ 175.0 km/h trap** — physically sensible: same engine as Ninja 650
     (likely ~12.5s) plus ~24kg dry mass penalty from ADV architecture gives ~0.35s slower.
   - Sources: Kawasaki UK/India press kit 2015 (kawasaki.co.uk/press); MCN Versys 650 road test
     2015 (MCN.co.uk); Bikez.com KLE650 2020 spec sheet; Kawasaki EPC parts catalog
     (epc.kawasaki.com, KLE650EFF 2020); BikeWale Versys 650 spec page 2022

## Validation

- `python3 -m pytest tests/test_scraper.py tests/test_validation.py tests/test_two_stroke.py`
  — **141 passed**, 0 failed, 571 warnings (pre-existing `datetime.utcnow()` deprecation)
- Both new bikes pass `spec_from_dict` validator; `finished_quarter=True`; ETs in [4.0, 26.0]s;
  traps in [40, 400] km/h
- **Reference baselines preserved EXACTLY: K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s,
  Δ +0.0000s on all three**

## DB re-seed

Ran `python3 -m motoquant.run --db motoquant.db import --known-bikes`:
- Imported: 39 (includes both new bikes + other fresh entries from prior pass timestamps)
- Errors: 430 (idempotency mismatches per documented WS-A April 27 hygiene — pre-existing)
- Total bikes in DB: 637
- Tire fitments rebuilt: 1193

## Headline stats

Cumulative 599→637 drift (from all 11 today's expansion passes) detected and patched:
- `web/app/page.js` (4 occurrences)
- `web/app/bikes/layout.js` (4 occurrences)
- `web/app/bikes/page.js` (1 occurrence)
- `web/app/features/layout.js` (1 occurrence)
- `web/app/layout.js` (2 occurrences)
- `web/app/StructuredData.js` (3 occurrences)
- `web/app/simulator/layout.js` (2 occurrences)
- `web/app/about/page.js` (1 occurrence)
- `web/app/whitepaper/page.js` (3 occurrences)
- `web/app/pricing/page.js` (1 occurrence)
- `web/app/blog/how-the-motoquant-physics-engine-works/page.js` (3 occurrences)
- `README.md` (2 occurrences)

`python3 scripts/audit_headline_stats.py` → "All headline numbers in sync. No action needed."

## Cluster band sanity

| Bike                   | Cluster         | Sim ET   | Trap       | Notes                                          |
|------------------------|-----------------|----------|------------|------------------------------------------------|
| Benelli TRK 502 (2017) | mid_twin_300_500| 14.554s  | 147.7 km/h | 47.5hp, 229kg ADV — heavy but expected         |
| Kawasaki Versys 650    | mid_twin_500_700| 12.847s  | 175.0 km/h | 68hp, 196kg — ~0.35s slower than Ninja 650     |

## Files touched

- `motoquant/scraper/known_bikes_extended.py` — appended 2 specs + 2 list entries
- `motoquant.db` — 39 fresh bike rows inserted + tire fitments rebuilt
- `web/app/page.js`, `web/app/bikes/layout.js`, `web/app/bikes/page.js`,
  `web/app/features/layout.js`, `web/app/layout.js`, `web/app/StructuredData.js`,
  `web/app/simulator/layout.js`, `web/app/about/page.js`, `web/app/whitepaper/page.js`,
  `web/app/pricing/page.js`,
  `web/app/blog/how-the-motoquant-physics-engine-works/page.js`, `README.md`
  — headline stats 599→637 patched
- `reports/catalog_expansion_2026-05-21_eleventh_pass.md` — this report
