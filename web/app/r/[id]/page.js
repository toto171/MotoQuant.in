'use client';

/**
 * /r/[id] — public shareable timeslip page for one saved sim run.
 *
 * Reads GET /api/runs/{id} (public, immutable). Renders the drag-strip
 * timeslip identity: seven-segment ET, split times, bike + venue, and a
 * "Simulate your own" CTA. WhatsApp-first share button for the Indian
 * market; OG metadata comes from the server layout.
 *
 * Cockpit v3 (July 2026): shared Skeleton loading state shaped like the
 * timeslip, `.card` surfaces, `.btn-primary` share button with the
 * copied-state flip, and a `.card` error state with Retry (brand-red).
 */

import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Share2, Check, AlertCircle } from 'lucide-react';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import ScoreboardDigits from '../../../components/ScoreboardDigits';
import CodeComment from '../../../components/CodeComment';
import { Skeleton } from '../../../components/Skeleton';
import { API_URL } from '../../../lib/api';

function Tile({ label, children }) {
  return (
    <div className="card px-4 py-3">
      <p className="label-mono mb-1.5">{label}</p>
      {children}
    </div>
  );
}

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
    <main id="main" className="min-h-screen bg-black text-white">
      <SiteNav />
      <section className="pt-28 md:pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          <CodeComment>
            {`// timeslip #${id || '—'} · motoquant timing assoc · official accuracy slip`}
          </CodeComment>

          {error && (
            <div className="mt-8 card border-brand-red/30 px-5 py-4 flex flex-wrap items-center gap-3 text-sm text-brand-red/90">
              <AlertCircle size={16} className="shrink-0 text-brand-red" aria-hidden="true" />
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
          )}

          {!error && !run && (
            <div className="mt-6 space-y-4" aria-busy="true" aria-label="Loading run">
              <div className="card overflow-hidden">
                <div className="px-6 py-4 border-b border-dashed border-white/15">
                  <Skeleton className="h-7 w-2/3 mb-2" />
                  <Skeleton className="h-3 w-1/3" />
                </div>
                <div className="px-6 py-8 flex flex-col items-center gap-3">
                  <Skeleton className="h-3 w-32" />
                  <Skeleton className="h-14 w-52" />
                  <Skeleton className="h-4 w-28" />
                </div>
              </div>
              <div className="flex flex-wrap gap-3">
                <Skeleton className="h-11 w-44 rounded-xl" />
                <Skeleton className="h-11 w-52 rounded-xl" />
              </div>
            </div>
          )}

          {run && (
            <>
              <div className="mt-6 card overflow-hidden">
                {/* masthead */}
                <div className="border-b border-dashed border-white/15 px-6 py-4">
                  <h1 className="font-display font-bold text-2xl md:text-3xl">
                    {bikeName || 'Motorcycle'}
                    {run.year ? <span className="text-white/40"> · {run.year}</span> : null}
                  </h1>
                  <p className="font-mono text-[11px] tracking-[0.2em] uppercase text-white/40 mt-1">
                    {run.venue || 'venue —'}
                    {run.created_at ? ` · ${String(run.created_at).slice(0, 10)}` : ''}
                  </p>
                </div>
                {/* headline ET */}
                <div className="px-6 py-8 text-center">
                  <p className="font-mono text-[11px] tracking-[0.3em] uppercase text-white/40 mb-3">
                    Quarter-mile ET
                  </p>
                  <div className="flex justify-center">
                    <ScoreboardDigits
                      value={Number(run.et_quarter_s).toFixed(3)}
                      h={56}
                    />
                  </div>
                  {run.trap_speed_kmh ? (
                    <p className="font-mono text-sm text-white/60 mt-4">
                      trap {Number(run.trap_speed_kmh).toFixed(1)} km/h
                    </p>
                  ) : null}
                </div>
                {/* splits */}
                {splits.length > 0 && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-white/5 border-t border-white/10">
                    {splits.map((s) => (
                      <div key={s.label} className="bg-black px-4 py-3 text-center">
                        <p className="label-mono">{s.label}</p>
                        <p className="font-mono font-bold tabular-nums mt-1">
                          {Number(s.value).toFixed(3)}s
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="mt-6 flex flex-wrap gap-3">
                <button type="button" onClick={doShare} className="btn-primary">
                  {copied ? (
                    <Check size={15} aria-hidden="true" />
                  ) : (
                    <Share2 size={15} aria-hidden="true" />
                  )}
                  {copied ? 'Link copied' : 'Share this timeslip'}
                </button>
                <Link href="/simulator" className="btn-ghost">
                  Simulate your own build
                </Link>
              </div>

              <div className="mt-10">
                <Tile label="How this number is made">
                  <p className="text-sm text-white/60 leading-relaxed">
                    Simulated by MotoQuant&apos;s RK4 physics engine — 15 coupled sub-models
                    (engine, clutch, tire thermal, aero, weight transfer, wheelie control)
                    integrated at 1&nbsp;ms steps under the venue&apos;s real air density.
                    Validated against 223 published benchmarks.
                  </p>
                </Tile>
              </div>
            </>
          )}
        </div>
      </section>
      <SiteFooter />
    </main>
  );
}
