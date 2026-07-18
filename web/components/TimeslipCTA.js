'use client';

/**
 * TimeslipCTA — "Ran this bike? Submit your Dragy timeslip" card on the
 * bike detail page (inventory A3-20).
 *
 * Why it exists: real instrumented timeslips are the #1 accuracy lever —
 * most entry-cluster benchmarks are DERIVED estimates because nobody has
 * published a GPS-verified run. A rider who owns the bike on this page is
 * exactly the person who can close that gap, so we ask at the moment of
 * peak relevance.
 *
 * Link target: the simulator's existing calibrate/upload surface. The
 * simulator accepts `?bike_id=` as a preselect alias of `?bike=` (see
 * web/app/simulator/page.js shared-build read-back); there is no tab
 * deep-link param, so the copy names the Upload tab explicitly rather than
 * pretending the link lands on it.
 *
 * Telemetry: fires `timeslip_cta_clicked` via the existing track() export.
 * Called defensively — telemetry must never break navigation.
 */

import Link from 'next/link';
import { Upload } from 'lucide-react';
import { track } from '../lib/telemetry';

export default function TimeslipCTA({ bikeId }) {
  const onClick = () => {
    try {
      track('timeslip_cta_clicked', { bike_id: bikeId ?? null });
    } catch {
      /* never let telemetry block the navigation */
    }
  };

  return (
    <div className="card p-5 flex flex-col sm:flex-row sm:items-center gap-4 border-dashed">
      <div className="flex-1 min-w-0">
        <p className="label-mono mb-2">Own one? · Help calibrate it</p>
        <p className="font-display font-semibold text-white text-base">
          Ran this bike? Submit your Dragy timeslip
        </p>
        <p className="text-sm text-white/65 mt-1.5">
          Real GPS runs feed the calibration corpus directly — every verified
          timeslip tightens the published accuracy for this exact bike. The
          link opens the simulator with this bike preselected; drop your Dragy
          CSV in the <span className="text-white/85">Upload</span> tab.
        </p>
      </div>
      <Link
        href={`/simulator?bike_id=${bikeId}`}
        onClick={onClick}
        data-cta="timeslip-upload"
        data-bike-id={bikeId ?? ''}
        className="btn-ghost shrink-0"
      >
        <Upload size={16} /> Upload a timeslip →
      </Link>
    </div>
  );
}
