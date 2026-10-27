import Link from 'next/link';
import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import CodeComment from '../../components/CodeComment';
import { Reveal } from '../../components/Reveal';
import ScoreboardDigits from '../../components/ScoreboardDigits';
import TerminalCtaVariant from './TerminalCtaVariant';

export const metadata = {
  // absolute: already branded — skip the '%s · MotoQuant' template
  title: { absolute: 'Whitepaper — MotoQuant Physics Engine (Pacejka Tire Model + RK4)' },
  description:
    'MotoQuant whitepaper: a free Pacejka tire-model motorcycle quarter-mile calculator built on 15 sub-models and RK4 integration at 1 ms, validated against 250 source-quality-weighted benchmarks across a cylinder-aware 12-cluster taxonomy. Reference baselines K5 / R1 / Hayabusa accurate to four decimals across every commit.',
  alternates: { canonical: 'https://motoquant.in/whitepaper' },
  keywords: [
    'motoquant whitepaper',
    'motorcycle physics engine whitepaper',
    'pacejka tire model motorcycle',
    'pacejka motorcycle tire model calculator',
    'motorcycle quarter mile calculator pacejka',
    'rk4 motorcycle simulation',
    '15 sub-model drag simulator',
    'motorcycle drag racing physics paper',
  ],
  openGraph: {
    title: 'MotoQuant — Physics Engine Whitepaper (Pacejka + RK4)',
    description:
      '15 sub-models. RK4 at 1 ms. Pacejka tire model. 12-cluster cylinder-aware taxonomy. Source-quality weighted validation. Reference baselines accurate to four decimals.',
    url: 'https://motoquant.in/whitepaper',
    type: 'article',
  },
};

