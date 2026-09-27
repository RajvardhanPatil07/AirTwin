import { useEffect, useState } from "react";
import { ArrowRight, Moon, Sun, RefreshCw, MapPin } from "lucide-react";
import type {
  ActionId,
  AttributionResponse,
  BacktestResponse,
  Cuts,
  DashboardData,
  ForecastResponse,
  ScenarioResponse,
  Station,
} from "../types";
import { api, loadDashboard } from "../lib/api";
import { dateLabel, number, timeLabel } from "../lib/format";
import { DEFAULT_CUTS } from "../mocks/engine";
import { MapView } from "../components/MapView";
import { DataBadge } from "../components/DataBadge";
import { ScenarioPanel } from "../components/ScenarioPanel";
import {
  AttributionChart,
  BacktestChart,
  ForecastChart,
} from "../components/Charts";
import { AssumptionsPanel } from "../components/AssumptionsPanel";
import { Clock } from "../components/Clock";

const TABS = [
  "Overview",
  "Forecast",
  "Backtest",
  "Sources",
  "Scenarios",
] as const;
type Tab = (typeof TABS)[number];

export function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [locationId, setLocationId] = useState("bhosari");
  const [cellLocation, setCellLocation] = useState<Station | null>(null);
  const [tab, setTab] = useState<Tab>("Scenarios");
  const [dark, setDark] = useState(false);
  const [after, setAfter] = useState(true);
  const [cuts, setCuts] = useState<Cuts>({ ...DEFAULT_CUTS });
  const [appliedCuts, setAppliedCuts] = useState<Cuts>({ ...DEFAULT_CUTS });
  const [scenario, setScenario] = useState<ScenarioResponse | null>(null);
  const [action, setAction] = useState<ActionId>("combined");
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [backtest, setBacktest] = useState<BacktestResponse | null>(null);
  const [attribution, setAttribution] = useState<AttributionResponse | null>(
    null,
  );
  const [hours, setHours] = useState(24);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  const location =
    cellLocation ??
    data?.stations.find((s) => s.id === locationId) ??
    data?.stations[0];

  useEffect(() => {
    let active = true;
    loadDashboard().then((result) => {
      if (active) setData(result);
    });
    return () => {
      active = false;
    };
  }, []);
  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
  }, [dark]);
  useEffect(() => {
    if (!data || !location) return;
    let active = true;
    setLoading(true);
    setError(null);
    setScenario(null);
    Promise.all([
      api.scenarios(location, appliedCuts, data.demo),
      api.forecast(location, data.demo, hours),
      api.backtest(location, data.demo),
      api.attribution(location, data.demo),
    ])
      .then(([nextScenario, nextForecast, nextBacktest, nextAttribution]) => {
        if (!active) return;
        setScenario(nextScenario);
        setForecast(nextForecast);
        setBacktest(nextBacktest);
        setAttribution(nextAttribution);
        setLoading(false);
      })
      .catch(() => {
        if (active) {
          setLoading(false);
          setError(
            "Could not load location analysis. Retry or select another location.",
          );
        }
      });
    return () => {
      active = false;
    };
  }, [data, location, appliedCuts, hours, retry]);

  const selected =
    scenario?.results.find((result) => result.id === action) ??
    scenario?.results[0] ??
    null;
  const outdated = Object.keys(cuts).some(
    (key) => cuts[key as keyof Cuts] !== appliedCuts[key as keyof Cuts],
  );
  const chooseLocation = (next: Station) => {
    if (running) return;
    setLocationId(next.id);
    // Grid selection uses the BEFORE concentration even while displaying an after layer.
    const baselineCell = data?.cells.find((cell) => cell.id === next.id);
    setCellLocation(baselineCell ? { ...next, pm25: baselineCell.pm25 } : null);
    setAction("combined");
  };
  const run = async () => {
    if (!data || !location || running) return;
    setRunning(true);
    setError(null);
    try {
      const next = await api.scenarios(location, cuts, data.demo);
      setScenario(next);
      setAppliedCuts({ ...cuts });
      setAction("combined");
      setAfter(true);
    } catch {
      setError(
        "Scenario calculation failed. The previous result is retained; please retry.",
      );
    } finally {
      setRunning(false);
    }
  };

  if (!data || !location)
    return (
      <main className="startup" role="status">
        <RefreshCw className="spin" />
        <h1>Loading AirTwin PCMC</h1>
        <p>Preparing the pollution grid and location analysis.</p>
      </main>
    );
  return (
    <main className="dashboard">
      <header className="app-header">
        <div className="brand">
          <img
            src="/assets/airtwin-logo.png"
            width={44}
            height={44}
            alt="AirTwin contour logo"
          />
          <div>
            <h1>AirTwin PCMC</h1>
            <p>
              Urban Environmental Digital Twin · Pune &amp; Pimpri-Chinchwad
            </p>
          </div>
        </div>
        <div className="header-status">
          <Clock />
          <span className="status-chip data-time">
            Data as of {dateLabel(location.timestamp)} ·{" "}
            {timeLabel(location.timestamp)}
          </span>
          <span className={`status-chip ${data.demo ? "demo-chip" : ""}`}>
            {data.demo ? "DEMO DATA" : "API DATA"}
          </span>
          <button
            className="theme-button"
            aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
            onClick={() => setDark(!dark)}
          >
            {dark ? <Sun size={12} /> : <Moon size={12} />}
            {dark ? "Light" : "Dark"}
          </button>
        </div>
      </header>
      {data.warning && (
        <div className="api-warning" role="status">
          {data.warning}
        </div>
      )}
      <section className="story" aria-live="polite">
        <div className="story-main">
          <DataBadge source="modeled" />
          <div>
            <div className="eyebrow">
              {location.short_name.toUpperCase()} · INTERVENTION RESULT
            </div>
            {selected ? (
              <p>
                Modeled intervention{" "}
                {selected.reduction > 0
                  ? "lowers PM2.5"
                  : "leaves PM2.5 unchanged"}{" "}
                at {location.short_name}:{" "}
                <b className="before-number">{number(selected.before)}</b>
                <ArrowRight size={17} />
                <b className="after-number">{number(selected.after)} µg/m³</b>
                <b className="reduction-number">
                  ({selected.reduction > 0 ? "−" : ""}
                  {number(selected.reduction_percent)}%)
                </b>
              </p>
            ) : (
              <p>Preparing the selected location’s scenario…</p>
            )}
          </div>
        </div>
        <div className="story-labels">
          <DataBadge
            source={location.source_type}
            detail={data.demo ? "DEMO INPUT" : "BASELINE"}
          />
          <DataBadge source="modeled" detail="INTERVENTION" />
        </div>
      </section>
      <section className="workspace">
        <MapView
          stations={data.stations}
          cells={after && selected ? selected.cells : data.cells}
          selected={location}
          onSelect={chooseLocation}
          after={after}
          onAfter={() => setAfter(!after)}
          dark={dark}
          demo={data.demo}
        />
        <aside className="insight-panel">
          <div className="location-heading">
            <div>
              <label className="eyebrow" htmlFor="location">
                SELECTED LOCATION
              </label>
              <div className="location-picker">
                <select
                  id="location"
                  value={cellLocation ? "grid" : location.id}
                  disabled={running}
                  onChange={(event) => {
                    const station = data.stations.find(
                      (s) => s.id === event.target.value,
                    );
                    if (station) chooseLocation(station);
                  }}
                >
                  {cellLocation && (
                    <option value="grid">{cellLocation.name}</option>
                  )}
                  {data.stations.map((station) => (
                    <option key={station.id} value={station.id}>
                      {station.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <span
              className={`result-status ${outdated ? "stale" : ""}`}
              role="status"
            >
              {loading
                ? "LOADING"
                : outdated
                  ? "RESULTS OUTDATED"
                  : "RESULTS CURRENT"}
            </span>
          </div>
          <nav className="tabs" role="tablist" aria-label="Location insights">
            {TABS.map((item) => (
              <button
                key={item}
                role="tab"
                id={`tab-${item}`}
                aria-selected={tab === item}
                aria-controls="insight-content"
                className={tab === item ? "active" : ""}
                onClick={() => setTab(item)}
              >
                {item}
              </button>
            ))}
          </nav>
          <div
            id="insight-content"
            role="tabpanel"
            aria-labelledby={`tab-${tab}`}
          >
            {error && (
              <div className="error-state" role="alert">
                <p>{error}</p>
                <button onClick={() => setRetry(retry + 1)}>
                  Retry analysis
                </button>
              </div>
            )}
            {loading ? (
              <div className="loading-state" role="status">
                <RefreshCw size={18} className="spin" />
                Loading location analysis…
              </div>
            ) : (
              <>
                {tab === "Scenarios" && (
                  <ScenarioPanel
                    cuts={cuts}
                    onCuts={setCuts}
                    response={scenario}
                    selected={selected}
                    onSelect={setAction}
                    onRun={run}
                    outdated={outdated}
                    busy={running}
                    inputSource={location.source_type}
                  />
                )}
                {tab === "Forecast" && forecast && (
                  <ForecastChart
                    data={forecast}
                    hours={hours}
                    onHours={setHours}
                    demo={data.demo}
                  />
                )}
                {tab === "Backtest" && backtest && (
                  <BacktestChart data={backtest} demo={data.demo} />
                )}
                {tab === "Sources" && attribution && (
                  <AttributionChart data={attribution} />
                )}
                {tab === "Overview" && (
                  <section className="tab-content overview">
                    <div className="section-heading">
                      <h2>
                        <MapPin size={16} /> {location.name}
                      </h2>
                      <DataBadge source={location.source_type} />
                    </div>
                    <div className="overview-reading">
                      <span>Baseline PM2.5</span>
                      <strong>
                        {number(location.pm25)} <small>µg/m³</small>
                      </strong>
                      <p>
                        {dateLabel(location.timestamp)} ·{" "}
                        {timeLabel(location.timestamp)} IST
                      </p>
                    </div>
                    <p className="summary-note">
                      Compare likely sources and three emission-control actions.
                      Results are ranked by population-weighted exposure
                      reduction.
                    </p>
                    {data.demo && (
                      <div className="demo-notice">
                        <b>Offline frontend demonstration</b>
                        <p>
                          All location inputs and population counts are
                          synthetic. Forecasts in this browser-only fallback are
                          illustrative and the backtest predictor is persistence.
                          Connect VITE_API_BASE_URL to use the executable backend.
                        </p>
                      </div>
                    )}
                    <AssumptionsPanel
                      assumptions={location.assumptions}
                      title="Input provenance"
                    />
                    <button
                      className="run-button"
                      onClick={() => setTab("Scenarios")}
                    >
                      Compare interventions
                    </button>
                  </section>
                )}
              </>
            )}
          </div>
        </aside>
      </section>
    </main>
  );
}
