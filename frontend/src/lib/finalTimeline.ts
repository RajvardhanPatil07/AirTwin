import type { Cell, TimelineFrame, TimelineResponse } from "../types";

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
  if (values.size < Math.max(1, baseline.length / 2)) return null;
  // Preserve spatial extent, cell provenance, and metadata from the baseline.
  return baseline.map((cell) => ({
    ...cell,
    pm25: values.get(cell.id) ?? cell.pm25,
    source_type: cell.source_type === "synthetic" ? "synthetic" : "modeled",
  }));
}
