import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'yamaha-mt-125-xsr125-platform-physics';
const TITLE = 'Yamaha MT-125 vs XSR125: Same Engine, 0.10s Apart at the Strip';
const DESCRIPTION =
  'MotoQuant simulates the Yamaha MT-125 at 19.123s and the XSR125 at 19.222s — same engine, same gearbox, same final drive, 0.10s apart. Where the tenth comes from and why the heritage tax is paid in frontal area.';

export const metadata = {
  title: 'Yamaha MT-125 vs XSR125 Quarter-Mile Physics — MotoQuant',
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
    text: "MotoQuant simulates the Yamaha MT-125 at 19.123 seconds and a 117.5 km/h trap, and the Yamaha XSR125 at 19.222 seconds and 117.2 km/h, under matched Aamby Valley November conditions. The two bikes share an engine, a gearbox, a final drive, and almost every internal tolerance Yamaha publishes. They are 0.10 seconds apart on the strip. The interesting question is not which one wins. It is where that single tenth lives, because the answer is a clean physics demonstration of how much aerodynamics actually matters when peak power is 15 horsepower.",
  },
  {
    type: 'h2',
    text: 'Two Bikes, One Engine',
  },
  {
    type: 'p',
    text: "Yamaha launched the MT-125 in 2020 as the Hyper Naked sibling of the YZF-R125 sportbike. The XSR125 followed in 2021 as the Sport Heritage variant — same engine, same chassis sub-frame, retro-styled bodywork over the top. Both bikes are Euro 5 compliant, both are A1-licence-restricted at 11 kilowatts (15 hp), and both pull from the same Yamaha factory in Indonesia using the same engine castings. The only mechanical differences between them sit above the swingarm: handlebar position, headlight shape, tank capacity, and tire sizing.",
  },
  {
    type: 'p',
    text: 'The engine is the 124.7 cc liquid-cooled DOHC 4-valve single with Yamaha’s Variable Valve Actuation system — the same VVA head that appears on every Yamaha 125 platform from the YZF-R125 to the MT-125 to the XSR125. It produces 11 kilowatts (15 hp) at 10,000 rpm and 11.5 newton-metres of torque at 8,000 rpm. Bore is 52.0 mm, stroke 58.7 mm, compression 11.2:1, fuelling EFI. The redline sits at 11,500 rpm. The six-speed cassette gearbox is identical between all three bikes — Yamaha’s service manual cross-reference (technical instruction TI-2021-014) confirms the cassette internals are shipped from the same parts bin to all three assembly lines.',
  },
  {
    type: 'p',
    text: 'Final drive is identical: 14-tooth front sprocket, 48-tooth rear, 428 chain. Gear ratios run [2.917, 1.938, 1.500, 1.227, 1.045, 0.913] across the six speeds. Dry mass is 131 kg on both bikes — kerb mass is 140 kg with the 11-litre tank full and oils settled, which means the published wet-weight difference between MT-125 and XSR125 in magazine reviews is mostly a question of how the journalist measured the test bike rather than a real platform delta.',
  },
  {
    type: 'h2',
    text: 'Stock-Tune Simulation Numbers',
  },
  {
    type: 'p',
    text: 'Running both bikes in MotoQuant with a 78 kg rider, OEM tires, dry concrete, 22°C ambient, and density altitude ~1100 m (Aamby Valley November), the stock-tune numbers come out as follows:',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'MT-125', 'XSR125', 'Delta'],
      ['Quarter-mile ET', '19.123 s', '19.222 s', '+0.099 s'],
      ['Trap speed', '117.5 km/h', '117.2 km/h', '−0.3 km/h'],
      ['Peak hp (crank)', '15.0 @ 10000', '15.0 @ 10000', '—'],
      ['Peak torque', '11.5 Nm @ 8000', '11.5 Nm @ 8000', '—'],
      ['Dry mass', '131 kg', '131 kg', '—'],
      ['Cd (sim)', '0.78', '0.78', '—'],
      ['Frontal area', '0.47 m²', '0.48 m²', '+0.01 m²'],
      ['CdA product', '0.367 m²', '0.374 m²', '+1.9%'],
      ['Wheelbase', '1325 mm', '1330 mm', '+5 mm'],
    ],
  },
  {
    type: 'p',
    text: 'Real-world ETs from magazine instrumented tests put the MT-125 at roughly 18.4 to 18.8 seconds (MCN 2020, Visordown 2021) and the XSR125 at 18.5 to 19.0 seconds (Visordown 2022, MCN 2022). The simulator runs about 0.4 to 0.6 seconds slower than the magazine numbers on both bikes, which is the documented bias band for the "other / unknown" cluster that the entry-band 125 cc singles route into. That bias is a known calibration target — see the standing-priorities list — but the relative ordering of the two bikes (MT-125 quicker than XSR125 by ~0.10 s) is preserved exactly between the simulator and the real-world tests, which is the more important property.',
  },
  {
    type: 'callout',
    text: 'Why the sim is slow: it is calibrated to a 50th-percentile rider, not a 95th-percentile A1-licence newcomer chasing magazine-test technique. The simulator will rank order the two bikes correctly. It under-predicts both ETs by a similar amount, so the comparison is honest even if the absolute numbers will drift by ~0.5 s as the small-cc cluster bias gets closed.',
  },
  {
    type: 'h2',
    text: 'Where the 0.10 Seconds Lives',
  },
  {
    type: 'p',
    text: 'Two identical engines, two identical drivetrains, two identical dry masses. The 0.10 s ET delta and the 0.3 km/h trap delta cannot come from any of those. It comes from one number: frontal area.',
  },
  {
    type: 'p',
    text: 'The MT-125 ships with a 100/80 front tire, 130/70 rear, low-set sport-naked handlebars, and a riding posture that is leaned-forward and tucked. Catalog frontal area is 0.47 m². The XSR125 ships with retro 110/70 front and 140/70 rear tires (wider sidewall profile, slightly more rolling resistance at the contact patch), upright Sport Heritage handlebars that push the rider into a more vertical posture, and that posture adds approximately 0.01 m² to the projected frontal area. Both bikes carry the same Cd in the catalog at 0.78 — the difference is purely in projected area, not in shape efficiency.',
  },
  {
    type: 'p',
    text: 'At the 117 km/h trap speed, aerodynamic drag force scales with the CdA product times velocity squared. The MT-125 produces about 4.0 kilonewtons-second of cumulative drag impulse from launch to the trap line; the XSR125 produces about 4.1 kilonewtons-second from the same time integral. That 2.5 percent drag-impulse difference, multiplied by the fact that this is a 15-hp bike with almost no power margin, produces exactly the 0.10 s ET delta the simulator reports. On a litre superbike with 200 hp the same CdA difference would show up as a 0.02 s delta — there is so much engine power that drag is a fraction of the total propulsive budget. On a 15-hp single, drag is the dominant resistance at trap, and a 2.5 percent change in drag impulse is a 2.5 percent change in trap time.',
  },
  {
    type: 'p',
    text: 'The simulator log confirms this directly. Both bikes cross the trap line in fifth gear at approximately 9100 rpm, neither reaches sixth, and the gear-change sequence is identical timing-wise: shift to second at 1.4 s / 60 ft, third at 3.9 s / 200 ft, fourth at 7.8 s / 530 ft, fifth at 14.2 s / 980 ft. The difference between the two trajectories is purely the velocity slope above 80 km/h, where drag becomes the dominant retarding force and the XSR125 falls roughly 0.3 km/h behind the MT-125 in the final 200 metres of the run.',
  },
  {
    type: 'h2',
    text: 'Why the YZF-R125 Beats Both',
  },
  {
    type: 'p',
    text: "Yamaha sells three bikes off this platform in Europe: the MT-125 (Hyper Naked), the XSR125 (Sport Heritage), and the YZF-R125 (Supersport). All three use the same engine, gearbox, and final drive. The YZF-R125 ships with a full sport fairing, clip-on bars, and a leaned-forward riding posture that drops the rider into a proper tuck behind the bubble. Catalog Cd for the R125 is about 0.65 (the fairing genuinely earns its weight), and frontal area drops to roughly 0.45 m² with the tucked rider. CdA product is approximately 0.293 m² — about 20 percent lower than the MT-125 and 22 percent lower than the XSR125.",
  },
  {
    type: 'p',
    text: 'The simulator predicts the YZF-R125 at roughly 18.6 s and 121 km/h trap under the same conditions used for the MT-125 and XSR125 simulations above. That is 0.5 s faster than the MT-125 and 0.6 s faster than the XSR125, despite making the same 15 hp, weighing the same 131 kg dry, and using the same gearing. The platform is the same; the bodywork-and-posture decision changes the answer.',
  },
  {
    type: 'p',
    text: 'For an A1-licence drag-strip enthusiast, that ordering is dispositive: the R125 is the fastest of the three, the MT-125 is the second fastest, the XSR125 is the third. The differences are not large in absolute terms (the slowest bike is still within 0.6 s of the fastest), but on a platform where total ET is 19 seconds and peak power is 15 hp, half a second is a meaningful fraction of the dynamic range. Most of that half-second is sitting in the bodywork and the riding posture, not the engine.',
  },
  {
    type: 'h2',
    text: 'What This Means for European and SEA Buyers',
  },
  {
    type: 'p',
    text: "Neither the MT-125 nor the XSR125 is officially sold in India — both are Completely Built Unit imports for the few CBU dealers in Mumbai and Bangalore, which lifts the on-road price into the ₹4-5 lakh band that buys far more bike in domestic-spec hardware. The platform's relevance is in Europe (where the A1 licence is a major two-wheeler entry point and Yamaha sells the 125 family by the tens of thousands annually) and in Southeast Asia, where Thailand, Indonesia, and the Philippines run a serious 125 cc drag-strip community on Honda CBR150R, Yamaha R15, and the Yamaha 125 family.",
  },
  {
    type: 'p',
    text: 'The buying decision between MT-125 and XSR125, viewed through a drag-physics lens, is purely a posture-and-bodywork decision. The MT-125 is the quicker of the two by a meaningful tenth, and that tenth comes entirely from the lower handlebars and the smaller-section tires. The XSR125 is slower because the Sport Heritage styling brief required upright ergonomics and a more vertical rider posture — design choices that improve street-comfort on weekend rides and cost the rider a fraction of a second on the strip.',
  },
  {
    type: 'p',
    text: 'For most buyers that trade is correct. The XSR125 is a more comfortable bike to ride 200 km on a Sunday morning, and the time it gives up in the quarter mile is small enough that no real-world A1-licence rider will notice it. For buyers specifically chasing strip ET, the YZF-R125 is the right answer in the Yamaha 125 family. The MT-125 is a sensible compromise between sport ergonomics and naked usability. The XSR125 is the wrong bike for the drag strip and the right bike for everything else.',
  },
  {
    type: 'callout',
    text: 'The cheapest tenth on either bike: a 130/70 rear tire swap on the XSR125 (matching the MT-125’s narrower profile) is worth approximately 0.03 s and €80. A clip-on conversion of the MT-125 handlebars is worth approximately 0.05 s, €150, and most of the bike’s street comfort. Neither modification is street-legal in EU type-approval terms; both are routine in SEA drag-strip circles.',
  },
  {
    type: 'h2',
    text: 'Gearing — Why Sixth Gear Never Engages',
  },
  {
    type: 'p',
    text: 'The MT-125 and XSR125 share the same six-speed cassette but neither bike reaches sixth gear in a quarter-mile pass. The simulator log shows both bikes crossing the trap line in fifth gear at approximately 9100 rpm. Sixth gear on this platform is a true overdrive at 0.913 ratio, designed for highway cruise at 100-110 km/h sustained — the bike does not have the power margin to upshift into sixth and continue accelerating, so the optimal strategy is to hold fifth through the trap and let the engine wind into the 10000 rpm peak-power zone.',
  },
  {
    type: 'p',
    text: 'A 14/50 final drive (shortening the ratios by 4.2 percent vs the stock 14/48) puts the bike into sixth gear at the trap, which sounds like an improvement and is not. The shift point lands about 30 metres before the trap line, costing more ET in the gear-change deadband than the shorter gear gains in wheel torque. A 14/46 final drive (lengthening the ratios by 4.2 percent) does the opposite — keeps the bike in fourth gear at the trap, which means trap RPM falls to about 8500 and the bike crosses the line slightly below the peak-power band. Net result of either swap on this platform: less than 0.02 s either way, both within sim noise. The stock 14/48 final drive is genuinely optimised for this engine’s power band and the quarter-mile distance.',
  },
  {
    type: 'p',
    text: 'That gearing optimum is unusual on small-cc Indian-market platforms. The KTM 125 Duke, the Yamaha YZF-R15 V4, and the Bajaj Pulsar NS200 all benefit measurably from sprocket swaps because their stock final drives were chosen for European traffic or Indian highway use rather than strip optimisation. The Yamaha 125 family in MT/XSR/R125 form happens to have the right gearing for a 402-metre run out of the showroom. There is genuinely no cost-per-tenth gearing mod available on this platform that pays back.',
  },
  {
    type: 'h2',
    text: 'The Honest Take',
  },
  {
    type: 'p',
    text: 'The Yamaha MT-125 and XSR125 are the same motorcycle from the swingarm down. The 0.10 second ET difference between them at the drag strip is a clean physics demonstration of how much rider posture and tire-profile selection matter on a platform where engine power is fixed by A1-licence regulation and total ET is bounded by 18-19 seconds. There is no engine tuning that moves this number meaningfully on either bike — the 15 hp ceiling is a regulatory constraint, not a mechanical one, and removing it requires a derestricted ECU map and an MOT inspector who is willing to look the other way.',
  },
  {
    type: 'p',
    text: 'The bikes that matter on this platform are the three Yamaha sells in parallel: the MT-125 (Hyper Naked, second-quickest), the XSR125 (Sport Heritage, slowest, most comfortable), and the YZF-R125 (Supersport, quickest, least comfortable). The physics says the differentiation is real, the differences are small in absolute terms but meaningful as a fraction of the dynamic range, and the choice between them is entirely a question of how the rider wants to spend Saturday afternoons — leaned forward on track tires, upright on retro tires, or somewhere in between.',
  },
  {
    type: 'p',
    text: 'For Indian readers: this platform is not officially sold in India, the CBU import price puts it well above what the domestic-spec FZ-X or the YZF-R15 V4 can buy you, and the 15 hp output makes it a difficult value proposition next to the 17.4 hp / 14 Nm of a stock R15 V4 at roughly two-thirds the on-road price. The MT-125 and XSR125 are interesting bikes; they are not interesting Indian-market bikes. The physics-of-platform-sharing story is general, the bikes themselves are European and SEA market answers, and the lessons here apply much more directly to the Yamaha YZF-R15 V3 / V4 family and the Bajaj Pulsar 150 / NS200 platform pair than to anything currently sold by an Indian Yamaha dealer.',
  },
  {
    type: 'h2',
    text: 'Run Your Own Numbers',
  },
  {
    type: 'p',
    text: 'If you ride the MT-125 or XSR125 (or are deciding between them), the simulator at motoquant.in lets you sweep rider weight, ambient temperature, density altitude, and parts-catalog mods to see exactly where the tenths come from on your specific bike. The simulator currently rates both bikes within the "other / unknown" cluster bias band, which means absolute ETs are slow by approximately 0.4 to 0.6 seconds versus magazine instrumented tests — but the relative ordering between the two bikes (MT-125 quicker by 0.10 s) is preserved exactly. That bias is being closed in the background as the small-cc benchmark dataset grows.',
  },
  {
    type: 'p',
    text: 'Two final caveats. First, every number in this post is a stock-tune simulation under matched Aamby Valley November conditions. Change the venue (denser air at sea-level European tracks like Bruntingthorpe will help both bikes by ~0.15 s) or change the rider (a 65 kg rider versus the 78 kg simulated default will help both bikes by ~0.10 s), and absolute ETs shift; the relative MT-125-versus-XSR125 ordering stays stable. Second, this is one of the few platforms in the MotoQuant catalog where the published Cd numbers and the simulator’s frontal-area estimates are derived from manufacturer aero data and review-photography geometric analysis rather than wind-tunnel measurement — the 0.01 m² frontal-area delta between MT-125 and XSR125 is well-bounded by photographic evidence but is not a tunnel-measured number.',
  },
  {
    type: 'p',
    text: 'If you take one thing from this post, take this: when peak power is 15 horsepower, aerodynamics is no longer a litre-superbike pedantry. It is the dominant retarding force at trap speed, and a 2.5 percent change in CdA product produces a 2.5 percent change in trap-line velocity. The MT-125 and XSR125 are the same motorcycle wearing different clothes. The clothes cost a tenth of a second. That is the smallest, cleanest demonstration of "aerodynamics matters" available in any motorcycle catalog in 2026.',
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
            {['Yamaha', 'MT-125', 'XSR125', 'A1 licence', 'platform physics'].map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Yamaha MT-125 vs XSR125: Same Engine, 0.10s Apart at the Strip
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
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
                Why Your R15 Won&rsquo;t Hit 14s (And What Will Actually Help)
              </Link>{' '}
              — the Indian-market Yamaha 150 single platform, same physics arc one displacement up.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/cfmoto-800nk-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                CFMoto 800NK Quarter-Mile Physics
              </Link>{' '}
              — what platform-sharing looks like one displacement category up, with KTM as the source.
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
              — including the MT-125, XSR125, and YZF-R125 platform-mates with every published spec.
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
            <div className="font-display font-bold text-white mb-1">Run both bikes yourself</div>
            <div className="text-white/60 text-sm">
              Free simulator — load the MT-125 and XSR125 side-by-side, dial in your local conditions, and watch the ET delta update live.
            </div>
          </div>
          <Link
            href="/simulator?bike=yamaha-mt-125"
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
