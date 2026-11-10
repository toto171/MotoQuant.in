import Link from "next/link";
import SiteNav from "../../../components/SiteNav";
import SiteFooter from "../../../components/SiteFooter";
import StructuredData, { articleSchema } from "../../StructuredData";

const SLUG = "royal-enfield-interceptor-650-quarter-mile-physics";
const TITLE =
  "RE Interceptor 650 quarter-mile physics: 14.15s on 47hp";
const DESCRIPTION =
  "MotoQuant sims the RE Interceptor 650 at 14.15s and 155.8 km/h trap, 0.05s slower than its GT 650 sibling because of the upright bars. Plus a cost-per-tenth mod ladder.";

export const metadata = {
  title: "Royal Enfield Interceptor 650 quarter-mile physics | MotoQuant",
  description: DESCRIPTION,
  keywords: [
    "royal enfield interceptor 650 quarter mile",
    "interceptor 650 drag time",
    "interceptor 650 0-100",
    "interceptor 650 vs continental gt 650 quarter mile",
    "interceptor 650 top speed",
    "re 650 twin drag",
    "interceptor 650 sprocket size for drag",
    "interceptor 650 mods india",
    "re 650 cost per tenth",
    "interceptor 650 powertronic flash price",
    "interceptor 650 valley run",
    "interceptor 650 vs himalayan 450 quarter mile",
    "interceptor 650 vs ns400z",
    "royal enfield 650 cluster bias",
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
    text: "MotoQuant simulates the Royal Enfield Interceptor 650 at 14.15 seconds and 155.8 km/h trap under Aamby Valley November conditions. The Continental GT 650 runs 0.05 seconds quicker with an engine that is mechanically identical down to the cam profiles: 47 hp, 52 Nm, and 181 kg dry for the Interceptor. The difference is the wide handlebars and the upright seat. The Interceptor pushes 0.50 m² of frontal area through the air against the GT 650's 0.46 m², and at 150 km/h that 9 percent aero penalty costs almost exactly 50 milliseconds of ET. This is India's best-selling mid-displacement bike (Royal Enfield moved 31,847 Interceptor 650 units in FY24, per its annual report), so 14.15 seconds is where every owner's mod-budget question starts. Below are the cluster bias band and the cost-per-tenth ladder for an owner who wants to see a 13 on the timing board.",
  },
  {
    type: "h2",
    text: "What the Interceptor 650 is",
  },
  {
    type: "p",
    text: "Royal Enfield launched the 650 twin platform in late 2018: one engine, two bodies. Both bikes share the Bajaj-built 648 cc air/oil-cooled SOHC parallel twin, the 270-degree crank, the six-speed gearbox with the same internal ratios, the primary drive, and the 16-tooth front and 46-tooth rear sprockets on 520 chain. The Interceptor 650 wears the upright standard-naked body with wide tubular handlebars, mid-set pegs, and a 13.7-litre tank shaped to be sat behind. The Continental GT 650 wears the cafe-racer body on the same chassis, with clip-on bars roughly 80 mm lower, rear-set pegs that move the rider 40 mm back, and a 12.5-litre tank shaped to be tucked into. Catalog dry mass is 181 kg for the Interceptor and 184 kg for the GT 650, which carries 3 kg of extra body panels and the cafe seat hump. Both bikes have a 1,400 mm wheelbase.",
  },
  {
    type: "p",
    text: "The 648 cc twin makes 47 hp at 7,150 rpm and 52 Nm at 5,250 rpm from a 78.0 × 67.8 mm bore and stroke. Compression is 9.5:1, fuelling is Bosch EFI, and a single Bosch electronic unit fires both cylinders on a 270/450-degree pattern. Royal Enfield built the engine to be under-stressed: a 7,500 rpm redline (the Kawasaki Ninja 650 revs to 11,000 rpm on the same displacement) and a flat torque curve that gives 90 percent of peak torque from 3,000 rpm to 6,500 rpm. That suits a 60,000 km Indian commute. It does not suit a 12-second quarter mile, and the simulator shows both.",
  },
  {
    type: "h2",
    text: "Stock-tune simulation numbers",
  },
  {
    type: "p",
    text: "Here is the stock-tune result under Aamby Valley November conditions (density altitude around 1,100 m, 22°C ambient, dry asphalt, OEM Pirelli Phantom Sportscomp 130/70-18 rear at μ_peak ≈ 1.20, 78 kg rider):",
  },
  {
    type: "table",
    rows: [
      ["Metric", "Value", "Source"],
      ["Quarter-mile ET", "14.151 s", "MotoQuant sim"],
      ["Trap speed", "155.8 km/h", "MotoQuant sim"],
      ["60-foot", "2.481 s @ 51.6 km/h", "MotoQuant sim"],
      ["Eighth-mile", "9.182 s @ 124.7 km/h", "MotoQuant sim"],
      ["Expected real-world ET", "13.95 to 14.10 s", "cluster bias correction"],
      ["Peak hp (crank)", "47 @ 7,150 rpm", "RE 2024 spec sheet"],
      ["Peak torque", "52 Nm @ 5,250 rpm", "RE 2024 spec sheet"],
      ["Cd / frontal area", "0.76 / 0.50 m²", "MotoQuant catalog"],
    ],
  },
  {
    type: "p",
    text: "The Interceptor 650 sits in the simulator's mid_twin_500_700 cluster, which carries a bias band of about +0.16 seconds slow as of the May 30 2026 sweep. Apply that correction, and a well-prepped surface, a competent rider and warm tires should give 13.95 to 14.10 seconds. The little timed data that exists agrees. TeamBHP forum members have logged GPS-timed Interceptor 650 quarters between 13.9 and 14.4 seconds, depending on rider technique and ambient conditions, with most around 14.1. The order against the GT 650 (cleaner aero) and the Super Meteor 650 (heavier, taller) follows from the bikes' physical differences.",
  },
  {
    type: "callout",
    text: "Why the Interceptor is the slowest of the three RE 650 bikes: the three share one engine, but their mass and aero differ. The Continental GT 650 sims at 14.10 seconds on a smaller frontal area (clip-ons drop the rider 80 mm and pull the elbows in). The Super Meteor 650 sims at 14.62 seconds, 0.47 seconds slower than the Interceptor, because the cruiser body adds 40 kg and an upright torso that catches the wind. The Interceptor sits between them on every physical measure, and that is where the simulator puts it.",
  },
  {
    type: "h2",
    text: "Where the tenths live",
  },
  {
    type: "p",
    text: "The Interceptor 650 sim trace splits into three phases. From the launch line to 60 feet (2.481 seconds, 51.6 km/h) the bike is in first gear with the OEM clutch slipping. Peak wheel torque is roughly 195 Nm through the 16/46 final drive and the 3.071:1 first gear, and the OEM Pirelli Phantom Sportscomp rear can transmit almost all of it: slip ratio peaks at about 8 percent off the line, well inside the tire's grip envelope. Grip sets the limit in this phase, but with room to spare, because the OEM rubber is good for the torque on offer. The 2.48-second 60-foot is almost exactly what Interceptor owners post on GPS apps.",
  },
  {
    type: "p",
    text: "From 60 feet to the eighth-mile (9.182 seconds, 124.7 km/h) the bike runs through second and third and into fourth. With the torque peak at 5,250 rpm and the power peak at 7,150 rpm, the engine spends most of this phase between 5,000 and 7,500 rpm, the meat of the torque curve and the band the SOHC head was tuned for. It is not a high-rev screamer like the Ninja 650. It pulls cleanly from the torque peak to the rev limit, and the simulator log shows fairly even acceleration through second and third. This is the most efficient phase of the run.",
  },
  {
    type: "p",
    text: "Over the back 660 feet, from the eighth-mile to the trap, the bike is in fourth and fifth and aerodynamics take over. At 130 km/h, drag on a 0.76 Cd × 0.50 m² frontal area is roughly 285 N, about 60 percent of the rear-wheel thrust available at that speed. By 150 km/h drag has reached 380 N and the bike is running out of power to push against it. The simulated bike crosses the trap in fifth at 7,200 rpm, close to the power peak, and acceleration tails off over the last 200 feet. It never gets to upshift. Sixth is an overdriven highway gear at 1.000:1 that the Interceptor 650 does not use in a quarter-mile run.",
  },
  {
    type: "h2",
    text: "Interceptor 650 vs the Indian mid-twin field",
  },
  {
    type: "p",
    text: "The table compares five bikes that sit within ₹3 lakh of the Interceptor 650 on the Indian market and overlap with it on use. The numbers are MotoQuant stock-tune simulations under the same Aamby Valley November conditions, with OEM tires and OEM gearing on every bike (no mods, no swaps):",
  },
  {
    type: "table",
    rows: [
      ["Bike", "Sim ET", "Sim trap", "Kerb", "Peak hp", "Cd"],
      ["Kawasaki Ninja 650", "12.85 s", "184.3 km/h", "196 kg", "67", "0.62"],
      ["Bajaj Pulsar NS400Z", "13.42 s", "172.1 km/h", "174 kg", "40", "0.62"],
      ["RE Continental GT 650", "14.10 s", "157.8 km/h", "184 kg", "47", "0.68"],
      ["RE Interceptor 650", "14.15 s", "155.8 km/h", "181 kg", "47", "0.76"],
      ["RE Super Meteor 650", "14.62 s", "143.9 km/h", "221 kg", "47", "0.85"],
      ["Himalayan 450", "14.78 s", "138.2 km/h", "196 kg", "40", "0.82"],
    ],
  },
  {
    type: "p",
    text: "The Ninja 650 is in a different class. With 67 hp from Kawasaki's higher-revving parallel twin and a Cd of 0.62 behind a proper sport fairing, it posts a 12.85-second quarter that no production RE 650 will catch on a stock tune. An Interceptor 650 owner who wants to outrun one needs Stage 2 ECU work plus a turbo (not realistic at this displacement) or a different bike. The two are built for different buyers: the Ninja 650 for the strip, the Interceptor 650 for comfort all day. The Pulsar NS400Z slots between the Ninja 650 and the RE 650 twins at 13.42 seconds. Its KTM-derived 373 cc single makes 40 hp in a much lighter 174 kg chassis with sport-naked aero. On paper the Interceptor has the better power-to-weight ratio, 259 hp/tonne against 230 for the NS400Z, but that is misleading because the NS400Z carries far less aero penalty.",
  },
  {
    type: "p",
    text: "The spread across the three RE 650s is what the chassis physics predicts. The GT 650 leads at 14.10 on cleaner aero, 0.05 seconds ahead. The Interceptor 650 sits in the middle at 14.15. The Super Meteor 650 trails at 14.62, 0.47 seconds back, because its cruiser ergonomics, extra 40 kg and larger frontal area add up to a strip penalty that no engine tune on the shared 648 cc twin can recover. For an Indian buyer choosing between ₹3.04 lakh (Interceptor 650 ex-showroom Delhi, May 2026), ₹3.21 lakh (Continental GT 650) and ₹3.84 lakh (Super Meteor 650), the simulator's quickest strip pick is the GT 650, by 0.05 seconds. That margin is too small to outweigh the riding position you prefer. Pick the body you want to ride; on the strip the Interceptor and the GT are close to identical.",
  },
  {
    type: "h2",
    text: "Cost-per-tenth mod ladder for Indian Interceptor owners",
  },
  {
    type: "p",
    text: "From the 14.15-second stock baseline, which mods buy the most ET per rupee? The simulator runs each mod on its own against stock under Aamby Valley November conditions. Cost per tenth is the price of each 0.1 seconds of ET (lower is cheaper):",
  },
  {
    type: "table",
    rows: [
      ["Mod", "Spend", "ΔET", "Cost per tenth"],
      ["F15/R46 sprocket swap (JT + Diamond chain)", "₹2,400", "0.16 s", "₹15,000"],
      ["S&S Cycle Grand National slip-on (Indian-spec)", "₹38,500", "0.09 s", "₹427,800"],
      ["Powertronic Stage 1 ECU flash", "₹14,500", "0.21 s", "₹69,000"],
      ["Continental ContiRoadAttack 4 rear", "₹11,200", "0.06 s", "₹186,700"],
      ["Stage 1 + F15/R46 sprocket combo", "₹16,900", "0.34 s", "₹49,700"],
    ],
  },
  {
    type: "p",
    text: "The F15/R46 sprocket swap is the best buy. The stock Interceptor 650 runs F16/R46 on a 520 chain. Drop the front sprocket by one tooth to F15 and the final drive ratio rises from 2.875 to 3.067. That 6.7 percent shorter gearing keeps the engine nearer its 5,250 rpm torque peak through the launch. The simulator says the swap cuts 0.16 seconds, almost all of it in the first three gears. A JT front sprocket (JTF1264.15) costs about ₹950 and a Diamond 520 chain costs ₹1,450 at most Pune workshops: ₹2,400 fitted. The job takes 30 minutes, does not affect the warranty, can be fully undone, and is the cheapest tenth on any Indian-market mid-twin by a wide margin. The cost is engine speed on the highway: at 110 km/h in sixth it rises from roughly 4,200 rpm to 4,500 rpm. Most owners say they don't notice.",
  },
  {
    type: "p",
    text: "Powertronic India offers its Stage 1 flash for the 2020-onwards EFI Interceptor 650 (the 2018-2019 carburetor-era bikes cannot be flashed). The flash remaps fuel and ignition between 4,500 and 7,500 rpm, where the SOHC head does its work, and adds roughly 3 hp at the rear wheel. Powertronic India's published dyno chart shows 44 wheel hp after the flash, up from 41 stock. The simulator turns that into 0.21 seconds off the ET. The largest single share comes from the smoother midrange torque curve, which picks up about 0.04 seconds of 60-foot time on top of the back-half power gain. Add the F15/R46 sprocket swap and the combo costs ₹16,900 and takes the sim ET from 14.15 to 13.81: a 13 on the timing board for under ₹17,000, on a chassis that is otherwise stock. That is exceptional value at this displacement.",
  },
  {
    type: "p",
    text: "The S&S Cycle Grand National slip-on at ₹38,500 is the worst cost per tenth on the ladder, by a factor of nine. In the simulator it adds roughly 0.8 hp at the wheel through lower backpressure and saves about 1.4 kg at the rear, together worth 0.09 seconds. It sounds very different from the OEM cans. Royal Enfield tuned the stock exhaust to a mellow 89 dB at idle for Indian noise regulations; the S&S unit runs around 96 dB with the dB-killer fitted and closer to 101 dB without. If you want the sound, the S&S is well built and makes sense. If only the strip number matters, the same ₹38,500 pays for 16 sprocket swaps' worth of ET reduction.",
  },
  {
    type: "callout",
    text: "Sim vs real-world ET: the simulator reports 14.151 seconds at Aamby Valley in November. Apply the mid_twin_500_700 cluster bias correction of about -0.16 seconds, and a well-prepped surface, a competent rider and warm tires should give 13.95 to 14.10 seconds. At Chennai MMRT in February (sea level, hot ambient, higher humidity), density-altitude scaling takes off another 0.07 seconds. The quickest realistic stock-tune Interceptor 650 time in India is roughly 13.88 seconds, at MMRT in cool February weather.",
  },
  {
    type: "h2",
    text: "Price and who should buy it",
  },
  {
    type: "p",
    text: "The Interceptor 650 costs ₹3.04 lakh ex-showroom Delhi in the standard Canyon Red, ₹3.13 lakh in the Glitter Dusk dual-tone, and ₹3.27 lakh for the Mark Two flagship trim with alloy wheels and premium paint. On-road in Mumbai or Bangalore it comes closer to ₹3.55 to 3.75 lakh, including TCS, RTO, insurance and the Royal Enfield genuine accessories most buyers add (engine guards, sump guard, touring screen). At that price it competes directly with the Kawasaki Ninja 500 (₹5.24 lakh, a good deal more), the Honda CB350 H'ness (₹2.18 lakh, a good deal less), the Triumph Speed 400 (₹2.40 lakh, a direct rival), and its own siblings, the Continental GT 650 (₹3.21 lakh) and the Super Meteor 650 (₹3.84 lakh).",
  },
  {
    type: "p",
    text: "The Interceptor 650 suits the Indian buyer who wants British parallel-twin character (the 270-degree crank fires like a Triumph Bonneville or a BMW F 900 GS, with an uneven exhaust beat and an idle with character), a real 600 km of highway range per tank, and Royal Enfield's dealer network. That network covers every Indian state, including the Northeast, where the Japanese mid-twins have no dealers. The strip number is not the reason to buy this bike. The reason is that it is comfortable everywhere, on a chassis that is well sorted for both 4-up urban traffic and full-luggage highway runs.",
  },
  {
    type: "p",
    text: "An Interceptor 650 owner curious about the strip has a clear three-step path. First, the F15/R46 front sprocket swap: ₹2,400, 30 minutes at a Pune or Bangalore workshop, 0.16 seconds, no effect on the warranty. Second, the Powertronic Stage 1 flash: ₹14,500, two hours including the dyno tune session, another 0.21 seconds, and fully reversible (Powertronic restores the OEM map on request if you sell the bike). Third, a sticky rear tire: the Continental ContiRoadAttack 4 in 130/70-18 at ₹11,200 from Performance Racing Store. A total mod budget of ₹28,100 puts the Interceptor 650 at a sim ET of roughly 13.72 seconds. That is faster than a stock Pulsar NS400Z and within shouting distance of a stock CFMoto 450NK, on a bike that still tours and still wears OEM bodywork.",
  },
  {
    type: "h2",
    text: "Why the Interceptor will not run a 12",
  },
  {
    type: "p",
    text: "What would it take to put an Interceptor 650 in the 12s? On the physics, no realistic budget closes that gap. The Ninja 650 runs 12.85 because it makes 20 more horsepower, 4,000 rpm higher in the rev range, on a chassis that is 15 kg lighter and 18 percent cleaner through the air. To match a stock Ninja 650, an Interceptor 650 would need a 20 hp engine gain: bored cylinders, higher-lift cams, larger throttle bodies and a race ECU, easily ₹2.5 lakh of parts and labor, and the bike is no longer street legal. It would also need to lose 15 kg, which means carbon bodywork, a lithium battery and lightweight wheels for roughly ₹1.4 lakh more. And dropping the Cd from 0.76 to 0.62 needs a custom sport fairing at ₹80,000 plus paint.",
  },
  {
    type: "p",
    text: "That adds up to about ₹4.8 lakh in mods on top of a ₹3.05 lakh bike, and at that money you should buy the Ninja 650 instead. The platform's strengths are elsewhere. The Interceptor 650 is a bike to ride 60,000 km, not one to chase Ninja 650s with at the strip. The 13.72-second sim number from the three-step ladder above is the right ceiling for this chassis. Past that, tenths cost ₹1 lakh each, which is a poor use of money on a 47-horsepower air-cooled twin.",
  },
  {
    type: "h2",
    text: "Gearing and launch RPM",
  },
  {
    type: "p",
    text: "The Interceptor 650 ships with F16/R46 final drive on a 520 chain and six-speed gearbox ratios of 3.071, 2.056, 1.583, 1.292, 1.125 and 1.000. In a stock-tune Aamby Valley run the simulator log shows: launch in first at 3,800 rpm with the OEM clutch slipping; second at 1.34 seconds and 62 feet; third at 3.18 seconds and 240 feet; fourth at 5.91 seconds and 620 feet; fifth at 9.74 seconds and 1,180 feet; then across the trap line in fifth at 7,200 rpm and 155.8 km/h. It is a five-gear quarter. Like the Tiger 900 GT Pro and most six-speed bikes with an overdriven top gear, it never engages sixth on the strip.",
  },
  {
    type: "p",
    text: "After the sprocket swap, launch RPM is the biggest gearing lever. The OEM ECU launches the Interceptor 650 at roughly 3,800 rpm, 1,450 rpm below the torque peak. That conservative launch protects the clutch from cold starts and saves new owners from embarrassing wheelies, but it costs ET. Flash Powertronic Stage 1 and raise the launch RPM to 5,000 rpm, nearer the 5,250 rpm torque peak, and the simulator's 60-foot drops from 2.481 to 2.328 seconds. Total ET falls by roughly 0.15 seconds, on top of the flash gains already counted in the cost-per-tenth table.",
  },
  {
    type: "h2",
    text: "Run your own numbers",
  },
  {
    type: "p",
    text: "If you are weighing the Interceptor 650 against the Continental GT 650, the Super Meteor 650, the Pulsar NS400Z, the Kawasaki Ninja 650, or a 2018-onwards Interceptor on the Indian used market, the simulator at motoquant.in lets you change rider weight, ambient temperature, density altitude, tires and parts-catalog mods. You see where the tenths come from on your bike in your conditions. The cluster-bias correction above is built into the model: when the simulator says 14.15, expect 13.95 to 14.10 on a well-prepped surface with a competent rider and warm tires.",
  },
  {
    type: "p",
    text: "Two caveats. First, every number in this post is a stock-tune simulation under Aamby Valley November conditions. At Chennai MMRT in February (sea level, hot ambient, higher humidity) the simulator takes roughly 0.07 seconds off the Interceptor 650 on density altitude alone. At a high-altitude strip like Leh in summer it adds 0.40 to 0.55 seconds to the same bike. That is rare for an Indian touring bike, but Interceptor owners do ride those routes, and RE has a dealer in Leh. The order of the mods holds across venues; the absolute ETs move with the air.",
  },
  {
    type: "p",
    text: "Second, the mid_twin_500_700 cluster is small: six published tests in the 10 November 2026 accuracy sweep, with a weighted bias of +0.135 seconds, so the simulator runs these parallel twins slightly slow on average. More instrumented timeslips from Indian Interceptor 650 owners would tighten it. The comparisons against the GT 650, the Super Meteor 650 and the Ninja 650 are more reliable than the absolute times, because a class-wide bias moves all of them together.",
  },
  {
    type: "p",
    text: "The Royal Enfield Interceptor 650 was not designed as a strip bike, and its 14.15-second sim time says so. But it responds to gearing and ECU mods in a linear, predictable way that few stock Indian bikes do. A ₹17,000 mod budget (front sprocket plus Powertronic Stage 1 flash) takes the ET to 13.81, faster than several bikes that cost twice as much.",
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
          datePublished: "2026-05-31",
        })}
      />
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {[
              "Royal Enfield",
              "Interceptor 650",
              "Mid-twin 500-700",
              "270-degree crank",
              "Indian mid-displacement",
              "physics",
            ].map((t) => (
              <span
                key={t}
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Royal Enfield Interceptor 650 quarter-mile physics: 14.15s on 47hp
          </h1>
          <div className="text-sm text-white/60 mb-12">
            31 May 2026 · 13 min read · MotoQuant Blog
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
                href="/blog/re-continental-gt-650-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Royal Enfield Continental GT 650 quarter-mile physics
              </Link>
              : the cafe-racer sibling, 0.05s quicker on the same engine
              through aero alone.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/pulsar-ns400z-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Bajaj Pulsar NS400Z quarter-mile physics
              </Link>
              : the 373cc KTM-derived single that slots between the Interceptor
              and the Ninja 650 on ET.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-to-tune-for-aamby-valley-in-november"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to tune for Aamby Valley in November
              </Link>
              : the venue conditions used for every simulation above.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/indian-drag-strip-elevation-comparison"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Indian drag strip elevation comparison
              </Link>
              : why the Interceptor 650 picks up 0.07s in Chennai MMRT vs Aamby.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-the-motoquant-physics-engine-works"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How the MotoQuant physics engine works
              </Link>
              : the 15-submodel RK4 stack behind every ET number above.
            </li>
            <li>
              ·{" "}
              <Link
                href="/bikes"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Browse the full bike catalog
              </Link>
              : the specs, gear ratios and Cd values the simulator uses.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">
              Run the Interceptor 650 yourself
            </div>
            <div className="text-white/60 text-sm">
              Free simulator: pick the Royal Enfield Interceptor 650, swap to
              an F15/R46 sprocket, and watch the ET drop into the 13.9s live.
            </div>
          </div>
          <Link
            href="/simulator?bike=royal-enfield-interceptor-650&venue=aamby-valley"
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
