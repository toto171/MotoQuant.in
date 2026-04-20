"""
MotoQuant Pro — Database Schema
==============================
SQLite schema with 15 tables covering bikes, tires, venues, weather, and parts.

Design principles for quantitative accuracy:
  1. Every parameter carries a confidence score (0.0–1.0) and provenance source.
  2. Dyno curves and gear ratios stored as normalized point tables for analysis.
  3. Venue weather supports both historical seasonal stats and live API snapshots.
  4. Parts track param_deltas: exact simulation-parameter changes per modification.
  5. Schema version tracked for forward-compatible migrations.
"""

SCHEMA_VERSION = 3

# ────────────────────────────────────────────────────────
# Full DDL executed on db.initialize()
# ────────────────────────────────────────────────────────

TABLES_DDL = """
-- ═══════════════════════════════════════════════════════════
-- META
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS schema_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- ═══════════════════════════════════════════════════════════
-- 1. MANUFACTURERS
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS manufacturers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    country     TEXT,
    aliases     TEXT,                           -- JSON array of alt names
    created_at  TEXT    DEFAULT (datetime('now','utc'))
);

-- ═══════════════════════════════════════════════════════════
-- 2. BIKE MODELS  (identity + headline specs for search)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS bike_models (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    manufacturer_id     INTEGER NOT NULL REFERENCES manufacturers(id),
    model_name          TEXT    NOT NULL,       -- "GSX-R 1000"
    model_code          TEXT,                   -- "K5", "4C8", "Gen1"
    year_from           INTEGER,
    year_to             INTEGER,
    category            TEXT,                   -- sport / naked / cruiser / adv / drag / touring
    subcategory         TEXT,                   -- supersport, hypersport, streetfighter

    -- Headline specs (searchable, quick-compare)
    displacement_cc     REAL,
    cylinder_count      INTEGER,
    cylinder_config     TEXT,                   -- I4, V2, I2, V4, L2, single
    bore_mm             REAL,
    stroke_mm           REAL,
    compression_ratio   REAL,
    peak_power_hp       REAL,                   -- At wheel unless noted
    peak_power_rpm      REAL,
    peak_torque_nm      REAL,
    peak_torque_rpm     REAL,
    dry_mass_kg         REAL,
    wet_mass_kg         REAL,
    wheelbase_mm        REAL,
    seat_height_mm      REAL,
    fuel_capacity_l     REAL,

    -- Data quality (quant provenance)
    data_completeness   REAL    DEFAULT 0.0,    -- 0–1 fraction of sim params filled
    data_quality        TEXT    DEFAULT 'scraped',
        -- scraped / spec_sheet / verified / dyno_validated / track_validated
    validation_et_s     REAL,                   -- known QM ET for cross-check
    validation_trap_kmh REAL,
    validation_source   TEXT,

    created_at          TEXT    DEFAULT (datetime('now','utc')),
    updated_at          TEXT    DEFAULT (datetime('now','utc')),

    UNIQUE(manufacturer_id, model_name, model_code, year_from)
);

CREATE INDEX IF NOT EXISTS idx_bike_models_mfr     ON bike_models(manufacturer_id);
CREATE INDEX IF NOT EXISTS idx_bike_models_disp    ON bike_models(displacement_cc);
CREATE INDEX IF NOT EXISTS idx_bike_models_cat     ON bike_models(category);
CREATE INDEX IF NOT EXISTS idx_bike_models_quality ON bike_models(data_quality);

-- ═══════════════════════════════════════════════════════════
-- 3. BIKE CONFIGS  (versioned full-parameter sets → BikeConfig)
--    Each row is a complete simulation-ready parameter snapshot.
--    JSON blobs map 1:1 to the existing dataclass hierarchy.
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS bike_configs (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    bike_model_id           INTEGER NOT NULL REFERENCES bike_models(id),
    version                 INTEGER NOT NULL DEFAULT 1,
    is_current              INTEGER NOT NULL DEFAULT 1,
    config_name             TEXT    NOT NULL DEFAULT 'stock',
        -- 'stock', 'stage1', 'stage2', 'pro_street', 'outlaw', 'custom'

    -- 14 parameter blocks as JSON  (mirrors BikeConfig dataclass tree)
    chassis_params          TEXT    NOT NULL,   -- JSON → ChassisParams
    engine_params           TEXT    NOT NULL,   -- JSON → EngineParams (excl dyno_curve)
    forced_induction_params TEXT    NOT NULL,
    drivetrain_params       TEXT    NOT NULL,
    clutch_params           TEXT    NOT NULL,
    tire_params             TEXT    NOT NULL,
    aero_params             TEXT    NOT NULL,
    suspension_params       TEXT    NOT NULL,
    braking_params          TEXT    NOT NULL,
    wheelie_params          TEXT    NOT NULL,
    rider_params            TEXT    NOT NULL,
    parasitic_params        TEXT    NOT NULL,
    staging_params          TEXT    NOT NULL,

    -- Provenance  (critical for quant accuracy)
    source                  TEXT    DEFAULT 'spec_sheet',
        -- spec_sheet / dyno_test / user_submitted / estimated / hybrid
    source_url              TEXT,
    confidence              REAL    DEFAULT 0.5,   -- 0–1 overall confidence
    notes                   TEXT,

    created_at              TEXT    DEFAULT (datetime('now','utc')),
    updated_at              TEXT    DEFAULT (datetime('now','utc')),

    UNIQUE(bike_model_id, version, config_name)
);

CREATE INDEX IF NOT EXISTS idx_bike_configs_model ON bike_configs(bike_model_id, is_current);

-- ═══════════════════════════════════════════════════════════
-- 4. DYNO CURVES  (normalized point table for cross-bike analysis)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS dyno_curves (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    bike_config_id      INTEGER NOT NULL REFERENCES bike_configs(id),
    curve_type          TEXT    NOT NULL DEFAULT 'torque',  -- torque / power
    is_at_wheel         INTEGER NOT NULL DEFAULT 1,
    rpm_points          TEXT    NOT NULL,       -- JSON array of floats
    torque_values       TEXT    NOT NULL,       -- JSON array (Nm or HP)
    num_points          INTEGER NOT NULL,

    -- Dyno provenance
    dyno_brand          TEXT,                   -- "Dynojet", "Bren", "Dynocom"
    correction_standard TEXT    DEFAULT 'SAE',  -- SAE / DIN / JIS / uncorrected
    ambient_temp_c      REAL,
    altitude_m          REAL,
    humidity_pct        REAL,

    source              TEXT,
    source_url          TEXT,
    confidence          REAL    DEFAULT 0.5,
    notes               TEXT,

    created_at          TEXT    DEFAULT (datetime('now','utc'))
);

CREATE INDEX IF NOT EXISTS idx_dyno_curves_config ON dyno_curves(bike_config_id);

-- ═══════════════════════════════════════════════════════════
-- 5. TIRE MANUFACTURERS
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS tire_manufacturers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    country     TEXT,
    created_at  TEXT    DEFAULT (datetime('now','utc'))
);

-- ═══════════════════════════════════════════════════════════
-- 6. TIRE MODELS  (the most critical sub-model for drag sim)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS tire_models (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    manufacturer_id     INTEGER NOT NULL REFERENCES tire_manufacturers(id),
    model_name          TEXT    NOT NULL,
    compound_type       TEXT    NOT NULL,
        -- street / sport / race / drag_dot / drag_slick / rain
    position            TEXT    NOT NULL DEFAULT 'rear',  -- front / rear / both

    -- Size
    width_mm            INTEGER,
    aspect_ratio        INTEGER,
    rim_diameter_inch   INTEGER,
    size_designation    TEXT    NOT NULL,       -- "190/55ZR17"

    -- Pacejka Magic Formula coefficients
    pacejka_B           REAL,                  -- stiffness
    pacejka_C           REAL,                  -- shape
    pacejka_D           REAL,                  -- peak (≈ mu_peak)
    pacejka_E           REAL,                  -- curvature

    -- Friction
    mu_peak             REAL,
    mu_slide            REAL,
    load_sensitivity_k  REAL,                  -- 1/N

    -- Thermal model
    optimal_temp_c      REAL,
    reversion_temp_c    REAL,
    thermal_conductivity REAL,
    tread_mass_kg       REAL,
    specific_heat       REAL,                  -- J/(kg·K)

    -- Physical
    rolling_radius_m    REAL,
    inertia_kgm2        REAL,
    growth_coeff        REAL,                  -- centrifugal expansion
    mass_kg             REAL,

    -- Rolling resistance
    crr_base            REAL,
    crr_speed_coeff     REAL,
    crr_temp_coeff      REAL,

    -- Pressure
    recommended_psi     REAL,
    drag_pressure_psi   REAL,                  -- recommended for drag

    -- Construction
    construction        TEXT    DEFAULT 'radial',  -- bias / radial / ntec

    -- Data quality
    data_source         TEXT,
    confidence          REAL    DEFAULT 0.5,

    -- Pricing (INR)
    price_inr           REAL,
    price_usd           REAL,
    available_india     INTEGER DEFAULT 0,

    created_at          TEXT    DEFAULT (datetime('now','utc')),
    updated_at          TEXT    DEFAULT (datetime('now','utc')),

    UNIQUE(manufacturer_id, model_name, size_designation)
);

CREATE INDEX IF NOT EXISTS idx_tire_compound ON tire_models(compound_type);
CREATE INDEX IF NOT EXISTS idx_tire_size     ON tire_models(size_designation);

-- ═══════════════════════════════════════════════════════════
-- 7. VENUES  (drag strips, airstrips, road closures)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS venues (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT    NOT NULL UNIQUE,
    short_name          TEXT,
    city                TEXT,
    state               TEXT,
    country             TEXT    DEFAULT 'India',

    -- Geographic
    latitude            REAL,
    longitude           REAL,
    altitude_m          REAL    NOT NULL,

    -- Track specs
    surface_type        TEXT    DEFAULT 'asphalt',
    track_length_m      REAL,
    track_gradient_pct  REAL    DEFAULT 0.0,
    track_heading_deg   REAL    DEFAULT 0.0,   -- compass bearing for wind calc

    -- Facilities
    has_vht             INTEGER DEFAULT 0,
    has_timing_system   INTEGER DEFAULT 0,
    timing_system_type  TEXT,                   -- "Compulink", "Portatree", "manual"
    sanctioning_body    TEXT,

    is_active           INTEGER DEFAULT 1,
    notes               TEXT,

    created_at          TEXT    DEFAULT (datetime('now','utc')),
    updated_at          TEXT    DEFAULT (datetime('now','utc'))
);

-- ═══════════════════════════════════════════════════════════
-- 8. WEATHER RECORDS  (live API snapshots + manual entries)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS weather_records (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    venue_id                INTEGER REFERENCES venues(id),
    recorded_at             TEXT    NOT NULL,   -- ISO 8601
    source                  TEXT    NOT NULL,
        -- openweathermap / weatherapi / manual / historical_avg

    -- Atmospheric
    ambient_temp_c          REAL,
    relative_humidity_pct   REAL,
    barometric_pressure_hpa REAL,
    dew_point_c             REAL,

    -- Wind
    wind_speed_ms           REAL,
    wind_direction_deg      REAL,
    wind_gust_ms            REAL,

    -- Track
    track_temp_c            REAL,

    -- Derived (computed on insert for fast queries)
    density_altitude_ft     REAL,
    air_density_kgm3        REAL,
    vapor_pressure_hpa      REAL,
    power_correction_factor REAL,

    -- Raw API response for audit trail
    raw_response            TEXT,               -- full JSON

    created_at              TEXT    DEFAULT (datetime('now','utc'))
);

CREATE INDEX IF NOT EXISTS idx_weather_venue_time ON weather_records(venue_id, recorded_at);

-- ═══════════════════════════════════════════════════════════
-- 9. VENUE SEASONAL CONDITIONS  (monthly normals for offline / Monte Carlo)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS venue_seasonal (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    venue_id            INTEGER NOT NULL REFERENCES venues(id),
    month               INTEGER NOT NULL,      -- 1–12

    -- Means
    avg_temp_c          REAL,
    avg_humidity_pct    REAL,
    avg_pressure_hpa    REAL,
    avg_wind_speed_ms   REAL,
    prevailing_wind_deg REAL,
    avg_track_temp_c    REAL,
    avg_density_alt_ft  REAL,

    -- Standard deviations (for Monte Carlo uncertainty)
    temp_std_c          REAL    DEFAULT 3.0,
    humidity_std_pct    REAL    DEFAULT 10.0,
    pressure_std_hpa    REAL    DEFAULT 5.0,

    UNIQUE(venue_id, month)
);

-- ═══════════════════════════════════════════════════════════
-- 10. PARTS CATEGORIES  (drag-relevant modification types)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS parts_categories (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL UNIQUE,
        -- sprocket / chain / tire / exhaust / ecu / clutch_kit /
        -- boost_kit / air_filter / fuel_system / wheelie_bar /
        -- swingarm_ext / quickshifter
    display_name    TEXT,
    affects_params  TEXT                       -- JSON: which BikeConfig sections this touches
);

-- ═══════════════════════════════════════════════════════════
-- 11. PARTS  (performance parts with Indian market pricing)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS parts (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id         INTEGER NOT NULL REFERENCES parts_categories(id),
    brand               TEXT    NOT NULL,
    model_name          TEXT    NOT NULL,
    part_number         TEXT,

    -- Compatibility
    fitment_rules       TEXT,                   -- JSON: {tier, bike_ids, match, excluded_bike_ids, description} (new in v2)
    compatible_bikes    TEXT,                   -- JSON array of bike_model_ids (legacy, nullable)
    fitment_universal   INTEGER DEFAULT 0,     -- 1 = fits many bikes (legacy)
    fitment_notes       TEXT,

    -- Category-specific specs
    specifications      TEXT    NOT NULL,       -- JSON: teeth count, link count, etc.

    -- Simulation impact  (THE KEY QUANT FIELD)
    -- JSON dict mapping dotted paths to deltas:
    --   {"drivetrain.rear_sprocket": 45, "drivetrain.front_sprocket": 15}
    param_overrides     TEXT,                  -- absolute values to set
    param_deltas        TEXT,                  -- additive changes
    param_multipliers   TEXT,                  -- multiplicative factors

    -- Pricing
    price_inr           REAL,
    price_usd           REAL,
    mrp_inr             REAL,                  -- MRP for Indian market

    -- Sourcing
    retailer            TEXT,
    retailer_url        TEXT,
    availability        TEXT    DEFAULT 'in_stock',
        -- in_stock / order / import_only / discontinued
    estimated_delivery_days INTEGER,
    last_price_check    TEXT,                  -- ISO date

    created_at          TEXT    DEFAULT (datetime('now','utc')),
    updated_at          TEXT    DEFAULT (datetime('now','utc')),

    UNIQUE(brand, part_number)
);

CREATE INDEX IF NOT EXISTS idx_parts_category ON parts(category_id);
CREATE INDEX IF NOT EXISTS idx_parts_brand    ON parts(brand);

-- ═══════════════════════════════════════════════════════════
-- 12. SIMULATION RUNS  (result archive with full traceability)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS sim_runs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    bike_config_id      INTEGER REFERENCES bike_configs(id),
    venue_id            INTEGER REFERENCES venues(id),
    weather_record_id   INTEGER REFERENCES weather_records(id),

    -- Key results
    et_quarter_s        REAL,
    trap_speed_kmh      REAL,
    et_eighth_s         REAL,
    speed_eighth_kmh    REAL,
    time_60ft_s         REAL,
    speed_60ft_kmh      REAL,
    time_330ft_s        REAL,
    time_1000ft_s       REAL,

    -- Sim config
    sim_version         TEXT,
    dt_s                REAL    DEFAULT 0.001,
    distance_m          REAL    DEFAULT 402.336,

    -- Split times (full JSON)
    split_times_json    TEXT,

    -- Optional: path to exported CSV for full time-domain data
    time_series_path    TEXT,

    -- Modifications applied (list of part IDs)
    applied_parts       TEXT,                  -- JSON array of part IDs

    created_at          TEXT    DEFAULT (datetime('now','utc')),
    notes               TEXT
);

CREATE INDEX IF NOT EXISTS idx_sim_runs_config ON sim_runs(bike_config_id);
CREATE INDEX IF NOT EXISTS idx_sim_runs_venue  ON sim_runs(venue_id);

-- ═══════════════════════════════════════════════════════════
-- 13. DATA PROVENANCE  (field-level audit trail)
--     Tracks WHERE each data point came from and HOW confident we are.
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS data_provenance (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type     TEXT    NOT NULL,          -- bike_model / bike_config / tire / venue / part
    entity_id       INTEGER NOT NULL,
    field_path      TEXT    NOT NULL,          -- dotted path: "engine.bore_mm"

    source_type     TEXT    NOT NULL,
        -- manufacturer_spec / service_manual / dyno_test / scrape /
        -- estimation / user_submission / computed
    source_url      TEXT,
    source_date     TEXT,
    confidence      REAL    NOT NULL DEFAULT 0.5,  -- 0–1
    notes           TEXT,

    created_at      TEXT    DEFAULT (datetime('now','utc'))
);

CREATE INDEX IF NOT EXISTS idx_provenance_entity ON data_provenance(entity_type, entity_id);

-- ═══════════════════════════════════════════════════════════
-- 14. BIKE-TIRE FITMENTS (OEM + recommended aftermarket)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS bike_tire_fitments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    bike_model_id   INTEGER NOT NULL REFERENCES bike_models(id),
    tire_model_id   INTEGER NOT NULL REFERENCES tire_models(id),
    position        TEXT    NOT NULL CHECK(position IN ('front','rear')),
    fitment_type    TEXT    NOT NULL DEFAULT 'oem'
                                   CHECK(fitment_type IN ('oem','recommended','drag_prep')),
    is_default      INTEGER NOT NULL DEFAULT 0,  -- 1 = selected by default for sim
    notes           TEXT,
    created_at      TEXT    DEFAULT (datetime('now','utc')),
    UNIQUE(bike_model_id, tire_model_id, position, fitment_type)
);

CREATE INDEX IF NOT EXISTS idx_fitments_bike     ON bike_tire_fitments(bike_model_id);
CREATE INDEX IF NOT EXISTS idx_fitments_tire     ON bike_tire_fitments(tire_model_id);
CREATE INDEX IF NOT EXISTS idx_fitments_position ON bike_tire_fitments(position);

-- ═══════════════════════════════════════════════════════════
-- 15. BIKE SUGGESTIONS  (user-submitted additions via web form)
--     Users can request bikes missing from the catalog. Entries
--     are reviewed manually before being promoted to bike_models.
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS bike_suggestions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    make                TEXT    NOT NULL,
    model               TEXT    NOT NULL,
    year                INTEGER,
    displacement_cc     REAL,
    peak_power_hp       REAL,
    dry_mass_kg         REAL,
    category            TEXT,               -- sport / naked / cruiser / adv / drag / touring
    notes               TEXT,               -- free-form rider context
    submitter_email     TEXT,               -- optional
    source_url          TEXT,               -- user-supplied spec page, optional
    flagged_out_of_bounds INTEGER NOT NULL DEFAULT 0,
        -- 1 = failed plausibility checks; still stored but marked for review
    status              TEXT    NOT NULL DEFAULT 'pending'
                                   CHECK(status IN ('pending','reviewed','added','rejected')),
    created_at          TEXT    DEFAULT (datetime('now','utc')),
    reviewed_at         TEXT
);

CREATE INDEX IF NOT EXISTS idx_bike_sugg_status  ON bike_suggestions(status);
CREATE INDEX IF NOT EXISTS idx_bike_sugg_make    ON bike_suggestions(make);
"""

