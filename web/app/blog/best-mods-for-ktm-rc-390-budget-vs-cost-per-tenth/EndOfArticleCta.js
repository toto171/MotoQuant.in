'use client';

// GROWTH_EXP_019 — RC 390 cost-per-tenth post · end-of-article CTA button copy
//
// A (control)  = "Run sim →"
//                Generic verb-noun, identical to every other end-of-article
//                CTA on the blog. No tie-back to the article topic.
// B (variant)  = "Build my RC 390 ladder →"
//                Outcome-specific copy that mirrors the article's central
//                framing ("cost-per-tenth ladder"). First-person possessive
//                ("my") to nudge ownership intent on a reader who has just
//                spent 13 minutes evaluating mod spend on their own bike.
//
// Hypothesis: a reader who finishes a 13-min mod-shopping article on the
// RC 390 has high commercial intent (they are evaluating ₹10k-₹70k mod
// budgets). The generic "Run sim →" button forces a mental hop from the
// article topic to a generic tool. A button that names the exact outcome
// the article was building toward ("the ladder for my RC 390") removes
// that hop and should lift simulator-runs / article-reader by ≥15%.
//
// Single-variable test: only the button label changes. Heading + subhead +
// href (?bike=ktm-rc-390&venue=aamby-valley) + styling all identical
// across arms so we are not confounding copy with placement or pre-fill.
//
// Default = A. Flag = ?variant=B. Same canonical URL, same h1, same meta —
// SEO-safe (the swapped string is inside a Link, not the page <head>).
// data-exp/data-variant on the Link for analytics attribution. Wrapped in
// <Suspense> at the call site per the Vercel static-prerender rule.
// EXP-001/EXP-018 are landing-hero, EXP-004 is /blog/the-physics-of-a-
// perfect-launch body, EXP-010 is /blog/pulsar-ns200-vs-apache-rtr-200,
// EXP-017 is /blog/hayabusa-vs-zx-14r — no surface conflict.

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';

export default function EndOfArticleCta() {
  const searchParams = useSearchParams();
  const variant = searchParams?.get('variant') === 'B' ? 'B' : 'A';

  const label = variant === 'B' ? 'Build my RC 390 ladder →' : 'Run sim →';

  return (
    <Link
      href="/simulator?bike=ktm-rc-390&venue=aamby-valley"
      data-exp="EXP-019"
      data-variant={variant}
      data-cta="end-of-article-rc390-ladder"
      className="shrink-0 px-5 py-2.5 bg-brand-orange text-black font-display font-bold rounded-lg text-sm hover:bg-brand-orangeLight transition-colors"
    >
      {label}
    </Link>
  );
}
