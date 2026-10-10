import { useCallback, useEffect, useRef, useState } from "react";
import { Send, Sparkles } from "lucide-react";
import { api } from "../lib/api";
import { operations, type Plan } from "../lib/operations";
import { ForecastChart, BacktestChart, AttributionChart } from "./Charts";
import { AssumptionsPanel } from "./AssumptionsPanel";
import type { Cuts, DashboardData, ExplainResponse, Station } from "../types";
import { AirMap } from "./GuidedAirMap";

function useRemote<T>(load: () => Promise<T>, delay = 0) {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<{
    data: T | null;
    error: string | null;
    busy: boolean;
  }>({ data: null, error: null, busy: true });
  useEffect(() => {
    let current = true;
    setState({ data: null, error: null, busy: true });
    const timer = window.setTimeout(
      () =>
        load()
          .then(
            (data) => current && setState({ data, error: null, busy: false }),
          )
          .catch(
            (error) =>
              current &&
              setState({
                data: null,
                error:
                  error instanceof Error ? error.message : "Request failed",
                busy: false,
              }),
          ),
      delay,
    );
    return () => {
      current = false;
      window.clearTimeout(timer);
    };
  }, [load, attempt, delay]);
  return { ...state, retry: () => setAttempt((value) => value + 1) };
}
const stamp = (value: string) =>
  new Date(value).toLocaleString("en-IN", { timeZone: "Asia/Kolkata" });
const money = (value: number) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
function RequestStatus({
  busy,
  error,
  retry,
}: {
  busy: boolean;
  error: string | null;
  retry?: () => void;
}) {
  return busy || error ? (
    <p role="status" className={error ? "api-warning" : "helper"}>
      {busy ? "Loading backend results…" : error}
      {error && retry && (
        <button className="at-text-button" onClick={retry}>
          Retry
        </button>
      )}
    </p>
  ) : null;
}
function GuidedChat({
  location,
  cuts,
  hours,
}: {
  location: Station;
  cuts: Cuts;
  hours: number;
}) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<ExplainResponse | null>(null);
  const [history, setHistory] = useState<{ role: string; content: string }[]>(
    [],
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const version = useRef(0);
  useEffect(() => {
    version.current += 1;
    setAnswer(null);
    setHistory([]);
    setBusy(false);
    setError(null);
    return () => {
      version.current += 1;
    };
  }, [location.id, cuts.traffic, cuts.industry, cuts.dust, hours]);
  return (
    <section className="at-panel at-chat">
      <h3>
        <Sparkles size={19} /> Ask AirTwin <span>Connected assistant</span>
      </h3>
      <p>
        Ask about {location.short_name}, the {hours}-hour outlook, or your
        selected action reductions. Answers cite backend evidence.
      </p>
      <form
        onSubmit={async (event) => {
          event.preventDefault();
          const text = question.trim();
          if (!text || busy) return;
          const request = ++version.current;
          setBusy(true);
          setError(null);
          setAnswer(null);
          try {
            const result = await api.explain(
              location.id,
              text,
              null,
              "pcmc",
              cuts,
              hours,
              history.slice(-8),
            );
            if (request !== version.current) return;
            setAnswer(result);
            setQuestion("");
            setHistory((previous) =>
              [
                ...previous,
                { role: "user", content: text },
                { role: "assistant", content: result.answer },
              ].slice(-8),
            );
          } catch (failure) {
            if (request === version.current)
              setError(
                failure instanceof Error
                  ? failure.message
                  : "Assistant request failed",
              );
          } finally {
            if (request === version.current) setBusy(false);
          }
        }}
      >
        <input
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          maxLength={1000}
          aria-label="Ask AirTwin"
          placeholder="What does this estimate mean?"
          disabled={busy}
        />
        <button aria-label="Send question" disabled={busy || !question.trim()}>
          <Send size={17} />
        </button>
      </form>
      <RequestStatus busy={busy} error={error} />
      {answer && (
        <div className="at-chat-answer" role="status">
          <b>
            {answer.method === "gemini_evidence_checked"
              ? `Gemini · ${answer.model}`
              : "Evidence summary · AI service unavailable"}
          </b>
          <p style={{ whiteSpace: "pre-wrap" }}>{answer.answer}</p>
          {answer.claims.map((claim, index) => (
            <small className="at-evidence-citation" key={index}>
              {claim.source_type.toUpperCase()} ·{" "}
              {claim.evidence_ids.join(", ")}
            </small>
          ))}
          <AssumptionsPanel
            title="Answer limitations"
            assumptions={answer.assumptions}
          />
        </div>
      )}
    </section>
  );
}

