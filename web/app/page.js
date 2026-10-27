'use client';

/**
 * MotoQuant — Landing Page (IGNITION v5 · "the digital timeslip, in cockpit orange")
 * ===================================================================
 * Full rewrite per web/DESIGN.md §7. Half the length of the Cockpit v3
 * landing: no boot sequence, no HUD chrome, no scroll-scrubbed manifesto,
 * no canvas backdrops, no hold-to-launch gate. Typography, whitespace and
 * three signal colors do the work.
 *
 * Structure:
 *   ① Hero — StageDots eyebrow · H1 · EXP-018 sub · CTAs · live widget (lg+)
 *   ② Stat strip (6 audit-shaped stats)
 *   ③ How it works (3 steps → mini timeslip)
 *   ④ Tool cards + row links
 *   ⑤ Proof — accuracy tiles · cluster bias · TOP10 slip · baselines
 *   ⑥ Built for the Indian strip
 *   ⑦ FAQ (faqSchema copy, native <details>)
 *   ⑧ CTA band
 *
 * PRESERVED VERBATIM (stat audit + experiments): STATS, TOP10,
 * HONEST_CLUSTERS, reference baselines, EXP-001 (?variant=B) and EXP-018
 * (?exp18=B) hooks with data-exp attrs, <Suspense> around the
 * useSearchParams consumer.
 */

import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import {
  Gauge, Wrench, Cpu, MessageSquare, MapPin, IndianRupee, Upload, Share2,
} from 'lucide-react';

import SiteNav from '../components/SiteNav';
import SiteFooter from '../components/SiteFooter';
import StageDots from '../components/StageDots';
import { Reveal, Stagger, StaggerItem } from '../components/Reveal';
import SimulatorWidget from '../components/SimulatorWidget';
import ScoreboardDigits, { ScoreboardCounter } from '../components/ScoreboardDigits';
import { LICENSE_SPDX, REPO_URL } from '../lib/site';

// ─── Validation: only the four clusters where the data is good ────────
// Per the 8 August 2026 weighted sweep (reports/acc_final_2026_08_08.json,
// cylinder-aware 12-cluster taxonomy — post physics-accuracy pass).
// Small-cc / 2T / cruiser clusters are bounded by benchmark data quality
// (DERIVED 0-100×1.6 estimates with declared ±0.7s uncertainty), not model
// fidelity, so they're shown in /docs/validation with their full caveat —
// not on the landing page.
const HONEST_CLUSTERS = [
  { name: 'Litre Sport ≥195hp',   bias: 0.0271,  mae: 0.1466, n: 30 },
  { name: 'Litre Sport 600-1000', bias: -0.0090, mae: 0.1755, n: 72 },
  { name: 'Sport Twin 600-1300',  bias: 0.0063,  mae: 0.2459, n: 48 },
  { name: 'All clusters · weighted overall', bias: 0.0073, mae: 0.2629, n: 276 },
];

// ─── Top-10 most accurate bikes ───────────────────────────────────────
// MUST equal the docs/validation TOP10 (8 August 2026 sweep,
// reports/acc_final_2026_08_08.json — 10 smallest |Δ| across the matched
// corpus, mean ±0.007s; every row is instrumented or magazine data — no
// DERIVED estimate reaches the top 10 in this sweep). Sync both together.
const TOP10 = [
  { rank: 1,  name: 'Kawasaki ZRX1200R',             year: 2001, cc: '1164cc I4', target: 10.85, sim: 10.8487, delta: -0.001, source: 'Cycle World 2001' },
  { rank: 2,  name: 'Honda CBR650R E-Clutch',        year: 2024, cc: '649cc I4',  target: 11.45, sim: 11.4521, delta:  0.002, source: 'MotoStatz (instrumented)' },
  { rank: 3,  name: 'BMW S 1000 RR',                 year: 2015, cc: '999cc I4',  target: 9.90,  sim: 9.9038,  delta:  0.004, source: 'Cycle World 2015' },
  { rank: 4,  name: 'Triumph Rocket 3 Storm R',      year: 2024, cc: '2458cc I3', target: 10.56, sim: 10.5541, delta: -0.006, source: 'Cycle World (tuned pass)' },
  { rank: 5,  name: 'Honda CBR250RR (Indonesia)',    year: 2017, cc: '250cc I2',  target: 14.60, sim: 14.6060, delta:  0.006, source: 'VBox 2017 (instrumented)' },
  { rank: 6,  name: 'MV Agusta Brutale 1000 RR Assen', year: 2024, cc: '998cc I4', target: 10.15, sim: 10.1430, delta: -0.007, source: 'Cycle World' },
  { rank: 7,  name: 'Yamaha MT-10 SP',               year: 2022, cc: '998cc I4',  target: 10.35, sim: 10.3405, delta: -0.010, source: 'Cycle World' },
  { rank: 8,  name: 'Ducati 1098',                   year: 2007, cc: '1099cc V2', target: 10.40, sim: 10.4100, delta:  0.010, source: 'Cycle World 2007' },
  { rank: 9,  name: 'Kawasaki Z H2 SE',              year: 2024, cc: '998cc I4',  target: 9.95,  sim: 9.9631,  delta:  0.013, source: 'Cycle World' },
  { rank: 10, name: 'Kawasaki Ninja ZX-10R',         year: 2011, cc: '998cc I4',  target: 10.08, sim: 10.0933, delta:  0.013, source: 'Sport Rider 7/11' },
];

