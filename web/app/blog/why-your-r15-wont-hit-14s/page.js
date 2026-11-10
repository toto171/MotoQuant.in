import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import CodeComment from '../../../components/CodeComment';
import ScoreboardDigits from '../../../components/ScoreboardDigits';

export const metadata = {
  title: "R15 V4 quarter-mile time: why your R15 won't hit 14s | MotoQuant",
  description: "Factory power says a Yamaha R15 V3/V4 should run ~14.5s over the quarter mile. Real R15s run 15.5–17.6s at Indian drag strips. Where each second goes: gearing, clutch slip, traction and aero.",
  keywords: ['R15 V4 quarter mile time', 'R15 V3 quarter mile', 'Yamaha R15 quarter mile', 'R15 V4 drag time', 'R15 V4 0-100 india', 'Indian 150cc drag', 'R15 tuning', 'why is my R15 slow', 'r15 vs ns200 drag', 'r15 vs hornet 2.0'],
  alternates: { canonical: 'https://motoquant.in/blog/why-your-r15-wont-hit-14s' },
  openGraph: {
    title: "Why your R15 won't hit 14s",
    description: 'Where the R15 V3 loses time between its factory power figure and its real drag times.',
    url: 'https://motoquant.in/blog/why-your-r15-wont-hit-14s',
    type: 'article',
    publishedTime: '2026-04-24T00:00:00Z',
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: 'The Yamaha YZF-R15 V3 makes 18.5 hp at the crank. Put that through a simple power-to-weight formula for a 134 kg bike and a 70 kg rider and you get a quarter-mile time of about 14.3–14.7 seconds. On a good day at a decent strip, most R15 V3s run 15.5–16.2 seconds, one to two full seconds slower.',
  },
  {
    type: 'h2',
    text: 'The numbers',
  },
  {
    type: 'p',
    text: 'Factory spec for the R15 V3: 155cc single-cylinder SOHC 4-valve, 18.4 hp @ 10,000 RPM, 14.7 Nm @ 7,500 RPM, dry mass 137 kg (kerb ~141 kg), 6-speed gearbox with gear ratios from the service manual: F14/R48 sprockets, ratios [2.833, 1.875, 1.429, 1.160, 0.963, 0.840].',
  },
  {
    type: 'p',
    text: 'MotoQuant\'s post-calibration sweep on the R15 V3 gives a simulated ET of about 15.1–15.6 seconds, depending on launch conditions and rider weight. Strip times that riders report on BikeWale, in YouTube drag videos and in Facebook R15 groups cluster around 15.6–16.0 seconds for stock bikes. That fits the 0.5–1.0 second gap our simulator correctly models.',
  },
  {
    type: 'h2',
    text: 'Loss 1: drivetrain and clutch (~0.3–0.5s)',
  },
  {
    type: 'p',
    text: 'The R15\'s wet multi-plate clutch is set up for the street, with smooth, progressive engagement. On the strip a jerky release does one of two things: the tyre spins up too fast and loses traction, or the engine bogs and loses RPM. Either costs time.',
  },
  {
    type: 'p',
    text: 'The R15 runs a 428-pitch chain. Worn or badly tensioned, it can lose 2–4% of engine power. That is 0.4–0.7 hp, a real loss when the whole bike makes 18 hp. MotoQuant models chain efficiency at 0.94 for small-cc bikes with budget-grade chains.',
  },
  {
    type: 'callout',
    text: 'The biggest clutch fix for the R15 is practice, not parts. A smooth, fast release at 4,000–4,500 RPM consistently beats a slip-and-dump at 6,000 RPM. In MotoQuant\'s simulation the best R15 launch RPM is around 4,200 RPM (56% of peak power RPM).',
  },
  {
    type: 'h2',
    text: 'Loss 2: gearing (~0.4–0.6s)',
  },
  {
    type: 'p',
    text: 'On the R15 V3 service-manual ratios, first gear runs out at about 40 km/h at redline and second at roughly 67 km/h. By the shift into third, around 2.5 seconds into the run, you are already past the point where launch errors compound.',
  },
  {
    type: 'p',
    text: 'Yamaha made first gear tall on purpose, because it helps fuel economy and cuts wheelspin on slippery roads. On a drag strip it keeps you longer in a lower-torque part of the curve before the bike gets on the pipe.',
  },
  {
    type: 'p',
    text: 'The usual strip mod for the R15 is a smaller front sprocket, F14 to F13 (−7% overall ratio). First gear then runs out at ~37 km/h, and the bike spends longer near peak torque. The mod is in MotoQuant\'s parts catalog, and on the R15 it typically cuts ET by 0.15–0.25 seconds.',
  },
  {
    type: 'h2',
    text: 'Loss 3: aerodynamics and the long run (~0.2–0.4s)',
  },
  {
    type: 'p',
    text: 'The R15 V3 has a Cd of about 0.308 (MotoQuant\'s per-bike value from frontal area analysis) and a frontal area of around 0.35 m², so Cd×A ≈ 0.108 m². At a 150 km/h trap speed, aero drag is the main force limiting terminal velocity.',
  },
  {
    type: 'p',
    text: 'On a 155cc bike making 18 hp, drag starts to matter earlier in the run than on a litre-class bike. The R15 reaches its aero-limited terminal velocity (roughly 140–145 km/h at full tuck) before the 402 m mark, so the last 100 metres are almost all a fight against drag.',
  },
  {
    type: 'h2',
    text: 'Loss 4: traction (~0.2–0.5s)',
  },
  {
    type: 'p',
    text: 'This is the least intuitive loss: traction limits the R15 more than power does. The stock MRF Revz tyres (100/80-17 front, 140/70-17 rear) have a μ_peak of roughly 0.95–1.05 on typical Indian asphalt. With a 141 kg kerb mass and a 70 kg rider, the total is 211 kg.',
  },
  {
    type: 'p',
    text: 'The most force the rear tyre can put down at launch is roughly (0.95 × 211 kg × 9.81 m/s²) × rear_load_fraction ≈ 1,000 N. With 18 hp and a 2.833 first gear, the engine can deliver more torque in first than the tyre can use. The tyre is the bottleneck.',
  },
  {
    type: 'p',
    text: 'A power-boost tune on a stock R15 gives disappointing ET gains because the extra torque just spins the rear tyre more. On the R15, do it in this order: (1) gearing, (2) tyres (MRF Zapper or CEAT Zoom Rad X3 for better μ_peak), (3) then power mods.',
  },
  {
    type: 'callout',
    text: 'In MotoQuant\'s R15 sweep, a 10% power boost cuts ET by ~0.05s on a stock-setup R15. A tyre with 10% higher μ_peak cuts it by ~0.18s. A sprocket change (F14 to F13) cuts ~0.22s, and tyre and sprocket together cut ~0.35s.',
  },
  {
    type: 'h2',
    text: 'What works',
  },
  {
    type: 'p',
    text: 'Ranked by ET gained per rupee for a stock R15 V3 on an Indian drag strip, from MotoQuant\'s cost-per-tenth analysis:',
  },
  {
    type: 'p',
    text: '1. Front sprocket reduction F14→F13 (₹800–1,200): −0.20–0.25s ET. The best cost per tenth in the parts catalog for this bike.',
  },
  {
    type: 'p',
    text: '2. Tyre upgrade to CEAT Zoom Rad X3 or MRF Zapper (₹4,000–6,000 fitted): −0.15–0.20s ET. Improves both grip and tyre temperature response.',
  },
  {
    type: 'p',
    text: '3. Air filter upgrade (K&N or DNA equivalent, ₹2,500–4,000): −0.06–0.10s ET. Lets the 155cc single breathe above 9,000 RPM, where the stock filter restricts it.',
  },
  {
    type: 'p',
    text: '4. Exhaust system slip-on (Tyga, Arrow, Higgspeed, ₹8,000–18,000): −0.08–0.12s ET. The gain is mostly mid-range torque rather than peak power, and mid-range is what a gearing-limited launch needs.',
  },
  {
    type: 'p',
    text: 'None of these gets a stock R15 V3 to a genuine 14s ET without a better launch and better conditions too. A well-prepared R15 with a good rider, the right sprocket, sticky tyres and a cold-weather session at Aamby Valley can realistically hit 15.0–15.2 seconds, against 15.8–16.2s stock.',
  },
  {
    type: 'h2',
    text: 'Weather and altitude',
  },
  {
    type: 'p',
    text: 'Between a 35°C day at a low-altitude strip and a 20°C morning at 1,100 m density altitude, your R15\'s ET can change by 0.3–0.5 seconds. Air density changes engine power (less oxygen at altitude) and aero drag (less drag at altitude, a net positive at DA >800 m). Enter your strip conditions in MotoQuant\'s location picker to see the effect.',
  },
];

