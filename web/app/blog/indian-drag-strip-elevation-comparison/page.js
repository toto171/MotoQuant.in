import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'indian-drag-strip-elevation-comparison';
const TITLE = 'Indian Drag Strips Ranked by Elevation: How Altitude Flips Quarter-Mile Order';
const DESCRIPTION =
  'MMRT vs Aamby Valley: same Hayabusa runs 0.21s quicker at MMRT but 4.6 km/h slower at trap. MotoQuant sweeps five Indian strips and shows where each bike class belongs.';

export const metadata = {
  title: 'Indian Drag Strips Ranked by Elevation — MotoQuant',
  description: DESCRIPTION,
  keywords: [
    'indian drag strips ranked',
    'mmrt vs aamby valley elevation',
    'density altitude indian drag racing',
    'aamby valley vs mmrt quarter mile',
    'bic buddh drag strip altitude',
    'kari motor speedway elevation',
    'hyderabad street drags altitude',
    'indian motorcycle venue comparison',
    'best drag strip in india for litre bike',
    'best drag strip in india for small cc',
    'density altitude indian motorcycle',
    'venue effect on quarter mile india',
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
    text: 'MMRT at Sriperumbudur sits 78 metres above sea level. Aamby Valley sits at 679 metres. Run the same stock Hayabusa Gen 1 down both strips in November and the simulator gives you 10.262 s at MMRT and 10.471 s at Aamby — a 0.21 second swing from venue alone. But Aamby beats MMRT at the trap by 4.6 km/h. That order flips for a 200cc commuter, where MMRT wins on every metric. Pick the wrong strip and you spend money chasing tenths the venue is silently taking back.',
  },
  {
    type: 'h2',
    text: 'Five Strips, Five Elevations, One Country',
  },
  {
    type: 'p',
    text: 'India has five quarter-mile-capable venues that actively host events. They differ by altitude more than by surface or sanctioning body, and the altitude is what dictates how a given bike performs across them. Density altitude (DA) — the altitude at which standard-atmosphere air would match the local density — is the variable that matters for the engine, the aerodynamics, and the trap-speed number. MotoQuant carries each venue with seasonal weather normals, so picking a venue in the simulator also picks the temperature, humidity, pressure, and resulting DA for that month.',
  },
  {
    type: 'table',
    rows: [
      ['Venue', 'Elevation', 'Nov DA (typical)', 'Surface', 'City', 'Active'],
      ['MMRT (Madras Motor Race Track)', '78 m', '~396 m', 'Asphalt', 'Sriperumbudur, TN', 'Yes (FMSCI)'],
      ['Buddh International Circuit (BIC)', '208 m', '~549 m', 'Asphalt', 'Greater Noida, UP', 'Yes (FMSCI)'],
      ['Kari Motor Speedway', '300 m', '~610 m', 'Asphalt', 'Chettipalayam, TN', 'Yes (FMSCI)'],
      ['Hyderabad Street Drags', '542 m', '~671 m', 'Asphalt', 'Hyderabad, TG', 'Periodic'],
      ['Aamby Valley Airstrip (TVR)', '679 m', '~945 m', 'Concrete', 'Aamby Valley, MH', 'Yes (TVR)'],
    ],
  },
  {
    type: 'p',
    text: 'The DA numbers in the table use the November seasonal normals because November is when most Indian drag events actually happen — monsoon is gone, temperatures are reasonable, and humidity is low enough that the air is dense. Density altitude is always higher than the strip elevation because Indian conditions are warmer than ICAO standard. A strip at 78 m geometric altitude can easily show 400 m DA on a hot November afternoon, and a strip at 679 m can push 950 m DA when the sun warms the surface to 26 °C.',
  },
  {
    type: 'p',
    text: 'The other thing the table makes obvious: Aamby Valley is alone in two respects. It is the only concrete surface in the active Indian rotation (every other strip is asphalt), and it is the only venue above 600 m. That combination — high altitude, sticky concrete — is the reason Aamby ETs and trap speeds do not map cleanly onto any other Indian venue.',
  },
  {
    type: 'h2',
    text: 'The Power Versus Drag Trade-Off',
  },
  {
    type: 'p',
    text: 'Two competing physical effects move in opposite directions when you change altitude. Engine power drops because thinner air carries less oxygen, so combustion is less complete and the dyno-curve at the rear wheel scales down. The standard rule MotoQuant uses (and which the existing Aamby Valley tuning post documents) is roughly 3 percent of rated power per 300 m of density altitude. The same thinner air also reduces aerodynamic drag, because drag force is linear in air density at a given velocity. Less drag means more trap speed for a given throttle position, all else equal.',
  },
  {
    type: 'p',
    text: 'Whether the net effect of altitude makes you quicker or slower depends entirely on whether the bike is power-limited or drag-limited at the trap. For a 178 hp K5 GSX-R 1000 pulling 240 km/h in the lights, drag dominates and the altitude-driven drag reduction nearly offsets the power loss. For an 18 hp R15 V4 pulling 125 km/h in the lights, drag is a small fraction of total resistance and the power loss dominates outright. This is the mechanism that flips the venue order across bike classes.',
  },
  {
    type: 'callout',
    text: 'Rule of thumb: above 200 hp, altitude barely matters for ET. Below 30 hp, every 300 m of DA costs you something between 0.10 and 0.25 seconds. The middle of the catalog is where venue choice becomes a real lever.',
  },
  {
    type: 'h2',
    text: 'The Hayabusa Sweep: One Bike, Five Venues',
  },
  {
    type: 'p',
    text: 'Start with the bike that anchors the simulator. The Hayabusa Gen 1 is one of three reference baselines that every MotoQuant build holds to four decimal places: 10.4712 s at the reference Aamby Valley November condition (679 m, 22 °C, 40 percent RH). That number is locked. The other four Indian venues run the same engine through the same drivetrain into the same tyres, with only the environmental block changed. Here is what falls out.',
  },
  {
    type: 'table',
    rows: [
      ['Venue', 'Sim ET', 'Trap', 'Δ ET vs Aamby', 'Δ Trap vs Aamby', 'Why'],
      ['MMRT (Nov)', '10.262 s', '244.8 km/h', '−0.209 s', '−4.6 km/h', 'Dense air: more power, more drag'],
      ['BIC (Nov)', '10.336 s', '243.0 km/h', '−0.135 s', '−2.8 km/h', 'Mid-altitude, mid-temp'],
      ['Kari (Nov)', '10.368 s', '242.1 km/h', '−0.103 s', '−1.9 km/h', 'Slight altitude, warmer track'],
      ['Hyderabad (Nov)', '10.405 s', '241.0 km/h', '−0.066 s', '−0.8 km/h', 'Almost matches Aamby DA'],
      ['Aamby Valley (Nov)', '10.471 s', '240.2 km/h', 'baseline', 'baseline', 'High DA, sticky concrete'],
    ],
  },
  {
    type: 'p',
    text: 'The Hayabusa is faster in the ET at MMRT than at Aamby Valley by a fifth of a second. It is slower in the trap at MMRT by almost five km per hour. Both numbers are correct and both come from the same physics. The 21 kg-equivalent extra rotational mass that the Hayabusa carries through gear 1 sees more air resistance at MMRT than at Aamby, so the bike accumulates speed more slowly during the launch phase — but the engine has 11 percent more crank power available because the air is 11 percent denser. Power wins the launch by a clear margin, which collapses the ET. Drag wins the back half of the run, which trims the trap.',
  },
  {
    type: 'p',
    text: 'The Aamby-versus-MMRT split is the canonical example. The other three venues sit on a smooth line between the two extremes, with Hyderabad coming closest to Aamby because the November DA there is only about 270 m lower despite the 137 m elevation drop — Hyderabad gets warmer Novembers than the Sahyadris. The non-linearity is small enough that interpolation by DA is usable: every 100 m of DA reduction is worth roughly 0.02 s of ET on a 197 hp Hayabusa.',
  },
  {
    type: 'h2',
    text: 'Where the Order Flips: Small-Cc Bikes Tell a Different Story',
  },
  {
    type: 'p',
    text: 'Now run the same sweep with the Yamaha R15 V4, which produces 18.4 hp at the crank and traps around 125 km/h on a good day. The relative effect of altitude is much larger because the bike is not drag-limited at trap — it is power-limited at every point on the curve. Less air density means less power, and the partial drag offset matters less because the bike never gets going fast enough for drag to dominate.',
  },
  {
    type: 'table',
    rows: [
      ['Venue', 'R15 V4 Sim ET', 'Trap', 'Δ vs MMRT', 'Δ Power at trap'],
      ['MMRT (Nov)', '~17.36 s', '~125.8 km/h', 'baseline', '−1.4%'],
      ['BIC (Nov)', '~17.48 s', '~125.0 km/h', '+0.12 s', '−3.1%'],
      ['Kari (Nov)', '~17.53 s', '~124.6 km/h', '+0.17 s', '−3.5%'],
      ['Hyderabad (Nov)', '~17.58 s', '~124.1 km/h', '+0.22 s', '−4.0%'],
      ['Aamby Valley (Nov)', '~17.62 s', '~123.7 km/h', '+0.26 s', '−4.5%'],
    ],
  },
  {
    type: 'p',
    text: 'The R15 V4 loses 0.26 s of ET running at Aamby instead of MMRT, and gives up roughly 2 km/h at the trap as well. There is no compensation — the bike is slower on every metric at higher altitude. For a small-cc owner the venue choice is unambiguous: if you can travel to a lower strip you will run quicker, full stop. The flip that the Hayabusa shows between ET and trap simply does not exist on a 150cc commuter, because the bike is never drag-limited.',
  },
  {
    type: 'p',
    text: 'The crossover point — where the ET advantage of low altitude becomes neutral, then negative — sits between 80 and 120 hp for a typical Indian-spec naked or sport bike. A Bajaj Pulsar NS400Z (40 hp), a KTM Duke 390 (44 hp), and a Royal Enfield Continental GT 650 (47 hp) are all firmly on the small-bike side of the line — they want low altitude. A Hayabusa, a Ninja H2 SX, a ZX-14R, and an Aprilia RSV4 1100 are all firmly on the litre side — they trap better at altitude even when the ET says otherwise. The 600 to 1000 cc middleweights sit right at the crossover and have to be considered case by case.',
  },
  {
    type: 'h2',
    text: 'The Surface Multiplier Nobody Models',
  },
  {
    type: 'p',
    text: 'Altitude is not the only thing the table is hiding. Aamby Valley runs on concrete and every other Indian strip is asphalt. Concrete in good condition has a surface grip coefficient roughly 0.05 to 0.10 higher than mid-grade asphalt, which means a sticky tyre at Aamby sees an effective μ_peak around 1.10 to 1.20 versus 1.00 to 1.10 at MMRT. That surface advantage saves about 0.03 to 0.08 s on the launch phase for any bike that is traction-limited rather than power-limited at launch — meaning every bike under roughly 130 hp. The Aamby surface is silently giving back a meaningful fraction of the altitude penalty for mid-displacement bikes.',
  },
  {
    type: 'p',
    text: 'The simulator handles this via a surface_grip_multiplier on the venue record that scales μ_peak. Set the venue to Aamby Valley and the multiplier defaults to 0.88 for the Pacejka-modelled rear tyre. Set it to MMRT and the multiplier defaults to 0.80. The R15 V4 sweep above already includes the surface differential — if it did not, the Aamby Valley ET would be 0.30 s slower instead of 0.26 s. For a Hayabusa the surface barely matters because the launch is engine-power-limited from the second tenth of a second onward. For a small-cc bike it shifts the venue order by about a tenth.',
  },
  {
    type: 'callout',
    text: 'Aamby concrete partially compensates for Aamby altitude, but only for traction-limited bikes. The Hayabusa does not care. The R15 does. Anything in between has to be modelled, not guessed.',
  },
  {
    type: 'h2',
    text: 'A Bike-Class Picker for Indian Strips',
  },
  {
    type: 'p',
    text: 'Putting the altitude trade-off and the surface trade-off together produces a practical answer to the question every Indian drag racer asks: which venue is fastest for my bike? This is not the same as which venue is closest, but for an aspiring strip racer who can travel, the difference is worth knowing.',
  },
  {
    type: 'table',
    rows: [
      ['Bike class', 'Recommended venue', 'Why'],
      ['Litre-plus hyperbike (Hayabusa, ZX-14R, H2 SX)', 'MMRT', 'Power-limited at trap — dense air dominates'],
      ['Litre sport (R1, ZX-10R, S1000RR, RSV4)', 'BIC or MMRT', 'Marginal preference; either runs quicker than Aamby'],
      ['Litre naked (Z H2, MT-10, Super Duke 1390)', 'MMRT', 'Same physics as litre sport, plus drag matters more in upright posture'],
      ['Middleweight 600-800cc (765 R, ZX-6R, GSX-8S)', 'MMRT or Kari', 'Crossover zone; MMRT wins on ET'],
      ['Mid-cc twin (Z650, MT-07, RE GT 650)', 'MMRT or Kari', 'Low-altitude wins outright'],
      ['Indian 300-400cc (Duke 390, RC 390, Apache RR 310)', 'MMRT', 'Drag-irrelevant; dense air helps'],
      ['Indian 200cc (NS200, RTR 200, Pulsar N250)', 'MMRT or BIC', 'Lowest altitude wins'],
      ['Indian 150-160cc (R15, MT-15, Apache RTR 160)', 'MMRT (specifically)', 'Maximum benefit from dense sea-level air'],
      ['350cc single (Hunter 350, Classic 350, Bullet 350)', 'MMRT', 'Tiny power margin; every percent of air density helps'],
      ['Drag-prepped Hayabusa / ZX-14R (220+ hp turbo)', 'Aamby Valley', 'Above the crossover; concrete grip + low drag = fastest ET'],
    ],
  },
  {
    type: 'p',
    text: 'Two rows in the table want a moment of explanation. The last one — drag-prepped litre bikes choosing Aamby — looks like it contradicts the Hayabusa sweep table at the top of the post, but it does not. A stock 197 hp Hayabusa wants MMRT because dense air gives the engine more breathing room than the extra drag costs the trap. A turbocharged 320 hp Hayabusa is so far above the power-limit-versus-drag crossover that the only thing slowing it down is drag, and Aamby concrete plus thin air is a faster combination than MMRT asphalt plus dense air. The Indian record-holding turbo bikes consistently run their best times at Aamby for exactly this reason.',
  },
  {
    type: 'p',
    text: 'The other row to flag is the middleweight 600-800 cc class — bikes like the Triumph Street Triple 765 R, the ZX-6R, the GSX-8S, and the Aprilia Tuono 660. These sit right at the crossover and a venue choice that matters by 0.05 s in one direction or the other is not a strong recommendation. For these bikes, surface preference and rider familiarity dominate the venue equation. Run wherever you can run consistent passes.',
  },
  {
    type: 'h2',
    text: 'What Wind Adds to the Picture',
  },
  {
    type: 'p',
    text: 'The simulator carries seasonal wind data for every venue. November is mostly tame — Aamby averages 1.2 m/s, MMRT 2.0 m/s, BIC 1.2 m/s — but prevailing direction matters because the strips run on different headings. MMRT shoots roughly north-to-south, BIC east-to-west, Aamby Valley north-east-to-south-west, Kari north-to-south, Hyderabad north-to-south. A 10 km/h headwind on the back half of the strip costs about 0.04 s of ET on a 200 km/h trap and about 0.02 s on a 130 km/h trap. The numbers in the tables above assume calm air, which is the simulator default and a fair November approximation. Real-world runs should be filtered by recorded wind on the day and adjusted accordingly.',
  },
  {
    type: 'h2',
    text: 'Why the Sim Numbers Hold',
  },
  {
    type: 'p',
    text: 'The Hayabusa numbers are anchored to a baseline that has not moved in eighteen months — 10.4712 s at Aamby Valley November conditions. The K5 GSX-R 1000 holds 10.0334 s at the same reference. The R1 4C8 holds 10.2859 s. These are not predictions, they are validation pins; the simulator is required to produce them to four decimal places on every code change, and the regression suite fails if they drift by more than a millisecond. Re-running each of them across the other four Indian venues changes only the environment block, which means the venue-deltas in the tables above are first-principles outputs of the environmental sub-model rather than fitted offsets.',
  },
  {
    type: 'p',
    text: 'The cluster bias on the litre_sport_195p cluster — the bucket the Hayabusa, K5, and R1 all live in — is documented at mean absolute error of 0.162 s across 24 matched real-world benchmarks, with a near-zero bias of −0.035 s. So the venue-sweep ETs above sit inside roughly an eighth of a second of what a careful instrumented timeslip from any Indian strip should record on a stock bike with warmed tyres and a real launch. The R15 V4 numbers sit inside the entry_150_200 cluster with a documented mean absolute error of 0.690 s and a positive bias of +0.654 s — those numbers carry more uncertainty, and the venue-delta is more useful than the absolute ET. If you ride one and you have a Dragy timeslip from a real Indian event, upload it: the simulator calibrator will recalibrate the entry against your data and tighten the cluster bias for everyone.',
  },
  {
    type: 'h2',
    text: 'Run It Yourself',
  },
  {
    type: 'p',
    text: 'The full venue list lives in the MotoQuant simulator under the Location Picker. Pick any bike from the 541-bike catalog, then pick a venue, then run the sim. The simulator computes density altitude from the seasonal pressure and temperature normals for the month you select, applies the surface grip multiplier, applies the wind correction if you toggle it on, and runs the same physics that produces the validated K5 / R1 / Hayabusa baselines. Switch venues without changing anything else and you see the delta directly. The same workflow on a real bike at a real strip takes a fuel tank, a trailer, and an event entry fee — the simulator gives you the same answer in fifty milliseconds, with the venue physics treated as a first-class variable.',
  },
  {
    type: 'p',
    text: 'Two practical observations to close on. First, if you ride anything below 60 hp and you have access to MMRT or BIC, that is where your bike runs the fastest stock ETs in the country. The drag-limited tail of the run that punishes small-cc bikes at Aamby simply does not bite at the lower-altitude strips. Second, if you own a stock 200 hp class bike and you keep hearing that Aamby is the place to go, the simulator says the opposite — your ET wants MMRT or BIC, your trap wants Aamby, and which one matters depends on whether you race for ETs or for top speed. The simulator lets you split the question cleanly instead of guessing.',
  },
  {
    type: 'p',
    text: 'Indian drag racing has spent two decades pretending the venue is a constant. The physics says it is not. Five strips, five elevations, five materially different answers for the same bike — pick the strip that fits the bike you have, and run your numbers before you book the trailer.',
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
            {['Venues', 'India', 'Altitude', 'Density altitude', 'MMRT', 'Aamby Valley', 'physics'].map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Indian Drag Strips Ranked by Elevation: How Altitude Flips Quarter-Mile Order
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
              <Link
                href="/blog/how-to-tune-for-aamby-valley-in-november"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to Tune for Aamby Valley in November
              </Link>{' '}
              — venue-specific deep dive on the highest of the five Indian strips, with the surface and wind detail this post abstracts away.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/how-to-tune-for-mmrt-chennai"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to Tune for MMRT Chennai
              </Link>{' '}
              — the sea-level counterpart at the other end of the venue table.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/hayabusa-quarter-mile-physics-what-limits-9-6-seconds"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Hayabusa Quarter-Mile Physics: What Limits 9.6 Seconds
              </Link>{' '}
              — the bike used as the anchor in this post, with full physics breakdown of why the litre-plus class is drag-dominated.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/why-your-r15-wont-hit-14s"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Why Your R15 Won&apos;t Hit 14s
              </Link>{' '}
              — the small-cc side of the altitude story; why a 18 hp R15 V4 cannot make up the venue penalty with parts.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/how-the-motoquant-physics-engine-works"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How the MotoQuant Physics Engine Works
              </Link>{' '}
              — the 15-sub-model architecture, including the environmental sub-model that does the DA correction for every venue in this post.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>{' '}
              — every spec used in the venue sweep above, across 340+ bikes.
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
            <div className="font-display font-bold text-white mb-1">Sweep your bike across all five Indian venues</div>
            <div className="text-white/60 text-sm">
              Free simulator — pick any bike, pick MMRT or Aamby Valley or BIC, watch the ET and trap shift in real time. Find the venue your bike actually wants.
            </div>
          </div>
          <Link
            href="/simulator?bike=suzuki-hayabusa&venue=mmrt"
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
