# EXP-017 — Inline mid-article CTA on /blog/hayabusa-vs-zx-14r-which-is-faster

- **Started:** 2026-05-25
- **Page:** `/blog/hayabusa-vs-zx-14r-which-is-faster`
- **Status:** live (default = A, B served on `?variant=B`)
- **Primary metric:** `simulator_runs / post_visitor`
- **Min sample:** 200 per arm
- **Owner:** growth-experiments agent (autonomous-ops)

## Hypothesis

Readers of this litre-hyper-sport comparison post hit peak comparison
intent at the moment the simulator's stock-tune ET numbers are revealed
— the Stock-Sim Results table sits ~25% into the article and shows the
ZX-14R at ~10.35 s vs the Hayabusa Gen1 reference at 10.4712 s. By the
time the reader reaches the existing end-of-post CTA card (line 384 in
`page.js`, ~400 lines into the rendered page), most have either bounced
or scrolled into the Related-reading sidebar.

Injecting a single inline CTA card immediately after the stock-sim
table + callout — i.e. at the intent peak, not at the bottom of the
funnel — should lift `simulator_runs / post_visitor` without affecting
scroll depth, SEO, or the existing end-of-post CTA's conversion (the
two CTAs serve different reader cohorts: mid-article = high-intent
verifier, end-of-post = full-read summariser).

This replicates the EXP-010 inline-CTA pattern on the project's
flagship litre-bike comparison post. EXP-010 ran on the Indian-mid-cc
NS200 vs RTR 200 cohort; EXP-017 isolates whether the same pattern
holds on a higher-intent, higher-trap-speed comparison cohort with
different visitor demographics (litre-bike searchers tend to be
modders / drag-strip regulars rather than first-bike commuters).

## What variants render

### Variant A (control, default — no flag)

The article flows exactly as published on 8 May 2026:

```
Stock-Sim Results <h2>
  paragraph (matched-conditions framing)
  table  (ET / trap / 60-ft / 1-8 / top-gear / cluster bias)
  paragraph  (10.4712 s reference + cluster bias commentary)
  callout    (stock vs modded disclaimer)
<h2> Where the ZX-14R Wins: Top-End Pull
  ... rest of article ...
```

The end-of-post CTA card at line 384 (`"Run your own Hayabusa-vs-ZX-14R"`)
is the only simulator affordance on the page.

### Variant B (`?variant=B`)

Identical to A, plus a glass CTA card injected between the stock-vs-
modded callout and the next h2:

```jsx
<div
  data-exp="EXP-017"
  data-variant="B"
  className="my-10 glass rounded-xl p-5 border border-brand-orange/30
             flex flex-col sm:flex-row items-center gap-4"
>
  <div className="flex-1">
    <div className="font-display font-bold text-white text-base mb-1">
      Want to run this matchup yourself?
    </div>
    <div className="text-white/65 text-sm leading-relaxed">
      Pick Hayabusa and ZX-14R side-by-side, dial rider weight, ambient
      temp, and tire choice, and watch the 0.12 s gap move in real time.
    </div>
  </div>
  <Link
    href="/simulator"
    data-exp="EXP-017"
    data-variant="B"
    data-cta="blog-inline-mid-article"
    data-post="hayabusa-vs-zx-14r-which-is-faster"
    className="shrink-0 px-4 py-2 bg-brand-orange text-black
               font-display font-bold rounded-lg text-sm
               hover:bg-brand-orangeLight transition-colors"
    aria-label="Run a quarter-mile simulation comparing Hayabusa Gen1 and ZX-14R"
  >
    Run this comparison →
  </Link>
</div>
```

The end-of-post CTA card at line 384 is preserved unchanged on both
arms — this is an additive test, not a replacement.

## How to read traffic

The variant is selected by URL search param at render time. Both arms
serve the same canonical URL (`https://motoquant.in/blog/hayabusa-vs-
zx-14r-which-is-faster`) and the same metadata / JSON-LD article
schema — crawlers see the control payload (variant B's CTA is hidden
in SSR because `useSearchParams` returns null during prerender).

### PostHog (preferred, once instrumented)

1. Define an event `experiment_cta_click` triggered by any `<a>` with a
   `data-exp` attribute, capturing all `data-*` attributes as event
   properties.
