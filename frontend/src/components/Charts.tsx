import {
  CartesianGrid,
  Legend,
  Line,
  ComposedChart,
  Area,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  PieChart,
  Pie,
  Cell as PieCell,
} from "recharts";
import type {
  AttributionResponse,
  BacktestResponse,
  ForecastResponse,
  SeriesPoint,
  SourceType,
} from "../types";
import { dateLabel, number, timeLabel } from "../lib/format";
import { DataBadge } from "./DataBadge";
import { AssumptionsPanel } from "./AssumptionsPanel";

function SeriesChart({
  series,
  backtest = false,
  targetSource,
  demo,
}: {
  series: SeriesPoint[];
  backtest?: boolean;
  targetSource: SourceType;
  demo: boolean;
}) {
  return (
    <div
      className="chart"
      role="img"
      aria-label={
        backtest
          ? "Historical target, prediction and persistence comparison in micrograms per cubic metre"
          : "Historical target and modeled PM2.5 forecast in micrograms per cubic metre"
      }
    >
      <ResponsiveContainer
        width="100%"
        height="100%"
        initialDimension={{ width: 500, height: 280 }}
      >
        <ComposedChart
          data={series.map((point) => ({
            ...point,
            band: point.p10 === null ? null : [point.p10, point.p90],
          }))}
          margin={{ top: 12, right: 14, left: -12, bottom: 4 }}
        >
          <CartesianGrid
            stroke="var(--border)"
            strokeDasharray="3 3"
            vertical={false}
          />
          <XAxis
            dataKey="timestamp"
            tickFormatter={(value) =>
              backtest
                ? new Date(value).toLocaleDateString("en-IN", {
                    timeZone: "Asia/Kolkata",
                    day: "numeric",
                    month: "short",
                  })
                : timeLabel(value)
            }
            minTickGap={65}
            tick={{ fontSize: 10, fill: "var(--muted)" }}
          />
          <YAxis tick={{ fontSize: 10, fill: "var(--muted)" }} />
          <Tooltip
            labelFormatter={(label) =>
              `${dateLabel(String(label))} · ${timeLabel(String(label))} IST`
            }
            contentStyle={{
              background: "var(--surface)",
              color: "var(--text)",
              borderColor: "var(--border)",
              borderRadius: 8,
            }}
            formatter={(value) =>
              typeof value === "number"
                ? `${number(value)} µg/m³`
                : String(value)
            }
          />
          <Legend wrapperStyle={{ fontSize: 10, paddingTop: 10 }} />
          <Area
            dataKey="band"
            name={demo ? "MODELED illustrative band" : "MODELED p10–p90 band"}
            fill="#0b7495"
            fillOpacity={0.1}
            stroke="none"
            legendType="none"
            tooltipType="none"
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="actual"
            name={`${targetSource.toUpperCase()} ${backtest ? "target" : "history"}`}
            stroke="var(--chart-target)"
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="predicted"
            name={backtest ? "MODELED predictor" : "MODELED projection"}
            stroke="var(--chart-predicted)"
            strokeWidth={2}
            strokeDasharray="6 4"
            dot={false}
          />
          {backtest && (
            <Line
              dataKey="persistence"
              name="MODELED persistence"
              stroke="var(--chart-baseline)"
              strokeDasharray="3 3"
              strokeWidth={1}
              dot={false}
            />
          )}
          <Line
            dataKey="p10"
            name={demo ? "MODELED illustrative lower" : "MODELED p10"}
            stroke="#9aa9a2"
            strokeDasharray="2 3"
            dot={false}
            legendType="none"
          />
          <Line
            dataKey="p90"
            name={demo ? "MODELED illustrative upper" : "MODELED p90"}
            stroke="#9aa9a2"
            strokeDasharray="2 3"
            dot={false}
            legendType="none"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ForecastChart({
  data,
  hours,
  onHours,
  demo,
  replay = false,
}: {
  data: ForecastResponse;
  hours: number;
  onHours: (hours: number) => void;
  demo: boolean;
  replay?: boolean;
}) {
  return (
    <section className="tab-content">
      <div className="section-heading">
        <div>
          <div className="eyebrow">PM2.5 · µg/m³</div>
          <h2>{demo ? "Illustrative pollution outlook" : "PM2.5 forecast"}</h2>
        </div>
        <select
          aria-label="Forecast horizon"
          value={hours}
          onChange={(event) => onHours(Number(event.target.value))}
        >
          {(replay ? [24] : [24, 48, 72]).map((h) => (
            <option key={h} value={h}>
              {h} hours
            </option>
          ))}
        </select>
      </div>
      <div className="badge-line">
        <DataBadge source={data.history_source_type} detail="HISTORY" />
        <DataBadge
          source={data.source_type}
          detail={demo ? "ILLUSTRATIVE" : "FORECAST"}
        />
      </div>
      <SeriesChart
        series={data.series}
        targetSource={data.history_source_type}
        demo={demo}
      />
      {data.history_reference && (
        <p className="helper">
          Temporal history reference: sensor {data.history_reference}. Forecast
          origin is the latest displayed history timestamp.
        </p>
      )}
      {data.shap && (
        <section
          className="shap-panel"
          aria-label="24-hour TreeSHAP forecast explanation"
        >
          <div className="eyebrow">MODELED · WHY THE 24-HOUR FORECAST?</div>
          <p className="helper">
            Contributions explain the 24-hour forecast in µg/m³, separately
            from source shares. Positive values raise this forecast.
          </p>
          {Object.entries(data.shap.groups).map(([name, value]) => (
            <div className="shap-row" key={name}>
              <span>{name}</span>
              <div>
                <i
                  style={{
                    width: `${(Math.abs(value) / Math.max(1, ...Object.values(data.shap!.groups).map(Math.abs))) * 100}%`,
                    background: value >= 0 ? "var(--orange)" : "var(--blue)",
                  }}
                />
              </div>
              <b>
                {value > 0 ? "+" : ""}
                {number(value, 2)}
              </b>
            </div>
          ))}
          <p className="helper">
            Base {number(data.shap.base_value, 2)} + contributions ={" "}
            {number(data.shap.prediction, 2)} µg/m³ · {data.shap.method}
          </p>
        </section>
      )}
      <AssumptionsPanel
        title="Forecast assumptions"
        assumptions={data.assumptions}
      />
    </section>
  );
}

export function BacktestChart({
  data,
  demo,
}: {
  data: BacktestResponse;
  demo: boolean;
}) {
  const m = data.metrics;
  return (
    <section className="tab-content">
      <div className="eyebrow">CHRONOLOGICAL VALIDATION</div>
      <h2>
        {demo
          ? "Synthetic backtest demonstration"
          : "Historical forecast backtest"}
      </h2>
      <div className="badge-line">
        <DataBadge source={data.target_source_type} detail="TARGET" />
        <DataBadge source="modeled" detail="PREDICTION" />
      </div>
      <p className="helper">
        {data.method} · {dateLabel(data.series[0].timestamp)} to{" "}
        {dateLabel(data.series.at(-1)!.timestamp)}
      </p>
      <div className="metric-grid">
        {[
          ["MAE", `${number(m.mae, 2)} µg/m³`],
          ["RMSE", `${number(m.rmse, 2)} µg/m³`],
          ["vs persistence", `${number(m.improvement_percent)}%`],
          ["Interval coverage", `${number(m.interval_coverage)}%`],
        ].map(([label, value]) => (
          <div key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      {m.improvement_percent < 0 && (
        <p className="validation-warning" role="status">
          Model loses to persistence on this holdout. Reported improvement is
          negative.
        </p>
      )}
      {!demo && m.interval_coverage < 70 && (
        <p className="validation-warning">
          p10–p90 coverage is low on this holdout; uncertainty is not well
          calibrated.
        </p>
      )}
      <SeriesChart
        series={data.series}
        backtest
        targetSource={data.target_source_type}
        demo={demo}
      />
      <p className="helper">
        R² {number(m.r2, 3)} · Persistence MAE {number(m.persistence_mae, 2)}{" "}
        µg/m³.{" "}
        {demo && "The demo predictor equals persistence, so improvement is 0%."}
      </p>
      {data.seasonal_baseline && (
        <p className="helper">
          Pooled training-only seasonal baseline MAE:{" "}
          {number(data.seasonal_baseline.mae, 2)} µg/m³. CV folds:{" "}
          {data.cv?.length ?? 0}.
        </p>
      )}
      <AssumptionsPanel
        title="Validation limits"
        assumptions={data.assumptions}
      />
    </section>
  );
}

export function AttributionChart({ data }: { data: AttributionResponse }) {
  return (
    <section className="tab-content">
      <div className="section-heading">
        <div>
          <div className="eyebrow">SOURCE CONTRIBUTIONS</div>
          <h2>Where might it come from?</h2>
        </div>
        <DataBadge source={data.source_type} detail="PROXY" />
      </div>
      <p className="helper">
        Concentration shares, including regional background. These are assumed
        sources, not SHAP explanations.
      </p>
      <div className="donut-layout">
        <div
          className="donut"
          role="img"
          aria-label="Proxy source contribution shares"
        >
          <ResponsiveContainer
            width="100%"
            height="100%"
            initialDimension={{ width: 250, height: 220 }}
          >
            <PieChart>
              <Pie
                data={data.shares}
                dataKey="value"
                nameKey="name"
                innerRadius="60%"
                outerRadius="85%"
                paddingAngle={2}
                stroke="none"
              >
                {data.shares.map((share) => (
                  <PieCell key={share.name} fill={share.color} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value) => `${number(Number(value) * 100)}%`}
                contentStyle={{
                  background: "var(--surface)",
                  color: "var(--text)",
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="source-list">
          {data.shares.map((share) => (
            <div key={share.name}>
              <span>
                <i style={{ background: share.color }} />
                {share.name}
              </span>
              <strong>{number(share.value * 100)}%</strong>
            </div>
          ))}
        </div>
      </div>
      <div className="summary-note">
        Regional background: <b>{number(data.background)} µg/m³</b>.
        Interventions act only on local excess.
      </div>
      <AssumptionsPanel
        title="Source attribution assumptions"
        assumptions={data.assumptions}
      />
    </section>
  );
}
