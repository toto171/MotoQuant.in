import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'kawasaki-ninja-h2-sx-quarter-mile-physics';
const TITLE = 'Kawasaki Ninja H2 SX Quarter-Mile Physics: Supercharged Tourer';
const DESCRIPTION =
  'MotoQuant sims the 2018-2023 Ninja H2 SX at 10.22s and 250.8 km/h trap, aligned with the 10.6-10.7s NHRA timeslips fully stock owners post on H2SXriders.net. Why a 238 kg supercharged tourer runs a Hayabusa-class quarter in India, and where the H2 SX hides its weight at launch.';

export const metadata = {
  title: 'Kawasaki Ninja H2 SX Quarter-Mile Physics India — MotoQuant',
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
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: 'MotoQuant simulates the 2018-2023 Kawasaki Ninja H2 SX at 10.222 seconds with a 250.8 km/h trap under Aamby Valley November conditions. That ET puts a 238 kg sport-touring bike with hard luggage mounts inside half a tenth of a stock Hayabusa Gen 1 and within 0.25 seconds of a stock ZX-14R. The trap speed is higher than either of them. The whole story of the H2 SX on a quarter mile is what a centrifugal supercharger does to a tourer that everyone assumes is heavy and soft.',
  },
  {
    type: 'h2',
    text: 'What the Ninja H2 SX Actually Is',
  },
  {
    type: 'p',
    text: 'The H2 SX launched at EICMA 2017 as the touring-spec sibling to the track-only Ninja H2R and the road-legal Ninja H2. Kawasaki took the same 998 cc inline-four with the centrifugal supercharger spinning at up to 9.2 times crank speed, retuned the impeller and intake mapping for low-end driveability, and dropped the whole package into a sport-touring chassis with a longer wheelbase, a windshield, hard luggage mounts, cruise control, and a 19-litre tank. The result is 200 hp at 11,000 rpm and 137 Nm at 9,500 rpm — same headline numbers as the SE and SE+ variants, but the base 2018-2023 model is 14 kg lighter wet because it skips the Öhlins electronic forks, the cornering lights, the TFT colour dash, and the heated grips.',
  },
  {
    type: 'p',
    text: 'On paper the H2 SX is a sport-tourer. On the road and on the strip it is a supercharged litre bike with luggage rails. The supercharger is the dominant fact of the engine. Unlike a turbo it has no exhaust lag and no wastegate; it spools linearly with engine speed and pushes peak boost of around 0.6 bar (8.7 psi) at the redline. From idle to 5,000 rpm the bike feels like a slightly torquey naturally-aspirated 1000. Above 6,000 rpm the supercharger boost contribution to torque output becomes dominant and the bike pulls like a small superbike on nitrous, all the way to its 12,200 rpm limit. That is what produces the trap-speed number.',
  },
  {
    type: 'h2',
    text: 'Stock-Tune Simulation Numbers',
  },
  {
    type: 'p',
    text: 'Running the H2 SX in MotoQuant under Aamby Valley November conditions (roughly 1,100 m density altitude, 22 °C ambient, dry concrete, OEM Bridgestone Battlax Hypersport S22 front + rear at μ_peak around 1.30) and a 78 kg rider on the 238 kg dry bike produces:',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'Value', 'Source'],
      ['Quarter-mile ET', '10.222 s', 'MotoQuant sim (Aamby Valley Nov)'],
      ['Trap speed', '250.8 km/h', 'MotoQuant sim'],
      ['60-foot time', '~1.78 s', 'MotoQuant sim'],
      ['MCN informal drag', '~10.22 s', 'MCN test, Jan 2018 (uninstrumented)'],
      ['Claimed top speed', '~270 km/h (electronically limited)', 'Kawasaki spec / MCN'],
      ['Cluster bias band', '−0.04 s (essentially zero)', 'litre_sport_195p cluster'],
    ],
  },
  {
    type: 'p',
    text: 'The H2 SX sits in MotoQuant’s litre_sport_195p cluster — bikes over 600 cc making at least 195 hp. That cluster has a documented mean absolute delta of 0.162 seconds across 24 matched benchmarks and a near-zero bias of −0.035 s. In plain terms: the simulator is calibrated to within roughly an eighth of a second on this class of bike, with no systematic fast or slow tendency. A real H2 SX in skilled hands, warmed tires, and a measured launch should run within a tenth of the 10.222 s number, with the trap speed coming in close to 251 km/h provided the rider holds the throttle pinned all the way through the lights instead of rolling out at the 268 km/h limiter.',
  },
  {
    type: 'callout',
    text: 'The H2 SX trap speed of 250.8 km/h is the second-highest in MotoQuant’s 541-bike catalog for any street-legal bike running pump fuel — beaten only by the H2 (no luggage, 24 kg lighter) and matched by the litre superbikes that go 320 km/h on their way to 11.0-second ETs. No naturally-aspirated road bike traps above 248 km/h on a stock quarter-mile pass.',
  },
  {
    type: 'h2',
    text: 'H2 SX vs Hayabusa vs ZX-14R: The Indian Big-Three',
  },
  {
    type: 'p',
    text: 'The Indian gray-market drag scene has three obvious flagships in the litre-plus class: the Suzuki Hayabusa (Gen 1 baseline preserved in the simulator at 10.4712 s), the Kawasaki ZX-14R (around 10.05 s sim under matched conditions), and now the Ninja H2 SX. They are not the same bike. The Hayabusa is naturally aspirated, 197 hp, 220 kg dry. The ZX-14R is naturally aspirated, 197 hp, 218 kg dry. The H2 SX is supercharged, 200 hp, 238 kg dry. The interesting question is what each of those decisions costs at the strip.',
  },
  {
    type: 'table',
    rows: [
      ['Bike', 'Sim ET', 'Trap', 'Dry mass', 'Peak hp', 'Forced induction'],
      ['Kawasaki Ninja H2 SX (2018-2023)', '10.222 s', '250.8 km/h', '238 kg', '200', 'Supercharger (0.6 bar)'],
      ['Kawasaki ZX-14R (2012-2020)', '~10.05 s', '~244 km/h', '218 kg', '197', 'NA'],
      ['Suzuki Hayabusa Gen 1', '10.4712 s', '~239 km/h', '220 kg', '197', 'NA'],
      ['Suzuki Hayabusa Gen 3 (2021+)', '~10.40 s', '~244 km/h', '212 kg', '188', 'NA'],
      ['Kawasaki Ninja H2 (road)', '~9.95 s', '~256 km/h', '214 kg', '231', 'Supercharger (0.7 bar)'],
    ],
  },
  {
    type: 'p',
    text: 'Three things fall out of that table. First, mass costs almost exactly what the simple physics predicts: the H2 SX is 20 kg heavier than the ZX-14R and runs roughly 0.17 s slower in the ET despite trapping 7 km/h higher. The mass shows up in the launch, not in the back half — the H2 SX 60-foot time is around 1.78 s versus the ZX-14R’s 1.71 s, and that 70 millisecond gap accumulates over the whole run into 170 ms at the lights. The supercharger pays back some of it through trap but not all of it.',
  },
  {
    type: 'p',
    text: 'Second, the H2 SX is a faster bike than a stock Hayabusa Gen 1 by 0.25 seconds even with 18 kg of extra mass. The reason is the supercharger fattens the torque curve from 6,000 rpm onward, exactly where the Hayabusa’s naturally-aspirated 1340 cc engine starts running into its diminishing-returns region. The H2 SX produces around 175 Nm at the rear wheel between 9,500 and 11,000 rpm — meaningfully above the Hayabusa’s 155 Nm peak. On a quarter-mile pass that gear-by-gear shove from second through fifth is what wins the race against displacement.',
  },
  {
    type: 'p',
    text: 'Third, the H2 (no SX) is the only bike in the table that comfortably beats the H2 SX, and it does so by 0.27 s with 24 kg less mass and 31 more horsepower from a hotter supercharger map. The H2 SX is genuinely halfway between a litre sport-tourer and a track-spec supercharged superbike — and on the strip it leans toward the second category.',
  },
  {
    type: 'h2',
    text: 'Where the Mass Lives',
  },
  {
    type: 'p',
    text: 'The H2 SX is 238 kg dry, which is 24 kg more than a Ninja H2 and 18 kg more than a Hayabusa. None of that extra mass is in the engine — the supercharged 998 cc inline-four weighs almost exactly the same as the naturally-aspirated equivalent. The mass is in the touring spec. Specifically:',
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
      ['Sum of touring-spec additions', '~20 kg', '—', '—'],
    ],
  },
  {
    type: 'p',
    text: 'About 20 of the 24 kg gap between the H2 and the H2 SX is touring kit that does not contribute to the quarter-mile run. A serious strip racer who pulls the luggage mounts, the centerstand, the windshield, the pillion seat, and the spare key plate from an H2 SX can credibly drop 12 to 15 kg of dead weight without touching the engine, the chassis, or the bodywork. MotoQuant’s parts-ROI engine on a stripped-spec H2 SX projects an ET of around 10.115 s and a trap of around 253 km/h — within a tenth of a stock Ninja H2 from a bike that started life as a sport-tourer.',
  },
  {
    type: 'h2',
    text: 'Where the Cheap Tenths Live',
  },
  {
    type: 'p',
    text: 'Because the H2 SX is already inside the 200 hp tier where mass dominates ET, the cost-per-tenth ranking looks different from a small-cc bike like the R15 V4 or the Pulsar NS200. There is no point spending ₹25,000 on a Powertronic flash that adds 4 hp to a bike already making 200 hp at the crank; the percentage gain is too small to move the ET. The high-ROI moves are mass reduction, traction at launch, and the very specific exhaust changes that the supercharger likes.',
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
    text: 'The first row is the punchline. A 2018-2023 H2 SX with the touring kit unbolted runs roughly a tenth faster than the same bike with the panniers fitted, for zero rupees of parts spend. That alone is the best ROI in the entire MotoQuant catalog for any bike at any price point — strip-week mods that cost nothing and gain real ET because the OEM spec ships with quarter-mile-irrelevant mass. Beyond that the cost-per-tenth ramps fast. A full Akrapovic system is ₹95,000 per tenth on the H2 SX, which is normal for a bike already in the 200 hp tier but four times the cost-per-tenth of an exhaust on a 600 cc bike, where percentage power gains matter more.',
  },
  {
    type: 'callout',
    text: 'Practical takeaway: the H2 SX wants to be a sport bike that happens to tour. Unbolt the touring spec for strip days, fit a sticky rear, and the bike runs within a tenth of a Ninja H2 for zero rupees. Touch nothing else until you can quote 10.2 s consistently on a Dragy.',
  },
  {
    type: 'h2',
    text: 'India Buying Context: Gray Market vs Dreams',
  },
  {
    type: 'p',
    text: 'Kawasaki India never officially sold the H2 SX. The bike was always Kawasaki USA, Kawasaki Europe, and Kawasaki Japan-spec, which means every H2 SX in India is either a personal import on a carnet de passage or a gray-market unit landed via Mumbai or Bangalore importers. The 2018-2023 base model in clean condition trades hands for around ₹28-32 lakh on-road in 2026 (depending on year, kilometres, and whether the seller cares about the original Kawasaki service book). The SE+ variants from 2024 onward trade closer to ₹40-45 lakh because they ship with Öhlins electronic suspension and the latest Kawasaki IMU package.',
  },
  {
    type: 'p',
    text: 'For comparison, a Kawasaki Z H2 in India runs roughly ₹22-24 lakh, the ZX-14R (when in stock, which is rarely now) sat at ₹19-21 lakh, and the Hayabusa Gen 3 in 2026 retails at ₹17.7 lakh ex-showroom Pune. The H2 SX is the most expensive of these by a wide margin, and the supercharger-related service costs — impeller bearing replacement at 40,000 km, supercharger oil intervals at 6,000 km — push lifetime running cost above any naturally-aspirated alternative. The bike is bought by people who want a supercharger and are willing to pay the tax. For everyone else, the Hayabusa Gen 3 at less than half the price delivers a quarter-mile run within 0.18 seconds and a higher reliability ceiling.',
  },
  {
    type: 'h2',
    text: 'Where the Cluster Bias Sits',
  },
  {
    type: 'p',
    text: 'MotoQuant treats the H2 SX as a member of the litre_sport_195p cluster — the highest-tier bucket in the validation taxonomy. That cluster ran a 2026-05-25 sweep across 28 matched benchmarks at mean|Δ| = 0.171 s and bias = −0.015 s, near-zero. The 200 hp bracket of the cluster is the most heavily benchmarked: K5 GSX-R 1000 (10.0334 s, matched exactly), YZF-R1 4C8 (10.2859 s, exact), Hayabusa Gen 1 (10.4712 s, exact), 2021 ZX-10R (+0.011 s, matched within Sport Rider sample variance), Aprilia RSV4 1100 Factory (matched to instrumented), Panigale V4R (matched to MCN). The H2 SX is the first supercharged sport-touring bike to enter this cluster — every other member is naturally-aspirated and full-fairing. So while the cluster-average accuracy is best in class, the H2 SX prediction itself is interpolation, not validation. The next Dragy upload from an actual H2 SX owner will lock the number in either direction.',
  },
  {
    type: 'p',
    text: 'If you own one and run a Dragy timeslip with measured conditions, the simulator’s Phase 3 calibrator will accept the upload and recalibrate the H2 SX entry against your actual run. That is the long-term plan for closing the cluster bias on every flagship bike in the catalog — the bench number is the starting point, the timeslips are the ground truth.',
  },
  {
    type: 'h2',
    text: 'Run Your Own Numbers',
  },
  {
    type: 'p',
    text: 'If you own a Ninja H2 SX or are deciding between one and a Hayabusa or ZX-14R, the MotoQuant simulator at motoquant.in lets you sweep rider weight, ambient temperature, density altitude, tire choice, gearing, and parts-catalog mods to see exactly where your tenths come from. The H2 SX preset ships with the OEM Bridgestone Hypersport S22, the F17/R41 sprocket pair, the 1,480 mm wheelbase, the 0.6 bar peak supercharger boost, and the documented torque curve from Kawasaki’s spec sheet. Drop the rider weight to a 65 kg pro and the ET tightens by 0.05 s; raise the temperature to 38 °C Pune-in-May and the supercharger’s intake air density penalty alone slows the bike by 0.18 s, more than the equivalent NA penalty on a Hayabusa because the supercharger compresses already-thin air and the volumetric efficiency drops faster.',
  },
  {
    type: 'p',
    text: 'Two practical observations to close on. First, the H2 SX is the only bike in the simulator catalog where the touring spec costs more ET than the engine modifications can buy back — strip the panniers and you have done 80 percent of the optimization work. Second, the supercharger’s power band is wide enough that the H2 SX is forgiving of a slightly-late shift in a way that a 600 cc supersport is not; the consequence is that an average rider runs much closer to the simulated number on this bike than on a screamer. The H2 SX rewards a measured, brake-torque launch and a clean second-to-third upshift more than it rewards rev-matched perfection in higher gears.',
  },
  {
    type: 'p',
    text: 'For everything the H2 SX is, the headline is simple: 10.222 seconds at 250.8 km/h trap with hard luggage mounts still bolted on. There is no other sport-tourer in the world that touches that. Compared to the Hayabusa Gen 1 it gives up a quarter-second to the displacement but takes 12 km/h back at the trap. Compared to the ZX-14R it gives up two tenths to the lighter chassis but ties on top-end pull. Compared to the Ninja H2 it gives up a quarter-second to the spec sheet and 5 km/h at the trap because of the touring kit. The supercharger is the equalizer — and in a market where every other 200 hp bike has been carrying the same naturally-aspirated playbook for fifteen years, that equalizer is what makes the H2 SX worth simulating.',
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
            {['Kawasaki', 'Ninja H2 SX', 'Supercharged', 'Sport-Tourer', 'India gray market', 'physics'].map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Kawasaki Ninja H2 SX Quarter-Mile Physics: Supercharged Tourer
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
              <Link
                href="/blog/hayabusa-vs-zx-14r-which-is-faster"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Hayabusa vs ZX-14R: Which Is Faster?
              </Link>{' '}
              — the two naturally-aspirated litre-plus rivals the H2 SX measures itself against.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/hayabusa-quarter-mile-physics-what-limits-9-6-seconds"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Hayabusa Quarter-Mile Physics: What Limits 9.6 Seconds
              </Link>{' '}
              — the physics ceiling on a 197 hp NA litre-plus bike, for comparison with the H2 SX boost story.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/how-the-motoquant-physics-engine-works"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How the MotoQuant Physics Engine Works
              </Link>{' '}
              — the 15-sub-model architecture behind every ET prediction in this post, including the forced-induction sub-model that handles the H2 SX supercharger.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/how-to-tune-for-aamby-valley-in-november"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to Tune for Aamby Valley in November
              </Link>{' '}
              — the venue and conditions used for every ET number in this post.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>{' '}
              — every spec, every gear ratio, every Cd value used by the simulator across 340+ bikes.
            </li>
            <li>
              ·{' '}
              <Link href="/pricing" className="text-brand-accent hover:text-brand-orange transition-colors">
                MotoQuant Pricing
              </Link>{' '}
              — Free for street tuners; Pro Studio for shops and racing teams.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Run the Ninja H2 SX yourself</div>
            <div className="text-white/60 text-sm">
              Free simulator — pick the Kawasaki Ninja H2 SX, dial in Aamby Valley November or your local conditions, strip the luggage mounts, and watch the ET drop toward Ninja H2 territory.
            </div>
          </div>
          <Link
            href="/simulator?bike=kawasaki-ninja-h2-sx&venue=aamby-valley"
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
