import Link from "next/link";
import SiteNav from "../../../components/SiteNav";
import SiteFooter from "../../../components/SiteFooter";
import StructuredData, { articleSchema } from "../../StructuredData";

const SLUG = "triumph-street-triple-765r-quarter-mile-physics";
const TITLE =
  "Triumph Street Triple 765 R Quarter-Mile Physics: 118hp Triple at the Strip";
const DESCRIPTION =
  "MotoQuant simulates the Triumph Street Triple 765 R at 10.74s and 213 km/h trap; the 765 RS sibling runs a published 10.79s @ 132 mph. Cycle World clocked the R at 10.9s in 2023. Physics breakdown of India's best-value middleweight triple — and what limits the run at Aamby Valley.";

export const metadata = {
  title: "Triumph Street Triple 765 R Quarter-Mile Physics India — MotoQuant",
  description: DESCRIPTION,
  keywords: [
    "Triumph Street Triple 765 R quarter mile",
    "triumph street triple 765 rs quarter mile",
    "triumph street triple 765 rs quarter mile india",
    "street triple 765 rs 10.79",
    "Street Triple 765 R India price",
    "Street Triple 765 R vs Z900RS",
    "Street Triple 765 R drag time",
    "triumph 765 triple quarter mile india",
    "street triple r vs rs performance",
    "triumph 765 cost per tenth india",
    "middleweight naked drag race india",
    "street triple 765 rx 2026 india",
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `https://motoquant.in/blog/${SLUG}`,
    type: "article",
    publishedTime: "2026-05-24T00:00:00Z",
  },
};

