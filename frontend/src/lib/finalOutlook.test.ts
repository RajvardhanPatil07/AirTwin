import { describe, expect, it } from "vitest";
import { forecastReferenceRange, selectedForecastPeak } from "./finalOutlook";
import type { ForecastResponse, Station, TimelineFrame } from "../types";

const station = (id: string): Station => ({
  id, name: id, short_name: id, latitude:18.52,longitude:73.85,pm25:40,
  timestamp:"2026-10-11T00:00:00Z",source_type:"modeled",assumptions:[],
});
const modeled: TimelineFrame = {
  hour:24, timestamp:"2026-10-12T00:00:00Z",source_type:"modeled",
  cells: [], stations:[{id:"a",pm25:60},{id:"b",pm25:20},{id:"unknown",pm25:999}],
};
describe("finalv1 forecast outlook", () => {
  it("ranks only named backend station forecasts, never fabricated locality values", () => {
    const range = forecastReferenceRange(modeled,[station("a"),station("b")]);
    expect(range.highest?.name).toBe("a");
    expect(range.highest?.pm25).toBe(60);
    expect(range.lowest?.name).toBe("b");
    expect(range.lowest?.pm25).toBe(20);
    expect(forecastReferenceRange(null,[station("a")]).highest).toBeNull();
  });
  it("identifies the peak only from modeled future predictions, not historical values", () => {
    const forecast:ForecastResponse = {
      location_id:"a",source_type:"modeled",history_source_type:"observed",assumptions:[],
      series:[
        {timestamp:"2026-10-10T00:00:00Z",actual:400,predicted:null,p10:null,p90:null,persistence:null},
        {timestamp:"2026-10-11T00:00:00Z",actual:null,predicted:31,p10:20,p90:40,persistence:null},
        {timestamp:"2026-10-11T12:00:00Z",actual:null,predicted:44,p10:34,p90:50,persistence:null},
      ],
    };
    expect(selectedForecastPeak(forecast)).toEqual({timestamp:"2026-10-11T12:00:00Z",pm25:44});
    expect(selectedForecastPeak(null)).toBeNull();
  });
});
