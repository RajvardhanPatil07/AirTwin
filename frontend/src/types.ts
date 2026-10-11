export type SourceType = "observed" | "modeled" | "synthetic";
export type RegionId = "pcmc";
export interface RegionInfo {
  id: RegionId;
  name: string;
  bounds: [[number, number], [number, number]];
  grid_size: number;
  boundary?: ZoneCollection | null;
  forecast_provider: string;
}
export interface DataPoint {
  model_reference_id?: string | null;
  value: number;
  unit: string;
  source_type: SourceType;
  timestamp: string;
}
export interface Provenance {
  source_type: SourceType;
  assumptions: string[];
}
export interface Station extends Provenance {
  model_reference_id?: string | null;
  id: string;
  name: string;
  short_name: string;
  latitude: number;
  longitude: number;
  pm25: number;
  timestamp: string;
  pollutants?: Record<string, DataPoint>;
  weather?: Weather;
}
export interface Cell extends Provenance {
  measurement_support?: { nearest_monitor_km: number | null; nearest_monitor_timestamp: string | null; synchronized_monitor_count: number; uncertainty: string } | null;
  id: string;
  latitude: number;
  longitude: number;
  bounds: [[number, number], [number, number]];
  pm25: number;
  background: number;
  population: number;
  population_source_type: SourceType;
  local_weights: Cuts;
}
export interface Cuts {
  traffic: number;
  industry: number;
  dust: number;
}
export type ActionId = keyof Cuts | "combined";
export interface ScenarioResult extends Provenance {
  id: ActionId;
  name: string;
  cuts: Cuts;
  rank: number;
  before: number;
  after: number;
  reduction: number;
  reduction_low: number;
  reduction_high: number;
  reduction_percent: number;
  exposure_benefit: number;
  exposure_benefit_low?: number;
  exposure_benefit_high?: number;
  population_source_type: SourceType;
  cells: Cell[];
}
export interface ScenarioResponse extends Provenance {
  scenario_id: string;
  location_id: string;
  location_status?: "estimated" | "no_resolvable_local_excess";
  status_reason?: string | null;
  results: ScenarioResult[];
}
export interface StationsResponse extends Provenance {
  stations: Station[];
  warnings?: string[];
  data_mode?: string;
  weather?: Weather;
  zones?: ZoneCollection;
  zones_source_type?: "mapped" | "illustrative";
  region?: RegionInfo;
  coverage?: Record<string, string | number | string[]>;
}
export interface HotspotsResponse extends Provenance {
  cells: Cell[];
}
export interface SeriesPoint {
  timestamp: string;
  actual: number | null;
  predicted: number | null;
  persistence: number | null;
  p10: number | null;
  p90: number | null;
}
export interface ForecastResponse extends Provenance {
  selection?: StationSelection | null;
  forecast_provider?: string | null;
  model_id?: string | null;
  model_version?: string | null;
  issued_at?: string | null;
  input_cutoff?: string | null;
  fallback_reason?: string | null;
  location_id: string;
  history_source_type: SourceType;
  history_reference?: string;
  shap?: ShapExplanation | null;
  weather_forecast?: Weather[];
  series: SeriesPoint[];
}
export interface Metrics {
  mae: number;
  rmse: number;
  r2: number;
  persistence_mae: number;
  improvement_percent: number;
  interval_coverage: number | null;
}
export interface BacktestResponse extends Provenance {
  selection?: StationSelection | null;
  location_id: string;
  target_source_type: SourceType;
  method: string;
  seasonal_baseline?: Record<string, number>;
  cv?: Record<string, number | string>[];
  skill?: SkillRow[];
  model?: string;
  series: SeriesPoint[];
  metrics: Metrics | null;
  available?: boolean;
}
export interface SkillRow {
  horizon: number;
  mae: number;
  persistence_mae: number;
  lightgbm_only_mae: number;
  seasonal_mae: number;
  cams_mae?: number;
  improvement_percent: number;
  interval_coverage: number;
  blend_weight: number;
}
export interface TimelineFrame {
  hour: number;
  timestamp: string;
  source_type: SourceType;
  stations: { id: string; pm25: number }[];
  cells: { id: string; pm25: number }[];
}
export interface TimelineResponse extends Provenance {
  origin: string;
  frames: TimelineFrame[];
}
export interface AttributionResponse extends Provenance {
  location_id: string;
  background: number;
  status?: "estimated" | "unresolved";
  status_reason?: string | null;
  shares: { name: string; value: number; color: string }[];
}
export interface DashboardData {
  stations: Station[];
  cells: Cell[];
  demo: boolean;
  warning: string | null;
  weather?: Weather;
  zones?: ZoneCollection;
  zones_source_type?: "mapped" | "illustrative";
  region?: RegionInfo;
  coverage?: Record<string, string | number | string[]>;
}

export interface ShapExplanation {
  groups: Record<string, number>;
  base_value: number;
  prediction: number;
  method: string;
  blend_weight?: number;
}
export interface Weather {
  source_type: SourceType;
  timestamp: string;
  wind_direction_10m?: number;
  wind_speed_10m?: number;
  temperature_2m?: number;
  relative_humidity_2m?: number;
  precipitation?: number;
  surface_pressure?: number;
  cloud_cover?: number;
}
export interface ZoneCollection {
  type: "FeatureCollection";
  features: {
    properties: { name: string; category: string; source_type: SourceType };
    geometry: { type: string; coordinates: number[][] | number[][][] };
  }[];
}
export interface ReplayResponse extends Provenance {
  timestamp: string;
  location_id: string;
  target_source_type: SourceType;
}
export interface ExplainResponse extends Provenance {
  answer: string;
  method: string;
  context: Record<string, unknown>;
  model: string;
  claims: { audience?: "residents" | "municipality" | "general"; kind?: "finding" | "conclusion" | "action" | "limitation"; text: string; source_type: SourceType; evidence_ids: string[] }[];
}
import type { StationSelection } from "./lib/operations";
