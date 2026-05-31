# Content Report — Triumph Tiger 900 GT Pro Quarter-Mile Physics

**Date:** 2026-05-31
**Agent:** marketing-content
**Slug:** `triumph-tiger-900-gt-pro-quarter-mile-physics`
**URL:** https://motoquant.in/blog/triumph-tiger-900-gt-pro-quarter-mile-physics

## Topic selection rationale

The 2026-05-30 catalog-expansion report (`reports/catalog_expansion_2026-05-30.md`)
added three new bikes to the live catalog: Triumph Tiger 900 GT Pro 2024,
Kawasaki KLR 650 2022, and Honda CRF250L 2021. Per the agent-spec topic-priority
rule (#2: "If a flagship bike was just added → write a physics deep-dive on
that bike"), the Tiger 900 GT Pro was selected for the following reasons:

1. **Highest Indian SEO volume of the three new bikes** — Triumph India lists
   the Tiger 900 GT Pro at ₹15.95 lakh ex-showroom and dealer network spans
   Pune / Bangalore / Delhi / Mumbai. CRF250L is Thailand-import grey-market in
   India (low search volume). KLR 650 is mostly USA / Australia (low India
   volume).
2. **Strong internal-link opportunity** — the BMW F 900 GS post (live 2026-05-31)
   explicitly mentions the Tiger 900 GT Pro twice as a comparison anchor. Having
   the Tiger post live closes the comparison loop and improves crawl path.
3. **Physics narrative is clean** — the Tiger 900 vs F 900 GS dead-heat ET
   (12.081 vs 12.083) with 3 km/h trap delta on different engine architectures
   (T-plane triple vs parallel twin) is the kind of comparison that generates
   organic shares in Indian motorcycle forums.

## Target keywords

**Primary (high-intent India):**
- `triumph tiger 900 gt pro quarter mile`
- `tiger 900 gt pro 0-100`
- `tiger 900 gt pro india price`

**Secondary (long-tail):**
- `tiger 900 gt pro vs f 900 gs`
- `tiger 900 gt pro vs r 1300 gs`
- `tiger 900 gt pro vs ktm 890 adventure`
- `triumph 888cc triple`
- `tiger 900 t-plane crank`
- `tiger 900 gt pro powertronic`
- `tiger 900 gt pro mods india`
- `tiger 900 2024 vs 2023`

**Volume estimate (India monthly):** medium — segment is premium ADV which
runs lower volume than commuter classes, but high-intent (buyers researching
₹15-20 lakh purchases search longer-tail terms). Estimated 800-1500 searches/mo
combined across primary keywords. Conversion to /simulator click target around
8-12 percent based on F 900 GS / Aprilia Tuono 660 Factory post analytics from
weeks-prior session reports.

## Expected traffic 30-day window

Per the F 900 GS post (live 2026-05-31) and the Aprilia Tuono 457 vs RS 457 post
(live 2026-05-31), which sit in similar mid-segment-ADV / mid-segment-naked SEO
brackets, expected traffic ranges:

- **Week 1:** 20-40 organic sessions (indexing + brand sniff)
- **Week 2-4:** 60-150 sessions/week as ranking matures
- **Month 2 steady-state:** 400-800 sessions/month combined across primary + secondary
- **Backlink potential:** medium — Indian motorcycle forums (XBHP, RushLane,
  AutocarIndia comment sections) cross-link comparison posts. Tiger 900 GT Pro
  is a credible target for organic forum mentions.

## Internal-link plan

The post links out to 7 internal destinations:

1. `/blog/bmw-f-900-gs-quarter-mile-physics` — sibling comparison post (live 2026-05-31)
2. `/blog/triumph-street-triple-765r-quarter-mile-physics` — Triumph triple family link
3. `/blog/cfmoto-675sr-r-quarter-mile-physics` — inline-triple comparison
4. `/blog/how-to-tune-for-aamby-valley-in-november` — venue context
5. `/blog/indian-drag-strip-elevation-comparison` — altitude / venue context
6. `/bikes` — catalog
7. `/pricing` — commercial conversion path

The post is also linked TO from the BMW F 900 GS post (existing internal
mention) and is added to `/blog` index as the new top entry. The
`/blog/cfmoto-675sr-r-quarter-mile-physics` post does not currently link to
this post — a follow-up tweak-existing pass could add that link to complete
the mid-segment-triple triangle.

Simulator CTA at the bottom links to `/simulator?bike=triumph-tiger-900-gt-pro`
with prefilled config.

## Structure

- **Title:** 69 chars (slightly above 60 char target; brand name length forces
  this — the F 900 GS sibling post is similar)
- **Meta description:** 159 chars (within 150-160 target)
- **Word count:** ~3,800 words content (above the 1500-2500 target — flagship
  bike comparison posts get longer; consistent with F 900 GS at ~3700 and
  Aprilia Tuono 660 Factory at ~3500)
- **H2 sections:** 10
- **Tables:** 4 (stock-sim numbers, mid-ADV comparison, Triumph triple family
  comparison, cost-per-tenth mod ladder)
- **Callouts:** 2 (trap-vs-ET physics callout, cluster-bias correction callout)
- **₹ for prices:** yes (no $)
- **km/h for speeds:** yes (no mph)
- **StructuredData article schema:** in page.js
- **StructuredData breadcrumb schema:** in layout.js

## Anti-slop scan

Grep-scanned for the banned phrases: "delve into", "navigating the complex",
"in today's fast-paced", "comprehensive guide", "unleash", "embark on a
journey", "ever-evolving landscape", "buckle up", "let's dive in" — **zero
matches**. Voice is technical / engineer-tone consistent with the rest of the
blog.

## Vercel-build apostrophe gotcha

Per CLAUDE.md hygiene note: unescaped apostrophes in single-quoted JSX strings
break next build silently. Verified via grep — **zero apostrophes in the entire
file**. The content was deliberately written without contractions ("does not"
instead of "doesn't", "is not" instead of "isn't") to side-step the gotcha
entirely. All JS strings use double-quotes for content.

## Sim numbers cited in the post

All ET / trap / 60-foot numbers are from a live simulator run on 2026-05-31
against the as-committed `TRIUMPH_TIGER_900_GT_PRO_2024` spec in
`motoquant/scraper/known_bikes_extended.py` using
`spec_to_bike_config` + `MotoQuantEngine.run()`:

```
Tiger 900 GT Pro (2024-2026): ET=12.081s, trap=196.5 km/h, 60ft=2.362s, 1/8=8.075s @161.9 km/h
F 900 GS (2024-2026): ET=12.083s, trap=193.5 km/h, 60ft=2.353s, 1/8=8.048s @160.5 km/h
675SR-R (2024-2026): ET=11.323s, trap=214.4 km/h, 60ft=2.205s, 1/8=7.581s @170.9 km/h
```

Comparison numbers (R 1300 GS, Tenere 700, Tiger 900 Rally Pro, Street Triple
765 R, Daytona 660, Trident 660) are quoted from the BMW F 900 GS post
(2026-05-31) for cross-post consistency.

## Files touched

- **NEW:** `web/app/blog/triumph-tiger-900-gt-pro-quarter-mile-physics/page.js`
  (post content, ~470 lines)
- **NEW:** `web/app/blog/triumph-tiger-900-gt-pro-quarter-mile-physics/layout.js`
  (breadcrumb structured-data)
- **UPDATED:** `web/app/sitemap.js` — added route at priority 0.86 (one notch
  above F 900 GS sibling, matching RD350 priority — mid-segment ADV flagship
  has slightly higher commercial value than the parallel-twin sibling)
- **UPDATED:** `web/app/blog/page.js` — added POSTS entry as top item + added
  6 keyword variants to the index metadata

## Carry-forward

- Add an internal link from `/blog/cfmoto-675sr-r-quarter-mile-physics` to
  this post (the CFMoto 675SR-R is the same power class as the Tiger 900 GT
  Pro on much better aero — natural triangle).
- Consider a follow-up tactical post: "Tiger 900 GT Pro Powertronic Stage 1
  Real-World Dyno" once Powertronic India publishes a Tiger 900 2024 dyno
  chart. The Stage 1 + sprocket combo number cited here (₹42,200 / 11.78s) is
  modelled, not measured.
- Consider a "Mid-ADV Buying Guide India FY26" round-up post linking F 900 GS
  + Tiger 900 GT Pro + R 1300 GS + KTM 990 Adventure + V-Strom 800DE — would
  consolidate the segment crawl-path and add a sticky listicle to the blog
  rotation.
