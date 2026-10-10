import { useEffect, useMemo, useRef, useState } from "react";
import type { LeafletEvent } from "leaflet";
import { CircleMarker, GeoJSON, MapContainer, Rectangle, ScaleControl, TileLayer, Tooltip, useMap, ZoomControl } from "react-leaflet";
import { Layers3, LocateFixed, MapPin, Search, X } from "lucide-react";
import type { GeoJsonObject } from "geojson";
import type { Cell, DashboardData, Station } from "../types";
import { concentrationColor, METRICS, readingFor, type MetricId } from "../lib/finalMetrics";
import { localityMatches } from "../lib/finalPlaces";
import { SmoothHeatLayer } from "./SmoothHeatLayer";
import { number, timeLabel, dateLabel } from "../lib/format";

function accessibleTarget(event: LeafletEvent, label: string, retries = 1) {
  const layer = event.target as { getElement?: () => SVGElement | undefined; fire: (name: string) => void };
  const element = layer.getElement?.();
  if (!element) {
    if (retries > 0) requestAnimationFrame(() => accessibleTarget(event, label, retries - 1));
    return;
  }
  element.setAttribute("role", "button");
  element.setAttribute("tabindex", "0");
  element.setAttribute("aria-label", label);
  element.addEventListener("keydown", (key: KeyboardEvent) => {
    if (key.key === "Enter" || key.key === " ") {
      key.preventDefault();
      layer.fire("click");
    }
  });
}

function FollowSelected({ selected, focus }: { selected: Station | null; focus: boolean }) {
  const map = useMap();
  const previousFocus = useRef(focus);
  useEffect(() => {
    if (focus && selected) map.flyTo([selected.latitude, selected.longitude], 12, { duration: 0.65 });
    else if (previousFocus.current && !focus) map.flyTo([18.60, 73.835], 11, { duration: 0.65 });
    previousFocus.current = focus;
  }, [focus, selected?.id, map]);
  return null;
}

function RecenterControl() {
  const map = useMap();
  return <button className="fm-recenter" type="button" aria-label="Reset map to Pune and PCMC" onClick={() => map.flyTo([18.60, 73.835], 11)}><LocateFixed size={17}/></button>;
}

