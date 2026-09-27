import { ArrowRight, RotateCw, Trophy } from "lucide-react";
import type {
  ActionId,
  Cuts,
  ScenarioResponse,
  ScenarioResult,
  SourceType,
} from "../types";
import { ACTIONS } from "../mocks/engine";
import { compact, number } from "../lib/format";
import { AssumptionsPanel } from "./AssumptionsPanel";

interface Props {
  cuts: Cuts;
  onCuts: (cuts: Cuts) => void;
  response: ScenarioResponse | null;
  selected: ScenarioResult | null;
  onSelect: (id: ActionId) => void;
  onRun: () => void;
  outdated: boolean;
  busy: boolean;
  inputSource: SourceType;
}
export function ScenarioPanel({
  cuts,
  onCuts,
  response,
  selected,
  onSelect,
  onRun,
  outdated,
  busy,
  inputSource,
}: Props) {
  return (
    <div className="scenario-panel">
      {selected && (
        <section
          className={`comparison ${outdated ? "outdated" : ""}`}
          aria-label="Scenario concentration comparison"
        >
          <div className="comparison-heading">
            <div>
              <div className="eyebrow orange">MODELED SCENARIO</div>
              <h2>{selected.name}</h2>
            </div>
            <span className="rank-badge">
              <Trophy size={12} /> RANK #{selected.rank}
            </span>
          </div>
          <div className="before-after">
            <div className="value-box">
              <div className="mini-badge">
                {inputSource === "synthetic"
                  ? "SYNTHETIC DEMO INPUT"
                  : inputSource === "observed"
                    ? "OBSERVED · STATION"
                    : "MODELED · BASELINE"}
              </div>
              <span>Selected location baseline</span>
              <strong>
                {number(selected.before)} <small>µg/m³</small>
              </strong>
            </div>
            <ArrowRight size={18} className="comparison-arrow" />
            <div className="value-box hatch">
              <div className="mini-badge">MODELED SCENARIO</div>
              <span>After intervention</span>
              <strong>
                {number(selected.after)} <small>µg/m³</small>
              </strong>
            </div>
          </div>
        </section>
      )}
      <section className="sliders" aria-label="Emission cut intensities">
        {ACTIONS.map((action) => (
          <label className="slider-row" key={action.id}>
            <span>
              {action.label}
              <small>0–{action.max}% emission cut</small>
            </span>
            <input
              aria-label={`${action.label} emission cut`}
              type="range"
              min={0}
              max={action.max}
              value={cuts[action.id]}
              onChange={(event) =>
                onCuts({ ...cuts, [action.id]: Number(event.target.value) })
              }
            />
            <output>{cuts[action.id]}%</output>
          </label>
        ))}
      </section>
      <button className="run-button" onClick={onRun} disabled={busy}>
        <RotateCw size={13} className={busy ? "spin" : ""} />
        {busy ? "Calculating scenario…" : "Run scenario"}
      </button>
      {response && (
        <div
          className="results-table"
          role="region"
          aria-label="Interventions ranked by exposure benefit"
        >
          <div className="result-head result-grid">
            <span>RANK</span>
            <span>ACTION</span>
            <span>
              Δ PM2.5
              <br />
              <small>µg/m³ reduction</small>
            </span>
            <span>REDUCTION</span>
            <span>
              PEOPLE-WEIGHTED BENEFIT
              <br />
              <small>
                {selected?.population_source_type.toUpperCase()} POPULATION
              </small>
            </span>
          </div>
          {response.results.map((result) => (
            <button
              key={result.id}
              className={`result-row result-grid ${selected?.id === result.id ? "active" : ""}`}
              aria-pressed={selected?.id === result.id}
              onClick={() => onSelect(result.id)}
            >
              <span>
                {result.rank === 1 ? (
                  <Trophy size={16} className="trophy" />
                ) : (
                  result.rank
                )}
              </span>
              <b>
                {result.id === "combined" ? "Combined package" : result.name}
              </b>
              <span>
                {number(result.reduction_low)}–{number(result.reduction_high)}
              </span>
              <b>{number(result.reduction_percent)}%</b>
              <span>
                {compact(result.exposure_benefit)} <small>person·µg/m³</small>
              </span>
            </button>
          ))}
        </div>
      )}
      {response && <AssumptionsPanel assumptions={response.assumptions} />}
    </div>
  );
}
