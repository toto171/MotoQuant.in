'use client';

/**
 * TronGrid v2 — "night strip" hero background (July 2026, operator-directed).
 *
 * A perspective wireframe floor with a drag strip running dead-center to the
 * vanishing point: brighter lane edges, three faint timing gates across the
 * lanes, ambient light-cycle traffic crossing the arena, and — on a clean
 * hold-to-launch release (`launchSignal`) — two racers rocketing DOWN the
 * strip toward the horizon, dragging fading light-walls, each timing gate
 * flashing as they cross it. The Tron light-cycle language aimed at the
 * thing this product actually is: a quarter-mile at night.
 *
 * Engineering discipline (v1 rules kept):
 *  - Canvas 2D, zero dependencies, one rAF loop, ~30 draw ops/frame.
 *  - Runs ONLY while on screen (IntersectionObserver) and the tab is
 *    visible (visibilitychange); resize via ResizeObserver, DPR capped at 2.
 *  - Head glows are pre-rendered sprites (canvas shadowBlur forces a blur
 *    pass per head per frame and janks weak GPUs — never reintroduce it).
 *  - prefers-reduced-motion: one static frame (grid + strip + gates).
 *  - pointer-events-none, aria-hidden; sits behind the hero's own glows.
 */

import { useEffect, useRef } from 'react';

const ORANGE = [255, 94, 31];
const MINT = [0, 255, 178];
const GREEN = [34, 197, 94];

// timing gates along the strip, in depth-parameter t (1 = viewer, 0 = horizon)
const GATE_TS = [0.62, 0.42, 0.26];

