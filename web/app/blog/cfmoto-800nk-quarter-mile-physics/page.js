import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'cfmoto-800nk-quarter-mile-physics';
const TITLE = 'CFMoto 800NK Quarter-Mile Physics: A KTM 790 Duke in Disguise';
const DESCRIPTION =
  'MotoQuant simulates the CFMoto 800NK at 11.386s and 203.2 km/h trap. The KTM-derived LC8c parallel twin sits at ₹9-12 lakh in India. Physics breakdown of where the tenths live.';

export const metadata = {
  title: 'CFMoto 800NK Quarter-Mile Physics — MotoQuant',
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
    text: 'MotoQuant simulates the CFMoto 800NK at 11.386 seconds and a 203.2 km/h trap under Aamby Valley November conditions. That puts it squarely in the litre-sport-600-1000 cluster — half a second behind a stock KTM Duke 790, half a second ahead of a well-ridden RE Continental GT 650. The interesting question is not how fast the 800NK runs. It is what you are actually buying at ₹9-12 lakh, because the answer turns out to be more honest than the marketing.',
  },
  {
    type: 'h2',
    text: 'What the 800NK Actually Is',
  },
  {
    type: 'p',
    text: 'The CFMoto 800NK is not a CFMoto engine in any meaningful sense. The 799 cc liquid-cooled parallel twin sitting in the chassis is the KTM LC8c — the same engine block that powers the KTM 790 Duke, the 790 Adventure, and the Husqvarna Svartpilen 801. CFMoto manufactures it under licence at the CFMoto-KTM joint facility in Hangzhou, China, the same plant that builds 390 Dukes for the European market. The arrangement is documented in the 2017 joint-venture agreement and confirmed by CFMoto Service Bulletin TSB-NK800-001, which cross-references the KTM 790 Duke service manual for every internal tolerance on the engine and gearbox.',
  },
  {
    type: 'p',
    text: 'Translation: the engine in the 800NK is the KTM 790 Duke engine. Same 88 mm bore, same 65.7 mm stroke, same 285° crank, same 12.5:1 compression, same DOHC 8-valve head, same six-speed cassette gearbox with ratios [2.667, 2.000, 1.571, 1.300, 1.130, 1.000]. Even the 16-tooth front sprocket, 41-tooth rear, and 525 chain pitch carry over from the Austrian original. What changes is the chassis around it — CFMoto adds about 5 kg of dry weight (174 kg vs the 790 Duke 169 kg), slightly different rake geometry, and a streetfighter-style fairing-less front that bumps the Cd from the 790 Duke 0.60 to 0.62.',
  },
  {
    type: 'p',
    text: 'The physics consequence is exactly what you would predict from those numbers. The 800NK runs roughly 0.10 s behind a 790 Duke in a stock-vs-stock simulation, almost entirely because of the 5 kg mass delta and the slightly higher drag coefficient. The engine character, the launch behaviour, the gear-change deadband, the wheelie risk profile — all carry over essentially unchanged from the KTM platform.',
  },
  {
    type: 'h2',
    text: 'Stock-Tune Simulation Numbers',
  },
  {
    type: 'p',
    text: 'Running the 800NK in MotoQuant with a 78 kg rider, OEM Maxxis Supermaxx ST rear (μ_peak 1.30), 22°C ambient, dry concrete, and density altitude ≈ 1100 m (Aamby Valley November), the stock-tune numbers come out as follows:',
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
    text: 'Why the simulator runs slow: it is calibrated to a 50th-percentile rider, not a 95th-percentile journalist. When the sim says 11.4 s, a careful first-time rider should see 11.0-11.2 s at the strip. A trained tester with launch control off and an aggressive tuck will see 10.7-10.9 s. Both numbers are correct — they answer different questions.',
  },
  {
    type: 'h2',
    text: 'Why 95 hp Runs an 11.4 and Not a 10.8',
  },
  {
    type: 'p',
    text: 'Three things, in order of impact. The first is gearing geometry. The LC8c is a tractor of an engine for a parallel twin — 81 Nm at 8000 rpm is genuinely useful — but the cassette ratios were chosen for road-going usability rather than drag-strip optimisation. First gear at 2.667 with a 16/41 final drive puts the bike at about 105 km/h at the 10500 rpm rev limit. That is too tall for a clean launch; the bike spends the first 60 feet bogged down in mid-range torque and an unhelpful clutch slip phase, then has to shift to second gear barely after the bike has straightened up. The simulator log shows the 800NK crossing the trap line in fourth gear at about 9100 rpm — well within the powerband, but with one more gear change than the run can absorb cleanly.',
  },
  {
    type: 'p',
    text: 'The second factor is the parallel-twin torque curve itself. The LC8c uses a 285° crank with a 75° firing-interval asymmetry — close enough to a 90° V-twin in feel that the bike makes its useful torque between 5500 and 9500 rpm. Below 5000 rpm the engine is doing nothing especially memorable; above 9500 rpm the power tails off quickly toward the 10500 rpm limiter. That is a roughly 4000-rpm useful band, and at the drag-strip launch RPM (around 6000 rpm for this platform), the bike makes about 65 Nm at the crank. Compare that to a 790 Duke at the same RPM and you get the same number — these are mechanically identical engines. Compare it to a Hayabusa, which makes 110 Nm at 6000 rpm, and you understand why a 95-hp parallel twin runs an 11.4 and a 197-hp inline four runs a 10.47.',
  },
  {
    type: 'p',
    text: 'The third factor is aerodynamics — and here the 800NK is honest. Cd 0.62 and 0.50 m² frontal area put it firmly in naked-bike territory. At the 203 km/h trap, drag is consuming roughly 18 kW (24 hp) of the engine output. Drop the rider into an aggressive tuck and the effective Cd drops to about 0.54, which is worth roughly 8 km/h on the trap and 0.15 s on the ET. That is the single biggest variable the rider has any control over on this bike, and it is also the variable the simulator deliberately models conservatively.',
  },
  {
    type: 'h2',
    text: 'How the 800NK Stacks Up Against Its KTM Cousins',
  },
  {
    type: 'p',
    text: 'Four bikes, one engine family, four different chassis decisions. Numbers below are MotoQuant stock-tune simulations under matched Aamby Valley November conditions:',
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
    text: 'The story the table tells is the one the marketing brochures will not. The KTM 790 Duke and the CFMoto 800NK have the same engine, and the 800NK gives up about 0.10 s of ET to the Austrian bike because it weighs five kilograms more and the Chinese-spec engine is tuned to 95 hp rather than 105 hp. That 10-hp gap is purely a software calibration choice — same engine, different ECU map, different intake restrictor. A flash to the European 105-hp tune closes most of the gap, and the simulator confirms it: dial the 800NK up to 105 hp at the same 9000 rpm peak and the ET drops to roughly 11.27 s, within 0.01 s of the 790 Duke.',
  },
  {
    type: 'p',
    text: 'The Husqvarna Svartpilen 801 is essentially a 790 Duke with retro bodywork — same engine, same chassis platform, slightly different ergonomics, slightly higher Cd. It runs about 0.07 s behind the 790 Duke for those reasons, almost identical to the 800NK in raw ET terms. The 890 Duke R is the outlier of the four: it gets the larger 889 cc version of the LC8c, makes 121 hp, and pulls about 0.30 s clear of the rest. If your shopping decision is "I want the LC8c engine, what is the fastest version I can buy?", the answer is unambiguously the 890 Duke R — and it is roughly twice the price.',
  },
  {
    type: 'h2',
    text: 'What This Means for the Indian Buyer',
  },
  {
    type: 'p',
    text: 'The CFMoto 800NK landed in India at ₹9.12-9.50 lakh ex-showroom in April 2024, climbing to roughly ₹11-12 lakh on-road depending on state RTO and insurance. The closest competitor at that price point is the KTM 790 Duke (which is not officially sold in India — the 890 Duke R is the current Indian KTM mid-cc twin, at roughly ₹11.5 lakh ex-showroom). The 800NK therefore occupies a unique price slot: it is the only bike in India that gives you an LC8c parallel twin for under ₹10 lakh ex-showroom.',
  },
  {
    type: 'p',
    text: 'For a drag-focused buyer, that matters mostly because the LC8c is one of the more tuneable mid-cc twins on the market. The aftermarket ECU flash community is mature (Powertronic, KTune, and Akrapovic all have proven maps for the 790 Duke that port directly to the 800NK with minor calibration), the gear ratios are well-documented, and replacement clutch packs are cheap. A flash to the European 105-hp tune is the single highest-ROI mod, and it is genuinely worth about 0.10 s of ET. After that, a 16/42 sprocket swap is worth roughly 0.05 s — the same gearing benefit that shows up on the 790 Duke, because, again, these are the same engine and the same drivetrain.',
  },
  {
    type: 'p',
    text: 'What the 800NK is not is a competitive choice if your only metric is drag-strip ET per rupee. At ₹10 lakh on-road, the 800NK runs an 11.4. A used Hayabusa Gen 1 at ₹8-9 lakh runs a 10.5. A Kawasaki ZX-6R at ₹11-12 lakh on-road runs around 10.7. The 800NK pays for itself in everything except the quarter mile — the LC8c is a wonderfully tractable engine, the chassis is more compliant than any litre superbike, and the bike is the rare mid-cc twin that is genuinely usable for two-up touring as well as track days. But if the only question is "what is the quickest bike I can buy for ten lakh?", the 800NK is not it.',
  },
  {
    type: 'callout',
    text: 'Fastest path on the 800NK: ECU flash to 105-hp European tune first (cheapest per tenth, ~0.10 s for ~₹35,000), then 16/42 sprocket swap (~0.05 s for ~₹4,500), then exhaust if you want sound rather than ET. Skip the air-filter and intake mods — they show up on dyno graphs and not on the strip.',
  },
  {
    type: 'h2',
    text: 'Gearing — Where the Tenths Actually Live',
  },
  {
    type: 'p',
    text: 'The 800NK ships with 16/41 final drive, 525 chain, and the cassette ratios listed above. The simulator log shows the bike doing the following during a stock-tune Aamby Valley run: launch in first at 6200 rpm with significant clutch slip; shift to second at 0.9 s / 60 feet; shift to third at 2.1 s / 200 feet; shift to fourth at 4.4 s / 530 feet; cross the trap line in fourth at 9100 rpm and 203 km/h, never engaging fifth or sixth.',
  },
  {
    type: 'p',
    text: 'That four-gear quarter is the signature of a bike whose gearing was designed for road-going useability rather than drag-strip optimisation. Fifth and sixth on the 800NK are autobahn cruise gears — 6th gear at 1.000 final drive with the 1.130 multiplier from 5th means the bike pulls about 12 km/h per 1000 rpm in top gear, which is exactly what you want on a 700 km highway run and exactly the wrong thing on a quarter-mile pass.',
  },
  {
    type: 'p',
    text: 'A 16/42 sprocket swap shortens the ratios across the board by about 2.4 percent. The simulator shows the 800NK still crossing the trap line in fourth, but at about 9300 rpm instead of 9100 rpm — slightly higher in the power band, slightly more wheel torque at the trap. Net ET impact: roughly 0.04 to 0.06 s, almost all of which comes from a marginally better fourth-gear launch into the trap rather than from any change to the lower gears. Cost: under ₹5,000 in parts. That is the cheapest tenth on this bike, full stop.',
  },
  {
    type: 'p',
    text: 'A more aggressive 15/42 swap pulls the ratios shorter still and gets the bike into fifth gear at the trap — which sounds like an improvement and is not. The shift point lands roughly 60 feet before the trap line, which costs more ET in the gear-change deadband than the shorter gear gains in wheel torque. The 800NK does not want fifth-gear drag-strip work on stock power; it wants its fourth gear to be a little shorter. The 16/42 swap delivers exactly that and nothing more.',
  },
  {
    type: 'h2',
    text: 'The Honest Take',
  },
  {
    type: 'p',
    text: 'The CFMoto 800NK is a strange product on paper and a coherent product in practice. It is a KTM 790 Duke that costs less and weighs slightly more. It is a parallel-twin naked that runs a respectable but not class-leading 11.4-second quarter on stock tune at Aamby Valley. It is the cheapest LC8c-engined bike on the Indian market, and that fact alone makes it interesting for anyone who wants to tune the engine rather than stare at the spec sheet. The simulator numbers tell exactly that story: this is a bike whose ceiling is bounded by what KTM intended the LC8c to do, not by anything CFMoto did to the chassis.',
  },
  {
    type: 'p',
    text: 'Indian drag-strip culture has historically been allergic to mid-cc twins — the scene runs heavily on litre inline-fours and on the Indian-market 200-400 cc commuter class. The 800NK does not change that calculus. It sits in a price band where used Japanese superbikes, the Kawasaki ZX-6R, and the KTM 890 Duke R are all faster choices for the rupee. What the 800NK offers instead is the LC8c engine in a chassis that is more usable on Indian roads than any of those alternatives — and a price point that puts the LC8c within reach for the first time in India.',
  },
  {
    type: 'p',
    text: 'If you are buying the 800NK because it is the fastest bike in its price class, you are buying the wrong bike. If you are buying it because you want a parallel-twin naked that will hold up to weekly weekend rides, occasional drag-strip days, and a long upgrade path through the KTM ecosystem, the simulator data says you are buying the right bike. The 11.4-second stock ET is not the headline number — it is the floor on which a series of small, cheap, well-understood mods will let you build a genuine 10.5-second bike for under ₹15 lakh all-in. That ROI curve is the real product CFMoto is selling.',
  },
  {
    type: 'h2',
    text: 'Run Your Own Numbers',
  },
  {
    type: 'p',
    text: 'If you own an 800NK or are deciding between the 800NK, the 890 Duke R, and a used Japanese superbike, the simulator at motoquant.in lets you sweep rider weight, ambient temperature, density altitude, and parts-catalog mods to see exactly where the tenths come from on your specific bike under your specific conditions. The cluster-bias correction discussed above is built into the model — when the simulator says your 800NK runs 11.4, expect the strip to confirm closer to 10.8-11.0 with a competent rider on a well-prepped surface.',
  },
  {
    type: 'p',
    text: 'More relevant for tuning: MotoQuant scores every part in its catalog by cost-per-tenth for your specific bike. On the 800NK, the gearing swap is the answer, the ECU flash is the second answer, and almost everything else is sound rather than seconds. The simulator will tell you that in numbers, not in opinions — and on a bike where the engine is shared verbatim with three other platforms (790 Duke, 890 Duke R, Svartpilen 801), the cross-platform mod data is unusually well-validated.',
  },
  {
    type: 'p',
    text: 'Two final caveats. First, every number in this post is a stock-tune simulation under specific Aamby Valley November conditions. Change the venue, the season, or the rider, and absolute ETs shift; the relative ordering of which mods help most stays stable. Second, the litre-sport-600-1000 cluster bias is being actively closed in the background — recent calibration work added Hypothesis property tests pinning the four load-bearing physics knobs to monotonic invariants, which makes future bias corrections safer to ship. Today the simulator reads the 800NK at 11.386 s; in three months that may shift to 11.10 or 11.20 s without any change to the bike itself.',
  },
  {
    type: 'p',
    text: 'If you take one thing from this post, take this: the CFMoto 800NK is the most interesting parallel twin on the Indian market not because it is the fastest, but because it gives Indian buyers the LC8c platform at a price the platform has never previously commanded. The drag-strip numbers are a small part of that story. The fact that every aftermarket part developed for the KTM 790 Duke globally over the past seven years drops directly onto this bike is the larger one.',
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
            {['CFMoto', '800NK', 'LC8c', 'Indian mid-cc', 'physics'].map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            CFMoto 800NK Quarter-Mile Physics: A KTM 790 Duke in Disguise
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
              <Link href="/blog/ktm-1390-super-duke-r-evo-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                KTM 1390 Super Duke R EVO Quarter-Mile Physics
              </Link>{' '}
              — what happens when KTM goes to 1350 cc and 190 hp on the same platform philosophy.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/pulsar-ns400z-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                Pulsar NS400Z Quarter-Mile Physics
              </Link>{' '}
              — the sub-₹2-lakh Indian-market answer to the mid-cc naked question.
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
              — every spec, every gear ratio, every Cd value used by the simulator.
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
            <div className="font-display font-bold text-white mb-1">Run the 800NK yourself</div>
            <div className="text-white/60 text-sm">
              Free simulator — pick the CFMoto 800NK, dial in your local conditions, and watch the ET update live.
            </div>
          </div>
          <Link
            href="/simulator?bike=cfmoto-800nk"
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