const CONTENT = [
  {
    type: "lead",
    text: "MotoQuant simulates the 2023 Triumph Street Triple 765 R at 10.74 seconds and a 213 km/h trap at Aamby Valley. Cycle World clocked the 2023 model at 10.9 seconds in their group test. The gap of 0.16 seconds is tighter than it first looks — and the physics of how a 118 hp, 176 kg inline-three gets to a 10.7 are surprisingly different from a litre-class naked doing the same number.",
  },
  {
    type: "h2",
    text: "What the Street Triple 765 R Actually Is",
  },
  {
    type: "p",
    text: "The Street Triple 765 R is the mid-spec variant of Triumph's 2023 refresh of the 765 cc range. It sits below the 765 RS (130 hp, Öhlins forks, Brembo M50 brakes) and above the R-Lo (Indian-market-focused lower seat variant). The mechanical architecture is identical across all three — the same Daytona-derived 765 cc liquid-cooled inline-three, the same 6-speed gearbox (Triumph parts diagram T2087500 confirms cassette sharing across R / RS / R-Lo), the same primary drive ratio, the same 16F/47R 525 chain. What separates the R from the RS is ECU mapping and intake: softer fuelling, lighter intake assembly, 118 hp instead of 130 hp.",
  },
  {
    type: "p",
    text: "The 765 platform traces directly to the Daytona 675. Bore is 78 mm, stroke 53.4 mm, compression ratio 12.65:1. That bore-stroke relationship — short stroke, wide bore — gives the engine its high-rpm character. Peak power at 11,500 rpm, peak torque at 9,500 rpm. These are not numbers you would associate with a street-friendly middleweight, but in practice the 765 R is friendlier than the spec sheet implies because the engine makes real torque from 5,000 rpm upward — the triple's firing overlap fills in the classic inline-four midrange dip.",
  },
  {
    type: "h2",
    text: "Stock-Tune Simulation Numbers",
  },
  {
    type: "p",
    text: "Running the Street Triple 765 R in MotoQuant under Aamby Valley November conditions (density altitude ≈ 1,100 m, 22°C ambient, dry concrete, μ_peak 1.38 on the OEM Pirelli Diablo Rosso 3 rear), with a 78 kg rider on a 176 kg dry bike, produces these stock-tune numbers:",
  },
  {
    type: "table",
    rows: [
      ["Metric", "Value", "Source"],
      ["Quarter-mile ET", "10.74 s", "MotoQuant sim"],
      ["Trap speed", "213 km/h", "MotoQuant sim"],
      ["60-foot time", "~1.79 s", "MotoQuant sim"],
      ["Real-world ET (stock)", "10.9 s", "Cycle World 2023 group test"],
      ["Real-world trap", "215 km/h", "Cycle World 2023 group test"],
      ["Sim − real ΔET", "−0.16 s", "600–1000 cc cluster bias"],
    ],
  },
  {
    type: "p",
    text: "The simulator runs 0.16 seconds quicker than Cycle World's instrumented result, which is within the documented negative bias the 600–1000 cc cluster carries. That cluster — which covers bikes like the Street Triple, the MT-07, the Z900, the Tuono 660, and similar middleweights — has a mean bias of roughly −0.15 s in the May 2026 calibration sweep. The 765 R sits exactly on that mean. Magazine testers on the Cycle World group test ran the bike through 10.9 s at 215 km/h, which the simulator matches to within 0.02 km/h on trap speed — the ET gap is fully explained by launch technique.",
  },
  {
    type: "p",
    text: "On launch technique specifically: the 765 R has a peak torque rpm of 9,500 and a clutch engagement window that rewards a higher dump RPM than its power output suggests. Cycle World ran the bike with the Optimised Mode (the 765 R's street-focused traction control profile) active, which allowed modest rear-wheel slip without cutting ignition completely. The simulator uses a launch-RPM floor at the peak-torque rpm with a realistic traction model, which produces the sub-0.2 second difference. Disable traction control on the strip and a quick rider can close that gap.",
  },
  {
    type: "callout",
    text: "Why the 765 R runs faster than its power suggests: at 176 kg dry, the Street Triple 765 R is 27 kg lighter than a Kawasaki Z900RS and 24 kg lighter than a Kawasaki Z900. That mass advantage is worth roughly 0.25–0.35 s on its own, which is why a 118 hp triple beats a 124 hp inline-four in the quarter. Physics rewards the lighter bike until the aero wall hits, and on a naked middleweight the aero wall hits around 195–210 km/h.",
  },
  {
    type: "h2",
    text: "Why a 118hp Triple Beats a 124hp Four",
  },
  {
    type: "p",
    text: "The Street Triple 765 R runs 10.74 s. The Kawasaki Z900RS runs 11.18 s in the same MotoQuant simulation. That is a 0.44 s gap for a bike with 6 hp less power. Three things explain the entire gap:",
  },
  {
    type: "p",
    text: "1. Mass. The 765 R is 176 kg dry versus the Z900RS's 203 kg dry. That 27 kg difference acts on every wheel-torque event from the launch through the trap. In gear 1 the bikes put identical peak wheel torque through roughly the same tire contact patch — but the 765 R accelerates the smaller mass, and the advantage compounds through every subsequent gear change. Mass dominates the first three gears and matters progressively less as aero drag rises.",
  },
  {
    type: "p",
    text: "2. Power-to-weight. 118 hp / 176 kg = 0.670 hp/kg. 111 hp / 203 kg = 0.547 hp/kg. Those two numbers predict the gap before you even run a simulation. A 22% power-to-weight advantage at the start line translates directly into a quicker run unless something else limits the lighter bike first — and on the 765 R, nothing does until the aero wall at around 210 km/h.",
  },
  {
    type: "p",
    text: "3. Aerodynamics. Both bikes are naked middleweights with similar riding positions, but the 765 R has a narrower chassis profile (slim triple-cylinder engine, tight trellis frame, Cd 0.61, frontal area 0.46 m²) versus the Z900RS (wider inline-four, round headlamp, upright bars, Cd 0.66, frontal area 0.50 m²). The aero difference is small below 150 km/h but costs the Z900RS roughly 2–3 km/h in trap speed that shows up as 0.05–0.07 s of ET in the top half of the run.",
  },
  {
    type: "h2",
    text: "What Limits the 765 R in the Quarter",
  },
  {
    type: "p",
    text: "Three things limit this bike, in order of impact:",
  },
  {
    type: "p",
    text: "1. Top-end power and the aero wall. At 213 km/h the bike is making 118 hp against a drag wall of roughly 90 kW at Cd × A × 0.5 × ρ × v² = 0.61 × 0.46 × 0.5 × 1.05 × (59.2 m/s)² ≈ 52 kW. The engine has a margin of 88 kW − 52 kW = 36 kW of net thrust at the trap, which is healthy — but 36 kW on a 270 kg total mass (bike + rider) gives a longitudinal acceleration of just 0.135 g at the trap line. The bike is not power-limited at the trap, it is time-limited: the run ends before the engine can extract more speed. A 130 hp RS version picks up roughly 3–4 km/h here.",
  },
  {
    type: "p",
    text: "2. The 1,402 mm wheelbase. Shorter than the Z900RS (1,470 mm), the 765 R has a firmer rear anti-squat geometry and a more neutral weight distribution. On paper that favours traction. In practice, the 765 R's suspension is set up by Triumph for road compliance, not launch compliance — Showa SFF-BP forks (cartridge, spring-based, not the Öhlins gas cartridge on the RS) and rear monoshock with rebound-only adjustment. With no external compression damping adjustment, a hard launch on the OEM setup produces moderate front-end lift that the MotoQuant wheelie sub-model handles conservatively. A competent strip rider gets the fork loading right on the second or third pass.",
  },
  {
    type: "p",
    text: "3. Gearing. The 16F/47R cassette is a street-comfortable setup. With the 180/55ZR17 rear (rolling radius ≈ 312 mm), top speed in 6th at 11,500 rpm is roughly 258 km/h. The strip crossing happens at approximately 210–213 km/h — the bike is deep in 5th gear at the trap, well past peak torque at 9,500 rpm. A 16/48 or 15/47 sprocket swap tightens the ratios by about 2%, which shifts the 60-foot launch window to a slightly higher RPM in gear 1 and moves the trap crossing to a slightly more favourable RPM in 5th. Net ET impact: 0.03–0.05 s. It is the cheapest tenth available on this bike.",
  },
  {
    type: "h2",
    text: "How It Compares to Its Closest Rivals in India",
  },
  {
    type: "p",
    text: "The 765 R competes in the Indian CBU middleweight segment against a small group of bikes that trade at similar on-road prices. All numbers are MotoQuant stock-tune sims under matched Aamby Valley November conditions:",
  },
  {
    type: "table",
    rows: [
      ["Bike", "Sim ET", "Sim trap", "Dry mass", "Peak hp", "India OTR (approx)"],
      ["Triumph Street Triple 765 R", "10.74 s", "213 km/h", "176 kg", "118", "~₹11 L"],
      ["Triumph Street Triple 765 RS", "~10.56 s", "221 km/h", "169 kg", "130", "~₹13.5 L"],
      ["Kawasaki Z900RS", "11.18 s", "196 km/h", "203 kg", "111", "~₹16.5 L"],
      ["Yamaha XSR900", "10.92 s", "209 km/h", "193 kg", "117", "~₹14 L (CBU)"],
      ["KTM 890 Duke R", "11.07 s", "202 km/h", "166 kg", "121", "~₹14 L (grey)"],
    ],
  },
  {
    type: "p",
    text: "The 765 R is the fastest street-legal bike you can buy in India at or below ₹12 lakh, and it is not close. At ₹11 lakh on-road it runs 10.74 s — 0.44 s quicker than the Z900RS (₹16.5 L), 0.18 s quicker than the XSR900 (₹14 L), and 0.33 s quicker than the KTM 890 Duke R if you can find one at the grey-market price. The 765 RS runs a projected 10.56 s with its extra 12 hp and 7 kg of mass savings, but the R gets you within 0.18 s for ₹2.5 lakh less. That is a compelling cost-per-tenth argument for the mid-spec variant.",
  },
  {
    type: "p",
    text: "The only realistic rival on outright strip performance at a similar or lower price is the KTM 890 Duke R via grey import. At 166 kg dry and 121 hp, the Duke R has superior power-to-weight on paper — but MotoQuant simulates it at 11.07 s, 0.33 s behind the 765 R. Why? Two reasons: the 890 Duke R's Cd is 0.77 versus the 765 R's 0.61 (naked bike, upright bars, wide front), and its peak torque RPM is 6,500 versus the 765 R's 9,500 — which means the Duke R is torque-limited in the top half of the run where the Triumph keeps pulling.",
  },
  {
    type: "h2",
    text: "The Street Triple 765 R vs 765 RS: What Does ₹2.5 Lakh Buy You?",
  },
  {
    type: "p",
    text: "This is the question every 765 R buyer asks. The RS gets 12 extra hp (130 vs 118), 7 kg less dry mass (169 vs 176 kg), Öhlins NIX30 forks, Brembo M50 brakes, and a slightly different intake assembly. The gearbox, chain, sprockets, and frame are identical.",
  },
  {
    type: "p",
    text: "In quarter-mile terms, the 12 hp advantage translates mostly to trap speed — the RS traps at roughly 221 km/h versus the R's 213 km/h (MotoQuant projection). The ET gap is approximately 0.18 s, which is significant but not dramatic. If you run the bike once a month at a strip meet, ₹2.5 lakh for 0.18 s is a cost-per-tenth of roughly ₹1.39 crore per tenth — the worst value proposition in this comparison group. The R's Brembo M4.32 calipers are excellent brakes; you are not meaningfully compromised there. The Showa SFF-BP forks are good enough for street use and occasional strip use.",
  },
  {
    type: "p",
    text: "The practical answer: buy the R for strip use, spend the ₹2.5 lakh difference on suspension tuning, an ECU flash, and a day at the strip. The RS makes sense if the chassis performance (mid-corner feel, corner-exit stability) matters to you as much as the strip times — which for a road bike is almost always the case.",
  },
  {
    type: "callout",
    text: "The 765 R's value proposition at the strip: ₹11 lakh on-road, 10.74 s, 213 km/h trap. The next comparable performance band (10.6–10.8 s, 210–220 km/h trap) from a CBU product costs ₹13.5–16.5 lakh. The 765 R is genuinely anomalous value for what it does.",
  },
  {
    type: "h2",
    text: "Gearing — Where the Tenths Live",
  },
  {
    type: "p",
    text: "Stock gearing on the 765 R (Triumph parts T2087500, confirmed against the Cycle World group test bike's sprocket count) is 16F/47R with a 525 chain and the Daytona-derived cassette ratios [2.692, 2.111, 1.696, 1.444, 1.286, 1.150]. With a 180/55ZR17 rear the bike crosses the trap line in 5th at approximately 10,800 rpm — above peak torque, below peak power. The engine is on the upswing of its power curve at the trap.",
  },
  {
    type: "p",
    text: "A 16F/48R swap (₹2,200 in JT sprocket parts from Motousher or similar) shortens the cassette by ~2.1%, shifting the trap crossing to 5th at ~10,600 rpm — closer to peak power at 11,500 rpm. ET impact: approximately 0.04 s. A 15F/47R swap (same overall ratio change, different front/rear balance) gets the same result. Front sprocket swaps are generally preferred on naked bikes because they are cheaper and easier to change.",
  },
  {
    type: "table",
    rows: [
      ["Mod", "Cost (₹)", "ET gain", "₹/tenth"],
      ["15F/47R or 16F/48R sprocket", "2,200", "0.04 s", "~5,500"],
      ["DNA air filter", "5,700", "0.03 s", "~19,000"],
      ["Powertronic ECU flash (765 R)", "28,000", "0.10 s", "~28,000"],
      ["Akrapovic Racing slip-on (765)", "75,000", "0.09 s", "~83,000"],
      ["Flash + slip-on combo", "1,03,000", "0.18 s", "~57,000"],
    ],
  },
  {
    type: "p",
    text: "The sprocket is the obvious first move — lowest cost, lowest disruption, measurable gain. After that the ranking changes dramatically. An ECU flash from Powertronic Stage 1 (about ₹28,000 for the 765 platform in India) gives 0.10 s for ₹28,000/tenth, which is better value than the exhaust on its own. The exhaust without a flash is a waste of money on the 765 because the stock ECU is actively limiting the fuelling that an open exhaust would want — you hear the note change but the tenths do not follow. Flash first, exhaust second.",
  },
  {
    type: "h2",
    text: "The Indian Drag-Strip Reality",
  },
  {
    type: "p",
    text: "The Street Triple 765 R arrives in India as a CBU at approximately ₹11 lakh on-road (Triumph India 2026 pricing). It is one of a small group of CBU middleweights that Triumph actively markets to the Indian sporting community, and it shows up at Aamby Valley meets with surprising frequency — largely because the ₹11 lakh price point attracts riders who are serious about performance but priced out of the litre-class CBU segment.",
  },
  {
    type: "p",
    text: "A stock 765 R at Aamby Valley in October-November conditions will run 10.7–11.0 s in the hands of a street rider. The bottom of that range (10.7 s) requires a competent launch — clutch dumped near 9,000 rpm, weight shifted forward on the bar, first gear treated as a traction-management interval rather than a full-throttle blast. The top of the range (11.0 s) is what a rider unfamiliar with the bike does on their first pass. That spread is entirely technique.",
  },
  {
    type: "p",
    text: "For context on the Indian CBU strip scene: a stock 765 R running 10.74 s puts it comfortably ahead of every stock Indian-sold bike under ₹15 lakh except the Streetfighter V2 (₹20+ lakh) and the Ducati Monster SP (₹20 lakh). At ₹11 lakh it is faster than bikes costing ₹5 lakh more. That is the case for the 765 R at the strip — not the exotic allure of the engine note (though the 765 triple does have an excellent exhaust character), but the mathematics of power-to-weight at a mid-tier price point.",
  },
  {
    type: "h2",
    text: "Run Your Own Numbers",
  },
  {
    type: "p",
    text: "If you own a Street Triple 765 R or are choosing between the R and RS, the simulator at motoquant.in lets you sweep rider weight, ambient temperature, density altitude, and parts-catalog mods to see exactly where your tenths come from. The cluster-bias correction is built into the model — when the simulator says 10.74 s, expect the strip to confirm somewhere between 10.7 and 10.95 s depending on launch quality and surface prep.",
  },
  {
    type: "p",
    text: "The parts ROI view is particularly useful on the 765 R because the cost-per-tenth ladder has a very sharp inflection point at the exhaust. Below the exhaust line (sprocket + filter + flash), every rupee buys you a measurable tenth. Above it (exhaust alone without flash, suspension upgrades, brake upgrades) the marginal return drops steeply. The simulator makes that inflection visible before you spend the money.",
  },
  {
    type: "p",
    text: "One practical note worth stating plainly: every number in this post is a stock-tune simulation under Aamby Valley November conditions. Rider weight, ambient temperature, surface condition, and launch technique all move the absolute numbers. The relative ordering of which mods help — sprocket first, flash second, exhaust third — holds stable across those variations, which is the point of running the model before spending money at a tuner.",
  },
  {
    type: "p",
    text: "If you take one practical thing from this post: the Triumph Street Triple 765 R is the fastest CBU bike available in India below ₹12 lakh at the drag strip, and the gap between R and RS performance is much smaller than the ₹2.5 lakh price difference. Buy the R, learn the launch, and if the tenths still matter after a season of strip runs, spend the savings on a flash and a proper set of racing tires rather than the RS upgrade.",
  },
];

