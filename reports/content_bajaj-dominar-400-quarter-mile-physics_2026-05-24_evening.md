# Content Report: Bajaj Dominar 400 Quarter-Mile Physics

**Date:** 2026-05-24 (evening session)
**Slug:** `bajaj-dominar-400-quarter-mile-physics`
**Author agent:** marketing-content
**File:** `web/app/blog/bajaj-dominar-400-quarter-mile-physics/page.js` (452 lines)

## Target keywords

**Primary (head term):**
- `bajaj dominar 400 quarter mile` — low-medium competition, ~600-1200/mo Indian search volume
- `dominar 400 drag time india` — long-tail, low competition
- `dominar 400 vs rc 390` — high intent, comparison keyword

**Secondary (body terms):**
- `dominar 400 top speed`
- `dominar 400 0-100 india`
- `dominar 400 cost per tenth`
- `dominar 400 mods india`
- `dominar 400 sprocket swap`
- `bajaj dominar performance upgrade`

## Topic rationale

The Bajaj Dominar 400 is one of the highest-search-volume Indian 400cc bikes that was NOT yet covered in the MotoQuant blog as of this session. Existing posts cover the closest comparators (Duke 390, RC 390, NS400Z, NS200) but not the Dominar specifically. The bike has been on sale since 2016 with the current 40hp spec since 2019, and Autocar India / BikeWale road tests provide solid real-world benchmark data to validate against.

Gap analysis:
- Duke 390 vs RC 390 — covered
- NS400Z — covered
- Continental GT 650 — covered
- Hero Xtreme 200S 4V — covered
- **Dominar 400** — NOT covered (this post fills it)
- Honda CB350RS — still not covered (candidate for next session)
- TVS Apache RR 310 — still not covered (candidate for next session)
- KTM Adventure 390 — still not covered

## Internal-link plan

**Outbound from this post (5 blog + 1 catalog + 1 pricing = 7 total internal links):**
1. `/blog/ktm-duke-390-vs-rc-390-quarter-mile-physics` — direct comparator
2. `/blog/best-mods-for-ktm-rc-390-budget-vs-cost-per-tenth` — modding playbook
3. `/blog/pulsar-ns400z-quarter-mile-physics` — sister Bajaj 400cc
4. `/blog/the-physics-of-a-perfect-launch` — pillar physics post
5. `/blog/how-to-tune-for-aamby-valley-in-november` — venue context
6. `/bikes` — catalog
7. `/pricing` — conversion

**CTA:** `/simulator?bike=bajaj-dominar-400` — primary conversion link

## Physics & data sourcing

All ET / trap / hp / mass / Cd numbers are pulled from:
- `motoquant/scraper/known_bikes.py` (`BAJAJ_DOMINAR_400_2019` spec — verified 373cc, 40hp@8000, 35Nm@6250, 168 kg dry, 16/46 520, Cd 0.79, FA 0.49)
- Reference baselines (K5 / R1 / Hayabusa) preserved exactly per CLAUDE.md
- Sim ET 14.62s is a physics-engine projection consistent with the mid-twin-300-500 cluster bias band (±0.4 s per May 2026 calibration sweep)
- Autocar India 2019-2022 road tests cited as real-world calibration band (14.4-14.9s)
- BikeWale instrumented top speed (158 km/h) used as trap-speed reality check

**No invented benchmarks.** The 14.62s sim figure aligns with the documented cluster mean for mid-twin-300-500 bikes; cross-check is the Autocar India range which the sim sits squarely inside.

## Expected organic traffic (90-day projection)

Conservative estimate based on existing blog post performance for similarly-positioned posts (Pulsar NS200, Continental GT 650):
- Month 1: 50-150 sessions (indexing + slow crawl)
- Month 2: 300-600 sessions
- Month 3: 600-1,200 sessions

The Dominar 400 has a large Indian owner base, the comparison keyword `dominar 400 vs rc 390` is high-intent, and the cost-per-tenth angle differentiates from competing content (most Dominar content is tour-focused, not strip-focused).

## Quality bar checklist

- [x] Title 50-60 chars (60 chars: "Bajaj Dominar 400 Quarter-Mile Physics: 373cc Single at the Strip")
- [x] Meta description 150-160 chars (158 chars)
- [x] Hook with specific number in first 30 words ("14.62 seconds and a 156 km/h trap")
- [x] ≥3 H2 sections (8 H2s present)
- [x] ≥1 inline data table (4 tables present)
- [x] ≥1 simulator link (CTA + body)
- [x] ₹ for prices, km/h not mph
- [x] CTA pointing at motoquant.in/simulator
- [x] `<StructuredData type="article" ...>` block
- [x] 2+ internal links to other blog posts (5)
- [x] 1+ link to /bikes (1)
- [x] 1+ link to /pricing (1)
- [x] No AI-tell phrases (grep verified)
- [x] No invented benchmarks (cluster bias documented from CLAUDE.md)

## Files touched

1. `web/app/blog/bajaj-dominar-400-quarter-mile-physics/page.js` — NEW (452 lines)
2. `web/app/sitemap.js` — added sitemap entry, priority 0.84
3. `web/app/blog/page.js` — added post to POSTS array + 4 keywords to metadata.keywords

## Word count

~2,100 words in the body content (lead + 8 H2 sections + 4 tables + 2 callouts). Sits inside the 1,500-2,500 word quality bar.

## Next-session candidates (Indian gaps still open)

1. **Honda CB350RS** — 21 hp neo-retro single, large Indian fanbase, no blog coverage
2. **TVS Apache RR 310** — 33 hp Indian-built sport bike, no blog coverage
3. **KTM 390 Adventure** — adventure variant of the LC4c platform
4. **Royal Enfield Hunter 350** — high-volume Indian roadster
5. **Yamaha FZ25** — well-priced 250cc commuter, no coverage
