# MotoQuant Pro — Competitive Landscape

Tracking competitors, adjacent products, and market signals. Updated weekly by the `competitive-intel` agent.

---

## 2026-05-26 — Week scan

### Direct competitors (motorcycle drag/ET tools)

| Name | URL | Category | Threat | Notes |
|---|---|---|---|---|
| DragSim5 (Motion Software) | proracingsim.com / motionsoftware.com | Desktop sim, paid (~$200+) | **Low-medium** | Closest functional analogue: simulates auto/dragster/motorcycle with FWD/RWD physics, gear-ratio optimisation, shift-point tuning. Windows-only legacy product, no India focus, no INR pricing, no Indian bike catalog. Their feature table reads as pro-tier but UI is 2000s-era. Our angle: web-native, 342-bike pre-configured Indian catalog, validated benchmarks. |
| DragCalc | dragcalc.com | Web calculator, free | **Low** | Markets itself as "physics-based" with tire models + weight transfer, but inputs are still power/weight/CdA — no per-bike preset. |
| Wallace Racing | wallaceracing.com | Web calculators, free | **Low** | Aging tools, simple HP/weight formulas. SEO-strong on legacy keywords. |
| XCceleration | xcceleration.com/et.calculator.html | Web calculator, free | **Low** | Single-formula tool. Often top-3 on "1/4 mile ET" SERPs. |
| Rob Robinette | robrobinette.com/et.htm | Web calculator, free | **Low** | Classic personal site, ranks well for HP→ET. |
| Speedmaster | speedmaster79.com/tools/14et-hp | Web calculator, free | **Low** | OEM-parts-vendor lead-gen tool. |
| AJ Designer | ajdesigner.com | Web calculator, free | **Low** | Power-from-ET reverse calc. |
| FIRGELLI Engineering | firgelliauto.com (blog tool) | Web calculator, free | **Low** | Recent entrant; SEO-aggressive blog format with "interactive tool + diagram + worked examples". Note the content pattern — worth mirroring. |

**Takeaway:** Generic calculators dominate SERPs but none offer per-bike physics, INR pricing, Indian-venue density-altitude, or parts ROI. MotoQuant's published "physics-based, validated against 90 benchmarks, 342 bikes" positioning per `data/seo_opportunities.json` remains defensible.

### Indirect / adjacent products

| Name | What it is | Threat | Notes |
|---|---|---|---|
| LeanGP | Home motorcycle riding simulator (hardware + sim) | Low | Different category (rider training, MotoGP-style lean dynamics). Not drag-focused. No overlap. |
| Indian Bikes Driving 3D (Rohit Gaming Studio) | Mobile arcade game | **None** | Different audience entirely; surfaced in our India query as SEO noise. |
| Ultraviolette F99 (manufacturer-side telemetry) | EV maker publishing Valley Run timing | Low-medium | F99 hit 10.712s at Valley Run 2024 (fastest Indian-manufacturer ET). They control the bike → telemetry → press loop in-house. If they publish a "configure your F99" web tool, that's a direct competitor for the EV slice. Not seen yet. |

### Indian moto-drag scene signals

- **Valley Run 2026 Summer** ran April 3-5 at Aamby Valley Airstrip (eliteoctane.com). Search SERPs are still mostly 2024 coverage — actual 2026 results haven't been widely indexed yet. Opportunity: if the 2026 results page lands, our `/simulator?venue=aamby-valley` should rank near it.
- **Generation Speed** (generationspeed.com) — India's motoring festival, broader audience. Not a tool competitor.
- **Autocar India "Aces of Speed"** content series — magazine-tier authority, top SERP for "hayabusa quarter mile india". Not a tool, but they're the discovery layer for our target audience.

### Adjacent / no-competitor categories (confirmed gaps)

- **No India-built motorcycle drag-physics simulator** turned up in the scan. The closest analogue (DragSim5) is desktop-only, dollar-priced, and English-language with US-market parts catalog.
- **No "ask AI to tune my bike for Aamby Valley" tool** exists publicly. Our /api/chat + ParsedSimRequest stack remains differentiated.
- **No INR-denominated parts ROI calculator for motorcycles** observed. Adjacent: Indian e-commerce part stores (Motousher, Powerteq, Riderzplanet, Performance Racing Store) publish prices but no ET-delta math.

### Threat synthesis

Three months running, no head-on competitor has emerged. The risk surface is:
1. **A US/EU competitor adds INR + Indian bike presets** — low likelihood (no commercial incentive without a local sales channel).
2. **An Indian YouTube channel ships a free ET calculator as a lead magnet** — medium likelihood, low real threat (no validated physics).
3. **A bike OEM (Ultraviolette, Hero, Bajaj) ships a "configure & race" microsite** — low likelihood, high consequence if it happens for their flagship bike family.

### Opportunity boosts (this week)

- **marketing-content (+10):** No competitor produced English-language content on "Valley Run 2026 results" or "fastest Indian electric motorcycle drag time" this week. Window open for our own coverage tied to F99 / Suvarna wheelie record narrative.
- **seo-keyword (+10):** "valley run 2026 results", "valley run drag race", "ultraviolette f99 quarter mile" are uncontested + transactional.
- **partnership-outreach (+5):** Elite Octane (Valley Run organisers) has no software-partner mention on eliteoctane.com — clean outreach surface.

### Don't-do this week

- Don't out-spend SEO competition on "quarter mile calculator" (generic, owned by US legacy sites). Stay on India-qualified long-tails.
- Don't position against DragSim5 directly — different market, different price point. Reference only as "we're the web-native, India-first equivalent" when needed.

---

## 2026-05-31 — Week scan

### Delta vs last week

