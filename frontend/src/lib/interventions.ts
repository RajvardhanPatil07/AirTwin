import type { ScenarioResult } from "../types";

export function compareInterventions(results: ScenarioResult[]) {
  const individual = results
    .filter((result) => result.id !== "combined")
    .sort((a, b) => b.exposure_benefit - a.exposure_benefit);
  const best = individual[0];
  if (!best || best.exposure_benefit <= 0)
    return { best: null, status: "none" as const };
  if (individual.some((result) => result.exposure_benefit_low === undefined || result.exposure_benefit_high === undefined))
    return { best, status: "unavailable" as const };
  const separated = individual.slice(1).every((result) => best.exposure_benefit_low! > result.exposure_benefit_high!);
  return { best, status: separated ? "separated" as const : "overlap" as const };
}
