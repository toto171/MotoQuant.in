import Link from "next/link";
import SiteNav from "../../../components/SiteNav";
import SiteFooter from "../../../components/SiteFooter";
import StructuredData, { articleSchema } from "../../StructuredData";
import { REPO_URL } from "../../../lib/site";

const SLUG = "honda-cb125r-quarter-mile-physics";
const TITLE = "Honda CB125R Quarter-Mile Physics: 14.7hp Neo Sports Café";
const DESCRIPTION =
  "MotoQuant simulates the Honda CB125R at 18.61s and 122 km/h trap — the fastest stock 125cc commuter in the entry cluster. Why the JC91 single out-traps a KTM 125 Duke by 4.4 km/h, where the ₹1.4 lakh price premium over an R15 V4 actually buys you, and the four cheapest tenths for the small-cc Honda owner.";

export const metadata = {
  title: "Honda CB125R Quarter-Mile Physics — MotoQuant",
  description: DESCRIPTION,
  keywords: [
    "honda cb125r quarter mile",
    "cb125r drag time india",
    "cb125r vs r15 v4",
    "cb125r vs ktm 125 duke",
    "honda cb125r 0-100",
    "cb125r top speed",
    "neo sports cafe 125cc",
    "honda jc91 platform",
    "cb125r cost per tenth",
    "small cc commuter drag",
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `https://motoquant.in/blog/${SLUG}`,
    type: "article",
    publishedTime: "2026-05-25T00:00:00Z",
  },
};

