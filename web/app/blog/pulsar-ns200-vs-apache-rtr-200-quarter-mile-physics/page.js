import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics';
const TITLE = 'Pulsar NS200 vs Apache RTR 200 4V: Quarter-Mile Physics';
const DESCRIPTION =
  'Bajaj Pulsar NS200 vs TVS Apache RTR 200 4V quarter-mile comparison. MotoQuant simulates the NS200 at ~15.9s and the RTR 200 4V at ~16.4s under matched Indian strip conditions. Spec-by-spec physics breakdown plus cost-per-tenth on the top three mods for each.';

export const metadata = {
  title: 'Pulsar NS200 vs Apache RTR 200 4V Quarter-Mile (India) — MotoQuant',
  description: DESCRIPTION,
  keywords: [
    'pulsar ns200 vs apache rtr 200',
    'ns200 vs apache 200 drag',
    'pulsar ns200 quarter mile',
    'apache rtr 200 4v quarter mile',
    'ns200 vs rtr 200 4v drag race',
    'Indian 200cc drag',
    'best 200cc bike for drag india',
    'ns200 mods cost per tenth',
    'apache rtr 200 mods',
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `https://motoquant.in/blog/${SLUG}`,
    type: 'article',
    publishedTime: '2026-05-18T00:00:00Z',
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: 'The Bajaj Pulsar NS200 and the TVS Apache RTR 200 4V are the two bikes the 200cc Indian drag conversation refuses to stop arguing about. MotoQuant simulates the 2017+ NS200 at roughly 15.9 seconds and the 2016+ Apache RTR 200 4V at roughly 16.4 seconds under matched Aamby Valley November conditions — a half-second gap that maps almost exactly onto the 4 hp and 18 kg the bikes do not share. Here is where each one wins, where the simulator says the gap actually lives, and which three mods buy the most ET on each platform for under ₹15,000.',
  },
  {
    type: 'h2',
    text: 'The Two Bikes on Paper',
  },
  {
    type: 'p',
    text: 'Both bikes are 200cc liquid-cooled DOHC 4-valve singles built around a perimeter frame, a 17-inch wheel set, and a 5-speed gearbox. Both are tuned for everyday commuting first, weekend drag-strip second. The NS200 uses a 72 × 49 mm short-stroke layout licensed off the KTM 200 Duke architecture. The RTR 200 4V runs a 67 × 55.4 mm slightly longer-stroke single TVS developed in-house, with race-bred refinements like a slipper clutch (added 2018+) and a quicker-revving valvetrain.',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'Pulsar NS200 (2017+)', 'Apache RTR 200 4V (2016+)'],
      ['Displacement', '199 cc', '197 cc'],
      ['Bore × stroke', '72.0 × 49.0 mm', '67.0 × 55.4 mm'],
      ['Compression', '10.5:1', '10.8:1'],
      ['Peak power', '24.2 hp @ 9,000 rpm', '20.2 hp @ 8,500 rpm'],
      ['Peak torque', '18.3 Nm @ 6,500 rpm', '16.8 Nm @ 6,000 rpm'],
      ['Dry mass', '160 kg', '142 kg'],
      ['Gears', '5-speed', '5-speed'],
      ['Final drive', '16F / 48R, 520 chain', '16F / 48R, 520 chain'],
      ['1st-gear ratio', '3.083', '2.917'],
      ['5th-gear ratio', '0.971', '0.880'],
      ['Cd', '0.80', '0.81'],
      ['Frontal area', '0.47 m²', '0.45 m²'],
      ['Front tire', '100/70R17', '100/70R17'],
      ['Rear tire', '130/70R17', '130/70R17'],
    ],
  },
  {
    type: 'p',
    text: 'Two numbers in that table do most of the work. The NS200 has 4 hp more peak power and the Apache is 18 kg lighter. Power-to-weight on the NS200 is roughly 24.2 hp / 230 kg total (160 kg dry plus 70 kg rider) = 105 hp/tonne. On the Apache it is 20.2 hp / 212 kg = 95 hp/tonne. A naive power-to-weight calculation predicts the NS200 wins by about 0.4–0.5 seconds at the strip. That is roughly what the physics says too — but for different reasons than the spec sheet suggests.',
  },
  {
    type: 'h2',
    text: 'What MotoQuant Says: Stock Sim Numbers',
  },
  {
    type: 'p',
    text: 'Running both bikes through the simulator at matched Aamby Valley November conditions — density altitude near 1,100 m, 22°C ambient, dry concrete with stock MRF Nylogrip Zapper at μ_peak ≈ 1.05, 70 kg rider in stock tuck — produces the following stock-tune output:',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'NS200 (2017+)', 'Apache RTR 200 4V (2016+)'],
      ['Quarter-mile ET (sim)', '~15.9 s', '~16.4 s'],
      ['Trap speed', '~123 km/h', '~118 km/h'],
      ['60-foot time', '~2.55 s', '~2.65 s'],
      ['1/8-mile ET', '~10.3 s', '~10.6 s'],
      ['Top gear at trap', '5th, ~8,900 rpm', '5th, ~8,400 rpm'],
      ['Cluster bias band', '±0.5 s entry-200-300', '±0.5 s entry-200-300'],
    ],
  },
  {
    type: 'p',
    text: 'Both ETs sit inside the entry-200-300cc cluster bias band of about ±0.5 seconds — large enough that a single dragy timeslip from either bike could move the predicted number a tenth either way. The simulator is honest about that band. The relative ordering (NS200 ahead by roughly 0.5 s, trap speed ahead by 5 km/h) is stable across rider weight, ambient temperature, and density altitude sweeps. Real-world community-reported times for stock NS200s on Indian strips cluster around 15.5–16.2 s; stock RTR 200 4V times cluster around 16.0–16.8 s. The simulator lands inside both bands.',
  },
  {
    type: 'callout',
    text: 'These are stock-tune simulations on stock OEM rubber. A well-launched NS200 with sticky aftermarket rubber, a fresh chain, and a smooth rider can dip into the 15.2–15.4 second range. A similarly-prepared RTR 200 4V lands in the 15.7–16.0 range. The 0.5 second gap stays stable across mod tiers.',
  },
  {
    type: 'h2',
    text: 'Where the NS200 Wins: Top-End Pull',
  },
  {
    type: 'p',
    text: 'The NS200 has 4 more horsepower and they are all at the top of the rev range. Peak power lands at 9,000 rpm versus the Apache\'s 8,500 rpm, which means the NS200 spends more of the quarter-mile in the meat of its torque curve before each upshift. The taller 5th gear (0.971 vs 0.880) lets the NS200 hold engine speed closer to peak power at trap, where the Apache is already past its torque peak and pulling against drag.',
  },
  {
    type: 'p',
    text: 'In the simulator log, the gap opens up after the 1/8-mile mark. Through the first 60 feet both bikes are clutch-limited and within 0.1 s of each other — the Apache\'s 18 kg weight advantage actually puts it slightly ahead in the first 30 metres. From 60 feet to the 1/8-mile, the bikes run nearly even. From the 1/8-mile to the trap, the NS200 pulls roughly 0.4 s clear, mostly because its short-stroke 72 mm bore is happier above 7,500 rpm than the Apache\'s 55.4 mm stroke is.',
  },
  {
    type: 'p',
    text: 'The short-stroke geometry matters more than the spec sheet shows. A 72 × 49 mm bore-to-stroke ratio of 1.47:1 gives the NS200 piston a slower mean speed at any RPM than the Apache\'s 67 × 55.4 mm (ratio 1.21:1), which means less reciprocating friction loss at the top of the rev band. On a dyno chart the two look similar through 7,000 rpm; above 8,000 rpm the NS200 keeps pulling while the Apache starts to taper. On the strip, that taper costs about 0.3 s of ET on its own.',
  },
  {
    type: 'h2',
    text: 'Where the Apache Wins: Launch, Mass, and Slipper Clutch',
  },
  {
    type: 'p',
    text: 'The Apache RTR 200 4V is 18 kg lighter dry — roughly an 11 percent system-mass advantage when you add a 70 kg rider. That weight matters most in the first 60 feet, where the engine is fighting inertia and not yet making peak power. The simulator confirms this: at the 60-foot mark, the Apache is consistently a tenth ahead of the NS200 regardless of launch RPM.',
  },
  {
    type: 'p',
    text: 'TVS also added a slipper clutch to the RTR 200 4V starting with the 2018 BS-IV refresh — useful for downshift stability on a road bike, and a small but real consistency advantage at the strip because it lets a less-experienced rider launch closer to the engine\'s capability without bogging on engagement. The NS200 still uses a conventional multi-plate wet clutch in 2026 spec, and Bajaj has never offered a slipper option from the factory on the NS variant.',
  },
  {
    type: 'p',
    text: 'For a rider weighing under 65 kg on a tight Indian strip with a short shutdown area, the Apache is the more launch-friendly bike. For a heavier rider (75 kg plus) on a strip with a long run-off, the NS200\'s top-end advantage stretches the gap. The simulator captures both effects: drop the rider weight to 60 kg and the gap closes to 0.3 s. Raise rider weight to 85 kg and the gap opens to 0.7 s.',
  },
  {
    type: 'h2',
    text: 'Top Three Mods Per Bike, Ranked by Cost-Per-Tenth',
  },
  {
    type: 'p',
    text: 'Both bikes run 520-pitch chains and 17-inch wheels, so the parts catalogs overlap almost completely. MotoQuant\'s parts-ROI engine ranks the top three mods for each bike under ₹15,000 by ET delta per rupee. Cost-per-tenth figures are Indian retailer prices from the May 2026 pricing-refresh pass.',
  },
  {
    type: 'table',
    rows: [
      ['Mod', 'NS200 ΔET', 'Apache ΔET', 'Indian price', '₹/tenth (NS200)', '₹/tenth (Apache)'],
      ['Front sprocket drop (16F → 15F)', '~0.20 s', '~0.22 s', '₹900', '₹450', '₹410'],
      ['MRF Zapper FY1 / Pirelli Diablo Rosso II', '~0.18 s', '~0.20 s', '₹6,500', '₹3,600', '₹3,250'],
      ['K&N drop-in air filter', '~0.06 s', '~0.07 s', '₹4,300', '₹7,200', '₹6,100'],
      ['Akrapovic slip-on (NS200) / SC-Project (Apache)', '~0.10 s', '~0.12 s', '₹38,000–48,000', '₹38,000–48,000', '~₹38,000'],
      ['Powertronic ECU re-flash (Stage 1)', '~0.15 s', '~0.13 s', '₹14,500', '₹9,700', '₹11,200'],
    ],
  },
  {
    type: 'p',
    text: 'Two patterns stand out. First, the sprocket swap is the cheapest tenth on both bikes by a wide margin — under ₹1,000 for around 0.2 seconds of ET. On the NS200, dropping from 16F to 15F shortens overall gearing by 6.25 percent, which keeps the engine higher in the powerband through the 1st-to-3rd shift sequence. On the Apache, the same change buys slightly more ET because the bike\'s longer-stroke single is more torque-limited than power-limited in the lower gears. Second, the tire upgrade is the second-best buy on both platforms — Indian factory rubber is the limiting factor in launch traction, not engine power.',
  },
  {
    type: 'p',
    text: 'Third, the ECU re-flash buys more ET on the NS200 than on the Apache because the NS200\'s OEM map is more conservative at the top of the rev band. The Powertronic Stage 1 map for the NS200 unlocks roughly 1.5 hp at 8,500 rpm that the stock map deliberately tapers off. On the Apache the same flash buys closer to 1.0 hp because TVS already runs a more aggressive top-end map from the factory. The exhaust mod buys nearly identical gains on both bikes — both engines are restricted at the OEM end-can, both respond well to a free-flow slip-on.',
  },
  {
    type: 'callout',
    text: 'The total mod budget on the NS200 to drop from 15.9 s to roughly 15.0 s under matched conditions: ₹26,200 (sprocket + tire + ECU flash). On the Apache to drop from 16.4 s to roughly 15.5 s: ₹22,000 (sprocket + tire + ECU flash). Neither bike will hit 14s without forced induction.',
  },
  {
    type: 'h2',
    text: 'Where the Gap Stops Mattering',
  },
  {
    type: 'p',
    text: 'A half-second is meaningful at the bench and at a real Indian strip with a Dragy on the tank. It is also small enough to be inside the run-to-run variance of either bike across a five-run session. The simulator predicts a 0.5 s gap; the standard deviation of stock-NS200 strip times across a typical Pune meet is roughly 0.3 s, and the standard deviation of stock-Apache times is similar. That means on any given day, a well-launched Apache will beat a poorly-launched NS200 — and the spec-sheet gap will look smaller than the simulator predicts.',
  },
  {
    type: 'p',
    text: 'The simulator output is for matched conditions, matched rider weight, and a clean launch on both bikes. Real strip days bring rider variance, tire temperature variance, and chain wear variance, all of which contribute roughly ±0.15 s of noise to either platform. The honest summary: the NS200 is the faster 200cc bike on paper and in the sim, by about 0.5 s of ET and 5 km/h of trap. The Apache RTR 200 4V is the more launch-friendly bike, the lighter bike, and the slipper-clutch bike. Pick based on what you actually want to do with it, not on a number from an internet drag race video.',
  },
  {
    type: 'h2',
    text: 'Indian Aftermarket Reality',
  },
  {
    type: 'p',
    text: 'The NS200 has been on sale in India for fourteen years and the aftermarket reflects that. Powertronic, KustomHub, Red Rooster, and Big Bird all stock NS200-specific exhaust, ECU, and clutch parts at every price point from ₹2,000 commuter slip-ons up to ₹85,000 full-system Akrapovic kits. The Apache RTR 200 4V has been on sale for ten years and the aftermarket is narrower but deeper at the race-prep end — TVS Racing\'s own one-make Apache cup runs a parallel parts ecosystem from teams like Sparks Racing and Race Concepts that is genuinely competitive at the strip.',
  },
  {
    type: 'p',
    text: 'For a first-time buyer choosing between the two in 2026, ex-showroom pricing puts the NS200 at roughly ₹1.61 lakh and the Apache RTR 200 4V at roughly ₹1.49 lakh — the Apache is the cheaper bike by about ₹12,000. Service intervals are similar at 4,000-6,000 km on both. Fuel economy in normal use is roughly 35–40 km/l on the NS200 and 38–42 km/l on the Apache. Neither bike is set up for serious drag-strip duty out of the box; both reward the same first ₹15,000 of mod spend in the same way.',
  },
  {
    type: 'h2',
    text: 'Run Your Own Numbers',
  },
  {
    type: 'p',
    text: 'The honest answer to "Pulsar NS200 vs Apache RTR 200 4V, which is faster" is: the NS200 wins by about 0.5 seconds of ET under matched stock-tune conditions, the Apache wins on launch consistency and base weight, and the gap is inside the run-to-run variance both bikes show on a real Indian strip. Picked on top-end pull and trap speed, the NS200 is the better drag bike. Picked on launch composure and short-strip work, the Apache is the better drag bike. Picked on out-of-the-box value, the Apache is the cheaper entry point with a slipper clutch and 18 kg less mass to push.',
  },
  {
    type: 'p',
    text: 'The simulator at motoquant.in lets you sweep rider weight, ambient temperature, density altitude, tire choice, and the full Indian parts catalog on both bikes side-by-side. The two bikes share enough mod paths (same chain pitch, same wheel size, overlapping ECU re-flash options) that you can test the same build budget on both and see exactly which platform gives you more ET for the rupee.',
  },
  {
    type: 'p',
    text: 'Two final caveats. First, every number in this post is a stock-tune simulation under specific conditions inside the entry-200-300cc cluster bias band of ±0.5 s. A single instrumented Dragy timeslip from either bike at a real Indian strip would tighten the simulator\'s prediction by a meaningful margin — and we will pull that data in through the calibrator the moment we have it. Second, the Indian aftermarket pricing shifts every quarter; the parts-ROI engine pulls live retailer pricing where it can and falls back to formula-based landing-cost math (USD × 84 × 1.30 import duty × 1.18 GST + ₹1,500 freight) where it cannot.',
  },
];

