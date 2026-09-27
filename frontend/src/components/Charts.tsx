import {
  Area,
  CartesianGrid,
  Cell as PieCell,
  ComposedChart,
  Legend,
  Line,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
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
          ? "Historical PM2.5 target, model and persistence comparison"
          : "Historical PM2.5 and modeled forecast"
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
          margin={{ top: 12, right: 10, left: -18, bottom: 2 }}
        >
          <CartesianGrid
            stroke="var(--border)"
            strokeDasharray="2 5"
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
            tick={{ fontSize: 12, fill: "var(--muted)" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 12, fill: "var(--muted)" }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            labelFormatter={(label) =>
              dateLabel(String(label)) + " · " + timeLabel(String(label))
            }
            contentStyle={{
              background: "var(--surface)",
              color: "var(--text)",
              borderColor: "var(--border)",
              borderRadius: 8,
              fontSize: 12,
            }}
            formatter={(value) =>
              typeof value === "number"
                ? number(value) + " µg/m³"
                : String(value)
            }
          />
          <Legend wrapperStyle={{ fontSize: 10, paddingTop: 8 }} />
          <Area
            dataKey="band"
            name={demo ? "Illustrative band" : "p10–p90"}
            fill="var(--blue)"
            fillOpacity={0.08}
            stroke="none"
            legendType="none"
            tooltipType="none"
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="actual"
            name={targetSource.toUpperCase()}
            stroke="var(--chart-target)"
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="predicted"
            name="Forecast"
            stroke="var(--chart-predicted)"
            strokeWidth={2}
            dot={false}
          />
          {backtest && (
            <Line
              dataKey="persistence"
              name="Persistence"
              stroke="var(--chart-baseline)"
              strokeDasharray="3 4"
              strokeWidth={1.2}
              dot={false}
            />
          )}
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
          <div className="eyebrow">PREDICT</div>
          <h2>PM2.5 forecast</h2>
        </div>
        <select
          aria-label="Forecast horizon"
          value={hours}
          onChange={(event) => onHours(Number(event.target.value))}
        >
          {(replay ? [24] : [24, 48, 72]).map((value) => (
            <option key={value} value={value}>
              {value}h
            </option>
          ))}
        </select>
      </div>

      <div className="badge-line">
        <DataBadge source={data.history_source_type} detail="HISTORY" />
        <DataBadge source={data.source_type} detail="FORECAST" />
      </div>

      <SeriesChart
        series={data.series}
        targetSource={data.history_source_type}
        demo={demo}
      />

      {!demo && data.history_reference?.startsWith("cams-") && (
        <p className="validation-warning">
          CAMS regional forecast · local validation unavailable.
        </p>
      )}

      {data.shap && (
        <section className="shap-panel" aria-label="Forecast feature explanation">
          <div className="eyebrow">24H FEATURE EFFECT</div>
          {Object.entries(data.shap.groups).map(([name, value]) => (
            <div className="shap-row" key={name}>
              <span>{name}</span>
              <div>
                <i
                  style={{
                    width:
                      (Math.abs(value) /
                        Math.max(
                          1,
                          ...Object.values(data.shap!.groups).map(Math.abs),
                        )) *
                        100 +
                      "%",
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
        </section>
      )}

      <AssumptionsPanel
        title="Assumptions"
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
  const metrics = data.metrics;

  if (!metrics || data.available === false) {
    return (
      <section className="tab-content">
        <div className="eyebrow">VALIDATE</div>
        <h2>No local holdout</h2>
        <p className="helper">Switch to Pune + PCMC for LightGBM validation.</p>
        <AssumptionsPanel
          assumptions={data.assumptions}
          title="Limits"
        />
      </section>
    );
  }

  return (
    <section className="tab-content">
      <div className="section-heading">
        <div>
          <div className="eyebrow">VALIDATE</div>
          <h2>Historical backtest</h2>
        </div>
        <DataBadge source={data.target_source_type} detail="TARGET" />
      </div>

      <div className="metric-grid">
        {[
          ["MAE", number(metrics.mae, 2)],
          ["RMSE", number(metrics.rmse, 2)],
          ["vs baseline", number(metrics.improvement_percent) + "%"],
          ["Coverage", number(metrics.interval_coverage) + "%"],
        ].map(([label, value]) => (
          <div key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>

      {metrics.improvement_percent < 0 && (
        <p className="validation-warning" role="status">
          Model trails persistence on this holdout.
        </p>
      )}

      <SeriesChart
        series={data.series}
        backtest
        targetSource={data.target_source_type}
        demo={demo}
      />

      <div className="chart-footnote">
        {dateLabel(data.series[0].timestamp)} →{" "}
        {dateLabel(data.series.at(-1)!.timestamp)}
      </div>

      <AssumptionsPanel
        title="Limits"
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
          <div className="eyebrow">EXPLAIN</div>
          <h2>Likely source mix</h2>
        </div>
        <DataBadge source={data.source_type} detail="PROXY" />
      </div>

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
                innerRadius="66%"
                outerRadius="88%"
                paddingAngle={2}
                stroke="none"
              >
                {data.shares.map((share) => (
                  <PieCell key={share.name} fill={share.color} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value) => number(Number(value) * 100) + "%"}
                contentStyle={{
                  background: "var(--surface)",
                  color: "var(--text)",
                  border: "1px solid var(--border)",
                  borderRadius: 8,
                  fontSize: 12,
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
        Background <b>{number(data.background)} µg/m³</b>
      </div>

      <AssumptionsPanel
        title="Assumptions"
        assumptions={data.assumptions}
      />
    </section>
  );
}
