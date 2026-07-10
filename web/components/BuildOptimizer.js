'use client';

/**
 * BuildOptimizer — budget-constrained parts build optimiser (STAGED v4).
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
 * FUNCTION IS FROZEN (v4 is a re-skin): job wrapper via useAsyncTask +
 * ActionButton (real % in the button, Stop always live), the ?bike_id
 * deep-link preselect reads window.location post-mount (NOT
 * useSearchParams) so the page keeps static-prerendering without a
 * Suspense boundary. v4 layout: input card stack left, one timeslip-style
 * results card right (lg:grid-cols-[0.9fr_1.1fr]).
 */

import { useEffect, useState } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import {
  Wrench, AlertCircle, ChevronDown, TrendingDown, TrendingUp, Cpu,
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
// dropped) = good = signal-go. Trap deltas read the opposite way
// (positive = faster = green).
const deltaTone = (n) =>
  n == null || Number(n) === 0
    ? 'font-mono tabular-nums text-white/50'
    : Number(n) < 0
      ? 'delta-down'
      : 'delta-up';
const deltaChip = (n) =>
  n == null || Number(n) === 0 ? 'chip' : Number(n) < 0 ? 'chip chip-go' : 'chip chip-foul';
const trapTone = (n) =>
  n == null || Number(n) === 0
    ? 'text-white/50'
    : Number(n) > 0
      ? 'text-signal-go'
      : 'text-signal-foul';

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

const BUDGET_PRESETS = [
  { label: '₹50K', value: 50000 },
  { label: '₹1.5L', value: 150000 },
  { label: '₹5L', value: 500000 },
];
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
    <div className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
      {/* ── Inputs (left column) ─────────────────────────────────────── */}
      <div className="relative space-y-4">
        <AnimatePresence>
          {task.active && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute -top-1 left-1 right-1 z-20"
            >
              <SimProgress active edge progress={task.progress} />
            </motion.div>
          )}
        </AnimatePresence>

        <div className="card p-5 md:p-6">
          <BikePicker value={bike} onSelect={setBike} popular={POPULAR_BIKES} />
        </div>

        {/* Budget */}
        <div className="card p-5 md:p-6">
          <span className="label-mono block mb-2">Budget</span>
          <p className="font-mono text-2xl font-bold text-white tabular-nums mb-3">
            {budget == null ? 'No limit' : fmtINR(budget)}
          </p>
          <input
            type="range"
            min={5000}
            max={2000000}
            step={5000}
            value={budget ?? 2000000}
            onChange={(e) => setBudget(Number(e.target.value))}
            aria-label="Budget in rupees"
            className="w-full h-1.5 bg-asphalt-4 rounded-full appearance-none cursor-pointer accent-accent"
          />
          <div className="flex flex-wrap gap-2 mt-3">
            {BUDGET_PRESETS.map((b) => (
              <button
                key={b.value}
                type="button"
                onClick={() => setBudget(b.value)}
                aria-pressed={budget === b.value}
                className={`chip h-9 px-3 transition-colors cursor-pointer ${
                  budget === b.value ? 'chip-volt' : 'hover:border-white/30 hover:text-white'
                }`}
              >
                {b.label}
              </button>
            ))}
            <button
              type="button"
              onClick={() => setBudget(OUTLAW_BUDGET)}
              aria-pressed={budget == null}
              className={`chip h-9 px-3 transition-colors cursor-pointer ${
                budget == null ? 'chip-volt' : 'hover:border-white/30 hover:text-white'
              }`}
            >
              Outlaw — no limit
            </button>
          </div>
        </div>

        {/* Goal + profile + rider */}
        <div className="card p-5 md:p-6 space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <span className="label-mono block mb-1.5">Goal</span>
              <div className="flex gap-1 rounded-lg border border-white/10 bg-asphalt-3/60 p-1">
                {GOALS.map(({ id, label, icon: Icon }) => (
                  <button
                    key={id}
                    type="button"
                    onClick={() => setGoal(id)}
                    aria-pressed={goal === id}
                    className={`flex-1 flex items-center justify-center gap-1.5 px-2 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                      goal === id ? 'bg-white/10 text-white' : 'text-white/50 hover:text-white/80'
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
                <select
                  id="mq-opt-profile"
                  value={profile}
                  onChange={(e) => setProfile(e.target.value)}
                  className="input-base appearance-none pr-8 cursor-pointer"
                >
                  {PROFILES.map((p) => (
                    <option key={p.id} value={p.id} className="bg-asphalt-2">
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
              className="w-full h-1.5 bg-asphalt-4 rounded-full appearance-none cursor-pointer accent-accent"
            />
          </div>
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
          <p className="text-[11px] text-white/40 font-mono text-center">
            Pick a bike to arm the optimiser.
          </p>
        )}
      </div>

      {/* ── Results (right column) ───────────────────────────────────── */}
      <div className="space-y-4">
        {/* Error */}
        <AnimatePresence>
          {task.error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="card border-signal-foul/30 bg-signal-foul/10 p-3 text-signal-foul text-sm flex items-center gap-2"
            >
              <AlertCircle size={16} aria-hidden="true" /> {task.error}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Empty (no parts found) */}
        {noParts && !task.active && (
          <div className="card p-6 text-center">
            <p className="text-white/80 text-sm font-semibold mb-1">No improving parts within budget</p>
            <p className="text-white/40 text-xs">
              Nothing in the {result.profile} catalog improves {result.bike_name} for{' '}
              {fmtINR(result.budget_inr)}. Try raising the budget or widening the profile.
            </p>
          </div>
        )}

        {/* Idle / running placeholder */}
        {!result && !task.error && (
          <div className="card p-8 md:p-10 text-center">
            <Wrench size={22} className="mx-auto text-white/30 mb-3" aria-hidden="true" />
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
              className="space-y-4"
            >
              {/* Header row: bike + scoring chip */}
              <div className="flex items-center justify-between flex-wrap gap-2">
                <h3 className="font-display text-xl md:text-2xl font-semibold uppercase text-white leading-[0.95]">
                  {result.bike_name}
                  <span className="label-mono ml-2">
                    {result.goal === 'max_trap' ? 'max trap' : 'min ET'} · {result.profile}
                  </span>
                </h3>
                {result.scoring_method && (
                  <span className="chip">
                    <Cpu size={10} aria-hidden="true" /> {result.scoring_method}
                    {result.scoring_stats?.out_of_envelope > 0 && (
                      <span className="text-signal-stage" title="some candidates fell outside the surrogate envelope">
                        · {result.scoring_stats.out_of_envelope} oob
                      </span>
                    )}
                  </span>
                )}
              </div>

              {/* The slip — base → optimised + parts + cost */}
              <div className="card p-5 md:p-6">
                <div className="flex items-start justify-between gap-3 flex-wrap">
                  <div className="min-w-0">
                    <p className="label-mono">Base → optimised</p>
                    <p className="font-mono text-3xl md:text-4xl font-bold text-white tabular-nums mt-1.5">
                      {fmtNum(result.base_et_s, 3)} → {fmtNum(result.optimized_et_s, 3)}
                      <span className="text-base text-white/40 ml-1">s</span>
                    </p>
                    <p className="text-xs font-mono text-white/40 tabular-nums mt-1.5">
                      trap {fmtNum(result.base_trap_kmh, 1)} → {fmtNum(result.optimized_trap_kmh, 1)} km/h ·{' '}
                      <span className={trapTone(result.delta_trap_kmh)}>
                        {fmtDelta(result.delta_trap_kmh, 1)}
                      </span>
                    </p>
                  </div>
                  <span className={`${deltaChip(result.delta_et_s)} h-7 px-2.5 text-xs shrink-0`}>
                    {fmtDelta(result.delta_et_s, 3)}s
                  </span>
                </div>

                <div className="centerline my-4" aria-hidden="true" />

                {/* Selected parts — timeslip rows */}
                <div className="flex items-center justify-between flex-wrap gap-2 mb-1">
                  <p className="label-mono">Selected parts ({parts.length})</p>
                  <p className="text-[10px] font-mono text-white/30">
                    {result.parts_evaluated} evaluated
                    {result.parts_skipped_incompatible ? ` · ${result.parts_skipped_incompatible} incompatible` : ''}
                    {result.parts_skipped_no_gain ? ` · ${result.parts_skipped_no_gain} no-gain` : ''}
                  </p>
                </div>
                <div>
                  {parts.map((p) => (
                    <div key={p.part_id} className="timeslip-row gap-3">
                      <span className="min-w-0">
                        <span className="block truncate text-white/85">
                          {partLabel(p.brand, p.name)}
                          {p.is_compatible === false && (
                            <span className="ml-2 text-[10px] uppercase text-signal-stage">incompatible</span>
                          )}
                        </span>
                        <span className="block text-[10px] uppercase tracking-wide text-white/35 mt-0.5">
                          {p.category_display || p.category}
                          {p.cost_per_tenth_inr != null && (
                            <span className="ml-2 text-white/25 normal-case">{fmtINR(p.cost_per_tenth_inr)}/tenth</span>
                          )}
                        </span>
                      </span>
                      <span className="shrink-0 text-right">
                        <span className={deltaTone(p.delta_et_s)}>{fmtDelta(p.delta_et_s, 3)}s</span>
                        <span className="text-white/60"> · {fmtINR(p.price_inr)}</span>
                      </span>
                    </div>
                  ))}
                </div>

                <div className="centerline my-4" aria-hidden="true" />

                {/* Cost summary */}
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <p className="label-mono">Total cost</p>
                    <p className="font-mono text-base md:text-lg font-bold text-white tabular-nums mt-1">
                      {fmtINR(result.total_cost_inr)}
                    </p>
                  </div>
                  <div>
                    <p className="label-mono">Budget used</p>
                    <p className="font-mono text-base md:text-lg font-bold text-white tabular-nums mt-1">
                      {fmtNum(result.budget_used_pct, 0)}%
                    </p>
                  </div>
                  <div>
                    <p className="label-mono">Cost / tenth</p>
                    <p className="font-mono text-base md:text-lg font-bold text-white tabular-nums mt-1">
                      {result.cost_per_tenth_inr == null ? '—' : fmtINR(result.cost_per_tenth_inr)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Synergies */}
              {synergies.length > 0 && (
                <div className="card p-4 md:p-5">
                  <p className="label-mono mb-2.5">Synergies</p>
                  <div className="space-y-1.5">
                    {synergies.map((s, i) => (
                      <div key={i} className="flex items-start justify-between gap-3 text-sm">
                        <span className="text-white/80">{s.description}</span>
                        {s.multiplier != null && (
                          <span className="font-mono text-white/85 shrink-0 tabular-nums">
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
                <div className="card p-4 md:p-5">
                  <p className="label-mono mb-2.5">Warnings</p>
                  <div className="space-y-2">
                    {warnings.map((w, i) => (
                      <p key={i} className="text-sm text-white/80 flex items-start gap-2">
                        <span className="chip chip-stage shrink-0">{w.severity}</span>
                        <span>{w.message}</span>
                      </p>
                    ))}
                  </div>
                </div>
              )}

              {/* Next upgrade */}
              {result.next_upgrade?.part && (
                <div className="card p-4 md:p-5">
                  <p className="label-mono mb-2.5">Next upgrade (beyond budget)</p>
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
                    <div className="text-right shrink-0 font-mono text-sm tabular-nums">
                      <p className="text-white">{fmtINR(result.next_upgrade.marginal_cost_inr)}</p>
                      {/* marginal_et_gain_s is a positive-good GAIN on the
                          wire; render as the resulting ET change (−) so every
                          ET number on the page reads the same direction. */}
                      <p className={`text-[11px] ${deltaTone(-result.next_upgrade.marginal_et_gain_s)}`}>
                        {fmtDelta(-result.next_upgrade.marginal_et_gain_s, 3)}s
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Category priority */}
              {Array.isArray(result.category_priority) && result.category_priority.length > 0 && (
                <div className="card p-4 md:p-5">
                  <p className="label-mono mb-3">Where the gains are</p>
                  <div>
                    {result.category_priority.slice(0, 6).map((c, i) => (
                      <div key={i} className="timeslip-row gap-3">
                        <span className="text-white/80 capitalize truncate">
                          {String(c.category || '').replace(/_/g, ' ')}
                        </span>
                        <span className="text-white/50 shrink-0 tabular-nums text-xs">
                          best{' '}
                          <span className={deltaTone(c.best_et_gain_s != null ? -c.best_et_gain_s : null)}>
                            {fmtDelta(c.best_et_gain_s != null ? -c.best_et_gain_s : null, 3)}s
                          </span>
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
