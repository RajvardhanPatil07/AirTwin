import type {
  AttributionResponse,
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

const base = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "");
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

export async function loadDashboard(): Promise<DashboardData> {
  if (!base)
    return {
      stations: demo.stations,
      cells: demo.cells,
      demo: true,
      warning: null,
    };
  try {
    const [stations, hotspots] = await Promise.all([
      request<StationsResponse>("/api/stations"),
      request<HotspotsResponse>("/api/hotspots?mode=before"),
    ]);
    if (!stations.stations?.length || !hotspots.cells?.length)
      throw new Error("API returned no locations or grid cells");
    return {
      stations: stations.stations,
      cells: hotspots.cells,
      demo: false,
      warning: null,
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
export const api = {
  forecast: (station: Station, isDemo: boolean, hours: number) =>
    isDemo
      ? Promise.resolve(demo.forecast(station, hours))
      : request<ForecastResponse>(
          `/api/forecast?location_id=${encodeURIComponent(station.id)}&hours=${hours}`,
        ),
  backtest: (station: Station, isDemo: boolean) =>
    isDemo
      ? Promise.resolve(demo.backtest(station))
      : request<BacktestResponse>(
          `/api/backtest?location_id=${encodeURIComponent(station.id)}`,
        ),
  attribution: (station: Station, isDemo: boolean) =>
    isDemo
      ? Promise.resolve(demo.attribution(station))
      : request<AttributionResponse>(
          `/api/attribution?location_id=${encodeURIComponent(station.id)}`,
        ),
  scenarios: (station: Station, cuts: Cuts, isDemo: boolean) =>
    isDemo
      ? Promise.resolve(demo.runScenario(station, cuts))
      : request<ScenarioResponse>("/api/scenarios", {
          method: "POST",
          body: JSON.stringify({ location_id: station.id, cuts }),
        }),
};