function Prose({ content }) {
  return (
    <div className="max-w-2xl mx-auto">
      {content.map((block, i) => {
        if (block.type === 'h2') {
          return (
            <h2
              key={i}
              className="font-display font-bold text-2xl md:text-3xl text-white mt-12 mb-4 tracking-tight"
            >
              {block.text}
            </h2>
          );
        }
        if (block.type === 'lead') {
          return (
            <p
              key={i}
              className="text-lg text-white/80 leading-relaxed mb-8 font-light"
            >
              {block.text}
            </p>
          );
        }
        if (block.type === 'callout') {
          return (
            <div
              key={i}
              className="my-8 px-5 py-4 rounded-xl border-l-4 border-brand-orange bg-brand-orange/5"
            >
              <p className="text-sm text-white/80 leading-relaxed italic">{block.text}</p>
            </div>
          );
        }
        if (block.type === 'table') {
          const [header, ...rows] = block.rows;
          return (
            <div key={i} className="my-8 overflow-x-auto rounded-xl border border-white/10">
              <table className="w-full text-sm font-mono">
                <thead className="bg-white/5">
                  <tr>
                    {header.map((h, hi) => (
                      <th
                        key={hi}
                        className="px-4 py-3 text-left text-[11px] uppercase tracking-wider text-brand-orange font-display font-semibold"
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, ri) => (
                    <tr key={ri} className="border-t border-white/5">
                      {row.map((cell, ci) => (
                        <td key={ci} className="px-4 py-2.5 text-white/75">
                          {cell}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }
        return (
          <p key={i} className="text-white/70 text-sm leading-relaxed mb-5">
            {block.text}
          </p>
        );
      })}
    </div>
  );
}

export default function PostPage() {
  return (
    <div className="min-h-screen bg-black text-white">
      <StructuredData
        data={articleSchema({
          title: TITLE,
          description: DESCRIPTION,
          slug: SLUG,
          datePublished: '2026-05-18',
        })}
      />
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          <div className="flex flex-wrap gap-2 mb-6">
            {['Bajaj', 'Pulsar NS200', 'TVS', 'Apache RTR 200 4V', 'Indian 200cc', 'comparison'].map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Pulsar NS200 vs Apache RTR 200 4V: Which Wins the Quarter Mile?
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
            18 May 2026 · 11 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        <div className="max-w-2xl mx-auto mt-16 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Simulate NS200 vs Apache RTR 200 4V side-by-side</div>
            <div className="text-white/60 text-sm">Pick both bikes, swap mods, sweep rider weight and venue conditions, and see the ET delta before you spend a rupee.</div>
          </div>
          <Link href="/simulator" className="shrink-0 px-5 py-2.5 bg-brand-orange text-black font-display font-bold rounded-lg text-sm hover:bg-brand-orangeLight transition-colors">Run sim →</Link>
        </div>

        <div className="max-w-2xl mx-auto mt-16">
          <h3 className="font-display font-bold text-lg text-white mb-4">Related reading</h3>
          <ul className="text-sm text-white/70 space-y-2">
            <li>
              ·{' '}
              <Link href="/blog/why-your-r15-wont-hit-14s" className="text-brand-accent hover:text-brand-orange transition-colors">
                Why Your R15 Won&apos;t Hit 14s
              </Link>{' '}
              — the same gearing-and-traction problem one displacement class down. Most of the lessons port across.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/hero-xtreme-200s-4v-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                Hero Xtreme 200S 4V Quarter-Mile Physics
              </Link>{' '}
              — the third 200cc Indian commuter-sport, and why it sits further behind the NS200 and Apache than its spec sheet predicts.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/the-physics-of-a-perfect-launch" className="text-brand-accent hover:text-brand-orange transition-colors">
                The Physics of a Perfect Launch
              </Link>{' '}
              — clutch slip, weight transfer, and the first 60 feet where the Apache often beats the NS200.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-to-tune-for-aamby-valley-in-november" className="text-brand-accent hover:text-brand-orange transition-colors">
                How to Tune for Aamby Valley in November
              </Link>{' '}
              — the venue conditions used for the simulation in this post.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>{' '}
              — NS200, RS200, RTR 200 4V, RTR 160 4V, and 330+ other bikes with full spec sheets and OEM tire fitments.
            </li>
            <li>
              ·{' '}
              <Link href="/pricing" className="text-brand-accent hover:text-brand-orange transition-colors">
                Pricing
              </Link>{' '}
              — free tier covers stock-tune sims on either bike; Pro adds the full parts-ROI engine and Dragy timeslip calibration.
            </li>
          </ul>
        </div>
      </article>

      <SiteFooter />
    </div>
  );
}
