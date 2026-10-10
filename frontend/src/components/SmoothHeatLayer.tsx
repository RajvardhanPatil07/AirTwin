/** Visual-only bilinear rendering of the existing modeled grid.
 * Never creates additional measurements; displayed resolution remains that of input cells.
 */
import { useEffect, useState } from "react";
import { ImageOverlay } from "react-leaflet";
import type { Cell } from "../types";

const STOPS: ReadonlyArray<[number, [number, number, number]]> = [
  [0, [32, 136, 198]],
  [20, [41, 183, 214]],
  [40, [44, 200, 160]],
  [58, [169, 216, 110]],
  [72, [246, 219, 105]],
  [94, [247, 142, 81]],
  [120, [214, 51, 85]],
  [160, [125, 26, 72]],
];
function colorAt(value: number): [number, number, number] {
  for (let i = 1; i < STOPS.length; i++) {
    const [high, upper] = STOPS[i], [low, lower] = STOPS[i - 1];
    if (value <= high) {
      const t = Math.max(0, Math.min(1, (value - low) / (high - low)));
      return [0, 1, 2].map((c) => Math.round(lower[c] * (1 - t) + upper[c] * t)) as [number, number, number];
    }
  }
  return [...STOPS[STOPS.length - 1][1]];
}
const clamp = (x: number, a: number, b: number) => Math.max(a, Math.min(b, x));
const smooth = (x: number) => { const t = clamp(x, 0, 1); return t * t * (3 - 2 * t); };
function sampleGrid(
  lat: number, lon: number, lats: number[], lons: number[],
  values: Map<string, number>,
): number | null {
  if (!lats.length || !lons.length) return null;
  const between = (arr: number[], x: number) => {
    if (arr.length === 1) return [0, 0] as const;
    const high = arr.findIndex((v) => v >= x);
    if (high < 0) return [arr.length - 1, arr.length - 1] as const;
    return [Math.max(0, high - 1), high] as const;
  };
  const [yi, yj] = between(lats, lat), [xi, xj] = between(lons, lon);
  const dy = yi === yj ? 0 : (lat - lats[yi]) / (lats[yj] - lats[yi]);
  const dx = xi === xj ? 0 : (lon - lons[xi]) / (lons[xj] - lons[xi]);
  let weighted = 0, sum = 0;
  for (const [i, rowWeight] of [[yi, 1 - dy], [yj, dy]]) {
    for (const [j, colWeight] of [[xi, 1 - dx], [xj, dx]]) {
      const value = values.get(i + ":" + j);
      const weight = rowWeight * colWeight;
      if (value !== undefined && weight > 0) { weighted += value * weight; sum += weight; }
    }
  }
  return sum ? weighted / sum : null;
}
export function SmoothHeatLayer({ cells, opacity = 0.86 }: { cells: Cell[]; opacity?: number }) {
  const [image, setImage] = useState<{url: string; bounds: [[number, number], [number, number]]} | null>(null);
  useEffect(() => {
    if (!cells.length) { setImage(null); return; }
    const valid = cells.filter((cell) => Number.isFinite(cell.pm25) && cell.bounds && cell.source_type !== "observed");
    if (!valid.length) { setImage(null); return; }
    const west = Math.min(...valid.map((cell) => cell.bounds[0][1]));
    const east = Math.max(...valid.map((cell) => cell.bounds[1][1]));
    const south = Math.min(...valid.map((cell) => cell.bounds[0][0]));
    const north = Math.max(...valid.map((cell) => cell.bounds[1][0]));
    const lats = [...new Set(valid.map((cell) => Number(cell.latitude.toFixed(6))))].sort((a, b) => a - b);
    const lons = [...new Set(valid.map((cell) => Number(cell.longitude.toFixed(6))))].sort((a, b) => a - b);
    const lookup = new Map<string, number>();
    for (const cell of valid) {
      const i = lats.indexOf(Number(cell.latitude.toFixed(6)));
      const j = lons.indexOf(Number(cell.longitude.toFixed(6)));
      lookup.set(i + ":" + j, cell.pm25);
    }
    const size = 384;
    const canvas = document.createElement("canvas");
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext("2d", { willReadFrequently: false });
    if (!ctx) return;
    const bitmap = ctx.createImageData(size, size);
    for (let y = 0; y < size; y++) {
      const v = (y + .5) / size;
      const lat = north - v * (north - south);
      for (let x = 0; x < size; x++) {
        const u = (x + .5) / size;
        const lon = west + u * (east - west);
        const value = sampleGrid(lat, lon, lats, lons, lookup);
        if (value === null) continue;
        const i = (y * size + x) * 4;
        const [red, green, blue] = colorAt(value);
        bitmap.data[i] = red;
        bitmap.data[i + 1] = green;
        bitmap.data[i + 2] = blue;
        const edge = smooth(Math.min(u, 1 - u, v, 1 - v) / .14);
        const intensity = clamp(0.52 + (value / 160) * 0.22, .48, .78);
        bitmap.data[i + 3] = Math.round(255 * intensity * edge);
      }
    }
    ctx.putImageData(bitmap, 0, 0);
    const url = canvas.toDataURL("image/png");
    setImage({url, bounds: [[south, west], [north, east]]});
    return () => {setImage(null);};
  }, [cells]);
  return image ? <ImageOverlay url={image.url} bounds={image.bounds} opacity={opacity} interactive={false} crossOrigin={false}/> : null;
}
