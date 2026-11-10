import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'ktm-duke-390-vs-rc-390-quarter-mile-physics';
const TITLE = 'KTM Duke 390 vs RC 390: quarter-mile physics at Aamby Valley';
const DESCRIPTION =
  'KTM Duke 390 vs RC 390 on the quarter mile. MotoQuant simulates the RC 390 at roughly 13.5s and 166 km/h trap, the Duke 390 at roughly 13.7s and 162 km/h. Same engine, two tenths apart at Aamby Valley. Where the gap comes from, four cost-per-tenth mods under ₹25,000, and the 11.342s Fast Track Racing record.';

export const metadata = {
  title: 'KTM Duke 390 vs RC 390 quarter mile | MotoQuant',
  description: DESCRIPTION,
  keywords: [
    'ktm duke 390 quarter mile',
    'rc 390 drag time',
    'duke 390 vs rc 390',
    'fastest ktm 390 india',
    'duke 390 et',
    'rc 390 0-100',
    'best mods for ktm rc 390 india',
    'rc 390 exhaust price india',
    'ktm 390 valley run',
    'duke 390 cost per tenth',
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
    text: 'The KTM RC 390 and the KTM Duke 390 share an engine, a frame layout, a gearbox, a sprocket pair, and a parts-bin of brake hardware. They do not share a body, a rider position, or a frontal area. MotoQuant simulates the 2022-onwards RC 390 at roughly 13.5 seconds and 166 km/h trap under matched Aamby Valley November conditions; the matching Duke 390 lands at roughly 13.7 seconds and 162 km/h. Two tenths of ET separate the two bikes on a strip, and almost all of it is aerodynamics. Fast Track Racing India clocked a heavily-modded Duke 390 at 11.342 seconds at the ASEAN Superfast event in 2023, about 2.3 seconds quicker than the stock simulation.',
  },
  {
    type: 'h2',
    text: 'Same engine, two bodies',
  },
  {
    type: 'p',
    text: 'The 2022 RC 390 and the post-2017 Duke 390 (the second-generation Duke, before the 2024 GP-inspired third gen) both run the LC4c single: Bajaj-built at Chakan, KTM-engineered. Displacement is 373.3 cc from an 89.0 mm bore and 60.0 mm stroke. Compression is 12.5:1, the head is DOHC with four valves, fuel injection is Bosch, cooling is liquid. Both bikes make 43.5 hp at 8,000 rpm and 37 Nm at 6,500 rpm. The 6-speed cassette is identical (ratios [3.230, 2.153, 1.571, 1.272, 1.089, 0.927]), as are the 16-tooth front and 45-tooth rear sprockets running 520 chain. The slipper clutch and the ride-by-wire throttle are shared. Even the front 110/70-17 tire is the same.',
  },
  {
    type: 'p',
    text: 'What differs is everything from the seat up. The RC 390 wears a full sport fairing, low clip-on bars, rear-set pegs, and a 13.7-litre tank shaped to be tucked into. The Duke 390 wears a naked exoskeleton-styled frame cover, wide handlebars, slightly more relaxed pegs, and the rider sits roughly 80 mm taller and significantly more upright. Catalog mass is identical at 149 kg dry, wheelbase is identical at 1,365 mm, and both bikes run a 150/60-17 rear tire. Underneath, it is the same chassis. The difference is the wind.',
  },
  {
    type: 'h2',
    text: 'Stock sim numbers at Aamby Valley',
  },
  {
    type: 'p',
    text: 'Running both bikes through MotoQuant at matched Aamby Valley November conditions (density altitude around 1,100 m, 22°C ambient, dry asphalt with the OEM Metzeler Sportec M5 rear tire at μ_peak ≈ 1.10, 70 kg rider in stock tuck) gives these numbers:',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'RC 390 (sim)', 'Duke 390 (sim)', 'Δ (Duke − RC)'],
      ['Quarter-mile ET', '~13.5 s', '~13.7 s', '+0.2 s'],
      ['Trap speed', '~166 km/h', '~162 km/h', '−4 km/h'],
      ['60-foot time', '~2.21 s', '~2.22 s', '+0.01 s'],
      ['1/8-mile ET', '~8.75 s', '~8.82 s', '+0.07 s'],
      ['Top gear at trap', '5th, ~7,400 rpm', '5th, ~7,250 rpm', '−150 rpm'],
      ['Cluster bias band', '±0.4 s mid-twin-300-500', '±0.4 s mid-twin-300-500', '–'],
    ],
  },
  {
    type: 'p',
    text: 'Both ETs sit inside MotoQuant\'s mid-twin-300-500 cluster bias band of about ±0.4 seconds. The relative gap (two tenths and four km/h) is stable across rider weight, ambient temperature, and density altitude sweeps. The Duke 390 is always slower, by margins that match a Cd × A delta. The bikes are roughly equal off the line, where aerodynamics barely matters, and the gap opens as speed climbs: the RC 390 is seven hundredths ahead at the 1/8-mile mark and two tenths ahead at the trap. Neither bike has a Dragy timeslip in our benchmark set yet, so the absolute numbers carry the cluster band of uncertainty, but the order of the two bikes is structural.',
  },
  {
    type: 'callout',
    text: 'As a check, Autocar India\'s stock GPS-timed runs put the Duke 390 around 13.6–14.0 seconds and the RC 390 around 13.3–13.7 seconds in their March 2022 head-to-head test, with the RC 390 consistently quicker by 0.2–0.4 seconds. Our simulator lands in the upper half of both bands and gets the gap right.',
  },
  {
    type: 'h2',
    text: 'Where the two tenths come from',
  },
  {
    type: 'p',
    text: 'Three things differ between the bikes. Two of them matter on the strip.',
  },
  {
    type: 'table',
    rows: [
      ['Spec', 'RC 390', 'Duke 390', 'ET cost on Duke'],
      ['Cd', '0.68', '0.81', '~0.12 s'],
      ['Frontal area', '0.41 m²', '0.47 m²', '~0.05 s'],
      ['Cd × A', '0.279', '0.380', '(sum: ~0.17 s, partially offsetting)'],
      ['Rider position', 'Tucked, clip-ons', 'Upright, wide bars', 'baked into Cd above'],
      ['Dry mass', '149 kg', '149 kg', '0 s'],
      ['Engine, gearing, tires', 'Identical', 'Identical', '0 s'],
    ],
  },
  {
    type: 'p',
    text: 'Cd × A on the Duke 390 is 36 percent higher than on the RC 390. That accounts for the whole ET delta and a little more. The simulator estimates roughly 0.17 seconds of pure-drag penalty, partly offset because a more upright rider usually loads the rear tire a few percent harder off the line (a tiny ET benefit, too small to show in two-decimal numbers). The net result is two tenths of ET and four km/h of trap, all of it aerodynamic.',
  },
  {
    type: 'p',
    text: 'This is also why the gap shrinks at lower-altitude, denser-air strips and grows at high-altitude, thinner-air ones. At MMRT (Chennai, near sea level, denser air, μ_peak ≈ 1.05) the drag penalty on the Duke is larger in absolute terms because aerodynamic force scales with air density; the simulator widens the gap to roughly 0.25 seconds at MMRT, with the RC 390 also pulling about 0.3 seconds quicker than its Aamby Valley number because the engine is making peak power in denser air. At a high-altitude venue like Leh at 3,500 m density altitude the gap shrinks below 0.15 seconds: thinner air, less drag penalty, both bikes losing power proportionally. Nobody drag-races at Leh; the simulator just lets you check that the physics behaves as it should.',
  },
  {
    type: 'h2',
    text: 'The Fast Track Racing 11.342s record',
  },
  {
    type: 'p',
    text: 'Fast Track Racing India entered the ASEAN Superfast Drag Challenge in Thailand in 2023 with a heavily-modded KTM 390 and ran an 11.342-second quarter-mile pass. That same team also clocked an 11.732 at Valley Run 2025 Winter at Aamby Valley. Both are real, legitimate runs, and both are roughly two and a half seconds quicker than a stock RC 390 or Duke 390 will run.',
  },
  {
    type: 'p',
    text: 'A serious Indian drag KTM 390 is not the machine that rolls off the showroom floor. A bike that runs an 11.3 typically has a free-flow exhaust pulling 2–3 hp at the top end, a full ECU re-flash adding another 2–3 hp and sharper throttle response, a custom intake giving back another hp or two, a forward-shifted swingarm with a lengthened wheelbase to fight wheelie, a drag-prep slick or DOT-drag rear tire bumping μ_peak from 1.10 to 1.35, lighter wheels dropping rotational inertia, and a rider trained to launch the bike at the precise clutch-engagement RPM that maximises the slip phase without bogging the engine. Each of those mods is worth 0.1 to 0.3 seconds. Stack five or six of them with a well-prepared rider and the bike drops from the 13.5-second range into the 11.5-12.0 second window. The Fast Track Racing record sits at the edge of that range, set by a team that has been refining the same chassis for years.',
  },
  {
    type: 'p',
    text: 'For a regular owner whose KTM 390 sees a strip twice a year and a commute the other 363 days, the useful question is how to get from 13.7s to 13.0s without making the bike unrideable on a Monday morning. That one is much easier to answer.',
  },
  {
    type: 'h2',
    text: 'Cost per tenth: four mods under ₹25,000',
  },
  {
    type: 'p',
    text: 'MotoQuant\'s parts-ROI engine ranks mods by cost-per-tenth at current Indian retail prices. The May 2026 price refresh scraped or formula-priced parts from Store4Riders, RidersPlanet, Performance Racing Store, KustomHub, Powerstroke, and Motodelic. These are the four most cost-effective mods under ₹25,000 each for the RC 390. The Duke 390 numbers are within ₹500 of these because the parts are physically identical.',
  },
  {
    type: 'table',
    rows: [
      ['Mod', 'ΔET (sim)', 'ΔTrap', 'Indian price', '₹/tenth'],
      ['Front sprocket drop (16T → 15T)', '~0.20 s', '+2 km/h', '₹950', '~₹475'],
      ['Sticky rear (TVS Eurogrip Protorq Extreme)', '~0.15 s', '+1 km/h', '₹6,400', '~₹4,270'],
      ['Powertronic Stage 1 ECU re-flash', '~0.22 s', '+3 km/h', '₹14,500', '~₹6,600'],
      ['DNA P-KT2S22-S2 air filter (drop-in)', '~0.08 s', '+1 km/h', '₹3,200', '~₹4,000'],
      ['Total (sprocket + tire + ECU + filter)', '~0.55 s', '+7 km/h', '₹25,050', '–'],
    ],
  },
  {
    type: 'p',
    text: 'The sprocket swap is the cheapest tenth on either bike by an order of magnitude. Dropping one tooth at the front shortens overall gearing by 6.25 percent, which keeps the engine higher in its power band through the first three gears, where the LC4c makes most of its useful torque. The side effects are roughly 4 percent lower top speed (irrelevant on a strip where you trap at 165–170 km/h anyway, well below the bike\'s ~180 km/h capability), slightly busier highway cruising and slightly higher fuel burn in stop-go traffic. None of those matter if you take the bike to the strip, and the whole job costs under a thousand rupees.',
  },
  {
    type: 'p',
    text: 'The TVS Eurogrip Protorq Extreme is one of the few Indian-made rear tires that clearly outgrips the OEM Metzeler Sportec M5 in dry-pavement launch conditions, particularly on a strip that has not been freshly prepped. It also costs half as much as a comparable Pirelli Rosso III. The Powertronic Stage 1 re-flash is a piggyback ECU that the Indian KTM community has run for several years; it adds roughly 1.5 to 2 hp of top-end power and noticeably sharpens the throttle map. The DNA filter is the cheapest mod on the list with a measurable airflow gain, and it needs no retune.',
  },
  {
    type: 'p',
    text: 'After all four mods, MotoQuant simulates the RC 390 at roughly 12.95 seconds and 173 km/h trap; the Duke 390 lands at roughly 13.15 seconds and 169 km/h. The gap stays at two tenths because all four mods work on engine and traction, not aerodynamics. Closing it means fixing the Duke\'s drag, and on a naked that takes a fly-screen, sport bodywork and an RC-style tuck, at which point you have built an RC 390 the hard way. If you want the strip number, buy the RC 390. If you want the everyday bike, buy the Duke; the two tenths are the cost of upright comfort.',
  },
  {
    type: 'callout',
    text: 'Three caveats. First, every simulator number in this post sits inside the mid-twin-300-500 cluster bias band of ±0.4 seconds; a real Dragy timeslip would tighten the prediction. Second, the Powertronic Stage 1 figure quoted here is the conservative end of the range: published dynos for that flash run from 1.2 to 2.5 hp depending on the test bike, the tune revision, and the riding altitude. Third, Indian aftermarket pricing shifts every quarter; these numbers reflect May 2026 retail.',
  },
  {
    type: 'h2',
    text: 'What about the 2024 Gen 3 Duke 390?',
  },
  {
    type: 'p',
    text: 'KTM launched a third-generation Duke 390 in 2024 with revised internals: a longer-stroke 399 cc displacement (89.0 × 64.0 mm versus the older 89.0 × 60.0 mm), a higher 45 hp peak power figure, a new TFT cluster, and a slightly heavier dry mass around 161 kg. That bike is not in the MotoQuant catalog as of this writing (May 2026), and the new RC 390 on the Gen 3 chassis is not widely sold yet either. When both are added, the comparison will shift a little. The Gen 3 Duke makes more peak power but is also heavier and slightly thirstier; we expect its stock ET to fall in the 13.4 to 13.7 second range at Aamby Valley, between the 2017–2023 Duke 390 and a stock RC 390. We will rerun this comparison when those entries land.',
  },
  {
    type: 'p',
    text: 'Until then, the 2017–2023 Duke 390 is still the most common version on Indian roads, with hundreds of thousands of units sold across the seven model years and a strong used-bike market under ₹2 lakh. The RC 390 in current trim sits at roughly ₹3.18 lakh ex-showroom; the second-gen Duke 390 used market hovers around ₹1.50–₹1.80 lakh depending on year and kilometres. For the value buyer, a used Duke 390 plus the four mods above costs less than a new RC 390 and runs the strip within three tenths of one.',
  },
  {
    type: 'h2',
    text: 'Run your own numbers',
  },
  {
    type: 'p',
    text: 'The KTM RC 390 and KTM Duke 390 are the same bike with two different bodies. The RC 390 runs two tenths quicker over the quarter-mile because its fairing and tucked rider position trim roughly 36 percent of frontal drag area. Every other lever on either bike (engine, gearbox, sprockets, chassis, tires, mass) is identical, and mods scale roughly equally on both. So the choice is about riding position, daily comfort, and how many days a year you spend on a strip versus in traffic. Three-quarters of Indian KTM 390 buyers pick the Duke for everyday rideability; one-quarter pick the RC for the body.',
  },
  {
    type: 'p',
    text: 'The MotoQuant simulator at motoquant.in lets you sweep rider weight, density altitude, ambient temperature, tire compound, and any combination of the 546 parts in the catalog against either bike, side by side. You can answer the practical questions ("for my 75 kg rider weight and my home strip at 600 m DA, will the Duke or RC be faster after a sprocket drop and a re-flash?") without trusting a YouTube comparison or a press release. A real Dragy timeslip from either bike, submitted through the "Submit a timeslip" form, would tighten the prediction. Until that data exists, the ±0.4 second cluster bias band is the real uncertainty.',
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

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          <div className="flex flex-wrap gap-2 mb-6">
            {['KTM', 'Duke 390', 'RC 390', 'Indian 400cc', 'comparison'].map((t) => (
              <span
                key={t}
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            KTM Duke 390 vs RC 390: quarter-mile physics at Aamby Valley
          </h1>
          <div className="text-sm text-white/60 mb-12">
            18 May 2026 · 12 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        <div className="max-w-2xl mx-auto mt-16 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Simulate the Duke 390 vs RC 390 side by side</div>
            <div className="text-white/60 text-sm">
              Sweep rider weight, density altitude, sprocket choice, ECU re-flash, and any of the 546 parts in the catalog. See the ET change before you spend a rupee.
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
                href="/blog/pulsar-ns400z-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Pulsar NS400Z quarter-mile physics (and why an RC 390 still wins)
              </Link>:{' '}
              the same RC 390 reference, now compared against Bajaj&apos;s first 400cc Pulsar.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Pulsar NS200 vs Apache RTR 200 4V: which wins the quarter mile?
              </Link>:{' '}
              the same comparison framing one displacement class down.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/the-physics-of-a-perfect-launch"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                The physics of a perfect launch
              </Link>:{' '}
              clutch slip, weight transfer, and the first 60 feet that matter most on a 390-class single.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/how-to-tune-for-aamby-valley-in-november"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to tune for Aamby Valley in November
              </Link>:{' '}
              the venue conditions used for every sim in this post, plus the DA penalty math.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/how-the-motoquant-physics-engine-works"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How the MotoQuant physics engine works
              </Link>:{' '}
              what is inside the simulator that produced these numbers, and what the cluster bias bands mean.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>:{' '}
              Duke 390, RC 390, NS400Z, Dominar 400, Apache RR 310, and 390+ other bikes with full spec sheets and OEM tire fitments.
            </li>
          </ul>
        </div>
      </article>

      <SiteFooter />
    </div>
  );
}