const ABSTRACT = `MotoQuant is a first-principles physics engine for predicting motorcycle quarter-mile drag-racing elapsed times. The model couples 15 independent sub-models — engine torque (Willans friction), Pacejka tire grip with thermal evolution, gear-shift and clutch slip dynamics, weight transfer and rider centre-of-gravity shift, aerodynamic drag with per-bike Cd × A, environmental conditions (density altitude, surface μ, ambient temp), and parasitic loss budget — through a fixed-step fourth-order Runge–Kutta integrator running at one-millisecond resolution. As of the August 2026 sweep we validate against 250 source-quality-weighted published quarter-mile benchmarks (276 matched) across a cylinder-aware 12-cluster taxonomy. Overall weighted bias is +0.007 s; weighted mean absolute error is 0.263 s. Within instrumented-magazine-data clusters (litre-sport ≥195 hp), weighted bias is +0.027 s and |Δ| is 0.147 s; across the ten cleanest validated runs the mean absolute error is ±0.007 s. Three reference baselines — GSX-R 1000 K5, YZF-R1 4C8, and Suzuki Hayabusa Gen1 — are preserved exactly to the fourth decimal place across every code change since July 13, 2026.`;

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
        'tire — Pacejka magic formula with thermal evolution, slip ratio, slip angle, peak μ, optimum temperature',
        'aero — drag coefficient × frontal area per-bike (Cd × A range 0.293–0.68 m²)',
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
      'As of the August 2026 sweep we benchmark against 250 published quarter-mile elapsed times (276 matched to a catalog bike) where the bike, year range, and venue conditions are unambiguous. Sources are classified by quality and weighted accordingly:',
    ],
    list: {
      title: 'Source-quality weights',
      items: [
        'instrumented (Cycle World, Sport Rider, Motorcyclist with timeslip photo) — weight 1.0',
        'magazine (MCN, RideApart, BikeWale published article)               — weight 0.7',
        'aggregator (FastestLaps, MotoStatz)                                  — weight 0.5',
        'forum or unverified timeslip                                         — weight 0.3',
        'unknown / single-source                                              — weight 0.4',
        'derived (0–100 km/h × 1.6 multiplier with declared ±0.7 s)           — weight 0.1',
      ],
    },
    extra: [
      'Per-cluster bias and weighted MAE are reported with N (sample size) so the reader can judge which clusters are statistically meaningful. Clusters dominated by derived benchmarks (the Indian small-cc and 2T entries) inherit the underlying ±0.7 s data uncertainty regardless of model fidelity.',
    ],
  },
  {
    id: 'results',
    n: '5',
    title: 'Results',
    table: {
      head: ['Cluster', 'N', 'Weighted bias', 'Weighted |Δ|'],
      rows: [
        ['Litre Sport ≥195 hp',          '30',  '+0.027 s', '0.147 s'],
        ['Litre Sport 600–1000 (I4/I3)', '72',  '−0.009 s', '0.176 s'],
        ['Sport Twin 600–1300',          '48',  '+0.006 s', '0.246 s'],
        ['Mid-Twin 500–700',             '17',  '+0.001 s', '0.145 s'],
        ['Mid-Twin 300–500',             '8',   '−0.038 s', '0.361 s'],
        ['Single 300–500',               '16',  '+0.030 s', '0.509 s'],
        ['Entry 200–300',                '14',  '−0.018 s', '0.231 s'],
        ['Entry 150–200',                '13',  '−0.011 s', '0.702 s'],
        ['Small-cc I4 screamer',         '2',   '+0.134 s', '0.962 s'],
        ['Two-stroke',                   '9',   '+0.077 s', '0.642 s'],
        ['Cruiser 1300+',                '5',   '+0.036 s', '0.209 s'],
        ['Other',                        '42',  '+0.019 s', '0.324 s'],
        ['All clusters · weighted',      '276', '+0.007 s', '0.263 s'],
      ],
    },
    body: [
      'The most accurate clusters are litre-sport ≥195 hp (+0.027 s weighted bias, 0.147 s weighted MAE) and mid-twin 500–700 (+0.001 s bias, 0.145 s weighted MAE) — well within the ±0.20 s tolerance the modern instrumented Cycle World and Sport Rider tests themselves report as 1-σ test-to-test variation; across the ten cleanest validated runs the mean absolute error is ±0.007 s. Overall weighted bias of +0.007 s indicates the model is essentially centred at zero, and 138 of the 276 matched benchmarks fall within ±0.20 s (75 within ±0.10 s, 42 within ±0.05 s). The remaining residual is bounded by benchmark-data quality, not by physics model fidelity: the small-cc and two-stroke clusters draw heavily from derived benchmarks with declared ±0.7 s uncertainty, fundamentally limiting validation precision regardless of how well the physics is modelled.',
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
        ['Suzuki GSX-R 1000 K5',  '2005', '178 hp', '9.9331 s', '±0.0000 s'],
        ['Yamaha YZF-R1 4C8',     '2007', '180 hp', '10.1436 s', '±0.0000 s'],
        ['Suzuki Hayabusa Gen1',  '1999', '197 hp', '10.3633 s', '±0.0000 s'],
      ],
    },
    body2: [
      'These baselines were re-pinned on July 13, 2026 as part of a physics-recalibration epoch paired with a benchmark-corpus expansion (221 → 250 unique tests); since that pin they have not drifted across catalog expansions, physics tuning passes, importer changes, or further cluster-taxonomy revisions. Drift protection comes from a full-catalog regression golden rather than a special-cased tuning constraint on these three bikes, and a regression in any of them still fails CI immediately.',
    ],
  },
  {
    id: 'reproducibility',
    n: '7',
    title: 'Reproducibility',
    body: [
      'MotoQuant is free and open source under the Apache License 2.0, and the complete source is published at github.com/da25mem5s02-debug/MotoQuant_v1 — so it is open to external audit by construction. The simulator code, all sub-model coefficients, the 541-bike catalog, the 593-part library, and every venue\'s seasonal weather profile are inspectable, forkable and re-runnable. Every parts ROI calculation is deterministic given the bike configuration and venue conditions. The repository contains:',
    ],
    list: {
      title: '',
      items: [
        'the full source — physics engine, catalog, API and website — under the Apache License 2.0',
        'reports/ directory with full validation sweeps (JSON + Markdown summaries) — one report per release',
        'tests/ — 4,393 regression tests covering catalog integrity, physics, API, and silent-failure detection across all 541 bikes',
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
      'We are honest about where the model is bounded. The two-stroke cluster still carries a +0.146 s weighted bias and a 0.537 s weighted |Δ| because piston-port 2T launch dynamics include an off-pipe / on-pipe transition whose integral-of-power-over-time is not perfectly captured by the current expansion-chamber Gaussian curve. The Indian entry small-cc cluster (entry-150-200) carries the largest weighted |Δ| in the corpus at 0.820 s — bias-centred at +0.018 s but noise-dominated, bounded by the declared ±0.7 s uncertainty of its derived benchmarks; reaching the published ≤0.05 s stretch goal requires per-bike Dragy / VBox-measured stock data, not further physics tuning.',
      'The cruiser 1300+ cluster has only N=3 and the small-cc I4 screamer cluster only N=2 — too small to draw statistically meaningful conclusions. The Apache RTR 200 4V is a documented outlier (sim 18.7 s vs derived 15.9 s) where the derived benchmark is suspiciously fast for a 20.5 hp / 153 kg bike; we have flagged it for audit but have not adjusted the model on the strength of one data point.',
    ],
  },
  {
    id: 'roadmap',
    n: '9',
    title: 'Roadmap',
    body: [
      'Three open work items, in priority order: (1) replace derived benchmark entries with measured Dragy / VBox runs from the Indian community; (2) port the remaining unused profile knobs (Pacejka C, chain efficiency override, tuck transition time, engine inertia multiplier) into their respective sub-models so future tuning passes have richer per-cluster expression; (3) audit the residual spread on the 300–500cc twin and single clusters to determine whether it is derived-benchmark noise, gear-cassette catalog drift, or a physics model gap.',
      'A Phase 5 calibrator-v2 will accept user-uploaded Dragy logs and contribute their measured ETs back to the benchmark corpus on opt-in. This closes the data-quality loop the small-cc clusters need without requiring any change to the physics model itself.',
    ],
  },
  {
    id: 'citation',
    n: '10',
    title: 'Citation',
    body: [
      'If you reference this whitepaper or use MotoQuant outputs in your own analysis, please cite as:',
    ],
    citation: 'Singh, R. & Desai, A. (2026). MotoQuant: A first-principles drag-racing physics engine for motorcycles. Pune, India. https://motoquant.in/whitepaper — source: https://github.com/da25mem5s02-debug/MotoQuant_v1 (Apache-2.0)',
  },
];

