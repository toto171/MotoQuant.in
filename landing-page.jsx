import React from 'react';
import { Zap, TrendingUp, BarChart3, Github, ExternalLink } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-black text-white">
      {/* Navigation */}
      <nav className="border-b border-gray-800 sticky top-0 bg-black/95 backdrop-blur">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="text-2xl font-bold tracking-tight">
            <span className="text-orange-500">Moto</span>Quant Pro
          </div>
          <div className="flex gap-6 items-center text-sm">
            <a href="#physics" className="hover:text-orange-500 transition">Physics</a>
            <a href="#validation" className="hover:text-orange-500 transition">Validation</a>
            <a href="#cta" className="hover:text-orange-500 transition">Get Started</a>
            <a href="https://github.com/hritwik-mudhai/motoquant" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white">
              <Github size={20} />
            </a>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 py-24 text-center">
        <div className="mb-6 inline-block px-4 py-2 bg-orange-500/10 border border-orange-500/30 rounded-full text-orange-400 text-sm font-medium">
          Open Source Drag Racing Physics Engine
        </div>
        <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
          The Physics of Faster
        </h1>
        <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-12">
          First-principles physics simulation for quarter-mile drag racing. Predict ET, optimize builds, and understand what actually matters on the strip.
        </p>
        <p className="text-gray-500 text-sm mb-8">
          Built for the Indian drag racing community. Validated on real bikes at Aamby Valley, MMRT, and beyond.
        </p>
      </section>

      {/* Validation Section */}
      <section id="validation" className="bg-gradient-to-b from-gray-900 to-black py-24 border-t border-gray-800">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-3xl font-bold mb-4">Validated on Real Data</h2>
          <p className="text-gray-400 mb-12 max-w-2xl">
            Our 15-submodel physics engine is tested against real drag racing telemetry and dyno data. The results speak for themselves.
          </p>

          <div className="grid md:grid-cols-3 gap-8">
            {/* GSX-R 1000 K5 */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-8">
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-2">Suzuki GSX-R 1000 K5</h3>
                <p className="text-sm text-gray-500">1000cc Superbike</p>
              </div>
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-400">Target ET (Aamby Valley)</p>
                  <p className="text-2xl font-bold text-orange-400">9.97s</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Simulated ET</p>
                  <p className="text-2xl font-bold">10.04s</p>
                </div>
                <div className="pt-4 border-t border-gray-800">
                  <p className="text-sm font-semibold text-green-400">Accuracy: ±0.07s (0.7%)</p>
                </div>
              </div>
            </div>

            {/* YZF-R1 */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-8">
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-2">Yamaha YZF-R1 4C8</h3>
                <p className="text-sm text-gray-500">1000cc Superbike</p>
              </div>
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-400">Target ET Range</p>
                  <p className="text-2xl font-bold text-orange-400">10.2–10.4s</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Simulated ET</p>
                  <p className="text-2xl font-bold">~10.3s</p>
                </div>
                <div className="pt-4 border-t border-gray-800">
                  <p className="text-sm font-semibold text-green-400">In-range ✓</p>
                </div>
              </div>
            </div>

            {/* Hayabusa */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-8">
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-2">Suzuki Hayabusa Gen1</h3>
                <p className="text-sm text-gray-500">1300cc Hyperbike</p>
              </div>
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-400">Target ET Range</p>
                  <p className="text-2xl font-bold text-orange-400">10.1–10.7s</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Simulated ET</p>
                  <p className="text-2xl font-bold">In range</p>
                </div>
                <div className="pt-4 border-t border-gray-800">
                  <p className="text-sm font-semibold text-green-400">Validated ✓</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Physics Section */}
      <section id="physics" className="max-w-6xl mx-auto px-6 py-24">
        <h2 className="text-3xl font-bold mb-12">15 Physics Sub-Models</h2>
        <div className="grid md:grid-cols-2 gap-8">
          <div>
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Zap className="text-orange-500" size={20} />
              Engine & Drivetrain
            </h3>
            <ul className="space-y-2 text-gray-300 text-sm">
              <li>• 3D engine torque curves (Willans friction model)</li>
              <li>• Forced induction (turbo, supercharger, nitrous)</li>
              <li>• Gear shifting and clutch engagement dynamics</li>
              <li>• Chain drive losses and sprocket ratios</li>
            </ul>
          </div>
          <div>
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <BarChart3 className="text-orange-500" size={20} />
              Aerodynamics & Grip
            </h3>
            <ul className="space-y-2 text-gray-300 text-sm">
              <li>• Drag coefficient and frontal area</li>
              <li>• Tire slip dynamics (Pacejka, thermal model)</li>
              <li>• Weight transfer and traction limits</li>
              <li>• Rider CoG shift and wheelie physics</li>
            </ul>
          </div>
          <div>
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <TrendingUp className="text-orange-500" size={20} />
              Environment & Setup
            </h3>
            <ul className="space-y-2 text-gray-300 text-sm">
              <li>• Air density altitude and temperature</li>
              <li>• Rolling resistance and surface grip</li>
              <li>• Staging, reaction time, and two-step control</li>
              <li>• Wind and weather effects</li>
            </ul>
          </div>
          <div>
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <ExternalLink className="text-orange-500" size={20} />
              Integration & Validation
            </h3>
            <ul className="space-y-2 text-gray-300 text-sm">
              <li>• RK4 fixed-step integrator (1 ms)</li>
              <li>• Adaptive step-size solver (RK45)</li>
              <li>• Tested on 245+ test cases</li>
              <li>• Validated against real telemetry</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Database Section */}
      <section className="bg-gray-900/50 border-t border-gray-800 py-24">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-3xl font-bold mb-12">Curated Bike Library</h2>
          <div className="grid md:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="text-3xl font-bold text-orange-400 mb-2">81</div>
              <p className="text-gray-400">Bikes</p>
              <p className="text-xs text-gray-500 mt-2">Superbikes, naked, retro across 15 manufacturers</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-orange-400 mb-2">29</div>
              <p className="text-gray-400">Tires</p>
              <p className="text-xs text-gray-500 mt-2">Pacejka model + thermal coefficients</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-orange-400 mb-2">58</div>
              <p className="text-gray-400">Parts</p>
              <p className="text-xs text-gray-500 mt-2">Sprockets, exhaust, ECU, nitrous</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-orange-400 mb-2">12</div>
              <p className="text-gray-400">Venues</p>
              <p className="text-xs text-gray-500 mt-2">Indian + international drag strips</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section id="cta" className="max-w-6xl mx-auto px-6 py-24">
        <div className="bg-gradient-to-r from-orange-600/20 to-orange-500/20 border border-orange-500/30 rounded-lg p-12 text-center">
          <h2 className="text-3xl font-bold mb-6">Ready to Optimize Your Build?</h2>
          <p className="text-gray-300 mb-8 max-w-2xl mx-auto">
            MotoQuant Pro is in active development. Right now, you can:
          </p>
          <div className="grid md:grid-cols-2 gap-6 max-w-2xl mx-auto mb-12">
            <div className="text-left p-4 bg-gray-900 rounded border border-gray-800">
              <h3 className="font-semibold mb-2">Use the CLI</h3>
              <p className="text-sm text-gray-400">Run full simulations from your terminal. See the code, contribute, or fork it for your own analysis.</p>
            </div>
            <div className="text-left p-4 bg-gray-900 rounded border border-gray-800">
              <h3 className="font-semibold mb-2">Web Simulator (Beta)</h3>
              <p className="text-sm text-gray-400">Coming Q3 2026: interactive browser-based simulator with live tuning and real-time ET prediction.</p>
            </div>
          </div>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a href="https://github.com/hritwik-mudhai/motoquant" target="_blank" rel="noopener noreferrer" className="px-8 py-3 bg-orange-600 hover:bg-orange-700 rounded font-semibold transition flex items-center justify-center gap-2">
              <Github size={20} />
              View on GitHub
            </a>
            <a href="https://github.com/hritwik-mudhai/motoquant#quickstart" target="_blank" rel="noopener noreferrer" className="px-8 py-3 border border-orange-500 text-orange-400 hover:bg-orange-500/10 rounded font-semibold transition">
              Quick Start
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-12 text-center text-gray-500 text-sm">
        <p>Built for the Indian drag racing community. Validated physics, open source.</p>
        <p className="mt-2">motoquant.in • GitHub • Made with ❤️ for the strip</p>
      </footer>
    </div>
  );
}
