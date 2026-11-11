import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema, OG_IMAGE } from '../../StructuredData';
import PostBikeLinks from '../../../components/PostBikeLinks';

const SLUG = 'suzuki-gsx-s750-vs-ktm-890-duke-quarter-mile';
const TITLE = 'Suzuki GSX-S750 vs KTM 890 Duke: Quarter-mile physics';
const DESCRIPTION =
  'MotoQuant simulates the GSX-S750 at 11.58s and the 890 Duke at 11.42s. The Duke is 27 kg lighter and 0.16s quicker. How mass beats displacement at the strip, and what limits each bike.';

export const metadata = {
  title: 'Suzuki GSX-S750 vs KTM 890 Duke quarter mile',
  description: DESCRIPTION,
  keywords: [
    'Suzuki GSX-S750 quarter mile',
    'KTM 890 Duke quarter mile',
    'GSX-S750 vs 890 Duke drag race',
    'GSX-S750 0-100',
    '890 Duke drag strip India',
    'mid-cc naked bike quarter mile',
    'suzuki 750 vs ktm 890 comparison',
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
    text: "MotoQuant simulates the Suzuki GSX-S750 at 11.58 seconds and 193 km/h trap, and the KTM 890 Duke at 11.42 seconds and 196 km/h trap. The 890 Duke weighs 27 kg less and wins by 0.16 seconds. Mass is not the only reason, though, and over one part of the run a stock GSX-S750 is faster than a stock 890 Duke.",
  },
  {
    type: 'h2',
    text: "The two bikes and what they are",
  },
  {
    type: 'p',
    text: "The Suzuki GSX-S750 (2015–2021) puts the 2005–2006 GSX-R750 K5/K6 engine in a naked bike. It keeps the 70 mm bore, the 48.7 mm stroke and the basic combustion chamber geometry, with revised cam profiles that pull the power delivery toward the mid-range and move the torque peak up to 9,000 rpm. The result is a 114 hp / 81 Nm inline-four that makes most of its power between 8,000 and 11,000 rpm. On the road it feels effortless and slightly droney. On a drag strip it means the bike works against its own preference for revs in gear 1, where you never touch 10,000 rpm.",
  },
  {
    type: 'p',
    text: "The KTM 890 Duke (2020–2023) is the standard, non-R variant of the LC8c parallel twin. It makes 105 hp at 8,000 rpm and 92 Nm at 6,500 rpm: 9 hp less than the GSX-S750 on paper, but 11 Nm more torque, with the peak arriving 2,500 rpm earlier. Its dry mass is 166 kg on the KTM EU spec sheet, against 193 kg for the GSX-S750. That 27 kg difference is roughly one adult passenger removed from the Suzuki.",
  },
  {
    type: 'p',
    text: "Both bikes are in the MotoQuant catalog. The GSX-S750 uses its own gear cassette, taken from Suzuki service manual 99500-36160-03E; the GSX-R750 K5/K6 transmission is a different unit. The 890 Duke shares its gearbox cassette with the 890 Duke R (confirmed in KTM service manual KTM-TI-2020-890D). The GSX-S750 runs 16F/45R sprockets and the 890 Duke runs 15F/42R, both on 520-pitch chain.",
  },
  {
    type: 'h2',
    text: "The simulation numbers",
  },
  {
    type: 'p',
    text: "Both bikes ran through MotoQuant in Aamby Valley November conditions: density altitude approximately 1,100 m, 22°C ambient, dry asphalt, a 78 kg rider and OEM Bridgestone tires. The stock-tune numbers:",
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'GSX-S750', '890 Duke', 'Gap'],
      ['Quarter-mile ET', '11.58 s', '11.42 s', '−0.16 s (Duke wins)'],
      ['Trap speed', '193 km/h', '196 km/h', '+3 km/h (Duke)'],
      ['60-foot time', '~1.98 s', '~1.88 s', '−0.10 s (Duke)'],
      ['Power-to-weight', '0.591 hp/kg', '0.633 hp/kg', '+7.1% (Duke)'],
      ['Sim cluster bias', '+0.18 s documented', '+0.18 s documented', 'matched'],
    ],
  },
  {
    type: 'p',
    text: "The 0.18s documented bias belongs to the litre_sport_600_1000 cluster, which both bikes fall into because both sit between 600 and 1000cc. Motorcycle Consumer News measured a stock GSX-S750 test bike at 11.4s and 194 km/h in November 2017. The simulator's 11.58s is 0.18s over that result, inside the documented +0.15–0.22s bias band for this cluster. The bias runs the expected way: the simulator is calibrated to a 50th-percentile rider, not a trained journalist making drag runs optimised with launch control.",
  },
  {
    type: 'callout',
    text: "The MotoQuant benchmark list has no instrumented quarter-mile record for the stock 890 Duke (as distinct from the 890 R and the 790 Duke). KTM factory literature puts 0-100 km/h at 3.1 seconds for the standard 890 Duke, which works out to approximately 11.3–11.5s over the quarter depending on trap speed. The simulator's 11.42s falls in that range. If you have a Dragy run on a stock 890 Duke, the import-dragy CLI can calibrate the simulator to your bike.",
  },
  {
    type: 'h2',
    text: "Why mass wins more than displacement",
  },
  {
    type: 'p',
    text: "A naive prediction, looking at a 749cc I4 against an 889cc parallel twin, would favour the bigger-displacement bike. That prediction is wrong.",
  },
  {
    type: 'p',
    text: "Over the first 60 feet of a quarter mile, the limit is not peak power. It is the available traction multiplied by the force the drivetrain can put at the rear wheel. Grip is comparable on both bikes (Bridgestone S21/S22 OEM fitments, μ_peak ≈ 1.35), and at any given wheel force the lighter bike accelerates faster. At 166 kg dry, the 890 Duke needs only 90 N of net force per unit acceleration, where the 193 kg GSX-S750 needs 111 N for the same rate. The Duke can launch harder before the front wheel lifts, and that traction advantage compounds through first gear.",
  },
  {
    type: 'p',
    text: "The GSX-S750 wins some of this back in the top half of the run. Between 130 and 190 km/h, with the engine pulling through 9,000–10,500 rpm, the inline-four makes more power than the parallel twin: its torque curve holds up better past 9,000 rpm, while the LC8c twin starts to fall off around 8,500 rpm. That is why the trap speed gap is only 3 km/h rather than 6 or 7 km/h, even though the Suzuki clearly loses the launch.",
  },
  {
    type: 'p',
    text: "On a 200 m sprint instead of a 402 m quarter, the result would likely be much closer. The Duke's launch advantage would dominate, but it would not have had time to compress into the trap. At 402 m the deficit is 0.16s; at 200 m it would be closer to 0.25s, because the Suzuki has less time to recover.",
  },
  {
    type: 'h2',
    text: "Gearing: Where the tenths are",
  },
  {
    type: 'p',
    text: "GSX-S750 gearing: [2.615, 1.882, 1.500, 1.261, 1.103, 0.966] with 16F/45R. Effective final drive ratio in 6th (0.966 × 16/45) = 0.343. With a 180/55ZR17 rear tire at approximately 295 mm rolling radius, top speed in 6th at full redline (12,000 rpm) is roughly 240 km/h. At a 193 km/h trap the bike crosses the timing beam in 5th gear, short of 5th gear's redline. The 6th-gear overdrive is a highway gear that never does drag-strip work.",
  },
  {
    type: 'p',
    text: "KTM 890 Duke gearing: [2.625, 1.941, 1.580, 1.346, 1.185, 1.071] with 15F/42R. Effective final drive in 6th (1.071 × 15/42) = 0.383. With a 180/55ZR17 rear, top speed in 6th at 9,000 rpm (peak power) is approximately 207 km/h. At a 196 km/h trap the Duke crosses the line right at peak-power rpm in 6th, which is nearly ideal. Its gearing is shorter and better matched to its powerband for a drag strip.",
  },
  {
    type: 'p',
    text: "The gearing difference accounts for a real part of the ET gap. The GSX-S750's taller gearing means more time in the gear-change deadband before 5th gear can pull through to trap speed. A sprocket swap to 16F/42R on the Suzuki (shortening final drive by ~7%) would move the trap crossing into 6th gear and likely recover 0.04–0.06s. A JT sprocket pair in 520 pitch costs approximately ₹3,200, which makes it one of the lowest cost-per-tenth mods in the catalog.",
  },
  {
    type: 'h2',
    text: "Where each bike loses time: Section by section",
  },
  {
    type: 'table',
    rows: [
      ['Section', 'GSX-S750 loses time because…', '890 Duke loses time because…'],
      [
        '0–60 ft',
        'Heavier; front wheel lifts sooner at same throttle, forces throttle back',
        'Narrower powerband at low RPM; must be more precise with launch RPM',
      ],
      [
        '60 ft–330 ft',
        'Mass compounds through gear 1→2 shift; torque peak at 9,000 rpm not yet reached',
        'Recovers here; 92 Nm at 6,500 rpm means strong pull into gear 2 immediately',
      ],
      [
        '330 ft–trap',
        'Recovers via inline-four high-RPM pull; trap penalty is only 3 km/h vs Duke',
        'Twin power curve softens above 8,500 rpm; Suzuki making up ground at 10,000+ rpm',
      ],
      [
        'Overall',
        '0.16 s slower; mass is the dominant lever, not displacement',
        '0.16 s quicker; gearing + power-to-weight advantage > Suzuki top-end power',
      ],
    ],
  },
  {
    type: 'h2',
    text: "The Indian market context",
  },
  {
    type: 'p',
    text: "The Suzuki GSX-S750 was officially sold in India in limited batches as a CBU import. Used 2018–2020 bikes in good condition typically sell for ₹6–8 lakh on IndiaMART and BikeWale, which makes it one of the most accessible liquid-cooled inline-fours for the Indian drag scene. The 890 Duke was never officially launched in India as a standalone model (only the Duke 390 and Duke 790 had proper CKD/CBU launches), but grey-market bikes arrive via Nepal and Dubai at approximately ₹10–12 lakh. Most 890 Duke owners in India ride the 890 R, which costs the same and has 16 hp more (121 hp) and slightly different suspension.",
  },
  {
    type: 'p',
    text: "For drag strip use at Aamby Valley or MMRT, the GSX-S750 at ₹7 lakh gives you an 11.58s bike that responds well to gearing and ECU tuning. The 890 Duke at ₹11 lakh gives you an 11.42s bike that is lighter from the factory but harder to find. If you want the lowest cost per second over the quarter mile, a used GSX-S750 with a sprocket swap and a Woolich ECU flash (₹25,000) gets you to approximately 11.4s for around ₹7.25 lakh all-in, competitive with a stock 890 Duke for a fraction of the purchase price.",
  },
  {
    type: 'p',
    text: "Off the strip, the comparison flips. The 890 Duke is noticeably lighter to throw around corners, and 92 Nm at 6,500 rpm makes it easy to ride fast without being in the powerband. The GSX-S750 feels more planted but asks you to work the revs harder.",
  },
  {
    type: 'h2',
    text: "Three mods per bike worth doing",
  },
  {
    type: 'p',
    text: "For the GSX-S750, in priority order:",
  },
  {
    type: 'table',
    rows: [
      ['Mod', 'ET gain', 'Cost (approx.)', 'Cost per tenth'],
      ['16F/42R sprocket pair (JT)', '~0.05 s', '₹3,200', '₹6,400/tenth'],
      ['Woolich Racing ECU tune (GSX-S750 map)', '~0.08 s', '₹28,000', '₹35,000/tenth'],
      ['Akrapovic Slip-On (750cc size)', '~0.04 s', '₹65,000', '₹162,500/tenth'],
    ],
  },
  {
    type: 'p',
    text: "For the KTM 890 Duke, in priority order:",
  },
  {
    type: 'table',
    rows: [
      ['Mod', 'ET gain', 'Cost (approx.)', 'Cost per tenth'],
      ['15F/40R sprocket pair (JT)', '~0.04 s', '₹3,400', '₹8,500/tenth'],
      ['Powertronic ECU map (890 Duke)', '~0.07 s', '₹22,000', '₹31,400/tenth'],
      ['Akrapovic Slip-On (890 Duke)', '~0.04 s', '₹72,000', '₹180,000/tenth'],
    ],
  },
  {
    type: 'callout',
    text: "The pattern is the same on both bikes: sprockets first, with the lowest cost per tenth by a large margin; the ECU second; the exhaust a distant third. The slip-on exhaust is the part riders buy most often for both bikes, because it sounds and looks better, but per tenth it is the worst value. Buy the sprockets, book a dyno day for the ECU tune, and spend what is left on track fees.",
  },
  {
    type: 'h2',
    text: "The physics of the I4 vs twin torque curve",
  },
  {
    type: 'p',
    text: "Run both bikes and look at the gear changes. The GSX-S750's inline-four has its torque curve peaking at 9,000 rpm in a relatively narrow Gaussian band: the synthetic torque curve the simulator builds from the 114 hp / 81 Nm spec points tapers off more steeply below peak-torque rpm than the LC8c twin's curve does.",
  },
  {
    type: 'p',
    text: "So after every upshift the GSX-S750 spends longer below its power peak, waiting for the revs to climb back into the sweet spot. On the 890 Duke, 92 Nm arrives at 6,500 rpm, so after a shift into 2nd or 3rd gear the engine is at its torque peak almost immediately. Across the 402 m the Duke has a wider window of useful traction, and it does not need to rev as hard to find its power.",
  },
  {
    type: 'p',
    text: "The spec sheet does not capture this mid-range advantage of the parallel twin. The inline-four's displacement and redline advantages are real, but they only show up in the top half of the run. By the time the GSX-S750 is using its 114 hp advantage at 10,500 rpm, the Duke is already across the line.",
  },
  {
    type: 'h2',
    text: "Run your own numbers",
  },
  {
    type: 'p',
    text: "If you own either bike or are choosing between them, the MotoQuant simulator lets you set your own conditions: rider weight, ambient temperature, the elevation of your local strip, and parts-catalog mods. Both bikes are in the catalog with Cd values and gear ratios from the service manuals. Each run at motoquant.in/simulator takes about 30 seconds.",
  },
  {
    type: 'p',
    text: "The simulator can rank the mods on each bike (sprockets vs ECU vs exhaust) with high confidence, because the ranking does not depend on whether the absolute ET is 11.42s or 11.25s. It can show the effect of weather and altitude, which helps when you are planning a trip to Aamby Valley from a sea-level city. It cannot tell you the exact ET you will run on your first pass. At this power level, launch technique is the largest uncontrolled variable between riders, worth approximately ±0.2s depending on how well you can modulate the clutch at 6,500 rpm.",
  },
  {
    type: 'p',
    text: "Both bikes reward a precise launch rpm. The GSX-S750 is more forgiving of a slightly low launch rpm because its inline-four builds revs quickly; the 890 Duke needs to be staged closer to its peak-torque rpm to get the front wheel up correctly. The parts ROI output lists the best launch rpm for each bike, and the sensitivity curve for 'staging.launch_rpm' shows where your tenths come from.",
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
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {['Suzuki', 'GSX-S750', 'KTM', '890 Duke', 'comparison', 'mid-cc naked'].map((t) => (
              <span
                key={t}
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Suzuki GSX-S750 vs KTM 890 Duke: Quarter-mile physics
          </h1>
          <div className="text-sm text-white/60 mb-12">
            18 May 2026 · 11 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        <PostBikeLinks ids={[763, 761]} />

        {/* Internal links / related reading */}
        <div className="max-w-2xl mx-auto mt-16">
          <h3 className="font-display font-bold text-lg text-white mb-4">Related reading</h3>
          <ul className="text-sm text-white/70 space-y-2">
            <li>
              ·{' '}
              <Link href="/blog/cfmoto-800nk-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                CFMoto 800NK quarter-mile physics
              </Link>:{' '}
              the other LC8c-derived parallel twin in the Indian market.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/the-physics-of-a-perfect-launch" className="text-brand-accent hover:text-brand-orange transition-colors">
                The physics of a perfect launch
              </Link>:{' '}
              clutch engagement, tire slip, and weight transfer in the first 60 feet.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-to-tune-for-aamby-valley-in-november" className="text-brand-accent hover:text-brand-orange transition-colors">
                How to tune for Aamby Valley in November
              </Link>:{' '}
              the venue conditions used for both simulations in this post.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/hayabusa-vs-zx-14r-which-is-faster" className="text-brand-accent hover:text-brand-orange transition-colors">
                Hayabusa vs ZX-14R: Which is faster off the line?
              </Link>:{' '}
              the same comparison for two hyper-sport bikes.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>:{' '}
              GSX-S750, 890 Duke, and 400+ other bikes with service-manual gear ratios.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Run both bikes yourself</div>
            <div className="text-white/60 text-sm">
              Free simulator: pick the GSX-S750 or 890 Duke, set your local conditions and compare the two.
            </div>
          </div>
          <Link
            href="/simulator?bike=suzuki-gsx-s750"
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
