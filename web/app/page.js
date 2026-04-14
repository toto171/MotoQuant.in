import { Zap, TrendingUp, BarChart3, ArrowRight, CheckCircle2, Wind, Activity, Clock, Gauge } from 'lucide-react';
import SimulatorWidget from '../components/SimulatorWidget';

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
            <a href="#simulator"  className="text-white/60 hover:text-white transition-colors hidden sm:block">Simulator</a>
            <a href="#physics"    className="text-white/60 hover:text-white transition-colors hidden sm:block">Physics</a>
            <a href="#validation" className="text-white/60 hover:text-white transition-colors hidden sm:block">Validation</a>
            <span className="inline-flex items-center gap-1.5 px-4 py-1.5 bg-white/4 border border-white/10 text-white/30 rounded-full text-sm cursor-default select-none">
              <Clock size={12} /> App Coming Soon
            </span>
          </div>
        </div>
      </nav>

      {/* ── Hero ─────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(to_right,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:64px_64px]" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-orange-600/15 rounded-full blur-3xl pointer-events-none" />

        <div className="relative max-w-6xl mx-auto px-6 pt-24 pb-20 text-center">
          <div className="mb-6 inline-flex items-center gap-2 px-4 py-1.5 bg-white/5 border border-white/10 rounded-full text-white/50 text-xs font-medium tracking-wide uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-orange-400 animate-pulse inline-block" />
            Open Source · First-Principles Physics Engine
          </div>

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

          <div className="flex flex-wrap gap-3 justify-center">
            <a
              href="#simulator"
              className="inline-flex items-center gap-2 px-7 py-3 bg-orange-600 hover:bg-orange-500 rounded-xl font-semibold transition-all shadow-lg shadow-orange-900/40 text-sm"
            >
              <Gauge size={16} /> Try the Simulator
            </a>
            <a
              href="#validation"
              className="inline-flex items-center gap-2 px-7 py-3 bg-white/6 hover:bg-white/10 border border-white/10 hover:border-white/20 rounded-xl font-semibold transition-all text-sm text-white/80"
            >
              View Validation Data
            </a>
          </div>

          {/* Quick stats strip */}
          <div className="mt-16 inline-grid grid-cols-4 divide-x divide-white/8 border border-white/8 rounded-2xl bg-white/3 backdrop-blur-sm overflow-hidden text-sm">
            {[
              { num: '565',   label: 'Tests passing' },
              { num: '108',   label: 'Bikes seeded' },
              { num: '15',    label: 'Physics models' },
              { num: '10',    label: 'Bikes validated' },
            ].map(({ num, label }) => (
              <div key={label} className="px-6 py-4 text-center">
                <div className="font-bold text-orange-400 text-lg">{num}</div>
                <div className="text-white/40 text-xs mt-0.5">{label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Coming Soon Banner ────────────────────────────────────────── */}
      <section className="border-t border-white/8 bg-gradient-to-r from-orange-950/30 via-[#0d0d0d] to-orange-950/30">
        <div className="max-w-6xl mx-auto px-6 py-6 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div>
            <p className="text-white/80 font-semibold text-sm mb-0.5">Full simulation app in development</p>
            <p className="text-white/40 text-xs">
              Parts ROI · Sobol sensitivity · Dyno & ECU import · Build optimiser · Leaderboard
            </p>
          </div>
          <span className="flex-shrink-0 inline-flex items-center gap-2 px-5 py-2 bg-white/5 border border-white/10 rounded-xl text-white/35 text-sm cursor-default select-none">
            <Clock size={14} /> Launching Soon
          </span>
        </div>
      </section>

      {/* ── Simulator Preview ─────────────────────────────────────────── */}
      <section id="simulator" className="border-t border-white/8 py-24">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-10">
            <p className="text-xs font-semibold uppercase tracking-widest text-orange-500 mb-3">Preview</p>
            <h2 className="text-3xl font-bold mb-3">Quarter-Mile Simulator</h2>
            <p className="text-white/50 max-w-lg mx-auto text-sm leading-relaxed">
              The simulator UI is ready — the cloud API backend is finishing deployment.
              Below is an interactive preview of exactly what you'll run.
            </p>
          </div>
          <SimulatorWidget />
        </div>
      </section>

      {/* ── Validation ───────────────────────────────────────────────── */}
      <section id="validation" className="border-t border-white/8 py-24 bg-white/[0.02]">
        <div className="max-w-6xl mx-auto px-6">
          <p className="text-xs font-semibold uppercase tracking-widest text-orange-500 mb-3">Ground Truth</p>
          <h2 className="text-3xl font-bold mb-3">Validated on Real Data</h2>
          <p className="text-white/50 mb-4 max-w-xl text-sm leading-relaxed">
            15-submodel physics engine benchmarked against published quarter-mile data from
            Cycle World, Motorcyclist, MCN, and Indian sources. All runs at ISA standard
            atmosphere — 15 °C, sea level, 75 kg rider.
          </p>

          {/* Summary strip */}
          <div className="flex flex-wrap gap-6 mb-12 text-sm">
            <div><span className="text-orange-400 font-bold text-lg">10</span> <span className="text-white/40">bikes validated</span></div>
            <div><span className="text-green-400 font-bold text-lg">10/10</span> <span className="text-white/40">within ±0.20s of reference</span></div>
            <div><span className="text-green-400 font-bold text-lg">8/10</span> <span className="text-white/40">within ±0.10s</span></div>
            <div><span className="text-orange-400 font-bold text-lg">6</span> <span className="text-white/40">manufacturers</span></div>
          </div>

          {/* Bike grid — 5 col on large, 2 col on small */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {[
              { name: 'Suzuki GSX-R 1000 K5',    cc: '999cc · Superbike',    target: '9.97s',      sim: '10.04s',  delta: '±0.07s' },
              { name: 'Yamaha YZF-R1 4C8',        cc: '998cc · Superbike',    target: '10.2–10.4s', sim: '~10.3s',  delta: 'In range' },
              { name: 'Kawasaki ZX-14R \'12',     cc: '1441cc · Hypersport',  target: '9.91–10.10s',sim: '9.95s',   delta: 'In range' },
              { name: 'Yamaha MT-09 \'21',         cc: '890cc · Naked',        target: '11.22–11.45s',sim: '11.32s', delta: 'In range' },
              { name: 'Kawasaki ZX-10RR \'21',    cc: '998cc · Superbike',    target: '10.28–10.45s',sim: '10.20s', delta: '−0.08s' },
              { name: 'Kawasaki ZZR1400 \'06',    cc: '1352cc · Hypersport',  target: '10.05–10.25s',sim: '10.01s', delta: '−0.04s' },
              { name: 'BMW M1000RR \'21',          cc: '999cc · Superbike',    target: '10.22–10.40s',sim: '10.17s', delta: '−0.05s' },
              { name: 'Honda CBR1000RR-R \'20',   cc: '999cc · Superbike',    target: '10.30–10.50s',sim: '10.23s', delta: '−0.07s' },
              { name: 'Suzuki GSX-R750 K8',       cc: '750cc · Supersport',   target: '10.92–11.12s',sim: '10.85s', delta: '−0.07s' },
              { name: 'RE Continental GT 650',    cc: '648cc · Sport Tourer', target: '14.90–15.50s',sim: '14.88s', delta: '−0.02s' },
            ].map((bike) => (
              <div key={bike.name} className="bg-white/5 backdrop-blur-md border border-white/8 rounded-xl p-4 hover:border-green-500/30 transition-colors">
                <div className="flex items-start justify-between mb-3">
                  <CheckCircle2 size={14} className="text-green-500 flex-shrink-0 mt-0.5" />
                  <span className="text-xs font-bold text-green-400 ml-auto">{bike.delta}</span>
                </div>
                <p className="text-xs font-semibold text-white leading-snug mb-1">{bike.name}</p>
                <p className="text-xs text-white/30 mb-3">{bike.cc}</p>
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-white/30">Ref</span>
                    <span className="text-orange-400 font-medium">{bike.target}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-white/30">Sim</span>
                    <span className="text-white font-medium">{bike.sim}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <p className="mt-6 text-xs text-white/25">
            Sources: Cycle World, Motorcyclist, MCN, Visordown, xBhp, overdrive.in · Validation ongoing — more bikes being added
          </p>
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
                items: ['RK4 fixed-step integrator at 1 ms timestep', 'Adaptive step-size solver (RK45)', '565 passing test cases', 'Validated against real GPS and ECU telemetry'],
              },
            ].map((block) => (
              <div key={block.title} className="bg-white/5 backdrop-blur-md border border-white/8 rounded-2xl p-7 hover:border-orange-500/20 transition-colors">
                <h3 className="text-sm font-semibold mb-4 flex items-center gap-2 text-orange-400">
                  {block.icon} {block.title}
                </h3>
                <ul className="space-y-2 text-white/50 text-sm">
                  {block.items.map((item) => (
                    <li key={item} className="flex items-start gap-2">
                      <span className="text-orange-600 mt-0.5">›</span> {item}
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
              { num: '108', label: 'Bikes',   note: '17 manufacturers incl. KTM, Bajaj, TVS, RE' },
              { num: '69',  label: 'Tires',   note: 'Pacejka + thermal model, 15 brands' },
              { num: '70',  label: 'Parts',   note: 'Sprockets, exhaust, ECU flash, nitrous, turbo' },
              { num: '12',  label: 'Venues',  note: '5 Indian + 7 international drag strips' },
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

      {/* ── What's Coming ─────────────────────────────────────────────── */}
      <section id="cta" className="border-t border-white/8 py-24">
        <div className="max-w-6xl mx-auto px-6">
          <div className="relative overflow-hidden bg-gradient-to-br from-orange-950/60 via-[#0d0d0d] to-[#0d0d0d] border border-orange-500/20 rounded-3xl p-10 md:p-14">
            <div className="absolute -top-20 -right-20 w-80 h-80 bg-orange-600/10 rounded-full blur-3xl pointer-events-none" />

            <div className="relative">
              <p className="text-xs font-semibold uppercase tracking-widest text-orange-500 mb-3">Roadmap</p>
              <h2 className="text-3xl md:text-4xl font-bold mb-4">What's Coming</h2>
              <p className="text-white/50 mb-10 max-w-xl text-sm leading-relaxed">
                The physics engine and full bike library are production-ready. The tools below are finishing
                deployment and will go live shortly.
              </p>

              <div className="grid sm:grid-cols-3 gap-4 mb-10">
                {/* Simulation App */}
                <div className="p-5 bg-orange-500/8 border border-orange-500/20 rounded-2xl">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Gauge size={15} className="text-orange-400" />
                      <h3 className="font-semibold text-sm text-orange-300">Simulation App</h3>
                    </div>
                    <span className="text-xs text-orange-500/60 bg-orange-500/10 px-2 py-0.5 rounded-full border border-orange-500/20">Soon</span>
                  </div>
                  <p className="text-xs text-white/50 leading-relaxed">Full GUI — parts ROI, Sobol analysis, dyno import, build optimiser, and leaderboard.</p>
                </div>

                {/* CLI */}
                <div className="p-5 bg-white/4 border border-white/8 rounded-2xl">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <TrendingUp size={15} className="text-white/60" />
                      <h3 className="font-semibold text-sm">CLI & Python API</h3>
                    </div>
                    <span className="text-xs text-white/25 bg-white/5 px-2 py-0.5 rounded-full border border-white/10">Soon</span>
                  </div>
                  <p className="text-xs text-white/50 leading-relaxed">Full simulation from the terminal. Import Dragy GPS, dyno curves, and Woolich ECU logs.</p>
                </div>

                {/* REST API */}
                <div className="p-5 bg-white/4 border border-white/8 rounded-2xl">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <BarChart3 size={15} className="text-white/60" />
                      <h3 className="font-semibold text-sm">REST API</h3>
                    </div>
                    <span className="text-xs text-white/25 bg-white/5 px-2 py-0.5 rounded-full border border-white/10">Soon</span>
                  </div>
                  <p className="text-xs text-white/50 leading-relaxed">POST /api/simulate — get full v(t), RPM(t), gear(t) time-series with Pydantic validation.</p>
                </div>
              </div>

              <div className="flex items-center gap-3 text-sm text-white/40">
                <ArrowRight size={15} className="text-orange-600" />
                In the meantime, explore the validation data and physics model breakdown above.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────────── */}
      <footer className="border-t border-white/8 py-10">
        <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row justify-between items-center gap-4 text-sm text-white/30">
          <div>
            <span className="text-orange-500 font-semibold">Moto</span>Quant Pro ·{' '}
            <span className="italic">The physics of faster</span>
          </div>
          <div className="flex items-center gap-5">
            <span>motoquant.in</span>
            <span>Built for the Indian drag strip</span>
          </div>
        </div>
      </footer>

    </div>
  );
}
