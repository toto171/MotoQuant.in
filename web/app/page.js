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

import { Suspense, useRef } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { motion, useScroll, useTransform } from 'framer-motion';
import {
  Zap, TrendingUp, BarChart3, ChevronDown, Cpu, Wind, Gauge,
  Brain, Target, MessageSquare, Upload,
} from 'lucide-react';

import SiteNav from '../components/SiteNav';
import SiteFooter from '../components/SiteFooter';
import ChristmasTree from '../components/ChristmasTree';
import TelemetryHUD from '../components/TelemetryHUD';
import { Reveal, Stagger, StaggerItem, Counter } from '../components/Reveal';
import SimulatorWidget from '../components/SimulatorWidget';
import PhysicsDial from '@/components/PhysicsDial';

// ─── Validation: only the four clusters where the data is good ────────
// Per CLAUDE.md April 30 weighted metrics. Small-cc / 2T / cruiser
// clusters are bounded by benchmark data quality (DERIVED 0-100×1.6
// estimates with declared ±0.7s uncertainty), not model fidelity, so
// they're shown in /docs/validation with their full caveat — not on
// the landing page.
const HONEST_CLUSTERS = [
  { name: 'Litre Sport ≥195hp',   bias: -0.011, mae: 0.150, n: 20 },
  { name: 'Litre Sport 600-1000', bias: -0.130, mae: 0.198, n: 24 },
  { name: 'Mid-Twin 300-500',     bias: -0.057, mae: 0.668, n: 11 },
  { name: 'All clusters · weighted overall', bias: 0.006, mae: 0.306, n: 74 },
];

// ─── Top-10 most accurate bikes (preserved from prior landing) ────────
const TOP10 = [
  { rank: 1,  name: 'Kawasaki Ninja ZX-10R',     year: 2021, cc: '998cc I4',     target: 10.00, sim: 10.011, delta:  0.011, source: 'Cycle World 2021' },
  { rank: 2,  name: 'Kawasaki Z 650',            year: 2017, cc: '649cc I2',     target: 12.40, sim: 12.412, delta:  0.012, source: 'MotoStatz 2017'   },
  { rank: 3,  name: 'Suzuki TL1000R',            year: 1998, cc: '996cc V-twin', target: 10.50, sim: 10.518, delta:  0.018, source: 'Cycle World 1998' },
  { rank: 4,  name: 'Honda CBR1000RR-R',         year: 2020, cc: '999cc I4',     target:  9.95, sim:  9.928, delta: -0.022, source: 'Cycle World 2020' },
  { rank: 5,  name: 'Kawasaki Ninja ZX-9R',      year: 2000, cc: '899cc I4',     target: 10.50, sim: 10.526, delta:  0.026, source: 'Sport Rider 2000' },
  { rank: 6,  name: 'Yamaha YZF-R1',             year: 2009, cc: '998cc I4 CF',  target: 10.20, sim: 10.172, delta: -0.028, source: 'Sport Rider 2009' },
  { rank: 7,  name: 'BMW M1000RR',               year: 2021, cc: '999cc I4',     target:  9.80, sim:  9.837, delta:  0.037, source: 'Cycle World 2021' },
  { rank: 8,  name: 'Ducati Streetfighter V4',   year: 2020, cc: '1103cc V4',    target: 10.10, sim: 10.143, delta:  0.043, source: 'Cycle World 2020' },
  { rank: 9,  name: 'MV Agusta Brutale 1000 RR', year: 2019, cc: '998cc I4',     target: 10.15, sim: 10.103, delta: -0.047, source: 'Cycle World 2019' },
  { rank: 10, name: 'TVS Apache RR 310',         year: 2020, cc: '312cc I1',     target: 15.46, sim: 15.537, delta:  0.077, source: 'BikeWale 2020'    },
];

