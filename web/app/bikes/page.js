'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, X, Plus, ChevronLeft, ChevronRight, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import SuggestBikeForm from '../../components/SuggestBikeForm';
import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import PageHero from '../../components/PageHero';
import { API_URL } from '../../lib/api';
import BikeCardCta from './BikeCardCta';

const PAGE_SIZE = 40;

function useDebounce(value, delay = 300) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const h = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(h);
  }, [value, delay]);
  return debounced;
}

function BikeCard({ bike }) {
  const power = bike.peak_power_hp ? `${Math.round(bike.peak_power_hp)} hp` : '—';
  const mass = bike.dry_mass_kg ? `${Math.round(bike.dry_mass_kg)} kg` : '—';
  const disp = bike.displacement_cc ? `${Math.round(bike.displacement_cc)}cc` : '—';
  return (
    // EXP-009: pill is an absolutely-positioned sibling so we don't nest <a>.
    // Control (default) renders nothing — visually identical to pre-EXP markup.
    <div
      className="relative h-full"
      data-exp="EXP-009"
      data-bike-id={bike.id ?? ''}
    >
      <Link
        href={`/bikes/${bike.id}`}
        className="block group h-full"
      >
        <div className="relative h-full rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 hover:border-brand-orange/50 transition-all duration-200 motion-safe:hover:-translate-y-1">
          <div
            aria-hidden="true"
            className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-brand-orange/70 to-transparent"
          />
          <div className="flex items-start justify-between mb-3">
            <div className="min-w-0 flex-1">
              <p className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/45 truncate">
                {bike.manufacturer}
              </p>
              <h3 className="font-display font-bold text-white text-lg leading-tight mt-1 line-clamp-2 group-hover:text-brand-orange transition-colors">
                {bike.model}
              </h3>
            </div>
            {bike.year && (
              <span className="font-mono text-xs text-white/50 shrink-0 ml-2 tabular-nums">{bike.year}</span>
            )}
          </div>
          <div className="grid grid-cols-3 gap-2 mt-4">
            <div>
              <p className="font-mono text-[9px] uppercase tracking-[0.25em] text-white/40">Disp.</p>
              <p className="text-sm font-mono text-white/90 tabular-nums mt-0.5">{disp}</p>
            </div>
            <div>
              <p className="font-mono text-[9px] uppercase tracking-[0.25em] text-white/40">Power</p>
              <p className="text-sm font-mono text-brand-orange tabular-nums mt-0.5">{power}</p>
            </div>
            <div>
              <p className="font-mono text-[9px] uppercase tracking-[0.25em] text-white/40">Mass</p>
              <p className="text-sm font-mono text-white/90 tabular-nums mt-0.5">{mass}</p>
            </div>
          </div>
          {bike.category && (
            <div className="mt-4 inline-block px-2 py-0.5 rounded border border-brand-orange/30 bg-brand-orange/5 font-mono text-[10px] uppercase tracking-[0.2em] text-brand-orange">
              {bike.category}
            </div>
          )}
        </div>
      </Link>
      <div className="absolute bottom-3 right-3 z-10 pointer-events-auto">
        <BikeCardCta bikeId={bike.id} />
      </div>
    </div>
  );
}

