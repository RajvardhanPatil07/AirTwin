import { z } from "zod";

const source = z.enum(["observed", "modeled", "synthetic"]);
const cell = z.object({
  id: z.string(), latitude: z.number(), longitude: z.number(),
  bounds: z.tuple([z.tuple([z.number(), z.number()]), z.tuple([z.number(), z.number()])]),
  pm25: z.number(), background: z.number(), population: z.number(),
  population_source_type: source, source_type: source, assumptions: z.array(z.string()),
  local_weights: z.object({ traffic: z.number(), industry: z.number(), dust: z.number() }),
  p10: z.number().nullable().optional(), p90: z.number().nullable().optional(),
});
const evidenceSource = z.object({id:z.string(),title:z.string(),url:z.string().url(),year:z.number(),supports:z.string()});
const action = z.object({ id: z.string(), name: z.string(), category: z.enum(["traffic", "industry", "dust"]), cost: z.number(), radius_km: z.number(), cut_percent: z.number(),
  duration_hours:z.number(), implementation_limits:z.array(z.string()), source_ids:z.array(z.string()),
  coverage:z.object({implementation_scope:z.string()}),
  cost_evidence:z.object({status:z.string(),documented_unit_cost_inr:z.number().nullable(),derivation:z.string(),unit:z.string()}),
  response_range_percent:z.object({low:z.number(),central:z.number(),high:z.number()}),
  response_evidence:z.object({status:z.string(),observed_causal_effect_available:z.boolean(),reason:z.string()}) });
