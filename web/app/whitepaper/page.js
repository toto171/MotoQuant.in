import Link from 'next/link';
import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import { Reveal } from '../../components/Reveal';
import ScoreboardDigits from '../../components/ScoreboardDigits';

export const metadata = {
  title: 'Whitepaper — MotoQuant Physics Engine (15 Sub-Models + RK4)',
  description:
    'MotoQuant whitepaper: a free, open-source motorcycle quarter-mile simulator built on 15 sub-models and RK4 integration at 1 ms, checked against 250 published tests weighted by source quality across a cylinder-aware 12-cluster taxonomy. Three reference bikes are held to four decimals by CI.',
  alternates: { canonical: 'https://motoquant.in/whitepaper' },
  keywords: [
    'motoquant whitepaper',
    'motorcycle physics engine whitepaper',
    'motorcycle quarter mile calculator',
    'rk4 motorcycle simulation',
    '15 sub-model drag simulator',
    'motorcycle drag racing physics paper',
  ],
  openGraph: {
    title: 'MotoQuant — Physics Engine Whitepaper (15 Sub-Models + RK4)',
    description:
      '15 sub-models. RK4 at 1 ms. 12-cluster cylinder-aware taxonomy. Validation weighted by source quality. Reference bikes held to four decimals.',
    url: 'https://motoquant.in/whitepaper',
    type: 'article',
  },
};

const ABSTRACT = `MotoQuant is a first-principles physics engine for predicting motorcycle quarter-mile drag-racing elapsed times. The model couples 15 independent sub-models — engine torque (Willans friction), rear-tyre grip with load sensitivity and thermal evolution, gear-shift and clutch slip dynamics, weight transfer and rider centre-of-gravity shift, aerodynamic drag with per-bike Cd × A, environmental conditions (density altitude, surface μ, ambient temp), and parasitic loss budget — through a fixed-step fourth-order Runge–Kutta integrator running at one-millisecond resolution. In the 10 November 2026 sweep the model is checked against 250 published quarter-mile tests, weighted by source quality (263 matches to catalog bikes), across a cylinder-aware 12-cluster taxonomy. Overall weighted bias is +0.023 s and the weighted mean absolute error is 0.25 s. Litre sport bikes, where most benchmarks come from instrumented magazine tests, are off by 0.15 to 0.17 s on average (weighted); across the ten cleanest validated runs the mean absolute error is ±0.006 s. Three reference baselines (GSX-R 1000 K5, YZF-R1 4C8 and Suzuki Hayabusa Gen1) are held exactly to the fourth decimal place by CI, and move only in a deliberate, sweep-justified accuracy pass.`;

