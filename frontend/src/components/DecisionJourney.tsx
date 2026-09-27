import {
  CheckCircle2,
  MapPin,
  PieChart,
  SlidersHorizontal,
  TrendingUp,
} from "lucide-react";
import type {
  AttributionResponse,
  BacktestResponse,
  ForecastResponse,
  ScenarioResponse,
  Station,
} from "../types";
import { number } from "../lib/format";
import { buildJourneySummary } from "../lib/journey";

export type JourneyTab =
  | "Overview"
  | "Forecast"
  | "Backtest"
  | "Sources"
  | "Scenarios";

export function DecisionJourney({
  location,
  forecast,
  backtest,
  attribution,
  scenario,
  active,
  onSelect,
}: {
  location: Station;
  forecast: ForecastResponse | null;
  backtest: BacktestResponse | null;
  attribution: AttributionResponse | null;
  scenario: ScenarioResponse | null;
  active: string;
  onSelect: (tab: JourneyTab) => void;
}) {
  const summary = buildJourneySummary(
    location,
    forecast,
    backtest,
    attribution,
    scenario,
  );
  const validation =
    summary.validationImprovement === null
      ? "No holdout"
      : (summary.validationImprovement >= 0 ? "+" : "") +
        number(summary.validationImprovement) +
        "% vs persistence";

  const steps: {
    tab: JourneyTab;
    kicker: string;
    label: string;
    value: string;
    detail: string;
    icon: typeof MapPin;
  }[] = [
    {
      tab: "Overview",
      kicker: "01 · OBSERVE",
      label: "Current air",
      value: number(summary.currentPm25) + " µg/m³",
      detail: location.source_type.toUpperCase() + " baseline",
      icon: MapPin,
    },
    {
      tab: "Forecast",
      kicker: "02 · PREDICT",
      label: "Forecast signal",
      value:
        summary.forecastPeak === null
          ? "Calculating…"
          : number(summary.forecastPeak) + " µg/m³ peak",
      detail: "Modeled future concentration",
      icon: TrendingUp,
    },
    {
      tab: "Backtest",
      kicker: "03 · VALIDATE",
      label: "Historical evidence",
      value: validation,
      detail:
        summary.validationMae === null
          ? "Validation unavailable here"
          : "MAE " + number(summary.validationMae) + " µg/m³",
      icon: CheckCircle2,
    },
    {
      tab: "Sources",
      kicker: "04 · EXPLAIN",
      label: "Likely local driver",
      value: summary.dominantSource ?? "Calculating…",
      detail:
        summary.dominantSourceShare === null
          ? "Proxy attribution"
          : number(summary.dominantSourceShare * 100) + "% proxy share",
      icon: PieChart,
    },
    {
      tab: "Scenarios",
      kicker: "05 · ACT",
      label: "Best single action",
      value: summary.bestAction ?? "Calculating…",
      detail:
        summary.bestActionReduction === null
          ? "Compare three interventions"
          : "−" + number(summary.bestActionReduction) + "% at this location",
      icon: SlidersHorizontal,
    },
  ];

  return (
    <section className="decision-journey" aria-label="AirTwin decision journey">
      {steps.map((step) => {
        const Icon = step.icon;
        return (
          <button
            key={step.tab}
            type="button"
            className={"journey-step " + (active === step.tab ? "active" : "")}
            onClick={() => onSelect(step.tab)}
            aria-pressed={active === step.tab}
          >
            <span className="journey-kicker">{step.kicker}</span>
            <span className="journey-heading">
              <Icon size={15} aria-hidden="true" />
              {step.label}
            </span>
            <strong>{step.value}</strong>
            <small>{step.detail}</small>
          </button>
        );
      })}
    </section>
  );
}
