import { useEffect, useState } from "react";
import {
  CircleMarker,
  MapContainer,
  Polygon,
  Polyline,
  Rectangle,
  TileLayer,
  Tooltip,
  useMap,
} from "react-leaflet";
import { Check, Layers, Wind } from "lucide-react";
import type { Cell, Station } from "../types";
import { colorFor } from "../mocks/engine";
import { number } from "../lib/format";
import { DataBadge } from "./DataBadge";
import type { LeafletEvent } from "leaflet";

function accessibleMapTarget(event: LeafletEvent, label: string) {
  const element = event.target.getElement();
  if (!element) return;
  element.setAttribute("role", "button");
  element.setAttribute("aria-label", label);
  element.setAttribute("tabindex", "0");
  element.onkeydown = (key: KeyboardEvent) => {
    if (key.key === "Enter" || key.key === " ") {
      key.preventDefault();
      event.target.fire("click");
    }
  };
}

const BANDS = [
  ["Good 0–30", "#22c55e"],
  ["Satisfactory 30–60", "#a3e635"],
  ["Moderate 60–90", "#facc15"],
  ["Poor 90–120", "#f97316"],
  ["Very poor 120–250", "#ef4444"],
  ["Severe >250", "#7f1d1d"],
];

function MapRuntime() {
  const map = useMap();
  useEffect(() => {
    const observer = new ResizeObserver(() => {
      map.invalidateSize();
      map.setZoom(map.getContainer().clientHeight < 700 ? 10 : 11);
    });
    observer.observe(map.getContainer());
    // This SVG pattern encodes modeled grid provenance; geography is rendered by Leaflet.
    const injectHatch = () => {
      const svg = map.getContainer().querySelector(".leaflet-overlay-pane svg");
      if (!svg || svg.querySelector("#model-hatch")) return;
      const ns = "http://www.w3.org/2000/svg";
      const defs = document.createElementNS(ns, "defs");
      const pattern = document.createElementNS(ns, "pattern");
      pattern.id = "model-hatch";
      for (const [key, value] of Object.entries({
        width: "10",
        height: "10",
        patternUnits: "userSpaceOnUse",
        patternTransform: "rotate(45)",
      }))
        pattern.setAttribute(key, value);
      const line = document.createElementNS(ns, "line");
      line.setAttribute("y2", "10");
      line.setAttribute("stroke", "rgba(255,255,255,.7)");
      line.setAttribute("stroke-width", "1.3");
      pattern.append(line);
      defs.append(pattern);
      svg.prepend(defs);
    };
    injectHatch();
    map.on("layeradd", injectHatch);
    return () => {
      observer.disconnect();
      map.off("layeradd", injectHatch);
    };
  }, [map]);
  return null;
}

