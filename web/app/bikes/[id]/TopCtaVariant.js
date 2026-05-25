'use client';

/**
 * EXP-011 — Top "Simulate this bike" CTA copy variant on /bikes/[id] detail.
 *
 * Hypothesis:
 *   Visitors who reach the bike-detail page are at peak intent — they have
 *   just selected the bike they want to know about. The current top CTA
 *   ("Simulate this bike →") describes the mechanism (run a simulation),
 *   not the answer the visitor came for ("how fast is THIS bike?"). A
 *   verb-result CTA that names the concrete output ("See its quarter-mile
 *   ET →") should lift CTR from the bike-detail page to /simulator without
 *   any other layout, copy, or routing change.
 *
 * Variants:
 *   A (control, default)  — "Simulate this bike →"
 *   B (?variant=B)        — "See its quarter-mile ET →"
 *
 * Only the top CTA copy changes across arms. The bottom CTA card (the
 * centered Simulate this bike / Back to catalog pair) is intentionally
 * unchanged on both arms so the experiment isolates copy as the single
 * variable, not placement or surface count.
 *
 * Same canonical URL, same h1, same metadata, same href
 * (/simulator?bike_id=<id>) — SEO-safe and single-variable per CLAUDE.md.
 *
 * Implementation note: useSearchParams() must live inside a Suspense
 * boundary or Next.js static-export fails with
 * `missing-suspense-with-csr-bailout` (see CLAUDE.md hygiene section).
 * Suspense fallback renders the control copy so SSR/initial paint is
 * byte-identical to pre-EXP-011.
 */

import { Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Gauge } from 'lucide-react';

function TopCtaInner({ bikeId }) {
  const params = useSearchParams();
  const variant = params?.get('variant') === 'B' ? 'B' : 'A';

  const label = variant === 'B' ? 'See its quarter-mile ET' : 'Simulate this bike';

  return (
    <Link
      href={`/simulator?bike_id=${bikeId}`}
      data-exp="EXP-011"
      data-variant={variant}
      data-cta="bike-detail-top"
      data-bike-id={bikeId ?? ''}
      className="shrink-0 inline-flex items-center gap-2 px-5 py-3 bg-brand-orange text-black font-display font-bold rounded-xl transition-all hover:shadow-[0_0_30px_rgba(255,94,31,0.4)] text-sm"
    >
      <Gauge size={16} /> {label} →
    </Link>
  );
}

// Control-equivalent fallback so SSR/initial paint matches the pre-EXP-011
// output. Same href, same styling, same data-* attributes minus the variant
// (it gets filled in once the client picks up search params).
function TopCtaFallback({ bikeId }) {
  return (
    <Link
      href={`/simulator?bike_id=${bikeId}`}
      data-exp="EXP-011"
      data-variant="A"
      data-cta="bike-detail-top"
      data-bike-id={bikeId ?? ''}
      className="shrink-0 inline-flex items-center gap-2 px-5 py-3 bg-brand-orange text-black font-display font-bold rounded-xl transition-all hover:shadow-[0_0_30px_rgba(255,94,31,0.4)] text-sm"
    >
      <Gauge size={16} /> Simulate this bike →
    </Link>
  );
}

export default function TopCtaVariant({ bikeId }) {
  return (
    <Suspense fallback={<TopCtaFallback bikeId={bikeId} />}>
      <TopCtaInner bikeId={bikeId} />
    </Suspense>
  );
}
