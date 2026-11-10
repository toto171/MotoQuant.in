import Link from "next/link";
import SiteNav from "../../components/SiteNav";
import SiteFooter from "../../components/SiteFooter";
import PageHero from "../../components/PageHero";

export const metadata = {
  title:
    "MotoQuant blog: Motorcycle drag racing physics & Indian bike breakdowns",
  // ≤160 chars; the per-post pages carry their own long-tail metadata —
  // stuffing the index was a keyword-cannibalisation risk, not a win.
  description:
    "Quarter-mile breakdowns bike by bike, mods ranked by cost per tenth, and tuning for Indian drag strips, all worked out in the MotoQuant simulator.",
  keywords: [
    "motorcycle drag racing blog",
    "motorcycle quarter mile times india",
    "cost per tenth motorcycle mods",
    "indian drag strips",
    "aamby valley tuning",
    "mmrt chennai drag racing",
    "hayabusa vs zx-14r",
    "ktm duke 390 quarter mile",
    "pulsar ns200 vs apache rtr 200",
    "r15 v4 quarter mile time",
    "royal enfield quarter mile",
    "2 stroke expansion chamber",
    "motorcycle physics blog india",
  ],
  alternates: { canonical: "https://motoquant.in/blog" },
};

const POSTS = [
  {
    slug: "motoquant-2-0-is-open-source",
    date: "2026-11-10",
    readTime: "5 min",
    tags: ["release", "open source", "accuracy"],
    title: "MotoQuant 2.0 is open source, including where it is wrong",
    excerpt:
      "MotoQuant 2.0 is free and open source under Apache-2.0, with no accounts and no paid plans. Across 263 matches with published tests it is off by 0.25 s on average. Sport bikes do best; small bikes, singles and two-strokes still come out about a quarter of a second quick or slow on average, and an individual bike can be off by more. What changed, where it is wrong, and how your timeslip makes it better.",
  },
  {
    slug: "pulsar-n125-vs-raider-125-vs-glamour-125-quarter-mile-physics",
    date: "2026-05-31",
    readTime: "13 min",
    tags: [
      "Bajaj",
      "Pulsar N125",
      "TVS Raider 125",
      "Hero Glamour 125",
      "Indian 125cc",
      "commuter shootout",
    ],
    title:
      "Pulsar N125 vs Raider 125 vs Glamour 125: Which 125cc commuter is the fastest?",
    excerpt:
      "MotoQuant simulates the TVS Raider 125 at 20.63s, Pulsar P125 at 20.68s, Pulsar N125 at 20.70s and Glamour 125 at 21.28s on a flat quarter mile. India's most-bought motorcycle class has no published ET data, because buyers in this segment look up fuel economy, not drag times. The Raider 125 wins by 0.07s on a sharper ignition map and 5 kg less mass; the Glamour 125 trails by 0.65s but saves ₹25,000/year in petrol. Top of the cost-per-tenth list: a ₹450 13F sprocket (~0.20s) and a ₹2,100 sport-rubber rear (~0.18s), the cheapest tenth in the MotoQuant catalog on any bike under 200cc.",
  },
  {
    slug: "royal-enfield-interceptor-650-quarter-mile-physics",
    date: "2026-05-31",
    readTime: "13 min",
    tags: [
      "Royal Enfield",
      "Interceptor 650",
      "Mid-twin 500-700",
      "270-degree crank",
      "Indian mid-displacement",
      "physics",
    ],
    title:
      "Royal Enfield Interceptor 650 quarter-mile physics: 14.15s on 47hp",
    excerpt:
      "MotoQuant simulates the Royal Enfield Interceptor 650 at 14.151s and a 155.8 km/h trap at Aamby Valley in November. That is 0.05s slower than the GT 650, which has the same engine, because the upright bars push 0.50 m² of frontal area against the cafe racer's 0.46 m². Top of the cost-per-tenth list: the F15/R46 sprocket swap (₹2,400, 0.16s off the ET) and the Powertronic Stage 1 flash (₹14,500, another 0.21s). The ₹17,000 mod combo puts the bike at a simulated 13.81s, faster than a stock Pulsar NS400Z.",
  },
  {
    slug: "triumph-tiger-900-gt-pro-quarter-mile-physics",
    date: "2026-05-31",
    readTime: "14 min",
    tags: [
      "Triumph",
      "Tiger 900 GT Pro",
      "Mid ADV",
      "T-plane triple",
      "Indian ADV market",
      "physics",
    ],
    title:
      "Triumph Tiger 900 GT Pro quarter-mile physics: 108hp triple at 12.08s",
    excerpt:
      "MotoQuant simulates the 2024 Triumph Tiger 900 GT Pro at 12.081s and a 196.5 km/h trap at Aamby Valley in November. It ties the BMW F 900 GS on ET and traps 3 km/h faster. The 13 hp the 2024 refresh added helps the back half of the quarter, not the launch. A Stage 1 tune with an F15/R42 sprocket (₹42,200 together) brings the bike to 11.78s, Street Triple 765 R territory, for ₹2 lakh less than the next variant up.",
  },
  {
    slug: "yamaha-rd350-quarter-mile-physics",
    date: "2026-05-31",
    readTime: "12 min",
    tags: [
      "Yamaha",
      "RD350",
      "Two-stroke",
      "Rajdoot RD350",
      "India",
      "physics",
    ],
    title: "Yamaha RD350 quarter-mile physics: Why a 1973 2-stroke still runs 14.7s",
    excerpt:
      "MotoQuant simulates the 1973 Yamaha RD350 at 14.707s and a ~145 km/h trap in Aamby Valley November conditions, quicker than a 2026 Pulsar NS200, Hunter 350 or R15 V4. Cycle World clocked the real bike at 14.000s in 1973. The May 31 2026 two-stroke clutch calibration took 347ms off the simulated ET. Also inside: the detune math for the Indian Rajdoot RD350 HT and LT, the simulator's known bias on two-strokes, and the cheapest tenth on the bike (a ₹450 sprocket swap).",
  },
  {
    slug: "bmw-f-900-gs-quarter-mile-physics",
    date: "2026-05-31",
    readTime: "13 min",
    tags: [
      "BMW",
      "F 900 GS",
      "Mid ADV",
      "Indian ADV market",
      "physics",
    ],
    title: "BMW F 900 GS quarter-mile physics: 105hp mid-ADV at 12.08s",
    excerpt:
      "MotoQuant simulates the 2024 BMW F 900 GS at 12.083s and a 193.5 km/h trap at Aamby Valley. It is 0.45s quicker than the F 850 GS it replaces, ties the Triumph Tiger 900 GT Pro on ET, and runs 0.91s behind its R 1300 GS sibling. Losing 14 kg does as much for ET as the extra 10 hp. Top of the cost-per-tenth list: a ₹17,200 switch to road-biased ADV tires (~0.13s).",
  },
  {
    slug: "cfmoto-675sr-r-quarter-mile-physics",
    date: "2026-05-31",
    readTime: "12 min",
    tags: [
      "CFMoto",
      "675SR-R",
      "Inline triple",
      "Indian mid-cc sport",
      "physics",
    ],
    title: "CFMoto 675SR-R quarter-mile physics: The 95hp Daytona 660 rival",
    excerpt:
      "CFMoto's first inline triple is aimed at under ₹6 lakh ex-showroom in India for FY26. MotoQuant simulates the 675SR-R at 11.323s and a 214.4 km/h trap, 5.6 km/h faster at the trap than a Daytona 660 with the same 95 hp, on better aerodynamics. How it compares with the Daytona 660, Street Triple 765 R, MT-09 and its 800NK sibling, plus the mods ranked by cost per tenth, led by the ₹32,000 Powertronic Stage 1 flash.",
  },
  {
    slug: "aprilia-tuono-457-vs-rs-457-quarter-mile-physics",
    date: "2026-05-31",
    readTime: "13 min",
    tags: [
      "Aprilia",
      "Tuono 457",
      "RS 457",
      "Entry naked twin",
      "India",
      "physics",
    ],
    title: "Aprilia Tuono 457 vs RS 457: Same engine, 0.41s different ET",
    excerpt:
      "The Aprilia Tuono 457 and RS 457 share the 47 hp twin, the 175 kg dry mass, the six-speed cassette and the 14F/42R sprockets. MotoQuant still simulates the Tuono at 13.681s and a 162.2 km/h trap, and the RS at 13.275s and 175.9 km/h. The whole 0.41 second gap is aerodynamic: Cd rises from 0.58 on the faired RS to 0.74 on the naked Tuono. Also: Indian prices (₹3.95 lakh vs ₹4.20 lakh), mods ranked by cost per tenth with the ₹3,050 sprocket-swap combo first, and how both compare with the KTM 390 Duke and Pulsar NS400Z.",
  },
  {
    slug: "600cc-supersport-launch-physics-engine-deceleration",
    date: "2026-05-30",
    readTime: "13 min",
    tags: [
      "Physics calibration",
      "600cc supersport",
      "Inline-four",
      "Launch model",
      "Engine deceleration",
    ],
    title: "Why 600cc supersports were running 200ms slow in our sim",
    excerpt:
      "MotoQuant's 600cc inline-four simulations were biased +0.207s slow against Sport Rider and MotoStatz benchmarks. The fix was one number: max_engine_decel_rads2 went from 150 to 600 radians per second squared. Why a 600cc inline-four crankshaft can decelerate four times faster during clutch slip than the old cap allowed, the simulated ETs for the GSX-R 600 K6, R6 13S and CBR600RR 2013 after the fix, and how the K5, R1 and Hayabusa reference baselines held to four decimals through the change.",
  },
  {
    slug: "honda-cbr150r-quarter-mile-physics",
    date: "2026-05-26",
    readTime: "11 min",
    tags: ["Honda", "CBR150R", "K56F", "150cc", "SE Asia", "physics"],
    title: "Honda CBR150R quarter-mile physics: 17hp SE Asia sport single",
    excerpt:
      "MotoQuant simulates the Indonesian Honda CBR150R at 18.42s and a 130.5 km/h trap, 0.08s quicker than a stock R15 V4 with 1hp less. Why 136 kg dry and a 0.62 Cd beat the heavier, faired R15 V4, how the CBR150R compares with the Malaysian RS150R underbone and the Y15ZR V2, and the four mods under ₹15,000 that help grey-market owners in India most.",
  },
  {
    slug: "suzuki-gsx-r600-k8-quarter-mile-physics",
    date: "2026-05-25",
    readTime: "12 min",
    tags: [
      "Suzuki",
      "GSX-R600 K8",
      "600cc supersport",
      "Inline-four",
      "physics",
    ],
    title: "Suzuki GSX-R600 K8 quarter-mile physics: 125hp 600cc supersport",
    excerpt:
      "Sport Rider clocked the 2008 GSX-R600 K8 at 10.91s and a 204.4 km/h trap at sea level. MotoQuant simulates it at 11.04s in Aamby Valley November conditions. Where the 0.13s gap comes from, what the K8 gained over the K6 (12 hp, lower Cd, shorter final drive), and how it compares with the 2008 R6, 2007 CBR600RR and 2009 ZX-6R. Plus four mods priced in India for a used K8, K9 or L0. The F15-to-F16 sprocket swap is unusual, but at Aamby Valley it pays back 0.08s.",
  },
  {
    slug: "indian-drag-strip-elevation-comparison",
    date: "2026-05-25",
    readTime: "12 min",
    tags: [
      "Venues",
      "India",
      "Altitude",
      "Density altitude",
      "MMRT",
      "Aamby Valley",
      "physics",
    ],
    title:
      "Indian drag strips ranked by elevation: What altitude costs over a quarter mile",
    excerpt:
      "Five Indian drag strips in November weather, run on the current engine. A stock Hayabusa Gen 1 loses 0.09 s between Buddh International Circuit and Aamby Valley; an R15 V4 loses 0.36 s. The venue order is the same for both bikes (BIC, MMRT, Kari, Hyderabad, Aamby), and small bikes pay four times as much for thin air.",
  },
  {
    slug: "royal-enfield-hunter-350-quarter-mile-physics",
    date: "2026-05-25",
    readTime: "12 min",
    tags: [
      "Royal Enfield",
      "Hunter 350",
      "J-platform",
      "Indian 350cc",
      "physics",
    ],
    title: "Royal Enfield Hunter 350 quarter-mile time & top speed (India)",
    excerpt:
      "The Hunter 350 is the quickest J-platform bike: MotoQuant simulates it at 16.895s ET, a 127.9 km/h trap and the claimed 114 km/h top speed, 0.84s ahead of the Bullet 350 and 1.025s ahead of the Classic 350. All four bikes share the same 20.2 hp single, so every tenth of the gap comes from mass and aerodynamics, not the engine. Why the lightest RE is also the fastest RE at the strip, plus the three cheapest mods under ₹25,000.",
  },
  {
    slug: "harley-nightster-rh975-quarter-mile-physics",
    date: "2026-05-25",
    readTime: "11 min",
    tags: [
      "Harley-Davidson",
      "Nightster RH975",
      "Revolution Max",
      "cruiser",
      "V-twin",
      "physics",
    ],
    title: "Harley Nightster RH975: Revolution Max quarter-mile physics",
    excerpt:
      "Cycle World clocked the Nightster RH975 at 11.99s, quicker than a Triumph Street Triple 765 R. MotoQuant simulates it at 12.45s, and almost all of the 0.46s gap is in the launch. Why a 90 hp, 212 kg belt-drive Harley runs an 11.x, and why the Sportster S RH1250S posts nearly the same time despite 31 more horsepower.",
  },
  {
    slug: "kawasaki-ninja-h2-sx-quarter-mile-physics",
    date: "2026-05-25",
    readTime: "11 min",
    tags: [
      "Kawasaki",
      "Ninja H2 SX",
      "Supercharged",
      "Sport-Tourer",
      "India gray market",
      "physics",
    ],
    title: "Kawasaki Ninja H2 SX quarter-mile physics: Supercharged tourer",
    excerpt:
      "MotoQuant simulates the 2018-2023 Ninja H2 SX at 10.20 s and a 232.8 km/h trap at Aamby Valley in November: a Hayabusa-class quarter mile from a 238 kg sport-tourer with its hard luggage mounts still bolted on. How the supercharger pays back the touring spec, where the 20 kg of pannier brackets sit, and how a stripped H2 SX runs within 0.06 s of a stock Ninja H2 without spending a rupee on parts. Grey-market price in India: ₹28-32 lakh, against ₹17.7 lakh for a Hayabusa Gen 3.",
  },
  {
    slug: "honda-cb125r-quarter-mile-physics",
    date: "2026-05-25",
    readTime: "11 min",
    tags: ["Honda", "CB125R", "Neo Sports Café", "125cc", "physics"],
    title: "Honda CB125R quarter-mile physics: 14.7hp Neo Sports Café",
    excerpt:
      "MotoQuant simulates the Honda CB125R at 18.61s and a 122 km/h trap, the fastest stock 125cc in the entry class. Why a 14.7 hp single out-traps a KTM 125 Duke by 4.4 km/h, what the ₹1.4 lakh premium over an R15 V4 buys you, and the four cheapest tenths for a small Honda. The JC91 platform has Showa SFF-BP forks and a radial-mount Nissin caliper, class-leading hardware that India never officially got.",
  },
  {
    slug: "husqvarna-svartpilen-250-vs-ktm-duke-250-quarter-mile-physics",
    date: "2026-05-25",
    readTime: "11 min",
    tags: [
      "Husqvarna",
      "Svartpilen 250",
      "KTM",
      "Duke 250",
      "LC4c platform",
      "comparison",
    ],
    title: "Husqvarna Svartpilen 250 vs KTM Duke 250: Quarter-mile physics",
    excerpt:
      "Same engine, same Bajaj plant at Chakan, same Pierer Mobility parts shelf, and still 0.316 seconds apart. MotoQuant simulates the Svartpilen 250 at 14.767s and 149 km/h, and the Duke 250 at 15.083s and 143 km/h. Where the gap comes from (final drive, frontal area, mass), and the cheapest mod that lets a Duke 250 owner match a stock Svartpilen.",
  },
  {
    slug: "royal-enfield-bullet-350-quarter-mile-physics",
    date: "2026-05-25",
    readTime: "11 min",
    tags: [
      "Royal Enfield",
      "Bullet 350",
      "J-platform",
      "Indian 350cc",
      "physics",
    ],
    title: "Royal Enfield Bullet 350 quarter-mile physics: 17.7s on the strip",
    excerpt:
      "Autocar India and BikeWale GPS-timed stock Bullet 350s at 17.8-18.3s; MotoQuant simulates the J-platform bike at 17.735s and a 118 km/h trap. Why 20.2 hp and 195 kg produce a 17-second ET, how the six-speed gearbox works against you at the strip, and what the J-platform siblings (Classic 350, Meteor 350, Hunter 350) inherit from the same engine.",
  },
  {
    slug: "honda-hornet-2-0-vs-pulsar-ns200-quarter-mile",
    date: "2026-05-25",
    readTime: "12 min",
    tags: [
      "Honda",
      "Hornet 2.0",
      "Bajaj",
      "Pulsar NS200",
      "Indian 200cc",
      "comparison",
    ],
    title: "Honda Hornet 2.0 vs Pulsar NS200: Which wins the quarter mile?",
    excerpt:
      "MotoQuant simulates the Honda Hornet 2.0 at ~17.55s and the Pulsar NS200 at ~15.9s in matched Aamby Valley conditions. Seven horsepower and 18 kg separate them. Why the gap comes from engine architecture rather than tuning, and how far mods can take each bike.",
  },
  {
    slug: "bajaj-dominar-400-quarter-mile-physics",
    date: "2026-05-24",
    readTime: "12 min",
    tags: ["Bajaj", "Dominar 400", "Indian 400cc", "sport-tourer", "physics"],
    title: "Bajaj Dominar 400 quarter-mile physics: 373cc single at the strip",
    excerpt:
      "Autocar India clocked the Bajaj Dominar 400 at 14.4-14.9s; MotoQuant simulates it at 14.62s and a 156 km/h trap. Where the 0.9s gap to a stock RC 390 comes from, why 168 kg of mass matters more than the 40hp engine, and four mods under ₹18,000 that close most of the gap for Indian Dominar owners.",
  },
  {
    slug: "yamaha-mt-15-v1-quarter-mile-physics",
    date: "2026-05-24",
    readTime: "10 min",
    tags: ["Yamaha", "MT-15 V1", "Indian 155cc", "naked sport", "physics"],
    title: "Yamaha MT-15 V1 quarter-mile physics: 155cc naked drag",
    excerpt:
      "In the simulator, the Yamaha MT-15 V1 runs 17.05s with a 125.5 km/h trap. It is the 2019 R15 V3 platform without VVA, and it loses about a tenth and a half to its faired sibling, mostly to aero rather than the engine. Where Indian 155cc owners find cheap tenths, and why a ₹3,850 sprocket-and-tire combo beats a ₹38,000 slip-on.",
  },
  {
    slug: "hayabusa-quarter-mile-physics-what-limits-9-6-seconds",
    date: "2026-05-24",
    readTime: "13 min",
    tags: [
      "Suzuki",
      "Hayabusa",
      "hyper sport",
      "drag prep",
      "India",
      "physics",
    ],
    title: "Hayabusa quarter-mile physics: What limits the 9.6",
    excerpt:
      "MotoQuant pins the Hayabusa Gen1 at 10.1100 s, a reference time its automated tests hold to four decimals. A drag-prepped Hayabusa runs 9.5-9.7s. The four to six tenths in between come from traction, geometry, gearing and air, not engine power, with a stage-by-stage cost-per-tenth table priced in India.",
  },
  {
    slug: "aprilia-tuono-660-factory-quarter-mile-physics",
    date: "2026-05-24",
    readTime: "12 min",
    tags: [
      "Aprilia",
      "Tuono 660 Factory",
      "middleweight naked",
      "India",
      "physics",
    ],
    title:
      "Aprilia Tuono 660 Factory quarter-mile physics: 11.02s on the strip",
    excerpt:
      "MotoQuant simulates the Aprilia Tuono 660 Factory at 11.02s and a 215.7 km/h trap, 0.3s ahead of the base Tuono 660. How 5 extra hp, 14 kg less and sharper gearing make up that gap, and why at ₹16.15 lakh the Factory trim is the value pick among middleweight nakeds in India.",
  },
  {
    slug: "triumph-street-triple-765r-quarter-mile-physics",
    date: "2026-05-24",
    readTime: "12 min",
    tags: ["Triumph", "Street Triple 765 R", "middleweight naked", "physics"],
    title:
      "Triumph Street Triple 765 R quarter-mile physics: 118hp triple at the strip",
    excerpt:
      "Cycle World clocked the 2023 Triumph Street Triple 765 R at 10.9s; MotoQuant simulates it at 10.74s and a 213 km/h trap. How a 118hp inline-three beats a 124hp inline-four by 0.44s, why the 765 R is the fastest CBU under ₹12 lakh at the strip, and the ₹2,200 sprocket swap to start with.",
  },
  {
    slug: "kawasaki-z900rs-quarter-mile-physics",
    date: "2026-05-22",
    readTime: "10 min",
    tags: ["Kawasaki", "Z900RS", "retro naked", "physics"],
    title: "Kawasaki Z900RS quarter-mile physics: Retro tax on a 948cc I4",
    excerpt:
      "MCN clocked a stock Kawasaki Z900RS at 11.4s and 199 km/h; MotoQuant simulates it at 11.18s and a 196 km/h trap. Where the 13 hp detune costs you tenths against a Z900, why the 6,500 rpm torque peak makes the launch easier than on most litre nakeds, and the ₹2,800 sprocket swap that buys 0.08 s.",
  },
  {
    slug: "ktm-890-duke-r-quarter-mile-india",
    title: "KTM 890 Duke R quarter mile in India: 11.07s on the grey market",
    date: "2026-05-22",
    readTime: "12 min",
    tags: ["KTM", "890 Duke R", "India grey market", "mid-cc naked", "physics"],
    excerpt:
      "MotoQuant simulates the KTM 890 Duke R at 11.07s and a 202 km/h trap at Aamby Valley, 0.35s quicker than the standard 890 Duke. Why almost every 890 Duke in India is the R variant, where the tenths come from, and the ₹46,400 Tier-1 mods that close the gap to a stock MT-09.",
  },
  {
    slug: "best-mods-for-ktm-rc-390-budget-vs-cost-per-tenth",
    title: "Best mods for KTM RC 390 in India: A cost-per-tenth ladder",
    date: "2026-05-22",
    readTime: "13 min",
    tags: ["KTM", "RC 390", "Duke 390", "cost-per-tenth", "India mods"],
    excerpt:
      "A stock RC 390 runs a 13.5s. Fast Track Racing India ran 11.342s. MotoQuant ranks every mod by rupees per tenth: a ₹950 sprocket takes off 0.20s, a ₹14,500 Powertronic Stage 1 takes off 0.22s, and the full Tier 1-2 build runs a 12.78 for ₹39,100. Where the cheap tenths are, and where each extra rupee starts buying less.",
  },
  {
    slug: "kawasaki-ninja-400-vs-zx-4r-quarter-mile-physics",
    title:
      "Kawasaki Ninja 400 vs ZX-4R: Parallel twin vs inline-four at the strip",
    date: "2026-05-22",
    readTime: "12 min",
    tags: ["Kawasaki", "Ninja 400", "ZX-4R", "Indian 400cc", "comparison"],
    excerpt:
      "MotoQuant simulates the Ninja 400 at ~13.1s and the ZX-4R at 12.681s and a 192.6 km/h trap: same 400cc class, 0.4s apart. Engine layout, redline and a ₹3.7 lakh price gap separate them. Mods for both bikes ranked by cost per tenth in India, and how a modded Ninja 400 gets within 0.10s of a stock ZX-4R for ₹21,000.",
  },
  {
    slug: "suzuki-gsx-s750-vs-ktm-890-duke-quarter-mile",
    title: "Suzuki GSX-S750 vs KTM 890 Duke: Quarter-mile physics",
    date: "2026-05-18",
    readTime: "11 min",
    tags: [
      "Suzuki",
      "GSX-S750",
      "KTM",
      "890 Duke",
      "comparison",
      "mid-cc naked",
    ],
    excerpt:
      "MotoQuant simulates the GSX-S750 at 11.58s and the 890 Duke at 11.42s. The Duke weighs 27 kg less and wins by 0.16s, but the Suzuki's inline-four claws back trap speed and finishes only 3 km/h down. Where each bike gains and loses time, and why both should start with a sprocket swap.",
  },
  {
    slug: "yezdi-roadster-quarter-mile-physics",
    title: "Yezdi Roadster quarter-mile physics: 334cc neo-retro at the strip",
    date: "2026-05-18",
    readTime: "11 min",
    tags: ["Yezdi", "Roadster 334", "BG6 platform", "Indian retro", "physics"],
    excerpt:
      "MotoQuant simulates the Yezdi Roadster 334 at 15.42s and a 138 km/h trap at Aamby Valley. It makes 28.6 hp, weighs 175 kg dry and shares the BG6 platform with the Scrambler, the Adventure 334 and the Jawa 42 Bobber 350. Why the ₹6,500 sprocket swap is the cheapest tenth on the bike, and how the Roadster compares with the Classic 350 and Duke 390.",
  },
  {
    slug: "how-to-tune-for-mmrt-chennai",
    title: "How to tune for MMRT Chennai: Sea-level, humid, hot track",
    date: "2026-05-18",
    readTime: "11 min",
    tags: ["MMRT", "Chennai", "venue", "tuning", "Tamil Nadu"],
    excerpt:
      "MMRT Chennai sits at 78 m with 80% humidity and a 30°C track in November. MotoQuant simulates a stock Hayabusa 0.07 s quicker at MMRT than at Aamby Valley in the same month, with a higher trap speed and the same 60-foot. Tuning math for the venue, a month-by-month ET table, and four adjustments to make before you trailer the bike.",
  },
  {
    slug: "yamaha-xsr900-gp-vs-mt-09-quarter-mile-physics",
    title: "Yamaha XSR900 GP vs MT-09: Where the heritage tax is paid",
    date: "2026-05-18",
    readTime: "11 min",
    tags: ["Yamaha", "XSR900 GP", "MT-09", "CP3 triple", "comparison"],
    excerpt:
      "MotoQuant simulates the Yamaha XSR900 GP at 10.98s and the MT-09 at 10.86s: same 890cc CP3 triple, same 6-speed cassette, 0.12s apart. Where the extra mass sits, why the fairing wins it back at top speed, and the CBU price math in India.",
  },
  {
    slug: "kawasaki-ninja-zx-4r-quarter-mile-physics",
    title: "Kawasaki Ninja ZX-4R quarter-mile physics: 400cc inline-four",
    date: "2026-05-18",
    readTime: "11 min",
    tags: ["Kawasaki", "Ninja ZX-4R", "400cc", "inline-four", "physics"],
    excerpt:
      "The 2024 Kawasaki Ninja ZX-4R runs 12.681s with a 192.6 km/h trap in MotoQuant. Why a 76 hp 400cc inline-four runs a 12.6 when every other 400-class bike runs a 13.5, plus three mods under ₹30,000 that close the gap to the ZX-4RR.",
  },
  {
    slug: "yamaha-mt-125-xsr125-platform-physics",
    title: "Yamaha MT-125 vs XSR125: Same engine, 0.10s apart at the strip",
    date: "2026-05-18",
    readTime: "10 min",
    tags: ["Yamaha", "MT-125", "XSR125", "A1 licence", "platform physics"],
    excerpt:
      "Same engine, same gearbox, same final drive, 0.10s apart: MotoQuant simulates the MT-125 at 19.123s and the XSR125 at 19.222s. Where the tenth goes, why the retro styling costs it in frontal area, and why the YZF-R125 beats both.",
  },
  {
    slug: "cfmoto-800nk-quarter-mile-physics",
    title: "CFMoto 800NK quarter-mile physics: A KTM 790 Duke in disguise",
    date: "2026-05-18",
    readTime: "11 min",
    tags: ["CFMoto", "800NK", "LC8c", "Indian mid-cc", "physics"],
    excerpt:
      "MotoQuant simulates the CFMoto 800NK at 11.386s and a 203.2 km/h trap. With the KTM-derived LC8c parallel twin and a ₹9-12 lakh price in India, it is the cheapest LC8c-engined bike on the market. Where the tenths come from, and why a 95 hp parallel twin runs an 11.4.",
  },
  {
    slug: "ktm-duke-390-vs-rc-390-quarter-mile-physics",
    title: "KTM Duke 390 vs RC 390: Quarter-mile physics at Aamby Valley",
    date: "2026-05-18",
    readTime: "12 min",
    tags: ["KTM", "Duke 390", "RC 390", "Indian 400cc", "comparison"],
    excerpt:
      "Same engine, two tenths apart, almost all of it aerodynamic. At Aamby Valley, MotoQuant simulates the RC 390 at ~13.5s and a 166 km/h trap, and the Duke 390 at ~13.7s and 162 km/h. Plus four mods under ₹25,000 ranked by cost per tenth, and a look at the Fast Track Racing 11.342s record.",
  },
  {
    slug: "ktm-duke-390-quarter-mile-stock-to-11s",
    title: "KTM Duke 390 quarter mile: From 13.3s stock to an 11.342s record",
    date: "2026-06-01",
    readTime: "13 min",
    tags: ["KTM", "Duke 390", "Indian 400cc", "drag mods", "cost per tenth"],
    excerpt:
      "MotoQuant simulates the stock 2022 Duke 390 at 13.30s and a 162 km/h trap at Aamby Valley. Fast Track Racing India ran 11.342s with the same engine. Those two seconds broken down mod by mod at Indian retail prices, plus a ₹49k build that puts the bike under 12.6s.",
  },
  {
    slug: "pulsar-ns400z-quarter-mile-physics",
    title: "Pulsar NS400Z quarter-mile physics (and why an RC 390 still wins)",
    date: "2026-05-18",
    readTime: "12 min",
    tags: ["Bajaj", "Pulsar NS400Z", "KTM RC 390", "Indian 400cc", "physics"],
    excerpt:
      "A stock RC 390 still beats the Pulsar NS400Z by 0.3s. MotoQuant simulates the NS400Z at ~13.8s and a 158 km/h trap at Aamby Valley, and the reasons are the 23 kg, the gearing and the Cd that the press release glossed over. Plus three mods under ₹22,000 ranked by cost per tenth.",
  },
  {
    slug: "re-continental-gt-650-quarter-mile-physics",
    title: "Royal Enfield Continental GT 650 quarter-mile physics",
    date: "2026-05-18",
    readTime: "10 min",
    tags: ["Royal Enfield", "Continental GT 650", "Indian 650cc", "cafe racer"],
    excerpt:
      "In MotoQuant, the RE Continental GT 650 runs ~14.1s with a 158 km/h trap. Why the 47 hp / 52 Nm air/oil-cooled twin is rev-limited rather than power-limited, and the ₹7,800 sprocket-and-tire combo that closes most of the gap.",
  },
  {
    slug: "pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics",
    title: "Pulsar NS200 vs Apache RTR 200 4V: Which wins the quarter mile?",
    date: "2026-05-18",
    readTime: "11 min",
    tags: [
      "Bajaj",
      "Pulsar NS200",
      "TVS",
      "Apache RTR 200 4V",
      "Indian 200cc",
      "comparison",
    ],
    excerpt:
      "MotoQuant simulates the NS200 at ~15.9s and the Apache RTR 200 4V at ~16.4s in matched Aamby Valley conditions. A spec-by-spec comparison, plus the three best mods per tenth under ₹15,000 for each bike.",
  },
  {
    slug: "how-a-2-stroke-expansion-chamber-actually-works",
    title: "How a 2-stroke expansion chamber actually works",
    date: "2026-05-08",
    readTime: "11 min",
    tags: ["2-stroke", "expansion chamber", "physics", "RX100", "RD350"],
    excerpt:
      "A pressure wave at 500 m/s, a tuned peak about 1,500 rpm wide, and a +0.494 s simulator bias on 2-stroke bikes. Why the pipe is the engine on an RX100, RD350 or RGV250, and what that means for cost per tenth at an Indian drag strip.",
  },
  {
    slug: "hayabusa-vs-zx-14r-which-is-faster",
    title: "Hayabusa vs ZX-14R: Which is faster off the line?",
    date: "2026-05-08",
    readTime: "11 min",
    tags: [
      "Suzuki",
      "Hayabusa",
      "Kawasaki",
      "ZX-14R",
      "hyper sport",
      "comparison",
    ],
    excerpt:
      "MotoQuant simulates a stock Hayabusa Gen1 at 10.218 s and a ZX-14R 2012 at 9.872 s at Aamby Valley in November. The two flagship hyper-bikes compared spec by spec: where each one wins, and why.",
  },
  {
    slug: "hero-xtreme-200s-4v-quarter-mile-physics",
    title: "Hero Xtreme 200S 4V quarter-mile physics: 200cc commuter drag",
    date: "2026-05-08",
    readTime: "9 min",
    tags: ["Hero", "Xtreme 200S 4V", "Indian 200cc", "commuter sport"],
    excerpt:
      "The Hero Xtreme 200S 4V runs 17.40s with a 125 km/h trap in the simulator. Why the 19.1 hp / 17.35 Nm 4-valve oil-cooled single is limited by gearing rather than power, and the two ₹3,600 mods that close most of the gap.",
  },
  {
    slug: "ktm-1390-super-duke-r-evo-quarter-mile-physics",
    title: "KTM 1390 Super Duke R EVO quarter-mile physics breakdown",
    date: "2026-05-08",
    readTime: "9 min",
    tags: ["KTM", "1390 Super Duke R", "physics", "litre naked"],
    excerpt:
      "MCN clocked stock test bikes of the KTM 1390 Super Duke R EVO at 9.95s; MotoQuant simulates the 2024 bike at 10.225s and a 237 km/h trap. What makes up the 0.275s gap, and what limits the bike at the strip.",
  },
  {
    slug: "how-the-motoquant-physics-engine-works",
    title: "How the MotoQuant physics engine works",
    date: "2026-04-27",
    readTime: "14 min",
    tags: ["physics", "engine", "validation", "methodology"],
    excerpt:
      "A tour of the 15 sub-models in the RK4 physics engine: engine torque curves, tyre grip and temperature, clutch slip, weight transfer. What we simulate, what we check it against, and what the remaining error means.",
  },
  {
    slug: "the-physics-of-a-perfect-launch",
    title: "The physics of a perfect launch",
    date: "2026-04-24",
    readTime: "8 min",
    tags: ["physics", "launch control", "clutch"],
    excerpt:
      "Clutch engagement rpm, tire slip ratio and weight transfer work together in the first 0.4 seconds, and getting any one of them wrong costs you tenths. The post works through the math for each.",
  },
  {
    slug: "why-your-r15-wont-hit-14s",
    title: "Why your R15 won't hit 14s (and what will actually help)",
    date: "2026-04-24",
    readTime: "10 min",
    tags: ["small-cc", "Yamaha R15", "Indian bikes", "tuning"],
    excerpt:
      "The Yamaha YZF-R15 V3 should run ~14.5s based on factory power. Most stock bikes run 15.5–16s. The gap comes from gearing, clutch slip and traction, not engine power, and the post accounts for it second by second.",
  },
  {
    slug: "how-to-tune-for-aamby-valley-in-november",
    title: "How to tune for Aamby Valley in November",
    date: "2026-04-24",
    readTime: "6 min",
    tags: ["venue", "Aamby Valley", "weather", "conditions"],
    excerpt:
      "November at Aamby Valley means 679 m of elevation, about 22°C and a density altitude near 1,100 m on an asphalt strip. What that costs each class of bike, and how to tune for it.",
  },
];

