import { describe, expect, it } from "vitest";
import { concentrationColor, interpretChange, isStale, orderedPlaces, rankedReferences, readingFor, supportsMetric } from "./finalMetrics";
import type { DashboardData, Station } from "../types";

const now = Date.parse("2026-10-11T00:00:00Z");
function station(id: string, value: number, source: Station["source_type"] = "modeled"): Station {
  return {
    id, name: id, short_name: id, latitude: 18.5, longitude: 73.8,
    pm25: value, timestamp: "2026-10-10T12:00:00Z",
    source_type: source, assumptions: ["Test-only provider reading"],
  };
}
function dashboard(): DashboardData {
  return {
    stations: [station("high", 90), station("low", 20)],
    cells: [{
      id: "cell-0", latitude: 18.5, longitude: 73.8,
      bounds: [[18.49,73.79],[18.51,73.81]], pm25: 38,
      background: 12, population: 1, population_source_type: "synthetic",
      source_type: "modeled", assumptions: ["Interpolated"],
      local_weights: { traffic: .3, industry: .3, dust: .4 },
    }], demo: false, warning: null,
  };
}
describe("finalv1 scientific UI data contract", () => {
  it("does not invent AQI, CO2, O2, or missing pollutant data", () => {
    const data = dashboard();
    expect(supportsMetric(data, "pm25")).toBe(true);
    expect(supportsMetric(data, "aqi")).toBe(false);
    expect(supportsMetric(data, "co2")).toBe(false);
    expect(supportsMetric(data, "o2")).toBe(false);
    expect(supportsMetric(data, "no2")).toBe(false);
    expect(readingFor(data.stations[0], "no2", false)).toBeNull();
  });
  it("reads real provider metadata for an available pollutant", () => {
    const st = station("model", 50);
    st.pollutants = { pm10: { value: 74, unit: "µg/m³", source_type: "modeled", timestamp: st.timestamp } };
    const reading = readingFor(st, "pm10", false, now);
    expect(reading?.value).toBe(74);
    expect(reading?.source).toBe("modeled");
    expect(reading?.unit).toBe("µg/m³");
  });
  it("keeps stale observed data clearly stale and demo clearly synthetic", () => {
    const old = station("openaq-19", 42, "observed");
    old.timestamp = "2026-10-07T12:00:00Z";
    expect(isStale(old.timestamp, now)).toBe(true);
    expect(readingFor(old, "pm25", false, now)?.stale).toBe(true);
    expect(readingFor(old, "pm25", true, now)?.source).toBe("synthetic");
  });
  it("ranks supported reference locations without inventing neighborhood locations", () => {
    expect(orderedPlaces(dashboard().stations, "pm25", false).map((s) => s.name)).toEqual(["high","low"]);
  });
  it("does not treat concentration bands as official AQI", () => {
    expect(concentrationColor(15)).toMatch(/^#/);
    expect(interpretChange(40, 20)).toBe("Cleaner");
    expect(interpretChange(20, 40)).toBe("Worse");
    expect(interpretChange(20, 20)).toBe("Similar");
    expect(interpretChange(null, 20)).toBe("Unavailable");
  });
});

describe("shared provider readings", () => {
  it("groups proven identical model series while preserving independent equal readings", () => {
    const a = {...station("a",55.5),model_reference_id:"series-1"};
    const b = {...station("b",55.5),model_reference_id:"series-1"};
    const independent = {...station("independent",55.5),model_reference_id:"series-2"};
    const monitor = {...station("monitor",55.5,"observed"),model_reference_id:"series-1"};
    const ranked = rankedReferences([a,b,independent,monitor,station("low",20)],"pm25",false);
    expect(ranked).toHaveLength(4);
    expect(ranked[0].locations.map(item => item.id)).toEqual(["a","b"]);
    expect(ranked.map(group => group.rank)).toEqual([1,1,1,2]);
  });
  it("keeps different timestamps and pollutant-specific references separate", () => {
    const a = {...station("a",55),model_reference_id:"same",pollutants:{pm10:{value:70,unit:"µg/m³",timestamp:"2026-10-10T12:00:00Z",source_type:"modeled" as const,model_reference_id:"pm10-a"}}};
    const b = {...a,id:"b",pollutants:{pm10:{...a.pollutants.pm10,model_reference_id:"pm10-b"}}};
    expect(rankedReferences([a,b],"pm25",false)).toHaveLength(1);
    expect(rankedReferences([a,b],"pm10",false)).toHaveLength(2);
    expect(rankedReferences([a,{...b,timestamp:"2026-10-10T13:00:00Z"}],"pm25",false)).toHaveLength(2);
  });
});
