import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'indian-drag-strip-elevation-comparison';
const TITLE = 'Indian Drag Strips Ranked by Elevation: What Altitude Costs Over a Quarter Mile';
const DESCRIPTION =
  'Five Indian drag strips on November weather: a stock Hayabusa loses 0.09 s between BIC and Aamby Valley, an R15 V4 loses 0.36 s. MotoQuant shows why small bikes pay more.';

export const metadata = {
  title: 'Indian Drag Strips Ranked by Elevation — MotoQuant',
  description: DESCRIPTION,
  keywords: [
    'indian drag strips ranked',
    'mmrt vs aamby valley elevation',
    'density altitude indian drag racing',
    'aamby valley vs mmrt quarter mile',
    'bic buddh drag strip altitude',
    'kari motor speedway elevation',
    'hyderabad street drags altitude',
    'indian motorcycle venue comparison',
    'best drag strip in india for litre bike',
    'best drag strip in india for small cc',
    'density altitude indian motorcycle',
    'venue effect on quarter mile india',
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
    text: 'Aamby Valley sits 679 metres above sea level; MMRT at Sriperumbudur sits at 78 m and Buddh International Circuit at 208 m. Run the same stock Hayabusa Gen 1 down all five Indian strips on November weather and the simulator gives 10.126 s at BIC and 10.218 s at Aamby, a 0.09 s swing from the venue alone. A Yamaha R15 V4 loses four times as much: 18.185 s at BIC against 18.549 s at Aamby. The venue order is the same for both bikes. The size of the penalty is not.',
  },
  {
    type: 'p',
    text: 'Updated 10 November 2026: every simulated time in this post was re-run on the current engine. An earlier version said Aamby was a concrete strip and that a Hayabusa traps faster there than at MMRT; neither is true of the current catalog or engine.',
  },
  {
    type: 'h2',
    text: 'Five Strips, Five Elevations, One Country',
  },
  {
    type: 'p',
    text: 'India has five quarter-mile venues in the MotoQuant catalog, all asphalt. They differ mainly in altitude and weather, and those two decide how much power an engine makes there. Density altitude (DA) is the altitude at which standard-atmosphere air would have the local density; it folds elevation, temperature, pressure and humidity into one number. MotoQuant carries November weather normals for each venue, so picking a venue also picks the conditions.',
  },
  {
    type: 'table',
    rows: [
      ['Venue', 'Elevation', 'Nov normal', 'Nov DA', 'Power vs reference day', 'City'],
      ['Buddh International Circuit (BIC)', '208 m', '21 °C, 45 % RH', '~490 m', '95.0 %', 'Greater Noida, UP'],
      ['MMRT (Madras Motor Race Track)', '78 m', '26 °C, 80 % RH', '~600 m', '93.8 %', 'Sriperumbudur, TN'],
      ['Kari Motor Speedway', '300 m', '25 °C, 55 % RH', '~790 m', '92.5 %', 'Chettipalayam, TN'],
      ['Hyderabad Street Drags', '542 m', '23 °C, 55 % RH', '~990 m', '90.5 %', 'Hyderabad, TG'],
      ['Aamby Valley Airstrip (TVR)', '679 m', '22 °C, 40 % RH', '~1,120 m', '89.5 %', 'Aamby Valley, MH'],
    ],
  },
  {
    type: 'p',
    text: 'The DA and power columns are computed the way the simulator computes them: SAE J1349 correction against the reference day of sea level, 25 °C and 50 % humidity. MMRT is the lowest strip but not the densest air in November, because 26 °C and 80 % humidity cost it more than 130 m of elevation costs BIC. Water vapour displaces oxygen, and the correction works on dry-air pressure.',
  },
  {
    type: 'h2',
    text: 'Power Against Drag',
  },
  {
    type: 'p',
    text: 'Thinner air does two things. The engine makes less power, because each intake stroke carries less oxygen. Aerodynamic drag also falls, because drag force is proportional to air density. Which effect wins depends on how much of the run a bike spends drag-limited. On the current engine, for the two stock bikes in this post, the power loss wins at every venue: both bikes are slower in ET and in trap speed as density altitude rises.',
  },
  {
    type: 'h2',
    text: 'The Hayabusa Sweep: One Bike, Five Venues',
  },
  {
    type: 'p',
    text: 'The Hayabusa Gen 1 is one of three reference bikes that every MotoQuant build holds to four decimal places: 10.1100 s at the reference conditions (sea level, 25 °C, 50 % humidity). The table changes only the venue and its November weather.',
  },
  {
    type: 'table',
    rows: [
      ['Venue', 'Sim ET', 'Trap', 'Δ ET vs Aamby', 'Δ Trap vs Aamby'],
      ['BIC (Nov)', '10.126 s', '231.6 km/h', '−0.092 s', '+3.5 km/h'],
      ['MMRT (Nov)', '10.145 s', '230.9 km/h', '−0.073 s', '+2.8 km/h'],
      ['Kari (Nov)', '10.166 s', '230.1 km/h', '−0.052 s', '+2.0 km/h'],
      ['Hyderabad (Nov)', '10.201 s', '228.7 km/h', '−0.017 s', '+0.6 km/h'],
      ['Aamby Valley (Nov)', '10.218 s', '228.1 km/h', 'baseline', 'baseline'],
    ],
  },
  {
    type: 'p',
    text: 'Between BIC and Aamby the Hayabusa gives up 5.8 % of its power and 0.9 % of its ET. Part of the reason is that a litre bike spends its launch traction-limited, where the missing power would only have spun the tyre.',
  },
  {
    type: 'h2',
    text: 'Small Bikes Pay More',
  },
  {
    type: 'p',
    text: 'Now the same sweep with the catalog Yamaha R15 V4. It is power-limited from launch to the finish, so every percent of power the air takes away comes straight out of the ET.',
  },
  {
    type: 'table',
    rows: [
      ['Venue', 'R15 V4 Sim ET', 'Trap', 'Δ ET vs BIC'],
      ['BIC (Nov)', '18.185 s', '115.4 km/h', 'baseline'],
      ['MMRT (Nov)', '18.262 s', '115.1 km/h', '+0.077 s'],
      ['Kari (Nov)', '18.347 s', '114.7 km/h', '+0.162 s'],
      ['Hyderabad (Nov)', '18.484 s', '114.0 km/h', '+0.299 s'],
      ['Aamby Valley (Nov)', '18.549 s', '113.7 km/h', '+0.364 s'],
    ],
  },
  {
    type: 'p',
    text: 'The R15 V4 loses 0.36 s between BIC and Aamby, 2.0 % of its ET, for the same 5.8 % power loss that cost the Hayabusa 0.9 %. For a small-bike owner the choice is simple: the strip with the densest air on the day runs quickest, and in November that is BIC, with MMRT close behind.',
  },
  {
    type: 'callout',
    text: 'In November the venue order is the same for both bikes: BIC, MMRT, Kari, Hyderabad, Aamby. What bike class changes is the size of the gap, from 0.09 s on a Hayabusa to 0.36 s on an R15 V4.',
  },
  {
    type: 'h2',
    text: 'What Wind Adds',
  },
  {
    type: 'p',
    text: 'The catalog stores November wind normals for every venue (Aamby averages 1.2 m/s, MMRT 2.0 m/s, BIC 1.2 m/s) and each strip\'s heading: MMRT and Kari run north to south, BIC east to west, Aamby north-west to south-east. The tables above assume calm air, the simulator default. A steady 10 km/h headwind at Aamby costs the Hayabusa 0.04 s and the R15 V4 0.21 s, because the slower bike spends longer in it with less power to spare. Real runs should be compared with the wind recorded on the day.',
  },
  {
    type: 'h2',
    text: 'How Far to Trust the Numbers',
  },
  {
    type: 'p',
    text: 'The three reference bikes (GSX-R 1000 K5 10.0436 s, YZF-R1 4C8 10.1092 s, Hayabusa Gen 1 10.1100 s, all at the sea-level reference conditions) are pinned: CI fails if any of them moves by a ten-thousandth of a second. The venue tables change only the environment, so the deltas between venues come from the environmental sub-model, not from fitted offsets.',
  },
  {
    type: 'p',
    text: 'Absolute times carry the error of each bike\'s class. In the 10 November 2026 accuracy sweep, litre sport bikes of 195 hp and up show a weighted mean absolute error of 0.171 s over 29 published tests, with a bias of −0.011 s. The 150–200 cc entry class shows 0.651 s over 13 tests, with a bias of −0.106 s, so for an R15 the venue delta is more useful than the absolute ET. If you have a Dragy run from an Indian strip, submit it through the "Submit a timeslip" form; reviewed runs join the benchmark set and tighten these figures for everyone.',
  },
  {
    type: 'h2',
    text: 'Run It Yourself',
  },
  {
    type: 'p',
    text: 'Pick any bike from the 534-bike catalog in the simulator, pick a venue, and run it. The simulator applies the venue\'s altitude, surface and weather, plus wind if you set it, and runs the same physics as the reference bikes. Change only the venue and you see its effect directly.',
  },
  {
    type: 'p',
    text: 'The practical rule: below about 60 hp, the strip with the densest air on the day is worth tenths, so BIC or MMRT in November. On a stock litre bike the venue is worth under a tenth, and rider and launch matter more.',
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
          dateModified: '2026-11-10',
        })}
      />
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {['Venues', 'India', 'Altitude', 'Density altitude', 'MMRT', 'Aamby Valley', 'physics'].map((t) => (
              <span
                key={t}
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Indian Drag Strips Ranked by Elevation: What Altitude Costs Over a Quarter Mile
          </h1>
          <div className="text-sm text-white/60 mb-12">
            25 May 2026 · 12 min read · MotoQuant Blog
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
                href="/blog/how-to-tune-for-aamby-valley-in-november"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to Tune for Aamby Valley in November
              </Link>{' '}
              — venue-specific deep dive on the highest of the five Indian strips.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/how-to-tune-for-mmrt-chennai"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to Tune for MMRT Chennai
              </Link>{' '}
              — the sea-level counterpart at the other end of the venue table.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/hayabusa-quarter-mile-physics-what-limits-9-6-seconds"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Hayabusa Quarter-Mile Physics: What Limits 9.6 Seconds
              </Link>{' '}
              — the bike used as the anchor in this post, with a breakdown of what limits a stock litre-plus bike.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/why-your-r15-wont-hit-14s"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Why Your R15 Won&apos;t Hit 14s
              </Link>{' '}
              — the small-cc side of the altitude story; why a 18 hp R15 V4 cannot make up the venue penalty with parts.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/how-the-motoquant-physics-engine-works"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How the MotoQuant Physics Engine Works
              </Link>{' '}
              — the 15-sub-model architecture, including the environmental sub-model that does the DA correction for every venue in this post.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>{' '}
              — every spec used in the venue sweep above, across 340+ bikes.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Sweep your bike across all five Indian venues</div>
            <div className="text-white/60 text-sm">
              Free simulator — pick any bike, pick MMRT or Aamby Valley or BIC, watch the ET and trap shift in real time. Find the venue your bike actually wants.
            </div>
          </div>
          <Link
            href="/simulator?bike=suzuki-hayabusa&venue=mmrt"
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
