import { describe, expect, it } from "vitest";
import { buildJourneySummary } from "./journey";
import type {
  AttributionResponse,
  BacktestResponse,
  ForecastResponse,
  ScenarioResponse,
  Station,
} from "../types";

const location: Station = {
  id: "bhosari",
  name: "Bhosari",
  short_name: "Bhosari",
  latitude: 18.62,
  longitude: 73.85,
  pm25: 100,
  timestamp: "2026-01-01T00:00:00+05:30",
  source_type: "observed",
  assumptions: [],
};

it("summarizes the five judge-facing evidence steps", () => {
  const forecast = {
    location_id: "bhosari",
    history_source_type: "observed",
    source_type: "modeled",
    assumptions: [],
    series: [
      {
        timestamp: "2026-01-01T01:00:00+05:30",
        actual: null,
        predicted: 110,
        persistence: null,
        p10: 90,
        p90: 125,
      },
      {
        timestamp: "2026-01-01T02:00:00+05:30",
        actual: null,
        predicted: 125,
        persistence: null,
        p10: 100,
        p90: 140,
      },
    ],
  } satisfies ForecastResponse;
  const backtest = {
    location_id: "bhosari",
    target_source_type: "observed",
    method: "holdout",
    source_type: "modeled",
    assumptions: [],
    series: [],
    metrics: {
      mae: 15,
      rmse: 20,
      r2: 0.4,
      persistence_mae: 16,
      improvement_percent: 6.25,
      interval_coverage: 80,
    },
  } satisfies BacktestResponse;
  const attribution = {
    location_id: "bhosari",
    background: 30,
    source_type: "modeled",
    assumptions: [],
    shares: [
      { name: "Traffic", value: 0.2, color: "#000" },
      { name: "Industry", value: 0.35, color: "#000" },
      { name: "Construction / road dust", value: 0.15, color: "#000" },
      { name: "Regional background", value: 0.3, color: "#000" },
    ],
  } satisfies AttributionResponse;

  const makeResult = (
    id: "traffic" | "industry" | "dust",
    name: string,
    benefit: number,
    reduction: number,
  ) => ({
    id,
    name,
    cuts: { traffic: 0, industry: 0, dust: 0 },
    rank: 1,
    before: 100,
    after: 100 - reduction,
    reduction,
    reduction_low: reduction * 0.8,
    reduction_high: reduction * 1.2,
    reduction_percent: reduction,
    exposure_benefit: benefit,
    population_source_type: "synthetic" as const,
    cells: [],
    source_type: "modeled" as const,
    assumptions: [],
  });

  const scenario = {
    scenario_id: "x",
    location_id: "bhosari",
    source_type: "modeled",
    assumptions: [],
    results: [
      {
        ...makeResult("traffic", "Combined", 100, 12),
        id: "combined" as const,
      },
      makeResult("traffic", "Traffic restriction", 20, 5),
      makeResult("industry", "Industrial controls", 50, 9),
      makeResult("dust", "Dust suppression", 15, 3),
    ],
  } satisfies ScenarioResponse;

  const summary = buildJourneySummary(
    location,
    forecast,
    backtest,
    attribution,
    scenario,
  );

  expect(summary.currentPm25).toBe(100);
  expect(summary.forecastPeak).toBe(125);
  expect(summary.validationImprovement).toBe(6.25);
  expect(summary.dominantSource).toBe("Industry");
  expect(summary.bestAction).toBe("Industrial controls");
  expect(summary.bestActionReduction).toBe(9);
});

describe("buildJourneySummary fallbacks", () => {
  it("keeps missing evidence explicit", () => {
    const summary = buildJourneySummary(location, null, null, null, null);
    expect(summary.forecastPeak).toBeNull();
    expect(summary.validationImprovement).toBeNull();
    expect(summary.dominantSource).toBeNull();
    expect(summary.bestAction).toBeNull();
  });
});
