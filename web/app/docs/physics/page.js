import Link from 'next/link';

export const metadata = {
  title: 'Physics whitepaper',
  description: 'The first-principles physics behind the MotoQuant quarter-mile simulator: 15 sub-models, RK4 integrator at 1 ms step, a rear-tyre grip model with load sensitivity and thermal evolution, Willans friction, 2T expansion-chamber Gaussian curve, weight transfer and weighted-benchmark validation.',
  alternates: { canonical: 'https://motoquant.in/docs/physics' },
  keywords: [
    'rk4 motorcycle simulator',
    'first principles motorcycle drag simulation',
    'motorcycle physics simulator methodology',
    'two stroke expansion chamber model',
    'willans friction motorcycle',
    'motorcycle quarter mile physics whitepaper',
    'physics based bike ET predictor',
    'validated drag racing model india',
  ],
};

const SUBMODELS = [
  { n: '01', name: 'Engine torque model', desc: 'Peak power + torque from spec; dyno curve injection if available. Willans mean-effective-pressure friction model for mechanical losses. 2T expansion-chamber Gaussian curve with powervalve width modulation.', file: 'submodels/engine.py' },
  { n: '02', name: 'Forced induction', desc: 'Turbocharger (boost curve, compressor map, lag), supercharger (mechanical drive loss, constant boost), nitrous (injection window, jetting-mass-flow). Boost type is a per-part parameter.', file: 'submodels/forced_induction.py' },
  { n: '03', name: 'Drivetrain', desc: 'Gear ratio lookup from 150+ Tier-1 service-manual-accurate families. Chain drive efficiency (0.95–0.97 across the catalog). Quickshifter model (zero-torque cut window, shift time).', file: 'submodels/drivetrain.py' },
  { n: '04', name: 'Clutch dynamics', desc: 'Wet multi-plate clutch with engagement rate (Nm/s) and slip RPM threshold. Slipper clutch branch: overrun torque reversal → spring-preload backstop. Clutch heat accumulation during engagement.', file: 'submodels/clutch.py' },
  { n: '05', name: 'Chain & sprocket', desc: 'Sprocket ratio applied to rear-wheel torque. Chain stretch factor (efficiency reduction over service interval). Checks that sprocket tooth counts are physically valid.', file: 'submodels/chain.py' },
  { n: '06', name: 'Tyre grip', desc: 'Traction limit μ × F_z,rear, where μ starts from the tyre\'s peak friction coefficient and is adjusted for load sensitivity, tread temperature, pressure rise with temperature and track preparation. Thermal evolution: heat from slip, conduction to the road surface and convection to the air. A Pacejka Magic Formula slip curve is implemented but not yet used by the integrator.', file: 'submodels/tire.py' },
  { n: '07', name: 'Aerodynamics', desc: 'F_drag = ½·ρ·Cd·A·v². Per-bike Cd (0.42–0.92 across the catalog) and frontal area (0.35–0.78 m²). Rider tuck transition: Cd interpolates from upright to tuck posture above a speed threshold. Wind vector support.', file: 'submodels/aero.py' },
  { n: '08', name: 'Weight transfer', desc: 'Longitudinal weight transfer: ΔF_z = m·a_x·h_cog / L_wb. Front axle load approaches zero at wheelie threshold. Rear axle load added to tyre normal force for traction calculation.', file: 'submodels/weight_transfer.py' },
  { n: '09', name: 'Rider dynamics', desc: 'Rider CoG height and longitudinal position; rider mass distributed across total system. Tuck factor: rider frontal area reduction at high speed. Separately tunable for different rider postures (sport tuck vs upright naked).', file: 'submodels/rider_dynamics.py' },
  { n: '10', name: 'Staging & launch', desc: 'Rollout distance, reaction time (added post-tree), two-step launch control RPM. For 2T engines, launch RPM defaults to tuned_rpm × 0.92. For 4T, configurable launch_rpm field in BikeConfig.', file: 'submodels/staging.py' },
  { n: '11', name: 'Environmental', desc: 'Air density from ISA model: ρ = P/(R_specific·T). Power correction factor: (P_std/P) × √(T_std/T). Density altitude calculation. Surface grip multiplier (asphalt, concrete, salt flat, dry lake). Wind resistance add-in.', file: 'submodels/environmental.py' },
  { n: '12', name: 'Braking', desc: 'Used for top-speed and calibration passes. max_decel = μ_front × front_load + μ_rear × rear_load, with brake balance split. Braking from trap speed to rest for multi-run simulation.', file: 'submodels/braking.py' },
  { n: '13', name: 'Wheelie model', desc: 'When front axle load → 0: system transitions to rotational dynamics. Wheelie bar extends effective wheelbase, resisting the transition. Wheelie contributes angular momentum competing with forward acceleration.', file: 'submodels/wheelie.py' },
  { n: '14', name: 'Parasitic losses', desc: 'Alternator (60–150 W), oil pump, water pump and valvetrain drag (none for a two-stroke), each set per bike and modelled as a power drain from the crankshaft.', file: 'submodels/parasitic.py' },
  { n: '15', name: 'Rolling resistance', desc: 'F_rr = Crr × m × g, with Crr = Crr_base + k_v × v², reduced as the tyre warms and raised on soft surfaces such as salt or a dry lake bed.', file: 'submodels/rolling_resistance.py' },
];

