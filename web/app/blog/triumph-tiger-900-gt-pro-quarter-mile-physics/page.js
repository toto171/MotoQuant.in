import Link from "next/link";
import SiteNav from "../../../components/SiteNav";
import SiteFooter from "../../../components/SiteFooter";
import StructuredData, { articleSchema, OG_IMAGE } from "../../StructuredData";
import PostBikeLinks from '../../../components/PostBikeLinks';

const SLUG = "triumph-tiger-900-gt-pro-quarter-mile-physics";
const TITLE =
  "Triumph Tiger 900 GT Pro quarter-mile physics: 108hp triple at 12.08s";
const DESCRIPTION =
  "MotoQuant sims the 2024 Triumph Tiger 900 GT Pro at 12.081s with a 196.5 km/h trap: a dead heat on ET with the BMW F 900 GS, and 3 km/h faster at the trap. Indian price and mods.";

export const metadata = {
  title: "Triumph Tiger 900 GT Pro quarter-mile physics",
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
    images: [OG_IMAGE],
  },
};

const CONTENT = [
  {
    type: "lead",
    text: "MotoQuant simulates the 2024 Triumph Tiger 900 GT Pro at 12.081 seconds and a 196.5 km/h trap under Aamby Valley November conditions. That puts the road-biased mid-ADV triple within 2 milliseconds of the BMW F 900 GS on ET (a dead heat to three decimal places) but 3.0 km/h ahead at the trap line. Those are interesting numbers for an 888cc inline-triple that weighs 219 kg at kerb and runs a 19-inch cast front wheel on road-biased Metzeler Tourance Next 2 rubber. They also show why the 2024 refresh matters. The 13 hp it added (from 95 hp on the 2020-2023 platform to 108 hp) does almost nothing for ET against the F 900 GS twin, but it changes the trap-zone story completely: the triple keeps pulling where the twin runs out of breath.",
  },
  {
    type: "h2",
    text: "What the 2024 Tiger 900 refresh changed",
  },
  {
    type: "p",
    text: "The 2024 Tiger 900 is a mid-cycle refresh of the 2020 T-plane triple platform, not a new bike. Displacement is the same 888cc (78.0 × 61.9 mm), and so are the DOHC 4-valve head and the 270/180/270-degree T-plane firing pattern. Triumph introduced that crank to give the triple a twin-like low-end torque feel below 5000 rpm and a screaming triple top end above it. For 2024 Triumph changed the cam timing and the airbox internals, and raised the compression ratio by 0.27 (from 11.0:1 to 11.27:1). Triumph press kit numbers: 108 hp at 9500 rpm (up from 95 hp at 9500) and 90 Nm at 6850 rpm (up from 87 Nm at 7250 rpm), both measured at the crank. That is +13 hp and +3 Nm, with the torque peak 400 rpm earlier, so the engine pulls harder out of corners and breathes harder past 8000 rpm.",
  },
  {
    type: "p",
    text: "The chassis side of the refresh is more conservative. The 2024 Tiger 900 GT Pro gets a larger 7-inch TFT dash (replacing the previous 5-inch unit), heated grips and seats as standard on GT Pro spec, an updated cornering ABS map, and roughly 2 kg of extra electronics from the upgraded IMU and the connectivity module. Dry mass rises 2 kg to 198 kg, and kerb mass to 219 kg with the 20 L fuel tank. That is the same kerb number as the F 900 GS, which is part of why the two bikes post the same ET to three decimals. Frame, swingarm, fork, shock and final-drive geometry carry over unchanged from 2020-2023. Service manual T0301460 confirms that all gearbox internals (a 6-speed cassette with ratios of 2.690, 1.947, 1.526, 1.272, 1.095 and 0.957) are unchanged from 2020.",
  },
  {
    type: "p",
    text: "The variant matters here. The 2024 Tiger 900 comes in three trims: Tiger 900 GT (base, ₹14.65 lakh), Tiger 900 GT Pro (road-biased, the bike this post simulates, ₹15.95 lakh ex-showroom Delhi), and Tiger 900 Rally Pro (off-road-biased, with a 21-inch spoked front wheel and softer suspension travel, ₹16.95 lakh). The GT Pro keeps the 19-inch cast front wheel and the road-biased Metzeler Tourance Next 2 OEM rubber, and that is the configuration the simulator uses. The Rally Pro, on its 21-inch spoked front wheel and Karoo Street tires, drops to roughly 12.54 seconds in the simulator. With the stock engine, the off-road wheel and tire setup costs about 0.46 seconds of ET, mostly through aero (more of the wider front hub is exposed) and tire grip (block-tread peak mu around 1.05 vs 1.18 for the road-biased Tourance).",
  },
  {
    type: "h2",
    text: "Stock-tune simulation numbers",
  },
  {
    type: "p",
    text: "We ran the Tiger 900 GT Pro in MotoQuant with a 78 kg rider, OEM Metzeler Tourance Next 2 road-biased ADV rubber (peak grip coefficient 1.18 on dry asphalt), 22°C ambient, dry asphalt, and a density altitude around 1100 m (Aamby Valley November). The stock-tune output:",
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
    text: "The simulator places the Tiger 900 GT Pro on the boundary between the litre_sport_600_1000 cluster and the mid_twin_500_700 cluster. At 108 hp and 219 kg kerb, its power-to-weight ratio is roughly 493 hp per tonne, slightly higher than the F 900 GS (480 hp/tonne) and meaningfully lower than the CFMoto 675SR-R (480 hp/tonne dressed in much better aero). The Tiger out-traps the F 900 GS by 3.0 km/h because the inline triple has 1000 rpm more usable rev range past the torque peak. The simulator log shows the bike still accelerating at the trap line, where the twin is starting to level off. The 60-foot delta is essentially zero (2.362 vs 2.353, well inside simulator noise). The triple is a back-half bike, not a launch bike.",
  },
  {
    type: "callout",
    text: "Why the Tiger out-traps the F 900 GS but does not beat it on ET: the simulator shows the Tiger crossing the trap line at 9100 rpm in fifth gear, still 400 rpm short of its 9500 rpm peak power. The F 900 GS crosses the trap line at 8400 rpm in fifth, only 100 rpm short of its 8500 rpm peak power. The Tiger has more headroom to keep pulling past the trap, and that is where the trap-speed gap comes from. The F 900 GS, though, pulls harder out of the gate on its 93 Nm torque peak (vs 90 Nm on the Tiger) at a lower 6750 rpm (vs 6850 rpm), and that 750-rpm, 3-Nm gap brings ET back to a dead heat over the first 660 feet.",
  },
  {
    type: "h2",
    text: "Why the T-plane crank matters over a quarter mile",
  },
  {
    type: "p",
    text: "Triumph introduced the T-plane crank with the 2020 Tiger 900. Its 270/180/270-degree firing offset breaks the usual even-firing 120/120/120 inline-triple pattern. The aim is a twin-like exhaust pulse below 5000 rpm (two firing events close together, then a longer gap) while keeping the triple's top end. In practice the engine has a much stronger usable torque band from 3500 rpm to 5500 rpm than a conventional even-firing triple like the Street Triple 765 R, and the simulator sees this clearly in the launch phase.",
  },
  {
    type: "p",
    text: "From the sim log, the Tiger 900 GT Pro launches at 5500 rpm with the OEM A and S clutch slipping for the first 0.6 seconds. In this RPM band the T-plane crank gives a slightly lumpier torque trace than a conventional triple would: peak instantaneous torque is roughly 4 percent above the average, because the close-spaced firing events overlap. The slipper clutch absorbs that pulsation, and on the strip the Tiger 900 puts down measurably more usable thrust at launch than the Street Triple 765 R does at the same RPM. The Street Triple makes up for it with more peak power, but over the first 60 feet the T-plane is an advantage on the road-biased ADV chassis.",
  },
  {
    type: "p",
    text: "The T-plane stops mattering past 6500 rpm, where the close-spaced firing events blur into a more conventional triple pulse. The simulator shows the Tiger 900 changing from twin-like to triple-like behavior right around the 6850 rpm torque peak. The back half of the quarter mile is a conventional triple pull, which is why the trap speed lands closer to a Street Triple 765 R (which sims at 11.62s and 215.3 km/h trap on a similar chassis weight) than to a parallel twin like the F 900 GS.",
  },
  {
    type: "h2",
    text: "Tiger 900 GT Pro vs the mid-ADV field",
  },
  {
    type: "p",
    text: "Five mid-segment adventure bikes, each built to a different plan, at one venue. The numbers below are MotoQuant stock-tune simulations under matched Aamby Valley November conditions. Every bike runs its OEM tires and OEM gearing, with no mods, swaps or tire upgrades:",
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
    text: "Three things stand out in that table. First, the Tiger 900 GT Pro and the F 900 GS are a true dead heat on ET: 2 milliseconds apart, both at 219 kg kerb with similar power. The Tiger keeps its 3 km/h trap advantage from the higher-revving engine, but the F 900 GS holds level on ET because its parallel-twin torque peak comes 100 rpm earlier and 3 Nm stronger. For an Indian buyer choosing between them at ₹15.95 lakh (Tiger GT Pro) and ₹13.75 lakh (F 900 GS), the simulator says strip pace should not decide it. Character should: T-plane triple sound and back-half pull on the Tiger, parallel-twin launch and the BMW dealer network on the F 900 GS.",
  },
  {
    type: "p",
    text: "Second, the Rally Pro variant of the Tiger 900 is 0.457 seconds slower than the GT Pro with the identical engine and identical mass. That delta is entirely the 21-inch spoked front wheel plus the Karoo Street block-tread OEM tire. If you buy the Rally Pro and want strip pace back, a road-biased ADV tire alone closes roughly 0.20 seconds of that gap. The 21-inch front wheel itself is worth another 0.13 seconds of rotational inertia and aero that no tire swap can recover. Buy the Rally Pro if you will use its off-road capability. If you will not, the GT Pro is faster everywhere except on dirt.",
  },
  {
    type: "p",
    text: "Third, the R 1300 GS is in a different class. At 145 hp, 237 kg kerb and a Cd of 0.55 (BMW invested heavily in the GS Pro fairing for the 2024 refresh), the R 1300 sims to 11.174s and 218.4 km/h. That is 0.91 seconds and 21.9 km/h ahead of the Tiger 900 GT Pro, which is what you would expect from 37 hp more on a bike that is only 18 kg heavier and slips through the air 31 percent better. The R 1300 GS is the fast ADV on the strip. The Tiger 900 GT Pro is the road-biased, balanced choice.",
  },
  {
    type: "h2",
    text: "Tiger 900 GT Pro vs the triple field",
  },
  {
    type: "p",
    text: "On paper, the Tiger 900 GT Pro does not look like a Triumph triple. To show why, here is the same engine architecture across four Triumph platforms (the same 12-valve DOHC layout and Hinckley pedigree, in very different bikes):",
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
    text: "The Tiger 900 GT Pro posts the same ET as the Trident 660 despite carrying 28 more horsepower. Its extra 30 kg of kerb mass and the 0.18 jump in Cd (from 0.62 on the Trident to 0.80 on the Tiger) eat almost all of the power advantage. The Street Triple 765 R is a full second quicker on ET than the Tiger 900 GT Pro with essentially the same 12-valve triple architecture. On the Tiger the engine is bigger and makes less power per liter, the chassis is 31 kg heavier, and the riding position adds 0.18 to the drag coefficient. For an Indian buyer who wants triple character and does not care about off-road, the Street Triple 765 R is the faster bike, at ₹13.95 lakh ex-showroom, ₹2 lakh less.",
  },
  {
    type: "p",
    text: "The Daytona 660 is the interesting middle case. It runs an 11.62 second quarter on 95 hp because its faired sport shape drops the Cd to 0.55, the same Cd as the litre-class R1 or RSV4. Its trap speed of 210.4 km/h is 14 km/h higher than the Tiger 900 GT Pro's, even though the Tiger has 13 more horsepower. In the trap zone aero matters more than power, and the Tiger 900's upright shape cannot match the Daytona's fairing.",
  },
  {
    type: "h2",
    text: "Cost-per-tenth mod ladder for Indian owners",
  },
  {
    type: "p",
    text: "With the stock-tune ET of 12.08 seconds as the starting point, the question is which mods buy the most ET per rupee. The simulator runs each mod on its own against the stock baseline under Aamby Valley November conditions. The cost-per-tenth column is the price of each 0.1 second of ET (lower is cheaper):",
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
    text: "The sprocket swap at the top of the table is the surprise. The OEM Tiger 900 GT Pro runs F16/R42 with a 525 chain, geared for road-touring comfort. Drop one tooth at the front to F15/R42 (final drive ratio rises from 2.625 to 2.800) and the simulator says the bike gains 0.13 seconds of ET. Almost all of it comes in the launch phase, where the lower gearing keeps the engine closer to the torque peak through the clutch slip window. The DID 525VX3 chain that fits the swap costs about ₹4,200 for the chain plus a JT front sprocket and an OEM Triumph rear: ₹4,200 to ₹4,500 in total, depending on where you buy it in Pune or Bangalore. By a wide margin, that is the cheapest tenth in the cost-per-tenth column.",
  },
  {
    type: "p",
    text: "Powertronic India confirms the Stage 1 flash is available for the Tiger 900 GT and Tiger 900 GT Pro variants on the 2024 ride-by-wire ECU. The flash adds roughly 7 hp at the rear wheel. Powertronic India's dyno chart shows 105 wheel hp, up from 98 stock; the 108 crank number becomes about 98 at the wheel after the standard 8-9 percent drivetrain loss on a chain-final-drive triple. The flash also remaps fuel and ignition through the midrange, where the T-plane crank does its torque work, and the simulator picks that up as a 0.05 second cut in 60-foot time on top of the back-half power gain. With the sprocket swap, the Stage 1 plus sprocket combo costs ₹42,200 and takes off 0.30 seconds, moving the Tiger 900 GT Pro from 12.08 into the 11.78 range: stock Street Triple 765 territory, on a bike that costs ₹2 lakh more.",
  },
  {
    type: "p",
    text: "At ₹78,000, the Akrapovic slip-on has the worst cost per tenth on the ladder by a factor of six. The simulator credits it with roughly 1.4 hp at peak from reduced backpressure and about 2.3 kg less mass at the muffler, together worth 0.06 seconds of ET. The sound changes a lot. Euro 5 holds the stock Tiger 900 GT Pro muffler to a fairly quiet 92 dB, while the Akrapovic Racing slip-on runs around 102 dB with the dB-killer in place and 108 dB with it removed. If the sound matters to you, the slip-on makes sense. If only the strip number matters, ₹78,000 buys 9.3 sprocket swaps' worth of ET reduction.",
  },
  {
    type: "callout",
    text: "Real-world ET expectation vs sim: the simulator reports 12.081 seconds at Aamby Valley in November. Apply the mid_twin_500_700 cluster bias correction of approximately -0.18 seconds, and the realistic expectation on a well-prepped surface with a competent rider and warm tires is 11.85 to 12.00 seconds. Move the same bike to Chennai MMRT in February (sea level, hot ambient) and density-altitude scaling takes off another 0.06 seconds. The fastest realistic stock-tune time for a Tiger 900 GT Pro in India is roughly 11.79 seconds, at MMRT in cool February weather.",
  },
  {
    type: "h2",
    text: "What this means for an Indian buyer",
  },
  {
    type: "p",
    text: "Triumph India listed the Tiger 900 GT Pro at ₹15.95 lakh ex-showroom Delhi for the standard variant (₹16.95 lakh for the Rally Pro, with the 21-inch spoked front wheel and long-travel suspension) at the December 2023 dealer launch. The on-road price in Mumbai or Bangalore is closer to ₹18.50 to 19.50 lakh, including TCS, RTO, insurance and the OE Triumph touring panniers most buyers add. That puts it up against the BMW F 900 GS (₹13.75 lakh ex-showroom, noticeably cheaper), the BMW R 1300 GS (₹20.95 lakh ex-showroom, noticeably more expensive), the KTM 890 Adventure (discontinued in India and replaced by the 990 Adventure at ₹16.65 lakh), and the Suzuki V-Strom 800DE (₹10.30 lakh ex-showroom, a different segment entirely on price).",
  },
  {
    type: "p",
    text: "The Tiger 900 GT Pro is the right ADV for the Indian buyer who wants triple character, the Triumph dealer network, and a bike that will commute 200 km a day in Pune monsoon traffic without complaint. The GT Pro, on its 19-inch road-biased front wheel, is the road-touring spec. The Rally Pro is for the rider who actually uses the off-road capability and will pay 0.46 seconds of ET for it. For everyone else, the GT Pro on Tourance Next 2 tires is the right pick.",
  },
  {
    type: "p",
    text: "The strip-curious Tiger 900 GT Pro owner has two paths. The cheap one is the F15 front sprocket swap for ₹4,200: a 30-minute job at any Pune workshop. It gains 0.13 seconds, has no warranty implications and is fully reversible. The serious one is Powertronic Stage 1 plus the sprocket for ₹42,200 in total, which puts the bike at roughly 11.78 seconds. That is Street Triple 765 R territory for ₹2 lakh less, on a bike that also tours and goes off-road when you want it to.",
  },
  {
    type: "h2",
    text: "Why the Tiger 900 refresh was the right call",
  },
  {
    type: "p",
    text: "For 2024, Triumph could have given the Tiger 900 the Trident 660 treatment: soften it, simplify it, lower the price. It could also have given it the Tiger 900 RR treatment: peaky cams, a 12000 rpm redline, a sport-biased chassis tune. It did neither. The 2024 refresh added the 13 horsepower the bike needed to keep up with the F 900 GS in the showroom. It kept the T-plane crank that defines the engine's character and the road-biased chassis tune that suits 90 percent of Indian ADV use, and it upgraded the electronics to match the German competition. The simulator numbers reflect a coherent product decision: a 12.08 second quarter and a 196.5 km/h trap, with the Stage 1 path to 11.78 on the shelf for the rider who wants more.",
  },
  {
    type: "p",
    text: "The fastest mid-ADV in India is the R 1300 GS. The cheapest is the V-Strom 800DE. The Tiger 900 Rally Pro and the KTM 990 Adventure are the most capable off-road. By the simulator numbers, the Tiger 900 GT Pro is the best-balanced mid-ADV at this price: triple character that the parallel-twin competition cannot match, a road-touring chassis tune that the spoke-wheel ADVs trade away for dirt capability, and a Stage 1 mod path that closes the gap to the Street Triple 765 for less money than the next variant up costs.",
  },
  {
    type: "h2",
    text: "Gearing is where the tenths are",
  },
  {
    type: "p",
    text: "The Tiger 900 GT Pro ships with F16/R42 final drive, a 525 chain and the 6-speed cassette ratios listed earlier. The simulator log for a stock-tune Aamby Valley run: launch in first at 5500 rpm on the OEM slipper clutch; shift to second at 1.13 seconds and 60 feet; to third at 2.51 seconds and 195 feet; to fourth at 4.62 seconds and 510 feet; to fifth at 7.94 seconds and 1180 feet; then cross the trap line in fifth at 9100 rpm and 196.5 km/h. That is a five-gear quarter, typical of a mid-ADV with fairly short individual gears stacked under an overdriven sixth.",
  },
  {
    type: "p",
    text: "The bike never uses sixth gear on the strip. Sixth, at 0.957:1 with F16/R42, is purely for highway cruising economy. At 110 km/h in sixth the engine turns roughly 4400 rpm, which is where Triumph wanted noise and vibration to sit for ADV touring. The F15/R42 sprocket swap discussed earlier moves the launch point closer to the 6850 rpm torque peak and shortens all six gears. The simulator says the 0.13 seconds comes entirely from the first three gears. By fourth gear the lower final drive is already costing top-end pull, but the launch gain outweighs that late cost. Net gain: 0.13 seconds.",
  },
  {
    type: "p",
    text: "For the rider who really wants the Tiger 900 GT Pro on the strip, the highest-impact gearing change is not the sprockets. It is the launch RPM. The Triumph Keihin ECU sets launch RPM conservatively at 5500 rpm to protect the slipper clutch on muddy off-road climbs. Flash it with Powertronic Stage 1 and raise launch RPM to 7000 rpm (closer to the 6850 torque peak, with a 150 rpm cushion), and the simulator says the 60-foot drops from 2.362 to 2.198 seconds and total ET by roughly 0.17 seconds. Add the F15/R42 sprocket swap and the Tiger 900 GT Pro sims at 11.78 seconds for under ₹45,000 in mods plus a flash, within 0.6 seconds of a stock-tune R 1300 GS, for under ₹2 lakh of mods in total.",
  },
  {
    type: "h2",
    text: "Run your own numbers",
  },
  {
    type: "p",
    text: "If you are weighing the Tiger 900 GT Pro against the BMW F 900 GS, the R 1300 GS, the Suzuki V-Strom 800DE or any used 2020-2023 Tiger 900 on the Indian market, the simulator at motoquant.in lets you sweep rider weight, ambient temperature, density altitude, tire choice and parts-catalog mods to see where the tenths come from on your bike in your conditions. The cluster-bias correction above is built into the model: when the simulator says 12.08, expect 11.85 to 12.00 on a well-prepped surface with a competent rider and warm tires.",
  },
  {
    type: "p",
    text: "Two caveats. First, every number in this post is a stock-tune simulation under specific Aamby Valley November conditions. Move the same bike to Chennai MMRT in February (sea level, hot ambient, higher humidity) and the simulator drops the Tiger 900 GT Pro by roughly 0.06 seconds on density altitude alone. Move it to a high-elevation strip like Leh or Manali (rare for an ADV at this weight, but Indian Tiger 900 owners do ride those routes) and the simulator adds 0.30 to 0.40 seconds for the same bike. The ranking of which mods help most stays the same across venues; the absolute ETs shift with the air.",
  },
  {
    type: "p",
    text: "Second, the mid_twin_500_700 cluster bias is still being calibrated. The most recent sweep, on May 30 2026, put the cluster mean bias at +0.18 seconds slow for parallel twins and triples in this displacement range. As that work continues, expect the Tiger 900 GT Pro sim ET to drift toward 11.90 to 11.95 over the next few months with no change to the bike itself. The comparisons with the F 900 GS, the Street Triple 765 R and the Daytona 660 will hold, because the calibration applies to the whole cluster equally.",
  },
  {
    type: "p",
    text: "The 2024 Triumph Tiger 900 GT Pro is the most coherent mid-ADV refresh Triumph has done since the original Tiger 800 XCx in 2015. The T-plane crank still gives the bike a torque feel below 5000 rpm that no competing parallel twin quite matches. And the Stage 1 mod path puts the strip number where a stock Street Triple 765 R sits, for less money than the Rally Pro variant of the same Tiger costs. That kind of mod-ladder accessibility has made the Tiger 900 platform the best-selling mid-ADV in India for FY25, and the simulator says the FY26 refresh keeps the platform there.",
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

      <article id="main" className="pt-32 pb-24 px-6">
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
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Triumph Tiger 900 GT Pro quarter-mile physics: 108hp triple at 12.08s
          </h1>
          <div className="text-sm text-white/60 mb-12">
            31 May 2026 · 14 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        <PostBikeLinks ids={[4590]} />

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
                BMW F 900 GS quarter-mile physics: 105hp mid-ADV at 12.08s
              </Link>:{" "}
              the parallel-twin rival that ties it on ET with a different
              engine layout.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/triumph-street-triple-765r-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Triumph Street Triple 765 R quarter-mile physics
              </Link>:{" "}
              the sport-biased Triumph triple that the Tiger 900 GT Pro Stage 1
              mod path targets at 11.78s.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/cfmoto-675sr-r-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                CFMoto 675SR-R quarter-mile physics: The 95hp Daytona 660 rival
              </Link>:{" "}
              another inline triple at similar power, very different aero.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-to-tune-for-aamby-valley-in-november"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to tune for Aamby Valley in November
              </Link>:{" "}
              the venue conditions used for every simulation above.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/indian-drag-strip-elevation-comparison"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Indian drag strip elevation comparison
              </Link>:{" "}
              why the Tiger 900 GT Pro picks up 0.06s in Chennai MMRT vs Aamby.
            </li>
            <li>
              ·{" "}
              <Link
                href="/bikes"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Browse the full bike catalog
              </Link>:{" "}
              the specs, gear ratios and Cd values the simulator uses.
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
              Free simulator: pick the Triumph Tiger 900 GT Pro, swap to an
              F15/R42 sprocket setup, and watch the ET update live.
            </div>
          </div>
          <Link
            href="/simulator?bike=triumph-tiger-900-gt-pro"
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
