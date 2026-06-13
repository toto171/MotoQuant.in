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
  // /api/tires now returns the total matching count (before the limit slice)
  // alongside the page. Optional so older backends that omit it still type.
  total?: number;
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

// Match clause inside fitment_rules (family/category-tier constraints).
// Schema documented at motoquant/database/schema.py::parts.fitment_rules.
// Every field is optional because each part declares only the constraints
// relevant to it (e.g. a "bodywork" universal part may omit all of them).
export interface FitmentMatch {
  manufacturers?: string[];
  engine_configs?: string[]; // "I1" | "I2" | "I3" | "I4" | "V2" | "V4" | ...
  categories?: string[];
  displacement_min_cc?: number;
  displacement_max_cc?: number;
  chain_pitch?: string; // "428" | "520" | "525" | "530"
  stroke_type?: number; // 2 or 4
  [extra: string]: unknown; // tolerate future schema additions (e.g. model_keywords)
}

// Shape of a parsed fitment_rules JSON blob as returned by /api/parts.
// `tier` is one of "exact" | "family" | "category" | "universal" (see
// motoquant/parts/compatibility.py). API may also return the raw JSON string
// if parsing fails; the union below documents that fallback explicitly.
export interface FitmentRule {
  tier: "exact" | "family" | "category" | "universal" | string;
  bike_ids?: number[];
  excluded_bike_ids?: number[];
  match?: FitmentMatch;
  description?: string;
  [extra: string]: unknown;
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
  // Legacy exact-bike compatibility list (JSON array of bike_model_ids).
  // Falls back to `string` if the API couldn't parse the stored JSON.
  compatible_bikes?: number[] | string | null;
  // Family-/category-tier fitment ruleset. Falls back to `string` if the API
  // couldn't parse the stored JSON.
  fitment_rules?: FitmentRule | string | null;
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

// ─── Save run ────────────────────────────────────────────────────────────

export interface SaveRunRequest {
  bike_id: number;
  venue_id?: number | null;
  et_quarter_s: number;
  trap_speed_kmh: number;
  et_60ft_s?: number | null;
  et_eighth_s?: number | null;
  et_1000ft_s?: number | null;
  notes?: string | null;
}

export interface SaveRunResponse {
  run_id: number;
  bike_id: number;
  bike_config_id: number;
}

// ─── Leaderboard ─────────────────────────────────────────────────────────

export interface LeaderboardEntry {
  id: number;
  et_quarter_s: number;
  trap_speed_kmh: number;
  manufacturer: string | null;
  model: string | null;
  year: number | null;
  created_at: string | null;
}

export interface LeaderboardResponse {
  leaderboard: LeaderboardEntry[];
  total: number;
}

// ─── Compare (A vs B) ────────────────────────────────────────────────────

export interface CompareRequest {
  // Build A (baseline)
  a_bike_id?: number | null;
  a_bike_preset?: string | null;
  a_power_boost_pct?: number;
  a_mass_delta_kg?: number;
  a_rider_mass_kg?: number;
  a_part_ids?: number[];
  a_front_tire_id?: number | null;
  a_rear_tire_id?: number | null;

  // Build B (modified)
  b_bike_id?: number | null;
  b_bike_preset?: string | null;
  b_power_boost_pct?: number;
  b_mass_delta_kg?: number;
  b_rider_mass_kg?: number;
  b_part_ids?: number[];
  b_front_tire_id?: number | null;
  b_rear_tire_id?: number | null;

