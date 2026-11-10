'use client';

/**
 * /r/[id] — public shareable timeslip page for one saved sim run (CLARITY v6).
 *
 * Reads GET /api/runs/{id} (public, immutable). A centered `.timeslip` card:
 * bike and venue, one plain sentence, the big quarter-mile time, ruled split
 * rows, finish-line speed. Then a WhatsApp-first share button
 * (navigator.share, clipboard fallback), Download PDF (print stylesheet,
 * fixed light-on-white in both themes) and "Run your own". OG metadata comes
 * from the server layout.
 */

import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Share2, Check, AlertCircle, Printer } from 'lucide-react';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import ResultSentence from '../../../components/ResultSentence';
import Term from '../../../components/Term';
import PrintTimeslip from '../../../components/PrintTimeslip';
import { Skeleton } from '../../../components/Skeleton';
import { API_URL } from '../../../lib/api';

export default function RunPage() {
  const { id } = useParams();
  const [run, setRun] = useState(null);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [attempt, setAttempt] = useState(0); // bumped by the Retry button

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    setRun(null);
    setError(null);
    fetch(`${API_URL}/api/runs/${id}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((d) => { if (!cancelled) setRun(d); })
      .catch((e) => { if (!cancelled) setError(e.message); });
    return () => { cancelled = true; };
  }, [id, attempt]);

  const splits = useMemo(() => {
    if (!run) return [];
    return [
      { label: 'First 60 ft (launch)', term: 'sixty', value: run.time_60ft_s },
      { label: '330 ft', value: run.time_330ft_s },
      { label: 'Halfway — ⅛ mile', term: 'eighth', value: run.et_eighth_s },
      { label: '1000 ft', value: run.time_1000ft_s },
    ].filter((s) => s.value != null);
  }, [run]);

  const bikeName = run ? [run.manufacturer, run.model].filter(Boolean).join(' ') : '';
  const shareText = run
    ? `${bikeName} ran a simulated ${Number(run.et_quarter_s).toFixed(3)} s quarter mile on MotoQuant`
    : '';

  const doShare = async () => {
    const url = typeof window !== 'undefined' ? window.location.href : '';
    if (navigator.share) {
      try {
        await navigator.share({ title: 'MotoQuant timeslip', text: shareText, url });
        return;
      } catch {
        /* user cancelled — fall through to clipboard */
      }
    }
    try {
      await navigator.clipboard.writeText(`${shareText}\n${url}`);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard unavailable — nothing sensible to do */
    }
  };

  return (
    <main
      id="main"
      className="min-h-screen bg-asphalt-0 text-white print:min-h-0 print:bg-[rgb(255_255_255)] print:text-[rgb(0_0_0)]"
    >
      {/* screen chrome — hidden when printing so the slip is the whole page */}
      <div className="print:hidden">
        <SiteNav />
      </div>
      <section className="pt-28 md:pt-32 pb-16 md:pb-24 px-4 sm:px-6 print:hidden">
        <div className="max-w-md mx-auto">
          {error && (
            <div className="card border-signal-foul/30 px-5 py-4">
              <div className="flex flex-wrap items-center gap-3 text-sm text-signal-foul/90">
                <AlertCircle size={16} className="shrink-0 text-signal-foul" aria-hidden="true" />
                <span className="flex-1 min-w-[200px]">
                  {error === '404'
                    ? 'This run does not exist, or it was removed.'
                    : `Couldn't load this run (${error}). The server may be waking up, which can take up to a minute.`}
                </span>
                {error !== '404' ? (
                  <button
                    type="button"
                    onClick={() => setAttempt((a) => a + 1)}
                    className="btn-ghost btn-sm"
                  >
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

          {!error && !run && (
            <div className="space-y-4" aria-busy="true" aria-label="Loading run">
              <div className="timeslip">
                <div className="flex items-center justify-between mb-4">
                  <Skeleton className="h-3 w-40" />
                  <Skeleton className="h-3 w-10" />
                </div>
                <Skeleton className="h-8 w-2/3 mb-2" />
                <Skeleton className="h-3 w-1/3 mb-6" />
                <div className="flex flex-col items-center gap-3 py-6">
                  <Skeleton className="h-3 w-24" />
                  <Skeleton className="h-14 w-52" />
                </div>
                <div className="space-y-2.5 pt-2">
                  {[...Array(5)].map((_, i) => (
                    <Skeleton key={i} className="h-4 w-full" />
                  ))}
                </div>
              </div>
              <div className="flex flex-wrap gap-3">
                <Skeleton className="h-11 w-44 rounded-lg" />
                <Skeleton className="h-11 w-36 rounded-lg" />
              </div>
            </div>
          )}

          {run && (
            <>
              <article className="timeslip">
                <p className="text-sm font-medium text-white/60">
                  MotoQuant simulated timeslip · run #{id || '—'}
                </p>

                <h1 className="mt-3 font-display font-bold text-2xl tracking-tight">
                  {bikeName || 'Motorcycle'}
                  {run.year ? <span className="text-white/55"> · {run.year}</span> : null}
                </h1>
                <p className="mt-1 text-sm text-white/65">
                  {run.venue ? `Conditions: ${run.venue}` : 'Conditions were not recorded for this run'}
                  {run.created_at ? ` · ${String(run.created_at).slice(0, 10)}` : ''}
                </p>

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
                    bikeName={bikeName || 'Motorcycle'}
                    et={Number(run.et_quarter_s)}
                    trapKmh={run.trap_speed_kmh ? Number(run.trap_speed_kmh) : null}
                    venueName={run.venue || null}
                    build=""
                  />
                </div>

                <div>
                  {splits.map((s) => (
                    <div key={s.label} className="timeslip-row">
                      <span className="font-sans text-white/70">
                        {s.term ? <Term k={s.term}>{s.label}</Term> : s.label}
                      </span>
                      <span className="font-semibold">{Number(s.value).toFixed(3)} s</span>
                    </div>
                  ))}
                  <div className="timeslip-row text-accent">
                    <span className="font-sans">Quarter mile</span>
                    <span className="font-bold">{Number(run.et_quarter_s).toFixed(3)} s</span>
                  </div>
                  {run.trap_speed_kmh ? (
                    <div className="timeslip-row">
                      <span className="font-sans text-white/70">
                        <Term k="trap">Finish-line speed</Term>
                      </span>
                      <span className="font-semibold">
                        {Number(run.trap_speed_kmh).toFixed(1)} km/h
                      </span>
                    </div>
                  ) : null}
                </div>
              </article>

              <div className="mt-6 flex flex-wrap gap-3">
                <button type="button" onClick={doShare} className="btn-primary">
                  {copied ? (
                    <Check size={15} aria-hidden="true" />
                  ) : (
                    <Share2 size={15} aria-hidden="true" />
                  )}
                  {copied ? 'Link copied' : 'Share this timeslip'}
                </button>
                {/* Print-to-PDF export (zero deps — PrintTimeslip supplies the
                    print layout). */}
                <button type="button" onClick={() => window.print()} className="btn-ghost">
                  <Printer size={15} aria-hidden="true" />
                  Download PDF
                </button>
                <Link href="/simulator" className="btn-ghost">
                  Run your own
                </Link>
              </div>

              <div className="mt-10 card px-4 py-3">
                <p className="text-sm font-medium text-white/80 mb-1.5">How this number is made</p>
                <p className="text-sm text-white/65 leading-relaxed">
                  This is a simulation, not a stopwatch time. MotoQuant works out the run
                  from the bike&apos;s engine, gearing, weight and tyres under the air at the
                  venue, and is checked against 250 published benchmarks.{' '}
                  <Link href="/validation" className="underline underline-offset-2 hover:text-accent">
                    See how accurate it is
                  </Link>
                  .
                </p>
              </div>
            </>
          )}
        </div>
      </section>
      {/* print-only face of the page — light-on-white one-page timeslip */}
      {run ? <PrintTimeslip run={run} id={id} /> : null}
      <div className="print:hidden">
        <SiteFooter />
      </div>
    </main>
  );
}
