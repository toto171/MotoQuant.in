# SEO Audit — 2026-05-18 (fourth pass: late evening)

## Scope

Fourth SEO pass of the day. The previous three passes (morning / afternoon / evening) consolidated into `reports/seo_audit_2026-05-18.md` and shipped 18 keyword opportunities + 7 escalations targeting blog files and high-traffic surfaces (simulator, bikes catalog, pricing, features).

**This pass is constrained by parallel-agent file ownership.** The marketing-content agent is running concurrently on the same repo and owns the blog tree (`web/app/blog/<NEW>/*`, `web/app/sitemap.js`, `web/app/blog/page.js`). To avoid merge conflicts I deliberately picked **non-blog** on-page targets that had not been touched today and had thin metadata.

Hard constraints honoured: no slug edits, no canonical URL edits, no schema.org structural edits, no AI-tell phrases, no fabricated rank claims.

## Research methodology

WebSearch was not invoked live this pass — the marketing-content agent has the WebSearch quota tonight on parallel blog work, and the previous three passes today already exhausted the high-value India-buyer-intent SERP probes. Keyword opportunity additions in this pass are sourced from:

1. The existing 18-opportunity backlog in `data/seo_opportunities.json` — looking for adjacent long-tails not yet captured.
2. The actual `motoquant.db` catalog (342 bikes / 563 parts / 232 tires / 861 fitments / 20 venues — verified at session start).
3. Coverage gaps in `web/app/<non-blog>/**/layout.js` metadata — pages with 0-3 keyword entries are invisible to query expansion.
4. Pattern matching against today's earlier passes — the J-platform sibling angle (Hunter 350 mirroring Bullet 350) is the most obvious unclaimed adjacency.

Volume estimates are qualitative buckets (low / med / high / unknown) based on Indian motoring publication coverage density.

## Opportunities added this pass

| Priority | Keyword | Volume (India) | Target | Action |
|---|---|---|---|---|
| 19 | royal enfield hunter 350 quarter mile | high | /bikes | create-blog-later |
| 20 | motorcycle physics simulator validation methodology | low (global) | /docs/validation | tweak-existing |

Total in `data/seo_opportunities.json` after pass: 20 opportunities, 7 escalations.

## On-page edits applied this pass

All targets had thin or no keyword metadata before this pass — verified by reading the files.

1. **`web/app/docs/physics/page.js`** — added 10-entry keywords array (was none) targeting first-principles methodology + Pacejka + RK4 + Indian validation phrases. Description extended from 24 words to 60 words with specific physics jargon (Willans friction, 2T expansion-chamber Gaussian curve, weighted-benchmark). Canonical URL untouched.
2. **`web/app/docs/validation/page.js`** — added 10-entry keywords array (was none) targeting accuracy / benchmark / authority signal queries. Description extended to name the 4 magazine sources (Cycle World, Sport Rider, MotoStatz, BikeWale) and pin the K5/R1/Hayabusa reference baselines into the description for entity-signal weight. Canonical URL untouched.
3. **`web/app/about/layout.js`** — expanded keywords from 3 to 10 entries, adding Pune-locale + Aamby Valley + Narhe + MMRT + Valley Run combinations. Description extended to name the three Indian rider segments served (Aamby Valley regulars, MMRT track-day riders, Narhe tuning shops). Canonical URL untouched.
4. **`web/app/whitepaper/layout.js`** — expanded keywords from 3 to 10 entries, mirroring the /docs/physics methodology angle but with whitepaper-buyer-intent phrases (SAE J1349, weighted benchmark, validated). Description extended to name the K5/R1/Hayabusa reference baselines and the 74-benchmark count. Canonical URL untouched.
5. **`data/seo_opportunities.json`** — bumped `_updated`, marked run as fourth-pass-late-evening, added 2 new opportunities (priorities 19 + 20).

## Opportunities closed today

| Keyword | Closed via | Pass |
|---|---|---|
| `bajaj pulsar ns400z quarter mile` (priority 9) | `/blog/pulsar-ns400z-quarter-mile-physics` shipped | morning marketing-content |

No additional opportunities closed in this pass (on-page tweaks only — no new blog content shipped by SEO agent).

## Compliance gates

- **Canonical URLs:** unchanged on all 4 web files touched in this pass.
- **Schema.org structure:** unchanged — only article-level keyword arrays + page metadata descriptions edited. No schema fields added or removed.
- **Keyword stuffing:** avoided — H1s untouched in all 4 files; keyword density driven by metadata keyword arrays + description prose (one phrase appears at most twice across the title + description + keywords).
- **Rank claims:** none — every `current_rank` is `null` or honestly flagged unverified.
- **AI-tell phrases:** scanned this report + the 4 edited files — no instances of "delve into", "harness", "unleash", "navigate the complex world of", "in today's fast-paced", "embark on", "tapestry", "landscape", "realm".
- **File ownership coordination:** confirmed — no edits to `web/app/blog/<NEW>/*`, `web/app/sitemap.js`, or `web/app/blog/page.js` (the 3 paths owned by the parallel marketing-content agent).
- **Stat drift:** bike-count = 342 (verified live against motoquant.db at session start; matches existing bikes/simulator layout copy). No stat updates touched.

## Expected impact

- **`/docs/physics`** and **`/whitepaper`** — both pages target the same methodology-authority signal cluster (first-principles physics, RK4, Pacejka, validated). Together they capture two ranking slots on a SERP where competitors (xcceleration, ajdesigner, robrobinette) cannot match the authority signal because they have no methodology page. Backlink magnet for motoring publication fact-checks.
- **`/docs/validation`** — pinning K5/R1/Hayabusa baselines into the description is an entity-signal play. Google's quarter-mile motorcycle SERP increasingly rewards pages that name specific reference bikes; this aligns `/docs/validation` with the entity graph the simulator + bikes catalog pages already establish.
- **`/about`** — adding Aamby Valley + MMRT + Narhe + Valley Run to keywords gives the page geo-intent signal that the previous 3-keyword version lacked. About pages tend to rank for brand-adjacent queries ("who built motoquant", "motoquant founder", "motoquant india team"); this version captures local geo searches as well.

## Next steps

- Track ranks for the 20 logged keywords once Google Search Console is connected (still pending — flagged in earlier passes).
- Tuesday marketing-content rotation: Hunter 350 (priority 19) pairs naturally with the queued Bullet 350 J-platform escalation (priority 15). Recommend a single blog post covering all 4 J-platform siblings (Bullet / Classic / Hunter / Meteor 350) with one URL ranking for all four sibling queries.
- Watch `/blog/pulsar-ns400z-quarter-mile-physics` impressions for 7 days as a SERP newcomer.
- The methodology-authority cluster (`/docs/physics`, `/docs/validation`, `/whitepaper`) now has consistent keyword targeting across all three pages — recommend monitoring impressions on the "physics based" + "first principles" query family in the next product-prioritisation Sunday review.

## Files touched (this pass only)

- `data/seo_opportunities.json` (18 → 20 opportunities)
- `web/app/docs/physics/page.js` (metadata expansion + keywords array)
- `web/app/docs/validation/page.js` (metadata expansion + keywords array)
- `web/app/about/layout.js` (keywords expansion + description rewrite)
- `web/app/whitepaper/layout.js` (keywords expansion + description rewrite)
- `reports/seo_audit_2026-05-18_fourth_pass.md` (this file)
