import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'hero-xtreme-200s-4v-quarter-mile-physics';
const TITLE = 'Hero Xtreme 200S 4V quarter-mile physics: 200cc commuter drag';
const DESCRIPTION =
  'MotoQuant simulates the Hero Xtreme 200S 4V at 17.40s with a 125 km/h trap. What the 19.1 hp 4-valve oil-cooled single can do at an Indian drag strip.';

export const metadata = {
  title: 'Hero Xtreme 200S 4V quarter-mile physics | MotoQuant',
  description: DESCRIPTION,
  keywords: [
    'Hero Xtreme 200S 4V quarter mile',
    'Hero Xtreme 200S 4V drag time',
    'Hero Xtreme 200S 4V top speed',
    'Indian 200cc drag race',
    'Xtreme 200S vs Pulsar NS200',
    'Karizma 4V head Xtreme 200S',
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `https://motoquant.in/blog/${SLUG}`,
    type: 'article',
    publishedTime: '2026-05-08T00:00:00Z',
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: 'MotoQuant simulates the Hero Xtreme 200S 4V at 17.40 seconds with a 125.1 km/h trap (sim-only, no instrumented Indian magazine ET on the books yet). The bike makes 19.1 hp at 8,500 rpm and 17.35 Nm at 6,500 rpm out of a 199.6 cc oil-cooled single, and on paper that puts it within a hair of the Bajaj Pulsar NS200 on power-to-weight. On the strip the simulator has it about 1.6 seconds behind.',
  },
  {
    type: 'h2',
    text: 'What the 200S 4V is',
  },
  {
    type: 'p',
    text: 'The Xtreme 200S 4V is the 2023 refresh of the older 2-valve Xtreme 200S. Hero MotoCorp put a Karizma-derived 4-valve cylinder head on the 199.6 cc oil-cooled single and gained roughly 3 hp over the outgoing 2V variant. Bore is 67 mm, stroke 56.5 mm, compression 9.8:1. The frame, half-fairing, 17-inch wheels, telescopic forks and 5-speed gearbox with 14F/42R 428-pitch chain all carry over from the 2V bike. The update is a head swap and an ECU re-flash, not a clean-sheet redesign. The chassis goes back to the original Karizma R platform, which Hero has been developing since 2003.',
  },
  {
    type: 'p',
    text: 'On a drag strip that matters, because the chassis was designed around a long-stroke commuter single: wide handlebars, a soft fork rate, a comfort-tuned rear monoshock, and a 158 kg dry mass that is heavy for the displacement class. The Xtreme is a sport-styled commuter, not a sport bike at a commuter price, and the simulator models it as one. The numbers that follow are not flattering.',
  },
  {
    type: 'h2',
    text: 'Stock-tune simulation numbers',
  },
  {
    type: 'p',
    text: 'The stock-tune run uses Aamby Valley November conditions (density altitude around 1100 m, 22°C ambient, dry asphalt with the OEM bias-ply 130/70-17 rear at μ_peak 1.05) and a 78 kg rider on the 158 kg dry bike:',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'Value', 'Source'],
      ['Quarter-mile ET', '17.40 s', 'MotoQuant sim (sim-only)'],
      ['Trap speed', '125.1 km/h', 'MotoQuant sim'],
      ['60-foot time', '~3.0 s', 'MotoQuant sim'],
      ['Claimed top speed', '~119 km/h', 'Hero MotoCorp / BikeWale'],
      ['Cluster bias band', '+0.5 to +1.4 s', 'entry-200-300 cluster'],
    ],
  },
  {
    type: 'p',
    text: 'Neither Indian Autos Mag nor BikeWale has published an instrumented quarter-mile time for the 200S 4V at the time of writing. There are only 0-60 km/h numbers (around 4.6 seconds) and a manufacturer-claimed top speed near 119 km/h. The simulator has a documented +0.5 to +1.4 second slow bias on the entry-200-300 cc cluster (Pulsar NS200, Apache RTR 200 4V, Duke 200, Pulsar N250 territory), so a real Xtreme with a competent rider on a warm bike plausibly runs closer to 16.5–17.0 seconds.',
  },
  {
    type: 'callout',
    text: 'Why the simulator runs slow on small-cc Indian bikes: most published ETs for this class are 0-100 km/h times multiplied by 1.6, a magazine shortcut rather than a real timing trap. Instrumented Indian small-cc data is thin, so the model is calibrated conservatively, to the slow end of plausible, until instrumented timeslips arrive through the "Submit a timeslip" form. The bias is deliberate, not a bug.',
  },
  {
    type: 'h2',
    text: 'Why the Xtreme is slower than the NS200',
  },
  {
    type: 'p',
    text: 'On power-to-weight, the Xtreme 200S 4V at 19.1 hp / 158 kg dry (about 121 hp/tonne) is within a few percent of the Bajaj Pulsar NS200 at 24.5 hp / 152 kg dry (around 161 hp/tonne, by Bajaj Auto official figures). In the simulator the NS200 runs roughly 15.8 seconds with a 130 km/h trap under the same conditions. That is an ET gap of about 1.6 seconds and a small trap-speed gap, more than power-to-weight alone would predict. Three things cause it:',
  },
  {
    type: 'p',
    text: '1. Peak-power rpm. The NS200 makes peak power at 9,750 rpm and revs happily to 11,000. The Xtreme peaks at 8,500, with the redline closer to 9,500. That is roughly a thousand fewer rpm of usable top-end pull, and on a 200 cc bike, where every rpm of headroom adds trap speed, the difference compounds. The NS200 spends more of each gear in the meaty part of the curve. The Xtreme runs out of revs sooner and has to upshift before the next gear has fully loaded.',
  },
  {
    type: 'p',
    text: '2. Cylinder cooling. The NS200 has Bajaj triple-spark oil cooling with a dedicated head oil cooler. The Xtreme has a simpler oil-cooled head with no dedicated cooler. Over back-to-back runs on a hot 35°C Aamby Valley afternoon, the Xtreme heat-soaks faster than the NS200 and starts losing 2-4% of peak power on runs three and four. The simulator does not currently model run-to-run heat soak, so its single-run numbers flatter the Xtreme slightly compared with a real drag-strip session.',
  },
  {
    type: 'p',
    text: '3. Aerodynamics. Hero rates the half-faired Xtreme at a Cd of around 0.78 with a frontal area near 0.46 m². The NS200, a naked sport, sits at Cd ≈ 0.80 with frontal area ~0.42 m². The half-fairing helps the Xtreme a little at higher speeds, but the wider commuter handlebars and more upright riding position give back most of that. At 125 km/h the two bikes are within 5% of each other on aerodynamic drag. That is too close to matter for ET, but it does keep the Xtreme\'s trap below the NS200\'s.',
  },
  {
    type: 'h2',
    text: 'What limits the Xtreme in the quarter',
  },
  {
    type: 'p',
    text: 'In order of impact for a stock bike:',
  },
  {
    type: 'p',
    text: '1. Gearing. The 5-speed cassette ratios on the 200S 4V are [3.182, 1.778, 1.318, 1.045, 0.875] with 14F/42R sprockets and a tire rolling radius around 290 mm on the 130/70-17 rear. With those numbers, fifth gear at 8,500 rpm gives a theoretical road speed of about 122 km/h, almost exactly the manufacturer-claimed top speed, so in 5th the bike is limited by gearing, not power. The simulator log shows the Xtreme crossing the trap line in 4th gear at roughly 8,200 rpm, then upshifting to 5th about 30 m before the trap line and arriving in 5th at about 7,400 rpm. Dropping from 14F to 13F (one tooth down at the front, around ₹400 in parts) shortens 5th enough that the bike reaches the trap with 5th still pulling.',
  },
  {
    type: 'p',
    text: "2. Clutch and launch. With only 17.35 Nm at 6,500 rpm, the Xtreme has the opposite problem to a litre bike: there is barely enough torque to wheelie, and the launch window is narrow. Drop the clutch below 5,000 rpm and the engine bogs. Launch above 7,500 rpm and the rear tire (bias-ply OEM rubber, μ_peak 1.05) does start to spin on dry asphalt, because the clutch hooks too hard. The simulator's small-cc clutch over-clutching factor, added in the May 2026 calibration pass, lets the Xtreme launch closer to its peak-torque rpm without snatching. That closes about 0.3 seconds of the larger gap the model had before the fix. A real rider on a real strip has to find that window by feel, and most do not.",
  },
  {
    type: 'p',
    text: '3. Tire compound. The OEM tire is a bias-ply commuter compound that lasts 25,000 km of city riding but is not sticky. A radial sport tire in the same size (a Pirelli Diablo Rosso II or an Apollo Alpha H1 in 130/70-17) raises μ_peak from around 1.05 to 1.30, worth roughly 0.4 seconds of ET through better launch traction and better mid-corner stability. At ~₹6,500 a pair, this is the cheapest tenth on the bike. The simulator scores tire mods per part and per bike, and the rear tire alone has the best ₹ per tenth on the Xtreme catalog page.',
  },
  {
    type: 'h2',
    text: 'How the Xtreme 200S 4V compares with its Indian 200cc peers',
  },
  {
    type: 'p',
    text: 'Here are MotoQuant stock-tune sims of four Indian 200cc commuter sport bikes under the same Aamby Valley November conditions:',
  },
  {
    type: 'table',
    rows: [
      ['Bike', 'Sim ET', 'Sim trap', 'Dry mass', 'Peak hp', 'Peak rpm'],
      ['Hero Xtreme 200S 4V', '17.40 s', '125 km/h', '158 kg', '19.1', '8500'],
      ['Bajaj Pulsar NS200', '~15.8 s', '~130 km/h', '152 kg', '24.5', '9750'],
      ['TVS Apache RTR 200 4V', '~16.2 s', '~127 km/h', '153 kg', '20.5', '8500'],
      ['KTM Duke 200 (2024)', '~15.6 s', '~131 km/h', '147 kg', '25.0', '10000'],
    ],
  },
  {
    type: 'p',
    text: 'The Xtreme is the slowest of the four, and its gap to the next-slowest, the Apache RTR 200 4V, is roughly 1.2 seconds, more than the spec sheets would suggest. The Apache makes its 20.5 hp at the same 8,500 rpm as the Xtreme but has a stiffer chassis, a sport tire as original equipment and a sharper gearbox. The gap from the Xtreme to the Duke 200 is almost two full seconds, though the Duke is only 5 kg lighter and 6 hp up. The Duke wins on revs (10,000 rpm peak), sportier chassis geometry and a tighter close-ratio gearbox.',
  },
  {
    type: 'p',
    text: 'If you are a commuter weighing the Xtreme 200S 4V against the Apache RTR 200 4V or the NS200, the drag-strip number is one input among many. The Xtreme is roughly ₹15,000 cheaper than the NS200 on-road in most cities (Hero MotoCorp 2026 pricing), the half-fairing does help comfort on long rides, and the Karizma-derived 4V head is durable. If quarter-mile time is all you care about, do not buy the Xtreme. If it is one of fifteen things you care about, the Xtreme is a perfectly defensible choice.',
  },
  {
    type: 'h2',
    text: 'Indian drag-strip reality and cost per tenth',
  },
  {
    type: 'p',
    text: 'The 200S 4V is rare at organised drag meets: most Indian 200cc strip regulars run NS200, RTR 200 4V or Duke 200 platforms because their aftermarket is larger. Aamby Valley and BIC see roughly half a dozen private Xtreme owners in a typical season, mostly on stock or near-stock bikes. The few modded Xtremes that turn up tend to stick to the cheapest mods per tenth. The simulator puts these numbers on them:',
  },
  {
    type: 'table',
    rows: [
      ['Mod', 'ET gain', 'Indian price', '₹ per tenth'],
      ['13F sprocket swap', '~0.20 s', '~₹400', '~₹200'],
      ['Apollo Alpha H1 130/70-17 rear', '~0.40 s', '~₹3,200', '~₹800'],
      ['K&N drop-in air filter', '~0.10 s', '~₹4,300', '~₹4,300'],
      ['Powertronic ECU flash', '~0.25 s', '~₹14,000', '~₹5,600'],
      ['SC-Project slip-on (off-road)', '~0.15 s', '~₹35,000', '~₹23,000'],
    ],
  },
  {
    type: 'p',
    text: 'The first two items cost almost nothing for what they give. Together the sprocket and the rear tire cost roughly ₹3,600 and take nearly 0.6 seconds off the simulator ET, the best ROI any 200cc Indian bike can offer. After those, the cost per tenth climbs fast and the gains level off. A full Powertronic flash, a slip-on and an air filter together get you another ~0.5 seconds for ~₹53,000, which on a ₹1.4 lakh bike is a 38% cost increase for a 3% ET improvement. Most owners stop at sprocket and tire and keep the rest of the budget for fuel and track time.',
  },
  {
    type: 'callout',
    text: 'The fastest cheap path on the 200S 4V: fit a 13F front sprocket and a sport-compound rear tire, about ₹3,600 for about 0.6 s of ET. Skip the slip-on exhaust unless you also want the noise. Its gain is real, but on a sub-25 hp bike the cost per tenth is brutal.',
  },
  {
    type: 'h2',
    text: 'Why the cluster bias matters for this bike',
  },
  {
    type: 'p',
    text: 'The simulator has a +0.5 to +1.4 second slow bias on the entry-200-300 cc cluster, wider than the +0.15 to +0.30 second band on the litre nakeds, because there is less benchmark data behind it. Most Indian magazine tests of 200cc bikes time only 0-100 km/h at the strip and convert that to a quarter-mile ET by multiplying by 1.6. The factor works for litre bikes that pull through to high trap speeds. It under-predicts ET on small-cc bikes, which reach the trap line in a lower gear and at lower trap speeds. So a magazine "quarter-mile" of 16.0 seconds on a 200cc bike is often a 0-100 of 10.0 seconds with the multiplier applied, and the real timed quarter is closer to 17.0.',
  },
  {
    type: 'p',
    text: 'For the Xtreme, that means the simulator\'s 17.40 second ET and a magazine 16.0 second ET probably describe the same bike, measured two different ways. If you own one, take it to a timed strip, run a Dragy or a VBOX, and trust the timing trap over the magazine number. The gap will close as more instrumented Indian small-cc timeslips join the benchmark set.',
  },
  {
    type: 'h2',
    text: 'Run your own numbers',
  },
  {
    type: 'p',
    text: 'If you own an Xtreme 200S 4V (or are deciding between it and an NS200, RTR 200 4V, or Duke 200), the simulator at motoquant.in lets you vary rider weight, ambient temperature, density altitude, tire choice, gearing and parts-catalog mods, and see where your tenths come from. The cluster bias is part of the model: when the simulator says your bike runs 17.40, expect the strip to show closer to 16.5–17.0 with a competent rider on a warm bike with sport rubber.',
  },
  {
    type: 'p',
    text: "For everyday tuning, the simulator's parts-ROI engine works out the cost per tenth for every bike in the catalog. On a 200S 4V the order is clear: sprocket swap and sport tire first, exhaust last. Most owners spend in the wrong order, which is why most modded 200cc bikes carry ₹50,000 of upgrades and gain less ET than a ₹3,600 sprocket and tire would have.",
  },
  {
    type: 'p',
    text: 'Two caveats. First, every number in this post is a stock-tune simulation under specific conditions. Change the rider weight, ambient temperature, surface or launch technique and the absolute ETs shift, but the order of which mods help most stays the same. Second, work on the entry-200-300 cluster bias is ongoing. The May 2026 calibration work added Hypothesis property tests that pin the four load-bearing physics knobs to monotonic invariants, and the small-cc clutch over-clutching rewrite from April 2026 has already cut the cluster bias roughly in half. The Xtreme number you see today might tighten by another 0.3–0.5 seconds as more Indian small-cc Dragy data comes in.',
  },
  {
    type: 'p',
    text: 'The Hero Xtreme 200S 4V is limited by gearing and tires, not power, and two cheap parts get you most of the available ET gain. The half-fairing is for comfort and the Karizma 4V head is for durability. Past that, the timing trap at a real strip has the last word.',
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
          datePublished: '2026-05-08',
        })}
      />
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {['Hero', 'Xtreme 200S 4V', 'Indian 200cc', 'commuter sport'].map((t) => (
              <span
                key={t}
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Hero Xtreme 200S 4V quarter-mile physics: 200cc commuter drag
          </h1>
          <div className="text-sm text-white/60 mb-12">
            8 May 2026 · 9 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        {/* Internal links / related reading */}
        <div className="max-w-2xl mx-auto mt-16">
          <h3 className="font-display font-bold text-lg text-white mb-4">Related reading</h3>
          <ul className="text-sm text-white/70 space-y-2">
            <li>
              ·{' '}
              <Link href="/blog/why-your-r15-wont-hit-14s" className="text-brand-accent hover:text-brand-orange transition-colors">
                Why Your R15 Won&apos;t Hit 14s
              </Link>:{' '}
              same small-cc cluster, same gearing-and-traction story, different bike.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-the-motoquant-physics-engine-works" className="text-brand-accent hover:text-brand-orange transition-colors">
                How the MotoQuant Physics Engine Works
              </Link>:{' '}
              the 15-sub-model architecture behind every ET prediction in this post.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/the-physics-of-a-perfect-launch" className="text-brand-accent hover:text-brand-orange transition-colors">
                The Physics of a Perfect Launch
              </Link>:{' '}
              clutch, slip, and weight transfer in the first 0.4 seconds.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-to-tune-for-aamby-valley-in-november" className="text-brand-accent hover:text-brand-orange transition-colors">
                How to Tune for Aamby Valley in November
              </Link>:{' '}
              the venue conditions used for the simulation in this post.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>:{' '}
              the specs, gear ratios and Cd values the simulator uses.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Run the Xtreme 200S 4V yourself</div>
            <div className="text-white/60 text-sm">
              Free simulator: pick the Hero Xtreme 200S 4V, set your local conditions and a sport tire, and watch the ET update live.
            </div>
          </div>
          <Link
            href="/simulator?bike=hero-xtreme-200s-4v"
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
