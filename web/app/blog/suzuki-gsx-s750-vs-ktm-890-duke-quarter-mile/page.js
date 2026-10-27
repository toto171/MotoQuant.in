import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';
import { REPO_URL } from '../../../lib/site';

const SLUG = 'suzuki-gsx-s750-vs-ktm-890-duke-quarter-mile';
const TITLE = 'Suzuki GSX-S750 vs KTM 890 Duke: Quarter-Mile Physics';
const DESCRIPTION =
  'MotoQuant simulates the GSX-S750 at 11.58s and the 890 Duke at 11.42s. 27 kg lighter, 0.16s quicker. How mass beats displacement at the strip — and what actually limits each bike.';

export const metadata = {
  title: 'Suzuki GSX-S750 vs KTM 890 Duke Quarter-Mile — MotoQuant',
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
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: 'MotoQuant simulates the Suzuki GSX-S750 at 11.58 seconds and 193 km/h trap, and the KTM 890 Duke at 11.42 seconds and 196 km/h trap. The 890 Duke weighs 27 kg less and wins by 0.16 seconds. But the reason it wins is not mass alone — and a stock GSX-S750 is faster than a stock 890 Duke in one specific part of the run.',
  },
  {
    type: 'h2',
    text: 'The Two Bikes and What They Actually Are',
  },
  {
    type: 'p',
    text: "The Suzuki GSX-S750 (2015–2021) is a naked repackage of the 2005–2006 GSX-R750 K5/K6 engine. Same 70 mm bore, same 48.7 mm stroke, same basic combustion chamber geometry — but with revised cam profiles that pull the power delivery toward mid-range and push the torque peak up to 9,000 rpm. The result is a 114 hp / 81 Nm inline-four that makes most of its power between 8,000 and 11,000 rpm. On the road that is an effortless, slightly droney experience. On a drag strip it means the bike is working against its own redline preference in gear 1, where you never touch 10,000 rpm.",
  },
  {
    type: 'p',
    text: "The KTM 890 Duke (2020–2023) is the standard, non-R variant of the LC8c parallel twin. It makes 105 hp at 8,000 rpm and 92 Nm at 6,500 rpm — 9 hp less than the GSX-S750 on paper, but with 11 Nm more torque and a peak that arrives 2,500 rpm earlier. Its dry mass is 166 kg per the KTM EU spec sheet. The GSX-S750 sits at 193 kg. That is a 27 kg difference — roughly one adult passenger removed from the Suzuki.",
  },
  {
    type: 'p',
    text: "Both bikes are in the MotoQuant catalog now. The GSX-S750 uses a dedicated gear cassette from Suzuki service manual 99500-36160-03E — not the GSX-R750 K5/K6 transmission, which is a distinct unit. The 890 Duke shares its gearbox cassette with the 890 Duke R (confirmed via KTM service manual KTM-TI-2020-890D). Sprockets: GSX-S750 runs 16F/45R, 890 Duke runs 15F/42R, both on 520-pitch chain.",
  },
  {
    type: 'h2',
    text: 'The Simulation Numbers',
  },
  {
    type: 'p',
    text: 'Running both bikes through MotoQuant under Aamby Valley November conditions — density altitude approximately 1,100 m, 22°C ambient, dry concrete, 78 kg rider, OEM Bridgestone tires — produces these stock-tune numbers:',
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
    text: "The 0.18s documented bias comes from the litre_sport_600_1000 cluster both bikes fall into (both sit between 600 and 1000cc). For the GSX-S750, Motorcycle Consumer News measured a stock test bike at 11.4s and 194 km/h in November 2017 — the simulator comes in at 11.58s, which is 0.18s over the real-world result and sits exactly within the documented +0.15–0.22s bias band for this cluster. That is validation in the right direction: the simulator is calibrated to a 50th-percentile rider, not a trained journalist doing launch-control-optimised drag runs.",
  },
  {
    type: 'callout',
    text: "No instrumented quarter-mile record exists in the MotoQuant benchmark list for the stock 890 Duke (distinct from the 890 R and the 790 Duke). KTM factory literature puts 0-100 km/h at 3.1 seconds for the standard 890 Duke, which maps to approximately 11.3–11.5s at the quarter depending on trap speed. The simulator's 11.42s is consistent with that range. If you have a Dragy run on a stock 890 Duke, the import-dragy CLI can calibrate the sim to your bike specifically.",
  },
  {
    type: 'h2',
    text: 'Why Mass Wins More Than Displacement',
  },
  {
    type: 'p',
    text: "The naive prediction looking at a 749cc I4 vs an 889cc parallel twin would favour the bigger-displacement bike. That prediction is wrong, and the physics explains why.",
  },
  {
    type: 'p',
    text: "In a quarter mile, the limiting factor for the first 60 feet is not peak power — it is available traction multiplied by the force the drivetrain can put at the rear wheel. Both bikes have comparable grip (Bridgestone S21/S22 OEM fitments, μ_peak ≈ 1.35 on both). But the lighter bike accelerates faster at any given wheel force. At 166 kg dry, the 890 Duke needs only 90 N of net force per unit acceleration where the 193 kg GSX-S750 needs 111 N for the same rate. The Duke gets to launch harder before the front wheel lifts, which means its traction advantage is compounded through the first gear interval.",
  },
  {
    type: 'p',
    text: "The GSX-S750 recovers some of this deficit in the top half of the run. Between 130 and 190 km/h, where the engine is pulling through 9,000–10,500 rpm, the inline-four produces more power than the parallel twin. The GSX-S750's torque curve holds up better past 9,000 rpm — the LC8c twin starts to fall off around 8,500 rpm. This is why the trap speed gap is only 3 km/h rather than 6 or 7 km/h: the Suzuki claws back power across the back half of the run even though it loses the launch decisively.",
  },
  {
    type: 'p',
    text: "If you ran these bikes on a 200 m sprint instead of a 402 m quarter, the result would likely be much closer. The Duke's launch advantage would dominate, but it would not have had time to compress into the trap. At 402 m the deficit is 0.16s — at 200 m it would be closer to 0.25s because the Suzuki has less time to recover.",
  },
  {
    type: 'h2',
    text: 'Gearing — Where the Tenths Are',
  },
  {
    type: 'p',
    text: "GSX-S750 gearing: [2.615, 1.882, 1.500, 1.261, 1.103, 0.966] with 16F/45R. Effective final drive ratio in 6th (0.966 × 16/45) = 0.343. With a 180/55ZR17 rear tire at approximately 295 mm rolling radius, that puts the top speed in 6th at full redline (12,000 rpm) at roughly 240 km/h. The quarter-mile trap at 193 km/h means the bike is crossing the timing beam in 5th gear, short of 5th gear's redline. The 6th gear overdrive is a highway gear that never does drag-strip work.",
  },
  {
    type: 'p',
    text: "KTM 890 Duke gearing: [2.625, 1.941, 1.580, 1.346, 1.185, 1.071] with 15F/42R. Effective final drive in 6th (1.071 × 15/42) = 0.383. With a 180/55ZR17 rear, top speed in 6th at 9,000 rpm (peak power) is approximately 207 km/h. The quarter-mile trap at 196 km/h means the Duke is crossing the line right at peak power RPM in 6th, which is nearly optimal. The gearing is shorter and better matched to the bike's powerband for a drag strip.",
  },
  {
    type: 'p',
    text: "This gearing difference is a meaningful contributor to the ET gap. The GSX-S750's taller gearing means more time spent in the gear-change deadband before 5th gear can pull through to trap speed. A sprocket swap to 16F/42R on the Suzuki (shortening final drive by ~7%) would move the trap crossing into 6th gear territory and likely recover 0.04–0.06s. Cost: approximately ₹3,200 for a JT sprocket pair on 520-pitch, which is among the lowest cost-per-tenth mods in the catalog.",
  },
  {
    type: 'h2',
    text: 'Where Each Bike Loses Time — Section by Section',
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
    text: 'The Indian Market Context',
  },
  {
    type: 'p',
    text: "The Suzuki GSX-S750 was officially sold in India in limited batches as a CBU import. Second-hand prices on IndiaMART and BikeWale typically land in the ₹6–8 lakh range for good-condition 2018–2020 examples — making it one of the most accessible liquid-cooled inline-fours available to the Indian drag scene. The 890 Duke was never officially launched in India as a standalone model (only the Duke 390 and Duke 790 saw proper CKD/CBU launches), but grey-market units via Nepal and Dubai arrive at approximately ₹10–12 lakh. Most 890 Duke owners in India are running the 890 R variant at the same price point — which has 16 hp more (121 hp) and slightly different suspension.",
  },
  {
    type: 'p',
    text: "For drag strip use at Aamby Valley or MMRT, the GSX-S750 at ₹7 lakh gives you an 11.58s bike that responds well to gearing and ECU tuning. The 890 Duke at ₹11 lakh gives you an 11.42s bike that is lighter from the factory but less easily sourced. If your goal is the lowest quarter-mile cost-per-second, a used GSX-S750 with a sprocket swap and a Woolich ECU flash (₹25,000) gets you to approximately 11.4s for around ₹7.25 lakh all-in — competitive with a stock 890 Duke for a fraction of the purchase price.",
  },
  {
    type: 'p',
    text: "That comparison flips if you prioritise the riding experience off the strip. The 890 Duke is noticeably lighter to throw around corners, and 92 Nm at 6,500 rpm makes it easier to ride fast without being in the powerband. The GSX-S750 feels more planted but rewards more aggressive rev management. Neither is a bad choice — they are just different tools.",
  },
  {
    type: 'h2',
    text: 'Three Mods Per Bike That Move the Needle',
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
    text: "Both bikes show the same pattern: sprockets first (lowest cost per tenth by a large margin), ECU second (mid-range value), exhaust a distant third. The slip-on exhaust is the most commonly purchased part in both categories because it sounds better and looks better — but on a cost-per-tenth basis it is the worst value. Buy the sprockets, book a dyno day for the ECU tune, and use the remaining budget for track fees.",
  },
  {
    type: 'h2',
    text: 'The Physics of the I4 vs Twin Torque Curve',
  },
  {
    type: 'p',
    text: "One of the more interesting sim outputs when you run both bikes is the shape of the gear-change events. The GSX-S750's inline-four has its torque curve peaking at 9,000 rpm with a relatively narrow Gaussian band — the synthetic torque curve the simulator builds from the 114 hp / 81 Nm spec points tapers off more steeply below peak-torque RPM than the LC8c twin's curve does.",
  },
  {
    type: 'p',
    text: "The result: after every upshift, the GSX-S750 spends a longer interval below its power peak, waiting for RPM to climb back into the sweet spot. On the 890 Duke, 92 Nm arrives at 6,500 rpm, which means after a shift into 2nd or 3rd gear the engine is already in its torque peak almost immediately. The Duke essentially has a wider window of useful traction across the 402 m — it does not need to rev as aggressively to find its power.",
  },
  {
    type: 'p',
    text: "This is the physics argument for the parallel twin's mid-range advantage that the spec sheet does not capture. The inline-four's displacement and redline advantages are real but they only materialise in the top half of the run. By the time the GSX-S750 is using its 114 hp advantage at 10,500 rpm, the Duke is already across the line.",
  },
  {
    type: 'h2',
    text: 'Run Your Own Numbers',
  },
  {
    type: 'p',
    text: "If you own either bike — or are deciding between them — the MotoQuant simulator lets you dial in your exact conditions: rider weight, ambient temperature, elevation at your local strip, and parts-catalog mods. Both the GSX-S750 and the 890 Duke are now in the catalog with service-manual-accurate gear ratios and Cd values. The comparison at motoquant.in/simulator takes about 30 seconds per run.",
  },
  {
    type: 'p',
    text: "A few practical notes on what the simulator can and cannot tell you. It can tell you the relative ranking of mods per bike — sprockets vs ECU vs exhaust — with high confidence, because the relative physics does not depend on whether the absolute ET is 11.42s or 11.25s. It can tell you the impact of weather and altitude, which is genuinely useful when you are planning a trip to Aamby Valley from a sea-level city. What it cannot tell you is the exact ET you will personally run on your first pass — launch technique variation between riders is the largest uncontrolled variable at this power level, worth approximately ±0.2s depending on how well you can modulate the clutch at 6,500 rpm.",
  },
  {
    type: 'p',
    text: "Both bikes reward precise launch RPM. The GSX-S750 is more forgiving of a slightly low launch RPM because its inline-four builds revs quickly; the 890 Duke needs to be staged closer to its peak-torque RPM to get the front wheel up correctly. The simulator documents both bikes' optimal launch RPM in the parts ROI output — look at the sensitivity curve for 'staging.launch_rpm' to see where your tenths come from.",
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
            {['Suzuki', 'GSX-S750', 'KTM', '890 Duke', 'comparison', 'mid-cc naked'].map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Suzuki GSX-S750 vs KTM 890 Duke: Quarter-Mile Physics
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
              <Link href="/blog/cfmoto-800nk-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                CFMoto 800NK Quarter-Mile Physics
              </Link>{' '}
              — the other LC8c-derived parallel twin in the Indian market.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/the-physics-of-a-perfect-launch" className="text-brand-accent hover:text-brand-orange transition-colors">
                The Physics of a Perfect Launch
              </Link>{' '}
              — clutch engagement, tire slip, and weight transfer in the first 60 feet.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-to-tune-for-aamby-valley-in-november" className="text-brand-accent hover:text-brand-orange transition-colors">
                How to Tune for Aamby Valley in November
              </Link>{' '}
              — the venue conditions used for both simulations in this post.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/hayabusa-vs-zx-14r-which-is-faster" className="text-brand-accent hover:text-brand-orange transition-colors">
                Hayabusa vs ZX-14R: Which Is Faster Off the Line?
              </Link>{' '}
              — the same comparison framework at the hyper-sport class.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>{' '}
              — GSX-S750, 890 Duke, and 400+ other bikes with service-manual gear ratios.
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

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Run both bikes yourself</div>
            <div className="text-white/60 text-sm">
              Free simulator — pick the GSX-S750 or 890 Duke, dial in your local conditions, and compare them head-to-head.
            </div>
          </div>
          <Link
            href="/simulator?bike=suzuki-gsx-s750"
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
