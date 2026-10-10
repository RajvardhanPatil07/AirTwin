import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity, ArrowDownRight, ArrowRight, BarChart3, CheckCircle2,
  ChevronRight, CircleHelp, CloudSun, Database, Gauge, GitCompareArrows,
  Layers3, Leaf, MapPin, RefreshCw, Search, ShieldCheck, SlidersHorizontal,
  TriangleAlert, Wind,
} from "lucide-react";
import type {
  ActionId, AttributionResponse, BacktestResponse, Cuts, DashboardData,
  ForecastResponse, ScenarioResponse, Station, TimelineResponse,
} from "../types";
import { api, loadDashboard } from "../lib/api";
import { dateLabel, number, timeLabel } from "../lib/format";
import { DEFAULT_CUTS } from "../mocks/engine";
// Map and Recharts are separate on-demand chunks, not part of the shell bundle.
const MapView = lazy(() => import("../components/MapView").then((module) => ({ default: module.MapView })));
const chartsModule = () => import("../components/Charts");
const ForecastChart = lazy(() => chartsModule().then((module) => ({ default: module.ForecastChart })));
const BacktestChart = lazy(() => chartsModule().then((module) => ({ default: module.BacktestChart })));
const AttributionChart = lazy(() => chartsModule().then((module) => ({ default: module.AttributionChart })));
import { ScenarioPanel } from "../components/ScenarioPanel";
import { AssumptionsPanel } from "../components/AssumptionsPanel";
import { TimelineBar } from "../components/TimelineBar";
import { AskAirTwin } from "../components/AskAirTwin";
import { DataBadge } from "../components/DataBadge";
import "./decision-studio.css";
import "./framevitals-theme.css";

type View = "overview" | "forecast" | "sources" | "scenarios" | "validation";
type SaveState = "none" | "saved" | "unsaved";
const NAV = [
  { id: "overview" as View, label: "City overview", icon: Gauge, description: "Status & map" },
  { id: "forecast" as View, label: "Forecast lab", icon: Activity, description: "1–72 hour outlook" },
  { id: "sources" as View, label: "Source insights", icon: Layers3, description: "Proxy contributions" },
  { id: "scenarios" as View, label: "Interventions", icon: SlidersHorizontal, description: "Compare actions" },
  { id: "validation" as View, label: "Validation", icon: BarChart3, description: "Historical evidence" },
];
const SOURCE_NAMES = ["Traffic", "Industry", "Construction / dust", "Regional background"];
const compare = (a: Cuts, b: Cuts) =>
  a.traffic === b.traffic && a.industry === b.industry && a.dust === b.dust;

function ModelNotice({ children }: { children: React.ReactNode }) {
  return <div className="tw-model-notice"><TriangleAlert size={15} /><p>{children}</p></div>;
}

