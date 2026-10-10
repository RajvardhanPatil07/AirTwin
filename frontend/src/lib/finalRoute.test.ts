import { describe, expect, it } from "vitest";
import {readRoute, resolveRouteStation, writeRoute} from "./finalRoute";
import type {DashboardData} from "../types";

describe("finalv1 shareable routes", () => {
  it("rejects invalid pages, horizons and metric choices", () => {
    expect(readRoute("?page=unknown&hours=999&metric=water")).toEqual({
      page:"overview", view:"explore", metric:"pm25", hours:24, location:null,
    });
    expect(readRoute("?page=map&view=analytics&hours=72&metric=no2&location=cell-34")).toEqual({
      page:"map", view:"analytics", metric:"no2", hours:72, location:"cell-34",
    });
  });
  it("writes one parameter without discarding existing selections", () => {
    const initial = new URL("https://example.org/?page=map&metric=pm10&location=openaq-33");
    const output = writeRoute(initial,{page:"forecast",hours:48});
    expect(output.searchParams.get("metric")).toBe("pm10");
    expect(output.searchParams.get("location")).toBe("openaq-33");
    expect(output.searchParams.get("hours")).toBe("48");
    expect(writeRoute(output,{view:"explore",location:null}).searchParams.has("location")).toBe(false);
  });
  it("restores selected backend grid cells without representing them as sensors", () => {
    const data:DashboardData = {
      demo: false, warning:null,
      stations:[{id:"pune-1",name:"Pune",short_name:"Pune",source_type:"modeled",
                 latitude:18.52,longitude:73.85,pm25:31,timestamp:"2026-10-10T16:00:00Z",assumptions:[]}],
      cells:[{id:"cell-9",latitude:18.55,longitude:73.77,pm25:48,
              bounds:[[18.54,73.76],[18.56,73.78]],background:20,population:100,
              source_type:"modeled",population_source_type:"synthetic",
              local_weights:{traffic:0.3,industry:0.3,dust:0.4}, assumptions:["Modeled grid"]}],
    };
    expect(resolveRouteStation(data,"cell-9")?.source_type).toBe("modeled");
    expect(resolveRouteStation(data,"cell-9")?.id).toBe("cell-9");
    expect(resolveRouteStation(data,"cell-9")?.assumptions.join(" ")).toContain("not an observed monitor");
    expect(resolveRouteStation(data,"pune-1")?.name).toBe("Pune");
    expect(resolveRouteStation(data,"unrecognized")?.name).toBe("Pune");
  });
});
