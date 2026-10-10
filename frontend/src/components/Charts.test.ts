import { createElement } from "react";
import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { BacktestChart } from "./Charts";
import type { BacktestResponse } from "../types";

describe("Observed station backtest", () => {
  it("renders a station benchmark with no seasonal baseline without inventing one", () => {
    const response: BacktestResponse = {
      location_id: "pune-cams-15",
      source_type: "modeled",
      target_source_type: "observed",
      assumptions: [
        "Station-specific benchmark does not validate the provider forecast.",
      ],
      method: "24-hour station-specific LightGBM",
      model: "openaq_station_lightgbm_24h",
      available: true,
      seasonal_baseline: {},
      cv: [],
      skill: [],
      metrics: {
        mae: 16.9,
        rmse: 21.5,
        r2: -0.19,
        persistence_mae: 11.1,
        improvement_percent: -52.2,
        interval_coverage: null,
      },
      series: [
        {
          timestamp: "2026-10-09T12:00:00+05:30",
          actual: 30,
          predicted: 40,
          persistence: 28,
          p10: null,
          p90: null,
        },
      ],
    };
    const html = renderToStaticMarkup(
      createElement(BacktestChart, { data: response, demo: false }),
    );
    expect(html).toContain("Observed station backtest");
    expect(html).toContain("Model loses to persistence");
    expect(html).not.toContain("Pooled training-only seasonal baseline");
    expect(html).not.toContain("Interval coverage");
  });
});