// ─── Stats strip — synced to current motoquant.db (Jul 6 2026) ────────
const STATS = [
  { num: 541, label: 'BIKES'      },
  { num: 254, label: 'TIRES'      },
  { num: 593, label: 'PARTS'      },
  { num: 20,  label: 'VENUES'     },
  { num: 4393, label: 'TESTS'      },
  { num: 15,  label: 'SUB-MODELS' },
];

// ─── Reference baselines — pinned to four decimals across every commit ─
const BASELINES = [
  { name: 'GSX-R 1000 K5',  et: '9.9331',  hp: '178 hp', year: '2005' },
  { name: 'YZF-R1 4C8',     et: '10.1436', hp: '180 hp', year: '2007' },
  { name: 'Hayabusa Gen1',  et: '10.3633', hp: '197 hp', year: '1999' },
];

// ─── Aggregate accuracy tiles (8 August 2026 sweep) ───────────────────
const ACCURACY_TILES = [
  { num: '250',     label: 'Published benchmarks' },
  { num: '75',      label: 'Within ±0.10s' },
  { num: '138',     label: 'Within ±0.20s' },
  { num: '±0.007s', label: 'Top 10 mean error' },
];

// ─── Tool cards ───────────────────────────────────────────────────────
const TOOLS = [
  {
    icon: Gauge,
    title: 'Simulator',
    body: 'Quarter-mile ET, trap speed and splits for any bike in the 541-bike catalog — on your strip, in your weather.',
    href: '/simulator',
    cta: 'Run a sim',
  },
  {
    icon: Wrench,
    title: 'Build Optimizer',
    body: 'Set a ₹ budget. The knapsack optimizer picks the parts that cut the most ET per rupee — no stacking two exhausts.',
    href: '/optimize',
    cta: 'Optimize a build',
  },
  {
    icon: Cpu,
    title: 'ECU Autotune',
    body: 'Gearing, launch RPM and fuel-trim guidance tuned to the day’s air density at your venue.',
    href: '/autotune',
    cta: 'Tune your setup',
  },
  {
    icon: MessageSquare,
    title: 'AI Chat',
    body: 'Ask in plain English. The agent runs real sims, optimizers and comparisons against the live catalog.',
    href: '/simulator',
    cta: 'Ask MotoQuant',
  },
];

// ─── Built for the Indian strip ───────────────────────────────────────
const INDIA_CARDS = [
  {
    icon: MapPin,
    title: 'Indian venues',
    body: 'Aamby Valley, MMRT, BIC, Kari — density altitude and seasonal weather built into every run.',
  },
  {
    icon: IndianRupee,
    title: 'INR parts pricing',
    body: '593 parts priced in ₹ with GST and import duty already factored in. Cost-per-tenth on every part.',
  },
  {
    icon: Upload,
    title: 'Dragy import',
    body: 'Upload Dragy GPS or dyno CSVs and overlay your real runs against the sim — ET, trap and splits for your bike and venue.',
  },
  {
    icon: Share2,
    title: 'Share your slip',
    body: 'Every saved run gets a public timeslip page built for WhatsApp — send your number, not a screenshot.',
  },
];