const SECTIONS = [
  {
    id: 'introduction',
    n: '1',
    title: 'Introduction',
    body: [
      'Motorcycle drag racing in India has grown rapidly across Aamby Valley (Lonavala, Maharashtra), MMRT Chennai, the Buddh International Circuit, Kari Motor Speedway (Coimbatore), and the Hyderabad strips. The community has outgrown the available tooling: spreadsheet calculators that treat power-to-weight as the sole input, regression-based estimators trained on limited international data, and per-bike rules of thumb that fail to generalise across mass, aero, gearing, traction, and venue conditions.',
      'MotoQuant is built to fill that gap. We aim for an open, audit-able simulator whose every coefficient traces back to a physical measurement — not a fitted curve. This whitepaper documents the architecture, validation methodology, and the honest residual error budget against which we benchmark every release.',
    ],
  },
  {
    id: 'architecture',
    n: '2',
    title: 'Architecture',
    body: [
      'The simulator is structured as a fixed-step fourth-order Runge–Kutta integrator over the bike state vector ⟨x, v, ω_e, T_tire, T_clutch, gear⟩. Each timestep evaluates 15 coupled sub-models that share state through the bike configuration. The integration step is fixed at dt = 1 ms; an adaptive step-size variant is available for clutch-slip-dominated regions where the engine RPM derivative changes faster than the tyre temperature derivative.',
    ],
    list: {
      title: 'The 15 sub-models',
      items: [
        'engine — 3D torque curve (Willans friction model), peak-power and peak-torque RPM, redline, idle, two-stroke expansion-chamber resonance for piston-port engines',
        'forced_induction — turbo, supercharger, nitrous; boost ramp, mechanical loss, injection windows',
        'drivetrain — gear ratios, primary/final drive, clutch slip ratio, shift time',
        'clutch — basket inertia, slipper-clutch ramp, engagement RPM and curve, lockup transition',
        'chain — drive efficiency, sprocket geometry, chain pitch (428 / 520 / 525 / 530)',
        'tire — peak friction coefficient with load sensitivity, tread temperature (heat balance and optimum window), pressure from temperature and track preparation; a Pacejka slip curve is coded but not yet used by the integrator',
        'aero — drag coefficient × frontal area per-bike (Cd × A from 0.20 to 0.60 m² across the catalog)',
        'weight_transfer — longitudinal load shift, front/rear normal force, traction limit',
        'rider_dynamics — centre-of-gravity shift on launch and during run, tucked / sit-up Cd × A transition',
        'staging — staged-position rollout (~1 ft), reaction-time floor, two-step launch RPM',
        'environmental — air density ρ, density altitude, ambient and track temp, wind, surface grip',
        'braking — μ-limited deceleration, brake bias, fade (used for shutdown after the 402 m line)',
        'wheelie — front-wheel lift detection, wheelie-bar logic for drag-prep builds',
        'parasitic — alternator, oil pump, water pump, valvetrain power draw',
        'rolling_resistance — Crr per surface and pressure',
      ],
    },
  },
  {
    id: 'category-profiles',
    n: '3',
    title: 'Category-flavoured physics',
    body: [
      'A single set of physics constants would either over-tune for litre-class superbikes (which dominate published benchmarks) or under-tune for small-cc commuters where engine inertia, basket inertia, and chassis fluid mass are systematically smaller. Every catalog bike is auto-tagged into one of a cylinder-aware 12-cluster taxonomy — litre_sport_195p, litre_sport_600_1000, sport_twin_600_1300, mid_twin_500_700, mid_twin_300_500, single_300_500, small_i4_screamer, entry_200_300, entry_150_200, two_stroke, cruiser_1300p, other — with per-cluster knobs for over-clutching factor, engine-deceleration limit, parasitic loss multiplier, and launch RPM floor. The July 2026 revision split twins, singles, and small-cc I4 screamers out of the original displacement-only buckets after the sweep showed sport twins simming ~0.2 s fast and small-cc I4s ~1.1 s slow, then re-centred every cluster against the full weighted corpus.',
      'The dispatch is back-compat-safe: bikes constructed before the taxonomy existed reproduce their pre-April-30 results bit-exactly through an "unknown" profile that preserves the legacy code path. Our three reference baselines (K5, R1, Hayabusa) have not drifted by more than 0.0000 s during the entire taxonomy roll-out.',
    ],
  },
  {
    id: 'validation',
    n: '4',
    title: 'Validation methodology',
    body: [
      'The 10 November 2026 sweep benchmarks against 250 published quarter-mile elapsed times (263 matched to a catalog bike) where the bike, year range, and venue conditions are unambiguous. Sources are classified by quality and weighted accordingly:',
    ],
    list: {
      title: 'Source-quality weights',
      items: [
        'instrumented (Cycle World, Sport Rider, Motorcyclist with timeslip photo) — weight 1.0',
        'magazine (MCN, RideApart, BikeWale published article)               — weight 0.7',
        'aggregator (FastestLaps, MotoStatz)                                  — weight 0.5',
        'forum or unverified timeslip                                         — weight 0.3',
        'unknown / single-source                                              — weight 0.5',
        'derived (0–100 km/h × 1.6 multiplier with declared ±0.7 s)           — weight 0.1',
      ],
    },
    extra: [
      'Per-cluster bias and weighted MAE are reported with N (sample size) so the reader can judge which clusters are statistically meaningful. Derived benchmarks (mostly Indian small-cc entries) carry a declared ±0.7 s uncertainty and are down-weighted to 0.1 for that reason.',
    ],
  },
  {
    id: 'results',
    n: '5',
    title: 'Results',
    table: {
      head: ['Cluster', 'N', 'Weighted bias', 'Weighted |Δ|'],
      rows: [
        ['Litre Sport ≥195 hp',          '29',  '−0.011 s', '0.171 s'],
        ['Litre Sport 600–1000 (I4/I3)', '76',  '−0.016 s', '0.146 s'],
        ['Sport Twin 600–1300',          '44',  '−0.001 s', '0.208 s'],
        ['Mid-Twin 500–700',             '6',   '+0.135 s', '0.199 s'],
        ['Mid-Twin 300–500',             '8',   '+0.189 s', '0.355 s'],
        ['Single 300–500',               '17',  '−0.265 s', '0.620 s'],
        ['Entry 200–300',                '14',  '+0.265 s', '0.325 s'],
        ['Entry 150–200',                '13',  '−0.106 s', '0.651 s'],
        ['Small-cc I4 screamer',         '2',   '−0.195 s', '0.270 s'],
        ['Two-stroke',                   '9',   '+0.259 s', '0.339 s'],
        ['Cruiser 1300+',                '4',   '+0.034 s', '0.220 s'],
        ['Other',                        '41',  '+0.154 s', '0.367 s'],
        ['All clusters · weighted',      '263', '+0.023 s', '0.25 s'],
      ],
    },
    body: [
      'The most accurate clusters are the litre sport bikes: 600–1000 cc fours and triples (−0.016 s weighted bias, 0.146 s weighted MAE over 76 matches) and the 195 hp and up group (−0.011 s, 0.171 s over 29). Both sit within the ±0.20 s that instrumented Cycle World and Sport Rider tests show between runs of the same bike, and across the ten cleanest validated runs the mean absolute error is ±0.006 s. Overall weighted bias is +0.023 s, so the model is close to centred, and 130 of the 263 matched benchmarks fall within ±0.20 s (72 within ±0.10 s, 42 within ±0.05 s). The rest of the error has two sources. One is benchmark quality: the small-cc clusters include derived benchmarks with a declared ±0.7 s uncertainty. The other is the model: small bikes, singles and two-strokes carry biases of a quarter of a second in either direction, and many small bikes still run a generic primary gear ratio (reports/gearing_experiment_2026_11_10.md).',
    ],
  },
  {
    id: 'baselines',
    n: '6',
    title: 'Reference baselines',
    body: [
      'Three bikes are designated reference baselines and gated in the test suite to reproduce exactly to the fourth decimal place across every commit:',
    ],
    table: {
      head: ['Bike', 'Year', 'Power', 'Reference ET', 'Δ (current)'],
      rows: [
        ['Suzuki GSX-R 1000 K5',  '2005', '178 hp', '10.0436 s', '±0.0000 s'],
        ['Yamaha YZF-R1 4C8',     '2007', '180 hp', '10.1092 s', '±0.0000 s'],
        ['Suzuki Hayabusa Gen1',  '1999', '197 hp', '10.1100 s', '±0.0000 s'],
      ],
    },
    body2: [
      'These baselines were last re-pinned on 5 November 2026 by the 2026-10/11 accuracy epoch, which moved them from 9.9331 / 10.1436 / 10.3633 s with a full weighted sweep as evidence (since that epoch, ET is timed from the 1-ft rollout beam, as at a drag strip). Between deliberate passes like that one they do not move: a full-catalog regression golden backs them up, and a change of a ten-thousandth of a second in any of the three fails CI.',
    ],
  },
  {
    id: 'reproducibility',
    n: '7',
    title: 'Reproducibility',
    body: [
      'MotoQuant is open to external audit. The simulator code, all sub-model coefficients, the 534-bike catalog, the 546-part library, and every venue\'s seasonal weather profile are inspectable. Every parts ROI calculation is deterministic given the bike configuration and venue conditions. We publish:',
    ],
    list: {
      title: '',
      items: [
        'reports/ directory with full validation sweeps (JSON + Markdown summaries) — one report per release',
        'tests/ — about 6,200 tests covering catalog integrity, physics, API, and silent-failure detection across all 534 bikes',
        '/docs/validation — the complete benchmark table with per-bike sources',
        '/validation — the interactive real-vs-simulated accuracy explorer',
        'CLAUDE.md — the project diary, with every design decision and trade-off recorded chronologically',
      ],
    },
    extra: [
      'External calibration is supported through the Phase 3 import pipeline. The hosted service accepts Dragy GPS logs (CSV / JSON / VBO) and dyno sheets (DynoJet, generic metric, MoTeC) with full SAE J1349 atmospheric correction, and overlays each real run against the simulation split by split. The offline engine toolchain additionally parses ECU logs (Woolich Racing, Power Commander PC-Link, MoTeC i2) and includes an auto-calibrator that fits Cd and μ-peak jointly via differential evolution followed by Nelder–Mead refinement.',
    ],
  },
  {
    id: 'limitations',
    n: '8',
    title: 'Known limitations',
    body: [
      'We are honest about where the model is bounded. The two-stroke cluster still carries a +0.077 s weighted bias and a 0.642 s weighted |Δ| because piston-port 2T launch dynamics include an off-pipe / on-pipe transition whose integral-of-power-over-time is not perfectly captured by the current expansion-chamber Gaussian curve. The Indian entry small-cc cluster (entry-150-200) carries the largest weighted |Δ| of any cluster with ten or more benchmarks at 0.702 s — bias-centred at −0.011 s but widely scattered. Its derived benchmarks carry a declared ±0.7 s uncertainty, but six of its seven instrumented rows also miss by 0.4–0.9 s, in both directions, and many small bikes still carry a known gearing limitation (reports/session_2026_11_10_epoch.md). Closing the gap needs both per-bike Dragy / VBox-measured stock data and sourced gearing for the benchmarked small bikes.',
      'The cruiser 1300+ cluster has only N=5 and the small-cc I4 screamer cluster only N=2 — too small to draw statistically meaningful conclusions. The Apache RTR 200 4V is a documented outlier: the simulator gives 18.95 s against an instrumented 18.1 s, a 0.85 s miss on a high-confidence row; we have not adjusted the model on the strength of one data point.',
    ],
  },
  {
    id: 'roadmap',
    n: '9',
    title: 'Roadmap',
    body: [
      'Three open work items, in priority order: (1) instrumented Dragy or VBOX timeslips for small bikes and two-strokes, to replace derived benchmark entries; (2) sourced primary gear ratios for small bikes, applied together with a re-tune of the small-bike launch and drivetrain losses, because applying the sourced gearing alone made the weighted error worse (reports/gearing_experiment_2026_11_10.md); (3) a launch model fitted to measured 60-ft times.',
      'Timeslips reach the project through the "Submit a timeslip" form on GitHub. A maintainer reviews each one before it joins the benchmark set, and every accepted instrumented run tightens the weighted sweep.',
    ],
  },
  {
    id: 'citation',
    n: '10',
    title: 'Citation',
    body: [
      'If you reference this whitepaper or use MotoQuant outputs in your own analysis, please cite as:',
    ],
    citation: 'Singh, R. & Desai, A. (2026). MotoQuant: A first-principles drag-racing physics engine for motorcycles. Pune, India. https://motoquant.in/whitepaper',
  },
];

