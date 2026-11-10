'use client';

/**
 * BuildOptimizer — "Best parts for your budget" (CLARITY v6).
 *
 * Pick a bike, set a budget, say what kind of build you want, press
 * "Find the best parts". Calls the job-backed POST /api/jobs/optimize (sync
 * fallback in lib/api.js) and explains the answer in plain words: one
 * sentence, before/after tiles, the parts sorted best value first, plain
 * warnings, and what to buy next.
 *
 * Request shape is unchanged: { bike_id, budget_inr (null = no limit), goal,
 * profile, rider_weight_kg, venue_id? }. Profiles are the real API values:
 * all | street_legal | drag_prep | full_race.
 *
 * ?bike_id= deep link preselects the bike (guarded window read, NOT
 * useSearchParams, so the page keeps prerendering).
 */

import { useEffect, useMemo, useRef, useState } from 'react';
import { Wrench, Gauge, SlidersHorizontal, Share2, Beaker, Check } from 'lucide-react';
import { API_URL, optimizeBuildJob, partLabel } from '../lib/api';
import useAsyncTask from '../lib/useAsyncTask';
import ActionButton from './ActionButton';
import SimProgress from './SimProgress';
import BikePicker from './BikePicker';
import LocationPicker from './LocationPicker';
import ConditionsLine, { DEFAULT_ALTITUDE_M, DEFAULT_TEMP_C } from './ConditionsLine';
import Term from './Term';
import NextSteps from './NextSteps';
import {
  Step,
  MoreOptions,
  ManualConditions,
  EMPTY_MANUAL,
  manualStates,
  conditionsBody,
  RangeField,
  Segmented,
  ErrorCard,
  fmtINR,
  fmtSecs,
  describeTimeChange,
  TONE_TEXT,
} from './tools/ToolBits';

// ─── options ────────────────────────────────────────────────────────────────
// Labels map onto the REAL API profile values — do not invent new ones.
const PROFILES = [
  { id: 'street_legal', label: 'Street legal', hint: 'Parts you can run on the road.' },
  { id: 'drag_prep', label: 'Drag-strip prep', hint: 'Bolt-ons and strip rubber.' },
  { id: 'full_race', label: 'Full race', hint: 'Everything, including nitrous and boost.' },
  { id: 'all', label: 'Anything goes', hint: 'No restrictions at all.' },
];
const PROFILE_LABEL = Object.fromEntries(PROFILES.map((p) => [p.id, p.label]));

const GOALS = [
  { id: 'min_et', label: 'Quickest time' },
  { id: 'max_trap', label: 'Highest finish speed' },
];

const BUDGET_PRESETS = [
  { label: '₹25,000', value: 25000 },
  { label: '₹50,000', value: 50000 },
  { label: '₹1,00,000', value: 100000 },
  { label: '₹2,00,000', value: 200000 },
];
// "No limit" — POST budget_inr: null (the API resolves null/0 to its ₹5M
// internal ceiling = effectively no limit). null in component state; the
// slider shows full-right while unlimited.
const NO_LIMIT = null;
const SLIDER_MAX = 2000000;

const SEVERITY_WORDS = { info: 'Note', warning: 'Heads up', critical: 'Important' };

// What the server uses when no place is chosen (stated before a run; after a
// run the server's echoed conditions block is shown instead).
const DEFAULT_CONDITIONS = `the default conditions (${DEFAULT_ALTITUDE_M} m altitude, ${DEFAULT_TEMP_C} °C)`;

const plainCategory = (s) => String(s || '').replace(/_/g, ' ');

