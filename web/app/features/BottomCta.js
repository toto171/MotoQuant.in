'use client';

import { Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Zap } from 'lucide-react';

function BottomCtaInner() {
  const params = useSearchParams();
  const variant = params.get('variant') === 'B' ? 'B' : 'A';

  // EXP-008: features bottom-CTA copy.
  // Variant A (control): "Try it free" — generic.
  // Variant B: outcome + time-bound proof on the CTA itself.
  const primaryLabel = variant === 'B' ? 'Run a sim — 15 seconds, no signup' : 'Try it free';
  const subhead =
    variant === 'B'
      ? 'Pick a bike, hit go. Real physics in your browser — no install, no account.'
      : 'Free in the browser. No account required to start.';

  return (
    <div
      className="max-w-3xl mx-auto text-center"
      data-exp="EXP-008"
      data-variant={variant}
    >
      <h2 className="font-display font-bold uppercase leading-[0.95] tracking-[-0.01em] text-4xl mb-4 text-white">
        Ready to run your first sim?
      </h2>
      <p className="text-white/65 mb-10 text-lg">{subhead}</p>
      <div className="flex flex-col sm:flex-row gap-4 justify-center">
        <Link
          href="/simulator"
          data-exp="EXP-008"
          data-variant={variant}
          data-cta="features-bottom-primary"
          className="btn-primary"
        >
          <Zap size={18} /> {primaryLabel}
        </Link>
        <Link href="/pricing" className="btn-ghost">
          See pricing
        </Link>
      </div>
    </div>
  );
}

export default function BottomCta() {
  return (
    <Suspense
      fallback={
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="font-display font-bold uppercase leading-[0.95] tracking-[-0.01em] text-4xl mb-4 text-white">
            Ready to run your first sim?
          </h2>
          <p className="text-white/65 mb-10 text-lg">
            Free in the browser. No account required to start.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/simulator" className="btn-primary">
              <Zap size={18} /> Try it free
            </Link>
            <Link href="/pricing" className="btn-ghost">
              See pricing
            </Link>
          </div>
        </div>
      }
    >
      <BottomCtaInner />
    </Suspense>
  );
}
