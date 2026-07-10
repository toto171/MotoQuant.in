'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { AnimatePresence } from 'framer-motion';
import { Search, X, Plus, ChevronLeft, ChevronRight, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import SuggestBikeForm from '../../components/SuggestBikeForm';
import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import PageHero from '../../components/PageHero';
import { SkeletonCards } from '../../components/Skeleton';
import { API_URL } from '../../lib/api';
import BikeCardCta from './BikeCardCta';

const PAGE_SIZE = 40;

// Module-level facet cache: the full-catalog manufacturer/category lists are
// fetched ONCE per app lifetime (limit=2000 sweep) and survive client-side
// back-navigation without a refetch (REDESIGN.md §5-B).
let FACETS_CACHE = null;

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
        <div className="card card-hover h-full p-5">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <p className="label-mono truncate">
                {bike.manufacturer}
              </p>
              <h3 className="font-display font-semibold uppercase text-white text-lg leading-[1.05] tracking-[-0.01em] mt-1.5 line-clamp-2 group-hover:text-accent transition-colors">
                {bike.model}
              </h3>
            </div>
            {bike.year && (
              <span className="font-mono text-xs text-white/40 shrink-0 tabular-nums">{bike.year}</span>
            )}
          </div>
          {/* Slip-style ruled figures row — numbers mono, right-aligned */}
          <div className="mt-4 pt-3 border-t border-dashed border-white/10 flex items-baseline justify-end gap-4 font-mono text-sm tabular-nums">
            <span className="text-white/55">{disp}</span>
            <span className="text-white/90">{power}</span>
            <span className="text-white/55">{mass}</span>
          </div>
          {bike.category && (
            <div className="mt-3">
              <span className="chip">{bike.category}</span>
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [suggestOpen, setSuggestOpen] = useState(false);

  // Full-catalog facet lists for the filter dropdowns (module-cached).
  const [facets, setFacets] = useState(FACETS_CACHE);

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

  // One full-catalog sweep to build the REAL filter option lists (the old
  // datalists were derived from the visible 40 rows — misleading). Non-fatal
  // on failure: the selects degrade to "Any" + whatever value is set.
  useEffect(() => {
    if (FACETS_CACHE) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API_URL}/api/bikes?limit=2000`);
        if (!res.ok) return;
        const data = await res.json();
        const rows = data.bikes || [];
        const uniq = (key) =>
          Array.from(new Set(rows.map(b => b[key]).filter(Boolean)))
            .sort((a, b) => String(a).localeCompare(String(b)));
        FACETS_CACHE = {
          manufacturers: uniq('manufacturer'),
          categories: uniq('category'),
        };
        if (!cancelled) setFacets(FACETS_CACHE);
      } catch {
        // Facet fetch is best-effort; the grid fetch surfaces real errors.
      }
    })();
    return () => { cancelled = true; };
  }, []);

  // If a filter value is set but missing from the facet list (deep link,
  // facet fetch failed), keep it selectable so the UI never lies.
  const manufacturerOptions = useMemo(() => {
    const list = facets?.manufacturers || [];
    return manufacturer && !list.includes(manufacturer) ? [manufacturer, ...list] : list;
  }, [facets, manufacturer]);

  const categoryOptions = useMemo(() => {
    const list = facets?.categories || [];
    return category && !list.includes(category) ? [category, ...list] : list;
  }, [facets, category]);

  const hasFilters = !!(search || manufacturer || category);
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="min-h-screen bg-asphalt-0 text-white">
      <SiteNav />

      <PageHero
        kicker="Motorcycle database"
        badge="541 bikes"
        title={<>Every bike. <span className="text-gradient-volt">Real physics.</span></>}
        sub={
          <>
            541 bikes modelled in MotoQuant Pro — Hayabusa, ZX-14R, R15 V4,
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
              className="text-white underline underline-offset-2 decoration-white/30 hover:text-accent transition-colors"
            >
              Suggest a bike
            </button>
            {' '}or{' '}
            <Link
              href="/simulator"
              className="text-white underline underline-offset-2 decoration-white/30 hover:text-accent transition-colors"
            >
              open the quarter-mile calculator
            </Link>.
          </>
        }
        stats={[
          { value: 541, label: 'BIKES' },
          { value: 254, label: 'TIRES' },
          { value: 1860, label: 'FITMENTS' },
        ]}
      >
        <div className="mt-4">
          <button
            onClick={() => setSuggestOpen(true)}
            className="btn-ghost"
          >
            <Plus size={16} /> Suggest a bike
          </button>
        </div>
      </PageHero>

      <main id="main" className="pb-16 px-4 sm:px-6">
        <div className="max-w-6xl mx-auto">
          {/* Filters — sticky below nav */}
          <div className="sticky top-16 z-40 card bg-asphalt-1/90 backdrop-blur-xl p-4 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-[1fr_180px_180px_auto] gap-3 items-end">
              <div>
                <label htmlFor="bike-search" className="label-mono block mb-2">
                  Search
                </label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40 pointer-events-none" size={16} />
                  <input
                    id="bike-search"
                    type="text"
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    placeholder="Search by make or model…"
                    className="input-base pl-10 font-mono"
                  />
                </div>
              </div>
              <div>
                <label htmlFor="bike-mfr" className="label-mono block mb-2">
                  Manufacturer
                </label>
                <select
                  id="bike-mfr"
                  value={manufacturer}
                  onChange={e => setManufacturer(e.target.value)}
                  className="input-base font-mono cursor-pointer"
                >
                  <option value="">Any</option>
                  {manufacturerOptions.map(m => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor="bike-cat" className="label-mono block mb-2">
                  Category
                </label>
                <select
                  id="bike-cat"
                  value={category}
                  onChange={e => setCategory(e.target.value)}
                  className="input-base font-mono cursor-pointer"
                >
                  <option value="">Any</option>
                  {categoryOptions.map(c => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>

              {hasFilters && (
                <button
                  onClick={() => { setSearch(''); setManufacturer(''); setCategory(''); }}
                  className="btn-ghost"
                >
                  <X size={14} /> Clear
                </button>
              )}
            </div>
            <div className="flex items-center justify-between mt-3 label-mono">
              <span>
                {loading ? 'querying catalog…' : `${total.toLocaleString()} bikes match · showing ${bikes.length}`}
              </span>
              <span className="tabular-nums">
                page {currentPage} / {totalPages}
              </span>
            </div>
          </div>

          {/* Grid — skeletons on every fetch, branded error with Retry */}
          {loading ? (
            <SkeletonCards count={12} />
          ) : error ? (
            <div className="card p-8 text-center">
              <AlertCircle size={24} className="mx-auto text-signal-foul mb-3" />
              <p className="font-display font-bold uppercase text-white text-lg">
                Couldn&apos;t load the catalog
              </p>
              <p className="text-sm text-white/65 mt-2 max-w-md mx-auto">
                The engine may be waking up — retry in a moment.
              </p>
              <p className="font-mono text-[11px] text-white/35 mt-3 break-all max-w-md mx-auto">
                {error}
              </p>
              <div className="mt-6">
                <button onClick={fetchBikes} className="btn-primary">
                  Retry
                </button>
              </div>
            </div>
          ) : bikes.length === 0 ? (
            <div className="py-24 text-center label-mono">
              No bikes match those filters.
              <div className="mt-6">
                <button
                  onClick={() => setSuggestOpen(true)}
                  className="btn-ghost normal-case tracking-normal"
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
                className="btn-ghost btn-sm"
              >
                <ChevronLeft size={14} /> Prev
              </button>
              <span className="label-mono tabular-nums">
                {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of {total}
              </span>
              <button
                onClick={() => setOffset(offset + PAGE_SIZE)}
                disabled={offset + PAGE_SIZE >= total || loading}
                className="btn-ghost btn-sm"
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
