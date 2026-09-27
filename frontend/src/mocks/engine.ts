import type {
  ActionId,
  AttributionResponse,
  BacktestResponse,
  Cell,
  Cuts,
  ForecastResponse,
  Metrics,
  ScenarioResponse,
  ScenarioResult,
  SeriesPoint,
  Station,
} from "../types";

export const BBOX = { south: 18.45, north: 18.8, west: 73.7, east: 73.98 };
export const DEMO_TIME = "2026-01-31T14:00:00+05:30";
export const DEFAULT_CUTS: Cuts = { traffic: 20, industry: 30, dust: 30 };
export const ACTIONS = [
  {
    id: "traffic" as const,
    name: "Traffic restriction",
    label: "Traffic",
    max: 50,
  },
  {
    id: "industry" as const,
    name: "Industrial controls",
    label: "Industrial controls",
    max: 60,
  },
  {
    id: "dust" as const,
    name: "Dust suppression",
    label: "Dust suppression",
    max: 70,
  },
];
export const DEMO_ASSUMPTIONS = [
  "All location readings and population counts in this demo are synthetic, not monitoring-station observations.",
  "Grid concentrations use inverse-distance interpolation (power 2) of six illustrative location values.",
  "Background is the 15th percentile of simultaneous demo readings, capped at each cell’s baseline; only local excess is reduced.",
  "Traffic, industry and dust are proxy weights, not measured chemical source contributions.",
  "Concentration pass-through is 0.7, with a 0.6–0.8 range and source weights varied ±20%. Weather stays constant.",
  "People-weighted benefit is reduction × synthetic cell population, not a count of people protected.",
];

const seeds: [string, string, string, number, number, number][] = [
  ["bhosari", "Bhosari MIDC", "Bhosari", 18.62, 73.85, 128],
  ["pimpri", "Pimpri", "Pimpri", 18.63, 73.8, 82],
  ["chakan", "Chakan MIDC", "Chakan", 18.76, 73.86, 139],
  ["hinjewadi", "Hinjewadi", "Hinjewadi", 18.59, 73.74, 56],
  ["shivajinagar", "Shivajinagar", "Shivajinagar", 18.53, 73.85, 74],
  ["hadapsar", "Hadapsar", "Hadapsar", 18.5, 73.93, 68],
];
export const stations: Station[] = seeds.map(
  ([id, name, short_name, latitude, longitude, pm25]) => ({
    id,
    name,
    short_name,
    latitude,
    longitude,
    pm25,
    timestamp: DEMO_TIME,
    source_type: "synthetic",
    assumptions: [DEMO_ASSUMPTIONS[0]],
  }),
);

export function colorFor(value: number) {
  return value <= 30
    ? "#22c55e"
    : value <= 60
      ? "#a3e635"
      : value <= 90
        ? "#facc15"
        : value <= 120
          ? "#f97316"
          : value <= 250
            ? "#ef4444"
            : "#7f1d1d";
}

export function idw(
  latitude: number,
  longitude: number,
  readings = stations,
): number {
  let sum = 0,
    weights = 0;
  for (const station of readings) {
    const distance2 =
      (latitude - station.latitude) ** 2 +
      ((longitude - station.longitude) *
        Math.cos((latitude * Math.PI) / 180)) **
        2;
    if (distance2 < 1e-12) return station.pm25;
    const weight = 1 / distance2;
    sum += station.pm25 * weight;
    weights += weight;
  }
  return weights ? sum / weights : 0;
}

function percentile(values: number[], fraction: number) {
  const sorted = [...values].sort((a, b) => a - b);
  const index = (sorted.length - 1) * fraction;
  return (
    sorted[Math.floor(index)] +
    (sorted[Math.ceil(index)] - sorted[Math.floor(index)]) * (index % 1)
  );
}
export const background = percentile(
  stations.map((s) => s.pm25),
  0.15,
);

