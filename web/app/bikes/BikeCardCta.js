'use client';

/**
 * EXP-009 — Inline simulator CTA on /bikes catalog cards.
 *
 * Hypothesis:
 *   Visitors browsing /bikes scroll the grid looking for their bike, click
 *   into the detail page to read specs, and never reach the simulator from
 *   the catalog. The current cards have one and only one action (Link →
 *   /bikes/<id>). An inline "Run sim" affordance on each card — same
 *   canonical URL, default off — should produce more sim runs per /bikes
 *   visit.
 *
 * Variants:
 *   A (control, default)  — no extra CTA. Cards are link-only.
 *   B (?variant=B)        — small "Run sim" pill rendered in the card
 *                           corner, linking to /simulator. Card body still
 *                           links to /bikes/<id>, so the dominant action is
 *                           unchanged; the variant only adds optionality.
 *
 * One variable per CLAUDE.md guidance. Same canonical URL. SEO unaffected.
 *
 * Implementation note: useSearchParams() must live inside a Suspense
 * boundary or Next.js static-export fails with
 * `missing-suspense-with-csr-bailout` (see CLAUDE.md hygiene section).
 */

import { Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Zap } from 'lucide-react';

function VariantPillInner({ bikeId }) {
  const params = useSearchParams();
  const variant = params?.get('variant') === 'B' ? 'B' : 'A';

  if (variant !== 'B') return null;

  // Stop the parent <Link> from swallowing the click — we want this CTA to
  // navigate to /simulator, not /bikes/<id>.
  const onClick = (e) => {
    e.stopPropagation();
  };

  return (
    <Link
      href="/simulator"
      onClick={onClick}
      data-exp="EXP-009"
      data-variant="B"
      data-cta="bikes-card-run-sim"
      data-bike-id={bikeId ?? ''}
      className="inline-flex items-center gap-1 px-2 py-1 rounded-md border border-brand-orange/60 bg-brand-orange/10 text-brand-orange text-[10px] font-mono uppercase tracking-wider hover:bg-brand-orange hover:text-black transition-colors"
      aria-label="Run a quarter-mile simulation"
    >
      <Zap size={10} /> Run sim
    </Link>
  );
}

/**
 * Default-export wrapper. Renders nothing on the control arm or until the
 * client picks up search params, so the SSR/static prerender output is
 * identical to the control.
 */
export default function BikeCardCta({ bikeId }) {
  return (
    <Suspense fallback={null}>
      <VariantPillInner bikeId={bikeId} />
    </Suspense>
  );
}
