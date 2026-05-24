# EXP-009 — Inline "Run sim" CTA on /bikes catalog cards

- **ID:** EXP-009
- **Started:** 2026-05-24
- **Page:** `/bikes`
- **Status:** live (default OFF — flag-gated)
- **Flag:** `?variant=B`

## Hypothesis

Visitors who land on `/bikes` are in a browse/lookup mode. They scroll the
754-bike paginated grid, find their bike, and click into `/bikes/<id>` to
read specs. The current `BikeCard` has exactly one action — a single `Link`
wrapping the whole card that navigates to the detail page. The simulator is
mentioned only in a prose sentence inside the page header
("...or open the quarter-mile calculator"), which most grid-scanners never
read. As a result, nearly all catalog traffic funnels into the detail page
and never reaches the simulator, even though every grid visitor implicitly
has the question "what does this bike actually run?" — which is exactly
what the simulator answers.

Adding a small inline `Run sim` pill to each card — secondary, visually
minor, but always present in the scan area — should lift
`simulator_runs / bikes_visitor` without cannibalising
`bikes_to_detail_page_ctr`, because the card body remains the dominant
hover target and the pill is small enough to read as supplementary.

## What changed

- **New file:** `web/app/bikes/BikeCardCta.js` — exports a
  `Suspense`-wrapped component that reads `?variant=B` via
  `useSearchParams()` and renders either `null` (control / variant A)
  or a small `Run sim` pill (variant B) that links to `/simulator`.
  Pill stops `event.propagation` so the parent `<Link>` click
  handler doesn't navigate to the detail page when the pill is clicked.
- **Edited:** `web/app/bikes/page.js` — `BikeCard` is wrapped in a
  `relative` outer `<div>` so the pill can be absolutely positioned in
  the bottom-right corner *outside* the parent `<Link>` (avoids nested
  `<a>` tags, which are invalid HTML). On the control arm the wrapper
  div is identical to the prior layout because `BikeCardCta` renders
  `null`. Adds `data-exp="EXP-009"` and `data-bike-id` for analytics.

## Variants

- **A (default, control):** No pill. Card markup is byte-identical to
  pre-EXP-009 render under SSR/SSG (the `Suspense` fallback is `null`).
- **B (`?variant=B`):** Small brand-orange `Run sim` pill in the card's
  bottom-right corner, linking to `/simulator`.

## Single variable

The only behavioural difference between arms is the presence of the
pill. The parent `<Link>`, the card visuals, the header subtitle prose,
and the page meta tags are unchanged across arms. Same canonical URL.
SEO unaffected.

## Primary metric

`simulator_runs_per_bikes_page_visitor`.

## Secondary metrics

- `bikes_card_run_sim_click_through_rate`
- `bikes_to_detail_page_ctr` (cannibalisation watchdog)
- `bikes_page_bounce_rate`
- `simulator_page_first_run_completion_rate_from_bikes_referrer`
- `bikes_to_simulator_time_to_click_s`

## Decision criteria

- **Ship B as new control** if `simulator_runs_per_bikes_visitor`
  lifts ≥15% with p<0.05 over ≥200 samples per arm AND
  `bikes_to_detail_page_ctr` does not drop >10% AND
  `simulator_page_first_run_completion_rate_from_bikes_referrer` does
  not drop >15% vs the site-wide baseline.
- **Roll back** if `bikes_to_detail_page_ctr` drops >10% (pill is
  cannibalising the detail path), `bikes_page_bounce_rate` rises >10%
  (visual noise reads as clutter), or first-run completion from the
  /bikes referrer collapses (pill is recruiting low-intent curiosity
  clicks).
- **Hold** for at least 200 samples per arm before declaring either
  outcome, per the standing growth-experiments rule.

## Rollback plan

Single-commit revert. Two files: delete
`web/app/bikes/BikeCardCta.js` and revert `web/app/bikes/page.js` to
the pre-EXP-009 `BikeCard` definition (one import line + one component
body). No DB changes, no API changes, no schema changes. Marking
the experiment `status: "rolled_back"` in
`data/growth_experiments.json` is the only data-layer change required.

## Notes on conflicts

- /bikes had **zero** live experiments prior to EXP-009 (confirmed
  against the eight existing entries in `data/growth_experiments.json`
  spanning landing-hero, /pricing ×2, /simulator, two blog surfaces,
  /login, and /features).
- The pill links to `/simulator` plain — **not** `/simulator?bike=<id>`
  — because the simulator does not currently honour a bike deeplink
  query param, and EXP-003 already owns the `?variant=B` flag on
  `/simulator` (controls the default pre-selected bike, A=Hayabusa /
  B=Pulsar NS 200). Bundling a deeplink with this CTA would confound
  EXP-009 with a separate feature and violate the one-variable rule.

## Static-prerender / SEO safety

- `useSearchParams()` lives inside `VariantPillInner`, which is wrapped
  in `<Suspense fallback={null}>` per the App Router static-export
  rule documented in `CLAUDE.md` ("`useSearchParams()` must live
  inside a `<Suspense>` boundary or Next.js will fail to prerender
  with `missing-suspense-with-csr-bailout`").
- Fallback is `null`, so the SSR/SSG HTML for the control and the
  pre-EXP page are byte-identical — no hydration mismatch, no layout
  shift, no anchor-text or link-graph change visible to crawlers.
- Outer `<Link href="/bikes/${bike.id}">` is unchanged, preserving the
  catalog → detail internal link graph that the sitemap relies on.
