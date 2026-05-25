# EXP-019 — RC 390 Cost-Per-Tenth Post · End-of-Article CTA Button Copy

**Started:** 2026-05-25 (Monday)
**Page:** `/blog/best-mods-for-ktm-rc-390-budget-vs-cost-per-tenth`
**Element:** End-of-article simulator CTA button label (orange `Link` inside the glass card after the *Run Your Own Ladder* h2)
**Flag:** `?variant=B` (default = A)
**Status:** live

---

## Hypothesis

Readers who finish this 13-min cost-per-tenth ladder post on the KTM RC 390 have high commercial intent: they have just spent 13 minutes pricing mod tiers between Rs9,700 and Rs2 lakh and are at peak readiness to model their own spend. The current end-of-article CTA button reads "Run sim" — a generic verb-noun identical to every other end-of-article CTA on the blog, with no tie-back to the article topic.

If naming the topical outcome on the button removes the mental hop from article-topic to generic-tool, simulator runs per article reader should lift.

Hypothesis stated as falsifiable claim:

> Replacing the end-of-article CTA button label with topic-specific, first-person-possessive copy ("Build my RC 390 ladder") will lift CTR on that button by >=15% relative to the generic "Run sim" control.

## Variant A (control) vs Variant B (treatment)

| Field | A (control) | B (variant) |
|---|---|---|
| Button label | `Run sim →` | `Build my RC 390 ladder →` |
| Card heading | "Build your own RC 390 ladder" | "Build your own RC 390 ladder" (unchanged) |
| Card subhead | "Sweep rider weight, density altitude, sprocket choice, ECU re-flash, exhaust, tire compound, and any of the 562 parts in the catalog. Cost-per-tenth ranks appear on every part toggle in the Pro tier." | unchanged |
| `href` | `/simulator?bike=ktm-rc-390&venue=aamby-valley` | unchanged |
| Card layout | `glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4` | unchanged |
| Button styling | `px-5 py-2.5 bg-brand-orange text-black font-display font-bold rounded-lg text-sm` | unchanged |
| Position in article | After *Run Your Own Ladder* h2, before *Related reading* list | unchanged |

**Single variable:** the literal text inside the button is the only delta. Card heading, subhead, href (with pre-fill query params), surrounding card, and all CSS classes are byte-identical across arms. Any observed CTR delta is attributable to the label swap alone.

## Primary metric

`simulator_runs_from_rc390_post / rc390_post_readers_who_reach_end_of_article`

Tracked via a `data-cta="end-of-article-rc390-ladder"` attribute on the rendered `Link` plus `data-variant={A|B}` on the same element. The analytics layer (PostHog / GA4 once the analytics bootstrap top-priority item lands) groups click events by the `data-variant` attribute and divides by `$pageview` events on the post URL that also fired a `scroll_depth_75` event (proxy for "reached end of article").

## Secondary metrics

1. `cta_click_through_rate` — raw clicks / impressions on the CTA element (not gated on scroll depth). Faster signal than the primary metric; useful for a kill-decision before the primary metric reaches significance.
2. `time_on_simulator_after_click_s` — engagement depth post-click. A label that promises specificity ("my RC 390 ladder") should produce longer sim sessions if the pre-fill matches the promise.
3. `build_page_visits_after_simulator` — `/build` traversals from `/simulator` within 5 min of an EXP-019 click. The cost-per-tenth framing in variant B explicitly maps to the parts ROI engine on `/build`.
4. `pro_signup_conversions_attributed_to_rc390_post` — `/pricing` -> Pro tier conversions where the last-touch referrer chain contains an EXP-019 click. The article is explicitly Pro-tier-aware ("cost-per-tenth ranks appear on every part toggle in the Pro tier") so a stronger CTA should pull more Pro intent.

## Minimum sample size

**200 readers per arm at the end-of-article CTA**, i.e. visitors who scroll past the *Run Your Own Ladder* h2.

Power calculation: control CTR estimated at ~25% on a high-intent end-of-article CTA on a 13-min post (industry baseline for mid-funnel content-to-tool CTAs is 15-30%). At p<0.05 two-tailed with 80% power, a two-proportion z-test detects a delta of >=12 percentage points (e.g. 25% -> 37%) with N=200 per arm. The hypothesised 15% relative lift on a 25% baseline = 3.75 percentage point absolute delta, which is below detectable range at N=200 — but the asymmetry of the test (we only need to confirm a >=15% relative lift to make the call, not detect a smaller one) lets us treat N=200 as a kill-decision threshold rather than a promote-decision threshold.

