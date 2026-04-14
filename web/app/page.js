import { Zap, TrendingUp, BarChart3, Github, ExternalLink, ArrowRight, CheckCircle2, Gauge, Wind, Activity } from 'lucide-react';
import SimulatorWidget from '../components/SimulatorWidget';

const STREAMLIT_URL = process.env.NEXT_PUBLIC_STREAMLIT_URL || 'https://app.motoquant.in';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-[#080808] text-white antialiased">

      {/* ── Nav ─────────────────────────────────────────────────────── */}
      <nav className="border-b border-white/8 sticky top-0 bg-[#080808]/90 backdrop-blur-xl z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="text-xl font-bold tracking-tight">
            <span className="text-orange-500">Moto</span><span className="text-white">Quant</span>
            <span className="text-white/40 font-normal ml-1 text-sm">Pro</span>
          </div>
          <div className="flex gap-5 items-center text-sm">
            <a href="#simulator" className="text-white/60 hover:text-white transition-colors hidden sm:block">Simulator</a>
            <a href="#physics"   className="text-white/60 hover:text-white transition-colors hidden sm:block">Physics</a>
            <a href="#validation" className="text-white/60 hover:text-white transition-colors hidden sm:block">Validation</a>
            <a
              href={STREAMLIT_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-4 py-1.5 bg-orange-500/10 border border-orange-500/40 text-orange-400 hover:bg-orange-500/20 hover:border-orange-500/70 rounded-full text-sm font-medium transition-all"
            >
              Run Simulations <ExternalLink size={13} />
            </a>
            <a href="https://github.com/da25mem5s02-debug/MotoQuant_v1" target="_blank" rel="noopener noreferrer" className="text-white/40 hover:text-white/80 transition-colors">
              <Github size={18} />
            </a>
          </div>
        </div>
      </nav>

      {/* ── Hero ─────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden">
        {/* Grid background */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(to_right,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:64px_64px]" />
        {/* Orange glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-orange-600/15 rounded-full blur-3xl pointer-events-none" />

        <div className="relative max-w-6xl mx-auto px-6 pt-24 pb-20 text-center">
          {/* Badge */}
          <div className="mb-6 inline-flex items-center gap-2 px-4 py-1.5 bg-white/5 border border-white/10 rounded-full text-white/60 text-xs font-medium tracking-wide uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-orange-400 animate-pulse inline-block" />
            Open Source · First-Principles Physics Engine
          </div>

          {/* Headline */}
          <h1 className="text-5xl sm:text-7xl font-black mb-6 leading-[1.05] tracking-tight">
            The Physics<br />
            of{' '}
            <span className="bg-gradient-to-r from-orange-400 to-orange-600 bg-clip-text text-transparent">
              Faster
            </span>
          </h1>

          <p className="text-lg sm:text-xl text-white/50 max-w-2xl mx-auto mb-3 leading-relaxed">
            First-principles quarter-mile simulation. Predict ET, optimise your build,
            and understand what actually moves the needle on the strip.
          </p>
          <p className="text-sm text-white/30 mb-10">
            Built for the Indian drag racing community · Validated at Aamby Valley, MMRT, BIC
          </p>

          {/* CTAs */}
          <div className="flex flex-wrap gap-3 justify-center">
            <a
              href={STREAMLIT_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-7 py-3 bg-orange-600 hover:bg-orange-500 rounded-xl font-semibold transition-all shadow-lg shadow-orange-900/40 hover:shadow-orange-700/50 text-sm"
            >
              <Gauge size={16} /> Run Simulations
            </a>
            <a
              href="#simulator"
              className="inline-flex items-center gap-2 px-7 py-3 bg-white/6 hover:bg-white/10 border border-white/10 hover:border-white/20 rounded-xl font-semibold transition-all text-sm text-white/80"
            >
              Try Live Preview
            </a>
            <a
              href="https://github.com/da25mem5s02-debug/MotoQuant_v1"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-7 py-3 bg-white/6 hover:bg-white/10 border border-white/10 hover:border-white/20 rounded-xl font-semibold transition-all text-sm text-white/80"
            >
              <Github size={15} /> GitHub
            </a>
          </div>

          {/* Quick stats strip */}
          <div className="mt-16 inline-grid grid-cols-4 divide-x divide-white/8 border border-white/8 rounded-2xl bg-white/3 backdrop-blur-sm overflow-hidden text-sm">
            {[
              { num: '506', label: 'Tests passing' },
              { num: '108', label: 'Bikes seeded' },
              { num: '15',  label: 'Physics models' },
              { num: '±0.07s', label: 'Validated accuracy' },
            ].map(({ num, label }) => (
              <div key={label} className="px-6 py-4 text-center">
                <div className="font-bold text-orange-400 text-lg">{num}</div>
                <div className="text-white/40 text-xs mt-0.5">{label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Streamlit App Callout ─────────────────────────────────────── */}
      <section className="border-t border-white/8 bg-gradient-to-r from-orange-950/40 via-orange-900/20 to-orange-950/40">
        <div className="max-w-6xl mx-auto px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <p className="text-white font-semibold mb-0.5">Want the full simulation experience?</p>
            <p className="text-white/50 text-sm">
              Parts ROI analysis · Sobol sensitivity · Dyno & ECU import · Build optimiser
            </p>
          </div>
          <a
            href={STREAMLIT_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-shrink-0 inline-flex items-center gap-2 px-6 py-2.5 bg-orange-600 hover:bg-orange-500 rounded-xl font-semibold text-sm transition-all shadow-lg shadow-orange-900/30"
          >
            Open Simulation App <ArrowRight size={15} />
          </a>
        </div>
      </section>

      {/* ── Live Preview Widget ───────────────────────────────────────── */}
      <section id="simulator" className="border-t border-white/8 py-24">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-10">
            <p className="text-xs font-semibold uppercase tracking-widest text-orange-500 mb-3">Live Preview</p>
            <h2 className="text-3xl font-bold mb-3">Quick Quarter-Mile Calculator</h2>
            <p className="text-white/50 max-w-lg mx-auto text-sm leading-relaxed">
              Pick a bike and get an ET estimate in under a second. For full simulation — parts ROI, dyno import, and build optimisation — open the app.
            </p>
          </div>
          <SimulatorWidget />
          <div className="mt-8 text-center">
            <a
              href={STREAMLIT_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-sm text-orange-400 hover:text-orange-300 transition-colors group"
            >
              Open the full simulation app for parts ROI, Sobol analysis & ECU import
              <ArrowRight size={14} className="group-hover:translate-x-0.5 transition-transform" />
            </a>
          </div>
        </div>
      </section>

      {/* ── Validation ───────────────────────────────────────────────── */}
      <section id="validation" className="border-t border-white/8 py-24 bg-white/[0.02]">
        <div className="max-w-6xl mx-auto px-6">
          <p className="text-xs font-semibold uppercase tracking-widest text-orange-500 mb-3">Ground Truth</p>
          <h2 className="text-3xl font-bold mb-3">Validated on Real Data</h2>
          <p className="text-white/50 mb-12 max-w-xl text-sm leading-relaxed">
            Our 15-submodel physics engine is tested against real drag telemetry and dyno data at Indian and international strips.
          </p>
          <div className="grid md:grid-cols-3 gap-5">
            {[
              { name: 'Suzuki GSX-R 1000 K5', cc: '1000cc Superbike', target: '9.97s', sim: '10.04s', accuracy: '±0.07s — 0.7%' },
              { name: 'Yamaha YZF-R1 4C8',    cc: '1000cc Superbike', target: '10.2–10.4s', sim: '~10.3s', accuracy: 'In range ✓' },
              { name: 'Suzuki Hayabusa Gen1', cc: '1300cc Hyperbike', target: '10.1–10.7s', sim: 'In range', accuracy: 'Validated ✓' },
            ].map((bike) => (
              <div key={bike.name} className="bg-white/5 backdrop-blur-md border border-white/8 rounded-2xl p-7 hover:border-orange-500/30 transition-colors">
                <div className="flex items-start justify-between mb-5">
                  <div>
                    <h3 className="font-semibold text-sm">{bike.name}</h3>
                    <p className="text-white/40 text-xs mt-0.5">{bike.cc}</p>
                  </div>
                  <CheckCircle2 size={18} className="text-green-500 mt-0.5 flex-shrink-0" />
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between items-baseline">
                    <span className="text-xs text-white/40">Target ET</span>
                    <span className="text-xl font-bold text-orange-400">{bike.target}</span>
                  </div>
                  <div className="flex justify-between items-baseline">
                    <span className="text-xs text-white/40">Simulated ET</span>
                    <span className="text-xl font-bold">{bike.sim}</span>
                  </div>
                  <div className="border-t border-white/8 pt-3">
                    <span className="text-xs font-semibold text-green-400">{bike.accuracy}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Physics sub-models ───────────────────────────────────────── */}
      <section id="physics" className="border-t border-white/8 py-24">
        <div className="max-w-6xl mx-auto px-6">
          <p className="text-xs font-semibold uppercase tracking-widest text-orange-500 mb-3">Under the Hood</p>
          <h2 className="text-3xl font-bold mb-12">15 Physics Sub-Models</h2>
          <div className="grid md:grid-cols-2 gap-5">
            {[
              {
                icon: <Zap size={18} />,
                title: 'Engine & Drivetrain',
                items: ['3D engine torque curves (Willans friction model)', 'Forced induction — turbo, supercharger, nitrous', 'Gear shifting and clutch engagement dynamics', 'Chain drive losses and sprocket ratios'],
              },
              {
                icon: <Wind size={18} />,
                title: 'Aerodynamics & Grip',
                items: ['Drag coefficient and frontal area per-model', 'Tire slip dynamics (Pacejka + thermal model)', 'Weight transfer and traction limits', 'Rider CoG shift and wheelie physics'],
              },
              {
                icon: <Activity size={18} />,
                title: 'Environment & Setup',
                items: ['Air density, altitude and temperature correction', 'Rolling resistance and surface grip multipliers', 'Staging, reaction time, two-step launch control', 'Wind and live weather effects'],
              },
              {
                icon: <BarChart3 size={18} />,
                title: 'Integration & Validation',
                items: ['RK4 fixed-step integrator at 1 ms timestep', 'Adaptive step-size solver (RK45)', '506+ passing test cases', 'Validated against real GPS and ECU telemetry'],
              },
            ].map((block) => (
              <div key={block.title} className="bg-white/5 backdrop-blur-md border border-white/8 rounded-2xl p-7 hover:border-orange-500/20 transition-colors">
                <h3 className="text-sm font-semibold mb-4 flex items-center gap-2 text-orange-400">
                  {block.icon} {block.title}
                </h3>
                <ul className="space-y-2 text-white/50 text-sm">
                  {block.items.map((item) => (
                    <li key={item} className="flex items-start gap-2">
                      <span className="text-orange-600 mt-0.5">›</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Stats ────────────────────────────────────────────────────── */}
      <section className="border-t border-white/8 py-24 bg-white/[0.02]">
        <div className="max-w-6xl mx-auto px-6">
          <p className="text-xs font-semibold uppercase tracking-widest text-orange-500 mb-3">The Library</p>
          <h2 className="text-3xl font-bold mb-14">Curated Bike Catalog</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-white/8 rounded-2xl overflow-hidden border border-white/8">
            {[
              { num: '108', label: 'Bikes', note: '17 manufacturers incl. KTM, Bajaj, TVS, RE' },
              { num: '69',  label: 'Tires', note: 'Pacejka + thermal model, 15 brands' },
              { num: '70',  label: 'Parts', note: 'Sprockets, exhaust, ECU flash, nitrous, turbo' },
              { num: '12',  label: 'Venues', note: '5 Indian + 7 international drag strips' },
            ].map((stat) => (
              <div key={stat.label} className="bg-[#080808] p-8 text-center">
                <div className="text-5xl font-black text-orange-400 mb-2 tabular-nums">{stat.num}</div>
                <p className="text-white font-semibold text-sm mb-1">{stat.label}</p>
                <p className="text-white/35 text-xs leading-snug">{stat.note}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────────────────── */}
      <section id="cta" className="border-t border-white/8 py-24">
        <div className="max-w-6xl mx-auto px-6">
          <div className="relative overflow-hidden bg-gradient-to-br from-orange-950/60 via-[#0d0d0d] to-[#0d0d0d] border border-orange-500/20 rounded-3xl p-10 md:p-14">
            {/* Glow */}
            <div className="absolute -top-20 -right-20 w-80 h-80 bg-orange-600/10 rounded-full blur-3xl pointer-events-none" />

            <div className="relative">
              <p className="text-xs font-semibold uppercase tracking-widest text-orange-500 mb-3">Get Started</p>
              <h2 className="text-3xl md:text-4xl font-bold mb-4">Start Simulating Today</h2>
              <p className="text-white/50 mb-10 max-w-xl text-sm leading-relaxed">
                Run the full simulation app, install the CLI, or hit the REST API. Three ways to put first-principles physics to work on your build.
              </p>

              <div className="grid sm:grid-cols-3 gap-4 mb-10">
                {/* Streamlit App */}
                <div className="p-5 bg-orange-500/8 border border-orange-500/30 rounded-2xl">
                  <div className="flex items-center gap-2 mb-2">
                    <Gauge size={15} className="text-orange-400" />
                    <h3 className="font-semibold text-sm text-orange-300">Simulation App</h3>
                  </div>
                  <p className="text-xs text-white/50 mb-4 leading-relaxed">Full GUI. Parts ROI, Sobol analysis, dyno import, build optimiser, leaderboard.</p>
                  <a
                    href={STREAMLIT_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 text-xs font-semibold text-orange-400 hover:text-orange-300 transition-colors"
                  >
                    Open App <ExternalLink size={11} />
                  </a>
                </div>

                {/* CLI */}
                <div className="p-5 bg-white/4 border border-white/8 rounded-2xl">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp size={15} className="text-white/60" />
                    <h3 className="font-semibold text-sm">CLI &amp; Python API</h3>
                  </div>
                  <p className="text-xs text-white/50 mb-4 leading-relaxed">Full simulation from the terminal. Import Dragy GPS, dyno curves, and Woolich ECU logs.</p>
                  <code className="text-xs text-orange-400">pip install motoquant</code>
                </div>

                {/* REST API */}
                <div className="p-5 bg-white/4 border border-white/8 rounded-2xl">
                  <div className="flex items-center gap-2 mb-2">
                    <BarChart3 size={15} className="text-white/60" />
                    <h3 className="font-semibold text-sm">REST API</h3>
                  </div>
                  <p className="text-xs text-white/50 mb-4 leading-relaxed">POST /api/simulate — get full v(t), RPM(t), gear(t) time-series with Pydantic validation.</p>
                  <code className="text-xs text-orange-400">api.motoquant.in/docs</code>
                </div>
              </div>

              <div className="flex gap-3 flex-wrap">
                <a
                  href={STREAMLIT_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-7 py-3 bg-orange-600 hover:bg-orange-500 rounded-xl font-semibold text-sm transition-all shadow-lg shadow-orange-900/40"
                >
                  <Gauge size={16} /> Open Simulation App
                </a>
                <a
                  href="https://github.com/da25mem5s02-debug/MotoQuant_v1"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-7 py-3 border border-orange-500/40 text-orange-400 hover:bg-orange-500/10 rounded-xl font-semibold text-sm transition-all"
                >
                  <Github size={16} /> View on GitHub
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────────── */}
      <footer className="border-t border-white/8 py-10">
        <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row justify-between items-center gap-4 text-sm text-white/30">
          <div>
            <span className="text-orange-500 font-bold">Moto</span>Quant Pro ·{' '}
            <span className="italic">The physics of faster</span>
          </div>
          <div className="flex items-center gap-5">
            <a href={STREAMLIT_URL} target="_blank" rel="noopener noreferrer" className="hover:text-orange-400 transition-colors">Simulation App</a>
            <a href="https://github.com/da25mem5s02-debug/MotoQuant_v1" className="hover:text-orange-400 transition-colors">GitHub</a>
            <span>Built for the Indian drag strip</span>
          </div>
        </div>
      </footer>

    </div>
  );
}
