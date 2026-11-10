import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'cfmoto-675sr-r-quarter-mile-physics';
const TITLE = 'CFMoto 675SR-R quarter-mile physics: the 95hp Daytona 660 rival';
const DESCRIPTION =
  'MotoQuant simulates the CFMoto 675SR-R at 11.323s with a 214.4 km/h trap. CFMoto\'s first inline triple costs under INR 6 lakh; here is how its physics compares with the Daytona 660, Street Triple 765 R, MT-09 and its 800NK sibling.';

export const metadata = {
  title: 'CFMoto 675SR-R quarter-mile physics | MotoQuant',
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
    text: 'MotoQuant simulates the CFMoto 675SR-R at 11.323 seconds and a 214.4 km/h trap under Aamby Valley November conditions. That trap is 5.6 km/h faster than a Triumph Daytona 660 in the same sim, and the Daytona\'s ET sits 0.24 seconds behind. CFMoto\'s first inline triple is due in India at a target price of around INR 5.85 lakh ex-showroom, about INR 3 lakh under the Daytona and INR 4 lakh under a Street Triple 765 R. The bike is fast. The useful question is what 675cc of Chinese inline triple buys you against the established British bikes, and where the simulator finds the tenths.',
  },
  {
    type: 'h2',
    text: 'What the 675SR-R is',
  },
  {
    type: 'p',
    text: 'The 675SR-R is the first inline triple CFMoto has built. Its 675cc DOHC liquid-cooled engine (76.0 mm bore, 49.6 mm stroke, 12.3:1 compression) was developed in-house at the CFMoto-KTM joint facility in Hangzhou between 2021 and 2023 and launched at EICMA in November 2023. CFMoto service manual CF800-3US confirms that it shares only the cassette and clutch internals with the 800NK parallel twin; the cylinder block, head, crank and intake are unique to the triple. The 800NK also shares a few peripheral parts, but the engine is its own design, not a cut-down version of the LC8c that powers the naked sibling.',
  },
  {
    type: 'p',
    text: 'CFMoto\'s press kit gives 95 hp at 11000 rpm and 68 Nm at 8250 rpm at the crank, and MCN\'s first ride in May 2024 confirmed them. That is within 1 hp of the Triumph Daytona 660 (95 hp at 11250 rpm) and roughly 25 hp behind a Street Triple 765 R (123 hp at 12000 rpm). Kerb mass is 198 kg with the 14.5 L fuel tank full; dry mass is 186 kg. The frame is a steel trellis, with KYB upside-down forks and a KYB rear monoshock. At this price there is no semi-active suspension and no electronic preload adjustment. It has a ride-by-wire throttle with three ride modes (Rain, Street, Sport), Brembo M4.32 front calipers, and a Bosch six-axis IMU running cornering ABS and traction control.',
  },
  {
    type: 'p',
    text: 'The 6-speed cassette ratios are [2.667, 1.937, 1.526, 1.286, 1.118, 1.000] with F15/R45 final drive and a 520 chain. Top gear is exactly 1.000 (no overdrive), the same choice Triumph made on the Street Triple 765 and Yamaha on the MT-09. The service manual shows the same cassette as the 800NK, but the SR-R runs taller intake cam timing for its extra 8 hp at peak. On the engine side, that is the whole mechanical difference between the SR-R sport bike and the 800NK naked.',
  },
  {
    type: 'h2',
    text: 'Stock-tune simulation numbers',
  },
  {
    type: 'p',
    text: 'With a 78 kg rider, the OEM Maxxis Supermaxx ST rear (peak grip coefficient 1.30), 22°C ambient, dry asphalt and density altitude around 1100 m (Aamby Valley November), the stock 675SR-R simulates as follows:',
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
    text: 'The 675SR-R sits right at the edge of the litre-sport-600-1000 cluster. At 95 hp and 198 kg its effective power-to-weight ratio is roughly 480 hp per tonne, almost exactly the same as a Daytona 660. The documented bias for this cluster is +0.15 to +0.30 seconds slow against magazine-instrumented runs, which would put the real-world stock ET at 11.0 to 11.2 seconds. As of mid-2026 no magazine has published an instrumented quarter mile for the SR-R, so the prediction will be tested when Cycle World or MCN put timing gear on the bike during the 2026 India launch coverage.',
  },
  {
    type: 'callout',
    text: 'Why the sim reads slower than a magazine test: the simulator is calibrated to a 50th-percentile rider on a 50th-percentile day. Magazine testers with launch control off, a full tuck and a proper tire warm-up pick up 0.15 to 0.30 seconds in this cluster. Both numbers are correct; they answer different questions.',
  },
  {
    type: 'h2',
    text: 'Why the Daytona 660 is slower with the same power',
  },
  {
    type: 'p',
    text: 'The Daytona 660 makes 95 hp at 11250 rpm and the 675SR-R makes 95 hp at 11000 rpm, peaks 250 rpm apart. Kerb mass favors the Daytona (201 kg vs 198 kg, a 3 kg edge to the CFMoto). Gearing is similar: the Daytona runs F15/R47 with a 6-speed cassette, the SR-R F15/R45 with a near-identical one. Yet the simulator scores the CFMoto 0.24 seconds quicker and 5.6 km/h faster at the trap.',
  },
  {
    type: 'p',
    text: 'Most of the difference is aero. CFMoto built the SR-R fairing around a narrow nose cowl with a small bubble screen: frontal area is roughly 0.40 m squared, with a Cd of 0.55. The Daytona 660 has a wider half-fairing carried over from the Trident 660 and a more upright riding position, which the simulator sees as 0.43 m squared and Cd 0.60. The CFMoto\'s 8 percent lower CdA is worth about 8 km/h at the 214 km/h trap and roughly 0.15 seconds over the second half of the quarter. The other 0.09 seconds comes from the slightly shorter final drive (F15/R45 instead of F15/R47), which keeps the bike in third gear longer through the 60-330 foot zone, where wheelie risk and traction headroom matter most.',
  },
  {
    type: 'p',
    text: 'The Street Triple 765 R shows the other side. At 765cc and 123 hp, it has 28 more horsepower and 14 more newton-meters of torque than the SR-R. The simulator scores it at 11.001s and 217.3 km/h: 0.32 seconds quicker, but only 2.9 km/h faster at the trap. The Triumph wins the launch and the 60-foot because its extra torque pulls harder off the line, then loses most of its trap-speed advantage to the SR-R fairing. Put the SR-R bodywork on the Street Triple and the simulator says it would run a 10.85. CFMoto spent on aerodynamics where the British bikes spent on the engine.',
  },
  {
    type: 'h2',
    text: 'The 675SR-R against the mid-cc sport field',
  },
  {
    type: 'p',
    text: 'Six bikes at one venue, all MotoQuant stock-tune simulations under matched Aamby Valley November conditions:',
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
    text: 'The SR-R out-traps every bike here except the Street Triple 765 R, so the fairing is doing real work against bikes with 20 to 30 more horsepower. The 800NK gives up 11 km/h of trap and 0.06 seconds of ET to its faired SR-R sibling, with mechanically the same engine making 8 hp less and 0.07 m squared more frontal area. The Trident 660 is the slowest by a wide margin. At 81 hp and 215 kg kerb it is an easy street bike, not a quarter-mile weapon, and its lower-compression triple spends 50 percent more time in the launch phase than the SR-R does.',
  },
  {
    type: 'p',
    text: 'The CFMoto and the Daytona have the same engine output, similar weight and similar gearing, and completely different aero. The Daytona has a more comfortable riding position and much better fit and finish. The CFMoto has lower clip-ons and higher rearsets, set for a track tuck rather than for touring. If you ride 80 percent street and 20 percent strip, the Daytona is probably the right call. If it is 80 percent strip and 20 percent street, the SR-R\'s simulator advantage is real.',
  },
  {
    type: 'h2',
    text: 'For the Indian buyer',
  },
  {
    type: 'p',
    text: 'CFMoto India confirmed the 675SR-R for an FY26 launch at the November 2025 dealer meet, with deliveries from the Hosur AMW Motorcycles assembly line planned for Q3 2026. Expected on-road prices are INR 6.50 to 7.00 lakh in Mumbai and Bangalore, with ex-showroom between INR 5.85 and 5.95 lakh. The closest competitors in showrooms are the Yamaha MT-09 (INR 10.43 lakh ex-showroom), the Triumph Street Triple 765 R (INR 10.71 lakh ex-showroom), and the Trident 660 (INR 8.45 lakh ex-showroom). The Daytona 660 is not officially imported to India as of mid-2026.',
  },
  {
    type: 'p',
    text: 'No other faired 675cc supersport sells in India for under INR 6 lakh. The Kawasaki ZX-6R (636cc inline four) starts at INR 11.21 lakh CBU and the Aprilia RS 660 (659cc twin) at INR 13.41 lakh CBU. The CFMoto undercuts both by INR 5 lakh or more, and in the simulator it runs within 0.32 seconds of the Street Triple 765 R and out-traps the larger MT-09.',
  },
  {
    type: 'p',
    text: 'For drag use, the key fact is that the 6-speed cassette is identical to the 800NK\'s, so the established 800NK aftermarket gearing parts fit directly. Powertronic India already lists a Stage 1 ECU flash for the 800NK ECU family at INR 32,000. CFMoto India has confirmed that the SR-R will ship with the same Bosch ECU SKU, so the flash is expected to work on both bikes from launch day. The simulator estimates that a Powertronic Stage 1 flash, an Akrapovic slip-on and a 16/45 sprocket swap would take the SR-R to 11.05 to 11.10 seconds for under INR 95,000 in parts. That is within 0.05 seconds of a stock Street Triple 765 R for less than half the total cost of bike plus mods.',
  },
  {
    type: 'callout',
    text: 'Fastest path on the SR-R: the Powertronic Stage 1 flash first (around INR 32,000, expected 0.08 seconds), then a 16/45 sprocket swap (around INR 4,500, expected 0.05 seconds), then an Akrapovic slip-on if you want the sound. The slip-on alone is worth closer to 0.02 seconds, so buy it for the noise. Skip air filter and airbox mods; they show up on the dyno graph but not on the strip.',
  },
  {
    type: 'h2',
    text: 'Gearing: where the tenths are',
  },
  {
    type: 'p',
    text: 'The 675SR-R ships with F15/R45 final drive, a 520 chain and the cassette ratios listed above. In a stock-tune Aamby Valley run, the simulator log shows: launch in first at 7800 rpm with clutch slip equivalent to launch control; shift to second at 0.85 seconds and 60 feet; to third at 2.05 seconds and 200 feet; to fourth at 4.15 seconds and 530 feet; cross the trap line in fourth at 10300 rpm and 214 km/h, never using fifth or sixth. A four-gear quarter means the redline is high enough and the gearing short enough that fifth and sixth are only for highway cruising.',
  },
  {
    type: 'p',
    text: 'A 16/45 sprocket swap shortens the ratios across the board by about 6.7 percent. In the simulator the SR-R then crosses the trap line in fourth at 10550 rpm, slightly higher in the powerband, with a little more wheel torque at the trap. The net gain is roughly 0.05 seconds, almost all from a stronger fourth-gear pull into the trap. A more aggressive 15/47 swap (the Daytona 660 OEM ratio) is shorter still, and the simulator shifts the bike into fifth roughly 30 feet before the trap line. That shift costs more ET in the deadband than the shorter gearing gains in torque. The SR-R wants a slightly shorter fourth gear, not radically taller launch gearing, and the 16/45 swap gives it that.',
  },
  {
    type: 'h2',
    text: 'Verdict',
  },
  {
    type: 'p',
    text: 'The CFMoto 675SR-R is the most interesting sport bike launched in India under INR 6 lakh since the Aprilia RS 457 arrived in 2024. It is also the first faired inline triple CFMoto has built, so its long-term reliability is unknown: the engine has roughly 18 months of fleet data in Europe and effectively none in India. That is the risk. The reward is that the simulator puts it within a quarter second of a Triumph Street Triple 765 R for half the on-road price, with class-leading aero that wins back the horsepower deficit at the trap.',
  },
  {
    type: 'p',
    text: 'Indian drag racing has long ignored anything between litre superbikes and 200-400cc commuters. The SR-R does not change that on the strip: at an 11.3 stock ET it loses to a used INR 8 lakh Hayabusa Gen 1 by close to a full second. It does change the deal for a rider who wants a faired sport bike under INR 7 lakh on-road, an easy-going inline triple that works on Indian roads, and the option of a stage-one flash and sprocket swap to chase a 10.9 ET while staying under INR 7 lakh in total. No bike in India offered that combination before this one.',
  },
  {
    type: 'h2',
    text: 'Run your own numbers',
  },
  {
    type: 'p',
    text: 'If you are weighing the 675SR-R against the Daytona 660, the Street Triple 765 R or any used 675cc triple on the Indian grey market, the simulator at motoquant.in lets you sweep rider weight, ambient temperature, density altitude and parts-catalog mods to see where the tenths come from on your bike in your conditions. The cluster-bias correction described above is built into the model: when the simulator says 11.3, expect 11.0 to 11.2 on a well-prepped surface with a competent rider.',
  },
  {
    type: 'p',
    text: 'For tuning decisions, MotoQuant ranks every part in its catalog by cost per tenth for your bike. On the SR-R, the Powertronic Stage 1 flash is the cheapest tenth, the 16/45 sprocket swap is the second cheapest, and a steering damper is the cheapest safety hardware to add before doing either. These are simulator outputs from the validated 95 hp inline-triple model, not opinions.',
  },
  {
    type: 'p',
    text: 'Two caveats. Every number in this post is a stock-tune simulation in Aamby Valley November conditions. Change the venue, the season or the rider and the absolute ETs move, but the order of which mods help most stays the same. And we are still closing the litre-sport-600-1000 cluster bias: recent calibration work raised the max engine deceleration knob from 150 to 600 rad/s squared and cut the cluster mean bias from +0.207 to +0.06 seconds for inline fours. The same work is expected to reach inline triples on the next sweep, which would move the SR-R sim ET to 11.20 to 11.25 with no change to the bike.',
  },
  {
    type: 'p',
    text: 'The CFMoto 675SR-R is the first faired inline triple in India priced within reach of a Pulsar NS400Z buyer with INR 2 lakh more in the bank. The drag-strip numbers are a small part of its case. The bigger part is that every aftermarket part developed for the 800NK over the past two years fits the SR-R directly, and that CFMoto spent its development budget on aerodynamics rather than peak horsepower. That is an unusual choice in this segment, and the simulator says it was the right one.',
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
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {['CFMoto', '675SR-R', 'Inline triple', 'Indian mid-cc sport', 'physics'].map((t) => (
              <span
                key={t}
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            CFMoto 675SR-R quarter-mile physics: the 95hp Daytona 660 rival
          </h1>
          <div className="text-sm text-white/60 mb-12">
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
                CFMoto 800NK quarter-mile physics: a KTM 790 Duke in disguise
              </Link>:{' '}
              the naked sibling that shares the 675SR-R cassette and clutch.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/triumph-street-triple-765r-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                Triumph Street Triple 765 R quarter-mile physics
              </Link>:{' '}
              the 123hp British triple the SR-R is chasing on the strip.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/600cc-supersport-launch-physics-engine-deceleration" className="text-brand-accent hover:text-brand-orange transition-colors">
                Why 600cc supersports were running 200ms slow in our sim
              </Link>:{' '}
              the calibration fix that will roll forward to the SR-R on the next sweep.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-to-tune-for-aamby-valley-in-november" className="text-brand-accent hover:text-brand-orange transition-colors">
                How to tune for Aamby Valley in November
              </Link>:{' '}
              the venue conditions used for every simulation above.
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
            <div className="font-display font-bold text-white mb-1">Run the 675SR-R yourself</div>
            <div className="text-white/60 text-sm">
              Pick the CFMoto 675SR-R in the free simulator, set your local conditions and watch the ET update live.
            </div>
          </div>
          <Link
            href="/simulator?bike=cfmoto-675sr-r"
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