/* ── Featured + rubric grouping ────────────────────────────────────────────
   The flagship methodology post anchors the index; every other card is
   grouped under a rubric inferred from its slug, so there is no per-post
   metadata to maintain — new posts land in the right section automatically. */
const FEATURED_SLUG = "how-the-motoquant-physics-engine-works";

const RUBRICS = [
  { id: "physics", title: "How it works" },
  { id: "guides", title: "Guides and drag-strip tuning" },
  { id: "comparisons", title: "Bike comparisons" },
  { id: "breakdowns", title: "Bike-by-bike breakdowns" },
];

function rubricFor(slug) {
  if (
    slug.includes("physics-engine-works") ||
    slug.includes("expansion-chamber") ||
    slug.includes("physics-of-a-perfect-launch") ||
    slug.includes("launch-physics-engine-deceleration")
  ) {
    return "physics";
  }
  if (
    slug.startsWith("how-to-") ||
    slug.includes("best-mods") ||
    slug.includes("wont-hit-14s") ||
    slug.includes("elevation-comparison") ||
    slug.includes("stock-to-11s")
  ) {
    return "guides";
  }
  if (slug.includes("-vs-")) return "comparisons";
  return "breakdowns";
}

function fmtDate(d) {
  return new Date(d).toLocaleDateString("en-IN", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function FeaturedPostCard({ post }) {
  return (
    <Link href={`/blog/${post.slug}`} className="block group mb-12">
      <article className="card card-hover card-pad">
        <p className="eyebrow mb-2">Start here</p>
        <h2 className="font-display font-semibold text-2xl md:text-3xl text-white leading-snug mb-3 group-hover:text-accent transition-colors">
          {post.title}
        </h2>
        <p className="text-white/70 text-base leading-relaxed mb-4 line-clamp-3">
          {post.excerpt}
        </p>
        <p className="text-sm text-white/60">
          {fmtDate(post.date)} · {post.readTime} read
        </p>
      </article>
    </Link>
  );
}

function PostCard({ post }) {
  return (
    <Link href={`/blog/${post.slug}`} className="block group h-full">
      <article className="card card-hover h-full card-pad">
        <h3 className="font-display font-semibold text-lg text-white mb-2 group-hover:text-accent transition-colors leading-snug">
          {post.title}
        </h3>
        <p className="text-white/70 text-sm leading-relaxed mb-3 line-clamp-3">
          {post.excerpt}
        </p>
        <p className="text-sm text-white/60">
          {fmtDate(post.date)} · {post.readTime} read
        </p>
      </article>
    </Link>
  );
}

export default function BlogIndexPage() {
  const featured = POSTS.find((p) => p.slug === FEATURED_SLUG) ?? POSTS[0];
  const byDateDesc = (a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0);
  const grouped = RUBRICS.map((rubric) => ({
    ...rubric,
    posts: POSTS.filter(
      (p) => p.slug !== featured.slug && rubricFor(p.slug) === rubric.id
    ).sort(byDateDesc),
  })).filter((rubric) => rubric.posts.length > 0);

  return (
    <div className="min-h-screen bg-asphalt-0 text-white">
      <SiteNav />

      <PageHero
        title="Blog"
        sub={`${POSTS.length} articles on how motorcycles launch, how to tune for each drag strip, and what every bike should run in the quarter mile.`}
      />

      <main id="main" className="pb-24 px-4 sm:px-6">
        <div className="max-w-5xl mx-auto">
          <p className="mb-8 max-w-3xl text-sm text-white/60">
            Simulated times in each post come from the engine as it stood on the post&apos;s date. The engine has been re-tuned since, so the simulator today can differ by a few tenths, and accuracy figures quoted with an older date are history. Posts marked &ldquo;Updated 10 November 2026&rdquo; were re-run on the current engine.
          </p>
          <FeaturedPostCard post={featured} />

          {grouped.map((rubric) => (
            <section key={rubric.id} className="mb-14 last:mb-0">
              <h2 className="font-display font-bold text-xl md:text-2xl tracking-tight text-white mb-5">
                {rubric.title}
              </h2>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
                {rubric.posts.map((post) => (
                  <PostCard key={post.slug} post={post} />
                ))}
              </div>
            </section>
          ))}
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
