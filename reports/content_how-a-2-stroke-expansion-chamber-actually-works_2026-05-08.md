# Content Report — How a 2-Stroke Expansion Chamber Actually Works

**Slug:** `how-a-2-stroke-expansion-chamber-actually-works`
**Published:** 2026-05-08
**Author:** marketing-content agent (autonomous-ops)
**Word count:** ~2,287 words across 33 prose blocks (within 1,500–2,500 target)
**Read time displayed:** 11 min

## Topic rationale

The MotoQuant catalog has 20 two-stroke bikes (added April 21, 2026 in the +20-bike 2T expansion) but no 2T physics explainer on the blog. Indian audiences care intensely about the RX100, RD350, and the imported Japanese 2T scene; the simulator's 2-stroke cluster carries the largest residual bias in the catalog (+0.494 s mean across 5 matched benchmarks per CLAUDE.md April 27 entry); and the underlying physics — pressure-wave round-trip, tuned RPM, Gaussian band geometry — is genuinely interesting and not well-explained anywhere else in the Indian moto-content space.

This post is a physics-explainer pillar, not a bike-comparison piece. Strategic value:

- Long-tail SEO on a non-saturated topic ("how a 2 stroke expansion chamber works" + variants).
- Internal-link hub for any future 2T bike comparison or RX100 / RD350 deep-dive.
- Demonstrates the simulator handles 2T physics rigorously, which differentiates MotoQuant from generic motorcycle-spec sites.

## Target keywords

Primary:

- `two stroke expansion chamber physics`
- `2T expansion chamber tuning`
- `how 2 stroke pipe works`

Secondary / long-tail:

- `RX100 expansion chamber`
- `RD350 expansion chamber`
- `tuned RPM 2-stroke`
- `YPVS RC valve powervalve`
- `Indian 2 stroke drag racing`

## Expected traffic

- Cold-launch organic: ~50–150 visits/month within 90 days. The Indian 2T enthusiast crowd is small but extremely engaged, and there is little competition on the long-tail "physics" framing.
- Internal traffic from the blog index, the existing R15 / launch-physics posts, and the /bikes catalog (2T bike pages should link back to this post once individual bike pages support inline blog references).
- Potential Reddit / xBhp / Team-BHP traction if shared into r/Motorcycles, r/2StrokeNation, or India-specific 2T owner groups.

## Internal-link plan (audited)

Outbound links from this post:

1. `/blog/how-the-motoquant-physics-engine-works` — referenced for the 15-sub-model architecture and the 2T torque-curve helper.
2. `/blog/the-physics-of-a-perfect-launch` — referenced for clutch/launch interaction differences vs 4T.
3. `/blog/why-your-r15-wont-hit-14s` — referenced as the small-cc 4T counterpart.
4. `/blog/how-to-tune-for-aamby-valley-in-november` — referenced for the venue context used in the simulation numbers.
5. `/bikes` — catalog browse (mentions the 20 2T entries explicitly).
6. `/pricing` — Free vs Pro tier link.
7. `/simulator?bike=yamaha-rx100` — CTA link with prefilled bike.

Inbound links (other posts that already exist and could be retroactively edited to link IN to this post in a future content pass): the R15 post and the physics-engine post both reference 2T physics in passing and would benefit from a "for the deep dive on 2-stroke pipe theory, see X" callout. Not edited in this pass to keep the diff minimal.

## Sources cited (all from the repo, NOT from training data)