function Prose({ content }) {
  return (
    <div className="max-w-2xl mx-auto">
      {content.map((block, i) => {
        if (block.type === 'h2') return <h2 key={i} className="font-display font-bold text-2xl md:text-3xl text-white mt-12 mb-4 tracking-tight">{block.text}</h2>;
        if (block.type === 'lead') return <p key={i} className="text-lg text-white/80 leading-relaxed mb-8 font-light">{block.text}</p>;
        if (block.type === 'callout') return (
          <div key={i} className="my-8 px-5 py-4 rounded-xl border-l-4 border-brand-orange bg-brand-orange/5">
            <p className="text-sm text-white/80 leading-relaxed italic">{block.text}</p>
          </div>
        );
        return <p key={i} className="text-white/75 text-base leading-relaxed mb-5">{block.text}</p>;
      })}
    </div>
  );
}

export default function PostPage() {
  return (
    <div className="min-h-screen bg-black text-white">
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          <div className="flex flex-wrap gap-2 mb-6">
            {['small-cc', 'Yamaha R15', 'Indian bikes', 'tuning'].map(t => (
              <span key={t} className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent">{t}</span>
            ))}
          </div>
          <CodeComment className="mb-4">r15 v3 · where the seconds go</CodeComment>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Why your R15 won&apos;t hit 14s (and what will help)
          </h1>
          <div className="text-sm text-white/60 mb-6">
            24 April 2026 · 10 min read · MotoQuant Blog
          </div>

          {/* stock vs prepped — timing-board strip */}
          <div className="relative overflow-hidden rounded-xl border border-brand-orange/20 bg-ink-1/60 p-5 mb-12 flex flex-wrap items-end gap-x-10 gap-y-4">
            <span aria-hidden="true" className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-brand-orange/50 to-transparent" />
            <div>
              <div className="flex items-end gap-1.5">
                <ScoreboardDigits value="16.2" h={26} label="16.2 seconds stock" />
                <span className="font-mono text-xs text-white/60 mb-0.5">s</span>
              </div>
              <div className="mt-1.5 text-xs text-white/60">stock · 15.8–16.2 band</div>
            </div>
            <div>
              <div className="flex items-end gap-1.5">
                <ScoreboardDigits value="15.0" h={26} label="15.0 seconds prepped" />
                <span className="font-mono text-xs text-white/60 mb-0.5">s</span>
              </div>
              <div className="mt-1.5 text-xs text-white/60">prepped · sprocket + tyres + filter</div>
            </div>
            <div className="text-xs text-accent mb-0.5">Δ −1.2 s · engine never opened</div>
          </div>
        </div>

        <Prose content={CONTENT} />

        <div className="max-w-2xl mx-auto mt-16 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Simulate your R15 setup</div>
            <div className="text-white/60 text-sm">Pick the YZF-R15 V3, try the sprocket mod in the parts builder, and see the ET change before you buy anything.</div>
          </div>
          <Link href="/simulator" className="shrink-0 px-5 py-2.5 bg-brand-orange text-on-accent font-display font-bold rounded-lg text-sm hover:bg-brand-orangeLight transition-colors">Open the simulator →</Link>
        </div>
      </article>

      <SiteFooter />
    </div>
  );
}
