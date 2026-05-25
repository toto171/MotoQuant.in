'use client';

/**
 * EXP-017 — Inline "Run this comparison" CTA mid-article on the
 * Hayabusa vs ZX-14R "which is faster" comparison post.
 *
 * Hypothesis:
 *   Readers of this comparison post hit peak comparison intent at the
 *   moment the simulator's stock-tune ET numbers are revealed — the
 *   "Stock-Sim Results" table sits ~25% into the article and shows the
 *   ZX-14R at ~10.35 s vs Hayabusa Gen1 at 10.471 s. By the time the
 *   reader reaches the existing end-of-post CTA (line 383, ~400 lines
 *   into the page), most have either bounced or scrolled into the
 *   "Related reading" sidebar. Injecting a single inline CTA card
 *   immediately after the stock-sim table + callout — i.e. at the
 *   intent peak rather than at the bottom of the funnel — should lift
 *   simulator_runs/post_visitor without affecting scroll depth, SEO,
 *   or the existing end-of-post CTA's conversion (the two CTAs serve
 *   different reader cohorts).
 *
 *   This replicates the EXP-010 inline-CTA pattern (NS200 vs RTR 200
 *   comparison post) on the project's flagship litre-bike comparison
 *   post. NS200 vs RTR 200 is an Indian-mid-cc cohort; this one is a
 *   litre-hyper-sport cohort with different traffic intent and a
 *   higher likely simulator-conversion ceiling.
 *
 * Variants:
 *   A (control, default)  — no mid-article CTA. Existing end-of-post
 *                           CTA card at line 383 is the only simulator
 *                           affordance on the page.
 *   B (?variant=B)        — inline CTA card injected after the stock-
 *                           sim numbers table + callout, linking to
 *                           /simulator. End-of-post CTA is preserved
 *                           unchanged on both arms.
 *
 * One variable per CLAUDE.md guidance. Same canonical URL. Meta tags
 * unchanged. SEO unaffected.
 *
 * Implementation note: useSearchParams() must live inside a Suspense
 * boundary or Next.js static-export fails with
 * `missing-suspense-with-csr-bailout` (see CLAUDE.md hygiene section).
 */

import { Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';

function InlineSimCtaInner() {
  const params = useSearchParams();
  const variant = params?.get('variant') === 'B' ? 'B' : 'A';

  if (variant !== 'B') return null;

  return (
    <div
      data-exp="EXP-017"
      data-variant="B"
      className="my-10 glass rounded-xl p-5 border border-brand-orange/30 flex flex-col sm:flex-row items-center gap-4"
    >
      <div className="flex-1">
        <div className="font-display font-bold text-white text-base mb-1">
          Want to run this matchup yourself?
        </div>
        <div className="text-white/65 text-sm leading-relaxed">
          Pick Hayabusa and ZX-14R side-by-side, dial rider weight, ambient temp, and tire choice, and watch the 0.12 s gap move in real time.
        </div>
      </div>
      <Link
        href="/simulator"
        data-exp="EXP-017"
        data-variant="B"
        data-cta="blog-inline-mid-article"
        data-post="hayabusa-vs-zx-14r-which-is-faster"
        className="shrink-0 px-4 py-2 bg-brand-orange text-black font-display font-bold rounded-lg text-sm hover:bg-brand-orangeLight transition-colors"
        aria-label="Run a quarter-mile simulation comparing Hayabusa Gen1 and ZX-14R"
      >
        Run this comparison →
      </Link>
    </div>
  );
}

/**
 * Default-export wrapper. Renders nothing on the control arm or until
 * the client picks up search params, so the SSR/static prerender output
 * is identical to the control. Suspense fallback is null.
 */
export default function InlineSimCta() {
  return (
    <Suspense fallback={null}>
      <InlineSimCtaInner />
    </Suspense>
  );
}
