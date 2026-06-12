'use client';

/**
 * BuildOptimizer — budget-constrained parts build optimiser.
 *
 * Lets a user pick a bike, set a ₹ budget, choose an optimisation goal
 * (min ET vs max trap) and a build profile (all / street-legal / drag-prep
 * / full-race), then calls POST /api/optimize/build and renders:
 *   - base → optimised ET & trap with deltas
 *   - total cost / budget-used % / cost-per-tenth
 *   - the selected parts list (name, category, price, ΔET)
 *   - the scoring-method chip (full_sim vs surrogate(dnn))
 *   - detected part synergies + compatibility warnings
 *   - the suggested next upgrade beyond the budget
 *
 * Mirrors SimulatorWidget's "use client" structure, glass-card styling,
 * brand-orange / brand-accent palette, framer-motion entrances, and
 * loading / error / empty handling. All optional / nullable fields
 * (cost_per_tenth_inr, roi_score, next_upgrade, synergies, warnings)
 * are guarded.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Wrench, Search, ChevronDown, AlertCircle, AlertTriangle, IndianRupee,
  TrendingDown, TrendingUp, Sparkles, ArrowRight, Cpu, Gauge, Layers,
} from 'lucide-react';
import { API_URL, optimizeBuildJob } from '../lib/api';
import SimProgress from './SimProgress';

// ─── helpers ────────────────────────────────────────────────────────────────
const fmtINR = (n) =>
  n == null ? '—' : `₹${Math.round(n).toLocaleString('en-IN')}`;
const fmtNum = (n, d = 1) => (n == null ? '—' : Number(n).toFixed(d));
const fmtDelta = (n, d = 3) =>
  n == null ? '—' : `${n > 0 ? '+' : ''}${Number(n).toFixed(d)}`;
// Sign-aware tone for ET / trap deltas. Backend convention (build_optimizer.py):
// delta_et_s = base − optimized, delta_trap = optimized − base ⇒ positive = faster.
// Purely presentational — no data-flow change.
const deltaTone = (n) =>
  n == null || Number(n) === 0
    ? 'text-white/50'
    : Number(n) > 0
      ? 'text-brand-accent'
      : 'text-brand-red';

const GOALS = [
  { id: 'min_et', label: 'Min ET', icon: TrendingDown },
  { id: 'max_trap', label: 'Max Trap', icon: TrendingUp },
];

const PROFILES = [
  { id: 'all', label: 'All parts' },
  { id: 'street_legal', label: 'Street legal' },
  { id: 'drag_prep', label: 'Drag prep' },
  { id: 'full_race', label: 'Full race' },
];

const BUDGET_PRESETS = [25000, 50000, 100000, 250000, 500000];

// ─── Bike picker (self-contained, debounced /api/bikes search) ───────────────
function BikePicker({ value, onSelect }) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState('');
  const [bikes, setBikes] = useState([]);
  const [loading, setLoading] = useState(false);
  const ref = useRef(null);
  const debounceRef = useRef(null);

  useEffect(() => {
    const h = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, []);

  useEffect(() => {
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      let cancelled = false;
      setLoading(true);
      const params = new URLSearchParams();
      if (q.trim()) params.set('search', q.trim());
      params.set('limit', '60');
      fetch(`${API_URL}/api/bikes?${params.toString()}`)
        .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
        .then((data) => {
          if (!cancelled) setBikes(data.bikes || []);
        })
        .catch(() => {
          if (!cancelled) setBikes([]);
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
      return () => {
        cancelled = true;
      };
    }, 220);
    return () => clearTimeout(debounceRef.current);
  }, [q]);

  const label = value
    ? `${value.manufacturer || ''} ${value.model || ''}`.trim()
    : 'Select a bike';

  return (
    <div className="relative" ref={ref}>
      <label className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.25em] text-white/45 mb-1.5">
        <Wrench size={11} className="text-brand-orange" /> Bike
      </label>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-3 py-2.5 rounded-lg border border-white/10 bg-ink-1 hover:border-brand-orange/40 text-left transition-colors"
      >
        <span className={`text-sm truncate ${value ? 'text-white' : 'text-white/40'}`}>
          {label}
          {value?.displacement_cc != null && (
            <span className="ml-2 text-[11px] font-mono text-white/40">
              {Math.round(value.displacement_cc)}cc
              {value.peak_power_hp != null && ` · ${Math.round(value.peak_power_hp)} hp`}
            </span>
          )}
        </span>
        <ChevronDown size={15} className={`text-white/40 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.15 }}
            className="absolute z-30 mt-1.5 w-full rounded-lg border border-white/10 bg-ink-2 shadow-2xl overflow-hidden"
          >
            <div className="p-2 border-b border-white/5">
              <div className="relative">
                <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-white/40" />
                <input
                  autoFocus
                  type="text"
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                  placeholder="Search bikes…"
                  className="w-full pl-8 pr-3 py-2 bg-ink-1 border border-white/10 rounded-md text-sm text-white placeholder:text-white/30 focus:border-brand-orange/60 focus:outline-none font-mono"
                />
              </div>
            </div>
            <div className="max-h-64 overflow-y-auto">
              {loading ? (
                <p className="px-3 py-4 text-xs text-white/40 font-mono">Loading…</p>
              ) : bikes.length === 0 ? (
                <p className="px-3 py-4 text-xs text-white/40 font-mono">No bikes found.</p>
              ) : (
                bikes.map((b) => (
                  <button
                    key={b.id}
                    type="button"
                    onClick={() => {
                      onSelect(b);
                      setOpen(false);
                    }}
                    className="w-full px-3 py-2 text-left hover:bg-brand-orange/10 transition-colors flex items-center justify-between gap-2"
                  >
                    <span className="text-sm text-white/90 truncate">
                      {b.manufacturer} {b.model}
                    </span>
                    <span className="text-[10px] font-mono text-white/40 shrink-0">
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

// ─── stat tile ───────────────────────────────────────────────────────────────
function StatTile({ label, value, sub, accent }) {
  return (
    <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 text-center">
      <p className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/45 mb-1.5">{label}</p>
      <p className={`text-2xl sm:text-3xl font-mono font-bold ${accent || 'text-white'}`}>{value}</p>
      {sub != null && <p className="text-[11px] text-white/40 mt-1.5 font-mono">{sub}</p>}
    </div>
  );
}

// ─── main ─────────────────────────────────────────────────────────────────────
export default function BuildOptimizer() {
  const [bike, setBike] = useState(null);
  const [budget, setBudget] = useState(100000);
  const [goal, setGoal] = useState('min_et');
  const [profile, setProfile] = useState('all');
  const [riderKg, setRiderKg] = useState(75);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [prog, setProg] = useState(null); // {progress, stage} from the jobs poller
  const abortRef = useRef(null);

  const stop = useCallback(() => {
    abortRef.current?.abort(); // runJob also cancels the job server-side
    setLoading(false);
    setProg(null);
  }, []);

  const run = useCallback(async () => {
    if (!bike) {
      setError('Pick a bike first.');
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    const controller = new AbortController();
    abortRef.current = controller;
    try {
      // Background job — SimProgress tracks real candidate-scoring progress.
      const data = await optimizeBuildJob(
        {
          bike_id: bike.id,
          budget_inr: budget,
          goal,
          profile,
          rider_weight_kg: riderKg,
        },
        setProg,
        controller.signal,
      );
      setResult(data);
    } catch (e) {
      if (e?.name === 'AbortError') return; // user pressed Stop
      setError(e.message || 'Optimisation failed.');
    } finally {
      setLoading(false);
      setProg(null);
    }
  }, [bike, budget, goal, profile, riderKg]);

  const parts = result?.parts || [];
  const synergies = result?.synergies || [];
  const warnings = result?.warnings || [];
  const noParts = result && parts.length === 0;

  return (
    <div className="space-y-6">
      {/* ── Controls card ───────────────────────────────────────────── */}
      <div className="relative bg-white/[0.02] backdrop-blur-xl border border-brand-orange/20 rounded-2xl p-5 sm:p-7">
        {/* orange hairline — promoted controls panel */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-brand-orange/70 to-transparent"
        />
        <AnimatePresence>
          {loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute top-0 left-1 right-1 z-20"
            >
              <SimProgress active edge progress={prog?.progress ?? null} />
            </motion.div>
          )}
        </AnimatePresence>

        <div className="relative z-10 space-y-5">
          <BikePicker value={bike} onSelect={setBike} />

          {/* Budget */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.25em] text-white/45">
                <IndianRupee size={11} className="text-brand-orange" /> Budget
              </label>
              <span className="text-sm font-mono font-bold text-brand-orange tabular-nums">{fmtINR(budget)}</span>
            </div>
            <input
              type="range"
              min={5000}
              max={800000}
              step={5000}
              value={budget}
              onChange={(e) => setBudget(Number(e.target.value))}
              className="w-full h-1.5 bg-white/10 rounded-full appearance-none cursor-pointer accent-brand-orange"
            />
            <div className="flex flex-wrap gap-1.5 mt-2.5">
              {BUDGET_PRESETS.map((b) => (
                <button
                  key={b}
                  type="button"
                  onClick={() => setBudget(b)}
                  className={`px-2.5 py-1 rounded-full text-[11px] font-mono border transition-colors ${
                    budget === b
                      ? 'bg-brand-orange/20 border-brand-orange/50 text-white'
                      : 'bg-white/[0.04] border-white/10 text-white/60 hover:text-white'
                  }`}
                >
                  {fmtINR(b)}
                </button>
              ))}
            </div>
          </div>

          {/* Goal + profile */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block font-mono text-[10px] uppercase tracking-[0.25em] text-white/45 mb-1.5">Goal</label>
              <div className="flex gap-1 bg-white/[0.04] rounded-lg p-1 border border-white/10">
                {GOALS.map(({ id, label, icon: Icon }) => (
                  <button
                    key={id}
                    type="button"
                    onClick={() => setGoal(id)}
                    className={`flex-1 flex items-center justify-center gap-1.5 px-2 py-1.5 rounded-md text-xs font-semibold transition-all ${
                      goal === id ? 'bg-brand-orange text-black shadow-sm' : 'text-white/50 hover:text-white/80'
                    }`}
                  >
                    <Icon size={12} /> {label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block font-mono text-[10px] uppercase tracking-[0.25em] text-white/45 mb-1.5">Profile</label>
              <div className="relative">
                <Layers size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-white/40 pointer-events-none" />
                <select
                  value={profile}
                  onChange={(e) => setProfile(e.target.value)}
                  className="w-full appearance-none pl-8 pr-8 py-2 bg-ink-1 border border-white/10 rounded-lg text-sm text-white focus:border-brand-orange/60 focus:outline-none cursor-pointer"
                >
                  {PROFILES.map((p) => (
                    <option key={p.id} value={p.id} className="bg-ink-2">
                      {p.label}
                    </option>
                  ))}
                </select>
                <ChevronDown size={14} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-white/40 pointer-events-none" />
              </div>
            </div>
          </div>

          {/* Rider weight */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block font-mono text-[10px] uppercase tracking-[0.25em] text-white/45">Rider weight</label>
              <span className="text-sm font-mono text-white/80 tabular-nums">{riderKg} kg</span>
            </div>
            <input
              type="range"
              min={50}
              max={130}
              value={riderKg}
              onChange={(e) => setRiderKg(Number(e.target.value))}
              className="w-full h-1.5 bg-white/10 rounded-full appearance-none cursor-pointer accent-brand-orange"
            />
          </div>

          {loading && (
            <SimProgress
              active
              progress={prog?.progress ?? null}
              stage={prog?.stage}
              label="Optimising build"
            />
          )}

          <motion.button
            onClick={loading ? stop : run}
            disabled={!bike}
            whileHover={{ scale: !bike ? 1 : 1.01 }}
            whileTap={{ scale: !bike ? 1 : 0.99 }}
            className={`w-full py-3.5 rounded-md text-sm flex items-center justify-center gap-2 transition-all disabled:opacity-40 disabled:cursor-not-allowed disabled:saturate-50 ${
              loading
                ? 'bg-brand-red/15 border border-brand-red/50 text-brand-red font-mono'
                : 'bg-brand-orange hover:bg-brand-orangeLight text-black font-display font-bold shadow-orange-soft'
            }`}
          >
            {loading ? (
              <span className="tabular-nums">
                ■ Stop — Optimising…{prog?.progress != null ? ` ${Math.round(prog.progress * 100)}%` : ''}
              </span>
            ) : (
              <>
                <Wrench size={16} /> Optimise build
              </>
            )}
          </motion.button>
        </div>
      </div>

      {/* ── Error ───────────────────────────────────────────────────── */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="p-3 bg-brand-red/10 border border-brand-red/30 rounded-lg text-brand-red text-sm flex items-center gap-2"
          >
            <AlertCircle size={16} /> {error}
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Empty (no parts found) ──────────────────────────────────── */}
      {noParts && !loading && (
        <div className="p-6 rounded-xl border border-white/[0.06] bg-white/[0.02] text-center">
          <p className="text-white/70 text-sm font-semibold mb-1">No improving parts within budget</p>
          <p className="text-white/40 text-xs">
            Nothing in the {result.profile} catalog improves {result.bike_name} for{' '}
            {fmtINR(result.budget_inr)}. Try raising the budget or widening the profile.
          </p>
        </div>
      )}

      {/* ── Results ─────────────────────────────────────────────────── */}
      <AnimatePresence>
        {result && parts.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
            transition={{ duration: 0.35 }}
            className="space-y-5"
          >
            {/* Header row: bike + scoring chip */}
            <div className="flex items-center justify-between flex-wrap gap-2">
              <h3 className="font-display text-lg font-bold text-white">
                {result.bike_name}
                <span className="ml-2 font-mono text-[10px] uppercase tracking-[0.25em] text-white/45">
                  {result.goal === 'max_trap' ? 'max trap' : 'min ET'} · {result.profile}
                </span>
              </h3>
              {result.scoring_method && (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-brand-accent/10 border border-brand-accent/30 text-[11px] font-mono text-brand-accent">
                  <Cpu size={11} /> {result.scoring_method}
                  {result.scoring_stats?.out_of_envelope > 0 && (
                    <span className="text-brand-amber/80" title="some candidates fell outside the surrogate envelope">
                      · {result.scoring_stats.out_of_envelope} oob
                    </span>
                  )}
                </span>
              )}
            </div>

            {/* Before → after */}
            <div className="grid grid-cols-2 gap-4">
              <StatTile
                label="ET (stock → tuned)"
                value={
                  <span>
                    {fmtNum(result.optimized_et_s, 3)}
                    <span className="text-base ml-1">s</span>
                  </span>
                }
                sub={
                  <>
                    from {fmtNum(result.base_et_s, 3)}s ·{' '}
                    <span className={deltaTone(result.delta_et_s)}>
                      {fmtDelta(result.delta_et_s, 3)}s
                    </span>
                  </>
                }
                accent="text-brand-orange"
              />
              <StatTile
                label="Trap (stock → tuned)"
                value={
                  <span>
                    {fmtNum(result.optimized_trap_kmh, 1)}
                  </span>
                }
                sub={
                  <>
                    from {fmtNum(result.base_trap_kmh, 1)} ·{' '}
                    <span className={deltaTone(result.delta_trap_kmh)}>
                      {fmtDelta(result.delta_trap_kmh, 1)}
                    </span>{' '}
                    km/h
                  </>
                }
                accent="text-white"
              />
            </div>

            {/* Cost summary */}
            <div className="grid grid-cols-3 gap-3">
              <StatTile label="Total cost" value={fmtINR(result.total_cost_inr)} accent="text-white" />
              <StatTile
                label="Budget used"
                value={`${fmtNum(result.budget_used_pct, 0)}%`}
                accent="text-brand-accent"
              />
              <StatTile
                label="Cost / tenth"
                value={result.cost_per_tenth_inr == null ? '—' : fmtINR(result.cost_per_tenth_inr)}
                accent="text-white"
              />
            </div>

            {/* Selected parts */}
            <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 sm:p-5">
              <div className="flex items-center justify-between mb-3">
                <p className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/45">
                  Selected parts ({parts.length})
                </p>
                <p className="text-[10px] font-mono text-white/30">
                  {result.parts_evaluated} evaluated
                  {result.parts_skipped_incompatible ? ` · ${result.parts_skipped_incompatible} incompatible` : ''}
                  {result.parts_skipped_no_gain ? ` · ${result.parts_skipped_no_gain} no-gain` : ''}
                </p>
              </div>
              <div className="space-y-1.5">
                {parts.map((p) => (
                  <div
                    key={p.part_id}
                    className="flex items-center justify-between gap-3 px-3 py-2.5 rounded-lg bg-white/[0.03] border border-white/[0.06]"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="text-sm text-white font-medium truncate">
                        {p.brand ? `${p.brand} ` : ''}{p.name}
                        {p.is_compatible === false && (
                          <span className="ml-2 text-[10px] text-brand-amber/80 font-mono">incompatible</span>
                        )}
                      </p>
                      <p className="text-[10px] font-mono text-white/40 uppercase tracking-wide mt-0.5">
                        {p.category_display || p.category}
                        {p.cost_per_tenth_inr != null && (
                          <span className="ml-2 text-white/30">{fmtINR(p.cost_per_tenth_inr)}/tenth</span>
                        )}
                      </p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-sm font-mono text-white tabular-nums">{fmtINR(p.price_inr)}</p>
                      <p className={`text-[11px] font-mono tabular-nums ${deltaTone(p.delta_et_s)}`}>
                        {fmtDelta(p.delta_et_s, 3)}s
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Synergies */}
            {synergies.length > 0 && (
              <div className="bg-brand-accent/[0.06] border border-brand-accent/25 rounded-xl p-4">
                <p className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.25em] text-brand-accent mb-2.5">
                  <Sparkles size={13} /> Synergies
                </p>
                <div className="space-y-1.5">
                  {synergies.map((s, i) => (
                    <div key={i} className="flex items-start justify-between gap-3 text-sm">
                      <span className="text-white/80">{s.description}</span>
                      {s.multiplier != null && (
                        <span className="font-mono text-brand-accent shrink-0 tabular-nums">
                          ×{Number(s.multiplier).toFixed(2)}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Warnings */}
            {warnings.length > 0 && (
              <div className="bg-brand-amber/[0.06] border border-brand-amber/25 rounded-xl p-4">
                <p className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.25em] text-brand-amber mb-2.5">
                  <AlertTriangle size={13} /> Warnings
                </p>
                <div className="space-y-1.5">
                  {warnings.map((w, i) => (
                    <p key={i} className="text-sm text-white/80">
                      <span className="text-[10px] font-mono uppercase text-brand-amber/70 mr-2">{w.severity}</span>
                      {w.message}
                    </p>
                  ))}
                </div>
              </div>
            )}

            {/* Next upgrade */}
            {result.next_upgrade?.part && (
              <div className="bg-white/[0.03] border border-white/10 rounded-xl p-4">
                <p className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.25em] text-white/45 mb-2.5">
                  <ArrowRight size={13} className="text-brand-orange" /> Next upgrade (beyond budget)
                </p>
                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-sm text-white font-medium truncate">
                      {result.next_upgrade.part.brand ? `${result.next_upgrade.part.brand} ` : ''}
                      {result.next_upgrade.part.name}
                    </p>
                    {result.next_upgrade.reason && (
                      <p className="text-[11px] text-white/40 mt-0.5">{result.next_upgrade.reason}</p>
                    )}
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-sm font-mono text-white tabular-nums">
                      {fmtINR(result.next_upgrade.marginal_cost_inr)}
                    </p>
                    <p className={`text-[11px] font-mono tabular-nums ${deltaTone(result.next_upgrade.marginal_et_gain_s)}`}>
                      {fmtDelta(result.next_upgrade.marginal_et_gain_s, 3)}s
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Category priority */}
            {Array.isArray(result.category_priority) && result.category_priority.length > 0 && (
              <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 sm:p-5">
                <p className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.25em] text-white/45 mb-3">
                  <Gauge size={13} className="text-brand-orange" /> Where the gains are
                </p>
                <div className="space-y-1.5">
                  {result.category_priority.slice(0, 6).map((c, i) => (
                    <div key={i} className="flex items-center justify-between gap-3 text-sm">
                      <span className="text-white/80 capitalize truncate">
                        {String(c.category || '').replace(/_/g, ' ')}
                      </span>
                      <span className="font-mono text-white/50 shrink-0 tabular-nums text-xs">
                        best {fmtDelta(c.best_et_gain_s, 3)}s
                        {c.avg_cost_per_tenth != null && ` · ${fmtINR(c.avg_cost_per_tenth)}/tenth`}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <p className="text-[11px] text-white/30 text-center pt-1">
              Estimates from first-principles RK4 physics · ROI knapsack across compatible parts.
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