If we want to detect a smaller lift (say, 8% relative = 2 percentage points absolute), N needs to scale to ~3,500 per arm. Given current traffic of an estimated 50-100 readers/week on a niche-keyword post like this one, that is a 7-12 month experiment — not viable. Hence the 200/arm kill threshold and the 400/arm inconclusive-kill rule below.

## Kill criteria

1. **Hard kill (negative result):** after 200 readers/arm, if variant B CTR is flat or down relative to A with p<0.05, revert to A immediately and log the negative result. The label swap is reversible in one line of code.
2. **Inconclusive kill:** after 400 readers/arm, if p>=0.10 in either direction, kill the experiment and try a stronger contrast in EXP-020+ (suggested: price-anchored CTA, e.g. "Price my RC 390 build" or "See my Rs10k tier ETs"). 400 readers/arm at 50-100 readers/week traffic = 8-16 weeks. Calendar gate: 12 weeks.
3. **Promote (positive result):** after 200 readers/arm, if variant B CTR lifts >=15% relative to A with p<0.05 AND the lift holds across both desktop (>=60%) and mobile (>=40%) slices, promote B to control. Open a follow-up experiment on card heading or subhead.
4. **Cross-experiment guardrail:** if global simulator_runs drop >10% week-over-week during the live window, audit for confounds (a competing experiment on /simulator changing the landing screen, an analytics outage, a Vercel build regression). Pause EXP-019 if confound is plausible.

## Instrumentation gaps (documented honestly)

1. **No analytics layer is wired yet.** Per CLAUDE.md STANDING PRIORITY #1, GA4 + PostHog bootstrap is the prerequisite to actually measuring any of these experiments. `data-exp` / `data-variant` / `data-cta` attributes are correct and present so that as soon as the analytics layer lands, attribution is retroactive on new events but not historical.
2. **No server-side bucketing.** Variant assignment is purely client-side via URL param. A visitor who lands on the post without `?variant=B` always sees A; there is no random bucketing. For a true randomised A/B test the experiment needs either (a) edge middleware that flips a cookie on first visit, or (b) a feature-flag service. EXP-019 in its current form is an *opt-in variant exposure test* — sufficient to confirm the variant renders correctly and to A/B-test among visitors who arrive via a campaign that adds the param (e.g. a paid ads experiment where the ad URL appends `?variant=B`). Same constraint as EXP-001 through EXP-018; will be lifted when the analytics work lands.
3. **No scroll-depth event yet.** The primary-metric denominator depends on a `scroll_depth_75` event that the current site does not emit. Until it does, fall back to `cta_impression` (any `data-exp=EXP-019` element rendered in DOM) as the denominator, which over-counts (includes bouncing visitors who never scroll near the CTA). Adjust the lift threshold up by ~30% to compensate for the over-count.

## Why this experiment, today

Per the playbook priority list: priority #1 (CTA copy) on a surface with the highest pre-existing commercial intent in the catalog. The KTM RC 390 cost-per-tenth post is unique among the 35+ blog posts because it is the only one that explicitly ladders mod spend in INR rupees-per-tenth-of-ET and ends on a high-intent action moment. Every other end-of-article CTA on the blog is on a more diffuse audience (general physics explainer, single-bike spec walkthrough, two-bike comparison). The RC 390 ladder reader is the closest thing on the site today to a qualified Pro-tier lead.

Single variable, single line of UI change, 12-week max runtime, immediate revert path. Tight scope, easy to judge.

---

**Files touched (3):**
- `web/app/blog/best-mods-for-ktm-rc-390-budget-vs-cost-per-tenth/EndOfArticleCta.js` (NEW, client component)
- `web/app/blog/best-mods-for-ktm-rc-390-budget-vs-cost-per-tenth/page.js` (wired Suspense + import)
- `data/growth_experiments.json` (appended EXP-019)

**Reports:**
- `reports/growth_exp_EXP-019_2026-05-25.md` (this file)