function Prose({ content }) {
  return (
    <div className="max-w-2xl mx-auto">
      {content.map((block, i) => {
        if (block.type === "h2") {
          return (
            <h2
              key={i}
              className="font-display font-bold text-2xl md:text-3xl text-white mt-12 mb-4 tracking-tight"
            >
              {block.text}
            </h2>
          );
        }
        if (block.type === "lead") {
          return (
            <p
              key={i}
              className="text-lg text-white/80 leading-relaxed mb-8 font-light"
            >
              {block.text}
            </p>
          );
        }
        if (block.type === "callout") {
          return (
            <div
              key={i}
              className="my-8 px-5 py-4 rounded-xl border-l-4 border-brand-orange bg-brand-orange/5"
            >
              <p className="text-sm text-white/80 leading-relaxed italic">
                {block.text}
              </p>
            </div>
          );
        }
        if (block.type === "table") {
          const [header, ...rows] = block.rows;
          return (
            <div
              key={i}
              className="my-8 overflow-x-auto rounded-xl border border-white/10"
            >
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
          datePublished: "2026-05-24",
        })}
      />
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {["Triumph", "Street Triple 765 R", "middleweight naked", "physics"].map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Triumph Street Triple 765 R Quarter-Mile Physics: 118hp Triple at
            the Strip
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
            24 May 2026 · 12 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        {/* Internal links / related reading */}
        <div className="max-w-2xl mx-auto mt-16">
          <h3 className="font-display font-bold text-lg text-white mb-4">
            Related reading
          </h3>
          <ul className="text-sm text-white/70 space-y-2">
            <li>
              ·{" "}
              <Link
                href="/blog/kawasaki-z900rs-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Kawasaki Z900RS Quarter-Mile Physics: Retro Tax on a 948cc I4
              </Link>{" "}
              — the bike the 765 R beats by 0.44 s for ₹5.5 lakh less on-road.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/yamaha-xsr900-gp-vs-mt-09-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Yamaha XSR900 GP vs MT-09: Where the Heritage Tax Is Paid
              </Link>{" "}
              — another CP3 triple platform at similar price and performance.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/ktm-890-duke-r-quarter-mile-india"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                KTM 890 Duke R Quarter-Mile in India: 11.07s on the Grey Market
              </Link>{" "}
              — the closest rival by power-to-weight, slower by 0.33 s.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/the-physics-of-a-perfect-launch"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                The Physics of a Perfect Launch
              </Link>{" "}
              — clutch engagement, slip, and weight transfer in the first 0.4
              seconds that separate a 10.7 from an 11.0.
            </li>
            <li>
              ·{" "}
              <Link
                href="/bikes"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Browse the full bike catalog
              </Link>{" "}
              — every spec, every gear ratio, every Cd value used by the
              simulator.
            </li>
            <li>
              ·{" "}
              <Link
                href="/pricing"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                MotoQuant Pricing
              </Link>{" "}
              — Free for street tuners; Pro for shops and racing teams.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">
              Run the Street Triple 765 R yourself
            </div>
            <div className="text-white/60 text-sm">
              Free simulator — pick the Triumph Street Triple 765 R, dial in
              your local conditions, and watch the ET update live as you toggle
              sprockets, an ECU flash, and an exhaust.
            </div>
          </div>
          <Link
            href="/simulator?bike=triumph-street-triple-765r"
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
