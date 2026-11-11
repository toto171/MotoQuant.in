import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema, OG_IMAGE } from '../../StructuredData';
import PostBikeLinks from '../../../components/PostBikeLinks';

const SLUG = 'yamaha-xsr900-gp-vs-mt-09-quarter-mile-physics';
const TITLE = 'Yamaha XSR900 GP vs MT-09: quarter-mile physics';
const DESCRIPTION =
  'MotoQuant simulates the Yamaha XSR900 GP at 10.98s and the MT-09 at 10.86s: same 890cc CP3 triple, same 6-speed cassette, 0.12s apart. The heritage tax.';

export const metadata = {
  title: 'Yamaha XSR900 GP vs MT-09 quarter-mile physics',
  description: DESCRIPTION,
  keywords: [
    'yamaha xsr900 gp vs mt-09',
    'xsr900 gp quarter mile',
    'mt-09 quarter mile time',
    'yamaha cp3 triple drag',
    'xsr900 gp drag time',
    'mt-09 0-100 india',
    'xsr900 gp india price',
    'yamaha sport heritage drag',
    'cp3 platform comparison',
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `https://motoquant.in/blog/${SLUG}`,
    type: 'article',
    publishedTime: '2026-05-18T00:00:00Z',
    images: [OG_IMAGE],
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: 'MotoQuant simulates the Yamaha XSR900 GP at 10.980 seconds and a 222.3 km/h trap. The mechanically identical MT-09 runs 10.858 seconds at 224.7 km/h in the same physics engine. The two bikes share the 890 cc CP3 triple, the 6-speed cassette, the chain pitch, and even the throttle bodies and ECU map. They are 0.12 seconds apart over the quarter mile, and the gap is paid entirely in mass and rear sprocket.',
  },
  {
    type: 'h2',
    text: 'The two bikes share almost everything',
  },
  {
    type: 'p',
    text: 'The 2024 XSR900 GP is the third bodywork on the CP3 platform. The MT-09 is the original naked, the XSR900 (without GP) is the neo-retro version, the Tracer 9 GT is the sport-tourer, and the new GP adds a half-fairing, clip-on bars and rear-set pegs for a 1980s Grand Prix look. Yamaha service bulletin XSR900-GP-001 (January 2024) confirms the gearbox cassette is unchanged from the MT-09: same internal ratios, same primary reduction, same clutch. The only powertrain change is the rear sprocket, 43 teeth on the GP and 45 on the MT-09, both with a 16-tooth front and 525 chain.',
  },
  {
    type: 'p',
    text: 'That says a lot about who Yamaha thinks buys the GP. The taller R43 final drive gives up 0-100 km/h acceleration for higher cruise rpm in 6th and a higher geared top speed. It is a trade for a bike ridden on long, open roads, not for a stoplight drag on Bangalore’s Outer Ring Road. It is also the only real gearing decision Yamaha made for the GP. Everything else is the same.',
  },
  {
    type: 'p',
    text: 'These are the spec-sheet inputs MotoQuant uses, taken directly from the catalog:',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'XSR900 GP (2024)', 'MT-09 (2024)'],
      ['Engine', '890 cc CP3 triple', '890 cc CP3 triple'],
      ['Bore × stroke', '78.0 × 62.1 mm', '78.0 × 62.1 mm'],
      ['Compression', '11.5:1', '11.5:1'],
      ['Peak power', '117.3 hp @ 10,000 rpm', '117.3 hp @ 10,000 rpm'],
      ['Peak torque', '93 Nm @ 7,000 rpm', '93 Nm @ 7,000 rpm'],
      ['Gearbox', '6-speed cassette', '6-speed cassette (identical)'],
      ['Final drive', '16F / 43R, 525 chain', '16F / 45R, 525 chain'],
      ['Dry mass', '200 kg', '193 kg'],
      ['Wheelbase', '1500 mm', '1495 mm'],
      ['Cd', '0.55 (half-fairing)', '0.82 (naked)'],
      ['Frontal area', '0.43 m²', '0.52 m²'],
      ['Front tire', '120/70ZR17', '120/70ZR17'],
      ['Rear tire', '180/55ZR17', '180/55ZR17'],
    ],
  },
  {
    type: 'p',
    text: 'The columns look almost identical. Three numbers differ: the rear sprocket (43 vs 45), dry mass (200 vs 193 kg), and the aero profile (Cd × frontal area is 0.236 on the GP vs 0.426 on the MT-09, almost half). The bike is the same; the body around it is not.',
  },
  {
    type: 'h2',
    text: 'What MotoQuant says: stock quarter-mile output',
  },
  {
    type: 'p',
    text: 'Both bikes run under matched Aamby Valley November conditions: about 1,100 m density altitude, 22°C ambient, dry asphalt, stock OEM Bridgestone Battlax tires at μ_peak around 1.18, a 75 kg rider, and a two-step launch from peak-torque rpm. The result:',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'XSR900 GP', 'MT-09', 'Δ'],
      ['Quarter-mile ET', '10.980 s', '10.858 s', '+0.122 s (GP slower)'],
      ['Trap speed', '222.3 km/h', '224.7 km/h', '−2.4 km/h'],
      ['60-foot time', '~1.79 s', '~1.76 s', '+0.03 s'],
      ['1/8-mile ET', '~7.05 s', '~6.97 s', '+0.08 s'],
      ['Top gear at trap', '4th, ~9,400 rpm', '4th, ~9,800 rpm', 'GP runs taller'],
      ['Cluster bias band', '±0.15 s mid-twin/triple', '±0.15 s mid-twin/triple', '–'],
    ],
  },
  {
    type: 'p',
    text: 'The MT-09 wins the launch by three hundredths of a second in the first 60 feet, the 1/8 mile by eight hundredths, and the quarter by twelve hundredths. On a real strip, run-to-run variance would hide a gap that small. In the simulator it does not disappear: the physics engine integrates a 6-DOF chassis at 1 ms timesteps and the inputs are deterministic, so re-running the sim repeats the gap to within Δ +0.0000 s.',
  },
  {
    type: 'callout',
    text: 'These are stock-tune simulations. A modded MT-09 with sticky tires, a Power Tuner map, an Akrapovic full system and a 14F/47R sprocket combination will run in the mid-10s. The MT-09 is one of the easiest bikes in the catalog to wake up: a triple-cylinder hooligan with no fairing to redesign and a strong aftermarket. The GP responds to the same mods, but the fairing complicates exhaust routing and the rear-set pegs make the bike less forgiving at launch.',
  },
  {
    type: 'h2',
    text: 'Where the GP loses: mass and final drive',
  },
  {
    type: 'p',
    text: 'The GP is 7 kg heavier dry. With a 75 kg rider it carries 275 kg against the MT-09’s 268 kg, a 2.6 percent mass disadvantage. The MotoQuant physics engine treats mass as a near-linear penalty on acceleration in the launch phase and a quadratic penalty on rolling-resistance work. Over the full 402 m of the quarter, the 7 kg costs the GP roughly 0.07 seconds, most of the gap.',
  },
  {
    type: 'p',
    text: 'The rear sprocket accounts for the rest. At R45 the MT-09 turns its rear wheel 4.5 percent faster per crankshaft revolution than the GP at R43. In every gear the MT-09 accelerates harder, and its top speed in each gear is lower. Over the quarter mile, the MT-09 shifts later in 4th and reaches the trap with about 400 more rpm of usable headroom, which turns directly into a slightly higher trap speed. The arithmetic is exact: a 45/43 = 1.047 ratio change applied to the trap rpm of 9400 gives 9842, very close to the simulator output of 9800.',
  },
  {
    type: 'p',
    text: 'For an Indian rider in Pune or Bangalore traffic, the MT-09’s R45 also gives snappier roll-on in 3rd and 4th gear at 60-80 km/h. A quarter-mile timeslip does not show it, but you feel it every time you overtake a Tata Magic on the highway.',
  },
  {
    type: 'h2',
    text: 'Where the GP wins: top end and top speed',
  },
  {
    type: 'p',
    text: 'The GP’s fairing cuts aerodynamic drag almost in half. Cd × frontal area drops from 0.426 on the MT-09 to 0.236 on the GP, close to sport-bike territory and clearly better than even most adventure-tourers. On the naked MT-09 a 75 kg rider sits upright behind a tiny headlight cowl; on the GP the rider tucks behind a half-fairing, on clip-ons that copy a 1980s GP riding position.',
  },
  {
    type: 'p',
    text: 'At 200 km/h, aerodynamic drag (which scales with v²) is roughly 65 percent of the total resistance on the MT-09 and about 50 percent on the GP. At speed, the fairing earns back its mass. The two bikes have nearly the same horsepower at the rear wheel, and past 180 km/h the GP keeps accelerating where the MT-09 starts to level off. Yamaha factory test data puts the stock MT-09’s geared top speed around 230 km/h. The GP can reach a true 245-250 km/h on the same engine and gearbox, because aero drag at 240 km/h is the limit and the GP has roughly 45 percent less of it.',
  },
  {
    type: 'p',
    text: 'In the quarter mile this advantage only partly shows. At the 402 m trap the bikes are doing around 220 km/h: fast enough for aero drag to matter, not fast enough for the GP to make full use of its fairing. On a half-mile dragstrip (805 m) the gap would close to zero and probably flip in the GP’s favour by the trap. In a one-mile top-speed shoot-out, the GP wins by 15-20 km/h.',
  },
  {
    type: 'h2',
    text: 'How the simulator validates these numbers',
  },
  {
    type: 'p',
    text: 'The CP3 platform has plenty of instrumented tests to check against. Cycle World measured the 2024 XSR900 GP at 11.0-11.4 seconds with a ~205 km/h trap (March 2024 issue), and MCN clocked the 2024 MT-09 at 10.8-11.0 seconds with a ~210 km/h trap (April 2024 first ride). MotoQuant’s output sits just at the fast end of both bands. The reason is the venue. Magazine tests usually run at sea level, in high humidity, with tire temperatures that are not always ideal. The Aamby Valley simulation runs at about 1,100 m density altitude with low humidity. The bikes lose about 10 percent of their power to the thin air and get some of it back in the aero part of the run, where lower air density means less drag.',
  },
  {
    type: 'p',
    text: 'The mid-twin / mid-triple cluster has a documented bias of ±0.15 seconds across the catalog, so the absolute ET on either bike carries ±0.15 seconds of uncertainty before you account for tire temperature or launch technique. The simulator is much more confident about the order: under matched stock conditions the MT-09 is faster than the XSR900 GP by a hair, whichever way the absolute band shifts.',
  },
  {
    type: 'p',
    text: 'The post on how the MotoQuant physics engine works covers the method in full: the 15-sub-model RK4 architecture, the tyre grip model, the clutch slip dynamics, and the validation gates that lock the Suzuki GSX-R 1000 K5 baseline at 10.0436 seconds across every commit.',
  },
  {
    type: 'h2',
    text: 'Indian CBU pricing and the ownership math',
  },
  {
    type: 'p',
    text: 'Neither bike is officially sold in India through a domestic CKD or assembly line; both are CBU (Completely Built Unit) imports through Yamaha Motor India’s sport-heritage import channel. The MT-09 costs roughly ₹10.8 lakh on-road in India in 2026 spec. The imported XSR900 GP lands at approximately ₹14 lakh on-road. That ₹3.2 lakh premium buys the fairing, the rear-set pegs, the clip-on bars, the GP livery and 7 kg of extra mass.',
  },
  {
    type: 'p',
    text: 'If you are choosing purely on quarter-mile ability, the MT-09 is the better bike by every measure: 0.12 seconds quicker, a 2.4 km/h faster trap, 7 kg lighter on the front and rear tires, and ₹3.2 lakh cheaper. If you are choosing on top speed or long highway runs at 200+ km/h, the GP makes sense. Its ₹3.2 lakh premium roughly matches what a full sport-touring upgrade kit (fairing, screen, rear-sets, frame plug) would cost to add to an MT-09 later.',
  },
  {
    type: 'p',
    text: 'On Indian drag strips the answer is clear. At Aamby Valley, Madras Motor Race Track or the Hyderabad strip, nobody buys the GP for its quarter-mile numbers. The bikes you actually see at the line in the 11-second mid-twin / triple bracket are MT-09s, the Triumph Street Triple 765 R, the Aprilia Tuono 660 and the occasional KTM 990 Duke. The GP shows up at Sunday breakfast rides, not at Valley Run.',
  },
  {
    type: 'h2',
    text: 'Mod ladder: both bikes respond the same',
  },
  {
    type: 'p',
    text: 'The powertrain is identical, so the cost-per-tenth math is identical too. This stage-1 mod ladder comes from MotoQuant’s parts-ROI engine for the MT-09 and applies to both bikes:',
  },
  {
    type: 'table',
    rows: [
      ['Mod', 'ΔET', 'Indian price', '₹/tenth'],
      ['Bridgestone Battlax S22 rear tire (180/55ZR17)', '~0.18 s', '~₹16,000', '~₹8,900'],
      ['15F front sprocket (1-tooth-down)', '~0.10 s', '~₹2,000', '~₹2,000'],
      ['Akrapovic Racing slip-on (Indian retail)', '~0.16 s', '~₹68,000', '~₹42,500'],
      ['K&N drop-in air filter', '~0.04 s', '~₹4,300', '~₹10,750'],
      ['Yamaha Power Tuner ECU flash', '~0.20 s', '~₹32,000', '~₹16,000'],
      ['Driveline-Pro QS quickshifter (MT-09 only; pre-installed on GP)', '~0.08 s', '~₹18,000', '~₹22,500'],
    ],
  },
  {
    type: 'p',
    text: 'Two cheap mods stand out. The 15F sprocket at ₹2,000 returns a tenth, the best cost per tenth in the catalog for either bike. The Power Tuner flash at ₹32,000 returns two tenths, the biggest single stage-1 gain before you start on the exhaust. Together the two cost under ₹35,000 and move the bike from a high-10 / low-11 into the mid-10 band.',
  },
  {
    type: 'p',
    text: 'The Akrapovic slip-on returns less per rupee than the ECU flash, because the CP3 triple already breathes well from the factory and the slip-on mostly changes the sound. If you are chasing ET, start with the sprocket and the flash.',
  },
  {
    type: 'h2',
    text: 'Run your own numbers',
  },
  {
    type: 'p',
    text: 'Which is faster, the XSR900 GP or the MT-09? The MT-09 wins the quarter mile by about 0.12 seconds under matched stock conditions, the GP wins the top-speed run by 15-20 km/h, and on a real strip the gap is well inside the run-to-run variance both bikes will show. Pick the MT-09 for the strip and the GP for the open highway.',
  },
  {
    type: 'p',
    text: 'If you own one of these bikes or are deciding between them, the simulator at motoquant.in lets you change rider weight, ambient temperature, density altitude, tire choice, gearing and parts-catalog mods and see where your tenths come from. The MT-09 baseline is reference-locked to the wider mid-twin / triple cluster band, and the XSR900 GP catalog entry runs through the same physics engine with its own spec-sheet inputs. The gaps in this post are what you get when you swap those inputs between the two bikes.',
  },
  {
    type: 'p',
    text: 'Two caveats. First, every number in this post is a stock-tune simulation under specific conditions. Change rider weight by 15 kg, ambient temperature by 10°C, or the surface from asphalt to a prepped strip, and the absolute ETs shift on both bikes, but the order (MT-09 wins the quarter, GP wins the top-speed run) holds. Second, the Indian CBU prices reflect 2026 retailer data and change every quarter. The parts catalog uses retailer prices where it has them and falls back to a landing-cost formula (USD × 84 × 1.30 import duty × 1.18 GST + ₹1500 freight) where it does not.',
  },
  {
    type: 'p',
    text: 'If a salesman in a Pune Yamaha showroom tells you the GP is faster than the MT-09 because of the fairing, he is half right. The GP is faster at 240 km/h. He just left out that the advantage only shows up on an empty stretch of road, which most Indians do not have access to. On the quarter mile, the only measure most buyers actually use to compare bikes, the MT-09 wins on every count.',
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
          datePublished: '2026-05-18',
        })}
      />
      <SiteNav />

      <article id="main" className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {['Yamaha', 'XSR900 GP', 'MT-09', 'CP3 triple', 'platform physics', 'comparison'].map((t) => (
              <span
                key={t}
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Yamaha XSR900 GP vs MT-09: where the heritage tax is paid
          </h1>
          <div className="text-sm text-white/60 mb-12">
            18 May 2026 · 11 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        <PostBikeLinks ids={[751]} />

        {/* Internal links / related reading */}
        <div className="max-w-2xl mx-auto mt-16">
          <h3 className="font-display font-bold text-lg text-white mb-4">Related reading</h3>
          <ul className="text-sm text-white/70 space-y-2">
            <li>
              ·{' '}
              <Link href="/blog/yamaha-mt-125-xsr125-platform-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                Yamaha MT-125 vs XSR125: same engine, 0.10s apart
              </Link>
              : the same platform-pair story at 125 cc instead of 890.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-the-motoquant-physics-engine-works" className="text-brand-accent hover:text-brand-orange transition-colors">
                How the MotoQuant physics engine works
              </Link>
              : the 15-sub-model RK4 architecture that produces the deterministic 0.12s gap between these two bikes.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/hayabusa-vs-zx-14r-which-is-faster" className="text-brand-accent hover:text-brand-orange transition-colors">
                Hayabusa vs ZX-14R: which is faster off the line?
              </Link>
              : another close comparison, at the litre-plus end.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-to-tune-for-aamby-valley-in-november" className="text-brand-accent hover:text-brand-orange transition-colors">
                How to tune for Aamby Valley in November
              </Link>
              : the venue conditions used for the simulation in this post.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>
              : MT-09, XSR900, XSR900 GP, Tracer 9 GT, and 340+ other bikes with full spec sheets.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Run your own XSR900 GP vs MT-09</div>
            <div className="text-white/60 text-sm">
              Free simulator: pick either bike, set your local conditions and rider weight, then re-run with the other to see where the tenths move.
            </div>
          </div>
          <Link
            href="/simulator?bike=yamaha-mt-09"
            className="shrink-0 px-5 py-2.5 bg-brand-orange text-on-accent font-display font-bold rounded-lg text-sm hover:bg-brand-orangeLight transition-colors"
          >
            Open the simulator →
          </Link>
        </div>
      </article>

      <SiteFooter />
    </div>
  );
}
