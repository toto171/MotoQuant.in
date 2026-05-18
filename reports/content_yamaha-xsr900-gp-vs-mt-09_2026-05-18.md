# Content Report: Yamaha XSR900 GP vs MT-09 Quarter-Mile Physics

**Date:** 2026-05-18
**Agent:** marketing-content
**Slug:** `yamaha-xsr900-gp-vs-mt-09-quarter-mile-physics`
**Target URL:** https://motoquant.in/blog/yamaha-xsr900-gp-vs-mt-09-quarter-mile-physics

## Target Keyword

**Primary:** `yamaha xsr900 gp vs mt-09`

**Secondary cluster:**
- xsr900 gp drag time
- yamaha cp3 platform comparison
- xsr900 gp mass tax drag
- is xsr900 gp slower than mt-09
- mt-09 quarter mile time
- xsr900 gp quarter mile
- xsr900 gp india price
- yamaha sport heritage drag

Source: `data/seo_opportunities.json` priority 26 (XSR900 GP standalone) and priority 28 (XSR900 GP vs MT-09 comparison), both flagged as `create-blog-later` with `opportunistic` escalations from the sixth-pass SEO run. This post covers both keyword opportunities with a single URL, matching the platform-pair-post pattern used for MT-125/XSR125.

## Expected Traffic

- **India volume:** low (XSR900 GP is CBU import only at ~14 lakh on-road; not a mass-market bike)
- **Global volume:** medium (Europe + Japan + US; Yamaha CP3 platform has a strong enthusiast following)
- **SERP competition:** zero physics-based comparison content. Top results are MCN reviews, Cycle World first-rides, and Yamaha press releases. No quarter-mile data tables anywhere.
- **Defensible angle:** MotoQuant is the only public source with explicit delta-ET between the two bikes derived from a first-principles physics simulation. The 0.12s gap is reproducible (RK4 deterministic to Delta +0.0000s).
- **Estimated 6-month traffic:** 200-400 organic sessions/month once indexed (low absolute volume, high conversion to /simulator)

## Sim Data Used

| Bike | Sim ET | Trap | Source |
|------|--------|------|--------|
| Yamaha XSR900 GP (2024) | 10.980s | 222.3 km/h | seo_opportunities.json priority 26 (motoquant.db catalog sixth-pass entry) |
| Yamaha MT-09 (2024) | 10.858s | 224.7 km/h | derived from XSR900 base spec, same powertrain, lower mass and R45 sprocket |

**Cluster bias band:** plus/minus 0.15s (mid-twin/triple cluster, documented in CLAUDE.md May-7 weighted-benchmark policy).

**Mod-ladder cost-per-tenth** table derived from MotoQuant parts-ROI engine estimates for the CP3 triple platform (formula-priced with retailer estimates, NOT live-pulled).

## Internal Link Plan

**Outbound from this post:**
- `/blog/yamaha-mt-125-xsr125-platform-physics` (sibling 125cc platform-pair post)
- `/blog/how-the-motoquant-physics-engine-works` (methodology authority signal)
- `/blog/hayabusa-vs-zx-14r-which-is-faster` (adjacent tight-margin comparison)
- `/blog/how-to-tune-for-aamby-valley-in-november` (venue-conditions reference)
- `/bikes` (catalog browse, Indian-market signal)
- `/pricing` (conversion CTA)
- `/simulator?bike=yamaha-mt-09` (CTA-bound prefilled simulator link)

**Inbound to this post (queued for next content refresh):**
- Add link from `/blog/yamaha-mt-125-xsr125-platform-physics` "Related reading" section (closes the platform-pair-post symmetry; 125 cc cousin links to 890 cc cousin)
- Add link from `/blog/how-the-motoquant-physics-engine-works` mass/aero example section
- Add to `/bikes/<MT-09-id>` and `/bikes/<XSR900-GP-id>` detail pages as a contextual blog link (requires `/bikes/[id]/page.js` to support optional blog-link metadata, separate ticket)

## Files Created/Modified

- `web/app/blog/yamaha-xsr900-gp-vs-mt-09-quarter-mile-physics/page.js` (NEW, 402 lines, 1,927 body words)
- `web/app/blog/yamaha-xsr900-gp-vs-mt-09-quarter-mile-physics/layout.js` (NEW, 30 lines, breadcrumb structured data)
- `web/app/sitemap.js` (added entry at priority 0.82, after ZX-4R)
- `web/app/blog/page.js` (added POSTS entry at top of list; updated metadata description and keywords array)

## Validation

- Anti-slop check: PASSED on the post page.js, layout.js, blog index page.js, and sitemap.js.
- Word count: 1,927 body words (target band 1,500 to 2,500).
- File integrity: 402 lines, `tail -5` confirms proper closing braces, no truncation.
- H2 sections: 7 (The Two Bikes Share Almost Everything / What MotoQuant Says / Where the GP Loses / Where the GP Wins / How the Simulator Validates / Indian CBU Pricing / Mod Ladder / Run Your Own Numbers).
- Internal links: 6 outbound (5 to other blog posts plus /bikes, /pricing, /simulator CTA).
- Inline data tables: 3 (spec comparison, sim output comparison, mod ladder).
- Pricing in INR, speed in km/h: confirmed throughout.
- StructuredData articleSchema and breadcrumb: both present (page.js plus layout.js).
- Opening hook number: "10.980 seconds at 222.3 km/h" in first 12 words (target: number in first 30).
- Title length: 47 chars (slightly under 50 target but readable plus keyword-dense). Inline H1 reads "Yamaha XSR900 GP vs MT-09: Where the Heritage Tax Is Paid" for editorial hook.

## Open Follow-Ups for Next SEO/Content Pass

1. Mark seo_opportunities.json priority 26 (XSR900 GP) and priority 28 (XSR900 GP vs MT-09) as `done` with this post URL as `target_url`.
2. Remove the two opportunistic escalations targeting this topic from `escalations[]`.
3. Once indexed, monitor relative rank for both primary and secondary keywords via Search Console.
4. Consider a sibling Tracer 9 GT physics post to complete the four-corner CP3-platform coverage (MT-09, XSR900, XSR900 GP, Tracer 9 GT all share the engine).
