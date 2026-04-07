import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Polyline, useMap, Popup } from "react-leaflet";
import L from "leaflet";
import type { Stop } from "../lib/types";
import { TILE_URLS } from "../lib/constants";
import { getRoadRoute } from "../api/client";
import "leaflet/dist/leaflet.css";

// Fix default marker icons in webpack/vite
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

interface Props {
  stops: Stop[];
  style: string;
  loopRoute?: boolean;
  routeType?: "straight" | "roads";
  tripId?: string;
}

function FitBounds({ stops }: { stops: Stop[] }) {
  const map = useMap();

  useEffect(() => {
    if (stops.length === 0) return;
    const bounds = L.latLngBounds(stops.map((s) => [s.lat, s.lon]));
    map.fitBounds(bounds, { padding: [50, 50] });
  }, [stops, map]);

  return null;
}

function createNumberedIcon(n: number, highlight: boolean) {
  return L.divIcon({
    html: `<div style="
      background:${highlight ? "#2563eb" : "#6b7280"};
      color:white;
      width:28px;height:28px;
      border-radius:50%;
      display:flex;align-items:center;justify-content:center;
      font-size:13px;font-weight:bold;
      border:2px solid white;
      box-shadow:0 1px 4px rgba(0,0,0,0.3);
    ">${n}</div>`,
    className: "",
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}

export function MapPanel({ stops, style, loopRoute, routeType, tripId }: Props) {
  const tileUrl = TILE_URLS[style] ?? TILE_URLS["positron"]!;
  const [roadCoords, setRoadCoords] = useState<[number, number][] | null>(null);

  useEffect(() => {
    if (routeType !== "roads" || !tripId || stops.length < 2) {
      setRoadCoords(null);
      return;
    }
    getRoadRoute(tripId)
      .then((data) => setRoadCoords(data.coordinates as [number, number][]))
      .catch(() => setRoadCoords(null));
  }, [routeType, tripId, stops]);

  return (
    <MapContainer
      center={[40, -4]}
      zoom={5}
      className="h-full w-full"
      zoomControl={true}
    >
      <TileLayer
        url={tileUrl}
        attribution='&copy; OpenStreetMap contributors'
      />
      <FitBounds stops={stops} />
      {stops.map((stop, i) => (
        <Marker
          key={stop.id}
          position={[stop.lat, stop.lon]}
          icon={createNumberedIcon(i + 1, stop.highlight)}
        >
          <Popup>
            <strong>{stop.label || stop.city}</strong>
            <br />
            {stop.dates}
          </Popup>
        </Marker>
      ))}
      {stops.length >= 2 && (() => {
        const pts: [number, number][] = roadCoords
          ? roadCoords
          : (() => {
              const p: [number, number][] = stops.map((s) => [s.lat, s.lon]);
              if (loopRoute) p.push(p[0]!);
              return p;
            })();
        const isRoad = !!roadCoords;
        return (
          <Polyline
            positions={pts}
            color="#3b82f6"
            weight={isRoad ? 2 : 3}
            opacity={0.75}
            smoothFactor={isRoad ? 2 : 1}
          />
        );
      })()}
    </MapContainer>
  );
}
