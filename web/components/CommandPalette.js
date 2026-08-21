'use client';

/**
 * CommandPalette — ⌘K / Ctrl+K jump-anywhere (IGNITION v5 skin).
 *
 * One input, grouped results:
 *   - Actions/pages: static route list with keyword aliases (fuzzy-ish match)
 *   - Bikes: live /api/bikes?search= (debounced) — the 541-bike catalog is the
 *     product, so "haya…" should take you to the bike, or straight into the
 *     simulator with it preloaded.
 *
 * Mounted once inside SiteNav (which is on every page). Opens via the nav
 * search button or the global hotkey. Full keyboard support: ↑↓ move, Enter
 * selects, Esc closes. Backdrop click closes. Body scroll locked while open.
 * Reduced-motion safe (opacity-only entrance).
 */

import { Fragment, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import {
  ArrowRight,
  BookOpen,
  Gauge,
  Search,
  Trophy,
  Wrench,
  Zap,
} from 'lucide-react';
import { API_URL } from '@/lib/api';

const ACTIONS = [
  { label: 'Run the simulator', href: '/simulator', kw: 'sim simulate quarter mile et run race', icon: Gauge, group: 'Tools' },
  { label: 'Optimize a build', href: '/optimize', kw: 'parts budget knapsack roi upgrade build optimizer', icon: Wrench, group: 'Tools' },
  { label: 'ECU autotune setup', href: '/autotune', kw: 'tune gearing launch rpm tyre pressure conditions ecu', icon: Zap, group: 'Tools' },
  { label: 'Browse the bike catalog', href: '/bikes', kw: 'bikes motorcycles catalog database specs', icon: Search, group: 'Tools' },
  { label: 'Leaderboard', href: '/leaderboard', kw: 'top runs fastest board ranking times', icon: Trophy, group: 'Tools' },
  { label: 'Pricing & plans', href: '/pricing', kw: 'price pro studio subscribe free cost', icon: ArrowRight, group: 'Pages' },
  { label: 'Docs — getting started', href: '/docs/getting-started', kw: 'documentation guide help how to start', icon: BookOpen, group: 'Pages' },
  { label: 'Docs — physics engine', href: '/docs/physics', kw: 'rk4 submodels engine model documentation', icon: BookOpen, group: 'Pages' },
  { label: 'Docs — validation data', href: '/docs/validation', kw: 'accuracy benchmarks validation error', icon: BookOpen, group: 'Pages' },
  { label: 'Features', href: '/features', kw: 'what can it do capabilities overview', icon: ArrowRight, group: 'Pages' },
  { label: 'Whitepaper', href: '/whitepaper', kw: 'paper methodology research physics', icon: BookOpen, group: 'Pages' },
  { label: 'Blog', href: '/blog', kw: 'articles posts guides comparisons', icon: BookOpen, group: 'Pages' },
  { label: 'About MotoQuant', href: '/about', kw: 'company founders story contact', icon: ArrowRight, group: 'Pages' },
  { label: 'Your account', href: '/account', kw: 'profile garage license keys subscription sign', icon: ArrowRight, group: 'Pages' },
];

function matchActions(q) {
  const t = q.trim().toLowerCase();
  if (!t) return ACTIONS.slice(0, 6);
  const terms = t.split(/\s+/);
  return ACTIONS.filter((a) => {
    const hay = `${a.label} ${a.kw}`.toLowerCase();
    return terms.every((term) => hay.includes(term));
  }).slice(0, 6);
}

export default function CommandPalette({ open, onClose }) {
  const router = useRouter();
  const reduced = useReducedMotion();
  const [q, setQ] = useState('');
  const [bikes, setBikes] = useState([]);
  const [bikesLoading, setBikesLoading] = useState(false);
  const [hi, setHi] = useState(0);
  const inputRef = useRef(null);
  const listRef = useRef(null);
  const debounceRef = useRef(null);

  // Reset on open; lock body scroll while open.
  useEffect(() => {
    if (open) {
      setQ('');
      setBikes([]);
      setHi(0);
      const prev = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
      // focus after the entrance frame
      const t = setTimeout(() => inputRef.current?.focus(), 30);
      return () => {
        document.body.style.overflow = prev;
        clearTimeout(t);
      };
    }
    return undefined;
  }, [open]);

  // Escape closes from anywhere — not just when the input holds focus
  // (focus lands 30 ms after open; other elements can also hold it).
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  // Live bike search (≥2 chars)
  useEffect(() => {
    if (!open) return undefined;
    clearTimeout(debounceRef.current);
    const t = q.trim();
    if (t.length < 2) {
      setBikes([]);
      setBikesLoading(false);
      return undefined;
    }
    setBikesLoading(true);
    let cancelled = false;
    debounceRef.current = setTimeout(() => {
      fetch(`${API_URL}/api/bikes?search=${encodeURIComponent(t)}&limit=6`)
        .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
        .then((d) => {
          if (!cancelled) setBikes(d.bikes || []);
        })
        .catch(() => {
          if (!cancelled) setBikes([]);
        })
        .finally(() => {
          if (!cancelled) setBikesLoading(false);
        });
    }, 180);
    return () => {
      cancelled = true;
      clearTimeout(debounceRef.current);
    };
  }, [q, open]);

  const actionHits = useMemo(() => matchActions(q), [q]);

  // Flat result list for keyboard navigation:
  // bikes contribute TWO entries each (view + simulate).
  const rows = useMemo(() => {
    const out = actionHits.map((a) => ({
      kind: 'action',
      key: `a:${a.href}`,
      label: a.label,
      sub: a.group,
      icon: a.icon,
      href: a.href,
    }));
    for (const b of bikes) {
      const name = `${b.manufacturer} ${b.model}`.trim();
      out.push({
        kind: 'bike',
        key: `b:${b.id}`,
        label: name,
        sub: `${b.displacement_cc ? `${Math.round(b.displacement_cc)}cc` : ''}${
          b.peak_power_hp ? ` · ${Math.round(b.peak_power_hp)} hp` : ''
        } — view specs`,
        icon: Search,
        href: `/bikes/${b.id}`,
      });
      out.push({
        kind: 'bike-sim',
        key: `s:${b.id}`,
        label: `Simulate the ${name}`,
        sub: 'open in the simulator',
        icon: Gauge,
        href: `/simulator?bike_id=${b.id}`,
      });
    }
    return out;
  }, [actionHits, bikes]);

  useEffect(() => {
    setHi((h) => Math.min(h, Math.max(0, rows.length - 1)));
  }, [rows.length]);

  const go = useCallback(
    (row) => {
      if (!row) return;
      onClose();
      router.push(row.href);
    },
    [onClose, router]
  );

  const onKeyDown = (e) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      onClose();
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHi((h) => Math.min(rows.length - 1, h + 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHi((h) => Math.max(0, h - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      go(rows[hi]);
    }
  };

  // keep highlight in view
  useEffect(() => {
    const el = listRef.current?.querySelector(`[data-idx="${hi}"]`);
    el?.scrollIntoView({ block: 'nearest' });
  }, [hi]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: reduced ? 0 : 0.15 }}
          className="fixed inset-0 z-[100] flex items-start justify-center bg-asphalt-0/80 backdrop-blur-sm px-4 pt-[12vh]"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) onClose();
          }}
          role="dialog"
          aria-modal="true"
          aria-label="Command palette"
        >
          <motion.div
            initial={reduced ? false : { opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={reduced ? { opacity: 0 } : { opacity: 0, y: -10 }}
            transition={{ duration: reduced ? 0 : 0.18 }}
            className="w-full max-w-xl overflow-hidden rounded-xl border border-white/10 bg-asphalt-1 shadow-2xl"
          >
            {/* Input strip — the .input-base voice (asphalt field, quiet placeholder) */}
            <div className="flex items-center gap-3 border-b border-white/10 bg-asphalt-3/60 px-4">
              <Search size={16} className="shrink-0 text-white/40" aria-hidden="true" />
              <input
                ref={inputRef}
                type="text"
                role="combobox"
                aria-expanded="true"
                aria-controls="cmdk-results"
                aria-activedescendant={rows[hi] ? `cmdk-${rows[hi].key}` : undefined}
                aria-label="Search pages, bikes and actions"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder="Search bikes, pages, actions…"
                className="h-14 w-full bg-transparent text-[15px] text-white placeholder:text-white/30 focus:outline-none"
              />
              <kbd className="chip shrink-0">esc</kbd>
            </div>

            <div ref={listRef} id="cmdk-results" role="listbox" className="max-h-[46vh] overflow-y-auto p-2">
              {rows.length === 0 && !bikesLoading && (
                <p className="px-3 py-6 text-center font-mono text-xs text-white/40">
                  No matches — try a bike name, “optimize”, “docs”…
                </p>
              )}
              {rows.map((row, i) => {
                const Icon = row.icon;
                // Presentational group headers: one before the action hits,
                // one where the live bike hits begin. aria-hidden so the
                // listbox's option list stays clean for AT.
                const header =
                  i === 0
                    ? row.kind === 'action'
                      ? 'Pages & actions'
                      : 'Bikes'
                    : row.kind === 'bike' && rows[i - 1]?.kind === 'action'
                      ? 'Bikes'
                      : null;
                return (
                  <Fragment key={row.key}>
                    {header && (
                      <div aria-hidden="true" className="label-mono px-3 pb-1.5 pt-3 first:pt-1.5">
                        {header}
                      </div>
                    )}
                    <button
                      id={`cmdk-${row.key}`}
                      data-idx={i}
                      type="button"
                      role="option"
                      aria-selected={i === hi}
                      onClick={() => go(row)}
                      onMouseEnter={() => setHi(i)}
                      className={`flex w-full items-center gap-3 rounded-lg border-l-2 px-3 py-2.5 text-left transition-colors ${
                        i === hi
                          ? 'border-accent bg-white/[0.06]'
                          : 'border-transparent hover:bg-white/5'
                      }`}
                    >
                      <Icon
                        size={15}
                        aria-hidden="true"
                        className={i === hi ? 'text-white/80' : 'text-white/40'}
                      />
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-sm text-white/90">{row.label}</span>
                        <span className="block truncate font-mono text-[10px] uppercase tracking-[0.2em] text-white/35">
                          {row.sub}
                        </span>
                      </span>
                      {i === hi && <kbd className="chip shrink-0">↵</kbd>}
                    </button>
                  </Fragment>
                );
              })}
              {bikesLoading && (
                <div className="space-y-2 p-3" aria-hidden="true">
                  <div className="skeleton h-4 w-2/3" />
                  <div className="skeleton h-4 w-1/2" />
                </div>
              )}
            </div>

            <div className="flex items-center justify-between border-t border-white/10 px-4 py-2">
              <span className="label-mono">↑↓ navigate · ↵ open</span>
              <span className="label-mono">full catalog searchable</span>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