// ─── FAQ — copy mirrors app/StructuredData.js faqSchema() ─────────────
const FAQ_ITEMS = [
  {
    q: 'What is MotoQuant?',
    a: 'MotoQuant is a free, open-source, physics-based motorcycle quarter-mile drag racing simulator. It predicts ET, trap speed, and split times for 541 production bikes using 15 independent physics sub-models and validated aero, tire, and dyno data.',
  },
  {
    q: 'How accurate is the quarter-mile prediction?',
    a: 'MotoQuant is validated against published magazine tests and Dragy runs: Suzuki GSX-R1000 K5 simulates 9.93s against a real 9.97s; Yamaha YZF-R1 simulates 10.14s against 10.3s; Suzuki Hayabusa simulates 10.36s (real range 10.1–10.7s). The August 2026 sweep covers 250 source-quality-weighted benchmarks (276 matched to catalog bikes) with a weighted mean bias of +0.007s; 138 of 276 land within ±0.20s of the published timeslip.',
  },
  {
    q: 'Which bikes are supported?',
    a: 'The catalog covers 541 bikes across 25+ manufacturers: Suzuki, Yamaha, Honda, Kawasaki, BMW, Ducati, Aprilia, KTM, Triumph, Royal Enfield, Bajaj, TVS, Hero, Harley-Davidson, Indian Motorcycle, CFMoto, Benelli, Husqvarna, MV Agusta, Moto Guzzi, Buell, and more. Includes Indian 200–400cc commuters (Pulsar N125, NS200, NS400Z, Apache RTR, R15 V4), SE Asia underbones, 400cc inline-fours (Kawasaki Ninja ZX-4R, ZX-4RR), retro flagships (Yamaha XSR900 GP), and 20 two-stroke drag bikes (RD350, RX100, RGV250, H2 Mach IV).',
  },
  {
    q: 'Is MotoQuant free?',
    a: 'Yes — MotoQuant is free and open source under the Apache License 2.0. There are no paid tiers, subscriptions or feature gates: the simulator, build optimizer, ECU autotune, chat assistant and Dragy/dyno calibration are free for everyone. An optional free account saves your runs to a garage and the leaderboard, and the full source code is on GitHub, so you can audit the physics or run your own copy.',
  },
  {
    q: 'Can I use MotoQuant for Indian drag strips?',
    a: 'Yes — MotoQuant was built for the Indian drag racing community. The venue database covers Aamby Valley (Pune), Madras Motor Race Track (Chennai), Buddh International Circuit (Greater Noida), Kari Motor Speedway (Coimbatore), and Hyderabad, plus seven international venues. Parts pricing is in INR with GST and import duty already factored in.',
  },
  {
    q: 'Can I upload my own Dragy or dyno data?',
    a: 'Yes. MotoQuant imports Dragy GPS logs (CSV or VBO) and DynoJet/MoTeC dyno sheets with SAE J1349 atmospheric correction, then overlays your real run against the simulation — ET, trap speed and split-by-split residuals for your specific bike.',
  },
];

// ─── Section eyebrow: StageDots (static) + label ──────────────────────
function Eyebrow({ children, center = false }) {
  return (
    <div
      className={[
        'flex items-center gap-2.5',
        center ? 'justify-center' : '',
      ].join(' ')}
    >
      <StageDots size={5} />
      <span className="label-mono">{children}</span>
    </div>
  );
}

