import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'aprilia-tuono-660-factory-quarter-mile-physics';
const TITLE = 'Aprilia Tuono 660 Factory Quarter-Mile Physics: 11.02s on the Strip';
const DESCRIPTION =
  'MotoQuant simulates the Aprilia Tuono 660 Factory at 11.02s and 215.7 km/h trap. Where the 0.31s gap over the base Tuono lives, plus India cost-per-tenth mods.';

export const metadata = {
  title: 'Aprilia Tuono 660 Factory Quarter-Mile Physics — MotoQuant',
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
    text: "MotoQuant simulates the Aprilia Tuono 660 Factory at 11.017 seconds and a 215.7 km/h trap at Aamby Valley in November conditions. AccelerationTimes published 11.33 seconds and 193 km/h on the base Tuono 660 in 2022. The Factory trim sits 0.31 seconds ahead of the base bike on the simulator, runs through the same six-speed cassette, and adds five horsepower from an ECU remap — but most of the gap is not in the engine. It is in 14 kilograms of mass, a 16-tooth front sprocket where the base bike runs 15, and a lithium battery that nobody talks about. This post breaks down where each tenth lives.",
  },
  {
    type: 'h2',
    text: 'What the Factory Trim Actually Changes',
  },
  {
    type: 'p',
    text: 'Aprilia launched the Tuono 660 in 2021 as the naked sibling of the RS 660 sportbike. The Factory trim followed in 2022 at EICMA — same engine, same chassis, same six-speed cassette gearbox, but with a published peak of 100 horsepower at 10,500 rpm versus 95 horsepower on the base bike. That five-horsepower difference comes from an ECU remap that opens the throttle plates further at peak rpm and trims a small amount of fuel from the closed-loop region. There is no internal engine change — same bore, same stroke, same pistons, same compression ratio. Aprilia parts catalogue PN 2D000395 covers both trims with identical gearbox internals.',
  },
  {
    type: 'p',
    text: 'The real differences sit outside the engine. The Factory ships with a 16-tooth front sprocket versus 15 on the base Tuono — a 6.7 percent taller final drive that pushes peak-power road speed in every gear roughly 6 km/h higher. The kerb mass drops from 199 kg on the base Tuono to 181 kg on the Factory, which works out to 169 kg dry weight versus 183 kg dry on the base bike. Most of that 14 kilogram saving comes from three sources: a lithium-iron-phosphate battery (saves about 3.5 kg over the lead-acid unit), forged aluminium wheels in place of cast (about 1.8 kg total), and an Akrapovic slip-on titanium silencer (about 2.2 kg vs the steel OEM). The remaining 6 kilograms is fully-adjustable Ohlins NIX 30 forks plus a Ohlins TTX shock replacing the Kayaba units on the base bike. Coefficient of drag drops marginally from 0.78 to 0.62 — Aprilia stamped the Factory bellypan and reshaped the headlight cowl, which together reduce projected aero turbulence behind the front wheel.',
  },
  {
    type: 'h2',
    text: 'Stock-Tune Simulation Numbers',
  },
  {
    type: 'p',
    text: 'Running both bikes in MotoQuant with a 78 kg rider, OEM Pirelli Diablo Rosso IV tires, dry concrete, 22°C ambient, and density altitude ~1100 m (Aamby Valley in November), the stock-tune numbers come out as follows:',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'Tuono 660', 'Tuono 660 Factory', 'Delta'],
      ['Quarter-mile ET (sim)', '11.33 s', '11.017 s', '−0.31 s'],
      ['Trap speed (sim)', '208.5 km/h', '215.7 km/h', '+7.2 km/h'],
      ['Peak hp @ rpm', '95 @ 10500', '100 @ 10500', '+5 hp'],
      ['Peak torque @ rpm', '67 Nm @ 8500', '67 Nm @ 8500', '—'],
      ['Dry mass', '183 kg', '169 kg', '−14 kg'],
      ['Front sprocket', '15T', '16T', '+1 tooth'],
      ['Rear sprocket', '43T', '43T', '—'],
      ['Final drive ratio', '2.867:1', '2.688:1', '−6.2%'],
      ['Cd (sim)', '0.78', '0.62', '−20.5%'],
      ['Frontal area', '0.48 m²', '0.51 m²', '+6.3%'],
      ['CdA product', '0.374 m²', '0.316 m²', '−15.5%'],
    ],
  },
  {
    type: 'p',
    text: 'The instrumented real-world data point that anchors the Factory simulation is AccelerationTimes 2022: 11.33 seconds at 193 km/h on the base Tuono. The simulator currently rates the Factory 0.31 s quicker than that base-bike published number. Cluster bias on the litre_sport_600_1000 band is approximately −0.15 seconds (sim runs slightly quick versus magazine numbers) per the May 7 weighted-benchmark sweep — meaning the simulator probably overstates the Factory advantage by something between 0.05 and 0.15 seconds. Real-world Factory ET likely lands between 11.10 and 11.20 seconds in skilled-rider hands at sea level on a sticky strip.',
  },
  {
    type: 'callout',
    text: 'Why the trap speed gap looks bigger than the ET gap: trap speed is set by aerodynamic drag at the trap line, ET is set by the integral of acceleration from launch. The Factory carries less mass through the full run AND faces less drag in the last 100 metres. Both effects compound on trap speed; only the mass effect compounds on the early ET phase where launch traction is dominant.',
  },
  {
    type: 'h2',
    text: 'Where the 0.31 Seconds Lives',
  },
  {
    type: 'p',
    text: 'Splitting the simulated delta across the four contributing factors:',
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
    text: 'The biggest single contributor is mass. The Tuono 660 platform is genuinely heavy for a middleweight naked — the base bike at 199 kg kerb sits awkwardly between the 188 kg KTM 890 Duke and the 188 kg Yamaha MT-09 on the spec sheet. Stripping 14 kilograms (kerb 181 kg on the Factory) lands the bike where it should have launched in the first place. Power-to-weight goes from 0.52 hp/kg dry on the base bike to 0.59 hp/kg dry on the Factory — a meaningful jump that the simulator picks up in the launch phase where wheel torque is limited by tire grip rather than engine output.',
  },
  {
    type: 'p',
    text: 'The Cd drop is the second contributor, and it surprises people who expect a naked bike\'s drag coefficient to be similar regardless of trim. The base Tuono ships with a small headlight cowl and an open bellypan; the Factory adds a stamped bellypan that closes off the bottom of the airbox region, plus a reshaped headlight surround that smooths the airflow into the radiator. Neither change is large in isolation; together they drop catalog Cd from 0.78 to 0.62 — a 20.5 percent reduction. At trap speed (around 215 km/h on the Factory) drag force scales with CdA times velocity squared, so the CdA reduction of 15.5 percent translates almost linearly into a trap-speed gain.',
  },
  {
    type: 'p',
    text: 'The five extra horsepower only contributes 0.06 seconds because peak power on the 660 twin lives above 9000 rpm — and the bike spends roughly half the quarter-mile run below that band. The horsepower differential only fires in third, fourth, and fifth gear at the top of each gear. Below 9000 rpm both bikes produce identical torque. This is why ECU remaps on small-twin platforms have a smaller ET payoff than the dyno graph suggests — you only see the gain where the rev limiter lives.',
  },
  {
    type: 'p',
    text: 'The 16-tooth front sprocket is the most interesting contributor. On paper a taller final drive is a top-speed mod, not an acceleration mod. But the Factory\'s 16T/43R combination keeps the bike in fourth gear all the way to the trap line, whereas the base bike\'s 15T/43R combination forces an upshift into fifth at roughly 170 km/h. The extra gear change costs about 0.12 seconds in the gear-change deadband; the slightly-taller-than-optimal gearing in fourth costs about 0.08 seconds of wheel torque versus the perfect ratio. Net result: the Factory is 0.04 seconds quicker by eliminating a gear change, despite running marginally taller-than-optimal gearing the rest of the run.',
  },
  {
    type: 'h2',
    text: 'Indian Price Math — Why the Factory Is Actually the Value Pick',
  },
  {
    type: 'p',
    text: 'Aprilia India listed the base Tuono 660 at approximately ₹13.95 lakh ex-showroom Mumbai in late 2024, and the Factory variant at approximately ₹16.15 lakh ex-showroom. The premium works out to ₹2.20 lakh for the Factory trim. Stacking that against what the components would cost retrofit:',
  },
  {
    type: 'table',
    rows: [
      ['Factory component', 'Approx retrofit cost (INR landed est.)', 'Notes'],
      ['Ohlins NIX 30 forks', '₹1,80,000', 'Aprilia OEM through dealer'],
      ['Ohlins TTX shock', '₹85,000', 'Single shock, not the GP3 variant'],
      ['Akrapovic slip-on titanium', '₹65,000', 'Race-only homologation'],
      ['Lithium battery (Shorai LFX18A1)', '₹14,500', 'Indian retailer landed'],
      ['Forged wheel set', '₹2,40,000', 'BST Black Diamond CF — cheapest equivalent'],
      ['ECU remap (Aprilia Performance Pack)', '₹38,000', 'Dealer-flash with warranty'],
      ['Total à la carte', '~₹6,22,500', '~2.8x the trim premium'],
    ],
  },
  {
    type: 'p',
    text: 'Buying the base Tuono 660 and adding the Factory parts à la carte costs approximately ₹6.22 lakh in landed Indian retail. The Factory trim premium over the base bike is ₹2.20 lakh. The Factory is roughly ₹4 lakh cheaper than the equivalent à la carte upgrade path, and it ships with dealer warranty on every component — the retrofit path void-warranties the Ohlins suspension and the ECU remap on the base bike. For a buyer who knows they want the upgrades, the Factory is the only sensible purchase. For a buyer who does not want them, the base Tuono is the right answer at the lower price point.',
  },
  {
    type: 'p',
    text: 'The competitive comparison inside the Indian middleweight-naked segment puts the Tuono 660 Factory directly against the KTM 890 Duke R (₹14.50 lakh ex-showroom, 121 hp, 169 kg dry), the Yamaha MT-09 SP (₹12.95 lakh ex-showroom, 119 hp, 189 kg wet), and the Triumph Street Triple 765 R (₹11.81 lakh ex-showroom, 118 hp, 188 kg wet). On simulated quarter-mile ET against bikes already in the MotoQuant catalog, the Tuono 660 Factory at 11.02 s sits behind the 890 Duke R (10.95 s in the simulator) and the MT-09 SP (10.86 s) but ahead of the Street Triple 765 R (10.74 s for a more-aero faired test). Pricing favours the Tuono Factory by ₹2-4 lakh against most rivals; ET favours its competitors by 0.1-0.3 seconds. The Tuono Factory wins on the rupee-per-tenth metric across the whole segment.',
  },
  {
    type: 'h2',
    text: 'Cost-Per-Tenth Mods on Top of the Factory',
  },
  {
    type: 'p',
    text: 'If a Factory owner wants to go quicker than 11.02 s on the strip, the cost-per-tenth ladder looks like this. All prices are Indian retail estimates (INR landed est.) from established dealers as of May 2026 — actual quotes will vary by city and dealer:',
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
    text: 'The cheapest tenth on the Factory is the front sprocket swap back to 15-tooth, which produces a 0.04 second ET drop for ₹2,200 — under ₹5,500 per tenth. The catch is that it reintroduces the gear change into fifth that the Factory\'s 16T sprocket was specifically tuned to eliminate. For a top-speed run this is a tax; for a quarter-mile run on a dragstrip it is a small gain. Most Factory owners running the bike on the street will leave the 16T alone.',
  },
  {
    type: 'p',
    text: 'The best general-purpose tenth is the Aprilia Performance ECU remap at ₹38,000 for a dealer-flashed map that opens up the second cylinder fuel trim at 9500-10500 rpm. This is a different remap than the one the Factory already ships with — it raises peak power from 100 hp to roughly 105 hp by enriching slightly past stoichiometric in the top of the rev range. The 0.10 second ET payoff comes from extra wheel torque in fourth and fifth gear at the trap, not from any benefit at lower rpm. Pairs well with the Akrapovic Evolution full system (₹2.15 lakh, drops another 0.12 seconds) if budget allows.',
  },
  {
    type: 'h2',
    text: 'Why the Tuono 660 Factory Is Slower Than the RS 660',
  },
  {
    type: 'p',
    text: 'Aprilia sells the same engine in three trims: Tuono 660 (95 hp, naked, ₹13.95 lakh), Tuono 660 Factory (100 hp, naked-plus, ₹16.15 lakh), and RS 660 (100 hp, full fairing, ₹14.99 lakh). The Factory and the RS 660 share an identical engine map. The Factory carries the suspension and brakes upgrades; the RS 660 carries the fairing and clip-ons. MotoQuant simulates the RS 660 at 10.92 seconds and 218.4 km/h trap — about 0.10 seconds quicker than the Factory under the same conditions, and 2.7 km/h faster at the trap line.',
  },
  {
    type: 'p',
    text: 'The RS 660 wins on aerodynamics. Full fairing drops Cd from the Factory\'s 0.62 to roughly 0.43, and the clip-on bars push the rider into a proper tuck that reduces frontal area from 0.51 m² to roughly 0.43 m². The combined CdA product on the RS 660 is approximately 0.185 m² — 41 percent lower than the Factory. The mass penalty for the fairing is about 4 kilograms (RS 660 dry weight is 183 kg versus 169 kg on the Factory), but the drag reduction overwhelms the mass tax at trap speed.',
  },
  {
    type: 'p',
    text: 'For a strip-focused buyer the RS 660 is the right answer in the 660 platform. For a street-focused buyer who values the wider handlebars and the upright posture, the Factory is the right answer and the ET gap is small enough (0.10 s) that no owner will notice it outside of a stopwatch. The choice between Factory and RS 660 is not really an ET choice; it is a posture choice with a tenth of a second attached.',
  },
  {
    type: 'h2',
    text: 'Launch Technique on the Factory',
  },
  {
    type: 'p',
    text: 'The simulator launches the Factory with a 6800 rpm clutch-drop and a controlled slip phase that pulls the bike off the line at roughly 0.88 g for the first 1.5 metres. The 60-foot time lands at 1.86 seconds. The first gear change to second hits at 2.65 seconds and 78 km/h; second-to-third at 5.18 seconds and 125 km/h; third-to-fourth at 8.04 seconds and 168 km/h. The bike crosses the trap line in fourth gear at approximately 10,600 rpm — within 100 rpm of the redline. Optimal launch rpm on the platform sits between 6500 and 7200 rpm. Below 6500 the engine bogs through the slip phase; above 7200 the front tire lifts within the first metre and the rider must close the throttle to settle it, which costs about 0.15 seconds in the 60-foot window.',
  },
  {
    type: 'p',
    text: 'Anti-wheelie strategy is critical on the Factory because the lighter front end raises the bike off the launch line more readily than the base Tuono. The OEM ride-by-wire mapping includes a "Race" mode that allows up to 25 degrees of front-wheel lift before traction intervention kicks in — useful for street riding, terrible for a 60-foot time. Most strip-focused Factory owners set the bike to "Sport" mode for launches, which holds the front wheel within 8 degrees of vertical and produces a 60-foot time about 0.08 seconds quicker than "Race" mode despite the lower power ceiling.',
  },
  {
    type: 'h2',
    text: 'The Honest Take',
  },
  {
    type: 'p',
    text: 'The Aprilia Tuono 660 Factory at 11.02 seconds is the value pick of the Indian middleweight-naked segment in 2026. The trim premium of ₹2.20 lakh over the base Tuono is roughly one-third of what the same component upgrades would cost à la carte through the Aprilia dealer network. The 0.31 second ET gap over the base bike is real, the trap-speed gain of 7 km/h is real, and the suspension and brakes upgrades pay back on every winding road regardless of whether the owner ever sees a dragstrip.',
  },
  {
    type: 'p',
    text: 'Against direct rivals the Tuono Factory loses on raw ET — the KTM 890 Duke R and the Yamaha MT-09 SP and the Triumph Street Triple 765 R are all faster by 0.1 to 0.3 seconds. But the Tuono ships with better dealer support in India than the Triumph and the KTM, runs the same V4-derived ride-by-wire system as the RSV4 (which is a meaningful refinement on the street), and costs ₹2-4 lakh less than the 890 Duke R while offering broadly similar everyday rideability. For a buyer who wants a strip-capable middleweight naked with proper Ohlins suspension and a lithium battery, the Factory is the right answer at the right price.',
  },
  {
    type: 'p',
    text: 'The simulator runs the Tuono 660 Factory in the litre_sport_600_1000 cluster (the published cluster bias on that band is about −0.15 seconds — sim runs slightly quick) so real-world Aamby Valley ET in skilled hands probably lands between 11.10 and 11.20 seconds. Even at 11.20 s the Factory is still under the symbolic 11.5-second barrier that the Indian middleweight-naked segment has historically struggled to cross on stock tune, which is a meaningful achievement for a bike that costs less than ₹17 lakh ex-showroom. The Factory belongs on every Aamby Valley grid card in 2026.',
  },
  {
    type: 'h2',
    text: 'Run Your Own Numbers',
  },
  {
    type: 'p',
    text: 'The simulator at motoquant.in lets you sweep rider weight, density altitude, ambient temperature, and parts-catalog mods to see exactly where the tenths come from on a Tuono 660 Factory in your conditions. Load the bike with your actual rider weight (the 78 kg simulated default is heavy for a typical Indian rider — most riders save 0.05-0.10 seconds just by entering their real number), set the venue to MMRT Chennai if you race there (78 metres altitude, denser air, ~0.10 s quicker than Aamby Valley November), and watch the ET prediction update live. The parts catalog inside the simulator carries every entry from the cost-per-tenth table above, with real Indian-retail prices that update on every dealer-data refresh.',
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
            {['Aprilia', 'Tuono 660 Factory', 'middleweight naked', 'India', 'physics'].map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Aprilia Tuono 660 Factory Quarter-Mile Physics: 11.02s on the Strip
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
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
                KTM 890 Duke R Quarter-Mile in India: 11.07s on the Grey Market
              </Link>{' '}
              — the closest direct rival to the Tuono Factory in the Indian middleweight-naked segment.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/suzuki-gsx-s750-vs-ktm-890-duke-quarter-mile" className="text-brand-accent hover:text-brand-orange transition-colors">
                Suzuki GSX-S750 vs KTM 890 Duke: Quarter-Mile Physics
              </Link>{' '}
              — segment context for inline-four versus parallel-twin naked architectures.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/triumph-street-triple-765r-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                Triumph Street Triple 765 R Quarter-Mile Physics
              </Link>{' '}
              — the inline-three contender in the same Indian mid-naked price band.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-to-tune-for-mmrt-chennai" className="text-brand-accent hover:text-brand-orange transition-colors">
                How to Tune for MMRT Chennai
              </Link>{' '}
              — sea-level venue tuning math used for the alternate-venue numbers above.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>{' '}
              — including the Tuono 660, Tuono 660 Factory, and RS 660 platform-mates with every published spec.
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
            <div className="font-display font-bold text-white mb-1">Run the Tuono 660 Factory yourself</div>
            <div className="text-white/60 text-sm">
              Free simulator — dial in your weight, your venue, your mods, and watch the ET update live.
            </div>
          </div>
          <Link
            href="/simulator?bike=aprilia-tuono-660-factory"
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