# Categories seeded on first init
SEED_PARTS_CATEGORIES = [
    # Note: "tire" is intentionally NOT a parts category — tires live in the
    # dedicated tire_models table and are selected via the sidebar Tires menu.
    ("sprocket", "Sprocket", '["drivetrain"]'),
    ("chain", "Chain / Belt", '["drivetrain"]'),
    ("exhaust", "Exhaust System", '["engine", "aero"]'),
    ("ecu", "ECU / Flash", '["engine", "staging"]'),
    ("clutch_kit", "Clutch Kit", '["clutch", "drivetrain"]'),
    ("boost_kit", "Turbo / SC / NOS", '["forced_induction", "engine"]'),
    ("nitrous", "Nitrous Kit", '["engine", "staging"]'),
    ("air_filter", "Air Filter", '["engine"]'),
    ("fuel_system", "Fuel System", '["engine", "forced_induction"]'),
    ("wheelie_bar", "Wheelie Bar", '["wheelie"]'),
    ("swingarm_ext", "Swingarm Ext", '["chassis", "suspension"]'),
    ("quickshifter", "Quickshifter", '["drivetrain"]'),
    ("battery", "Battery", '["chassis"]'),
    ("bodywork", "Bodywork", '["chassis", "aero"]'),
    ("suspension", "Suspension", '["suspension"]'),
    ("brakes", "Brakes", '["braking"]'),
]

