"""
MotoQuant Pro — Default Bike Configurations
==========================================
Real-world specifications for the three reference platforms.
All data from manufacturer service manuals and published dyno results.
"""

import numpy as np
from .models import (
    BikeConfig, ChassisParams, EngineParams, ForcedInductionParams,
    DrivetrainParams, ClutchParams, TireParams, AeroParams,
    SuspensionParams, BrakingParams, WheelieParams, RiderParams,
    ParasiticParams, StagingParams, EnvironmentParams, DynoCurve,
    CLUTCH_LOCKUP, CLUTCH_SLIPPER, BOOST_NA, DRIVE_CHAIN,
    STAGING_SHALLOW, TRACK_NONE, TRACK_VHT, RIDER_TUCK, FUEL_GASOLINE,
)


def _synthetic_torque_curve(peak_torque_nm: float, peak_rpm: float,
                            redline_rpm: float, idle_rpm: float = 2000,
                            peak_power_hp: float = None, peak_power_rpm: float = None,
                            points: int = 100) -> DynoCurve:
    """
    Generate a realistic inline-4 sportbike torque curve.

    The curve is constrained by:
      - Peak torque (Nm) at peak_rpm
      - Peak power (HP) at peak_power_rpm (if provided)
      - Smooth ramp from idle and decay to redline

    Uses an asymmetric bell: gentle Gaussian below peak, shaped falloff
    above peak calibrated so torque at peak_power_rpm produces the rated HP.
    """
    rpms = np.linspace(idle_rpm, redline_rpm, points)
    torque = np.zeros_like(rpms)

    # Torque required at peak power RPM to match rated HP
    if peak_power_hp is not None and peak_power_rpm is not None:
        T_at_peak_power = peak_power_hp * 745.7 / (peak_power_rpm * 2.0 * np.pi / 60.0)
    else:
        # Fallback: assume peak power at 90% of redline, ~85% of peak torque
        peak_power_rpm = redline_rpm * 0.9
        T_at_peak_power = peak_torque_nm * 0.85

    for i, rpm in enumerate(rpms):
        if rpm <= peak_rpm:
            # Below peak torque: Gaussian rise from low RPM
            x = (rpm - peak_rpm) / (peak_rpm - idle_rpm)
            # Broad Gaussian (sigma ~0.6 of the distance)
            T = peak_torque_nm * np.exp(-1.8 * x ** 2)
            # Low-RPM ramp: torque builds progressively from idle
            if rpm < peak_rpm * 0.6:
                ramp = max(0.25, (rpm - idle_rpm) / max(1.0, peak_rpm * 0.6 - idle_rpm))
                T *= ramp
        else:
            # Above peak torque: smooth interpolation between peak and redline
            # At peak_rpm: T = peak_torque_nm
            # At peak_power_rpm: T = T_at_peak_power (constrained by rated power)
            # At redline: T drops to ~60% of T_at_peak_power (typical rev limiter approach)
            frac = (rpm - peak_rpm) / max(1.0, redline_rpm - peak_rpm)
            if rpm <= peak_power_rpm:
                # Interpolate peak_torque → T_at_peak_power (gentle decline)
                frac_pp = (rpm - peak_rpm) / max(1.0, peak_power_rpm - peak_rpm)
                T = peak_torque_nm + (T_at_peak_power - peak_torque_nm) * frac_pp
            else:
                # Beyond peak power RPM: steeper decline toward redline
                frac_rl = (rpm - peak_power_rpm) / max(1.0, redline_rpm - peak_power_rpm)
                T_at_redline = T_at_peak_power * 0.55  # Steep falloff near limiter
                T = T_at_peak_power + (T_at_redline - T_at_peak_power) * frac_rl ** 1.5
            T = max(0.0, T)
        torque[i] = T

    torque = np.clip(torque, 0.0, peak_torque_nm * 1.05)
    return DynoCurve(rpm=rpms, torque_nm=torque, is_at_wheel=True)


