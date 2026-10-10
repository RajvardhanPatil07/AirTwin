import type { ForecastResponse, Station, TimelineFrame } from "../types";

export type NamedReference = { name: string; pm25: number; id: string };

/** Rank only API-published forecast reference points; not interpolated map pixels. */
export function forecastReferenceRange(
  frame: TimelineFrame | null,
  stations: Station[],
): { highest: NamedReference | null; lowest: NamedReference | null } {
  if (!frame) return {highest:null,lowest:null};
  const names = new Map(stations.map(station => [station.id, station]));
  const ordered = frame.stations.filter(station => names.has(station.id) &&
    Number.isFinite(station.pm25) && station.pm25 >= 0)
    .map(station => ({name:names.get(station.id)!.short_name || names.get(station.id)!.name,
      pm25:station.pm25,id:station.id}))
    .sort((a,b) => a.pm25 - b.pm25);
  return {lowest: ordered[0] ?? null,highest:ordered.at(-1) ?? null};
}
/** Peak of selected location forecast only; never claims a region-wide peak. */
export function selectedForecastPeak(forecast: ForecastResponse | null) {
  if (!forecast) return null;
  return forecast.series.filter(point =>
    point.predicted !== null && Number.isFinite(point.predicted))
    .reduce<{ timestamp:string; pm25:number } | null>((peak, point) =>
      point.predicted !== null && (!peak || point.predicted > peak.pm25) ?
        {timestamp:point.timestamp,pm25:point.predicted} : peak, null);
}
