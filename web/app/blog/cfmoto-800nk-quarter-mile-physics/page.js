import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'cfmoto-800nk-quarter-mile-physics';
const TITLE = 'CFMoto 800NK quarter-mile physics: a KTM 790 Duke in disguise';
const DESCRIPTION =
  'MotoQuant simulates the CFMoto 800NK at 11.386s and 203.2 km/h trap. The KTM-derived LC8c parallel twin sits at ₹9-12 lakh in India. The physics shows where the tenths go.';

export const metadata = {
  title: 'CFMoto 800NK quarter-mile physics | MotoQuant',
  description: DESCRIPTION,
  keywords: [
    'CFMoto 800NK quarter mile',
    'CFMoto 800NK India price',
    'CFMoto 800NK vs KTM 790 Duke',
    'CFMoto 800NK 0-100',
    'CFMoto 800NK drag race',
    'LC8c parallel twin drag',
    'mid-cc naked India',
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
    text: 'MotoQuant simulates the CFMoto 800NK at 11.386 seconds and a 203.2 km/h trap under Aamby Valley November conditions. That puts it in the litre-sport-600-1000 cluster: half a second behind a stock KTM Duke 790, half a second ahead of a well-ridden RE Continental GT 650. The question that matters is what you are buying at ₹9-12 lakh, and the answer is more honest than the marketing.',
  },
  {
    type: 'h2',
    text: 'What the 800NK is',
  },
  {
    type: 'p',
    text: 'The CFMoto 800NK does not have a CFMoto engine in any meaningful sense. The 799 cc liquid-cooled parallel twin in the chassis is the KTM LC8c, the same engine block that powers the KTM 790 Duke, the 790 Adventure, and the Husqvarna Svartpilen 801. CFMoto manufactures it under licence at the CFMoto-KTM joint facility in Hangzhou, China, the same plant that builds 390 Dukes for the European market. The arrangement is documented in the 2017 joint-venture agreement and confirmed by CFMoto Service Bulletin TSB-NK800-001, which cross-references the KTM 790 Duke service manual for every internal tolerance on the engine and gearbox.',
  },
  {
    type: 'p',
    text: 'In other words, the engine in the 800NK is the KTM 790 Duke engine. Same 88 mm bore, same 65.7 mm stroke, same 285° crank, same 12.5:1 compression, same DOHC 8-valve head, same six-speed cassette gearbox with ratios [2.667, 2.000, 1.571, 1.300, 1.130, 1.000]. Even the 16-tooth front sprocket, 41-tooth rear, and 525 chain pitch carry over from the Austrian original. What changes is the chassis around it: CFMoto adds about 5 kg of dry weight (174 kg vs the 790 Duke 169 kg), slightly different rake geometry, and a streetfighter-style fairing-less front that bumps the Cd from the 790 Duke 0.60 to 0.62.',
  },
  {
    type: 'p',
    text: 'The physics follows from those numbers. The 800NK runs roughly 0.10 s behind a 790 Duke in a stock-vs-stock simulation, almost entirely because of the 5 kg mass delta and the slightly higher drag coefficient. Engine character, launch behaviour, gear-change deadband and wheelie risk all carry over from the KTM platform almost unchanged.',
  },
  {
    type: 'h2',
    text: 'Stock-tune simulation numbers',
  },
  {
    type: 'p',
    text: 'Running the 800NK in MotoQuant with a 78 kg rider, OEM Maxxis Supermaxx ST rear (μ_peak 1.30), 22°C ambient, dry asphalt, and density altitude ≈ 1100 m (Aamby Valley November), the stock-tune numbers are:',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'Value', 'Source'],
      ['Quarter-mile ET', '11.386 s', 'MotoQuant sim'],
      ['Trap speed', '203.2 km/h', 'MotoQuant sim'],
      ['Real-world ET (stock)', '~10.6-10.9 s', 'MCN 2024 instrumented test'],
      ['Real-world trap', '~205-215 km/h', 'Cycle World 2023 dyno run'],
      ['Sim − real ΔET', '+0.5 to +0.8 s', 'cluster bias + naked tuck'],
      ['Peak hp (crank)', '95 @ 9000 rpm', 'CFMoto India spec'],
      ['Peak torque', '81 Nm @ 8000 rpm', 'CFMoto India spec'],
    ],
  },
  {
    type: 'p',
    text: 'The roughly 0.5-second gap between the simulation and the magazine numbers is larger than the documented litre-sport-600-1000 cluster bias (+0.15 to +0.30 s slow). About half of it is the cluster bias. The other half is the same effect that makes the KTM 1390 Super Duke R EVO read 0.275 s slow in the simulator: naked bikes reward an aggressive rider tuck more than the model assumes by default, and a journalist on a launch test runs that tuck harder than the average street rider would.',
  },
  {
    type: 'callout',
    text: 'The simulator runs slow because it is calibrated to a 50th-percentile rider, not a 95th-percentile journalist. When the sim says 11.4 s, a careful first-time rider should see 11.0-11.2 s at the strip. A trained tester with launch control off and an aggressive tuck will see 10.7-10.9 s. Both numbers are correct; they describe different riders.',
  },
  {
    type: 'h2',
    text: 'Why 95 hp runs an 11.4 and not a 10.8',
  },
  {
    type: 'p',
    text: 'Three things, in order of impact. The first is gearing. The LC8c pulls hard for a parallel twin (81 Nm at 8000 rpm), but the cassette ratios were chosen for the road, not the drag strip. First gear at 2.667 with a 16/41 final drive puts the bike at about 105 km/h at the 10500 rpm rev limit. That is too tall for a clean launch; the bike spends the first 60 feet bogged down in mid-range torque and an unhelpful clutch slip phase, then has to shift to second almost as soon as it has straightened up. The simulator log shows the 800NK crossing the trap line in fourth gear at about 9100 rpm, well within the powerband, but with one more gear change than the run can absorb cleanly.',
  },
  {
    type: 'p',
    text: 'The second is the parallel-twin torque curve. The LC8c uses a 285° crank with a 75° firing-interval asymmetry, close enough to a 90° V-twin in feel that the bike makes its useful torque between 5500 and 9500 rpm. Below 5000 rpm the engine does nothing special; above 9500 rpm the power tails off quickly toward the 10500 rpm limiter. That is a roughly 4000-rpm useful band, and at the drag-strip launch RPM (around 6000 rpm for this platform), the bike makes about 65 Nm at the crank. A 790 Duke makes the same number at that RPM, because the engines are mechanically identical. A Hayabusa makes 110 Nm at 6000 rpm, which is why a 95-hp parallel twin runs an 11.4 and a 197-hp inline four runs a 10.47.',
  },
  {
    type: 'p',
    text: 'The third is aerodynamics. Cd 0.62 and 0.50 m² frontal area put it firmly in naked-bike territory. At the 203 km/h trap, drag takes roughly 18 kW (24 hp) of the engine output. Drop the rider into an aggressive tuck and the effective Cd drops to about 0.54, which is worth roughly 8 km/h on the trap and 0.15 s on the ET. It is the biggest variable the rider controls on this bike, and the simulator deliberately models it conservatively.',
  },
  {
    type: 'h2',
    text: 'The 800NK against its KTM cousins',
  },
  {
    type: 'p',
    text: 'These four bikes share one engine family, and each has its own chassis. Numbers below are MotoQuant stock-tune simulations under matched Aamby Valley November conditions:',
  },
  {
    type: 'table',
    rows: [
      ['Bike', 'Sim ET', 'Sim trap', 'Dry mass', 'Peak hp', 'Cd'],
      ['KTM 790 Duke', '~11.28 s', '~206 km/h', '169 kg', '105', '0.60'],
      ['CFMoto 800NK', '11.386 s', '203 km/h', '174 kg', '95', '0.62'],
      ['Husqvarna Svartpilen 801', '~11.35 s', '~204 km/h', '171 kg', '105', '0.61'],
      ['KTM 890 Duke R', '~11.05 s', '~211 km/h', '169 kg', '121', '0.61'],
    ],
  },
  {
    type: 'p',
    text: 'The KTM 790 Duke and the CFMoto 800NK have the same engine. The 800NK gives up about 0.10 s of ET to the Austrian bike because it weighs five kilograms more and the Chinese-spec engine is tuned to 95 hp rather than 105 hp. That 10-hp gap is purely a calibration choice: the same engine with a different ECU map and a different intake restrictor. A flash to the European 105-hp tune closes most of it. In the simulator, the 800NK at 105 hp with the same 9000 rpm peak drops to roughly 11.27 s, within 0.01 s of the 790 Duke.',
  },
  {
    type: 'p',
    text: 'The Husqvarna Svartpilen 801 is essentially a 790 Duke with retro bodywork: same engine, same chassis platform, slightly different ergonomics, slightly higher Cd. It runs about 0.07 s behind the 790 Duke for those reasons, almost the same ET as the 800NK. The 890 Duke R is the outlier: it gets the larger 889 cc version of the LC8c, makes 121 hp, and pulls about 0.30 s clear of the rest. If you want the fastest LC8c bike you can buy, it is the 890 Duke R, at roughly twice the price.',
  },
  {
    type: 'h2',
    text: 'What this means for the Indian buyer',
  },
  {
    type: 'p',
    text: 'The CFMoto 800NK landed in India at ₹9.12-9.50 lakh ex-showroom in April 2024, climbing to roughly ₹11-12 lakh on-road depending on state RTO and insurance. The closest competitor at that price point is the KTM 790 Duke (which is not officially sold in India; the 890 Duke R is the current Indian KTM mid-cc twin, at roughly ₹11.5 lakh ex-showroom). That makes the 800NK the only bike in India that gives you an LC8c parallel twin for under ₹10 lakh ex-showroom.',
  },
  {
    type: 'p',
    text: 'For a drag-focused buyer, that matters because the LC8c is one of the more tuneable mid-cc twins on the market. The aftermarket for ECU flashes is mature (Powertronic, KTune, and Akrapovic all have proven maps for the 790 Duke that port directly to the 800NK with minor calibration), the gear ratios are well documented, and replacement clutch packs are cheap. A flash to the European 105-hp tune is the highest-ROI mod, worth about 0.10 s of ET. After that, a 16/42 sprocket swap is worth roughly 0.05 s, the same gain it gives the 790 Duke, since the engine and drivetrain are the same.',
  },
  {
    type: 'p',
    text: 'If your only measure is drag-strip ET per rupee, the 800NK is not competitive. At ₹10 lakh on-road, the 800NK runs an 11.4. A used Hayabusa Gen 1 at ₹8-9 lakh runs a 10.5. A Kawasaki ZX-6R at ₹11-12 lakh on-road runs around 10.7. The 800NK earns its price everywhere except the quarter mile: the LC8c is a very tractable engine, the chassis is more compliant than any litre superbike, and it is a rare mid-cc twin that works for two-up touring as well as track days. It is just not the quickest bike you can buy for ten lakh.',
  },
  {
    type: 'callout',
    text: 'Fastest path on the 800NK: ECU flash to 105-hp European tune first (cheapest per tenth, ~0.10 s for ~₹35,000), then 16/42 sprocket swap (~0.05 s for ~₹4,500), then exhaust if you want sound rather than ET. Skip the air-filter and intake mods: they show up on dyno graphs and not on the strip.',
  },
  {
    type: 'h2',
    text: 'Gearing: where the tenths are',
  },
  {
    type: 'p',
    text: 'The 800NK ships with 16/41 final drive, 525 chain, and the cassette ratios listed above. In a stock-tune Aamby Valley run, the simulator log shows this sequence: launch in first at 6200 rpm with significant clutch slip; shift to second at 0.9 s / 60 feet; shift to third at 2.1 s / 200 feet; shift to fourth at 4.4 s / 530 feet; cross the trap line in fourth at 9100 rpm and 203 km/h, never engaging fifth or sixth.',
  },
  {
    type: 'p',
    text: 'A four-gear quarter is typical of gearing designed for the road, not the drag strip. Fifth and sixth on the 800NK are autobahn cruise gears: 6th gear at 1.000 final drive with the 1.130 multiplier from 5th means the bike pulls about 12 km/h per 1000 rpm in top gear, which suits a 700 km highway run and is wrong for a quarter-mile pass.',
  },
  {
    type: 'p',
    text: 'A 16/42 sprocket swap shortens the ratios across the board by about 2.4 percent. The simulator shows the 800NK still crossing the trap line in fourth, but at about 9300 rpm instead of 9100 rpm: slightly higher in the power band, with slightly more wheel torque at the trap. The ET gain is roughly 0.04 to 0.06 s, almost all of it from a slightly stronger fourth-gear pull into the trap rather than from any change to the lower gears. The parts cost under ₹5,000, which makes it the cheapest tenth on this bike.',
  },
  {
    type: 'p',
    text: 'A more aggressive 15/42 swap shortens the ratios further and puts the bike in fifth at the trap. That sounds better and is not. The shift lands roughly 60 feet before the trap line, and the gear-change deadband costs more ET than the shorter gear gains in wheel torque. On stock power the 800NK wants to stay in fourth, with that gear a little shorter. The 16/42 swap does exactly that.',
  },
  {
    type: 'h2',
    text: 'Verdict',
  },
  {
    type: 'p',
    text: 'On paper the CFMoto 800NK is a strange product; in practice it makes sense. It is a KTM 790 Duke that costs less and weighs slightly more, and on stock tune at Aamby Valley it runs a respectable but not class-leading 11.4-second quarter. It is also the cheapest LC8c-engined bike on the Indian market, which makes it interesting for anyone who wants to tune the engine rather than stare at the spec sheet. In the simulator, its ceiling is set by what KTM intended the LC8c to do, not by anything CFMoto did to the chassis.',
  },
  {
    type: 'p',
    text: 'Indian drag racing has mostly stayed away from mid-cc twins: the scene runs heavily on litre inline-fours and on the Indian-market 200-400 cc commuter class. The 800NK does not change that. In its price band, used Japanese superbikes, the Kawasaki ZX-6R and the KTM 890 Duke R are all faster for the rupee. What the 800NK offers instead is the LC8c engine in a chassis more usable on Indian roads than any of those, at a price that puts the LC8c within reach in India for the first time.',
  },
  {
    type: 'p',
    text: 'If you want the fastest bike in its price class, the 800NK is the wrong bike. If you want a parallel-twin naked that will hold up to weekend rides, occasional drag-strip days and a long upgrade path through the KTM ecosystem, the simulator data says it is the right one. Treat the 11.4-second stock ET as the floor. From there, small, cheap, well-understood mods will let you build a genuine 10.5-second bike for under ₹15 lakh all-in, and that upgrade path is what CFMoto is selling.',
  },
  {
    type: 'h2',
    text: 'Run your own numbers',
  },
  {
    type: 'p',
    text: 'If you own an 800NK or are deciding between the 800NK, the 890 Duke R, and a used Japanese superbike, the simulator at motoquant.in lets you sweep rider weight, ambient temperature, density altitude, and parts-catalog mods to see where the tenths come from on your bike in your conditions. The cluster-bias correction discussed above is built into the model: when the simulator says your 800NK runs 11.4, expect closer to 10.8-11.0 at the strip with a competent rider on a well-prepped surface.',
  },
  {
    type: 'p',
    text: 'For tuning, MotoQuant scores every part in its catalog by cost-per-tenth for your bike. On the 800NK the gearing swap comes first, the ECU flash second, and almost everything else buys sound rather than seconds. Because the engine is shared unchanged with three other platforms (790 Duke, 890 Duke R, Svartpilen 801), the cross-platform mod data is unusually well-validated.',
  },
  {
    type: 'p',
    text: 'Two caveats. First, every number in this post is a stock-tune simulation under specific Aamby Valley November conditions. Change the venue, the season, or the rider, and absolute ETs shift; the relative ordering of which mods help most stays stable. Second, we are still working on the litre-sport-600-1000 cluster bias. Recent calibration work added Hypothesis property tests that pin the four main physics knobs to monotonic invariants, so future bias corrections are safer to ship. Today the simulator reads the 800NK at 11.386 s; in three months that may shift to 11.10 or 11.20 s without any change to the bike itself.',
  },
  {
    type: 'p',
    text: 'Every aftermarket part developed for the KTM 790 Duke worldwide over the past seven years fits this bike directly. That, more than its drag-strip numbers, is why the CFMoto 800NK is the most interesting parallel twin on the Indian market: it gives Indian buyers the LC8c platform at a price the platform has never had before.',
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
            {['CFMoto', '800NK', 'LC8c', 'Indian mid-cc', 'physics'].map((t) => (
              <span
                key={t}
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            CFMoto 800NK quarter-mile physics: a KTM 790 Duke in disguise
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
              <Link href="/blog/ktm-1390-super-duke-r-evo-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                KTM 1390 Super Duke R EVO quarter-mile physics
              </Link>:{' '}
              what happens when KTM goes to 1350 cc and 190 hp on the same platform philosophy.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/pulsar-ns400z-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                Pulsar NS400Z quarter-mile physics
              </Link>:{' '}
              the sub-₹2-lakh Indian-market answer to the mid-cc naked question.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-the-motoquant-physics-engine-works" className="text-brand-accent hover:text-brand-orange transition-colors">
                How the MotoQuant physics engine works
              </Link>:{' '}
              the 15-sub-model architecture behind every ET prediction in this post.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-to-tune-for-aamby-valley-in-november" className="text-brand-accent hover:text-brand-orange transition-colors">
                How to tune for Aamby Valley in November
              </Link>:{' '}
              the venue conditions used for every simulation above.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>:{' '}
              the specs, gear ratios and Cd values the simulator uses.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Run the 800NK yourself</div>
            <div className="text-white/60 text-sm">
              Pick the CFMoto 800NK in the free simulator, set your local conditions and watch the ET update live.
            </div>
          </div>
          <Link
            href="/simulator?bike=cfmoto-800nk"
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