# Indian venue seed data
SEED_VENUES = [
    {
        "name": "Aamby Valley Airstrip (TVR)",
        "short_name": "aamby",
        "city": "Aamby Valley City",
        "state": "Maharashtra",
        "country": "India",
        "latitude": 18.6856,
        "longitude": 73.3157,
        "altitude_m": 679.0,
        "surface_type": "asphalt",
        "track_length_m": 402.336,
        "track_heading_deg": 135.0,
        "has_vht": 0,
        "has_timing_system": 1,
        "timing_system_type": "Compulink",
        "sanctioning_body": "TVR",
    },
    {
        "name": "Madras Motor Race Track (MMRT)",
        "short_name": "mmrt",
        "city": "Sriperumbudur",
        "state": "Tamil Nadu",
        "country": "India",
        "latitude": 12.9269,
        "longitude": 79.9781,
        "altitude_m": 78.0,
        "surface_type": "asphalt",
        "track_length_m": 402.336,
        "track_heading_deg": 180.0,
        "has_vht": 0,
        "has_timing_system": 1,
        "sanctioning_body": "FMSCI",
    },
    {
        "name": "Buddh International Circuit (BIC)",
        "short_name": "bic",
        "city": "Greater Noida",
        "state": "Uttar Pradesh",
        "country": "India",
        "latitude": 28.3490,
        "longitude": 77.5334,
        "altitude_m": 208.0,
        "surface_type": "asphalt",
        "track_length_m": 402.336,
        "track_heading_deg": 90.0,
        "has_vht": 0,
        "has_timing_system": 1,
        "sanctioning_body": "FMSCI",
    },
    {
        "name": "Kari Motor Speedway",
        "short_name": "kari",
        "city": "Chettipalayam",
        "state": "Tamil Nadu",
        "country": "India",
        "latitude": 10.9167,
        "longitude": 76.9500,
        "altitude_m": 300.0,
        "surface_type": "asphalt",
        "track_length_m": 402.336,
        "track_heading_deg": 0.0,
        "has_vht": 0,
        "has_timing_system": 1,
        "sanctioning_body": "FMSCI",
    },
    {
        "name": "Hyderabad Street Drags",
        "short_name": "hyd_street",
        "city": "Hyderabad",
        "state": "Telangana",
        "country": "India",
        "latitude": 17.3850,
        "longitude": 78.4867,
        "altitude_m": 542.0,
        "surface_type": "asphalt",
        "track_length_m": 402.336,
        "track_heading_deg": 0.0,
        "has_vht": 0,
        "has_timing_system": 0,
        "sanctioning_body": None,
    },
    {
        "name": "Santa Pod Raceway (UK)",
        "short_name": "santa_pod",
        "city": "Podington",
        "state": "Bedfordshire",
        "country": "United Kingdom",
        "latitude": 52.2256,
        "longitude": -0.6231,
        "altitude_m": 76.0,
        "surface_type": "concrete",
        "track_length_m": 402.336,
        "track_heading_deg": 45.0,
        "has_vht": 1,
        "has_timing_system": 1,
        "timing_system_type": "Compulink",
        "sanctioning_body": "FIA/MSA",
    },
    {
        "name": "Auto Club Raceway at Pomona (USA)",
        "short_name": "pomona",
        "city": "Pomona",
        "state": "California",
        "country": "United States",
        "latitude": 34.0590,
        "longitude": -117.7564,
        "altitude_m": 265.0,
        "surface_type": "concrete",
        "track_length_m": 402.336,
        "track_heading_deg": 135.0,
        "has_vht": 1,
        "has_timing_system": 1,
        "timing_system_type": "Compulink",
        "sanctioning_body": "NHRA",
    },
    {
        "name": "Gainesville Raceway (USA)",
        "short_name": "gainesville",
        "city": "Gainesville",
        "state": "Florida",
        "country": "United States",
        "latitude": 29.6141,
        "longitude": -82.3628,
        "altitude_m": 50.0,
        "surface_type": "concrete",
        "track_length_m": 402.336,
        "track_heading_deg": 90.0,
        "has_vht": 1,
        "has_timing_system": 1,
        "timing_system_type": "Compulink",
        "sanctioning_body": "NHRA",
    },
    {
        "name": "Sydney Dragway (Australia)",
        "short_name": "sydney",
        "city": "Eastern Creek",
        "state": "New South Wales",
        "country": "Australia",
        "latitude": -33.8050,
        "longitude": 150.8600,
        "altitude_m": 60.0,
        "surface_type": "concrete",
        "track_length_m": 402.336,
        "track_heading_deg": 45.0,
        "has_vht": 1,
        "has_timing_system": 1,
        "timing_system_type": "Compulink",
        "sanctioning_body": "ANDRA",
    },
    {
        "name": "Dubai Autodrome Drag Strip (UAE)",
        "short_name": "dubai",
        "city": "Motor City",
        "state": "Dubai",
        "country": "United Arab Emirates",
        "latitude": 25.0498,
        "longitude": 55.2184,
        "altitude_m": 5.0,
        "surface_type": "asphalt",
        "track_length_m": 402.336,
        "track_heading_deg": 0.0,
        "has_vht": 1,
        "has_timing_system": 1,
        "timing_system_type": "ET-Slip",
        "sanctioning_body": "ATCUAE",
    },
    {
        "name": "Al-Ain Raceway (UAE)",
        "short_name": "al_ain",
        "city": "Al-Ain",
        "state": "Abu Dhabi",
        "country": "United Arab Emirates",
        "latitude": 24.1783,
        "longitude": 55.7000,
        "altitude_m": 310.0,
        "surface_type": "asphalt",
        "track_length_m": 402.336,
        "track_heading_deg": 90.0,
        "has_vht": 1,
        "has_timing_system": 1,
        "timing_system_type": "ET-Slip",
        "sanctioning_body": "ATCUAE",
    },
    {
        "name": "Circuito de Jerez (Spain)",
        "short_name": "jerez",
        "city": "Jerez de la Frontera",
        "state": "Andalusia",
        "country": "Spain",
        "latitude": 36.7085,
        "longitude": -6.0345,
        "altitude_m": 37.0,
        "surface_type": "asphalt",
        "track_length_m": 402.336,
        "track_heading_deg": 180.0,
        "has_vht": 0,
        "has_timing_system": 1,
        "timing_system_type": "Compulink",
        "sanctioning_body": "RFEDA/FIA",
    },
    # ════════════════════════════════════════════════════════════════════
    # LAND SPEED RECORD VENUES — measured mile / open-course top speed
    # ════════════════════════════════════════════════════════════════════
    {
        "name": "Bonneville Salt Flats (USA)",
        "short_name": "bonneville",
        "city": "Wendover",
        "state": "Utah",
        "country": "United States",
        "latitude": 40.7686,
        "longitude": -113.8500,
        "altitude_m": 1285.0,
        "surface_type": "salt",
        "track_length_m": 8046.72,  # 5-mile long course
        "track_heading_deg": 180.0,
        "has_vht": 0,
        "has_timing_system": 1,
        "timing_system_type": "SCTA/BNI timing beams",
        "sanctioning_body": "SCTA/BNI/FIM",
    },
    {
        "name": "El Mirage Dry Lake (USA)",
        "short_name": "el_mirage",
        "city": "Adelanto",
        "state": "California",
        "country": "United States",
        "latitude": 34.6406,
        "longitude": -117.6028,
        "altitude_m": 881.0,
        "surface_type": "dry_lake_bed",
        "track_length_m": 2092.0,  # 1.3-mile course
        "track_heading_deg": 45.0,
        "has_vht": 0,
        "has_timing_system": 1,
        "timing_system_type": "SCTA timing beams",
        "sanctioning_body": "SCTA",
    },
    {
        "name": "Loring Timing Association (USA)",
        "short_name": "loring",
        "city": "Limestone",
        "state": "Maine",
        "country": "United States",
        "latitude": 46.9486,
        "longitude": -67.8853,
        "altitude_m": 227.0,
        "surface_type": "asphalt",  # former SAC bomber runway
        "track_length_m": 2414.0,  # 1.5-mile (standing-mile + shutdown)
        "track_heading_deg": 30.0,
        "has_vht": 0,
        "has_timing_system": 1,
        "timing_system_type": "Stalker radar + MPH Racing",
        "sanctioning_body": "LTA",
    },
    {
        "name": "Texas Mile (USA)",
        "short_name": "texas_mile",
        "city": "Victoria",
        "state": "Texas",
        "country": "United States",
        "latitude": 28.8600,
        "longitude": -96.9300,
        "altitude_m": 35.0,
        "surface_type": "asphalt",
        "track_length_m": 1609.344,  # 1-mile standing start
        "track_heading_deg": 180.0,
        "has_vht": 0,
        "has_timing_system": 1,
        "timing_system_type": "Radar trap",
        "sanctioning_body": "Texas Mile LLC",
    },
    {
        "name": "Ohio Mile (USA)",
        "short_name": "ohio_mile",
        "city": "Wilmington",
        "state": "Ohio",
        "country": "United States",
        "latitude": 39.4289,
        "longitude": -83.7920,
        "altitude_m": 327.0,
        "surface_type": "asphalt",
        "track_length_m": 1609.344,
        "track_heading_deg": 45.0,
        "has_vht": 0,
        "has_timing_system": 1,
        "timing_system_type": "Timing beams + radar",
        "sanctioning_body": "ECTA",
    },
    {
        "name": "Elvington Airfield (UK)",
        "short_name": "elvington",
        "city": "Elvington",
        "state": "North Yorkshire",
        "country": "United Kingdom",
        "latitude": 53.9061,
        "longitude": -0.9875,
        "altitude_m": 21.0,
        "surface_type": "asphalt",
        "track_length_m": 2987.0,  # 9800 ft runway
        "track_heading_deg": 60.0,
        "has_vht": 0,
        "has_timing_system": 1,
        "timing_system_type": "SPEE3D / Racelogic VBOX",
        "sanctioning_body": "Straightliners/ACU",
    },
    {
        "name": "Nardò Ring High-Speed Track (Italy)",
        "short_name": "nardo",
        "city": "Nardò",
        "state": "Apulia",
        "country": "Italy",
        "latitude": 40.3297,
        "longitude": 17.8258,
        "altitude_m": 51.0,
        "surface_type": "asphalt",
        "track_length_m": 12600.0,  # 12.6 km banked oval
        "track_heading_deg": 0.0,
        "has_vht": 0,
        "has_timing_system": 1,
        "timing_system_type": "Prototype telemetry",
        "sanctioning_body": "Porsche Engineering (private)",
    },
    {
        "name": "Uyuni Salt Flat (Bolivia)",
        "short_name": "uyuni",
        "city": "Uyuni",
        "state": "Potosí",
        "country": "Bolivia",
        "latitude": -20.1338,
        "longitude": -67.4891,
        "altitude_m": 3656.0,  # highest LSR venue on earth — thin air = less drag
        "surface_type": "salt",
        "track_length_m": 10000.0,
        "track_heading_deg": 0.0,
        "has_vht": 0,
        "has_timing_system": 0,
        "timing_system_type": "Portable GPS timing",
        "sanctioning_body": None,
    },
]

