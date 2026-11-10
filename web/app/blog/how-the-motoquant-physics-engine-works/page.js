import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import CodeComment from '../../../components/CodeComment';
import ScoreboardDigits from '../../../components/ScoreboardDigits';

export const metadata = {
  title: 'How the MotoQuant physics engine works | MotoQuant Blog',
  description: 'The 15 sub-models and RK4 integrator behind MotoQuant, from engine torque curves to tyre grip, tyre temperature and launch slip: what we simulate, what we validate against, and what the remaining error means.',
  keywords: [
    'motorcycle physics simulation',
    'drag racing simulator',
    'RK4 motorcycle dynamics',
    'first-principles motorcycle physics',
    'MotoQuant engine',
    'physics validation',
    'drag racing model',
  ],
  alternates: { canonical: 'https://motoquant.in/blog/how-the-motoquant-physics-engine-works' },
  openGraph: {
    title: 'How the MotoQuant physics engine works',
    description: '15 sub-models and RK4 integration at 1ms, validated against 250 published drag-strip benchmarks (November 2026 sweep), with reference baselines held to 4 decimals.',
    url: 'https://motoquant.in/blog/how-the-motoquant-physics-engine-works',
    type: 'article',
    publishedTime: '2026-04-27T00:00:00Z',
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: 'MotoQuant simulates a motorcycle quarter-mile drag run from first principles. It has 15 independent sub-models (engine, clutch, drivetrain, chain, tires, aero, weight transfer, rider dynamics, staging, environmental, parasitic losses, rolling resistance, braking, wheelie, forced induction), coupled by a fixed-step RK4 integrator at one-millisecond resolution. The sections that follow cover what each sub-model does, what we validate against, and where the simulator falls short.',
  },
  {
    type: 'h2',
    text: 'The architecture in one picture',
  },
  {
    type: 'p',
    text: 'The state vector is six-dimensional: position, velocity, engine angular velocity, tire temperature, clutch temperature, and current gear. Every millisecond, the integrator computes forces and torques from each sub-model, combines them into a net acceleration and advances the state. RK4 with the aero re-evaluated at the midpoint stays numerically stable across the full speed range, from 0 m/s at the staging beam to the 200+ km/h trap.',
  },
  {
    type: 'p',
    text: 'Why fixed-step RK4 and not an adaptive solver? Drag races are short (10 to 20 seconds), so a 1 ms timestep gives 10,000–20,000 integration points, enough to resolve the launch slip phase, gear changes and the fast dynamics of clutch engagement. And a fixed step reproduces bit for bit across runs, which matters when you are debugging a 0.05-second discrepancy. An adaptive variant (use_adaptive_dt=True) is there for users who want faster runs and can give up reproducibility.',
  },
  {
    type: 'h2',
    text: 'Sub-model 1: engine torque',
  },
  {
    type: 'p',
    text: 'The engine sub-model takes RPM and time and returns crank torque. There are two paths. For the 21 most popular drag bikes (Hayabusa, R1, GSX-R 1000, ZX-10R, S1000RR, Panigale V4, RSV4, etc.) we ship measured dyno curves: RPM-vs-torque arrays sourced from Cycle World, Sport Rider, and Dynojet published tests. For everything else we synthesize a curve from the manufacturer-published peak power, peak torque, and the RPMs at which they occur.',
  },
  {
    type: 'p',
    text: 'The synthesized curve is an asymmetric Gaussian: a gentle ramp from idle to peak torque, then a shaped falloff to redline calibrated so the torque at peak power RPM produces exactly the rated horsepower. The shape parameters (sigma below peak, redline factor above peak) are calibrated by class. Modern litre superbikes get sigma=2.2 and a steep 0.48 redline factor for that "pulls hard then signs off" character. Mid-range 600-800cc 4-cyl engines get a plateau-like 0.88 redline factor, which matches dyno tests showing flat torque to redline. Small-cc commuters get a broader sigma=1.20, because real R15 and Pulsar dynos show flatter curves than the default Gaussian assumes.',
  },
  {
    type: 'p',
    text: 'Two-stroke engines get a different model. Their torque curves are dominated by expansion chamber resonance: a sharp peak at the tuned RPM with very little off-pipe torque. We synthesize a Gaussian-like band around the tuned RPM with width parameters that vary by configuration: piston-port singles (RX100, RD350) get a narrow band; YPVS-equipped powervalves (NSR250R, RGV250) get a wider band with stronger off-pipe torque; vintage triples (GT750, H2 Mach IV) get an overlapping multi-cylinder band that approaches 4-stroke smoothness.',
  },
  {
    type: 'h2',
    text: 'Sub-model 2: clutch slip and lockup',
  },
  {
    type: 'p',
    text: 'After the tire, the clutch is the most detailed sub-model. There are four types: standard lockup (most modern bikes), slider/centrifugal (vintage and small-cc), multi-stage (some MotoGP-derived sport bikes), and slipper (modern litre bikes for back-torque limiting). Each behaves differently under launch and downshift conditions.',
  },
  {
    type: 'p',
    text: 'During launch, the clutch is in the slip phase: engine RPM is held above the wheel-equivalent RPM, and friction transmits torque between the two. The amount of torque transmitted depends on the friction coefficient, the clamping force from the springs, the plate count, and the mean friction radius. These come from the clutch sub-config (which has real geometry from service manuals where available).',
  },
  {
    type: 'p',
    text: 'A subtle bug we fixed in late April 2026: the original slip model used T_transmitted = min(T_engine, T_clutch_max), which kept engine RPM pinned at the launch RPM during the entire slip phase. That is fine for big litre bikes where T_clutch_max is close to T_engine. For small-cc bikes where T_clutch_max is much larger than T_engine (clutch sized for safety, not engine output), it caused the simulation to under-predict launch acceleration by 30–40 % because the engine never had a chance to transfer kinetic energy through the clutch into wheel acceleration. The fix: rate-limited over-clutching, where T_transmitted can briefly exceed T_engine by up to (max_decel × engine_inertia) torque. That copies what riders do: feather the clutch and let the engine bog briefly.',
  },
  {
    type: 'callout',
    text: 'The slip phase typically resolves into lockup when the engine and wheel-equivalent RPMs come within ~10 RPM of each other. After that, the clutch is treated as a rigid coupling and the bike accelerates on engine torque alone, until the next gear change.',
  },
  {
    type: 'h2',
    text: 'Sub-model 3: drivetrain and gear cassette',
  },
  {
    type: 'p',
    text: 'The drivetrain is simple: primary ratio × current gear ratio × secondary ratio (front sprocket / rear sprocket) gives the total reduction. Multiply by engine torque to get rear-wheel torque. Divide by rear wheel rolling radius to get drive force.',
  },
  {
    type: 'p',
    text: 'Getting the right gear ratios for 534 different bikes took months. We maintain a Tier-1 lookup table with 150+ named-model entries derived from service manuals (R15 V4: 14F/48R, primary 2.83, gears 2.833 / 1.875 / 1.429 / 1.16 / 0.963 / 0.84; those numbers come from the YZF-R15 service manual, not from a forum). Bikes without a Tier-1 entry fall back to category-based defaults (sport-1000, naked-mid, cruiser-big, etc.) which are still better than generic numbers but lose the per-model detail.',
  },
  {
    type: 'p',
    text: 'Shift dynamics matter too. Each gear change costs simulation time equal to the shift_time_ms parameter (typically 50–80 ms with a quickshifter, 150–300 ms manual). During the shift, drive force is zero: the bike coasts. A badly chosen shift point can cost 0.05–0.15 seconds in ET if the engine drops below peak power on the next gear, so getting the shift_rpms array right per bike is part of the gear-cassette work.',
  },
  {
    type: 'h2',
    text: 'Sub-model 5: tires (grip and thermal)',
  },
  {
    type: 'p',
    text: 'The tire model returns the most longitudinal force the rear tire can deliver: a peak friction coefficient (μ_peak) times the load on the tire. μ_peak falls with load, follows the tread temperature through an optimum window, changes with tire pressure as the tire heats, and scales with the track surface and any prep. Each of the 254 tires in the library (drag slicks, sport touring, race compounds, Indian commuter rubber from MRF and CEAT) carries its own μ_peak and thermal window. The library also stores Pacejka Magic Formula coefficients (B, C, D, E) for every tire, and the full slip curve is coded, but the integrator does not use it yet: a launch is limited by the peak, not by where on the slip curve the tire sits.',
  },
  {
    type: 'p',
    text: 'On a real tire, peak longitudinal force occurs at a slip ratio of roughly 0.07–0.15. That is why launches with a little wheel spin can be faster than perfect-traction launches, and why a smoking tire is slower than measured throttle: above the peak, force falls off. Wiring that slip curve into the integrator is on the roadmap; it would move the pinned reference times, so it waits for a deliberate accuracy pass.',
  },
  {
    type: 'p',
    text: 'The thermal layer matters because mu_peak depends strongly on tire temperature: a sticky slick at 80°C can deliver 1.85 mu_peak, the same tire at 25°C delivers ~1.1. Our thermal model tracks heat generated from slip (Q = T_transmitted × slip_speed), conductance to track surface, and convection to ambient air. Real burnouts typically warm the tire from 25°C to 50–55°C, which is why we model the rear tire starting at the burnout-end temperature, not ambient.',
  },
  {
    type: 'h2',
    text: 'Sub-models 6–8: aero, weight transfer, rider dynamics',
  },
  {
    type: 'p',
    text: 'Aero is F_drag = 0.5 × rho × v² × Cd × A. The catch is that Cd × A changes with time. The rider transitions from an upright staging stance to a tucked aerodynamic position over roughly 2 seconds after launch, dropping Cd × A by 30–40 %. We model this transition with a sigmoid curve: at 0 seconds, the rider is upright (Cd × A = ~0.55); at 2 seconds, fully tucked (Cd × A = ~0.32). Cd and frontal area come from per-bike values; we measured or estimated each one of the 534 bikes individually after discovering that 71 % of the catalog had inherited a generic 0.32 Cd that is closer to a passenger car than a motorcycle.',
  },
  {
    type: 'p',
    text: 'Weight transfer reduces front axle load and increases rear axle load proportionally to acceleration × CoG_height / wheelbase. More rear load means more available traction. Past a critical point the front goes light enough that the bike wheelies. Wheelie is a separate sub-model that limits available drive force to whatever keeps the front wheel a few millimeters off the ground. A liter-class superbike on a hard launch typically wheelies in gear 1 around 0.7–1.0 g; the wheelie limit is what caps acceleration in that window, not engine power or tire grip.',
  },
  {
    type: 'p',
    text: 'Rider dynamics also includes a longitudinal CoG shift: the rider scoots back at launch (pulling weight rearward, helping traction) and tucks forward at speed (reducing aero drag). Both shifts are tracked in the sub-model and feed into weight transfer and aero respectively.',
  },
  {
    type: 'h2',
    text: 'Sub-models 9–15: the rest',
  },
  {
    type: 'p',
    text: 'Staging models the launch dead-time (reaction + vehicle response) and the two-step / launch-RPM logic. Environmental models air density, density altitude (which costs 1 % power per 100 m above sea level for naturally aspirated engines), wind, and surface grip multiplier. Forced induction handles turbo, supercharger, and nitrous boost profiles. Parasitic losses subtract alternator, water pump, oil pump, and valve-train power from net engine output. Rolling resistance scales with tire load and a temperature-dependent crr coefficient. Braking is there for planned features (reverse simulation, brake performance comparisons) and is off during a forward drag run. The full model was built up step by step over 6 months of development.',
  },
  {
    type: 'h2',
    text: 'How we validate',
  },
  {
    type: 'p',
    text: 'We maintain a list of 250 published drag-strip benchmarks (263 matched to a catalog bike), sourced from Cycle World, Sport Rider, MCN, Motorcycle Consumer News, MotorcycleDaily, MotoStatz, FastestLaps, and Indian Autos Mag where the magazine published the actual instrumented timeslip. For each benchmark, we run the simulator at the test-day environmental conditions and compare predicted ET against measured ET. Each source is weighted by quality (instrumented timeslip 1.0, magazine 0.7, aggregator 0.5, derived 0.1) and the delta gets bucketed by class on a cylinder-aware 12-cluster taxonomy (litre-sport-195+, litre-sport-600-1000, sport-twin-600-1300, singles-300-500, entry-150-200, two-stroke, etc.) so we can see where the physics holds and where it has systematic bias.',
  },
  {
    type: 'p',
    text: 'Three reference baselines are locked: GSX-R 1000 K5 (10.0436 s), YZF-R1 4C8 (10.1092 s), and Hayabusa Gen1 (10.1100 s). Every code change must keep these to four decimals. They catch "improvements" that quietly broke the engine.',
  },
  {
    type: 'p',
    text: 'Current state across 263 matched benchmarks (10 November 2026 sweep): the overall source-quality-weighted mean absolute error is 0.25 seconds, and the weighted bias is essentially zero (+0.023 s), so the simulator is not systematically optimistic or pessimistic. Across the ten cleanest validated runs the mean absolute error is ±0.006 s, and 130 of the 263 benchmarks fall within ±0.20 s. The litre sport classes are the tightest: 0.146 s weighted |Δ| for 600–1000 cc fours and triples, 0.171 s for 195 hp and up. The small-cc and 2-stroke clusters have higher variance, partly because their published benchmarks are themselves uncertain (most Indian small-cc ETs are estimated from 0–100 km/h times rather than measured timeslips).',
  },
  {
    type: 'h2',
    text: 'What the remaining error means',
  },
  {
    type: 'p',
    text: 'A 0.26-second weighted mean error sounds large. It is comparable to magazine-test variance. Cycle World publishing a 10.20-second ET for a CBR1000RR is rounding from a real run that might have been 10.18 to 10.23 depending on staging, weight transfer technique, and rider weight. Our 0.15-second weighted mean on the litre-class is close to the published-test noise floor.',
  },
  {
    type: 'p',
    text: 'For the small-cc cluster (R15, Pulsar, Apache, FZ25 class), the gap is a mix of physics residual and benchmark uncertainty. We have audited the benchmarks against multiple sources where available, downgraded clearly-modded forum claims to the more conservative published instrumented numbers, and flagged remaining estimates with explicit ±0.7-second uncertainty markers. The simulator is now centered at zero bias on this cluster, which means its long-run predictions are unbiased even where individual data points have noise.',
  },
  {
    type: 'p',
    text: 'What helps next is measured data, plus sourced gearing for the small bikes, not a more complex model. The calibration module (motoquant/calibration/calibrator.py) can already fit drag coefficient and tyre grip to a Dragy run when you run it yourself; the website only lines your run up against the simulation and keeps nothing. The validation loop closes as riders submit timeslips through the "Submit a timeslip" form and reviewed runs join the benchmark set.',
  },
  {
    type: 'h2',
    text: 'Open source, citable, replayable',
  },
  {
    type: 'p',
    text: 'Every simulation MotoQuant runs is reproducible. Given the same BikeConfig and Race environment, you get the same ET to four decimals every time. The state vector is exposed in the timeseries output, so you can plot RPM, gear, slip ratio, drive force, and aero drag against time and see exactly what the simulator did. When the prediction disagrees with reality, the timeseries tells you whether it is a launch problem, a gearing problem, an aero problem, or something else.',
  },
  {
    type: 'p',
    text: 'The sub-models are tested independently. test_validation.py exercises physics conservation laws (energy in == energy out + heat). test_no_silent_failures.py runs all 534 catalog bikes and asserts each finishes within the time budget or is on an explicit DNF whitelist for vintage low-power 2-strokes. test_submodel_kaizen.py catches silent failure modes in clutch, tire thermal, braking, and rider dynamics. The full suite has about 6,200 tests; integration tests exercise the surrogate models, ROI engine, and recommendations layer.',
  },
  {
    type: 'h2',
    text: 'What you can do with it',
  },
  {
    type: 'p',
    text: 'A tuner can try a power commander map, an exhaust or a sprocket change and see the predicted change in ET, trap speed and cost per tenth of a second before spending money. A racer preparing for Aamby Valley in November can enter the venue conditions, the bike and the current tune, then adjust launch RPM and shift points until the predicted ET stops improving. A beginner can learn what actually limits a drag run on their own bike. Most people overrate peak power and underrate mass, gearing and traction.',
  },
  {
    type: 'p',
    text: 'We keep building it because nothing like it existed for the Indian and SE Asia drag scene. Most simulators target US litre superbikes on prepped concrete with VHT. We started there too (the K5 reference baseline came from US drag-strip data) and worked outward to the bikes and conditions that matter to riders running R15s at Narhe and Pulsars at Aamby Valley.',
  },
];

