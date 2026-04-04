"use client";
import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

interface Grid {
  id: string;
  city: string;
  center_lat: number;
  center_lng: number;
  map_color: string;
  state_label: string;
  risk_percent: number;
  insured_worker_count: number;
  feature_snapshot?: {
    flood_risk?: number;
    aqi?: number;
    heat_index?: number;
    rain_6h?: number;
    weather_description?: string;
  };
  active_disruption_count: number;
}

interface Props {
  grids: Grid[];
  selectedGridId?: string | null;
  onSelectGrid?: (gridId: string) => void;
}

const GRID_DEG = 0.009;

export default function DisruptionMap({ grids, selectedGridId, onSelectGrid }: Props) {
  const mapRef = useRef<HTMLDivElement>(null);
  const leafletMap = useRef<L.Map | null>(null);

  useEffect(() => {
    if (!mapRef.current || leafletMap.current) return;

    const map = L.map(mapRef.current, {
      center: [12.935, 77.605],
      zoom: 13,
      zoomControl: true,
    });

    // Dark tile layer (CartoDB Dark Matter - free)
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

    // Clear existing layers (except tile)
    map.eachLayer((layer) => {
      if (!(layer instanceof L.TileLayer)) {
        map.removeLayer(layer);
      }
    });

    // Draw microgrid polygons
    grids.forEach((grid) => {
      const lat = grid.center_lat - GRID_DEG / 2;
      const lng = grid.center_lng - GRID_DEG / 2;

      const bounds: L.LatLngBoundsExpression = [
        [lat, lng],
        [lat + GRID_DEG, lng + GRID_DEG],
      ];

      const isDisrupted = grid.active_disruption_count > 0;
      const isSelected = selectedGridId === grid.id;
      const color = grid.map_color || "#10B981";
      const feature = grid.feature_snapshot || {};
      const rain6h = Number(feature.rain_6h || 0).toFixed(1);

      const rect = L.rectangle(bounds, {
        color: color,
        weight: isSelected ? 2.5 : 1,
        opacity: isSelected ? 0.95 : 0.7,
        fillOpacity: isDisrupted ? 0.42 : isSelected ? 0.28 : 0.18,
        fillColor: color,
      }).addTo(map);

      rect.bindPopup(`
        <div style="font-family: Inter, sans-serif; font-size: 12px; line-height: 1.5;">
          <strong>${grid.city} · ${grid.id}</strong><br/>
          State: ${grid.state_label}<br/>
          Live Risk: ${grid.risk_percent}%<br/>
          Rain 6h: ${rain6h} mm<br/>
          AQI: ${feature.aqi ?? "n/a"}<br/>
          Heat Index: ${feature.heat_index ?? "n/a"}°C<br/>
          Insured Workers: ${grid.insured_worker_count}<br/>
          ${isDisrupted ? '<span style="color: #EF4444; font-weight: bold;">⚡ ACTIVE DISRUPTION</span>' : ""}
        </div>
      `);
      rect.on("click", () => onSelectGrid?.(grid.id));

      // Pulsing effect for disrupted grids
      if (isDisrupted) {
        const pulseRect = L.rectangle(bounds, {
          color: "#EF4444",
          weight: 2,
          opacity: 0.8,
          fillOpacity: 0,
          className: "pulse-overlay",
        }).addTo(map);
        pulseRect.on("click", () => onSelectGrid?.(grid.id));

        // Simple pulsing via interval
        let visible = true;
        const pulseInterval = setInterval(() => {
          visible = !visible;
          pulseRect.setStyle({ opacity: visible ? 0.8 : 0.2 });
        }, 1000);

        // Store cleanup (simplified)
        (pulseRect as unknown as Record<string, unknown>)._pulseInterval = pulseInterval;
      }
    });

    if (grids.length > 0) {
      const selected = grids.find((grid) => grid.id === selectedGridId) || grids[0];
      map.setView([selected.center_lat, selected.center_lng], selectedGridId ? 13 : 11);
    }
  }, [grids, selectedGridId, onSelectGrid]);

  return <div ref={mapRef} className="w-full h-full" />;
}
