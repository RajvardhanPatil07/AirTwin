import { ArrowRight, Leaf, MoveUpRight } from "lucide-react";
import "./landing.css";

/**
 * FrameVitals landing-page composition, adapted for AirTwin.
 * No data fetching here: the public entry point stays fast, focused, and honest.
 */
const LENSES = [
  {
    number: "01",
    title: "Pollution, mapped",
    text: "Inspect Pune–PCMC station references and modeled PM2.5 hotspots on an interactive map. Select a location to carry it into the analysis.",
    route: "map",
    label: "Explore map",
  },
  {
    number: "02",
    title: "Forecasting",
    text: "Examine a 1–72 hour PM2.5 outlook, its time origin and uncertainty band. Predictions are always separated from readings.",
    route: "forecast",
    label: "Open forecast",
  },
  {
    number: "03",
    title: "Source hypotheses",
    text: "Compare estimated traffic, industrial, road-dust and regional contributions. These are spatial proxies, not measured source apportionment.",
    route: "sources",
    label: "View sources",
  },
  {
    number: "04",
    title: "Policy experiments",
    text: "Adjust traffic, industrial and dust controls. Compare three interventions and their combined modeled scenario.",
    route: "scenarios",
    label: "Compare actions",
  },
  {
    number: "05",
    title: "Historical validation",
    text: "Review held-out prediction errors, persistence baselines and evidence limits before interpreting any forecast.",
    route: "validation",
    label: "Check evidence",
  },
  {
    number: "06",
    title: "Transparent provenance",
    text: "Distinguish observed station readings, provider-modeled context and synthetic fallback data, with timestamps and assumptions.",
    route: "map",
    label: "See provenance",
  },
] as const;

const NAV = [
  { label: "Overview", route: "" },
  { label: "Map", route: "map" },
  { label: "Forecast", route: "forecast" },
  { label: "Sources", route: "sources" },
  { label: "Scenarios", route: "scenarios" },
  { label: "Validation", route: "validation" },
] as const;

export function LandingPage() {
  return (
    <div className="air-home">
      <a className="air-skip" href="#air-home-main">Skip to main content</a>
      <header className="air-home-nav">
        <div className="air-container air-home-nav-inner">
          <a href="#/" className="air-home-brand" aria-label="AirTwin home">
            <span className="air-brand-glyph"><Leaf size={17} strokeWidth={1.8} /></span>
            <strong>AirTwin</strong>
            <small>ENR / 01</small>
          </a>
          <nav aria-label="Site navigation" className="air-home-links">
            {NAV.map(({ label, route }) => (
              <a key={label} className={route === "" ? "is-current" : ""} aria-current={route === "" ? "page" : undefined}
                href={route ? "#/" + route : "#/"}>{label}</a>
            ))}
          </nav>
        </div>
      </header>

      <main id="air-home-main" className="air-container">
        <section className="air-home-hero" aria-labelledby="air-hero-title">
          <span className="air-hero-watermark" aria-hidden="true">AT/01</span>
          <p className="air-eyebrow">Urban environmental intelligence · Pune / PCMC</p>
          <h1 id="air-hero-title">Read the signal<br />in your air.</h1>
          <p className="air-home-lede">A digital twin for understanding pollution today, testing what might happen tomorrow, and comparing the interventions that could change it.</p>
          <div className="air-home-actions">
            <a className="air-btn-primary" href="#/map">Explore the city map <ArrowRight size={17}/></a>
            <a className="air-btn-secondary" href="#/scenarios">Compare interventions <MoveUpRight size={16}/></a>
            <span className="air-intro-chip"><i aria-hidden="true"/> Pune–PCMC study area</span>
          </div>
        </section>

        <div className="air-rule"><span>Inspection map</span></div>

        <section className="air-home-section" aria-labelledby="air-lenses-heading">
          <p className="air-eyebrow">What AirTwin explores</p>
          <h2 id="air-lenses-heading">Six analytical lenses.</h2>
          <p className="air-section-lede">From a citywide view to one practical decision. Each lens has its own page, so you only see the information you need.</p>
          <div className="air-lenses">
            {LENSES.map((item) => (
              <article className="air-lens" key={item.number}>
                <p className="air-eyebrow">{item.number}</p>
                <h3>{item.title}</h3>
                <p>{item.text}</p>
                <a href={"#/" + item.route}>{item.label} <ArrowRight size={14}/></a>
              </article>
            ))}
          </div>
        </section>

        <div className="air-rule"><span>Important limits</span></div>

        <section className="air-home-section air-home-limits" aria-labelledby="air-limits-heading">
          <p className="air-eyebrow">Honest about the evidence</p>
          <h2 id="air-limits-heading">A decision aid. Not proof.</h2>
          <p className="air-section-lede">AirTwin is a model of possible air-quality outcomes, not a measurement of policies that have already worked.</p>
          <div className="air-limit-grid">
            <p><span>01 /</span> Observed means a station or measurement-provider reading, with its original timestamp and freshness limits.</p>
            <p><span>02 /</span> Map grids, future forecasts and intervention outcomes are modeled, not additional physical sensors.</p>
            <p><span>03 /</span> Source contributions are assumption-driven estimates rather than causal source-apportionment measurements.</p>
            <p><span>04 /</span> Historical model results must not be presented as proof of accuracy for a different live provider forecast.</p>
          </div>
          <a className="air-evidence-link" href="#/validation">Inspect the evidence <ArrowRight size={17}/></a>
        </section>
      </main>
      <footer className="air-home-footer air-container">
        <div className="air-rule"><span>Fin</span></div>
        <div className="air-home-footer-inner">
          <span>AirTwin · Dot.local · ENR–01</span>
          <span>Pune–PCMC · OpenAQ · CAMS · Open-Meteo</span>
        </div>
      </footer>
    </div>
  );
}
