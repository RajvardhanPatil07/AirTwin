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
          className={"comparison " + (outdated ? "outdated" : "")}
          aria-label="Scenario concentration comparison"
        >
          <div className="comparison-heading">
            <div>
              <div className="eyebrow">SELECTED SCENARIO</div>
              <h2>{selected.name}</h2>
            </div>
            <span className="rank-badge">
              {selected.rank === 1 ? <Trophy size={11} /> : null}
              #{selected.rank}
            </span>
          </div>

          <div className="before-after">
            <div className="value-box">
              <span>
                {inputSource === "observed"
                  ? "Observed"
                  : inputSource === "synthetic"
                    ? "Synthetic"
                    : "Modeled"}
              </span>
              <strong>
                {number(selected.before)}
                <small> µg/m³</small>
              </strong>
            </div>

            <ArrowRight size={16} className="comparison-arrow" />

            <div className="value-box hatch">
              <span>After</span>
              <strong>
                {number(selected.after)}
                <small> µg/m³</small>
              </strong>
              <em>−{number(selected.reduction_percent)}%</em>
            </div>
          </div>
        </section>
      )}

      <section className="sliders" aria-label="Emission cut intensities">
        {ACTIONS.map((action) => (
          <label className="slider-row" key={action.id}>
            <span>{action.label}</span>
            <output>{cuts[action.id]}%</output>
            <input
              aria-label={action.label + " emission cut"}
              type="range"
              min={0}
              max={action.max}
              value={cuts[action.id]}
              onChange={(event) =>
                onCuts({ ...cuts, [action.id]: Number(event.target.value) })
              }
            />
          </label>
        ))}
      </section>

      <button className="run-button" onClick={onRun} disabled={busy}>
        <RotateCw size={13} className={busy ? "spin" : ""} />
        {busy ? "Calculating…" : outdated ? "Run scenario" : "Re-run scenario"}
      </button>

      {response && (
        <div
          className="results-table"
          role="region"
          aria-label="Interventions ranked by exposure benefit"
        >
          {response.results.map((result) => (
            <button
              key={result.id}
              className={
                "result-row result-simple-grid " +
                (selected?.id === result.id ? "active" : "")
              }
              aria-pressed={selected?.id === result.id}
              onClick={() => onSelect(result.id)}
            >
              <span className="rank-cell">
                {result.rank === 1 ? <Trophy size={13} /> : result.rank}
              </span>
              <span className="result-name">
                <b>{result.id === "combined" ? "Combined" : result.name}</b>
                <small>{compact(result.exposure_benefit)} weighted benefit</small>
              </span>
              <strong>−{number(result.reduction_percent)}%</strong>
            </button>
          ))}
        </div>
      )}

      {response && (
        <AssumptionsPanel
          assumptions={response.assumptions}
          title="Assumptions"
        />
      )}
    </div>
  );
}
