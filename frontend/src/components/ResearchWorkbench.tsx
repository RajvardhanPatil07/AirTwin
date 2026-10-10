import { useEffect, useRef, useState } from "react";
import { Activity, ArrowRight, ChevronDown, Factory, Gauge, Info, Leaf, ShieldAlert, TrendingDown, Truck } from "lucide-react";
import type { AttributionResponse, BacktestResponse, Cuts, ScenarioResponse, Station } from "../types";
import type { Plan } from "../lib/operations";
import { operations } from "../lib/operations";
import { api } from "../lib/api";
import { number } from "../lib/format";

type Mode = "scenarios" | "sources" | "validation" | "planner";
const DEFAULT_CUTS: Cuts = { traffic: 20, industry: 30, dust: 30 };
const CONTROLS = [
  { key: "traffic", title: "Traffic restrictions", max: 50, Icon: Truck },
  { key: "industry", title: "Industrial controls", max: 60, Icon: Factory },
  { key: "dust", title: "Dust suppression", max: 70, Icon: Leaf },
] as const;

export function ResearchWorkbench({ selected, demo }: { selected: Station | null; demo: boolean }) {
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<Mode>("scenarios");
  const [cuts, setCuts] = useState<Cuts>(DEFAULT_CUTS);
  const [scenario, setScenario] = useState<ScenarioResponse | null>(null);
  const [attribution, setAttribution] = useState<AttributionResponse | null>(null);
  const [backtest, setBacktest] = useState<BacktestResponse | null>(null);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [budget, setBudget] = useState(300000);
  const [target, setTarget] = useState(12);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const version = useRef(0);

  useEffect(() => {
    version.current += 1;
    setScenario(null);
    setAttribution(null);
    setBacktest(null);
    setPlan(null);
    setError("");
    setLoading(false);
  }, [selected?.id, demo]);

  async function run(next: Mode = mode) {
    if (!selected) return;
    const active = ++version.current;
    setLoading(true);
    setError("");
    try {
      switch (next) {
        case "scenarios": {
          const result = await api.scenarios(selected, cuts, demo);
          if (active === version.current) setScenario(result);
          break;
        }
        case "sources": {
          const result = await api.attribution(selected, demo);
          if (active === version.current) setAttribution(result);
          break;
        }
        case "validation": {
          const result = await api.backtest(selected, demo);
          if (active === version.current) setBacktest(result);
          break;
        }
        case "planner": {
          if (demo) throw new Error("The planner needs the connected backend. Synthetic demonstration data cannot establish an intervention budget.");
          const result = await operations.plan({
            budget, target_percent: target, unavailable_actions: [],
            sensor_loss_percent: 0, withheld_location_id: null,
            replay_at: null, region: "pcmc", cost_multiplier: 1,
            response_multiplier: 1, preference: "robust",
          });
          if (active === version.current) setPlan(result);
          break;
        }
      }
    } catch (exception) {
      if (active === version.current) setError(exception instanceof Error ? exception.message : "Analysis could not be completed");
    } finally {
      if (active === version.current) setLoading(false);
    }
  }
  const selectMode = (next: Mode) => {
    setMode(next);
    setError("");
  };
  const combined = scenario?.results.find((result) => result.id === "combined");
  return <section className="fv-research-shell" aria-label="Evidence and scenario research workbench">
    <button type="button" className="fv-research-toggle" aria-expanded={open} onClick={() => setOpen((v) => !v)}>
      <span><Gauge size={17}/><strong>Research & policy modeling</strong><small>Optional · Detailed evidence and modeled comparisons</small></span>
      <ChevronDown size={18} className={open ? "open" : ""}/>
    </button>
    {open && <div className="fv-research-content">
      <div className="fv-research-header"><span><ShieldAlert size={15}/> Simulation and evidence only — no official controls are executed.</span>
        <span>{demo ? "SYNTHETIC DEMO" : "BACKEND COMPUTED"}</span>
      </div>
      <div className="fv-research-tabs" role="tablist" aria-label="Research analysis">
        {([
          ["scenarios", "What-if actions"],
          ["sources", "Source proxies"],
          ["validation", "Historical validation"],
          ["planner", "Budget planning"],
        ] as const).map(([key, label]) =>
          <button role="tab" aria-selected={mode === key} type="button" key={key} className={mode === key ? "active" : ""} onClick={() => selectMode(key)}>{label}</button>)}
      </div>
      {mode === "scenarios" && <div className="fv-research-layout">
        <div className="fv-research-editor"><h3>Model interventions for {selected?.short_name ?? "a selected area"}</h3>
          <p>Adjust plausible activity changes. These are assumed responses, not verified causal outcomes.</p>
          {CONTROLS.map(({key,title,max,Icon}) => <label key={key} className="fv-slider-row">
            <span><Icon size={15}/> {title}<b>{cuts[key]}%</b></span>
            <input type="range" min="0" max={max} step="5" value={cuts[key]} onChange={(event) => setCuts((v) => ({...v,[key]:Number(event.target.value)}))}/>
          </label>)}
          <button type="button" className="fv-button fv-primary" disabled={loading || !selected} onClick={() => void run("scenarios")}>
            {loading ? "Calculating…" : "Compare modeled actions"} <ArrowRight size={16}/>
          </button>
        </div>
        <div className="fv-research-results">
          {combined ? <>
            <div className="fv-research-figure"><span>Combined modeled intervention</span>
              <strong>{number(combined.before)} <small>→</small> {number(combined.after)} <small>µg/m³</small></strong>
              <p>Reduction: {number(combined.reduction)} µg/m³ · {number(combined.reduction_percent)}%</p>
            </div>
            <div className="fv-research-actions">{scenario?.results.map((row) => <div key={row.id}>
              <span>{row.name}<small>{row.source_type.toUpperCase()}</small></span>
              <strong>−{number(row.reduction)} µg/m³</strong>
            </div>)}</div>
            <div className="fv-research-disclaimer"><Info size={14}/> {scenario?.assumptions?.slice(0, 2).join(" ")}</div>
          </> : <div className="fv-research-empty">Run the model to compare traffic, industry, dust, and combined modeled reductions.</div>}
        </div>
      </div>}
      {mode === "sources" && <div className="fv-research-layout"><div className="fv-research-editor">
        <h3>Source contribution estimates</h3><p>These are assumptions from spatial and activity proxies, not chemical source apportionment or SHAP explanations.</p>
        <button type="button" className="fv-button fv-primary" disabled={loading || !selected} onClick={() => void run("sources")}>{loading ? "Calculating…" : "Load source assumptions"}</button>
      </div><div className="fv-research-results">
        {attribution ? <>
          <p className="fv-provenance">MODELED · {attribution.status ?? "estimated"}</p>
          {attribution.shares.map((share) => <div className="fv-source-bar" key={share.name}>
            <div><span>{share.name}</span><strong>{number(share.value * 100)}%</strong></div>
            <div className="fv-source-track"><i style={{width: Math.max(0,Math.min(100,share.value * 100))+"%", background:share.color}}/></div>
          </div>)}
          <small>{attribution.status_reason ?? attribution.assumptions.slice(0, 2).join(" ")}</small>
        </> : <div className="fv-research-empty">Inspect the three activity proxies and regional background. No measured causal source attribution is claimed.</div>}
      </div></div>}
      {mode === "validation" && <div className="fv-research-layout"><div className="fv-research-editor">
        <h3>Historical forecast validation</h3>
        <p>Held-out predictions compared with past reference targets and the persistence baseline. This does not validate today's provider forecast.</p>
        <button type="button" className="fv-button fv-primary" disabled={loading || !selected} onClick={() => void run("validation")}>{loading ? "Checking…" : "Load historical backtest"}</button>
      </div><div className="fv-research-results">{backtest ? backtest.metrics ? <>
        <div className="fv-research-figure"><span>Held-out MAE · {backtest.target_source_type.toUpperCase()} target</span>
          <strong>{number(backtest.metrics.mae)} <small>µg/m³</small></strong>
          <p>Persistence: {number(backtest.metrics.persistence_mae)} µg/m³</p>
        </div>
        <p className={backtest.metrics.improvement_percent < 0 ? "fv-inline-warning" : "fv-research-verified"}>
          {backtest.metrics.improvement_percent > 0 ? "Improvement" : "Difference"} vs persistence: {number(backtest.metrics.improvement_percent)}%
        </p>
        <small>{backtest.method} · {backtest.assumptions.slice(0, 2).join(" ")}</small>
      </> : <div className="fv-research-empty">No validated historical test is available for this location. Do not infer forecast skill from the live map.</div> : <div className="fv-research-empty">Backtesting requires a historical test set, not a live pollution snapshot.</div>}</div></div>}
      {mode === "planner" && <div className="fv-research-layout"><div className="fv-research-editor">
        <h3>Assumption-based intervention budget</h3><p>Find a possible mix of modeled actions under a hypothetical INR budget. Costs and effectiveness require municipal verification.</p>
        <label className="fv-field-label">Budget (₹)<input type="number" min="0" max="10000000" step="10000" value={budget} onChange={(event) => setBudget(Math.max(0, Math.min(10000000, Number(event.target.value) || 0)))}/></label>
        <label className="fv-field-label">Target modeled reduction (%)<input type="number" min="0" max="100" step="1" value={target} onChange={(event) => setTarget(Math.max(0,Math.min(100,Number(event.target.value) || 0)))}/></label>
        <button type="button" className="fv-button fv-primary" disabled={loading || demo} onClick={() => void run("planner")}>{loading ? "Solving…" : "Compute suggested package"}</button>
      </div><div className="fv-research-results">{plan ? <>
        <div className="fv-research-figure"><span>Selected hypothetical plan · {plan.baseline_kind}</span>
          <strong>{number(plan.selected.reduction_percent)}% <small>modeled reduction</small></strong>
          <p>Assumed cost ₹{number(plan.selected.cost, 0)} · Budget ₹{number(plan.budget, 0)}</p>
        </div>
        <div className="fv-research-actions">{plan.selected.actions.map((action) =>
          <div key={action.id}><span>{action.name}<small>{action.category}</small></span><strong>₹{number(action.cost,0)}</strong></div>)}</div>
        <small>Target {plan.target_feasible ? "feasible under model assumptions" : "not feasible under model assumptions"} · {plan.coverage.coverage_note}. {plan.assumptions.slice(0,2).join(" ")}</small>
      </> : <div className="fv-research-empty">{demo ? "The real planning API is unavailable in synthetic demo mode." : "Request an optimization against the live backend's action catalog and evidence constraints."}</div>}</div></div>}
      {error && <p role="alert" className="fv-inline-warning">Could not complete analysis: {error}</p>}
      <div className="fv-research-bottom"><Activity size={14}/> Forecast modeling, proxy attribution, and policy scenario assumptions are distinct kinds of evidence. No automatic city operations are performed.</div>
    </div>}
  </section>;
}