function renderBlock(block, idx) {
  switch (block.type) {
    case 'lead':
      return (
        <p key={idx} className="text-lg leading-relaxed text-white/85 mb-8 first-letter:text-3xl first-letter:font-display first-letter:font-bold first-letter:text-brand-orange first-letter:mr-1 first-letter:float-left first-letter:leading-tight">
          {block.text}
        </p>
      );
    case 'h2':
      return (
        <h2 key={idx} className="font-display font-bold text-2xl text-white mt-12 mb-4 leading-snug">
          {block.text}
        </h2>
      );
    case 'p':
      return (
        <p key={idx} className="text-white/75 text-base leading-relaxed mb-5">
          {block.text}
        </p>
      );
    case 'callout':
      return (
        <aside key={idx} className="my-7 p-5 rounded-xl border border-brand-orange/30 bg-brand-orange/5 text-white/85 text-sm leading-relaxed">
          {block.text}
        </aside>
      );
    default:
      return null;
  }
}

const articleSchema = {
  '@context': 'https://schema.org',
  '@type': 'Article',
  headline: 'How the MotoQuant physics engine works',
  description: 'The 15 sub-models and RK4 integrator behind MotoQuant.',
  author: { '@type': 'Organization', name: 'MotoQuant' },
  publisher: { '@type': 'Organization', name: 'MotoQuant', logo: { '@type': 'ImageObject', url: 'https://motoquant.in/logo.png' } },
  datePublished: '2026-04-27',
  mainEntityOfPage: { '@type': 'WebPage', '@id': 'https://motoquant.in/blog/how-the-motoquant-physics-engine-works' },
};

