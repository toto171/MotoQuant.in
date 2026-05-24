'use client';

/**
 * EXP-010 — Inline "Run this comparison" CTA mid-article on the
 * Pulsar NS200 vs Apache RTR 200 4V comparison post.
 *
 * Hypothesis:
 *   Mid-article readers reach the stock-sim numbers table (~1/3 down the
 *   page) at peak comparison intent — they have just absorbed the spec
 *   sheet and the simulator's ET prediction for both bikes and are now
 *   in the most likely "let me check this myself" mental state of the
 *   read. The page currently has exactly ONE CTA card (line 316) which
 *   sits below the entire 200-line article body; by the time readers
 *   reach it, most have either bounced or scrolled past into the
 *   "Related reading" links. Inserting an inline CTA card immediately
 *   after the stock-sim table — i.e. at the intent peak rather than at
 *   the end of the funnel — should lift simulator_runs/post_visitor
 *   without affecting scroll depth, SEO, or the existing end-of-post
 *   CTA's conversion (the two CTAs serve different reader cohorts).
 *
 * Variants:
 *   A (control, default)  — no mid-article CTA. Existing end-of-post
 *                           CTA card at line 316 is the only simulator
 *                           affordance on the page.
 *   B (?variant=B)        — inline CTA card injected after the stock-sim
 *                           numbers table, linking to /simulator. End-of-
 *                           post CTA is preserved unchanged on both arms.
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
      data-exp="EXP-010"
      data-variant="B"
      className="my-10 glass rounded-xl p-5 border border-brand-orange/30 flex flex-col sm:flex-row items-center gap-4"
    >
      <div className="flex-1">
        <div className="font-display font-bold text-white text-base mb-1">
          Want to test this on your own bike?
        </div>
        <div className="text-white/65 text-sm leading-relaxed">
          Pick NS200 and RTR 200 4V side-by-side, swap rider weight, ambient temp, and tire choice, and watch the ET gap move in real time.
        </div>
      </div>
      <Link
        href="/simulator"
        data-exp="EXP-010"
        data-variant="B"
        data-cta="blog-inline-mid-article"
        data-post="pulsar-ns200-vs-apache-rtr-200"
        className="shrink-0 px-4 py-2 bg-brand-orange text-black font-display font-bold rounded-lg text-sm hover:bg-brand-orangeLight transition-colors"
        aria-label="Run a quarter-mile simulation comparing NS200 and Apache RTR 200 4V"
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
