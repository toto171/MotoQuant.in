'use client';

/**
 * AccuracyExplorer — the flagship "real vs simulated" accuracy surface
 * (IGNITION v5 skin — see web/DESIGN.md).
 *
 * Everything is computed from web/app/validation/accuracy_data.json (passed
 * in as `data`) so the page can never drift from the sweep. Five panels:
 *
 *   1. HERO scatter  — real ET (x) vs sim ET (y), same scale both axes,
 *      a dashed y=x perfect-prediction diagonal + a ±0.2s tolerance band.
 *      Source confidence is encoded as dot opacity + radius, so the low-
 *      confidence DERIVED estimates visibly recede — that's the honesty
 *      story. Single data hue (signal orange). Hover tooltip + filter + a
 *      table fallback for screen readers / no-hover.
 *   2. DISTRIBUTION  — seven-seg stat tiles (within ±0.05/0.10/0.20/0.50,
 *      overall |Δ|, mean bias, top-10 cleanest).
 *   3. RESIDUAL HISTOGRAM — Δ = sim−real, diverging signal-go (sim faster)
 *      / signal-foul (sim slower), neutral centre, orange mean-bias marker.
 *   4. PER-CLUSTER — horizontal weighted-|Δ| bars, status-coloured with the
 *      numeric label always present (colour is never the only signal).
 *   5. BEST PREDICTIONS — the ten cleanest published (non-derived) runs,
 *      plus the honest callout about the DERIVED entry-cc / 2T benchmarks.
 *
 * Chart palette (v6): all colours are theme variables (lib/theme.js cssVar), so
 * the chart is legible in both light and dark. Chart backgrounds are
 * transparent on .card panels.
 *
 * Reduced-motion safe (the SVGs are static + hover-only).
 * Responsive: SVGs scale via viewBox (no body overflow); the wide tables
 * scroll inside their own overflow-x containers.
 */

import { useState, useMemo } from 'react';
import Link from 'next/link';
import ScoreboardDigits from './ScoreboardDigits';
import { cssVar } from '../lib/theme';

// Theme-aware chart palette: every colour reads a CSS variable so it follows
// the light/dark theme with no re-render (see lib/theme.js).
const ACCENT = cssVar('--accent'); // primary data series
const ACCENT_BRIGHT = cssVar('--accent-bright'); // hover / active state
const GO = cssVar('--go'); // negative residual (sim faster)
const FOUL = cssVar('--foul'); // positive residual (sim slower)
const FG = cssVar('--fg'); // foreground ink (text, strokes)
const GRID = cssVar('--fg', 0.14); // neutral gridlines / frames
const BAND = cssVar('--accent', 0.1); // ±0.2s tolerance band fill
const NEUTRAL_BIN = cssVar('--fg', 0.35); // |Δ| < 0.05 centre bin

const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const signed = (n, d = 3) => (n > 0 ? '+' : n < 0 ? '−' : '±') + Math.abs(n).toFixed(d);

// Short, human source label for the tooltip / table.
function shortSource(src) {
  if (!src) return '–';
  const cut = src.split('(')[0].trim();
  return cut.length > 30 ? cut.slice(0, 29) + '…' : cut;
}

// Cluster status chip — colour never the only signal (word is always present).
function StatusChip({ mae }) {
  const status = mae < 0.2 ? 'tight' : mae < 0.5 ? 'fair' : 'wide';
  const cls = mae < 0.2 ? 'chip-go' : mae < 0.5 ? 'chip-stage' : 'chip-foul';
  return <span className={`chip ${cls}`}>{status}</span>;
}

