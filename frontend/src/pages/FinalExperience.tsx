import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowRight, ArrowUpRight, ChevronDown, ChevronRight, CloudMoon,
  CloudSun, Compass, Info, Layers, Leaf, LockKeyhole, MapPin, Moon, RefreshCw,
  ShieldCheck, Sparkles, Sun, TrendingDown, Wind, X,
} from "lucide-react";
import { Area, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DashboardData, ExplainResponse, ForecastResponse, Station, TimelineResponse } from "../types";
import { api, loadDashboard } from "../lib/api";
import { DEFAULT_CUTS } from "../mocks/engine";
import { dateLabel, number, timeLabel } from "../lib/format";
import { alignedForecastFrame, cellsAtFrame } from "../lib/finalTimeline";
import { readRoute, writeRoute, resolveRouteStation } from "../lib/finalRoute";
import { forecastReferenceRange, selectedForecastPeak } from "../lib/finalOutlook";
import {
  concentrationLabel, interpretChange, isStale, METRICS,
  orderedPlaces, provenanceLabel, rankedReferences, referenceName, readingFor, supportsMetric,
  type MetricId,
} from "../lib/finalMetrics";
import "../final.css";

const FinalMap = lazy(async () => ({
  default: (await import("../components/FinalMap")).FinalMap,
}));
const ResearchWorkbench = lazy(async () => ({
  default: (await import("../components/ResearchWorkbench")).ResearchWorkbench,
}));
type Page = "overview" | "map" | "forecast";
type Subview = "explore" | "analytics";

function routeFromURL(): Page {
  return readRoute(window.location.search).page;
}
function isPage(value: string): value is Page {
  return value === "overview" || value === "map" || value === "forecast";
}
function sourcePill(source: string, stale = false) {
  return source.toUpperCase() + (stale ? " · STALE" : "");
}
function formatStamp(value?: string | null): string {
  if (!value || !Number.isFinite(Date.parse(value))) return "Time unavailable";
  return dateLabel(value) + " · " + timeLabel(value) + " IST";
}
function advice(value: number | null): string {
  if (value === null) return "Check provider availability before planning outdoor activity.";
  if (value > 60) return "Fine particles are elevated here. Consider reducing prolonged outdoor exertion and using a well-fitted N95 outdoors.";
  if (value > 30) return "Consider less traffic-exposed routes and check updated readings before long outdoor activity.";
  return "Check current readings before heading out; conditions and individual sensitivity can change.";
}
function CoverageDetails({ data, locationId }: { data: DashboardData; locationId?: string }) {
  if (data.demo || !data.coverage) return null;
  const coverage = data.coverage;
  const support = data.cells.find((cell) => cell.id === locationId)?.measurement_support;
  return <section className="fv-coverage" aria-label="Measurement coverage">
    <strong>{Number(coverage.observed_points ?? 0)} fresh PM2.5 monitors · {Number(coverage.synchronized_monitor_count ?? 0)} contribute to this map hour</strong>
    <p>CAMS covers roughly {Number(coverage.native_model_resolution_km ?? 45)} km. Neighborhood differences and local error remain unvalidated.</p>
    {support?.nearest_monitor_km != null && <p>Nearest fresh monitor: {number(support.nearest_monitor_km)} km away, measured {formatStamp(support.nearest_monitor_timestamp)}.</p>}
    <details className="fv-disclosure"><summary>Coverage and local model readiness</summary>
      <p>Measurements must be within 24 hours. Only measurements from the model's hour enter the surface; other fresh readings remain separate monitor markers.</p>
      <p>{Number(coverage.discovered_pm25_sensors ?? 0)} OpenAQ sensors discovered. {Number(coverage.monitor_check_failures ?? 0)} location checks failed in the last refresh.</p>
      <p>{Number(coverage.training_observed_hours ?? 0)} cached measured hours across {Number(coverage.training_monitor_count ?? 0)} monitors in the last 30 days. Longest sensor history: {Number(coverage.largest_monitor_history_hours ?? 0)} hours.</p>
      <p>The station benchmark needs 240 complete 24-hour prediction pairs, plus exact historical lags and separate fit, selection and test periods. A finer spatial model also needs validation on withheld monitors before release.</p>
      <p>No calibrated uncertainty interval is available for this map. Traffic and land-use assumptions do not establish local pollution causes.</p>
    </details>
  </section>;
}

function futureAt(data: ForecastResponse | null, hours: number) {
  if (!data) return null;
  const future = data.series.filter((point) => point.predicted !== null);
  return future[Math.min(hours, future.length) - 1] ?? null;
}
function SkyIcon({ night }: { night: boolean }) {
  return night ? <Moon size={17}/> : <Sun size={17}/>;
}

