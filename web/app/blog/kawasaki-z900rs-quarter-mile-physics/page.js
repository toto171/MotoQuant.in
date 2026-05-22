import Link from "next/link";
import SiteNav from "../../../components/SiteNav";
import SiteFooter from "../../../components/SiteFooter";
import StructuredData, { articleSchema } from "../../StructuredData";

const SLUG = "kawasaki-z900rs-quarter-mile-physics";
const TITLE = "Kawasaki Z900RS Quarter-Mile Physics: Retro Tax on a 948cc I4";
const DESCRIPTION =
  "MotoQuant simulates the Kawasaki Z900RS at 11.18s and 196 km/h trap. MCN clocked the stock bike at 11.4s. Where the 13 hp detune actually costs you tenths versus a Z900, and the ₹8,500 sprocket that closes most of the gap.";

export const metadata = {
  title: "Kawasaki Z900RS Quarter-Mile Physics — MotoQuant",
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
    text: "MotoQuant simulates the Kawasaki Z900RS at 11.18 seconds and a 196 km/h trap at Aamby Valley. MCN clocked the 2018 stock test bike at 11.4 seconds and 199 km/h. The simulator is 0.22 seconds faster than the magazine, which sounds backwards for a retro neo-classic — until you look at where the retro tax actually shows up, which is not where most riders expect.",
  },
  {
    type: "h2",
    text: "What the Z900RS Actually Is",
  },
  {
    type: "p",
    text: "The Z900RS shares the Z900 chassis, the 948 cc liquid-cooled inline-four, the cassette gearbox, and the trellis frame. What changes is the engine tune. Where the Z900 makes 124 hp at 9,500 rpm with peak torque at 7,700 rpm, the Z900RS makes 111 hp at 8,500 rpm with the same 98.5 Nm peak torque dropped down to 6,500 rpm. Same engine, revised cams, different valve timing, a heavier flywheel feel — Kawasaki rebuilt the character without changing the architecture.",
  },
  {
    type: "p",
    text: "That tuning shift is what the retro segment buys. Riders who want a low-rpm pull and a fat midrange — Z1-era ergonomics, a round headlamp, traditional tank-and-seat lines — get them without sacrificing the chassis underneath. The penalty for that compromise is exactly 13 hp at the top end and roughly 1,000 rpm of usable rev range. In quarter-mile terms, that penalty is smaller than it sounds.",
  },
  {
    type: "h2",
    text: "Stock-Tune Simulation Numbers",
  },
  {
    type: "p",
    text: "Running the Z900RS in MotoQuant under Aamby Valley November conditions (density altitude ≈ 1,100 m, 22°C ambient, dry concrete, μ_peak 1.32 on the OEM Dunlop Sportmax D214 rear), with a 78 kg rider on a 203 kg dry bike, produces the following stock-tune numbers:",
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
    text: "The simulator running quicker than the magazine here is the opposite of the bias the litre-naked cluster shows on the 1390 Super Duke or the M1000R, where MotoQuant systematically runs ~0.25 s slow. The Z900RS sits inside the 600–1000 cc litre cluster which carries roughly a −0.15 s bias as documented in the May 2026 calibration sweep. That bias does almost all the work here: subtract it and the sim lines up to within ~0.07 s of MCN, which is well inside the magazine-to-magazine variance for this displacement class.",
  },
  {
    type: "p",
    text: "The remaining gap of roughly 0.07 s is rider technique. MCN ran the bike to 199 km/h trap in the high-7,000 rpm range of 5th gear, which means the launch transient was conservative — slipping the clutch slightly long, feathering the throttle into gear 1, no two-stepping. The simulator runs an idealised but realistic launch with peak-torque rpm at the dump point, which on a 6,500 rpm-torque-peak bike happens to be exactly where the Z900RS wants to be launched. That alignment is why this specific bike sims slightly quicker than measured rather than slower.",
  },
  {
    type: "callout",
    text: "Why the Z900RS launches well: peak torque at 6,500 rpm sits in the sweet spot for clutch dumping on a 200 kg bike. Most litre nakeds peak torque at 8,500–10,000 rpm, which means the launch RPM is either too high (wheelies) or too low (bogs). The Z900RS just happens to land on a sweet spot, and the simulator captures that exactly.",
  },
  {
    type: "h2",
    text: "Where the Retro Tax Actually Lives",
  },
  {
    type: "p",
    text: "A Z900 in MotoQuant under the same Aamby Valley conditions runs roughly 10.85 s and 207 km/h trap — about 0.33 s and 11 km/h faster than the Z900RS. That spread is what you pay for the round headlamp and the tank stripes. The interesting question is where the spread comes from, since the engine architecture is identical.",
  },
  {
    type: "p",
    text: "Three contributors, in order of impact:",
  },
  {
    type: "p",
    text: "1. The 13 hp top-end loss accounts for ~0.15 s of the gap. Power is most useful between 180 and 210 km/h on a litre naked — the Z900 keeps pulling cleanly through that band where the Z900RS hits its 8,500 rpm power peak and starts running into its drag wall. This is purely a top-end effect and shows up in trap speed more than ET.",
  },
  {
    type: "p",
    text: "2. The 13 kg mass increase (203 kg dry vs ~190 kg for the Z900) accounts for ~0.08 s. The Z900RS carries more material in the steel tank, the round-headlamp assembly, the chrome bits, and a thicker subframe to support the retro seat. That mass is launched at the same wheel torque, so 60-foot time increases by roughly 0.04 s and ET tracks linearly from there.",
  },
  {
    type: "p",
    text: "3. The 0.66 Cd value (vs the Z900 at roughly 0.61) accounts for the remaining ~0.10 s. Round headlamp, wider bars for the upright stance, a more upright tank profile, and the absence of the Z900's slight cowl all add drag. Above 160 km/h this is the dominant factor; below 100 km/h it barely matters. On the strip, where most of the time is spent between 60 and 200 km/h, the drag penalty is a quiet but consistent tax.",
  },
  {
    type: "p",
    text: "Add them up and the 0.33 s spread is fully accounted for. None of it is gearing — the Z900RS and Z900 use identical sprockets, primary ratio, and overall gear cassette ratios. Kawasaki kept the drivetrain unchanged precisely because the engine torque profile lets it.",
  },
  {
    type: "h2",
    text: "What Actually Limits the Z900RS in the Quarter",
  },
  {
    type: "p",
    text: "Three things, in order of impact:",
  },
  {
    type: "p",
    text: "1. Top-end power. The bike makes 111 hp and traps at 196 km/h — for context, that is roughly the trap speed a stock Ducati Monster 821 or a Triumph Street Triple 765 R lands at, but the Triumph carries the speed past 200 km/h and the Z900RS does not. Past 180 km/h the bike is asking the chassis to push 0.50 m² of frontal area through air at sub-luxury power output. Top speed is roughly 220 km/h in 6th and the bike spends very little time near it.",
  },
  {
    type: "p",
    text: "2. The 1,470 mm wheelbase combined with the upright rider position. The Z900RS sits the rider noticeably higher and further back than the Z900, which pushes more weight onto the rear tire — friendly for launch traction but unfriendly for aerodynamics. In gear 1 the bike wants to wheelie at full throttle below 50 km/h. The wheelie sub-model in MotoQuant flags the front wheel lifting between 30 and 50 km/h unless throttle is feathered, which is what every MCN-style test rider does instinctively but most owners do not.",
  },
  {
    type: "p",
    text: "3. The 525 chain with 15F/42R sprockets gives the bike a usable but unaggressive overall gearing. The 1.038 ratio in 6th means top gear is essentially a cruise gear, not a drag-strip gear — the bike crosses the trap line near the top of 5th at roughly 8,400 rpm. A single-tooth swap on the rear (15F/43R or 16F/42R) is the cheapest tenth on the bike, and the math runs almost identically to the Z900 because they share gearing.",
  },
  {
    type: "h2",
    text: "Z900RS vs Its Closest Rivals in India",
  },
  {
    type: "p",
    text: "Three retro and neo-retro nakeds, three different physics profiles. Numbers below are MotoQuant stock-tune sims under matched Aamby Valley conditions:",
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
    text: "The Z900RS is the slowest of the four, and it is also the most expensive on-road in most Indian metros (Kawasaki India pricing puts the 2026 Z900RS at ₹16.46 lakh ex-showroom). That is the headline tension every prospective Z900RS buyer should know about: you are paying a premium for the styling and the riding position, and you are paying it in straight-line performance.",
  },
  {
    type: "p",
    text: "The honest counter-argument is that the Z900RS is not bought for the strip. The cassette gearbox, the four-cylinder smoothness, the inline-four sound, and the build quality (which is, on a Kawasaki at this price, genuinely excellent) buy a real-world bike that does most things well and costs less to live with than a Triumph long-term. The Street Triple 765 R is 0.44 s quicker over the quarter, but it is also a different bike in every other dimension — louder, harder seat, twitchier throttle, more aggressive ergonomics.",
  },
  {
    type: "p",
    text: "For the strip-curious Z900RS owner, the Yamaha XSR900 is the more honest comparison. Same retro intent, same midrange-fat tune, 0.26 s quicker, traps 13 km/h higher, costs roughly ₹2.5 lakh less as a CBU. The XSR900 is the bike the Z900RS would have been if Kawasaki had given it 117 hp instead of 111.",
  },
  {
    type: "h2",
    text: "Gearing — Where the Tenths Actually Live",
  },
  {
    type: "p",
    text: "Stock gearing on the Z900RS (cassette P/N 99924-1601 per Kawasaki service manual) is 15F/42R with a 525 chain and the cassette ratios [2.692, 2.058, 1.650, 1.380, 1.181, 1.038] — verbatim from the Z900. With a 180/55ZR17 rear (rolling radius ≈ 314 mm) and the 1.038 final-drive multiplier in 6th, the bike hits its 8,500 rpm power peak at roughly 235 km/h in 6th. That is well above the 196 km/h trap speed, which means 6th gear is doing no useful work on the strip.",
  },
  {
    type: "p",
    text: "The simulator log shows the bike crossing the trap line in 5th at roughly 8,200 rpm — slightly under peak power, well above peak torque. The bike is power-limited at the trap, not gearing-limited. A 15F/43R sprocket swap (₹2,400 in parts, half an hour of labour) shortens the cassette by 2.4% across the board, which shifts the trap-crossing rpm to roughly 8,400 rpm and gives the bike a slightly quicker 60-foot. Net ET impact: ~0.05 s on a stock bike.",
  },
  {
    type: "p",
    text: "A more aggressive 15F/45R swap (₹2,800 in parts) shortens the ratios by 7% — closer to a drag-prep setup. The bike spends its quarter mile entirely in 1st through 5th, with 6th becoming useless on the highway above about 160 km/h. ET impact: roughly 0.08 s on a stock bike. The cost-per-tenth on either swap is between ₹3,500 and ₹4,800, which is the lowest cost-per-tenth available on the Z900RS by a wide margin.",
  },
  {
    type: "h2",
    text: "The Indian Drag-Strip Reality",
  },
  {
    type: "p",
    text: "The Z900RS arrives in India at roughly ₹16.5 lakh on-road (Kawasaki India, 2026 pricing). Aamby Valley meets see a handful of Z900RS owners running stock or near-stock — most of them treat the bike as a cruise-and-occasional-strip machine rather than a dedicated drag tool. A stock Z900RS at Aamby Valley in October-November conditions will run 11.1–11.3 s in the hands of an experienced rider, which lines up with the simulator output once you account for the launch technique discussed earlier.",
  },
  {
    type: "p",
    text: "Indian-market mods that move the needle, ranked by cost-per-tenth:",
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
    text: "Notice the cost-per-tenth ladder. The sprocket swap is by far the cheapest tenth, and after that the ladder rises quickly. The Akrapovic full system is at the top of the cost ladder but is also the only path to a sub-11 s Z900RS on stock displacement — it is a budget-killer of a mod, justified only if you are committed to running the bike on the strip regularly. For an enthusiast who runs maybe six quarter-mile passes a year, the right answer is the sprocket swap plus an air filter, full stop.",
  },
  {
    type: "callout",
    text: "Fastest cheap path on the Z900RS: sprocket first (₹2,800, 0.08 s), then air filter (₹5,700, 0.04 s). Total ₹8,500 and 0.12 s ET. Skip the exhaust unless you are also doing a flash — slip-ons without ECU work give the engine extra airflow it cannot use, and you pay for the noise without the tenths.",
  },
  {
    type: "h2",
    text: "Run Your Own Numbers",
  },
  {
    type: "p",
    text: "If you own a Z900RS or are deciding between a Z900RS and a Street Triple 765 R, the simulator at motoquant.in lets you sweep rider weight, ambient temperature, density altitude, and parts-catalog mods to see exactly where your tenths come from. The cluster-bias correction discussed above is baked into the model — when the simulator says your bike runs 11.18 s, expect the strip to confirm somewhere between 11.1 and 11.4 s depending on technique, traffic, and surface prep.",
  },
  {
    type: "p",
    text: "More relevant for everyday tuning: the simulator shows you which mods are dead weight. Spending ₹52,000 on a slip-on to gain 0.10 s is a different value calculation than spending ₹2,800 on a sprocket pair to gain 0.08 s. MotoQuant's parts ROI engine spells that out per part per bike — and on a Z900RS, the gearing answer is overwhelmingly the right answer for anyone whose primary goal is faster passes rather than the Akrapovic burble at idle.",
  },
  {
    type: "p",
    text: "Two caveats worth stating plainly. First, every number in this post is a stock-tune simulation under specific conditions. Change the rider weight, the ambient temperature, the surface, or the launch technique and the absolute ETs shift. The relative ordering of which mods help most stays stable across those changes, which is the whole point of running the simulator before spending money. Second, the litre-naked cluster carries a small negative bias (~0.15 s) for retro and upright bikes specifically because real-world riders sit up and catch more air than the model assumes. Plan for the strip to be 0.1–0.2 s slower than the simulator output until you have done a few timed passes and learned the bike.",
  },
  {
    type: "p",
    text: "If you take one practical thing from this post, take this: the Z900RS is a bike that rewards a careful, low-revving launch and punishes anyone trying to ride it like a sport bike. The 6,500 rpm torque peak is your friend off the line, but the 8,500 rpm power peak is your only ally between 160 and 200 km/h. Match your shift points to those numbers, swap the rear sprocket for ₹2,800, and the bike runs as hard as Kawasaki ever intended it to.",
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
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Kawasaki Z900RS Quarter-Mile Physics: Retro Tax on a 948cc I4
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
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
                Yamaha XSR900 GP vs MT-09: Where the Heritage Tax Is Paid
              </Link>{" "}
              — the same retro-vs-naked physics question on the Yamaha triple.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/yezdi-roadster-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Yezdi Roadster 334 Quarter-Mile Physics
              </Link>{" "}
              — neo-retro at the other end of the price ladder.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/the-physics-of-a-perfect-launch"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                The Physics of a Perfect Launch
              </Link>{" "}
              — why the Z900RS's 6,500 rpm torque peak makes the launch easier
              than most litre nakeds.
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
              Run the Z900RS yourself
            </div>
            <div className="text-white/60 text-sm">
              Free simulator — pick the Kawasaki Z900RS, dial in your local
              conditions, and watch the ET update live as you toggle sprockets
              and air filters.
            </div>
          </div>
          <Link
            href="/simulator?bike=kawasaki-z900rs"
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
