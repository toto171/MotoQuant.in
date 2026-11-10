import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'yamaha-rd350-quarter-mile-physics';
const TITLE = 'Yamaha RD350 quarter-mile physics: why a 1973 2-stroke still runs 14.7s';
const DESCRIPTION =
  'MotoQuant sims the 1973 Yamaha RD350 at 14.707s and a 145 km/h trap under Aamby Valley November conditions, quicker than a stock Pulsar NS200, Pulsar 220F or Hunter 350 in 2026. Cycle World clocked the real bike at 14.000s in 1973. Where the 0.7s sim residual comes from, what the Indian Rajdoot RD350 HT actually delivered, and why a 39hp piston-port twin still beats modern 200cc commuters.';

export const metadata = {
  title: 'Yamaha RD350 quarter-mile time (1973) | MotoQuant',
  description: DESCRIPTION,
  keywords: [
    'yamaha rd350 quarter mile',
    'rd350 drag time',
    'rajdoot rd350 quarter mile',
    'rd350 ht specifications',
    'rd350 vs pulsar ns200',
    'rd350 0-100',
    'yamaha rd350 top speed',
    'rd350 sim time',
    'two stroke drag racing india',
    'rd350 vs hunter 350',
    'rd350 vs r15 v4',
    'fastest indian 2-stroke',
    'rd350 physics',
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `https://motoquant.in/blog/${SLUG}`,
    type: 'article',
    publishedTime: '2026-05-31T00:00:00Z',
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: 'MotoQuant simulates the 1973 Yamaha RD350 at 14.707 seconds and about 145 km/h trap under Aamby Valley November conditions. Cycle World clocked the real bike at 14.000 seconds in 1973, on prepped strip rubber with a trained tester. Fifty-three years later, a 39 hp air-cooled twin that costs less than a used Honda Activa still runs a quicker stock quarter mile than the Pulsar NS200, the Pulsar 220F, the Royal Enfield Hunter 350 or any J-platform single sold in India today.',
  },
  {
    type: 'h2',
    text: 'The stock numbers',
  },
  {
    type: 'p',
    text: 'The Yamaha RD350 was sold globally from 1973 to 1975 as a 347 cc air-cooled parallel-twin two-stroke. Bore 64 mm, stroke 54 mm, compression 6.6:1, two 28 mm Mikuni VM carburettors, piston-port induction. Yamaha rated the export model at 39 hp at 7500 rpm and 36 Nm at 6500 rpm. Dry mass 155 kg, wheelbase 1320 mm. The gearbox is a 6-speed with ratios [2.461, 1.555, 1.190, 0.961, 0.821, 0.740], final drive 16/37 on 520 chain. Sources for every spec: Yamaha 1973 RD350 service manual (catalog 352), Cycle World December 1973 instrumented test, and the MotorBikeCatalog 352-series database cross-checked against three independent forum threads.',
  },
  {
    type: 'p',
    text: 'Under Aamby Valley November conditions (22°C ambient, 40% RH, 679 m elevation, asphalt strip), MotoQuant runs the simulation through 15 physics sub-models including the new 2-stroke clutch-engagement model that shipped in the May 31 2026 calibration pass. The result, with a 78 kg rider:',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'Value', 'Source'],
      ['Quarter-mile ET', '14.707 s', 'MotoQuant sim'],
      ['Trap speed', '~145 km/h', 'MotoQuant sim'],
      ['60-foot time', '2.512 s', 'MotoQuant sim'],
      ['1/8-mile ET', '9.51 s @ 124 km/h', 'MotoQuant sim'],
      ['Cycle World 1973 ET', '14.000 s', 'Cycle World Dec 1973'],
      ['Sim residual (cluster)', '+0.707 s slow', 'Documented two_stroke cluster bias band'],
      ['Peak hp (crank)', '39 @ 7500 rpm', 'Yamaha 1973 service manual'],
      ['Peak torque', '36 Nm @ 6500 rpm', 'Yamaha 1973 service manual'],
      ['Dry mass', '155 kg', 'Yamaha 1973 service manual'],
      ['Cd', '0.62', 'MotoQuant aero estimate, naked-sport class'],
      ['Frontal area', '0.50 m²', 'MotoQuant aero estimate, naked-sport class'],
    ],
  },
  {
    type: 'p',
    text: 'The sim runs 0.707 s slower than the Cycle World benchmark. The gap is documented, and it shrank by 0.347 s in the calibration that shipped today; before that, the same configuration ran 15.054 s. Across all five validated 2-stroke bikes in the catalog (RD350, RD400, NSR250R, RG500 Gamma, RS250), the cluster mean absolute delta is currently 0.630 s with a +0.169 s bias. So the cluster reads slow against instrumented magazine tests.',
  },
  {
    type: 'callout',
    text: 'Why the residual is not zero: there is no clean closed-form physics model for 2-stroke crank deceleration during clutch engagement. MotoQuant caps the rate at max_engine_decel_rads2 = 1500 rad/s² (raised today from 800), which matches the Honda HRC NSR250 service-manual figure of ~10000 rpm/s peak transient. Real drag launches depend on rider technique (clutch slip duration, throttle modulation, body position), which the simulator approximates with a parametric model. Cycle World used a trained drag tester on prepped Goodyear DT slicks; the sim uses OEM-class tyre μ. Both numbers are useful, and neither is wrong.',
  },
  {
    type: 'h2',
    text: 'Why 39 horsepower beats modern 200cc commuters',
  },
  {
    type: 'p',
    text: 'A 2026 Bajaj Pulsar NS200 makes 24.5 hp at 9750 rpm from a 199.5 cc liquid-cooled DOHC single. A 2026 Honda Hornet 2.0 makes 17.3 hp from a 184 cc air-cooled single. A 2026 Yamaha R15 V4 makes 18.4 hp from a 155 cc liquid-cooled VVA single. The Royal Enfield Hunter 350 makes 20.2 hp from a 349 cc air-cooled SOHC single. The RD350 makes 39 hp from a 347 cc air-cooled piston-port twin: roughly 60 percent more power than the quickest of those moderns, on similar mass, with a far smaller frontal area than any RE 350.',
  },
  {
    type: 'p',
    text: 'Specific output shows where the engineering stood. The RD350 makes 112 hp per litre, the Pulsar NS200 123 and the R15 V4 119. None of the modern commuters is far ahead of the 1973 piston-port twin on that measure. The RD350 was already at the ceiling of what a mass-production, naturally aspirated 2-stroke could deliver in 1973 with carburettors and a fixed expansion chamber. The 4-stroke commuter class caught up to that specific output around 2010, with the first generation of liquid-cooled DOHC singles. The RD350 was there fifty years earlier.',
  },
  {
    type: 'table',
    rows: [
      ['Bike', 'Year', 'Peak hp', 'Dry mass', 'Sim ET', 'Sim trap'],
      ['Yamaha RD350', '1973', '39 hp', '155 kg', '14.707 s', '~145 km/h'],
      ['Yamaha RD400 Daytona', '1976', '44 hp', '161 kg', '14.157 s', '~152 km/h'],
      ['Pulsar NS200', '2025', '24.5 hp', '156 kg', '~16.05 s', '~120 km/h'],
      ['Hunter 350', '2025', '20.2 hp', '171 kg', '16.895 s', '~128 km/h'],
      ['R15 V4', '2024', '18.4 hp', '142 kg', '~16.5 s', '~125 km/h'],
      ['CB350 Hness', '2025', '21 hp', '186 kg', '~16.8 s', '~118 km/h'],
    ],
  },
  {
    type: 'p',
    text: 'Almost all of the 1.3 to 2.2 second gap between the RD350 and any modern Indian 200-350cc commuter is engine power. The chassis mass band is the same, so is the 17-inch rear wheel, and tyre grip and gearing are similar. The 2-stroke twin simply makes much more torque across a usable rev band, and sends it to the rear wheel through a 6-speed gearbox geared to suit the engine\'s specific output. Even the RD400 Daytona, three years newer and 6 hp stronger, is only half a second quicker than the RD350 in the sim. The RD350 was already most of the way to the practical limit for a carburetted 2-stroke twin.',
  },
  {
    type: 'h2',
    text: 'The Indian context: Rajdoot RD350 HT and LT',
  },
  {
    type: 'p',
    text: 'Escorts Group licensed the RD350 from Yamaha and sold it in India under the Rajdoot brand from 1983 to 1989. Two variants reached the Indian market: the High Torque (HT) and the Low Torque (LT). The HT was rated at 30.5 hp at 6750 rpm, the LT at 27.0 hp at 6500 rpm. Both numbers are below the 39 hp Yamaha export figure because Escorts modified the carburettor jet, ignition timing, and (on the LT specifically) the expansion chamber geometry to comply with Indian fuel-quality and emissions standards of the era. Indian petrol in the early 1980s was 87 octane and contained tetraethyl lead; jetting and timing were detuned to avoid pre-ignition on long highway runs. The chassis, gearbox, and basic engine architecture were identical to the export 1973-1975 spec.',
  },
  {
    type: 'p',
    text: 'In the sim, the HT\'s 8.5 hp deficit (12 hp on the LT) shows. With the same chassis and peak power scaled to 30.5 hp at 6750 rpm, MotoQuant puts the Rajdoot RD350 HT at approximately 15.6 seconds and a 135 km/h trap. The LT slows to roughly 15.9 seconds and a 130 km/h trap. Both are still well ahead of any modern Indian 200-350cc commuter on a stock tune. Re-jet to the original 1973 Yamaha specification of 240 main jets in both cylinders, fit an expansion chamber that escaped the Escorts detuning, and most of the difference between an HT and an export RD350 closes.',
  },
  {
    type: 'p',
    text: 'This is the version that built the bike\'s reputation in India. The Bombay-to-Pune Expressway timeslips that circulate on old Indian Yamaha forums (sub-30-minute runs through traffic on a stock Rajdoot RD350 HT in 1986) fit the sim\'s 135 km/h trap speed. A bike that traps at 135 km/h over a quarter mile will easily cruise at 140 km/h on an open expressway. The Splendor of the same era trapped at about 95 km/h, a generation behind.',
  },
  {
    type: 'h2',
    text: 'The two-stroke clutch engagement problem',
  },
  {
    type: 'p',
    text: 'During clutch slip, a 4-stroke single has a measurable rotational inertia. The crank, flywheel, valves, cam and connecting rod all store kinetic energy that the clutch has to bleed off as the rear wheel comes up to engine speed. On a typical 4-stroke litre superbike such as a GSX-R 1000 K5, the slip phase transfers roughly 1.6 kJ at the friction surface, dissipated as heat over about 1.2 seconds of launch.',
  },
  {
    type: 'p',
    text: 'A 2-stroke is different. There are no valves, no camshaft, no separate oil pump (most premix), and the flywheel is sized for crank balance rather than slip-bleed capacity. The rotational inertia of an RD350 crank-and-piston assembly is roughly 0.0035 kg·m², about 60 percent of a comparable 4-stroke 350. During clutch engagement the crank can slow down much faster, so the clutch has less work to do to bleed off rpm and the bike accelerates harder out of the hole.',
  },
  {
    type: 'p',
    text: 'MotoQuant\'s 2-stroke category profile (cluster tag two_stroke) carries its own max_engine_decel_rads2 parameter, separate from the 4-stroke clusters. Before May 31 2026 that parameter was capped at 800 rad/s², a conservative number taken from generic 4-stroke literature. After the calibration that shipped today it is 1500 rad/s², which matches the Honda HRC NSR250 service-manual figure of ~10000 rpm/s peak transient (≈1050 rad/s² steady, with chamber-on transition peaks higher). The change took 347 ms off the RD350 sim ET directly, and 120 ms off the NSR250R MC21 sim. The May 31 physics calibration report has the full sweep table.',
  },
  {
    type: 'p',
    text: 'At the strip, an RD350 wants more aggressive clutch slip than a 4-stroke of equivalent power, and the 2T crank can take it. The expansion chamber needs revs in the tuned band (around 7500 rpm for the stock RD350 chamber) to make the rated power. A soft launch that drops the engine below 5500 rpm during clutch engagement falls off the pipe: the chamber stops stuffing charge and the bike accelerates as if it had 22 hp instead of 39. A short, hard clutch slip with the engine held at 7000-7500 rpm, launched on the first hint of front-wheel lift, gives the 14-second result. A soft, street-style launch gives a 16-second result on the same hardware.',
  },
  {
    type: 'callout',
    text: 'On a two-stroke you launch from the tuned rpm, not from idle. The clutch bridges the gap between zero road speed and the engine speed where the pipe resonates, and the slip has to be short enough that the engine never drops out of the tuned band. The 4-stroke method (modulate throttle to control front-wheel lift) does not work on a 2-stroke. The 2-stroke launch is binary: on the pipe, or off it.',
  },
  {
    type: 'h2',
    text: 'Gearing: why the 6-speed matters',
  },
  {
    type: 'p',
    text: 'The RD350\'s 6-speed gearbox is one of the cleanest pieces of engineering on the bike. Ratios [2.461, 1.555, 1.190, 0.961, 0.821, 0.740] with 16/37 final drive on a 17-inch rear wheel give these road speeds at peak power:',
  },
  {
    type: 'table',
    rows: [
      ['Gear', 'Ratio', 'Speed at 7500 rpm (peak power)'],
      ['1st', '2.461', '~52 km/h'],
      ['2nd', '1.555', '~83 km/h'],
      ['3rd', '1.190', '~108 km/h'],
      ['4th', '0.961', '~134 km/h'],
      ['5th', '0.821', '~157 km/h'],
      ['6th', '0.740', '~174 km/h'],
    ],
  },
  {
    type: 'p',
    text: 'The sim traps at ~145 km/h, in fifth gear at about 7000 rpm, inside the tuned band. Sixth is for highway cruising and never comes into play on the strip. The first-to-second shift happens at about 52 km/h and 7500 rpm and drops the engine to about 4700 rpm in second. That is below the tuned band, so there is a short lull while the chamber catches up. The second-to-third shift at 83 km/h drops the engine to 6400 rpm, well within the band. From third gear on, the engine stays on the pipe for the rest of the run.',
  },
  {
    type: 'p',
    text: 'A 1-tooth larger front sprocket (17/37 instead of 16/37) shortens overall final drive by 6.25 percent. The simulator shows roughly 0.18 s of ET gain at Aamby Valley November conditions on a stock RD350: the change tightens up the first-to-second shift point and keeps the engine higher in the tuned band through second gear. It costs about ₹450 for a JT Sprockets unit from any Indian motorcycle parts retailer. That makes it the cheapest quarter-mile tenth on the bike, and it is a known mod in Indian RD350 restoration circles. The 16/37 OEM combination was chosen for highway durability and chain longevity, not strip ET.',
  },
  {
    type: 'h2',
    text: 'Where the stock tune falls apart, and what survives restoration',
  },
  {
    type: 'p',
    text: 'A 53-year-old RD350 in India in 2026 is almost certainly not stock. Most running examples have been through 30-40 years of makeshift repairs, decarbonising and substitute parts. The faults that most often cost strip ET are a leaking crank seal (it steals primary compression and drops peak power by 4-7 hp), a slack expansion chamber baffle (it shifts the tuned rpm and narrows the band) and a worn clutch basket (it stretches the slip and bleeds the launch). All three can be fixed. None needs work on the engine internals beyond a top-end rebuild, which any competent 2-stroke shop in Pune, Bangalore or Coimbatore can do.',
  },
  {
    type: 'p',
    text: 'For a properly restored RD350 (crank seals replaced, expansion chamber checked or replaced with a Yamaha service replica, clutch overhauled with new friction plates, carburettors rebuilt with the original 240 main jets), the simulator suggests an Aamby Valley November ET of approximately 14.2 to 14.5 seconds with a competent launch, and a trap speed of 142 to 148 km/h. The Cycle World 1973 benchmark bounds that range on the optimistic side, and the modelled cluster bias bounds it on the conservative side.',
  },
  {
    type: 'p',
    text: 'A well-prepared RD350 in 2026 is not as fast as a stock 2026 KTM Duke 390 (sim ~13.5 s) or a stock 2024 Aprilia RS 457 (sim ~13.3 s). It is much faster than any sub-300cc commuter sold in India today, and it is a different kind of motorcycle. The KTM and the Aprilia have three more generations of engineering refinement behind them. The RD350 is a museum piece that is still quick enough to beat most of the bikes sold to Indian commuters in 2026.',
  },
  {
    type: 'h2',
    text: 'Comparisons and simulator links',
  },
  {
    type: 'p',
    text: 'The MotoQuant simulator at motoquant.in has the 1973 Yamaha RD350 spec loaded as bike entry 352 (the model code matches the Yamaha factory designation). You can set rider mass, ambient temperature, density altitude and strip surface from the Location Picker. Aamby Valley loads the conditions used in this post. MMRT Chennai or Kari Motor Speedway will move the ET by roughly 0.15 to 0.30 s, depending on altitude, humidity and surface grip.',
  },
  {
    type: 'p',
    text: 'The simulator also runs the RD400 Daytona, the RGV250 Gamma VJ22, the Yamaha RX100 and the Aprilia RS125: every other Indian-market 2-stroke that left useful drag-strip data behind. The catalog at motoquant.in/bikes filters by stroke type, so you can list the 2-strokes on their own. Each one shows its sim residual, so if you are weighing up a restoration project you can see what to expect on a strip.',
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
          datePublished: '2026-05-31',
        })}
      />
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          <div className="flex flex-wrap gap-2 mb-6">
            {['Yamaha', 'RD350', 'Two-stroke', 'Rajdoot RD350', 'India', 'physics'].map((t) => (
              <span
                key={t}
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Yamaha RD350 quarter-mile physics: why a 1973 2-stroke still runs 14.7s
          </h1>
          <div className="text-sm text-white/60 mb-12">
            31 May 2026 · 12 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        <div className="max-w-2xl mx-auto mt-16 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Run an RD350 sim with your own numbers</div>
            <div className="text-white/60 text-sm">
              Pick the Yamaha RD350 in the simulator and set your strip and rider weight. The Aamby Valley November conditions used in this post load by default.
            </div>
          </div>
          <Link
            href="/simulator?bike=yamaha-rd350-1973&venue=aamby-valley"
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
                href="/blog/how-a-2-stroke-expansion-chamber-actually-works"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How a 2-stroke expansion chamber actually works
              </Link>:{' '}
              the pressure-wave physics that makes the RD350 chamber stuff fresh charge back into the cylinder at 7500 rpm.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/yezdi-roadster-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Yezdi Roadster quarter-mile physics
              </Link>:{' '}
              the other 2-stroke twin that built a following in India, in the same chassis class.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/the-physics-of-a-perfect-launch"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                The physics of a perfect launch
              </Link>:{' '}
              why 2-stroke launch is binary (on the pipe or off it) and how that differs from a 4-stroke launch.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/how-to-tune-for-aamby-valley-in-november"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to tune for Aamby Valley in November
              </Link>:{' '}
              the venue, the conditions, and the density-altitude math used in every sim in this post.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/royal-enfield-hunter-350-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Royal Enfield Hunter 350 quarter-mile physics
              </Link>:{' '}
              the 2025 350cc commuter that the 1973 RD350 still beats by over two seconds.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>:{' '}
              every 2-stroke in MotoQuant alongside the modern 200-400cc class for direct comparison.
            </li>
          </ul>
        </div>
      </article>

      <SiteFooter />
    </div>
  );
}
