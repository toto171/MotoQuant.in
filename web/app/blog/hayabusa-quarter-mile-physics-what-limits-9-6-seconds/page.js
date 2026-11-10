import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'hayabusa-quarter-mile-physics-what-limits-9-6-seconds';
const TITLE = 'Hayabusa quarter-mile physics: what limits the 9.6';
const DESCRIPTION =
  'MotoQuant simulates the Suzuki Hayabusa Gen1 at exactly 10.1100 seconds, a reference baseline CI holds to four decimals. What stops a stock Hayabusa from running 9.6 on a strip, and where the missing half-second comes from on a drag-prepped build.';

export const metadata = {
  title: 'Hayabusa quarter-mile physics: what limits the 9.6 seconds',
  description: DESCRIPTION,
  keywords: [
    'Hayabusa quarter mile time',
    'Hayabusa 9.6 second quarter mile',
    'Hayabusa drag racing physics',
    'Suzuki Hayabusa Gen1 quarter mile',
    'Hayabusa Gen3 quarter mile india',
    'Hayabusa drag prep india',
    'hayabusa stretched swingarm',
    'hayabusa launch control',
    'hayabusa traction limit',
    'hayabusa aamby valley',
    'hayabusa cost per tenth',
    'hayabusa power commander india',
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `https://motoquant.in/blog/${SLUG}`,
    type: 'article',
    publishedTime: '2026-05-24T00:00:00Z',
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: 'MotoQuant simulates the Suzuki Hayabusa Gen1 at exactly 10.1100 seconds, a reference baseline pinned to four decimal places that every physics commit has to preserve. A drag-prepped Hayabusa with a stretched swingarm, 14-tooth front sprocket, sticky DOT drag rear and a Power Commander tune runs the strip in 9.5 to 9.7 seconds. The four to six tenths between those numbers come from traction, geometry, gearing and air, not from engine power. This post shows where each tenth comes from, what it costs in rupees, and why a stock Hayabusa cannot break 10 seconds however good the rider is.',
  },
  {
    type: 'h2',
    text: 'What the 10.1100 means',
  },
  {
    type: 'p',
    text: 'The Hayabusa Gen1 reference configuration inside MotoQuant is a 1999-2007 spec: 1299 cc inline-four, 170 hp at the rear wheel, 220 kg dry, 1485 mm wheelbase, 530 mm centre of gravity height, 51 percent front weight, 25 degrees of rake, 190/50ZR17 OEM Bridgestone Battlax BT-014 rear. Run that configuration in MotoQuant\'s 15-sub-model RK4 physics engine at the reference conditions (sea level, 25 degrees Celsius, 50 percent humidity, dry asphalt, rear-tyre mu_peak 1.40, 75 kg rider) and the simulator returns 10.1100 seconds at 232.4 km/h trap, on the first run and on the thousandth.',
  },
  {
    type: 'p',
    text: 'That number is not allowed to move. The other two reference baselines pinned alongside it are the Suzuki GSX-R 1000 K5 at 10.0436 seconds and the Yamaha YZF-R1 4C8 at 10.1092 seconds. Every commit to the physics engine, whether it touches the torque curve generator, the clutch slip model or the tyre grip model, or adds a gear cassette to the Tier-1 lookup, has to leave all three numbers where they are: a delta of 0.0000 seconds. The published tests behind them are 9.97 s for the K5 (Cycle World), 10.30 s for the R1 (Sport Rider) and 10.40 s for the Hayabusa (Cycle World). The pins are not fitted to those three numbers; they come out of a fit across all 250 published tests, so the K5 runs 0.07 s slow against its magazine time, and the R1 and the Hayabusa run 0.19 s and 0.29 s quick against theirs.',
  },
  {
    type: 'p',
    text: 'So 10.1100 is the simulator\'s answer for a stock Hayabusa in near-ideal conditions. Why is it not 9.7, or 9.6, or the 10.05 that 2024 Hayabusa Gen3 magazine tests report on US strips? The four-to-six-tenths gap between the stock baseline and a drag-prepped strip bike comes from four physics constraints, and more engine power fixes none of them.',
  },
  {
    type: 'h2',
    text: 'Constraint one: geometry and wheelie',
  },
  {
    type: 'p',
    text: 'A stock Hayabusa wheelies in first gear at full throttle from rest, and the wheelie sub-model shows why. With 220 kg dry mass, 530 mm CoG height, 1485 mm wheelbase, and roughly 600 Nm of torque at the rear wheel in first gear (170 hp at 9500 rpm crank, gear ratio 2.583, primary 1.596, final drive 2.353, all multiplied through with about 92 percent driveline efficiency), the front wheel lifts at about 1.05 g of longitudinal acceleration. The bike gets there with 800 rpm of clutch slip and one careful right hand. Once the front goes light, the rider has to roll off the throttle to keep the bike from going vertical, so for the first 60 feet the bike makes less torque than it can deliver.',
  },
  {
    type: 'p',
    text: 'A drag-prepped Hayabusa deals with this using a stretched swingarm (typically a Schnitz Racing 8-inch or 10-inch extension that pushes the wheelbase from 1485 mm to about 1700 mm) and a lowered front end that drops CoG height from 530 mm to about 400 mm. Together the two changes cut the wheelie tendency roughly in half. In the simulator the launch acceleration window opens from 0.95 g to about 1.25 g in the first 0.4 seconds, worth 0.25 to 0.30 seconds of ET on its own. A Schnitz extension costs roughly ₹95,000 landed in India with import duty and GST, and a lowering link adds another ₹15,000. The geometry change works out to about ₹40,000 per tenth.',
  },
  {
    type: 'h2',
    text: 'Constraint two: traction',
  },
  {
    type: 'p',
    text: 'The OEM Bridgestone BT-014 fitted to the Gen1 Hayabusa has a mu_peak around 1.18 at its best operating temperature of 65 degrees Celsius. On a cold November strip at Aamby Valley the first launch usually happens with tyre temperatures around 25 to 30 degrees Celsius, which puts the contact patch about 10 to 15 degrees below the peak mu window. MotoQuant\'s thermal sub-model includes this: cold-tyre mu sits at roughly 1.05 to 1.10 for the first 100 metres of the run and climbs to 1.18 only as heat from the burnout and launch soaks in.',
  },
  {
    type: 'p',
    text: 'A sport-compound DOT drag tyre (Pirelli Diablo Supercorsa SC1 in 190/50 or 200/50, or Bridgestone Battlax R11) has a mu_peak around 1.40 to 1.50 at the same operating temperature, with a steeper warm-up curve that reaches peak grip inside the first 20 metres of a good burnout. In the simulator, a sticky DOT tyre is worth about 0.20 seconds of ET. At 1.05 g of cold-launch acceleration the bike covers the first 60 feet in 1.74 seconds; at 1.30 g on a warm tyre the same 60 feet takes 1.55 seconds. The remaining tenths come from carrying that higher launch speed through the entire run.',
  },
  {
    type: 'p',
    text: 'A Pirelli Diablo Supercorsa SC1 190/50ZR17 costs roughly ₹18,000 at Indian retail. That is about ₹9,000 per tenth, the best cost-per-tenth of any modification on the bike, and it is the first thing MotoQuant\'s parts-ROI engine recommends when you ask it to optimise a Hayabusa build on any budget above ₹15,000.',
  },
  {
    type: 'callout',
    text: 'Tyre first holds for every fast bike in the catalog: the cheapest tenths are almost always in the contact patch, not the engine. A Hayabusa with a Power Commander and a slip-on on stock OEM tyres runs slower than a stock Hayabusa with a sticky DOT rear, because a tuned engine that cannot put its power down loses to a stock engine that can.',
  },
  {
    type: 'h2',
    text: 'Constraint three: gearing',
  },
  {
    type: 'p',
    text: 'The stock Hayabusa runs 17F/40R final drive on a 530 chain, a road ratio chosen for a 290+ km/h top speed and an easy 110 km/h cruise in 6th gear. For drag racing it is too tall in the lower gears. On the OEM ratio, first gear carries the bike to about 110 km/h before redline, and in the simulator the bike shifts to second at roughly 0.9 seconds. A drag-prepped Hayabusa runs 16F/45R or even 15F/47R. That shortens first gear enough for the bike to cross 60 feet in first without a shift, and to cross the 1/8-mile mark in third instead of fourth.',
  },
  {
    type: 'p',
    text: 'In MotoQuant\'s gear-ratio sweep on a Hayabusa, the stock 17/40 setup hits the trap line in fourth gear at about 9,200 rpm, roughly 300 rpm short of peak power. A 16/45 setup hits it in fourth at 9,400 rpm, almost exactly on the peak. A 15/47 setup hits it in third at 9,700 rpm, slightly past peak power, so the engine spends more of the middle of the run in the fat part of the torque curve. The 15/47 ratio is worth about 0.12 seconds of ET over stock and costs roughly 25 km/h of top speed. On a 1320-foot strip that is a clear win; for a top-speed run on a long stretch it is the wrong choice.',
  },
  {
    type: 'p',
    text: 'At Indian retail a 16-tooth front sprocket in 530 pitch costs about ₹2,500 and a 47-tooth rear sprocket about ₹4,200. A matching 530 X-ring chain (DID VX3 or RK GB) adds ₹9,000 to ₹11,000. The full gearing change comes in under ₹18,000 for about 0.12 seconds of ET: roughly ₹15,000 per tenth, the second-best cost-per-tenth after the tyre swap.',
  },
  {
    type: 'h2',
    text: 'Constraint four: aerodynamics at the trap',
  },
  {
    type: 'p',
    text: 'At 235 km/h aerodynamic drag on a Hayabusa takes about 92 percent of the engine\'s output, so the bike spends more of its power pushing air than accelerating. The Gen1 Hayabusa runs a Cd of roughly 0.62 with a frontal area of 0.50 square metres, giving a Cd-times-A product of 0.31. The Gen3 improved this a little: Cd dropped to roughly 0.58 with the same frontal area, giving 0.29. That 7 percent cut in drag area is worth about 4 km/h at the trap and roughly 0.04 to 0.05 seconds of ET on a stock-tune simulation.',
  },
  {
    type: 'p',
    text: 'On a drag-prepped Hayabusa the rider stays tucked behind the windscreen for the entire run, the mirrors usually come off, and a chin-on-tank position cuts effective Cd-times-A by roughly 8 to 10 percent. That is worth another 5 to 6 km/h at the trap and about 0.06 seconds of ET. It costs zero rupees and one upset traffic cop.',
  },
  {
    type: 'p',
    text: 'After rider position, the next aerodynamic step is a replacement fairing: a Sharkskinz race fairing without the OEM rear cowl light cluster, mirror mounts or stock windscreen. It is worth maybe 0.03 to 0.04 seconds of ET and costs roughly ₹45,000 landed in India. At over ₹100,000 per tenth, aerodynamic mods rank last on the parts-ROI ladder for the strip. For top-speed runs, where Cd dominates the calculation, they rank first.',
  },
  {
    type: 'h2',
    text: 'Stage 1 to drag prep: the numbers',
  },
  {
    type: 'p',
    text: 'Put the four constraints together and you get the upgrade path from stock to a drag-prepped 9.6. Each rung was simulated in May 2026 on an earlier engine version, in Aamby Valley November conditions with a 75 kg rider. The absolute times are therefore higher than today\'s simulator gives (it puts a stock Gen1 at 10.22 s in the same conditions), so the steps between rungs are the useful part. Cost-per-tenth figures use Indian retail prices from the parts catalog as of May 2026.',
  },
  {
    type: 'table',
    rows: [
      ['Stage', 'Mod stack', 'Sim ET', 'Trap', 'Indian cost', '₹/tenth (cumulative)'],
      ['Stock', 'OEM, factory tune, BT-014 rear', '10.47 s', '235 km/h', '–', '–'],
      ['Stage 1a', '+ Pirelli Supercorsa rear DOT', '10.27 s', '237 km/h', '₹18,000', '₹9,000'],
      ['Stage 1b', '+ 16F/45R gearing + DID 530 VX3', '10.15 s', '232 km/h', '₹32,000', '₹10,000'],
      ['Stage 2', '+ Akrapovic slip-on + K&N filter + Power Commander V', '9.94 s', '241 km/h', '₹1,55,000', '₹29,000'],
      ['Stage 3', '+ stretched swingarm + lowering link', '9.68 s', '243 km/h', '₹2,65,000', '₹33,500'],
      ['Drag prep', '+ rider tuck + race fairing + clutch lockup', '9.55 s', '247 km/h', '₹3,15,000', '₹34,200'],
    ],
  },
  {
    type: 'p',
    text: 'The first ₹50,000 spent on a Hayabusa buys 0.32 seconds of ET: a tyre and a sprocket. After that, every extra tenth costs noticeably more. And even with ₹3.15 lakh of mods the simulator stops at 9.55 seconds. Going lower needs either a turbo kit (₹4 to 6 lakh landed, worth another 1.0 to 1.2 seconds of ET if the fuel system and clutch can take it) or a fully race-prepped chassis with billet wheels, a lithium-ion battery, the instruments removed and ECU launch control. Neither is a weekend job.',
  },
  {
    type: 'callout',
    text: 'You can walk through this ladder for your own Hayabusa at motoquant.in. Pick the bike, set your local strip conditions, then switch each mod on and off and watch the ET change as you go. It is free, with no signup and no ads.',
  },
  {
    type: 'h2',
    text: 'Why a stock Hayabusa cannot break 10 seconds',
  },
  {
    type: 'p',
    text: 'Whatever limits the Hayabusa at 9.6 also explains why a stock bike never breaks 10. The four constraints (wheelie geometry, cold-tyre traction, road-spec gearing and a road-spec rider posture) together cost the stock bike roughly half a second of ET against what the engine and chassis could otherwise deliver. The engine is not the bottleneck. A dyno chart for a stock 197-horsepower Hayabusa Gen2 shows roughly 170 hp at the rear wheel, enough to push a 220 kg bike with a 95 kg rider through the 402 metres of a quarter mile in about 9.5 seconds if every other constraint were removed.',
  },
  {
    type: 'p',
    text: 'None of those constraints is easy to remove on a road-registered bike. A stretched swingarm makes the bike unrideable in city traffic. A sticky DOT drag rear wears out in 800 kilometres. Short gearing means a 110 km/h cruise at 6,500 rpm in 6th instead of 4,200 rpm. The Hayabusa was built as a fast road bike, and the four-to-eight-tenths penalty it pays at the strip is the price of that. The Gen3 trims the penalty slightly with better aerodynamics and a stronger fuel-injection map, which is why magazine ETs for a stock 2024 Gen3 land closer to 10.05 seconds than the Gen1\'s 10.40.',
  },
  {
    type: 'h2',
    text: 'The Indian context: Hayabusa Gen3 vs used Gen2 strip builds',
  },
  {
    type: 'p',
    text: 'An Indian buyer looking at the Hayabusa today has a practical choice: spend ₹16.9 lakh on a new 2026 Gen3 with the full Suzuki Motorcycle India warranty and dealer service network, or find a 2008-2012 Gen2 on the used market for ₹6 to 9 lakh and put the savings into mods. Which one the simulator favours depends on what you want from the bike.',
  },
  {
    type: 'p',
    text: 'If you want the fastest possible quarter-mile at Aamby Valley or BIC, a used Gen2 with ₹3 lakh of mods runs 9.55 seconds and a new Gen3 in showroom trim runs around 10.05 seconds. The used bike wins by half a second for less total spend. If you want a fast bike that does a daily 100-kilometre commute, weekend rides to Lonavla and the odd strip day, and stays under warranty, the Gen3 wins on everything else. The strip ET gap between a stock Gen3 and a lightly modded Gen2 (rear tyre and sprocket only) is roughly 0.10 to 0.12 seconds, well inside what a better rider on either bike will find through practice.',
  },
  {
    type: 'p',
    text: 'Drag shops in Pune and Narhe follow a set pattern with the Hayabusa. They buy used Gen1 and Gen2 bikes from the grey market or first-owner trade-ins, strip them down for drag use, and run them through a 6-to-12-month build that lands them in the 9.4 to 9.7 second range. A turbo Hayabusa from one of the established Narhe shops typically runs 8.5 to 8.8 seconds at the strip and costs roughly ₹14 to 18 lakh in mods on top of the donor bike. Those builds are a different discussion. MotoQuant can simulate forced induction through the `forced_induction.boost_type` field, but the assumptions involved (clutch lockup, fuel pump capacity, intercooler thermal management) go outside the validated stock-tune envelope.',
  },
  {
    type: 'h2',
    text: 'Run the numbers on your Hayabusa',
  },
  {
    type: 'p',
    text: 'Every number in this post is a simulator output for specific conditions. Change the rider weight by 15 kilograms, the ambient temperature by 10 degrees Celsius, the density altitude from Aamby Valley\'s 1100 metres to MMRT Chennai\'s 78 metres, the launch RPM, or the surface from asphalt to a prepped strip, and the ETs shift on every line of the table above. The order of where the tenths come from stays the same: tyre first, gearing second, geometry third, engine fourth, and aerodynamics last for the strip and first for top speed.',
  },
  {
    type: 'p',
    text: 'The simulator at motoquant.in has the Hayabusa Gen1, Gen2 and Gen3 as separate catalog entries with their own spec sheets, plus 531 other bikes to compare against. Pick your bike, venue and conditions, then sweep mods and read the ET change directly. The Gen1 number is locked at 10.1100 seconds as a reference and will not move. The Gen2 and Gen3 sit in the litre sport 195 hp-and-up class, which shows a weighted mean absolute error of 0.171 s against 29 published tests. If you have a Dragy timeslip from your own Hayabusa, send it through the "Submit a timeslip" form; once reviewed, the run joins the benchmark set.',
  },
  {
    type: 'p',
    text: 'The quickest route to a 9.6-second Hayabusa runs through the contact patch and the chain, not the exhaust. Anyone selling you an Akrapovic slip-on as your first Hayabusa mod is selling you the second-most-expensive tenth in the catalog. Buy the tyre first.',
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
          datePublished: '2026-05-24',
        })}
      />
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {['Suzuki', 'Hayabusa', 'hyper sport', 'drag prep', 'India', 'physics'].map((t) => (
              <span
                key={t}
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Hayabusa quarter-mile physics: what limits the 9.6
          </h1>
          <div className="text-sm text-white/60 mb-12">
            24 May 2026 · 13 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        {/* Internal links / related reading */}
        <div className="max-w-2xl mx-auto mt-16">
          <h3 className="font-display font-bold text-lg text-white mb-4">Related reading</h3>
          <ul className="text-sm text-white/70 space-y-2">
            <li>
              ·{' '}
              <Link href="/blog/hayabusa-vs-zx-14r-which-is-faster" className="text-brand-accent hover:text-brand-orange transition-colors">
                Hayabusa vs ZX-14R: which is faster off the line?
              </Link>
              : a spec-by-spec comparison with the Kawasaki ZX-14R.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/the-physics-of-a-perfect-launch" className="text-brand-accent hover:text-brand-orange transition-colors">
                The physics of a perfect launch
              </Link>
              : clutch slip, weight transfer and traction in the first 0.4 seconds, and why a composed launch decides hyper-sport ET more than peak power does.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-to-tune-for-aamby-valley-in-november" className="text-brand-accent hover:text-brand-orange transition-colors">
                How to tune for Aamby Valley in November
              </Link>
              : the venue conditions used for every simulation in this post.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-the-motoquant-physics-engine-works" className="text-brand-accent hover:text-brand-orange transition-colors">
                How the MotoQuant physics engine works
              </Link>
              : the 15-sub-model RK4 engine that holds the Hayabusa Gen1 baseline at 10.1100s across every commit.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the bike catalog
              </Link>
              : Hayabusa Gen1, Gen2, Gen3 and 330+ other bikes with full spec sheets and OEM tyre fitments.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Walk the Hayabusa upgrade ladder yourself</div>
            <div className="text-white/60 text-sm">
              The simulator is free. Pick the Hayabusa, set your local conditions and rider weight, then add mods one at a time to see which tenths cost what.
            </div>
          </div>
          <Link
            href="/simulator?bike=suzuki-hayabusa"
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
