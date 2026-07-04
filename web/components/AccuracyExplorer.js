'use client';

/**
 * AccuracyExplorer — the flagship "real vs simulated" accuracy surface.
 *
 * Everything is computed from web/app/validation/accuracy_data.json (passed
 * in as `data`) so the page can never drift from the sweep. Five panels:
 *
 *   1. HERO scatter  — real ET (x) vs sim ET (y), same scale both axes,
 *      a dashed y=x perfect-prediction diagonal + a ±0.2s tolerance band.
 *      Source confidence is encoded as dot opacity + radius, so the low-
 *      confidence DERIVED estimates visibly recede — that's the honesty
 *      story. Single hue (brand-orange). Hover tooltip + filter + a table
 *      fallback for screen readers / no-hover.
 *   2. DISTRIBUTION  — timing-board stat tiles (within ±0.05/0.10/0.20/0.50,
 *      overall |Δ|, mean bias, top-10 cleanest).
 *   3. RESIDUAL HISTOGRAM — Δ = sim−real, diverging mint (sim faster) /
 *      amber (sim slower), neutral centre, mean-bias marker.
 *   4. PER-CLUSTER — horizontal weighted-|Δ| bars, status-coloured with the
 *      numeric label always present (colour is never the only signal).
 *   5. BEST PREDICTIONS — the ten cleanest published (non-derived) runs,
 *      plus the honest callout about the DERIVED entry-cc / 2T benchmarks.
 *
 * Dark cockpit identity (the site is dark-only — no theme toggle exists).
 * Reduced-motion safe (Reveal handles it; the SVGs are static + hover-only).
 * Responsive: SVGs scale via viewBox (no body overflow); the wide table
 * scrolls inside its own overflow-x container.
 */

import { useState, useMemo } from 'react';
import Link from 'next/link';
import { Reveal } from './Reveal';
import ScoreboardDigits from './ScoreboardDigits';

const ORANGE = '#FF5E1F';
const MINT = '#00FFB2';
const AMBER = '#F59E0B';
const NEUTRAL = '#52525B';

const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const signed = (n, d = 3) => (n > 0 ? '+' : n < 0 ? '−' : '±') + Math.abs(n).toFixed(d);

// Short, human source label for the tooltip / table.
function shortSource(src) {
  if (!src) return '—';
  const cut = src.split('(')[0].trim();
  return cut.length > 30 ? cut.slice(0, 29) + '…' : cut;
}

