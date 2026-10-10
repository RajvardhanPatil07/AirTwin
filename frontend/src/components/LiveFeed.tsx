import { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { operations, type Feed } from "../lib/operations";
import { dateLabel, timeLabel } from "../lib/format";

function measurementStatus(timestamp: string, now: number) {
  const age = now - Date.parse(timestamp);
  if (!Number.isFinite(age) || age < 0) return "stale";
  return age < 3 * 3600000 ? "fresh" : age <= 24 * 3600000 ? "delayed" : "stale";
}

export function FeedReadings({ feed, now }: { feed: Feed; now: number }) {
  const records = feed.records.map(record => ({ ...record, status: measurementStatus(record.timestamp, now) }));
  const fresh = records.filter(record => record.status === "fresh");
  const delayed = records.filter(record => record.status !== "fresh");
  const cards = (items: typeof records) => <div className="feed-records">{items.map(record => <article className="feed-record" key={record.id}>
    <span className={`feed-state ${record.status}`}>{record.status === "fresh" ? "OBSERVED · LIVE" : record.status === "delayed" ? "OBSERVED · DELAYED" : "OBSERVED · STALE"}</span>
    <strong>{record.name}</strong><span className="feed-value">{record.value.toFixed(0)} <small>AQI</small></span>
    <span>Measured {dateLabel(record.timestamp)} · {timeLabel(record.timestamp)} IST</span>
    <a href={record.source_url} target="_blank" rel="noreferrer">Provider source</a>
  </article>)}</div>;
  return <>
    <p className="helper">{fresh.length} stations with readings less than 3 hours old. IITM refreshes every 15 minutes while the backend runs.</p>
    {cards(fresh)}
    {!fresh.length && <p className="api-warning">No fresh station AQI readings available. See delayed readings below.</p>}
    {!!delayed.length && <details className="feed-delayed">
      <summary>Unavailable or delayed · {delayed.length} stations</summary>
      <p className="helper">Last known readings. These are excluded from the live feed.</p>
      {cards(delayed)}
    </details>}
  </>;
}

export function LiveFeed({ replay }: { replay: boolean }) {
  const [feed, setFeed] = useState<Feed | null>(null);
  const [error, setError] = useState(false);
  const [checked, setChecked] = useState(0);
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    let active = true;
    const refresh = () => {
      setNow(Date.now());
      return operations.feed().then(next => {
        if (active) { setFeed(next); setError(false); setNow(Date.now()); }
      }).catch(() => active && setError(true));
    };
    refresh();
    const timer = window.setInterval(refresh, 60000);
    return () => { active = false; window.clearInterval(timer); };
  }, [checked]);
  return <section className="live-feed" aria-label="Observed station AQI feed">
    <div className="section-heading"><div><h2>Observed station AQI</h2><p className="helper">IITM Pune · provider-published index{replay && " · current feed alongside historical replay"}</p></div>
      <button className="status-chip" onClick={() => setChecked(x => x + 1)}><RefreshCw size={12} /> Check feed</button></div>
    <p className="helper">Observed AQI uses index units. CAMS / Open-Meteo PM2.5 values elsewhere are modeled estimates in µg/m³.</p>
    <p className="helper">Last successful IITM fetch: {feed?.checked_at ? `${dateLabel(feed.checked_at)} ${timeLabel(feed.checked_at)} IST` : "pending"}.</p>
    <p className="helper" role="status">{error ? "Feed connection unavailable. Previous readings retain their measurement times and continue aging." : !feed ? "Checking observed station feed…" : "Checking the backend every minute; Check feed does not trigger an IITM scrape."}</p>
    {feed && <FeedReadings feed={feed} now={now} />}
  </section>;
}
