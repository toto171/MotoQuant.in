import Link from 'next/link';
import { Suspense } from 'react';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'best-mods-for-ktm-rc-390-budget-vs-cost-per-tenth';
const TITLE = 'Best mods for KTM RC 390 in India: a cost-per-tenth ladder';
const DESCRIPTION =
  'The best mods for a KTM RC 390 in India, ranked by rupees per tenth of ET at Aamby Valley. A ₹950 sprocket cuts 0.20s, a ₹14,500 Powertronic flash cuts another 0.22s, and the full ₹68,000 build runs a 12.6 stock. Fast Track Racing India ran 11.342s; here is what closing that gap costs.';

export const metadata = {
  title: 'Best mods for KTM RC 390 in India: cost per tenth | MotoQuant',
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
    text: 'A stock 2022-onwards KTM RC 390 runs a 13.5-second quarter mile in MotoQuant at matched Aamby Valley November conditions. Fast Track Racing India ran an 11.342 on a heavily modded version of the same chassis at the ASEAN Superfast event in 2023. That 2.16-second gap is mostly mod budget. Given enough rupees, a team can make a 390 run an 11; the useful question is which tenth comes off first for each rupee you spend. MotoQuant\'s parts-ROI engine builds the RC 390 ladder that follows, from the ₹950 sprocket at the cheap end to the ₹2 lakh drag-prep build at the expensive end. Every number is a sim ET at Aamby Valley with a 70 kg rider on the stock OEM Metzeler Sportec M5 tires, unless the mod replaces the tire. Indian retail prices come from the May 2026 pricing refresh against Store4Riders, RidersPlanet, Performance Racing Store, KustomHub, Motodelic and Powerstroke.',
  },
  {
    type: 'h2',
    text: 'How cost per tenth works',
  },
  {
    type: 'p',
    text: 'Cost per tenth is the rupees you spend divided by the tenths of a second you take off. A ₹950 front-sprocket swap that cuts 0.20 seconds is ₹475 per tenth. A ₹14,500 ECU re-flash that cuts 0.22 seconds is ₹6,591 per tenth. A ₹85,000 turbo kit that cuts 0.30 seconds is ₹28,333 per tenth, fourteen times more expensive per tenth than the sprocket. The ladder ranks mods by this number, lowest first, because a sensible owner buys the cheapest tenth first. The first ₹25,000 of mods on an RC 390 buys roughly 0.55 seconds. The next ₹25,000 buys 0.20, and the ₹50,000 after that buys 0.15.',
  },
  {
    type: 'p',
    text: 'In India the order matters for two more reasons. Above ₹50,000 the limit is what you can buy at all: many top-end drag mods (drag slicks, stretched swingarms, lightweight wheels) are import-only, and 30 percent customs duty plus 18 percent GST plus ₹1,500 freight brings the landed cost to roughly 1.55× the USD retail price. And most RC 390 owners ride the bike 350 days a year and drag-race it twice; a mod that ruins daily riding for a tenth of ET is a bad trade for almost everyone. The ladder below marks street legality and daily rideability on every line.',
  },
  {
    type: 'h2',
    text: 'Tier 1 (under ₹10,000): the cheap tenths',
  },
  {
    type: 'p',
    text: 'Anyone who takes an RC 390 to the strip should do these four. Together they cost ₹9,700 and take roughly 0.35 seconds off a stock bike, at ₹2,771 per tenth, well below anything in the higher tiers.',
  },
  {
    type: 'table',
    rows: [
      ['Mod', 'ΔET (sim)', 'ΔTrap', 'Indian price', '₹/tenth', 'Street legal'],
      ['Front sprocket: 15T (down from OEM 16T)', '~0.20 s', '+2 km/h', '₹950', '~₹475', 'Yes'],
      ['DNA P-KT2S22-S2 drop-in air filter', '~0.08 s', '+1 km/h', '₹3,200', '~₹4,000', 'Yes'],
      ['Higher-octane fuel (97 RON Speed/XP-95)', '~0.04 s', '+1 km/h', '₹2,400 / tank', '~₹6,000', 'Yes'],
      ['Tire pressure drop: rear 32 → 28 psi launch', '~0.03 s', '0 km/h', '₹0', '₹0', 'Yes'],
      ['Total Tier 1', '~0.35 s', '+4 km/h', '₹9,700 once + ₹2,400/tank', '~₹2,771 effective', '–'],
    ],
  },
  {
    type: 'p',
    text: 'The sprocket swap gives the best return of any mod on a 390-class single. One tooth less at the front shortens overall gearing by 6.25 percent. That keeps the LC4c in the strong part of its torque curve through the first three gears, which is where a quarter-mile run spends most of its time. The 15-tooth front is a stock JT JTF1901-15 part, ₹950 at any Indian KTM workshop. The downsides: about 4 percent less top speed, higher revs at a 100 km/h cruise, and a measurable fuel-economy hit in stop-go traffic. None of that matters on a strip where you trap at 168 km/h, well below the bike\'s 180 km/h stock top speed.',
  },
  {
    type: 'p',
    text: 'The DNA filter is a drop-in panel filter that flows roughly 22 percent more air than the OEM paper filter. On the dyno it gains 0.8 to 1.5 hp at peak. That is small, but it adds cleanly to a re-flash later and lasts the rest of the bike\'s life with one wash a year. It needs no tune and no airbox change, and it stays fully OBD-compliant. Higher-octane fuel helps a little. The LC4c runs 12.5:1 compression, and on regular 91 RON the ECU pulls a few degrees of ignition advance if it detects knock; Indian Oil XP-95 or Speed 97 lets the bike hold its mapped timing. The 0.04 seconds is real but small, so pay for it on strip days, not on the daily commute.',
  },
  {
    type: 'p',
    text: 'Dropping rear pressure from the OEM 32 psi to 28 psi for the launch widens the contact patch and adds roughly 8 percent to peak μ during the first two seconds, and it costs nothing. Put it back to 32 psi before you ride home, because at strip pressure the bike handles poorly above 100 km/h.',
  },
  {
    type: 'h2',
    text: 'Tier 2 (₹10,000 to ₹30,000): the mid-range',
  },
  {
    type: 'p',
    text: 'Most owners stop here. On top of Tier 1, this tier costs ₹21,400 (₹31,100 in total) and takes off roughly 0.30 seconds more, at ₹7,133 per tenth. Against stock, the bike is now roughly 0.65 seconds quicker: it runs a 12.85 instead of a 13.50.',
  },
  {
    type: 'table',
    rows: [
      ['Mod', 'ΔET (sim)', 'ΔTrap', 'Indian price', '₹/tenth', 'Street legal'],
      ['Powertronic Stage 1 ECU re-flash', '~0.22 s', '+3 km/h', '₹14,500', '~₹6,591', 'Yes (open-loop tune)'],
      ['TVS Eurogrip Protorq Extreme rear', '~0.10 s', '+1 km/h', '₹6,400', '~₹6,400', 'Yes'],
      ['Bybre slip-on muffler (legal, 95 dB)', '~0.05 s', '+1 km/h', '₹8,500', '~₹17,000', 'Yes'],
      ['Tier 2 only (incremental)', '~0.37 s', '+5 km/h', '₹29,400', '~₹7,946', '–'],
      ['Stock + Tier 1 + Tier 2', '~0.72 s', '+9 km/h', '₹39,100', '–', '–'],
    ],
  },
  {
    type: 'p',
    text: 'The Powertronic Stage 1 is the most installed performance mod on Indian KTM 390s. It is a piggyback ECU that intercepts the fuel-injection signal between the Bosch ME17 main ECU and the injectors. It adds 8 to 12 percent more fuel above 6,000 rpm and remaps the ignition advance for a slightly leaner cruise. On the LC4c it gains 1.5 to 2.5 hp at the top end on the dyno, depending on the tune revision, and the May 2026 Powertronic firmware also fixes the factory bog at 4,200 rpm. The OBD port still works, the bike still passes BS6 emissions, and the install is plug-and-play in under 30 minutes. The 0.22-second figure is the conservative average across Aamby Valley sim sweeps; some bikes pick up 0.30 seconds, some only 0.15.',
  },
  {
    type: 'p',
    text: 'The TVS Eurogrip Protorq Extreme is the most underrated mod on this list. It is an Indian-made sport-touring tire that grips clearly better than the OEM Metzeler Sportec M5 on dry launches, especially on strips that have not been freshly prepped: μ_peak at 50°C is about 1.18 against 1.10 for the OEM tire. It costs half as much as a Pirelli Rosso III with similar grip, which makes it the best value here. It lasts 12,000 to 14,000 km in mixed riding and is slightly worse in the wet than the Metzeler. The Bybre slip-on muffler is the legal option: 95 dB measured at 4,500 rpm, so it will not get you pulled over, and a KTM dealer can fit it with no recalibration. It is also the cheapest exhaust mod that moves the dyno needle. The louder ₹35,000 SC-Project slip-on adds roughly 0.04 seconds more for ₹26,500 more, a terrible cost per tenth.',
  },
  {
    type: 'callout',
    text: 'If you fit both, fit the exhaust first. The Powertronic Stage 1 changes the fuel map and the Bybre slip-on changes the exhaust back-pressure, so the re-flash has to allow for the new back-pressure curve. Done the other way round, the bike runs rich at low load and loses 6 to 8 percent in city fuel economy with no ET benefit. Indian Powertronic dealers know this; ask for the slip-on-aware revision when you book the install.',
  },
  {
    type: 'h2',
    text: 'Tier 3 (₹30,000 to ₹70,000): diminishing returns',
  },
  {
    type: 'p',
    text: 'Past ₹30,000, the cost per tenth roughly doubles with every extra ₹15,000. This tier is for owners who compete in regional drag events two or three times a year; most casual track-day riders should stop at Tier 2. Tier 3 adds ₹38,000 (₹68,500 in total) and roughly 0.25 seconds, at ₹15,200 per tenth for this tier alone. Against stock, the bike is now roughly 0.95 seconds quicker and runs a 12.55.',
  },
  {
    type: 'table',
    rows: [
      ['Mod', 'ΔET (sim)', 'ΔTrap', 'Indian price', '₹/tenth', 'Daily rideable'],
      ['SC-Project CR-T full system (titanium)', '~0.12 s', '+2 km/h', '₹52,000', '~₹43,333', 'Loud (105 dB)'],
      ['JT slipper clutch upgrade (replaces OEM)', '~0.06 s', '+0 km/h', '₹18,500', '~₹30,833', 'Yes'],
      ['Lightweight TZR-style alloy wheels (-2.8 kg rotational)', '~0.07 s', '+1 km/h', '₹38,000', '~₹54,286', 'Yes'],
      ['Tier 3 mix (full exhaust + slipper, skip wheels)', '~0.18 s', '+2 km/h', '₹70,500', '~₹39,167', '–'],
    ],
  },
  {
    type: 'p',
    text: 'The SC-Project CR-T full system replaces the whole stock exhaust from header to muffler, saves about 4.5 kg and frees another 2.5 to 3.5 hp beyond the slip-on figure. The cost per tenth is brutal (₹43,333 against ₹6,591 for the Powertronic), but the trap-speed gain is real and carries into a bigger build. At 105 dB the bike is track-only. Do not ride it on Indian roads: it will draw police attention in any city, and a noise-violation fine is ₹5,000 plus impoundment.',
  },
  {
    type: 'p',
    text: 'The JT slipper clutch is the mid-tier mod people overlook. The OEM RC 390 slipper has roughly 32 percent slip at peak engagement and the JT replacement about 18 percent. More torque reaches the rear wheel while the clutch slips at launch, and the engine loses less RPM on the shift from first to second. The gain is about 0.06 seconds. It is also the only mod on this list that makes the bike better to ride every day: smoother engagement, less clutch judder in stop-go traffic, and longer fade-free life on track. The ₹18,500 includes labour at an authorised KTM workshop.',
  },
  {
    type: 'p',
    text: 'Lightweight wheels are the worst return in this tier at ₹54,286 per tenth, yet most serious Indian drag 390s run them. Under acceleration, mass at the rim costs roughly 8× more than mass on the chassis, because it has to be both moved forward and spun up. Taking 2.8 kg off the rims does as much for acceleration as taking about 22 kg off the frame. The price is brutal, but the gain multiplies with every later mod instead of just adding to it. If you are building for a real 11-second pass, you need the wheels. If you are stopping at a 12.5, skip them.',
  },
  {
    type: 'h2',
    text: 'Tier 4 (above ₹70,000): drag prep',
  },
  {
    type: 'p',
    text: 'Past ₹70,000 you are no longer modding a street bike. You are building a strip bike that happens to be road-legal. Most of this tier is imported, and customs, GST and freight bring the landed cost to roughly 1.55× the USD retail price. Tier 4 adds ₹95,000 to ₹150,000 depending on your choices (₹165,000 to ₹220,000 in total) and roughly 0.40 to 0.60 seconds. The bike now runs an 11.95 to 12.15, close to the Fast Track Racing 11.342 record at last.',
  },
  {
    type: 'table',
    rows: [
      ['Mod', 'ΔET (sim)', 'ΔTrap', 'Indian price', '₹/tenth', 'Notes'],
      ['Mickey Thompson ET Drag DOT rear (drag-prep slick)', '~0.20 s', '+3 km/h', '₹24,000', '~₹12,000', 'Track-only'],
      ['Schnitz / Brock\'s stretched swingarm (+150 mm)', '~0.15 s', '+2 km/h', '₹62,000', '~₹41,333', 'Track-only'],
      ['Bazzaz / Rapid Bike full-control ECU + custom tune', '~0.10 s', '+2 km/h', '₹38,000', '~₹38,000', 'Track-only'],
      ['Stage 2 head + cam (port and polish, +1 mm lift)', '~0.12 s', '+3 km/h', '₹42,000', '~₹35,000', 'Track-only'],
      ['Full Tier 4 build', '~0.57 s', '+10 km/h', '₹166,000', '~₹29,123', '–'],
    ],
  },
  {
    type: 'p',
    text: 'Start Tier 4 with the drag rear tire. Without it the other mods do not work: a stretched swingarm without a sticky rear tire just gives you a longer wheelie. The Mickey Thompson ET Drag is a DOT-marked drag tire, so it is technically road-legal, but it is useless in the wet and wears through in under 300 km on the street. Treat it as track-only. Drag shops in Pune will fit and balance one for around ₹2,500 labour on top of the part price.',
  },
  {
    type: 'p',
    text: 'The stretched swingarm stops wheelies. A stock RC 390 with a sticky rear, a re-flash and a hard launch will lift the front wheel through first gear and lose roughly 0.4 seconds in the air. The Schnitz or Brock\'s 150 mm stretch moves the rear axle back, which lowers the centre-of-gravity ratio that causes the wheelie, so the rider can put full torque to the rear without lifting. Finding one is the hard part: only one or two Indian shops (Narhe in Pune, occasionally a Hyderabad fabricator) keep them in stock. A direct US import lands at roughly ₹62,000 including duty. It has to stay on the track, because the bike turns like a barge with the stretch fitted.',
  },
  {
    type: 'p',
    text: 'The Bazzaz or Rapid Bike full-control ECU replaces the Powertronic piggyback and overrides the main ECU. It can run separate fuel and ignition maps for each gear, auto-tune in closed loop with a wideband O2 sensor, run launch control, and pull timing in chosen gears to control wheelies. Indian dyno tuners (Powertec Bangalore, Performance Racing Store Delhi, RidersPlanet Mumbai) charge about ₹8,000 to ₹12,000 for a tune session on top of the part cost. The gain depends more on the tuner than on the part: a badly mapped Bazzaz can give back the whole Powertronic gain.',
  },
  {
    type: 'p',
    text: 'Stage 2 head work is as far as a single goes without a big-bore kit. A skilled head porter at one of three or four Indian shops will flow-bench the OEM head, port and polish the intake runners, and fit a +1 mm lift cam. For street use the LC4c valvetrain handles the extra lift on stock springs; for competition it needs uprated springs (₹4,500 extra). The power gain is roughly 4 to 6 hp on top of all earlier mods. This is also the mod that starts to wear the slipper clutch: past about 50 hp the OEM-spec assembly begins to glaze, so if you do strip days, plan a clutch swap every 8,000 km.',
  },
  {
    type: 'h2',
    text: 'The full ladder',
  },
  {
    type: 'p',
    text: 'Each tier stacked on stock, with a 70 kg rider in Aamby Valley November conditions:',
  },
  {
    type: 'table',
    rows: [
      ['Build', 'Total cost', 'Sim ET', 'Trap', 'ΔET vs stock', 'Effective ₹/tenth'],
      ['Stock RC 390', '₹0', '~13.50 s', '~166 km/h', '0 s', '–'],
      ['+ Tier 1 (cheap tenths)', '₹9,700', '~13.15 s', '~170 km/h', '−0.35 s', '~₹2,771'],
      ['+ Tier 2 (re-flash + grip)', '₹39,100', '~12.78 s', '~175 km/h', '−0.72 s', '~₹5,431'],
      ['+ Tier 3 (full exhaust + slipper)', '₹109,600', '~12.60 s', '~177 km/h', '−0.90 s', '~₹12,178'],
      ['+ Tier 4 (drag-prep)', '~₹275,600', '~12.03 s', '~187 km/h', '−1.47 s', '~₹18,748'],
      ['Fast Track Racing 11.342s build (estimated)', '~₹650,000', '11.342 s', '~196 km/h', '−2.16 s', '~₹30,093'],
    ],
  },
  {
    type: 'p',
    text: 'The first ₹39,100 buys 0.72 seconds, about a third of the whole gap to the Fast Track Racing record. The next ₹70,500 buys another 0.18, and the next ₹166,000 another 0.57. The last ₹374,400 buys roughly 0.69 more, but by then each tenth costs ₹54,260. Even so, the public mod ladder never quite reaches the record. A serious 11.3-second pass needs custom head work, custom-ratio gearboxes, drag-only chassis changes, and a rider with hundreds of practice launches. Money buys the parts; only practice buys the last two tenths.',
  },
  {
    type: 'h2',
    text: 'Which build for which rider',
  },
  {
    type: 'p',
    text: 'Where to stop depends on how you use the bike.',
  },
  {
    type: 'p',
    text: 'A weekend rider who takes the bike to the strip twice a year should stop at Tier 1 plus one Tier 2 mod, most likely the Powertronic Stage 1, because it helps daily riding as much as strip times. That is ₹24,200 for about 0.57 seconds, or ₹4,246 per tenth. The bike stays street-legal, passes emissions, and runs a 12.93 on a clean strip day.',
  },
  {
    type: 'p',
    text: 'A serious track-day rider who does Valley Run Summer and Winter plus one other regional event should do all of Tier 1 and Tier 2, plus the JT slipper clutch from Tier 3. That is ₹57,600 for about 0.78 seconds, or ₹7,385 per tenth, and the bike runs a 12.72. It is loud enough to need a strip-only muffler swap, but it is road-legal again once the OEM exhaust goes back on for the ride home.',
  },
  {
    type: 'p',
    text: 'A competitive amateur chasing the 11-second window adds the rest of Tier 3 (full SC-Project and lightweight wheels), then the drag rear tire, the stretched swingarm and the full-control ECU from Tier 4. That is roughly ₹275,000 for about 1.47 seconds, or ₹18,748 per tenth, and the bike runs a 12.03. By now the chassis is track-only, and you need a separate street RC 390 or another bike for daily use.',
  },
  {
    type: 'p',
    text: 'Each tier roughly doubles the cost per tenth. The same happens on any bike when you push a fixed power-to-weight design for more. The LC4c was designed as a 43.5 hp commuter engine, and each step toward 60 hp takes more work and costs more than the last. The Duke 390 follows the same ladder: the body differs, but the powertrain mods carry over line for line.',
  },
  {
    type: 'h2',
    text: 'What the ladder leaves out',
  },
  {
    type: 'p',
    text: 'Three kinds of mod show up in YouTube build videos but did not make the ladder. Big-bore kits can take the 373.3 cc engine to roughly 430 cc with oversize pistons and machined cylinder sleeves, but the parts cost ₹65,000 to ₹80,000 in India, and the reliability penalty over 6,000 km of street use makes the cost per tenth worse than spending the same on Tier 4 bolt-ons. A dry-shot 15 to 20 hp nitrous kit costs ₹35,000 to ₹50,000 plus bottle refills, but the LC4c bottom end is not built for it, and engine life drops sharply after 50 to 100 strip passes. A turbo or supercharger conversion is possible, but the Indian aftermarket has no plug-and-play kit for the LC4c, so every build is custom at ₹2 to 3 lakh, with no warranty. All three are in the MotoQuant parts catalog with simulated ET impact. None of them makes the best cost-per-tenth ladder for the 11.5-12.5 second window most amateur builds aim for.',
  },
  {
    type: 'p',
    text: 'For the mods that did make it, the MotoQuant simulator at motoquant.in builds the same ladder for your bike year, rider weight, home strip and choice of parts. It shows the cost-per-tenth ranking each time you toggle a part, sweeps ambient conditions, and takes a Dragy timeslip from your own runs to tighten the prediction beyond the current ±0.4-second cluster bias band.',
  },
  {
    type: 'callout',
    text: 'Three caveats. Every ET in this post sits inside the ±0.4-second bias band for the mid-twin-300-500 cluster; a real Dragy timeslip from your bike would tighten the prediction. Indian aftermarket prices change every quarter, and these are from the May 2026 pricing refresh, so allow ±15 percent when you actually buy. And any mod can fail under strip-day stress; the ladder assumes parts work as advertised and tuners do their job. Tier 1 almost never fails, while Tier 4 mods often need more tuning sessions before they deliver their full headline gain.',
  },
  {
    type: 'h2',
    text: 'Run your own ladder',
  },
  {
    type: 'p',
    text: 'A stock KTM RC 390 in India is a 13.5-second quarter-mile bike. The first ₹40,000 of mods buys 0.72 seconds and keeps it street-legal. The next ₹70,000 buys 0.18 seconds and starts to make it track-only. The rest of the gap to the Fast Track Racing 11.342-second record costs ₹500,000 and a team. Where you stop depends on how many strip days you do in a year.',
  },
  {
    type: 'p',
    text: 'The simulator at motoquant.in/simulator runs the same physics that produced every ET in this post. It works with any of the 546 parts in the catalog and any of the 20 seeded venues, and sweeps rider weight, ambient temperature, density altitude and tire compound. The build page shows the parts-ROI ranking (cost per tenth, ET change, trap change, compatibility warning), and the Dragy upload lines your own timeslip up against the simulation. Start with the stock RC 390 and Tier 1. That is the answer for 80 percent of owners, and it costs under ₹10,000 to check.',
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
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Best mods for KTM RC 390 in India: a cost-per-tenth ladder
          </h1>
          <div className="text-sm text-white/60 mb-12">
            22 May 2026 · 13 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        <div className="max-w-2xl mx-auto mt-16 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Build your own RC 390 ladder</div>
            <div className="text-white/60 text-sm">
              Sweep rider weight, density altitude, sprocket, ECU re-flash, exhaust, tire compound and any of the 546 parts in the catalog. The simulator shows the cost per tenth on every part toggle.
            </div>
          </div>
          <Link
            href="/simulator?bike=ktm-rc-390&venue=aamby-valley"
            className="shrink-0 px-5 py-2.5 bg-brand-orange text-on-accent font-display font-bold rounded-lg text-sm hover:bg-brand-orangeLight transition-colors"
          >
            Open the simulator →
          </Link>
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
                KTM Duke 390 vs RC 390: quarter-mile physics at Aamby Valley
              </Link>:
              same engine, two tenths apart, and where the gap comes from.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/pulsar-ns400z-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Pulsar NS400Z quarter-mile physics (and why an RC 390 still wins)
              </Link>:
              the closest rival in the segment, run through the same cost-per-tenth ladder.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/the-physics-of-a-perfect-launch"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                The physics of a perfect launch
              </Link>:
              clutch slip, weight transfer, and the first 60 feet that decide most of the 390-class quarter-mile.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/how-to-tune-for-aamby-valley-in-november"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to tune for Aamby Valley in November
              </Link>:
              the venue conditions used for every sim in this post, plus the density altitude math.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/how-the-motoquant-physics-engine-works"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How the MotoQuant physics engine works
              </Link>:
              the 15-sub-model RK4 engine, the cluster bias bands, and what the residual error means.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>:
              RC 390, Duke 390, NS400Z, Apache RR 310, Dominar 400, and 390+ other bikes with full spec sheets and OEM tire fitments.
            </li>
          </ul>
        </div>
      </article>

      <SiteFooter />
    </div>
  );
}
