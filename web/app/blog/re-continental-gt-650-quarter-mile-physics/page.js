import Link from "next/link";
import SiteNav from "../../../components/SiteNav";
import SiteFooter from "../../../components/SiteFooter";
import StructuredData, { articleSchema } from "../../StructuredData";

const SLUG = "re-continental-gt-650-quarter-mile-physics";
const TITLE = "Royal Enfield Continental GT 650 Quarter-Mile Physics";
const DESCRIPTION =
  "MotoQuant simulates the RE Continental GT 650 at ~14.1s and 158 km/h trap. Where the 47 hp air/oil-cooled twin loses tenths to its 650cc peers at Aamby Valley.";

export const metadata = {
  title: "RE Continental GT 650 Quarter-Mile Physics — MotoQuant",
  description: DESCRIPTION,
  keywords: [
    "Continental GT 650 quarter mile",
    "Continental GT 650 drag time",
    "Continental GT 650 top speed",
    "Royal Enfield 650 twin",
    "GT 650 vs Interceptor 650 drag",
    "interceptor 650 vs continental gt 650 quarter mile",
    "re 650 twins acceleration",
    "interceptor 650 drag time",
    "Indian 650 cafe racer",
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `https://motoquant.in/blog/${SLUG}`,
    type: "article",
    publishedTime: "2026-05-18T00:00:00Z",
  },
};

