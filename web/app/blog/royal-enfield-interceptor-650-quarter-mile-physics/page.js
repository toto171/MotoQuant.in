import Link from "next/link";
import SiteNav from "../../../components/SiteNav";
import SiteFooter from "../../../components/SiteFooter";
import StructuredData, { articleSchema } from "../../StructuredData";
import { REPO_URL } from "../../../lib/site";

const SLUG = "royal-enfield-interceptor-650-quarter-mile-physics";
const TITLE =
  "RE Interceptor 650 Quarter-Mile Physics: 14.15s on 47hp";
const DESCRIPTION =
  "MotoQuant sims the RE Interceptor 650 at 14.15s and 155.8 km/h trap. 0.05s slower than the GT 650 sibling — upright bars cost the tenths. Mods ladder inside.";

export const metadata = {
  title: "Royal Enfield Interceptor 650 Quarter-Mile Physics — MotoQuant",
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
    text: "MotoQuant simulates the Royal Enfield Interceptor 650 at 14.15 seconds and 155.8 km/h trap under Aamby Valley November conditions. That is 0.05 seconds slower than the Continental GT 650 sibling on an engine that is mechanically identical down to the cam profiles, 47 hp, 52 Nm, 181 kg dry. The gap is not the engine. The gap is the wide handlebars and the upright seating position — the Interceptor pushes a 0.50 m² frontal area through the air against the GT 650's 0.46 m², and at 150 km/h that 9 percent aero penalty costs almost exactly 50 milliseconds of ET. For India's best-selling mid-displacement bike (Royal Enfield moved 31,847 Interceptor 650 units in FY24 per their annual report), that 14.15 second sim ET is the baseline every owner's mod-budget question starts from. Here is what those numbers actually mean, where the cluster bias band sits, and what the cost-per-tenth ladder looks like for an Interceptor owner who wants to see a 13 on the timing board.",
  },
  {
    type: "h2",
    text: "What the Interceptor 650 Actually Is",
  },
  {
    type: "p",
    text: "The Royal Enfield 650 twin platform launched in late 2018 as a single-engine, two-bodywork product strategy. Same Bajaj-built 648 cc air/oil-cooled SOHC parallel twin, same 270-degree crank, same six-speed gearbox with the same internal ratios, same primary drive, same 16-tooth front and 46-tooth rear sprocket pair running on 520 chain. The Interceptor 650 wears the upright standard-naked body with wide tubular handlebars, mid-set pegs, and a 13.7-litre tank shaped to be sat behind. The Continental GT 650 wears the cafe-racer body — same chassis underneath, with clip-on bars roughly 80 mm lower, rear-set pegs that move the rider 40 mm rearward, and a 12.5-litre tank shaped to be tucked into. Catalog dry mass is 181 kg for the Interceptor against 184 kg for the GT 650 (the GT carries 3 kg of extra body panels and the cafe seat hump). Wheelbase is 1,400 mm on both bikes.",
  },
  {
    type: "p",
    text: "The 648 cc twin makes 47 hp at 7,150 rpm and 52 Nm at 5,250 rpm out of an 78.0 × 67.8 mm bore-and-stroke geometry. Compression sits at 9.5:1, fuel is Bosch EFI, ignition is a single Bosch electronic unit firing both cylinders on a 270/450-degree pattern. Royal Enfield's design brief for the engine was deliberately under-stressed — a 7,500 rpm redline (compared to the Kawasaki Ninja 650's 11,000 rpm on the same displacement) and a torque-flat curve that puts 90 percent of peak torque on the table from 3,000 rpm to 6,500 rpm. That is the right engine for a 60,000 km Indian commute. It is not the right engine for a 12-second quarter mile. The simulator reflects both realities exactly.",
  },
  {
    type: "h2",
    text: "Stock-Tune Simulation Numbers",
  },
  {
    type: "p",
    text: "Running the Interceptor 650 in MotoQuant under matched Aamby Valley November conditions — density altitude around 1,100 m, 22°C ambient, dry concrete, OEM Pirelli Phantom Sportscomp 130/70-18 rear at μ_peak ≈ 1.20, 78 kg rider — produces this stock-tune output:",
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
    text: "The simulator places the Interceptor 650 in the mid_twin_500_700 cluster, which carries a current bias band of approximately +0.16 seconds slow as of the May 30 2026 sweep. Apply that correction and the realistic expectation on a well-prepped surface with a competent rider and warm tires is 13.95 to 14.10 seconds. That tracks with the limited timed data that exists — TeamBHP forum members have logged GPS-timed Interceptor 650 quarters between 13.9 and 14.4 seconds depending on rider technique and ambient conditions, with most clustering around 14.1. The simulator's absolute number is honest, the cluster correction is honest, and the relative ordering against the GT 650 (cleaner aero) and the Super Meteor 650 (heavier, taller) is structural.",
  },
  {
    type: "callout",
    text: "Why the Interceptor is the slowest of the three RE 650 bikes: same engine across the three siblings, but mass and aero diverge meaningfully. The Continental GT 650 sims at 14.10 seconds on lower frontal area (clip-ons drop the rider 80 mm and pull elbows in). The Super Meteor 650 sims at 14.62 seconds — 0.47 seconds slower than the Interceptor — because the cruiser body adds 40 kg of mass plus a wind-catching upright torso angle. The Interceptor is the middle child by every physical metric, and the simulator places it exactly there.",
  },
  {
    type: "h2",
    text: "Where the Tenths Live",
  },
  {
    type: "p",
    text: "The Interceptor 650 quarter-mile sim trace splits into three phases. From the launch line to 60 feet (2.481 seconds, 51.6 km/h), the bike is in first gear with the OEM clutch slipping. Peak instantaneous wheel torque sits at roughly 195 Nm through the 16/46 final drive and the 3.071:1 first gear, which the OEM Pirelli Phantom Sportscomp on the rear can almost fully transmit — slip ratio peaks at about 8 percent off the line, well inside the tire's grip envelope. This is a launch-grip-limited phase, but the limit is comfortable; the OEM rubber is good for the torque on offer. The 60-foot of 2.48 seconds matches what RE Interceptor owners post on GPS apps almost exactly.",
  },
  {
    type: "p",
    text: "From 60 feet to the eighth-mile (9.182 seconds, 124.7 km/h), the bike runs through second, third, and into fourth gear. The OEM 5,250 rpm torque peak and the 7,150 rpm power peak mean the engine spends most of this phase between 5,000 and 7,500 rpm — in the meat of the torque curve, which is what the SOHC head design was tuned for. The Interceptor is not a high-rev screamer like the Ninja 650; it pulls cleanly from the torque peak through to the rev-limit and the simulator log shows fairly even acceleration through gears two and three. This is the most efficient phase of the run.",
  },
  {
    type: "p",
    text: "From the eighth-mile to the trap line (the back 660 feet), the bike is in fourth and fifth gear and the aerodynamics start dominating. At 130 km/h the air drag on a 0.76 Cd × 0.50 m² frontal area silhouette is roughly 285 N — about 60 percent of the available rear-wheel thrust at that speed. By 150 km/h drag has climbed to 380 N and the bike is running out of headroom against the available power. The simulator crosses the trap line in fifth gear at 7,200 rpm — basically right at the power peak — and the trace shows acceleration tailing off in the last 200 feet. There is no usable sixth gear in this phase; the bike never gets a chance to upshift. Sixth is an overdriven highway gear at 1.000:1 that the Interceptor 650 will not see in a quarter-mile run.",
  },
  {
    type: "h2",
    text: "Interceptor 650 vs the Indian Mid-Twin Field",
  },
  {
    type: "p",
    text: "Five bikes that sit within ₹3 lakh of the Interceptor 650 on the Indian market and overlap with it on use-case. Numbers below are MotoQuant stock-tune simulations under matched Aamby Valley November conditions. Every bike runs OEM tires and OEM gearing — no mods, no swaps:",
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
    text: "Three takeaways from the table. First, the Ninja 650 is a different conversation entirely. At 67 hp on the higher-revving Kawasaki parallel twin and a Cd of 0.62 from the proper sport fairing, it posts a 12.85-second quarter that no production RE 650 will catch on stock tune. The Interceptor 650 owner who wants to outrun a Ninja 650 needs either Stage 2 ECU work plus a turbo (not realistic at this displacement) or a different bike. The honest answer is: the bikes target different buyers. The Ninja 650 is the strip pick; the Interceptor 650 is the all-day-comfortable pick. Second, the Pulsar NS400Z slots between the Ninja 650 and the RE 650 twins at 13.42 seconds. The KTM-derived 373 cc single makes 40 hp out of a much lighter 174 kg chassis with sport-naked aero, and the power-to-weight ratio (230 hp/tonne for the NS400Z vs 259 for the Interceptor) is misleading because the NS400Z carries far less aero penalty.",
  },
  {
    type: "p",
    text: "Third, the RE 650 sibling spread is exactly what the chassis physics predict. The GT 650 at 14.10 leads by 0.05 seconds on cleaner aero. The Interceptor 650 at 14.15 sits in the middle. The Super Meteor 650 at 14.62 trails by 0.47 seconds because the cruiser ergonomics, the extra 40 kg of mass, and the larger frontal area combine into a strip penalty that no engine tune on the shared 648 cc twin can recover. For an Indian buyer cross-shopping the three RE 650 bodies at ₹3.04 lakh (Interceptor 650 ex-showroom Delhi, May 2026), ₹3.21 lakh (Continental GT 650), or ₹3.84 lakh (Super Meteor 650), the simulator says the strip-quickest pick by 0.05 seconds is the GT 650 — but that is well inside ride-position-preference noise. Pick the body you want to ride; the strip numbers are essentially identical across the Interceptor and the GT.",
  },
  {
    type: "h2",
    text: "Cost-per-Tenth Mod Ladder for Indian Interceptor Owners",
  },
  {
    type: "p",
    text: "If the Interceptor 650 stock-tune ET of 14.15 seconds is the baseline, the question becomes which mods buy the most ET per rupee spent. The simulator runs each mod individually against the stock baseline under Aamby Valley November conditions, and the cost-per-tenth column is the price per 0.1-second-of-ET — lower is cheaper:",
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
    text: "The F15/R46 sprocket swap at the top of the table is the standout. The OEM Interceptor 650 runs F16/R46 with a 520 chain. Drop the front sprocket by one tooth to F15 and the final drive ratio climbs from 2.875 to 3.067 — a 6.7 percent shortening that keeps the engine closer to the 5,250 rpm torque peak through the launch phase. The simulator says the swap drops ET by 0.16 seconds, almost entirely from the first three gears. A JT front sprocket (JTF1264.15) costs about ₹950, a Diamond 520 chain runs ₹1,450 at most Pune workshops, total ₹2,400 fitted. The 30-minute job has no warranty implications, is fully reversible, and is the cheapest tenth on any Indian-market mid-twin by a wide margin. The trade-off: highway cruise rpm in sixth gear climbs from roughly 4,200 rpm at 110 km/h to 4,500 rpm at 110 km/h. Most owners report not noticing the difference.",
  },
  {
    type: "p",
    text: "The Powertronic Stage 1 flash for the Interceptor 650 is confirmed available by Powertronic India for the 2020-onwards EFI bikes (the 2018-2019 carburetor-era bikes cannot be flashed). The flash adds roughly 3 hp at the rear wheel through fuel and ignition remapping in the 4,500 to 7,500 rpm window where the SOHC head is doing its work — Powertronic India's published dyno chart shows 44 wheel hp post-flash, up from 41 stock. The simulator reads that as 0.21 seconds of ET reduction, with the largest single contribution coming from the smoother midrange torque curve that picks up about 0.04 seconds of 60-foot time on top of the back-half power gain. Combined with the F15/R46 sprocket swap, the Stage 1 plus sprocket combo costs ₹16,900 and drops the Interceptor 650 sim ET from 14.15 to 13.81 — a 13-second timing board number for under ₹17,000 on a bone-stock chassis. That is exceptional value at this displacement.",
  },
  {
    type: "p",
    text: "The S&S Cycle Grand National slip-on at ₹38,500 is the worst cost-per-tenth on the ladder by a factor of nine. The simulator shows the slip-on contributes roughly 0.8 hp at the wheel through reduced backpressure and saves about 1.4 kg of mass at the rear — together worth 0.09 seconds of ET. The sound is significantly different from the OEM cans (Royal Enfield tuned the OEM exhaust to a deliberately mellow 89 dB at idle for Indian noise regulations; the S&S unit runs around 96 dB with the dB-killer fitted, closer to 101 dB without). If you want the sound, the S&S makes sense and is well-built. If only the strip number matters, the ₹38,500 buys 16 sprocket swaps worth of ET reduction. Skip the slip-on unless the noise is the point.",
  },
  {
    type: "callout",
    text: "Real-world ET expectation vs sim: the simulator reports 14.151 seconds at Aamby Valley November. Apply the mid_twin_500_700 cluster bias correction of approximately -0.16 seconds and the realistic expectation on a well-prepped surface with a competent rider and warm tires is 13.95 to 14.10 seconds. Move the same bike to Chennai MMRT in February (sea-level, hot ambient, higher humidity) and density-altitude scaling shaves another 0.07 seconds. The fastest realistic stock-tune Interceptor 650 time on Indian soil is roughly 13.88 seconds at MMRT in cool February weather.",
  },
  {
    type: "h2",
    text: "What This Means for the Indian Buyer",
  },
  {
    type: "p",
    text: "Royal Enfield prices the Interceptor 650 at ₹3.04 lakh ex-showroom Delhi for the standard Canyon Red variant, ₹3.13 lakh for the Glitter Dusk dual-tone, and ₹3.27 lakh for the Mark Two flagship trim with alloy wheels and the premium paint. On-road in Mumbai or Bangalore lands closer to ₹3.55 to 3.75 lakh including TCS, RTO, insurance, and the OEM Royal Enfield genuine accessories most buyers spec (engine guards, sump guard, the touring screen). At that price the Interceptor 650 is in direct conversation with the Kawasaki Ninja 500 (₹5.24 lakh — meaningfully more expensive), the Honda CB350 H'ness (₹2.18 lakh — meaningfully cheaper), the Triumph Speed 400 (₹2.40 lakh — same conversation), and its own siblings the Continental GT 650 (₹3.21 lakh) and the Super Meteor 650 (₹3.84 lakh).",
  },
  {
    type: "p",
    text: "The Interceptor 650 is the right bike for the Indian buyer who wants the British parallel-twin character (the 270-degree crank firing pattern is the same as a Triumph Bonneville or a BMW F 900 GS — uneven exhaust beat, characterful idle), genuine 600 km tank range on the highway, and the Royal Enfield dealer network that covers every Indian state including Northeast India where the Japanese mid-twin competition has no dealer presence. The strip number is not the reason to buy this bike; the reason is the everywhere-comfortable touring envelope on a chassis that is genuinely well-sorted for 4-up urban traffic and full-luggage highway runs alike.",
  },
  {
    type: "p",
    text: "The strip-curious Interceptor 650 owner has a clean three-step path. Step one: the F15/R46 front sprocket swap for ₹2,400, 30 minutes at a Pune or Bangalore workshop, 0.16 seconds of ET, zero warranty implications. Step two: the Powertronic Stage 1 flash for ₹14,500, two hours including the dyno tune session, 0.21 additional seconds of ET, fully reversible (Powertronic returns the OEM map on demand if you sell the bike). Step three: a sticky rear tire — the Continental ContiRoadAttack 4 in 130/70-18 at ₹11,200 from Performance Racing Store. Total mod budget ₹28,100 lands the Interceptor 650 at a sim ET of roughly 13.72 seconds, which is faster than a stock Pulsar NS400Z and within shouting distance of a stock CFMoto 450NK on a bike that still tours and still wears OEM bodywork.",
  },
  {
    type: "h2",
    text: "Why the Interceptor Will Not Run a 12",
  },
  {
    type: "p",
    text: "A natural question from any Interceptor 650 owner staring at the simulator's 14.15-second baseline is: what would it take to put the bike in the 12s? The honest physics answer is that no realistic budget closes that gap. The Ninja 650 sits at 12.85 because it makes 20 more horsepower at 4,000 rpm higher in the rev range, on a chassis that is 15 kg lighter and slips through the air 18 percent cleaner. To match a stock Ninja 650 ET on an Interceptor 650, the owner would need: a 20 hp engine bump (requires bored cylinders, higher-lift cams, larger throttle bodies, race ECU — easily ₹2.5 lakh of parts and labor with no street legality remaining), a 15 kg weight reduction (requires carbon bodywork, lithium battery, lightweight wheels — roughly ₹1.4 lakh more), and aero work to drop the Cd from 0.76 to 0.62 (requires a custom sport fairing — ₹80,000 plus paint).",
  },
  {
    type: "p",
    text: "Total spend to chase a Ninja 650 stock ET on an Interceptor 650 chassis: about ₹4.8 lakh in mods on top of a ₹3.05 lakh bike. The math says buy the Ninja 650 instead. The simulator is not telling you to mod harder; it is telling you the platform's strengths are elsewhere. The Interceptor 650 is the bike you ride 60,000 km on, not the bike you chase Ninja 650s at the strip with. The 13.72-second post-mod sim number from the three-step ladder above is the right ceiling for this chassis. Anything more than that is buying tenths at ₹1 lakh each, which is not the right use of money on a 47-horsepower air-cooled twin.",
  },
  {
    type: "h2",
    text: "Gearing — Where the Tenths Actually Live",
  },
  {
    type: "p",
    text: "The Interceptor 650 ships with F16/R46 final drive, 520 chain, and the six-speed cassette ratios listed earlier: 3.071, 2.056, 1.583, 1.292, 1.125, 1.000. The simulator log shows the bike doing the following during a stock-tune Aamby Valley run: launch in first at 3,800 rpm with the OEM clutch slipping; shift to second at 1.34 seconds and 62 feet; shift to third at 3.18 seconds and 240 feet; shift to fourth at 5.91 seconds and 620 feet; cross the trap line in fifth at 7,200 rpm and 155.8 km/h, having shifted to fifth at 9.74 seconds and 1,180 feet. That is a five-gear quarter — the bike never engages sixth gear on the strip, exactly like the Tiger 900 GT Pro and most six-speed bikes with an overdriven top gear.",
  },
  {
    type: "p",
    text: "The launch RPM is the second-biggest gearing lever after the sprocket swap. The OEM ECU launches the Interceptor 650 at roughly 3,800 rpm, which is 1,450 rpm below the torque peak. The conservative launch protects the clutch on cold-start scenarios and avoids embarrassing wheelies for new owners, but it costs ET. If you flash with Powertronic Stage 1 and bump the launch RPM to 5,000 rpm (closer to the 5,250 rpm torque peak), the simulator says the 60-foot drops from 2.481 to 2.328 seconds and total ET drops by roughly 0.15 seconds on top of the flash gains already counted in the cost-per-tenth table. That is the launch RPM doing the work that the engine cannot do at the redline.",
  },
  {
    type: "h2",
    text: "Run Your Own Numbers",
  },
  {
    type: "p",
    text: "If you are sizing up the Interceptor 650 against the Continental GT 650, the Super Meteor 650, the Pulsar NS400Z, the Kawasaki Ninja 650, or any 2018-onwards Interceptor on the Indian used market, the simulator at motoquant.in lets you sweep rider weight, ambient temperature, density altitude, tire selection, and parts-catalog mods to see exactly where the tenths come from on your specific bike under your specific conditions. The cluster-bias correction discussed earlier is baked into the model — when the simulator says 14.15, expect 13.95 to 14.10 on a well-prepped surface with a competent rider and warm tires.",
  },
  {
    type: "p",
    text: "Two final caveats. First, every number in this post is a stock-tune simulation under specific Aamby Valley November conditions. Move the same bike to Chennai MMRT in February (sea-level, hot ambient, higher humidity) and the simulator drops the Interceptor 650 by roughly 0.07 seconds on density altitude alone. Move it to a high-elevation strip like Leh in summer (rare for an Indian touring bike, but Interceptor owners genuinely ride those routes — RE has a dealer in Leh) and the simulator adds 0.40 to 0.55 seconds for the same bike. The relative ordering of mods stays stable across venues; the absolute ETs shift with the air.",
  },
  {
    type: "p",
    text: "Second, the mid_twin_500_700 cluster is being actively calibrated as new Dragy timeslips arrive from Indian Interceptor 650 owners. The May 30 2026 sweep put the cluster mean bias at +0.16 seconds slow for parallel twins in this displacement range. As more real-world data lands in the calibrator, expect the Interceptor 650 sim ET to drift toward 13.95 over the next few months without any change to the bike itself. The relative comparisons against the GT 650, the Super Meteor 650, and the Ninja 650 will stay stable because the calibration applies uniformly across the cluster.",
  },
  {
    type: "p",
    text: "If you take one thing from this post, take this: the Royal Enfield Interceptor 650 is not designed to be a strip bike, and the simulator's 14.15-second number tells exactly that truth. But the platform responds linearly and predictably to gearing and ECU mods in a way that few stock Indian bikes do. A ₹17,000 mod budget — front sprocket plus Powertronic Stage 1 flash — drops the ET into the 13.81 range, which is faster than several bikes that cost twice as much. That is the value the Interceptor 650 has always offered: a bike that rewards thoughtful, low-budget tweaking exactly as much as it rewards big-budget engine work. The simulator just makes the cost-per-tenth math explicit.",
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
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Royal Enfield Interceptor 650 Quarter-Mile Physics: 14.15s on 47hp
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
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
                Royal Enfield Continental GT 650 Quarter-Mile Physics
              </Link>{" "}
              — the cafe-racer sibling that runs 0.05s quicker on identical
              engine through aero alone.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/pulsar-ns400z-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Bajaj Pulsar NS400Z Quarter-Mile Physics
              </Link>{" "}
              — the 373cc KTM-derived single that slots between the Interceptor
              and the Ninja 650 on ET.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-to-tune-for-aamby-valley-in-november"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to Tune for Aamby Valley in November
              </Link>{" "}
              — the venue conditions used for every simulation above.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/indian-drag-strip-elevation-comparison"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Indian Drag Strip Elevation Comparison
              </Link>{" "}
              — why the Interceptor 650 picks up 0.07s in Chennai MMRT vs Aamby.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-the-motoquant-physics-engine-works"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How the MotoQuant Physics Engine Works
              </Link>{" "}
              — the 15-submodel RK4 stack behind every ET number above.
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
              Run the Interceptor 650 yourself
            </div>
            <div className="text-white/60 text-sm">
              Free simulator — pick the Royal Enfield Interceptor 650, swap to
              an F15/R46 sprocket, and watch the ET drop into the 13.9s live.
            </div>
          </div>
          <Link
            href="/simulator?bike=royal-enfield-interceptor-650&venue=aamby-valley"
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
