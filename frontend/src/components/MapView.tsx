import { useEffect, useState } from "react";
import {
  CircleMarker,
  GeoJSON,
  MapContainer,
  Polygon,
  Polyline,
  Rectangle,
  TileLayer,
  Tooltip,
  useMap,
} from "react-leaflet";
import { Check, Wind } from "lucide-react";
import type { GeoJsonObject } from "geojson";
import type {
  Cell,
  RegionInfo,
  Station,
  Weather,
  ZoneCollection,
} from "../types";
import { colorFor } from "../mocks/engine";
import { number } from "../lib/format";
import { DataBadge } from "./DataBadge";
import type { LeafletEvent } from "leaflet";

function accessibleMapTarget(event: LeafletEvent, label: string, retry = true) {
  const element = event.target.getElement();
  if (!element) {
    if (retry)
      requestAnimationFrame(() => accessibleMapTarget(event, label, false));
    return;
  }
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
  ["0–30", "#22c55e"],
  ["30–60", "#a3e635"],
  ["60–90", "#facc15"],
  ["90–120", "#f97316"],
  ["120–250", "#ef4444"],
  [">250", "#7f1d1d"],
];

const LAYER_LABELS = {
  Hotspots: "Grid",
  Stations: "Sensors",
  Zones: "Zones",
} as const;

function MapRuntime({ region }: { region?: RegionInfo }) {
  const map = useMap();

  useEffect(() => {
    const observer = new ResizeObserver(() => {
      map.invalidateSize();
      if (region?.id === "maharashtra")
        map.fitBounds(region.bounds, { padding: [30, 30] });
      else map.setZoom(map.getContainer().clientHeight < 700 ? 10 : 11);
    });

    observer.observe(map.getContainer());

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
      })) {
        pattern.setAttribute(key, value);
      }
      const line = document.createElementNS(ns, "line");
      line.setAttribute("y2", "10");
      line.setAttribute("stroke", "rgba(255,255,255,.6)");
      line.setAttribute("stroke-width", "1.1");
      pattern.append(line);
      defs.append(pattern);
      svg.prepend(defs);
    };

    injectHatch();
    map.on("layeradd", injectHatch);
    if (region) map.fitBounds(region.bounds, { padding: [30, 30] });

    return () => {
      observer.disconnect();
      map.off("layeradd", injectHatch);
    };
  }, [map, region]);

  return null;
}

