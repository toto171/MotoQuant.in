import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'kawasaki-ninja-zx-4r-quarter-mile-physics';
const TITLE = 'Kawasaki Ninja ZX-4R Quarter-Mile Physics: 400cc Inline-Four';
const DESCRIPTION =
  'MotoQuant simulates the 2024 Kawasaki Ninja ZX-4R at 12.681s and 192.6 km/h trap. Why a 400cc inline-four runs a 12.6, and what closes the 0.1s gap to the ZX-4RR.';

export const metadata = {
  title: 'Kawasaki Ninja ZX-4R Quarter-Mile Physics | MotoQuant',
  description: DESCRIPTION,
  keywords: [
    'kawasaki ninja zx-4r quarter mile',
    'zx-4r drag race',
    'zx-4r vs zx-4rr',
    'zx-4r india price',
    'kawasaki zx-4r 0-100',
    'kawasaki zx-4r vs ninja 400',
    '400cc inline four drag',
    'kawasaki zx-4r top speed',
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
    text: 'MotoQuant simulates the 2024 Kawasaki Ninja ZX-4R at 12.681 seconds and a 192.6 km/h trap under matched Aamby Valley November conditions. Cycle World clocked a stock ZX-4RR in the 12.4–12.8s band at roughly 190 km/h trap. The 400cc inline-four revs to 15,500 rpm, makes 76 hp at the crank, and runs an ET that no Indian 300–400cc twin or single can touch. So why does a 76 hp small-bore four-cylinder land closer to a 600cc supersport than to a Duke 390?',
  },
  {
    type: 'h2',
    text: 'What the ZX-4R is',
  },
  {
    type: 'p',
    text: "Kawasaki built two versions of the 2024 Ninja ZX-4 platform: the ZX-4RR (already in the MotoQuant catalog) and the ZX-4R base trim, added to the catalog the day this post went up. Both share the 399 cc DOHC inline-four with four 32 mm throttle bodies, the 6-speed cassette, the 17F/45R 520 chain and the trellis frame. The base bike is a cost-down version. It drops the KQS quickshifter and the slipper clutch's assist function, swaps the ZX-4RR's tubular braced swingarm for a plain cast-aluminium unit, and adds 2 kg of dry mass for a listed 191 kg.",
  },
  {
    type: 'p',
    text: 'You keep the engine. Same 80 hp claimed at the crank, same 39 Nm peak torque at 13,000 rpm, same 15,500 rpm redline. The bike is one of only two production motorcycles in the world right now built around a 400cc inline-four screamer (the other is its own ZX-25R sibling at 250cc), and it behaves like nothing else at this displacement. A KTM RC 390 single makes its peak torque at 7,000 rpm and signs off by 10,000. The ZX-4R wants to be ridden like a 600cc supersport: rev it past 11,000, hold the throttle pinned, and shift at 15,000.',
  },
  {
    type: 'h2',
    text: 'Stock-tune simulation numbers',
  },
  {
    type: 'p',
    text: 'Results for the ZX-4R in MotoQuant under Aamby Valley November conditions (density altitude ≈ 1100 m, 22°C ambient, dry asphalt, μ_peak 1.32 on the OEM Dunlop Sportmax GPR-300 rear), with a 78 kg rider on a 191 kg dry bike:',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'Value', 'Source'],
      ['Quarter-mile ET', '12.681 s', 'MotoQuant sim'],
      ['Trap speed', '192.6 km/h', 'MotoQuant sim'],
      ['60-foot time', '~2.15 s', 'MotoQuant sim'],
      ['Real-world ET (ZX-4RR)', '12.4–12.8 s', 'Cycle World 2024'],
      ['Real-world trap (ZX-4RR)', '~190 km/h', 'Cycle World 2024'],
      ['Sim − real ΔET', '~0.0 s', 'within band'],
    ],
  },
  {
    type: 'p',
    text: 'The simulation lands in the middle of the published instrumented band. That is typical for the litre-sport-600-1000 cluster, where the April 27 sweep documented a 0.22s mean absolute error across 29 matched benchmarks. The bike sits in that cluster despite its 400cc displacement because its engine, a high-revving inline-four with peak power at 14,500 rpm, behaves like a scaled-down 600cc supersport rather than a scaled-up 400cc twin. The tyre grip model, the gear-cassette torque multiplication and the synthesized 0.88 redline-factor torque tail all carry over directly from the ZX-6R class.',
  },
  {
    type: 'callout',
    text: 'Look at the trap speed: 192.6 km/h. A stock Pulsar NS400Z traps at 158 km/h, an RC 390 at 166 km/h, and a Ninja 400 twin at about 175 km/h. By the 1,000-foot line the ZX-4R has left every other 400-class bike behind, with the same displacement.',
  },
  {
    type: 'h2',
    text: 'Why the inline-four screamer wins at 400cc',
  },
  {
    type: 'p',
    text: 'Three physics advantages explain the 0.7-second gap between a ZX-4R and a Ninja 400 twin. In order of size:',
  },
  {
    type: 'p',
    text: '1. Usable power band. The ZX-4R makes peak power at 14,500 rpm and pulls cleanly from about 9,500 rpm, so the engine does real work across a 5,000 rpm window. A KTM RC 390 single makes peak power at 9,000 rpm and pulls cleanly from about 6,500 rpm: a 2,500 rpm window. With six speeds, a ZX-4R rider keeps the engine in the top 30 percent of its rev range for nearly the whole quarter-mile. The RC 390 has to ride out the long tail of its post-peak torque drop in every gear.',
  },
  {
    type: 'p',
    text: "2. Gear-ratio resolution. The ZX-4R's cassette ratios are 2.928 / 2.055 / 1.611 / 1.333 / 1.157 / 1.038, with a 2.219 primary and 17F/45R sprockets. Six closely spaced ratios under a very high redline give small rpm drops on each shift in the simulator: about 1,200 rpm at the 14,500 rpm shift points. The bike never falls out of its power band. The Ninja 400 twin drops 2,800 rpm on each shift, because its cassette is matched to a 12,000 rpm redline with fewer usable revs above peak power.",
  },
  {
    type: 'p',
    text: '3. Mass distribution and chassis. At 191 kg dry, the ZX-4R is heavier than a Ninja 400 twin at 168 kg, but the extra mass sits low and central around the inline-four crank. That lowers the polar moment about the launch axis, so the simulator records less front-end lightening per unit of acceleration than on a top-heavy twin of similar power. In practice, the ZX-4R can carry slightly more throttle in gear 1 before it hits the wheelie limit, even though it is heavier.',
  },
  {
    type: 'h2',
    text: 'ZX-4R vs ZX-4RR: what two kilograms cost',
  },
  {
    type: 'p',
    text: 'The 2 kg dry-mass gap between the ZX-4R (191 kg) and the ZX-4RR (189 kg) is small but measurable. Both bikes, run in MotoQuant under identical conditions:',
  },
  {
    type: 'table',
    rows: [
      ['Bike', 'Sim ET', 'Sim trap', 'Dry mass', 'Quickshifter', 'India price'],
      ['Kawasaki ZX-4R', '12.681 s', '192.6 km/h', '191 kg', 'No', '~₹8.5 lakh'],
      ['Kawasaki ZX-4RR', '12.58 s', '193.4 km/h', '189 kg', 'Yes (KQS)', '~₹9.5 lakh'],
      ['Δ', '+0.10 s', '−0.8 km/h', '+2 kg', '–', '−₹1.0 lakh'],
    ],
  },
  {
    type: 'p',
    text: "The ZX-4RR is about 0.10 seconds quicker in ET and 0.8 km/h faster at the trap. Most of that comes from the quickshifter. KQS cuts about 60 milliseconds off each upshift, and the run has five upshifts, so the quickshifter alone accounts for roughly 0.05–0.07s. The other 0.03–0.05s comes from the lower mass and the slightly stiffer braced swingarm, which gives marginally better launch traction. For an Indian buyer choosing between the two, the ZX-4R is the better cost-per-tenth buy: a Healtech or Translogic quickshifter retrofit costs about ₹18,000–25,000, recovers most of the ZX-4RR's ET advantage, and leaves you ₹75,000 ahead.",
  },
  {
    type: 'p',
    text: "Suspension is the exception. The ZX-4RR ships with a fully adjustable 37 mm Showa BPF front fork; the ZX-4R gets a non-adjustable Showa SFF-BP unit. For street riding and casual track days the base fork is fine. For repeated quarter-mile launches, where rebound damping affects how the front wheel goes from compressed to extended, the ZX-4RR fork is better. Upgrading the base fork means going aftermarket (an Öhlins NIX30 cartridge kit runs about ₹85,000 fitted), so the base trim's cost-per-tenth advantage shrinks if you plan to race the bike seriously.",
  },
  {
    type: 'h2',
    text: 'What limits the ZX-4R in the quarter',
  },
  {
    type: 'p',
    text: "Three things, ranked by impact on the simulated ET:",
  },
  {
    type: 'p',
    text: '1. Launch RPM and clutch slip. The ZX-4R needs an 11,000–12,000 rpm launch to keep the inline-four in its power band off the line. Below 9,000 rpm the engine cannot make enough torque to keep the rear wheel accelerating through the first 30 metres, so a lazy clutch dump at 7,000 rpm bogs the bike and adds 0.3–0.5s to the 60-foot time. The simulator pins its launch-RPM floor to peak-torque rpm (13,000 for this engine), which is aggressive but not magazine-level optimal. MCN test riders dump the clutch at exactly the point where the front tire starts to skim, typically 12,500 rpm on this bike.',
  },
  {
    type: 'p',
    text: '2. Aerodynamics above 170 km/h. Its Cd of about 0.62 and frontal area of 0.41 m² give a Cd × A of roughly 0.254 m². That is excellent for a small-displacement sport bike (about 8 percent lower than a Ninja 400, thanks to the deeper full fairing), but it is what limits the back half of the run. Above 170 km/h, the simulator shows aerodynamic drag taking about 55 percent of the rear-wheel power. The only fix is a tail fairing extension, which is not legal on public roads in India.',
  },
  {
    type: 'p',
    text: '3. Gear-3-to-gear-4 shift point. On the stock 17F/45R sprockets, the ZX-4R crosses the trap line in fifth gear at about 14,800 rpm, just under the 15,000 rpm shift point and well into peak power. But the simulator log shows a brief drop into the gear-4 power band at the 1,000-foot mark, where a slightly earlier shift would have kept the engine 500 rpm higher. The fix is in the rider, not the bike: practice the shift sequence, and do not chase the rev limiter on the 3-to-4 change. Nailing this shift is worth roughly 0.03–0.05s of ET.',
  },
  {
    type: 'h2',
    text: 'How the ZX-4R compares with other 400-class bikes in India',
  },
  {
    type: 'p',
    text: 'Four 400cc-class bikes sold in India, all simulated at Aamby Valley in MotoQuant. These are stock-tune sims under matched November conditions:',
  },
  {
    type: 'table',
    rows: [
      ['Bike', 'Sim ET', 'Sim trap', 'Peak hp', 'Configuration', 'India price'],
      ['Kawasaki Ninja ZX-4R', '12.68 s', '193 km/h', '76 (crank)', 'I4 400cc', '~₹8.5 lakh'],
      ['Kawasaki Ninja 400', '13.45 s', '175 km/h', '49', 'I2 399cc', '~₹5.2 lakh'],
      ['Bajaj Pulsar NS400Z', '13.80 s', '158 km/h', '40', 'I1 373cc', '~₹1.85 lakh'],
      ['KTM RC 390', '13.50 s', '166 km/h', '44', 'I1 373cc', '~₹3.18 lakh'],
    ],
  },
  {
    type: 'p',
    text: "The ZX-4R is the only inline-four here, and it is the quickest by 0.7–1.1 seconds. The Ninja 400 twin and the RC 390 single are within 0.05s of each other despite being 26 hp apart on the spec sheet, because the single's longer-stroke torque advantage at low RPM makes up for the twin's higher peak. The ZX-4R works in a different physics regime. A 600cc supersport like the Ninja ZX-6R 636 simulates at about 11.3s and a 215 km/h trap, so the ZX-4R closes more than half the gap between a 400cc twin and a 600cc four while making 38 hp less than the ZX-6R.",
  },
  {
    type: 'p',
    text: 'If you are weighing the ZX-4R against a used Ninja ZX-6R 636 or a CBR650R, the spec-sheet horsepower numbers mislead. It does not match a 600cc supersport in absolute ET, but it gets within 1.4 seconds and ~22 km/h of trap. What you lose in top-end power you gain in gear-1 wheelie limit, low-speed manners, road tax and insurance premium. For the 80 percent of owners who never touch a quarter-mile strip outside the occasional track day, the ZX-4R is the more practical 400-class flagship.',
  },
  {
    type: 'h2',
    text: 'Indian-market mods that cut ET',
  },
  {
    type: 'p',
    text: 'MotoQuant scores cost-per-tenth on every part in its catalog. For the ZX-4R at Aamby Valley, these are the top three mods by ET impact, priced at Indian retail:',
  },
  {
    type: 'p',
    text: '1. Quickshifter (Healtech iQSE-2 or Translogic AT QS): about ₹22,000 fitted, worth roughly 0.06s ET. Fit this first, because it replaces the factory part the ZX-4R is missing. The ECU is already wired for it (Kakimoto-style ignition cut); you only need the strain-gauge shift rod and harness.',
  },
  {
    type: 'p',
    text: '2. ECU flash + Akrapovic Racing slip-on: about ₹85,000 combined (₹18,000 for the flash from Powertronic or KTune Bengaluru, ₹67,000 for the slip-on). Worth roughly 0.10–0.12s ET. The flash raises the 14,500 rpm rev-limiter to about 15,200 rpm and remaps the fuel curve for the freer-flowing exhaust. The slip-on saves about 2.5 kg and cuts post-cat backpressure. Together they push trap speed to about 197 km/h.',
  },
  {
    type: 'p',
    text: '3. Sprocket swap to 16F/45R: about ₹4,800 in parts, worth roughly 0.04s ET. It drops the final-drive ratio enough to keep the engine 800 rpm higher in every gear, which matters more than usual on a peaky inline-four. The cost is highway cruising rpm, up by about 600 rpm at 100 km/h. That is mostly a comfort issue, not a reliability one; the engine is happy at 8,000 rpm all day.',
  },
  {
    type: 'callout',
    text: 'Skip suspension upgrades and steel-braided brake lines: they do not move ET on a drag run. Spend that money on a quickshifter and a good set of tires (Pirelli Diablo Rosso IV or Bridgestone Battlax S22 in 110/70-17 front and 150/60-17 rear). On this bike, tires are the biggest single variable in 60-foot consistency.',
  },
  {
    type: 'h2',
    text: 'At Indian drag strips',
  },
  {
    type: 'p',
    text: "Kawasaki India dealerships in select metros sell the ZX-4R at roughly ₹8.5 lakh on-road for the standard bike and ₹9.5 lakh for the ZX-4RR. Aamby Valley and the BIC drag strip see about half a dozen ZX-4 series bikes at a typical monthly meet, most of them ZX-4RRs. On stock tune at Aamby Valley in October-November conditions, an experienced rider with a proper launch runs a ZX-4R at 12.6–12.8s. The simulator's 12.681s sits inside that range.",
  },
  {
    type: 'p',
    text: 'It is not a wheelie machine. The front wheel does not lift easily without aggressive clutch work or a slope, because peak torque comes so high in the rev range that the bike is already moving when it arrives. That matters on the strip, because launches are much more consistent on a torque-late inline-four than on a torque-early single. A first-time ZX-4R rider can typically get within 0.15s of their best ET inside ten passes; a first-time Pulsar NS400Z rider often needs thirty passes to learn the wheelie-management line.',
  },
  {
    type: 'h2',
    text: 'Run your own numbers',
  },
  {
    type: 'p',
    text: 'If you own a ZX-4R, are weighing one against a used ZX-6R or a CBR650R, or want to see what a 400cc inline-four does, the free simulator at motoquant.in lets you change rider weight, ambient temperature, density altitude, sprockets and catalog parts, and shows where each tenth comes from. The cluster bias on this class is documented at 0.0–0.2 seconds from published instrumented tests, so the simulated numbers hold up in absolute terms, not only relative ones.',
  },
  {
    type: 'p',
    text: 'The ZX-4R is the cheapest way into inline-four ownership in India right now, and it does not need much to run quickly: a quickshifter and a sprocket swap together are worth more than a ₹2-lakh exhaust-and-ECU package on most twins. Spend your first weekend learning the high-RPM launch, and the bike will run the ETs its spec sheet promises.',
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
            {['Kawasaki', 'Ninja ZX-4R', '400cc', 'inline-four', 'physics'].map((t) => (
              <span
                key={t}
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Kawasaki Ninja ZX-4R Quarter-Mile Physics: 400cc Inline-Four
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
              <Link href="/blog/ktm-duke-390-vs-rc-390-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                KTM Duke 390 vs RC 390: Quarter-Mile Physics at Aamby Valley
              </Link>:{' '}
              the 400-class single-cylinder benchmark the ZX-4R outruns by a full second.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/pulsar-ns400z-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                Pulsar NS400Z Quarter-Mile Physics (and Why an RC 390 Still Wins)
              </Link>:{' '}
              the cheapest Indian 400 single, and why displacement is not destiny.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-the-motoquant-physics-engine-works" className="text-brand-accent hover:text-brand-orange transition-colors">
                How the MotoQuant Physics Engine Works
              </Link>:{' '}
              the 15-sub-model architecture behind every ET prediction.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-to-tune-for-aamby-valley-in-november" className="text-brand-accent hover:text-brand-orange transition-colors">
                How to Tune for Aamby Valley in November
              </Link>:{' '}
              the venue conditions used for the simulation in this post.
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
            <div className="font-display font-bold text-white mb-1">Run the ZX-4R yourself</div>
            <div className="text-white/60 text-sm">
              Free simulator: pick the Kawasaki Ninja ZX-4R, dial in your local conditions, and watch the ET update live.
            </div>
          </div>
          <Link
            href="/simulator?bike=kawasaki-ninja-zx-4r"
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
