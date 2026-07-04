'use client';

// GROWTH_EXP_016 — /docs/physics post-sub-models simulator CTA (presence test)
//
// A (control)  = no inline CTA after the 15-sub-models grid (current state;
//                only the two terminal "Next" nav cards "Validation Data" +
//                "Run your first sim" render at the page end — byte-identical
//                across arms on the control).
// B (variant)  = one glass CTA card injected immediately after the 15-sub-models
//                section (between the sub-models grid and the BikeConfig section).
//                Copy: "See all 15 sub-models fire on your bike →"
//                Subhead: "Pick your bike. Run the quarter mile. Real RK4 physics
//                — no install, no signup."
//
// Hypothesis: readers who scroll through all 15 sub-model rows are at a peak
// "this is technically serious" credibility inflection point — they have just
// absorbed engine torque model, Pacejka magic formula, weight transfer, clutch
// dynamics, etc. The page currently gives no in-article affordance to act on
// that understanding: the only simulator link is buried in a two-equal-weight
// nav card block at the very end of a 4-section article. Placing a single CTA
// card at the natural "I just saw the engine — now I want to see it run" moment
// (immediately after the sub-models list, before the BikeConfig prose that
// requires additional technical background) should lift simulator-runs /
// physics-page-visitor without changing nav structure or breaking the reader's
// sense that the page is a doc, not a sales sheet.
//
// Single-variable test: ONLY the presence of one inline CTA card changes. The
// BikeConfig section, the Numerical Integrator section, the Overview section,
// the terminal Next nav cards, the article H1, the 15 sub-model rows, meta
// tags, and the docs sidebar are byte-identical across arms.
//
// SEO-safe: Suspense fallback is null (variant A branch) so SSR/SSG output is
// byte-identical to pre-EXP-016. Hydration promotes to B only if ?variant=B is
// present. Same canonical URL on both arms (https://motoquant.in/docs/physics).
// data-exp + data-variant + data-cta on the Link element so click-attribution
// survives without analytics infra.
//
// No page conflict: /docs/physics had zero live experiments. Existing experiments:
// EXP-001 landing, EXP-002 + EXP-005 /pricing, EXP-003 /simulator, EXP-004
// /blog/the-physics-of-a-perfect-launch, EXP-006 /blog index, EXP-007 /login,
// EXP-008 /features, EXP-009 /bikes catalog, EXP-010
// /blog/pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics, EXP-011 /bikes/[id],
// EXP-012 /about, EXP-013 /whitepaper, EXP-014 /docs/getting-started,
// EXP-015 /docs/validation.

import Link from 'next/link';
import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';

function CtaCard() {
  return (
    <div className="my-10">
      <Link
        href="/simulator"
        data-exp="EXP-016"
        data-variant="B"
        data-cta="physics-post-submodels"
        className="group block glass rounded-xl p-6 border border-brand-orange/40 hover:border-brand-orange bg-brand-orange/[0.04] transition-colors"
      >
        <div className="flex flex-col sm:flex-row sm:items-center gap-4 sm:gap-6">
          <div className="flex-1">
            <div className="font-display font-bold text-lg text-brand-orange mb-1 group-hover:text-white transition-colors">
              See all 15 sub-models fire on your bike →
            </div>
            <div className="text-sm text-white/65 leading-relaxed">
              Pick your bike. Run the quarter mile. Real RK4 physics — no install, no signup.
            </div>
          </div>
          <div className="shrink-0 hidden sm:flex flex-col items-end font-mono text-[10px] text-white/40 uppercase tracking-widest">
            <span>541 bikes</span>
            <span>1 ms timestep</span>
            <span>15 sub-models</span>
          </div>
        </div>
      </Link>
    </div>
  );
}

function SubModelsCtaInner() {
  const params = useSearchParams();
  const variant = params?.get('variant') === 'B' ? 'B' : 'A';
  if (variant !== 'B') return null;
  return <CtaCard />;
}

export default function SubModelsCtaVariant() {
  // Suspense fallback is null (variant A) so SSR/SSG markup is byte-identical
  // to pre-EXP-016. Hydration promotes to B only if ?variant=B is present.
  return (
    <Suspense fallback={null}>
      <SubModelsCtaInner />
    </Suspense>
  );
}