export interface GuidedPlanControls {
  budget: number;
  target: number;
  unavailable: string[];
}
function GuidedPlan({
  onPlan,
  controls,
  onControls,
  previousPlan,
}: {
  onPlan: (plan: Plan) => void;
  controls: GuidedPlanControls;
  onControls: (controls: GuidedPlanControls) => void;
  previousPlan: Plan | null;
}) {
  const { budget, target, unavailable } = controls;
  const setBudget = (budget: number) => onControls({ ...controls, budget });
  const setTarget = (target: number) => onControls({ ...controls, target });
  const load = useCallback(
    () =>
      operations.plan({
        budget,
        target_percent: target,
        unavailable_actions: unavailable,
        sensor_loss_percent: 0,
        withheld_location_id: null,
        replay_at: null,
        region: "pcmc",
        cost_multiplier: 1,
        response_multiplier: 1,
      }),
    [budget, target, unavailable],
  );
  const result = useRemote(load, 350);
  useEffect(() => {
    if (result.data) onPlan(result.data);
  }, [result.data, onPlan]);
  return (
    <div className="at-two-columns">
      <section className="at-panel">
        <h3>Budget and available actions</h3>
        <p>
          Costs and intervention responses are synthetic assumptions. Packages
          are computed by the backend using its 24-hour forecast.
        </p>
        <label className="planning-control">
          Total budget <strong>{money(budget)}</strong>
          <input
            aria-label="Intervention budget"
            type="range"
            min="0"
            max="700000"
            step="10000"
            value={budget}
            onChange={(event) => setBudget(Number(event.target.value))}
          />
        </label>
        <label className="planning-control">
          Target reduction <strong>{target}%</strong>
          <input
            aria-label="Target reduction"
            type="range"
            min="0"
            max="50"
            value={target}
            onChange={(event) => setTarget(Number(event.target.value))}
          />
        </label>
        {(result.data ?? previousPlan) && (
          <fieldset>
            <legend>Unavailable actions</legend>
            {(result.data ?? previousPlan)!.catalog.actions.map((action) => (
              <label className="action-availability" key={action.id}>
                <input
                  type="checkbox"
                  checked={unavailable.includes(action.id)}
                  onChange={(event) =>
                    onControls({
                      ...controls,
                      unavailable: event.target.checked
                        ? [...unavailable, action.id]
                        : unavailable.filter((id) => id !== action.id),
                    })
                  }
                />{" "}
                {action.name}
              </label>
            ))}
          </fieldset>
        )}
        <RequestStatus {...result} />
      </section>
      <section className="at-panel">
        <h3>Preferred feasible package</h3>
        {result.data && (
          <>
            <p>
              <b>
                {result.data.selected.actions
                  .map((action) => action.name)
                  .join(" + ") || "No action"}
              </b>
            </p>
            <div className="at-big-number">
              {result.data.selected.reduction_percent.toFixed(1)}
              <small>% reduction</small>
            </div>
            <p>
              {money(result.data.selected.cost)} expenditure ·{" "}
              {money(result.data.selected.budget_remaining)} remaining
            </p>
            <p>
              {result.data.target_feasible
                ? "Target feasible under the declared assumptions."
                : `Target infeasible. Maximum feasible modeled reduction: ${result.data.maximum_feasible_reduction_percent.toFixed(1)}%.`}
            </p>
            <p>
              {result.data.feasible_count} feasible packages · Forecast valid{" "}
              {stamp(result.data.forecast_valid_at)} IST
            </p>
            <p>{result.data.forecast.method}</p>
            {result.data.forecast.fallback_reason && (
              <p className="api-warning">
                {result.data.forecast.fallback_reason}
              </p>
            )}
            <AssumptionsPanel
              assumptions={result.data.assumptions}
              title="Planning assumptions"
            />
          </>
        )}
      </section>
    </div>
  );
}

