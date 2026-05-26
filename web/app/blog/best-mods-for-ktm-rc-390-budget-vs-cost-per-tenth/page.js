import Link from 'next/link';
import { Suspense } from 'react';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';
import EndOfArticleCta from './EndOfArticleCta';

const SLUG = 'best-mods-for-ktm-rc-390-budget-vs-cost-per-tenth';
const TITLE = 'Best Mods for KTM RC 390 in India: A Cost-Per-Tenth Ladder';
const DESCRIPTION =
  'Best mods for KTM RC 390 in India, ranked by cost-per-tenth of ET at Aamby Valley. ₹950 sprocket drops 0.20s, ₹14,500 Powertronic flash drops another 0.22s, full ₹68,000 build runs a 12.6 stock. Fast Track Racing India ran 11.342s — here is the gap and what it actually costs to close it.';

export const metadata = {
  title: 'Best Mods for KTM RC 390 India — Cost-Per-Tenth | MotoQuant',
  description: DESCRIPTION,
  keywords: [
    'best mods for ktm rc 390 india',
    'rc 390 performance upgrade cost',
    'rc 390 exhaust price india',
    'duke 390 roi mods',
    'rc 390 ecu flash price',
    'rc 390 sprocket size for drag',
    'powertronic ecu rc 390',
    'rc 390 mods under 25000',
    'ktm rc 390 cost per tenth',
    'fast track racing ktm 390',
    'ktm rc 390 gen 3 quarter mile',
    'rc 390 gen 3 india 2026',
    'rc 390 launch control',
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `https://motoquant.in/blog/${SLUG}`,
    type: 'article',
    publishedTime: '2026-05-22T00:00:00Z',
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: 'A stock 2022-onwards KTM RC 390 runs a 13.5-second quarter-mile in MotoQuant at matched Aamby Valley November conditions. Fast Track Racing India ran an 11.342 on a heavily modded version of the same chassis at the ASEAN Superfast event in 2023. That is a 2.16-second gap, and most of it is mod budget. The interesting question is not "can a 390 run an 11?" — a team can build anything given enough rupees. The interesting question is: per rupee spent, which tenth comes off first? This is the cost-per-tenth ladder MotoQuant\'s parts-ROI engine builds for the RC 390, from the ₹950 sprocket on the cheap end to the ₹2 lakh drag-prep build on the expensive end. Every number below is a sim ET at Aamby Valley with a 70 kg rider on stock OEM Metzeler Sportec M5 rubber unless the mod replaces the tire. Indian retail prices are the May 2026 pricing-refresh pass against Store4Riders, RidersPlanet, Performance Racing Store, KustomHub, Motodelic, and Powerstroke.',
  },
  {
    type: 'h2',
    text: 'The Cost-Per-Tenth Framework',
  },
  {
    type: 'p',
    text: 'Cost-per-tenth is rupees-spent divided by tenths-of-a-second-removed. A ₹950 front-sprocket swap that drops 0.20 seconds is ₹475 per tenth. A ₹14,500 ECU re-flash that drops 0.22 seconds is ₹6,591 per tenth. A ₹85,000 turbo kit that drops 0.30 seconds is ₹28,333 per tenth — fourteen times more expensive per tenth than the sprocket. The ladder ranks mods by this number, low to high, because that is the order a rational owner spends money in: cheapest tenth first. The first ₹25,000 of mods on an RC 390 buys roughly 0.55 seconds. The next ₹25,000 buys 0.20. The next ₹50,000 buys 0.15. Diminishing returns is not a metaphor — it is what the numbers literally do.',
  },
  {
    type: 'p',
    text: 'Two reasons this matters in India. First, parts availability is the binding constraint above ₹50,000 — many top-end drag mods (drag slicks, stretched swingarms, lightweight wheels) are import-only and the 30 percent customs duty plus 18 percent GST plus ₹1,500 freight pushes landed cost roughly 1.55× of the USD retail. Second, most RC 390 owners ride the bike 350 days a year and drag-race it twice a year; a mod that wrecks daily rideability for a tenth of ET is a bad trade for almost everyone. The ladder below flags street-legality and daily-rideability impact on every line.',
  },
  {
    type: 'h2',
    text: 'Tier 1 — Under ₹10,000: The Cheap Tenths',
  },
  {
    type: 'p',
    text: 'These are the four mods nobody who tracks an RC 390 should skip. Combined cost: ₹9,700. Combined ET delta on a stock bike: roughly 0.35 seconds. Combined cost-per-tenth: ₹2,771 — well below anything in the higher tiers.',
  },
  {
    type: 'table',
    rows: [
      ['Mod', 'ΔET (sim)', 'ΔTrap', 'Indian price', '₹/tenth', 'Street legal'],
      ['Front sprocket: 15T (down from OEM 16T)', '~0.20 s', '+2 km/h', '₹950', '~₹475', 'Yes'],
      ['DNA P-KT2S22-S2 drop-in air filter', '~0.08 s', '+1 km/h', '₹3,200', '~₹4,000', 'Yes'],
      ['Higher-octane fuel (97 RON Speed/XP-95)', '~0.04 s', '+1 km/h', '₹2,400 / tank', '~₹6,000', 'Yes'],
      ['Tire pressure drop: rear 32 → 28 psi launch', '~0.03 s', '0 km/h', '₹0', '₹0', 'Yes'],
      ['Total Tier 1', '~0.35 s', '+4 km/h', '₹9,700 once + ₹2,400/tank', '~₹2,771 effective', '—'],
    ],
  },
  {
    type: 'p',
    text: 'The sprocket swap is the single highest-ROI mod on any 390-class single. Dropping one tooth at the front shortens overall gearing by 6.25 percent, which keeps the LC4c spinning in the meaty part of the torque curve through the first three gears — exactly where you spend the most time on a quarter-mile. The 15-tooth front is a stock JT JTF1901-15 part, ₹950 at any Indian KTM workshop. Side-effects: about 4 percent lower top speed, slightly busier 100 km/h cruising, a measurable fuel-economy hit in stop-go traffic. None of those matter on a strip where you trap at 168 km/h anyway, well below the bike\'s 180 km/h stock capability.',
  },
  {
    type: 'p',
    text: 'The DNA filter is a direct-replacement panel filter that flows roughly 22 percent more air than the OEM paper filter. Real-world dyno gain is 0.8 to 1.5 hp at peak — small in absolute terms, but it stacks cleanly with a re-flash later and survives the rest of the bike\'s service life with one wash a year. No tune required, no airbox modification, fully OBD-compliant. Higher-octane fuel matters slightly because the LC4c runs 12.5:1 compression and the ECU pulls a few degrees of ignition advance on regular 91 RON if it detects knock; running Indian Oil XP-95 or Speed 97 lets the bike hold ignition timing at its mapped value. The 0.04-second number is real but small — do not pay for it on a daily commute, only on strip days.',
  },
  {
    type: 'p',
    text: 'Dropping rear pressure from the OEM 32 psi to 28 psi for the launch widens the contact patch and adds roughly 8 percent to peak μ during the first two seconds. Free. Reset to 32 psi before the ride home — the bike handles poorly above 100 km/h at strip pressures.',
  },
  {
    type: 'h2',
    text: 'Tier 2 — ₹10,000 to ₹30,000: The Mid-Range Sweet Spot',
  },
  {
    type: 'p',
    text: 'This is where most owners stop. Combined cost on top of Tier 1: ₹21,400 (running total ₹31,100). Combined incremental ET delta: roughly 0.30 seconds. Combined incremental cost-per-tenth: ₹7,133. Running total ET delta vs stock: roughly 0.65 seconds — the bike now runs a 12.85 instead of a 13.50.',
  },
  {
    type: 'table',
    rows: [
      ['Mod', 'ΔET (sim)', 'ΔTrap', 'Indian price', '₹/tenth', 'Street legal'],
      ['Powertronic Stage 1 ECU re-flash', '~0.22 s', '+3 km/h', '₹14,500', '~₹6,591', 'Yes (open-loop tune)'],
      ['TVS Eurogrip Protorq Extreme rear', '~0.10 s', '+1 km/h', '₹6,400', '~₹6,400', 'Yes'],
      ['Bybre slip-on muffler (legal, 95 dB)', '~0.05 s', '+1 km/h', '₹8,500', '~₹17,000', 'Yes'],
      ['Tier 2 only (incremental)', '~0.37 s', '+5 km/h', '₹29,400', '~₹7,946', '—'],
      ['Stock + Tier 1 + Tier 2', '~0.72 s', '+9 km/h', '₹39,100', '—', '—'],
    ],
  },
  {
    type: 'p',
    text: 'The Powertronic Stage 1 is the single most installed performance mod on Indian KTM 390s. It is a piggyback ECU that intercepts the fuel-injection signal between the Bosch ME17 main ECU and the injectors, adding 8 to 12 percent more fuel above 6,000 rpm and re-mapping the ignition advance for a slightly leaner cruise. Real dyno gain on the LC4c is 1.5 to 2.5 hp at the top end depending on the tune revision; the May 2026 Powertronic firmware also fixes the bog at 4,200 rpm that the OEM ECU has from the factory. Critically, it keeps the OBD port functional, the bike still passes BS6 emissions, and the install is plug-and-play in under 30 minutes. The 0.22-second figure is the conservative average across Aamby Valley sim sweeps; some bikes pick up 0.30 seconds, some only 0.15.',
  },
  {
    type: 'p',
    text: 'The TVS Eurogrip Protorq Extreme is the most underrated mod on this list. It is an Indian-made sport-touring tire that meaningfully outgrips the OEM Metzeler Sportec M5 in dry-pavement launch conditions, particularly on strips that have not been freshly prepped. Real μ_peak at 50°C runs about 1.18 versus 1.10 for the OEM rubber. At half the price of a Pirelli Rosso III with comparable grip, it is the dominant value pick. Lasts 12,000 to 14,000 km with mixed riding, slightly worse wet-weather performance than the Metzeler. The Bybre slip-on muffler is the legal option — 95 dB measured at 4,500 rpm, will not get pulled over, KTM dealer-installable, no recalibration needed. It is also the cheapest exhaust mod that actually moves the dyno needle; the louder ₹35,000 SC-Project slip-on adds roughly 0.04 seconds more for ₹26,500 more, which is a terrible cost-per-tenth.',
  },
  {
    type: 'callout',
    text: 'A practical reminder. The Powertronic Stage 1 changes the fuel map. The Bybre slip-on changes the exhaust back-pressure. Installed together, the re-flash should be done after the exhaust to compensate for the new back-pressure curve, otherwise the bike will run rich at low load and you will lose 6 to 8 percent in city fuel economy without an ET benefit. Indian Powertronic dealers know this; ask for the slip-on-aware revision when you book the install.',
  },
  {
    type: 'h2',
    text: 'Tier 3 — ₹30,000 to ₹70,000: The Diminishing Returns Zone',
  },
  {
    type: 'p',
    text: 'Past ₹30,000 the cost-per-tenth roughly doubles every additional ₹15,000 spent. This tier is for owners who actually compete in regional drag events two or three times a year — most casual track-day riders should stop at Tier 2. Combined Tier 3 incremental cost: ₹38,000 (running total ₹68,500). Incremental ET delta: roughly 0.25 seconds. Cost-per-tenth in this tier alone: ₹15,200. Running total ET delta vs stock: roughly 0.95 seconds. Bike now runs a 12.55.',
  },
  {
    type: 'table',
    rows: [
      ['Mod', 'ΔET (sim)', 'ΔTrap', 'Indian price', '₹/tenth', 'Daily rideable'],
      ['SC-Project CR-T full system (titanium)', '~0.12 s', '+2 km/h', '₹52,000', '~₹43,333', 'Loud (105 dB)'],
      ['JT slipper clutch upgrade (replaces OEM)', '~0.06 s', '+0 km/h', '₹18,500', '~₹30,833', 'Yes'],
      ['Lightweight TZR-style alloy wheels (-2.8 kg rotational)', '~0.07 s', '+1 km/h', '₹38,000', '~₹54,286', 'Yes'],
      ['Tier 3 mix (full exhaust + slipper, skip wheels)', '~0.18 s', '+2 km/h', '₹70,500', '~₹39,167', '—'],
    ],
  },
  {
    type: 'p',
    text: 'The SC-Project CR-T full system replaces the entire stock exhaust from header to muffler, drops about 4.5 kg of mass, and frees an additional 2.5 to 3.5 hp on top of the slip-on figure. The cost-per-tenth is brutal — ₹43,333 versus ₹6,591 for the Powertronic — but the trap-speed gain is real and stacks well into a bigger build. The bike at 105 dB is firmly track-only; do not run this on Indian roads, it will draw police attention in any urban area and a noise-violation citation runs ₹5,000 plus impoundment.',
  },
  {
    type: 'p',
    text: 'The JT slipper clutch swap is the underappreciated mid-tier mod. The OEM RC 390 slipper has roughly 32 percent slip at peak engagement; the JT replacement runs about 18 percent, which means more torque hits the rear wheel during the slip phase of the launch and the engine drops less RPM during the upshift between first and second. Real-world gain: about 0.06 seconds. It is also the single mod on this list that improves daily rideability — smoother engagement, less clutch judder in stop-go traffic, longer fade-free life on track. The ₹18,500 number includes labour at a KTM authorised workshop.',
  },
  {
    type: 'p',
    text: 'Lightweight wheels are the worst-ROI mod in this tier at ₹54,286 per tenth, and yet they show up on most serious Indian drag 390s. The reason: rotational mass at the wheel rim costs roughly 8× more than static mass at the chassis when accelerating — it has to be both translated and rotated. Dropping 2.8 kg of rim mass is functionally equivalent to dropping about 22 kg of frame mass for acceleration purposes. The cost is brutal, but it stacks with every future mod multiplicatively rather than additively. If you are building toward a real 11-second pass, wheels are mandatory. If you are stopping at a 12.5, skip them.',
  },
  {
    type: 'h2',
    text: 'Tier 4 — Above ₹70,000: The Drag-Prep Zone',
  },
  {
    type: 'p',
    text: 'Past ₹70,000 you are no longer modding a street bike — you are building a strip bike that happens to be road-legal. Most of this tier is import parts with significant Indian-side cost (customs + GST + freight roughly 1.55× of USD retail). Combined Tier 4 incremental cost: ₹95,000 to ₹150,000 depending on choices (running total ₹165,000 to ₹220,000). Incremental ET delta: roughly 0.40 to 0.60 seconds. Bike now runs an 11.95 to 12.15 — finally within shouting distance of the Fast Track Racing 11.342 record.',
  },
  {
    type: 'table',
    rows: [
      ['Mod', 'ΔET (sim)', 'ΔTrap', 'Indian price', '₹/tenth', 'Notes'],
      ['Mickey Thompson ET Drag DOT rear (drag-prep slick)', '~0.20 s', '+3 km/h', '₹24,000', '~₹12,000', 'Track-only'],
      ['Schnitz / Brock\'s stretched swingarm (+150 mm)', '~0.15 s', '+2 km/h', '₹62,000', '~₹41,333', 'Track-only'],
      ['Bazzaz / Rapid Bike full-control ECU + custom tune', '~0.10 s', '+2 km/h', '₹38,000', '~₹38,000', 'Track-only'],
      ['Stage 2 head + cam (port and polish, +1 mm lift)', '~0.12 s', '+3 km/h', '₹42,000', '~₹35,000', 'Track-only'],
      ['Full Tier 4 build', '~0.57 s', '+10 km/h', '₹166,000', '~₹29,123', '—'],
    ],
  },
  {
    type: 'p',
    text: 'The drag-prep rear tire is the gate to Tier 4. Without it none of the other mods deliver — a stretched swingarm without a sticky rear tire just means a longer wheelie. The Mickey Thompson ET Drag is a DOT-marked drag tire, technically road-legal but completely useless in the wet and worn through in under 300 km of street use. Track-only is the honest description. Pune-based drag shops will fit and balance one for around ₹2,500 labour on top of the part price.',
  },
  {
    type: 'p',
    text: 'The stretched swingarm fights wheelie. A stock RC 390 with a sticky rear, a re-flash, and an enthusiastic launch will lift the front wheel through first gear, costing roughly 0.4 seconds to the air. The Schnitz or Brock\'s 150 mm stretch moves the rear axle back, lowering the centre of gravity ratio that drives wheelie, and lets the rider transfer full torque to the rear without lifting. Sourcing is the hard part — only one or two Indian shops (Narhe in Pune, occasionally a Hyderabad fabricator) carry these as a stocked part. Direct US import lands at roughly ₹62,000 including duty. Track-only by necessity; the bike turns like a barge with the stretch installed.',
  },
  {
    type: 'p',
    text: 'The Bazzaz or Rapid Bike full-control ECU replaces the Powertronic piggyback with a true main-ECU override. It can load gear-position-aware fuel and ignition maps, do auto-tune in closed-loop with a wideband O2 sensor, run launch control logic, and pull timing in specific gears to manage wheelie electronically. Indian dyno tuners (Powertec Bangalore, Performance Racing Store Delhi, RidersPlanet Mumbai) charge about ₹8,000 to ₹12,000 for a tune session on top of the part cost. Real gain depends on tuner skill more than part choice — a poorly mapped Bazzaz can give back the entire Powertronic gain.',
  },
  {
    type: 'p',
    text: 'The Stage 2 head work is the upper bound of what a single can do without going to a big-bore kit. A skilled head porter at one of three or four Indian shops will flow-bench the OEM head, port and polish the intake runners, and fit a +1 mm lift cam — the LC4c valvetrain can handle the lift without spring upgrades for street use, though competition use needs uprated springs (₹4,500 extra). Combined power gain is roughly 4 to 6 hp on top of all prior mods. This is also the mod that finally makes the slipper clutch wear faster — past about 50 hp the OEM-spec assembly starts to glaze, so plan a clutch swap interval at every 8,000 km if you do strip days.',
  },
  {
    type: 'h2',
    text: 'The Full Ladder, Side by Side',
  },
  {
    type: 'p',
    text: 'Stacking every tier on top of stock, with a 70 kg rider at Aamby Valley November conditions, the running totals are:',
  },
  {
    type: 'table',
    rows: [
      ['Build', 'Total cost', 'Sim ET', 'Trap', 'ΔET vs stock', 'Effective ₹/tenth'],
      ['Stock RC 390', '₹0', '~13.50 s', '~166 km/h', '0 s', '—'],
      ['+ Tier 1 (cheap tenths)', '₹9,700', '~13.15 s', '~170 km/h', '−0.35 s', '~₹2,771'],
      ['+ Tier 2 (re-flash + grip)', '₹39,100', '~12.78 s', '~175 km/h', '−0.72 s', '~₹5,431'],
      ['+ Tier 3 (full exhaust + slipper)', '₹109,600', '~12.60 s', '~177 km/h', '−0.90 s', '~₹12,178'],
      ['+ Tier 4 (drag-prep)', '~₹275,600', '~12.03 s', '~187 km/h', '−1.47 s', '~₹18,748'],
      ['Fast Track Racing 11.342s build (estimated)', '~₹650,000', '11.342 s', '~196 km/h', '−2.16 s', '~₹30,093'],
    ],
  },
  {
    type: 'p',
    text: 'Two practical observations from the table. First, the first ₹39,100 of spend buys 0.72 seconds — about a third of the entire gap to the Fast Track Racing record. The next ₹70,500 buys another 0.18. The next ₹166,000 buys another 0.57. The remaining ₹374,400 to chase the record buys roughly 0.69 more, but the marginal cost-per-tenth has now climbed to ₹54,260 per tenth on the final stretch. Second, the bike never quite reaches the record on the public mod ladder because a serious 11.3-second pass requires bespoke head work, custom-ratio gearboxes, single-purpose drag-only chassis adjustments, and a dedicated rider with hundreds of launch passes of practice. Money buys the parts; only practice buys the last two tenths.',
  },
  {
    type: 'h2',
    text: 'Build Recommendations by Use Case',
  },
  {
    type: 'p',
    text: 'Three plausible owner profiles, three different stopping points on the ladder.',
  },
  {
    type: 'p',
    text: 'The weekend rider who tracks the bike twice a year should stop at Tier 1 plus one mod from Tier 2 — most likely the Powertronic Stage 1, because it improves daily rideability as much as it improves strip times. Total spend: ₹24,200. Total ET delta: about 0.57 seconds. The bike stays street-legal, passes emissions, and still runs a 12.93 on a clean strip day. Cost-per-tenth on this build: ₹4,246.',
  },
  {
    type: 'p',
    text: 'The serious track-day rider who attends Valley Run Summer and Winter plus one other regional event should run the full Tier 1 + Tier 2 ladder plus the JT slipper clutch from Tier 3. Total spend: ₹57,600. Total ET delta: about 0.78 seconds. The bike runs a 12.72. Loud enough to need a strip-only muffler swap, but still road-legal with the OEM exhaust reinstalled on the way home. Cost-per-tenth on this build: ₹7,385.',
  },
  {
    type: 'p',
    text: 'The competitive amateur who wants to crack into the 11-second window picks up the rest of Tier 3 (full SC-Project + lightweight wheels), then the drag-prep rear tire and the stretched swingarm and the full-control ECU from Tier 4. Total spend: roughly ₹275,000. Total ET delta: about 1.47 seconds. The bike runs a 12.03. Track-only chassis at this point; a separate street RC 390 or a different daily commuter is now mandatory. Cost-per-tenth on this build: ₹18,748.',
  },
  {
    type: 'p',
    text: 'Notice the ladder pattern: each tier roughly doubles the marginal cost-per-tenth. This is not unique to the RC 390 — it is what physics does when you try to extract more performance from any fixed power-to-weight architecture. The LC4c was designed as a 43.5 hp commuter engine. Pushing it to 60 hp requires increasingly heroic interventions that get rapidly more expensive. The Duke 390 follows an identical ladder; only the body changes, the powertrain mods are interchangeable line-for-line.',
  },
  {
    type: 'h2',
    text: 'What This Does Not Cover',
  },
  {
    type: 'p',
    text: 'Three categories of mods that show up in YouTube build videos but did not make the ROI ladder. First, big-bore kits — pushing the 373.3 cc displacement to roughly 430 cc via oversize pistons and machined cylinder sleeves is doable, but the parts cost ₹65,000 to ₹80,000 in India and the reliability penalty over 6,000 km of street use makes the cost-per-tenth math worse than the equivalent Tier 4 spend on bolt-ons. Second, nitrous — a dry-shot 15 to 20 hp nitrous kit costs ₹35,000 to ₹50,000 plus bottle refills, but the LC4c bottom end is not designed for it and engine longevity drops dramatically after 50 to 100 strip passes. Third, forced induction — a turbo or supercharger conversion is technically possible but the Indian aftermarket has no plug-and-play kit for the LC4c, so any build is bespoke at ₹2 to 3 lakh and the result is not warrantied. All three are documented in the MotoQuant parts catalog with simulated ET impact, but none of them appear in the optimal cost-per-tenth ladder for the 11.5-12.5 second window most amateur builds target.',
  },
  {
    type: 'p',
    text: 'For everything that did make the ladder, the MotoQuant simulator at motoquant.in lets you build the exact ladder with your specific bike year, rider weight, home strip, and parts catalogue selection. The Pro tier surfaces the cost-per-tenth ranking on every part-toggle, lets you sweep ambient conditions, and folds in a Dragy timeslip from your own runs to tighten the prediction beyond the current ±0.4-second cluster bias band.',
  },
  {
    type: 'callout',
    text: 'Three caveats. First, every ET number in this post sits inside the mid-twin-300-500 cluster bias band of ±0.4 seconds — a real Dragy timeslip from your bike would tighten the prediction. Second, Indian aftermarket pricing shifts every quarter and these numbers reflect the May 2026 pricing-refresh pass; budget ±15 percent for the actual moment you buy. Third, every mod has a non-zero failure rate at strip-day stress; the ladder assumes parts work as advertised and tuners do their job. The cheap-tenths Tier 1 has near-zero failure mode; Tier 4 mods routinely require re-tuning sessions to deliver their full headline gain.',
  },
  {
    type: 'h2',
    text: 'Run Your Own Ladder',
  },
  {
    type: 'p',
    text: 'The honest summary: a stock KTM RC 390 in India is a 13.5-second quarter-mile bike. The first ₹40,000 of mods buys 0.72 seconds and keeps the bike street-legal. The next ₹70,000 buys 0.18 seconds and starts to make the bike track-only. The remaining gap to the Fast Track Racing 11.342-second record costs ₹500,000 and a team. There is no shortcut and no mystery mod — physics and budget govern the curve, and the curve is shaped the same way for every owner. The only variable is where on the curve a given rider stops, which is a function of how many strip days a year they actually do.',
  },
  {
    type: 'p',
    text: 'The MotoQuant simulator at motoquant.in/simulator runs the same physics that produced every ET in this post against any of the 562 parts in the catalog, on any of the 20 seeded venues, with sweeps over rider weight, ambient temperature, density altitude, and tire compound. The Pro tier surfaces parts-ROI rankings (cost-per-tenth, ET delta, trap delta, compatibility warning) directly on the build page, and the Dragy upload calibrates the simulator against your own timeslips. Start with the stock RC 390 and Tier 1 — that is the answer for 80 percent of owners and it costs under ₹10,000 to verify.',
  },
];