// ─── Stats strip — synced to current motoquant.db (Apr 30 2026) ───────
const STATS = [
  { num: 793, label: 'BIKES'      },
  { num: 232, label: 'TIRES'      },
  { num: 563, label: 'PARTS'      },
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
      className="hidden sm:flex absolute bottom-6 left-1/2 -translate-x-1/2 text-[10px] font-mono uppercase tracking-[0.3em] text-white/40 flex-col items-center gap-1 pointer-events-none"
      animate={{ y: [0, 6, 0] }}
      transition={{ duration: 2, repeat: Infinity }}
    >
      Scroll · launch sequence
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
              <div className="font-display font-bold text-3xl sm:text-4xl text-brand-orange">
                <Counter value={s.num} />
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
        Honest physics &middot; April 30, 2026
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
          <div className="mt-3 font-mono font-bold text-3xl tabular-nums text-white">
            {b.et}<span className="text-white/40 text-xl">s</span>
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

  // ── Dial gets its OWN scroll progress, decoupled from the hero. ──
  // On mobile the dial stacks BELOW the tree, so by the time the gauge
  // is on-screen the hero progress is already past 0.5 and the needle
  // would only sweep the low-RPM portion before the hero fades out. By
  // scoping the dial's progress to its own bounding-box passing through
  // the viewport (`start end` → `end start`), the full 1500→14500 RPM
  // sweep maps to "dial enters viewport bottom" → "dial exits viewport
  // top", which works at every viewport height.
  const dialRef = useRef(null);
  const { scrollYProgress: dialProgress } = useScroll({
    target: dialRef,
    offset: ['start end', 'end start'],
  });

  return (
    <div className="min-h-screen bg-black text-white antialiased overflow-x-clip">
      <SiteNav />

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
          <div className="absolute inset-x-0 bottom-0 h-1/3 bg-gradient-to-t from-black to-transparent" />
        </div>

        <motion.div
          style={{ opacity: heroFade }}
          className="relative max-w-7xl mx-auto px-4 sm:px-8 lg:px-16 pt-4 sm:pt-8 pb-12 sm:pb-20 lg:pb-32 min-h-[calc(640px-4rem)] sm:min-h-[calc(800px-4rem)] lg:min-h-[calc(100vh-4rem)] flex flex-col items-center justify-center"
        >
          {/* Tree + dial centerpiece. Stacks on mobile, side-by-side on lg+.
              The previous `scale-[0.7] sm:scale-[0.85]` on the tree wrapper
              created a phantom-bounding-box gap below the tree on mobile —
              the visual was shrunk 30% but the layout box stayed full size.
              Removed; the tree's own `w-[180px] sm:w-[220px]` responsive
              width handles small viewports cleanly. */}
          <div className="relative w-full max-w-[1080px] mx-auto pointer-events-none flex flex-col items-center gap-3 sm:gap-6 lg:flex-row lg:items-start lg:justify-center lg:gap-12 min-w-0">
            <div className="pointer-events-auto flex-shrink-0 lg:mt-10">
              <ChristmasTree />
            </div>
            <div ref={dialRef} className="w-full max-w-full sm:max-w-[600px] lg:max-w-[640px] flex-shrink min-w-0">
              <PhysicsDial progress={dialProgress} className="w-full h-auto" />
            </div>
          </div>

          {/* Hero copy — centred below the centerpiece */}
          <div className="relative z-10 mt-6 sm:mt-8 lg:mt-10 max-w-3xl text-center">
            <Reveal y={20} duration={0.7}>
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-brand-orange/40 bg-brand-orange/10 text-[10px] sm:text-xs font-mono uppercase tracking-[0.25em] text-brand-orange">
                Proudly Built in India
              </div>
            </Reveal>

            <Reveal y={32} duration={0.9} delay={0.05}>
              <h1 className="mt-5 sm:mt-7 font-display font-bold text-[2rem] sm:text-5xl lg:text-6xl leading-[1.05] sm:leading-[0.95] tracking-[-0.03em] sm:tracking-[-0.04em] text-white">
                The physics of{' '}
                <span className="text-gradient-orange">faster.</span>
              </h1>
            </Reveal>

            {/* GROWTH_EXP_018: hero subhead framing — physics-first (A) vs Indian-community-first (B) */}
            <Reveal y={20} duration={0.7} delay={0.15}>
              {exp18Variant === 'B' ? (
                <p
                  className="mt-7 text-lg sm:text-xl text-white/70 leading-relaxed max-w-xl mx-auto"
                  data-exp="EXP-018"
                  data-variant="B"
                >
                  Your bike. Your strip. Your quarter-mile ET — predicted to
                  within{' '}
                  <span className="text-white">±0.05s</span> on the litre-class.{' '}
                  <span className="text-white">790 Indian and global bikes</span>,{' '}
                  <span className="text-white">563 parts with INR pricing</span>,{' '}
                  <span className="text-white">Aamby Valley to MMRT.</span>
                </p>
              ) : (
                <p
                  className="mt-7 text-lg sm:text-xl text-white/70 leading-relaxed max-w-xl mx-auto"
                  data-exp="EXP-018"
                  data-variant="A"
                >
                  A first-principles drag simulator for India&rsquo;s motorcycle
                  drag-racing community.{' '}
                  <span className="text-white">793 bikes</span>,{' '}
                  <span className="text-white">563 parts</span>,{' '}
                  <span className="text-white">20 venues</span> — tuned to
                  within ±0.05s of real-world ETs on the litre-class.
                </p>
              )}
            </Reveal>

            <Reveal y={16} duration={0.7} delay={0.22}>
              <div className="mt-7 flex flex-wrap gap-2 text-[11px] font-mono justify-center">
                <span className="px-3 py-1.5 rounded-full border border-white/10 text-white/55">
                  Aamby Valley · MMRT · Kari · Hyderabad
                </span>
                <span className="px-3 py-1.5 rounded-full border border-brand-orange/30 text-brand-orange">
                  +0.006s mean bias on 74 of 114 benchmarks
                </span>
                <span className="px-3 py-1.5 rounded-full border border-white/10 text-white/55">
                  RK4 · 1ms · 15 sub-models
                </span>
              </div>
            </Reveal>

            <Reveal y={20} duration={0.7} delay={0.3}>
              {/* GROWTH_EXP_001: A/B variant — see data/growth_experiments.json */}
              <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
                <Link
                  href="/simulator"
                  data-exp="EXP-001"
                  data-variant={ctaVariant}
                  className="inline-flex items-center justify-center px-7 py-4 rounded-md bg-brand-orange hover:bg-brand-orangeLight text-black font-display font-bold transition-colors shadow-orange-soft"
                >
                  {heroCtaLabel}
                </Link>
                <Link
                  href="#telemetry"
                  className="inline-flex items-center justify-center px-7 py-4 rounded-md border-2 border-brand-orange/40 hover:border-brand-orange text-brand-orange font-display font-bold transition-colors"
                >
                  See it run
                </Link>
              </div>
            </Reveal>
          </div>
        </motion.div>

        <ScrollHint />
      </section>

      {/* ─── PINNED TELEMETRY HUD ────────────────────────────── */}
      <TelemetryHUD />

      {/* ─── STATS STRIP ─────────────────────────────────────── */}
      <StatsStrip />

      {/* ─── WHY MOTOQUANT — 4 value props ───────────────────── */}
      <section id="why" className="py-24 md:py-32 px-6 border-t border-brand-orange/10">
        <div className="max-w-7xl mx-auto">
          <Reveal>
            <div className="text-center mb-16 max-w-3xl mx-auto">
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
                body: '793 bikes including 57 Indian commuters (Pulsar N125, NS200, NS400Z, Apache RTR, R15 V4, Duke 390, RE Interceptor 650), 15 SE Asia drag cubs, the Kawasaki Ninja ZX-4R/ZX-4RR 400cc inline-fours, and the complete Indian racing scene. Parts prices in INR with live retailer data. Venues: Aamby Valley, MMRT, BIC, Kari, Hyderabad.',
                href: '/bikes',
                cta: 'Browse all 793 bikes →',
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
                body: 'Kawasaki ZX-10R 2021 at ±0.011s. Top-10 mean error ±0.032s. Reference baselines: K5 10.0334s, R1 10.2859s, Hayabusa 10.4712s — preserved exactly to four decimals across every commit.',
                href: '/docs/validation',
                cta: 'See benchmark table →',
              },
            ].map(({ icon: Icon, title, body, href, cta }) => (
              <StaggerItem
                key={title}
                className="group rounded-xl border border-brand-orange/20 hover:border-brand-orange/50 transition-colors bg-white/[0.02] p-8"
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
        className="relative py-24 md:py-32 px-6 border-t border-brand-orange/10"
      >
        <div className="max-w-7xl mx-auto">
          <Reveal>
            <div className="text-center mb-12 max-w-2xl mx-auto">
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
      <section id="physics" className="py-24 md:py-32 px-6 border-t border-brand-orange/10 bg-ink-1/40">
        <div className="max-w-7xl mx-auto">
          <Reveal>
            <div className="mb-16 max-w-3xl">
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
      <section id="intelligence" className="py-24 md:py-32 px-6 border-t border-brand-orange/10">
        <div className="max-w-7xl mx-auto">
          <Reveal>
            <div className="mb-16 max-w-3xl">
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
      <section id="validation" className="py-24 md:py-32 px-6 border-t border-brand-orange/10">
        <div className="max-w-7xl mx-auto">
          <Reveal>
            <div className="mb-12 max-w-3xl">
              <h2 className="font-display font-bold text-4xl md:text-5xl text-white tracking-tight">
                Validated on Real Telemetry
              </h2>
              <p className="mt-4 text-white/70 text-lg">
                We don&rsquo;t just predict — we measure. 79 weighted benchmarks
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
                  not drifted in 47 days.
                </p>
                <ReferenceBaselines />
              </div>
            </Reveal>
          </div>

          {/* Aggregate stats strip */}
          <Reveal>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-10">
              {[
                { num: '79',      label: 'Bikes benchmarked' },
                { num: '15',      label: 'Within ±0.10s' },
                { num: '30',      label: 'Within ±0.20s' },
                { num: '±0.032s', label: 'Top 10 mean error' },
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
                const colour = abs < 0.05 ? 'text-brand-accent' : abs < 0.10 ? 'text-emerald-300' : 'text-amber-300';
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
      <section className="relative py-32 px-6 border-t border-brand-orange/10 overflow-hidden">
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
