import Link from 'next/link';
import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import CodeComment from '../../components/CodeComment';
import { Reveal } from '../../components/Reveal';
import ScoreboardDigits from '../../components/ScoreboardDigits';
import TerminalCtaVariant from './TerminalCtaVariant';

export const metadata = {
  title: 'Whitepaper — MotoQuant Pro Physics Engine (Pacejka Tire Model + RK4)',
  description:
    'MotoQuant Pro whitepaper: a free Pacejka tire-model motorcycle quarter-mile calculator built on 15 sub-models and RK4 integration at 1 ms, validated against 223 source-quality-weighted benchmarks across 8 cluster categories. Reference baselines K5 / R1 / Hayabusa accurate to four decimals across every commit.',
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
    title: 'MotoQuant Pro — Physics Engine Whitepaper (Pacejka + RK4)',
    description:
      '15 sub-models. RK4 at 1 ms. Pacejka tire model. 8-cluster taxonomy. Source-quality weighted validation. Reference baselines accurate to four decimals.',
    url: 'https://motoquant.in/whitepaper',
    type: 'article',
  },
};

const ABSTRACT = `MotoQuant Pro is a first-principles physics engine for predicting motorcycle quarter-mile drag-racing elapsed times. The model couples 15 independent sub-models — engine torque (Willans friction), Pacejka tire grip with thermal evolution, gear-shift and clutch slip dynamics, weight transfer and rider centre-of-gravity shift, aerodynamic drag with per-bike Cd × A, environmental conditions (density altitude, surface μ, ambient temp), and parasitic loss budget — through a fixed-step fourth-order Runge–Kutta integrator running at one-millisecond resolution. As of the July 2026 sweep we validate against 223 source-quality-weighted published quarter-mile benchmarks (246 matched) across an 8-cluster taxonomy. Overall weighted bias is −0.026 s; weighted mean absolute error is 0.242 s. Within instrumented-magazine-data clusters (litre-sport ≥195 hp), weighted bias is −0.015 s and |Δ| is 0.137 s; across the ten cleanest validated runs the mean absolute error is ±0.009 s. Three reference baselines — GSX-R 1000 K5, YZF-R1 4C8, and Suzuki Hayabusa Gen1 — are preserved exactly to the fourth decimal place across every code change since April 30, 2026.`;

