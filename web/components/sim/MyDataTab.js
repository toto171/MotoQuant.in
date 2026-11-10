'use client';

import { useMemo, useRef } from 'react';
import { BarChart3, ExternalLink, Upload, Zap } from 'lucide-react';
import Term from '../Term';
import SimProgress from '../SimProgress';
import { ErrorTile, PANEL } from './controls';
import { DynoChart, RealVsSimChart } from './charts';
import { mergeOnTime } from '../../lib/timeseries';
import { timeslipIssueUrl } from '../../lib/contribute';
import { bikeName } from './format';

export default function MyDataTab({ sim }) {
  const {
    dragyTask, dynoTask, uploadResult: u, onDragyFile, onDynoFile, lastDragyFileRef, lastDynoFileRef, bike,
  } = sim;
  const dragyRef = useRef(null);
  const dynoRef = useRef(null);
  const busy = dragyTask.active || dynoTask.active;

  const realVsSim = useMemo(() => {
    if (u?.type !== 'dragy' || !u.best_run?.timeseries || !u.overlay?.sim_timeseries) return [];
    const real = u.best_run.timeseries;
    const simTs = u.overlay.sim_timeseries;
    // The uploaded run and the simulation use different sample times.
    return mergeOnTime([
      { prefix: 'r', t: real.t_s, channels: { v: real.v_kmh } },
      { prefix: 's', t: simTs.t_s, channels: { v: simTs.v_kmh } },
    ]).map((row) => ({ t: row.t, real: row.r_v, sim: row.s_v }));
  }, [u]);

  const dynoCurve = useMemo(() => {
    if (u?.type !== 'dyno' || !u.curve) return [];
    return u.curve.rpm.map((rpm, i) => ({
      rpm,
      power: u.curve.power_hp?.[i] ?? 0,
      torque: u.curve.torque_nm?.[i] ?? 0,
    }));
  }, [u]);

  const err = u?.overlay?.et_error_s;

  return (
    <div className="space-y-4">
      <p className="text-sm text-white/70">
        Upload a real <Term k="dragy">Dragy</Term> run or a <Term k="dyno">dyno</Term> pull to check the simulator
        against your own bike.
      </p>

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <input type="file" ref={dragyRef} accept=".csv,.json" onChange={onDragyFile} className="hidden" aria-label="Choose a Dragy file" />
          <button
            type="button"
            onClick={() => dragyRef.current?.click()}
            disabled={busy}
            className="flex min-h-[112px] w-full flex-col items-center justify-center gap-1 rounded-xl border border-dashed border-white/25 p-4 text-center transition-colors hover:border-accent/60 disabled:opacity-50"
          >
            <Zap size={22} aria-hidden="true" className="text-accent" />
            <span className="text-sm font-semibold text-white">Upload a Dragy run</span>
            <span className="text-xs text-white/60">CSV or JSON export</span>
          </button>
        </div>
        <div>
          <input type="file" ref={dynoRef} accept=".csv,.txt" onChange={onDynoFile} className="hidden" aria-label="Choose a dyno file" />
          <button
            type="button"
            onClick={() => dynoRef.current?.click()}
            disabled={busy}
            className="flex min-h-[112px] w-full flex-col items-center justify-center gap-1 rounded-xl border border-dashed border-white/25 p-4 text-center transition-colors hover:border-accent/60 disabled:opacity-50"
          >
            <BarChart3 size={22} aria-hidden="true" className="text-accent" />
            <span className="text-sm font-semibold text-white">Upload a dyno pull</span>
            <span className="text-xs text-white/60">DynoJet or MoTeC CSV</span>
          </button>
        </div>
      </div>

      {busy && (
        <div className="mx-auto max-w-sm">
          <SimProgress
            active
            label={dragyTask.active ? 'Reading your Dragy run' : 'Reading your dyno file'}
            onStop={dragyTask.active ? dragyTask.stop : dynoTask.stop}
          />
        </div>
      )}
      {dragyTask.error && !dragyTask.active && (
        <ErrorTile
          message={`The Dragy upload failed — ${dragyTask.error}`}
          onRetry={lastDragyFileRef.current ? () => dragyTask.run(lastDragyFileRef.current) : undefined}
        />
      )}
      {dynoTask.error && !dynoTask.active && (
        <ErrorTile
          message={`The dyno upload failed — ${dynoTask.error}`}
          onRetry={lastDynoFileRef.current ? () => dynoTask.run(lastDynoFileRef.current) : undefined}
        />
      )}

      {u?.type === 'dragy' && (
        <div className="space-y-4">
          <div className={PANEL}>
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <h3 className="font-display text-base font-semibold text-white">
                Your best run{u.runs_detected > 1 ? ` (of ${u.runs_detected})` : ''}
              </h3>
              {u.filename && <span className="truncate text-xs text-white/55">{u.filename}</span>}
            </div>
            <div className="mt-3 grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-white/65"><Term k="et">Quarter-mile time</Term></p>
                {u.best_run?.et_quarter_s != null && (
                  <p className="font-display text-3xl font-bold tabular-nums text-accent">{u.best_run.et_quarter_s.toFixed(3)} s</p>
                )}
              </div>
              <div>
                <p className="text-sm text-white/65"><Term k="trap">Finish-line speed</Term></p>
                {u.best_run?.trap_speed_kmh != null && (
                  <p className="font-display text-3xl font-bold tabular-nums text-white">{u.best_run.trap_speed_kmh.toFixed(1)} km/h</p>
                )}
              </div>
            </div>
            {u.best_run?.splits && (
              <div className="mt-3 grid grid-cols-2 gap-x-6 sm:grid-cols-3">
                {Object.entries(u.best_run.splits).map(([k, v]) => (
                  <div key={k} className="stat-row"><span>{k}</span><span>{v?.toFixed(3)} s</span></div>
                ))}
              </div>
            )}
            {u.best_run?.et_quarter_s != null && (
              <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-white/10 pt-4">
                <p className="min-w-[14rem] flex-1 text-sm text-white/65">
                  Your file stays with you; nothing here is stored. To help the simulator, submit
                  this run as a public GitHub issue with the numbers filled in, and attach the
                  Dragy screenshot there.
                </p>
                <a
                  href={timeslipIssueUrl({
                    bikeName: bike ? bikeName(bike) : '',
                    bikeId: bike?.id ?? null,
                    et: u.best_run.et_quarter_s,
                    trap: u.best_run.trap_speed_kmh,
                    sixty: u.best_run.splits?.['60ft_s'] ?? u.best_run.splits?.['60ft'],
                    eighth: u.best_run.splits?.['660ft_s'] ?? u.best_run.splits?.['660ft'],
                  })}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-ghost btn-sm"
                >
                  Submit this run <ExternalLink size={14} aria-hidden="true" />
                </a>
              </div>
            )}
          </div>

          {u.overlay && typeof err === 'number' && (
            <div className={`rounded-xl border p-4 ${Math.abs(err) < 0.15 ? 'border-signal-go/30 bg-signal-go/[0.06]' : 'border-signal-stage/30 bg-signal-stage/[0.06]'}`}>
              <h3 className="font-display text-base font-semibold text-white">Your run against the simulator — {u.overlay.bike_name}</h3>
              <p className="mt-1 text-sm text-white/80">
                {Math.abs(err) < 0.005
                  ? 'The simulator matches your run.'
                  : `The simulator is ${Math.abs(err).toFixed(3)} s ${err > 0 ? 'slower' : 'quicker'} than your run.`}
              </p>
              <div className="mt-2">
                <div className="stat-row"><span>Simulator quarter-mile time</span><span>{u.overlay.sim_et_s?.toFixed(3)} s</span></div>
                {u.overlay.v_rmse_kmh != null && (
                  <div className="stat-row"><span>Average speed difference</span><span>{u.overlay.v_rmse_kmh.toFixed(1)} km/h</span></div>
                )}
              </div>
            </div>
          )}

          {realVsSim.length > 0 && <div className={PANEL}><RealVsSimChart data={realVsSim} /></div>}
        </div>
      )}

      {u?.type === 'dyno' && (
        <div className="space-y-4">
          <div className={PANEL}>
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <h3 className="font-display text-base font-semibold text-white"><Term k="dyno">Dyno</Term> result</h3>
              {u.filename && <span className="truncate text-xs text-white/55">{u.filename}</span>}
            </div>
            <div className="mt-3 grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-white/65">Peak power</p>
                {u.peak_power_hp != null && <p className="font-display text-3xl font-bold tabular-nums text-accent">{u.peak_power_hp.toFixed(1)} hp</p>}
              </div>
              <div>
                <p className="text-sm text-white/65">Peak torque</p>
                {u.peak_torque_nm != null && <p className="font-display text-3xl font-bold tabular-nums text-white">{u.peak_torque_nm.toFixed(1)} Nm</p>}
              </div>
            </div>
            <div className="mt-3">
              {u.rpm_at_peak_power != null && <div className="stat-row"><span>Engine speed at peak power</span><span>{u.rpm_at_peak_power.toFixed(0)} rpm</span></div>}
              {u.rpm_at_peak_torque != null && <div className="stat-row"><span>Engine speed at peak torque</span><span>{u.rpm_at_peak_torque.toFixed(0)} rpm</span></div>}
              {u.correction_factor != null && <div className="stat-row"><span>Weather correction (SAE J1349)</span><span>{u.correction_factor.toFixed(4)}</span></div>}
              {u.n_points != null && <div className="stat-row"><span>Data points</span><span>{u.n_points}</span></div>}
            </div>
          </div>
          {dynoCurve.length > 0 && <div className={PANEL}><DynoChart data={dynoCurve} /></div>}
        </div>
      )}

      {!u && !busy && !dragyTask.error && !dynoTask.error && (
        <div className="py-4 text-center text-sm text-white/65">
          <Upload size={28} aria-hidden="true" className="mx-auto mb-2 text-white/35" />
          We will read your file, show the split times and lay it over the simulator so you can see how close it is.
        </div>
      )}
    </div>
  );
}
