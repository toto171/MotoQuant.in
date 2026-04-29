'use client';

/**
 * TelemetryHUD — sticky-pinned section that plays a real Kawasaki
 * Ninja H2R quarter-mile run on scroll progress.
 *
 * Layout: text + headline above, big v(t) speed-trace chart in the
 * middle, HUD gauges on the right. RPM / speed / gear / ET / distance
 * counters tick through the run as the user scrolls.
 *
 * Reference baseline (Motorcycle USA timeslip + Cycle World testing):
 *   Kawasaki Ninja H2R — 9.620s @ 257 km/h, finishing in gear 5,
 *   14,500 redline.
 *
 * Matches the PhysicsDial above so both the dial and the trace are
 * showing the same bike's run.
 */

import { useRef, useState, useMemo, useEffect } from 'react';
import { useScroll, useMotionValueEvent } from 'framer-motion';

// Hand-curated waypoints for the H2R baseline run.
// Time (s), velocity (km/h), gear, RPM, distance (m).
// H2R accelerates much harder than the K5 — peak power is ~310 hp
// from a 998 cc supercharged I4 — so the v(t) curve is much steeper
// off the line and asymptotes higher at the trap.
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

function Gauge({ label, value, unit, percent, accent = false, full = false }) {
  return (
    <div
      className={[
        'rounded-xl border border-white/10 bg-white/[0.025] p-4 sm:p-5',
        full ? 'col-span-2' : '',
      ].join(' ')}
    >
      <div className="text-[10px] font-mono uppercase tracking-widest text-white/45">
        {label}
      </div>
      <div className="mt-1.5 flex items-baseline gap-1.5 leading-none">
        <span
          className={[
            'font-mono font-bold tabular-nums text-3xl sm:text-4xl',
            accent ? 'text-brand-orange' : 'text-white',
          ].join(' ')}
        >
          {value}
        </span>
        {unit && <span className="font-mono text-xs text-white/45">{unit}</span>}
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

// Speed-trace chart — replaces the bike silhouette as the visual.
// Shows the v(t) curve; a moving dot tracks the current run state.
function SpeedTrace({ currentV, currentT, progress }) {
  const tracePath = useMemo(() => {
    const N = 80;
    const pts = [];
    const fillPts = ['M 0 200'];
    for (let i = 0; i <= N; i++) {
      const u = i / N;
      const t = u * TOTAL_T;
      let idx = 0;
      while (idx < RUN.length - 1 && RUN[idx + 1].t < t) idx++;
      const a = RUN[idx];
      const b = RUN[Math.min(idx + 1, RUN.length - 1)];
      const span = (b.t - a.t) || 1;
      const ub = Math.min(1, Math.max(0, (t - a.t) / span));
      const v = lerp(a.v, b.v, ub);
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
    <div className="relative h-[260px] sm:h-[320px] lg:h-[400px] rounded-2xl border border-white/10 bg-ink-1/60 overflow-hidden">
      <span className="absolute top-3 left-3 w-6 h-6 border-t-2 border-l-2 border-brand-orange" />
      <span className="absolute bottom-3 right-3 w-6 h-6 border-b-2 border-r-2 border-brand-orange" />

      <div className="absolute top-3 left-12 right-12 flex justify-between items-baseline">
        <div className="font-mono text-[10px] tracking-widest text-brand-orange/85">
          v(t) · NINJA H2R · 1/4 mile
        </div>
        <div className="flex items-center gap-2 font-mono text-[10px] tracking-widest text-brand-accent">
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
        </defs>

        <g stroke="#27272A" strokeWidth="0.6" strokeDasharray="3 4">
          <line x1="0" y1="40"  x2="600" y2="40"  />
          <line x1="0" y1="80"  x2="600" y2="80"  />
          <line x1="0" y1="120" x2="600" y2="120" />
          <line x1="0" y1="160" x2="600" y2="160" />
        </g>

        {/* Ghost trace — full curve, low opacity. Tells the user where the
            run is HEADING; the bright "live" path overlays only the portion
            already covered by scroll progress. */}
        <path d={tracePath.stroke} stroke="#FF5E1F" strokeWidth="1.25" fill="none"
              strokeLinecap="round" strokeLinejoin="round" opacity="0.18" />

        {/* Progress-clipped fill — uses a clipPath rectangle that grows with
            progress so the orange area fill only shows under the drawn portion. */}
        <defs>
          <clipPath id="vfill-clip">
            <rect x="0" y="0" width={Math.max(0, Math.min(1, progress)) * 600} height="220" />
          </clipPath>
        </defs>
        <path d={tracePath.fill} fill="url(#vfill)" clipPath="url(#vfill-clip)" />

        {/* Live trace — same path, but drawn via stroke-dashoffset so the
            line "draws on" as scroll progresses. pathLength=1 normalises any
            length to 0..1 so the offset math is independent of the actual
            geometric length of the curve. */}
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

        <circle cx={dotX} cy={dotY} r="6" fill="#FF8F57" />
        <circle cx={dotX} cy={dotY} r="11" fill="none" stroke="#FF5E1F" strokeWidth="1.5" opacity="0.55" />
        <line x1={dotX} y1={dotY} x2={dotX} y2="200" stroke="#FF5E1F" strokeDasharray="3 4" strokeWidth="1" opacity="0.55" />
      </svg>

      <div className="absolute bottom-3 left-12 right-12 flex justify-between font-mono text-[9px] text-white/40 tracking-widest">
        <span>0.0s</span>
        <span>2.4s</span>
        <span>4.8s</span>
        <span>7.2s</span>
        <span>9.62s</span>
      </div>

      <div className="absolute bottom-3 left-3 font-mono text-[10px] tracking-widest text-brand-orange/85">
        REC · 60FPS · 0.001s ε
      </div>
    </div>
  );
}

export default function TelemetryHUD() {
  const sectionRef = useRef(null);
  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ['start start', 'end end'],
  });

  // Initialise from progress=0 so gauges show staged-and-idle values
  // (RPM ≈ 4500, spd 0, gear 1, et 0, dist 0) on first paint instead of all
  // zeros. Without this, mobile users saw RPM=0 / chart=full-trace on first
  // load — a desync between visible chart and gauge readouts.
  const initial = useMemo(() => sampleRun(0), []);
  const [rpm, setRpm] = useState(Math.round(initial.r));
  const [spd, setSpd] = useState(initial.v);
  const [gear, setGear] = useState(initial.g);
  const [et, setEt] = useState(initial.t);
  const [dist, setDist] = useState(initial.d);
  // Track progress as React state so the chart can clip its drawn portion.
  // Mirrors the motion value but persists across renders so SVG path-length
  // math is stable per render.
  const [progress, setProgress] = useState(0);

  useMotionValueEvent(scrollYProgress, 'change', (p) => {
    const clamped = Math.min(1, Math.max(0, p));
    const s = sampleRun(clamped);
    setProgress(clamped);
    setRpm(Math.round(s.r));
    setSpd(s.v);
    setGear(s.g);
    setEt(s.t);
    setDist(s.d);
  });

  // Fire once on mount in case the user has already scrolled (browser back
  // / fragment navigation / refresh in the middle of the page). Without
  // this the chart and gauges stay at "scroll=0" values until the user
  // moves the scroll wheel manually.
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

  return (
    <section
      ref={sectionRef}
      id="telemetry"
      className="relative bg-gradient-to-b from-black via-ink-1 to-black border-t border-brand-orange/10"
      style={{ height: 'clamp(180vh, 220vh, 280vh)' }}
    >
      <div className="sticky top-0 h-screen overflow-hidden flex flex-col">
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
          <div className="max-w-7xl mx-auto h-full grid lg:grid-cols-[1fr_460px] gap-6 sm:gap-8 items-start lg:items-center">
            <SpeedTrace currentV={spd} currentT={et} progress={progress} />

            <div className="grid grid-cols-2 gap-3 sm:gap-4">
              <Gauge
                label="Engine RPM"
                value={rpm.toLocaleString()}
                unit={`/ ${REDLINE.toLocaleString()}`}
                percent={(rpm / REDLINE) * 100}
              />
              <Gauge
                label="Speed"
                value={spd.toFixed(1)}
                unit="km/h"
                percent={(spd / TRAP_KMH) * 100}
              />
              <Gauge label="Gear"     value={gear}            unit={null} />
              <Gauge label="Elapsed"  value={et.toFixed(3)}   unit="s" accent />
              <Gauge
                label="Distance · Quarter Mile"
                value={Math.round(dist)}
                unit="/ 402 m"
                percent={(dist / TRACK_M) * 100}
                full
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
