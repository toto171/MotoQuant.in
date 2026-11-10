/**
 * MotoQuant — landing page (CLARITY v6, web/DESIGN.md §5 "/ — landing").
 *
 * A SERVER component: every section is plain HTML in the first response — no
 * scroll-triggered reveals, no counters, no client-only gating (the previous
 * page wrapped everything in a useSearchParams Suspense boundary, which made
 * the prerendered HTML empty). Only the calculator widget is client code.
 *
 * Structure: hero + calculator · what do you want to do · how it works ·
 * can I trust the numbers · open source · FAQ.
 *
 * Stat-audit shapes preserved (scripts/audit_headline_stats.py): STATS
 * (`num: N, label: 'BIKES'`), the "541 bikes" / "584 parts" / "254 tires" /
 * "20 venues" / "250 benchmarks" phrasing, ACCURACY_TILES, HONEST_CLUSTERS,
 * TOP10.
 */

import Link from 'next/link';
import {
  Gauge, Wrench, Settings2, GitCompare, GitFork, Github, PlusCircle, Flag, BookOpen,
} from 'lucide-react';

import SiteNav from '../components/SiteNav';
import SiteFooter from '../components/SiteFooter';
import SimulatorWidget from '../components/SimulatorWidget';
import { FAQ_ITEMS } from './StructuredData';

const REPO_URL = 'https://github.com/toto171/MotoQuant.in';
const ISSUES_URL = `${REPO_URL}/issues/new/choose`;

// ─── Accuracy: the clusters where published data is good ──────────────
// Per the 8 August 2026 weighted sweep (reports/acc_final_2026_08_08.json).
// Small-bike / two-stroke / cruiser groups are limited by the quality of
// published tests, not the model, and are shown in full on /docs/validation.
const HONEST_CLUSTERS = [
  { name: 'Litre sport bikes, 195 hp and up', bias: 0.0271, mae: 0.1466, n: 30 },
  { name: 'Litre sport bikes, 600–1000 cc', bias: -0.0090, mae: 0.1755, n: 72 },
  { name: 'Sport twins, 600–1300 cc', bias: 0.0063, mae: 0.2459, n: 48 },
  { name: 'All bikes, weighted overall', bias: 0.0073, mae: 0.2629, n: 276 },
];

// MUST equal the docs/validation TOP10 (8 August 2026 sweep — the 10 smallest
// differences across the matched set, mean ±0.007 s; every row is instrumented
// or magazine data). Sync both together.
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

// What the catalog holds (synced to motoquant.db by audit_headline_stats.py).
const STATS = [
  { num: 541, label: 'BIKES' },
  { num: 584, label: 'PARTS' },
  { num: 254, label: 'TIRES' },
  { num: 20,  label: 'VENUES' },
];
const STAT_WORDS = { BIKES: 'bikes', PARTS: 'parts', TIRES: 'tyres', VENUES: 'venues' };

// Aggregate accuracy tiles (8 August 2026 sweep).
const ACCURACY_TILES = [
  { num: '250',     label: 'published tests checked' },
  { num: '75',      label: 'within 0.10 s' },
  { num: '138',     label: 'within 0.20 s' },
  { num: '±0.007 s', label: 'average error, 10 best' },
];

const TASKS = [
  {
    icon: Gauge,
    title: 'See how fast my bike is',
    body: 'Pick a bike and get its quarter-mile time, finish-line speed and top speed.',
    href: '/simulator',
  },
  {
    icon: Wrench,
    title: 'Find the best parts for my budget',
    body: 'Tell us how much you want to spend. We test every compatible part and pick the combination that makes the bike quickest.',
    href: '/optimize',
  },
  {
    icon: Settings2,
    title: 'Get a race-day setup',
    body: 'Gearing, launch RPM and tyre pressure that suit the air and altitude where you are racing.',
    href: '/autotune',
  },
  {
    icon: GitCompare,
    title: 'Compare two bikes',
    body: 'Race any two bikes head to head. Open the simulator, switch to Advanced and choose Compare.',
    href: '/simulator',
  },
];

