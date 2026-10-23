import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';
import { REPO_URL } from '../../../lib/site';

const SLUG = 'pulsar-ns400z-quarter-mile-physics';
const TITLE = 'Bajaj Pulsar NS400Z Quarter-Mile Physics (and Why an RC 390 Still Wins)';
const DESCRIPTION =
  'Bajaj Pulsar NS400Z quarter-mile time and 0-100 in India: MotoQuant simulates the NS400Z at roughly 13.8s ET and 158 km/h trap at Aamby Valley, lining up against the BikeWale-tested 6.4s 0-100. A stock KTM RC 390 still beats it by 0.3s. Physics-based explanation of the 23 kg, the gearing, and the Cd the press release ignored — plus three cost-per-tenth mods under ₹20,000.';

export const metadata = {
  title: 'Pulsar NS400Z Quarter Mile & 0-100 (India) vs RC 390 — MotoQuant',
  description: DESCRIPTION,
  keywords: [
    'pulsar ns400z quarter mile',
    'pulsar ns400z 0-100',
    'ns400z drag time india',
    'pulsar ns400z vs rc 390',
    'bajaj ns400z top speed',
    'ns400z mods cost per tenth',
    'pulsar ns400z review india',
    'first 400cc indian bike',
    'ns400z vs duke 390',
    'ns400z acceleration india',
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `https://motoquant.in/blog/${SLUG}`,
    type: 'article',
    publishedTime: '2026-05-18T00:00:00Z',
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: 'The Bajaj Pulsar NS400Z is the first ever 400cc Pulsar and the first Indian-made 400 single in this price bracket. The press kit makes a lot of the 40 hp, the slipper clutch, and the ride-by-wire throttle. MotoQuant simulates the NS400Z at roughly 13.8 seconds and 158 km/h trap under matched Aamby Valley conditions. The KTM RC 390 — same 89 × 60 mm bore and stroke, same 12.5:1 compression, same Bajaj-built engine architecture — runs about 13.5 seconds in the simulator at the same venue. The NS400Z is a 50,000-rupee cheaper bike with a slipper clutch and more torque on tap, but on a strip, a stock RC 390 still beats it by three tenths. Here is exactly where those tenths go.',
  },
  {
    type: 'h2',
    text: 'What the NS400Z Actually Is',
  },
  {
    type: 'p',
    text: 'The Pulsar NS400Z launched in May 2024 at an ex-showroom price of ₹1.85 lakh. It uses the same 373.3 cc liquid-cooled DOHC 4-valve single that powers the KTM 390 family — the engine is built at Bajaj\'s Chakan plant for both brands. Bore is 89.0 mm, stroke is 60.0 mm, compression is 12.5:1. Bajaj tunes the engine to 40 hp at 8,800 rpm and 35 Nm at 6,500 rpm — about 3.5 hp and 2 Nm down on the RC 390\'s 43.5 hp / 37 Nm spec, but with a flatter mid-range and a longer service interval target.',
  },
  {
    type: 'p',
    text: 'The bike sits on a perimeter steel frame derived from the NS200, gets USD forks at the front, a monoshock at the rear, and a 320 mm petal disc with a Bybre radial caliper. Ride modes (Road, Rain, Off-Road, Sport), a slipper clutch, an assist clutch, dual-channel ABS, and Bluetooth-connected instrumentation come standard. Kerb mass is 174 kg, dry mass is 172 kg per MotoQuant\'s catalog entry. The bike runs a 110/70-17 front and 140/70-17 rear on cast alloy wheels — slightly skinnier than the RC 390\'s 110/70-17 and 150/60-17 fitment.',
  },
  {
    type: 'h2',
    text: 'Stock Sim Numbers at Aamby Valley',
  },
  {
    type: 'p',
    text: 'Running the NS400Z through the simulator at matched Aamby Valley November conditions — density altitude near 1,100 m, 22°C ambient, dry concrete with the OEM MRF rear tire at μ_peak ≈ 1.08, 70 kg rider in stock upright tuck — produces these numbers:',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'NS400Z (sim)', 'RC 390 (sim, same venue)'],
      ['Quarter-mile ET', '~13.8 s', '~13.5 s'],
      ['Trap speed', '~158 km/h', '~166 km/h'],
      ['60-foot time', '~2.30 s', '~2.21 s'],
      ['1/8-mile ET', '~8.95 s', '~8.75 s'],
      ['Top gear at trap', '5th, ~7,600 rpm', '5th, ~7,400 rpm'],
      ['Cluster bias band', '±0.40 s mid-twin-300-500', '±0.40 s mid-twin-300-500'],
    ],
  },
  {
    type: 'p',
    text: 'Both ETs sit inside MotoQuant\'s mid-twin-300-500 cluster bias band of about ±0.4 seconds. The relative gap (NS400Z three tenths slower, 8 km/h less trap, one tenth slower at the 60-foot) is stable across rider weight, ambient temperature, and density altitude sweeps. A single instrumented Dragy timeslip from either bike would tighten the prediction by a real margin, and we will fold that into the calibrator the moment it lands in the inbox. Until then, the simulator is the best public stock-tune number for the NS400Z that exists.',
  },
  {
    type: 'callout',
    text: 'Counter-intuitive but defensible: the cheaper, heavier, larger Pulsar NS400Z is slower than the lighter, sharper, more expensive KTM RC 390 across every split on a stock-tune strip run. The press release talks about price and torque. The simulator talks about mass, gearing, and aerodynamics.',
  },
  {
    type: 'h2',
    text: 'Where the Three Tenths Live',
  },
  {
    type: 'p',
    text: 'The NS400Z and the RC 390 share an engine. They do not share much else. Three differences explain almost the entire ET gap between them:',
  },
  {
    type: 'table',
    rows: [
      ['Spec', 'NS400Z', 'RC 390', 'ET cost on NS400Z'],
      ['Dry mass', '172 kg', '149 kg', '~0.15 s'],
      ['Cd × frontal area', '0.78 × 0.55 = 0.429', '0.68 × 0.41 = 0.279', '~0.10 s'],
      ['First-gear ratio (overall)', '2.714 × 2.667 primary × 2.67 final = 19.3:1', '3.230 × 2.667 × 2.81 final = 24.2:1', '~0.05 s'],
      ['Peak power', '40 hp @ 8,800 rpm', '43.5 hp @ 8,000 rpm', '~0.05 s'],
      ['Tire width (rear)', '140/70-17', '150/60-17', '~0.02 s (RC 390 launches slightly better)'],
    ],
  },
  {
    type: 'p',
    text: 'The mass gap is the biggest single contributor. 23 kg of dry mass plus a rider puts the NS400Z at roughly 244 kg total system mass versus the RC 390\'s 219 kg. Power-to-weight is 165 hp/tonne on the NS400Z and 198 hp/tonne on the RC 390 — a 17 percent advantage to the KTM that maps onto roughly 0.15 seconds of ET in the simulator. That gap is largest in the first 60 feet where the engine is fighting inertia, and shrinks but does not disappear by the trap.',
  },
  {
    type: 'p',
    text: 'Aerodynamics is the second biggest contributor. The NS400Z is a naked streetfighter with upright bars, a wide tank, and a rider seated bolt upright; the RC 390 is a clip-on fully-faired sport bike with a rider tucked into the bubble. The simulator pulls Cd 0.78 and frontal area 0.55 m² for the NS400Z (giving Cd × A = 0.429) and Cd 0.68 / 0.41 m² for the RC 390 (Cd × A = 0.279). That is a 54 percent higher drag area on the Pulsar, which costs about 8 km/h of trap speed and roughly 0.10 seconds of ET by the time the bike is past the 1/8-mile mark.',
  },
  {
    type: 'p',
    text: 'Gearing is the most interesting one. The NS400Z has a taller first gear (2.714 vs the RC 390\'s 3.230) and a shorter final-drive ratio (15/40 = 2.67 vs the RC 390\'s 16/45 = 2.81). The net first-gear overall reduction is 19.3:1 on the NS400Z versus 24.2:1 on the RC 390 — meaning the RC 390 multiplies engine torque 25 percent more aggressively off the line. Bajaj likely tuned the NS400Z for highway cruising and clutch life rather than strip launches; the RC 390 is geared to make the most of every newton-metre.',
  },
  {
    type: 'h2',
    text: 'Where the NS400Z Actually Wins',
  },
  {
    type: 'p',
    text: 'The simulator is brutal but the NS400Z is not a bad bike. On metrics the strip does not measure, it walks away from the RC 390. The slipper clutch is meaningfully better at preventing rear-wheel chatter on aggressive downshifts. The torque curve is broader and flatter — the NS400Z makes 95 percent of peak torque from 4,500 to 7,500 rpm, where the RC 390 has a steeper curve that peaks harder but tapers earlier. The riding position is daily-commute-friendly in a way that no clip-on sport bike will ever be. The cluster is wider, the seat is bigger, the suspension is softer.',
  },
  {
    type: 'p',
    text: 'At ₹1.85 lakh ex-showroom, the NS400Z is also roughly ₹1.30 lakh cheaper than the RC 390\'s ₹3.18 lakh sticker. For a buyer choosing between the two, the NS400Z gives up three tenths of quarter-mile ET in exchange for keeping 1.3 lakh in the bank. The "first Indian 400" headline is also genuine — Bajaj is shipping a 400cc DOHC liquid-cooled single at a price point no global brand can hit in this market. That matters for the segment, even if it does not matter at the strip.',
  },
  {
    type: 'h2',
    text: 'Three Mods That Close the Gap',
  },
  {
    type: 'p',
    text: 'MotoQuant\'s parts-ROI engine ranks the top three NS400Z mods under ₹20,000 by cost-per-tenth at Indian retail. All three are available off the shelf in 2026; pricing is from the May 2026 pricing-refresh pass against Indian aftermarket retailers (Store4Riders, RidersPlanet, Performance Racing Store, KustomHub).',
  },
  {
    type: 'table',
    rows: [
      ['Mod', 'ΔET (sim)', 'ΔTrap', 'Indian price', '₹/tenth'],
      ['Front sprocket drop (15F → 14F)', '~0.18 s', '+2 km/h', '₹900', '~₹500'],
      ['Sticky rear tire (TVS Eurogrip Protorq Extreme)', '~0.15 s', '+1 km/h', '₹6,200', '~₹4,100'],
      ['Powertronic Stage 1 ECU re-flash', '~0.20 s', '+3 km/h', '₹14,500', '~₹7,250'],
      ['Total (sprocket + tire + ECU)', '~0.50 s', '+6 km/h', '₹21,600', '—'],
    ],
  },
  {
    type: 'p',
    text: 'The sprocket swap is the cheapest tenth on the bike by an order of magnitude. Dropping one tooth at the front shortens overall gearing by roughly 6.7 percent, which keeps the engine higher in its power band through the first three gears — exactly where the NS400Z is currently giving up time to the RC 390. The Eurogrip Protorq Extreme is a step up from the OEM MRF rear in compound stickiness; on a tight Indian strip with patchy concrete it buys back most of the launch-grip gap the NS400Z has against an RC 390 on Metzeler Sportec M5 rubber. The Powertronic Stage 1 re-flash unlocks an additional 1.5–2 hp at the top of the rev band by relaxing Bajaj\'s conservative OEM map; you also get sharper throttle response that matters at the strip but matters even more on commute days.',
  },
  {
    type: 'p',
    text: 'After all three mods, MotoQuant simulates the NS400Z at roughly 13.3 seconds and 164 km/h trap — quicker than a stock RC 390 by 0.2 seconds. Total spend is ₹21,600 against an RC 390 retail premium of ₹1.30 lakh. That is the actual value calculation: a modded NS400Z runs the RC 390 down for 17 percent of the price gap. Add another ₹35,000 of mods to the RC 390 (Akrapovic slip-on, K&N filter, sprocket drop) and it pulls back ahead; both bikes scale roughly together past that point.',
  },
  {
    type: 'callout',
    text: 'Three caveats. First, every simulator number in this post sits inside the mid-twin-300-500 cluster bias band of ±0.4 seconds. A real Dragy timeslip would tighten the prediction. Second, Indian aftermarket pricing shifts every quarter — the parts-ROI engine pulls live retailer prices where it can and falls back to formula-based landing-cost math (USD × 84 × 1.30 import duty × 1.18 GST + ₹1,500 freight) where it cannot. Third, the NS400Z launched in May 2024; service-history data and long-term durability comparisons against the RC 390 are still being written.',
  },
  {
    type: 'h2',
    text: 'Aamby Valley vs MMRT vs Your Local Strip',
  },
  {
    type: 'p',
    text: 'The numbers above are for Aamby Valley in November — roughly 1,100 m density altitude, 22°C ambient, dry concrete with a μ_peak of about 1.08. At lower-altitude strips the picture sharpens for the NS400Z. At MMRT (Chennai, sea level, 30°C, μ_peak ≈ 1.05 on the better days) the simulator drops the NS400Z to roughly 13.5 seconds and 161 km/h trap — gaining about 0.3 s of ET because the engine is making peak power again without the 1,100 m density-altitude penalty. The RC 390 also gains, but slightly less in relative terms because its tighter gearing was already extracting more from the available power.',
  },
  {
    type: 'p',
    text: 'At a high-altitude venue — for example Leh at 3,500 m DA — the gap between the two bikes shrinks because both are losing power at roughly the same percentage and the lighter RC 390\'s mass advantage matters less when both bikes are making 25 percent less power. Aerodynamic drag is also lower (thinner air), which disproportionately helps the draggier NS400Z. The simulator predicts the gap shrinks to about 0.15 seconds at Leh. Nobody runs drag races at Leh, but it is a useful sanity check on the physics.',
  },
  {
    type: 'h2',
    text: 'Run Your Own Numbers',
  },
  {
    type: 'p',
    text: 'The honest summary: the Pulsar NS400Z is a quick bike for its price. It is also slower than a stock KTM RC 390 by about three tenths of quarter-mile ET, because the NS400Z is 23 kg heavier, 54 percent draggier, and geared for highway cruising rather than strip launches. Two of those three differences are unfixable without major surgery; one (the gearing) is fixable with a ₹900 sprocket. The cheapest path from "factory NS400Z" to "faster than a factory RC 390 at Aamby Valley" is ₹21,600. The cheapest path to "factory RC 390" is to buy an RC 390 for ₹1.30 lakh more than the NS400Z.',
  },
  {
    type: 'p',
    text: 'The MotoQuant simulator at motoquant.in lets you side-by-side the NS400Z and the RC 390, swap rider weight, density altitude, ambient temperature, tire compound, and any of the 593 parts in the catalog. You can answer the actual question a buyer cares about — "for my budget of X and my home strip Y, which of these two bikes runs faster, and what do I need to do to get there" — without trusting a YouTube comparison video or a press release.',
  },
  {
    type: 'p',
    text: 'And the moment a real Dragy timeslip from a stock NS400Z lands in the calibrator (which we expect within weeks of this being published), the simulator will fold it in and tighten the prediction. The current ±0.4 second cluster bias band is the honest uncertainty number until that data exists; it is wider than the gap to the RC 390, but the relative ordering across the cluster is stable. The NS400Z is third or fourth quickest in its segment behind the RC 390 and the Duke 390, ahead of the Apache RR 310 and well ahead of the Dominar 400. That order does not change across reasonable sweeps of the input parameters.',
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
          datePublished: '2026-05-18',
        })}
      />
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          <div className="flex flex-wrap gap-2 mb-6">
            {['Bajaj', 'Pulsar NS400Z', 'KTM RC 390', 'Indian 400cc', 'physics'].map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Pulsar NS400Z Quarter-Mile Physics (and Why an RC 390 Still Wins)
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
            18 May 2026 · 12 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        <div className="max-w-2xl mx-auto mt-16 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Simulate the NS400Z vs RC 390 head-to-head</div>
            <div className="text-white/60 text-sm">Pick both bikes, sweep rider weight, swap mods, change venue conditions, and see the ET delta before you spend a rupee on either one.</div>
          </div>
          <Link href="/simulator" className="shrink-0 px-5 py-2.5 bg-brand-orange text-black font-display font-bold rounded-lg text-sm hover:bg-brand-orangeLight transition-colors">Run sim →</Link>
        </div>

        <div className="max-w-2xl mx-auto mt-16">
          <h3 className="font-display font-bold text-lg text-white mb-4">Related reading</h3>
          <ul className="text-sm text-white/70 space-y-2">
            <li>
              ·{' '}
              <Link href="/blog/pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                Pulsar NS200 vs Apache RTR 200 4V: Which Wins the Quarter Mile?
              </Link>{' '}
              — the same physics one displacement class down, with the same Bajaj-vs-rival framing.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/why-your-r15-wont-hit-14s" className="text-brand-accent hover:text-brand-orange transition-colors">
                Why Your R15 Won&apos;t Hit 14s (And What Will Actually Help)
              </Link>{' '}
              — gearing, traction, and the small-cc traps the press release never mentions.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-to-tune-for-aamby-valley-in-november" className="text-brand-accent hover:text-brand-orange transition-colors">
                How to Tune for Aamby Valley in November
              </Link>{' '}
              — the venue conditions used for the simulation in this post, plus the DA penalty math.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-the-motoquant-physics-engine-works" className="text-brand-accent hover:text-brand-orange transition-colors">
                How the MotoQuant Physics Engine Works
              </Link>{' '}
              — what is inside the simulator that produced these numbers and what the cluster bias bands mean.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>{' '}
              — NS400Z, RC 390, Duke 390, Dominar 400, Apache RR 310, and 390+ other bikes with full spec sheets and OEM tire fitments.
            </li>
            <li>
              ·{' '}
              <a
                href={REPO_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                MotoQuant on GitHub
              </a>{' '}
              — free and open source: audit the physics behind every number in this post, or run it yourself.
            </li>
          </ul>
        </div>
      </article>

      <SiteFooter />
    </div>
  );
}
