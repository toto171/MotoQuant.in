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
 * (`num: N, label: 'BIKES'`), the "534 bikes" / "546 parts" / "254 tires" /
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
import StructuredData, { FAQ_ITEMS, faqSchema, SITE_URL, OG_IMAGE } from './StructuredData';

const HOME_TITLE = 'Motorcycle quarter-mile and drag race simulator | MotoQuant';
const HOME_DESCRIPTION =
  "Free quarter-mile simulator for 534 motorcycles. See your bike's time and finish-line speed, then find the parts worth buying, priced in rupees.";

export const metadata = {
  title: { absolute: HOME_TITLE },
  description: HOME_DESCRIPTION,
  alternates: { canonical: '/' },
  openGraph: {
    title: HOME_TITLE,
    description: HOME_DESCRIPTION,
    url: SITE_URL,
    siteName: 'MotoQuant',
    images: [OG_IMAGE],
    locale: 'en_IN',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: HOME_TITLE,
    description: HOME_DESCRIPTION,
    images: [OG_IMAGE],
  },
};

const REPO_URL = 'https://github.com/toto171/MotoQuant.in';
const SUGGEST_URL = `${REPO_URL}/issues/new?template=suggest-bike.yml`;
const TIMESLIP_URL = `${REPO_URL}/issues/new?template=submit-timeslip.yml`;

// ─── Accuracy: the clusters where published data is good ──────────────
// Per the 10 November 2026 weighted sweep (reports/acc_final_2026_11_10.json).
// Small-bike / two-stroke / cruiser groups are limited partly by the quality
// of published tests and, for small bikes, by a known gearing limitation
// (reports/session_2026_11_10_epoch.md); shown in full on /docs/validation.
const HONEST_CLUSTERS = [
  { name: 'Litre sport bikes, 195 hp and up', bias: -0.0106, mae: 0.1712, n: 29 },
  { name: 'Sport bikes, 600–1000 cc', bias: -0.0163, mae: 0.1462, n: 76 },
  { name: 'Sport twins, 600–1300 cc', bias: -0.0008, mae: 0.2083, n: 44 },
  { name: 'All bikes, weighted overall', bias: 0.0226, mae: 0.2495, n: 263 },
];

// MUST equal the docs/validation TOP10 (10 November 2026 sweep — the 10 smallest
// differences among non-derived benchmarks, mean ±0.006 s; DERIVED estimates
// are excluded). Sync both together.
const TOP10 = [
  { rank: 1,  name: 'Kawasaki Ninja ZX-10R',     year: 2011, cc: '998 cc',  target: 10.08, sim: 10.0786, delta: -0.001, source: 'Sport Rider, July 2011' },
  { rank: 2,  name: 'Aprilia RS 660 Factory',    year: 2025, cc: '659 cc',  target: 11.24, sim: 11.2439, delta:  0.004, source: 'MotoStatz (Dragy)' },
  { rank: 3,  name: 'Yamaha FZ6 Fazer',          year: 2004, cc: '600 cc',  target: 11.53, sim: 11.5347, delta:  0.005, source: 'Cycle World 2004' },
  { rank: 4,  name: 'BMW M 1000 RR',             year: 2021, cc: '999 cc',  target: 9.80,  sim: 9.8051,  delta:  0.005, source: 'Cycle World 2021' },
  { rank: 5,  name: 'BMW S 1000 RR',             year: 2019, cc: '999 cc',  target: 9.85,  sim: 9.8446,  delta: -0.005, source: 'Cycle World 2019' },
  { rank: 6,  name: 'Yamaha RD350',              year: 1973, cc: '347 cc',  target: 14.30, sim: 14.3058, delta:  0.006, source: 'Cycle World (period test)' },
  { rank: 7,  name: 'Yamaha VMAX 1700',          year: 2009, cc: '1679 cc', target: 10.30, sim: 10.3063, delta:  0.006, source: 'Cycle World 2009' },
  { rank: 8,  name: 'Suzuki SV650X',             year: 2018, cc: '645 cc',  target: 12.10, sim: 12.1075, delta:  0.007, source: 'motorcyclespecs.com' },
  { rank: 9,  name: 'Triumph Speed Triple 1050', year: 2005, cc: '1050 cc', target: 11.01, sim: 11.0190, delta:  0.009, source: 'Sport Rider 2005' },
  { rank: 10, name: 'Yamaha MT-10',              year: 2016, cc: '998 cc',  target: 10.35, sim: 10.3610, delta:  0.011, source: 'Cycle World 2016' },
];

