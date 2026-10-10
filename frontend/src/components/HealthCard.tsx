import { HeartPulse } from "lucide-react";
import type { ForecastResponse, SourceType } from "../types";
import { subIndex } from "../lib/naqi";
import { number, timeLabel, dateLabel } from "../lib/format";
import { DataBadge } from "./DataBadge";

export function HealthCard({
  pm25,
  source,
  forecast,
}: {
  pm25: number;
  source: SourceType;
  forecast: ForecastResponse | null;
}) {
  const now = subIndex(pm25);
  const future = (forecast?.series ?? []).filter(
    (point) => point.predicted !== null,
  );
  const next24 = future.slice(0, 24);
  const peak = next24.reduce<(typeof next24)[number] | null>(
    (best, point) =>
      !best || (point.predicted ?? 0) > (best.predicted ?? 0) ? point : best,
    null,
  );
  const peakBand = peak ? subIndex(peak.predicted ?? 0) : null;
  const cleanest = next24
    .filter((point) => {
      const hour = Number(timeLabel(point.timestamp).slice(0, 2));
      return hour >= 6 && hour <= 20;
    })
    .reduce<(typeof next24)[number] | null>(
      (best, point) =>
        !best || (point.predicted ?? 0) < (best.predicted ?? 0) ? point : best,
      null,
    );
  const gauge = Math.min(now.aqi, 500) / 500;
  return (
    <section className="health-card" aria-label="Indicative air quality and health advice">
      <div className="health-gauge" style={{ ["--level" as string]: gauge, ["--band" as string]: now.color }}>
        <svg viewBox="0 0 120 70" aria-hidden="true">
          <path d="M10 64 A50 50 0 0 1 110 64" className="gauge-track" />
          <path
            d="M10 64 A50 50 0 0 1 110 64"
            className="gauge-value"
            pathLength={1}
            style={{ strokeDasharray: `${gauge} 1`, stroke: now.color }}
          />
        </svg>
        <div>
          <strong>{now.aqi}</strong>
          <span>{now.name}</span>
        </div>
      </div>
      <div className="health-copy">
        <div className="eyebrow">
          <HeartPulse size={12} /> INDICATIVE NAQI · PM2.5 {number(pm25)} µg/m³
        </div>
        <p>{now.advice}</p>
        {peak && peakBand && (
          <p className="health-forecast">
            Next 24 h peak:{" "}
            <b className="band-chip" style={{ background: peakBand.color, color: peakBand.band >= 4 ? "#fff" : undefined }}>
              {peakBand.name}
            </b>{" "}
            ({number(peak.predicted ?? 0)} µg/m³) at {timeLabel(peak.timestamp)}
            {cleanest && (
              <>
                {" "}· best daytime window {timeLabel(cleanest.timestamp)},{" "}
                {dateLabel(cleanest.timestamp)}
              </>
            )}
          </p>
        )}
        <div className="badge-line">
          <DataBadge source={source} detail="NOW" />
          {peak && <DataBadge source="modeled" detail="FORECAST" />}
        </div>
        <small>
          CPCB PM2.5 sub-index breakpoints applied to hourly values; official
          AQI uses 24-hour averages across pollutants. General guidance, not
          medical advice.
        </small>
      </div>
    </section>
  );
}