interface Props {
  region?: RegionInfo;
  stations: Station[];
  cells: Cell[];
  selected: Station;
  onSelect: (location: Station) => void;
  after: boolean;
  onAfter: () => void;
  dark: boolean;
  demo: boolean;
  weather?: Weather;
  zones?: ZoneCollection;
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
  weather,
  zones,
  region,
}: Props) {
  const [layers, setLayers] = useState({
    Hotspots: true,
    Stations: true,
    Zones: true,
  });
  const [hover, setHover] = useState<string | null>(null);
  const [tileError, setTileError] = useState(false);

  const baseline = cells.find((cell) => cell.id === selected.id);
  const tooltipTarget =
    stations.find((station) => station.id === hover) ??
    cells.find((cell) => cell.id === hover) ??
    cells.find((cell) => cell.id === selected.id) ??
    selected;
  const tooltipStation = stations.find(
    (station) => station.id === tooltipTarget.id,
  );

  return (
    <section
      className={"map-shell " + (dark ? "dark-map" : "")}
      aria-label={(region?.name ?? "Pune and PCMC") + " pollution map"}
    >
      <MapContainer
        center={[18.6, 73.82]}
        zoom={11}
        zoomControl={false}
        scrollWheelZoom
        minZoom={5}
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
                weight: 0.45,
                fillColor: colorFor(cell.pm25),
                fillOpacity: 0.4,
              }}
              eventHandlers={{
                add: (event) =>
                  accessibleMapTarget(event, "Select grid " + cell.id),
                mouseover: () => setHover(cell.id),
                mouseout: () => setHover(null),
                click: () =>
                  onSelect({
                    id: cell.id,
                    name: "Grid cell " + cell.id.replace("cell-", ""),
                    short_name: "Selected grid cell",
                    latitude: cell.latitude,
                    longitude: cell.longitude,
                    pm25: cell.pm25,
                    timestamp: stations[0].timestamp,
                    source_type: "modeled",
                    assumptions: cell.assumptions,
                  }),
              }}
            />
          ))}

        {layers.Hotspots &&
          cells.map((cell) => (
            <Rectangle
              key={"hatch-" + cell.id}
              bounds={cell.bounds}
              interactive={false}
              pathOptions={{
                stroke: false,
                fillOpacity: 0.6,
                className: "grid-hatch",
              }}
            />
          ))}

        {layers.Zones && zones && (
          <GeoJSON
            data={zones as unknown as GeoJsonObject}
            style={{
              color: "#8b5cf6",
              weight: 1.5,
              dashArray: "7 6",
              fillOpacity: 0.03,
            }}
          />
        )}

        {layers.Zones && !zones && (
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
                weight: 1.5,
                dashArray: "7 6",
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
                weight: 1.5,
                dashArray: "7 6",
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
              pathOptions={{ color: "#38bdf8", weight: 3, opacity: 0.55 }}
            />
          </>
        )}

        {layers.Stations &&
          stations.map((station) => (
            <CircleMarker
              key={station.id}
              center={[station.latitude, station.longitude]}
              radius={station.id === selected.id ? 8 : 5.5}
              pathOptions={{
                color:
                  station.source_type === "observed" ? "#84d8b8" : "#8a8478",
                weight: station.id === selected.id ? 3 : 2,
                fillColor: colorFor(station.pm25),
                fillOpacity: station.source_type === "observed" ? 1 : 0.55,
                dashArray:
                  station.source_type === "modeled" ? "3 2" : undefined,
              }}
              eventHandlers={{
                add: (event) =>
                  accessibleMapTarget(event, "Select location " + station.name),
                click: () => onSelect(station),
                mouseover: () => setHover(station.id),
                mouseout: () => setHover(null),
              }}
            />
          ))}

        {baseline && (
          <CircleMarker
            center={[selected.latitude, selected.longitude]}
            radius={6}
            pathOptions={{ color: "#5eead4", fillOpacity: 0, weight: 2 }}
          />
        )}

        <CircleMarker
          center={[tooltipTarget.latitude, tooltipTarget.longitude]}
          radius={0}
          interactive={false}
          pathOptions={{ stroke: false, fill: false }}
        >
          <Tooltip
            permanent
            direction="right"
            offset={[10, 0]}
            className="station-tooltip"
          >
            <strong>
              {tooltipStation ? tooltipStation.short_name + " · " : ""}
              {number(tooltipTarget.pm25, tooltipStation ? 0 : 1)} µg/m³
            </strong>
            <br />
            <DataBadge
              source={tooltipStation?.source_type ?? "modeled"}
              detail={
                tooltipStation
                  ? demo
                    ? "DEMO"
                    : tooltipStation.source_type === "modeled"
                      ? "CAMS"
                      : "SENSOR"
                  : after
                    ? "SCENARIO"
                    : "GRID"
              }
            />
          </Tooltip>
        </CircleMarker>

        {region?.boundary && (
          <GeoJSON
            key={region.id}
            data={region.boundary as unknown as GeoJsonObject}
            style={{ color: "#5eead4", weight: 1.5, fill: false }}
          />
        )}

        <MapRuntime region={region} />
      </MapContainer>

      <div className="map-banner">
        <span className="map-dot" />
        {after ? "Scenario" : "Baseline"}
        {demo ? " · demo" : ""}
      </div>

      <div className="map-controls" aria-label="Map layers">
        {(Object.keys(layers) as (keyof typeof layers)[]).map((layer) => (
          <button
            key={layer}
            aria-pressed={layers[layer]}
            className={layers[layer] ? "selected-layer" : ""}
            onClick={() => {
              setLayers({ ...layers, [layer]: !layers[layer] });
              setHover(null);
            }}
          >
            {LAYER_LABELS[layer]}
            {layers[layer] && <Check size={10} />}
          </button>
        ))}
        <button className="after-toggle" aria-pressed={after} onClick={onAfter}>
          {after ? "After" : "Before"}
        </button>
      </div>

      {tileError && (
        <div className="tile-warning" role="status">
          Basemap unavailable
        </div>
      )}

      {(demo || weather?.wind_speed_10m !== undefined) && (
        <div className="wind-card">
          <Wind size={13} />
          <strong>
            {demo
              ? "NW · 11 km/h"
              : number(weather?.wind_direction_10m ?? 0, 0) +
                "° · " +
                number((weather?.wind_speed_10m ?? 0) * 3.6) +
                " km/h"}
          </strong>
        </div>
      )}

      <div className="map-legend" aria-label="PM2.5 concentration bands">
        <span className="legend-title">PM2.5</span>
        <div className="band-grid">
          {BANDS.map(([label, color]) => (
            <span key={label}>
              <i style={{ background: color }} />
              {label}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
