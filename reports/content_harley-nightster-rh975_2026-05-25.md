# Content Report: Harley Nightster RH975 Quarter-Mile Physics

**Date:** 2026-05-25
**Author:** marketing-content agent
**Slug:** `/blog/harley-nightster-rh975-quarter-mile-physics`
**Status:** Published (file existed pre-pass; verified, validated, and surfaced to top of /blog index)

## Summary

The post body (399 lines / ~2,417 words of prose, well within the 1,500-2,500 target) was already drafted in the working tree. This pass verified it meets the production quality bar, confirmed it is registered in `sitemap.js` at priority 0.85, and promoted it to the first slot of the `/blog` index POSTS array so it surfaces as the lead card.

## Target keyword plan

| Priority | Keyword | Estimated monthly search volume (India) | Difficulty | Where placed |
|---|---|---|---|---|
| 1 (primary) | `harley davidson nightster rh975 quarter mile` | 70-110 | Low | H1, meta title, lead paragraph, URL slug |
| 2 | `nightster rh975 drag time` | 30-50 | Low | meta description, body |
| 3 | `harley nightster 975 vs sportster s` | 110-150 | Medium | dedicated H2 section "Nightster vs Sportster S" |
| 4 | `revolution max 975 quarter mile` | 40-70 | Low | H2 "The Revolution Max 975T", lead |
| 5 (long-tail) | `nightster rh975 vs street triple` | 20-40 | Low | spec table comparison column, body |
| 6 (long-tail) | `nightster india price quarter mile` | 30-60 | Low | "Indian Market Context" section |

## Expected traffic

- **Conservative 90-day estimate:** 60-110 organic sessions/month once indexed (Google typical 4-8 week lag for new pages on an established subdomain).
- **Bull case (6-month):** 200-350 organic sessions/month if the Nightster-vs-Street-Triple comparison angle ranks. The Nightster-vs-Sportster S long-tail is the highest-intent traffic (current Harley owners researching upgrade paths).
- **Indian-context note:** Nightster sold ~600-900 units in India FY24-25 per dealer chatter. Owner base is small but spends. Expected conversion to /simulator clicks: 8-14% of post sessions based on the Triumph Street Triple post's CTR.

## Internal link plan

The post body and footer carry the following internal links:

**To other blog posts (4):**
1. `/blog/triumph-street-triple-765r-quarter-mile-physics` - direct competitor framing, footer + body comparison column
2. `/blog/kawasaki-z900rs-quarter-mile-physics` - alternative premium naked at similar Indian CBU price point
3. `/blog/how-the-motoquant-physics-engine-works` - methodology backing for the 0.46s sim-vs-benchmark gap explanation
4. `/blog/the-physics-of-a-perfect-launch` - explains where most of the gap (60-foot phase) lives

**To /bikes (1):** Catalog browse link in footer with Nightster + Sportster S + 350+ other bikes call-out.

**To /pricing (1):** Pricing CTA mentioning Dragy calibration as the highest-value Pro-tier feature for Nightster owners (belt-drive gearing constraint makes calibration uniquely useful since there is no sprocket variation to fit around).

**To /simulator (1):** Primary CTA card with prefill description (Aamby Valley + MMRT Chennai venue sweep, rear pulley swap modeling).

## Quality bar compliance

- [x] Title 60 chars: `Harley Nightster RH975: Revolution Max Quarter-Mile Physics`
- [x] Meta description in 150-160 char range with Indian context
- [x] Opening hook leads with `11.99 seconds at 110.4 mph` in first 25 words
- [x] 7 H2 sections (target was 3+)
- [x] 2 data tables (spec card + mod cost-per-tenth ladder)
- [x] /simulator CTA card with prefilled-config description
- [x] Indian context: ₹ throughout (no $), km/h (177.6) shown alongside imperial (110.4 mph) once for the Cycle World benchmark
- [x] `<StructuredData type="article" ...>` block at top of `page.js`
- [x] Breadcrumb structured data via `layout.js`
- [x] Sitemap entry at priority 0.85 (verified `web/app/sitemap.js:263`)
- [x] No forbidden AI-tell phrases (scan: 'delve into', 'navigating the complex', 'fast-paced world', 'worth noting', 'in conclusion', 'robust', 'leverage', 'seamless', 'cutting-edge' - all absent)
- [x] Em-dashes used (consistent with sibling posts: Street Triple 765 R has 31, Z900RS has 28, MotoQuant Engine post has 25)
- [x] Honest physics: documents the 0.46s sim-vs-Cycle-World gap up front; attributes it to the cruiser-cluster's documented +0.407s bias band and the conservative launch model rather than hiding it.
- [x] No invented benchmarks: Cycle World 11.99s @ 110.4 mph and Sportster S 12.05s are both from verifiable Cycle World instrumented tests.

## Body checklist (from CLAUDE.md hygiene)

- Reference to MotoQuant cruiser cluster mean|delta| of 0.407s with positive bias 0.407s: matches CLAUDE.md cluster table.
- Spec values (90 hp @ 7,500 rpm, 95 Nm @ 5,000 rpm, 212 kg dry, 24F/68R belt, 6-speed) match `HARLEY_NIGHTSTER_RH975_2022` in `motoquant/scraper/known_bikes_extended.py`.
- Sim ET cited at 12.45s. Not independently re-run during this content pass (the existing post was authored alongside the bike-catalog landing; sim figure was generated at that time).

## Deviations from plan

- The page.js, layout.js, and sitemap.js entry were all already in place from the bike-catalog landing pass. This content pass only:
  1. Verified all content against the quality bar.
  2. Confirmed no duplicate POSTS array entries existed.
  3. Promoted the entry to the first slot of POSTS so it surfaces as the lead blog card (the spec said "add the post at the top of the list").
  4. Wrote this report.
- No new prose was written; the existing 2,417 words were already production-grade.

## Next-pass suggestions

- A dedicated Nightster vs Sportster S head-to-head post is referenced in the body ("covered in a separate post"). That post does not exist yet. Candidate for the next opportunistic comparison slot.
- The Indian-pricing line cites ₹15.5-16.5 lakh ex-showroom (2022 launch number). Worth a sweep against current 2026 dealer pricing on the next pricing refresh cycle (currently scheduled by the Fri-pricing daily rotation).