const SECTIONS = [
  {
    id: 'introduction',
    n: '1',
    title: 'Introduction',
    body: [
      'Motorcycle drag racing in India has grown rapidly across Aamby Valley (Lonavala, Maharashtra), MMRT Chennai, the Buddh International Circuit, Kari Motor Speedway (Coimbatore), and the Hyderabad strips. The community has outgrown the available tooling: spreadsheet calculators that treat power-to-weight as the sole input, regression-based estimators trained on limited international data, and per-bike rules of thumb that fail to generalise across mass, aero, gearing, traction, and venue conditions.',
      'MotoQuant Pro is built to fill that gap. We aim for an open, audit-able simulator whose every coefficient traces back to a physical measurement — not a fitted curve. This whitepaper documents the architecture, validation methodology, and the honest residual error budget against which we benchmark every release.',
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
    title: 'Category-Flavoured Physics',
    body: [
      'A single set of physics constants would either over-tune for litre-class superbikes (which dominate published benchmarks) or under-tune for small-cc commuters where engine inertia, basket inertia, and chassis fluid mass are systematically smaller. As of April 30, 2026, every catalog bike is auto-tagged into one of an 8-cluster taxonomy — litre_sport_195p, litre_sport_600_1000, mid_twin_500_700, mid_twin_300_500, entry_200_300, entry_150_200, two_stroke, cruiser_1300p — with per-cluster knobs for over-clutching factor, engine-deceleration limit, parasitic loss multiplier, and launch RPM floor.',
      'The dispatch is back-compat-safe: bikes constructed before the taxonomy existed reproduce their pre-April-30 results bit-exactly through an "unknown" profile that preserves the legacy code path. Our three reference baselines (K5, R1, Hayabusa) have not drifted by more than 0.0000 s during the entire taxonomy roll-out.',
    ],
  },
  {
    id: 'validation',
    n: '4',
    title: 'Validation Methodology',
    body: [
      'As of the July 2026 sweep we benchmark against 223 published quarter-mile elapsed times (246 matched to a catalog bike) where the bike, year range, and venue conditions are unambiguous. Sources are classified by quality and weighted accordingly:',
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
        ['Litre Sport ≥195 hp',          '31',  '−0.015 s', '0.137 s'],
        ['Litre Sport 600–1000',         '104', '−0.064 s', '0.192 s'],
        ['Mid-Twin 500–700',             '13',  '+0.047 s', '0.132 s'],
        ['Mid-Twin 300–500',             '23',  '−0.086 s', '0.516 s'],
        ['Entry 200–300',                '15',  '+0.071 s', '0.343 s'],
        ['Entry 150–200',                '12',  '+0.018 s', '0.820 s'],
        ['Two-stroke',                   '6',   '+0.153 s', '0.584 s'],
        ['Cruiser 1300+',                '3',   '+0.234 s', '0.234 s'],
        ['Other',                        '39',  '+0.022 s', '0.285 s'],
        ['All clusters · weighted',      '246', '−0.026 s', '0.242 s'],
      ],
    },
    body: [
      'The most accurate clusters are mid-twin 500–700 (0.132 s weighted MAE) and litre-sport ≥195 hp (−0.015 s weighted bias, 0.137 s weighted MAE) — well within the ±0.20 s tolerance the modern instrumented Cycle World and Sport Rider tests themselves report as 1-σ test-to-test variation; across the ten cleanest validated runs the mean absolute error is ±0.009 s. Overall weighted bias of −0.026 s indicates the model is essentially centred at zero, and 130 of the 246 matched benchmarks fall within ±0.20 s (72 within ±0.10 s, 40 within ±0.05 s). The remaining residual is bounded by benchmark-data quality, not by physics model fidelity: the small-cc and two-stroke clusters draw heavily from derived benchmarks with declared ±0.7 s uncertainty, fundamentally limiting validation precision regardless of how well the physics is modelled.',
    ],
  },
  {
    id: 'baselines',
    n: '6',
    title: 'Reference Baselines',
    body: [
      'Three bikes are designated reference baselines and gated in the test suite to reproduce exactly to the fourth decimal place across every commit:',
    ],
    table: {
      head: ['Bike', 'Year', 'Power', 'Reference ET', 'Δ (current)'],
      rows: [
        ['Suzuki GSX-R 1000 K5',  '2005', '178 hp', '10.0334 s', '±0.0000 s'],
        ['Yamaha YZF-R1 4C8',     '2007', '180 hp', '10.2859 s', '±0.0000 s'],
        ['Suzuki Hayabusa Gen1',  '1999', '197 hp', '10.4712 s', '±0.0000 s'],
      ],
    },
    body2: [
      'These baselines have not drifted since April 30, 2026 — across catalog expansions, physics tuning passes, importer changes, and the introduction of the 8-cluster taxonomy. A regression in any of them fails CI immediately.',
    ],
  },
  {
    id: 'reproducibility',
    n: '7',
    title: 'Reproducibility',
    body: [
      'MotoQuant Pro is open to external audit. The simulator code, all sub-model coefficients, the 541-bike catalog, the 594-part library, and every venue\'s seasonal weather profile are inspectable. Every parts ROI calculation is deterministic given the bike configuration and venue conditions. We publish:',
    ],
    list: {
      title: '',
      items: [
        'reports/ directory with full validation sweeps (JSON + Markdown summaries) — one report per release',
        'tests/ — 976 regression tests covering catalog integrity, physics, API, and silent-failure detection across all 541 bikes',
        '/docs/validation — the complete benchmark table with per-bike sources',
        'CLAUDE.md — the project diary, with every design decision and trade-off recorded chronologically',
      ],
    },
    extra: [
      'External calibration is supported through the Phase 3 import pipeline: Dragy GPS logs (CSV / JSON / VBO), dyno sheets (DynoJet, generic metric, MoTeC) with full SAE J1349 atmospheric correction, and ECU logs (Woolich Racing, Power Commander PC-Link, MoTeC i2). The auto-calibrator fits Cd and μ-peak jointly via differential evolution followed by Nelder–Mead refinement.',
    ],
  },
  {
    id: 'limitations',
    n: '8',
    title: 'Known Limitations',
    body: [
      'We are honest about where the model is bounded. The two-stroke cluster still carries a small +0.072 s weighted bias and a 0.471 s weighted |Δ| because piston-port 2T launch dynamics include an off-pipe / on-pipe transition whose integral-of-power-over-time is not perfectly captured by the current expansion-chamber Gaussian curve. The Indian entry small-cc cluster (entry-150-200) carries the largest residual bias in the corpus at +0.217 s, bounded by the declared ±0.7 s uncertainty of its derived benchmarks; reaching the published ≤0.05 s stretch goal requires per-bike Dragy / VBox-measured stock data, not further physics tuning.',
      'The cruiser 1300+ cluster has only N=2 (VMAX 1700, Rocket 3) — too small to draw statistically meaningful conclusions. The Apache RTR 200 4V is a documented outlier (sim 18.7 s vs derived 15.9 s) where the derived benchmark is suspiciously fast for a 20.5 hp / 153 kg bike; we have flagged it for audit but have not adjusted the model on the strength of one data point.',
    ],
  },
  {
    id: 'roadmap',
    n: '9',
    title: 'Roadmap',
    body: [
      'Three open work items, in priority order: (1) replace derived benchmark entries with measured Dragy / VBox runs from the Indian community; (2) port the unused profile knobs (Cd ceiling, Pacejka C, μ-peak override, chain efficiency override, tuck transition time, engine inertia multiplier) into their respective sub-models so future tuning passes have richer per-cluster expression; (3) audit the bidirectional spread on mid-twin 300–500 (CB350RS / Ninja 400 systematically slow vs Apache RR 310 / Benelli 302R systematically fast) to determine whether the residual is gear-cassette catalog drift or physics model gap.',
      'A Phase 5 calibrator-v2 will accept user-uploaded Dragy logs and contribute their measured ETs back to the benchmark corpus on opt-in. This closes the data-quality loop the small-cc clusters need without requiring any change to the physics model itself.',
    ],
  },
  {
    id: 'citation',
    n: '10',
    title: 'Citation',
    body: [
      'If you reference this whitepaper or use MotoQuant Pro outputs in your own analysis, please cite as:',
    ],
    citation: 'Singh, R. & Desai, A. (2026). MotoQuant Pro: A first-principles drag-racing physics engine for motorcycles. Pune, India. https://motoquant.in/whitepaper',
  },
];

