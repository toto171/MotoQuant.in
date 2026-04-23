'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Filter, X, Plus, ChevronLeft, ChevronRight, AlertCircle, Check } from 'lucide-react';
import Link from 'next/link';
import SuggestBikeForm from '../../components/SuggestBikeForm';
import { API_URL } from '../../lib/api';

const PAGE_SIZE = 24;

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
    <Link
      href={`/bikes/${bike.id}`}
      className="block group"
    >
      <motion.div
        whileHover={{ y: -3 }}
        transition={{ duration: 0.2 }}
        className="h-full glass rounded-xl border border-white/10 p-5 hover:border-brand-orange/50 transition-colors"
      >
        <div className="flex items-start justify-between mb-3">
          <div className="min-w-0 flex-1">
            <p className="font-mono text-[10px] text-white/50 uppercase tracking-wider truncate">
              {bike.manufacturer}
            </p>
            <h3 className="font-display font-bold text-white text-lg leading-tight mt-1 line-clamp-2 group-hover:text-brand-orange transition-colors">
              {bike.model}
            </h3>
          </div>
          {bike.year && (
            <span className="font-mono text-xs text-white/50 shrink-0 ml-2">{bike.year}</span>
          )}
        </div>
        <div className="grid grid-cols-3 gap-2 mt-4">
          <div>
            <p className="text-[9px] font-mono uppercase tracking-wider text-white/40">Disp.</p>
            <p className="text-sm font-mono text-white/90 tabular-nums mt-0.5">{disp}</p>
          </div>
          <div>
            <p className="text-[9px] font-mono uppercase tracking-wider text-white/40">Power</p>
            <p className="text-sm font-mono text-brand-orange tabular-nums mt-0.5">{power}</p>
          </div>
          <div>
            <p className="text-[9px] font-mono uppercase tracking-wider text-white/40">Mass</p>
            <p className="text-sm font-mono text-white/90 tabular-nums mt-0.5">{mass}</p>
          </div>
        </div>
        {bike.category && (
          <div className="mt-4 inline-block px-2 py-0.5 rounded border border-brand-orange/30 bg-brand-orange/5 text-[10px] font-mono text-brand-orange uppercase tracking-wide">
            {bike.category}
          </div>
        )}
      </motion.div>
    </Link>
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
    <div className="min-h-screen bg-ink-0 text-white">
      {/* Nav */}
      <nav className="fixed top-0 inset-x-0 h-16 backdrop-blur bg-black/80 border-b border-brand-orange/10 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-full flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="text-xl font-display font-bold tracking-tight">
              <span className="text-gradient-orange">Moto</span>
              <span>Quant</span>
            </div>
            <div className="ml-2 px-2 py-1 rounded text-xs font-mono font-semibold text-brand-accent border border-brand-accent/30 bg-brand-accent/5">
              Pro
            </div>
          </Link>
          <div className="hidden md:flex gap-8 items-center text-sm font-mono">
            <Link href="/simulator" className="text-white/60 hover:text-white transition-colors">Simulator</Link>
            <Link href="/bikes" className="text-brand-orange transition-colors">Bikes</Link>
            <Link href="/#physics" className="text-white/60 hover:text-white transition-colors">Physics</Link>
            <Link href="/#validation" className="text-white/60 hover:text-white transition-colors">Validation</Link>
          </div>
          <Link
            href="/simulator"
            className="px-3 sm:px-4 py-2 bg-brand-orange hover:bg-brand-orangeLight text-black font-semibold rounded-lg text-xs sm:text-sm font-display transition-colors"
          >
            Launch <span className="hidden sm:inline">Simulator</span>
          </Link>
        </div>
      </nav>

      <main className="pt-24 pb-16 px-4 sm:px-6">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="mb-10">
            <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
              <div>
                <h1 className="font-display font-bold text-4xl md:text-5xl text-white">
                  Bikes Catalog
                </h1>
                <p className="text-white/70 mt-3 max-w-2xl">
                  Every bike modelled in MotoQuant Pro — individual aero, dyno curves, and service-manual gear ratios.
                  Missing yours? Let us know.
                </p>
              </div>
              <button
                onClick={() => setSuggestOpen(true)}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg border-2 border-brand-orange text-brand-orange hover:bg-brand-orange hover:text-black font-display font-semibold transition-colors whitespace-nowrap"
              >
                <Plus size={16} /> Suggest a bike
              </button>
            </div>
          </div>

          {/* Filters */}
          <div className="glass rounded-xl border border-white/10 p-4 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-[1fr_180px_180px_auto] gap-3">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40" size={16} />
                <input
                  type="text"
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  placeholder="Search by make or model…"
                  className="w-full pl-10 pr-3 py-2.5 bg-black/40 border border-white/10 rounded-lg text-sm text-white placeholder:text-white/30 focus:border-brand-orange focus:outline-none font-mono"
                />
              </div>
              <input
                type="text"
                value={manufacturer}
                onChange={e => setManufacturer(e.target.value)}
                placeholder="Manufacturer"
                list="mfr-list"
                className="w-full px-3 py-2.5 bg-black/40 border border-white/10 rounded-lg text-sm text-white placeholder:text-white/30 focus:border-brand-orange focus:outline-none font-mono"
              />
              <datalist id="mfr-list">
                {manufacturers.map(m => <option key={m} value={m} />)}
              </datalist>
              <input
                type="text"
                value={category}
                onChange={e => setCategory(e.target.value)}
                placeholder="Category"
                list="cat-list"
                className="w-full px-3 py-2.5 bg-black/40 border border-white/10 rounded-lg text-sm text-white placeholder:text-white/30 focus:border-brand-orange focus:outline-none font-mono"
              />
              <datalist id="cat-list">
                {categories.map(c => <option key={c} value={c} />)}
              </datalist>

              {hasFilters && (
                <button
                  onClick={() => { setSearch(''); setManufacturer(''); setCategory(''); }}
                  className="inline-flex items-center gap-1 px-3 py-2.5 rounded-lg border border-white/10 hover:border-white/30 text-sm text-white/60 hover:text-white transition-colors font-mono"
                >
                  <X size={14} /> Clear
                </button>
              )}
            </div>
            <div className="flex items-center justify-between mt-3 text-xs font-mono text-white/50">
              <span>
                {loading ? 'Loading…' : `${total.toLocaleString()} bikes match · showing ${bikes.length}`}
              </span>
              <span>
                Page {currentPage} / {totalPages}
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
                className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-300 text-sm flex items-center gap-2"
              >
                <AlertCircle size={16} /> {error}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Grid */}
          {!loading && bikes.length === 0 && !error ? (
            <div className="py-24 text-center text-white/50 font-mono text-sm">
              No bikes match those filters.
              <div className="mt-6">
                <button
                  onClick={() => setSuggestOpen(true)}
                  className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg border-2 border-brand-orange text-brand-orange hover:bg-brand-orange hover:text-black font-display font-semibold transition-colors"
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
                className="inline-flex items-center gap-1 px-3 py-2 rounded-lg border border-white/10 hover:border-brand-orange/50 disabled:opacity-30 disabled:cursor-not-allowed text-sm font-mono text-white/80 transition-colors"
              >
                <ChevronLeft size={14} /> Prev
              </button>
              <span className="font-mono text-xs text-white/60 tabular-nums">
                {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of {total}
              </span>
              <button
                onClick={() => setOffset(offset + PAGE_SIZE)}
                disabled={offset + PAGE_SIZE >= total || loading}
                className="inline-flex items-center gap-1 px-3 py-2 rounded-lg border border-white/10 hover:border-brand-orange/50 disabled:opacity-30 disabled:cursor-not-allowed text-sm font-mono text-white/80 transition-colors"
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
    </div>
  );
}
