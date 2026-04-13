"""
MotoQuant Pro — Database Seeder
===============================
Migrate Phase 1 hardcoded defaults into the database.

Seeds:
  - 3 reference bikes (GSX-R 1000 K5, YZF-R1 4C8, Hayabusa Gen1)
  - Validation benchmarks for each
  - Sample tire entries
  - Sample performance parts (Indian market)
  - Provenance records for all seeded data
"""

from .connection import MotoQuantDB
from ..defaults import gsxr1000_k5, yzfr1_4c8, hayabusa_gen1


def seed_reference_bikes(db: MotoQuantDB):
    """Seed the 3 Phase 1 reference bikes with full provenance."""
    bikes = [
        {
            "factory": gsxr1000_k5,
            "manufacturer": "Suzuki",
            "model_code": "K5",
            "year_from": 2005,
            "year_to": 2006,
            "category": "sport",
            "validation_et": 9.97,
            "validation_trap": 230.0,
            "validation_source": "MotoQuant Phase 1 calibration (published magazine tests)",
            "confidence": 0.85,
        },
        {
            "factory": yzfr1_4c8,
            "manufacturer": "Yamaha",
            "model_code": "4C8",
            "year_from": 2007,
            "year_to": 2008,
            "category": "sport",
            "validation_et": 10.3,
            "validation_trap": 225.0,
            "validation_source": "MotoQuant Phase 1 calibration (published magazine tests)",
            "confidence": 0.80,
        },
        {
            "factory": hayabusa_gen1,
            "manufacturer": "Suzuki",
            "model_code": "Gen1",
            "year_from": 1999,
            "year_to": 2007,
            "category": "sport",
            "validation_et": 9.9,
            "validation_trap": 235.0,
            "validation_source": "MotoQuant Phase 1 calibration (published tests + drag results)",
            "confidence": 0.85,
        },
    ]

    for bike_info in bikes:
        config = bike_info["factory"]()

        model_id, config_id = db.bikes.upsert_from_config(
            config=config,
            manufacturer_name=bike_info["manufacturer"],
            model_code=bike_info["model_code"],
            year_from=bike_info["year_from"],
            year_to=bike_info["year_to"],
            category=bike_info["category"],
            source="spec_sheet",
            confidence=bike_info["confidence"],
        )

        # Set validation benchmark
        db.bikes.set_validation_benchmark(
            model_id=model_id,
            et_s=bike_info["validation_et"],
            trap_kmh=bike_info["validation_trap"],
            source=bike_info["validation_source"],
        )

        # Add provenance for key parameters
        critical_fields = [
            ("engine.dyno_curve", "estimation", 0.70,
             "Synthetic curve from _synthetic_torque_curve(), calibrated to match published WHP"),
            ("engine.displacement_cc", "manufacturer_spec", 0.99,
             "From service manual"),
            ("chassis.dry_mass_kg", "manufacturer_spec", 0.95,
             "Published dry weight"),
            ("drivetrain.gear_ratios", "manufacturer_spec", 0.99,
             "From service manual"),
            ("drivetrain.front_sprocket", "manufacturer_spec", 0.99,
             "Stock sprocket"),
            ("drivetrain.rear_sprocket", "manufacturer_spec", 0.99,
             "Stock sprocket"),
            ("tires.mu_peak", "estimation", 0.60,
             "Estimated for sport radial on prepped surface; needs track validation"),
            ("tires.pacejka_B", "estimation", 0.50,
             "Generic sport tire Pacejka; high uncertainty"),
            ("aero.cd", "estimation", 0.55,
             "Estimated from frontal area and fairing type; CFD or wind tunnel needed"),
            ("chassis.cog_height_mm", "estimation", 0.50,
             "Estimated combined bike+rider CoG; very sensitive parameter"),
        ]

        for field_path, source_type, confidence, notes in critical_fields:
            db.bikes.add_provenance(
                entity_id=config_id,
                field_path=field_path,
                source_type=source_type,
                confidence=confidence,
                entity_type="bike_config",
                notes=notes,
            )

    return len(bikes)


def seed_sample_tires(db: MotoQuantDB):
    """Seed tire library with common drag-relevant tires available in India."""
    tires = [
        # Rear drag/sport tires
        {
            "manufacturer": "Michelin",
            "model_name": "Power GP2",
            "size": "190/55ZR17",
            "compound": "race",
            "position": "rear",
            "mu_peak": 1.45,
            "mu_slide": 1.10,
            "pacejka_B": 11.0, "pacejka_C": 1.65, "pacejka_D": 1.45, "pacejka_E": -0.4,
            "optimal_temp_c": 70.0, "reversion_temp_c": 110.0,
            "rolling_radius_m": 0.310, "mass_kg": 5.8, "inertia_kgm2": 0.52,
            "crr_base": 0.010, "growth_coeff": 2e-9,
            "recommended_psi": 32.0, "drag_pressure_psi": 24.0,
            "price_inr": 22000, "available_india": 1,
            "confidence": 0.65,
        },
        {
            "manufacturer": "Pirelli",
            "model_name": "Diablo Supercorsa SC2",
            "size": "190/55ZR17",
            "compound": "race",
            "position": "rear",
            "mu_peak": 1.50,
            "mu_slide": 1.15,
            "pacejka_B": 11.5, "pacejka_C": 1.65, "pacejka_D": 1.50, "pacejka_E": -0.3,
            "optimal_temp_c": 75.0, "reversion_temp_c": 115.0,
            "rolling_radius_m": 0.310, "mass_kg": 5.5, "inertia_kgm2": 0.50,
            "crr_base": 0.009, "growth_coeff": 2.2e-9,
            "recommended_psi": 30.0, "drag_pressure_psi": 22.0,
            "price_inr": 25000, "available_india": 1,
            "confidence": 0.70,
        },
        {
            "manufacturer": "Bridgestone",
            "model_name": "Battlax RS11",
            "size": "190/50ZR17",
            "compound": "sport",
            "position": "rear",
            "mu_peak": 1.38,
            "mu_slide": 1.05,
            "pacejka_B": 10.0, "pacejka_C": 1.65, "pacejka_D": 1.38, "pacejka_E": -0.5,
            "optimal_temp_c": 60.0, "reversion_temp_c": 100.0,
            "rolling_radius_m": 0.302, "mass_kg": 6.0, "inertia_kgm2": 0.55,
            "crr_base": 0.012, "growth_coeff": 2e-9,
            "recommended_psi": 36.0, "drag_pressure_psi": 26.0,
            "price_inr": 18000, "available_india": 1,
            "confidence": 0.60,
        },
        {
            "manufacturer": "Dunlop",
            "model_name": "Sportmax Q4",
            "size": "190/55ZR17",
            "compound": "race",
            "position": "rear",
            "mu_peak": 1.48,
            "mu_slide": 1.12,
            "pacejka_B": 11.0, "pacejka_C": 1.65, "pacejka_D": 1.48, "pacejka_E": -0.35,
            "optimal_temp_c": 72.0, "reversion_temp_c": 112.0,
            "rolling_radius_m": 0.310, "mass_kg": 5.6, "inertia_kgm2": 0.51,
            "crr_base": 0.010, "growth_coeff": 2.1e-9,
            "recommended_psi": 31.0, "drag_pressure_psi": 23.0,
            "price_inr": 20000, "available_india": 0,  # Import only
            "confidence": 0.65,
        },
        # Front tires
        {
            "manufacturer": "Michelin",
            "model_name": "Power GP2",
            "size": "120/70ZR17",
            "compound": "race",
            "position": "front",
            "mu_peak": 1.40,
            "mu_slide": 1.05,
            "pacejka_B": 10.0, "pacejka_C": 1.65, "pacejka_D": 1.40, "pacejka_E": -0.5,
            "rolling_radius_m": 0.305, "mass_kg": 4.0, "inertia_kgm2": 0.35,
            "crr_base": 0.010,
            "recommended_psi": 33.0,
            "price_inr": 18000, "available_india": 1,
            "confidence": 0.65,
        },
        # Indian market tire
        {
            "manufacturer": "MRF",
            "model_name": "Revz FC1",
            "size": "190/50ZR17",
            "compound": "sport",
            "position": "rear",
            "mu_peak": 1.30,
            "mu_slide": 0.98,
            "pacejka_B": 9.5, "pacejka_C": 1.60, "pacejka_D": 1.30, "pacejka_E": -0.6,
            "optimal_temp_c": 55.0, "reversion_temp_c": 95.0,
            "rolling_radius_m": 0.302, "mass_kg": 6.5, "inertia_kgm2": 0.58,
            "crr_base": 0.014, "growth_coeff": 2e-9,
            "recommended_psi": 36.0, "drag_pressure_psi": 28.0,
            "price_inr": 8500, "available_india": 1,
            "confidence": 0.55,
        },
    ]

    count = 0
    for t in tires:
        kwargs = {k: v for k, v in t.items()
                  if k not in ("manufacturer", "model_name", "size", "compound", "position")}
        db.tires.create(
            manufacturer_name=t["manufacturer"],
            model_name=t["model_name"],
            size_designation=t["size"],
            compound_type=t["compound"],
            position=t["position"],
            **kwargs,
        )
        count += 1
    return count


