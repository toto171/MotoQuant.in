import { Suspense } from "react";
import Link from "next/link";
import SiteNav from "../../components/SiteNav";
import SiteFooter from "../../components/SiteFooter";
import PageHero from "../../components/PageHero";
import { Stagger, StaggerItem } from "../../components/Reveal";
import EndOfBlogIndexCta from "./EndOfBlogIndexCta";

export const metadata = {
  title:
    "MotoQuant Blog — Motorcycle Drag Racing Physics & Indian Bike Breakdowns",
  // ≤160 chars; the per-post pages carry their own long-tail metadata —
  // stuffing the index was a keyword-cannibalisation risk, not a win.
  description:
    "Physics-first quarter-mile breakdowns, cost-per-tenth mod guides, and Indian venue tuning from the MotoQuant simulation engine.",
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
      "Pulsar N125 vs Raider 125 vs Glamour 125: Which 125cc Commuter Is the Fastest?",
    excerpt:
      "MotoQuant sims the TVS Raider 125 at 20.63s, Pulsar P125 at 20.68s, Pulsar N125 at 20.70s, and Glamour 125 at 21.28s on a flat quarter mile. India's most-bought motorcycle class has zero published ET data because the segment buyer searches for fuel economy, not drag times. The Raider 125 wins by 0.07s on a sharper ignition map and 5 kg less mass; the Glamour 125 trails by 0.65s but saves ₹25,000/year in petrol. Cost-per-tenth ladder topped by a ₹450 13F sprocket (~0.20s) and a ₹2,100 sport-rubber rear (~0.18s) — the cheapest tenth in the entire MotoQuant catalog on any bike under 200cc.",
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
      "Royal Enfield Interceptor 650 Quarter-Mile Physics: 14.15s on 47hp",
    excerpt:
      "MotoQuant sims the Royal Enfield Interceptor 650 at 14.151s and 155.8 km/h trap under Aamby Valley November — 0.05s slower than the GT 650 sibling on identical engine because upright bars push 0.50 m² of frontal area instead of the cafe-racer's 0.46 m². Cost-per-tenth ladder topped by the F15/R46 sprocket swap (₹2,400, drops ET 0.16s) and the Powertronic Stage 1 flash (₹14,500, drops another 0.21s). ₹17,000 mod combo lands the bike at a 13.81s sim ET — faster than a stock Pulsar NS400Z.",
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
      "Triumph Tiger 900 GT Pro Quarter-Mile Physics: 108hp Triple at 12.08s",
    excerpt:
      "MotoQuant sims the 2024 Triumph Tiger 900 GT Pro at 12.081s and 196.5 km/h trap under Aamby Valley November — dead-heat on ET with the BMW F 900 GS, 3 km/h faster at the trap. The +13 hp the 2024 refresh added moves the back half of the quarter, not the launch. Stage 1 + F15/R42 sprocket combo (₹42,200) lands the bike at 11.78s — Street Triple 765 R territory for ₹2 lakh less than the next variant up.",
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
    title: "Yamaha RD350 Quarter-Mile Physics: Why a 1973 2-Stroke Still Runs 14.7s",
    excerpt:
      "MotoQuant sims the 1973 Yamaha RD350 at 14.707s and ~145 km/h trap under Aamby Valley November conditions — quicker than a 2026 Pulsar NS200, Hunter 350, or R15 V4. Cycle World clocked the real bike at 14.000s in 1973. The May 31 2026 two-stroke clutch calibration shaved 347ms off the sim ET. Includes the Indian Rajdoot RD350 HT / LT detune math, the cluster-bias honest framing, and the cheapest mod tenth on the bike (a ₹450 sprocket swap).",
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
    title: "BMW F 900 GS Quarter-Mile Physics: 105hp Mid-ADV at 12.08s",
    excerpt:
      "MotoQuant sims the 2024 BMW F 900 GS at 12.083s and 193.5 km/h trap under Aamby Valley conditions — 0.45s quicker than the F 850 GS it replaces, dead-heat on ET with the Triumph Tiger 900 GT Pro, 0.91s behind the R 1300 GS sibling. The 14 kg weight reduction is doing as much for ET as the +10 hp engine bump. Cost-per-tenth ladder topped by a ₹17,200 road-biased ADV tire swap (~0.13s).",
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
    title: "CFMoto 675SR-R Quarter-Mile Physics: The 95hp Daytona 660 Rival",
    excerpt:
      "MotoQuant sims the CFMoto 675SR-R at 11.323s and 214.4 km/h trap — 5.6 km/h faster at the trap than a Daytona 660 with the same 95 hp, on better aerodynamics. CFMoto first inline triple targets sub-₹6 lakh ex-showroom in India for FY26. Physics breakdown vs Daytona 660 / Street Triple 765 R / MT-09 / 800NK sibling, plus the cost-per-tenth mod ladder topped by the ₹32,000 Powertronic Stage 1 flash.",
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
    title: "Aprilia Tuono 457 vs RS 457: Same Engine, 0.41s Different ET",
    excerpt:
      "MotoQuant sims the Aprilia Tuono 457 at 13.681s and 162.2 km/h trap, and the RS 457 at 13.275s / 175.9 km/h. Same 47 hp twin, same 175 kg dry, same six-speed cassette, same 14F/42R sprockets. The 0.41 second gap is entirely aerodynamic — Cd climbs from 0.58 on the faired RS to 0.74 on the naked Tuono. Indian price math (₹3.95 lakh vs ₹4.20 lakh), cost-per-tenth mod ladder topped by the ₹3,050 sprocket-swap combo, and the comparison against KTM 390 Duke + Pulsar NS400Z.",
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
    title: "Why 600cc Supersports Were Running 200ms Slow in Our Sim",
    excerpt:
      "MotoQuant's 600cc inline-four sims were biased +0.207s slow against Sport Rider and MotoStatz benchmarks. The fix was one number: max_engine_decel_rads2 lifted from 150 to 600 radians per second squared. Why a 600cc inline-four crankshaft physically wants to decelerate four times faster during clutch slip than the old cap allowed, what the GSX-R 600 K6 / R6 13S / CBR600RR 2013 sim ETs look like after the fix, and how K5/R1/Hayabusa reference baselines stayed pinned to four decimals through the change.",
  },
  {
    slug: "honda-cbr150r-quarter-mile-physics",
    date: "2026-05-26",
    readTime: "11 min",
    tags: ["Honda", "CBR150R", "K56F", "150cc", "SE Asia", "physics"],
    title: "Honda CBR150R Quarter-Mile Physics: 17hp SE Asia Sport Single",
    excerpt:
      "MotoQuant simulates the Indonesian Honda CBR150R at 18.42s and 130.5 km/h trap — quicker than a stock R15 V4 by 0.08s on a 1hp deficit. Why the 136 kg dry mass and 0.62 Cd beat the heavier R15 V4 fairing, how the CBR150R compares to the Malaysian RS150R underbone and the Y15ZR V2, and the four mods under ₹15,000 that move the needle for India grey-market owners.",
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
    title: "Suzuki GSX-R600 K8 Quarter-Mile Physics: 125hp 600cc Supersport",
    excerpt:
      "Sport Rider clocked the 2008 GSX-R600 K8 at 10.91s and 204.4 km/h trap at sea level. MotoQuant simulates it at 11.04s under Aamby Valley November conditions. Where the 0.13s gap lives, what the K8 actually gained over the K6 (12 hp, lower Cd, shorter final drive), and a head-to-head against the 2008 R6 + 2007 CBR600RR + 2009 ZX-6R. Plus four India-priced mods that move the needle on a used K8/K9/L0 — the F15-to-F16 sprocket swap is unusual but pays back 0.08s at Aamby Valley specifically.",
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
      "Indian Drag Strips Ranked by Elevation: How Altitude Flips Quarter-Mile Order",
    excerpt:
      "MMRT at 78 m runs a stock Hayabusa Gen 1 at 10.262s — 0.21s quicker than the same bike at Aamby Valley (679 m), but 4.6 km/h slower at the trap. The order flips entirely for a 200cc commuter, where MMRT wins on every metric. MotoQuant sweeps the same physics across all five active Indian strips (MMRT, BIC, Kari, Hyderabad, Aamby Valley) and shows which bike class wants which venue. Drag-prepped turbo Hayabusas want Aamby. Stock R15 V4s want MMRT. The crossover sits between 80 and 120 hp.",
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
    title: "Royal Enfield Hunter 350 Quarter-Mile Time & Top Speed (India)",
    excerpt:
      "MotoQuant simulates the Hunter 350 at 16.895s ET, a 127.9 km/h trap, and the claimed 114 km/h top speed — the quickest J-platform sibling, 0.84s ahead of the Bullet 350 and 1.025s ahead of the Classic 350. All four bikes share the same 20.2 hp single. Every tenth of the gap is mass and aerodynamics, not engine. Physics breakdown of why the lightest RE is also the fastest RE at the strip, plus the three cheapest mods under ₹25,000.",
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
    title: "Harley Nightster RH975: Revolution Max Quarter-Mile Physics",
    excerpt:
      "Cycle World clocked the Nightster RH975 at 11.99s — quicker than a Triumph Street Triple 765 R. MotoQuant simulates it at 12.45s; the 0.46s gap is almost entirely launch phase. Physics breakdown of why a 90 hp 212 kg belt-drive Harley runs an 11.x, and why the Sportster S RH1250S posts nearly the same time despite 31 more horsepower.",
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
    title: "Kawasaki Ninja H2 SX Quarter-Mile Physics: Supercharged Tourer",
    excerpt:
      "MotoQuant sims the 2018-2023 Ninja H2 SX at 10.222s and 250.8 km/h trap — a Hayabusa-class quarter-mile from a 238 kg sport-tourer with hard luggage mounts still bolted on. Why the supercharger pays back the touring spec, where the 20 kg of pannier brackets actually live, and how a stripped H2 SX runs within a tenth of a stock Ninja H2 for zero rupees of parts spend. India gray-market context: ₹28-32 lakh vs ₹17.7 lakh Hayabusa Gen 3.",
  },
  {
    slug: "honda-cb125r-quarter-mile-physics",
    date: "2026-05-25",
    readTime: "11 min",
    tags: ["Honda", "CB125R", "Neo Sports Café", "125cc", "physics"],
    title: "Honda CB125R Quarter-Mile Physics: 14.7hp Neo Sports Café",
    excerpt:
      "MotoQuant simulates the Honda CB125R at 18.61s and 122 km/h trap — the fastest stock 125cc in the entry cluster. Why a 14.7 hp single out-traps a KTM 125 Duke by 4.4 km/h, where the ₹1.4 lakh price premium over an R15 V4 actually buys you, and the four cheapest tenths for the small-cc Honda owner. JC91 platform, Showa SFF-BP forks, radial-mount Nissin caliper — class-leading hardware that India never officially got.",
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
    title: "Husqvarna Svartpilen 250 vs KTM Duke 250: Quarter-Mile Physics",
    excerpt:
      "MotoQuant sims the Svartpilen 250 at 14.767s / 149 km/h and the Duke 250 at 15.083s / 143 km/h. Same engine, same Bajaj Chakan plant, same Pierer Mobility parts shelf — and 0.316 seconds separates them at the strip. Physics breakdown of where the gap lives (final drive, frontal area, mass), why the Husky surprises everyone, and the cheapest mod that lets a Duke 250 owner match a stock Svartpilen.",
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
    title: "Royal Enfield Bullet 350 Quarter-Mile Physics: 17.7s on the Strip",
    excerpt:
      "MotoQuant simulates the Bullet 350 J-platform at 17.735s and 118 km/h trap. Autocar India and BikeWale GPS-timed 17.8-18.3s on stock bikes. Why 20.2 hp and 195 kg produce a 17-second ET, how the six-speed gearbox works against you at the strip, and what the J-platform siblings (Classic 350, Meteor 350, Hunter 350) inherit from the same engine.",
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
    title: "Honda Hornet 2.0 vs Pulsar NS200: Which Wins the Quarter Mile?",
    excerpt:
      "MotoQuant simulates the Honda Hornet 2.0 at ~17.55s and the Pulsar NS200 at ~15.9s under matched Aamby Valley conditions. Seven horsepower and 18 kg separate them — physics-first breakdown of why the gap is engine architecture, not tuning, plus the mod ceiling on each platform.",
  },
  {
    slug: "bajaj-dominar-400-quarter-mile-physics",
    date: "2026-05-24",
    readTime: "12 min",
    tags: ["Bajaj", "Dominar 400", "Indian 400cc", "sport-tourer", "physics"],
    title: "Bajaj Dominar 400 Quarter-Mile Physics: 373cc Single at the Strip",
    excerpt:
      "MotoQuant simulates the Bajaj Dominar 400 at 14.62s and 156 km/h trap. Autocar India clocked 14.4-14.9s on the same bike. Where the 0.9s gap to a stock RC 390 lives, why 168 kg of mass costs more than the 40hp engine, and four mods under ₹18,000 that close most of the gap for Indian Dominar owners.",
  },
  {
    slug: "yamaha-mt-15-v1-quarter-mile-physics",
    date: "2026-05-24",
    readTime: "10 min",
    tags: ["Yamaha", "MT-15 V1", "Indian 155cc", "naked sport", "physics"],
    title: "Yamaha MT-15 V1 Quarter-Mile Physics: 155cc Naked Drag",
    excerpt:
      "MotoQuant simulates the Yamaha MT-15 V1 at 17.05s and 125.5 km/h trap. The 2019 R15 V3 platform without VVA loses about a tenth and a half to its faired sibling — most of it aero, not engine. Where the cheap tenths actually live for Indian 155cc owners, and why a ₹3,850 sprocket-and-tire combo beats a ₹38,000 slip-on.",
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
    title: "Hayabusa Quarter-Mile Physics: What Limits the 9.6",
    excerpt:
      "MotoQuant locks the Hayabusa Gen1 at 10.4712s — a reference baseline preserved across every physics commit since April 2024. A drag-prepped Hayabusa runs 9.5-9.7s. The seven tenths between are not engine power. They are traction, geometry, gearing, and air — broken down with a stage-by-stage Indian cost-per-tenth table.",
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
      "Aprilia Tuono 660 Factory Quarter-Mile Physics: 11.02s on the Strip",
    excerpt:
      "MotoQuant simulates the Aprilia Tuono 660 Factory at 11.02s and 215.7 km/h trap. 5 extra hp, 14 kg less, sharper gearing — where the 0.3s gap over the base Tuono 660 actually lives, and why the Factory trim is the value pick of the Indian middleweight-naked segment at ₹16.15 lakh.",
  },
  {
    slug: "triumph-street-triple-765r-quarter-mile-physics",
    date: "2026-05-24",
    readTime: "12 min",
    tags: ["Triumph", "Street Triple 765 R", "middleweight naked", "physics"],
    title:
      "Triumph Street Triple 765 R Quarter-Mile Physics: 118hp Triple at the Strip",
    excerpt:
      "MotoQuant simulates the Triumph Street Triple 765 R at 10.74s and 213 km/h trap. Cycle World clocked the 2023 model at 10.9s. How a 118hp inline-three beats a 124hp inline-four by 0.44s, why the 765 R is the fastest CBU under ₹12 lakh at the strip, and the ₹2,200 sprocket swap that starts the upgrade ladder.",
  },
  {
    slug: "kawasaki-z900rs-quarter-mile-physics",
    date: "2026-05-22",
    readTime: "10 min",
    tags: ["Kawasaki", "Z900RS", "retro naked", "physics"],
    title: "Kawasaki Z900RS Quarter-Mile Physics: Retro Tax on a 948cc I4",
    excerpt:
      "MotoQuant simulates the Kawasaki Z900RS at 11.18s and 196 km/h trap. MCN clocked 11.4s and 199 km/h on the stock bike. Where the 13 hp detune actually costs you tenths versus a Z900, why the 6,500 rpm torque peak makes the launch easier than most litre nakeds, and the ₹2,800 sprocket swap that buys 0.08 s.",
  },
  {
    slug: "ktm-890-duke-r-quarter-mile-india",
    title: "KTM 890 Duke R Quarter-Mile in India: 11.07s on the Grey Market",
    date: "2026-05-22",
    readTime: "12 min",
    tags: ["KTM", "890 Duke R", "India grey market", "mid-cc naked", "physics"],
    excerpt:
      "MotoQuant simulates the KTM 890 Duke R at 11.07s and 202 km/h trap at Aamby Valley — 0.35s quicker than the standard 890 Duke. Why almost every 890 Duke in India is actually the R variant, where the tenths come from, and the ₹46,400 Tier-1 stack that closes the gap to a stock MT-09.",
  },
  {
    slug: "best-mods-for-ktm-rc-390-budget-vs-cost-per-tenth",
    title: "Best Mods for KTM RC 390 in India: A Cost-Per-Tenth Ladder",
    date: "2026-05-22",
    readTime: "13 min",
    tags: ["KTM", "RC 390", "Duke 390", "cost-per-tenth", "India mods"],
    excerpt:
      "Stock RC 390 runs a 13.5s. Fast Track Racing India ran 11.342s. MotoQuant ranks every mod by ₹/tenth: ₹950 sprocket drops 0.20s, ₹14,500 Powertronic Stage 1 drops 0.22s, full Tier 1-2 build runs a 12.78 for ₹39,100. Where the cheap tenths live and where diminishing returns kick in.",
  },
  {
    slug: "kawasaki-ninja-400-vs-zx-4r-quarter-mile-physics",
    title:
      "Kawasaki Ninja 400 vs ZX-4R: Parallel Twin vs Inline-Four at the Strip",
    date: "2026-05-22",
    readTime: "12 min",
    tags: ["Kawasaki", "Ninja 400", "ZX-4R", "Indian 400cc", "comparison"],
    excerpt:
      "MotoQuant simulates the Ninja 400 at ~13.1s and the ZX-4R at 12.681s and 192.6 km/h trap — same 400cc class, 0.4s apart. Architecture, redline, and the ₹3.7 lakh price gap explain everything. India cost-per-tenth mods for both bikes, and a modded Ninja 400 gets within 0.10s of a stock ZX-4R for ₹21,000.",
  },
  {
    slug: "suzuki-gsx-s750-vs-ktm-890-duke-quarter-mile",
    title: "Suzuki GSX-S750 vs KTM 890 Duke: Quarter-Mile Physics",
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
      "MotoQuant simulates the GSX-S750 at 11.58s and the 890 Duke at 11.42s. The Duke weighs 27 kg less and wins by 0.16s — but the Suzuki inline-four claws back 3 km/h in trap speed. Physics-based breakdown of where each bike wins and loses, plus sprocket-first tuning strategy for both.",
  },
  {
    slug: "yezdi-roadster-quarter-mile-physics",
    title: "Yezdi Roadster Quarter-Mile Physics: 334cc Neo-Retro at the Strip",
    date: "2026-05-18",
    readTime: "11 min",
    tags: ["Yezdi", "Roadster 334", "BG6 platform", "Indian retro", "physics"],
    excerpt:
      "MotoQuant simulates the Yezdi Roadster 334 at 15.42s and 138 km/h trap at Aamby Valley. 28.6 hp, 175 kg dry, BG6 platform shared with the Scrambler / Adventure 334 / Jawa 42 Bobber 350. Why the ₹6,500 sprocket swap is the cheapest tenth on the bike, and where the Roadster sits against the Classic 350 and Duke 390.",
  },
  {
    slug: "how-to-tune-for-mmrt-chennai",
    title: "How to Tune for MMRT Chennai: Sea-Level, Humid, Hot Track",
    date: "2026-05-18",
    readTime: "11 min",
    tags: ["MMRT", "Chennai", "venue", "tuning", "Tamil Nadu"],
    excerpt:
      "MMRT Chennai sits at 78 m altitude with 80% humidity and 30°C track temperatures most of the year. MotoQuant simulates the same Hayabusa 0.05s quicker at MMRT than Aamby Valley in November, with a higher trap speed but a slightly worse 60-foot. Venue-specific tuning math, month-by-month ET table, and four practical adjustments before you trailer the bike.",
  },
  {
    slug: "yamaha-xsr900-gp-vs-mt-09-quarter-mile-physics",
    title: "Yamaha XSR900 GP vs MT-09: Where the Heritage Tax Is Paid",
    date: "2026-05-18",
    readTime: "11 min",
    tags: ["Yamaha", "XSR900 GP", "MT-09", "CP3 triple", "comparison"],
    excerpt:
      "MotoQuant simulates the Yamaha XSR900 GP at 10.98s and the MT-09 at 10.86s — same 890cc CP3 triple, same 6-speed cassette, 0.12s apart. Spec-by-spec physics breakdown of where the mass lives, why the fairing pays it back at top speed, and the Indian CBU pricing math.",
  },
  {
    slug: "kawasaki-ninja-zx-4r-quarter-mile-physics",
    title: "Kawasaki Ninja ZX-4R Quarter-Mile Physics: 400cc Inline-Four",
    date: "2026-05-18",
    readTime: "11 min",
    tags: ["Kawasaki", "Ninja ZX-4R", "400cc", "inline-four", "physics"],
    excerpt:
      "MotoQuant simulates the 2024 Kawasaki Ninja ZX-4R at 12.681s and 192.6 km/h trap. Why a 76 hp 400cc inline-four runs a 12.6 when every other 400-class bike runs a 13.5 — plus three mods under ₹30,000 that close the gap to the ZX-4RR.",
  },
  {
    slug: "yamaha-mt-125-xsr125-platform-physics",
    title: "Yamaha MT-125 vs XSR125: Same Engine, 0.10s Apart at the Strip",
    date: "2026-05-18",
    readTime: "10 min",
    tags: ["Yamaha", "MT-125", "XSR125", "A1 licence", "platform physics"],
    excerpt:
      "MotoQuant simulates the MT-125 at 19.123s and the XSR125 at 19.222s — same engine, same gearbox, same final drive, 0.10s apart. Where the tenth lives, why the heritage tax is paid in frontal area, and why the YZF-R125 beats both.",
  },
  {
    slug: "cfmoto-800nk-quarter-mile-physics",
    title: "CFMoto 800NK Quarter-Mile Physics: A KTM 790 Duke in Disguise",
    date: "2026-05-18",
    readTime: "11 min",
    tags: ["CFMoto", "800NK", "LC8c", "Indian mid-cc", "physics"],
    excerpt:
      "MotoQuant simulates the CFMoto 800NK at 11.386s and 203.2 km/h trap. The KTM-derived LC8c parallel twin sits at ₹9-12 lakh in India — the cheapest LC8c-engined bike on the market. Physics breakdown of where the tenths live and why a 95 hp parallel twin runs an 11.4.",
  },
  {
    slug: "ktm-duke-390-vs-rc-390-quarter-mile-physics",
    title: "KTM Duke 390 vs RC 390: Quarter-Mile Physics at Aamby Valley",
    date: "2026-05-18",
    readTime: "12 min",
    tags: ["KTM", "Duke 390", "RC 390", "Indian 400cc", "comparison"],
    excerpt:
      "MotoQuant simulates the RC 390 at ~13.5s and 166 km/h trap, the Duke 390 at ~13.7s and 162 km/h at Aamby Valley. Same engine, two tenths apart — almost all of it aerodynamic. Plus four cost-per-tenth mods under ₹25,000 and a look at the Fast Track Racing 11.342s record.",
  },
  {
    slug: "ktm-duke-390-quarter-mile-stock-to-11s",
    title: "KTM Duke 390 Quarter Mile: From 13.3s Stock to an 11.342s Record",
    date: "2026-06-01",
    readTime: "13 min",
    tags: ["KTM", "Duke 390", "Indian 400cc", "drag mods", "cost per tenth"],
    excerpt:
      "MotoQuant simulates the stock 2022 Duke 390 at 13.30s and 162 km/h trap at Aamby Valley. Fast Track Racing India ran 11.342s with the same engine. Two seconds of ET decomposed mod-by-mod, with Indian retail pricing — plus a practical ₹49k build that puts the bike under 12.6s.",
  },
  {
    slug: "pulsar-ns400z-quarter-mile-physics",
    title: "Pulsar NS400Z Quarter-Mile Physics (and Why an RC 390 Still Wins)",
    date: "2026-05-18",
    readTime: "12 min",
    tags: ["Bajaj", "Pulsar NS400Z", "KTM RC 390", "Indian 400cc", "physics"],
    excerpt:
      "MotoQuant simulates the Pulsar NS400Z at ~13.8s and 158 km/h trap at Aamby Valley. A stock RC 390 still beats it by 0.3s. Physics-based explanation of the 23 kg, the gearing, and the Cd that the press release glossed over — plus three cost-per-tenth mods under ₹22,000.",
  },
  {
    slug: "re-continental-gt-650-quarter-mile-physics",
    title: "Royal Enfield Continental GT 650 Quarter-Mile Physics",
    date: "2026-05-18",
    readTime: "10 min",
    tags: ["Royal Enfield", "Continental GT 650", "Indian 650cc", "cafe racer"],
    excerpt:
      "MotoQuant simulates the RE Continental GT 650 at ~14.1s and 158 km/h trap. Why the 47 hp / 52 Nm air/oil-cooled twin is rev-limited rather than power-limited — and the ₹7,800 sprocket-and-tire combo that closes most of the gap.",
  },
  {
    slug: "pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics",
    title: "Pulsar NS200 vs Apache RTR 200 4V: Which Wins the Quarter Mile?",
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
      "MotoQuant simulates the NS200 at ~15.9s and the Apache RTR 200 4V at ~16.4s under matched Aamby Valley conditions. Spec-by-spec physics breakdown plus the top three cost-per-tenth mods under ₹15,000 for each.",
  },
  {
    slug: "how-a-2-stroke-expansion-chamber-actually-works",
    title: "How a 2-Stroke Expansion Chamber Actually Works",
    date: "2026-05-08",
    readTime: "11 min",
    tags: ["2-stroke", "expansion chamber", "physics", "RX100", "RD350"],
    excerpt:
      "A pressure wave at 500 m/s, a tuned-RPM peak about 1,500 rpm wide, and a +0.494 s simulator bias on the 2T cluster. Why the pipe IS the engine on an RX100, RD350, or RGV250 — and what that means for cost-per-tenth at an Indian drag strip.",
  },
  {
    slug: "hayabusa-vs-zx-14r-which-is-faster",
    title: "Hayabusa vs ZX-14R: Which Is Faster Off the Line?",
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
      "MotoQuant simulates the Hayabusa Gen1 reference at 10.471s and pegs the ZX-14R 2012 with a slim ~0.12 second ET advantage under matched conditions. Spec-by-spec breakdown of the two flagship hyper-bikes — where each one wins, and why.",
  },
  {
    slug: "hero-xtreme-200s-4v-quarter-mile-physics",
    title: "Hero Xtreme 200S 4V Quarter-Mile Physics: 200cc Commuter Drag",
    date: "2026-05-08",
    readTime: "9 min",
    tags: ["Hero", "Xtreme 200S 4V", "Indian 200cc", "commuter sport"],
    excerpt:
      "MotoQuant simulates the Hero Xtreme 200S 4V at 17.40s and 125 km/h trap. Why the 19.1 hp / 17.35 Nm 4-valve oil-cooled single is gearing-limited, not power-limited — and the two ₹3,600 mods that close most of the gap.",
  },
  {
    slug: "ktm-1390-super-duke-r-evo-quarter-mile-physics",
    title: "KTM 1390 Super Duke R EVO Quarter-Mile Physics Breakdown",
    date: "2026-05-08",
    readTime: "9 min",
    tags: ["KTM", "1390 Super Duke R", "physics", "litre naked"],
    excerpt:
      "MotoQuant simulates the 2024 KTM 1390 Super Duke R EVO at 10.225s and 237 km/h trap. MCN clocked stock test bikes at 9.95s. Here is exactly what the 0.275s gap is — and what actually limits the bike at the strip.",
  },
  {
    slug: "how-the-motoquant-physics-engine-works",
    title: "How the MotoQuant Physics Engine Works",
    date: "2026-04-27",
    readTime: "14 min",
    tags: ["physics", "engine", "validation", "methodology"],
    excerpt:
      "A first-principles tour of the 15-sub-model RK4 physics engine. Engine torque curves, Pacejka tires, clutch slip dynamics, weight transfer — what we simulate, what we validate against, and what the residual error actually means.",
  },
  {
    slug: "the-physics-of-a-perfect-launch",
    title: "The Physics of a Perfect Launch",
    date: "2026-04-24",
    readTime: "8 min",
    tags: ["physics", "launch control", "clutch"],
    excerpt:
      "Clutch engagement RPM, tire slip ratio, and weight transfer work together in the first 0.4 seconds. Getting any one wrong costs you tenths. Here is what the math says.",
  },
  {
    slug: "why-your-r15-wont-hit-14s",
    title: "Why Your R15 Won't Hit 14s (And What Will Actually Help)",
    date: "2026-04-24",
    readTime: "10 min",
    tags: ["small-cc", "Yamaha R15", "Indian bikes", "tuning"],
    excerpt:
      "The Yamaha YZF-R15 V3 should run ~14.5s based on factory power. Most stock bikes run 15.5–16s. The gap is not about engine power — it is about gearing, clutch slip, and traction. We break down every second.",
  },
  {
    slug: "how-to-tune-for-aamby-valley-in-november",
    title: "How to Tune for Aamby Valley in November",
    date: "2026-04-24",
    readTime: "6 min",
    tags: ["venue", "Aamby Valley", "weather", "conditions"],
    excerpt:
      "November at Aamby Valley means density altitude around 1100 m, 18–24°C, and concrete with a good grip coefficient. Every one of these numbers changes your optimal tune. Here is the MotoQuant venue analysis.",
  },
];

