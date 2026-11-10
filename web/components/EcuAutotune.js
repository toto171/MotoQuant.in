'use client';

/**
 * EcuAutotune — "Race-day setup" (CLARITY v6).
 *
 * Pick a bike, say where you are racing, press "Get my setup". Calls the
 * job-backed POST /api/jobs/autotune (sync fallback in lib/api.js) and
 * explains the answer in plain words: today's air, then one card per
 * recommendation with what to change, from → to, time gained and why.
 *
 * Honesty rules (never present a recommendation with a made-up benefit):
 *  - Gearing is a simulated sweep; its time change is real.
 *  - Launch RPM: when the sweep found NO time change (or the backend marks it
 *    not modelled — `adjustable:false` / `modelled:false` / null rpm), no RPM
 *    to change to is shown; the card says so and de-emphasises itself.
 *  - Tyre pressure and fuel/timing are `is_guideline` → labelled
 *    "General guidance — not simulated for this bike" and de-emphasised.
 *
 * Request shape is unchanged (see lib/api.js autotuneEcuBody). Manual
 * condition inputs are validated + clamped before they enter the body.
 */

import { useEffect, useMemo, useRef, useState } from 'react';
import { Sliders, Cog, Flag, CircleDot, Flame, Zap, Wrench } from 'lucide-react';
import { API_URL, autotuneEcuJob } from '../lib/api';
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
  RangeField,
  ErrorCard,
  ManualConditions,
  EMPTY_MANUAL,
  manualStates,
  conditionsBody,
  describeTimeChange,
  fmtSecs,
} from './tools/ToolBits';

// ─── helpers ────────────────────────────────────────────────────────────────
const fmtNum = (n, d = 1) => (n == null || !Number.isFinite(Number(n)) ? '' : Number(n).toFixed(d));
const fmtInt = (n) =>
  n == null || !Number.isFinite(Number(n)) ? '' : Math.round(Number(n)).toLocaleString('en-IN');
const signed = (n, d = 1) => {
  if (n == null || !Number.isFinite(Number(n))) return '';
  const v = Number(n);
  return `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v).toFixed(d)}`;
};

// What the server uses when no place is chosen (stated before a run, so there
// is no server block to read yet; after a run the echoed block is used).
const DEFAULT_CONDITIONS = `the default conditions (${DEFAULT_ALTITUDE_M} m altitude, ${DEFAULT_TEMP_C} °C)`;
const GUIDANCE_LABEL = 'General guidance: not simulated for this bike';

// ─── result pieces ──────────────────────────────────────────────────────────
function FromTo({ label, from, to, unit }) {
  return (
    <div className="min-w-[88px]">
      <p className="text-xs text-white/60">{label}</p>
      <p className="mt-0.5 font-mono text-lg font-bold tabular-nums text-white">
        {to}
        {unit && <span className="ml-1 text-xs font-medium text-white/60">{unit}</span>}
      </p>
      {from != null && from !== '' && (
        <p className="text-xs text-white/60">
          was <span className="font-mono tabular-nums">{from}</span>
        </p>
      )}
    </div>
  );
}

/**
 * One recommendation. `muted` cards (general guidance / not modelled) get a
 * dashed border and a quieter heading, but their text stays AA-contrast.
 */
function RecCard({ icon: Icon, title, change = null, badge = null, muted = false, children }) {
  return (
    <section
      className={`card card-pad ${muted ? 'border-dashed bg-transparent' : ''}`}
      aria-label={title}
    >
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3
          className={`flex items-center gap-2 font-display text-lg font-semibold ${
            muted ? 'text-white/80' : 'text-white'
          }`}
        >
          {Icon && <Icon size={18} className={muted ? 'text-white/55' : 'text-accent'} aria-hidden="true" />}
          {title}
        </h3>
        {change && (
          <span
            className={`chip h-7 px-2.5 text-sm font-semibold ${
              change.tone === 'go' ? 'chip-go' : change.tone === 'foul' ? 'chip-foul' : ''
            }`}
          >
            {change.text}
          </span>
        )}
        {!change && badge && <span className="chip h-auto py-1 text-xs">{badge}</span>}
      </div>
      {children}
    </section>
  );
}

