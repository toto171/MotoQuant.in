'use client';

/**
 * SimCharts — every recharts usage on the simulator page, split into its own
 * chunk. recharts is ~90-100 KB gzip and the charts only ever render inside
 * conditional result branches, so /simulator loads these via next/dynamic
 * (ssr: false, Skeleton placeholder) and keeps recharts out of the route's
 * initial chunk.
 *
 * The JSX is moved VERBATIM from web/app/simulator/page.js (Aug 2026) — only
 * the values each block closed over became props.
 */

import { useId } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area
} from 'recharts';

const CHART_COLORS = { a: '#FF5E1F', b: '#6FE3B2' };

export function SimChart({ data, dataKey, label, unit, color = CHART_COLORS.a, domain }) {
  const gradId = useId();
  if (!data || data.length === 0) return null;
  const gid = `grad-${dataKey}-${gradId}`;
  return (
    <div className="h-44">
      <p className="label-mono mb-2">{label}</p>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.2} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
          <XAxis dataKey="t" tick={{ fontSize: 9, fill: 'rgba(255,255,255,0.4)' }} tickFormatter={v => `${v}s`} />
          <YAxis tick={{ fontSize: 9, fill: 'rgba(255,255,255,0.4)' }} domain={domain} />
          <Tooltip
            contentStyle={{ background: '#10141B', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, fontSize: 11 }}
            labelFormatter={v => `${v}s`}
            formatter={v => [`${typeof v === 'number' ? v.toFixed(1) : v} ${unit}`, label]}
          />
          <Area type="monotone" dataKey={dataKey} stroke={color} strokeWidth={1.5}
            fill={`url(#${gid})`} dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

// A-vs-B overlay charts (Speed / RPM / Power). `compareResult` is the
// /api/simulate/compare response; the caller guards that BOTH a.timeseries
// and b.timeseries exist before rendering.
export function CompareOverlayCharts({ compareResult }) {
  const overlayData = compareResult.a.timeseries.t_s.map((t, i) => ({
    t: +t.toFixed(2),
    a_speed: compareResult.a.timeseries.v_kmh?.[i] ?? 0,
    b_speed: compareResult.b.timeseries.v_kmh?.[i] ?? 0,
    a_rpm: compareResult.a.timeseries.rpm?.[i] ?? 0,
    b_rpm: compareResult.b.timeseries.rpm?.[i] ?? 0,
    a_power: compareResult.a.timeseries.power_kw?.[i] ?? 0,
    b_power: compareResult.b.timeseries.power_kw?.[i] ?? 0,
  }));
  return (
    <div className="space-y-4">
      <p className="label-mono">Overlay Charts</p>
      {[
        { key: 'speed', label: 'Speed (km/h)', unit: 'km/h' },
        { key: 'rpm', label: 'Engine RPM', unit: 'rpm' },
        { key: 'power', label: 'Power (kW)', unit: 'kW' },
      ].map(chart => (
        <div key={chart.key} className="h-44">
          <p className="label-mono mb-2">{chart.label}</p>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={overlayData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="t" tick={{ fontSize: 9, fill: 'rgba(255,255,255,0.4)' }} tickFormatter={v => `${v}s`} />
              <YAxis tick={{ fontSize: 9, fill: 'rgba(255,255,255,0.4)' }} />
              <Tooltip
                contentStyle={{ background: '#10141B', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, fontSize: 11 }}
                labelFormatter={v => `${v}s`}
              />
              <Line type="monotone" dataKey={`a_${chart.key}`} stroke="#FF5E1F" strokeWidth={1.5} dot={false} name="Build A" />
              <Line type="monotone" dataKey={`b_${chart.key}`} stroke="#6FE3B2" strokeWidth={1.5} dot={false} name="Build B" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ))}
    </div>
  );
}

// Real (Dragy) vs Sim speed overlay. realTs = uploadResult.best_run.timeseries,
// simTs = uploadResult.overlay.sim_timeseries; the caller guards both exist.
export function DragySpeedOverlay({ realTs, simTs }) {
  const maxLen = Math.max(realTs.t_s.length, simTs.t_s.length);
  const overlayData = [];
  for (let i = 0; i < maxLen; i++) {
    overlayData.push({
      t: (realTs.t_s[i] ?? simTs.t_s[i] ?? 0).toFixed(2),
      real: realTs.v_kmh?.[i] ?? null,
      sim: simTs.v_kmh?.[i] ?? null,
    });
  }
  return (
    <div className="h-48">
      <p className="label-mono mb-2">Speed Overlay — Real vs Sim</p>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={overlayData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
          <XAxis dataKey="t" tick={{ fontSize: 9, fill: 'rgba(255,255,255,0.4)' }} tickFormatter={v => `${v}s`} />
          <YAxis tick={{ fontSize: 9, fill: 'rgba(255,255,255,0.4)' }} />
          <Tooltip contentStyle={{ background: '#10141B', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, fontSize: 11 }} labelFormatter={v => `${v}s`} />
          <Line type="monotone" dataKey="real" stroke="#34D97B" strokeWidth={2} dot={false} name="Real (Dragy)" />
          <Line type="monotone" dataKey="sim" stroke="#FF5E1F" strokeWidth={1.5} strokeDasharray="4 2" dot={false} name="Sim" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// Dyno power/torque curve. `curve` = uploadResult.curve ({rpm, power_hp,
// torque_nm} arrays); the caller guards it exists.
export function DynoCurveChart({ curve }) {
  const curveData = curve.rpm.map((rpm, i) => ({
    rpm,
    power: curve.power_hp?.[i] ?? 0,
    torque: curve.torque_nm?.[i] ?? 0,
  }));
  return (
    <div className="h-52">
      <p className="label-mono mb-2">Power & Torque vs RPM</p>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={curveData} margin={{ top: 0, right: 0, left: -10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
          <XAxis dataKey="rpm" tick={{ fontSize: 9, fill: 'rgba(255,255,255,0.4)' }} tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
          <YAxis yAxisId="power" tick={{ fontSize: 9, fill: '#FF5E1F' }} orientation="left" />
          <YAxis yAxisId="torque" tick={{ fontSize: 9, fill: '#6FE3B2' }} orientation="right" />
          <Tooltip contentStyle={{ background: '#10141B', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, fontSize: 11 }} labelFormatter={v => `${v} RPM`} />
          <Line yAxisId="power" type="monotone" dataKey="power" stroke="#FF5E1F" strokeWidth={2} dot={false} name="Power (hp)" />
          <Line yAxisId="torque" type="monotone" dataKey="torque" stroke="#6FE3B2" strokeWidth={1.5} dot={false} name="Torque (Nm)" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
