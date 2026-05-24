import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'hayabusa-quarter-mile-physics-what-limits-9-6-seconds';
const TITLE = 'Hayabusa Quarter-Mile Physics: What Limits the 9.6';
const DESCRIPTION =
  'MotoQuant simulates the Suzuki Hayabusa Gen1 at exactly 10.4712 seconds — a reference baseline locked across every physics commit since April 2024. What stops a stock Hayabusa from running 9.6 on a strip, and where the seven tenths come from on a drag-prepped build.';

export const metadata = {
  title: 'Hayabusa Quarter-Mile Physics: What Limits the 9.6 Seconds',
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
    text: 'MotoQuant simulates the Suzuki Hayabusa Gen1 at exactly 10.4712 seconds — a reference baseline pinned to four decimal places that every physics commit since April 2024 has had to preserve. A drag-prepped Hayabusa with a stretched swingarm, 14-tooth front sprocket, sticky DOT drag rear, and a Power Commander tune runs the strip in 9.5 to 9.7 seconds. The seven tenths between those two numbers are not engine power. They are traction, geometry, gearing, and air. Here is exactly where each tenth lives, what it costs in rupees, and why a stock Hayabusa cannot break 10 seconds no matter how good the rider is.',
  },
  {
    type: 'h2',
    text: 'The 10.4712 Number, and What It Means',
  },
  {
    type: 'p',
    text: 'The Hayabusa Gen1 reference configuration inside MotoQuant is a 1999-2007 spec — 1299 cc inline-four, 170 hp at the rear wheel, 220 kg dry, 1485 mm wheelbase, 530 mm centre of gravity height, 51 percent front weight, 25 degrees of rake, 190/50ZR17 OEM Bridgestone Battlax BT-014 rear. Run that configuration in MotoQuant\'s 15-sub-model RK4 physics engine under matched Aamby Valley November conditions — density altitude around 1100 m, 22 degrees Celsius ambient, dry concrete with mu_peak around 1.30, 75 kg rider, two-step rev limiter set at peak torque RPM — and the simulator returns 10.4712 seconds at roughly 235 km/h trap, on the first run and on the thousandth.',
  },
  {
    type: 'p',
    text: 'That number is contractually load-bearing. The other two reference baselines pinned alongside it are the Suzuki GSX-R 1000 K5 at 10.0334 seconds and the Yamaha YZF-R1 4C8 at 10.2859 seconds. Every commit to the physics engine — every tweak to the torque curve generator, every change to the clutch slip model, every adjustment to the Pacejka tire coefficients, every new gear cassette in the Tier-1 lookup — has to leave all three numbers at delta plus 0.0000 seconds. The K5 and R1 baselines are validated against magazine ETs of 9.97s and 10.30s respectively, so MotoQuant runs a tiny touch conservative on those two. The Hayabusa sits inside the published range of 10.1 to 10.7 seconds for a stock Gen1 on a prepared strip.',
  },
  {
    type: 'p',
    text: 'So 10.4712 is the simulator answer for a stock Hayabusa under near-ideal conditions. The question is why it is not 9.7. Or 9.6. Or the 10.05 that the 2024 Hayabusa Gen3 magazine tests report on US strips. The seven-to-eight-tenths gap between the simulator stock baseline and a drag-prepped strip car comes from four specific physics constraints that no amount of engine power touches.',
  },
  {
    type: 'h2',
    text: 'Constraint One: Geometry and Wheelie',
  },
  {
    type: 'p',
    text: 'A stock Hayabusa wheelies in first gear at full throttle from rest. This is not a personality trait — it is the wheelie sub-model output. With 220 kg dry mass, 530 mm CoG height, 1485 mm wheelbase, and roughly 600 Nm of torque at the rear wheel in first gear (170 hp at 9500 rpm crank, gear ratio 2.583, primary 1.596, final drive 2.353, all multiplied through with about 92 percent driveline efficiency), the longitudinal acceleration that lifts the front wheel arrives at about 1.05 g. The bike makes that with 800 rpm of clutch slip and one careful right hand. The moment the front goes light, the rider has to roll out of throttle to keep the bike from going vertical, which means the bike spends the first 60 feet making less torque than it can deliver.',
  },
  {
    type: 'p',
    text: 'A drag-prepped Hayabusa attacks this with a stretched swingarm — typically a Schnitz Racing 8-inch or 10-inch extension that pushes the wheelbase from 1485 mm to about 1700 mm — and a lowered front end that drops CoG height from 530 mm to about 400 mm. Those two changes together cut the wheelie tendency roughly in half. The simulator shows the launch acceleration window opening from 0.95 g to about 1.25 g in the first 0.4 seconds, which is worth 0.25 to 0.30 seconds of ET on its own. A Schnitz extension costs roughly ₹95,000 landed in India with import duty and GST. A lowering link adds another ₹15,000. Combined cost-per-tenth on the geometry change works out to about ₹40,000 per tenth.',
  },
  {
    type: 'h2',
    text: 'Constraint Two: Traction',
  },
  {
    type: 'p',
    text: 'The OEM Bridgestone BT-014 fitted to the Gen1 Hayabusa has a Pacejka mu_peak around 1.18 at the optimal operating temperature of 65 degrees Celsius. On a cold strip in November at Aamby Valley, the first launch typically happens with tire temperatures around 25 to 30 degrees Celsius, which puts the contact patch about 10 to 15 degrees below the peak mu window. MotoQuant\'s thermal sub-model captures this — cold-tire mu sits at roughly 1.05 to 1.10 for the first 100 metres of the run, climbing to 1.18 only as the burnout and launch heat soaks in.',
  },
  {
    type: 'p',
    text: 'A sport-compound DOT drag tire — Pirelli Diablo Supercorsa SC1 in 190/50 or 200/50, or Bridgestone Battlax R11 — has a mu_peak around 1.40 to 1.50 at the same operating temperature, with a steeper warm-up curve that gets to peak grip inside the first 20 metres of a properly executed burnout. Swapping to a sticky DOT tire is worth about 0.20 seconds of ET in the simulator. The math is straightforward: at 1.05 g of cold-launch acceleration, the bike covers the first 60 feet in 1.74 seconds. At 1.30 g of warm-tire acceleration, the same 60 feet drops to 1.55 seconds. The remaining tenths come from carrying that higher launch speed through the entire run.',
  },
  {
    type: 'p',
    text: 'A Pirelli Diablo Supercorsa SC1 190/50ZR17 lists at roughly ₹18,000 in Indian retail. That is about ₹9,000 per tenth — the single best cost-per-tenth modification on the bike. It is also the first thing the parts-ROI engine inside MotoQuant recommends when you ask it to optimise a Hayabusa build under any budget above ₹15,000.',
  },
  {
    type: 'callout',
    text: 'The tire-first principle holds across every fast bike in the catalog. The cheapest tenths almost always live in the contact patch, not the engine. A Hayabusa with a Power Commander and a slip-on but stock OEM tires runs slower than a stock Hayabusa with a sticky DOT rear. The reason is simple: a tuned engine that cannot put power down loses to a stock engine that can.',
  },
  {
    type: 'h2',
    text: 'Constraint Three: Gearing',
  },
  {
    type: 'p',
    text: 'The stock Hayabusa runs 17F/40R final drive on a 530 chain — a road-bike ratio engineered to give a 290+ km/h top speed and a comfortable 110 km/h cruise in 6th gear. For drag racing this is too tall in the lower gears. First gear at the OEM ratio carries the bike from launch to about 110 km/h before redline; the simulator shows the bike shifting to second at roughly 0.9 seconds elapsed. A drag-prepped Hayabusa runs 16F/45R or even 15F/47R, which shortens first gear enough that the bike crosses 60 feet in first gear without needing a shift, and crosses the 1/8-mile mark in third instead of fourth.',
  },
  {
    type: 'p',
    text: 'The MotoQuant gear-ratio sweep on a Hayabusa shows the picture clearly. The stock 17/40 setup hits the trap line in fourth gear at about 9,200 rpm — roughly 300 rpm short of the peak power RPM. A 16/45 setup hits the trap line in fourth at 9,400 rpm, basically on the peak. A 15/47 setup hits the trap in third at 9,700 rpm, slightly past peak power, which means more time spent in the meat of the torque curve through the middle of the run. The 15/47 ratio is worth about 0.12 seconds of ET versus stock, with a top-speed penalty of roughly 25 km/h. For a 1320-foot strip that is a clean win; for a top-speed run on a long stretch it is the wrong tool.',
  },
  {
    type: 'p',
    text: 'A 16-tooth front sprocket in 530 pitch costs about ₹2,500 in Indian retail. A 47-tooth rear sprocket runs about ₹4,200. A new 530 X-ring chain to match (DID VX3 or RK GB) adds ₹9,000 to ₹11,000. The full gearing change comes in under ₹18,000 for about 0.12 seconds of ET — roughly ₹15,000 per tenth, second-best cost-per-tenth after the tire swap.',
  },
  {
    type: 'h2',
    text: 'Constraint Four: Aerodynamics at the Trap',
  },
  {
    type: 'p',
    text: 'At 235 km/h the aerodynamic drag force on a Hayabusa is about 92 percent of the engine\'s output. The bike is fighting air harder than it is fighting acceleration. The Gen1 Hayabusa runs a Cd of roughly 0.62 with a frontal area of 0.50 square metres, giving a Cd-times-A product of 0.31. The Gen3 cleaned this up modestly — Cd dropped to roughly 0.58 with the same frontal area, giving 0.29. That 7 percent improvement in drag area is worth about 4 km/h at the trap and roughly 0.04 to 0.05 seconds of ET on a stock-tune simulation.',
  },
  {
    type: 'p',
    text: 'For a drag-prepped Hayabusa the aerodynamic question shifts. The rider is tucked behind the windscreen for the entire run, the mirrors are typically removed, and a chin-on-tank position drops effective Cd-times-A by roughly 8 to 10 percent. That is worth another 5 to 6 km/h at the trap and about 0.06 seconds of ET. The cost is zero rupees and one upset traffic cop.',
  },
  {
    type: 'p',
    text: 'Beyond the rider position, the next aerodynamic step is a fairing replacement — a Sharkskinz race fairing without the OEM rear cowl light cluster, mirror mounts, or stock windscreen. That swap is worth maybe 0.03 to 0.04 seconds of ET and costs roughly ₹45,000 landed in India. Cost-per-tenth runs over ₹100,000, which is why aerodynamic mods rank dead last on the parts-ROI ladder for the strip. They are top of the ladder for top-speed runs, where Cd dominates the entire calculation.',
  },
  {
    type: 'h2',
    text: 'The Full Stage-1 to Drag-Prep Math',
  },
  {
    type: 'p',
    text: 'Putting the four constraints together gives the realistic upgrade path from stock 10.47 to drag-prepped 9.6. The simulator output for each rung is run under matched Aamby Valley November conditions with a 75 kg rider. Cost-per-tenth columns use Indian retail prices from the parts catalog as of May 2026:',
  },
  {
    type: 'table',
    rows: [
      ['Stage', 'Mod stack', 'Sim ET', 'Trap', 'Indian cost', '₹/tenth (cumulative)'],
      ['Stock', 'OEM, factory tune, BT-014 rear', '10.47 s', '235 km/h', '—', '—'],
      ['Stage 1a', '+ Pirelli Supercorsa rear DOT', '10.27 s', '237 km/h', '₹18,000', '₹9,000'],
      ['Stage 1b', '+ 16F/45R gearing + DID 530 VX3', '10.15 s', '232 km/h', '₹32,000', '₹10,000'],
      ['Stage 2', '+ Akrapovic slip-on + K&N filter + Power Commander V', '9.94 s', '241 km/h', '₹1,55,000', '₹29,000'],
      ['Stage 3', '+ stretched swingarm + lowering link', '9.68 s', '243 km/h', '₹2,65,000', '₹33,500'],
      ['Drag prep', '+ rider tuck + race fairing + clutch lockup', '9.55 s', '247 km/h', '₹3,15,000', '₹34,200'],
    ],
  },
  {
    type: 'p',
    text: 'Two patterns jump out of that table. First, the first ₹50,000 spent on a Hayabusa buys 0.32 seconds of ET — a tire and a sprocket. Past that point every additional tenth gets meaningfully more expensive. Second, even at ₹3.15 lakh of mod budget the simulator stops at 9.55 seconds. Getting below that requires either a turbo kit (₹4 to 6 lakh landed, worth another 1.0 to 1.2 seconds of ET if the fuel system and clutch can handle it) or a fully race-prepped chassis with billet wheels, lithium-ion battery, removed instrumentation, and ECU launch control. Neither is a Sunday-morning weekend mod.',
  },
  {
    type: 'callout',
    text: 'The MotoQuant simulator at motoquant.in lets you walk through this exact ladder for your own Hayabusa. Pick the bike, dial in your local strip conditions, then toggle each mod on and off to see the ET delta in real time. Free, no signup, no ads.',
  },
  {
    type: 'h2',
    text: 'Why a Stock Hayabusa Cannot Break 10 Seconds',
  },
  {
    type: 'p',
    text: 'The cleanest answer to "what limits the Hayabusa at 9.6" is also the answer to "why does a stock bike never break 10". The four constraints — wheelie geometry, cold-tire traction, road-spec gearing, and a road-spec rider posture — together cost the stock bike about 0.7 to 0.8 seconds of ET versus what the engine and the chassis could otherwise deliver. The engine itself is not the bottleneck. A stock 197-horsepower Hayabusa Gen2 dyno chart shows roughly 170 hp at the rear wheel; that is enough power to push a 220 kg bike with a 95 kg rider through the 402 metres of a quarter mile in about 9.5 seconds if every other constraint were removed.',
  },
  {
    type: 'p',
    text: 'None of those constraints are easy to remove on a road-registered bike. A stretched swingarm makes the bike unrideable in city traffic. A sticky DOT drag rear wears out in 800 kilometres. Short gearing means a 110 km/h cruise at 6,500 rpm in 6th instead of 4,200 rpm. The Hayabusa was engineered to be a fast road bike, and the four-tenths-to-eight-tenths penalty it pays at the strip is the cost of that road-bike DNA. The Gen3 reduces the penalty slightly through aerodynamic refinement and a stronger fuel-injection map, which is why magazine ETs on a stock 2024 Gen3 land closer to 10.05 seconds than the Gen1\'s 10.47.',
  },
  {
    type: 'h2',
    text: 'The Indian Context: Hayabusa Gen3 vs Used Gen2 Strip Builds',
  },
  {
    type: 'p',
    text: 'For an Indian buyer looking at the Hayabusa today, the practical question is whether to spend ₹16.9 lakh on a brand-new 2026 Gen3 with full Suzuki Motorcycle India warranty and dealer service network, or hunt the used market for a 2008-2012 Gen2 around ₹6 to 9 lakh and put the savings into mods. The simulator answer flips based on what you want from the bike.',
  },
  {
    type: 'p',
    text: 'If the goal is the fastest possible quarter-mile time at Aamby Valley or BIC: a used Gen2 with ₹3 lakh of mods runs 9.55 seconds. A brand-new Gen3 in showroom trim runs around 10.05 seconds. The used bike wins by half a second for less total spend. If the goal is a fast bike that does daily 100-kilometre commutes, weekend rides to Lonavla, occasional trips to a strip, and remains under warranty: the Gen3 wins on every other axis. The strip ET difference between stock Gen3 and a lightly-modded Gen2 (rear tire plus sprocket only) is roughly 0.10 to 0.12 seconds — well inside what a better rider on either bike will improve through practice.',
  },
  {
    type: 'p',
    text: 'For Pune and Narhe drag shops, the Hayabusa pattern is well-established. Used Gen1 and Gen2 platforms get bought from grey-market or first-owner trade-ins, stripped for strip duty, and run through a 6-to-12-month build cycle that lands them in the 9.4 to 9.7 second range. A turbo Hayabusa build from one of the established Narhe shops typically delivers 8.5 to 8.8 second ETs at the strip and runs roughly ₹14 to 18 lakh in mod budget on top of the donor bike. Those builds are a different category of conversation — the simulator inside MotoQuant supports forced-induction physics via the `forced_induction.boost_type` field, but the assumptions involved (clutch lockup, fuel pump capacity, intercooler thermal management) push outside the validated stock-tune envelope.',
  },
  {
    type: 'h2',
    text: 'Run the Numbers on Your Hayabusa',
  },
  {
    type: 'p',
    text: 'Every number in this post is a simulator output under specific conditions. Change rider weight by 15 kilograms, change ambient temperature by 10 degrees Celsius, change density altitude from Aamby Valley\'s 1100 metres to MMRT Chennai\'s 78 metres, change the launch RPM, change the surface from concrete to asphalt — and the absolute ETs shift on every line of the table above. The relative ordering of where the tenths come from stays the same: tire first, gearing second, geometry third, engine fourth, aerodynamics last for the strip and first for top-speed.',
  },
  {
    type: 'p',
    text: 'The simulator at motoquant.in carries the Hayabusa Gen1, Gen2, and Gen3 as separate catalog entries with their own spec sheets, plus 333 other bikes you can compare against. Pick your bike, pick your venue, pick your conditions, then sweep mods and read the ET delta directly. The Hayabusa Gen1 number is reference-locked at 10.4712 seconds and will not move; the Gen2 and Gen3 sit inside the litre-plus hyper-sport cluster with the documented ±0.15 second bias band. If you upload a Dragy timeslip from your own Hayabusa, the calibrator will pull that data point in and tighten the bias on your specific build.',
  },
  {
    type: 'p',
    text: 'The 9.6-second Hayabusa is real. It lives at the end of a ladder of physics constraints, each costing a measurable amount in tenths and a measurable amount in rupees. The fastest path up that ladder runs through the contact patch and the chain, not the exhaust. Anyone selling you an Akrapovic slip-on as your first Hayabusa mod is selling you the second-most-expensive tenth in the catalog. Buy the tire first.',
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
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Hayabusa Quarter-Mile Physics: What Limits the 9.6
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
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
                Hayabusa vs ZX-14R: Which Is Faster Off the Line?
              </Link>{' '}
              — spec-by-spec head-to-head with the Kawasaki ZX-14R, the other half of the hyper-sport conversation.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/the-physics-of-a-perfect-launch" className="text-brand-accent hover:text-brand-orange transition-colors">
                The Physics of a Perfect Launch
              </Link>{' '}
              — clutch slip, weight transfer, and traction in the first 0.4 seconds. Why launch composure decides hyper-sport ET more than peak power does.
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
              <Link href="/blog/how-the-motoquant-physics-engine-works" className="text-brand-accent hover:text-brand-orange transition-colors">
                How the MotoQuant Physics Engine Works
              </Link>{' '}
              — the 15-sub-model RK4 architecture that locks the Hayabusa Gen1 baseline at 10.4712s and keeps it there across every commit.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>{' '}
              — Hayabusa Gen1, Gen2, Gen3 and 330+ other bikes with full spec sheets and OEM tire fitments.
            </li>
            <li>
              ·{' '}
              <Link href="/pricing" className="text-brand-accent hover:text-brand-orange transition-colors">
                MotoQuant Pricing
              </Link>{' '}
              — Free for street tuners; Pro for shops and racing teams.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Walk the Hayabusa upgrade ladder yourself</div>
            <div className="text-white/60 text-sm">
              Free simulator — pick the Hayabusa, dial in your local conditions and rider weight, then toggle mods one at a time to see exactly which tenths cost what.
            </div>
          </div>
          <Link
            href="/simulator?bike=suzuki-hayabusa"
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
