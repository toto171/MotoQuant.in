'use client';

/**
 * /runs — runs saved in this browser.
 *
 * There are no accounts. "Save this run" in the simulator stores the run here
 * (localStorage, see lib/runs.js); nothing is sent to a server. Each entry
 * opens its timeslip, which re-runs the setup with the current physics.
 */

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowRight, Trash2 } from 'lucide-react';
import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import PageHero from '../../components/PageHero';
import { clearRuns, deleteRun, listRuns, onRunsChange } from '../../lib/runs';
import { conditionsSummary } from '../../lib/timeslip';

function changeCount(run) {
  let n = (run.parts || []).length;
  if (run.powerBoost) n += 1;
  if (run.massChange) n += 1;
  if (run.tyresChanged) n += 1;
  return n;
}

export default function RunsPage() {
  const [runs, setRuns] = useState(null); // null until read on the client
  const [confirmClear, setConfirmClear] = useState(false);

  useEffect(() => {
    const read = () => setRuns(listRuns());
    read();
    return onRunsChange(read);
  }, []);

  return (
    <main id="main" className="min-h-screen bg-asphalt-0 text-white">
      <SiteNav />
      <PageHero
        kicker="Your runs"
        title="Runs saved in this browser"
        sub="Save a run from the simulator and it appears here. Nothing is uploaded: the list lives in this browser only, so clearing your browser data clears it too."
      />
      <section className="px-4 pb-20 sm:px-6">
        <div className="mx-auto max-w-3xl">
          {runs === null ? null : runs.length === 0 ? (
            <div className="card card-pad text-center">
              <p className="text-white/80">You have not saved a run in this browser yet.</p>
              <Link href="/simulator" className="btn-primary mt-5 inline-flex">
                Open the simulator <ArrowRight size={16} aria-hidden="true" />
              </Link>
            </div>
          ) : (
            <>
              <ul className="space-y-3">
                {runs.map((run) => {
                  const n = changeCount(run);
                  return (
                    <li key={run.id} className="card flex flex-wrap items-center gap-4 px-5 py-4">
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-display font-semibold text-white">{run.bikeName}</p>
                        <p className="mt-0.5 text-sm text-white/60">
                          {conditionsSummary(run.environment)}
                        </p>
                        <p className="mt-0.5 text-sm text-white/55">
                          {n === 0 ? 'Stock' : n === 1 ? '1 change from stock' : `${n} changes from stock`}
                          {run.savedAt ? ` · saved ${new Date(run.savedAt).toLocaleDateString('en-IN')}` : ''}
                        </p>
                      </div>
                      <p className="font-display text-2xl font-bold tabular-nums text-accent">
                        {Number(run.et).toFixed(3)}
                        <span className="ml-0.5 text-sm font-semibold text-white/60">s</span>
                      </p>
                      <div className="flex items-center gap-2">
                        <Link href={`/timeslip?${run.query}`} className="btn-ghost btn-sm">
                          Timeslip
                        </Link>
                        <button
                          type="button"
                          onClick={() => deleteRun(run.id)}
                          aria-label={`Delete the saved ${run.bikeName} run`}
                          className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-white/[0.12] text-white/60 transition-colors hover:border-signal-foul/50 hover:text-signal-foul"
                        >
                          <Trash2 size={15} aria-hidden="true" />
                        </button>
                      </div>
                    </li>
                  );
                })}
              </ul>
              <div className="mt-6 flex flex-wrap items-center justify-between gap-3 text-sm text-white/55">
                <p>
                  The time shown is the one you saved. A timeslip re-runs the setup, so it can
                  differ slightly after the simulator is updated.
                </p>
                {confirmClear ? (
                  <span className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => {
                        clearRuns();
                        setConfirmClear(false);
                      }}
                      className="btn-ghost btn-sm text-signal-foul"
                    >
                      Delete all {runs.length}
                    </button>
                    <button type="button" onClick={() => setConfirmClear(false)} className="btn-ghost btn-sm">
                      Keep them
                    </button>
                  </span>
                ) : (
                  <button type="button" onClick={() => setConfirmClear(true)} className="btn-ghost btn-sm">
                    Delete all
                  </button>
                )}
              </div>
            </>
          )}
        </div>
      </section>
      <SiteFooter />
    </main>
  );
}
