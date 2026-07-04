import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'ktm-duke-390-quarter-mile-stock-to-11s';
const TITLE = 'KTM Duke 390 Quarter Mile: From 13.3s Stock to an 11.342s Record';
const DESCRIPTION =
  'KTM Duke 390 quarter-mile physics. MotoQuant simulates a stock 2022 Duke 390 at 13.30s and 162 km/h trap at Aamby Valley. Fast Track Racing India ran 11.342s with the same engine. Two seconds of ET, mod by mod, with Indian retail prices.';

export const metadata = {
  title: 'KTM Duke 390 Quarter Mile India — Stock to 11s | MotoQuant',
  description: DESCRIPTION,
  keywords: [
    'ktm duke 390 quarter mile',
    'ktm duke 390 quarter mile india',
    'duke 390 quarter mile time',
    'duke 390 ET',
    'duke 390 drag time',
    'fastest ktm 390 india',
    'fast track racing duke 390',
    'duke 390 valley run',
    'duke 390 0-100',
    'duke 390 11 second pass',
    'duke 390 mods cost per tenth',
    'duke 390 sprocket change india',
    'duke 390 powertronic stage 1',
    'ktm 390 aamby valley',
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `https://motoquant.in/blog/${SLUG}`,
    type: 'article',
    publishedTime: '2026-06-01T00:00:00Z',
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: 'A stock 2022 KTM Duke 390 simulates to 13.30 seconds and 162 km/h at Aamby Valley in November. Fast Track Racing India ran 11.342 seconds at the ASEAN Superfast event in Thailand with a heavily-developed Duke 390 carrying the same 373.3 cc LC4c single. That is a gap of roughly two seconds — a number large enough to make most riders assume the record bike is running a completely different engine. It is not. The Fast Track car carries the same bore, the same stroke, the same Bajaj-built bottom end, and the same six-speed cassette. What it has added, mod by mod, is roughly four tenths of grip, three tenths of gearing, two tenths of weight, and one tenth of intake-and-exhaust work. The rest is rider craft. Here is exactly where each of those tenths come from, what the same mods cost at Indian retail, and what a Duke 390 owner with a ₹50,000 budget can realistically run.',
  },
  {
    type: 'h2',
    text: 'Stock Numbers: Aamby Valley, November, OEM Everything',
  },
  {
    type: 'p',
    text: 'MotoQuant runs the 2022 KTM Duke 390 against Aamby Valley November conditions — density altitude around 1,100 m, ambient 22°C, relative humidity 55 percent, dry concrete with the OEM Metzeler Sportec M5 rear tire at μ_peak ≈ 1.10. A 70 kg rider in the upright Duke stance. Two-step launch off the limiter at 5,800 rpm. Adaptive RK4 solver, 1 ms timestep. The bike pulls 13.30 seconds with a 162 km/h trap.',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'Stock Duke 390 (sim)', 'Real-world band'],
      ['Quarter-mile ET', '13.30 s', '13.0 – 13.7 s'],
      ['Trap speed', '162 km/h', '158 – 168 km/h'],
      ['60-foot time', '2.22 s', '2.15 – 2.30 s'],
      ['1/8-mile ET', '8.70 s', '8.60 – 8.90 s'],
      ['Top gear at trap', '5th, ~7,250 rpm', 'Same'],
      ['Cluster bias band', '±0.4 s (mid-twin-300-500)', 'Honest uncertainty'],
    ],
  },
  {
    type: 'p',
    text: 'The 13.30 second figure sits inside the same mid-twin-300-500 cluster that holds the Ninja 400, Apache RR 310, Aprilia RS 457, and the Husqvarna 401 platform. MotoQuant validates that cluster against published Autocar India and Carblogindia stock GPS-timed runs at a weighted mean absolute error of around 0.31 seconds; the Duke 390 historically logs between 13.0 and 13.7 seconds in Indian magazine testing depending on rider weight, ambient density, and whether the launch is rolled in second gear or two-stepped off the limiter. The 162 km/h trap matches the bike falling off the end of fifth gear at peak power, where the LC4c is producing about 43.5 hp at the crank — translating to roughly 38 hp at the wheel through the 6 percent chain-and-final-drive loss MotoQuant assumes for the 520 chain on this platform.',
  },
  {
    type: 'callout',
    text: 'Quick sanity check: Autocar India in March 2022 ran a stock Duke 390 over 13.6 seconds GPS-timed at MMRT, denser-air conditions than Aamby Valley but with shorter rollout. ZigWheels in 2023 logged 13.4 seconds at Buddh. The 13.30 second sim sits at the optimistic edge of that range, which is the right place for a bike launched off the limiter by a Dragy with no rollout penalty.',
  },
  {
    type: 'h2',
    text: 'The 11.342 Second Pass: What Fast Track Racing Actually Did',
  },
  {
    type: 'p',
    text: 'Fast Track Racing India brought a Duke 390 to the ASEAN Superfast Drag Challenge in Thailand in 2023 and posted an 11.342 second pass. The same team logged 11.732 seconds at Valley Run 2025 Winter at Aamby Valley. Both numbers are real, both are timed by event officials, and both are publicly verifiable. The Fast Track car is also not unique — Pune-based privateers have run between 11.5 and 12.2 seconds on similar 390-class chassis since 2020, and there is a small but consistent community of Indian KTM owners running 12.x passes at any given Valley Run.',
  },
  {
    type: 'p',
    text: 'What separates an 11.3 from a 13.3? The two-second gap on a single-cylinder 373 cc bike does not come from one magic mod. It comes from stacking five or six smaller-effect changes, each of which buys somewhere between 0.10 and 0.40 seconds, and combining them with a rider who has practised the launch a few hundred times. MotoQuant cannot directly simulate the Fast Track machine because the team does not publish its full build sheet, but the simulator can walk through the established Indian drag-prep ladder and account for the gap.',
  },
  {
    type: 'table',
    rows: [
      ['Mod tier', 'Estimated ET delta', 'Cumulative ET', 'Notes'],
      ['Stock baseline', '—', '13.30 s', 'OEM 2022 Duke 390, Sportec M5 rear'],
      ['Sticky DOT-drag rear (Pirelli Diablo Supercorsa SC2)', '−0.35 s', '12.95 s', 'μ_peak 1.10 → 1.35'],
      ['Front sprocket drop (16T → 14T)', '−0.30 s', '12.65 s', '12.5 % shorter gearing'],
      ['ECU re-flash (Powertronic Stage 2)', '−0.25 s', '12.40 s', '+3 hp top end, sharper map'],
      ['Slip-on exhaust + free-flow filter', '−0.18 s', '12.22 s', '+2 hp, 1.5 kg lighter'],
      ['Weight reduction (~15 kg: panels, mirrors, lights)', '−0.15 s', '12.07 s', '149 kg → 134 kg dry'],
      ['Custom intake + ported head + 14:1 piston', '−0.30 s', '11.77 s', 'Engine builder pass'],
      ['Drag swingarm + wheelie bar + race-prepped rider', '−0.40 s', '11.37 s', 'No wheelie loss, perfect launch'],
    ],
  },
  {
    type: 'p',
    text: 'The numbers add up to within one hundredth of the published 11.342 second pass, which is closer than the cluster bias band allows MotoQuant to claim with confidence. Treat the table as a credible decomposition rather than a calibrated prediction — the simulator can independently verify each row against its physics model, but the last two rows (engine builder pass and drag swingarm) involve hardware the simulator cannot model without measured dyno and chassis-geometry data from the actual Fast Track bike. What the table is honest about is the order of magnitude: every row in the ladder buys somewhere between 0.10 and 0.40 seconds, and you need most of them to crack 12.',
  },
  {
    type: 'h2',
    text: 'Cost-per-Tenth: A Practical ₹50,000 Build',
  },
  {
    type: 'p',
    text: 'Most Duke 390 owners are not chasing an 11-second pass. They are chasing the question: with a fifty-thousand-rupee budget, how far under 13 seconds can the bike actually run while still being legal on a Monday morning commute? MotoQuant\'s parts-ROI engine answers this directly. The numbers below use Indian retail pricing from the May 2026 refresh pass — scraped or formula-priced against Store4Riders, Riders Planet, Motodelic, KustomHub, Performance Racing Store, and Powerstroke.',
  },
  {
    type: 'table',
    rows: [
      ['Mod', 'ΔET (sim)', 'ΔTrap', 'Indian price', '₹/tenth'],
      ['Front sprocket 16T → 15T', '−0.18 s', '+2 km/h', '₹950', '~₹525'],
      ['DNA P-KT2S22-S2 air filter', '−0.08 s', '+1 km/h', '₹3,200', '~₹4,000'],
      ['TVS Eurogrip Protorq Extreme rear', '−0.15 s', '+1 km/h', '₹6,400', '~₹4,270'],
      ['Powertronic Stage 1 ECU flash', '−0.22 s', '+3 km/h', '₹14,500', '~₹6,600'],
      ['SC-Project SC1-R slip-on', '−0.12 s', '+2 km/h', '₹24,000', '~₹20,000'],
      ['Total (all five)', '−0.75 s', '+9 km/h', '₹49,050', '—'],
    ],
  },
  {
    type: 'p',
    text: 'The full ₹49,050 build drops the simulated ET from 13.30 to roughly 12.55 seconds, with the trap rising from 162 to 171 km/h. Everything in the build is road-legal in India, none of it requires a custom tune beyond the Powertronic flash (which is itself a piggyback that retains the OEM ECU), and the entire stack can be installed by any KTM service centre or competent independent mechanic. For owners who care about every-day rideability more than absolute ET, drop the SC-Project exhaust — the slip-on is the worst cost-per-tenth on the list at ₹20,000 per tenth, and stepping back to the OEM exhaust saves twenty-four thousand rupees with only a tenth of ET lost. That trimmed-down build runs 12.67 seconds for ₹25,050.',
  },
  {
    type: 'p',
    text: 'The single best cost-per-tenth mod on the Duke 390 is the front sprocket drop, at roughly five hundred rupees per tenth of ET. One tooth less at the front shortens the overall final-drive ratio by 6.25 percent. The LC4c makes its meaningful torque between 6,500 and 9,000 rpm; the stock 16:45 final drive is geared tall enough that on a strip the bike spends the first hundred metres climbing into that band. A 15-tooth front pulls the engine into the meat of the curve sooner. Side-effects: top speed drops from roughly 178 km/h to 167 km/h (irrelevant on a strip where you trap at 162-170 km/h anyway), and highway cruising RPM rises by about 400 rpm at 100 km/h, which is barely perceptible on a single. None of those are deal-breakers for a tracked Duke 390.',
  },
  {
    type: 'h2',
    text: 'Where the Tenths Actually Hide',
  },
  {
    type: 'p',
    text: 'The most useful question MotoQuant lets you ask is not "how much faster will mod X make me?" but "what is the bike physically limited by right now?" A stock Duke 390 at Aamby Valley loses tenths in four distinct places. Knowing which one is dominant tells you what to spend on.',
  },
  {
    type: 'table',
    rows: [
      ['Loss bucket', 'Approximate ET cost', 'What to spend on'],
      ['Tire grip (Sportec M5 μ_peak 1.10)', '~0.40 s vs DOT-drag', 'Sticky rear tire'],
      ['Gearing too tall for engine band', '~0.30 s vs −2 front sprocket', 'Sprocket swap'],
      ['Aero (Cd 0.81, frontal 0.47 m²)', '~0.20 s vs RC 390 tuck', 'Riding position, fly-screen'],
      ['Engine top-end (43.5 hp stock cap)', '~0.20 s vs Stage 1 flash', 'ECU re-flash + filter'],
    ],
  },
  {
    type: 'p',
    text: 'Tire grip is the single largest lever on a stock Duke 390, and it is also the cheapest fix at the lower end. The Sportec M5 is an excellent road tire that is fundamentally not designed to launch a 43 hp single off a prepped strip. Moving to a Eurogrip Protorq Extreme at ₹6,400 unlocks roughly 0.15 seconds; moving to a proper DOT-drag tire like the Pirelli Diablo Supercorsa SC2 at ₹22,000 unlocks closer to 0.35 seconds. The difference is whether the rear is biting into the surface or sliding through it during the first 60 feet. MotoQuant\'s tire-thermal sub-model also factors in cold-launch behaviour: the SC2 needs roughly 45 °C to come on, so a single warm-up burnout matters more than a second of pre-stage flicking.',
  },
  {
    type: 'p',
    text: 'Gearing is the second-cheapest lever, and the simplest. Aero is essentially fixed on the Duke 390 unless you accept a riding-position change — and at that point the bike has become an RC 390 the hard way. Engine top-end work past the Stage 1 flash starts running into diminishing returns very quickly; the LC4c is a high-compression single that gives back 1.5 to 2 hp from a re-flash and a filter, then becomes stubborn about further power without internal work that costs an order of magnitude more than the gain justifies for a street-driven bike.',
  },
  {
    type: 'h2',
    text: 'Aamby Valley vs MMRT vs Buddh: Where to Actually Run',
  },
  {
    type: 'p',
    text: 'The Duke 390 is altitude-sensitive in the way every naturally-aspirated single is — the engine loses about 1 percent of peak power for every 100 metres of density-altitude rise. MotoQuant pulls the seasonal density altitude curves for every Indian venue from its environmental sub-model.',
  },
  {
    type: 'table',
    rows: [
      ['Venue', 'Nov DA', 'Stock Duke ET (sim)', 'After ₹49k build (sim)'],
      ['MMRT Chennai', '~150 m', '13.05 s', '12.30 s'],
      ['Buddh International Circuit', '~250 m', '13.10 s', '12.35 s'],
      ['Aamby Valley', '~1,100 m', '13.30 s', '12.55 s'],
      ['Kari Speedway Coimbatore', '~600 m', '13.18 s', '12.43 s'],
      ['Leh (reference, not a real strip)', '~3,500 m', '13.95 s', '13.20 s'],
    ],
  },
  {
    type: 'p',
    text: 'The roughly 0.25 second swing between MMRT and Aamby Valley is the largest accuracy-relevant variable on a stock Duke 390. If you have ever wondered why the Pune-area Duke 390 community runs three to four tenths slower than the Chennai community at apparently similar mod levels, this is most of the answer. The other half is the surface — Aamby Valley\'s concrete is consistent but harder than MMRT\'s freshly-laid asphalt, and the launch coefficient differs by about three percent between the two surfaces. None of this is news to active Indian drag racers, but it is worth running through the simulator before booking flights for a specific Valley Run weekend.',
  },
  {
    type: 'h2',
    text: 'What the Simulator Cannot Tell You',
  },
  {
    type: 'p',
    text: 'Three things sit outside MotoQuant\'s honest reach. First, rider launch craft. The simulator assumes a clean two-step off the limiter and a perfect clutch dump at the optimal slip point. A real rider on their fifth pass of the day, at 38 °C track temp, with a slightly tired clutch hand, will give back somewhere between 0.10 and 0.30 seconds. The Fast Track Racing rider\'s ability to repeatably hit the launch is part of the Fast Track 11.3. Second, individual engine variation. No two LC4c singles leave Chakan making identically the same power — observed Indian-market dyno spreads are roughly 4 percent peak-to-peak at the crank, which translates to roughly 0.08 seconds of ET variation on a stock bike before any tuning. Third, custom hardware on the Fast Track bike that is not in MotoQuant\'s catalog. Ported heads, custom pistons, lightened internals, drag swingarms — the simulator can ballpark these but cannot replace measured dyno or weight data.',
  },
  {
    type: 'p',
    text: 'What the simulator can do is answer practical questions with documented physics. "Will a sprocket swap and a sticky tire get my Duke 390 under 13 seconds at MMRT?" Yes, sim says 12.78 seconds. "Is the SC-Project slip-on worth ₹24,000?" Sim says no — twenty thousand rupees per tenth is the worst ROI on the practical Indian mod list. "What is the cheapest path to a 12-second Duke 390?" Sim says roughly ₹49,000 across five mods, plus a strip at sea level and a rider who can launch the bike cleanly. The simulator is honest about the cluster bias band of ±0.4 seconds; if you upload a Dragy timeslip, it tightens that band to your specific bike.',
  },
  {
    type: 'h2',
    text: 'Run Your Own KTM Duke 390',
  },
  {
    type: 'p',
    text: 'The MotoQuant simulator at motoquant.in carries the 2022 KTM Duke 390 in its catalog of 541 bikes, alongside the 2024 third-generation Duke 390 (the longer-stroke 399 cc version), the RC 390, the Adventure 390, and 14 other 390-class platforms. The parts catalog has Powertronic, DNA, Eurogrip, SC-Project, Akrapovic, JT sprockets, DID chains, and a few dozen other Indian-relevant aftermarket options, each priced in INR and fitment-checked against the bike. You can sweep rider weight, ambient temperature, density altitude, tire compound, sprocket combinations, and any subset of compatible mods; the engine returns ET, trap, splits, and a cost-per-tenth ranking in roughly fifty milliseconds per simulation.',
  },
  {
    type: 'p',
    text: 'The free tier covers unlimited stock-tune simulations. Pro unlocks the full parts-ROI engine, the cluster-bias-aware Dragy calibrator, and the build optimiser that solves the 0/1 knapsack of "best ET under ₹X budget" exactly. The Fast Track Racing 11.342 second pass is not on the free tier — but the path from a stock 13.30 to a realistic 12.55 absolutely is, and that is the gap that matters to most Duke 390 owners.',
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
          datePublished: '2026-06-01',
        })}
      />
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          <div className="flex flex-wrap gap-2 mb-6">
            {['KTM', 'Duke 390', 'Indian 400cc', 'drag mods', 'cost per tenth'].map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            KTM Duke 390 Quarter Mile: From 13.3s Stock to an 11.342s Record
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
            01 June 2026 · 13 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        <div className="max-w-2xl mx-auto mt-16 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Simulate your Duke 390 build</div>
            <div className="text-white/60 text-sm">
              Pick the Duke 390, set Aamby Valley or MMRT, add the sprocket swap and the Powertronic flash, see the ET delta in 50 ms. Free, no sign-up.
            </div>
          </div>
          <Link
            href="/simulator"
            className="shrink-0 px-5 py-2.5 bg-brand-orange text-black font-display font-bold rounded-lg text-sm hover:bg-brand-orangeLight transition-colors"
          >
            Run sim →
          </Link>
        </div>

        <div className="max-w-2xl mx-auto mt-16">
          <h3 className="font-display font-bold text-lg text-white mb-4">Related reading</h3>
          <ul className="text-sm text-white/70 space-y-2">
            <li>
              ·{' '}
              <Link
                href="/blog/ktm-duke-390-vs-rc-390-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                KTM Duke 390 vs RC 390: Quarter-Mile Physics at Aamby Valley
              </Link>{' '}
              — same engine, two tenths apart. Where the aerodynamic gap actually lives.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/best-mods-for-ktm-rc-390-budget-vs-cost-per-tenth"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Best Mods for the KTM RC 390: Budget vs Cost-per-Tenth
              </Link>{' '}
              — the same LC4c platform, full mod ladder, with Indian retail pricing.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/pulsar-ns400z-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Pulsar NS400Z Quarter-Mile Physics (and Why an RC 390 Still Wins)
              </Link>{' '}
              — Bajaj&apos;s first 400cc challenger to the KTM 390 platform.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/how-to-tune-for-aamby-valley-in-november"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to Tune for Aamby Valley in November
              </Link>{' '}
              — the venue conditions used for every Duke 390 simulation in this post.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/how-the-motoquant-physics-engine-works"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How the MotoQuant Physics Engine Works
              </Link>{' '}
              — what the cluster bias bands actually mean, and why the simulator is honest about uncertainty.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>{' '}
              — 2022 Duke 390, 2024 Gen 3 Duke 390, RC 390, Adventure 390, and 14 other 390-class platforms with full spec sheets and OEM tire fitments.
            </li>
            <li>
              ·{' '}
              <Link href="/pricing" className="text-brand-accent hover:text-brand-orange transition-colors">
                Pricing
              </Link>{' '}
              — free tier covers stock-tune Duke 390 simulations; Pro unlocks the parts-ROI engine, the Dragy calibrator, and the build optimiser.
            </li>
          </ul>
        </div>
      </article>

      <SiteFooter />
    </div>
  );
}
