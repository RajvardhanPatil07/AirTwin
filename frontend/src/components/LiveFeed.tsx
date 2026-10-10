import { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { operations, type Feed } from "../lib/operations";
import { dateLabel, timeLabel } from "../lib/format";

export function LiveFeed({ replay }: { replay: boolean }) {
  const [feed, setFeed] = useState<Feed | null>(null);
  const [error, setError] = useState(false);
  const [checked, setChecked] = useState(0);
  useEffect(() => {
    let active = true;
    const refresh = () => operations.feed().then(next => {
      if (active) { setFeed(next); setError(false); }
    }).catch(() => active && setError(true));
    refresh();
    const timer = window.setInterval(refresh, 30000);
    return () => { active = false; window.clearInterval(timer); };
  }, [checked]);
  return <section className="live-feed" aria-label="Observed station AQI feed">
    <div className="section-heading"><div><h2>Observed station AQI</h2><p className="helper">IITM Pune · provider-published index, separate from PM2.5 concentration{replay && " · current feed alongside historical replay"}</p></div>
      <button className="status-chip" onClick={() => setChecked(x => x + 1)}><RefreshCw size={12} /> Check feed</button></div>
    <p className="helper" role="status">{error ? "Feed connection unavailable. Last received records retain their measurement timestamps." : feed ? `${feed.fresh_count} stations with readings within 3 hours. Source checked ${feed.checked_at ? `${dateLabel(feed.checked_at)} ${timeLabel(feed.checked_at)} IST` : "pending"}.` : "Checking observed station feed…"}</p>
    <div className="feed-records">{feed?.records.filter(r => r.status !== "stale").map(record => <article className="feed-record" key={`${record.id}-${record.timestamp}`}>
      <span className={`feed-state ${record.status}`}>{record.status === "fresh" ? "OBSERVED · FRESH" : "OBSERVED · DELAYED"}</span>
      <strong>{record.name}</strong><span className="feed-value">{record.value.toFixed(0)} <small>AQI</small></span>
      <span>{dateLabel(record.timestamp)} · {timeLabel(record.timestamp)} IST</span>
      <a href={record.source_url} target="_blank" rel="noreferrer">Provider source</a>
    </article>)}</div>
    {feed && !feed.fresh_count && <p className="api-warning">No fresh station indices currently available. Processing cannot make delayed source readings current.</p>}
  </section>;
}
