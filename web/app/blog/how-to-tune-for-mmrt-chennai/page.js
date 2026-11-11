import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema, OG_IMAGE } from '../../StructuredData';

const SLUG = 'how-to-tune-for-mmrt-chennai';
const TITLE = 'How to tune for MMRT Chennai: sea-level, humid, hot track';
const DESCRIPTION =
  'MMRT Chennai sits at 78 m with 80% humidity in November: denser air than Aamby Valley, but hotter, wetter intake air. The venue-specific tuning math.';

export const metadata = {
  title: 'How to tune for MMRT Chennai',
  description: DESCRIPTION,
  keywords: [
    'mmrt chennai drag racing motorcycle',
    'madras motor race track quarter mile',
    'how to tune for mmrt chennai',
    'mmrt drag strip events',
    'chennai motorcycle drag racing',
    'tamil nadu drag racing',
    'mmrt vs aamby valley',
    'mmrt density altitude',
    'mmrt sriperumbudur drag',
    'mmrt timing system',
    'kari motor speedway drag racing',
    'coimbatore drag racing motorcycle',
    'indian drag strip weather',
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `https://motoquant.in/blog/${SLUG}`,
    type: 'article',
    publishedTime: '2026-05-18T00:00:00Z',
    modifiedTime: '2026-11-10T00:00:00Z',
    images: [OG_IMAGE],
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: 'Aamby Valley sits at 679 m above sea level and Madras Motor Race Track at 78 m, and most of the difference between the two venues follows from that. MotoQuant simulates a stock Hayabusa Gen1 at 10.218 seconds at Aamby Valley in November and 10.145 seconds at MMRT in the same month, with a trap speed 2.8 km/h higher at MMRT and the same 60-foot. The denser air helps. The humidity takes back some engine power, the rubber runs hotter, and the prevailing wind blows at an angle to the strip. This is what changes when you trailer a bike from Pune to Sriperumbudur, and how to set it up. (Updated 10 November 2026: every simulated time here was re-run on the current engine.)',
  },
  {
    type: 'h2',
    text: 'Where MMRT is',
  },
  {
    type: 'p',
    text: 'Madras Motor Race Track is in Sriperumbudur, 40 km west of Chennai city centre, on the highway toward Kanchipuram. The site was developed in the early 1990s and the permanent 3.7 km road circuit opened in 2002. The front straight, the same surface the Indian National Road Racing Championship races on, has hosted FMSCI-sanctioned quarter-mile drag events well before and after that. It is roughly 600 m long with a usable braking area, comfortably long enough for a 402 m quarter mile from a standing start. The surface is conventional bitumen, slightly polished by years of road-racing rubber, and the timing system is a fixed FMSCI-grade beam setup operated by the track. Coordinates: 12.93° N, 79.98° E; altitude per MotoQuant venue data: 78 m. The track sits in a flat farming belt with scrub and palmyra trees on three sides and the Chennai-Bengaluru NH48 corridor on the fourth, which matters for crosswind shelter, as the wind section below explains.',
  },
  {
    type: 'h2',
    text: 'The weather contrast: MMRT vs Aamby Valley',
  },
  {
    type: 'p',
    text: 'MotoQuant\'s venue database holds twelve months of seasonal weather for every Indian drag strip. In the same calendar month, the two most-searched venues, MMRT and Aamby Valley, look almost nothing alike. These are the November numbers (the Valley Run Winter season, and the most common time to ship a bike to either venue):',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'MMRT (Nov)', 'Aamby Valley (Nov)', 'Effect on ET'],
      ['Altitude', '78 m', '679 m', 'MMRT denser baseline'],
      ['Ambient temperature', '26°C', '22°C', 'MMRT hotter intake'],
      ['Track temperature', '30°C', '26°C', 'MMRT softer rubber'],
      ['Relative humidity', '80%', '40%', 'MMRT lower effective O₂'],
      ['Barometric pressure', '1012 hPa', '1014 hPa', 'roughly even'],
      ['Density altitude', '~600 m', '~1,120 m', 'MMRT ~520 m lower'],
      ['Wind speed', '2.0 m/s', '1.2 m/s', 'MMRT slightly windier'],
      ['Prevailing wind', '045° NE', '045° NE', 'shared'],
      ['Rain probability', '~25% (NE monsoon)', '<5%', 'MMRT weather risk'],
    ],
  },
  {
    type: 'p',
    text: 'Density altitude is the number that matters most for engine power. In November MMRT sits about 520 m lower in DA than Aamby Valley: more oxygen per intake stroke, more power. The simulator applies the SAE J1349 power correction against its sea-level reference day. The factor is 0.938 at MMRT against 0.895 at Aamby Valley in November, so a Hayabusa makes about 4.8 percent more power at MMRT. That number already includes the humidity.',
  },
  {
    type: 'p',
    text: 'Humidity pushes back. The correction works on dry-air pressure, and 80 percent humidity at 26°C puts enough water vapour in the intake to cost MMRT about a percent of power. That is why MMRT, the lowest strip in the catalog, still has less dense air than BIC in November. Even so, the net engine effect against Aamby Valley is close to five percent in MMRT\'s favour.',
  },
  {
    type: 'h2',
    text: 'The track surface and the 60-foot',
  },
  {
    type: 'p',
    text: 'The other lever is traction off the line. The track temperature in November runs 30°C against Aamby Valley\'s 26°C; in April and May, MMRT\'s normals reach 42 to 48°C. Tyre friction falls once the rubber runs past its operating window, and the simulator models that through each tyre\'s thermal window and peak friction coefficient. In November the difference does not show: the simulated 60-foot for a stock Hayabusa is 1.821 s at both venues.',
  },
  {
    type: 'p',
    text: 'The MMRT surface is road-racing asphalt, not a purpose-built drag strip with prep compound, so its friction never reaches what a VHT-prepped strip delivers. The catalog stores both MMRT and Aamby Valley as unprepped asphalt with the same surface multiplier, so in the simulator the difference between them comes from the air, not the surface.',
  },
  {
    type: 'callout',
    text: 'Sanity check: the simulator runs a stock Hayabusa Gen1 at 10.145 seconds at MMRT in November against 10.218 seconds at Aamby Valley, with a trap 2.8 km/h higher at MMRT and the same 60-foot. In the 10 November 2026 accuracy sweep, the litre sport 195 hp-and-up class shows a weighted mean absolute error of 0.171 s against published tests, so treat the venue gap as more reliable than either absolute time. Run it for your own bike in the simulator.',
  },
  {
    type: 'h2',
    text: 'Tuning changes that help',
  },
  {
    type: 'p',
    text: 'Four tuning changes are worth making when you trailer from a cool, high-altitude venue to MMRT. None of them is a gear-ratio change. Run the cassette you ran at Aamby Valley: gearing is set for a target trap speed, and on the same bike the trap speeds at the two venues are within about 3 km/h.',
  },
  {
    type: 'table',
    rows: [
      ['Adjustment', 'Aamby setting', 'MMRT setting', 'Reason'],
      ['Launch RPM', 'Peak torque + 500', 'Peak torque + 200', 'Hotter tire, less margin'],
      ['Rear tire pressure', '~30 psi cold', '~28 psi cold', 'Hotter track, larger contact patch'],
      ['Front tire pressure', '~34 psi cold', '~33 psi cold', 'Marginal, follows rear'],
      ['Clutch slip ramp', 'Aggressive', 'Slightly softer', 'Heat-soak protection'],
      ['Fuel grade', 'Indian 95 RON', 'Indian 95 RON', 'No change'],
      ['Air filter', 'OEM or DNA stage 1', 'Same', 'Denser air does not change this'],
    ],
  },
  {
    type: 'p',
    text: 'Launch RPM matters most. At Aamby Valley, on a cool track with a fresh tire, a Hayabusa-class bike can launch at peak torque plus 500 rpm (roughly 7,500 rpm on a Gen1) and the rear tire will take the slip. On MMRT\'s 30 to 48°C track surface, the same launch RPM gives a smoky, wasteful first quarter-second. Drop to peak torque plus 200 rpm (roughly 7,200 rpm) and the bike hooks up cleaner, with about 0.03 seconds back in the 60-foot. It is the cheapest tenth at MMRT, and most stock-tune riders ignore it.',
  },
  {
    type: 'p',
    text: 'The tire pressure change is small but real. A hotter track surface heats the whole rear tire much faster, and dropping 2 psi from baseline gives about 8 to 10 percent more contact patch area, at the cost of a little high-speed stability that nobody needs in a quarter mile. The usual rule of thumb: drop 2 psi rear and 1 psi front from your Aamby Valley setting. Do not go lower unless you are running a drag-prep slick, which needs different math.',
  },
  {
    type: 'p',
    text: 'The clutch slip ramp matters because MMRT punishes a stiff engagement. A drag clutch set up for a cool Aamby Valley track can safely engage hard within roughly 0.20 seconds of release. At MMRT the same setting overloads the rear and spins it off the line, and that wheelspin takes another 0.10 seconds to clean up. A softer ramp and a longer slip window give a cleaner hookup. Clutch tuning differs from bike to bike, but the principle is the same for all of them: a hotter, less grippy track wants a softer release.',
  },
  {
    type: 'h2',
    text: 'When to race: MMRT month by month',
  },
  {
    type: 'p',
    text: 'MMRT\'s climate changes through the year, and the simulator\'s twelve-month weather table shows what that costs. Quarter-mile ET on a stock Hayabusa Gen1 moves by about 0.05 seconds across the calendar at MMRT, mostly with air temperature:',
  },
  {
    type: 'table',
    rows: [
      ['Month', 'Ambient', 'Track temp', 'RH', 'Hayabusa sim ET'],
      ['January', '25°C', '30°C', '65%', '10.130 s'],
      ['February', '26°C', '32°C', '60%', '10.132 s'],
      ['March', '28°C', '36°C', '60%', '10.143 s'],
      ['April', '31°C', '42°C', '65%', '10.165 s'],
      ['May', '34°C', '48°C', '55%', '10.176 s'],
      ['October', '28°C', '34°C', '75%', '10.155 s'],
      ['November', '26°C', '30°C', '80%', '10.145 s'],
      ['December', '25°C', '28°C', '75%', '10.135 s'],
    ],
  },
  {
    type: 'p',
    text: 'January and December are the quickest months at MMRT in the simulator, and May the slowest, 0.05 s behind January on a stock Hayabusa. The engine model sees only the air; a real rear tyre on a 48°C May track may lose more than that. October brings the northeast monsoon, and the rain risk matters more than the air. The practical window is November through February.',
  },
  {
    type: 'h2',
    text: 'The wind and the crosswind',
  },
  {
    type: 'p',
    text: 'MMRT\'s November wind normal is about 2 m/s from 045 degrees (northeast), light but steady. The strip runs roughly north-south, so that wind sits about 45 degrees off the bike\'s axis: roughly 1.4 m/s along the strip and 1.4 m/s across it. The venue runs above assume calm air; set the wind in the simulator to see its effect. The crosswind matters more for stability than for ET. On a fully faired litre-class bike at a 240+ km/h trap, a 1.4 m/s crosswind puts a sideways force of roughly 35 N on the fairing. A normal rider handles that easily, but it is uncomfortable on a heavily modified bike with less weight on the front end. Aamby Valley\'s prevailing wind also comes from 045°, so the wind behaves the same way there, at a similar strength.',
  },
  {
    type: 'h2',
    text: 'Kari Motor Speedway',
  },
  {
    type: 'p',
    text: 'Kari Motor Speedway in Coimbatore was a drag racing venue before either MMRT or Aamby Valley. The site hosted FMSCI-sanctioned drag events in the late 1990s, before B. Vijay Kumar built the permanent F3 circuit on the same land in 2002. The track now runs the Royal Enfield Continental GT Cup, the Indian National Road Racing Championship Group A, and various TVS and Honda one-make championships. It is not currently used for drag racing. If you searched for "Kari Motor Speedway drag racing" because of that history: the drag heritage is real, but the active drag venues today are MMRT, Aamby Valley, Buddh and a handful of airstrip events in the north. Coimbatore tuners still go to MMRT, a 5 hour drive east, for instrumented quarter-mile work.',
  },
  {
    type: 'h2',
    text: 'Run your own numbers',
  },
  {
    type: 'p',
    text: 'MMRT has denser air than Aamby Valley and a hotter track. On the current engine the air wins for every bike we ran in November: a stock Hayabusa is 0.07 s quicker at MMRT, and a Continental GT 650, RC 390, Duke 390, Pulsar NS400Z and Pulsar NS200 are 0.17 s to 0.28 s quicker. Pick the venue and the simulator applies all of this from its weather table. The four tuning changes above (lower launch RPM, lower tyre pressures, softer clutch ramp, the same cassette) are about the track temperature, which the simulator models less fully than the air.',
  },
  {
    type: 'p',
    text: 'In the simulator at motoquant.in you can switch between MMRT and Aamby Valley with one dropdown and run the same bike at both venues side by side. Every venue setting in the database (twelve months of weather, surface type, prevailing wind) feeds the physics engine the same way, and the 534-bike catalog, the 254-tire fitment library and the 546-part ROI engine all respond to the venue you pick. If you are planning a December MMRT entry on a stock Hayabusa, a modded Duke 390 or a Pulsar NS400Z, you can build the run sheet here before you load the trailer.',
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
          dateModified: '2026-11-10',
        })}
      />
      <SiteNav />

      <article id="main" className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          <div className="flex flex-wrap gap-2 mb-6">
            {['MMRT', 'Chennai', 'venue', 'tuning', 'Tamil Nadu'].map((t) => (
              <span
                key={t}
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            How to tune for MMRT Chennai: sea-level, humid, hot track
          </h1>
          <div className="text-sm text-white/60 mb-12">
            18 May 2026 · 11 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        <div className="max-w-2xl mx-auto mt-16 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Simulate your bike at MMRT vs Aamby Valley</div>
            <div className="text-white/60 text-sm">
              Switch venues with one dropdown. Sweep month, track temperature, rider weight, tire compound and any of the 546 parts in the catalog, and see your ET difference before you pay the entry fee.
            </div>
          </div>
          <Link
            href="/simulator?venue=mmrt"
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
                href="/blog/how-to-tune-for-aamby-valley-in-november"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to tune for Aamby Valley in November
              </Link>
              : the high-altitude venue this post uses as its baseline.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/hayabusa-vs-zx-14r-which-is-faster"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Hayabusa vs ZX-14R: which is faster off the line?
              </Link>
              : the Hayabusa used as the reference bike for the MMRT and Aamby Valley comparisons here.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/the-physics-of-a-perfect-launch"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                The physics of a perfect launch
              </Link>
              : the physics behind the launch-RPM and clutch-ramp changes above.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/ktm-duke-390-vs-rc-390-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                KTM Duke 390 vs RC 390: quarter-mile physics at Aamby Valley
              </Link>
              : the same venue comparison for a 400-class single, with a quick MMRT estimate.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/how-the-motoquant-physics-engine-works"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How the MotoQuant physics engine works
              </Link>
              : what is inside the simulator that produced these numbers, and what the cluster bias bands mean.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>
              : 534 bikes with full spec sheets, OEM tire fitments, and venue-aware quarter-mile predictions for every Indian drag strip in the database.
            </li>
          </ul>
        </div>
      </article>

      <SiteFooter />
    </div>
  );
}
