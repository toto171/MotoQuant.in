'use client';

import {
  Cpu, BarChart3, Upload, TrendingUp, Code2,
  ArrowRight, UserCircle2 } from 'lucide-react';
import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import PageHero from '../../components/PageHero';
import { Reveal } from '../../components/Reveal';
import ScoreboardDigits from '../../components/ScoreboardDigits';
import BottomCta from './BottomCta';

const SITE_URL = 'https://motoquant.in';

const FEATURES = [
  {
    id: 'physics',
    icon: Cpu,
    label: '01 / Physics Engine',
    title: <>First-principles <span className="text-accent">simulation</span></>,
    subtitle: '15 independent sub-models. No curve-fitting. Every coefficient traceable to a physical measurement.',
    body: `MotoQuant's physics engine integrates 15 coupled differential equations at a 1 ms timestep using a fixed-step RK4 integrator (with an optional adaptive solver). Unlike spreadsheet calculators that treat power-to-weight ratio as the only variable, MotoQuant models:

Pacejka tire model with thermal evolution, so grip changes as the tyre heats. Aerodynamic drag with a per-bike Cd×A (0.308–0.68 m²) — no two bikes share the same number. Gear shifting and clutch engagement dynamics including slipper clutch behaviour. Forced induction — turbo lag, supercharger mechanical loss, nitrous injection windows. Engine inertia and parasitic losses (alternator, oil pump, water pump, valvetrain).

The adaptive-dt solver is especially useful for identifying the precise clutch engagement window that produces the minimum 60-ft time. Reference baselines — GSX-R 1000 K5 at 9.933s, R1 at 10.144s, Hayabusa Gen1 at 10.363s — are pinned bit-identical on every code change and validated against the August 2026 weighted benchmark corpus (250 published tests, weighted mean |Δ| 0.263s).`,
    docsLink: '/docs/physics',
    docsLabel: 'Read the physics whitepaper',
    stats: [
      { num: '15', label: 'Sub-models' },
      { num: '1 ms', label: 'Timestep' },
      { num: '4,393', label: 'Regression tests' },
    ],
    readout: {
      title: 'engine.telemetry',
      log: [
        'rk4 step 1 ms · 15 submodels coupled',
        'pacejka thermal · aero midpoint re-eval',
        'baseline lock: k5 / r1 / hayabusa Δ 0.0000',
      ],
      value: '9.9331',
      unit: 's',
      valueLabel: 'gsx-r 1000 k5 · reference et',
      bars: [
        { label: 'traction', pct: 86 },
        { label: 'aero load', pct: 64 },
        { label: 'clutch slip', pct: 23 },
      ],
    },
  },
  {
    id: 'catalog',
    icon: BarChart3,
    label: '02 / Parts Catalog',
    title: <>Parts <span className="text-accent">ROI</span> before you buy</>,
    subtitle: '593 parts. Cost-per-tenth ranking. Budget-constrained knapsack optimiser.',
    body: `The parts catalog covers 593 upgrades across 20 categories — exhausts, ECU flashes, forced induction kits, slipper clutches, suspension, brakes, wheelie bars. Every part has a physics-accurate parameter delta: an Akrapovič slip-on doesn't add a round number of horsepower, it shifts the entire torque curve.

The ROI engine runs a 0/1 knapsack DP at ₹100 bucket resolution across any compatible parts set. Tell it your budget and it finds the combination that minimises your ET. The cost-per-tenth column tells you how many rupees you're paying per 0.1 second of ET gain — the clearest way to compare a ₹15,000 exhaust against a ₹60,000 turbo kit.

Build profiles — Street Legal, Drag Prep, Full Race — pre-filter the catalog so you don't accidentally spec a nitrous kit onto a street-registered bike.`,
    docsLink: '/docs/getting-started',
    docsLabel: 'See build optimizer guide',
    stats: [
      { num: '593', label: 'Parts' },
      { num: '20', label: 'Categories' },
      { num: '₹100', label: 'Budget granularity' },
    ],
    readout: {
      title: 'roi.ledger',
      log: [
        'knapsack dp armed · ₹100 buckets',
        'exclusive groups: exhaust ×1 · ecu ×1',
        'best build found · within budget',
      ],
      value: '-0.832',
      unit: 's ΔET',
      valueLabel: 'akrapovič full system · hayabusa',
      bars: [
        { label: 'exhaust', pct: 88 },
        { label: 'ecu flash', pct: 66 },
        { label: 'air filter', pct: 38 },
      ],
    },
  },
  {
    id: 'calibration',
    icon: Upload,
    label: '03 / Calibration',
    title: <>Import <span className="text-accent">real</span> run data</>,
    subtitle: 'Dragy GPS logs and dyno sheets. Overlay your real runs against the sim and see exactly where prediction and reality diverge.',
    body: `Physics is only as good as its inputs. MotoQuant accepts two data sources:

Dragy GPS logs (CSV, JSON, or RaceChrono VBO-derived exports) — the importer detects run boundaries, finds the staged position, integrates v(t) to distance, and interpolates ET at exactly 402.336 m with sub-sample accuracy. The best-run selector removes outliers from multi-run files.

Dyno sheets (DynoJet CSV, generic metric CSV, MoTeC tab-delimited) with full SAE J1349 atmospheric correction so power figures are apples-to-apples regardless of dyno location.

Once a real run is imported, the sim-overlay compare lines your Dragy trace up against the simulated run for the same bike and venue: ET and trap-speed error, split-by-split deltas at every standard mark, and the v(t) residual — so you can see whether the gap is in your launch, your shifts, or your top-end pull, and tune the setup that actually matches your bike.`,
    docsLink: '/docs/getting-started',
    docsLabel: 'Calibration walkthrough',
    stats: [
      { num: '2', label: 'Data sources' },
      { num: 'J1349', label: 'SAE dyno correction' },
      { num: '10 Hz', label: 'Dragy GPS rate' },
    ],
    readout: {
      title: 'dragy.import',
      log: [
        'run boundary detected · staged',
        'v(t) integrated · 10 hz gps',
        'et interpolated at the beam',
      ],
      value: '402.336',
      unit: 'm',
      valueLabel: 'quarter mile · sub-sample accuracy',
      bars: [
        { label: 'gps fix', pct: 92 },
        { label: 'sim overlay', pct: 71 },
        { label: 'split match', pct: 64 },
      ],
    },
  },
  {
    id: 'roi',
    icon: TrendingUp,
    label: '04 / ROI & Optimization',
    title: <>Budget-aware build <span className="text-accent">optimization</span></>,
    subtitle: 'Surrogate-accelerated build optimizer. Compatibility-filtered candidates. Budget-aware to ₹100.',
    body: `Beyond the parts catalog, MotoQuant ships a full optimization stack:

The Build Optimizer scores candidate builds through a trained surrogate (R² > 0.99 against the full RK4 sim) and transparently falls back to full simulation whenever a build leaves the surrogate's training envelope — then verifies the winning build with a real sim. Candidates are compatibility-filtered for your bike, and the knapsack enforces exclusivity so it never stacks two exhausts or two ECUs.

ECU Autotune is a conditions-aware setup advisor: it sweeps gearing and launch RPM on the full simulator under your venue's actual air density, and adds tyre-pressure and fuel-trim guidance. The Outlaw pipeline chains it all — drag-prep rubber, a no-limit full-race build, then autotune on the modified bike.

The Smart Recommendations engine wraps the knapsack with synergy detection: if you've selected an exhaust, it weights ECU flashes higher because the pair delivers super-linear gains. Compatibility rules block physically nonsensical combinations (dual exhausts, stacked ECUs).

Natural language queries — "optimize my Hayabusa for 35°C at Aamby Valley, budget ₹50k" — resolve against the live catalog and return a full recommendation set.`,
    docsLink: '/docs/physics',
    docsLabel: 'How the optimizer works',
    stats: [
      { num: '4', label: 'Optimization tools' },
      { num: '₹100', label: 'Budget granularity' },
      { num: 'R² > 0.99', label: 'Surrogate accuracy' },
    ],
    readout: {
      title: 'optimizer.trace',
      log: [
        'candidates compatibility-filtered',
        'surrogate scoring · full-sim fallback',
        'best build verified · full rk4',
      ],
      value: '0.99',
      unit: 'R²',
      valueLabel: 'surrogate vs full rk4 sim',
      bars: [
        { label: 'power', pct: 81 },
        { label: 'mass', pct: 57 },
        { label: 'aero cd', pct: 44 },
      ],
    },
  },
  {
    id: 'api',
    icon: Code2,
    label: '05 / REST API',
    title: <>Open <span className="text-accent">REST API</span></>,
    subtitle: 'FastAPI. Full timeseries. CORS-open for web integrations.',
    body: `Every feature the web UI uses is accessible via the public REST API hosted at motoquant-api.onrender.com.

POST /api/simulate — full simulation returning complete v(t), RPM, gear, acceleration, and ET. Typical latency 80–150 ms.
POST /api/simulate/quick — ET + trap speed + splits only, ~50 ms. Used by the slider-driven BuildPage.
POST /api/simulate/compare — A-vs-B comparison, returns both timeseries with delta ET/trap and cost-to-tenth.
POST /api/calibrate/dragy — upload a Dragy CSV and get run-boundary detection + best-run ET/trap/splits, with optional sim overlay.
POST /api/calibrate/dyno — upload a dyno CSV and get the corrected torque curve ready for injection.
GET /api/bikes — paginated catalog with manufacturer/category filters.
GET /api/venues — all 20 venues with 12-month seasonal weather data.

Interactive docs at /docs (FastAPI's automatic OpenAPI UI). No authentication for basic simulation — rate-limited to 60 requests/minute per IP. Authenticated API keys (email to request) unlock higher limits and private run storage.`,
    docsLink: '/docs/getting-started',
    docsLabel: 'API reference',
    stats: [
      { num: '12', label: 'Endpoints' },
      { num: '~100ms', label: 'Full sim latency' },
      { num: '60/min', label: 'Rate limit' },
    ],
    readout: {
      title: 'api.monitor',
      log: [
        'post /api/simulate/quick · 200 ok',
        'p50 latency steady · warm engine',
        'cors open · 60 req/min per ip',
      ],
      value: '50',
      unit: 'ms',
      valueLabel: 'quick sim · warm response',
      bars: [
        { label: 'uptime', pct: 99 },
        { label: 'p50', pct: 34 },
        { label: 'p95', pct: 58 },
      ],
    },
  },
  {
    id: 'accounts',
    icon: UserCircle2,
    label: '06 / Accounts & Garage',
    title: <>Your <span className="text-accent">garage</span>, saved</>,
    subtitle: 'Free accounts. Shareable builds. 30 free sims a day — Pro unlocks the rest.',
    body: `Create a free account with an email + password (or a passwordless magic link) and your simulator work stops being throwaway: every run you save lands in My Garage on your account page — bike, build, ET, trap speed, venue, date.

Found a setup worth bragging about? Hit Share on the simulator and send a link that reopens your exact bike, venue and tuning sliders on any device.

The Free tier gives every account 30 full simulations a day across the entire 541-bike catalog — no card required. Pro (₹499/mo) adds unlimited sims, the build optimiser, parts ROI and saved runs; Studio (₹1,999/mo) adds Dragy GPS import and dyno calibration.`,
    docsLink: '/login?signup=1',
    docsLabel: 'Create a free account',
    stats: [
      { num: '30', label: 'Free sims per day' },
      { num: '25+', label: 'Runs in your garage' },
      { num: '1-tap', label: 'Build sharing' },
    ],
    readout: {
      title: 'garage.sync',
      log: [
        'run saved → my garage',
        'share link armed · ?bike&venue&rider',
        'free tier: 30 sims/day',
      ],
      value: '9.62',
      unit: 's',
      valueLabel: 'best saved et · clean run',
      bars: [
        { label: 'runs', pct: 74 },
        { label: 'builds', pct: 52 },
        { label: 'shares', pct: 31 },
      ],
    },
  },
];