interface Props {
  stations: Station[];
  cells: Cell[];
  selected: Station;
  onSelect: (location: Station) => void;
  after: boolean;
  onAfter: () => void;
  dark: boolean;
  demo: boolean;
}
export function MapView({
  stations,
  cells,
  selected,
  onSelect,
  after,
  onAfter,
  dark,
  demo,
}: Props) {
  const [layers, setLayers] = useState({
    Hotspots: true,
    Stations: true,
    Zones: true,
  });
  const [hover, setHover] = useState<string | null>(null);
  const [tileError, setTileError] = useState(false);
  const baseline = cells.find((cell) => cell.id === selected.id);
  return (
    <section
      className={`map-shell ${dark ? "dark-map" : ""}`}
      aria-label="Pune and PCMC pollution map"
    >
      <MapContainer
        center={[18.6, 73.82]}
        zoom={11}
        zoomControl={false}
        scrollWheelZoom
        minZoom={9}
        maxZoom={15}
        className="map"
        attributionControl
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          eventHandlers={{
            tileerror: () => setTileError(true),
            tileload: () => setTileError(false),
          }}
        />
        {layers.Hotspots &&
          cells.map((cell) => (
            <Rectangle
              key={cell.id}
              bounds={cell.bounds}
              pathOptions={{
                color: "#ffffff",
                weight: 0.6,
                fillColor: colorFor(cell.pm25),
                fillOpacity: 0.44,
              }}
              eventHandlers={{
                add: (event) =>
                  accessibleMapTarget(event, `Select grid ${cell.id}`),
                mouseover: () => setHover(cell.id),
                mouseout: () => setHover(null),
                click: () =>
                  onSelect({
                    id: cell.id,
                    name: `Grid cell ${cell.id.replace("cell-", "")}`,
                    short_name: "Selected grid cell",
                    latitude: cell.latitude,
                    longitude: cell.longitude,
                    pm25: cell.pm25,
                    timestamp: stations[0].timestamp,
                    source_type: "modeled",
                    assumptions: cell.assumptions,
                  }),
              }}
            >
              {hover === cell.id && (
                <Tooltip sticky>
                  <strong>{number(cell.pm25)} µg/m³</strong>
                  <br />
                  <DataBadge
                    source="modeled"
                    detail={after ? "SCENARIO" : "INTERPOLATED"}
                  />
                  {demo && (
                    <div className="tooltip-note">Synthetic demo inputs</div>
                  )}
                </Tooltip>
              )}
            </Rectangle>
          ))}
        {layers.Hotspots &&
          cells.map((cell) => (
            <Rectangle
              key={`hatch-${cell.id}`}
              bounds={cell.bounds}
              interactive={false}
              pathOptions={{
                stroke: false,
                fillOpacity: 0.7,
                className: "grid-hatch",
              }}
            />
          ))}
        {layers.Zones && (
          <>
            <Polygon
              positions={[
                [18.606, 73.831],
                [18.646, 73.833],
                [18.652, 73.873],
                [18.611, 73.881],
              ]}
              pathOptions={{
                fill: false,
                color: "#8b5cf6",
                weight: 2,
                dashArray: "9 7",
              }}
            />
            <Polygon
              positions={[
                [18.735, 73.823],
                [18.786, 73.825],
                [18.792, 73.894],
                [18.744, 73.905],
              ]}
              pathOptions={{
                fill: false,
                color: "#8b5cf6",
                weight: 2,
                dashArray: "9 7",
              }}
            />
            <Polyline
              positions={[
                [18.77, 73.73],
                [18.69, 73.75],
                [18.61, 73.77],
                [18.53, 73.79],
                [18.46, 73.82],
              ]}
              pathOptions={{ color: "#3b82f6", weight: 4, opacity: 0.65 }}
            />
          </>
        )}
        {layers.Stations &&
          stations.map((station) => (
            <CircleMarker
              key={station.id}
              center={[station.latitude, station.longitude]}
              radius={station.id === selected.id ? 8 : 6}
              pathOptions={{
                color:
                  station.source_type === "observed" ? "#15803d" : "#4b5563",
                weight: 3,
                fillColor: colorFor(station.pm25),
                fillOpacity: 1,
              }}
              eventHandlers={{
                add: (event) =>
                  accessibleMapTarget(event, `Select location ${station.name}`),
                click: () => onSelect(station),
                mouseover: () => setHover(station.id),
                mouseout: () => setHover(null),
              }}
            >
              {(hover === station.id ||
                (!hover && station.id === selected.id)) && (
                <Tooltip
                  permanent
                  direction="right"
                  offset={[10, 0]}
                  className="station-tooltip"
                >
                  <strong>
                    {station.short_name} · {number(station.pm25, 0)} µg/m³
                  </strong>
                  <br />
                  <DataBadge
                    source={station.source_type}
                    detail={demo ? "DEMO LOCATION" : "STATION"}
                  />
                </Tooltip>
              )}
            </CircleMarker>
          ))}
        {baseline && (
          <CircleMarker
            center={[selected.latitude, selected.longitude]}
            radius={6}
            pathOptions={{ color: "#0b4f6c", fillOpacity: 0, weight: 3 }}
          />
        )}
        <MapRuntime />
      </MapContainer>
      <div className="map-banner">
        <DataBadge
          source="modeled"
          detail={after ? "SCENARIO" : "INTERPOLATED"}
        />
        <span>
          {after
            ? "Projected after intervention"
            : "Baseline concentration grid"}
          {demo && " · synthetic inputs"}
        </span>
      </div>
      <div className="map-controls" aria-label="Map layers">
        {(Object.keys(layers) as (keyof typeof layers)[]).map(
          (layer, index) => (
            <button
              key={layer}
              aria-pressed={layers[layer]}
              className={layers[layer] && index === 0 ? "selected-layer" : ""}
              onClick={() => {
                setLayers({ ...layers, [layer]: !layers[layer] });
                setHover(null);
              }}
            >
              {layer}
              {layers[layer] && <Check size={11} />}
            </button>
          ),
        )}
        <button className="after-toggle" aria-pressed={after} onClick={onAfter}>
          {after ? "AFTER VIEW · ON" : "BEFORE VIEW"}
        </button>
      </div>
      <div className="map-context">
        <Layers size={14} />
        <span>
          12 × 12 grid
          <br />
          <small>
            {layers.Zones ? "Illustrative zones shown" : "Zones hidden"}
          </small>
        </span>
      </div>
      {tileError && (
        <div className="tile-warning" role="status">
          Basemap unavailable. Demo grid remains interactive.
        </div>
      )}
      {demo && (
        <div className="wind-card">
          <Wind size={14} />
          <div>
            <span>WIND · SYNTHETIC</span>
            <strong>NW · 11 km/h</strong>
          </div>
        </div>
      )}
      <div className="map-legend">
        <div className="eyebrow">PM2.5 CONCENTRATION BANDS · µg/m³</div>
        <div className="band-grid">
          {BANDS.map(([label, color]) => (
            <span key={label}>
              <i style={{ background: color }} />
              {label}
            </span>
          ))}
        </div>
        <div className="legend-provenance">
          <DataBadge source="observed" detail="SOLID" />
          <DataBadge source="modeled" detail="HATCH" />
          <DataBadge source="synthetic" />
        </div>
        <p>Station markers stay at baseline in after view.</p>
      </div>
    </section>
  );
}
