'use client';

/**
 * BuildOptimizer — budget-constrained parts build optimiser (Cockpit v3).
 *
 * Lets a user pick a bike, set a ₹ budget, choose an optimisation goal
 * (min ET vs max trap) and a build profile (all / street-legal / drag-prep
 * / full-race), then calls the job-backed POST /api/jobs/optimize (with
 * sync fallback) and renders:
 *   - base → optimised ET & trap with deltas
 *   - total cost / budget-used % / cost-per-tenth
 *   - the selected parts list (name, category, price, ΔET)
 *   - the scoring-method chip (full_sim vs surrogate(dnn))
 *   - detected part synergies + compatibility warnings
 *   - the suggested next upgrade beyond the budget
 *
 * v3 changes: shared BikePicker (+ popular chips), two-column workbench
 * (controls left / results right, stacked below lg), useAsyncTask +
 * ActionButton for the run/stop pattern (real % in the button, Stop always
 * live), .card/.label-mono/.btn-* surfaces. The ?bike_id deep-link preselect
 * reads window.location post-mount (NOT useSearchParams) so the page keeps
 * static-prerendering without a Suspense boundary.
 */

import { useEffect, useState } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import {
  Wrench, AlertCircle, AlertTriangle, IndianRupee, ChevronDown,
  TrendingDown, TrendingUp, Sparkles, ArrowRight, Cpu, Gauge, Layers,
} from 'lucide-react';
import { API_URL, optimizeBuildJob, partLabel } from '../lib/api';
import useAsyncTask from '../lib/useAsyncTask';
import ActionButton from './ActionButton';
import SimProgress from './SimProgress';
import BikePicker from './BikePicker';

// ─── helpers ────────────────────────────────────────────────────────────────
const fmtINR = (n) =>
  n == null ? '—' : `₹${Math.round(n).toLocaleString('en-IN')}`;
const fmtNum = (n, d = 1) => (n == null ? '—' : Number(n).toFixed(d));
const fmtDelta = (n, d = 3) =>
  n == null ? '—' : `${n > 0 ? '+' : ''}${Number(n).toFixed(d)}`;
// Sign-aware tone for ET deltas. Convention unified July 6, 2026:
// delta_et_s = optimized − base everywhere ⇒ NEGATIVE = faster (time
// dropped) = good. Trap deltas use the opposite tone (positive = faster).
const deltaTone = (n) =>
  n == null || Number(n) === 0
    ? 'text-white/50'
    : Number(n) < 0
      ? 'text-brand-accent'
      : 'text-brand-red';
const trapTone = (n) =>
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
  { id: 'full_race', label: 'Full race / Outlaw' },
];

const BUDGET_PRESETS = [25000, 50000, 100000, 250000, 500000];
// Outlaw / open class — POST budget_inr: null (the API resolves null/0 to
// its ₹5M internal ceiling = effectively no limit). Sentinel is null in
// component state; the slider shows full-right while unlimited.
const OUTLAW_BUDGET = null;

// One-tap starts for first-time users (shared BikePicker `popular` prop).
const POPULAR_BIKES = [
  { label: 'Hayabusa', search: 'hayabusa' },
  { label: 'R15 V4', search: 'r15 v4' },
  { label: 'Duke 390', search: 'duke 390' },
  { label: 'Classic 350', search: 'classic 350' },
  { label: 'ZX-10R', search: 'zx-10r' },
  { label: 'GSX-R1000', search: 'gsx-r1000' },
];

