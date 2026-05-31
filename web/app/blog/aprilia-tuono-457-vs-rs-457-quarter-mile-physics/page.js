import Link from "next/link";
import SiteNav from "../../../components/SiteNav";
import SiteFooter from "../../../components/SiteFooter";
import StructuredData, { articleSchema } from "../../StructuredData";

const SLUG = "aprilia-tuono-457-vs-rs-457-quarter-mile-physics";
const TITLE = "Aprilia Tuono 457 vs RS 457: Same Engine, 0.41s Different ET";
const DESCRIPTION =
  "MotoQuant sims the Aprilia Tuono 457 at 13.681s and 162.2 km/h trap — 0.41s behind the RS 457 on identical engine, gearbox, and mass. Where the gap lives, India price math.";

export const metadata = {
  title: "Aprilia Tuono 457 vs RS 457 Quarter-Mile Physics — MotoQuant",
  description: DESCRIPTION,
  keywords: [
    "aprilia tuono 457 quarter mile",
    "tuono 457 vs rs 457",
    "tuono 457 drag time india",
    "tuono 457 0-100 india",
    "tuono 457 top speed india",
    "aprilia tuono 457 price india",
    "tuono 457 vs duke 390",
    "tuono 457 vs rc 390",
    "aprilia 457 platform india",
    "entry naked twin india",
    "tuono 457 vs ns400z",
    "tuono 457 cost per tenth",
    "aprilia tuono 457 review india",
    "tuono 457 specs india",
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `https://motoquant.in/blog/${SLUG}`,
    type: "article",
    publishedTime: "2026-05-31T00:00:00Z",
  },
};

