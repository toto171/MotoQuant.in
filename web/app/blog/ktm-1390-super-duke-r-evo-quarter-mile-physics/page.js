import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema, OG_IMAGE } from '../../StructuredData';
import PostBikeLinks from '../../../components/PostBikeLinks';

const SLUG = 'ktm-1390-super-duke-r-evo-quarter-mile-physics';
const TITLE = 'KTM 1390 Super Duke R EVO quarter-mile physics breakdown';
const DESCRIPTION =
  'KTM 1390 Super Duke R EVO quarter-mile time: MotoQuant simulates the 2024 EVO at 10.225s with a 237.3 km/h trap at Aamby Valley. MCN clocked 9.95s on a stock bike. India pricing, the cost per tenth of each mod, and what closes the 0.275s gap.';

export const metadata = {
  title: 'KTM 1390 Super Duke R EVO quarter-mile physics',
  description: DESCRIPTION,
  keywords: [
    'KTM 1390 Super Duke R quarter mile',
    'KTM 1390 EVO quarter mile india',
    'KTM 1390 Super Duke R EVO drag time',
    'KTM 1390 EVO 0-100',
    'KTM 1390 EVO 0-100 india',
    'Super Duke R EVO drag race',
    'KTM 1390 vs 1290 drag',
    'KTM 1390 price india',
    'KTM 1390 Super Duke R EVO india review',
    'ktm 1390 evo vs kawasaki h2',
    'ktm 1390 evo vs s1000r',
    'litre naked drag race india',
    'fastest naked bike india quarter mile',
    'ktm 1390 aamby valley',
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `https://motoquant.in/blog/${SLUG}`,
    type: 'article',
    publishedTime: '2026-05-08T00:00:00Z',
    images: [OG_IMAGE],
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: 'MotoQuant simulates the 2024 KTM 1390 Super Duke R EVO at 10.225 seconds and a 237.3 km/h trap. Cycle World and MCN clocked stock test bikes at roughly 9.95s. The 0.275s gap is not noise. The model carries a bias for the whole litre-naked cluster by design, and where that bias comes from tells you a lot about what this bike does on a drag strip.',
  },
  {
    type: 'h2',
    text: 'What the 1390 is',
  },
  {
    type: 'p',
    text: "The 1390 Super Duke R EVO is not a clean-sheet redesign. KTM's 2024 press kit says so: the 1390 inherits the 1290 EVO platform with new pistons and a new crankshaft. Bore moves from 108 to 110 mm, displacement from 1301 to 1350 cc, and peak figures climb from 180 hp / 140 Nm to 190 hp / 145 Nm. Everything else (the chrome-moly trellis frame, the 6-speed cassette gearbox, the 17F/41R 525 chain, the WP Apex suspension, the Brembo Stylema brakes) carries over unchanged from the 1290 EVO.",
  },
  {
    type: 'p',
    text: 'The carryover matters because it lets the simulator hold everything except the engine constant. The 1290 Super Duke R EVO is already in the MotoQuant catalog, with gearing taken from the service manual and a published Cycle World ET in the 9.7s range. Put a 110 mm piston into the same chassis and the math should give a slightly heavier, slightly torquier version of the same drag profile. It does, but the trap speed is the more interesting number.',
  },
  {
    type: 'h2',
    text: 'Stock-tune simulation numbers',
  },
  {
    type: 'p',
    text: 'We ran the 1390 in MotoQuant under Aamby Valley November conditions (density altitude ≈ 1100 m, 22°C ambient, dry asphalt, μ_peak 1.35 on the OEM Bridgestone S22 rear), with a 78 kg rider on a 200 kg dry bike. On the stock tune it gives these numbers:',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'Value', 'Source'],
      ['Quarter-mile ET', '10.225 s', 'MotoQuant sim'],
      ['Trap speed', '237.3 km/h', 'MotoQuant sim'],
      ['60-foot time', '~1.81 s', 'MotoQuant sim'],
      ['Real-world ET (stock)', '~9.95 s', 'MCN 2024 launch test'],
      ['Real-world trap', '232–238 km/h', 'MCN / Cycle World'],
      ['Sim − real ΔET', '+0.275 s', 'cluster bias'],
    ],
  },
  {
    type: 'p',
    text: 'The +0.275s gap sits inside the documented +0.15–0.30s slow bias for the litre-naked cluster. The simulator shows the same bias on the 1290 Super Duke R, the BMW M1000R, the Streetfighter V4 and the Tuono V4 1100 Factory. Naked litre bikes run quicker on the strip than the simulator predicts because riders tuck hard once the launch is over. MotoQuant models a gentler tuck so the cluster stays honest in street-spec conditions.',
  },
  {
    type: 'p',
    text: "Launch RPM is the second cause. Magazine testers run a fully warmed bike with traction control at its lowest setting, dump the clutch at exactly the rpm where the front tire just begins to skim, and ride the throttle through 60 feet on the edge of a wheelie. MotoQuant pins its launch-RPM floor to the bike's peak-torque rpm. That is conservative and repeatable, and it suits a smart rider rather than a heroic one. On the 1390 the difference is roughly 0.10 to 0.15s of 60-foot time, which alone accounts for half of the sim-real gap.",
  },
  {
    type: 'callout',
    text: 'The simulator runs slow on purpose. Magazine drag tests are run by trained journalists with launch control, race fuel where allowed, and aggressive tucks. A street rider on a stock bike at Aamby Valley will see numbers closer to the simulation than to the magazine. The model is calibrated to the 50th-percentile real-world rider, not the 95th.',
  },
  {
    type: 'h2',
    text: 'Why the 1390 is faster than the 1290, and by how much',
  },
  {
    type: 'p',
    text: "Power is up 10 hp, torque is up 5 Nm, and dry weight is up roughly 25 kg over the listed-spec 1290 (much of it regulatory equipment, not engine mass). The simulator's per-bike sweep has the 1390 EVO running ~0.05–0.08s faster than the 1290 EVO under matched conditions. Almost all of that comes in the top half of the run, where the extra 10 hp matters more than the extra mass. The 60-foot times are within 0.01s because off the line both bikes are limited by gearing and traction, not by power.",
  },
  {
    type: 'p',
    text: "The trap-speed delta is bigger than the ET delta. The 1390 gains ~3 km/h in the trap (237 vs 234 km/h), so the extra power is doing useful work between 200 and 230 km/h, where the older 1290 was already running into its drag wall. If you own a 1290 and are tempted to upgrade for the drag strip, the honest answer is that the 1390 is faster, but not by much. The chassis is identical and the gearing carries over, so you're paying for 10 hp and a piston upgrade. A used 1290 with an Akrapovic full system and an ECU flash will run within 0.05s of a stock 1390.",
  },
  {
    type: 'p',
    text: "There is one exception. The 1390's revised crankshaft and pistons sharpen throttle response between 4,000 and 7,000 rpm, the range the bike spends most of its time in during a low-traction launch. The simulator does not currently model this transient gain, because its torque curve is interpolated from peak figures plus the documented dyno band. The real 1390 may therefore pull slightly harder out of the hole than the model predicts. That would bring a careful rider closer to the magazine's 9.95s than to the simulated 10.225s: better mid-band response takes another 0.05–0.10s off the simulated time with no other change.",
  },
  {
    type: 'h2',
    text: 'What limits the 1390 in the quarter',
  },
  {
    type: 'p',
    text: 'Three things, in order of impact:',
  },
  {
    type: 'p',
    text: "1. Wheelie. With 145 Nm of torque at 8,000 rpm, a 200 kg dry bike and a 1432 mm wheelbase, the 1390 has the highest wheelie risk of any production naked at any RPM below 70 km/h. The simulator's wheelie sub-model shows the front wheel lifting at full throttle through gear 1 and most of gear 2, unless the rider feathers the throttle or moves their CoG well forward. MCN's test riders found the same on real bikes: the 1390 is a wheelie machine, and gear 1 is limited by torque rather than by power.",
  },
  {
    type: 'p',
    text: "2. Aerodynamics. The 1390's listed Cd is 0.73, with a frontal area of 0.54 m². That is naked-bike territory, about 25% more aerodynamic drag than a faired Hayabusa at 250 km/h, and it is why the trap speed levels off around 237 km/h instead of the 245+ where a sport bike with similar power would land. The only fixes are a touring screen or a dedicated drag fairing, and neither leaves the 1390 the bike KTM intended.",
  },
  {
    type: 'p',
    text: '3. Sixth gear is a true overdrive. Final drive in 6th is 1.000 with 17F/41R sprockets, so the simulator has the bike crossing the trap line in 5th gear under most conditions. Sixth is an autobahn cruising gear, not a drag-strip gear. Dropping to 16F/41R would shorten 5th enough to put the bike on the trap line in top gear, with a small ET gain, at the cost of top-end roll-on punch. MotoQuant\'s parts catalog scores exactly this kind of swap: a drag-strip sprocket pair costs ~₹3,800 per tenth on this bike.',
  },
  {
    type: 'h2',
    text: 'How the simulation compares with the 1290 Super Duke R EVO and the Streetfighter V4',
  },
  {
    type: 'p',
    text: 'Each of these flagship litre nakeds has a different physics profile. The numbers are MotoQuant stock-tune sims under matched conditions:',
  },
  {
    type: 'table',
    rows: [
      ['Bike', 'Sim ET', 'Sim trap', 'Dry mass', 'Peak hp', 'Real-world ET'],
      ['KTM 1390 SDR EVO', '10.225 s', '237 km/h', '200 kg', '190', '~9.95 s'],
      ['KTM 1290 SDR EVO', '10.27 s', '234 km/h', '175 kg', '180', '~9.93 s'],
      ['Ducati Streetfighter V4', '10.05 s', '243 km/h', '178 kg', '208', '~9.7 s'],
      ['BMW M1000R', '10.10 s', '241 km/h', '199 kg', '210', '~9.8 s'],
    ],
  },
  {
    type: 'p',
    text: "The 1390 is the slowest of the four in raw simulation, but the gap to the Streetfighter V4 and the M1000R is smaller than the spec sheet suggests, because both faster bikes pay for their power with a much higher wheelie risk at launch. In the 60-foot zone the 1390's longer wheelbase pays back: the Streetfighter V4 cannot put 208 hp to the ground in gear 1 without traction control stepping in. On a perfectly prepped drag strip with launch control disabled, the four bikes run within 0.25s of each other.",
  },
  {
    type: 'p',
    text: "Two-rider data on each platform shows the same thing another way. The Streetfighter V4 traps about 6 km/h higher than the 1390 (243 vs 237 km/h) but beats it by only 0.18s in ET. A bike that does that is winning on the top half of the run, not at the launch. The 1390's chassis gives one of the easier litre-naked launches, even though its engine outputs no longer lead the class. The typical Indian buyer runs maybe ten quarter-mile passes a year, and for that rider an easier launch means more consistent runs than the spec sheet would predict.",
  },
  {
    type: 'h2',
    text: 'Gearing is where the tenths are',
  },
  {
    type: 'p',
    text: "Stock gearing on the 1390 EVO is 17F/41R with a 525 chain and the cassette ratios [2.500, 1.857, 1.538, 1.300, 1.148, 1.000], unchanged from the 1290 EVO. With a 200/55ZR17 rear (rolling radius ≈ 320 mm) and the 1.000 final-drive multiplier in 6th, the bike hits its 10,000 rpm power peak at roughly 295 km/h in 6th. That is well above the 237 km/h trap speed, so 6th gear never does real drag-strip work.",
  },
  {
    type: 'p',
    text: "The simulator log shows the bike crossing the trap line in 5th at roughly 9,500 rpm, slightly under peak power and slightly over peak torque. A 16/41 sprocket swap moves that crossing into 6th at about 8,800 rpm. That sounds worse, but it isn't. Because 6th is an overdrive, wheel torque at 8,800 rpm in 6th is essentially the same as in 5th at 9,500 rpm, and the bike makes the shift earlier and spends less time in the gear-change deadband. Net ET gain: roughly 0.04 to 0.06 seconds, depending on how the rider rides.",
  },
  {
    type: 'p',
    text: "A more aggressive 16/42 swap shortens the ratios further and makes the 1390 a true 5th-gear quarter-mile bike. The cost is that 6th becomes useless on the highway: the bike pulls through 250 km/h in 5th, then does very little in 6th. Most owners who make this swap are committed to drag-strip use. Nobody street-rides a 1390 on 16/42 gearing for long.",
  },
  {
    type: 'h2',
    text: 'The 1390 at Indian drag strips',
  },
  {
    type: 'p',
    text: "The 1390 Super Duke R EVO costs roughly ₹22.5 lakh on-road in India (KTM India, 2026 pricing). At a typical monthly meet, Aamby Valley and the BIC drag strip see roughly two dozen private owners running litre nakeds. Most ride 1290s, with a handful of older RSV4 Tuonos and the occasional MT-10. On the stock tune at Aamby Valley in October-November conditions, an experienced rider will run a 1390 at 10.1–10.2s. The simulator's 10.225s sits at the slower end of that range, where a careful first-time tester would land.",
  },
  {
    type: 'p',
    text: "The Indian-market mods that make a real difference: an Akrapovic Racing slip-on (~₹1.85 lakh) is worth roughly 0.06s ET. A KTM PowerParts Akrapovic Evolution full system (~₹3.2 lakh) plus an ECU flash from KTune or Powertronic (~₹35,000) is worth roughly 0.18s. A 16/42 sprocket swap (~₹4,500 in parts) is worth roughly 0.04–0.06s. None of these is cheap per tenth on a stock bike that already runs 10-flat. The bike is so fast as delivered that each extra tenth costs a lot, which is why Indian owners usually tune the 1390 lightly.",
  },
  {
    type: 'callout',
    text: 'Fastest path on the 1390: gearing first (cheapest per tenth), then a flash, then exhaust. Skip suspension upgrades unless you compete. The 1390 chassis is good enough off the showroom floor that aftermarket Öhlins is a comfort upgrade, not an ET upgrade.',
  },
  {
    type: 'h2',
    text: 'Run your own numbers',
  },
  {
    type: 'p',
    text: "If you own a 1390, or are choosing between the 1390 and the 1290, the simulator at motoquant.in lets you sweep rider weight, ambient temperature, density altitude and parts-catalog mods to see where your tenths come from. The cluster-bias correction above is built into the model: when the simulator says your bike runs 10.2, expect the strip to show closer to 9.95–10.05 with a competent rider. That gap is documented and intentional.",
  },
  {
    type: 'p',
    text: "For everyday tuning, the simulator also shows which mods are dead weight. Spending ₹1.85 lakh on an exhaust to gain 0.06s is a different deal from spending ₹4,500 on a sprocket pair to gain 0.05s. MotoQuant's parts ROI engine works this out for each part on each bike. On a 1390, gearing is by far the best answer if your main goal is quarter-mile time rather than topping a friend's MotoVlog.",
  },
  {
    type: 'p',
    text: "Two caveats. First, every number in this post is a stock-tune simulation under specific conditions. Change the rider weight, the ambient temperature, the surface or the launch technique and the absolute ETs shift, but the ranking of which mods help most stays the same. Second, work on closing the simulator's litre-naked cluster bias is ongoing. The May 2026 calibration work added Hypothesis property tests that pin the four load-bearing physics knobs to monotonic invariants, which makes future bias corrections safer to ship. Today's 10.225s might become a 10.10s in three months with no change to the bike's spec.",
  },
  {
    type: 'p',
    text: "On the KTM 1390 Super Duke R EVO, the launch is harder to get right than it looks, and the chassis is more forgiving than an engine this strong would lead you to expect. Spend your first weekend at the strip learning the launch, not bolting on parts.",
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
          datePublished: '2026-05-08',
        })}
      />
      <SiteNav />

      <article id="main" className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {['KTM', '1390 Super Duke R', 'physics', 'litre naked'].map((t) => (
              <span
                key={t}
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            KTM 1390 Super Duke R EVO quarter-mile physics breakdown
          </h1>
          <div className="text-sm text-white/60 mb-12">
            8 May 2026 · 9 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        <PostBikeLinks ids={[341]} />

        {/* Internal links / related reading */}
        <div className="max-w-2xl mx-auto mt-16">
          <h3 className="font-display font-bold text-lg text-white mb-4">Related reading</h3>
          <ul className="text-sm text-white/70 space-y-2">
            <li>
              ·{' '}
              <Link href="/blog/the-physics-of-a-perfect-launch" className="text-brand-accent hover:text-brand-orange transition-colors">
                The physics of a perfect launch
              </Link>:{' '}
              clutch, slip, and weight transfer in the first 0.4 seconds.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-the-motoquant-physics-engine-works" className="text-brand-accent hover:text-brand-orange transition-colors">
                How the MotoQuant physics engine works
              </Link>:{' '}
              the 15-sub-model architecture behind every ET prediction.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-to-tune-for-aamby-valley-in-november" className="text-brand-accent hover:text-brand-orange transition-colors">
                How to tune for Aamby Valley in November
              </Link>:{' '}
              the venue conditions used for the simulation in this post.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>:{' '}
              the specs, gear ratios and Cd values the simulator uses.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Run the 1390 yourself</div>
            <div className="text-white/60 text-sm">
              Free simulator: pick the 1390 Super Duke R EVO, dial in your local conditions, and watch the ET update live.
            </div>
          </div>
          <Link
            href="/simulator?bike=ktm-1390-super-duke-r-evo"
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
