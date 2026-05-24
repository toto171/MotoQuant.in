import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'yamaha-mt-15-v1-quarter-mile-physics';
const TITLE = 'Yamaha MT-15 V1 Quarter-Mile Physics: 155cc Naked Drag';
const DESCRIPTION =
  'MotoQuant simulates the Yamaha MT-15 V1 at 17.05s and 125.5 km/h trap. Why the no-VVA naked loses a tenth to the R15 V3 — and where Indian cheap tenths live.';

export const metadata = {
  title: 'Yamaha MT-15 V1 Quarter-Mile Physics — MotoQuant',
  description: DESCRIPTION,
  keywords: [
    'Yamaha MT-15 V1 quarter mile',
    'MT-15 V1 drag time india',
    'MT-15 V1 vs R15 V3',
    'Yamaha MT-15 2019 0-100',
    'MT-15 V1 top speed india',
    'is MT-15 V1 faster than NS200',
    'MT-15 V1 cost per tenth',
    'Yamaha 155cc drag race',
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `https://motoquant.in/blog/${SLUG}`,
    type: 'article',
    publishedTime: '2026-05-24T00:00:00Z',
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: 'MotoQuant simulates the Yamaha MT-15 V1 at 17.05 seconds with a 125.5 km/h trap. The bike makes 18.4 hp at 10,000 rpm and 14.7 Nm at 8,500 rpm out of a 155.09 cc DOHC four-valve single — the same engine that powers the YZF-R15 V3, minus the Variable Valve Actuation that Yamaha reserved for the R15 V3 export and the later MT-15 V2. The 1 hp gap to the R15 V3 looks small on paper. On the strip it is closer to a tenth and a half, and the reason has more to do with aero, gearing intent, and how the V1 ECU manages the powerband than with peak numbers.',
  },
  {
    type: 'h2',
    text: 'What the MT-15 V1 Actually Is',
  },
  {
    type: 'p',
    text: 'The MT-15 V1 launched in India in March 2019 as a naked-bike companion to the YZF-R15 V3. It shares the V3 chassis, suspension, brakes, six-speed gearbox, and 155.09 cc liquid-cooled DOHC engine — bore 58 mm, stroke 58.7 mm, compression 11.6:1, 4-valve head with rocker-arm valve actuation. The single biggest deletion versus the R15 V3 in 2019 was VVA. Yamaha kept VVA on the R15 V3 in markets like Indonesia and India for the faired bike, but the MT-15 V1 sold in India between 2019 and 2020 ran a non-VVA cam profile that gives up a low- and mid-range torque shoulder around 6,000 rpm. The V2 refresh in 2022 added VVA back and bumped the bike to 18.5 hp; the V1 owners stayed at 18.4 hp for the life of the model.',
  },
  {
    type: 'p',
    text: 'The other deletions matter less but compound: no clip-ons, no full fairing, no rear-set pegs, slightly taller wide handlebar, and an upright riding position. Dry mass is 134 kg versus 139 kg for the R15 V3, which sounds like an advantage but isolated mass changes on a quarter-mile rarely show up the way you expect when the rider position is also changing the aerodynamic profile. The MT-15 V1 is heavier in trap-line drag than the V3 even though it is lighter on the kerb.',
  },
  {
    type: 'h2',
    text: 'Stock-Tune Simulation Numbers',
  },
  {
    type: 'p',
    text: 'Running the MT-15 V1 in MotoQuant under Aamby Valley November conditions (roughly 1,100 m density altitude, 22 °C ambient, dry concrete, the OEM 140/70-17 MRF Zapper rear at μ_peak around 1.10) and a 78 kg rider on the 134 kg dry bike produces:',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'Value', 'Source'],
      ['Quarter-mile ET', '17.05 s', 'MotoQuant sim (sim-only)'],
      ['Trap speed', '125.5 km/h', 'MotoQuant sim'],
      ['60-foot time', '~2.9 s', 'MotoQuant sim'],
      ['Claimed top speed', '~131 km/h', 'Yamaha India / BikeWale'],
      ['Cluster bias band', '+0.5 to +1.0 s', 'entry_150_200 cluster'],
    ],
  },
  {
    type: 'p',
    text: 'There is no published Indian Autos Mag or BikeWale instrumented quarter-mile ET on the MT-15 V1 at the time of writing — only a 0-100 km/h test of around 11.7 seconds and a manufacturer claim of 131 km/h top speed. The simulator carries a documented +0.5 to +1.0 second slow bias on the entry_150_200 cluster, so a competent rider on a warmed bike with sticky rubber is plausibly running closer to 16.3 to 16.7 seconds on a real strip. The bias is honest, not a bug — most published Indian 0-100 numbers in this class come from non-instrumented runs converted into ETs with a 1.6 multiplier, which under-predicts the real timed quarter on small-cc bikes by exactly this margin.',
  },
  {
    type: 'callout',
    text: 'Why the simulator under-predicts small-cc Indian ETs: the cluster bias is calibrated against the most reliable instrumented sources available, which are mostly litre-bike magazine tests. Indian 150cc-200cc instrumented data is thin, so the model is conservatively biased to the slower end of plausible until Dragy uploads start flowing through the Phase 3 calibrator.',
  },
  {
    type: 'h2',
    text: 'MT-15 V1 vs YZF-R15 V3: Same Engine, Different ET',
  },
  {
    type: 'p',
    text: 'The MT-15 V1 and the R15 V3 share an engine block, a service-manual gear cassette, the same 14F/42R sprocket pair, and the same 520-pitch chain. The R15 V3 sold in India in 2019 ran VVA and made 19.04 hp at 10,000 rpm; the MT-15 V1 ran no-VVA and made 18.4 hp at the same 10,000 rpm. So why does the MT-15 V1 sim at 17.05 seconds while the R15 V3 sim runs closer to 16.95 seconds under matched conditions, despite being 5 kg lighter on the kerb?',
  },
  {
    type: 'table',
    rows: [
      ['Spec', 'MT-15 V1 (2019)', 'YZF-R15 V3 (2019)'],
      ['Displacement', '155.09 cc', '155.09 cc'],
      ['Peak hp', '18.4 @ 10,000 rpm', '19.04 @ 10,000 rpm'],
      ['Peak torque', '14.7 Nm @ 8,500 rpm', '14.7 Nm @ 8,500 rpm'],
      ['VVA cam', 'No', 'Yes (above ~7,400 rpm)'],
      ['Dry mass', '134 kg', '139 kg'],
      ['Gearing', '6-spd · F14/R42 · 520', '6-spd · F14/R42 · 520'],
      ['Cd (estimated)', '~0.62', '~0.50'],
      ['Frontal area', '~0.43 m²', '~0.40 m²'],
      ['Rider position', 'Upright commuter', 'Aggressive sport'],
    ],
  },
  {
    type: 'p',
    text: 'Three things are happening. First, VVA. The R15 V3 cam switches profile above roughly 7,400 rpm and recovers about 0.6 hp at the top end while filling a torque dip the MT-15 V1 has between 6,000 and 7,500 rpm. On a quarter-mile pass the bike spends most of second through fourth gear at 8,500 to 10,500 rpm, which is squarely inside the VVA-on zone. So the MT-15 is not just down on peak — it is down on power right where the run actually lives.',
  },
  {
    type: 'p',
    text: 'Second, aerodynamics. The R15 V3 fairing plus low clip-ons plus a tucked rider puts the bike at roughly Cd 0.50 with frontal area 0.40 m². The MT-15 V1, with its wide handlebar, upright rider, and exposed engine, sits closer to Cd 0.62 and frontal area 0.43 m². At 125 km/h the aerodynamic drag force on the MT-15 V1 is about 19 percent higher than on the R15 V3, and that drag delta dominates the final 80 metres of the run where engine power and aero force are roughly balanced. The 5 kg mass advantage helps the launch but cannot pay for the drag at trap.',
  },
  {
    type: 'p',
    text: 'Third, the no-VVA cam profile means the MT-15 V1 wants to be shifted slightly earlier than the R15 V3. The simulator log shows the V1 upshifting from third to fourth at around 10,200 rpm, fourth to fifth at 10,000 rpm, and crossing the trap line in fifth at 9,200 rpm. The R15 V3 under matched conditions holds gears a few hundred rpm longer because the VVA-on cam keeps making power past the no-VVA torque peak. A real-world MT-15 V1 rider who short-shifts from feel — which is most of them, since the bike sounds finished above 9,500 — gives back another tenth.',
  },
  {
    type: 'h2',
    text: 'MT-15 V1 vs Pulsar NS200 vs Apache RTR 200 4V',
  },
  {
    type: 'p',
    text: 'The more useful Indian comparison for an MT-15 V1 owner is against the 200cc class one rung up. The MT-15 V1 has the better chassis, better brakes, and a more sophisticated DOHC four-valve top end than either the Pulsar NS200 or the Apache RTR 200 4V — but it concedes 5 hp and roughly 5 Nm to both. On the strip, displacement wins:',
  },
  {
    type: 'table',
    rows: [
      ['Bike', 'Sim ET', 'Sim trap', 'Dry mass', 'Peak hp', 'Peak rpm'],
      ['Yamaha MT-15 V1', '17.05 s', '125.5 km/h', '134 kg', '18.4', '10,000'],
      ['Bajaj Pulsar NS200', '~15.8 s', '~130 km/h', '152 kg', '24.5', '9,750'],
      ['TVS Apache RTR 200 4V', '~16.2 s', '~127 km/h', '153 kg', '20.5', '8,500'],
      ['Hero Xtreme 200S 4V', '~17.4 s', '~125 km/h', '158 kg', '19.1', '8,500'],
    ],
  },
  {
    type: 'p',
    text: 'The MT-15 V1 sits inside the entry-200-300 cluster on a power-to-weight basis (137 hp per tonne dry) but outside it on absolute trap speed because the bike runs out of fifth gear before it runs out of road. The NS200 finishes the run in sixth at around 10,400 rpm and the Apache 4V in fifth at around 9,200 rpm, both pulling harder at the trap than the MT-15 is capable of from a no-VVA 155cc top end. The Xtreme 200S 4V is the only bike in this cluster the MT-15 V1 beats outright in ET, and the gap is only 0.35 seconds.',
  },
  {
    type: 'p',
    text: 'For an Indian buyer cross-shopping these four, the drag-strip number is one input among many. The MT-15 V1 is the most expensive of the four on the secondary market (₹1.55 lakh on-road in 2026 for a clean low-kilometre 2019 example versus around ₹1.4 lakh for the NS200 and Apache 4V and ₹1.35 lakh for the Xtreme 4V). The MT-15 V1 also has by far the most sophisticated chassis — Deltabox frame, six-speed close-ratio gearbox, 282 mm front disc with ByBre two-piston caliper, 17-inch wheels with MRF Zapper FYM radials. If you care about handling and brake feel more than ET, the MT-15 V1 is the right answer. If you care only about quarter-mile time, the NS200 wins by 1.25 seconds and costs less.',
  },
  {
    type: 'h2',
    text: 'Where the Cheap Tenths Live on a Stock MT-15 V1',
  },
  {
    type: 'p',
    text: 'Because the bike is no-VVA and revs to 11,000, the cheap tenths cluster around two things: holding peak power longer and reducing the gearing-cap that costs the V1 its trap speed. The MotoQuant parts-ROI engine ranks every catalog mod by ₹ per tenth on this specific bike, and the ranking is unambiguous:',
  },
  {
    type: 'table',
    rows: [
      ['Mod', 'ET gain', 'Indian price', '₹ per tenth'],
      ['13F front sprocket', '~0.18 s', '~₹450', '~₹250'],
      ['Apollo Alpha H1 140/70-17 rear', '~0.35 s', '~₹3,400', '~₹970'],
      ['DNA Stage 2 air filter', '~0.12 s', '~₹3,200', '~₹2,670'],
      ['Powertronic ECU flash (no-VVA map)', '~0.20 s', '~₹13,500', '~₹6,750'],
      ['SC-Project CR-T slip-on (off-road)', '~0.15 s', '~₹38,000', '~₹25,300'],
    ],
  },
  {
    type: 'p',
    text: 'The sprocket and tire combination costs roughly ₹3,850 and shaves close to half a second off the simulator ET. That is the highest-ROI ₹3,850 you can spend on a 155cc Indian bike. The Powertronic flash is the third tenth-buyer if you are willing to give up the OEM warranty (most 2019-2020 MT-15 V1s are out of warranty in 2026 anyway). Beyond those three the cost-per-tenth ramps fast, and the SC-Project slip-on is more about exhaust note than ET on a bike making only 18.4 hp.',
  },
  {
    type: 'callout',
    text: 'Fastest cheap path on the MT-15 V1: 13F front sprocket plus a sport-compound 140/70-17 rear tire. That is roughly ₹3,850 for half a second of ET. Skip the slip-on unless you also want the noise — the gain is real but the cost per tenth is brutal on a bike with sub-25 hp.',
  },
  {
    type: 'h2',
    text: 'Why the Gearing Cap Is the Story',
  },
  {
    type: 'p',
    text: 'The MT-15 V1 ships from Yamaha India with 14F front, 42R rear sprockets and a 520 chain. The cassette ratios are [2.833, 1.875, 1.429, 1.166, 0.963, 0.840] — close-ratio at the top, sport-bike-style. With a 140/70-17 rear at rolling radius about 296 mm, sixth gear at 10,000 rpm gives a theoretical road speed of around 134 km/h, which lines up almost exactly with the Yamaha-claimed 131 km/h. The bike is gearing-limited in sixth, not power-limited.',
  },
  {
    type: 'p',
    text: 'The simulator shows the MT-15 V1 crossing the trap line in fifth gear at 9,200 rpm. Sixth never engages on a stock quarter-mile pass — the run is over before the gear is needed. A one-tooth-down front sprocket swap to 13F shortens every gear by about 7 percent, which means the bike now finishes the run in fifth at closer to 9,800 rpm (further inside the powerband) and the trap speed bumps by roughly 1.5 km/h while ET drops by about 0.18 seconds. The trade-off is a 7 percent reduction in top speed, which on a bike that never sees its claimed 131 km/h in normal use is essentially free. This is the same gearing-cap story that runs through every small-cc Indian bike on the simulator — see the Why Your R15 Won&apos;t Hit 14s analysis for the same physics on the faired sibling.',
  },
  {
    type: 'h2',
    text: 'Run Your Own Numbers',
  },
  {
    type: 'p',
    text: 'If you own an MT-15 V1 (or are deciding between it and an R15 V3, NS200, Apache 4V, or Xtreme 200S 4V), the MotoQuant simulator at motoquant.in lets you sweep rider weight, ambient temperature, density altitude, tire choice, gearing, and parts-catalog mods to see exactly where your tenths come from. The cluster bias is built into the model — when the simulator reports 17.05 seconds, a competent rider on a warmed bike with sport rubber should expect the strip to confirm closer to 16.3 to 16.7 seconds.',
  },
  {
    type: 'p',
    text: 'More relevant for everyday tuning: the simulator&apos;s parts-ROI engine quantifies cost-per-tenth for every bike in the catalog. On the MT-15 V1 the answer is the same as on the R15 V3 and the Xtreme 4V — sprocket and tire first, exhaust last. Most 155cc owners spend money in the wrong order, which is why most modded MT-15 V1s cost ₹50,000 in upgrades and gain less ET than a ₹3,850 sprocket-and-tire combo would have delivered.',
  },
  {
    type: 'p',
    text: 'Two final caveats. First, every number in this post is a stock-tune simulation under specific Aamby Valley November conditions. Change the rider weight, the ambient temperature, the surface, or the launch technique and the absolute ETs shift, but the relative ordering of which mods help most stays stable. Second, the simulator entry_150_200 cluster bias is being actively closed. The May 2026 Hypothesis property tests pin the four load-bearing physics knobs (mass, dyno-curve magnitude, Cd, frontal area) to monotonic invariants, and the small-cc clutch over-clutching rewrite from April 2026 already cut the cluster bias roughly in half. The MT-15 V1 number you see today might tighten by another 0.3 to 0.5 seconds as more Indian small-cc Dragy data lands.',
  },
  {
    type: 'p',
    text: 'If you take one practical thing from this post, take this: the MT-15 V1 is gearing-limited and aero-limited, not power-limited. The R15 V3 shares the engine but wins by a tenth on the strip because the fairing and tuck close almost 20 percent of the aero gap at trap speed. You cannot bolt a fairing onto a naked, but you can drop a sprocket and fit a sticky tire for ₹3,850. That is the entire MT-15 V1 quarter-mile playbook in one sentence.',
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
          datePublished: '2026-05-24',
        })}
      />
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {['Yamaha', 'MT-15 V1', 'Indian 155cc', 'naked sport', 'physics'].map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Yamaha MT-15 V1 Quarter-Mile Physics: 155cc Naked Drag
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
            24 May 2026 · 10 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        {/* Internal links / related reading */}
        <div className="max-w-2xl mx-auto mt-16">
          <h3 className="font-display font-bold text-lg text-white mb-4">Related reading</h3>
          <ul className="text-sm text-white/70 space-y-2">
            <li>
              ·{' '}
              <Link
                href="/blog/why-your-r15-wont-hit-14s"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Why Your R15 Won&apos;t Hit 14s
              </Link>{' '}
              — same 155cc engine block as the MT-15 V1, fairing-on, faster anyway.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/hero-xtreme-200s-4v-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Hero Xtreme 200S 4V Quarter-Mile Physics
              </Link>{' '}
              — closest 200cc rival on the slow end of the small-cc cluster.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Pulsar NS200 vs Apache RTR 200 4V
              </Link>{' '}
              — the 200cc class the MT-15 V1 cross-shoppers usually end up in.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/how-the-motoquant-physics-engine-works"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How the MotoQuant Physics Engine Works
              </Link>{' '}
              — the 15-sub-model architecture behind every ET prediction in this post.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/how-to-tune-for-aamby-valley-in-november"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
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
            <div className="font-display font-bold text-white mb-1">Run the MT-15 V1 yourself</div>
            <div className="text-white/60 text-sm">
              Free simulator — pick the Yamaha MT-15 V1, dial in your local conditions and a sport tire, and watch the ET tighten live.
            </div>
          </div>
          <Link
            href="/simulator?bike=yamaha-mt-15-v1"
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
