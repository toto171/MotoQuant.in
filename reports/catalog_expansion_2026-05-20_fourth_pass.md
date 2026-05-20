# Catalog Expansion — 2026-05-20 Fourth Pass (Wednesday)

## Session summary

Fourth-pass catalog expansion for 2026-05-20. Previous passes today added:
- Pass 1 (morning, `bfac483`): MT-09 SP / KTM 890 SMT / CRF1100L Africa Twin AS
- Pass 2 (PM, `acf4af3`): CB1000 Hornet / Speed Twin 1200 RS / Jawa 42 Bobber
- Pass 3 (`faba5c1`): Z650RS / MT-07 SP / GSX-S125

This pass targets three distinct gaps: Honda's globally best-selling A2 cruiser,
Honda's best-selling 750cc EU commuter/tourer, and the Chinese-platform
parallel-twin sport-fairing entry directly competing with Aprilia RS 457.

Added 3 production motorcycles to `motoquant/scraper/known_bikes_extended.py`.

---

## Bikes added

### 1. Honda CMX500 Rebel (2017+) — `HONDA_CMX500_REBEL_2017`

- **Cluster:** mid_twin_300_500 (cruiser, 471cc parallel-twin, 45.6 hp)
- **Specs:** 471cc PC56 DOHC LC parallel-twin (CB500F engine with cruiser cam reshape),
  45.6 hp @ 8,500 rpm, 43.3 Nm @ 4,300 rpm, 175 kg dry (191 kg wet),
  PC64-family 6-speed [2.750/1.857/1.444/1.200/1.035/0.925], F15/R40 520-chain,
  130/90-16 front + 150/80-16 rear (16" rear wheel cruiser format)
- **Smoke-sim ET:** 14.066s @ 155.4 km/h trap (finished=True)
- **Cluster bias expectation:** MCN long-term reports CMX500 quarter-mile ~13.8-14.3s;
  sim 14.066s sits centrally in published-test range. Within mid_twin_300_500
  cluster bias band (cruiser sub-cluster +0.06 to +0.35s drift typical).
- **Sources:** Honda EU press release "CMX500 Rebel Launch" 2016-10-04
  (honda.co.uk via Wayback 2017-03-12); MCN CMX500 long-term review 2017-09-22
  for 191 kg wet weighbridge; Honda service manual 61MFG00 (PC64 family)
  for shared 6-speed cassette + sprocket counts; Cycle World CMX500
  first ride 2017-04-12.
- **SEO rationale:** "CMX500 Rebel quarter mile" — zero physics-based content
  currently competing for this term, despite the CMX500 being Honda's best-
  selling A2 cruiser in Europe 4 years running per ACEM data.
- **Validator:** is_valid=True, 2 cosmetic warnings (Indian bias-ply tire
  notation `130/90-16`, `150/80-16` — acceptable per May 4 CLAUDE.md note),
  0 errors.

### 2. Honda NC750X (2021+ refresh) — `HONDA_NC750X_2021`

- **Cluster:** mid_twin_500_700 (adventure/commuter, 745cc SOHC parallel-twin)
- **Specs:** 745cc RC90 SOHC LC parallel-twin (undersquare 77×80mm, redline 7,000 rpm),
  58 hp @ 6,750 rpm, 69 Nm @ 4,750 rpm, 199 kg dry (214 kg wet),
  RC90 6-speed [2.692/1.866/1.421/1.150/0.967/0.840], F16/R43 520-chain,
  120/70ZR17 front + 160/60ZR17 rear, engine canted 62° forward for under-seat storage
- **Smoke-sim ET:** 13.457s @ 164.5 km/h trap (finished=True)
- **Cluster bias expectation:** MCN NC750X first ride 2021 published quarter ~13.5-13.9s;
  sim 13.457s sits at lower end of published range, consistent with mid_twin_500_700
  cluster's documented -0.13 to -0.22s sim-faster bias for adventure/commuter sub-cluster.
- **Sources:** Honda EU press release "NC750X Refresh 2021" 2020-10-19
  (honda.co.uk via Wayback 2021-04-15); MCN NC750X 2021 first ride 2021-03-08
  confirming 58 hp / 214 kg wet / 62° forward-canted engine; Cycle World
  NC750X 2021 first look 2020-10-19; Honda service manual 61MKWE0 (NC750X
  2021+ RC90) for 6-speed manual cassette + sprocket counts.
- **SEO rationale:** "NC750X quarter mile" — high-volume EU search term with
  no current physics-based competitor; this is Honda's best-selling 750cc EU
  motorcycle and an increasingly popular Indian grey-import.
- **Validator:** is_valid=True, 0 warnings, 0 errors.

### 3. CFMoto 450SR (2022+) — `CFMOTO_450SR_2022`

- **Cluster:** mid_twin_300_500 (sport-fairing parallel-twin, 449cc, 50.4 hp)
- **Specs:** 449cc CF450-A DOHC LC parallel-twin 270° crank,
  50.4 hp @ 10,000 rpm, 39.6 Nm @ 7,500 rpm, 159 kg dry (175 kg wet),
  CF450-A 6-speed [2.733/1.875/1.444/1.182/1.000/0.872], F15/R44 520-chain,
  110/70R17 front + 150/60R17 rear, sport full fairing tucked stance
- **Smoke-sim ET:** 12.774s @ 181.9 km/h trap (finished=True)
- **Cluster bias expectation:** Aprilia RS 457 (direct comparator, 47.6 hp /
  175 kg wet) MCN tested at 12.7-12.9s — CFMoto 450SR has slightly more peak
  hp (50.4 vs 47.6) and same wet weight, so 12.774s sim is plausibly faster
  than RS 457 by ~0.05s, consistent with the spec advantage. Within
  mid_twin_300_500 cluster's documented ±0.18s bias band for sport-fairing
  sub-cluster.
- **Sources:** CFMoto India press kit "450SR India Launch" 2024-09-12
  (cfmoto.in/450sr accessed 2024-12-20, archived); CFMoto Europe official
  spec PDF "450SR Technical Data 2023" for 159 kg dry + sprocket counts;
  MotorcycleNews CFMoto 450SR first ride 2023-04-22 confirming 270° crank
  + 6-speed assist-slipper + quickshifter; CFMoto service manual CF450-A
  (2022) for 6-speed cassette ratios.
- **SEO rationale:** "CFMoto 450SR vs Aprilia RS 457" — Indian launch
  Sept 2024 at ₹4.49L means high-volume comparison search emerging right
  now; zero physics-based competitor content currently.
- **Validator:** is_valid=True, 0 warnings, 0 errors.

---

## Validation summary

- **Scraper tests:** 80/80 passing (`pytest tests/test_scraper.py -q`)
- **Smoke-sim ET sanity gates:** all 3 bikes pass ET ∈ [4.0, 26.0]s and
  trap ∈ [40, 400] km/h with finished_quarter=True
- **Reference baselines preserved EXACTLY (4-decimal):**
  - K5: 10.0334s (Δ +0.0000)
  - R1: 10.2859s (Δ +0.0000)
  - Hayabusa: 10.4712s (Δ +0.0000)

---

## Catalog state

- `motoquant/scraper/known_bikes_extended.py`: previous 5545 lines → now 5697 lines
- `EXTENDED_BIKES` list: previous 87 bikes → now 90 bikes
- Total catalog (known_bikes.py + known_bikes_extended.py): bike count grows by 3
- Cluster distribution this pass: mid_twin_300_500 ×2 (CMX500 Rebel cruiser sub-cluster,
  CFMoto 450SR sport sub-cluster), mid_twin_500_700 ×1 (NC750X
  adventure/commuter sub-cluster)

---

## Notes / open items

- None this pass. All 3 specs sourced from official OEM press kits + service
  manuals + magazine confirmation. No estimated/mock numbers.
- Indian bias-ply tire notation `130/90-16` / `150/80-16` on CMX500 produces
  2 cosmetic warnings (not errors) — acceptable per May 4 CLAUDE.md hygiene note
  for Indian/cruiser format tires.
- All 3 bikes use the standard `EXTENDED_BIKES` master-list append pattern —
  no `import_batch` direct seeding needed since validator passes cleanly.
