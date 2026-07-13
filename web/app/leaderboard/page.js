'use client';

/**
 * /leaderboard — public venue-filterable leaderboard of saved sim runs.
 *
 * Reads GET /api/leaderboard?venue_id=N (venue filter added July 2026) and
 * renders "THE BOARD": timeslip-strip rows ranked by quarter-mile ET, each
 * linking to its public /r/[id] slip. Saved runs come from /api/simulate/save
 * (the account Garage flow), so this page is also the "why save a run?"
 * answer — your run lands here.
 *
 * STAGED v4 (July 2026): PageHero, `.card` strip rows (rank mono / bike name
 * condensed uppercase / venue `.chip` / big mono ET), `.input-base` venue
 * select, shared Skeleton rows, signal-foul error card with Retry. House
 * reference sims hold an empty board (honestly chipped "HOUSE REFERENCE");
 * the first real saved run replaces them.
 */

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { MapPin, AlertCircle } from 'lucide-react';
import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import PageHero from '../../components/PageHero';
import { Skeleton } from '../../components/Skeleton';
import { API_URL } from '../../lib/api';

// House reference runs — shown ONLY when the board has no saved runs yet, so
// a first visitor never sees a dead room. These are the three pinned
// reference-bike baselines (the same numbers in the footer strip), honestly
// labeled as the house's own sims. The first real saved run replaces them.
const HOUSE_RUNS = [
  { key: 'k5', bike: 'Suzuki GSX-R 1000 K5', year: 2005, et: '10.033', trap: '239.8 km/h' },
  { key: 'r1', bike: 'Yamaha YZF-R1 4C8', year: 2007, et: '10.286', trap: '236.1 km/h' },
  { key: 'busa', bike: 'Suzuki Hayabusa Gen1', year: 1999, et: '10.471', trap: '243.0 km/h' },
];

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

function Rank({ pos }) {
  return (
    <span
      className={`w-8 shrink-0 text-right font-mono tabular-nums text-sm ${
        pos === 1 ? 'font-bold text-accent' : 'text-white/40'
      }`}
      aria-label={`Position ${pos}`}
    >
      {String(pos).padStart(2, '0')}
    </span>
  );
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
    <main id="main" className="min-h-screen bg-asphalt-0 text-white">
      <SiteNav />
      <PageHero
        kicker="Public leaderboard"
        badge="Saved runs · ranked by ET"
        title={<>The board.</>}
        sub="Every run saved to a MotoQuant garage lands here — ranked by quarter-mile ET, filterable by venue. Sign in, simulate, save, and put your build on the board."
      />

      <section className="px-6 pb-16 md:pb-24">
        <div className="max-w-4xl mx-auto">
          {/* venue filter */}
          <div className="flex flex-wrap items-center gap-3 mb-8">
            <MapPin size={16} className="text-white/40" aria-hidden="true" />
            <label htmlFor="venue-filter" className="label-mono">
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
            <div className="card border-signal-foul/30 px-5 py-4 flex flex-wrap items-center gap-3 text-sm text-signal-foul/90">
              <AlertCircle size={16} className="shrink-0 text-signal-foul" aria-hidden="true" />
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
                <Skeleton key={i} className="h-16 rounded-xl" />
              ))}
            </div>
          )}

          {!error && rows !== null && rows.length === 0 && (
            <div>
              <p className="label-mono mb-3">
                {venueName} · no saved runs yet — house reference sims hold the board
              </p>
              <ol className="space-y-2" aria-label="House reference runs">
                {HOUSE_RUNS.map((r, i) => (
                  <li
                    key={r.key}
                    className="card flex items-center gap-3 md:gap-4 px-4 py-3"
                  >
                    <Rank pos={i + 1} />
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-display font-semibold uppercase text-base md:text-lg leading-tight">
                        {r.bike}
                        <span className="text-white/40"> · {r.year}</span>
                      </p>
                      <div className="mt-1.5 flex flex-wrap items-center gap-2">
                        <span className="chip">House reference</span>
                        <span className="label-mono">Aamby Valley · stock sim</span>
                      </div>
                    </div>
                    <div className="shrink-0 text-right">
                      <p className="font-mono font-bold tabular-nums text-xl md:text-2xl leading-none">
                        {r.et}
                      </p>
                      <p className="label-mono mt-1.5">{r.trap}</p>
                    </div>
                  </li>
                ))}
              </ol>
              <div className="card mt-4 text-center py-10 px-6">
                <p className="text-white/65 mb-5">
                  Take P1 from the house — run a sim and save it to the board.
                </p>
                <Link href="/simulator" className="btn-primary">
                  Run a simulation
                </Link>
              </div>
            </div>
          )}

          {!error && rows !== null && rows.length > 0 && (
            <ol className="space-y-2">
              {rows.map((r, i) => (
                <li key={r.id}>
                  {/* Whole row links to the run's public timeslip — the share
                      loop starts here, not just from the save flow. */}
                  <Link
                    href={`/r/${r.id}`}
                    className={`card card-hover flex items-center gap-3 md:gap-4 px-4 py-3 ${
                      i === 0 ? 'border-accent/30' : ''
                    }`}
                  >
                    <Rank pos={i + 1} />
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-display font-semibold uppercase text-base md:text-lg leading-tight">
                        {(r.manufacturer || '—') + ' ' + (r.model || '')}
                        {r.year ? <span className="text-white/40"> · {r.year}</span> : null}
                      </p>
                      <div className="mt-1.5 flex flex-wrap items-center gap-2">
                        <span className="chip max-w-[180px] truncate">{r.venue || 'venue —'}</span>
                        <span className="label-mono">{fmtDate(r.created_at)} · view slip →</span>
                      </div>
                    </div>
                    <div className="shrink-0 text-right">
                      <p className="font-mono font-bold tabular-nums text-xl md:text-2xl leading-none">
                        {Number(r.et_quarter_s).toFixed(3)}
                      </p>
                      <p className="label-mono mt-1.5">
                        {r.trap_speed_kmh ? `${Number(r.trap_speed_kmh).toFixed(1)} km/h` : ''}
                      </p>
                    </div>
                  </Link>
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
