'use client';

/**
 * TelemetryHUD — full-viewport section that plays a real Kawasaki
 * Ninja H2R quarter-mile run on scroll progress.
 *
 * July 2026 motion pass (field-reported fixes):
 *  - Responds from the moment the section peeks into the viewport
 *    (offset 'start 0.95' → 'end 0.35') instead of lagging the reader.
 *  - Scroll progress runs through a critically-damped spring, so the
 *    needle/values carry physical inertia instead of tracking raw
 *    scroll jitter (reduced-motion users get the raw, un-sprung value).
 *  - Right gauge column is minmax() responsive — the fixed 460px column
 *    could crowd the 1024-1150px laptop band.
 *  - SpeedTrace panel redesigned: speed axis, timing-split markers
 *    (60ft / ⅛ mile / 1000ft), gear-shift ticks on the curve, glowing
 *    live dot, and a 3D perspective entrance.
 *
 * Reference baseline (Motorcycle USA timeslip + Cycle World testing):
 *   Kawasaki Ninja H2R — 9.620s @ 257 km/h, finishing in gear 5,
 *   14,500 redline.
 */

import { useRef, useState, useMemo, useEffect } from 'react';
import {
  motion,
  useScroll,
  useSpring,
  useMotionValueEvent,
  useReducedMotion,
} from 'framer-motion';
import ScoreboardDigits from './ScoreboardDigits';

// Hand-curated waypoints for the H2R baseline run.
const RUN = [
  { t: 0.000,  v: 0,    g: 1, r: 4500,  d: 0      },
  { t: 0.600,  v: 80,   g: 1, r: 13500, d: 8      },
  { t: 1.200,  v: 130,  g: 2, r: 11000, d: 28     },
  { t: 2.000,  v: 175,  g: 2, r: 14000, d: 65     },
  { t: 2.700,  v: 200,  g: 3, r: 11500, d: 105    },
  { t: 3.600,  v: 225,  g: 3, r: 14000, d: 165    },
  { t: 4.500,  v: 240,  g: 4, r: 12500, d: 222    },
  { t: 5.700,  v: 250,  g: 4, r: 14000, d: 305    },
  { t: 7.000,  v: 254,  g: 5, r: 13500, d: 372    },
  { t: 9.620,  v: 257,  g: 5, r: 13800, d: 402.336 },
];

const TOTAL_T = 9.620;
const REDLINE = 14500;
const TRAP_KMH = 270;
const TRACK_M = 402.336;

// Timing splits interpolated from the RUN table (distance → time).
const SPLITS = [
  { t: 0.91, label: '60FT' },
  { t: 4.17, label: '⅛ MILE' },
  { t: 5.70, label: '1000FT' },
];
// Gear-shift moments (RUN waypoints where the gear increments).
const SHIFTS = [
  { t: 1.2, g: 2 },
  { t: 2.7, g: 3 },
  { t: 4.5, g: 4 },
  { t: 7.0, g: 5 },
];

function lerp(a, b, t) { return a + (b - a) * t; }

function sampleRun(progress) {
  const t = progress * TOTAL_T;
  let i = 0;
  while (i < RUN.length - 1 && RUN[i + 1].t < t) i++;
  const a = RUN[i];
  const b = RUN[Math.min(i + 1, RUN.length - 1)];
  const span = (b.t - a.t) || 1;
  const u = Math.min(1, Math.max(0, (t - a.t) / span));
  return {
    t,
    v: lerp(a.v, b.v, u),
    g: u > 0.5 ? b.g : a.g,
    r: lerp(a.r, b.r, u),
    d: lerp(a.d, b.d, u),
  };
}

function vAt(t) {
  let i = 0;
  while (i < RUN.length - 1 && RUN[i + 1].t < t) i++;
  const a = RUN[i];
  const b = RUN[Math.min(i + 1, RUN.length - 1)];
  const span = (b.t - a.t) || 1;
  return lerp(a.v, b.v, Math.min(1, Math.max(0, (t - a.t) / span)));
}

