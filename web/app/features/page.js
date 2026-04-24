'use client';

import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import Link from 'next/link';
import {
  Cpu, BarChart3, Upload, TrendingUp, Monitor, Code2,
  ChevronRight, Zap, ArrowRight
} from 'lucide-react';

const SITE_URL = 'https://motoquant.in';

function RevealSection({ children, className = '' }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-80px' });
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 30 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

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
    mockup: null, // TODO: screenshot of sim chart
    stats: [
      { num: '15', label: 'Sub-models' },
      { num: '1 ms', label: 'Timestep' },
      { num: '838', label: 'Regression tests' },
    ],
  },
  {
    id: 'catalog',
    icon: BarChart3,
    label: '02 / Parts Catalog',
    title: 'Parts ROI Before You Buy',
    subtitle: '465 parts. Cost-per-tenth ranking. Budget-constrained knapsack optimiser.',
    body: `The parts catalog covers 465 upgrades across 20 categories — exhausts, ECU flashes, forced induction kits, slipper clutches, suspension, brakes, wheelie bars. Every part has a physics-accurate parameter delta: an Akrapovič slip-on doesn't add a round number of horsepower, it shifts the entire torque curve.

The ROI engine runs a 0/1 knapsack DP at ₹100 bucket resolution across any compatible parts set. Tell it your budget and it finds the combination that minimises your ET. The cost-per-tenth column tells you how many rupees you're paying per 0.1 second of ET gain — the clearest way to compare a ₹15,000 exhaust against a ₹60,000 turbo kit.

Build profiles — Street Legal, Drag Prep, Full Race — pre-filter the catalog so you don't accidentally spec a nitrous kit onto a street-registered bike.`,
    docsLink: '/docs/getting-started',
    docsLabel: 'See build optimizer guide',
    mockup: null, // TODO: screenshot of BuildPage parts list
    stats: [
      { num: '465', label: 'Parts' },
      { num: '20', label: 'Categories' },
      { num: '₹100', label: 'Budget granularity' },
    ],
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
    mockup: null, // TODO: screenshot of overlay chart
    stats: [
      { num: '3', label: 'Data sources' },
      { num: 'DE + NM', label: 'Optimizer' },
      { num: '<0.2s', label: 'Typical post-cal error' },
    ],
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
    mockup: null, // TODO: screenshot of ROI table
    stats: [
      { num: '7', label: 'Opt. parameters' },
      { num: '30–50', label: 'Iterations to converge' },
      { num: 'R² > 0.99', label: 'Surrogate accuracy' },
    ],
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

Desktop beta access is available to tuning shops and racing teams. Contact hello@motoquant.in to apply.`,
    docsLink: '/docs/getting-started',
    docsLabel: 'Desktop beta access',
    mockup: null, // TODO: screenshot of desktop app
    stats: [
      { num: '5', label: 'Pages' },
      { num: 'Offline', label: 'No cloud needed' },
      { num: 'Tauri 2', label: 'Framework' },
    ],
  },
  {
    id: 'api',
    icon: Code2,
    label: '06 / REST API',
    title: 'Open REST API',
    subtitle: 'FastAPI. Full timeseries. CORS-open for web integrations.',
    body: `Every feature the web UI uses is accessible via the public REST API hosted at web-production-de6eb.up.railway.app.

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
    mockup: null, // TODO: screenshot of OpenAPI docs
    stats: [
      { num: '12', label: 'Endpoints' },
      { num: '~100ms', label: 'Full sim latency' },
      { num: '60/min', label: 'Rate limit' },
    ],
  },
];

