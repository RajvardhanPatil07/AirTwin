import { describe, expect, it } from "vitest";
import {
  attribution,
  backtest,
  background,
  cells,
  delta,
  idw,
  localWeights,
  runScenario,
  stations,
} from "./engine";

describe("transparent demo scenario engine", () => {
  it("leaves every value unchanged at zero cuts", () => {
    runScenario(stations[0], {
      traffic: 0,
      industry: 0,
      dust: 0,
    }).results.forEach((action) => {
      expect(action.reduction).toBe(0);
      expect(action.exposure_benefit).toBe(0);
      expect(action.after).toBe(action.before);
    });
  });
  it("combined equals individual concentration and exposure benefits", () => {
    const result = runScenario(stations[0], {
      traffic: 20,
      industry: 30,
      dust: 30,
    });
    const combined = result.results.find((action) => action.id === "combined")!;
    const singles = result.results.filter((action) => action.id !== "combined");
    expect(combined.reduction).toBeCloseTo(
      singles.reduce((sum, action) => sum + action.reduction, 0),
      10,
    );
    expect(combined.exposure_benefit).toBeCloseTo(
      singles.reduce((sum, action) => sum + action.exposure_benefit, 0),
      6,
    );
    combined.cells.forEach((cell, index) => {
      expect(cell.pm25).toBeLessThanOrEqual(cells[index].pm25);
      expect(cell.pm25).toBeGreaterThanOrEqual(cell.background);
    });
  });
  it("source shares and local weights sum to one", () => {
    stations.forEach((station) => {
      expect(
        attribution(station).shares.reduce(
          (sum, share) => sum + share.value,
          0,
        ),
      ).toBeCloseTo(1, 12);
      const weights = localWeights(station.latitude, station.longitude);
      expect(weights.traffic + weights.industry + weights.dust).toBeCloseTo(
        1,
        12,
      );
    });
  });
  it("IDW reproduces exact station values", () => {
    stations.forEach((station) =>
      expect(idw(station.latitude, station.longitude)).toBe(station.pm25),
    );
  });
  it("does not reduce background and caps cuts", () => {
    expect(
      delta(
        40,
        60,
        { traffic: 1, industry: 0, dust: 0 },
        { traffic: 50, industry: 0, dust: 0 },
      ),
    ).toBe(0);
    const weights = localWeights(18.62, 73.85);
    expect(
      delta(128, background, weights, {
        traffic: 100,
        industry: 100,
        dust: 100,
      }),
    ).toBe(
      delta(128, background, weights, { traffic: 50, industry: 60, dust: 70 }),
    );
  });
  it("computes demo metrics and preserves synthetic provenance", () => {
    const result = backtest(stations[0]);
    expect(result.target_source_type).toBe("synthetic");
    expect(result.metrics.mae).toBeGreaterThan(0);
    expect(result.metrics.mae).toBe(result.metrics.persistence_mae);
    expect(result.metrics.improvement_percent).toBe(0);
    expect(cells).toHaveLength(144);
    expect(
      stations.every((station) => station.source_type === "synthetic"),
    ).toBe(true);
  });
  it("keeps uncertainty ranges valid for low-concentration locations", () => {
    stations.forEach((station) => {
      const response = runScenario(station, {
        traffic: 50,
        industry: 60,
        dust: 70,
      });
      response.results.forEach((result) => {
        expect(result.reduction_low).toBeGreaterThanOrEqual(0);
        expect(result.reduction_high).toBeGreaterThanOrEqual(
          result.reduction_low,
        );
        expect(result.after).toBeLessThanOrEqual(result.before);
      });
      expect(attribution(station).background).toBeLessThanOrEqual(station.pm25);
    });
  });
});