const STEPS = [
  {
    title: 'Pick your bike',
    body: 'Choose from 541 bikes, from a Pulsar NS200 to a Hayabusa. Each has its own gearing, weight, aerodynamics and power curve.',
  },
  {
    title: 'Say where you are racing',
    body: 'Optional. Altitude, heat and humidity change how much power an engine makes, so a result at Aamby Valley is not the same as one at the coast.',
  },
  {
    title: 'Read your time, then try upgrades',
    body: 'You get your quarter-mile time in plain words. Then see which parts, gearing and setup would make it quicker, and what each tenth of a second costs.',
  },
];

function signed(n) {
  return `${n > 0 ? '+' : n < 0 ? '−' : '±'}${Math.abs(n).toFixed(3)} s`;
}

function SectionHead({ eyebrow, title, lede }) {
  return (
    <div className="max-w-2xl">
      <p className="eyebrow">{eyebrow}</p>
      <h2 className="mt-2 font-display text-2xl font-bold tracking-tight text-white md:text-4xl">
        {title}
      </h2>
      {lede && <p className="mt-3 text-base leading-relaxed text-white/75 md:text-lg">{lede}</p>}
    </div>
  );
}

export default function HomePage() {
  return (
    <div className="min-h-screen overflow-x-clip bg-asphalt-0 text-white antialiased">
      <SiteNav />

      <main id="main">
        {/* ─── Hero + calculator ──────────────────────────────────── */}
        <section className="relative overflow-hidden pt-16">
          {/* Theme-aware backdrop: soft accent glow built from CSS variables,
              so it reads correctly in both the light and dark themes. */}
          <div
            className="pointer-events-none absolute inset-0"
            aria-hidden="true"
            style={{
              backgroundImage:
                'radial-gradient(60rem 28rem at 85% 0%, rgb(var(--accent) / 0.14), transparent 70%), radial-gradient(40rem 24rem at 0% 100%, rgb(var(--accent) / 0.06), transparent 70%)',
            }}
          />

          <div className="relative mx-auto grid max-w-6xl items-start gap-8 px-4 pb-14 pt-8 sm:px-6 md:pb-20 md:pt-14 lg:grid-cols-[1fr_1.1fr] lg:gap-12">
            <div className="min-w-0 lg:pt-6">
              <p className="eyebrow">Free and open source</p>
              <h1 className="mt-3 font-display text-4xl font-bold tracking-tight text-white md:text-6xl">
                Know your quarter-mile time before you race.
              </h1>
              <p className="mt-4 max-w-xl text-base leading-relaxed text-white/75 md:text-lg">
                Pick your bike, see how fast it should run, and find out what actually
                makes it quicker. Free and open source.
              </p>

              <div className="mt-6 flex flex-col gap-3 sm:flex-row">
                <Link href="/simulator" className="btn-primary">
                  Open the simulator
                </Link>
                <Link href="/bikes" className="btn-ghost">
                  Browse 541 bikes
                </Link>
              </div>

              <p className="mt-5 text-sm text-white/60">
                Checked against 250 published quarter-mile tests.
              </p>
            </div>

            <div className="min-w-0">
              <SimulatorWidget />
            </div>
          </div>
        </section>

        {/* ─── What do you want to do? ────────────────────────────── */}
        <section className="border-t border-white/10 px-4 py-14 sm:px-6 md:py-20">
          <div className="mx-auto max-w-6xl">
            <SectionHead eyebrow="Start here" title="What do you want to do?" />
            <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {TASKS.map(({ icon: Icon, title, body, href }) => (
                <Link
                  key={title}
                  href={href}
                  className="card card-hover card-pad flex h-full flex-col"
                >
                  <span className="flex h-11 w-11 items-center justify-center rounded-xl border border-white/10 bg-asphalt-3">
                    <Icon className="text-accent" size={20} aria-hidden="true" />
                  </span>
                  <h3 className="mt-4 font-display text-lg font-semibold text-white">{title}</h3>
                  <p className="mt-2 flex-1 text-sm leading-relaxed text-white/70">{body}</p>
                </Link>
              ))}
            </div>
          </div>
        </section>

        {/* ─── How it works ───────────────────────────────────────── */}
        <section className="border-t border-white/10 bg-asphalt-1 px-4 py-14 sm:px-6 md:py-20">
          <div className="mx-auto max-w-6xl">
            <SectionHead eyebrow="How it works" title="Three steps to your number" />
            <ol className="mt-8 grid gap-4 md:grid-cols-3">
              {STEPS.map((s, i) => (
                <li key={s.title} className="card card-pad">
                  <span className="step-badge" aria-hidden="true">{i + 1}</span>
                  <h3 className="mt-3 font-display text-lg font-semibold text-white">
                    <span className="sr-only">Step {i + 1}: </span>
                    {s.title}
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-white/70">{s.body}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* ─── Can I trust the numbers? ───────────────────────────── */}
        <section id="accuracy" className="border-t border-white/10 px-4 py-14 sm:px-6 md:py-20">
          <div className="mx-auto max-w-6xl">
            <SectionHead
              eyebrow="Accuracy"
              title="Can I trust the numbers?"
              lede="For most bikes, yes. We compare MotoQuant with 250 benchmarks from published tests by Cycle World, Sport Rider, MCN and Motorcyclist, and publish every miss. On the 10 closest bikes the simulator is within 0.01 s of the magazine time on average."
            />

            <dl className="mt-8 grid grid-cols-2 gap-4 md:grid-cols-4">
              {ACCURACY_TILES.map((t) => (
                <div key={t.label} className="card card-pad">
                  <dd className="font-display text-3xl font-bold tabular-nums text-accent md:text-4xl">
                    {t.num}
                  </dd>
                  <dt className="mt-1 text-sm text-white/70">{t.label}</dt>
                </div>
              ))}
            </dl>

            <div className="card card-pad mt-6">
              <h3 className="font-display text-lg font-semibold text-white">
                Where it is strongest
              </h3>
              <div className="mt-3">
                {HONEST_CLUSTERS.map((c) => (
                  <div key={c.name} className="stat-row flex-wrap gap-y-1">
                    <span>{c.name}</span>
                    <span className="text-right">
                      {c.n} tests · off by {c.mae.toFixed(2)} s on average ·{' '}
                      {c.bias >= 0
                        ? `leans ${c.bias.toFixed(3)} s slow`
                        : `leans ${Math.abs(c.bias).toFixed(3)} s quick`}
                    </span>
                  </div>
                ))}
              </div>
              <p className="mt-4 text-sm leading-relaxed text-white/70">
                <strong className="font-semibold text-white">The honest limit:</strong> small
                bikes, two-strokes and cruisers are less well covered by published tests, so
                their results carry a wider margin. That reflects missing data more than the
                physics.{' '}
                <Link
                  href="/validation"
                  className="text-accent underline underline-offset-2 hover:text-accent-bright"
                >
                  See the full accuracy report
                </Link>
                .
              </p>
            </div>

            <div className="card mt-6 overflow-hidden">
              <div className="border-b border-white/10 px-5 py-3 md:px-6">
                <h3 className="font-display text-lg font-semibold text-white">
                  The 10 closest matches
                </h3>
                <p className="text-sm text-white/60">
                  Published time against MotoQuant&rsquo;s time for the same bike.
                </p>
              </div>
              <table className="w-full text-xs sm:text-sm">
                <caption className="sr-only">
                  The ten bikes where MotoQuant is closest to the published quarter-mile time
                </caption>
                <thead>
                  <tr className="border-b border-white/10 text-left text-white/70">
                    <th scope="col" className="px-3 py-3 font-medium md:px-6">Bike</th>
                    <th scope="col" className="px-1.5 py-3 text-right font-medium">Published</th>
                    <th scope="col" className="px-1.5 py-3 text-right font-medium">MotoQuant</th>
                    <th scope="col" className="px-1.5 py-3 text-right font-medium md:px-4">Difference</th>
                    <th scope="col" className="hidden px-4 py-3 text-right font-medium md:table-cell md:px-6">
                      Source
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {TOP10.map((b) => (
                    <tr key={b.rank} className="border-b border-white/[0.06] last:border-b-0">
                      <td className="px-3 py-3 md:px-6">
                        <span className="block font-semibold text-white">{b.name}</span>
                        <span className="block text-xs text-white/60">{b.year} · {b.cc}</span>
                      </td>
                      <td className="px-1.5 py-3 text-right font-mono tabular-nums text-white/75">
                        {b.target.toFixed(2)} s
                      </td>
                      <td className="px-1.5 py-3 text-right font-mono font-semibold tabular-nums text-white">
                        {b.sim.toFixed(2)} s
                      </td>
                      <td className="px-1.5 py-3 text-right font-mono tabular-nums text-white/75 md:px-4">
                        {signed(b.delta)}
                      </td>
                      <td className="hidden px-4 py-3 text-right text-xs text-white/60 md:table-cell md:px-6">
                        {b.source}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-6">
              <Link href="/validation" className="btn-ghost">
                Explore every benchmark
              </Link>
            </div>
          </div>
        </section>

        {/* ─── Open source ────────────────────────────────────────── */}
        <section className="border-t border-white/10 bg-asphalt-1 px-4 py-14 sm:px-6 md:py-20">
          <div className="mx-auto max-w-6xl">
            <SectionHead
              eyebrow="Open source"
              title="Free, open, and yours to improve"
              lede="MotoQuant is released under the MIT License. The simulator, the bike catalog and the accuracy checks are all public, so anyone can read the maths, fix a number or run their own copy."
            />

            <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[
                { icon: Github, title: 'View on GitHub', body: 'Read the code, report a bug or star the project.', href: REPO_URL, external: true },
                { icon: PlusCircle, title: 'Add your bike', body: 'Missing a model? Tell us the specs and we will add it.', href: ISSUES_URL, external: true },
                { icon: Flag, title: 'Send us your timeslip', body: 'Real runs make the numbers better. Share yours.', href: ISSUES_URL, external: true },
                { icon: BookOpen, title: 'Read the physics', body: 'How the simulation works, step by step, in plain language.', href: '/docs/physics' },
              ].map(({ icon: Icon, title, body, href, external }) => (
                <a
                  key={title}
                  href={href}
                  {...(external ? { target: '_blank', rel: 'noopener noreferrer' } : {})}
                  className="card card-hover card-pad flex h-full flex-col"
                >
                  <span className="flex h-11 w-11 items-center justify-center rounded-xl border border-white/10 bg-asphalt-3">
                    <Icon className="text-accent" size={20} aria-hidden="true" />
                  </span>
                  <h3 className="mt-4 font-display text-lg font-semibold text-white">{title}</h3>
                  <p className="mt-2 flex-1 text-sm leading-relaxed text-white/70">{body}</p>
                </a>
              ))}
            </div>

            <p className="mt-8 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-white/70">
              <GitFork size={16} className="text-white/60" aria-hidden="true" />
              <span>What is inside:</span>
              {STATS.map((s, i) => (
                <span key={s.label}>
                  <strong className="font-semibold text-white tabular-nums">{s.num}</strong>{' '}
                  {STAT_WORDS[s.label]}
                  {i < STATS.length - 1 ? ',' : '.'}
                </span>
              ))}
            </p>
          </div>
        </section>

        {/* ─── FAQ ────────────────────────────────────────────────── */}
        <section className="border-t border-white/10 px-4 py-14 sm:px-6 md:py-20">
          <div className="mx-auto max-w-3xl">
            <SectionHead eyebrow="Questions" title="Straight answers" />
            <div className="mt-8 space-y-3">
              {FAQ_ITEMS.map(({ q, a }) => (
                <details key={q} className="card group px-5 py-2">
                  <summary className="flex min-h-[48px] cursor-pointer list-none items-center justify-between gap-4 [&::-webkit-details-marker]:hidden">
                    <span className="font-display text-base font-semibold text-white md:text-lg">
                      {q}
                    </span>
                    <span
                      aria-hidden="true"
                      className="shrink-0 text-xl text-white/60 transition-transform duration-200 group-open:rotate-45"
                    >
                      +
                    </span>
                  </summary>
                  <p className="pb-3 pt-1 text-sm leading-relaxed text-white/75 md:text-base">{a}</p>
                </details>
              ))}
            </div>

            <div className="mt-10 text-center">
              <Link href="/simulator" className="btn-primary">
                Open the simulator
              </Link>
            </div>
          </div>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}
