import { useEffect } from "react";
import { MapPin } from "lucide-react";
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Rectangle,
  Tooltip,
  useMap,
} from "react-leaflet";
import type { Cell as MapCell } from "../types";
type Place = {
  name: string;
  area: string;
  lat: number;
  lng: number;
  value: number;
};

function MapPosition({ place }: { place: Place }) {
  const map = useMap();
  useEffect(() => {
    map.setView([place.lat, place.lng], 12);
  }, [map, place]);
  return null;
}
export function AirMap({
  place,
  heat = false,
  value = place.value,
  compact = false,
  cells,
}: {
  place: Place;
  heat?: boolean;
  value?: number;
  compact?: boolean;
  cells?: MapCell[];
}) {
  return (
    <div className={`at-map ${compact ? "compact" : ""}`}>
      <MapContainer
        center={[place.lat, place.lng]}
        zoom={12}
        scrollWheelZoom={false}
        zoomControl={!compact}
        style={{ height: "100%", width: "100%" }}
      >
        <MapPosition place={place} />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {heat &&
          cells?.map((cell) => (
            <Rectangle
              key={cell.id}
              bounds={cell.bounds}
              pathOptions={{
                color: "#fff",
                weight: 0.6,
                fillColor:
                  cell.pm25 < 30
                    ? "#a1d4a5"
                    : cell.pm25 < 60
                      ? "#f4c474"
                      : "#eb8684",
                fillOpacity: 0.48,
              }}
            >
              <Tooltip>
                {cell.pm25.toFixed(1)} µg/m³ · {cell.source_type}
              </Tooltip>
            </Rectangle>
          ))}
        {heat &&
          !cells &&
          Array.from({ length: 81 }, (_, i) => {
            const row = Math.floor(i / 9),
              col = i % 9,
              lat = place.lat + (row - 4) * 0.009,
              lng = place.lng + (col - 4) * 0.009;
            const colors =
              value < 30
                ? ["#a1d4a5", "#c1dd91", "#e4e7a3"]
                : ["#f4c474", "#f29d80", "#eb8684", "#e5dc85"];
            return (
              <Rectangle
                key={i}
                bounds={[
                  [lat, lng],
                  [lat + 0.009, lng + 0.009],
                ]}
                pathOptions={{
                  color: "#fff",
                  weight: 0.6,
                  fillColor: colors[(row + col * 2) % colors.length],
                  fillOpacity: 0.48,
                }}
              />
            );
          })}
        <CircleMarker
          center={[place.lat, place.lng]}
          radius={8}
          pathOptions={{
            color: "#fff",
            weight: 3,
            fillColor: "#08734b",
            fillOpacity: 1,
          }}
        >
          <Tooltip permanent direction="top" offset={[0, -10]}>
            <b>{place.name}</b>
            <br />
            {heat
              ? `${Number(value.toFixed(1))} µg/m³${cells ? " · modeled estimate" : compact ? "" : " · example estimate"}`
              : place.area}
          </Tooltip>
        </CircleMarker>
      </MapContainer>
      <div className="at-map-caption">
        <MapPin size={13} /> Pune + PCMC{" "}
        {heat && (
          <span>
            {cells
              ? "Backend concentration grid · modeled"
              : "Illustrative concentration grid"}
          </span>
        )}
      </div>
    </div>
  );
}
