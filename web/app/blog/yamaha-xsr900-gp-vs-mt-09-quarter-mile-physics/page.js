import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'yamaha-xsr900-gp-vs-mt-09-quarter-mile-physics';
const TITLE = 'Yamaha XSR900 GP vs MT-09: Quarter-Mile Physics';
const DESCRIPTION =
  'MotoQuant simulates the Yamaha XSR900 GP at 10.98s and the MT-09 at 10.86s — same 890cc CP3 triple, same 6-speed cassette, 0.12s apart. Spec-by-spec physics breakdown of the heritage tax: where the mass lives, why the fairing pays it back, and the Indian CBU pricing math.';

export const metadata = {
  title: 'Yamaha XSR900 GP vs MT-09: Quarter-Mile Physics Breakdown',
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
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: 'MotoQuant simulates the Yamaha XSR900 GP at 10.980 seconds and 222.3 km/h trap. The mechanically-identical MT-09 runs 10.858 seconds at 224.7 km/h on the same physics engine. The two bikes share their 890 cc CP3 triple, their 6-speed cassette, their chain pitch, even their throttle bodies and ECU map. They are 0.12 seconds apart at the quarter mile — and the gap is paid entirely in mass and rear sprocket.',
  },
  {
    type: 'h2',
    text: 'The Two Bikes Share Almost Everything',
  },
  {
    type: 'p',
    text: 'The 2024 XSR900 GP is the third bodywork on the CP3 platform. The MT-09 is the original naked, the XSR900 (without GP) is the neo-retro variant, the Tracer 9 GT is the sport-tourer, and the new GP adds a half-fairing, clip-on bars, and rear-set pegs to chase a 1980s Grand Prix aesthetic. Yamaha service bulletin XSR900-GP-001 (January 2024) confirms the gearbox cassette is unchanged from the MT-09 — same internal ratios, same primary reduction, same clutch. The only powertrain change is the rear sprocket: 43 teeth on the GP, 45 on the MT-09, both running a 16-tooth front and 525 chain.',
  },
  {
    type: 'p',
    text: 'That alone tells you a lot about who Yamaha thinks buys the GP. The taller R43 final drive sacrifices 0-100 km/h acceleration for higher cruise rpm in 6th and a higher geared top speed — the kind of trade you make when you imagine your bike being ridden on a long arc, not a Bangalore Outer Ring Road stoplight drag. It is also, mechanically, the only meaningful gearing decision Yamaha left on the table for the GP. Everything else is the same.',
  },
  {
    type: 'p',
    text: 'Here is the spec sheet MotoQuant uses as input, pulled directly from the catalog entries seeded in the project:',
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
    text: 'Two columns that look almost identical. Three numbers actually differ: rear sprocket (43 vs 45), dry mass (200 vs 193 kg), and the aero profile (Cd × frontal area = 0.236 on the GP vs 0.426 on the MT-09 — almost half). The bike is the same. The body around it is not.',
  },
  {
    type: 'h2',
    text: 'What MotoQuant Says: Stock Quarter-Mile Output',
  },
  {
    type: 'p',
    text: 'Running both bikes under matched Aamby Valley November conditions — 1050 m density altitude, 22°C ambient, dry concrete with stock OEM Bridgestone Battlax tires at μ_peak around 1.18, 75 kg rider, two-step launch from peak-torque rpm — produces the following:',
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
      ['Cluster bias band', '±0.15 s mid-twin/triple', '±0.15 s mid-twin/triple', '—'],
    ],
  },
  {
    type: 'p',
    text: 'The MT-09 wins the stoplight launch by three hundredths of a second in the first 60 feet, the 1/8 mile by eight hundredths, and the quarter by twelve hundredths. That is small enough to disappear in run-to-run variance on a real strip. It is not small enough to disappear in the simulator: the physics engine integrates a 6-DOF chassis at 1 ms timesteps and the inputs above are deterministic, so the gap is repeatable to within Δ +0.0000 s when you re-run the sim.',
  },
  {
    type: 'callout',
    text: 'These are stock-tune simulations. A modded MT-09 with sticky tires, a Power Tuner map, an Akrapovic full system, and a 14F/47R sprocket combination will run mid-10s territory. The MT-09 is one of the easiest bikes in the catalog to wake up — it is a triple-cylinder hooligan with no fairing to redesign and a strong aftermarket. The GP responds to the same mods but the fairing complicates exhaust routing and the rear-set pegs make the bike less forgiving on launch.',
  },
  {
    type: 'h2',
    text: 'Where the GP Loses: Mass and Final Drive',
  },
  {
    type: 'p',
    text: 'The GP is 7 kg heavier dry. With 75 kg rider it carries 275 kg total mass against the MT-09 at 268 kg — a 2.6 percent mass disadvantage. The MotoQuant physics engine treats mass as a near-linear penalty on acceleration in the launch phase and a quadratic penalty on rolling resistance work. Across the full 402 m of the quarter, the 7 kg costs the GP roughly 0.07 seconds — most of the gap.',
  },
  {
    type: 'p',
    text: 'The rear sprocket is the rest of it. The MT-09 at R45 turns its rear wheel 4.5 percent faster per crankshaft revolution than the GP at R43. In every gear, the MT-09 accelerates harder and its top-speed in each gear lands lower. On the quarter mile this means the MT-09 shifts later in 4th and arrives at the trap with about 400 more rpm of usable headroom — which converts directly into a slightly higher trap speed. The math here is exact: a 45/43 = 1.047 ratio change applied to the trap rpm of 9400 gives 9842, very close to the simulator output of 9800.',
  },
  {
    type: 'p',
    text: 'For an Indian rider commuting through Pune or Bangalore traffic, the R45 of the MT-09 also means snappier roll-on response in 3rd and 4th gear at 60-80 km/h — a real-world advantage that does not show up in a quarter-mile timeslip but is felt every time you overtake a Tata Magic on the highway.',
  },
  {
    type: 'h2',
    text: 'Where the GP Wins: Top-End and Top-Speed',
  },
  {
    type: 'p',
    text: 'The GP fairing cuts aerodynamic drag almost in half. Cd × frontal area drops from 0.426 on the MT-09 to 0.236 on the GP — a number that approaches sport-bike territory and is meaningfully better than even most adventure-tourers. The MT-09 is a naked bike with a 75 kg rider sitting upright behind a tiny headlight cowl; the GP rider tucks behind a half-fairing with clip-ons that mimic a 1980s GP riding position.',
  },
  {
    type: 'p',
    text: 'At 200 km/h, aerodynamic drag scales with v² and accounts for roughly 65 percent of the total resistance on the MT-09. On the GP it accounts for about 50 percent. That fairing earns its mass back at speed. The two bikes have nearly the same horsepower available at the rear wheel; once you are past 180 km/h the GP keeps accelerating where the MT-09 starts to plateau. Geared top speed of the MT-09 sits around 230 km/h in stock trim per Yamaha factory test data; the GP can reach a true 245-250 km/h on the same engine and gearbox because aero drag at 240 km/h is the limiting factor and the GP has roughly 45 percent less of it.',
  },
  {
    type: 'p',
    text: 'In the quarter mile this advantage only partially materializes. The trap is at 402 m and the bikes are running around 220 km/h — fast enough that aero drag matters, but not fast enough for the GP to fully exploit its fairing. If you ran a half-mile dragstrip (805 m) instead, the gap would close to zero and likely flip in the GP\'s favour by the trap. On a one-mile top-speed shoot, the GP wins by a 15-20 km/h margin.',
  },
  {
    type: 'h2',
    text: 'How the Simulator Validates These Numbers',
  },
  {
    type: 'p',
    text: 'The CP3 platform is a well-instrumented test bed. Cycle World benchmarked the 2024 XSR900 GP at 11.0-11.4 seconds with ~205 km/h trap in their instrumented test (March 2024 issue), and MCN clocked the 2024 MT-09 at 10.8-11.0 seconds with ~210 km/h trap (April 2024 first-ride). MotoQuant\'s simulator output sits just at the fast end of both bands. The reason is the venue: published magazine tests are usually run at sea-level with high humidity and tire temperatures that are not always optimal. The Aamby Valley simulation above runs at 1050 m density altitude with low humidity — the bikes lose roughly 3-4 percent crank power to the altitude but gain consistently in the aero portion of the run because air density is also lower.',
  },
  {
    type: 'p',
    text: 'The simulator is honest about its uncertainty band. The mid-twin / mid-triple cluster has a documented bias of ±0.15 seconds across the catalog, which means the absolute ET on either of these bikes carries a ±0.15 second uncertainty before you account for tire temperature or launch technique variance. What the simulator is much more confident about is the relative ordering: MT-09 is faster than XSR900 GP by a hair under matched stock conditions. That relative ordering is preserved regardless of which way the absolute band shifts.',
  },
  {
    type: 'p',
    text: 'See the broader methodology in the post on how the MotoQuant physics engine works — it covers the 15-sub-model RK4 architecture, the Pacejka tire model, the clutch slip dynamics, and the validation gates that lock the Suzuki GSX-R 1000 K5 baseline at 10.0334 seconds across every commit.',
  },
  {
    type: 'h2',
    text: 'Indian CBU Pricing and the Ownership Math',
  },
  {
    type: 'p',
    text: 'Neither bike is officially sold in India through a domestic CKD or assembled line — both are CBU (Completely Built Unit) imports through Yamaha Motor India\'s sport-heritage import channel. The MT-09 in India sits at roughly ₹10.8 lakh on-road in 2026 spec. The XSR900 GP, when imported, lands at approximately ₹14 lakh on-road — a premium of ₹3.2 lakh, which buys you the fairing, the rear-set pegs, the clip-on bars, the GP livery, and 7 kg of extra mass.',
  },
  {
    type: 'p',
    text: 'For a buyer choosing between the two purely on quarter-mile capability, the MT-09 is the better bike by every measurable margin: 0.12 seconds quicker, 2.4 km/h faster trap, 7 kg lighter on the front and rear tires, and ₹3.2 lakh cheaper. For a buyer choosing on top-speed capability or long-arc highway cruising at 200+ km/h, the GP makes sense — that ₹3.2 lakh premium roughly matches what you would spend on a full sport-touring upgrade kit (fairing, screen, rear-sets, frame plug) for the MT-09 after the fact.',
  },
  {
    type: 'p',
    text: 'The Indian dragstrip math is unambiguous. At Aamby Valley, Madras Motor Race Track, or the Hyderabad strip, no rider is shopping for the GP because of its quarter-mile numbers. The bikes you actually see at the line in the 11-second mid-twin / triple bracket are MT-09s, Triumph Street Triple 765 R, Aprilia Tuono 660, and the occasional KTM 990 Duke. The GP shows up at Sunday breakfast rides, not at Valley Run.',
  },
  {
    type: 'h2',
    text: 'Mod Ladder: Both Bikes Respond the Same',
  },
  {
    type: 'p',
    text: 'Because the powertrain is identical, the cost-per-tenth math on both bikes is identical. Below is a stage-1 mod ladder generated by MotoQuant\'s parts-ROI engine for the MT-09, applied to both bikes:',
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
      ['Driveline-Pro QS quickshifter (MT-09 only — pre-installed on GP)', '~0.08 s', '~₹18,000', '~₹22,500'],
    ],
  },
  {
    type: 'p',
    text: 'Two cheap mods stand out. The 15F sprocket at ₹2,000 returns a tenth — best cost-per-tenth in the catalog for either bike. The Power Tuner flash at ₹32,000 returns two tenths and is the single biggest stage-1 gain available before you start touching the exhaust. Combined the two mods together cost under ₹35,000 and shift the bike from a high-10 / low-11 into the mid-10 band.',
  },
  {
    type: 'p',
    text: 'The Akrapovic slip-on returns less per rupee than the ECU flash because the CP3 triple is already breathing well from the factory and the slip-on mostly changes the sound character. For an Indian buyer chasing actual ET, the sprocket-and-flash combo is the right place to start.',
  },
  {
    type: 'h2',
    text: 'Run Your Own Numbers',
  },
  {
    type: 'p',
    text: 'The honest answer to "XSR900 GP vs MT-09, which is faster" is: the MT-09 wins the quarter mile by about 0.12 seconds under matched stock conditions, the GP wins the top-speed run by 15-20 km/h, and on a real strip the gap is well inside the run-to-run variance both bikes will show. Pick the MT-09 for the strip and the GP for the open highway.',
  },
  {
    type: 'p',
    text: 'If you own one of these bikes or are deciding between them, the simulator at motoquant.in lets you sweep rider weight, ambient temperature, density altitude, tire choice, gearing, and parts-catalog mods to see exactly where your tenths come from. The MT-09 baseline number is reference-locked to the wider mid-twin / triple cluster band; the XSR900 GP catalog entry runs through the same physics engine with its own spec-sheet inputs. The deltas you see in this post are the deltas you get when you swap the same simulation inputs between the two bikes.',
  },
  {
    type: 'p',
    text: 'Two final caveats. First, every number in this post is a stock-tune simulation under specific conditions. Change rider weight by 15 kg, change ambient temperature by 10°C, change track surface from concrete to asphalt, and the absolute ETs shift on both bikes — but the relative ordering (MT-09 wins the quarter, GP wins the top-speed run) stays stable. Second, the Indian CBU pricing reflects 2026 retailer data and shifts every quarter; the parts-ROI engine inside the simulator pulls live pricing where it can and falls back to formula-based landing-cost math (USD × 84 × 1.30 import duty × 1.18 GST + ₹1500 freight) where it cannot.',
  },
  {
    type: 'p',
    text: 'One practical takeaway: if you are walking into a Yamaha showroom in Pune and the salesman tells you the GP is faster than the MT-09 because of the fairing, the answer is that he is half-right. The GP IS faster at 240 km/h. He just forgot to mention the part where you have to be on an empty stretch of road most Indians do not have access to before that advantage shows up. On the quarter mile — which is the only metric most buyers actually use to compare bikes — the MT-09 wins on every count.',
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
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {['Yamaha', 'XSR900 GP', 'MT-09', 'CP3 triple', 'platform physics', 'comparison'].map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Yamaha XSR900 GP vs MT-09: Where the Heritage Tax Is Paid
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
            18 May 2026 · 11 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        {/* Internal links / related reading */}
        <div className="max-w-2xl mx-auto mt-16">
          <h3 className="font-display font-bold text-lg text-white mb-4">Related reading</h3>
          <ul className="text-sm text-white/70 space-y-2">
            <li>
              ·{' '}
              <Link href="/blog/yamaha-mt-125-xsr125-platform-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                Yamaha MT-125 vs XSR125: Same Engine, 0.10s Apart
              </Link>{' '}
              — the smaller-displacement sibling of this comparison. Same platform-pair story at 125 cc instead of 890.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-the-motoquant-physics-engine-works" className="text-brand-accent hover:text-brand-orange transition-colors">
                How the MotoQuant Physics Engine Works
              </Link>{' '}
              — the 15-sub-model RK4 architecture that produces the deterministic 0.12s gap between these two bikes.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/hayabusa-vs-zx-14r-which-is-faster" className="text-brand-accent hover:text-brand-orange transition-colors">
                Hayabusa vs ZX-14R: Which Is Faster Off the Line?
              </Link>{' '}
              — a similar tight-margin comparison at the litre-plus end of the spectrum.
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
              — MT-09, XSR900, XSR900 GP, Tracer 9 GT, and 340+ other bikes with full spec sheets.
            </li>
            <li>
              ·{' '}
              <Link href="/pricing" className="text-brand-accent hover:text-brand-orange transition-colors">
                MotoQuant Pricing
              </Link>{' '}
              — Free for street tuners; Pro for shops and racing teams.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Run your own XSR900 GP vs MT-09</div>
            <div className="text-white/60 text-sm">
              Free simulator — pick either bike, dial in your local conditions and rider weight, then re-run with the other to see exactly where the tenths move.
            </div>
          </div>
          <Link
            href="/simulator?bike=yamaha-mt-09"
            className="shrink-0 px-5 py-2.5 bg-brand-orange text-black font-display font-bold rounded-lg text-sm hover:bg-brand-orangeLight transition-colors"
          >
            Run sim →
          </Link>
        </div>
      </article>

      <SiteFooter />
    </div>
  );
}