// ─── main ─────────────────────────────────────────────────────────────────────
export default function EcuAutotune() {
  const [bike, setBike] = useState(null);
  const [location, setLocation] = useState(null);
  const [riderKg, setRiderKg] = useState(75);
  const [stopped, setStopped] = useState(false);
  const [ran, setRan] = useState(null);
  const resultRef = useRef(null);

  // Optional manual conditions (override / supplement the resolved location)
  const [manual, setManual] = useState(EMPTY_MANUAL);

  // Per-field parse/validate state (drives inline hints + the request body)
  const fieldStates = manualStates(manual);

  // Job-backed run — useAsyncTask owns AbortController + progress + error;
  // autotuneEcuJob polls /api/jobs with the real sweep % and cancels the
  // job server-side when the signal aborts (Stop).
  const task = useAsyncTask(async (signal, onProgress) => {
    if (!bike) throw new Error('Choose a bike first.');
    const body = {
      bike_id: bike.id,
      rider_weight_kg: riderKg,
      ...conditionsBody(location, fieldStates),
    };

    return autotuneEcuJob(body, onProgress, signal);
  });

  const run = () => {
    setStopped(false);
    const manualUsed = Object.values(fieldStates).some((f) => f.value != null);
    setRan({
      bike,
      riderKg,
      location,
      manualUsed,
      label: location
        ? location.venue_name || location.location_name || location._label || 'your chosen place'
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
  const env = result?.environment;
  const gearing = result?.gearing;
  const launch = result?.launch_rpm;
  const tyre = result?.tyre_pressure;
  const fuel = result?.fuel_timing;
  const combined = result?.combined;

  // On phones the result lands below the button — bring it into view.
  useEffect(() => {
    if (!result || !resultRef.current) return;
    if (window.matchMedia && window.matchMedia('(min-width: 1024px)').matches) return;
    const calm = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    resultRef.current.scrollIntoView({ behavior: calm ? 'auto' : 'smooth', block: 'start' });
  }, [result]);

  // Preselect a bike from ?bike_id (links from the simulator / bike pages).
  // Guarded window read (not useSearchParams) so the page keeps prerendering.
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
      .catch(() => {}); // bad id / offline: leave the picker empty
    return () => {
      cancelled = true;
    };
  }, []);

  // ── plain-language pieces ──
  let airSentence = null;
  if (env) {
    const loss = Number(env.power_loss_pct);
    if (Number.isFinite(loss)) {
      if (loss >= 1.5) {
        airSentence = `Thin air here costs about ${Math.round(loss)} % of your engine's power.`;
      } else if (loss <= -1.5) {
        airSentence = `Dense air here gives you about ${Math.round(Math.abs(loss))} % more power than standard air.`;
      } else {
        airSentence = "The air here is close to standard, so it barely changes your power.";
      }
    }
  }

  const gearChange = gearing?.adjustable ? describeTimeChange(gearing.delta_et_s) : null;
  const netChange = combined ? describeTimeChange(combined.delta_et_s) : null;
  const netSentence =
    result && combined && result.stock?.et_s != null && combined.et_s != null ? (
      netChange && netChange.tone !== 'flat' ? (
        <>
          With this setup your {result.bike_name} should run the quarter mile in about{' '}
          <strong className="font-semibold text-white">{fmtSecs(combined.et_s)} s</strong> instead of{' '}
          {fmtSecs(result.stock.et_s)} s, {netChange.text}.
        </>
      ) : (
        <>
          Your stock setup is already the quickest we found for these conditions:{' '}
          <strong className="font-semibold text-white">{fmtSecs(result.stock.et_s)} s</strong> for the
          quarter mile.
        </>
      )
    ) : null;

  // Launch RPM honesty: only present a number when the sweep measured a gain.
  const launchModelled =
    launch &&
    launch.adjustable !== false &&
    launch.modelled !== false &&
    launch.recommended_rpm != null;
  const launchChange = launchModelled ? describeTimeChange(launch.delta_et_s) : null;
  const launchHasGain = !!launchChange && launchChange.tone !== 'flat';

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] lg:items-start">
      {/* ── Inputs ─────────────────────────────────────────────────────── */}
      <div className="space-y-4">
        <Step n={1} title="Choose your bike">
          <BikePicker value={bike} onSelect={setBike} popular />
        </Step>

        <Step n={2} id="mq-tune-where" title="Where are you racing?">
          <LocationPicker
            value={location}
            onResolved={setLocation}
            onCleared={() => setLocation(null)}
            compact
          />
          <p className="field-hint">
            Adjusts for altitude and weather. Skip this and we use {DEFAULT_CONDITIONS}.
          </p>

          <div className="mt-3">
            <ManualConditions idPrefix="mq-manual" storageKey="mq-tune-manual" manual={manual} setManual={setManual} />
          </div>
        </Step>

        <Step n={3} title="Rider weight">
          <RangeField
            id="mq-tune-rider"
            label="Rider weight with gear"
            valueText={`${riderKg} kg`}
            min={50}
            max={130}
            value={riderKg}
            onChange={setRiderKg}
          />
        </Step>

        <div>
          <ActionButton
            task={stoppableTask}
            onRun={run}
            label={
              <>
                <Sliders size={18} aria-hidden="true" /> Get my setup
              </>
            }
            runningLabel="Working out your setup"
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
                label="Testing gearing and launch settings"
              />
              <p className="field-hint text-center">You can stop at any time.</p>
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
              {stopped ? 'Stopped' : 'Your setup will appear here'}
            </h2>
            <p className="mt-1 text-sm text-white/70">
              {stopped
                ? 'The run was stopped. Change anything you like and press Get my setup again.'
                : 'You will see how the air changes your power, then gearing, launch RPM, tyre pressure and fuel advice, with the time each one is worth.'}
            </p>
          </div>
        )}

        {result && (
          <>
            {/* Today's air + the headline */}
            <section className="card card-pad" aria-label="Summary">
              <p className="eyebrow mb-2">{result.bike_name}</p>
              {airSentence && (
                <p className="font-display text-xl font-semibold leading-snug text-white md:text-2xl">
                  {airSentence}
                </p>
              )}
              {netSentence && <p className="mt-3 text-base leading-relaxed text-white/80">{netSentence}</p>}
              <ConditionsLine
                className="mt-3 text-sm text-white/65"
                env={env}
                placeLabel={ran?.label}
                onChange={() =>
                  document.getElementById('mq-tune-where')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
                }
              />
              <p className="mt-1 text-sm text-white/65">Rider: {ran?.riderKg ?? riderKg} kg.</p>

              {env && (
                <div className="mt-4 border-t border-white/10 pt-1">
                  <div className="stat-row">
                    <span>Air temperature</span>
                    <span>{fmtNum(env.temperature_c, 1)} °C</span>
                  </div>
                  <div className="stat-row">
                    <span>Humidity</span>
                    <span>{fmtNum(env.humidity_pct, 0)} %</span>
                  </div>
                  <div className="stat-row">
                    <span>Altitude</span>
                    <span>{fmtInt(env.altitude_m)} m</span>
                  </div>
                  <div className="stat-row">
                    <span>
                      <Term k="da">Effective altitude</Term> (what the engine feels)
                    </span>
                    <span>{fmtInt(env.density_altitude_m)} m</span>
                  </div>
                  <div className="stat-row">
                    <span>Air density</span>
                    <span>{fmtNum(env.air_density_kgm3, 3)} kg/m³</span>
                  </div>
                  {env.power_loss_pct != null && (
                    <div className="stat-row">
                      <span>Power compared with standard air</span>
                      <span>{fmtNum(100 - Number(env.power_loss_pct), 0)} %</span>
                    </div>
                  )}
                </div>
              )}
            </section>

            {/* Simulated advice first */}
            {gearing && (
              <RecCard
                icon={Cog}
                title="Gearing (sprockets)"
                change={gearChange && gearChange.tone !== 'flat' ? gearChange : null}
                muted={!gearing.adjustable}
                badge={gearing.adjustable ? (gearChange ? 'No change needed' : null) : 'Not adjustable'}
              >
                {gearing.adjustable ? (
                  gearing.recommended_rear === gearing.stock_rear ? (
                    <p className="text-sm text-white/80">
                      Keep your stock {fmtInt(gearing.stock_front)}/{fmtInt(gearing.stock_rear)} sprockets: we
                      tried bigger and smaller rear sprockets and none was quicker in these conditions.
                    </p>
                  ) : (
                    <>
                      <div className="mb-3 flex flex-wrap gap-x-8 gap-y-3">
                        <FromTo
                          label="Front sprocket (teeth)"
                          to={fmtInt(gearing.recommended_front)}
                          from={
                            gearing.stock_front !== gearing.recommended_front
                              ? fmtInt(gearing.stock_front)
                              : null
                          }
                        />
                        <FromTo
                          label="Rear sprocket (teeth)"
                          to={fmtInt(gearing.recommended_rear)}
                          from={fmtInt(gearing.stock_rear)}
                        />
                      </div>
                      <p className="text-sm text-white/75">
                        {Number(gearing.recommended_rear) > Number(gearing.stock_rear)
                          ? 'A bigger rear sprocket makes the gearing shorter: harder acceleration, a little less top speed. '
                          : 'A smaller rear sprocket makes the gearing taller: a little less punch off the line, more top speed. '}
                        <Term k="gearing">What is gearing?</Term>
                      </p>
                    </>
                  )
                ) : (
                  <p className="text-sm text-white/75">
                    This bike has a {gearing.drive || 'shaft or belt'} final drive, so there are no sprockets to
                    change. Your gearing is fixed.
                  </p>
                )}
              </RecCard>
            )}

            {launch &&
              (!launchModelled ? (
                <RecCard icon={Flag} title="Launch RPM" muted badge="Not modelled">
                  <p className="text-sm text-white/75">
                    {launch.reason || 'Launch RPM isn\u2019t modelled for this bike.'}
                    {launch.stock_rpm != null && (
                      <>
                        {' '}
                        Start from your usual {fmtInt(launch.stock_rpm)} rpm and adjust by feel on the line.
                      </>
                    )}
                  </p>
                </RecCard>
              ) : launchHasGain ? (
                <RecCard icon={Flag} title="Launch RPM" change={launchChange}>
                  <div className="mb-3 flex flex-wrap gap-x-8 gap-y-3">
                    <FromTo
                      label="Launch at"
                      to={fmtInt(launch.recommended_rpm)}
                      unit="rpm"
                      from={launch.stock_rpm != null ? `${fmtInt(launch.stock_rpm)} rpm` : null}
                    />
                  </div>
                  {launch.rationale && <p className="text-sm text-white/75">{launch.rationale}</p>}
                </RecCard>
              ) : (
                <RecCard icon={Flag} title="Launch RPM" muted badge={GUIDANCE_LABEL}>
                  <p className="text-sm text-white/75">
                    In our simulation, changing the <Term k="launch_rpm">launch RPM</Term> made no difference to
                    this bike&apos;s time, so we can&apos;t give you a number with a measured
                    benefit.
                    {launch.stock_rpm != null && (
                      <>
                        {' '}
                        Start from your usual {fmtInt(launch.stock_rpm)} rpm and adjust by feel on the line.
                      </>
                    )}
                  </p>
                </RecCard>
              ))}

            {/* General guidance (not simulated) */}
            {tyre && (
              <RecCard
                icon={CircleDot}
                title="Tyre pressure"
                muted={tyre.is_guideline !== false}
                badge={tyre.is_guideline !== false ? GUIDANCE_LABEL : null}
              >
                <div className="mb-3 flex flex-wrap gap-x-8 gap-y-3">
                  <FromTo
                    label="Rear"
                    to={fmtNum(tyre.rear_psi, 0)}
                    unit="psi"
                    from={tyre.stock_rear_psi != null ? fmtNum(tyre.stock_rear_psi, 0) : null}
                  />
                  <FromTo
                    label="Front"
                    to={fmtNum(tyre.front_psi, 0)}
                    unit="psi"
                    from={tyre.stock_front_psi != null ? fmtNum(tyre.stock_front_psi, 0) : null}
                  />
                </div>
                {tyre.rationale && <p className="text-sm text-white/75">{tyre.rationale}</p>}
              </RecCard>
            )}

            {fuel && (
              <RecCard
                icon={Flame}
                title="Fuel and timing"
                muted={fuel.is_guideline !== false}
                badge={fuel.is_guideline !== false ? GUIDANCE_LABEL : null}
              >
                {fuel.applicable === false ? (
                  <p className="text-sm text-white/75">
                    {fuel.rationale || 'No fuel or timing change is suggested for these conditions.'}
                  </p>
                ) : (
                  <>
                    <div className="mb-3 flex flex-wrap gap-x-8 gap-y-3">
                      <FromTo label="Fuel trim" to={`${signed(fuel.fuel_trim_pct, 1)}`} unit="%" />
                      <FromTo label="Spark timing" to={`${signed(fuel.timing_advance_deg, 1)}`} unit="°" />
                    </div>
                    {fuel.rationale && <p className="text-sm text-white/75">{fuel.rationale}</p>}
                  </>
                )}
              </RecCard>
            )}

            <p className="px-1 text-xs text-white/60">
              Gearing and launch figures come from the <Term k="full_sim">full simulation</Term> for the
              conditions above. Tyre pressure and fuel advice are general rules of thumb. Confirm them with a
              test pass or a dyno before a competitive run.
            </p>

            <NextSteps
              items={[
                ran?.bike && {
                  icon: Zap,
                  title: 'Simulate this bike',
                  hint: 'See its quarter-mile time, splits and charts.',
                  href: `/simulator?bike=${ran.bike.id}${
                    ran.location?.matched_venue_id != null ? `&venue=${ran.location.matched_venue_id}` : ''
                  }${ran.riderKg !== 75 ? `&rider=${ran.riderKg}` : ''}`,
                },
                ran?.bike && {
                  icon: Wrench,
                  title: 'Find the best parts for my budget',
                  hint: 'We test every compatible part and pick the quickest set.',
                  href: `/optimize?bike_id=${ran.bike.id}`,
                },
              ].filter(Boolean)}
            />
          </>
        )}
      </div>
    </div>
  );
}
