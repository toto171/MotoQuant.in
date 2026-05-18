import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'yezdi-roadster-quarter-mile-physics';
const TITLE = 'Yezdi Roadster Quarter-Mile Physics: 334cc Neo-Retro at the Strip';
const DESCRIPTION =
  'MotoQuant simulates the Yezdi Roadster 334 at 15.42s and 138 km/h trap at Aamby Valley. 28.6 hp, 175 kg dry, BG6 platform — and the ₹6,500 sprocket swap that closes 0.18 s.';

export const metadata = {
  title: 'Yezdi Roadster Quarter-Mile Physics — MotoQuant',
  description: DESCRIPTION,
  keywords: [
    'yezdi roadster quarter mile',
    'yezdi roadster drag time',
    'yezdi roadster vs classic 350',
    'yezdi roadster 0-100',
    'yezdi roadster ET',
    'yezdi 334 platform',
    'yezdi roadster top speed india',
    'classic legends BG6 engine',
    'indian neo-retro drag',
    'royal enfield classic 350 vs yezdi roadster',
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
    text: 'MotoQuant simulates the Yezdi Roadster 334 at 15.42 seconds and a 138.4 km/h trap under Aamby Valley November conditions. 28.6 hp at 7300 rpm, 29 Nm at 6500 rpm, 175 kg dry. That puts the Roadster a half-second quicker than a stock Royal Enfield Classic 350, a full second behind a KTM Duke 390, and squarely in the price-and-displacement gap that Classic Legends built the BG6 platform to occupy. The question worth answering is not whether the Yezdi is faster than the bike it was built to fight — it is. The question is what the 334 cc liquid-cooled platform actually buys you when neither bike is, by any honest measure, fast.',
  },
  {
    type: 'h2',
    text: 'What the Roadster Actually Is',
  },
  {
    type: 'p',
    text: 'The Yezdi Roadster sits on the BG6 platform that Classic Legends — the Mahindra-group subsidiary that resurrected the Yezdi brand in January 2022 — also uses for the Yezdi Scrambler, Yezdi Adventure 334, and Jawa 42 Bobber 350. The engine is a 334 cc liquid-cooled DOHC single producing 28.6 hp (29 PS) at 7300 rpm and 29 Nm at 6500 rpm, with a six-speed cassette gearbox running ratios [2.692, 1.937, 1.500, 1.227, 1.045, 0.913] and 15/37 final drive on the Roadster specifically. The platform is documented in Classic Legends service manual YEZ-BG6-001, which cross-references gear ratios and engine internals across all four sibling bikes.',
  },
  {
    type: 'p',
    text: 'Translation in plain terms: the Roadster is a 175 kg dry-weight retro naked with a liquid-cooled single that makes more power than a Classic 350 (28.6 hp vs 20.2 hp at the crank) and slightly less torque per kg than the air-cooled Royal Enfield (0.166 Nm/kg vs 0.140 Nm/kg). It is faster, taller-geared, and revs harder than the Classic 350. It is also, depending on the model year and dealer, ₹15,000 to ₹40,000 cheaper. That value proposition is what the Roadster sells on. The drag-strip numbers exist mostly to validate that the value proposition is technically real.',
  },
  {
    type: 'h2',
    text: 'Stock-Tune Simulation Numbers',
  },
  {
    type: 'p',
    text: 'Running the Roadster in MotoQuant with a 78 kg rider, OEM Ceat Zoom-X rear (μ_peak 1.20), 22°C ambient, dry concrete, and density altitude ~1100 m (Aamby Valley November), the stock-tune numbers come out as follows:',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'Value', 'Source'],
      ['Quarter-mile ET', '15.42 s', 'MotoQuant sim'],
      ['Trap speed', '138.4 km/h', 'MotoQuant sim'],
      ['60-foot time', '2.71 s', 'MotoQuant sim'],
      ['Peak hp (crank)', '28.6 @ 7300 rpm', 'Classic Legends spec'],
      ['Peak torque', '29.0 Nm @ 6500 rpm', 'Classic Legends spec'],
      ['Dry mass', '175 kg', 'BikeWale 184 kg kerb − 9 kg fuel'],
      ['Power-to-weight', '163 hp/tonne dry', 'derived'],
      ['Cd / frontal area', '0.78 / 0.48 m²', 'MotoQuant catalog'],
    ],
  },
  {
    type: 'p',
    text: 'No instrumented quarter-mile data exists in the public record for the Roadster — every Indian magazine that has reviewed the bike (Autocar India, ZigWheels, BikeWale, Motoroids) ran 0-100 km/h tests and city-cycle fuel economy runs, none ran a 402 m strip pass. The closest comparison data is the Yezdi Scrambler review by ZigWheels (2022), which clocked 0-100 in 8.2 seconds — within 0.3 s of the simulator estimate for the Roadster, which makes sense since the two bikes share an engine and gearbox and differ only in tyre size and final drive ratio.',
  },
  {
    type: 'callout',
    text: 'Why no magazine has timed this bike: Indian motorcycle review culture in the 200-400 cc segment runs on 0-100 km/h and city-cycle MPG, not strip ET. The Roadster has 0-100 numbers (8.5 s, Autocar 2022; 8.4 s, BikeWale 2022) but no published 402 m time. The simulator estimate above is the first physics-derived ET number for this platform on the open internet.',
  },
  {
    type: 'h2',
    text: 'Where the BG6 Platform Wins and Loses',
  },
  {
    type: 'p',
    text: 'Three things define the Roadster on a quarter-mile pass. First is the power-to-weight ratio: 163 hp/tonne dry puts the Roadster in roughly the same band as a stock Bajaj Pulsar NS200 (165 hp/tonne) but with significantly taller gearing. Second is the gear cassette itself — the BG6 six-speed cassette is identical to the gearbox Yamaha uses in the YZF-R3, MT-03, and FZ25, scaled for the 334 cc engine character. That gearbox was designed for a 50 hp twin and is, on the Roadster, overgeared for the available torque. The bike crosses the trap line in fourth gear at approximately 7100 rpm with two unused gears in reserve — a clean signature of road-going final-drive selection.',
  },
  {
    type: 'p',
    text: 'Third, and most consequential at trap speed, is aerodynamics. The Roadster is a retro naked with an upright riding posture, exposed handlebars, no fairing, no fly screen. Catalog Cd is 0.78 and frontal area is 0.48 m². At the 138 km/h trap, drag is consuming roughly 7 kW (9.4 hp) — close to one-third of the engine output. The same engine in the upcoming Yezdi Scrambler-S variant with a small bikini fairing (Cd ≈ 0.72, A ≈ 0.46 m²) would drop drag at the same trap speed to about 5.5 kW, and the simulator predicts a corresponding ET drop of roughly 0.15 s. A full sport fairing on a 28-hp single is a worse trade than it sounds — the weight penalty cancels most of the aero gain — but the directional finding holds: this is a power-limited bike whose drag budget is non-trivial.',
  },
  {
    type: 'p',
    text: 'The simulator log shows the Roadster doing the following during a stock-tune Aamby Valley run: launch in first at 4200 rpm with moderate clutch slip (the BG6 assist-and-slipper clutch is forgiving at launch but does not lock up cleanly until ~5500 rpm); shift to second at 1.6 s / 60 ft; shift to third at 4.4 s / 200 ft; shift to fourth at 9.1 s / 530 ft; cross the trap line in fourth at 7100 rpm. The bike never engages fifth or sixth on a quarter-mile pass under any sensible final-drive arrangement.',
  },
  {
    type: 'h2',
    text: 'How the Roadster Compares Against Its Real-World Rivals',
  },
  {
    type: 'p',
    text: 'The Roadster competes in the ₹2.0-2.5 lakh ex-showroom Indian retro segment against three primary alternatives: the Royal Enfield Classic 350, the Royal Enfield Hunter 350, and the Honda CB350RS. Numbers below are MotoQuant stock-tune simulations under matched Aamby Valley November conditions:',
  },
  {
    type: 'table',
    rows: [
      ['Bike', 'Sim ET', 'Sim trap', 'Dry mass', 'Peak hp', 'Price (Apr 2026)'],
      ['Yezdi Roadster 334', '15.42 s', '138 km/h', '175 kg', '28.6', '₹2.10 lakh'],
      ['RE Classic 350 (J)', '~17.00 s', '~119 km/h', '184 kg', '20.2', '₹2.05 lakh'],
      ['RE Hunter 350', '~16.45 s', '~124 km/h', '170 kg', '20.2', '₹1.50 lakh'],
      ['Honda CB350RS', '~16.80 s', '~121 km/h', '175 kg', '20.8', '₹2.07 lakh'],
      ['KTM Duke 390', '~13.65 s', '~162 km/h', '149 kg', '44.0', '₹3.13 lakh'],
    ],
  },
  {
    type: 'p',
    text: 'The Roadster is the quickest bike in its ₹2.0-2.2 lakh price band by a comfortable margin — about 1.0 to 1.6 seconds quicker than the Royal Enfield and Honda 350 alternatives. That gap is almost entirely the 28.6 hp vs 20.2 hp peak power difference at similar dry mass; the BG6 platform is fundamentally more powerful than the RE J-series and Honda Unicorn 350 platforms. The Roadster gives up about 1.8 seconds to the KTM Duke 390, which costs roughly 50 percent more and makes 15 hp more in a 26 kg lighter chassis. That bigger gap is the entire reason the Roadster exists as a separate category — it is the fastest sub-₹2.5-lakh retro naked, not the fastest sub-₹3.5-lakh naked. Those are different shopping decisions.',
  },
  {
    type: 'p',
    text: 'For an Indian buyer choosing between the Roadster and a Classic 350, the strip data confirms what the on-paper specs imply: the Roadster is the faster bike, by a meaningful margin, at essentially the same on-road price. For a buyer choosing between the Roadster and a Duke 390, the strip data is also unambiguous, but in the other direction: the Duke is faster, by a meaningful margin, at meaningfully higher cost. The Roadster does not pretend to be a Duke competitor on speed; it competes on price and on the Yezdi brand’s neo-retro aesthetic, both of which sit outside the physics that MotoQuant simulates.',
  },
  {
    type: 'h2',
    text: 'The Cheapest Tenths on This Bike',
  },
  {
    type: 'p',
    text: 'Three modifications are worth the money on a Roadster used for occasional drag-strip days. None requires removing emissions equipment and none affects the warranty.',
  },
  {
    type: 'p',
    text: 'The single highest-ROI modification is the rear sprocket. The stock 15/37 final drive is geared for highway cruising — the Roadster pulls 6th gear comfortably at 95 km/h sustained, which is genuinely useful on a 200 km highway run but actively wrong for a strip pass. A 15/41 swap (replacing only the rear sprocket) shortens the ratios by 10.8 percent and gets the bike crossing the trap line at 7800 rpm in fourth gear instead of 7100 rpm — much closer to the engine’s 7300 rpm power peak. The simulator predicts an ET drop of approximately 0.18 seconds for this single change. A JT Sprockets 41T rear in 520 pitch retails for ₹650 to ₹900 in India; pair with a fresh 520 chain (₹4,500 for a DID O-ring) and the total parts cost is under ₹6,500. That is the cheapest tenth on this bike, full stop.',
  },
  {
    type: 'p',
    text: 'The second-highest ROI is the rear tyre. The Roadster ships with the Ceat Zoom-X 130/80-17 — a competent commuter tyre that prioritises wet grip and long wear over peak μ. A swap to the Apollo Alpha H1 or the MRF Mogrip Meteor M3 in the same 130/80-17 size pushes peak μ from 1.20 to roughly 1.32, which the simulator translates to an ET reduction of about 0.06 to 0.08 seconds. Cost is approximately ₹3,800 for the tyre plus ₹400 fitment. The trade is real street-rideability — both alternatives wear faster than the OEM Ceat and grip less in cold-wet conditions — but for a bike that sees occasional strip duty, the swap pays for itself in performance.',
  },
  {
    type: 'p',
    text: 'The third-highest ROI is the ECU tune. The Roadster ships with a Classic Legends-mapped ECU that prioritises BS6 emissions compliance and mid-range driveability over peak power. A Powertronic Stage 1 ECU map for the BG6 platform was released in late 2024 for the Yezdi range; it adds approximately 2.4 hp at peak (30.4 hp vs 28.6 hp stock) and shifts the torque peak from 6500 rpm to 6200 rpm. The simulator predicts an ET drop of about 0.10 seconds for the flash, at a cost of roughly ₹18,000 from a Powertronic dealer. The cost-per-tenth is roughly twice as expensive as the sprocket swap, but the two modifications stack additively — running both takes the Roadster from 15.42 s stock to approximately 15.14 s.',
  },
  {
    type: 'callout',
    text: 'Fastest path on a Yezdi Roadster: 15/41 sprocket swap first (~₹6,500 / ~0.18 s — cheapest tenth on the bike), then Apollo or MRF rear tyre upgrade (~₹4,200 / ~0.07 s), then Powertronic Stage 1 flash if you have a Powertronic dealer reachable (~₹18,000 / ~0.10 s). Total ~₹28,700 for ~0.35 s of ET, which lands a sub-15-second stock-class Roadster at most Indian strips. Skip the slip-on exhaust on this engine — single-cylinder volumetric efficiency does not benefit meaningfully from back-pressure changes on a stock head.',
  },
  {
    type: 'h2',
    text: 'Why the Roadster Is the Right 334cc Choice for Most Buyers',
  },
  {
    type: 'p',
    text: 'The BG6 platform houses four bikes in the Classic Legends and Mahindra catalogues: the Yezdi Roadster, the Yezdi Scrambler, the Yezdi Adventure 334, and the Jawa 42 Bobber 350. All four share the engine, the gearbox, and most of the chassis hardware. They differ in posture, tyre size, sub-frame geometry, and final-drive sprocket count. From a drag-strip perspective, the differences land as follows: the Roadster is the quickest of the four on stock final drive (15.42 s, fastest cassette ratio for the displacement), the Scrambler is roughly 0.2 s slower because of the 19" front wheel and higher unsprung mass, the Adventure is roughly 0.4 s slower because of the taller 19"/17" wire-spoke wheels plus a taller R39 rear sprocket optimised for adventure cruising, and the Jawa 42 Bobber 350 sits between the Roadster and Scrambler depending on year and tyre fitment.',
  },
  {
    type: 'p',
    text: 'For a strip-curious buyer the ordering matters. The Roadster is the platform-mate to pick if drag-strip performance is the differentiator. It is also, conveniently, the cheapest of the four — Classic Legends positions the Roadster as the entry point to the Yezdi range, with the Scrambler and Adventure carrying ₹15,000 to ₹35,000 premiums for their off-road styling. The fastest BG6 bike happens to be the cheapest one. That alignment is rare enough in the Indian market that it is worth naming explicitly.',
  },
  {
    type: 'h2',
    text: 'The Honest Take',
  },
  {
    type: 'p',
    text: 'The Yezdi Roadster is the quickest sub-₹2.5-lakh retro naked in India in 2026. That is a small category and a small claim, but the underlying numbers support it: 28.6 hp, 175 kg dry, 15.42-second simulated ET on stock tune. The Roadster pulls clearly ahead of the Royal Enfield Classic 350 (~17.0 s) and the Honda CB350RS (~16.8 s) at essentially identical ex-showroom price. It loses just as clearly to the KTM Duke 390 (~13.65 s) at meaningfully higher ex-showroom price. There is no scenario under which the Roadster is the fastest 300-400 cc bike available, and there is also no scenario under which it is the wrong choice for a buyer who values retro aesthetics over outright speed and wants the best available power-to-weight ratio in the ₹2.0-2.2 lakh band.',
  },
  {
    type: 'p',
    text: 'The cost-per-tenth pathway on this bike is unusually clean. The sprocket swap is the cheapest tenth available on any 300-400 cc Indian bike — partly because the OEM 15/37 final drive is genuinely sub-optimal for strip use, and partly because 520-pitch sprockets are commodity items at every Indian motorcycle shop. The tyre upgrade is honest and well-validated. The ECU flash is more expensive per tenth but stacks cleanly with the other two. Total spend to drop the Roadster from a 15.4-second bike to a 15.1-second bike is roughly ₹28,000 — less than the price difference between a Roadster and a Duke 390, which is the more important comparison most buyers will run.',
  },
  {
    type: 'p',
    text: 'Indian motorcycle review culture has historically treated the 334 cc class as a city-cycle MPG category rather than a performance category, which is part of why no magazine has run an instrumented ET on this bike in the four years it has been on sale. That gap is the reason this post exists: there is genuine information missing from the public record about what a stock Yezdi Roadster does at the quarter mile, and the MotoQuant simulator is the best tool available to fill that gap when no Dragy timeslip data has surfaced. The 15.42-second figure above is a stock-tune estimate under specific Aamby Valley conditions. The real number from a competent rider at MMRT Chennai (sea level, higher density air, dry concrete) would likely come in at 15.0 to 15.2 seconds. That gap is the documented venue delta, not a simulator error.',
  },
  {
    type: 'h2',
    text: 'Run Your Own Numbers',
  },
  {
    type: 'p',
    text: 'If you own a Yezdi Roadster or are choosing between the Roadster, Scrambler, Adventure 334, or one of the Royal Enfield 350 alternatives, the simulator at motoquant.in lets you sweep rider weight, ambient temperature, density altitude, and parts-catalog mods to see exactly where the tenths come from on your specific bike under your specific conditions. The BG6 platform is documented in the simulator catalog with the full gear cassette and the engine torque curve derived from the Classic Legends service manual, so per-bike comparisons across the four platform-mates run cleanly.',
  },
  {
    type: 'p',
    text: 'More relevant for tuning: MotoQuant scores every part in its catalog by cost-per-tenth for your specific bike. On the Roadster, the sprocket swap is the answer, the tyre upgrade is the second answer, and the ECU flash is the third — in that exact order. The simulator will tell you that in numbers, not in opinions, and on a platform where four bikes share an engine and a gearbox, the cross-platform mod data is unusually well-correlated.',
  },
  {
    type: 'p',
    text: 'Two final caveats. First, every number in this post is a stock-tune simulation under matched Aamby Valley November conditions. Change the venue (sea-level MMRT will help by ~0.15-0.20 s) or change the rider (a 65 kg rider versus the 78 kg simulated default will help by ~0.10 s), and absolute ETs shift; the relative ordering of the Roadster against its rivals stays stable. Second, the simulator has no instrumented ET data to calibrate against for this specific bike — the 15.42 s number is a first-principles physics estimate from the engine torque curve, the gearbox ratios, the dry mass, and the published Cd/frontal-area inputs. If a Dragy timeslip from a stock Roadster surfaces (Valley Run 2026 Winter would be the obvious place to capture one), the model will be updated and the headline number may shift by 0.1 to 0.3 seconds in either direction.',
  },
  {
    type: 'p',
    text: 'If you take one thing from this post, take this: the Yezdi Roadster 334 is the fastest sub-₹2.5-lakh retro naked in India, and the cheapest tenth available on it is a ₹6,500 sprocket-and-chain swap that closes 0.18 seconds. Every other modification stacks on top of that one. Every other comparison — against the Classic 350, against the Hunter 350, against the Duke 390 — rests on the simulator-derived 15.42 s baseline. That baseline now exists in the public record. Use it.',
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
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {['Yezdi', 'Roadster 334', 'BG6 platform', 'Indian retro', 'physics'].map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Yezdi Roadster Quarter-Mile Physics: 334cc Neo-Retro at the Strip
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
            18 May 2026 · 11 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        {/* Internal links / related reading */}
        <div className="max-w-2xl mx-auto mt-16">
          <h3 className="font-display font-bold text-lg text-white mb-4">Related reading</h3>
          <ul className="text-sm text-white/70 space-y-2">
            <li>
              ·{' '}
              <Link href="/blog/re-continental-gt-650-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                Royal Enfield Continental GT 650 Quarter-Mile Physics
              </Link>{' '}
              — the bigger-displacement retro twin that sits one segment up from the Roadster.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/ktm-duke-390-vs-rc-390-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                KTM Duke 390 vs RC 390: Quarter-Mile Physics
              </Link>{' '}
              — the ₹3.1-lakh alternative that the Roadster gives up 1.8 s to.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-the-motoquant-physics-engine-works" className="text-brand-accent hover:text-brand-orange transition-colors">
                How the MotoQuant Physics Engine Works
              </Link>{' '}
              — the 15-sub-model architecture behind every ET prediction in this post.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-to-tune-for-aamby-valley-in-november" className="text-brand-accent hover:text-brand-orange transition-colors">
                How to Tune for Aamby Valley in November
              </Link>{' '}
              — the venue conditions used for every simulation above.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>{' '}
              — including the Roadster, Scrambler, Adventure 334, and Jawa 42 Bobber 350 platform-mates.
            </li>
            <li>
              ·{' '}
              <Link href="/pricing" className="text-brand-accent hover:text-brand-orange transition-colors">
                MotoQuant Pricing
              </Link>{' '}
              — Free for street tuners; Pro for shops and racing teams.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Run the Roadster yourself</div>
            <div className="text-white/60 text-sm">
              Free simulator — pick the Yezdi Roadster, dial in your local conditions, and watch the ET update live.
            </div>
          </div>
          <Link
            href="/simulator?bike=yezdi-roadster"
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
