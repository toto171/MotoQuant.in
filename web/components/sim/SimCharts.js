'use client';

/**
 * Recharts-based charts for /simulator. This file is the ONLY place recharts
 * is imported, and it is only ever loaded through ./charts (next/dynamic), so
 * the ~100 KB chart library stays out of the initial bundle (F10).
 * All colours go through cssVar() so charts read in both themes.
 */

import { memo, useId } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area,
} from 'recharts';
import { cssVar } from '../../lib/theme';

export const COLOR = {
  a: cssVar('--accent'),
  b: cssVar('--go'),
  stage: cssVar('--stage'),
  foul: cssVar('--foul'),
};

const GRID = cssVar('--fg', 0.12);
const TICK = { fontSize: 11, fill: cssVar('--fg', 0.65) };
const TOOLTIP = {
  background: cssVar('--surface-2'),
  border: `1px solid ${cssVar('--fg', 0.18)}`,
  borderRadius: 8,
  fontSize: 12,
  color: cssVar('--fg'),
};

/** One filled-area time series (speed, rpm, gear …). */
export const SimChart = memo(function SimChart({ data, dataKey, label, unit, color = COLOR.a, domain, height = 176 }) {
  const gradId = useId();
  if (!data || data.length === 0) return null;
  const gid = `grad-${dataKey}-${gradId}`;
  return (
    <figure className="m-0" style={{ height: height + 28 }}>
      <figcaption className="mb-2 text-sm font-medium text-white/75">{label}</figcaption>
      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 4, right: 4, left: -16, bottom: 0 }}>
            <defs>
              <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity={0.28} />
                <stop offset="100%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={GRID} />
            <XAxis dataKey="t" tick={TICK} tickFormatter={(v) => `${v}s`} />
            <YAxis tick={TICK} domain={domain} />
            <Tooltip
              contentStyle={TOOLTIP}
              labelFormatter={(v) => `${v} s`}
              formatter={(v) => [`${typeof v === 'number' ? v.toFixed(1) : v} ${unit}`, label]}
            />
            <Area type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2} fill={`url(#${gid})`} dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </figure>
  );
});

/** Build A vs Build B overlay for one channel. */
export const OverlayChart = memo(function OverlayChart({ data, keyBase, label }) {
  return (
    <figure className="m-0" style={{ height: 204 }}>
      <figcaption className="mb-2 text-sm font-medium text-white/75">{label}</figcaption>
      <div style={{ height: 176 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 4, right: 4, left: -16, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={GRID} />
            <XAxis dataKey="t" tick={TICK} tickFormatter={(v) => `${v}s`} />
            <YAxis tick={TICK} />
            <Tooltip contentStyle={TOOLTIP} labelFormatter={(v) => `${v} s`} />
            <Line type="monotone" dataKey={`a_${keyBase}`} stroke={COLOR.a} strokeWidth={2} dot={false} name="Build A" />
            <Line type="monotone" dataKey={`b_${keyBase}`} stroke={COLOR.b} strokeWidth={2} dot={false} name="Build B" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </figure>
  );
});

/** Real (Dragy) vs simulated speed. */
export const RealVsSimChart = memo(function RealVsSimChart({ data }) {
  return (
    <figure className="m-0" style={{ height: 224 }}>
      <figcaption className="mb-2 text-sm font-medium text-white/75">Speed: your run vs the simulator</figcaption>
      <div style={{ height: 192 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 4, right: 4, left: -16, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={GRID} />
            <XAxis dataKey="t" tick={TICK} tickFormatter={(v) => `${v}s`} />
            <YAxis tick={TICK} />
            <Tooltip contentStyle={TOOLTIP} labelFormatter={(v) => `${v} s`} />
            <Line type="monotone" dataKey="real" stroke={COLOR.b} strokeWidth={2.5} dot={false} name="Your run (Dragy)" />
            <Line type="monotone" dataKey="sim" stroke={COLOR.a} strokeWidth={2} strokeDasharray="5 3" dot={false} name="Simulator" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </figure>
  );
});

/** Dyno power + torque curve. */
export const DynoChart = memo(function DynoChart({ data }) {
  return (
    <figure className="m-0" style={{ height: 244 }}>
      <figcaption className="mb-2 text-sm font-medium text-white/75">Power and torque against engine speed</figcaption>
      <div style={{ height: 212 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 4, right: 4, left: -8, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={GRID} />
            <XAxis dataKey="rpm" tick={TICK} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
            <YAxis yAxisId="power" tick={{ ...TICK, fill: COLOR.a }} orientation="left" />
            <YAxis yAxisId="torque" tick={{ ...TICK, fill: COLOR.b }} orientation="right" />
            <Tooltip contentStyle={TOOLTIP} labelFormatter={(v) => `${v} rpm`} />
            <Line yAxisId="power" type="monotone" dataKey="power" stroke={COLOR.a} strokeWidth={2.5} dot={false} name="Power (hp)" />
            <Line yAxisId="torque" type="monotone" dataKey="torque" stroke={COLOR.b} strokeWidth={2} dot={false} name="Torque (Nm)" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </figure>
  );
});
