import type {
  AttributionResponse,
  BacktestResponse,
  ForecastResponse,
  ScenarioResponse,
  Station,
} from "../types";

export interface JourneySummary {
  currentPm25: number;
  forecastPeak: number | null;
  validationImprovement: number | null;
  validationMae: number | null;
  dominantSource: string | null;
  dominantSourceShare: number | null;
  bestAction: string | null;
  bestActionReduction: number | null;
}

export function buildJourneySummary(
  location: Station,
  forecast: ForecastResponse | null,
  backtest: BacktestResponse | null,
  attribution: AttributionResponse | null,
  scenario: ScenarioResponse | null,
): JourneySummary {
  const forecastValues =
    forecast?.series
      .map((point) => point.predicted)
      .filter((value): value is number => value !== null) ?? [];
  const forecastPeak = forecastValues.length
    ? Math.max(...forecastValues)
    : null;

  const localShares =
    attribution?.shares.filter(
      (share) => !share.name.toLowerCase().includes("background"),
    ) ?? [];
  const dominant = localShares.reduce<(typeof localShares)[number] | null>(
    (best, share) => (!best || share.value > best.value ? share : best),
    null,
  );

  const individual =
    scenario?.results.filter((result) => result.id !== "combined") ?? [];
  const bestAction = individual.reduce<(typeof individual)[number] | null>(
    (best, result) =>
      !best || result.exposure_benefit > best.exposure_benefit ? result : best,
    null,
  );

  return {
    currentPm25: location.pm25,
    forecastPeak,
    validationImprovement: backtest?.metrics?.improvement_percent ?? null,
    validationMae: backtest?.metrics?.mae ?? null,
    dominantSource: dominant?.name ?? null,
    dominantSourceShare: dominant?.value ?? null,
    bestAction: bestAction?.name ?? null,
    bestActionReduction: bestAction?.reduction_percent ?? null,
  };
}
