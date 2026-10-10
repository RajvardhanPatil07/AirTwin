import type {
  AttributionResponse,
  ExplainResponse,
  ReplayResponse,
  BacktestResponse,
  Cuts,
  DashboardData,
  ForecastResponse,
  HotspotsResponse,
  ScenarioResponse,
  Station,
  StationsResponse,
  RegionId,
  TimelineResponse,
  DecisionRunResponse,
  DataHealthResponse,
} from "../types";
import * as demo from "../mocks/engine";

const base = (
  import.meta.env.VITE_API_BASE_URL ?? "/backend"
).replace(/\/$/, "");
async function request<T>(
  path: string,
  init?: RequestInit,
  timeout = 8000,
): Promise<T> {
  const response = await fetch(`${base}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    signal: AbortSignal.timeout(timeout),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      typeof error.detail === "string"
        ? error.detail
        : `API returned ${response.status}`,
    );
  }
  const data = await response.json();
  if (!["observed", "modeled", "synthetic"].includes(data.source_type)) {
    throw new Error("API response is missing valid data provenance");
  }
  if (data.source_type === "modeled" && !Array.isArray(data.assumptions)) {
    throw new Error("Modeled API response is missing assumptions");
  }
  return data as T;
}

// Browser read model: deduplicate overlapping requests and keep bounded, short-lived
// snapshots. Mutations (decision runs and explanations) always bypass this cache.
type CacheEntry = { until: number; value?: unknown; pending?: Promise<unknown> };
const readCache = new Map<string, CacheEntry>();
const MAX_CACHE_ENTRIES = 64;

function cachedRead<T>(path: string, ttlMs = 60_000, force = false, timeout = 8000): Promise<T> {
  const now = Date.now();
  const current = readCache.get(path);
  if (!force && current?.value !== undefined && current.until > now) {
    return Promise.resolve(current.value as T);
  }
  if (!force && current?.pending) return current.pending as Promise<T>;

  const entry: CacheEntry = { until: 0 };
  const pending = request<T>(path, undefined, timeout).then(
    (value) => {
      entry.value = value;
      entry.until = Date.now() + ttlMs;
      delete entry.pending;
      return value;
    },
    (error) => {
      // Do not poison future attempts with failed/aborted requests.
      if (readCache.get(path) === entry) readCache.delete(path);
      throw error;
    },
  );
  entry.pending = pending;
  if (readCache.size >= MAX_CACHE_ENTRIES) {
    const oldest = readCache.keys().next().value;
    if (oldest !== undefined) readCache.delete(oldest);
  }
  readCache.set(path, entry);
  return pending;
}

export async function loadDashboard(
  replayAt: string | null = null,
  region: RegionId = "pcmc",
  forceRefresh = false,
): Promise<DashboardData> {
  if (!base)
    return {
      stations: demo.stations,
      cells: demo.cells,
      demo: true,
      warning: null,
    };
  try {
    // A single response replaces two expensive spatial queries on upgraded APIs.
    // Older deployments keep working through the original version-one routes.
    let stations: StationsResponse;
    let hotspots: HotspotsResponse;
    try {
      const bundle = await cachedRead<StationsResponse & HotspotsResponse>(
        withReplay(`/api/v2/bootstrap?region=${region}`, replayAt),
        30_000,
        forceRefresh,
      );
      stations = bundle;
      hotspots = bundle;
    } catch (error) {
      // Only retry via v1 when the API reports a missing endpoint. Network
      // failures should fall back promptly rather than wait for extra timeouts.
      if (!(error instanceof Error) || !error.message.includes("404")) throw error;
      [stations, hotspots] = await Promise.all([
        cachedRead<StationsResponse>(
          withReplay(`/api/stations?region=${region}`, replayAt), 30_000, forceRefresh,
        ),
        cachedRead<HotspotsResponse>(
          withReplay(`/api/hotspots?mode=before&region=${region}`, replayAt), 30_000, forceRefresh,
        ),
      ]);
    }
    if (!stations.stations?.length || !hotspots.cells?.length)
      throw new Error("API returned no locations or grid cells");
    return {
      stations: stations.stations,
      cells: hotspots.cells,
      demo: false,
      warning: stations.warnings?.join(" ") || null,
      weather: stations.weather,
      zones: stations.zones,
      zones_source_type: stations.zones_source_type,
      region: stations.region,
      coverage: stations.coverage,
    };
  } catch (error) {
    return {
      stations: demo.stations,
      cells: demo.cells,
      demo: true,
      warning:
        `Backend unavailable or incompatible (${error instanceof Error ? error.message : "connection failed"}). Showing synthetic demo data.`,
    };
  }
}
function withReplay(path: string, replayAt: string | null) {
  return replayAt
    ? `${path}${path.includes("?") ? "&" : "?"}replay_at=${encodeURIComponent(replayAt)}`
    : path;
}
export const api = {
  replay: () => request<ReplayResponse>("/api/replay"),
  dataHealth: (region: RegionId = "pcmc") =>
    request<DataHealthResponse>("/api/v2/data-health?region=" + encodeURIComponent(region)),
  runDecision: (locationId: string, cuts: Cuts, replayAt: string | null, region: RegionId = "pcmc") =>
    request<DecisionRunResponse>("/api/v2/decision-runs", {
      method: "POST",
      body: JSON.stringify({ location_id: locationId, cuts, replay_at: replayAt, region }),
    }, 60000),
  timeline: (replayAt: string | null, region: RegionId) =>
    cachedRead<TimelineResponse>(withReplay(`/api/timeline?region=${region}`, replayAt), 120_000, false, 60000),
  explain: (
    locationId: string,
    question: string,
    replayAt: string | null,
    region: RegionId,
    cuts: Cuts,
    hours: number,
    history: { role: string; content: string }[],
  ) =>
    request<ExplainResponse>(
      "/api/explain",
      {
        method: "POST",
        body: JSON.stringify({
          location_id: locationId,
          question,
          replay_at: replayAt,
          region,
          cuts,
          hours,
          history,
        }),
      },
      110000,
    ),
  forecast: (
    station: Station,
    isDemo: boolean,
    hours: number,
    replayAt: string | null = null,
    region: RegionId = "pcmc",
  ) =>
    isDemo
      ? Promise.resolve(demo.forecast(station, hours))
      : cachedRead<ForecastResponse>(
          withReplay(
            `/api/forecast?location_id=${encodeURIComponent(station.id)}&hours=${hours}&region=${region}`,
            replayAt,
          ),
        ),
  backtest: (
    station: Station,
    isDemo: boolean,
    replayAt: string | null = null,
    region: RegionId = "pcmc",
  ) =>
    isDemo
      ? Promise.resolve(demo.backtest(station))
      : cachedRead<BacktestResponse>(
          withReplay(
            `/api/backtest?location_id=${encodeURIComponent(station.id)}&region=${region}`,
            replayAt,
          ),
        ),
  attribution: (
    station: Station,
    isDemo: boolean,
    replayAt: string | null = null,
    region: RegionId = "pcmc",
  ) =>
    isDemo
      ? Promise.resolve(demo.attribution(station))
      : cachedRead<AttributionResponse>(
          withReplay(
            `/api/attribution?location_id=${encodeURIComponent(station.id)}&region=${region}`,
            replayAt,
          ),
        ),
  scenarios: (
    station: Station,
    cuts: Cuts,
    isDemo: boolean,
    replayAt: string | null = null,
    region: RegionId = "pcmc",
  ) =>
    isDemo
      ? Promise.resolve(demo.runScenario(station, cuts))
      : request<ScenarioResponse>("/api/scenarios", {
          method: "POST",
          body: JSON.stringify({
            location_id: station.id,
            cuts,
            replay_at: replayAt,
            region,
          }),
        }),
};