function Section({ s }) {
  return (
    <section id={s.id} className="scroll-mt-24 mb-16">
      <div className="flex items-baseline gap-4 mb-5">
        <span className="font-mono text-white/60 text-sm tabular-nums">§{s.n}</span>
        <h2 className="font-display font-bold text-2xl md:text-3xl tracking-tight text-white">
          {s.title}
        </h2>
      </div>
      {s.body && s.body.map((p, i) => (
        <p key={`b${i}`} className="text-white/75 leading-relaxed mb-4">
          {p}
        </p>
      ))}
      {s.list && (
        <div className="card my-6 p-5">
          {s.list.title && (
            <div className="mb-3 text-sm font-semibold text-white/80">
              {s.list.title}
            </div>
          )}
          <ul className="space-y-2 text-sm text-white/65 leading-relaxed">
            {s.list.items.map((item, i) => (
              <li key={i} className="flex gap-3">
                <span className="text-white/60 shrink-0">›</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {s.table && (
        <div className="card my-6 p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-white/[0.03] border-b border-white/10">
                  {s.table.head.map((h, i) => (
                    <th
                      key={i}
                      className="text-left px-4 py-3 text-xs font-medium text-white/60 whitespace-nowrap"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {s.table.rows.map((row, i) => {
                  const isOverall = row[0]?.includes?.('All clusters');
                  return (
                    <tr
                      key={i}
                      className={[
                        'border-b border-white/5 last:border-0',
                        isOverall ? 'bg-white/[0.04]' : '',
                      ].join(' ')}
                    >
                      {row.map((cell, j) => (
                        <td
                          key={j}
                          className={[
                            'px-4 py-3 whitespace-nowrap',
                            j === 0 ? 'text-white/85' : 'text-white/65 font-mono tabular-nums',
                            isOverall ? 'font-semibold text-white' : '',
                          ].join(' ')}
                        >
                          {cell}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
      {s.body2 && s.body2.map((p, i) => (
        <p key={`b2${i}`} className="text-white/75 leading-relaxed mb-4">
          {p}
        </p>
      ))}
      {s.extra && s.extra.map((p, i) => (
        <p key={`e${i}`} className="text-white/75 leading-relaxed mb-4">
          {p}
        </p>
      ))}
      {s.citation && (
        <pre className="card my-4 p-5 text-sm font-mono text-white/75 whitespace-pre-wrap break-words leading-relaxed">
          {s.citation}
        </pre>
      )}
    </section>
  );
}

export default function WhitepaperPage() {
  return (
    <div className="min-h-screen bg-asphalt-0 text-white">
      <SiteNav />

      <main id="main" className="pt-32 pb-20 px-6">
        <article className="max-w-4xl mx-auto">
          {/* Cover */}
          <Reveal>
          <div className="mb-16 pb-12">
            <div className="text-sm text-white/60 mb-4">
              Whitepaper · Version 1.0 · April 30, 2026 · validation data: November 2026 sweep
            </div>
            <h1 className="font-display font-bold text-4xl sm:text-5xl lg:text-6xl tracking-tight text-white mb-6">
              MotoQuant:<br />A first-principles drag-racing <span className="text-accent">physics engine</span> for motorcycles
            </h1>
            <p className="text-white/65 text-base mb-2">
              Ritwik Singh &nbsp;·&nbsp; Arya Desai
            </p>
            <p className="text-white/60 text-sm font-mono">
              MotoQuant &middot; Pune, India &middot;{' '}
              <a href="mailto:motoquant@gmail.com" className="text-white/70 hover:text-white transition-colors">
                motoquant@gmail.com
              </a>
            </p>

            {/* Top-level stats — timing-board tiles, regenerated from the
                10 November 2026 sweep (reports/acc_final_2026_11_10.json): 250 benchmarks,
                263 matches, weighted bias +0.023 s. Same corpus as /features and
                /docs/validation. */}
            <div className="mt-10 grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { seg: '15', label: 'Sub-models' },
                { seg: '534', label: 'Catalog bikes' },
                { seg: '250', label: 'Weighted benchmarks' },
                { seg: '0.023', pre: '+', post: 's', label: 'Weighted bias' },
              ].map(t => (
                <div key={t.label} className="card p-4">
                  <div className="flex items-end justify-center gap-1">
                    {t.pre && <span className="font-mono text-sm text-white/60 mb-0.5">{t.pre}</span>}
                    <ScoreboardDigits value={t.seg} h={24} label={`${t.pre || ''}${t.seg}${t.post || ''}`} />
                    {t.post && <span className="font-mono text-sm text-white/60 mb-0.5">{t.post}</span>}
                  </div>
                  <div className="label-mono mt-2 text-center">{t.label}</div>
                </div>
              ))}
            </div>
            <div className="centerline mt-12" aria-hidden="true" />
          </div>
          </Reveal>

          {/* Abstract */}
          <section id="abstract" className="mb-16 scroll-mt-24">
            <p className="mb-6 rounded-xl border border-accent/25 bg-accent/5 px-4 py-3 text-base leading-relaxed text-white/85">
              <strong className="font-semibold text-white">In short:</strong> MotoQuant predicts a motorcycle&apos;s
              quarter-mile time from physics, not from a fitted curve. This paper explains how it works, how we
              check it against 250 published results, and where it is still weak.
            </p>
            <h2 className="mb-3 font-display text-xl font-semibold text-white">Abstract</h2>
            <p className="text-white/75 leading-relaxed text-base border-l-2 border-accent/60 pl-5">
              {ABSTRACT}
            </p>
          </section>

          {/* Table of contents */}
          <nav id="toc" className="mb-16 scroll-mt-24">
            <h2 className="mb-3 font-display text-xl font-semibold text-white">Contents</h2>
            <ol className="space-y-2 columns-1 sm:columns-2 gap-x-10">
              {SECTIONS.map(s => (
                <li key={s.id} className="flex items-baseline gap-3 break-inside-avoid">
                  <span className="font-mono text-white/60 text-sm tabular-nums">§{s.n}</span>
                  <a
                    href={`#${s.id}`}
                    className="text-white/75 hover:text-white transition-colors text-sm"
                  >
                    {s.title}
                  </a>
                </li>
              ))}
            </ol>
          </nav>

          {/* Sections */}
          {SECTIONS.map(s => <Section key={s.id} s={s} />)}

          {/* Footer / next steps */}
          <div className="mt-20 pt-10 border-t border-white/5">
            <h2 className="mb-3 font-display text-xl font-semibold text-white">Continue reading</h2>
            <div className="grid sm:grid-cols-3 gap-4">
              <Link href="/docs/physics" className="group card card-hover p-5">
                <div className="font-display font-semibold text-white group-hover:text-accent transition-colors">
                  How the physics works →
                </div>
                <div className="text-sm text-white/65 mt-1">Sub-model deep-dives.</div>
              </Link>
              <Link href="/docs/validation" className="group card card-hover p-5">
                <div className="font-display font-semibold text-white group-hover:text-accent transition-colors">
                  Accuracy data →
                </div>
                <div className="text-sm text-white/65 mt-1">Per-bike benchmark table.</div>
              </Link>
              <Link href="/simulator" className="group card card-hover border-accent/40 p-5">
                <div className="font-display font-semibold text-accent">Open the simulator →</div>
                <div className="text-sm text-white/65 mt-1">See the engine for yourself.</div>
              </Link>
            </div>
          </div>
        </article>
      </main>

      <SiteFooter />
    </div>
  );
}
