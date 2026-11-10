'use client';

/**
 * CommandPalette — ⌘K / Ctrl+K jump-anywhere (CLARITY v6).
 *
 * One input, grouped results:
 *   - Actions/pages: static route list with keyword aliases (fuzzy-ish match)
 *   - Bikes: live /api/bikes?search= (debounced) — the 534-bike catalog is the
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
  { label: 'Quarter-mile simulator', desc: 'See how fast a bike runs the quarter mile', href: '/simulator', kw: 'sim simulate run race et elapsed time calculate calculator', icon: Gauge, group: 'Tools' },
  { label: 'Upgrades: best parts for your budget', desc: 'We test every compatible part and pick the quickest mix', href: '/optimize', kw: 'optimize optimizer parts budget knapsack roi upgrade build mods', icon: Wrench, group: 'Tools' },
  { label: 'Race-day setup', desc: 'Gearing, launch RPM and tyre pressure for today\'s air', href: '/autotune', kw: 'autotune tune tuning gearing launch rpm tyre tire pressure conditions ecu setup', icon: Zap, group: 'Tools' },
  { label: 'Browse bikes', desc: 'Search every motorcycle you can simulate', href: '/bikes', kw: 'bikes motorcycles catalog database specs', icon: Search, group: 'Tools' },
  { label: 'Leaderboard', desc: 'Every bike ranked by simulated stock time', href: '/leaderboard', kw: 'top fastest quickest board ranking times stock compare', icon: Trophy, group: 'Tools' },
  { label: 'Getting started', desc: 'A 5-minute walkthrough of the simulator', href: '/docs/getting-started', kw: 'documentation guide help how to start tutorial', icon: BookOpen, group: 'Learn' },
  { label: 'Glossary', desc: 'Drag-racing terms in plain English', href: '/docs/glossary', kw: 'terms jargon meaning et trap sixty launch definitions what is', icon: BookOpen, group: 'Learn' },
  { label: 'How the physics works', desc: 'What the simulator calculates, step by step', href: '/docs/physics', kw: 'rk4 submodels engine model documentation physics', icon: BookOpen, group: 'Learn' },
  { label: 'Accuracy', desc: 'How close predictions are to real timeslips', href: '/validation', kw: 'validation benchmarks error trust accurate', icon: BookOpen, group: 'Learn' },
  { label: 'Blog', desc: 'Guides and deep dives', href: '/blog', kw: 'articles posts guides comparisons', icon: BookOpen, group: 'Learn' },
  { label: 'About MotoQuant', desc: 'Who builds this, and why it is open source', href: '/about', kw: 'story founders contact team', icon: ArrowRight, group: 'Learn' },
  { label: 'Features', desc: 'Everything the simulator can do', href: '/features', kw: 'what can it do capabilities overview', icon: ArrowRight, group: 'Learn' },
  { label: 'Whitepaper', desc: 'The method behind the numbers', href: '/whitepaper', kw: 'paper methodology research physics', icon: BookOpen, group: 'Learn' },
  { label: 'Source code on GitHub', desc: 'MotoQuant is free and open source (Apache-2.0)', href: 'https://github.com/toto171/MotoQuant.in', kw: 'github open source apache license code repo contribute', icon: ArrowRight, group: 'Project' },
  { label: 'Your runs', desc: 'Runs you saved in this browser', href: '/runs', kw: 'saved runs history garage timeslips my runs', icon: ArrowRight, group: 'Project' },
];

function matchActions(q) {
  const t = q.trim().toLowerCase();
  if (!t) return ACTIONS.slice(0, 6);
  const terms = t.split(/\s+/);
  return ACTIONS.filter((a) => {
    const hay = `${a.label} ${a.desc} ${a.kw}`.toLowerCase();
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
      sub: a.desc,
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
        } · view specs`,
        icon: Search,
        href: `/bikes/${b.id}`,
      });
      out.push({
        kind: 'bike-sim',
        key: `s:${b.id}`,
        label: `Simulate the ${name}`,
        sub: 'Open it in the simulator',
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
      if (/^https?:\/\//.test(row.href)) {
        window.open(row.href, '_blank', 'noopener,noreferrer');
        return;
      }
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
          className="fixed inset-0 z-[100] flex items-start justify-center bg-black/50 backdrop-blur-sm px-4 pt-[12vh]"
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
            className="w-full max-w-xl overflow-hidden rounded-2xl border border-white/10 bg-asphalt-1 shadow-[var(--overlay-shadow)]"
          >
            {/* Input strip — the .input-base voice (asphalt field, quiet placeholder) */}
            <div className="flex items-center gap-3 border-b border-white/10 bg-asphalt-3/60 px-4">
              <Search size={16} className="shrink-0 text-white/55" aria-hidden="true" />
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
                placeholder="Search bikes, pages and tools…"
                className="h-14 w-full bg-transparent text-base text-white placeholder:text-white/50 focus:outline-none"
              />
              <kbd className="chip shrink-0">Esc</kbd>
            </div>

            <div ref={listRef} id="cmdk-results" role="listbox" className="max-h-[46vh] overflow-y-auto p-2">
              {rows.length === 0 && !bikesLoading && (
                <p className="px-3 py-6 text-center text-sm text-white/60">
                  No matches. Try a bike name, “upgrades” or “glossary”.
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
                      ? 'Pages and tools'
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
                        className={i === hi ? 'text-white/80' : 'text-white/55'}
                      />
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-sm text-white/90">{row.label}</span>
                        <span className="block truncate text-xs text-white/60">
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
              <span className="label-mono">↑↓ to move · Enter to open</span>
              <span className="label-mono">Every bike is searchable</span>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
