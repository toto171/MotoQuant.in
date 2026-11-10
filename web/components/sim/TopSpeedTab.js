'use client';

import { useMemo } from 'react';
import { Gauge } from 'lucide-react';
import Term from '../Term';
import ActionButton from '../ActionButton';
import SimProgress from '../SimProgress';
import { ErrorTile, PANEL } from './controls';
import { SimChart } from './charts';
import ConditionsLine from '../ConditionsLine';

const LSR = [
  { key: 'quarter_mile', label: '¼ mile', sub: '402 m' },
  { key: 'half_mile', label: '½ mile', sub: '805 m' },
  { key: 'one_km', label: '1 km', sub: '1,000 m' },
  { key: 'one_mile', label: '1 mile', sub: '1,609 m' },
  { key: 'two_mile', label: '2 miles', sub: '3,219 m' },
];

export default function TopSpeedTab({ sim }) {
  const { topSpeedTask: task, topRes: r, topFresh, bike, startTopSpeed, selectedParts } = sim;

  const chartData = useMemo(() => {
    const ts = r?.timeseries;
    if (!ts?.t?.length) return [];
    return ts.t.map((t, i) => ({ t: +t.toFixed(2), speed: +(ts.v_kmh?.[i] ?? 0).toFixed(1) }));
  }, [r]);

  if (task.active) {
    return (
      <div className="mx-auto max-w-md py-10">
        <SimProgress active progress={task.progress} stage={task.stage} label="Finding the top speed" onStop={task.stop} />
        <p className="mt-2 text-center text-sm text-white/60">Simulating up to two minutes at full throttle.</p>
      </div>
    );
  }

  if (task.error) {
    return (
      <div className="space-y-4 py-4">
        <ErrorTile message={`The top-speed run failed: ${task.error}`} onRetry={startTopSpeed} />
      </div>
    );
  }

  if (!r) {
    return (
      <div className="py-8 text-center">
        <Gauge size={32} aria-hidden="true" className="mx-auto mb-3 text-white/35" />
        <h3 className="font-display text-lg font-semibold text-white">How fast can it go?</h3>
        <p className="mx-auto mt-1 max-w-sm text-sm text-white/65">
          Runs flat out until the bike stops speeding up, then reports its <Term k="top_speed">top speed</Term> and
          land-speed-record split times (¼ mile to 2 miles).
        </p>
        <ActionButton task={task} onRun={startTopSpeed} label="Find the top speed" runningLabel="Top speed" disabled={!bike} className="mt-5" />
      </div>
    );
  }

  const lsr = r.lsr_splits || {};
  return (
    <div className="space-y-4">
      {!topFresh && (
        <p role="status" className="rounded-xl border border-white/15 bg-white/[0.04] p-3 text-sm text-white/80">
          You changed something since this run. Run it again to update.
        </p>
      )}
      <div className={`${PANEL} text-center`}>
        <p className="text-sm text-white/65"><Term k="top_speed">Top speed</Term></p>
        {r.terminal_velocity_kmh != null && (
          <p className="font-display text-6xl font-bold leading-none tabular-nums text-accent">
            {r.terminal_velocity_kmh.toFixed(1)}
            <span className="ml-1.5 text-2xl font-semibold text-white/60">km/h</span>
          </p>
        )}
        <p className="mt-2 text-sm text-white/65 tabular-nums">
          {r.terminal_velocity_mph?.toFixed(1)} mph · {r.terminal_velocity_ms?.toFixed(1)} m/s
        </p>
        <p className={`chip mt-3 !h-auto py-1 ${r.reached_plateau ? 'chip-go' : 'chip-stage'}`}>
          {r.reached_plateau ? 'It stopped speeding up: this is its top speed' : 'Still speeding up when the run ended, so it could go faster'}
        </p>
      </div>

      <div className={PANEL}>
        <div className="stat-row"><span>Time to reach top speed</span><span>{r.time_to_terminal_s?.toFixed(2)} s</span></div>
        <div className="stat-row">
          <span>Distance to reach top speed</span>
          <span>
            {r.distance_to_terminal_m >= 1000
              ? `${(r.distance_to_terminal_m / 1000).toFixed(2)} km`
              : `${r.distance_to_terminal_m?.toFixed(0)} m`}
          </span>
        </div>
        <div className="stat-row"><span>Power at top speed</span><span>{r.terminal_power_hp?.toFixed(0)} hp</span></div>
        <div className="stat-row"><span>Gear</span><span>{r.terminal_gear}</span></div>
        <div className="stat-row"><span><Term k="redline">Engine speed</Term></span><span>{r.terminal_rpm?.toLocaleString('en-US')} rpm</span></div>
      </div>

      {LSR.some((s) => lsr[s.key]) && (
        <div className={PANEL}>
          <h3 className="mb-2 font-display text-base font-semibold text-white">Land-speed-record splits</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10 text-left text-white/60">
                  <th className="py-2 font-medium">Distance</th>
                  <th className="py-2 text-right font-medium">Time</th>
                  <th className="py-2 text-right font-medium">Speed</th>
                </tr>
              </thead>
              <tbody>
                {LSR.filter((s) => lsr[s.key]).map((s) => (
                  <tr key={s.key} className="border-b border-white/[0.08] last:border-0">
                    <td className="py-2.5 text-white">{s.label} <span className="text-xs text-white/55">{s.sub}</span></td>
                    <td className="py-2.5 text-right font-mono tabular-nums text-white">{lsr[s.key].time_s?.toFixed(3)} s</td>
                    <td className="py-2.5 text-right font-mono tabular-nums text-white">{lsr[s.key].speed_kmh?.toFixed(1)} km/h</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {chartData.length > 0 && (
        <div className={PANEL}>
          <SimChart data={chartData} dataKey="speed" label="Speed against time" unit="km/h" />
        </div>
      )}

      <ConditionsLine env={r.environment} className="text-sm text-white/60" />
      {(r.parts_skipped?.length ?? 0) > 0 && (
        <p className="text-sm text-white/60">Some parts in this setup are no longer in the catalog and were skipped.</p>
      )}

      <ActionButton task={task} onRun={startTopSpeed} label="Run it again" runningLabel="Top speed" variant="ghost" disabled={!bike} className="w-full" />
    </div>
  );
}
