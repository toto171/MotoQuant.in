import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';

export const metadata = {
  title: "Why Your R15 Won't Hit 14s — MotoQuant Blog",
  description: "The Yamaha YZF-R15 V3 should run ~14.5s based on factory power. Most stock bikes run 15.5–16s. The gap is about gearing, clutch slip, and traction — not engine power.",
  keywords: ['Yamaha R15 quarter mile', 'R15 V3 drag time', 'Indian 150cc drag', 'R15 tuning', 'why is my R15 slow'],
  alternates: { canonical: 'https://motoquant.in/blog/why-your-r15-wont-hit-14s' },
  openGraph: {
    title: "Why Your R15 Won't Hit 14s",
    description: 'The gap between factory power and real-world drag times on the R15 V3 — analysed.',
    url: 'https://motoquant.in/blog/why-your-r15-wont-hit-14s',
    type: 'article',
    publishedTime: '2026-04-24T00:00:00Z',
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: 'The Yamaha YZF-R15 V3 makes 18.5 hp at the crank. A naive power-to-weight calculation on a 134 kg bike with a 70 kg rider gives a theoretical quarter-mile time of about 14.3–14.7 seconds. On a good day at a decent strip, most R15 V3s run 15.5–16.2 seconds. That is a gap of one to two full seconds. This article explains exactly where each of those seconds goes.',
  },
  {
    type: 'h2',
    text: 'The Numbers That Matter',
  },
  {
    type: 'p',
    text: 'Factory spec for the R15 V3: 155cc single-cylinder SOHC 4-valve, 18.4 hp @ 10,000 RPM, 14.7 Nm @ 7,500 RPM, dry mass 137 kg (kerb ~141 kg), 6-speed gearbox with gear ratios from the service manual: F14/R48 sprockets, ratios [2.833, 1.875, 1.429, 1.160, 0.963, 0.840].',
  },
  {
    type: 'p',
    text: 'MotoQuant\'s post-calibration sweep on the R15 V3 gives a simulated ET of approximately 15.1–15.6 seconds depending on launch conditions and rider weight. Community-reported strip times from BikeWale, YouTube drag videos, and Facebook R15 groups cluster around 15.6–16.0 seconds for stock bikes. This is consistent with a 0.5–1.0 second gap that our simulator correctly models.',
  },
  {
    type: 'h2',
    text: 'Loss #1: Drivetrain and Clutch Losses (~0.3–0.5s)',
  },
  {
    type: 'p',
    text: 'The R15\'s wet multi-plate clutch is tuned for street riding — smooth, progressive engagement. On the strip, a jerky release causes two problems: the tyre spins up too fast (hurting traction) or the engine bogs (losing RPM). Either costs time.',
  },
  {
    type: 'p',
    text: 'Chain drive losses on a 428-pitch chain (R15 uses 428) with a worn or improperly tensioned chain can account for 2–4% of engine power. That is 0.4–0.7 hp — meaningful when the total is 18 hp. MotoQuant models chain efficiency at 0.94 for small-cc bikes with budget-grade chains.',
  },
  {
    type: 'callout',
    text: 'The single biggest clutch fix for the R15 is practice, not parts. A smooth, fast release at 4,000–4,500 RPM consistently beats a slip-and-dump at 6,000 RPM. MotoQuant\'s simulation shows the optimal R15 launch RPM is around 4,200 RPM — 56% of peak power RPM.',
  },
  {
    type: 'h2',
    text: 'Loss #2: Gearing and Acceleration Structure (~0.4–0.6s)',
  },
  {
    type: 'p',
    text: 'The R15 V3 service-manual gear ratios produce a very specific acceleration curve. First gear takes the bike from 0 to approximately 40 km/h at redline. Second gear gets you to roughly 67 km/h. By the time you are shifting into third gear (around 2.5 seconds into the run), you are already past the point where launch errors compound.',
  },
  {
    type: 'p',
    text: 'The tall first gear is a deliberate design choice — it helps with fuel economy and reduces wheelspin on slippery roads. On a drag strip, it means you spend more time in a lower-torque part of the curve before the bike fully gets on the pipe.',
  },
  {
    type: 'p',
    text: 'The most common gearing mod for the R15 on the strip is a front sprocket drop from F14 to F13 (−7% overall ratio), which drops first-gear top speed to ~37 km/h and extends the time the bike spends near peak torque. MotoQuant\'s parts catalog includes this mod — it typically shows an ET improvement of 0.15–0.25 seconds on the R15.',
  },
  {
    type: 'h2',
    text: 'Loss #3: Aerodynamics and the Long Run (~0.2–0.4s)',
  },
  {
    type: 'p',
    text: 'The R15 V3 has a Cd of approximately 0.308 (MotoQuant\'s per-bike value from frontal area analysis) with a frontal area of around 0.35 m². Cd×A ≈ 0.108 m². At 150 km/h trap speed, aerodynamic drag is the dominant force limiting terminal velocity.',
  },
  {
    type: 'p',
    text: 'For a 155cc bike making 18 hp, aero drag becomes significant earlier in the run than for a litre-class bike. The R15 reaches its aero-limited terminal velocity — roughly 140–145 km/h at full tuck — before the 402 m mark. The last 100 metres of the run are fought almost entirely against drag rather than being powered by engine torque.',
  },
  {
    type: 'h2',
    text: 'Loss #4: Traction and Small-CC Physics (~0.2–0.5s)',
  },
  {
    type: 'p',
    text: 'This is the most counterintuitive one: the R15\'s traction model limits it more than its power does. The stock MRF Revz 100/80-17 front / 140/70-17 rear tires have a μ_peak of roughly 0.95–1.05 on typical Indian asphalt. With a 141 kg kerb mass and a 70 kg rider, total system mass is 211 kg.',
  },
  {
    type: 'p',
    text: 'Maximum traction-limited force at launch is roughly (0.95 × 211 kg × 9.81 m/s²) × rear_load_fraction ≈ 1,000 N on the rear wheel. At 18 hp and a first-gear ratio of 2.833, the engine can deliver more torque than the tyre can use in the first gear — meaning the tyre is the bottleneck, not the engine.',
  },
  {
    type: 'p',
    text: 'This is why adding more power to a stock R15 via a power-boost tune produces disappointing ET gains. The extra torque just spins the rear tyre more. The correct sequence for the R15 is: (1) gearing optimisation, (2) tyre upgrade (MRF Zapper or CEAT Zoom Rad X3 for better μ_peak), (3) then consider power mods.',
  },
  {
    type: 'callout',
    text: 'The MotoQuant R15 sweep confirms this: a 10% power boost drops ET by ~0.05s on a stock-setup R15. A tyre with 10% higher μ_peak drops it by ~0.18s. A sprocket change (F13 from F14) drops it by ~0.22s. The tire and sprocket together: ~0.35s. That is the correct tuning order.',
  },
  {
    type: 'h2',
    text: 'What Actually Works',
  },
  {
    type: 'p',
    text: 'Ranked by ET return per rupee for a stock R15 V3 on an Indian drag strip, based on MotoQuant\'s cost-per-tenth analysis:',
  },
  {
    type: 'p',
    text: '1. Front sprocket reduction F14→F13 (₹800–1,200): −0.20–0.25s ET. Best cost-per-tenth in the entire parts catalog for this bike.',
  },
  {
    type: 'p',
    text: '2. Tyre upgrade to CEAT Zoom Rad X3 or MRF Zapper (₹4,000–6,000 fitted): −0.15–0.20s ET. Improves both grip and tyre temperature response.',
  },
  {
    type: 'p',
    text: '3. Air filter upgrade (K&N or DNA equivalent, ₹2,500–4,000): −0.06–0.10s ET. Frees the 155cc single to breathe above 9,000 RPM where it was previously restricted.',
  },
  {
    type: 'p',
    text: '4. Exhaust system slip-on (Tyga, Arrow, Higgspeed, ₹8,000–18,000): −0.08–0.12s ET. Gains are mostly mid-range torque, not peak power, which is what matters for gearing-constrained launches.',
  },
  {
    type: 'p',
    text: 'None of these will get a stock R15 V3 to a genuine 14s ET without also optimising the launch and conditions. But a well-prepared R15 with a good driver, correct sprocket, sticky tyres, and a cold-weather session at Aamby Valley can realistically hit 15.0–15.2 seconds — a meaningful improvement over the stock 15.8–16.2s.',
  },
  {
    type: 'h2',
    text: 'Conditions Matter More Than You Think',
  },
  {
    type: 'p',
    text: 'A 35°C day at a low-altitude strip versus a 20°C morning at 1,100 m density altitude can change your R15\'s ET by 0.3–0.5 seconds. Air density affects both engine power (less oxygen at altitude) and aerodynamic drag (lower drag at altitude — a net positive at DA >800 m). MotoQuant\'s location picker lets you input your strip conditions and see the exact impact.',
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
        return <p key={i} className="text-white/70 text-sm leading-relaxed mb-5">{block.text}</p>;
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
              <span key={t} className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide">{t}</span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Why Your R15 Won&apos;t Hit 14s (And What Will Actually Help)
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
            24 April 2026 · 10 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        <div className="max-w-2xl mx-auto mt-16 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Simulate your R15 setup</div>
            <div className="text-white/60 text-sm">Select the YZF-R15 V3 and try the sprocket mod in the parts builder. See the ET delta before you buy anything.</div>
          </div>
          <Link href="/simulator" className="shrink-0 px-5 py-2.5 bg-brand-orange text-black font-display font-bold rounded-lg text-sm hover:bg-brand-orangeLight transition-colors">Run sim →</Link>
        </div>
      </article>

      <SiteFooter />
    </div>
  );
}
