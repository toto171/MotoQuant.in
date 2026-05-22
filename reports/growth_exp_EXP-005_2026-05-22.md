# Growth Experiment EXP-005 — Pro Tier Tag-Line Copy

**Date:** 2026-05-22  
**Page:** `/pricing`  
**Element:** Pro tier tag-line (the 14-word descriptor directly under the ₹499 price)  
**Flag:** `?exp5=B` (independent of EXP-002's `?variant=B`)  
**Status:** live

---

## Hypothesis

Visitors who reach `/pricing` after running a free simulation already know they want more capability. The question they are answering on the pricing page is not "should I care about this product?" — they already clicked through from the simulator. The question is "will ₹499/month tell me something I can act on at the track?"

The current Pro tag line — *"Everything you need to go faster."* — is aspirational positioning. It does not answer that question. It could describe a protein bar, a riding course, or a workshop dyno session. A visitor reading it has to scroll to the feature table and mentally construct the answer themselves.

Variant B replaces it with a line that names the three capabilities unique to Pro that are absent in the Free tier and that directly support a purchase decision at the drag strip: unlimited simulations, ROI per part (which tells you the cost-per-tenth-of-a-second for each mod), and the build optimizer. The closing clause — "know what each mod does before you buy it" — frames the ₹499 not as a subscription cost but as money saved on wrong parts.

If the specificity reduces the "is this worth it?" pause, `pro_checkout_init_clicks / pricing_page_visitor` should rise.

---

## Variant copy

| Arm | Tag-line under ₹499 price |
|-----|--------------------------|
| A (control) | *Everything you need to go faster.* |
| B (variant) | *Unlimited sims, ROI per part, build optimizer — know what each mod does before you buy it.* |

No other copy changes. The Pro button (EXP-002), the feature table, the FAQ, the Studio card, and the page h1 are identical on both arms.

---

## Implementation

`useSearchParams()` in `PricingPageInner()` reads `?exp5=B`. The function is already inside the existing `<Suspense fallback={null}>` wrapper (added for EXP-002), so no new Suspense boundary was needed. The variant is derived from a separate `exp5` param so EXP-002 and EXP-005 can be toggled independently: `?variant=B&exp5=B` activates both; `?exp5=B` alone activates only this experiment.

The `<p>` element carrying the tag line has `data-exp="EXP-005"` and `data-variant={exp5Variant}` for analytics attribution. Control renders byte-identically at the default URL.

---

## Expected effect size and decision criteria

The pricing page is low-traffic relative to the landing page — a conservative estimate for this community at current scale is 30–60 pricing page visitors per week. At that rate, 200 samples per arm takes roughly 7–14 weeks.

Decision threshold: ship Variant B as the new control if `pro_checkout_init / pricing_visitor` lifts ≥15% with p < 0.05 over ≥200 samples per arm. Roll back if `razorpay_checkout_completion` drops >5% (specificity should convert intent, not inflate abandon-rate). Monitor `studio_cta_cannibalisation_rate` — if Studio conversion also rises, the effect is positive differentiation; if only Studio cannibalises Pro with no net gain, that signals the variant is shifting tier preference rather than lifting overall intent.

The 15% threshold is chosen because it represents a meaningful revenue lift (₹499 × 0.15 × n subs) while being large enough to clear measurement noise at this sample size. A 5–10% lift that doesn't clear p < 0.05 at 200 samples is inconclusive, not a roll-back signal.