def gsxr1000_k5() -> BikeConfig:
    """
    Suzuki GSX-R 1000 K5/K6 (2005-2006)
    Published quarter-mile: ~10.0 s @ 230 km/h (stock, sea level)
    """
    # Realistic torque curve for the K5 (measured ~160 HP at wheel)
    dyno = _synthetic_torque_curve(
        peak_torque_nm=115.0,  # ~115 Nm at wheel
        peak_rpm=9500,
        redline_rpm=13000,
        idle_rpm=1200,
        peak_power_hp=160.0,   # 160 HP at wheel
        peak_power_rpm=11500,
    )

    return BikeConfig(
        name="Suzuki GSX-R 1000 K5/K6",
        chassis=ChassisParams(
            dry_mass_kg=166.0,        # Dry weight
            rider_mass_kg=75.0,
            fluid_mass_kg=17.0,       # Full fuel + fluids
            fuel_mass_kg=18.0,        # 17.5L tank
            wheelbase_mm=1405.0,
            cog_height_mm=540.0,      # Estimated bike+rider
            front_weight_pct=0.52,
            rake_deg=23.4,
            trail_mm=97.0,
            seat_height_mm=810.0,
        ),
        engine=EngineParams(
            dyno_curve=dyno,
            peak_power_hp=160.0,      # At wheel (chassis dyno)
            peak_torque_nm=115.0,     # At wheel
            peak_power_rpm=11500,
            peak_torque_rpm=9500,
            redline_rpm=13000,
            launch_rpm=8000,
            idle_rpm=1200,
            displacement_cc=999,
            bore_mm=73.4,
            stroke_mm=59.0,
            compression_ratio=12.5,
            engine_inertia_kgm2=0.04,
            crank_rotation_cw=True,
            counter_rotating=False,
            fuel_type=FUEL_GASOLINE,
            afr_wot=12.5,
            coolant_temp_c=85.0,
            motoring_torque_nm=40.0,
        ),
        forced_induction=ForcedInductionParams(boost_type=BOOST_NA),
        drivetrain=DrivetrainParams(
            primary_ratio=1.553,      # 73/47
            gear_ratios=[2.562, 1.947, 1.565, 1.350, 1.208, 1.064],
            final_drive_ratio=2.471,  # 42/17
            front_sprocket=17,
            rear_sprocket=42,
            chain_pitch_mm=15.875,    # 530 chain
            chain_links=110,
            chain_slack_mm=25.0,
            drive_type=DRIVE_CHAIN,
            primary_efficiency=0.99,
            trans_efficiency_per_mesh=0.985,
            chain_efficiency=0.97,
            clutch_type=CLUTCH_LOCKUP,
            clutch_engage_rpm=6000,
            air_shifter=False,
            shift_cut_type="ignition",
            shift_cut_duration_ms=65,
            total_shift_time_ms=120,
        ),
        clutch=ClutchParams(
            clutch_type=CLUTCH_LOCKUP,
            plate_count=8,
            plate_od_mm=120,
            plate_id_mm=85,
            mu_static=0.38,
            spring_preload_n=1200,
            engage_rpm=6000,
            basket_inertia_kgm2=0.01,
            thermal_mass_jk=500,
            fade_temp_c=250,
            slipper_ratio=0.0,       # No slipper on K5
        ),
        tires=TireParams(
            rear_model="Stock Bridgestone BT014R",
            rear_size="190/50-17",
            rear_rolling_radius_m=0.302,
            rear_pressure_psi=28.0,
            rear_mass_kg=6.0,
            rear_inertia_kgm2=0.55,
            front_size="120/70-17",
            front_rolling_radius_m=0.305,
            front_pressure_psi=33.0,
            front_mass_kg=4.0,
            front_inertia_kgm2=0.35,
            mu_peak=1.40,             # Sport radial on prepped surface
            mu_slide=1.05,
            load_sensitivity_k=0.00003,  # Low for modern radial sport compound
            pacejka_B=10.0,
            pacejka_C=1.65,
            pacejka_D=1.4,
            pacejka_E=-0.5,
            optimal_temp_c=65.0,
            reversion_temp_c=105.0,
            growth_coeff=2e-9,
            crr_base=0.012,
            crr_speed_coeff=5e-6,
            burnout_end_temp_c=80.0,   # Proper burnout heats tire significantly
            time_burnout_to_launch_s=8.0,  # Quick staging after burnout
            track_prep_type=TRACK_VHT,     # Prepped drag strip surface
        ),
        aero=AeroParams(
            cd=0.70,
            frontal_area_m2=0.45,
            cl=0.08,
            rider_position=RIDER_TUCK,
            belly_pan=False,
            ram_air_efficiency=0.6,
            ram_air_area_cm2=20.0,
        ),
        suspension=SuspensionParams(
            front_spring_rate_nmm=10.0,
            rear_spring_rate_nmm=85.0,
            swingarm_length_mm=590.0,
            swingarm_extension_mm=0.0,
            anti_squat_pct=85.0,
            static_sag_mm=30.0,
        ),
        braking=BrakingParams(
            front_disc_dia_mm=310.0,
            front_caliper_pistons=4,
            rear_disc_dia_mm=220.0,
            abs_equipped=False,       # No ABS on K5
        ),
        wheelie=WheelieParams(wheelie_bar=False),
        rider=RiderParams(
            mass_kg=75.0,
            height_cm=175,
            launch_forward_shift_mm=80,
            tuck_transition_time_s=2.0,
        ),
        parasitic=ParasiticParams(alternator_present=True),
        staging=StagingParams(
            staging_type=STAGING_SHALLOW,
            rollout_distance_mm=350,
            launch_rpm=8000,
            two_step=False,
        ),
        environment=EnvironmentParams(
            venue_name="Sea Level Reference",
            altitude_m=0,
            ambient_temp_c=25.0,
            relative_humidity_pct=50.0,
            barometric_pressure_hpa=1013.25,
            track_temp_c=30.0,
        ),
    )