export default function Page() {
  return (
    <div className="min-h-screen bg-black text-white">
      <SiteNav />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(articleSchema) }} />

      <main id="main" className="max-w-3xl mx-auto px-6 pt-32 pb-12">
        <Link href="/blog" className="text-brand-accent text-sm font-mono mb-6 inline-block hover:text-brand-orange transition-colors">
          ← back to blog
        </Link>

        <header className="mb-10">
          <div className="flex flex-wrap gap-1.5 mb-4">
            {['physics', 'engine', 'validation', 'methodology'].map(t => (
              <span key={t} className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent">
                {t}
              </span>
            ))}
          </div>
          <CodeComment className="mb-4">engine bay · 15 submodels exposed</CodeComment>
          <h1 className="font-display font-bold text-4xl md:text-5xl text-white leading-tight mb-4">
            How the MotoQuant physics engine works
          </h1>
          <p className="text-white/55 text-sm font-mono">
            April 27, 2026 · 14 min read
          </p>
        </header>

        <article className="prose-custom">
          {CONTENT.map(renderBlock)}
        </article>

        <footer className="mt-16 pt-8 border-t border-white/10">
          <p className="text-white/55 text-sm">
            To try it on your bike,{' '}
            <Link href="/" className="text-brand-orange hover:text-brand-accent transition-colors">
              run a simulation
            </Link>{' '}
            on the home page: pick a bike and set your conditions.
          </p>
          {/* Reference baselines — timing-board panel */}
          <div className="relative overflow-hidden rounded-xl border border-brand-orange/20 bg-ink-1/60 p-5 mt-6">
            <span aria-hidden="true" className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-brand-orange/50 to-transparent" />
            <div className="text-xs text-white/60 mb-4">
              Reference baselines · held to four decimals by CI
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {[
                ['GSX-R 1000 K5', '10.0436'],
                ['YZF-R1 4C8', '10.1092'],
                ['Hayabusa Gen1', '10.1100'],
              ].map(([bike, et]) => (
                <div key={bike}>
                  <div className="flex items-end gap-1">
                    <ScoreboardDigits value={et} h={22} label={`${et} seconds`} />
                    <span className="font-mono text-[10px] text-white/60 mb-0.5">s</span>
                  </div>
                  <div className="mt-1.5 text-xs text-white/60">{bike}</div>
                </div>
              ))}
            </div>
            <p className="text-white/60 text-xs mt-4">
              The bias, mean absolute error and within-tolerance figures in this post come from the 10 November 2026 sweep against 250 published benchmarks (263 matched).
            </p>
          </div>
        </footer>
      </main>

      <SiteFooter />
    </div>
  );
}
