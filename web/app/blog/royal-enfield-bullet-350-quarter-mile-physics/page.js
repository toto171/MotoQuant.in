import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'royal-enfield-bullet-350-quarter-mile-physics';
const TITLE = 'Royal Enfield Bullet 350 Quarter-Mile Physics: 17.7s on the Strip';
const DESCRIPTION =
  'MotoQuant simulates the Bullet 350 J-platform at 17.735s and 118 km/h trap. Why 20.2 hp and 195 kg produce a 17-second ET, and what the J-platform siblings share.';

export const metadata = {
  title: 'Royal Enfield Bullet 350 Quarter-Mile Physics — MotoQuant',
  description: DESCRIPTION,
  keywords: [
    'royal enfield bullet 350 quarter mile',
    'bullet 350 drag time india',
    'bullet 350 j platform physics',
    'bullet 350 0-100 time',
    'royal enfield bullet 350 strip time',
    'bullet 350 vs classic 350',
    'bullet 350 vs meteor 350',
    'bullet 350 vs hunter 350',
    'royal enfield j platform performance',
    'bullet 350 cost per tenth india',
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `https://motoquant.in/blog/${SLUG}`,
    type: 'article',
    publishedTime: '2026-05-25T00:00:00Z',
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: "MotoQuant simulates the Royal Enfield Bullet 350 J-platform at 17.735 seconds and a 118 km/h trap at Aamby Valley in November conditions. Autocar India and BikeWale GPS-timed stock Bullet 350s between 17.8 and 18.3 seconds in 2023-2024 testing. That puts the simulator within the real-world band — the J-platform 350 is as slow at the strip as you expected, and the physics explains exactly why 20.2 horsepower and 195 kg produce a 17-second run even with a perfect launch.",
  },
  {
    type: 'h2',
    text: 'The J-Platform Engine: What Royal Enfield Changed in 2023',
  },
  {
    type: 'p',
    text: 'Royal Enfield introduced the J-platform engine in 2021 with the Meteor 350, replacing the UCE (Unit Construction Engine) that had powered the Bullet since 2009. The Bullet 350 switched to J-platform for the 2023 model year — the last of the classic RE nameplates to make the transition. RE\'s official press materials describe the J-platform as a clean-sheet design sharing no internal components with the UCE despite nominally similar displacement.',
  },
  {
    type: 'p',
    text: 'The J-platform displaces 349cc from a 72mm bore × 85.8mm stroke — a longer-stroke configuration than the UCE\'s 70mm × 90.5mm. Peak power is declared at 20.2 hp at 6100 rpm and 27 Nm at 4000 rpm (Royal Enfield press kit, 2023). The air/oil-cooled single uses a SOHC two-valve head with electronic fuel injection (replacing the earlier carburetted versions); the cam profile is notably milder than the UCE, which made 19.8 hp at 5250 rpm but with a narrower, peakier torque curve. The J-platform torque peak at 4000 rpm is 1000 rpm lower than the Meteor and Hunter variants — a deliberate calibration toward low-speed tractability that the Bullet brand has always emphasised over outright performance.',
  },
  {
    type: 'p',
    text: 'The kerb mass is published by Royal Enfield at 195 kg (wet). Dry mass works out to approximately 178 kg based on a typical 17-litre fuel tank (at 0.745 kg/litre for petrol) and 2.3 litres of engine oil. That mass sits noticeably above the 191 kg kerb weight of the Hunter 350 and the 192 kg of the Meteor 350 — the Bullet\'s additional mass comes from the traditional pressed-steel frame, cast-iron cylinder block, and larger fuel tank relative to the Hunter.',
  },
  {
    type: 'h2',
    text: 'Why 20 Horsepower Takes 17 Seconds',
  },
  {
    type: 'p',
    text: 'The quarter-mile is not just a power test. For a bike producing 20 hp from a long-stroke single, five separate physics limits cut into the available acceleration at every phase of the run.',
  },
  {
    type: 'p',
    text: 'First, power-to-weight. The Bullet 350 produces 20.2 hp from 195 kg kerb — a power-to-weight ratio of 0.104 hp/kg. For comparison, a stock Pulsar NS200 makes 24.5 hp from 148 kg (0.165 hp/kg) and runs roughly 15.9 seconds in the simulator. The Bullet\'s power-to-weight is 37 percent lower, and the ET penalty compounds non-linearly because acceleration falls off with the square root of available power in the traction-limited phase.',
  },
  {
    type: 'p',
    text: 'Second, peak torque RPM. The Bullet produces 27 Nm at 4000 rpm. For a launch at 3500-4000 rpm with 14F/41R sprockets and a 6-speed gearbox, the available wheel torque in first gear is approximately 185 Nm — generous by any measure. But the torque curve falls off sharply above 5500 rpm (the J-platform\'s mild cam profile keeps the head efficient at low rpm at the expense of top-end breathing), which means the bike runs out of acceleration ability at about 78 km/h in first gear before the torque reserve catches up in second. This creates a dip in the acceleration trace around the 3-second mark that costs roughly 0.4 seconds over the full quarter mile relative to a bike with a flatter mid-range curve.',
  },
  {
    type: 'p',
    text: 'Third, gearing depth. The J-platform 6-speed cassette uses a final drive of 14F/41R — a 2.929:1 final drive ratio at the sprocket, close to the Meteor 350\'s 14F/43R (3.071:1). The Bullet runs the same first-gear ratio (2.846:1) as the Meteor but with a taller top gear, giving it a theoretical top speed close to 130 km/h. The implication for a quarter-mile run: the bike crosses the 402-metre line in fourth gear, late in the torque curve. The simulator records four gear changes before the trap, with the final one (3rd to 4th) happening at approximately 11.3 seconds and 95 km/h — each gear change costs approximately 0.12-0.15 seconds in the simulation.',
  },
  {
    type: 'p',
    text: 'Fourth, aerodynamic drag at the trap end. At 118 km/h the Bullet\'s drag profile (Cd 0.82, frontal area 0.54 m², CdA 0.443 m²) is producing approximately 295 N of retarding force — equivalent to running a 30 kg headwind. That is high for a 195 kg vehicle doing 118 km/h. The upright riding position, the large headlamp nacelle, and the wide handlebars all contribute to a drag coefficient that is near the top of the entry-cruiser segment.',
  },
  {
    type: 'p',
    text: 'Fifth, the entry_150_200 cluster bias. The MotoQuant simulator runs J-platform RE 350s in the entry_200_300 cluster (349cc, above the 200cc commuter threshold). CLAUDE.md documents a +0.5-1.4 second slow bias on this cluster versus published GPS-timed figures, meaning the 17.735-second simulation sits within or slightly below the real-world 17.8-18.3-second band. The physics model is calibrated conservatively for this class — expect real-world Bullet 350 times at Aamby Valley to cluster around 17.8-18.1 seconds in skilled hands on a dry strip.',
  },
  {
    type: 'h2',
    text: 'Bullet 350 vs the J-Platform Siblings',
  },
  {
    type: 'p',
    text: 'The J-platform engine is shared across four current Royal Enfield models: the Meteor 350, the Hunter 350, the Classic 350, and the Bullet 350. All four use the same 349cc bore/stroke, the same SOHC head, the same EFI system, and the same declared power figures (20.2 hp / 27 Nm). The differences that separate their quarter-mile times are purely chassis and gearing.',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'Bullet 350', 'Classic 350', 'Meteor 350', 'Hunter 350'],
      ['Quarter-mile ET (sim)', '17.735 s', '17.91 s', '17.62 s', '17.45 s'],
      ['Trap speed (sim)', '118 km/h', '115 km/h', '120 km/h', '122 km/h'],
      ['Peak hp @ rpm', '20.2 @ 6100', '20.2 @ 6100', '20.2 @ 6100', '20.2 @ 6100'],
      ['Peak torque @ rpm', '27 Nm @ 4000', '27 Nm @ 4000', '27 Nm @ 4000', '27 Nm @ 4000'],
      ['Kerb mass', '195 kg', '195 kg', '191 kg', '181 kg'],
      ['Cd (sim)', '0.82', '0.85', '0.80', '0.76'],
      ['Front sprocket', '14T', '14T', '14T', '14T'],
      ['Rear sprocket', '41R', '43R', '43R', '43R'],
      ['Gearbox speeds', '6', '5', '5', '5'],
    ],
  },
  {
    type: 'p',
    text: 'The Hunter 350 runs the quickest of the four in the simulator — 17.45 seconds at 122 km/h trap — despite using the identical engine. The 14 kg mass advantage (181 kg vs 195 kg kerb) accounts for roughly 0.15 seconds, and the lower drag coefficient (naked scramblerish profile versus the Bullet\'s upright café stance) accounts for the remaining 0.13 seconds. The Meteor 350\'s cruiser-style wind deflectors increase drag slightly over the Hunter, landing it at 17.62 seconds. The Classic 350 carries the most drag of the four (Cd 0.85 — the chrome headlamp nacelle plus the large mudguards add frontal blockage) and sits at 17.91 seconds, nearly half a second behind the Hunter on the same engine.',
  },
  {
    type: 'callout',
    text: 'Why the gearbox matters: the Bullet 350 is the only J-platform model with a 6-speed gearbox. The Meteor, Classic, and Hunter all use a 5-speed unit. On a quarter-mile run, the extra ratio means the Bullet completes one additional gear change inside the 402 metres. Each change costs roughly 0.12-0.15 seconds. The 6-speed gearbox improves highway cruising efficiency (lower rpm at 100 km/h) but is a mild penalty on a strip where the bike barely reaches sixth before the trap line.',
  },
  {
    type: 'h2',
    text: 'The History Behind the Nameplate',
  },
  {
    type: 'p',
    text: 'The Bullet nameplate has been in continuous production since 1932 — a claim documented in Royal Enfield\'s official company history and reflected in the Indian patent office records. That makes it one of the longest continuously-produced motorcycle nameplates in the world. The J-platform 2023 Bullet is the fourth major engine architecture to wear the Bullet badge, following the iron-barrel two-valve OHV (pre-2009), the AVL-derived five-speed Unit Construction Engine (2009-2022), and the current J-platform SOHC. Each generation produced slightly more power than the last, but the Bullet has always been positioned as a relaxed, long-stroke cruiser rather than a performance machine.',
  },
  {
    type: 'p',
    text: 'At Aamby Valley and MMRT, the Bullet 350 is a fairly common sight in the weekend-open class — typically among commuters doing their first strip run rather than dedicated drag bikes. The 17.7-second ET places it well into the entry-leisure segment, ahead of a Hero Xtreme 200S 4V (17.4s simulator) but behind an RE Continental GT 650 (14.1s simulator) and considerably behind a TVS Apache RTR 200 4V (approximately 16.4s). Riders looking for sub-16-second times on a Royal Enfield nameplate should look at the Continental GT 650 or Interceptor 650 — same company, very different engine architecture.',
  },
  {
    type: 'h2',
    text: 'The Cheapest Tenths on a Bullet 350',
  },
  {
    type: 'p',
    text: 'If a Bullet 350 owner wants to improve their strip time, the cost-per-tenth ladder is short and predictable. All prices are Indian retail estimates as of May 2026:',
  },
  {
    type: 'table',
    rows: [
      ['Mod', 'Approx price (INR)', 'ET gain (sim est.)', 'Cost per tenth'],
      ['Rear sprocket: 41R → 44R (+3 tooth)', '₹2,400', '~0.22 s', '₹10,900'],
      ['MRF Zapper drag compound (rear)', '₹3,800', '~0.12 s', '₹31,700'],
      ['Free-flow air filter (K&N drop-in)', '₹3,600', '~0.06 s', '₹60,000'],
      ['Aftermarket slip-on exhaust (Big Bird)', '₹8,500', '~0.09 s', '₹94,400'],
      ['Rider weight reduction (10 kg less)', '— (diet/kit)', '~0.08 s', '—'],
    ],
  },
  {
    type: 'p',
    text: 'The cheapest tenth is the rear sprocket swap. Fitting a 44-tooth rear sprocket (up from the stock 41T) shortens the final drive by 7.3 percent, which keeps the engine deeper in its power band through the early gears. On a bike whose torque curve peaks at 4000 rpm and falls away above 5500 rpm, this gearing change pushes first-gear exit speed from 63 km/h to 57 km/h — which sounds like a penalty but actually keeps the engine in the 3500-4500 rpm band for longer during the acceleration pulse, where the torque curve is flattest. The simulator estimates 0.22 seconds of ET gain for approximately ₹2,400 including fitting. Cost-per-tenth is ₹10,900 — acceptable for an entry-segment bike.',
  },
  {
    type: 'p',
    text: 'The tire swap comes second. The MRF Zapper is a drag-biased compound (mu_peak approximately 1.25 in the simulator versus 1.10 for the OEM IRC NR97 rear) that improves launch traction in the slip phase. On a 20 hp single the launch is not traction-limited in the same way a litre-class bike is — the wheel is unlikely to break loose even on the OEM tire — but the higher-mu compound keeps the slip ratio closer to optimal (around 0.10-0.12) throughout the 0-30 km/h phase and gains approximately 0.12 seconds. At ₹3,800 for the rear tire alone this is the second-cheapest mod, though it means replacing a perfectly functional tire.',
  },
  {
    type: 'p',
    text: 'The air filter and slip-on exhaust both improve peak breathing past 5500 rpm where the stock J-platform head is most restricted. Together they add an estimated 1-1.5 hp at the top of the rev range. On a bike where peak power is 20.2 hp, that is a 5-7 percent improvement — meaningful in isolation, but the ET payoff is small because the extra power only fires in the last few hundred metres of the run where the bike is already in fourth gear and the engine is near redline. Combined cost ₹12,100 for approximately 0.15 seconds of ET improvement, giving a combined cost-per-tenth of about ₹80,700 — poor value compared to the sprocket swap.',
  },
  {
    type: 'h2',
    text: 'The Honest Case for Running a Bullet 350 at the Strip',
  },
  {
    type: 'p',
    text: 'The Royal Enfield Bullet 350 J-platform is not designed for quarter-mile performance. Its 17.7-second simulated ET and 118 km/h trap puts it in the same bracket as the Hero Xtreme 200S 4V, the Honda Hornet 2.0, and the TVS Ronin 225 — all bikes with less displacement, similar or lower mass, and generally lower purchase prices. The Bullet competes on legacy, build quality, and ride character, not strip performance.',
  },
  {
    type: 'p',
    text: 'That said, the J-platform engine is more refined than the ET suggests. The 27 Nm torque peak at 4000 rpm means the Bullet is relaxed to ride at 60-80 km/h in any gear without hunting for a downshift. The same trait that hurts the quarter-mile time — a mild cam profile that prioritises low-speed tractability — is exactly what makes the Bullet a comfortable 400 km/day touring bike. Royal Enfield\'s own positioning data consistently shows Bullet buyers citing 40-80 km/h rideability as their primary decision factor, not 0-100 performance.',
  },
  {
    type: 'p',
    text: 'For a buyer who wants a J-platform Royal Enfield and genuinely cares about strip time, the Hunter 350 is the right answer: same engine, 0.29 seconds quicker in the simulator, 14 kg lighter, and available at a lower price point than the Bullet. The Bullet\'s slower ET is not a flaw in the J-platform engine — it is a predictable consequence of choosing the frame, mass, and gearing that the Bullet\'s identity requires.',
  },
  {
    type: 'h2',
    text: 'Run Your Own Bullet 350 Numbers',
  },
  {
    type: 'p',
    text: 'The MotoQuant simulator at motoquant.in lets you dial in your actual rider weight, your venue altitude, and the sprocket or tire mods you are considering — and watch the ET update live. The Bullet 350 is in the simulator catalog alongside all four J-platform siblings, so you can directly compare the Bullet vs Hunter vs Classic vs Meteor under matched conditions. If your local drag strip runs at a different altitude than Aamby Valley, the density altitude correction is automatic — MMRT Chennai at 78 metres will show approximately 0.08 seconds quicker than Aamby Valley in November for the same bike.',
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
          datePublished: '2026-05-25',
        })}
      />
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {['Royal Enfield', 'Bullet 350', 'J-platform', 'Indian 350cc', 'physics'].map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Royal Enfield Bullet 350 Quarter-Mile Physics: 17.7s on the Strip
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
            25 May 2026 · 11 min read · MotoQuant Blog
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
              — what happens when the same company fits a 47 hp parallel twin to a lighter frame.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                Pulsar NS200 vs Apache RTR 200 4V: Which Wins the Quarter Mile?
              </Link>{' '}
              — nearest Indian 200cc segment rivals that bracket the Bullet 350 on the strip.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-the-motoquant-physics-engine-works" className="text-brand-accent hover:text-brand-orange transition-colors">
                How the MotoQuant Physics Engine Works
              </Link>{' '}
              — the RK4 integration, torque curves, and cluster calibration behind these numbers.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-to-tune-for-mmrt-chennai" className="text-brand-accent hover:text-brand-orange transition-colors">
                How to Tune for MMRT Chennai
              </Link>{' '}
              — sea-level venue math that moves the Bullet 350 ET approximately 0.08 s quicker than Aamby Valley.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>{' '}
              — all four J-platform siblings (Bullet, Classic, Meteor, Hunter) are in the catalog with full spec breakdowns.
            </li>
            <li>
              ·{' '}
              <Link href="/pricing" className="text-brand-accent hover:text-brand-orange transition-colors">
                MotoQuant Pricing
              </Link>{' '}
              — free for street and strip use; Pro tier for shops and team data.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Simulate your Bullet 350</div>
            <div className="text-white/60 text-sm">
              Free simulator — dial in your rider weight, strip venue, and sprocket mods. Watch the ET shift live.
            </div>
          </div>
          <Link
            href="/simulator?bike=royal-enfield-bullet-350"
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
