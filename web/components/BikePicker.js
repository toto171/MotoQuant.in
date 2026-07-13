'use client';

/**
 * BikePicker — the ONE bike-selection control (STAGED v4).
 *
 * Replaces the byte-identical pickers that lived inside BuildOptimizer.js and
 * EcuAutotune.js. Same visual language, upgraded to a real combobox:
 *   - aria-expanded / role="listbox" / role="option" + aria-selected
 *   - full keyboard support: ↑ ↓ move, Enter selects, Escape closes
 *   - debounced /api/bikes?search= (220 ms), skeleton rows while loading
 *   - optional `popular` quick chips so first-time users get one-tap starts
 *
 * Props
 *  - value    : selected bike object | null ({id, manufacturer, model, …})
 *  - onSelect : (bike) => void
 *  - label    : field label (default 'Bike')
 *  - popular  : optional [{label, search}] quick chips — chip click runs the
 *               search and selects the first hit
 */

import { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { ChevronDown, Search, Wrench } from 'lucide-react';
import { API_URL } from '@/lib/api';

const LIST_ID = 'bike-picker-listbox';

export default function BikePicker({ value, onSelect, label = 'Bike', popular = null }) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState('');
  const [bikes, setBikes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hi, setHi] = useState(-1); // highlighted option index
  const ref = useRef(null);
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
          if (!cancelled) setBikes([]);
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

  const pick = (b) => {
    onSelect(b);
    setOpen(false);
    setQ('');
  };

  const onKeyDown = (e) => {
    if (e.key === 'Escape') {
      setOpen(false);
      return;
    }
    if (!bikes.length) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHi((i) => Math.min(bikes.length - 1, i + 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHi((i) => Math.max(0, i - 1));
    } else if (e.key === 'Enter' && hi >= 0 && hi < bikes.length) {
      e.preventDefault();
      pick(bikes[hi]);
    }
  };

  // keep the highlighted option scrolled into view
  useEffect(() => {
    if (hi < 0 || !listRef.current) return;
    const el = listRef.current.querySelector(`[data-idx="${hi}"]`);
    el?.scrollIntoView({ block: 'nearest' });
  }, [hi]);

  const pickPopular = async (search) => {
    try {
      const r = await fetch(
        `${API_URL}/api/bikes?search=${encodeURIComponent(search)}&limit=1`
      );
      if (!r.ok) return;
      const data = await r.json();
      if (data.bikes?.[0]) pick(data.bikes[0]);
    } catch {
      /* chip is a convenience — stay quiet on failure */
    }
  };

  const display = value
    ? `${value.manufacturer || ''} ${value.model || ''}`.trim()
    : 'Select a bike';

  return (
    <div className="relative" ref={ref}>
      <span className="label-mono mb-1.5 flex items-center gap-1.5">
        <Wrench size={11} className="text-white/40" aria-hidden="true" /> {label}
      </span>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={open ? LIST_ID : undefined}
        className="input-base flex items-center justify-between gap-2 text-left transition-colors hover:border-white/20"
      >
        <span className={`truncate text-sm ${value ? 'text-white' : 'text-white/40'}`}>
          {display}
          {value?.displacement_cc != null && (
            <span className="label-mono ml-2">
              {Math.round(value.displacement_cc)}cc
              {value.peak_power_hp != null && ` · ${Math.round(value.peak_power_hp)} hp`}
            </span>
          )}
        </span>
        <ChevronDown
          size={15}
          aria-hidden="true"
          className={`shrink-0 text-white/40 transition-transform ${open ? 'rotate-180' : ''}`}
        />
      </button>

      {popular && popular.length > 0 && !value && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {popular.map((p) => (
            <button
              key={p.label}
              type="button"
              onClick={() => pickPopular(p.search)}
              className="chip transition-colors hover:border-accent/40 hover:text-white"
            >
              {p.label}
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
            className="absolute z-30 mt-1.5 w-full overflow-hidden rounded-lg border border-white/10 bg-asphalt-1 shadow-2xl"
          >
            <div className="border-b border-white/[0.08] p-2">
              <div className="relative">
                <Search
                  size={14}
                  aria-hidden="true"
                  className="absolute left-2.5 top-1/2 -translate-y-1/2 text-white/40"
                />
                <input
                  autoFocus
                  type="text"
                  role="combobox"
                  aria-expanded={open}
                  aria-controls={LIST_ID}
                  aria-activedescendant={hi >= 0 ? `bike-opt-${hi}` : undefined}
                  aria-label="Search bikes"
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                  onKeyDown={onKeyDown}
                  placeholder="Search bikes…"
                  className="input-base h-10 pl-8 pr-3 font-mono"
                />
              </div>
            </div>
            <div ref={listRef} id={LIST_ID} role="listbox" className="max-h-64 overflow-y-auto">
              {loading ? (
                <div className="space-y-2 p-3" aria-hidden="true">
                  <div className="skeleton h-4 w-3/4" />
                  <div className="skeleton h-4 w-2/3" />
                  <div className="skeleton h-4 w-4/5" />
                </div>
              ) : bikes.length === 0 ? (
                <p className="px-3 py-4 font-mono text-xs text-white/40">No bikes found.</p>
              ) : (
                bikes.map((b, i) => (
                  <button
                    key={b.id}
                    id={`bike-opt-${i}`}
                    data-idx={i}
                    type="button"
                    role="option"
                    aria-selected={value?.id === b.id}
                    onClick={() => pick(b)}
                    onMouseEnter={() => setHi(i)}
                    className={`flex w-full items-center justify-between gap-2 border-l-2 px-3 py-2 text-left transition-colors ${
                      i === hi
                        ? 'border-accent bg-white/[0.06]'
                        : 'border-transparent hover:bg-white/[0.06]'
                    }`}
                  >
                    <span className="truncate text-sm text-white/90">
                      {b.manufacturer} {b.model}
                    </span>
                    <span className="label-mono shrink-0">
                      {b.displacement_cc ? `${Math.round(b.displacement_cc)}cc` : ''}
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
