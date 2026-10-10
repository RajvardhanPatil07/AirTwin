import type { DashboardData, Station } from "../types";
import { METRICS, type MetricId } from "./finalMetrics";

export type RoutePage = "overview" | "map" | "forecast";
export type RouteView = "explore" | "analytics";
export interface RouteState {
  page: RoutePage;
  view: RouteView;
  metric: MetricId;
  hours: 24 | 48 | 72;
  location: string | null;
}
export function readRoute(search: string): RouteState {
  const params = new URLSearchParams(search);
  const name = params.get("page");
  const metric = params.get("metric");
  const hours = Number(params.get("hours"));
  const location = params.get("location");
  return {
    page: name === "map" || name === "forecast" ? name : "overview",
    view: params.get("view") === "analytics" ? "analytics" : "explore",
    metric: METRICS.some((option) => option.id === metric) ? metric as MetricId : "pm25",
    hours: hours === 48 || hours === 72 ? hours : 24,
    location: location && location.length < 160 ? location : null,
  };
}
export function writeRoute(url: URL, changes: Partial<RouteState>): URL {
  const updated = new URL(url);
  if (changes.page !== undefined) updated.searchParams.set("page", changes.page);
  if (changes.view !== undefined) {
    if (changes.view === "analytics") updated.searchParams.set("view", changes.view);
    else updated.searchParams.delete("view");
  }
  if (changes.metric !== undefined) updated.searchParams.set("metric", changes.metric);
  if (changes.hours !== undefined) updated.searchParams.set("hours", String(changes.hours));
  if (changes.location !== undefined) {
    if (changes.location) updated.searchParams.set("location", changes.location);
    else updated.searchParams.delete("location");
  }
  return updated;
}
export function resolveRouteStation(data: DashboardData, location: string | null): Station | null {
  if (!data.stations.length) return null;
  if (location) {
    const found = data.stations.find((station) => station.id === location);
    if (found) return found;
    const cell = data.cells.find((grid) => grid.id === location);
    if (cell) return {
      id: cell.id,
      name: "Modeled grid · " + cell.id,
      short_name: "Grid cell",
      latitude: cell.latitude, longitude: cell.longitude,
      pm25: cell.pm25, timestamp: data.stations[0].timestamp,
      source_type: data.demo ? "synthetic" : "modeled",
      assumptions: [...cell.assumptions, "Nearest existing modeled grid cell; not an observed monitor."],
    };
  }
  return data.stations.find((station) => station.name.toLowerCase().includes("pune")) ?? data.stations[0];
}