def yzfr1_4c8() -> BikeConfig:
    """
    Yamaha YZF-R1 4C8 (2007-2008) — Crossplane crank
    Published quarter-mile: ~10.2 s @ 225 km/h (stock, sea level)
    """
    dyno = _synthetic_torque_curve(
        peak_torque_nm=110.0,
        peak_rpm=9000,
        redline_rpm=12500,
        idle_rpm=1100,
        peak_power_hp=155.0,   # 155 HP at wheel
        peak_power_rpm=11000,
    )

    return BikeConfig(
        name="Yamaha YZF-R1 4C8",
        chassis=ChassisParams(
            dry_mass_kg=177.0,
            rider_mass_kg=75.0,
            fluid_mass_kg=17.0,
            fuel_mass_kg=18.0,
            wheelbase_mm=1415.0,
            cog_height_mm=545.0,
            front_weight_pct=0.53,
            rake_deg=24.0,
            trail_mm=102.0,
            seat_height_mm=835.0,
        ),
        engine=EngineParams(
            dyno_curve=dyno,
            peak_power_hp=155.0,
            peak_torque_nm=110.0,
            peak_power_rpm=11500,
            peak_torque_rpm=9000,
            redline_rpm=12500,
            launch_rpm=7500,
            idle_rpm=1100,
            displacement_cc=998,
            bore_mm=77.0,
            stroke_mm=53.6,
            compression_ratio=12.7,
            engine_inertia_kgm2=0.04,
            crank_rotation_cw=True,
            counter_rotating=True,     # Crossplane crank!
            fuel_type=FUEL_GASOLINE,
            afr_wot=12.5,
            motoring_torque_nm=38.0,
        ),
        forced_induction=ForcedInductionParams(boost_type=BOOST_NA),
        drivetrain=DrivetrainParams(
            primary_ratio=1.512,       # 65/43
            gear_ratios=[2.533, 2.063, 1.762, 1.522, 1.348, 1.208],
            final_drive_ratio=2.529,   # 43/17
            front_sprocket=17,
            rear_sprocket=43,
            chain_pitch_mm=15.875,
            chain_links=114,
            chain_slack_mm=28.0,
            drive_type=DRIVE_CHAIN,
            primary_efficiency=0.99,
            trans_efficiency_per_mesh=0.985,
            chain_efficiency=0.97,
            clutch_type=CLUTCH_LOCKUP,
            clutch_engage_rpm=5500,
            shift_cut_type="ignition",
            total_shift_time_ms=130,
        ),
        clutch=ClutchParams(
            clutch_type=CLUTCH_LOCKUP,
            plate_count=9,
            plate_od_mm=125,
            plate_id_mm=88,
            mu_static=0.38,
            spring_preload_n=1100,
            engage_rpm=5500,
            basket_inertia_kgm2=0.012,
            thermal_mass_jk=550,
            fade_temp_c=250,
            slipper_ratio=0.4,        # Has slipper clutch
        ),
        tires=TireParams(
            rear_model="Stock Dunlop Sportmax",
            rear_size="190/50-17",
            rear_rolling_radius_m=0.302,
            rear_pressure_psi=28.0,
            rear_mass_kg=6.0,
            rear_inertia_kgm2=0.55,
            mu_peak=1.40,
            load_sensitivity_k=0.00003,
            crr_base=0.012,
            growth_coeff=2e-9,
            burnout_end_temp_c=80.0,
            time_burnout_to_launch_s=8.0,
            track_prep_type=TRACK_VHT,
        ),
        aero=AeroParams(
            cd=0.72,
            frontal_area_m2=0.44,
            cl=0.08,
            rider_position=RIDER_TUCK,
            ram_air_efficiency=0.65,
            ram_air_area_cm2=25.0,
        ),
        wheelie=WheelieParams(wheelie_bar=False),
        rider=RiderParams(mass_kg=75.0, launch_forward_shift_mm=80),
        staging=StagingParams(launch_rpm=7500, two_step=False),
        environment=EnvironmentParams(
            venue_name="Sea Level Reference",
            altitude_m=0,
            ambient_temp_c=25.0,
            relative_humidity_pct=50.0,
        ),
    )


