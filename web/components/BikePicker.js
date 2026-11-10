'use client';

/**
 * BikePicker — the ONE bike-selection control (CLARITY v6).
 *
 * A button that shows the chosen bike and opens a search box with a list of
 * matches. Accessible combobox/listbox:
 *   - visible <label> wired to the trigger (htmlFor / id)
 *   - trigger: aria-haspopup="listbox", aria-expanded, aria-controls
 *   - search input: role="combobox", aria-expanded, aria-controls,
 *     aria-autocomplete="list", aria-activedescendant -> highlighted option
 *   - ArrowDown/ArrowUp move, Home/End jump, Enter selects, Escape closes and
 *     returns focus to the trigger; ArrowDown on the trigger opens the list
 *   - debounced /api/bikes?search= (220 ms), skeleton rows while loading
 *   - optional `popular` quick chips (one-tap starts, >= 44 px tall)
 *
 * Props (backward compatible — only optional props were added)
 *  - value       : selected bike object | null ({id, manufacturer, model, …})
 *  - onSelect    : (bike) => void
 *  - label       : field label (default 'Bike')
 *  - popular     : optional boolean — show the shared popular-bike chips
 *                  (lib/popularBikes.js); a chip selects that family's newest
 *                  generation and is not rendered if the catalogue lacks it
 *  - placeholder : optional search-box placeholder
 *  - hint        : optional helper line shown under the control
 */

