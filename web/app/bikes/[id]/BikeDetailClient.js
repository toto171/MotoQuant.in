'use client';

/**
 * The /bikes/[id] page body. The server page (page.js) passes `stock`, this
 * bike's entry from the committed stock leaderboard, so the name, the heading
 * and the simulated time are in the server HTML even when the backend API is
 * asleep. The full spec sheet (engine, weight and shape, gearing, tyres) is
 * fetched from the API in the browser, as before.
 */

import { useState, useEffect, useCallback } from 'react';
import { ChevronLeft, Zap, Wind, Cog, CircleDot, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import { API_URL } from '../../../lib/api';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import Term from '../../../components/Term';
import { SkeletonCard } from '../../../components/Skeleton';
import TimeslipCTA from '../../../components/TimeslipCTA';
import BikePredictedTime from '../../../components/catalog/BikePredictedTime';

function fmt(value, suffix = '', decimals = null) {
  if (value === null || value === undefined || value === '') return null;
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) return null;
    return `${decimals !== null ? value.toFixed(decimals) : value}${suffix}`;
  }
  return String(value);
}

/** One spec row: label left, value right. Rows with no value are hidden. */
function SpecRow({ label, term, value }) {
  if (value === null || value === undefined || value === '') return null;
  return (
    <div className="stat-row">
      <span>{term ? <Term k={term}>{label}</Term> : label}</span>
      <span>{value}</span>
    </div>
  );
}

function SpecBlock({ icon: Icon, title, children }) {
  return (
    <div className="card h-full p-5">
      <h2 className="flex items-center gap-2 font-display font-semibold text-white text-lg mb-3">
        <Icon size={16} className="text-white/55" aria-hidden="true" />
        {title}
      </h2>
      <div>{children}</div>
    </div>
  );
}

/** Loading skeleton for the two spec cards, so the page doesn't jump when data lands. */
function SpecSkeleton() {
  return (
    <div aria-hidden="true" className="grid md:grid-cols-2 gap-4 mt-4 mb-4">
      <SkeletonCard rows={8} />
      <SkeletonCard rows={8} />
    </div>
  );
}

/**
 * Props (all from the server page):
 *  - stock      : { id, manufacturer, model, year_from, year_to, category,
 *                   displacement_cc, et_s, trap_kmh }
 *  - riderKg    : rider weight the stock time was simulated with
 *  - conditions : the conditions it was simulated in (stock_times.json)
 */
