import Link from "next/link";
import SiteNav from "../../../components/SiteNav";
import SiteFooter from "../../../components/SiteFooter";
import StructuredData, { articleSchema } from "../../StructuredData";

const SLUG = "suzuki-gsx-r600-k8-quarter-mile-physics";
const TITLE = "Suzuki GSX-R600 K8 quarter-mile physics: 125hp 600cc";
const DESCRIPTION =
  "Sport Rider clocked the 2008 GSX-R600 K8 at 10.91s sea level. MotoQuant sims 11.04s at Aamby Valley. K8 vs K6, four India mods for a used 600.";

export const metadata = {
  title: "Suzuki GSX-R600 K8 quarter-mile physics | MotoQuant",
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
    text: "Sport Rider strapped its test gear to a stock 2008 Suzuki GSX-R600 K8 and clocked 10.91 seconds at 204.4 km/h trap at sea level. MotoQuant simulates the same bike at 11.04 seconds and 198.6 km/h trap under Aamby Valley November conditions. The 0.13 second gap is entirely the 1,100 m density altitude penalty, not a physics bug. The more useful question is what the K8 changed over the 2006-2007 K6 that was already in the catalogue, and whether the 12 extra horsepower buys back the 2 kg of frame weight.",
  },
  {
    type: "h2",
    text: "What the K8 is",
  },
  {
    type: "p",
    text: "Suzuki launched the third-generation GSX-R600 at INTERMOT 2007 as the 2008 model year, internal code K8. The year codes are Suzuki's own: K8 is the 2008 model, K9 the 2009 carryover, L0 the 2010 carryover. All three years share the same chassis, engine map, and bodywork. Suzuki replaced the K8 in 2011 with a heavily revised model called the L1, so K8 to L0 is one self-contained three-year generation.",
  },
  {
    type: "p",
    text: "The engine's dimensions carried over from the K6: same 67.0 mm bore, same 42.5 mm stroke, same 599 cc displacement, same DOHC four-valve head. The internals changed. Suzuki fitted lighter pistons (3 g lighter per piston per the service-manual bulletin), revised intake cam timing, larger throttle bodies, and a new SDTV secondary butterfly map. Compression went from 12.9:1 on the K6 to 13.3:1 on the K8. Peak power rose from 113 hp to 125 hp, both at 13,500 rpm. Peak torque moved from 66.8 Nm at 12,000 rpm to 69 Nm at 11,200 rpm: a little more torque, a little lower in the rev range, which matters at the strip.",
  },
  {
    type: "p",
    text: "Suzuki rebuilt the frame around a new aluminium twin-spar casting that swapped the K6's diagonal upper rail for a wider, hollower section. The new frame added 2 kg (162 vs 160 kg dry) and gained roughly 8 percent torsional rigidity per the Suzuki engineering brief. Brakes moved from axial four-piston to radial-mount four-piston Tokico calipers from the same supplier as the contemporary GSX-R1000 K8. Suspension is Showa SFF-BP up front and a Showa monoshock at the rear, both adjustable for preload, compression, and rebound.",
  },
  {
    type: "p",
    text: "The K8 sat alongside the GSX-R750 K8 on the same dealership floor and shared much of its hardware: same frame casting (re-tuned for the 750cc engine torque), same swingarm, same brakes, same forks. The 750 made 148 hp from 750 cc on the same wheelbase and added roughly 1 kg. In the 2008 model year, Suzuki was the only manufacturer offering a 600cc and a 750cc supersport on the same chassis; Honda, Yamaha, and Kawasaki only had 600s.",
  },
  {
    type: "h2",
    text: "Stock-tune simulation numbers",
  },
  {
    type: "p",
    text: "Running the GSX-R600 K8 in MotoQuant under matched Aamby Valley November conditions (density altitude approximately 1,100 m, 22°C ambient, dry asphalt, μ_peak 1.30 on the OEM 180/55ZR17 rear), with a 78 kg rider on the 162 kg dry bike, gives these stock-tune numbers:",
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
    text: "The 0.13 second gap between the simulator and the Sport Rider sea-level number is almost entirely density altitude. Aamby Valley at 1,100 m loses roughly 11 percent of standard sea-level air density, which costs the engine about 13 horsepower at the crank and adds roughly 0.1 to 0.15 seconds of ET on a 125 hp bike. The 5.8 km/h trap-speed gap has the same cause: density altitude scaling at peak crank power. In sea-level Madras Motor Race Track conditions, the simulator returns 10.93 s and 203.8 km/h trap for the same K8, within 0.02 s and 0.6 km/h of the Sport Rider number. The calibration holds; the K8 lands inside the litre-sport-600-1000 cluster's documented ±0.22 s mean absolute delta band.",
  },
  {
    type: "callout",
    text: "A 600cc supersport at Aamby Valley is roughly 0.15 seconds slower than the same bike at MMRT Chennai, about half a bike length over the quarter. For a personal-best run, sea-level Chennai wins for any naturally-aspirated 600, and the trap-speed gap widens at the top end, where density altitude losses compound.",
  },
  {
    type: "h2",
    text: "K8 vs K6: where the 12 horsepower went",
  },
  {
    type: "p",
    text: "The K6 has been in the MotoQuant catalogue since the first physics work in 2024. Run back to back under matched Aamby Valley conditions, the two bikes show what the K8 refresh bought:",
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
    text: "Three changes do almost all the work. The 12 horsepower is worth roughly 0.10 seconds on its own: the simulator's power sensitivity on a 162 kg supersport at this displacement is around 0.85 hundredths per horsepower in the top third of the run. The aero changes matter more than the spec sheet suggests: Cd dropped from 0.68 to 0.60 because the K8 cowl reshape moved the stagnation point lower on the screen and Suzuki added a small lip on the upper fairing that re-attaches the flow before it separates off the rider's helmet. That 0.08 Cd reduction is worth another 0.08 to 0.10 seconds at trap speeds above 180 km/h, where drag dominates.",
  },
  {
    type: "p",
    text: "The third change is the gearing. Suzuki dropped the front sprocket from F17 (K6 OEM) to F15 (K8 OEM) while keeping R42 at the rear. The final drive ratio jumps from 2.471 (K6) to 2.800 (K8), 13.3 percent shorter. With the K8's revised cassette (slightly closer first-to-second ratios per the K8 service manual GSF-8A-M5), the bike spends less time bouncing off the rev limiter between shifts and reaches the trap line in fifth gear at roughly 13,200 rpm. The K6 arrived in high fifth, just short of a shift to sixth. The gearing change alone is worth about 0.08 seconds, and unusually for a stock-bike spec change, it costs nothing at the top end. Both bikes are gearing-limited at a theoretical sixth-gear top speed around 263 km/h, well above the simulated trap.",
  },
  {
    type: "p",
    text: "Net result: the K8 is 0.27 seconds quicker, 5.8 km/h faster at the trap and 2 kg heavier. A K6 gives 96 percent of the K8's strip number for typically ₹50,000 to ₹75,000 less on the used Indian market. A K8 brings radial brakes, a more rigid frame, and better parts availability in the long run, because Suzuki sold the platform across three model years.",
  },
  {
    type: "h2",
    text: "K8 vs its 2008 inline-four rivals",
  },
  {
    type: "p",
    text: "Four 600cc inline-fours competed against the K8 in 2008, and all four are in the MotoQuant catalogue. Here they are under matched Aamby Valley conditions with the same 78 kg rider:",
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
    text: "The 2008 R6 is the fastest of the four on paper and in the simulator, by 0.07 seconds and 2.6 km/h. The R6's edge comes from 2 extra horsepower, slightly better aerodynamics and an even shorter final drive. It pays for them with 4 kg of extra mass and a notoriously narrow powerband below 9,000 rpm. The CBR600RR runs 0.04 s behind the K8 despite 7 fewer horsepower; the Honda wins back ground with 7 kg less mass and a harder 60-foot launch from its slipper-equipped cassette. The 2009 ZX-6R is the slowest of the four, mainly on aerodynamics: the older 599 cc Kawasaki carried a higher Cd and a less aggressive intake, and it shows in the trap-speed column.",
  },
  {
    type: "p",
    text: "The table leaves out what every Indian used-supersport buyer cares about: parts availability. The K8 chassis carried through to 2010 unchanged. Tokico front pads, Showa fork seals, and OEM SDTV throttle-body service kits are all still in current Suzuki India catalogue support. The 2008 R6 chassis carried through 2016 with only minor revisions, so Yamaha parts are similarly available. The 2007 CBR600RR was a one-year clean-sheet design (Honda redesigned it in 2008 with a new frame), so a 2007 is a slightly harder used buy in India. The 2009 ZX-6R was the last year of the 599 cc generation; Kawasaki moved to 636 cc in 2013, and 599 cc parts are now grey-market only.",
  },
  {
    type: "h2",
    text: "What limits the K8 at Aamby Valley",
  },
  {
    type: "p",
    text: "Three limits, in order of impact on the simulated ET:",
  },
  {
    type: "p",
    text: "1. The 1.81 s 60-foot. A modern litre superbike with the same rider posts 1.55 to 1.60 s to the 60-foot line. The K8 gives away roughly two-tenths in the first 18 metres. With 125 hp at 13,500 rpm, there is not enough torque at 4,000 rpm to break the rear loose, but there is enough that the clutch needs careful slip through the first half of first gear. The simulator runs an idealised launch and still posts 1.81 s, because below 80 km/h the bike is limited by engine output, not tyre grip. The K8 has traction to spare and not enough torque to use it. That is the usual 600cc story at the strip.",
  },
  {
    type: "p",
    text: "2. The 198.6 km/h trap. The K8 crosses the trap line in fifth gear at roughly 13,000 rpm, just below the 13,500 rpm power peak. Sixth is a highway gear; the bike never uses it in a quarter. The 198.6 km/h trap follows directly from the gearing and aero. To raise it you need more power (ECU flash, slip-on exhaust, or both) or less drag (rider tuck position, taller windscreen, removed mirrors). Both work, and neither is free.",
  },
  {
    type: "p",
    text: "3. The 11.2-second band is the K8's effective lower bound on stock gearing. The simulator shows you can shave to roughly 10.80 s with the standard 600cc mod ladder (Yoshimura R-77 slip-on, Power Commander V map, K&N drop-in filter, 16T rear sprocket reduction, lithium battery, race-pad up). Below 10.80 s you need wet-clutch slip-on slicks plus an aftermarket airbox. The same spend gets a 2025 ZX-6R into the high 10.7s with less effort, and that is the trade-off a used-K8 buyer makes against a new bike.",
  },
  {
    type: "h2",
    text: "The Indian used market",
  },
  {
    type: "p",
    text: "Suzuki never officially sold the GSX-R600 in India during the K8 to L0 production window. Every K8, K9, or L0 in India arrived via CBU import (mostly through the Hyderabad and Pune dealership grey channels between 2008 and 2012), private import from the Middle East, or domestic resale of bikes originally imported by club racers. In May 2026, a well-maintained K8 to L0 with under 30,000 km on the clock sells for ₹3.8 lakh to ₹5.5 lakh, depending on documentation, ABS prep status, and accident history.",
  },
  {
    type: "p",
    text: "That puts the K8 in a strange price band. A used 2022 Kawasaki Ninja 400 sells for roughly ₹4.5 lakh and runs the quarter in the high 12s. A used 2018 Suzuki GSX-R600 K8 sells for the same money and runs the quarter in the low 11s: a 1.4-second gap for the same price. The catch is parts and service: the Ninja 400 has full Kawasaki India dealer support, the K8 has none. Service costs roughly 3x at any of the four or five qualified Indian supersport mechanics (Naveen in Bangalore, Dhruva in Pune, Shaheed in Hyderabad), and a major service interval at 24,000 km runs ₹35,000 to ₹50,000.",
  },
  {
    type: "p",
    text: "Mods that make a difference on a K8, ranked by cost-per-tenth at Indian retail in May 2026:",
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
    text: "The 16-tooth front-sprocket swap is unusual for a supersport because the K8 already runs an aggressively short F15. Going to F16 lengthens the final drive by 6.7 percent, which trades 60-foot time for a higher trap-line gear and slightly lower trap rpm. The simulator shows a net 0.08 s gain at Aamby Valley because the K8 spends roughly 0.18 s of the run bouncing off the rev limiter in third and fourth on stock F15. The longer F16 lets the engine breathe past peak power instead of clipping the limiter mid-shift. At MMRT Chennai (sea level, denser air, more engine output) the gain narrows to roughly 0.05 s, so this is mainly a mod for altitude strips.",
  },
  {
    type: "callout",
    text: "The cheapest quick path on a used K8 in India: 16T front sprocket (₹950, 0.08 s) plus K&N drop-in (₹4,600, 0.04 s) plus lithium battery (₹8,200, 0.05 s). That is ₹13,750 in total for 0.17 s of ET. A used Yoshimura R-77 slip-on adds 0.12 s for another ₹32,000, putting the full stack at ₹45,750 for 0.29 s of ET gain. Getting below 10.80 s takes a full race exhaust plus mapping, close to ₹1.2 lakh. At that spend, ask whether a new ZX-6R 2024 makes more sense.",
  },
  {
    type: "h2",
    text: "Gearing on the K8's cassette",
  },
  {
    type: "p",
    text: "Stock gearing on the K8 cassette is [2.733, 2.000, 1.590, 1.310, 1.130, 1.000] from Suzuki service manual 99500-36142-01E. Combined with the F15/R42 sprocket pair (2.800 final drive) and a 180/55ZR17 rear with rolling radius approximately 306 mm, the bike hits its 13,500 rpm power peak at exactly 86 km/h in first, 118 km/h in second, 148 km/h in third, 180 km/h in fourth, 209 km/h in fifth, and a theoretical 237 km/h in sixth. At the simulator's 198.6 km/h trap, the K8 is about 10 km/h short of the fifth-gear power peak, so it crosses the line still pulling hard rather than tapering off. That is where you want a supersport at the strip.",
  },
  {
    type: "p",
    text: "Switching to F16/R42 lengthens every shift point by 6.7 percent: first becomes 92 km/h, fifth becomes 223 km/h, sixth becomes 253 km/h. The trap-line rpm in fifth drops from roughly 13,000 to about 12,200, still well inside the useful power band of a 125 hp DOHC inline-four with a flat top end. The simulator finds 0.08 seconds of ET because the K8 stops bouncing off the rev limiter in lower gears. Going further to F16/R41 or F17/R42 starts to leave first-gear launch too tall for an Aamby Valley standing start and reverses the gain.",
  },
  {
    type: "h2",
    text: "Run your own numbers",
  },
  {
    type: "p",
    text: "If you are considering a used K8 import, or own one and want to know its strip ceiling, the simulator at motoquant.in lets you sweep rider weight, ambient temperature, density altitude, and parts-catalogue mods to see where each tenth comes from. The catalogue has the K8 alongside the K6 reference, the 2008 R6, the 2007 CBR600RR, and the 2009 ZX-6R for head-to-head comparisons. Switch from Aamby Valley to MMRT Chennai to see how much altitude costs you, and swap the stock F15 sprocket for F16 to see the gearing maths worked the same way as the engineering brief.",
  },
  {
    type: "p",
    text: "Two caveats on the numbers. First, the Sport Rider 10.91 s test used a professional drag rider with a launch-control technique a club-day owner will not repeat. Real-world Indian K8 strip times sit in the 11.2 to 11.7 second band depending on rider technique, surface temperature, and humidity. The simulator's 11.04 s number is closer to the professional-rider envelope than the typical club-day number. Second, the litre-sport-600-1000 cluster's documented bias is roughly +0.15 s mean (sim slightly slow) with a band of ±0.22 s, so treat the absolute number as conservative and base the buying decision on the relative deltas (K8 vs K6, K8 vs CBR600RR, F15 vs F16).",
  },
  {
    type: "p",
    text: "The K8 remains the cheapest entry point into the 11-second quarter mile in India. A clean used K8 with the F15-to-F16 swap, a K&N filter, and a lithium battery costs ₹4.5 lakh delivered to your door with 0.17 s of ET gain over stock. For a strip-focused buyer that competes with a new Aprilia RS 660 or a used Triumph Street Triple 765 R, and the K8 has a supersport pedigree the parallel-twin and triple alternatives cannot match. If the simulator says it is faster than what you ride now, and parts availability works out for your city, read the K8's full bike page next.",
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
                  className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
                >
                  {t}
                </span>
              ),
            )}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Suzuki GSX-R600 K8 quarter-mile physics: 125hp 600cc supersport
          </h1>
          <div className="text-sm text-white/60 mb-12">
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
                Hayabusa quarter-mile physics: what limits the 9.6
              </Link>:{" "}
              the litre-class big brother to the GSX-R600 with the same Suzuki
              SDTV throttle architecture.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-to-tune-for-mmrt-chennai"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to tune for MMRT Chennai
              </Link>:{" "}
              the sea-level Chennai strip, where the K8 should break into the
              10.9s band like the Sport Rider test.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/triumph-street-triple-765r-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Triumph Street Triple 765 R quarter-mile physics
              </Link>:{" "}
              the 118 hp triple that runs within 0.3 s of the K8 with a very
              different engine layout.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-the-motoquant-physics-engine-works"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How the MotoQuant physics engine works
              </Link>:{" "}
              the 15-sub-model RK4 stack that produces every number in this
              post.
            </li>
            <li>
              ·{" "}
              <Link
                href="/bikes"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Browse the full bike catalog
              </Link>:{" "}
              the GSX-R600 specs, gear ratios and Cd values the simulator
              uses.
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
              Pick the 2008 Suzuki GSX-R600 K8 in the free simulator, set your
              local conditions and watch the ET update live as you swap
              sprockets, slip-ons and lithium batteries.
            </div>
          </div>
          <Link
            href="/simulator?bike=suzuki-gsx-r600-k8-2008"
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
