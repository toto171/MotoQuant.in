'use client';

/**
 * TronScene3D — WebGL light-cycle arena (July 2026, Tron: Legacy pass).
 *
 * The hero backdrop upgraded from the 2D canvas to a real perspective scene:
 *  - shader-drawn infinite grid floor scrolling toward the viewer, with
 *    anti-aliased minor/major lines and horizon distance fade
 *  - light cycles riding the lattice, cornering at 90°, each dragging a
 *    persisting ribbon light-wall that decays from the tail
 *  - faked floor reflections (the classic mirrored-geometry trick: walls and
 *    head glows re-rendered at y→−y through the additive, mostly-transparent
 *    floor at ~⅓ intensity)
 *  - horizon glow band + white-hot head sprites
 *  - scroll parallax on the camera (rises + pitches down as the hero scrolls)
 *  - `launchSignal` contract identical to TronGrid: each increment fires a
 *    4-cycle boost burst (one mint) straight across the arena
 *
 * Engineering discipline:
 *  - Loaded ONLY via TronBackdrop (next/dynamic, ssr:false) on ≥lg,
 *    motion-OK, WebGL-capable clients; TronGrid 2D remains the fallback.
 *  - rAF runs only while on screen (IntersectionObserver) and the tab is
 *    visible; ResizeObserver drives renderer sizing; DPR capped at 1.75.
 *  - No lights, no shadows — everything is additive unlit shader work.
 *  - Full disposal on unmount (geometries, materials, textures, renderer,
 *    explicit WEBGL_lose_context release).
 */

import { useEffect, useRef } from 'react';
import * as THREE from 'three';

const ORANGE = new THREE.Color(0xff5e1f);
const MINT = new THREE.Color(0x00ffb2);

// Arena layout (world units). The lattice cell matches the grid shader.
const CELL = 4;
const X_BOUND = 72;
const Z_FAR = -150;
const Z_NEAR = 12;
const MAX_TRAIL = 96; // ribbon points per cycle
const WALL_H = 1.35;

// ── shaders ────────────────────────────────────────────────────────────────

const GRID_VERT = /* glsl */ `
  varying vec2 vWorld;
  void main() {
    vec4 wp = modelMatrix * vec4(position, 1.0);
    vWorld = wp.xz;
    gl_Position = projectionMatrix * viewMatrix * wp;
  }
`;

const GRID_FRAG = /* glsl */ `
  precision highp float;
  uniform float uTime;
  uniform vec3 uColor;
  varying vec2 vWorld;

  float lineMask(vec2 p, float width) {
    vec2 g = abs(fract(p) - 0.5) / (fwidth(p) * width);
    return 1.0 - min(min(g.x, g.y), 1.0);
  }

  void main() {
    // scroll the lattice toward the viewer
    vec2 p = vec2(vWorld.x, vWorld.y - uTime * 6.0) / ${CELL.toFixed(1)};
    float minor = lineMask(p, 1.1) * 0.36;
    float major = lineMask(p / 4.0, 1.4) * 0.66;
    float glow  = lineMask(p / 4.0, 6.0) * 0.12; // soft halo around majors
    float i = max(minor, major) + glow;

    // fade with distance from the camera line (z) and at the side edges
    float depth = clamp((vWorld.y - ${Z_FAR.toFixed(1)}) / ${(Z_NEAR - Z_FAR).toFixed(1)}, 0.0, 1.0);
    float fade = smoothstep(0.02, 0.45, depth) * (1.0 - smoothstep(0.93, 1.0, depth));
    fade *= 1.0 - smoothstep(0.55, 1.0, abs(vWorld.x) / ${X_BOUND.toFixed(1)});

    gl_FragColor = vec4(uColor * i * fade, i * fade);
  }
`;