/* ── Mock instrument readout panel — replaces the old "Screenshot coming
      soon" placeholder with a self-contained readout. Pure JSX/CSS:
      timeslip surface + ruled log lines + one big mono figure + static
      readout bars. Zero new deps, zero network cost.
      HONESTY: these are illustrative compositions (the headline figures
      are real — e.g. the K5 9.9331s reference ET — but the bars and log
      lines are staged), so the panel says so instead of claiming "live". ── */
function FeatureReadout({ readout }) {
  return (
    <div className="timeslip">
      {/* slip header */}
      <div className="flex items-center justify-between pb-2.5 border-b border-dashed border-white/10">
        <span className="label-mono">
          {readout.title}
        </span>
        <span className="chip">demo</span>
      </div>

      <div className="pt-4">
        {/* engine-log lines */}
        <div className="space-y-1.5 font-mono text-[11px] leading-relaxed" aria-hidden="true">
          {readout.log.map((line, i) => (
            <div key={i} className="text-white/40">
              <span className="text-white/25">//&nbsp;</span>
              {line}
            </div>
          ))}
        </div>

        {/* headline mono figure */}
        <div className="mt-5 flex items-end gap-2">
          <ScoreboardDigits value={readout.value} h={34} label={`${readout.value} ${readout.unit}`} />
          <span className="font-mono text-xs text-white/40 mb-0.5">{readout.unit}</span>
        </div>
        <div className="label-mono mt-1.5">
          {readout.valueLabel}
        </div>

        {/* static readout bars */}
        <div className="mt-5 space-y-2">
          {readout.bars.map((b) => (
            <div key={b.label} className="flex items-center gap-3">
              <span className="w-20 shrink-0 font-mono text-[9px] uppercase tracking-[0.18em] text-white/35">
                {b.label}
              </span>
              <span className="flex-1 h-1 rounded-full bg-white/5 overflow-hidden">
                <span
                  className="block h-full rounded-full bg-white/30"
                  style={{ width: `${b.pct}%` }}
                />
              </span>
              <span className="w-8 shrink-0 text-right font-mono text-[9px] tabular-nums text-white/35">
                {b.pct}
              </span>
            </div>
          ))}
        </div>

        {/* honesty caption — this panel is a composition, not a live feed */}
        <div className="label-mono mt-5 text-white/30">
          illustrative readout — try the real thing in the simulator
        </div>
      </div>
    </div>
  );
}