def hayabusa_gen1() -> BikeConfig:
    """
    Suzuki Hayabusa GSX1300R Gen1 (1999-2007)
    Published quarter-mile: ~9.8-10.0 s @ 235 km/h (stock, sea level)
    Heavier but more powerful, geared for top speed.
    """
    dyno = _synthetic_torque_curve(
        peak_torque_nm=130.0,         # More torque than the 1000s
        peak_rpm=8500,
        redline_rpm=11000,
        idle_rpm=1100,
        peak_power_hp=170.0,   # 170 HP at wheel (Gen1 with ram air)
        peak_power_rpm=10000,
    )

    return BikeConfig(
        name="Suzuki Hayabusa GSX1300R Gen1",
        chassis=ChassisParams(
            dry_mass_kg=215.0,        # Heavier than litre bikes
            rider_mass_kg=75.0,
            fluid_mass_kg=22.0,       # Bigger tank
            fuel_mass_kg=21.0,
            wheelbase_mm=1485.0,      # Longer wheelbase
            cog_height_mm=530.0,      # Lower CoG (touring geometry)
            front_weight_pct=0.51,
            rake_deg=25.0,
            trail_mm=107.0,
            seat_height_mm=805.0,
        ),
        engine=EngineParams(
            dyno_curve=dyno,
            peak_power_hp=170.0,      # Stock at wheel
            peak_torque_nm=130.0,
            peak_power_rpm=10000,
            peak_torque_rpm=8500,
            redline_rpm=11000,
            launch_rpm=7000,
            idle_rpm=1100,
            displacement_cc=1299,
            bore_mm=81.0,
            stroke_mm=63.0,
            compression_ratio=11.0,
            engine_inertia_kgm2=0.055, # Bigger engine
            crank_rotation_cw=True,
            counter_rotating=False,
            fuel_type=FUEL_GASOLINE,
            afr_wot=12.5,
            motoring_torque_nm=50.0,  # More engine braking
        ),
        forced_induction=ForcedInductionParams(boost_type=BOOST_NA),
        drivetrain=DrivetrainParams(
            primary_ratio=1.596,       # 83/52 (actually varies by source)
            gear_ratios=[2.615, 1.937, 1.526, 1.285, 1.136, 1.043],
            final_drive_ratio=2.353,   # 40/17
            front_sprocket=17,
            rear_sprocket=40,
            chain_pitch_mm=15.875,     # 530 chain
            chain_links=114,
            chain_slack_mm=30.0,
            drive_type=DRIVE_CHAIN,
            primary_efficiency=0.99,
            trans_efficiency_per_mesh=0.985,
            chain_efficiency=0.97,
            clutch_type=CLUTCH_LOCKUP,
            clutch_engage_rpm=5500,
            total_shift_time_ms=140,
        ),
        clutch=ClutchParams(
            clutch_type=CLUTCH_LOCKUP,
            plate_count=9,
            plate_od_mm=130,
            plate_id_mm=90,
            mu_static=0.38,
            spring_preload_n=1400,
            engage_rpm=5500,
            basket_inertia_kgm2=0.015,
            thermal_mass_jk=600,
            fade_temp_c=250,
            slipper_ratio=0.0,
        ),
        tires=TireParams(
            rear_model="Stock Bridgestone BT56R",
            rear_size="190/50-17",
            rear_rolling_radius_m=0.302,
            rear_pressure_psi=28.0,
            rear_mass_kg=6.5,
            rear_inertia_kgm2=0.58,
            mu_peak=1.40,
            load_sensitivity_k=0.00003,
            crr_base=0.012,
            growth_coeff=2e-9,
            burnout_end_temp_c=80.0,
            time_burnout_to_launch_s=8.0,
            track_prep_type=TRACK_VHT,
        ),
        aero=AeroParams(
            cd=0.62,                   # More aerodynamic (full fairing)
            frontal_area_m2=0.50,      # Wider
            cl=0.06,
            rider_position=RIDER_TUCK,
            ram_air_efficiency=0.70,   # Good ram air system
            ram_air_area_cm2=30.0,
        ),
        wheelie=WheelieParams(wheelie_bar=False),
        rider=RiderParams(mass_kg=75.0, launch_forward_shift_mm=80),
        staging=StagingParams(launch_rpm=7000, two_step=False),
        environment=EnvironmentParams(
            venue_name="Sea Level Reference",
            altitude_m=0,
            ambient_temp_c=25.0,
            relative_humidity_pct=50.0,
        ),
    )


def aamby_valley_winter(config: BikeConfig) -> BikeConfig:
    """Apply Aamby Valley TVR Winter Edition conditions to any bike config."""
    config.environment = EnvironmentParams(
        venue_name="Aamby Valley (TVR Winter)",
        altitude_m=679.0,
        ambient_temp_c=20.0,
        relative_humidity_pct=35.0,
        barometric_pressure_hpa=1013.25,
        track_temp_c=25.0,
        track_surface="asphalt",
        track_prep=TRACK_NONE,
    )
    return config


def aamby_valley_summer(config: BikeConfig) -> BikeConfig:
    """Apply Aamby Valley TVR Summer Edition conditions to any bike config."""
    config.environment = EnvironmentParams(
        venue_name="Aamby Valley (TVR Summer)",
        altitude_m=679.0,
        ambient_temp_c=30.0,
        relative_humidity_pct=70.0,
        barometric_pressure_hpa=1013.25,
        track_temp_c=42.0,
        track_surface="asphalt",
        track_prep=TRACK_NONE,
    )
    return config
