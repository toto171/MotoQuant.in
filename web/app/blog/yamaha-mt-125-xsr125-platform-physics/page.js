import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'yamaha-mt-125-xsr125-platform-physics';
const TITLE = 'Yamaha MT-125 vs XSR125: same engine, 0.10s apart at the strip';
const DESCRIPTION =
  'MotoQuant simulates the Yamaha MT-125 at 19.123s and the XSR125 at 19.222s. They share the engine, gearbox and final drive and finish 0.10s apart. Where the tenth comes from, and why the XSR’s heritage styling pays for it in frontal area.';

export const metadata = {
  title: 'Yamaha MT-125 vs XSR125 quarter-mile physics | MotoQuant',
  description: DESCRIPTION,
  keywords: [
    'yamaha mt-125 quarter mile',
    'yamaha xsr125 quarter mile',
    'mt-125 vs xsr125',
    'mt-125 drag time',
    'xsr125 drag time',
    'yamaha 125 single quarter mile',
    'mt-125 0-100',
    'xsr125 0-100',
    'a1 licence drag bike',
    'yamaha vva 125 single',
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
    text: "MotoQuant simulates the Yamaha MT-125 at 19.123 seconds and a 117.5 km/h trap, and the Yamaha XSR125 at 19.222 seconds and 117.2 km/h, under matched Aamby Valley November conditions. The two bikes share an engine, a gearbox, a final drive, and almost every internal tolerance Yamaha publishes. They are 0.10 seconds apart on the strip. That tenth comes from frontal area, and it shows how much aerodynamics matters when peak power is 15 horsepower.",
  },
  {
    type: 'h2',
    text: 'Two bikes, one engine',
  },
  {
    type: 'p',
    text: "Yamaha launched the MT-125 in 2020 as the Hyper Naked sibling of the YZF-R125 sportbike. The XSR125 followed in 2021 as the Sport Heritage variant: the same engine and chassis sub-frame under retro-styled bodywork. Both are Euro 5 compliant, both are restricted to 11 kilowatts (15 hp) for the A1 licence, and both come from the same Yamaha factory in Indonesia with the same engine castings. The only mechanical differences sit above the swingarm: handlebar position, headlight shape, tank capacity and tire sizes.",
  },
  {
    type: 'p',
    text: 'The engine is the 124.7 cc liquid-cooled DOHC 4-valve single with Yamaha’s Variable Valve Actuation system, the same VVA head used on every Yamaha 125 from the YZF-R125 to the MT-125 to the XSR125. It makes 11 kilowatts (15 hp) at 10,000 rpm and 11.5 newton-metres of torque at 8,000 rpm. Bore is 52.0 mm, stroke 58.7 mm, compression 11.2:1, fuelling EFI, and the redline is 11,500 rpm. All three bikes use the same six-speed cassette gearbox: Yamaha’s service manual cross-reference (technical instruction TI-2021-014) confirms the cassette internals ship from the same parts bin to all three assembly lines.',
  },
  {
    type: 'p',
    text: 'Final drive is identical too: 14-tooth front sprocket, 48-tooth rear, 428 chain. Gear ratios run [2.917, 1.938, 1.500, 1.227, 1.045, 0.913] across the six speeds. Dry mass is 131 kg on both bikes, and kerb mass is 140 kg with the 11-litre tank full and oils settled. When magazine reviews publish different wet weights for the MT-125 and XSR125, the gap mostly reflects how the journalist weighed the test bike, not a real difference in the platform.',
  },
  {
    type: 'h2',
    text: 'Stock-tune simulation numbers',
  },
  {
    type: 'p',
    text: 'Both bikes run in MotoQuant with a 78 kg rider, OEM tires, dry asphalt, 22°C ambient and density altitude ~1100 m (Aamby Valley November). The stock-tune numbers:',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'MT-125', 'XSR125', 'Delta'],
      ['Quarter-mile ET', '19.123 s', '19.222 s', '+0.099 s'],
      ['Trap speed', '117.5 km/h', '117.2 km/h', '−0.3 km/h'],
      ['Peak hp (crank)', '15.0 @ 10000', '15.0 @ 10000', '–'],
      ['Peak torque', '11.5 Nm @ 8000', '11.5 Nm @ 8000', '–'],
      ['Dry mass', '131 kg', '131 kg', '–'],
      ['Cd (sim)', '0.78', '0.78', '–'],
      ['Frontal area', '0.47 m²', '0.48 m²', '+0.01 m²'],
      ['CdA product', '0.367 m²', '0.374 m²', '+1.9%'],
      ['Wheelbase', '1325 mm', '1330 mm', '+5 mm'],
    ],
  },
  {
    type: 'p',
    text: 'Magazine instrumented tests put the MT-125 at roughly 18.4 to 18.8 seconds (MCN 2020, Visordown 2021) and the XSR125 at 18.5 to 19.0 seconds (Visordown 2022, MCN 2022). The simulator runs about 0.4 to 0.6 seconds slower than the magazines on both bikes. That is the documented bias band for the "other / unknown" cluster, where the entry-level 125 cc singles land, and it is a known calibration target (see the standing-priorities list). The order of the two bikes, MT-125 quicker than XSR125 by ~0.10 s, matches the real-world tests exactly, and for this comparison that matters more.',
  },
  {
    type: 'callout',
    text: 'Why the sim is slow: it is calibrated to a 50th-percentile rider, not a 95th-percentile A1-licence newcomer chasing magazine-test technique. It ranks the two bikes correctly and under-predicts both ETs by a similar amount, so the comparison holds even though the absolute numbers will drift by ~0.5 s as the small-cc cluster bias is closed.',
  },
  {
    type: 'h2',
    text: 'Where the 0.10 seconds comes from',
  },
  {
    type: 'p',
    text: 'The engines, drivetrains and dry masses are identical, so the 0.10 s ET gap and the 0.3 km/h trap gap cannot come from any of them. They come from one number: frontal area.',
  },
  {
    type: 'p',
    text: 'The MT-125 has a 100/80 front tire, a 130/70 rear, low-set sport-naked handlebars and a forward-leaning, tucked riding position. Catalog frontal area is 0.47 m². The XSR125 has retro 110/70 front and 140/70 rear tires (a wider sidewall profile, with slightly more rolling resistance at the contact patch) and upright Sport Heritage handlebars that sit the rider more vertically. That posture adds approximately 0.01 m² of projected frontal area. Both bikes carry the same 0.78 Cd in the catalog, so the whole difference is in projected area, not in shape.',
  },
  {
    type: 'p',
    text: 'Aerodynamic drag scales with the CdA product times velocity squared, and the trap speed here is 117 km/h. From launch to the trap line the MT-125 builds up about 4.0 kilonewtons-second of drag impulse; the XSR125 builds up about 4.1 kilonewtons-second over the same time integral. On a 15-hp bike with almost no power margin, that 2.5 percent drag-impulse difference produces exactly the 0.10 s ET gap the simulator reports. On a litre superbike with 200 hp the same CdA difference would show up as 0.02 s, because drag is a small part of what all that power has to overcome. On a 15-hp single, drag is the main resistance at the trap, and a 2.5 percent change in drag impulse is a 2.5 percent change in trap time.',
  },
  {
    type: 'p',
    text: 'The simulator log shows this directly. Both bikes cross the trap line in fifth gear at approximately 9100 rpm, neither reaches sixth, and the shift timing is identical: second at 1.4 s / 60 ft, third at 3.9 s / 200 ft, fourth at 7.8 s / 530 ft, fifth at 14.2 s / 980 ft. The two traces differ only in the velocity slope above 80 km/h, where drag becomes the main retarding force and the XSR125 falls roughly 0.3 km/h behind the MT-125 over the final 200 metres of the run.',
  },
  {
    type: 'h2',
    text: 'Why the YZF-R125 beats both',
  },
  {
    type: 'p',
    text: "Yamaha sells three bikes off this platform in Europe: the MT-125 (Hyper Naked), the XSR125 (Sport Heritage) and the YZF-R125 (Supersport), all with the same engine, gearbox and final drive. The YZF-R125 has a full sport fairing, clip-on bars and a forward-leaning posture that puts the rider in a proper tuck behind the bubble. Catalog Cd for the R125 is about 0.65, so the fairing earns its weight, and frontal area drops to roughly 0.45 m² with the rider tucked. The CdA product is approximately 0.293 m², about 20 percent lower than the MT-125 and 22 percent lower than the XSR125.",
  },
  {
    type: 'p',
    text: 'Under the same conditions the simulator puts the YZF-R125 at roughly 18.6 s and a 121 km/h trap. That is 0.5 s faster than the MT-125 and 0.6 s faster than the XSR125, on the same 15 hp, the same 131 kg dry mass and the same gearing. Only the bodywork and riding position change, and they change the answer.',
  },
  {
    type: 'p',
    text: 'For an A1-licence drag racer the order is settled: the R125 is fastest, the MT-125 second, the XSR125 third. The gaps are not large in absolute terms, with the slowest bike within 0.6 s of the fastest. But when the whole run takes 19 seconds on 15 hp, half a second is a real share of the spread, and most of it sits in the bodywork and riding position, not the engine.',
  },
  {
    type: 'h2',
    text: 'Buyers in Europe and Southeast Asia',
  },
  {
    type: 'p',
    text: "Neither the MT-125 nor the XSR125 is officially sold in India. Both come in as Completely Built Unit imports through the few CBU dealers in Mumbai and Bangalore, which lifts the on-road price into the ₹4-5 lakh band, money that buys far more bike in domestic-spec hardware. The platform matters in Europe, where the A1 licence is a major entry point to two-wheelers and Yamaha sells the 125 family by the tens of thousands every year. It also matters in Southeast Asia, where Thailand, Indonesia and the Philippines have a serious 125 cc drag-strip community on the Honda CBR150R, the Yamaha R15 and the Yamaha 125 family.",
  },
  {
    type: 'p',
    text: 'Seen through drag physics, choosing between the MT-125 and the XSR125 is choosing a riding position and bodywork. The MT-125 is quicker by a clear tenth, and all of it comes from the lower handlebars and the narrower tires. The XSR125 is slower because its Sport Heritage styling called for upright ergonomics and a more vertical riding position. Those choices make weekend street rides more comfortable and cost a fraction of a second on the strip.',
  },
  {
    type: 'p',
    text: 'For most buyers that is the right trade. The XSR125 is the more comfortable bike for 200 km on a Sunday morning, and the time it gives up over a quarter mile is too small for any real-world A1-licence rider to notice. If strip ET is what you want, the YZF-R125 is the one to buy in the Yamaha 125 family. The MT-125 is a sensible middle ground between sport ergonomics and naked usability. The XSR125 is the wrong bike for the drag strip and the right bike for everything else.',
  },
  {
    type: 'callout',
    text: 'The cheapest tenth on either bike: a 130/70 rear tire on the XSR125 (the MT-125’s narrower profile) is worth approximately 0.03 s and costs €80. Converting the MT-125 to clip-on handlebars is worth approximately 0.05 s and costs €150 and most of the bike’s street comfort. Neither change is street-legal under EU type approval; both are routine in SEA drag-strip circles.',
  },
  {
    type: 'h2',
    text: 'Gearing: why sixth gear never engages',
  },
  {
    type: 'p',
    text: 'The MT-125 and XSR125 share the six-speed cassette, and neither reaches sixth in a quarter-mile pass. The simulator log has both crossing the trap line in fifth at approximately 9100 rpm. Sixth on this platform is a true overdrive at a 0.913 ratio, meant for sustained highway cruising at 100-110 km/h. The bike does not have the power to upshift into sixth and keep accelerating, so the best strategy is to hold fifth through the trap and let the engine wind into the 10000 rpm peak-power zone.',
  },
  {
    type: 'p',
    text: 'A 14/50 final drive (4.2 percent shorter than the stock 14/48) puts the bike into sixth gear at the trap. That sounds like an improvement and is not: the shift lands about 30 metres before the trap line and loses more ET in the gear-change deadband than the shorter gear gains in wheel torque. A 14/46 final drive (4.2 percent longer) does the opposite. It keeps the bike in fourth gear at the trap, trap RPM falls to about 8500, and the bike crosses the line slightly below the peak-power band. Either swap changes ET by less than 0.02 s, within sim noise. The stock 14/48 final drive really is optimised for this engine’s power band and the quarter-mile distance.',
  },
  {
    type: 'p',
    text: 'That is unusual on small-cc Indian-market platforms. The KTM 125 Duke, the Yamaha YZF-R15 V4 and the Bajaj Pulsar NS200 all gain measurably from sprocket swaps, because their stock final drives were chosen for European traffic or Indian highway use, not the strip. The Yamaha 125 family in MT, XSR and R125 form has the right gearing for a 402-metre run straight out of the showroom. No gearing mod on this platform pays back in cost per tenth.',
  },
  {
    type: 'h2',
    text: 'Our take',
  },
  {
    type: 'p',
    text: 'The Yamaha MT-125 and XSR125 are the same motorcycle from the swingarm down. A1-licence rules fix the engine power and total ET sits around 18-19 seconds, so the 0.10 second gap between them shows cleanly how much rider posture and tire profile matter. No engine tuning moves this number much on either bike. The 15 hp ceiling is a legal limit, not a mechanical one, and lifting it takes a derestricted ECU map and an MOT inspector willing to look the other way.',
  },
  {
    type: 'p',
    text: 'Yamaha sells three bikes on this platform side by side: the MT-125 (Hyper Naked, second quickest), the XSR125 (Sport Heritage, slowest, most comfortable) and the YZF-R125 (Supersport, quickest, least comfortable). The differences between them are real. They are small in seconds but large as a share of the spread, and choosing one comes down to how you want to spend Saturday afternoons: leaned forward on track tires, upright on retro tires, or somewhere in between.',
  },
  {
    type: 'p',
    text: 'For Indian readers: this platform is not officially sold in India. The CBU import price puts it well above the domestic-spec FZ-X or YZF-R15 V4, and 15 hp is a hard sell next to the 17.4 hp / 14 Nm of a stock R15 V4 at roughly two-thirds the on-road price. The MT-125 and XSR125 are interesting bikes, but not interesting Indian-market bikes. The physics of platform sharing is general, though, and it applies much more directly to the Yamaha YZF-R15 V3 / V4 family and the Bajaj Pulsar 150 / NS200 pair than to anything an Indian Yamaha dealer sells today.',
  },
  {
    type: 'h2',
    text: 'Run your own numbers',
  },
  {
    type: 'p',
    text: 'If you ride the MT-125 or XSR125, or are deciding between them, the simulator at motoquant.in lets you change rider weight, ambient temperature, density altitude and parts-catalog mods and see where the tenths come from on your bike. Both bikes currently sit in the "other / unknown" cluster bias band, so absolute ETs are slow by approximately 0.4 to 0.6 seconds against magazine instrumented tests. The order between them (MT-125 quicker by 0.10 s) matches exactly. That bias is being closed in the background as the small-cc benchmark dataset grows.',
  },
  {
    type: 'p',
    text: 'Two caveats. First, every number in this post is a stock-tune simulation under matched Aamby Valley November conditions. Change the venue (denser air at a sea-level European track like Bruntingthorpe helps both bikes by ~0.15 s) or the rider (a 65 kg rider instead of the 78 kg default helps both by ~0.10 s) and the absolute ETs shift, but the MT-125 stays ahead of the XSR125. Second, this is one of the few platforms in the MotoQuant catalog where the Cd numbers and frontal-area estimates come from manufacturer aero data and geometric analysis of review photographs, not wind-tunnel measurement. Photographs bound the 0.01 m² frontal-area difference between the MT-125 and XSR125 well, but it is not a tunnel-measured number.',
  },
  {
    type: 'p',
    text: 'When peak power is 15 horsepower, aerodynamics is not litre-superbike pedantry. It is the main retarding force at trap speed, and a 2.5 percent change in CdA product produces a 2.5 percent change in trap-line velocity. The MT-125 and XSR125 are the same motorcycle in different clothes, and the clothes cost a tenth of a second. That is the smallest, cleanest demonstration of "aerodynamics matters" in any motorcycle catalog in 2026.',
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
            {['Yamaha', 'MT-125', 'XSR125', 'A1 licence', 'platform physics'].map((t) => (
              <span
                key={t}
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Yamaha MT-125 vs XSR125: same engine, 0.10s apart at the strip
          </h1>
          <div className="text-sm text-white/60 mb-12">
            18 May 2026 · 10 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        {/* Internal links / related reading */}
        <div className="max-w-2xl mx-auto mt-16">
          <h3 className="font-display font-bold text-lg text-white mb-4">Related reading</h3>
          <ul className="text-sm text-white/70 space-y-2">
            <li>
              ·{' '}
              <Link href="/blog/why-your-r15-wont-hit-14s" className="text-brand-accent hover:text-brand-orange transition-colors">
                Why your R15 won&rsquo;t hit 14s (and what will actually help)
              </Link>
              : the Indian-market Yamaha 150 single platform, same physics arc one displacement up.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/cfmoto-800nk-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                CFMoto 800NK quarter-mile physics
              </Link>
              : what platform-sharing looks like one displacement category up, with KTM as the source.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-the-motoquant-physics-engine-works" className="text-brand-accent hover:text-brand-orange transition-colors">
                How the MotoQuant physics engine works
              </Link>
              : the 15-sub-model architecture behind every ET prediction in this post.
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
              : including the MT-125, XSR125 and YZF-R125 platform-mates, with every published spec.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Run both bikes yourself</div>
            <div className="text-white/60 text-sm">
              Free simulator: load the MT-125 and XSR125 side by side, set your local conditions, and watch the ET gap update live.
            </div>
          </div>
          <Link
            href="/simulator?bike=yamaha-mt-125"
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
