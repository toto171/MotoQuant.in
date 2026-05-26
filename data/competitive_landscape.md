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
