# Core audit — partial results (2026-10-23)

Run was stopped early at the operator's request (usage budget). Findings below come from the read-only finders; `verdicts` lists the independent verifier votes that completed before the stop. Treat unverified findings as leads, not facts.

## [high/epoch] Engine + clutch-basket inertia is double-counted in the vehicle's effective mass during clutch slip
- Area: physics — `motoquant/physics.py` 782 (m_eff = self.effective_mass(gear)); submodels/drivetrain.py:31
- Verdicts: real=True repro=True; real=True repro=True
- Trigger: Any launch. While the clutch is unlocked, the engine is integrated separately (d_omega_e = T_net/I_e). Even so, effective_mass(gear) still adds (I_e + I_basket)*(i_total/r)^2 to the wheel-side mass for the whole slip phase. On the references that phase is 0 to ~110 km/h, about 3.1 s (K5: rpm stays pinned at 9500 until t=3.107 s at 109.9 km/h).
- Evidence: Gear-1 phantom mass: K5 53.0 kg (m_eff 320.8 vs ~268), R1 53.5 kg, Hayabusa 74.0 kg. Dropping that term while not clutch_locked (/tmp/claude-audit-phys/slipmass.py) changes ET: K5 9.9331->9.3627 (-0.570), R1 10.1436->9.7151 (-0.429), Busa 10.3633->9.7587 (-0.605); K5 60ft 1.960->1.686. Side effect: weight-reduction parts (248 parts use a dry_mass delta) are undervalued about 4-5x, and the 60ft gets SLOWER with less mass. K5 -10 kg gives dET -0.0157 but d60ft +0.0051 (with the fix: -0.0740 / -0.0127). On a turbo Hayabusa, adding a -6.8 kg exhaust after the turbo made ET slower (9.7167 -> 9.7461) (/tmp/claude-audit-phys/masssign.py, fi_parts.py).
- Proposed fix: In run(), when not clutch_locked, use m_eff = effective_mass(gear) - (I_e + I_basket)*(overall_ratio(gear)/r_rear)^2. Re-tune the per-cluster mu_peak_scale/launch knobs against the weighted corpus and re-pin the baselines in the same epoch (ADR-0002). The current calibration absorbs this error.

## [high/safe] Any boost_type (including N2O with a zero shot) floors the NA base engine's density correction at 0.97
- Area: physics — `motoquant/submodels/environmental.py` 94
- Verdicts: real=True repro=True; real=True repro=True
- Trigger: Set forced_induction.boost_type='n2o' (or turbo/SC with target 0) on any bike at a high-density-altitude venue. is_boosted makes power_correction = max(0.97, rho/rho_std). Nitrous adds its own oxidiser and does nothing for the base engine's lost air density. Indian venues are exactly where this bites (Aamby summer DA ~4838 ft, NA correction 0.866).
- Evidence: K5 + aamby_valley_summer: NA 10.1125 s. Same bike with boost_type='n2o' and a 0 hp shot: 9.8773 (-0.235 s from nothing). With a 20 hp shot: 9.7124 (-0.400), so ~59% of the advertised nitrous gain is the floor artifact. At sea level the zero-shot N2O still gives -0.015 s. Parts 100/141/142 (35/50/15 HP kits) all give an identical -0.1612 s on DB Hayabusa; that whole delta is this floor (see the FI-parts finding).
- Proposed fix: Apply the floor only when boost actually compensates for density, i.e. turbo with absolute-pressure boost control. For n2o, sc_roots and anything with zero target boost, use rho/rho_std. If a floor is kept for turbos, compute it from the turbo model (boost target vs local P_atm), not from the boost_type flag. References are NA, so the pins do not move.

