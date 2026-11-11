import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema, OG_IMAGE } from '../../StructuredData';
import PostBikeLinks from '../../../components/PostBikeLinks';

const SLUG = 'honda-hornet-2-0-vs-pulsar-ns200-quarter-mile';
const TITLE = 'Honda Hornet 2.0 vs Pulsar NS200: quarter-mile physics';
const DESCRIPTION =
  'Honda Hornet 2.0 vs Bajaj Pulsar NS200 quarter-mile comparison for Indian riders. MotoQuant simulates the Hornet 2.0 at ~17.55s and the NS200 at ~15.9s. Seven hp and 18 kg separate them; the physics shows where the gap comes from.';

export const metadata = {
  title: 'Honda Hornet 2.0 vs Pulsar NS200 quarter-mile India',
  description: DESCRIPTION,
  keywords: [
    'honda hornet 2.0 vs pulsar ns200 drag',
    'hornet 2.0 vs ns200 quarter mile',
    'honda hornet 2.0 drag time',
    'ns200 vs hornet 2.0',
    'honda hornet 2.0 quarter mile',
    'pulsar ns200 drag time india',
    'honda hornet 2.0 0-100 india',
    'best 184cc bike india drag',
    'indian 200cc drag comparison',
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
    text: 'MotoQuant simulates the stock Honda Hornet 2.0 at roughly 17.55 seconds and the stock Bajaj Pulsar NS200 at roughly 15.9 seconds under matched Aamby Valley November conditions. That 1.65 second gap is the largest ET difference in the Indian 180-200cc naked segment, and it comes from seven horsepower rather than mass, gearing or tires. The physics below shows why Honda\'s 184cc learner-friendly naked loses to Bajaj\'s 199cc performance-oriented single by a gap that no amount of cheap modding fully closes.',
  },
  {
    type: 'h2',
    text: 'The two bikes on paper',
  },
  {
    type: 'p',
    text: 'The Honda Hornet 2.0 arrived in India in 2020 as a replacement for the CB Hornet 160R. Honda kept the oil-cooled architecture, upped displacement to 184.4 cc, added fuel injection, and aimed the bike at learner-to-intermediate riders who wanted the Honda badge and manageable power. The result is a 17 hp single with a 64 × 57 mm long-stroke layout, a SOHC 2-valve head, and a spec sheet that looks civilised, almost deliberately gentle.',
  },
  {
    type: 'p',
    text: 'The Bajaj Pulsar NS200 runs a 72 × 49 mm short-stroke 199 cc single developed from the KTM 200 Duke architecture, with a DOHC 4-valve head and 24.2 hp at 9,000 rpm. It has been on sale in India since 2012 and has a well-documented drag strip record across Pune, Mumbai, and MMRT Chennai meets. The NS200 is heavier (160 kg dry against the Hornet\'s 142 kg), but it carries 7.2 more horsepower.',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'Honda Hornet 2.0 (2020+)', 'Bajaj Pulsar NS200 (2017+)'],
      ['Displacement', '184 cc', '199 cc'],
      ['Bore × stroke', '64.0 × 57.0 mm', '72.0 × 49.0 mm'],
      ['Bore-to-stroke ratio', '1.12:1 (long stroke)', '1.47:1 (short stroke)'],
      ['Compression', '10.0:1', '10.5:1'],
      ['Valvetrain', 'SOHC 2-valve', 'DOHC 4-valve'],
      ['Peak power', '17.0 hp @ 8,500 rpm', '24.2 hp @ 9,000 rpm'],
      ['Peak torque', '16.0 Nm @ 6,500 rpm', '18.3 Nm @ 6,500 rpm'],
      ['Dry mass', '142 kg', '160 kg'],
      ['Gears', '5-speed', '5-speed'],
      ['Final drive', '16F / 46R, 520 chain', '16F / 48R, 520 chain'],
      ['1st-gear ratio', '3.313', '3.083'],
      ['5th-gear ratio', '0.688', '0.971'],
      ['Cd', '0.80', '0.80'],
      ['Frontal area', '0.45 m²', '0.47 m²'],
      ['Front tire', '100/70R17', '100/70R17'],
      ['Rear tire', '130/70R17', '130/70R17'],
    ],
  },
  {
    type: 'p',
    text: 'Two numbers in that table explain most of the gap: the Hornet 2.0 is 18 kg lighter but makes 7.2 hp less power. Power-to-weight for the Hornet 2.0 is 17 hp / 212 kg total (142 kg dry + 70 kg rider) = 80 hp per tonne. For the NS200 it is 24.2 hp / 230 kg total = 105 hp per tonne. That 25 hp-per-tonne gap is large, about the same as the difference between a stock NS200 and a stock Apache RTR 200 4V combined with another stage of engine tuning.',
  },
  {
    type: 'h2',
    text: 'What the simulator says: stock numbers side by side',
  },
  {
    type: 'p',
    text: 'Running both bikes through the MotoQuant physics engine at matched Aamby Valley November conditions (density altitude near 1,100 m, 22°C ambient, dry asphalt with stock OEM rubber at μ_peak ≈ 1.05, 70 kg rider in stock tuck) gives these numbers:',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'Honda Hornet 2.0', 'Bajaj Pulsar NS200'],
      ['Quarter-mile ET (sim)', '~17.55 s', '~15.9 s'],
      ['Trap speed', '~116 km/h', '~123 km/h'],
      ['60-foot time', '~2.70 s', '~2.55 s'],
      ['1/8-mile ET', '~11.3 s', '~10.3 s'],
      ['Top gear at trap', '5th, ~8,300 rpm', '5th, ~8,900 rpm'],
      ['Cluster', 'entry-150-200 (±0.75 s band)', 'entry-200-300 (±0.5 s band)'],
    ],
  },
  {
    type: 'p',
    text: 'The simulator puts the gap at roughly 1.65 seconds, consistent with the Carblogindia drag test that showed the NS200 winning both rounds by a wide margin. Both ETs sit inside their cluster bias bands, so the Hornet 2.0 could run as fast as 16.8 s with a perfect launch and a well-worn set of OEM tires, and the NS200 could dip to 15.4 s. The order does not change: even if the Hornet beats its cluster centre by a full second, it still loses to the NS200 by 0.5 seconds.',
  },
  {
    type: 'callout',
    text: 'The Hornet 2.0 sits in MotoQuant\'s entry-150-200 cc cluster alongside bikes like the Hero Xtreme 200S 4V (17.40 s, 19.1 hp) and the R15 V4 (17.62 s real-world, 18.4 hp). That cluster has a documented mean absolute error of 0.75 s because published benchmarks for these bikes are sparse and run-to-run variance is high. The NS200 sits in the entry-200-300 cc cluster with a 0.5 s band. Treat both ETs as physics-based estimates, not guaranteed strip times.',
  },
  {
    type: 'h2',
    text: 'Why the gap is engine power, not mass',
  },
  {
    type: 'p',
    text: 'On a short drag strip, low mass matters most in the first 30 metres, where traction and inertia dominate, and less as the bike nears terminal velocity in 5th gear. The Hornet 2.0\'s 18 kg weight advantage saves roughly 0.15 seconds in the first 60 feet, and in the simulator the Hornet is marginally faster through the very first part of the run despite carrying 7.2 hp less.',
  },
  {
    type: 'p',
    text: 'From 60 feet onward, engine output takes over. The NS200\'s short-stroke geometry (a 72 mm bore against the Hornet\'s 64 mm) allows more power output per revolution while keeping mean piston speed under control. The DOHC 4-valve head breathes more freely at 8,000-9,000 rpm than the Hornet\'s SOHC 2-valve. By the 1/8-mile mark the NS200 is roughly 0.7 seconds clear, and it extends that gap to 1.65 seconds by the 402 m mark as the Hornet runs out of engine at the top of 5th gear.',
  },
  {
    type: 'p',
    text: 'The Hornet 2.0\'s long-stroke 64 × 57 mm layout (bore-to-stroke ratio 1.12:1) is deliberately tuned for low-end torque and smooth delivery, which helps in city traffic and not on a drag strip. With the torque peak at 6,500 rpm the bike pulls reasonably well through the first three gears, but the 17 hp ceiling limits top-end acceleration. By 5th gear the Hornet makes roughly 9 kW of wheel power against the NS200\'s 16 kW, and that 7 kW gap becomes the 1.65 s ET difference.',
  },
  {
    type: 'h2',
    text: 'Gearing: where the Hornet partly compensates',
  },
  {
    type: 'p',
    text: 'In one place the Hornet 2.0 is set up more aggressively than the NS200: its 5th-gear ratio. The Hornet runs a 0.688 fifth gear against the NS200\'s 0.971, a deeper overdrive by a wide margin. Paired with a F16/R46 final drive against the NS200\'s F16/R48, the Hornet\'s overall top-gear ratio is shorter than the NS200\'s, so the Hornet can rev closer to peak power at trap speed instead of lugging in a taller gear. That partly makes up for the power deficit in the low-speed stages of the run.',
  },
  {
    type: 'p',
    text: 'In the simulator log, the Hornet reaches 5th gear at roughly the same distance as the NS200 (around 250 metres) and holds engine speed reasonably close to its 8,500 rpm power peak all the way to the 402 m mark. The NS200 does the same with its own 0.971 fifth. The Hornet\'s gearing advantage is real but modest: if the Hornet ran the same overdrive 5th gear as the NS200 (0.971), its sim ET would be roughly 0.3 seconds slower. Honda\'s engineers chose the right ratio for a modest-power single.',
  },
  {
    type: 'h2',
    text: 'Can the Hornet 2.0 close the gap with mods?',
  },
  {
    type: 'p',
    text: 'No, not without engine work. Both bikes share the same 520-pitch chain, the same 17-inch wheel set, and similar tire profiles, so the basic mod order is the same. But the Hornet 2.0 starts 1.65 seconds behind, and the Indian parts catalog for a 184cc oil-cooled SOHC 2-valve single is much thinner than the NS200\'s after fourteen years on sale.',
  },
  {
    type: 'table',
    rows: [
      ['Mod', 'Hornet 2.0 ΔET', 'NS200 ΔET', 'Indian price (approx.)', '₹/tenth (Hornet 2.0)'],
      ['Front sprocket drop (16F → 15F)', '~0.18 s', '~0.20 s', '₹900', '₹500'],
      ['Sport tire upgrade (MRF Zapper FY1)', '~0.16 s', '~0.18 s', '₹5,800', '₹3,600'],
      ['Slip-on exhaust (KustomHub / Big Bird)', '~0.07 s', '~0.10 s', '₹7,000–12,000', '₹10,000–17,000'],
      ['ECU piggyback / re-flash (aftermarket)', '~0.05 s', '~0.15 s', '₹8,000–14,500', '₹16,000–29,000'],
    ],
  },
  {
    type: 'p',
    text: 'As on every other Indian 180-200cc naked, the sprocket swap and tire upgrade are the cheapest tenths. Dropping to a 15T front sprocket shortens the overall drive ratio by about 6 percent, which keeps the engine near its torque peak for more of each gear. On the Hornet 2.0 this buys roughly 0.18 seconds, similar to the NS200, because both bikes are gearing-limited in the lower gears rather than traction-limited.',
  },
  {
    type: 'p',
    text: 'The Hornet 2.0 falls behind on ECU tuning. The NS200 has a large aftermarket for Powertronic, Aracer, and Bazzaz flashes, which add roughly 1.5-2.0 hp above 8,000 rpm, where the OEM map is conservative. The Hornet 2.0 has a much thinner ECU re-flash market in India: Honda\'s FI map is already near the engine\'s mechanical limit at 17 hp, so there is less headroom. An aftermarket piggyback on the Hornet 2.0 buys roughly 0.05 seconds versus the NS200\'s 0.15. The ₹/tenth ratio is three times worse.',
  },
  {
    type: 'p',
    text: 'Taking the Hornet 2.0 from ~17.55 s to roughly 17.05 s costs approximately ₹15,000 (sprocket + tire + exhaust). Taking the NS200 from ~15.9 s to roughly 15.0 s costs approximately ₹26,200 (sprocket + tire + ECU flash). Both are reasonable entry-level drag budgets, but the Hornet 2.0 has a lower ceiling: its engine allows few further gains without a head rebuild or a forced-induction kit, and neither has an established Indian market at this displacement.',
  },
  {
    type: 'callout',
    text: 'The Hornet 2.0 will not break 17 seconds on an Indian strip without significant engine work. The NS200, with a ₹26,000 mod budget, can regularly break 15.0 seconds. Tuning will not close the gap: it comes from the two engine designs and the power-to-weight they give.',
  },
  {
    type: 'h2',
    text: 'Where the Hornet 2.0 wins',
  },
  {
    type: 'p',
    text: 'At a drag strip the NS200 wins clearly. Everywhere else the comparison is closer. The Hornet 2.0 is 18 kg lighter than the NS200, which matters on tight Indian city roads and low-speed manoeuvring. Its SOHC 2-valve engine with a long stroke runs cooler, requires less frequent valve adjustments, and is more tolerant of mixed-quality fuel. Honda India\'s service network is denser than Bajaj\'s in many tier-2 and tier-3 cities.',
  },
  {
    type: 'p',
    text: 'The Hornet 2.0\'s power delivery is also friendlier for newer riders. The torque curve is flatter and the peak comes at 6,500 rpm (the same rpm as the NS200\'s torque peak), but the Hornet\'s lower absolute power output means a rider mistake at the strip results in a slower run rather than a traction-breaking wheelie. For a rider who wants to try Indian strip meets without the NS200\'s sharper character, the Hornet 2.0 is a reasonable learner platform.',
  },
  {
    type: 'p',
    text: 'In mid-2026 the Hornet 2.0 costs roughly ₹1.35 lakh ex-showroom and the NS200 roughly ₹1.61 lakh. The ₹26,000 difference is almost exactly the cost of the NS200\'s Tier-1 mod stack above. Buying the NS200 at stock and adding the ₹26,000 mod budget costs roughly the same as a stock NS200 alone: ₹1.87 lakh versus ₹1.35 lakh for the Hornet 2.0. For a buyer who just wants to commute and do occasional strip runs, the Hornet 2.0 is rational. For a buyer who wants the fastest 200cc Indian bike for the money at the strip, the NS200 wins easily.',
  },
  {
    type: 'h2',
    text: 'The third bike to consider',
  },
  {
    type: 'p',
    text: 'Anyone comparing the Hornet 2.0 and NS200 should also look at the TVS Apache RTR 200 4V, which sits between them on almost every measure. The Apache runs ~16.4 seconds stock, weighs 142 kg (same as the Hornet 2.0), makes 20.2 hp, and comes with a factory slipper clutch. It costs roughly ₹1.49 lakh ex-showroom: ₹14,000 more than the Hornet 2.0, ₹12,000 less than the NS200.',
  },
  {
    type: 'p',
    text: 'For a buyer choosing between all three: the Hornet 2.0 is the cheapest and lightest, the Apache RTR 200 4V is the best value for strip use (slipper clutch, 20 hp, same mass as the Hornet), and the NS200 is the fastest of the three. If strip performance matters most, the ₹12,000 premium for the NS200 over the Apache buys roughly 0.5 seconds of ET and a far deeper aftermarket. If overall value matters most, the Apache is the pick. If budget is the hard constraint and the strip is occasional, the Hornet 2.0 is the pragmatic choice.',
  },
  {
    type: 'h2',
    text: 'Run your own numbers',
  },
  {
    type: 'p',
    text: 'Under matched stock conditions the Bajaj Pulsar NS200 beats the Honda Hornet 2.0 by roughly 1.65 seconds of ET. That gap is larger than the full spread of the 200cc Indian naked segment, and no bolt-on mod combination at a reasonable budget closes it. It comes from seven horsepower, and those seven horsepower come from the engine design: a 17 hp SOHC 2-valve long-stroke commuter against a 24 hp DOHC 4-valve short-stroke performance single.',
  },
  {
    type: 'p',
    text: 'The MotoQuant simulator at motoquant.in lets you run both bikes at any Indian venue with any combination of tire, sprocket, exhaust, and ECU flash from the full Indian parts catalog. You can also sweep rider weight (the Hornet 2.0\'s 18 kg mass advantage matters more at 60 kg rider weight than at 90 kg) and ambient conditions. If you have a Dragy timeslip from either bike at an Indian strip, submit it through the "Submit a timeslip" form; a reviewed run joins the benchmark set.',
  },
  {
    type: 'p',
    text: 'The simulator for this comparison is pre-configured at the link below with both bikes at Aamby Valley November conditions, 70 kg rider, stock tune. Adjust rider weight, temperature, and tire choice to match your own strip. If you are choosing between the NS200 and the Apache RTR 200 4V, the real rivals in this segment, the post linked below compares those two in full.',
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
            {['Honda', 'Hornet 2.0', 'Bajaj', 'Pulsar NS200', 'Indian 200cc', 'comparison'].map((t) => (
              <span
                key={t}
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Honda Hornet 2.0 vs Pulsar NS200: which wins the quarter mile?
          </h1>
          <div className="text-sm text-white/60 mb-12">
            25 May 2026 · 12 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        <PostBikeLinks ids={[86]} />

        <div className="max-w-2xl mx-auto mt-16 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Simulate Hornet 2.0 vs NS200 side by side</div>
            <div className="text-white/60 text-sm">Pick both bikes at Aamby Valley, sweep rider weight, swap tires and sprockets, and see whether the 1.65 s gap shrinks before you spend a rupee on mods.</div>
          </div>
          <Link
            href="/simulator?bike=hornet-2.0&venue=aamby-valley"
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
              <Link href="/blog/pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                Pulsar NS200 vs Apache RTR 200 4V: which wins the quarter mile?
              </Link>:{' '}
              the NS200 against its toughest Indian rival. The Apache is 18 kg lighter and carries a slipper clutch; the NS200 wins by half a second on engine power alone.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/hero-xtreme-200s-4v-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                Hero Xtreme 200S 4V quarter-mile physics
              </Link>:{' '}
              the third 200cc Indian commuter-sport, at ~17.40 s and directly comparable to the Hornet 2.0 cluster. It shows why a 4-valve 200cc single is still slower than a 4-valve 200cc short-stroke when the gearing is too tall.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/why-your-r15-wont-hit-14s" className="text-brand-accent hover:text-brand-orange transition-colors">
                Why your R15 won&apos;t hit 14s
              </Link>:{' '}
              the same gearing-and-traction story one displacement class down, with the R15 V4 at ~17.62 s real-world. Most of the lessons on clutch slip and launch RPM apply to the Hornet 2.0 directly.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/the-physics-of-a-perfect-launch" className="text-brand-accent hover:text-brand-orange transition-colors">
                The physics of a perfect launch
              </Link>:{' '}
              the first 60 feet, where the Hornet 2.0&apos;s 18 kg mass advantage counts most: clutch slip, weight transfer, and why launch RPM matters more than engine power in the opening metres.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>:{' '}
              Honda Hornet 2.0, Pulsar NS200, Apache RTR 200 4V, Hero Xtreme 200S 4V, and 350+ other bikes with full spec sheets and OEM tire fitments.
            </li>
          </ul>
        </div>
      </article>

      <SiteFooter />
    </div>
  );
}
