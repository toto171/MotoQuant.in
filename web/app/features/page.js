'use client';

import Link from 'next/link';
import {
  Cpu, BarChart3, Upload, TrendingUp, Monitor, Code2,
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
    title: 'First-Principles Simulation',
    subtitle: '15 independent sub-models. No curve-fitting. Every coefficient traceable to a physical measurement.',
    body: `MotoQuant's physics engine integrates 15 coupled differential equations at a 1 ms timestep using a fixed-step RK4 integrator (with an optional adaptive solver). Unlike spreadsheet calculators that treat power-to-weight ratio as the only variable, MotoQuant models:

Pacejka tire model with thermal evolution, so grip changes as the tyre heats. Aerodynamic drag with a per-bike Cd×A (0.308–0.68 m²) — no two bikes share the same number. Gear shifting and clutch engagement dynamics including slipper clutch behaviour. Forced induction — turbo lag, supercharger mechanical loss, nitrous injection windows. Engine inertia and parasitic losses (alternator, oil pump, water pump, valvetrain).

The adaptive-dt solver is especially useful for identifying the precise clutch engagement window that produces the minimum 60-ft time. Reference baselines — GSX-R 1000 K5 at 10.033s, R1 at 10.286s, Hayabusa Gen1 at 10.471s — are all within 0.001s of published Cycle World and Sport Rider timeslips.`,
    docsLink: '/docs/physics',
    docsLabel: 'Read the physics whitepaper',
    stats: [
      { num: '15', label: 'Sub-models' },
      { num: '1 ms', label: 'Timestep' },
      { num: '976', label: 'Regression tests' },
    ],
    readout: {
      title: 'engine.telemetry',
      log: [
        'rk4 step 1 ms · 15 submodels coupled',
        'pacejka thermal · aero midpoint re-eval',
        'baseline lock: k5 / r1 / hayabusa Δ 0.0000',
      ],
      value: '10.0334',
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
    title: 'Parts ROI Before You Buy',
    subtitle: '563 parts. Cost-per-tenth ranking. Budget-constrained knapsack optimiser.',
    body: `The parts catalog covers 563 upgrades across 20 categories — exhausts, ECU flashes, forced induction kits, slipper clutches, suspension, brakes, wheelie bars. Every part has a physics-accurate parameter delta: an Akrapovič slip-on doesn't add a round number of horsepower, it shifts the entire torque curve.

The ROI engine runs a 0/1 knapsack DP at ₹100 bucket resolution across any compatible parts set. Tell it your budget and it finds the combination that minimises your ET. The cost-per-tenth column tells you how many rupees you're paying per 0.1 second of ET gain — the clearest way to compare a ₹15,000 exhaust against a ₹60,000 turbo kit.

Build profiles — Street Legal, Drag Prep, Full Race — pre-filter the catalog so you don't accidentally spec a nitrous kit onto a street-registered bike.`,
    docsLink: '/docs/getting-started',
    docsLabel: 'See build optimizer guide',
    stats: [
      { num: '563', label: 'Parts' },
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
    title: 'Import Real Run Data',
    subtitle: 'Dragy GPS, dyno sheets, ECU logs. Auto-calibrate Cd and μ to match your actual strip times.',
    body: `Physics is only as good as its inputs. MotoQuant accepts three data sources:

Dragy GPS logs (CSV, JSON, or RaceChrono VBO-derived exports) — the importer detects run boundaries, finds the staged position, integrates v(t) to distance, and interpolates ET at exactly 402.336 m with sub-sample accuracy. The best-run selector removes outliers from multi-run files.

Dyno sheets (DynoJet CSV, generic metric CSV, MoTeC tab-delimited) with full SAE J1349 atmospheric correction so power figures are apples-to-apples regardless of dyno location.

ECU logs (Woolich Racing, Power Commander PC-Link, MoTeC i2) with automatic channel mapping and run-window detection from the speed channel.

Once you have a real run imported, the auto-calibrator fits Cd + μ_peak jointly using differential evolution (global) followed by Nelder-Mead refinement (local). The result is a BikeConfig that matches your specific bike, rider, and track surface — not a generic factory spec.`,
    docsLink: '/docs/getting-started',
    docsLabel: 'Calibration walkthrough',
    stats: [
      { num: '3', label: 'Data sources' },
      { num: 'DE + NM', label: 'Optimizer' },
      { num: '<0.2s', label: 'Typical post-cal error' },
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
        { label: 'fit cd', pct: 71 },
        { label: 'fit μ peak', pct: 64 },
      ],
    },
  },
  {
    id: 'roi',
    icon: TrendingUp,
    label: '04 / ROI & Optimization',
    title: 'Bayesian Build Optimization',
    subtitle: 'BoTorch Gaussian-process optimizer. 7-parameter continuous search. Budget-aware.',
    body: `Beyond the parts catalog, MotoQuant ships a full optimization stack:

Sobol global sensitivity analysis quantifies which parameters matter most for your specific bike. On a stock Hayabusa, aero Cd and μ_peak have similar sensitivity. On a built Pulsar NS200, the clutch engagement RPM dominates.

Bayesian optimization (BoTorch) searches a 7-parameter continuous space — power, mass, Cd, frontal area, tire μ, tire pressure, final drive ratio — within a budget constraint. It converges in 30–50 iterations using expected improvement acquisition. No grid search required.

The Smart Recommendations engine wraps the knapsack with synergy detection: if you've selected an exhaust, it weights ECU flashes higher because the pair delivers super-linear gains. Compatibility rules block physically nonsensical combinations (dual exhausts, stacked ECUs).

Natural language queries — "optimize my Hayabusa for 35°C at Aamby Valley, budget ₹50k" — resolve against the live catalog and return a full recommendation set.`,
    docsLink: '/docs/physics',
    docsLabel: 'How the optimizer works',
    stats: [
      { num: '7', label: 'Opt. parameters' },
      { num: '30–50', label: 'Iterations to converge' },
      { num: 'R² > 0.99', label: 'Surrogate accuracy' },
    ],
    readout: {
      title: 'optimizer.trace',
      log: [
        'sobol indices ranked · 14 features',
        'gp acquisition: expected improvement',
        'converged in 37 iterations',
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
    id: 'desktop',
    icon: Monitor,
    label: '05 / Desktop App',
    title: 'Native Desktop — macOS, Windows, Linux',
    subtitle: 'Tauri 2 + React 19. Python physics sidecar. Offline-first. No browser required.',
    body: `The MotoQuant desktop app (currently in closed beta) is a Tauri 2 shell wrapping a React 19 frontend. It spawns a PyInstaller-packaged FastAPI sidecar on an ephemeral port at startup — so you get the full 15-sub-model physics engine locally, with no cloud dependency.

Five pages ship in the current build: Simulate (bike + venue + sliders + 4-panel chart — speed, RPM, g-force, power), Bikes (searchable paginated catalog), Build (parts composer with live ET delta on every toggle), Compare (A-vs-B head-to-head with overlaid v(t) chart), and History (full leaderboard from local DB).

The physics sidecar is the same code that powers the web API — same importer, same gear-ratio library, same 15 sub-models. Results are deterministic across web and desktop.

Desktop beta access is available to tuning shops and racing teams. Contact motoquant@gmail.com to apply.`,
    docsLink: '/docs/getting-started',
    docsLabel: 'Desktop beta access',
    stats: [
      { num: '5', label: 'Pages' },
      { num: 'Offline', label: 'No cloud needed' },
      { num: 'Tauri 2', label: 'Framework' },
    ],
    readout: {
      title: 'sidecar.boot',
      log: [
        'ephemeral port bound · 127.0.0.1',
        'physics sidecar online in 2.4 s',
        'engine online · zero cloud calls',
      ],
      value: '501',
      unit: 'bikes',
      valueLabel: 'full catalog · bundled offline',
      bars: [
        { label: 'local db', pct: 100 },
        { label: 'sim engine', pct: 100 },
        { label: 'cloud dep', pct: 0 },
      ],
    },
  },
  {
    id: 'api',
    icon: Code2,
    label: '06 / REST API',
    title: 'Open REST API',
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
    label: '07 / Accounts & Garage',
    title: 'Your Garage, Saved',
    subtitle: 'Free accounts. Saved runs. Shareable builds. Every Pro feature unlocked during the open beta.',
    body: `Create a free account with an email + password (or a passwordless magic link) and your simulator work stops being throwaway: every run you save lands in My Garage on your account page — bike, build, ET, trap speed, venue, date.

Found a setup worth bragging about? Hit Share on the simulator and send a link that reopens your exact bike, venue and tuning sliders on any device.

While MotoQuant is in open beta, everything in the Pro and Studio tiers — unlimited sims, the build optimiser, ECU autotune, Dragy/dyno imports — is unlocked free for every account. Paid plans only begin at commercial launch, with advance notice.`,
    docsLink: '/login?signup=1',
    docsLabel: 'Create a free account',
    stats: [
      { num: '₹0', label: 'During open beta' },
      { num: '25+', label: 'Runs in your garage' },
      { num: '1-tap', label: 'Build sharing' },
    ],
    readout: {
      title: 'garage.sync',
      log: [
        'run saved → my garage',
        'share link armed · ?bike&venue&rider',
        'open beta: pro tier unlocked',
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

/* ── Mock cockpit readout panel — replaces the old "Screenshot coming
      soon" placeholder with a self-contained instrument view. Pure
      JSX/CSS: terminal header + engine-log lines + one seven-segment
      figure + static readout bars. Zero new deps, zero network cost.
      HONESTY: these are illustrative compositions (the headline figures
      are real — e.g. the K5 10.0334s reference ET — but the bars and log
      lines are staged), so the panel says so instead of claiming "live". ── */
function FeatureReadout({ readout }) {
  return (
    <div className="relative rounded-xl border border-brand-orange/15 bg-ink-1/60 overflow-hidden">
      <span
        aria-hidden="true"
        className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-brand-orange/60 to-transparent"
      />
      {/* terminal header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/5 bg-black/40">
        <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/45">
          {readout.title}
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-white/25" aria-hidden="true" />
          <span className="font-mono text-[9px] uppercase tracking-[0.2em] text-white/40">demo</span>
        </span>
      </div>

      <div className="p-5">
        {/* engine-log lines */}
        <div className="space-y-1.5 font-mono text-[11px] leading-relaxed" aria-hidden="true">
          {readout.log.map((line, i) => (
            <div key={i} className="text-white/40">
              <span className="text-brand-orange/60">//&nbsp;</span>
              {line}
              {i === readout.log.length - 1 && (
                <span className="cc-cursor text-brand-orange/70">_</span>
              )}
            </div>
          ))}
        </div>

        {/* seven-segment figure */}
        <div className="mt-5 flex items-end gap-2">
          <ScoreboardDigits value={readout.value} h={34} label={`${readout.value} ${readout.unit}`} />
          <span className="font-mono text-xs text-white/40 mb-0.5">{readout.unit}</span>
        </div>
        <div className="mt-1.5 font-mono text-[10px] uppercase tracking-[0.25em] text-white/45">
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
                  className="block h-full rounded-full bg-gradient-to-r from-brand-orangeDeep to-brand-orange"
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
    <div className="min-h-screen bg-black text-white overflow-x-hidden">
      <SiteNav />

      {/* Hero — unified cockpit voice */}
      <PageHero
        kicker="15 submodels · capability index"
        badge="Full feature list"
        title={<>Everything inside <span className="text-gradient-orange">MotoQuant Pro</span></>}
        sub="Seven capability areas — from first-principles physics through to a native desktop app, an open REST API, and your saved garage. Every layer is built on the same validated simulation engine."
        stats={[
          { value: 15, label: 'Sub-models' },
          { value: 563, label: 'Parts' },
          { value: 216, label: 'Benchmarks' },
        ]}
        className="border-b border-brand-orange/10"
      >
        {/* Quick-jump nav */}
        <Reveal y={10} duration={0.5} delay={0.28}>
          <div className="mt-4 flex flex-wrap gap-2">
            {FEATURES.map(f => (
              <a
                key={f.id}
                href={`#${f.id}`}
                className="px-3 py-1.5 rounded-full border border-brand-orange/25 bg-brand-orange/5 text-xs font-mono text-brand-orange/80 hover:border-brand-orange hover:text-brand-orange transition-colors"
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
                className={`py-20 md:py-28 border-b border-brand-orange/10 ${idx === FEATURES.length - 1 ? 'border-none' : ''}`}
              >
                <div className={`grid md:grid-cols-2 gap-12 md:gap-16 items-start ${isEven ? '' : 'md:[&>*:first-child]:order-2'}`}>
                  {/* Text side */}
                  <div>
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-10 h-10 rounded-lg bg-brand-orange/10 border border-brand-orange/30 flex items-center justify-center">
                        <Icon size={20} className="text-brand-orange" />
                      </div>
                      <span className="font-mono text-[10px] text-brand-orange/70 uppercase tracking-[0.25em]">{feature.label}</span>
                    </div>
                    <h2 className="font-display font-bold text-3xl md:text-4xl mb-3 text-white leading-tight">
                      {feature.title}
                    </h2>
                    <p className="text-brand-orange/80 font-mono text-sm mb-6 leading-relaxed">
                      {feature.subtitle}
                    </p>
                    <div className="prose prose-sm prose-invert max-w-none">
                      {feature.body.split('\n\n').map((para, i) => (
                        <p key={i} className="text-white/70 text-sm leading-relaxed mb-4">{para}</p>
                      ))}
                    </div>
                    <a
                      href={feature.docsLink}
                      className="inline-flex items-center gap-1.5 mt-4 text-sm text-brand-accent font-mono hover:text-brand-orange transition-colors"
                    >
                      {feature.docsLabel} <ArrowRight size={14} />
                    </a>
                  </div>

                  {/* Instrument side */}
                  <div className="space-y-4">
                    {/* Stats row — cockpit cards */}
                    <div className="grid grid-cols-3 gap-3">
                      {feature.stats.map((s, i) => (
                        <div key={i} className="relative overflow-hidden rounded-xl bg-ink-1/60 p-4 border border-brand-orange/20 text-center">
                          <span
                            aria-hidden="true"
                            className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-brand-orange/50 to-transparent"
                          />
                          <div className="font-display font-bold text-xl text-brand-orange tabular-nums">{s.num}</div>
                          <div className="font-mono text-[10px] text-white/45 uppercase tracking-[0.25em] mt-1">{s.label}</div>
                        </div>
                      ))}
                    </div>
                    {/* Mock cockpit readout */}
                    <FeatureReadout readout={feature.readout} />
                  </div>
                </div>
              </section>
            </Reveal>
          );
        })}
      </div>

      {/* Bottom CTA — EXP-008: variant-aware via ?variant=B */}
      <section className="py-20 md:py-28 px-6 border-t border-brand-orange/10 bg-ink-1/30">
        <Reveal>
          <BottomCta />
        </Reveal>
      </section>

      <SiteFooter />
    </div>
  );
}
