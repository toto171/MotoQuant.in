'use client';

/**
 * StockBoard — the filterable table on /leaderboard.
 *
 * Receives every bike's simulated stock time (already sorted fastest first)
 * and filters it in the browser by name, type and engine size. Rank is the
 * bike's position on the whole board, so filtering never renumbers it.
 */

import { useMemo, useState } from 'react';
import Link from 'next/link';
import { Search } from 'lucide-react';

const TYPES = [
  ['', 'All types'],
  ['sport', 'Sport'],
  ['naked', 'Naked'],
  ['adventure', 'Adventure'],
  ['cruiser', 'Cruiser'],
  ['touring', 'Touring'],
  ['other', 'Other'],
];
const MAIN_TYPES = new Set(['sport', 'naked', 'adventure', 'cruiser', 'touring']);

const SIZES = [
  ['', 'Any engine size', 0, Infinity],
  ['s', 'Up to 200 cc', 0, 200],
  ['m', '201 to 400 cc', 200.0001, 400],
  ['l', '401 to 700 cc', 400.0001, 700],
  ['xl', '701 to 1000 cc', 700.0001, 1000],
  ['xxl', 'Over 1000 cc', 1000.0001, Infinity],
];

const PAGE = 50;

export default function StockBoard({ bikes }) {
  const [query, setQuery] = useState('');
  const [type, setType] = useState('');
  const [size, setSize] = useState('');
  const [shown, setShown] = useState(PAGE);

  const ranked = useMemo(() => bikes.map((b, i) => ({ ...b, rank: i + 1 })), [bikes]);
  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    const band = SIZES.find(([k]) => k === size);
    return ranked.filter((b) => {
      if (q && !`${b.manufacturer} ${b.model}`.toLowerCase().includes(q)) return false;
      if (type === 'other' ? MAIN_TYPES.has(b.category) : type && b.category !== type) return false;
      if (band && band[0]) {
        const cc = Number(b.displacement_cc);
        if (!(cc >= band[2] && cc <= band[3])) return false;
      }
      return true;
    });
  }, [ranked, query, type, size]);

  const reset = () => setShown(PAGE);

  return (
    <div>
      <div className="mb-5 grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto_auto]">
        <label className="relative block">
          <span className="sr-only">Search bikes</span>
          <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-white/45" aria-hidden="true" />
          <input
            type="search"
            value={query}
            onChange={(e) => { setQuery(e.target.value); reset(); }}
            placeholder="Search by make or model"
            className="input-base h-11 pl-9 pr-3"
          />
        </label>
        <label className="block">
          <span className="sr-only">Type of bike</span>
          <select value={type} onChange={(e) => { setType(e.target.value); reset(); }} className="input-base h-11">
            {TYPES.map(([v, label]) => (
              <option key={v} value={v}>{label}</option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="sr-only">Engine size</span>
          <select value={size} onChange={(e) => { setSize(e.target.value); reset(); }} className="input-base h-11">
            {SIZES.map(([v, label]) => (
              <option key={v} value={v}>{label}</option>
            ))}
          </select>
        </label>
      </div>

      <p className="mb-3 text-sm text-white/55" aria-live="polite">
        {rows.length === bikes.length
          ? `${bikes.length} bikes`
          : `${rows.length} of ${bikes.length} bikes`}
      </p>

      {rows.length === 0 ? (
        <div className="card card-pad text-center text-white/70">No bike matches those filters.</div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-white/10 text-xs text-white/55">
              <tr>
                <th scope="col" className="w-12 px-3 py-3 text-right font-medium">#</th>
                <th scope="col" className="px-3 py-3 font-medium">Bike</th>
                <th scope="col" className="hidden px-3 py-3 font-medium sm:table-cell">Engine</th>
                <th scope="col" className="px-3 py-3 text-right font-medium">Quarter mile</th>
                <th scope="col" className="hidden px-3 py-3 text-right font-medium md:table-cell">Finish speed</th>
                <th scope="col" className="px-3 py-3"><span className="sr-only">Simulate</span></th>
              </tr>
            </thead>
            <tbody>
              {rows.slice(0, shown).map((b) => (
                <tr key={b.id} className="border-b border-white/[0.06] last:border-0">
                  <td className={`px-3 py-3 text-right font-mono tabular-nums ${b.rank === 1 ? 'font-bold text-accent' : 'text-white/55'}`}>
                    {b.rank}
                  </td>
                  <td className="px-3 py-3">
                    <Link href={`/bikes/${b.id}`} className="font-medium text-white hover:text-accent">
                      {b.manufacturer} {b.model}
                    </Link>
                  </td>
                  <td className="hidden px-3 py-3 text-white/60 sm:table-cell">
                    {b.displacement_cc ? `${Math.round(b.displacement_cc)} cc` : '–'}
                    <span className="text-white/40"> · {String(b.category || '').replace(/_/g, ' ')}</span>
                  </td>
                  <td className="px-3 py-3 text-right font-mono font-semibold tabular-nums text-white">
                    {b.et_s.toFixed(3)} s
                  </td>
                  <td className="hidden px-3 py-3 text-right font-mono tabular-nums text-white/65 md:table-cell">
                    {b.trap_kmh.toFixed(1)} km/h
                  </td>
                  <td className="px-3 py-3 text-right">
                    <Link
                      href={`/simulator?bike=${b.id}`}
                      className="whitespace-nowrap text-accent underline-offset-2 hover:underline"
                      aria-label={`Simulate the ${b.manufacturer} ${b.model}`}
                    >
                      Simulate
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {rows.length > shown && (
        <div className="mt-5 text-center">
          <button type="button" onClick={() => setShown((n) => n + PAGE * 2)} className="btn-ghost">
            Show more ({rows.length - shown} left)
          </button>
        </div>
      )}
    </div>
  );
}
