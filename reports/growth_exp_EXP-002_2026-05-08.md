# EXP-002 — Pricing-page Pro CTA copy A/B test

**Date launched:** 2026-05-08 (Friday)
**Page:** `web/app/pricing/page.js` (motoquant.in/pricing)
**Element:** Pro-tier subscribe CTA button copy
**Status:** Live (default OFF — control unchanged)

## Hypothesis

Visitors who reach `/pricing` have already cleared the awareness funnel —
they know what MotoQuant does and are evaluating commitment. The current Pro
CTA "Subscribe to Pro" frames the click as an open-ended subscription
commitment, which triggers loss-aversion at the most price-sensitive moment.

The risk-reversal exists on the page (the "7-day money-back guarantee" line
sits directly under the button) but it is one font-size smaller, lower
contrast, and below the action — visitors don't read top-to-bottom on a
pricing card, they fixate on price → button → click. The safety net is
present but invisible.

Variant B — "Start Pro · 7-day refund" — reframes the action as a
low-commitment trial start and pulls the risk-reversal up onto the button
itself, where the eye is already focused. "Start" replaces "Subscribe"
(verb-of-beginning vs verb-of-binding) and "7-day refund" is shorter and
more concrete than "money-back guarantee".

Expected lift: pro_checkout_init / pricing_visitor up ≥15% on Variant B,
with no >5% drop in Razorpay checkout-completion rate (we want trial
intent, not abandoned-cart inflation).

## Variant copy

| Variant | Pro CTA text |
|---|---|
| A (control, default) | `Subscribe to Pro` |
| B (`?variant=B`) | `Start Pro · 7-day refund` |

The Studio CTA ("Subscribe to Studio") and Free CTA ("Start free") are held
constant — single-variable test discipline. The "7-day money-back guarantee"
caption below the button is also unchanged in both variants (so Variant B is
strictly additive — risk-reversal moves on-button without removing the
backup signal underneath).

Both variants:

- Serve the same canonical URL `/pricing`.
- Hit the same `POST /api/subscriptions/checkout` endpoint with the same
  `{tier: "pro", billing_cycle}` payload.
- Render the same h1 ("Simple, honest pricing.") and meta description.
- Show the same price (₹499/mo monthly · ₹4,999/yr yearly).

SEO is unaffected — search engines and uncrawled visitors both see Variant A
in the static SSR output.

## Implementation notes

- Single point-of-change: `web/app/pricing/page.js`.
- `useSearchParams()` from `next/navigation` reads `?variant=B` at render
  time.
- Variant flag is purely client-side — the static-rendered HTML the crawler
  sees is always Variant A.
- The Pro `<button>` carries `data-exp="EXP-002"` + `data-variant={proCtaVariant}`
  so any future analytics layer (PostHog / GA4) can attribute click events
  to the variant arm without further wiring.
- Net change: ~13 LOC in `pricing/page.js`.

## Page-conflict check

EXP-001 is live on `web/app/page.js` (landing hero CTA). EXP-002 is on
`web/app/pricing/page.js`. Different pages → no rule violation against
"never start a 2nd experiment on the same page while the first is live".
EXP-001 has not yet hit min_sample (200) but the two pages are distinct
funnel stages so the variant assignments don't interfere.

## Primary metric

**pro_checkout_init_clicks / pricing_page_visitor** — measured via
`data-exp="EXP-002"` button click vs. unique visitor counter on
`/pricing`. Until analytics is bootstrapped (top-3 priority item), counts
are sampled by manually distributing the two URLs:

- Control: `https://www.motoquant.in/pricing`
- Variant B: `https://www.motoquant.in/pricing?variant=B`

## Secondary metrics

- **pro_cta_click_through_rate** — sanity check: are people clicking at all?
- **razorpay_checkout_completion_rate** — guards against false positive
  where Variant B inflates click intent but doesn't translate to actual
  paid conversions.
- **studio_cta_cannibalisation_rate** — does refund-anchored Pro copy
  steal click-intent from the higher-tier Studio plan? If Studio clicks
  drop >10%, Variant B is a tier-mix loss even if Pro clicks lift.
- **pricing_page_bounce_rate** — does the variant change time-on-page?

## Sample size & when-to-stop

- **Min samples per arm:** 200 unique pricing-page visitors.
- **Expected effect size:** +15% on primary metric. With baseline pro CTR
  estimated at ~5% (industry SaaS pricing pages), n=200 per arm gives ~80%
  power to detect a 15% relative lift at p<0.05 (one-tailed Z-test on
  proportions).
- **Decision rule:**
  - Ship Variant B as new control if pro_checkout_init/visitor lifts
    ≥15% with p<0.05 over ≥200 samples per arm AND
    razorpay_checkout_completion drops <5%.
  - Roll back if Studio cannibalisation >10% (refund-anchor stealing
    higher-tier intent).
  - Hold both variants live if results inconclusive after 200 samples;
    re-evaluate at 500 samples.
  - No decision before 200 samples per arm — even if the early read
    looks dramatic.

## Files touched

- `web/app/pricing/page.js` — added `useSearchParams` import, variant
  state, button copy resolver, `data-exp` / `data-variant` attributes on
  Pro CTA.
- `data/growth_experiments.json` — appended EXP-002 entry.
- `reports/growth_exp_EXP-002_2026-05-08.md` — this report.
