# EXP-011 — Bike-detail top CTA copy: verb-result vs mechanism

- **Started:** 2026-05-25
- **Page:** `/bikes/[id]` (bike-detail page, e.g. `/bikes/4` for Hayabusa)
- **Element:** top-right "Simulate this bike" CTA beside the bike title
- **Status:** live (default off — control serves at canonical URL)
- **Flag:** `?variant=B`

## Hypothesis

Users on the bike-detail page don't click through to the simulator at the rate they should because the top CTA copy ("Simulate this bike →") describes the mechanism — running a simulation — rather than naming the concrete answer the visitor came for ("what is THIS bike's quarter-mile ET?"). A verb-result CTA ("See its quarter-mile ET →") puts the outcome on the click target itself and should lift CTR without any other layout, copy, or routing change.

## Variants

- **A (control, default):** `Simulate this bike →`
- **B (`?variant=B`):** `See its quarter-mile ET →`

Only the button label text changes. Href (`/simulator?bike_id=<id>`), Gauge icon, Tailwind classes, surrounding layout, h1, metadata, OG tags, and the bottom-of-page CTA card pair are all unchanged across arms. **Single variable: top CTA copy.**

## Primary metric

`simulator_runs_per_bike_detail_visitor` — the conversion of a bike-detail page view into a downstream simulator run. Click attribution via `data-exp="EXP-011"` + `data-variant={A|B}` + `data-cta="bike-detail-top"` + `data-bike-id` on the Link element so attribution survives without analytics infra.

## Expected effect size

The verb-result CTA pattern has prior support on this site (EXP-001 tests the same idea on the landing hero). I expect a 10–20% relative lift in top-CTA CTR. Even taking the lower bound, on a high-intent surface (a visitor has already filtered the 754-bike catalog to one bike), a CTR lift translates directly into simulator-runs/visitor — the bike-detail page has essentially no other downstream conversion path that competes.

Conservative point estimate for primary metric: **+12% relative lift in simulator-runs/bike-detail-visitor.** Threshold for shipping is ≥15%, so this is an experiment we expect to land at the lower edge of significance — the secondary-metric guardrails matter more than the headline number.

## Decision rule

Ship variant B as new control if:
- `simulator_runs_per_bike_detail_visitor` lifts ≥15% with p<0.05 over ≥200 samples per arm, AND
- `bike_detail_bottom_cta_click_through_rate` does not increase >20% in absolute terms (we want the top CTA copy to win on its own merits, not redistribute clicks down the page).

Hold for ≥200 samples per arm before any call. No interim peek-and-decide.

## Kill criteria

Roll back if any of the following:
- `bike_detail_page_bounce_rate` rises >10% (verb-result copy reads spammy or unclear in context)
- `simulator_page_first_run_completion_rate` from the bike-detail referrer drops >10% vs. site-wide baseline (B is recruiting low-intent curiosity clicks that bounce off `/simulator`)
- A visitor support ticket explicitly flags the copy as confusing for a returning user (qualitative signal, surfaces from #support, not analytics)

## Implementation

- New client component: `web/app/bikes/[id]/TopCtaVariant.js`
  - `useSearchParams()` inside a `<Suspense fallback={<TopCtaFallback />}>` per the static-prerender / CSR-bailout rule documented in CLAUDE.md
  - Suspense fallback renders the control copy with the same href, styling, icon, and `data-*` attributes — first-paint output is byte-identical to pre-EXP-011, so SSR/SSG remains stable and zero layout shift occurs
- `web/app/bikes/[id]/page.js`: replaced the inline top CTA `<Link>` with `<TopCtaVariant bikeId={bike.id} />`. Bottom CTA card pair (lines ~218-230, "Simulate this bike" + "Back to catalog") intentionally **not** touched — that holds the single-variable rule.

## SEO safety

- Same canonical URL (`/bikes/<id>`)
- Same h1 (`{bike.model}`)
- Same metadata, OG tags, structured data
- Same href on the CTA (`/simulator?bike_id=<id>`)
- Same first-paint markup as control (Suspense fallback is the control)

## Page-conflict check

| Experiment | Page |
|---|---|
| EXP-001 | landing-hero (`/`) |
| EXP-002, EXP-005 | `/pricing` |
| EXP-003 | `/simulator` |
| EXP-004 | `/blog/the-physics-of-a-perfect-launch` |
| EXP-006 | `/blog` (index) |
| EXP-007 | `/login` |
| EXP-008 | `/features` |
| EXP-009 | `/bikes` (catalog grid — NOT the detail page) |
| EXP-010 | `/blog/pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics` |
| **EXP-011** | **`/bikes/[id]` (detail page)** ← first experiment on this surface |

No conflict. `/bikes/[id]` had zero live experiments prior to today.

## Funnel-interaction note

A visitor at `/bikes?variant=B` who clicks the EXP-009 "Run sim" pill bypasses `/bikes/[id]` entirely → never sees EXP-011. A visitor at `/bikes?variant=B` who instead clicks a card body → arrives at `/bikes/<id>?variant=B` → sees EXP-011 variant B. When analysing EXP-011 results, segment by referrer arm (direct vs `/bikes?variant=A` vs `/bikes?variant=B`) before declaring a lift — the cohorts at `/bikes/[id]` arriving via EXP-009 control vs variant B may have different baseline intent profiles.

## Follow-ups if B wins (separate experiments, not bundled)

- (a) Replicate the verb-result copy on the bottom-of-page CTA card for consistency
- (b) Replicate on the simulator's own Run button
- (c) Evaluate a `/simulator?bike_id=<id>&run=auto` deeplink that auto-runs the sim on arrival — that is a feature change, not a copy test