def seed_sample_parts(db: MotoQuantDB):
    """Seed sample performance parts with Indian market pricing."""
    parts = [
        # Sprockets
        {
            "category": "sprocket",
            "brand": "Driven Racing",
            "model_name": "520 Front Sprocket 15T",
            "part_number": "DR-520-15F",
            "specs": {"teeth": 15, "pitch": "520", "position": "front"},
            "param_overrides": {"drivetrain.front_sprocket": 15},
            "price_inr": 2800,
            "availability": "in_stock",
            "retailer": "MotoParts India",
            "universal": True,
        },
        {
            "category": "sprocket",
            "brand": "Driven Racing",
            "model_name": "520 Front Sprocket 16T",
            "part_number": "DR-520-16F",
            "specs": {"teeth": 16, "pitch": "520", "position": "front"},
            "param_overrides": {"drivetrain.front_sprocket": 16},
            "price_inr": 2800,
            "availability": "in_stock",
            "retailer": "MotoParts India",
            "universal": True,
        },
        {
            "category": "sprocket",
            "brand": "Driven Racing",
            "model_name": "530 Rear Sprocket 44T",
            "part_number": "DR-530-44R",
            "specs": {"teeth": 44, "pitch": "530", "position": "rear"},
            "param_overrides": {"drivetrain.rear_sprocket": 44},
            "price_inr": 4500,
            "availability": "in_stock",
            "retailer": "MotoParts India",
            "universal": False,
        },
        {
            "category": "sprocket",
            "brand": "Driven Racing",
            "model_name": "530 Rear Sprocket 45T",
            "part_number": "DR-530-45R",
            "specs": {"teeth": 45, "pitch": "530", "position": "rear"},
            "param_overrides": {"drivetrain.rear_sprocket": 45},
            "price_inr": 4500,
            "availability": "in_stock",
            "retailer": "MotoParts India",
            "universal": False,
        },
        # Chain
        {
            "category": "chain",
            "brand": "RK",
            "model_name": "GB530GXW Gold X-Ring 120L",
            "part_number": "RK-530GXW-120",
            "specs": {"pitch": "530", "links": 120, "type": "x-ring"},
            "param_overrides": {"drivetrain.chain_links": 120},
            "param_multipliers": {"drivetrain.chain_efficiency": 1.02},
            "price_inr": 9500,
            "availability": "in_stock",
            "retailer": "Grand Pitstop",
        },
        # ECU
        {
            "category": "ecu",
            "brand": "Woolich Racing",
            "model_name": "ECU Flash Stage 1",
            "part_number": "WR-FLASH-S1",
            "specs": {"type": "flash", "stage": 1, "features": ["rev_limiter_raise", "fuel_map", "ignition_map"]},
            "param_deltas": {"engine.peak_power_hp": 8.0, "engine.peak_torque_nm": 5.0},
            "param_overrides": {"engine.redline_rpm": 13500, "staging.two_step": True,
                                "staging.launch_rpm": 9000},
            "price_inr": 18000,
            "availability": "in_stock",
            "retailer": "Woolich Racing India",
        },
        # Exhaust
        {
            "category": "exhaust",
            "brand": "Akrapovic",
            "model_name": "Racing Full System GP Ti",
            "part_number": "AK-S-S10R-GP",
            "specs": {"type": "full_system", "material": "titanium", "weight_kg": 4.2},
            "param_deltas": {"engine.peak_power_hp": 6.0, "engine.peak_torque_nm": 4.0},
            "param_multipliers": {"chassis.dry_mass_kg": 0.96},
            "price_inr": 185000,
            "availability": "order",
            "retailer": "Superbike India",
            "delivery_days": 30,
        },
        # Clutch
        {
            "category": "clutch_kit",
            "brand": "Barnett",
            "model_name": "Extra Plate Kevlar Kit",
            "part_number": "BN-306-25-40002",
            "specs": {"material": "kevlar", "plates": 9, "extra_plates": 1},
            "param_overrides": {
                "clutch.plate_count": 9,
                "clutch.friction_material": "kevlar",
                "clutch.mu_static": 0.45,
            },
            "price_inr": 12000,
            "availability": "in_stock",
            "retailer": "MotoParts India",
        },
        # Quickshifter
        {
            "category": "quickshifter",
            "brand": "HM Quickshifter",
            "model_name": "Super Lite Universal",
            "part_number": "HM-QS-SLU",
            "specs": {"type": "push", "sensor": "strain_gauge"},
            "param_overrides": {
                "drivetrain.quickshifter": True,
                "drivetrain.total_shift_time_ms": 60.0,
                "drivetrain.shift_cut_duration_ms": 40.0,
            },
            "price_inr": 22000,
            "availability": "order",
            "retailer": "HM India",
            "universal": True,
            "delivery_days": 14,
        },
        # Swingarm extension
        {
            "category": "swingarm_ext",
            "brand": "Voodoo Industries",
            "model_name": '6" Swingarm Extension Kit',
            "part_number": "VI-SAE-6",
            "specs": {"extension_mm": 152.4, "material": "billet_aluminum"},
            "param_overrides": {"chassis.swingarm_extension_mm": 152.4},
            "price_inr": 35000,
            "availability": "import_only",
            "retailer": "Voodoo Ind. (US)",
            "delivery_days": 45,
        },
    ]

    count = 0
    for p in parts:
        db.parts.create(
            category_name=p["category"],
            brand=p["brand"],
            model_name=p["model_name"],
            specifications=p["specs"],
            part_number=p.get("part_number"),
            fitment_universal=p.get("universal", False),
            fitment_notes=p.get("fitment_notes"),
            param_overrides=p.get("param_overrides"),
            param_deltas=p.get("param_deltas"),
            param_multipliers=p.get("param_multipliers"),
            price_inr=p.get("price_inr"),
            retailer=p.get("retailer"),
            availability=p.get("availability", "in_stock"),
            estimated_delivery_days=p.get("delivery_days"),
        )
        count += 1
    return count


