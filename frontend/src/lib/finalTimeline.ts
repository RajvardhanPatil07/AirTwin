import type { Cell, ForecastResponse, TimelineFrame, TimelineResponse } from "../types";

/** The API supplies spatial forecast frames only at explicitly calculated hours. */
export function frameAtOrBefore(timeline: TimelineResponse | null, hour: number): TimelineFrame | null {
  if (!timeline?.frames?.length) return null;
  const valid = timeline.frames
    .filter((frame) => frame.hour <= hour && frame.hour >= 0 && frame.cells.length)
    .sort((a, b) => a.hour - b.hour);
  return valid.at(-1) ?? null;
}
export function cellsAtFrame(baseline: Cell[], frame: TimelineFrame | null): Cell[] | null {
  if (!frame) return null;
  const values = new Map(frame.cells
    .filter((cell) => Number.isFinite(cell.pm25) && cell.pm25 >= 0)
    .map((cell) => [cell.id, cell.pm25]));
  if (!baseline.length) return null;
  const projected: Cell[] = [];
  for (const cell of baseline) {
    const pm25 = values.get(cell.id);
    if (pm25 === undefined) return null;
    projected.push({...cell, pm25, source_type: cell.source_type === "synthetic" ? "synthetic" : "modeled"});
  }
  return projected;
}

/** Match a spatial map to the same forecast issue time as the selected-area
 * chart. Never combine unrelated provider snapshots, even if hours match.
 */
export function alignedForecastFrame(
  timeline: TimelineResponse | null,
  forecast: ForecastResponse | null,
  selection: number,
): TimelineFrame | null {
  if (!timeline || !forecast) return null;
  const predicted = forecast.series.filter(point =>
    point.predicted !== null && Number.isFinite(point.predicted));
  if (!predicted.length) return null;
  const origin = Date.parse(timeline.origin);
  const first = Date.parse(predicted[0].timestamp);
  const timestamp = Date.parse(predicted[Math.min(Math.max(0,selection),predicted.length - 1)].timestamp);
  if (![origin,first,timestamp].every(Number.isFinite)) return null;
  // A direct forecast starts one hour after its issue timestamp.
  if (Math.abs(first - origin - 3600_000) > 1000) return null;
  const hour = Math.floor((timestamp - origin) / 3600_000 + 1e-6);
  if (hour < 0) return null;
  const lastHour = Math.max(...timeline.frames.map(frame => frame.hour));
  if (hour > lastHour) return null;
  return frameAtOrBefore(timeline, hour);
}
