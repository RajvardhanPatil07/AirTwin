import { ArrowRight, ArrowUpRight } from "lucide-react";
import "./landing.css";

/**
 * AirTwin's public entry, modeled on the supplied screenshot of the
 * FrameVitals landing page (framevitals.vercel.app).
 * No data, maps, or model runs are fetched until a workspace link is opened.
 */
const DESTINATIONS = [
  {
    number: "01",
    title: "Explore the map.",
    body: "Understand PM2.5 levels, station readings and modeled city hotspots.",
    href: "#/map",
    action: "Open city map",
  },
  {
    number: "02",
    title: "See what comes next.",
    body: "Explore air-quality forecasts and their uncertainty over the next 72 hours.",
    href: "#/forecast",
    action: "View forecasts",
  },
  {
    number: "03",
    title: "Understand the sources.",
    body: "Compare the likely contributions from traffic, industry, dust and background.",
    href: "#/sources",
    action: "Explore sources",
  },
  {
    number: "04",
    title: "Test a cleaner future.",
    body: "Compare traffic, industrial and dust-control interventions before acting.",
    href: "#/scenarios",
    action: "Compare actions",
  },
  {
    number: "05",
    title: "Check the evidence.",
    body: "Inspect historical tests, reference baselines and model limitations.",
    href: "#/validation",
    action: "View validation",
  },
] as const;

function Starburst() {
  return (
    <svg className="air-hero-star" viewBox="0 0 160 160" aria-hidden="true" focusable="false">
      <path d="M80 1V159M1 80H159M24 24L136 136M136 24L24 136" />
    </svg>
  );
}

export function LandingPage() {
  return (
    <div className="air-home">
      <a className="air-skip" href="#air-main">Skip to content</a>
      <header className="air-home-nav">
        <div className="air-home-nav-inner">
          <a href="#/" className="air-home-brand" aria-label="AirTwin home">AirTwin</a>
          <a className="air-home-github" href="https://github.com/RajvardhanPatil07/AirTwin"
            target="_blank" rel="noopener noreferrer" aria-label="AirTwin on GitHub (opens in a new tab)">
            GITHUB <ArrowUpRight size={14} strokeWidth={2.5} />
          </a>
        </div>
      </header>

      <main id="air-main">
        <section className="air-home-hero" aria-labelledby="air-hero-title">
          <div className="air-hero-grid" aria-hidden="true" />
          <div className="air-hero-orb" aria-hidden="true" />
          <div className="air-red-band" aria-hidden="true" />
          <div className="air-hero-inner">
            <Starburst />
            <div className="air-hero-copy">
              <p className="air-hero-eyebrow">AIR QUALITY / URBAN FUTURES</p>
              <h1 id="air-hero-title" className="air-display">
                <span>THE CITY</span>
                <span className="air-display-indent">HAS A</span>
                <span>PULSE.</span>
              </h1>
              <p className="air-home-lede">
                Understand where pollution rises, what drives it, and what could make tomorrow's air cleaner.
              </p>
              <div className="air-home-actions">
                <a className="air-hero-button air-hero-button-primary" href="#/map">EXPLORE AIR TWIN</a>
                <a className="air-hero-button air-hero-button-outline" href="#/forecast">
                  FORECAST LAB <ArrowUpRight size={14} strokeWidth={2.3}/>
                </a>
              </div>
            </div>
            <span className="air-hero-caption" aria-hidden="true">PUNE · PIMPRI-CHINCHWAD / ENR–01</span>
          </div>
        </section>

        <section className="air-explore" id="explore" aria-labelledby="air-explore-heading">
          <div className="air-container">
            <div className="air-section-intro">
              <p className="air-small-label">01 / THE EXPERIENCE</p>
              <h2 id="air-explore-heading">EXPLORE THE<br/><em>CITY TWIN.</em></h2>
              <p>Five linked workspaces. One clearer picture of your city's air.</p>
            </div>
            <div className="air-destinations">
              {DESTINATIONS.map((item) => (
                <a className="air-destination" href={item.href} key={item.number}>
                  <span className="air-destination-number">{item.number}</span>
                  <span className="air-destination-content">
                    <strong>{item.title}</strong>
                    <small>{item.body}</small>
                  </span>
                  <span className="air-destination-action">
                    <span>{item.action}</span>
                    <ArrowUpRight size={20} strokeWidth={1.6} />
                  </span>
                </a>
              ))}
            </div>
          </div>
        </section>

        <section className="air-caveat" aria-labelledby="air-caveat-title">
          <div className="air-container air-caveat-inner">
            <div>
              <p className="air-small-label">02 / THE EVIDENCE</p>
              <h2 id="air-caveat-title">EVIDENCE,<br/><em>NOT ASSUMPTION.</em></h2>
            </div>
            <div className="air-caveat-description">
              <p>AirTwin distinguishes observed sensor readings from modeled predictions and synthetic demonstrations. Proposed pollution-control outcomes are estimates, not measured policy effects.</p>
              <a href="#/validation">EXPLORE THE VALIDATION <ArrowRight size={17}/></a>
            </div>
          </div>
        </section>
      </main>
      <footer className="air-home-footer">
        <div className="air-container air-footer-row">
          <span className="air-footer-logo">AirTwin</span>
          <span>DOT.LOCAL / ENR–01</span>
          <a href="#/map">ENTER THE CITY TWIN <ArrowUpRight size={15}/></a>
        </div>
      </footer>
    </div>
  );
}
