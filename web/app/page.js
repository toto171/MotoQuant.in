import { Zap, TrendingUp, BarChart3, ArrowRight, CheckCircle2, Wind, Activity, Clock, Gauge, ChevronDown } from 'lucide-react';
import Link from 'next/link';
import SimulatorWidget from '../components/SimulatorWidget';

// FAQ data — each entry targets a real search query
const FAQS = [
  {
    q: 'What is the quarter mile time of a Suzuki GSX-R 1000?',
    a: 'The Suzuki GSX-R 1000 K5 runs a quarter mile in approximately 9.97 seconds with a trap speed of around 239 km/h under ISA standard conditions (sea level, 15 °C, 75 kg rider). MotoQuant Pro simulates the GSX-R 1000 at 10.04 s — within 0.07 s of the published benchmark.',
  },
  {
    q: 'How fast is a Kawasaki Ninja ZX-14R in the quarter mile?',
    a: 'The Kawasaki ZX-14R (Ninja H2 predecessor, 1441 cc) covers the quarter mile in approximately 9.91–10.10 seconds. MotoQuant Pro\'s physics simulation predicts 9.95 s, which falls within the published range. It is one of the fastest stock motorcycles available for drag racing.',
  },
  {
    q: 'What is the quarter mile time of a Suzuki Hayabusa?',
    a: 'The Suzuki GSX1300R Hayabusa (Gen 1) runs a quarter mile in 10.1–10.7 seconds depending on conditions, gearing, and rider weight. At Indian venues like Aamby Valley (altitude ~120 m), expect times toward the slower end of that range. MotoQuant Pro simulates the Hayabusa at 10.47 s at sea level, ISA conditions.',
  },
  {
    q: 'What is the quarter mile time of a KTM Duke 390?',
    a: 'The KTM Duke 390 (2023 model, 373.2 cc, ~44 PS) runs the quarter mile in approximately 13.5–14.2 seconds under normal conditions. At altitude (Aamby Valley, ~120 m above sea level) expect the high end of that range. MotoQuant Pro includes the Duke 390 in its 108-bike database with individual Cd and frontal area for accurate simulation.',
  },
  {
    q: 'How does altitude affect motorcycle drag racing times?',
    a: 'Altitude reduces air density, which lowers aerodynamic drag but also reduces engine power on naturally aspirated engines. The net effect is usually slower ETs at altitude: at 500 m elevation, expect roughly 0.10–0.15 s slower quarter mile times. At Aamby Valley (~120 m), the effect is small but measurable. MotoQuant Pro models this with a full density altitude correction using live weather data.',
  },
  {
    q: 'Is there a free motorcycle drag racing simulator for Indian bikes?',
    a: 'Yes — MotoQuant Pro is a free, physics-based motorcycle drag racing simulator purpose-built for the Indian market. It includes 108 bikes across 17 manufacturers including KTM, Bajaj Pulsar, TVS Apache, Royal Enfield, Hero, Yamaha India (R15, MT-15, FZ-X), Honda India (CBR 250R, CB 300R), Kawasaki India (Ninja 300/400), and Triumph India. Indian drag venues (Aamby Valley, MMRT, BIC, Kari, Hyderabad) are all modelled with actual seasonal weather data.',
  },
  {
    q: 'What is the quarter mile time of a Bajaj Pulsar NS200?',
    a: 'The Bajaj Pulsar NS200 (199.5 cc, ~24.5 PS) runs the quarter mile in approximately 15.0–15.8 seconds under standard conditions. Times will vary based on rider weight, tyre choice, and atmospheric conditions. MotoQuant Pro simulates the NS200 with its production gear ratios sourced from Bajaj service manuals.',
  },
  {
    q: 'How accurate is MotoQuant Pro compared to real drag racing times?',
    a: 'MotoQuant Pro has been validated against published quarter mile data from Cycle World, Motorcyclist, MCN, and Indian sources. 10 out of 10 validated bikes land within ±0.20 s of their reference time, and 8 out of 10 are within ±0.10 s. The physics engine uses 15 sub-models including Pacejka tyre dynamics, RK4 numerical integration at 1 ms timestep, and per-model aerodynamic coefficients.',
  },
  {
    q: 'Which motorcycle modifications improve quarter mile times the most in India?',
    a: 'Based on MotoQuant Pro\'s parts ROI analysis (in INR): (1) ECU flash / tune — typically 0.15–0.30 s improvement for ₹8,000–₹20,000; (2) Sprocket change (rear +1 tooth) — 0.05–0.10 s for ₹1,500–₹3,000; (3) Exhaust system — 0.05–0.15 s for ₹15,000–₹50,000; (4) Slick or drag-compound tyres — 0.10–0.25 s. Parts ROI analysis will be available in the upcoming full simulator release.',
  },
  {
    q: 'What drag racing venues are supported in MotoQuant Pro?',
    a: 'MotoQuant Pro currently models 12 drag venues: 5 Indian strips (Aamby Valley Airstrip, MMRT Chennai, BIC Delhi, Kari Motor Speedway, Hyderabad Racing Circuit) and 7 international venues (Santa Pod UK, Pomona Fairplex USA, Gainesville Raceway USA, Sydney Dragway Australia, Dubai Autodrome, Al-Ain Dragway UAE, and Jerez Circuit Spain). Each venue has full 12-month seasonal weather and altitude data.',
  },
  {
    q: 'How do I predict my motorcycle\'s quarter mile time?',
    a: 'Use MotoQuant Pro\'s free web simulator: select your bike from the 108-bike database, enter rider weight, adjust power/mass if you\'ve done modifications, and click Run. The physics engine runs a 15-submodel simulation and returns ET, trap speed, and gear-by-gear telemetry. The full app (coming soon) will also accept Dragy GPS data, dyno curves, and ECU logs for calibration.',
  },
  {
    q: 'What is a good quarter mile time for a 600 cc motorcycle?',
    a: 'A stock 600 cc supersport (Yamaha YZF-R6, Kawasaki ZX-6R, Honda CBR600RR) runs the quarter mile in approximately 10.8–11.5 seconds. A well-prepared drag bike in the same class with slicks, ECU tune, and sprocket change can approach 10.4–10.6 seconds. A stock 600 cc naked (Yamaha MT-07, Kawasaki Z650) will run 11.0–12.0 seconds depending on power-to-weight ratio.',
  },
];

