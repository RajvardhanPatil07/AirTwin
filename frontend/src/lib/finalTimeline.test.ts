import { describe, expect, it } from "vitest";
import { frameAtOrBefore, cellsAtFrame, alignedForecastFrame } from "./finalTimeline";
import { localityMatches, nearestGridCell } from "./finalPlaces";
import type { Cell, DashboardData, TimelineResponse } from "../types";

const cell = (id: string, lat: number, lon: number, pm25: number): Cell => ({
  id, latitude: lat, longitude: lon, pm25,
  bounds: [[lat - .01, lon - .01], [lat + .01, lon + .01]],
  background: 10, population: 100, population_source_type: "synthetic",
  source_type: "modeled", assumptions: ["Coarse interpolation"],
  local_weights: {traffic:.4,industry:.3,dust:.3},
});
const cells = [cell("cell-baner",18.56,73.78,48),cell("cell-city",18.52,73.85,64)];
const frame: TimelineResponse = {
  source_type:"modeled", assumptions:["Provider forecasts only"],
  origin:"2026-10-10T12:00:00Z",
  frames:[
    {hour:0,timestamp:"2026-10-10T12:00:00Z",source_type:"modeled",stations:[],cells:[{id:"cell-baner",pm25:48},{id:"cell-city",pm25:64}]},
    {hour:6,timestamp:"2026-10-10T18:00:00Z",source_type:"modeled",stations:[],cells:[{id:"cell-baner",pm25:31},{id:"cell-city",pm25:60}]},
    {hour:12,timestamp:"2026-10-11T00:00:00Z",source_type:"modeled",stations:[],cells:[{id:"cell-baner",pm25:26},{id:"cell-city",pm25:53}]},
  ],
};
describe("finalv1 mapped forecast and locality integration", () => {
  it("uses only published future frames rather than fabricating every hour", () => {
    expect(frameAtOrBefore(frame, 5)?.hour).toBe(0);
    expect(frameAtOrBefore(frame, 6)?.hour).toBe(6);
    expect(frameAtOrBefore(frame, 10)?.hour).toBe(6);
    expect(frameAtOrBefore(frame, 16)?.hour).toBe(12);
    expect(frameAtOrBefore(null, 12)).toBeNull();
  });
  it("updates underlying grid values without changing boundaries or source metadata", () => {
    const future = cellsAtFrame(cells,frame.frames[1]);
    expect(future?.map((x) => x.pm25)).toEqual([31,60]);
    expect(future?.[0].id).toBe(cells[0].id);
    expect(future?.[0].bounds).toEqual(cells[0].bounds);
    expect(future?.[0].source_type).toBe("modeled");
    expect(cells[0].pm25).toBe(48);
    expect(cellsAtFrame(cells,null)).toBeNull();
  });
  it("refuses to draw a forecast grid issued for a different datetime", () => {
    const forecast = {
      location_id:"model-reference",
      source_type:"modeled" as const,
      history_source_type:"modeled" as const,
      assumptions:[],
      series:[
        {timestamp:"2026-10-10T13:00:00Z",actual:null,predicted:40,p10:null,p90:null,persistence:null},
        {timestamp:"2026-10-10T18:00:00Z",actual:null,predicted:34,p10:null,p90:null,persistence:null},
      ],
    };
    expect(alignedForecastFrame(frame,forecast,1)?.hour).toBe(6);
    const mismatch = {...forecast,series:forecast.series.map((point) => ({
      ...point,timestamp:point.timestamp.replace("2026-10-10","2026-10-08"),
    }))};
    expect(alignedForecastFrame(frame,mismatch,1)).toBeNull();
  });
  it("keeps locality search on already modeled grid cells", () => {
    const data: DashboardData = {stations:[],cells,demo:false,warning:null};
    const matches=localityMatches(data,"baner");
    expect(matches).toHaveLength(1);
    expect(matches[0].id).toBe("cell-baner");
    expect(matches[0].pm25).toBe(48);
    expect(matches[0].source_type).toBe("modeled");
    expect(matches[0].assumptions.at(-1)).toContain("not a monitor");
    expect(nearestGridCell(cells,18.56,73.78)?.id).toBe("cell-baner");
  });
});

it("uses published 48 and 72 hour map frames without freezing at 24 hours", () => {
  const origin = Date.parse(frame.origin);
  const stamp = (hour: number) => new Date(origin + hour * 3600_000).toISOString();
  const extended = {...frame, frames: [0,24,48,72].map(hour => ({
    hour, timestamp:stamp(hour), source_type:"modeled" as const,
    stations:[], cells:[{id:"cell-baner",pm25:48-hour/2},{id:"cell-city",pm25:64-hour/2}],
  }))};
  const forecast = {location_id:"model-reference",source_type:"modeled" as const,
    history_source_type:"modeled" as const,assumptions:[],
    series:Array.from({length:72}, (_, i) => ({timestamp:stamp(i+1),actual:null,predicted:40,p10:null,p90:null,persistence:null}))};
  expect(alignedForecastFrame(extended,forecast,47)?.hour).toBe(48);
  expect(alignedForecastFrame(extended,forecast,71)?.hour).toBe(72);
  expect(alignedForecastFrame({...extended,frames:extended.frames.slice(0,2)},forecast,71)).toBeNull();
});

it("does not mix old baseline pixels into an incomplete future grid", () => {
  expect(cellsAtFrame(cells, {...frame.frames[1],cells:[{id:"cell-baner",pm25:31}]})).toBeNull();
});
