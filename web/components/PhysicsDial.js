'use client';

/**
 * PhysicsDial — Kawasaki Ninja H2R-inspired dashboard.
 *
 * Two-zone composition inside one SVG:
 *
 *   LEFT  ─ analogue tachometer modelled on the H2R cluster
 *           - 270° clockwise sweep, 0 → 15 (×1000 r/min)
 *           - White scale 0-10k → amber 10-13k → orange 13-14.5k →
 *             red redline 14.5-15k (real H2R redlines around 14,500)
 *           - Numbers every 2k, minor ticks every 1k
 *           - Red needle pivots from idle (1500 rpm) to redline; rotation
 *             is critically-damped via framer-motion useSpring so it
 *             reads like a real analog needle, not a stepwise SVG node
 *           - Brand-orange centre boss
 *           - "x1000 r/min" sub-label, big live RPM in the well
 *
 *   RIGHT ─ digital LCD panel
 *           - Slight blue tint, scanline texture, like a real backlit LCD
 *           - Top status row: PHYSICS · RK4 · 1ms · scene tag
 *           - Big morphing centre value (RPM / ET / TRAP per scroll)
 *           - GEAR letter that auto-shifts 1..6 with progress
 *           - "NINJA H2R" branding under the LCD
 *
 * Scroll-driven scenes (0..1):
 *   0.00 - 0.40   live RPM ticking 1500 → 14500
 *   0.40 - 0.70   ET stopwatch counting up to 9.6200s (H2R 1/4 mile)
 *   0.70 - 1.00   trap speed counting up to 257 km/h (H2R trap)
 *
 * (A bottom HP/torque dyno strip lived here previously; pulled out
 * Apr 30 because it crowded the staging-tree column. If you want it
 * back, the H2R dyno waypoints are in git history.)
 *
 * Source: published Kawasaki + Cycle World H2R dyno tests; quarter
 * mile from Motorcycle USA timeslip (9.62s / 256 km/h).
 */

import { useEffect, useRef, useState } from 'react';
import { useMotionValue, useMotionValueEvent, useSpring } from 'framer-motion';

const VIEW_W = 880;
const VIEW_H = 460;

// ─── TACH GEOMETRY ───────────────────────────────────────────────────
const T_CX = 260;
const T_CY = 280;
const T_R_BEZEL = 232;
const T_R_BAND = 200;
const T_BAND_W = 16;
const T_R_TICK_OUT = 184;
const T_R_TICK_IN_MAJOR = 156;
const T_R_TICK_IN_MINOR = 168;
const T_R_LABEL = 138;
const T_R_NEEDLE = 188;
const T_R_NEEDLE_TAIL = 26;

// H2R-style sweep: 270° clockwise from 8 o'clock to 4 o'clock.
const SWEEP_START_DEG = 135;
const SWEEP_TOTAL_DEG = 270;
const RPM_MAX = 15000;        // tach scale upper bound
const REDLINE = 14500;        // H2R redline

// ─── HELPERS ─────────────────────────────────────────────────────────
function bandPath(rpmFrom, rpmTo) {
  const a0 = SWEEP_START_DEG + (rpmFrom / RPM_MAX) * SWEEP_TOTAL_DEG;
  const a1 = SWEEP_START_DEG + (rpmTo   / RPM_MAX) * SWEEP_TOTAL_DEG;
  const r = T_R_BAND;
  const toXY = (deg) => {
    const a = (deg) * Math.PI / 180;
    return [T_CX + r * Math.cos(a), T_CY + r * Math.sin(a)];
  };
  const [x0, y0] = toXY(a0);
  const [x1, y1] = toXY(a1);
  const large = (a1 - a0) > 180 ? 1 : 0;
  return `M ${x0.toFixed(2)} ${y0.toFixed(2)} A ${r} ${r} 0 ${large} 1 ${x1.toFixed(2)} ${y1.toFixed(2)}`;
}
function gaugePt(deg, radius) {
  const a = deg * Math.PI / 180;
  return [T_CX + radius * Math.cos(a), T_CY + radius * Math.sin(a)];
}

// ─── TICKS + NUMBERS ─────────────────────────────────────────────────
function TickAndNumber({ rpmK }) {
  const rpm = rpmK * 1000;
  const deg = SWEEP_START_DEG + (rpm / RPM_MAX) * SWEEP_TOTAL_DEG;
  const [x1, y1] = gaugePt(deg, T_R_TICK_OUT);
  const [x2, y2] = gaugePt(deg, T_R_TICK_IN_MAJOR);
  const [lx, ly] = gaugePt(deg, T_R_LABEL);
  const isRed = rpmK >= 14;
  const tickColor = rpmK >= 14 ? '#EF4444' : rpmK >= 13 ? '#FF5E1F' : rpmK >= 10 ? '#F59E0B' : '#FAFAFA';
  return (
    <g>
      <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={tickColor} strokeWidth="3" strokeLinecap="round" />
      <text
        x={lx}
        y={ly + 6}
        textAnchor="middle"
        fontFamily="ui-monospace, monospace"
        fontWeight="800"
        fontSize="22"
        fill={isRed ? '#EF4444' : '#FAFAFA'}
      >
        {rpmK}
      </text>
    </g>
  );
}