# Seasonal weather normals for Indian venues (month 1–12)
# Source: historical averages from weather stations near each venue
SEED_SEASONAL_DATA = {
    "Aamby Valley Airstrip (TVR)": {
        # month: (avg_temp, avg_hum, avg_press, avg_wind, prevail_wind, track_temp, da_ft, temp_std, hum_std, press_std)
        1: (18.0, 30.0, 1018.0, 1.5, 45.0, 22.0, 2800, 3.0, 8.0, 4.0),
        2: (20.0, 28.0, 1016.0, 1.8, 45.0, 25.0, 3100, 3.0, 8.0, 4.0),
        3: (24.0, 25.0, 1013.0, 2.0, 90.0, 32.0, 3600, 3.5, 10.0, 4.0),
        4: (28.0, 30.0, 1010.0, 2.5, 90.0, 38.0, 4200, 3.0, 12.0, 4.0),
        5: (30.0, 45.0, 1006.0, 2.5, 270.0, 42.0, 4800, 2.5, 15.0, 5.0),
        6: (26.0, 75.0, 1002.0, 3.0, 270.0, 30.0, 4500, 2.0, 10.0, 5.0),
        7: (24.0, 85.0, 1000.0, 3.5, 270.0, 26.0, 4200, 1.5, 8.0, 4.0),
        8: (24.0, 85.0, 1002.0, 3.0, 270.0, 26.0, 4100, 1.5, 8.0, 4.0),
        9: (24.0, 80.0, 1006.0, 2.0, 270.0, 28.0, 3900, 2.0, 10.0, 4.0),
        10: (24.0, 60.0, 1010.0, 1.5, 90.0, 30.0, 3600, 2.5, 12.0, 4.0),
        11: (22.0, 40.0, 1014.0, 1.2, 45.0, 26.0, 3100, 3.0, 10.0, 4.0),
        12: (19.0, 32.0, 1017.0, 1.2, 45.0, 22.0, 2900, 3.0, 8.0, 4.0),
    },
    "Madras Motor Race Track (MMRT)": {
        1: (25.0, 65.0, 1014.0, 2.5, 45.0, 30.0, 1200, 2.0, 10.0, 3.0),
        2: (26.0, 60.0, 1013.0, 2.5, 45.0, 32.0, 1400, 2.0, 10.0, 3.0),
        3: (28.0, 60.0, 1011.0, 2.0, 90.0, 36.0, 1700, 2.0, 10.0, 3.0),
        4: (31.0, 65.0, 1008.0, 2.5, 180.0, 42.0, 2200, 2.0, 10.0, 4.0),
        5: (34.0, 55.0, 1005.0, 3.0, 180.0, 48.0, 2800, 2.5, 12.0, 4.0),
        6: (33.0, 50.0, 1004.0, 3.5, 270.0, 45.0, 2600, 2.0, 10.0, 4.0),
        7: (31.0, 55.0, 1004.0, 3.5, 270.0, 40.0, 2300, 2.0, 10.0, 4.0),
        8: (31.0, 60.0, 1004.0, 3.0, 270.0, 40.0, 2300, 2.0, 10.0, 4.0),
        9: (30.0, 70.0, 1006.0, 2.5, 270.0, 38.0, 2100, 2.0, 10.0, 4.0),
        10: (28.0, 75.0, 1010.0, 2.0, 45.0, 34.0, 1600, 2.0, 10.0, 3.0),
        11: (26.0, 80.0, 1012.0, 2.0, 45.0, 30.0, 1300, 2.0, 10.0, 3.0),
        12: (25.0, 75.0, 1014.0, 2.0, 45.0, 28.0, 1100, 2.0, 10.0, 3.0),
    },
    "Buddh International Circuit (BIC)": {
        1: (14.0, 60.0, 1020.0, 1.5, 315.0, 16.0, 1500, 4.0, 15.0, 5.0),
        2: (17.0, 50.0, 1017.0, 2.0, 315.0, 20.0, 1700, 4.0, 12.0, 5.0),
        3: (23.0, 35.0, 1013.0, 2.5, 270.0, 30.0, 2200, 4.0, 10.0, 4.0),
        4: (30.0, 25.0, 1008.0, 3.0, 270.0, 40.0, 3000, 4.0, 10.0, 4.0),
        5: (35.0, 25.0, 1004.0, 3.5, 270.0, 50.0, 3800, 3.0, 10.0, 5.0),
        6: (36.0, 45.0, 998.0, 3.5, 270.0, 50.0, 4200, 3.0, 15.0, 5.0),
        7: (32.0, 75.0, 998.0, 3.0, 270.0, 38.0, 3600, 2.0, 10.0, 4.0),
        8: (31.0, 80.0, 1000.0, 2.5, 270.0, 36.0, 3400, 2.0, 8.0, 4.0),
        9: (30.0, 70.0, 1004.0, 2.0, 90.0, 36.0, 3000, 2.5, 10.0, 4.0),
        10: (27.0, 50.0, 1010.0, 1.5, 90.0, 32.0, 2400, 3.0, 12.0, 4.0),
        11: (21.0, 45.0, 1016.0, 1.2, 315.0, 24.0, 1800, 3.5, 12.0, 5.0),
        12: (15.0, 55.0, 1019.0, 1.2, 315.0, 18.0, 1500, 4.0, 15.0, 5.0),
    },
    "Kari Motor Speedway": {
        1: (24.0, 55.0, 1014.0, 1.5, 90.0, 28.0, 1800, 2.5, 10.0, 3.0),
        2: (25.0, 50.0, 1013.0, 1.5, 90.0, 30.0, 2000, 2.5, 10.0, 3.0),
        3: (27.0, 45.0, 1011.0, 2.0, 90.0, 34.0, 2300, 2.5, 10.0, 3.0),
        4: (28.0, 55.0, 1008.0, 2.0, 270.0, 38.0, 2600, 2.0, 10.0, 3.0),
        5: (30.0, 50.0, 1005.0, 2.5, 270.0, 42.0, 3000, 2.0, 10.0, 4.0),
        6: (28.0, 60.0, 1004.0, 3.0, 270.0, 38.0, 2800, 2.0, 12.0, 4.0),
        7: (26.0, 75.0, 1004.0, 3.0, 270.0, 32.0, 2400, 2.0, 10.0, 3.0),
        8: (26.0, 75.0, 1006.0, 2.5, 270.0, 32.0, 2400, 2.0, 10.0, 3.0),
        9: (26.0, 70.0, 1008.0, 2.0, 90.0, 32.0, 2400, 2.0, 10.0, 3.0),
        10: (26.0, 60.0, 1011.0, 1.5, 90.0, 32.0, 2400, 2.0, 10.0, 3.0),
        11: (25.0, 55.0, 1013.0, 1.5, 90.0, 30.0, 2000, 2.0, 10.0, 3.0),
        12: (24.0, 55.0, 1014.0, 1.5, 90.0, 28.0, 1800, 2.5, 10.0, 3.0),
    },
    "Hyderabad Street Drags": {
        1: (22.0, 50.0, 1018.0, 2.0, 45.0, 26.0, 2200, 3.0, 10.0, 3.0),
        2: (24.0, 45.0, 1016.0, 2.0, 45.0, 28.0, 2400, 3.0, 10.0, 3.0),
        3: (27.0, 40.0, 1013.0, 2.5, 90.0, 34.0, 2700, 3.0, 10.0, 4.0),
        4: (30.0, 40.0, 1010.0, 2.5, 270.0, 40.0, 3200, 3.0, 10.0, 4.0),
        5: (32.0, 45.0, 1006.0, 2.5, 270.0, 44.0, 3600, 2.5, 10.0, 5.0),
        6: (28.0, 70.0, 1003.0, 3.0, 270.0, 34.0, 3200, 2.0, 15.0, 5.0),
        7: (26.0, 80.0, 1002.0, 3.0, 270.0, 30.0, 2800, 2.0, 10.0, 4.0),
        8: (26.0, 80.0, 1004.0, 2.5, 270.0, 30.0, 2800, 2.0, 10.0, 4.0),
        9: (26.0, 75.0, 1008.0, 2.0, 270.0, 32.0, 2800, 2.5, 12.0, 4.0),
        10: (25.0, 65.0, 1012.0, 1.5, 45.0, 30.0, 2400, 3.0, 10.0, 3.0),
        11: (23.0, 55.0, 1015.0, 1.5, 45.0, 27.0, 2200, 3.0, 10.0, 3.0),
        12: (21.0, 50.0, 1017.0, 1.5, 45.0, 25.0, 2000, 3.0, 10.0, 3.0),
    },
    "Santa Pod Raceway (UK)": {
        # UK maritime climate: mild summers, cool winters, moderate humidity
        1: (3.0, 70.0, 1020.0, 3.5, 270.0, 5.0, 1000, 4.0, 12.0, 8.0),
        2: (4.0, 68.0, 1019.0, 3.5, 270.0, 6.0, 1100, 4.0, 12.0, 8.0),
        3: (7.0, 65.0, 1018.0, 3.0, 270.0, 10.0, 1400, 4.0, 12.0, 7.0),
        4: (11.0, 60.0, 1016.0, 2.5, 270.0, 15.0, 1800, 4.0, 10.0, 6.0),
        5: (16.0, 55.0, 1014.0, 2.5, 270.0, 21.0, 2200, 3.0, 10.0, 6.0),
        6: (19.0, 60.0, 1012.0, 2.5, 270.0, 24.0, 2400, 3.0, 10.0, 6.0),
        7: (21.0, 62.0, 1011.0, 2.5, 270.0, 26.0, 2500, 2.5, 10.0, 6.0),
        8: (21.0, 62.0, 1012.0, 2.5, 270.0, 26.0, 2500, 2.5, 10.0, 6.0),
        9: (17.0, 65.0, 1013.0, 3.0, 270.0, 21.0, 2100, 3.0, 10.0, 6.0),
        10: (12.0, 68.0, 1015.0, 3.5, 270.0, 14.0, 1600, 4.0, 12.0, 6.0),
        11: (7.0, 70.0, 1017.0, 3.5, 270.0, 9.0, 1200, 4.0, 12.0, 7.0),
        12: (4.0, 72.0, 1019.0, 3.5, 270.0, 6.0, 1100, 4.0, 12.0, 8.0),
    },
    "Auto Club Raceway at Pomona (USA)": {
        # SoCal inland: hot dry summers, mild winters, low humidity
        1: (14.0, 50.0, 1019.0, 1.5, 315.0, 18.0, 1200, 4.0, 12.0, 5.0),
        2: (15.0, 48.0, 1018.0, 1.5, 315.0, 19.0, 1300, 4.0, 12.0, 5.0),
        3: (18.0, 45.0, 1016.0, 1.5, 315.0, 23.0, 1600, 4.0, 10.0, 5.0),
        4: (22.0, 40.0, 1013.0, 1.5, 315.0, 28.0, 2000, 4.0, 10.0, 5.0),
        5: (27.0, 35.0, 1009.0, 1.5, 315.0, 35.0, 2600, 3.0, 10.0, 5.0),
        6: (33.0, 30.0, 1008.0, 1.5, 315.0, 42.0, 3400, 3.0, 8.0, 5.0),
        7: (35.0, 28.0, 1008.0, 1.5, 315.0, 45.0, 3800, 2.5, 8.0, 5.0),
        8: (34.0, 30.0, 1009.0, 1.5, 315.0, 44.0, 3600, 2.5, 8.0, 5.0),
        9: (31.0, 32.0, 1011.0, 1.5, 315.0, 40.0, 3200, 3.0, 8.0, 5.0),
        10: (25.0, 38.0, 1013.0, 1.5, 315.0, 31.0, 2400, 3.0, 10.0, 5.0),
        11: (19.0, 42.0, 1015.0, 1.5, 315.0, 24.0, 1700, 4.0, 10.0, 5.0),
        12: (14.0, 48.0, 1018.0, 1.5, 315.0, 18.0, 1200, 4.0, 12.0, 5.0),
    },
    "Gainesville Raceway (USA)": {
        # Florida subtropical: hot humid summers, mild winters, high humidity
        1: (16.0, 70.0, 1017.0, 2.5, 45.0, 21.0, 1000, 3.0, 12.0, 4.0),
        2: (17.0, 68.0, 1016.0, 2.5, 45.0, 22.0, 1100, 3.0, 12.0, 4.0),
        3: (20.0, 65.0, 1014.0, 2.5, 45.0, 26.0, 1400, 3.0, 12.0, 4.0),
        4: (24.0, 68.0, 1011.0, 2.5, 180.0, 32.0, 1900, 3.0, 12.0, 4.0),
        5: (28.0, 72.0, 1008.0, 3.0, 180.0, 38.0, 2600, 2.5, 10.0, 5.0),
        6: (30.0, 78.0, 1006.0, 3.5, 270.0, 40.0, 2900, 2.0, 8.0, 5.0),
        7: (31.0, 80.0, 1005.0, 3.5, 270.0, 41.0, 3100, 2.0, 8.0, 5.0),
        8: (31.0, 80.0, 1005.0, 3.0, 270.0, 41.0, 3100, 2.0, 8.0, 5.0),
        9: (29.0, 77.0, 1008.0, 3.0, 270.0, 38.0, 2700, 2.0, 10.0, 4.0),
        10: (25.0, 72.0, 1011.0, 2.5, 45.0, 32.0, 1900, 3.0, 12.0, 4.0),
        11: (21.0, 70.0, 1014.0, 2.5, 45.0, 25.0, 1300, 3.0, 12.0, 4.0),
        12: (17.0, 70.0, 1016.0, 2.5, 45.0, 21.0, 1000, 3.0, 12.0, 4.0),
    },
    "Sydney Dragway (Australia)": {
        # Southern Hemisphere: seasons reversed. Jan=summer, Jul=winter
        1: (26.0, 60.0, 1013.0, 2.5, 45.0, 33.0, 1200, 2.5, 10.0, 4.0),
        2: (26.0, 62.0, 1013.0, 2.5, 45.0, 33.0, 1200, 2.5, 10.0, 4.0),
        3: (23.0, 62.0, 1014.0, 2.5, 45.0, 29.0, 1000, 2.5, 10.0, 4.0),
        4: (19.0, 60.0, 1015.0, 2.0, 45.0, 24.0, 800, 3.0, 10.0, 3.0),
        5: (15.0, 58.0, 1016.0, 2.0, 45.0, 19.0, 600, 3.0, 10.0, 3.0),
        6: (12.0, 56.0, 1017.0, 2.0, 270.0, 15.0, 500, 3.0, 10.0, 3.0),
        7: (11.0, 55.0, 1017.0, 1.5, 270.0, 14.0, 450, 3.5, 10.0, 3.0),
        8: (12.0, 55.0, 1016.0, 1.5, 270.0, 15.0, 500, 3.5, 10.0, 3.0),
        9: (15.0, 56.0, 1015.0, 2.0, 45.0, 20.0, 650, 3.0, 10.0, 3.0),
        10: (19.0, 58.0, 1014.0, 2.0, 45.0, 25.0, 900, 2.5, 10.0, 4.0),
        11: (22.0, 60.0, 1013.0, 2.5, 45.0, 29.0, 1000, 2.5, 10.0, 4.0),
        12: (25.0, 62.0, 1013.0, 2.5, 45.0, 32.0, 1100, 2.5, 10.0, 4.0),
    },
    "Dubai Autodrome Drag Strip (UAE)": {
        # Desert climate: extreme heat in summer, mild winters, very low humidity
        1: (19.0, 35.0, 1016.0, 2.0, 270.0, 24.0, 1100, 3.0, 10.0, 5.0),
        2: (21.0, 32.0, 1015.0, 2.0, 270.0, 26.0, 1300, 3.0, 8.0, 5.0),
        3: (26.0, 28.0, 1013.0, 2.0, 270.0, 32.0, 1800, 3.0, 8.0, 5.0),
        4: (32.0, 25.0, 1010.0, 2.0, 270.0, 40.0, 2600, 3.0, 8.0, 5.0),
        5: (39.0, 22.0, 1006.0, 2.0, 270.0, 50.0, 3900, 2.5, 8.0, 6.0),
        6: (43.0, 20.0, 1004.0, 1.5, 270.0, 55.0, 4600, 2.0, 5.0, 6.0),
        7: (45.0, 22.0, 1003.0, 1.5, 270.0, 57.0, 4900, 2.0, 5.0, 6.0),
        8: (44.0, 24.0, 1004.0, 1.5, 270.0, 56.0, 4700, 2.0, 5.0, 6.0),
        9: (40.0, 26.0, 1007.0, 2.0, 270.0, 51.0, 3900, 2.5, 8.0, 5.0),
        10: (33.0, 28.0, 1010.0, 2.0, 270.0, 41.0, 2600, 3.0, 8.0, 5.0),
        11: (26.0, 32.0, 1013.0, 2.0, 270.0, 32.0, 1800, 3.0, 8.0, 5.0),
        12: (21.0, 35.0, 1015.0, 2.0, 270.0, 26.0, 1300, 3.0, 10.0, 5.0),
    },
    "Al-Ain Raceway (UAE)": {
        # Inland desert: even hotter than coastal, very dry, higher altitude effect
        1: (17.0, 30.0, 1018.0, 1.5, 270.0, 22.0, 1500, 3.0, 10.0, 5.0),
        2: (19.0, 28.0, 1017.0, 1.5, 270.0, 24.0, 1700, 3.0, 8.0, 5.0),
        3: (24.0, 25.0, 1015.0, 1.5, 270.0, 31.0, 2300, 3.0, 8.0, 5.0),
        4: (31.0, 22.0, 1012.0, 1.5, 270.0, 41.0, 3300, 3.0, 8.0, 5.0),
        5: (39.0, 20.0, 1008.0, 1.5, 270.0, 50.0, 4600, 2.5, 5.0, 6.0),
        6: (44.0, 18.0, 1006.0, 1.0, 270.0, 56.0, 5500, 2.0, 5.0, 6.0),
        7: (47.0, 20.0, 1005.0, 1.0, 270.0, 60.0, 6000, 2.0, 5.0, 6.0),
        8: (46.0, 21.0, 1006.0, 1.0, 270.0, 59.0, 5800, 2.0, 5.0, 6.0),
        9: (41.0, 23.0, 1008.0, 1.5, 270.0, 52.0, 4800, 2.5, 8.0, 5.0),
        10: (33.0, 25.0, 1011.0, 1.5, 270.0, 43.0, 3300, 3.0, 8.0, 5.0),
        11: (25.0, 28.0, 1014.0, 1.5, 270.0, 32.0, 2300, 3.0, 8.0, 5.0),
        12: (19.0, 30.0, 1016.0, 1.5, 270.0, 24.0, 1700, 3.0, 10.0, 5.0),
    },
    "Circuito de Jerez (Spain)": {
        # Mediterranean: hot dry summers, mild wet winters, Atlantic-facing
        1: (10.0, 68.0, 1018.0, 3.0, 270.0, 13.0, 800, 4.0, 12.0, 6.0),
        2: (11.0, 66.0, 1017.0, 3.0, 270.0, 14.0, 900, 4.0, 12.0, 6.0),
        3: (14.0, 62.0, 1015.0, 2.5, 270.0, 19.0, 1200, 4.0, 10.0, 6.0),
        4: (18.0, 58.0, 1012.0, 2.5, 270.0, 25.0, 1700, 4.0, 10.0, 5.0),
        5: (23.0, 52.0, 1009.0, 2.5, 270.0, 31.0, 2200, 3.0, 10.0, 5.0),
        6: (28.0, 48.0, 1008.0, 2.5, 270.0, 37.0, 2700, 2.5, 8.0, 5.0),
        7: (31.0, 45.0, 1007.0, 2.5, 270.0, 41.0, 3100, 2.5, 8.0, 5.0),
        8: (31.0, 46.0, 1008.0, 2.5, 270.0, 41.0, 3100, 2.5, 8.0, 5.0),
        9: (27.0, 52.0, 1010.0, 2.5, 270.0, 35.0, 2600, 3.0, 8.0, 5.0),
        10: (21.0, 58.0, 1012.0, 3.0, 270.0, 28.0, 1900, 3.0, 10.0, 5.0),
        11: (15.0, 64.0, 1015.0, 3.0, 270.0, 19.0, 1200, 4.0, 10.0, 6.0),
        12: (11.0, 68.0, 1017.0, 3.0, 270.0, 14.0, 900, 4.0, 12.0, 6.0),
    },
}