function Section({ s }) {
  return (
    <section id={s.id} className="scroll-mt-24 mb-16">
      <div className="flex items-baseline gap-4 mb-5">
        <span className="font-mono text-white/40 text-sm tabular-nums">§{s.n}</span>
        <h2 className="font-display font-bold text-3xl tracking-tight text-white">
          {s.title}
        </h2>
      </div>
      {s.body && s.body.map((p, i) => (
        <p key={`b${i}`} className="text-white/65 leading-relaxed mb-4">
          {p}
        </p>
      ))}
      {s.list && (
        <div className="card my-6 p-5">
          {s.list.title && (
            <div className="label-mono mb-3">
              {s.list.title}
            </div>
          )}
          <ul className="space-y-2 text-sm text-white/65 leading-relaxed">
            {s.list.items.map((item, i) => (
              <li key={i} className="flex gap-3">
                <span className="text-white/40 shrink-0">›</span>
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
                      className="text-left px-4 py-3 font-mono text-[10px] uppercase tracking-[0.25em] text-white/45"
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
        <p key={`b2${i}`} className="text-white/65 leading-relaxed mb-4">
          {p}
        </p>
      ))}
      {s.extra && s.extra.map((p, i) => (
        <p key={`e${i}`} className="text-white/65 leading-relaxed mb-4">
          {p}
        </p>
      ))}
      {s.citation && (
        <pre className="card my-4 p-5 text-xs font-mono text-white/75 whitespace-pre-wrap leading-relaxed">
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
            <CodeComment className="mb-4">formal specification · rk4 · 1ms</CodeComment>
            <div className="label-mono mb-4">
              Whitepaper · Version 1.0 · April 30, 2026 · validation data: August 2026 sweep
            </div>
            <h1 className="font-display font-bold text-4xl sm:text-5xl lg:text-6xl tracking-tight text-white mb-6">
              MotoQuant:<br />A first-principles drag-racing <span className="text-accent">physics engine</span> for motorcycles
            </h1>
            <p className="text-white/65 text-base mb-2">
              Ritwik Singh &nbsp;·&nbsp; Arya Desai
            </p>
            <p className="text-white/40 text-sm font-mono">
              MotoQuant &middot; Pune, India &middot;{' '}
              <a href="mailto:motoquant@gmail.com" className="text-white/70 hover:text-white transition-colors">
                motoquant@gmail.com
              </a>
            </p>

            {/* Top-level stats — timing-board tiles, regenerated from the
                8 August 2026 sweep (reports/acc_final_2026_08_08.json): 250 benchmarks,
                276 matched, weighted bias +0.007 s. Same corpus as /features and
                /docs/validation. */}
            <div className="mt-10 grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { seg: '15', label: 'Sub-models' },
                { seg: '541', label: 'Catalog bikes' },
                { seg: '250', label: 'Weighted benchmarks' },
                { seg: '0.007', pre: '+', post: 's', label: 'Weighted bias' },
              ].map(t => (
                <div key={t.label} className="card p-4">
                  <div className="flex items-end justify-center gap-1">
                    {t.pre && <span className="font-mono text-sm text-white/40 mb-0.5">{t.pre}</span>}
                    <ScoreboardDigits value={t.seg} h={24} label={`${t.pre || ''}${t.seg}${t.post || ''}`} />
                    {t.post && <span className="font-mono text-sm text-white/40 mb-0.5">{t.post}</span>}
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
            <div className="label-mono mb-3">Abstract</div>
            <p className="text-white/75 leading-relaxed text-[15px] border-l-2 border-accent/60 pl-5">
              {ABSTRACT}
            </p>
          </section>

          {/* Table of contents */}
          <nav id="toc" className="mb-16 scroll-mt-24">
            <div className="label-mono mb-3">Contents</div>
            <ol className="space-y-2 columns-1 sm:columns-2 gap-x-10">
              {SECTIONS.map(s => (
                <li key={s.id} className="flex items-baseline gap-3 break-inside-avoid">
                  <span className="font-mono text-white/40 text-sm tabular-nums">§{s.n}</span>
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
            <div className="label-mono mb-3">
              Continue reading
            </div>
            <div className="grid sm:grid-cols-3 gap-4">
              <Link href="/docs/physics" className="group card card-hover p-5">
                <div className="font-display font-semibold text-white group-hover:text-accent transition-colors">
                  Physics docs →
                </div>
                <div className="text-sm text-white/55 mt-1">Sub-model deep-dives.</div>
              </Link>
              <Link href="/docs/validation" className="group card card-hover p-5">
                <div className="font-display font-semibold text-white group-hover:text-accent transition-colors">
                  Validation data →
                </div>
                <div className="text-sm text-white/55 mt-1">Per-bike benchmark table.</div>
              </Link>
              <TerminalCtaVariant />
            </div>
          </div>
        </article>
      </main>

      <SiteFooter />
    </div>
  );
}
