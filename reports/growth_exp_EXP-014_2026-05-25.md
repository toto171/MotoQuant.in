# EXP-014 — /docs/getting-started bottom simulator CTA presence test

- **Started:** 2026-05-25
- **Page:** `/docs/getting-started`
- **Element:** bottom CTA card (injected above the "Next" nav cards at end of article)
- **Type:** Presence test (control = no CTA; variant = single grounded CTA card)
- **Flag:** `?variant=B`
- **Default:** A (control)
- **Status:** live

## Hypothesis

Visitors who finish all 5 steps of `/docs/getting-started` have just absorbed a
step-by-step walkthrough of exactly how to run a simulation — they know what to
do, where to do it, and what output they will see. Yet the page ends with two
"Next" nav cards both pointing deeper into docs (`/docs/physics`,
`/docs/validation`), with no direct path to `/simulator`. The pre-EXP-014 page
has zero simulator CTAs anywhere.

The getting-started cohort is at peak procedural readiness immediately after the
last step. Adding one CTA card before the Next nav block gives that readiness a
concrete next action and should convert reading intent into simulator runs without
displacing the two existing docs nav cards (which remain on both arms).

> **Failure mode targeted:** user reads 5 steps about how to run a simulation,
> then navigates away because the page provides no affordance to act on what they
> just read.

**Falsifiable:** if adding the CTA card does not lift `simulator_runs /
getting-started-visitor` by ≥15%, the readiness hypothesis is wrong — either
the cohort already knows the path to `/simulator` and does not need an in-page
affordance, or they are reading purely as reference and have no run-intent at
this moment.

## Variants

| Arm | Description |
|-----|-------------|
| **A — control** | Pre-EXP-014 behaviour: article ends, Next nav cards follow, SiteFooter follows. Hidden `<span data-exp="EXP-014" data-variant="A">` sentinel for analytics. |
| **B — variant** | A glass card injected immediately above the Next nav cards. Headline: `"You've read the steps. Now run a sim."` Subhead: `"Pick your bike, set your conditions, and see your quarter-mile ET — same engine you just read about. No account required."` Brand-orange `Run a sim →` button → `/simulator`. Next nav cards remain below the card on variant B — additive only. |

**Single-variable rule:** copy + href fixed on variant B. The only thing that
varies is the presence of the card. Copy refinement is a separate follow-up
experiment if B wins.

## Primary metric

`simulator_runs_per_getting_started_visitor`

Attribution via `data-exp="EXP-014"` + `data-variant` + `data-cta-link=
"getting-started-bottom"` on the Link element.

## Secondary metrics

| Metric | Guard-rail purpose |
|--------|-------------------|
| `getting_started_bottom_cta_click_through_rate` | Sanity-check the CTA is reachable and being seen |
| `getting_started_docs_physics_ctr_delta` | Cannibalisation guard — card must not displace deeper docs reading |
| `getting_started_docs_validation_ctr_delta` | Same |
| `getting_started_page_bounce_rate` | Roll back if rises >10% (CTA reads premature) |
| `simulator_page_first_run_completion_rate_from_getting_started_referrer` | Roll back if drops >10% vs site-wide baseline |

## Minimum sample

200 per arm before any decision.

## Decision criteria

Ship variant B as new control if:

1. `simulator_runs / getting-started-visitor` lifts **≥15%** with **p<0.05**
   over **≥200 samples per arm**, AND
2. `simulator_page_first_run_completion_rate_from_getting_started_referrer` does
   not drop more than 10% vs site-wide baseline (intent from this cohort should
   be high — a completion-rate drop signals the CTA is recruiting anxious or
   confused clicks rather than ready-to-run intent).

Roll back if:

- `getting_started_page_bounce_rate` rises >10%, OR
- `getting_started_docs_physics_ctr` + `getting_started_docs_validation_ctr`
  together drop >25% in absolute terms (the card must not displace the deeper
  docs path — both downstream nav cards should retain most of their CTR on
  variant B).

## Implementation

Files touched:

- `web/app/docs/getting-started/RunSimCta.js` (new, 62 lines) — `'use client'`
  component. `useSearchParams()` inside `RunSimCtaInner` directly (no inner
  wrapper needed — the `<Suspense>` boundary is at the call site in `page.js`).
  Variant A: hidden sentinel span. Variant B: glass card with headline, subhead,
  brand-orange Link.
- `web/app/docs/getting-started/page.js` (3-line edit) — added `Suspense`
  import, `RunSimCta` import, mounted `<Suspense fallback={null}><RunSimCta />
  </Suspense>` immediately before the `{/* Next steps */}` block.

Untouched:

- `web/app/docs/layout.js` — DocsLayout sidebar, reference baselines sidebar
  widget, metadata, canonical `https://motoquant.in/docs`. SEO surface unchanged.
- All 5 `<Step>` sections, the Option A/B/C guide sections, the chart-reading
  section. Variant B is purely additive.
- The two "Next" nav cards (Physics Whitepaper, Validation Data) — present and
  unchanged on both arms.

## SEO safety

- Same canonical URL (`/docs/getting-started`)
- Same `<h1>Your First Simulation</h1>`
- Same metadata, OG tags (served from `export const metadata` in the server component)
- `page.js` remains a server component; only `RunSimCta.js` is `'use client'`
- Suspense fallback is `null`, so SSR/SSG markup is byte-identical to
  pre-EXP-014 on both arms

## Page-conflict audit (no overlap)

| EXP | Page |
|-----|------|
| EXP-001 | landing hero (`/`) |
| EXP-002, EXP-005 | `/pricing` |
| EXP-003 | `/simulator` |
| EXP-004 | `/blog/the-physics-of-a-perfect-launch` |
| EXP-006 | `/blog` index |
| EXP-007 | `/login` |
| EXP-008 | `/features` bottom |
| EXP-009 | `/bikes` catalog grid |
| EXP-010 | `/blog/pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics` |
| EXP-011 | `/bikes/[id]` top CTA |
| EXP-012 | `/about` |
| EXP-013 | `/whitepaper` |
| **EXP-014** | **`/docs/getting-started` (this experiment)** |

`/docs/getting-started` had zero live experiments prior to today.

## Non-overlap with today's other experiments

- EXP-011 (today): `/bikes/[id]` — different page, copy test on an existing CTA.
- EXP-012 (today): `/about` — different page, presence test on the about page.
- EXP-013 (today): `/whitepaper` — different page, copy test on the terminal CTA.
- EXP-014 (this): `/docs/getting-started` — presence test, first experiment on
  this page. No element overlap with any of the above.

## Follow-ups if B wins (separate experiments, not bundled)

- (a) Copy retest: `'Run a sim →'` vs `'Run my first sim →'` on the button — the
  procedural-confirmation framing (`first sim`) may outperform the generic verb on
  a how-to-guide cohort.
- (b) Replicate the pattern on `/docs/physics` and `/docs/validation`, which
  similarly end with nav cards pointing to sibling docs and no direct `/simulator`
  off-ramp. One page at a time, each as a separate experiment.