export default function BikesPage() {
  const [search, setSearch] = useState('');
  const [manufacturer, setManufacturer] = useState('');
  const [category, setCategory] = useState('');
  const [offset, setOffset] = useState(0);

  const [bikes, setBikes] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [suggestOpen, setSuggestOpen] = useState(false);

  const debouncedSearch = useDebounce(search, 300);

  const fetchBikes = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (debouncedSearch) params.set('search', debouncedSearch);
      if (manufacturer) params.set('manufacturer', manufacturer);
      if (category) params.set('category', category);
      params.set('limit', String(PAGE_SIZE));
      params.set('offset', String(offset));
      const res = await fetch(`${API_URL}/api/bikes?${params.toString()}`);
      if (!res.ok) {
        const msg = await res.text();
        throw new Error(`API error ${res.status}: ${msg}`);
      }
      const data = await res.json();
      setBikes(data.bikes || []);
      setTotal(data.total || 0);
    } catch (e) {
      setError(e.message || 'Failed to load bikes');
    } finally {
      setLoading(false);
    }
  }, [debouncedSearch, manufacturer, category, offset]);

  useEffect(() => {
    fetchBikes();
  }, [fetchBikes]);

  // Reset offset when filters change
  useEffect(() => {
    setOffset(0);
  }, [debouncedSearch, manufacturer, category]);

  const manufacturers = useMemo(() => {
    const set = new Set(bikes.map(b => b.manufacturer).filter(Boolean));
    return Array.from(set).sort();
  }, [bikes]);

  const categories = useMemo(() => {
    const set = new Set(bikes.map(b => b.category).filter(Boolean));
    return Array.from(set).sort();
  }, [bikes]);

  const hasFilters = !!(search || manufacturer || category);
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="min-h-screen bg-black text-white">
      <SiteNav />

      <PageHero
        kicker="catalog loaded [501/501] · search armed"
        badge="Motorcycle Database"
        title={<>Motorcycle Specs &amp; <span className="text-gradient-orange">Quarter-Mile Database</span></>}
        sub={
          <>
            501 bikes modelled in MotoQuant Pro — Hayabusa, ZX-14R, R15 V4,
            Yamaha MT-15 V1, KTM Duke 390, Pulsar NS200, Pulsar 125 Neon,
            Pulsar N250, Apache RTR, Interceptor 650, Yezdi Roadster, Hero
            Glamour 125, CFMoto 800NK, GSX-R600 K8 and the full Indian +
            SE Asia drag-strip catalog. Individual aero (Cd
            &amp; frontal area), dyno curves, service-manual gear ratios,
            and predicted ET at Aamby Valley + 19 other venues.
            Missing yours?{' '}
            <button
              type="button"
              onClick={() => setSuggestOpen(true)}
              className="text-brand-orange hover:underline underline-offset-2"
            >
              Suggest a bike
            </button>
            {' '}or{' '}
            <Link href="/simulator" className="text-brand-orange hover:underline underline-offset-2">
              open the quarter-mile calculator
            </Link>.
          </>
        }
        stats={[
          { value: 501, label: 'BIKES' },
          { value: 232, label: 'TIRES' },
          { value: 1253, label: 'FITMENTS' },
        ]}
      >
        <div className="mt-4">
          <button
            onClick={() => setSuggestOpen(true)}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md border border-brand-orange/40 text-brand-orange hover:bg-brand-orange/10 font-display font-semibold text-sm transition-colors"
          >
            <Plus size={16} /> Suggest a bike
          </button>
        </div>
      </PageHero>

      <main className="pb-16 px-4 sm:px-6">
        <div className="max-w-6xl mx-auto">
          {/* Filters — sticky below nav */}
          <div className="sticky top-16 z-40 rounded-xl border border-white/[0.06] bg-ink-1/90 backdrop-blur-xl p-4 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-[1fr_180px_180px_auto] gap-3 items-end">
              <div>
                <label htmlFor="bike-search" className="block font-mono text-[10px] uppercase tracking-[0.25em] text-white/45 mb-2">
                  Search
                </label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40" size={16} />
                  <input
                    id="bike-search"
                    type="text"
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    placeholder="Search by make or model…"
                    className="w-full pl-10 pr-3 py-2.5 bg-ink-1 border border-white/10 rounded-md text-sm text-white placeholder:text-white/30 focus:border-brand-orange/60 focus:outline-none font-mono"
                  />
                </div>
              </div>
              <div>
                <label htmlFor="bike-mfr" className="block font-mono text-[10px] uppercase tracking-[0.25em] text-white/45 mb-2">
                  Manufacturer
                </label>
                <input
                  id="bike-mfr"
                  type="text"
                  value={manufacturer}
                  onChange={e => setManufacturer(e.target.value)}
                  placeholder="Any"
                  list="mfr-list"
                  className="w-full px-3 py-2.5 bg-ink-1 border border-white/10 rounded-md text-sm text-white placeholder:text-white/30 focus:border-brand-orange/60 focus:outline-none font-mono"
                />
              </div>
              <datalist id="mfr-list">
                {manufacturers.map(m => <option key={m} value={m} />)}
              </datalist>
              <div>
                <label htmlFor="bike-cat" className="block font-mono text-[10px] uppercase tracking-[0.25em] text-white/45 mb-2">
                  Category
                </label>
                <input
                  id="bike-cat"
                  type="text"
                  value={category}
                  onChange={e => setCategory(e.target.value)}
                  placeholder="Any"
                  list="cat-list"
                  className="w-full px-3 py-2.5 bg-ink-1 border border-white/10 rounded-md text-sm text-white placeholder:text-white/30 focus:border-brand-orange/60 focus:outline-none font-mono"
                />
              </div>
              <datalist id="cat-list">
                {categories.map(c => <option key={c} value={c} />)}
              </datalist>

              {hasFilters && (
                <button
                  onClick={() => { setSearch(''); setManufacturer(''); setCategory(''); }}
                  className="inline-flex items-center gap-1 px-3 py-2.5 rounded-md border border-white/10 hover:border-white/30 font-mono text-[10px] uppercase tracking-[0.25em] text-white/60 hover:text-white transition-colors"
                >
                  <X size={14} /> Clear
                </button>
              )}
            </div>
            <div className="flex items-center justify-between mt-3 font-mono text-[10px] uppercase tracking-[0.25em] text-white/45">
              <span>
                {loading ? 'querying catalog…' : `${total.toLocaleString()} bikes match · showing ${bikes.length}`}
              </span>
              <span className="tabular-nums">
                page {currentPage} / {totalPages}
              </span>
            </div>
          </div>

          {/* Error */}
          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="mb-4 p-3 bg-brand-red/10 border border-brand-red/40 rounded-lg text-brand-red/90 text-sm flex items-center gap-2"
              >
                <AlertCircle size={16} /> {error}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Grid */}
          {!loading && bikes.length === 0 && !error ? (
            <div className="py-24 text-center font-mono text-[11px] uppercase tracking-[0.25em] text-white/45">
              No bikes match those filters.
              <div className="mt-6">
                <button
                  onClick={() => setSuggestOpen(true)}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md border border-brand-orange/40 text-brand-orange hover:bg-brand-orange/10 font-display font-semibold text-sm normal-case tracking-normal transition-colors"
                >
                  <Plus size={16} /> Suggest this bike
                </button>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {bikes.map(b => <BikeCard key={b.id} bike={b} />)}
            </div>
          )}

          {/* Pagination */}
          {total > PAGE_SIZE && (
            <div className="flex items-center justify-center gap-3 mt-8">
              <button
                onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                disabled={offset === 0 || loading}
                className="inline-flex items-center gap-1 px-3 py-2 rounded-md border border-white/10 hover:border-brand-orange/50 disabled:opacity-30 disabled:cursor-not-allowed font-mono text-[10px] uppercase tracking-[0.25em] text-white/70 hover:text-white transition-colors"
              >
                <ChevronLeft size={14} /> Prev
              </button>
              <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/45 tabular-nums">
                {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of {total}
              </span>
              <button
                onClick={() => setOffset(offset + PAGE_SIZE)}
                disabled={offset + PAGE_SIZE >= total || loading}
                className="inline-flex items-center gap-1 px-3 py-2 rounded-md border border-white/10 hover:border-brand-orange/50 disabled:opacity-30 disabled:cursor-not-allowed font-mono text-[10px] uppercase tracking-[0.25em] text-white/70 hover:text-white transition-colors"
              >
                Next <ChevronRight size={14} />
              </button>
            </div>
          )}
        </div>
      </main>

      {/* Suggest modal */}
      <AnimatePresence>
        {suggestOpen && (
          <SuggestBikeForm onClose={() => setSuggestOpen(false)} />
        )}
      </AnimatePresence>

      <SiteFooter />
    </div>
  );
}
