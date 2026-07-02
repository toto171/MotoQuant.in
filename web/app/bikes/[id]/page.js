'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { ChevronLeft, Gauge, Zap, Wind, CircleDot, AlertCircle, Wrench, SearchX } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { API_URL } from '../../../lib/api';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import CodeComment from '../../../components/CodeComment';
import { Reveal, Stagger, StaggerItem } from '../../../components/Reveal';
import { ScoreboardCounter } from '../../../components/ScoreboardDigits';
import { Skeleton, SkeletonCard } from '../../../components/Skeleton';
import TopCtaVariant from './TopCtaVariant';

function formatCell(value, suffix = '', decimals = null) {
  if (value === null || value === undefined || value === '') return '—';
  if (typeof value === 'number') {
    if (decimals !== null) return `${value.toFixed(decimals)}${suffix}`;
    return `${value}${suffix}`;
  }
  return String(value);
}

function SpecRow({ label, value }) {
  return (
    <div className="flex justify-between items-baseline gap-3 py-2 border-b border-white/5 last:border-0">
      <span className="label-mono">{label}</span>
      <span className="text-sm font-mono text-white tabular-nums text-right">{value}</span>
    </div>
  );
}

function SpecBlock({ icon: Icon, title, children }) {
  return (
    <div className="card relative h-full p-5">
      <div
        aria-hidden="true"
        className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-brand-orange/70 to-transparent"
      />
      <h3 className="flex items-center gap-2 font-display font-bold text-white text-base mb-3">
        <Icon size={16} className="text-brand-orange" />
        {title}
      </h3>
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
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {[0, 1, 2, 3].map(i => (
          <div key={i} className="card p-5 text-center">
            <Skeleton className="h-3 w-20 mx-auto mb-4" />
            <Skeleton className="h-8 w-16 mx-auto" />
          </div>
        ))}
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
    <div className="min-h-screen bg-black text-white">
      <SiteNav />

      <main className="pt-24 pb-16 px-4 sm:px-6">
        <div className="max-w-6xl mx-auto">
          <Link
            href="/bikes"
            className="inline-flex items-center gap-1 font-mono text-[11px] uppercase tracking-[0.2em] text-white/55 hover:text-brand-orange transition-colors mb-6"
          >
            <ChevronLeft size={16} /> All bikes
          </Link>

          {loading && <DetailSkeleton />}

          {!loading && error && (
            notFound ? (
              <div className="card p-8 md:p-12 text-center">
                <SearchX size={28} className="mx-auto text-brand-amber mb-4" />
                <CodeComment center className="mb-3">err 404 · no spec sheet at this id</CodeComment>
                <p className="font-display font-bold text-white text-2xl">
                  This bike isn&apos;t in the catalog
                </p>
                <p className="text-sm text-white/65 mt-3 max-w-md mx-auto">
                  It may have been re-numbered in a catalog update, or it hasn&apos;t
                  been modelled yet. Browse the full catalog or suggest it from there.
                </p>
                <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
                  <Link href="/bikes" className="btn-primary">
                    Browse the catalog
                  </Link>
                  <Link href="/simulator" className="btn-ghost">
                    Open the simulator
                  </Link>
                </div>
              </div>
            ) : (
              <div className="card p-8 md:p-12 text-center">
                <AlertCircle size={28} className="mx-auto text-brand-red mb-4" />
                <p className="font-display font-bold text-white text-2xl">
                  Couldn&apos;t load this bike
                </p>
                <p className="text-sm text-white/65 mt-3 max-w-md mx-auto">
                  The engine may be waking up — retry in a moment.
                </p>
                <div className="mt-8">
                  <button onClick={load} className="btn-primary">
                    Retry
                  </button>
                </div>
              </div>
            )
          )}

          {!loading && !error && bike && (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
            >
              {/* Kicker — engine-log voice */}
              <CodeComment className="mb-4">
                {`specs loaded · ${bike.tire_fitments?.length ?? 0} tire fitments`}
              </CodeComment>

              {/* Header */}
              <div className="mb-8 flex flex-col sm:flex-row sm:items-start sm:justify-between gap-6">
                <div>
                  <p className="font-mono text-[10px] uppercase tracking-[0.25em] text-brand-orange mb-2">
                    {bike.manufacturer}
                  </p>
                  <h1 className="font-display font-bold text-3xl sm:text-5xl text-white leading-tight">
                    {bike.model}
                  </h1>
                  <div className="flex flex-wrap gap-2 mt-4">
                    {bike.year && (
                      <span className="px-2 py-1 rounded border border-white/10 bg-white/5 font-mono text-xs text-white/70 tabular-nums">
                        {bike.year}
                      </span>
                    )}
                    {bike.category && (
                      <span className="px-2 py-1 rounded border border-brand-orange/30 bg-brand-orange/5 font-mono text-xs uppercase tracking-[0.15em] text-brand-orange">
                        {bike.category}
                      </span>
                    )}
                    {bike.data_quality && (
                      <span className="px-2 py-1 rounded border border-brand-accent/30 bg-brand-accent/5 font-mono text-xs uppercase tracking-[0.15em] text-brand-accent">
                        Data · {bike.data_quality}
                      </span>
                    )}
                  </div>
                </div>
                {/* Prominent simulate CTA beside the title — EXP-011 variant-aware */}
                <TopCtaVariant bikeId={bike.id} />
              </div>

              {/* Headline stats — power + displacement on the timing board */}
              <Stagger className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8" stagger={0.07}>
                {[
                  {
                    label: 'Displacement',
                    seg: bike.displacement_cc != null ? Math.round(bike.displacement_cc) : null,
                    unit: 'cc',
                  },
                  {
                    label: 'Peak Power',
                    seg: bike.peak_power_hp != null ? Math.round(bike.peak_power_hp) : null,
                    unit: 'hp',
                  },
                  { label: 'Dry Mass', value: formatCell(bike.dry_mass_kg, ' kg', 0) },
                  { label: 'Year', value: formatCell(bike.year) },
                ].map((s, i) => (
                  <StaggerItem key={i} className="h-full">
                    <div className="card h-full p-5 text-center">
                      <p className="label-mono">
                        {s.label}
                      </p>
                      {'seg' in s ? (
                        s.seg != null ? (
                          <div className="mt-3 flex items-end justify-center gap-1.5">
                            <ScoreboardCounter value={s.seg} h={28} />
                            <span className="label-mono pb-0.5">
                              {s.unit}
                            </span>
                          </div>
                        ) : (
                          <p className="font-display font-bold text-2xl md:text-3xl text-white/40 mt-2">—</p>
                        )
                      ) : (
                        <p className="font-display font-bold text-2xl md:text-3xl tabular-nums text-white mt-2">
                          {s.value}
                        </p>
                      )}
                    </div>
                  </StaggerItem>
                ))}
              </Stagger>

              {/* Detail blocks */}
              <Reveal y={20} className="grid md:grid-cols-2 gap-4 mb-8">
                <SpecBlock icon={Zap} title="Engine">
                  <SpecRow label="Cylinders" value={formatCell(bike.cylinder_count)} />
                  <SpecRow label="Config" value={formatCell(bike.cylinder_config)} />
                  <SpecRow label="Bore" value={formatCell(bike.bore_mm, ' mm', 1)} />
                  <SpecRow label="Stroke" value={formatCell(bike.stroke_mm, ' mm', 1)} />
                  <SpecRow label="Compression" value={formatCell(bike.compression_ratio, ':1', 1)} />
                  <SpecRow label="Peak Torque" value={formatCell(bike.peak_torque_nm, ' Nm', 0)} />
                  <SpecRow label="Peak Power RPM" value={formatCell(bike.peak_power_rpm, ' rpm', 0)} />
                  <SpecRow label="Redline" value={formatCell(bike.redline_rpm, ' rpm', 0)} />
                </SpecBlock>

                <SpecBlock icon={Wind} title="Aero & Chassis">
                  <SpecRow label="Cd" value={formatCell(bike.cd, '', 2)} />
                  <SpecRow label="Frontal Area" value={formatCell(bike.frontal_area_m2, ' m²', 2)} />
                  <SpecRow label="Wheelbase" value={formatCell(bike.wheelbase_m, ' m', 3)} />
                  <SpecRow
                    label="CoG Height"
                    value={
                      bike.cog_height_mm != null
                        ? `${Number(bike.cog_height_mm).toFixed(0)} mm`
                        : formatCell(bike.cog_height_m, ' m', 2)
                    }
                  />
                  <SpecRow
                    label={bike.wet_mass_derived ? 'Wet Mass (est.)' : 'Wet Mass'}
                    value={formatCell(bike.wet_mass_kg, ' kg', 0)}
                  />
                  <SpecRow label="Chain Pitch" value={formatCell(bike.chain_pitch)} />
                  <SpecRow label="Front Sprocket" value={formatCell(bike.front_sprocket)} />
                  <SpecRow label="Rear Sprocket" value={formatCell(bike.rear_sprocket)} />
                </SpecBlock>
              </Reveal>

              {/* Tire fitments */}
              {bike.tire_fitments && bike.tire_fitments.length > 0 && (
                <Reveal y={20}>
                  <SpecBlock icon={CircleDot} title={`OEM & Recommended Tires (${bike.tire_fitments.length})`}>
                    <div className="grid gap-2 mt-1">
                      {bike.tire_fitments.map((f, i) => (
                        <div
                          key={i}
                          className="grid grid-cols-[72px_1fr_auto] gap-3 items-baseline py-2 border-b border-white/5 last:border-0"
                        >
                          <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-brand-orange">
                            {f.position}
                          </span>
                          <div>
                            <p className="text-sm font-semibold text-white">{f.manufacturer} {f.model}</p>
                            <p className="text-xs font-mono text-white/50">{f.size_designation} · {f.compound_type}</p>
                          </div>
                          <span className={`text-[10px] font-mono uppercase tracking-[0.15em] px-2 py-0.5 rounded border ${
                            f.fitment_type === 'oem'
                              ? 'text-brand-accent border-brand-accent/40 bg-brand-accent/5'
                              : 'text-white/60 border-white/20 bg-white/5'
                          }`}>
                            {f.fitment_type}
                          </span>
                        </div>
                      ))}
                    </div>
                  </SpecBlock>
                </Reveal>
              )}

              {/* Bottom CTA — differentiated from the top EXP-011 CTA:
                  primary names the concrete run, ghost routes to the
                  build optimizer instead of repeating "Simulate this bike". */}
              <Reveal y={16}>
                <div className="mt-10 flex flex-col sm:flex-row gap-3 justify-center">
                  <Link
                    href={`/simulator?bike_id=${bike.id}`}
                    className="btn-primary"
                  >
                    <Gauge size={16} /> Run the quarter-mile →
                  </Link>
                  <Link
                    href={`/optimize?bike_id=${bike.id}`}
                    className="btn-ghost"
                  >
                    <Wrench size={16} /> Build &amp; optimize
                  </Link>
                </div>
              </Reveal>
            </motion.div>
          )}
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
