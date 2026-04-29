'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ChevronLeft, Gauge, Zap, Wind, CircleDot, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { API_URL } from '../../../lib/api';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';

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
    <div className="flex justify-between items-baseline py-2 border-b border-white/5 last:border-0">
      <span className="text-xs font-mono uppercase tracking-wider text-white/50">{label}</span>
      <span className="text-sm font-mono text-white tabular-nums">{value}</span>
    </div>
  );
}

function SpecBlock({ icon: Icon, title, children }) {
  return (
    <div className="glass rounded-xl border border-white/10 p-5">
      <h3 className="flex items-center gap-2 font-display font-bold text-white text-base mb-3">
        <Icon size={16} className="text-brand-orange" />
        {title}
      </h3>
      <div>{children}</div>
    </div>
  );
}

export default function BikeDetailPage() {
  const params = useParams();
  const bikeId = params?.id;

  const [bike, setBike] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!bikeId) return;
    setLoading(true);
    setError(null);
    fetch(`${API_URL}/api/bikes/${bikeId}`)
      .then(async res => {
        if (!res.ok) {
          const msg = await res.text();
          throw new Error(`API error ${res.status}: ${msg}`);
        }
        return res.json();
      })
      .then(data => setBike(data))
      .catch(e => setError(e.message || 'Failed to load bike'))
      .finally(() => setLoading(false));
  }, [bikeId]);

  return (
    <div className="min-h-screen bg-black text-white">
      <SiteNav />

      <main className="pt-24 pb-16 px-4 sm:px-6">
        <div className="max-w-6xl mx-auto">
          <Link
            href="/bikes"
            className="inline-flex items-center gap-1 text-sm font-mono text-white/60 hover:text-brand-orange transition-colors mb-6"
          >
            <ChevronLeft size={16} /> All bikes
          </Link>

          {loading && (
            <div className="py-24 text-center text-white/50 font-mono text-sm">Loading bike…</div>
          )}

          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-300 text-sm flex items-center gap-2">
              <AlertCircle size={16} /> {error}
            </div>
          )}

          {!loading && !error && bike && (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
            >
              {/* Header */}
              <div className="mb-8 flex flex-col sm:flex-row sm:items-start sm:justify-between gap-6">
                <div>
                  <p className="font-mono text-xs text-brand-orange uppercase tracking-widest mb-2">
                    {bike.manufacturer}
                  </p>
                  <h1 className="font-display font-bold text-3xl sm:text-5xl text-white leading-tight">
                    {bike.model}
                  </h1>
                  <div className="flex flex-wrap gap-2 mt-4">
                    {bike.year && (
                      <span className="px-2 py-1 rounded border border-white/10 bg-white/5 text-xs font-mono text-white/70">
                        {bike.year}
                      </span>
                    )}
                    {bike.category && (
                      <span className="px-2 py-1 rounded border border-brand-orange/30 bg-brand-orange/5 text-xs font-mono text-brand-orange uppercase">
                        {bike.category}
                      </span>
                    )}
                    {bike.data_quality && (
                      <span className="px-2 py-1 rounded border border-brand-accent/30 bg-brand-accent/5 text-xs font-mono text-brand-accent uppercase">
                        Data · {bike.data_quality}
                      </span>
                    )}
                  </div>
                </div>
                {/* Prominent simulate CTA beside the title */}
                <Link
                  href={`/simulator?bike_id=${bike.id}`}
                  className="shrink-0 inline-flex items-center gap-2 px-5 py-3 bg-brand-orange text-black font-display font-bold rounded-xl transition-all hover:shadow-[0_0_30px_rgba(255,94,31,0.4)] text-sm"
                >
                  <Gauge size={16} /> Simulate this bike →
                </Link>
              </div>

              {/* Headline stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                {[
                  { label: 'Displacement', value: formatCell(bike.displacement_cc, 'cc', 0) },
                  { label: 'Peak Power', value: formatCell(bike.peak_power_hp, ' hp', 0), highlight: true },
                  { label: 'Dry Mass', value: formatCell(bike.dry_mass_kg, ' kg', 0) },
                  { label: 'Year', value: formatCell(bike.year) },
                ].map((s, i) => (
                  <div key={i} className="glass rounded-xl border border-white/10 p-5 text-center">
                    <p className="text-[10px] font-mono uppercase tracking-widest text-white/50">
                      {s.label}
                    </p>
                    <p className={`font-display font-bold text-2xl md:text-3xl tabular-nums mt-2 ${
                      s.highlight ? 'text-brand-orange' : 'text-white'
                    }`}>
                      {s.value}
                    </p>
                  </div>
                ))}
              </div>

              {/* Detail blocks */}
              <div className="grid md:grid-cols-2 gap-4 mb-8">
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
              </div>

              {/* Tire fitments */}
              {bike.tire_fitments && bike.tire_fitments.length > 0 && (
                <SpecBlock icon={CircleDot} title={`OEM & Recommended Tires (${bike.tire_fitments.length})`}>
                  <div className="grid gap-2 mt-1">
                    {bike.tire_fitments.map((f, i) => (
                      <div
                        key={i}
                        className="grid grid-cols-[72px_1fr_auto] gap-3 items-baseline py-2 border-b border-white/5 last:border-0"
                      >
                        <span className="text-[10px] font-mono uppercase tracking-wider text-brand-orange">
                          {f.position}
                        </span>
                        <div>
                          <p className="text-sm font-semibold text-white">{f.manufacturer} {f.model}</p>
                          <p className="text-xs font-mono text-white/50">{f.size_designation} · {f.compound_type}</p>
                        </div>
                        <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded border ${
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
              )}

              {/* CTA */}
              <div className="mt-10 flex flex-col sm:flex-row gap-3 justify-center">
                <Link
                  href={`/simulator?bike_id=${bike.id}`}
                  className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-brand-orange text-black font-display font-bold rounded-lg transition-all hover:shadow-[0_0_30px_rgba(255,94,31,0.4)]"
                >
                  <Gauge size={16} /> Simulate this bike
                </Link>
                <Link
                  href="/bikes"
                  className="inline-flex items-center justify-center gap-2 px-6 py-3 border-2 border-white/20 hover:border-brand-orange/60 text-white/80 font-display font-semibold rounded-lg transition-colors"
                >
                  Back to catalog
                </Link>
              </div>
            </motion.div>
          )}
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
