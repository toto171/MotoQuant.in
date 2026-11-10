'use client';

/**
 * ResultCard — "Your result": the big quarter-mile time, one plain sentence,
 * the conditions it was computed under, then the numbers (CLARITY v6 rule 5).
 * Used by Simple mode and by the Advanced "Quarter mile" tab.
 *
 * Honesty rules: never a `—` row (rows that cannot be filled are hidden);
 * the instant estimate is labelled as such; the conditions line always names
 * where the air came from; a stale result is dimmed and says so; Save is only
 * offered on an exact server result that matches the current inputs.
 */

import Link from 'next/link';
import { Check } from 'lucide-react';
import ResultSentence from '../ResultSentence';
import Term from '../Term';
import ActionButton from '../ActionButton';
import SimProgress from '../SimProgress';
import { ErrorTile } from './controls';
import ConditionsLine from '../ConditionsLine';
import { fmt, inr, isNum, quickerSlower } from './format';

function scrollToId(id) {
  const el = typeof document !== 'undefined' ? document.getElementById(id) : null;
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    const focusable = el.querySelector('input, button');
    focusable?.focus?.({ preventScroll: true });
  }
}

export default function ResultCard({ sim, advanced = false }) {
  const {
    bike, headline, headlineFresh, exactFull, quickRes, quickFresh, selectedParts, buildCost, liveActive,
    quickTask, fullSimTask, saveTask, saveable, savedRun, startFullSim, calculateNow,
    setShowEnv,
  } = sim;

  const meta = headline?.meta;
  const stale = !!headline && !headlineFresh && !liveActive;
  const et = headline?.et_quarter_s;
  const modified = !!meta && (meta.partCount > 0 || meta.powerBoost !== 0 || meta.massChange !== 0);

  const changeLocation = () => {
    if (advanced) {
      setShowEnv(true);
      setTimeout(() => scrollToId('sim-env'), 60);
    } else {
      scrollToId('sim-location');
    }
  };

  // The "parts make it quicker" strip comes from the quick sim (it also runs
  // the stock bike); the exact full simulation agrees with it to the millisecond.
  const delta =
    quickRes && quickFresh && !quickRes.estimated && isNum(quickRes.stock_et_s) && isNum(quickRes.et_delta_s)
      ? quickRes
      : null;
  const venueChosen = !!meta?.venueId;
  const skipped = headline?.parts_skipped || [];

  const rows = headline
    ? [
        ['sixty', 'First 60 ft (launch)', fmt(headline.et_60ft_s, 2) && `${fmt(headline.et_60ft_s, 2)} s`],
        ['eighth', 'Halfway — ⅛ mile', fmt(headline.et_eighth_s, 2) && `${fmt(headline.et_eighth_s, 2)} s`],
        ['trap', 'Finish-line speed', fmt(headline.trap_speed_kmh, 0) && `${fmt(headline.trap_speed_kmh, 0)} km/h`],
        [null, 'Power', fmt(headline.peak_power_hp, 0) && `${fmt(headline.peak_power_hp, 0)} hp`],
        [null, 'Total weight with rider', fmt(headline.total_mass_kg, 0) && `${fmt(headline.total_mass_kg, 0)} kg`],
      ].filter((r) => r[2])
    : [];

  const runFull = () => startFullSim(advanced ? { goTo: 'charts' } : {});

  return (
    <section className="card card-pad relative overflow-hidden" aria-labelledby="sim-result-title">
      {quickTask.active && <SimProgress active edge className="absolute inset-x-0 top-0" />}

      <div className="flex items-center justify-between gap-3">
        <h2 id="sim-result-title" className="font-display text-xl font-semibold text-white">Your result</h2>
        {headline?.estimated && <span className="chip chip-stage">Instant estimate</span>}
        {headline && !headline.estimated && <span className="chip chip-go">Exact</span>}
      </div>

      {!bike && (
        <p className="mt-4 text-base text-white/70">Choose a bike to see its quarter-mile time.</p>
      )}

      {bike && !headline && !quickTask.error && (
        <div aria-busy="true" aria-label="Calculating your time" className="mt-4">
          <p role="status" className="text-sm text-white/70">Calculating exact time…</p>
          <div className="skeleton mt-2 h-5 w-40" />
          <div className="skeleton mt-3 h-16 w-56" />
          <div className="skeleton mt-4 h-4 w-full" />
          <div className="skeleton mt-2 h-4 w-3/4" />
        </div>
      )}

      {quickTask.error && !quickTask.active && (
        <ErrorTile
          className="mt-4"
          message={quickTask.error}
          onRetry={calculateNow}
          retryLabel="Try again"
        />
      )}

      {headline && isNum(et) && (
        <div className={`mt-4 transition-opacity ${stale ? 'opacity-60' : ''}`}>
          <p className="text-sm text-white/65"><Term k="et">Quarter-mile time</Term></p>
          <p className="font-display text-6xl font-bold leading-none tabular-nums text-accent md:text-7xl">
            {et.toFixed(headline.estimated ? 2 : 3)}
            <span className="ml-1.5 text-2xl font-semibold text-white/60">s</span>
          </p>

          <ResultSentence
            className="mt-4"
            bikeName={meta?.bikeName}
            riderKg={meta?.riderKg}
            et={et}
            trapKmh={headline.trap_speed_kmh}
            venueName={meta?.venueName}
            estimated={!!headline.estimated}
            build={modified ? 'modified' : 'stock'}
          />

          <ConditionsLine
            className="mt-2 text-sm text-white/65"
            env={headline.environment}
            estimate={headline.environment || !headline.estimated ? null : headline.estimateAssumes || {}}
            unreported={!headline.environment && !headline.estimated}
            placeLabel={!venueChosen ? meta?.placeLabel : null}
            onChange={changeLocation}
          />

          {skipped.length > 0 && (
            <p role="status" className="mt-3 rounded-xl border border-signal-stage/30 bg-signal-stage/[0.07] p-3 text-sm text-white/80">
              Some parts in this setup are no longer in the catalog and were skipped.
            </p>
          )}

          {headline.estimated && (
            <p className="mt-3 rounded-xl border border-signal-stage/30 bg-signal-stage/[0.07] p-3 text-sm text-white/80">
              This is an <Term k="instant_estimate">instant estimate</Term> (typically within about 0.1 s). Run the{' '}
              <Term k="full_sim">full simulation</Term> for the exact time, split times and charts.
            </p>
          )}

          {stale && (
            <p role="status" className="mt-3 rounded-xl border border-white/15 bg-white/[0.04] p-3 text-sm text-white/80">
              You changed something. Press <strong>Calculate my time</strong> to update this result.
            </p>
          )}

          {rows.length > 0 && (
            <div className="mt-4">
              {rows.map(([k, label, value]) => (
                <div className="stat-row" key={label}>
                  <span>{k ? <Term k={k}>{label}</Term> : label}</span>
                  <span>{value}</span>
                </div>
              ))}
            </div>
          )}

          {delta && (
            <div
              className={`mt-4 rounded-xl border p-3 text-sm ${
                delta.et_delta_s < 0
                  ? 'border-signal-go/30 bg-signal-go/[0.07]'
                  : delta.et_delta_s > 0
                    ? 'border-signal-foul/30 bg-signal-foul/[0.07]'
                    : 'border-white/15 bg-white/[0.03]'
              }`}
            >
              <p className="font-medium text-white">
                Your parts make it{' '}
                <span className={delta.et_delta_s < 0 ? 'text-signal-go' : delta.et_delta_s > 0 ? 'text-signal-foul' : ''}>
                  {quickerSlower(delta.et_delta_s)}
                </span>
              </p>
              <p className="mt-0.5 text-white/70">
                Without them: {delta.stock_et_s.toFixed(3)} s. With them: {delta.et_quarter_s.toFixed(3)} s.
              </p>
              {buildCost > 0 && selectedParts.length > 0 && (
                <p className="mt-1 text-white/70">
                  {selectedParts.length} {selectedParts.length === 1 ? 'part' : 'parts'}, {inr(buildCost)}
                  {delta.et_delta_s < 0 && (
                    <>
                      {' · '}
                      <Term k="cost_per_tenth">Cost per tenth of a second</Term>:{' '}
                      {inr(buildCost / (Math.abs(delta.et_delta_s) * 10))}
                    </>
                  )}
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── Actions ───────────────────────────────────────────────────── */}
      <div className="mt-5 space-y-3">
        {!liveActive && bike && (
          <ActionButton
            task={quickTask}
            onRun={calculateNow}
            label="Calculate my time"
            runningLabel="Calculating"
            className="w-full"
          />
        )}

        {headline?.estimated && (
          <ActionButton
            task={fullSimTask}
            onRun={runFull}
            label="Run the full simulation"
            runningLabel="Full simulation"
            variant={liveActive ? 'primary' : 'ghost'}
            className="w-full"
          />
        )}

        {headline && !headline.estimated && saveable && (
          savedRun ? (
            <div className="rounded-xl border border-signal-go/30 bg-signal-go/[0.07] p-3 text-sm">
              <p className="flex items-center gap-2 font-medium text-signal-go">
                <Check size={16} aria-hidden="true" /> Saved in this browser
              </p>
              <p className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-white/80">
                <Link href={`/timeslip?${savedRun.query}`} className="font-medium text-accent underline underline-offset-2">Open the timeslip</Link>
                <Link href="/runs" className="underline underline-offset-2">Your runs</Link>
              </p>
            </div>
          ) : (
            <ActionButton
              task={saveTask}
              onRun={() => saveTask.run()}
              label="Save this run"
              runningLabel="Saving"
              className="w-full"
            />
          )
        )}
        {saveTask.error && !saveTask.active && (
          <ErrorTile message={saveTask.error} onRetry={() => saveTask.run()} />
        )}

        {headline && !headline.estimated && !exactFull && (
          <ActionButton
            task={fullSimTask}
            onRun={runFull}
            label="Run the full simulation for charts and splits"
            runningLabel="Full simulation"
            variant="ghost"
            className="w-full"
          />
        )}
        {fullSimTask.error && !fullSimTask.active && (
          <ErrorTile message={`The full simulation failed — ${fullSimTask.error}`} onRetry={runFull} />
        )}
      </div>
    </section>
  );
}
