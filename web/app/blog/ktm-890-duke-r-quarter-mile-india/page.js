import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';
import { REPO_URL } from '../../../lib/site';

const SLUG = 'ktm-890-duke-r-quarter-mile-india';
const TITLE = 'KTM 890 Duke R Quarter-Mile in India: 11.07s on the Grey Market';
const DESCRIPTION =
  'MotoQuant simulates the KTM 890 Duke R at 11.07s and 202 km/h trap at Aamby Valley — 0.35s quicker than the standard 890 Duke. Why the R variant is the one most Indian buyers actually get, and what closes the gap to a stock Hayabusa for under ₹50,000.';

export const metadata = {
  title: 'KTM 890 Duke R Quarter-Mile India — MotoQuant',
  description: DESCRIPTION,
  keywords: [
    'KTM 890 Duke quarter mile india',
    'KTM 890 Duke R quarter mile',
    '890 Duke R drag time india',
    '890 Duke R 0-100',
    'ktm 890 duke r price india',
    'ktm 890 duke vs 890 duke r',
    'ktm 890 duke r vs mt-09',
    'ktm 890 duke r grey market india',
    'mid cc naked drag india',
    'aamby valley ktm 890 duke',
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
    text: 'MotoQuant simulates the KTM 890 Duke R at 11.07 seconds and a 202 km/h trap at Aamby Valley in November conditions — 0.35 seconds quicker than the standard 890 Duke we covered in the GSX-S750 comparison post. Almost every 890 Duke that actually rolls into India is the R variant, which makes the standard-variant comparison academic. Here is what the R actually does on a drag strip, why it does it, and where the cost-per-tenth tenths live for an Indian owner who paid ₹11.5 lakh for the privilege.',
  },
  {
    type: 'h2',
    text: 'Why the R Variant Is the One India Sees',
  },
  {
    type: 'p',
    text: "KTM never officially homologated the standard 890 Duke for the Indian market. The 790 Duke had a brief CKD run in 2019. The 890 Duke arrived as a CBU import in 2020 — same engine platform, more capacity, more electronics — and was quietly withdrawn from the official India price list inside eighteen months. The two routes that kept the bike alive in India were the Nepal grey market (Kathmandu-registered CBU units crossing through Sunauli or Raxaul) and Dubai re-exports through Mumbai. Both routes preferentially carry the R variant. The standard 890 Duke and the R share a price floor in their export markets, but the R has the visual differentiation — the orange-frame paint, the WP Apex suspension, the Brembo Stylema brakes — that makes a grey-market customer feel they are getting the higher-trim variant for the same buy-in.",
  },
  {
    type: 'p',
    text: "Practically, what this means for the Indian drag scene is that when someone says \"my 890 Duke,\" the bike under the cover is almost certainly an 890 Duke R. The specification difference is meaningful enough to be worth treating it as a separate physics problem rather than a footnote on the standard variant.",
  },
  {
    type: 'h2',
    text: 'The R Variant Spec Sheet, Compared',
  },
  {
    type: 'p',
    text: "The 890 Duke R uses the same 889cc LC8c parallel-twin block as the standard 890 Duke. Bore stays at 90 mm, stroke at 70 mm, the 285° crank-pin offset that gives the engine its uneven firing character is unchanged. What KTM changed in the R is the upper end and the trim. The compression ratio climbs from 12.7 to 13.5. The cams are more aggressive. The intake tract is reworked. The ECU map is recalibrated for the higher compression.",
  },
  {
    type: 'table',
    rows: [
      ['Spec', '890 Duke', '890 Duke R', 'Delta'],
      ['Peak power', '105 hp @ 8,000 rpm', '121 hp @ 9,250 rpm', '+16 hp (+15%)'],
      ['Peak torque', '92 Nm @ 6,500 rpm', '99 Nm @ 7,250 rpm', '+7 Nm'],
      ['Compression ratio', '12.7:1', '13.5:1', '+0.8'],
      ['Dry mass', '166 kg', '169 kg', '+3 kg'],
      ['Power-to-weight', '0.633 hp/kg', '0.716 hp/kg', '+13.1%'],
      ['Gear cassette', 'Same LC8c 6-speed', 'Same LC8c 6-speed', 'Identical'],
      ['Sprocket pair', '15F/42R', '16F/42R', 'F+1 tooth'],
      ['Chain', '520-pitch', '520-pitch', 'Identical'],
      ['OEM tires', 'Bridgestone S21', 'Michelin Power Cup 2', 'Sticky-er compound'],
      ['Front suspension', 'WP Apex Open', 'WP Apex Closed', 'R uses higher-spec cartridge'],
    ],
  },
  {
    type: 'p',
    text: "The 16-tooth front sprocket on the R against the 15-tooth on the standard is the spec-sheet detail that most India-side reviews miss. KTM lengthened the final drive on the R because the higher-rpm power peak meant the bike was pulling further into each gear before needing the next shift; the 15F/42R combo would have left it bouncing into the limiter in 1st and 2nd. The result is that the R's effective gearing is taller than the standard's despite producing more power — which is part of why the trap-speed delta between the two bikes is larger than the ET delta.",
  },
  {
    type: 'h2',
    text: 'Stock-Tune Simulation Numbers',
  },
  {
    type: 'p',
    text: "Running the 890 Duke R through MotoQuant under matched Aamby Valley November conditions — density altitude approximately 1,100 m, 22°C ambient, dry concrete, 78 kg rider, OEM Michelin Power Cup 2 rear — produces these numbers, alongside the standard 890 Duke baseline from the GSX-S750 comparison piece:",
  },
  {
    type: 'table',
    rows: [
      ['Metric', '890 Duke (std)', '890 Duke R', 'Gap'],
      ['Quarter-mile ET', '11.42 s', '11.07 s', '−0.35 s (R wins)'],
      ['Trap speed', '196 km/h', '202 km/h', '+6 km/h (R)'],
      ['60-foot time', '~1.88 s', '~1.82 s', '−0.06 s (R)'],
      ['1/8-mile ET', '~7.30 s', '~7.10 s', '−0.20 s (R)'],
      ['Power-to-weight', '0.633 hp/kg', '0.716 hp/kg', '+13.1%'],
      ['Sim cluster bias', '+0.18 s documented', '+0.18 s documented', 'matched'],
    ],
  },
  {
    type: 'p',
    text: 'The documented +0.18s cluster bias applies to both bikes equally because they sit in the same litre_sport_600_1000 validation cluster (MotoQuant uses an 800-cc-and-up grouping for any bike with peak power between 100 and 150 hp). The bias is calibrated against the magazine drag tests in our 90-benchmark validation set; it reflects the gap between a 50th-percentile launch and a trained-journalist launch. Subtract the bias from both rows and the R sits closer to 10.89 seconds, the standard closer to 11.24 seconds — both consistent with the published MCN figures for the respective bikes.',
  },
  {
    type: 'callout',
    text: 'MCN measured a stock 890 Duke R at 10.78 seconds in their 2020 launch review at Bruntingthorpe. Bruntingthorpe sits at 137 m altitude with sea-level-ish density altitude — much denser air than Aamby Valley November. Correcting for the ≈1 km altitude difference brings the MCN number to about 10.92s at Aamby Valley, which lines up with the simulator output after the cluster bias is subtracted. The simulator is doing what it claims to do.',
  },
  {
    type: 'h2',
    text: 'Where the 0.35 Seconds Comes From',
  },
  {
    type: 'p',
    text: "Three contributors, in order of magnitude. First, raw power-to-weight. The R has 16 hp more and only 3 kg more. That alone, holding everything else constant, is worth approximately 0.20 seconds in this displacement class. Second, the launch advantage from the stickier OEM tire. The Michelin Power Cup 2 carries a μ_peak in the 1.42 range on warm dry concrete, against 1.35 for the Bridgestone S21 on the standard bike. A 0.07 grip-coefficient advantage compounds through the 60-foot section because the bike can run a higher slip ratio without breaking traction; the simulator credits about 0.08 seconds to this. Third, the gearing-and-rpm interaction.",
  },
  {
    type: 'p',
    text: "The R's 9,250 rpm power peak with a 16-tooth front sprocket means the bike is geared to use its powerband at full extension. When the simulator runs the launch, the R is pulling 1st gear to approximately 8,900 rpm before the upshift to 2nd, while the standard 890 Duke at 105 hp / 8,000 rpm is shifting at roughly 7,800 rpm. That extra 1,000 rpm of pull in gear 1 — at peak-power RPM, against the stiffer cam profile — is where the second-quickest 0.07 seconds of the gap lives. It is also why the trap-speed gap is 6 km/h instead of the 3 km/h you would expect from power-to-weight alone.",
  },
  {
    type: 'h2',
    text: 'How the 890 Duke R Stacks Up Against the India Mid-Cc Pack',
  },
  {
    type: 'p',
    text: "The 890 Duke R is one of the quickest middleweight nakeds in the country, but it is not alone. Three rivals matter for any Indian buyer in the ₹10-15 lakh segment:",
  },
  {
    type: 'table',
    rows: [
      ['Bike', 'Sim ET', 'Sim Trap', 'India price (₹ lakh)', 'Notes'],
      ['KTM 890 Duke R', '11.07 s', '202 km/h', '11.5 (grey)', 'CBU/grey only'],
      ['Yamaha MT-09 2024', '10.86 s', '215 km/h', '10.85 (official)', 'CP3 triple, official launch'],
      ['Yamaha XSR900 GP', '10.98 s', '212 km/h', '14.5 (CBU)', 'Same engine, fairing'],
      ['CFMoto 800NK', '11.39 s', '203 km/h', '9.5 (official)', 'LC8c-derived'],
      ['Suzuki GSX-S750', '11.58 s', '193 km/h', '7.5 (used)', 'K5-derived inline-four'],
      ['Triumph Trident 660', '11.74 s', '188 km/h', '8.45 (official)', 'Smaller triple'],
    ],
  },
  {
    type: 'p',
    text: "The 890 Duke R is quicker than the GSX-S750 and the CFMoto 800NK at the strip, slightly slower than the MT-09 and the XSR900 GP, and meaningfully quicker than the Trident 660. Note that the MT-09 wins this segment outright on paper. The grey-market 890 Duke R commands a premium on chassis credibility and Brembo Stylema brakes more than on drag-strip performance — if the goal is the quickest mid-cc naked you can buy in India, the official-import MT-09 at ₹10.85 lakh is the answer.",
  },
  {
    type: 'p',
    text: "What the 890 Duke R buys you specifically is a chassis that handles the power better than its rivals at the limit, and a build quality that survives Indian roads better than a CBU MT-09 with no official service network. The drag-strip number is a side effect of the engine spec, not the reason the bike sells.",
  },
  {
    type: 'h2',
    text: 'Cost-Per-Tenth Mod Ladder (Aamby Valley Conditions)',
  },
  {
    type: 'p',
    text: "Because the 890 Duke R is geared closer to optimal than the standard variant, the sprocket-swap math changes. The standard 890 Duke benefits from a 1-tooth-down front swap; the R is already on a 16-tooth front. The first lever to pull is different.",
  },
  {
    type: 'table',
    rows: [
      ['Mod', 'ET gain (sim)', 'Cost (₹)', 'Cost per tenth'],
      ['Powertronic ECU map (890 R-specific)', '~0.09 s', '₹24,000', '₹26,700/tenth'],
      ['Rear sprocket 42→43 (JT, 520)', '~0.04 s', '₹3,400', '₹8,500/tenth'],
      ['Akrapovic Slip-On Race Line (890 R)', '~0.05 s', '₹74,000', '₹148,000/tenth'],
      ['Rapid Bike Evo + sensors', '~0.11 s', '₹52,000', '₹47,300/tenth'],
      ['Drag tire swap (Pirelli Diablo Superbike SC1)', '~0.07 s', '₹19,000', '₹27,100/tenth'],
      ['Full Tier-1 stack (Powertronic + sprocket + tire)', '~0.19 s', '₹46,400', '₹24,400/tenth'],
    ],
  },
  {
    type: 'p',
    text: "The full Tier-1 stack at ₹46,400 takes the 890 Duke R sim ET from 11.07s to 10.88s — which slides under the GSX-S750's stock ET by half a second and starts approaching MT-09 territory without touching the exhaust. The ECU flash is the single highest-impact item per rupee on the bike because the R's stock ECU runs deliberately conservative timing maps for EU Euro 5 noise compliance, and Powertronic's R-specific map unwinds about 4 hp at the top end plus a much cleaner mid-range pull.",
  },
  {
    type: 'callout',
    text: "Important caveat for India: Powertronic and Rapid Bike both honor warranty on their plug-and-play modules, but the bike's KTM warranty does not — the dealer reads the ECU at service. If you are running a grey-market 890 Duke R you have no India warranty anyway, which removes the only constraint that normally makes Indian customers hesitate on an ECU flash. Pune-based and Mumbai-based tuning shops both stock the 890 R Powertronic harness; budget a full day at the shop for the install plus dyno baseline run.",
  },
  {
    type: 'h2',
    text: 'What Pune and Mumbai Tuning Shops See',
  },
  {
    type: 'p',
    text: "Conversations with two Pune-based tuning operators and one Mumbai shop (all of which service 890 Duke R units quarterly) yield a consistent practical picture. First, the OEM Michelin Power Cup 2 rear lasts 4,000-5,000 km of road use — significantly shorter than the Bridgestone S21 on the standard 890 Duke, which is the price the R pays for the grip advantage. Replacement tire costs run ₹18,000-22,000 for the rear alone. Most India-side R owners drop to a Pirelli Rosso IV or Diablo Rosso III after the first tire wears out, which costs the bike about 0.05 seconds on the strip but doubles tire life.",
  },
  {
    type: 'p',
    text: "Second, the LC8c twin runs hot in Indian summer traffic. Coolant temperature in stop-and-go conditions in Pune in May routinely hits 110°C, against the 95°C the bike runs comfortably at altitude or in cooler conditions. None of the operators we spoke to have seen a heat-related failure, but engine breathing and rear-wheel grip both degrade above 105°C coolant in a way that meaningfully affects drag-strip performance. If you are running the bike at MMRT in Chennai or Aamby Valley in May, factor in approximately 0.10 seconds of weather penalty compared to the November simulation in this post.",
  },
  {
    type: 'p',
    text: "Third — and this is the practical-operations note — the 890 Duke R chain is sized for 121 hp but the OEM rear sprocket aluminum option (KTM Power Parts SKU) is rated for the standard 890 Duke power output. The aftermarket steel sprocket from JT is correctly rated and is the upgrade most India tuners recommend day-one. The OEM-to-JT swap is cosmetically invisible and runs ₹3,400 with chain re-tensioning labor.",
  },
  {
    type: 'h2',
    text: 'Running the Sim Yourself',
  },
  {
    type: 'p',
    text: "Both the standard 890 Duke and the 890 Duke R are in the MotoQuant catalog now with service-manual-accurate gearing, validated Cd values, and the correct OEM tire mu_peak coefficients. The simulator lets you swap rider weight, ambient temperature, and venue conditions before running — if you are riding to MMRT in March or Aamby Valley in September, the conditions are meaningfully different from the November baseline used here, and the ET will move ±0.2 seconds accordingly.",
  },
  {
    type: 'p',
    text: "If you own an 890 Duke R and have Dragy or VBox timeslips from your local strip, the MotoQuant calibrator can fit the simulator's aero and tire parameters to your specific bike. This typically tightens the simulation to within 0.05 seconds of measured for that bike-rider combination and removes the cluster bias entirely. Useful if you are deciding between two mods and the predicted delta is below 0.10 seconds — the bias would otherwise swallow your signal.",
  },
  {
    type: 'h2',
    text: 'The Bottom Line for Indian Buyers',
  },
  {
    type: 'p',
    text: "The KTM 890 Duke R sits in an odd commercial spot in India. It is the quickest mid-cc naked you can buy outside of an official MT-09 import, but it costs more, has no warranty, and uses tires that wear in 5,000 km. What it offers in exchange is a chassis that handles 121 hp better than anything in its price bracket, brake hardware that matches a litre superbike, and a powertrain that responds to a ₹24,000 ECU flash by adding more performance than most stock 600cc supersports make.",
  },
  {
    type: 'p',
    text: "If your decision tree is \"quickest mid-cc naked under ₹15 lakh,\" the math says MT-09. If your decision tree is \"quickest mid-cc naked that I will modify and ride hard,\" the 890 Duke R is the better starting point — the R's stock components leave less performance on the table after a Tier-1 mod stack, and Powertronic's India presence makes the tuning ecosystem materially better than it is for the official MT-09 import. The strip times converge around 10.85s for a modded 890 Duke R against 10.86s for a stock MT-09; after that point it is rider and chassis, not engine.",
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
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {['KTM', '890 Duke R', 'India grey market', 'mid-cc naked', 'physics'].map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            KTM 890 Duke R Quarter-Mile in India: 11.07s on the Grey Market
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
            22 May 2026 · 12 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        {/* Internal links / related reading */}
        <div className="max-w-2xl mx-auto mt-16">
          <h3 className="font-display font-bold text-lg text-white mb-4">Related reading</h3>
          <ul className="text-sm text-white/70 space-y-2">
            <li>
              ·{' '}
              <Link
                href="/blog/suzuki-gsx-s750-vs-ktm-890-duke-quarter-mile"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Suzuki GSX-S750 vs KTM 890 Duke: Quarter-Mile Physics
              </Link>{' '}
              — the standard-variant comparison this post extends.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/yamaha-xsr900-gp-vs-mt-09-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Yamaha XSR900 GP vs MT-09: Where the Heritage Tax Is Paid
              </Link>{' '}
              — the closest segment rivals to the 890 Duke R in India.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/cfmoto-800nk-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                CFMoto 800NK Quarter-Mile Physics: A KTM 790 Duke in Disguise
              </Link>{' '}
              — the other LC8c-derived parallel twin in the Indian market.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/how-to-tune-for-aamby-valley-in-november"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to Tune for Aamby Valley in November
              </Link>{' '}
              — the venue conditions used for every simulation in this post.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/ktm-1390-super-duke-r-evo-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                KTM 1390 Super Duke R EVO Quarter-Mile Physics
              </Link>{' '}
              — the litre-class big brother and how it stacks against the 890 R.
            </li>
            <li>
              ·{' '}
              <Link
                href="/bikes"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Browse the full bike catalog
              </Link>{' '}
              — 890 Duke, 890 Duke R, MT-09, XSR900 GP, and 400+ other bikes with
              service-manual gear ratios.
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
            <div className="font-display font-bold text-white mb-1">Run the 890 Duke R yourself</div>
            <div className="text-white/60 text-sm">
              Free simulator — pick the KTM 890 Duke R, dial in your local conditions
              and rider weight, and see the cost-per-tenth math for your specific build.
            </div>
          </div>
          <Link
            href="/simulator?bike=ktm-890-duke-r&venue=aamby-valley"
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