function SubModelRow({ model }) {
  return (
    <div className="py-4 border-b border-white/[0.05] last:border-0">
      <div className="flex items-start gap-4">
        <div className="w-8 shrink-0 pt-1">
          <span className="font-mono text-sm tabular-nums text-accent">{model.n}</span>
        </div>
        <div className="flex-1">
          <div className="font-display font-bold text-sm text-white mb-1">{model.name}</div>
          <p className="text-sm text-white/70 leading-relaxed">{model.desc}</p>
          <div className="mt-1.5 font-mono text-xs text-white/60 break-all">{model.file}</div>
        </div>
      </div>
    </div>
  );
}

export default function PhysicsPage() {
  return (
    <article>
      <header className="mb-12">
        <p className="eyebrow mb-2">For the curious</p>
        <h1 className="font-display font-bold text-3xl md:text-4xl text-white mb-4 tracking-tight">How the physics works</h1>
        <p className="text-white/70 text-base leading-relaxed mb-5">
          The engineering behind every prediction: the 15 sub-models, the numerical integrator and how
          we check the results. You do not need any of this to use the simulator.
        </p>
        <p className="rounded-xl border border-accent/25 bg-accent/5 px-4 py-3 text-base leading-relaxed text-white/85">
          MotoQuant steps your bike forward
          one millisecond at a time. At each step it works out engine power, gearing, tyre grip, drag and weight
          transfer, until the bike crosses the quarter-mile line.
        </p>
      </header>

      {/* Overview */}
      <section className="mb-14">
        <h2 className="font-display font-bold text-2xl text-white mb-4">Overview</h2>
        <p className="text-white/75 text-base leading-relaxed mb-4">
          MotoQuant solves the motorcycle drag problem as a system of coupled ODEs. The state vector at each timestep
          is [position, velocity, engine_RPM, tyre_temperature, clutch_temperature, gear]. The RK4 integrator advances
          this vector at dt = 1 ms (fixed-step mode) or dt_min = 0.5 ms / dt_max = 5 ms (adaptive mode), re-evaluating
          aerodynamic and traction forces at the midpoint of each step.
        </p>
        <p className="text-white/75 text-base leading-relaxed mb-4">
          The simulation stops when the bike crosses 402.336 m (the quarter mile), when elapsed time passes
          26 s (so a bike that cannot finish does not loop forever), or when a NaN/Inf appears in the state vector.
          In that last case it exits early with an error flag instead of returning a corrupted result.
        </p>
        <div className="card p-5 mb-4 border-brand-orange/20">
          <div className="label-mono text-brand-accent mb-2">State vector</div>
          <code className="block overflow-x-auto text-sm font-mono text-white/80">[x, v, ω_e, T_tyre, T_clutch, gear]</code>
          <div className="mt-3 grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs font-mono text-white/60">
            <span>x: position (m)</span>
            <span>v: velocity (m/s)</span>
            <span>ω_e: engine RPM (rad/s)</span>
            <span>T_tyre: tyre temp (°C)</span>
            <span>T_clutch: clutch temp (°C)</span>
            <span>gear: gear index (1–6)</span>
          </div>
        </div>
        <div className="card p-5 border-brand-orange/20">
          <div className="label-mono text-brand-accent mb-2">Force balance at each timestep</div>
          <code className="block overflow-x-auto whitespace-pre text-sm font-mono text-white/80 leading-relaxed">
            F_net = F_traction − F_aero − F_rolling_resistance − F_grade<br />
            a = F_net / m_total<br />
            F_traction = min(T_wheel / R_tyre, μ(F_z_rear, T_tyre) × F_z_rear)
          </code>
        </div>
      </section>

      {/* Integrator */}
      <section className="mb-14">
        <h2 className="font-display font-bold text-2xl text-white mb-4">Numerical integrator</h2>
        <p className="text-white/75 text-base leading-relaxed mb-4">
          The fixed-step RK4 integrator runs at dt = 1 ms. For most bikes that is accurate enough: the maximum
          position error per step is O(dt⁵) ≈ 10⁻¹⁵ m, well within measurement noise.
        </p>
        <p className="text-white/75 text-base leading-relaxed mb-4">
          The adaptive-dt solver uses a fifth-order embedded RK pair (RK45) with error control. Step size is
          halved when position error exceeds 10⁻⁴ m and doubled when error is below 10⁻⁶ m. It helps most in
          clutch-heavy launches, where the state changes fast and 1 ms steps may mis-time the engagement point
          slightly.
        </p>
        <p className="text-white/75 text-base leading-relaxed">
          Aerodynamic drag is re-evaluated at the RK4 midpoint (i.e. at v + k₁/2 rather than at v) to reduce
          the systematic bias that naive Euler or basic RK4 produces at high velocities. The gain is small but
          measurable on bikes that spend much of the run above 180 km/h.
        </p>
      </section>

      {/* Sub-models */}
      <section className="mb-14">
        <h2 className="font-display font-bold text-2xl text-white mb-2">The 15 sub-models</h2>
        <p className="text-white/60 text-sm mb-6">
          Each sub-model is an independent Python module in <code className="font-mono text-brand-accent break-words">motoquant/submodels/</code>.
          They communicate only through the BikeConfig dataclass and the current state vector, with no global state.
        </p>
        <div className="card px-5 border-brand-orange/20 divide-y divide-white/[0.05]">
          {SUBMODELS.map(m => <SubModelRow key={m.n} model={m} />)}
        </div>
      </section>

      {/* Bike config */}
      <section className="mb-14">
        <h2 className="font-display font-bold text-2xl text-white mb-4">BikeConfig: the parameter container</h2>
        <p className="text-white/75 text-base leading-relaxed mb-4">
          Every simulation takes a <code className="font-mono text-brand-accent break-words">BikeConfig</code> object, a nested Pydantic/dataclass
          structure with 13 parameter sections: EngineParams, ForcedInductionParams, DrivetrainParams, ClutchParams,
          ChainParams, TireParams, AeroParams, ChassisParams, WheelieParams, RiderParams, StagingParams,
          EnvironmentParams, ParasiticParams.
        </p>
        <p className="text-white/75 text-base leading-relaxed mb-4">
          The <code className="font-mono text-brand-accent break-words">spec_to_bike_config()</code> function in <code className="font-mono text-brand-accent break-words">scraper/importer.py</code> converts
          a raw <code className="font-mono text-brand-accent break-words">BikeSpec</code> (scraped or hand-entered) into a validated BikeConfig. It applies
          displacement-scaled engine inertia, chain-pitch-inferred drivetrain parameters, category-aware tyre grip
          defaults, and the 150+ Tier-1 gear ratio families.
        </p>
        <p className="text-white/75 text-base leading-relaxed">
          Parts mods use dotted paths to override specific fields (e.g. <code className="font-mono text-brand-accent break-words">engine.peak_power_hp</code>,
          <code className="font-mono text-brand-accent mx-1 break-all">drivetrain.front_sprocket</code>). The bridge module validates every path before applying it
          and logs a warning if a path is stale.
        </p>
      </section>

      {/* Next */}
      <div className="pt-8 border-t border-brand-orange/10">
        <div className="label-mono mb-4">Next</div>
        <div className="grid sm:grid-cols-2 gap-4">
          <Link href="/docs/validation" className="card card-hover block p-4 group">
            <div className="font-display font-bold text-white mb-1 group-hover:text-brand-orange transition-colors">Validation data →</div>
            <div className="text-xs text-white/60">Benchmark table with 250 benchmarks, per-cluster accuracy metrics, and methodology.</div>
          </Link>
          <Link href="/docs/getting-started" className="card card-hover block p-4 group">
            <div className="font-display font-bold text-white mb-1 group-hover:text-brand-orange transition-colors">Run your first simulation →</div>
            <div className="text-xs text-white/60">The five-minute getting started guide.</div>
          </Link>
        </div>
      </div>
    </article>
  );
}
