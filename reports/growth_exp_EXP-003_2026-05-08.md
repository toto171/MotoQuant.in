# EXP-003 — Simulator default-bike A/B test

**Date launched:** 2026-05-08 (Friday)
**Page:** `web/app/simulator/page.js` (motoquant.in/simulator)
**Element:** default pre-selected motorcycle
**Status:** Live (default OFF — control unchanged on canonical URL)

## Hypothesis

Visitors landing on `/simulator` see a bike pre-selected so they can hit Run
without first picking. Pre-EXP-003 the simulator pre-selected `bikes[0]`,
which is alphabetical-first from `/api/bikes` (Aprilia RS 457). The
layout.js metadata + OG image both reference Hayabusa, so the practical
"control" in user perception is the aspirational Hayabusa — but the
underlying code wasn't actually defaulting there.

Two problems with that:

1. The aspirational default ("look, a 220 hp 1340 cc liter bike!") creates a
   "this isn't for me" cognitive cost for the dominant Indian-market
   visitor, whose actual bike is a 150–250 cc commuter. The
   bike-picker-change rate before any run is the proxy: if visitors are
   forced to change the default before clicking Run, the cost shows up as
   abandoned simulator sessions (visitor opens the dropdown, gets distracted
   by 290 options, leaves).
2. The simulator page is the highest-leverage point in the conversion
   funnel (landing → simulator → run → save → signup). Reducing the
   "first-run time" by even 10 s on average compounds into measurable
   simulator-runs/visitor lift.

Variant B pre-selects **Pulsar NS 200**, the highest-volume Indian
commuter most likely to match the visitor's actual bike. The hypothesis is
that a localised default reduces the picker-change friction enough that
simulator-runs/visitor lifts ≥15 %, without compromising aspirational
visitors (who can still switch to Hayabusa in two clicks).

Variant A keeps Hayabusa as the explicit control on the canonical URL so
the SEO-stable Hayabusa keywords in `layout.js` (`hayabusa quarter mile
calculator`, `gsxr 1000 drag simulator`) and the OG image reference still
match what a search-result-CTR visitor lands on.

## Implementation

- Client component reads `?variant=B` via `useSearchParams()` in
  `web/app/simulator/page.js`.
- Variant-aware default-bike selection done in `pickDefaultBikeForVariant()`
  — name-substring regex match against the API-loaded bike list so catalog
  reshuffles (Hayabusa Gen1 vs 2008-2012 vs 2021-2024 vs 25th Anniversary)
  don't break the variant.
- Falls back to `bikes[0]` (the existing pre-EXP-003 alphabetical-first
  behaviour) if no name match — protects against unseeded DB or catalog
  reorganisation.
- The `<SimulatorPageInner>` component is wrapped in `<Suspense
  fallback={null}>` per the App-Router static-prerender rule documented in
  `web/CONTRIBUTING.md`. Without the boundary `next build` errors with
  `missing-suspense-with-csr-bailout` (same pattern as EXP-001 on
  `web/app/page.js`).
- `data-exp="EXP-003"` and `data-variant="A|B"` attributes live on the
  bike-picker Card so analytics can attribute the simulator-run event back
  to the correct arm.
- Zero infrastructure dependencies: no feature flag service, no backend
  variant assignment, no cookies. URL-param toggle only.

## Control vs variant

|             | Variant A (control)                                                  | Variant B                                                       |
|-------------|----------------------------------------------------------------------|-----------------------------------------------------------------|
| Default bike| Hayabusa (Suzuki, ≥1299 cc, I4 superbike)                            | Pulsar NS 200 (Bajaj, 199 cc, 24 hp single)                     |
| URL         | `/simulator` (canonical) or `?variant=A`                             | `/simulator?variant=B`                                          |
| h1          | unchanged                                                            | unchanged                                                       |
| Meta        | unchanged                                                            | unchanged                                                       |
| OG image    | unchanged                                                            | unchanged                                                       |
| SEO keywords| unchanged                                                            | unchanged                                                       |