| Claim | Source |
|---|---|
| `band_lo` / `band_hi` / `baseline` Gaussian parameters and per-cylinder branches | `motoquant/defaults.py::_synthetic_2stroke_torque_curve` (lines 172–266) |
| RX100 spec: 11 hp @ 7,500 rpm, 10.5 Nm @ 6,500 rpm, 7,500 rpm tuned, piston-port, no powervalve, 4-speed [2.833, 1.705, 1.238, 1.000], 14F/50R 428 chain, 100 kg dry, Cd 0.70, frontal area 0.52 m² | `motoquant/scraper/known_bikes.py::YAMAHA_RX100_1985` (lines 9951–9989) |
| RD350 1974 spec: 39 hp @ 7,500 rpm, 36 Nm @ 6,500 rpm, twin-cylinder, no powervalve, 6-speed | `motoquant/scraper/known_bikes.py::YAMAHA_RD350_1974` (lines 9791–9829) |
| RGV250 VJ22 spec: 62 hp @ 10,500 rpm tuned, AETC powervalve | `motoquant/scraper/known_bikes.py::SUZUKI_RGV250_VJ22_1992` (lines 10111–10135) |
| RD500LC spec: 87 hp @ 9,500 rpm tuned, 4-cyl V4, YPVS on all four cylinders | `motoquant/scraper/known_bikes.py::YAMAHA_RD500LC_1984` (lines 9871–9909) |
| 2-stroke cluster validation: N=5 matched benchmarks, mean \|Δ\|=0.848 s, bias=+0.494 s | CLAUDE.md April 27, 2026 entry (final cluster metrics block) |
| 2T staging: launch_rpm = max(peak_torque_rpm, tuned_rpm) capped at 0.96 × redline | CLAUDE.md April 27 entry (engine-RPM floor-clamp section) and `motoquant/scraper/importer.py::spec_to_bike_config` |
| 13 dedicated expansion chambers across 7 sub-categories of 41 2T parts | CLAUDE.md "Two-Stroke Expansion + Catalog + Compat Filter (April 21, 2026)" block |
| Akrapovic / Powertronic / sport-tire cost-per-tenth comparison values | `web/app/blog/hero-xtreme-200s-4v-quarter-mile-physics/page.js` (the May 1, 2026 pricing refresh values) |

No magazine prose was quoted verbatim. The Cycle World 1973 RD350 reference is a citation, not a quotation. No fabricated benchmark numbers.

## Files touched (full paths — for postflight commit)

- `/tmp/mq-session-1778221833-619/repo/web/app/blog/how-a-2-stroke-expansion-chamber-actually-works/page.js` (new, ~330 lines after prettier)
- `/tmp/mq-session-1778221833-619/repo/web/app/blog/how-a-2-stroke-expansion-chamber-actually-works/layout.js` (new, ~40 lines after prettier)
- `/tmp/mq-session-1778221833-619/repo/web/app/blog/page.js` (modified — added new post to the top of POSTS array; prettier reformatted the file as a side effect)
- `/tmp/mq-session-1778221833-619/repo/web/app/sitemap.js` (modified — added the new slug; prettier reformatted)
- `/tmp/mq-session-1778221833-619/repo/reports/content_how-a-2-stroke-expansion-chamber-actually-works_2026-05-08.md` (this report)

## Validation gates passed

- `npx prettier --write` on all 4 touched JS files — clean.
- AI-tell phrase scan (delve / let's dive / tapestry / etc.) — zero hits.
- Manual re-read for fabricated benchmarks — every numerical claim is sourced from `motoquant/defaults.py`, `motoquant/scraper/known_bikes.py`, CLAUDE.md, or an existing blog post's pricing section.
- Metadata + structured-data (`articleSchema` + breadcrumb in layout) shape mirrors `web/app/blog/the-physics-of-a-perfect-launch/page.js` and `web/app/blog/hero-xtreme-200s-4v-quarter-mile-physics/page.js`.
- One inline data-table (5-bike tuned-RPM comparison).
- Three H2 sections minimum — actual count: 8 H2 sections plus lead.
- Internal links: 4 to other blog posts, 1 to /bikes, 1 to /pricing, 1 to /simulator with prefilled `?bike=yamaha-rx100` query.
- Currency: ₹ throughout; metric units (km/h, m/s, mm) throughout.

## One-line commit message

`feat(blog): publish 2-stroke expansion chamber physics explainer (~2.3k words, RX100/RD350/RGV250 case studies)`