export default function BikeDetailClient({ stock, riderKg, conditions }) {
  const bikeId = stock.id;

  const [bike, setBike] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null); // { status, message }

  const load = useCallback(async () => {
    if (!bikeId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/bikes/${bikeId}`);
      if (!res.ok) {
        let msg = '';
        try { msg = await res.text(); } catch {}
        const err = new Error(msg || `API error ${res.status}`);
        err.status = res.status;
        throw err;
      }
      setBike(await res.json());
    } catch (e) {
      setError({ status: e?.status ?? null, message: e?.message || 'Failed to load bike' });
    } finally {
      setLoading(false);
    }
  }, [bikeId]);

  useEffect(() => {
    load();
  }, [load]);

  const notFound = error?.status === 404;
  const name = [stock.manufacturer, stock.model].filter(Boolean).join(' ');
  const initial = {
    et: stock.et_s,
    trap: stock.trap_kmh,
    riderKg,
    // Same shape as the server's echoed `environment` block, so
    // ConditionsLine words it exactly like a live default-conditions result.
    env: { ...conditions, is_default: true, source: 'default' },
  };

  return (
    <div className="min-h-screen bg-asphalt-0 text-white">
      <SiteNav />

      <main id="main" className="pt-24 pb-16 px-4 sm:px-6">
        <div className="max-w-6xl mx-auto">
          <Link
            href="/bikes"
            className="inline-flex min-h-[44px] items-center gap-1 text-sm font-medium text-white/65 hover:text-white transition-colors mb-2"
          >
            <ChevronLeft size={16} aria-hidden="true" /> All bikes
          </Link>

          <div className="mb-6">
            {/* The maker sits inside the h1 (styled as the small label above
                the model) so the heading names the whole bike. */}
            <h1 className="font-display font-bold text-3xl sm:text-5xl tracking-tight text-white">
              <span className="block font-sans text-sm font-medium tracking-normal text-white/60">
                {stock.manufacturer}
              </span>{' '}
              {stock.model}
            </h1>
            <div className="flex flex-wrap gap-2 mt-3">
              <span className="chip tabular-nums">{stock.year_from}</span>
              <span className="chip">{stock.category.replace(/_/g, ' ')}</span>
              <span className="chip tabular-nums">{Math.round(stock.displacement_cc)} cc</span>
              {bike?.peak_power_hp != null && (
                <span className="chip tabular-nums">{Math.round(bike.peak_power_hp)} hp</span>
              )}
              {bike?.dry_mass_kg != null && (
                <span className="chip tabular-nums">{Math.round(bike.dry_mass_kg)} kg dry</span>
              )}
            </div>
          </div>

          <BikePredictedTime bike={stock} initial={initial} />

          {loading && <SpecSkeleton />}

          {!loading && error && (
            <div className="card p-6 md:p-8 text-center mt-4 mb-4">
              <AlertCircle size={24} className="mx-auto text-signal-stage mb-3" aria-hidden="true" />
              {notFound ? (
                <p className="text-sm text-white/70 max-w-md mx-auto">
                  The full spec sheet for this bike is not available right now. The simulator
                  still has it.
                </p>
              ) : (
                <>
                  <p className="font-display font-semibold text-white text-lg">
                    Couldn&apos;t load the full specs
                  </p>
                  <p className="text-sm text-white/65 mt-2 max-w-md mx-auto">
                    The server may be waking up. Try again in a few seconds.
                  </p>
                  <div className="mt-6">
                    <button type="button" onClick={load} className="btn-ghost">Try again</button>
                  </div>
                </>
              )}
            </div>
          )}

          {!loading && !error && bike && (
            <div>
              <div className="grid md:grid-cols-2 gap-4 mt-4 mb-4">
                <SpecBlock icon={Zap} title="Engine">
                  <SpecRow label="Cylinders" value={fmt(bike.cylinder_count)} />
                  <SpecRow label="Layout" value={fmt(bike.cylinder_config)} />
                  <SpecRow label="Bore" value={fmt(bike.bore_mm, ' mm', 1)} />
                  <SpecRow label="Stroke" value={fmt(bike.stroke_mm, ' mm', 1)} />
                  <SpecRow label="Compression ratio" value={fmt(bike.compression_ratio, ':1', 1)} />
                  <SpecRow label="Peak torque" value={fmt(bike.peak_torque_nm, ' Nm', 0)} />
                  <SpecRow label="Peak power at" value={fmt(bike.peak_power_rpm, ' rpm', 0)} />
                  <SpecRow label="Redline" term="redline" value={fmt(bike.redline_rpm, ' rpm', 0)} />
                </SpecBlock>

                <div className="grid gap-4 content-start">
                  <SpecBlock icon={Wind} title="Weight and shape">
                    <SpecRow label="Air resistance (Cd)" term="cd_a" value={fmt(bike.cd, '', 2)} />
                    <SpecRow label="Frontal area" value={fmt(bike.frontal_area_m2, ' m²', 2)} />
                    <SpecRow label="Wheelbase" value={fmt(bike.wheelbase_m, ' m', 3)} />
                    <SpecRow
                      label="Centre-of-gravity height"
                      value={
                        bike.cog_height_mm != null
                          ? `${Number(bike.cog_height_mm).toFixed(0)} mm`
                          : fmt(bike.cog_height_m, ' m', 2)
                      }
                    />
                    <SpecRow
                      label={bike.wet_mass_derived ? 'Weight with fluids (estimated)' : 'Weight with fluids'}
                      value={fmt(bike.wet_mass_kg, ' kg', 0)}
                    />
                  </SpecBlock>

                  <SpecBlock icon={Cog} title="Gearing">
                    <SpecRow label="Chain size" value={fmt(bike.chain_pitch)} />
                    <SpecRow label="Front sprocket" term="sprockets" value={fmt(bike.front_sprocket)} />
                    <SpecRow label="Rear sprocket" value={fmt(bike.rear_sprocket)} />
                  </SpecBlock>
                </div>
              </div>

              {bike.tire_fitments && bike.tire_fitments.length > 0 && (
                <SpecBlock icon={CircleDot} title={`Tyres that fit (${bike.tire_fitments.length})`}>
                  <div className="grid gap-2 mt-1">
                    {bike.tire_fitments.map((f, i) => (
                      <div
                        key={i}
                        className="grid grid-cols-[64px_1fr_auto] gap-3 items-baseline py-2 border-b border-white/10 last:border-0"
                      >
                        <span className="text-sm text-white/60 capitalize">{f.position}</span>
                        <div>
                          <p className="text-sm font-semibold text-white">{f.manufacturer} {f.model}</p>
                          <p className="text-xs font-mono text-white/60 tabular-nums">
                            {f.size_designation} · {f.compound_type}
                          </p>
                        </div>
                        <span className={`chip ${f.fitment_type === 'oem' ? 'border-white/25 text-white/85' : ''}`}>
                          {f.fitment_type === 'oem' ? 'Factory fit' : f.fitment_type === 'drag_prep' ? 'Drag prep' : f.fitment_type === 'recommended' ? 'Recommended' : f.fitment_type}
                        </span>
                      </div>
                    ))}
                  </div>
                </SpecBlock>
              )}

            </div>
          )}

          <div className="mt-4">
            <TimeslipCTA bikeId={stock.id} bikeName={name} />
          </div>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
