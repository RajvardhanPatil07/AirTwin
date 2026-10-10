import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { FeedReadings } from "./LiveFeed";
import type { Feed } from "../lib/operations";

const feed: Feed = {
  source_type: "observed", assumptions: [], checked_at: "2026-10-10T12:00:00Z", fresh_count: 2,
  records: [
    { id: "fresh", name: "Fresh station", indicator: "AQI", value: 121, timestamp: "2026-10-10T11:00:00Z", received_at: "2026-10-10T12:00:00Z", status: "fresh", age_hours: 1, source_url: "https://ews.tropmet.res.in/pune/index.php" },
    { id: "old", name: "Delayed station", indicator: "AQI", value: 134, timestamp: "2026-10-10T09:00:00Z", received_at: "2026-10-10T12:00:00Z", status: "fresh", age_hours: 0, source_url: "https://ews.tropmet.res.in/pune/index.php" },
  ],
};

describe("Observed AQI feed", () => {
  it("separates delayed measurements despite a recent fetch and cached fresh status", () => {
    const html = renderToStaticMarkup(createElement(FeedReadings, { feed, now: Date.parse("2026-10-10T12:00:00Z") }));
    const split = html.indexOf("Unavailable or delayed");
    expect(html.slice(0, split)).toContain("Fresh station");
    expect(html.slice(0, split)).not.toContain("Delayed station");
    expect(html.slice(split)).toContain("Delayed station");
    expect(html).toContain("Measured");
  });

  it("ages cached readings out of the live section during an outage", () => {
    const html = renderToStaticMarkup(createElement(FeedReadings, { feed, now: Date.parse("2026-10-12T12:00:00Z") }));
    expect(html).toContain("No fresh station AQI readings available");
    expect(html).not.toContain("OBSERVED · LIVE");
    expect(html).toContain("OBSERVED · STALE");
  });
});