/* ── Featured + rubric grouping ────────────────────────────────────────────
   The flagship methodology post anchors the index; every other card is
   grouped under a rubric inferred from its slug, so there is no per-post
   metadata to maintain — new posts land in the right section automatically. */
const FEATURED_SLUG = "how-the-motoquant-physics-engine-works";

const RUBRICS = [
  { id: "physics", title: "Physics & engineering" },
  { id: "guides", title: "Guides & venue tuning" },
  { id: "comparisons", title: "Bike comparisons" },
  { id: "breakdowns", title: "Bike breakdowns" },
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

function FeaturedPostCard({ post }) {
  return (
    <Link href={`/blog/${post.slug}`} className="block group mb-16">
      <article className="card card-hover relative overflow-hidden p-6 md:p-8">
        <span
          aria-hidden="true"
          className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-brand-orange/60 to-transparent"
        />
        <div className="label-mono text-brand-orange mb-4">
          Featured dispatch
        </div>
        <div className="grid md:grid-cols-[minmax(0,1.7fr)_minmax(0,1fr)] gap-6 md:gap-10 items-start">
          <div>
            <h2 className="font-display font-bold text-2xl md:text-3xl text-white leading-snug mb-4 group-hover:text-brand-orange transition-colors">
              {post.title}
            </h2>
            <p className="text-white/60 text-sm leading-relaxed mb-5">
              {post.excerpt}
            </p>
            <div className="flex items-center gap-4">
              <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/45">
                {new Date(post.date).toLocaleDateString("en-IN", {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}{" "}
                · {post.readTime} read
              </span>
              <span className="text-brand-accent text-xs font-mono group-hover:text-brand-orange transition-colors">
                Read the deep dive →
              </span>
            </div>
          </div>
          <div className="flex flex-wrap gap-1.5 content-start md:justify-end">
            {post.tags.map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide h-fit"
              >
                {t}
              </span>
            ))}
          </div>
        </div>
      </article>
    </Link>
  );
}

function PostCard({ post }) {
  return (
    <Link href={`/blog/${post.slug}`} className="block group h-full">
      <article className="relative h-full overflow-hidden rounded-xl border border-brand-orange/15 bg-ink-1/60 p-6 transition duration-300 hover:border-brand-orange/40 motion-safe:group-hover:-translate-y-1">
        <span
          aria-hidden="true"
          className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-brand-orange/50 to-transparent"
        />
        <div className="flex flex-wrap gap-1.5 mb-4">
          {post.tags.map((t) => (
            <span
              key={t}
              className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
            >
              {t}
            </span>
          ))}
        </div>
        <h2 className="font-display font-bold text-xl text-white mb-3 group-hover:text-brand-orange transition-colors leading-snug">
          {post.title}
        </h2>
        <p className="text-white/60 text-sm leading-relaxed mb-4">
          {post.excerpt}
        </p>
        <div className="flex items-center justify-between gap-3">
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/45">
            {new Date(post.date).toLocaleDateString("en-IN", {
              year: "numeric",
              month: "long",
              day: "numeric",
            })}{" "}
            · {post.readTime} read
          </div>
          <span className="shrink-0 text-brand-accent text-xs font-mono group-hover:text-brand-orange transition-colors">
            Read →
          </span>
        </div>
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
    <div className="min-h-screen bg-black text-white">
      <SiteNav />

      {/* Hero — unified cockpit voice; kicker count stays in lockstep
          with the POSTS array by construction. */}
      <PageHero
        kicker={`${POSTS.length} dispatches · physics · tuning · data`}
        badge="MotoQuant Blog"
        title={<>The physics of <span className="text-gradient-orange">drag racing.</span></>}
        sub="Technical deep-dives on motorcycle physics, tuning strategy, and data analysis. Written for the Indian drag racing community."
      />

      <main className="pb-24 px-6">
        <div className="max-w-5xl mx-auto">
          <FeaturedPostCard post={featured} />

          {grouped.map((rubric) => (
            <section key={rubric.id} className="mb-16 last:mb-0">
              <div className="flex flex-wrap items-baseline gap-3 mb-6">
                <h2 className="font-display font-bold text-2xl text-white">
                  {rubric.title}
                </h2>
                <span className="label-mono">
                  {rubric.posts.length}{" "}
                  {rubric.posts.length === 1 ? "post" : "posts"}
                </span>
              </div>
              <Stagger className="grid md:grid-cols-2 lg:grid-cols-3 gap-6" stagger={0.04}>
                {rubric.posts.map((post) => (
                  <StaggerItem key={post.slug} className="h-full">
                    <PostCard post={post} />
                  </StaggerItem>
                ))}
              </Stagger>
            </section>
          ))}

          {/* GROWTH_EXP_006 — end-of-grid simulator CTA (default OFF, ?variant=B) */}
          <Suspense fallback={null}>
            <EndOfBlogIndexCta />
          </Suspense>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
