import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';
import { REPO_URL } from '../../../lib/site';

const SLUG = 'hero-xtreme-200s-4v-quarter-mile-physics';
const TITLE = 'Hero Xtreme 200S 4V Quarter-Mile Physics: 200cc Commuter Drag';
const DESCRIPTION =
  'MotoQuant simulates the Hero Xtreme 200S 4V at 17.40s and 125 km/h trap. What the 19.1 hp 4-valve oil-cooled single can really do at an Indian drag strip.';

export const metadata = {
  title: 'Hero Xtreme 200S 4V Quarter-Mile Physics — MotoQuant',
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
    text: 'MotoQuant simulates the Hero Xtreme 200S 4V at 17.40 seconds with a 125.1 km/h trap — sim-only, no instrumented Indian magazine ET on the books yet. The bike makes 19.1 hp at 8,500 rpm and 17.35 Nm at 6,500 rpm out of a 199.6 cc oil-cooled single, and on paper that puts it within a hair of the Bajaj Pulsar NS200 on power-to-weight. On the strip it sits in a different place entirely, and the reasons are interesting.',
  },
  {
    type: 'h2',
    text: 'What the 200S 4V Actually Is',
  },
  {
    type: 'p',
    text: 'The Xtreme 200S 4V is the 2023 refresh of the older 2-valve Xtreme 200S. Hero MotoCorp dropped a Karizma-derived 4-valve cylinder head onto the 199.6 cc oil-cooled single and picked up roughly 3 hp over the outgoing 2V variant. Bore is 67 mm, stroke 56.5 mm, compression 9.8:1. The frame, the half-fairing, the 17-inch wheels, the telescopic forks, the 5-speed gearbox with 14F/42R 428-pitch chain — all carried over from the 2V bike. This is a head swap and an ECU re-flash, not a clean-sheet redesign, and the chassis dates back to the original Karizma R platform Hero has been iterating on since 2003.',
  },
  {
    type: 'p',
    text: 'For a drag-strip analysis that matters because the chassis was designed around a long-stroke commuter single — wide handlebars, soft fork rate, comfort-tuned rear monoshock, and a 158 kg dry mass that is heavy for the displacement class. The Xtreme is a sport-styled commuter, not a sport bike with commuter pricing. The simulator has to model it as exactly what it is, and the resulting numbers are honest rather than flattering.',
  },
  {
    type: 'h2',
    text: 'Stock-Tune Simulation Numbers',
  },
  {
    type: 'p',
    text: 'Running the Xtreme 200S 4V in MotoQuant under Aamby Valley November conditions (density altitude around 1100 m, 22°C ambient, dry concrete with the OEM bias-ply 130/70-17 rear at μ_peak 1.05) and a 78 kg rider on the 158 kg dry bike produces the following stock-tune output:',
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
    text: 'There is no published Indian Autos Mag or BikeWale instrumented quarter-mile time on the 200S 4V at the time of writing — only 0-60 km/h numbers (around 4.6 seconds) and a manufacturer-claimed top speed near 119 km/h. The simulator carries a documented +0.5 to +1.4 second slow bias on the entry-200-300 cc cluster (Pulsar NS200, Apache RTR 200 4V, Duke 200, Pulsar N250 territory), so the real-world Xtreme is plausibly running closer to 16.5–17.0 seconds in the hands of a competent rider on a warmed bike.',
  },
  {
    type: 'callout',
    text: 'Why the simulator runs slow on small-cc Indian bikes: the cluster bias is honest, not a bug. Most published 0-100 km/h times for this class are converted to ETs by multiplying by 1.6 — a magazine shortcut, not a real timing trap. Real instrumented Indian small-cc data is thin, so the model is conservatively calibrated to the slower end of plausible until Dragy uploads start flowing through the calibrator.',
  },
  {
    type: 'h2',
    text: 'Why the Xtreme Is Slower Than the NS200',
  },
  {
    type: 'p',
    text: 'On power-to-weight, the Xtreme 200S 4V at 19.1 hp / 158 kg dry (about 121 hp/tonne) is within a few percent of the Bajaj Pulsar NS200 at 24.5 hp / 152 kg dry (around 161 hp/tonne, by Bajaj Auto official figures). In the simulator the NS200 runs roughly 15.8 seconds at 130 km/h trap under the same conditions. That is a ~1.6 second ET gap and a small trap-speed gap, and the gap is bigger than the power-to-weight ratio alone would predict. Three things are happening:',
  },
  {
    type: 'p',
    text: '1. Peak-power RPM. The NS200 makes peak power at 9,750 rpm and is happy to rev to 11,000. The Xtreme peaks at 8,500 and the redline sits closer to 9,500. That is roughly a thousand fewer rpm of usable top-end pull, and on a 200 cc bike where every rpm of headroom translates into trap-speed gain, the difference compounds. The NS200 spends more of its time in the gear in the meaty part of the curve. The Xtreme runs out of revs faster and forces an upshift before the next gear has fully loaded.',
  },
  {
    type: 'p',
    text: '2. Cylinder cooling. The NS200 uses Bajaj triple-spark oil-cooling with a dedicated head oil cooler. The Xtreme uses a simpler oil-cooled head without the dedicated cooler. On a hot 35°C Aamby Valley afternoon over consecutive runs, the Xtreme will heat-soak faster than the NS200 and start losing 2-4% peak power on runs three and four. The simulator does not currently model run-to-run heat soak, so its single-run numbers flatter the Xtreme slightly relative to a real drag-strip session.',
  },
  {
    type: 'p',
    text: '3. Aerodynamics. Hero rates the half-faired Xtreme at a Cd of around 0.78 with a frontal area near 0.46 m². The NS200 — a naked sport — sits at Cd ≈ 0.80 with frontal area ~0.42 m². The half-fairing helps the Xtreme slightly at higher speeds but the wider commuter handlebars and more upright rider position give back most of the gain. At 125 km/h the two bikes are within 5% of each other on aerodynamic drag, which is too close to matter for ET but does cap the Xtreme below the NS200 in trap.',
  },
  {
    type: 'h2',
    text: 'What Actually Limits the Xtreme in the Quarter',
  },
  {
    type: 'p',
    text: 'In order of impact for a stock bike:',
  },
  {
    type: 'p',
    text: '1. Gearing. The 5-speed cassette ratios on the 200S 4V are [3.182, 1.778, 1.318, 1.045, 0.875] with 14F/42R sprockets and a tire rolling radius around 290 mm on the 130/70-17 rear. With those numbers, fifth gear at 8,500 rpm gives a theoretical road speed of about 122 km/h — almost exactly the manufacturer-claimed top speed. That means the bike is gearing-limited, not power-limited, in 5th. The simulator log shows the Xtreme crossing the trap line in 4th gear at roughly 8,200 rpm, then up-shifting to 5th about 30 m before the trap line and arriving in 5th at about 7,400 rpm. A drop from 14F to 13F (a one-tooth-down sprocket swap, around ₹400 in parts) shortens 5th enough to land the bike in the trap with 5th still pulling.',
  },
  {
    type: 'p',
    text: "2. Clutch and launch. With only 17.35 Nm at 6,500 rpm, the Xtreme has the opposite problem of a litre bike: there is barely enough torque to wheelie, and the launch window is narrow. Drop the clutch below 5,000 rpm and the engine bogs; bring the launch above 7,500 rpm and the rear tire — bias-ply OEM rubber, μ_peak 1.05 — actually does start to spin on dry concrete because the clutch hooks too hard. The simulator's small-cc clutch over-clutching factor (added in the May 2026 calibration pass) lets the Xtreme launch closer to its peak-torque rpm without snatching, which closes about 0.3 seconds of the bigger pre-fix gap. A real rider on a real strip needs to find that window by feel, and most do not.",
  },
  {
    type: 'p',
    text: '3. Tire compound. The OEM tire is a bias-ply commuter compound — durable for 25,000 km of city riding, but sticky it is not. A radial sport tire of the same size (a Pirelli Diablo Rosso II or an Apollo Alpha H1 in 130/70-17) bumps μ_peak from around 1.05 to 1.30, which translates to roughly 0.4 seconds of ET gain through better launch traction and better mid-corner stability. At ~₹6,500 a pair, this is the cheapest tenth on the bike. The simulator scores tire mods explicitly per part per bike — the rear tire alone is the highest-ROI ₹ per tenth on the Xtreme catalog page.',
  },
  {
    type: 'h2',
    text: 'How the Xtreme 200S 4V Compares to Its Indian 200cc Peers',
  },
  {
    type: 'p',
    text: 'Four 200cc Indian commuter sport bikes, four different physics profiles. Numbers below are MotoQuant stock-tune sims under matched Aamby Valley November conditions:',
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
    text: 'Two patterns stand out. First, the Xtreme is the slowest of the four and the gap to the next-slowest (Apache RTR 200 4V) is roughly 1.2 seconds — bigger than the spec-sheet difference would suggest. The Apache makes its 20.5 hp at the same 8,500 rpm as the Xtreme but uses a stiffer chassis, a sport tire OEM, and a sharper gearbox. Second, the gap from the Xtreme to the Duke 200 is almost two full seconds, and the Duke is only 5 kg lighter and 6 hp up. The Duke wins because of revs (10,000 rpm peak), a sportier chassis geometry, and a tighter close-ratio gearbox.',
  },
  {
    type: 'p',
    text: 'For an Indian commuter buyer weighing the Xtreme 200S 4V against the Apache RTR 200 4V or the NS200, the drag-strip number is one input among many. The Xtreme is roughly ₹15,000 cheaper than the NS200 on-road in most cities (Hero MotoCorp 2026 pricing), the half-fairing actually helps long-distance comfort, and the Karizma-derived 4V head is genuinely durable. If quarter-mile time is the only metric you care about, the Xtreme is not the bike to buy. If quarter-mile time is one of fifteen things you care about, it is a perfectly defensible choice.',
  },
  {
    type: 'h2',
    text: 'Indian Drag-Strip Reality and Cost-per-Tenth',
  },
  {
    type: 'p',
    text: 'The 200S 4V is rare at organised drag meets — most Indian 200cc strip regulars run NS200, RTR 200 4V, or Duke 200 platforms because of the larger aftermarket. Aamby Valley and BIC see roughly half a dozen private Xtreme owners across a typical season, mostly running stock or near-stock. The handful of modded Xtremes that do show up tend to focus on the cheapest-per-tenth mods, which the simulator quantifies cleanly:',
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
    text: 'The first two items are basically free relative to ET gain. The sprocket and the rear tire together cost roughly ₹3,600 and shave nearly 0.6 seconds off the simulator ET — that is the single best ROI any 200cc Indian bike can offer. Beyond those, the cost-per-tenth ramps fast and the gains plateau. A full Powertronic flash plus a slip-on plus an air filter together get you another ~0.5 seconds for ~₹53,000, which on a ₹1.4 lakh bike is a 38% cost increase for a 3% ET improvement. Most owners stop at sprocket-and-tire and keep the rest of the budget for fuel and track time.',
  },
  {
    type: 'callout',
    text: 'Fastest cheap path on the 200S 4V: drop a 13F front sprocket and fit a sport-compound rear tire. That is ~₹3,600 for ~0.6 s ET. Skip the slip-on exhaust unless you also want the noise — the gain is real but the cost-per-tenth is brutal on a sub-25 hp bike.',
  },
  {
    type: 'h2',
    text: 'Why the Cluster Bias Matters for This Bike Specifically',
  },
  {
    type: 'p',
    text: 'The simulator carries a +0.5 to +1.4 second slow bias on the entry-200-300 cc cluster — wider than the +0.15 to +0.30 second band on the litre nakeds, because the underlying benchmark data is thinner. Most 200cc Indian magazine tests are 0-100 km/h numbers (the only metric the testers actually time at the strip) converted to quarter-mile ETs by multiplying by 1.6. That conversion factor works for litre bikes that pull through to high trap speeds; it under-predicts ET on small-cc bikes that arrive at the trap line in a lower gear and at lower trap speeds. So a magazine "quarter-mile" of 16.0 seconds on a 200cc bike is often actually a 0-100 of 10.0 seconds with a multiplier applied, and the real timed quarter is closer to 17.0.',
  },
  {
    type: 'p',
    text: 'For the Xtreme specifically that means the simulator 17.40 second ET and a magazine 16.0 second ET are probably describing the same physical bike — they are just produced by different methodologies. The honest answer for an owner is: take the Xtreme to a real timed strip, run a Dragy or a VBOX, and trust the timing trap over the magazine number. The simulator will close the gap as more Indian small-cc Dragy data flows into the calibrator, which is a Phase 3 priority.',
  },
  {
    type: 'h2',
    text: 'Run Your Own Numbers',
  },
  {
    type: 'p',
    text: 'If you own an Xtreme 200S 4V (or are deciding between it and an NS200, RTR 200 4V, or Duke 200), the simulator at motoquant.in lets you sweep rider weight, ambient temperature, density altitude, tire choice, gearing, and parts-catalog mods to see exactly where your tenths come from. The cluster bias is built into the model — when the simulator says your bike runs 17.40, expect the strip to confirm closer to 16.5–17.0 with a competent rider on a warmed bike with sport rubber.',
  },
  {
    type: 'p',
    text: "More relevant for everyday tuning: the simulator's parts-ROI engine quantifies cost-per-tenth for every bike in the catalog. On a 200S 4V the answer is loud and clear — sprocket swap and sport tire first, exhaust last. Most owners spend money in the wrong order, which is why most modded 200cc bikes cost ₹50,000 in upgrades and gain less ET than a ₹3,600 sprocket-and-tire combo would have delivered.",
  },
  {
    type: 'p',
    text: 'Two final caveats. First, every number in this post is a stock-tune simulation under specific conditions. Change the rider weight, the ambient temperature, the surface, or the launch technique and the absolute ETs shift, but the relative ordering of which mods help most stays stable. Second, the simulator entry-200-300 cluster bias is being actively closed in the background. The May 2026 calibration work added Hypothesis property tests that pin the four load-bearing physics knobs to monotonic invariants, and the small-cc clutch over-clutching rewrite from April 2026 has already cut the cluster bias roughly in half. The Xtreme number you see today might tighten by another 0.3–0.5 seconds as more Indian small-cc Dragy data lands.',
  },
  {
    type: 'p',
    text: 'If you take one practical thing from this post, take this: the Hero Xtreme 200S 4V is gearing-limited and tire-limited, not power-limited. Two cheap parts will get you most of the available ET gain. The half-fairing is for comfort, the Karizma 4V head is for durability, and the strip is where the simulator stops talking and the timing trap starts.',
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
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Hero Xtreme 200S 4V Quarter-Mile Physics: 200cc Commuter Drag
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
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
              </Link>{' '}
              — same small-cc cluster, same gearing-and-traction story, different bike.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-the-motoquant-physics-engine-works" className="text-brand-accent hover:text-brand-orange transition-colors">
                How the MotoQuant Physics Engine Works
              </Link>{' '}
              — the 15-sub-model architecture behind every ET prediction in this post.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/the-physics-of-a-perfect-launch" className="text-brand-accent hover:text-brand-orange transition-colors">
                The Physics of a Perfect Launch
              </Link>{' '}
              — clutch, slip, and weight transfer in the first 0.4 seconds.
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
              — every spec, every gear ratio, every Cd value used by the simulator.
            </li>
            <li>
              ·{' '}
              <a
                href={REPO_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                MotoQuant on GitHub
              </a>{' '}
              — free and open source: audit the physics behind every number in this post, or run it yourself.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Run the Xtreme 200S 4V yourself</div>
            <div className="text-white/60 text-sm">
              Free simulator — pick the Hero Xtreme 200S 4V, dial in your local conditions and a sport tire, and watch the ET tighten live.
            </div>
          </div>
          <Link
            href="/simulator?bike=hero-xtreme-200s-4v"
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
