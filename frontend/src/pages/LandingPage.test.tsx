import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { LandingPage } from "./LandingPage";

describe("FrameVitals-inspired AirTwin landing page", () => {
  const markup = renderToStaticMarkup(<LandingPage />);

  it("displays the supplied reference's major visual landmarks", () => {
    expect(markup).toContain('class="air-home-hero"');
    expect(markup).toContain('class="air-hero-star"');
    expect(markup).toContain('class="air-hero-orb"');
    expect(markup).toContain('class="air-red-band"');
    expect(markup).toContain("AIR");
    expect(markup).toContain("HAS A");
    expect(markup).toContain("PULSE.");
    expect(markup).toContain("START THE TOUR");
  });

  it("links to all five independently accessible workspaces", () => {
    for (const route of ["map", "forecast", "sources", "scenarios", "validation"]) {
      expect(markup).toContain('href="#/' + route + '"');
    }
  });

  it("uses a real public GitHub destination with safe external-link attributes", () => {
    expect(markup).toContain("https://github.com/RajvardhanPatil07/AirTwin");
    expect(markup).toContain('rel="noopener noreferrer"');
    expect(markup).toContain('href="#/map"');
  });

  it("keeps measured and modeled claims distinct", () => {
    expect(markup).toContain("observed sensor readings");
    expect(markup).toContain("modeled predictions");
    expect(markup).toContain("not measured policy effects");
  });
});
