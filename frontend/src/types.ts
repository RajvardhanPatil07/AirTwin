export type SourceType = "observed" | "modeled" | "synthetic";
export interface Provenance {
  source_type: SourceType;
  assumptions: string[];
}
export interface Station extends Provenance {
  id: string;
  name: string;
  short_name: string;
  latitude: number;
  longitude: number;
  pm25: number;
  timestamp: string;
}
export interface Cell extends Provenance {
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
  population_source_type: SourceType;
  cells: Cell[];
}
export interface ScenarioResponse extends Provenance {
  scenario_id: string;
  location_id: string;
  results: ScenarioResult[];
}
export interface StationsResponse extends Provenance {
  stations: Station[];
  warnings?: string[];
  data_mode?: string;
  weather?: Weather;
  zones?: ZoneCollection;
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
  location_id: string;
  history_source_type: SourceType;
  history_reference?: string;
  shap?: ShapExplanation;
  weather_forecast?: Weather[];
  series: SeriesPoint[];
}
export interface Metrics {
  mae: number;
  rmse: number;
  r2: number;
  persistence_mae: number;
  improvement_percent: number;
  interval_coverage: number;
}
export interface BacktestResponse extends Provenance {
  location_id: string;
  target_source_type: SourceType;
  method: string;
  seasonal_baseline?: Record<string, number>;
  cv?: Record<string, number | string>[];
  series: SeriesPoint[];
  metrics: Metrics;
}
export interface AttributionResponse extends Provenance {
  location_id: string;
  background: number;
  shares: { name: string; value: number; color: string }[];
}
export interface DashboardData {
  stations: Station[];
  cells: Cell[];
  demo: boolean;
  warning: string | null;
  weather?: Weather;
  zones?: ZoneCollection;
}

export interface ShapExplanation {
  groups: Record<string, number>;
  base_value: number;
  prediction: number;
  method: string;
}
export interface Weather {
  source_type: SourceType;
  timestamp: string;
  wind_direction_10m?: number;
  wind_speed_10m?: number;
  temperature_2m?: number;
  relative_humidity_2m?: number;
  precipitation?: number;
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
}
