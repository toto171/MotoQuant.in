import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'harley-nightster-rh975-quarter-mile-physics';
const TITLE = 'Harley Nightster RH975: Revolution Max Quarter-Mile Physics';
const DESCRIPTION =
  'Harley-Davidson Nightster RH975 quarter-mile physics deep-dive. MotoQuant simulates the 975cc Revolution Max 975T V-twin at 12.45s; Cycle World clocked 11.99s at 110.4 mph. Honest breakdown of the gap — and why a 90 hp Harley keeps up with 600cc middleweights. Indian context included.';

export const metadata = {
  title: 'Harley Nightster RH975 Quarter-Mile Physics — MotoQuant',
  description: DESCRIPTION,
  keywords: [
    'harley davidson nightster rh975 quarter mile',
    'nightster rh975 drag time',
    'nightster 975 quarter mile india',
    'harley nightster 975 0-100',
    'revolution max 975t drag',
    'nightster vs sportster s drag race',
    'nightster rh975 vs street triple',
    'harley davidson india drag racing',
    'revolution max 975 quarter mile time',
    'nightster india price quarter mile',
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
    text: 'Cycle World\'s 2022 instrumented test put the Harley-Davidson Nightster RH975 through the quarter mile in 11.99 seconds at 110.4 mph. That makes a stock Nightster quicker than a Triumph Street Triple 765 R on the drag strip — and within tenths of a Kawasaki Ninja 650. The Revolution Max 975T V-twin is not the sluggish cruiser motor most people assume it is. MotoQuant simulates the Nightster at 12.45 seconds, a 0.46-second gap from the Cycle World benchmark, which sits inside the cruiser cluster\'s documented bias band. Here is what the physics actually says about why a 90 hp belt-drive Harley runs an 11.x.',
  },
  {
    type: 'h2',
    text: 'The Revolution Max 975T: A Different Kind of V-Twin',
  },
  {
    type: 'p',
    text: 'Harley-Davidson introduced the Revolution Max platform in 2021 with the Pan America adventure bike. The Nightster arrived in 2022 as the first dedicated street model using the smaller 975cc version of the engine. The architecture is a significant departure from the Milwaukee-Eight and Twin Cam V-twins that built Harley\'s reputation: the Revolution Max 975T is a liquid-cooled, DOHC 4-valve-per-cylinder 60° V-twin with variable valve timing and a counterbalancer shaft. It looks more like a Ducati V-twin on paper than a traditional Harley pushrod engine.',
  },
  {
    type: 'p',
    text: 'Peak power is 90 hp at 7,500 rpm. Peak torque is 95 Nm at 5,000 rpm. The torque peak lands 2,500 rpm earlier than the power peak — a broad, accessible curve designed for real-world riding, not a narrow RPM spike. The 60° vee angle and counterbalancer produce a much smoother idle than the traditional 45° big V-twins, and the variable valve timing extends the usable power band across a wider RPM range than a fixed-cam equivalent would allow.',
  },
  {
    type: 'p',
    text: 'The final drive is belt — a 24-tooth front pulley and a 68-tooth rear, giving an overall drive ratio that sits on the tall side for a drag application. Belt drive eliminates chain stretch and sprocket wear but means a Nightster owner cannot simply drop a tooth on the front pulley the way they would on a chain-drive bike. The drivetrain geometry is fixed at the belt ratio; the only available gearing change is the rear pulley, which requires more work and cost than a sprocket swap.',
  },
  {
    type: 'h2',
    text: 'Spec Card: Nightster RH975 vs the 600cc Middleweight Benchmark',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'Nightster RH975 (2022+)', 'Triumph Street Triple 765 R (2023)', 'Kawasaki Ninja 650 (2023)'],
      ['Displacement', '975 cc', '765 cc', '649 cc'],
      ['Engine type', 'LC DOHC 60° V-twin', 'LC DOHC inline-triple', 'LC DOHC parallel-twin'],
      ['Peak power', '90 hp @ 7,500 rpm', '118 hp @ 11,700 rpm', '68 hp @ 8,000 rpm'],
      ['Peak torque', '95 Nm @ 5,000 rpm', '79 Nm @ 9,350 rpm', '64 Nm @ 6,700 rpm'],
      ['Dry mass', '212 kg', '166 kg', '193 kg'],
      ['Gears', '6-speed', '6-speed', '6-speed'],
      ['Final drive', 'Belt 24F/68R', 'Chain 17F/41R 520', 'Chain 14F/43R 520'],
      ['Cd', '0.88 (upright cruiser)', '0.72 (naked sport)', '0.80 (naked sport)'],
      ['Frontal area', '0.52 m²', '0.44 m²', '0.46 m²'],
      ['Cycle World / MCN ET', '11.99 s @ 110.4 mph', '10.9 s @ ~132 mph', '~13.4 s'],
      ['MotoQuant sim ET', '12.45 s @ 184.7 km/h', '10.74 s @ 213 km/h', 'N/A in this post'],
    ],
  },
  {
    type: 'p',
    text: 'The comparison column that matters is the Street Triple 765 R. The Triumph makes 28 more horsepower, weighs 46 kg less, and runs a sport-naked aero package with a significantly smaller frontal area. It costs more in most markets. And it beats the Nightster by roughly 1.7-1.9 seconds of ET. The Nightster, with 67 percent of the Triumph\'s peak power and 128 percent of its mass, runs within two seconds of a motorcycle that most riders would consider genuinely quick. That is the Revolution Max 975T\'s case for being taken seriously at the strip.',
  },
  {
    type: 'h2',
    text: 'Sim vs Cycle World: The 0.46-Second Gap',
  },
  {
    type: 'p',
    text: 'MotoQuant simulates the stock Nightster RH975 at 12.450 seconds and 184.7 km/h (114.7 mph) trap. Cycle World clocked 11.99 seconds at 110.4 mph (177.6 km/h) in their 2022 instrumented test, run under California conditions. The gap is 0.46 seconds of ET and 7.1 km/h (4.3 mph) of trap speed.',
  },
  {
    type: 'callout',
    text: 'The trap speed inversion — MotoQuant simulates a higher trap speed (184.7 km/h) than Cycle World recorded (177.6 km/h) while also simulating a slower ET (12.45 s vs 11.99 s) — is a known signature of the cruiser cluster\'s bias pattern. It means the simulator is getting the bike to the 402 m mark on a slower trajectory overall, but is reaching a similar terminal velocity. The most likely cause: the launch and clutch engagement phase is more conservative in the model than Cycle World\'s instrumented rider achieved in their test. Cycle World tests are done with professional riders performing optimal launches. The simulator uses a stock launch-RPM profile without manual optimisation.',
  },
  {
    type: 'p',
    text: 'For context: the MotoQuant cruiser-1300+ cluster — which the Nightster sits adjacent to as a large V-twin — has a documented mean absolute error of 0.407 seconds and a positive bias of 0.407 seconds (simulator runs slower than reality). The Nightster\'s 0.46-second gap is within that range. This is not a physics error specific to the Nightster; it reflects the fundamental challenge of modelling the launch phase on heavy bikes with belt drives and tall final gearing.',
  },
  {
    type: 'p',
    text: 'The full split breakdown from MotoQuant: 60-foot at 2.339 seconds, 330-foot at 5.589 seconds, 1/8-mile at 8.212 seconds and 153.7 km/h, 1,000-foot at 10.494 seconds. A real Nightster with an optimal launch typically runs the 60-foot in roughly 2.05-2.10 seconds, which explains most of the gap — the simulator\'s modelled clutch engagement is conservative, losing about 0.25 seconds in the first 60 feet.',
  },
  {
    type: 'h2',
    text: 'Why the Nightster Runs an 11.x: Physics of the V-Twin',
  },
  {
    type: 'p',
    text: 'Three factors make the Nightster faster than its paper power-to-weight ratio suggests.',
  },
  {
    type: 'p',
    text: 'First: the torque curve shape. Peak torque arrives at 5,000 rpm — in most riding situations the Nightster is already well into its power band before first gear becomes power-limited. In a quarter-mile run, a bike that produces strong torque at 4,000-6,000 rpm makes better use of its power during the gearing-limited early phase of the run than a high-revving engine that only produces peak power at 10,000 rpm. The Nightster is not traction-limited at launch the way a 100+ hp sport bike is — it goes relatively cleanly from launch RPM to redline in first gear without significant wheel slip on dry pavement.',
  },
  {
    type: 'p',
    text: 'Second: displacement advantage. 975 cc produces torque more easily than 765 cc. The Street Triple 765 R needs to rev to 9,350 rpm to match the Nightster\'s 95 Nm peak torque. The Nightster is at that torque level from roughly 3,500 rpm upward. In a drag context, a wider torque plateau means the bike stays in a high-torque state across a larger range of gear ratios and engine speeds. The gearing does not need to be as aggressively short to keep the engine in its useful range.',
  },
  {
    type: 'p',
    text: 'Third: the weight, while large in absolute terms, is not as damaging to ET as it appears. At 212 kg dry, the Nightster\'s power-to-weight ratio is approximately 68 hp per tonne (using 90 hp and 132 kg total — bike dry mass plus approximate fuel and a 70 kg rider). The Street Triple 765 R at 166 kg dry runs approximately 115 hp per tonne on the same calculation. The Triumph\'s massive advantage in power-to-weight is the reason it beats the Nightster by 1.7-1.9 seconds — not the Nightster\'s weight in isolation. A bike running 11.99 seconds with 68 hp per tonne is physically well-sorted.',
  },
  {
    type: 'h2',
    text: 'Belt Drive at the Strip: What It Costs You',
  },
  {
    type: 'p',
    text: 'Belt drive has a real power loss penalty versus a well-maintained chain drive. Harley-Davidson\'s belt system runs at roughly 2-3 percent drivetrain loss versus a typical 1.5-2 percent for a chain drive in good condition. At 90 hp crank output, the difference is approximately 0.5-1.5 hp at the wheel — a small but measurable disadvantage.',
  },
  {
    type: 'p',
    text: 'The larger issue for drag racing is the fixed gearing. A chain-drive bike owner can change sprockets for ₹900-3,000 and gain 0.15-0.25 seconds of ET by optimising the drive ratio for the quarter mile. The Nightster\'s belt system requires either a different rear pulley (which is a larger job, typically ₹8,000-15,000 in India including labour) or accepting the stock gearing as fixed. The stock 24F/68R gives an overall first-gear ratio that is appropriate for street riding — moderate, not aggressive — and the bike runs through all six gears before reaching the 402 m mark.',
  },
  {
    type: 'p',
    text: 'In MotoQuant\'s split data, the Nightster uses all six gears by the time it crosses the quarter-mile. A well-set-up drag bike at this power level would ideally be in 3rd or 4th gear at the 402 m mark, maximising power delivery per gear. The Nightster\'s tall gearing forces it through the cassette, losing engine efficiency at each shift transition. This is the primary mechanical reason MotoQuant\'s sim ET is 0.46 seconds slower than the Cycle World benchmark — the model\'s launch RPM and clutch engagement are set conservatively, but the gearing analysis is correct.',
  },
  {
    type: 'h2',
    text: 'What Mods Actually Move the Needle on a Nightster',
  },
  {
    type: 'p',
    text: 'The Indian Nightster market is thin for dedicated drag parts — the bike is priced at approximately ₹15.5-16.5 lakh ex-showroom in India and attracts buyers who are primarily interested in street and touring use rather than strip performance. The parts ecosystem reflects this. There are realistic options, but the cost-per-tenth ladder looks different from a Pulsar NS200 or RC 390.',
  },
  {
    type: 'table',
    rows: [
      ['Mod', 'Estimated ΔET', 'Approx. Indian price', '₹ per tenth'],
      ['Slip-on exhaust (Vance & Hines / Cobra)', '~0.08 s', '₹35,000–55,000', '₹4.4 lakh–6.9 lakh per tenth'],
      ['ECU re-flash (Dynojet PCV + Autotune)', '~0.10 s', '₹22,500–38,000', '₹2.25 lakh–3.8 lakh per tenth'],
      ['Rear pulley swap (shorter ratio, custom)', '~0.18 s', '₹12,000–20,000 (parts + labour)', '₹67,000–1.1 lakh per tenth'],
      ['Rider mass reduction: −10 kg', '~0.06 s', '—', '—'],
      ['Sport tire (front: 100/80ZR17, rear: 150/70ZR17)', '~0.07 s', '₹8,000–14,000', '₹1.1 lakh–2.0 lakh per tenth'],
    ],
  },
  {
    type: 'p',
    text: 'The cost-per-tenth numbers for the Nightster are substantially worse than for Indian commuter bikes or even most 600cc middleweights. This is not a failure of the parts — the ECU flash and exhaust are genuine improvements. It is a consequence of the Nightster\'s starting point: at 11.99-12.45 seconds stock, the absolute gains from bolt-on mods are smaller in percentage terms than on a 14-17 second commuter bike, and the parts are priced for the premium cruiser segment rather than the performance segment.',
  },
  {
    type: 'p',
    text: 'The rear pulley swap is the highest-ROI drag-specific modification on the Nightster platform. Dropping the rear pulley from 68T to 62T shortens the overall gearing by approximately 9 percent, which keeps the engine closer to its peak torque band through a larger portion of each gear span. MotoQuant\'s model suggests this would recover roughly 0.15-0.20 seconds — enough to put a well-launched Nightster solidly into the 11.7-11.8 second range. Custom rear pulleys are available through Harley-Davidson tuning specialists in Bangalore and Mumbai; expect to source the pulley from the US market at approximately ₹12,000-15,000 and add ₹3,000-5,000 for belt-length matching and fitting.',
  },
  {
    type: 'callout',
    text: 'The Nightster\'s belt drive is the single biggest structural constraint for drag tuning. Every other performance motorcycle in its price range offers a chain drive that allows ₹900-3,000 sprocket swaps for rapid gearing experiments. The Nightster requires a pulley swap that costs 10-20x more and is not reversible in an afternoon. If your primary goal is strip performance, this is the tradeoff you accept with the Harley platform.',
  },
  {
    type: 'h2',
    text: 'Nightster vs Sportster S: The Natural Comparison',
  },
  {
    type: 'p',
    text: 'Harley-Davidson sells the Sportster S RH1250S alongside the Nightster using the larger Revolution Max 1250T engine — 121 hp, 127 Nm, and the same belt-drive architecture. The Sportster S weighs approximately 228 kg wet, about 10-15 kg more than the Nightster in comparable trim. The power-to-weight ratio is roughly 83 hp per tonne for the Sportster S versus the Nightster\'s 68 hp per tonne.',
  },
  {
    type: 'p',
    text: 'Cycle World tested the Sportster S in 2021 and posted a 12.05 second quarter mile — almost exactly the same as the Nightster\'s 11.99 seconds. The Sportster S\'s 31 additional horsepower and 32 Nm of extra torque are partially offset by its additional mass and its taller overall gearing. The Nightster, despite its smaller engine, essentially matches the Sportster S at the strip under controlled conditions.',
  },
  {
    type: 'p',
    text: 'This is a counterintuitive result worth dwelling on. The Nightster is roughly ₹3-4 lakh less expensive in India, lighter, narrower, and easier to ride in traffic. At the drag strip it posts the same time as the flagship model in its family. The Revolution Max 975T engine is that well-suited to the bike\'s weight and gearing — which tells you something about the mechanical efficiency of the smaller engine package versus the 1250T in the heavier Sportster S chassis.',
  },
  {
    type: 'p',
    text: 'A full Nightster vs Sportster S physics breakdown — including the launch characteristics of each engine, the torque curve comparison at matched RPM, and the gearing optimisation path for both — is covered in a separate post. The short version: if strip performance is the primary criterion, the Nightster is the better pick of the two in stock form.',
  },
  {
    type: 'h2',
    text: 'The Indian Market Context',
  },
  {
    type: 'p',
    text: 'The Nightster arrived in India in 2022 at approximately ₹15.5 lakh ex-showroom, positioning it above the Royal Enfield Super Meteor 650 and below the Triumph Bonneville T120. In the Indian performance context, that price buys significantly more quarter-mile performance from a KTM 890 Duke R (11.07 s, ₹11-12 lakh via grey market) or a BMW S 1000 R (sub-10 s, ₹22 lakh). The Nightster is not purchased in India because it is the fastest motorcycle at any price point. It is purchased because of the combination of style, sound, riding position, and the Revolution Max\'s mechanical character — all of which are real.',
  },
  {
    type: 'p',
    text: 'For an Indian drag strip context: the Nightster will comfortably beat any stock Indian 650cc twin (RE Continental GT 650 runs approximately 14.1 seconds, RE Interceptor 650 similar), any 400cc Indian bike (RC 390 at approximately 13.5 seconds), and most stock 600cc sport bikes from the used market. It competes directly with stock Kawasaki Ninja 650 (approximately 13.4 seconds), MT-07 class bikes, and the lower end of the litre-class naked segment.',
  },
  {
    type: 'p',
    text: 'At an Aamby Valley strip meet, a stock Nightster in the hands of a competent rider running consistent launches is going to beat most of the Indian bikes in the paddock. That is a genuine surprise to most observers who associate Harley-Davidson with slow, heavy touring bikes. The Revolution Max 975T platform changed that.',
  },
  {
    type: 'h2',
    text: 'Simulate It Yourself',
  },
  {
    type: 'p',
    text: 'The MotoQuant sim result of 12.45 seconds is the physics prediction under conservative launch conditions and stock tune. The Cycle World 11.99 seconds is the instrumented benchmark with a professional rider performing optimal launches at sea-level California conditions. The 0.46-second gap is almost entirely accounted for by launch optimisation — the Nightster\'s belt drive and V-twin character make it tractable to ride aggressively from the line without significant wheel spin, so a competent rider can consistently improve on the sim\'s conservative launch model.',
  },
  {
    type: 'p',
    text: 'If you own a Nightster and have a Dragy GPS timer, the MotoQuant calibrator at motoquant.in can fit the simulator\'s predictions to your actual timeslip data. This tightens the prediction band from the cluster\'s ±0.4 second band down to approximately ±0.15 seconds and generates an accurate mod-by-mod ROI table for your specific bike and launch style. The calibrator is especially useful for the Nightster because the belt-drive gearing constraint means the simulation\'s gear-ratio assumptions are exact — there is no sprocket variation to account for.',
  },
  {
    type: 'p',
    text: 'The simulator at motoquant.in has the Nightster RH975 pre-loaded with full spec including the Revolution Max 975T torque curve, 24F/68R belt gearing, and 212 kg dry mass. You can sweep venue conditions (Aamby Valley November at 1,100 m density altitude versus MMRT Chennai at near sea level and 30°C), rider weight, and the limited mod catalog to model what a rear pulley swap or ECU flash actually buys in seconds on your home strip.',
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
          <div className="flex flex-wrap gap-2 mb-6">
            {['Harley-Davidson', 'Nightster RH975', 'Revolution Max', 'cruiser', 'V-twin', 'physics'].map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Harley Nightster RH975: Revolution Max Quarter-Mile Physics
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
            25 May 2026 · 11 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        <div className="max-w-2xl mx-auto mt-16 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Simulate the Nightster RH975</div>
            <div className="text-white/60 text-sm">Load the Nightster at Aamby Valley or MMRT Chennai, sweep rider weight and conditions, and model the rear pulley swap or ECU flash before spending ₹15,000–55,000 on mods.</div>
          </div>
          <Link
            href="/simulator"
            className="shrink-0 px-5 py-2.5 bg-brand-orange text-black font-display font-bold rounded-lg text-sm hover:bg-brand-orangeLight transition-colors"
          >
            Run sim →
          </Link>
        </div>

        <div className="max-w-2xl mx-auto mt-16">
          <h3 className="font-display font-bold text-lg text-white mb-4">Related reading</h3>
          <ul className="text-sm text-white/70 space-y-2">
            <li>
              ·{' '}
              <Link href="/blog/triumph-street-triple-765r-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                Triumph Street Triple 765 R Quarter-Mile Physics
              </Link>{' '}
              — the Nightster's nearest competitor in the 11-12 second range from a completely different architecture. 118 hp inline-three at ₹10.67 lakh, beats the Nightster by ~1.75 s, but costs less.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/kawasaki-z900rs-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                Kawasaki Z900RS Quarter-Mile Physics
              </Link>{' '}
              — another premium naked in the 11-second range: 948cc inline-four, retro styling, 11.18 s sim. The Z900RS and Nightster are natural strip rivals at similar Indian CBU price points.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-the-motoquant-physics-engine-works" className="text-brand-accent hover:text-brand-orange transition-colors">
                How the MotoQuant Physics Engine Works
              </Link>{' '}
              — the full methodology behind the 12.45 s prediction: clutch model, belt-drive efficiency, V-twin torque curve synthesis, and why the cruiser cluster has a +0.4 s bias.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/the-physics-of-a-perfect-launch" className="text-brand-accent hover:text-brand-orange transition-colors">
                The Physics of a Perfect Launch
              </Link>{' '}
              — most of the Nightster's 0.46 s gap to Cycle World's benchmark lives in the first 60 feet. Clutch engagement RPM, weight transfer, and slip ratio on a 212 kg V-twin.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>{' '}
              — Harley-Davidson Nightster RH975, Sportster S RH1250S, and 350+ other bikes with full spec sheets and OEM tire fitments.
            </li>
            <li>
              ·{' '}
              <Link href="/pricing" className="text-brand-accent hover:text-brand-orange transition-colors">
                Pricing
              </Link>{' '}
              — free tier covers stock-tune sims on the Nightster; Pro adds the Dragy calibration, full mod-ROI engine, and multi-run statistical analysis for timeslip matching.
            </li>
          </ul>
        </div>
      </article>

      <SiteFooter />
    </div>
  );
}