function StatusPill({ mae }) {
  const status = mae < 0.2 ? 'tight' : mae < 0.5 ? 'fair' : 'data-limited';
  const cls =
    mae < 0.2
      ? 'bg-brand-green/10 text-brand-green'
      : mae < 0.5
        ? 'bg-brand-amber/10 text-brand-amber'
        : 'bg-brand-red/10 text-brand-red';
  return (
    <span className={`px-2 py-0.5 rounded text-[9px] font-mono uppercase tracking-wide ${cls}`}>
      {status}
    </span>
  );
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
                'px-3 py-1.5 rounded-full font-mono text-[10px] uppercase tracking-[0.15em] transition-colors',
                on
                  ? 'border border-brand-orange/60 bg-brand-orange/15 text-brand-orange'
                  : 'border border-white/12 bg-white/[0.02] text-white/55 hover:text-white hover:border-white/30',
              ].join(' ')}
            >
              {f.label}
            </button>
          );
        })}
      </div>

      <div className="card border-white/10 p-3 sm:p-4">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="w-full h-auto block"
          role="img"
          aria-label="Scatter plot of real quarter-mile ET versus simulated ET for every matched benchmark. Dots cluster tightly on the perfect-prediction diagonal."
        >
          {/* plot frame */}
          <rect x={M.l} y={M.t} width={S} height={S} fill="#0A0A0B" stroke="#27272A" strokeWidth="1" />

          {/* ±0.2s tolerance band */}
          <polygon points={band} fill="rgba(255,94,31,0.07)" />

          {/* gridlines + tick labels */}
          {ticks.map((t) => (
            <g key={t}>
              <line x1={sx(t)} y1={M.t} x2={sx(t)} y2={M.t + S} stroke="#1A1A1D" strokeWidth="0.75" />
              <line x1={M.l} y1={sy(t)} x2={M.l + S} y2={sy(t)} stroke="#1A1A1D" strokeWidth="0.75" />
              <text x={sx(t)} y={M.t + S + 16} fill="#FFFFFF" opacity="0.4" fontSize="10" fontFamily="monospace" textAnchor="middle">
                {t}
              </text>
              <text x={M.l - 8} y={sy(t) + 3.5} fill="#FFFFFF" opacity="0.4" fontSize="10" fontFamily="monospace" textAnchor="end">
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
            stroke="#FF8F57"
            strokeWidth="1.4"
            strokeDasharray="6 5"
            opacity="0.85"
          />
          <text
            x={sx(hi) - 4}
            y={sy(hi) + 16}
            fill="#FF8F57"
            opacity="0.9"
            fontSize="10.5"
            fontFamily="monospace"
            textAnchor="end"
          >
            perfect prediction · sim = real
          </text>

          {/* axis titles */}
          <text x={M.l + S / 2} y={H - 4} fill="#FFFFFF" opacity="0.55" fontSize="11" fontFamily="monospace" textAnchor="middle">
            REAL ET (s) — published timeslip
          </text>
          <text
            x={14}
            y={M.t + S / 2}
            fill="#FFFFFF"
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
                fill={ORANGE}
                fillOpacity={isH ? 1 : o}
                stroke={isH ? '#FFFFFF' : 'none'}
                strokeWidth={isH ? 1.2 : 0}
                onMouseEnter={() => setHover(i)}
                onMouseLeave={() => setHover(null)}
                style={{ cursor: 'pointer' }}
              >
                <title>{`${b.make} ${b.model} (${b.year}) — real ${b.real_et}s / sim ${b.sim_et}s / Δ ${signed(b.delta)}s`}</title>
              </circle>
            );
          })}

          {/* hover tooltip */}
          {tip && (
            <g pointerEvents="none">
              <line x1={tip.px} y1={tip.py} x2={tip.x + (tip.x < tip.px ? tip.tw : 0)} y2={tip.y + tip.th / 2} stroke="#FF5E1F" strokeWidth="0.75" opacity="0.5" />
              <rect x={tip.x} y={tip.y} width={tip.tw} height={tip.th} rx="7" fill="#111113" stroke="#FF5E1F" strokeOpacity="0.5" strokeWidth="1" />
              <text x={tip.x + 12} y={tip.y + 20} fill="#FFFFFF" fontSize="12" fontFamily="monospace" fontWeight="600">
                {`${hb.make} ${hb.model}`.slice(0, 26)}
              </text>
              <text x={tip.x + 12} y={tip.y + 36} fill="#A1A1AA" fontSize="10.5" fontFamily="monospace">
                {`${hb.year} · ${hb.disp_cc}cc · ${hb.cluster_label}`.slice(0, 32)}
              </text>
              <text x={tip.x + 12} y={tip.y + 53} fill="#FFFFFF" fontSize="11" fontFamily="monospace">
                {`real ${hb.real_et}s   sim ${hb.sim_et}s`}
              </text>
              <text x={tip.x + 12} y={tip.y + 70} fontSize="11" fontFamily="monospace">
                <tspan fill={hb.delta < 0 ? MINT : AMBER}>{`Δ ${signed(hb.delta)}s`}</tspan>
                <tspan fill="#A1A1AA">{`  ${shortSource(hb.source)}`}</tspan>
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
              <span key={s.label} className="inline-flex items-center gap-1.5 text-[11px] text-white/55">
                <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
                  <circle cx="8" cy="8" r={r} fill={ORANGE} fillOpacity={o} />
                </svg>
                {s.label}
              </span>
            );
          })}
          {clipped > 0 && (
            <span className="text-[11px] text-white/35 font-mono">
              · {clipped} slow outlier{clipped > 1 ? 's' : ''} clamped to the {hi}s edge
            </span>
          )}
        </div>
      </div>

      {/* accessible table fallback */}
      <details className="mt-4 group">
        <summary className="cursor-pointer label-mono text-white/50 hover:text-brand-orange transition-colors select-none">
          Show all {bikes.length} matched benchmarks as a table ▸
        </summary>
        <div className="mt-3 overflow-x-auto card border-white/10">
          <table className="w-full text-left border-collapse min-w-[640px]">
            <thead>
              <tr className="text-[10px] font-mono uppercase tracking-widest text-white/45 border-b border-white/10">
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
                    <td className="px-3 py-1.5 text-white/45 font-mono text-xs">{b.year}</td>
                    <td className="px-3 py-1.5 text-right font-mono text-white/70 tabular-nums">{b.real_et}s</td>
                    <td className="px-3 py-1.5 text-right font-mono text-white/70 tabular-nums">{b.sim_et}s</td>
                    <td className={`px-3 py-1.5 text-right font-mono tabular-nums ${b.delta < 0 ? 'text-brand-accent' : 'text-brand-amber'}`}>{signed(b.delta)}s</td>
                    <td className="px-3 py-1.5 text-white/40 text-xs">{shortSource(b.source)}</td>
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
function StatTile({ value, unit, pre, label, sub, accent = true }) {
  return (
    <div className="card border-brand-orange/15 p-4 sm:p-5 flex flex-col">
      <div className="flex items-end gap-1 leading-none min-h-[26px]">
        {pre && <span className={`font-mono text-sm mb-0.5 ${accent ? 'text-brand-orange' : 'text-white/50'}`}>{pre}</span>}
        <ScoreboardDigits value={value} h={26} color={accent ? ORANGE : '#FFFFFF'} label={`${pre || ''}${value}${unit || ''}`} />
        {unit && <span className="font-mono text-xs text-white/40 mb-0.5">{unit}</span>}
      </div>
      <div className="font-mono text-[10px] text-white/50 uppercase tracking-[0.18em] mt-3">{label}</div>
      {sub && <div className="font-mono text-[10px] text-white/35 mt-1">{sub}</div>}
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
        <StatTile value={topTen.toFixed(3)} unit="s" pre="±" label="Top-10 cleanest" sub="mean |Δ| of the 10 best" />
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
    if (c < -0.05) return MINT;
    if (c > 0.05) return AMBER;
    return NEUTRAL;
  };
  const dx = M.l + ((clamp(bias, BMIN, BMIN + NB * BINW) - BMIN) / (NB * BINW)) * PW;

  const xLabels = [-1, -0.5, 0, 0.5, 1];

  return (
    <div className="card border-white/10 p-3 sm:p-4">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto block" role="img" aria-label="Histogram of the residual delta (sim minus real) across all matched benchmarks, sharply centred near zero.">
        {/* count gridlines */}
        {[0.25, 0.5, 0.75, 1].map((f) => (
          <line key={f} x1={M.l} y1={cy(maxCount * f)} x2={M.l + PW} y2={cy(maxCount * f)} stroke="#1A1A1D" strokeWidth="0.75" />
        ))}
        {/* zero line */}
        <line x1={M.l + PW / 2} y1={M.t} x2={M.l + PW / 2} y2={M.t + PH} stroke="#3F3F46" strokeWidth="1" strokeDasharray="3 4" />

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
              <title>{`Δ ${center(i).toFixed(2)}±0.05s — ${c} bike${c > 1 ? 's' : ''}`}</title>
            </rect>
          );
        })}

        {/* mean-bias marker */}
        <line x1={dx} y1={M.t - 2} x2={dx} y2={M.t + PH} stroke="#FF5E1F" strokeWidth="1.4" />
        <text x={dx} y={M.t - 4} fill="#FF8F57" fontSize="10" fontFamily="monospace" textAnchor="middle">
          bias {signed(bias)}s
        </text>

        {/* x labels */}
        {xLabels.map((v) => {
          const x = M.l + ((v - BMIN) / (NB * BINW)) * PW;
          return (
            <text key={v} x={x} y={M.t + PH + 18} fill="#FFFFFF" opacity="0.4" fontSize="10" fontFamily="monospace" textAnchor="middle">
              {v > 0 ? `+${v}` : v}
            </text>
          );
        })}
        <text x={M.l} y={H - 3} fill={MINT} opacity="0.7" fontSize="9.5" fontFamily="monospace">◀ sim faster</text>
        <text x={M.l + PW} y={H - 3} fill={AMBER} opacity="0.75" fontSize="9.5" fontFamily="monospace" textAnchor="end">sim slower ▶</text>

        {/* hover count */}
        {hover != null && bins[hover] > 0 && (
          <text x={cx(hover) + bw / 2} y={cy(bins[hover]) - 5} fill="#FFFFFF" fontSize="10.5" fontFamily="monospace" textAnchor="middle" fontWeight="600">
            {bins[hover]}
          </text>
        )}
      </svg>
      <p className="mt-2 px-1 text-[11px] text-white/45 font-mono">
        Δ = simulated − real. {bikes.length} benchmarks binned at 0.1s; the mass sits inside ±0.2s, centred on a near-zero bias.
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
  const fill = (mae) => (mae < 0.2 ? '#22C55E' : mae < 0.5 ? '#F59E0B' : '#EF4444');
  return (
    <div className="card border-white/10 p-4 sm:p-6">
      <div className="space-y-3.5">
        {rows.map((c) => {
          const w = Math.min(100, (c.w_mean_abs / DOMAIN) * 100);
          return (
            <div key={c.label} className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-4 gap-y-1">
              <div className="min-w-0">
                <div className="flex items-baseline gap-2">
                  <span className="font-display font-semibold text-sm text-white truncate">{c.label}</span>
                  <span className="font-mono text-[10px] text-white/40 shrink-0">N={c.n}</span>
                </div>
              </div>
              <div className="flex items-center gap-3 justify-self-end">
                <span className="font-mono text-xs text-white/45 tabular-nums w-16 text-right">bias {signed(c.w_bias, 2)}</span>
                <StatusPill mae={c.w_mean_abs} />
              </div>
              <div className="col-span-2 flex items-center gap-3">
                <div className="h-2.5 flex-1 rounded-full bg-white/[0.05] overflow-hidden">
                  <div
                    className="h-full rounded-full transition-[width] duration-500"
                    style={{ width: `${w}%`, backgroundColor: fill(c.w_mean_abs) }}
                  />
                </div>
                <span className="font-mono text-sm text-white tabular-nums w-14 text-right">{c.w_mean_abs.toFixed(3)}s</span>
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-5 flex flex-wrap items-center gap-x-5 gap-y-1.5 text-[11px] text-white/45">
        <span className="label-mono">Weighted |Δ|</span>
        <span className="inline-flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: '#22C55E' }} /> tight &lt; 0.20s</span>
        <span className="inline-flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: '#F59E0B' }} /> fair &lt; 0.50s</span>
        <span className="inline-flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: '#EF4444' }} /> data-limited ≥ 0.50s</span>
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
    <div className="card border-brand-orange/20 overflow-hidden">
      <div className="flex items-center justify-between gap-3 px-4 sm:px-5 py-2.5 border-b border-dashed border-white/15 bg-ink-1/70">
        <span className="font-mono text-[10px] tracking-[0.2em] uppercase text-white/45">MotoQuant timing assoc · cleanest published runs</span>
        <span className="hidden sm:block font-mono text-[10px] tracking-[0.18em] uppercase text-brand-orange/80">10 smallest |Δ| · non-derived</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse min-w-[600px]">
          <thead>
            <tr className="text-[10px] font-mono uppercase tracking-widest text-white/45 border-b border-brand-orange/20 bg-white/[0.02]">
              <th className="px-4 py-2.5 font-medium">#</th>
              <th className="px-4 py-2.5 font-medium">Bike</th>
              <th className="px-4 py-2.5 font-medium text-right">Real ET</th>
              <th className="px-4 py-2.5 font-medium text-right">Sim ET</th>
              <th className="px-4 py-2.5 font-medium text-right">Δ</th>
              <th className="px-4 py-2.5 font-medium">Source</th>
            </tr>
          </thead>
          <tbody>
            {top.map((b, i) => {
              const abs = b.abs_delta;
              const col = abs < 0.05 ? 'text-brand-accent' : abs < 0.1 ? 'text-brand-green' : 'text-brand-amber';
              return (
                <tr key={i} className="border-b border-white/[0.04] last:border-0 hover:bg-brand-orange/[0.03] transition-colors">
                  <td className="px-4 py-3 font-display font-bold text-brand-orange">{i + 1}</td>
                  <td className="px-4 py-3">
                    <div className="font-display font-bold text-white text-sm whitespace-nowrap">{b.make} {b.model}</div>
                    <div className="font-mono text-[11px] text-white/40">{b.year} · {b.disp_cc}cc</div>
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-white/70 tabular-nums text-sm">{b.real_et.toFixed(2)}s</td>
                  <td className="px-4 py-3 text-right font-mono text-white tabular-nums text-sm font-semibold">{b.sim_et.toFixed(2)}s</td>
                  <td className={`px-4 py-3 text-right font-display font-bold tabular-nums text-sm ${col}`}>{signed(b.delta)}s</td>
                  <td className="px-4 py-3 font-mono text-[11px] text-white/40">{shortSource(b.source)}</td>
                </tr>
              );
            })}
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
      <Reveal>
        <div className="mb-6 max-w-2xl">
          <div className="label-mono text-brand-orange mb-2.5">{kicker}</div>
          <h2 className="font-display font-bold text-2xl sm:text-3xl text-white tracking-tight">{title}</h2>
          {sub && <p className="mt-3 text-white/60 text-sm sm:text-base leading-relaxed">{sub}</p>}
        </div>
      </Reveal>
      <Reveal delay={0.05}>{children}</Reveal>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────
export default function AccuracyExplorer({ data }) {
  const { bikes, distribution, overall, clusters, references, n_matched } = data;

  const topTen = useMemo(() => {
    const cleanest = [...bikes].sort((a, b) => a.abs_delta - b.abs_delta).slice(0, 10);
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
      <Reveal>
        <div className="card border-brand-orange/15 px-4 sm:px-6 py-4 mb-14 flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-8">
          <div className="label-mono text-white/50 shrink-0">Reference baselines · Δ ±0.0000 since Apr 2026</div>
          <div className="flex flex-wrap gap-x-8 gap-y-2">
            {REFS.map((r) => (
              <div key={r.name} className="flex items-baseline gap-2">
                <span className="font-mono text-xs text-white/55">{r.name}</span>
                <span className="font-mono text-sm text-brand-accent tabular-nums font-semibold">{r.et.toFixed(4)}s</span>
              </div>
            ))}
          </div>
        </div>
      </Reveal>

      <Section
        kicker="01 · real vs simulated"
        title="Every prediction against its timeslip"
        sub={`One dot per matched benchmark: the published real ET on the x-axis, MotoQuant's simulated ET on the y-axis, on the same scale. The dashed line is a perfect prediction; the shaded stripe is the ±0.2s tolerance band that instrumented magazine tests report as their own run-to-run spread. Dot weight = source confidence, so the low-confidence DERIVED estimates recede.`}
      >
        <Scatter bikes={bikes} />
      </Section>

      <Section
        kicker="02 · the numbers"
        title="Where the residuals land"
        sub={`Across ${n_matched} matched benchmarks the model is essentially centred at zero, and more than half land inside a fifth of a second.`}
      >
        <Distribution dist={distribution} overall={overall} n={n_matched} topTen={topTen} />
      </Section>

      <Section
        kicker="03 · residual shape"
        title="A tight, near-symmetric error distribution"
        sub="The residual Δ = sim − real, binned at 0.1s. Mint bins are runs we call faster than reality, amber bins slower; the mass is stacked on the centre with only a whisker of bias."
      >
        <Histogram bikes={bikes} bias={overall.w_bias} />
      </Section>

      <Section
        kicker="04 · by segment"
        title="Litre classes are tight; entry-cc is data-limited"
        sub="Weighted mean absolute error per cluster. The litre and mid-twin sport clusters — the ones with real instrumented timeslips — sit well under 0.20s. The wide clusters are the small-cc and two-stroke bikes whose benchmarks are DERIVED estimates, not a model failure."
      >
        <ClusterBreakdown clusters={clusters} />
      </Section>

      <Section
        kicker="05 · cleanest predictions"
        title="Ten runs, ten real timeslips"
        sub="The ten smallest residuals among fully published (non-derived) benchmarks — Cycle World, Sport Rider, MCN, MotoStatz, FastestLaps. Race fuel, professional rider, ideal strip."
      >
        <BestPredictions bikes={bikes} />
        {/* honest callout */}
        <div className="mt-6 card border-brand-amber/25 bg-brand-amber/[0.04] p-5 sm:p-6">
          <div className="label-mono text-brand-amber mb-2">Honest caveat · data, not physics</div>
          <p className="text-white/70 text-sm leading-relaxed">
            The <span className="text-white font-semibold">entry 150–200cc</span> and{' '}
            <span className="text-white font-semibold">two-stroke</span> clusters carry large |Δ| because most of their
            benchmarks are <span className="text-brand-amber font-mono">DERIVED</span> — 0-100 km/h times multiplied by 1.6,
            with a declared ±0.7s uncertainty. That is a benchmark-data limit, not a physics limit. A single real Dragy
            timeslip replaces the estimate and collapses the residual. If you have run your bike,{' '}
            <Link href="/simulator" className="text-brand-accent hover:text-white underline underline-offset-2 transition-colors">
              simulate it
            </Link>{' '}
            and send us your slip — measured data goes straight into the corpus.
          </p>
        </div>
      </Section>

      {/* cross-links */}
      <div className="pt-8 border-t border-brand-orange/10 grid sm:grid-cols-2 gap-4">
        <Link href="/docs/validation" className="card card-hover block p-4 group">
          <div className="font-display font-bold text-white mb-1 group-hover:text-brand-orange transition-colors">Per-bike benchmark table →</div>
          <div className="text-xs text-white/50">Methodology, per-cluster bias, and the full source list.</div>
        </Link>
        <Link href="/whitepaper" className="card card-hover block p-4 group">
          <div className="font-display font-bold text-white mb-1 group-hover:text-brand-orange transition-colors">Read the whitepaper →</div>
          <div className="text-xs text-white/50">The physics, the validation method, the honest error budget.</div>
        </Link>
      </div>
    </div>
  );
}
