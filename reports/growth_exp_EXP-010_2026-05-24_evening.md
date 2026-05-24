# EXP-010 — Inline mid-article "Run this comparison" CTA on NS200 vs Apache RTR 200 4V post

- **ID:** EXP-010
- **Started:** 2026-05-24 (evening)
- **Page:** `/blog/pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics`
- **Status:** live (default OFF — flag-gated)
- **Flag:** `?variant=B`

## Surface selection — why this post and not the landing page

EXP-009 (live earlier today on `/bikes`) and the other eight active
experiments collectively occupy every other obvious primary surface:
landing-hero (EXP-001), `/pricing` ×2 (EXP-002 + EXP-005), `/simulator`
(EXP-003), `/blog/the-physics-of-a-perfect-launch` (EXP-004), the `/blog`
index (EXP-006), `/login` (EXP-007), `/features` (EXP-008), and `/bikes`
(EXP-009). Starting a second experiment on any of those would violate
the "never start a 2nd experiment on the same page while the first is
live" rule from the role brief.

Looking at unoccupied surfaces, the highest-ROI free target is the
Pulsar NS200 vs Apache RTR 200 4V comparison post. Three reasons:
(1) it sits in the Indian-market comparison-shopper cohort which is
exactly the audience the role brief flags as undermonetised; (2) it is
a long-form 200-line article with EXACTLY ONE CTA (line 316, post-
conclusion) — high leverage for an inline intent-peak test; (3) blog
posts are the discovery surface where most organic search traffic
lands, so a working pattern here can replicate to the other 28 posts.

## Hypothesis

Mid-article readers reach the stock-sim numbers table (~1/3 down the
page) at peak comparison intent — they have just absorbed the spec
sheet and seen MotoQuant's ET prediction for both bikes, and are in
the most likely "let me check this myself" mental state of the entire
read. The current post has exactly one simulator CTA, a card at the
bottom of the article. By the time readers reach it, most have either
bounced or scrolled past into "Related reading" links.

An inline CTA card placed immediately after the stock-sim numbers
table — i.e. at the intent peak, not at the end of the funnel —
should lift `simulator_runs / blog_post_visitor` without affecting
scroll depth, time-on-page, or SEO. The two CTAs target different
reader cohorts (mid-article scanners vs full-read finishers), so
cannibalisation of the end-of-post CTA should be limited.

## What changed

- **New file:** `web/app/blog/pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics/InlineSimCta.js`
  (87 lines) — exports a `Suspense`-wrapped component that reads
  `?variant=B` via `useSearchParams()` and renders either `null`
  (control / variant A) or an inline glass-card CTA (variant B) with
  copy "Want to test this on your own bike?" and a brand-orange
  "Run this comparison →" button linking to `/simulator`.
- **Edited:** `web/app/blog/pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics/page.js`
  (376 → 390 lines, +14). One new import, one new sentinel block
  `{ type: 'inline-cta' }` injected into `CONTENT` immediately after
  the stock-sim numbers table block, and one new dispatch case in
  the `Prose` renderer that maps that block type to `<InlineSimCta />`.
  Server / client boundary kept clean: page.js stays a server component;
  only `InlineSimCta.js` is `"use client"`.

## Variants

- **A (default, control):** No mid-article CTA. The existing
  end-of-post CTA at line ~316 is the only simulator affordance on
  the page. SSR/SSG output is byte-identical to the pre-EXP-010 page.
- **B (`?variant=B`):** Inline glass-card CTA rendered between the
  stock-sim numbers table and the "Both ETs sit inside the entry-
  200-300cc cluster bias band" paragraph. End-of-post CTA preserved
  unchanged.

## Single variable

The only behavioural difference between arms is the presence of the
mid-article CTA card. End-of-post CTA, article copy, tables, callouts,
meta tags (title, description, canonical, openGraph, structured data),
related-reading block, and nav/footer are all unchanged across arms.
Same canonical URL. SEO unaffected.

## Primary metric

`simulator_runs_per_blog_post_visitor`.

## Secondary metrics

- `blog_inline_cta_click_through_rate`
- `blog_end_of_post_cta_click_through_rate_delta` (cannibalisation watchdog)
- `post_scroll_depth_p50` (interruption watchdog)
- `post_time_on_page_p50`
- `simulator_page_first_run_completion_rate_from_post_referrer`

## Decision criteria

- **Ship B as new control** if `simulator_runs/blog_post_visitor`
  lifts ≥15% with p<0.05 over ≥200 samples per arm AND
  `blog_end_of_post_cta_click_through_rate` does not drop >25%
  (different cohort, should retain most of its conversion).
- **Roll back** if `post_scroll_depth_p50` drops >15% (CTA reads as
  interruption rather than affordance), OR if first-run completion
  from the post referrer drops >15% vs site-wide baseline (CTA is
  recruiting low-intent curiosity clicks).
- **Hold** for ≥200 samples per arm before declaring either outcome.

## Rollback plan

Single-commit revert. Two files: delete
`web/app/blog/pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics/InlineSimCta.js`
and revert `page.js` to the pre-EXP-010 state (one import line + one
CONTENT sentinel block + one Prose dispatch case). No DB / API / schema
changes. Marking the experiment `status: "rolled_back"` in
`data/growth_experiments.json` is the only data-layer change required.

## Static-prerender / SEO safety

- `useSearchParams()` lives inside `InlineSimCtaInner`, wrapped in
  `<Suspense fallback={null}>` per the App Router static-export rule
  documented in CLAUDE.md.
- Fallback is `null`, so the SSR/SSG HTML for the control and the
  pre-EXP-010 page are byte-identical — no hydration mismatch, no
  layout shift, no anchor-text or link-graph change visible to crawlers.
- Meta tags (title, description, canonical URL, openGraph, article
  structured data) are unchanged across arms. The canonical URL still
  points to `https://motoquant.in/blog/pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics`
  on both variants.

## Notes on conflicts

- The post had **zero** live experiments prior to EXP-010 (confirmed
  against the nine existing entries in `data/growth_experiments.json`).
- EXP-004 owns a different blog post
  (`/blog/the-physics-of-a-perfect-launch`); EXP-006 owns the `/blog`
  INDEX, not a post. No conflict.
- EXP-009 (also started today, on `/bikes`) is a different page entirely
  and the two run in parallel without interaction risk.

## Follow-up if B wins

Replicate the pattern on the other 28 blog posts at the same structural
location (post-stock-sim-table / post-headline-numbers block). At that
point, promote the per-post `InlineSimCta.js` into a shared
`web/components/blog/InlineSimCta.js` component to avoid 29-way
copy/paste maintenance debt.