const CONTENT = [
  {
    type: "lead",
    text: "MotoQuant simulates the Royal Enfield Continental GT 650 at roughly 14.1 seconds and 158 km/h trap under Aamby Valley November conditions. The 648 cc air/oil-cooled parallel twin makes 47 hp at 7,150 rpm and 52 Nm at 5,250 rpm out of an 78 mm bore and 67.8 mm stroke — a deliberately under-stressed engine that runs the same internals as the Interceptor 650 but wears a clip-on cafe-racer body. On a strip, the spec sheet is only half the story; the chassis, the gearing, and a 182 kg dry mass do most of the talking.",
  },
  {
    type: "h2",
    text: "What the Continental GT 650 Actually Is",
  },
  {
    type: "p",
    text: "The Continental GT 650 launched in 2018 alongside the Interceptor 650 on a shared Harris-designed steel-tube cradle frame. Both bikes use the same SOHC, 4-valve-per-cylinder, 270-degree-crank parallel twin — same 78 mm bore, same 67.8 mm stroke, same 9.5:1 compression, same 47 hp at 7,150 rpm, same 52 Nm at 5,250 rpm. The differences are cosmetic and ergonomic: clip-on bars and rearsets on the GT, an upright bar and mid-controls on the Interceptor. Royal Enfield rates both at 198 kg kerb mass; MotoQuant uses 182 kg dry as the comparable number.",
  },
  {
    type: "p",
    text: "For drag analysis the GT 650 is interesting precisely because it is not a sport bike pretending to be a cafe racer — it is an unstressed twin built to deliver torque at low rpm and survive 50,000 km of badly maintained Indian-highway riding. Peak power lives at 7,150 rpm, redline sits around 7,500, and the meaty part of the torque curve is from about 3,000 to 6,500 rpm. The simulator treats the GT 650 as a mid-twin-500-700 cluster bike — same class as the Kawasaki Ninja 650, Yamaha MT-07, and Aprilia RS 660 — and the cluster bias band is +0.16 seconds, well within tolerance.",
  },
  {
    type: "h2",
    text: "Stock-Tune Simulation Numbers",
  },
  {
    type: "p",
    text: "Running the Continental GT 650 in MotoQuant under Aamby Valley November conditions (density altitude ~1,100 m, 22°C ambient, dry concrete with the OEM Pirelli Phantom Sportscomp 130/70-18 rear at μ_peak 1.20) and a 78 kg rider on the 182 kg dry bike produces the following stock-tune output:",
  },
  {
    type: "table",
    rows: [
      ["Metric", "Value", "Source"],
      ["Quarter-mile ET", "~14.1 s", "MotoQuant sim"],
      ["Trap speed", "~158 km/h", "MotoQuant sim"],
      ["60-foot time", "~2.45 s", "MotoQuant sim"],
      ["Manufacturer top speed", "~163 km/h", "Royal Enfield official"],
      ["Cluster bias band", "+0.16 s", "mid-twin-500-700"],
    ],
  },
  {
    type: "p",
    text: "The mid-twin-500-700 cluster is one of the better-calibrated bands in the simulator — N=14 matched benchmarks with mean absolute error of 0.615 seconds and a near-zero bias of -0.133 seconds (centred). The GT 650 result is sim-only as of this writing; no published Indian Autos Mag or Sport Rider instrumented quarter-mile has surfaced for the bike. MCN ran an Interceptor 650 in 2018 and clocked roughly 14.2 seconds at 162 km/h with a competent UK rider on a warmed bike, which lines up almost exactly with the simulator output once you account for the difference in rider weight and density altitude.",
  },
  {
    type: "callout",
    text: "The GT 650 and the Interceptor 650 share an engine, a frame, and a 6-speed gearbox. The GT is roughly 0.05 seconds quicker in the simulator under matched conditions because the clip-on riding position lowers the rider CoG by about 40 mm and tightens the projected frontal area from ~0.50 m² to ~0.46 m². Past 130 km/h the GT pulls slightly cleaner, which shows up as a small trap-speed edge rather than a launch advantage.",
  },
  {
    type: "h2",
    text: "Why the GT 650 Runs Mid-14s and Not Low-13s",
  },
  {
    type: "p",
    text: "On power-to-weight, the GT 650 sits at 47 hp / 182 kg dry (~258 hp/tonne). For comparison, the Aprilia RS 660 runs 100 hp / 169 kg dry (~592 hp/tonne) and the Kawasaki Ninja 650 runs 67 hp / 192 kg dry (~349 hp/tonne). The RS 660 sims around 11.4 seconds, the Ninja 650 around 13.0 seconds, the GT 650 around 14.1 seconds. Three structural factors account for the gap:",
  },
  {
    type: "p",
    text: "1. Peak-power RPM. The GT 650 makes its 47 hp at 7,150 rpm and redlines at 7,500. The Ninja 650 makes 67 hp at 8,000 and redlines at 11,000. The Aprilia RS 660 makes 100 hp at 10,500 and redlines at 11,500. Every additional 1,000 rpm of usable headroom translates into more time in each gear in the meaty part of the curve, which means more area under the torque-versus-time integral, which means more momentum carried into the next gear. The GT 650 has the shortest usable rev band of the three by a wide margin, and the bike is forced to upshift while its peers are still pulling.",
  },
  {
    type: "p",
    text: "2. Air/oil cooling. The GT 650 is air/oil cooled with a small oil cooler under the engine; no liquid jacket, no thermostat-controlled coolant loop. Over consecutive runs the head and barrel heat-soak quickly, and on a hot 35°C Aamby Valley afternoon by run three or four the simulator predicts a 4-6% peak-power loss from intake-air-temperature creep alone. The Ninja 650 and the RS 660 are both liquid-cooled and hold steady through a full session. MotoQuant does not currently model run-to-run heat soak as a first-class effect, so the 14.1-second number flatters the GT slightly relative to a real second-half-of-session timeslip.",
  },
  {
    type: "p",
    text: "3. Gearing. The GT 650 runs gear ratios [3.071, 2.056, 1.583, 1.292, 1.125, 1.000] with 16F/43R sprockets on a 520 chain, and a rear tire rolling radius of about 305 mm. With those numbers, sixth gear at 7,150 rpm gives roughly 165 km/h — almost exactly the manufacturer-claimed top speed. The bike is gearing-limited rather than power-limited at the top end, which is intentional: Royal Enfield ships the GT 650 with a single 6th gear ratio of 1.000 (a non-overdriven top gear, unlike most 650 twins) precisely because the engine cannot hold redline against drag past 165 km/h on stock gearing. The simulator log shows the GT crossing the trap line in fifth gear at about 6,400 rpm.",
  },
  {
    type: "h2",
    text: "What Actually Limits the Continental GT 650 in the Quarter",
  },
  {
    type: "p",
    text: "In order of impact for a stock bike:",
  },
  {
    type: "p",
    text: "1. Aerodynamics. The clip-on bars give a forward-leaning rider position, which is genuinely better than the Interceptor's upright posture for trap speed. The simulator uses a Cd of 0.68 and a frontal area of 0.46 m² for the GT versus 0.72 and 0.50 m² for the Interceptor. From 80 km/h upward, aero drag is the dominant resistive force on a sub-50 hp twin — at 150 km/h the GT is burning roughly 28 kW just pushing air. A serious cafe-racer fairing (a quarter-fairing in fibreglass, ~₹8,000) drops Cd to about 0.62 and shaves 0.10-0.15 seconds off ET. Most owners never bother because the bike is bought for the look, not the strip time.",
  },
  {
    type: "p",
    text: "2. Launch and clutch. With 52 Nm at 5,250 rpm and a healthy slipper clutch, the GT 650 has an easy launch window. Drop the clutch around 4,000 rpm and the engine pulls cleanly without bogging; bring it above 6,000 and the rear tire — on stock Pirelli Phantoms at μ_peak 1.20 — does not break traction even on warm Indian concrete. The mid-twin-500-700 cluster fix from May 2026 raised the over-clutching factor for this band, which means the simulator now lets the GT launch closer to its peak-torque rpm without snatching. The launch is not where the GT loses time; the launch is one of the things it does well.",
  },
  {
    type: "p",
    text: "3. Tire compound. The OEM Pirelli Phantom Sportscomp is a sport-touring radial, durable and well-mannered but not a true sport compound. A switch to a Pirelli Diablo Rosso II or a Michelin Pilot Power 3 in 130/70-18 lifts μ_peak from around 1.20 to 1.35, which translates to roughly 0.15-0.20 seconds of ET gain through better launch traction and tighter cornering exits at low-speed sections (less relevant for a straight strip, but a real factor on track-day quarter-mile boards). At ~₹14,000 a pair, this is a moderate-ROI mod for a bike whose main weakness is not traction.",
  },
  {
    type: "h2",
    text: "How the GT 650 Compares to Its 650-Twin Peers",
  },
  {
    type: "p",
    text: "Five mid-twin-class bikes sold in India, five different physics profiles. Numbers below are MotoQuant stock-tune sims under matched Aamby Valley November conditions:",
  },
  {
    type: "table",
    rows: [
      ["Bike", "Sim ET", "Sim trap", "Dry mass", "Peak hp", "Peak rpm"],
      [
        "RE Continental GT 650",
        "~14.1 s",
        "~158 km/h",
        "182 kg",
        "47.0",
        "7150",
      ],
      ["RE Interceptor 650", "~14.2 s", "~156 km/h", "182 kg", "47.0", "7150"],
      [
        "Kawasaki Ninja 650 (2017+)",
        "~13.0 s",
        "~178 km/h",
        "171 kg",
        "67.3",
        "8000",
      ],
      [
        "Yamaha MT-07 (2020+)",
        "~12.4 s",
        "~187 km/h",
        "164 kg",
        "72.4",
        "8750",
      ],
      [
        "Aprilia RS 660 (2021+)",
        "~11.4 s",
        "~205 km/h",
        "169 kg",
        "100.0",
        "10500",
      ],
    ],
  },
  {
    type: "p",
    text: "Two patterns stand out. First, the gap from the GT 650 to the Ninja 650 is 1.1 seconds, larger than the 20-hp gap alone would predict, because the Ninja also has 11 fewer kilograms of mass and 850 more rpm of usable headroom. Second, the gap from the GT 650 to the Aprilia RS 660 is nearly 2.7 seconds — that is a different category of bike at a different price point, and the comparison is mostly there to anchor expectations rather than to suggest the GT should compete.",
  },
  {
    type: "p",
    text: "For an Indian buyer cross-shopping the GT 650 against the Interceptor 650 or against an Indian-spec Ninja 650, the drag-strip time is one input among many. The GT is roughly ₹2.95 lakh on-road in most cities (Royal Enfield 2026 pricing), the Interceptor is around ₹2.85 lakh, and the Ninja 650 is closer to ₹7.5 lakh CKD. The GT 650 is twice as much bike as a Ninja 300 for two-thirds the price of a Ninja 650, and the drag-strip number reflects that positioning honestly.",
  },
  {
    type: "h2",
    text: "Cost-per-Tenth on the GT 650",
  },
  {
    type: "p",
    text: "The GT 650 has a respectable Indian aftermarket centred around the shared 650-twin platform — S&S Cycle full systems, K&N replacement filters, Power Commander V piggyback ECUs, and a handful of cafe-racer-specific seats, clip-ons, and tail kits. The simulator quantifies cost-per-tenth cleanly:",
  },
  {
    type: "table",
    rows: [
      ["Mod", "ET gain", "Indian price", "₹ per tenth"],
      ["K&N drop-in air filter", "~0.08 s", "~₹6,500", "~₹8,100"],
      ["15F front sprocket swap", "~0.12 s", "~₹600", "~₹500"],
      ["SuperTrapp 2-into-1 slip-on", "~0.18 s", "~₹35,000", "~₹19,400"],
      ["S&S Cycle full system", "~0.35 s", "~₹95,000", "~₹27,100"],
      ["Power Commander V flash", "~0.20 s", "~₹38,000", "~₹19,000"],
      ["Pirelli Diablo Rosso II rear", "~0.15 s", "~₹7,200", "~₹4,800"],
    ],
  },
  {
    type: "p",
    text: "The cheapest tenth on the bike is a 15-tooth front sprocket — drop one tooth, shorten every gear, accept a small top-speed reduction, and gain about 0.12 seconds for under ₹600. The sport tire and the air filter together cost ~₹13,700 and shave roughly 0.23 seconds, which is the realistic budget-tune sweet spot. Beyond that, the full-system exhaust and the ECU flash together push another half-second for ₹130,000 — a 45% increase in build cost on a ₹2.95 lakh bike for a 4% ET improvement. Most GT owners stop at sprocket-and-tire and reserve the rest of the budget for track-day fees or a quarter-fairing.",
  },
  {
    type: "callout",
    text: "Fastest cheap path on the GT 650: 15F front sprocket plus a sport-compound rear tire. That is ~₹7,800 for roughly 0.27 seconds. Skip the full system unless you also want the noise — the gain is real, but the cost-per-tenth on a sub-50 hp twin is brutal.",
  },
  {
    type: "h2",
    text: "Why the Cluster Bias Is Tighter Here Than on Smaller Bikes",
  },
  {
    type: "p",
    text: "The mid-twin-500-700 cluster sits at a mean absolute error of 0.615 seconds with a bias of -0.133 seconds across 14 matched benchmarks. The entry-200-300 cluster (Pulsar NS200, Apache RTR 200 4V, Hero Xtreme 200S 4V) sits at +0.211 seconds bias across only 6 benchmarks. The mid-twin band is more accurate because the underlying benchmark data is denser and more reliable — Sport Rider, Cycle World, and MCN all run mid-twin parallel twins regularly, the published quarter-mile times are real instrumented runs rather than 0-100 km/h numbers multiplied by 1.6, and the bikes are popular enough that multiple independent magazine tests agree to within ~0.2 seconds.",
  },
  {
    type: "p",
    text: "For the GT 650 specifically that means the simulator 14.1-second ET is probably within 0.2 seconds of what you would actually see at a real timed strip on a warmed bike with a competent rider. The honest answer for an owner who wants certainty is the same as for any bike: take the GT to a real timed strip, run a Dragy or a VBOX, and trust the timing trap over the simulator. But the simulator is a closer approximation here than it is for smaller bikes, and the relative ordering of which mods help most is reliable regardless.",
  },
  {
    type: "h2",
    text: "Run Your Own Numbers",
  },
  {
    type: "p",
    text: "If you own a Continental GT 650 (or are deciding between it and an Interceptor 650, a Ninja 650, or one of the entry 650-class twins), the simulator at motoquant.in lets you sweep rider weight, ambient temperature, density altitude, tire choice, gearing, and parts-catalog mods to see exactly where your tenths come from. Pick the GT 650 from the catalog, set the venue to Aamby Valley or your local strip, and the simulator will show stock and modded ET side-by-side with the cost-per-tenth ranking built in.",
  },
  {
    type: "p",
    text: "More relevant for everyday tuning: the parts-ROI engine ranks every catalog modification by cost-per-tenth for your specific bike. On a GT 650 the answer is loud and clear — front sprocket and sport tire first, slip-on or full system later if you also want the noise. Most owners spend money in the wrong order, which is why most modded 650 twins cost ₹1 lakh in upgrades and gain less ET than a ₹7,800 sprocket-and-tire combo would have delivered.",
  },
  {
    type: "p",
    text: "Two final caveats. First, every number in this post is a stock-tune simulation under specific conditions. Change the rider weight, the ambient temperature, the surface, or the launch technique and the absolute ETs shift, but the relative ordering of which mods help most stays stable. Second, the mid-twin-500-700 cluster bias has been actively closed over the past three months — the May 2026 clutch over-clutching rewrite cut the cluster mean absolute error from 1.07 to 0.62 seconds, and continued Dragy submissions from Indian GT 650 owners will tighten that further. The GT number you see today is the most honest the simulator has ever been on this bike, and it will only get more accurate.",
  },
  {
    type: "p",
    text: "If you take one practical thing from this post, take this: the Royal Enfield Continental GT 650 is rev-limited and gearing-limited, not power-limited at launch. A one-tooth front sprocket and a real sport tire close most of the gap to what the bike can do at the strip. The clip-on bars are for the look, the air/oil cooling is for the durability, and the strip is where the simulator stops talking and the timing trap starts.",
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
          datePublished: "2026-05-18",
        })}
      />
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {[
              "Royal Enfield",
              "Continental GT 650",
              "Indian 650cc",
              "cafe racer",
            ].map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Royal Enfield Continental GT 650 Quarter-Mile Physics
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
            18 May 2026 · 10 min read · MotoQuant Blog
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
                href="/blog/pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Pulsar NS200 vs Apache RTR 200 4V
              </Link>{" "}
              — smaller-cluster comparison post with the same cost-per-tenth
              methodology.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/hayabusa-vs-zx-14r-which-is-faster"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Hayabusa vs ZX-14R: Which Is Faster Off the Line?
              </Link>{" "}
              — top-of-stack flagship hyper-bike comparison at the other end of
              the catalog.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-the-motoquant-physics-engine-works"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How the MotoQuant Physics Engine Works
              </Link>{" "}
              — the 15-sub-model architecture behind every ET prediction in this
              post.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-to-tune-for-aamby-valley-in-november"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to Tune for Aamby Valley in November
              </Link>{" "}
              — the venue conditions used for the simulation in this post.
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
              Run the Continental GT 650 yourself
            </div>
            <div className="text-white/60 text-sm">
              Free simulator — pick the RE Continental GT 650, dial in your
              local conditions and a sport tire, and watch the ET tighten live.
            </div>
          </div>
          <Link
            href="/simulator?bike=re-continental-gt-650"
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