def seed_tire_library(db: MotoQuantDB) -> int:
    """
    Expanded tire library: ~30 tires covering all drag-relevant compounds,
    manufacturers, and positions. Includes full Pacejka coefficients,
    thermal model, Indian market pricing.

    Pacejka longitudinal Magic Formula:
        F = D * sin(C * arctan(B*slip - E*(B*slip - arctan(B*slip))))
    where D = mu_peak, C = shape, B = stiffness, E = curvature.

    Thermal model: grip = D * f(T), where f peaks at optimal_temp_c and
    declines toward reversion_temp_c above/below.
    """
    tires = [

        # ── MICHELIN ──────────────────────────────────────────────────────
        {
            "manufacturer": "Michelin", "model_name": "Power Cup 2",
            "size": "190/55ZR17", "compound": "race", "position": "rear",
            "mu_peak": 1.48, "mu_slide": 1.12,
            "pacejka_B": 11.5, "pacejka_C": 1.65, "pacejka_D": 1.48, "pacejka_E": -0.35,
            "optimal_temp_c": 68.0, "reversion_temp_c": 108.0,
            "thermal_conductivity": 0.20, "tread_mass_kg": 2.4, "specific_heat": 1700,
            "rolling_radius_m": 0.310, "mass_kg": 5.8, "inertia_kgm2": 0.52,
            "crr_base": 0.010, "crr_speed_coeff": 2.5e-5, "crr_temp_coeff": -0.0002,
            "growth_coeff": 2.0e-9, "construction": "radial",
            "recommended_psi": 32.0, "drag_pressure_psi": 24.0,
            "price_inr": 21000, "available_india": 1, "confidence": 0.68,
        },
        {
            "manufacturer": "Michelin", "model_name": "Power Cup 2",
            "size": "120/70ZR17", "compound": "race", "position": "front",
            "mu_peak": 1.42, "mu_slide": 1.06,
            "pacejka_B": 10.0, "pacejka_C": 1.65, "pacejka_D": 1.42, "pacejka_E": -0.48,
            "optimal_temp_c": 65.0, "reversion_temp_c": 105.0,
            "rolling_radius_m": 0.305, "mass_kg": 4.0, "inertia_kgm2": 0.35,
            "crr_base": 0.010,
            "recommended_psi": 33.0,
            "price_inr": 17500, "available_india": 1, "confidence": 0.65,
        },
        {
            "manufacturer": "Michelin", "model_name": "Power Slick 2",
            "size": "190/55ZR17", "compound": "drag_slick", "position": "rear",
            "mu_peak": 1.65, "mu_slide": 1.28,
            "pacejka_B": 13.5, "pacejka_C": 1.65, "pacejka_D": 1.65, "pacejka_E": -0.15,
            "optimal_temp_c": 85.0, "reversion_temp_c": 130.0,
            "thermal_conductivity": 0.22, "tread_mass_kg": 2.8, "specific_heat": 1650,
            "rolling_radius_m": 0.312, "mass_kg": 5.2, "inertia_kgm2": 0.48,
            "crr_base": 0.008, "crr_speed_coeff": 2.0e-5, "crr_temp_coeff": -0.0003,
            "growth_coeff": 2.5e-9, "construction": "radial",
            "recommended_psi": 26.0, "drag_pressure_psi": 18.0,
            "price_inr": 28000, "available_india": 0, "confidence": 0.75,
        },
        {
            "manufacturer": "Michelin", "model_name": "Pilot Power 3",
            "size": "190/55ZR17", "compound": "sport", "position": "rear",
            "mu_peak": 1.33, "mu_slide": 1.00,
            "pacejka_B": 9.5, "pacejka_C": 1.65, "pacejka_D": 1.33, "pacejka_E": -0.55,
            "optimal_temp_c": 55.0, "reversion_temp_c": 92.0,
            "rolling_radius_m": 0.310, "mass_kg": 6.1, "inertia_kgm2": 0.54,
            "crr_base": 0.012, "crr_speed_coeff": 3.0e-5,
            "growth_coeff": 1.8e-9, "construction": "radial",
            "recommended_psi": 36.0, "drag_pressure_psi": 28.0,
            "price_inr": 16000, "available_india": 1, "confidence": 0.60,
        },
        {
            "manufacturer": "Michelin", "model_name": "Road 6",
            "size": "190/55ZR17", "compound": "street", "position": "rear",
            "mu_peak": 1.20, "mu_slide": 0.90,
            "pacejka_B": 8.5, "pacejka_C": 1.65, "pacejka_D": 1.20, "pacejka_E": -0.65,
            "optimal_temp_c": 45.0, "reversion_temp_c": 85.0,
            "rolling_radius_m": 0.310, "mass_kg": 6.5, "inertia_kgm2": 0.57,
            "crr_base": 0.013, "crr_speed_coeff": 3.5e-5,
            "growth_coeff": 1.6e-9, "construction": "radial",
            "recommended_psi": 38.0, "drag_pressure_psi": 30.0,
            "price_inr": 13500, "available_india": 1, "confidence": 0.55,
        },

        # ── PIRELLI ───────────────────────────────────────────────────────
        {
            "manufacturer": "Pirelli", "model_name": "Diablo Supercorsa SC2",
            "size": "190/55ZR17", "compound": "race", "position": "rear",
            "mu_peak": 1.50, "mu_slide": 1.15,
            "pacejka_B": 11.5, "pacejka_C": 1.65, "pacejka_D": 1.50, "pacejka_E": -0.30,
            "optimal_temp_c": 75.0, "reversion_temp_c": 115.0,
            "thermal_conductivity": 0.21, "tread_mass_kg": 2.5, "specific_heat": 1680,
            "rolling_radius_m": 0.310, "mass_kg": 5.5, "inertia_kgm2": 0.50,
            "crr_base": 0.009, "crr_speed_coeff": 2.2e-5, "crr_temp_coeff": -0.00025,
            "growth_coeff": 2.2e-9, "construction": "radial",
            "recommended_psi": 30.0, "drag_pressure_psi": 22.0,
            "price_inr": 25000, "available_india": 1, "confidence": 0.72,
        },
        {
            "manufacturer": "Pirelli", "model_name": "Diablo Supercorsa SC1",
            "size": "190/55ZR17", "compound": "race", "position": "rear",
            "mu_peak": 1.55, "mu_slide": 1.20,
            "pacejka_B": 12.0, "pacejka_C": 1.65, "pacejka_D": 1.55, "pacejka_E": -0.22,
            "optimal_temp_c": 80.0, "reversion_temp_c": 125.0,
            "thermal_conductivity": 0.22, "tread_mass_kg": 2.3, "specific_heat": 1650,
            "rolling_radius_m": 0.310, "mass_kg": 5.3, "inertia_kgm2": 0.49,
            "crr_base": 0.008, "crr_speed_coeff": 2.0e-5, "crr_temp_coeff": -0.0003,
            "growth_coeff": 2.3e-9, "construction": "radial",
            "recommended_psi": 28.0, "drag_pressure_psi": 20.0,
            "price_inr": 27000, "available_india": 1, "confidence": 0.70,
        },
        {
            "manufacturer": "Pirelli", "model_name": "Diablo Rosso Corsa II",
            "size": "190/55ZR17", "compound": "sport", "position": "rear",
            "mu_peak": 1.38, "mu_slide": 1.04,
            "pacejka_B": 10.0, "pacejka_C": 1.65, "pacejka_D": 1.38, "pacejka_E": -0.50,
            "optimal_temp_c": 60.0, "reversion_temp_c": 100.0,
            "rolling_radius_m": 0.310, "mass_kg": 6.0, "inertia_kgm2": 0.53,
            "crr_base": 0.011, "crr_speed_coeff": 2.8e-5,
            "growth_coeff": 1.9e-9, "construction": "radial",
            "recommended_psi": 34.0, "drag_pressure_psi": 26.0,
            "price_inr": 19500, "available_india": 1, "confidence": 0.62,
        },
        {
            "manufacturer": "Pirelli", "model_name": "Diablo Supercorsa SC2",
            "size": "120/70ZR17", "compound": "race", "position": "front",
            "mu_peak": 1.45, "mu_slide": 1.08,
            "pacejka_B": 10.5, "pacejka_C": 1.65, "pacejka_D": 1.45, "pacejka_E": -0.40,
            "optimal_temp_c": 72.0, "reversion_temp_c": 112.0,
            "rolling_radius_m": 0.305, "mass_kg": 4.1, "inertia_kgm2": 0.36,
            "crr_base": 0.010,
            "recommended_psi": 32.0,
            "price_inr": 21000, "available_india": 1, "confidence": 0.68,
        },

        # ── BRIDGESTONE ───────────────────────────────────────────────────
        {
            "manufacturer": "Bridgestone", "model_name": "Battlax Racing R11",
            "size": "190/55ZR17", "compound": "race", "position": "rear",
            "mu_peak": 1.42, "mu_slide": 1.07,
            "pacejka_B": 10.5, "pacejka_C": 1.65, "pacejka_D": 1.42, "pacejka_E": -0.42,
            "optimal_temp_c": 65.0, "reversion_temp_c": 105.0,
            "thermal_conductivity": 0.19, "tread_mass_kg": 2.5, "specific_heat": 1710,
            "rolling_radius_m": 0.310, "mass_kg": 5.7, "inertia_kgm2": 0.51,
            "crr_base": 0.010, "crr_speed_coeff": 2.5e-5, "crr_temp_coeff": -0.0002,
            "growth_coeff": 2.0e-9, "construction": "radial",
            "recommended_psi": 32.0, "drag_pressure_psi": 24.0,
            "price_inr": 20500, "available_india": 1, "confidence": 0.65,
        },
        {
            "manufacturer": "Bridgestone", "model_name": "Battlax Hypersport S22",
            "size": "190/55ZR17", "compound": "sport", "position": "rear",
            "mu_peak": 1.35, "mu_slide": 1.02,
            "pacejka_B": 9.8, "pacejka_C": 1.65, "pacejka_D": 1.35, "pacejka_E": -0.52,
            "optimal_temp_c": 58.0, "reversion_temp_c": 98.0,
            "rolling_radius_m": 0.310, "mass_kg": 6.2, "inertia_kgm2": 0.55,
            "crr_base": 0.012, "crr_speed_coeff": 2.8e-5,
            "growth_coeff": 1.8e-9, "construction": "radial",
            "recommended_psi": 36.0, "drag_pressure_psi": 27.0,
            "price_inr": 17500, "available_india": 1, "confidence": 0.60,
        },
        {
            "manufacturer": "Bridgestone", "model_name": "Battlax RS11",
            "size": "190/50ZR17", "compound": "sport", "position": "rear",
            "mu_peak": 1.38, "mu_slide": 1.05,
            "pacejka_B": 10.0, "pacejka_C": 1.65, "pacejka_D": 1.38, "pacejka_E": -0.50,
            "optimal_temp_c": 60.0, "reversion_temp_c": 100.0,
            "rolling_radius_m": 0.302, "mass_kg": 6.0, "inertia_kgm2": 0.55,
            "crr_base": 0.012, "crr_speed_coeff": 2.8e-5,
            "growth_coeff": 2.0e-9, "construction": "radial",
            "recommended_psi": 36.0, "drag_pressure_psi": 26.0,
            "price_inr": 18000, "available_india": 1, "confidence": 0.60,
        },

        # ── DUNLOP ────────────────────────────────────────────────────────
        {
            "manufacturer": "Dunlop", "model_name": "Sportmax Q4",
            "size": "190/55ZR17", "compound": "race", "position": "rear",
            "mu_peak": 1.48, "mu_slide": 1.12,
            "pacejka_B": 11.0, "pacejka_C": 1.65, "pacejka_D": 1.48, "pacejka_E": -0.35,
            "optimal_temp_c": 72.0, "reversion_temp_c": 112.0,
            "thermal_conductivity": 0.20, "tread_mass_kg": 2.4, "specific_heat": 1690,
            "rolling_radius_m": 0.310, "mass_kg": 5.6, "inertia_kgm2": 0.51,
            "crr_base": 0.010, "crr_speed_coeff": 2.4e-5,
            "growth_coeff": 2.1e-9, "construction": "radial",
            "recommended_psi": 31.0, "drag_pressure_psi": 23.0,
            "price_inr": 20000, "available_india": 0, "confidence": 0.65,
        },
        {
            "manufacturer": "Dunlop", "model_name": "Drag Radial D212 GP Pro",
            "size": "190/55ZR17", "compound": "drag_dot", "position": "rear",
            "mu_peak": 1.58, "mu_slide": 1.22,
            "pacejka_B": 12.5, "pacejka_C": 1.65, "pacejka_D": 1.58, "pacejka_E": -0.18,
            "optimal_temp_c": 78.0, "reversion_temp_c": 120.0,
            "thermal_conductivity": 0.22, "tread_mass_kg": 2.6, "specific_heat": 1660,
            "rolling_radius_m": 0.311, "mass_kg": 5.4, "inertia_kgm2": 0.49,
            "crr_base": 0.009, "crr_speed_coeff": 2.1e-5, "crr_temp_coeff": -0.0003,
            "growth_coeff": 2.4e-9, "construction": "radial",
            "recommended_psi": 26.0, "drag_pressure_psi": 18.0,
            "price_inr": 32000, "available_india": 0, "confidence": 0.78,
            # Notes: DOT-legal drag tire, classified as drag_dot
        },
        {
            "manufacturer": "Dunlop", "model_name": "Roadsmart IV",
            "size": "190/55ZR17", "compound": "street", "position": "rear",
            "mu_peak": 1.22, "mu_slide": 0.92,
            "pacejka_B": 8.8, "pacejka_C": 1.65, "pacejka_D": 1.22, "pacejka_E": -0.63,
            "optimal_temp_c": 45.0, "reversion_temp_c": 82.0,
            "rolling_radius_m": 0.310, "mass_kg": 6.8, "inertia_kgm2": 0.58,
            "crr_base": 0.013, "crr_speed_coeff": 3.8e-5,
            "growth_coeff": 1.5e-9, "construction": "radial",
            "recommended_psi": 38.0,
            "price_inr": 12000, "available_india": 0, "confidence": 0.50,
        },

        # ── METZELER ──────────────────────────────────────────────────────
        {
            "manufacturer": "Metzeler", "model_name": "Racetec RR K2",
            "size": "190/55ZR17", "compound": "race", "position": "rear",
            "mu_peak": 1.46, "mu_slide": 1.10,
            "pacejka_B": 11.0, "pacejka_C": 1.65, "pacejka_D": 1.46, "pacejka_E": -0.38,
            "optimal_temp_c": 70.0, "reversion_temp_c": 110.0,
            "thermal_conductivity": 0.20, "tread_mass_kg": 2.5, "specific_heat": 1700,
            "rolling_radius_m": 0.310, "mass_kg": 5.7, "inertia_kgm2": 0.51,
            "crr_base": 0.010, "crr_speed_coeff": 2.5e-5,
            "growth_coeff": 2.0e-9, "construction": "radial",
            "recommended_psi": 30.0, "drag_pressure_psi": 22.0,
            "price_inr": 22500, "available_india": 1, "confidence": 0.65,
        },
        {
            "manufacturer": "Metzeler", "model_name": "Sportec M9 RR",
            "size": "190/55ZR17", "compound": "sport", "position": "rear",
            "mu_peak": 1.36, "mu_slide": 1.03,
            "pacejka_B": 9.7, "pacejka_C": 1.65, "pacejka_D": 1.36, "pacejka_E": -0.53,
            "optimal_temp_c": 58.0, "reversion_temp_c": 97.0,
            "rolling_radius_m": 0.310, "mass_kg": 6.1, "inertia_kgm2": 0.54,
            "crr_base": 0.011, "crr_speed_coeff": 2.8e-5,
            "growth_coeff": 1.85e-9, "construction": "radial",
            "recommended_psi": 35.0, "drag_pressure_psi": 27.0,
            "price_inr": 18000, "available_india": 1, "confidence": 0.58,
        },

        # ── CONTINENTAL ───────────────────────────────────────────────────
        {
            "manufacturer": "Continental", "model_name": "ContiTrack",
            "size": "190/55ZR17", "compound": "race", "position": "rear",
            "mu_peak": 1.44, "mu_slide": 1.09,
            "pacejka_B": 10.8, "pacejka_C": 1.65, "pacejka_D": 1.44, "pacejka_E": -0.40,
            "optimal_temp_c": 68.0, "reversion_temp_c": 108.0,
            "rolling_radius_m": 0.310, "mass_kg": 5.8, "inertia_kgm2": 0.52,
            "crr_base": 0.010, "crr_speed_coeff": 2.5e-5,
            "growth_coeff": 1.95e-9, "construction": "radial",
            "recommended_psi": 31.0, "drag_pressure_psi": 23.0,
            "price_inr": 19000, "available_india": 1, "confidence": 0.60,
        },

        # ── MRF ───────────────────────────────────────────────────────────
        {
            "manufacturer": "MRF", "model_name": "Revz FC1",
            "size": "190/50ZR17", "compound": "sport", "position": "rear",
            "mu_peak": 1.30, "mu_slide": 0.98,
            "pacejka_B": 9.5, "pacejka_C": 1.60, "pacejka_D": 1.30, "pacejka_E": -0.60,
            "optimal_temp_c": 55.0, "reversion_temp_c": 95.0,
            "thermal_conductivity": 0.18, "tread_mass_kg": 2.7, "specific_heat": 1750,
            "rolling_radius_m": 0.302, "mass_kg": 6.5, "inertia_kgm2": 0.58,
            "crr_base": 0.014, "crr_speed_coeff": 3.2e-5,
            "growth_coeff": 2.0e-9, "construction": "radial",
            "recommended_psi": 36.0, "drag_pressure_psi": 28.0,
            "price_inr": 8500, "available_india": 1, "confidence": 0.55,
        },
        {
            "manufacturer": "MRF", "model_name": "Revz FB",
            "size": "120/70ZR17", "compound": "sport", "position": "front",
            "mu_peak": 1.25, "mu_slide": 0.93,
            "pacejka_B": 8.5, "pacejka_C": 1.60, "pacejka_D": 1.25, "pacejka_E": -0.63,
            "optimal_temp_c": 50.0, "reversion_temp_c": 88.0,
            "rolling_radius_m": 0.305, "mass_kg": 4.5, "inertia_kgm2": 0.38,
            "crr_base": 0.013,
            "recommended_psi": 36.0,
            "price_inr": 7200, "available_india": 1, "confidence": 0.52,
        },
        {
            "manufacturer": "MRF", "model_name": "Revz EF1 Drag",
            "size": "190/50ZR17", "compound": "drag_dot", "position": "rear",
            # Indian drag-spec tire developed for ISDC events
            "mu_peak": 1.42, "mu_slide": 1.08,
            "pacejka_B": 12.0, "pacejka_C": 1.65, "pacejka_D": 1.42, "pacejka_E": -0.22,
            "optimal_temp_c": 75.0, "reversion_temp_c": 115.0,
            "thermal_conductivity": 0.20, "tread_mass_kg": 2.5, "specific_heat": 1680,
            "rolling_radius_m": 0.302, "mass_kg": 5.8, "inertia_kgm2": 0.52,
            "crr_base": 0.009, "crr_speed_coeff": 2.2e-5, "crr_temp_coeff": -0.0003,
            "growth_coeff": 2.3e-9, "construction": "radial",
            "recommended_psi": 26.0, "drag_pressure_psi": 18.0,
            "price_inr": 14500, "available_india": 1, "confidence": 0.72,
        },

        # ── CEAT ──────────────────────────────────────────────────────────
        {
            "manufacturer": "CEAT", "model_name": "Zoom Sport",
            "size": "190/55ZR17", "compound": "sport", "position": "rear",
            "mu_peak": 1.22, "mu_slide": 0.92,
            "pacejka_B": 9.0, "pacejka_C": 1.60, "pacejka_D": 1.22, "pacejka_E": -0.62,
            "optimal_temp_c": 50.0, "reversion_temp_c": 88.0,
            "rolling_radius_m": 0.310, "mass_kg": 6.8, "inertia_kgm2": 0.60,
            "crr_base": 0.015, "crr_speed_coeff": 3.5e-5,
            "growth_coeff": 1.7e-9, "construction": "radial",
            "recommended_psi": 38.0, "drag_pressure_psi": 30.0,
            "price_inr": 7800, "available_india": 1, "confidence": 0.50,
        },

        # ── MAXXIS ────────────────────────────────────────────────────────
        {
            "manufacturer": "Maxxis", "model_name": "Supermaxx Sport",
            "size": "190/55ZR17", "compound": "sport", "position": "rear",
            "mu_peak": 1.28, "mu_slide": 0.96,
            "pacejka_B": 9.2, "pacejka_C": 1.62, "pacejka_D": 1.28, "pacejka_E": -0.58,
            "optimal_temp_c": 52.0, "reversion_temp_c": 90.0,
            "rolling_radius_m": 0.310, "mass_kg": 6.6, "inertia_kgm2": 0.59,
            "crr_base": 0.014, "crr_speed_coeff": 3.3e-5,
            "growth_coeff": 1.8e-9, "construction": "radial",
            "recommended_psi": 38.0, "drag_pressure_psi": 30.0,
            "price_inr": 9500, "available_india": 1, "confidence": 0.52,
        },

        # ── PIRELLI 200 profile (Hayabusa / S1000RR) ──────────────────────
        {
            "manufacturer": "Pirelli", "model_name": "Diablo Supercorsa SP V4",
            "size": "200/55ZR17", "compound": "sport", "position": "rear",
            "mu_peak": 1.40, "mu_slide": 1.06,
            "pacejka_B": 10.2, "pacejka_C": 1.65, "pacejka_D": 1.40, "pacejka_E": -0.46,
            "optimal_temp_c": 62.0, "reversion_temp_c": 102.0,
            "thermal_conductivity": 0.20, "tread_mass_kg": 2.7, "specific_heat": 1690,
            "rolling_radius_m": 0.315, "mass_kg": 6.2, "inertia_kgm2": 0.56,
            "crr_base": 0.011, "crr_speed_coeff": 2.7e-5,
            "growth_coeff": 2.0e-9, "construction": "radial",
            "recommended_psi": 33.0, "drag_pressure_psi": 25.0,
            "price_inr": 22000, "available_india": 1, "confidence": 0.63,
        },
        {
            "manufacturer": "Michelin", "model_name": "Power GP2",
            "size": "200/55ZR17", "compound": "race", "position": "rear",
            "mu_peak": 1.47, "mu_slide": 1.11,
            "pacejka_B": 11.2, "pacejka_C": 1.65, "pacejka_D": 1.47, "pacejka_E": -0.36,
            "optimal_temp_c": 70.0, "reversion_temp_c": 110.0,
            "rolling_radius_m": 0.315, "mass_kg": 6.0, "inertia_kgm2": 0.55,
            "crr_base": 0.010, "crr_speed_coeff": 2.4e-5,
            "growth_coeff": 2.1e-9, "construction": "radial",
            "recommended_psi": 30.0, "drag_pressure_psi": 22.0,
            "price_inr": 23500, "available_india": 1, "confidence": 0.66,
        },

        # ── DRAG SLICK (trued slick — not DOT-legal) ──────────────────────
        {
            "manufacturer": "Mickey Thompson", "model_name": "ET Street SS 29.0x10.5R18",
            "size": "295/35R18", "compound": "drag_slick", "position": "rear",
            # Used on open drag events / dyno pulls only
            "mu_peak": 1.72, "mu_slide": 1.35,
            "pacejka_B": 14.0, "pacejka_C": 1.65, "pacejka_D": 1.72, "pacejka_E": -0.10,
            "optimal_temp_c": 95.0, "reversion_temp_c": 145.0,
            "thermal_conductivity": 0.24, "tread_mass_kg": 3.5, "specific_heat": 1600,
            "rolling_radius_m": 0.335, "mass_kg": 7.2, "inertia_kgm2": 0.72,
            "crr_base": 0.007, "crr_speed_coeff": 1.8e-5, "crr_temp_coeff": -0.0004,
            "growth_coeff": 3.5e-9, "construction": "bias_ply",
            "recommended_psi": 20.0, "drag_pressure_psi": 12.0,
            "price_inr": 95000, "available_india": 0, "confidence": 0.80,
        },
        {
            "manufacturer": "Shinko", "model_name": "Stealth R265 Drag",
            "size": "180/55ZR17", "compound": "drag_dot", "position": "rear",
            "mu_peak": 1.55, "mu_slide": 1.20,
            "pacejka_B": 12.5, "pacejka_C": 1.65, "pacejka_D": 1.55, "pacejka_E": -0.16,
            "optimal_temp_c": 80.0, "reversion_temp_c": 120.0,
            "thermal_conductivity": 0.21, "tread_mass_kg": 2.4, "specific_heat": 1670,
            "rolling_radius_m": 0.307, "mass_kg": 5.4, "inertia_kgm2": 0.49,
            "crr_base": 0.009, "crr_speed_coeff": 2.0e-5, "crr_temp_coeff": -0.0003,
            "growth_coeff": 2.5e-9, "construction": "radial",
            "recommended_psi": 26.0, "drag_pressure_psi": 17.0,
            "price_inr": 45000, "available_india": 0, "confidence": 0.73,
        },
    ]

    count = 0
    for t in tires:
        kwargs = {k: v for k, v in t.items()
                  if k not in ("manufacturer", "model_name", "size", "compound", "position")}
        db.tires.create(
            manufacturer_name=t["manufacturer"],
            model_name=t["model_name"],
            size_designation=t["size"],
            compound_type=t["compound"],
            position=t["position"],
            **kwargs,
        )
        count += 1
    return count


