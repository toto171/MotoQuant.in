import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema, OG_IMAGE } from '../../StructuredData';
import PostBikeLinks from '../../../components/PostBikeLinks';

const SLUG = 'pulsar-ns400z-quarter-mile-physics';
const TITLE = 'Bajaj Pulsar NS400Z quarter-mile physics (and why an RC 390 still wins)';
const DESCRIPTION =
  'MotoQuant simulates the Bajaj Pulsar NS400Z at roughly 13.8s ET and a 158 km/h trap at Aamby Valley. A stock KTM RC 390 still beats it by 0.3s. Here is why.';

export const metadata = {
  title: 'Pulsar NS400Z quarter mile & 0-100 (India) vs RC 390',
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
    images: [OG_IMAGE],
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: 'The Bajaj Pulsar NS400Z is the first 400cc Pulsar and the first Indian-made 400 single in its price bracket. The press kit leans on the 40 hp, the slipper clutch and the ride-by-wire throttle. MotoQuant simulates the NS400Z at roughly 13.8 seconds and a 158 km/h trap under matched Aamby Valley conditions. The KTM RC 390 (same 89 × 60 mm bore and stroke, same 12.5:1 compression, same Bajaj-built engine architecture) runs about 13.5 seconds in the simulator at the same venue. The NS400Z is 50,000 rupees cheaper and has a slipper clutch and more torque on tap, but on a strip a stock RC 390 still beats it by three tenths. Here is where those tenths go.',
  },
  {
    type: 'h2',
    text: 'What the NS400Z is',
  },
  {
    type: 'p',
    text: 'The Pulsar NS400Z launched in May 2024 at ₹1.85 lakh ex-showroom. It uses the same 373.3 cc liquid-cooled DOHC 4-valve single as the KTM 390 family; Bajaj builds the engine at its Chakan plant for both brands. Bore is 89.0 mm, stroke 60.0 mm, compression 12.5:1. Bajaj tunes it to 40 hp at 8,800 rpm and 35 Nm at 6,500 rpm, about 3.5 hp and 2 Nm down on the RC 390\'s 43.5 hp / 37 Nm, but with a flatter mid-range and a longer target service interval.',
  },
  {
    type: 'p',
    text: 'The bike uses a perimeter steel frame derived from the NS200, with USD forks at the front, a monoshock at the rear, and a 320 mm petal disc with a Bybre radial caliper. Ride modes (Road, Rain, Off-Road, Sport), a slipper clutch, an assist clutch, dual-channel ABS and Bluetooth-connected instruments are standard. Kerb mass is 174 kg; dry mass is 172 kg per MotoQuant\'s catalog entry. It runs a 110/70-17 front and 140/70-17 rear on cast alloy wheels, slightly narrower than the RC 390\'s 110/70-17 and 150/60-17.',
  },
  {
    type: 'h2',
    text: 'Stock sim numbers at Aamby Valley',
  },
  {
    type: 'p',
    text: 'The simulator\'s numbers for the NS400Z under matched Aamby Valley November conditions (density altitude near 1,100 m, 22°C ambient, dry asphalt, OEM MRF rear tire at μ_peak ≈ 1.08, 70 kg rider in a stock upright tuck):',
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
    text: 'Both ETs sit inside MotoQuant\'s mid-twin-300-500 cluster bias band of about ±0.4 seconds. The relative gap (NS400Z three tenths slower, 8 km/h less trap speed, one tenth slower at the 60-foot) holds across sweeps of rider weight, ambient temperature and density altitude. One instrumented Dragy timeslip from either bike would tighten the prediction noticeably, and the "Submit a timeslip" form is how to send one. Until then, this simulation is the best public stock-tune number there is for the NS400Z.',
  },
  {
    type: 'callout',
    text: 'It is surprising, but the physics holds: on a stock-tune strip run, the cheaper, heavier, larger Pulsar NS400Z is slower at every split than the lighter, sharper, more expensive KTM RC 390. The press release talks about price and torque. The simulator looks at mass, gearing and aerodynamics.',
  },
  {
    type: 'h2',
    text: 'Where the three tenths go',
  },
  {
    type: 'p',
    text: 'The NS400Z and the RC 390 share an engine and not much else. Three differences explain almost all of the ET gap between them:',
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
    text: 'Mass is the biggest single factor. The NS400Z carries 23 kg more dry mass; with a rider, that puts it at roughly 244 kg total against the RC 390\'s 219 kg. Power-to-weight is 165 hp/tonne on the NS400Z and 198 hp/tonne on the RC 390, a 17 percent advantage to the KTM that the simulator turns into roughly 0.15 seconds of ET. The gap is largest in the first 60 feet, where the engine is fighting inertia, and it shrinks but does not disappear by the trap.',
  },
  {
    type: 'p',
    text: 'Aerodynamics comes second. The NS400Z is a naked streetfighter with upright bars, a wide tank and the rider sitting bolt upright; the RC 390 is a fully faired sport bike with clip-ons and the rider tucked behind the bubble. The simulator uses Cd 0.78 and a frontal area of 0.55 m² for the NS400Z (Cd × A = 0.429) and Cd 0.68 / 0.41 m² for the RC 390 (Cd × A = 0.279). The Pulsar\'s drag area is 54 percent higher, which costs about 8 km/h of trap speed and roughly 0.10 seconds of ET by the time the bike is past the 1/8-mile mark.',
  },
  {
    type: 'p',
    text: 'Gearing is the most interesting of the three. The NS400Z has a taller first gear (2.714 vs the RC 390\'s 3.230) and a shorter final-drive ratio (15/40 = 2.67 vs the RC 390\'s 16/45 = 2.81). Overall first-gear reduction is 19.3:1 on the NS400Z against 24.2:1 on the RC 390, so the RC 390 multiplies engine torque 25 percent more off the line. Bajaj probably tuned the NS400Z for highway cruising and clutch life rather than strip launches; the RC 390 is geared to make the most of every newton-metre.',
  },
  {
    type: 'h2',
    text: 'Where the NS400Z wins',
  },
  {
    type: 'p',
    text: 'The simulator is harsh, but the NS400Z is not a bad bike. On things the strip does not measure, it beats the RC 390 easily. The slipper clutch does a noticeably better job of stopping rear-wheel chatter on hard downshifts. The torque curve is broader and flatter: the NS400Z makes 95 percent of peak torque from 4,500 to 7,500 rpm, while the RC 390\'s steeper curve peaks harder but tails off earlier. The riding position suits a daily commute in a way no clip-on sport bike can. The cluster is wider, the seat is bigger and the suspension is softer.',
  },
  {
    type: 'p',
    text: 'At ₹1.85 lakh ex-showroom, the NS400Z is also roughly ₹1.30 lakh cheaper than the RC 390\'s ₹3.18 lakh sticker. A buyer who picks the NS400Z over the RC 390 gives up three tenths of quarter-mile ET and keeps 1.3 lakh in the bank. The "first Indian 400" headline is also true: Bajaj is selling a 400cc DOHC liquid-cooled single at a price no global brand can match in this market. That matters for the segment, even if it does not matter at the strip.',
  },
  {
    type: 'h2',
    text: 'Three mods that close the gap',
  },
  {
    type: 'p',
    text: 'MotoQuant\'s parts-ROI engine ranks the top three NS400Z mods under ₹20,000 by cost per tenth at Indian retail prices. All three are available off the shelf in 2026. Prices come from the May 2026 price refresh against Indian aftermarket retailers (Store4Riders, RidersPlanet, Performance Racing Store, KustomHub).',
  },
  {
    type: 'table',
    rows: [
      ['Mod', 'ΔET (sim)', 'ΔTrap', 'Indian price', '₹/tenth'],
      ['Front sprocket drop (15F → 14F)', '~0.18 s', '+2 km/h', '₹900', '~₹500'],
      ['Sticky rear tire (TVS Eurogrip Protorq Extreme)', '~0.15 s', '+1 km/h', '₹6,200', '~₹4,100'],
      ['Powertronic Stage 1 ECU re-flash', '~0.20 s', '+3 km/h', '₹14,500', '~₹7,250'],
      ['Total (sprocket + tire + ECU)', '~0.50 s', '+6 km/h', '₹21,600', '–'],
    ],
  },
  {
    type: 'p',
    text: 'The sprocket swap is the cheapest tenth on the bike by an order of magnitude. Dropping one tooth at the front shortens overall gearing by roughly 6.7 percent, which keeps the engine higher in its power band through the first three gears, exactly where the NS400Z now loses time to the RC 390. The Eurogrip Protorq Extreme has a stickier compound than the OEM MRF rear. On a tight Indian strip with patchy asphalt, it wins back most of the launch-grip gap to an RC 390 on Metzeler Sportec M5 tires. The Powertronic Stage 1 re-flash adds 1.5–2 hp at the top of the rev range by relaxing Bajaj\'s conservative OEM map. It also sharpens throttle response, which helps at the strip and helps even more on commute days.',
  },
  {
    type: 'p',
    text: 'After all three mods, MotoQuant simulates the NS400Z at roughly 13.3 seconds and a 164 km/h trap, 0.2 seconds quicker than a stock RC 390. The total spend is ₹21,600, against an RC 390 price premium of ₹1.30 lakh. That is the real value calculation: a modded NS400Z beats a stock RC 390 for 17 percent of the price gap.',
  },
  {
    type: 'p',
    text: 'Spend another ₹35,000 on the RC 390 (Akrapovic slip-on, K&N filter, sprocket drop) and it pulls back ahead; past that point both bikes improve at roughly the same rate.',
  },
  {
    type: 'callout',
    text: 'Three caveats. First, every simulator number in this post sits inside the mid-twin-300-500 cluster bias band of ±0.4 seconds; a real Dragy timeslip would tighten the prediction. Second, Indian aftermarket prices change every quarter. The parts catalog uses retailer prices where it has them and falls back to a landing-cost formula (USD × 84 × 1.30 import duty × 1.18 GST + ₹1,500 freight) where it does not. Third, the NS400Z launched in May 2024, so service-history data and long-term durability comparisons with the RC 390 do not exist yet.',
  },
  {
    type: 'h2',
    text: 'Aamby Valley vs MMRT vs your local strip',
  },
  {
    type: 'p',
    text: 'The numbers above are for Aamby Valley in November: roughly 1,100 m density altitude, 22°C ambient, dry asphalt with a μ_peak of about 1.08. At lower-altitude strips the NS400Z looks better. At MMRT (Chennai, sea level, 30°C, μ_peak ≈ 1.05 on the better days) the simulator puts the NS400Z at roughly 13.5 seconds and a 161 km/h trap, about 0.3 s quicker, because the engine makes peak power again without the 1,100 m density-altitude penalty. The RC 390 gains too, but slightly less in relative terms, because its shorter gearing was already getting more from the available power.',
  },
  {
    type: 'p',
    text: 'At a high-altitude venue (for example Leh at 3,500 m DA), the gap between the two bikes shrinks. Both lose power by roughly the same percentage, and the RC 390\'s lower mass matters less when both bikes are making 25 percent less power. Thinner air also means less aerodynamic drag, which helps the draggier NS400Z more. The simulator predicts the gap shrinks to about 0.15 seconds at Leh. Nobody runs drag races at Leh, but it is a useful check on the physics.',
  },
  {
    type: 'h2',
    text: 'Run your own numbers',
  },
  {
    type: 'p',
    text: 'The Pulsar NS400Z is quick for its price. It is also about three tenths slower than a stock KTM RC 390 over the quarter mile, because it is 23 kg heavier, 54 percent draggier, and geared for highway cruising rather than strip launches. Two of those three cannot be fixed without major work; the gearing can be fixed with a ₹900 sprocket. The cheapest route from a factory NS400Z to beating a factory RC 390 at Aamby Valley costs ₹21,600. The cheapest route to a factory RC 390 is to buy one, for ₹1.30 lakh more than the NS400Z.',
  },
  {
    type: 'p',
    text: 'The MotoQuant simulator at motoquant.in lets you run the NS400Z and the RC 390 side by side and change rider weight, density altitude, ambient temperature, tire compound and any of the 546 parts in the catalog. That answers the question a buyer actually has ("for my budget of X and my home strip Y, which of these two bikes runs faster, and what do I need to do to get there") without relying on a YouTube comparison video or a press release.',
  },
  {
    type: 'p',
    text: 'A real Dragy timeslip from a stock NS400Z, sent through the "Submit a timeslip" form, would tighten the prediction. Until that data exists, the ±0.4 second cluster bias band is the honest measure of uncertainty. It is wider than the gap to the RC 390, but the relative order across the cluster is stable. The NS400Z is third or fourth quickest in its segment, behind the RC 390 and the Duke 390, ahead of the Apache RR 310 and well ahead of the Dominar 400. That order does not change across reasonable sweeps of the inputs.',
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
          datePublished: '2026-05-18',
        })}
      />
      <SiteNav />

      <article id="main" className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          <div className="flex flex-wrap gap-2 mb-6">
            {['Bajaj', 'Pulsar NS400Z', 'KTM RC 390', 'Indian 400cc', 'physics'].map((t) => (
              <span
                key={t}
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Pulsar NS400Z quarter-mile physics (and why an RC 390 still wins)
          </h1>
          <div className="text-sm text-white/60 mb-12">
            18 May 2026 · 12 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        <PostBikeLinks ids={[145]} />

        <div className="max-w-2xl mx-auto mt-16 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Simulate the NS400Z vs RC 390 head-to-head</div>
            <div className="text-white/60 text-sm">Pick both bikes, change rider weight, mods and venue conditions, and see the ET difference before you spend a rupee on either one.</div>
          </div>
          <Link href="/simulator" className="shrink-0 px-5 py-2.5 bg-brand-orange text-on-accent font-display font-bold rounded-lg text-sm hover:bg-brand-orangeLight transition-colors">Open the simulator →</Link>
        </div>

        <div className="max-w-2xl mx-auto mt-16">
          <h3 className="font-display font-bold text-lg text-white mb-4">Related reading</h3>
          <ul className="text-sm text-white/70 space-y-2">
            <li>
              ·{' '}
              <Link href="/blog/pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                Pulsar NS200 vs Apache RTR 200 4V: which wins the quarter mile?
              </Link>:{' '}
              the same physics one displacement class down, with the same Bajaj-vs-rival framing.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/why-your-r15-wont-hit-14s" className="text-brand-accent hover:text-brand-orange transition-colors">
                Why your R15 won&apos;t hit 14s (and what will actually help)
              </Link>:{' '}
              gearing, traction, and the small-cc traps the press release never mentions.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-to-tune-for-aamby-valley-in-november" className="text-brand-accent hover:text-brand-orange transition-colors">
                How to tune for Aamby Valley in November
              </Link>:{' '}
              the venue conditions used for the simulation in this post, plus the DA penalty math.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-the-motoquant-physics-engine-works" className="text-brand-accent hover:text-brand-orange transition-colors">
                How the MotoQuant physics engine works
              </Link>:{' '}
              what is inside the simulator that produced these numbers and what the cluster bias bands mean.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>:{' '}
              NS400Z, RC 390, Duke 390, Dominar 400, Apache RR 310, and 390+ other bikes with full spec sheets and OEM tire fitments.
            </li>
          </ul>
        </div>
      </article>

      <SiteFooter />
    </div>
  );
}
