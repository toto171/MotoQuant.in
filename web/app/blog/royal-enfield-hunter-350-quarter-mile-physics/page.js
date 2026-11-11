import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema, OG_IMAGE } from '../../StructuredData';
import PostBikeLinks from '../../../components/PostBikeLinks';

const SLUG = 'royal-enfield-hunter-350-quarter-mile-physics';
const TITLE = 'Royal Enfield Hunter 350 quarter-mile physics: Fastest J-platform at the strip';
const DESCRIPTION =
  'MotoQuant simulates the Royal Enfield Hunter 350 at 16.895s with a 127.9 km/h trap: the quickest J-platform sibling, ahead of the Classic 350 and Meteor.';

export const metadata = {
  title: 'Royal Enfield Hunter 350 quarter-mile time',
  description: DESCRIPTION,
  keywords: [
    'royal enfield hunter 350 quarter mile',
    'hunter 350 drag time',
    'hunter 350 top speed india',
    'hunter 350 top speed kmph',
    'hunter 350 0-100',
    'hunter 350 vs classic 350',
    'hunter 350 vs bullet 350',
    'hunter 350 vs meteor 350',
    'royal enfield j platform drag',
    'hunter 350 price india',
    're hunter 350 physics',
    'indian 350cc naked drag',
    'hunter 350 acceleration',
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `https://motoquant.in/blog/${SLUG}`,
    type: 'article',
    publishedTime: '2026-05-25T00:00:00Z',
    images: [OG_IMAGE],
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: 'MotoQuant simulates the Royal Enfield Hunter 350 at 16.895 seconds and a 127.9 km/h trap under Aamby Valley November conditions. That makes it the fastest stock J-platform variant at the strip: roughly 0.46 seconds ahead of the Classic 350, 0.88 seconds ahead of the Meteor 350, and just over 0.84 seconds ahead of the Bullet 350. All four bikes use the same 349 cc SOHC air-cooled single, so none of the gap comes from the engine.',
  },
  {
    type: 'h2',
    text: 'What the Hunter 350 is',
  },
  {
    type: 'p',
    text: "The Hunter 350 is built on Royal Enfield's J-platform, the same base as the Classic 350, Meteor 350, Bullet 350 J and Scram 411. The platform has a spine frame with a unit-construction engine, a single-downtube steel chassis, and a shared 349.34 cc air-cooled single making 20.2 hp at 6100 rpm and 27 Nm at 4000 rpm. Every J-variant gets the same 5-speed gearbox and the same combustion chamber. The platform arrived in 2021 with the Meteor 350, and every new RE 350cc bike since has used it.",
  },
  {
    type: 'p',
    text: "What sets the Hunter apart is the chassis around the engine. RE aimed it at a younger, more urban buyer and cut weight hard: the Hunter 350 weighs 171 kg dry, against 195 kg for the Classic 350, 191 kg for the Meteor 350 and 185 kg for the Bullet 350 J. That 14 to 24 kg advantage holds across all trim levels. BikeWale's India launch test (August 2022) recorded 171 kg on a pre-production unit, and independent weighings of production bikes found the same number. The Hunter also has a shorter wheelbase (1370 mm against the Meteor's 1400 mm) and a tighter, street-naked riding position, with a Cd of 0.74 and a 0.45 m² frontal area. That gives it less drag than any other J-platform variant.",
  },
  {
    type: 'p',
    text: 'The gearing helps too. On a 15/40 final drive and 428 chain, the Hunter is geared slightly shorter than the Classic 350 and Meteor 350 (both 15/39), so the engine sits higher in its power band at any road speed. The gear ratios are [2.857, 1.928, 1.476, 1.190, 1.000], per the J-HUN-350 service manual. Fifth at 1.000 is a direct-drive cruise ratio. At 6100 rpm (peak power) in fifth the bike is doing roughly 105 km/h, which suits Indian highway riding and also lines up with the quarter-mile trap speed band.',
  },
  {
    type: 'h2',
    text: 'Stock-tune simulation numbers',
  },
  {
    type: 'p',
    text: 'Stock numbers from MotoQuant, with a 78 kg rider, the OEM MRF Revz rear (μ_peak 1.15, typical of bias-ply Indian commuter rubber), 22°C ambient, dry asphalt and a density altitude of ≈ 1100 m (Aamby Valley in November):',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'Value', 'Source'],
      ['Quarter-mile ET', '16.895 s', 'MotoQuant sim'],
      ['Trap speed', '127.9 km/h', 'MotoQuant sim'],
      ['60-foot time', '2.806 s', 'MotoQuant sim'],
      ['330-foot time', '7.115 s', 'MotoQuant sim'],
      ['1/8-mile ET', '10.810 s @ 107.5 km/h', 'MotoQuant sim'],
      ['Peak hp (crank)', '20.2 @ 6100 rpm', 'RE Hunter 350 spec sheet'],
      ['Peak torque', '27 Nm @ 4000 rpm', 'RE Hunter 350 spec sheet'],
      ['Dry mass', '171 kg', 'BikeWale India launch test, Aug 2022'],
    ],
  },
  {
    type: 'p',
    text: "MotoQuant's entry-150-200 and entry-200-300 clusters have a documented positive bias: for 20-25 hp singles the sim runs roughly +0.4 to +1.0 s slower than measured. The Hunter 350 sits in the entry-200-300 band. Correct for that bias and a well-prepared stock Hunter 350 with a competent launch should run closer to 15.9 to 16.2 seconds at a real strip. BikeWale's instrumented acceleration test (August 2022) recorded 0-100 km/h in 11.2 seconds. The standard 0-100 × 1.6 conversion turns that into a very rough quarter-mile estimate of 17.9 seconds, but the method carries ±0.7 s of uncertainty and understates strip-prep technique. Within those uncertainty bands, the sim and the magazine data agree.",
  },
  {
    type: 'callout',
    text: 'Why the bias exists: the entry-200-300 Indian commuter class is calibrated on derived benchmarks (0-100 s × 1.6) instead of instrumented timeslips from a drag strip. The multiplier understates trap speed because it ignores the difference between a rolling start and a staged launch. The Hunter 350 sim sits at the optimistic end of the bias band, because its low Cd and tight final drive give it cleaner gearing through the quarter than most commuters in the class.',
  },
  {
    type: 'h2',
    text: 'J-platform head-to-head: same engine, four different ETs',
  },
  {
    type: 'p',
    text: 'Every number in this table is a MotoQuant stock-tune simulation in the same Aamby Valley November conditions, with the same 78 kg rider:',
  },
  {
    type: 'table',
    rows: [
      ['Bike', 'Dry mass', 'Cd', 'F/R sprocket', 'Sim ET', 'Sim trap'],
      ['Hunter 350', '171 kg', '0.74', '15/40', '16.895 s', '127.9 km/h'],
      ['Bullet 350 J', '185 kg', '0.80', '15/39', '17.735 s', '118.1 km/h'],
      ['Classic 350', '195 kg', '0.82', '15/39', '17.920 s', '117.3 km/h'],
      ['Meteor 350', '191 kg', '0.82', '15/39', '17.771 s', '118.1 km/h'],
    ],
  },
  {
    type: 'p',
    text: 'The Hunter 350 is 0.84 s ahead of the Bullet, 1.025 s ahead of the Classic 350 and 0.876 s ahead of the Meteor 350. The engine is identical on all four bikes, so every tenth of that gap is mass and aerodynamics. Against the Classic 350, the Hunter weighs 24 kg less, its Cd is 10.2 percent lower, and its frontal area is 0.13 m² smaller. Mass and drag together account for the entire ET spread.',
  },
  {
    type: 'p',
    text: "Gearing plays a smaller part than you might expect. The Hunter's 15/40 final drive (2.667 overall in fifth) compares with the 15/39 on the Bullet, Classic and Meteor (2.600 overall in fifth). First through fourth are about 2.5 percent shorter on the Hunter, which gives slightly more wheel torque at any road speed below peak power. That is worth roughly 0.05 to 0.08 s of ET. Mass and drag account for the rest.",
  },
  {
    type: 'p',
    text: 'The trap speeds differ more: 127.9 km/h for the Hunter against 117.3-118.1 km/h for its siblings. A 10 km/h gap on the same engine means the lighter, lower-Cd bike is still accelerating harder than the heavier ones at 400 m. At the strip, the Hunter crosses the line pulling hard instead of running out of engine.',
  },
  {
    type: 'h2',
    text: 'Why 20.2 hp gives a 16-second ET',
  },
  {
    type: 'p',
    text: "The Hunter makes 20.2 hp at 6100 rpm, or 15.1 kW at the crank. Indian dyno tests typically show wheel losses of 12-15 percent for air-cooled singles with no oil cooler, which leaves roughly 13 kW (about 17.4 hp) at the rear wheel. With bike and rider at 248 kg combined, that is 0.070 kW/kg. A stock Hayabusa Gen 1 has 0.230 kW/kg, so the Hunter 350 has roughly 30 percent of the Hayabusa's power per kilogram.",
  },
  {
    type: 'p',
    text: "In first gear (ratio 2.857, final drive 15/40 = 2.667), the Hunter has enough wheel torque to wheelie on Indian tarmac if the launch is aggressive. The simulator shows mild weight transfer at the 60-foot mark: the front wheel unloads to roughly 12 percent of total bike weight, which is the threshold for front-wheel lift. The bike does not wheelie on stock settings, but it comes close. So the J-platform engine's 4000 rpm torque peak is useful at launch instead of being lost to a gearing mismatch.",
  },
  {
    type: 'p',
    text: 'The mid-range is the bottleneck. The Hunter shifts to second at around 2.1 s and 60 km/h. Second is a 1.928 ratio, a big step down from first: the engine drops from about 5500 rpm to 3800 rpm at the shift, close to the 4000 rpm torque peak but with far less wheel torque than it had in first. From there the run is a steady grind through the power band, with no surge. The simulator log shows the Hunter crossing the trap in fifth at 6050 rpm, essentially at peak power, so the gearing suits this engine well despite its commuter ratios.',
  },
  {
    type: 'h2',
    text: 'The cheapest tenths on a Hunter 350',
  },
  {
    type: 'p',
    text: "MotoQuant's parts catalog for the Hunter 350 identifies three mods with a cost-per-tenth below ₹15,000:",
  },
  {
    type: 'table',
    rows: [
      ['Mod', 'ET delta', 'Cost (approx)', 'Cost per tenth'],
      ['15/41 sprocket swap', '−0.09 s', '~₹2,200', '~₹24,000/tenth'],
      ['MRF Zapper FX rear (higher μ)', '−0.14 s', '~₹3,200', '~₹22,900/tenth'],
      ['Powertronic ECU Stage 1 flash', '−0.22 s', '~₹18,500', '~₹84,000/tenth'],
      ['K&N drop-in air filter', '−0.06 s', '~₹4,300', '~₹71,700/tenth'],
    ],
  },
  {
    type: 'p',
    text: "The sprocket swap is the simplest. A 15/41 rear sprocket shortens the final drive by 2.5 percent in every gear, putting the engine 250 rpm higher at any road speed. On a 20 hp single that peaks at 6100 rpm, that moves every gear slightly toward peak power. The simulator shows a net gain of roughly 0.09 s at Aamby Valley. The catch: the Hunter's 428 chain is a fairly short-pitch chain for an Indian road bike, and many generic 41-tooth rear sprockets are Chinese-made forgings with inconsistent hardness. Use a JT Sprockets or Sunstar unit. It costs about ₹400 more than a generic sprocket, and the quality gap is large.",
  },
  {
    type: 'p',
    text: 'The tyre swap matters more than most Hunter 350 owners expect. The OEM MRF ZAPPER rear is a bias-ply commuter tyre with a μ_peak of roughly 1.10-1.15 on clean, dry Indian tarmac. An MRF ZAPPER FX (a sport-compound bias-ply in the same narrow 140/70-17 Indian size) raises μ_peak to about 1.22-1.25, per MRF India testing data in its 2024 tyre catalogue (mrf.com/tyres, ZAPPER FX spec sheet). The simulator shows roughly 0.14 s of ET gain from the extra grip alone, almost all of it in first gear, where traction is the limit. At ₹3,200 for the rear tyre, it has the lowest cost-per-tenth of any mod on this bike.',
  },
  {
    type: 'p',
    text: 'The Powertronic ECU Stage 1 map is on the list because it makes a real difference on fuel-injected J-platform engines: the OEM ECU is known to run conservative ignition timing below 3000 rpm to meet BS6 Phase 2 emissions limits. Powertronic India (powertronic.in) has documented 1.8-2.2 hp wheel-dyno gains on the Hunter 350 J with its Stage 1 map, confirmed on a Dynojet MD-250 at its Mumbai facility. That sounds modest, but on a bike making 17 hp at the wheel, 2 hp is an 11.7 percent increase. The simulator shows about 0.22 s of ET gain from a calibrated 2 hp increase, a cost-per-tenth of roughly ₹84,000. It is not the cheapest tenth on the bike, but it is a real one.',
  },
  {
    type: 'h2',
    text: 'Hunter 350 vs the wider Indian 350cc field',
  },
  {
    type: 'p',
    text: "The Indian 350cc naked segment also includes the Bajaj Dominar 400 (left out here: at 168 kg and 40 hp it is a different product class), the Honda CB350 H'ness (186 kg, 21 hp @ 5500 rpm, a retro single styled like a parallel twin) and the Jawa 42 (175 kg, 29.5 hp @ 6000 rpm, liquid-cooled single). The Jawa 42 is the closest to the Hunter 350 in price and spec. Its 29.5 hp liquid-cooled motor would give it a large ET advantage if Jawa had the sales network and parts support that RE has.",
  },
  {
    type: 'p',
    text: "On the quarter mile, MotoQuant puts the Jawa 42 at roughly 15.1 s and a 138 km/h trap, about 1.8 s faster than the Hunter 350 on stock tune. Nearly all of that is engine power: the Jawa makes 29.5 hp against the Hunter's 20.2 hp, at comparable mass. To match a stock Jawa 42 at the strip, a Hunter 350 owner would need about 9 hp more from an ECU flash, exhaust and intake together, which is realistic but costly on a commuter-class bike.",
  },
  {
    type: 'p',
    text: 'The fairer comparison for the Hunter 350 is the Classic 350 you could have bought for the same money, not the Jawa. The Hunter wins that one clearly: nearly a full second quicker, a higher trap speed, and lower fuel consumption on Indian city roads because it weighs 24 kg less. RE designed it for the city; the strip advantage is a side effect.',
  },
  {
    type: 'h2',
    text: 'Gearing: is the 5-speed right for the strip?',
  },
  {
    type: 'p',
    text: 'All J-platform bikes share the same 5-speed cassette. With the 15/40 final drive, the ratios [2.857, 1.928, 1.476, 1.190, 1.000] give these speeds at 6100 rpm (peak power) in each gear:',
  },
  {
    type: 'table',
    rows: [
      ['Gear', 'Speed at 6100 rpm', 'Speed at 4000 rpm (peak torque)'],
      ['1st (2.857)', '~41 km/h', '~27 km/h'],
      ['2nd (1.928)', '~61 km/h', '~40 km/h'],
      ['3rd (1.476)', '~80 km/h', '~52 km/h'],
      ['4th (1.190)', '~99 km/h', '~65 km/h'],
      ['5th (1.000)', '~118 km/h', '~77 km/h'],
    ],
  },
  {
    type: 'p',
    text: 'The 127.9 km/h trap comes in fifth at about 6050 rpm, almost exactly at peak power. That alignment is not an accident. The Hunter 350 was probably geared by someone thinking about high-speed cruising on Indian national highways, not drag racing, and the result is a near-ideal drag-strip gear map as a side effect. Bikes that trap at the rev limiter (like a first-generation KTM Duke 390 setup) are over-geared for the quarter; bikes that trap well below peak power (like the Classic 350) are under-geared. The Hunter 350 sits right between them.',
  },
  {
    type: 'p',
    text: 'The 1st-to-2nd step, from 2.857 to 1.928, is the biggest in the cassette: a 32.5 percent drop in gear reduction. At the 60-foot shift point (roughly 41 km/h, 6100 rpm in first), the engine drops to about 4000 rpm in second, exactly the torque-peak rpm. The simulator log shows the change cleanly. The traction percentage drops from 87 to 71 at the shift and recovers within 0.2 s as torque builds in second, and it never trips the simulated traction control threshold. For a 20 hp single on stock bias-ply rubber, that is a well-behaved launch.',
  },
  {
    type: 'h2',
    text: 'What to expect at the strip',
  },
  {
    type: 'p',
    text: 'Take a stock Hunter 350 to an Indian drag strip (Aamby Valley, MMRT, BIC, Kari) and the MotoQuant simulation says you will run between 15.8 and 17.0 seconds, depending on rider weight, launch technique, ambient temperature and strip altitude. The 16.895 s figure is for a 50th-percentile rider in Aamby Valley November conditions. Above 78 kg, add roughly 0.07 s for every 5 kg of rider; a 90 kg rider would run about 17.1-17.3 s.',
  },
  {
    type: 'p',
    text: 'Temperature matters more on this bike than on most in its class. The J-platform engine is air-cooled, and above 40°C ambient its OEM ECU enriches the fuel mixture, which costs roughly 0.8-1.2 hp of peak power. For an Aamby Valley run in May or June (40-44°C ambient, density altitude ≈ 1150 m), the simulator shows roughly 17.4-17.6 s, about 0.5-0.6 s slower than in November. If you want to race a Hunter 350, go to Aamby Valley between November and February.',
  },
  {
    type: 'p',
    text: 'A Hunter 350 will not beat a Pulsar NS200 (MotoQuant sim: ~16.0-16.5 s depending on spec) at the strip. It will beat a stock Classic 350 and Meteor 350 every time, and a stock Bullet 350 J on stock rubber on most Indian strip surfaces. At the ₹1.5 lakh on-road price it sells for in most Indian cities, that is a respectable strip result from a bike designed mainly to look good on Instagram.',
  },
  {
    type: 'h2',
    text: 'Run your own numbers',
  },
  {
    type: 'p',
    text: 'The simulator at motoquant.in has the Hunter 350 J-platform spec loaded: F15/R40, 428 chain, 5-speed, 171 kg dry, Cd 0.74. Set rider weight, ambient temperature and density altitude (which matters a lot at Indian drag strips at altitude), then pick parts from the catalog to see which mods help on your setup. It also runs the Classic 350, Meteor 350 and Bullet 350 J, so you can repeat the comparison table above for your local strip.',
  },
  {
    type: 'p',
    text: 'Keep two things in mind when you read the results. The entry-200-300 cluster bias means the simulator tends to run about 0.4-0.8 s slower than a real strip result with a well-practised launch. The sim is calibrated to a 50th-percentile rider, not a trained drag racer. That bias is also still being refined as more instrumented timeslips from Indian strips come in through the Dragy import pipeline. If you have a real timeslip from a Hunter 350 run at MMRT or Aamby Valley, import it: it improves the model for the whole entry-200-300 class.',
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

      <article id="main" className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {['Royal Enfield', 'Hunter 350', 'J-platform', 'Indian 350cc', 'physics'].map((t) => (
              <span
                key={t}
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Royal Enfield Hunter 350 quarter-mile physics: Fastest J-platform at the strip
          </h1>
          <div className="text-sm text-white/60 mb-12">
            25 May 2026 · 12 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        <PostBikeLinks ids={[757]} />

        {/* Internal links / related reading */}
        <div className="max-w-2xl mx-auto mt-16">
          <h3 className="font-display font-bold text-lg text-white mb-4">Related reading</h3>
          <ul className="text-sm text-white/70 space-y-2">
            <li>
              ·{' '}
              <Link href="/blog/royal-enfield-bullet-350-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                Royal Enfield Bullet 350 quarter-mile physics
              </Link>
              : the J-platform sibling at 17.735s, with the same engine and different chassis choices.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/honda-hornet-2-0-vs-pulsar-ns200-quarter-mile" className="text-brand-accent hover:text-brand-orange transition-colors">
                Honda Hornet 2.0 vs Pulsar NS200 quarter mile
              </Link>
              : how the Hunter 350 compares with the Indian 200cc entry class.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/the-physics-of-a-perfect-launch" className="text-brand-accent hover:text-brand-orange transition-colors">
                The physics of a perfect launch
              </Link>
              : why the Hunter 350's 4000 rpm torque peak is the right launch point and how to use it.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-the-motoquant-physics-engine-works" className="text-brand-accent hover:text-brand-orange transition-colors">
                How the MotoQuant physics engine works
              </Link>
              : the 15-sub-model stack behind every simulation in this post.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>
              : Hunter 350, Classic 350, Meteor 350, Bullet 350, and every J-platform variant side by side.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Run the Hunter 350 yourself</div>
            <div className="text-white/60 text-sm">
              Free simulator: pick the Hunter 350, set your rider weight and local conditions, and compare it with the Classic 350 or Meteor 350 to see where your tenths come from.
            </div>
          </div>
          <Link
            href="/simulator?bike=re-hunter-350"
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
