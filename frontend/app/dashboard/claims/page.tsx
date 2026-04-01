"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import ClaimCard from "@/components/dashboard/ClaimCard";

export default function ClaimsPage() {
  const [claims, setClaims] = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchClaims = async () => {
      const workerId = localStorage.getItem("worker_id");
      if (!workerId) return;
      try {
        const data = await api<Array<Record<string, unknown>>>(`/claims/worker/${workerId}?limit=20`);
        setClaims(data);
      } catch (err) {
        console.error(err);
      }
      setLoading(false);
    };
    fetchClaims();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-10 h-10 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const totalPayout = claims.reduce((sum, c) => sum + ((c.payout_amount as number) || 0), 0);
  const approvedCount = claims.filter(c => c.status === "paid" || c.status === "approved").length;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-white">Claims History</h1>

      {/* Summary stats */}
      <div className="grid grid-cols-3 gap-3">
        <div className="glass-card p-3 text-center">
          <p className="text-2xl font-bold text-white">{claims.length}</p>
          <p className="text-xs text-slate-400">Total Claims</p>
        </div>
        <div className="glass-card p-3 text-center">
          <p className="text-2xl font-bold text-emerald-400">{approvedCount}</p>
          <p className="text-xs text-slate-400">Approved</p>
        </div>
        <div className="glass-card p-3 text-center">
          <p className="text-2xl font-bold text-amber-400">₹{totalPayout.toFixed(0)}</p>
          <p className="text-xs text-slate-400">Total Paid</p>
        </div>
      </div>

      {/* Claims list */}
      {claims.length > 0 ? (
        <div className="space-y-3">
          {claims.map((claim, i) => (
            <div key={claim.id as string} style={{ animationDelay: `${i * 80}ms` }} className="fade-in-up">
              <ClaimCard claim={claim as Parameters<typeof ClaimCard>[0]["claim"]} />
            </div>
          ))}
        </div>
      ) : (
        <div className="glass-card p-8 text-center">
          <p className="text-3xl mb-3">🛡️</p>
          <p className="text-white font-semibold">No claims yet</p>
          <p className="text-slate-400 text-sm mt-1">
            We&apos;re monitoring weather and AQI 24/7. Claims are processed automatically — you don&apos;t need to do anything!
          </p>
        </div>
      )}
    </div>
  );
}
