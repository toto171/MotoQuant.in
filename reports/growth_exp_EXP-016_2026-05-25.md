# Growth Experiment EXP-016
**Started:** 2026-05-25  
**Page:** `/docs/physics`  
**Element:** Inline CTA card injected after the 15-sub-models grid

---

## Background

The EXP-015 decision criteria explicitly called out `/docs/physics` as the next candidate for this pattern:

> "replicate the post-methodology placement on /docs/physics which similarly ends with sibling-doc nav cards and no inline /simulator off-ramp."

`/docs/physics` had zero live experiments before this session.

---

## Hypothesis

Readers who scroll through all 15 sub-model rows on `/docs/physics` are at a peak "this is technically serious" credibility inflection point — they have just absorbed the engine torque model, Pacejka magic formula, weight transfer, clutch dynamics, the RK4 integrator detail, and 10 other modules. The page currently provides no in-article affordance to act on that understanding: the only simulator link is buried in one of two equal-weight nav cards at the very end of a 4-section article.

Placing a single CTA card at the natural "I just saw the engine — now I want to see it run" moment (immediately after the sub-models grid, before the BikeConfig section) should lift `simulator_runs / physics_page_visitor` without changing nav structure or breaking the reader's sense that the page is a doc, not a sales sheet.

This is a **presence-only test**: copy and href are fixed on variant B so we are not confounding presence with messaging.

---

## Variants

**A (control):** No inline CTA after the sub-models grid. The BikeConfig section follows directly. The only simulator affordances on the page are the two terminal Next nav cards at the bottom ("Validation Data →" and "Run your first sim →"). This is pre-EXP-016 behaviour.

**B (variant):** A glass CTA card injected immediately after the 15-sub-models grid (before the BikeConfig section):
- Headline: `See all 15 sub-models fire on your bike →`
- Subhead: `Pick your bike. Run the quarter mile. Real RK4 physics — no install, no signup.`
- Right-rail stat strip (desktop only): `336 bikes / 1 ms timestep / 15 sub-models`
- Links to `/simulator`

The two terminal Next nav cards are retained on both arms — additive, not a replacement.

---

## Primary Metric

`simulator_runs_per_physics_page_visitor`

## Secondary Metrics

| Metric | Purpose |
|---|---|
| `physics_inline_cta_click_through_rate` | Is the card itself clickable, or is it noise? |
| `physics_terminal_nav_validation_ctr_delta` | Are we cannibalising the deeper docs path? |
| `physics_terminal_nav_getting_started_ctr_delta` | Same check for getting-started nav |
| `physics_page_bounce_rate` | Does the CTA read as intrusive / pushy? |
| `simulator_page_first_run_completion_rate_from_physics_referrer` | Is the intent genuine (completes a run) or curiosity (lands on /simulator and bounces)? |

---

## Implementation

- **Client component:** `web/app/docs/physics/SubModelsCtaVariant.js` — `useSearchParams()` inside `<Suspense fallback={null}>` per the Vercel App-Router CSR-bailout rule (CLAUDE.md hygiene, web/CONTRIBUTING.md).
- **Mount point:** `web/app/docs/physics/page.js` — between the sub-models `<section>` and the BikeConfig `<section>`, via `<SubModelsCtaVariant />` call.
- **Fallback:** `null` on both arms for SSR/SSG — zero layout shift, zero hydration mismatch, zero SEO drift.
- **Attribution:** `data-exp="EXP-016"`, `data-variant="B"`, `data-cta="physics-post-submodels"` on the Link element.
- **Flag:** `?variant=B` — same param as EXP-001/002/003/004/006/007/008/009/011/012/013/014/015 (no conflict; each owns a different page).

---

## Decision Criteria

- **Ship B as new control** if `simulator_runs/physics-visitor` lifts ≥15% with p<0.05 over ≥200 samples per arm AND `simulator_page_first_run_completion_rate` from the physics referrer does not drop >10% vs. site-wide baseline.
- **Roll back** if `physics_page_bounce_rate` rises >10% OR if `physics_terminal_nav_validation_ctr + physics_terminal_nav_getting_started_ctr` together drop >25% in absolute terms (card cannibalising docs depth rather than adding net conversion).
- **No decision** before 200 samples per arm.

---

## No-Conflict Audit

| EXP | Page | Status |
|---|---|---|
| EXP-001 | /landing-hero | live |
| EXP-002 | /pricing (Pro button) | live |
| EXP-003 | /simulator default bike | live |
| EXP-004 | /blog/physics-of-perfect-launch | live |
| EXP-005 | /pricing (Pro tag-line) | live |
| EXP-006 | /blog index | live |
| EXP-007 | /login | live |
| EXP-008 | /features bottom CTA | live |
| EXP-009 | /bikes catalog grid | live |
| EXP-010 | /blog/pulsar-ns200-vs-apache-rtr-200 | live |
| EXP-011 | /bikes/[id] top CTA | live |
| EXP-012 | /about | live |
| EXP-013 | /whitepaper | live |
| EXP-014 | /docs/getting-started | live |
| EXP-015 | /docs/validation | live |
| **EXP-016** | **/docs/physics** | **live (this session)** |

`/docs/physics` had zero live experiments. No conflict.

---

## Follow-up Candidates (if B wins)

1. **Copy retest** on the EXP-016 card: "See all 15 sub-models fire on your bike" (mechanism-naming) vs. "Run your first simulation — 15 seconds" (time-bound framing tested in EXP-008 on a different cohort).
2. **Earlier placement** test: inject a CTA between the Numerical Integrator section and the sub-models grid for readers who arrived already knowing what RK4 means.
3. **Combined docs-physics-funnel** test: presence CTA on both `/docs/physics` and `/docs/validation` as a coordinated experiment to measure whether the physics-docs funnel as a whole benefits from the pattern.