const WALL_VERT = /* glsl */ `
  attribute float aAlpha;
  varying float vAlpha;
  varying float vY;
  void main() {
    vAlpha = aAlpha;
    vY = position.y;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const WALL_FRAG = /* glsl */ `
  precision highp float;
  uniform vec3 uColor;
  uniform float uGain;
  uniform float uWallH;
  varying float vAlpha;
  varying float vY;
  void main() {
    // hot ridge at the top edge of the wall (where the cycle passed),
    // translucent sheet below — the Tron: Legacy light-wall read.
    float y = clamp(abs(vY) / uWallH, 0.0, 1.0);
    float sheet = mix(0.42, 0.14, y);
    float ridge = smoothstep(0.82, 1.0, y) * 1.0;
    float a = vAlpha * (sheet + ridge) * uGain;
    vec3 c = mix(uColor, vec3(1.0), ridge * 0.55);
    gl_FragColor = vec4(c * a, a);
  }
`;

const HORIZON_VERT = /* glsl */ `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const HORIZON_FRAG = /* glsl */ `
  precision highp float;
  uniform vec3 uColor;
  varying vec2 vUv;
  void main() {
    float band = exp(-pow((vUv.y - 0.5) * 4.2, 2.0));
    float side = 1.0 - smoothstep(0.55, 1.0, abs(vUv.x - 0.5) * 2.0);
    float a = band * side * 0.22;
    gl_FragColor = vec4(uColor * a, a);
  }
`;

// ── helpers ────────────────────────────────────────────────────────────────

function makeGlowTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 64;
  const g = c.getContext('2d');
  const grad = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  grad.addColorStop(0, 'rgba(255,255,255,1)');
  grad.addColorStop(0.25, 'rgba(255,255,255,0.55)');
  grad.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = grad;
  g.fillRect(0, 0, 64, 64);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

const HEADINGS = [
  [1, 0],
  [-1, 0],
  [0, 1],
  [0, -1],
];