// ─── pieces ─────────────────────────────────────────────────────────────────
function Tile({ title, time, trap, accent = false, change = null, trapChange = null }) {
  return (
    <div className={`rounded-xl border p-4 ${accent ? 'border-accent/50 bg-accent/[0.06]' : 'border-white/10 bg-white/[0.03]'}`}>
      <p className="text-sm font-medium text-white/70">{title}</p>
      <p className={`mt-1 font-display text-4xl font-bold tabular-nums md:text-5xl ${accent ? 'text-accent' : 'text-white'}`}>
        {time}
        <span className="ml-1 text-base font-medium text-white/60">s</span>
      </p>
      {change && (
        <p className={`mt-1 text-sm font-semibold ${TONE_TEXT[change.tone]}`}>{change.text}</p>
      )}
      {trap != null && (
        <p className="mt-2 text-sm text-white/70">
          <Term k="trap">Finish-line speed</Term>{' '}
          <span className="font-mono tabular-nums text-white">{trap} km/h</span>
          {trapChange && (
            <span className={`block font-semibold ${TONE_TEXT[trapChange.tone]}`}>{trapChange.text}</span>
          )}
        </p>
      )}
    </div>
  );
}

function trapChangeOf(delta) {
  if (delta == null || !Number.isFinite(Number(delta))) return null;
  const v = Number(delta);
  if (Math.abs(v) < 0.05) return null;
  return v > 0
    ? { text: `${v.toFixed(1)} km/h faster`, tone: 'go' }
    : { text: `${Math.abs(v).toFixed(1)} km/h slower`, tone: 'foul' };
}

function scoringNote(result) {
  const m = String(result.scoring_method || '');
  const oob = result.scoring_stats?.out_of_envelope || 0;
  if (!m || m === 'full_sim') {
    return (
      <>
        Every part was tested with the <Term k="full_sim">full simulation</Term>.
      </>
    );
  }
  return (
    <>
      Most parts were scored with the <Term k="instant_estimate">instant model</Term> (fast and close, not exact)
      {m.includes('fallback') || oob > 0 ? ' and the rest with the full simulation' : ''}.
    </>
  );
}