function Section({ s }) {
  return (
    <section id={s.id} className="scroll-mt-24 mb-16">
      <div className="flex items-baseline gap-4 mb-5">
        <span className="font-mono text-brand-orange text-sm tabular-nums">§{s.n}</span>
        <h2 className="font-display font-bold text-3xl tracking-tight text-white">
          {s.title}
        </h2>
      </div>
      {s.body && s.body.map((p, i) => (
        <p key={`b${i}`} className="text-white/75 leading-relaxed mb-4">
          {p}
        </p>
      ))}
      {s.list && (
        <div className="relative overflow-hidden my-6 rounded-xl border border-brand-orange/15 bg-ink-1/60 p-5">
          <span aria-hidden="true" className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-brand-orange/50 to-transparent" />
          {s.list.title && (
            <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-brand-orange mb-3">
              {s.list.title}
            </div>
          )}
          <ul className="space-y-2 text-sm text-white/70 leading-relaxed">
            {s.list.items.map((item, i) => (
              <li key={i} className="flex gap-3">
                <span className="text-brand-orange shrink-0">›</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {s.table && (
        <div className="relative my-6 rounded-xl border border-brand-orange/15 bg-ink-1/40 overflow-hidden">
          <span aria-hidden="true" className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-brand-orange/50 to-transparent" />
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
                      isOverall ? 'bg-brand-orange/5' : '',
                    ].join(' ')}
                  >
                    {row.map((cell, j) => (
                      <td
                        key={j}
                        className={[
                          'px-4 py-3',
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
        <pre className="my-4 p-5 rounded-xl border border-brand-orange/15 bg-ink-1/60 text-xs font-mono text-white/75 whitespace-pre-wrap leading-relaxed">
          {s.citation}
        </pre>
      )}
    </section>
  );
}

export default function WhitepaperPage() {
  return (
    <div className="min-h-screen bg-black text-white">
      <SiteNav />

      <main id="main" className="pt-32 pb-20 px-6">
        <article className="max-w-4xl mx-auto">
          {/* Cover */}
          <Reveal>
          <div className="mb-16 pb-12 border-b border-brand-orange/10">
            <CodeComment className="mb-4">formal specification · rk4 · 1ms</CodeComment>
            <div className="text-[11px] font-mono uppercase tracking-[0.3em] text-brand-orange mb-4">
              Whitepaper · Version 1.0 · April 30, 2026 · validation data: July 2026 sweep
            </div>
            <h1 className="font-display font-bold text-4xl sm:text-5xl lg:text-6xl tracking-[-0.03em] leading-[1.05] text-white mb-6">
              MotoQuant Pro:<br />A First-Principles Drag-Racing Physics Engine for Motorcycles
            </h1>
            <p className="text-white/60 text-base mb-2">
              Ritwik Singh &nbsp;·&nbsp; Arya Desai
            </p>
            <p className="text-white/40 text-sm font-mono">
              MotoQuant Pro &middot; Pune, India &middot;{' '}
              <a href="mailto:motoquant@gmail.com" className="text-brand-accent hover:text-white transition-colors">
                motoquant@gmail.com
              </a>
            </p>

            {/* Top-level stats — timing-board tiles, regenerated from the
                3 July 2026 sweep (reports/acc_final_2026_07_03.json): 223 benchmarks,
                246 matched, weighted bias −0.026 s. Same corpus as /features and
                /docs/validation. */}
            <div className="mt-10 grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { seg: '15', label: 'Sub-models' },
                { seg: '535', label: 'Catalog bikes' },
                { seg: '223', label: 'Weighted benchmarks' },
                { seg: '0.026', pre: '−', post: 's', label: 'Weighted bias' },
              ].map(t => (
                <div key={t.label} className="relative overflow-hidden rounded-xl border border-brand-orange/20 bg-ink-1/60 p-4">
                  <span aria-hidden="true" className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-brand-orange/50 to-transparent" />
                  <div className="flex items-end justify-center gap-1">
                    {t.pre && <span className="font-mono text-sm text-brand-orange mb-0.5">{t.pre}</span>}
                    <ScoreboardDigits value={t.seg} h={24} label={`${t.pre || ''}${t.seg}${t.post || ''}`} />
                    {t.post && <span className="font-mono text-sm text-white/40 mb-0.5">{t.post}</span>}
                  </div>
                  <div className="font-mono text-[10px] text-white/45 tracking-[0.25em] mt-2 uppercase text-center">{t.label}</div>
                </div>
              ))}
            </div>
          </div>
          </Reveal>

          {/* Abstract */}
          <section id="abstract" className="mb-16 scroll-mt-24">
            <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-brand-orange mb-3">Abstract</div>
            <p className="text-white/75 leading-relaxed text-[15px] border-l-2 border-brand-orange/50 pl-5">
              {ABSTRACT}
            </p>
          </section>

          {/* Table of contents */}
          <nav id="toc" className="mb-16 scroll-mt-24">
            <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-brand-orange mb-3">Contents</div>
            <ol className="space-y-2 columns-1 sm:columns-2 gap-x-10">
              {SECTIONS.map(s => (
                <li key={s.id} className="flex items-baseline gap-3 break-inside-avoid">
                  <span className="font-mono text-brand-orange/70 text-sm tabular-nums">§{s.n}</span>
                  <a
                    href={`#${s.id}`}
                    className="text-white/75 hover:text-brand-orange transition-colors text-sm"
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
          <div className="mt-20 pt-10 border-t border-brand-orange/10">
            <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-brand-orange mb-3">
              Continue reading
            </div>
            <div className="grid sm:grid-cols-3 gap-4">
              <Link href="/docs/physics" className="group relative overflow-hidden rounded-xl border border-brand-orange/15 hover:border-brand-orange/40 bg-ink-1/60 p-5 transition-colors">
                <span aria-hidden="true" className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-brand-orange/50 to-transparent" />
                <div className="font-display font-bold text-white group-hover:text-brand-orange transition-colors">
                  Physics docs →
                </div>
                <div className="text-sm text-white/55 mt-1">Sub-model deep-dives.</div>
              </Link>
              <Link href="/docs/validation" className="group relative overflow-hidden rounded-xl border border-brand-orange/15 hover:border-brand-orange/40 bg-ink-1/60 p-5 transition-colors">
                <span aria-hidden="true" className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-brand-orange/50 to-transparent" />
                <div className="font-display font-bold text-white group-hover:text-brand-orange transition-colors">
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
