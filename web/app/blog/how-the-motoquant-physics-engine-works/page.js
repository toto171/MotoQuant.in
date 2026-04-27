import Link from 'next/link';

export const metadata = {
  title: 'How the MotoQuant Physics Engine Works — MotoQuant Blog',
  description: 'A first-principles tour of the 15-sub-model RK4 physics engine that powers MotoQuant Pro. From engine torque curves to Pacejka tire models to launch slip dynamics — what we simulate, what we validate against, and what the residual error actually means.',
  keywords: [
    'motorcycle physics simulation',
    'drag racing simulator',
    'Pacejka tire model',
    'RK4 motorcycle dynamics',
    'first-principles motorcycle physics',
    'MotoQuant engine',
    'physics validation',
    'drag racing model',
  ],
  alternates: { canonical: 'https://motoquant.in/blog/how-the-motoquant-physics-engine-works' },
  openGraph: {
    title: 'How the MotoQuant Physics Engine Works',
    description: '15 sub-models, RK4 integration at 1ms, validated against 90 published drag-strip benchmarks. Reference baselines accurate to 4 decimals. A tour of what is under the hood.',
    url: 'https://motoquant.in/blog/how-the-motoquant-physics-engine-works',
    type: 'article',
    publishedTime: '2026-04-27T00:00:00Z',
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: 'MotoQuant Pro is a first-principles physics simulator for motorcycle quarter-mile drag racing. It is built around 15 independent sub-models — engine, clutch, drivetrain, chain, tires, aero, weight transfer, rider dynamics, staging, environmental, parasitic losses, rolling resistance, braking, wheelie, forced induction — coupled by a fixed-step RK4 integrator running at one-millisecond resolution. This post is a tour of what each sub-model does, what we validate against, and where the simulator is honest about its limits.',
  },
  {
    type: 'h2',
    text: 'The Architecture in One Picture',
  },
  {
    type: 'p',
    text: 'The state vector is six-dimensional: position, velocity, engine angular velocity, tire temperature, clutch temperature, and current gear. Every millisecond, the integrator advances this state by computing forces and torques from each sub-model and combining them into a net acceleration. RK4 with aero midpoint re-evaluation gets us numerical stability across the full speed range — from 0 m/s at the staging beam to the 200+ km/h trap.',
  },
  {
    type: 'p',
    text: 'Why fixed-step RK4 instead of an adaptive solver? Two reasons. First, drag races are short — 10 to 20 seconds — and a 1 ms timestep gives 10,000–20,000 integration points, which is more than enough resolution to capture the launch slip phase, gear changes, and the high-frequency dynamics of clutch engagement. Second, fixed-step is reproducible bit-for-bit across runs, which matters when you are debugging a 0.05-second discrepancy. We also expose an adaptive variant (use_adaptive_dt=True) for users who want faster simulation at the cost of reproducibility.',
  },
  {
    type: 'h2',
    text: 'Sub-Model 1: Engine Torque',
  },
  {
    type: 'p',
    text: 'The engine sub-model takes RPM and time and returns crank torque. There are two paths. For the 21 most popular drag bikes (Hayabusa, R1, GSX-R 1000, ZX-10R, S1000RR, Panigale V4, RSV4, etc.) we ship measured dyno curves — RPM-vs-torque arrays sourced from Cycle World, Sport Rider, and Dynojet published tests. For everything else we synthesize a curve from the manufacturer-published peak power, peak torque, and the RPMs at which they occur.',
  },
  {
    type: 'p',
    text: 'The synthesized curve is an asymmetric Gaussian: a gentle ramp from idle to peak torque, then a shaped falloff to redline calibrated so the torque at peak power RPM produces exactly the rated horsepower. The shape parameters (sigma below peak, redline factor above peak) are calibrated by class — modern litre superbikes get sigma=2.2 and a steep 0.48 redline factor for that "pulls hard then signs off" character; mid-range 600-800cc 4-cyl get a plateau-like 0.88 redline factor that matches dyno tests showing flat torque to redline; small-cc commuters get a broader sigma=1.20 because real R15 and Pulsar dynos show flatter curves than the default Gaussian assumes.',
  },
  {
    type: 'p',
    text: 'Two-stroke engines get a different model entirely. Their torque curves are dominated by expansion chamber resonance — a sharp peak at the tuned RPM with very little off-pipe torque. We synthesize a Gaussian-like band around the tuned RPM with width parameters that vary by configuration: piston-port singles (RX100, RD350) get a narrow band; YPVS-equipped powervalves (NSR250R, RGV250) get a wider band with stronger off-pipe torque; vintage triples (GT750, H2 Mach IV) get an overlapping multi-cylinder band that approaches 4-stroke smoothness.',
  },
  {
    type: 'h2',
    text: 'Sub-Model 2: Clutch Slip and Lockup',
  },
  {
    type: 'p',
    text: 'The clutch is the most physics-intensive sub-model after the tire. There are four types: standard lockup (most modern bikes), slider/centrifugal (vintage and small-cc), multi-stage (some MotoGP-derived sport bikes), and slipper (modern litre bikes for back-torque limiting). Each behaves differently under launch and downshift conditions.',
  },
  {
    type: 'p',
    text: 'During launch, the clutch is in the slip phase: engine RPM is held above the wheel-equivalent RPM, and friction transmits torque between the two. The amount of torque transmitted depends on the friction coefficient, the clamping force from the springs, the plate count, and the mean friction radius — these come from the clutch sub-config (which has real geometry from service manuals where available).',
  },
  {
    type: 'p',
    text: 'A subtle bug we fixed in late April 2026 — the original slip model used T_transmitted = min(T_engine, T_clutch_max), which kept engine RPM pinned at the launch RPM during the entire slip phase. That is fine for big litre bikes where T_clutch_max is close to T_engine. For small-cc bikes where T_clutch_max is much larger than T_engine (clutch sized for safety, not engine output), it caused the simulation to under-predict launch acceleration by 30–40 % because the engine never had a chance to transfer kinetic energy through the clutch into wheel acceleration. The fix: rate-limited over-clutching where T_transmitted can briefly exceed T_engine by up to (max_decel × engine_inertia) torque, simulating the real-world rider technique of feathering the clutch while bogging the engine briefly.',
  },
  {
    type: 'callout',
    text: 'The slip phase typically resolves into lockup when the engine and wheel-equivalent RPMs come within ~10 RPM of each other. After that, the clutch is treated as a rigid coupling and the bike accelerates on engine torque alone — until the next gear change.',
  },
  {
    type: 'h2',
    text: 'Sub-Model 3: Drivetrain and Gear Cassette',
  },
  {
    type: 'p',
    text: 'Drivetrain is conceptually simple: primary ratio × current gear ratio × secondary ratio (front sprocket / rear sprocket) gives the total reduction. Multiply by engine torque to get rear-wheel torque. Divide by rear wheel rolling radius to get drive force.',
  },
  {
    type: 'p',
    text: 'In practice, getting the right gear ratios for 287 different bikes was its own multi-month effort. We maintain a Tier-1 lookup table with 150+ named-model entries derived from service manuals (R15 V4: 14F/48R, primary 2.83, gears 2.833 / 1.875 / 1.429 / 1.16 / 0.963 / 0.84 — those numbers come from the YZF-R15 service manual, not from a forum). Bikes without a Tier-1 entry fall back to category-based defaults (sport-1000, naked-mid, cruiser-big, etc.) which are still better than generic numbers but lose the per-model flavor.',
  },
  {
    type: 'p',
    text: 'Shift dynamics matter too. Each gear change costs simulation time equal to the shift_time_ms parameter (typically 50–80 ms with a quickshifter, 150–300 ms manual). During the shift, drive force is zero — the bike coasts. A poorly-calibrated shift point can cost 0.05–0.15 seconds in ET if the engine drops below peak power on the next gear, so getting the shift_rpms array right per bike is part of the gear-cassette work.',
  },
  {
    type: 'h2',
    text: 'Sub-Model 5: Tires (Pacejka with Thermal)',
  },
  {
    type: 'p',
    text: 'Tire physics is a Pacejka Magic Formula model. Given a slip ratio and a load (vertical force on the tire), the model returns the longitudinal force the tire can deliver. The shape of the curve is controlled by four parameters per tire: B (stiffness), C (shape), D (peak), and E (curvature). These come from a tire library of 232 tires across 16 manufacturers — drag slicks, sport touring, race compounds, Indian commuter rubber (MRF, CEAT), all with calibrated Pacejka coefficients.',
  },
  {
    type: 'p',
    text: 'Peak longitudinal force occurs at a slip ratio of roughly 0.07–0.15 for road tires. That is why launches with deliberate wheel spin can be faster than perfect-traction launches — you are operating at the peak of the slip-vs-force curve instead of below it. Above the peak, force falls off rapidly, which is why aggressive throttle on a smoking tire is slower than measured throttle.',
  },
  {
    type: 'p',
    text: 'The thermal layer is critical. mu_peak depends strongly on tire temperature: a sticky slick at 80°C can deliver 1.85 mu_peak, the same tire at 25°C delivers ~1.1. Our thermal model tracks heat generated from slip (Q = T_transmitted × slip_speed), conductance to track surface, and convection to ambient air. Real burnouts typically warm the tire from 25°C to 50–55°C, which is why we model the rear tire starting at the burnout-end temperature, not ambient.',
  },
  {
    type: 'h2',
    text: 'Sub-Models 6–8: Aero, Weight Transfer, Rider Dynamics',
  },
  {
    type: 'p',
    text: 'Aero is straightforward: F_drag = 0.5 × rho × v² × Cd × A. The interesting part is that Cd × A is time-varying. The rider transitions from an upright staging stance to a tucked aerodynamic position over roughly 2 seconds after launch, dropping Cd × A by 30–40 %. We model this transition with a sigmoid curve — at 0 seconds, the rider is upright (Cd × A = ~0.55); at 2 seconds, fully tucked (Cd × A = ~0.32). Cd and frontal area come from per-bike values; we measured or estimated each one of the 327 bikes individually after discovering that 71 % of the catalog had inherited a generic 0.32 Cd that is closer to a passenger car than a motorcycle.',
  },
  {
    type: 'p',
    text: 'Weight transfer reduces front axle load and increases rear axle load proportionally to acceleration × CoG_height / wheelbase. More rear load = more available traction (good). Past a critical point, front goes light enough that the bike wheelies — a separate sub-model that limits available drive force to whatever keeps the front wheel a few millimeters off the ground. A liter-class superbike on a hard launch typically wheelies in gear 1 around 0.7–1.0 g; the wheelie limit is what caps acceleration in that window, not engine power or tire grip.',
  },
  {
    type: 'p',
    text: 'Rider dynamics also includes a longitudinal CoG shift — the rider scoots back at launch (pulling weight rearward, helping traction) and tucks forward at speed (reducing aero drag). Both shifts are tracked in the sub-model and feed into weight transfer and aero respectively.',
  },
  {
    type: 'h2',
    text: 'Sub-Models 9–15: The Rest',
  },
  {
    type: 'p',
    text: 'Staging models the launch dead-time (reaction + vehicle response) and the two-step / launch-RPM logic. Environmental models air density, density altitude (which costs 1 % power per 100 m above sea level for naturally aspirated engines), wind, and surface grip multiplier. Forced induction handles turbo, supercharger, and nitrous boost profiles. Parasitic losses subtract alternator, water pump, oil pump, and valve-train power from net engine output. Rolling resistance scales with tire load and a temperature-dependent crr coefficient. Braking is for the next-step plans (reverse simulation, brake performance comparisons) and is not active during a forward drag run. The full model has been built up incrementally over 6 months of development.',
  },
  {
    type: 'h2',
    text: 'How We Validate',
  },
  {
    type: 'p',
    text: 'We maintain a list of 90+ published drag-strip benchmarks — sourced from Cycle World, Sport Rider, MCN, Motorcycle Consumer News, MotorcycleDaily, MotoStatz, FastestLaps, and Indian Autos Mag where the magazine published the actual instrumented timeslip. For each benchmark, we run the simulator at the test-day environmental conditions and compare predicted ET against measured ET. The delta gets bucketed by class (litre-sport-195+, litre-sport-600-1000, mid-twin-300-500, entry-150-200, two-stroke, etc.) so we can see where the physics is honest and where it has systematic bias.',
  },
  {
    type: 'p',
    text: 'Three reference baselines are protected absolutely: GSX-R 1000 K5 (10.0334 s), YZF-R1 4C8 (10.2859 s), and Hayabusa Gen1 (10.4712 s). Every code change must preserve these to four decimals. They are the regression test that catches "improvements" that secretly broke the engine.',
  },
  {
    type: 'p',
    text: 'Current state across 90 matched benchmarks: overall mean absolute error is 0.365 seconds, bias is essentially zero (-0.002 s — meaning the simulator is no longer systematically optimistic or pessimistic). The 195+ hp class is the tightest at 0.162 s mean |Δ|. The small-cc and 2-stroke clusters have higher variance, partly because their published benchmarks are themselves uncertain (most Indian small-cc ETs are estimated from 0–100 km/h times rather than measured timeslips).',
  },
  {
    type: 'h2',
    text: 'What the Residual Error Actually Means',
  },
  {
    type: 'p',
    text: 'A 0.36-second mean error sounds large. In context, it is comparable to magazine-test variance — Cycle World publishing a 10.20-second ET for a CBR1000RR is rounding from a real run that might have been 10.18 to 10.23 depending on staging, weight transfer technique, and rider weight. Our 0.18-second mean on the litre-class is close to the published-test noise floor.',
  },
  {
    type: 'p',
    text: 'For the small-cc cluster (R15, Pulsar, Apache, FZ25 class), the gap is a mix of physics residual and benchmark uncertainty. We have audited the benchmarks against multiple sources where available, downgraded clearly-modded forum claims to the more conservative published instrumented numbers, and flagged remaining estimates with explicit ±0.7-second uncertainty markers. The simulator is now centered at zero bias on this cluster, which means its long-run predictions are unbiased even where individual data points have noise.',
  },
  {
    type: 'p',
    text: 'The path forward is measured data, not more model complexity. Phase 3 of the project is a Dragy GPS calibrator — a CLI that takes a real Dragy timeslip from your bike on your strip, fits the simulator parameters to your run, and produces a personalized config that matches your build. Once that is in production, the validation loop closes: stock-bike benchmarks become user-uploaded measurements rather than magazine claims.',
  },
  {
    type: 'h2',
    text: 'Open Source, Citable, Replayable',
  },
  {
    type: 'p',
    text: 'Every simulation MotoQuant runs is reproducible. Given the same BikeConfig and Race environment, you get the same ET to four decimals every time. The state vector is exposed in the timeseries output, so you can plot RPM, gear, slip ratio, drive force, and aero drag against time and see exactly what the simulator did. When the prediction disagrees with reality, the timeseries tells you whether it is a launch problem, a gearing problem, an aero problem, or something else.',
  },
  {
    type: 'p',
    text: 'The sub-models are tested independently. test_validation.py exercises physics conservation laws (energy in == energy out + heat). test_no_silent_failures.py runs all 287 catalog bikes and asserts each finishes within the time budget or is on an explicit DNF whitelist for vintage low-power 2-strokes. test_submodel_kaizen.py catches silent failure modes in clutch, tire thermal, braking, and rider dynamics. The full suite passes 174 fast tests; integration tests exercise the surrogate models, ROI engine, and recommendations layer.',
  },
  {
    type: 'h2',
    text: 'What This Buys You',
  },
  {
    type: 'p',
    text: 'For a tuner, the simulator is a what-if explorer. Try a power commander map, an exhaust, a sprocket change — see the predicted ET delta and trap-speed delta and cost-per-tenth-of-a-second before spending money. For a racer prepping for Aamby Valley in November, plug in the venue conditions, your bike, and your current tune; iterate launch RPM and gear-shift points until the predicted ET converges. For a beginner, it is a way to learn what physics actually limits a drag run on your specific bike — most people overestimate the importance of peak power and underestimate the importance of mass, gearing, and traction.',
  },
  {
    type: 'p',
    text: 'For us, it is a tool we keep building because there was nothing else like it for the Indian and SE Asia drag scene. Most existing simulators target US litre superbikes on prepped concrete with VHT. We started there too — the K5 reference baseline came from US drag-strip data — and built outward to cover the bikes and conditions that matter to riders running R15s at Narhe and Pulsars at Aamby Valley. The physics is universal; the calibration data is what makes a simulator useful for a specific community.',
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
  headline: 'How the MotoQuant Physics Engine Works',
  description: 'A first-principles tour of the 15-sub-model RK4 physics engine that powers MotoQuant Pro.',
  author: { '@type': 'Organization', name: 'MotoQuant' },
  publisher: { '@type': 'Organization', name: 'MotoQuant', logo: { '@type': 'ImageObject', url: 'https://motoquant.in/logo.png' } },
  datePublished: '2026-04-27',
  mainEntityOfPage: { '@type': 'WebPage', '@id': 'https://motoquant.in/blog/how-the-motoquant-physics-engine-works' },
};

export default function Page() {
  return (
    <main className="min-h-screen bg-brand-carbon text-white">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(articleSchema) }} />

      <div className="max-w-3xl mx-auto px-6 py-12">
        <Link href="/blog" className="text-brand-accent text-sm font-mono mb-6 inline-block hover:text-brand-orange transition-colors">
          ← back to blog
        </Link>

        <header className="mb-10">
          <div className="flex flex-wrap gap-1.5 mb-4">
            {['physics', 'engine', 'validation', 'methodology'].map(t => (
              <span key={t} className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide">
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl text-white leading-tight mb-4">
            How the MotoQuant Physics Engine Works
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
            Want to try it on your bike?{' '}
            <Link href="/" className="text-brand-orange hover:text-brand-accent transition-colors">
              Run a simulation
            </Link>{' '}
            on the home page — pick a bike, set your conditions, and see the physics in action.
          </p>
          <p className="text-white/40 text-xs mt-4">
            Reference baselines preserved across all releases: GSX-R 1000 K5 = 10.0334 s, YZF-R1 4C8 = 10.2859 s, Hayabusa Gen1 = 10.4712 s. All claims about cluster bias, mean absolute error, and within-tolerance fractions in this post reflect the April 27, 2026 sweep against 90 published benchmarks.
          </p>
        </footer>
      </div>
    </main>
  );
}
