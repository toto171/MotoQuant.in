'use client';

import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { AnimatePresence } from 'framer-motion';
import { Search, X, Plus, ChevronLeft, ChevronRight, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import SuggestBikeForm from '../../components/SuggestBikeForm';
import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import PageHeader from '../../components/PageHeader';
import { SkeletonCards } from '../../components/Skeleton';
import { API_URL, getBikeCatalog } from '../../lib/api';

const PAGE_SIZE = 40;

// Module-level facet cache: the full-catalog manufacturer/category lists are
// derived ONCE per app lifetime from the shared memoised catalog and survive
// client-side back-navigation without a refetch.
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
  const specs = [
    bike.displacement_cc ? `${Math.round(bike.displacement_cc)} cc` : null,
    bike.peak_power_hp ? `${Math.round(bike.peak_power_hp)} hp` : null,
    bike.dry_mass_kg ? `${Math.round(bike.dry_mass_kg)} kg` : null,
  ].filter(Boolean);
  const name = [bike.manufacturer, bike.model].filter(Boolean).join(' ');
  return (
    <article className="card card-hover flex h-full flex-col p-5" data-bike-id={bike.id ?? ''}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-sm text-white/60 truncate">{bike.manufacturer}</p>
          <h2 className="font-display font-semibold text-white text-lg mt-0.5 line-clamp-2">
            {bike.model}
          </h2>
        </div>
        {bike.year && (
          <span className="font-mono text-xs text-white/55 shrink-0 tabular-nums">{bike.year}</span>
        )}
      </div>
      {specs.length > 0 && (
        <p className="mt-3 font-mono text-sm tabular-nums text-white/75">{specs.join(' · ')}</p>
      )}
      {bike.category && (
        <div className="mt-2">
          <span className="chip">{bike.category}</span>
        </div>
      )}
      <div className="mt-auto flex flex-wrap items-center gap-2 pt-4">
        <Link
          href={`/simulator?bike_id=${bike.id}`}
          className="btn-primary btn-sm"
          aria-label={`Simulate ${name}`}
        >
          Simulate this bike
        </Link>
        <Link
          href={`/bikes/${bike.id}`}
          className="btn-ghost btn-sm"
          aria-label={`Details for ${name}`}
        >
          Details
        </Link>
      </div>
    </article>
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

  // F5: every fetch gets an AbortController plus a request id, so a slow
  // response for an old filter can never overwrite a newer one. Offset resets
  // in the same state update as the filter change (see handlers below).
  const reqId = useRef(0);
  const abortRef = useRef(null);

  const fetchBikes = useCallback(async () => {
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    const id = ++reqId.current;
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (debouncedSearch) params.set('search', debouncedSearch);
      if (manufacturer) params.set('manufacturer', manufacturer);
      if (category) params.set('category', category);
      params.set('limit', String(PAGE_SIZE));
      params.set('offset', String(offset));
      const res = await fetch(`${API_URL}/api/bikes?${params.toString()}`, { signal: ctrl.signal });
      if (!res.ok) throw new Error(`API error ${res.status}`);
      const data = await res.json();
      if (id !== reqId.current) return;
      setBikes(data.bikes || []);
      setTotal(data.total || 0);
      setLoading(false);
    } catch (e) {
      if (e?.name === 'AbortError' || id !== reqId.current) return;
      setError(e.message || 'Failed to load bikes');
      setLoading(false);
    }
  }, [debouncedSearch, manufacturer, category, offset]);

  useEffect(() => {
    fetchBikes();
    return () => abortRef.current?.abort();
  }, [fetchBikes]);

  const onSearch = (v) => { setSearch(v); setOffset(0); };
  const onManufacturer = (v) => { setManufacturer(v); setOffset(0); };
  const onCategory = (v) => { setCategory(v); setOffset(0); };
  const clearFilters = () => { setSearch(''); setManufacturer(''); setCategory(''); setOffset(0); };

  // One full-catalog sweep (shared, memoised getBikeCatalog) to build the REAL
  // filter option lists. Non-fatal on failure: the selects degrade to "Any".
  useEffect(() => {
    if (FACETS_CACHE) return;
    let cancelled = false;
    getBikeCatalog()
      .then((rows) => {
        const uniq = (key) =>
          Array.from(new Set(rows.map((b) => b[key]).filter(Boolean))).sort((a, b) =>
            String(a).localeCompare(String(b))
          );
        FACETS_CACHE = { manufacturers: uniq('manufacturer'), categories: uniq('category') };
        if (!cancelled) setFacets(FACETS_CACHE);
      })
      .catch(() => {
        // best-effort; the grid fetch surfaces real errors.
      });
    return () => { cancelled = true; };
  }, []);

  // If a filter value is set but missing from the facet list, keep it
  // selectable so the UI never lies.
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

      <PageHeader
        title="Bikes"
        lede={
          <>
            541 motorcycles you can simulate. Pick one to see its predicted time. Missing yours?{' '}
            <button
              type="button"
              onClick={() => setSuggestOpen(true)}
              className="text-white underline underline-offset-2 decoration-white/30 hover:text-accent transition-colors"
            >
              Suggest a bike
            </button>
            .
          </>
        }
      />

      <main id="main" className="pb-16 px-4 sm:px-6">
        <div className="max-w-6xl mx-auto">
          {/* Search and filters */}
          <div className="card card-pad mb-6">
            <div className="grid grid-cols-1 md:grid-cols-[1fr_200px_200px_auto] gap-3 items-end">
              <div>
                <label htmlFor="bike-search" className="field-label">Search</label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-white/45 pointer-events-none" size={16} aria-hidden="true" />
                  <input
                    id="bike-search"
                    type="search"
                    value={search}
                    onChange={(e) => onSearch(e.target.value)}
                    placeholder="Make or model, e.g. Duke 390"
                    className="input-base pl-10"
                  />
                </div>
              </div>
              <div>
                <label htmlFor="bike-mfr" className="field-label">Make</label>
                <select
                  id="bike-mfr"
                  value={manufacturer}
                  onChange={(e) => onManufacturer(e.target.value)}
                  className="input-base cursor-pointer"
                >
                  <option value="">Any make</option>
                  {manufacturerOptions.map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor="bike-cat" className="field-label">Type</label>
                <select
                  id="bike-cat"
                  value={category}
                  onChange={(e) => onCategory(e.target.value)}
                  className="input-base cursor-pointer"
                >
                  <option value="">Any type</option>
                  {categoryOptions.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
              {hasFilters && (
                <button type="button" onClick={clearFilters} className="btn-ghost">
                  <X size={14} aria-hidden="true" /> Clear filters
                </button>
              )}
            </div>
            <p className="mt-3 text-sm text-white/60" role="status" aria-live="polite">
              {loading
                ? 'Loading bikes…'
                : `${total.toLocaleString()} ${total === 1 ? 'bike matches' : 'bikes match'} · page ${currentPage} of ${totalPages}`}
            </p>
          </div>

          {loading ? (
            <SkeletonCards count={12} />
          ) : error ? (
            <div className="card p-8 text-center">
              <AlertCircle size={24} className="mx-auto text-signal-foul mb-3" aria-hidden="true" />
              <p className="font-display font-semibold text-white text-lg md:text-xl">
                Couldn&apos;t load the bikes
              </p>
              <p className="text-sm text-white/65 mt-2 max-w-md mx-auto">
                The server may be waking up. Try again in a few seconds.
              </p>
              <p className="font-mono text-xs text-white/55 mt-3 break-all max-w-md mx-auto">{error}</p>
              <div className="mt-6">
                <button type="button" onClick={fetchBikes} className="btn-primary">
                  Try again
                </button>
              </div>
            </div>
          ) : bikes.length === 0 ? (
            <div className="card card-pad py-14 text-center">
              <p className="font-display text-lg font-semibold text-white">No bikes match those filters.</p>
              <p className="mt-2 text-sm text-white/65">Try a shorter search, or add the bike you are looking for.</p>
              <div className="mt-6 flex flex-wrap justify-center gap-3">
                <button type="button" onClick={clearFilters} className="btn-ghost">Clear filters</button>
                <button type="button" onClick={() => setSuggestOpen(true)} className="btn-primary">
                  <Plus size={16} aria-hidden="true" /> Suggest a bike
                </button>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {bikes.map((b) => <BikeCard key={b.id} bike={b} />)}
            </div>
          )}

          {total > PAGE_SIZE && (
            <nav className="flex items-center justify-center gap-3 mt-8" aria-label="Pagination">
              <button
                type="button"
                onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                disabled={offset === 0 || loading}
                className="btn-ghost btn-sm"
              >
                <ChevronLeft size={14} aria-hidden="true" /> Previous
              </button>
              <span className="text-sm text-white/70 tabular-nums">
                {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of {total}
              </span>
              <button
                type="button"
                onClick={() => setOffset(offset + PAGE_SIZE)}
                disabled={offset + PAGE_SIZE >= total || loading}
                className="btn-ghost btn-sm"
              >
                Next <ChevronRight size={14} aria-hidden="true" />
              </button>
            </nav>
          )}
        </div>
      </main>

      <AnimatePresence>
        {suggestOpen && <SuggestBikeForm onClose={() => setSuggestOpen(false)} />}
      </AnimatePresence>

      <SiteFooter />
    </div>
  );
}
