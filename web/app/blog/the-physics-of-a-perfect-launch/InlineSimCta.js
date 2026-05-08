'use client';

// GROWTH_EXP_004 — blog post inline-simulator CTA placement
//
// A (control)  = no inline CTA (existing pattern: single end-of-post card)
// B (variant)  = pull-quote-style inline CTA after the 2nd H2, mid-scroll
//
// Hypothesis: blog readers who scroll past the 2nd H2 hit a natural section
// break; an inline CTA there should outperform the end-of-post CTA where
// the reader is already mentally exiting. Single-variable test (placement
// only — copy + href identical to the end-of-post card so we are not
// confounding placement with copy).
//
// Default = A. Flag = ?variant=B. Same canonical URL, same h1, same meta —
// SEO-safe. data-exp/data-variant on the wrapper for analytics attribution.
// EXP-001 is on landing-hero, EXP-002 on /pricing, EXP-003 on /simulator —
// no page conflict.

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';

export default function InlineSimCta() {
  const searchParams = useSearchParams();
  const variant = searchParams?.get('variant') === 'B' ? 'B' : 'A';

  // Variant A is pixel-identical to the pre-experiment control: nothing
  // renders here. The end-of-post CTA card below remains untouched on both
  // arms so this is purely an additive A/B on the inline slot.
  if (variant !== 'B') {
    return <span data-exp="EXP-004" data-variant="A" hidden />;
  }

  return (
    <div
      data-exp="EXP-004"
      data-variant="B"
      className="my-10 px-5 py-5 rounded-xl border-l-4 border-brand-orange bg-brand-orange/10 flex flex-col sm:flex-row items-start sm:items-center gap-4"
    >
      <div className="flex-1">
        <div className="font-display font-bold text-white text-base mb-1">
          Try this on your bike — right now
        </div>
        <div className="text-white/70 text-sm leading-relaxed">
          Pick your bike, set the launch RPM, and see the 60-ft + ET change live. Free, no signup.
        </div>
      </div>
      <Link
        href="/simulator"
        data-exp="EXP-004"
        data-variant="B"
        data-cta="inline-mid-post"
        className="shrink-0 px-5 py-2.5 bg-brand-orange text-black font-display font-bold rounded-lg text-sm hover:bg-brand-orangeLight transition-colors"
      >
        Run sim →
      </Link>
    </div>
  );
}