export function localWeights(latitude: number, longitude: number): Cuts {
  const proximity = (lat: number, lon: number) =>
    Math.exp(-((latitude - lat) ** 2 + (longitude - lon) ** 2) / 0.003);
  const traffic = 0.6 + 0.5 * proximity(18.63, 73.8);
  const industry =
    0.3 + 2.5 * (proximity(18.62, 73.85) + proximity(18.76, 73.86));
  const dust = 0.5 + 0.6 * proximity(18.59, 73.74);
  const total = traffic + industry + dust;
  return {
    traffic: traffic / total,
    industry: industry / total,
    dust: dust / total,
  };
}

export const cells: Cell[] = Array.from({ length: 144 }, (_, i) => {
  const row = Math.floor(i / 12),
    col = i % 12;
  const dy = (BBOX.north - BBOX.south) / 12,
    dx = (BBOX.east - BBOX.west) / 12;
  const south = BBOX.south + row * dy,
    west = BBOX.west + col * dx;
  const latitude = south + dy / 2,
    longitude = west + dx / 2;
  const pm25 = idw(latitude, longitude);
  return {
    id: `cell-${row}-${col}`,
    latitude,
    longitude,
    bounds: [
      [south, west],
      [south + dy, west + dx],
    ],
    pm25,
    background: Math.min(background, pm25),
    population: Math.round(
      700 +
        9000 *
          Math.exp(
            -((latitude - 18.6) ** 2 + (longitude - 73.83) ** 2) / 0.009,
          ),
    ),
    population_source_type: "synthetic",
    local_weights: localWeights(latitude, longitude),
    source_type: "modeled",
    assumptions: DEMO_ASSUMPTIONS,
  };
});

export function delta(
  value: number,
  regional: number,
  weights: Cuts,
  cuts: Cuts,
  passThrough = 0.7,
) {
  const weightedCut = ACTIONS.reduce(
    (total, action) =>
      total +
      (weights[action.id] *
        Math.max(0, Math.min(cuts[action.id], action.max))) /
        100,
    0,
  );
  return Math.max(value - regional, 0) * weightedCut * passThrough;
}

export function runScenario(
  location: Station,
  cuts: Cuts,
  grid = cells,
): ScenarioResponse {
  const weights = localWeights(location.latitude, location.longitude);
  const packages: { id: ActionId; name: string; cuts: Cuts }[] = [
    { id: "combined", name: "Combined clean-air package", cuts: { ...cuts } },
    ...ACTIONS.map((action) => ({
      id: action.id,
      name: action.name,
      cuts: { traffic: 0, industry: 0, dust: 0, [action.id]: cuts[action.id] },
    })),
  ];
  const results = packages
    .map<ScenarioResult>((action) => {
      const reduction = delta(location.pm25, background, weights, action.cuts);
      const next = grid.map((cell) => ({
        ...cell,
        pm25: Math.max(
          cell.background,
          cell.pm25 -
            delta(cell.pm25, cell.background, cell.local_weights, action.cuts),
        ),
      }));
      return {
        ...action,
        rank: 0,
        before: location.pm25,
        after: location.pm25 - reduction,
        reduction,
        reduction_low:
          delta(location.pm25, background, weights, action.cuts, 0.6) * 0.8,
        reduction_high: Math.min(
          Math.max(location.pm25 - background, 0),
          delta(location.pm25, background, weights, action.cuts, 0.8) * 1.2,
        ),
        reduction_percent: location.pm25
          ? (reduction / location.pm25) * 100
          : 0,
        exposure_benefit: grid.reduce(
          (sum, cell, i) => sum + (cell.pm25 - next[i].pm25) * cell.population,
          0,
        ),
        cells: next,
        source_type: "modeled",
        population_source_type: "synthetic",
        assumptions: DEMO_ASSUMPTIONS,
      };
    })
    .sort((a, b) => b.exposure_benefit - a.exposure_benefit);
  results.forEach((result, i) => {
    result.rank = i + 1;
  });
  return {
    scenario_id: `demo-${location.id}-${cuts.traffic}-${cuts.industry}-${cuts.dust}`,
    location_id: location.id,
    results,
    source_type: "modeled",
    assumptions: DEMO_ASSUMPTIONS,
  };
}

