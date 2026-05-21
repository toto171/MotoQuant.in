# Catalog Expansion Report — 2026-05-21 (Thursday — Tenth Pass)

## Bikes added (3)

1. **TVS NTorq 125 Race XP (2021-2026)** — India's top-spec performance scooter
   - 124.8cc liquid-cooled SOHC single (Revv X engine), 9.38 hp @ 7500 rpm / 10.5 Nm @ 6000 rpm
   - CVT (belt drive), 109 kg dry, 90/90-12 front + rear tires
   - Key: Only the second scooter in the catalog (after Yamaha Aerox 155 SE Asia); NTorq is the
     dominant Indian performance scooter segment (5 lakh+ units sold) — real drag presence
   - CVT modeled as 5 synthetic steps [2.800, 1.950, 1.400, 1.050, 0.900] + belt final drive;
     same convention as Yamaha Aerox 155 in this catalog
   - Cluster: entry_150_200 (sub-26hp; 9.4hp scooter)
   - **Smoke sim ET: 22.618s @ 101.5 km/h trap** — within the entry_150_200 slow band (documented
     +0.5-1.5s bias for small commuters; this is a 9.4hp scooter so 22s is physically expected)
   - Sources: TVS Motors press kit 2021 (tvsmotor.com), BikeWale verified spec sheet,
     BikeDekho NTorq Race XP review Oct 2021, MotorcycleDaily India first ride

2. **Bajaj Pulsar NS200 BS6 (2020-2026)** — BS6-compliant refresh of iconic 200cc naked
   - 199.5cc liquid-cooled DOHC triple-spark single, 24.17 hp @ 9750 rpm / 18.74 Nm @ 8000 rpm
   - 6-speed, F14/R43 520 chain, 148 kg dry; adds ABS + OBD-II vs BS4 predecessor
   - Only the 2017 and 2012 variants exist in the main catalog — the 2020 BS6 is distinct enough
     (ABS + FI recalibration + HSTC + OBD-II hardware adds ~3 kg and changes chassis character)
   - Cluster: entry_200_300 (24.5 PS, 200cc single)
   - **Smoke sim ET: 16.371s @ 133.7 km/h trap** — consistent with the entry_200_300 cluster band
     and matches the documented sim for the Suzuki V-Strom SX 250 (16.030s @ 133.7km/h) at
     a similar power/weight ratio but different configuration
   - Sources: Bajaj Auto BS6 press kit (bajajauto.com, Feb 2020), BikeDekho spec sheet (2020
     launch), BikeWale "Pulsar NS200 BS6 vs BS4" comparison, Bajaj service manual SB-NS200-2020

3. **Honda SP160 (2023-2026)** — Honda India's premium 160cc commuter with traction control
   - 163.7cc air-cooled SOHC single (PGM-FI), 13.48 hp @ 8500 rpm / 14.1 Nm @ 6000 rpm
   - 5-speed, F17/R45 428 chain, 137 kg dry; segment-first HSTC traction control
   - Fills a clear gap: Honda CB350 H'ness + CB300R + Unicorn 160 are in catalog but no SP160
   - Cluster: entry_150_200 (13.5hp, 163cc single)
   - **Smoke sim ET: 19.346s @ 112.1 km/h trap** — reasonable for a 13.5hp 160cc commuter;
     consistent with similar-class bikes in the entry_150_200 cluster
   - Sources: Honda India press release (hondamotorcycle.co.in, Jan 2023), BikeDekho SP160
     spec sheet, BikeWale SP160 vs Unicorn 160 BS6 comparison, Indian Autos Mag SP160
     road test (Apr 2023)

## Validation

- `python3 -m pytest tests/test_scraper.py` — **80 passed**, 0 failed, 569 deprecation
  warnings (pre-existing `datetime.utcnow()` usage in `spec.py:101` — not introduced here)
- All 3 new bikes pass `spec_from_dict` validator; finished_quarter=True; ETs in [4.0, 26.0]s;
  traps in [40, 400] km/h
- TVS NTorq CVT note: validator requires gears in [4, 7]; modeled with 5 synthetic CVT steps
  and `chain_pitch="belt"` + `final_drive="belt"` per the established Yamaha Aerox 155 convention
- **Reference baselines preserved EXACTLY: K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s,
  Δ +0.0000s on all three**

## Cluster band sanity

| Bike                 | Cluster        | Sim ET   | Trap      | Notes                                |
|----------------------|----------------|----------|-----------|--------------------------------------|
| TVS NTorq 125 RX     | entry_150_200  | 22.618s  | 101.5km/h | 9.4hp CVT scooter — upper end of band|
| Bajaj NS200 BS6      | entry_200_300  | 16.371s  | 133.7km/h | 24.5hp naked — mid-band              |
| Honda SP160          | entry_150_200  | 19.346s  | 112.1km/h | 13.5hp commuter — within band        |
