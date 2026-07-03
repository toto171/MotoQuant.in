'use client';

// GROWTH_EXP_015 — /docs/validation post-methodology credibility CTA
//
// A (control)  = no inline CTA (current state; only the two terminal "Next"
//                nav cards "Getting Started" + "Try the simulator" render
//                below this slot, byte-identical across arms).
// B (variant)  = one glass card injected between the Methodology section and
//                the terminal Next nav, with copy that grounds the just-read
//                ±0.009s top-10 mean error + Δ ±0.0000 baseline drift into a
//                first-run promise:
//                  "Run your bike through the same engine →"
//                  "535 bikes pre-loaded. Same RK4 integrator. Same ±0.009s
//                  top-10 mean error. No signup."
//
// Hypothesis: visitors who reach the bottom of /docs/validation have just
// absorbed 74-benchmark accuracy data, per-cluster bias breakdown, three
// reference baselines (K5 / R1 / Hayabusa, Δ ±0.0000 since Apr 30), and the
// honest "known limitations" disclosure on small-cc and 2T residual bias.
// They sit at peak technical credibility — every objection a skeptical Indian
// drag-scene reader could raise has been preemptively addressed on this page.
// The terminal Next nav presents two equal-weight wayfinding cards
// ("Getting Started" + "Try the simulator"), which reads as documentation
// chrome rather than a conviction CTA. A single inline glass card injected
// right after Methodology — using the exact numbers the reader just saw —
// should lift /simulator CTR without changing nav structure or breaking the
// reader's sense that the page is a doc, not a sales sheet.
//
// Single-variable test: ONLY the presence of one card changes. The two Next
// nav cards (Getting Started + Try the simulator), the article H1, all six
// sections, the cover-stat grid, the cluster table, the methodology prose,
// meta tags, and the docs sidebar are byte-identical across arms.
//
// SEO-safe: Suspense fallback renders the variant A null branch verbatim so
// SSR/SSG output is byte-identical to pre-EXP-015. Hydration promotes to B
// only if ?variant=B is present in the URL. Same canonical URL on both arms
// (https://motoquant.in/docs/validation). data-exp + data-variant on the Link
// itself so click-attribution survives without analytics infra.
//
// No page conflict: /docs/validation had zero live experiments. Existing
// experiments hit landing (EXP-001), /pricing (EXP-002, EXP-005), /simulator
// (EXP-003), two blog posts (EXP-004, EXP-010), /blog index (EXP-006),
// /login (EXP-007), /features (EXP-008), /bikes index (EXP-009),
// /bikes/[id] (EXP-011), /about (EXP-012), /whitepaper (EXP-013), and
// /docs/getting-started (EXP-014).

import Link from 'next/link';
import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';

function CtaCard() {
  return (
    <section className="mb-14">
      <Link
        href="/simulator"
        data-exp="EXP-015"
        data-variant="B"
        data-cta="validation-post-methodology"
        className="group block glass rounded-xl p-6 border border-brand-orange/40 hover:border-brand-orange bg-brand-orange/[0.04] transition-colors"
      >
        <div className="flex flex-col sm:flex-row sm:items-center gap-4 sm:gap-6">
          <div className="flex-1">
            <div className="font-display font-bold text-lg text-brand-orange mb-1 group-hover:text-white transition-colors">
              Run your bike through the same engine →
            </div>
            <div className="text-sm text-white/65 leading-relaxed">
              535 bikes pre-loaded. Same RK4 integrator. Same ±0.009s top-10
              mean error. No signup.
            </div>
          </div>
          <div className="shrink-0 hidden sm:flex flex-col items-end font-mono text-[10px] text-white/40 uppercase tracking-widest">
            <span>K5 · 10.0334s</span>
            <span>R1 · 10.2859s</span>
            <span>Busa · 10.4712s</span>
          </div>
        </div>
      </Link>
    </section>
  );
}

function VariantInner() {
  const params = useSearchParams();
  const variant = params?.get('variant') === 'B' ? 'B' : 'A';
  if (variant !== 'B') return null;
  return <CtaCard />;
}

export default function CredibilityCtaVariant() {
  // Fallback is null (variant A) so SSR/SSG markup matches the pre-EXP-015
  // control byte-for-byte. Hydration then promotes to B only if ?variant=B
  // is present in the URL.
  return (
    <Suspense fallback={null}>
      <VariantInner />
    </Suspense>
  );
}