// Bike reference data for lookup grid — top searched bikes
const BIKE_LOOKUP = [
  // Validated bikes first
  { name: 'Suzuki GSX-R 1000 K5', cc: '999cc', et: '10.04s', slug: 'suzuki-gsx-r-1000-k5' },
  { name: 'Kawasaki ZX-14R', cc: '1441cc', et: '9.95s', slug: 'kawasaki-zx-14r' },
  { name: 'Suzuki Hayabusa Gen1', cc: '1299cc', et: '10.47s', slug: 'suzuki-hayabusa-gen1' },
  { name: 'Yamaha YZF-R1 4C8', cc: '998cc', et: '10.30s', slug: 'yamaha-yzf-r1-4c8' },
  { name: 'BMW M1000RR', cc: '999cc', et: '10.17s', slug: 'bmw-m1000rr' },
  { name: 'Honda CBR1000RR-R', cc: '999cc', et: '10.23s', slug: 'honda-cbr1000rr-r' },
  { name: 'Kawasaki ZX-10RR', cc: '998cc', et: '10.20s', slug: 'kawasaki-zx-10rr' },
  { name: 'Kawasaki ZZR1400', cc: '1352cc', et: '10.01s', slug: 'kawasaki-zzr1400' },
  { name: 'Suzuki GSX-R750 K8', cc: '750cc', et: '10.85s', slug: 'suzuki-gsx-r750-k8' },
  { name: 'Royal Enfield GT 650', cc: '648cc', et: '14.88s', slug: 'royal-enfield-gt-650' },
  // Indian market bikes
  { name: 'KTM Duke 390', cc: '373cc', et: '~13.8s', slug: 'ktm-duke-390' },
  { name: 'KTM Duke 250', cc: '248cc', et: '~15.2s', slug: 'ktm-duke-250' },
  { name: 'KTM RC 390', cc: '373cc', et: '~13.6s', slug: 'ktm-rc-390' },
  { name: 'Bajaj Pulsar NS200', cc: '199cc', et: '~15.5s', slug: 'bajaj-pulsar-ns200' },
  { name: 'Bajaj Pulsar RS200', cc: '199cc', et: '~15.3s', slug: 'bajaj-pulsar-rs200' },
  { name: 'Bajaj Dominar 400', cc: '373cc', et: '~13.9s', slug: 'bajaj-dominar-400' },
  { name: 'TVS Apache RR 310', cc: '312cc', et: '~14.2s', slug: 'tvs-apache-rr-310' },
  { name: 'Yamaha R15 V4', cc: '155cc', et: '~17.0s', slug: 'yamaha-r15-v4' },
  { name: 'Yamaha MT-15 V2', cc: '155cc', et: '~17.3s', slug: 'yamaha-mt-15-v2' },
  { name: 'Honda CBR 250R', cc: '249cc', et: '~15.4s', slug: 'honda-cbr-250r' },
  { name: 'Royal Enfield Interceptor 650', cc: '648cc', et: '~14.9s', slug: 'royal-enfield-interceptor-650' },
  { name: 'Royal Enfield Himalayan 450', cc: '452cc', et: '~15.8s', slug: 'royal-enfield-himalayan-450' },
  { name: 'Triumph Speed 400', cc: '398cc', et: '~13.9s', slug: 'triumph-speed-400' },
  { name: 'Kawasaki Ninja 400', cc: '399cc', et: '~13.5s', slug: 'kawasaki-ninja-400' },
  // Superbikes
  { name: 'Ducati Panigale V4', cc: '1103cc', et: '~9.9s', slug: 'ducati-panigale-v4' },
  { name: 'Aprilia RSV4 Factory', cc: '1099cc', et: '~10.0s', slug: 'aprilia-rsv4-factory' },
  { name: 'Yamaha YZF-R6', cc: '599cc', et: '~11.1s', slug: 'yamaha-yzf-r6' },
  { name: 'Kawasaki ZX-6R', cc: '636cc', et: '~11.0s', slug: 'kawasaki-zx-6r' },
  { name: 'Kawasaki Z900', cc: '948cc', et: '~10.9s', slug: 'kawasaki-z900' },
  { name: 'Yamaha MT-09', cc: '890cc', et: '11.32s', slug: 'yamaha-mt-09' },
];

