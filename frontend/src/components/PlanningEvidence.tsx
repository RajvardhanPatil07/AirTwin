import type { Plan, PlanPreference, ResilienceEvidence } from "../lib/operations";

const money=(value:number)=>new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",maximumFractionDigits:0}).format(value);
const stamp=(value:string)=>new Date(value).toLocaleString("en-IN",{timeZone:"Asia/Kolkata"});
const percent=(value:number)=>value>0&&value<.001 ? "<0.001" : value.toFixed(3);

export function PlanningBaseline({plan}:{plan:Plan}) {
  const c=plan.coverage;
  const labels={live_provider:"Current provider context",historical_replay:"Historical replay",cached_historical:"Dated historical cache",synthetic_demo:"Synthetic demonstration"};
  return <div>
    <h3>Planning baseline</h3>
    <p><b>{labels[c.mode]}</b> · {plan.forecast.method}</p>
    <p>{c.fresh_monitor_count} eligible observed PM2.5 monitors · {c.modeled_point_count} modeled reference points. {c.discovered_monitor_count} sensors discovered.</p>
    <p>{plan.forecast.available_sensors} observed monitors used by the spatial forecaster. {plan.forecast.masked_sensor_ids.length} withheld or masked.</p>
    <p>Input cutoff {stamp(plan.forecast.input_cutoff)} IST. {plan.baseline_kind==="forecast" ? "Forecast valid" : "Snapshot at"} {stamp(plan.forecast_valid_at)} IST.</p>
    {c.mode==="cached_historical" && <p className="api-warning">These observations are historical. Use replay for a dated demonstration; this is not a current city forecast.</p>}
    {c.monitors.length>0 ? <details><summary>Observed monitor ages and coverage</summary>
      <ul>{c.monitors.map(m=><li key={m.id}>{m.name}: {m.pm25.toFixed(2)} µg/m³ · {stamp(m.timestamp)} IST · {c.mode==="historical_replay" || c.mode==="cached_historical" ? `${m.age_at_issue_hours.toFixed(1)} hours old at the historical issue` : `${m.age_hours.toFixed(1)} hours old`} · {m.status}</li>)}</ul>
    </details> : <p>No observed PM2.5 readings are eligible in this snapshot. CAMS is modeled context; AQI indices cannot replace concentration measurements.</p>}
    <details><summary>Coverage limits and provider status</summary><p>{c.freshness_rule}</p><p>{c.coverage_note}</p>{c.warnings.map(w=><p key={w}>{w}</p>)}</details>
    {plan.forecast.selection_evidence.filter(r=>r.loss_percent===0).map(r=><p key={r.horizon}>Earlier validation selected {r.selected_method}: model MAE {r.model_mae.toFixed(2)}, spatial persistence MAE {r.spatial_persistence_mae.toFixed(2)} µg/m³ on {r.samples} pairs. Later test performance is separate.</p>)}
    {plan.heldout_result && <p>Withheld {plan.heldout_result.name}: predicted {plan.heldout_result.predicted.toFixed(2)} µg/m³ at {stamp(plan.heldout_result.valid_at)} IST; observed target {plan.heldout_result.actual===null ? "unavailable" : `${plan.heldout_result.actual.toFixed(2)} µg/m³`}. This target is excluded from the predictors.</p>}
  </div>;
}

export function PlanChoices({plan,onPreference}:{plan:Plan;onPreference:(preference:PlanPreference)=>void}) {
  const activePreference=plan.preference==="min_cost"&&!plan.target_feasible ? "robust" : plan.preference;
  return <div><h3>Compare feasible choices</h3>
    {plan.recommendations.map(r=><div key={r.kind}>
      <button className="status-chip" aria-pressed={activePreference===r.kind} disabled={r.package===null} onClick={()=>onPreference(r.kind)}>{r.label}</button>
      {r.package ? <p>{money(r.package.cost)} · {percent(r.package.reduction_percent)}% central reduction · {r.package.affected_areas.join(", ") || "No action"}</p> : <p>No package meets the target within this budget.</p>}
    </div>)}
    <p>{plan.selected_reason}</p>
    <p>Selected response envelope {percent(plan.selected.response_envelope_low_percent)}–{percent(plan.selected.response_envelope_high_percent)}%. This assumed range includes failed implementation; it is not a confidence interval.</p>
    <p>Conditional operation: {plan.selected.benefit_low.toFixed(0)}–{plan.selected.benefit_high.toFixed(0)} person·µg/m³ across {plan.stability.stress_cases} stress cases. {plan.stability.forecast_uncertainty_used ? "Forecast bands included." : "Forecast uncertainty unavailable."}</p>
    <p>Costs +20%: {plan.cost_sensitivity.changed ? "package changes" : "package retained"}; {money(plan.cost_sensitivity.expenditure)} expenditure.</p>
  </div>;
}