function ForecastTrend({ forecast, demo }: { forecast: ForecastResponse | null; demo: boolean }) {
  const rows = forecast?.series.map((point) => ({
    ...point, stamp: point.timestamp,
    band: point.p10 !== null && point.p90 !== null ? [point.p10, point.p90] : null,
  })) ?? [];
  return <section className="fv-chart-shell">
    <div className="fv-chart-caption"><span className="fv-key"><i className="fv-key-history"/> {forecast?.history_source_type.toUpperCase() ?? "HISTORY"}</span>
      <span className="fv-key"><i className="fv-key-future"/> {demo ? "SYNTHETIC" : "MODELED"} forecast</span></div>
    {!rows.length ? <div className="fv-chart-empty">Waiting for a supported PM2.5 forecast.</div> :
      <div className="fv-chart" role="img" aria-label="Historical and projected PM2.5 concentration time series in micrograms per cubic metre">
        <ResponsiveContainer width="100%" height="100%" initialDimension={{width: 440, height: 240}}>
          <ComposedChart data={rows} margin={{top: 10, right: 5, bottom: 2, left: -22}}>
            <CartesianGrid stroke="#dbe5e5" strokeDasharray="3 6" vertical={false}/>
            <XAxis dataKey="stamp" minTickGap={65} tickLine={false} axisLine={false} tick={{fill:"#698197",fontSize:10}}
              tickFormatter={(t: string) => timeLabel(t)}/>
            <YAxis tickLine={false} axisLine={false} tick={{fill:"#698197",fontSize:10}}/>
            <Tooltip labelFormatter={(label) => formatStamp(String(label))}
              contentStyle={{borderRadius:14,border:"1px solid #dce7eb",fontSize:12}}
              formatter={(value, name) => [Array.isArray(value) ? value.map((v) => number(Number(v))).join("–") : number(Number(value)) + " µg/m³", String(name)]}/>
            <Area dataKey="band" name="Modeled interval" fill="#67b7d0" fillOpacity={0.18} stroke="none" isAnimationActive={false}/>
            <Line type="monotone" dataKey="actual" name="Historical values" stroke="#198a8c" strokeWidth={2.4} connectNulls={false} dot={false} isAnimationActive={false}/>
            <Line type="monotone" dataKey="predicted" name="Modeled forecast" stroke="#216cc0" strokeWidth={2.7}
              strokeDasharray="6 3" dot={false} connectNulls={false} isAnimationActive={false}/>
          </ComposedChart>
        </ResponsiveContainer>
      </div>}
  </section>;
}

