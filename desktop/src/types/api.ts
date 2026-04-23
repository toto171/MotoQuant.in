// TypeScript mirrors of the FastAPI Pydantic schemas exposed by motoquant.api.
// Keep this file in lockstep with motoquant/api.py — if a field is added or
// renamed on the server, fix it here (and everywhere the renamed field is
// consumed). The backend rounds numeric values before returning; the frontend
// treats them as opaque numbers.

// ─── Bikes ───────────────────────────────────────────────────────────────

export interface BikeSummary {
  id: number;
  manufacturer: string | null;
  model: string | null;
  year: number | null;
  category: string | null;
  displacement_cc: number | null;
  peak_power_hp: number | null;
  dry_mass_kg: number | null;
  data_quality: string | null;
}

export interface BikesListResponse {
  total: number;
  offset: number;
  limit: number;
  bikes: BikeSummary[];
}

export interface TireFitment {
  position: "front" | "rear" | string;
  fitment_type: string; // "oem" | "recommended" | "drag_prep"
  manufacturer: string;
  model: string;
  size_designation: string;
  compound_type: string;
  tire_id: number;
}

// /api/bikes/{id} returns every column plus optional extras from bike_configs.
// The fields below are the ones the UI actually reads; extras are tolerated.
export interface BikeDetail extends BikeSummary {
  model_code?: string | null;
  year_to?: number | null;
  subcategory?: string | null;
  cylinder_count?: number | null;
  cylinder_config?: string | null;
  bore_mm?: number | null;
  stroke_mm?: number | null;
  compression_ratio?: number | null;
  peak_power_rpm?: number | null;
  peak_torque_nm?: number | null;
  peak_torque_rpm?: number | null;
  wet_mass_kg?: number | null;
  wheelbase_mm?: number | null;
  wheelbase_m?: number | null;
  seat_height_mm?: number | null;
  fuel_capacity_l?: number | null;
  cd?: number | null;
  frontal_area_m2?: number | null;
  front_sprocket?: number | null;
  rear_sprocket?: number | null;
  chain_pitch?: string | null;
  cog_height_mm?: number | null;
  cog_height_m?: number | null;
  redline_rpm?: number | null;
  validation_et_s?: number | null;
  validation_trap_kmh?: number | null;
  validation_source?: string | null;
  tire_fitments?: TireFitment[];
  [extra: string]: unknown;
}

// ─── Venues ──────────────────────────────────────────────────────────────

export interface Venue {
  id: number;
  name: string;
  country: string;
  city?: string | null;
  altitude_m: number | null;
  surface_type?: string | null;
  track_length_m?: number | null;
  latitude?: number | null;
  longitude?: number | null;
  [extra: string]: unknown;
}

export interface VenuesResponse {
  venues: Venue[];
}

// ─── Tires ───────────────────────────────────────────────────────────────

export interface Tire {
  id: number;
  manufacturer: string;
  model: string;
  model_name?: string;
  size_designation: string;
  compound_type: string;
  [extra: string]: unknown;
}

export interface TiresResponse {
  tires: Tire[];
}

// ─── Parts ───────────────────────────────────────────────────────────────

export interface PartsCategory {
  id: number;
  name: string;
  display_name: string;
  [extra: string]: unknown;
}

export interface PartsCategoriesResponse {
  categories: PartsCategory[];
}

export interface Part {
  id: number;
  category_id: number;
  category_name: string;
  category_display: string;
  brand: string;
  model_name: string;
  price_inr: number | null;
  power_delta_hp?: number | null;
  mass_delta_kg?: number | null;
  param_overrides?: Record<string, number | string | boolean> | null;
  param_deltas?: Record<string, number> | null;
  param_multipliers?: Record<string, number> | null;
  specifications?: Record<string, unknown> | null;
  compatible_bikes?: unknown;
  fitment_rules?: unknown;
  compatible?: boolean;
  fitment_reason?: string | null;
  [extra: string]: unknown;
}

export interface PartsResponse {
  parts: Part[];
  total: number;
  bike_id: number | null;
  compatible_only: boolean;
}

// ─── Simulation ──────────────────────────────────────────────────────────

export interface SimulateRequest {
  bike_id?: number | null;
  bike_preset?: "gsxr1000_k5" | "yzfr1_4c8" | "hayabusa_gen1" | null;
  power_boost_pct?: number;
  mass_delta_kg?: number;
  rider_mass_kg?: number;
  front_tire_id?: number | null;
  rear_tire_id?: number | null;
  venue_id?: number | null;
  ambient_temp_c?: number | null;
  track_temp_c?: number | null;
  humidity_pct?: number | null;
  headwind_kmh?: number | null;
  use_adaptive_dt?: boolean;
}

export interface Splits {
  "60ft_s": number;
  "330ft_s": number;
  "660ft_s": number;
  "1000ft_s": number;
  "1320ft_s": number;
}

export interface SimBikeSummary {
  manufacturer: string;
  model: string;
  peak_power_hp: number;
  dry_mass_kg: number;
}

export interface SimConfigSummary {
  peak_power_hp: number;
  peak_torque_nm: number;
  total_mass_kg: number;
  dry_mass_kg: number;
  displacement_cc: number | null;
  redline_rpm: number | null;
  gear_count: number;
  cd: number | null;
  rider_mass_kg: number;
}

export interface SimTimeseries {
  t_s: number[];
  v_kmh: number[];
  x_m: number[];
  rpm: number[];
  gear: number[];
  accel_g: number[];
  traction_pct: number[];
  tire_temp_c: number[];
  power_kw: number[];
  F_drive_N: number[];
  F_drag_N: number[];
}

export interface SimulateResponse {
  et_quarter_s: number;
  trap_speed_kmh: number;
  trap_speed_ms: number;
  splits: Splits;
  bike: SimBikeSummary;
  config: SimConfigSummary;
  timeseries: SimTimeseries;
}

// ─── Quick sim ───────────────────────────────────────────────────────────

export interface QuickSimRequest {
  bike_id?: number | null;
  bike_preset?: string | null;
  power_boost_pct?: number;
  mass_delta_kg?: number;
  rider_mass_kg?: number;
  part_ids?: number[];
  front_tire_id?: number | null;
  rear_tire_id?: number | null;
  venue_id?: number | null;
  ambient_temp_c?: number | null;
  track_temp_c?: number | null;
  humidity_pct?: number | null;
  headwind_kmh?: number | null;
}

export interface AppliedPart {
  id: number;
  name: string;
  brand: string;
  price_inr: number | null;
}

export interface QuickSimResponse {
  et_quarter_s: number;
  trap_speed_kmh: number;
  et_60ft_s: number;
  et_eighth_s: number;
  bike_name: string;
  peak_power_hp: number;
  total_mass_kg: number;
  parts_applied: AppliedPart[];
  build_cost_inr: number;
  stock_et_s: number | null;
  et_delta_s: number | null;
}

// ─── Generic error ───────────────────────────────────────────────────────

export interface ApiError {
  detail: string;
  status: number;
}
