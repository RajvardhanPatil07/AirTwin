import { useEffect, useState } from "react";
import { History, MapPin, Moon, RefreshCw, Sun } from "lucide-react";
import type {
  RegionId,
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
import { AskAirTwin } from "../components/AskAirTwin";

const TABS = [
  { id: "Overview", step: "01", label: "Observe" },
  { id: "Forecast", step: "02", label: "Predict" },
  { id: "Backtest", step: "03", label: "Validate" },
  { id: "Sources", step: "04", label: "Explain" },
  { id: "Scenarios", step: "05", label: "Act" },
] as const;
type Tab = (typeof TABS)[number]["id"];

export function Dashboard() {
  const [region, setRegion] = useState<RegionId>("pcmc");
  const [replayAt, setReplayAt] = useState<string | null>(null);
  const [switching, setSwitching] = useState(false);
  const [data, setData] = useState<DashboardData | null>(null);
  const [locationId, setLocationId] = useState("bhosari");
  const [cellLocation, setCellLocation] = useState<Station | null>(null);
  const [tab, setTab] = useState<Tab>("Overview");
  const [dark, setDark] = useState(true);
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
    data?.stations.find((station) => station.id === locationId) ??
    data?.stations[0];

  useEffect(() => {
    let active = true;
    loadDashboard(replayAt, region).then((result) => {
      if (!active) return;
      setData(result);
      if (!replayAt) {
        setLocationId(
          result.stations.find((station) =>
            station.name.includes(region === "maharashtra" ? "Pune" : "Bhosari"),
          )?.id ?? result.stations[0].id,
        );
      }
      setCellLocation(null);
      setSwitching(false);
    });
    return () => {
      active = false;
    };
  }, [replayAt, region]);

  useEffect(() => {
    if (replayAt) return;
    let active = true;
    const timer = window.setInterval(() => {
      loadDashboard(null, region).then((next) => {
        if (!active) return;
        setData((previous) =>
          previous?.coverage?.updated_at === next.coverage?.updated_at &&
          previous?.stations[0]?.timestamp === next.stations[0]?.timestamp
            ? previous
            : next,
        );
      });
    }, 60000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [region, replayAt]);

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
      api.scenarios(location, appliedCuts, data.demo, replayAt, region),
      api.forecast(location, data.demo, hours, replayAt, region),
      api.backtest(location, data.demo, replayAt, region),
      api.attribution(location, data.demo, replayAt, region),
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
        if (!active) return;
        setLoading(false);
        setError("Analysis unavailable. Retry or choose another location.");
      });
    return () => {
      active = false;
    };
  }, [data, location, appliedCuts, hours, retry, replayAt, region]);

  const currentScenario =
    scenario?.location_id === location?.id ? scenario : null;
  const selected =
    currentScenario?.results.find((result) => result.id === action) ??
    currentScenario?.results[0] ??
    null;
  const outdated = Object.keys(cuts).some(
    (key) => cuts[key as keyof Cuts] !== appliedCuts[key as keyof Cuts],
  );

  const chooseLocation = (next: Station) => {
    if (running) return;
    setLocationId(next.id);
    const baselineCell = data?.cells.find((cell) => cell.id === next.id);
    setCellLocation(baselineCell ? { ...next, pm25: baselineCell.pm25 } : null);
    setAction("combined");
  };

  const toggleReplay = async () => {
    if (switching) return;
    setSwitching(true);
    setHours(24);
    try {
      if (replayAt) setReplayAt(null);
      else {
        const replay = await api.replay();
        setLocationId(replay.location_id);
        setReplayAt(replay.timestamp);
      }
    } catch {
      setSwitching(false);
      setError("Historical replay could not load.");
    }
  };

  const run = async () => {
    if (!data || !location || running) return;
    setRunning(true);
    setError(null);
    try {
      const next = await api.scenarios(
        location,
        cuts,
        data.demo,
        replayAt,
        region,
      );
      setScenario(next);
      setAppliedCuts({ ...cuts });
      setAction("combined");
      setAfter(true);
    } catch {
      setError("Scenario calculation failed. Retry.");
    } finally {
      setRunning(false);
    }
  };

  if (!data || !location) {
    return (
      <main className="startup" role="status">
        <RefreshCw className="spin" />
        <h1>AirTwin</h1>
        <p>Loading city model…</p>
      </main>
    );
  }

  const weather = location.weather?.source_type
    ? location.weather
    : data.weather;
  const pm10 = location.pollutants?.pm10;

  return (
    <main className="dashboard">
      <header className="app-header">
        <div className="brand">
          <img
            src="/assets/airtwin-logo.png"
            width={36}
            height={36}
            alt="AirTwin contour logo"
          />
          <div>
            <h1>AirTwin</h1>
            <p>
              ENR-01 · {region === "maharashtra" ? "Maharashtra" : "Pune + PCMC"}
            </p>
          </div>
        </div>

        <div className="header-status">
          <label className="status-chip region-control">
            <select
              aria-label="Region"
              value={region}
              onChange={(event) => {
                setReplayAt(null);
                setCellLocation(null);
                setData(null);
                setScenario(null);
                setRegion(event.target.value as RegionId);
              }}
            >
              <option value="pcmc">Pune + PCMC</option>
              <option value="maharashtra">Maharashtra</option>
            </select>
          </label>

          <DataBadge
            source={location.source_type}
            detail={data.demo ? "DEMO" : "INPUT"}
          />

          <span className="status-chip data-time">
            {dateLabel(location.timestamp)} · {timeLabel(location.timestamp)}
          </span>

          {!data.demo && region === "pcmc" && (
            <button
              className="icon-button"
              disabled={switching}
              onClick={toggleReplay}
              aria-label={replayAt ? "Exit historical replay" : "Historical replay"}
              aria-pressed={Boolean(replayAt)}
              title={replayAt ? "Exit replay" : "Historical replay"}
            >
              <History size={15} />
            </button>
          )}

          <button
            className="icon-button"
            aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
            onClick={() => setDark(!dark)}
            title={dark ? "Light theme" : "Dark theme"}
          >
            {dark ? <Sun size={15} /> : <Moon size={15} />}
          </button>

          <AskAirTwin
            location={location}
            demo={data.demo}
            replayAt={replayAt}
            region={region}
            cuts={appliedCuts}
            hours={hours}
          />
        </div>
      </header>

      {replayAt && (
        <div className="replay-banner" role="status">
          Historical replay · {dateLabel(replayAt)} · {timeLabel(replayAt)}
        </div>
      )}

      {data.warning && (
        <div className="api-warning" role="status">
          {data.warning}
        </div>
      )}

      <section className="workspace">
        <MapView
          stations={data.stations}
          cells={after && selected ? selected.cells : data.cells}
          selected={location}
          onSelect={chooseLocation}
          after={after && Boolean(selected)}
          onAfter={() => setAfter(!after)}
          dark={dark}
          demo={data.demo}
          weather={weather}
          region={data.region}
          zones={data.zones}
        />

        <aside className="insight-panel">
          <div className="location-heading">
            <div>
              <div className="eyebrow">
                {region === "maharashtra" ? "STATE VIEW" : "CITY VIEW"}
              </div>
              <div className="location-picker">
                <select
                  id="location"
                  aria-label="Selected location"
                  value={cellLocation ? "grid" : location.id}
                  disabled={running}
                  onChange={(event) => {
                    const station = data.stations.find(
                      (item) => item.id === event.target.value,
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
              className={"result-status " + (outdated ? "stale" : "")}
              role="status"
            >
              {loading || !selected ? "Loading" : outdated ? "Unsaved" : "Current"}
            </span>
          </div>

          <nav className="tabs" role="tablist" aria-label="AirTwin workflow">
            {TABS.map((item, index) => (
              <button
                key={item.id}
                role="tab"
                id={"tab-" + item.id}
                aria-selected={tab === item.id}
                tabIndex={tab === item.id ? 0 : -1}
                onKeyDown={(event) => {
                  const next =
                    event.key === "ArrowRight"
                      ? TABS[(index + 1) % TABS.length].id
                      : event.key === "ArrowLeft"
                        ? TABS[(index + TABS.length - 1) % TABS.length].id
                        : event.key === "Home"
                          ? TABS[0].id
                          : event.key === "End"
                            ? TABS[TABS.length - 1].id
                            : null;
                  if (!next) return;
                  event.preventDefault();
                  setTab(next);
                  document.getElementById("tab-" + next)?.focus();
                }}
                aria-controls="insight-content"
                className={tab === item.id ? "active" : ""}
                onClick={() => setTab(item.id)}
              >
                <span>{item.step}</span>
                {item.label}
              </button>
            ))}
          </nav>

          <div
            id="insight-content"
            role="tabpanel"
            aria-labelledby={"tab-" + tab}
          >
            {error && (
              <div className="error-state" role="alert">
                <span>{error}</span>
                <button onClick={() => setRetry((value) => value + 1)}>
                  Retry
                </button>
              </div>
            )}

            {loading || (!selected && !error) ? (
              <div className="loading-state" role="status">
                <RefreshCw size={16} className="spin" />
                Loading…
              </div>
            ) : (
              <>
                {tab === "Scenarios" && (
                  <ScenarioPanel
                    cuts={cuts}
                    onCuts={setCuts}
                    response={currentScenario}
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
                    replay={Boolean(replayAt)}
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
                    <div className="overview-hero">
                      <div>
                        <div className="eyebrow">BASELINE PM2.5</div>
                        <div className="overview-value">
                          <strong>{number(location.pm25)}</strong>
                          <span>µg/m³</span>
                        </div>
                      </div>
                      <DataBadge source={location.source_type} />
                    </div>

                    <div className="overview-meta">
                      <MapPin size={13} />
                      <span>{location.short_name}</span>
                      <span>·</span>
                      <span>{dateLabel(location.timestamp)}</span>
                      <span>·</span>
                      <span>{timeLabel(location.timestamp)}</span>
                    </div>

                    {(pm10 || weather) && (
                      <div className="overview-stats">
                        {pm10 && (
                          <div>
                            <span>PM10</span>
                            <strong>{number(pm10.value)}</strong>
                            <small>{pm10.unit}</small>
                          </div>
                        )}
                        {weather?.wind_speed_10m !== undefined && (
                          <div>
                            <span>Wind</span>
                            <strong>{number(weather.wind_speed_10m * 3.6)}</strong>
                            <small>km/h</small>
                          </div>
                        )}
                        {weather?.relative_humidity_2m !== undefined && (
                          <div>
                            <span>Humidity</span>
                            <strong>{number(weather.relative_humidity_2m, 0)}</strong>
                            <small>%</small>
                          </div>
                        )}
                      </div>
                    )}

                    {data.demo && (
                      <div className="demo-notice">
                        Synthetic offline mode.
                      </div>
                    )}

                    <AssumptionsPanel
                      assumptions={location.assumptions}
                      title="Provenance & assumptions"
                    />

                    <button
                      className="quiet-cta"
                      onClick={() => setTab("Scenarios")}
                    >
                      Simulate actions →
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
