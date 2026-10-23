'use client';

// GROWTH_EXP_013 — /whitepaper terminal-CTA copy retest
//
// A (control)  = "Run a simulation →" + "See the engine for yourself."
// B (variant)  = "See your bike against our 74 benchmarks →" +
//                "Pick your bike. Get a quarter-mile ET from the same physics
//                you just read about."
//
// Hypothesis: visitors who finish the whitepaper have absorbed 10 sections of
// methodology, results, baselines, and limitations. They sit at peak technical
// credibility but the current terminal CTA describes mechanism ("run a
// simulation") rather than the concrete output the reader will receive from
// having just read 74-benchmark validation data ("see your bike against those
// 74 benchmarks"). Verb-result framing that grounds the just-established
// credibility into a specific first-run promise should lift /simulator CTR
// from /whitepaper without disturbing the two sibling cards (Physics docs,
// Validation data) which serve different reader cohorts.
//
// Single-variable test: ONLY the third card's button label and subhead change.
// h2 ("Continue reading"), the two sibling cards (Physics docs, Validation
// data), the card href (/simulator), the card border + bg styling, the
// surrounding article structure, meta tags, h1, and the cover-stat grid are
// all byte-identical across arms.
//
// SEO-safe: Suspense fallback renders variant A markup verbatim so SSR/SSG
// output is byte-identical to pre-EXP-013. data-exp + data-variant on the
// Link itself so click-attribution survives without analytics infra.
//
// No page conflict: /whitepaper had zero live experiments. EXP-001 landing,
// EXP-002+005 /pricing (retired Oct 2026 with the page), EXP-003 /simulator, EXP-004 /blog/the-physics-of-a-
// perfect-launch post body, EXP-006 /blog index, EXP-007 /login, EXP-008
// /features, EXP-009 /bikes catalog, EXP-010 /blog/pulsar-ns200-vs-apache-rtr-
// 200-quarter-mile-physics, EXP-011 /bikes/[id], EXP-012 /about.

import Link from 'next/link';
import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';

const COPY = {
  A: {
    title: 'Run a simulation →',
    subhead: 'See the engine for yourself.',
  },
  B: {
    title: 'See your bike against our 74 benchmarks →',
    subhead:
      'Pick your bike. Get a quarter-mile ET from the same physics you just read about.',
  },
};

function Card({ variant }) {
  const c = COPY[variant];
  return (
    <Link
      href="/simulator"
      data-exp="EXP-013"
      data-variant={variant}
      data-cta="whitepaper-terminal"
      className="group rounded-xl border border-accent/40 hover:border-accent bg-asphalt-2/80 p-5 transition-colors"
    >
      <div className="font-display font-semibold text-accent">{c.title}</div>
      <div className="text-sm text-white/65 mt-1">{c.subhead}</div>
    </Link>
  );
}

function VariantInner() {
  const params = useSearchParams();
  const variant = params?.get('variant') === 'B' ? 'B' : 'A';
  return <Card variant={variant} />;
}

export default function TerminalCtaVariant() {
  // Fallback is variant A so SSR/SSG markup matches the pre-EXP-013 control
  // byte-for-byte. Hydration then promotes to B only if ?variant=B is present.
  return (
    <Suspense fallback={<Card variant="A" />}>
      <VariantInner />
    </Suspense>
  );
}
