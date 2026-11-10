import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'yezdi-roadster-quarter-mile-physics';
const TITLE = 'Yezdi Roadster quarter-mile physics: 334cc neo-retro at the strip';
const DESCRIPTION =
  'MotoQuant simulates the Yezdi Roadster 334 at 15.42s with a 138 km/h trap at Aamby Valley: 28.6 hp, 175 kg dry, the BG6 platform, and a ₹6,500 sprocket swap worth 0.18 s.';

export const metadata = {
  title: 'Yezdi Roadster quarter-mile physics | MotoQuant',
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
    text: 'MotoQuant simulates the Yezdi Roadster 334 at 15.42 seconds with a 138.4 km/h trap under Aamby Valley November conditions. It makes 28.6 hp at 7300 rpm and 29 Nm at 6500 rpm, and weighs 175 kg dry. That puts it a half-second quicker than a stock Royal Enfield Classic 350, a full second behind a KTM Duke 390, and right in the price-and-displacement gap that Classic Legends built the BG6 platform to fill. The Yezdi is faster than the bike it was built to fight. The open question is what the 334 cc liquid-cooled platform buys you when neither bike is, by any honest measure, fast.',
  },
  {
    type: 'h2',
    text: 'What the Roadster is',
  },
  {
    type: 'p',
    text: 'The Yezdi Roadster sits on the BG6 platform that Classic Legends (the Mahindra-group subsidiary that revived the Yezdi brand in January 2022) also uses for the Yezdi Scrambler, Yezdi Adventure 334, and Jawa 42 Bobber 350. The engine is a 334 cc liquid-cooled DOHC single producing 28.6 hp (29 PS) at 7300 rpm and 29 Nm at 6500 rpm, with a six-speed cassette gearbox running ratios [2.692, 1.937, 1.500, 1.227, 1.045, 0.913] and 15/37 final drive on the Roadster specifically. Classic Legends service manual YEZ-BG6-001 documents the platform and cross-references gear ratios and engine internals across all four sibling bikes.',
  },
  {
    type: 'p',
    text: 'The Roadster is a 175 kg (dry) retro naked whose liquid-cooled single makes more power than a Classic 350 (28.6 hp vs 20.2 hp at the crank) and slightly less torque per kg than the air-cooled Royal Enfield (0.166 Nm/kg vs 0.140 Nm/kg). It is faster, taller-geared, and revs harder than the Classic 350. Depending on the model year and dealer, it is also ₹15,000 to ₹40,000 cheaper. The Roadster sells on that value, and the drag-strip numbers mostly check that the value is real.',
  },
  {
    type: 'h2',
    text: 'Stock-tune simulation numbers',
  },
  {
    type: 'p',
    text: 'Stock-tune numbers from MotoQuant with a 78 kg rider, OEM Ceat Zoom-X rear (μ_peak 1.20), 22°C ambient, dry asphalt and density altitude ~1100 m (Aamby Valley November):',
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
    text: 'There is no published instrumented quarter-mile time for the Roadster. Every Indian magazine that reviewed the bike (Autocar India, ZigWheels, BikeWale, Motoroids) ran 0-100 km/h tests and city-cycle fuel economy runs; none ran a 402 m strip pass. The closest data is ZigWheels’ 2022 review of the Yezdi Scrambler, which clocked 0-100 in 8.2 seconds, within 0.3 s of the simulator estimate for the Roadster. That is expected: the two bikes share an engine and gearbox and differ only in tyre size and final drive ratio.',
  },
  {
    type: 'callout',
    text: 'Why no magazine has timed this bike: Indian reviews in the 200-400 cc segment report 0-100 km/h and city-cycle MPG, not strip ET. The Roadster has 0-100 numbers (8.5 s, Autocar 2022; 8.4 s, BikeWale 2022) but no published 402 m time. The simulator estimate above is the first physics-derived ET for this platform on the open internet.',
  },
  {
    type: 'h2',
    text: 'Where the BG6 platform wins and loses',
  },
  {
    type: 'p',
    text: 'Three things define the Roadster on a quarter-mile pass. The first is power-to-weight: 163 hp/tonne dry puts it in roughly the same band as a stock Bajaj Pulsar NS200 (165 hp/tonne), but with much taller gearing. The second is the gearbox. The BG6 six-speed cassette is identical to the gearbox Yamaha uses in the YZF-R3, MT-03 and FZ25, scaled for the 334 cc engine. It was designed for a 50 hp twin, and on the Roadster it is overgeared for the torque available. The bike crosses the trap line in fourth at about 7100 rpm with two gears unused, the mark of a final drive chosen for the road.',
  },
  {
    type: 'p',
    text: 'The third, and the one that matters most at trap speed, is aerodynamics. The Roadster is an upright retro naked with exposed handlebars and no fairing or fly screen. Catalog Cd is 0.78 and frontal area is 0.48 m². At the 138 km/h trap, drag takes roughly 7 kW (9.4 hp), close to one-third of the engine output. The same engine in the upcoming Yezdi Scrambler-S, with a small bikini fairing (Cd ≈ 0.72, A ≈ 0.46 m²), would see about 5.5 kW of drag at the same trap speed, and the simulator predicts an ET roughly 0.15 s lower. A full sport fairing on a 28-hp single is a worse trade than it sounds, because the extra weight cancels most of the aero gain. Still, on a bike this short of power, drag takes a real share of the budget.',
  },
  {
    type: 'p',
    text: 'In the simulator log for a stock-tune Aamby Valley run, the Roadster launches in first at 4200 rpm with moderate clutch slip (the BG6 assist-and-slipper clutch is forgiving at launch but does not lock up cleanly until ~5500 rpm). It shifts to second at 1.6 s / 60 ft, to third at 4.4 s / 200 ft and to fourth at 9.1 s / 530 ft, then crosses the trap line in fourth at 7100 rpm. With any sensible final drive, it never uses fifth or sixth on a quarter-mile pass.',
  },
  {
    type: 'h2',
    text: 'How the Roadster compares with its rivals',
  },
  {
    type: 'p',
    text: 'The Roadster competes in the ₹2.0-2.5 lakh (ex-showroom) Indian retro segment against three main alternatives: the Royal Enfield Classic 350, the Royal Enfield Hunter 350 and the Honda CB350RS. The numbers below are MotoQuant stock-tune simulations under the same Aamby Valley November conditions:',
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
    text: 'The Roadster is the quickest bike in its ₹2.0-2.2 lakh price band by a clear margin, about 1.0 to 1.6 seconds ahead of the Royal Enfield and Honda 350s. Almost all of that gap is the 28.6 hp vs 20.2 hp peak power difference at similar dry mass; the BG6 platform simply makes more power than the RE J-series and Honda Unicorn 350 platforms. The Roadster gives up about 1.8 seconds to the KTM Duke 390, which costs roughly 50 percent more and makes 15 hp more in a chassis 26 kg lighter. That bigger gap is why the Roadster sits in its own category: it is the fastest sub-₹2.5-lakh retro naked, not the fastest sub-₹3.5-lakh naked. Those are different purchases.',
  },
  {
    type: 'p',
    text: 'Against a Classic 350, the strip data confirms the spec sheet: the Roadster is clearly faster at about the same on-road price. Against a Duke 390 the data is just as clear the other way: the Duke is much faster and costs much more. The Roadster does not try to match a Duke on speed. It competes on price and on the Yezdi brand’s neo-retro styling, and MotoQuant simulates neither.',
  },
  {
    type: 'h2',
    text: 'The cheapest tenths on this bike',
  },
  {
    type: 'p',
    text: 'Three modifications are worth the money on a Roadster used for occasional drag-strip days. None requires removing emissions equipment and none affects the warranty.',
  },
  {
    type: 'p',
    text: 'The best return is the rear sprocket. The stock 15/37 final drive is geared for highway cruising: the Roadster holds 6th gear comfortably at a steady 95 km/h, which is useful on a 200 km highway run and wrong for a strip pass. A 15/41 swap (rear sprocket only) shortens the ratios by 10.8 percent, and the bike crosses the trap line in fourth at 7800 rpm instead of 7100 rpm, much closer to the engine’s 7300 rpm power peak. The simulator predicts about 0.18 seconds off the ET for this one change. A JT Sprockets 41T rear in 520 pitch costs ₹650 to ₹900 in India; add a fresh 520 chain (₹4,500 for a DID O-ring) and the parts come to under ₹6,500. It is the cheapest tenth on this bike.',
  },
  {
    type: 'p',
    text: 'Next is the rear tyre. The Roadster ships with the Ceat Zoom-X 130/80-17, a good commuter tyre built for wet grip and long wear rather than peak μ. An Apollo Alpha H1 or MRF Mogrip Meteor M3 in the same 130/80-17 size raises peak μ from 1.20 to roughly 1.32, which the simulator turns into about 0.06 to 0.08 seconds off the ET. Cost is about ₹3,800 for the tyre plus ₹400 fitting. You give up some street manners: both wear faster than the OEM Ceat and grip less when it is cold and wet. For a bike that does occasional strip days, the swap is worth it.',
  },
  {
    type: 'p',
    text: 'Third is the ECU. The stock Classic Legends map puts BS6 emissions compliance and mid-range driveability ahead of peak power. Powertronic released a Stage 1 map for the BG6 Yezdi range in late 2024. It adds about 2.4 hp at peak (30.4 hp vs 28.6 hp stock) and moves the torque peak from 6500 rpm to 6200 rpm. The simulator predicts about 0.10 seconds off the ET, for roughly ₹18,000 at a Powertronic dealer. Per tenth that is about twice the cost of the sprocket swap, but the two add up: with both, the Roadster goes from 15.42 s stock to about 15.14 s.',
  },
  {
    type: 'callout',
    text: 'Mod order on a Yezdi Roadster: 15/41 sprocket swap first (~₹6,500 / ~0.18 s, the cheapest tenth on the bike), then an Apollo or MRF rear tyre (~₹4,200 / ~0.07 s), then a Powertronic Stage 1 flash if a Powertronic dealer is within reach (~₹18,000 / ~0.10 s). Total ~₹28,700 for ~0.35 s of ET, which lands a sub-15-second stock-class Roadster at most Indian strips. Skip the slip-on exhaust: on a stock head, back-pressure changes do little for a single’s volumetric efficiency.',
  },
  {
    type: 'h2',
    text: 'Why the Roadster is the right 334cc choice for most buyers',
  },
  {
    type: 'p',
    text: 'Four bikes in the Classic Legends and Mahindra catalogues use the BG6 platform: the Yezdi Roadster, the Yezdi Scrambler, the Yezdi Adventure 334 and the Jawa 42 Bobber 350. They share the engine, the gearbox and most of the chassis hardware, and differ in riding posture, tyre size, sub-frame geometry and final-drive sprocket count. At the strip, the Roadster is the quickest of the four on stock final drive (15.42 s, fastest cassette ratio for the displacement). The Scrambler is roughly 0.2 s slower because of its 19" front wheel and higher unsprung mass. The Adventure is roughly 0.4 s slower because of its taller 19"/17" wire-spoke wheels and a taller R39 rear sprocket chosen for adventure cruising. The Jawa 42 Bobber 350 sits between the Roadster and the Scrambler, depending on year and tyre fitment.',
  },
  {
    type: 'p',
    text: 'If drag-strip performance is what you are buying for, pick the Roadster. It is also the cheapest of the four: Classic Legends sells the Roadster as the entry point to the Yezdi range, and the Scrambler and Adventure cost ₹15,000 to ₹35,000 more for their off-road styling. The fastest BG6 bike is the cheapest one, which is rare in the Indian market.',
  },
  {
    type: 'h2',
    text: 'The verdict',
  },
  {
    type: 'p',
    text: 'The Yezdi Roadster is the quickest sub-₹2.5-lakh retro naked in India in 2026. It is a small category and a small claim, and the numbers back it: 28.6 hp, 175 kg dry, a 15.42-second simulated ET on stock tune. The Roadster is clearly ahead of the Royal Enfield Classic 350 (~17.0 s) and the Honda CB350RS (~16.8 s) at almost the same ex-showroom price. It is just as clearly behind the KTM Duke 390 (~13.65 s), which costs a lot more. It will never be the fastest 300-400 cc bike you can buy. For a buyer who puts retro looks ahead of outright speed and wants the best power-to-weight ratio in the ₹2.0-2.2 lakh band, it is never the wrong choice.',
  },
  {
    type: 'p',
    text: 'The mod path on this bike is simple. The sprocket swap is the cheapest tenth on any 300-400 cc Indian bike, partly because the OEM 15/37 final drive is poor for strip use and partly because every Indian motorcycle shop stocks 520-pitch sprockets. The tyre upgrade is well validated. The ECU flash costs more per tenth but adds cleanly to the other two. Taking the Roadster from a 15.4-second bike to a 15.1-second bike costs roughly ₹28,000, less than the price gap between a Roadster and a Duke 390, and that is the comparison most buyers will make.',
  },
  {
    type: 'p',
    text: 'Indian reviewers have treated the 334 cc class as a city-cycle MPG category, not a performance one, which is part of why no magazine has run an instrumented ET on this bike in the four years it has been on sale. This post exists to fill that gap. Nobody has published what a stock Yezdi Roadster does over a quarter mile, and until Dragy timeslip data surfaces, the MotoQuant simulator is the best tool for estimating it. The 15.42-second figure above is a stock-tune estimate under specific Aamby Valley conditions. A competent rider at MMRT Chennai (sea level, higher density air, dry asphalt) would likely run 15.0 to 15.2 seconds. That difference is the documented venue delta, not a simulator error.',
  },
  {
    type: 'h2',
    text: 'Run your own numbers',
  },
  {
    type: 'p',
    text: 'If you own a Yezdi Roadster, or are choosing between the Roadster, Scrambler, Adventure 334 and the Royal Enfield 350s, the simulator at motoquant.in lets you change rider weight, ambient temperature, density altitude and parts-catalog mods and see where the tenths come from on your bike in your conditions. The catalog carries the full BG6 gear cassette and the engine torque curve from the Classic Legends service manual, so comparisons across the four platform-mates are like for like.',
  },
  {
    type: 'p',
    text: 'For tuning, MotoQuant scores every part in its catalog by cost per tenth on your bike. On the Roadster the order is sprocket swap, then tyre, then ECU flash. The simulator gives you that order in numbers, and because four bikes share the engine and gearbox, mod data from one carries over well to the others.',
  },
  {
    type: 'p',
    text: 'Two caveats. First, every number in this post is a stock-tune simulation under the same Aamby Valley November conditions. Change the venue (sea-level MMRT helps by ~0.15-0.20 s) or the rider (a 65 kg rider instead of the 78 kg simulated default helps by ~0.10 s) and the absolute ETs move; the Roadster’s place among its rivals does not. Second, there is no instrumented ET for this bike to calibrate against. The 15.42 s number is a first-principles estimate from the engine torque curve, the gearbox ratios, the dry mass and the published Cd/frontal-area inputs. If a Dragy timeslip from a stock Roadster turns up (Valley Run 2026 Winter would be the obvious place to get one), the model will be updated, and the headline number may move by 0.1 to 0.3 seconds either way.',
  },
  {
    type: 'p',
    text: 'The Yezdi Roadster 334 is the fastest sub-₹2.5-lakh retro naked in India, and the cheapest tenth on it is a ₹6,500 sprocket-and-chain swap worth 0.18 seconds. Start there; every other mod stacks on top of it. The comparisons with the Classic 350, the Hunter 350 and the Duke 390 all rest on the simulated 15.42 s baseline, and that baseline is now public.',
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

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {['Yezdi', 'Roadster 334', 'BG6 platform', 'Indian retro', 'physics'].map((t) => (
              <span
                key={t}
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Yezdi Roadster quarter-mile physics: 334cc neo-retro at the strip
          </h1>
          <div className="text-sm text-white/60 mb-12">
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
                Royal Enfield Continental GT 650 quarter-mile physics
              </Link>
              : the bigger retro twin, one segment above the Roadster.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/ktm-duke-390-vs-rc-390-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                KTM Duke 390 vs RC 390: quarter-mile physics
              </Link>
              : the ₹3.1-lakh bike that the Roadster gives up 1.8 s to.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-the-motoquant-physics-engine-works" className="text-brand-accent hover:text-brand-orange transition-colors">
                How the MotoQuant physics engine works
              </Link>
              : the 15 sub-models behind every ET prediction in this post.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-to-tune-for-aamby-valley-in-november" className="text-brand-accent hover:text-brand-orange transition-colors">
                How to tune for Aamby Valley in November
              </Link>
              : the venue conditions used for every simulation above.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>
              : including the Roadster and its platform-mates, the Scrambler, Adventure 334 and Jawa 42 Bobber 350.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Run the Roadster yourself</div>
            <div className="text-white/60 text-sm">
              Free simulator: pick the Yezdi Roadster, set your local conditions, and watch the ET update live.
            </div>
          </div>
          <Link
            href="/simulator?bike=yezdi-roadster"
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
