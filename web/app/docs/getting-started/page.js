import { Suspense } from 'react';
import Link from 'next/link';
import RunSimCta from './RunSimCta';

export const metadata = {
  title: 'Getting Started — Run Your First Motorcycle Quarter-Mile Simulation',
  description: 'Step-by-step guide to running your first motorcycle quarter-mile drag simulation in MotoQuant Pro — pick from 342 bikes, choose Aamby Valley or MMRT or BIC as your venue, dial in rider weight + power delta + mass, and interpret the ET, 60-foot, and trap speed output. No physics PhD required.',
  keywords: [
    'motoquant getting started',
    'how to use motorcycle drag simulator',
    'motorcycle quarter mile simulation guide',
    'first drag simulation tutorial',
    'how to predict motorcycle quarter mile time',
    'motorcycle 60 ft time guide',
    'aamby valley simulation setup',
  ],
  alternates: { canonical: 'https://motoquant.in/docs/getting-started' },
};

function Step({ n, title, children }) {
  return (
    <div className="flex gap-5 mb-10">
      <div className="shrink-0 w-8 h-8 rounded-full bg-brand-orange/15 border border-brand-orange/40 flex items-center justify-center font-mono text-sm font-bold text-brand-orange">
        {n}
      </div>
      <div className="flex-1">
        <h3 className="font-display font-bold text-lg text-white mb-2">{title}</h3>
        <div className="text-white/70 text-sm leading-relaxed space-y-3">{children}</div>
      </div>
    </div>
  );
}

function Code({ children }) {
  return (
    <code className="block bg-black/50 border border-brand-orange/15 rounded-lg px-4 py-3 font-mono text-xs text-brand-accent my-3 overflow-x-auto">
      {children}
    </code>
  );
}

function InlineCode({ children }) {
  return <code className="bg-white/10 px-1.5 py-0.5 rounded font-mono text-xs text-brand-accent">{children}</code>;
}

