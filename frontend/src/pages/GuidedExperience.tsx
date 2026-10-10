import { useEffect, useState } from "react";
import {
  ArrowRight,
  ArrowLeft,
  ArrowDown,
  MapPin,
  Search,
  X,
  Leaf,
  Wind,
  Sun,
  Moon,
  CloudSun,
  Car,
  Factory,
  Construction,
  CircleHelp,
  ChevronDown,
  Check,
  Send,
  Play,
  Pause,
  ExternalLink,
  LocateFixed,
  Layers,
  Download,
  Sparkles,
} from "lucide-react";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip as ChartTooltip,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { SpotlightNavbar } from "../components/ui/spotlight-navbar";
import AnimatedButton from "../components/ui/animated-button";

import { api, loadDashboard } from "../lib/api";
import type { DashboardData } from "../types";
import type { Plan } from "../lib/operations";
import {
  GuidedBackendPanels,
  type GuidedPlanControls,
} from "../components/GuidedBackendPanels";

import { AirMap } from "../components/GuidedAirMap";

const steps = [
  "Place",
  "Air today",
  "Forecast",
  "Understand",
  "Try actions",
  "Plan",
  "Evidence",
  "Review",
];
const places = [
  {
    name: "Bhosari",
    area: "Pimpri-Chinchwad",
    lat: 18.6298,
    lng: 73.8482,
    value: 48,
  },
  {
    name: "Chinchwad",
    area: "Pimpri-Chinchwad",
    lat: 18.6273,
    lng: 73.7804,
    value: 36,
  },
  { name: "Hinjawadi", area: "Pune", lat: 18.5913, lng: 73.7389, value: 32 },
  { name: "Kothrud", area: "Pune", lat: 18.5074, lng: 73.8077, value: 29 },
  { name: "Hadapsar", area: "Pune", lat: 18.5089, lng: 73.926, value: 43 },
  { name: "Aundh", area: "Pune", lat: 18.559, lng: 73.807, value: 31 },
  {
    name: "Chakan",
    area: "Pimpri-Chinchwad",
    lat: 18.76,
    lng: 73.86,
    value: 52,
  },
];
type Place = (typeof places)[number];
const sources = [
  {
    name: "Traffic",
    detail: "Vehicle emissions",
    percent: 45,
    color: "#f16b6c",
    icon: Car,
  },
  {
    name: "Industry",
    detail: "Industrial emissions",
    percent: 30,
    color: "#268dbc",
    icon: Factory,
  },
  {
    name: "Road dust",
    detail: "Dust and construction",
    percent: 20,
    color: "#f2b84d",
    icon: Construction,
  },
  {
    name: "Other",
    detail: "Other sources",
    percent: 5,
    color: "#a7b2bc",
    icon: Layers,
  },
];
const plans = [
  {
    name: "Balanced plan",
    description: "A mix of traffic, industry and dust control",
    reduction: 24,
    cost: 500,
  },
  {
    name: "Higher impact",
    description: "Stronger action across all sources",
    reduction: 32,
    cost: 900,
  },
  {
    name: "Lower cost",
    description: "Focused on affordable, high-impact actions",
    reduction: 16,
    cost: 250,
  },
  {
    name: "Industry focus",
    description: "Prioritise industrial emission controls",
    reduction: 20,
    cost: 400,
  },
];
function planConstraint(
  index: number,
  budget: number,
  available: boolean[],
): string | null {
  const enabled =
    index === 3
      ? available[1]
      : index === 2
        ? available[0] && available[2]
        : available.slice(0, 3).every(Boolean);
  if (!enabled) return "Required actions are unavailable";
  if (plans[index].cost > budget) return "Exceeds your example budget";
  return null;
}
function Forecast({
  value,
  hours = 24,
  evidence = false,
  period = "1 month",
  reliability = 100,
}: {
  value: number;
  hours?: number;
  evidence?: boolean;
  period?: string;
  reliability?: number;
}) {
  const data = Array.from({ length: evidence ? 25 : 13 }, (_, i) => {
    const estimate = Math.round(
      value +
        Math.sin(i * 1.8) * 7 -
        i * 0.8 +
        (evidence ? (100 - reliability) * 0.12 : 0),
    );
    const monthStep =
      period === "1 year"
        ? 12
        : period === "6 months"
          ? 6
          : period === "3 months"
            ? 3
            : 1;
    return {
      time: evidence
        ? new Date(2026, 9 - monthStep, 10 + i * monthStep).toLocaleDateString(
            "en-IN",
            { day: "numeric", month: "short" },
          )
        : new Date(
            2026,
            9,
            10,
            10 + Math.round((i * hours) / 12),
          ).toLocaleString("en-IN", {
            day: "numeric",
            month: "short",
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
          }),
      estimate,
      measured:
        reliability === 0 || (i * 17) % 100 >= reliability
          ? null
          : Math.round(
              value + Math.sin(i * 1.8) * 7 - i * 0.8 + Math.sin(i * 2.4) * 18,
            ),
      upper: estimate + 20,
      lower: Math.max(5, estimate - 13),
    };
  });
  return (
    <div className="at-chart">
      <ResponsiveContainer
        width="100%"
        height="100%"
        minWidth={0}
        initialDimension={{ width: 500, height: 245 }}
      >
        {evidence ? (
          <LineChart
            data={data}
            margin={{ left: 0, right: 15, top: 15, bottom: 5 }}
          >
            <CartesianGrid stroke="var(--at-line)" vertical={false} />
            <XAxis
              dataKey="time"
              minTickGap={30}
              tick={{ fontSize: 11, fill: "var(--at-muted)" }}
            />
            <YAxis
              domain={[0, 125]}
              tick={{ fontSize: 11, fill: "var(--at-muted)" }}
              width={34}
            />
            <ChartTooltip />
            <Line
              isAnimationActive={false}
              name="Example station reading"
              dataKey="measured"
              stroke="#268dbc"
              strokeWidth={2}
              dot={{ r: 3 }}
            />
            <Line
              isAnimationActive={false}
              name="Example model estimate"
              dataKey="estimate"
              stroke="#6b9d45"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        ) : (
          <AreaChart
            data={data}
            margin={{ left: 0, right: 15, top: 15, bottom: 5 }}
          >
            <CartesianGrid stroke="var(--at-line)" />
            <XAxis
              dataKey="time"
              minTickGap={35}
              tick={{ fontSize: 11, fill: "var(--at-muted)" }}
            />
            <YAxis
              domain={[0, 125]}
              tick={{ fontSize: 11, fill: "var(--at-muted)" }}
              width={34}
            />
            <ChartTooltip />
            <Area
              isAnimationActive={false}
              dataKey="upper"
              name="Upper example estimate"
              stroke="none"
              fill="#d8ede2"
            />
            <Area
              isAnimationActive={false}
              dataKey="lower"
              name="Lower example estimate"
              stroke="none"
              fill="var(--at-panel)"
              fillOpacity={1}
            />
            <Area
              isAnimationActive={false}
              dataKey="estimate"
              name="Example PM2.5"
              stroke="var(--at-green)"
              strokeWidth={2.5}
              fill="transparent"
              dot={{
                r: 3,
                fill: "var(--at-green)",
                stroke: "var(--at-panel)",
                strokeWidth: 1.5,
              }}
            />
          </AreaChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
function PrimaryButton({
  children,
  onClick,
}: {
  children: React.ReactNode;
  onClick: () => void;
}) {
  return (
    <AnimatedButton className="at-primary" onClick={onClick}>
      {children}
      <ArrowRight size={17} />
    </AnimatedButton>
  );
}

export function GuidedExperience({ onAdvanced }: { onAdvanced: () => void }) {
  const [step, setStep] = useState(0),
    [selectedPlace, setPlace] = useState(places[0]);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [refresh, setRefresh] = useState(0);
  const [backendPlan, setBackendPlan] = useState<Plan | null>(null);
  const [planControls, setPlanControls] = useState<GuidedPlanControls>({
    budget: 300000,
    target: 12,
    unavailable: [],
  });
  useEffect(() => {
    let active = true;
    const load = () =>
      loadDashboard().then((data) => {
        if (active) setDashboard(data);
      });
    void load();
    const timer = window.setInterval(load, 900000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [refresh]);
  const connected = dashboard !== null && !dashboard.demo;
  const backendPlaces = connected
    ? dashboard.stations.map((station) => ({
        name: station.short_name,
        area: "Pune + PCMC",
        lat: station.latitude,
        lng: station.longitude,
        value: station.pm25,
      }))
    : places;
  const place =
    backendPlaces.find((item) => item.name === selectedPlace.name) ??
    backendPlaces[0];
  const backendLocation = connected
    ? dashboard.stations.find((station) => station.short_name === place.name)
    : undefined;
  const [query, setQuery] = useState("Bhosari"),
    [dark, setDark] = useState(false),
    [hours, setHours] = useState(24),
    [playing, setPlaying] = useState(false),
    [frame, setFrame] = useState(0);
  const [actions, setActions] = useState([30, 40, 50]),
    [calculated, setCalculated] = useState([30, 40, 50]);
  const [budget, setBudget] = useState(500),
    [target, setTarget] = useState(30),
    [available, setAvailable] = useState([true, true, true, false]),
    [planIndex, setPlanIndex] = useState(0);
  const [question, setQuestion] = useState(""),
    [answer, setAnswer] = useState(""),
    [period, setPeriod] = useState("1 month"),
    [station, setStation] = useState("Bhosari Industrial Area"),
    [reliability, setReliability] = useState(75);
  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(
      () => setFrame((f) => (f + 1) % (hours + 1)),
      850,
    );
    return () => clearInterval(timer);
  }, [playing, hours]);
  const reduction = calculated.reduce(
    (sum, v, i) => sum + (v * sources[i].percent) / 100,
    0,
  );
  const after = Math.max(5, Math.round(place.value * (1 - reduction / 100))),
    selectedPlan = plans[planIndex];
  const matches = backendPlaces.filter((p) =>
    p.name.toLowerCase().includes(query.toLowerCase()),
  );
  const choose = (p: Place) => {
    setPlace(p);
    setQuery(p.name);
  };
  const go = (index: number) => {
    setStep(index);
    setPlaying(false);
  };
  const titles = [
    "Understand the air.\nExplore what could help.",
    `Air in ${place.name}, ${place.area}`,
    `How might the air change in ${place.name}?`,
    `What may be adding to pollution in ${place.name}?`,
    `What could reduce pollution in ${place.name}?`,
    "Build a city-wide plan",
    "How well did the model work before?",
    "Your comparison at a glance",
  ];
  const descriptions = [
    "A little guidance, every step. Explore air quality in Pune and Pimpri-Chinchwad, understand what might change, and try actions for cleaner air.",
    "Explore nearby stations, weather and estimated fine particles.",
    "See estimated PM2.5 levels over the next hours and days.",
    "Explore estimated source contributions and ask questions.",
    connected
      ? "Adjust assumed reductions and compare the backend scenario."
      : "Adjust actions and compare an illustrative before-and-after estimate.",
    "Set a budget and compare action packages for Pune + PCMC.",
    connected
      ? "Check measured historical validation and its limits for this location."
      : "Compare example model estimates with example station readings.",
    `${place.name}, ${place.area} · Your area, forecast and selected actions.`,
  ];
  async function downloadReview() {
    if (backendLocation) {
      try {
        const result = await api.scenarios(
          backendLocation,
          {
            traffic: calculated[0],
            industry: calculated[1],
            dust: calculated[2],
          },
          false,
        );
        const blob = new Blob(
          [
            JSON.stringify(
              {
                location: backendLocation,
                scenario: result,
                plan: backendPlan,
              },
              null,
              2,
            ),
          ],
          { type: "application/json" },
        );
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = "airtwin-backend-review.json";
        anchor.click();
        URL.revokeObjectURL(url);
      } catch {
        window.alert("The backend review could not be saved. Please retry.");
      }
      return;
    }
    const blob = new Blob(
      [
        JSON.stringify(
          {
            data: "Illustrative demo, not live observations",
            place: place.name,
            current: place.value,
            estimatedAfter: after,
            actions: calculated,
            plan: selectedPlan,
          },
          null,
          2,
        ),
      ],
      { type: "application/json" },
    );
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "airtwin-example-review.json";
    anchor.click();
    URL.revokeObjectURL(url);
  }
  return (
    <div className={`at-app ${dark ? "at-dark dark" : ""}`}>
      <header className="at-header">
        <a
          className="at-brand"
          href="#"
          onClick={(event) => {
            event.preventDefault();
            go(0);
          }}
        >
          <span className="at-logo">
            <Leaf size={23} />
          </span>
          AirTwin
          <span className="at-brand-divider" />{" "}
          <span className="at-brand-caption">
            A little guidance, every step
          </span>
        </a>
        <div className="at-header-controls">
          <span className="at-region">
            <MapPin size={14} /> Pune + PCMC
          </span>
          <button
            className="at-theme"
            onClick={() => setDark(!dark)}
            aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
          >
            {dark ? <Sun size={17} /> : <Moon size={17} />}
          </button>
          <button className="at-advanced" onClick={onAdvanced}>
            Advanced view <ExternalLink size={13} />
          </button>
        </div>
      </header>
      <div className="at-navigation">
        <SpotlightNavbar
          items={steps.map((label, index) => ({
            label,
            href: `#step-${index + 1}`,
          }))}
          activeIndex={step}
          onItemClick={(_, index) => go(index)}
        />
      </div>
      <main className="at-main">
        <div className="at-demo">
          <CircleHelp size={15} />
          <span>
            {connected
              ? "Backend connected"
              : dashboard
                ? "Offline example"
                : "Connecting to backend…"}
          </span>
          <span className="at-demo-detail">
            {backendLocation
              ? `${backendLocation.source_type.toUpperCase()} · Updated ${new Date(backendLocation.timestamp).toLocaleString("en-IN", { timeZone: "Asia/Kolkata" })} IST. CAMS points are model samples, not monitors.`
              : dashboard
                ? (dashboard.warning ??
                  "Illustrative demo data. Backend disabled in this configuration.")
                : "Checking the API. Preview values are illustrative."}
          </span>
          <button
            className="at-text-button"
            onClick={() => setRefresh((value) => value + 1)}
          >
            Refresh connection
          </button>
        </div>
        <section className={`at-workspace ${step === 0 ? "at-welcome" : ""}`}>
          <div className="at-page-heading">
            {step > 0 && (
              <div className="at-step-label">
                STEP {step + 1} OF 8 <span>{steps[step]}</span>
              </div>
            )}
            <h1>{titles[step]}</h1>
            <p>{descriptions[step]}</p>
            {step > 0 && (
              <span className="at-location-chip">
                <MapPin size={13} />
                {place.name}
                <span>{connected ? "Backend data" : "Example scenario"}</span>
              </span>
            )}
          </div>
          {step === 0 && (
            <div className="at-welcome-content">
              <div className="at-place-form">
                <label htmlFor="at-place-search">
                  Where would you like to start?
                </label>
                <div className="at-search">
                  <Search size={19} />
                  <input
                    id="at-place-search"
                    value={query}
                    placeholder="Search an area in Pune + PCMC"
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && matches[0]) choose(matches[0]);
                    }}
                  />
                  <button
                    aria-label="Clear search"
                    onClick={() => setQuery("")}
                  >
                    <X size={16} />
                  </button>
                </div>
                <div className="at-search-results">
                  {matches.length ? (
                    matches.slice(0, 3).map((p) => (
                      <button key={p.name} onClick={() => choose(p)}>
                        <MapPin size={18} />
                        <span>
                          <b>{p.name}</b>
                          <small>{p.area}</small>
                        </span>
                        {place.name === p.name && <Check size={16} />}
                      </button>
                    ))
                  ) : (
                    <p>No matching area. Try Bhosari, Aundh or Kothrud.</p>
                  )}
                </div>
                <div className="at-welcome-actions">
                  <PrimaryButton onClick={() => go(1)}>
                    Check my area
                  </PrimaryButton>
                  <button className="at-secondary" onClick={() => go(5)}>
                    Plan city actions <ArrowRight size={17} />
                  </button>
                </div>
                <div className="at-popular">
                  <span>Or explore a popular area</span>
                  <div>
                    {backendPlaces.slice(2, 9).map((p) => (
                      <button onClick={() => choose(p)} key={p.name}>
                        {p.name}
                        <ArrowRight size={12} />
                      </button>
                    ))}
                  </div>
                </div>
              </div>
              <div className="at-welcome-map">
                <AirMap place={place} />
                <div className="at-map-note">
                  <LocateFixed size={18} />
                  <div>
                    <b>A clearer picture of your neighbourhood</b>
                    <span>
                      Start with a place. See the air, then explore what could
                      help.
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
          {!connected && step === 1 && (
            <div className="at-overview-grid">
              <div className="at-stat-stack">
                <section className="at-panel">
                  <h3>
                    Estimated fine particles <span>PM2.5</span>
                  </h3>
                  <div className="at-big-number">
                    {place.value}
                    <small>µg/m³</small>
                  </div>
                  <span className="at-badge">Example estimate</span>
                  <p>
                    A model estimate for the area, rather than a reading from a
                    station.
                  </p>
                  <div className="at-quality-scale">
                    <i />
                    <i />
                    <i />
                    <i />
                    <i />
                  </div>
                </section>
                <section className="at-panel">
                  <h3>Example weather</h3>
                  <div className="at-weather">
                    <CloudSun size={36} color="#d79d22" />
                    <span>
                      <b>28°C</b>
                      <small>Partly cloudy</small>
                    </span>
                    <Wind size={24} />
                    <span>
                      <b>5 km/h</b>
                      <small>Wind NNW</small>
                    </span>
                  </div>
                  <details>
                    <summary>
                      More weather details <ChevronDown size={13} />
                    </summary>
                    <p>
                      Humidity 62% · No rain in this example. Weather can
                      influence how pollution disperses.
                    </p>
                  </details>
                </section>
              </div>
              <AirMap place={place} heat />
              <section className="at-panel at-stations">
                <h3>Nearby air quality stations</h3>
                <p>Example station values · not current AQI</p>
                {[
                  {
                    name: "Bhosari Industrial Area",
                    distance: "2.1 km",
                    aqi: 162,
                    color: "#d48915",
                  },
                  {
                    name: "Chinchwad",
                    distance: "4.3 km",
                    aqi: 88,
                    color: "#188c52",
                  },
                  {
                    name: "Akurdi",
                    distance: "6.1 km",
                    aqi: 142,
                    color: "#d48915",
                  },
                ].map((s) => (
                  <div className="at-station" key={s.name}>
                    <span
                      className="at-station-dot"
                      style={{ borderColor: s.color }}
                    />
                    <div>
                      <b>{s.name}</b>
                      <small>{s.distance} from selected area</small>
                    </div>
                    <span style={{ color: s.color }}>
                      AQI <b>{s.aqi}</b>
                    </span>
                  </div>
                ))}
                <details>
                  <summary>
                    About these example stations <ArrowRight size={13} />
                  </summary>
                  <p>
                    Names show the regional context. Values are illustrative and
                    must not be used for health decisions.
                  </p>
                </details>
                <div className="at-station-note">
                  <CircleHelp size={17} />
                  <p>
                    Station AQI and modeled PM2.5 describe different things.
                    Compare each with its own units.
                  </p>
                </div>
                <PrimaryButton onClick={() => go(2)}>
                  See next 24 hours
                </PrimaryButton>
              </section>
            </div>
          )}
          {!connected && step === 2 && (
            <div className="at-two-columns">
              <section className="at-panel at-forecast-panel">
                <div className="at-segments">
                  {[6, 24, 72].map((h) => (
                    <button
                      className={hours === h ? "selected" : ""}
                      key={h}
                      onClick={() => {
                        setHours(h);
                        setFrame(0);
                      }}
                    >
                      Next {h} hours
                    </button>
                  ))}
                </div>
                <div className="at-chart-label">
                  Estimated PM2.5 <span>µg/m³</span>
                </div>
                <Forecast value={place.value} hours={hours} />
                <div className="at-legend">
                  <span>
                    <i style={{ background: "#08734b" }} />
                    Example model estimate
                  </span>
                  <span>
                    <i style={{ background: "#d8ede2" }} />
                    Illustrative uncertainty bounds
                  </span>
                </div>
                <details className="at-disclosure">
                  <summary>
                    How reliable is this? <ChevronDown size={15} />
                  </summary>
                  <p>
                    This preview uses example values. In real forecasts, the
                    range reflects uncertainty. Predictions may change with
                    weather, traffic and available observations.
                  </p>
                </details>
              </section>
              <section className="at-panel at-forecast-map">
                <h3>
                  Forecast map <span>Example hour {frame}</span>
                </h3>
                <AirMap
                  place={place}
                  heat
                  value={Math.max(12, place.value - Math.floor(frame / 2))}
                />
                <div className="at-playback">
                  <button
                    onClick={() => setPlaying(!playing)}
                    aria-label={playing ? "Pause forecast" : "Play forecast"}
                  >
                    {playing ? <Pause size={17} /> : <Play size={17} />}
                  </button>
                  <input
                    type="range"
                    min="0"
                    max={hours}
                    value={frame}
                    onChange={(e) => setFrame(Number(e.target.value))}
                    aria-label="Forecast hour"
                  />
                  <span>+{frame}h</span>
                </div>
              </section>
            </div>
          )}
          {!connected && step === 3 && (
            <div className="at-source-grid">
              <section className="at-panel at-source-panel">
                <div className="at-source-chart">
                  <ResponsiveContainer
                    width="100%"
                    height={240}
                    minWidth={0}
                    initialDimension={{ width: 250, height: 240 }}
                  >
                    <PieChart>
                      <Pie
                        isAnimationActive={false}
                        data={sources}
                        dataKey="percent"
                        innerRadius={75}
                        outerRadius={106}
                        paddingAngle={2}
                        stroke="none"
                      >
                        {sources.map((s) => (
                          <Cell key={s.name} fill={s.color} />
                        ))}
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                  <div>
                    <b>{place.value}</b>
                    <span>µg/m³</span>
                    <small>Example PM2.5</small>
                  </div>
                </div>
                <div className="at-source-list">
                  {sources.map((s) => (
                    <div key={s.name}>
                      <s.icon size={21} color={s.color} />
                      <span>{s.detail}</span>
                      <b>{s.percent}%</b>
                      <small>
                        {Math.round((place.value * s.percent) / 100)} µg/m³
                      </small>
                    </div>
                  ))}
                </div>
                <div className="at-source-foot">
                  <b>Assumed contributions</b>
                  <p>
                    Example shares illustrate the model. They do not identify
                    measured pollution sources.
                  </p>
                  <details>
                    <summary>
                      About sources and assumptions <ChevronDown size={14} />
                    </summary>
                    <p>
                      The demo assumes 45% traffic, 30% industry, 20% road dust
                      and 5% other sources. Real attribution needs validated
                      emissions and weather inputs.
                    </p>
                  </details>
                </div>
              </section>
              <section className="at-panel at-chat">
                <h3>
                  <Sparkles size={19} />
                  Ask AirTwin<span>Demo guide</span>
                </h3>
                <div className="at-chat-question">
                  What does this estimate mean?
                </div>
                <p>
                  The example estimate for {place.name} is{" "}
                  <b>{place.value} µg/m³</b> of PM2.5. The chart splits that
                  total into assumed source contributions.
                </p>
                <p className="at-chat-hint">
                  Explore the assumptions behind the numbers.
                </p>
                {answer && (
                  <div className="at-chat-answer" role="status">
                    {answer}
                  </div>
                )}
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    if (question.trim()) {
                      setAnswer(
                        `This offline guide cannot answer "${question.trim()}" with live evidence. For this example, source shares are assumptions and action effects scale with your selected reductions. Use Advanced view for the connected assistant.`,
                      );
                      setQuestion("");
                    }
                  }}
                >
                  <input
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="Ask a follow-up question…"
                    aria-label="Ask AirTwin"
                  />
                  <button
                    aria-label="Send question"
                    disabled={!question.trim()}
                  >
                    <Send size={17} />
                  </button>
                </form>
              </section>
            </div>
          )}
          {!connected && step === 4 && (
            <div className="at-action-grid">
              <section className="at-panel">
                <h3>
                  Adjust actions <span>Illustrative levels</span>
                </h3>
                {sources.slice(0, 3).map((s, i) => (
                  <div className="at-action" key={s.name}>
                    <s.icon color={s.color} size={24} />
                    <div>
                      <b>Reduce {s.name.toLowerCase()} emissions</b>
                      <div className="at-slider-row">
                        <input
                          aria-label={`Reduce ${s.name.toLowerCase()}`}
                          type="range"
                          min="0"
                          max="80"
                          step="5"
                          value={actions[i]}
                          onChange={(e) =>
                            setActions(
                              actions.map((v, n) =>
                                n === i ? Number(e.target.value) : v,
                              ),
                            )
                          }
                        />
                        <output>{actions[i]}%</output>
                      </div>
                      <small>
                        {
                          [
                            "Cleaner vehicles, less congestion",
                            "Cleaner fuel, improved controls",
                            "Road cleaning, construction dust control",
                          ][i]
                        }
                      </small>
                    </div>
                  </div>
                ))}
                <div className="at-current">
                  Current example estimate <b>{place.value} µg/m³</b>
                </div>
                <PrimaryButton onClick={() => setCalculated([...actions])}>
                  Calculate estimate
                </PrimaryButton>
              </section>
              <section className="at-panel">
                <h3>
                  Before & after <span>Estimated PM2.5</span>
                </h3>
                <div className="at-map-compare">
                  <div>
                    <h4>Current example</h4>
                    <AirMap place={place} value={place.value} heat compact />
                  </div>
                  <ArrowRight size={24} />
                  <div>
                    <h4>With selected actions</h4>
                    <AirMap place={place} value={after} heat compact />
                  </div>
                </div>
                <div className="at-result">
                  <span className="at-result-icon">
                    <ArrowDown size={24} />
                  </span>
                  <div>
                    <small>Estimated change</small>
                    <b>
                      {place.value} <ArrowRight size={19} />{" "}
                      <strong>{after} µg/m³</strong>
                      <span>
                        −
                        {Math.round(
                          ((place.value - after) / place.value) * 100,
                        )}
                        %
                      </span>
                    </b>
                  </div>
                  <p>
                    Simulated result, not a measured improvement. Actual results
                    may differ.
                  </p>
                </div>
              </section>
            </div>
          )}
          {!connected && step === 5 && (
            <div className="at-plan-grid">
              <section className="at-panel">
                <label className="at-range-label">
                  Total budget{" "}
                  <span>₹ {budget.toLocaleString("en-IN")} crore</span>
                  <input
                    type="range"
                    min="0"
                    max="2000"
                    step="50"
                    value={budget}
                    onChange={(e) => setBudget(Number(e.target.value))}
                  />
                </label>
                <div className="at-range-extents">
                  <span>₹ 0</span>
                  <span>₹ 2,000 crore</span>
                </div>
                <label className="at-range-label">
                  Target reduction <span>{target}%</span>
                  <input
                    type="range"
                    min="10"
                    max="50"
                    value={target}
                    onChange={(e) => setTarget(Number(e.target.value))}
                  />
                </label>
                <h3>Action availability</h3>
                {sources.map((s, i) => (
                  <div className="at-toggle-row" key={s.name}>
                    <s.icon size={19} color={s.color} />
                    <span>{s.detail}</span>
                    <button
                      role="switch"
                      aria-checked={available[i]}
                      aria-label={`Enable ${s.name.toLowerCase()} actions`}
                      className={available[i] ? "on" : ""}
                      onClick={() =>
                        setAvailable(
                          available.map((v, n) => (n === i ? !v : v)),
                        )
                      }
                    >
                      <i />
                    </button>
                  </div>
                ))}
                <p className="at-footnote">
                  Example costs and benefits. This is a planning exercise, not a
                  funded city proposal.
                </p>
              </section>
              <section className="at-panel">
                <h3>
                  Compare plans <span>Pune + PCMC</span>
                </h3>
                <div className="at-plan-options">
                  {plans.map((p, i) => {
                    const constraint = planConstraint(i, budget, available);
                    const meetsTarget = (p.reduction / 48) * 100 >= target;
                    return (
                      <button
                        key={p.name}
                        className={
                          planIndex === i
                            ? `selected ${constraint ? "infeasible" : ""}`
                            : ""
                        }
                        onClick={() => setPlanIndex(i)}
                      >
                        <span className="at-radio">
                          {planIndex === i &&
                            (constraint ? (
                              <CircleHelp size={12} />
                            ) : (
                              <Check size={12} />
                            ))}
                        </span>
                        <span>
                          <b>{p.name}</b>
                          <small>{p.description}</small>
                          <em>
                            {constraint ??
                              (meetsTarget
                                ? "Within budget · meets target"
                                : "Within budget · below target")}
                          </em>
                        </span>
                        <strong>−{p.reduction} µg/m³</strong>
                        <b>₹ {p.cost} crore</b>
                      </button>
                    );
                  })}
                </div>
                <details>
                  <summary>
                    View action list and assumptions <ChevronDown size={14} />
                  </summary>
                  <p>
                    {selectedPlan.name} targets an illustrative{" "}
                    {selectedPlan.reduction} µg/m³ reduction. Your target is{" "}
                    {target}%. Toggle availability to explore constraints; final
                    feasibility needs a validated optimisation model.
                  </p>
                </details>
              </section>
            </div>
          )}
          {!connected && step === 6 && (
            <div className="at-two-columns">
              <section className="at-panel">
                <div className="at-segments">
                  {["1 month", "3 months", "6 months", "1 year"].map((p) => (
                    <button
                      key={p}
                      className={period === p ? "selected" : ""}
                      onClick={() => setPeriod(p)}
                    >
                      {p}
                    </button>
                  ))}
                </div>
                <div className="at-chart-label">
                  Example PM2.5 comparison · {period} · {station}
                </div>
                <Forecast
                  value={
                    station === "Chinchwad"
                      ? 36
                      : station === "Akurdi"
                        ? 43
                        : 48
                  }
                  evidence
                  period={period}
                  reliability={reliability}
                />
                <div className="at-legend">
                  <span>
                    <i style={{ background: "#268dbc" }} />
                    Example station reading
                  </span>
                  <span>
                    <i style={{ background: "#6b9d45" }} />
                    Example model estimate
                  </span>
                </div>
              </section>
              <section className="at-panel">
                <label className="at-select-label">
                  Station
                  <select
                    value={station}
                    onChange={(e) => setStation(e.target.value)}
                  >
                    <option>Bhosari Industrial Area</option>
                    <option>Chinchwad</option>
                    <option>Akurdi</option>
                  </select>
                </label>
                <div className="at-evidence-stat">
                  <CircleHelp size={30} />
                  <div>
                    <span>Example average difference</span>
                    <b>
                      {station === "Chinchwad" ? 14 : 18} <small>µg/m³</small>
                    </b>
                    <p>
                      Illustrative comparison. This preview does not calculate a
                      real backtest.
                    </p>
                  </div>
                </div>
                <details>
                  <summary>
                    What does this mean? <ChevronDown size={14} />
                  </summary>
                  <p>
                    The average difference describes how far model estimates
                    were from station readings. Lower values indicate closer
                    agreement, but a single number does not describe all
                    uncertainty.
                  </p>
                </details>
                <h3 className="at-spaced">Include fewer stations</h3>
                <div className="at-segments">
                  {[100, 75, 50, 25, 0].map((v) => (
                    <button
                      key={v}
                      className={reliability === v ? "selected" : ""}
                      onClick={() => setReliability(v)}
                    >
                      {v}%
                    </button>
                  ))}
                </div>
                <p className="at-footnote">
                  {reliability}% of example stations included. Lower coverage
                  widens the example model difference. Use Advanced view for
                  actual sensor resilience results.
                </p>
              </section>
            </div>
          )}
          {!connected && step === 7 && (
            <>
              <div className="at-summary-top">
                <section>
                  <span>Current example estimate</span>
                  <b>
                    {place.value}
                    <small>µg/m³</small>
                  </b>
                  <p>Example weather · 28°C · Partly cloudy · 5 km/h</p>
                </section>
                <section>
                  <span>With your selected actions</span>
                  <b>
                    {after}
                    <small>µg/m³</small>
                    <em>
                      −{Math.round(((place.value - after) / place.value) * 100)}
                      %
                    </em>
                  </b>
                  <p>Simulated result, not a measured improvement.</p>
                </section>
              </div>
              <div className="at-review-grid">
                <section className="at-panel">
                  <h3>Forecast</h3>
                  <Forecast value={place.value} />
                  <button className="at-text-button" onClick={() => go(2)}>
                    View forecast <ArrowRight size={14} />
                  </button>
                </section>
                <section className="at-panel">
                  <h3>Assumed sources</h3>
                  {sources.map((s) => (
                    <div className="at-review-source" key={s.name}>
                      <s.icon size={17} color={s.color} />
                      <span>{s.name}</span>
                      <b>{s.percent}%</b>
                    </div>
                  ))}
                  <button className="at-text-button" onClick={() => go(3)}>
                    View details <ArrowRight size={14} />
                  </button>
                </section>
                <section className="at-panel">
                  <h3>City-wide example plan</h3>
                  <b
                    className={`at-plan-name ${planConstraint(planIndex, budget, available) ? "infeasible" : ""}`}
                  >
                    {planConstraint(planIndex, budget, available) ? (
                      <CircleHelp size={17} />
                    ) : (
                      <Check size={17} />
                    )}
                    {selectedPlan.name}
                  </b>
                  <strong className="at-plan-saving">
                    −{selectedPlan.reduction} µg/m³
                  </strong>
                  <p>₹ {selectedPlan.cost} crore · Example cost</p>
                  <p
                    className={
                      planConstraint(planIndex, budget, available)
                        ? "at-plan-warning"
                        : ""
                    }
                  >
                    {planConstraint(planIndex, budget, available) ??
                      "Within your budget; required actions are available."}
                  </p>

                  <ul>
                    {sources.slice(0, 3).map((s, i) => (
                      <li key={s.name}>
                        {s.name}: {calculated[i]}% reduction
                      </li>
                    ))}
                  </ul>
                  <button className="at-text-button" onClick={() => go(5)}>
                    View plan <ArrowRight size={14} />
                  </button>
                </section>
                <section className="at-panel">
                  <h3>Model evidence</h3>
                  <CircleHelp size={27} />
                  <b className="at-review-evidence">
                    {station === "Chinchwad" ? 14 : 18} <small>µg/m³</small>
                  </b>
                  <p>
                    {station} · Example average difference. Live validation is
                    available in Advanced view.
                  </p>
                  <button className="at-text-button" onClick={() => go(6)}>
                    View evidence <ArrowRight size={14} />
                  </button>
                </section>
              </div>
            </>
          )}
          {connected && backendLocation && dashboard && (
            <GuidedBackendPanels
              step={step}
              location={backendLocation}
              dashboard={dashboard}
              hours={hours}
              onHours={setHours}
              actions={actions}
              onActions={setActions}
              calculated={calculated}
              onCalculate={() => setCalculated([...actions])}
              plan={backendPlan}
              onPlan={setBackendPlan}
              planControls={planControls}
              onPlanControls={setPlanControls}
            />
          )}
          {step > 0 && (
            <footer className="at-page-footer">
              <button
                className="at-secondary"
                onClick={() => go(step === 7 ? 4 : step - 1)}
              >
                <ArrowLeft size={16} />
                {step === 7 ? "Adjust actions" : "Back"}
              </button>
              <span>Your progress is kept as you explore.</span>
              {step === 7 ? (
                <button className="at-primary" onClick={downloadReview}>
                  {connected ? "Save review" : "Save example review"}{" "}
                  <Download size={17} />
                </button>
              ) : (
                <PrimaryButton onClick={() => go(step + 1)}>
                  Next: {steps[step + 1]}
                </PrimaryButton>
              )}
            </footer>
          )}
        </section>
        <div className="at-bottom-note">
          <span>
            <Leaf size={14} /> A clearer view. More informed choices.
          </span>
          <span>
            Pune & Pimpri-Chinchwad ·{" "}
            {connected ? "Connected experience" : "Example experience"}
          </span>
        </div>
      </main>
    </div>
  );
}
