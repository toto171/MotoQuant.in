import Link from "next/link";
import SiteNav from "../../../components/SiteNav";
import SiteFooter from "../../../components/SiteFooter";
import StructuredData, { articleSchema } from "../../StructuredData";

const SLUG = "honda-cbr150r-quarter-mile-physics";
const TITLE =
  "Honda CBR150R Quarter-Mile Physics: 17hp SE Asia Sport Single";
const DESCRIPTION =
  "MotoQuant simulates the Indonesian Honda CBR150R at 18.42s and 130.5 km/h trap — quicker than a stock R15 V4 by 0.08s on a 1hp deficit. Why the 136 kg dry mass and 0.62 Cd win against the heavier R15 V4 fairing, how the CBR150R compares to the Malaysian RS150R underbone, and the four mods under ₹15,000 that move the needle for India grey-market owners.";

export const metadata = {
  title: "Honda CBR150R Quarter-Mile Physics — MotoQuant",
  description: DESCRIPTION,
  keywords: [
    "honda cbr150r quarter mile",
    "cbr150r drag time india",
    "cbr150r vs r15 v4",
    "cbr150r vs rs150r",
    "honda cbr150r 0-100",
    "cbr150r top speed india",
    "cbr150r indonesia grey market",
    "se asia 150cc drag",
    "cbr150r vs y15zr",
    "cbr150r cost per tenth",
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `https://motoquant.in/blog/${SLUG}`,
    type: "article",
    publishedTime: "2026-05-26T00:00:00Z",
  },
};

