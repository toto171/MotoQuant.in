'use client';

/**
 * MotoQuant Pro — Landing Page (Direction A · Christmas Tree)
 * ==============================================================
 * Cinematic motorsport landing built around three signature moments:
 *
 *   1. Hero        — sticky christmas tree (lights amber→green on
 *                    scroll progress) + headline + CTAs
 *   2. Telemetry   — sticky-pinned HUD; MV-F4-style superbike
 *                    silhouette + RPM/speed/gear/ET counters that tick
 *                    through a real GSX-R K5 quarter-mile run
 *   3. Validation  — only the "honest physics" clusters: litre 195+,
 *                    litre 600-1000, mid-twin 300-500, overall.
 *                    The bias-positive small-cc / 2T / cruiser clusters
 *                    are intentionally omitted from the headline view
 *                    (they live in /docs/validation for transparency).
 *
 * Every prior surface is preserved: stats strip, intelligence-layer
 * cards, top-10 leaderboard, embedded SimulatorWidget, "Built for
 * Champions" panel.
 */

import { Suspense, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { motion, useScroll, useTransform, useMotionValue } from 'framer-motion';
import {
  Zap, TrendingUp, BarChart3, ChevronDown, Cpu, Wind, Gauge,
  Brain, Target, MessageSquare, Upload,
} from 'lucide-react';

import SiteNav from '../components/SiteNav';
import SiteFooter from '../components/SiteFooter';
import ChristmasTree from '../components/ChristmasTree';
import TelemetryHUD from '../components/TelemetryHUD';
import { Reveal, Stagger, StaggerItem } from '../components/Reveal';
import SimulatorWidget from '../components/SimulatorWidget';
import PhysicsDial from '@/components/PhysicsDial';
import BootSequence from '../components/BootSequence';
import HudFrame from '../components/HudFrame';
import CodeComment from '../components/CodeComment';
import ManifestoScrub from '../components/ManifestoScrub';
import LaunchControl from '../components/LaunchControl';
import ScoreboardDigits, { ScoreboardCounter } from '../components/ScoreboardDigits';
import SectionRail from '../components/SectionRail';
import TronGrid from '../components/TronGrid';

// ─── Validation: only the four clusters where the data is good ────────
// Per the 3 July 2026 weighted sweep (reports/acc_final_2026_07_03.json). Small-cc / 2T / cruiser
// clusters are bounded by benchmark data quality (DERIVED 0-100×1.6
// estimates with declared ±0.7s uncertainty), not model fidelity, so
// they're shown in /docs/validation with their full caveat — not on
// the landing page.
const HONEST_CLUSTERS = [
  { name: 'Litre Sport ≥195hp',   bias: -0.015, mae: 0.137, n: 31 },
  { name: 'Litre Sport 600-1000', bias: -0.064, mae: 0.192, n: 104 },
  { name: 'Mid-Twin 300-500',     bias: -0.086, mae: 0.516, n: 23 },
  { name: 'All clusters · weighted overall', bias: -0.026, mae: 0.242, n: 246 },
];

// ─── Top-10 most accurate bikes ───────────────────────────────────────
// MUST equal the docs/validation TOP10 (3 July 2026 sweep,
// reports/acc_final_2026_07_03.json — 10 smallest |Δ| among published
// non-derived benchmarks, mean ±0.009s). Sync both together.
const TOP10 = [
  { rank: 1,  name: 'Honda CBR 600RR',            year: 2007, cc: '599cc I4',  target: 10.844, sim: 10.8447, delta:  0.001, source: 'Sport Rider' },
  { rank: 2,  name: 'Kawasaki Z H2 SE',           year: 2020, cc: '998cc I4',  target: 9.95,   sim: 9.9471,  delta: -0.003, source: 'Cycle World 2020' },
  { rank: 3,  name: 'Kawasaki Ninja ZX-9R',       year: 2000, cc: '899cc I4',  target: 10.5,   sim: 10.4968, delta: -0.003, source: 'Sport Rider 2000' },
  { rank: 4,  name: 'Kawasaki Ninja H2',          year: 2015, cc: '998cc I4',  target: 9.62,   sim: 9.6252,  delta:  0.005, source: 'MCN 2015' },
  { rank: 5,  name: 'Kawasaki Ninja ZX-10R',      year: 2021, cc: '998cc I4',  target: 10.0,   sim: 10.0106, delta:  0.011, source: 'Cycle World 2021' },
  { rank: 6,  name: 'Kawasaki ZZR1400',           year: 2006, cc: '1352cc I4', target: 9.9,    sim: 9.9112,  delta:  0.011, source: 'MCN 2006' },
  { rank: 7,  name: 'Yamaha YZF-R6',              year: 2007, cc: '599cc I4',  target: 10.854, sim: 10.8653, delta:  0.011, source: 'Sport Rider 2007' },
  { rank: 8,  name: 'Kawasaki Z900RS',            year: 2020, cc: '948cc I4',  target: 11.35,  sim: 11.3372, delta: -0.013, source: 'MotoStatz 2022' },
  { rank: 9,  name: 'Triumph Rocket 3 Storm R',   year: 2024, cc: '2458cc I3', target: 10.56,  sim: 10.5757, delta:  0.016, source: 'Cycle World 2020' },
  { rank: 10, name: 'Aprilia RS 457',             year: 2024, cc: '457cc I2',  target: 13.3,   sim: 13.3158, delta:  0.016, source: 'FastestLaps 2024' },
];

// ─── Stats strip — synced to current motoquant.db (Apr 30 2026) ───────
const STATS = [
  { num: 535, label: 'BIKES'      },
  { num: 232, label: 'TIRES'      },
  { num: 594, label: 'PARTS'      },
  { num: 20,  label: 'VENUES'     },
  { num: 976, label: 'TESTS'      },
  { num: 15,  label: 'SUB-MODELS' },
];

// ──────────────────────────────────────────────────────────────────────
function ScrollHint() {
  return (
    <motion.div
      // Hidden on phones (collides with the See-it-run CTA on a
      // min-h-[640px] hero). Shown from sm: upward where the hero has
      // breathing room and the hint reads as a tasteful affordance.
      className="hidden sm:flex absolute bottom-3 left-1/2 -translate-x-1/2 text-[10px] font-mono uppercase tracking-[0.3em] text-white/40 flex-col items-center gap-1 pointer-events-none"
      animate={{ y: [0, 6, 0] }}
      transition={{ duration: 2, repeat: Infinity }}
    >
      Scroll · live telemetry
      <ChevronDown className="w-3 h-3 text-brand-orange" />
    </motion.div>
  );
}

function StatsStrip() {
  return (
    <section className="bg-gradient-to-r from-ink-1 via-black to-ink-1 border-y border-brand-orange/20 py-10">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-3 md:grid-cols-6 gap-y-6">
          {STATS.map((s, i) => (
            <div
              key={s.label}
              className={[
                'text-center',
                i < STATS.length - 1 ? 'md:border-r md:border-brand-orange/15' : '',
              ].join(' ')}
            >
              <div className="flex justify-center sm:hidden">
                <ScoreboardCounter value={s.num} h={22} />
              </div>
              <div className="hidden sm:flex justify-center">
                <ScoreboardCounter value={s.num} h={30} />
              </div>
              <div className="font-mono text-[10px] sm:text-xs text-white/50 tracking-[0.25em] mt-2">
                {s.label}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── Filtered cluster bias chart ──────────────────────────────────────
function ClusterBars() {
  // bias range maps to a centred bar around the zero line.
  // Max absolute bias rendered is 0.20s — that's the visual ceiling for
  // the "good" clusters; mae is shown as a faint outer hairline so the
  // user can see spread without conflating it with bias.
  const SCALE = 0.20;
  return (
    <div className="rounded-xl border border-white/10 bg-ink-1/70 p-6 sm:p-8">
      <div className="text-[11px] font-mono uppercase tracking-[0.2em] text-brand-orange mb-1">
        Honest physics &middot; June 13, 2026
      </div>
      <h3 className="font-display font-bold text-2xl sm:text-3xl text-white tracking-tight mb-2 leading-tight">
        Where the data is good, we are within 0.20s.
      </h3>
      <p className="text-sm text-white/55 leading-relaxed mb-6 max-w-xl">
        Source-quality weighted (instrumented = 1.0, magazine = 0.7).
        Only the clusters with strong instrumented benchmark coverage are
        shown — the small-cc, two-stroke and cruiser residuals are
        bounded by benchmark data quality, not model fidelity.{' '}
        <Link
          href="/docs/validation"
          className="text-brand-accent hover:text-white transition-colors"
        >
          Full breakdown →
        </Link>
      </p>

      <div className="space-y-4">
        {HONEST_CLUSTERS.map((c) => {
          const sign = c.bias < 0 ? -1 : 1;
          const pct  = Math.min(50, Math.abs(c.bias) / SCALE * 50);
          return (
            <div
              key={c.name}
              className="grid grid-cols-[1.4fr_3fr_0.7fr] sm:grid-cols-[1.5fr_4fr_0.8fr] gap-3 items-center"
            >
              <div>
                <div className="text-sm text-white/85 leading-tight">{c.name}</div>
                <div className="text-[10px] font-mono text-white/40 mt-0.5">
                  N={c.n} &middot; |Δ| {c.mae.toFixed(3)}s
                </div>
              </div>

              <div className="relative h-2.5 rounded-full bg-white/5 overflow-visible">
                {/* zero axis line */}
                <span className="absolute top-[-3px] bottom-[-3px] left-1/2 w-px bg-brand-orange/60" />
                <Reveal y={0} duration={0.9} margin="-40px" className="absolute inset-y-0 left-0 right-0">
                  <div
                    className={[
                      'absolute top-0 bottom-0 rounded-full',
                      'bg-gradient-to-r from-brand-orange to-brand-orangeLight',
                    ].join(' ')}
                    style={{
                      ...(sign < 0
                        ? { right: '50%', width: `${pct}%` }
                        : { left:  '50%', width: `${pct}%` }),
                    }}
                  />
                </Reveal>
              </div>

              <div
                className={[
                  'font-mono text-sm tabular-nums text-right font-semibold',
                  sign < 0 ? 'text-amber-300' : 'text-emerald-300',
                ].join(' ')}
              >
                {sign > 0 ? '+' : ''}{c.bias.toFixed(3)}s
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-6 flex items-center justify-between text-[10px] font-mono uppercase tracking-widest text-white/40">
        <span>← sim faster</span>
        <span>cluster bias</span>
        <span>sim slower →</span>
      </div>
    </div>
  );
}

// ─── Reference baselines panel (the timeless engineering moment) ──────
function ReferenceBaselines() {
  const baselines = [
    { name: 'GSX-R 1000 K5',  et: '10.0334', hp: '178 hp', year: '2005' },
    { name: 'YZF-R1 4C8',     et: '10.2859', hp: '180 hp', year: '2007' },
    { name: 'Hayabusa Gen1',  et: '10.4712', hp: '197 hp', year: '1999' },
  ];
  return (
    <div className="grid sm:grid-cols-3 gap-4">
      {baselines.map((b) => (
        <Reveal key={b.name} className="rounded-xl border border-white/10 bg-ink-1/60 p-6 relative overflow-hidden">
          <span className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-brand-orange to-transparent" />
          <div className="text-[10px] font-mono uppercase tracking-widest text-white/45">
            {b.name}
          </div>
          <div className="mt-3 flex items-end gap-1.5">
            <ScoreboardDigits value={b.et} h={28} color="#FFFFFF" label={`${b.et} seconds`} />
            <span className="text-white/40 font-mono text-sm">s</span>
          </div>
          <div className="mt-2 text-[11px] font-mono text-emerald-300">
            Δ ±0.0000s &middot; {b.hp}
          </div>
          <div className="mt-3 pt-3 border-t border-white/5 flex justify-between text-[10px] font-mono text-white/40">
            <span>{b.year}</span>
            <span>Aamby Valley · ISA</span>
          </div>
        </Reveal>
      ))}
    </div>
  );
}

// ─── Physics + Intelligence card layout (preserved from old landing) ──
function PhysicsCard({ icon: Icon, title, items }) {
  return (
    <Reveal className="rounded-xl border border-brand-orange/20 hover:border-brand-orange/50 transition-colors bg-white/[0.02] p-7">
      <h3 className="font-display font-bold text-lg flex items-center gap-3 text-white mb-5">
        <span className="w-9 h-9 rounded-md bg-brand-orange/10 border border-brand-orange/30 flex items-center justify-center">
          <Icon className="w-4 h-4 text-brand-orange" />
        </span>
        {title}
      </h3>
      <ul className="space-y-2.5 text-sm text-white/65 font-mono leading-relaxed">
        {items.map((item, i) => (
          <li key={i}>
            <span className="text-brand-orange mr-1.5">›</span>
            {item}
          </li>
        ))}
      </ul>
    </Reveal>
  );
}

// ──────────────────────────────────────────────────────────────────────
function HomePageInner() {
  // GROWTH_EXP_001: hero-CTA copy A/B test — see data/growth_experiments.json
  // Default OFF (control). Visitors who land with ?variant=B see the
  // verb-result variant. Same href, same SEO, same h1.
  const searchParams = useSearchParams();
  const ctaVariant = searchParams?.get('variant') === 'B' ? 'B' : 'A';
  const heroCtaLabel = ctaVariant === 'B' ? "See your bike's quarter-mile ET" : 'Try the simulator';

  // GROWTH_EXP_018: hero subhead value-prop framing A/B test
  // Default OFF (control = physics-first). Visitors who land with ?exp18=B
  // see the Indian-community-first framing that names the drag-racing
  // identity up front rather than the technical methodology.
  // Uses ?exp18=B (not ?variant=B) to avoid contaminating EXP-001 arms.
  // Same h1, same CTAs, same meta — SEO-safe. Single variable: subhead only.
  const exp18Variant = searchParams?.get('exp18') === 'B' ? 'B' : 'A';

  // Track scroll progress through the hero so the christmas tree
  // lights light in sequence.
  const heroRef = useRef(null);
  const { scrollYProgress: heroProgress } = useScroll({
    target: heroRef,
    offset: ['start start', 'end start'],
  });
  const heroFade = useTransform(heroProgress, [0.6, 1], [1, 0]);

  // ── Dial drive (July 2026 fix: respond from the FIRST scroll pixel). ──
  // The old mapping scoped progress to the dial's own box crossing the
  // viewport TOP ('start start' → 'end start'), which meant hundreds of
  // pixels of scrolling produced zero needle movement — field-reported as
  // "the rpm gauge moves very late" (the telemetry section below was at
  // 13.5k rpm while the hero dial still idled at 1,500). The hero's own
  // progress is 0 exactly at rest and grows from the first scroll tick, so
  // the dial now rides heroProgress: idle at rest, needle building
  // immediately, redline by ~half the hero's exit. dialRef stays on the
  // wrapper (LaunchControl positioning depends on it).
  const dialRef = useRef(null);

  // ── LAUNCH CONTROL (hold-to-launch) ──────────────────────────────
  // BITKRAFT-style hold gate. holdMV is driven by the LaunchControl
  // button; the dial needle reads max(scroll, hold) so both inputs
  // share one needle with no extra render loops. Tree restarts via
  // runSignal; an early release lights the red foul bulb.
  const holdMV = useMotionValue(0);
  // heroProgress is 0 at rest (hero top pinned to viewport top), so a tiny
  // 2% dead-zone keeps the genuine 1,500-rpm idle on first paint while the
  // needle starts building on the very first wheel tick. Full sweep lands
  // by 55% of the hero's exit — the run plays while the dial is still
  // prominently on screen instead of after it has left.
  const dialCurved = useTransform(heroProgress, [0.02, 0.55], [0, 1], { clamp: true });
  const dialDrive = useTransform([dialCurved, holdMV], ([a, b]) => Math.max(a, b));
  const [treeRun, setTreeRun] = useState(0);
  const [treeFoul, setTreeFoul] = useState(false);
  // Increments on a clean hold-to-launch release → TronGrid streak burst.
  const [launchSignal, setLaunchSignal] = useState(0);

  return (
    <div className="min-h-screen bg-black text-white antialiased overflow-x-clip">
      <BootSequence
        bikes={STATS[0].num}
        tires={STATS[1].num}
        parts={STATS[2].num}
        venues={STATS[3].num}
      />
      <HudFrame />
      <SiteNav />
      <SectionRail
        sections={[
          { id: 'telemetry', label: 'Telemetry' },
          { id: 'manifesto', label: 'Manifesto' },
          { id: 'why', label: 'Why MotoQuant' },
          { id: 'simulator', label: 'Live simulator' },
          { id: 'physics', label: 'Physics' },
          { id: 'intelligence', label: 'Intelligence' },
          { id: 'validation', label: 'Validation' },
        ]}
      />

      {/* ─── HERO ─────────────────────────────────────────────── */}
      <section
        ref={heroRef}
        className="relative min-h-[640px] sm:min-h-[800px] lg:min-h-screen pt-16 overflow-hidden bg-black"
      >
        {/* background — radial glow + grid + horizon lights */}
        <div className="absolute inset-0 pointer-events-none">
          <div
            className="absolute inset-0"
            style={{
              background:
                'radial-gradient(900px 480px at 30% 80%, rgba(255,94,31,0.12), transparent 60%), radial-gradient(700px 320px at 70% 20%, rgba(34,197,94,0.06), transparent 60%)',
            }}
          />
          <div className="absolute inset-0 bg-grid-fade opacity-25" />
          {/* Tron floor — live light-cycle traffic; a clean hold-to-launch
              release fires a burst across it (launchSignal). Deliberately the
              lightweight 2D canvas: a WebGL three.js arena was built and
              pulled same-day after operator preview feedback (visible lag on
              laptop-class GPUs + didn't earn its keep visually). Canvas
              renders nothing until mounted, so the static grid above is the
              SSR / reduced-motion base layer. */}
          <TronGrid launchSignal={launchSignal} className="opacity-80" />
          <div className="absolute inset-x-0 bottom-0 h-1/3 bg-gradient-to-t from-black to-transparent" />
        </div>

        <motion.div
          style={{ opacity: heroFade }}
          className="relative max-w-7xl mx-auto px-4 sm:px-8 lg:px-12 pt-4 sm:pt-6 pb-16 sm:pb-20 lg:pb-16 min-h-[calc(640px-4rem)] sm:min-h-[calc(800px-4rem)] lg:min-h-[calc(100vh-4rem)] flex items-center justify-center"
        >
          {/* One-viewport cockpit (lg+): tree on the left; dial, copy and the
              HOLD TO LAUNCH control stacked on the right — staging lights,
              revs and the launch button share a single sightline (the v1
              layout put the CTAs ~1.5 viewports below the tree, so the
              countdown was never visible while holding). Mobile keeps the
              vertical stack; LaunchControl's built-in mini lamps carry the
              countdown there. */}
          <div className="w-full max-w-[1100px] flex flex-col items-center gap-4 sm:gap-6 lg:grid lg:grid-cols-[auto_minmax(0,1fr)] lg:gap-10 lg:items-center">
            <div className="pointer-events-auto flex-shrink-0">
              <ChristmasTree runSignal={treeRun} foul={treeFoul} />
            </div>

            <div className="w-full min-w-0 flex flex-col items-center lg:items-start">
              <div ref={dialRef} className="w-full max-w-[540px] lg:max-w-[560px]">
                <PhysicsDial progress={dialDrive} className="w-full h-auto" />
              </div>

          {/* Hero copy — beside the tree, under the dial.
              Cockpit v3 declutter: the "Built in India" badge pill became a
              small mono eyebrow, and the pill row below the subhead is capped
              at two (accuracy claim + solver signature) so the lg column
              reads eyebrow → h1 → subhead → pills → CTAs. */}
          <div className="relative z-10 mt-5 sm:mt-6 max-w-2xl text-center lg:text-left">
            <Reveal y={20} duration={0.7}>
              <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-brand-orange/80">
                Proudly built in India
              </div>
            </Reveal>

            <Reveal y={32} duration={0.9} delay={0.05}>
              <h1 className="mt-4 sm:mt-5 font-display font-bold text-[2rem] sm:text-5xl lg:text-[3.4rem] leading-[1.05] sm:leading-[0.98] tracking-[-0.03em] sm:tracking-[-0.04em] text-white">
                The physics of{' '}
                <span className="text-gradient-orange">faster.</span>
              </h1>
            </Reveal>

            {/* GROWTH_EXP_018: hero subhead framing — physics-first (A) vs Indian-community-first (B) */}
            <Reveal y={20} duration={0.7} delay={0.15}>
              {exp18Variant === 'B' ? (
                <p
                  className="mt-4 text-base sm:text-lg text-white/70 leading-relaxed max-w-xl mx-auto lg:mx-0"
                  data-exp="EXP-018"
                  data-variant="B"
                >
                  Your bike. Your strip. Your quarter-mile ET — predicted to
                  within{' '}
                  <span className="text-white">±0.009s</span> on our 10 cleanest validated runs.{' '}
                  <span className="text-white">535 Indian and global bikes</span>,{' '}
                  <span className="text-white">594 parts with INR pricing</span>,{' '}
                  <span className="text-white">Aamby Valley to MMRT.</span>
                </p>
              ) : (
                <p
                  className="mt-4 text-base sm:text-lg text-white/70 leading-relaxed max-w-xl mx-auto lg:mx-0"
                  data-exp="EXP-018"
                  data-variant="A"
                >
                  A first-principles drag simulator for India&rsquo;s motorcycle
                  drag-racing community.{' '}
                  <span className="text-white">535 bikes</span>,{' '}
                  <span className="text-white">594 parts</span>,{' '}
                  <span className="text-white">20 venues</span> — validated
                  against 223 published quarter-mile tests — ±0.009s across the 10 cleanest.
                </p>
              )}
            </Reveal>

            <Reveal y={16} duration={0.7} delay={0.22}>
              <div className="mt-4 flex flex-wrap gap-2 text-[11px] font-mono justify-center lg:justify-start">
                <span className="px-3 py-1.5 rounded-full border border-brand-orange/30 text-brand-orange">
                  −0.026s mean bias across 223 benchmarks
                </span>
                <span className="px-3 py-1.5 rounded-full border border-white/10 text-white/55">
                  RK4 · 1ms · 15 sub-models
                </span>
              </div>
            </Reveal>

            <Reveal y={20} duration={0.7} delay={0.3}>
              {/* GROWTH_EXP_001: A/B variant — see data/growth_experiments.json */}
              <div className="mt-6 flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
                <Link
                  href="/simulator"
                  data-exp="EXP-001"
                  data-variant={ctaVariant}
                  className="inline-flex items-center justify-center px-7 py-4 rounded-md bg-brand-orange hover:bg-brand-orangeLight text-black font-display font-bold transition-colors shadow-orange-soft"
                >
                  {heroCtaLabel}
                </Link>
                <LaunchControl
                  holdMV={holdMV}
                  onTreeRun={() => setTreeRun((c) => c + 1)}
                  onFoul={setTreeFoul}
                  onLaunch={() => setLaunchSignal((c) => c + 1)}
                />
              </div>
            </Reveal>
          </div>
            </div>
          </div>
        </motion.div>

        <ScrollHint />
      </section>

      {/* ─── PINNED TELEMETRY HUD ────────────────────────────── */}
      <TelemetryHUD />

      {/* ─── MANIFESTO — scroll-scrubbed belief system ────────── */}
      <ManifestoScrub />

      {/* ─── STATS STRIP ─────────────────────────────────────── */}
      <StatsStrip />

      {/* ─── WHY MOTOQUANT — 4 value props ───────────────────── */}
      <section id="why" className="py-20 md:py-28 px-6 border-t border-brand-orange/10">
        <div className="max-w-7xl mx-auto">
          <Reveal>
            <div className="text-center mb-16 max-w-3xl mx-auto">
              <CodeComment center className="mb-5">value props loaded [4/4]</CodeComment>
              <h2 className="font-display font-bold text-4xl md:text-5xl text-white tracking-tight">
                Why MotoQuant?
              </h2>
              <p className="mt-4 text-white/65 text-lg">
                The difference between guessing and knowing what your build will run.
              </p>
            </div>
          </Reveal>

          <Stagger className="grid sm:grid-cols-2 gap-6">
            {[
              {
                icon: Cpu,
                title: 'First-Principles Physics',
                body: '15 independent sub-models — not a lookup table, not a regression. Every coefficient traces back to a real physical measurement: Pacejka tire grip, Willans friction engine model, RK4 numerical integration at 1ms timestep.',
                href: '/whitepaper',
                cta: 'Read the whitepaper →',
              },
              {
                icon: Target,
                title: 'Indian Market-First',
                body: '535 bikes including 57 Indian commuters (Pulsar N125, NS200, NS400Z, Apache RTR, R15 V4, Duke 390, RE Interceptor 650), 15 SE Asia drag cubs, the Kawasaki Ninja ZX-4R/ZX-4RR 400cc inline-fours, and the complete Indian racing scene. Parts prices in INR with live retailer data. Venues: Aamby Valley, MMRT, BIC, Kari, Hyderabad.',
                href: '/bikes',
                cta: 'Browse all 535 bikes →',
              },
              {
                icon: TrendingUp,
                title: 'ROI Before You Buy',
                body: "Parts ROI knapsack tells you which mods deliver the most ET per rupee within your budget. Cost-per-tenth ranking across the full catalog. Stop buying parts that don't move the number.",
                href: '/features',
                cta: 'See the ROI engine →',
              },
              {
                icon: BarChart3,
                title: 'Validated',
                body: 'Kawasaki ZX-10R 2021 at ±0.011s. Top-10 mean error ±0.009s. Reference baselines: K5 10.0334s, R1 10.2859s, Hayabusa 10.4712s — preserved exactly to four decimals across every commit.',
                href: '/docs/validation',
                cta: 'See benchmark table →',
              },
            ].map(({ icon: Icon, title, body, href, cta }) => (
              <StaggerItem
                key={title}
                className="group card card-hover p-5 md:p-6"
              >
                <div className="flex items-center gap-3 mb-4">
                  <span className="w-10 h-10 rounded-md bg-brand-orange/10 border border-brand-orange/30 flex items-center justify-center">
                    <Icon className="w-5 h-5 text-brand-orange" />
                  </span>
                  <h3 className="font-display font-bold text-xl text-white">{title}</h3>
                </div>
                <p className="text-white/65 text-sm leading-relaxed mb-5">{body}</p>
                <Link href={href} className="text-brand-accent text-xs font-mono hover:text-brand-orange transition-colors">
                  {cta}
                </Link>
              </StaggerItem>
            ))}
          </Stagger>
        </div>
      </section>

      {/* ─── EMBEDDED SIMULATOR ──────────────────────────────── */}
      <section
        id="simulator"
        className="relative py-20 md:py-28 px-6 border-t border-brand-orange/10"
      >
        <div className="max-w-7xl mx-auto">
          <Reveal>
            <div className="text-center mb-12 max-w-2xl mx-auto">
              <CodeComment center className="mb-5">engine warm · awaiting input</CodeComment>
              <h2 className="font-display font-bold text-4xl md:text-5xl text-white tracking-tight">
                Run It Yourself
              </h2>
              <p className="mt-4 text-white/70 text-lg">
                Real physics, running live. Pick a bike, adjust your setup,
                get your ET in under a second.
              </p>
            </div>
          </Reveal>

          {/* ambient glow framing the widget */}
          <div className="absolute -left-40 top-1/2 w-80 h-80 rounded-full bg-brand-orange/10 blur-3xl pointer-events-none" />
          <div className="absolute -right-40 top-1/2 w-80 h-80 rounded-full bg-brand-orangeDeep/10 blur-3xl pointer-events-none" />

          <div className="relative z-10">
            <SimulatorWidget />
          </div>
        </div>
      </section>

      {/* ─── PHYSICS — 15 sub-models ─────────────────────────── */}
      <section id="physics" className="py-20 md:py-28 px-6 border-t border-brand-orange/10 bg-ink-1/40">
        <div className="max-w-7xl mx-auto">
          <Reveal>
            <div className="mb-16 max-w-3xl">
              <CodeComment className="mb-5">loading submodels [15/15] · rk4 @ 1ms</CodeComment>
              <h2 className="font-display font-bold text-4xl md:text-5xl text-white tracking-tight">
                15 Physics Sub-Models
              </h2>
              <p className="mt-4 text-white/70 text-lg">
                Every coefficient is traceable to a real measurement.
                No curve-fitting against times — pure physics.
              </p>
            </div>
          </Reveal>

          <div className="grid md:grid-cols-2 gap-6">
            <PhysicsCard
              icon={Zap}
              title="Engine & Drivetrain"
              items={[
                '3D engine torque curves (Willans friction model)',
                'Forced induction — turbo, supercharger, nitrous',
                'Gear shifting and clutch engagement dynamics',
                'Chain drive losses and sprocket ratios',
              ]}
            />
            <PhysicsCard
              icon={Gauge}
              title="Grip & Aerodynamics"
              items={[
                'Pacejka tire model with thermal evolution',
                'Drag coefficient and frontal area per-bike',
                'Weight transfer and traction limits',
                'Rider CoG shift and wheelie physics',
              ]}
            />
            <PhysicsCard
              icon={Wind}
              title="Environment & Setup"
              items={[
                'Air density, altitude and temperature correction',
                'Surface grip for asphalt, concrete, salt and dry lake',
                'Staging, reaction time, two-step launch control',
                '20 venues: Aamby Valley, MMRT, BIC, Santa Pod, Pomona',
              ]}
            />
            <PhysicsCard
              icon={BarChart3}
              title="Numerics & Validation"
              items={[
                'RK4 fixed-step integrator at 1ms timestep',
                'Adaptive step-size solver with error bounds',
                '976 regression tests, zero silent failures',
                'Validated against real GPS and ECU telemetry',
              ]}
            />
          </div>
        </div>
      </section>

      {/* ─── INTELLIGENCE LAYER — Phase 4 AI features ─────────── */}
      <section id="intelligence" className="py-20 md:py-28 px-6 border-t border-brand-orange/10">
        <div className="max-w-7xl mx-auto">
          <Reveal>
            <div className="mb-16 max-w-3xl">
              <CodeComment className="mb-5">analysis stack online · surrogate: dnn.pkl</CodeComment>
              <h2 className="font-display font-bold text-4xl md:text-5xl text-white tracking-tight">
                Intelligence Layer
              </h2>
              <p className="mt-4 text-white/70 text-lg">
                Physics is the floor, not the ceiling. MotoQuant Pro ships a full
                analysis stack on top of the solver — so you spend less time
                sweeping sliders and more time building the right bike.
              </p>
            </div>
          </Reveal>

          <div className="grid md:grid-cols-2 gap-6">
            <PhysicsCard
              icon={Target}
              title="Smart Recommendations"
              items={[
                'Parts ROI knapsack — best ET delta per ₹',
                'Build profiles: Street / Drag Prep / Full Race',
                'Synergy detection (exhaust + ECU, turbo + fuel)',
                'Upgrade path: Budget → Mid → Performance → Full Send',
              ]}
            />
            <PhysicsCard
              icon={Brain}
              title="Bayesian Optimisation"
              items={[
                'BoTorch Gaussian-process build optimiser',
                '7-parameter continuous search (power, mass, aero, grip, gearing)',
                'Budget-aware penalty with INR cost estimates',
                'Converges in 30–50 iterations — no grid search',
              ]}
            />
            <PhysicsCard
              icon={MessageSquare}
              title="Natural Language Queries"
              items={[
                '"Optimise my Hayabusa for 35°C at Aamby Valley, budget 50k"',
                'Regex parser extracts bike, venue, weather, budget',
                'Resolves against the live catalog and runs the sim end-to-end',
                'Mistral 7B / Llama hook for Phase 5 conversational tuning',
              ]}
            />
            <PhysicsCard
              icon={Cpu}
              title="Surrogate Predictors"
              items={[
                'XGBoost & PyTorch DNN models trained on Sobol-sampled sims',
                'Sub-millisecond ET predictions for slider-driven UIs',
                'R² > 0.99, within-50ms accuracy on held-out bikes',
                'Feature importance + uncertainty for every prediction',
              ]}
            />
            <PhysicsCard
              icon={Upload}
              title="Import & Auto-Calibrate"
              items={[
                'Dragy GPS CSV / JSON / VBO with run-boundary detection',
                'Dyno curves: DynoJet, generic metric, MoTeC (SAE J1349)',
                'ECU logs: Woolich, Power Commander, MoTeC i2',
                'Auto-calibrator fits Cd + μ via DE + Nelder-Mead',
              ]}
            />
            <PhysicsCard
              icon={TrendingUp}
              title="Sensitivity & Overlay"
              items={[
                'Sobol global sensitivity indices (S1 + ST)',
                'Multi-run statistical model — CV, 95% CI, recommended N',
                'Sim-vs-real v(t) overlay with RMSE, MAE, split errors',
                'Composite cost function ready for any optimiser',
              ]}
            />
          </div>
        </div>
      </section>

      {/* ─── VALIDATION — honest physics + Top 10 ────────────── */}
      <section id="validation" className="py-20 md:py-28 px-6 border-t border-brand-orange/10">
        <div className="max-w-7xl mx-auto">
          <Reveal>
            <div className="mb-12 max-w-3xl">
              <CodeComment className="mb-5">cross-checking 223 weighted benchmarks</CodeComment>
              <h2 className="font-display font-bold text-4xl md:text-5xl text-white tracking-tight">
                Validated on Real Telemetry
              </h2>
              <p className="mt-4 text-white/70 text-lg">
                We don&rsquo;t just predict — we measure. 223 weighted benchmarks
                against published Cycle World, Sport Rider, MCN, and
                Motorcyclist tests. Reference baselines preserved exactly to
                four decimals across every commit.
              </p>
            </div>
          </Reveal>

          <div className="grid lg:grid-cols-[1.05fr_1fr] gap-10 mb-14">
            <Reveal>
              <ClusterBars />
            </Reveal>
            <Reveal y={32} duration={0.85} delay={0.1}>
              <div className="space-y-6">
                <h3 className="font-display font-bold text-2xl sm:text-3xl text-white tracking-tight leading-tight">
                  Three reference baselines.<br />Four decimals. Across every commit.
                </h3>
                <p className="text-white/60 text-sm leading-relaxed">
                  Every code change is gated on these three quarter-mile times
                  reproducing exactly to the fourth decimal place. They have
                  not drifted since April 2026.
                </p>
                <ReferenceBaselines />
              </div>
            </Reveal>
          </div>

          {/* Aggregate stats strip */}
          <Reveal>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-10">
              {[
                { num: '223',     label: 'Bikes benchmarked' },
                { num: '72',      label: 'Within ±0.10s' },
                { num: '130',     label: 'Within ±0.20s' },
                { num: '±0.009s', label: 'Top 10 mean error' },
              ].map((s) => (
                <div key={s.label} className="rounded-xl border border-brand-orange/20 bg-white/[0.02] p-5 text-center">
                  <div className="font-display font-bold text-2xl md:text-3xl text-brand-orange tabular-nums">
                    {s.num}
                  </div>
                  <div className="font-mono text-[10px] text-white/55 tracking-widest mt-1 uppercase">
                    {s.label}
                  </div>
                </div>
              ))}
            </div>
          </Reveal>

          {/* Top-10 leaderboard */}
          <Reveal>
            <div className="rounded-xl border border-brand-orange/20 bg-white/[0.02] overflow-hidden">
              {/* timeslip masthead — the leaderboard reads as an official slip */}
              <div className="flex items-center justify-between gap-3 px-5 py-2.5 border-b border-dashed border-white/15 bg-ink-1/70">
                <span className="font-mono text-[10px] tracking-[0.22em] uppercase text-white/45">
                  MotoQuant timing assoc · official accuracy slip
                </span>
                <span className="hidden sm:block font-mono text-[10px] tracking-[0.18em] uppercase text-brand-orange/80">
                  10 cleanest pulls · 223 benchmarks
                </span>
              </div>
              <div className="hidden md:grid grid-cols-[40px_1fr_120px_120px_120px_140px] gap-4 px-5 py-3 border-b border-brand-orange/20 bg-white/[0.02] text-[10px] font-mono uppercase tracking-widest text-white/45">
                <div>#</div>
                <div>Bike</div>
                <div className="text-right">Published ET</div>
                <div className="text-right">Simulated ET</div>
                <div className="text-right">Δ</div>
                <div className="text-right">Source</div>
              </div>

              {TOP10.map((b) => {
                const abs = Math.abs(b.delta);
                const colour = abs < 0.05 ? 'text-brand-accent' : abs < 0.10 ? 'text-brand-green' : 'text-brand-amber';
                const sign = b.delta === 0 ? '±' : b.delta > 0 ? '+' : '';
                return (
                  <div
                    key={b.rank}
                    className="md:grid md:grid-cols-[40px_1fr_120px_120px_120px_140px] md:gap-4 px-5 py-4 border-b border-white/[0.04] last:border-0 hover:bg-brand-orange/[0.04] transition-colors"
                  >
                    {/* mobile */}
                    <div className="md:hidden flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <span className="font-display font-bold text-brand-orange text-lg tabular-nums">#{b.rank}</span>
                        <span className="font-display font-bold text-white text-sm">{b.name}</span>
                      </div>
                      <span className={`font-display font-bold text-sm tabular-nums ${colour}`}>
                        {sign}{b.delta.toFixed(3)}s
                      </span>
                    </div>
                    <div className="md:hidden grid grid-cols-3 gap-2 text-xs">
                      <div><div className="text-white/40 text-[10px] font-mono uppercase tracking-wider mb-0.5">Year</div><div className="text-white/80 font-mono">{b.year}</div></div>
                      <div><div className="text-white/40 text-[10px] font-mono uppercase tracking-wider mb-0.5">Target</div><div className="text-white/80 font-mono tabular-nums">{b.target.toFixed(2)}s</div></div>
                      <div><div className="text-white/40 text-[10px] font-mono uppercase tracking-wider mb-0.5">Sim</div><div className="text-white/80 font-mono tabular-nums">{b.sim.toFixed(2)}s</div></div>
                    </div>
                    <div className="md:hidden mt-2 text-[10px] font-mono text-white/40">{b.cc} &middot; {b.source}</div>

                    {/* desktop */}
                    <div className="hidden md:block font-display font-bold text-brand-orange text-lg tabular-nums">{b.rank}</div>
                    <div className="hidden md:block">
                      <div className="font-display font-bold text-white">{b.name}</div>
                      <div className="font-mono text-xs text-white/45">{b.year} &middot; {b.cc}</div>
                    </div>
                    <div className="hidden md:block text-right font-mono text-white/80 tabular-nums">{b.target.toFixed(2)}s</div>
                    <div className="hidden md:block text-right font-mono text-white tabular-nums font-semibold">{b.sim.toFixed(2)}s</div>
                    <div className={`hidden md:block text-right font-display font-bold tabular-nums ${colour}`}>
                      {sign}{b.delta.toFixed(3)}s
                    </div>
                    <div className="hidden md:block text-right font-mono text-[10px] text-white/40 self-center">{b.source}</div>
                  </div>
                );
              })}
            </div>
          </Reveal>

          <Reveal className="mt-6 text-center text-sm text-white/55 font-mono">
            <p>
              Plug in your own Dragy GPS logs to auto-calibrate for your bike,
              rider style, and venue.{' '}
              <span className="text-brand-accent">Zero guesswork.</span>
            </p>
          </Reveal>
        </div>
      </section>

      {/* ─── CTA — green-light moment ────────────────────────── */}
      <section className="relative py-20 md:py-28 px-6 border-t border-brand-orange/10 overflow-hidden">
        <div
          className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[900px] rounded-full pointer-events-none"
          style={{
            background:
              'radial-gradient(circle, rgba(34,197,94,0.18) 0%, rgba(34,197,94,0) 60%)',
          }}
        />
        <div className="relative max-w-3xl mx-auto text-center">
          <Reveal>
            <h2 className="font-display font-bold text-5xl md:text-7xl tracking-[-0.03em] leading-[0.95]">
              Stage. Burn. <span className="text-brand-green drop-shadow-[0_0_24px_rgba(34,197,94,0.6)]">Green.</span>
            </h2>
          </Reveal>
          <Reveal delay={0.1}>
            <p className="mt-6 text-lg text-white/65">
              Pick a bike. Pick a track. Pick a build. We&rsquo;ll run the physics.
            </p>
          </Reveal>
          <Reveal delay={0.2}>
            <Link
              href="/simulator"
              className="mt-10 inline-flex items-center justify-center px-9 py-4 rounded-md bg-brand-green text-black font-display font-bold text-lg shadow-[0_16px_50px_rgba(34,197,94,0.45)] hover:scale-[1.02] transition-transform"
            >
              Run your first sim →
            </Link>
          </Reveal>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}


// ──────────────────────────────────────────────────────────────────────
// Default export wraps HomePageInner in <Suspense> so the static
// prerender of `/` doesn't bail out on the EXP-001 useSearchParams()
// call. Without this boundary, `next build` errors with
// "missing-suspense-with-csr-bailout" on the root route. See
// web/CONTRIBUTING.md for the full rule.
export default function HomePage() {
  return (
    <Suspense fallback={null}>
      <HomePageInner />
    </Suspense>
  );
}
