'use client';

/**
 * /timeslip — a shareable timeslip for one run.
 *
 * The link carries the setup (bike, upgrades, tyres and the exact conditions
 * as numbers; see lib/runs.js). This page sends it to the simulator and shows
 * what comes back, so the time on a shared slip is always one the physics
 * produced. Anything changed from stock is listed on the slip itself.
 */

import { Suspense, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { AlertCircle, Check, Printer, Share2 } from 'lucide-react';
import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import ResultSentence from '../../components/ResultSentence';
import Term from '../../components/Term';
import PrintTimeslip from '../../components/PrintTimeslip';
import { Skeleton } from '../../components/Skeleton';
import { API_URL } from '../../lib/api';
import { timeslipRequest } from '../../lib/runs';
import { conditionsSummary, changesFromStock } from '../../lib/timeslip';

function TimeslipView() {
  const params = useSearchParams();
  const query = params.toString();
  const body = useMemo(() => timeslipRequest(new URLSearchParams(query)), [query]);
  const [run, setRun] = useState(null);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!body) return undefined;
    let cancelled = false;
    setRun(null);
    setError(null);
    fetch(`${API_URL}/api/simulate/quick`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
      .then(async (r) => {
        if (r.ok) return r.json();
        let detail = '';
        try {
          const j = await r.json();
          detail = typeof j?.detail === 'string' ? j.detail : '';
        } catch {
          /* status only */
        }
        const e = new Error(detail || String(r.status));
        e.status = r.status;
        e.detail = detail;
        throw e;
      })
      .then((d) => {
        if (!cancelled) setRun(d);
      })
      .catch((e) => {
        if (!cancelled) setError(e);
      });
    return () => {
      cancelled = true;
    };
  }, [body, attempt]);

  const changes = useMemo(() => (run ? changesFromStock(body, run) : []), [body, run]);
  const riderKg = Number.isFinite(Number(body?.rider_mass_kg)) ? Number(body.rider_mass_kg) : 75;
  const conditions = run ? conditionsSummary(run.environment) : '';
  const splits = run
    ? [
        { label: 'First 60 ft (launch)', term: 'sixty', value: run.et_60ft_s },
        { label: 'Halfway — ⅛ mile', term: 'eighth', value: run.et_eighth_s },
      ].filter((s) => s.value != null)
    : [];

  const doShare = async () => {
    const url = window.location.href;
    const text = run
      ? `${run.bike_name}: a simulated ${Number(run.et_quarter_s).toFixed(3)} s quarter mile on MotoQuant`
      : 'MotoQuant timeslip';
    if (navigator.share) {
      try {
        await navigator.share({ title: 'MotoQuant timeslip', text, url });
        return;
      } catch {
        /* dismissed: fall through to copying the link */
      }
    }
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard unavailable */
    }
  };

  let message = null;
  if (!body) {
    message = 'This link does not name a bike, so there is nothing to show.';
  } else if (error) {
    if (error.status === 404) {
      message = /^(Bike|Venue|Tire) .* not found/i.test(error.detail || '')
        ? `This run cannot be shown: ${error.detail}. The catalog has changed since the link was made.`
        : 'This run cannot be shown: something in the link is no longer in the catalog.';
    } else if (error.status === 422) {
      message = error.message || 'This link describes a setup the simulator cannot run.';
    } else if (error.status === 429) {
      message = 'Too many requests from this connection. Please try again in a minute.';
    } else {
      message = 'We could not reach the simulator. The server may be waking up, which can take up to a minute.';
    }
  }
  const canRetry = body && error && ![404, 422].includes(error.status);

  return (
    <main
      id="main"
      className="min-h-screen bg-asphalt-0 text-white print:min-h-0 print:bg-[rgb(255_255_255)] print:text-[rgb(0_0_0)]"
    >
      <div className="print:hidden">
        <SiteNav />
      </div>
      <section className="px-4 pb-16 pt-28 sm:px-6 md:pb-24 md:pt-32 print:hidden">
        <div className="mx-auto max-w-md">
          {message && (
            <div className="card border-signal-foul/30 px-5 py-4">
              <div className="flex flex-wrap items-center gap-3 text-sm text-signal-foul/90">
                <AlertCircle size={16} className="shrink-0 text-signal-foul" aria-hidden="true" />
                <span className="min-w-[200px] flex-1">{message}</span>
                {canRetry ? (
                  <button type="button" onClick={() => setAttempt((a) => a + 1)} className="btn-ghost btn-sm">
                    Try again
                  </button>
                ) : (
                  <Link href="/simulator" className="btn-ghost btn-sm">
                    Open the simulator
                  </Link>
                )}
              </div>
            </div>
          )}

          {body && !error && !run && (
            <div className="timeslip space-y-4" aria-busy="true" aria-label="Running the simulation">
              <Skeleton className="h-3 w-40" />
              <Skeleton className="h-8 w-2/3" />
              <Skeleton className="h-3 w-1/2" />
              <div className="flex flex-col items-center gap-3 py-6">
                <Skeleton className="h-3 w-24" />
                <Skeleton className="h-14 w-52" />
              </div>
              {[...Array(4)].map((_, i) => (
                <Skeleton key={i} className="h-4 w-full" />
              ))}
            </div>
          )}

          {run && (
            <>
              <article className="timeslip">
                <p className="text-sm font-medium text-white/60">MotoQuant simulated timeslip</p>
                <h1 className="mt-3 font-display text-2xl font-bold tracking-tight">{run.bike_name}</h1>
                <p className="mt-1 text-sm text-white/65">{conditions}</p>

                <div className="centerline mt-5" aria-hidden="true" />

                <div className="py-7 text-center">
                  <p className="text-sm font-medium text-white/65">
                    <Term k="et">Quarter-mile time</Term>
                  </p>
                  <p className="mt-2 font-display text-6xl font-bold tabular-nums text-accent md:text-7xl">
                    {Number(run.et_quarter_s).toFixed(3)}
                    <span className="ml-1 text-2xl font-semibold text-white/60">s</span>
                  </p>
                  <ResultSentence
                    className="mt-4 text-left"
                    bikeName={run.bike_name}
                    riderKg={riderKg}
                    et={Number(run.et_quarter_s)}
                    trapKmh={run.trap_speed_kmh ? Number(run.trap_speed_kmh) : null}
                    venueName={run.environment?.source === 'venue' ? run.environment.name : null}
                    build={changes.length ? 'modified' : 'stock'}
                  />
                </div>

                <div>
                  {splits.map((s) => (
                    <div key={s.label} className="timeslip-row">
                      <span className="font-sans text-white/70">
                        <Term k={s.term}>{s.label}</Term>
                      </span>
                      <span className="font-semibold">{Number(s.value).toFixed(3)} s</span>
                    </div>
                  ))}
                  <div className="timeslip-row text-accent">
                    <span className="font-sans">Quarter mile</span>
                    <span className="font-bold">{Number(run.et_quarter_s).toFixed(3)} s</span>
                  </div>
                  <div className="timeslip-row">
                    <span className="font-sans text-white/70">
                      <Term k="trap">Finish-line speed</Term>
                    </span>
                    <span className="font-semibold">{Number(run.trap_speed_kmh).toFixed(1)} km/h</span>
                  </div>
                </div>

                <div className="mt-5 border-t border-white/10 pt-4 text-sm">
                  <p className="font-medium text-white/80">
                    {changes.length ? 'Changed from stock' : 'Stock bike'}
                  </p>
                  {changes.length > 0 && (
                    <ul className="mt-1.5 list-disc space-y-0.5 pl-5 text-white/65">
                      {changes.map((c) => (
                        <li key={c}>{c}</li>
                      ))}
                    </ul>
                  )}
                  {run.parts_skipped?.length > 0 && (
                    <p className="mt-2 text-white/55">
                      {run.parts_skipped.length === 1 ? 'One part' : `${run.parts_skipped.length} parts`} in
                      this link no longer fit or exist and {run.parts_skipped.length === 1 ? 'was' : 'were'} left
                      off.
                    </p>
                  )}
                </div>
              </article>

              <div className="mt-6 flex flex-wrap gap-3">
                <button type="button" onClick={doShare} className="btn-primary">
                  {copied ? <Check size={15} aria-hidden="true" /> : <Share2 size={15} aria-hidden="true" />}
                  {copied ? 'Link copied' : 'Share this timeslip'}
                </button>
                <button type="button" onClick={() => window.print()} className="btn-ghost">
                  <Printer size={15} aria-hidden="true" />
                  Save as PDF
                </button>
                <Link href={`/simulator?${query}`} className="btn-ghost">
                  Open in the simulator
                </Link>
              </div>

              <div className="card mt-10 px-4 py-3">
                <p className="mb-1.5 text-sm font-medium text-white/80">How this number is made</p>
                <p className="text-sm leading-relaxed text-white/65">
                  This is a simulation, not a stopwatch time. The link holds the bike, the changes
                  and the conditions; this page runs them through the current version of the
                  physics each time it opens, so nobody can type a time in.{' '}
                  <Link href="/validation" className="underline underline-offset-2 hover:text-accent">
                    See how close the simulator is to real timeslips
                  </Link>
                  .
                </p>
              </div>
            </>
          )}
        </div>
      </section>
      {run ? (
        <PrintTimeslip
          bikeName={run.bike_name}
          et={run.et_quarter_s}
          trapKmh={run.trap_speed_kmh}
          splits={splits}
          conditions={[`${Math.round(riderKg)} kg rider`, conditions].filter(Boolean).join(' · ')}
          changes={changes}
        />
      ) : null}
      <div className="print:hidden">
        <SiteFooter />
      </div>
    </main>
  );
}

export default function TimeslipPage() {
  return (
    <Suspense fallback={null}>
      <TimeslipView />
    </Suspense>
  );
}