export function FinalExperience() {
  const [page, setPage] = useState<Page>(() => routeFromURL());
  const [subview, setSubview] = useState<Subview>(() => readRoute(window.location.search).view);
  const [entered, setEntered] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    return window.sessionStorage.getItem("airtwin-guest-entry") === "1" || isPage(params.get("page") ?? "") && params.has("page");
  });
  const [authNotice, setAuthNotice] = useState(false);
  const [data, setData] = useState<DashboardData | null>(null);
  const [refresh, setRefresh] = useState(0);
  const [selected, setSelected] = useState<Station | null>(null);
  const [focus, setFocus] = useState(false);
  const [metric, setMetric] = useState<MetricId>(() => readRoute(window.location.search).metric);
  const [metricOpen, setMetricOpen] = useState(false);
  const [rankOpen, setRankOpen] = useState(false);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [hours, setHours] = useState<24 | 48 | 72>(() => readRoute(window.location.search).hours);
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [timeline, setTimeline] = useState<TimelineResponse | null>(null);
  const [timelineError, setTimelineError] = useState("");
  const [forecastBusy, setForecastBusy] = useState(false);
  const [forecastError, setForecastError] = useState("");
  const [timeIndex, setTimeIndex] = useState(23);
  const [effectsOn, setEffectsOn] = useState(true);
  const [question, setQuestion] = useState("");
  const [answeredQuestion, setAnsweredQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [answerMeta, setAnswerMeta] = useState("");
  const [answerClaims, setAnswerClaims] = useState<ExplainResponse["claims"]>([]);
  const [answerNotes, setAnswerNotes] = useState<string[]>([]);
  const [asking, setAsking] = useState(false);
  const answerRequest = useRef(0);
  useEffect(() => {
    answerRequest.current += 1;
    setAnswer("");setAnswerClaims([]);setAnswerNotes([]);setApiError("");setAsking(false);
  }, [selected?.id, metric]);
  const [apiError, setApiError] = useState("");
  const [mobilePanel, setMobilePanel] = useState(() => window.innerWidth > 640);
  const displayMetric = page === "map" ? metric : "pm25";
  const displayMetricInfo = METRICS.find((item) => item.id === displayMetric)!;

  const navigate = useCallback((next: Page, options?: {tab?: Subview; metricMenu?: boolean; ranked?: boolean; location?: Station | null; pollutant?: MetricId}) => {
    const url = writeRoute(new URL(window.location.href), {
      page: next,
      view: options?.tab ?? "explore",
      ...(options?.pollutant ? {metric: options.pollutant} : {}),
      ...(options?.location ? {location: options.location.id} : {}),
    });
    window.history.pushState(null, "", url);
    setPage(next);
    if (options?.pollutant) setMetric(options.pollutant);
    setSubview(options?.tab ?? "explore");
    setMetricOpen(Boolean(options?.metricMenu));
    setRankOpen(Boolean(options?.ranked));
    setDetailsOpen(Boolean(options?.ranked));
    if (options?.location) setSelected(options.location);
    if (next !== "forecast") setFocus(false);
    setMobilePanel(window.innerWidth > 640);
  }, []);
  useEffect(() => {
    const onPop = () => {
      const route = readRoute(window.location.search);
      setPage(route.page);
      setSubview(route.view);
      setMetric(data && !supportsMetric(data, route.metric) ? "pm25" : route.metric);
      setHours(route.hours);
      if (data) setSelected(resolveRouteStation(data, route.location));
      setDetailsOpen(false);
      setRankOpen(false);
      setMetricOpen(false);
      setFocus(false);
    };
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, [data]);
  useEffect(() => {
    const onEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setMetricOpen(false);
        setRankOpen(false);
        setDetailsOpen(false);
      }
    };
    window.addEventListener("keydown", onEscape);
    return () => window.removeEventListener("keydown", onEscape);
  }, []);
  useEffect(() => {
    let active = true;
    loadDashboard().then((result) => {
      if (!active) return;
      setData(result);
      const route = readRoute(window.location.search);
      setMetric(supportsMetric(result, route.metric) ? route.metric : "pm25");
      setSelected((previous) => resolveRouteStation(result, route.location ?? previous?.id ?? null));
    }).catch(() => {});
    return () => { active = false; };
  }, [refresh]);
  useEffect(() => {
    const timer = window.setInterval(() => setRefresh((count) => count + 1), 15 * 60 * 1000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!selected || !data) return;
    let active = true;
    setForecastBusy(true);
    setForecastError("");
    setForecast(null);
    api.forecast(selected, data.demo, hours).then((result) => {
      if (active) setForecast(result);
    }).catch((error: unknown) => {
      if (active) setForecastError(error instanceof Error ? error.message : "Forecast unavailable");
    }).finally(() => {if (active) setForecastBusy(false);});
    return () => { active = false; };
  }, [selected, data?.demo, hours]);
  useEffect(() => {
    if (page !== "forecast") return;
    if (!data || data.demo) {setTimeline(null); return;}
    let active = true;
    setTimelineError("");
    setTimeline(null);
    api.timeline(null, "pcmc").then((result) => {
      if (active) setTimeline(result);
    }).catch((error: unknown) => {
      if (active) {setTimeline(null);setTimelineError(error instanceof Error ? error.message : "Spatial forecast unavailable");}
    });
    return () => {active = false;};
  }, [page, data]);
  useEffect(() => {setTimeIndex(Math.min(hours - 1, 23));}, [hours]);
  useEffect(() => {setAnswer("");setAnswerMeta("");}, [selected?.id]);

  const sorted = useMemo(() => data ? orderedPlaces(data.stations, displayMetric, data.demo) : [], [data, displayMetric]);
  const references = useMemo(() => data ? rankedReferences(data.stations, displayMetric, data.demo) : [], [data, displayMetric]);
  const topReference = references[0];
  const selectedReference = references.find((group) => group.locations.some((location) => location.id === selected?.id));
  const top = sorted[0] ?? null;
  const primary = selected && data ? readingFor(selected, displayMetric, data.demo) : null;
  const allPM = useMemo(() => data ? rankedReferences(data.stations.filter((station) => station.source_type !== "observed"), "pm25", data.demo) : [], [data]);
  const meanPM = allPM.length ? allPM.reduce((sum, group) => sum + group.reading.value, 0) / allPM.length : null;
  const when = forecast?.series.filter((point) => point.predicted !== null)[Math.min(timeIndex, hours - 1)] ?? null;
  const first = selected?.pm25 ?? null;
  const tomorrow = futureAt(forecast, 24);
  const trend = interpretChange(first, tomorrow?.predicted ?? null);
  const tomorrowChange = first !== null && tomorrow?.predicted != null
    ? `${tomorrow.predicted - first > 0 ? "+" : ""}${number(tomorrow.predicted - first)} µg/m³ vs latest reference` : "Change unavailable";
  const selectedTime = when?.timestamp || tomorrow?.timestamp;
  const localHour = selectedTime ? Number(new Intl.DateTimeFormat("en-GB", {timeZone:"Asia/Kolkata",hour:"2-digit",hourCycle:"h23"}).format(new Date(selectedTime))) : 12;
  const night = page === "forecast" && (localHour < 6 || localHour >= 19);
  const selectedWeather = forecast?.weather_forecast?.find((weather) =>
    selectedTime && Math.abs(Date.parse(weather.timestamp) - Date.parse(selectedTime)) < 3600000);
  const haze = when?.predicted !== null && when?.predicted !== undefined && when.predicted > 60;
  const cloudy = selectedWeather?.cloud_cover !== undefined && selectedWeather.cloud_cover >= 65;
  const atmosphere = night && effectsOn
    ? cloudy ? "cloudy" : haze ? "hazy" : selectedWeather ? "clear" : "off"
    : "off";
  const spatialFrame = alignedForecastFrame(timeline, forecast, timeIndex);
  const forecastCells = useMemo(() => data ? cellsAtFrame(data.cells, spatialFrame) : null, [data, spatialFrame]);
  const spatialTimestamp = forecastCells && spatialFrame?.hour ? formatStamp(spatialFrame.timestamp) : null;
  const dayReferenceRange = useMemo(() => {
    const dayFrame = alignedForecastFrame(timeline, forecast, 23);
    return forecastReferenceRange(dayFrame?.hour === 24 ? dayFrame : null, data?.stations ?? []);
  }, [timeline, forecast, data]);
  const selectedPeak = useMemo(() => selectedForecastPeak(forecast), [forecast]);
  const avgStale = data?.stations[0] ? isStale(data.stations[0].timestamp) : true;
  const topReading = top && data ? readingFor(top, displayMetric, data.demo) : null;

  const chooseMetric = (id: MetricId) => {
    if (!data || !supportsMetric(data, id)) return;
    setMetric(id);
    window.history.replaceState(null, "", writeRoute(new URL(window.location.href), {metric: id}));
    setMetricOpen(false);
    setRankOpen(false);
  };
  const chooseLocation = (station: Station) => {
    setSelected(station);
    window.history.replaceState(null, "", writeRoute(new URL(window.location.href), {location: station.id}));
    setDetailsOpen(true);
    setMobilePanel(window.innerWidth > 640);
    if (page === "forecast") setFocus(true);
  };
  const enter = () => { window.sessionStorage.setItem("airtwin-guest-entry","1"); setEntered(true); };

  const ask = async () => {
    if (!selected || !data || !question.trim()) return;
    setAnsweredQuestion(question.trim());
    setAnswerClaims([]);setAnswerNotes([]);
    if (data.demo) {
      setAnswer("The backend is unavailable; these readings are synthetic demonstration values. A grounded AI response cannot be generated.");
      setAnswerMeta("OFFLINE DEMO · NO AI REQUEST");
      return;
    }
    const requestId = ++answerRequest.current;
    setAsking(true);setApiError("");setAnswer("");
    try {
      const result = await api.explain(selected.id, question.trim(), null, "pcmc", DEFAULT_CUTS, hours, [], metric);
      if (requestId !== answerRequest.current) return;
      setAnswer(result.answer);
      setAnswerClaims(result.claims);
      setAnswerNotes(result.assumptions);
      setAnswerMeta((result.method === "gemini_evidence_checked" ? "Gemini · " + result.model : "Evidence summary · AI unavailable") + " · " + selected.short_name);
    } catch (error) {
      if (requestId !== answerRequest.current) return;
      setApiError(error instanceof Error ? error.message : "Assistant unavailable");
      const reading = readingFor(selected, metric, data.demo);
      setAnswer("Live AI is unavailable. " + selected.name + (reading
        ? " has a " + sourcePill(reading.source,reading.stale) + " " + METRICS.find((item) => item.id === metric)?.label + " reference value of " + number(reading.value) + " " + reading.unit + " at " + formatStamp(reading.timestamp)
        : " has no supported reading for the selected pollutant") +
        ". This reading alone does not establish a causal pollution source or guarantee a safe activity.");
      setAnswerMeta("LOCAL EVIDENCE SUMMARY · NOT AN AI RESPONSE");
    } finally {if (requestId === answerRequest.current) setAsking(false);}
  };

  if (!entered) return <div className="fv-welcome">
    <div className="fv-welcome-bg"><span className="fv-welcome-line"/><div className="fv-welcome-map" aria-hidden="true"/></div>
    <header className="fv-welcome-header"><div className="fv-brand"><span className="fv-brand-icon"><Wind size={22}/></span><strong>AirTwin</strong></div><span>Pune + Pimpri-Chinchwad</span></header>
    <main className="fv-welcome-content">
      <div className="fv-welcome-copy"><span className="fv-eyebrow"><span className="fv-dot"/> YOUR CITY, CLEARER</span>
        <h1>Know your air.<br/><em>Shape your city.</em></h1>
        <p>Explore real measurements when available, modeled pollution patterns, and tomorrow’s outlook for Pune and PCMC.</p>
        <div className="fv-welcome-benefits"><span><MapPin size={15}/> Explore your area</span><span><Layers size={15}/> Understand the data</span><span><CloudSun size={15}/> See the outlook</span></div>
      </div>
      <section className="fv-entry-card"><div className="fv-entry-visual"><Wind size={27}/></div><span className="fv-eyebrow">WELCOME TO AIRTWIN</span><h2>Explore your city</h2><p>No account needed to see the latest available air-quality information.</p>
        <button type="button" className="fv-button fv-primary fv-wide" onClick={enter}>Explore as guest <ArrowRight size={18}/></button>
        <div className="fv-entry-divider"><span>ACCOUNT ACCESS</span></div>
        <button type="button" className="fv-entry-option" onClick={() => setAuthNotice(true)}><span><ShieldCheck size={18}/> Public account</span><ChevronRight size={16}/></button>
        <button type="button" className="fv-entry-option" onClick={() => setAuthNotice(true)}><span><LockKeyhole size={18}/> PMC / PCMC employee</span><ChevronRight size={16}/></button>
        {authNotice && <div className="fv-info-alert" role="status">Secure account verification is not configured on the current API. Guest browsing works; government-only controls remain locked.</div>}
      </section>
    </main><footer className="fv-welcome-footer">OpenAQ observed data · CAMS/Open-Meteo modeled context · explicit synthetic fallback</footer>
  </div>;

  return <div className={"fv-app fv-desktop-scene fv-scene-" + page + (subview === "analytics" && page === "map" ? " fv-scene-analytics" : "") + (night ? " fv-scene-night" : "")}>
    <header className="fv-header">
      <div className="fv-header-start">
        <button className="fv-brand fv-reset" type="button" onClick={() => navigate("overview")} aria-label="AirTwin Overview">
          <span className="fv-brand-icon"><Wind size={20}/></span><strong>AirTwin</strong>
        </button>
      </div>
      <nav aria-label="Main navigation" className="fv-nav">{(["overview","map","analytics","forecast"] as const).map((item) =>
        <button key={item} type="button" className={(item === "analytics" ? page === "map" && subview === "analytics" : page === item && (item !== "map" || subview === "explore")) ? "active" : ""} aria-current={(item === "analytics" ? page === "map" && subview === "analytics" : page === item && (item !== "map" || subview === "explore")) ? "page" : undefined} onClick={() => item === "analytics" ? navigate("map", {tab:"analytics"}) : item === "map" ? navigate("map", {tab:"explore"}) : navigate(item)}>
          {item === "overview" ? <Compass size={15}/> : item === "map" ? <Layers size={15}/> : item === "analytics" ? <Sparkles size={15}/> : <CloudSun size={15}/>}
          {item.charAt(0).toUpperCase() + item.slice(1)}
        </button>)}</nav>
      <div className="fv-header-end">
        <button className="fv-refresh" type="button" aria-label="Refresh backend data" title="Refresh data" onClick={() => setRefresh((count) => count + 1)}><RefreshCw size={17}/></button>
        <span className={"fv-live-state" + (data?.demo || avgStale ? " is-stale" : "")}>
          <i/>{!data ? "Connecting" : data.demo ? "Demo data" : avgStale ? "Source may be stale" : "Provider snapshot"}
        </span>
        <button type="button" className="fv-profile" title="Accounts require verified server authentication" onClick={() => setAuthNotice(!authNotice)} aria-expanded={authNotice} aria-controls="fv-account-info"><Info size={14}/> Account info</button>
      </div>
    </header>
    {authNotice && <div id="fv-account-info" className="fv-account-warning" role="status"><LockKeyhole size={16}/> Sign-in and verified municipal roles require a secure authentication backend; access has not been enabled. <button type="button" aria-label="Close notice" onClick={() => setAuthNotice(false)}><X size={14}/></button></div>}
    <main className="fv-main">
      <div className="fv-page-heading">
        <div><span className="fv-eyebrow">{page === "overview" ? "YOUR CITY AT A GLANCE" : page === "map" ? "EXPLORE YOUR ENVIRONMENT" : "LOOKING AHEAD"}</span>
          <h1>{page === "overview" ? "A clearer view of your city." : page === "map" ? subview === "analytics" ? "Understand your air." : "Find your air." : focus && selected ? "Looking ahead · " + selected.short_name : "Tomorrow starts here."}</h1>
          <p>{page === "overview" ? "Pune and Pimpri-Chinchwad · Latest available pollution context" : page === "map" ? "Real monitors, modeled patterns, and the stories behind the numbers." : "Time-based PM2.5 projections, with their sources and uncertainty clearly marked."}</p></div>
        {data && <div className="fv-snapshot-chip"><span className={"fv-status-icon" + (data.demo ? " demo" : "")}/><div><strong>{data.demo ? "SYNTHETIC DEMO" : "PROVIDER DATA"}</strong><small>{formatStamp(data.stations[0]?.timestamp)}</small></div></div>}
      </div>
      {!data ? <div className="fv-loading" role="status"><RefreshCw size={24} className="fv-spin"/> Connecting to the environmental data service…</div> :
      <div className={"fv-workspace fv-" + page + (subview === "analytics" ? " fv-analytics" : "")}>
        <div className="fv-map-column">
          {page === "map" && <div className="fv-map-toolbar">
            <div className="fv-segment" role="group" aria-label="Map workspace">
              <button type="button" className={subview === "explore" ? "selected" : ""} onClick={() => {setSubview("explore");navigate("map",{tab:"explore"});}}>Explore</button>
              <button type="button" className={subview === "analytics" ? "selected" : ""} onClick={() => {setSubview("analytics");navigate("map",{tab:"analytics"});}}>Analytics</button>
            </div>
            <div className="fv-dropdown-container">
              <button type="button" className="fv-select-button" aria-expanded={metricOpen} onClick={() => {setMetricOpen(!metricOpen);setRankOpen(false);}}>{METRICS.find((item) => item.id === metric)?.label} <ChevronDown size={15}/></button>
              {metricOpen && <div className="fv-dropdown fv-metrics-menu" role="listbox" aria-label="Select pollutant">
                {METRICS.map((option) => {
                  const supported = supportsMetric(data, option.id);
                  return <button key={option.id} role="option" aria-selected={metric === option.id} type="button" disabled={!supported} title={supported ? option.description : "Unavailable: " + option.description}
                    onClick={() => chooseMetric(option.id)}>
                    <span>{option.label}</span><small>{supported ? option.unit : "Unavailable"}</small>
                  </button>;
                })}
              </div>}
            </div>
            {subview === "explore" && <div className="fv-dropdown-container">
              <button type="button" className="fv-select-button fv-ranked-btn" aria-expanded={rankOpen} onClick={() => {setRankOpen(!rankOpen);setMetricOpen(false);}}>Highest readings <ChevronDown size={15}/></button>
              {rankOpen && <div className="fv-dropdown fv-ranked-menu"><strong>{references.length} distinct provider readings</strong><small>Shared CAMS time series are grouped. The regional model cannot distinguish every neighborhood. Equal values share a rank.</small>
                {references.slice(0, 8).map((group) => <div className="fv-reference-group" key={group.locations[0].id}>
                  <button type="button" onClick={() => {chooseLocation(group.locations[0]);setRankOpen(false);}}><b>{group.rank}</b><span>{referenceName(group.locations)}</span><strong>{number(group.reading.value)} <small>{group.reading.unit}</small></strong></button>
                  {group.locations.length > 1 && <details><summary>Choose from {group.locations.length} covered areas</summary>{group.locations.map((station) => <button type="button" key={station.id} onClick={() => {chooseLocation(station);setRankOpen(false);}}>{station.short_name || station.name}</button>)}</details>}
                </div>)}
              </div>}
            </div>}
          </div>}
          {page === "forecast" && <div className="fv-map-toolbar">
            <span className="fv-select-button">PM2.5 <small>µg/m³</small></span>
            <div className="fv-segment" role="group" aria-label="Forecast horizon">{([24,48,72] as const).map((h) => <button key={h} type="button" className={hours === h ? "selected" : ""} onClick={() => {
              setHours(h);
              window.history.replaceState(null, "", writeRoute(new URL(window.location.href), {hours:h}));
            }}>{h}h</button>)}</div>
            <button type="button" className="fv-select-button fv-effects" aria-pressed={effectsOn} onClick={() => setEffectsOn(!effectsOn)}><SkyIcon night={night}/> Effects {effectsOn ? "on" : "off"}</button>
          </div>}
          <div className="fv-map-frame">
            <Suspense fallback={<div className="fv-map-loading" role="status">Loading the city map…</div>}>
              <FinalMap data={data} selected={selected} onSelect={chooseLocation} metric={displayMetric}
                widePanel={page === "map" && subview === "analytics"} night={night} focus={(focus && page === "forecast") || (detailsOpen && page === "map")} atmosphere={atmosphere} forecast={page === "forecast"}
                forecastCells={page === "forecast" ? forecastCells : null}
                forecastStations={page === "forecast" && spatialTimestamp ? spatialFrame?.stations : []}
                spatialTimestamp={page === "forecast" ? spatialTimestamp : null}
                onClearFocus={() => {setFocus(false);setDetailsOpen(false);}}/>
            </Suspense>
            {page === "overview" && <div className="fv-map-floating"><span className="fv-eyebrow">SPATIAL ESTIMATE</span><strong>Know where air is changing.</strong><span>{data.cells.length} interpolated cells · not additional monitors</span></div>}
            {page === "forecast" && <div className="fv-map-floating fv-forecast-overlay"><span className="fv-eyebrow">{night ? "EVENING OUTLOOK" : "FORECAST VIEW"}</span><strong>{selected?.short_name ?? "Pune + PCMC"}</strong><span>{spatialTimestamp ? "Modeled spatial forecast " + spatialTimestamp : "Spatial forecast unavailable · map shows modeled baseline"} · {data.demo ? "SYNTHETIC DEMO" : "IDW spatial layer"}</span></div>}
          </div>
          {page === "forecast" && <div className="fv-time-strip"><div className="fv-time-shortcuts"><button type="button" onClick={() => setTimeIndex(0)} disabled={!forecast || forecastBusy}>Next hour</button><button type="button" onClick={() => setTimeIndex(23)} disabled={!forecast || forecastBusy}>Tomorrow</button></div><span>Now · {formatStamp(forecast?.input_cutoff)}</span>
            <input type="range" min="0" max={Math.max(0, Math.min(hours, forecast?.series.filter((p) => p.predicted !== null).length ?? hours) - 1)} value={timeIndex} disabled={forecastBusy || !forecast}
              onChange={(event) => setTimeIndex(Number(event.target.value))} aria-label="Select forecast time" aria-valuetext={selectedTime ? formatStamp(selectedTime) : "Unavailable"}/>
            <span>Selected · {selectedTime ? formatStamp(selectedTime) : "Unavailable"}</span></div>}
          {page === "forecast" && <div className="fv-map-disclaimer"><Info size={13}/> {spatialTimestamp ? "Map shows the latest published frame at or before the selected time, up to 72 hours where available. The displayed map timestamp may differ from the hourly chart." : "Map uses the baseline when a time-aligned spatial forecast is unavailable."} {timelineError && "Spatial feed: " + timelineError}</div>}
          {page !== "forecast" && <div className="fv-map-disclaimer"><Info size={13}/> {displayMetric === "pm25" ? "Map grid is interpolated PM2.5, not a street-level monitor network." : "Reference points show " + displayMetricInfo.label + "; no modeled heat surface is available for this pollutant."} {data.demo && "All readings in this fallback are synthetic."}</div>}
        </div>
        <aside className={"fv-side" + (!mobilePanel ? " fv-side-collapsed" : "")}>
          <section className="fv-area-context" aria-label="Selected area summary"><div><small>{page === "overview" ? "Selected area · PM2.5" : "Selected area · " + displayMetricInfo.label}</small><strong>{selected?.short_name ?? "Choose an area"}</strong></div><div><strong>{primary ? number(primary.value) + " " + primary.unit : "Not reported"}</strong><small>{primary ? provenanceLabel(primary.source,primary.stale) + " · " + formatStamp(primary.timestamp) : "Select a supported reference"}</small></div></section>
          <button className="fv-mobile-panel" type="button" aria-expanded={mobilePanel} aria-controls="fv-page-details" onClick={() => setMobilePanel(!mobilePanel)}>{mobilePanel ? "Hide details" : "Show details"} <ChevronDown size={15}/></button>
          {page === "overview" && <div id="fv-page-details" className="fv-overview-cards">
            <button type="button" className="fv-card fv-card-primary" onClick={() => navigate("map", {metricMenu:true,pollutant:"pm25"})}>
              <span className="fv-card-kicker"><Wind size={16}/> Air today <ChevronRight size={17}/></span>
              <div className="fv-card-value"><strong>{meanPM !== null ? number(meanPM, 0) : "—"}</strong><div><span>µg/m³</span><small>PM2.5 · mean of {allPM.length} distinct model signals</small></div></div>
              <span className="fv-card-status">{meanPM !== null ? concentrationLabel(meanPM) : "Unavailable"}</span>
              <span className="fv-card-foot">{sourcePill(data.demo ? "synthetic" : "modeled",avgStale)} · Not an official AQI</span>
            </button>
            <button type="button" className="fv-card fv-hotspot-card" onClick={() => navigate("map", {ranked:true,pollutant:"pm25",location:orderedPlaces(data.stations,"pm25",data.demo)[0]})}>
              <span className="fv-card-kicker"><MapPin size={16}/> Highest PM2.5 reference <ChevronRight size={17}/></span>
              <div className="fv-card-text"><strong>{referenceName(topReference?.locations ?? [])}</strong>
                <span>{topReference?.locations.map((location) => location.short_name).slice(0,3).join(", ")}{(topReference?.locations.length ?? 0) > 3 ? " and more" : ""}</span></div>
              <span className="fv-card-foot">MODELED / OBSERVED provenance shown in Map</span>
            </button>
            <button type="button" className="fv-card fv-tomorrow-card" onClick={() => navigate("forecast")}>
              <span className="fv-card-kicker"><TrendingDown size={16}/> Tomorrow · {selected?.short_name ?? "selected area"} <ChevronRight size={17}/></span>
              <div className="fv-card-text"><strong>{forecastBusy ? "Loading…" : forecastError ? "Unavailable" : trend}</strong>
                <span>{tomorrow?.predicted !== null && tomorrow?.predicted !== undefined ? number(tomorrow.predicted) + " µg/m³ · " + tomorrowChange : "No supported prediction yet"}</span></div>
              <span className="fv-card-foot">{data.demo ? "SYNTHETIC" : "MODELED"} · {selected?.short_name ?? "Pune"}</span>
            </button>
            <button type="button" className="fv-overview-tips" onClick={() => navigate("map", {tab:"analytics",pollutant:"pm25"})}><Leaf size={18}/><span><strong>Area tips & AI</strong><small>{advice(selected?.pm25 ?? meanPM)}</small></span><ArrowRight size={16}/></button>
          </div>}
          {page === "map" && subview === "explore" && <div id="fv-page-details" className="fv-explore-panels">
            <div className="fv-card fv-insights"><span className="fv-card-kicker"><Layers size={16}/> Map insights</span>
              <h2>{selected?.short_name ?? "Explore an area"}</h2>
              <p>Values follow the selected pollutant and location.</p>
              {selectedReference && selectedReference.locations.length > 1 && <details className="fv-disclosure"><summary>Shared model reading · {selectedReference.locations.length} areas</summary><p>{selectedReference.locations.map((location) => location.short_name).join(", ")}. These locations share the same provider time series; the model does not establish differences between them.</p></details>}
              <div className="fv-reading-box"><span>{METRICS.find((item) => item.id === metric)?.label}</span><strong>{primary ? number(primary.value) : "Unavailable"} <small>{primary?.unit ?? ""}</small></strong>
                <span className="fv-provenance">{primary ? provenanceLabel(primary.source, primary.stale) : "NOT REPORTED"}</span></div>
              {primary && <small className="fv-reading-date">{formatStamp(primary.timestamp)}<br/>{primary.spatialSupport}</small>}
              <div className="fv-insight-rows">
                <div><span>Highest reference reading</span><strong>{referenceName(topReference?.locations ?? [])}</strong></div>
                <div><span>Reading</span><strong>{topReading ? number(topReading.value) + " " + topReading.unit : "Unavailable"}</strong></div>
                <div><span>Lowest reference reading</span><strong>{referenceName(references.at(-1)?.locations ?? [])}</strong></div>
              </div>
              {data.weather && <div className="fv-weather-summary"><Wind size={15}/> Wind {data.weather.wind_speed_10m !== undefined ? number(data.weather.wind_speed_10m * 3.6,0) + " km/h · MODELED" : "Unavailable"}</div>}
              <CoverageDetails data={data} locationId={selected?.id}/><div className="fv-note">Readings from different sources and timestamps are not an official synchronized citywide AQI.</div>
            </div>
            {detailsOpen && selected && <section className="fv-card fv-detail-drawer" role="region" aria-label="Selected area details">
              <div className="fv-drawer-title"><span className="fv-eyebrow">AREA DETAILS</span><button type="button" onClick={() => setDetailsOpen(false)} aria-label="Close area details"><X size={17}/></button></div>
              <h3>{selected.name}</h3><span className="fv-provenance">{sourcePill(selected.source_type,isStale(selected.timestamp))}</span>
              <div className="fv-measurement-grid">{METRICS.filter((m) => m.property).map((m) => {const r = readingFor(selected,m.id,data.demo);return <div key={m.id}><span>{m.label}</span><strong>{r ? number(r.value) : "—"}</strong><small>{r?.unit ?? "Unavailable"}</small></div>;})}</div>
              <small>{formatStamp(selected.timestamp)} · {selected.assumptions?.[0] ?? "Provider reading"}</small>
              <button type="button" className="fv-small-link" onClick={() => navigate("forecast")}>View area forecast <ArrowRight size={15}/></button>
            </section>}
          </div>}
          {page === "map" && subview === "analytics" && <div id="fv-page-details" className="fv-analytics-panels">
            <section className="fv-card fv-ai-panel"><span className="fv-card-kicker"><Sparkles size={17}/> Ask AirTwin AI</span>
              <h2>Air quality in {selected?.short_name ?? "your area"}.</h2><p>Understand the data and get practical steps for {selected?.short_name ?? "your selected area"}.</p>
              <div className="fv-suggestions">{["What can we do to improve air quality here?","Can I exercise outside?","Why might air quality change?"].map((q) =>
                <button key={q} type="button" onClick={() => setQuestion(q)}>{q} <ArrowUpRight size={12}/></button>)}</div>
              <form onSubmit={(event) => {event.preventDefault();void ask();}}>
                <label htmlFor="fv-question">Your question</label>
                <textarea id="fv-question" value={question} onChange={(event) => setQuestion(event.target.value)} rows={3} maxLength={400} placeholder="Ask something about this location…"/>
                <button type="submit" className="fv-button fv-primary" disabled={asking || !question.trim()}>{asking ? "Reading data and preparing steps…" : "Ask AirTwin"} <ArrowRight size={15}/></button>
              </form>
              {apiError && <p className="fv-inline-warning">Service error: {apiError}</p>}
              {answer && <div className="fv-ai-answer" role="status"><div className="fv-chat-question"><span>You asked</span><p>{answeredQuestion}</p></div><strong>{answerMeta}</strong>
                {answerClaims.length ? <>
                  {answerClaims.filter((claim) => claim.kind === "conclusion").map((claim,index) => <p className="fv-answer-conclusion" key={index}>{claim.text}</p>)}
                  {(["residents", "municipality", "general"] as const).map((audience) => {
                    const steps = answerClaims.filter((claim) => claim.kind === "action" && (claim.audience ?? "general") === audience);
                    return steps.length ? <section key={audience}><h3>{audience === "residents" ? "What residents can do" : audience === "municipality" ? "What to request from the municipality" : "Next steps"}</h3><ol>{steps.map((claim,index) => <li key={index}>{claim.text}</li>)}</ol></section> : null;
                  })}
                  {answerClaims.filter((claim) => claim.kind === "limitation").map((claim,index) => <p key={index}>{claim.text}</p>)}
                  <details><summary>What the data says</summary>{answerClaims.filter((claim) => (claim.kind ?? "finding") === "finding").map((claim,index) => <p key={index}>{claim.text}</p>)}</details>
                  <details><summary>Sources and answer limitations</summary>
                    {answerClaims.map((claim, index) => <p key={index}>{claim.source_type.toUpperCase()} · {claim.evidence_ids.join(", ")}</p>)}
                    {answerNotes.map((note) => <p key={note}>{note}</p>)}
                  </details>
                </> : <p>{answer}</p>}
              </div>}
              <div className="fv-note">AI explanations depend on available data and do not prove pollution causes.</div>
            </section>
            <section className="fv-card fv-advice-panel"><span className="fv-card-kicker"><Leaf size={16}/> Area tips</span><h2>Small steps, clearer choices.</h2>
              <div className="fv-advice-item"><span className="fv-advice-icon"><Wind size={18}/></span><div><strong>Plan your outdoor time</strong><p>{advice(selected?.pm25 ?? meanPM)}</p></div></div>
              <div className="fv-advice-item"><span className="fv-advice-icon"><MapPin size={18}/></span><div><strong>Check the source</strong><p>Modeled map cells aren't air monitors. Choose a recent measured station reading where available.</p></div></div>
              <div className="fv-advice-item"><span className="fv-advice-icon"><ShieldCheck size={18}/></span><div><strong>Protect sensitive groups</strong><p>Children, older adults, and people with breathing or heart conditions may need extra care when particles rise.</p></div></div>
              <div className="fv-divider"/>
              <div className="fv-locked"><LockKeyhole size={17}/><div><strong>Municipal operations</strong><p>Only executing municipal actions requires a server-verified PMC/PCMC role. Read-only model experiments below are public; employee access remains disabled until secure authentication is connected.</p></div></div>
              <details className="fv-disclosure"><summary>Data assumptions and provenance</summary><p>{selected?.assumptions?.join(" ") || "Select an area on the map to inspect its evidence."}</p></details>
            </section>
            <Suspense fallback={<div role="status" className="fv-research-shell">Loading research tools…</div>}>
              <ResearchWorkbench selected={selected} demo={data.demo}/>
            </Suspense>
          </div>}
          {page === "forecast" && <div id="fv-page-details" className="fv-forecast-panels">
            <div className="fv-card fv-forecast-summary"><span className="fv-card-kicker"><CloudMoon size={17}/> {focus ? "Area forecast" : "Selected reference forecast"}</span>
              <h2>{selected?.short_name ?? "Choose an area"}</h2><p>PM2.5 outlook · {hours} hours</p><p className="fv-selected-time">{selectedTime ? formatStamp(selectedTime) : "Loading selected time…"}</p>
              <div className="fv-forecast-values"><div><span>Latest reference</span><strong>{first !== null ? number(first,0) : "—"}</strong><small>µg/m³ · {selected?.source_type.toUpperCase()}</small></div>
                <div><span>Selected time</span><strong>{when?.predicted !== null && when?.predicted !== undefined ? number(when.predicted,0) : "—"}</strong><small>µg/m³ · {data.demo ? "SYNTHETIC" : "MODELED"}</small></div>
                <div><span>Tomorrow</span><strong>{trend}</strong><small>{tomorrowChange}</small></div></div>
              <div className="fv-outlook-weather"><SkyIcon night={night}/> {night ? "Night" : "Day"} · {selectedWeather?.cloud_cover !== undefined ? number(selectedWeather.cloud_cover,0) + "% modeled forecast cloud cover" : "Forecast cloud cover unavailable"}</div>
            </div>
            <div className="fv-card fv-forecast-chart-card"><div className="fv-chart-heading"><div><span className="fv-card-kicker"><TrendingDown size={16}/> Forecast trend</span><p>{forecast?.forecast_provider ?? "PM2.5 predictions from connected backend"}</p></div><span className="fv-mini-pill">{hours}h</span></div>
              {forecastBusy ? <div className="fv-chart-empty">Loading forecast…</div> : forecastError ? <div className="fv-inline-warning">{forecastError}</div> :
              <ForecastTrend forecast={forecast} demo={data.demo}/>}
              <div className="fv-forecast-caption">{forecast?.issued_at ? "Issued " + formatStamp(forecast.issued_at) : "Prediction time unavailable"} · {data.demo ? "SYNTHETIC DEMO" : "MODELED OUTLOOK"}</div>
              {forecast?.fallback_reason && <div className="fv-inline-warning">{forecast.fallback_reason === "location_has_no_observed_sensor" ? "Recent measured station history is unavailable for this location. Showing the CAMS provider forecast." : forecast.fallback_reason}</div>}
            </div>
            <section className="fv-card fv-tomorrow-insights" aria-label="Tomorrow's computed outlook">
              <span className="fv-card-kicker"><CloudSun size={16}/> Forecast outlook · Backend evidence</span>
              <div className="fv-forecast-insights-grid">
                <div><span>Highest modeled reference</span><strong>{dayReferenceRange.highest?.name ?? "Unavailable"}</strong>
                  <small>{dayReferenceRange.highest ? number(dayReferenceRange.highest.pm25, 0) + " µg/m³ · modeled" : "No spatial forecast"}</small></div>
                <div><span>Relatively lower reference</span><strong>{dayReferenceRange.lowest?.name ?? "Unavailable"}</strong>
                  <small>{dayReferenceRange.lowest ? number(dayReferenceRange.lowest.pm25, 0) + " µg/m³ · modeled" : "No spatial forecast"}</small></div>
                <div><span>Selected-area predicted peak</span><strong>{selectedPeak ? formatStamp(selectedPeak.timestamp) : "Unavailable"}</strong>
                  <small>{selectedPeak ? number(selectedPeak.pm25, 0) + " µg/m³ · within " + hours + "h" : "Forecast not available"}</small></div>
                <div><span>Weather forecast at selection</span>
                  <strong>{selectedWeather?.cloud_cover !== undefined ? number(selectedWeather.cloud_cover, 0) + "% cloud" : "Unavailable"}</strong>
                  <small>{selectedWeather?.wind_speed_10m !== undefined ? number(selectedWeather.wind_speed_10m * 3.6, 0) + " km/h modeled wind" : "Wind forecast not available"}</small></div>
              </div>
              <p>Ranked points are forecast reference locations, not measured street hotspots; forecasts are not causal attributions.</p>
            </section>
            <div className="fv-card fv-forecast-note"><span className="fv-card-kicker"><Info size={16}/> Reading this forecast</span><p>{advice(when?.predicted ?? null)}</p>
              <small>{forecast?.history_source_type?.toUpperCase() ?? "UNKNOWN"} history · MODELED future. Historical validation is separate from current forecast confidence.</small>
              {forecast && <details className="fv-disclosure"><summary>Forecast source and limitations</summary><p>{forecast.assumptions.join(" ")}</p></details>}
              {focus && <button type="button" className="fv-small-link" onClick={() => setFocus(false)}>← Back to city view</button>}
            </div>
          </div>}
        </aside>
      </div>}
    </main>
    <footer className="fv-footer"><span><Wind size={13}/> AirTwin · Environmental decision support</span><span>{data?.demo ? "SYNTHETIC OFFLINE DATA" : "Modeled grid + independently timestamped observations"} · Pune + PCMC</span><a href="https://openaq.org/" target="_blank" rel="noreferrer">OpenAQ</a> · <a href="https://open-meteo.com/" target="_blank" rel="noreferrer">Open-Meteo</a></footer>
  </div>;
}