function MinorTick({ rpmK }) {
  const rpm = rpmK * 1000;
  const deg = SWEEP_START_DEG + (rpm / RPM_MAX) * SWEEP_TOTAL_DEG;
  const [x1, y1] = gaugePt(deg, T_R_TICK_OUT);
  const [x2, y2] = gaugePt(deg, T_R_TICK_IN_MINOR);
  return <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#71717A" strokeWidth="1.5" strokeLinecap="round" />;
}

function Needle({ rpmSpring }) {
  // Needle is built around the pivot at (T_CX, T_CY) and rotated via the
  // SVG `transform` attribute (works reliably across browsers, unlike
  // CSS transform-box on grouped SVG nodes).
  //
  // `rpmSpring` is a framer-motion spring motion value — we subscribe to
  // it and re-render with the smoothed value, so the needle glides like
  // a real analog tach instead of stepping per scroll event.
  const [smoothRpm, setSmoothRpm] = useState(rpmSpring.get?.() ?? 1500);
  useMotionValueEvent(rpmSpring, 'change', (v) => setSmoothRpm(v));
  const deg = SWEEP_START_DEG + (Math.min(RPM_MAX, Math.max(0, smoothRpm)) / RPM_MAX) * SWEEP_TOTAL_DEG;
  const px0 = T_CX - T_R_NEEDLE_TAIL;
  const px1 = T_CX + T_R_NEEDLE - 14;
  const px2 = T_CX + T_R_NEEDLE;
  return (
    <g transform={`rotate(${deg.toFixed(2)} ${T_CX} ${T_CY})`}>
      <polygon
        points={`${px0},${T_CY - 3} ${px0},${T_CY + 3} ${px1},${T_CY + 2} ${px2},${T_CY} ${px1},${T_CY - 2}`}
        fill="#EF4444"
        stroke="#7F1D1D"
        strokeWidth="0.6"
      />
      <line
        x1={px0 + 4}
        y1={T_CY}
        x2={px2 - 4}
        y2={T_CY}
        stroke="#FCA5A5"
        strokeWidth="0.8"
        opacity="0.6"
      />
    </g>
  );
}

// ─── LCD READOUT ─────────────────────────────────────────────────────
function LCD({ scene, rpm, et, trap, gear }) {
  const X = 540;
  const Y = 130;
  const W = 310;
  const H = 240;

  let centreLabel, centreValue, centreUnit, secondaryLabel, secondaryValue;
  if (scene === 0) {
    centreLabel = 'ENGINE RPM';
    centreValue = rpm.toLocaleString();
    centreUnit = 'r/min';
    secondaryLabel = 'GEAR';
    secondaryValue = gear;
  } else if (scene === 1) {
    centreLabel = 'ELAPSED';
    centreValue = et.toFixed(4);
    centreUnit = 's';
    secondaryLabel = 'NINJA H2R';
    secondaryValue = '402.336 m';
  } else {
    centreLabel = 'TRAP';
    centreValue = trap.toString();
    centreUnit = 'km/h';
    secondaryLabel = 'GREEN';
    secondaryValue = 'GO RACE';
  }

  return (
    <g>
      <rect x={X - 6} y={Y - 6} width={W + 12} height={H + 12} rx="10" fill="#0A0A0A" stroke="#27272A" strokeWidth="1.5" />
      <rect x={X} y={Y} width={W} height={H} rx="6" fill="#0F1B2D" />
      <rect x={X} y={Y} width={W} height={H} rx="6" fill="url(#lcdScan)" opacity="0.55" />

      <g fontFamily="ui-monospace, monospace" fontSize="10" letterSpacing="1.5">
        <text x={X + 18} y={Y + 26} fill="#FF5E1F">PHYSICS</text>
        <text x={X + 100} y={Y + 26} fill="#F59E0B">RK4</text>
        <text x={X + 152} y={Y + 26} fill="#22C55E">1ms</text>
        <text x={X + 220} y={Y + 26} fill="#FAFAFA">{scene === 0 ? 'TACH' : scene === 1 ? 'ET' : 'TRAP'}</text>
      </g>
      <line x1={X + 12} y1={Y + 38} x2={X + W - 12} y2={Y + 38} stroke="#1A2A45" strokeWidth="1" />

      <text x={X + W / 2} y={Y + 66} textAnchor="middle"
        fontFamily="ui-monospace, monospace" fontSize="13" letterSpacing="3" fill="#7DD3FC" opacity="0.85">
        {centreLabel}
      </text>
      <text x={X + W / 2} y={Y + 132} textAnchor="middle"
        fontFamily="ui-monospace, monospace" fontWeight="800" fontSize="62" fill="#FAFAFA">
        {centreValue}
      </text>
      <text x={X + W / 2} y={Y + 162} textAnchor="middle"
        fontFamily="ui-monospace, monospace" fontSize="14" letterSpacing="3" fill="#7DD3FC" opacity="0.85">
        {centreUnit}
      </text>

      <line x1={X + 12} y1={Y + H - 50} x2={X + W - 12} y2={Y + H - 50} stroke="#1A2A45" strokeWidth="1" />
      <g fontFamily="ui-monospace, monospace">
        <text x={X + 18} y={Y + H - 24} fontSize="10" letterSpacing="2" fill="#7DD3FC" opacity="0.7">
          {secondaryLabel}
        </text>
        <text x={X + W - 18} y={Y + H - 24} textAnchor="end" fontSize="16" fontWeight="700" fill="#FAFAFA">
          {secondaryValue}
        </text>
      </g>
    </g>
  );
}

