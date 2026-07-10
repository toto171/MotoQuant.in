# Catalog Web-Scrape — 2026-07-10

Full-catalog web-research corpus gathered by a 51-agent fan-out (operator request:
"scrape as much data as you can on our full bikes, parts and tyres library").
**Read-only data collection** — nothing in `motoquant.db`, the seed sources, or the
physics was modified. This directory is the input for a follow-up update pass.

Honest-data rules enforced on every agent: no fabrication; every price/benchmark
carries its exact source URL; source types labeled honestly (`instrumented` /
`magazine` / `aggregator` / `forum_or_timeslip` / `estimate`); `found=false` /
`not_found` preferred over guessing.

## Coverage

| Track | Catalog | Researched | File |
|---|---|---|---|
| Bikes | 541 | **541 (100%)** | `bikes_web_data.json` |
| Parts | 593 | **593 (100%)** | `parts_web_data.json` |
| Tire families | 120 (254 rows) | **120 (100%)** | `tires_web_data.json` |

## Bikes — spec verification + benchmark hunt

- **214 spec discrepancies** flagged across 168 bikes (60 high-confidence). By field: peak_power_hp x70, dry_mass_kg x64, peak_torque_nm x49, wet_mass_kg x23, displacement_cc x8.
- **103 new benchmark data points**: 67 quarter-mile (20 instrumented, 24 magazine), 13 top-speed, 23 0-100. The existing sweep corpus covers ~258 of 541 bikes; these finds target the uncovered tail.

### Instrumented quarter-mile finds (strongest candidates for the benchmark corpus)

