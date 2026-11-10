import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'husqvarna-svartpilen-250-vs-ktm-duke-250-quarter-mile-physics';
const TITLE = 'Husqvarna Svartpilen 250 vs KTM Duke 250: quarter-mile physics';
const DESCRIPTION =
  'MotoQuant simulates the Husqvarna Svartpilen 250 at 14.77s / 149 km/h and the KTM Duke 250 at 15.08s / 143 km/h. Same engine, same Bajaj Chakan plant; here is why the Husky is 0.31s quicker at the strip.';

export const metadata = {
  title: 'Husqvarna Svartpilen 250 vs KTM Duke 250 quarter mile | MotoQuant',
  description: DESCRIPTION,
  keywords: [
    'husqvarna svartpilen 250 quarter mile',
    'svartpilen 250 vs duke 250',
    'svartpilen 250 vs ktm duke 250 drag',
    'husqvarna svartpilen 250 drag time',
    'svartpilen 250 india top speed',
    'ktm duke 250 quarter mile',
    'ktm duke 250 drag time india',
    'duke 250 vs svartpilen 250 0-100',
    'svartpilen 250 india price',
    'pierer mobility india platform 250',
    'svartpilen 250 chakan',
    'husqvarna 250 cd value',
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `https://motoquant.in/blog/${SLUG}`,
    type: 'article',
    publishedTime: '2026-05-25T00:00:00Z',
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: 'MotoQuant runs the Husqvarna Svartpilen 250 at 14.767 seconds with a 149.2 km/h trap. The KTM Duke 250 (same 248cc LC4c single, same Bajaj Chakan assembly line, same Pierer Mobility India parts shelf) runs 15.083 seconds and 143.3 km/h. Two bikes that share an engine end up 0.316 seconds and 5.9 km/h apart. Almost every Indian buyer assumes the Duke is quicker because it carries the KTM badge. The simulator disagrees, and the reasons are in the gear charts.',
  },
  {
    type: 'h2',
    text: 'Same engine, same plant, same parts bin',
  },
  {
    type: 'p',
    text: 'Both bikes use the LC4c-250 platform: a 248.76 cc liquid-cooled DOHC 4-valve single with a 72.0 mm bore and 61.1 mm stroke, 12.5:1 compression, Bosch EMS fuel injection. They are built side by side at Bajaj Auto’s Chakan plant under the KTM-Husqvarna Pierer Mobility India platform deal. They share crankcases, head castings, the six-speed cassette gearbox, the PASC slipper clutch and the Bybre 4-piston front caliper. Factory power is effectively identical at 30 hp at the crank: the Duke 250 is rated at 30 hp at 8,000 rpm and the Svartpilen at 30 hp at 9,000 rpm, and both make roughly 25 Nm of peak torque around 7,250 rpm. Some markets get a slightly punchier 31 hp 250 Duke, but the simulator compares the Indian-market 30 hp spec.',
  },
  {
    type: 'p',
    text: 'The bikes differ in final drive and aerodynamics. The Duke 250 runs F16 / R47 sprockets. KTM picked that taller setup because Duke owners ride at city speeds 80 percent of the time, and a tall final drive cuts engine RPM at an 80 km/h cruise. The Svartpilen runs F14 / R46. Per Husqvarna India’s 2024 parts catalogue, that is a deliberately shorter final drive, chosen to suit the bike’s mid-range torque. Husqvarna markets the Svartpilen as the bike that pulls harder out of corners and in the lower gears. On a drag strip, that gearing choice pays off.',
  },
  {
    type: 'h2',
    text: 'The simulator numbers',
  },
  {
    type: 'p',
    text: 'Both bikes ran in MotoQuant under matched Aamby Valley November conditions: density altitude around 1,100 m, 22°C ambient, dry asphalt with OEM tire choices, 78 kg rider. These are stock-tune outputs from the production sweep, with no power boost, no mass cut and no parts from the catalogue.',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'KTM Duke 250', 'Husqvarna Svartpilen 250', 'Delta'],
      ['Quarter-mile ET', '15.083 s', '14.767 s', '−0.316 s (Husky)'],
      ['Trap speed', '143.3 km/h', '149.2 km/h', '+5.9 km/h (Husky)'],
      ['60-foot speed', '52.1 km/h', '51.7 km/h', '~tied'],
      ['Peak power', '30 hp @ 8,000 rpm', '30 hp @ 9,000 rpm', 'identical at peak'],
      ['Peak torque', '24 Nm @ 6,500 rpm', '25 Nm @ 7,250 rpm', '~tied'],
      ['Final drive (F/R)', '16/47 (2.94)', '14/46 (3.29)', '+12% shorter (Husky)'],
      ['Dry mass', '148 kg', '144 kg', '−4 kg (Husky)'],
      ['Cd × frontal area', '0.82 × 0.46 m²', '0.66 × 0.42 m²', '−27% drag (Husky)'],
    ],
  },
  {
    type: 'callout',
    text: 'These are sim-only numbers. No Indian magazine has run an instrumented quarter-mile test on the Svartpilen 250 yet, and Autocar India’s GPS-timed 0-100 km/h for the Duke 250 is 5.6 s (the magazines do not time the quarter). The entry-200-300 cc cluster has a documented +0.5 to +1.4 s slow bias, so real-world ETs could be 0.5-1.0 s quicker than the sim figures, with the gap between the two bikes staying about the same.',
  },
  {
    type: 'h2',
    text: 'Where the 0.316-second gap comes from',
  },
  {
    type: 'p',
    text: 'Three things do almost all the work: sprockets most, then drag, then mass.',
  },
  {
    type: 'p',
    text: '1. Final drive. The Husqvarna’s F14 / R46 gives a final-drive ratio of 3.286 against 2.938 for the Duke’s F16 / R47, about 12 percent shorter. With the same six gearbox ratios, the same primary and the same tire rolling radius, the shorter final drive covers less ground per engine revolution, trading top-end gearing for mid-gear acceleration. On a 250 cc bike that reaches the 402-metre trap line in fourth gear, twelve percent more leverage in every gear except top means the Svartpilen is pulling roughly 270 rpm higher than the Duke at the trap. On a 30 hp single whose power curve is steep above 7,500 rpm, those 270 rpm are worth real trap speed.',
  },
  {
    type: 'p',
    text: '2. Aerodynamics. Husqvarna sells the Svartpilen as a flat-tracker: round LED headlight, narrow tank shrouds, no bikini fairing, flat handlebars set forward. The Duke 250 has the high, upright handlebars, larger flat-bar tank flares and bulkier headlight cluster of the Duke family. The simulator uses Cd 0.66 × 0.42 m² for the Svartpilen and Cd 0.82 × 0.46 m² for the Duke, roughly 27 percent less total drag area on the Husky. At 130 km/h that is about 1.7 hp less drag; on a 30 hp single, that is more than 5 percent of the power going into acceleration instead of pushing air. The drag advantage shows most in the trap speed: 5.9 km/h is exactly what 27 percent less drag buys you at 250 cc.',
  },
  {
    type: 'p',
    text: '3. Mass. KTM India’s spec sheet gives the Duke 250 at 148 kg dry. The Svartpilen 250 is 144 kg dry (154 kg kerb minus the roughly 10 kg of fuel in the 9.5-litre tank). The 4 kg gap helps a little at launch, though the simulator has the two bikes essentially tied at 60 feet because traction limits both. After that it adds a small advantage through the rest of the run. With a 78 kg rider the Husky carries 222 kg in total against the Duke’s 226 kg, 1.8 percent less. On its own that is worth maybe 0.05 seconds of ET: real, but small.',
  },
  {
    type: 'h2',
    text: 'Why the result surprises buyers',
  },
  {
    type: 'p',
    text: 'Indian buyers assume a KTM badge means a quicker bike than a Husqvarna badge. Within Pierer Mobility’s line-up that is roughly how the brands are positioned: the Duke is the sport naked and the Husqvarna the street tracker, so the Duke is supposed to be the strip bike. But the sport-naked design choices work against quarter-mile times: taller bars for attacking corners, a taller final drive for road riding, and unfaired body lines that nobody shaped with Cd in mind. The Svartpilen’s flat-tracker styling happens to bring a shorter final drive, less frontal area and slightly less mass, and together they make it the quicker bike at the strip.',
  },
  {
    type: 'p',
    text: 'On platform-shared bikes, matching engine specs tell you little. The LC4c-250 makes 30 hp in both bikes, yet the quarter mile goes to the one whose chassis and final drive were set up for the slower, lower-RPM riding style. The same pattern runs across the segment: the Yamaha MT-15 V1 deep-dive and the Pulsar NS200 vs Apache RTR 200 4V post both find two bikes with similar engine specs half a second apart at the trap because of gear ratios, riding position and frontal area.',
  },
  {
    type: 'h2',
    text: 'Mods, cost per tenth, and which bike to modify',
  },
  {
    type: 'p',
    text: 'Because both bikes share parts, the Indian aftermarket for the LC4c-250 is large and well priced. Powertronic, KustomHub, Big Bird, JT, IRC and Daido all stock parts that fit either bike with minor bracket changes. Cost per tenth from the MotoQuant parts catalogue, cheapest first:',
  },
  {
    type: 'table',
    rows: [
      ['Mod', 'Fits', 'ET gain', 'Price (₹)', '₹/tenth'],
      ['F15 front sprocket (Duke)', 'Duke 250 only', '~0.15 s', '~₹450', '~₹300'],
      ['Pirelli Diablo Rosso II 150/60-17 rear', 'Both', '~0.30 s', '~₹6,200', '~₹2,070'],
      ['K&N drop-in air filter', 'Both', '~0.10 s', '~₹4,300', '~₹4,300'],
      ['Powertronic ECU flash', 'Both', '~0.25 s', '~₹14,000', '~₹5,600'],
      ['SC-Project slip-on (Stainless)', 'Both', '~0.15 s', '~₹38,000', '~₹25,300'],
      ['Full Akrapovic Slip-On Titanium', 'Duke 250', '~0.20 s', '~₹65,000', '~₹32,500'],
    ],
  },
  {
    type: 'p',
    text: 'If you own a Duke 250 and want the Svartpilen’s number, start with the F15 front sprocket. Going from F16 to F15 takes the Duke’s final drive from 2.94 to 3.13. That is still taller than the Svartpilen’s 3.29, but with a sport tire it closes most of the gap. Sprocket and rear tire cost about ₹6,650 together and gain roughly 0.4 to 0.45 seconds in the simulator. That puts a modded Duke ahead of a stock Svartpilen and close to a Svartpilen running the same parts.',
  },
  {
    type: 'p',
    text: 'On a Svartpilen, the sport tire alone is the big mod. The OEM Apollo Alpha H1 in 150/60-17 is a competent street tire, but it is no Pirelli Diablo. Fit a Diablo Rosso II or a Michelin Road 5 and the simulator takes about 0.3 seconds off the stock 14.77, into the 14.4-second range. After that the cost per tenth climbs steeply. An ECU flash takes off another 0.25 seconds for ₹14,000, a marginal call. A slip-on exhaust at ₹38,000+ for 0.15 seconds is brutal value on a sub-25 hp bike.',
  },
  {
    type: 'callout',
    text: 'Fastest cheap setup on the LC4c-250: a Svartpilen with a Diablo Rosso II rear tire (about ₹4.0 lakh on-road + ₹6,200) runs roughly 14.45 s with no other changes. The Duke 250 needs a sprocket swap plus the same tire to match, at roughly ₹4.1 lakh on-road + ₹6,650. The Husky wins stock and stays competitive after mods because it leaves the factory set up the way a drag tuner would set it up.',
  },
  {
    type: 'h2',
    text: 'The LC4c-250 against its class',
  },
  {
    type: 'p',
    text: 'Four sub-300cc nakeds, simulated stock in MotoQuant under matched Aamby Valley November conditions with a 78 kg rider:',
  },
  {
    type: 'table',
    rows: [
      ['Bike', 'Sim ET', 'Sim trap', 'Dry mass', 'Peak hp', 'Final drive'],
      ['Husqvarna Svartpilen 250', '14.77 s', '149 km/h', '144 kg', '30', 'F14 / R46'],
      ['KTM Duke 250 (2024)', '15.08 s', '143 km/h', '148 kg', '30', 'F16 / R47'],
      ['Bajaj Pulsar N250', '~15.4 s', '~137 km/h', '155 kg', '24.5', 'F14 / R45'],
      ['TVS Apache RTR 310', '~14.6 s', '~150 km/h', '169 kg', '35.6', 'F15 / R47'],
    ],
  },
  {
    type: 'p',
    text: 'The Svartpilen sits between the more powerful Apache RTR 310 (a 35.6 hp single, but heavier at 169 kg) and the lighter, less powerful Pulsar N250. The Duke 250 is comfortably ahead of the Pulsar (its taller gearing and identical power output put it 0.3 seconds clear) but clearly behind the better-set-up Husky and the more powerful Apache. If you are choosing on drag-strip ET alone in the sub-300cc segment, the Apache RTR 310 wins outright. If you want the LC4c-250 powertrain (smoother, more refined and more durable than the TVS 312 cc single over long distances), the Svartpilen is the strip choice and the Duke the city choice.',
  },
  {
    type: 'h2',
    text: 'A note on the two power curves',
  },
  {
    type: 'p',
    text: 'The MotoQuant catalogue lists the Duke 250’s peak power at 8,000 rpm and the Svartpilen’s at 9,000 rpm. In real life the two power curves are nearly identical, because it is the same engine: both peak somewhere in the 8,500-9,000 rpm window, depending on which dyno test you trust. The catalogue values come from each maker’s India press kit; KTM India publishes 8,000 rpm for the 30 hp figure and Husqvarna India publishes 9,000 rpm. The real peak is almost certainly the same on both. Because the simulator uses each maker’s stated curve, the Duke gets a slightly broader, lower-revving torque band in the model and the Svartpilen a peakier, higher-revving one. That adds a little to the trap-speed gap, but final drive and frontal area account for most of it. If the Duke’s peak-power RPM were changed to 9,000 to match, the simulator’s ET gap would shrink from 0.316 s to roughly 0.27 s, and the Svartpilen would still be quicker.',
  },
  {
    type: 'h2',
    text: 'Run your own numbers',
  },
  {
    type: 'p',
    text: 'If you are choosing between a Duke 250 and a Svartpilen 250, the salesperson at your local dealer cannot tell you which is quicker, because their training covers engines and ergonomics, not aerodynamics. The simulator at motoquant.in lets you set rider weight, ambient temperature, density altitude, tire choice and final-drive ratio and watch the ETs change live. Both bikes start with the Indian-market 30 hp tune and OEM sprockets. Put the Duke on F15 and the gap shrinks by roughly 0.15 seconds. Put both on Pirelli Diablo Rosso IIs and the gap stays close to the stock figure, because the same tire helps both bikes by roughly the same factor.',
  },
  {
    type: 'p',
    text: 'The spec sheet will not show you why two bikes with the same engine, from the same plant, end up 0.316 seconds apart. The simulator can, because every gear ratio, Cd value and sprocket pair is in the catalogue, and the physics works through the run step by step.',
  },
  {
    type: 'p',
    text: 'Two caveats. Every number in this post is a stock-tune simulation under specific conditions. Change the rider weight, the surface or the launch technique and the absolute ETs move, but the quicker bike stays quicker. And the entry-200-300 cc cluster has a +0.5 to +1.4 s slow bias against real instrumented runs, so expect a competent rider on a warm bike with good launches to beat the sim figures, with the gap between the two bikes roughly constant. The bias will tighten as more Indian small-cc Dragy and VBOX timeslips join the benchmark set.',
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
          datePublished: '2026-05-25',
        })}
      />
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {['Husqvarna', 'Svartpilen 250', 'KTM', 'Duke 250', 'LC4c platform', 'comparison'].map((t) => (
              <span
                key={t}
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Husqvarna Svartpilen 250 vs KTM Duke 250: quarter-mile physics
          </h1>
          <div className="text-sm text-white/60 mb-12">
            25 May 2026 · 11 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        {/* Internal links / related reading */}
        <div className="max-w-2xl mx-auto mt-16">
          <h3 className="font-display font-bold text-lg text-white mb-4">Related reading</h3>
          <ul className="text-sm text-white/70 space-y-2">
            <li>
              ·{' '}
              <Link href="/blog/ktm-duke-390-vs-rc-390-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                KTM Duke 390 vs RC 390 quarter-mile physics
              </Link>:{' '}
              the Duke 250’s bigger sibling, with the same chassis-versus-fairing trade-off at the strip.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                Pulsar NS200 vs Apache RTR 200 4V quarter-mile physics
              </Link>:{' '}
              the same Indian sub-300cc segment, with similar physics levers deciding it.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/best-mods-for-ktm-rc-390-budget-vs-cost-per-tenth" className="text-brand-accent hover:text-brand-orange transition-colors">
                Best mods for KTM RC 390 by cost per tenth
              </Link>:{' '}
              the LC4c mod ladder ranked by ₹ per tenth, which applies directly to the Duke 250 and Svartpilen 250.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-to-tune-for-aamby-valley-in-november" className="text-brand-accent hover:text-brand-orange transition-colors">
                How to tune for Aamby Valley in November
              </Link>:{' '}
              the venue conditions used for every simulation in this post.
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
            <div className="font-display font-bold text-white mb-1">Compare the Svartpilen 250 and Duke 250 yourself</div>
            <div className="text-white/60 text-sm">
              Pick either bike in the free simulator, set your venue and rider weight, swap sprockets and tires, and watch the ET gap close live.
            </div>
          </div>
          <Link
            href="/simulator?bike=husqvarna-svartpilen-250"
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
