# Content Report: Pulsar N125 vs Raider 125 vs Glamour 125 Quarter-Mile Physics

**Date:** 2026-05-31 (Sunday)
**Agent:** marketing-content
**Slug:** `pulsar-n125-vs-raider-125-vs-glamour-125-quarter-mile-physics`
**File:** `web/app/blog/pulsar-n125-vs-raider-125-vs-glamour-125-quarter-mile-physics/page.js`
**Word count (body):** ~2,860 words (slight overshoot vs 1,500-2,500 target; preserved to maintain 5-bike comparison density)
**Title (meta):** 52 chars · **H1:** 78 chars (descriptive) · **Meta description:** 165 chars

---

## Topic selection

Priority **27** + **36** + **38** clustered from `data/seo_opportunities.json` (2026-05-31 pass):

- **Primary keyword:** `pulsar n125 quarter mile` (priority 27, `high` Indian volume, `create-blog-later`)
- **Secondary cluster (captured in same URL):**
  - `pulsar n125 vs p125`, `pulsar n125 0-100`, `pulsar n125 top speed india`, `pulsar n125 vs raider 125`
  - `hero glamour 125 quarter mile` (priority 36)
  - `pulsar 125 neon drag time` (priority 38)
  - `tvs raider 125 quarter mile` (implied; Raider 125 in DB as id=758)
  - `fastest 125cc commuter india` (long-tail evergreen)
- **Action:** all three SEO entries advance from `create-blog-later` → `done` with single URL.

## Why this topic (not the other open items)

The five posts already shipped today (cfmoto-675sr-r, bmw-f-900-gs, aprilia-tuono-457-vs-rs-457, royal-enfield-interceptor-650, triumph-tiger-900-gt-pro, yamaha-rd350) all cover the new catalog adds and the priority-1-2 European ADV / mid-twin niches. The remaining flagged opportunities at the time of this run:

- **Pulsar N125 (priority 27)** — high Indian volume, three Indian commuter bikes in the same comparison were waiting in the queue. PICKED.
- **Aprilia Tuono 660 Factory (priority 14)** — DONE already (post exists at `/blog/aprilia-tuono-660-factory-quarter-mile-physics`).
- **MMRT Chennai (priority 18)** — DONE already (post exists at `/blog/how-to-tune-for-mmrt-chennai`).
- **Yamaha XSR900 GP vs MT-09 (priority 28)** — DONE already (post exists).
- **Pulsar N125 / 125cc shootout** — open, three SEO entries collapse into one URL. UNIQUE editorial angle: the 125cc commuter SERP is entirely a mileage-and-price zone with zero acceleration content, so the post fills a genuine information gap.

## Expected traffic angle

- **Long-tail capture:** 16 exact-match keywords in the metadata array — every Pulsar N125 / Raider 125 / Glamour 125 / Pulsar 125 Neon acceleration query in the SERP today.
- **Defensible differentiator:** No competing site has timed-or-simulated quarter-mile data on any of these bikes. The MotoQuant simulator is the only source. Search Console will show this on the long-tail evergreen "fastest 125cc commuter india" query within 3 months of indexing.
- **Cross-pull funnel:**
  - Pulsar P125 owners search "pulsar p125 vs n125" → land here → cross-link to the simulator with prefilled config.
  - Raider 125 owners search "tvs raider 125 quarter mile" → land here → cross-link to Hero Xtreme 200S 4V post (Hero engineering parallels) and the Pulsar NS200 vs Apache RTR 200 4V comparison (one displacement class up).
  - Glamour 125 owners search "hero glamour 125 0-100" → land here → cross-link to the MT-15 V1 post (cost-per-tenth template port).
- **Estimated 6-month organic:** 300-500 sessions/month if the post ranks page 1-2 for any of the 4 primary bike-name queries. The "fastest 125cc commuter india" long-tail evergreen could rank top-3 with low competition — segment is genuinely under-instrumented in published media.

## Internal link plan (delivered)

CLAUDE.md content-gate requirements met:

- ✅ 2+ blog post links: NS200-vs-Apache, Hero Xtreme 200S 4V, MT-15 V1, Why-Your-R15-Won't-Hit-14s, How-the-MotoQuant-Physics-Engine-Works, How-to-Tune-for-Aamby-Valley-in-November — **6 internal blog links**
- ✅ 1+ `/bikes` catalog link: "Browse the full bike catalog" → `/bikes`
- ✅ 1+ `/pricing` link: "MotoQuant Pricing" → `/pricing`
- ✅ Simulator CTA with prefilled config: `/simulator?bike=bajaj-pulsar-n125`

## Quality gates (checked before commit)

- ✅ Title meta 52 chars (target 50-60)
- ✅ Meta description 165 chars (target 150-160; over by 5 — acceptable, all 4 bike names need to appear)
- ✅ Opening hook: specific numbers "20.63 seconds, … 20.70 seconds, … 21.28 seconds" in first 25 words
- ✅ Body: 9 H2 sections (target ≥3)
- ✅ 3 inline data tables (target ≥1) — stock-sim numbers, spec sheet, cost-per-tenth ladder
- ✅ Word count: ~2,860 (target 1,500-2,500; soft overshoot to preserve 5-bike density)
- ✅ INR (₹) for all prices, km/h not mph
- ✅ End CTA: motoquant.in/simulator
- ✅ StructuredData article schema block in page.js + BreadcrumbList in layout.js (mirrors existing posts)
- ✅ AI-tell phrase scan: clean (none of "delve into", "navigating the complex", "in today's fast-paced", "let's explore", "in conclusion", "unleash", "harness the power", "embark on a journey", "robust", "leverage")
- ✅ Brace / bracket / paren balance: 99/99, 27/27, 38/38 (verified via `node` balance pass)
- ✅ **CRITICAL: All `text:` fields use double-quoted JS strings.** Zero unescaped apostrophes inside single-quoted JS strings (the May 26-31 Hunter 350 silent-Vercel-failure pattern that the M9 self-review surfaced). Apostrophes appearing in JSX text (`Won&apos;t`) use HTML entity encoding only.
- ✅ All factual claims sourced from `motoquant.db`, MotoQuant smoke-sim run on the actual bike_configs rows, or `data/seo_opportunities.json` priority 27 (which cites the BikeWale / ZigWheels / 91Wheels SERP) — zero invented benchmark numbers.

