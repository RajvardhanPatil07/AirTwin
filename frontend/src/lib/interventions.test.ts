import { describe, expect, it } from "vitest";
import { runScenario, stations } from "../mocks/engine";
import { compareInterventions } from "./interventions";

const results = runScenario(stations[0], { traffic: 20, industry: 30, dust: 30 }).results;
describe("individual intervention evidence", () => {
  it("excludes the combined package and uses population-weighted benefit", () => {
    const compared = compareInterventions(results);
    expect(compared.best?.id).not.toBe("combined");
    expect(compared.best?.exposure_benefit).toBe(Math.max(...results.filter(r => r.id !== "combined").map(r => r.exposure_benefit)));
  });
  it("does not recommend an action at zero cuts", () => {
    expect(compareInterventions(runScenario(stations[0], { traffic: 0, industry: 0, dust: 0 }).results).status).toBe("none");
  });
  it("distinguishes overlapping bounds from a separated leader", () => {
    const individual = results.filter(r => r.id !== "combined");
    const separated = individual.map((r, i) => ({ ...r, exposure_benefit: i === 0 ? 100 : 10, exposure_benefit_low: i === 0 ? 80 : 5, exposure_benefit_high: i === 0 ? 120 : 15 }));
    expect(compareInterventions(separated).status).toBe("separated");
    expect(compareInterventions(separated.map(r => ({ ...r, exposure_benefit_high: 150 }))).status).toBe("overlap");
    expect(compareInterventions(individual.map(r => ({ ...r, exposure_benefit_low: undefined }))).status).toBe("unavailable");
  });
});
