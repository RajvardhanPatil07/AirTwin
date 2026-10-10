import { useEffect, useState } from "react";
import { operations, type Plan, type PlanPreference, type ResilienceEvidence } from "../lib/operations";
import { ActionEvidence, PlanChoices, PlanningBaseline, PlanningExplanation } from "./PlanningEvidence";
import { number, timeLabel, dateLabel } from "../lib/format";
import { AssumptionsPanel } from "./AssumptionsPanel";

const money = (value: number) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(value);
export function PlanningPanel({ replayAt, snapshotAt, onPlan, onReplay, onCurrent }: {
  replayAt: string | null; snapshotAt: string; onPlan: (plan: Plan) => void;
  onReplay: (timestamp: string) => void; onCurrent: (current: boolean) => void;
}) {
  const [budget, setBudget] = useState(300000);
  const [loss, setLoss] = useState(0);
  const [withheld, setWithheld] = useState(false);
  const [unavailable, setUnavailable] = useState<string[]>([]);
  const [cost, setCost] = useState(1);
  const [response, setResponse] = useState(1);
  const [preference,setPreference]=useState<PlanPreference>("robust");
  const [storedPlan, setPlan] = useState<Plan | null>(null);
  const plan = storedPlan && storedPlan.replay_at === replayAt &&
    Date.parse(storedPlan.snapshot_at) === Date.parse(snapshotAt) ? storedPlan : null;
  const [evidence, setEvidence] = useState<ResilienceEvidence | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { let active = true; operations.evidence().then(next => active && setEvidence(next)).catch(() => active && setError("Historical resilience evidence could not load.")); return () => { active = false; }; }, []);
  useEffect(() => {
    let active = true;
    setBusy(true); onCurrent(false);
    const timer = window.setTimeout(() => {
      setBusy(true); setError(null);
      operations.plan({ budget, sensor_loss_percent: loss, withheld_location_id: withheld && evidence?.available && replayAt ? evidence.report.withheld_station_id : null,
        unavailable_actions: unavailable, replay_at: replayAt, region: "pcmc", cost_multiplier: cost, response_multiplier: response, target_percent: 12,preference })
        .then(next => { if (active) { setPlan(next); onPlan(next); onCurrent(true); } })
        .catch(() => active && setError("Planning failed. Any retained package is marked outdated and belongs only to the same snapshot; retry by changing a control."))
        .finally(() => active && setBusy(false));
    }, 350);
    return () => { active = false; window.clearTimeout(timer); };
  }, [budget, loss, withheld, unavailable, replayAt, cost, response, evidence, snapshotAt, onPlan, onCurrent,preference]);
  const rows = evidence?.available ? evidence.report.results.filter(r => r.scope === "withheld_location" && r.horizon === 24) : [];
  return <section className="tab-content planning-panel">
    <div className="section-heading"><h2>Budget and sensor resilience</h2><span className="data-badge modeled">MODELED</span></div>
    <p className="helper">Forecast-guided 24-hour packages. Costs and intervention responses are synthetic assumptions.</p>
    <label className="planning-control">Budget <strong>{money(budget)}</strong><input aria-label="Intervention budget" type="range" min="0" max="700000" step="10000" value={budget} onChange={e => setBudget(Number(e.target.value))} /></label>
    <label className="planning-control">Simulated sensor loss <strong>{loss}%</strong><select aria-label="Sensor loss" value={loss} onChange={e => setLoss(Number(e.target.value))}>{[0, 25, 50, 75].map(v => <option key={v} value={v}>{v}%</option>)}</select></label>
    <label className="planning-control">Cost multiplier <strong>{cost.toFixed(2)}×</strong><input aria-label="Intervention cost multiplier" type="range" min="0.5" max="2" step="0.1" value={cost} onChange={e => setCost(Number(e.target.value))} /></label>
    <label className="planning-control">Response multiplier <strong>{response.toFixed(2)}×</strong><input aria-label="Intervention response multiplier" type="range" min="0.2" max="2" step="0.1" value={response} onChange={e => setResponse(Number(e.target.value))} /></label>
    {evidence?.available && <div className="resilience-replay"><p>Withheld monitor: {evidence.withheld_name}. Excluded from model fitting, calibration and development neighbor inputs.</p>
      {evidence.replay_at && <button className="status-chip" onClick={() => evidence.replay_at && onReplay(evidence.replay_at)}>Load evaluated sensor replay</button>}
      <label><input type="checkbox" disabled={!replayAt} checked={withheld} onChange={e => setWithheld(e.target.checked)} /> Withhold this monitor from replay inputs</label></div>}
    <p role="status">{busy ? "Recomputing forecasts and feasible packages…" : error ?? "Results match the displayed controls."}</p>
    {plan && <>
      <PlanningBaseline plan={plan}/>
      <p className="helper">{plan.baseline_kind === "forecast" ? "Forecast valid" : "Snapshot at"} {dateLabel(plan.forecast_valid_at)} · {timeLabel(plan.forecast_valid_at)} IST. {plan.forecast.method}; {plan.forecast.available_sensors}/{plan.forecast.total_sensors} observed PM2.5 inputs available.</p>
      {plan.forecast.fallback_reason && <p className="api-warning">{plan.forecast.fallback_reason} Forecast uncertainty is unavailable; package stability cannot be established from forecast uncertainty.</p>}
      <fieldset><legend>Unavailable actions</legend>{plan.catalog.actions.map(a => <label className="action-availability" key={a.id}><input type="checkbox" checked={unavailable.includes(a.id)} onChange={e => setUnavailable(prev => e.target.checked ? [...prev, a.id] : prev.filter(id => id !== a.id))} />{a.name}</label>)}</fieldset>
      <h3>Preferred feasible package</h3>
      <p>{plan.selected.actions.map(a => a.name).join(" + ") || "No action"}</p>
      <div className="planning-metrics"><div><span>Expenditure</span><strong>{money(plan.selected.cost)}</strong></div><div><span>Modeled reduction</span><strong>{number(plan.selected.reduction_percent, 2)}%</strong></div><div><span>Remaining</span><strong>{money(plan.selected.budget_remaining)}</strong></div></div>
      <p className="helper">{plan.objective}</p>
      <PlanChoices plan={plan} onPreference={setPreference}/>
      <PlanningExplanation plan={plan}/>
      <ActionEvidence plan={plan}/>
      <p>{plan.feasible_count} feasible packages; {plan.rejected_count} rejected.</p>
      <p className="api-warning">{plan.target_feasible ? "12% target is feasible under the declared assumptions." : `12% target is infeasible. Maximum feasible modeled reduction: ${number(plan.maximum_feasible_reduction_percent, 2)}%.`}</p>
      {plan.heldout_result && <p className="api-warning">Withheld {plan.heldout_result.name}: MODELED 24-hour PM2.5 {number(plan.heldout_result.predicted, 2)} µg/m³, band {number(plan.heldout_result.p10, 2)}–{number(plan.heldout_result.p90, 2)}. OBSERVED held-out target {plan.heldout_result.actual === null ? "unavailable" : `${number(plan.heldout_result.actual, 2)} µg/m³`} at {dateLabel(plan.heldout_result.valid_at)} {timeLabel(plan.heldout_result.valid_at)} IST. The target never enters predictors.</p>}
      {plan.stability.status === "unstable" && <p className="api-warning">Recommendation is unstable across the declared forecast and response stress cases.</p>}
      <p>Preferred package retained in {number(plan.stability.same_package_fraction * 100, 0)}% of {plan.stability.stress_cases} declared stress cases. {plan.stability.forecast_uncertainty_used ? "Forecast bands and response uncertainty used." : "Response sensitivity only; forecast uncertainty unavailable."}</p>
      <p>Costs +20%: {plan.cost_sensitivity.changed ? "package changes" : "package unchanged"}; expenditure {money(plan.cost_sensitivity.expenditure)}; {plan.cost_sensitivity.feasible_count} feasible packages.</p>
      <div className="planning-table"><table><caption>Feasible alternatives · modeled</caption><thead><tr><th>Actions</th><th>Spend</th><th>Reduction</th></tr></thead><tbody>{plan.alternatives.map(p => <tr key={p.id}><td>{p.actions.map(a => a.name).join(" + ") || "No action"}</td><td>{money(p.cost)}</td><td>{number(p.reduction_percent, 2)}%</td></tr>)}</tbody></table></div>
      <details><summary>Rejected package and violated constraints</summary><p>Package containing all eight actions</p><ul>{plan.rejected_package.violations.map(v => <li key={v}>{v}</li>)}</ul></details>
      <button className="status-chip" onClick={() => { const blob = new Blob([JSON.stringify(plan, null, 2)], { type: "application/json" }); const url = URL.createObjectURL(blob); const a = document.createElement("a"); a.href = url; a.download = "airtwin-plan.json"; a.click(); URL.revokeObjectURL(url); }}>Export package evidence</button>
      <AssumptionsPanel assumptions={plan.assumptions} title="Planning assumptions" />
    </>}
    {rows.length > 0 && <div className="planning-table"><table><caption>24-hour withheld-monitor historical test · µg/m³</caption><thead><tr><th>Loss</th><th>Pairs</th><th>Model MAE</th><th>IDW MAE</th><th>Persistence MAE</th><th>Coverage</th><th>Band width</th></tr></thead><tbody>{rows.map(r => <tr key={r.loss_percent}><td>{r.loss_percent}%</td><td>{r.samples}</td><td>{number(r.mae, 2)}</td><td>{number(r.idw_mae, 2)}</td><td>{number(r.persistence_mae, 2)}</td><td>{number(r.coverage_percent, 1)}%</td><td>{number(r.mean_interval_width, 1)}</td></tr>)}</tbody></table><p className="helper">Persistence comparisons, interval widths, dates and exact splits are in the evidence report. High coverage can reflect wide intervals.</p></div>}
  </section>;
}