export default function FeaturesPage() {
  return (
    <div className="min-h-screen bg-asphalt-0 text-white overflow-x-hidden">
      <SiteNav />

      {/* Hero — IGNITION v5 voice */}
      <PageHero
        kicker="15 submodels · capability index"
        badge="Full feature list"
        title={<>Everything inside <span className="text-gradient-orange">MotoQuant Pro</span></>}
        sub="Six capability areas — from first-principles physics through to an open REST API and your saved garage. Every layer is built on the same validated simulation engine."
        stats={[
          { value: 15, label: 'Sub-models' },
          { value: 593, label: 'Parts' },
          { value: 250, label: 'Benchmarks' },
        ]}
      >
        {/* Quick-jump nav */}
        <Reveal y={10} duration={0.5} delay={0.28}>
          <div className="mt-4 flex flex-wrap gap-2">
            {FEATURES.map(f => (
              <a
                key={f.id}
                href={`#${f.id}`}
                className="btn-ghost btn-sm"
              >
                {f.label.split(' / ')[1]}
              </a>
            ))}
          </div>
        </Reveal>
      </PageHero>

      {/* Feature sections */}
      <div className="max-w-6xl mx-auto px-6">
        {FEATURES.map((feature, idx) => {
          const Icon = feature.icon;
          const isEven = idx % 2 === 0;
          return (
            <Reveal key={feature.id}>
              <section
                id={feature.id}
                className={`py-16 md:py-24 border-b border-white/5 ${idx === FEATURES.length - 1 ? 'border-none' : ''}`}
              >
                <div className={`grid md:grid-cols-2 gap-12 md:gap-16 items-start ${isEven ? '' : 'md:[&>*:first-child]:order-2'}`}>
                  {/* Text side */}
                  <div>
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-10 h-10 rounded-lg bg-asphalt-2 border border-white/[0.08] flex items-center justify-center">
                        <Icon size={20} className="text-white/70" />
                      </div>
                      <span className="label-mono">{feature.label}</span>
                    </div>
                    <h2 className="font-display font-bold text-3xl md:text-4xl tracking-tight mb-3 text-white">
                      {feature.title}
                    </h2>
                    <p className="text-white/65 font-mono text-sm mb-6 leading-relaxed">
                      {feature.subtitle}
                    </p>
                    <div className="prose prose-sm prose-invert max-w-none">
                      {feature.body.split('\n\n').map((para, i) => (
                        <p key={i} className="text-white/65 text-sm leading-relaxed mb-4">{para}</p>
                      ))}
                    </div>
                    <a
                      href={feature.docsLink}
                      className="inline-flex items-center gap-1.5 mt-4 text-sm text-accent font-mono hover:text-accent-bright transition-colors"
                    >
                      {feature.docsLabel} <ArrowRight size={14} />
                    </a>
                  </div>

                  {/* Instrument side */}
                  <div className="space-y-4">
                    {/* Stats row — mono readout cards */}
                    <div className="grid grid-cols-3 gap-3">
                      {feature.stats.map((s, i) => (
                        <div key={i} className="card p-4 text-center">
                          <div className="font-mono font-bold text-xl text-white tabular-nums">{s.num}</div>
                          <div className="label-mono mt-1">{s.label}</div>
                        </div>
                      ))}
                    </div>
                    {/* Mock instrument readout */}
                    <FeatureReadout readout={feature.readout} />
                  </div>
                </div>
              </section>
            </Reveal>
          );
        })}
      </div>

      {/* Bottom CTA — EXP-008: variant-aware via ?variant=B */}
      <section className="py-16 md:py-24 px-6 border-t border-white/5 bg-asphalt-1/30">
        <Reveal>
          <BottomCta />
        </Reveal>
      </section>

      <SiteFooter />
    </div>
  );
}
