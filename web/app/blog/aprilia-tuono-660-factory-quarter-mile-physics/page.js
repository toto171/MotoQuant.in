import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'aprilia-tuono-660-factory-quarter-mile-physics';
const TITLE = 'Aprilia Tuono 660 Factory quarter-mile physics: 11.02s on the strip';
const DESCRIPTION =
  'MotoQuant simulates the Aprilia Tuono 660 Factory at 11.02s with a 215.7 km/h trap. Where its 0.31s gap over the base Tuono comes from, plus the cost per tenth of mods in India.';

export const metadata = {
  title: 'Aprilia Tuono 660 Factory quarter-mile physics | MotoQuant',
  description: DESCRIPTION,
  keywords: [
    'aprilia tuono 660 factory quarter mile',
    'tuono 660 factory drag time',
    'tuono 660 factory vs base',
    'tuono 660 factory 0-100 india',
    'aprilia tuono 660 factory price india',
    'tuono 660 factory vs rs 660',
    'aprilia 660 platform india',
    'middleweight naked drag india',
    'mt-09 vs tuono 660 factory',
    'aprilia tuono 660 factory cost per tenth',
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
    text: 'MotoQuant simulates the Aprilia Tuono 660 Factory at 11.017 seconds with a 215.7 km/h trap, in Aamby Valley November conditions. AccelerationTimes published 11.33 seconds and 193 km/h for the base Tuono 660 in 2022. In the simulator the Factory is 0.31 seconds ahead of the base bike. It uses the same six-speed cassette and gets five more horsepower from an ECU remap, but most of the gap comes from outside the engine: 14 kilograms less mass, a 16-tooth front sprocket where the base bike has 15, and a lithium battery that nobody talks about.',
  },
  {
    type: 'h2',
    text: 'What the Factory trim changes',
  },
  {
    type: 'p',
    text: 'Aprilia launched the Tuono 660 in 2021 as the naked sibling of the RS 660 sportbike. The Factory trim followed at EICMA in 2022 with the same engine, chassis and six-speed cassette gearbox, and a published peak of 100 horsepower at 10,500 rpm against 95 horsepower on the base bike. The extra five horsepower comes from an ECU remap that opens the throttle plates further at peak rpm and trims a little fuel from the closed-loop region. Nothing inside the engine changes: bore, stroke, pistons and compression ratio are the same. Aprilia parts catalogue PN 2D000395 covers both trims with identical gearbox internals.',
  },
  {
    type: 'p',
    text: "The differences that matter are outside the engine. The Factory has a 16-tooth front sprocket against 15 on the base Tuono, a 6.7 percent taller final drive that raises the peak-power road speed in every gear by roughly 6 km/h. Kerb mass drops from 199 kg on the base Tuono to 181 kg on the Factory, which works out to 169 kg dry against 183 kg dry on the base bike. Most of that 14 kilogram saving comes from three parts: a lithium-iron-phosphate battery (about 3.5 kg lighter than the lead-acid unit), forged aluminium wheels in place of cast (about 1.8 kg in total) and an Akrapovic titanium slip-on silencer (about 2.2 kg lighter than the steel OEM one). The remaining 6 kilograms is in the fully adjustable Ohlins NIX 30 forks and Ohlins TTX shock that replace the base bike's Kayaba units. Coefficient of drag drops marginally from 0.78 to 0.62. Aprilia stamped the Factory bellypan and reshaped the headlight cowl, which together reduce projected aero turbulence behind the front wheel.",
  },
  {
    type: 'h2',
    text: 'Stock-tune simulation numbers',
  },
  {
    type: 'p',
    text: 'Both bikes in MotoQuant on stock tune, with a 78 kg rider, OEM Pirelli Diablo Rosso IV tires, dry asphalt, 22°C ambient and a density altitude of ~1100 m (Aamby Valley in November):',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'Tuono 660', 'Tuono 660 Factory', 'Delta'],
      ['Quarter-mile ET (sim)', '11.33 s', '11.017 s', '−0.31 s'],
      ['Trap speed (sim)', '208.5 km/h', '215.7 km/h', '+7.2 km/h'],
      ['Peak hp @ rpm', '95 @ 10500', '100 @ 10500', '+5 hp'],
      ['Peak torque @ rpm', '67 Nm @ 8500', '67 Nm @ 8500', '–'],
      ['Dry mass', '183 kg', '169 kg', '−14 kg'],
      ['Front sprocket', '15T', '16T', '+1 tooth'],
      ['Rear sprocket', '43T', '43T', '–'],
      ['Final drive ratio', '2.867:1', '2.688:1', '−6.2%'],
      ['Cd (sim)', '0.78', '0.62', '−20.5%'],
      ['Frontal area', '0.48 m²', '0.51 m²', '+6.3%'],
      ['CdA product', '0.374 m²', '0.316 m²', '−15.5%'],
    ],
  },
  {
    type: 'p',
    text: "The instrumented real-world data point behind the Factory simulation is the AccelerationTimes 2022 test: 11.33 seconds at 193 km/h on the base Tuono. The simulator rates the Factory 0.31 s quicker than that published base-bike number. The May 7 weighted-benchmark sweep puts the cluster bias on the litre_sport_600_1000 band at about −0.15 seconds (the sim runs slightly quick against magazine numbers), so the simulator probably overstates the Factory's advantage by 0.05 to 0.15 seconds. A skilled rider at sea level on a sticky strip will likely run the Factory at 11.10 to 11.20 seconds.",
  },
  {
    type: 'callout',
    text: 'Why the trap speed gap looks bigger than the ET gap: trap speed is set by aerodynamic drag at the trap line, while ET is the integral of acceleration from the launch. The Factory carries less mass for the whole run and also has less drag in the last 100 metres. Both effects add up in trap speed. Early in the run, where launch traction dominates, only the mass effect counts.',
  },
  {
    type: 'h2',
    text: 'Where the 0.31 seconds comes from',
  },
  {
    type: 'p',
    text: 'The simulated gap, split across the four factors behind it:',
  },
  {
    type: 'table',
    rows: [
      ['Factor', 'Contribution to ΔET', 'Why'],
      ['14 kg less mass', '~0.13 s', 'Power-to-weight goes from 0.52 to 0.59 hp/kg dry'],
      ['Cd drop 0.78 → 0.62', '~0.08 s', 'CdA falls 15.5%; drag impulse drops most in the last 200 m'],
      ['+5 hp peak power', '~0.06 s', 'Only fires after 9000 rpm; affects last two gears'],
      ['16T vs 15T front sprocket', '~0.04 s', 'Fewer gear changes inside the quarter; reaches 5th smoother'],
    ],
  },
  {
    type: 'p',
    text: 'Mass is the biggest contributor. The Tuono 660 is heavy for a middleweight naked: the base bike at 199 kg kerb sits awkwardly between the 188 kg KTM 890 Duke and the 188 kg Yamaha MT-09 on the spec sheet. Taking off 14 kilograms (181 kg kerb on the Factory) puts the bike where it should have been from the start. Power-to-weight rises from 0.52 hp/kg dry on the base bike to 0.59 hp/kg dry on the Factory, and the simulator picks that up in the launch phase, where tire grip, not engine output, limits wheel torque.',
  },
  {
    type: 'p',
    text: "The Cd drop comes second, which surprises people who expect a naked bike's drag coefficient to stay about the same across trims. The base Tuono has a small headlight cowl and an open bellypan. The Factory adds a stamped bellypan that closes off the bottom of the airbox region and a reshaped headlight surround that smooths the airflow into the radiator. Neither change is large on its own; together they drop catalog Cd from 0.78 to 0.62, a 20.5 percent reduction. At trap speed (around 215 km/h on the Factory), drag force scales with CdA times velocity squared, so the 15.5 percent CdA reduction turns almost linearly into a trap-speed gain.",
  },
  {
    type: 'p',
    text: 'The five extra horsepower add only 0.06 seconds, because peak power on the 660 twin is above 9000 rpm and the bike spends roughly half the run below that. The extra power only shows at the top of third, fourth and fifth gear; below 9000 rpm both bikes make identical torque. That is why an ECU remap on a small twin gains less ET than the dyno graph suggests: the gain only shows up near the rev limiter.',
  },
  {
    type: 'p',
    text: "The 16-tooth front sprocket is the surprising one. On paper a taller final drive is a top-speed mod, not an acceleration mod. But the Factory's 16T/43R keeps the bike in fourth all the way to the trap line, while the base bike's 15T/43R forces an upshift into fifth at roughly 170 km/h. That extra shift costs about 0.12 seconds in the gear-change deadband. The slightly tall gearing in fourth costs about 0.08 seconds of wheel torque against the ideal ratio. Net, the Factory is 0.04 seconds quicker for skipping a shift, even though its gearing is a little tall for the rest of the run.",
  },
  {
    type: 'h2',
    text: 'Indian price math: why the Factory is the value pick',
  },
  {
    type: 'p',
    text: 'In late 2024 Aprilia India listed the base Tuono 660 at about ₹13.95 lakh ex-showroom Mumbai and the Factory at about ₹16.15 lakh ex-showroom, a premium of ₹2.20 lakh for the Factory trim. Here is what the same components would cost as a retrofit:',
  },
  {
    type: 'table',
    rows: [
      ['Factory component', 'Approx retrofit cost (INR landed est.)', 'Notes'],
      ['Ohlins NIX 30 forks', '₹1,80,000', 'Aprilia OEM through dealer'],
      ['Ohlins TTX shock', '₹85,000', 'Single shock, not the GP3 variant'],
      ['Akrapovic slip-on titanium', '₹65,000', 'Race-only homologation'],
      ['Lithium battery (Shorai LFX18A1)', '₹14,500', 'Indian retailer landed'],
      ['Forged wheel set', '₹2,40,000', 'BST Black Diamond CF (cheapest equivalent)'],
      ['ECU remap (Aprilia Performance Pack)', '₹38,000', 'Dealer-flash with warranty'],
      ['Total à la carte', '~₹6,22,500', '~2.8x the trim premium'],
    ],
  },
  {
    type: 'p',
    text: 'Adding the Factory parts to a base Tuono 660 à la carte costs about ₹6.22 lakh at landed Indian retail prices, against the ₹2.20 lakh Factory premium. So the Factory is roughly ₹4 lakh cheaper than the same upgrades bought separately, and every component comes with dealer warranty; on a retrofitted base bike, you lose the warranty on the Ohlins suspension and the ECU remap. If you know you want the upgrades, the Factory is the only sensible purchase. If you do not, the base Tuono is the right bike at the lower price.',
  },
  {
    type: 'p',
    text: 'In the Indian middleweight-naked segment, the Tuono 660 Factory goes up against the KTM 890 Duke R (₹14.50 lakh ex-showroom, 121 hp, 169 kg dry), the Yamaha MT-09 SP (₹12.95 lakh ex-showroom, 119 hp, 189 kg wet) and the Triumph Street Triple 765 R (₹11.81 lakh ex-showroom, 118 hp, 188 kg wet). On simulated quarter-mile ET against bikes already in the MotoQuant catalog, the Tuono 660 Factory at 11.02 s sits behind the 890 Duke R (10.95 s in the simulator) and the MT-09 SP (10.86 s) but ahead of the Street Triple 765 R (10.74 s for a more-aero faired test). Pricing favours the Tuono Factory by ₹2-4 lakh against most rivals; ET favours its competitors by 0.1-0.3 seconds. On rupees per tenth, the Tuono Factory wins across the whole segment.',
  },
  {
    type: 'h2',
    text: 'Cost-per-tenth mods on top of the Factory',
  },
  {
    type: 'p',
    text: 'For a Factory owner who wants to go quicker than 11.02 s on the strip, this is the cost-per-tenth ladder. All prices are Indian retail estimates (INR landed est.) from established dealers as of May 2026; actual quotes vary by city and dealer.',
  },
  {
    type: 'table',
    rows: [
      ['Mod', 'Approx price', 'ET drop', 'Cost per tenth'],
      ['Pirelli Diablo Supercorsa SP V4 tires', '₹38,000', '~0.08 s', '₹47,500'],
      ['Akrapovic Evolution full system', '₹2,15,000', '~0.12 s', '₹1,79,000'],
      ['Aprilia Performance ECU remap', '₹38,000', '~0.10 s', '₹38,000'],
      ['DDA+ telemetry + custom map', '₹85,000', '~0.07 s', '₹1,21,400'],
      ['Carbon airbox lid', '₹22,000', '~0.03 s', '₹73,300'],
      ['Drop 1 tooth front sprocket (15T)', '₹2,200', '~0.04 s', '₹5,500'],
    ],
  },
  {
    type: 'p',
    text: "The cheapest tenth on the Factory is going back to a 15-tooth front sprocket: a 0.04 second ET drop for ₹2,200, under ₹5,500 per tenth. The catch is that it brings back the shift into fifth that the Factory's 16T sprocket was chosen to remove. On a top-speed run that costs you; on a quarter-mile dragstrip run it is a small gain. Most Factory owners who ride on the street will leave the 16T alone.",
  },
  {
    type: 'p',
    text: "The best all-round tenth is the Aprilia Performance ECU remap: ₹38,000 for a dealer-flashed map that opens up the second cylinder's fuel trim at 9500-10500 rpm. It is a different remap from the one the Factory already has. It raises peak power from 100 hp to roughly 105 hp by running slightly rich of stoichiometric at the top of the rev range. The 0.10 second gain comes from extra wheel torque in fourth and fifth gear at the trap; none of it comes from lower rpm. If the budget allows, add the Akrapovic Evolution full system (₹2.15 lakh, another 0.12 seconds).",
  },
  {
    type: 'h2',
    text: 'Why the Tuono 660 Factory is slower than the RS 660',
  },
  {
    type: 'p',
    text: 'Aprilia sells the same engine in three trims: Tuono 660 (95 hp, naked, ₹13.95 lakh), Tuono 660 Factory (100 hp, naked-plus, ₹16.15 lakh) and RS 660 (100 hp, full fairing, ₹14.99 lakh). The Factory and the RS 660 share an identical engine map. The Factory gets the suspension and brake upgrades; the RS 660 gets the fairing and clip-ons. MotoQuant simulates the RS 660 at 10.92 seconds with a 218.4 km/h trap: about 0.10 seconds quicker than the Factory in the same conditions, and 2.7 km/h faster at the trap line.',
  },
  {
    type: 'p',
    text: "The RS 660 wins on aerodynamics. The full fairing drops Cd from the Factory's 0.62 to roughly 0.43, and the clip-on bars put the rider in a proper tuck that cuts frontal area from 0.51 m² to roughly 0.43 m². Combined CdA on the RS 660 is about 0.185 m², 41 percent lower than the Factory. The fairing adds about 4 kilograms (RS 660 dry weight is 183 kg against 169 kg for the Factory), but at trap speed the drag reduction more than pays for the extra mass.",
  },
  {
    type: 'p',
    text: 'For a strip-focused buyer, the RS 660 is the one to buy on the 660 platform. For a street rider who wants the wider handlebars and upright posture, the Factory is the better choice, and the 0.10 s gap is too small for any owner to notice without a stopwatch. Choosing between the Factory and the RS 660 is really about riding posture, with a tenth of a second attached.',
  },
  {
    type: 'h2',
    text: 'Launch technique on the Factory',
  },
  {
    type: 'p',
    text: 'The simulator launches the Factory with a 6800 rpm clutch drop and a controlled slip phase that pulls the bike off the line at roughly 0.88 g for the first 1.5 metres. The 60-foot time is 1.86 seconds. The shift from first to second comes at 2.65 seconds and 78 km/h, second to third at 5.18 seconds and 125 km/h, and third to fourth at 8.04 seconds and 168 km/h. The bike crosses the trap line in fourth at about 10,600 rpm, within 100 rpm of the redline. The best launch rpm on this platform is between 6500 and 7200 rpm. Below 6500 the engine bogs through the slip phase. Above 7200 the front tire lifts within the first metre and the rider has to close the throttle to settle it, which costs about 0.15 seconds over the first 60 feet.',
  },
  {
    type: 'p',
    text: 'Anti-wheelie settings are critical on the Factory, because its lighter front end lifts off the launch line more easily than the base Tuono\'s. The OEM ride-by-wire mapping has a "Race" mode that allows up to 25 degrees of front-wheel lift before traction intervention starts: useful for street riding, terrible for a 60-foot time. Most strip-focused Factory owners launch in "Sport" mode, which holds the front wheel within 8 degrees of vertical and gives a 60-foot time about 0.08 seconds quicker than "Race" mode despite the lower power ceiling.',
  },
  {
    type: 'h2',
    text: 'The verdict',
  },
  {
    type: 'p',
    text: 'At 11.02 seconds, the Aprilia Tuono 660 Factory is the value pick of the Indian middleweight-naked segment in 2026. Its ₹2.20 lakh premium over the base Tuono is roughly one-third of what the same upgrades would cost à la carte through the Aprilia dealer network. It is 0.31 seconds quicker than the base bike and 7 km/h faster at the trap, and the suspension and brake upgrades pay back on every winding road, whether or not the owner ever sees a dragstrip.',
  },
  {
    type: 'p',
    text: 'Against direct rivals the Tuono Factory loses on raw ET: the KTM 890 Duke R, the Yamaha MT-09 SP and the Triumph Street Triple 765 R are all 0.1 to 0.3 seconds faster. But the Tuono has better dealer support in India than the Triumph and the KTM, uses the same V4-derived ride-by-wire system as the RSV4 (a real refinement on the street), and costs ₹2-4 lakh less than the 890 Duke R with broadly similar everyday rideability. If you want a strip-capable middleweight naked with proper Ohlins suspension and a lithium battery, the Factory is the right bike at the right price.',
  },
  {
    type: 'p',
    text: 'The simulator puts the Tuono 660 Factory in the litre_sport_600_1000 cluster, where the published bias is about −0.15 seconds (the sim runs slightly quick), so a skilled rider at Aamby Valley will probably run 11.10 to 11.20 seconds. Even 11.20 s is under the 11.5-second mark that Indian middleweight nakeds have historically struggled to beat on stock tune, and the Factory does it for less than ₹17 lakh ex-showroom.',
  },
  {
    type: 'h2',
    text: 'Run your own numbers',
  },
  {
    type: 'p',
    text: 'The simulator at motoquant.in lets you sweep rider weight, density altitude, ambient temperature and parts-catalog mods to see where the tenths come from on a Tuono 660 Factory in your conditions. Enter your real rider weight: the 78 kg default is heavy for a typical Indian rider, and most riders gain 0.05-0.10 seconds from that alone. If you race at MMRT Chennai, set MMRT as the venue (78 metres altitude, denser air, ~0.10 s quicker than Aamby Valley November). The ET prediction updates as you go. The simulator\'s parts catalog has every entry from the cost-per-tenth table above, with Indian retail prices that update on every dealer-data refresh.',
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
            {['Aprilia', 'Tuono 660 Factory', 'middleweight naked', 'India', 'physics'].map((t) => (
              <span
                key={t}
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Aprilia Tuono 660 Factory quarter-mile physics: 11.02s on the strip
          </h1>
          <div className="text-sm text-white/60 mb-12">
            24 May 2026 · 12 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        {/* Internal links / related reading */}
        <div className="max-w-2xl mx-auto mt-16">
          <h3 className="font-display font-bold text-lg text-white mb-4">Related reading</h3>
          <ul className="text-sm text-white/70 space-y-2">
            <li>
              ·{' '}
              <Link href="/blog/ktm-890-duke-r-quarter-mile-india" className="text-brand-accent hover:text-brand-orange transition-colors">
                KTM 890 Duke R quarter-mile in India: 11.07s on the grey market
              </Link>:{' '}
              the closest direct rival to the Tuono Factory in the Indian middleweight-naked segment.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/suzuki-gsx-s750-vs-ktm-890-duke-quarter-mile" className="text-brand-accent hover:text-brand-orange transition-colors">
                Suzuki GSX-S750 vs KTM 890 Duke: quarter-mile physics
              </Link>:{' '}
              how inline-four and parallel-twin nakeds compare in the same segment.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/triumph-street-triple-765r-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                Triumph Street Triple 765 R quarter-mile physics
              </Link>:{' '}
              the inline-three rival in the same Indian mid-naked price band.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-to-tune-for-mmrt-chennai" className="text-brand-accent hover:text-brand-orange transition-colors">
                How to tune for MMRT Chennai
              </Link>:{' '}
              sea-level venue tuning math used for the alternate-venue numbers above.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>:{' '}
              including the Tuono 660, Tuono 660 Factory and RS 660, with every published spec.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Run the Tuono 660 Factory yourself</div>
            <div className="text-white/60 text-sm">
              Free simulator: set your weight, venue and mods, and watch the ET update live.
            </div>
          </div>
          <Link
            href="/simulator?bike=aprilia-tuono-660-factory"
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
