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

export async function loadDashboard(
  replayAt: string | null = null,
  region: RegionId = "pcmc",
): Promise<DashboardData> {
  if (!base)
    return {
      stations: demo.stations,
      cells: demo.cells,
      demo: true,
      warning: null,
    };
  try {
    const [stations, hotspots] = await Promise.all([
      request<StationsResponse>(
        withReplay(`/api/stations?region=${region}`, replayAt),
      ),
      request<HotspotsResponse>(
        withReplay(`/api/hotspots?mode=before&region=${region}`, replayAt),
      ),
    ]);
    if (!stations.stations?.length || !hotspots.cells?.length)
      throw new Error("API returned no locations or grid cells");
    return {
      stations: stations.stations,
      cells: hotspots.cells,
      demo: false,
      warning: stations.warnings?.join(" ") || null,
      weather: stations.weather,
      zones: stations.zones,
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
      60000,
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
      : request<ForecastResponse>(
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
      : request<BacktestResponse>(
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
      : request<AttributionResponse>(
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