export function GuidedBackendPanels({
  step,
  location,
  dashboard,
  hours,
  onHours,
  actions,
  onActions,
  calculated,
  onCalculate,
  plan,
  onPlan,
  planControls,
  onPlanControls,
}: {
  step: number;
  location: Station;
  dashboard: DashboardData;
  hours: number;
  onHours: (hours: number) => void;
  actions: number[];
  onActions: (actions: number[]) => void;
  calculated: number[];
  onCalculate: () => void;
  plan: Plan | null;
  onPlan: (plan: Plan) => void;
  planControls: GuidedPlanControls;
  onPlanControls: (controls: GuidedPlanControls) => void;
}) {
  const { id } = location;
  const cuts = {
    traffic: calculated[0],
    industry: calculated[1],
    dust: calculated[2],
  };
  const forecastLoad = useCallback(
    () => api.forecast(location, false, hours),
    [id, location, hours],
  );
  const attributionLoad = useCallback(
    () => api.attribution(location, false),
    [id, location],
  );
  const scenarioLoad = useCallback(
    () =>
      api.scenarios(
        location,
        {
          traffic: calculated[0],
          industry: calculated[1],
          dust: calculated[2],
        },
        false,
      ),
    [id, location, calculated],
  );
  const backtestLoad = useCallback(
    () => (step === 6 ? api.backtest(location, false) : Promise.resolve(null)),
    [id, location, step],
  );
  const forecast = useRemote(forecastLoad),
    attribution = useRemote(attributionLoad),
    scenario = useRemote(scenarioLoad),
    backtest = useRemote(backtestLoad);
  const place = {
    name: location.short_name,
    area: "Pune + PCMC",
    lat: location.latitude,
    lng: location.longitude,
    value: location.pm25,
  };
  const combined = scenario.data?.results.find(
    (result) => result.id === "combined",
  );
  if (step === 1)
    return (
      <div className="at-overview-grid">
        <div className="at-stat-stack">
          <section className="at-panel">
            <h3>Fine particles · PM2.5</h3>
            <div className="at-big-number">
              {location.pm25}
              <small>µg/m³</small>
            </div>
            <span className="at-badge">
              {location.source_type.toUpperCase()}
            </span>
            <p>
              {location.name} · {stamp(location.timestamp)} IST
            </p>
            <AssumptionsPanel assumptions={location.assumptions} />
          </section>
          <section className="at-panel">
            <h3>Weather · modeled</h3>
            {location.weather ? (
              <>
                <p>
                  <b>{location.weather.temperature_2m}°C</b> · Wind{" "}
                  {location.weather.wind_speed_10m} km/h
                </p>
                <p>
                  Humidity {location.weather.relative_humidity_2m}% · Rain{" "}
                  {location.weather.precipitation} mm
                </p>
                <p>{stamp(location.weather.timestamp)} IST</p>
              </>
            ) : (
              <p>Weather unavailable for this location.</p>
            )}
          </section>
        </div>
        <AirMap place={place} heat cells={dashboard.cells} />
        <section className="at-panel at-stations">
          <h3>Nearby reference points</h3>
          <p>PM2.5 · µg/m³. Modeled points are not station AQI readings.</p>
          {[...dashboard.stations]
            .sort(
              (a, b) =>
                (a.latitude - location.latitude) ** 2 +
                (a.longitude - location.longitude) ** 2 -
                ((b.latitude - location.latitude) ** 2 +
                  (b.longitude - location.longitude) ** 2),
            )
            .slice(0, 4)
            .map((station) => (
              <div className="at-station" key={station.id}>
                <span>
                  <b>{station.short_name}</b>
                  <small>
                    {station.source_type} · {stamp(station.timestamp)} IST
                  </small>
                </span>
                <b>{station.pm25}</b>
              </div>
            ))}
        </section>
      </div>
    );
  if (step === 2)
    return (
      <div className="at-two-columns">
        <section className="at-panel at-connected-chart">
          <RequestStatus {...forecast} />
          {forecast.data && (
            <ForecastChart
              data={forecast.data}
              demo={false}
              hours={hours}
              onHours={onHours}
              replay={false}
            />
          )}
        </section>
        <section className="at-panel">
          <h3>Current modeled map</h3>
          <AirMap place={place} heat cells={dashboard.cells} />
          <p>
            This map shows the current snapshot. The chart shows the
            time-varying forecast.
          </p>
        </section>
      </div>
    );
  if (step === 3)
    return (
      <div className="at-source-grid">
        <section className="at-panel at-connected-chart">
          <RequestStatus {...attribution} />
          {attribution.data && <AttributionChart data={attribution.data} />}
        </section>
        <GuidedChat location={location} cuts={cuts} hours={hours} />
      </div>
    );
  if (step === 4)
    return (
      <div className="at-action-grid">
        <section className="at-panel">
          <h3>Adjust assumed reductions</h3>
          {["Traffic", "Industry", "Dust"].map((name, index) => (
            <label className="planning-control" key={name}>
              {name} <strong>{actions[index]}%</strong>
              <input
                type="range"
                aria-label={`Reduce ${name.toLowerCase()}`}
                min="0"
                max="80"
                step="5"
                value={actions[index]}
                onChange={(event) =>
                  onActions(
                    actions.map((value, n) =>
                      n === index ? Number(event.target.value) : value,
                    ),
                  )
                }
              />
            </label>
          ))}
          <button className="at-primary" onClick={onCalculate}>
            Calculate estimate
          </button>
          <RequestStatus {...scenario} />
          {actions.some((value, index) => value !== calculated[index]) && (
            <p>Inputs changed. Calculate to update the result.</p>
          )}
        </section>
        <section className="at-panel">
          <h3>Before & after · modeled scenario</h3>
          {combined && (
            <>
              <div className="at-map-compare">
                <AirMap place={place} heat compact cells={dashboard.cells} />
                <AirMap
                  place={place}
                  heat
                  compact
                  value={combined.after}
                  cells={combined.cells}
                />
              </div>
              <div className="at-big-number">
                {combined.before.toFixed(1)} → {combined.after.toFixed(1)}
                <small>µg/m³</small>
              </div>
              <p>
                {combined.reduction_percent.toFixed(1)}% estimated reduction.
                Simulated, not a measured improvement.
              </p>
              {scenario.data?.status_reason && (
                <p>{scenario.data.status_reason}</p>
              )}
              <AssumptionsPanel assumptions={combined.assumptions} />
            </>
          )}
        </section>
      </div>
    );
  if (step === 5)
    return (
      <GuidedPlan
        onPlan={onPlan}
        controls={planControls}
        onControls={onPlanControls}
        previousPlan={plan}
      />
    );
  if (step === 6)
    return (
      <section className="at-panel at-connected-chart">
        <RequestStatus {...backtest} />
        {backtest.data && <BacktestChart data={backtest.data} demo={false} />}
      </section>
    );
  if (step === 7)
    return (
      <>
        <div className="at-review-comparison">
          <section className="at-panel">
            <h3>Current {location.source_type} estimate</h3>
            <div className="at-big-number">
              {location.pm25}
              <small>µg/m³</small>
            </div>
            <p>{stamp(location.timestamp)} IST</p>
          </section>
          <section className="at-panel">
            <h3>With calculated actions</h3>
            <RequestStatus {...scenario} />
            {combined && (
              <>
                <div className="at-big-number">
                  {combined.after.toFixed(1)}
                  <small>µg/m³</small>
                </div>
                <p>
                  {combined.reduction_percent.toFixed(1)}% simulated reduction
                </p>
              </>
            )}
          </section>
        </div>
        <div className="at-review-grid">
          <section className="at-panel">
            <h3>Forecast</h3>
            <RequestStatus {...forecast} />
            {forecast.data && (
              <p>
                {forecast.data.forecast_provider ?? forecast.data.model_id} ·{" "}
                {hours} hours · modeled
              </p>
            )}
          </section>
          <section className="at-panel">
            <h3>Calculated actions</h3>
            <p>
              Traffic {cuts.traffic}% · Industry {cuts.industry}% · Dust{" "}
              {cuts.dust}%
            </p>
            <p>
              Effects apply to assumed local contributions above regional
              background.
            </p>
          </section>
          <section className="at-panel">
            <h3>Last computed city plan</h3>
            {plan ? (
              <>
                <p>
                  {plan.selected.actions
                    .map((action) => action.name)
                    .join(" + ") || "No action"}
                </p>
                <p>
                  {money(plan.selected.cost)} ·{" "}
                  {plan.selected.reduction_percent.toFixed(1)}% reduction
                </p>
                <p>Forecast valid {stamp(plan.forecast_valid_at)} IST</p>
              </>
            ) : (
              <p>Open Plan to compute a package.</p>
            )}
          </section>
          <section className="at-panel">
            <h3>Evidence limits</h3>
            <p>
              Historical backtesting does not validate the current provider
              forecast. Open Evidence to check availability for this location.
            </p>
            <AssumptionsPanel assumptions={location.assumptions} />
          </section>
        </div>
      </>
    );
  return null;
}
