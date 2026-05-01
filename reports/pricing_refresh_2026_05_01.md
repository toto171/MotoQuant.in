# Pricing Refresh — May 1, 2026

**Run type:** Daily improvement loop, Friday focus = pricing refresh.

## Targets researched (12 parts)

7 newest parts (drag-prep specialty, Apr 30 formula-priced) + 5 flagship anchor parts likely to have moved since Apr 27 audit.

## Outcome — 4 high-confidence updates applied

| ID | Brand | Model | Before (₹) | After (₹) | Δ | Source |
|----|-------|-------|-----------:|----------:|--:|--------|
| 56 | Akrapovic | Racing Full System Hayabusa | 185,000 | 238,000 | +29 % | Riderz Planet direct listing |
| 87 | K&N | K&N Drop-In Air Filter | 6,500 | 4,300 | -34 % | Store4Riders ₹3,790 / Moglix ₹4,854 mid |
| 240 | Akrapovic | Slip-On Line Duke 390 / RC 390 | 48,000 | 90,000 | +88 % | Superbikestore.in ₹84,802 + Quora ₹100k mid |
| 561 | DID | 525 VX3 Race Chain — 120L | 6,500 | 9,200 | +42 % | Motousher 116-link ₹9,100 / 122-link ₹9,300 interpolated |

All four had `last_price_check` stamped to `2026-05-01`. Total parts in DB unchanged at **562**.

## Outcome — 8 parts deferred (insufficient public data)

| ID | Brand | Model | Reason |
|----|-------|-------|--------|
| 49 | Dynojet | PCVI Stage 1 Universal | "PCVI Stage 1" terminology ambiguous on Indian retailers; current ₹16,000 plausible |
| 178 | Akrapovic | Full System Panigale | SKU mapping ambiguous — Superbikestore's ₹1,050,000 is Evolution Line Titanium 2025; Racing Line stainless is ~₹536,700; current ₹190,000 in DB labelled generically. Needs clarification of which tier the catalog entry represents before bumping. Per CLAUDE.md hygiene: honest > apparent accuracy. |
| 556 | Schnitz Racing | 8" Hayabusa Gen 1 swingarm | Schnitz catalog has no public USD MSRP visible to web search snippets; would need direct vendor contact |
| 557 | Schnitz Racing | 10" Hayabusa Gen 2 swingarm | Same — Schnitz pricing requires direct query |
| 558 | DME Racing | 12" ZX-14R swingarm | DME built-to-order, no fixed MSRP |
| 559 | Brock's Performance | 14" Pro Mod swingarm | Not surfaced on Brock's current catalog; likely custom/discontinued — needs vendor contact |
| 560 | EK | 428 Heavy-Duty Drag Chain | EK 428 SR available on Amazon US / eBay but no India retailer pricing found |
| 562 | RK | 530 PRODR Drag Chain | RK PRODR is professional-tier, not stocked by Indian commodity retailers |

The 4 swingarm rows + the 2 specialty drag chains (560/562) carry their original Apr 30 landing-cost-formula INR estimates. They're flagged for a follow-up pass once a partnership with Pune/Narhe drag shops can yield real Indian distributor pricing.

## Headline-stats drift cleanup (bonus)

`scripts/audit_headline_stats.py` flagged 3 stale "555 parts" references from yesterday's catalog expansion (555 → 562). Patched in the same commit:

- `web/app/page.js:322` — landing-page parts tile
- `web/app/features/page.js:57,59` — features-page parts subtitle + body
- `README.md:86` — Phase 2 stats blurb

Also corrected the OEM-fitment count in README.md (846 → 861) which had the same drift origin. Audit re-run reports clean.

## Sources cited

- [Motousher — DID 525 VX3 116-link](https://www.motousher.com/products/did-chain-525-pitch-116-links)
- [Motousher — DID 525 VX3 122-link](https://www.motousher.com/products/did-chain-525-pitch-122-links-vx3)
- [Riderz Planet — Akrapovic Racing Line Hayabusa](https://www.riderzplanet.com/products/akrapovic-racing-line-full-exhaust-system-for-gsx-1300r-hayabusa)
- [Superbikestore — Akrapovic Slip-On Duke 390](https://superbikestore.in/products/akrapovic-slip-on-exhaust-for-ktm-duke-390)
- [Store4Riders — K&N Air Filters](https://www.store4riders.com/brands/k&n-bike-air-filter)
- [Moglix — K&N Air Filter](https://www.moglix.com/brands/k&n/automotive/automotive-filters/air-filter/216170100)

## Validation

Reference baselines preserved exactly to 4 decimals: K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s. Focused-test subset 239/239 green (test_scraper, test_validation, test_two_stroke, test_compatibility, test_category_dispatch, test_pricing). One pre-existing failure in `test_catalog_integration::test_rsv4_no_panigale_leak` unchanged from yesterday's carry-forward. ROI smoke-test (`analysis roi --bike-id 11 --part-ids 56`) confirms the new ₹238,000 Akrapovic Hayabusa price flows correctly through `compute_parts_roi` — Δ ET 0.832s, cost-per-tenth ₹28,622.

## Carry-forward for next pricing pass

1. Resolve Part 178 (Akrapovic Panigale) SKU ambiguity — confirm whether DB entry represents Evolution Line Titanium (top, ~₹1,050,000) or Racing Line Stainless (mid, ~₹536,700).
2. Establish Pune/Narhe drag-shop partnership pipeline so swingarm + specialty chain pricing has a non-formula source.
3. Pass-2 candidates: high-volume Indian commuter parts (Pulsar exhausts, Apache slipper clutches, R15 ECU flashes) — 4-day-old prices but high catalog visibility.