const CONTENT = [
  {
    type: "lead",
    text: "MotoQuant simulates the Honda CB125R at 18.607 seconds and 122.2 km/h trap under Aamby Valley November conditions — the fastest stock 125cc bike in the entire entry-cluster sweep. MCN's 2022 long-term test of the same JC91 platform reported a 16.8 s real-world quarter, which lines up with the documented +1.8 second small-cc cluster bias almost to the tenth. The interesting question is not why the CB125R is fast for a 125. It is why a 14.7 hp single out-traps a 14.5 hp KTM 125 Duke by 4.4 km/h when the engine architecture is nearly identical.",
  },
  {
    type: "h2",
    text: "What the CB125R Actually Is",
  },
  {
    type: "p",
    text: "Honda launched the CB125R in late 2018 as the smallest member of the Neo Sports Café family — the styling language that also produces the CB300R, CB650R, and CB1000R. The platform code is JC91 and the engine is a 124.9 cc liquid-cooled DOHC four-valve single, with a 58 mm bore and a 47.2 mm stroke. The 2018 launch made 13.4 hp at 10,000 rpm. A 2021 refresh added a new cam profile and lighter pistons to push the peak to 14.7 hp at 10,000 rpm with 11.6 Nm of torque at 8,000 rpm. The cassette is a JC91-specific six-speed and the bike runs a 14F/45R sprocket pair on a 428 chain.",
  },
  {
    type: "p",
    text: "Chassis side, the bike carries 41 mm Showa SFF-BP upside-down forks, a radial-mount four-piston front caliper, and an aluminium swingarm. For an A1-licence-legal commuter aimed primarily at European learners, this is class-leading hardware. Honda priced it accordingly. The CB125R has never been sold in India — Indonesia, Vietnam, and the Philippines got it through the Asia-Oceania distribution pipeline, and Indian buyers chasing one route through grey-market importers at ₹3.3 to ₹3.6 lakh on-road for a fresh bike.",
  },
  {
    type: "p",
    text: "The 122 kg dry weight (130 kg kerb less roughly 7.5 kg of fuel in the 10.1 L tank) is the load-bearing number for everything that follows. Two competitors share the same engine displacement and broadly the same power output. The CB125R is the lightest of the three by 27 kg.",
  },
  {
    type: "h2",
    text: "Stock-Tune Simulation Numbers",
  },
  {
    type: "p",
    text: "Running the CB125R in MotoQuant under matched Aamby Valley November conditions (density altitude approximately 1,100 m, 22°C ambient, dry concrete surface, μ_peak 1.18 on the OEM 150/60R17 rear), with a 78 kg rider on the 122 kg dry bike, produces the following stock-tune output:",
  },
  {
    type: "table",
    rows: [
      ["Metric", "Value", "Source"],
      ["Quarter-mile ET", "18.607 s", "MotoQuant sim"],
      ["Trap speed", "122.2 km/h", "MotoQuant sim"],
      ["60-foot time", "3.468 s", "MotoQuant sim"],
      ["330-foot trap", "81.5 km/h", "MotoQuant sim"],
      ["Eighth-mile trap", "101.8 km/h", "MotoQuant sim"],
      ["Real-world ET (stock)", "16.5–17.0 s", "MCN 2022 long-term test"],
      ["Sim − real ΔET", "+1.6–2.1 s", "entry-150-200 cluster bias"],
    ],
  },
  {
    type: "p",
    text: "The simulator running roughly 1.8 seconds slow on the CB125R is not a CB125R-specific bug. The entry-150-200 cluster — bikes between 125 and 200 cc, naked, single-cylinder, 14 to 22 hp — has carried a documented positive bias since the cluster-classifier work in late April 2026. Real-world riders on 125 cc bikes launch at higher RPM than the conservative simulator default, slip the clutch through more of gear 1, and shift earlier into the powerband. The cluster mean absolute delta is +1.836 seconds, with the bias narrowing by roughly 0.4 seconds after the May calibrator pass. Strip the bias and the CB125R lands within 0.2 seconds of the MCN test number, which is well inside instrumented-test repeatability on a sub-15 hp bike.",
  },
  {
    type: "callout",
    text: "Reading the bias right: the +1.8 second offset on small-cc bikes is not noise; it is a known calibration gap that affects every 125-class bike in the catalogue equally. Use the simulator output for relative comparisons (which mod helps more, which bike is faster on paper) rather than absolute ETs. The relative ordering — CB125R vs Duke 125 vs GSX-S125 — is rock-solid.",
  },
  {
    type: "h2",
    text: "Why the CB125R Out-Traps Its Rivals",
  },
  {
    type: "p",
    text: "Three direct competitors share the CB125R's displacement bracket. The numbers below are MotoQuant stock-tune sims under matched conditions, all with the same 78 kg rider:",
  },
  {
    type: "table",
    rows: [
      ["Bike", "Sim ET", "Sim trap", "Dry mass", "Peak hp", "Cd"],
      ["Honda CB125R", "18.61 s", "122.2 km/h", "122 kg", "14.7", "0.65"],
      ["KTM 125 Duke", "19.43 s", "117.8 km/h", "149 kg", "14.5", "0.68"],
      ["Suzuki GSX-S125", "20.23 s", "115.4 km/h", "133 kg", "14.7", "0.68"],
      [
        "Yamaha YZF-R15 V4 (155)",
        "18.50 s",
        "121.4 km/h",
        "141 kg",
        "18.4",
        "0.69",
      ],
      [
        "Yamaha MT-15 V2 (155)",
        "19.14 s",
        "112.2 km/h",
        "141 kg",
        "18.4",
        "0.74",
      ],
    ],
  },
  {
    type: "p",
    text: "The CB125R is 0.82 s quicker than the KTM 125 Duke despite making 0.2 hp more — the gap is mass and aerodynamics, not engine. The CB125R is 27 kg lighter than the Duke (122 vs 149 kg) and carries a slightly lower drag coefficient (0.65 vs 0.68). At a 14.7 hp power ceiling, 27 kg is roughly half a tenth per kilogram of relevant mass-to-power impact on the launch phase, and the drag delta extends through the second half of the run.",
  },
  {
    type: "p",
    text: "More remarkable is the comparison with the YZF-R15 V4. The R15 makes 18.4 hp — 25 percent more than the CB125R — yet only beats it by 0.10 seconds and traps 0.8 km/h slower. The reason is straightforward: the R15 carries 19 more kilograms of mass and a higher Cd (0.69 vs 0.65) from its full sport fairing. The 3.7 hp Yamaha advantage barely compensates for the structural weight of being a sportbike rather than a streetfighter. The CB125R does not have a fairing to drag through the air, and the upright stance puts the rider in clean air at quarter-mile trap speeds where the R15 rider is tucked into a turbulent wake.",
  },
  {
    type: "p",
    text: "The CB125R out-traps the MT-15 V2 by exactly 10 km/h despite giving away 3.7 hp. Same chassis as the R15 V4 with the fairing removed, but the upright bars push the MT-15's rider into a much higher frontal-area position — Cd × A drops by roughly 0.7 percent on the CB125R vs the MT-15 because Honda's wind-tunnel work on the Neo Sports Café family carved the seat hump and the tank cover to actually shed air at modest speeds, while the MT-15 just has a streetfighter cowl tacked on top of an R15 chassis. The CB125R is a small-cc aero study Honda never advertises.",
  },
  {
    type: "h2",
    text: "What Limits the CB125R at the Strip",
  },
  {
    type: "p",
    text: "Three limits, in order of impact on the simulated ET:",
  },
  {
    type: "p",
    text: "1. The 14.7 hp ceiling. The bike is power-limited from roughly 80 km/h onward — the gearing is short enough to keep the engine on the boil but there is no top-end reserve. The simulator log shows the bike crossing the trap line in 5th gear at roughly 9,800 rpm, just under the 10,000 rpm power peak. Sixth gear is essentially a highway cruise gear that the bike never uses on the strip. Power is the dominant limit and it cannot be lifted meaningfully without compromising EU emissions compliance.",
  },
  {
    type: "p",
    text: "2. The 3.47 s 60-foot time. Three and a half seconds to cover the first 60 feet is class-typical for a small-cc single, but it is also where roughly half of the ET delta to a fast 250-class bike lives. The CB125R can technically launch at peak torque (8,000 rpm), but most riders sit at 5,500 to 6,500 rpm and slip the clutch through gear 1. The simulator runs an idealised launch and still leaves 3.47 s on the table, because below 30 km/h the 11.6 Nm torque peak just is not enough to break the rear wheel loose on a 122 kg bike with a 78 kg rider. There is no traction to exploit; the bike is acceleration-limited by raw engine output.",
  },
  {
    type: "p",
    text: "3. The 14F/45R sprocket pair on a 428 chain. The 3.214 final-drive ratio is conservative for a strip-focused setup — Honda chose it for European stop-light commuting where 1st gear needs to be tractable from a standstill. A 14F/47R swap (₹1,400 in parts at any Indian Honda dealer that stocks JC91 service kit) shortens the cassette by 4.4 percent, drops 60-foot time by roughly 0.08 s, and bumps the trap-crossing rpm closer to 10,000 in fifth. A 13F/47R swap (₹1,200) is even more aggressive but starts to compromise 6th-gear usability above 110 km/h.",
  },
  {
    type: "h2",
    text: "The Indian Grey-Market Reality",
  },
  {
    type: "p",
    text: "Honda India has confirmed multiple times — most recently in the 2025 Auto Expo media briefing — that the CB125R will not be officially imported. The reasons are straightforward: at the grey-market landed cost of roughly ₹3.4 lakh on-road, the bike has to compete with the Yamaha R15 V4 (₹1.95 lakh on-road), the KTM 125 Duke (₹1.95 lakh), and the TVS Apache RTR 200 4V (₹1.58 lakh). The CB125R is the slowest of those four on power and the smallest on displacement, but it is faster than the Duke 125 over the quarter and within a tenth of the R15 V4.",
  },
  {
    type: "p",
    text: "The bike's actual buyer in India is the rider who already owns an R15 or a Duke and wants the Showa USD forks, the radial-mount caliper, and the Neo Sports Café styling as a second bike. At ₹3.4 lakh the CB125R is not a value-for-money proposition; it is a hardware-for-the-class proposition. The fork tubes and the caliper alone would cost roughly ₹85,000 to retrofit to an R15 V4, and the result would still be heavier and uglier than the CB125R.",
  },
  {
    type: "p",
    text: "Indian-market mods that move the needle on a CB125R, ranked by cost-per-tenth:",
  },
  {
    type: "table",
    rows: [
      ["Mod", "Cost (₹)", "ET gain", "₹/tenth"],
      ["14F/47R sprocket swap", "1,400", "0.08 s", "~1,750"],
      ["K&N drop-in air filter (HA-1287)", "3,800", "0.03 s", "~12,700"],
      ["Lithium battery (-2.2 kg)", "6,500", "0.04 s", "~16,250"],
      ["Akrapovic slip-on (CB125R-specific)", "42,000", "0.07 s", "~60,000"],
      ["Powertronic ECU flash (grey market)", "18,000", "0.05 s", "~36,000"],
    ],
  },
  {
    type: "p",
    text: "The sprocket swap is by far the best tenth on the bike — ₹1,750 per tenth is among the lowest cost-per-tenth ratios in the entire 125-class catalogue. Anything past the sprocket and the air filter on a CB125R is diminishing returns territory. The Akrapovic slip-on adds the right exhaust note but only buys 0.07 s of ET at ₹60,000 per tenth, which only makes sense if the buyer already values the noise and the badging more than the cost.",
  },
  {
    type: "callout",
    text: "Fastest cheap path on a CB125R: 14F/47R sprocket (₹1,400, 0.08 s) plus K&N drop-in filter (₹3,800, 0.03 s) plus lithium battery (₹6,500, 0.04 s) — total ₹11,700 for 0.15 s of ET. That is roughly half what one Akrapovic slip-on costs for double the ET gain. The exhaust adds nothing the simulator can detect at this displacement.",
  },
  {
    type: "h2",
    text: "Gearing — Where the Math Falls Out",
  },
  {
    type: "p",
    text: "Stock gearing on the JC91 cassette is [3.083, 2.063, 1.571, 1.250, 1.045, 0.892] from Honda service manual PN 64MKND00. Combined with the F14/R45 sprocket pair and a 150/60R17 rear (rolling radius approximately 290 mm), the bike hits its 10,000 rpm power peak at exactly 36 km/h in first, 53 km/h in second, 70 km/h in third, 88 km/h in fourth, 105 km/h in fifth, and a theoretical 123 km/h in sixth — which is the same number as the simulator's 122.2 km/h trap, give or take a tenth. The CB125R trap speed is essentially a top-speed test in a straight line.",
  },
  {
    type: "p",
    text: "The 14F/47R swap shifts every shift-point downward by 4.4 percent — first becomes 34 km/h, fifth becomes 100 km/h, and the bike crosses the trap line at 117 km/h in fifth instead of bouncing off the 10,000 rpm power peak in fifth at 105 km/h. The simulator catches roughly 0.08 s of ET from the shorter gearing across the run, with most of it coming in the first 100 metres where the bike spends three full gear-shifts. Net effect: a CB125R with the sprocket swap runs at the speeds the bike feels designed for.",
  },
  {
    type: "p",
    text: "Going more aggressive — 13F/47R or 14F/49R — eats into 6th-gear cruising at higher highway speeds, where the bike will start to run out of revs above 105 km/h. For a strip-only rider this is fine; for the realistic CB125R buyer who also commutes the bike, the 14F/47R is the sweet spot.",
  },
  {
    type: "h2",
    text: "Run Your Own Numbers",
  },
  {
    type: "p",
    text: "If you are considering a CB125R import — or already own one and want to know what the bike's strip ceiling actually is — the simulator at motoquant.in lets you sweep rider weight, ambient temperature, density altitude, and parts-catalog mods to see where each tenth lives. The 1.8 s cluster bias is built into the model and the relative ordering is what you should trust. When the simulator says the CB125R is 0.82 s faster than a KTM 125 Duke, that delta holds at the strip even if both bikes run absolute times a second or two quicker than the simulator predicts.",
  },
  {
    type: "p",
    text: "More usefully, the simulator shows you which mods are dead weight on a small-cc bike. Spending ₹42,000 on a slip-on for 0.07 s on a CB125R is a different conversation than spending ₹11,700 on sprockets-plus-filter-plus-battery for 0.15 s. The parts ROI engine breaks down the cost-per-tenth for every part in the catalogue against the bike you select, and on a 125-class commuter the ladder always comes out gearing-first.",
  },
  {
    type: "p",
    text: "Two caveats. First, the absolute ETs in this post are simulator output under specific conditions — change the rider weight, the surface, the temperature, or the launch technique and the numbers shift. The CB125R will run quicker than 18.6 seconds at the strip; expect 16.5 to 17.5 s depending on rider technique. Second, the +1.8 s cluster bias is not a bug or a calibration error; it is a known artefact of the way the model treats clutch slip on sub-15 hp bikes. Future calibrator passes will narrow it as the Indian Dragy submission corpus grows, but for now the relative deltas are what matter and the absolute numbers are systematically conservative.",
  },
  {
    type: "p",
    text: "The CB125R remains an oddity in the Indian market — a 125 cc Honda that costs almost twice as much as an R15 V4 and out-traps every other 125 in the catalogue. If the grey-market price ever drops below ₹2.7 lakh it becomes a genuine alternative to the R15 V4 for buyers who value chassis hardware over fairings. Until then, it is a bike for connoisseurs of the Neo Sports Café and for the rare Indian rider who has already lapped the strip on a Duke 250 and wants something smaller, lighter, and stranger to ride home on.",
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
          datePublished: "2026-05-25",
        })}
      />
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {["Honda", "CB125R", "Neo Sports Café", "125cc", "physics"].map(
              (t) => (
                <span
                  key={t}
                  className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
                >
                  {t}
                </span>
              ),
            )}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Honda CB125R Quarter-Mile Physics: 14.7hp Neo Sports Café
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
            25 May 2026 · 11 min read · MotoQuant Blog
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
                href="/blog/husqvarna-svartpilen-250-vs-ktm-duke-250-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Husqvarna Svartpilen 250 vs KTM Duke 250: Quarter-Mile Physics
              </Link>{" "}
              — the same Pierer Mobility 125-platform story scaled to 249cc.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/why-your-r15-wont-hit-14s"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Why Your R15 V4 Won't Hit 14s
              </Link>{" "}
              — the closest Indian-market rival to the CB125R, with the same
              small-cc cluster bias story.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/yamaha-mt-125-xsr125-platform-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Yamaha MT-125 vs XSR125: Platform Physics
              </Link>{" "}
              — the European 125-class competitor with the same 14.7 hp ceiling
              and different chassis priorities.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/the-physics-of-a-perfect-launch"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                The Physics of a Perfect Launch
              </Link>{" "}
              — why 3.47 s 60-foot time is the floor on a sub-15 hp bike.
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
              <a
                href={REPO_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                MotoQuant on GitHub
              </a>{" "}
              — free and open source: audit the physics behind every number in this post, or run it yourself.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">
              Run the CB125R yourself
            </div>
            <div className="text-white/60 text-sm">
              Free simulator — pick the Honda CB125R, dial in your local
              conditions, and watch the ET update live as you toggle sprockets,
              air filters, and lithium batteries.
            </div>
          </div>
          <Link
            href="/simulator?bike=honda-cb125r"
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
