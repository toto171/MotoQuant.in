'use client';

/**
 * BikePredictedTime — the lead card on /bikes/[id] (CLARITY v6).
 *
 * Shows the bike's predicted quarter-mile time as a plain sentence plus the
 * conditions it was computed under, then the primary "Open in simulator"
 * action. The number comes from the in-browser instant estimate (same model
 * as the server surrogate, no network round trip) and falls back to the
 * server's quick simulation when the estimate is unavailable. If neither
 * answers, the sentence is simply omitted — never a placeholder number.
 *
 * Conditions (a stock bike, 75 kg rider, the server's default air) are
 * worded by ConditionsLine — from the server's echoed `environment` block
 * when the server answered, or from what the instant estimate assumes.
 *
 * `initial` ({ et, trap, env, riderKg }) is a stored full-simulation result (the stock
 * leaderboard, passed down by the server page). When given, the card renders
 * it in the server HTML and computes nothing: no skeleton, no network.
 */

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Gauge } from 'lucide-react';
import ResultSentence from '../ResultSentence';
import Term from '../Term';
import { API_URL } from '../../lib/api';
import ConditionsLine from '../ConditionsLine';
import { predictQuick } from '../../lib/surrogate';

const RIDER_KG = 75;

export default function BikePredictedTime({ bike, initial = null }) {
  const stored =
    initial && Number.isFinite(initial.et) ? { ...initial, instant: false, exact: true } : null;
  const [est, setEst] = useState(stored); // {et, trap, instant, exact?, env?}
  const [done, setDone] = useState(!!stored);
  const hasStored = !!stored;

  useEffect(() => {
    if (hasStored) return undefined;
    let cancelled = false;
    const ctrl = new AbortController();
    (async () => {
      let out = null;
      try {
        const r = await predictQuick({ bikeId: bike.id, riderMassKg: RIDER_KG });
        if (r.ok) out = { et: r.etS, trap: r.trapKmh, instant: true };
      } catch {
        /* fall through to the server */
      }
      if (!out) {
        try {
          const res = await fetch(`${API_URL}/api/simulate/quick`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ bike_id: bike.id, rider_mass_kg: RIDER_KG }),
            signal: ctrl.signal,
          });
          if (res.ok) {
            const d = await res.json();
            if (Number.isFinite(d.et_quarter_s)) {
              out = { et: d.et_quarter_s, trap: d.trap_speed_kmh, instant: false, env: d.environment || null };
            }
          }
        } catch {
          /* leave the sentence out */
        }
      }
      if (!cancelled) {
        setEst(out);
        setDone(true);
      }
    })();
    return () => {
      cancelled = true;
      ctrl.abort();
    };
  }, [bike.id, hasStored]);

  const name = [bike.manufacturer, bike.model].filter(Boolean).join(' ');

  return (
    <section className="card card-pad" aria-labelledby="predicted-time-heading">
      <h2 id="predicted-time-heading" className="text-sm font-medium text-white/70">
        {est?.exact ? 'Simulated' : 'Predicted'} <Term k="et">quarter-mile time</Term>
      </h2>
      <div className="mt-2 min-h-[4.5rem]" aria-live="polite">
        {est ? (
          <>
            <p className="font-display text-5xl font-bold tabular-nums text-accent md:text-6xl">
              {est.et.toFixed(est.exact ? 3 : 2)} <span className="text-2xl text-white/70 md:text-3xl">s</span>
            </p>
            <ResultSentence
              className="mt-3"
              bikeName={name}
              riderKg={est.riderKg ?? RIDER_KG}
              et={est.et}
              trapKmh={est.trap}
              exact={!!est.exact}
            />
            <p className="mt-2 text-sm text-white/60">
              {est.instant && (
                <>
                  <Term k="instant_estimate" />.{' '}
                </>
              )}
              <ConditionsLine
                as="span"
                className=""
                env={est.env}
                estimate={est.env || !est.instant ? null : {}}
                unreported={!est.env && !est.instant}
              />{' '}
              Pick your own location in the simulator.
            </p>
          </>
        ) : done ? (
          <p className="text-base text-white/70">
            We couldn&apos;t work out a time for this bike just now. Open it in the simulator to try again.
          </p>
        ) : (
          <div className="space-y-2" aria-hidden="true">
            <div className="skeleton h-12 w-40" />
            <div className="skeleton h-4 w-full max-w-md" />
          </div>
        )}
      </div>
      <div className="mt-4 flex flex-wrap gap-3">
        <Link
          href={`/simulator?bike_id=${bike.id}`}
          className="btn-primary"
          data-cta="bike-detail-top"
          data-bike-id={bike.id ?? ''}
        >
          <Gauge size={16} aria-hidden="true" /> Open in simulator
        </Link>
        <Link href={`/optimize?bike_id=${bike.id}`} className="btn-ghost">
          Find the best parts
        </Link>
      </div>
    </section>
  );
}