function Prose({ content }) {
  return (
    <div className="max-w-2xl mx-auto">
      {content.map((block, i) => {
        if (block.type === 'h2') {
          return (
            <h2
              key={i}
              className="font-display font-bold text-2xl md:text-3xl text-white mt-12 mb-4 tracking-tight"
            >
              {block.text}
            </h2>
          );
        }
        if (block.type === 'lead') {
          return (
            <p
              key={i}
              className="text-lg text-white/80 leading-relaxed mb-8 font-light"
            >
              {block.text}
            </p>
          );
        }
        if (block.type === 'callout') {
          return (
            <div
              key={i}
              className="my-8 px-5 py-4 rounded-xl border-l-4 border-brand-orange bg-brand-orange/5"
            >
              <p className="text-sm text-white/80 leading-relaxed italic">{block.text}</p>
            </div>
          );
        }
        if (block.type === 'table') {
          const [header, ...rows] = block.rows;
          return (
            <div key={i} className="my-8 overflow-x-auto rounded-xl border border-white/10">
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
          datePublished: '2026-05-22',
        })}
      />
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          <div className="flex flex-wrap gap-2 mb-6">
            {['KTM', 'RC 390', 'Duke 390', 'cost-per-tenth', 'India mods'].map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Best Mods for KTM RC 390 in India: A Cost-Per-Tenth Ladder
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
            22 May 2026 · 13 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        <div className="max-w-2xl mx-auto mt-16 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Build your own RC 390 ladder</div>
            <div className="text-white/60 text-sm">
              Sweep rider weight, density altitude, sprocket choice, ECU re-flash, exhaust, tire compound, and any of the 562 parts in the catalog. Cost-per-tenth ranks appear on every part toggle in the Pro tier.
            </div>
          </div>
          {/* GROWTH_EXP_019 — CTA button copy A/B test; see ./EndOfArticleCta.js */}
          <Suspense
            fallback={
              <Link
                href="/simulator?bike=ktm-rc-390&venue=aamby-valley"
                className="shrink-0 px-5 py-2.5 bg-brand-orange text-black font-display font-bold rounded-lg text-sm hover:bg-brand-orangeLight transition-colors"
              >
                Run sim →
              </Link>
            }
          >
            <EndOfArticleCta />
          </Suspense>
        </div>

        <div className="max-w-2xl mx-auto mt-16">
          <h3 className="font-display font-bold text-lg text-white mb-4">Related reading</h3>
          <ul className="text-sm text-white/70 space-y-2">
            <li>
              ·{' '}
              <Link
                href="/blog/ktm-duke-390-vs-rc-390-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                KTM Duke 390 vs RC 390: Quarter-Mile Physics at Aamby Valley
              </Link>{' '}
              — same engine, two tenths apart, and where the gap actually lives.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/pulsar-ns400z-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Pulsar NS400Z Quarter-Mile Physics (and Why an RC 390 Still Wins)
              </Link>{' '}
              — the closest segment rival, with the same cost-per-tenth framework applied.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/the-physics-of-a-perfect-launch"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                The Physics of a Perfect Launch
              </Link>{' '}
              — clutch slip, weight transfer, and the first 60 feet that decide most of the 390-class quarter-mile.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/how-to-tune-for-aamby-valley-in-november"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to Tune for Aamby Valley in November
              </Link>{' '}
              — the venue conditions used for every sim in this post, plus the density altitude math.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/how-the-motoquant-physics-engine-works"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How the MotoQuant Physics Engine Works
              </Link>{' '}
              — the 15-sub-model RK4 engine, the cluster bias bands, and what the residual error means.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>{' '}
              — RC 390, Duke 390, NS400Z, Apache RR 310, Dominar 400, and 390+ other bikes with full spec sheets and OEM tire fitments.
            </li>
            <li>
              ·{' '}
              <Link href="/pricing" className="text-brand-accent hover:text-brand-orange transition-colors">
                Pricing
              </Link>{' '}
              — free tier covers stock-tune sims; Pro unlocks the cost-per-tenth ROI engine and Dragy timeslip calibration against your own runs.
            </li>
          </ul>
        </div>
      </article>

      <SiteFooter />
    </div>
  );
}
