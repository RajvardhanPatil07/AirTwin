// India National AQI (CPCB) PM2.5 sub-index breakpoints, 24-hour average basis.
// Applied here to hourly/forecast values as an indicative band, not an official AQI.
const BREAKS: [number, number, number, number][] = [
  [0, 30, 0, 50],
  [31, 60, 51, 100],
  [61, 90, 101, 200],
  [91, 120, 201, 300],
  [121, 250, 301, 400],
  [251, 500, 401, 500],
];

export const CATEGORIES = [
  { name: "Good", color: "#22c55e", advice: "Air quality is fine for everyone. Outdoor activity is safe." },
  { name: "Satisfactory", color: "#a3e635", advice: "Minor breathing discomfort for sensitive people. Normal activity is fine." },
  { name: "Moderate", color: "#facc15", advice: "People with asthma, heart disease, children and older adults should limit long outdoor exertion." },
  { name: "Poor", color: "#f97316", advice: "Sensitive groups should avoid outdoor exercise. Everyone should reduce prolonged exertion." },
  { name: "Very poor", color: "#ef4444", advice: "Avoid outdoor activity. Keep windows closed during peak hours; consider a well-fitted N95 outdoors." },
  { name: "Severe", color: "#7f1d1d", advice: "Health emergency conditions. Stay indoors and follow official advisories." },
] as const;

export function subIndex(pm25: number) {
  const value = Math.max(0, Math.round(pm25));
  const index = BREAKS.findIndex(([, high]) => value <= high);
  const band = index === -1 ? BREAKS.length - 1 : index;
  const [lo, hi, ilo, ihi] = BREAKS[band];
  const clamped = Math.min(value, hi);
  const aqi = Math.round(ilo + ((ihi - ilo) * (clamped - lo)) / Math.max(1, hi - lo));
  return { aqi, band, ...CATEGORIES[band] };
}
