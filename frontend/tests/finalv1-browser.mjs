import assert from "node:assert/strict";
import {mkdir} from "node:fs/promises";
import {chromium} from "playwright";

const base = process.env.FRONTEND_URL || "http://127.0.0.1:5173";
const browser = await chromium.launch({headless: true, args:["--no-sandbox"]});
const page = await browser.newPage({viewport:{width:1440,height:960},deviceScaleFactor:1});
const runtimeErrors = [];
page.on("pageerror", error => runtimeErrors.push(error.message));
await mkdir("screenshots", {recursive:true});
const route = async (pageName) => {
  await page.getByRole("navigation",{name:"Main navigation"}).getByRole("button",{name:pageName,exact:true}).click();
  await page.waitForTimeout(500);
};
try {
  await page.goto(base, {waitUntil:"domcontentloaded",timeout:45000});
  await page.getByRole("button",{name:/explore as guest/i}).click();
  await page.locator(".fv-overview-cards").waitFor({timeout:30000});
  await page.locator(".leaflet-container").waitFor({timeout:30000});
  await page.waitForFunction(() => {
    const tiles = [...globalThis.document.querySelectorAll(".leaflet-tile-loaded")];
    return tiles.some((tile) => tile instanceof globalThis.HTMLImageElement && tile.naturalWidth > 0);
  }, { timeout: 35000 });
  assert.equal(await page.locator(".fv-nav button").count(),3, "Exactly three primary pages");
  await page.screenshot({path:"screenshots/overview-desktop.png",fullPage:true});
  await route("Map");
  await page.getByRole("button",{name:"PM2.5"}).first().click();
  assert.ok(await page.getByRole("option",{name:/AQI/i}).isDisabled(), "No invented AQI layer");
  await page.screenshot({path:"screenshots/map-metrics-desktop.png",fullPage:true});
  await page.getByRole("button",{name:"PM2.5"}).first().click();
  await page.getByRole("button",{name:/Most affected/i}).click();
  await page.locator(".fv-ranked-menu").waitFor();
  await page.screenshot({path:"screenshots/map-ranked-desktop.png",fullPage:true});
  await page.getByRole("button",{name:"Analytics",exact:true}).click();
  await page.locator(".fv-ai-panel").waitFor();
  await page.getByRole("button",{name:/Research & policy modeling/i}).click();
  await page.getByRole("button",{name:/Compare modeled actions/i}).click();
  await page.locator(".fv-research-figure").first().waitFor({timeout:30000});
  await page.screenshot({path:"screenshots/analytics-desktop.png",fullPage:true});
  await route("Forecast");
  await page.locator(".fv-forecast-chart-card").waitFor();
  await page.getByRole("button",{name:/Effects on/i}).click();
  await page.getByRole("slider",{name:"Select forecast time"}).fill("8");
  await page.screenshot({path:"screenshots/forecast-desktop.png",fullPage:true});
  await page.setViewportSize({width:390,height:844});
  await page.waitForTimeout(700);
  assert.equal(await page.getByRole("button",{name:/Map layers/i}).getAttribute("aria-expanded"), "false", "Map layer controls collapse on mobile");
  await page.screenshot({path:"screenshots/forecast-mobile.png",fullPage:true});
  const overflow = await page.evaluate(() => globalThis.document.documentElement.scrollWidth - globalThis.document.documentElement.clientWidth);
  assert.ok(overflow <= 2, "Mobile layout must not cause horizontal document overflow: " + overflow);
  assert.deepEqual(runtimeErrors, [], "No uncaught JS errors: " + runtimeErrors.join("; "));
  console.log("AirTwin finalv1 browser smoke passed: guest, Overview, Map dropdown, hotspots, Analytics scenarios, Forecast, mobile layout.");
} finally {await browser.close();}
