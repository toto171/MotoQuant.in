# Growth Experiment EXP-012 — /about end-of-page simulator CTA

- **Started:** 2026-05-25
- **Page:** `/about`
- **Element:** End-of-page glass CTA card pinned between the contact-form section and `SiteFooter`
- **Type:** Presence test (control = no terminal CTA; variant = single grounded CTA card)
- **Flag:** `?variant=B`
- **Default:** A (control)
- **Status:** live

## Hypothesis

Users land on `/about` to vet credibility — they read the Pune origin story, the
first-principles methodology, the ±0.032 s top-10 calibration result, the
founder bios (Arya Desai / Hritwik Mudhai), the roadmap, and reach the contact
form. The page has **zero outbound clicks toward `/simulator`** today: `page.js`
imports `Link` from `next/link` but never uses it; the only anchors on the page
are `mailto:` links. The cohort that finishes reading either uses `SiteNav` to
navigate away, fills the contact form (high-intent B2B), or drops into
`SiteFooter` — none of those paths exercise the actual product the about-page
just pitched.

A single terminal CTA card after the contact form (the natural end-of-content
breakpoint) should lift `simulator_runs / about_visitor` by converting
credibility-validated readers into first-run users at the moment of peak trust.

> **Failure mode being targeted:** visitors land, absorb the pitch, then exit
> through the footer because the page has no concrete next action.

## Variants

| Arm | Description |
|-----|-------------|
| **A — control** | Pre-EXP-012 behaviour: contact-form section drops directly into `SiteFooter`. Hidden `<span data-exp="EXP-012" data-variant="A">` placeholder for analytics attribution. |
| **B — variant** | A glass-bordered CTA section pinned below the contact form and above the footer. Copy: `"You've read the pitch. Now run the numbers."` Subhead: `"Same first-principles engine. Same ±0.032 s top-10 error. 15 seconds, no signup — pick your bike and see its quarter-mile ET."` Brand-orange `Run a sim` button → `/simulator`. |

**Single-variable rule:** copy + href fixed on variant B — this is a *presence*
test, not a copy test. Distinct from EXP-008 (`/features` copy test on an
existing CTA) and EXP-011 (`/bikes/[id]` copy test on an existing CTA).

## Primary metric

`simulator_runs_per_about_page_visitor`

## Secondary metrics

- `about_end_of_page_cta_click_through_rate` (B arm only — sanity check the
  CTA is reachable)
- `about_page_bounce_rate` (roll back if rises >10 %)
- `about_contact_form_submission_rate_delta` (roll back if drops >10 % — the
  contact form is the existing high-intent action on the page and the CTA
  must add an off-ramp, not redirect B2B inquiries away from email)
- `about_to_simulator_time_to_click_s`
- `simulator_page_first_run_completion_rate_from_about_referrer` (roll back if
  >15 % below site-wide baseline — CTA is recruiting low-intent curiosity
  clicks rather than credibility-validated readers)

## Minimum sample

200 per arm before any decision.

## Decision criteria

Ship variant B as new control if:

1. `simulator_runs / about_visitor` lifts **≥15 %** with **p<0.05** over **≥200
   samples per arm**, AND
2. `about_contact_form_submission_rate` does not drop more than 10 %, AND
3. `simulator_page_first_run_completion_rate_from_about_referrer` does not drop
   more than 15 % vs site-wide baseline.

Roll back if `about_page_bounce_rate` rises >10 % or if any of the secondary-
metric floors are breached.

## Implementation

Files touched:

- `web/app/about/EndOfAboutCta.js` (new, 79 lines) — client component owning the
  `useSearchParams()` flag check, the variant-A hidden span, and the variant-B
  glass card. Rendered inside a `<Suspense fallback={null}>` boundary per the
  CLAUDE.md Vercel App-Router static-prerender / CSR-bailout rule.
- `web/app/about/page.js` (2 small edits) — added `Suspense` import, added
  `EndOfAboutCta` import, mounted `<Suspense fallback={null}><EndOfAboutCta />
  </Suspense>` immediately before `<SiteFooter />`.

Untouched:

- `web/app/about/layout.js` — metadata, canonical, OG tags, breadcrumbs
  structured data. SEO surface is byte-identical on both arms.
- Hero, story, founders, roadmap, contact form, all `mailto:` anchors, all
  copy. Variant B is purely additive.

## Build verification

`cd web && npx next build` passes:

```
○ /about    7.05 kB   (static prerender)
```

`/about` continues to prerender as static content (the page already had
`'use client'`, so the Suspense boundary protects the new
`useSearchParams()` call against static-prerender bailout).

## No page conflict

| EXP | Page |
|-----|------|
| EXP-001 | landing hero |
| EXP-002, 005 | `/pricing` |
| EXP-003 | `/simulator` |
| EXP-004 | `/blog/the-physics-of-a-perfect-launch` |
| EXP-006 | `/blog` index |
| EXP-007 | `/login` |
| EXP-008 | `/features` bottom |
| EXP-009 | `/bikes` catalog grid |
| EXP-010 | `/blog/pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics` |
| EXP-011 | `/bikes/[id]` top CTA |
| **EXP-012** | **/about (this experiment)** |

`/about` had no live experiments prior to this.

## Follow-up branches (if B wins)

- **Copy refinement (EXP-013 candidate):** test verb-result vs aspirational
  copy on the now-default CTA (`Run a sim` is already verb-result; an
  alternative `See your bike's quarter-mile ET` mirrors EXP-001's variant B).
- **`/whitepaper` copy retest:** the whitepaper page already has a terminal
  CTA card to `/simulator` with generic `Open the simulator` framing — a
  credibility-grounded copy retest there could be a sibling experiment.

## Don't

- Don't declare a winner before 200 samples per arm.
- Don't start a second experiment on `/about` while EXP-012 is live.
- Don't bundle copy variants into this experiment — single variable per
  CLAUDE.md guidance.