// ─── stat tile ───────────────────────────────────────────────────────────────
function StatTile({ label, value, sub, accent }) {
  return (
    <div className="card p-4 text-center">
      <p className="label-mono mb-1.5">{label}</p>
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
  const reduce = useReducedMotion();

  // Job-backed run — useAsyncTask owns AbortController + progress + error;
  // optimizeBuildJob polls /api/jobs with real candidate-scoring % and
  // cancels the job server-side when the signal aborts (Stop).
  const task = useAsyncTask(async (signal, onProgress) => {
    if (!bike) throw new Error('Pick a bike first.');
    return optimizeBuildJob(
      {
        bike_id: bike.id,
        budget_inr: budget,
        goal,
        profile,
        rider_weight_kg: riderKg,
      },
      onProgress,
      signal,
    );
  });

  // Preselect a bike from ?bike_id (deep link from /bikes/[id] "Optimize build").
  // Guarded window read (not useSearchParams) so the un-Suspense'd client page
  // keeps prerendering; no-op when the param is absent or invalid.
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const raw = new URLSearchParams(window.location.search).get('bike_id');
    const id = raw != null ? Number(raw) : NaN;
    if (!Number.isInteger(id) || id <= 0) return;
    let cancelled = false;
    fetch(`${API_URL}/api/bikes/${id}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((b) => {
        if (!cancelled && b && b.id != null) {
          setBike({ id: b.id, manufacturer: b.manufacturer, model: b.model });
        }
      })
      .catch(() => {}); // bad id / offline → silently leave the picker empty
    return () => {
      cancelled = true;
    };
  }, []);

  const run = () => {
    task.reset(); // clear the previous result + error before a fresh run
    task.run();
  };

  const result = task.result;
  const parts = result?.parts || [];
  const synergies = result?.synergies || [];
  const warnings = result?.warnings || [];
  const noParts = result && parts.length === 0;

  return (
    <div className="grid gap-6 lg:grid-cols-5 lg:items-start">
      {/* ── Controls (left column) ───────────────────────────────────── */}
      <div className="lg:col-span-2 card relative border-brand-orange/20 p-5 md:p-6">
        {/* orange hairline — promoted controls panel */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-brand-orange/70 to-transparent"
        />
        <AnimatePresence>
          {task.active && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute top-0 left-1 right-1 z-20"
            >
              <SimProgress active edge progress={task.progress} />
            </motion.div>
          )}
        </AnimatePresence>

        <div className="relative z-10 space-y-5">
          <BikePicker value={bike} onSelect={setBike} popular={POPULAR_BIKES} />

          {/* Budget */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="label-mono flex items-center gap-1.5">
                <IndianRupee size={11} className="text-brand-orange" aria-hidden="true" /> Budget
              </span>
              <span className="text-sm font-mono font-bold text-brand-orange tabular-nums">
                {budget == null ? 'No limit' : fmtINR(budget)}
              </span>
            </div>
            <input
              type="range"
              min={5000}
              max={2000000}
              step={5000}
              value={budget ?? 2000000}
              onChange={(e) => setBudget(Number(e.target.value))}
              aria-label="Budget in rupees"
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
              <button
                type="button"
                onClick={() => setBudget(OUTLAW_BUDGET)}
                aria-pressed={budget == null}
                className={`px-2.5 py-1 rounded-full text-[11px] font-mono border transition-colors ${
                  budget == null
                    ? 'bg-brand-orange/20 border-brand-orange/50 text-white'
                    : 'bg-white/[0.04] border-white/10 text-white/60 hover:text-white'
                }`}
              >
                Outlaw — no limit
              </button>
            </div>
          </div>

          {/* Goal + profile */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <span className="label-mono block mb-1.5">Goal</span>
              <div className="flex gap-1 bg-white/[0.04] rounded-xl p-1 border border-white/10">
                {GOALS.map(({ id, label, icon: Icon }) => (
                  <button
                    key={id}
                    type="button"
                    onClick={() => setGoal(id)}
                    aria-pressed={goal === id}
                    className={`flex-1 flex items-center justify-center gap-1.5 px-2 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      goal === id ? 'bg-brand-orange text-black shadow-sm' : 'text-white/50 hover:text-white/80'
                    }`}
                  >
                    <Icon size={12} aria-hidden="true" /> {label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label htmlFor="mq-opt-profile" className="label-mono block mb-1.5">Profile</label>
              <div className="relative">
                <Layers size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40 pointer-events-none" aria-hidden="true" />
                <select
                  id="mq-opt-profile"
                  value={profile}
                  onChange={(e) => setProfile(e.target.value)}
                  className="input-base appearance-none pl-9 pr-8 cursor-pointer"
                >
                  {PROFILES.map((p) => (
                    <option key={p.id} value={p.id} className="bg-ink-2">
                      {p.label}
                    </option>
                  ))}
                </select>
                <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 pointer-events-none" aria-hidden="true" />
              </div>
            </div>
          </div>

          {/* Rider weight */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="label-mono block">Rider weight</span>
              <span className="text-sm font-mono text-white/80 tabular-nums">{riderKg} kg</span>
            </div>
            <input
              type="range"
              min={50}
              max={130}
              value={riderKg}
              onChange={(e) => setRiderKg(Number(e.target.value))}
              aria-label="Rider weight in kilograms"
              className="w-full h-1.5 bg-white/10 rounded-full appearance-none cursor-pointer accent-brand-orange"
            />
          </div>

          {task.active && (
            <SimProgress
              active
              progress={task.progress}
              stage={task.stage}
              label="Optimising build"
            />
          )}

          <ActionButton
            task={task}
            onRun={run}
            label={
              <>
                <Wrench size={16} aria-hidden="true" /> Optimise build
              </>
            }
            runningLabel="Optimising"
            disabled={!bike}
            className="w-full"
          />
          {!bike && (
            <p className="text-[11px] text-white/35 font-mono text-center">
              Pick a bike to arm the optimiser.
            </p>
          )}
        </div>
      </div>

      {/* ── Results (right column) ───────────────────────────────────── */}
      <div className="lg:col-span-3 space-y-5">
        {/* Error */}
        <AnimatePresence>
          {task.error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="card border-brand-red/30 bg-brand-red/10 p-3 text-brand-red text-sm flex items-center gap-2"
            >
              <AlertCircle size={16} aria-hidden="true" /> {task.error}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Empty (no parts found) */}
        {noParts && !task.active && (
          <div className="card p-6 text-center">
            <p className="text-white/70 text-sm font-semibold mb-1">No improving parts within budget</p>
            <p className="text-white/40 text-xs">
              Nothing in the {result.profile} catalog improves {result.bike_name} for{' '}
              {fmtINR(result.budget_inr)}. Try raising the budget or widening the profile.
            </p>
          </div>
        )}

        {/* Idle / running placeholder */}
        {!result && !task.error && (
          <div className="card p-8 md:p-10 text-center">
            <Wrench size={22} className="mx-auto text-brand-orange/60 mb-3" aria-hidden="true" />
            <p className="label-mono mb-2">
              {task.active ? 'Optimiser running' : 'Optimiser standing by'}
            </p>
            <p className="text-sm text-white/45 max-w-sm mx-auto">
              {task.active
                ? 'Scoring candidate builds against the physics engine — the best combination lands here.'
                : 'Pick a bike, set a budget, and the knapsack solver returns the fastest legal combination of parts.'}
            </p>
            {task.active && (
              <div className="max-w-xs mx-auto mt-5">
                <SimProgress active progress={task.progress} stage={task.stage} label="Optimising build" />
              </div>
            )}
          </div>
        )}

        {/* Results */}
        <AnimatePresence>
          {result && parts.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: reduce ? 0 : 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: reduce ? 0 : 12 }}
              transition={{ duration: 0.35 }}
              className="space-y-5"
            >
              {/* Header row: bike + scoring chip */}
              <div className="flex items-center justify-between flex-wrap gap-2">
                <h3 className="font-display text-lg font-bold text-white">
                  {result.bike_name}
                  <span className="label-mono ml-2">
                    {result.goal === 'max_trap' ? 'max trap' : 'min ET'} · {result.profile}
                  </span>
                </h3>
                {result.scoring_method && (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-brand-accent/10 border border-brand-accent/30 text-[11px] font-mono text-brand-accent">
                    <Cpu size={11} aria-hidden="true" /> {result.scoring_method}
                    {result.scoring_stats?.out_of_envelope > 0 && (
                      <span className="text-brand-amber/80" title="some candidates fell outside the surrogate envelope">
                        · {result.scoring_stats.out_of_envelope} oob
                      </span>
                    )}
                  </span>
                )}
              </div>

              {/* Before → after */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
                      <span className={trapTone(result.delta_trap_kmh)}>
                        {fmtDelta(result.delta_trap_kmh, 1)}
                      </span>{' '}
                      km/h
                    </>
                  }
                  accent="text-white"
                />
              </div>

              {/* Cost summary — 3-up in the wide column */}
              <div className="grid grid-cols-3 gap-3 md:gap-4">
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
              <div className="card p-5 md:p-6">
                <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
                  <p className="label-mono">
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
                      className="flex items-center justify-between gap-3 px-3 py-2.5 rounded-xl bg-white/[0.03] border border-white/10"
                    >
                      <div className="min-w-0 flex-1">
                        <p className="text-sm text-white font-medium truncate">
                          {partLabel(p.brand, p.name)}
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
                <div className="card border-brand-accent/25 bg-brand-accent/[0.06] p-4 md:p-5">
                  <p className="label-mono flex items-center gap-1.5 !text-brand-accent mb-2.5">
                    <Sparkles size={13} aria-hidden="true" /> Synergies
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
                <div className="card border-brand-amber/25 bg-brand-amber/[0.06] p-4 md:p-5">
                  <p className="label-mono flex items-center gap-1.5 !text-brand-amber mb-2.5">
                    <AlertTriangle size={13} aria-hidden="true" /> Warnings
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
                <div className="card p-4 md:p-5">
                  <p className="label-mono flex items-center gap-1.5 mb-2.5">
                    <ArrowRight size={13} className="text-brand-orange" aria-hidden="true" /> Next upgrade (beyond budget)
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
                      {/* marginal_et_gain_s is a positive-good GAIN on the
                          wire; render as the resulting ET change (−) so every
                          ET number on the page reads the same direction. */}
                      <p className={`text-[11px] font-mono tabular-nums ${deltaTone(-result.next_upgrade.marginal_et_gain_s)}`}>
                        {fmtDelta(-result.next_upgrade.marginal_et_gain_s, 3)}s
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Category priority */}
              {Array.isArray(result.category_priority) && result.category_priority.length > 0 && (
                <div className="card p-5 md:p-6">
                  <p className="label-mono flex items-center gap-1.5 mb-3">
                    <Gauge size={13} className="text-brand-orange" aria-hidden="true" /> Where the gains are
                  </p>
                  <div className="space-y-1.5">
                    {result.category_priority.slice(0, 6).map((c, i) => (
                      <div key={i} className="flex items-center justify-between gap-3 text-sm">
                        <span className="text-white/80 capitalize truncate">
                          {String(c.category || '').replace(/_/g, ' ')}
                        </span>
                        <span className="font-mono text-white/50 shrink-0 tabular-nums text-xs">
                          best {fmtDelta(c.best_et_gain_s != null ? -c.best_et_gain_s : null, 3)}s
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
    </div>
  );
}
