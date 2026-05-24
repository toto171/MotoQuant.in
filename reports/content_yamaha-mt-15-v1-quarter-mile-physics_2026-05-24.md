# Content Report: Yamaha MT-15 V1 Quarter-Mile Physics

**Date:** 2026-05-24 (Sunday)
**Agent:** marketing-content (A4)
**Slug:** `yamaha-mt-15-v1-quarter-mile-physics`
**File:** `web/app/blog/yamaha-mt-15-v1-quarter-mile-physics/page.js`
**Word count (body):** ~2,030 words (target 1,500–2,500)
**Title:** "Yamaha MT-15 V1 Quarter-Mile Physics: 155cc Naked Drag" (54 chars)
**Meta description:** 157 chars

---

## Topic selection

Priority 44 from `data/seo_opportunities.json` (2026-05-24 pass):

- **Primary keyword:** `yamaha mt-15 v1 quarter mile`
- **Volume:** high (Indian-market segment)
- **Secondary:** `mt-15 v1 drag time india`, `mt-15 v1 vs r15 v3`, `yamaha mt-15 2019 0-100`, `mt-15 v1 top speed india`, `is mt-15 v1 faster than ns200`
- **Action:** `create-blog-later` → now `done`

The Yamaha MT-15 V1 (2019-2020) was just added to the catalog today by the catalog-expansion agent (see `reports/catalog_expansion_2026-05-24.md`). Smoke sim: 17.0507s @ 125.5 km/h trap. Sits inside the entry_150_200 cluster.

## Why this topic (not 45 or 46)

- Priority 45 (Pulsar 125 Neon) is `very-high` volume but is a sub-125cc commuter — same cost-per-tenth story as Hero Glamour 125 (priority 36 already covered) and Hero Splendor segment. Less differentiated angle.
- Priority 46 (GSX-R600 K8) is `med` volume — narrower audience, and the K6 / K8 / K9 supersport era is well-covered globally; harder to rank against existing US/UK content.
- Priority 44 (MT-15 V1) is `high` volume + has the **strongest unique angle**: same engine block as the R15 V3 but with VVA deleted, which is a story almost no other site tells with physics rigor. Indian 155cc segment is a high-intent buyer audience and the comparison naturally cross-links to the R15 V4 post (Why Your R15 Won't Hit 14s) and the NS200/Apache 4V comparison post.

## Expected traffic angle

- **Long-tail capture:** Five exact-match secondary queries above.
- **Cross-pull:** R15 V3 / V4 owners googling "MT-15 V1 vs R15 V3" land on this post → cross-link funnel to the existing R15 post and on to /simulator?bike=yamaha-mt-15-v1.
- **Indian 155cc-200cc cross-shopper segment:** The NS200 / Apache 4V / Xtreme 4V comparison table captures readers comparing across displacement classes — feeds them into all three sibling posts and the simulator.
- **Estimated 6-month organic:** 200-400 sessions/month if the post ranks page 1-2 for the primary keyword. Comparison query "mt-15 v1 vs r15 v3" is the highest-intent funnel because R15 owners ask it.

## Internal link plan (delivered)

Required links (CLAUDE.md content gates):

- ✅ 2+ blog post links: Why Your R15 Won't Hit 14s, Hero Xtreme 200S 4V, Pulsar NS200 vs Apache RTR 200 4V, How the MotoQuant Physics Engine Works, How to Tune for Aamby Valley in November — **5 internal blog links**
- ✅ 1+ /bikes catalog link: "Browse the full bike catalog" → `/bikes`
- ✅ 1+ /pricing link: "MotoQuant Pricing" → `/pricing`
- ✅ Simulator CTA with prefilled config: `/simulator?bike=yamaha-mt-15-v1`

## Quality gates (checked before commit)

- ✅ Title 54 chars (50-60 target)
- ✅ Meta description 157 chars (150-160 target)
- ✅ Opening hook: "17.05 seconds with a 125.5 km/h trap" in first 25 words
- ✅ Body: 7 H2 sections (target ≥3)
- ✅ 4 inline data tables (target ≥1)
- ✅ Word count: ~2,030 (target 1,500-2,500)
- ✅ INR (₹) for all prices, km/h not mph
- ✅ End CTA: motoquant.in/simulator
- ✅ StructuredData article schema block + breadcrumb in layout.js (mirrors existing posts)
- ✅ AI-tell phrase scan: none of "delve into", "navigating the complex", "in today's fast-paced", "let's explore", "it's important to note", "in conclusion", "unleash", "unlock", "harness the power", "embark on a journey"
- ✅ Brace / bracket / paren balance: 88/88, 38/38, 42/42
- ✅ All factual claims sourced from CLAUDE.md, `reports/catalog_expansion_2026-05-24.md`, or Yamaha India / BikeWale (no fabricated benchmarks)

## Factual-claim sources

| Claim | Source |
|---|---|
| MT-15 V1 18.4 hp @ 10,000 rpm, 14.7 Nm @ 8,500 rpm | Yamaha India press release March 2019; Bike India first ride Apr 2019 |
| 134 kg dry mass | reports/catalog_expansion_2026-05-24.md |
| 6-spd · F14/R42 · 520 chain | Yamaha service manual 5D71 (2019), via catalog-expansion report |
| Same engine block as R15 V3 minus VVA | Yamaha India spec sheet; widely confirmed |
| Sim ET 17.05s @ 125.5 km/h trap | MotoQuant smoke-sim, reports/catalog_expansion_2026-05-24.md |
| Cluster bias band +0.5 to +1.0s | CLAUDE.md May 2026 entry; entry_150_200 cluster |
| NS200 ~15.8s, Apache 4V ~16.2s, Xtreme 4V ~17.4s sim ETs | Existing per-bike CLAUDE.md notes + Hero Xtreme 200S 4V blog post numbers |
| Aamby Valley November conditions (DA ~1100m, 22°C) | Existing venue data + matched against Hero Xtreme post |

## Files touched

1. `web/app/blog/yamaha-mt-15-v1-quarter-mile-physics/page.js` (new, 23 KB)
2. `web/app/blog/yamaha-mt-15-v1-quarter-mile-physics/layout.js` (new, breadcrumb schema)
3. `web/app/blog/page.js` (POSTS array — added new entry at top; metadata description / keywords extended with MT-15 V1 SEO terms)
4. `web/app/sitemap.js` (added new slug after Hero Xtreme 200S 4V at priority 0.82)
5. `reports/content_yamaha-mt-15-v1-quarter-mile-physics_2026-05-24.md` (this report)

## Carry-forward / escalations

None blocking. Suggested follow-up:

- Update `data/seo_opportunities.json` priority 44 `action: create-blog-later` → `done` next time the SEO agent runs (this agent does not own that file today).
- When MT-15 V2 catalog entry lands, a comparison post "MT-15 V1 vs V2: what VVA actually buys you" would be a clean follow-up using the same internal-link structure.
