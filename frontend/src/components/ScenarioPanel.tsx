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
import { compareInterventions } from "../lib/interventions";
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
  const comparison = compareInterventions(response?.results ?? []);
  return (
    <div className="scenario-panel">
      {selected && (
        <section
          className={`comparison ${outdated ? "outdated" : ""}`}
          aria-label="Scenario concentration comparison"
        >
          <div className="comparison-heading">
            <div>
              <h2>Clean-air scenario</h2>
              <p>{selected.name}</p>
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
          <div className="reduction-strip" aria-live="polite">
            <strong>Estimated reduction {number(selected.reduction_percent)}%</strong>
            <span>{outdated ? "Run to update" : "Modeled estimate"}</span>
          </div>
        </section>
      )}
      {response && (
        <section className="intervention-evidence" aria-label="Individual action comparison" aria-live="polite">
          <h3>{outdated ? "Previous action comparison" : "Which individual action helps most?"}</h3>
          <p>{comparison.best ? <><strong>{comparison.best.name}</strong> leads for the applied cuts, ranked across this region by population-weighted exposure reduction.</> : "No modeled exposure reduction at these cuts. Try increasing an intervention."}</p>
          <p>{comparison.status === "separated" ? "Its benefit range stays above the other individual actions within the tested sensitivity envelope." : comparison.status === "overlap" ? "Exposure-benefit ranges overlap. These bounds alone do not establish a robust winner; overlap does not prove the ranking reverses." : comparison.status === "unavailable" ? "This backend does not supply exposure sensitivity bounds. Ranking robustness is unavailable." : "The combined package adds the three individual effects; it is not a fourth independent policy."}</p>
          <small>Same snapshot and weather; cuts can differ by action. Sensitivity varies pass-through 0.6–0.8 and source scaling ±20%. These are assumption bounds, not confidence intervals. {selected?.population_source_type === "modeled" ? "Population uses WorldPop 2020 modeled counts." : "Population is synthetic."}</small>
        </section>
      )}
      <h3 className="intervention-heading">Adjust interventions</h3>
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
        <details className="ranked-actions" open>
          <summary>Compare all three actions and combined package</summary>
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
                {result.exposure_benefit_low !== undefined && result.exposure_benefit_high !== undefined && <small className="benefit-range">Range {compact(result.exposure_benefit_low)}–{compact(result.exposure_benefit_high)}</small>}
              </span>
            </button>
          ))}
        </div>
        </details>
      )}
      {response && <AssumptionsPanel assumptions={response.assumptions} />}
    </div>
  );
}