// What the catalog holds (synced to motoquant.db by audit_headline_stats.py).
const STATS = [
  { num: 534, label: 'BIKES' },
  { num: 546, label: 'PARTS' },
  { num: 254, label: 'TIRES' },
  { num: 20,  label: 'VENUES' },
];
const STAT_WORDS = { BIKES: 'bikes', PARTS: 'parts', TIRES: 'tyres', VENUES: 'venues' };

// Aggregate accuracy tiles (10 November 2026 sweep).
const ACCURACY_TILES = [
  { num: '250',     label: 'published tests checked' },
  { num: '72',      label: 'within 0.10 s' },
  { num: '130',     label: 'within 0.20 s' },
  { num: '±0.006 s', label: 'average error, 10 best' },
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
    body: 'Choose from 534 bikes, from a Pulsar NS200 to a Hayabusa. Each has its own gearing, weight, aerodynamics and power curve.',
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

      {/* FAQPage markup only here: this is the one page that shows the FAQ. */}
      <StructuredData data={faqSchema()} />
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
                Pick your bike to see the time it should run and which changes
                would make it quicker.
              </p>

              <div className="mt-6 flex flex-col gap-3 sm:flex-row">
                <Link href="/simulator" className="btn-primary">
                  Open the simulator
                </Link>
                <Link href="/bikes" className="btn-ghost">
                  Browse 534 bikes
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
              lede="For sport bikes, yes. Across 263 matches with published tests (Cycle World, Sport Rider, MotoStatz Dragy runs and others), the simulator is off by 0.25 s on average, and by less on sport bikes. Every miss is published."
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
                <strong className="font-semibold text-white">Weaker areas:</strong> small
                bikes, two-strokes and cruisers are less well covered by published tests, so
                their results carry a wider margin. Small bikes are the weakest class: their
                gearing in the catalog is still inferred, and{' '}
                <a
                  href="https://github.com/toto171/MotoQuant.in/blob/main/reports/gearing_experiment_2026_11_10.md"
                  className="text-accent underline underline-offset-2 hover:text-accent-bright"
                  rel="noopener"
                >
                  fixing it needs a re-tune
                </a>
                .{' '}
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
                See every benchmark
              </Link>
            </div>
          </div>
        </section>

        {/* ─── Open source ────────────────────────────────────────── */}
        <section className="border-t border-white/10 bg-asphalt-1 px-4 py-14 sm:px-6 md:py-20">
          <div className="mx-auto max-w-6xl">
            <SectionHead
              eyebrow="Open source"
              title="Free, and anyone can improve it"
              lede="MotoQuant is released under the Apache License 2.0. The simulator, the bike catalog and the accuracy checks are all public: read the maths, correct a number or run your own copy."
            />

            <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[
                { icon: Github, title: 'Read the code', body: 'Every line of the simulator and the site, on GitHub.', href: REPO_URL, external: true },
                { icon: PlusCircle, title: 'Suggest a bike', body: 'Missing a model? Send its specifications and a source.', href: SUGGEST_URL, external: true },
                { icon: Flag, title: 'Submit a timeslip', body: 'Send a real run. Each one we check and add improves the numbers.', href: TIMESLIP_URL, external: true },
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
            <SectionHead eyebrow="FAQ" title="Common questions" />
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
