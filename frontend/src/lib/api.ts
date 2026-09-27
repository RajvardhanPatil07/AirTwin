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
} from "../types";
import * as demo from "../mocks/engine";

const base = (
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000"
).replace(/\/$/, "");
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${base}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    signal: AbortSignal.timeout(8000),
  });
  if (!response.ok) throw new Error(`API returned ${response.status}`);
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
      request<StationsResponse>(withReplay("/api/stations", replayAt)),
      request<HotspotsResponse>(
        withReplay("/api/hotspots?mode=before", replayAt),
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
    };
  } catch {
    return {
      stations: demo.stations,
      cells: demo.cells,
      demo: true,
      warning:
        "Backend unavailable or incompatible. Showing synthetic demo data.",
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
  explain: (locationId: string, question: string, replayAt: string | null) =>
    request<ExplainResponse>("/api/explain", {
      method: "POST",
      body: JSON.stringify({
        location_id: locationId,
        question,
        replay_at: replayAt,
      }),
    }),
  forecast: (
    station: Station,
    isDemo: boolean,
    hours: number,
    replayAt: string | null = null,
  ) =>
    isDemo
      ? Promise.resolve(demo.forecast(station, hours))
      : request<ForecastResponse>(
          withReplay(
            `/api/forecast?location_id=${encodeURIComponent(station.id)}&hours=${hours}`,
            replayAt,
          ),
        ),
  backtest: (
    station: Station,
    isDemo: boolean,
    replayAt: string | null = null,
  ) =>
    isDemo
      ? Promise.resolve(demo.backtest(station))
      : request<BacktestResponse>(
          withReplay(
            `/api/backtest?location_id=${encodeURIComponent(station.id)}`,
            replayAt,
          ),
        ),
  attribution: (
    station: Station,
    isDemo: boolean,
    replayAt: string | null = null,
  ) =>
    isDemo
      ? Promise.resolve(demo.attribution(station))
      : request<AttributionResponse>(
          withReplay(
            `/api/attribution?location_id=${encodeURIComponent(station.id)}`,
            replayAt,
          ),
        ),
  scenarios: (
    station: Station,
    cuts: Cuts,
    isDemo: boolean,
    replayAt: string | null = null,
  ) =>
    isDemo
      ? Promise.resolve(demo.runScenario(station, cuts))
      : request<ScenarioResponse>("/api/scenarios", {
          method: "POST",
          body: JSON.stringify({
            location_id: station.id,
            cuts,
            replay_at: replayAt,
          }),
        }),
};
