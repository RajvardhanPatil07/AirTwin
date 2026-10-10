import assert from "node:assert/strict";
import { chromium } from "playwright";

const base = process.env.FRONTEND_URL || "http://127.0.0.1:5173";
const browser = await chromium.launch({headless: true, args: ["--no-sandbox"]});
const page = await browser.newPage({viewport:{width:1320,height:920}});
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));

try {
  const health = await page.request.get(base + "/backend/api/health", {timeout:30000});
  assert.equal(health.status(),200, "FastAPI is genuinely running behind Vite's /backend proxy");
  const healthData = await health.json();
  assert.equal(healthData.status,"ok");

  const stationsResponse = await page.request.get(base + "/backend/api/stations?region=pcmc", {timeout:30000});
  assert.equal(stationsResponse.status(),200);
  const stationData = await stationsResponse.json();
  assert.ok(stationData.stations.length > 0);
  const stationId = stationData.stations[0].id;

  const forecast = await page.request.get(base + "/backend/api/forecast?location_id=" +
    encodeURIComponent(stationId) + "&hours=24&region=pcmc", {timeout:60000});
  assert.equal(forecast.status(),200, "Real backend forecast endpoint must respond");
  assert.ok((await forecast.json()).series.length > 20);

  const timeline = await page.request.get(base + "/backend/api/timeline?region=pcmc", {timeout:60000});
  assert.equal(timeline.status(),200, "Spatial forecast timeline endpoint must respond");
  assert.ok((await timeline.json()).frames.length >= 2);

  const scenarios = await page.request.post(base + "/backend/api/scenarios", {
    data:{location_id:stationId,region:"pcmc",cuts:{traffic:20,industry:30,dust:30}},timeout:60000,
  });
  assert.equal(scenarios.status(),200, "Real backend scenario computation must respond");
  assert.ok((await scenarios.json()).results.find((item) => item.id === "combined"));

  await page.goto(base, {waitUntil:"domcontentloaded",timeout:45000});
  await page.getByRole("button",{name:/Explore as guest/i}).click();
  await page.locator(".fv-overview-cards").waitFor({timeout:35000});
  assert.equal(await page.getByText(/Showing synthetic demo data\./i).count(),0,
    "A valid API must never be silently replaced by frontend synthetic fallback");

  const nav = page.getByRole("navigation",{name:"Main navigation"});
  await nav.getByRole("button",{name:"Map",exact:true}).click();
  await page.getByRole("button",{name:"Analytics",exact:true}).click();
  await page.getByRole("button",{name:/Research & policy modeling/i}).click();
  await page.getByRole("button",{name:/Compare modeled actions/i}).click();
  await page.locator(".fv-research-figure").first().waitFor({timeout:60000});

  await nav.getByRole("button",{name:"Forecast",exact:true}).click();
  await page.locator(".fv-forecast-chart-card").waitFor();
  await page.getByRole("button",{name:"48h",exact:true}).click();
  assert.equal(new URL(page.url()).searchParams.get("hours"),"48");
  await page.reload({waitUntil:"domcontentloaded"});
  await page.getByRole("button",{name:"48h",exact:true}).waitFor();
  assert.ok((await page.getByRole("button",{name:"48h",exact:true}).getAttribute("class")).includes("selected"),
    "Forecast hours survive refresh");
  assert.equal(new URL(page.url()).searchParams.get("page"),"forecast");
  assert.deepEqual(errors, [], "No browser JavaScript crashes");
  console.log("Connected AirTwin smoke passed: /api/health, stations, LightGBM forecast, spatial timeline, interventions, live-source UI, 48-hour route refresh.");
} finally {
  await browser.close();
}