2. Cohort the post's visitor stream by URL contains
   `/blog/hayabusa-vs-zx-14r-which-is-faster` and split arms by URL
   `searchParams.variant` (`A` = absent or any value ≠ `B`; `B` = `B`).
3. The conversion event is `simulator_run_started` (from the
   `/simulator` page). Stitch via `distinct_id` over a 30-minute window
   after the post visit.
4. Pull the funnel: post visit → CTA click (if any) → `/simulator`
   landing → first run. Compare CTR (`CTA click / post visit`) and
   primary metric (`simulator_run_started / post visit`) across arms.

### GA4 fallback

1. Custom event `select_content` on the inline CTA's click, with
   `content_type=blog_inline_cta` and `item_id=EXP-017`.
2. Use audience segmentation by `page_referrer` containing
   `/blog/hayabusa-vs-zx-14r-which-is-faster` on the `/simulator` page,
   and segment by URL parameter `variant`.

### Manual log inspection (until analytics land)

Vercel access logs include the full request URL. Pre-aggregate:

- `total_post_visitors`: count distinct IPs requesting
  `/blog/hayabusa-vs-zx-14r-which-is-faster` per day.
- `variant_b_visitors`: same with `?variant=B` in query.
- `simulator_referrals_a` vs `simulator_referrals_b`: count distinct
  IPs that hit `/simulator` within 5 minutes of a post visit, split by
  whether the post visit URL had `?variant=B`.

The natural traffic split is roughly 95 / 5 (organic + Related links
don't carry the flag), so until paid traffic or QR codes split it
evenly, expect ~3 weeks to accumulate 200 samples on arm B at current
post traffic of ~30 visits/day.

## Pass / fail criteria

**Pass** (ship B as new control) if all three hold:

1. `simulator_runs / post_visitor` lifts **≥ 15 %** on arm B with
   `p < 0.05` over **≥ 200 samples per arm**.
2. `post_bounce_rate` does not rise **> 10 %** vs. site-wide baseline.
3. `simulator_page_first_run_completion_rate` from the post referrer
   does not drop **> 10 %** (intent should be high since they just saw
   the stock-sim ET numbers; a completion-rate collapse means the CTA
   is recruiting low-intent skimmer clicks).

**Roll back** if either holds:

1. `post_scroll_depth_75pct` drops **> 10 %** on arm B (the inline CTA
   is intercepting scrollers and bouncing them out of the funnel
   before they read the rest of the article).
2. `blog_end_of_post_cta_ctr` drops **> 30 %** in absolute terms
   (inline card cannibalising the existing end-of-post CTA without net
   lift = failed test).

**No decision** before 200 samples per arm.

## Follow-up experiments if B wins

(a) **Copy retest on the headline** — `"Want to run this matchup
    yourself?"` (current B, question-first) vs proof-anchored
    `"See the 0.12 s gap close on your launch RPM"` (numbers-first
    framing).

(b) **Replicate** the mid-article inline-CTA placement on the next two
    highest-traffic comparison posts:
    - `/blog/suzuki-gsx-s750-vs-ktm-890-duke-quarter-mile`
    - `/blog/honda-hornet-2-0-vs-pulsar-ns200-quarter-mile`

(c) **Placement test** within comparison-post articles:
    - current B = immediately after the stock-sim table + callout
    - B' = immediately after the callout + one paragraph deeper
    - B'' = immediately before the parts-ROI / stage-1 table further
            into the article

Find the highest-converting intent moment within the cohort.

## Files touched

- `web/app/blog/hayabusa-vs-zx-14r-which-is-faster/InlineSimCta.js`
  (NEW — variant component, default-exports a `<Suspense>`-wrapped CTA)
- `web/app/blog/hayabusa-vs-zx-14r-which-is-faster/page.js`
  (MOD — imports `InlineSimCta`, adds `{type:'inline_cta_slot'}` block,
   extends `Prose` renderer with a case that delegates to the variant)
- `data/growth_experiments.json` (MOD — appended EXP-017 entry,
   bumped `updated` field)
- `reports/growth_exp_EXP-017_2026-05-25.md` (NEW — this file)

## Reversibility

One-step rollback: delete the import line + the `{type:'inline_cta_slot'}`
block + the `if (block.type === 'inline_cta_slot')` case + the
`InlineSimCta.js` file. JSON entry → mark `status: "killed"` and append
postmortem.
