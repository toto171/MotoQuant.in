import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema, OG_IMAGE } from '../../StructuredData';
import PostBikeLinks from '../../../components/PostBikeLinks';

const SLUG = 'harley-nightster-rh975-quarter-mile-physics';
const TITLE = 'Harley Nightster RH975: Revolution Max quarter-mile physics';
const DESCRIPTION =
  'MotoQuant simulates the Harley Nightster RH975 at 12.38s; Cycle World clocked 11.99s at 110.4 mph. Where the gap comes from, and what it means in India.';

export const metadata = {
  title: 'Harley Nightster RH975 quarter-mile physics',
  description: DESCRIPTION,
  keywords: [
    'harley davidson nightster rh975 quarter mile',
    'nightster rh975 drag time',
    'nightster 975 quarter mile india',
    'harley nightster 975 0-100',
    'revolution max 975t drag',
    'nightster vs sportster s drag race',
    'nightster rh975 vs street triple',
    'harley davidson india drag racing',
    'revolution max 975 quarter mile time',
    'nightster india price quarter mile',
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
    text: 'Cycle World\'s 2022 instrumented test put the Harley-Davidson Nightster RH975 through the quarter mile in 11.99 seconds at 110.4 mph. That makes a stock Nightster quicker than a Triumph Street Triple 765 R on the drag strip, and within tenths of a Kawasaki Ninja 650. The Revolution Max 975T V-twin is not the slow cruiser engine most people take it for. MotoQuant simulates the Nightster at 12.38 seconds, 0.39 seconds off the Cycle World figure and inside the cruiser cluster\'s documented bias band. Here is why a 90 hp belt-drive Harley runs an 11.x.',
  },
  {
    type: 'h2',
    text: 'The Revolution Max 975T: a different kind of V-twin',
  },
  {
    type: 'p',
    text: 'Harley-Davidson introduced the Revolution Max platform in 2021 with the Pan America adventure bike. The Nightster followed in 2022 as the first dedicated street model built around the smaller 975cc version. The engine is a clear break from the Milwaukee-Eight and Twin Cam V-twins that built Harley\'s name: the Revolution Max 975T is a liquid-cooled 60° V-twin with DOHC, 4 valves per cylinder, variable valve timing and a counterbalancer shaft. On paper it looks more like a Ducati V-twin than a traditional Harley pushrod engine.',
  },
  {
    type: 'p',
    text: 'Peak power is 90 hp at 7,500 rpm and peak torque is 95 Nm at 5,000 rpm. The torque peak comes 2,500 rpm before the power peak, which gives a broad curve built for real-world riding rather than a narrow RPM spike. The 60° vee and the counterbalancer give a much smoother idle than the traditional 45° big V-twins, and variable valve timing spreads usable power across a wider RPM range than fixed cams would.',
  },
  {
    type: 'p',
    text: 'The final drive is a belt: a 24-tooth front pulley and a 68-tooth rear, an overall ratio on the tall side for drag use. A belt does not stretch or wear sprockets, but a Nightster owner cannot simply drop a tooth at the front the way a chain-drive owner can. The belt ratio fixes the gearing. The only change available is the rear pulley, which takes more work and money than a sprocket swap.',
  },
  {
    type: 'h2',
    text: 'Spec card: Nightster RH975 vs the 600cc middleweight benchmark',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'Nightster RH975 (2022+)', 'Triumph Street Triple 765 R (2023)', 'Kawasaki Ninja 650 (2023)'],
      ['Displacement', '975 cc', '765 cc', '649 cc'],
      ['Engine type', 'LC DOHC 60° V-twin', 'LC DOHC inline-triple', 'LC DOHC parallel-twin'],
      ['Peak power', '90 hp @ 7,500 rpm', '118 hp @ 11,700 rpm', '68 hp @ 8,000 rpm'],
      ['Peak torque', '95 Nm @ 5,000 rpm', '79 Nm @ 9,350 rpm', '64 Nm @ 6,700 rpm'],
      ['Dry mass', '212 kg', '166 kg', '193 kg'],
      ['Gears', '6-speed', '6-speed', '6-speed'],
      ['Final drive', 'Belt 24F/68R', 'Chain 17F/41R 520', 'Chain 14F/43R 520'],
      ['Cd', '0.88 (upright cruiser)', '0.72 (naked sport)', '0.80 (naked sport)'],
      ['Frontal area', '0.52 m²', '0.44 m²', '0.46 m²'],
      ['Cycle World / MCN ET', '11.99 s @ 110.4 mph', '10.9 s @ ~132 mph', '~13.4 s'],
      ['MotoQuant sim ET', '12.38 s @ 181.8 km/h', '10.74 s @ 213 km/h', 'N/A in this post'],
    ],
  },
  {
    type: 'p',
    text: 'The column that matters is the Street Triple 765 R. The Triumph makes 28 hp more, weighs 46 kg less, and has a sport-naked aero package with a much smaller frontal area. It costs more in most markets, and it beats the Nightster by roughly 1.7-1.9 seconds of ET. With 67 percent of the Triumph\'s peak power and 128 percent of its mass, the Nightster still runs within two seconds of a bike most riders would call quick. That is the case for taking the Revolution Max 975T seriously at the strip.',
  },
  {
    type: 'h2',
    text: 'Sim vs Cycle World: the 0.39-second gap',
  },
  {
    type: 'p',
    text: 'MotoQuant simulates the stock Nightster RH975 at 12.377 seconds with a 181.8 km/h (113.0 mph) trap. Cycle World clocked 11.99 seconds at 110.4 mph (177.6 km/h) in its 2022 instrumented test, under California conditions. The gap is 0.39 seconds of ET and 4.2 km/h (2.6 mph) of trap speed.',
  },
  {
    type: 'callout',
    text: 'The trap-speed inversion is a known signature of the cruiser cluster\'s bias: MotoQuant simulates a higher trap speed than Cycle World recorded (181.8 km/h vs 177.6 km/h) but a slower ET (12.38 s vs 11.99 s). The simulated bike reaches the 402 m mark on a slower path overall, at a similar terminal speed. The most likely cause is the launch: the model\'s clutch engagement is more conservative than what Cycle World\'s test rider managed. Cycle World uses professional riders making optimal launches. The simulator uses a stock launch-RPM profile with no manual optimisation.',
  },
  {
    type: 'p',
    text: 'For context, MotoQuant\'s cruiser-1300+ cluster (the Nightster sits next to it as a large V-twin) has a documented mean absolute error of 0.407 seconds and a positive bias of 0.407 seconds, meaning the simulator runs slower than reality. The Nightster\'s 0.39-second gap is inside that range. It is not a physics error specific to the Nightster. It comes from the general difficulty of modelling the launch on heavy bikes with belt drives and tall final gearing.',
  },
  {
    type: 'p',
    text: 'MotoQuant\'s full splits: 60-foot at 2.295 seconds, 330-foot at 5.498 seconds, 1/8-mile at 8.116 seconds and 152.2 km/h, 1,000-foot at 10.405 seconds. A real Nightster with an optimal launch typically runs the 60-foot in roughly 2.05-2.10 seconds. That accounts for roughly half the gap: the simulator\'s clutch engagement is conservative and loses about 0.2 seconds in the first 60 feet.',
  },
  {
    type: 'h2',
    text: 'Why the Nightster runs an 11.x: the V-twin physics',
  },
  {
    type: 'p',
    text: 'Three things make the Nightster quicker than its paper power-to-weight ratio suggests.',
  },
  {
    type: 'p',
    text: 'First, the shape of the torque curve. Peak torque arrives at 5,000 rpm, so in most situations the Nightster is well into its power band before first gear becomes power-limited. Early in a quarter-mile run, while gearing is the limit, a bike with strong torque at 4,000-6,000 rpm uses its power better than a high-revving engine that makes peak power only at 10,000 rpm. The Nightster is not traction-limited at launch the way a 100+ hp sport bike is. On dry pavement it pulls from launch RPM to redline in first gear without much wheel slip.',
  },
  {
    type: 'p',
    text: 'Second, displacement. 975 cc makes torque more easily than 765 cc. The Street Triple 765 R has to rev to 9,350 rpm to match the Nightster\'s 95 Nm peak torque; the Nightster is at that level from roughly 3,500 rpm up. In a drag run, a wider torque plateau keeps the bike in a high-torque state across more gear ratios and engine speeds, so the gearing does not need to be as short to keep the engine in its useful range.',
  },
  {
    type: 'p',
    text: 'Third, the weight is large but does less damage to ET than it seems. At 212 kg dry, the Nightster\'s power-to-weight ratio is approximately 68 hp per tonne (using 90 hp and 132 kg total: bike dry mass plus approximate fuel and a 70 kg rider). The Street Triple 765 R at 166 kg dry works out to approximately 115 hp per tonne on the same calculation. The Triumph beats the Nightster by 1.7-1.9 seconds because of that big power-to-weight advantage, not because of the Nightster\'s weight on its own. A bike that runs 11.99 seconds on 68 hp per tonne is well sorted.',
  },
  {
    type: 'h2',
    text: 'Belt drive at the strip: what it costs you',
  },
  {
    type: 'p',
    text: 'A belt loses more power than a well-maintained chain. Harley-Davidson\'s belt system loses roughly 2-3 percent in the drivetrain, against a typical 1.5-2 percent for a chain in good condition. At 90 hp at the crank, the difference is approximately 0.5-1.5 hp at the wheel: small, but measurable.',
  },
  {
    type: 'p',
    text: 'The bigger problem for drag racing is the fixed gearing. A chain-drive owner can change sprockets for ₹900-3,000 and gain 0.15-0.25 seconds of ET by matching the drive ratio to the quarter mile. On the Nightster the choice is a different rear pulley (a bigger job, typically ₹8,000-15,000 in India including labour) or living with the stock gearing. The stock 24F/68R gives an overall first-gear ratio suited to street riding (moderate, not aggressive), and the bike goes through all six gears before the 402 m mark.',
  },
  {
    type: 'p',
    text: 'In MotoQuant\'s split data, the Nightster has used all six gears by the time it crosses the quarter-mile. A well-set-up drag bike at this power level would ideally be in 3rd or 4th at the 402 m mark, getting the most from each gear. The Nightster\'s tall gearing forces it through the whole cassette, and it loses engine efficiency at every shift. This is the main mechanical reason MotoQuant\'s sim ET is 0.39 seconds slower than the Cycle World benchmark. The model\'s launch RPM and clutch engagement are conservative, but the gearing analysis is correct.',
  },
  {
    type: 'h2',
    text: 'Which mods help on a Nightster',
  },
  {
    type: 'p',
    text: 'Dedicated drag parts for the Nightster are scarce in India. The bike costs approximately ₹15.5-16.5 lakh ex-showroom, and its buyers mostly care about street and touring use, not strip times. The parts on offer reflect that. There are realistic options, but the cost-per-tenth ladder looks different from a Pulsar NS200\'s or an RC 390\'s.',
  },
  {
    type: 'table',
    rows: [
      ['Mod', 'Estimated ΔET', 'Approx. Indian price', '₹ per tenth'],
      ['Slip-on exhaust (Vance & Hines / Cobra)', '~0.08 s', '₹35,000–55,000', '₹4.4 lakh–6.9 lakh per tenth'],
      ['ECU re-flash (Dynojet PCV + Autotune)', '~0.10 s', '₹22,500–38,000', '₹2.25 lakh–3.8 lakh per tenth'],
      ['Rear pulley swap (shorter ratio, custom)', '~0.18 s', '₹12,000–20,000 (parts + labour)', '₹67,000–1.1 lakh per tenth'],
      ['Rider mass reduction: −10 kg', '~0.06 s', '–', '–'],
      ['Sport tire (front: 100/80ZR17, rear: 150/70ZR17)', '~0.07 s', '₹8,000–14,000', '₹1.1 lakh–2.0 lakh per tenth'],
    ],
  },
  {
    type: 'p',
    text: 'The Nightster\'s cost per tenth is much worse than on Indian commuter bikes or even most 600cc middleweights. The parts are not the problem; the ECU flash and exhaust are real improvements. The cause is the starting point. At 11.99-12.38 seconds stock, bolt-on mods gain less in percentage terms than on a 14-17 second commuter, and the parts are priced for the premium cruiser segment rather than the performance segment.',
  },
  {
    type: 'p',
    text: 'The rear pulley swap is the best-value drag modification on the Nightster. Going from a 68T to a 62T rear pulley shortens overall gearing by approximately 9 percent, which keeps the engine nearer its peak torque band through more of each gear. MotoQuant\'s model suggests this would recover roughly 0.15-0.20 seconds, enough to put a well-launched Nightster solidly in the 11.7-11.8 second range.',
  },
  {
    type: 'p',
    text: 'Harley-Davidson tuning specialists in Bangalore and Mumbai can supply custom rear pulleys. Expect to source the pulley from the US at approximately ₹12,000-15,000, plus ₹3,000-5,000 for belt-length matching and fitting.',
  },
  {
    type: 'callout',
    text: 'The belt drive is the biggest structural limit on drag tuning a Nightster. Every other performance bike at its price has a chain, so a ₹900-3,000 sprocket swap lets you try different gearing quickly. The Nightster needs a pulley swap that costs 10-20x more and cannot be undone in an afternoon. If strip performance is your main goal, that is the trade-off you accept with the Harley.',
  },
  {
    type: 'h2',
    text: 'Nightster vs Sportster S: the obvious comparison',
  },
  {
    type: 'p',
    text: 'Harley-Davidson sells the Sportster S RH1250S alongside the Nightster. It uses the larger Revolution Max 1250T engine (121 hp, 127 Nm) with the same belt drive. The Sportster S weighs approximately 228 kg wet, about 10-15 kg more than the Nightster in comparable trim. Power-to-weight is roughly 83 hp per tonne for the Sportster S against the Nightster\'s 68 hp per tonne.',
  },
  {
    type: 'p',
    text: 'Cycle World tested the Sportster S in 2021 and recorded a 12.05 second quarter mile, almost the same as the Nightster\'s 11.99 seconds. Its extra 31 hp and 32 Nm are partly cancelled out by its extra mass and taller overall gearing. Under controlled conditions, the smaller-engined Nightster matches the Sportster S at the strip.',
  },
  {
    type: 'p',
    text: 'That is a surprising result. In India the Nightster costs roughly ₹3-4 lakh less, and it is lighter, narrower and easier to ride in traffic. At the drag strip it posts the same time as the flagship of its family. The Revolution Max 975T suits the bike\'s weight and gearing that well, which says something about how efficient the smaller engine package is next to the 1250T in the heavier Sportster S chassis.',
  },
  {
    type: 'p',
    text: 'A separate post covers the full Nightster vs Sportster S physics: how each engine launches, the two torque curves at matched RPM, and the gearing changes for both. In short, if strip performance is what you care about most, the stock Nightster is the better pick of the two.',
  },
  {
    type: 'h2',
    text: 'The Indian market',
  },
  {
    type: 'p',
    text: 'The Nightster arrived in India in 2022 at approximately ₹15.5 lakh ex-showroom, above the Royal Enfield Super Meteor 650 and below the Triumph Bonneville T120. In Indian performance terms, that money buys much more quarter-mile performance in a KTM 890 Duke R (11.07 s, ₹11-12 lakh via grey market) or a BMW S 1000 R (sub-10 s, ₹22 lakh).',
  },
  {
    type: 'p',
    text: 'Indian buyers do not choose the Nightster because it is the fastest bike at its price. They choose it for the style, the sound, the riding position and the Revolution Max\'s mechanical character, and all of those are real.',
  },
  {
    type: 'p',
    text: 'At an Indian drag strip, the Nightster will comfortably beat any stock Indian 650cc twin (the RE Continental GT 650 runs approximately 14.1 seconds, the RE Interceptor 650 about the same), any 400cc Indian bike (RC 390 at approximately 13.5 seconds), and most stock 600cc sport bikes from the used market. It competes directly with a stock Kawasaki Ninja 650 (approximately 13.4 seconds), MT-07-class bikes and the lower end of the litre-class naked segment.',
  },
  {
    type: 'p',
    text: 'At an Aamby Valley strip meet, a stock Nightster with a competent rider making consistent launches will beat most of the Indian bikes in the paddock. That surprises most people, who think of Harley-Davidson as slow, heavy touring bikes. The Revolution Max 975T changed that.',
  },
  {
    type: 'h2',
    text: 'Simulate it yourself',
  },
  {
    type: 'p',
    text: 'MotoQuant\'s 12.38 seconds is the physics prediction with a conservative launch and stock tune. Cycle World\'s 11.99 seconds is an instrumented benchmark from a professional rider making optimal launches at sea level in California. Launch technique accounts for almost all of the 0.39-second gap. The Nightster\'s belt drive and V-twin character let a rider launch hard without much wheel spin, so a competent rider can reliably beat the sim\'s conservative launch model.',
  },
  {
    type: 'p',
    text: 'If you own a Nightster and a Dragy GPS timer, upload a run in the simulator to compare it with the simulation split by split; the file is compared and then deleted, not kept. To help improve the model, send the run through the "Submit a timeslip" form; a reviewed run joins the benchmark set. The Nightster is a good candidate because its belt drive fixes the gearing, so there is no sprocket variation to account for.',
  },
  {
    type: 'p',
    text: 'The simulator at motoquant.in has the Nightster RH975 loaded with its full spec, including the Revolution Max 975T torque curve, 24F/68R belt gearing and 212 kg dry mass. You can change venue conditions (Aamby Valley November at 1,100 m density altitude, or MMRT Chennai near sea level at 30°C), rider weight and the limited mod catalog to see what a rear pulley swap or ECU flash buys in seconds at your home strip.',
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
          <div className="flex flex-wrap gap-2 mb-6">
            {['Harley-Davidson', 'Nightster RH975', 'Revolution Max', 'cruiser', 'V-twin', 'physics'].map((t) => (
              <span
                key={t}
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Harley Nightster RH975: Revolution Max quarter-mile physics
          </h1>
          <div className="text-sm text-white/60 mb-12">
            25 May 2026 · 11 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        <PostBikeLinks ids={[722]} />

        <div className="max-w-2xl mx-auto mt-16 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Simulate the Nightster RH975</div>
            <div className="text-white/60 text-sm">Load the Nightster at Aamby Valley or MMRT Chennai, change rider weight and conditions, and model the rear pulley swap or ECU flash before spending ₹15,000–55,000 on mods.</div>
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
              <Link href="/blog/triumph-street-triple-765r-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                Triumph Street Triple 765 R quarter-mile physics
              </Link>
              : the Nightster's nearest rival in the 11-12 second range, built a completely different way: a 118 hp inline-three at ₹10.67 lakh that beats the Nightster by ~1.75 s and costs less.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/kawasaki-z900rs-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                Kawasaki Z900RS quarter-mile physics
              </Link>
              : another premium naked in the 11-second range, a retro 948cc inline-four that sims at 11.18 s. The Z900RS and the Nightster are natural strip rivals at similar Indian CBU prices.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-the-motoquant-physics-engine-works" className="text-brand-accent hover:text-brand-orange transition-colors">
                How the MotoQuant physics engine works
              </Link>
              : the full method behind the 12.38 s prediction: clutch model, belt-drive efficiency, V-twin torque curve synthesis, and why the cruiser cluster has a +0.4 s bias.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/the-physics-of-a-perfect-launch" className="text-brand-accent hover:text-brand-orange transition-colors">
                The physics of a perfect launch
              </Link>
              : most of the Nightster's 0.39 s gap to Cycle World's benchmark is in the first 60 feet. Clutch engagement RPM, weight transfer, and slip ratio on a 212 kg V-twin.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>
              : Harley-Davidson Nightster RH975, Sportster S RH1250S, and 350+ other bikes with full spec sheets and OEM tire fitments.
            </li>
          </ul>
        </div>
      </article>

      <SiteFooter />
    </div>
  );
}
