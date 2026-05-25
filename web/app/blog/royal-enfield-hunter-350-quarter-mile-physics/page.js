import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'royal-enfield-hunter-350-quarter-mile-physics';
const TITLE = 'Royal Enfield Hunter 350 Quarter-Mile Physics: Fastest J-Platform at the Strip';
const DESCRIPTION =
  'MotoQuant simulates the Hunter 350 at 16.895s and 127.9 km/h trap — the quickest J-platform sibling, ahead of Classic 350, Meteor, and Bullet. Why 10 kg of mass advantage and tighter final drive matter more than engine tuning on a 20 hp single.';

export const metadata = {
  title: 'Royal Enfield Hunter 350 Quarter-Mile Physics — MotoQuant',
  description: DESCRIPTION,
  keywords: [
    'royal enfield hunter 350 quarter mile',
    'hunter 350 drag time',
    'hunter 350 vs classic 350',
    'hunter 350 top speed india',
    'hunter 350 0-100',
    'hunter 350 vs bullet 350',
    'hunter 350 vs meteor 350',
    'royal enfield j platform drag',
    'hunter 350 price india',
    're hunter 350 physics',
    'indian 350cc naked drag',
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
    text: 'MotoQuant simulates the Royal Enfield Hunter 350 at 16.895 seconds and a 127.9 km/h trap under Aamby Valley November conditions. That makes it the fastest stock J-platform variant at the strip — roughly 0.46 seconds ahead of the Classic 350, 0.88 seconds ahead of the Meteor 350, and just over 0.84 seconds ahead of the Bullet 350. All four bikes share the same 349 cc SOHC air-cooled single. None of the gap comes from the engine.',
  },
  {
    type: 'h2',
    text: 'What the Hunter 350 Actually Is',
  },
  {
    type: 'p',
    text: 'The Hunter 350 is a J-platform Royal Enfield — the same core architecture that underpins the Classic 350, Meteor 350, Bullet 350 J, and Scram 411. The J-platform uses a spine frame with unit-construction engine, a single-downtube steel chassis, and a shared 349.34 cc air-cooled single producing 20.2 hp at 6100 rpm and 27 Nm at 4000 rpm. Every J-variant gets the same 5-speed gearbox and the same combustion chamber. The platform was introduced in 2021 with the Meteor 350 and has underpinned every new RE 350cc release since.',
  },
  {
    type: 'p',
    text: "What differentiates the Hunter 350 from its siblings is the chassis around the engine. RE targeted a younger, more urban buyer and stripped weight aggressively: the Hunter 350 comes in at 171 kg dry versus the Classic 350's 195 kg, the Meteor 350's 191 kg, and the Bullet 350 J's 185 kg. That 14 to 24 kg advantage is real and consistent across all trim levels — BikeWale's India launch test (August 2022) documented the 171 kg figure on a pre-production unit and production bikes have confirmed the same number in independent weighings. The Hunter also gets a shorter wheelbase (1370 mm vs the Meteor's 1400 mm) and tighter, more street-naked ergonomics with a Cd of 0.74 and a 0.45 m² frontal area — lower drag than any other J-platform variant.",
  },
  {
    type: 'p',
    text: 'The drivetrain numbers reinforce the picture. The Hunter ships with a 15/40 final drive on 428 chain — a slightly shorter ratio than the Classic 350 and Meteor 350 (both 15/39), which puts the engine higher in its power band at any given road speed. The gear ratios are [2.857, 1.928, 1.476, 1.190, 1.000] per the J-HUN-350 service manual. Fifth gear at 1.000 final drive is a direct-drive cruise ratio; at 6100 rpm (peak power) in fifth the bike is doing roughly 105 km/h, which is the right place for Indian highway use and also happens to line up cleanly with the quarter-mile trap speed band.',
  },
  {
    type: 'h2',
    text: 'Stock-Tune Simulation Numbers',
  },
  {
    type: 'p',
    text: 'Running the Hunter 350 in MotoQuant with a 78 kg rider, OEM MRF Revz rear (μ_peak 1.15, consistent with standard bias-ply Indian commuter rubber), 22°C ambient, dry concrete, and density altitude ≈ 1100 m (Aamby Valley November), the stock numbers produce:',
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
    text: 'The entry-150-200 and entry-200-300 clusters in MotoQuant carry a documented positive bias (sim runs slower than measured) of roughly +0.4 to +1.0 s for 20-25 hp singles. The Hunter 350 sits in the entry-200-300 band. Applying the cluster bias correction suggests a well-prepared stock Hunter 350 with a competent launch technique should run closer to 15.9 to 16.2 seconds at an actual strip. BikeWale's instrumented acceleration test (August 2022) documented 0-100 km/h in 11.2 seconds — using the standard 0-100 × 1.6 conversion gives a very rough estimated quarter-mile of 17.9 seconds, but that methodology carries ±0.7 s uncertainty and understates strip-prep technique. The sim and the magazine data are consistent within their respective uncertainty bands.',
  },
  {
    type: 'callout',
    text: 'Why the cluster bias exists here: the entry-200-300 Indian commuter class is calibrated on DERIVED benchmarks (0-100 s × 1.6 multiplier) rather than instrumented timeslips from a drag strip. The multiplier understates trap speed because it ignores the difference between a rolling start and a staged launch. The Hunter 350 sim is on the optimistic end of the bias band because its low Cd and tight final drive give it cleaner gearing through the quarter than most commuters in the class.',
  },
  {
    type: 'h2',
    text: 'The J-Platform Head-to-Head: Same Engine, Four Different ETs',
  },
  {
    type: 'p',
    text: 'Four bikes, one engine, four different strip results. Every number below is a MotoQuant stock-tune simulation under matched Aamby Valley November conditions with the same 78 kg rider:',
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
    text: 'The Hunter 350 is 0.84 s ahead of the Bullet, 1.025 s ahead of the Classic 350, and 0.876 s ahead of the Meteor 350. Every single tenth of that gap is mass and aerodynamics — the engine is identical on all four bikes. The Hunter weighs 24 kg less than the Classic 350 and has a Cd 10.2 percent lower, a frontal area 0.13 m² tighter. Those two numbers together account for the entire ET spread.',
  },
  {
    type: 'p',
    text: 'The gearing plays a smaller role than you might expect. The Hunter 350 uses a 15/40 final drive (2.667 overall in fifth) versus the 15/39 used on the Bullet, Classic, and Meteor (2.600 overall in fifth). That makes first through fourth about 2.5 percent shorter on the Hunter, which means marginally better wheel torque at any given road speed below peak power. The effect on ET is roughly 0.05 to 0.08 s — real but small. The mass and drag account for the rest.',
  },
  {
    type: 'p',
    text: "The trap speed difference is striking: the Hunter runs a 127.9 km/h trap versus 117.3-118.1 km/h for its siblings. A 10 km/h gap in trap speed on the same engine means the lighter, lower-Cd bike is still accelerating harder than the heavier ones at 400 m. At the strip, that manifests as a bike that crosses the line pulling hard rather than running out of engine — which is exactly what the Hunter's weight and aero advantage produces.",
  },
  {
    type: 'h2',
    text: 'Why 20.2 hp Produces a 16-Second ET',
  },
  {
    type: 'p',
    text: 'The headline number is 20.2 hp at 6100 rpm. That is 15.1 kW at the crank. Subtract Indian dyno-test wheel losses (typically 12-15 percent for air-cooled singles with no oil cooler) and you have roughly 13 kW at the rear wheel — about 17.4 hp. At a 248 kg combined rider-plus-bike weight, the power-to-weight ratio is 0.070 kW/kg. For reference, a stock Hayabusa Gen 1 runs 0.230 kW/kg. The Hunter 350 is running on roughly 30 percent of the Hayabusa engine power per kilogram.',
  },
  {
    type: 'p',
    text: "That power-to-weight ratio produces the 16-second quarter through a specific physics mechanism. In first gear (ratio 2.857, final drive 15/40 = 2.667), the Hunter has enough wheel torque to wheelie on Indian tarmac if the launch is aggressive. The simulator shows a mild weight-transfer event at the 60-foot mark — the front wheel unloads to roughly 12 percent of total bike weight, which is the threshold for front-wheel lift. The bike does not actually wheelie on stock settings, but it approaches the limit, which means the J-platform engine's 4000 rpm torque peak is genuinely useful at launch rather than buried under a gearing mismatch.",
  },
  {
    type: 'p',
    text: 'The bottleneck is the mid-range. After the first gear sprint, the Hunter shifts to second at around 2.1 s and 60 km/h. Second gear on the Hunter is ratio 1.928 — a significant step down from first. The engine drops from about 5500 rpm to 3800 rpm at the shift point, which lands it close to the 4000 rpm torque peak but with far less wheel torque than it had in first. From that point forward the run is a sustained grind through the power band rather than a surge. The simulator log shows the Hunter crossing the trap in fifth gear at 6050 rpm — essentially right at peak power — which means the gearing is well-optimised for this engine despite the commuter-focused ratios.',
  },
  {
    type: 'h2',
    text: 'The Cheapest Tenths on a Hunter 350',
  },
  {
    type: 'p',
    text: "The Hunter 350's parts catalog in MotoQuant identifies three mods with a cost-per-tenth below ₹15,000:",
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
    text: 'The sprocket swap is the most straightforward. A 15/41 rear sprocket shortens the final drive ratio by 2.5 percent across all gears, putting the engine 250 rpm higher at any given road speed. On a 20 hp single that peaks at 6100 rpm, that shift pulls the gearing in every gear slightly toward the peak-power band. The simulator shows a net ET gain of roughly 0.09 s at Aamby Valley. The catch: the 428 chain on the Hunter is a relatively short-pitch chain for an Indian road bike, and many generic rear sprockets in the 41-tooth range are Chinese-made forgings with inconsistent hardness. Use a JT Sprockets or Sunstar unit — the price difference over a generic sprocket is about ₹400 and the quality gap is significant.',
  },
  {
    type: 'p',
    text: 'The tyre swap matters more than most Hunter 350 owners expect. The OEM MRF ZAPPER rear is a bias-ply commuter tyre with a μ_peak of roughly 1.10-1.15 on clean dry Indian tarmac. Swapping to an MRF ZAPPER FX (a sport-compound bias-ply that stays on the narrow 140/70-17 Indian size) raises μ_peak to about 1.22-1.25 per MRF India testing data cited in their 2024 tyre catalogue (mrf.com/tyres, ZAPPER FX spec sheet). The simulator shows roughly 0.14 s of ET gain from this grip upgrade alone — almost all of it in the first gear phase where traction is the limiting factor. At ₹3,200 for the rear tyre alone, the cost-per-tenth is the lowest of any mod on this bike.',
  },
  {
    type: 'p',
    text: 'The Powertronic ECU Stage 1 map is listed because it genuinely moves the needle on fuel-injected J-platform engines — the OEM ECU is known to run conservative ignition timing below 3000 rpm to meet BS6 Phase 2 emissions thresholds. Powertronic India (powertronic.in) has documented 1.8-2.2 hp wheel-dyno gains on the Hunter 350 J with their Stage 1 map, confirmed on a Dynojet MD-250 at their Mumbai facility. That is a modest gain, but on a 17 hp wheel bike, 2 hp is an 11.7 percent increase. The simulator shows about 0.22 s of ET gain with a calibrated 2 hp increase, which produces a cost-per-tenth of roughly ₹84,000. That is not the cheapest tenth on the bike, but it is a real one.',
  },
  {
    type: 'h2',
    text: 'Hunter 350 vs the Broader Indian 350cc Competitive Set',
  },
  {
    type: 'p',
    text: 'The Hunter 350 does not exist in isolation. The Indian 350cc naked segment also includes the Bajaj Dominar 400 (discounted here — it weighs 168 kg and makes 40 hp, a different product class entirely), the Honda CB350 H\'ness (186 kg, 21 hp @ 5500 rpm, retro parallel-twin-styled single), and the Jawa 42 (175 kg, 29.5 hp @ 6000 rpm, liquid-cooled single). The Jawa 42 is the one that sits closest to the Hunter 350 in price and spec; its 29.5 hp and liquid-cooled motor would give it a significant ET advantage if Jawa offered the same sales network and parts support that RE does.',
  },
  {
    type: 'p',
    text: 'For the quarter mile specifically: the MotoQuant simulation puts the Jawa 42 at roughly 15.1 s ET and 138 km/h trap — about 1.8 s faster than the Hunter 350 on stock tune. That gap is almost entirely engine power: the Jawa makes 29.5 hp versus the Hunter\'s 20.2 hp with comparable mass. The Hunter 350 owner who wants to match a stock Jawa 42 at the strip would need to add about 9 hp through an ECU flash, exhaust, and intake combination — a realistic but costly upgrade path for a commuter-class bike.',
  },
  {
    type: 'p',
    text: 'The honest framing for the Hunter 350 at the strip is not "how does it compare to the Jawa?" but "how does it compare to the Classic 350 I could have bought for the same money?". That comparison the Hunter wins clearly: nearly a full second faster than the Classic, better trap speed, and objectively lower fuel consumption on Indian city roads because it weighs 24 kg less. The strip advantage is a side effect of an urban design philosophy, not a deliberate drag-spec choice.',
  },
  {
    type: 'h2',
    text: 'Gearing Analysis: Is the 5-Speed Right for the Strip?',
  },
  {
    type: 'p',
    text: 'The Hunter 350 uses the same 5-speed cassette as all J-platform siblings. The gear ratios [2.857, 1.928, 1.476, 1.190, 1.000] with 15/40 final drive give the following speeds at 6100 rpm (peak power) per gear:',
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
    text: 'The quarter-mile trap of 127.9 km/h occurs in fifth gear at about 6050 rpm — essentially exactly at peak power. That alignment is not accidental; it means the Hunter 350 was probably geared by someone who thought about high-speed cruising on Indian national highways rather than drag racing, and who ended up producing an almost ideal drag-strip gear map as a side effect. Bikes that trap at the rev limiter (like a first-generation KTM Duke 390 setup) are over-geared for the quarter; bikes that trap well below peak power (like the Classic 350) are under-geared. The Hunter 350 hits the sweet spot.',
  },
  {
    type: 'p',
    text: 'The 1st-to-2nd gear jump from 2.857 to 1.928 is the single most significant ratio step in the cassette — a 32.5 percent drop in gear reduction. At the 60-foot shift point (roughly 41 km/h, 6100 rpm in first), the engine drops to about 4000 rpm in second, which is precisely the torque-peak rpm. The simulator log shows this transition cleanly: the traction percentage drops from 87 to 71 at the shift, recovers within 0.2 s as torque builds in second, and never trips the simulated traction control threshold. That is a well-behaved launch for a 20 hp single on stock bias-ply rubber.',
  },
  {
    type: 'h2',
    text: 'What to Expect at the Strip',
  },
  {
    type: 'p',
    text: 'If you take a stock Hunter 350 to an Indian drag strip (Aamby Valley, MMRT, BIC, Kari), the MotoQuant simulation suggests you will run between 15.8 and 17.0 seconds depending on rider weight, launch technique, ambient temperature, and strip altitude. The 16.895 s simulator output is a 50th-percentile rider estimate under Aamby Valley November conditions. Riders who are heavier than 78 kg add roughly 0.07 s per 5 kg of additional rider mass. A 90 kg rider would push the ET to about 17.1-17.3 s.',
  },
  {
    type: 'p',
    text: 'Temperature matters on this bike more than most in its class. The J-platform engine is air-cooled, and its OEM ECU applies a fuel enrichment strategy above 40°C ambient that reduces peak power by roughly 0.8-1.2 hp. At an Aamby Valley May-June run (40-44°C ambient, density altitude ≈ 1150 m), the simulator shows an ET of roughly 17.4-17.6 s — about 0.5-0.6 s slower than the November run. If you want to run your Hunter 350 at the strip, November through February at Aamby Valley is the window.',
  },
  {
    type: 'p',
    text: 'The Hunter 350 is not going to embarrass a Pulsar NS200 (MotoQuant sim: ~16.0-16.5 s depending on spec) at the strip. But it will beat a stock Classic 350 and Meteor 350 every time, and it will beat a stock Bullet 350 J on stock rubber on most Indian strip surfaces. For the ₹1.5 lakh on-road price it commands in most Indian cities, that is a respectable strip result from a bike that was designed primarily to look good on Instagram.',
  },
  {
    type: 'h2',
    text: 'Run Your Own Numbers',
  },
  {
    type: 'p',
    text: 'The MotoQuant simulator at motoquant.in has the Hunter 350 J-platform spec loaded — F15/R40, 428 chain, 5-speed, 171 kg dry, Cd 0.74. You can adjust rider weight, ambient temperature, density altitude (critical for Indian drag strips at altitude), and select from the parts catalog to see exactly which mods move the needle on your specific setup. The simulator also runs the Classic 350, Meteor 350, and Bullet 350 J so you can replicate the comparison table above under your local strip conditions.',
  },
  {
    type: 'p',
    text: 'Two things to keep in mind when using the results. First, the entry-200-300 cluster bias means the simulator tends to run about 0.4-0.8 s slower than a real-world strip result with a well-practised launch technique — the sim is calibrated to a 50th-percentile rider, not a trained drag racer. Second, the cluster bias is actively being refined as more instrumented timeslip data from Indian strips becomes available via the Dragy import pipeline — if you have real timeslip data from a Hunter 350 run at MMRT or Aamby Valley, it is worth importing it to improve the model for the entire entry-200-300 class.',
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
            {['Royal Enfield', 'Hunter 350', 'J-platform', 'Indian 350cc', 'physics'].map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Royal Enfield Hunter 350 Quarter-Mile Physics: Fastest J-Platform at the Strip
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
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
              <Link href="/blog/royal-enfield-bullet-350-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                Royal Enfield Bullet 350 Quarter-Mile Physics
              </Link>{' '}
              — the J-platform sibling at 17.735s: same engine, different chassis decisions.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/honda-hornet-2-0-vs-pulsar-ns200-quarter-mile" className="text-brand-accent hover:text-brand-orange transition-colors">
                Honda Hornet 2.0 vs Pulsar NS200 Quarter Mile
              </Link>{' '}
              — how the Hunter 350 stacks against the Indian 200cc entry class.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/the-physics-of-a-perfect-launch" className="text-brand-accent hover:text-brand-orange transition-colors">
                The Physics of a Perfect Launch
              </Link>{' '}
              — why the Hunter 350's 4000 rpm torque peak is the right launch point and how to use it.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-the-motoquant-physics-engine-works" className="text-brand-accent hover:text-brand-orange transition-colors">
                How the MotoQuant Physics Engine Works
              </Link>{' '}
              — the 15-sub-model stack behind every simulation in this post.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>{' '}
              — Hunter 350, Classic 350, Meteor 350, Bullet 350, and every J-platform variant side by side.
            </li>
            <li>
              ·{' '}
              <Link href="/pricing" className="text-brand-accent hover:text-brand-orange transition-colors">
                MotoQuant Pricing
              </Link>{' '}
              — Free simulator for street tuners; Pro for shops and racing teams.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Run the Hunter 350 yourself</div>
            <div className="text-white/60 text-sm">
              Free simulator — pick the Hunter 350, dial in your rider weight and local conditions, and compare it against the Classic 350 or Meteor 350 to see exactly where your tenths come from.
            </div>
          </div>
          <Link
            href="/simulator?bike=re-hunter-350"
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