- **Valley Run 2026 Summer date corrected** to **April 17-19, 2026** per eliteoctane.com/events.html (last week's note had April 3-5; that was the Summer 2024/2025 cadence). The event has already happened; no results page indexed yet.
- **2026 Suzuki Hayabusa unveiled** in the UK with throttle-map + cruise-control + quickshifter updates. Indian-press coverage is fresh (Autocar India, ackodrive, gaadikey, BikeWale, BikeDekho, 91wheels all carrying the story). India-spec arrival "expected near term," UK OTR £18,599 ≈ ₹21.55 lakh. Hayabusa is one of our three baseline reference bikes — content + catalog opportunity.
- **Ultraviolette F99 production launch is Q1 2026** per multiple Indian press; ZigWheels, BikeDekho, 91wheels, autoX, TheBikeJunction all carry product pages; expected ₹4.5L-₹8L spread. The 10.712s Valley Run 2024 quarter-mile record remains the headline stat.
- **MotoGuru AI** (themotoguru.com) — new entrant claiming "intelligent motorcycle recommendations & advice." Single-page landing site, no visible product behind it. Could not extract feature set or pricing — homepage is title-only. Threat unclear; tracking for next week.

### Direct competitors (motorcycle drag/ET tools)

| Name | URL | Change this week | Threat | Notes |
|---|---|---|---|---|
| DragSim5 (Motion Software) | motionsoftware.com/dragsim5.htm | None observed | Low-medium | Still Windows-only legacy product. No new release indexed. |
| DragCalc / Wallace Racing / XCceleration / Rob Robinette / Speedmaster / AJ Designer / FIRGELLI | (see last week's table) | None observed | Low | Generic web calculators, no India focus. SERP positions stable. |
| MotoGuru AI | themotoguru.com | **NEW — first surfaced this week** | Unknown | "AI motorcycle recommendations" positioning; landing page minimal. Need a deeper probe next week to confirm whether it overlaps our recommend/build-optimizer surface. |

### Adjacent / mass-audience signal

- **Drag Drive Simulator (Roblox)** — Beta V1.1.3 "LIMITED x BIG UPDATE" rolled out late March + early April 2026; Update V1.1.4 followed April 25. The game added **manual Gear Ratio Tuning** (shorter ratios = faster acceleration, lower top speed; longer ratios = inverse) and a new **Pettarani Track** drag-strip map set in Makassar, Indonesia. The game has 1.6 billion+ visits and ~tens of millions of weekly players.
  - **Not a competitor** (game vs. tool), but it is now teaching gear-ratio drag-strategy vocabulary to a teenage mass audience.
  - **Opportunity:** the same vocabulary that MotoQuant's gear-cassette UI uses (front sprocket, primary ratio, top-gear overdrive) is now being normalised. Educational SEO content on "how gear ratios actually change quarter-mile ET" maps onto a growing search base.

### Indian moto-news signal

- **2026 Suzuki Hayabusa updates** dominated bike-news cycles last week across Autocar India / BikeWale / BikeDekho / 91wheels / Smartprix / autoX / ackodrive. Themes covered: throttle-map tweaks for low-rev torque, cruise-control-during-quickshift, two new colour schemes (gloss black + dark red infill; white + blue accents).
  - **Action:** publish a blog post quantifying the throttle-map update's ET delta on MotoQuant's stock Hayabusa Gen 3 config. The reference baseline is 10.4712s; even a modest +5% low-rev torque map should be measurable in sim. This is exactly the "validated physics tied to fresh OEM news" content angle our SEO map calls for.
- **ZigWheels / BikeWale** — no dedicated drag-race coverage indexed this week, but Hayabusa news volume is the lead India bike story.

### Other axes scanned (no new signal)

- **"AI motorcycle tuning"** — surfaces Rapid Bike EVO2 (real-time auto-fuel adjustment, hardware in the loop), Motovation USA blog post on AI tuning, Aoocci AI voice assistant integration. None overlap our build-optimizer / ET-prediction stack.
- **"motorcycle build parts ROI calculator India"** — Reddit returned zero hits. The category gap from previous weeks holds.
- **Surrogate-model motorcycle simulation** — academic + VI-Grade enterprise tools only. No consumer-facing surrogate sim landed.

### Threat synthesis

Still no head-on direct competitor. Two new things to watch:
1. **MotoGuru AI** — single-page site, unknown depth. If it ships a build-recommender, that overlaps our `analysis recommend` + Build Optimizer surface (Track B delivery just-shipped).
2. **OEM-side telemetry pages** — the F99 production launch + 2026 Hayabusa cycle means OEM-controlled "configure & race" microsites get more likely. Still low probability, still high consequence.

### Opportunity boosts (this week)

- **marketing-content (+18):** 2026 Hayabusa news cycle is live now; a "what the new throttle map does to ET" post hits Hayabusa search demand at peak. Independent and Valley Run 2026 recap coverage gap also unfilled.
- **catalog-expansion (+10):** Add the 2026 Hayabusa throttle-map-updated config + the production-spec Ultraviolette F99 once specs settle. F99 carries the "fastest Indian-manufactured" headline-stat moat.
- **seo-keyword (+12):** "2026 hayabusa quarter mile", "2026 hayabusa india price", "ultraviolette f99 launch india" are uncontested high-intent India queries this week.
- **partnership-outreach (+3):** Elite Octane's events page still shows no software partner. Carry-over from last week.

### Don't-do this week

- Don't react to MotoGuru AI yet — single landing page, no visible product. Probe deeper next week before allocating any response budget.
- Don't write generic "best quarter-mile calculator" comparison content; US legacy sites own those SERPs.

---