// ─── SCROLL SCENE ────────────────────────────────────────────────────
// H2R: idle → 14,500 RPM redline. Quarter mile 9.62s @ 257 km/h.
function sampleScene(p) {
  const v = Math.min(1, Math.max(0, p));
  const rpm = Math.round(1500 + v * (REDLINE - 1500));
  const gear = Math.min(6, Math.max(1, Math.floor(1 + v * 6)));
  let scene = 0, et = 0, trap = 0;
  if (v < 0.4) {
    scene = 0;
  } else if (v < 0.7) {
    scene = 1;
    et = 9.62 * ((v - 0.4) / 0.3);
  } else {
    scene = 2;
    et = 9.62;
    trap = Math.round(257 * ((v - 0.7) / 0.3));
  }
  return { rpm, et, trap, gear, scene };
}

export default function PhysicsDial({ progress, className = '' }) {
  // RPM motion value drives a critically-damped spring → the Needle
  // component subscribes to that spring so it glides analog-style
  // even when the scroll handler fires only every few frames.
  const rpmMV = useMotionValue(1500);
  const rpmSpring = useSpring(rpmMV, { stiffness: 140, damping: 22, mass: 0.4 });

  const [rpm, setRpm] = useState(1500);
  const [et, setEt] = useState(0);
  const [trap, setTrap] = useState(0);
  const [gear, setGear] = useState(1);
  const [scene, setScene] = useState(0);

  useMotionValueEvent(progress, 'change', (p) => {
    const s = sampleScene(p);
    rpmMV.set(s.rpm);
    setRpm(s.rpm);
    setEt(s.et);
    setTrap(s.trap);
    setGear(s.gear);
    setScene(s.scene);
  });

  useEffect(() => {
    const v = progress.get?.() ?? 0;
    const s = sampleScene(v);
    rpmMV.set(s.rpm);
    setRpm(s.rpm); setEt(s.et); setTrap(s.trap); setGear(s.gear); setScene(s.scene);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ─── ANIME.JS FIRST-PAINT DRAW-ON ──────────────────────────────────
  // Runs once when the component mounts. Bands draw on (stroke-dashoffset
  // 1→0), then labels fade in. Respects prefers-reduced-motion.
  const svgRef = useRef(null);
  useEffect(() => {
    const root = svgRef.current;
    if (!root) return;
    const reduced =
      typeof window !== 'undefined' &&
      window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const bands = root.querySelectorAll('[data-anim="band"]');
    const labels = root.querySelectorAll('[data-anim="label"]');

    if (reduced) {
      // Skip animation, snap to final state.
      bands.forEach((el) => { el.style.strokeDashoffset = '0'; });
      labels.forEach((el) => { el.style.opacity = '1'; });
      return;
    }

    let cancelled = false;
    import('animejs/lib/anime.es.js').then((mod) => {
      if (cancelled) return;
      const anime = mod.default || mod;
      const tl = anime.timeline({ easing: 'easeOutQuart' });
      tl.add({
        targets: bands,
        strokeDashoffset: [1, 0],
        duration: 700,
        delay: anime.stagger(90, { start: 100 }),
      });
      tl.add({
        targets: labels,
        opacity: [0, 1],
        duration: 500,
        delay: anime.stagger(120),
      }, '-=400');
    }).catch(() => {
      // anime.js failed to load — snap to final state, never strand visuals.
      bands.forEach((el) => { el.style.strokeDashoffset = '0'; });
      labels.forEach((el) => { el.style.opacity = '1'; });
    });

    return () => { cancelled = true; };
  }, []);

  const majors = [0, 2, 4, 6, 8, 10, 12, 14];
  const minors = [1, 3, 5, 7, 9, 11, 13, 15];

  return (
    <svg
      ref={svgRef}
      viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
      className={['select-none block max-w-full', className].join(' ')}
      style={{ filter: 'drop-shadow(0 0 60px rgba(255,94,31,0.18))' }}
      aria-hidden="true"
    >
      <defs>
        <pattern id="lcdScan" patternUnits="userSpaceOnUse" width="2" height="3">
          <rect width="2" height="3" fill="#0F1B2D" />
          <rect width="2" height="1" fill="#1A2A45" opacity="0.4" />
        </pattern>
      </defs>

      {/* Dashboard housing */}
      <rect
        x="12"
        y="20"
        width={VIEW_W - 24}
        height={VIEW_H - 40}
        rx="20"
        fill="#050505"
        stroke="#1F1F22"
        strokeWidth="2"
      />

      {/* TACH */}
      <circle cx={T_CX} cy={T_CY} r={T_R_BEZEL} fill="#0A0A0A" stroke="#27272A" strokeWidth="3" />
      <circle cx={T_CX} cy={T_CY} r={T_R_BEZEL - 12} fill="#0F0F11" />

      <path d={bandPath(0,    10000)} stroke="#FAFAFA" strokeWidth={T_BAND_W} fill="none" opacity="0.92" pathLength="1" data-anim="band" style={{ strokeDasharray: 1, strokeDashoffset: 1 }} />
      <path d={bandPath(10000, 13000)} stroke="#F59E0B" strokeWidth={T_BAND_W} fill="none" pathLength="1" data-anim="band" style={{ strokeDasharray: 1, strokeDashoffset: 1 }} />
      <path d={bandPath(13000, REDLINE)} stroke="#FF5E1F" strokeWidth={T_BAND_W} fill="none" pathLength="1" data-anim="band" style={{ strokeDasharray: 1, strokeDashoffset: 1 }} />
      <path d={bandPath(REDLINE, 15000)} stroke="#EF4444" strokeWidth={T_BAND_W} fill="none" pathLength="1" data-anim="band" style={{ strokeDasharray: 1, strokeDashoffset: 1 }} />

      {minors.map((k) => <MinorTick key={`m-${k}`} rpmK={k} />)}
      {majors.map((k) => <TickAndNumber key={`M-${k}`} rpmK={k} />)}

      <text x={T_CX} y={T_CY - 50} textAnchor="middle"
        fontFamily="ui-monospace, monospace" fontSize="12" letterSpacing="3" fill="#71717A">
        x1000
      </text>
      <text x={T_CX} y={T_CY - 32} textAnchor="middle"
        fontFamily="ui-monospace, monospace" fontSize="13" fontWeight="700" fill="#A1A1AA">
        r/min
      </text>
      <text x={T_CX} y={T_CY + 90} textAnchor="middle"
        fontFamily="ui-monospace, monospace" fontSize="36" fontWeight="800" fill="#FAFAFA">
        {rpm.toLocaleString()}
      </text>

      <Needle rpmSpring={rpmSpring} />

      <circle cx={T_CX} cy={T_CY} r="22" fill="#1F1F22" stroke="#3F3F46" strokeWidth="1.5" />
      <circle cx={T_CX} cy={T_CY} r="10" fill="#FF5E1F" />
      <circle cx={T_CX} cy={T_CY} r="4" fill="#0A0A0A" />

      <text x={T_CX} y={T_CY + T_R_BEZEL + 28} textAnchor="middle"
        fontFamily="ui-monospace, monospace" fontSize="11" letterSpacing="3" fill="#52525B"
        data-anim="label" style={{ opacity: 0 }}>
        TACHO · NINJA H2R · REDLINE 14,500
      </text>

      {/* LCD */}
      <LCD scene={scene} rpm={rpm} et={et} trap={trap} gear={gear} />

      <g fontFamily="ui-monospace, monospace" fontSize="10" letterSpacing="2">
        <circle cx="555" cy="100" r="4" fill="#22C55E" />
        <text x="568" y="104" fill="#22C55E">LIVE</text>
        <text x="640" y="104" fill="#71717A">·</text>
        <text x="660" y="104" fill="#71717A">15 SUB-MODELS</text>
      </g>
      <text x="694" y="395" textAnchor="middle"
        fontFamily="ui-monospace, monospace" fontSize="10" letterSpacing="1.5" fill="#52525B"
        data-anim="label" style={{ opacity: 0 }}>
        NINJA H2R · 998 cm³ · 310 hp · supercharged
      </text>
    </svg>
  );
}
