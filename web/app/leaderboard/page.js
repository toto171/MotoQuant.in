'use client';

/**
 * /leaderboard — public venue-filterable leaderboard of saved sim runs.
 *
 * Reads GET /api/leaderboard?venue_id=N (venue filter added July 2026) and
 * renders the timing-board aesthetic: seven-segment ETs, trophy on P1.
 * Saved runs come from /api/simulate/save (the account Garage flow), so this
 * page is also the "why save a run?" answer — your run lands here.
 *
 * Cockpit v3 (July 2026): shared Skeleton loading rows, `.card`/`.card-hover`
 * row surfaces, `.input-base` venue select, and a `.card` error state with a
 * Retry button (brand-red, no raw Tailwind reds).
 */

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { Trophy, MapPin, AlertCircle } from 'lucide-react';
import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import PageHero from '../../components/PageHero';
import ScoreboardDigits from '../../components/ScoreboardDigits';
import { Skeleton } from '../../components/Skeleton';
import { API_URL } from '../../lib/api';

function fmtDate(iso) {
  if (!iso) return '—';
  try {
    return new Date(iso + (iso.endsWith('Z') ? '' : 'Z')).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return iso.slice(0, 10);
  }
}

export default function LeaderboardPage() {
  const [venues, setVenues] = useState([]);
  const [venueId, setVenueId] = useState('');
  const [rows, setRows] = useState(null);
  const [error, setError] = useState(null);
  const [attempt, setAttempt] = useState(0); // bumped by the Retry button

  useEffect(() => {
    fetch(`${API_URL}/api/venues`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`venues ${r.status}`))))
      .then((d) => setVenues(d.venues || d || []))
      .catch(() => setVenues([]));
  }, []);

  useEffect(() => {
    let cancelled = false;
    setRows(null);
    setError(null);
    const q = venueId ? `?venue_id=${venueId}&limit=50` : '?limit=50';
    fetch(`${API_URL}/api/leaderboard${q}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`leaderboard ${r.status}`))))
      .then((d) => { if (!cancelled) setRows(d.leaderboard || []); })
      .catch((e) => { if (!cancelled) setError(e.message); });
    return () => { cancelled = true; };
  }, [venueId, attempt]);

  const venueName = useMemo(() => {
    if (!venueId) return 'All venues';
    const v = venues.find((v) => String(v.id) === String(venueId));
    return v ? v.name : 'Venue';
  }, [venueId, venues]);

  return (
    <main className="min-h-screen bg-black text-white">
      <SiteNav />
      <PageHero
        kicker="// leaderboard: saved runs sorted by ET · venue filter armed"
        badge="Public Leaderboard"
        title={
          <>
            The quickest <span className="text-gradient-orange">saved runs.</span>
          </>
        }
        sub="Every run saved to a MotoQuant garage lands here — ranked by quarter-mile ET, filterable by venue. Sign in, simulate, save, and put your build on the board."
      />

      <section className="px-6 pb-24">
        <div className="max-w-4xl mx-auto">
          {/* venue filter */}
          <div className="flex flex-wrap items-center gap-3 mb-8">
            <MapPin size={16} className="text-brand-orange" aria-hidden="true" />
            <label htmlFor="venue-filter" className="label-mono text-[11px]">
              Venue
            </label>
            <select
              id="venue-filter"
              value={venueId}
              onChange={(e) => setVenueId(e.target.value)}
              className="input-base w-auto min-w-[180px]"
            >
              <option value="">All venues</option>
              {venues.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name}
                </option>
              ))}
            </select>
          </div>

          {error && (
            <div className="card border-brand-red/30 px-5 py-4 flex flex-wrap items-center gap-3 text-sm text-brand-red/90">
              <AlertCircle size={16} className="shrink-0 text-brand-red" aria-hidden="true" />
              <span className="flex-1 min-w-[200px]">
                Could not load the leaderboard ({error}). The engine may be waking
                up — a cold start can take up to a minute.
              </span>
              <button
                type="button"
                onClick={() => setAttempt((a) => a + 1)}
                className="btn-ghost btn-sm"
              >
                Retry
              </button>
            </div>
          )}

          {!error && rows === null && (
            <div className="space-y-2" aria-busy="true" aria-label="Loading leaderboard">
              {[...Array(6)].map((_, i) => (
                <Skeleton key={i} className="h-16 rounded-2xl" />
              ))}
            </div>
          )}

          {!error && rows !== null && rows.length === 0 && (
            <div className="card text-center py-16 px-6">
              <p className="label-mono text-[11px] mb-3">
                {venueName} · no saved runs yet
              </p>
              <p className="text-white/70 mb-6">
                The board is empty — first run takes P1.
              </p>
              <Link href="/simulator" className="btn-primary">
                Run a simulation
              </Link>
            </div>
          )}

          {!error && rows !== null && rows.length > 0 && (
            <ol className="space-y-2">
              {rows.map((r, i) => (
                <li
                  key={r.id}
                  className={`card card-hover flex items-center gap-4 px-4 py-3 ${
                    i === 0 ? 'border-brand-orange/40 bg-brand-orange/[0.06]' : ''
                  }`}
                >
                  <span className="w-8 shrink-0 font-mono text-sm text-white/40 text-right">
                    {i === 0 ? (
                      <Trophy size={16} className="inline text-brand-orange" aria-label="P1" />
                    ) : (
                      `P${i + 1}`
                    )}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">
                      {(r.manufacturer || '—') + ' ' + (r.model || '')}
                      {r.year ? <span className="text-white/40"> · {r.year}</span> : null}
                    </p>
                    <p className="font-mono text-[10px] tracking-[0.2em] uppercase text-white/35">
                      {r.venue || 'venue —'} · {fmtDate(r.created_at)}
                    </p>
                  </div>
                  <div className="shrink-0 text-right">
                    <ScoreboardDigits value={Number(r.et_quarter_s).toFixed(3)} h={22} />
                    <p className="font-mono text-[10px] tracking-[0.2em] text-white/40 mt-1">
                      {r.trap_speed_kmh ? `${Number(r.trap_speed_kmh).toFixed(1)} km/h` : ''}
                    </p>
                  </div>
                </li>
              ))}
            </ol>
          )}
        </div>
      </section>
      <SiteFooter />
    </main>
  );
}
