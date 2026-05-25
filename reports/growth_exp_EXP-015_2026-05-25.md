# EXP-015 — /docs/validation post-methodology credibility CTA

- **Started:** 2026-05-25
- **Page:** `/docs/validation`
- **Status:** live (default control; activate B via `?variant=B`)
- **Flag:** URL param `?variant=B`
- **Min sample:** 200 per arm

## Hypothesis

Visitors who reach the bottom of `/docs/validation` have absorbed
74-benchmark accuracy data, per-cluster bias breakdown, three hand-calibrated
reference baselines (K5 / R1 / Hayabusa, Δ ±0.0000 since Apr 30 2026), and the
honest "known limitations" disclosure on small-cc and 2T residual bias.

They sit at peak technical credibility — every objection a skeptical
Indian-drag-scene reader could raise has been preemptively addressed on this
exact page. Yet the page currently ends with two equal-weight nav cards
("Getting Started" + "Try the simulator") that read as documentation chrome,
not as a conviction CTA.

The hypothesis is that a single inline glass card injected immediately after
the Methodology section — copy-keyed to the just-read accuracy numbers — will
lift `/simulator` CTR without changing nav structure or breaking the reader's
sense that the page is a doc, not a sales sheet.

## Mechanic (single variable)

The only thing that changes between arms is the presence of one card. Both
arms ship byte-identical HTML for the article header, all six body sections,
the docs sidebar, meta tags, canonical URL, and the two terminal Next nav
cards.

| | Variant A (control) | Variant B |
|---|---|---|
| Inline CTA card after Methodology | absent | present |
| Terminal Next nav (Getting Started + Try the simulator) | present | present |
| Article H1, six sections, sidebar, meta | identical | identical |

**Variant B copy:**

> **Run your bike through the same engine →**
> 327 bikes pre-loaded. Same RK4 integrator. Same ±0.032s top-10 mean error.
> No signup.
>
> *(right-rail stat strip on sm+: K5 10.0334s / R1 10.2859s / Busa 10.4712s)*

## Decision rule

Ship variant B as the new control if:

- `simulator_runs / validation-visitor` lifts **≥15%** with **p<0.05** over
  **≥200 samples per arm**, AND
- `simulator_page_first_run_completion_rate` from the validation referrer
  does **not** drop **>10%** vs. site-wide baseline (high-intent cohort
  should run sims at or above the site average; if completion collapses,
  the CTA is recruiting low-intent clicks).

Roll back if:

- `validation_page_bounce_rate` rises **>10%** (CTA reads premature or pushy
  after methodology), OR
- `validation_next_simulator_card_ctr` drops **>30%** in absolute terms
  (cannibalisation without net lift is failure — we don't want the inline
  card to merely move clicks from the nav card).

No decision before 200 samples per arm.

## Expected lift

EXP-014 on `/docs/getting-started` predicted a similar "peak procedural
readiness" lift; this page is "peak technical credibility" which is a strong
trigger for the Indian drag-scene cohort that has been burned by
unsubstantiated tuning claims before. Conservative point estimate: **+18%**
on `simulator_runs/validation-visitor`. Range: **+8% to +35%** depending on
how much of the existing simulator-card CTR was already credibility-driven
vs. simple wayfinding.

## SEO safety

- Same canonical URL on both arms
  (`https://motoquant.in/docs/validation`).
- `Suspense fallback={null}` so SSR/SSG output is byte-identical to
  pre-EXP-015 on both arms — no hydration mismatch, no layout shift.
- URL param only (`?variant=B`), no route fork.
- Variant A renders nothing additional; the article content the crawler sees
  is identical to before this experiment landed.

## Files touched

- `web/app/docs/validation/CredibilityCtaVariant.js` (new, 'use client',
  Suspense-wrapped useSearchParams)
- `web/app/docs/validation/page.js` (one import + one component mount above
  the terminal Next nav)
- `data/growth_experiments.json` (appended EXP-015)

## Follow-ups if B wins

1. Copy retest on the headline — verb-result ("Run your bike through the
   same engine") vs proof-anchored ("Get an ET for your bike with ±0.032s
   accuracy").
2. Replicate the post-methodology placement on `/docs/physics`, which also
   ends with sibling-doc nav cards and no inline `/simulator` off-ramp.