## [high/safe] 10 of 20 forced-induction parts deliver zero forced-induction power: missing n2o_stages / target_boost_bar, and their hp deltas are discarded
- Area: physics — `motoquant/database/bridge.py` 440 (is_na rule); data in database/seed.py:6328/6992/7015, seed_catalogs/drag_specific.py:299/331, drag_essentials.py:776
- Verdicts: real=True repro=True; real=True repro=True
- Trigger: Apply part 100/141/142 (N2O kits with n2o_hp_per_stage but no n2o_stages; the default is 0, so hp_add = hp*0). Or apply turbo kits 336/337/338/339/341/581/582 (boost_type=turbo, no target_boost_bar, default 0.0, so zero boost). The turbo kits encode their gain as engine.peak_power_hp deltas (+55..+180 hp), but the bridge scales the dyno curve only when is_na. Overrides are applied first, so boost_type is already 'turbo' and the curve is never scaled. The same rule makes any NA power part (exhaust/ECU) a dead knob when it is applied after a boost part: the result depends on order.
- Evidence: On DB Hayabusa (id 3): part 336 'Stage 1 Hayabusa Kit' (+100 hp) leaves the dyno curve max torque unchanged at 130.00 Nm, target_boost_bar=0.0, and peak_power_hp shows 270 (misleading). dET is only -0.142 s, all of it DA floor + mass. Part 337 (+180 hp) gives -0.124 s. Parts 100/141/142 give an identical -0.1612 s regardless of 15/35/50 hp. Part 340 (SC) also has its +60 hp delta discarded. Exhaust then turbo: 9.7558; turbo then exhaust: 9.7461; the exhaust hp is ignored in the second order (/tmp/claude-audit-phys/fi_parts.py).
- Proposed fix: Data: give the N2O kits n2o_stages=1 and the turbo/SC kits a target_boost_bar (from their specs.boost_psi), and drop their peak_power_hp deltas. Bridge: scale the dyno curve for hp deltas whenever the part itself is not an FI part (decide per part, not by the config's current boost state), or warn when an FI part carries hp deltas. Add a liveness test: every boost_kit/nitrous part must move ET by more than the DA-floor-only baseline.

## [high/safe] Expansion-chamber parts' tuned_rpm override only moves the 2T launch-floor clamp, making 'upgrades' slower
- Area: physics — `motoquant/physics.py` 740-753 (launch floor), engine.tuned_rpm consumer
- Verdicts: real=True repro=True; real=True repro=True
- Trigger: Every production config carries a baked dyno_curve (541/541), so get_torque ignores tuned_rpm, powervalve, expansion_chamber and reed_valve. tuned_rpm survives only as the 2T launch floor: floor_rpm = tuned_rpm * launch_floor_factor (1.0). The 14 expansion-chamber parts override tuned_rpm, pinning the engine at that rpm through the whole slip phase without moving the torque band. Nothing bounds floor_rpm to the curve or redline: RD400 + tuned 11000 > redline 8260.
- Evidence: Part 428 (+8 hp, +4 Nm, -2.8 kg) on NSR250R SP: dET +0.702 s (slower); TZR250 (part 434): +0.705; RD400 (part 425): +0.141. The same part 428 without the tuned_rpm override: -0.623 (NSR), -0.613 (TZR), -0.654 (RD400). tuned_rpm alone on NSR250R (stock 9500): 8200 -> +1.13 s, 11000 -> +1.52 s. powervalve/expansion_chamber/reed_valve flags alone: dET exactly 0.000 (/tmp/claude-audit-phys/probe_parts.py, nsr.py).
- Proposed fix: When a dyno_curve is present, derive the 2T floor from the curve's actual torque-peak rpm, or ignore tuned_rpm overrides, and clamp floor_rpm <= redline. Have pipe parts reshape or scale the curve rather than move tuned_rpm. Alternatively drop the tuned_rpm override from the 14 parts. Document the 2T flags as dead on curve-carrying configs, or wire them into the curve generator. References are 4T with floor 0, so the pins are unaffected.

## [medium/epoch] Over-clutch extra torque plus the launch-floor clamp creates sustained torque from nothing for the whole slip phase
- Area: physics — `motoquant/physics.py` 714-759
- Verdicts: real=True repro=True; real=True repro=True
- Trigger: Any cluster with over_clutch_factor>0 and launch_floor_factor>0. The engine starts at the floor (peak_torque_rpm). T_transmitted = T_e + min(headroom*ocf, decel*I_e) decelerates omega_e, then the floor clamp resets omega_e every step. The 'inertia energy' extra torque is therefore delivered indefinitely, though the code comment says it is 'briefly drawing energy from engine inertia'. The clutch cap is >=374 Nm everywhere, so decel*I always binds.
- Evidence: Free torque during slip at the floor, catalog medians (/tmp/claude-audit-phys/freetq.py): other +45% (n=114), cruiser_1300p +56%, two_stroke +59%, small_i4 +86% (ZX-25R +101%), mid_twin_500_700 +27%, entry_200_300 +9%. An energy-conserving clamp (refund the clamped delta-omega*I/dt from T_transmitted) gives: ZX-25R 13.517->15.832 (+2.32 s), Splendor Plus +2.33, RX100 +1.57, Ninja 400 +0.18, R15 V4 +0.17, Fat Bob +0.055 (/tmp/claude-audit-phys/floorcons.py). The current cluster calibration depends on this non-physical term.
- Proposed fix: Make the term honest: only transmit the extra torque while omega_e is actually above the floor, by subtracting the clamp's refunded inertia torque. Alternatively rename max_engine_decel_rads2 as an explicit empirical 'launch torque multiplier' so nobody 'fixes' it accidentally. Either path needs a full re-tune in an epoch, and the Rust port must replicate the current behaviour bit-for-bit until then.

## [medium/safe] Zero-hysteresis rev limiter (torque 0, then negative from parasitic) chatters at 1 kHz, so run_top_speed never detects the plateau
- Area: physics — `motoquant/submodels/engine.py` 28 (limiter), physics.py:1064 (plateau detector)
- Verdicts: real=True repro=True; real=True repro=True
- Trigger: Any bike that is rev-limited in top gear before it is aero-limited. Above 1.02*redline, torque is 0; physics then subtracts parasitic/omega, so drive goes negative. Below the limit torque returns at full value. The accel channel flips sign every few steps and |a| never stays below 0.05 m/s^2 for 1.5 s.
- Evidence: Catalog scan of all 541 current configs (/tmp/claude-audit-phys/tsscan.py): 88 are limiter-bound at top speed, and all 76 'reached_plateau=False' cases are among them. Examples: Ninja 400 reports time_to_terminal 111.7 s / 6254 m but was within 0.2 km/h of terminal at 27.7 s / 1187 m; CBR600RR 109.7 s vs 13.2 s / 543 m; CBR1000RR 2004 106.7 s vs 12.0 s / 516 m. K5 with a 70T rear: accel -2.61..+1.45 m/s^2 with 1429 sign flips in the last 2000 samples; reported 111.2 s vs actual 11.1 s. terminal_power_kw/rpm/gear are sampled at an arbitrary chatter peak. These fields are exposed by /api/simulate/topspeed, the MCP server and the chat agent. Hysteresis alone does not fix detection; quarter-mile ET change is negligible (+0.0004 s).
- Proposed fix: Model the limiter like the speed limiter (clamp a_net <= 0 when rpm >= 1.02*redline in top gear, and do not subtract parasitic while fuel is cut). And/or detect the plateau from windowed delta-v or the mean of a over plateau_window_s instead of instantaneous |a|. References never reach the limiter, so the pins are unaffected.

## [medium/epoch] slip_ratio drops from 0.05 to ~0 exactly at the traction limit, so a spinning tire heats less than a gripping one
- Area: physics — `motoquant/physics.py` 814-819
- Verdicts: real=True repro=True; real=True repro=True
- Trigger: Every traction-limited step. Unclipped: slip = |F|/F_max*0.05, which approaches 0.05 at the limit. Clipped: slip = min(0.3, (F_demand-F_max)/F_max*0.1), which starts at 0. slip feeds Q_friction = |F_x|*|v*slip| in the tire thermal model and the published 'slip' channel.
- Evidence: K5: 3554 clipped steps. slip just below the limit has mean 0.0497; when clipped, min 0.00000 and median 0.00933. Making it continuous (0.05 + excess*0.1) raises peak tire temp 98.3->106.2 C and moves ET +0.0626 s (K5), +0.0236 (R1), +0.0557 (Busa) (/tmp/claude-audit-phys/slipdisc.py). The output slip channel shows near-zero slip during wheelspin.
- Proposed fix: Use a continuous slip estimate (e.g. 0.05 + k*(F_demand-F_max)/F_max when clipped), or derive slip from the Pacejka inverse. Re-calibrate and re-pin in an epoch.

## [medium/safe] Clutch type, slipper_ratio, engage_rpm (non-slider) and drivetrain.clutch_type are dead; the whole clutch_kit category is ET-neutral
- Area: physics — `motoquant/physics.py` 646 (only CLUTCH_SLIDER is special-cased); submodels/clutch.py never called by run()
- Verdicts: not yet verified
- Trigger: Apply any clutch part. run() calls neither ClutchModel.torque nor anything that reads clutch_type except 'slider'. multistage, slipper and lockup behave identically. T_transmitted = min(|T_e|, cap) with cap >= 374 Nm, so mu_static/spring_preload/plate_count never bind. drivetrain.clutch_type and drivetrain.clutch_engage_rpm are duplicate fields nothing reads.
- Evidence: 22 clutch parts measured on compatible bikes (/tmp/claude-audit-phys/probe_parts.py): every |dET| <= 0.0045 s and most exactly 0.0000 (mass only). This includes the three 'Multistage Lock-Up Clutch' parts 574/575/576 (dET 0.0000/0.0000/-0.0006) and slipper kits 74/75/76/235/250, whose every param path is dead. K5 with clutch_type='slipper', engage_rpm=4200 or mu_static=0.48 gives dET exactly 0.
- Proposed fix: Dispatch CLUTCH_MULTISTAGE (and slipper overrun) through ClutchModel in the slip branch, leaving the 'lockup' path that the references use untouched. Delete or alias the drivetrain.clutch_type/clutch_engage_rpm duplicates. Add a liveness test so clutch_kit parts cannot all be zero. Until then, flag clutch parts as 'not simulated' in ROI/optimizer output.

## [medium/safe] EnvironmentParams.track_prep/track_prep_passes are never read; venue VHT is ignored and the 3 reference DB rows get VHT grip everywhere
- Area: physics — `motoquant/models.py` 724 (EnvironmentParams.track_prep); physics.py:204 reads tires.track_prep_type; nlp.py:408 writes the dead field
- Verdicts: not yet verified
- Trigger: NL queries mentioning VHT/PJ1/rubber write config.environment.track_prep, which has zero effect. nlp's 'rubber' also doesn't match TRACK_RUBBER='rubber_buildup'. venues.has_vht (=1 for Santa Pod/Pomona/Gainesville/Sydney/Dubai/Al-Ain) is never mapped. Physics reads only TireParams.track_prep_type: 'vht' on DB rows 1-3 (copied from defaults.py), 'none' on the other 538.
- Evidence: DB Hayabusa (id 3) at the default Aamby env: setting environment.track_prep='vht' gives dET 0.0000. Its tire-level VHT is worth 0.472 s (10.484 vs 10.956 with tires.track_prep_type='none'). So /api/simulate?bike_id=1..3 carries a +12% grip bonus at unprepped venues (Aamby has_vht=0, Bonneville), while catalog bikes never get it at has_vht venues (/tmp/claude-audit-phys check inline).
- Proposed fix: Have physics take the prep from the environment, e.g. mu_prep from env.track_prep (set by venue has_vht / NL / API), falling back to tires.track_prep_type for legacy configs. Keeping the factory references' tire VHT with env prep 'none' keeps the pins. Fix the nlp 'rubber' -> TRACK_RUBBER mapping.

## [medium/safe] At-wheel dyno curves cancel drivetrain efficiency, so chain-efficiency parts and parasitic changes are dead on 35 configs
- Area: physics — `motoquant/submodels/engine.py` 34 (T_base /= self.eta_dt) with drivetrain.py wheel_torque *eta_dt
- Verdicts: not yet verified
- Trigger: Any config whose dyno_curve.is_at_wheel=True (35 current DB configs, incl. R15 V4, Apache RTR 200 4V, ZX-10R 04-15, Panigale V4, H2, ZX-14R, R1/R6 variants, plus the 3 references). The crank torque is rebuilt with the CURRENT config's eta and immediately multiplied back by the same eta, so a chain upgrade cannot change wheel torque. Parasitic losses are also skipped for at-wheel curves.
- Evidence: K5 with drivetrain.chain_efficiency x1.02 (what the 21 chain parts do): dET +0.000000. Removing the alternator and oil pump: dET +0.000000. DB scan: 35 is_current configs carry at-wheel curves.
- Proposed fix: Record the drivetrain efficiency at curve-measurement time on DynoCurve (e.g. eta_ref, defaulting to the config's eta at import). Then convert T_crank = T_wheel/eta_ref and deliver T_crank*eta_current. Unmodified configs stay bit-identical; part deltas become live.

## [low/epoch] Rider launch lean (80 mm) is applied as a whole-vehicle CoG shift instead of being scaled by rider mass fraction
- Area: physics — `motoquant/models.py` 640-651 (RiderParams.cog_offset) consumed by submodels/weight_transfer.py:32 and wheelie.py:27
- Verdicts: not yet verified
- Trigger: Every launch. launch_forward_shift_mm documents the rider's forward lean. Moving a 75 kg rider 80 mm moves the 258 kg combined CoG only ~23 mm, but L_f_eff = L_f - 0.080 is applied directly. That removes ~144 N of static rear load (~12%) at launch. There is also a hard -0.03 m step at t = tuck_transition_time_s, a discontinuous load jump.
- Evidence: Scaling the offset by m_rider/m_total (0.29/0.28/0.24): K5 9.9331->9.9001 (-0.033), R1 10.1436->10.0870 (-0.057), Busa 10.3633->10.3285 (-0.035); 60ft improves ~0.045 s. The references are traction-limited, not wheelie-limited (wheelie limit 14.5-15.3 m/s^2).
- Proposed fix: Scale cog_offset by rider_mass/total_mass inside WeightTransfer/Wheelie (and the -0.03 tuck offset), and smooth the transition end. Re-tune in an epoch.

## [low/safe] Swingarm extension stretches both L_f and L_r by front_weight_pct instead of only moving the rear axle back
- Area: physics — `motoquant/models.py` 105-117 (wheelbase_m / L_f / L_r)
- Verdicts: not yet verified
- Trigger: Apply any of the 8 chassis.swingarm_extension_mm parts. wheelbase_m includes the extension but front_weight_pct is held constant, so L_r grows by ext*fwp (~0.5*ext) and L_f grows by ext*(1-fwp). In reality the front axle-to-CoG distance is unchanged, L_r grows by the full extension, and the static front fraction rises.
- Evidence: K5 +101.6 mm: model L_r 0.731->0.783 (wheelie a0 15.45 m/s^2), dET +0.125. Geometric L_r 0.832 (a0 16.32), dET +0.312. +254 mm: model +0.297 vs geometric +0.861. Hayabusa 4in: +0.099 vs +0.266 (/tmp/claude-audit-phys inline run). Extension parts are mis-valued on wheelie-limited and traction-limited bikes alike.
- Proposed fix: Store the CoG position relative to the front axle: L_f = L_stock*(1-fwp), L_r = L_stock*fwp + ext, and derive static loads from that. References have ext=0, so the pins don't move.

## [low/safe] Intercooler charge-temp penalty is applied only WHEN an intercooler is fitted; 'none' gets no penalty
- Area: physics — `motoquant/submodels/forced_induction.py` 51-54
- Verdicts: not yet verified
- Trigger: A turbo config with intercooler_type='none' vs 'a2a'/'a2w'. The temp_penalty (1 - 0.02*(1-eta_ic)*bar) sits inside `if intercooler_type != 'none'`, so the non-intercooled turbo makes the most torque.
- Evidence: Hayabusa turbo at 1 bar, torque mult: none 1.9928 > a2w(0.95) 1.9908 > a2a(0.75) 1.9828 > a2a(0.5) 1.9729. ET differences are sub-ms here because of traction limiting, but the sign is wrong for every turbo ROI/optimizer comparison.
- Proposed fix: Treat 'none' as eta_ic=0 (the maximum penalty) and apply the penalty unconditionally for turbo/SC.

## [low/safe] Unknown or misspelled category_tag silently falls back to the 'unknown' profile; a None tag re-derives a different cluster from wheel hp
- Area: physics — `motoquant/category_profiles.py` 527-531 (get_profile); physics.py:227-239
- Verdicts: not yet verified
- Trigger: A saved config JSON (config_io.load_config doesn't validate) with category_tag 'litre-sport-195+' (the old sweep-label style), a case variant, or 'unknown'. Or a config with category_tag=None, whose derivation uses peak_power_hp, which on at-wheel references is the 160 hp wheel figure.
- Evidence: K5 with tag 'litre-sport-195+' or 'Litre_Sport_195P' gets profile 'unknown': 0 warnings, dET +0.371 s. With tag None it derives 'litre_sport_600_1000', dET +0.041 s.
- Proposed fix: Log a warning (or raise in config_io/get_profile) for tags not in _PROFILES, and normalise case. Prefer spec crank hp for derivation or persist the tag.

## [low/epoch] ECU-flash 'two-step' overrides make litre bikes launch slower because the non-two-step path already launches at peak-torque rpm
- Area: physics — `motoquant/submodels/staging.py` initial_omega_e (two_step -> launch_rpm, else peak_torque_rpm)
- Verdicts: not yet verified
- Trigger: Parts 44/45/46/47 set staging.two_step=True, launch_rpm=8500 on K5/R1, whose peak_torque_rpm is 9500/9000. With over_clutch 0 the engine is held at launch rpm for the entire slip phase, so 'launch control' lowers it.
- Evidence: Staging portion of each part (full part vs part without staging overrides): K5 Stage 1 +0.0028 s, Stage 2 +0.0025, R1 Stage 1 +0.0080, Stage 2 +0.0046. Launch control is credited negatively in ROI.
- Proposed fix: Model two-step as max(launch_rpm, the clutch-held default) or wire the epoch-gated staging dead-time so launch control has a real benefit. Otherwise drop the staging overrides from ECU parts.

## [low/safe] run(distance<=0) raises UnboundLocalError and run_top_speed(max_time<dt) raises ValueError
- Area: physics — `motoquant/physics.py` 969 (out_a[step] = a_net / G after a zero-iteration loop); 1077 (np.argmax on empty)
- Verdicts: not yet verified
- Trigger: MotoQuantEngine(cfg).run(distance=0.0), run_distance(0) or run(distance=-5): the loop never executes but `x >= distance` triggers the final-store block, which references a_net. run_top_speed(max_time=0.0005) produces empty arrays and np.argmax fails. The API's pydantic bounds guard this, but direct callers (CLI/MCP local backend/analysis code) are unguarded.
- Evidence: distance=0.0 gives UnboundLocalError: cannot access local variable 'a_net'; run_distance(0) gives the same; run_top_speed(max_time=0.0005) gives ValueError: attempt to get argmax of an empty sequence.
- Proposed fix: Validate distance > 0 and max_time >= dt at the top of run()/run_top_speed() and raise ValueError with a clear message. Guard the final-store block with step > 0.

## [high/safe] to_config() overrides every config's curve with a stale dyno_curves row: CLI, chat and NL sims disagree with the API for 508 of 541 bikes
- Area: data — `motoquant/database/bike_repo.py` 457-473
- Verdicts: not yet verified
- Trigger: `python -m motoquant.run sim --bike-id 4093` (MT-15 V1), or any chat-agent or NL tool sim of a catalog bike. These go through `db.bikes.to_config()` (run.py:698/811/1142, llm/agent.py:279/640, llm/runner.py, nlp.py:385). `/api/simulate` and the golden or sweep scripts use `db_row_to_config()` with no override.
- Evidence: `to_config()` loads `SELECT * FROM dyno_curves WHERE bike_config_id=? ORDER BY created_at DESC LIMIT 1` and passes it as `dyno_override`, replacing `engine_params.dyno_curve`. `reseed_configs_from_specs.py` and every patch_*.py rewrite only the bike_configs JSON blobs and never touch dyno_curves. In the shipped DB, comparing each current config's dyno_curves row with its engine_params curve gave: 508 stale, 33 identical, 0 missing. 506 of the stale rows still carry is_at_wheel=1 (pre-Aug-8 at-wheel semantics, no 1.08 crank recal), e.g. GSX-R 1000 2017 peak 117.6 vs 127.0 Nm. Measured ET with to_config minus db_row_to_config: MT-15 V1 -1.987 s (17.219 vs 19.205; the CLI prints 17.2186 while the API path gives 19.205), Hero Passion XPro -0.387, YZF-R9 -0.239, bike 217 -0.232, 264/800 -0.196, plus about +0.02 s on most litre bikes. Over a 34-bike sample, mean |d| = 0.118 s.
- Proposed fix: Make bike_configs.engine_params the single source of truth. Either drop the dyno_override lookup in `to_config()` (use the embedded curve), or have `create_config`/reseed/patches upsert the dyno_curves row for the config id they rewrite. Add a regression test asserting `to_config(id)` and `db_row_to_config(row)` give the same ET. Reference pins are unaffected: ids 1-3 are among the 33 identical rows.

## [high/safe] Importer never sets DrivetrainParams.drive_type, so every shaft, belt and CVT bike runs chain efficiency and the chain slack model
- Area: data — `motoquant/scraper/importer.py` 873
- Verdicts: not yet verified
- Trigger: Any catalog shaft bike, e.g. /api/simulate for bike_id 128 (BMW R 1250 GS), 224 (K1300S), 112 (VMAX 1700), 208 (FJR1300), 125/4586 (Rocket 3), 243, 252, 702, 725, 794, 798, 1256, 3126, 4611, 210.
- Evidence: `_build_drivetrain_from_spec` returns `DrivetrainParams(...)` without a drive_type argument, so the default 'chain' applies. Shipped DB: drive_type counter = {'chain': 541}. physics.py:202 uses `drivetrain_efficiency()`, which applies shaft_efficiency only when drive_type=='shaft', and submodels/chain.py applies the launch slack only to chain bikes. So shaft_efficiency is a dead knob catalog-wide, which contradicts the defaults.py comment 'a shaft bike now pays ~8% more loss than a chain bike'. Affected: 18 shaft, 24 belt (HD/Indian/Buell/Chinchilla) and 2 CVT bikes. Measured on the DB path with drive_type flipped to shaft: eta 0.946 -> 0.829, ET +0.306 (R1250GS 11.658->11.964), +0.371 (VMAX 1700), +0.312 (FJR), +0.376 (K1300S), +0.281 (K1600), +0.328/+0.302 (Rocket 3 R/Storm R), +0.256 (Tiger 1200).
- Proposed fix: Set drive_type in the importer from spec.final_drive when declared, else from the sentinel/inference (shaft for BMW R/K, Guzzi, FJR, VMAX, Rocket 3, Tiger 1200, Super Tenere, R 18; belt for HD/Indian/Buell/Benda belt and CVT scooters). The default shaft_efficiency of 0.85 is pessimistic (a real shaft loses roughly 3-6% more than a chain), so calibrate it to about 0.92-0.94 before wiring. Then reseed and run the full weighted sweep. Reference bikes are chain, so the pins hold.

## [high/safe] `db seed` / `make db` on the shipped motoquant.db is not idempotent and silently reverts curated patch data
- Area: data — `motoquant/database/seed.py` 9269
- Verdicts: not yet verified
- Trigger: `make db` (Makefile:34-36 runs `db init` and `db seed` on the tracked motoquant.db), or `python -m motoquant.run db seed`. The CLI also suggests running `db seed` when a parts search returns nothing (run.py:1262).
- Evidence: Ran `seed_all()` on a copy of the shipped DB and diffed against the original. parts: 468 rows changed: price_inr reverted on 279 (e.g. Driven 520 14T 3719.2->2600), model_name on 225 (re-introduces the brand-doubled names patch_2026_06_14 removed, e.g. 'GPR Stabiliser EVO...'; brand-prefixed names 0->225), price_usd on 210, mrp_inr on 113, retailer on 112, availability on 36 (Bazzaz units 'discontinued'->'in_stock'), param_deltas on 12 (Akrapovic Hayabusa mass -6.8->-6.3), fitment_rules on 138 (6 at match level). last_price_check was set to today on all 593 parts, because the parts_repo.create upsert at line 214 stamps date('now'). tire_models: 38 changed (available_india 0->1 on 24 tires that patch_2026_07_13 flagged discontinued; 11 prices; 5 size designations). bike_tire_fitments: +134 / -32 OEM rows (1783->1885), undoing patch_2026_08_08. bike_configs/dyno_curves: +3 phantom reference versions, because the stored blobs still carry the removed headwind_ms/crosswind_ms keys and that defeats the create_config byte-equality guard. Each patch_* script run individually on the shipped DB is a no-op, so the shipped DB is at the chain fixpoint and seed_all is what diverges.
- Proposed fix: Make seed upserts insert-only for existing rows: do not overwrite price/name/availability/fitment_rules on an existing (brand, part_number) or tire, and do not bump last_price_check unless the price actually changed. Alternatively, have `db seed` refuse to run on a populated DB unless --force is given, and change `make db` to target a scratch path. Fold the curated patch values back into seed sources. Strip dead keys in the create_config comparison.

## [medium/safe] Importer discards BikeSpec.final_drive and chain_pitch: 139 curated specs get a heuristic pitch, giving phantom chain parts on shaft/CVT/belt bikes and none on real chain bikes
- Area: data — `motoquant/scraper/importer.py` 475-553
- Verdicts: not yet verified
- Trigger: Parts fitment for bike 210 Super Tenere XT1200Z (spec declares final_drive 'shaft'), 725 BMW R 18 (shaft), 2651 TVS NTorq (declares belt/CVT), 4636 Benda Chinchilla 500 (declares belt), 247 H-D Pan America 1250 (real chain), 203 Honda CB1100 (real 530 chain), 17 YZF-R1 (2007-2008).
- Evidence: BikeSpec has `final_drive` and `chain_pitch` fields (spec.py:66-67) and known_bikes sets them, but `_infer_chain_pitch()` never reads them. It uses make and displacement rules instead. Of the specs, 139 declare a value that the inference overrides: e.g. YZF-R1 2007-08 declares 530 but the DB stores 520, while reference id 2 (the same R1 4C8) stores 530; RE Classic/Meteor/Hunter 350 declare 428 but get 520. Shaft/CVT/belt bikes with phantom pitches match chain and sprocket parts: Super Tenere 525 (14 parts), R 18 530 (21), NTorq 428 (12), Chinchilla 520 (24). Real chain bikes get None and lose parts: Pan America, because the H-D rule says 'belt except X440' (H-D media kit: Final Drive Chain 19/48), loses 14 parts; CB1100, wrongly listed in _NON_CHAIN_MODELS as 'shaft drive' (JT lists 530 chain, 18/39-40), loses 23 parts. patch_2026_07_06 [A] reports these bikes as 'already clean'.
- Proposed fix: In `_infer_chain_pitch` and `_build_drivetrain_from_spec`, honour spec.final_drive ('shaft'/'belt' gives None plus drive_type) and spec.chain_pitch when it is a numeric code, before falling back to heuristics. Remove CB1100 from _NON_CHAIN_MODELS and add 'Pan America' to the H-D chain exceptions. Add 'R 18' to the BMW shaft list and NTorq to the non-chain list. Then reseed.

## [medium/safe] Ninja H2 library dyno curve is about 1.8x real torque (243 Nm at-wheel), so sim trap is 32 km/h over the benchmark
- Area: data — `motoquant/scraper/dyno_curves.py` 1062
- Verdicts: not yet verified
- Trigger: /api/simulate for bike_id 45 (Kawasaki Ninja H2 2015-2023), which matches KNOWN_DYNO_CURVES ('kawasaki','ninja h2',2015,2024).
- Evidence: `dyno_kawasaki_h2()` returns torque peaking at 243 Nm (5500-6000 rpm) flagged is_at_wheel=True. Its own docstring says '(at wheel?! Claimed, may be crank)'. The real H2 makes 133.5-141.7 Nm crank at 10,500 rpm, and the DB headline is 141.7 Nm. The stored curve implies 294.9 hp at-wheel against a 228 hp crank claim, which is the only library curve above its rated power. Sim: ET 9.728 s, trap 279.1 km/h, peak wheel power 267 hp, top speed 327.6 km/h. Benchmark in scripts/validation_sweep.py:93 is 9.62 s @ 247 km/h (MCN 2015). ET only looks right because the launch is traction-limited.
- Proposed fix: Replace the curve with a sourced H2 dyno trace (about 200 whp, about 125-130 Nm wheel peak near 10-11k rpm) or drop the library entry so the spec path's synthetic crank curve is used. Then reseed bike 45 and regenerate golden and surrogate.

## [medium/safe] Synthetic torque curve in the 50-70 Nm band keeps power rising to redline, 16% past rated×ladder×recal, on 33 bikes
- Area: data — `motoquant/defaults.py` 154
- Verdicts: not yet verified
- Trigger: Any catalog bike with peak_torque_nm in [50,70) whose redline sits well above peak_power_rpm: MT-07, Ninja/Z 650, SV650, RS 660/Tuono 660, Tracer 7, all RE 650 twins, Tenere 700, Versys 650, etc.
- Evidence: Beyond peak_power_rpm the curve decays only to T_at_redline_factor=0.88. The importer sets redline = 1.32 × peak_power_rpm for twins under 700cc (importer.py:634), so power at redline = 0.88×1.32 = 1.162× the calibrated peak. In the shipped DB all 33 bikes in this band show curve max power exactly 1.162× expected, peaking AT redline: MT-07 rated 74 hp @9000 gives 92.8 hp @11880; Interceptor 650 rated 47.2 @7250 gives 62.2 hp @9570 (the real 650 twin limiter is about 7.5-8k); RS 660 100 hp gives 125.5 hp @13860. Capping power at its peak-rpm value beyond peak_power_rpm changes ET by +0.32 s (MT-07 12.224->12.545, trap 185.2->177.7), +0.26 (Interceptor), +0.20 (RS 660) and +0.30 (Ninja 650). Note R9 and RC213V-S separately carry inconsistent specs.
- Proposed fix: Constrain the post-peak segment so P(rpm) never exceeds the value at peak_power_rpm (T ≤ T_at_peak_power·ω_pp/ω), and/or reduce the twin redline factor. The mid_twin/sport_twin cluster knobs were calibrated around the inflated curves, so re-tune them with scripts/tune_cluster_knobs.py and regenerate golden and surrogate in the same pass. References build hand-made curves, so the pins hold.

## [medium/safe] Validator lets physically impossible power/torque combinations through (warning only) and its hp/cc check is ~10× too loose
- Area: data — `motoquant/scraper/validator.py` 80, 209-220
- Verdicts: not yet verified
- Trigger: `import --spec-json`, the chat estimator (llm/estimator.py) or scrape import with e.g. YZF-R9: peak_power 117.4 hp @12500, peak_torque 93 Nm @11500. Or a typo spec: 599cc, 450 hp.
- Evidence: There is no check that the power at the torque peak (T·ω) is ≤ rated peak power, or that torque at the power peak is ≤ rated peak torque. 14 catalog specs violate this by more than 5%: Tesi 1D 1.37×, YZF-R9 1.28× (93 Nm @11500 = 150 hp > 117.4), RC213V-S 1.20× (118 Nm @11500 = 190 hp > 159), FZ-X, Duke 250, 890 Duke, Daytona 955i... validate_spec(R9) returns valid with one 'Torque inconsistency' warning. The resulting curve makes 161.8 hp (1.28× expected), and the R9 sims 10.427 s / 241 km/h against 10.804 s / 224.9 km/h with real rpm points (10000/7000). HP_PER_CC_MAX = 3.0 hp/cc (real NA max is about 0.25), so a 599cc NA bike at 450 hp / 230 Nm validates with zero warnings or errors.
- Proposed fix: Make it an error, or at least confidence-gate it, when P(T_peak) > 1.05·P_peak or T(P_peak) > 1.05·T_peak, or when peak_torque_rpm > peak_power_rpm for 4T. Set HP_PER_CC_MAX to about 0.33 NA (with a boosted/2T allowance). Fix the R9 (10000/7000), RC213V-S and Tesi 1D specs, then reseed.

## [medium/safe] validate_spec() mutates the spec, injecting generic I4 gear ratios and car-like Cd 0.32 that bypass the importer's Tier-1 lookup
- Area: data — `motoquant/scraper/validator.py` 253-269
- Verdicts: not yet verified
- Trigger: Any spec reaching import_batch/import_spec, `run.py import --spec-json`, or the chat estimator (validate_spec runs before spec_to_bike_config) with gears set but no gear_ratios, or no cd. Example: Yamaha 'YZF-R15 V4', 155cc, gears=6, no ratios, no cd.
- Evidence: validate_spec does setattr(spec.gear_ratios=DEFAULT_GEAR_RATIOS_6=[2.6,2.105,1.75,1.5,1.333,1.2]) and spec.cd=0.32. `_build_drivetrain_from_spec` only uses the Tier-1 lookup when spec.gear_ratios is falsy, so the R15's service-manual cassette [2.833..0.84] is replaced, and Cd 0.42 becomes 0.32. Measured: without validation ET 18.196 s and top speed 144.9 km/h; after validation ET 18.279 s and top speed 120.6 km/h (rev-limited in a non-overdrive 6th). The reseed path never validates, so reseed and import diverge for such specs. All 538 curated specs carry cd and ratios, so the shipped DB is unaffected; it is latent for user, estimator and scrape inputs.
- Proposed fix: Remove the auto-fill of gear_ratios and Cd from validate_spec (or put it on a copy behind an explicit flag). Let spec_to_bike_config's Tier-1/Tier-2 lookup and category aero own the defaults, and report the would-be fills as warnings only.

## [medium/safe] 7 turbo kits set boost_type with no target_boost_bar, so their peak_power_hp delta is dropped: the '+180 hp' ORP twin-turbo equals the '+100 hp' kit
- Area: data — `motoquant/database/bridge.py` 442
- Verdicts: not yet verified
- Trigger: Apply part 336 (Velocity Turbo Stage 1 Hayabusa, +100 hp), 337 (ORP Twin-Turbo, +180 hp), 338 (HKS R1), 339 (Garrett Panigale V4, +85), 341 (Trask V-twin, +85), 581 (Trask Assault M8, +75) or 582 (Trask Tornado M8, +55). This happens in the optimizer, outlaw pipeline, `parts --impact` and quick-sim with part_ids.
- Evidence: apply_part_to_config scales the dyno curve only when `is_na`, and these parts override forced_induction.boost_type='turbo' while leaving target_boost_bar at 0.0. So the +hp delta never reaches the curve and the boost model gets 0 bar. On Hayabusa (id 3), peak wheel power goes 114.3 -> 123.7 kW for BOTH 337 (+180 hp) and 336 (+100 hp). ET: -0.124 s (337) vs -0.142 s (336). Compare part 96 Schnitzer turbo (0.827 bar, no hp delta): -0.767 s, 233 kW. Trask 341 on Scout: -0.177 s, against a claimed +85 hp. Seeded in seed_catalogs/drag_specific.py:299/331 and drag_essentials.py:776.
- Proposed fix: Give each kit a target_boost_bar (plus spool/intercooler) consistent with its claimed gain, and drop the dead peak_power_hp/peak_torque_nm deltas. Alternatively, have apply_part_to_config warn when a part sets boost_type≠na with target_boost_bar 0 and also carries a power delta. Patch the shipped DB via an idempotent patch script.

## [medium/safe] parts_repo.search fails open: preset bikes in the optimizer get the first 200 parts alphabetically, compatible or not, and unknown bike ids return the whole catalog
- Area: data — `motoquant/database/parts_repo.py` 288-306
- Verdicts: not yet verified
- Trigger: POST /api/optimize/build (or the job/outlaw variants) with bike_preset='hayabusa' or 'gsxr1000_k5' and no bike_id. api.py passes bike_model_id=req.bike_id=None into optimize_build, which calls parts_repo.search(bike_model_id=None, limit=200). Also search(bike_model_id=999999).
- Evidence: With bike_model_id=None, no compatibility filter runs and SQL LIMIT 200 is applied in brand order: 132 of the 200 candidates are incompatible with the K5 (e.g. 'Agency Power Full System Rocket 3', 'Agostini Full System Moto Guzzi V85 TT', 'AFAM 525 Premium Chain'), and 133 of the 201 K5-compatible parts are never considered. With a nonexistent id the `if bike_row:` guard skips filtering and all 593 parts are returned as compatible, against 205 for bike 3.
- Proposed fix: Resolve presets to their DB model ids (1/2/3) before optimizing. In search(), return [] when a bike_model_id is given but not found, and never apply a pre-filter LIMIT on the optimizer path.

## [medium/safe] Sport-class Cd ×0.55 normalisation leaves catalog litre bikes with half the reference CdA: the same R1 4C8 tops 358 km/h in the catalog vs 288 as the reference
- Area: data — `motoquant/scraper/importer.py` 1060
- Verdicts: not yet verified
- Trigger: /api/simulate/topspeed for catalog sport bikes without a speed limiter, e.g. 17 YZF-R1 (2007-2008), 295 M 1000 RR (2025), 291 CBR1000RR-R SP 2024, 302 Superveloce, 130 RS 660.
- Evidence: Reference id 2 'YZF-R1 4C8' (2007-08) has cd 0.72 / fa 0.44, CdA 0.317: ET 10.345, trap 227.6, top 288.0 km/h. Catalog id 17 'YZF-R1 (2007-2008)', the same motorcycle, has cd 0.396 (0.72×0.55), CdA 0.174: ET 10.262, trap 241.4, top 358.0 km/h. Same pattern for K5 ref (CdA 0.315, top 299.9) vs GSX-R 1000 2007-08 (0.173, 358.9). Other catalog top speeds: M 1000 RR 2025 410.7 km/h, CBR1000RR-R SP 2024 405.4, Superveloce 397.1, RS 660 (100 hp) 322.7. The docstring's claim that references use tuck Cd 0.32 contradicts defaults.py (0.70). This is the queued 'topspeed +24 bias' item; it is still live and also duplicates the R1 4C8 entity with divergent results.
- Proposed fix: Re-base catalog sport aero on the reference CdA convention (about 0.30-0.33 m² tucked for litre sport plus rider) instead of cd×0.55, re-tune clusters, and regenerate. At minimum, dedupe catalog id 17 against reference id 2.

## [low/safe] Same motorcycle stored as 2 rows with overlapping years and different physics: user-visible ET differs by up to 0.66 s
- Area: data — `motoquant/scraper/known_bikes.py` 1855, 3510, 11629
- Verdicts: not yet verified
- Trigger: Picking either row of these pairs in the bike picker: 78/100 Continental GT 650, 79/99 Interceptor 650, 101/4092 Super Meteor 650, 190/318 G310RR, 193/4592 Tuono 457, 307/758 Raider 125, 313/2653 SP 160 vs SP160, 316/2186 V-Strom SX 250 (plus 53/231 848 EVO, which is known/queued).
- Evidence: DB-path ET for each pair: Continental GT 650 14.153 vs 13.531 (mass 202 vs 182), Interceptor 650 14.175 vs 13.654, SP 160 19.135 vs 19.794, Tuono 457 13.491 vs 13.263, Super Meteor 14.257 vs 14.085, G310RR 15.701 vs 15.816. The Aug-8 dedup only collapsed exact-key duplicates; these survive because names or year ranges differ slightly.
- Proposed fix: Adjudicate each pair to one spec (keep the sourced mass/power), merge rows via an idempotent patch that re-points fitments/sim_runs/archetypes, and add a test for overlapping (mfr, normalized-name, years) pairs.

## [low/safe] Several catalog cassettes or final drives are inconsistent with siblings and reality (Pan America, Rocket 3 R, Low Rider ST/Road Glide, 2025 overdrive sets)
- Area: data — `motoquant/scraper/known_bikes.py` 5056, 9212, 11008, 11042
- Verdicts: not yet verified
- Trigger: Sims or top-speed runs of bikes 247, 125, 133, 134, 296, 295, 302, 39.
- Evidence: Pan America 1250 spec 19/43 (2.263); the H-D media kit says chain 19/48 (2.53). ET 11.515 vs 11.599 with real gearing. Rocket 3 R spec carries fabricated chain sprockets 18/47 (2.611), while Rocket 3 Storm R (same drivetrain, per its own comment) uses 2.846; ET 10.812 vs 10.931. Low Rider ST and Road Glide (M8 117) have primary 1.0 and cassette [3.627..0.84], so overall 1st is 7.04, against 9.31 on every other M8 row (primary 1.353, [3.337..1.0]); rev-limited top-gear speed is 483 km/h. 2025 entries have overdrive cassettes unlike their siblings: RS 660 Factory 6th 0.695 (RS 660 has 1.037), M 1000 RR 2025 0.927 (M1000RR 2021 has 1.28), Superveloce 0.837, ZX-10R 2008-10 0.871. Rev-limited top-gear speeds are 459-509 km/h. Quarter-mile ET effect is small (≤0.05 s) except for Rocket 3 and Pan America.
- Proposed fix: Re-source these cassettes and final drives from service manuals. Encode the Rocket 3 R as the 0/0 shaft sentinel so 2.846 applies. Add a sanity test that rev-limited top-gear speed ≤ about 1.3× the factory or benchmark top speed.

## [low/safe] Rear rolling radius ignores 2-digit-width and inch tire sizes (21 bikes fall back to 0.302 m); front radius is never derived (0.305 on all 541)
- Area: data — `motoquant/scraper/importer.py` 966
- Verdicts: not yet verified
- Trigger: Specs with rear sizes like '80/90-17' (Y15ZR, RS150R, Exciter, Sonic, Supra, Raider R150), '80/100-18', '90/90-12' (TVS NTorq), or inch sizes '4.00-18' (GT750, H2 Mach IV), '3.50-18', '4.60-18' (KLX300).
- Evidence: `re.match(r"(\d{3})/(\d{2})", ...)` requires a 3-digit width, so these 21 specs keep the 0.302 m default. Geometric radius is 0.233 for NTorq (30% error, an effective gearing change), 0.325 for GT750/H2 Mach IV, and 0.288 for the 80/90-17 underbones. Measured: NTorq ET 20.636 -> 20.392 with a 0.233 m radius, GT750 12.096 -> 12.030, H2 Mach IV 11.503 -> 11.427. front_rolling_radius_m is 0.305 for all 541 configs (122 more than 5% off, e.g. 21-inch fronts 0.348), which feeds the front-wheel inertia term.
- Proposed fix: Parse widths with \d{2,3}, support inch bias sizes (section×25.4), and compute front radius from front_tire_size the same way. Reseed afterwards.

## [low/safe] Shipped DB never received the Trask turbo 1950cc cap fix: 12 M8/Thunderstroke big twins can't see the kit
- Area: data — `motoquant/database/seed_catalogs/drag_specific.py` 530-536
- Verdicts: not yet verified
- Trigger: Compatible parts, optimizer or outlaw for bikes 133, 134, 4598-4601 (H-D 1868/1923cc) and 248, 303, 793, 4597, 4604, 4606 (Indian 1768-1890cc).
- Evidence: The seed source has displacement_max_cc 1950 ('so Harley M8 114/117 ... actually match'), but the shipped DB part 341 rule still has 1750 and the old description. list_compatible_for_bike gives trask341=False for all 12 bikes, and True after a re-seed. In the other direction, seed sources for parts 345 (Rekluse) and 362 (HM QS) list only 'Indian Motorcycle', so a fresh seed drops all Indian bikes from them until merge_manufacturers runs, and that patch is not in the documented reseed chain.
- Proposed fix: Add an idempotent patch setting part 341's rule to the seed value (and re-check other seed-vs-DB rule diffs). Use 'Indian' in the seed sources for 345/362, or add patch_2026_06_13_merge_manufacturers to the documented chain.

## [low/safe] Validator 'unit correction' converts in the wrong direction and accepts the out-of-bounds result
- Area: data — `motoquant/scraper/validator.py` 152-170
- Verdicts: not yet verified
- Trigger: validate_spec on a spec with peak_torque_nm=450 or peak_power_hp=600 (e.g. from the chat estimator or scraped input).
- Evidence: Torque branch: the guard tests `5 <= val*0.7457 <= 400` but multiplies by 1.356, so 450 Nm becomes 610.2 Nm. That is even further out of bounds, yet the result is valid=True with only a 'looks like ft-lb' warning. Power branch: an out-of-bounds HIGH value is 'treated as kW' and multiplied by 0.7457 (HP→kW, the inverse of kW→HP), so 600 becomes 447.4 hp and is accepted. Values below the lower bound are never corrected.
- Proposed fix: Only apply a conversion when the converted value lands in bounds and the direction is physically meaningful (kW→hp ×1.341 for implausibly LOW hp; lb-ft→Nm ×1.356 for LOW torque). Re-check bounds after conversion and error otherwise.

## [low/safe] Live-price freshness cache never hits (retailer key mismatch), and refresh_retailer_urls stamps last_price_check without checking any price
- Area: data — `motoquant/database/pricing_refresh.py` 239-251, 414-423
- Verdicts: not yet verified
- Trigger: Repeated `fetch_live_price(conn, pid)` without force, or `pricing refresh` followed by `pricing stale`.
- Evidence: The freshness query filters part_prices by parts.retailer (e.g. 'superbikestore.in'), but the upsert stores result.retailer from the adapter (e.g. 'Superbike Store'). With a mocked adapter, 3 consecutive non-forced calls made 3 network fetches; with matching names it made 1. 70 of the 72 URL-bearing parts carry a retailer string no adapter emits. refresh_retailer_urls sets last_price_check=today on every part with a retailer ('bookkeeping — harmless'), and seed upserts do the same, so stale_parts()/coverage_report() report fresh prices that were never checked.
- Proposed fix: Key the freshness check on the same retailer value that is stored (or on part_id + source_url). Only update last_price_check when a price was actually fetched or verified.

## [low/safe] Reseed syncs only disp/hp/torque/mass headline columns, so 7 bikes show rpm/wheelbase that disagree with their physics blobs
- Area: data — `scripts/reseed_configs_from_specs.py` 166-185
- Verdicts: not yet verified
- Trigger: /api/bikes/{id} or the bike pages for 316 V-Strom SX 250, 81 R15 V4, 82 MT-15 V2, 86/314 Hornet 2.0, 53 848 EVO, 755 Yezdi Adventure.
- Evidence: Headline vs engine/chassis blob: V-Strom SX 250 hp@8000 vs 9300, tq@6250 vs 7300, wheelbase 1355 vs 1440 (the Aug-8 'height-as-wheelbase' fix reached physics only); 848 EVO tq@8250 vs 9750; R15 V4 hp@10250 vs 10000, wb 1345 vs 1325; Hornet tq@6500 vs 6000, wb 1320/1330 vs 1355; Yezdi Adventure hp@7300 vs 8000.
- Proposed fix: Sync peak_power_rpm, peak_torque_rpm, wheelbase_mm, cylinder_count/config and category in the reseed UPDATE (reuse extract_headline_specs).

## [low/safe] create_config idempotency guard ignores category_tag, so a re-derived taxonomy never persists via the import path
- Area: data — `motoquant/database/bike_repo.py` 330
- Verdicts: not yet verified
- Trigger: `import --known-bikes` after a derive_category_tag change that leaves the 13 param blobs byte-identical.
- Evidence: The guard compares only _PARAM_COLS. With identical params and category_tag='cruiser_1300p', create_config on MT-07 (bike 25) returned the existing config 834 with its tag still 'sport_twin_600_1300' and still 1 version. The reseed path does write category_tag, so the two paths diverge for any taxonomy-only change; the stale tag picks the wrong CategoryProfile at runtime.
- Proposed fix: Include category_tag in the comparison, or UPDATE category_tag on the reused row.

## [high/safe] optimize_build reports the combined-build ET from the surrogate, not a full sim, so the headline delta is off by roughly 45%
- Area: analysis — `motoquant/analysis/build_optimizer.py` 694
- Verdicts: not yet verified
- Trigger: /api/optimize/build in production, where the numpy surrogate auto-loads from artifacts/surrogate/surrogate_numpy.npz, with any build that has no boost part. Repro: optimize_build(cfg_for(5), 60000, PartsRepository(conn), bike_model_id=5, profile='street_legal', surrogate=NumpySurrogate.load(...))
- Evidence: Per-part deltas are re-checked with full sims, but the combined build goes through predictor(build_cfg). Its feature vector differs from the baseline, so the surrogate scores it, and it cannot see quickshifters, chains or clutch kits. Full sim of the identical part list (applied in price order): bike 5 [13,50,359,289,88] reported 10.2376 s / -0.180 s vs full sim 10.0933 s / -0.324 s; bike 11 [25,359,87] reported -0.073 s vs -0.138 s; bike 65 [238,231,215], all surrogate-visible parts, reported -0.546 s vs -0.845 s. cost_per_tenth_inr is derived from the wrong delta. The code comment calls this the 'Combined sim of the selected build'.
- Proposed fix: Always run the final combined verification through roi._run_et (one extra full sim per request), and compute delta_et_s and cost_per_tenth from that result.

## [high/safe] The feature-blind fallback only fires when the feature vector is bit-identical to stock, so 39 parts that also touch a visible field are mis-scored by the surrogate
- Area: analysis — `motoquant/analysis/build_optimizer.py` 239
- Verdicts: not yet verified
- Trigger: Parts that change a blind field plus any surrogate-visible field, e.g. model-specific quickshifters 546-550 (total_shift_time_ms plus dry_mass_kg +0.15 kg), wheelie bars 109/110/168-170/417-420 (+mass), clutch kits 540-545, shocks with cog_height_mm 513-521, Woolich flashes 44-48 (two_step/launch_rpm).
- Evidence: make_predictor(numpy surrogate) vs full sim, delta ET: part 548 on bike 1: surrogate +0.0011 s, full sim -0.0486 s. 546 on bike 2: +0.0006 vs -0.0611. 547 on bike 3: +0.0002 vs -0.0540. 550 on bike 49: -0.0001 vs -0.0523. predictor.stats() showed feature_blind=0. These parts are scored as zero or slower, so they are never selected and never reach the verification loop. The optimizer cannot recommend them when a surrogate is loaded.
- Proposed fix: Compute _blind_relevant_signature for every config, not only fvec==ref. If the blind signature differs from the reference, full-sim the config, using the existing _blind_cache keyed on (sig, fvec).

## [high/safe] Turbo/SC kits and nitrous kits sit in separate exclusive groups but write the same forced_induction.boost_type scalar, and NA power parts applied after a boost part are dead
- Area: analysis — `motoquant/analysis/roi.py` 158
- Verdicts: not yet verified
- Trigger: optimize_build(cfg_for(11) Hayabusa 2008, 450000, bike_model_id=11, numpy surrogate). It selects both NX Dual-Stage 60 HP nitrous (143, ₹95k) and the Kraftwerks C-1 supercharger (140, ₹220k).
- Evidence: The parts are applied cheapest first, so boost_type ends up 'sc_centrifugal' and the nitrous override is discarded. Full sim of the build is 9.728 s with the ₹95k nitrous and 9.728 s without it, yet the output lists it as the top contributor at Δ -0.532 s. bridge.apply_part_to_config only scales the dyno curve when is_na, so any power part applied after boost_type flips adds 0 hp. Turbo 137 then PCVI 50: 8.2713 s, identical to turbo alone. Order also matters: on the outlaw build, optimize_build applies parts in price order (final boost=turbo, 8.987 s) while outlaw.py:161 re-applies them in display order (final boost=n2o, 9.0117 s). Autotune therefore tunes a different bike from the one that was priced.
- Proposed fix: Put boost_kit and nitrous in one exclusive knapsack group (alias nitrous->boost_kit in _EXCLUSIVE_CATEGORY_ALIASES). Apply NA power mods before boost parts, or scale the dyno curve regardless of boost. Make outlaw apply parts in the same price-ascending order as optimize_build.

## [high/safe] fuel_system, bodywork and unpositioned brake/suspension parts are freely stackable: the outlaw build buys 6 fairing kits and 13 fuel-system parts, and a QS listed under 'ecu' stacks with a real QS
- Area: analysis — `motoquant/analysis/roi.py` 158
- Verdicts: not yet verified
- Trigger: optimize_outlaw(cfg_for(11), parts_repo, tire_repo, bike_model_id=11, budget_inr=None, numpy surrogate). Also optimize_build(cfg_for(5), 150000, bike_model_id=5).
- Evidence: The outlaw build selected 6 complete fairing sets (167,166,107,165,108,164 = -27.5 kg; ET 10.2352 -> 10.1515 vs 10.2101 with one fairing). It also selected 13 fuel_system parts: 4 'Advanced Fuel System 5/6/7/8', two injector sets (ID1050X plus ID725), AEM Infinity standalone ECU, Bazzaz BKN, HealTech iFlash, two pumps and a surge tank. Together they add 197 -> 234.3 hp, a phantom -0.26 s. It also took 3 caliper kits, 7 pad sets, 2 master cylinders, and a coilover plus a rear shock. Build dry mass went 220 -> 178.4 kg. Separately, HealTech QuickShifter (117) is in the 'ecu' category and was selected alongside Dynojet QEM QS (359) on bike 5. Its absolute override total_shift_time_ms=60 replaces 48 ms: [359] 10.3505 s vs [359,117] 10.3662 s, so ₹33,951 is spent on a regression.
- Proposed fix: Add slot keys for fuel_system (controller / injectors / pump), bodywork (fairing set) and pads without a position (one front pad group). When two parts write the same absolute override path, put them in one knapsack group (derive groups from overlapping param_overrides keys). Re-categorise part 117 as quickshifter.

## [high/safe] The knapsack picks front and rear sprockets independently on additive gains. The combined ratio is never evaluated, and the outlaw build ends up 0.72 s slower than its own turbo alone
- Area: analysis — `motoquant/analysis/build_optimizer.py` 704
- Verdicts: not yet verified
- Trigger: Outlaw run on bike 11 (Hayabusa 2008-12, MT drag slick mu 1.92). It selected front 15T (274) and rear 50T (31), each individually beneficial at about -0.11 s.
- Evidence: Stock gearing is 18/43; together the two sprockets give 15/50 (+39% final drive). On slicks: [31,274] 9.7347 s vs stock 9.5864 s (+0.148 s slower). [137 turbo] 8.2713 s vs [137,31,274] 9.1025 s. The full ₹25.6 lakh outlaw build verifies at 8.987 s while the ₹2.8 lakh turbo alone gives 8.271 s. The verify loop only re-checks single parts, so nothing catches a combined build that is worse than a subset of itself.
- Proposed fix: Treat front+rear sprockets as one gearing group whose candidates are evaluated as pairs (or as the resulting final ratio). After selection, run a greedy drop-one pass on the full-sim combined build and remove any part whose removal improves ET.

## [high/safe] 7 turbo kits (₹3.2-8 L) produce zero boost and 3 nitrous kits produce zero HP. The only 'gain' is the boosted density floor
- Area: analysis — `motoquant/submodels/environmental.py` 94
- Verdicts: not yet verified
- Trigger: Parts 336/337/338/339/341/581/582 set boost_type='turbo' without target_boost_bar (default 0.0) and carry peak_power_hp deltas (+75..+180 hp). Parts 100/141/142 set n2o_hp_per_stage without n2o_stages (default 0).
- Evidence: On bike 11 (Hayabusa 2008), comparing Aamby (679 m) and sea level: twin-turbo 337 (+180 hp claimed, peak_power_hp shows 377) gives d=-0.088 s at Aamby but +0.046 s SLOWER at sea level. The dyno curve is not scaled because bridge.py:440 skips scaling when is_boosted, and the boost target is 0 bar. ZEX 35 HP (100), ZEX 50 HP (141) and NX 15 HP (142) all give exactly -0.1344 s at Aamby and +0.0000 s at sea level. The altitude 'gain' is the max(0.97, rho/rho0) power floor, which is granted to any non-NA boost_type, including nitrous (not density-compensating) and 0-bar boost.
- Proposed fix: Fix the catalog rows: set target_boost_bar from specifications.boost_psi, set n2o_stages=1, and drop the peak_power deltas from boost parts. Apply the boosted DA floor only when boost_type is turbo/sc and target_boost_bar>0, not for n2o.

## [high/safe] In clutch slip the engine clips to redline*1.02, which round-trips to just above the cut threshold. Torque goes to exactly 0 and the bike freezes, so boost parts show up as 2-15 s slower
- Area: analysis — `motoquant/physics.py` 757
- Verdicts: not yet verified
- Trigger: Boost/nitrous parts whose torque exceeds clutch capacity. Examples: HKS GT Turbo (137) on bike 40 ZX-10R 2011-15; Kraftwerks C-1 (140) on bike 58 Panigale V4; NX 60HP dual-stage (143) on bike 57 1299 Panigale.
- Evidence: ZX-10R plus 137 gives ET 25.574 s vs stock 10.363 s. Trace: from t=2 s to 24 s, v is frozen at 58.7 km/h in gear 1, rpm=14586 (clip) and F_drive=0. Clip omega back to rpm = 14586.000000000002, which is > redline*1.02 = 14586.0, so EngineModel.torque (engine.py:27) returns 0.0. a_net is clamped >= 0 in slip, so the clutch never locks. Panigale V4 plus 140: 9.998 -> 25.688 s. 1299 Panigale plus 143: 10.14 -> 12.12 s. Overall 19 of 1596 compatible boost/nitrous (part, bike) pairs simulate slower, and 279 pairs spend more than 0.3 s at the limiter. ROI, the optimizer and the outlaw pipeline report these parts as large losses. The K5/R1/Hayabusa references spend 0.0 s at the clip.
- Proposed fix: Clip omega_e slightly below the cut (e.g. redline*1.02*(1-1e-9)), or use the same threshold in both places. While slipping at the limiter, transmit min(T_clutch_max, limiter-averaged torque) instead of a hard 0.

## [high/safe] BikeRepository.to_config overrides each config's JSON dyno curve with stale dyno_curves rows, so chat, NL and CLI sims diverge from /api/simulate by up to 2.28 s
- Area: analysis — `motoquant/database/bike_repo.py` 466
- Verdicts: not yet verified
- Trigger: Any to_config caller: llm/agent.py:279/640, llm/runner.py:634/1084/1670, nlp.py:385, and run.py sim/analysis --bike-id.
- Evidence: 508 of 541 current configs have a dyno_curves row (last written 2026-07-04, is_at_wheel=1) that differs from engine_params.dyno_curve (post-Aug-8 crank-mode curves, is_at_wheel=False). to_config prefers the table row as dyno_override. Across the catalog, 506 of 541 bikes differ by more than 1 ms, mean |Δ| 0.094 s, max 2.28 s. Bike 151 YZF-R15 V3: to_config 16.510 s vs API path db_row_to_config(dict(cfg_row)) 18.786 s. Bike 4093 Xtreme 250R: 17.219 vs 19.205. Bike 348 MT-15 V1: 16.305 vs 15.541. The stale rows also flip is_at_wheel, which disables parasitic losses and chain-efficiency effects on those paths.
- Proposed fix: Drop the dyno_curves override in to_config (the JSON blob is the reseeded source of truth), or make reseed_configs_from_specs rewrite or delete the dyno_curves rows. Add a test asserting to_config ET == db_row_to_config ET for every current config.

## [medium/safe] The ECU-autotune launch-RPM sweep does nothing on 520 of 541 bikes (two_step=False) and returns a made-up 'lower launch RPM' recommendation
- Area: analysis — `motoquant/analysis/ecu_autotune.py` 214
- Verdicts: not yet verified
- Trigger: autotune(cfg_for(4600)) (HD Street Bob 114) or any bike whose staging.two_step is False. Also the outlaw setup stage, e.g. bike 11 with budget 60000.
- Evidence: StagingModel.initial_omega_e ignores staging.launch_rpm unless two_step is True, and the sweep never sets two_step. Street Bob candidates [2400, 3190, 3970, 4760, 5540, 6330, 8000] rpm all give 12.5585 s. The result is recommended_rpm 2400 (the lowest grid point, from min() tie-breaking), delta 0.0, with rationale 'lower launch RPM reduces wheelspin / bog'. stock_rpm reports 8000, an unused dataclass default (above this bike's redline). Outlaw on bike 11: 'recommended 5760 rpm, delta 0.0, lower launch RPM reduces wheelspin'. 520 of 541 DB configs have two_step=False.
- Proposed fix: In the sweep and in the combined verification, set cfg.staging.two_step=True with each candidate launch_rpm (or sweep peak_torque_rpm when no two-step is fitted). Report stock as the RPM the engine actually launches at. If all candidates tie, return 'no change'.

## [medium/safe] The autotune gearing sweep is clamped to 28-56 teeth. For 19 belt/shaft bikes the stock gearing is never simulated and an impossible ratio is recommended
- Area: analysis — `motoquant/analysis/ecu_autotune.py` 132
- Verdicts: not yet verified
- Trigger: autotune(cfg_for(4600)) on the HD Street Bob 114: belt pulleys 32/66, drive_type stored as 'chain'.
- Evidence: lo=max(28,56)=56 and hi=min(56,79)=56, so every candidate collapses to 56T. Candidates = [(56, 12.4732)] and stock 66 is never simulated. The tool recommends '32/56 — taller (more top-end)', a 10-tooth rear-pulley change, with delta -0.085 s. 19 bikes have rear >= 57 (HD/Indian belt pulleys 65-72T, Buell 65T, VMAX 1200 shaft 57T). Chain_adjustable only checks front>0 and rear>0, so belt and shaft bikes receive sprocket advice.
- Proposed fix: Always include the stock rear count in the candidate set. Derive the clamp from stock (e.g. rear*0.85..rear*1.20 with no absolute 56 cap), and skip the sweep when chain_pitch is None or drive_type is belt/shaft.

## [medium/safe] The outlaw pipeline neither deducts nor reports the drag-tyre cost, so a user budget is exceeded by the tyre price
- Area: analysis — `motoquant/analysis/outlaw.py` 207
- Verdicts: not yet verified
- Trigger: optimize_outlaw(cfg_for(11), parts_repo, TireRepository(conn), bike_model_id=11, budget_inr=60000).
- Evidence: The tyre stage fits the Mickey Thompson ET Drag Slick at price_inr 41,400, and the knapsack then spends ₹58,700 of the full ₹60,000. Actual spend is ₹100,100, 67% over budget, while total_cost_inr reports 58,700.
- Proposed fix: Subtract the fitted tyre price from resolved_budget before optimize_build, and add it to total_cost_inr (or itemise it). If the tyre alone exceeds the budget, skip it.

## [medium/safe] _find_next_upgrade suggests parts for slots the build already fills (a second sprocket in the same position, a second air filter), and these often make the build slower
- Area: analysis — `motoquant/analysis/recommendations.py` 489
- Verdicts: not yet verified
- Trigger: optimize_build(..., profile='street_legal', numpy surrogate). Bike 77 (Apache RTR 160 4V) at 8000; bike 5 at 20000/60000; bike 11 at 20000; bike 65 at 15000.
- Evidence: Bike 77: the build already has front sprocket 210, and next_upgrade suggests front sprocket 211 with marginal_et_gain_s 0.108. Real effect: 17.3307 -> 17.4579 s (0.127 s slower). Bike 5: the build has rear sprocket 13, and the suggestion is rear 14 (+0.057 claimed) at 10.2784 -> 10.3141 (slower). Bike 11: rear 25 has rear 26 suggested at 10.0977 -> 10.1463 (slower). Bike 65: the build has a DNA air filter (231), and a second air filter (233, Green Filter) is suggested, which is physically impossible.
- Proposed fix: Exclude candidates whose _knapsack_group_key matches a group already used by the selected build (pass position_of/slot_of through), or score the marginal gain with a real sim of build+part.

## [medium/safe] After surrogate verification overwrites delta_et_s, roi_score and cost_per_tenth_inr are not recomputed, so the API reports inconsistent ROI numbers
- Area: analysis — `motoquant/analysis/build_optimizer.py` 669
- Verdicts: not yet verified
- Trigger: optimize_build with the numpy surrogate on bike 11 at 450000, bike 65 at 15000.
- Evidence: Bike 11: PCVI Stage 2 shows delta -0.0845 s but cost_per_tenth ₹40,780 (the verified delta implies ₹21,065) and roi 0.245 (implied 0.475). DNA Stage 2 filter: ₹26,207/tenth vs ₹12,569 implied. Bike 65: Red Baron slip-on ₹2,927/tenth vs ₹2,051 implied. The stale roi_score also drives _find_next_upgrade ranking and rank_categories best_roi.
- Proposed fix: When writing the verified delta back, recompute r.roi_score and r.cost_per_tenth_inr via roi._roi_metrics(r.price_inr, d_et).

## [medium/safe] The Bayesian optimizer's power_delta_hp and rear_pressure_delta have no effect, and mass changes reduce the estimated cost
- Area: analysis — `motoquant/analysis/bayesian_opt.py` 229
- Verdicts: not yet verified
- Trigger: BayesianBuildOptimizer(gsxr1000_k5(), budget_inr=20000), calling _apply_params_to_config and _estimate_cost directly. The same applies to every catalog config, since all 541 carry dyno curves.
- Evidence: power_delta_hp=+50 gives ET 9.933056 (identical to base) yet costs ₹40,000. Line 240 bumps peak_power_hp without scaling the dyno curve (Sobol and bridge do scale it). rear_pressure_delta=+3 gives an identical ET because rear_pressure_psi is never read by physics. COST_PER_UNIT mass=-1500 multiplied by abs(delta) makes any mass change negative cost: -15 kg or +5 kg both cost ₹0, and '+40 hp alone' at ₹32,000 (over the ₹20k budget) becomes ₹9,500 with -15 kg, slipping under the budget penalty.
- Proposed fix: Scale engine.dyno_curve.torque_nm by the power ratio (as sobol._apply_sample_row does). Drop the pressure dimension or wire it into physics. Cost mass as max(0,-delta)*1500 (reduction costs money, adding mass is free).

## [medium/safe] The NL runner throws away apply_part_to_config's result, applies incompatible parts, and misparses budgets, bikes, wind and part keywords
- Area: analysis — `motoquant/nlp.py` 511
- Verdicts: not yet verified
- Trigger: NLSimRunner(db).run_query('my hayabusa with nitrous and exhaust at aamby valley'); NLQueryParser().parse(...) on the queries listed below.
- Evidence: run_query reports applied_parts=['Harley EFI Nitrous System — Twin Bottle','Full System Rocket 3'] on a Hayabusa. These are the first alphabetical rows from search(category=...) with no bike filter, and ET is 10.2352 s, identical to the stock query, because the returned config is discarded. 'with turbo' finds nothing, since there are no 'turbo', 'supercharger', 'clutch', 'weight_reduction' or 'tire' categories. 'vht prep' writes environment.track_prep, which physics never reads (it reads tires.track_prep_type). _resolve_bike('k5') returns BMW 'R 1250 RT' (model_code K52), and 'r1' returns 'R 12 nineT'. 'budget of 50,000 inr' parses as 50, and '1.5 lakh' as None. '3 m/s headwind' also sets altitude_m=3. 'brake discs' adds 'supercharger' (substring 'sc'), and 'wet track' adds 'clutch'.
- Proposed fix: Use config = apply_part_to_config(config, part), choose parts with search(category, bike_model_id=...), map keywords to real categories, strip commas and support k/lakh in budgets, make the altitude regex reject m/s, use word-boundary keyword matching, and write tires.track_prep_type.

## [medium/safe] Chain-efficiency parts have no effect on the 35 bikes with at-wheel dyno curves, because at-wheel torque is divided by the modified efficiency
- Area: analysis — `motoquant/submodels/engine.py` 34
- Verdicts: not yet verified
- Trigger: Part 291 'RK 530 Premium Chain' (chain_efficiency x1.02) on bike 3, bike 40 or bike 1 (35 current configs have is_at_wheel=True).
- Evidence: Bike 3 Hayabusa Gen1: 10.4841 -> 10.4841. ZX-10R 2011-15: 10.3629 -> 10.3629. K5 DB row: 10.0347 -> 10.0347. The code converts T_wheel to crank torque as T/eta_dt using the NEW eta and then multiplies back by the same eta, so any chain or efficiency upgrade cancels exactly. The torque was measured with the stock drivetrain, so it should be divided by the stock eta.
- Proposed fix: Store the drivetrain efficiency the curve was measured with (e.g. DynoCurve.eta_at_measure, defaulting to the config's eta at import) and divide by that. Stock configs are unchanged, so the reference ETs do not move.

## [low/safe] find_best_build's min_delta_et_ms noise floor has no effect on which parts are selected
- Area: analysis — `motoquant/analysis/roi.py` 806
- Verdicts: not yet verified
- Trigger: find_best_build(cfg_for(5), 100000, prepo, part_ids=[289,88,359,375,376], bike_model_id=5, min_delta_et_ms=100.0)
- Evidence: With floor=100 ms the knapsack still selects 359 (67 ms), 289 (32 ms) and 88 (24 ms) for ₹31,639, the same set as floor=5 ms. Only roi_score is zeroed, because the candidates filter and gain_of use the raw delta_et_s. In no-limit outlaw runs the optimizer buys anything with a positive delta, e.g. ₹11,990 HEL brake lines for 1.5 ms.
- Proposed fix: Filter candidates on gain_of(r)*1000 >= min_delta_et_ms in find_best_build and in build_optimizer._select_build.

## [low/safe] The candidate pool is cut at 200 parts in brand order, so 4 bikes silently lose their alphabetically-last compatible parts
- Area: analysis — `motoquant/analysis/build_optimizer.py` 550
- Verdicts: not yet verified
- Trigger: optimize_build, recommend_build, generate_upgrade_path or find_best_build on bike 1, 2, 3 or 17 (201-205 compatible parts).
- Evidence: Hayabusa Gen1 (3) has 205 compatible parts. search(limit=200) drops ZEX 50 HP (141), ZEX 35 HP (100), Öhlins FG424 fork (383), Öhlins Fork V5 (149) and Öhlins STX shock (104, which carries mu_peak x1.02) from every optimizer and recommender run.
- Proposed fix: Pass limit=None (or a value above the catalog size) for optimizer candidate discovery.

## [low/safe] Turbo, supercharger and nitrous kits are compatible with the factory-supercharged Ninja H2 and H2R
- Area: analysis — `motoquant/parts/compatibility.py` 30
- Verdicts: not yet verified
- Trigger: is_compatible(part 137 HKS GT Turbo / 140 Kraftwerks C-1, bike 45 Ninja H2 or 328 Ninja H2R).
- Evidence: Both kits match through their family rules (sport category plus displacement). FitmentMatch has no forced-induction constraint, and the H2's supercharger is baked into an NA-flagged curve. H2 + HKS turbo: 9.728 -> 9.829 s. H2R + C-1: 9.813 -> 9.930 s. The optimizer and ROI list a second supercharger as a purchasable part.
- Proposed fix: Add an 'aspiration' constraint (or excluded_bike_ids) to boost/nitrous fitment rules and flag factory-boosted models in bike_models.

## [low/safe] Part 54 (Rapid Bike EVO) enables two-step with no launch_rpm, so every one of its 393 compatible bikes launches at the generic 8000 rpm default
- Area: analysis — `motoquant/database/bridge.py` 371
- Verdicts: not yet verified
- Trigger: apply_part_to_config with part 54 (param_overrides {'staging.two_step': true}) on any compatible bike, e.g. 241 Thruxton 1200 R.
- Evidence: The launch RPM becomes min(8000, redline) regardless of the engine. Thruxton 1200 R (peak torque 4950, redline 7425) launches at redline and runs +1.798 s slower. YZF-R9 is +0.084 s, Scram 411 +0.067 s, and others gain. In a 12-bike sample, 4 got slower. The DB staging.launch_rpm=8000 is a dataclass default, not per-bike data.
- Proposed fix: When a part flips two_step on without a launch_rpm, set launch_rpm from the bike (e.g. peak_torque_rpm, or a cluster launch factor times redline), and stamp a real launch_rpm into bike_configs.

## [low/safe] CLI 'analysis surrogate ... --bike-id' crashes because it queries a nonexistent 'bikes' table
- Area: analysis — `motoquant/run.py` 2443
- Verdicts: not yet verified
- Trigger: python3 -m motoquant.run --db motoquant.db analysis surrogate generate --bike-id 5 --n-samples 2 --output /tmp/x.npz
- Evidence: sqlite3.OperationalError: no such table: bikes. The schema only has bike_models/bike_configs, so per-bike surrogate generate/train/evaluate is unusable.
- Proposed fix: Load the config with db.bikes.get_current_config(bike_id) and db_row_to_config(dict(row)) (or bikes.to_config once that is fixed).

## [low/safe] At the outlaw '₹5M no-limit' budget the grouped knapsack DP costs about 80 s of CPU per call and runs up to 4 times per request
- Area: analysis — `motoquant/analysis/roi.py` 420
- Verdicts: not yet verified
- Trigger: _grouped_knapsack(200 singleton candidates, 5_000_000) with the default bucket of ₹100 (W=50,000), as used by optimize_outlaw(budget_inr=None) and by the surrogate verify loop (up to 3 reselections).
- Evidence: Measured: budget 500k = 4.3 s / 2 MB; 2M = 27.9 s / 13 MB; 5M = 81.3 s / 47 MB peak, single-threaded. Each group copies W+1 choice lists (new_choice=[c[:] for c in choice]). On Render's 0.5 CPU this holds the GIL for minutes inside the job thread, starving the poll handler.
- Proposed fix: Store back-pointers instead of copying choice lists. When the sum of candidate prices is at or below the budget, skip the DP and take the best item per group. Or scale BUCKET with the budget (e.g. ₹1000 above ₹1M).

## [low/safe] Sobol uses absolute Cd/area/radius bounds that exclude 36% of catalog bikes' nominal Cd, so sensitivities are computed away from the actual bike
- Area: analysis — `motoquant/analysis/sobol.py` 100
- Verdicts: not yet verified
- Trigger: compute_sobol_indices(cfg) for any bike with aero.cd < 0.55, e.g. post-normalisation sport bikes with Cd 0.30-0.45.
- Evidence: Across current configs, Cd ranges from 0.300 to 0.920 (median 0.720), and 36.2% fall outside the hard-coded [0.55, 0.95] sample range. Rear radius has 6.1% outside [0.28, 0.33] and frontal area 3.3% outside [0.38, 0.62]. For these bikes every sample uses a Cd the bike never has, so et_mean, et_range and the indices describe a different machine than base_et_s.
- Proposed fix: Make aero_cd, frontal_area and rolling_radius relative bounds (e.g. 0.85-1.15 times nominal), or centre the absolute bounds on the nominal value.

## [high/safe] web_fetch SSRF guard bypassed by URL-parser differential (backslash before '@')
- Area: runtime — `motoquant/llm/webtools.py` 94
- Verdicts: not yet verified
- Trigger: Agent tool web_fetch (reachable by any anonymous /api/chat user via prompt) with url 'http://127.0.0.1:PORT\@example.com/' or 'http://169.254.169.254\@example.com/latest/meta-data/'. The same string as a redirect Location also passes, since each hop is re-checked with the same _check_url.
- Evidence: _check_url validates urllib.parse.urlparse(url).hostname, which reads 'example.com' (it treats '127.0.0.1\' as userinfo). requests/urllib3 parse the same string and connect to 127.0.0.1. Parser comparison: 'http://127.0.0.1\@example.com/' gives urlparse host example.com but requests host 127.0.0.1; same for 'http://127.0.0.1:80\@example.com/'. End-to-end test against a localhost server on :18765 (getaddrinfo stubbed only so the decoy example.com resolves publicly): web_fetch('http://127.0.0.1:18765/') -> {'error': 'host resolves to a private or reserved address'}, but web_fetch('http://127.0.0.1:18765\@example.com/') -> {'text': 'INTERNAL-SECRET path=/%5C@example.com/'}.
- Proposed fix: In _check_url, reject any URL containing '\', whitespace or control characters, and any URL with userinfo (parsed.username/parsed.password or '@' in netloc). Also parse with urllib3.util.parse_url (the parser requests uses) and refuse if its host differs from urlparse's hostname. Stronger option: resolve once, then connect to the vetted IP through a pinned adapter, which also closes the DNS-rebinding residual. Add a test with the backslash payload.

## [high/safe] Dragy run detection is O(windows x N): a small crafted upload pins the API CPU for hours
- Area: runtime — `motoquant/calibration/dragy.py` 340
- Verdicts: not yet verified
- Trigger: POST /api/calibrate/dragy (anonymous; 6 uploads/60s per IP; 25 MB cap) with a CSV 'Time (s),Speed (m/s)' that repeats 5 zero-speed rows then 1 row at 40 m/s.
- Evidence: For every staged window, _detect_runs calls _detect_sample_rate(t) (np.median over the FULL file) and _integrate_distance over the whole remaining file. Measured: 60k rows (659 KB) took 5.9 s; 120k rows (1.35 MB) took 41.4 s (worse than quadratic). Extrapolating to the 25 MB cap (~2.3M rows) gives hours per upload. The route runs this via asyncio.to_thread on the default executor (shared with the overlay sim and the dyno parse), so a few uploads saturate the 0.5-CPU instance under the GIL.
- Proposed fix: Compute the sample rate once in _build_run_list and pass it in. In _detect_runs, integrate only up to launch_idx + MAX_RUN_DURATION_S*rate frames, not the rest of the file. After a run is accepted, skip staged windows that start before its end index. Also cap the total row count, e.g. reject files over about 200k samples.

## [high/safe] `calibrate overlay --bike-id N` always simulates the K5 reference: ImportError swallowed
- Area: runtime — `motoquant/run.py` 1929
- Verdicts: not yet verified
- Trigger: python -m motoquant.run --db motoquant.db calibrate overlay run.csv --bike-id 275 (any bike id)
- Evidence: The handler imports `bike_row_to_config` from database.bridge, but no such function exists (bridge has db_row_to_config, which takes a bike_configs row). The resulting ImportError is caught by `except Exception: pass`, so the code falls back to gsxr1000_k5(). Run against the RX100 (id 275) and the Hayabusa (id 3), the report printed the identical sim 'Sim : 9.9331 s' (the pinned K5 ET) and identical split errors (-0.0318/-0.5061/.../-1.4151 s). The real RX100 sims 20.85 s. The report never names which bike was simulated.
- Proposed fix: Use db.bikes.get_current_config(bike_id) + db.bikes.to_config(config_id), matching cmd_sim. Print an error and return 1 when the bike is not found, not a silent K5 fallback. Print the simulated bike name in the report. Add a CLI test asserting different bikes give different sim ETs.

## [high/safe] tires.mu_peak is a dead knob for 118 bikes (sport_twin_600_1300, single_300_500), so the calibrator and the rear-tire swap do nothing to grip
- Area: runtime — `motoquant/physics.py` 266
- Verdicts: not yet verified
- Trigger: Any config whose category_tag is sport_twin_600_1300 (71 bikes, e.g. MT-07 id 25, TL1000R id 13) or single_300_500 (47 bikes). Paths: calibrate() with PRESET_AERO_TIRE or PRESET_TIRE_ONLY, `sim --rear-tire ID`, or any part/tire override that changes mu_peak.
- Evidence: MotoQuantEngine replaces tire_cfg.tires.mu_peak with the profile's mu_peak_override (1.31 / 1.18) and ignores the config's value. Measured on DB configs: TL1000R ET at tires.mu_peak 1.0/1.4/1.8 = 10.755/10.755/10.755 s; MT-07 = 12.1828 ×3. In the calibrator the mu dimension has zero gradient, so it returns an arbitrary 'fitted' mu_peak. In the CLI, a rear-tire swap changes only radius and thermal behaviour, never grip.
- Proposed fix: Make the override express the cluster's default grip without discarding a user or calibration change. One way: at import, store override/importer_default as a ratio and apply it multiplicatively, or apply the override only when cfg.tires.mu_peak still equals the importer's category default. Reference bikes (litre_sport_195p) have override None, so the three pins do not move. Re-verify the stock ETs of the two clusters bit-for-bit (golden snapshot) and add a liveness test: changing mu_peak changes ET for each cluster.

## [medium/safe] DynoJet 'RPM,WHP,TQ' files (the module's own documented format) are read as Nm, so the injected torque curve is 26% low
- Area: runtime — `motoquant/calibration/dyno.py` 186
- Verdicts: not yet verified
- Trigger: parse_dyno_file / POST /api/calibrate/dyno / `calibrate import-dyno` on a CSV with header 'RPM,WHP,TQ' where TQ is in lb-ft (docstring: 'DynoJet : RPM, WHP (or HP), TQ (lb-ft)'). The test fixture in tests/test_calibration.py uses exactly this header.
- Evidence: _detect_torque_unit only returns lbft when the label contains 'lb'/'ft', so a bare 'TQ' falls to 'nm'. With both columns present, the power column is used for peak_power but the torque column becomes the DynoCurve. Consistent file (true peak 140.2 hp / 94.9 Nm): reported peak_torque_nm = 70.0, peak_power_hp = 140.0, but the injected curve implies only 103.3 hp. CLI output: 'Peak torque : 69.8 Nm'. Any sim using the imported curve loses about 26% power.
- Proposed fix: When both channels are present, infer the torque unit from consistency: compare T*omega/1000 to P_kW, with ratio about 1.0 meaning Nm and about 0.7376 meaning lb-ft. Alternatively, default a unitless torque column to lb-ft whenever the power column is in hp. Warn when power and torque disagree by more than 5%.

## [medium/safe] ECU column units ignored: mph and m/s speed read as km/h, °F read as °C, psi read as kPa
- Area: runtime — `motoquant/calibration/ecu.py` 604
- Verdicts: not yet verified
- Trigger: `calibrate import-ecu` on a Woolich/PC-Link/generic CSV whose speed column is 'Speed (mph)', 'VSS (mph)' or 'Vehicle Speed (m/s)', or whose temp/MAP columns are 'Coolant Temp (F)' / 'MAP (psi)'.
- Evidence: _map_column strips the parenthesised unit before matching, and the generic km/h patterns (e.g. ^speed[_ (km/h)]*$, ^vss.*(km.?h)?$) appear before the mph, °F and psi patterns. Output: _map_column('Speed (mph)') -> ('vehicle_speed_ms', 0.2778); 'Vehicle Speed (m/s)' -> 0.2778; 'Coolant Temp (F)' -> ('coolant_temp_c', None); 'MAP (psi)' -> ('map_kpa', None). The same run logged in km/h parses as ET 11.381 s / 208.8 km/h; logged in mph or m/s it gives ET nan (the quarter is never reached).
- Proposed fix: Match on col_lower first and check the unit-specific patterns (mph, m/s, °F, psi) before the generic ones. Or extract the parenthesised unit and apply the same unit-override table used for MoTeC units rows (_apply_unit_overrides). Add a test per unit.

## [medium/safe] One blank or null speed cell crashes the whole Dragy parse (arrays desync) instead of skipping the row
- Area: runtime — `motoquant/calibration/dragy.py` 425
- Verdicts: not yet verified
- Trigger: A Dragy/RaceChrono CSV with one empty speed cell (e.g. '5.00,'), a JSON sample with "speed_kmh": null, or a top-level JSON array. Paths: CLI `calibrate import-dragy`, /api/calibrate/dragy, calibrate overlay.
- Evidence: In _parse_csv_body and _parse_json, ts.append() succeeds before vs.append() raises, so the row is only partially appended and t/v lengths diverge. Observed: blank_cell.csv -> ValueError 'operands could not be broadcast together with shapes (179,) (178,)'. The CLI shows a raw traceback (only DragParseError is caught); the API returns 422 with the numpy message. null.json raises the same ValueError. A top-level list JSON gives AttributeError "'list' object has no attribute 'get'". The code comment says 'skip malformed rows'.
- Proposed fix: Parse every field of a row into locals, then append them together only when all succeed. Validate the JSON shape (dict with a runs list of dicts) and raise DragParseError otherwise. In the CLI, catch ValueError/AttributeError along with DragParseError.

## [medium/safe] Dragy CSV detection: 'm/s' anywhere in the header flips speed units, and a header 'Elapsed' picks the Distance column as time
- Area: runtime — `motoquant/calibration/dragy.py` 187
- Verdicts: not yet verified
- Trigger: (a) Header 'Time (s),Speed (mph),Accel (m/s2)'. (b) Header 'Elapsed,Speed (km/h),Distance (m)'.
- Evidence: (a) _detect_csv_units searches the joined header string, so the accel column's 'm/s' sets speed_unit='ms' and mph values are taken as m/s: the same run gives ET 7.053 s / 357.4 km/h instead of 11.348 s / 209.1 km/h. (b) _col_index tries candidate 't' before 'elapsed' with substring matching, so 'distance' matches 't' (index 2): ET 28.489 s / 74.3 km/h. Also the 'd' distance candidate matches 'speed'; harmless only because the distance array is unused.
- Proposed fix: Detect units from the selected speed column's own label, not the joined header. Drop single-letter substring candidates ('t', 'v', 'd'), or require exact equality for them, and put 'elapsed' before generic tokens. Warn when the speed unit is defaulted (no unit in the header).

## [medium/safe] Calibrator Nelder-Mead refinement ignores the declared parameter bounds
- Area: runtime — `motoquant/calibration/calibrator.py` 326
- Verdicts: not yet verified
- Trigger: calibrate(config, run, PRESET_AERO_ONLY, global_search=False) or any run where the optimum lies outside the bounds; also with DE enabled, since NM refines without bounds.
- Evidence: minimize(method='Nelder-Mead') is called without bounds= in both calibrate() and calibrate_multi_run(). Synthetic real run generated from the K5 with cd=0.30: result fitted {'aero.cd': 0.3000037}, outside the PRESET bounds (0.45, 0.95), in 37 evaluations. With noisy GPS data, NM can likewise return negative or absurd mu/cd that apply() writes into the config.
- Proposed fix: Pass bounds=bounds to both minimize() calls (scipy >= 1.7 supports bounded Nelder-Mead), or clip x inside _Objective and clip the final x_final.

## [medium/safe] PRESET_FULL uses nonexistent 'drivetrain.efficiency' (crash), and _set_param silently writes phantom attributes
- Area: runtime — `motoquant/calibration/calibrator.py` 82
- Verdicts: not yet verified
- Trigger: calibrate(cfg, run, params_to_fit=PRESET_FULL) (public export), or any spec with a typo'd path.
- Evidence: DrivetrainParams has no 'efficiency' field; efficiency comes from the drivetrain_efficiency() method over primary/trans/chain fields. _get_param(cfg,'drivetrain.efficiency') -> AttributeError (not CalibrationError), so PRESET_FULL always crashes. _set_param uses bare setattr: on the K5, _set_param(cfg,'drivetrain.efficiency',0.82) leaves ET 9.9331 -> 9.9331, a dead knob accepted silently.
- Proposed fix: Point PRESET_FULL at a real field, e.g. drivetrain.chain_efficiency (0.90–0.99). In _set_param/_get_param, validate the last segment with dataclasses.fields() and raise CalibrationError on unknown paths.

## [medium/safe] Successful `sim` CLI runs exit with status 1 and dump the full SimResult repr to stderr
- Area: runtime — `motoquant/run.py` 3818
- Verdicts: not yet verified
- Trigger: python -m motoquant.run --db motoquant.db sim --bike-id 1 [--json]
- Evidence: cmd_sim returns the SimResult object, and `sys.exit(main() or 0)` passes a non-int object, so Python prints its repr (about 4 KB of arrays) to stderr and exits 1. Observed: exit=1 with stderr starting 'SimResult(dt=0.001, t=array([...' even with --json and valid JSON on stdout. This breaks `&&`/`set -e` scripting and CI use of the CLI. `bikes` exits 0.
- Proposed fix: Have cmd_sim return 0, or in main() map non-int handler results to 0: `rc = handler(args); return rc if isinstance(rc, int) else 0`.

## [medium/safe] `bikes --fitments BIKE_ID` crashes: BikeRepository has no .get()
- Area: runtime — `motoquant/run.py` 529
- Verdicts: not yet verified
- Trigger: python -m motoquant.run --db motoquant.db bikes --fitments 1 (documented in CLAUDE.md CLI reference)
- Evidence: Traceback: "AttributeError: 'BikeRepository' object has no attribute 'get'" at run.py:529. A static scan of all db.<repo>.<method>( calls in run.py found this as the only missing method; the repo exposes get_model().
- Proposed fix: Use db.bikes.get_model(args.fitments) and add a CLI test for --fitments.

## [medium/safe] Rate limits are bypassable by rotating X-Forwarded-For when no appending proxy is in front (self-hosted / direct uvicorn)
- Area: runtime — `motoquant/ratelimit.py` 47
- Verdicts: not yet verified
- Trigger: Any rate-limited route (chat, optimize, autotune, simulate, calibrate uploads) on a deployment reached directly (the open-source `uvicorn motoquant.api:app` path), with each request carrying a fresh 'X-Forwarded-For: 10.0.0.N'.
- Evidence: client_ip always trusts the rightmost XFF hop and has no trusted-proxy configuration. FastAPI TestClient with rate_limit('chat', 3): same client without XFF -> [200,200,200,429,429]; spoofed XFF per request -> 8× 200; 'X-Forwarded-For: 1.2.3.4, 9.9.9.N' -> 5× 200. The cost fuse is therefore fully bypassable unless a proxy appends the hop.
- Proposed fix: Add an env setting (e.g. MOTOQUANT_TRUSTED_PROXY_HOPS, default 0 for self-hosting, 1 on Render). Use request.client.host when 0, else take the Nth-from-right hop, and only when request.client.host is a trusted proxy address. Document it in the deploy guide.

## [medium/safe] SAE correction accepts any pressure/temperature/RH, so pressure entered in inHg (as DynoJet sheets print it) inflates power 3.3×
- Area: runtime — `motoquant/calibration/dyno.py` 144
- Verdicts: not yet verified
- Trigger: parse_dyno_file(..., temp_c=25, pressure_kpa=29.92) via `calibrate import-dyno --pressure 29.92` or the /api/calibrate/dyno form field pressure_kpa=29.92 (also bar 1.013, or rh_pct>100).
- Evidence: CF printed 3.309 and peak power 463.3 hp for a 140 hp run. p_dry is only floored at 0.1 kPa (CF up to 990×). The power clip in _smooth_and_fill runs before correction, so it does not bound the corrected output.
- Proposed fix: Validate inputs: pressure 60–110 kPa (auto-convert values 25–32 as inHg and 0.6–1.1 as bar, with a warning), temp −20–60 °C, RH 0–100. Reject or clamp CF outside about 0.85–1.20. Add the same bounds to the API Form fields (ge/le).

## [low/safe] ECU run extraction is O(n²) over a trailing idle window, so logs that end stationary take minutes to parse
- Area: runtime — `motoquant/calibration/ecu.py` 698
- Verdicts: not yet verified
- Trigger: `calibrate import-ecu` on a 100 Hz Woolich-style log that ends with the bike stopped (common at key-off), or an all-idle log.
- Evidence: In _extract_runs_from_speed (and _extract_runs_from_rpm), when the sub-threshold window reaches end-of-file (stage_end == n) the loop does `i += 1` and rescans the same window from each index. Measured: 24,000 idle rows (493 KB) took 39.4 s; a run plus a 60 s idle tail took 2.4 s. A 10-minute idle tail would take minutes; 30 minutes about an hour or more.
- Proposed fix: After scanning a sub-threshold window, set i = stage_end whatever the outcome (and likewise j in the RPM fallback).

## [low/safe] ECU parser rejects realistic logs outright: first column 'Vehicle…' or 'Session…' misdetected as MoTeC, and any text column drops every row
- Area: runtime — `motoquant/calibration/ecu.py` 501
- Verdicts: not yet verified
- Trigger: (a) Comma CSV whose header starts with 'Vehicle Speed (km/h),Time,RPM,…' (or 'Session Time', 'Event'). (b) A log with a non-numeric extra column, e.g. 'Lap Name' = 'Q1' or a date/time-of-day column. (c) A log with no time column.
- Evidence: (a) The MoTeC preamble regex ^\s*(Segment|Format|Venue|Vehicle|Driver|Event|Session) matches the header itself; the file is then tab-split and the first data row is consumed as 'units', giving 'ECUParseError: No numeric data rows found'. (b) Unmapped columns become extra_col_map entries, and one failed float() sets row_ok=False for the whole row, so ecu_textcol.csv gives 'No numeric data rows found'. (c) The no-time fallback is t = arange(n)/(n-1), which squashes a 16 s log to 1.0 s: sample_rate 1600 Hz, ET nan.
- Proposed fix: (a) Only treat the file as MoTeC when the preamble line is a key/value line (e.g. contains a tab or ',' followed by a value) and the header row is tab-delimited. (b) Parse extra columns best-effort (NaN on failure) instead of rejecting the row. (c) Without a time column, raise ECUParseError or require a --sample-rate argument rather than inventing a 1 s axis.

## [low/safe] 'SAE J1349' correction omits the standard's 1.18/−0.18 mechanical-efficiency terms
- Area: runtime — `motoquant/calibration/dyno.py` 156
- Verdicts: not yet verified
- Trigger: Any corrected dyno import (temp_c and pressure_kpa supplied), e.g. 35 °C / 95 kPa / 60% RH.
- Evidence: The code computes CF = (99/Pd)·sqrt(T/298.15). SAE J1349 (JUN90/AUG2004, and DynoJet's 'SAE' mode) is CF = 1.18·(99/Pd)·sqrt(T/298) − 0.18, so every deviation from 1 is understated by 18%. At 35 °C / 95 kPa / 60% RH the module gives CF ≈ 1.098 against the standard's ≈ 1.116, about 1.6% power. The module, CLI and API all label the value 'SAE J1349'.
- Proposed fix: Use cf = 1.18*(99/p_dry)*sqrt(T/298.15) - 0.18, or rename the correction (e.g. 'simple/DIN-style') if the friction-free form is intended. Update the test that asserts CF direction.

## [low/safe] SSRF guard allows 100.64.0.0/10 (shared/CGNAT), which includes Alibaba Cloud metadata 100.100.100.200
- Area: runtime — `motoquant/llm/webtools.py` 83
- Verdicts: not yet verified
- Trigger: web_fetch('http://100.100.100.200/latest/meta-data/') or any host resolving into 100.64.0.0/10 (Tailscale nodes, carrier-grade NAT internal hosts) on a self-hosted deployment.
- Evidence: _host_is_private checks is_private/is_loopback/is_link_local/is_reserved/is_multicast/is_unspecified; for 100.64.0.1 all are False on Python 3.11 and 3.13 (ALLOWED), while ipaddress.ip_address('100.100.100.200').is_global is False.
- Proposed fix: Block whenever `not ip.is_global` (plus the existing checks), which covers 100.64/10, 192.0.0.0/24, benchmarking ranges and others.

## [low/safe] Bike resolver misses common catalog queries ('RE Classic 350', 'Kawasaki ZX10R', 'GSX-R1000 K5')
- Area: runtime — `motoquant/llm/resolver.py` 121
- Verdicts: not yet verified
- Trigger: resolve_bike() from the chat pipeline with 'RE Classic 350', 'Kawasaki ZX10R', 'BMW S1000RR' or 'GSX-R1000 K5'.
- Evidence: Against the shipped DB: 'RE Classic 350' -> None, although the top suggestion is 'Classic 350 (2021-2026)'. 'RE' is stripped for searching, but scoring uses the raw query against the 'royal enfield' tokens (Jaccard 40 < 60). 'Kawasaki ZX10R' and 'BMW S1000RR' -> None with zero candidates (no letter/digit-boundary normalisation against 'Ninja ZX-10R' / 'S 1000 RR'). 'GSX-R1000 K5' -> None, although the catalog holds 'GSX-R 1000 K5/K6' (the K5 reference bike). The agent then reports the bike as not found or runs an LLM-recalled estimate instead of the curated config.
- Proposed fix: Score with the manufacturer-stripped query (or expand aliases such as 're' -> 'royal enfield'). Normalise tokens by splitting letter/digit boundaries and also comparing a joined (no-space/no-hyphen) form, so that 'zx10r' matches 'zx-10r' and 's1000rr' matches 's 1000 rr'. Add those queries to the resolver tests.

## [low/safe] Multi-run Dragy JSON reports wrong run_index (0, 2, 4…)
- Area: runtime — `motoquant/calibration/dragy.py` 560
- Verdicts: not yet verified
- Trigger: A Dragy JSON with 3 entries in 'runs'.
- Evidence: r.run_index = run_idx + len(results) double counts. Parsing a 3-run JSON gave run indices [0, 2, 4], and to_dict() exposes run_index.
- Proposed fix: Use r.run_index = len(results) + k for the k-th run in `partial` (a running counter).
