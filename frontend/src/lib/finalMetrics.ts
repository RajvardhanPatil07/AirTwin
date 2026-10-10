import type { Cell, DashboardData, SourceType, Station } from "../types";

export type MetricId = "pm25" | "aqi" | "pm10" | "no2" | "co2" | "o2" | "so2" | "o3";
export type Reading = {
  metric: MetricId;
  value: number;
  unit: string;
  timestamp: string;
  source: SourceType;
  provider: string;
  spatialSupport: string;
  stale: boolean;
};

export const METRICS: { id: MetricId; label: string; property?: string; unit: string; description: string }[] = [
  { id: "pm25", label: "PM2.5", property: "pm25", unit: "µg/m³", description: "Fine particulate concentration. Not an official AQI." },
  { id: "aqi", label: "AQI", unit: "index", description: "A published, standards-based AQI layer is not available from this endpoint." },
  { id: "pm10", label: "PM10", property: "pm10", unit: "µg/m³", description: "Coarse particulate concentration, where reported." },
  { id: "no2", label: "NO₂", property: "nitrogen_dioxide", unit: "µg/m³", description: "Nitrogen dioxide from available station/provider readings." },
  { id: "co2", label: "CO₂", unit: "ppm", description: "CO₂ is not reported by the currently connected pollution API." },
  { id: "o2", label: "O₂", unit: "%", description: "Oxygen concentration is not reported by the currently connected pollution API." },
  { id: "so2", label: "SO₂", property: "sulphur_dioxide", unit: "µg/m³", description: "Sulfur dioxide, where available." },
  { id: "o3", label: "O₃", property: "ozone", unit: "µg/m³", description: "Ozone, where available." },
];

const STALE_AFTER_HOURS = 24;

export function isStale(timestamp: string, now = Date.now()): boolean {
  const stamp = Date.parse(timestamp);
  return !Number.isFinite(stamp) || now - stamp > STALE_AFTER_HOURS * 3600_000 || stamp > now;
}

export function readingFor(station: Station, id: MetricId, demo: boolean, now = Date.now()): Reading | null {
  const metric = METRICS.find((item) => item.id === id);
  if (!metric?.property) return null;
  const supplied = metric.property === "pm25" ? undefined : station.pollutants?.[metric.property];
  if (metric.property !== "pm25" && !supplied) return null;
  const value = supplied ? supplied.value : station.pm25;
  const timestamp = supplied ? supplied.timestamp : station.timestamp;
  const source = demo ? "synthetic" : supplied?.source_type ?? station.source_type;
  if (!Number.isFinite(value) || value < 0) return null;
  return {
    metric: id, value,
    unit: supplied?.unit || metric.unit,
    timestamp,
    source,
    provider: demo ? "Offline illustration" : source === "observed" ? "OpenAQ / measured station" : "CAMS via Open-Meteo",
    spatialSupport: station.id.startsWith("cell-") ? "IDW interpolated grid cell" : source === "observed" ? "Monitor location" : "Modeled reference location",
    stale: isStale(timestamp, now),
  };
}

export function supportsMetric(data: DashboardData, id: MetricId): boolean {
  if (id === "pm25") return data.cells.some((cell) => Number.isFinite(cell.pm25));
  if (id === "aqi" || id === "co2" || id === "o2") return false;
  return data.stations.some((station) => readingFor(station, id, data.demo) !== null);
}

export function concentrationLabel(value: number): string {
  // Descriptive concentration band, NOT an official PM2.5 AQI category.
  if (value <= 30) return "Lower concentration";
  if (value <= 60) return "Elevated concentration";
  return "Higher concentration";
}

export function concentrationColor(value: number): string {
  if (value <= 20) return "#46b99b";
  if (value <= 40) return "#a8d56b";
  if (value <= 60) return "#f2d46b";
  if (value <= 90) return "#ef9c56";
  if (value <= 120) return "#d95756";
  return "#9c2f51";
}

export function hottestCell(cells: Cell[]): Cell | null {
  return [...cells].filter((cell) => Number.isFinite(cell.pm25))
    .sort((a, b) => b.pm25 - a.pm25)[0] ?? null;
}

export function orderedPlaces(stations: Station[], id: MetricId, demo: boolean): Station[] {
  return [...stations]
    .filter((station) => readingFor(station, id, demo))
    .sort((a, b) => (readingFor(b, id, demo)?.value ?? -1) - (readingFor(a, id, demo)?.value ?? -1));
}

export function interpretChange(first: number | null, later: number | null): string {
  if (first === null || later === null || !Number.isFinite(first) || !Number.isFinite(later)) return "Unavailable";
  const delta = later - first;
  if (Math.abs(delta) < Math.max(2, first * 0.08)) return "Similar";
  return delta < 0 ? "Cleaner" : "Worse";
}

export function provenanceLabel(source: SourceType, stale = false): string {
  return (source.toUpperCase()) + (stale ? " · STALE" : "");
}
