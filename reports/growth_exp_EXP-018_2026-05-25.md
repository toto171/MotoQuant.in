# EXP-018 — Hero Subhead Framing: Physics-First vs Indian-Community-First

**Started:** 2026-05-25  
**Page:** Landing hero (`https://motoquant.in/`)  
**Element:** Hero subhead paragraph (below h1 "The physics of faster.")  
**Flag:** `?exp18=B` (independent of EXP-001's `?variant=B`)

---

## Hypothesis

The current hero subhead opens with methodology: "A first-principles drag simulator for India's motorcycle drag-racing community." The visitor must infer that this tool is for them from a product-category label, not from a direct statement of ownership and outcome.

Variant B flips the order: "Your bike. Your strip. Your quarter-mile ET" — asserts the visitor's ownership of the result in the first six words, then justifies it with the same accuracy/catalog/venue specifics. Same information, different sequence.

**Predicted mechanism:** Visitors scanning the hero on mobile read the first 10 words and decide whether to scroll. "A first-principles" signals method; "Your bike. Your strip." signals belonging. The Indian drag community skews toward outcome-seekers (they already know they want an ET), not methodology-vetters (who will find the whitepaper after first engagement). If this is correct, B should reduce the "is this for me?" moment and shorten time-to-first-sim-run.

---

## Variant Copy

**Control (A):**
> A first-principles drag simulator for India's motorcycle drag-racing community. 790 bikes, 563 parts, 20 venues — tuned to within ±0.05s of real-world ETs on the litre-class.

**Variant B:**
> Your bike. Your strip. Your quarter-mile ET — predicted to within ±0.05s on the litre-class. 790 Indian and global bikes, 563 parts with INR pricing, Aamby Valley to MMRT.

---

## What Changed

- Single file: `web/app/page.js`
- Added `exp18Variant` resolver in `HomePageInner()` (reads `?exp18=B`, falls back to `'A'`)
- Subhead `<p>` conditionally renders control or variant copy
- Both arms carry `data-exp="EXP-018"` and `data-variant` for analytics
- h1, both CTA buttons, pill tags, all below-hero sections: unchanged

---

## Implementation Notes

`HomePageInner()` already calls `useSearchParams()` for EXP-001 and is already inside `<Suspense fallback={null}>` in the default export. No new Suspense boundary required. Uses `?exp18=B` (not `?variant=B`) so EXP-001 and EXP-018 arms are orthogonal — a visitor can be in any of the four arm combinations without contamination.

SEO impact: none. The `<p>` element is not indexed as a heading; the meta description (which mirrors the control subhead) is unchanged; canonical URL is unchanged.

---

## Primary Metric

`simulator_runs / landing_visitor`

Measured as: unique simulator-run events fired on `/simulator` during a session that started on `/` with the respective `?exp18` param value.

## Secondary Metrics

| Metric | Rollback trigger |
|---|---|
| `landing_page_bounce_rate` | +10% vs control arm |
| `hero_cta_click_through_rate` | N/A (tracked for interaction with EXP-001) |
| `time_on_page_s` | Informational |
| `scroll_depth_past_stats_strip_pct` | -10% would indicate B copy is not holding below-fold attention |

---

## Expected Lift Range

Based on analogous copy rewrites in the SaaS conversion literature (methodology-first to outcome-first on hero subheads for technical products targeting practitioners): +8% to +22% on primary metric. The Indian-specific specificity ("Aamby Valley to MMRT", "INR pricing") adds localisation that is absent from the control, which may independently add +5-10% on Indian-origin traffic. Conservative mid-point: +12%.

---

## Decision Criteria

- **Ship B as new control:** lift ≥15%, p<0.05, n≥200 per arm, bounce rate not up >10%
- **Roll back:** bounce rate up >10% OR scroll depth past stats strip down >10%
- **No decision before:** 200 samples per arm
- **Interaction check:** analyse EXP-001 and EXP-018 arms independently before declaring any interaction effect (four-cell breakdown: A/A, A/B, B/A, B/B)

---

## How to Measure

1. Tag sessions arriving at `/?exp18=B` with `exp18=B`; all others get `exp18=A`
2. Count `simulator_run` events per session grouped by `exp18` arm
3. Run a two-proportion z-test on `runs / sessions` at ≥200 sessions per arm
4. Secondary: compare bounce rate and scroll depth between arms with the same test

---

## Files Touched

- `web/app/page.js` — variant flag + conditional subhead rendering
- `data/growth_experiments.json` — EXP-018 entry appended
- `reports/growth_exp_EXP-018_2026-05-25.md` — this file