// ─────────────────────────────────────────────────────────────────────────
// 1. HERO SCATTER
// ─────────────────────────────────────────────────────────────────────────
function Scatter({ bikes }) {
  const [filter, setFilter] = useState('all'); // all | trusted | derived
  const [hover, setHover] = useState(null);

  // Axis domain from the data — square, same scale both axes, clipped at 20s
  // so the dense 9.5–16s cloud isn't crushed by a couple of slow estimates.
  const { lo, hi, clipped } = useMemo(() => {
    const vals = [];
    bikes.forEach((b) => vals.push(b.real_et, b.sim_et));
    const rawHi = Math.max(...vals);
    const loV = Math.max(9, Math.floor(Math.min(...vals)));
    const hiV = Math.min(20, Math.ceil(rawHi));
    const clip = bikes.filter((b) => b.real_et > hiV || b.sim_et > hiV).length;
    return { lo: loV, hi: hiV, clipped: clip };
  }, [bikes]);

  const shown = useMemo(() => {
    if (filter === 'trusted') return bikes.filter((b) => b.weight >= 0.7);
    if (filter === 'derived') return bikes.filter((b) => b.weight < 0.7);
    return bikes;
  }, [bikes, filter]);

  // viewBox geometry — a square plot with room for axes.
  const M = { l: 46, r: 14, t: 14, b: 42 };
  const S = 520;
  const W = M.l + S + M.r;
  const H = M.t + S + M.b;
  const sx = (et) => M.l + ((clamp(et, lo, hi) - lo) / (hi - lo)) * S;
  const sy = (et) => M.t + (1 - (clamp(et, lo, hi) - lo) / (hi - lo)) * S;

  const step = hi - lo > 8 ? 2 : 1;
  const ticks = [];
  for (let t = lo; t <= hi + 0.001; t += step) ticks.push(t);

  // ±0.2s tolerance band as one clipped polygon around the diagonal.
  const band = [
    [lo, lo + 0.2],
    [hi - 0.2, hi],
    [hi, hi],
    [hi, hi - 0.2],
    [lo + 0.2, lo],
    [lo, lo],
  ]
    .map(([x, y]) => `${sx(x).toFixed(1)},${sy(y).toFixed(1)}`)
    .join(' ');

  const dotStyle = (w) => ({
    r: 2.4 + w * 2.9,
    o: 0.2 + w * 0.72,
  });

  const hb = hover != null ? shown[hover] : null;

  // Tooltip geometry (drawn inside the SVG so it scales with the chart).
  let tip = null;
  if (hb) {
    const px = sx(hb.real_et);
    const py = sy(hb.sim_et);
    const tw = 210;
    const th = 82;
    const flipX = px > W - tw - 10;
    const flipY = py < th + 10;
    tip = {
      px,
      py,
      x: flipX ? px - tw - 10 : px + 10,
      y: flipY ? py + 12 : py - th - 12,
      tw,
      th,
    };
  }

  const FILTERS = [
    { id: 'all', label: `All · ${bikes.length}` },
    { id: 'trusted', label: 'Instrumented + magazine' },
    { id: 'derived', label: 'Derived estimates' },
  ];

  return (
    <div>
      {/* filter row */}
      <div className="flex flex-wrap items-center gap-2 mb-4">
        {FILTERS.map((f) => {
          const on = filter === f.id;
          return (
            <button
              key={f.id}
              type="button"
              onClick={() => {
                setFilter(f.id);
                setHover(null);
              }}
              aria-pressed={on}
              className={[
                'px-4 min-h-[44px] rounded-full text-sm font-medium transition-colors',
                on
                  ? 'border border-accent/60 bg-accent/10 text-accent'
                  : 'border border-white/15 bg-white/[0.02] text-white/70 hover:text-white hover:border-white/30',
              ].join(' ')}
            >
              {f.label}
            </button>
          );
        })}
      </div>

      <div className="card p-3 sm:p-4">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="w-full h-auto block"
          role="img"
          aria-label="Scatter plot of real quarter-mile ET versus simulated ET for every matched benchmark. Dots cluster tightly on the perfect-prediction diagonal."
        >
          {/* plot frame — transparent fill; the .card carries the surface */}
          <rect x={M.l} y={M.t} width={S} height={S} fill="none" stroke={GRID} strokeWidth="1" />

          {/* ±0.2s tolerance band */}
          <polygon points={band} fill={BAND} />

          {/* gridlines + tick labels */}
          {ticks.map((t) => (
            <g key={t}>
              <line x1={sx(t)} y1={M.t} x2={sx(t)} y2={M.t + S} stroke={GRID} strokeWidth="0.75" />
              <line x1={M.l} y1={sy(t)} x2={M.l + S} y2={sy(t)} stroke={GRID} strokeWidth="0.75" />
              <text x={sx(t)} y={M.t + S + 16} fill={FG} opacity="0.7" fontSize="10" fontFamily="monospace" textAnchor="middle">
                {t}
              </text>
              <text x={M.l - 8} y={sy(t) + 3.5} fill={FG} opacity="0.7" fontSize="10" fontFamily="monospace" textAnchor="end">
                {t}
              </text>
            </g>
          ))}

          {/* perfect-prediction diagonal */}
          <line
            x1={sx(lo)}
            y1={sy(lo)}
            x2={sx(hi)}
            y2={sy(hi)}
            stroke={ACCENT}
            strokeWidth="1.2"
            strokeDasharray="6 5"
            opacity="0.7"
          />
          <text
            x={sx(hi) - 4}
            y={sy(hi) + 16}
            fill={ACCENT}
            opacity="0.8"
            fontSize="10.5"
            fontFamily="monospace"
            textAnchor="end"
          >
            perfect prediction · sim = real
          </text>

          {/* axis titles */}
          <text x={M.l + S / 2} y={H - 4} fill={FG} opacity="0.75" fontSize="11" fontFamily="monospace" textAnchor="middle">
            REAL ET (s): published timeslip
          </text>
          <text
            x={14}
            y={M.t + S / 2}
            fill={FG}
            opacity="0.55"
            fontSize="11"
            fontFamily="monospace"
            textAnchor="middle"
            transform={`rotate(-90 14 ${M.t + S / 2})`}
          >
            SIMULATED ET (s)
          </text>

          {/* dots */}
          {shown.map((b, i) => {
            const { r, o } = dotStyle(b.weight);
            const isH = hover === i;
            return (
              <circle
                key={`${b.make}-${b.model}-${b.year}-${i}`}
                cx={sx(b.real_et)}
                cy={sy(b.sim_et)}
                r={isH ? r + 2 : r}
                fill={isH ? ACCENT_BRIGHT : ACCENT}
                fillOpacity={isH ? 1 : o}
                stroke={isH ? FG : 'none'}
                strokeWidth={isH ? 1.2 : 0}
                onMouseEnter={() => setHover(i)}
                onMouseLeave={() => setHover(null)}
                style={{ cursor: 'pointer' }}
              >
                <title>{`${b.make} ${b.model} (${b.year}): real ${b.real_et}s / sim ${b.sim_et}s / Δ ${signed(b.delta)}s`}</title>
              </circle>
            );
          })}

          {/* hover tooltip */}
          {tip && (
            <g pointerEvents="none">
              <line x1={tip.px} y1={tip.py} x2={tip.x + (tip.x < tip.px ? tip.tw : 0)} y2={tip.y + tip.th / 2} stroke={cssVar('--fg', 0.45)} strokeWidth="0.75" />
              <rect x={tip.x} y={tip.y} width={tip.tw} height={tip.th} rx="7" fill={cssVar('--surface-1')} stroke={cssVar('--fg', 0.3)} strokeWidth="1" />
              <text x={tip.x + 12} y={tip.y + 20} fill={FG} fontSize="12" fontFamily="monospace" fontWeight="600">
                {`${hb.make} ${hb.model}`.slice(0, 26)}
              </text>
              <text x={tip.x + 12} y={tip.y + 36} fill={cssVar('--fg', 0.7)} fontSize="10.5" fontFamily="monospace">
                {`${hb.year} · ${hb.disp_cc}cc · ${hb.cluster_label}`.slice(0, 32)}
              </text>
              <text x={tip.x + 12} y={tip.y + 53} fill={FG} fontSize="11" fontFamily="monospace">
                {`real ${hb.real_et}s   sim ${hb.sim_et}s`}
              </text>
              <text x={tip.x + 12} y={tip.y + 70} fontSize="11" fontFamily="monospace">
                <tspan fill={hb.delta < 0 ? GO : FOUL}>{`Δ ${signed(hb.delta)}s`}</tspan>
                <tspan fill={cssVar('--fg', 0.7)}>{`  ${shortSource(hb.source)}`}</tspan>
              </text>
            </g>
          )}
        </svg>

        {/* legend — confidence encoding */}
        <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 px-1">
          <span className="label-mono">Benchmark source confidence</span>
          {[
            { w: 1.0, label: 'Instrumented' },
            { w: 0.7, label: 'Magazine' },
            { w: 0.5, label: 'Aggregator' },
            { w: 0.1, label: 'Derived (0-100×1.6 est)' },
          ].map((s) => {
            const { r, o } = dotStyle(s.w);
            return (
              <span key={s.label} className="inline-flex items-center gap-1.5 text-xs text-white/65">
                <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
                  <circle cx="8" cy="8" r={r} fill={ACCENT} fillOpacity={o} />
                </svg>
                {s.label}
              </span>
            );
          })}
          {clipped > 0 && (
            <span className="text-xs text-white/65 font-mono">
              · {clipped} slow outlier{clipped > 1 ? 's' : ''} drawn at the {hi}s edge
            </span>
          )}
        </div>
      </div>

      {/* accessible table fallback */}
      <details className="mt-4 group">
        <summary className="cursor-pointer label-mono hover:text-accent transition-colors select-none">
          Show all {bikes.length} matched benchmarks as a table ▸
        </summary>
        <div className="mt-3 overflow-x-auto card">
          <table className="w-full text-left border-collapse min-w-[640px]">
            <thead>
              <tr className="text-xs font-medium text-white/65 border-b border-white/10">
                <th className="px-3 py-2 font-medium">Bike</th>
                <th className="px-3 py-2 font-medium">Year</th>
                <th className="px-3 py-2 font-medium text-right">Real</th>
                <th className="px-3 py-2 font-medium text-right">Sim</th>
                <th className="px-3 py-2 font-medium text-right">Δ</th>
                <th className="px-3 py-2 font-medium">Source</th>
              </tr>
            </thead>
            <tbody>
              {[...bikes]
                .sort((a, b) => a.abs_delta - b.abs_delta)
                .map((b, i) => (
                  <tr key={i} className="border-b border-white/[0.04] last:border-0 text-sm">
                    <td className="px-3 py-1.5 text-white/85 whitespace-nowrap">{b.make} {b.model}</td>
                    <td className="px-3 py-1.5 text-white/65 font-mono text-xs">{b.year}</td>
                    <td className="px-3 py-1.5 text-right font-mono text-white/70 tabular-nums">{b.real_et}s</td>
                    <td className="px-3 py-1.5 text-right font-mono text-white/70 tabular-nums">{b.sim_et}s</td>
                    <td className={`px-3 py-1.5 text-right ${b.delta > 0 ? 'delta-up' : 'delta-down'}`}>{signed(b.delta)}s</td>
                    <td className="px-3 py-1.5 text-white/65 text-xs">{shortSource(b.source)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// 2. DISTRIBUTION TILES
// ─────────────────────────────────────────────────────────────────────────
function StatTile({ value, unit, pre, label, sub }) {
  return (
    <div className="card p-4 sm:p-5 flex flex-col">
      <div className="flex items-end gap-1 leading-none min-h-[28px]">
        {pre && <span className="font-mono text-sm mb-0.5 text-white/65">{pre}</span>}
        <ScoreboardDigits value={value} h={28} label={`${pre || ''}${value}${unit || ''}`} />
        {unit && <span className="font-mono text-xs text-white/65 mb-0.5">{unit}</span>}
      </div>
      <div className="label-mono mt-3">{label}</div>
      {sub && <div className="font-mono text-xs text-white/65 mt-1">{sub}</div>}
    </div>
  );
}

function Distribution({ dist, overall, n, topTen }) {
  const pct = (c) => `${Math.round((c / n) * 100)}% of ${n}`;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatTile value={dist.within_0_05} label="Within ±0.05s" sub={pct(dist.within_0_05)} />
        <StatTile value={dist.within_0_10} label="Within ±0.10s" sub={pct(dist.within_0_10)} />
        <StatTile value={dist.within_0_20} label="Within ±0.20s" sub={pct(dist.within_0_20)} />
        <StatTile value={dist.within_0_50} label="Within ±0.50s" sub={pct(dist.within_0_50)} />
      </div>
      <div className="grid grid-cols-3 gap-3">
        <StatTile value={overall.w_mean_abs.toFixed(2)} unit="s" label="Weighted |Δ|" sub="mean absolute error" />
        <StatTile
          value={Math.abs(overall.w_bias).toFixed(3)}
          unit="s"
          pre={overall.w_bias < 0 ? '−' : '+'}
          label="Weighted bias"
          sub={overall.w_bias < 0 ? 'sim slightly faster' : 'sim slightly slower'}
        />
        <StatTile value={topTen.toFixed(3)} unit="s" pre="±" label="Top-10 cleanest" sub="mean |Δ| of the 10 best published runs" />
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// 3. RESIDUAL HISTOGRAM
// ─────────────────────────────────────────────────────────────────────────
function Histogram({ bikes, bias }) {
  const [hover, setHover] = useState(null);
  const BINW = 0.1;
  const BMIN = -1.05;
  const NB = 21; // centre bin [-0.05,0.05) sits on zero
  const bins = useMemo(() => {
    const arr = Array.from({ length: NB }, () => 0);
    bikes.forEach((b) => {
      const d = clamp(b.delta, BMIN, BMIN + NB * BINW - 1e-9);
      const idx = clamp(Math.floor((d - BMIN) / BINW), 0, NB - 1);
      arr[idx]++;
    });
    return arr;
  }, [bikes]);

  const maxCount = Math.max(...bins);
  const M = { l: 34, r: 14, t: 14, b: 34 };
  const PW = 620;
  const PH = 210;
  const W = M.l + PW + M.r;
  const H = M.t + PH + M.b;
  const bw = PW / NB;
  const cx = (i) => M.l + i * bw;
  const cy = (c) => M.t + (1 - c / maxCount) * PH;
  const center = (i) => BMIN + (i + 0.5) * BINW;
  const colorFor = (i) => {
    const c = center(i);
    if (c < -0.05) return GO;
    if (c > 0.05) return FOUL;
    return NEUTRAL_BIN;
  };
  const dx = M.l + ((clamp(bias, BMIN, BMIN + NB * BINW) - BMIN) / (NB * BINW)) * PW;

  const xLabels = [-1, -0.5, 0, 0.5, 1];

  return (
    <div className="card p-3 sm:p-4">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto block" role="img" aria-label="Histogram of the residual delta (sim minus real) across all matched benchmarks, sharply centred near zero.">
        {/* count gridlines */}
        {[0.25, 0.5, 0.75, 1].map((f) => (
          <line key={f} x1={M.l} y1={cy(maxCount * f)} x2={M.l + PW} y2={cy(maxCount * f)} stroke={GRID} strokeWidth="0.75" />
        ))}
        {/* zero line */}
        <line x1={M.l + PW / 2} y1={M.t} x2={M.l + PW / 2} y2={M.t + PH} stroke={cssVar('--fg', 0.35)} strokeWidth="1" strokeDasharray="3 4" />

        {/* bars */}
        {bins.map((c, i) => {
          if (c === 0) return null;
          const isH = hover === i;
          return (
            <rect
              key={i}
              x={cx(i) + 1}
              y={cy(c)}
              width={bw - 2}
              height={M.t + PH - cy(c)}
              fill={colorFor(i)}
              fillOpacity={isH ? 1 : 0.82}
              onMouseEnter={() => setHover(i)}
              onMouseLeave={() => setHover(null)}
              style={{ cursor: 'pointer' }}
            >
              <title>{`Δ ${center(i).toFixed(2)}±0.05s: ${c} bike${c > 1 ? 's' : ''}`}</title>
            </rect>
          );
        })}

        {/* mean-bias marker — the one orange detail on this panel */}
        <line x1={dx} y1={M.t - 2} x2={dx} y2={M.t + PH} stroke={ACCENT} strokeWidth="1.4" />
        <text x={dx} y={M.t - 4} fill={ACCENT} opacity="0.9" fontSize="10" fontFamily="monospace" textAnchor="middle">
          bias {signed(bias)}s
        </text>

        {/* x labels */}
        {xLabels.map((v) => {
          const x = M.l + ((v - BMIN) / (NB * BINW)) * PW;
          return (
            <text key={v} x={x} y={M.t + PH + 18} fill={FG} opacity="0.7" fontSize="10" fontFamily="monospace" textAnchor="middle">
              {v > 0 ? `+${v}` : v}
            </text>
          );
        })}
        <text x={M.l} y={H - 3} fill={GO} opacity="0.8" fontSize="9.5" fontFamily="monospace">◀ sim faster</text>
        <text x={M.l + PW} y={H - 3} fill={FOUL} opacity="0.8" fontSize="9.5" fontFamily="monospace" textAnchor="end">sim slower ▶</text>

        {/* hover count */}
        {hover != null && bins[hover] > 0 && (
          <text x={cx(hover) + bw / 2} y={cy(bins[hover]) - 5} fill={FG} fontSize="10.5" fontFamily="monospace" textAnchor="middle" fontWeight="600">
            {bins[hover]}
          </text>
        )}
      </svg>
      <p className="mt-2 px-1 text-xs text-white/65 font-mono">
        Δ = simulated − real. {bikes.length} benchmarks binned at 0.1s; most sit inside ±0.2s, centred on a near-zero bias.
      </p>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// 4. PER-CLUSTER BARS
// ─────────────────────────────────────────────────────────────────────────
function ClusterBreakdown({ clusters }) {
  const rows = useMemo(
    () => Object.values(clusters).sort((a, b) => a.w_mean_abs - b.w_mean_abs),
    [clusters],
  );
  const DOMAIN = 0.9;
  const barCls = (mae) =>
    mae < 0.2 ? 'bg-signal-go' : mae < 0.5 ? 'bg-signal-stage' : 'bg-signal-foul';
  return (
    <div className="card p-4 sm:p-6">
      <div className="space-y-3.5">
        {rows.map((c) => {
          const w = Math.min(100, (c.w_mean_abs / DOMAIN) * 100);
          return (
            <div key={c.label} className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-4 gap-y-1">
              <div className="min-w-0">
                <div className="flex items-baseline gap-2">
                  <span className="font-display font-semibold text-sm text-white truncate">{c.label}</span>
                  <span className="font-mono text-xs text-white/65 shrink-0">N={c.n}</span>
                </div>
              </div>
              <div className="flex items-center gap-3 justify-self-end">
                <span className="font-mono text-xs text-white/65 tabular-nums w-16 text-right">bias {signed(c.w_bias, 2)}</span>
                <StatusChip mae={c.w_mean_abs} />
              </div>
              <div className="col-span-2 flex items-center gap-3">
                <div className="h-2.5 flex-1 rounded-full bg-white/[0.05] overflow-hidden">
                  <div
                    className={`h-full rounded-full ${barCls(c.w_mean_abs)}`}
                    style={{ width: `${w}%` }}
                  />
                </div>
                <span className="font-mono text-sm text-white tabular-nums w-14 text-right">{c.w_mean_abs.toFixed(3)}s</span>
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-5 flex flex-wrap items-center gap-x-5 gap-y-1.5 text-xs text-white/65">
        <span className="label-mono">Weighted |Δ|</span>
        <span className="inline-flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-signal-go" /> tight &lt; 0.20s</span>
        <span className="inline-flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-signal-stage" /> fair &lt; 0.50s</span>
        <span className="inline-flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-signal-foul" /> wide ≥ 0.50s</span>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// 5. BEST PREDICTIONS
// ─────────────────────────────────────────────────────────────────────────
function BestPredictions({ bikes }) {
  const top = useMemo(
    () =>
      [...bikes]
        .filter((b) => b.quality !== 'derived')
        .sort((a, b) => a.abs_delta - b.abs_delta)
        .slice(0, 10),
    [bikes],
  );
  return (
    <div className="card overflow-hidden">
      <div className="flex items-center justify-between gap-3 px-4 sm:px-5 py-2.5 border-b border-dashed border-white/15 bg-asphalt-1/70">
        <span className="label-mono">MotoQuant timing assoc · cleanest published runs</span>
        <span className="hidden sm:block text-xs text-white/65">10 smallest |Δ| · non-derived</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse min-w-[600px]">
          <thead>
            <tr className="text-xs font-medium text-white/65 border-b border-white/10 bg-white/[0.02]">
              <th className="px-4 py-2.5 font-medium">#</th>
              <th className="px-4 py-2.5 font-medium">Bike</th>
              <th className="px-4 py-2.5 font-medium text-right">Real ET</th>
              <th className="px-4 py-2.5 font-medium text-right">Sim ET</th>
              <th className="px-4 py-2.5 font-medium text-right">Δ</th>
              <th className="px-4 py-2.5 font-medium">Source</th>
            </tr>
          </thead>
          <tbody>
            {top.map((b, i) => (
              <tr key={i} className="border-b border-white/[0.04] last:border-0 hover:bg-white/[0.03] transition-colors">
                <td className="px-4 py-3 font-mono text-white/65 tabular-nums">{i + 1}</td>
                <td className="px-4 py-3">
                  <div className="font-display font-semibold text-white text-sm whitespace-nowrap">{b.make} {b.model}</div>
                  <div className="font-mono text-xs text-white/65">{b.year} · {b.disp_cc}cc</div>
                </td>
                <td className="px-4 py-3 text-right font-mono text-white/70 tabular-nums text-sm">{b.real_et.toFixed(2)}s</td>
                <td className="px-4 py-3 text-right font-mono text-white tabular-nums text-sm font-semibold">{b.sim_et.toFixed(2)}s</td>
                <td className={`px-4 py-3 text-right text-sm font-semibold ${b.delta > 0 ? 'delta-up' : 'delta-down'}`}>{signed(b.delta)}s</td>
                <td className="px-4 py-3 font-mono text-xs text-white/65">{shortSource(b.source)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// SECTION SHELL
// ─────────────────────────────────────────────────────────────────────────
function Section({ kicker, title, sub, children }) {
  return (
    <section className="mb-16 md:mb-24">
      <div>
        <div className="mb-6 max-w-2xl">
          <p className="eyebrow mb-2">{kicker}</p>
          <h2 className="font-display font-bold text-3xl md:text-4xl tracking-tight text-white">{title}</h2>
          {sub && <p className="mt-3 text-white/75 text-base leading-relaxed">{sub}</p>}
        </div>
      </div>
      <div>{children}</div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────
export default function AccuracyExplorer({ data }) {
  const { bikes, distribution, overall, clusters, references, n_matched } = data;

  const topTen = useMemo(() => {
    // Same set as the "closest matches" table: published runs only, DERIVED
    // estimates excluded.
    const cleanest = [...bikes]
      .filter((b) => b.quality !== 'derived')
      .sort((a, b) => a.abs_delta - b.abs_delta)
      .slice(0, 10);
    return cleanest.reduce((s, b) => s + b.abs_delta, 0) / cleanest.length;
  }, [bikes]);

  const REFS = [
    { name: 'GSX-R 1000 K5', et: references.K5 },
    { name: 'YZF-R1 4C8', et: references.R1 },
    { name: 'Hayabusa Gen1', et: references.Hayabusa },
  ];

  return (
    <div className="max-w-6xl mx-auto px-6 pb-24">
      {/* reference-baseline strip */}
      <div>
        <div className="card px-4 sm:px-6 py-4 mb-14 flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-8">
          <div className="text-sm text-white/70 shrink-0">Reference bikes, unchanged since July 2026</div>
          <div className="flex flex-wrap gap-x-8 gap-y-2">
            {REFS.map((r) => (
              <div key={r.name} className="flex items-baseline gap-2">
                <span className="font-mono text-xs text-white/70">{r.name}</span>
                <span className="font-mono text-sm text-white tabular-nums font-semibold">{r.et.toFixed(4)}s</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <Section
        kicker="Real vs simulated"
        title={<>Every prediction against its <span className="text-accent">timeslip</span></>}
        sub={`One dot per matched benchmark: the published real ET on the x-axis, MotoQuant's simulated ET on the y-axis, on the same scale. The dashed line is a perfect prediction; the shaded stripe is the ±0.2s tolerance band that instrumented magazine tests report as their own run-to-run spread. Larger, more solid dots come from more trusted sources, so the low-confidence DERIVED estimates fade into the background.`}
      >
        <Scatter bikes={bikes} />
      </Section>

      <Section
        kicker="The numbers"
        title={<>Where the <span className="text-accent">residuals</span> land</>}
        sub={`Across ${n_matched} matched benchmarks the model is centred close to zero, and more than half land inside a fifth of a second.`}
      >
        <Distribution dist={distribution} overall={overall} n={n_matched} topTen={topTen} />
      </Section>

      <Section
        kicker="Residual shape"
        title={<>A tight, <span className="text-accent">near-symmetric</span> error distribution</>}
        sub="The residual Δ = sim − real, binned at 0.1s. Green bins are runs the simulator calls faster than reality, red bins slower. Most runs stack up in the centre, and the bias is very small."
      >
        <Histogram bikes={bikes} bias={overall.w_bias} />
      </Section>

      <Section
        kicker="By segment"
        title={<>Litre classes are <span className="text-accent">tight</span>; small bikes are the weakest</>}
        sub="Weighted mean absolute error for each of the 12 clusters, which group bikes by cylinder layout as well as size (twins, singles and small-cc I4s are kept apart from same-displacement I4s). The litre and 500–700cc mid-twin clusters (the ones with the most instrumented timeslips) sit under 0.20s, and sport twins sit just above it. The wide clusters are the small-cc and two-stroke bikes: their benchmarks are mostly DERIVED estimates, and small bikes are also where the model is weakest."
      >
        <ClusterBreakdown clusters={clusters} />
      </Section>

      <Section
        kicker="Cleanest predictions"
        title={<>Ten runs, ten <span className="text-accent">real</span> timeslips</>}
        sub="The ten smallest residuals among fully published (non-derived) benchmarks: Cycle World, Sport Rider, MCN, MotoStatz, FastestLaps. Conditions: race fuel, professional rider, ideal strip."
      >
        <BestPredictions bikes={bikes} />
        {/* honest callout */}
        <div className="mt-6 card border-signal-stage/25 bg-signal-stage/[0.04] p-5 sm:p-6">
          <div className="label-mono text-signal-stage mb-2">Caveat</div>
          <p className="text-white/75 text-base leading-relaxed">
            The <span className="text-white font-semibold">entry 150–200cc</span> and{' '}
            <span className="text-white font-semibold">two-stroke</span> clusters carry large |Δ| because most of their
            benchmarks are <span className="text-signal-stage font-mono">DERIVED</span>: 0-100 km/h times multiplied by 1.6,
            with a declared ±0.7s uncertainty, so part of the spread comes from the benchmark data itself. Small bikes are also the
            weakest class of the simulator: many of them still carry a known gearing limitation, documented in{' '}
            <a
              href="https://github.com/toto171/MotoQuant.in/blob/main/reports/session_2026_11_10_epoch.md"
              className="text-accent hover:text-accent-bright underline underline-offset-2 transition-colors"
              rel="noopener"
            >
              the repository
            </a>
            . A single real Dragy timeslip replaces an estimate and collapses its residual. If you have run your bike,{' '}
            <Link href="/simulator" className="text-accent hover:text-accent-bright underline underline-offset-2 transition-colors">
              simulate it
            </Link>{' '}
            and send us your slip. Measured data goes straight into the corpus.
          </p>
        </div>
      </Section>

      {/* cross-links */}
      <div className="pt-8 border-t border-white/10 grid sm:grid-cols-2 gap-4">
        <Link href="/docs/validation" className="card card-hover block p-4 group">
          <div className="font-display font-semibold text-white mb-1 group-hover:text-accent transition-colors">Per-bike benchmark table →</div>
          <div className="text-sm text-white/65">Methodology, per-cluster bias, and the full source list.</div>
        </Link>
        <Link href="/whitepaper" className="card card-hover block p-4 group">
          <div className="font-display font-semibold text-white mb-1 group-hover:text-accent transition-colors">Read the whitepaper →</div>
          <div className="text-sm text-white/65">The physics, the validation method and the error budget.</div>
        </Link>
      </div>
    </div>
  );
}
