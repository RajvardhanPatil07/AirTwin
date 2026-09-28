import { useEffect, useMemo, useState } from "react";
import { Moon, Sun, RefreshCw, MapPin, Leaf } from "lucide-react";
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
  TimelineResponse,
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
import { HealthCard } from "../components/HealthCard";
import { TimelineBar } from "../components/TimelineBar";

const TABS = [
  "Overview",
  "Forecast",
  "Backtest",
  "Sources",
  "Scenarios",
] as const;
type Tab = (typeof TABS)[number];

export function Dashboard() {
  const [region, setRegion] = useState<RegionId>("maharashtra");
  const [replayAt, setReplayAt] = useState<string | null>(null);
  const [switching, setSwitching] = useState(false);
  const [data, setData] = useState<DashboardData | null>(null);
  const [locationId, setLocationId] = useState("bhosari");
  const [cellLocation, setCellLocation] = useState<Station | null>(null);
  const [tab, setTab] = useState<Tab>("Scenarios");
  const [timeline, setTimeline] = useState<TimelineResponse | null>(null);
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [frameIndex, setFrameIndex] = useState(0);
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
  const [dashboardRetry, setDashboardRetry] = useState(0);
  const location =
    cellLocation ??
    data?.stations.find((s) => s.id === locationId) ??
    data?.stations[0];

  useEffect(() => {
    let active = true;
    loadDashboard(replayAt, region).then((result) => {
      if (active) {
        setData(result);
        if (!replayAt)
          setLocationId(
            result.stations.find((station) =>
              station.name.includes(
                region === "maharashtra" ? "Pune" : "Bhosari",
              ),
            )?.id ?? result.stations[0].id,
          );
        setCellLocation(null);
        setSwitching(false);
      }
    });
    return () => {
      active = false;
    };
  }, [replayAt, region, dashboardRetry]);
  useEffect(() => {
    if (replayAt) return;
    let active = true;
    const timer = window.setInterval(() => {
      loadDashboard(null, region).then((next) => {
        if (active)
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
    setTimeline(null);
    setFrameIndex(0);
    if (!data || data.demo) return;
    let active = true;
    setTimelineLoading(true);
    api
      .timeline(replayAt, region)
      .then((next) => active && setTimeline(next))
      .catch(() => active && setTimeline(null))
      .finally(() => active && setTimelineLoading(false));
    return () => {
      active = false;
    };
  }, [data, replayAt, region]);
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
  }, [data, location, appliedCuts, hours, retry, replayAt, region]);

  const frame = frameIndex > 0 ? timeline?.frames[frameIndex] : undefined;
  const mapCells = useMemo(() => {
    if (!data) return [];
    if (frame) {
      const values = new Map(frame.cells.map((cell) => [cell.id, cell.pm25]));
      return data.cells.map((cell) => ({ ...cell, pm25: values.get(cell.id) ?? cell.pm25 }));
    }
    return null;
  }, [data, frame]);
  const mapStations = useMemo(() => {
    if (!data || !frame) return data?.stations ?? [];
    const values = new Map(frame.stations.map((station) => [station.id, station.pm25]));
    return data.stations.map((station) =>
      values.has(station.id)
        ? { ...station, pm25: values.get(station.id)!, source_type: "modeled" as const }
        : station,
    );
  }, [data, frame]);
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
    // Grid selection uses the BEFORE concentration even while displaying an after layer.
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
      setError("Historical replay could not load. Please retry.");
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
          <span className="brand-mark" aria-label="AirTwin leaf logo" role="img"><Leaf size={36} strokeWidth={1.7} /></span>
          <div>
            <h1>AirTwin {region === "maharashtra" ? "Maharashtra" : "PCMC"}</h1>
            <p>
              Urban Environmental Digital Twin ·{" "}
              {region === "maharashtra"
                ? "Maharashtra"
                : "Pune & Pimpri-Chinchwad"}
            </p>
          </div>
        </div>
        <div className="header-status">
          <label className="status-chip">
            Region{" "}
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
          {!data.demo && region === "pcmc" && (
            <button
              className="status-chip replay-toggle"
              disabled={switching}
              onClick={toggleReplay}
              aria-pressed={Boolean(replayAt)}
            >
              {switching
                ? "Loading replay…"
                : replayAt
                  ? "Exit replay"
                  : "Historical replay"}
            </button>
          )}
          <button
            className="theme-button"
            aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
            onClick={() => setDark(!dark)}
          >
            {dark ? <Sun size={12} /> : <Moon size={12} />}
            {dark ? "Light" : "Dark"}
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
          REPLAYED HISTORICAL DATA · {dateLabel(replayAt)} ·{" "}
          {timeLabel(replayAt)} IST · target{" "}
          {location.source_type.toUpperCase()}
        </div>
      )}
      {data.warning && (
        <div className="api-warning" role="status">
          {data.warning}
          {data.demo && <button className="status-chip" onClick={() => setDashboardRetry(value => value + 1)}>Retry backend</button>}
        </div>
      )}
      {data.coverage?.modeled_points !== undefined && (
        <div className="api-warning">
          Coverage: {data.coverage.modeled_points} CAMS model reference points ·{" "}
          {data.coverage.observed_points} fresh observed points · provider cache
          refreshed hourly while the backend is running.
        </div>
      )}
      <section className="workspace-intro">
        <h2>Explore air quality</h2>
        <p>Compare local conditions and test clean-air interventions.</p>
        <div className="intro-summary">
          <div><span>Selected location</span><strong>{location.short_name}</strong></div>
          <div><span>PM2.5 · {location.source_type}</span><strong>{number(location.pm25)} <small>µg/m³</small></strong></div>
          <div><span>Scenario benefit · modeled</span><strong>{selected ? `${number(selected.reduction_percent)}%` : "Preparing…"}</strong></div>
        </div>
        <span>{data.demo ? "Synthetic demonstration" : `Snapshot · ${dateLabel(location.timestamp)} · ${timeLabel(location.timestamp)} IST`}
          {!data.demo && !replayAt && Date.now() - Date.parse(location.timestamp) > 24 * 3600000 && <strong className="snapshot-stale"> · STALE: over 24 h old; forecasts start at this snapshot</strong>}
        </span>
      </section>
      <section className="workspace">
        <MapView
          stations={mapStations}
          cells={mapCells ?? (after && selected ? selected.cells : data.cells)}
          selected={location}
          onSelect={chooseLocation}
          after={!frame && after && Boolean(selected)}
          forecastLabel={frame ? `+${frame.hour} h forecast` : null}
          onAfter={() => {
            setFrameIndex(0);
            setAfter(!after);
          }}
          timeline={data.demo ? <div className="timeline-bar timeline-unavailable">Forecast timeline requires backend data · synthetic demo shown</div> :
            <TimelineBar
              timeline={timeline}
              index={frameIndex}
              onIndex={setFrameIndex}
              loading={timelineLoading}
            />
          }
          dark={dark}
          demo={data.demo}
          weather={
            location.weather?.source_type ? location.weather : data.weather
          }
          region={data.region}
          zones={data.zones}
          zonesSourceType={data.zones_source_type}
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
              {loading || !selected
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
                tabIndex={tab === item ? 0 : -1}
                onKeyDown={(event) => {
                  const index = TABS.indexOf(item);
                  const next =
                    event.key === "ArrowRight"
                      ? TABS[(index + 1) % TABS.length]
                      : event.key === "ArrowLeft"
                        ? TABS[(index + TABS.length - 1) % TABS.length]
                        : event.key === "Home"
                          ? TABS[0]
                          : event.key === "End"
                            ? TABS[TABS.length - 1]
                            : null;
                  if (next) {
                    event.preventDefault();
                    setTab(next);
                    document.getElementById(`tab-${next}`)?.focus();
                  }
                }}
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
            {loading || (!selected && !error) ? (
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
                    <div className="section-heading">
                      <h2>
                        <MapPin size={16} /> {location.name}
                      </h2>
                      <DataBadge source={location.source_type} />
                    </div>
                    <HealthCard
                      pm25={location.pm25}
                      source={location.source_type}
                      forecast={forecast}
                    />
                    <p className="helper">
                      Snapshot {dateLabel(location.timestamp)} ·{" "}
                      {timeLabel(location.timestamp)} IST
                    </p>
                    <p className="summary-note">
                      Compare likely sources and three emission-control actions.
                      Results are ranked by population-weighted exposure
                      reduction.
                    </p>
                    {location.pollutants && (
                      <div className="environment-readings">
                        <h3>Environmental context · CAMS / Open-Meteo</h3>
                        {Object.entries(location.pollutants).map(
                          ([key, point]) => (
                            <p key={key}>
                              <span>
                                {key === "pm2_5"
                                  ? "PM2.5"
                                  : key === "pm10"
                                    ? "PM10"
                                    : key.replaceAll("_", " ")}
                              </span>{" "}
                              <strong>
                                {number(point.value)} {point.unit}
                              </strong>{" "}
                              <DataBadge source={point.source_type} />
                            </p>
                          ),
                        )}
                        {location.weather &&
                          Object.entries(location.weather)
                            .filter(
                              ([key, value]) =>
                                !["source_type", "timestamp"].includes(key) &&
                                typeof value === "number",
                            )
                            .map(([key, value]) => (
                              <p key={key}>
                                {key.replaceAll("_", " ")}:{" "}
                                {number(value as number)}{" "}
                                <DataBadge source="modeled" />
                              </p>
                            ))}
                        <small>
                          Weather units: °C, % humidity/cloud, m/s wind, °
                          direction, mm rain, hPa pressure.
                        </small>
                      </div>
                    )}
                    {data.demo && (
                      <div className="demo-notice">
                        <b>Offline frontend demonstration</b>
                        <p>
                          All location inputs and population counts are
                          synthetic. This local fallback uses illustrative
                          forecasts and a persistence demonstration. Connect the
                          backend to use trained LightGBM forecasts.
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