// ─── main ─────────────────────────────────────────────────────────────────────
export default function BuildOptimizer() {
  const [bike, setBike] = useState(null);
  const [budget, setBudget] = useState(100000);
  const [goal, setGoal] = useState('min_et');
  const [profile, setProfile] = useState('all');
  const [riderKg, setRiderKg] = useState(75);
  const [location, setLocation] = useState(null);
  const [stopped, setStopped] = useState(false);
  const [copied, setCopied] = useState(false);
  const [forceMore, setForceMore] = useState(false);
  // What the last run was actually started with (the inputs may change after).
  const [ran, setRan] = useState(null);
  const resultRef = useRef(null);
  const moreRef = useRef(null);

  const [manual, setManual] = useState(EMPTY_MANUAL);
  const fieldStates = manualStates(manual);

  // Job-backed run — useAsyncTask owns AbortController + progress + error;
  // optimizeBuildJob polls /api/jobs with real candidate-scoring % and
  // cancels the job server-side when the signal aborts (Stop).
  const task = useAsyncTask(async (signal, onProgress) => {
    if (!bike) throw new Error('Choose a bike first.');
    return optimizeBuildJob(
      {
        bike_id: bike.id,
        budget_inr: budget,
        goal,
        profile,
        rider_weight_kg: riderKg,
        // A seeded track, any other place by name, and/or hand-set values —
        // the same fields (and meaning) as Race-day setup.
        ...conditionsBody(location, fieldStates),
      },
      onProgress,
      signal,
    );
  });

  // Preselect a bike from ?bike_id (deep link from /bikes/[id]).
  useEffect(() => {
    if (typeof window === 'undefined') return undefined;
    const raw = new URLSearchParams(window.location.search).get('bike_id');
    const id = raw != null ? Number(raw) : NaN;
    if (!Number.isInteger(id) || id <= 0) return undefined;
    let cancelled = false;
    fetch(`${API_URL}/api/bikes/${id}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((b) => {
        if (!cancelled && b && b.id != null) {
          setBike({
            id: b.id,
            manufacturer: b.manufacturer,
            model: b.model,
            displacement_cc: b.displacement_cc,
            peak_power_hp: b.peak_power_hp,
          });
        }
      })
      .catch(() => {}); // bad id / offline → leave the picker empty
    return () => {
      cancelled = true;
    };
  }, []);

  const run = () => {
    setStopped(false);
    setCopied(false);
    setRan({
      bike,
      budget,
      goal,
      profile,
      riderKg,
      venue: location && location.matched_venue_id != null ? location : null,
      label: location
        ? location.venue_name || location.location_name || location._label || null
        : null,
    });
    task.reset(); // clear the previous result + error before a fresh run
    task.run();
  };

  const stoppableTask = useMemo(
    () => ({
      ...task,
      stop: () => {
        setStopped(true);
        task.stop();
      },
    }),
    [task],
  );

  const result = task.result;
  const parts = useMemo(() => {
    const list = [...(result?.parts || [])];
    // Best value first: lowest rupees per tenth, unknowns last, then biggest gain.
    list.sort((a, b) => {
      const ca = a.cost_per_tenth_inr;
      const cb = b.cost_per_tenth_inr;
      const fa = ca != null && Number.isFinite(ca);
      const fb = cb != null && Number.isFinite(cb);
      if (fa && fb && ca !== cb) return ca - cb;
      if (fa !== fb) return fa ? -1 : 1;
      return (a.delta_et_s ?? 0) - (b.delta_et_s ?? 0);
    });
    return list;
  }, [result]);
  const synergies = result?.synergies || [];
  const warnings = result?.warnings || [];
  const noParts = !!result && parts.length === 0;

  // On phones the result lands below the button — bring it into view.
  useEffect(() => {
    if (!result || !resultRef.current) return;
    if (window.matchMedia && window.matchMedia('(min-width: 1024px)').matches) return;
    const calm = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    resultRef.current.scrollIntoView({ behavior: calm ? 'auto' : 'smooth', block: 'start' });
  }, [result]);

  const openMoreOptions = () => {
    setForceMore(true);
    requestAnimationFrame(() =>
      moreRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' }),
    );
  };

  // ── derived result text ──
  const rBudgetText = ran?.budget == null ? 'no limit' : fmtINR(ran.budget);
  let sentence = null;
  if (result && parts.length > 0 && result.base_et_s != null && result.optimized_et_s != null) {
    const change = describeTimeChange(result.delta_et_s);
    const spend = fmtINR(result.total_cost_inr);
    const n = parts.length;
    const partsWord = `${n} ${n === 1 ? 'part' : 'parts'}`;
    if (result.goal === 'max_trap') {
      const tc = trapChangeOf(result.delta_trap_kmh);
      sentence = (
        <>
          Spend <strong className="font-semibold text-white">{spend}</strong> on {partsWord}:{' '}
          finish-line speed {Number(result.base_trap_kmh).toFixed(0)} →{' '}
          {Number(result.optimized_trap_kmh).toFixed(0)} km/h
          {tc ? `, ${tc.text}` : ''}. Quarter-mile time {fmtSecs(result.base_et_s)} s →{' '}
          {fmtSecs(result.optimized_et_s)} s{change && change.tone !== 'flat' ? `, ${change.text}` : ''}.
        </>
      );
    } else {
      sentence = (
        <>
          Spend <strong className="font-semibold text-white">{spend}</strong> on {partsWord}:{' '}
          {fmtSecs(result.base_et_s)} s → {fmtSecs(result.optimized_et_s)} s
          {change ? (change.tone === 'flat' ? ', no change' : `, ${change.text}`) : ''}.
        </>
      );
    }
  }

  const simHref = (() => {
    if (!result || !ran?.bike || parts.length === 0) return null;
    const q = new URLSearchParams();
    q.set('bike', String(ran.bike.id));
    q.set('parts', parts.map((p) => p.part_id).join(','));
    if (ran.venue?.matched_venue_id != null) q.set('venue', String(ran.venue.matched_venue_id));
    if (ran.riderKg !== 75) q.set('rider', String(ran.riderKg));
    return `/simulator?${q.toString()}`;
  })();

  const copyLink = async () => {
    if (!simHref) return;
    const url = `${window.location.origin}${simHref}`;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      window.prompt('Copy this link', url);
    }
  };

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] lg:items-start">
      {/* ── Inputs ─────────────────────────────────────────────────────── */}
      <div className="space-y-4">
        <Step n={1} title="Choose your bike">
          <BikePicker value={bike} onSelect={setBike} popular />
        </Step>

        <Step n={2} title="Set your budget">
          <p className="font-display text-3xl font-bold tabular-nums text-white" aria-live="polite">
            {budget == null ? 'No limit' : fmtINR(budget)}
          </p>
          <div className="mt-2">
            <label htmlFor="mq-opt-budget" className="sr-only">
              Budget in rupees
            </label>
            <input
              id="mq-opt-budget"
              type="range"
              min={5000}
              max={SLIDER_MAX}
              step={5000}
              value={budget ?? SLIDER_MAX}
              onChange={(e) => setBudget(Number(e.target.value))}
              aria-valuetext={budget == null ? 'No limit' : fmtINR(budget)}
              className="h-11 w-full cursor-pointer accent-accent"
            />
          </div>
          <div className="mt-1 flex flex-wrap gap-2" role="group" aria-label="Budget presets">
            {BUDGET_PRESETS.map((b) => (
              <button
                key={b.value}
                type="button"
                onClick={() => setBudget(b.value)}
                aria-pressed={budget === b.value}
                className={`inline-flex min-h-[44px] items-center rounded-full border px-4 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/70 ${
                  budget === b.value
                    ? 'border-accent bg-accent/10 text-accent'
                    : 'border-white/15 text-white/80 hover:border-accent/60 hover:text-white'
                }`}
              >
                {b.label}
              </button>
            ))}
            <button
              type="button"
              onClick={() => setBudget(NO_LIMIT)}
              aria-pressed={budget == null}
              className={`inline-flex min-h-[44px] items-center rounded-full border px-4 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/70 ${
                budget == null
                  ? 'border-accent bg-accent/10 text-accent'
                  : 'border-white/15 text-white/80 hover:border-accent/60 hover:text-white'
              }`}
            >
              No limit
            </button>
          </div>
          {budget == null && (
            <p className="field-hint">
              <Term k="outlaw">Outlaw-style build</Term>: we pick the quickest combination whatever it costs.
            </p>
          )}
        </Step>

        <Step n={3} title="What kind of build?">
          <fieldset>
            <legend className="sr-only">Build type</legend>
            <div className="grid gap-2 sm:grid-cols-2">
              {PROFILES.map((p) => {
                const on = profile === p.id;
                return (
                  <label
                    key={p.id}
                    className={`relative flex min-h-[64px] cursor-pointer flex-col justify-center rounded-xl border px-4 py-3 transition-colors focus-within:ring-2 focus-within:ring-accent/70 ${
                      on
                        ? 'border-accent bg-accent/[0.08]'
                        : 'border-white/15 hover:border-white/30'
                    }`}
                  >
                    <input
                      type="radio"
                      name="mq-opt-profile"
                      value={p.id}
                      checked={on}
                      onChange={() => setProfile(p.id)}
                      className="peer sr-only"
                    />
                    <span className="flex items-center justify-between gap-2 font-display text-base font-semibold text-white">
                      {p.label}
                      {on && <Check size={16} className="text-accent" aria-hidden="true" />}
                    </span>
                    <span className="mt-0.5 text-sm text-white/65">{p.hint}</span>
                  </label>
                );
              })}
            </div>
            <p className="field-hint">
              <Term k="build_profile">What do these mean?</Term>
            </p>
          </fieldset>
        </Step>

        <div ref={moreRef} id="mq-opt-where" className="card card-pad scroll-mt-24">
          <MoreOptions storageKey="mq-opt-more" label="More options" forceOpen={forceMore}>
            <Segmented
              idPrefix="mq-opt-goal"
              label="What matters most?"
              options={GOALS}
              value={goal}
              onChange={setGoal}
            />
            <div>
              <span className="field-label">Where are you racing? (optional)</span>
              <LocationPicker
                value={location}
                onResolved={setLocation}
                onCleared={() => setLocation(null)}
                compact
              />
              <p className="field-hint">
                Adjusts for altitude and weather. Without a choice we use {DEFAULT_CONDITIONS}.
              </p>
              <div className="mt-3">
                <ManualConditions idPrefix="mq-opt-manual" storageKey="mq-opt-manual" manual={manual} setManual={setManual} />
              </div>
            </div>
            <RangeField
              id="mq-opt-rider"
              label="Rider weight with gear"
              valueText={`${riderKg} kg`}
              min={50}
              max={130}
              value={riderKg}
              onChange={setRiderKg}
            />
          </MoreOptions>
        </div>

        <div>
          <ActionButton
            task={stoppableTask}
            onRun={run}
            label={
              <>
                <Wrench size={18} aria-hidden="true" /> Find the best parts
              </>
            }
            runningLabel="Testing parts"
            disabled={!bike}
            className="w-full"
          />
          {!bike && !task.active && (
            <p className="field-hint text-center">Choose a bike above to get started.</p>
          )}
          {task.active && (
            <div className="mt-3" aria-live="polite">
              <SimProgress
                active
                progress={task.progress}
                stage={task.stage}
                label="Testing every compatible part"
              />
              <p className="field-hint text-center">
                This can take up to a minute or two. You can stop at any time.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* ── Results ────────────────────────────────────────────────────── */}
      <div ref={resultRef} className="scroll-mt-24 space-y-4" aria-live="polite">
        {task.error && <ErrorCard message={task.error} onRetry={bike ? run : undefined} />}

        {!result && !task.error && !task.active && (
          <div className="card card-pad">
            <h2 className="font-display text-lg font-semibold text-white">
              {stopped ? 'Stopped' : 'Your result will appear here'}
            </h2>
            <p className="mt-1 text-sm text-white/70">
              {stopped
                ? 'The search was stopped. Change anything you like and press Find the best parts again.'
                : "We'll show the parts to buy, what each one costs and how much quicker they make your bike."}
            </p>
          </div>
        )}

        {noParts && !task.active && (
          <div className="card card-pad">
            <h2 className="font-display text-lg font-semibold text-white">
              No parts would help within {rBudgetText}
            </h2>
            <p className="mt-1 text-sm text-white/70">
              Nothing in the {PROFILE_LABEL[result.profile] || 'selected'} group makes the{' '}
              {result.bike_name} quicker at {fmtINR(result.budget_inr) || 'this budget'}. Try a bigger budget or
              a wider build type such as &quot;Anything goes&quot;.
            </p>
          </div>
        )}

        {result && parts.length > 0 && (
          <>
            {/* The answer, in a sentence */}
            <section className="card card-pad" aria-label="Result">
              <p className="eyebrow mb-2">{result.bike_name}</p>
              <p className="font-display text-xl font-semibold leading-snug text-white md:text-2xl">
                {sentence}
              </p>
              <p className="mt-3 text-sm text-white/65">
                Build type: {PROFILE_LABEL[result.profile] || result.profile} · Goal:{' '}
                {result.goal === 'max_trap' ? 'highest finish speed' : 'quickest time'} · Rider:{' '}
                {ran?.riderKg ?? riderKg} kg
              </p>
              <ConditionsLine
                className="mt-1 text-sm text-white/65"
                env={result.environment}
                placeLabel={ran?.label}
                onChange={openMoreOptions}
              />

              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                <Tile
                  title="Stock"
                  time={fmtSecs(result.base_et_s, 3)}
                  trap={result.base_trap_kmh != null ? Number(result.base_trap_kmh).toFixed(0) : null}
                />
                <Tile
                  accent
                  title="With these parts"
                  time={fmtSecs(result.optimized_et_s, 3)}
                  change={describeTimeChange(result.delta_et_s, 3)}
                  trap={result.optimized_trap_kmh != null ? Number(result.optimized_trap_kmh).toFixed(0) : null}
                  trapChange={trapChangeOf(result.delta_trap_kmh)}
                />
              </div>
            </section>

            {/* Parts list */}
            <section className="card card-pad" aria-labelledby="mq-opt-parts-h">
              <h2 id="mq-opt-parts-h" className="font-display text-lg font-semibold text-white">
                Parts to buy ({parts.length})
              </h2>
              <p className="mt-1 text-sm text-white/65">
                Best value first. Value is measured as rupees per tenth of a second (
                <Term k="cost_per_tenth">cost per tenth</Term>) — lower is better.
              </p>
              <ul className="mt-3 divide-y divide-white/[0.08]">
                {parts.map((p) => {
                  const change =
                    result.goal === 'max_trap' && p.delta_trap_ms != null
                      ? (() => {
                          const kmh = Number(p.delta_trap_ms) * 3.6;
                          if (Math.abs(kmh) < 0.05) return describeTimeChange(p.delta_et_s);
                          return kmh > 0
                            ? { text: `${kmh.toFixed(1)} km/h faster`, tone: 'go' }
                            : { text: `${Math.abs(kmh).toFixed(1)} km/h slower`, tone: 'foul' };
                        })()
                      : describeTimeChange(p.delta_et_s);
                  return (
                    <li key={p.part_id} className="flex items-start justify-between gap-4 py-3">
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-white">{partLabel(p.brand, p.name)}</p>
                        <p className="mt-0.5 text-xs capitalize text-white/60">
                          {plainCategory(p.category_display || p.category)}
                          {p.cost_per_tenth_inr != null && Number.isFinite(p.cost_per_tenth_inr) && (
                            <span className="normal-case">
                              {' '}
                              · {fmtINR(p.cost_per_tenth_inr)} per 0.1 s
                            </span>
                          )}
                        </p>
                        {p.is_compatible === false && (
                          <p className="mt-1 text-xs font-medium text-signal-stage">
                            May not fit this bike — check before buying.
                          </p>
                        )}
                      </div>
                      <div className="shrink-0 text-right">
                        <p className="font-mono text-sm font-medium tabular-nums text-white">
                          {fmtINR(p.price_inr)}
                        </p>
                        {change && (
                          <p className={`mt-0.5 text-xs font-semibold ${TONE_TEXT[change.tone]}`}>
                            {change.text}
                          </p>
                        )}
                      </div>
                    </li>
                  );
                })}
              </ul>

              <div className="mt-2 border-t border-white/10 pt-1">
                <div className="stat-row">
                  <span>Total cost</span>
                  <span>{fmtINR(result.total_cost_inr)}</span>
                </div>
                {ran?.budget != null && result.budget_used_pct != null && (
                  <div className="stat-row">
                    <span>Budget used</span>
                    <span>{Number(result.budget_used_pct).toFixed(0)} %</span>
                  </div>
                )}
                {result.cost_per_tenth_inr != null && Number.isFinite(result.cost_per_tenth_inr) && (
                  <div className="stat-row">
                    <span>
                      <Term k="cost_per_tenth">Cost per tenth of a second</Term>, whole build
                    </span>
                    <span>{fmtINR(result.cost_per_tenth_inr)}</span>
                  </div>
                )}
              </div>
              <p className="mt-2 text-xs text-white/60">
                We tested {result.parts_evaluated ?? parts.length} parts
                {result.parts_skipped_incompatible
                  ? `; ${result.parts_skipped_incompatible} don't fit this bike`
                  : ''}
                {result.parts_skipped_no_gain
                  ? `; ${result.parts_skipped_no_gain} wouldn't make it quicker`
                  : ''}
                .
              </p>
            </section>

            {synergies.length > 0 && (
              <section className="card card-pad" aria-labelledby="mq-opt-syn-h">
                <h2 id="mq-opt-syn-h" className="font-display text-lg font-semibold text-white">
                  Parts that work well together
                </h2>
                <ul className="mt-2 space-y-2">
                  {synergies.map((s, i) => (
                    <li
                      key={i}
                      className="text-sm text-white/80"
                      title={s.multiplier != null ? `Combined effect ×${Number(s.multiplier).toFixed(2)}` : undefined}
                    >
                      {s.description}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {warnings.length > 0 && (
              <section className="card card-pad" aria-labelledby="mq-opt-warn-h">
                <h2 id="mq-opt-warn-h" className="font-display text-lg font-semibold text-white">
                  Things to check
                </h2>
                <ul className="mt-2 space-y-2.5">
                  {warnings.map((w, i) => (
                    <li key={i} className="flex items-start gap-2.5 text-sm text-white/80">
                      <span
                        className={`chip shrink-0 ${
                          w.severity === 'critical' ? 'chip-foul' : 'chip-stage'
                        }`}
                      >
                        {SEVERITY_WORDS[w.severity] || 'Note'}
                      </span>
                      <span>{w.message}</span>
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {result.next_upgrade?.part && (
              <section className="card card-pad" aria-labelledby="mq-opt-next-h">
                <h2 id="mq-opt-next-h" className="font-display text-lg font-semibold text-white">
                  If you have more to spend
                </h2>
                <div className="mt-2 flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-white">
                      {partLabel(result.next_upgrade.part.brand, result.next_upgrade.part.name)}
                    </p>
                    {result.next_upgrade.reason && (
                      <p className="mt-0.5 text-sm text-white/65">{result.next_upgrade.reason}</p>
                    )}
                  </div>
                  <div className="shrink-0 text-right">
                    {result.next_upgrade.marginal_cost_inr != null && (
                      <p className="font-mono text-sm font-medium tabular-nums text-white">
                        +{fmtINR(result.next_upgrade.marginal_cost_inr)}
                      </p>
                    )}
                    {result.next_upgrade.marginal_et_gain_s != null && (
                      // marginal_et_gain_s is a positive-good GAIN on the wire.
                      <p className="mt-0.5 text-xs font-semibold text-signal-go">
                        {describeTimeChange(-result.next_upgrade.marginal_et_gain_s)?.text}
                      </p>
                    )}
                  </div>
                </div>
              </section>
            )}

            {Array.isArray(result.category_priority) && result.category_priority.length > 0 && (
              <details className="card card-pad group">
                <summary className="flex min-h-[44px] cursor-pointer list-none items-center justify-between font-display text-lg font-semibold text-white">
                  Which kinds of parts help most
                  <span className="text-sm font-medium text-accent group-open:hidden">Show</span>
                  <span className="hidden text-sm font-medium text-accent group-open:inline">Hide</span>
                </summary>
                <ul className="mt-2 divide-y divide-white/[0.08]">
                  {result.category_priority.slice(0, 6).map((c, i) => {
                    const ch = c.best_et_gain_s != null ? describeTimeChange(-c.best_et_gain_s) : null;
                    return (
                      <li key={i} className="flex items-baseline justify-between gap-3 py-2.5 text-sm">
                        <span className="capitalize text-white/85">{plainCategory(c.category)}</span>
                        <span className="text-right text-white/65">
                          {ch && <span className={`font-semibold ${TONE_TEXT[ch.tone]}`}>best: {ch.text}</span>}
                          {c.avg_cost_per_tenth != null && Number.isFinite(c.avg_cost_per_tenth) && (
                            <span> · about {fmtINR(c.avg_cost_per_tenth)} per 0.1 s</span>
                          )}
                        </span>
                      </li>
                    );
                  })}
                </ul>
              </details>
            )}

            <p className="flex items-start gap-2 px-1 text-xs text-white/60">
              <Gauge size={14} className="mt-0.5 shrink-0" aria-hidden="true" />
              <span>
                {scoringNote(result)} These are predictions from a physics model, not a guarantee — real
                results depend on tuning, tyres and the day.
              </span>
            </p>

            <NextSteps
              items={[
                simHref && {
                  icon: Beaker,
                  title: 'Try these parts in the simulator',
                  hint: 'Opens the simulator with this exact set of parts.',
                  href: simHref,
                },
                ran?.bike && {
                  icon: SlidersHorizontal,
                  title: 'Get a race-day setup for this bike',
                  hint: 'Gearing and tyre pressure for the day you race.',
                  href: `/autotune?bike_id=${ran.bike.id}`,
                },
                simHref && {
                  icon: Share2,
                  title: copied ? 'Link copied' : 'Copy a link to this build',
                  hint: 'Send it to a friend or your tuner.',
                  onClick: copyLink,
                },
              ].filter(Boolean)}
            />
          </>
        )}
      </div>
    </div>
  );
}
