'use client';

/**
 * TelemetryHUD — sticky-pinned section that plays a real GSX-R K5
 * quarter-mile run on scroll progress.
 *
 * The outer <section> is `height: 280vh`. The inner content uses
 * `position: sticky` to lock to the viewport while the user scrolls.
 * `useScroll({ target: ref, offset: ['start start', 'end end'] })`
 * gives us a 0..1 progress through the section; we sample a hand-built
 * waypoint table to drive RPM / speed / gear / ET / distance counters
 * and a velocity-vs-time trace.
 *
 * Reference baseline preserved exactly:
 *   GSX-R 1000 K5 — 10.0334s @ 239.8 km/h, finishing in gear 6.
 */

import { useRef, useState } from 'react';
import { useScroll, useMotionValueEvent } from 'framer-motion';
import BikeSilhouette from './BikeSilhouette';

// Hand-curated waypoints for the GSX-R K5 baseline run.
// Time (s), velocity (km/h), gear, RPM, distance (m).
const RUN = [
  { t: 0.000,  v: 0,     g: 1, r: 4500,  d: 0     },
  { t: 0.800,  v: 62,    g: 1, r: 11200, d: 8     },
  { t: 1.600,  v: 105,   g: 2, r: 10600, d: 28    },
  { t: 2.500,  v: 142,   g: 2, r: 11800, d: 60    },
  { t: 3.400,  v: 168,   g: 3, r: 11000, d: 99    },
  { t: 4.500,  v: 188,   g: 4, r: 11400, d: 156   },
  { t: 5.700,  v: 204,   g: 4, r: 12000, d: 219   },
  { t: 7.100,  v: 219,   g: 5, r: 11600, d: 299   },
  { t: 8.500,  v: 230,   g: 5, r: 12200, d: 360   },
  { t: 10.0334, v: 239.8, g: 6, r: 12100, d: 402.336 },
];

const TOTAL_T = 10.0334;
const REDLINE = 13500;
const TRAP_KMH = 260;
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
            'font-mono font-bold tabular-nums',
            accent ? 'text-brand-orange' : 'text-white',
            full ? 'text-3xl sm:text-4xl' : 'text-3xl sm:text-4xl',
          ].join(' ')}
        >
          {value}
        </span>
        {unit && (
          <span className="font-mono text-xs text-white/45">{unit}</span>
        )}
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

export default function TelemetryHUD() {
  const sectionRef = useRef(null);
  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ['start start', 'end end'],
  });

  const [rpm, setRpm] = useState(0);
  const [spd, setSpd] = useState(0);
  const [gear, setGear] = useState(1);
  const [et, setEt] = useState(0);
  const [dist, setDist] = useState(0);

  useMotionValueEvent(scrollYProgress, 'change', (p) => {
    const s = sampleRun(Math.min(1, Math.max(0, p)));
    setRpm(Math.round(s.r));
    setSpd(s.v);
    setGear(s.g);
    setEt(s.t);
    setDist(s.d);
  });

  return (
    <section
      ref={sectionRef}
      id="telemetry"
      className="relative bg-gradient-to-b from-black via-ink-1 to-black border-t border-brand-orange/10"
      style={{ height: '280vh' }}
    >
      <div className="sticky top-0 h-screen overflow-hidden flex flex-col">
        {/* Headline (top-anchored, doesn't scroll) */}
        <div className="px-6 sm:px-10 lg:px-16 pt-24 pb-6">
          <div className="max-w-7xl mx-auto">
            <div className="text-[11px] font-mono uppercase tracking-[0.25em] text-brand-orange mb-3">
              Live HUD &middot; Suzuki GSX-R 1000 K5 &middot; Aamby Valley &middot; ISA
            </div>
            <h2 className="font-display font-bold text-3xl sm:text-4xl lg:text-5xl text-white tracking-tight leading-[1.05] max-w-3xl">
              15 sub-models. RK4 at 1&nbsp;ms. Telemetry that matches the timeslip.
            </h2>
          </div>
        </div>

        {/* HUD grid */}
        <div className="flex-1 px-6 sm:px-10 lg:px-16 pb-10 overflow-hidden">
          <div className="max-w-7xl mx-auto h-full grid lg:grid-cols-[1fr_460px] gap-8 items-center">
            {/* Bike viewport — telemetry frame around the silhouette */}
            <div className="relative h-[240px] sm:h-[300px] lg:h-[380px] rounded-2xl border border-white/10 bg-ink-1/60 overflow-hidden">
              {/* Frame corners */}
              <span className="absolute top-3 left-3 w-6 h-6 border-t-2 border-l-2 border-brand-orange" />
              <span className="absolute bottom-3 right-3 w-6 h-6 border-b-2 border-r-2 border-brand-orange" />

              {/* Speed lines layer */}
              <div className="absolute inset-0 pointer-events-none">
                {[20, 35, 56, 72, 85].map((top, i) => (
                  <div
                    key={i}
                    className="absolute h-px bg-gradient-to-r from-transparent via-brand-orange/45 to-transparent"
                    style={{
                      top: `${top}%`,
                      left: '0',
                      right: '0',
                      opacity: 0.5 + 0.1 * (i % 2),
                    }}
                  />
                ))}
              </div>

              {/* The bike */}
              <div className="absolute inset-0 flex items-center justify-center px-8">
                <BikeSilhouette className="w-full max-w-[640px] h-auto" />
              </div>

              {/* Stamp overlay */}
              <div className="absolute bottom-3 left-3 font-mono text-[10px] tracking-widest text-brand-orange/85">
                REC &middot; 60FPS &middot; 0.001s ε
              </div>
              <div className="absolute top-3 right-3 flex items-center gap-2 font-mono text-[10px] tracking-widest text-brand-accent">
                <span className="w-1.5 h-1.5 rounded-full bg-brand-accent animate-live-pulse" />
                LIVE
              </div>
            </div>

            {/* HUD gauges */}
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
