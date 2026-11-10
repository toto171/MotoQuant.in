'use client';

import { useMemo } from 'react';
import { BarChart3 } from 'lucide-react';
import Term from '../Term';
import ActionButton from '../ActionButton';
import SimProgress from '../SimProgress';
import { ErrorTile, PANEL } from './controls';
import { SimChart, COLOR_NAMES } from './charts';
import { conditionsText, fmt } from './format';

function PartsNote({ sim }) {
  if (!sim.selectedParts.length) return null;
  return (
    <p className="rounded-xl border border-signal-stage/30 bg-signal-stage/[0.07] p-3 text-sm text-white/80">
      The full simulation uses your bike, weight, tyres and conditions but <strong>not your selected parts yet</strong>.
      For a time with parts, use the Quarter mile tab.
    </p>
  );
}

function StaleNote({ sim }) {
  const { fullRes, fullFresh } = sim;
  if (!fullRes || fullFresh) return null;
  return (
    <p role="status" className="rounded-xl border border-white/15 bg-white/[0.04] p-3 text-sm text-white/80">
      You changed something since this run. Run the full simulation again to update.
    </p>
  );
}

export function ChartsTab({ sim }) {
  const { fullSimTask: task, fullRes, bike, startFullSim } = sim;

  const chartData = useMemo(() => {
    const ts = fullRes?.timeseries;
    if (!ts?.t_s) return [];
    // The server reports tyre grip used as 0-100 already multiplied by 100 again
    // (values up to ~10,000); show a true percentage.
    const tmax = Math.max(0, ...(ts.traction_pct || [0]));
    const tdiv = tmax > 200 ? 100 : 1;
    return ts.t_s.map((t, i) => ({
      t: +t.toFixed(2),
      speed: ts.v_kmh?.[i] ?? 0,
      rpm: ts.rpm?.[i] ?? 0,
      gear: ts.gear?.[i] ?? 0,
      traction: (ts.traction_pct?.[i] ?? 0) / tdiv,
      tire_temp: ts.tire_temp_c?.[i] ?? 0,
      power: ts.power_kw?.[i] ?? 0,
    }));
  }, [fullRes]);

  const run = () => startFullSim();

  if (task.active) {
    return (
      <div className="mx-auto max-w-md py-10">
        <SimProgress active progress={task.progress} stage={task.stage} label="Running the full simulation" onStop={task.stop} />
        <p className="mt-2 text-center text-sm text-white/60">Your charts will appear here.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {task.error && <ErrorTile message={`The full simulation failed — ${task.error}`} onRetry={run} />}
      <PartsNote sim={sim} />
      <StaleNote sim={sim} />
      {chartData.length > 0 ? (
        <div className="space-y-6">
          <div className="grid gap-5 sm:grid-cols-2">
            <SimChart data={chartData} dataKey="speed" label="Speed (km/h)" unit="km/h" />
            <SimChart data={chartData} dataKey="rpm" label="Engine speed (rpm)" unit="rpm" />
          </div>
          <div className="grid gap-5 sm:grid-cols-2">
            <SimChart data={chartData} dataKey="gear" label="Gear" unit="" color={COLOR_NAMES.b} />
            <SimChart data={chartData} dataKey="traction" label="Tyre grip used (%)" unit="%" color={COLOR_NAMES.b} domain={[0, 110]} />
          </div>
          <div className="grid gap-5 sm:grid-cols-2">
            <SimChart data={chartData} dataKey="power" label="Power (kW)" unit="kW" color={COLOR_NAMES.stage} />
            <SimChart data={chartData} dataKey="tire_temp" label="Rear tyre temperature (°C)" unit="°C" color={COLOR_NAMES.foul} />
          </div>
          <p className="text-sm text-white/60">
            Conditions: {conditionsText(fullRes.meta)}. <Term k="traction">What is tyre grip used?</Term>
          </p>
        </div>
      ) : (
        <div className="py-8 text-center">
          <BarChart3 size={32} aria-hidden="true" className="mx-auto mb-3 text-white/35" />
          <h3 className="font-display text-lg font-semibold text-white">See what happens along the strip</h3>
          <p className="mx-auto mt-1 max-w-sm text-sm text-white/65">
            Run the full simulation to chart speed, engine speed, gear, grip, power and tyre temperature.
          </p>
          <ActionButton task={task} onRun={run} label="Run the full simulation" runningLabel="Full simulation" disabled={!bike} className="mt-5" />
        </div>
      )}
    </div>
  );
}

const SPLITS = [
  ['60ft_s', 'sixty', 'First 60 ft', '18.3 m'],
  ['330ft_s', null, '330 ft', '100.6 m'],
  ['660ft_s', 'eighth', 'Halfway — ⅛ mile', '201.2 m'],
  ['1000ft_s', null, '1,000 ft', '304.8 m'],
  ['1320ft_s', 'et', 'Finish — ¼ mile', '402.3 m'],
];

export function SplitsTab({ sim }) {
  const { fullSimTask: task, fullRes, headline, bike, startFullSim } = sim;
  const run = () => startFullSim();
  const hasFull = !!fullRes;

  if (task.active) {
    return (
      <div className="mx-auto max-w-md py-10">
        <SimProgress active progress={task.progress} stage={task.stage} label="Running the full simulation" onStop={task.stop} />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {task.error && <ErrorTile message={`The full simulation failed — ${task.error}`} onRetry={run} />}
      <PartsNote sim={sim} />
      <StaleNote sim={sim} />
      {hasFull ? (
        <div className="timeslip overflow-x-auto">
          <h3 className="mb-2 font-display text-base font-semibold text-white"><Term k="splits">Split times</Term></h3>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-dashed border-white/20 text-left text-white/60">
                <th className="py-2 font-medium">Distance</th>
                <th className="py-2 text-right font-medium">Time</th>
                <th className="py-2 text-right font-medium">Speed</th>
              </tr>
            </thead>
            <tbody>
              {SPLITS.map(([key, term, label, metres]) => {
                const t = fullRes.splits?.[key];
                if (typeof t !== 'number') return null;
                return (
                  <tr key={key} className="border-b border-dashed border-white/10 last:border-0">
                    <td className="py-2.5 text-white/80">
                      {term && term !== 'et' ? <Term k={term}>{label}</Term> : label}{' '}
                      <span className="text-xs text-white/55">{metres}</span>
                    </td>
                    <td className="py-2.5 text-right font-mono font-medium tabular-nums text-white">{t.toFixed(3)} s</td>
                    <td className="py-2.5 text-right font-mono tabular-nums text-white/70">
                      {key === '1320ft_s' ? `${fmt(fullRes.trap_speed_kmh, 1)} km/h` : ''}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="py-8 text-center">
          {headline && !headline.estimated && headline.et_60ft_s != null ? (
            <>
              <p className="text-sm text-white/70">From your last calculation:</p>
              <p className="mt-1 font-mono text-base tabular-nums text-white">
                60 ft {fmt(headline.et_60ft_s, 3)} s · ⅛ mile {fmt(headline.et_eighth_s, 3)} s · ¼ mile {fmt(headline.et_quarter_s, 3)} s
              </p>
            </>
          ) : headline ? (
            <p className="text-sm text-white/70">
              The instant estimate gives a quarter-mile time of {fmt(headline.et_quarter_s, 2)} s but no split times.
            </p>
          ) : (
            <p className="text-sm text-white/70">Choose a bike to see its split times.</p>
          )}
          <ActionButton task={task} onRun={run} label="Get the full split times" runningLabel="Full simulation" disabled={!bike} className="mt-5" />
        </div>
      )}
    </div>
  );
}
