import { Zap, TrendingUp, BarChart3, Github } from 'lucide-react';
import SimulatorWidget from '../components/SimulatorWidget';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-black text-white">

      {/* Nav */}
      <nav className="border-b border-gray-800 sticky top-0 bg-black/95 backdrop-blur z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="text-2xl font-bold tracking-tight">
            <span className="text-orange-500">Moto</span>Quant Pro
          </div>
          <div className="flex gap-6 items-center text-sm">
            <a href="#simulator" className="hover:text-orange-500 transition-colors">Quick Sim</a>
            <a href="/simulator" className="hover:text-orange-500 transition-colors font-semibold text-orange-400">Full Dashboard</a>
            <a href="#physics"   className="hover:text-orange-500 transition-colors">Physics</a>
            <a href="#validation" className="hover:text-orange-500 transition-colors">Validation</a>
            <a href="#cta"       className="hover:text-orange-500 transition-colors">Get Started</a>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 py-20 text-center">
        <div className="mb-6 inline-block px-4 py-2 bg-orange-500/10 border border-orange-500/30 rounded-full text-orange-400 text-sm font-medium">
          Open Source Drag Racing Physics Engine
        </div>
        <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
          The Physics of Faster
        </h1>
        <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-6">
          First-principles physics simulation for quarter-mile drag racing. Predict ET, optimize builds, and understand what actually moves the needle on the strip.
        </p>
        <p className="text-gray-500 text-sm">
          Built for the Indian drag racing community. Validated on real bikes at Aamby Valley, MMRT, and beyond.
        </p>
        <div className="mt-10 flex gap-4 justify-center">
          <a href="/simulator" className="px-6 py-3 bg-orange-600 hover:bg-orange-700 rounded-lg font-semibold transition-colors">
            Open Full Dashboard
          </a>
          <a href="#simulator" className="px-6 py-3 border border-gray-700 hover:border-gray-500 rounded-lg font-semibold transition-colors">
            Quick Simulator
          </a>
          <a href="#physics"
            className="px-6 py-3 border border-gray-700 hover:border-gray-500 rounded-lg font-semibold transition-colors flex items-center gap-2">
            How It Works
          </a>
        </div>
      </section>

      {/* Live Simulator */}
      <section id="simulator" className="bg-gray-950 border-t border-gray-800 py-24">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-3">Live Quarter-Mile Simulator</h2>
            <p className="text-gray-400 max-w-xl mx-auto">
              Real physics, running in the cloud. Pick a bike, adjust your setup, get your ET in under a second.
            </p>
          </div>
          <SimulatorWidget />
        </div>
      </section>

      {/* Validation */}
      <section id="validation" className="border-t border-gray-800 py-24">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-3xl font-bold mb-3">Validated on Real Data</h2>
          <p className="text-gray-400 mb-12 max-w-2xl">
            Our 15-submodel physics engine is tested against real drag racing telemetry and dyno data.
          </p>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { name: 'Suzuki GSX-R 1000 K5', cc: '1000cc Superbike', target: '9.97s', sim: '10.04s', accuracy: '±0.07s (0.7%)', check: true },
              { name: 'Yamaha YZF-R1 4C8',    cc: '1000cc Superbike', target: '10.2–10.4s', sim: '~10.3s', accuracy: 'In-range ✓', check: true },
              { name: 'Suzuki Hayabusa Gen1', cc: '1300cc Hyperbike', target: '10.1–10.7s', sim: 'In range', accuracy: 'Validated ✓', check: true },
            ].map((bike) => (
              <div key={bike.name} className="bg-gray-950 border border-gray-800 rounded-xl p-8">
                <h3 className="font-semibold mb-1">{bike.name}</h3>
                <p className="text-sm text-gray-500 mb-6">{bike.cc}</p>
                <div className="space-y-4">
                  <div>
                    <p className="text-xs text-gray-400 mb-1">Target ET</p>
                    <p className="text-2xl font-bold text-orange-400">{bike.target}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 mb-1">Simulated ET</p>
                    <p className="text-2xl font-bold">{bike.sim}</p>
                  </div>
                  <div className="border-t border-gray-800 pt-4">
                    <p className="text-sm font-semibold text-green-400">{bike.accuracy}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Physics */}
      <section id="physics" className="bg-gray-950 border-t border-gray-800 py-24">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-3xl font-bold mb-12">15 Physics Sub-Models</h2>
          <div className="grid md:grid-cols-2 gap-10">
            {[
              {
                icon: <Zap className="text-orange-500" size={20} />,
                title: 'Engine & Drivetrain',
                items: ['3D engine torque curves (Willans friction model)', 'Forced induction — turbo, supercharger, nitrous', 'Gear shifting and clutch engagement dynamics', 'Chain drive losses and sprocket ratios'],
              },
              {
                icon: <BarChart3 className="text-orange-500" size={20} />,
                title: 'Aerodynamics & Grip',
                items: ['Drag coefficient and frontal area per-model', 'Tire slip dynamics (Pacejka + thermal model)', 'Weight transfer and traction limits', 'Rider CoG shift and wheelie physics'],
              },
              {
                icon: <TrendingUp className="text-orange-500" size={20} />,
                title: 'Environment & Setup',
                items: ['Air density, altitude and temperature correction', 'Rolling resistance and surface grip multipliers', 'Staging, reaction time, two-step launch control', 'Wind and live weather effects'],
              },
              {
                icon: <Github className="text-orange-500" size={20} />,
                title: 'Integration & Validation',
                items: ['RK4 fixed-step integrator at 1 ms timestep', 'Adaptive step-size solver (RK45)', '559+ passing test cases', 'Validated against real GPS and ECU telemetry'],
              },
            ].map((block) => (
              <div key={block.title}>
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  {block.icon} {block.title}
                </h3>
                <ul className="space-y-2 text-gray-300 text-sm">
                  {block.items.map((item) => (
                    <li key={item}>• {item}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="border-t border-gray-800 py-24">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-3xl font-bold mb-12">Curated Bike Library</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {[
              { num: '111', label: 'Bikes',  note: '17 manufacturers incl. KTM, Bajaj, TVS, RE' },
              { num: '69',  label: 'Tires',  note: 'Pacejka + thermal model, 15 brands' },
              { num: '70',  label: 'Parts',  note: 'Sprockets, exhaust, ECU flash, nitrous' },
              { num: '12',  label: 'Venues', note: '5 Indian + 7 international strips' },
            ].map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="text-4xl font-bold text-orange-400 mb-1">{stat.num}</div>
                <p className="text-gray-300 font-medium">{stat.label}</p>
                <p className="text-gray-500 text-xs mt-1">{stat.note}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section id="cta" className="bg-gray-950 border-t border-gray-800 py-24">
        <div className="max-w-6xl mx-auto px-6">
          <div className="bg-gradient-to-br from-orange-600/20 to-orange-500/10 border border-orange-500/30 rounded-2xl p-12 text-center">
            <h2 className="text-3xl font-bold mb-4">Run Your Own Simulation</h2>
            <p className="text-gray-300 mb-10 max-w-xl mx-auto">
              Use the live simulator above, or install the CLI for full analysis — calibrate against your own Dragy GPS runs, import ECU logs, and predict parts ROI.
            </p>
            <div className="grid sm:grid-cols-2 gap-4 max-w-xl mx-auto mb-10">
              <div className="text-left p-5 bg-black/50 rounded-xl border border-gray-800">
                <h3 className="font-semibold mb-1">CLI &amp; Python API</h3>
                <p className="text-sm text-gray-400">Full simulation from your terminal. Import Dragy GPS, dyno curves, and Woolich ECU logs for calibration.</p>
                <code className="block mt-3 text-xs text-orange-400 bg-black/50 p-2 rounded">pip install motoquant</code>
              </div>
              <div className="text-left p-5 bg-black/50 rounded-xl border border-gray-800">
                <h3 className="font-semibold mb-1">REST API</h3>
                <p className="text-sm text-gray-400">POST /api/simulate with a bike config and get full time-series v(t), RPM, gear, and ET.</p>
                <code className="block mt-3 text-xs text-orange-400 bg-black/50 p-2 rounded">api.motoquant.in/docs</code>
              </div>
            </div>
            <div className="flex gap-4 justify-center flex-wrap">
              <a
                href="#simulator"
                className="inline-flex items-center gap-2 px-8 py-3 bg-orange-600 hover:bg-orange-700 rounded-lg font-semibold transition-colors"
              >
                <Zap size={20} /> Try the Simulator
              </a>
              <a
                href="mailto:motoquant@gmail.com"
                className="inline-flex items-center gap-2 px-8 py-3 border border-orange-500 text-orange-400 hover:bg-orange-500/10 rounded-lg font-semibold transition-colors"
              >
                Get in Touch
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-10 text-center text-gray-500 text-sm">
        <p>Built for the Indian drag racing community. Validated physics, open source.</p>
        <p className="mt-2">motoquant.in · Made with ❤️ for the strip</p>
      </footer>

    </div>
  );
}