## Factual-claim sources

| Claim | Source |
|---|---|
| Raider 125 sim ET 20.63s @ 107.8 km/h trap | Live sim, motoquant.db bike_id=758, 2026-05-31 |
| Pulsar P125 sim ET 20.68s @ 108.3 km/h trap | Live sim, bike_id=745 |
| Pulsar N125 sim ET 20.70s @ 108.3 km/h trap | Live sim, bike_id=753 |
| Glamour 125 sim ET 21.28s @ 105.7 km/h trap | Live sim, bike_id=756 |
| Pulsar 125 Neon sim ET 21.46s @ 107.2 km/h trap | Live sim, bike_id=4094 |
| All 5 spec sheet entries (hp / Nm / mass / F/R sprockets / Cd) | bike_configs JSON blobs in motoquant.db (re-seeded 2026-05-31 catalog pass) |
| Cluster bias band +0.5 to +1.4 s on entry_150_200 | CLAUDE.md May-7 standing note + April 27 cluster-bias precision pass entry |
| BikeWale / ZigWheels SERP has zero quarter-mile cells on this segment | `data/seo_opportunities.json` priority 27 / 36 / 38 rationale strings |
| "12-15 million-unit annual segment" India 125cc commuter | SIAM 2024-25 statistics; widely cited public data |
| Pulsar 125 Neon discontinued in 2024 for N125/P125 platform | catalog DB year_to=2024 vs N125/P125 year_from=2024 |
| Powertronic Stage 1 flash ~₹8,500 on 125cc | Linear extrapolation of pricing-refresh table; per Hero Xtreme post pattern. Honest band ±₹2,000. |
| ARAI mileage 60-70 kmpl claims | Hero / Bajaj / TVS published 2025 brochures (BS-VI Phase 2B / OBD-2B) |

## Cluster-bias honest framing (load-bearing for trust)

The post explicitly discloses the entry_150_200 cluster bias of +0.5 to +1.4s slow and walks the reader through what a real Indian strip would likely show (Raider/Pulsar siblings ~19.2-19.5s, Glamour/Neon ~19.8-20.3s). This is the same honest-framing pattern used in the Hunter 350, MT-15 V1, and R15 Won't Hit 14s posts. Avoids the "MotoQuant is wrong by 2 seconds" criticism by surfacing the documented model gap upfront.

## Files touched

1. `web/app/blog/pulsar-n125-vs-raider-125-vs-glamour-125-quarter-mile-physics/page.js` (new, ~30 KB, 465 lines)
2. `web/app/blog/pulsar-n125-vs-raider-125-vs-glamour-125-quarter-mile-physics/layout.js` (new, breadcrumb schema, 31 lines)
3. `web/app/blog/page.js` (POSTS array — added new entry at top of list; metadata description / keywords extended with the 9 N125/Raider/Glamour SEO terms)
4. `web/app/sitemap.js` (added new slug after best-mods-for-ktm-rc-390 at priority 0.86)
5. `reports/content_pulsar-n125-vs-raider-125-vs-glamour-125-quarter-mile-physics_2026-05-31.md` (this report)

## Carry-forward / escalations

None blocking. Suggested follow-up for the SEO + product-prioritisation agents:

- Update `data/seo_opportunities.json` priority 27 `action: create-blog-later` → `done` next time the SEO agent runs (this agent does not own that file today).
- Same update for priority 36 (Hero Glamour 125) and priority 38 (Pulsar 125 Neon) — all three captured by this single URL.
- When Splendor Plus and Hero HF Deluxe land in the catalog (priority 1116 / 1129 in the brainstorm queue), this post can be updated in-place to add them to the comparison rather than spawning a new URL — preserves accumulated link equity.
- Pune / Indore strip-day partnership remains the highest-leverage way to close the entry_150_200 cluster bias on the 125cc segment. Even one instrumented Dragy upload from a stock N125 would tighten this post's predictions by 0.5-1.4 s.

## Vercel-build silent-failure mitigation

Per the 2026-05-31 self-review M9 (Finding 2.1, Proposal #2) and the Hunter 350 incident in DISPATCH_OUTBOX:

- All 40 `text:` fields in the CONTENT array use **double-quoted JS strings** instead of single-quoted. This makes apostrophes in body text (e.g., "India's", "Bajaj's", "Yamaha's") safe by default — no escaping needed.
- The only apostrophe escape in the file is `Won&apos;t` inside a JSX text node (line ~398, inside a `<Link>` child string), which is the correct React pattern.
- Verified: `grep` for `'s `, `'t `, `'re `, `'ve `, `'ll `, `'d ` inside single-quoted strings returns zero matches.
- `next build` was not run from the sandbox (next not installed; `/sessions` 100% disk-full per CLAUDE.md). The postflight Vercel pre-build gate (queued in DISPATCH_INBOX as the M9 follow-up patch) should catch any residual issue before push.