export function attribution(location: Station): AttributionResponse {
  const weights = localWeights(location.latitude, location.longitude);
  const excess = Math.max(location.pm25 - background, 0);
  return {
    location_id: location.id,
    background: Math.min(background, location.pm25),
    source_type: "modeled",
    assumptions: DEMO_ASSUMPTIONS,
    shares: [
      {
        name: "Traffic",
        value: (weights.traffic * excess) / location.pm25,
        color: "#0b4f6c",
      },
      {
        name: "Industry",
        value: (weights.industry * excess) / location.pm25,
        color: "#b45309",
      },
      {
        name: "Construction / road dust",
        value: (weights.dust * excess) / location.pm25,
        color: "#6b7280",
      },
      {
        name: "Regional background",
        value: Math.min(background, location.pm25) / location.pm25,
        color: "#9bbdb0",
      },
    ],
  };
}

function time(offset: number) {
  return new Date(Date.parse(DEMO_TIME) + offset * 3600000).toISOString();
}
function syntheticHistory(location: Station, offset: number) {
  return Math.max(
    5,
    location.pm25 +
      13 * Math.sin((offset * Math.PI) / 12) +
      7 * Math.cos(offset / 9) -
      7,
  );
}
export function forecast(location: Station, hours = 24): ForecastResponse {
  const series: SeriesPoint[] = Array.from(
    { length: 49 + hours },
    (_, index) => {
      const offset = index - 48;
      const predicted =
        offset >= 0
          ? Math.max(5, location.pm25 + 10 * Math.sin((offset * Math.PI) / 12))
          : null;
      return {
        timestamp: time(offset),
        actual: offset <= 0 ? syntheticHistory(location, offset) : null,
        predicted,
        persistence: null,
        p10: predicted === null ? null : predicted - 14,
        p90: predicted === null ? null : predicted + 14,
      };
    },
  );
  return {
    location_id: location.id,
    series,
    history_source_type: "synthetic",
    source_type: "modeled",
    assumptions: [
      "Illustrative browser-only projection of synthetic data; this fallback does not call the backend model.",
      "The ±14 µg/m³ band is illustrative, not a calibrated p10–p90 interval.",
    ],
  };
}

export function metricsFor(series: SeriesPoint[]): Metrics {
  const pairs = series.filter(
    (p) => p.actual !== null && p.predicted !== null && p.persistence !== null,
  );
  const mean = pairs.reduce((sum, p) => sum + p.actual!, 0) / pairs.length;
  const mae =
    pairs.reduce((sum, p) => sum + Math.abs(p.predicted! - p.actual!), 0) /
    pairs.length;
  const squared = pairs.reduce(
    (sum, p) => sum + (p.predicted! - p.actual!) ** 2,
    0,
  );
  const variance = pairs.reduce((sum, p) => sum + (p.actual! - mean) ** 2, 0);
  const baseline =
    pairs.reduce((sum, p) => sum + Math.abs(p.persistence! - p.actual!), 0) /
    pairs.length;
  return {
    mae,
    rmse: Math.sqrt(squared / pairs.length),
    r2: variance ? 1 - squared / variance : 0,
    persistence_mae: baseline,
    improvement_percent: baseline ? (1 - mae / baseline) * 100 : 0,
    interval_coverage:
      (pairs.filter((p) => p.actual! >= p.p10! && p.actual! <= p.p90!).length /
        pairs.length) *
      100,
  };
}
export function backtest(location: Station): BacktestResponse {
  // Prediction and interval use only the reading 24 hours before each target.
  const series: SeriesPoint[] = Array.from({ length: 168 }, (_, i) => {
    const offset = i - 168,
      actual = syntheticHistory(location, offset),
      persistence = syntheticHistory(location, offset - 24);
    const predicted = persistence;
    return {
      timestamp: time(offset),
      actual,
      persistence,
      predicted,
      p10: predicted - 14,
      p90: predicted + 14,
    };
  });
  return {
    location_id: location.id,
    series,
    metrics: metricsFor(series),
    method: "24-hour persistence placeholder",
    source_type: "modeled",
    target_source_type: "synthetic",
    assumptions: [
      "Metrics are computed from the displayed synthetic series, not real station observations.",
      "The browser demo predictor equals persistence. Backend mode uses the chronological scikit-learn backtest.",
      "This is a seven-day chronological demonstration, not the required winter holdout.",
    ],
  };
}