function Gauge({ label, value, unit, percent, accent = false, full = false, seg = false, shiftLight = null }) {
  return (
    <div
      className={[
        'min-w-0 rounded-xl border border-white/10 bg-white/[0.025] p-4 sm:p-5',
        full ? 'col-span-2' : '',
      ].join(' ')}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="text-[10px] font-mono uppercase tracking-widest text-white/45 truncate">
          {label}
        </div>
        {shiftLight && (
          <span
            aria-hidden="true"
            className={[
              'h-2 w-2 shrink-0 rounded-full transition-colors duration-100',
              shiftLight === 'red'
                ? 'bg-brand-red shadow-lamp-red'
                : shiftLight === 'amber'
                  ? 'bg-brand-amber shadow-lamp-amber'
                  : 'bg-white/15',
            ].join(' ')}
          />
        )}
      </div>
      <div className="mt-1.5 flex items-baseline gap-1.5 leading-none">
        {seg ? (
          <>
            <span className="flex sm:hidden"><ScoreboardDigits value={value} h={26} label={String(value)} /></span>
            <span className="hidden sm:flex"><ScoreboardDigits value={value} h={32} label={String(value)} /></span>
          </>
        ) : (
        <span
          className={[
            'font-mono font-bold tabular-nums text-3xl sm:text-4xl',
            accent ? 'text-brand-orange' : 'text-white',
          ].join(' ')}
        >
          {value}
        </span>
        )}
        {unit && <span className="font-mono text-xs text-white/45 whitespace-nowrap">{unit}</span>}
      </div>
      {percent != null && (
        <div className="mt-3 h-1.5 rounded-full bg-white/10 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-brand-green via-brand-amber to-brand-red transition-[width] duration-75"
            style={{ width: `${Math.min(100, Math.max(0, percent))}%` }}
          />
        </div>
      )}
    </div>
  );
}

