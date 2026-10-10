import type { Cell, DashboardData, Station } from "../types";

/** Named navigation anchors. Never treated as monitoring stations. */
const PLACES: ReadonlyArray<{name: string; lat: number; lon: number}> = [
  { name: "Baner", lat: 18.559, lon: 73.779 },
  { name: "Chinchwad", lat: 18.627, lon: 73.784 },
  { name: "Akurdi", lat: 18.650, lon: 73.773 },
  { name: "Aundh", lat: 18.560, lon: 73.808 },
  { name: "Pimpri", lat: 18.628, lon: 73.803 },
  { name: "Kothrud", lat: 18.508, lon: 73.808 },
  { name: "Shivajinagar", lat: 18.531, lon: 73.848 },
  { name: "Hadapsar", lat: 18.507, lon: 73.926 },
  { name: "Hinjawadi", lat: 18.593, lon: 73.738 },
  { name: "Kharadi", lat: 18.551, lon: 73.940 },
  { name: "Bhosari", lat: 18.630, lon: 73.851 },
  { name: "Wakad", lat: 18.602, lon: 73.770 },
  { name: "Nigdi", lat: 18.656, lon: 73.770 },
  { name: "Chakan", lat: 18.758, lon: 73.861 },
  { name: "Pune", lat: 18.520, lon: 73.856 },
];
const squaredKm = (latA: number, lonA: number, latB: number, lonB: number) =>
  (latA - latB) ** 2 + (lonA - lonB) ** 2 * Math.cos(latA * Math.PI / 180) ** 2;
export function nearestGridCell(cells: Cell[], latitude: number, longitude: number): Cell | null {
  let best: Cell | null = null, distance = Number.POSITIVE_INFINITY;
  for (const cell of cells) {
    if (!Number.isFinite(cell.pm25)) continue;
    const next = squaredKm(latitude, longitude, cell.latitude, cell.longitude);
    if (next < distance) { best = cell; distance = next; }
  }
  return best;
}
/** All values and forecast IDs come from backend cells. Names are only search aliases. */
export function localityMatches(data: DashboardData, query: string): Station[] {
  const term = query.toLowerCase().trim();
  if (!term) return [];
  const names = data.stations.map((station) => station.short_name.toLowerCase());
  return PLACES.filter((place) => place.name.toLowerCase().includes(term) && !names.some((name) => name === place.name.toLowerCase()))
    .slice(0, 5)
    .flatMap((place) => {
      const cell = nearestGridCell(data.cells, place.lat, place.lon);
      if (!cell) return [];
      return [{
        id: cell.id,
        name: place.name + " vicinity · interpolated grid",
        short_name: place.name,
        latitude: cell.latitude, longitude: cell.longitude,
        pm25: cell.pm25, timestamp: data.stations[0]?.timestamp ?? "",
        source_type: data.demo ? "synthetic" : "modeled",
        assumptions: [...cell.assumptions, "Locality search uses the closest existing model grid cell. It is not a monitor at the named location."],
      } satisfies Station];
    });
}
