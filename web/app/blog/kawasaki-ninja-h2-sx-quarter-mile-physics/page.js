import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema, OG_IMAGE } from '../../StructuredData';
import PostBikeLinks from '../../../components/PostBikeLinks';

const SLUG = 'kawasaki-ninja-h2-sx-quarter-mile-physics';
const TITLE = 'Kawasaki Ninja H2 SX quarter-mile physics: supercharged tourer';
const DESCRIPTION =
  'MotoQuant simulates the 2018-2023 Ninja H2 SX at 10.20 s and a 232.8 km/h trap at Aamby Valley in November, level with a stock Hayabusa Gen 1. Why a 238 kg supercharged tourer runs a Hayabusa-class quarter in India, and where it loses to the ZX-14R.';

export const metadata = {
  title: 'Kawasaki Ninja H2 SX quarter-mile physics India',
  description: DESCRIPTION,
  keywords: [
    'kawasaki ninja h2 sx quarter mile',
    'kawasaki ninja h2 sx quarter mile india',
    'kawasaki ninja h2 sx vs hayabusa india',
    'h2 sx drag time',
    'ninja h2 sx vs hayabusa',
    'h2 sx vs zx-14r quarter mile',
    'ninja h2 sx india price',
    'h2 sx 0-300 km/h',
    'supercharged motorcycle quarter mile',
    'h2 sx vs h2 sx se+',
    'ninja h2 sx grey market india',
    'h2 sx top speed india',
    'kawasaki supercharger drag',
    'h2 sx cost per tenth',
    'h2 sx 10.6 quarter mile',
    'ninja h2 sx se+ drag time',
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `https://motoquant.in/blog/${SLUG}`,
    type: 'article',
    publishedTime: '2026-05-25T00:00:00Z',
    modifiedTime: '2026-11-10T00:00:00Z',
    images: [OG_IMAGE],
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: 'MotoQuant simulates the 2018-2023 Kawasaki Ninja H2 SX at 10.203 seconds with a 232.8 km/h trap under Aamby Valley November conditions. That puts a 238 kg sport-touring bike with hard luggage mounts level with the simulator’s stock Hayabusa Gen 1 (10.218 s) and a third of a second behind a stock ZX-14R. The reason is a centrifugal supercharger, fitted to a tourer that everyone assumes is heavy and soft. (Updated 10 November 2026: every simulated time here was re-run on the current engine.)',
  },
  {
    type: 'h2',
    text: 'What the Ninja H2 SX is',
  },
  {
    type: 'p',
    text: 'The H2 SX launched at EICMA 2017 as the touring sibling of the track-only Ninja H2R and the road-legal Ninja H2. Kawasaki took the same 998 cc inline-four, with its centrifugal supercharger spinning at up to 9.2 times crank speed, retuned the impeller and intake mapping for low-end driveability, and put it in a sport-touring chassis with a longer wheelbase, a windshield, hard luggage mounts, cruise control and a 19-litre tank. It makes 200 hp at 11,000 rpm and 137 Nm at 9,500 rpm, the same headline numbers as the SE and SE+ variants, but the base 2018-2023 model is 14 kg lighter wet because it does without the Öhlins electronic forks, the cornering lights, the TFT colour dash and the heated grips.',
  },
  {
    type: 'p',
    text: 'On paper the H2 SX is a sport-tourer. On the road and on the strip it is a supercharged litre bike with luggage rails, and the supercharger shapes everything about the engine. Unlike a turbo it has no exhaust lag and no wastegate: its boost rises linearly with engine speed, peaking at around 0.6 bar (8.7 psi) at the redline. From idle to 5,000 rpm the bike feels like a slightly torquey naturally aspirated 1000. Above 6,000 rpm the boost takes over, and the bike pulls like a small superbike on nitrous all the way to its 12,200 rpm limit. That is where the trap speed comes from.',
  },
  {
    type: 'h2',
    text: 'Stock-tune simulation numbers',
  },
  {
    type: 'p',
    text: 'MotoQuant results for the H2 SX under Aamby Valley November conditions (roughly 1,100 m density altitude, 22 °C ambient, dry asphalt, OEM Bridgestone Battlax Hypersport S22 front and rear at μ_peak around 1.30), with a 78 kg rider on the 238 kg dry bike:',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'Value', 'Source'],
      ['Quarter-mile ET', '10.203 s', 'MotoQuant sim (Aamby Valley Nov)'],
      ['Trap speed', '232.8 km/h', 'MotoQuant sim'],
      ['60-foot time', '1.851 s', 'MotoQuant sim'],
      ['MCN informal drag', '~10.22 s', 'MCN test, Jan 2018 (uninstrumented)'],
      ['Claimed top speed', '~270 km/h (electronically limited)', 'Kawasaki spec / MCN'],
      ['Class error (weighted MAE)', '0.171 s, bias −0.011 s', 'litre_sport_195p, 10 Nov 2026 sweep'],
    ],
  },
  {
    type: 'p',
    text: 'MotoQuant files the H2 SX in its litre_sport_195p cluster: bikes over 600 cc making at least 195 hp. In the 10 November 2026 accuracy sweep that cluster shows a weighted mean absolute error of 0.171 seconds across 29 published tests, with a bias of −0.011 s. So on this class of bike the simulator is usually within about two tenths, and it does not lean fast or slow. None of those 29 tests is a supercharged sport-tourer, so the H2 SX number is interpolation rather than validation.',
  },
  {
    type: 'callout',
    text: 'The H2 SX trap speed of 232.8 km/h is 4.7 km/h above the stock Hayabusa Gen 1, but 6.6 km/h below the Ninja H2 and 11 km/h below the ZX-14R in the same conditions.',
  },
  {
    type: 'h2',
    text: 'H2 SX vs Hayabusa vs ZX-14R: the Indian big three',
  },
  {
    type: 'p',
    text: 'The Indian gray-market drag scene has three obvious flagships in the litre-plus class: the Suzuki Hayabusa (Gen 1 reference pinned in the simulator at 10.1100 s), the Kawasaki ZX-14R, and now the Ninja H2 SX. They are built very differently. The Hayabusa is naturally aspirated, 197 hp, 220 kg dry. The ZX-14R is naturally aspirated, 197 hp, 218 kg dry. The H2 SX is supercharged, 200 hp, 238 kg dry. Here is what each of those choices costs at the strip.',
  },
  {
    type: 'table',
    rows: [
      ['Bike', 'Sim ET', 'Trap', 'Dry mass', 'Peak hp', 'Forced induction'],
      ['Kawasaki Ninja H2 SX (2018-2023)', '10.203 s', '232.8 km/h', '238 kg', '200', 'Supercharger (0.6 bar)'],
      ['Kawasaki ZX-14R (2012-2023)', '9.872 s', '243.8 km/h', '218 kg', '197', 'NA'],
      ['Suzuki Hayabusa Gen 1', '10.218 s', '228.1 km/h', '220 kg', '197', 'NA'],
      ['Suzuki Hayabusa Gen 3 (2021+)', '10.323 s', '229.4 km/h', '212 kg', '188', 'NA'],
      ['Kawasaki Ninja H2 (road)', '10.072 s', '239.4 km/h', '214 kg', '231', 'Supercharger (0.7 bar)'],
    ],
  },
  {
    type: 'p',
    text: 'The ZX-14R is the quickest bike in the table: 0.33 s ahead of the H2 SX and 11 km/h faster at the trap, with 20 kg less to carry. The two leave the line together (60-foot 1.851 s for the H2 SX, 1.856 s for the ZX-14R), so the gap opens after the launch, where the lighter, naturally aspirated 1441 cc bike keeps pulling.',
  },
  {
    type: 'p',
    text: 'Despite carrying 18 kg more, the H2 SX is level with a stock Hayabusa Gen 1 (0.015 s ahead). The supercharger fattens the torque curve from 6,000 rpm up, just where the Hayabusa’s naturally aspirated engine starts running into diminishing returns, and that pays for the touring weight.',
  },
  {
    type: 'p',
    text: 'The H2 (no SX) beats the H2 SX by 0.13 s and 6.6 km/h, with 24 kg less mass and 31 more horsepower from a hotter supercharger map. The H2 SX sits between a litre sport-tourer and a track-spec supercharged superbike.',
  },
  {
    type: 'h2',
    text: 'Where the mass is',
  },
  {
    type: 'p',
    text: 'At 238 kg dry, the H2 SX carries 24 kg more than a Ninja H2 and 18 kg more than a Hayabusa. None of the extra mass is in the engine: the supercharged 998 cc inline-four weighs almost exactly the same as the naturally aspirated equivalent. It is in the touring spec:',
  },
  {
    type: 'table',
    rows: [
      ['Component', 'Approximate mass (kg)', 'On the H2?', 'On the SX?'],
      ['Hard luggage mounts (frame + brackets)', '~3.5', 'No', 'Yes'],
      ['Larger 19-litre fuel tank vs H2 17 L', '~1.5 (empty), +2 fuel', 'No', 'Yes'],
      ['Touring windshield + bodywork', '~4', 'No', 'Yes'],
      ['Cruise control hardware + sensors', '~1', 'No', 'Yes'],
      ['Pillion grab rails + larger seat', '~2', 'No', 'Yes'],
      ['Heavier kickstand + centerstand provision', '~2', 'No', 'Yes'],
      ['Longer subframe + tail section', '~5', 'No', 'Yes'],
      ['Stainless brake lines + larger reservoir', '~1', 'No', 'Yes'],
      ['Sum of touring-spec additions', '~20 kg', '–', '–'],
    ],
  },
  {
    type: 'p',
    text: 'About 20 of the 24 kg between the H2 and the H2 SX is touring kit that does nothing for a quarter-mile run. A serious strip racer who removes the luggage mounts, the centerstand, the windshield, the pillion seat and the spare key plate from an H2 SX can realistically drop 12 to 15 kg of dead weight without touching the engine, the chassis or the bodywork. In MotoQuant, taking 12 to 15 kg off the H2 SX gives 10.128 s to 10.109 s and a trap of about 235 km/h, within 0.06 s of a stock Ninja H2.',
  },
  {
    type: 'h2',
    text: 'Where the cheap tenths are',
  },
  {
    type: 'p',
    text: 'Because the H2 SX is already in the 200 hp tier, where mass dominates ET, its cost-per-tenth ranking looks different from a small-cc bike like the R15 V4 or the Pulsar NS200. There is no point spending ₹25,000 on a Powertronic flash that adds 4 hp to a bike already making 200 hp at the crank; the percentage gain is too small to move the ET. The best returns come from mass reduction, launch traction and the specific exhaust changes the supercharger likes.',
  },
  {
    type: 'table',
    rows: [
      ['Mod', 'ET gain (approx)', 'Indian price', '₹ per tenth'],
      ['Strip luggage mounts + windshield + centerstand', '~0.10 s', '~₹0 (just labor)', '~₹0'],
      ['Lithium battery (vs OEM lead-acid, -3.5 kg)', '~0.04 s', '~₹18,000', '~₹45,000'],
      ['Akrapovic GP slip-on (lighter, supercharger-friendly)', '~0.12 s', '~₹1,15,000', '~₹95,000'],
      ['Sticky compound rear (Pirelli Diablo Supercorsa SP)', '~0.06 s', '~₹26,000', '~₹43,000'],
      ['Cassette swap to F18 front (taller, +2 km/h trap)', '~0.02 s', '~₹1,200', '~₹6,000'],
      ['Two-step launch limiter at 7,500 rpm', '~0.08 s', '~₹35,000 (Bazzaz QS-3)', '~₹44,000'],
    ],
  },
  {
    type: 'p',
    text: 'A 2018-2023 H2 SX with the touring kit unbolted (the first row) runs roughly a tenth faster than the same bike with the panniers fitted, for zero rupees of parts. That is the best return in the entire MotoQuant catalog, for any bike at any price: strip-week changes that cost nothing and gain real ET, because the bike leaves the factory carrying mass that does nothing over a quarter mile. After that the cost-per-tenth climbs fast. A full Akrapovic system is ₹95,000 per tenth on the H2 SX, normal for a bike already in the 200 hp tier but four times the cost-per-tenth of an exhaust on a 600 cc bike, where percentage power gains matter more.',
  },
  {
    type: 'callout',
    text: 'For strip days, unbolt the touring kit and fit a sticky rear, and the H2 SX runs within a tenth of a Ninja H2 for zero rupees. Touch nothing else until you can show 10.2 s consistently on a Dragy.',
  },
  {
    type: 'h2',
    text: 'Buying one in India: the gray market',
  },
  {
    type: 'p',
    text: 'Kawasaki India never officially sold the H2 SX. It was only ever a US, European and Japanese-spec bike, so every H2 SX in India is either a personal import on a carnet de passage or a gray-market unit brought in by importers in Mumbai or Bangalore. A clean 2018-2023 base model sells for around ₹28-32 lakh on-road in 2026, depending on year, kilometres, and whether the seller has kept the original Kawasaki service book. The SE+ variants from 2024 onward sell closer to ₹40-45 lakh because they have Öhlins electronic suspension and the latest Kawasaki IMU package.',
  },
  {
    type: 'p',
    text: 'For comparison, a Kawasaki Z H2 costs roughly ₹22-24 lakh in India, the ZX-14R (rarely in stock now) sold at ₹19-21 lakh, and the Hayabusa Gen 3 retails at ₹17.7 lakh ex-showroom Pune in 2026. The H2 SX is the most expensive of these by a wide margin, and its supercharger servicing (impeller bearing replacement at 40,000 km, supercharger oil every 6,000 km) pushes lifetime running cost above any naturally aspirated alternative. People buy it because they want a supercharger and will pay for it. For everyone else, the Hayabusa Gen 3 at less than half the price runs a quarter mile within 0.18 seconds and has a higher reliability ceiling.',
  },
  {
    type: 'h2',
    text: 'Where the cluster bias sits',
  },
  {
    type: 'p',
    text: 'MotoQuant puts the H2 SX in the litre_sport_195p cluster, the top tier of its validation taxonomy. A 2026-05-25 sweep of that cluster across 28 matched benchmarks gave mean|Δ| = 0.171 s and bias = −0.015 s, near zero. The 200 hp bracket of the cluster has the most benchmarks: K5 GSX-R 1000 (10.0334 s, matched exactly), YZF-R1 4C8 (10.2859 s, exact), Hayabusa Gen 1 (10.4712 s, exact) [figures as of that dated sweep; the July 2026 epoch re-based the pins], 2021 ZX-10R (+0.011 s, matched within Sport Rider sample variance), Aprilia RSV4 1100 Factory (matched to instrumented), Panigale V4R (matched to MCN). The H2 SX is the first supercharged sport-tourer in this cluster; every other member is naturally aspirated and fully faired. So although the cluster-average accuracy is best in class, the H2 SX prediction itself is interpolation, not validation. A Dragy run from a stock H2 SX, sent in through the "Submit a timeslip" form, would test it.', // [historical baselines]
  },
  {
    type: 'p',
    text: 'If you own one and record a Dragy timeslip with measured conditions, submit it through the "Submit a timeslip" form; once reviewed, the run joins the benchmark set. That is the long-term plan for closing the cluster bias on every flagship bike in the catalog, with the bench number as the starting point and the timeslips as the ground truth.',
  },
  {
    type: 'h2',
    text: 'Run your own numbers',
  },
  {
    type: 'p',
    text: 'If you own a Ninja H2 SX, or are choosing between one and a Hayabusa or ZX-14R, the simulator at motoquant.in lets you sweep rider weight, ambient temperature, density altitude, tire choice, gearing and parts-catalog mods to see where your tenths come from. The H2 SX preset has the OEM Bridgestone Hypersport S22, the F17/R41 sprocket pair, the 1,480 mm wheelbase, the 0.6 bar peak supercharger boost and the documented torque curve from Kawasaki’s spec sheet. Drop the rider weight to a 65 kg pro and the ET falls by 0.05 s. Raise the temperature to 38 °C, Pune in May, and the supercharger’s intake air density penalty alone slows the bike by 0.18 s. That is more than the same penalty on a naturally aspirated Hayabusa, because the supercharger compresses already-thin air and its volumetric efficiency drops faster.',
  },
  {
    type: 'p',
    text: 'The H2 SX is the only bike in the simulator catalog where the touring spec costs more ET than engine modifications can buy back: take off the panniers and you have done 80 percent of the work. Its supercharged power band is also wide enough to forgive a slightly late shift in a way a 600 cc supersport will not, so an average rider gets much closer to the simulated number on this bike than on a high-revving one. It rewards a measured brake-torque launch and a clean second-to-third upshift more than perfect rev-matching in the higher gears.',
  },
  {
    type: 'p',
    text: 'With hard luggage mounts still bolted on, the H2 SX runs 10.203 seconds at a 232.8 km/h trap. It is level with the Hayabusa Gen 1 on ET and 4.7 km/h faster at the trap. It gives up a third of a second to the ZX-14R’s lighter chassis and bigger engine, and 0.13 seconds and 6.6 km/h to the Ninja H2, which has no touring kit to carry.',
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

      <article id="main" className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {['Kawasaki', 'Ninja H2 SX', 'supercharged', 'sport-tourer', 'India gray market', 'physics'].map((t) => (
              <span
                key={t}
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Kawasaki Ninja H2 SX quarter-mile physics: supercharged tourer
          </h1>
          <div className="text-sm text-white/60 mb-12">
            25 May 2026 · 11 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        <PostBikeLinks ids={[4584]} />

        {/* Internal links / related reading */}
        <div className="max-w-2xl mx-auto mt-16">
          <h3 className="font-display font-bold text-lg text-white mb-4">Related reading</h3>
          <ul className="text-sm text-white/70 space-y-2">
            <li>
              ·{' '}
              <Link
                href="/blog/hayabusa-vs-zx-14r-which-is-faster"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Hayabusa vs ZX-14R: which is faster?
              </Link>:{' '}
              the two naturally aspirated litre-plus rivals the H2 SX is measured against.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/hayabusa-quarter-mile-physics-what-limits-9-6-seconds"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Hayabusa quarter-mile physics: what limits 9.6 seconds
              </Link>:{' '}
              the physics ceiling on a 197 hp naturally aspirated litre-plus bike, to compare with the supercharged H2 SX.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/how-the-motoquant-physics-engine-works"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How the MotoQuant physics engine works
              </Link>:{' '}
              the 15-sub-model architecture behind every ET prediction in this post, including the forced-induction sub-model that handles the H2 SX supercharger.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/how-to-tune-for-aamby-valley-in-november"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to tune for Aamby Valley in November
              </Link>:{' '}
              the venue and conditions used for every ET number in this post.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>:{' '}
              every spec, gear ratio and Cd value the simulator uses, across 340+ bikes.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Run the Ninja H2 SX yourself</div>
            <div className="text-white/60 text-sm">
              Free simulator: pick the Kawasaki Ninja H2 SX, set Aamby Valley November or your local conditions, remove the luggage mounts and watch the ET get close to a Ninja H2.
            </div>
          </div>
          <Link
            href="/simulator?bike=kawasaki-ninja-h2-sx&venue=aamby-valley"
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
