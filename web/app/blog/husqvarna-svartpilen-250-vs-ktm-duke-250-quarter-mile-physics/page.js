import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';
import { REPO_URL } from '../../../lib/site';

const SLUG = 'husqvarna-svartpilen-250-vs-ktm-duke-250-quarter-mile-physics';
const TITLE = 'Husqvarna Svartpilen 250 vs KTM Duke 250: Quarter-Mile Physics';
const DESCRIPTION =
  'MotoQuant sims the Husqvarna Svartpilen 250 at 14.77s / 149 km/h and KTM Duke 250 at 15.08s / 143 km/h. Same engine, same Bajaj Chakan plant — why the Husky is 0.31s quicker at the strip.';

export const metadata = {
  title: 'Husqvarna Svartpilen 250 vs KTM Duke 250 Quarter Mile — MotoQuant',
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
    text: 'MotoQuant runs the Husqvarna Svartpilen 250 at 14.767 seconds and 149.2 km/h trap. The KTM Duke 250 — same 248cc LC4c single, same Bajaj Chakan assembly line, same Pierer Mobility India parts shelf — runs 15.083 seconds and 143.3 km/h. That is a 0.316-second ET gap and a 5.9 km/h trap gap between two bikes that share an engine. Almost every Indian buyer assumes the Duke is the quicker bike because it carries the KTM badge. The simulator says otherwise, and the reasons are sitting in the gear charts.',
  },
  {
    type: 'h2',
    text: 'Same Engine, Same Plant, Same Pierer Mobility Parts Bin',
  },
  {
    type: 'p',
    text: 'Both bikes use the LC4c-250 platform — a 248.76 cc liquid-cooled DOHC 4-valve single with a 72.0 mm bore and 61.1 mm stroke, 12.5:1 compression, Bosch EMS fuel injection. They are built side by side at Bajaj Auto’s Chakan plant under the KTM-Husqvarna Pierer Mobility India platform deal. Same crankcases, same head castings, same six-speed cassette gearbox, same PASC slipper clutch, same Bybre 4-piston front caliper. The factory-spec power numbers are functionally identical at 30 hp at the crank, with the Duke 250 stated at 30 hp at 8,000 rpm and the Svartpilen at 30 hp at 9,000 rpm — both produce roughly 25 Nm of peak torque around 7,250 rpm. KTM’s slightly punchier 31 hp 250 Duke variant exists in some markets but the Indian-market 30 hp spec is what the simulator is comparing.',
  },
  {
    type: 'p',
    text: 'Where the two bikes diverge is final drive and aerodynamics. The Duke 250 runs F16 / R47 sprockets — the taller setup KTM picked because Duke owners ride at city speeds 80 percent of the time and a tall final drive cuts engine RPM at 80 km/h cruise. The Svartpilen runs F14 / R46. Per Husqvarna India’s 2024 parts catalogue, that is a deliberately shorter final drive chosen to match the bike’s mid-range-torque character — Husqvarna’s positioning is that the Svartpilen punches harder out of corners and accelerates harder in the lower gears. On a drag strip, that exact choice pays off.',
  },
  {
    type: 'h2',
    text: 'The Simulator Numbers',
  },
  {
    type: 'p',
    text: 'Running both bikes in MotoQuant under matched Aamby Valley November conditions (density altitude around 1,100 m, 22°C ambient, dry concrete with OEM tire choices, 78 kg rider) produces the head-to-head below. These are stock-tune outputs from the production sweep — no power boost, no mass cut, no parts catalogue mods applied.',
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
    text: 'Sim-only numbers. There is no instrumented Indian magazine quarter-mile test on the Svartpilen 250 yet, and Autocar India’s Duke 250 GPS-timed 0-100 km/h sits at 5.6 s (the magazines do not time to the quarter). The entry-200-300 cc cluster carries a documented +0.5 to +1.4 s slow bias, so real-world ETs are plausibly 0.5-1.0 s quicker than the sim figures, with the gap between the two bikes holding stable.',
  },
  {
    type: 'h2',
    text: 'Where the 0.316-Second Gap Actually Lives',
  },
  {
    type: 'p',
    text: 'Three physics levers do almost all the work. Sprocketing is the loudest of them, drag is the next, mass is the smallest.',
  },
  {
    type: 'p',
    text: '1. Final drive. The Husqvarna’s F14 / R46 combination gives a final-drive ratio of 3.286 against the Duke’s F16 / R47 ratio of 2.938 — about 12 percent shorter on the Husky. With the same six gearbox ratios, the same primary, and the same tire rolling radius, a shorter final drive means the bike covers less ground per engine revolution. That trades top-end gearing for mid-gear acceleration. On a 250 cc bike that arrives at the 402-metre trap line in fourth gear, twelve percent of extra mechanical leverage in every gear except top means the Svartpilen is pulling roughly 270 rpm higher than the Duke at the trap. On a 30 hp single where the power curve is steep above 7,500 rpm, those 270 rpm are worth a meaningful chunk of trap speed.',
  },
  {
    type: 'p',
    text: '2. Aerodynamics. Husqvarna sells the Svartpilen as a flat-tracker — round LED headlight, narrow tank shrouds, no bikini fairing, flat handlebars set forward. The Duke 250 has the high upright handlebars, the larger flat-bar tank flares, and the bulkier headlight cluster that defines the Duke design language. The simulator carries Cd 0.66 × 0.42 m² for the Svartpilen against Cd 0.82 × 0.46 m² for the Duke — a roughly 27 percent reduction in total drag area on the Husky. At 130 km/h that is about 1.7 hp less drag, which on a 30 hp single is more than 5 percent of available power redirected from pushing air to accelerating mass. The Svartpilen’s drag advantage shows up most clearly in the trap-speed gap — 5.9 km/h is exactly what 27 percent less drag buys you at 250 cc.',
  },
  {
    type: 'p',
    text: '3. Mass. The Duke 250 ships at 148 kg dry by KTM India’s spec sheet. The Svartpilen 250 ships at 144 kg dry — 154 kg kerb minus the roughly 10 kg of fuel in the 9.5-litre tank. The 4 kg gap shows up at launch (slightly better 60-foot performance, though the simulator says the two bikes are essentially tied at 60 feet because traction is the binding constraint for both) and accumulates marginal advantage through the run. With a 78 kg rider, the Husky carries 222 kg of total mass against the Duke’s 226 kg — a 1.8 percent advantage. By itself that is worth maybe 0.05 seconds of ET. It is a real but small contribution to the gap.',
  },
  {
    type: 'h2',
    text: 'Why the Result Surprises Everyone',
  },
  {
    type: 'p',
    text: 'Indian buyers default to the assumption that KTM-badged bikes are quicker than Husqvarna-badged bikes. Inside Pierer Mobility’s positioning that is roughly true: the Duke line is sport-naked, the Husqvarna line is street-tracker. So the Duke is supposed to be the strip bike. But sport-naked positioning translates to design choices — taller bars for aggressive corner attack, taller final drive for road riding, fairing-free body lines that nobody designed with Cd in mind — that work against quarter-mile times. The Svartpilen’s flat-tracker styling happens to incorporate three physics decisions that quietly add up to a quicker bike at the strip: shorter final drive, lower frontal area, slightly less mass.',
  },
  {
    type: 'p',
    text: 'This is also a reminder of how thin engine-spec parity actually is on platform-shared bikes. The LC4c-250 makes 30 hp in both bikes. Yet the bike that wins the quarter mile is the one whose chassis and final drive were configured for the slower, lower-RPM riding style. The lesson generalises across the segment — the Yamaha MT-15 V1 deep-dive and the Pulsar NS200 vs Apache RTR 200 4V post both show the same pattern, where two bikes with similar engine specs diverge by half a second at the trap because of gear ratios, rider position, and frontal area.',
  },
  {
    type: 'h2',
    text: 'Mods, Cost-per-Tenth, and Which Bike to Modify',
  },
  {
    type: 'p',
    text: 'The Indian aftermarket for the LC4c-250 platform is large and well-priced because both bikes share parts. Powertronic, KustomHub, Big Bird, JT, IRC, Daido all stock parts that fit either platform with minor bracket changes. Cost-per-tenth ranks pulled from the MotoQuant parts catalogue, sorted cheapest first:',
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
    text: 'For Duke 250 owners chasing the Svartpilen’s number, the cheapest path is the F15 front sprocket swap. Dropping from F16 to F15 brings the Duke’s final drive from 2.94 to 3.13 — still taller than the Svartpilen’s 3.29 but close enough that combined with a sport tire it closes most of the gap. Total cost: about ₹6,650 for sprocket plus rear tire. ET gain: roughly 0.4 to 0.45 seconds in the simulator. That puts a modded Duke ahead of a stock Svartpilen and within striking distance of a modded Svartpilen running the same parts.',
  },
  {
    type: 'p',
    text: 'For Svartpilen owners, the sport tire alone is the headline mod. The OEM Apollo Alpha H1 in 150/60-17 is a competent street tire but it is not a Pirelli Diablo. Swap rubber for a Diablo Rosso II or a Michelin Road 5 and the simulator returns about 0.3 seconds of ET on top of the stock 14.77 — putting the bike into the 14.4-second zone. Beyond that the cost-per-tenth ramps up steeply. An ECU flash adds another 0.25 seconds for ₹14,000, which is a marginal call. A slip-on exhaust at ₹38,000+ for 0.15 seconds is, on a sub-25 hp bike, brutal value.',
  },
  {
    type: 'callout',
    text: 'Fastest cheap path on the LC4c-250 platform: the Svartpilen + Diablo Rosso II rear tire combo (about ₹4.0 lakh on-road + ₹6,200) lands you at roughly 14.45 s without any other changes. The Duke 250 needs a sprocket swap plus the same tire to match, at roughly ₹4.1 lakh on-road + ₹6,650. The Husky wins the stock fight and stays competitive after mods because its chassis was already configured the way a drag tuner would have configured it.',
  },
  {
    type: 'h2',
    text: 'How the LC4c-250 Class Stacks Up',
  },
  {
    type: 'p',
    text: 'Four sub-300cc nakeds, four physics profiles. Sim numbers below are MotoQuant stock-tune outputs under matched Aamby Valley November conditions with a 78 kg rider.',
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
    text: 'The Svartpilen lands between the more powerful Apache RTR 310 (35.6 hp single, but heavier at 169 kg) and the lighter but lower-powered Pulsar N250. The Duke 250 is comfortably ahead of the Pulsar — its taller gearing and identical power output put it 0.3 seconds clear — but visibly behind the better-configured Husky and the more-powerful Apache. For a buyer choosing strictly on drag-strip ET in the sub-300cc segment, the Apache RTR 310 wins outright. For a buyer who wants the LC4c-250 powertrain (smoother, more refined, more durable than the TVS 312 cc single in long-distance use) the Svartpilen is the choice on the strip, the Duke is the choice on city roads.',
  },
  {
    type: 'h2',
    text: 'Notes on the Engine-Curve Asymmetry',
  },
  {
    type: 'p',
    text: 'There is one detail in the catalogue worth flagging. The Duke 250 spec in the MotoQuant catalogue lists peak power at 8,000 rpm; the Svartpilen lists it at 9,000 rpm. In real life the two engines have nearly identical power curves because they are the same engine — both peak somewhere in the 8,500-9,000 rpm window depending on which dyno-test you trust. The catalogue values come from each manufacturer’s India press kit; KTM India publishes 8,000 rpm for the 30 hp number while Husqvarna India publishes 9,000 rpm. The actual peak in either bike is almost certainly the same. The simulator uses each manufacturer’s stated curve, so the Duke gets a slightly broader and lower-revving torque band in the model while the Svartpilen gets a peakier, higher-revving one. This asymmetry contributes a small amount to the trap-speed gap but is not the primary driver — the final-drive and frontal-area gaps account for most of it. If the Duke’s peak-power RPM were updated to 9,000 to match the Svartpilen, the simulator’s ET gap would tighten from 0.316 s to roughly 0.27 s. The qualitative ordering would not change.',
  },
  {
    type: 'h2',
    text: 'Run Your Own Numbers',
  },
  {
    type: 'p',
    text: 'If you are deciding between a Duke 250 and a Svartpilen 250 — and the salesperson at your local dealer cannot tell you which is quicker because their training is on engines and ergonomics, not aerodynamics — the simulator at motoquant.in lets you set rider weight, ambient temperature, density altitude, tire choice, and final-drive ratio and watch the ETs move in real time. The default load-out for both bikes ships with the Indian-market 30 hp tune and OEM sprocketing. Swap the Duke to F15 and the gap collapses by roughly 0.15 seconds. Swap both to Pirelli Diablo Rosso IIs and the gap stays close to the stock figure because the same tire upgrade scales both bikes by roughly the same factor.',
  },
  {
    type: 'p',
    text: 'The broader takeaway is that platform-shared bikes diverge at the strip in ways the spec sheet does not advertise. Same engine, same plant, same parts shelf — and yet 0.316 seconds of ET separates them, almost all of it coming from final drive and frontal area. That is the kind of difference the simulator surfaces cleanly because every gear ratio, every Cd value, and every sprocket pair lives in the catalogue and the physics walks the consequences forward step by step.',
  },
  {
    type: 'p',
    text: 'Two final caveats. First, every number in this post is a stock-tune simulation under specific conditions; change the rider weight or the surface or the launch technique and the absolute ETs shift, but the relative ordering of which bike is quicker stays stable. Second, the entry-200-300 cc cluster carries a +0.5 to +1.4 s slow bias against real-world instrumented data; expect a competent rider on a warmed bike with good launches to run quicker than the sim figures, with the gap between the two bikes holding roughly constant. Both biases will tighten as more Indian small-cc Dragy and VBOX uploads flow into the calibrator.',
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
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Husqvarna Svartpilen 250 vs KTM Duke 250: Quarter-Mile Physics
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
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
                KTM Duke 390 vs RC 390 Quarter-Mile Physics
              </Link>{' '}
              — bigger sibling of the Duke 250, same Pierer Mobility platform discipline, same chassis-vs-fairing tradeoff at the strip.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                Pulsar NS200 vs Apache RTR 200 4V Quarter-Mile Physics
              </Link>{' '}
              — same Indian sub-300cc segment, different platform politics, similar physics levers.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/best-mods-for-ktm-rc-390-budget-vs-cost-per-tenth" className="text-brand-accent hover:text-brand-orange transition-colors">
                Best Mods for KTM RC 390 by Cost-per-Tenth
              </Link>{' '}
              — the LC4c-platform mod ladder ranked by ₹ per tenth, applies one-to-one to Duke 250 and Svartpilen 250 owners.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-to-tune-for-aamby-valley-in-november" className="text-brand-accent hover:text-brand-orange transition-colors">
                How to Tune for Aamby Valley in November
              </Link>{' '}
              — the venue conditions used for every simulation in this post.
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
            <div className="font-display font-bold text-white mb-1">Compare the Svartpilen 250 and Duke 250 yourself</div>
            <div className="text-white/60 text-sm">
              Free simulator — pick either bike, dial in your venue and rider weight, swap sprockets and tires, and watch the ET delta close in real time.
            </div>
          </div>
          <Link
            href="/simulator?bike=husqvarna-svartpilen-250"
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