// ─── ② Stat strip ─────────────────────────────────────────────────────
function StatsStrip() {
  return (
    <section className="border-y border-white/[0.08] bg-asphalt-1/60">
      <div className="max-w-6xl mx-auto px-6 py-10">
        <div className="grid grid-cols-3 md:grid-cols-6 gap-y-8">
          {STATS.map((s, i) => (
            <div
              key={s.label}
              className={[
                'text-center',
                i < STATS.length - 1 ? 'md:border-r md:border-white/[0.08]' : '',
              ].join(' ')}
            >
              <div className="flex justify-center sm:hidden">
                <ScoreboardCounter value={s.num} h={22} />
              </div>
              <div className="hidden sm:flex justify-center">
                <ScoreboardCounter value={s.num} h={30} />
              </div>
              <div className="label-mono mt-2">{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── ③ How it works ──────────────────────────────────────────────────
function HowItWorks() {
  return (
    <section className="py-16 md:py-24 px-6">
      <div className="max-w-6xl mx-auto">
        <Reveal>
          <Eyebrow>How it works</Eyebrow>
          <h2 className="mt-4 font-display font-bold text-3xl md:text-4xl tracking-tight text-white">
            Three steps to your <span className="text-accent">number</span>
          </h2>
        </Reveal>

        <Stagger className="mt-10 grid md:grid-cols-3 gap-4 md:gap-6">
          <StaggerItem className="card p-5 md:p-6">
            <div className="label-mono">Step 01</div>
            <h3 className="mt-3 font-display font-semibold text-lg md:text-xl text-white">
              Pick your bike
            </h3>
            <p className="mt-3 text-sm text-white/65 leading-relaxed">
              541 bikes with real gearing cassettes, per-bike aero and dyno
              curves — from a Pulsar NS200 to a Hayabusa. Stock or with parts
              from the 593-part catalog.
            </p>
          </StaggerItem>

          <StaggerItem className="card p-5 md:p-6">
            <div className="label-mono">Step 02</div>
            <h3 className="mt-3 font-display font-semibold text-lg md:text-xl text-white">
              Set your strip
            </h3>
            <p className="mt-3 text-sm text-white/65 leading-relaxed">
              20 venues with density altitude and seasonal weather, rider
              weight, power and mass changes. The physics corrects for the air
              you actually race in.
            </p>
          </StaggerItem>

          <StaggerItem className="card p-5 md:p-6">
            <div className="label-mono">Step 03</div>
            <h3 className="mt-3 font-display font-semibold text-lg md:text-xl text-white">
              Get your slip
            </h3>
            <div className="timeslip mt-4 text-[13px]" aria-hidden="true">
              <div className="label-mono pb-1">MotoQuant · Official slip</div>
              <div className="timeslip-row">
                <span className="text-white/45">BIKE</span>
                <span className="text-white/85">GSX-R 1000 K5</span>
              </div>
              <div className="timeslip-row">
                <span className="text-white/45">¼-MILE ET</span>
                <span className="inline-flex items-baseline gap-1">
                  <ScoreboardDigits value="9.9331" h={22} label="9.9331 s" />
                  <span className="font-mono text-xs text-white/40">s</span>
                </span>
              </div>
              <div className="timeslip-row">
                <span className="text-white/45">BASELINE</span>
                <span className="delta-down">Δ ±0.0000s</span>
              </div>
            </div>
          </StaggerItem>
        </Stagger>
      </div>
    </section>
  );
}

// ─── ④ Tool cards ─────────────────────────────────────────────────────
function ToolCards() {
  return (
    <section className="py-16 md:py-24 px-6 border-t border-white/[0.08]">
      <div className="max-w-6xl mx-auto">
        <Reveal>
          <Eyebrow>The toolbox</Eyebrow>
          <h2 className="mt-4 font-display font-bold text-3xl md:text-4xl tracking-tight text-white">
            Every tool points at <span className="text-accent">one number</span>
          </h2>
        </Reveal>

        <Stagger className="mt-10 grid sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
          {TOOLS.map(({ icon: Icon, title, body, href, cta }) => (
            <StaggerItem key={title}>
              <Link href={href} className="card card-hover flex h-full flex-col p-5 md:p-6">
                <span className="flex h-10 w-10 items-center justify-center rounded-lg border border-white/[0.12] bg-asphalt-3">
                  <Icon className="text-white/70" size={18} aria-hidden="true" />
                </span>
                <h3 className="mt-4 font-display font-semibold text-lg md:text-xl text-white">
                  {title}
                </h3>
                <p className="mt-2 flex-1 text-sm text-white/65 leading-relaxed">{body}</p>
                <span className="label-mono mt-4 text-white/60">{cta} →</span>
              </Link>
            </StaggerItem>
          ))}
        </Stagger>

        <Stagger className="mt-4 md:mt-6 grid sm:grid-cols-2 gap-4 md:gap-6">
          <StaggerItem>
            <Link
              href="/bikes"
              className="card card-hover flex items-center justify-between gap-4 px-5 py-4"
            >
              <div className="min-w-0">
                <div className="font-display font-semibold text-lg md:text-xl text-white">
                  Bikes database
                </div>
                <div className="text-sm text-white/55 truncate">
                  541 bikes · specs, gearing, aero and OEM tire fitments
                </div>
              </div>
              <span className="label-mono shrink-0 text-white/60">Browse →</span>
            </Link>
          </StaggerItem>
          <StaggerItem>
            <Link
              href="/leaderboard"
              className="card card-hover flex items-center justify-between gap-4 px-5 py-4"
            >
              <div className="min-w-0">
                <div className="font-display font-semibold text-lg md:text-xl text-white">
                  Leaderboard
                </div>
                <div className="text-sm text-white/55 truncate">
                  Fastest community runs, venue-filtered, each with a public slip
                </div>
              </div>
              <span className="label-mono shrink-0 text-white/60">View →</span>
            </Link>
          </StaggerItem>
        </Stagger>
      </div>
    </section>
  );
}

// ─── ⑤ Proof — accuracy tiles + cluster bias + TOP10 + baselines ──────
function DeltaCell({ delta }) {
  const sign = delta === 0 ? '±' : delta > 0 ? '+' : '';
  return (
    <span className={delta < 0 ? 'delta-down' : 'delta-up'}>
      {sign}{delta.toFixed(3)}s
    </span>
  );
}

// Accuracy-tile numerals — seven-segment digits for the hero figure, with
// any non-digit prefix/suffix ('±', 's') rendered as quiet mono beside the
// board (the LED board only has segments for 0-9, '.', '-').
function TileDigits({ value }) {
  const m = String(value).match(/^([^0-9]*)([0-9][0-9.]*)(.*)$/);
  if (!m) {
    return (
      <span className="font-mono font-bold tabular-nums text-2xl text-white">
        {value}
      </span>
    );
  }
  const [, prefix, digits, suffix] = m;
  return (
    <span className="inline-flex items-baseline gap-1">
      {prefix ? <span className="font-mono text-sm text-white/45">{prefix}</span> : null}
      <ScoreboardDigits value={digits} h={26} label={String(value)} />
      {suffix ? <span className="font-mono text-sm text-white/45">{suffix}</span> : null}
    </span>
  );
}

function ProofSection() {
  return (
    <section className="py-16 md:py-24 px-6 border-t border-white/[0.08] bg-asphalt-1/40">
      <div className="max-w-6xl mx-auto">
        <Reveal>
          <Eyebrow>Validation</Eyebrow>
          <h2 className="mt-4 font-display font-bold text-3xl md:text-4xl tracking-tight text-white">
            We publish the <span className="text-accent">error bars</span>
          </h2>
          <p className="mt-4 max-w-2xl text-white/65">
            250 weighted benchmarks (276 matched) against published Cycle
            World, Sport Rider, MCN and Motorcyclist tests. Where the data is
            good, we are within 0.20s — and where it isn&rsquo;t, we say so.
          </p>
        </Reveal>

        {/* Accuracy tiles */}
        <Stagger className="mt-10 grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
          {ACCURACY_TILES.map((s) => (
            <StaggerItem key={s.label} className="card p-5 text-center">
              <div className="flex justify-center">
                <TileDigits value={s.num} />
              </div>
              <div className="label-mono mt-2">{s.label}</div>
            </StaggerItem>
          ))}
        </Stagger>

        {/* Cluster bias — the honest-physics strip */}
        <Reveal className="mt-6">
          <div className="card p-5 md:p-6">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <h3 className="font-display font-semibold text-lg md:text-xl text-white">
                Cluster bias · weighted sweep
              </h3>
              <span className="label-mono">Source-quality weighted</span>
            </div>
            <div className="mt-4">
              {HONEST_CLUSTERS.map((c) => (
                <div
                  key={c.name}
                  className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 border-b border-dashed border-white/10 py-2.5 last:border-b-0"
                >
                  <span className="text-sm text-white/85">{c.name}</span>
                  <span className="font-mono text-xs tabular-nums text-white/45">
                    N={c.n} · |Δ| {c.mae.toFixed(3)}s ·{' '}
                    <DeltaCell delta={c.bias} />
                  </span>
                </div>
              ))}
            </div>
            <p className="mt-4 text-xs text-white/40 leading-relaxed">
              Only clusters with strong instrumented coverage are shown — the
              small-cc, two-stroke and cruiser residuals are bounded by
              benchmark data quality, not model fidelity.{' '}
              <Link href="/docs/validation" className="text-white/65 underline decoration-white/25 underline-offset-2 hover:text-white transition-colors">
                Full breakdown
              </Link>
            </p>
          </div>
        </Reveal>

        {/* TOP10 accuracy slip */}
        <Reveal className="mt-6">
          <div className="card overflow-hidden">
            <div className="flex items-center justify-between gap-3 border-b border-dashed border-white/15 bg-asphalt-1/70 px-5 py-2.5">
              <span className="label-mono">
                MotoQuant timing assoc · official accuracy slip
              </span>
              <span className="label-mono hidden sm:block">
                10 cleanest pulls · 250 benchmarks
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] text-sm">
                <thead>
                  <tr className="border-b border-white/[0.08] text-left">
                    <th className="label-mono px-5 py-3 font-medium">#</th>
                    <th className="label-mono px-3 py-3 font-medium">Bike</th>
                    <th className="label-mono px-3 py-3 text-right font-medium">Published</th>
                    <th className="label-mono px-3 py-3 text-right font-medium">Simulated</th>
                    <th className="label-mono px-3 py-3 text-right font-medium">Δ</th>
                    <th className="label-mono px-5 py-3 text-right font-medium">Source</th>
                  </tr>
                </thead>
                <tbody>
                  {TOP10.map((b) => {
                    const derived = b.source.includes('DERIVED');
                    return (
                      <tr
                        key={b.rank}
                        className="border-b border-white/[0.04] last:border-b-0 hover:bg-white/[0.02] transition-colors"
                      >
                        <td className="px-5 py-3 font-mono tabular-nums text-white/45">
                          {b.rank}
                        </td>
                        <td className="px-3 py-3">
                          <div className="font-display font-semibold text-white">
                            {b.name}
                          </div>
                          <div className="font-mono text-xs text-white/40 tabular-nums">
                            {b.year} · {b.cc}
                          </div>
                        </td>
                        <td className="px-3 py-3 text-right font-mono tabular-nums text-white/70">
                          {b.target.toFixed(2)}s
                        </td>
                        <td className="px-3 py-3 text-right font-mono font-semibold tabular-nums text-white">
                          {b.sim.toFixed(2)}s
                        </td>
                        <td className="px-3 py-3 text-right">
                          <DeltaCell delta={b.delta} />
                        </td>
                        <td className="px-5 py-3 text-right font-mono text-xs text-white/40">
                          {derived ? (
                            <span className="chip chip-stage">DERIVED</span>
                          ) : (
                            b.source
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </Reveal>

        {/* Reference baselines */}
        <Stagger className="mt-6 grid sm:grid-cols-3 gap-4 md:gap-6">
          {BASELINES.map((b) => (
            <StaggerItem key={b.name} className="card p-5 md:p-6">
              <div className="label-mono">{b.name}</div>
              <div className="mt-3 flex items-baseline gap-1.5">
                <span className="font-mono font-bold tabular-nums text-3xl text-white">
                  {b.et}
                </span>
                <span className="font-mono text-sm text-white/40">s</span>
              </div>
              <div className="mt-2 font-mono text-xs tabular-nums text-signal-go">
                Δ ±0.0000s · {b.hp}
              </div>
              <div className="mt-3 flex justify-between border-t border-white/[0.06] pt-3 font-mono text-[10px] text-white/40">
                <span>{b.year}</span>
                <span>Pinned · every commit</span>
              </div>
            </StaggerItem>
          ))}
        </Stagger>

        <Reveal className="mt-8">
          <Link href="/validation" className="btn-ghost">
            Explore the validation data
          </Link>
        </Reveal>
      </div>
    </section>
  );
}

// ─── ⑥ Built for the Indian strip ─────────────────────────────────────
function IndianStrip() {
  return (
    <section className="py-16 md:py-24 px-6 border-t border-white/[0.08]">
      <div className="max-w-6xl mx-auto">
        <Reveal>
          <Eyebrow>Home turf</Eyebrow>
          <h2 className="mt-4 font-display font-bold text-3xl md:text-4xl tracking-tight text-white">
            Built for the <span className="text-accent">Indian strip</span>
          </h2>
        </Reveal>

        <Stagger className="mt-10 grid sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
          {INDIA_CARDS.map(({ icon: Icon, title, body }) => (
            <StaggerItem key={title} className="card p-5">
              <span className="flex h-10 w-10 items-center justify-center rounded-lg border border-white/[0.12] bg-asphalt-3">
                <Icon size={18} className="text-white/70" aria-hidden="true" />
              </span>
              <h3 className="mt-4 font-display font-semibold text-lg md:text-xl text-white">
                {title}
              </h3>
              <p className="mt-2 text-sm text-white/65 leading-relaxed">{body}</p>
            </StaggerItem>
          ))}
        </Stagger>
      </div>
    </section>
  );
}

// ─── ⑦ FAQ ────────────────────────────────────────────────────────────
function FaqSection() {
  return (
    <section className="py-16 md:py-24 px-6 border-t border-white/[0.08]">
      <div className="max-w-3xl mx-auto">
        <Reveal>
          <Eyebrow center>Questions</Eyebrow>
          <h2 className="mt-4 text-center font-display font-bold text-3xl md:text-4xl tracking-tight text-white">
            Straight <span className="text-accent">answers</span>
          </h2>
        </Reveal>

        <div className="mt-10 space-y-3">
          {FAQ_ITEMS.map(({ q, a }) => (
            <details key={q} className="card group px-5 py-4">
              <summary className="flex min-h-[44px] cursor-pointer list-none items-center justify-between gap-4 [&::-webkit-details-marker]:hidden">
                <span className="font-display font-semibold text-base md:text-lg text-white">
                  {q}
                </span>
                <span
                  aria-hidden="true"
                  className="shrink-0 font-mono text-white/40 transition-transform duration-200 group-open:rotate-45"
                >
                  +
                </span>
              </summary>
              <p className="mt-3 text-sm text-white/65 leading-relaxed">{a}</p>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── ⑧ CTA band ───────────────────────────────────────────────────────
function CtaBand() {
  return (
    <section className="py-16 md:py-24 px-6 border-t border-white/[0.08]">
      <div className="max-w-3xl mx-auto text-center">
        <Reveal>
          <div className="centerline mb-10" aria-hidden="true" />
          <h2 className="font-display font-bold text-3xl md:text-4xl tracking-tight text-white">
            Run the <span className="text-accent">number</span> before you buy the parts
          </h2>
        </Reveal>
        <Reveal delay={0.1}>
          <p className="mt-5 text-lg text-white/65">
            Pick a bike. Pick a strip. We&rsquo;ll run the physics — free and open
            source, no account needed.
          </p>
        </Reveal>
        <Reveal delay={0.2}>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link href="/simulator" className="btn-primary">
              Run your first sim
            </Link>
            <a
              href={REPO_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-ghost"
            >
              Read the source on GitHub
            </a>
          </div>
          <p className="mt-4 label-mono">{LICENSE_SPDX} · every line of the physics is public</p>
        </Reveal>
      </div>
    </section>
  );
}

// ──────────────────────────────────────────────────────────────────────
function HomePageInner() {
  // GROWTH_EXP_001: hero-CTA copy A/B test — see data/growth_experiments.json
  // Default OFF (control). Visitors who land with ?variant=B see the
  // verb-result variant. Same href, same SEO, same h1.
  const searchParams = useSearchParams();
  const ctaVariant = searchParams?.get('variant') === 'B' ? 'B' : 'A';
  const heroCtaLabel = ctaVariant === 'B' ? "See your bike's quarter-mile ET" : 'Run a sim';

  // GROWTH_EXP_018: hero subhead value-prop framing A/B test
  // Default OFF (control = physics-first). Visitors who land with ?exp18=B
  // see the Indian-community-first framing that names the drag-racing
  // identity up front rather than the technical methodology.
  // Uses ?exp18=B (not ?variant=B) to avoid contaminating EXP-001 arms.
  // Same h1, same CTAs, same meta — SEO-safe. Single variable: subhead only.
  const exp18Variant = searchParams?.get('exp18') === 'B' ? 'B' : 'A';

  return (
    <div className="min-h-screen bg-asphalt-0 text-white antialiased overflow-x-clip">
      <SiteNav />

      <main id="main">
        {/* ─── ① HERO ───────────────────────────────────────────── */}
        <section className="relative overflow-hidden pt-16">
          {/* Backdrop: the static "launch" strip render (signal-orange trail
              on night asphalt, web/scripts/generate_hero_image.py) under
              readability fades — darkest over the left text column. Still a
              single static image: no canvas, no scroll effects. */}
          <div className="pointer-events-none absolute inset-0" aria-hidden="true">
            <div
              className="absolute inset-0 bg-cover bg-[position:52%_100%] opacity-70 md:opacity-100"
              style={{ backgroundImage: "url('/hero/launch.webp')" }}
            />
            {/* text-column + edge fades keep the headline on pure asphalt */}
            <div className="absolute inset-0 bg-gradient-to-r from-asphalt-0 from-0% via-asphalt-0/40 via-40% to-transparent to-75%" />
            <div className="absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-asphalt-0 to-transparent" />
            <div className="absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-asphalt-0 to-transparent" />
          </div>

          <div className="relative mx-auto grid max-w-6xl items-center gap-10 px-6 py-16 md:py-24 lg:grid-cols-[1.05fr_1fr] lg:gap-14">
            <div>
              <div className="flex items-center gap-3">
                <StageDots animate />
                <span className="label-mono">Physics-based · Free &amp; open source</span>
              </div>

              <h1 className="mt-6 font-display font-bold text-4xl md:text-6xl tracking-tight text-white">
                Know your time before you{' '}
                <span className="text-accent">stage</span>
              </h1>

              {/* GROWTH_EXP_018: hero subhead framing — physics-first (A) vs Indian-community-first (B) */}
              {exp18Variant === 'B' ? (
                <p
                  className="mt-5 max-w-xl text-base md:text-lg text-white/65 leading-relaxed"
                  data-exp="EXP-018"
                  data-variant="B"
                >
                  Your bike. Your strip. Your quarter-mile ET — predicted to
                  within{' '}
                  <span className="text-white">±0.007s</span> on our 10 cleanest validated runs.{' '}
                  <span className="text-white">541 Indian and global bikes</span>,{' '}
                  <span className="text-white">593 parts with INR pricing</span>,{' '}
                  <span className="text-white">Aamby Valley to MMRT.</span>
                </p>
              ) : (
                <p
                  className="mt-5 max-w-xl text-base md:text-lg text-white/65 leading-relaxed"
                  data-exp="EXP-018"
                  data-variant="A"
                >
                  A first-principles drag simulator for India&rsquo;s motorcycle
                  drag-racing community.{' '}
                  <span className="text-white">541 bikes</span>,{' '}
                  <span className="text-white">593 parts</span>,{' '}
                  <span className="text-white">20 venues</span> — validated
                  against 250 published quarter-mile tests — ±0.007s across the 10 cleanest.
                </p>
              )}

              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                {/* GROWTH_EXP_001: A/B variant — see data/growth_experiments.json */}
                <Link
                  href="/simulator"
                  data-exp="EXP-001"
                  data-variant={ctaVariant}
                  className="btn-primary"
                >
                  {heroCtaLabel}
                </Link>
                <Link href="/bikes" className="btn-ghost">
                  Browse 541 bikes
                </Link>
              </div>

              <div className="mt-6 font-mono text-xs text-white/40 tabular-nums">
                RK4 · 1ms · 15 sub-models · +0.007s mean bias across 250 benchmarks
              </div>
            </div>

            {/* Live simulator — the hero's proof (lg+ only; phones get it
                one tap away at /simulator). */}
            <Reveal className="hidden min-w-0 lg:block" y={20}>
              <SimulatorWidget />
            </Reveal>
          </div>
        </section>

        {/* ─── ② STATS ──────────────────────────────────────────── */}
        <StatsStrip />

        {/* ─── ③ HOW IT WORKS ───────────────────────────────────── */}
        <HowItWorks />

        {/* ─── ④ TOOLS ──────────────────────────────────────────── */}
        <ToolCards />

        {/* ─── ⑤ PROOF ──────────────────────────────────────────── */}
        <ProofSection />

        {/* ─── ⑥ INDIAN STRIP ───────────────────────────────────── */}
        <IndianStrip />

        {/* ─── ⑦ FAQ ────────────────────────────────────────────── */}
        <FaqSection />

        {/* ─── ⑧ CTA ────────────────────────────────────────────── */}
        <CtaBand />
      </main>

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
