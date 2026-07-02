'use client';

/**
 * /r/[id] — public shareable timeslip page for one saved sim run.
 *
 * Reads GET /api/runs/{id} (public, immutable). Renders the drag-strip
 * timeslip identity: seven-segment ET, split times, bike + venue, and a
 * "Simulate your own" CTA. WhatsApp-first share button for the Indian
 * market; OG metadata comes from the server layout.
 */

import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Share2, AlertCircle } from 'lucide-react';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import ScoreboardDigits from '../../../components/ScoreboardDigits';
import CodeComment from '../../../components/CodeComment';
import { API_URL } from '../../../lib/api';

function Tile({ label, children }) {
  return (
    <div className="rounded-lg border border-white/8 bg-white/[0.02] px-4 py-3">
      <p className="font-mono text-[10px] tracking-[0.25em] uppercase text-white/40 mb-1.5">
        {label}
      </p>
      {children}
    </div>
  );
}

export default function RunPage() {
  const { id } = useParams();
  const [run, setRun] = useState(null);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!id) return;
    fetch(`${API_URL}/api/runs/${id}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then(setRun)
      .catch((e) => setError(e.message));
  }, [id]);

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
    <main className="min-h-screen bg-black text-white">
      <SiteNav />
      <section className="pt-28 md:pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          <CodeComment>
            {`// timeslip #${id || '—'} · motoquant timing assoc · official accuracy slip`}
          </CodeComment>

          {error && (
            <div className="mt-8 flex items-center gap-2 text-sm text-red-400 border border-red-500/20 bg-red-500/5 rounded-lg px-4 py-3">
              <AlertCircle size={16} aria-hidden="true" />
              {error === '404'
                ? 'This run does not exist (or was removed).'
                : `Could not load this run (${error}). The engine may be waking up — try again in a minute.`}
            </div>
          )}

          {!error && !run && (
            <div className="mt-8 space-y-3" aria-busy="true" aria-label="Loading run">
              <div className="h-24 rounded-lg bg-white/[0.03] animate-pulse" />
              <div className="h-40 rounded-lg bg-white/[0.03] animate-pulse" />
            </div>
          )}

          {run && (
            <>
              <div className="mt-6 border border-white/10 rounded-xl overflow-hidden">
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
                        <p className="font-mono text-[10px] tracking-[0.25em] uppercase text-white/40">
                          {s.label}
                        </p>
                        <p className="font-mono font-bold tabular-nums mt-1">
                          {Number(s.value).toFixed(3)}s
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="mt-6 flex flex-wrap gap-3">
                <button
                  onClick={doShare}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg border border-white/15 text-sm font-medium hover:border-brand-orange/60 transition-colors"
                >
                  <Share2 size={15} aria-hidden="true" />
                  {copied ? 'Link copied' : 'Share this timeslip'}
                </button>
                <Link
                  href="/simulator"
                  className="inline-flex items-center px-5 py-2.5 rounded-lg bg-brand-orange text-black font-display font-bold text-sm hover:bg-brand-orangeLight transition-colors"
                >
                  Simulate your own build
                </Link>
              </div>

              <div className="mt-10">
                <Tile label="How this number is made">
                  <p className="text-sm text-white/60 leading-relaxed">
                    Simulated by MotoQuant&apos;s RK4 physics engine — 15 coupled sub-models
                    (engine, clutch, tire thermal, aero, weight transfer, wheelie control)
                    integrated at 1&nbsp;ms steps under the venue&apos;s real air density.
                    Validated against 216 published benchmarks.
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
