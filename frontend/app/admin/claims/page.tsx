"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import ClaimsTable from "@/components/admin/ClaimsTable";

interface Claim {
  id: string;
  trigger_type: string;
  status: string;
  payout_amount: number;
  income_gap: number;
  fraud_score: number;
  created_at: string;
  hinglish_explanation: string;
  earning_simulation: Record<string, unknown>;
  workers?: { name: string; platform: string; grid_id: string };
}

export default function AdminClaimsPage() {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [simForm, setSimForm] = useState({
    trigger_type: "heavy_rainfall",
    grid_id: "BLR_05_08",
    severity: 65,
  });
  const [simResult, setSimResult] = useState<string | null>(null);
  const [selectedClaim, setSelectedClaim] = useState<Claim | null>(null);

  const fetchClaims = async () => {
    try {
      const data = await api<Claim[]>("/admin/claims-queue?limit=50");
      setClaims(data);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchClaims();
    const interval = setInterval(fetchClaims, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleSimulate = async () => {
    setSimulating(true);
    setSimResult(null);
    try {
      const res = await api<{ message: string }>("/admin/simulate-trigger", {
        method: "POST",
        body: simForm,
      });
      setSimResult(res.message);
      // Refresh claims after 2s
      setTimeout(fetchClaims, 2000);
    } catch (err) {
      setSimResult(`Error: ${err instanceof Error ? err.message : "Failed"}`);
    }
    setSimulating(false);
  };

  const handleApprove = async (claimId: string) => {
    await api(`/claims/${claimId}/approve`, { method: "PUT" });
    fetchClaims();
  };

  const handleReject = async (claimId: string) => {
    await api(`/claims/${claimId}/reject`, { method: "PUT" });
    fetchClaims();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Claims Queue</h1>
        <span className="text-sm text-slate-400">Auto-refreshes every 10s</span>
      </div>

      {/* 🔴 SIMULATE DISRUPTION - Critical for Demo */}
      <div className="glass-card p-5 border-2 border-red-500/30">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-xl">🔴</span>
          <h2 className="text-lg font-bold text-white">Simulate Disruption</h2>
          <span className="text-xs bg-red-500/20 text-red-400 px-2 py-0.5 rounded-full">DEMO</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div>
            <label className="text-xs text-slate-400 block mb-1">Trigger Type</label>
            <select
              value={simForm.trigger_type}
              onChange={(e) => setSimForm({ ...simForm, trigger_type: e.target.value })}
              className="input-field text-sm"
            >
              <option value="heavy_rainfall">🌧️ Heavy Rainfall</option>
              <option value="extreme_heat">🌡️ Extreme Heat</option>
              <option value="severe_aqi">😷 Severe AQI</option>
              <option value="flood_alert">🌊 Flood Alert</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Grid ID</label>
            <input
              value={simForm.grid_id}
              onChange={(e) => setSimForm({ ...simForm, grid_id: e.target.value })}
              className="input-field text-sm"
              placeholder="BLR_05_08"
            />
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Severity</label>
            <input
              type="number"
              value={simForm.severity}
              onChange={(e) => setSimForm({ ...simForm, severity: Number(e.target.value) })}
              className="input-field text-sm"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={handleSimulate}
              disabled={simulating}
              className="w-full bg-red-500 hover:bg-red-600 text-white font-bold py-3 px-4 rounded-xl transition-all active:scale-95 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {simulating ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>🔴 Fire Trigger</>
              )}
            </button>
          </div>
        </div>

        {simResult && (
          <div className="mt-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-3 text-sm text-emerald-400">
            {simResult}
          </div>
        )}
      </div>

      <ClaimsTable
        claims={claims}
        onSelectClaim={setSelectedClaim}
        onApprove={handleApprove}
        onReject={handleReject}
      />

      {/* Claim detail modal */}
      {selectedClaim && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" onClick={() => setSelectedClaim(null)}>
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
          <div className="relative w-full max-w-lg mx-4 glass-card p-6 max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-white">Claim Details</h3>
              <button onClick={() => setSelectedClaim(null)} className="text-slate-400 hover:text-white text-xl">✕</button>
            </div>

            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-400">Worker</span>
                <span className="text-white">{selectedClaim.workers?.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Trigger</span>
                <span className="text-white capitalize">{selectedClaim.trigger_type.replace(/_/g, " ")}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Income Gap</span>
                <span className="text-red-400">₹{selectedClaim.income_gap.toFixed(0)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Payout</span>
                <span className="text-emerald-400 font-bold">₹{selectedClaim.payout_amount.toFixed(0)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Fraud Score</span>
                <span className={selectedClaim.fraud_score > 0.5 ? "text-red-400" : "text-emerald-400"}>
                  {(selectedClaim.fraud_score * 100).toFixed(0)}%
                </span>
              </div>

              <hr className="border-slate-700" />

              <div>
                <p className="text-slate-400 mb-1">Hinglish Explanation</p>
                <p className="text-emerald-300 bg-emerald-500/10 p-3 rounded-xl text-sm">{selectedClaim.hinglish_explanation}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