import { useEffect, useId, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { ChevronDown, Search } from 'lucide-react';
import { API_URL, getBikeCatalog } from '@/lib/api';
import { popularChips } from '@/lib/popularBikes';

const DEFAULT_PLACEHOLDER = 'Search bikes, e.g. Duke 390';

export default function BikePicker({
  value,
  onSelect,
  label = 'Bike',
  popular = null,
  placeholder = DEFAULT_PLACEHOLDER,
  hint = null,
}) {
  const uid = useId().replace(/:/g, '');
  const triggerId = `bike-trigger-${uid}`;
  const listId = `bike-list-${uid}`;
  const optId = (i) => `bike-opt-${uid}-${i}`;

  const [open, setOpen] = useState(false);
  const [q, setQ] = useState('');
  const [bikes, setBikes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);
  const [hi, setHi] = useState(-1); // highlighted option index
  const ref = useRef(null);
  const triggerRef = useRef(null);
  const debounceRef = useRef(null);
  const listRef = useRef(null);

  useEffect(() => {
    const h = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, []);

  useEffect(() => {
    if (!open) return undefined;
    clearTimeout(debounceRef.current);
    let cancelled = false;
    debounceRef.current = setTimeout(() => {
      setLoading(true);
      setFailed(false);
      const params = new URLSearchParams();
      if (q.trim()) params.set('search', q.trim());
      params.set('limit', '60');
      fetch(`${API_URL}/api/bikes?${params.toString()}`)
        .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
        .then((data) => {
          if (!cancelled) {
            setBikes(data.bikes || []);
            setHi(-1);
          }
        })
        .catch(() => {
          if (!cancelled) {
            setBikes([]);
            setFailed(true);
          }
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    }, 220);
    return () => {
      cancelled = true;
      clearTimeout(debounceRef.current);
    };
  }, [q, open]);

  const close = (refocus = false) => {
    setOpen(false);
    if (refocus) triggerRef.current?.focus();
  };

  const pick = (b) => {
    onSelect(b);
    setOpen(false);
    setQ('');
    triggerRef.current?.focus();
  };

  const onKeyDown = (e) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      close(true);
      return;
    }
    if (!bikes.length) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHi((i) => Math.min(bikes.length - 1, i + 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHi((i) => Math.max(0, i - 1));
    } else if (e.key === 'Home') {
      e.preventDefault();
      setHi(0);
    } else if (e.key === 'End') {
      e.preventDefault();
      setHi(bikes.length - 1);
    } else if (e.key === 'Enter' && hi >= 0 && hi < bikes.length) {
      e.preventDefault();
      pick(bikes[hi]);
    }
  };

  const onTriggerKeyDown = (e) => {
    if (e.key === 'ArrowDown' && !open) {
      e.preventDefault();
      setOpen(true);
    } else if (e.key === 'Escape' && open) {
      e.preventDefault();
      setOpen(false);
    }
  };

  // keep the highlighted option scrolled into view
  useEffect(() => {
    if (hi < 0 || !listRef.current) return;
    const el = listRef.current.querySelector(`[data-idx="${hi}"]`);
    el?.scrollIntoView({ block: 'nearest' });
  }, [hi]);

  // Popular chips come from the full catalogue (already fetched once per page
  // for the other pickers), so each chip selects a real, current record.
  const [chips, setChips] = useState([]);
  useEffect(() => {
    if (!popular) return undefined;
    let live = true;
    getBikeCatalog()
      .then((all) => { if (live) setChips(popularChips(all)); })
      .catch(() => { if (live) setChips([]); });
    return () => { live = false; };
  }, [popular]);

  const display = value
    ? `${value.manufacturer || ''} ${value.model || ''}`.trim()
    : 'Choose a bike';

  const specs = [];
  if (value?.displacement_cc != null) specs.push(`${Math.round(value.displacement_cc)} cc`);
  if (value?.peak_power_hp != null) specs.push(`${Math.round(value.peak_power_hp)} hp`);

  return (
    <div className="relative" ref={ref}>
      <label htmlFor={triggerId} className="field-label">
        {label}
      </label>
      <button
        id={triggerId}
        ref={triggerRef}
        type="button"
        onClick={() => setOpen((v) => !v)}
        onKeyDown={onTriggerKeyDown}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={open ? listId : undefined}
        className="input-base flex h-auto min-h-[48px] items-center justify-between gap-2 py-1.5 text-left transition-colors hover:border-white/25"
      >
        <span className="min-w-0 flex-1">
          <span className={`block truncate ${value ? 'text-white' : 'text-white/55'}`}>{display}</span>
          {specs.length > 0 && (
            <span className="block truncate text-xs text-white/60">{specs.join(' · ')}</span>
          )}
        </span>
        <ChevronDown
          size={16}
          aria-hidden="true"
          className={`shrink-0 text-white/55 transition-transform ${open ? 'rotate-180' : ''}`}
        />
      </button>
      {hint && <p className="field-hint">{hint}</p>}

      {popular && chips.length > 0 && !value && (
        <div className="mt-2.5 flex flex-wrap gap-2" role="group" aria-label="Popular bikes">
          {chips.map((c) => (
            <button
              key={c.label}
              type="button"
              onClick={() => pick(c.bike)}
              className="inline-flex min-h-[44px] items-center rounded-full border border-white/15 px-4 text-sm font-medium text-white/80 transition-colors hover:border-accent/60 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/70"
            >
              {c.label}
            </button>
          ))}
        </div>
      )}

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.15 }}
            className="absolute z-30 mt-1.5 w-full overflow-hidden rounded-xl border border-white/10 bg-asphalt-1 shadow-2xl"
            style={{ boxShadow: 'var(--overlay-shadow)' }}
          >
            <div className="border-b border-white/[0.08] p-2">
              <div className="relative">
                <Search
                  size={16}
                  aria-hidden="true"
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-white/55"
                />
                <input
                  autoFocus
                  type="text"
                  role="combobox"
                  aria-expanded={open}
                  aria-controls={listId}
                  aria-autocomplete="list"
                  aria-activedescendant={hi >= 0 ? optId(hi) : undefined}
                  aria-label="Search bikes"
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                  onKeyDown={onKeyDown}
                  placeholder={placeholder}
                  autoComplete="off"
                  className="input-base h-11 pl-9 pr-3"
                />
              </div>
            </div>
            <div
              ref={listRef}
              id={listId}
              role="listbox"
              aria-label="Bikes"
              className="max-h-64 overflow-y-auto"
            >
              {loading ? (
                <div className="space-y-2 p-3" aria-hidden="true">
                  <div className="skeleton h-4 w-3/4" />
                  <div className="skeleton h-4 w-2/3" />
                  <div className="skeleton h-4 w-4/5" />
                </div>
              ) : bikes.length === 0 ? (
                <p className="px-3 py-4 text-sm text-white/60" role="status">
                  {failed
                    ? "Couldn't load bikes. Check your connection and try again."
                    : 'No bikes match that search.'}
                </p>
              ) : (
                bikes.map((b, i) => (
                  <button
                    key={b.id}
                    id={optId(i)}
                    data-idx={i}
                    type="button"
                    role="option"
                    tabIndex={-1}
                    aria-selected={value?.id === b.id}
                    onClick={() => pick(b)}
                    onMouseEnter={() => setHi(i)}
                    className={`flex min-h-[44px] w-full items-center justify-between gap-2 border-l-2 px-3 py-2 text-left transition-colors ${
                      i === hi
                        ? 'border-accent bg-white/[0.1]'
                        : 'border-transparent hover:bg-white/[0.06]'
                    }`}
                  >
                    <span className="truncate text-sm text-white/90">
                      {b.manufacturer} {b.model}
                    </span>
                    <span className="shrink-0 text-xs text-white/60">
                      {b.displacement_cc ? `${Math.round(b.displacement_cc)} cc` : ''}
                    </span>
                  </button>
                ))
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