export function DecisionStudio() {
  const [view, setView] = useState<View>("overview");
  const [data, setData] = useState<DashboardData | null>(null);
  const [replayAt, setReplayAt] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState("");
  const [selectedGrid, setSelectedGrid] = useState<Station | null>(null);
  const [search, setSearch] = useState("");
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [backtest, setBacktest] = useState<BacktestResponse | null>(null);
  const [attribution, setAttribution] = useState<AttributionResponse | null>(null);
  const [scenario, setScenario] = useState<ScenarioResponse | null>(null);
  const [timeline, setTimeline] = useState<TimelineResponse | null>(null);
  const [timelineRequested, setTimelineRequested] = useState(false);
  const [frameIndex, setFrameIndex] = useState(0);
  const [hours, setHours] = useState(24);
  const [cuts, setCuts] = useState<Cuts>({ ...DEFAULT_CUTS });
  const [appliedCuts, setAppliedCuts] = useState<Cuts>({ ...DEFAULT_CUTS });
  const [action, setAction] = useState<ActionId>("combined");
  const [after, setAfter] = useState(false);
  const [reload, setReload] = useState(0);
  const [loading, setLoading] = useState(true);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveState, setSaveState] = useState<SaveState>("none");
  const [saveMessage, setSaveMessage] = useState("");
  const [storage, setStorage] = useState<{ configured: boolean; connected: boolean; runs: number } | null>(null);
  const location = selectedGrid ?? data?.stations.find((s) => s.id === selectedId) ?? data?.stations[0];

  useEffect(() => {
    let active = true;
    setLoading(true);
    loadDashboard(replayAt, "pcmc", reload > 0).then((next) => {
      if (!active) return;
      // Keep the last valid city reading during transient provider failures.
      setData((old) => next.demo && old && !old.demo
        ? { ...old, warning: next.warning }
        : next);
      setSelectedId((old) => next.stations.some((item) => item.id === old) ? old : (next.stations[0]?.id ?? ""));
      setSelectedGrid(null);
      setError(null);
      setLoading(false);
    }).catch(() => {
      if (active) {
        setError("Unable to refresh the AirTwin data workspace.");
        setLoading(false);
      }
    });
    return () => { active = false; };
  }, [replayAt, reload]);

  useEffect(() => {
    if (replayAt) return;
    const timer = window.setInterval(() => setReload((old) => old + 1), 60000);
    return () => window.clearInterval(timer);
  }, [replayAt]);

  // Only request analyses the active panel can show. Slow validation and
  // attribution work never block the initial city overview or map.
  useEffect(() => {
    setForecast(null);
    setBacktest(null);
    setAttribution(null);
    setScenario(null);
    setSaveState("none");
  }, [location?.id, replayAt, data?.demo]);

  useEffect(() => {
    if (!data || !location) return;
    let active = true;
    setAnalysisLoading(true);
    const jobs: Promise<unknown>[] = [];
    if (view === "overview" || view === "forecast") {
      jobs.push(api.forecast(location, data.demo, hours, replayAt, "pcmc")
        .then((value) => { if (active) setForecast(value); }));
    }
    if (view === "validation") {
      jobs.push(api.backtest(location, data.demo, replayAt, "pcmc")
        .then((value) => { if (active) setBacktest(value); }));
    }
    if (view === "sources") {
      jobs.push(api.attribution(location, data.demo, replayAt, "pcmc")
        .then((value) => { if (active) setAttribution(value); }));
    }
    if (view === "overview" || view === "scenarios") {
      jobs.push(api.scenarios(location, appliedCuts, data.demo, replayAt, "pcmc")
        .then((value) => { if (active) setScenario(value); }));
    }
    Promise.allSettled(jobs).then((results) => {
      if (!active) return;
      if (results.length > 0 && results.every((result) => result.status === "rejected")) {
        setError("Selected analysis is unavailable. Try another location or retry.");
      } else {
        setError(null);
      }
      setAnalysisLoading(false);
    });
    return () => { active = false; };
    // Do not depend on appliedCuts: saving a user-run decision should not
    // trigger a competing speculative request that overwrites its result.
  }, [data, location?.id, view, hours, replayAt, reload]);

  useEffect(() => {
    if (!data || data.demo) {
      setStorage(null);
      return;
    }
    let active = true;
    api.dataHealth("pcmc").then((result) => active && setStorage(result.database))
      .catch(() => active && setStorage(null));
    return () => { active = false; };
  }, [data?.stations[0]?.timestamp, data?.demo]);

  useEffect(() => {
    // Hour-by-hour interpolation is costly. Do not generate it until someone
    // chooses to explore the playback timeline.
    if (!timelineRequested || !data || data.demo) return;
    let active = true;
    setFrameIndex(0);
    setTimeline(null);
    api.timeline(replayAt, "pcmc").then((result) => active && setTimeline(result))
      .catch(() => {
        if (active) {
          setTimeline(null);
          // Restore the load button so an unsuccessful playback can be retried.
          setTimelineRequested(false);
        }
      });
    return () => { active = false; };
  }, [timelineRequested, data?.stations[0]?.timestamp, data?.demo, replayAt]);

  const timelineControl = useMemo(() => data?.demo
    ? <div className="timeline-bar timeline-unavailable">Forecast replay requires the backend · SYNTHETIC demo shown</div>
    : !timelineRequested
      ? <button type="button" className="timeline-bar tw-timeline-load" onClick={() => setTimelineRequested(true)}>Load modeled forecast playback</button>
      : <TimelineBar timeline={timeline} index={frameIndex} onIndex={(n) => { setFrameIndex(n); setAfter(false); }} loading={!timeline}/>,
    [data?.demo, timelineRequested, timeline, frameIndex],
  );

  const selected = useMemo(() =>
    scenario?.results.find((item) => item.id === action) ?? scenario?.results[0] ?? null,
    [scenario, action],
  );
  const frame = frameIndex > 0 ? timeline?.frames[frameIndex] : undefined;
  const mapStations = useMemo(() => {
    if (!data) return [];
    if (!frame) return data.stations;
    const values = new Map(frame.stations.map((item) => [item.id, item.pm25]));
    return data.stations.map((item) => values.has(item.id)
      ? { ...item, pm25: values.get(item.id)!, source_type: "modeled" as const }
      : item);
  }, [data, frame]);
  const mapCells = useMemo(() => {
    if (!data) return [];
    if (frame) {
      const values = new Map(frame.cells.map((item) => [item.id, item.pm25]));
      return data.cells.map((item) => ({ ...item, pm25: values.get(item.id) ?? item.pm25 }));
    }
    return after && selected ? selected.cells : data.cells;
  }, [data, frame, after, selected]);
  const hotCells = useMemo(() =>
    [...(data?.cells ?? [])].sort((a, b) => b.pm25 - a.pm25).slice(0, 4),
    [data],
  );
  const forecastValues = forecast?.series.filter((point) => point.predicted != null) ?? [];
  const future24 = forecastValues[23]?.predicted;
  const stale = Boolean(location?.timestamp && Date.now() - Date.parse(location.timestamp) > 24 * 3600000);
  const dirty = !compare(cuts, appliedCuts);
  const counts = data?.stations.reduce((acc, item) => {
    acc[item.source_type] = (acc[item.source_type] ?? 0) + 1;
    return acc;
  }, { observed: 0, modeled: 0, synthetic: 0 }) ?? { observed: 0, modeled: 0, synthetic: 0 };
  const filtered = data?.stations.filter((item) => item.name.toLowerCase().includes(search.toLowerCase())) ?? [];

  function navigateTo(next: View) {
    setView(next);
    if (window.matchMedia("(max-width: 1100px)").matches) {
      window.requestAnimationFrame(() => document.getElementById("analysis-panel")?.scrollIntoView({ behavior: "smooth", block: "start" }));
    }
  }

  const chooseLocation = useCallback((next: Station) => {
    if (running) return;
    setSelectedId(next.id);
    const original = data?.cells.find((cell) => cell.id === next.id);
    setSelectedGrid(original ? { ...next, pm25: original.pm25, source_type: "modeled" } : null);
    setFrameIndex(0);
    setAfter(false);
    setAction("combined");
  }, [running, data?.cells]);

  const toggleAfter = useCallback(() => {
    setFrameIndex(0);
    setAfter((last) => !last);
  }, []);

  async function toggleReplay() {
    if (loading || data?.demo) return;
    setHours(24);
    setSelectedGrid(null);
    setAfter(false);
    if (replayAt) {
      setReplayAt(null);
      return;
    }
    try {
      const replay = await api.replay();
      setSelectedId(replay.location_id);
      setReplayAt(replay.timestamp);
      setView("validation");
    } catch {
      setError("Historical replay is currently unavailable.");
    }
  }

  async function runIntervention() {
    if (!location || !data || running) return;
    setRunning(true);
    setSaveState("none");
    try {
      if (data.demo) {
        const next = await api.scenarios(location, cuts, true, replayAt, "pcmc");
        setScenario(next);
        setSaveState("unsaved");
        setSaveMessage("Synthetic offline demonstration; no decision was saved.");
      } else {
        try {
          const result = await api.runDecision(location.id, cuts, replayAt, "pcmc");
          setScenario(result.scenario);
          setSaveState(result.persisted ? "saved" : "unsaved");
          setSaveMessage(result.persisted ? "Saved as " + result.run_id : (result.storage_warning ?? "Not saved"));
          if (result.persisted) {
            api.dataHealth("pcmc").then((next) => setStorage(next.database)).catch(() => undefined);
          }
        } catch {
          const result = await api.scenarios(location, cuts, false, replayAt, "pcmc");
          setScenario(result);
          setSaveState("unsaved");
          setSaveMessage("Scenario calculated using the existing API; database persistence is unavailable.");
        }
      }
      setAppliedCuts({ ...cuts });
      setAfter(true);
      setFrameIndex(0);
      setAction("combined");
    } catch {
      setError("Scenario calculation failed. Your previous results have been preserved.");
    } finally {
      setRunning(false);
    }
  }

  if (!data || !location) {
    return <main className="tw-startup" role="status">
      <RefreshCw className="tw-spin" size={28} />
      <h1>AirTwin is preparing the city workspace</h1>
      <p>Loading Pune–PCMC air-quality references and model layers.</p>
      {error && <button onClick={() => setReload((n) => n + 1)}>Try again</button>}
    </main>;
  }
  return (
    <main className="tw-shell">
      <a className="tw-skip-link" href="#tw-content">Skip to city dashboard</a>
      <div className="tw-main" id="tw-content">
        <header className="fv-topbar">
          <div className="fv-topbar-inner">
            <a className="fv-brand" href="#tw-content" aria-label="AirTwin city overview" onClick={() => setView("overview")}>
              <span className="fv-brand-symbol"><Leaf size={18} strokeWidth={1.8}/></span>
              <span className="fv-brand-name">AirTwin</span>
              <span className="fv-build-label">ENR / 01</span>
            </a>
            <nav className="fv-nav" aria-label="AirTwin workspace views">
              {NAV.map(({ id, label }) => (
                <button type="button" key={id} className={"fv-nav-link" + (view === id ? " is-active" : "")}
                  aria-current={view === id ? "page" : undefined} onClick={() => navigateTo(id)}>
                  {label}
                </button>
              ))}
            </nav>
            <div className="fv-top-actions">
              <span className="fv-region-tag"><span className="tw-status-dot"/>Pune / PCMC</span>
              <button type="button" className="tw-icon-button" title="Refresh dataset" aria-label="Refresh dataset"
                onClick={() => setReload((n) => n + 1)}>
                <RefreshCw size={16} className={loading ? "tw-spin" : ""}/>
              </button>
              <AskAirTwin location={location} demo={data.demo} replayAt={replayAt} region="pcmc" cuts={appliedCuts} hours={hours}/>
            </div>
          </div>
        </header>
        <div className="tw-body">
          <div className="tw-introduction">
            <div className="fv-hero-copy">
              <div className="tw-overline"><span className="tw-live-dot"/> URBAN ENVIRONMENTAL INTELLIGENCE · PUNE / PCMC</div>
              <h1>Read the air.<span> Shape what happens next.</span></h1>
              <p>From pollution observations to modeled forecasts and intervention comparisons. Every prediction keeps its evidence, timestamp and limitations visible.</p>
              <div className="tw-hero-actions">
                <button type="button" className="tw-primary-action" onClick={() => navigateTo("scenarios")}>Compare interventions <ArrowRight size={16}/></button>
                <button type="button" className="tw-secondary-action" onClick={() => navigateTo("forecast")}>Explore forecast <Activity size={16}/></button>
              </div></div>
            <div className="tw-provenance-key" aria-label="Evidence provenance legend"><span className="fv-key-label">EVIDENCE KEY</span>
              <DataBadge source="observed"/><DataBadge source="modeled"/><DataBadge source="synthetic"/>
            </div>
          </div>

          {(data.warning || stale || replayAt) && <div className={"tw-banner" + (stale || data.demo ? " is-caution" : "")} role="status">
            <TriangleAlert size={17}/>
            <div>
              {replayAt && <strong>Historical replay · {dateLabel(replayAt)}, {timeLabel(replayAt)} IST. </strong>}
              {stale && !replayAt && <strong>Historical or stale snapshot — not a live street-level measurement. </strong>}
              {data.warning && <span>{data.warning}</span>}
            </div>
            {data.demo && <button onClick={() => setReload((n) => n + 1)}>Retry API</button>}
          </div>}

          <div className="fv-section-divider"><span>01 / CITY READOUT</span><span>Reference values · {dateLabel(location.timestamp)}</span></div>
          <section className="tw-kpis" aria-label="City workspace metrics">
            <div className="tw-kpi tw-kpi-main">
              <span><Wind size={16}/> SELECTED PM2.5 <DataBadge source={location.source_type}/></span>
              <div><strong>{number(location.pm25)}</strong><small>µg/m³</small></div>
              <p>{location.short_name} · {timeLabel(location.timestamp)} IST</p>
            </div>
            <div className="tw-kpi">
              <span><CloudSun size={16}/> +24H OUTLOOK <DataBadge source="modeled"/></span>
              <div><strong>{future24 == null ? "—" : number(future24)}</strong><small>µg/m³</small></div>
              <p>Projection from the selected origin</p>
            </div>
            <div className="tw-kpi">
              <span><GitCompareArrows size={16}/> POTENTIAL REDUCTION <DataBadge source="modeled"/></span>
              <div><strong>{selected ? number(selected.reduction_percent) : "—"}</strong><small>%</small></div>
              <p>{selected ? selected.name : "Awaiting analysis"} · assumed action</p>
            </div>
            <div className="tw-kpi">
              <span><ShieldCheck size={16}/> HISTORICAL MAE <DataBadge source="modeled"/></span>
              <div><strong>{backtest?.metrics ? number(backtest.metrics.mae) : "—"}</strong><small>µg/m³</small></div>
              <p>{backtest?.metrics ? (backtest.metrics.improvement_percent >= 0 ? "Compared with persistence baseline" : "Underperforms persistence on this holdout") : view === "validation" ? "No held-out metrics for this location" : "Open Validation to load historical evidence"}</p>
            </div>
          </section>

          <div className="fv-section-divider"><span>02 / SPATIAL WORKSPACE</span><span>Observed inputs · modeled output</span></div>
          <div className="tw-workspace">
            <div className="tw-map-column">
              <section className="tw-map-panel" id="pollution-map" aria-label="PM2.5 hotspot exploration">
                <div className="tw-panel-heading"><div>
                  <div className="tw-eyebrow">SPATIAL INTELLIGENCE</div>
                  <h2>Pollution hotspots <span>· Pune–PCMC</span></h2>
                </div>
                <div className="tw-toolbar">
                  <button className={replayAt ? "tw-small-button active" : "tw-small-button"} disabled={data.demo} onClick={toggleReplay}>{replayAt ? "Exit historical replay" : "Replay history"}</button>
                  <span className="tw-grid-badge">{data.cells.length} modeled cells</span>
                </div></div>
                <Suspense fallback={<div className="tw-map-loading" role="status">Preparing interactive pollution map…</div>}>
                <MapView
                  stations={mapStations}
                  cells={mapCells}
                  selected={location}
                  onSelect={chooseLocation}
                  after={!frame && after && Boolean(selected)}
                  onAfter={toggleAfter}
                  dark={false}
                  demo={data.demo}
                  weather={location.weather?.source_type ? location.weather : data.weather}
                  zones={data.zones}
                  zonesSourceType={data.zones_source_type}
                  region={data.region}
                  forecastLabel={frame ? "+" + frame.hour + "h modeled forecast" : null}
                  timeline={timelineControl}
                />
                </Suspense>
                <div className="tw-map-caption">
                  <span><CheckCircle2 size={14}/> Each station retains its source type and timestamp</span>
                  <span>Hotspot grid = modeled interpolation, not observed sensors</span>
                </div>
              </section>

              <div className="tw-bottom-cards">
                <section className="tw-mini-panel">
                  <div className="tw-mini-title"><span><MapPin size={16}/> Highest modeled cells</span><DataBadge source="modeled"/></div>
                  {hotCells.map((cell, index) => (
                    <button key={cell.id} className="tw-hotspot-row" onClick={() => chooseLocation({
                      id: cell.id, name: "Grid cell " + cell.id.replace("cell-", ""), short_name: "Modeled grid cell",
                      latitude: cell.latitude, longitude: cell.longitude,
                      pm25: cell.pm25, timestamp: location.timestamp, source_type: "modeled",
                      assumptions: cell.assumptions,
                    })}>
                      <b>{String(index + 1).padStart(2, "0")}</b><span>{cell.id.replace("cell-", "Grid ")}</span>
                      <strong>{number(cell.pm25)} <small>µg/m³</small></strong><ChevronRight size={14}/>
                    </button>
                  ))}
                </section>
                <section className="tw-mini-panel">
                  <div className="tw-mini-title"><span><Database size={16}/> Data provenance</span><CircleHelp size={15}/></div>
                  <div className="tw-provenance-counts">
                    <div><strong>{counts.observed}</strong><span>Observed station readings</span></div>
                    <div><strong>{counts.modeled}</strong><span>Modeled reference locations</span></div>
                    <div><strong>{counts.synthetic}</strong><span>Synthetic locations</span></div>
                  </div>
                  <div className="tw-db-state"><span className={storage?.connected ? "tw-db-online" : "tw-db-offline"}/>
                    {storage?.connected ? "PostgreSQL connected · " + storage.runs + " saved decision runs" : "Decision store " + (storage?.configured ? "unavailable" : "not configured")}
                  </div>
                  <p>CAMS samples, gridded estimates and scenarios remain explicitly <b>MODELED</b>.</p>
                </section>
              </div>
            </div>

            <aside className="tw-inspector" id="analysis-panel" aria-label="Selected location analysis">
              <div className="tw-inspector-header">
                <div className="tw-eyebrow">03 / LOCAL DECISION STUDIO</div>
                <h2>{location.short_name}</h2>
                <div className="tw-selection-caption"><DataBadge source={location.source_type} detail="BASELINE"/> · {dateLabel(location.timestamp)} {timeLabel(location.timestamp)} IST</div>
                <label className="tw-location-search"><Search size={16}/>
                  <input aria-label="Search locations" placeholder="Search locations..." value={search} onChange={(e) => setSearch(e.target.value)}/>
                </label>
                <select aria-label="Selected location" value={selectedGrid ? "selected-grid" : location.id} onChange={(event) => {
                  const next = data.stations.find((s) => s.id === event.target.value);
                  if (next) chooseLocation(next);
                }}>
                  {selectedGrid && <option value="selected-grid">{selectedGrid.name}</option>}
                  {filtered.map((item) => <option key={item.id} value={item.id}>{item.name} · {item.source_type}</option>)}
                  {!filtered.length && <option value={location.id}>{location.name}</option>}
                </select>
              </div>
              <div className="tw-section-tabs" role="tablist" aria-label="Analytical views">
                {NAV.map(({ id, label }) => <button key={id} type="button" role="tab" id={"tw-tab-" + id} aria-controls="tw-analysis-content" aria-selected={view === id}
                  onClick={() => navigateTo(id)} className={view === id ? "selected" : ""}>{label.split(" ")[0]}</button>)}
              </div>
              <div className="tw-inspector-content" id="tw-analysis-content" role="tabpanel" aria-labelledby={"tw-tab-" + view}>
                <Suspense fallback={<div className="tw-loading" role="status">Loading visualization…</div>}>
                {error && <ModelNotice>{error} <button onClick={() => setReload((n) => n + 1)}>Retry</button></ModelNotice>}
                {analysisLoading && <div className="tw-loading" role="status"><RefreshCw className="tw-spin" size={17}/> Updating analytical context…</div>}
                {view === "overview" && <div className="tw-overview">
                  <div className="tw-eyebrow">WHAT THE EVIDENCE SAYS</div>
                  <h3>From city map to practical choices</h3>
                  <p className="tw-copy">Explore forecasted PM2.5, likely source contributions and modeled policy outcomes for this selected location.</p>
                  <div className="tw-overview-step"><span>01</span><div><strong>Predict what changes</strong><p>{hours}-hour modeled outlook with uncertainty intervals and an origin timestamp.</p></div><button aria-label="Open forecast" onClick={() => navigateTo("forecast")}><ArrowRight size={17}/></button></div>
                  <div className="tw-overview-step"><span>02</span><div><strong>Explore source hypotheses</strong><p>Traffic, industry, dust and background based on configured spatial proxies.</p></div><button aria-label="Open source analysis" onClick={() => navigateTo("sources")}><ArrowRight size={17}/></button></div>
                  <div className="tw-overview-step"><span>03</span><div><strong>Compare interventions</strong><p>Rank three individual actions and their combined modeled effect.</p></div><button aria-label="Open interventions" onClick={() => navigateTo("scenarios")}><ArrowRight size={17}/></button></div>
                  <div className="tw-compact-summary">
                    <span>Selected area's potential modeled benefit</span>
                    <div><strong>{selected ? number(selected.reduction) : "—"}</strong><small>µg/m³</small></div>
                    <p>{selected ? number(selected.reduction_low) + "–" + number(selected.reduction_high) + " µg/m³ sensitivity range" : "No result available"}</p>
                  </div>
                  {backtest?.metrics && backtest.metrics.improvement_percent < 0 &&
                    <ModelNotice>Model MAE is worse than persistence for this holdout. Do not interpret the forecast as verified superior.</ModelNotice>}
                  <AssumptionsPanel assumptions={location.assumptions} title="Input provenance and limitations"/>
                </div>}
                {view === "forecast" && (forecast
                  ? <><ForecastChart data={forecast} hours={hours} onHours={setHours} demo={data.demo} replay={Boolean(replayAt)}/>
                    {forecast.history_reference?.startsWith("pune-cams") && <ModelNotice>CAMS provider forecast, not independently validated LightGBM at this point.</ModelNotice>}</>
                  : <div className="tw-empty">Forecast for this location is unavailable.</div>)}
                {view === "sources" && <div>
                  <div className="tw-inspector-intro"><div className="tw-eyebrow">SOURCE HYPOTHESES</div>
                    <p>These are proxy-based shares, not a chemical source-apportionment study or causal attribution.</p></div>
                  {attribution ? <AttributionChart data={attribution}/> : <div className="tw-empty">Source analysis unavailable.</div>}
                  <div className="tw-source-note"><strong>Included contributors</strong>
                    <p>{SOURCE_NAMES.join(" · ")}</p>
                    <DataBadge source="modeled" detail="ASSUMED WEIGHTS"/>
                  </div>
                </div>}
                {view === "scenarios" && <div>
                  <div className="tw-inspector-intro"><div className="tw-eyebrow">POLICY SIMULATOR</div>
                    <p>Set hypothetical reductions and compare four outcomes. Results are conditional model estimates.</p></div>
                  {scenario && selected
                    ? <ScenarioPanel cuts={cuts} onCuts={setCuts} response={scenario}
                        selected={selected} onSelect={setAction} onRun={runIntervention}
                        outdated={dirty} busy={running} inputSource={location.source_type}/>
                    : <div className="tw-empty">Intervention calculations unavailable.</div>}
                  {saveState !== "none" && <div role="status" className={"tw-save-note " + saveState}>
                    {saveState === "saved" ? <CheckCircle2 size={16}/> : <TriangleAlert size={16}/>}
                    <span>{saveMessage}</span></div>}
                  <ModelNotice>Estimated benefits use assumed pass-through, proxy source shares and synthetic population weights. They are not measured policy outcomes.</ModelNotice>
                </div>}
                {view === "validation" && <div>
                  <div className="tw-inspector-intro"><div className="tw-eyebrow">EVIDENCE CHECK</div>
                    <p>Look at held-out historical prediction error, persistence comparisons and uncertainty coverage.</p></div>
                  {backtest?.available === false && !data.demo && !replayAt
                    ? <div className="tw-validation-gate">
                        <ShieldCheck size={27}/>
                        <h3>Validate the AirTwin model separately</h3>
                        <p>This live Pune–PCMC layer uses CAMS provider output, which has no local held-out validation here. The separate historical LightGBM model was evaluated on past station observations; its accuracy must not be presented as CAMS accuracy.</p>
                        <button onClick={toggleReplay}>Open historical model validation <ArrowRight size={15}/></button>
                      </div>
                    : backtest ? <BacktestChart data={backtest} demo={data.demo}/> : <div className="tw-empty">Historical evaluation unavailable.</div>}
                </div>}
                </Suspense>
              </div>
              <div className="tw-inspector-footer"><ArrowDownRight size={16}/> Interpretation is for decision support only. Always inspect data age, provenance and model limitations.</div>
            </aside>
          </div>
          <footer className="tw-footer"><span>AirTwin / Dot.local — ENR–01 Urban Environmental Digital Twin</span><span>OpenAQ · CAMS · Open-Meteo · LightGBM · proxy scenarios</span></footer>
        </div>
      </div>
    </main>
  );
}
