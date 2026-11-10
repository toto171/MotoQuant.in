'use client';

import { useMemo } from 'react';
import { Layers } from 'lucide-react';
import BikePicker from '../BikePicker';
import Term from '../Term';
import ActionButton from '../ActionButton';
import SimProgress from '../SimProgress';
import { ErrorTile, PANEL, SimSlider } from './controls';
import ConditionsLine from '../ConditionsLine';
import { OverlayChart } from './charts';
import { bikeName, inr } from './format';
import { mergeOnTime } from '../../lib/timeseries';

const CHANNELS = [
  { key: 'speed', label: 'Speed (km/h)' },
  { key: 'rpm', label: 'Engine speed (rpm)' },
  { key: 'power', label: 'Power (kW)' },
];

export default function CompareTab({ sim }) {
  const {
    bike, compareBike, setCompareBike, comparePower, setComparePower, compareMass, setCompareMass,
    compareTask: task, compareRes: r, compareFresh, startCompare, powerBoost, selectedParts,
  } = sim;

  // A and B are sampled on their own time grids (different ETs, different
  // step counts), so each is interpolated over ITS OWN time axis.
  const overlay = useMemo(() => {
    const a = r?.a?.timeseries;
    const b = r?.b?.timeseries;
    if (!a?.t_s || !b?.t_s) return [];
    return mergeOnTime([
      { prefix: 'a', t: a.t_s, channels: { speed: a.v_kmh, rpm: a.rpm, power: a.power_kw } },
      { prefix: 'b', t: b.t_s, channels: { speed: b.v_kmh, rpm: b.rpm, power: b.power_kw } },
    ]);
  }, [r]);

  const bName = r?.meta?.bBikeName || bikeName(compareBike || bike);
  const delta = r?.delta;
  const headline =
    delta?.faster === 'B'
      ? `Build B is ${Math.abs(delta.et_s).toFixed(3)} s quicker than Build A`
      : delta?.faster === 'A'
        ? `Build A is ${Math.abs(delta.et_s).toFixed(3)} s quicker than Build B`
        : 'Dead heat: both builds run the same time';

  return (
    <div className="space-y-4">
      <div className="grid items-start gap-3 sm:grid-cols-2">
        <div className="rounded-xl border border-accent/30 bg-accent/[0.05] p-4">
          <h3 className="font-display text-base font-semibold text-accent">Build A: your current setup</h3>
          <p className="mt-1 text-sm text-white/75">
            {bikeName(bike)} · {powerBoost !== 0 ? `${powerBoost > 0 ? '+' : ''}${powerBoost} % power` : 'stock power'} ·{' '}
            {selectedParts.length} {selectedParts.length === 1 ? 'part' : 'parts'}
          </p>
        </div>
        <div className="rounded-xl border border-signal-go/30 bg-signal-go/[0.05] p-4">
          <h3 className="font-display text-base font-semibold text-signal-go">Build B: compare against</h3>
          <div className="mt-3 space-y-4">
            <BikePicker value={compareBike || bike} onSelect={setCompareBike} label="Bike B" />
            <SimSlider label="Engine power change" value={comparePower} onChange={setComparePower} min={-20} max={50} unit=" %" signed good="up" />
            <SimSlider label="Weight added or removed" value={compareMass} onChange={setCompareMass} min={-30} max={30} unit=" kg" signed good="down" />
          </div>
        </div>
      </div>

      <ActionButton task={task} onRun={startCompare} label="Compare the two bikes" runningLabel="Comparing" disabled={!bike} className="w-full" />
      {task.active && <SimProgress active progress={task.progress} stage={task.stage} label="Running both builds" onStop={task.stop} />}
      {task.error && !task.active && <ErrorTile message={`The comparison failed: ${task.error}`} onRetry={startCompare} />}

      {r && delta && (
        <div className="space-y-4">
          {!compareFresh && (
            <p role="status" className="rounded-xl border border-white/15 bg-white/[0.04] p-3 text-sm text-white/80">
              You changed something since this comparison. Run it again to update.
            </p>
          )}
          <div className={`${PANEL} text-center`}>
            <p className="font-display text-xl font-semibold text-white">{headline}</p>
            <p className="mt-1 text-sm text-white/70 tabular-nums">
              Finish-line speed: {Math.abs(delta.trap_kmh).toFixed(1)} km/h {delta.trap_kmh >= 0 ? 'higher' : 'lower'} for Build B
              {delta.cost_diff_inr !== 0 && ` · Build B costs ${inr(Math.abs(delta.cost_diff_inr))} ${delta.cost_diff_inr > 0 ? 'more' : 'less'}`}
            </p>
          </div>

          <ConditionsLine env={r.environment} className="text-sm text-white/60" />

          <div className="grid gap-3 sm:grid-cols-2">
            {[
              { label: 'Build A', name: r.meta.bikeName, d: r.a, tone: 'border-accent/30 text-accent' },
              { label: 'Build B', name: bName, d: r.b, tone: 'border-signal-go/30 text-signal-go' },
            ].map(({ label, name, d, tone }) => (
              <div key={label} className={`rounded-xl border bg-white/[0.03] p-4 ${tone.split(' ')[0]}`}>
                <h3 className={`font-display text-base font-semibold ${tone.split(' ')[1]}`}>{label}</h3>
                <p className="mb-1 truncate text-sm text-white/65">{name}</p>
                <div className="stat-row"><span><Term k="et">Quarter-mile time</Term></span><span className="whitespace-nowrap">{d.et_quarter_s?.toFixed(3)} s</span></div>
                <div className="stat-row"><span><Term k="trap">Finish-line speed</Term></span><span className="whitespace-nowrap">{d.trap_speed_kmh?.toFixed(1)} km/h</span></div>
                <div className="stat-row"><span><Term k="sixty">First 60 ft</Term></span><span className="whitespace-nowrap">{d.et_60ft_s?.toFixed(3)} s</span></div>
                <div className="stat-row"><span>Power</span><span className="whitespace-nowrap">{d.peak_power_hp?.toFixed(0)} hp</span></div>
                <div className="stat-row"><span>Total weight</span><span className="whitespace-nowrap">{d.total_mass_kg?.toFixed(0)} kg</span></div>
              </div>
            ))}
          </div>

          {overlay.length > 0 && (
            <div className={`${PANEL} space-y-5`}>
              <h3 className="font-display text-base font-semibold text-white">Side by side along the strip</h3>
              <p className="flex gap-4 text-sm text-white/70">
                <span className="text-accent">● Build A</span>
                <span className="text-signal-go">● Build B</span>
              </p>
              {CHANNELS.map((c) => <OverlayChart key={c.key} data={overlay} keyBase={c.key} label={c.label} />)}
            </div>
          )}
        </div>
      )}

      {!r && !task.active && !task.error && (
        <div className="py-4 text-center text-sm text-white/65">
          <Layers size={28} aria-hidden="true" className="mx-auto mb-2 text-white/35" />
          Pick a second bike or change its power and weight, then compare the two.
        </div>
      )}
    </div>
  );
}