export default function TronScene3D({ launchSignal = 0, className = '' }) {
  const hostRef = useRef(null);
  const burstQueue = useRef(0);
  const prevLaunch = useRef(launchSignal);

  useEffect(() => {
    if (launchSignal === prevLaunch.current) return;
    prevLaunch.current = launchSignal;
    burstQueue.current += 1;
  }, [launchSignal]);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return undefined;

    let renderer;
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
        powerPreference: 'low-power',
      });
    } catch {
      return undefined; // wrapper already gated on WebGL, but belt-and-braces
    }
    renderer.setClearColor(0x000000, 0);
    renderer.setPixelRatio(Math.min(1.75, window.devicePixelRatio || 1));
    const canvas = renderer.domElement;
    canvas.setAttribute('aria-hidden', 'true');
    canvas.setAttribute('data-engine', 'tron-3d');
    canvas.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;pointer-events:none;';
    host.appendChild(canvas);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(55, 1, 0.1, 420);
    const CAM_BASE_Y = 3.4;
    camera.position.set(0, CAM_BASE_Y, 26);
    camera.lookAt(0, 1.0, -70);

    const disposables = [];
    const track = (r) => {
      disposables.push(r);
      return r;
    };

    // floor
    const gridMat = track(
      new THREE.ShaderMaterial({
        vertexShader: GRID_VERT,
        fragmentShader: GRID_FRAG,
        uniforms: { uTime: { value: 0 }, uColor: { value: ORANGE.clone() } },
        transparent: true,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      })
    );
    const gridGeo = track(new THREE.PlaneGeometry(X_BOUND * 2.6, Z_NEAR - Z_FAR + 40));
    const grid = new THREE.Mesh(gridGeo, gridMat);
    grid.rotation.x = -Math.PI / 2;
    grid.position.z = (Z_FAR + Z_NEAR) / 2;
    scene.add(grid);

    // horizon glow band
    const horizonMat = track(
      new THREE.ShaderMaterial({
        vertexShader: HORIZON_VERT,
        fragmentShader: HORIZON_FRAG,
        uniforms: { uColor: { value: ORANGE.clone() } },
        transparent: true,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      })
    );
    const horizonGeo = track(new THREE.PlaneGeometry(560, 26));
    const horizon = new THREE.Mesh(horizonGeo, horizonMat);
    horizon.position.set(0, 2.0, Z_FAR - 4);
    scene.add(horizon);

    const glowTex = track(makeGlowTexture());

    // ── light cycles ──────────────────────────────────────────────────────
    const cycles = [];

    function makeRibbon(color, wallH) {
      const geo = new THREE.BufferGeometry();
      const positions = new Float32Array(MAX_TRAIL * 2 * 3);
      const alphas = new Float32Array(MAX_TRAIL * 2);
      geo.setAttribute('position', new THREE.BufferAttribute(positions, 3).setUsage(THREE.DynamicDrawUsage));
      geo.setAttribute('aAlpha', new THREE.BufferAttribute(alphas, 1).setUsage(THREE.DynamicDrawUsage));
      const index = new Uint16Array((MAX_TRAIL - 1) * 6);
      for (let i = 0; i < MAX_TRAIL - 1; i++) {
        const v = i * 2;
        index.set([v, v + 1, v + 2, v + 1, v + 3, v + 2], i * 6);
      }
      geo.setIndex(new THREE.BufferAttribute(index, 1));
      geo.setDrawRange(0, 0);
      // Ribbons rebuild every frame in world space; skip culling rather than
      // recompute bounds (the arena always spans the frustum anyway).
      geo.boundingSphere = new THREE.Sphere(new THREE.Vector3(0, 0, -60), 400);

      const mkMat = (gain) =>
        new THREE.ShaderMaterial({
          vertexShader: WALL_VERT,
          fragmentShader: WALL_FRAG,
          uniforms: {
            uColor: { value: color.clone() },
            uGain: { value: gain },
            uWallH: { value: wallH },
          },
          transparent: true,
          blending: THREE.AdditiveBlending,
          depthWrite: false,
          side: THREE.DoubleSide,
        });
      const wallMat = mkMat(1.0);
      const mirrorMat = mkMat(0.32); // faked floor reflection
      const wall = new THREE.Mesh(geo, wallMat);
      const mirror = new THREE.Mesh(geo, mirrorMat);
      mirror.scale.y = -1;
      scene.add(wall);
      scene.add(mirror);
      return { geo, wallMat, mirrorMat, wall, mirror };
    }

    function makeHead(color) {
      const mat = new THREE.SpriteMaterial({
        map: glowTex,
        color: 0xffffff,
        transparent: true,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      });
      const halo = new THREE.SpriteMaterial({
        map: glowTex,
        color: color.clone(),
        transparent: true,
        opacity: 0.65,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      });
      const core = new THREE.Sprite(mat);
      core.scale.set(1.5, 1.5, 1);
      const glow = new THREE.Sprite(halo);
      glow.scale.set(4.2, 4.2, 1);
      const refl = new THREE.Sprite(halo.clone());
      refl.material.opacity = 0.22;
      refl.scale.set(3.4, 3.4, 1);
      scene.add(core);
      scene.add(glow);
      scene.add(refl);
      return { core, glow, refl, mats: [mat, halo, refl.material] };
    }

    function spawnCycle({ boost = false, mint = false, lag = 0 } = {}) {
      const color = mint ? MINT : ORANGE;
      const heading = boost
        ? [1, 0]
        : HEADINGS[Math.floor(Math.random() * HEADINGS.length)];
      const lane = (n) => Math.round(n / CELL) * CELL;
      const x = boost
        ? -X_BOUND - lag * 8 // staggered wave front entering from the left
        : lane(THREE.MathUtils.randFloatSpread(X_BOUND * 1.4));
      // boost cycles run the NEAR lanes so the burst sweeps big across the
      // frame — the launch payoff, not distant background traffic
      const z = boost
        ? lane(THREE.MathUtils.randFloat(-64, -16))
        : lane(THREE.MathUtils.randFloat(-120, -20));
      const wallH = boost ? WALL_H * 1.7 : WALL_H;
      cycles.push({
        x,
        z,
        heading,
        speed: boost ? THREE.MathUtils.randFloat(38, 54) : THREE.MathUtils.randFloat(9, 15),
        boost,
        wallH,
        life: 0,
        nextTurn: boost ? Infinity : THREE.MathUtils.randFloat(0.9, 2.4),
        trail: [{ x, z, t: 0 }],
        clock: 0,
        dying: false,
        ...makeRibbon(color, wallH),
        head: makeHead(color),
      });
    }

    function killCycle(c) {
      scene.remove(c.wall, c.mirror, c.head.core, c.head.glow, c.head.refl);
      c.geo.dispose();
      c.wallMat.dispose();
      c.mirrorMat.dispose();
      c.head.mats.forEach((m) => m.dispose());
    }

    const TRAIL_LIFE = 2.6;

    function updateCycle(c, dt) {
      c.clock += dt;
      if (!c.dying) {
        c.life += dt;
        c.x += c.heading[0] * c.speed * dt;
        c.z += c.heading[1] * c.speed * dt;

        // 90° corner on the lattice
        if (c.clock > c.nextTurn) {
          c.clock = 0;
          c.nextTurn = THREE.MathUtils.randFloat(0.9, 2.6);
          c.x = Math.round(c.x / CELL) * CELL;
          c.z = Math.round(c.z / CELL) * CELL;
          const [hx, hz] = c.heading;
          const left = [hz, -hx];
          const right = [-hz, hx];
          let turn = Math.random() < 0.5 ? left : right;
          // steer back toward the arena when drifting out
          if (c.x > X_BOUND * 0.7) turn = [-1, 0];
          else if (c.x < -X_BOUND * 0.7) turn = [1, 0];
          else if (c.z < Z_FAR * 0.85) turn = [0, 1];
          else if (c.z > -14) turn = [0, -1];
          c.heading = turn;
        }

        const last = c.trail[c.trail.length - 1];
        const moved = Math.hypot(c.x - last.x, c.z - last.z);
        if (moved > 0.6) c.trail.push({ x: c.x, z: c.z, t: 0 });
        else {
          last.x = c.x;
          last.z = c.z;
        }

        // boost cycles enter from beyond the left edge (staggered lag) and
        // die only on the right exit; ambient traffic dies on any bound
        const out = c.boost
          ? c.x > X_BOUND
          : Math.abs(c.x) > X_BOUND + 6 || c.z < Z_FAR - 6 || c.z > Z_NEAR;
        if (out) c.dying = true;
      }

      // age + prune the trail
      for (const p of c.trail) p.t += dt;
      while (c.trail.length && c.trail[0].t > TRAIL_LIFE) c.trail.shift();
      if (c.dying && c.trail.length < 2) return false;

      // rebuild ribbon attributes
      const n = Math.min(c.trail.length, MAX_TRAIL);
      const start = c.trail.length - n;
      const pos = c.geo.attributes.position.array;
      const alp = c.geo.attributes.aAlpha.array;
      for (let i = 0; i < n; i++) {
        const p = c.trail[start + i];
        const a = Math.max(0, 1 - p.t / TRAIL_LIFE);
        const hgt = c.wallH * (0.35 + 0.65 * a);
        const v = i * 2;
        pos[v * 3] = p.x;
        pos[v * 3 + 1] = 0;
        pos[v * 3 + 2] = p.z;
        pos[v * 3 + 3] = p.x;
        pos[v * 3 + 4] = hgt;
        pos[v * 3 + 5] = p.z;
        alp[v] = a;
        alp[v + 1] = a;
      }
      c.geo.attributes.position.needsUpdate = true;
      c.geo.attributes.aAlpha.needsUpdate = true;
      c.geo.setDrawRange(0, Math.max(0, (n - 1) * 6));

      // head sprites
      const headA = c.dying ? 0 : 1;
      c.head.core.position.set(c.x, 0.55, c.z);
      c.head.glow.position.set(c.x, 0.6, c.z);
      c.head.refl.position.set(c.x, -0.6, c.z);
      c.head.core.material.opacity = headA;
      c.head.glow.material.opacity = 0.65 * headA;
      c.head.refl.material.opacity = 0.22 * headA;
      return true;
    }

    // ── loop + lifecycle ──────────────────────────────────────────────────
    const st = { running: false, visible: false, raf: 0, lastTs: 0, spawnT: 0, time: 0 };
    const scrollRef = { p: 0 };

    const onScroll = () => {
      scrollRef.p = Math.min(1, Math.max(0, window.scrollY / Math.max(1, window.innerHeight)));
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();

    function tick(ts) {
      if (!st.running) return;
      const dt = Math.min(0.05, (ts - st.lastTs) / 1000 || 0.016);
      st.lastTs = ts;
      st.time += dt;
      gridMat.uniforms.uTime.value = st.time;

      // scroll parallax — camera lifts and pitches down as the hero scrolls
      const p = scrollRef.p;
      camera.position.y = CAM_BASE_Y + p * 3.2;
      camera.position.z = 26 - p * 4;
      camera.lookAt(0, 1.0 - p * 2.2, -70);

      // ambient traffic
      st.spawnT += dt;
      const ambient = cycles.filter((c) => !c.boost).length;
      if (st.spawnT > 2.2 && ambient < 5) {
        st.spawnT = 0;
        spawnCycle({ mint: Math.random() < 0.12 });
      }

      // launch bursts from the christmas tree
      while (burstQueue.current > 0) {
        burstQueue.current -= 1;
        for (let i = 0; i < 4; i++) spawnCycle({ boost: true, mint: i === 2, lag: i });
      }

      for (let i = cycles.length - 1; i >= 0; i--) {
        if (!updateCycle(cycles[i], dt)) {
          killCycle(cycles[i]);
          cycles.splice(i, 1);
        }
      }

      renderer.render(scene, camera);
      st.raf = requestAnimationFrame(tick);
    }

    const start = () => {
      if (st.running || !st.visible || document.hidden) return;
      st.running = true;
      st.lastTs = performance.now();
      st.raf = requestAnimationFrame(tick);
    };
    const stop = () => {
      st.running = false;
      cancelAnimationFrame(st.raf);
    };

    const resize = () => {
      const rect = host.getBoundingClientRect();
      const w = Math.max(1, rect.width);
      const h = Math.max(1, rect.height);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h, false);
    };
    const ro = new ResizeObserver(resize);
    ro.observe(host);
    resize();

    const io = new IntersectionObserver(
      ([entry]) => {
        st.visible = entry.isIntersecting;
        if (entry.isIntersecting) start();
        else stop();
      },
      { threshold: 0.05 }
    );
    io.observe(host);

    const onVis = () => (document.hidden ? stop() : start());
    document.addEventListener('visibilitychange', onVis);
    const onCtxLost = (e) => {
      e.preventDefault();
      stop();
    };
    const onCtxRestored = () => start();
    canvas.addEventListener('webglcontextlost', onCtxLost);
    canvas.addEventListener('webglcontextrestored', onCtxRestored);

    return () => {
      stop();
      io.disconnect();
      ro.disconnect();
      window.removeEventListener('scroll', onScroll);
      document.removeEventListener('visibilitychange', onVis);
      canvas.removeEventListener('webglcontextlost', onCtxLost);
      canvas.removeEventListener('webglcontextrestored', onCtxRestored);
      cycles.forEach(killCycle);
      cycles.length = 0;
      disposables.forEach((d) => d.dispose());
      renderer.dispose();
      renderer.getContext()?.getExtension('WEBGL_lose_context')?.loseContext();
      canvas.remove();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div
      ref={hostRef}
      aria-hidden="true"
      className={`pointer-events-none absolute inset-0 h-full w-full ${className}`}
    />
  );
}