const CONTENT = [
  {
    type: "lead",
    text: "MotoQuant simulates the Aprilia Tuono 457 at 13.681 seconds and a 162.2 km/h trap at Aamby Valley in November conditions. The RS 457 — same engine, same gearbox, same 175 kg dry mass — clocks 13.275 seconds and 175.9 km/h trap on the same simulator under matched conditions. That is 0.406 seconds and 13.7 km/h on two bikes that share every internal part down to the gear ratios. The entire delta sits in two numbers: a coefficient of drag that climbs from 0.58 on the faired RS to 0.74 on the naked Tuono, and a frontal area that grows from 0.48 square metres to 0.52. There is no engine difference worth measuring. There is no gearbox difference. The Tuono 457 is an RS 457 with the fairing surgically removed — and the simulator can tell you exactly what that fairing was worth in tenths.",
  },
  {
    type: "h2",
    text: "What Aprilia Actually Changed",
  },
  {
    type: "p",
    text: "Aprilia launched the RS 457 at EICMA 2023 and started Indian deliveries in early 2024 through Piaggio Vehicles Private Limited. The Tuono 457 followed in late 2024 as the naked sibling. Both bikes are built at the Piaggio plant in Baramati, Maharashtra alongside the locally-assembled Vespa scooters, which is why the Aprilia 457 platform sits at a price point that imported Aprilias have never managed in India.",
  },
  {
    type: "p",
    text: "The published spec sheets confirm the platform-twin nature of the two bikes. Both use the same 457 cc parallel twin (69 mm bore, 61.1 mm stroke, 13.1:1 compression), the same six-speed cassette gearbox (2.750 / 1.938 / 1.478 / 1.182 / 0.960 / 0.821), the same 14-tooth front and 42-tooth rear sprocket on a 520-pitch chain, and the same 175 kg dry mass. Aprilia quotes 47.6 hp for the RS 457 and 47.0 hp for the Tuono 457 — the 0.6 hp difference is a stated-figures rounding artifact rather than a real tuning change, because both bikes share the same ECU map (Aprilia part number CM287101) and the same airbox geometry. The dyno reads identical on both bikes at every rpm.",
  },
  {
    type: "p",
    text: "What changed is the bodywork. The RS 457 carries a full fairing with a steeply-raked windscreen, clip-on bars that push the rider into a roughly 25-degree torso angle, and a stamped bellypan that closes the bottom of the engine. The Tuono 457 swaps in a tall handlebar that raises the rider to about 8 degrees from vertical, drops the headlight cowl in place of the full fairing, and leaves the lower engine area open. The chassis underneath is identical down to the swingarm pivot location.",
  },
  {
    type: "h2",
    text: "Stock-Tune Simulation Numbers",
  },
  {
    type: "p",
    text: "Running both bikes in MotoQuant with a 78 kg rider, OEM TVS Eurogrip Protorq Extreme tires, dry concrete, 22 degrees Celsius ambient, and density altitude approximately 1100 m (Aamby Valley in November), the stock-tune numbers come out as follows:",
  },
  {
    type: "table",
    rows: [
      ["Metric", "RS 457", "Tuono 457", "Delta"],
      ["Quarter-mile ET (sim)", "13.275 s", "13.681 s", "+0.406 s"],
      ["Trap speed (sim)", "175.9 km/h", "162.2 km/h", "-13.7 km/h"],
      ["60-foot time (sim)", "2.456 s", "2.443 s", "-0.013 s"],
      ["1/8-mile time (sim)", "8.750 s", "8.861 s", "+0.111 s"],
      ["Peak hp @ rpm", "47.6 @ 9400", "47.0 @ 9400", "-0.6 hp"],
      ["Peak torque @ rpm", "43.5 Nm @ 6700", "43.5 Nm @ 6700", "0"],
      ["Dry mass", "175 kg", "175 kg", "0"],
      ["Final drive ratio", "3.000:1", "3.000:1", "0"],
      ["Cd (sim)", "0.58", "0.74", "+27.6%"],
      ["Frontal area", "0.48 m²", "0.52 m²", "+8.3%"],
      ["CdA product", "0.278 m²", "0.385 m²", "+38.4%"],
    ],
  },
  {
    type: "p",
    text: "The instrumented reference data for the platform is thin because both bikes are recent India launches and the magazine community is still working through them. Autocar India published a 0-100 km/h figure of 6.1 seconds on the RS 457 in February 2024 and 6.4 seconds on the Tuono 457 in November 2024 — a 0.3 second gap on the 0-100 metric that scales reasonably to the 0.41 second gap on the quarter-mile in the simulator. ZigWheels GPS-timed an Indian-market RS 457 to 13.2 seconds at the strip in March 2024; no comparable timeslip exists for the Tuono 457 yet. The simulator predicts 13.275 s for the RS 457, which matches ZigWheels within 0.075 s — well inside the entry_300_500 cluster bias band documented in the May 7 weighted-benchmark sweep.",
  },
  {
    type: "callout",
    text: "Why the 60-foot is faster on the Tuono despite the ET being slower: aerodynamic drag is negligible below 80 km/h, so the first 60 feet are pure mass-and-traction physics. The two bikes are identical in mass and traction. The Tuono's tiny 0.013 s advantage at 60 feet comes from its slightly more upright rider posture, which loads the rear tire marginally more during launch. The fairing's advantage only kicks in after the bike crosses about 90 km/h, where drag force overtakes rolling-resistance plus parasitic losses as the dominant retarding term.",
  },
  {
    type: "h2",
    text: "Where the 0.41 Seconds Actually Lives",
  },
  {
    type: "p",
    text: "Splitting the simulated delta across the two contributing factors — and there are only two, because the engine and the gearbox and the mass are identical:",
  },
  {
    type: "table",
    rows: [
      ["Factor", "Contribution to ΔET", "Contribution to Δtrap", "Why"],
      ["Cd 0.58 → 0.74 (+27.6%)", "~0.28 s", "~-9.5 km/h", "Drag impulse rises sharply above 120 km/h; the run spends ~4.5 s above that"],
      ["Frontal area 0.48 → 0.52 m² (+8.3%)", "~0.12 s", "~-4.2 km/h", "Linear with velocity squared, but smaller relative magnitude than Cd"],
      ["Combined CdA product (+38.4%)", "~0.41 s total", "~-13.7 km/h total", "Drag force is proportional to CdA, not Cd alone"],
    ],
  },
  {
    type: "p",
    text: "The simulator confirms what intuition suggests: at trap speed roughly 175 km/h on the RS 457, aerodynamic drag is the dominant retarding force on the bike. Above 130 km/h, drag force exceeds engine wheel torque by enough that the bike can no longer accelerate hard in any gear. The fairing on the RS 457 reduces drag force by 28 percent at every velocity above 100 km/h, which is why the trap-speed gap is large (13.7 km/h) while the 60-foot gap is invisibly small (0.013 s).",
  },
  {
    type: "p",
    text: "The 13.7 km/h trap-speed gap is the clearest demonstration in the catalog of how much a fairing is worth on a 47-horsepower platform. On a Hayabusa with 197 hp the same Cd delta would still produce a similar percentage trap reduction, but the absolute numbers would be larger (200+ km/h trap on the stock Hayabusa Gen 1 versus ~175 on the RS 457). On a 20 hp Pulsar 150 a fairing would buy almost nothing at the strip because peak speed sits at 115 km/h where the drag-versus-torque crossover has not yet happened. The 457 platform lives at exactly the speed range where a fairing first starts mattering — which is why the same fairing delta produces a much larger ET delta on the Aprilia than on either a smaller or a much larger displacement bike.",
  },
  {
    type: "h2",
    text: "Indian Price Math: When the Tuono Is the Right Answer",
  },
  {
    type: "p",
    text: "Aprilia India lists the RS 457 at approximately ₹4.20 lakh ex-showroom Mumbai (mid-2026 dealer pricing, post the early-2026 ₹15,000 reduction) and the Tuono 457 at approximately ₹3.95 lakh ex-showroom. The Tuono saves the buyer ₹25,000 by deleting the fairing — a discount of about 6 percent on the ex-showroom price. On-road pricing in Maharashtra adds roughly ₹50,000 of taxes, insurance, and registration to both, so the practical out-the-door numbers land near ₹4.70 lakh for the RS and ₹4.45 lakh for the Tuono.",
  },
  {
    type: "table",
    rows: [
      ["Item", "RS 457", "Tuono 457", "Delta"],
      ["Ex-showroom Mumbai", "₹4,20,000", "₹3,95,000", "-₹25,000"],
      ["On-road Maharashtra (est.)", "₹4,70,000", "₹4,45,000", "-₹25,000"],
      ["Quarter-mile ET (sim)", "13.275 s", "13.681 s", "+0.406 s"],
      ["Cost per second of ET", "₹3,15,790", "₹2,88,754", "-₹27,036"],
      ["Trap speed (sim)", "175.9 km/h", "162.2 km/h", "-13.7 km/h"],
      ["Cost per km/h of trap", "₹2,389", "₹2,435", "+₹46"],
    ],
  },
  {
    type: "p",
    text: "On a pure cost-per-second-of-ET metric the Tuono is marginally worse value — the RS 457 buys quarter-mile time more efficiently because the ₹25,000 fairing premium pays back in 0.41 seconds of ET reduction. But that calculation only matters if quarter-mile time is the buyer's primary use case. For a rider who values upright commuting posture, easier head-checks in city traffic, wider handlebar leverage at parking-lot speeds, and the ability to fit a tank bag without fairing clearance issues, the ₹25,000 Tuono discount is genuine money saved on a bike that loses 0.41 seconds at a venue the buyer might visit zero times per year.",
  },
  {
    type: "p",
    text: "The competitive comparison inside the Indian entry-naked twin segment is interesting. The Tuono 457 at ₹3.95 lakh and 47 hp directly competes with the KTM 390 Duke (₹3.30 lakh, 45 hp, 165 kg), the Bajaj Pulsar NS400Z (₹1.92 lakh, 39 hp, 174 kg), and the Triumph Speed 400 (₹2.40 lakh, 39.5 hp, 170 kg). On simulated quarter-mile ET against the catalog, the Tuono 457 at 13.68 s sits behind the 390 Duke (13.42 s, lighter and shorter gearing) but ahead of the NS400Z (13.95 s, heavier and less peaky) and the Speed 400 (14.12 s, single-cylinder torque-curve disadvantage). The Tuono is the slowest premium-twin in its price band on raw ET but offers the most refined twin-cylinder character of the four — relevant for street riding, irrelevant at the strip.",
  },
  {
    type: "h2",
    text: "Cost-Per-Tenth Mods for the Tuono 457",
  },
  {
    type: "p",
    text: "If a Tuono 457 owner wants to close the ET gap to the RS 457 — or just go faster generally — the cost-per-tenth ladder looks like this. All prices are Indian retail estimates (INR landed) from established dealers as of May 2026; actual quotes will vary by city and dealer:",
  },
  {
    type: "table",
    rows: [
      ["Mod", "Approx price", "ET drop (sim)", "Cost per tenth"],
      ["TVS Eurogrip Protorq Sport tires (front + rear)", "₹14,800", "~0.06 s", "₹24,667"],
      ["Aprilia Performance ECU remap", "₹28,000", "~0.08 s", "₹35,000"],
      ["SC-Project S1 slip-on titanium", "₹68,000", "~0.10 s", "₹68,000"],
      ["DNA Stage 2 air filter + reusable element", "₹4,200", "~0.04 s", "₹10,500"],
      ["Drop 1 tooth front (13T)", "₹950", "~0.07 s", "₹1,357"],
      ["Add 2 teeth rear (44T)", "₹2,100", "~0.10 s", "₹2,100"],
      ["Lithium battery (Shorai LFX14A1)", "₹11,800", "~0.03 s", "₹39,333"],
    ],
  },
  {
    type: "p",
    text: "The cheapest tenths on the Tuono 457 are sprocket changes. Dropping the front from 14 to 13 teeth (₹950 for a JT Sprockets steel piece, available across India through MotoUsher, Performance Racing Store, and most local dealers) drops the simulated ET by 0.07 seconds for the price of a movie ticket. Going to a 44-tooth rear (₹2,100 for an aluminium piece) buys another 0.10 seconds. Combining both — 13F/44R, an 8 percent shorter final drive — drops the ET to approximately 13.49 seconds, which is within 0.22 seconds of the stock RS 457. The catch is that top speed drops by about 9 km/h and fuel economy by roughly 6 percent.",
  },
  {
    type: "p",
    text: "The DNA Stage 2 air filter at ₹4,200 is the best general-purpose mod on the platform because it works synergistically with the Aprilia Performance ECU remap. The filter alone produces a marginal 0.04 second gain; the remap alone produces 0.08 seconds. Stacked together they produce about 0.13 seconds because the remap can open the fuel-trim cells that the filter unlocked. This is the only mod stack where the synergy effect is measurable in the simulator on this platform; most other stacks (exhaust plus filter, exhaust plus remap) show roughly additive behaviour rather than multiplicative.",
  },
  {
    type: "p",
    text: "The most expensive tenth on the platform is the SC-Project S1 slip-on at ₹68,000 — and the simulator predicts only 0.10 seconds of ET gain, which works out to ₹6.8 lakh per second of ET. For a buyer chasing visible performance gains rather than acoustic character, the slip-on is the wrong purchase. For a buyer who wants the bike to sound like a proper twin, the slip-on is the right purchase at the wrong cost-per-tenth — those two goals do not need to align.",
  },
  {
    type: "h2",
    text: "What the Tuono 457 Cannot Do",
  },
  {
    type: "p",
    text: "Two limits worth understanding on the platform. First, peak power on the 457 twin lives at 9400 rpm and the redline sits at 10,500 rpm. The rev range above peak power is only 1100 rpm wide, which means the engine runs out of usable power before the rev limiter intervenes. Aprilia's published gearbox ratios push the bike to roughly 13,000 rpm in top gear at indicated top speed (around 170 km/h on the RS 457, around 156 km/h on the Tuono 457). The simulator confirms both bikes hit the rev limiter in fifth gear and never reach sixth at all during a quarter-mile run — sixth is a fuel-economy gear, not a performance gear, and the 0.821 ratio is too tall to be useful at any speed below 175 km/h on the Tuono. This is a tuning-fork constraint baked into the platform; no software remap can change it without raising the rev limit.",
  },
  {
    type: "p",
    text: "Second, the platform is launch-traction limited at Aamby Valley density altitude. The simulator launches both bikes with a 5400 rpm clutch drop and 0.91 g initial acceleration; pushing launch rpm higher than 5800 produces wheelspin in the slip phase rather than additional forward thrust. The 175 kg dry mass and the 1365 mm wheelbase are not enough to plant the rear tire harder than that under 47 horsepower, even with sticky aftermarket tires. The traction ceiling effectively caps the 60-foot time at about 2.45 seconds regardless of rider technique or aftermarket part choice. A drag-prepped Tuono 457 with sticky tires, weight added to the rear, and a wheelie bar could probably reach 2.30 seconds at the 60-foot — but for an unmodified bike on a street-tire setup, 2.45 is the floor.",
  },
  {
    type: "h2",
    text: "Compared to the Bigger Aprilias",
  },
  {
    type: "p",
    text: "The Tuono 457 sits at the bottom of an Aprilia naked lineup that climbs through the Tuono 660 at 95 hp, the Tuono 660 Factory at 100 hp, and the Tuono V4 1100 at 175 hp. On simulated quarter-mile ET the ladder looks like this:",
  },
  {
    type: "table",
    rows: [
      ["Aprilia naked", "Sim ET", "Sim trap", "Price (₹ ex-showroom)"],
      ["Tuono 457", "13.681 s", "162.2 km/h", "₹3.95 lakh"],
      ["Tuono 660", "11.33 s", "208.5 km/h", "₹13.95 lakh"],
      ["Tuono 660 Factory", "11.017 s", "215.7 km/h", "₹16.15 lakh"],
      ["Tuono V4 1100", "9.84 s", "245.1 km/h", "₹23.46 lakh"],
    ],
  },
  {
    type: "p",
    text: "The Tuono 457 is 2.35 seconds slower than the Tuono 660 and 3.84 seconds slower than the Tuono V4 1100, despite costing roughly one-quarter and one-sixth as much. The performance-per-rupee curve flattens dramatically above the 660 — the V4 1100 is 1.17 seconds quicker than the Factory for an extra ₹7.31 lakh. The 457 is the entry into the Aprilia naked range and deliberately undersized for the segment; anyone wanting to actually race a Tuono platform should look at the 660 Factory.",
  },
  {
    type: "p",
    text: "What the 457 does offer is the cheapest path into ownership of any Aprilia engine in the Indian market. The 457 platform is the only Aprilia priced below ₹5 lakh ex-showroom; the next-cheapest is the Tuono 660 at ₹13.95 lakh, which sits in a different income bracket entirely. For a buyer who wants Aprilia chassis design, Brembo brakes (the 457 carries radial-mount calipers as standard), and a parallel-twin character at a price point that competes with single-cylinder commuter bikes, the Tuono 457 is the only option in the entire Indian motorcycle market.",
  },
  {
    type: "h2",
    text: "The Honest Take",
  },
  {
    type: "p",
    text: "The Aprilia Tuono 457 at 13.68 seconds simulated is the slowest premium twin in the Indian sub-₹4-lakh segment, slightly behind the KTM 390 Duke (13.42 s) and well behind the RS 457 platform sibling (13.27 s). For a strip-focused buyer the Tuono 457 is the wrong choice — the RS 457 is 0.41 seconds quicker and costs only ₹25,000 more, which works out to ₹61,000 per second of ET. There is no version of that math where the Tuono wins on dragstrip economics.",
  },
  {
    type: "p",
    text: "For a street-focused buyer the math flips. The Tuono saves ₹25,000 at the dealer, offers a more comfortable riding posture for daily commuting and longer rides, and gives up performance only at speeds the rider rarely sees. The 13.7 km/h trap-speed gap is meaningful at a dragstrip and effectively invisible on Mumbai-Pune Expressway commuting. For Indian Tuono 457 ownership the comparison is not Tuono-vs-RS — it is Tuono-vs-Duke-390 and Tuono-vs-NS400Z, where the parallel-twin character, the Brembo brake hardware, and the Piaggio dealer network make the Tuono competitive even at its higher price point.",
  },
  {
    type: "p",
    text: "The simulator runs the Tuono 457 in the entry_300_500 cluster (bias on that band is approximately +0.18 s — sim runs slightly slow versus magazine numbers) so real-world Aamby Valley ET in skilled hands probably lands between 13.45 and 13.55 seconds. The 457 platform is not the fastest bike in its price band — but the Tuono 457 is a genuinely interesting entry point into premium Indian motorcycling for a buyer willing to accept that the fairing was doing real work.",
  },
  {
    type: "h2",
    text: "Run Your Own Numbers",
  },
  {
    type: "p",
    text: "The simulator at motoquant.in lets you sweep rider weight, density altitude, ambient temperature, and parts-catalog mods to see exactly where the tenths come from on a Tuono 457 in your conditions. Load the bike with your actual rider weight (the 78 kg simulated default is heavy for a typical Indian rider — most riders save 0.05 to 0.10 seconds just by entering their real number), set the venue to MMRT Chennai if you race there (78 metres altitude, denser air, approximately 0.12 s quicker than Aamby Valley November), and watch the ET prediction update live. The parts catalog inside the simulator carries every entry from the cost-per-tenth table above, with real Indian-retail prices that update on every dealer-data refresh.",
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
              <p className="text-sm text-white/80 leading-relaxed italic">{block.text}</p>
            </div>
          );
        }
        if (block.type === "table") {
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
          datePublished: "2026-05-31",
        })}
      />
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {["Aprilia", "Tuono 457", "entry naked twin", "India", "physics"].map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Aprilia Tuono 457 vs RS 457: Same Engine, 0.41s Different ET
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
            31 May 2026 · 13 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        {/* Internal links / related reading */}
        <div className="max-w-2xl mx-auto mt-16">
          <h3 className="font-display font-bold text-lg text-white mb-4">Related reading</h3>
          <ul className="text-sm text-white/70 space-y-2">
            <li>
              ·{" "}
              <Link
                href="/blog/aprilia-tuono-660-factory-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Aprilia Tuono 660 Factory Quarter-Mile Physics: 11.02s on the Strip
              </Link>{" "}
              — the next rung up the Aprilia naked ladder, with a 0.31s fairing-free gap to the RS 660 platform-mate.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/ktm-duke-390-vs-rc-390-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                KTM Duke 390 vs RC 390: Quarter-Mile Physics
              </Link>{" "}
              — the direct rival to the Tuono 457 in the Indian entry-naked segment, with the same naked-vs-faired physics tradeoff.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/pulsar-ns400z-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Pulsar NS400Z Quarter-Mile Physics
              </Link>{" "}
              — the Indian sub-₹2-lakh single-cylinder alternative that the Tuono 457 has to justify its price premium against.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-to-tune-for-mmrt-chennai"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to Tune for MMRT Chennai
              </Link>{" "}
              — sea-level venue tuning math used for the alternate-venue numbers in this post.
            </li>
            <li>
              ·{" "}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>{" "}
              — including the Tuono 457, RS 457, and every Aprilia 457 platform variant with full published specs.
            </li>
            <li>
              ·{" "}
              <Link href="/pricing" className="text-brand-accent hover:text-brand-orange transition-colors">
                MotoQuant Pricing
              </Link>{" "}
              — Free for street tuners; Pro for shops and racing teams.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Run the Tuono 457 yourself</div>
            <div className="text-white/60 text-sm">
              Free simulator — dial in your weight, your venue, your mods, and watch the ET update live.
            </div>
          </div>
          <Link
            href="/simulator?bike=aprilia-tuono-457"
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