// Speed-trace chart: v(t) with speed axis, timing splits, gear-shift ticks
// and a glowing live dot tracking the current run state.
function SpeedTrace({ currentV, currentT, progress }) {
  const tracePath = useMemo(() => {
    const N = 120;
    const pts = [];
    const fillPts = ['M 0 200'];
    for (let i = 0; i <= N; i++) {
      const u = i / N;
      const v = vAt(u * TOTAL_T);
      const x = u * 600;
      const y = 200 - (v / TRAP_KMH) * 170;
      pts.push(`${i === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`);
      fillPts.push(`L ${x.toFixed(1)} ${y.toFixed(1)}`);
    }
    fillPts.push('L 600 200 Z');
    return { stroke: pts.join(' '), fill: fillPts.join(' ') };
  }, []);

  const dotX = (currentT / TOTAL_T) * 600;
  const dotY = 200 - (currentV / TRAP_KMH) * 170;

  return (
    <div className="relative h-full min-h-[200px] sm:min-h-[280px] min-w-0 rounded-2xl border border-white/10 bg-gradient-to-br from-ink-1/80 to-black overflow-hidden">
      <span className="absolute top-3 left-3 w-6 h-6 border-t-2 border-l-2 border-brand-orange" />
      <span className="absolute bottom-3 right-3 w-6 h-6 border-b-2 border-r-2 border-brand-orange" />

      <div className="absolute top-3 left-10 right-10 sm:left-12 sm:right-12 flex justify-between items-baseline gap-2 z-10">
        <div className="font-mono text-[9px] sm:text-[10px] tracking-widest text-brand-orange/85 truncate">
          v(t) · NINJA H2R · 1/4 mile
        </div>
        <div className="flex items-center gap-1.5 font-mono text-[9px] sm:text-[10px] tracking-widest text-brand-accent shrink-0">
          <span className="w-1.5 h-1.5 rounded-full bg-brand-accent animate-live-pulse" />
          LIVE
        </div>
      </div>

      <svg viewBox="0 0 600 220" className="absolute inset-0 w-full h-full" preserveAspectRatio="none">
        <defs>
          <linearGradient id="vfill" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0" stopColor="#FF5E1F" stopOpacity="0.35" />
            <stop offset="1" stopColor="#FF5E1F" stopOpacity="0" />
          </linearGradient>
          <filter id="dot-glow" x="-80%" y="-80%" width="260%" height="260%">
            <feGaussianBlur stdDeviation="4" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <clipPath id="vfill-clip">
            <rect x="0" y="0" width={Math.max(0, Math.min(1, progress)) * 600} height="220" />
          </clipPath>
        </defs>

        {/* speed gridlines */}
        <g stroke="#27272A" strokeWidth="0.6" strokeDasharray="3 4">
          <line x1="0" y1="43.4"  x2="600" y2="43.4"  />
          <line x1="0" y1="86.7"  x2="600" y2="86.7"  />
          <line x1="0" y1="143.3" x2="600" y2="143.3" />
        </g>
        {/* speed axis labels (SVG text scales with the chart) */}
        <g fill="#FFFFFF" opacity="0.28" fontSize="9" fontFamily="monospace">
          <text x="6" y="41">250</text>
          <text x="6" y="84">180</text>
          <text x="6" y="141">90</text>
        </g>

        {/* timing-split markers */}
        {SPLITS.map((s) => {
          const x = (s.t / TOTAL_T) * 600;
          const passed = progress * TOTAL_T >= s.t;
          return (
            <g key={s.label}>
              <line
                x1={x} y1="24" x2={x} y2="200"
                stroke={passed ? '#FF5E1F' : '#3F3F46'}
                strokeWidth="0.8"
                strokeDasharray="2 5"
                opacity={passed ? 0.5 : 0.35}
              />
              <text
                x={x + 4} y="32"
                fill={passed ? '#FF8F57' : '#FFFFFF'}
                opacity={passed ? 0.9 : 0.3}
                fontSize="8.5"
                fontFamily="monospace"
                letterSpacing="1"
              >
                {s.label}
              </text>
            </g>
          );
        })}

        {/* Ghost trace — where the run is heading */}
        <path d={tracePath.stroke} stroke="#FF5E1F" strokeWidth="1.25" fill="none"
              strokeLinecap="round" strokeLinejoin="round" opacity="0.18" />

        {/* Progress-clipped area fill */}
        <path d={tracePath.fill} fill="url(#vfill)" clipPath="url(#vfill-clip)" />

        {/* Live trace — draws on with progress */}
        <path
          d={tracePath.stroke}
          stroke="#FF5E1F"
          strokeWidth="2.5"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
          pathLength="1"
          strokeDasharray="1"
          strokeDashoffset={1 - Math.max(0, Math.min(1, progress))}
        />

        {/* gear-shift ticks on the curve */}
        {SHIFTS.map((s) => {
          const x = (s.t / TOTAL_T) * 600;
          const y = 200 - (vAt(s.t) / TRAP_KMH) * 170;
          const passed = progress * TOTAL_T >= s.t;
          return (
            <g key={s.g} opacity={passed ? 1 : 0.3}>
              <circle cx={x} cy={y} r="3" fill={passed ? '#FFFFFF' : '#52525B'} />
              <text
                x={x} y={y - 8}
                fill={passed ? '#FFFFFF' : '#71717A'}
                opacity="0.75"
                fontSize="8.5"
                fontFamily="monospace"
                textAnchor="middle"
              >
                {s.g}
              </text>
            </g>
          );
        })}

        {/* live dot — glowing */}
        <circle cx={dotX} cy={dotY} r="6" fill="#FF8F57" filter="url(#dot-glow)" />
        <circle cx={dotX} cy={dotY} r="11" fill="none" stroke="#FF5E1F" strokeWidth="1.5" opacity="0.55" />
        <line x1={dotX} y1={dotY} x2={dotX} y2="200" stroke="#FF5E1F" strokeDasharray="3 4" strokeWidth="1" opacity="0.55" />
      </svg>

      <div className="absolute bottom-2 left-10 right-10 sm:left-12 sm:right-12 flex justify-between font-mono text-[8px] sm:text-[9px] text-white/40 tracking-widest tabular-nums">
        <span>0.0s</span>
        <span className="hidden xs:inline sm:inline">2.4s</span>
        <span>4.8s</span>
        <span className="hidden xs:inline sm:inline">7.2s</span>
        <span>9.62s</span>
      </div>

      <div className="hidden sm:block absolute bottom-2 left-3 font-mono text-[9px] tracking-widest text-brand-orange/85 pointer-events-none">
        REC · 60FPS · 0.001s ε
      </div>
    </div>
  );
}

