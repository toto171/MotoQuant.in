# Content Report — Royal Enfield Continental GT 650 Quarter-Mile Physics

- **Date:** 2026-05-18
- **Slug:** `re-continental-gt-650-quarter-mile-physics`
- **URL:** `https://motoquant.in/blog/re-continental-gt-650-quarter-mile-physics`
- **Word count (CONTENT prose, excluding JSX/tables):** ~1,920 words
- **Read time:** 10 min

## Target keyword and SEO intent

- **Primary keyword:** "Continental GT 650 quarter mile" (low-medium volume, low competition in India)
- **Secondary keywords:**
  - "Royal Enfield 650 twin drag time"
  - "Continental GT 650 vs Interceptor 650"
  - "Continental GT 650 top speed"
  - "GT 650 mods Indian price"
- **Intent:** Informational + commercial — owner/buyer comparing 650-class twins, wanting a concrete drag-strip number plus a mod prioritisation.
- **Indian context:** Pricing in ₹, conditions referenced to Aamby Valley, Royal Enfield is an Indian manufacturer with high domestic search volume on this model family.

## Expected traffic

- Conservative 90-day estimate: **80-150 monthly organic sessions** once indexed.
- GT 650 + Interceptor 650 together are RE's best-selling 650cc lineup in India; cluster of related long-tail keywords (e.g. "GT 650 drag race", "GT 650 exhaust ET gain", "GT 650 sprocket tuning") should compound traffic over 6-12 months.
- Internal pipeline: this post links into `/simulator?bike=re-continental-gt-650` which should convert at the standard blog-to-simulator rate.

## Internal-link plan

| Outbound link | Anchor | Reason |
|---------------|--------|--------|
| `/blog/pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics` | "Pulsar NS200 vs Apache RTR 200 4V" | Same methodology, smaller cluster |
| `/blog/hayabusa-vs-zx-14r-which-is-faster` | "Hayabusa vs ZX-14R" | Counterweight at the other end of catalog |
| `/blog/how-the-motoquant-physics-engine-works` | "How the MotoQuant Physics Engine Works" | Methodology / authority |
| `/blog/how-to-tune-for-aamby-valley-in-november` | "How to Tune for Aamby Valley in November" | Venue conditions context |
| `/bikes` | "Browse the full bike catalog" | Catalog discovery |
| `/pricing` | "MotoQuant Pricing" | Commercial-tier CTA |
| `/simulator?bike=re-continental-gt-650` | "Run sim →" | Primary conversion CTA |

## Sources for factual claims

All sim numbers anchored against documented values:

- **Spec data** (47 hp / 52 Nm / 182 kg dry / 16F/43R sprockets / [3.071, 2.056, 1.583, 1.292, 1.125, 1.000] ratios / Cd 0.68 / frontal area 0.46 m²): `motoquant/scraper/known_bikes.py:1787` `RE_CONTINENTAL_GT_650` spec block.
- **Cluster metrics** (mid-twin-500-700 N=14, mean|Δ|=0.615s, bias=-0.133s): CLAUDE.md April 27 evening session metrics summary.
- **MCN Interceptor 650 14.2s @ 162 km/h reference:** documented in BENCHMARKS list (RE 650 cluster), used as a real-world anchor.
- **Peer-bike sim ETs** (RS 660 ~11.4s, Ninja 650 ~13.0s, MT-07 ~12.4s): consistent with the mid-twin-500-700 cluster validation sweep documented in CLAUDE.md April 27 metrics block.
- **Indian pricing** (₹2.95L on-road GT 650; ₹35k SuperTrapp slip-on; ₹95k S&S Cycle full system; ₹38k Power Commander V flash; ₹6.5k K&N filter; ₹7.2k Pirelli Diablo Rosso II rear): pulled from the April 27 WS-D pricing audit (`reports/pricing_audit_2026_04_27.{json,md}`) and verified against `pricing_refresh.py` retailer-URL ladder.
- **May 2026 clutch over-clutching rewrite** (cluster MAE 1.07 → 0.62 s): documented in CLAUDE.md April 27 evening + carry-forward into May calibration entries.

## Validation checklist

- [x] No AI-tell phrases ("delve into", "harness", "navigating the complex world of", "in today's fast-paced world", "leveraging cutting-edge", "unleash the power of", "comprehensive guide to...")
- [x] Opening hook has a specific number within first 30 words (14.1s, 158 km/h trap, 47 hp / 52 Nm / 182 kg, 78 mm bore)
- [x] At least 3 H2 sections (7 actual H2s)
- [x] Inline data-table (3 tables: stock-tune numbers, peer comparison, cost-per-tenth)
- [x] Internal links: 4 to other blog posts, 1 to `/bikes`, 1 to `/pricing`, 1 to `/simulator?bike=...`
- [x] CTA pointing to `motoquant.in/simulator`
- [x] All prices in ₹, all speeds in km/h
- [x] `<StructuredData type="article" ...>` block in page.js mirroring existing posts
- [x] layout.js with breadcrumb structured data, matching neighbouring posts
- [x] Sitemap updated with new slug
- [x] Blog index (`web/app/blog/page.js`) prepended with the new post

## Notes for future iterations

- Once an Indian Autos Mag or BikeWale instrumented quarter-mile lands on the GT 650, refresh the "sim-only" caveat with a real-world delta.
- The 16F/43R sprocket combo in `known_bikes.py` differs slightly from the Interceptor's 16F/46R — worth a separate technical-deep-dive comparing the two on identical conditions to isolate gearing as the sole variable.
- If S&S Cycle releases an official India-distributor price update, refresh the ₹95,000 number against the live retailer.
