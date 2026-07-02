'use client';

/**
 * /leaderboard — public venue-filterable leaderboard of saved sim runs.
 *
 * Reads GET /api/leaderboard?venue_id=N (venue filter added July 2026) and
 * renders the timing-board aesthetic: seven-segment ETs, trophy on P1.
 * Saved runs come from /api/simulate/save (the account Garage flow), so this
 * page is also the "why save a run?" answer — your run lands here.
 */

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { Trophy, MapPin, AlertCircle } from 'lucide-react';
import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import PageHero from '../../components/PageHero';
import ScoreboardDigits from '../../components/ScoreboardDigits';
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

  useEffect(() => {
    fetch(`${API_URL}/api/venues`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`venues ${r.status}`))))
      .then((d) => setVenues(d.venues || d || []))
      .catch(() => setVenues([]));
  }, []);

  useEffect(() => {
    setRows(null);
    setError(null);
    const q = venueId ? `?venue_id=${venueId}&limit=50` : '?limit=50';
    fetch(`${API_URL}/api/leaderboard${q}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`leaderboard ${r.status}`))))
      .then((d) => setRows(d.leaderboard || []))
      .catch((e) => setError(e.message));
  }, [venueId]);

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
            <label
              htmlFor="venue-filter"
              className="font-mono text-[11px] tracking-[0.25em] uppercase text-white/50"
            >
              Venue
            </label>
            <select
              id="venue-filter"
              value={venueId}
              onChange={(e) => setVenueId(e.target.value)}
              className="bg-ink-2 border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-orange/60"
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
            <div className="flex items-center gap-2 text-sm text-red-400 border border-red-500/20 bg-red-500/5 rounded-lg px-4 py-3">
              <AlertCircle size={16} aria-hidden="true" />
              Could not load the leaderboard ({error}). The engine may be waking up — try again in a minute.
            </div>
          )}

          {!error && rows === null && (
            <div className="space-y-2" aria-busy="true" aria-label="Loading leaderboard">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-14 rounded-lg bg-white/[0.03] animate-pulse" />
              ))}
            </div>
          )}

          {!error && rows !== null && rows.length === 0 && (
            <div className="text-center border border-white/10 rounded-xl py-16 px-6">
              <p className="font-mono text-[11px] tracking-[0.25em] uppercase text-white/40 mb-3">
                {venueName} · no saved runs yet
              </p>
              <p className="text-white/70 mb-6">
                The board is empty — first run takes P1.
              </p>
              <Link
                href="/simulator"
                className="inline-block px-5 py-2.5 rounded-lg bg-brand-orange text-black font-display font-bold text-sm hover:bg-brand-orangeLight transition-colors"
              >
                Run a simulation
              </Link>
            </div>
          )}

          {!error && rows !== null && rows.length > 0 && (
            <ol className="space-y-2">
              {rows.map((r, i) => (
                <li
                  key={r.id}
                  className={`flex items-center gap-4 rounded-lg border px-4 py-3 ${
                    i === 0
                      ? 'border-brand-orange/40 bg-brand-orange/[0.06]'
                      : 'border-white/8 bg-white/[0.02]'
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
