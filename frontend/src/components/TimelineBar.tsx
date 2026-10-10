import { useEffect, useRef, useState } from "react";
import { Pause, Play, Clock3 } from "lucide-react";
import type { TimelineResponse } from "../types";
import { dateLabel, timeLabel } from "../lib/format";
import { DataBadge } from "./DataBadge";

export function TimelineBar({
  timeline,
  index,
  onIndex,
  loading,
}: {
  timeline: TimelineResponse | null;
  index: number;
  onIndex: (index: number) => void;
  loading: boolean;
}) {
  const [playing, setPlaying] = useState(false);
  const indexRef = useRef(index);
  indexRef.current = index;
  const frames = timeline?.frames ?? [];
  useEffect(() => {
    if (!playing || frames.length < 2) return;
    const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    const timer = window.setInterval(() => {
      const next = indexRef.current + 1;
      if (next >= frames.length) {
        setPlaying(false);
        return;
      }
      onIndex(next);
    }, reduce ? 2000 : 1100);
    return () => window.clearInterval(timer);
  }, [playing, frames.length, onIndex]);
  if (loading && !timeline)
    return (
      <div className="timeline-bar" role="status">
        <Clock3 size={14} /> Building forecast timeline…
      </div>
    );
  if (!frames.length) return null;
  const frame = frames[Math.min(index, frames.length - 1)];
  return (
    <div className="timeline-bar" aria-label="Forecast timeline">
      <button
        className="timeline-play"
        aria-label={playing ? "Pause forecast animation" : "Play forecast animation"}
        onClick={() => {
          if (!playing && index >= frames.length - 1) onIndex(0);
          setPlaying(!playing);
        }}
      >
        {playing ? <Pause size={14} /> : <Play size={14} />}
      </button>
      <div className="timeline-track">
        <input
          type="range"
          min={0}
          max={frames.length - 1}
          step={1}
          value={index}
          aria-label="Forecast hour"
          aria-valuetext={frame.hour === 0 ? "Now" : `plus ${frame.hour} hours`}
          onChange={(event) => {
            setPlaying(false);
            onIndex(Number(event.target.value));
          }}
        />
        <div className="timeline-ticks" aria-hidden="true">
          {frames.map((item, i) => (
            <span key={item.hour} className={i === index ? "active" : ""}>
              {item.hour === 0
                ? "Now"
                : i === index || item.hour % 12 === 0 || i === frames.length - 1
                  ? `+${item.hour}h`
                  : "·"}
            </span>
          ))}
        </div>
      </div>
      <div className="timeline-label">
        <strong>
          {frame.hour === 0 ? "Snapshot" : `+${frame.hour} h`} · {timeLabel(frame.timestamp)}
        </strong>
        <span>{dateLabel(frame.timestamp)}</span>
      </div>
      <DataBadge source={frame.source_type} detail={frame.hour === 0 ? "SNAPSHOT" : "FORECAST"} />
    </div>
  );
}
