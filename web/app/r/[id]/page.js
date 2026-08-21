'use client';

/**
 * /r/[id] — public shareable timeslip page for one saved sim run.
 *
 * Reads GET /api/runs/{id} (public, immutable). THE showcase of the IGNITION
 * v5 identity: a full-page centered `.timeslip` — perforated edges, timing-
 * assoc masthead with StageDots, giant seven-segment ET in signal orange,
 * dashed split rows with the quarter-mile line highlighted, trap speed —
 * then a WhatsApp-first share button (navigator.share → clipboard fallback)
 * and a "Run your own" CTA. OG metadata comes from the server layout.
 */

import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Share2, Check, AlertCircle, Printer } from 'lucide-react';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StageDots from '../../../components/StageDots';
import ScoreboardDigits from '../../../components/ScoreboardDigits';
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
      { label: '60 FT', value: run.time_60ft_s },
      { label: '330 FT', value: run.time_330ft_s },
      { label: '1/8 MILE', value: run.et_eighth_s },
      { label: '1000 FT', value: run.time_1000ft_s },
    ].filter((s) => s.value != null);
  }, [run]);

  const bikeName = run ? [run.manufacturer, run.model].filter(Boolean).join(' ') : '';
  const shareText = run
    ? `${bikeName} just ran a ${Number(run.et_quarter_s).toFixed(3)}s quarter mile on MotoQuant 🏁`
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
      className="min-h-screen bg-asphalt-0 text-white print:min-h-0 print:bg-white print:text-black"
    >
      {/* screen chrome — hidden when printing so the slip is the whole page */}
      <div className="print:hidden">
        <SiteNav />
      </div>
      <section className="pt-28 md:pt-32 pb-16 md:pb-24 px-6 print:hidden">
        <div className="max-w-md mx-auto">
          {error && (
            <div className="card border-signal-foul/30 px-5 py-4">
              <div className="flex flex-wrap items-center gap-3 text-sm text-signal-foul/90">
                {error === '404' ? (
                  <StageDots foul className="shrink-0" />
                ) : (
                  <AlertCircle size={16} className="shrink-0 text-signal-foul" aria-hidden="true" />
                )}
                <span className="flex-1 min-w-[200px]">
                  {error === '404'
                    ? 'This run does not exist (or was removed).'
                    : `Could not load this run (${error}). The engine may be waking up — a cold start can take up to a minute.`}
                </span>
                {error !== '404' ? (
                  <button
                    type="button"
                    onClick={() => setAttempt((a) => a + 1)}
                    className="btn-ghost btn-sm"
                  >
                    Retry
                  </button>
                ) : (
                  <Link href="/simulator" className="btn-ghost btn-sm">
                    Run your own
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
                {/* masthead — the timing booth's letterhead */}
                <div className="flex items-center justify-between gap-3">
                  <p className="label-mono">Motoquant timing assoc</p>
                  <StageDots animate className="shrink-0" />
                </div>
                <p className="label-mono mt-1 text-white/25">
                  Official timeslip · run #{id || '—'}
                </p>

                <h1 className="mt-5 font-display font-bold text-2xl tracking-tight">
                  {bikeName || 'Motorcycle'}
                  {run.year ? <span className="text-white/40"> · {run.year}</span> : null}
                </h1>
                <p className="label-mono mt-2">
                  {run.venue || 'venue —'}
                  {run.created_at ? ` · ${String(run.created_at).slice(0, 10)}` : ''}
                </p>

                <div className="centerline mt-5" aria-hidden="true" />

                {/* headline ET — the seven-segment timing board, in signal orange */}
                <div className="py-8 text-center">
                  <p className="label-mono mb-3">Quarter-mile ET</p>
                  <div className="flex items-end justify-center gap-2">
                    <ScoreboardDigits
                      value={Number(run.et_quarter_s).toFixed(3)}
                      h={56}
                      label={`${Number(run.et_quarter_s).toFixed(3)} seconds`}
                    />
                    <span className="font-mono text-2xl text-white/40 leading-none">s</span>
                  </div>
                </div>

                {/* split rows — the ruled slip body */}
                <div>
                  {splits.map((s) => (
                    <div key={s.label} className="timeslip-row">
                      <span className="text-white/40 uppercase tracking-[0.15em] text-xs">
                        {s.label}
                      </span>
                      <span className="font-semibold">{Number(s.value).toFixed(3)}s</span>
                    </div>
                  ))}
                  <div className="timeslip-row text-accent">
                    <span className="uppercase tracking-[0.15em] text-xs">1/4 mile</span>
                    <span className="font-bold">{Number(run.et_quarter_s).toFixed(3)}s</span>
                  </div>
                  {run.trap_speed_kmh ? (
                    <div className="timeslip-row">
                      <span className="text-white/40 uppercase tracking-[0.15em] text-xs">
                        Trap speed
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
                    print layout). Ungated by design; candidate Pro gate
                    post-launch. */}
                <button type="button" onClick={() => window.print()} className="btn-ghost">
                  <Printer size={15} aria-hidden="true" />
                  Download PDF
                </button>
                <Link href="/simulator" className="btn-ghost">
                  Run your own
                </Link>
              </div>

              <div className="mt-10 card px-4 py-3">
                <p className="label-mono mb-1.5">How this number is made</p>
                <p className="text-sm text-white/65 leading-relaxed">
                  Simulated by MotoQuant&apos;s RK4 physics engine — 15 coupled sub-models
                  (engine, clutch, tire thermal, aero, weight transfer, wheelie control)
                  integrated at 1&nbsp;ms steps under the venue&apos;s real air density.
                  Validated against 250 published benchmarks.
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
