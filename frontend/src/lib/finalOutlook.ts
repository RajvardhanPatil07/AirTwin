import { rankedReferences, referenceName } from "./finalMetrics";
import type { ForecastResponse, Station, TimelineFrame } from "../types";

export type NamedReference = { name: string; pm25: number; id: string };

/** Rank only API-published forecast reference points; not interpolated map pixels. */
export function forecastReferenceRange(
  frame: TimelineFrame | null,
  stations: Station[],
): { highest: NamedReference | null; lowest: NamedReference | null } {
  if (!frame) return {highest:null,lowest:null};
  const names = new Map(stations.map(station => [station.id, station]));
  const projected = frame.stations.filter(station => names.has(station.id) &&
    Number.isFinite(station.pm25) && station.pm25 >= 0)
    .map(station => ({...names.get(station.id)!, pm25:station.pm25, timestamp:frame.timestamp, source_type:"modeled" as const}));
  const ordered = rankedReferences(projected, "pm25", false);
  const named = (group: typeof ordered[number] | undefined): NamedReference | null => group
    ? {name:referenceName(group.locations),pm25:group.reading.value,id:group.locations[0].id} : null;
  return {highest:named(ordered[0]),lowest:named(ordered.at(-1))};
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
