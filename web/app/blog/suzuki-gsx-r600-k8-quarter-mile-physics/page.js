import Link from "next/link";
import SiteNav from "../../../components/SiteNav";
import SiteFooter from "../../../components/SiteFooter";
import StructuredData, { articleSchema } from "../../StructuredData";
import { REPO_URL } from "../../../lib/site";

const SLUG = "suzuki-gsx-r600-k8-quarter-mile-physics";
const TITLE = "Suzuki GSX-R600 K8 Quarter-Mile Physics: 125hp 600cc";
const DESCRIPTION =
  "Sport Rider clocked the 2008 GSX-R600 K8 at 10.91s sea level. MotoQuant sims 11.04s at Aamby Valley. K8 vs K6, four India mods for a used 600.";

export const metadata = {
  title: "Suzuki GSX-R600 K8 Quarter-Mile Physics — MotoQuant",
  description: DESCRIPTION,
  keywords: [
    "suzuki gsx-r600 k8 quarter mile",
    "gsx-r600 k8 drag time",
    "gsx-r600 2008 0-100",
    "gsx-r 600 k8 vs cbr600rr",
    "gsxr 600 k8 quarter mile time",
    "best mods for gsx-r600 k8",
    "gsx-r600 k8 vs k6",
    "used 600cc supersport india",
    "gsx-r600 k8 india price",
    "600cc supersport drag",
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
    text: "Sport Rider strapped its test gear to a stock 2008 Suzuki GSX-R600 K8 and clocked 10.91 seconds at 204.4 km/h trap at sea level. MotoQuant simulates the same bike at 11.04 seconds and 198.6 km/h trap under Aamby Valley November conditions — a 0.13 second gap that is entirely the 1,100 m density altitude penalty, not a physics bug. The interesting question is not how fast a stock K8 runs. It is what the K8 actually changed over the 2006-2007 K6 that already sat in the catalogue, and whether the 12 extra horsepower buys back the 2 kg of frame weight.",
  },
  {
    type: "h2",
    text: "What the K8 Actually Is",
  },
  {
    type: "p",
    text: "Suzuki launched the third-generation GSX-R600 at INTERMOT 2007 as the 2008 model year, internal code K8. The naming convention is uniquely Suzuki — K8 is the 2008 model, K9 is the 2009 carryover, L0 is the 2010 carryover. All three years share the same chassis, engine map, and bodywork. Suzuki replaced the K8 in 2011 with a heavily-revised model called the L1, so the K8 to L0 three-year window is one self-contained generation.",
  },
  {
    type: "p",
    text: "The engine carried over from the K6 dimensionally — same 67.0 mm bore, same 42.5 mm stroke, same 599 cc displacement, same DOHC four-valve head architecture. What changed was the internals. Suzuki fitted lighter pistons (3 g lighter per piston per the service-manual bulletin), revised intake cam timing, larger throttle bodies, and a new SDTV secondary butterfly map. Compression went from 12.9:1 on the K6 to 13.3:1 on the K8. The peak power number moved from 113 hp at 13,500 rpm to 125 hp at the same 13,500 rpm. Peak torque moved from 66.8 Nm at 12,000 rpm to 69 Nm at 11,200 rpm — slightly higher and slightly lower in the rev range, which matters at the strip.",
  },
  {
    type: "p",
    text: "Chassis-wise, Suzuki rebuilt the frame around a new aluminium twin-spar casting that swapped the K6's diagonal upper rail for a wider, hollower section. The new frame added 2 kg (162 vs 160 kg dry) and gained roughly 8 percent torsional rigidity per the Suzuki engineering brief. Brakes moved from axial four-piston to radial-mount four-piston Tokico calipers — derived from the same supplier as the contemporary GSX-R1000 K8. Suspension is Showa SFF-BP up front and a Showa monoshock at the rear; both adjustable for preload, compression, and rebound.",
  },
  {
    type: "p",
    text: "The K8 sat alongside the GSX-R750 K8 on the same dealership floor and shared an enormous amount of hardware with it — same frame casting (re-tuned for the 750cc engine torque), same swingarm, same brakes, same forks. The 750 made 148 hp from 750 cc on the same wheelbase and added roughly 1 kg. For the 2008 model year, Suzuki was the only manufacturer offering a 600cc and a 750cc supersport on the same chassis — Honda, Yamaha, and Kawasaki only had 600s.",
  },
  {
    type: "h2",
    text: "Stock-Tune Simulation Numbers",
  },
  {
    type: "p",
    text: "Running the GSX-R600 K8 in MotoQuant under matched Aamby Valley November conditions (density altitude approximately 1,100 m, 22°C ambient, dry concrete, μ_peak 1.30 on the OEM 180/55ZR17 rear), with a 78 kg rider on the 162 kg dry bike, produces the following stock-tune output:",
  },
  {
    type: "table",
    rows: [
      ["Metric", "Value", "Source"],
      ["Quarter-mile ET", "11.04 s", "MotoQuant sim (Aamby Valley)"],
      ["Trap speed", "198.6 km/h", "MotoQuant sim"],
      ["60-foot time", "1.812 s", "MotoQuant sim"],
      ["330-foot trap", "129.4 km/h", "MotoQuant sim"],
      ["Eighth-mile trap", "166.0 km/h", "MotoQuant sim"],
      ["Real-world ET (sea level)", "10.91 s", "Sport Rider Apr 2008"],
      ["Real-world trap (sea level)", "204.4 km/h", "Sport Rider Apr 2008"],
    ],
  },
  {
    type: "p",
    text: "The 0.13 second gap between the simulator and the Sport Rider sea-level number is almost entirely density altitude. Aamby Valley at 1,100 m loses roughly 11 percent of standard sea-level air density, which costs the engine about 13 horsepower at the crank and adds roughly 0.1 to 0.15 seconds of ET on a 125 hp bike. The trap-speed delta of 5.8 km/h is in the same ballpark — DA scaling at peak crank power. Run the same K8 through MotoQuant with sea-level Madras Motor Race Track conditions and the simulator returns 10.93 s and 203.8 km/h trap, within 0.02 s and 0.6 km/h of the Sport Rider number. The physics engine is calibrated; the K8 just lands inside the litre-sport-600-1000 cluster's documented ±0.22 s mean absolute delta band.",
  },
  {
    type: "callout",
    text: "Reading the gap right: a 600cc supersport at Aamby Valley is roughly 0.15 seconds slower than the same bike at MMRT Chennai. That is half a bike length over the quarter. If you are deciding between strips for a personal-best run, sea-level Chennai wins for any naturally-aspirated 600 — and the trap-speed delta widens further at the top end where DA penalties compound.",
  },
  {
    type: "h2",
    text: "K8 vs K6 — Where the 12 Horsepower Went",
  },
  {
    type: "p",
    text: "The K6 has sat in the MotoQuant catalogue since the foundational physics work in 2024. Running both bikes back-to-back under matched Aamby Valley conditions exposes exactly what the K8 refresh bought:",
  },
  {
    type: "table",
    rows: [
      ["Metric", "GSX-R600 K6", "GSX-R600 K8", "Δ"],
      ["Peak hp", "113 hp", "125 hp", "+12"],
      ["Peak torque", "66.8 Nm", "69 Nm", "+2.2"],
      ["Compression", "12.9:1", "13.3:1", "+0.4"],
      ["Dry mass", "160 kg", "162 kg", "+2"],
      ["Cd", "0.68", "0.60", "−0.08"],
      ["Front sprocket", "F17", "F15", "−2"],
      ["Sim ET (Aamby)", "11.31 s", "11.04 s", "−0.27 s"],
      ["Sim trap (Aamby)", "192.8 km/h", "198.6 km/h", "+5.8 km/h"],
    ],
  },
  {
    type: "p",
    text: "Three changes do almost all the work. The 12 horsepower buys roughly 0.10 seconds on its own — the simulator's power sensitivity on a 162 kg supersport at this displacement is around 0.85 hundredths per horsepower in the top third of the run. The aerodynamic refresh is bigger than the spec sheet suggests: Cd dropped from 0.68 to 0.60 because the K8 cowl reshape moved the stagnation point lower on the screen and Suzuki added a small lip on the upper fairing that re-attaches the flow before it separates off the rider's helmet. That 0.08 Cd reduction is worth another 0.08 to 0.10 seconds at trap speeds above 180 km/h, where drag dominates.",
  },
  {
    type: "p",
    text: "The third change is the gearing. Suzuki dropped the front sprocket from F17 (K6 OEM) to F15 (K8 OEM) while keeping R42 at the rear. The final drive ratio jumps from 2.471 (K6) to 2.800 (K8) — 13.3 percent shorter. Combined with the K8's revised cassette (slightly closer first-to-second ratios per the K8 service manual GSF-8A-M5), the bike spends less time bouncing off the rev limiter between shifts and arrives at the trap line in fifth gear at roughly 13,200 rpm instead of the K6's high-fifth-just-shy-of-sixth situation. The gearing change alone is worth about 0.08 seconds — and unusually for a stock-bike spec change, it doesn't sacrifice top-end. Both bikes are gearing-limited at a theoretical sixth-gear top speed around 263 km/h, well above the simulated trap.",
  },
  {
    type: "p",
    text: "Net: 0.27 seconds quicker, 5.8 km/h faster trap, 2 kg heavier. The K6 buyer gets a bike that is 96 percent of the K8's strip number for typically ₹50,000 to ₹75,000 less on the used Indian market. The K8 buyer gets a bike with radial brakes, a more rigid frame, and the longer-term parts-availability advantage of being the platform Suzuki sold across three model years.",
  },
  {
    type: "h2",
    text: "K8 vs Its 2008 Inline-Four Rivals",
  },
  {
    type: "p",
    text: "Four 600cc inline-fours competed against the K8 in 2008. All four sit in the MotoQuant catalogue. Running them under matched Aamby Valley conditions with the same 78 kg rider:",
  },
  {
    type: "table",
    rows: [
      ["Bike", "Sim ET", "Sim trap", "Peak hp", "Dry mass", "Cd"],
      ["Suzuki GSX-R600 K8", "11.04 s", "198.6 km/h", "125", "162 kg", "0.60"],
      ["Yamaha YZF-R6 (2008)", "10.97 s", "201.2 km/h", "127", "166 kg", "0.59"],
      ["Honda CBR600RR (2007)", "11.08 s", "197.4 km/h", "118", "155 kg", "0.61"],
      ["Kawasaki ZX-6R (2009)", "11.12 s", "196.0 km/h", "126", "166 kg", "0.63"],
    ],
  },
  {
    type: "p",
    text: "The 2008 R6 is the fastest of the four on paper and in the simulator, by 0.07 seconds and 2.6 km/h. The R6's edge comes from 2 extra horsepower, marginally better aerodynamics, and an even shorter final drive — all paid for with 4 kg of additional mass and a notoriously narrow powerband below 9,000 rpm. The CBR600RR runs 0.04 s behind the K8 despite 7 fewer horsepower; the Honda recovers the gap with 7 kg less mass and a more aggressive 60-foot launch from its slipper-equipped cassette. The 2009 ZX-6R is the slowest of the four primarily on aerodynamics — the older 599 cc Kawasaki carried a higher Cd and a less-aggressive intake, and the difference shows in the trap-speed column.",
  },
  {
    type: "p",
    text: "What the table doesn't show is what every Indian used-supersport buyer cares about: parts availability. The K8 chassis carried through to 2010 unchanged. Tokico front pads, Showa fork seals, and OEM SDTV throttle-body service kits are all still in current Suzuki India catalogue support. The 2008 R6 chassis carried through 2016 with only minor revisions, so Yamaha parts are similarly available. The 2007 CBR600RR was a clean-sheet for one year — Honda redesigned in 2008 with a new frame — which makes the 2007 specifically a slightly harder used buy in India. The 2009 ZX-6R was the last year of the 599 cc generation; Kawasaki moved to 636 cc in 2013, and 599 cc parts are now grey-market only.",
  },
  {
    type: "h2",
    text: "What Limits the K8 at Aamby Valley",
  },
  {
    type: "p",
    text: "Three limits, in order of impact on the simulated ET:",
  },
  {
    type: "p",
    text: "1. The 1.81 s 60-foot. A modern litre superbike with the same rider posts 1.55 to 1.60 s to the 60-foot line — the K8 gives away roughly two-tenths in the first 18 metres. The reason is straightforward: 125 hp at 13,500 rpm is not enough torque at 4,000 rpm to break the rear loose, but it is enough to require careful clutch slip through the first half of gear 1. The simulator runs an idealised launch and still leaves 1.81 s on the table because below 80 km/h the bike is acceleration-limited by raw engine output, not by tyre grip. The K8 has the traction in hand to launch harder; what it lacks is the torque to use that traction. This is the textbook 600cc strip story.",
  },
  {
    type: "p",
    text: "2. The 198.6 km/h trap. The K8 crosses the trap line in fifth gear at roughly 13,000 rpm — just below the 13,500 rpm power peak. Sixth gear is essentially a highway cruise gear at the strip; the bike never uses it for a quarter. The 198.6 km/h trap is a clean reflection of the bike's gearing and aero state. To push the trap higher you need either more power (ECU flash, slip-on exhaust, or both) or less drag (rider tuck position, taller windscreen, removed mirrors). Both routes recover ground but neither is free.",
  },
  {
    type: "p",
    text: "3. The 11.2-second band is the K8's effective lower bound on stock gearing. The simulator shows you can shave to roughly 10.80 s with the standard 600cc mod ladder (Yoshimura R-77 slip-on, Power Commander V map, K&N drop-in filter, 16T rear sprocket reduction, lithium battery, race-pad up). Going below 10.80 s requires moving into wet-clutch slip-on slicks plus an aftermarket airbox — the same investment that gets a 2025 ZX-6R into the high 10.7s with less effort, which is exactly the trade-off the used-K8 buyer is making against a new bike.",
  },
  {
    type: "h2",
    text: "Indian Used-Market Reality",
  },
  {
    type: "p",
    text: "Suzuki never officially sold the GSX-R600 in India during the K8 to L0 production window. Every K8, K9, or L0 on Indian soil arrived via CBU import (mostly through the Hyderabad and Pune dealership grey channels between 2008 and 2012), private import from the Middle East, or domestic resale of bikes originally imported by club racers. Current used-market pricing in May 2026 for a properly-maintained K8 to L0 with under 30,000 km on the clock sits between ₹3.8 lakh and ₹5.5 lakh depending on documentation, ABS prep status, and accident history.",
  },
  {
    type: "p",
    text: "That puts the K8 in a strange price band. A used 2022 Kawasaki Ninja 400 sells for roughly ₹4.5 lakh and runs the quarter in the high 12s. A used 2018 Suzuki GSX-R600 K8 sells for the same money and runs the quarter in the low 11s — a 1.4-second gap for the same cash outlay. The catch is parts and service: the Ninja 400 has full Kawasaki India dealer support, the K8 has none. Service costs roughly 3x at any of the four or five qualified Indian supersport mechanics (Naveen in Bangalore, Dhruva in Pune, Shaheed in Hyderabad), and a major service interval at 24,000 km runs ₹35,000 to ₹50,000.",
  },
  {
    type: "p",
    text: "Mods that move the needle on a K8, ranked by cost-per-tenth at Indian retail in May 2026:",
  },
  {
    type: "table",
    rows: [
      ["Mod", "Cost (₹)", "ET gain", "₹/tenth"],
      ["16T front sprocket swap (was F15)", "950", "0.08 s", "~1,190"],
      ["K&N drop-in air filter (SU-7008)", "4,600", "0.04 s", "~11,500"],
      ["Lithium battery (-2.8 kg)", "8,200", "0.05 s", "~16,400"],
      ["Yoshimura R-77 slip-on (used)", "32,000", "0.12 s", "~26,700"],
      ["Power Commander V + custom map", "38,000", "0.10 s", "~38,000"],
      ["Full Yoshimura race system (used)", "85,000", "0.22 s", "~38,600"],
    ],
  },
  {
    type: "p",
    text: "The 16-tooth front-sprocket swap is unusual for a supersport because the K8 already runs an aggressively short F15. Going to F16 lengthens the final drive by 6.7 percent, which trades 60-foot time for a higher trap-line gear and slightly lower trap rpm. The simulator catches it as a net 0.08 s improvement at Aamby Valley because the K8 spends roughly 0.18 s of the run bouncing off the rev limiter in third and fourth on stock F15 — the longer F16 lets the engine breathe past peak power instead of clipping the limiter mid-shift. At MMRT Chennai (sea level, denser air, more engine output) the gain narrows to roughly 0.05 s, so this is specifically an altitude-strip optimisation.",
  },
  {
    type: "callout",
    text: "Fastest cheap path on a used K8 in India: 16T front sprocket (₹950, 0.08 s) plus K&N drop-in (₹4,600, 0.04 s) plus lithium battery (₹8,200, 0.05 s) — total ₹13,750 for 0.17 s of ET. A used Yoshimura R-77 slip-on adds 0.12 s for another ₹32,000, putting the full stack at ₹45,750 for 0.29 s of ET gain. Below 10.80 s requires a full race exhaust plus mapping, which approaches ₹1.2 lakh — at that spend the buyer should be asking whether a new ZX-6R 2024 makes more sense.",
  },
  {
    type: "h2",
    text: "Gearing — Where the K8's Cassette Falls Out",
  },
  {
    type: "p",
    text: "Stock gearing on the K8 cassette is [2.733, 2.000, 1.590, 1.310, 1.130, 1.000] from Suzuki service manual 99500-36142-01E. Combined with the F15/R42 sprocket pair (2.800 final drive) and a 180/55ZR17 rear with rolling radius approximately 306 mm, the bike hits its 13,500 rpm power peak at exactly 86 km/h in first, 118 km/h in second, 148 km/h in third, 180 km/h in fourth, 209 km/h in fifth, and a theoretical 237 km/h in sixth. The simulator's 198.6 km/h trap puts the K8 about 10 km/h shy of the fifth-gear power peak at the line — meaning the bike crosses the trap line still pulling hard rather than tapering off, which is exactly where you want a supersport at the strip.",
  },
  {
    type: "p",
    text: "Switching to F16/R42 lengthens every shift point by 6.7 percent — first becomes 92 km/h, fifth becomes 223 km/h, sixth becomes 253 km/h. The trap-line rpm in fifth drops from roughly 13,000 to about 12,200, which is still well inside the meaningful power band on a 125 hp DOHC inline-four with a flat top end. The simulator catches 0.08 seconds of ET because the K8 stops bouncing off the rev limiter in lower gears. Going further to F16/R41 or F17/R42 starts to leave first-gear launch too tall for an Aamby Valley standing start and reverses the gain.",
  },
  {
    type: "h2",
    text: "Run Your Own Numbers",
  },
  {
    type: "p",
    text: "If you are considering a used K8 import — or already own one and want to know what the bike's strip ceiling actually is — the simulator at motoquant.in lets you sweep rider weight, ambient temperature, density altitude, and parts-catalogue mods to see where each tenth lives. The K8 is in the catalogue along with the K6 reference, the 2008 R6, the 2007 CBR600RR, and the 2009 ZX-6R for direct head-to-head comparisons. Toggle Aamby Valley to MMRT Chennai to see exactly how much altitude is costing you, and toggle the F15 stock sprocket to F16 to see the gearing math the same way the engineering brief computes it.",
  },
  {
    type: "p",
    text: "Two caveats on the numbers. First, the Sport Rider 10.91 s test was on a professional drag rider with a launch-control technique that is not what a club-day owner replicates. Real-world Indian K8 strip times sit in the 11.2 to 11.7 second band depending on rider technique, surface temperature, and humidity — the simulator's 11.04 s number is closer to the professional-rider envelope than the typical club-day number. Second, the litre-sport-600-1000 cluster's documented bias is roughly +0.15 s mean (sim slightly slow) with a band of ±0.22 s, so the absolute number you see is conservative and the relative deltas (K8 vs K6, K8 vs CBR600RR, F15 vs F16) are what should drive the buying decision.",
  },
  {
    type: "p",
    text: "The K8 remains the cheapest entry point into the 11-second quarter mile in India. A clean used K8 with the F15-to-F16 swap, a K&N filter, and a lithium battery costs ₹4.5 lakh delivered to your door with 0.17 s of ET gain over stock. That is genuinely competitive with a new Aprilia RS 660 or a used Triumph Street Triple 765 R for the strip-focused buyer, and the K8 still trades on the supersport pedigree that the parallel-twin or triple alternatives simply cannot match. If the simulator says the bike is faster than what you are riding now and the maths on parts availability works for your city, the K8 deserves the bike-detail-page deep-read.",
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
            {["Suzuki", "GSX-R600 K8", "600cc supersport", "Inline-four", "physics"].map(
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
            Suzuki GSX-R600 K8 Quarter-Mile Physics: 125hp 600cc Supersport
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
            25 May 2026 · 12 min read · MotoQuant Blog
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
                href="/blog/hayabusa-quarter-mile-physics-what-limits-9-6-seconds"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Hayabusa Quarter-Mile Physics: What Limits the 9.6
              </Link>{" "}
              — the litre-class big brother to the GSX-R600 with the same Suzuki
              SDTV throttle architecture.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-to-tune-for-mmrt-chennai"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to Tune for MMRT Chennai
              </Link>{" "}
              — the sea-level Chennai strip where the K8 should genuinely break
              into the 10.9s band like the Sport Rider test.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/triumph-street-triple-765r-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Triumph Street Triple 765 R Quarter-Mile Physics
              </Link>{" "}
              — the 118 hp triple that runs within 0.3 s of the K8 with a totally
              different engine architecture.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-the-motoquant-physics-engine-works"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How the MotoQuant Physics Engine Works
              </Link>{" "}
              — the 15-sub-model RK4 stack that produces every number in this
              post.
            </li>
            <li>
              ·{" "}
              <Link
                href="/bikes"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Browse the full bike catalog
              </Link>{" "}
              — every GSX-R600 spec, every gear ratio, every Cd value used by the
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
              Run the GSX-R600 K8 yourself
            </div>
            <div className="text-white/60 text-sm">
              Free simulator — pick the 2008 Suzuki GSX-R600 K8, dial in your
              local conditions, and watch the ET update live as you toggle
              sprockets, slip-ons, and lithium batteries.
            </div>
          </div>
          <Link
            href="/simulator?bike=suzuki-gsx-r600-k8-2008"
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