| Bike | ET (s) | Trap (km/h) | Source |
|---|---|---|---|
| BMW M 1000 R (2023-2026) (id 129) | 9.8 | — | [MCN (Motorcycle News) dragstrip test](https://www.youtube.com/watch?v=C1RkmqCOhWg) |
| Ducati 1299 Panigale (id 57) | 10.17 | 246.2 | [Motostatz acceleration/top-speed data](https://motostatz.com/15-17-ducati-1299-panigale-acceleration/) |
| Ducati DesertX (id 707) | 11.84 | 177.8 | [Motostatz GPS-timed quarter mile test](https://motostatz.com/ducati-desertx-top-speed-acceleration/) |
| Harley-Davidson V-Rod Muscle (2009-2017) (id 103) | 11.875 | 183.7 | [Rider Magazine road test (Feb 2009 issue) — timed runs at Infineon Raceway dragstrip](https://ridermagazine.com/2009/01/12/2009-harley-davidson-v-rod-muscle-road-test/) |
| Honda CB500F (2019-2026) (id 201) | 13.36 | 157.7 | [MotoStatz GPS test](https://motostatz.com/honda-cb500f-acceleration-top-speed/) |
| Indian FTR 1200 S (2019-2024) (id 105) | 11.2 | 193.08 | [MotoStatz GPS acceleration test](https://motostatz.com/indian-ftr-1200-acceleration-top-speed-review/) |
| KTM Duke 200 (2017-2023) (id 65) | 16.1 | 125.5 | [MotoStatz GPS test](https://motostatz.com/ktm-200-duke-top-speed-acceleration/) |
| KTM Duke 390 (2017-2023) (id 66) | 13.3 | 154.98 | [MotoStatz GPS test](https://motostatz.com/ktm-390-duke-acceleration/) |
| KTM RC 390 (2022-2024) (id 67) | 13.13 | 159.29 | [MotoStatz GPS test (43 crank hp / 42 rwhp variant)](https://motostatz.com/ktm-rc-390-top-speed-and-acceleration/) |
| Kawasaki Ninja 300 (2013-2024) (id 87) | 14.1 | 149.64 | [MotoStatz GPS test](https://motostatz.com/kawasaki-ninja-300-acceleration/) |
| Kawasaki Ninja 400 (2018-2024) (id 88) | 12.98 | 164.12 | [MotoStatz GPS test](https://motostatz.com/kawasaki-ninja-400-acceleration/) |
| Kawasaki Vulcan S (2015-2026) (id 118) | 13.03 | 165.8 | [MotoStatz Vulcan S acceleration & top speed review (GPS test)](https://motostatz.com/kawasaki-vulcan-s-acceleration-top-speed-review/) |
| Suzuki Hayabusa (2021-2024, Gen3) (id 12) | 8.97 | 260.7 | [MCN (Motorcycle News UK) launch test, Sywell Aerodrome](https://www.motorcyclenews.com/bike-reviews/suzuki/gsx1300r-hayabusa/2021/) |
| Suzuki SV650 (2016-2026) (id 119) | 11.82 | 185 | [MotoStatz - Suzuki SV650 Acceleration](https://motostatz.com/suzuki-sv650-acceleration/) |
| Yamaha VMAX 1200 (1985-2007) (id 4611) | 10.64 | 206.9 | [Cycle World, May 1985 ("How Fast Will It Go...Really?")](https://magazine.cycleworld.com/article/1985/5/1/how-fast-will-it-goreally) |
| Yamaha VMAX 1700 (2009-2020) (id 112) | 10.26 | 218.5 | [Cycle World test of the 2009 VMAX](https://www.cycleworld.com/2010/06/14/comparison-vmax-vs-3max/) |
| Yamaha XSR700 (2018-2024) (id 694) | 12.22 | 172.2 | [MotoStatz straight-line performance test](https://motostatz.com/yamaha-xsr700-engine-and-straight-line-performance-review/) |
| Yamaha YZF-R1 (2004-2006) (id 16) | 10.31 | 231.7 | [MotoStatz GPS test (04-06 YZF-R1)](https://motostatz.com/04-06-yamaha-yzf-r1-top-speed-acceleration/) |
| Yamaha YZF-R3 (2015-2022) (id 152) | 14 | 152.9 | [MotoStatz GPS test](https://motostatz.com/yamaha-yzf-r3-acceleration/) |
| Yamaha YZF-R7 (2022-2026) (id 110) | 11.64 | 186.7 | [MotoStatz GPS test](https://motostatz.com/yamaha-yzf-r7-top-speed-acceleration/) |

### High-confidence spec discrepancies (sample — full list in JSON)

| Bike | Field | DB | Web | Source |
|---|---|---|---|---|
| Kawasaki Z900 (2020-2024) (id 47) | wet_mass_kg | None | 212 | [www.cycleworld.com](https://www.cycleworld.com/story/buyers-guide/2020-kawasaki-z900/) |
| Bajaj Dominar 400 (2019-2024) (id 72) | wet_mass_kg | None | 193 | [www.zigwheels.com](https://www.zigwheels.com/bajaj-bikes/2019-2024-dominar-400/specifications/) |
| Bajaj Dominar 250 (2020-2024) (id 73) | wet_mass_kg | None | 180 | [www.bajajauto.com](https://www.bajajauto.com/bikes/dominar/dominar-250/specifications) |
| BMW R 1250 GS (2019-2025) (id 128) | wet_mass_kg | None | 249 | [www.zigwheels.com](https://www.zigwheels.com/bmw-bikes/r-1250-gs/specifications/) |
| Honda CRF1100L Africa Twin (2020-2026) (id 202) | wet_mass_kg | None | 226 | [www.adventurebikerider.com](https://www.adventurebikerider.com/article/honda-africa-twin-and-africa-twin-adventure-sports/) |
| BMW R nineT (2014-2023) (id 226) | wet_mass_kg | None | 222 | [ridermagazine.com](https://ridermagazine.com/2014/08/29/2014-bmw-r-ninet-road-test/) |
| Moto Guzzi V85 TT (2019-2026) (id 252) | wet_mass_kg | None | 229 | [www.advpulse.com](https://www.advpulse.com/adv-bikes/moto-guzzi-v85-tt-specs/) |
| Aprilia RSV4 1100 Factory FW1A (2025-2026) (id 331) | wet_mass_kg | None | 204 | [www.motoplanete.us](https://www.motoplanete.us/aprilia/11176/RSV4-1100-Factory-2025/contact.html) |
| Kawasaki Versys-X 300 (2017-2024) (id 730) | wet_mass_kg | None | 175 | [www.kawasaki.com](https://www.kawasaki.com/en-us/motorcycle/versys/adventure-touring/versys-x-300/2026-versys-x-300-abs) |
| Honda CRF1100L Africa Twin Adventure Sports (2020-2026) (id 766) | wet_mass_kg | None | 238 | [www.adventurebikerider.com](https://www.adventurebikerider.com/article/honda-africa-twin-and-africa-twin-adventure-sports/) |
| BMW K1600 GT (2022-2026) (id 798) | wet_mass_kg | None | 343 | [www.bennetts.co.uk](https://www.bennetts.co.uk/bikesocial/reviews/bikes/bmw/k1600-gt-gtl-bagger-grand-america-2022-review) |
| Kawasaki W230 (2024-2026) (id 4090) | wet_mass_kg | None | 143 | [www.kawasaki.com](https://www.kawasaki.com/en-us/motorcycle/w/retro-classic/w230) |
| Yamaha YZF-R9 (2025) (id 294) | peak_power_hp | 168 | 117.4 | [www.moto-data.net](https://www.moto-data.net/yamaha/yzf-r9-2025) |
| Honda RC213V-S (2015-2016) (id 333) | peak_power_hp | 215 | 159 | [www.motorcyclenews.com](https://www.motorcyclenews.com/bike-reviews/honda/rc213v-s/2015/) |
| Triumph Speed Twin 900 (2019-2024) (id 91) | peak_torque_nm | 65.6 | 80 | [www.triumphmotorcycles.com](https://www.triumphmotorcycles.com/for-the-ride/news/motorcycles/speed-twin-900-your-questions-our-answers) |
| KTM 890 SMT (2023-2026) (id 765) | dry_mass_kg | 163 | 194 | [www.mcnews.com.au](https://www.mcnews.com.au/2023-ktm-890-smt-specifications/) |
| Honda X-Blade 160 (2018-2024) (id 350) | peak_power_hp | 17 | 13.8 | [www.bikedekho.com](https://www.bikedekho.com/honda/xblade) |
| Indian Pursuit Dark Horse (2024-2025) (id 303) | peak_torque_nm | 211 | 174 | [www.autoevolution.com](https://www.autoevolution.com/moto/indian-pursuit-powerplus-dark-horse-108-2025.html) |
| Kawasaki Z H2 SE (2024-2025) (id 299) | peak_power_hp | 239 | 197.3 | [www.cycleworld.com](https://www.cycleworld.com/kawasaki/ninja-z-h2-se-abs/) |
| Hero Xtreme 250R (2024-2025) (id 348) | peak_power_hp | 25.31 | 29.6 | [www.heromotocorp.com](https://www.heromotocorp.com/en-in/motorcycles/Xtreme-250r.html) |
| Honda CBR900RR (1998-1999) (id 320) | peak_power_hp | 152 | 130 | [www.autoevolution.com](https://www.autoevolution.com/moto/honda-cbr-900-rr-fireblade-1998.html) |
| Triumph Tiger 900 Rally (2020-2026) (id 127) | dry_mass_kg | 228 | 196 | [bikez.com](https://bikez.com/motorcycles/triumph_tiger_900_rally_2020.php) |
| Honda RC30 (VFR750R) (1988-1992) (id 324) | dry_mass_kg | 215 | 185 | [en.wikipedia.org](https://en.wikipedia.org/wiki/Honda_VFR750R) |
| Triumph Speed T4 (2024-2026) (id 696) | peak_torque_nm | 36 | 31 | [www.triumphmotorcycles.in](https://www.triumphmotorcycles.in/motorcycles/classic/speed-t4/specification) |
| Hero Xtreme 250R (2024-2025) (id 348) | peak_torque_nm | 22 | 25 | [www.heromotocorp.com](https://www.heromotocorp.com/en-in/motorcycles/Xtreme-250r.html) |

## Parts — pricing refresh + SKU audit

- **289/593 parts priced from live listings** (72 INR India-retail, 217 USD-only — feed these through the `pricing_refresh.estimate_landing_cost_inr` landed-cost formula).
- **54 parts moved >15% vs DB price** (INR-vs-INR comparisons only).
- **191 parts flagged `sku_exists: low`** — no evidence the exact product exists as named. Heaviest brands: Regina Pro x9, Sprocket Specialists x8, SC-Project x8, ClutchCo x8, Two Brothers Racing x4, GPR x3, Arrow x3, K-Tech x3. Many look like formula-generated seed entries (fictional variant names on real brands, or fully fictional brands like ClutchCo / Regina Pro / Sprocket Specialists / Schnitzer swingarms). Recommend a triage pass: rename to honest class names (per the July-6 P183/P194/P195/P501 precedent) or replace with verified SKUs.
- **6 discontinued**: Bazzaz ZFi Fuel Controller Quickshift Unit (id 51); Bazzaz Quick Shift Fuel Control (id 95); Bazzaz ZFi Standalone Fuel Management (id 116); AEM Infinity Fuel Management (id 146); Bazzaz Z-Fi Piggyback ECU (id 407); Bazzaz Z-Fi Fuel Controller Suzuki Hayabusa (1299cc) (id 504).

### Largest INR price moves (>15%)

| Part | Category | DB ₹ | Web ₹ | Δ | Source |
|---|---|---|---|---|---|
| EBC HH Sintered Brake Pads Front Ducati Panigale V4R (1103cc) (id 527) | brakes | 3,800 | 24,000 | +532% | [www.motomillion.com](https://www.motomillion.com/products/ebc-double-h-sintered-front-brake-pads-for-panigale-v4-v4s-v4r) |
| YSS Rear Shock Absorber Yamaha R15 V4 (155cc) (id 513) | suspension | 14,000 | 49,000 | +250% | [www.indiamart.com](https://www.indiamart.com/proddetail/yamaha-yzf-r15-racing-2017-2023-yss-shock-absorber-2855455877230.html) |
| Rapid Bike EVO Fuel Injection Controller (id 54) | ecu | 18,000 | 48,500 | +169% | [bikegear.in](https://bikegear.in/rapid-bike-evo-fuel-management-module-yamaha-krbevo-098-online-india) |
| Rapid Bike EVO EFI Tuning Module (id 115) | ecu | 18,000 | 48,500 | +169% | [bikegear.in](https://bikegear.in/rapid-bike-evo-fuel-management-module-yamaha-krbevo-098-online-india) |
| Rapid Bike Evo Piggyback (id 410) | ecu | 18,000 | 48,500 | +169% | [motopoto.com](https://motopoto.com/products/rapidbike-module-for-kawasaki-z900-2017) |
| Öhlins STX Rear Shock (id 104) | suspension | 55,000 | 145,000 | +164% | [bikegear.in](https://bikegear.in/ohlins-stx-36-twin-shock-indian-in-524-online-india) |
| K&N Air Filter Honda CB300R (286cc) (id 489) | air_filter | 3,500 | 8,290 | +137% | [www.motoplanetdelhi.com](https://www.motoplanetdelhi.com/knha2819highflowairfilter/pid-2226711344) |
| S&S Cycle Grand National Slip-On RE 650 (id 248) | exhaust | 38,500 | 90,000 | +134% | [shop.bmwmcgr.com](https://shop.bmwmcgr.com/products/royal-enfield-s-s-slip-on-for-650-twins) |
| Öhlins Rear Shock Yamaha YZF-R1 (998cc) (id 516) | suspension | 85,000 | 186,115 | +119% | [bikegear.in](https://bikegear.in/ohlins-ttx-gp-shock-absorber-yamaha-ya-468-online-india) |
| K&N Air Filter Yamaha R15 V4 (155cc) (id 483) | air_filter | 3,200 | 6,790 | +112% | [www.store4riders.com](https://www.store4riders.com/k-n-bike-air-filter-for-yamaha-r15-v2-v3-v4.html) |
| Yosh R-77 600cc Slip-On (id 190) | exhaust | 45,000 | 2,800 | -94% | [www.indiamart.com](https://www.indiamart.com/proddetail/r-77-yoshimura-bike-exhaust-26502977112.html) |
| MWR Pro Filter KTM 390 / Husqvarna 401 (id 356) | air_filter | 4,200 | 7,990 | +90% | [motopoto.com](https://motopoto.com/products/mc-050-15) |
| Race Dynamics RD Duke 390 ECU Tune (id 123) | ecu | 11,000 | 19,500 | +77% | [lrlmotors.com](https://lrlmotors.com/products/powertronic-ktm-duke-390-2020) |
| Diamond Chain 428 Rear Sprocket 45T Small-cc (id 498) | sprocket | 1,800 | 500 | -72% | [dir.indiamart.com](https://dir.indiamart.com/impcat/motorcycle-sprocket.html) |
| Power Commander V Kawasaki ZX-10R (998cc) (id 509) | ecu | 58,000 | 17,800 | -69% | [superbikestore.in](https://superbikestore.in/products/dynojet-power-commander-v-for-kawasaki-zx-10r-2016-20) |
| Rapid Bike Racing Piggyback (id 411) | ecu | 35,000 | 57,990 | +66% | [motopoto.com](https://motopoto.com/collections/rapidbike) |
| Generic Universal Frame Sliders Kit (id 293) | bodywork | 4,000 | 1,424 | -64% | [www.amazon.in](https://www.amazon.in/Frame-Slider/s?k=Frame+Slider) |
| EBC HH Sintered Brake Pads Front Yamaha R15 V4 (155cc) (id 522) | brakes | 1,800 | 2,899 | +61% | [lrlmotors.com](https://lrlmotors.com/products/yamaha-r15-v3-ebc-doubel-sintered-brake-pads-front) |
| Generic Universal DOT-4 Brake Fluid Premium (id 296) | brakes | 800 | 317 | -60% | [www.amazon.in](https://www.amazon.in/LIQUI-3091-Motorbike-Brake-Fluid/dp/B00LH5BK9M) |
| DNA Air Filter Yamaha YZF-R1 (998cc) (id 486) | air_filter | 8,900 | 13,699 | +54% | [motocentral.in](https://motocentral.in/products/dna-air-filter-for-yamaha-r1-r1s-r1m-1000-series-15-22-p-y10s15-0r-yma-r1) |
| Leo Vince LV-10 1000cc Slip-On (id 177) | exhaust | 72,000 | 35,000 | -51% | [superbikestore.in](https://superbikestore.in/products/leovince-lv-10-slip-on-exhaust-for-suzuki-gsxr-1000) |
| Walbro 450 LPH Fuel Pump (id 144) | fuel_system | 15,000 | 22,063 | +47% | [www.amazon.in](https://www.amazon.in/Walbro-F90000274-Universal-Pressure-Version/dp/B07D3VFRXK) |
| HEL Braided Lines Small-CC (id 377) | brakes | 7,500 | 10,990 | +47% | [n1-racing.com](https://n1-racing.com/collections/hel) |
| Brembo Sintered Brake Pads Front Royal Enfield Interceptor 650 (650cc) (id 529) | brakes | 2,800 | 1,499 | -46% | [www.indiamart.com](https://www.indiamart.com/proddetail/royal-enfield-interceptor-continental-650-sintered-brake-pads-23502157697.html) |
| JT Sprockets 530 Rear Sprocket 44T (id 27) | sprocket | 5,200 | 2,800 | -46% | [ridersjunction.com](https://ridersjunction.com/products/sprockets-rear-890-45t-jt-jtr890-45) |

## Tires — family status + India pricing

- Status: **95 current / 8 discontinued / 16 not found / 1 unknown**; 62 families carry live prices (95 price points).

### Discontinued families (catalog carries these as current)

| Family | Rows | Successor | Notes |
|---|---|---|---|
| Avon Roadrunner AM26 | ids 221,222 | Avon Roadrider MkII | MODEL NAME WRONG: AM26 is the 'Roadrider', not 'Roadrunner'. The AM26 Roadrider is no longer made (forum + retailer confirmation: https://ww |
| Continental ContiRaceAttack Comp Soft | ids 188 | ContiRaceAttack 2 (Soft/Medium) | Continental's current race-tire lineup is ContiRaceAttack 2 (soft/medium) and ContiRaceAttack 2 Street; multiple sources (continental-tires. |
| Dunlop American Elite | ids 237,240 | Dunlop American Elite 2 (AE2) | Multiple sources (roadglide.org forum, tuckerspeed.com, triketalk.com) confirm Dunlop has discontinued the original USA-made American Elite  |
| Metzeler Racetec RR K2 | ids 16 | Racetec RR K3 | Metzeler's Racetec RR line uses per-size compound-generation suffixes (K1/K2/K3). Official metzeler.com and current retailers (torqueblock.c |
| Michelin Pilot Activ | ids 208,225 | — | Pilot Activ is no longer listed on Michelin's official site (michelinman.com) and could not be found as a current product on any Indian reta |
| Michelin Pilot Power 3 | ids 4,72,80,177 | Michelin Power RS (intermediate), superseded again by Michelin Power 5 | Pilot Power 3 is an older-generation Michelin sport tire, discontinued at the manufacturer level and replaced first by Power RS (also now go |
| Pirelli Diablo | ids 150,156,157,158,159,160 | Diablo Rosso (sport-size range); Diablo Powercruiser (cruiser/muscle sizes such as 240/40ZR18) | Pirelli press materials confirm the original 'Diablo' sport line was replaced by 'Diablo Rosso' in 2008; Pirelli's current official catalogu |
| Pirelli Diablo Supercorsa SC1 | ids 7,97,164 | Diablo Supercorsa V3 (current generation; lineage moved SC → SC2 → V2 → V3) | Pirelli's own product page ('DIABLO Supercorsa V3 SC New') and multiple India retailers confirm the Supercorsa line has moved on through SC  |

### Not-found families (verify naming or drop)

- **CEAT Zoom Sport** (ids 22,184) — No CEAT product named 'Zoom Sport' exists - the Zoom family is Zoom / Zoom Plus / Zoom Rad X1 / Zoom Cruz (ceat.com Zoom listing: https://www.ceat.com/bike-tyre
- **Continental ConmiTour** (ids 238) — No Continental tire named 'ConmiTour' exists - name appears garbled. Continental's road products in 180/55ZR17 are Conti Motion / ContiRoadAttack 4 (e.g. https:
- **Continental Conti Twins** (ids 206) — 'ContiTwins' is a real Continental line but it is a vintage/classic-bike tire family (RB2/K112 style, inch and small metric vintage sizes) - it is NOT made in 1
- **Dunlop KR461 Race** (ids 194) — No evidence 'Dunlop KR461' exists anywhere in Dunlop's racing catalog (checked dunlopracing.com, dunlopmotorcycletires.com, and retailer listings). Dunlop's act
- **FDR Sportmax** (ids 99,100,113,114,115,117,118,122,124) — No evidence of an 'FDR Sportmax' product exists. 'Sportmax' is a Dunlop trademark (Dunlop Sportmax line); FDR's actual sport-oriented tire is called 'FDR Sport 
- **M&H Racemaster 5.5/18** (ids 165) — Could not find any M&H Racemaster motorcycle drag slick listed in a '5.5/18' (tread-width/rim) size — confirmed real sizes in the line are 4.0/26.6-18, 5.0/26.0
- **M&H Racemaster 6.0/18** (ids 215) — No '6.0/18' size found in M&H's published motorcycle drag slick catalog; closest confirmed size is 6.0/26.0-15 (mandhtires.com/6.0-26.0-15-Motorcycle-Drag-Slick
- **Maxxis Insane** (ids 161) — No evidence a 'Maxxis Insane' motorcycle tyre exists. Not found on maxxis.com (US), maxxis-europe.com, maxxis.com.ph, or maxxistyres.co.in (India), nor on any r
- **Mickey Thompson ET Drag R** (ids 54) — FLAG: size 26x10.5R15 and the 'ET Drag R' naming both trace to Mickey Thompson's AUTOMOTIVE drag-radial catalog (ET Street R bias tire, e.g. 'Mach-E ET Street R
- **Mickey Thompson ET Street SS 29.0x10.5R18** (ids 26) — FLAG: size 295/35R18 matches Mickey Thompson's automotive Street Comp / ET Street S/S radial line for cars (e.g. 'Mickey Thompson Street Comp 295/35R18', part# 
- **MRF Revz EF1 Drag** (ids 21,185) — No 'EF1' variant exists anywhere in MRF's Revz lineup. Confirmed real Revz sub-variants (via mrftyres.com official product pages): Revz, Revz S, Revz C, Revz C1
- **MRF Revz FB** (ids 20) — No 'FB' designation found anywhere in MRF's Revz range on mrftyres.com or Indian retailers (tyremarket.com, tyres.cardekho.com, tyreplex.com, Flipkart, IndiaMAR
- **OE Bias-Ply OE Bias-Ply 3.25-16** (ids 262) — 'OE Bias-Ply' is not an identifiable tire manufacturer/brand -- appears to be a generic placeholder in our catalog representing typical original-equipment bias-
- **OE Bias-Ply OE Bias-Ply 3.25-19** (ids 260) — Same issue as the other 'OE Bias-Ply' entries -- not a real manufacturer/brand, appears to be a generic vintage-OEM-sizing placeholder (90/90-19 front). Coker T
- **OE Bias-Ply OE Bias-Ply 4.00-18** (ids 261) — Same issue as the other 'OE Bias-Ply' entries -- not a real manufacturer/brand, generic vintage-OEM-sizing placeholder (110/90-18 rear). Coker Tire's 'Indian Sc
- **Shinko Stealth R265 Drag** (ids 27,189) — Could NOT find any evidence a Shinko tire named/coded 'R265' or 'Stealth R265' exists — searches of Shinko's own site (shinkotireusa.com) and general web turned

## How to consume (the update pass)

1. **Benchmarks**: add the instrumented + strong magazine quarter-mile rows to `scripts/validation_sweep.py` BENCHMARKS (respect the honest-data weighting: instrumented=1.0, magazine=0.7, aggregator=0.5, forum=0.3). Re-run the weighted sweep before/after; baselines K5/R1/Hayabusa must stay bit-identical.
2. **Bike specs**: triage `spec_checks` high-confidence rows against `known_bikes*.py` sources; fixes go in the spec source (not the DB) followed by the standard reseed chain + golden/surrogate regen.
3. **Parts prices**: apply INR prices directly (stamp `last_price_check=2026-07-10`); USD-only through the landed-cost formula; `sku_exists: low` entries need the honesty triage before repricing.
4. **Tires**: mark discontinued families (keep rows for historical fitments, flag availability), update `price_inr`/`available_india` from the price points.

Raw journals with full agent transcripts live in the session workspace; the JSON files here are the durable artifact.