const pkg = z.object({ id: z.string(), actions: z.array(action), cost: z.number(), benefit: z.number(), worst_case_benefit: z.number(), benefit_low: z.number(), benefit_high: z.number(), reduction_percent: z.number(), budget_remaining: z.number(), affected_areas: z.array(z.string()),response_envelope_low_percent:z.number(),response_envelope_high_percent:z.number() });
export const preferenceSchema=z.enum(["robust","max_benefit","min_cost"]);
export type PlanPreference=z.infer<typeof preferenceSchema>;
export const stationSelectionSchema=z.object({selected_method:z.string(),selection_model_mae:z.number(),selection_persistence_mae:z.number(),test_model_mae:z.number(),test_persistence_mae:z.number(),fit_rows:z.number(),selection_rows:z.number(),test_rows:z.number(),fit_target_end:z.string(),selection_issue_start:z.string(),selection_target_end:z.string(),test_issue_start:z.string(),test_target_end:z.string(),reason:z.string(),seasonal_comparisons:z.array(z.object({season:z.string(),samples:z.number(),lightgbm_mae:z.number(),persistence_mae:z.number(),selected_mae:z.number()}))});
export type StationSelection=z.infer<typeof stationSelectionSchema>;
const coverageSchema=z.object({mode:z.enum(["historical_replay","live_provider","cached_historical","synthetic_demo"]),checked_at:z.string(),snapshot_at:z.string(),fresh_monitor_count:z.number(),observed_monitor_count:z.number(),discovered_monitor_count:z.number(),modeled_point_count:z.number(),warnings:z.array(z.string()),freshness_rule:z.string(),coverage_note:z.string(),monitors:z.array(z.object({id:z.string(),name:z.string(),pm25:z.number(),timestamp:z.string(),age_hours:z.number(),age_at_issue_hours:z.number(),eligible:z.boolean(),status:z.string()}))});
export const planSchema = z.object({
  source_type: source, assumptions: z.array(z.string()), budget: z.number(),
  catalog: z.object({ actions: z.array(action), assumption_source_type: z.literal("synthetic"),evidence_sources:z.array(evidenceSource) }),
  selected: pkg, alternatives: z.array(pkg), feasible_count: z.number(), rejected_count: z.number(),
  rejected_package: z.object({ action_ids: z.array(z.string()), violations: z.array(z.string()) }),
  cells_before: z.array(cell), cells_after: z.array(cell), target_percent: z.number(), target_feasible: z.boolean(), maximum_feasible_reduction_percent: z.number(),
  baseline_kind: z.enum(["forecast", "snapshot"]),
  forecast_valid_at: z.string(), snapshot_at: z.string(), replay_at: z.string().nullable(),
  objective: z.string(),
  coverage:coverageSchema,preference:preferenceSchema,selected_reason:z.string(),
  recommendations:z.array(z.object({kind:preferenceSchema,label:z.string(),package:pkg.nullable(),reason:z.string()})),
  explanation:z.object({background_share_percent:z.number(),local_excess_share_percent:z.number(),weighted_baseline_pm25:z.number(),available_actions_maximum_percent:z.number(),minimum_budget_for_target:z.number().nullable(),target_gap_percent:z.number(),unavailable_action_count:z.number(),limiting_reason:z.enum(["target_met","budget","action_scope_and_background"]),category_reductions:z.array(z.object({category:z.string(),reduction_percent:z.number()})),notes:z.array(z.string())}),
  heldout_result: z.object({ name: z.string(), predicted: z.number(), p10: z.number(), p90: z.number(), actual: z.number().nullable(), valid_at: z.string() }).nullable(),
  stability: z.object({ same_package_fraction: z.number(), stress_cases: z.number(), forecast_uncertainty_used: z.boolean(), status: z.string() }),
  cost_sensitivity: z.object({ cost_increase_percent: z.number(), feasible_count: z.number(), changed: z.boolean(), expenditure: z.number(), selected_package_id: z.string() }),
  forecast: z.object({ available_sensors: z.number(), total_sensors: z.number(), masked_sensor_ids: z.array(z.string()), withheld_location_id: z.string().nullable(), method: z.string(), uncertainty_kind: z.string(), fallback_reason: z.string().nullable(), issued_at: z.string(), input_cutoff: z.string(),selection_evidence:z.array(z.object({horizon:z.number(),loss_percent:z.number(),selected_method:z.string(),model_mae:z.number(),spatial_persistence_mae:z.number(),samples:z.number()})) }),
});
const feedSchema = z.object({
  source_type: z.literal("observed"), assumptions: z.array(z.string()), checked_at: z.string().nullable(), fresh_count: z.number(),
  records: z.array(z.object({ id: z.string(), name: z.string(), indicator: z.literal("AQI"), value: z.number(), timestamp: z.string(), received_at: z.string(), status: z.enum(["fresh", "delayed", "stale"]), age_hours: z.number(), source_url: z.string() })),
});
const evidenceSchema = z.discriminatedUnion("available", [
  z.object({ available: z.literal(false), assumptions: z.array(z.string()) }),
  z.object({ available: z.literal(true), assumptions: z.array(z.string()), replay_at: z.string().nullable(), withheld_name: z.string(), report: z.object({ withheld_station_id: z.string(), test_issue_start: z.string(), target_source_types: z.array(source), results: z.array(z.object({ scope: z.string(), horizon: z.number(), loss_percent: z.number(), samples: z.number(), mae: z.number(), idw_mae: z.number(), persistence_mae: z.number(), coverage_percent: z.number(), mean_interval_width: z.number() })),station_season_results:z.array(z.object({station_id:z.string(),season:z.string(),horizon:z.number(),loss_percent:z.number(),samples:z.number(),selected_method:z.string(),selected_mae:z.number(),lightgbm_mae:z.number(),spatial_persistence_mae:z.number()})) }) }),
]);
export type Plan = z.infer<typeof planSchema>;
export type Feed = z.infer<typeof feedSchema>;
export type ResilienceEvidence = z.infer<typeof evidenceSchema>;
export interface PlanInput {
  budget: number; unavailable_actions: string[]; sensor_loss_percent: number;
  withheld_location_id: string | null; replay_at: string | null; region: "pcmc";
  cost_multiplier: number; response_multiplier: number; target_percent: number;
  preference?: PlanPreference;
}
const base = (import.meta.env.VITE_API_BASE_URL ?? "/backend").replace(/\/$/, "");
async function read(path: string, body?: PlanInput): Promise<unknown> {
  const response = await fetch(`${base}/api/${path}`, {
    method: body ? "POST" : "GET", headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined, signal: AbortSignal.timeout(60000),
  });
  if (!response.ok) {
    const error: unknown=await response.json().catch(()=>null);
    const parsed=z.object({detail:z.string()}).safeParse(error);
    throw new Error(parsed.success ? parsed.data.detail : `Service returned ${response.status}`);
  }
  return response.json();
}
export const operations = {
  feed: async () => feedSchema.parse(await read("feed")),
  evidence: async () => evidenceSchema.parse(await read("resilience/evidence")),
  plan: async (input: PlanInput) => planSchema.parse(await read("plans", input)),
};