Single-variable change: only the default-bike pre-selection. Same dropdown,
same parts catalog, same physics engine, same chart panel, same canonical
URL, same metadata.

## Metrics

**Primary:** `simulator_runs_per_visitor_to_simulator_page`

This is the funnel-step conversion rate that directly tests whether the
localised default reduces the activation barrier. A "simulator run" is
defined as the first successful POST to `/api/simulate/quick` or
`/api/simulate` with a 2xx response, attributed to the variant via
`data-variant` on the bike-picker Card at click time.

**Secondary:**

1. **`bike_picker_change_rate`** — % of variant-B visitors who open the
   bike dropdown and pick a different bike before running. The hypothesis
   says B should reduce this. If B *increases* it materially, the Pulsar
   default is missing the mark and we have evidence to roll back.
2. **`first_run_time_to_click_s`** — wall-clock seconds from
   `/simulator` page-view to first Run click. Drops should track
   primary-metric lift if the hypothesis is right.
3. **`simulator_page_bounce_rate`** — guards against the failure mode
   where aspirational-segment visitors see Pulsar pre-loaded and leave.
4. **`post_run_parts_engagement_rate`** — % who interact with the parts
   catalog after their first run. Pulsar visitors are likely to engage more
   with the parts catalog because Pulsar parts are abundant + cheap; if
   variant B doesn't lift this it's a signal the localised-default theory
   is weaker than expected.

## Sample-size justification

Same minimum as EXP-001 / EXP-002: **200 samples per arm**. With 200/arm
and a baseline simulator-runs/visitor of ~0.40 (estimated; refresh from
production data when first 50 samples land), a 15 % relative lift to ~0.46
is detectable at p<0.05 with two-tailed power ≥0.80. We hold the floor at
200 samples per arm so we don't ship a rollout off chance variation in the
first 30 visitors.

## Decision criteria

**Ship variant B as new control** if all three are true:

1. `simulator_runs_per_visitor` lifts ≥15 % on B with p<0.05.
2. `simulator_page_bounce_rate` does not increase >10 % on B.
3. `bike_picker_change_rate` on B is at least as low as on A (the whole
   point is the default is *useful*, not just *different*).

**Roll back to variant A** if either:

1. `simulator_page_bounce_rate` increases >10 % on B (Pulsar default is
   pushing aspirational-segment visitors away).
2. `bike_picker_change_rate` on B is ≥120 % of A (visitors are immediately
   overriding the default → it isn't reducing friction).

**Continue collecting** if metrics are within ±10 % of A and sample size
is below the 200/arm floor.

**SEO consideration:** Even if B wins outright, Hayabusa stays as the
explicit `?variant=A` path because the layout.js metadata + OG copy +
search-keyword targeting all reference Hayabusa. The default flip on the
canonical URL would otherwise create a search-result-CTR mismatch
("hayabusa quarter mile calculator" → user lands on a Pulsar). Long-term
fix if B wins: rewrite `layout.js` metadata to a bike-agnostic frame
("Run a quarter-mile drag sim for any motorcycle in seconds") so canonical
URL can default to whichever bike has highest activation.

## Files touched

- `web/app/simulator/page.js` — added `Suspense`, `useSearchParams`,
  `pickDefaultBikeForVariant()` helper, `defaultBikeVariant` state, wrapped
  default export in `<Suspense>`, `data-exp`/`data-variant` on bike-picker
  Card.
- `data/growth_experiments.json` — appended EXP-003 entry.
- `reports/growth_exp_EXP-003_2026-05-08.md` — this design doc.

## Cross-experiment guardrails

- EXP-001 is on `web/app/page.js` (landing hero) — different page, no
  conflict.
- EXP-002 is on `web/app/pricing/page.js` (pricing) — different page, no
  conflict.
- EXP-003 is on `web/app/simulator/page.js` (simulator) — first experiment
  on this page; no concurrent variants to interact with.

The "never two live experiments on the same page" rule is satisfied.
