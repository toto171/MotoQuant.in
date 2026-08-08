# Glossary — drag racing and the MotoQuant physics model

Terms a rider or tuner will actually use, plus the model-internal names you
will meet in the codebase. Load this when a conversation goes deeper than the
headline numbers in `SKILL.md`.

## The run

| Term | Meaning |
|---|---|
| **Quarter mile** | 402.336 m from a standing start. The classic drag distance. |
| **ET (elapsed time)** | Time from launch to the finish line, in seconds. The headline number. |
| **Trap speed** | Speed at the finish line. Tracks power-to-weight closely and is nearly immune to launch quality, so a bike that traps high but runs a slow ET has a launch problem, not a power problem. |
| **60-foot** | Time over the first 18.288 m. The launch-quality number — traction, clutch work, wheelie limit and gearing all show up here. |
| **330-foot / eighth mile (660 ft) / 1000-foot** | Intermediate splits. The eighth mile is a class in its own right for small-bore and street bikes. |
| **Rollout** | The ~0.3 m the front wheel rolls between breaking the stage beam and starting the clock. Strip timeslips include it, so a real slip can read slightly quicker than a rollout-free simulation of the same run. |
| **Staging** | Rolling forward until the pre-stage and stage beams are broken. "Deep staging" trades reaction time for a shorter effective run. |
| **Reaction time** | Time from green to the bike leaving the beam. It is a racer stat, not a bike stat, and is not part of ET. |
| **Red light / foul** | Leaving before green. Instant loss regardless of ET. |
| **Timeslip** | The printed record of a run: reaction, 60-ft, 330, eighth, 1000-ft, quarter, trap. |
| **Dial-in** | In bracket racing, the ET a racer predicts. Running quicker than your dial-in ("breaking out") loses. |

## Launch and drivetrain

| Term | Meaning |
|---|---|
| **Launch RPM** | Engine speed held against the clutch at the green. Too low bogs; too high spins or wheelies. |
| **Two-step** | A second rev limiter that pins the engine at launch RPM while the throttle is pinned. |
| **Over-clutching** | Deliberately slipping the clutch so the engine stays in its torque band while the tire hooks up. MotoQuant models this per bike class (`CategoryProfile.over_clutch_factor`); it dominates the first 60 feet on small-capacity bikes. |
| **Slipper clutch** | Back-torque-limiting clutch — helps on downshifts, does nothing for a launch. |
| **Lockup clutch** | Centrifugal clutch that slips by design at launch and progressively locks. A drag-specific part. |
| **Quickshifter** | Cuts ignition or fuel for a clutchless full-throttle upshift, cutting shift time from ~150 ms to ~50–70 ms. |
| **Air shifter** | Pneumatic shifter — the same idea, faster and used in the outlaw classes. |
| **Final drive** | Rear sprocket teeth ÷ front sprocket teeth. Bigger number = "shorter" gearing = more wheel torque, lower top speed. 16/45 = 2.81; 16/47 = 2.94. |
| **Shorter / taller gearing** | Shorter (bigger rear, or smaller front) trades top speed for acceleration. Whether it helps a quarter mile is bike-specific — simulate it, do not assume. |
| **Chain pitch** | 428 / 520 / 525 / 530 — the chain and sprocket size standard. Parts must match, and MotoQuant's fitment engine enforces it. |
| **Wheelie bar** | Rear-extending bar that stops the front lifting, letting a bike use more torque off the line. |
| **Swingarm extension** | Lengthens the wheelbase, moving weight forward so the bike wheelies less and launches harder. Standard on outlaw builds. |

## Air, weather and the track

| Term | Meaning |
|---|---|
| **Density altitude (DA)** | The altitude the air *behaves* like once temperature, humidity and barometric pressure are folded in. The single most useful weather number in drag racing. |
| **Correction factor** | The multiplier that normalises measured power to a standard day. MotoQuant's dyno importer uses **SAE J1349**. |
| **Prepped track** | Surface treated with traction compound. Grip is far above raw asphalt; the seeded concrete venues in the catalog are all prepped strips. |
| **Track temperature** | Surface temperature, distinct from ambient. Drives tire warm-up and grip. |
| **Headwind / tailwind** | Signed in km/h; negative headwind is a tailwind. Affects both aero drag and ram-air intake pressure. |

## Engine and tuning

| Term | Meaning |
|---|---|
| **Crank vs wheel horsepower** | Manufacturers quote crank; a dyno measures at the wheel, typically 10–15 % lower. MotoQuant's catalog stores what the source stated and notes which it is. |
| **Dyno curve** | Torque against RPM. When a real curve exists the engine reads it directly; otherwise a synthetic curve is generated from peak power/torque and engine character. |
| **ECU flash / piggyback** | Remapping fuel and ignition, either by rewriting the stock ECU or by intercepting its signals (Power Commander, Bazzaz, Aracer). |
| **AFR / lambda** | Air-fuel ratio. ~12.5:1 is typical for maximum power on petrol. |
| **Forced induction** | Turbo, supercharger, or nitrous. In MotoQuant, `boost_type` — an unrecognised value is rejected at engine construction rather than silently ignored. |
| **Two-stroke terms** | *Expansion chamber* (a tuned exhaust that stuffs the charge back in at the resonant "tuned RPM"), *powervalve* (variable exhaust port timing that widens the band), *reed valve*. Two-stroke torque curves are modelled as a narrow Gaussian around the tuned RPM. |
| **Stage 1 / 2 / 3 / 4 (outlaw)** | Build tiers — see `SKILL.md`. "Outlaw" and "open class" both mean stage 4: unlimited budget, full drag prep. |

## Model-internal names (codebase)

| Name | What it is |
|---|---|
| `BikeConfig` | The complete parameter set for one bike: engine, drivetrain, chassis, aero, tires, clutch, staging, environment, rider. |
| `category_tag` | The taxonomy-v2 cluster (e.g. `litre_sport_195p`, `sport_twin_600_1300`, `small_i4_screamer`) that selects per-class launch and clutch behaviour. A bike's cluster changes its physics. |
| `CategoryProfile` | The knob set attached to a cluster: over-clutch factor, engine-decel limit, launch floor, grip scale. |
| `mu_peak` | Peak tire friction coefficient. Rear-tire only — drive traction is rear physics. |
| Pacejka B/C/D/E | Magic-formula tire coefficients; `D` is essentially peak grip. |
| Pinned baselines | GSX-R 1000 K5 **9.9331 s**, YZF-R1 4C8 **10.1436 s**, Hayabusa Gen1 **10.3633 s** — bit-identical, CI-gated. Any change that moves them is a regression unless deliberately re-based with a full benchmark sweep. |
| Surrogate | A trained numpy model that approximates the simulator for fast search inside the build optimizer. It is a *cache of the physics*, regenerated whenever the physics changes. |
| Weighted benchmark sweep | The accuracy measurement: every catalog bike simulated against published real-world ETs, each weighted by source quality (instrumented 1.0 → derived 0.1). Current: **277 matched, weighted mean \|error\| 0.2721 s, bias −0.0047 s**. |
