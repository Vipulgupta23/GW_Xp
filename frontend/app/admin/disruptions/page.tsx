"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import dynamic from "next/dynamic";

const MapComponent = dynamic(() => import("@/components/admin/DisruptionMap"), { ssr: false });

interface Grid {
  id: string;
  center_lat: number;
  center_lng: number;
  flood_risk: number;
  heat_index: number;
  aqi_avg: number;
  composite_risk: number;
}

interface Disruption {
  id: string;
  trigger_type: string;
  grid_id: string;
  severity: number;
  threshold: number;
  weather_description: string;
  is_active: boolean;
  started_at: string;
}

export default function DisruptionsPage() {
  const [grids, setGrids] = useState<Grid[]>([]);
  const [disruptions, setDisruptions] = useState<Disruption[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [g, d] = await Promise.all([
          api<Grid[]>("/microgrids/all"),
          api<Disruption[]>("/admin/disruptions"),
        ]);
        setGrids(g);
        setDisruptions(d);
      } catch (err) {
        console.error(err);
      }
      setLoading(false);
    };
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const TRIGGER_ICONS: Record<string, string> = {
    heavy_rainfall: "🌧️",
    extreme_heat: "🌡️",
    severe_aqi: "😷",
    flood_alert: "🌊",
    platform_outage: "📵",
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-10 h-10 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Live Disruption Map</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Map */}
        <div className="lg:col-span-2 glass-card overflow-hidden" style={{ height: "500px" }}>
          <MapComponent grids={grids} disruptions={disruptions} />
        </div>

        {/* Active Disruptions Sidebar */}
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
            Active Triggers ({disruptions.length})
          </h3>
          {disruptions.length > 0 ? (
            disruptions.map((d) => (
              <div key={d.id} className="glass-card p-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xl">{TRIGGER_ICONS[d.trigger_type] || "⚡"}</span>
                  <span className="text-white font-semibold text-sm capitalize">
                    {d.trigger_type.replace(/_/g, " ")}
                  </span>
                </div>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Grid</span>
                    <span className="text-white font-mono">{d.grid_id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Severity</span>
                    <span className="text-red-400 font-bold">{d.severity}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Threshold</span>
                    <span className="text-slate-300">{d.threshold}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Started</span>
                    <span className="text-slate-300">
                      {new Date(d.started_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
                    </span>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="glass-card p-6 text-center">
              <p className="text-slate-400 text-sm">No active disruptions</p>
              <p className="text-slate-500 text-xs mt-1">Use Simulate Trigger to test</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