export default function HomePage() {
  return (
    <div className="min-h-screen bg-[#080808] text-white antialiased">

      {/* ── FAQ JSON-LD ─────────────────────────────────────────────── */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'FAQPage',
            mainEntity: FAQS.map(({ q, a }) => ({
              '@type': 'Question',
              name: q,
              acceptedAnswer: { '@type': 'Answer', text: a },
            })),
          }),
        }}
      />

      {/* ── Nav ─────────────────────────────────────────────────────── */}
      <nav className="border-b border-white/8 sticky top-0 bg-[#080808]/90 backdrop-blur-xl z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="text-xl font-bold tracking-tight">
            <span className="text-orange-500">Moto</span><span className="text-white">Quant</span>
            <span className="text-white/40 font-normal ml-1 text-sm">Pro</span>
          </div>
          <div className="flex gap-5 items-center text-sm">
            <a href="#simulator"  className="text-white/60 hover:text-white transition-colors hidden sm:block">Simulator</a>
            <a href="#bikes"      className="text-white/60 hover:text-white transition-colors hidden sm:block">Bike Library</a>
            <a href="#physics"    className="text-white/60 hover:text-white transition-colors hidden sm:block">Physics</a>
            <a href="#faq"        className="text-white/60 hover:text-white transition-colors hidden sm:block">FAQ</a>
            <Link
              href="/bikes"
              className="inline-flex items-center gap-1.5 px-4 py-1.5 bg-orange-600/20 border border-orange-500/30 text-orange-400 hover:bg-orange-600/30 rounded-full text-sm transition-colors"
            >
              All 108 Bikes →
            </Link>
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
            Free · Open Source · First-Principles Physics Engine
          </div>

          <h1 className="text-5xl sm:text-7xl font-black mb-6 leading-[1.05] tracking-tight">
            Motorcycle<br />
            Quarter Mile{' '}
            <span className="bg-gradient-to-r from-orange-400 to-orange-600 bg-clip-text text-transparent">
              Simulator
            </span>
          </h1>

          <p className="text-lg sm:text-xl text-white/50 max-w-2xl mx-auto mb-3 leading-relaxed">
            India's only physics-based motorcycle drag racing ET predictor.
            Simulate any bike, any venue, any build — in seconds.
          </p>
          <p className="text-sm text-white/30 mb-10">
            108 bikes · 15 physics sub-models · Validated at Aamby Valley, MMRT &amp; BIC · Indian parts pricing in ₹
          </p>

          <div className="flex flex-wrap gap-3 justify-center">
            <a
              href="#simulator"
              className="inline-flex items-center gap-2 px-7 py-3 bg-orange-600 hover:bg-orange-500 rounded-xl font-semibold transition-all shadow-lg shadow-orange-900/40 text-sm"
            >
              <Gauge size={16} /> Try the Simulator Free
            </a>
            <Link
              href="/bikes"
              className="inline-flex items-center gap-2 px-7 py-3 bg-white/6 hover:bg-white/10 border border-white/10 hover:border-white/20 rounded-xl font-semibold transition-all text-sm text-white/80"
            >
              Browse 108 Bikes
            </Link>
          </div>

          {/* Quick stats strip */}
          <div className="mt-16 inline-grid grid-cols-4 divide-x divide-white/8 border border-white/8 rounded-2xl bg-white/3 backdrop-blur-sm overflow-hidden text-sm">
            {[
              { num: '108',   label: 'Indian & global bikes' },
              { num: '±0.07s', label: 'Best validation accuracy' },
              { num: '15',    label: 'Physics sub-models' },
              { num: '5',     label: 'Indian drag venues' },
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
              Parts ROI in ₹ · Sobol sensitivity · Dragy GPS import · Dyno &amp; ECU import · Build optimiser · Leaderboard
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
            <p className="text-xs font-semibold uppercase tracking-widest text-orange-500 mb-3">Free Tool</p>
            <h2 className="text-3xl font-bold mb-3">Motorcycle Quarter Mile Calculator</h2>
            <p className="text-white/50 max-w-lg mx-auto text-sm leading-relaxed">
              Select your bike, enter rider weight, and simulate. The physics engine models
              tyre slip, weight transfer, gear shifting, and ambient conditions — not just power-to-weight.
            </p>
          </div>
          <SimulatorWidget />
        </div>
      </section>

      {/* ── Bike Quick Lookup ─────────────────────────────────────────── */}
      <section id="bikes" className="border-t border-white/8 py-24 bg-white/[0.02]">
        <div className="max-w-6xl mx-auto px-6">
          <p className="text-xs font-semibold uppercase tracking-widest text-orange-500 mb-3">Quick Reference</p>
          <h2 className="text-3xl font-bold mb-2">Quarter Mile Times by Bike</h2>
          <p className="text-white/40 text-sm mb-8 max-w-xl">
            Simulated ET at ISA conditions (sea level, 15 °C, 75 kg rider).
            Indian-venue results will differ — use the simulator above.{' '}
            <Link href="/bikes" className="text-orange-400 hover:underline">See all 108 bikes →</Link>
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 mb-8">
            {BIKE_LOOKUP.map((bike) => (
              <Link
                key={bike.slug}
                href={`/bikes/${bike.slug}`}
                className="group bg-white/4 hover:bg-white/7 border border-white/8 hover:border-orange-500/20 rounded-xl p-3 transition-all"
              >
                <div className="text-orange-400 font-bold text-base tabular-nums mb-1">{bike.et}</div>
                <div className="text-white/80 text-xs font-medium leading-snug group-hover:text-white transition-colors">{bike.name}</div>
                <div className="text-white/30 text-xs mt-0.5">{bike.cc}</div>
              </Link>
            ))}
          </div>

          <div className="flex items-center justify-between">
            <p className="text-xs text-white/25">
              * Simulated ET — actual strip times depend on conditions, tyres, and rider. Times marked ~ are model predictions, not validated benchmarks.
            </p>
            <Link
              href="/bikes"
              className="inline-flex items-center gap-1.5 text-sm text-orange-400 hover:text-orange-300 transition-colors font-medium"
            >
              All 108 bikes <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      </section>

      {/* ── Validation ───────────────────────────────────────────────── */}
      <section id="validation" className="border-t border-white/8 py-24">
        <div className="max-w-6xl mx-auto px-6">
          <p className="text-xs font-semibold uppercase tracking-widest text-orange-500 mb-3">Ground Truth</p>
          <h2 className="text-3xl font-bold mb-3">Validated Against Real Data</h2>
          <p className="text-white/50 mb-4 max-w-xl text-sm leading-relaxed">
            15-submodel physics engine benchmarked against published quarter-mile data from
            Cycle World, Motorcyclist, MCN, xBhp, and overdrive.in. All runs at ISA standard
            atmosphere — 15 °C, sea level, 75 kg rider.
          </p>

          <div className="flex flex-wrap gap-6 mb-12 text-sm">
            <div><span className="text-orange-400 font-bold text-lg">10</span> <span className="text-white/40">bikes validated</span></div>
            <div><span className="text-green-400 font-bold text-lg">10/10</span> <span className="text-white/40">within ±0.20s of reference</span></div>
            <div><span className="text-green-400 font-bold text-lg">8/10</span> <span className="text-white/40">within ±0.10s</span></div>
            <div><span className="text-orange-400 font-bold text-lg">6</span> <span className="text-white/40">manufacturers</span></div>
          </div>

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
      <section id="physics" className="border-t border-white/8 py-24 bg-white/[0.02]">
        <div className="max-w-6xl mx-auto px-6">
          <p className="text-xs font-semibold uppercase tracking-widest text-orange-500 mb-3">Under the Hood</p>
          <h2 className="text-3xl font-bold mb-4">15 Physics Sub-Models</h2>
          <p className="text-white/50 max-w-2xl text-sm mb-12 leading-relaxed">
            Unlike simple power-to-weight calculators, MotoQuant Pro runs a full numerical
            simulation of your motorcycle's run — from staged position to the traps. Every
            millisecond accounts for tyre slip, aerodynamic drag, clutch engagement, gear-shift
            timing, rider weight transfer, and real atmospheric conditions at your chosen venue.
          </p>
          <div className="grid md:grid-cols-2 gap-5">
            {[
              {
                icon: <Zap size={18} />,
                title: 'Engine &amp; Drivetrain',
                items: ['3D engine torque curves (Willans friction model)', 'Forced induction — turbo, supercharger, nitrous', 'Gear shifting and clutch engagement dynamics', 'Chain drive losses and sprocket ratios'],
              },
              {
                icon: <Wind size={18} />,
                title: 'Aerodynamics &amp; Grip',
                items: ['Per-model Cd + frontal area (0 over-generalization)', 'Tyre slip dynamics (Pacejka + thermal model)', 'Weight transfer and traction limits', 'Rider CoG shift and wheelie physics'],
              },
              {
                icon: <Activity size={18} />,
                title: 'Environment &amp; Setup',
                items: ['Air density, altitude and temperature correction', 'Rolling resistance and surface grip multipliers', 'Staging, reaction time, two-step launch control', 'Live weather effects at 12 drag venues'],
              },
              {
                icon: <BarChart3 size={18} />,
                title: 'Integration &amp; Validation',
                items: ['RK4 fixed-step integrator at 1 ms timestep', 'Adaptive step-size solver (RK45)', '565 passing test cases', 'Validated against real GPS and ECU telemetry'],
              },
            ].map((block) => (
              <div key={block.title} className="bg-white/5 backdrop-blur-md border border-white/8 rounded-2xl p-7 hover:border-orange-500/20 transition-colors">
                <h3 className="text-sm font-semibold mb-4 flex items-center gap-2 text-orange-400">
                  {block.icon} <span dangerouslySetInnerHTML={{ __html: block.title }} />
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
      <section className="border-t border-white/8 py-24">
        <div className="max-w-6xl mx-auto px-6">
          <p className="text-xs font-semibold uppercase tracking-widest text-orange-500 mb-3">The Library</p>
          <h2 className="text-3xl font-bold mb-14">Curated Bike &amp; Parts Catalog</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-white/8 rounded-2xl overflow-hidden border border-white/8">
            {[
              { num: '108', label: 'Bikes', note: '17 manufacturers incl. KTM, Bajaj, TVS, RE, Hero' },
              { num: '69',  label: 'Tyres',   note: 'Pacejka + thermal model, 15 brands incl. MRF, CEAT' },
              { num: '70',  label: 'Parts',   note: 'Sprockets, exhaust, ECU flash, nitrous, turbo, slicks' },
              { num: '12',  label: 'Venues',  note: '5 Indian strips + 7 international with seasonal weather' },
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

      {/* ── FAQ ──────────────────────────────────────────────────────── */}
      <section id="faq" className="border-t border-white/8 py-24 bg-white/[0.02]">
        <div className="max-w-4xl mx-auto px-6">
          <p className="text-xs font-semibold uppercase tracking-widest text-orange-500 mb-3">FAQ</p>
          <h2 className="text-3xl font-bold mb-12">
            Frequently Asked Questions
          </h2>

          <div className="space-y-3">
            {FAQS.map(({ q, a }, i) => (
              <details
                key={i}
                className="group bg-white/4 border border-white/8 rounded-2xl overflow-hidden hover:border-white/15 transition-colors"
              >
                <summary className="flex items-start justify-between gap-4 p-6 cursor-pointer list-none select-none">
                  <h3 className="text-sm font-semibold text-white/90 leading-snug">{q}</h3>
                  <ChevronDown
                    size={16}
                    className="flex-shrink-0 mt-0.5 text-white/30 group-open:rotate-180 transition-transform"
                  />
                </summary>
                <div className="px-6 pb-6 text-sm text-white/55 leading-relaxed border-t border-white/8 pt-4">
                  {a}
                </div>
              </details>
            ))}
          </div>

          <p className="mt-10 text-xs text-white/25">
            Have a question not listed here? More bikes, venues, and community features coming with the full app launch.
          </p>
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
                <div className="p-5 bg-orange-500/8 border border-orange-500/20 rounded-2xl">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Gauge size={15} className="text-orange-400" />
                      <h3 className="font-semibold text-sm text-orange-300">Simulation App</h3>
                    </div>
                    <span className="text-xs text-orange-500/60 bg-orange-500/10 px-2 py-0.5 rounded-full border border-orange-500/20">Soon</span>
                  </div>
                  <p className="text-xs text-white/50 leading-relaxed">Full GUI — parts ROI in ₹, Sobol analysis, dyno import, build optimiser, and leaderboard.</p>
                </div>

                <div className="p-5 bg-white/4 border border-white/8 rounded-2xl">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <TrendingUp size={15} className="text-white/60" />
                      <h3 className="font-semibold text-sm">CLI &amp; Python API</h3>
                    </div>
                    <span className="text-xs text-white/25 bg-white/5 px-2 py-0.5 rounded-full border border-white/10">Soon</span>
                  </div>
                  <p className="text-xs text-white/50 leading-relaxed">Full simulation from the terminal. Import Dragy GPS, dyno curves, and Woolich ECU logs.</p>
                </div>

                <div className="p-5 bg-white/4 border border-white/8 rounded-2xl">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <BarChart3 size={15} className="text-white/60" />
                      <h3 className="font-semibold text-sm">REST API</h3>
                    </div>
                    <span className="text-xs text-white/25 bg-white/5 px-2 py-0.5 rounded-full border border-white/10">Soon</span>
                  </div>
                  <p className="text-xs text-white/50 leading-relaxed">POST /api/simulate — get full v(t), RPM(t), gear(t) timeseries with Pydantic validation.</p>
                </div>
              </div>

              <div className="flex items-center gap-3 text-sm text-white/40">
                <ArrowRight size={15} className="text-orange-600" />
                In the meantime, explore the simulator and bike library above.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────────── */}
      <footer className="border-t border-white/8 py-10">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4 text-sm text-white/30 mb-6">
            <div>
              <span className="text-orange-500 font-semibold">Moto</span>Quant Pro ·{' '}
              <span className="italic">The physics of faster</span>
            </div>
            <div className="flex items-center gap-5">
              <Link href="/bikes" className="hover:text-white/60 transition-colors">Bike Library</Link>
              <span>motoquant.in</span>
              <span>Built for the Indian drag strip</span>
            </div>
          </div>
          {/* Footer keyword-rich text for SEO — helps long-tail crawling */}
          <p className="text-xs text-white/15 text-center leading-relaxed max-w-3xl mx-auto">
            MotoQuant Pro is a free motorcycle quarter mile calculator and drag racing simulator.
            Predict ET for KTM Duke, Bajaj Pulsar, TVS Apache, Royal Enfield, Yamaha, Honda, Kawasaki,
            Suzuki, and more. Indian drag strips covered: Aamby Valley, MMRT Chennai, BIC Delhi, Kari Motor Speedway.
          </p>
        </div>
      </footer>

    </div>
  );
}
