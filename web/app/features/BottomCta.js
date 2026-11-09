'use client';

import { Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Zap } from 'lucide-react';

function BottomCtaInner() {
  const params = useSearchParams();
  const variant = params.get('variant') === 'B' ? 'B' : 'A';

  // EXP-008: features bottom-CTA copy.
  // Variant A (control): "Run a sim" — generic.
  // Variant B: outcome + time-bound proof on the CTA itself.
  const primaryLabel = variant === 'B' ? 'Run a sim — 15 seconds, no signup' : 'Run a sim';
  const subhead =
    variant === 'B'
      ? 'Pick a bike, hit go. Real physics in your browser — no install, no account.'
      : 'Free and open source. No account required.';

  return (
    <div
      className="max-w-3xl mx-auto text-center"
      data-exp="EXP-008"
      data-variant={variant}
    >
      <h2 className="font-display font-bold text-4xl tracking-tight mb-4 text-white">
        Ready to run your <span className="text-accent">first sim</span>?
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
        <a
          href="https://github.com/toto171/MotoQuant.in"
          target="_blank"
          rel="noopener noreferrer"
          className="btn-ghost"
        >
          View on GitHub
        </a>
      </div>
    </div>
  );
}

export default function BottomCta() {
  return (
    <Suspense
      fallback={
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="font-display font-bold text-4xl tracking-tight mb-4 text-white">
            Ready to run your <span className="text-accent">first sim</span>?
          </h2>
          <p className="text-white/65 mb-10 text-lg">
            Free and open source. No account required.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/simulator" className="btn-primary">
              <Zap size={18} /> Run a sim
            </Link>
            <a
              href="https://github.com/toto171/MotoQuant.in"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-ghost"
            >
              View on GitHub
            </a>
          </div>
        </div>
      }
    >
      <BottomCtaInner />
    </Suspense>
  );
}