export default function TelemetryHUD() {
  const sectionRef = useRef(null);
  const reduced = useReducedMotion();
  const { scrollYProgress } = useScroll({
    target: sectionRef,
    // Respond the moment the section peeks in (top at 95% viewport) and
    // complete while it is still mostly on screen (bottom at 35%). The old
    // window ('start end' → 'center start') played most of the run while
    // the section was still half-hidden and left the visible portion for a
    // late jump — field-reported as "moves very late".
    offset: ['start 0.95', 'end 0.35'],
  });
  // Physical inertia: the needle chases scroll through a critically-damped
  // spring instead of tracking raw scroll jitter. Reduced motion reads the
  // raw value (no overshoot, no lag).
  const sprung = useSpring(scrollYProgress, { stiffness: 120, damping: 26, mass: 0.35 });
  const driver = reduced ? scrollYProgress : sprung;

  const initial = useMemo(() => sampleRun(0), []);
  const [rpm, setRpm] = useState(Math.round(initial.r));
  const [spd, setSpd] = useState(initial.v);
  const [gear, setGear] = useState(initial.g);
  const [et, setEt] = useState(initial.t);
  const [dist, setDist] = useState(initial.d);
  const [progress, setProgress] = useState(0);

  useMotionValueEvent(driver, 'change', (p) => {
    const clamped = Math.min(1, Math.max(0, p));
    const s = sampleRun(clamped);
    setProgress(clamped);
    setRpm(Math.round(s.r));
    setSpd(s.v);
    setGear(s.g);
    setEt(s.t);
    setDist(s.d);
  });

  // Sync once on mount for mid-page loads (back navigation / refresh).
  useEffect(() => {
    const p = scrollYProgress.get();
    const clamped = Math.min(1, Math.max(0, p));
    const s = sampleRun(clamped);
    setProgress(clamped);
    setRpm(Math.round(s.r));
    setSpd(s.v);
    setGear(s.g);
    setEt(s.t);
    setDist(s.d);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Shift-light micro-interaction: amber above 12.5k, red at 14k+.
  const shiftLight = rpm >= 14000 ? 'red' : rpm >= 12500 ? 'amber' : 'off';

  // 3D entrance for the two panels — perspective tilt settling flat as the
  // section arrives. Opacity+transform only; skipped under reduced motion.
  const enter = (delay) =>
    reduced
      ? {}
      : {
          initial: { opacity: 0, y: 28, rotateX: 10 },
          whileInView: { opacity: 1, y: 0, rotateX: 0 },
          viewport: { once: true, margin: '0px 0px -15% 0px' },
          transition: { duration: 0.7, ease: [0.16, 1, 0.3, 1], delay },
        };

  return (
    <section
      ref={sectionRef}
      id="telemetry"
      className="relative bg-gradient-to-b from-black via-ink-1 to-black border-t border-brand-orange/10 h-[100svh] min-h-[640px] overflow-hidden flex flex-col"
    >
      <div className="h-full flex flex-col">
        <div className="px-6 sm:px-10 lg:px-16 pt-20 sm:pt-24 pb-4 sm:pb-6">
          <div className="max-w-7xl mx-auto">
            <div className="text-[11px] font-mono uppercase tracking-[0.25em] text-brand-orange mb-3">
              Live HUD &middot; Kawasaki Ninja H2R &middot; Aamby Valley &middot; ISA
            </div>
            <h2 className="font-display font-bold text-3xl sm:text-4xl lg:text-5xl text-white tracking-tight leading-[1.05] max-w-3xl">
              15 sub-models. RK4 at 1&nbsp;ms. Telemetry that matches the timeslip.
            </h2>
          </div>
        </div>

        <div className="flex-1 px-6 sm:px-10 lg:px-16 pb-10 overflow-hidden">
          <div
            className="max-w-7xl mx-auto h-full grid grid-rows-[1fr_auto] lg:grid-rows-1 lg:grid-cols-[minmax(0,1fr)_minmax(330px,440px)] gap-4 sm:gap-6 lg:gap-8 items-stretch lg:items-center"
            style={{ perspective: '1200px' }}
          >
            <motion.div className="min-w-0 h-full" {...enter(0)}>
              <SpeedTrace currentV={spd} currentT={et} progress={progress} />
            </motion.div>

            <motion.div className="grid min-w-0 grid-cols-2 gap-3 sm:gap-4" {...enter(0.12)}>
              <Gauge
                label="Engine RPM"
                value={rpm.toLocaleString()}
                unit={`/ ${REDLINE.toLocaleString()}`}
                percent={(rpm / REDLINE) * 100}
                shiftLight={shiftLight}
              />
              <Gauge
                label="Speed"
                value={spd.toFixed(1)}
                unit="km/h"
                percent={(spd / TRAP_KMH) * 100}
              />
              <Gauge label="Gear"     value={gear}            unit={null} />
              <Gauge label="Elapsed"  value={et.toFixed(3)}   unit="s" accent seg />
              <Gauge
                label="Distance · Quarter Mile"
                value={Math.round(dist)}
                unit="/ 402 m"
                percent={(dist / TRACK_M) * 100}
                full
              />
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  );
}
