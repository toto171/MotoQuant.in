'use client';

/**
 * TimeslipCTA — "Ran this bike? Submit your timeslip" card on the bike page.
 *
 * Real instrumented runs are the biggest accuracy lever: many small-bike
 * benchmarks are estimates because nobody has published a GPS-verified run.
 * The rider who owns the bike on this page can close that gap. Submitting
 * opens a prefilled public GitHub issue (reviewed before anything changes);
 * comparing opens the simulator, where a Dragy file is checked against the
 * simulation in the browser session and not stored.
 */

import Link from 'next/link';
import { ExternalLink, Upload } from 'lucide-react';
import { track } from '../lib/telemetry';
import { timeslipIssueUrl } from '../lib/contribute';

export default function TimeslipCTA({ bikeId, bikeName }) {
  const onClick = (action) => () => {
    try {
      track('timeslip_cta_clicked', { bike_id: bikeId ?? null, action });
    } catch {
      /* never let telemetry block the navigation */
    }
  };

  return (
    <div className="card flex flex-col gap-4 border-dashed p-5 sm:flex-row sm:items-center">
      <div className="min-w-0 flex-1">
        <p className="font-display text-base font-semibold text-white">Ran this bike? Submit your timeslip</p>
        <p className="mt-1.5 text-sm text-white/65">
          A real run makes the predictions for this bike more accurate. Submissions are public
          GitHub issues that a maintainer reviews. You can also compare a Dragy file with the
          simulation first: open the simulator, switch to Advanced and use the{' '}
          <span className="text-white/85">My data</span> tab.
        </p>
      </div>
      <div className="flex shrink-0 flex-wrap gap-2">
        <a
          href={timeslipIssueUrl({ bikeName, bikeId })}
          target="_blank"
          rel="noopener noreferrer"
          onClick={onClick('submit')}
          className="btn-primary btn-sm"
        >
          Submit a timeslip <ExternalLink size={14} aria-hidden="true" />
        </a>
        <Link href={`/simulator?bike_id=${bikeId}`} onClick={onClick('compare')} className="btn-ghost btn-sm">
          <Upload size={14} aria-hidden="true" /> Compare
        </Link>
      </div>
    </div>
  );
}
