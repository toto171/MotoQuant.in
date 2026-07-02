'use client';

/**
 * TronGrid — light-cycle hero background (July 2026, operator-directed).
 *
 * A perspective wireframe floor drifting toward the viewer with Tron-style
 * light-cycle streaks racing across its lanes, each dragging a fading light
 * wall — the drag-strip-at-night rendered in the site's own signal colors.
 *
 * Integration: `launchSignal` (a counter) fires a multi-streak burst — the
 * page wires it to LaunchControl's green-light release, so a perfect launch
 * on the christmas tree sends light cycles tearing across the grid.
 *
 * Engineering discipline:
 *  - Canvas 2D, zero dependencies, one rAF loop.
 *  - Runs ONLY while on screen (IntersectionObserver) and the tab is
 *    visible (visibilitychange); resize via ResizeObserver, DPR capped at 2.
 *  - prefers-reduced-motion: draws one static grid frame, no animation.
 *  - pointer-events-none, aria-hidden; sits behind the hero's own glows.
 */

import { useEffect, useRef } from 'react';

const ORANGE = [255, 94, 31];
const MINT = [0, 255, 178];

export default function TronGrid({ launchSignal = 0, className = '' }) {
  const canvasRef = useRef(null);
  const stateRef = useRef({
    streaks: [],
    phase: 0,
    lastSpawn: 0,
    running: false,
    visible: false,
    raf: 0,
    lastTs: 0,
  });

  // Fire a burst when the launch counter increments (skip initial mount).
  const prevLaunch = useRef(launchSignal);
  useEffect(() => {
    if (launchSignal === prevLaunch.current) return;
    prevLaunch.current = launchSignal;
    const st = stateRef.current;
    for (let i = 0; i < 4; i++) {
      st.streaks.push({
        depth: 0.18 + Math.random() * 0.72,
        x: -0.15 - i * 0.07,
        speed: 1.6 + Math.random() * 0.9, // screen-widths per second
        color: i === 2 ? MINT : ORANGE,
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
      if (reduced) drawFrame(0); // keep the static frame crisp on resize
    };

    // Perspective helpers: depth t ∈ [0..1], 0 = horizon, 1 = viewer.
    const horizonY = () => h * 0.44;
    const depthY = (t) => horizonY() + (h - horizonY()) * Math.pow(t, 2.1);

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

    function drawStreaks(dt) {
      for (let i = st.streaks.length - 1; i >= 0; i--) {
        const s = st.streaks[i];
        s.x += s.speed * dt;
        if (s.x > 1.35) {
          st.streaks.splice(i, 1);
          continue;
        }
        const y = depthY(s.depth);
        const scale = 0.45 + s.depth * 0.8; // nearer lanes = bigger, brighter
        const headX = s.x * w;
        const trailLen = w * (s.boost ? 0.34 : 0.22) * scale;
        const [r, g, b] = s.color;

        // light wall (fading trail)
        const tg = ctx.createLinearGradient(headX - trailLen, y, headX, y);
        tg.addColorStop(0, `rgba(${r},${g},${b},0)`);
        tg.addColorStop(1, `rgba(${r},${g},${b},${0.55 * scale})`);
        ctx.strokeStyle = tg;
        ctx.lineWidth = Math.max(1, 2.4 * scale);
        ctx.beginPath();
        ctx.moveTo(headX - trailLen, y);
        ctx.lineTo(headX, y);
        ctx.stroke();

        // head — hot core with glow
        ctx.save();
        ctx.shadowColor = `rgba(${r},${g},${b},0.9)`;
        ctx.shadowBlur = 12 * scale;
        ctx.fillStyle = `rgba(255,255,255,${0.9 * scale})`;
        ctx.beginPath();
        ctx.arc(headX, y, Math.max(1.2, 2.1 * scale), 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }
    }

    function drawFrame(dt) {
      ctx.clearRect(0, 0, w, h);
      drawGrid(st.phase);
      if (!reduced) drawStreaks(dt);
    }

    function tick(ts) {
      if (!st.running) return;
      const dt = Math.min(0.05, (ts - st.lastTs) / 1000 || 0.016);
      st.lastTs = ts;
      st.phase = (st.phase + dt * 0.55) % 9; // grid drift toward viewer

      // ambient light-cycle traffic
      st.lastSpawn += dt;
      if (st.lastSpawn > 2.4 + Math.random() * 2.2 && st.streaks.length < 5) {
        st.lastSpawn = 0;
        st.streaks.push({
          depth: 0.15 + Math.random() * 0.75,
          x: -0.15,
          speed: 0.55 + Math.random() * 0.5,
          color: Math.random() < 0.12 ? MINT : ORANGE,
          boost: false,
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
      drawFrame(0); // single static frame — the grid without motion
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
