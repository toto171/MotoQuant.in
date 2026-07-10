'use client';

// GROWTH_EXP_006 — blog index end-of-grid simulator CTA
//
// A (control)  = no terminal CTA — visitors who scroll the whole post grid
//                either click a post card or bounce.
// B (variant)  = end-of-grid CTA card pinned below the post grid, inviting
//                visitors to try the simulator before they leave.
//
// Hypothesis: the blog index has 22 post cards and zero terminal action.
// Readers who scroll the full list are high-intent (they came to learn
// about drag racing physics) but the page offers no off-ramp to /simulator
// at the natural end-of-list breakpoint. A grid-aligned CTA card after the
// last post should lift simulator-runs / blog-index-visitor without
// touching the SEO-stable post list above.
//
// Single-variable test: presence of the end-of-grid CTA. Copy + href fixed
// across the variant arm so we are not confounding placement with copy.
//
// Default = A. Flag = ?variant=B. Same canonical URL, same h1, same meta —
// SEO-safe. data-exp/data-variant on the wrapper + Link for analytics
// attribution. Wrapped in <Suspense> at the call site per the Vercel
// static-prerender rule. EXP-001 is on landing-hero, EXP-002 + EXP-005 on
// /pricing, EXP-003 on /simulator, EXP-004 on /blog/the-physics-of-a-
// perfect-launch — no page conflict (EXP-004 is the post body, EXP-006 is
// the index).

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';

export default function EndOfBlogIndexCta() {
  const searchParams = useSearchParams();
  const variant = searchParams?.get('variant') === 'B' ? 'B' : 'A';

  // Variant A is pixel-identical to the pre-experiment control: nothing
  // renders here. The post grid above stays untouched on both arms so the
  // experiment is a clean additive slot.
  if (variant !== 'B') {
    return <span data-exp="EXP-006" data-variant="A" hidden />;
  }

  return (
    <div
      data-exp="EXP-006"
      data-variant="B"
      className="mt-10 card border-accent/30 p-6 md:p-8 flex flex-col md:flex-row items-start md:items-center gap-5"
    >
      <div className="flex-1">
        <div className="font-display font-semibold uppercase text-white text-xl md:text-2xl mb-2">
          Stop reading. Run the numbers on your bike.
        </div>
        <div className="text-white/65 text-sm md:text-base leading-relaxed">
          Pick your bike, pick a venue, see your quarter-mile ET in 50 ms.
          Free, no signup — the same physics engine these posts are written from.
        </div>
      </div>
      <Link
        href="/simulator"
        data-exp="EXP-006"
        data-variant="B"
        data-cta="end-of-blog-index"
        className="btn-primary shrink-0"
      >
        Run the simulator →
      </Link>
    </div>
  );
}
