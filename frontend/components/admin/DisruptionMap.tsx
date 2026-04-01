"use client";
import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

interface Grid {
  id: string;
  center_lat: number;
  center_lng: number;
  flood_risk: number;
  composite_risk: number;
}

interface Disruption {
  id: string;
  grid_id: string;
  trigger_type: string;
  severity: number;
}

interface Props {
  grids: Grid[];
  disruptions: Disruption[];
}

const GRID_DEG = 0.009;

function getGridColor(risk: number): string {
  if (risk > 0.6) return "#EF4444";
  if (risk > 0.35) return "#FBBF24";
  return "#10B981";
}

export default function DisruptionMap({ grids, disruptions }: Props) {
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

    const activeGridIds = new Set(disruptions.map((d) => d.grid_id));

    // Draw microgrid polygons
    grids.forEach((grid) => {
      const lat = grid.center_lat - GRID_DEG / 2;
      const lng = grid.center_lng - GRID_DEG / 2;

      const bounds: L.LatLngBoundsExpression = [
        [lat, lng],
        [lat + GRID_DEG, lng + GRID_DEG],
      ];

      const isDisrupted = activeGridIds.has(grid.id);
      const color = isDisrupted ? "#EF4444" : getGridColor(grid.composite_risk);

      const rect = L.rectangle(bounds, {
        color: color,
        weight: 1,
        opacity: 0.6,
        fillOpacity: isDisrupted ? 0.4 : 0.15,
        fillColor: color,
      }).addTo(map);

      rect.bindPopup(`
        <div style="font-family: Inter, sans-serif; font-size: 12px; line-height: 1.5;">
          <strong>${grid.id}</strong><br/>
          Composite Risk: ${(grid.composite_risk * 100).toFixed(0)}%<br/>
          Flood Risk: ${(grid.flood_risk * 100).toFixed(0)}%<br/>
          ${isDisrupted ? '<span style="color: #EF4444; font-weight: bold;">⚡ ACTIVE DISRUPTION</span>' : ''}
        </div>
      `);

      // Pulsing effect for disrupted grids
      if (isDisrupted) {
        const pulseRect = L.rectangle(bounds, {
          color: "#EF4444",
          weight: 2,
          opacity: 0.8,
          fillOpacity: 0,
          className: "pulse-overlay",
        }).addTo(map);

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

  }, [grids, disruptions]);

  return <div ref={mapRef} className="w-full h-full" />;
}
