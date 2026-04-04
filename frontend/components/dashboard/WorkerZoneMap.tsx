"use client";
import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

interface LiveGrid {
  id: string;
  center_lat: number;
  center_lng: number;
  map_color: string;
  state_label: string;
  active_disruption_count: number;
}

interface WorkerZoneMapProps {
  grids: LiveGrid[];
  workerGridId?: string | null;
}

const GRID_DEG = 0.009;

export default function WorkerZoneMap({ grids, workerGridId }: WorkerZoneMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const leafletMap = useRef<L.Map | null>(null);

  useEffect(() => {
    if (!mapRef.current || leafletMap.current) return;

    const map = L.map(mapRef.current, {
      center: [12.9716, 77.5946],
      zoom: 12,
      zoomControl: false,
      attributionControl: false,
    });

    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
      attribution: '&copy; <a href="https://carto.com/">CARTO</a>',
      maxZoom: 19,
    }).addTo(map);

    leafletMap.current = map;

    return () => {
      map.remove();
      leafletMap.current = null;
    };
  }, []);

  useEffect(() => {
    const map = leafletMap.current;
    if (!map) return;

    map.eachLayer((layer) => {
      if (!(layer instanceof L.TileLayer)) {
        map.removeLayer(layer);
      }
    });

    grids.forEach((grid) => {
      const lat = grid.center_lat - GRID_DEG / 2;
      const lng = grid.center_lng - GRID_DEG / 2;
      const isWorkerGrid = grid.id === workerGridId;
      const rect = L.rectangle(
        [
          [lat, lng],
          [lat + GRID_DEG, lng + GRID_DEG],
        ],
        {
          color: grid.map_color,
          weight: isWorkerGrid ? 2.5 : 1,
          opacity: isWorkerGrid ? 0.95 : 0.65,
          fillColor: grid.map_color,
          fillOpacity: isWorkerGrid ? 0.4 : 0.12,
        },
      ).addTo(map);

      rect.bindPopup(
        `<strong>${grid.id}</strong><br/>${grid.state_label}<br/>${
          grid.active_disruption_count > 0 ? "Active disruption in zone" : "No active disruption"
        }`,
      );
    });

    const focus = grids.find((grid) => grid.id === workerGridId) || grids[0];
    if (focus) {
      map.setView([focus.center_lat, focus.center_lng], 13);
    }
  }, [grids, workerGridId]);

  return <div ref={mapRef} className="h-56 w-full rounded-2xl overflow-hidden" />;
}
