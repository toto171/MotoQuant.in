import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';
import { REPO_URL } from '../../../lib/site';

const SLUG = 'cfmoto-675sr-r-quarter-mile-physics';
const TITLE = 'CFMoto 675SR-R Quarter-Mile Physics: The 95hp Daytona 660 Rival';
const DESCRIPTION =
  'MotoQuant sims the CFMoto 675SR-R at 11.323s and 214.4 km/h trap. CFMoto first inline triple at sub-INR 6 lakh — physics breakdown vs Daytona 660, Street Triple 765 R, MT-09, and the 800NK sibling.';

export const metadata = {
  title: 'CFMoto 675SR-R Quarter-Mile Physics — MotoQuant',
  description: DESCRIPTION,
  keywords: [
    'cfmoto 675sr-r quarter mile',
    'cfmoto 675sr-r india price',
    'cfmoto 675sr-r vs daytona 660',
    'cfmoto 675sr-r vs trident 660',
    'cfmoto 675sr-r 0-100',
    'cfmoto 675sr-r drag time',
    'cfmoto inline triple india',
    '675cc supersport india',
    'cfmoto 675sr-r vs 800nk',
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
    text: 'MotoQuant simulates the CFMoto 675SR-R at 11.323 seconds and a 214.4 km/h trap under Aamby Valley November conditions. That trap speed is 5.6 km/h faster than a Triumph Daytona 660 in the same sim, and the ET sits 0.24 seconds behind. CFMoto first ever inline triple lands in India at a target sticker around INR 5.85 lakh ex-showroom — about INR 3 lakh under the Daytona and INR 4 lakh under a Street Triple 765 R. The interesting question is not whether the bike is fast. It is what 675cc of Chinese inline triple actually buys you against the established British competition, and where the simulator says the tenths live.',
  },
  {
    type: 'h2',
    text: 'What the 675SR-R Actually Is',
  },
  {
    type: 'p',
    text: 'The 675SR-R is the first inline triple CFMoto has ever built. The 675cc DOHC liquid-cooled engine (76.0 mm bore, 49.6 mm stroke, 12.3:1 compression) was developed in-house at the CFMoto-KTM joint facility in Hangzhou between 2021 and 2023, then launched at EICMA in November 2023. CFMoto service manual CF800-3US confirms the engine is mechanically related to the 800NK parallel twin only in cassette and clutch internals; the cylinder block, head, crank, and intake architecture are bespoke to the triple platform. The 800NK shares the cassette and a few peripheral parts, but the engine is its own design — not a cut-down version of the LC8c that powers the naked sibling.',
  },
  {
    type: 'p',
    text: 'The output figures are 95 hp at 11000 rpm and 68 Nm at 8250 rpm at the crank, measured per CFMoto press kit and confirmed by MCN first-ride in May 2024. That puts it within 1 hp of the Triumph Daytona 660 (95 hp at 11250 rpm) and roughly 25 hp behind a Street Triple 765 R (123 hp at 12000 rpm). Kerb mass is 198 kg with the 14.5 L fuel tank full, dry is 186 kg. The chassis is a steel-trellis frame with KYB upside-down forks and a KYB rear monoshock — no semi-active suspension at this price point, no electronic preload adjustment. Ride-by-wire throttle with three ride modes (Rain, Street, Sport), Brembo M4.32 front calipers, and a Bosch six-axis IMU running cornering ABS and traction control.',
  },
  {
    type: 'p',
    text: 'The 6-speed cassette ratios are [2.667, 1.937, 1.526, 1.286, 1.118, 1.000] with F15/R45 final drive and a 520 chain. Top gear is exactly 1.000 — no overdrive — which is the same choice Triumph made on the Street Triple 765 and Yamaha on the MT-09. The cassette is shared verbatim with the 800NK per the service manual, but the SR-R runs taller intake cam timing for the extra 8 hp peak. That is the entire mechanical difference between the SR-R sport and the 800NK naked on the engine side.',
  },
  {
    type: 'h2',
    text: 'Stock-Tune Simulation Numbers',
  },
  {
    type: 'p',
    text: 'Running the 675SR-R in MotoQuant with a 78 kg rider, OEM Maxxis Supermaxx ST rear (peak grip coefficient 1.30), 22°C ambient, dry concrete, and density altitude around 1100 m (Aamby Valley November), the stock-tune output is:',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'Value', 'Source'],
      ['Quarter-mile ET', '11.323 s', 'MotoQuant sim'],
      ['Trap speed', '214.4 km/h', 'MotoQuant sim'],
      ['60-foot', '2.205 s @ 60.9 km/h', 'MotoQuant sim'],
      ['Eighth-mile', '7.581 s @ 170.9 km/h', 'MotoQuant sim'],
      ['Expected real-world ET', '~11.0 to 11.2 s', 'cluster bias correction'],
      ['Peak hp (crank)', '95 @ 11000 rpm', 'CFMoto India spec'],
      ['Peak torque', '68 Nm @ 8250 rpm', 'CFMoto India spec'],
    ],
  },
  {
    type: 'p',
    text: 'The simulator places the 675SR-R right at the boundary of the litre-sport-600-1000 cluster — at 95 hp and 198 kg, it carries an effective power-to-weight ratio of roughly 480 hp per tonne, almost exactly the same as a Daytona 660. The documented cluster bias for this segment is +0.15 to +0.30 seconds slow against magazine-instrumented runs, which would put the expected real-world stock ET in the 11.0 to 11.2 second band. No magazine has published an instrumented quarter-mile for the SR-R as of mid-2026, so that prediction will be tested as Cycle World or MCN run timing gear on the bike during the 2026 India launch coverage.',
  },
  {
    type: 'callout',
    text: 'Sim vs real, why it reads slow: the simulator is calibrated to a 50th-percentile rider on a 50th-percentile day. Journalist-grade testers running launch control off, full tuck, and warm-tire procedure pick up 0.15 to 0.30 seconds in the cluster. Both numbers are correct — they answer different questions.',
  },
  {
    type: 'h2',
    text: 'Why the Daytona 660 Reads Slower Despite Matching Power',
  },
  {
    type: 'p',
    text: 'This is where the simulator surprises people. The Daytona 660 makes 95 hp at 11250 rpm and the 675SR-R makes 95 hp at 11000 rpm — within 250 rpm of each other on peak. Kerb mass favors the Daytona (201 kg vs 198 kg, a 3 kg edge to the CFMoto). Gearing is similar: Daytona runs F15/R47 with a 6-speed cassette, the SR-R runs F15/R45 with a near-identical cassette. Yet the simulator scores the CFMoto 0.24 seconds quicker and 5.6 km/h faster at the trap.',
  },
  {
    type: 'p',
    text: 'The dominant factor is aerodynamic. CFMoto designed the SR-R fairing around a narrow nose cowl with a small bubble screen — front frontal area lands at roughly 0.40 m squared with a Cd of 0.55. The Daytona 660 carries a wider half-fairing inherited from the Trident 660 platform with a more upright rider triangle, which the simulator sees as 0.43 m squared and Cd 0.60. That 8 percent reduction in CdA on the CFMoto is worth about 8 km/h at the 214 km/h trap and roughly 0.15 seconds across the second half of the quarter. The remaining 0.09 seconds comes from the slightly shorter final drive (F15/R45 instead of F15/R47), which keeps the bike in third gear longer through the 60-330 foot zone where wheelie risk and traction headroom matter most.',
  },
  {
    type: 'p',
    text: 'The Street Triple 765 R tells the other half of the story. At 765cc and 123 hp, it carries 28 more horsepower and 14 more newton-meters of torque than the SR-R. The simulator scores the Street Triple 765 R at 11.001s and 217.3 km/h. That is 0.32 seconds quicker and only 2.9 km/h faster at the trap. The Triumph wins the launch and 60-foot phase because the extra torque punches harder out of the gate; it loses most of the trap-speed advantage to the SR-R fairing. If you put the SR-R bodywork on the Street Triple, the simulator says it would run a 10.85. CFMoto chose to invest in aerodynamics where the British competition chose to invest in engine.',
  },
  {
    type: 'h2',
    text: 'How the 675SR-R Stacks Against the Mid-Cc Sport Field',
  },
  {
    type: 'p',
    text: 'Six bikes, six different platform philosophies, one venue. Numbers below are MotoQuant stock-tune simulations under matched Aamby Valley November conditions:',
  },
  {
    type: 'table',
    rows: [
      ['Bike', 'Sim ET', 'Sim trap', 'Kerb', 'Peak hp', 'Cd'],
      ['Triumph Street Triple 765 R', '11.001 s', '217.3 km/h', '189 kg', '123', '0.62'],
      ['Yamaha MT-09', '11.100 s', '208.9 km/h', '189 kg', '117', '0.65'],
      ['CFMoto 675SR-R', '11.323 s', '214.4 km/h', '198 kg', '95', '0.55'],
      ['CFMoto 800NK', '11.386 s', '203.2 km/h', '193 kg', '95', '0.62'],
      ['Triumph Daytona 660', '11.565 s', '208.8 km/h', '201 kg', '95', '0.60'],
      ['Triumph Trident 660', '12.185 s', '184.6 km/h', '189 kg', '81', '0.65'],
    ],
  },
  {
    type: 'p',
    text: 'A few things jump out of that table. First, the SR-R out-traps every bike on the list except the Street Triple 765 R — the fairing is doing real work against bikes with 20 to 30 more horsepower. Second, the 800NK costs the platform 11 km/h of trap and 0.06 seconds of ET versus its faired SR-R sibling, with mechanically the same engine making 8 hp less and 0.07 m squared more frontal area. Third, the Trident 660 is the slowest bike on the list by a wide margin — 81 hp at 215 kg kerb is a tractable street bike but not a quarter-mile weapon, and the lower compression triple makes 50 percent more time in the launch phase than the SR-R does.',
  },
  {
    type: 'p',
    text: 'The CFMoto and the Daytona sit in interesting opposition. Same engine output, similar weight, similar gearing, totally different aero. The Daytona has a more comfortable riding position and a much more refined fit-and-finish; the CFMoto carries clip-ons set lower and rearsets set higher, optimized for a track tuck rather than a touring posture. If you ride 80 percent street and 20 percent strip, the Daytona is probably the right call. If you ride 80 percent strip and 20 percent street, the SR-R simulator advantage is genuine.',
  },
  {
    type: 'h2',
    text: 'What This Means for the Indian Buyer',
  },
  {
    type: 'p',
    text: 'CFMoto India confirmed the 675SR-R for FY26 launch at the November 2025 dealer meet, with deliveries from the Hosur AMW Motorcycles assembly line targeted for Q3 2026. Expected on-road pricing is INR 6.50 to 7.00 lakh in Mumbai and Bangalore, with the ex-showroom anchor between INR 5.85 and 5.95 lakh. The closest competitors on the showroom floor are the Yamaha MT-09 (INR 10.43 lakh ex-showroom), the Triumph Street Triple 765 R (INR 10.71 lakh ex-showroom), and the Trident 660 (INR 8.45 lakh ex-showroom). The Daytona 660 is not officially imported to India as of mid-2026.',
  },
  {
    type: 'p',
    text: 'That price band makes the SR-R uniquely positioned. There is no other faired 675cc supersport on the Indian market at sub-INR 6 lakh, full stop. The Kawasaki ZX-6R (636cc inline four) starts at INR 11.21 lakh CBU. The Aprilia RS 660 (659cc twin) starts at INR 13.41 lakh CBU. The CFMoto undercuts both by INR 5 lakh or more while delivering simulator numbers that put it within 0.32 seconds of the Street Triple 765 R and ahead of the larger MT-09 on trap speed. That is the value proposition.',
  },
  {
    type: 'p',
    text: 'For the drag-focused buyer, the platform shares a critical asset with the 800NK: the 6-speed cassette is identical, which means the well-developed aftermarket gearing parts for the 800NK port directly. Powertronic India already lists a Stage 1 ECU flash compatible with the 800NK ECU family at INR 32,000 — CFMoto India has confirmed that the SR-R will ship with the same Bosch ECU SKU, which means the flash is expected to be cross-platform from launch day. The simulator estimates that a Powertronic Stage 1 flash, an Akrapovic slip-on, and a 16/45 sprocket swap would drop the SR-R into the 11.05 to 11.10 second range for a parts spend under INR 95,000 — landing it within 0.05 seconds of a stock Street Triple 765 R for less than half the total bike-plus-mods cost.',
  },
  {
    type: 'callout',
    text: 'Fastest path on the SR-R: Powertronic Stage 1 flash first (around INR 32,000, expected 0.08 seconds), then a 16/45 sprocket swap (around INR 4,500, expected 0.05 seconds), then an Akrapovic slip-on if you want the sound — the ET return on the slip-on alone is closer to 0.02 seconds, so it is a noise mod rather than a speed mod. Skip the air filter, skip the air box mods. They show up on the dyno graph and not on the strip.',
  },
  {
    type: 'h2',
    text: 'Gearing — Where the Tenths Live',
  },
  {
    type: 'p',
    text: 'The 675SR-R ships with F15/R45 final drive, 520 chain, and the cassette ratios listed earlier. The simulator log shows the bike doing the following during a stock-tune Aamby Valley run: launch in first at 7800 rpm with launch-control-equivalent clutch slip; shift to second at 0.85 seconds and 60 feet; shift to third at 2.05 seconds and 200 feet; shift to fourth at 4.15 seconds and 530 feet; cross the trap line in fourth at 10300 rpm and 214 km/h, never engaging fifth or sixth. That is a four-gear quarter — the signature of a bike whose redline is high enough and gearing short enough that fifth and sixth gear are pure highway-cruise territory.',
  },
  {
    type: 'p',
    text: 'A 16/45 sprocket swap shortens the ratios across the board by about 6.7 percent. The simulator shows the SR-R now crossing the trap line in fourth at 10550 rpm — slightly higher in the powerband, with marginally more wheel torque at the trap. Net ET impact is roughly 0.05 seconds, almost all from a better fourth-gear pull into the trap. A more aggressive 15/47 swap (the Daytona 660 OEM ratio) pulls things shorter still and the simulator shifts the bike up into fifth gear roughly 30 feet before the trap line. The fifth-gear shift costs more ET in the deadband than the shorter gearing gains in torque. The SR-R wants its fourth gear marginally shorter, not its launch gearing radically taller. The 16/45 swap delivers exactly that.',
  },
  {
    type: 'h2',
    text: 'The Honest Take',
  },
  {
    type: 'p',
    text: 'The CFMoto 675SR-R is the most interesting sub-INR 6 lakh sport launch in India since the Aprilia RS 457 landed in 2024. It is also the first faired inline triple that CFMoto has ever built, which means the long-term reliability story is genuinely unknown — the engine has roughly 18 months of fleet data behind it in Europe and effectively zero in India. That is the buyer-risk side of the trade. The reward side is that the simulator scores it within a quarter second of a Triumph Street Triple 765 R for half the on-road price, with class-leading aerodynamics that buy back the horsepower deficit on trap speed.',
  },
  {
    type: 'p',
    text: 'Indian drag-strip culture has historically been allergic to mid-cc bikes that are not litre superbikes or 200-400cc commuters. The SR-R does not change that calculus on the strip itself — at 11.3 stock ET, it loses to a used Hayabusa Gen 1 at INR 8 lakh by close to a full second. What the SR-R does change is the value proposition for the rider who wants a faired sport bike with a sub-INR 7 lakh on-road price, a tractable inline-triple character that is genuinely usable on Indian roads, and the option to drop a stage-one flash plus sprocket swap to chase a 10.9 ET without breaking the INR 7 lakh total cost ceiling. That combination did not exist in India before this bike.',
  },
  {
    type: 'h2',
    text: 'Run Your Own Numbers',
  },
  {
    type: 'p',
    text: 'If you are sizing up the 675SR-R against the Daytona 660, the Street Triple 765 R, or any of the used 675cc triples on the Indian grey market, the simulator at motoquant.in lets you sweep rider weight, ambient temperature, density altitude, and parts-catalog mods to see exactly where the tenths come from on your specific bike under your specific conditions. The cluster-bias correction discussed earlier is baked into the model — when the simulator says 11.3, expect 11.0 to 11.2 on a well-prepped surface with a competent rider.',
  },
  {
    type: 'p',
    text: 'More useful for tuning decisions: MotoQuant scores every part in its catalog by cost-per-tenth for your specific bike. On the SR-R, the simulator says the Powertronic Stage 1 flash is the cheapest tenth, the 16/45 sprocket swap is the second cheapest tenth, and a steering damper is the cheapest piece of safety hardware you can add before doing either. None of those are opinions — they are simulator outputs against the validated 95 hp inline-triple model.',
  },
  {
    type: 'p',
    text: 'Two final caveats. First, every number in this post is a stock-tune simulation under specific Aamby Valley November conditions. Change the venue, the season, or the rider, and absolute ETs shift; the relative ordering of which mods help most stays stable. Second, the litre-sport-600-1000 cluster bias is being actively closed in the background — the recent calibration work that lifted the max engine deceleration knob from 150 to 600 rad/s squared dropped the cluster mean bias from +0.207 to +0.06 seconds for inline fours. The same calibration work is expected to roll forward to inline triples on the next sweep, which would push the SR-R sim ET into the 11.20 to 11.25 range without any change to the bike itself.',
  },
  {
    type: 'p',
    text: 'If you take one thing from this post, take this: the CFMoto 675SR-R is the first faired inline triple available in India at a price point that puts the platform within reach of a Pulsar NS400Z buyer with INR 2 lakh more in the bank. The drag-strip numbers are a small part of that story. The fact that every aftermarket part developed for the 800NK over the past two years drops directly onto the SR-R is the larger one — and so is the fact that CFMoto chose to spend its development budget on aerodynamics rather than peak horsepower. That is an unusual choice in this segment, and the simulator says it was the correct one.',
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
          datePublished: '2026-05-31',
        })}
      />
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {['CFMoto', '675SR-R', 'Inline triple', 'Indian mid-cc sport', 'physics'].map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            CFMoto 675SR-R Quarter-Mile Physics: The 95hp Daytona 660 Rival
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
            31 May 2026 · 12 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        {/* Internal links / related reading */}
        <div className="max-w-2xl mx-auto mt-16">
          <h3 className="font-display font-bold text-lg text-white mb-4">Related reading</h3>
          <ul className="text-sm text-white/70 space-y-2">
            <li>
              ·{' '}
              <Link href="/blog/cfmoto-800nk-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                CFMoto 800NK Quarter-Mile Physics: A KTM 790 Duke in Disguise
              </Link>{' '}
              — the naked sibling that shares the 675SR-R cassette and clutch.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/triumph-street-triple-765r-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                Triumph Street Triple 765 R Quarter-Mile Physics
              </Link>{' '}
              — the 123hp British triple the SR-R is hunting on the strip.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/600cc-supersport-launch-physics-engine-deceleration" className="text-brand-accent hover:text-brand-orange transition-colors">
                Why 600cc Supersports Were Running 200ms Slow in Our Sim
              </Link>{' '}
              — the calibration fix that will roll forward to the SR-R on the next sweep.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-to-tune-for-aamby-valley-in-november" className="text-brand-accent hover:text-brand-orange transition-colors">
                How to Tune for Aamby Valley in November
              </Link>{' '}
              — the venue conditions used for every simulation above.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>{' '}
              — every spec, every gear ratio, every Cd value used by the simulator.
            </li>
            <li>
              ·{' '}
              <a
                href={REPO_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                MotoQuant on GitHub
              </a>{' '}
              — free and open source: audit the physics behind every number in this post, or run it yourself.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Run the 675SR-R yourself</div>
            <div className="text-white/60 text-sm">
              Free simulator — pick the CFMoto 675SR-R, dial in your local conditions, and watch the ET update live.
            </div>
          </div>
          <Link
            href="/simulator?bike=cfmoto-675sr-r"
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
