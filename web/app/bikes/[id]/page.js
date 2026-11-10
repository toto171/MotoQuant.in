'use client';

import { useState, useEffect, useCallback } from 'react';
import { ChevronLeft, Zap, Wind, Cog, CircleDot, AlertCircle, SearchX } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { API_URL } from '../../../lib/api';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import Term from '../../../components/Term';
import { Skeleton, SkeletonCard } from '../../../components/Skeleton';
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

/**
 * Loading skeleton shaped like the final layout — header block, four stat
 * tiles, and the two spec cards — so the page doesn't jump when data lands.
 */
function DetailSkeleton() {
  return (
    <div aria-hidden="true">
      {/* kicker line */}
      <Skeleton className="h-3 w-56 mb-6" />

      {/* header block: manufacturer label + title + chips, CTA at right */}
      <div className="mb-8 flex flex-col sm:flex-row sm:items-start sm:justify-between gap-6">
        <div className="flex-1 min-w-0">
          <Skeleton className="h-3 w-28 mb-3" />
          <Skeleton className="h-10 w-72 max-w-full mb-4" />
          <div className="flex flex-wrap gap-2">
            <Skeleton className="h-7 w-16" />
            <Skeleton className="h-7 w-20" />
            <Skeleton className="h-7 w-24" />
          </div>
        </div>
        <Skeleton className="h-12 w-52 shrink-0" />
      </div>

      {/* four headline stat tiles */}
      <div className="card card-pad mb-4">
        <Skeleton className="h-4 w-48 mb-4" />
        <Skeleton className="h-14 w-40" />
      </div>

      {/* two spec cards */}
      <div className="grid md:grid-cols-2 gap-4">
        <SkeletonCard rows={8} />
        <SkeletonCard rows={8} />
      </div>
    </div>
  );
}

export default function BikeDetailPage() {
  const params = useParams();
  const bikeId = params?.id;

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

          {loading && <DetailSkeleton />}

          {!loading && error && (
            notFound ? (
              <div className="card p-8 md:p-12 text-center">
                <SearchX size={28} className="mx-auto text-signal-stage mb-4" aria-hidden="true" />
                <p className="font-display font-semibold text-white text-xl md:text-2xl">
                  This bike isn&apos;t in the catalog
                </p>
                <p className="text-sm text-white/65 mt-3 max-w-md mx-auto">
                  It may have been renumbered in a catalog update, or it hasn&apos;t
                  been added yet. Browse all bikes, or suggest it from there.
                </p>
                <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
                  <Link href="/bikes" className="btn-primary">Browse all bikes</Link>
                  <Link href="/simulator" className="btn-ghost">Open the simulator</Link>
                </div>
              </div>
            ) : (
              <div className="card p-8 md:p-12 text-center">
                <AlertCircle size={28} className="mx-auto text-signal-foul mb-4" aria-hidden="true" />
                <p className="font-display font-semibold text-white text-xl md:text-2xl">
                  Couldn&apos;t load this bike
                </p>
                <p className="text-sm text-white/65 mt-3 max-w-md mx-auto">
                  The server may be waking up. Try again in a few seconds.
                </p>
                <div className="mt-8">
                  <button type="button" onClick={load} className="btn-primary">Try again</button>
                </div>
              </div>
            )
          )}

          {!loading && !error && bike && (
            <div>
              <div className="mb-6">
                <p className="text-sm font-medium text-white/60">{bike.manufacturer}</p>
                <h1 className="font-display font-bold text-3xl sm:text-5xl tracking-tight text-white">
                  {bike.model}
                </h1>
                <div className="flex flex-wrap gap-2 mt-3">
                  {bike.year && <span className="chip tabular-nums">{bike.year}</span>}
                  {bike.category && <span className="chip">{bike.category}</span>}
                  {bike.displacement_cc != null && (
                    <span className="chip tabular-nums">{Math.round(bike.displacement_cc)} cc</span>
                  )}
                  {bike.peak_power_hp != null && (
                    <span className="chip tabular-nums">{Math.round(bike.peak_power_hp)} hp</span>
                  )}
                  {bike.dry_mass_kg != null && (
                    <span className="chip tabular-nums">{Math.round(bike.dry_mass_kg)} kg dry</span>
                  )}
                </div>
              </div>

              <BikePredictedTime bike={bike} />

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

              <div className="mt-4">
                <TimeslipCTA bikeId={bike.id} />
              </div>
            </div>
          )}
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