export function PlanningExplanation({plan}:{plan:Plan}) {
  const e=plan.explanation;
  return <div><h3>Why this reduction?</h3>
    <p>Population-weighted baseline {e.weighted_baseline_pm25.toFixed(2)} µg/m³. Assumed background accounts for {e.background_share_percent.toFixed(1)}%; local excess accounts for {e.local_excess_share_percent.toFixed(1)}%.</p>
    <p>Available actions can achieve at most {percent(plan.maximum_feasible_reduction_percent)}% within this budget, or {percent(e.available_actions_maximum_percent)}% with the budget limit removed. Operational limits remain.</p>
    {e.limiting_reason==="budget" && e.minimum_budget_for_target!==null ? <p>The target requires at least {money(e.minimum_budget_for_target)} under the current central assumptions.</p> : e.limiting_reason==="action_scope_and_background" ? <p>More budget alone cannot reach {plan.target_percent}%. Background, action reach, assumed source shares and operational limits constrain the available actions.</p> : <p>The central target is feasible. It is not guaranteed in every stress case.</p>}
    <p>{e.unavailable_action_count} actions unavailable. Gap to target {percent(e.target_gap_percent)} percentage points.</p>
    <details><summary>Source contributions and spatial limits</summary>
      {e.category_reductions.map(r=><p key={r.category}>{r.category}: {percent(r.reduction_percent)} percentage points of the selected city-grid reduction.</p>)}
      {e.notes.map(note=><p key={note}>{note}</p>)}
    </details>
  </div>;
}

export function SpatialForecastEvidence({evidence}:{evidence:ResilienceEvidence}) {
  if(!evidence.available) return <p>{evidence.assumptions.join(" ")}</p>;
  const rows=evidence.report.station_season_results.filter(r=>r.horizon===24&&r.loss_percent===0);
  return <section className="at-panel"><h3>Historical spatial forecast evidence</h3>
    <p>Observed-target 24-hour test by monitor and represented season. Withheld monitor {evidence.withheld_name} is excluded from fitting and selection. Test issues start {stamp(evidence.report.test_issue_start)} IST.</p>
    <p>LightGBM or spatial persistence is selected using an earlier period. These later results measure that choice; missing seasons are unvalidated. This does not validate the current CAMS forecast or intervention effects.</p>
    <div className="planning-table"><table><caption>No simulated sensor loss · MAE in µg/m³</caption><thead><tr><th>Monitor</th><th>Season</th><th>Pairs</th><th>Selected</th><th>LightGBM MAE</th><th>Spatial persistence MAE</th><th>Selected MAE</th></tr></thead><tbody>{rows.map(r=><tr key={`${r.station_id}-${r.season}`}><td>{r.station_id}</td><td>{r.season.replaceAll("_"," ")}</td><td>{r.samples}</td><td>{r.selected_method}</td><td>{r.lightgbm_mae.toFixed(2)}</td><td>{r.spatial_persistence_mae.toFixed(2)}</td><td>{r.selected_mae.toFixed(2)}</td></tr>)}</tbody></table></div>
  </section>;
}

export function ActionEvidence({plan}:{plan:Plan}) {
  return <details><summary>Action costs, response ranges and sources</summary>
    <p>Comparable local operating prices are unverified. These scenario amounts do not constitute procurement estimates. A policy citation supports context, not the numerical cost or causal effect.</p>
    {plan.catalog.actions.map(a=><details key={a.id}><summary>{a.name} · {money(a.cost)} scenario cost</summary>
      <p>{a.duration_hours}-hour scenario horizon · assumed {a.radius_km} km distance-decay radius. This is not a measured service area or effect lifetime.</p>
      <p>{a.coverage.implementation_scope}</p><p>{a.cost_evidence.derivation}</p>
      <p>Assumed local {a.category} source cut {a.response_range_percent.low}–{a.response_range_percent.high}% · central {a.response_range_percent.central}%. {a.response_evidence.reason}</p>
      <ul>{a.implementation_limits.map(limit=><li key={limit}>{limit}</li>)}</ul>
      {a.source_ids.map(id=>{const source=plan.catalog.evidence_sources.find(s=>s.id===id);return source ? <p key={id}><a href={source.url} target="_blank" rel="noreferrer">{source.title} ({source.year})</a>. {source.supports}</p> : null;})}
    </details>)}
  </details>;
}