export default function FeaturesPage() {
  return (
    <div className="min-h-screen bg-ink-0 text-white overflow-x-hidden">
      {/* Nav */}
      <nav className="fixed top-0 inset-x-0 h-16 backdrop-blur bg-black/80 border-b border-brand-orange/10 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-full flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="text-xl font-display font-bold tracking-tight">
              <span className="text-gradient-orange">Moto</span>
              <span>Quant</span>
            </div>
            <div className="ml-2 px-2 py-1 rounded text-xs font-mono font-semibold text-brand-accent border border-brand-accent/30 bg-brand-accent/5">
              Pro
            </div>
          </Link>
          <div className="hidden md:flex gap-6 items-center text-sm font-mono">
            <Link href="/simulator" className="text-white/60 hover:text-white transition-colors">Simulator</Link>
            <Link href="/bikes" className="text-white/60 hover:text-white transition-colors">Bikes</Link>
            <Link href="/features" className="text-brand-orange">Features</Link>
            <Link href="/docs/getting-started" className="text-white/60 hover:text-white transition-colors">Docs</Link>
            <Link href="/blog" className="text-white/60 hover:text-white transition-colors">Blog</Link>
            <Link href="/pricing" className="text-white/60 hover:text-white transition-colors">Pricing</Link>
          </div>
          <Link
            href="/simulator"
            className="px-4 py-2 bg-brand-orange text-black font-display font-bold rounded-lg text-sm hover:bg-brand-orangeLight transition-colors"
          >
            Try free
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-20 px-6 text-center border-b border-brand-orange/10">
        <div className="max-w-3xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mb-4 inline-block px-4 py-1.5 rounded-full border border-brand-orange/40 bg-brand-orange/10 text-xs font-mono text-brand-orange uppercase tracking-widest"
          >
            Full feature list
          </motion.div>
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="font-display font-bold text-5xl md:text-6xl mb-6 tracking-tighter text-gradient-orange"
          >
            Everything inside MotoQuant Pro
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-white/70 text-lg max-w-2xl mx-auto leading-relaxed"
          >
            Six capability areas — from first-principles physics through to a native desktop app and open REST API.
            Every layer is built on the same validated simulation engine.
          </motion.p>

          {/* Quick-jump nav */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.35 }}
            className="mt-10 flex flex-wrap justify-center gap-2"
          >
            {FEATURES.map(f => (
              <a
                key={f.id}
                href={`#${f.id}`}
                className="px-3 py-1.5 rounded-full border border-brand-orange/25 bg-brand-orange/5 text-xs font-mono text-brand-orange/80 hover:border-brand-orange hover:text-brand-orange transition-colors"
              >
                {f.label.split(' / ')[1]}
              </a>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Feature sections */}
      <div className="max-w-6xl mx-auto px-6">
        {FEATURES.map((feature, idx) => {
          const Icon = feature.icon;
          const isEven = idx % 2 === 0;
          return (
            <RevealSection key={feature.id}>
              <section
                id={feature.id}
                className={`py-24 md:py-28 border-b border-brand-orange/10 ${idx === FEATURES.length - 1 ? 'border-none' : ''}`}
              >
                <div className={`grid md:grid-cols-2 gap-12 md:gap-16 items-start ${isEven ? '' : 'md:[&>*:first-child]:order-2'}`}>
                  {/* Text side */}
                  <div>
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-10 h-10 rounded-lg bg-brand-orange/10 border border-brand-orange/30 flex items-center justify-center">
                        <Icon size={20} className="text-brand-orange" />
                      </div>
                      <span className="font-mono text-xs text-brand-orange/70 uppercase tracking-widest">{feature.label}</span>
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

                  {/* Visual side */}
                  <div className="space-y-4">
                    {/* Stats row */}
                    <div className="grid grid-cols-3 gap-3">
                      {feature.stats.map((s, i) => (
                        <div key={i} className="glass rounded-xl p-4 border border-brand-orange/20 text-center">
                          <div className="font-display font-bold text-xl text-brand-orange tabular-nums">{s.num}</div>
                          <div className="font-mono text-[10px] text-white/50 uppercase tracking-wide mt-1">{s.label}</div>
                        </div>
                      ))}
                    </div>
                    {/* Screenshot placeholder */}
                    <div className="glass rounded-xl border border-brand-orange/15 overflow-hidden aspect-video flex items-center justify-center bg-ink-1/60">
                      {feature.mockup ? (
                        <img src={feature.mockup} alt={`${feature.title} screenshot`} className="w-full h-full object-cover" />
                      ) : (
                        <div className="text-center">
                          <Icon size={32} className="text-brand-orange/20 mx-auto mb-2" />
                          <p className="text-xs font-mono text-white/20">
                            {/* TODO: add screenshot before launch */}
                            Screenshot coming soon
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </section>
            </RevealSection>
          );
        })}
      </div>

      {/* Bottom CTA */}
      <section className="py-24 px-6 border-t border-brand-orange/10 bg-ink-1/30">
        <div className="max-w-3xl mx-auto text-center">
          <RevealSection>
            <h2 className="font-display font-bold text-4xl mb-4 text-white">Ready to run your first sim?</h2>
            <p className="text-white/60 mb-10 text-lg">Free in the browser. No account required to start.</p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/simulator"
                className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-brand-orange text-black font-display font-bold rounded-lg glow-orange text-base hover:bg-brand-orangeLight transition-colors"
              >
                <Zap size={18} /> Try it free
              </Link>
              <Link
                href="/pricing"
                className="inline-flex items-center justify-center gap-2 px-8 py-4 border-2 border-brand-orange text-brand-orange font-display font-bold rounded-lg transition-colors text-base"
              >
                See pricing
              </Link>
            </div>
          </RevealSection>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-brand-orange/10 py-8 px-6 text-center text-white/40 text-xs font-mono">
        <p>© {new Date().getFullYear()} MotoQuant Pro · <Link href="/" className="hover:text-brand-orange transition-colors">motoquant.in</Link></p>
      </footer>
    </div>
  );
}
