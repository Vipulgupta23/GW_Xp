"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import StatsBar from "@/components/admin/StatsBar";

interface Stats {
  total_workers: number;
  active_disruptions: number;
  claims_today: number;
  total_payout_today: number;
  fraud_alerts: number;
  active_policies: number;
}

interface DailyStat {
  date: string;
  claims: number;
  payout: number;
}

export default function AdminOverview() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [dailyStats, setDailyStats] = useState<DailyStat[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [s, d] = await Promise.all([
          api<Stats>("/admin/stats"),
          api<DailyStat[]>("/admin/daily-stats?days=7"),
        ]);
        setStats(s);
        setDailyStats(d);
      } catch (err) {
        console.error(err);
      }
      setLoading(false);
    };
    fetchStats();
    const interval = setInterval(fetchStats, 15000);
    return () => clearInterval(interval);
  }, []);

  if (loading || !stats) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-10 h-10 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const maxPayout = Math.max(...dailyStats.map(d => d.payout), 1);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Dashboard Overview</h1>

      {/* Stats Row */}
      <StatsBar stats={stats} />

      {/* Simple chart */}
      <div className="glass-card p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Last 7 Days — Claims & Payouts</h2>
        {dailyStats.length > 0 ? (
          <div className="space-y-3">
            {dailyStats.map((day, i) => (
              <div key={day.date} className="flex items-center gap-4 fade-in-up" style={{ animationDelay: `${i * 60}ms` }}>
                <span className="text-xs text-slate-400 w-16 shrink-0">
                  {new Date(day.date).toLocaleDateString("en-IN", { month: "short", day: "numeric" })}
                </span>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <div className="flex-1 h-4 bg-slate-700 rounded overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-amber-500 to-amber-600 rounded transition-all duration-500"
                        style={{ width: `${Math.max((day.payout / maxPayout) * 100, 2)}%` }}
                      />
                    </div>
                    <span className="text-xs text-amber-400 font-mono w-16 text-right">₹{day.payout.toFixed(0)}</span>
                  </div>
                </div>
                <span className="text-xs text-slate-500 w-14 text-right">{day.claims} claims</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-slate-400 text-sm text-center py-8">No data for the last 7 days</p>
        )}
      </div>
    </div>
  );
}