def seed_parts_catalog(db: MotoQuantDB) -> int:
    """
    Expanded parts catalog covering the full drag-prep workflow:
    - Front sprockets: 14T–17T (520 & 530 pitch)
    - Rear sprockets: 40T–48T (520 & 530 pitch)
    - Chains: 520/530 gold X-ring and O-ring in standard/+5 link counts
    - ECU flashes: per-bike (Woolich, Bazzaz, Dynojet)
    - Exhaust: full systems & slip-ons (Akrapovic, Yoshimura, Arrow, Two Brothers, Leo Vince)
    - Launch control / quickshifter combos
    - Weight reduction (lithium battery, carbon fairing, undertray)
    - Nitrous (GSXR 1000 specific)
    """
    parts = []

    # ── FRONT SPROCKETS (520 pitch) ──────────────────────────────────────
    for teeth, price in [(14, 2600), (15, 2800), (16, 2800), (17, 2600)]:
        parts.append({
            "category": "sprocket",
            "brand": "Driven Racing",
            "model_name": f"520 Front Sprocket {teeth}T",
            "part_number": f"DR-520-{teeth}F",
            "specs": {"teeth": teeth, "pitch": "520", "position": "front",
                      "spline_count": 18},
            "param_overrides": {"drivetrain.front_sprocket": teeth},
            "price_inr": price, "availability": "in_stock",
            "retailer": "MotoParts India", "universal": True,
        })

    # ── FRONT SPROCKETS (530 pitch — Hayabusa) ────────────────────────────
    for teeth, price in [(16, 2800), (17, 2800), (18, 2900)]:
        parts.append({
            "category": "sprocket",
            "brand": "JT Sprockets",
            "model_name": f"530 Front Sprocket {teeth}T",
            "part_number": f"JT-530-{teeth}F",
            "specs": {"teeth": teeth, "pitch": "530", "position": "front",
                      "spline_count": 25},
            "param_overrides": {"drivetrain.front_sprocket": teeth},
            "price_inr": price, "availability": "in_stock",
            "retailer": "Grand Pitstop", "universal": False,
            "fitment_notes": "530-pitch bikes (Hayabusa Gen1/2, Bandit 1200)",
        })

    # ── REAR SPROCKETS (520 pitch) ────────────────────────────────────────
    rear_520 = [
        (40, "Aluminium 7075", 4200), (41, "Aluminium 7075", 4200),
        (42, "Aluminium 7075", 4500), (43, "Aluminium 7075", 4500),
        (44, "Aluminium 7075", 4500), (45, "Aluminium 7075", 4500),
        (46, "Steel", 3800), (47, "Steel", 3800), (48, "Steel", 3800),
    ]
    for teeth, material, price in rear_520:
        parts.append({
            "category": "sprocket",
            "brand": "Driven Racing",
            "model_name": f"520 Rear Sprocket {teeth}T ({material})",
            "part_number": f"DR-520-{teeth}R",
            "specs": {"teeth": teeth, "pitch": "520", "position": "rear",
                      "material": material},
            "param_overrides": {"drivetrain.rear_sprocket": teeth},
            "price_inr": price, "availability": "in_stock",
            "retailer": "MotoParts India", "universal": False,
            "fitment_notes": "520-pitch bikes (GSX-R 1000, YZF-R1, CBR 1000RR)",
        })

    # ── REAR SPROCKETS (530 pitch — Hayabusa) ─────────────────────────────
    for teeth, price in [(40, 5000), (42, 5000), (44, 5200), (45, 5200), (46, 5200)]:
        parts.append({
            "category": "sprocket",
            "brand": "JT Sprockets",
            "model_name": f"530 Rear Sprocket {teeth}T",
            "part_number": f"JT-530-{teeth}R",
            "specs": {"teeth": teeth, "pitch": "530", "position": "rear"},
            "param_overrides": {"drivetrain.rear_sprocket": teeth},
            "price_inr": price, "availability": "in_stock",
            "retailer": "Grand Pitstop", "universal": False,
            "fitment_notes": "530-pitch bikes (Hayabusa Gen1/2)",
        })

    # ── CHAINS ────────────────────────────────────────────────────────────
    chains = [
        {
            "brand": "RK", "model": "GB520GXW Gold X-Ring 110L",
            "pn": "RK-520GXW-110", "pitch": "520", "links": 110,
            "type": "x-ring", "eff": 1.02, "price": 8500,
        },
        {
            "brand": "RK", "model": "GB520GXW Gold X-Ring 120L",
            "pn": "RK-520GXW-120", "pitch": "520", "links": 120,
            "type": "x-ring", "eff": 1.02, "price": 9000,
        },
        {
            "brand": "RK", "model": "GB530GXW Gold X-Ring 110L",
            "pn": "RK-530GXW-110", "pitch": "530", "links": 110,
            "type": "x-ring", "eff": 1.02, "price": 10500,
        },
        {
            "brand": "DID", "model": "VX3 Gold 520-120L O-Ring",
            "pn": "DID-520VX3-120", "pitch": "520", "links": 120,
            "type": "o-ring", "eff": 1.015, "price": 9800,
        },
        {
            "brand": "DID", "model": "VX3 Gold 530-110L O-Ring",
            "pn": "DID-530VX3-110", "pitch": "530", "links": 110,
            "type": "o-ring", "eff": 1.015, "price": 11000,
        },
        {
            "brand": "EK", "model": "MVXZ2 520-120L Heavy Duty",
            "pn": "EK-520MVXZ2-120", "pitch": "520", "links": 120,
            "type": "x-ring", "eff": 1.02, "price": 9200,
        },
    ]
    for c in chains:
        parts.append({
            "category": "chain",
            "brand": c["brand"],
            "model_name": c["model"],
            "part_number": c["pn"],
            "specs": {"pitch": c["pitch"], "links": c["links"], "type": c["type"]},
            "param_overrides": {"drivetrain.chain_links": c["links"]},
            "param_multipliers": {"drivetrain.chain_efficiency": c["eff"]},
            "price_inr": c["price"], "availability": "in_stock",
            "retailer": "Grand Pitstop", "universal": False,
            "fitment_notes": f"{c['pitch']}-pitch motorcycles",
        })

    # ── ECU FLASHES (Woolich Racing) ─────────────────────────────────────
    ecu_woolich = [
        {
            "model": "GSX-R 1000 K5/K6 Stage 1 Flash",
            "pn": "WR-GSXR-K5-S1",
            "bike": "Suzuki GSX-R 1000 K5/K6",
            "stage": 1,
            "hp_delta": 8.0, "tq_delta": 5.0, "redline": 13500,
            "price": 18000,
        },
        {
            "model": "GSX-R 1000 K5/K6 Stage 2 Flash",
            "pn": "WR-GSXR-K5-S2",
            "bike": "Suzuki GSX-R 1000 K5/K6",
            "stage": 2,
            "hp_delta": 14.0, "tq_delta": 9.0, "redline": 14000,
            "price": 25000,
        },
        {
            "model": "YZF-R1 4C8 Stage 1 Flash",
            "pn": "WR-YZFR1-4C8-S1",
            "bike": "Yamaha YZF-R1 4C8",
            "stage": 1,
            "hp_delta": 7.0, "tq_delta": 4.5, "redline": 13800,
            "price": 18000,
        },
        {
            "model": "Hayabusa Gen1 Stage 1 Flash",
            "pn": "WR-BUSA-G1-S1",
            "bike": "Suzuki Hayabusa Gen1",
            "stage": 1,
            "hp_delta": 10.0, "tq_delta": 7.0, "redline": 11200,
            "price": 20000,
        },
    ]
    for e in ecu_woolich:
        parts.append({
            "category": "ecu",
            "brand": "Woolich Racing",
            "model_name": e["model"],
            "part_number": e["pn"],
            "specs": {
                "type": "flash", "stage": e["stage"],
                "bike": e["bike"],
                "features": ["custom_fuel_map", "ignition_map",
                             "rev_limiter_raise", "two_step_launch"],
            },
            "param_deltas": {
                "engine.peak_power_hp": e["hp_delta"],
                "engine.peak_torque_nm": e["tq_delta"],
            },
            "param_overrides": {
                "engine.redline_rpm": e["redline"],
                "staging.two_step": True,
                "staging.launch_rpm": 8500,
            },
            "price_inr": e["price"], "availability": "in_stock",
            "retailer": "Woolich Racing India",
        })

    # Bazzaz ZFi + ZFiTC (traction control + fuel)
    parts.append({
        "category": "ecu",
        "brand": "Bazzaz",
        "model_name": "ZFiTC Fuel + TC Module Universal",
        "part_number": "BZ-ZFITC-U",
        "specs": {
            "type": "piggyback", "features": [
                "16x16_fuel_map", "traction_control", "quickshift_compatible",
            ],
        },
        "param_deltas": {"engine.peak_power_hp": 4.0},
        "param_overrides": {
            "staging.traction_control_level": 3,
            "staging.two_step": True,
        },
        "price_inr": 32000, "availability": "order",
        "retailer": "Bazzaz India", "delivery_days": 21, "universal": True,
    })

    # Dynojet Power Vision 3 (flasher + dyno integration)
    parts.append({
        "category": "ecu",
        "brand": "Dynojet",
        "model_name": "Power Vision 3 Flashing Unit",
        "part_number": "DJ-PV3",
        "specs": {
            "type": "flash_device",
            "features": ["auto-tune", "power_commander_maps", "data_logging"],
        },
        "param_deltas": {"engine.peak_power_hp": 6.0, "engine.peak_torque_nm": 4.0},
        "param_overrides": {
            "staging.two_step": True,
            "staging.launch_rpm": 9000,
        },
        "price_inr": 45000, "availability": "order",
        "retailer": "Dynojet India", "delivery_days": 14, "universal": False,
    })

    # ── EXHAUST SYSTEMS ───────────────────────────────────────────────────
    exhausts = [
        # Full systems
        {
            "brand": "Akrapovic", "model": "Racing Full System GP Ti",
            "pn": "AK-S-S10R-GP", "type": "full_system", "material": "titanium",
            "weight_kg": 4.2, "hp_delta": 6.0, "tq_delta": 4.0, "mass_mult": 0.96,
            "price": 185000, "avail": "order", "days": 30,
        },
        {
            "brand": "Yoshimura", "model": "R-77 Full System SS/SS/CF",
            "pn": "YO-1120100", "type": "full_system", "material": "stainless",
            "weight_kg": 5.8, "hp_delta": 4.5, "tq_delta": 3.0, "mass_mult": 0.975,
            "price": 75000, "avail": "order", "days": 21,
        },
        {
            "brand": "Yoshimura", "model": "Alpha Racing Full System Ti",
            "pn": "YO-ALPHA-TI", "type": "full_system", "material": "titanium",
            "weight_kg": 3.8, "hp_delta": 7.5, "tq_delta": 5.5, "mass_mult": 0.97,
            "price": 210000, "avail": "import_only", "days": 45,
        },
        {
            "brand": "Arrow", "model": "Full Exhaust Pro-Race Ti",
            "pn": "AR-71470PRN", "type": "full_system", "material": "titanium",
            "weight_kg": 4.5, "hp_delta": 5.5, "tq_delta": 3.8, "mass_mult": 0.965,
            "price": 165000, "avail": "order", "days": 30,
        },
        # Slip-ons (bolt-on, less weight reduction)
        {
            "brand": "Akrapovic", "model": "Slip-On Exhaust Carbon Ti",
            "pn": "AK-S-S10SO1-HZC", "type": "slip_on", "material": "titanium",
            "weight_kg": 1.8, "hp_delta": 2.5, "tq_delta": 1.5, "mass_mult": 0.987,
            "price": 55000, "avail": "in_stock", "days": None,
        },
        {
            "brand": "Two Brothers Racing", "model": "M2 Black Slip-On",
            "pn": "TBR-005-3670406V", "type": "slip_on", "material": "aluminum",
            "weight_kg": 2.4, "hp_delta": 2.0, "tq_delta": 1.2, "mass_mult": 0.991,
            "price": 28000, "avail": "in_stock", "days": None,
        },
        {
            "brand": "Leo Vince", "model": "LV-10 Full Titanium Slip-On",
            "pn": "LV-15227T", "type": "slip_on", "material": "titanium",
            "weight_kg": 1.6, "hp_delta": 2.8, "tq_delta": 1.6, "mass_mult": 0.985,
            "price": 38000, "avail": "order", "days": 14,
        },
    ]
    for ex in exhausts:
        parts.append({
            "category": "exhaust",
            "brand": ex["brand"],
            "model_name": ex["model"],
            "part_number": ex["pn"],
            "specs": {
                "type": ex["type"], "material": ex["material"],
                "weight_kg": ex["weight_kg"],
            },
            "param_deltas": {
                "engine.peak_power_hp": ex["hp_delta"],
                "engine.peak_torque_nm": ex["tq_delta"],
            },
            "param_multipliers": {"chassis.dry_mass_kg": ex["mass_mult"]},
            "price_inr": ex["price"],
            "availability": ex["avail"],
            "retailer": "Superbike India",
            "delivery_days": ex.get("days"),
        })

    # ── CLUTCH KITS ───────────────────────────────────────────────────────
    parts += [
        {
            "category": "clutch_kit",
            "brand": "Barnett", "model_name": "Extra Plate Kevlar Kit",
            "part_number": "BN-306-25-40002",
            "specs": {"material": "kevlar", "plates": 9, "extra_plates": 1},
            "param_overrides": {
                "clutch.plate_count": 9,
                "clutch.friction_material": "kevlar",
                "clutch.mu_static": 0.45,
            },
            "price_inr": 12000, "availability": "in_stock",
            "retailer": "MotoParts India",
        },
        {
            "category": "clutch_kit",
            "brand": "Hinson", "model_name": "Clutch Cover + Inner Hub Kit",
            "part_number": "HN-BC051-8A",
            "specs": {"material": "billet_aluminum", "type": "cover_inner_hub"},
            "param_overrides": {
                "clutch.slip_rpm_threshold": 200.0,
                "clutch.engagement_rate": 1.2,
            },
            "price_inr": 48000, "availability": "import_only",
            "retailer": "Hinson (US)", "delivery_days": 45,
        },
        {
            "category": "clutch_kit",
            "brand": "EBC",
            "model_name": "Clutch Kit Pro-Lite Carbon",
            "part_number": "EBC-CK-PL-C",
            "specs": {"material": "carbon", "plates": 8},
            "param_overrides": {
                "clutch.friction_material": "carbon",
                "clutch.mu_static": 0.50,
            },
            "price_inr": 18000, "availability": "order",
            "retailer": "EBC India", "delivery_days": 21,
        },
    ]

    # ── QUICKSHIFTERS ─────────────────────────────────────────────────────
    parts += [
        {
            "category": "quickshifter",
            "brand": "HM Quickshifter", "model_name": "Super Lite Universal",
            "part_number": "HM-QS-SLU",
            "specs": {"type": "push", "sensor": "strain_gauge"},
            "param_overrides": {
                "drivetrain.quickshifter": True,
                "drivetrain.total_shift_time_ms": 60.0,
                "drivetrain.shift_cut_duration_ms": 40.0,
            },
            "price_inr": 22000, "availability": "order",
            "retailer": "HM India", "delivery_days": 14, "universal": True,
        },
        {
            "category": "quickshifter",
            "brand": "Translogic", "model_name": "QS Pro III Bidirectional",
            "part_number": "TL-QS3-BD",
            "specs": {"type": "bidirectional", "sensor": "hall_effect",
                      "auto-blipper": True},
            "param_overrides": {
                "drivetrain.quickshifter": True,
                "drivetrain.total_shift_time_ms": 50.0,
                "drivetrain.shift_cut_duration_ms": 30.0,
                "drivetrain.auto_blipper": True,
            },
            "price_inr": 38000, "availability": "order",
            "retailer": "Translogic India", "delivery_days": 21, "universal": True,
        },
    ]

    # ── SWINGARM EXTENSIONS ───────────────────────────────────────────────
    parts += [
        {
            "category": "swingarm_ext",
            "brand": "Voodoo Industries", "model_name": '4" Swingarm Extension Kit',
            "part_number": "VI-SAE-4",
            "specs": {"extension_mm": 101.6, "material": "billet_aluminum"},
            "param_overrides": {"chassis.swingarm_extension_mm": 101.6},
            "price_inr": 28000, "availability": "import_only",
            "retailer": "Voodoo Ind. (US)", "delivery_days": 45,
        },
        {
            "category": "swingarm_ext",
            "brand": "Voodoo Industries", "model_name": '6" Swingarm Extension Kit',
            "part_number": "VI-SAE-6",
            "specs": {"extension_mm": 152.4, "material": "billet_aluminum"},
            "param_overrides": {"chassis.swingarm_extension_mm": 152.4},
            "price_inr": 35000, "availability": "import_only",
            "retailer": "Voodoo Ind. (US)", "delivery_days": 45,
        },
        {
            "category": "swingarm_ext",
            "brand": "Indian Custom Fab", "model_name": '4" Bespoke Swingarm Ext',
            "part_number": "ICF-SAE-4",
            "specs": {"extension_mm": 101.6, "material": "4130_chromoly"},
            "param_overrides": {"chassis.swingarm_extension_mm": 101.6},
            "price_inr": 18000, "availability": "order",
            "retailer": "Custom Fab (Mumbai)", "delivery_days": 30,
        },
    ]

    # ── WEIGHT REDUCTION ─────────────────────────────────────────────────
    parts += [
        {
            "category": "battery",
            "brand": "Shorai", "model_name": "LFX14A2-BS12 Lithium Battery",
            "part_number": "SH-LFX14A2",
            "specs": {"capacity_ah": 14, "technology": "lithium",
                      "weight_kg": 0.9, "replaces_weight_kg": 3.8},
            # Net mass reduction ~2.9 kg
            "param_deltas": {"chassis.dry_mass_kg": -2.9},
            "price_inr": 12000, "availability": "in_stock",
            "retailer": "MotoParts India", "universal": True,
        },
        {
            "category": "battery",
            "brand": "Antigravity", "model_name": "ATX30-HD-RS Restart Lithium",
            "part_number": "AG-ATX30-HD",
            "specs": {"capacity_ah": 30, "technology": "lithium",
                      "restart_capable": True, "weight_kg": 1.6},
            "param_deltas": {"chassis.dry_mass_kg": -2.2},
            "price_inr": 18000, "availability": "order",
            "retailer": "Antigravity India", "delivery_days": 14, "universal": True,
        },
        {
            "category": "bodywork",
            "brand": "Attack Performance", "model_name": "Full Carbon Bodywork Kit",
            "part_number": "AP-CBFK-GSXR",
            "specs": {"material": "carbon_fiber", "pieces": 7, "weight_kg": 4.2,
                      "replaces_weight_kg": 9.5},
            "param_deltas": {"chassis.dry_mass_kg": -5.3},
            "price_inr": 120000, "availability": "import_only",
            "retailer": "Attack Performance (US)", "delivery_days": 60,
        },
        {
            "category": "bodywork",
            "brand": "Hotbodies Racing", "model_name": "GP Undertray + Frame Sliders",
            "part_number": "HB-GPUL-GSXR",
            "specs": {"material": "fiberglass", "weight_kg": 1.8,
                      "replaces_weight_kg": 3.2},
            "param_deltas": {"chassis.dry_mass_kg": -1.4},
            "price_inr": 8500, "availability": "in_stock",
            "retailer": "MotoParts India",
        },
    ]

    # ── NITROUS ───────────────────────────────────────────────────────────
    parts += [
        {
            "category": "nitrous",
            "brand": "Nitrous Express", "model_name": "NX Motorcycle Wet Kit 20 HP",
            "part_number": "NX-MK-20WET",
            "specs": {"type": "wet_kit", "hp_shot": 20, "bottle_oz": 10,
                      "note": "Single solenoid; requires fuel enrichment"},
            # Activates as a power multiplier above launch threshold
            "param_deltas": {"engine.peak_power_hp": 20.0},
            "param_overrides": {"staging.nitrous_active": True},
            "price_inr": 45000, "availability": "import_only",
            "retailer": "NX India", "delivery_days": 45,
        },
        {
            "category": "nitrous",
            "brand": "Nitrous Express", "model_name": "NX Motorcycle Dry Kit 40 HP",
            "part_number": "NX-MK-40DRY",
            "specs": {"type": "dry_kit", "hp_shot": 40, "bottle_oz": 10,
                      "note": "Requires upgraded injectors for safe fuel delivery"},
            "param_deltas": {"engine.peak_power_hp": 40.0},
            "param_overrides": {"staging.nitrous_active": True},
            "price_inr": 65000, "availability": "import_only",
            "retailer": "NX India", "delivery_days": 45,
        },
    ]

    count = 0
    for p in parts:
        db.parts.create(
            category_name=p["category"],
            brand=p["brand"],
            model_name=p["model_name"],
            specifications=p["specs"],
            part_number=p.get("part_number"),
            fitment_universal=p.get("universal", False),
            fitment_notes=p.get("fitment_notes"),
            param_overrides=p.get("param_overrides"),
            param_deltas=p.get("param_deltas"),
            param_multipliers=p.get("param_multipliers"),
            price_inr=p.get("price_inr"),
            retailer=p.get("retailer"),
            availability=p.get("availability", "in_stock"),
            estimated_delivery_days=p.get("delivery_days"),
        )
        count += 1
    return count


def seed_all(db: MotoQuantDB) -> dict:
    """
    Run full seed: bikes, tires (sample + expanded library), parts (sample + catalog).
    Venues and seasonal data are seeded by db.initialize().

    Returns counts of seeded entities.
    """
    counts = {
        "bikes": seed_reference_bikes(db),
        "tires": seed_sample_tires(db) + seed_tire_library(db),
        "parts": seed_sample_parts(db) + seed_parts_catalog(db),
    }
    return counts