export function FinalMap({
  data, selected, onSelect, metric, night = false, focus = false, atmosphere = "off",
  onClearFocus, forecast = false, forecastCells = null, spatialTimestamp = null,
}: {
  data: DashboardData;
  selected: Station | null;
  onSelect: (station: Station) => void;
  metric: MetricId;
  night?: boolean;
  focus?: boolean;
  atmosphere?: "off" | "clear" | "hazy" | "cloudy";
  onClearFocus?: () => void;
  forecast?: boolean;
  forecastCells?: Cell[] | null;
  spatialTimestamp?: string | null;
}) {
  const [layers, setLayers] = useState({ modeled: true, observed: true, boundaries: false });
  const [search, setSearch] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [tileError, setTileError] = useState(false);
  const metricInfo = METRICS.find((item) => item.id === metric)!;
  const showGrid = layers.modeled && metric === "pm25";
  const displayedCells = forecastCells ?? data.cells;
  const markers = useMemo(() =>
    data.stations.filter((station) => readingFor(station, metric, data.demo) && (layers.observed || station.source_type !== "observed")),
    [data.stations, metric, data.demo, layers.observed]);
  const featuredIds = useMemo(() => new Set(
    [...markers].sort((a, b) => (readingFor(b, metric, data.demo)?.value ?? -1) - (readingFor(a, metric, data.demo)?.value ?? -1))
      .slice(0, 3).map((station) => station.id)), [markers, metric, data.demo]);
  const matches = useMemo(() => [
    ...data.stations.filter((station) =>
      station.name.toLowerCase().includes(search.trim().toLowerCase())).slice(0, 6),
    ...localityMatches(data, search),
  ].slice(0, 9), [search, data]);
  // Public OpenStreetMap tiles do not require an API key. Respect tile-policy
  // attribution and avoid restricted CARTO/Apple imagery.
  const tile = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
  return <section className={"fm-shell" + (night ? " fm-night" : "") + (focus ? " fm-focus" : "")} aria-label="Interactive Pune and PCMC air-quality map">
    <MapContainer center={[18.60, 73.835]} zoom={11} minZoom={9} maxZoom={16} zoomControl={false} scrollWheelZoom className="fm-leaflet">
      <TileLayer key={tile} url={tile}
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>'
        eventHandlers={{ tileerror: () => setTileError(true), tileload: () => setTileError(false) }}/>
      <ZoomControl position="bottomleft"/>
      <ScaleControl position="bottomleft" imperial={false}/>
      <FollowSelected selected={selected} focus={focus}/>
      <RecenterControl/>
      {showGrid && <SmoothHeatLayer cells={displayedCells} opacity={selected && focus ? 0.66 : 1}/>} 
      {showGrid && data.cells.map((cell) => <Rectangle key={cell.id} bounds={cell.bounds}
        pathOptions={{
          color: selected?.id === cell.id ? "#194e85" : "transparent",
          weight: selected?.id === cell.id ? 2.7 : 0,
          fillColor: concentrationColor(cell.pm25),
          fillOpacity: selected?.id === cell.id ? 0.075 : 0.005,
        }}
        eventHandlers={{ add: (event) => accessibleTarget(event, "Select modeled grid cell " + cell.id), click: () => onSelect({
          id: cell.id, name: "Modeled grid · " + cell.id, short_name: "Grid cell",
          latitude: cell.latitude, longitude: cell.longitude, pm25: cell.pm25,
          timestamp: data.stations[0]?.timestamp ?? "", source_type: data.demo ? "synthetic" : "modeled",
          assumptions: cell.assumptions,
        }) }}>
        <Tooltip sticky><strong>{number(displayedCells.find((c) => c.id === cell.id)?.pm25 ?? cell.pm25)} µg/m³</strong><br/>{data.demo ? "SYNTHETIC" : "MODELED"} · {spatialTimestamp ? "SPATIAL FORECAST" : "IDW BASELINE"}<br/>Not a street-level measurement</Tooltip>
      </Rectangle>)}
      {layers.boundaries && data.zones && <GeoJSON key="zones" data={data.zones as unknown as GeoJsonObject}
        style={{ color: "#1f77b4", weight: 2, fillOpacity: 0.025, dashArray: "5 4" }}/>}
      {markers.map((station) => {
        const reading = readingFor(station, metric, data.demo)!;
        const active = selected?.id === station.id;
        return <CircleMarker key={station.id} center={[station.latitude, station.longitude]}
          radius={active ? 10 : station.source_type === "observed" ? 6 : 4.5}
          pathOptions={{
            color: active ? "#fff" : station.source_type === "observed" ? "#0e5a86" : "#fff",
            weight: active ? 3 : 1.5,
            fillColor: concentrationColor(reading.value),
            fillOpacity: focus && !active ? 0.35 : 0.97,
            dashArray: station.source_type !== "observed" ? "4 3" : undefined,
          }}
          eventHandlers={{ add: (event) => accessibleTarget(event, "Select location " + station.name), click: () => onSelect(station) }}>
          <Tooltip direction="top" offset={[0, -8]} permanent={active || featuredIds.has(station.id) || station.id === data.stations[0]?.id}>
            <strong>{station.short_name || station.name}</strong><br/>
            {number(reading.value)} {reading.unit} · {reading.source.toUpperCase()}<br/>
            {dateLabel(reading.timestamp)} {timeLabel(reading.timestamp)} IST
          </Tooltip>
        </CircleMarker>;
      })}
    </MapContainer>
    {night && atmosphere !== "off" && <div className={"fm-atmosphere fm-" + atmosphere} aria-hidden="true"/>}
    <div className="fm-search-wrap">
      <div className="fm-search">
        <Search size={17}/><input value={search} aria-label="Find a mapped location" placeholder="Search Pune & PCMC locations"
          onFocus={() => setSearchOpen(true)} onChange={(event) => {setSearch(event.target.value);setSearchOpen(true);}}
          onKeyDown={(event) => {if (event.key === "Escape") setSearchOpen(false);}}/>
        {search && <button type="button" aria-label="Clear search" onClick={() => {setSearch("");setSearchOpen(false);}}><X size={16}/></button>}
      </div>
      {searchOpen && search.trim() && <div className="fm-search-results">
        {matches.length ? matches.map((station) => <button key={station.id} type="button"
          onClick={() => { onSelect(station); setSearch(station.name); setSearchOpen(false); }}>
          <MapPin size={15}/><span>{station.name}</span><small>{station.source_type.toUpperCase()}</small>
        </button>) : <p>No mapped location matches that name.</p>}
      </div>}
    </div>
    <div className="fm-layerbox">
      <div className="fm-layerhead"><Layers3 size={15}/> Map layers</div>
      <label><input type="checkbox" checked={layers.modeled} disabled={metric !== "pm25"} onChange={(event) => setLayers((v) => ({...v, modeled: event.target.checked}))}/> Modeled PM2.5 grid</label>
      <label><input type="checkbox" checked={layers.observed} onChange={(event) => setLayers((v) => ({...v, observed: event.target.checked}))}/> Observed monitors</label>
      <label><input type="checkbox" checked={layers.boundaries} disabled={!data.zones} onChange={(event) => setLayers((v) => ({...v, boundaries: event.target.checked}))}/> Mapped boundaries</label>
    </div>
    {focus && <button className="fm-back-city" type="button" onClick={onClearFocus}>← Back to city</button>}
    <div className="fm-legend">
      <div className="fm-legend-top"><span className="fm-legend-dot"/><strong>{metricInfo.label}</strong><small>{metric === "pm25" ? "Interpolated · MODELED" : "Reference readings"}</small></div>
      {metric === "pm25" ? <>
        <div className="fm-gradient"/><div className="fm-legend-scale"><span>0</span><span>30</span><span>60</span><span>90</span><span>120+</span></div>
        <div className="fm-legend-foot">µg/m³ · smooth display of a coarse 12×12 modeled grid, not extra measurements or AQI</div>
      </> : <div className="fm-legend-foot">No modeled heat surface for {metricInfo.label}. Only supported reference readings.</div>}
      {forecast && <div className="fm-legend-foot">{spatialTimestamp ? "MODELED spatial forecast · " + spatialTimestamp + " · per-station prediction interpolated via IDW." : "Spatial baseline only; dated forecast grid unavailable."}</div>}
      {data.demo && <div className="fm-demo">SYNTHETIC DEMO · not measured air</div>}
    </div>
    {tileError && <div className="fm-tile-error" role="status">Basemap tiles are temporarily unavailable; geographic data labels remain.</div>}
  </section>;
}