  // Shared conditions
  venue_id?: number | null;
  ambient_temp_c?: number | null;
  track_temp_c?: number | null;
  humidity_pct?: number | null;
  headwind_kmh?: number | null;
}

// Compare timeseries is a subset of SimTimeseries — no x_m / tire_temp / forces.
export interface CompareTimeseries {
  t_s: number[];
  v_kmh: number[];
  rpm: number[];
  gear: number[];
  accel_g: number[];
  traction_pct: number[];
  power_kw: number[];
}

export interface CompareBuildSummary {
  label: "A" | "B";
  et_quarter_s: number;
  trap_speed_kmh: number;
  et_60ft_s: number;
  et_eighth_s: number;
  bike_name: string;
  peak_power_hp: number;
  total_mass_kg: number;
  parts_applied: AppliedPart[];
  build_cost_inr: number;
  timeseries?: CompareTimeseries;
}

export interface CompareDelta {
  et_s: number;
  trap_kmh: number;
  faster: "A" | "B" | "tie";
  cost_diff_inr: number;
}

export interface CompareResponse {
  a: CompareBuildSummary;
  b: CompareBuildSummary;
  delta: CompareDelta;
}

// ─── Generic error ───────────────────────────────────────────────────────

export interface ApiError {
  detail: string;
  status: number;
}

// ─── Chat (Phase A LLM) ───────────────────────────────────────────────────

export interface ChatRequest {
  /** Natural-language tuning query, 1–2000 chars. */
  query: string;
  /** Whether to request a plain-English summary from the LLM. */
  run_summary?: boolean;
}

export interface ChatBikeSuggestion {
  id: number | null;
  manufacturer: string | null;
  model: string | null;
  year_range: string | null;
}

export interface ChatResponse {
  raw_query: string;
  bike_name: string;
  bike_id: number | null;
  venue_name: string | null;
  venue_id: number | null;
  parsed_notes: string;
  optimization_goal: string;
  bike_suggestions: ChatBikeSuggestion[];
  sim_result: Record<string, unknown> | null;
  summary: string | null;
  error: string | null;
  error_detail: string | null;
}

// ─── Surrogate model (POST /api/surrogate/*) ─────────────────────────────
// Fast inference (target p95 < 5 ms) over a trained DNN/XGBoost model.
// Used for live BuildPage previews where running a full physics sim per
// slider tick would feel laggy. Falls back to /api/simulate/quick when
// `within_training_envelope` is false (signals out-of-distribution input).

export interface SurrogatePredictRequest {
  bike_id?: number | null;
  power_boost_pct?: number; // -50..200
  mass_delta_kg?: number;   // -100..200
  aero_cd_override?: number | null; // 0.30..1.20
  tire_mu_override?: number | null; // 0.50..1.80
  altitude_m?: number; // 0..5000
  rider_weight_kg?: number; // 40..150
}

export interface SurrogatePredictResponse {
  et_s: number;
  trap_kmh: number;
  inference_ms: number;
  source: string;            // "dnn" | "xgboost" | etc.
  within_training_envelope: boolean;
  envelope_violations: string[];
}

export interface SurrogateCompareRequest {
  config_a: SurrogatePredictRequest;
  config_b: SurrogatePredictRequest;
}

export interface SurrogateCompareResponse {
  a: SurrogatePredictResponse;
  b: SurrogatePredictResponse;
  delta_et_s: number;
  delta_trap_kmh: number;
  faster: "a" | "b" | "tie";
}

// ─── Build optimizer + ECU autotune (Track B) ─────────────────────────────

export interface OptimizeBuildRequest {
  bike_id?: number;
  bike_preset?: string;
  budget_inr: number;
  goal: "min_et" | "max_trap";
  profile?: string;
  rider_weight_kg?: number;
  venue_id?: number;
  max_candidates?: number;
}

export interface OptimizedPart {
  part_id: number;
  name: string;
  brand: string;
  category: string;
  category_display: string;
  price_inr: number;
  delta_et_s: number;
  delta_trap_ms: number;
  roi_score: number | null;
  cost_per_tenth_inr: number | null;
  is_compatible: boolean;
}

export interface OptimizeSynergy {
  category_a: string;
  category_b: string;
  multiplier: number;
  description: string;
}

export interface OptimizeWarning {
  severity: string;
  category_a: string;
  category_b: string | null;
  message: string;
}

export interface OptimizeNextUpgrade {
  part: OptimizedPart;
  marginal_et_gain_s: number;
  marginal_cost_inr: number;
  marginal_roi: number | null;
  reason: string;
}

export interface OptimizedBuild {
  bike_name: string;
  goal: string;
  budget_inr: number;
  profile: string;
  base_et_s: number;
  base_trap_kmh: number;
  optimized_et_s: number;
  optimized_trap_kmh: number;
  delta_et_s: number;
  delta_trap_kmh: number;
  total_cost_inr: number;
  budget_used_pct: number;
  cost_per_tenth_inr: number | null;
  parts: OptimizedPart[];
  synergies: OptimizeSynergy[];
  warnings: OptimizeWarning[];
  next_upgrade: OptimizeNextUpgrade | null;
  // category_priority is a heterogeneous server aggregate; not rendered.
  category_priority: Array<Record<string, unknown>>;
  parts_evaluated: number;
  parts_skipped_incompatible: number;
  parts_skipped_no_gain: number;
  scoring_method: string;
  scoring_stats: Record<string, unknown>;
}

export interface AutotuneRequest {
  bike_id?: number;
  bike_preset?: string;
  location?: string;
  venue_id?: number;
  lat?: number;
  lon?: number;
  altitude_m?: number;
  ambient_temp_c?: number;
  track_temp_c?: number;
  humidity_pct?: number;
  pressure_hpa?: number;
  rider_weight_kg?: number;
  gear_span?: number;
  launch_steps?: number;
}

export interface AutotuneEnvironment {
  location: string | null;
  temperature_c: number;
  track_temp_c: number;
  humidity_pct: number;
  pressure_hpa: number;
  altitude_m: number;
  air_density_kgm3: number;
  density_altitude_ft: number;
  density_altitude_m: number;
  power_correction_pct: number;
  power_loss_pct: number;
}

export interface AutotuneStock {
  et_s: number;
  trap_kmh: number;
  launch_rpm: number;
  front_sprocket: number;
  rear_sprocket: number;
  rear_pressure_psi: number;
  front_pressure_psi: number;
}

export interface AutotuneGearingCandidate {
  front_sprocket: number;
  rear_sprocket: number;
  final_drive: number;
  et_s: number;
  trap_kmh: number;
  is_stock: boolean;
}

export interface AutotuneGearing {
  adjustable: boolean;
  drive: string;
  stock_front?: number;
  stock_rear?: number;
  recommended_front?: number;
  recommended_rear?: number;
  recommended_final_drive: number;
  et_s: number;
  trap_kmh?: number;
  delta_et_s: number;
  recommendation: string;
  candidates: AutotuneGearingCandidate[];
}

export interface AutotuneLaunchCandidate {
  launch_rpm: number;
  et_s: number;
  trap_kmh: number;
  is_stock: boolean;
}

export interface AutotuneLaunchRpm {
  stock_rpm: number;
  recommended_rpm: number;
  et_s: number;
  trap_kmh: number;
  delta_et_s: number;
  rationale: string;
  candidates: AutotuneLaunchCandidate[];
}

export interface AutotuneTyrePressure {
  stock_rear_psi: number;
  stock_front_psi: number;
  rear_psi: number;
  front_psi: number;
  rationale: string;
  is_guideline: boolean;
}

export interface AutotuneFuelTiming {
  fuel_trim_pct: number;
  timing_advance_deg: number;
  density_ratio: number;
  applicable: boolean;
  rationale: string;
  is_guideline: boolean;
}

export interface AutotuneCombined {
  et_s: number;
  trap_kmh: number;
  delta_et_s: number;
}

export interface EcuAutotune {
  bike_name: string;
  environment: AutotuneEnvironment;
  stock: AutotuneStock;
  gearing: AutotuneGearing;
  launch_rpm: AutotuneLaunchRpm;
  tyre_pressure: AutotuneTyrePressure;
  fuel_timing: AutotuneFuelTiming;
  combined: AutotuneCombined;
  rationale: string;
  scoring_method: string;
  environment_source: string;
}

// ─── Background jobs (POST /api/jobs/*) ───────────────────────────────────
// Long-running work (full sim, top-speed, optimise, autotune) runs on a
// daemon thread server-side; the client polls for real progress instead of
// showing an indeterminate spinner. The synchronous routes still exist for
// backends that predate /api/jobs/* (the bundled sidecar may be older), so
// runJob() falls back to them on 404/405.
//   POST /api/jobs/{kind}  → 202 { job_id, kind, status }
//   GET  /api/jobs/{id}    → { status, progress 0..1, stage, result|error }
//   POST /api/jobs/{id}/cancel  (cooperative Stop)

export type JobKind = "simulate" | "topspeed" | "optimize" | "autotune";

// Mirrors motoquant/jobs.py Job.status.
export type JobStatus =
  | "queued"
  | "running"
  | "done"
  | "error"
  | "cancelled";

export interface JobStartResponse {
  job_id: string;
  kind: string;
  status: JobStatus;
}

// GET /api/jobs/{id}. `result` is present only when status === "done"; its
// shape depends on `kind` (a SimulateResponse, TopSpeed result, OptimizedBuild
// or EcuAutotune). Callers narrow it themselves.
export interface JobStatusResponse {
  job_id: string;
  kind: string;
  status: JobStatus;
  progress: number; // 0..1
  stage: string;
  result?: unknown;
  error?: string;
}

// What runJob() reports up to the UI on each poll (and during connect /
// restart transitions where progress is not yet known).
export interface JobProgress {
  status: "connecting" | JobStatus;
  progress: number | null;
  stage: string;
}