export default function GettingStartedPage() {
  return (
    <article>
      <header className="mb-12">
        <div className="text-xs font-mono text-brand-orange/70 uppercase tracking-widest mb-2">Getting Started</div>
        <h1 className="font-display font-bold text-4xl text-white mb-4 tracking-tight">Your First Simulation</h1>
        <p className="text-white/60 text-base leading-relaxed">
          MotoQuant runs in the browser — no installation required to simulate. The desktop app and API
          are optional for advanced workflows. Start here.
        </p>
      </header>

      {/* Quick path */}
      <section className="mb-14">
        <h2 className="font-display font-bold text-2xl text-white mb-6">Option A — Web Simulator (instant, no account)</h2>
        <Step n="1" title="Open the simulator">
          <p>Navigate to <Link href="/simulator" className="text-brand-accent hover:text-brand-orange transition-colors font-mono">/simulator</Link>. No account required.</p>
        </Step>
        <Step n="2" title="Pick your bike">
          <p>Use the category tabs (Indian Sport / Indian Naked / Royal Enfield / Dream Bikes) or the search box to find your bike. The widget defaults to the Suzuki Hayabusa Gen1 — one of the best-validated bikes in the catalog.</p>
          <p>If your bike is not listed, use the <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">"Suggest a bike"</Link> form on the Bikes page. We add community-requested bikes regularly.</p>
        </Step>
        <Step n="3" title="Set your conditions">
          <p>The three sliders control:</p>
          <ul className="list-disc list-inside space-y-1 text-white/60 text-sm mt-2">
            <li><strong className="text-white">Rider weight</strong> — your weight in kg. Affects total system mass and CoG height.</li>
            <li><strong className="text-white">Power boost</strong> — percentage modifier on peak power and torque. Use this to simulate mods without selecting individual parts.</li>
            <li><strong className="text-white">Mass change</strong> — kg added or removed. Positive = added weight (pillion, luggage). Negative = weight reduction (stripped bodywork).</li>
          </ul>
        </Step>
        <Step n="4" title="Set your venue (optional)">
          <p>Click <strong className="text-white">Race location</strong> and either select a named venue (Aamby Valley, MMRT, BIC, Santa Pod, etc.) or enter your GPS coordinates. The simulator loads seasonal weather data automatically — density altitude, temperature, humidity, surface grip.</p>
          <p>If you skip this, the simulation runs at ISA sea-level conditions (15°C, 101.325 kPa, 0 m).</p>
        </Step>
        <Step n="5" title="Run and read the results">
          <p>Press <strong className="text-white">Run Simulation</strong>. Results appear in under a second:</p>
          <ul className="list-disc list-inside space-y-1 text-white/60 text-sm mt-2">
            <li><strong className="text-white">Quarter-Mile ET</strong> — elapsed time at 402.336 m, in seconds.</li>
            <li><strong className="text-white">Trap Speed</strong> — velocity at the 402 m mark, in km/h.</li>
            <li><strong className="text-white">Split Timeline</strong> — 60 ft, ⅛ mile, and ¼ mile ETs.</li>
            <li><strong className="text-white">Peak Power</strong> — effective power after altitude correction.</li>
          </ul>
        </Step>
      </section>

      {/* Desktop */}
      <section className="mb-14">
        <h2 className="font-display font-bold text-2xl text-white mb-6">Option B — Desktop App (beta)</h2>
        <p className="text-white/70 text-sm leading-relaxed mb-6">
          The desktop app runs the same physics engine locally with no cloud dependency. It adds five pages:
          full Simulate, Bikes browser, Build (parts composer), Compare (A-vs-B), and History (local leaderboard).
        </p>
        <div className="glass rounded-xl border border-brand-orange/20 p-5 mb-6">
          <div className="font-mono text-xs text-brand-orange/70 uppercase tracking-wide mb-3">Beta access</div>
          <p className="text-white/60 text-sm">
            Desktop beta is currently available to tuning shops and racing teams. Email{' '}
            <a href="mailto:motoquant@gmail.com?subject=MotoQuant%20Desktop%20Beta" className="text-brand-accent hover:text-brand-orange transition-colors">
              motoquant@gmail.com
            </a>{' '}
            with your use case to apply.
          </p>
        </div>
        <Step n="1" title="Prerequisites">
          <p>The desktop app requires macOS 13+, Windows 10/11 (x64), or Linux (Ubuntu 20+). The Python physics sidecar is bundled — no separate Python install needed.</p>
        </Step>
        <Step n="2" title="Install">
          <p>Download the installer from the release link provided in your beta invite email. Run the installer; it places the <InlineCode>MotoQuant Pro</InlineCode> app in your Applications / Program Files folder.</p>
        </Step>
        <Step n="3" title="First launch">
          <p>On first launch, the app spawns the physics sidecar on a random localhost port. You will see a loading screen for 2–8 seconds while the sidecar starts, then the Simulate page appears. The engine status chip in the top bar should show <strong className="text-brand-accent">Engine online</strong>.</p>
        </Step>
        <Step n="4" title="Development mode">
          <p>If you are contributing to the frontend and want to run against a live API, set:</p>
          <Code>MOTOQUANT_DEV_BACKEND_URL=http://127.0.0.1:8000</Code>
          <p>in your environment before launching the app. The app will skip the sidecar spawn and hit your manually-started uvicorn instance instead.</p>
        </Step>
      </section>

      {/* API */}
      <section className="mb-14">
        <h2 className="font-display font-bold text-2xl text-white mb-6">Option C — REST API</h2>
        <p className="text-white/70 text-sm leading-relaxed mb-6">
          The API is public and CORS-open. No authentication for basic simulation (rate-limited to 60 req/min per IP).
        </p>
        <Step n="1" title="Quick sim">
          <Code>{`POST https://motoquant-api.onrender.com/api/simulate/quick
Content-Type: application/json

{
  "bike_id": 1,
  "rider_mass_kg": 70,
  "power_boost_pct": 0,
  "mass_delta_kg": 0
}`}
          </Code>
          <p>Returns: <InlineCode>et_quarter_s</InlineCode>, <InlineCode>trap_speed_kmh</InlineCode>, <InlineCode>et_60ft_s</InlineCode>, <InlineCode>et_eighth_s</InlineCode>, <InlineCode>peak_power_hp</InlineCode>, <InlineCode>bike_name</InlineCode>.</p>
        </Step>
        <Step n="2" title="Full sim with timeseries">
          <Code>{`POST /api/simulate
{
  "bike_id": 1,
  "rider_mass_kg": 70,
  "power_boost_pct": 0,
  "use_adaptive_dt": false
}`}
          </Code>
          <p>Returns everything from quick sim plus <InlineCode>timeseries</InlineCode>: arrays of velocity, RPM, gear, acceleration, power at every 10 ms step.</p>
        </Step>
        <Step n="3" title="Interactive docs">
          <p>Full OpenAPI interactive docs (try-it-now) are available at:</p>
          <Code>https://motoquant-api.onrender.com/docs</Code>
        </Step>
      </section>

      {/* Reading the chart */}
      <section>
        <h2 className="font-display font-bold text-2xl text-white mb-6">Reading the Simulation Chart</h2>
        <p className="text-white/70 text-sm leading-relaxed mb-4">
          The desktop app (and the full simulator page) shows a 4-panel chart:
        </p>
        <div className="space-y-4">
          {[
            { label: 'Speed (km/h)', desc: 'Velocity over time. The slope of this curve is your instantaneous acceleration. A steep slope in first gear, flattening out toward trap speed.' },
            { label: 'RPM', desc: 'Engine RPM over time. You should see it rise to redline in each gear, drop at each upshift, then rise again. If RPM is flat for long periods, the clutch is slipping.' },
            { label: 'Acceleration (g)', desc: 'Longitudinal g-force. Typically 0.3–0.6g at launch for street bikes, 0.5–0.9g for built drag bikes. The ET reference line marks where ¼ mile falls on the time axis.' },
            { label: 'Power (kW)', desc: 'Wheel power delivered to the road. This is lower than engine power due to drivetrain losses, clutch slip during engagement, and tyre slip.' },
          ].map(item => (
            <div key={item.label} className="flex gap-4 p-4 rounded-lg glass border border-white/10">
              <div className="font-mono text-xs text-brand-orange w-32 shrink-0 pt-0.5">{item.label}</div>
              <div className="text-sm text-white/70">{item.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* EXP-014 — presence test: bottom CTA before the Next nav cards */}
      <Suspense fallback={null}>
        <RunSimCta />
      </Suspense>

      {/* Next steps */}
      <div className="mt-14 pt-8 border-t border-brand-orange/10">
        <div className="text-xs font-mono text-white/40 uppercase tracking-widest mb-4">Next</div>
        <div className="grid sm:grid-cols-2 gap-4">
          <Link href="/docs/physics" className="glass rounded-xl p-4 border border-white/10 hover:border-brand-orange/40 transition-colors group">
            <div className="font-display font-bold text-white mb-1 group-hover:text-brand-orange transition-colors">Physics Whitepaper →</div>
            <div className="text-xs text-white/50">15 sub-models, equations, and validation methodology.</div>
          </Link>
          <Link href="/docs/validation" className="glass rounded-xl p-4 border border-white/10 hover:border-brand-orange/40 transition-colors group">
            <div className="font-display font-bold text-white mb-1 group-hover:text-brand-orange transition-colors">Validation Data →</div>
            <div className="text-xs text-white/50">Benchmark table, per-cluster accuracy, and methodology.</div>
          </Link>
        </div>
      </div>
    </article>
  );
}