export default function TronGrid({ launchSignal = 0, className = '' }) {
  const canvasRef = useRef(null);
  const stateRef = useRef({
    streaks: [],
    racers: [],
    gates: GATE_TS.map((t) => ({ t, flash: 0 })),
    phase: 0,
    lastSpawn: 0,
    lastSolo: 3.0,
    running: false,
    visible: false,
    raf: 0,
    lastTs: 0,
  });

  // Fire a two-lane launch when the counter increments (skip initial mount).
  const prevLaunch = useRef(launchSignal);
  useEffect(() => {
    if (launchSignal === prevLaunch.current) return;
    prevLaunch.current = launchSignal;
    const st = stateRef.current;
    // two racers down the strip + crossing streaks for immediate wide energy
    st.racers.push(
      { lane: -0.62, u: 0, dur: 1.45, delay: 0,    color: ORANGE, trail: [], dim: 1 },
      { lane:  0.62, u: 0, dur: 1.62, delay: 0.07, color: MINT,   trail: [], dim: 1 }
    );
    for (let i = 0; i < 3; i++) {
      st.streaks.push({
        depth: 0.2 + Math.random() * 0.65,
        x: -0.15 - i * 0.06,
        speed: 1.6 + Math.random() * 0.9,
        color: ORANGE,
        boost: true,
      });
    }
  }, [launchSignal]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return undefined;
    const ctx = canvas.getContext('2d');
    const st = stateRef.current;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Pre-rendered head-glow sprites (white-hot core -> color halo).
    const glowSprite = (() => {
      const cache = new Map();
      return ([r, g, b]) => {
        const key = `${r},${g},${b}`;
        let sp = cache.get(key);
        if (!sp) {
          sp = document.createElement('canvas');
          sp.width = sp.height = 48;
          const g2 = sp.getContext('2d');
          const grad = g2.createRadialGradient(24, 24, 0, 24, 24, 24);
          grad.addColorStop(0, 'rgba(255,255,255,0.95)');
          grad.addColorStop(0.18, `rgba(${r},${g},${b},0.85)`);
          grad.addColorStop(0.5, `rgba(${r},${g},${b},0.25)`);
          grad.addColorStop(1, `rgba(${r},${g},${b},0)`);
          g2.fillStyle = grad;
          g2.fillRect(0, 0, 48, 48);
          cache.set(key, sp);
        }
        return sp;
      };
    })();

    let w = 0;
    let h = 0;
    let dpr = 1;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      dpr = Math.min(2, window.devicePixelRatio || 1);
      w = rect.width;
      h = rect.height;
      canvas.width = Math.max(1, Math.round(w * dpr));
      canvas.height = Math.max(1, Math.round(h * dpr));
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      if (reduced) drawFrame(0);
    };

    // Perspective helpers: depth t ∈ [0..1], 0 = horizon, 1 = viewer.
    const horizonY = () => h * 0.44;
    const depthY = (t) => horizonY() + (h - horizonY()) * Math.pow(t, 2.1);
    // screen-space scale factor along the strip (0 at horizon, 1 at bottom)
    const spread = (t) => (depthY(t) - horizonY()) / (h - horizonY());
    const stripHalfBottom = () => w * 0.155;

    function drawGrid(phase) {
      const hy = horizonY();
      const cx = w * 0.5;

      // horizon glow line
      const grad = ctx.createLinearGradient(0, hy - 18, 0, hy + 22);
      grad.addColorStop(0, 'rgba(255,94,31,0)');
      grad.addColorStop(0.5, 'rgba(255,94,31,0.10)');
      grad.addColorStop(1, 'rgba(255,94,31,0)');
      ctx.fillStyle = grad;
      ctx.fillRect(0, hy - 18, w, 40);

      // converging longitudinal lines
      ctx.lineWidth = 1;
      const LANES = 11;
      for (let i = -LANES; i <= LANES; i++) {
        const spreadTop = i * w * 0.012;
        const spreadBot = i * w * 0.13;
        const a = 0.055 * (1 - Math.abs(i) / (LANES + 3));
        ctx.strokeStyle = `rgba(255,94,31,${a.toFixed(3)})`;
        ctx.beginPath();
        ctx.moveTo(cx + spreadTop, hy);
        ctx.lineTo(cx + spreadBot, h + 2);
        ctx.stroke();
      }

      // lateral lines sliding toward the viewer
      const ROWS = 9;
      for (let k = 0; k < ROWS; k++) {
        const t = ((k + phase) % ROWS) / ROWS;
        const y = depthY(t);
        const a = 0.02 + t * 0.075;
        ctx.strokeStyle = `rgba(255,94,31,${a.toFixed(3)})`;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }
    }

    function drawStrip() {
      const hy = horizonY();
      const cx = w * 0.5;
      const shb = stripHalfBottom();

      // soft glow wedge over the strip
      const wedge = ctx.createLinearGradient(0, hy, 0, h);
      wedge.addColorStop(0, 'rgba(255,94,31,0.010)');
      wedge.addColorStop(1, 'rgba(255,94,31,0.035)');
      ctx.fillStyle = wedge;
      ctx.beginPath();
      ctx.moveTo(cx, hy);
      ctx.lineTo(cx - shb, h);
      ctx.lineTo(cx + shb, h);
      ctx.closePath();
      ctx.fill();

      // lane edges — brighter than the lattice
      ctx.lineWidth = 1.4;
      ctx.strokeStyle = 'rgba(255,94,31,0.22)';
      ctx.beginPath();
      ctx.moveTo(cx, hy);
      ctx.lineTo(cx - shb, h);
      ctx.moveTo(cx, hy);
      ctx.lineTo(cx + shb, h);
      ctx.stroke();
      // center line — faint dashes
      ctx.lineWidth = 1;
      ctx.strokeStyle = 'rgba(255,94,31,0.07)';
      ctx.setLineDash([6, 10]);
      ctx.beginPath();
      ctx.moveTo(cx, hy);
      ctx.lineTo(cx, h);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    function drawGates() {
      const cx = w * 0.5;
      const shb = stripHalfBottom();
      for (const gate of st.gates) {
        const s = spread(gate.t);
        const y = depthY(gate.t);
        const half = shb * s;
        const base = 0.09 + s * 0.04;
        const flash = Math.max(0, gate.flash);
        const [r, g, b] = flash > 0 ? GREEN : ORANGE;
        const a = Math.min(0.75, base + flash * 0.7);
        ctx.lineWidth = flash > 0 ? 1.8 : 1;
        ctx.strokeStyle = `rgba(${r},${g},${b},${a.toFixed(3)})`;
        ctx.beginPath();
        ctx.moveTo(cx - half, y);
        ctx.lineTo(cx + half, y);
        ctx.stroke();
        // gate posts
        ctx.fillStyle = `rgba(${r},${g},${b},${Math.min(0.9, a + 0.1).toFixed(3)})`;
        ctx.fillRect(cx - half - 1.5, y - 3.5 * s - 1, 2, 3.5 * s + 2);
        ctx.fillRect(cx + half - 0.5, y - 3.5 * s - 1, 2, 3.5 * s + 2);
      }
    }

    function updateRacers(dt) {
      const cx = w * 0.5;
      const shb = stripHalfBottom();
      for (let i = st.racers.length - 1; i >= 0; i--) {
        const rc = st.racers[i];
        if (rc.delay > 0) {
          rc.delay -= dt;
          continue;
        }
        const prevU = rc.u;
        rc.u += dt / rc.dur;
        // accelerating coverage: slow off the line, screaming at the top end.
        // Launch depth starts at t=0.80 — the visible mid-band; the very
        // bottom of the canvas is buried under the hero's black fade.
        const ease = (u) => Math.pow(Math.min(1, u), 1.75);
        const t = 0.8 - ease(rc.u) * 0.76; // depth 0.80 -> 0.04
        const s = spread(Math.max(0.02, t));
        const x = cx + rc.lane * shb * s;
        const y = depthY(Math.max(0.02, t));
        rc.trail.push({ x, y, age: 0 });
        if (rc.trail.length > 26) rc.trail.shift();

        // gate flashes on crossing
        const tPrev = 0.8 - ease(prevU) * 0.76;
        for (const gate of st.gates) {
          if (tPrev > gate.t && t <= gate.t) gate.flash = 1;
        }

        for (const p of rc.trail) p.age += dt;

        if (rc.u >= 1.12) {
          st.racers.splice(i, 1);
          continue;
        }

        // light wall down the lane
        const [r, g, b] = rc.color;
        for (let k = 1; k < rc.trail.length; k++) {
          const p0 = rc.trail[k - 1];
          const p1 = rc.trail[k];
          const fade = Math.max(0, 1 - p1.age / 0.9) * rc.dim;
          ctx.strokeStyle = `rgba(${r},${g},${b},${(0.58 * fade).toFixed(3)})`;
          ctx.lineWidth = Math.max(1.2, 3.2 * ((p1.y - horizonY()) / (h - horizonY())));
          ctx.beginPath();
          ctx.moveTo(p0.x, p0.y);
          ctx.lineTo(p1.x, p1.y);
          ctx.stroke();
        }

        // head glow (skip once past the horizon)
        if (rc.u < 1) {
          const sz = Math.max(10, 40 * (0.25 + 0.75 * s)) * rc.dim;
          ctx.globalAlpha = Math.min(1, 0.6 + s * 0.5) * rc.dim;
          ctx.drawImage(glowSprite(rc.color), x - sz / 2, y - sz / 2, sz, sz);
          ctx.globalAlpha = 1;
        }
      }
      for (const gate of st.gates) gate.flash = Math.max(0, gate.flash - dt * 2.2);
    }

    function drawStreaks(dt) {
      for (let i = st.streaks.length - 1; i >= 0; i--) {
        const s = st.streaks[i];
        s.x += s.speed * dt;
        if (s.x > 1.35) {
          st.streaks.splice(i, 1);
          continue;
        }
        const y = depthY(s.depth);
        const scale = 0.45 + s.depth * 0.8;
        const headX = s.x * w;
        const trailLen = w * (s.boost ? 0.34 : 0.22) * scale;
        const [r, g, b] = s.color;

        const tg = ctx.createLinearGradient(headX - trailLen, y, headX, y);
        tg.addColorStop(0, `rgba(${r},${g},${b},0)`);
        tg.addColorStop(1, `rgba(${r},${g},${b},${0.55 * scale})`);
        ctx.strokeStyle = tg;
        ctx.lineWidth = Math.max(1, 2.4 * scale);
        ctx.beginPath();
        ctx.moveTo(headX - trailLen, y);
        ctx.lineTo(headX, y);
        ctx.stroke();

        const sz = Math.max(10, 26 * scale);
        ctx.globalAlpha = Math.min(1, 0.95 * scale + 0.2);
        ctx.drawImage(glowSprite(s.color), headX - sz / 2, y - sz / 2, sz, sz);
        ctx.globalAlpha = 1;
      }
    }

    function drawFrame(dt) {
      ctx.clearRect(0, 0, w, h);
      drawGrid(st.phase);
      drawStrip();
      drawGates();
      if (!reduced) {
        updateRacers(dt);
        drawStreaks(dt);
      }
    }

    function tick(ts) {
      if (!st.running) return;
      const dt = Math.min(0.05, (ts - st.lastTs) / 1000 || 0.016);
      st.lastTs = ts;
      st.phase = (st.phase + dt * 0.55) % 9;

      // ambient crossing traffic
      st.lastSpawn += dt;
      if (st.lastSpawn > 2.4 + Math.random() * 2.2 && st.streaks.length < 4) {
        st.lastSpawn = 0;
        st.streaks.push({
          depth: 0.15 + Math.random() * 0.75,
          x: -0.15,
          speed: 0.55 + Math.random() * 0.5,
          color: Math.random() < 0.12 ? MINT : ORANGE,
        });
      }

      // occasional solo practice run down the strip (dimmer than a launch)
      st.lastSolo += dt;
      if (st.lastSolo > 7 + Math.random() * 4 && st.racers.length === 0) {
        st.lastSolo = 0;
        st.racers.push({
          lane: Math.random() < 0.5 ? -0.45 : 0.45,
          u: 0,
          dur: 2.1,
          delay: 0,
          color: ORANGE,
          trail: [],
          dim: 0.55,
        });
      }

      drawFrame(dt);
      st.raf = requestAnimationFrame(tick);
    }

    const start = () => {
      if (reduced || st.running || !st.visible || document.hidden) return;
      st.running = true;
      st.lastTs = performance.now();
      st.raf = requestAnimationFrame(tick);
    };
    const stop = () => {
      st.running = false;
      cancelAnimationFrame(st.raf);
    };

    const ro = new ResizeObserver(resize);
    ro.observe(canvas);
    resize();

    if (reduced) {
      drawFrame(0);
      return () => ro.disconnect();
    }

    const io = new IntersectionObserver(
      ([entry]) => {
        st.visible = entry.isIntersecting;
        if (entry.isIntersecting) start();
        else stop();
      },
      { threshold: 0.05 }
    );
    io.observe(canvas);

    const onVis = () => (document.hidden ? stop() : start());
    document.addEventListener('visibilitychange', onVis);

    return () => {
      stop();
      io.disconnect();
      ro.disconnect();
      document.removeEventListener('visibilitychange', onVis);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className={`pointer-events-none absolute inset-0 h-full w-full ${className}`}
    />
  );
}
