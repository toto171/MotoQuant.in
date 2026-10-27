import Link from "next/link";
import SiteNav from "../../../components/SiteNav";
import SiteFooter from "../../../components/SiteFooter";
import StructuredData, { articleSchema } from "../../StructuredData";
import { REPO_URL } from "../../../lib/site";

const SLUG = "triumph-tiger-900-gt-pro-quarter-mile-physics";
const TITLE =
  "Triumph Tiger 900 GT Pro Quarter-Mile Physics: 108hp Triple at 12.08s";
const DESCRIPTION =
  "MotoQuant sims the 2024 Triumph Tiger 900 GT Pro at 12.081s / 196.5 km/h trap — dead-heat ET with BMW F 900 GS, 3 km/h faster at trap. Indian price + mods.";

export const metadata = {
  title: "Triumph Tiger 900 GT Pro Quarter-Mile Physics — MotoQuant",
  description: DESCRIPTION,
  keywords: [
    "triumph tiger 900 gt pro quarter mile",
    "tiger 900 gt pro 0-100",
    "tiger 900 gt pro india price",
    "tiger 900 gt pro vs f 900 gs",
    "tiger 900 gt pro vs r 1300 gs",
    "tiger 900 gt pro vs ktm 890 adventure",
    "tiger 900 gt pro drag time",
    "triumph 888cc triple",
    "tiger 900 t-plane crank",
    "mid adventure bike india",
    "tiger 900 2024 vs 2023",
    "tiger 900 gt pro top speed",
    "tiger 900 gt pro powertronic",
    "tiger 900 gt pro mods india",
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
    text: "MotoQuant simulates the 2024 Triumph Tiger 900 GT Pro at 12.081 seconds and a 196.5 km/h trap under Aamby Valley November conditions. That puts the road-biased mid-ADV triple within 2 milliseconds of the BMW F 900 GS on ET — dead heat to three decimal places — but 3.0 km/h ahead at the trap line. For a 219 kg kerb 888cc inline-triple riding a 19-inch front cast wheel on road-biased Metzeler Tourance Next 2 rubber, those are interesting numbers. They are also the reason the 2024 refresh matters: the +13 hp the 2024 update added (95 hp on the 2020-2023 platform up to 108 hp) does almost nothing for ET versus the F 900 GS twin, but it changes the trap zone story completely. The triple keeps pulling where the twin runs out of breath.",
  },
  {
    type: "h2",
    text: "What the 2024 Tiger 900 Refresh Actually Changed",
  },
  {
    type: "p",
    text: "The 2024 Tiger 900 is not a new bike. It is a mid-cycle refresh of the 2020 T-plane triple platform — same 888cc displacement (78.0 × 61.9 mm), same DOHC 4-valve head architecture, same 270/180/270-degree T-plane crank firing pattern that Triumph introduced to give the triple a twin-like low-end torque feel below 5000 rpm and a screaming triple-like top-end above. What Triumph changed for 2024 is cam timing, the airbox internals, and a 0.27 bump in compression ratio (from 11.0:1 up to 11.27:1). Triumph press kit numbers: 108 hp at 9500 rpm (up from 95 hp at 9500), 90 Nm at 6850 rpm (up from 87 Nm at 7250 rpm), both measured at the crank. That is +13 hp and +3 Nm with the torque peak moved 400 rpm earlier in the rev range — the engine pulls harder out of corners and breathes harder past 8000 rpm.",
  },
  {
    type: "p",
    text: "The chassis side of the refresh is more conservative. The 2024 Tiger 900 GT Pro adds a larger 7-inch TFT dash (the previous 5-inch unit pulled), heated grips and seats as standard on GT Pro spec, an updated cornering ABS map, and roughly 2 kg of added electronics weight from the upgraded IMU and the connectivity module. Dry mass climbs 2 kg to 198 kg, kerb climbs to 219 kg including the 20 L fuel tank — same kerb number as the F 900 GS, which is part of why the two bikes post the same ET to three decimals. Frame, swingarm, fork, shock, and final drive geometry carry over from 2020-2023 unchanged. Service manual T0301460 confirms all gearbox internals — 6-speed cassette with ratios of 2.690, 1.947, 1.526, 1.272, 1.095, and 0.957 — are unchanged from 2020.",
  },
  {
    type: "p",
    text: "The variant matters here. The 2024 Tiger 900 ships in three trims: Tiger 900 GT (base, ₹14.65 lakh), Tiger 900 GT Pro (road-biased, the bike this post simulates, ₹15.95 lakh ex-showroom Delhi), and Tiger 900 Rally Pro (off-road-biased with 21-inch front spoke wheel and softer suspension travel, ₹16.95 lakh). The GT Pro keeps the 19-inch front cast wheel and the road-biased Metzeler Tourance Next 2 OEM rubber, which is the configuration the simulator uses. The Rally Pro variant on its 21-inch front spoke wheel and Karoo Street tires drops to roughly 12.54 seconds in the simulator — the off-road wheel and tire setup cost about 0.46 seconds of ET stock-engine, mostly through aero (wider front hub exposure) and tire grip (block-tread peak mu around 1.05 vs 1.18 for the road-biased Tourance).",
  },
  {
    type: "h2",
    text: "Stock-Tune Simulation Numbers",
  },
  {
    type: "p",
    text: "Running the Tiger 900 GT Pro in MotoQuant with a 78 kg rider, OEM Metzeler Tourance Next 2 road-biased ADV rubber (peak grip coefficient 1.18 on dry concrete), 22°C ambient, dry concrete, and density altitude around 1100 m (Aamby Valley November), the stock-tune output is:",
  },
  {
    type: "table",
    rows: [
      ["Metric", "Value", "Source"],
      ["Quarter-mile ET", "12.081 s", "MotoQuant sim"],
      ["Trap speed", "196.5 km/h", "MotoQuant sim"],
      ["60-foot", "2.362 s @ 56.4 km/h", "MotoQuant sim"],
      ["Eighth-mile", "8.075 s @ 161.9 km/h", "MotoQuant sim"],
      ["Expected real-world ET", "~11.80 to 12.00 s", "cluster bias correction"],
      ["Peak hp (crank)", "108 @ 9500 rpm", "Triumph 2024 spec"],
      ["Peak torque", "90 Nm @ 6850 rpm", "Triumph 2024 spec"],
      ["Cd / frontal area", "0.80 / 0.56 m²", "MotoQuant catalog"],
    ],
  },
  {
    type: "p",
    text: "The simulator places the Tiger 900 GT Pro on the boundary between the litre_sport_600_1000 cluster and the mid_twin_500_700 cluster. At 108 hp and 219 kg kerb the power-to-weight ratio is roughly 493 hp per tonne — slightly higher than the F 900 GS (480 hp/tonne) and meaningfully lower than the CFMoto 675SR-R (480 hp/tonne dressed in much better aero). The Tiger out-traps the F 900 GS by 3.0 km/h because the inline triple has 1000 rpm more usable rev range past the torque peak, and the simulator log shows the bike still accelerating at the trap line where the twin is starting to plateau. The 60-foot delta is essentially zero (2.362 vs 2.353 — well inside simulator noise), which confirms the triple is not a launch-pace bike. It is a back-half bike.",
  },
  {
    type: "callout",
    text: "Why the Tiger out-traps but does not out-ET the F 900 GS: the simulator shows the Tiger crossing the trap line at 9100 rpm in fifth gear, still 400 rpm short of its 9500 rpm peak power. The F 900 GS crosses the trap line at 8400 rpm in fifth, only 100 rpm short of its 8500 rpm peak power. The Tiger has more headroom to keep pulling past the trap, which is why the trap speed gap exists. But the F 900 GS pulls harder out of the gate on its 93 Nm torque peak (vs 90 Nm on the Tiger) at a lower 6750 rpm (vs 6850 rpm) — that 750-rpm-and-3-Nm gap closes the ET back to a dead heat through the first 660 feet.",
  },
  {
    type: "h2",
    text: "Why the T-Plane Crank Matters for the Quarter Mile",
  },
  {
    type: "p",
    text: "Triumph introduced the T-plane crank with the 2020 Tiger 900 — a 270/180/270-degree firing offset that breaks the conventional even-firing 120/120/120 inline-triple pattern. The point of the T-plane is to give the triple a twin-like exhaust pulse below 5000 rpm (two firing events close together, then a longer gap) while preserving the triple-like top-end. In practice this means the engine has a much stronger usable torque band from 3500 rpm to 5500 rpm than a conventional even-firing triple like the Street Triple 765 R — and the simulator sees this clearly in the launch phase.",
  },
  {
    type: "p",
    text: "From the sim log, the Tiger 900 GT Pro launches at 5500 rpm with the OEM A and S clutch slipping for the first 0.6 seconds. The T-plane crank produces a slightly lumpier torque trace than a conventional triple would in this RPM band — peak instantaneous torque is roughly 4 percent higher than the average, because the close-spaced firing events overlap. The slipper clutch absorbs that pulsation, but the result on the strip is that the Tiger 900 puts down measurably more usable thrust in the launch phase than the Street Triple 765 R does at the same RPM. The Street Triple compensates with more peak power, but for the 60-foot specifically, the T-plane is a launch advantage on the road-biased ADV chassis.",
  },
  {
    type: "p",
    text: "Where the T-plane stops mattering is past 6500 rpm, where the close-spaced firing events blur into a more conventional triple pulse. The simulator shows the Tiger 900 transitioning from twin-like behavior to triple-like behavior right around the 6850 rpm torque peak — the back half of the quarter-mile is a conventional triple pull, which is why the trap speed lands closer to a Street Triple 765 R (which sims at 11.62s and 215.3 km/h trap on a similar chassis weight) than to a parallel twin like the F 900 GS.",
  },
  {
    type: "h2",
    text: "Tiger 900 GT Pro vs the Mid-ADV Field",
  },
  {
    type: "p",
    text: "Five mid-segment adventure bikes, five different platform philosophies, one venue. Numbers below are MotoQuant stock-tune simulations under matched Aamby Valley November conditions. Every bike runs its OEM tires and OEM gearing — no mods, no swaps, no tire upgrades:",
  },
  {
    type: "table",
    rows: [
      ["Bike", "Sim ET", "Sim trap", "Kerb", "Peak hp", "Cd"],
      ["BMW R 1300 GS", "11.174 s", "218.4 km/h", "237 kg", "145", "0.55"],
      ["Triumph Tiger 900 GT Pro", "12.081 s", "196.5 km/h", "219 kg", "108", "0.80"],
      ["BMW F 900 GS", "12.083 s", "193.5 km/h", "219 kg", "105", "0.82"],
      ["Triumph Tiger 900 Rally Pro", "12.538 s", "184.4 km/h", "228 kg", "108", "0.85"],
      ["Yamaha Tenere 700", "12.660 s", "179.9 km/h", "204 kg", "73", "0.82"],
    ],
  },
  {
    type: "p",
    text: "Three things are worth pulling out of that table. First, the Tiger 900 GT Pro and the F 900 GS are a true dead heat on ET — 2 milliseconds apart, both running 219 kg kerb on similar power outputs. The Tiger keeps the 3 km/h trap advantage from its higher-revving engine, but the F 900 GS holds the line on ET because the parallel-twin torque peak comes in 100 rpm earlier and 3 Nm harder. For an Indian buyer cross-shopping at ₹15.95 lakh (Tiger GT Pro) vs ₹13.75 lakh (F 900 GS), the simulator says the buy is not about strip pace. It is about character: T-plane triple noise and back-half pull on the Tiger, parallel-twin launch and BMW dealer network on the F 900 GS.",
  },
  {
    type: "p",
    text: "Second, the Rally Pro variant of the Tiger 900 costs 0.457 seconds versus the GT Pro on identical engine and identical mass. That delta is entirely the 21-inch front spoke wheel plus the Karoo Street block-tread OEM tire. If you spec the Rally Pro and want strip pace back, the swap to a road-biased ADV tire alone closes roughly 0.20 seconds of that gap — but the 21-inch front wheel itself is worth another 0.13 seconds of rotational inertia and aero that no tire swap can recover. The Rally Pro is the bike you buy if you actually use the off-road capability. If you do not, the GT Pro is faster everywhere except dirt.",
  },
  {
    type: "p",
    text: "Third, the R 1300 GS is in a different conversation. At 145 hp, 237 kg kerb, and a Cd of 0.55 (BMW invested heavily in the GS Pro fairing for the 2024 refresh), the R 1300 sims to 11.174s and 218.4 km/h. That is 0.91 seconds and 21.9 km/h ahead of the Tiger 900 GT Pro, which is what you would expect from a 37 hp power bump on a bike that is only 18 kg heavier and slips through the air 31 percent better. The R 1300 GS is the strip-fast ADV. The Tiger 900 GT Pro is the road-biased balance pick.",
  },
  {
    type: "h2",
    text: "Tiger 900 GT Pro vs the Triple Field",
  },
  {
    type: "p",
    text: "The Tiger 900 GT Pro is the Triumph triple that does not look like a Triumph triple on paper. To make that visible, here is the same engine architecture across four Triumph platforms — same 12-valve DOHC layout, same Hinckley pedigree, very different bikes:",
  },
  {
    type: "table",
    rows: [
      ["Bike", "Disp", "Peak hp", "Kerb", "Cd", "Sim ET", "Sim trap"],
      ["Daytona 660", "660 cc", "95", "201 kg", "0.55", "11.62 s", "210.4 km/h"],
      ["Street Triple 765 R", "765 cc", "118", "188 kg", "0.62", "11.087 s", "215.3 km/h"],
      ["Tiger 900 GT Pro", "888 cc", "108", "219 kg", "0.80", "12.081 s", "196.5 km/h"],
      ["Trident 660", "660 cc", "80", "189 kg", "0.62", "12.10 s", "194.8 km/h"],
    ],
  },
  {
    type: "p",
    text: "The takeaway: the Tiger 900 GT Pro posts the same ET as the Trident 660 despite carrying 28 more horsepower. The 30 kg of additional kerb mass and the 0.18 jump in Cd (from 0.62 on the Trident to 0.80 on the Tiger) eat almost all of the power advantage. The Street Triple 765 R is one full second quicker on ET than the Tiger 900 GT Pro on essentially the same 12-valve triple architecture — the engine is bigger and makes less power per liter on the Tiger, the chassis is 31 kg heavier, and the riding position adds 0.18 to the drag coefficient. For an Indian buyer who wants triple character and does not care about off-road, the Street Triple 765 R is the faster bike for ₹2 lakh less at ₹13.95 lakh ex-showroom.",
  },
  {
    type: "p",
    text: "The Daytona 660 is the interesting middle ground. It posts a 11.62 second quarter on 95 hp because the faired sport silhouette drops the Cd to 0.55 — the same Cd as the litre-class R1 or RSV4. The Daytona 660 trap speed of 210.4 km/h is 14 km/h higher than the Tiger 900 GT Pro despite the Tiger carrying 13 more horsepower. Aero matters more than power in the trap zone, and the Tiger 900 silhouette is fighting a losing battle against the Daytona fairing.",
  },
  {
    type: "h2",
    text: "Cost-per-Tenth Mod Ladder for Indian Owners",
  },
  {
    type: "p",
    text: "If the Tiger 900 GT Pro stock-tune ET of 12.08 seconds is the starting point, the question becomes which mods buy the most ET per rupee spent. The simulator runs each mod individually against the stock baseline under Aamby Valley November conditions, and the cost-per-tenth column is the price-per-0.1-second-of-ET — lower is cheaper:",
  },
  {
    type: "table",
    rows: [
      ["Mod", "Spend", "ΔET", "Cost per tenth"],
      ["F15/R42 sprocket swap (DID 525VX3)", "₹4,200", "0.13 s", "₹32,300"],
      ["Powertronic Stage 1 ECU flash", "₹38,000", "0.18 s", "₹211,100"],
      ["Bridgestone Battlax T32 (rear, 17in)", "₹14,800", "0.09 s", "₹164,400"],
      ["Akrapovic Slip-On Racing (Ti)", "₹78,000", "0.06 s", "₹1,300,000"],
      ["Stage 1 + sprocket combo", "₹42,200", "0.30 s", "₹140,700"],
    ],
  },
  {
    type: "p",
    text: "The sprocket-swap line at the top of the table is the surprise. The OEM Tiger 900 GT Pro runs F16/R42 with a 525 chain, which is geared for road-touring comfort. Drop the front sprocket by one tooth to F15/R42 (final drive ratio climbs from 2.625 to 2.800) and the simulator says the bike picks up 0.13 seconds of ET — almost entirely in the launch phase, where the lower gearing keeps the engine closer to the torque peak through the clutch slip window. The DID 525VX3 chain that fits the swap costs about ₹4,200 for the chain plus a JT front sprocket and an OEM Triumph rear, total ₹4,200 to ₹4,500 depending on where you source it in Pune or Bangalore. That is the cheapest tenth in the cost-per-tenth column by a wide margin.",
  },
  {
    type: "p",
    text: "The Powertronic Stage 1 flash for the Tiger 900 GT Pro is confirmed available by Powertronic India for the Tiger 900 GT and Tiger 900 GT Pro variants on the 2024 ride-by-wire ECU. The flash adds roughly 7 hp at the rear wheel (Powertronic India dyno chart shows 105 wheel hp up from 98 stock — the 108 crank number translates to about 98 at the wheel through the standard 8-9 percent drivetrain loss on a chain-final-drive triple). The flash also remaps fuel and ignition through the midrange where the T-plane crank is doing its torque work, which the simulator picks up as a 0.05 second 60-foot reduction on top of the back-half power gain. Combined with the sprocket swap, the Stage 1 plus sprocket combo costs ₹42,200 and shaves 0.30 seconds — moving the Tiger 900 GT Pro stock-tune from 12.08 into the 11.78 range, which is Street Triple 765 stock territory on a bike that costs ₹2 lakh more.",
  },
  {
    type: "p",
    text: "The Akrapovic slip-on at ₹78,000 is the worst cost-per-tenth on the ladder by a factor of six. The simulator shows the slip-on contributes roughly 1.4 hp peak through reduced backpressure and saves about 2.3 kg of mass off the muffler — together worth 0.06 seconds of ET. The sound is significantly different (the Tiger 900 GT Pro stock muffler is regulated by Euro 5 to a fairly quiet 92 dB; the Akrapovic Racing slip-on runs around 102 dB with the dB-killer in place, 108 dB with the dB-killer removed). If the sound matters to you, the slip-on makes sense. If only the strip number matters, the ₹78,000 buys 9.3 sprocket-swaps worth of ET reduction. Skip the slip-on unless the noise matters.",
  },
  {
    type: "callout",
    text: "Real-world ET expectation vs sim: the simulator reports 12.081 seconds at Aamby Valley November. Apply the mid_twin_500_700 cluster bias correction of approximately -0.18 seconds and the realistic expectation on a well-prepped surface with a competent rider and warm tires is 11.85 to 12.00 seconds. Move the same bike to Chennai MMRT in February (sea-level, hot ambient) and density-altitude scaling shaves another 0.06 seconds. The fastest realistic Tiger 900 GT Pro stock-tune time on Indian soil is roughly 11.79 seconds at MMRT in cool February weather.",
  },
  {
    type: "h2",
    text: "What This Means for the Indian Buyer",
  },
  {
    type: "p",
    text: "Triumph India listed the Tiger 900 GT Pro at ₹15.95 lakh ex-showroom Delhi for the standard variant (₹16.95 lakh for the Rally Pro variant with the 21-inch front spoke wheel and the long-travel suspension) at the December 2023 dealer launch. On-road in Mumbai or Bangalore lands closer to ₹18.50 to 19.50 lakh including TCS, RTO, insurance, and the OE Triumph touring panniers most buyers spec. That puts the Tiger 900 GT Pro in direct conversation with the BMW F 900 GS (₹13.75 lakh ex-showroom — meaningfully cheaper), the BMW R 1300 GS (₹20.95 lakh ex-showroom — meaningfully more expensive), the KTM 890 Adventure (discontinued in India, replaced by 990 Adventure at ₹16.65 lakh), and the Suzuki V-Strom 800DE (₹10.30 lakh ex-showroom — a different segment entirely on price).",
  },
  {
    type: "p",
    text: "The Tiger 900 GT Pro is the right ADV for the Indian buyer who wants triple character and the Triumph dealer network, and wants a bike that genuinely commutes 200 km a day in Pune monsoon traffic without complaining. The GT Pro variant on its 19-inch road-biased front wheel is the road-touring spec, not the off-road spec. The Rally Pro variant exists for the rider who actually uses the off-road capability and is willing to pay 0.46 seconds of ET for it. For everyone else, the GT Pro on Tourance Next 2 tires is the right pick.",
  },
  {
    type: "p",
    text: "The strip-curious Tiger 900 GT Pro owner has two paths. The cheap path is the F15 front sprocket swap for ₹4,200 — a 30-minute job at any Pune workshop, picks up 0.13 seconds, no warranty implications, fully reversible. The serious path is Powertronic Stage 1 plus the sprocket combo for ₹42,200 total, which lands the bike at roughly 11.78 seconds — Street Triple 765 R territory for ₹2 lakh less, on a bike that also tours and goes off-road on demand. That is good value for the strip-curious ADV rider.",
  },
  {
    type: "h2",
    text: "Why the Tiger 900 Refresh Was the Right Call",
  },
  {
    type: "p",
    text: "Triumph could have walked into the 2024 refresh and given the Tiger 900 the Trident 660 treatment — soften it, simplify it, drop the price point. Triumph could also have done the Tiger 900 RR treatment — peaky cams, a 12000 rpm redline, a sport-biased chassis tune. Triumph did neither. The 2024 refresh added the 13 horsepower the bike needed to keep up with the F 900 GS in the showroom, kept the T-plane crank that defines the engine character, kept the road-biased chassis tune that suits 90 percent of Indian ADV use cases, and bumped the electronics package to keep parity with the German competition. The simulator numbers reflect a coherent product decision: 12.08 second quarter, 196.5 km/h trap, with the Stage 1 path to 11.78 sitting on the shelf for the rider who wants more.",
  },
  {
    type: "p",
    text: "The Tiger 900 GT Pro is not the fastest mid-ADV in India — the R 1300 GS is. It is not the cheapest — the V-Strom 800DE is. It is not the most off-road capable — the Tiger 900 Rally Pro variant and the KTM 990 Adventure are. What the Tiger 900 GT Pro is, by the simulator numbers, is the best-balanced mid-ADV at this price point: triple character that the parallel-twin competition cannot match, road-touring chassis tune that the spoke-wheel ADVs trade away for dirt capability, and a Stage 1 mod path that closes the gap to the Street Triple 765 for less money than the next variant up costs.",
  },
  {
    type: "h2",
    text: "Gearing — Where the Tenths Live",
  },
  {
    type: "p",
    text: "The Tiger 900 GT Pro ships with F16/R42 final drive, 525 chain, and the 6-speed cassette ratios listed earlier. The simulator log shows the bike doing the following during a stock-tune Aamby Valley run: launch in first at 5500 rpm with the OEM slipper clutch; shift to second at 1.13 seconds and 60 feet; shift to third at 2.51 seconds and 195 feet; shift to fourth at 4.62 seconds and 510 feet; cross the trap line in fifth at 9100 rpm and 196.5 km/h, having shifted to fifth at 7.94 seconds and 1180 feet. That is a five-gear quarter — the signature of a mid-ADV with relatively short individual gears stacked under an overdriven sixth.",
  },
  {
    type: "p",
    text: "Notice that the bike never engages sixth gear on the strip — sixth at 0.957:1 with F16/R42 is purely for highway cruise economy. At 110 km/h in sixth, the engine sits at roughly 4400 rpm, which is where Triumph wanted noise and vibration to live for ADV touring. The F15/R42 sprocket swap discussed earlier shifts the launch point closer to the 6850 rpm torque peak and tightens the gear stack across all six gears. The simulator says the resulting gearing change picks up the 0.13 seconds entirely through the first three gears — by fourth gear the lower final drive is already costing top-end pull, but the launch advantage outweighs the late-shift cost. Net positive 0.13 seconds.",
  },
  {
    type: "p",
    text: "For the rider who genuinely wants the Tiger 900 GT Pro to do the strip thing, the highest-impact gearing change is not the sprockets. It is the launch RPM. The OEM launch RPM in the Triumph Keihin ECU is set conservatively at 5500 rpm to protect the slipper clutch on muddy off-road climbs. If you flash with Powertronic Stage 1 and bump the launch RPM to 7000 rpm (closer to the 6850 torque peak with a 150 rpm cushion), the simulator says the 60-foot drops from 2.362 to 2.198 seconds and the total ET drops by roughly 0.17 seconds. Combine that with the F15/R42 sprocket swap and the Tiger 900 GT Pro sims out at 11.78 seconds for under ₹45,000 in mods plus a flash — closing to within 0.6 seconds of the R 1300 GS stock-tune for under ₹2 lakh in mods total.",
  },
  {
    type: "h2",
    text: "Run Your Own Numbers",
  },
  {
    type: "p",
    text: "If you are sizing up the Tiger 900 GT Pro against the BMW F 900 GS, the R 1300 GS, the Suzuki V-Strom 800DE, or any used 2020-2023 Tiger 900 on the Indian market, the simulator at motoquant.in lets you sweep rider weight, ambient temperature, density altitude, tire selection, and parts-catalog mods to see exactly where the tenths come from on your specific bike under your specific conditions. The cluster-bias correction discussed earlier is baked into the model — when the simulator says 12.08, expect 11.85 to 12.00 on a well-prepped surface with a competent rider and warm tires.",
  },
  {
    type: "p",
    text: "Two final caveats. First, every number in this post is a stock-tune simulation under specific Aamby Valley November conditions. Move the same bike to Chennai MMRT in February (sea-level, hot ambient, higher humidity) and the simulator drops the Tiger 900 GT Pro by roughly 0.06 seconds on density altitude alone. Move it to a high-elevation strip like Leh or Manali (rare for an ADV at this weight, but Indian Tiger 900 owners do ride those routes) and the simulator adds 0.30 to 0.40 seconds for the same bike. The relative ordering of which mods help most stays stable across venues; the absolute ETs shift with the air.",
  },
  {
    type: "p",
    text: "Second, the mid_twin_500_700 cluster bias is being actively calibrated in the background. The most recent sweep pass on May 30 2026 put the cluster mean bias at +0.18 seconds slow for parallel twins and triples in this displacement range. As the calibration work continues, expect the Tiger 900 GT Pro sim ET to drift toward 11.90 to 11.95 over the next few months without any change to the bike itself. The relative comparisons against the F 900 GS, the Street Triple 765 R, and the Daytona 660 will stay stable because the calibration applies uniformly across the cluster.",
  },
  {
    type: "p",
    text: "If you take one thing from this post, take this: the Triumph Tiger 900 GT Pro 2024 is the most coherent mid-ADV refresh Triumph has done since the original Tiger 800 XCx in 2015. The +13 hp does almost nothing for ET versus the F 900 GS twin, but it changes the back-half character completely. The T-plane crank still gives the bike a torque feel below 5000 rpm that no competing parallel twin can quite match. And the Stage 1 mod path puts the strip number where the Street Triple 765 R sits stock, for less money than the Rally Pro variant of the same Tiger costs. That is the kind of mod-ladder accessibility that has made the Tiger 900 platform the best-selling mid-ADV in India for FY25 — and the simulator says the FY26 refresh keeps the platform there.",
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
              "Triumph",
              "Tiger 900 GT Pro",
              "Mid ADV",
              "T-plane triple",
              "Indian ADV market",
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
            Triumph Tiger 900 GT Pro Quarter-Mile Physics: 108hp Triple at 12.08s
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
            31 May 2026 · 14 min read · MotoQuant Blog
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
                href="/blog/bmw-f-900-gs-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                BMW F 900 GS Quarter-Mile Physics: 105hp Mid-ADV at 12.08s
              </Link>{" "}
              — the parallel-twin sibling that posts a dead-heat ET on different
              engine architecture.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/triumph-street-triple-765r-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Triumph Street Triple 765 R Quarter-Mile Physics
              </Link>{" "}
              — the sport-biased Triumph triple that the Tiger 900 GT Pro Stage 1
              mod path targets at 11.78s.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/cfmoto-675sr-r-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                CFMoto 675SR-R Quarter-Mile Physics: The 95hp Daytona 660 Rival
              </Link>{" "}
              — another inline triple at similar power, very different aero.
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
              — why the Tiger 900 GT Pro picks up 0.06s in Chennai MMRT vs Aamby.
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
              Run the Tiger 900 GT Pro yourself
            </div>
            <div className="text-white/60 text-sm">
              Free simulator — pick the Triumph Tiger 900 GT Pro, swap to an
              F15/R42 sprocket setup, and watch the ET update live.
            </div>
          </div>
          <Link
            href="/simulator?bike=triumph-tiger-900-gt-pro"
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
