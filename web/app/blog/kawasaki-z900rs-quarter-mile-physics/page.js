import Link from "next/link";
import SiteNav from "../../../components/SiteNav";
import SiteFooter from "../../../components/SiteFooter";
import StructuredData, { articleSchema } from "../../StructuredData";

const SLUG = "kawasaki-z900rs-quarter-mile-physics";
const TITLE = "Kawasaki Z900RS quarter-mile physics: retro tax on a 948cc I4";
const DESCRIPTION =
  "MotoQuant simulates the Kawasaki Z900RS at 11.18s and 196 km/h trap. MCN clocked the stock bike at 11.4s. Where the 13 hp detune costs you tenths against a Z900, and the ₹8,500 sprocket that closes most of the gap.";

export const metadata = {
  title: "Kawasaki Z900RS quarter-mile physics | MotoQuant",
  description: DESCRIPTION,
  keywords: [
    "Kawasaki Z900RS quarter mile",
    "Z900RS 0-100 India",
    "Z900RS vs Z900 drag",
    "Z900RS India price",
    "retro naked drag race India",
    "Z900RS cost per tenth",
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `https://motoquant.in/blog/${SLUG}`,
    type: "article",
    publishedTime: "2026-05-22T00:00:00Z",
  },
};

const CONTENT = [
  {
    type: "lead",
    text: "MotoQuant simulates the Kawasaki Z900RS at 11.18 seconds and a 196 km/h trap at Aamby Valley. MCN clocked the 2018 stock test bike at 11.4 seconds and 199 km/h. The simulator is 0.22 seconds quicker than the magazine. That sounds backwards for a retro neo-classic, but the retro tax does not show up where most riders expect it.",
  },
  {
    type: "h2",
    text: "What the Z900RS is",
  },
  {
    type: "p",
    text: "The Z900RS shares the Z900 chassis, the 948 cc liquid-cooled inline-four, the cassette gearbox, and the trellis frame. What changes is the engine tune. The Z900 makes 124 hp at 9,500 rpm with peak torque at 7,700 rpm; the Z900RS makes 111 hp at 8,500 rpm, with the same 98.5 Nm peak torque moved down to 6,500 rpm. The engine is the same, with revised cams, different valve timing and a heavier flywheel feel.",
  },
  {
    type: "p",
    text: "That tune is what retro buyers pay for. Riders who want low-rpm pull and a fat midrange (Z1-era ergonomics, a round headlamp, traditional tank-and-seat lines) get them on the same chassis. The cost is exactly 13 hp at the top end and roughly 1,000 rpm of usable rev range, which over a quarter mile matters less than it sounds.",
  },
  {
    type: "h2",
    text: "Stock-tune simulation numbers",
  },
  {
    type: "p",
    text: "Run in MotoQuant under Aamby Valley November conditions (density altitude ≈ 1,100 m, 22°C ambient, dry asphalt, μ_peak 1.32 on the OEM Dunlop Sportmax D214 rear), with a 78 kg rider on a 203 kg dry bike, the stock-tune Z900RS gives these numbers:",
  },
  {
    type: "table",
    rows: [
      ["Metric", "Value", "Source"],
      ["Quarter-mile ET", "11.18 s", "MotoQuant sim"],
      ["Trap speed", "196 km/h", "MotoQuant sim"],
      ["60-foot time", "~1.92 s", "MotoQuant sim"],
      ["Real-world ET (stock)", "11.4 s", "MCN 2018 instrumented"],
      ["Real-world trap", "199 km/h", "MCN 2018 instrumented"],
      ["Sim − real ΔET", "−0.22 s", "see analysis below"],
    ],
  },
  {
    type: "p",
    text: "Here the simulator runs quicker than the magazine, the opposite of the litre-naked cluster's bias on the 1390 Super Duke or the M1000R, where MotoQuant consistently runs ~0.25 s slow. The Z900RS sits in the 600–1000 cc litre cluster, which carries roughly a −0.15 s bias according to the May 2026 calibration sweep. That bias explains almost all of the gap: subtract it and the sim lands within ~0.07 s of MCN, well inside the spread between magazines for this displacement class.",
  },
  {
    type: "p",
    text: "The remaining gap of roughly 0.07 s is rider technique. MCN's run trapped at 199 km/h in the high-7,000 rpm range of 5th gear, which means the launch was conservative: the clutch slipped slightly long, the throttle feathered in gear 1, no two-step. The simulator uses an idealised but realistic launch that drops the clutch at peak-torque rpm, and on a bike with its torque peak at 6,500 rpm that is exactly where the Z900RS wants to launch. That is why this bike sims slightly quicker than measured rather than slower.",
  },
  {
    type: "callout",
    text: "The Z900RS launches well because its 6,500 rpm torque peak is the right place to drop the clutch on a 200 kg bike. Most litre nakeds peak at 8,500–10,000 rpm, so the launch rpm ends up either too high (wheelies) or too low (bogs). The simulator captures that.",
  },
  {
    type: "h2",
    text: "Where the retro tax comes from",
  },
  {
    type: "p",
    text: "Under the same Aamby Valley conditions a Z900 runs roughly 10.85 s and a 207 km/h trap in MotoQuant, about 0.33 s and 11 km/h faster than the Z900RS. That is what you pay for the round headlamp and the tank stripes. Since the engine architecture is identical, the question is where the gap comes from.",
  },
  {
    type: "p",
    text: "It comes from three places, in order of impact:",
  },
  {
    type: "p",
    text: "1. The 13 hp top-end loss accounts for ~0.15 s of the gap. On a litre naked, power matters most between 180 and 210 km/h. The Z900 keeps pulling cleanly through that band, while the Z900RS reaches its 8,500 rpm power peak and starts running into its drag wall. It is purely a top-end effect, and it shows in trap speed more than in ET.",
  },
  {
    type: "p",
    text: "2. The extra 13 kg (203 kg dry against ~190 kg for the Z900) accounts for ~0.08 s. The weight is in the steel tank, the round headlamp assembly, the chrome parts and a thicker subframe for the retro seat. The same wheel torque has to launch it, so the 60-foot time grows by roughly 0.04 s and ET follows linearly from there.",
  },
  {
    type: "p",
    text: "3. The 0.66 Cd (against roughly 0.61 for the Z900) accounts for the remaining ~0.10 s. The round headlamp, wider bars for the upright stance, a more upright tank and the lack of the Z900's small cowl all add drag. Above 160 km/h drag is the largest factor; below 100 km/h it barely matters. On the strip, where most of the time is spent between 60 and 200 km/h, it costs a little on every pass.",
  },
  {
    type: "p",
    text: "Together these make up the whole 0.33 s. None of it is gearing: the Z900RS and Z900 use identical sprockets, primary ratio and cassette ratios. Kawasaki could keep the drivetrain unchanged because the engine's torque profile allows it.",
  },
  {
    type: "h2",
    text: "What limits the Z900RS in the quarter",
  },
  {
    type: "p",
    text: "Three things, in order of impact:",
  },
  {
    type: "p",
    text: "1. Top-end power. The bike makes 111 hp and traps at 196 km/h, roughly where a stock Ducati Monster 821 or a Triumph Street Triple 765 R traps, but the Triumph carries its speed past 200 km/h and the Z900RS does not. Past 180 km/h the bike is pushing 0.50 m² of frontal area through the air on modest power. Top speed is roughly 220 km/h in 6th, and the bike spends very little time near it.",
  },
  {
    type: "p",
    text: "2. The 1,470 mm wheelbase with the upright riding position. The Z900RS seats the rider noticeably higher and further back than the Z900. That puts more weight on the rear tyre, which helps launch traction and hurts aerodynamics. In gear 1 the bike wants to wheelie at full throttle below 50 km/h: MotoQuant's wheelie sub-model shows the front wheel lifting between 30 and 50 km/h unless the throttle is feathered. MCN-style test riders do that by instinct; most owners do not.",
  },
  {
    type: "p",
    text: "3. Gearing. The 525 chain with 15F/42R sprockets gives usable but mild overall gearing. With a 1.038 ratio, 6th is a cruising gear, and the bike crosses the trap line near the top of 5th at roughly 8,400 rpm. A single-tooth change (15F/43R or 16F/42R) is the cheapest tenth on the bike, and the sums run almost exactly as on the Z900 because the two share gearing.",
  },
  {
    type: "h2",
    text: "Z900RS vs its closest rivals in India",
  },
  {
    type: "p",
    text: "MotoQuant stock-tune sims of the Z900RS and three retro and neo-retro rivals, all under the same Aamby Valley conditions:",
  },
  {
    type: "table",
    rows: [
      ["Bike", "Sim ET", "Sim trap", "Dry mass", "Peak hp", "India OTR"],
      ["Kawasaki Z900RS", "11.18 s", "196 km/h", "203 kg", "111", "~₹16.5 L"],
      [
        "Triumph Street Triple 765 R",
        "10.74 s",
        "213 km/h",
        "188 kg",
        "118",
        "~₹11 L",
      ],
      [
        "Triumph Speed Twin 1200",
        "11.45 s",
        "188 km/h",
        "216 kg",
        "99",
        "~₹13 L",
      ],
      ["Yamaha XSR900", "10.92 s", "209 km/h", "193 kg", "117", "~₹14 L (CBU)"],
    ],
  },
  {
    type: "p",
    text: "The Z900RS is the slowest of the four and, in most Indian metros, the most expensive on-road (Kawasaki India pricing puts the 2026 Z900RS at ₹16.46 lakh ex-showroom). Every Z900RS buyer should know this: you pay a premium for the styling and the riding position, in money and in straight-line performance.",
  },
  {
    type: "p",
    text: "Then again, nobody buys a Z900RS for the strip. The cassette gearbox, the smooth inline-four and its sound, and the build quality (excellent on a Kawasaki at this price) make a road bike that does most things well and costs less to live with than a Triumph over the long term. The Street Triple 765 R is 0.44 s quicker over the quarter, but it differs in everything else too: louder, a harder seat, a twitchier throttle and more aggressive ergonomics.",
  },
  {
    type: "p",
    text: "For a Z900RS owner curious about the strip, the Yamaha XSR900 is the fairer comparison. It has the same retro intent and the same fat-midrange tune, runs 0.26 s quicker, traps 13 km/h higher and costs roughly ₹2.5 lakh less as a CBU. The XSR900 is the bike the Z900RS would have been if Kawasaki had given it 117 hp instead of 111.",
  },
  {
    type: "h2",
    text: "Gearing: where the tenths are",
  },
  {
    type: "p",
    text: "Stock gearing on the Z900RS (cassette P/N 99924-1601 per Kawasaki service manual) is 15F/42R with a 525 chain and the cassette ratios [2.692, 2.058, 1.650, 1.380, 1.181, 1.038], the same as the Z900. With a 180/55ZR17 rear (rolling radius ≈ 314 mm) and the 1.038 final-drive multiplier in 6th, the bike reaches its 8,500 rpm power peak at roughly 235 km/h in 6th. That is well above the 196 km/h trap speed, so 6th gear does no useful work on the strip.",
  },
  {
    type: "p",
    text: "In the simulator log the bike crosses the trap line in 5th at roughly 8,200 rpm, slightly under peak power and well above peak torque. At the trap it is limited by power, not gearing. A 15F/43R sprocket swap (₹2,400 in parts, half an hour of labour) shortens every gear by 2.4%, which moves the trap-crossing rpm to roughly 8,400 rpm and gives a slightly quicker 60-foot. On a stock bike that is worth ~0.05 s of ET.",
  },
  {
    type: "p",
    text: "A shorter 15F/45R swap (₹2,800 in parts) cuts the ratios by 7%, closer to a drag-prep setup. The bike runs the whole quarter mile in 1st to 5th, and 6th becomes useless on the highway above about 160 km/h. On a stock bike it is worth roughly 0.08 s of ET. Either swap costs between ₹3,500 and ₹4,800 per tenth, by far the lowest cost-per-tenth on the Z900RS.",
  },
  {
    type: "h2",
    text: "The Z900RS at Indian strips",
  },
  {
    type: "p",
    text: "The Z900RS costs roughly ₹16.5 lakh on-road in India (Kawasaki India, 2026 pricing). A handful of owners run stock or near-stock bikes at Aamby Valley meets, and most of them treat it as a road bike that goes to the strip now and then, not a dedicated drag bike. In October-November conditions at Aamby Valley an experienced rider will run a stock Z900RS in 11.1–11.3 s, which matches the simulator once you allow for the launch technique discussed earlier.",
  },
  {
    type: "p",
    text: "Indian-market mods that make a difference, ranked by cost-per-tenth:",
  },
  {
    type: "table",
    rows: [
      ["Mod", "Cost (₹)", "ET gain", "₹/tenth"],
      ["15F/45R sprocket swap", "2,800", "0.08 s", "~3,500"],
      ["DNA air filter", "5,700", "0.04 s", "~14,200"],
      ["Akrapovic slip-on", "52,000", "0.10 s", "~52,000"],
      ["Powertronic ECU flash", "24,500", "0.08 s", "~30,600"],
      ["Akrapovic full system + flash", "1,82,000", "0.22 s", "~83,000"],
    ],
  },
  {
    type: "p",
    text: "The sprocket swap is by far the cheapest tenth, and the cost climbs quickly after it. The Akrapovic full system costs the most, but it is also the only way to a sub-11 s Z900RS on stock displacement. It eats a budget, and it makes sense only if you will run the bike on the strip regularly. If you run maybe six quarter-mile passes a year, fit the sprocket and an air filter and stop there.",
  },
  {
    type: "callout",
    text: "The cheapest fast path on the Z900RS is the sprocket first (₹2,800, 0.08 s), then the air filter (₹5,700, 0.04 s): ₹8,500 and 0.12 s of ET in total. Skip the exhaust unless you are also doing a flash. A slip-on without ECU work gives the engine extra airflow it cannot use, so you pay for the noise without the tenths.",
  },
  {
    type: "h2",
    text: "Run your own numbers",
  },
  {
    type: "p",
    text: "If you own a Z900RS, or are choosing between it and a Street Triple 765 R, the simulator at motoquant.in lets you sweep rider weight, ambient temperature, density altitude and parts-catalog mods to see where your tenths come from. The cluster-bias correction discussed above is built into the model: when the simulator says your bike runs 11.18 s, expect the strip to give somewhere between 11.1 and 11.4 s, depending on technique, traffic and surface prep.",
  },
  {
    type: "p",
    text: "For everyday tuning, the simulator also shows which mods are dead weight. Spending ₹52,000 on a slip-on to gain 0.10 s is a very different deal from spending ₹2,800 on a sprocket pair to gain 0.08 s. MotoQuant's parts ROI engine shows this for each part on each bike, and on a Z900RS gearing is clearly the answer if you want faster passes more than the Akrapovic burble at idle.",
  },
  {
    type: "p",
    text: "Two caveats. First, every number in this post is a stock-tune simulation under specific conditions. Change the rider weight, ambient temperature, surface or launch technique and the absolute ETs shift, but the order of which mods help most stays the same, and that order is why you run the simulator before spending money. Second, the litre-naked cluster carries a small negative bias (~0.15 s) for retro and upright bikes, because real riders sit up and catch more air than the model assumes. Plan for the strip to be 0.1–0.2 s slower than the simulator until you have done a few timed passes and learned the bike.",
  },
  {
    type: "p",
    text: "The Z900RS rewards a careful, low-rpm launch and punishes anyone who rides it like a sport bike. Use the 6,500 rpm torque peak off the line and the 8,500 rpm power peak between 160 and 200 km/h. Match your shift points to those numbers and swap the rear sprocket for ₹2,800.",
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
          datePublished: "2026-05-22",
        })}
      />
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {["Kawasaki", "Z900RS", "retro naked", "physics"].map((t) => (
              <span
                key={t}
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Kawasaki Z900RS quarter-mile physics: retro tax on a 948cc I4
          </h1>
          <div className="text-sm text-white/60 mb-12">
            22 May 2026 · 10 min read · MotoQuant Blog
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
                href="/blog/yamaha-xsr900-gp-vs-mt-09-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Yamaha XSR900 GP vs MT-09: where the heritage tax is paid
              </Link>
              : the same retro-vs-naked physics question on the Yamaha triple.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/yezdi-roadster-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Yezdi Roadster 334 quarter-mile physics
              </Link>
              : neo-retro at the other end of the price ladder.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/the-physics-of-a-perfect-launch"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                The physics of a perfect launch
              </Link>
              : why the Z900RS's 6,500 rpm torque peak makes the launch easier
              than most litre nakeds.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-to-tune-for-aamby-valley-in-november"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to tune for Aamby Valley in November
              </Link>
              : the venue conditions used for the simulation in this post.
            </li>
            <li>
              ·{" "}
              <Link
                href="/bikes"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Browse the bike catalog
              </Link>
              : the specs, gear ratios and Cd values the simulator uses.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">
              Run the Z900RS yourself
            </div>
            <div className="text-white/60 text-sm">
              The simulator is free. Pick the Kawasaki Z900RS, set your local
              conditions, and watch the ET change as you swap sprockets and air
              filters.
            </div>
          </div>
          <Link
            href="/simulator?bike=kawasaki-z900rs"
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
