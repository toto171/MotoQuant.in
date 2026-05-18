# SEO Audit — 2026-05-18 (Ninth Pass / Monday late)

Ninth SEO pass of 2026-05-18. Eight passes earlier today logged 37 opportunities + 13 escalations across simulator, bikes, features, pricing, about, whitepaper, docs/physics, docs/validation, and the blog index. This ninth pass focuses on the catalog-expansion bikes shipping tonight (CFMoto 800NK + Yamaha MT-125 + Yamaha XSR125) plus a fresh Indian-market signal: Suzuki India's OBD-2B Gen-3 Hayabusa refresh.

## What changed this pass

### `data/seo_opportunities.json`
- `_run` bumped to `ninth-pass-2026-05-18`.
- `_methodology` rewritten to document the ninth-pass focus + research signals.
- **+3 opportunities** (priorities 38-40):
  - **#38 `cfmoto 800nk vs ktm 790 duke quarter mile`** — comparison/buyer-decision, med Indian volume. Shared LC8c parallel twin platform between CFMoto 800NK (added today) and KTM 790 Duke (already in catalog). SERP has zero physics-based comparison content. Action: tweak existing `/blog/cfmoto-800nk-quarter-mile-physics` post (shipped earlier today) with 790-Duke comparison phrasing.
  - **#39 `pulsar n250 vs apache rtr 200 4v drag race`** — comparison, high Indian volume. Carblogindia ran the real-world drag (N250 wins from launch); SERP is YouTube + spec-comparison pages only. Both bikes already in catalog. Action: extend the existing `/blog/pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics` post to 3-bike OR queue dedicated N250-vs-RTR-200 post.
  - **#40 `hayabusa 2026 gen 3 quarter mile india`** — informational/buyer-funnel, high Indian volume. Suzuki India launched OBD-2B Gen-3 at ₹18.06 lakh ex-showroom (190 PS, 150 Nm, revised throttle maps). 0-100 in 2.6s claimed but no SERP carries instrumented quarter-mile ET. Action: refresh `/blog/hayabusa-vs-zx-14r-which-is-faster` with Gen-3 paragraph + Hayabusa bike-detail page.
- **+3 escalations** queued for `marketing-content` (all `opportunistic`):
  - CFMoto 800NK vs KTM 790 Duke — LC8c platform-share quarter-mile physics breakdown.
  - Pulsar N250 vs Apache RTR 200 4V — physics-based drag analysis.
  - Suzuki Hayabusa 2026 Gen 3 quarter-mile physics — OBD-2B refresh impact.

### On-page edits (4 files)
1. `web/app/simulator/layout.js` — keywords array +3 entries (CFMoto 800NK vs KTM 790 Duke, Pulsar N250 vs Apache RTR 200 4V, Hayabusa 2026 Gen 3).
2. `web/app/bikes/layout.js` — keywords array +3 spec-database entries (CFMoto 800NK specs, Hayabusa 2026 Gen 3 specs, Pulsar N250 specifications).
3. `web/app/blog/page.js` — meta keywords array +3 entries for the 3 new keyword targets.
4. `web/app/bikes/page.js` — H1 subtitle namecheck cluster expanded to include "Pulsar N250" + "CFMoto 800NK" alongside the existing entity cluster.

### What was NOT changed
- No edits to `web/app/StructuredData.js` — schema markup structure is load-bearing.
- No edits to `web/sitemap.xml` — marketing-content owns blog + sitemap.
- No canonical URL changes (slug stability is load-bearing for existing rankings).
- No new blog posts shipped this pass (escalations queued instead).

## Top 3 keyword opportunities surfaced this pass
1. **CFMoto 800NK vs KTM 790 Duke** — clean LC8c platform-share story, SERP gap, immediate tweak to live post.
2. **Pulsar N250 vs Apache RTR 200 4V drag race** — high Indian volume, real-world drag exists (Carblogindia), MotoQuant has the physics.
3. **Hayabusa 2026 Gen 3 quarter mile india** — fresh news hook (Suzuki India OBD-2B launch), buyer-funnel signal, no SERP carries an India-specific instrumented ET.

## Sources researched (WebSearch 2026-05-18)
- CFMoto 800NK: AccelerationTimes.com, FastestLaps.com, autos.maxabout.com, fasterwheeler.com, cfmoto.com (no quarter-mile data on any).
- Pulsar N250 vs Apache RTR 200 4V: carblogindia.com (real-world drag), zigwheels.com, autocarindia.com, bikewale.com (0-60/0-100 only, no quarter-mile).
- Hayabusa 2026: bikewale.com, suzukimotorcycle.co.in, autocarindia.com, autox.com, 91wheels.com (₹18.06 lakh, 190 PS, 2.6s 0-100 with launch control claimed, no instrumented quarter-mile).

## Co-ordination
- catalog-expansion adding 1-2 bikes tonight from {CFMoto 800NK, Yamaha MT-125, Yamaha XSR125}.
- marketing-content already shipped one blog post per CFMoto / MT-125+XSR125 platform-pair earlier today.
- This pass adds the comparison-pair angles to the existing posts via meta-keyword + entity-namecheck refresh without splitting URLs.

## Carry-forward for next SEO pass
- Track ranking on the 3 new keyword targets once Search Console connection is wired.
- Pulsar N250 dedicated post vs extending NS200 post — decision pending content-budget.
- Hayabusa Gen-3 paragraph add to flagship comparison post — ready to ship next Tuesday.
- All 13 prior `marketing-content` escalations still open.
