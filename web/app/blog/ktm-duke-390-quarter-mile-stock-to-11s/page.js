import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'ktm-duke-390-quarter-mile-stock-to-11s';
const TITLE = 'KTM Duke 390 quarter mile: from 13.3s stock to an 11.342s record';
const DESCRIPTION =
  'KTM Duke 390 quarter-mile physics. MotoQuant simulates a stock 2022 Duke 390 at 13.30s and 162 km/h trap at Aamby Valley. Fast Track Racing India ran 11.342s with the same engine. Two seconds of ET, mod by mod, with Indian retail prices.';

export const metadata = {
  title: 'KTM Duke 390 quarter mile in India: stock to 11s | MotoQuant',
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
    text: 'A stock 2022 KTM Duke 390 simulates to 13.30 seconds and 162 km/h at Aamby Valley in November. Fast Track Racing India ran 11.342 seconds at the ASEAN Superfast event in Thailand on a heavily developed Duke 390 with the same 373.3 cc LC4c single. A gap of roughly two seconds makes most riders assume the record bike has a different engine. It does not. The Fast Track bike has the same bore, the same stroke, the same Bajaj-built bottom end and the same six-speed cassette. Mod by mod, it has added roughly four tenths of grip, three tenths of gearing, two tenths of weight and one tenth of intake and exhaust work. The rest is rider craft. This post traces each of those tenths, prices the same mods at Indian retail, and works out what a Duke 390 owner with a ₹50,000 budget can realistically run.',
  },
  {
    type: 'h2',
    text: 'Stock numbers: Aamby Valley, November, OEM everything',
  },
  {
    type: 'p',
    text: 'MotoQuant runs the 2022 KTM Duke 390 at 13.30 seconds with a 162 km/h trap under Aamby Valley November conditions: density altitude around 1,100 m, ambient 22°C, relative humidity 40 percent, and dry asphalt with the OEM Metzeler Sportec M5 rear tire at μ_peak ≈ 1.10. The 70 kg rider sits in the upright Duke stance. The launch is a two-step off the limiter at 5,800 rpm, and the solver is adaptive RK4 with a 1 ms timestep.',
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
      ['Cluster bias band', '±0.4 s (mid-twin-300-500)', 'Model uncertainty'],
    ],
  },
  {
    type: 'p',
    text: 'The Duke 390 sits in the mid-twin-300-500 cluster, with the Ninja 400, Apache RR 310, Aprilia RS 457 and the Husqvarna 401 platform. MotoQuant validates that cluster against published stock GPS-timed runs from Autocar India and Carblogindia, at a weighted mean absolute error of around 0.31 seconds. In Indian magazine testing the Duke 390 has logged between 13.0 and 13.7 seconds, depending on rider weight, ambient density, and whether the launch is rolled in second gear or two-stepped off the limiter. The 162 km/h trap is where the bike runs off the end of fifth gear at peak power. There the LC4c makes about 43.5 hp at the crank, or roughly 38 hp at the wheel after the 6 percent chain and final-drive loss MotoQuant assumes for the 520 chain on this platform.',
  },
  {
    type: 'callout',
    text: 'A sanity check: in March 2022 Autocar India ran a stock Duke 390 at over 13.6 seconds, GPS-timed at MMRT, in denser air than Aamby Valley but with shorter rollout. ZigWheels logged 13.4 seconds at Buddh in 2023. The 13.30 second sim sits at the optimistic edge of that range, which is where it should be for a bike launched off the limiter and timed by a Dragy with no rollout penalty.',
  },
  {
    type: 'h2',
    text: 'The 11.342 second pass: what Fast Track Racing did',
  },
  {
    type: 'p',
    text: 'Fast Track Racing India brought a Duke 390 to the ASEAN Superfast Drag Challenge in Thailand in 2023 and posted an 11.342 second pass. The same team logged 11.732 seconds at Valley Run 2025 Winter at Aamby Valley. Event officials timed both runs, and both are publicly verifiable. The Fast Track bike is not unique either. Pune-based privateers have run between 11.5 and 12.2 seconds on similar 390-class chassis since 2020, and a small, steady group of Indian KTM owners runs 12.x passes at any given Valley Run.',
  },
  {
    type: 'p',
    text: 'On a 373 cc single, the two seconds between an 11.3 and a 13.3 do not come from one magic mod. They come from five or six smaller changes, each worth between 0.10 and 0.40 seconds, plus a rider who has practised the launch a few hundred times. The team does not publish its full build sheet, so MotoQuant cannot simulate the Fast Track bike directly. It can walk through the usual Indian drag-prep ladder and account for the gap.',
  },
  {
    type: 'table',
    rows: [
      ['Mod tier', 'Estimated ET delta', 'Cumulative ET', 'Notes'],
      ['Stock baseline', '–', '13.30 s', 'OEM 2022 Duke 390, Sportec M5 rear'],
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
    text: 'The numbers add up to within one hundredth of the published 11.342 second pass, which is closer than the cluster bias band lets MotoQuant claim with confidence. Read the table as a credible breakdown, not a calibrated prediction. The simulator can verify each row against its physics model, but the last two rows (engine builder pass and drag swingarm) involve hardware it cannot model without measured dyno and chassis-geometry data from the Fast Track bike itself. The order of magnitude is the solid part: every row in the ladder buys between 0.10 and 0.40 seconds, and you need most of them to crack 12.',
  },
  {
    type: 'h2',
    text: 'Cost per tenth: a practical ₹50,000 build',
  },
  {
    type: 'p',
    text: 'Most Duke 390 owners are not chasing an 11-second pass. Their question is this: with a fifty-thousand-rupee budget, how far under 13 seconds can the bike run and still be legal for the Monday morning commute? MotoQuant\'s parts-ROI engine answers it. The prices below are Indian retail from the May 2026 refresh, scraped or formula-priced against Store4Riders, Riders Planet, Motodelic, KustomHub, Performance Racing Store, and Powerstroke.',
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
      ['Total (all five)', '−0.75 s', '+9 km/h', '₹49,050', '–'],
    ],
  },
  {
    type: 'p',
    text: 'The full ₹49,050 build takes the simulated ET from 13.30 to roughly 12.55 seconds and the trap from 162 to 171 km/h. Everything in it is road-legal in India. Nothing needs a custom tune beyond the Powertronic flash, which is a piggyback that keeps the OEM ECU, and any KTM service centre or competent independent mechanic can fit the lot. If you care more about everyday rideability than absolute ET, drop the SC-Project exhaust. At ₹20,000 per tenth it is the worst cost per tenth on the list, and going back to the OEM exhaust saves twenty-four thousand rupees and loses only a tenth of ET. That trimmed build runs 12.67 seconds for ₹25,050.',
  },
  {
    type: 'p',
    text: 'The best cost-per-tenth mod on the Duke 390 is the front sprocket drop, at roughly five hundred rupees per tenth of ET. One tooth less at the front shortens the overall final-drive ratio by 6.25 percent. The LC4c makes its useful torque between 6,500 and 9,000 rpm, and the stock 16:45 final drive is tall enough that on a strip the bike spends the first hundred metres climbing into that band. A 15-tooth front sprocket gets the engine into the meat of the curve sooner. There are two costs. Top speed drops from roughly 178 km/h to 167 km/h, which does not matter on a strip where you trap at 162-170 km/h. Highway cruising revs rise by about 400 rpm at 100 km/h, which you will barely feel on a single. Neither is a deal-breaker for a Duke 390 that goes to the strip.',
  },
  {
    type: 'h2',
    text: 'Where the tenths hide',
  },
  {
    type: 'p',
    text: 'A more useful question than "how much faster will mod X make me?" is "what limits the bike right now?" A stock Duke 390 at Aamby Valley loses tenths in four places, and the biggest one tells you what to spend on.',
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
    text: 'Tire grip is the largest lever on a stock Duke 390, and at the low end it is also the cheapest fix. The Sportec M5 is an excellent road tire, but it was not designed to launch a 43 hp single off a prepped strip. A Eurogrip Protorq Extreme at ₹6,400 is worth roughly 0.15 seconds; a proper DOT-drag tire like the Pirelli Diablo Supercorsa SC2 at ₹22,000 is worth closer to 0.35 seconds. The difference is whether the rear bites into the surface or slides over it in the first 60 feet. MotoQuant\'s tire-thermal sub-model also covers cold launches: the SC2 needs roughly 45 °C to come on, so one warm-up burnout matters more than a second of pre-stage flicking.',
  },
  {
    type: 'p',
    text: 'Gearing is the second-cheapest lever, and the simplest. Aero is more or less fixed on the Duke 390 unless you change the riding position, and then you have built an RC 390 the hard way. Engine work past the Stage 1 flash hits diminishing returns quickly. The LC4c is a high-compression single that gives 1.5 to 2 hp from a re-flash and a filter. After that, more power needs internal work that costs an order of magnitude more than the gain is worth on a street bike.',
  },
  {
    type: 'h2',
    text: 'Aamby Valley vs MMRT vs Buddh: where to run',
  },
  {
    type: 'p',
    text: 'Like every naturally aspirated single, the Duke 390 is sensitive to altitude: the engine loses about 1 percent of peak power for every 100 metres of density-altitude rise. MotoQuant takes the seasonal density-altitude curve for each Indian venue from its environmental sub-model.',
  },
  {
    type: 'table',
    rows: [
      ['Venue', 'Nov DA', 'Stock Duke ET (sim)', 'After ₹49k build (sim)'],
      ['MMRT Chennai', '~600 m', '13.05 s', '12.30 s'],
      ['Buddh International Circuit', '~490 m', '13.10 s', '12.35 s'],
      ['Aamby Valley', '~1,120 m', '13.30 s', '12.55 s'],
      ['Kari Speedway Coimbatore', '~790 m', '13.18 s', '12.43 s'],
      ['Leh (reference, not a real strip)', '~3,500 m', '13.95 s', '13.20 s'],
    ],
  },
  {
    type: 'p',
    text: 'The times in this table come from the engine as it stood in May 2026; the DA column uses the current catalog\'s November normals. On the current engine a stock 2017-2023 Duke 390 is 0.19 s quicker at MMRT than at Aamby Valley in November, and BIC edges MMRT because of MMRT\'s humidity (see the venue comparison post). That swing of roughly 0.2 seconds between MMRT and Aamby Valley is the largest accuracy-relevant variable on a stock Duke 390. It is a large part of why the Pune-area Duke 390 community runs three to four tenths slower than Chennai riders at what look like similar mod levels. Active Indian drag racers know this already, but run it through the simulator before you book flights for a Valley Run weekend.',
  },
  {
    type: 'h2',
    text: 'What the simulator cannot tell you',
  },
  {
    type: 'p',
    text: 'Three things are outside what MotoQuant can model with confidence. The first is rider launch craft. The simulator assumes a clean two-step off the limiter and a perfect clutch dump at the best slip point. A real rider on the fifth pass of the day, at 38 °C track temperature, with a slightly tired clutch hand, will give back between 0.10 and 0.30 seconds. Part of the Fast Track 11.3 is their rider hitting that launch again and again. The second is engine-to-engine variation. No two LC4c singles leave Chakan making exactly the same power. Observed Indian-market dyno spreads are roughly 4 percent peak-to-peak at the crank, or roughly 0.08 seconds of ET on a stock bike before any tuning. The third is custom hardware on the Fast Track bike that is not in MotoQuant\'s catalog: ported heads, custom pistons, lightened internals, drag swingarms. The simulator can ballpark these, but it cannot replace measured dyno or weight data.',
  },
  {
    type: 'p',
    text: 'What the simulator can do is answer practical questions with documented physics. "Will a sprocket swap and a sticky tire get my Duke 390 under 13 seconds at MMRT?" Yes: the sim says 12.78 seconds. "Is the SC-Project slip-on worth ₹24,000?" The sim says no, because twenty thousand rupees per tenth is the worst ROI on the practical Indian mod list. "What is the cheapest path to a 12-second Duke 390?" Roughly ₹49,000 across five mods, plus a strip at sea level and a rider who can launch the bike cleanly. The cluster bias band is ±0.4 seconds. If you have a Dragy timeslip, send it through the "Submit a timeslip" form; a reviewed run joins the benchmark set.',
  },
  {
    type: 'h2',
    text: 'Run your own KTM Duke 390',
  },
  {
    type: 'p',
    text: 'The simulator at motoquant.in has the 2022 KTM Duke 390 in its catalog of 534 bikes, along with the 2024 third-generation Duke 390 (the longer-stroke 399 cc version), the RC 390, the Adventure 390 and 14 other 390-class platforms. The parts catalog has Powertronic, DNA, Eurogrip, SC-Project, Akrapovic, JT sprockets, DID chains and a few dozen other aftermarket options for Indian riders, each priced in INR and checked for fitment against the bike. You can vary rider weight, ambient temperature, density altitude, tire compound, sprocket combination and any set of compatible mods. Each simulation returns ET, trap, splits and a cost-per-tenth ranking in roughly fifty milliseconds.',
  },
  {
    type: 'p',
    text: 'MotoQuant is free and open source, including the full parts-ROI engine and the build optimiser, which solves the 0/1 knapsack of "best ET under ₹X budget" exactly. A stock-plus-bolt-ons build will not reach the Fast Track Racing 11.342 second pass. It can get from a stock 13.30 to a realistic 12.55, and that is the gap most Duke 390 owners care about.',
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
                        className="px-4 py-3 text-left text-xs text-accent font-display font-semibold whitespace-nowrap"
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
          <p key={i} className="text-white/75 text-base leading-relaxed mb-5">
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
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            KTM Duke 390 quarter mile: from 13.3s stock to an 11.342s record
          </h1>
          <div className="text-sm text-white/60 mb-12">
            01 June 2026 · 13 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        <div className="max-w-2xl mx-auto mt-16 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Simulate your Duke 390 build</div>
            <div className="text-white/60 text-sm">
              Pick the Duke 390, set Aamby Valley or MMRT, add the sprocket swap and the Powertronic flash, and see the ET change in 50 ms. Free, no sign-up.
            </div>
          </div>
          <Link
            href="/simulator"
            className="shrink-0 px-5 py-2.5 bg-brand-orange text-on-accent font-display font-bold rounded-lg text-sm hover:bg-brand-orangeLight transition-colors"
          >
            Open the simulator →
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
              </Link>:{' '}
              same engine, two tenths apart, and where the aerodynamic gap comes from.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/best-mods-for-ktm-rc-390-budget-vs-cost-per-tenth"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Best Mods for the KTM RC 390: Budget vs Cost-per-Tenth
              </Link>:{' '}
              the same LC4c platform, full mod ladder, with Indian retail pricing.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/pulsar-ns400z-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Pulsar NS400Z Quarter-Mile Physics (and Why an RC 390 Still Wins)
              </Link>:{' '}
              Bajaj&apos;s first 400cc challenger to the KTM 390 platform.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/how-to-tune-for-aamby-valley-in-november"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to Tune for Aamby Valley in November
              </Link>:{' '}
              the venue conditions used for every Duke 390 simulation in this post.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/how-the-motoquant-physics-engine-works"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How the MotoQuant Physics Engine Works
              </Link>:{' '}
              what the cluster bias bands mean, and how the simulator reports its uncertainty.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>:{' '}
              2022 Duke 390, 2024 Gen 3 Duke 390, RC 390, Adventure 390, and 14 other 390-class platforms with full spec sheets and OEM tire fitments.
            </li>
          </ul>
        </div>
      </article>

      <SiteFooter />
    </div>
  );
}
