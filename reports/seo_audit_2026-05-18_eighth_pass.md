# SEO Audit — 2026-05-18 (Eighth Pass)

**Agent:** seo-keyword
**Session:** 1779121832-645 (Monday 2026-05-18)
**Run order:** Eighth SEO pass of the day. Passes 1-7 already logged 33 opportunities and 11 escalations across `/simulator`, `/bikes`, `/features`, `/pricing`, `/about`, `/whitepaper`, `/docs/physics`, `/docs/validation`, and four blog posts. This pass focuses on yesterday's three new bikes (Yezdi Roadster 334, Yezdi Adventure 334, Hero Glamour 125 — added to `motoquant.db` in commit `0cdb5f4`) plus one methodology-broadening keyword.

## What changed

### Files touched
- `/tmp/mq-session-1779121832-645/repo/data/seo_opportunities.json`
  - Bumped `_run` to `eighth-pass-2026-05-18`
  - Refreshed `_methodology` block with eighth-pass scope
  - Appended four new opportunities (priorities 34-37) covering the three catalog additions + one methodology slot-broadening variant
  - Appended two new `marketing-content` escalations (Yezdi-vs-RE Classic 350 platform comparison + Hero Glamour 125 vs Pulsar N125 commuter shootout)
- `/tmp/mq-session-1779121832-645/repo/web/app/simulator/layout.js`
  - Added 4 new keywords to the existing keyword array: `yezdi roadster quarter mile`, `yezdi adventure 334 drag time`, `hero glamour 125 drag`, `motorcycle drag time predictor india`
- `/tmp/mq-session-1779121832-645/repo/web/app/bikes/layout.js`
  - Added 3 new spec-database keywords: `yezdi roadster 334 specs`, `yezdi adventure 334 specs`, `hero glamour 125 specs`
- `/tmp/mq-session-1779121832-645/repo/web/app/bikes/page.js`
  - H1 subtitle now namechecks `Yezdi Roadster` and `Hero Glamour 125` alongside the existing entity-mention cluster (Hayabusa, ZX-14R, R15 V4, KTM Duke 390, Pulsar NS200, Apache RTR, Interceptor 650)

### Counts
- Opportunities logged before this pass: 33
- New opportunities added this pass: 4
- Total after this pass: 37
- New marketing-content escalations: 2 (Yezdi Roadster vs RE Classic 350; Hero Glamour 125 vs Pulsar N125)
- Total escalations: 13
- On-page edits: 3 files touched

## Keyword research rationale (eighth pass)

The three new bikes added on 2026-05-17 (Yezdi Roadster 334, Yezdi Adventure 334, Hero Glamour 125) all sit in underserved SERP regions:

1. **Yezdi Roadster 334** — neo-retro 334cc oil-cooled single positioned as the Indian challenger to the RE Classic 350. Yezdi nameplate revived under Classic Legends (Mahindra group) in 2022; year-on-year search trend climbing. SERP top results are BikeWale / BikeDekho / ZigWheels spec pages with zero instrumented ET data. The "is Yezdi faster than RE Classic 350?" question is a recurring forum thread that nobody answers with physics.

2. **Yezdi Adventure 334** — shares the same 334cc oil-cooled single as the Roadster but adds adventure-touring geometry, ~15 kg more mass, taller suspension. Direct competition for the RE Himalayan 450 (which has a bigger engine and heavier mass — clean cross-comparison story). Year-2 search demand still climbing.

3. **Hero Glamour 125** — one of India's longest-running 125cc commuter nameplates, ~150k unit-per-year average sales. SERP is overwhelmingly mileage-and-price queries with literally zero quarter-mile ET data because the 125cc commuter audience does not search for drag times. That intent-mismatch is the editorial differentiator: a single 125cc-commuter shootout post (Glamour 125, Pulsar N125, Splendor Plus when added) could land an evergreen rank for the underserved "which 125cc commuter is the fastest" query.

4. **Motorcycle drag time predictor india** — slot-broadening variant on the existing `/simulator` primary keyword cluster. Users searching "predictor" instead of "calculator/simulator" are doing the same job with different vocabulary; capturing both phrasings requires both in the keywords array.

## On-page tactics

- **Simulator keywords array** (`web/app/simulator/layout.js`) now contains 27 entries (was 23) — picks up the three new entity keywords plus the methodology variant without polluting the primary high-volume phrases.
- **Bikes layout keywords** (`web/app/bikes/layout.js`) gained three spec-database entries — matches the page's `CollectionPage` schema and ranks for `<bike> specs` queries, which are typically high-intent informational pre-purchase searches.
- **Bikes page H1 subtitle** (`web/app/bikes/page.js`) extends the existing entity-mention cluster to include Yezdi Roadster and Hero Glamour 125. Natural placement — these are real bikes in the catalog, not keyword stuffing.

## What was NOT done

- No edits to `web/app/blog/*` (marketing-content owns blog).
- No edits to `web/app/sitemap.js` or `robots.txt`.
- No canonical URL changes.
- No `schema.org` JSON-LD structural edits (StructuredData FAQ + Indian Market-First tile entity mentions were already updated in the seventh-pass run yesterday).
- No new blog posts created — three escalations queued for marketing-content to pick up on Tuesday's slot.

## Verification

- `python3 -c "import json; d = json.load(open('data/seo_opportunities.json'))"` parses cleanly.
- JSON keys: 37 opportunities + 13 escalations + correct `_run` tag.
- No keyword duplications within the simulator keyword array (verified by visual diff).
- The three new on-page edits are surgical — no slug, schema, or canonical changes.

## Suggested follow-ups for next pass

- Once the Yezdi Roadster vs RE Classic 350 blog post lands, mark priority 34 `action: in-flight` and queue rank tracking.
- The Hero Glamour 125 entry should escalate to `action: in-flight` once the 125cc commuter shootout post is drafted — but ideally wait for the Splendor Plus / Honda Shine 125 catalog entries to broaden the post to a full 4-bike segment shootout (avoids single-bike thinness).
- The `motorcycle drag time predictor india` variant should be re-checked next Sunday via the product-prioritisation agent — if the slot-broadening keyword does not pick up rank within 2 weeks, fold back into the primary `motorcycle quarter mile calculator india` cluster to avoid keyword-bloat dilution.

## Commit summary

`seo(meta): refresh opportunities + 3 on-page wins`

- +4 opportunities (Yezdi Roadster, Yezdi Adventure 334, Hero Glamour 125, drag time predictor variant)
- +2 escalations
- 3 on-page edits (simulator keywords, bikes layout keywords, bikes page H1 subtitle)
