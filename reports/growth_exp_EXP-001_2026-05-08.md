# EXP-001 — Hero CTA copy A/B test

**Date launched:** 2026-05-08 (Friday)
**Page:** `web/app/page.js` (motoquant.in landing hero)
**Element:** Primary hero CTA button
**Status:** Live (default OFF — control unchanged)

## Hypothesis

Indian-market visitors landing on motoquant.in don't try the simulator because
the hero CTA copy doesn't tell them what they'll get. The current "Try the
simulator" is a generic verb-noun that puts the burden on the visitor to
imagine the outcome. Variant B replaces it with a verb-result CTA that names
the concrete outcome — "See your bike's quarter-mile ET" — which:

- Tells the visitor what they will receive (quarter-mile ET, the literal
  product output).
- Uses second-person ("your bike") to localise instantly without a
  geo-detection layer.
- Lands in the drag-racing vocabulary the target community already uses.

Expected lift: simulator-runs / landing-visitor up ≥15% on Variant B.

## Variant copy

| Variant | Hero CTA text |
|---|---|
| A (control, default) | `Try the simulator` |
| B (`?variant=B`) | `See your bike's quarter-mile ET` |

Both variants serve the same canonical URL, the same `<a href="/simulator">`,
the same `<h1>` ("The physics of faster."), and the same meta description.
SEO is unaffected — search engines and uncrawled visitors both see Variant A.

## Implementation notes

- Single point-of-change: `web/app/page.js`.
- `useSearchParams()` from `next/navigation` reads `?variant=B` at render time.
- Variant flag is purely client-side, so the static-rendered HTML the crawler
  sees is always Variant A.
- The `<Link>` carries `data-exp="EXP-001"` + `data-variant={ctaVariant}` so
  any future analytics layer (PostHog / GA4) can attribute click events to
  the variant arm without further wiring.
- Net change: ~12 LOC in `page.js`.

## How to read results

Until GA4 / PostHog is bootstrapped (one of the standing top-3 priorities),
results need to be sampled by manually distributing the two URLs:

- Control arm: share `https://www.motoquant.in/`
- Variant arm: share `https://www.motoquant.in/?variant=B`

Track in whatever analytics is available:

1. **Primary:** simulator runs / unique landing visitor per arm.
2. **Secondary:** hero CTA click-through rate, bounce rate, time-to-first-run.

Once analytics is live, switch to a 50/50 random assignment via a
`Math.random() < 0.5` flip in the same `useSearchParams()` block — same code
shape, no further design work.

## Decision criteria

- **Ship Variant B as new control** if simulator-runs/visitor lifts ≥15%
  with p<0.05 over ≥200 samples per arm.
- **Roll back** if bounce rate increases >10% or CTR decreases.
- **No decision before 200 samples per arm.**
- Re-evaluate at the next Friday growth-experiments slot.