const CONTENT = [
  {
    type: "lead",
    text: "MotoQuant simulates the 2021-onwards Honda CBR150R at 18.42 seconds and 130.5 km/h trap under matched Aamby Valley November conditions. That is a tenth quicker than a stock Yamaha R15 V4 despite making one full horsepower less. The CBR150R is also 14 km/h slower at the trap than the R15 V4. Both numbers come out of the same calculation, and the explanation is the same: 136 kg dry against the R15's 142 kg, with a Cd that is seven percent lower thanks to the bigger fairing being shaped by Honda's HRC wind-tunnel team rather than bolted on as an afterthought. The CBR150R is a fixture of the Malaysian and Indonesian drag scene, available in India only through grey-market importers at roughly ₹2.6 to ₹2.9 lakh on-road. Here is what the 17.1 hp single actually does at the strip, where the gap to the R15 V4 lives, and which mods are worth running on a 150 cc Honda that India never officially sold.",
  },
  {
    type: "h2",
    text: "The K56F Platform",
  },
  {
    type: "p",
    text: "The current Indonesian-market CBR150R uses Honda's K56F platform, launched in 2021 as a clean-sheet replacement for the long-running KC platform that traces back to the 2002 CBR150R Thailand build. Engine is a 149.16 cc liquid-cooled DOHC four-valve single, 57.3 mm bore by 57.8 mm stroke, 11.3:1 compression. Peak power is 17.1 hp at 9,000 rpm, peak torque is 14.4 Nm at 7,000 rpm. The cassette is a six-speed with ratios [2.833, 1.875, 1.400, 1.133, 0.969, 0.852], identical to the Malaysian RS150R underbone running the same engine family. The sprocket pair is 15F/40R on a 428 chain, slightly taller than the RS150R's 15F/43R because the CBR150R sits in a full sport chassis and is geared for highway cruising rather than stoplight launches.",
  },
  {
    type: "p",
    text: "Chassis side, the bike runs 31 mm telescopic front forks (not the upside-down units the CB150R Streetfire gets), a single-pot front caliper with petal disc, and a steel-tube diamond frame. Dry mass is 136 kg, kerb is roughly 144 kg with the 12-litre tank topped off. The fairing is a scaled-down CBR250RR shape and the rider sits in a moderately committed tuck position — clip-ons mounted above the top yoke, mid-set pegs, a 795 mm seat that puts a 175 cm rider in clean air at trap speeds rather than tucked behind a screen the way the bigger CBR designs allow.",
  },
  {
    type: "p",
    text: "Honda India does not sell the CBR150R. Its Indian portfolio in this class is the Hornet 2.0 and CB200X (184 cc, 17.0 hp), both running the older SOHC HET engine that traces back to the 2014 CB Trigger. The K56F engine is a generation newer and more refined, but Honda has briefed that homologating an Indonesian build for Indian regulations does not justify the volume — Indian 150-class buyers who want a faired sport bike are pointed at the R15 V4 instead.",
  },
  {
    type: "h2",
    text: "Stock-Tune Simulation Numbers",
  },
  {
    type: "p",
    text: "Running the CBR150R in MotoQuant under matched Aamby Valley November conditions (density altitude roughly 1,100 m, 22°C ambient, dry concrete surface, μ_peak 1.18 on the OEM 130/70-17 rear at IRC SCT-001 reference grip), with a 70 kg rider in tuck position on the 136 kg dry bike, produces the following:",
  },
  {
    type: "table",
    rows: [
      ["Metric", "Value", "Source"],
      ["Quarter-mile ET", "18.42 s", "MotoQuant sim"],
      ["Trap speed", "130.5 km/h", "MotoQuant sim"],
      ["60-foot time", "3.41 s", "MotoQuant sim"],
      ["330-foot trap", "83.8 km/h", "MotoQuant sim"],
      ["Eighth-mile trap", "104.1 km/h", "MotoQuant sim"],
      ["Top-gear at trap", "5th, ~9,200 rpm", "MotoQuant sim"],
      ["Real-world ET (stock)", "16.6 – 17.2 s", "MotoStatz, Pertamax7"],
      ["Entry-150-200 cluster bias", "+1.84 s mean |Δ|", "MotoQuant sweep"],
    ],
  },
  {
    type: "p",
    text: "Strip the documented +1.84 s entry-150-200 cluster bias and the CBR150R lands within 0.4 seconds of the MotoStatz instrumented runs — which is well inside repeatability for a 17 hp bike at a 70 kg rider weight. The bias is structural; it affects every bike in the 125-200 cc band roughly equally and has been narrowing pass over pass as the calibrator ingests more real-world timeslips. The relative ordering — CBR150R quicker than R15 V4 quicker than Y15ZR V2 — is what the simulator gets right with confidence.",
  },
  {
    type: "callout",
    text: "The +1.84 s small-cc cluster bias is not noise. It is a known calibration gap where the simulator launches more conservatively than a real rider would on a sub-20 hp bike. Use the relative deltas (CBR150R 0.08 s ahead of the R15 V4) rather than the absolute ETs. The relative ordering holds at the strip even when the absolute numbers run a second or two quicker than the sim predicts.",
  },
  {
    type: "h2",
    text: "Why the CBR150R Beats a 1hp-Heavier R15 V4",
  },
  {
    type: "p",
    text: "Three direct rivals share the 150-class displacement bracket. All four bikes below run MotoQuant stock-tune sims under matched conditions with the same 70 kg rider:",
  },
  {
    type: "table",
    rows: [
      ["Bike", "Sim ET", "Sim trap", "Dry mass", "Peak hp", "Cd"],
      ["Honda CBR150R (K56F)", "18.42 s", "130.5 km/h", "136 kg", "17.1", "0.62"],
      ["Yamaha YZF-R15 V4", "18.50 s", "144.2 km/h", "142 kg", "18.1", "0.69"],
      ["Honda RS150R (Malaysia)", "18.74 s", "126.8 km/h", "118 kg", "16.1", "0.62"],
      ["Yamaha Y15ZR V2 (Malaysia)", "19.05 s", "124.4 km/h", "118 kg", "15.4", "0.72"],
      ["Yamaha MT-15 V2 (India)", "19.14 s", "112.2 km/h", "141 kg", "18.4", "0.74"],
    ],
  },
  {
    type: "p",
    text: "The CBR150R beats the R15 V4 by 0.08 seconds on ET but loses 13.7 km/h at the trap. The two numbers tell different halves of the same story. The CBR150R is lighter by 6 kg and has a meaningfully lower Cd, so it accelerates harder through the first half of the run when the engine is making meaningful percentage gains over rolling resistance and drag. By the trap, the R15 V4's one-horsepower advantage has compounded across the full quarter and its taller top gear lets it carry more speed across the line. If the strip were 200 metres long the CBR150R would win by two-tenths; if it were a kilometre, the R15 V4 would walk away by half a second.",
  },
  {
    type: "p",
    text: "The Malaysian RS150R is interesting in the opposite direction. The underbone shares the CBR150R's engine architecture but loses 1 hp on a different cam profile and runs an 18 kg lighter chassis with no fairing. Despite the weight advantage, the CBR150R is 0.32 seconds quicker over the quarter because the underbone's wide handlebars push the rider into dirty air at 100+ km/h. The 0.62 Cd on the CBR150R applies to a bike with a fairing; the same Cd value on the RS150R underbone assumes the rider is willing to tuck flat over a fuel tank that is not shaped for it. Real-world underbone riders at the strip get worse aerodynamics than the spec sheet implies, which is why the Malaysian SuperRimba 150 cc class has the CBR150R and the Y15ZR running broadly equal ETs despite the spec-sheet horsepower spread.",
  },
  {
    type: "p",
    text: "The MT-15 V2 comparison is the most embarrassing for Yamaha. Same chassis as the R15 V4 with the fairing removed and the upright bars added back, and the bike loses 0.64 seconds over the quarter and 32 km/h at the trap. The MT-15 V2 makes more peak power than the CBR150R on paper, but the streetfighter rider position adds roughly 0.05 m² of frontal area at trap speeds and the 0.74 Cd is brutal. The CBR150R out-traps the MT-15 V2 by 18 km/h despite making 1.3 hp less. Aerodynamics on small-cc bikes is a much bigger story than the magazine spec sheets ever acknowledge.",
  },
  {
    type: "h2",
    text: "What Limits the CBR150R at the Strip",
  },
  {
    type: "p",
    text: "Three limits, in order of impact on the simulated ET:",
  },
  {
    type: "p",
    text: "1. The 17.1 hp ceiling at 9,000 rpm. The bike is power-limited from roughly 90 km/h onward. The simulator log shows the CBR150R crossing the trap line in fifth at 9,200 rpm — just past peak power, with sixth gear left untouched because the bike runs out of road before it runs out of revs in fifth. Honda built the gearbox for an Indonesian rider who needs sixth gear for 100 km/h highway commuting, not for a strip run. Power cannot be lifted meaningfully without losing Euro 5 compliance on the carbureted version or breaking the Indonesian-market emissions cert on the FI bike — both of which matter for grey-market import to India where the bike has to be road-registerable.",
  },
  {
    type: "p",
    text: "2. The 3.41 s 60-foot time. The CBR150R has 14.4 Nm of peak torque arriving at 7,000 rpm, which is one of the higher torque-to-mass ratios in the 150 class. But the bike still needs to slip the clutch through gear one because below 30 km/h the rear tire is making more grip than the engine is producing torque. The 60-foot time is roughly half a second longer than what a perfectly-launched bike of the same spec could theoretically achieve, but closing that gap requires a launch-control aftermarket ECU and a quickshifter neither of which exists for the K56F platform yet. The CBR150R is acceleration-limited from a standstill — the chassis could handle more, but the engine has not got more to give.",
  },
  {
    type: "p",
    text: "3. The 15F/40R sprocket pair on a 428 chain. The 2.667 final-drive ratio is tall for a strip-focused setup — Honda chose it for the Jakarta commuting-rider profile where sixth-gear cruising at 90 km/h needs to sit around 6,500 rpm for fuel economy. The simulator catches a 14F/40R swap (₹950 in parts at any Honda Big Wing dealer that stocks K56F service kit) trimming 0.06 s off the ET by shortening the entire cassette by 6.7 percent. Combined with a 14F/42R pair the savings get closer to 0.09 s, at the cost of dropping 6th-gear cruising from 90 to 84 km/h. For an Indian grey-market owner who tracks the bike rather than commutes it, this is the cheapest tenth on the platform.",
  },
  {
    type: "h2",
    text: "The Indian Grey-Market Reality",
  },
  {
    type: "p",
    text: "Honda India has confirmed at multiple BS6 emissions briefings that the CBR150R K56F will not be brought to India under any branding. The reason is straightforward: at the grey-market landed cost of roughly ₹2.7 lakh on-road (₹2.45 lakh ex-showroom plus roughly ₹25,000 of homologation, registration, and dealer-fitted bits), the CBR150R has to compete with the R15 V4 at ₹1.95 lakh on-road, the Apache RTR 200 4V at ₹1.58 lakh, and the Pulsar NS200 at ₹1.62 lakh. None of those bikes match the CBR150R on chassis hardware, but all three undercut it on price by ₹70,000 to ₹1.1 lakh.",
  },
  {
    type: "p",
    text: "The Indian buyer profile for a CBR150R is the rider who has already owned an R15 V4 and wants a more refined engine plus the Honda quality dividend. The K56F has a documented 30,000+ km major-service interval, against the R15 V4 cassette which most owners report needing chain-and-sprocket attention at 18,000 km and valve-clearance work at 24,000 km. For a high-mileage owner the ₹70,000 premium pays back over five years; for a strip-only rider it does not.",
  },
  {
    type: "p",
    text: "Indian-market mods that move the needle on a CBR150R, ranked by cost-per-tenth based on the seed parts catalogue:",
  },
  {
    type: "table",
    rows: [
      ["Mod", "Cost (₹)", "ET gain", "₹/tenth"],
      ["14F/42R sprocket swap", "1,200", "0.09 s", "~1,333"],
      ["K&N drop-in air filter (HA-1287 cross-fit)", "3,800", "0.04 s", "~9,500"],
      ["Lithium battery (Shorai LFX09, –2.4 kg)", "6,800", "0.04 s", "~17,000"],
      ["BMC race air filter (HRC-spec slip)", "4,400", "0.03 s", "~14,700"],
      ["Powertronic ECU flash (grey-market)", "18,000", "0.05 s", "~36,000"],
    ],
  },
  {
    type: "p",
    text: "The sprocket swap is by far the best tenth on the bike — under ₹1,500 per tenth puts it in the top quartile of cost-per-tenth ratios across the entire 150-class catalogue. After that, the air filter and the lithium battery are the diminishing-returns pair to chase. The Powertronic ECU flash exists for the K56F but is exclusively a grey-market product (Powertronic does not officially support a bike Honda India does not sell), and the 0.05 s gain at ₹36,000 per tenth makes sense only for an owner who also values the throttle response and the fuel-mapping refinement that the flash brings beyond peak power.",
  },
  {
    type: "callout",
    text: "Cheapest strip-prep path on a CBR150R: 14F/42R sprockets (₹1,200, 0.09 s) plus a Shorai lithium battery (₹6,800, 0.04 s) plus the K&N drop-in filter (₹3,800, 0.04 s) — total ₹11,800 for 0.17 s of ET. That is one-third the price of a slip-on exhaust for nearly twice the ET gain. On a 17 hp bike, mass and gearing dominate everything else.",
  },
  {
    type: "h2",
    text: "Gearing Math — Where the 5th-Gear Trap Comes From",
  },
  {
    type: "p",
    text: "Stock gearing on the K56F cassette is [2.833, 1.875, 1.400, 1.133, 0.969, 0.852] from Honda service-manual reference for the 2021 facelift. Combined with the 15F/40R sprocket pair and a 130/70-17 rear (rolling radius approximately 290 mm), the bike hits its 9,000 rpm power peak at exactly 38 km/h in first, 57 km/h in second, 76 km/h in third, 94 km/h in fourth, 110 km/h in fifth, and a theoretical 125 km/h in sixth. The simulator's 130.5 km/h trap speed sits four km/h past where fifth-gear redline would land — the bike is crossing the line at 9,200 rpm in fifth, which is 200 rpm past peak power and just under the 11,000 rpm soft limiter.",
  },
  {
    type: "p",
    text: "The 14F/42R swap shifts every shift-point downward by 6.7 percent. First becomes 35 km/h, fifth becomes 102 km/h, and the bike crosses the trap line at 122 km/h in fifth instead of bouncing off the rev limiter in fifth at 110 km/h. Net effect on the simulator is roughly 0.09 s of ET savings across the run, with most of the saving coming from the first 80 metres where the bike spends gears one and two. After 200 metres the shorter gearing actually loses a fraction of a tenth to the stock setup because the engine spends more time in the upper revs across all gears — but the launch-phase savings dominate.",
  },
  {
    type: "p",
    text: "Going more aggressive — 13F/42R or 14F/44R — eats into sixth-gear cruising above 100 km/h, where most Indian grey-market owners actually ride the bike. A 14F/42R is the sweet spot for an owner who wants the strip gain without giving up the highway. A 13F/40R is the configuration the Malaysian SuperRimba 150 cc grid runs, but those bikes never see a road above 80 km/h between events.",
  },
  {
    type: "h2",
    text: "Run Your Own Numbers",
  },
  {
    type: "p",
    text: "If you are considering a CBR150R grey-market import or already own one and want to know what the bike's strip ceiling actually is, the simulator at motoquant.in lets you sweep rider weight, ambient temperature, density altitude, and parts-catalogue mods to see where each tenth lives. The 1.84 s cluster bias is baked into the model — use the relative deltas. When the sim says the CBR150R is 0.08 s quicker than the R15 V4, that delta holds at the strip even if both bikes run absolute times a second or two quicker than the simulator predicts on a hot launch.",
  },
  {
    type: "p",
    text: "More usefully, the parts ROI engine breaks down cost-per-tenth for every part in the catalogue against the bike you select. On a 150-class commuter the ladder always comes out gearing-first, mass-second, breathing-third, and exhaust-fourth — with ECU somewhere between fourth and irrelevant depending on the platform. The CBR150R is no different. Spending ₹38,000 on a slip-on for 0.04 s on the K56F is a different conversation than spending ₹11,800 on sprockets-plus-filter-plus-battery for 0.17 s. The simulator is built to make exactly that conversation easier, and the parts ladder for the CBR150R is one of the cleaner ones in the small-cc segment because the platform is purpose-built for what Honda set out to make it do.",
  },
  {
    type: "p",
    text: "Two caveats. First, the absolute ETs in this post are simulator output under specific conditions — change the rider weight, the surface, the temperature, or the launch technique and the numbers shift. The CBR150R will run quicker than 18.42 seconds at the strip in real life; expect 16.6 to 17.5 s depending on rider technique, with the MotoStatz instrumented test as the published reference point. Second, the +1.84 s cluster bias is a known artefact of how the model treats clutch slip on sub-20 hp bikes. Future calibrator passes will narrow it as the Indian and SE Asia Dragy submission corpus grows.",
  },
  {
    type: "p",
    text: "The CBR150R remains an oddity in the Indian market — a Honda 150 that costs ₹70,000 more than an R15 V4 and out-traps every faired 150 in the catalogue. If the grey-market price ever drops below ₹2.3 lakh it becomes a genuine alternative to the R15 V4 for buyers who value Honda's long-term refinement over the Yamaha's last horsepower. Until then, the CBR150R is a bike for connoisseurs of the K56F engine and for the rare Indian rider who has already lapped the strip on a Duke 390 and wants something smaller, lighter, and stranger to track on the weekends.",
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
          datePublished: "2026-05-26",
        })}
      />
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {["Honda", "CBR150R", "K56F", "150cc", "SE Asia", "physics"].map(
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
            Honda CBR150R Quarter-Mile Physics: 17hp SE Asia Sport Single
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
            26 May 2026 · 11 min read · MotoQuant Blog
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
                href="/blog/honda-cb125r-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Honda CB125R Quarter-Mile Physics
              </Link>{" "}
              — the smaller Neo Sports Café sibling with the same small-cc
              cluster bias story and the same grey-market import math.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/why-your-r15-wont-hit-14s"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Why Your R15 V4 Won&apos;t Hit 14s
              </Link>{" "}
              — the Indian-market 155cc rival the CBR150R beats by 0.08 s
              despite a one-horsepower deficit.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/yamaha-mt-15-v1-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Yamaha MT-15 V1 Quarter-Mile Physics
              </Link>{" "}
              — the naked R15 platform that the CBR150R out-traps by 18 km/h
              despite making less power.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-to-tune-for-aamby-valley-in-november"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to Tune for Aamby Valley in November
              </Link>{" "}
              — the venue and conditions used for every sim ET in this post.
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
              Run the CBR150R yourself
            </div>
            <div className="text-white/60 text-sm">
              Free simulator — pick the Honda CBR150R, dial in your local
              conditions, and watch the ET update live as you toggle sprockets,
              air filters, and lithium batteries.
            </div>
          </div>
          <Link
            href="/simulator?bike=honda-cbr150r"
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
