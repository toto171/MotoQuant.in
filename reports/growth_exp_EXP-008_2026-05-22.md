# EXP-008 — /features bottom-of-page CTA copy + subhead

**Started:** 2026-05-22
**Status:** live, default OFF (variant A served unless `?variant=B`)
**Page:** `/features`
**Element:** Bottom-of-page primary CTA copy + subhead pair

## Hypothesis

Visitors who reach the bottom of `/features` have read six feature blocks and are evaluating *"is this real, and what will actually happen if I click?"* The current CTA "Try it free" with subhead "Free in the browser. No account required to start." restates the free-ness twice but never names the concrete first-run outcome. The copy is generic enough to describe any free SaaS — it does nothing to convert the specific cohort that just spent 90+ seconds reading about physics sub-models, Pacejka tire coefficients, and 976 regression tests.

Variant B replaces the button with **"Run a sim — 15 seconds, no signup"** and the subhead with **"Pick a bike, hit go. Real physics in your browser — no install, no account."** Both name the action ("run a sim"), the time cost ("15 seconds"), and the absence of friction ("no signup", "no install") on the click target itself.

If grounding the next click in a time-bound, action-specific promise reduces drop-off vs the generic free-ness framing, `simulator_runs / features_page_visitor` should rise.

**Distinct from EXP-001** (landing-hero, cold visitor): this is a mid-funnel feature-reader cohort with higher intent but also higher "is this real?" skepticism — so the test asks a different question even though the surface (CTA copy) is the same category.

## Variants

| Arm | CTA label | Subhead |
|-----|-----------|---------|
| **A (control)** | `Try it free` | `Free in the browser. No account required to start.` |
| **B (treatment)** | `Run a sim — 15 seconds, no signup` | `Pick a bike, hit go. Real physics in your browser — no install, no account.` |

The h2 ("Ready to run your first sim?"), href (`/simulator`), the secondary "See pricing" CTA, and all surrounding layout are **byte-identical** across arms. Single variable rule: this is a copy-bundle test (button + subhead together as one message), not a multi-element redesign.

## Metrics

- **Primary:** `simulator_runs / features_page_visitor`
- **Secondary:** features-bottom-CTA CTR, features→pricing CTR, features-page bounce rate, /simulator first-run completion rate, features→simulator time-to-click

## Decision criteria

Ship B as new control if the primary lifts **≥15% with p<0.05 over ≥200 samples per arm AND** simulator-page first-run completion does not drop >5% (we want intent-to-actually-run, not inflated curiosity clicks). Roll back if features→pricing CTR drops >25% (cannibalisation) or page bounce rises >10% (reads spammy). No decision before 200 samples per arm.

## Implementation

- New client component: `web/app/features/BottomCta.js`
  - `BottomCtaInner` uses `useSearchParams()`; reads `?variant=B`.
  - Outer `BottomCta` wraps inner in `<Suspense>` with a fallback that renders variant A markup verbatim — keeps SSG output byte-identical to pre-EXP-008.
  - `data-exp="EXP-008"` + `data-variant={variant}` on wrapper div AND primary `<Link>` so click-attribution survives even if wrapper analytics break.
- `web/app/features/page.js` — inline bottom-CTA block replaced with `<BottomCta />`; kept inside the existing `<RevealSection>` so framer-motion reveal animation is unchanged on both arms.
- Same canonical URL, same h1, same meta — SEO-safe.

## Page-conflict check

- EXP-001 → landing-hero
- EXP-002, EXP-005 → /pricing
- EXP-003 → /simulator
- EXP-004 → /blog/the-physics-of-a-perfect-launch
- EXP-006 → /blog (index)
- EXP-007 → /login
- **EXP-008 → /features** ← previously had zero live experiments. No conflict.

## Funnel-interaction note

A visitor arriving via landing-hero variant B (EXP-001) and then clicking through to /features will, if also at variant B here, see a consistent verb-result message stack. When evaluating EXP-008 lift, segment by landing-arrival variant to avoid attributing landing-hero lift to features-page CTA lift (or vice versa). Pure /features direct-arrival traffic is the cleanest cohort for the primary metric.

## Follow-ups (if B wins)

1. Evaluate replicating the time-bound + action-specific pattern on landing-hero as a 3-way EXP-001 follow-up (only after EXP-001 has resolved).
2. Consider applying the same framing to the `/about` bottom CTA and the `/docs/getting-started` "Try the simulator" inline links — as separate micro-experiments, one surface at a time.
3. Do **not** bundle copy changes across pages in a single experiment — placement and audience differ enough to invalidate cross-page learnings.
