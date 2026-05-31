# Content Report — yamaha-rd350-quarter-mile-physics

**Date:** 2026-05-31
**Agent:** A4 marketing-content
**Slug:** `/blog/yamaha-rd350-quarter-mile-physics`
**Status:** Shipped

---

## Target keyword

- **Primary:** `yamaha rd350 quarter mile` (informational, India-heavy intent)
- **Secondary:**
  - `rd350 drag time`
  - `rajdoot rd350 quarter mile`
  - `rd350 ht specifications`
  - `rd350 vs pulsar ns200`
  - `rd350 0-100`
  - `yamaha rd350 top speed`
  - `two stroke drag racing india`
  - `rd350 vs hunter 350`
  - `rd350 vs r15 v4`
  - `fastest indian 2-stroke`

## Why this topic

1. **Editorial freshness:** Today (2026-05-31) the A2 physics-calibration agent shipped a 2-stroke `max_engine_decel_rads2` calibration that improved the RD350 sim accuracy by 347 ms. That gives the post a "what changed and why" hook that no competitor SERP entry has.
2. **High India search intent:** The RD350 (Rajdoot RD350 HT/LT, 1983-89 in India) has constant nostalgia/collector/restoration search demand. SERP top results are forums and old YouTube clips with no physics breakdown.
3. **No existing post:** Confirmed via `ls web/app/blog/` — RD350 had zero coverage despite being arguably the most-searched single Indian 2-stroke nameplate.
4. **Cross-link bait:** Post links naturally into the existing `how-a-2-stroke-expansion-chamber-actually-works`, `yezdi-roadster-quarter-mile-physics`, `royal-enfield-hunter-350-quarter-mile-physics`, `the-physics-of-a-perfect-launch`, `how-to-tune-for-aamby-valley-in-november` cluster.

## Expected monthly traffic

- Indian organic SEO volume for "yamaha rd350" cluster is estimated **medium-high** based on the SEO opportunities file's pattern for similar single-bike posts (e.g. priority 4 "ktm duke 390 quarter mile" was labelled `high`; RD350 sits in the same band given the comparable enthusiast install base).
- Conservative 90-day estimate: 400-800 organic sessions/month at steady state after Google indexes the URL (3-6 weeks).
- Pickup boost from the cluster-bias honest framing — gives the post a unique academic angle that no SERP competitor matches.

## Internal-link plan

The post links outward to:

1. `/blog/how-a-2-stroke-expansion-chamber-actually-works` — natural extension of the 2T launch/charge-stuffing physics
2. `/blog/yezdi-roadster-quarter-mile-physics` — Indian 2T sibling/competitor
3. `/blog/the-physics-of-a-perfect-launch` — the binary on-pipe/off-pipe launch insight
4. `/blog/how-to-tune-for-aamby-valley-in-november` — the venue + density-altitude context
5. `/blog/royal-enfield-hunter-350-quarter-mile-physics` — the modern 350cc commuter that the 1973 RD350 still beats
6. `/bikes` — catalog browse
7. `/pricing` — conversion CTA
8. `/simulator?bike=yamaha-rd350-1973&venue=aamby-valley` — primary in-content CTA

That meets the bar: ≥ 2 to other blog posts (5), ≥ 1 to /bikes (1), ≥ 1 to /pricing (1).

## Numerical claims and provenance

Every numerical claim is sourced from one of:

- `motoquant/scraper/known_bikes.py` (RD350 / RD400 / RX100 spec sheet — Yamaha service manual sourced)
- `reports/physics_calibration_2026-05-31.md` (today's two_stroke sim numbers: 14.707s ET, 0.347s improvement, max_engine_decel_rads2 800→1500 knob change)
- Cycle World December 1973 instrumented test (14.000s ET — cited in calibration report)
- Existing `royal-enfield-hunter-350-quarter-mile-physics` post (Hunter 350 sim ET 16.895s for comparison table)
- `CLAUDE.md` cluster-bias documentation (entry_200_300 +0.5-1.0s, two_stroke band)
- Honda HRC NSR250 service manual (cited in calibration report for the 10000 rpm/s peak crank deceleration)

**No invented numbers.** All comparison ETs (NS200 ~16.05s, R15 V4 ~16.5s, CB350 H'ness ~16.8s) are stated in approximate form because they are cluster-bias-adjusted estimates documented in CLAUDE.md May 7 cluster summary; precise sweep entries vary across documented sweeps. The Rajdoot HT/LT detune numbers are derived analytically from the export 39 hp baseline by linear scaling on peak power.

## Anti-slop verification

- Grep for `delve into | navigating the complex | fast-paced world | worth noting that | comprehensive guide | let's explore | embark on a journey` — **no matches** (verified).
- All ₹ prices used, all km/h speeds, no mph.
- No claim of "comprehensive" or "ultimate" anywhere.
- No magazine prose copied verbatim — Cycle World 1973 cited only for the 14.000s ET number.

## Word count

- Body content: **2,083 words** (target 1,500-2,500 — within range)
- Title: 51 chars (target 50-60 — within range)
- Reading time displayed: 12 min (matches blog index entry)

## Files touched

1. `web/app/blog/yamaha-rd350-quarter-mile-physics/page.js` — new (407 lines)
2. `web/app/blog/yamaha-rd350-quarter-mile-physics/layout.js` — new (40 lines, breadcrumbs)
3. `web/app/sitemap.js` — edit (added new entry at priority 0.86)
4. `web/app/blog/page.js` — edit (added new POSTS entry at top, dated 2026-05-31)
5. `reports/content_yamaha-rd350-quarter-mile-physics_2026-05-31.md` — this report

## Validation gates passed

- [x] Title 50-60 chars (51)
- [x] Opening hook contains specific number within first 30 words ("14.707 seconds and about 145 km/h trap")
- [x] Body has ≥ 3 H2 sections (8 H2 sections)
- [x] Body has ≥ 1 data table (4 tables)
- [x] Simulator link with prefilled config (`/simulator?bike=yamaha-rd350-1973&venue=aamby-valley`)
- [x] ₹ for prices (e.g. ₹450 sprocket)
- [x] km/h not mph throughout
- [x] CTA at end pointing to /simulator
- [x] StructuredData block injected via articleSchema
- [x] ≥ 2 internal blog links (5), ≥ 1 to /bikes (1), ≥ 1 to /pricing (1)
- [x] Brace balance 86/86, paren balance 52/52, bracket balance 37/37
- [x] All 28 text-block string literals parse cleanly (Python regex audit)
- [x] No AI-tell phrases
- [x] Reference baselines K5/R1/Hayabusa NOT touched (no claims to or from those numbers)

## Blockers / open items

None. Post is shipping-ready.

## Future SEO follow-up

- Track ranking weekly via Search Console once the URL indexes
- Consider companion post `rd350-vs-rd400-quarter-mile-physics` if the standalone gets traction (RD400 is also in catalog, the pair-post format works well — c.f. `aprilia-tuono-457-vs-rs-457-quarter-mile-physics`)
- Update the `seo_opportunities.json` priorities tracker — mark the implicit RD350 demand bucket as `done`
