"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import ISSGauge from "@/components/dashboard/ISSGauge";
import DisruptionBanner from "@/components/dashboard/DisruptionBanner";
import ActivePolicyCard from "@/components/dashboard/ActivePolicyCard";
import ClaimCard from "@/components/dashboard/ClaimCard";
import WhatsAppModal from "@/components/dashboard/WhatsAppModal";

export default function DashboardPage() {
  const [worker, setWorker] = useState<Record<string, unknown> | null>(null);
  const [policy, setPolicy] = useState<Record<string, unknown> | null>(null);
  const [claims, setClaims] = useState<Array<Record<string, unknown>>>([]);
  const [showWhatsApp, setShowWhatsApp] = useState(false);
  const [latestPayout, setLatestPayout] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const workerId = localStorage.getItem("worker_id");
    if (!workerId) return;

    const fetchData = async () => {
      try {
        const [w, p, c] = await Promise.all([
          api<Record<string, unknown>>(`/workers/${workerId}`),
          api<{ policy: Record<string, unknown> | null }>(`/policies/active/${workerId}`),
          api<Array<Record<string, unknown>>>(`/claims/worker/${workerId}?limit=5`),
        ]);
        setWorker(w);
        setPolicy(p.policy);
        setClaims(c);

        // Auto-show WhatsApp modal for latest paid claim
        const paidClaim = c.find((cl: Record<string, unknown>) => cl.status === "paid" || cl.status === "approved");
        if (paidClaim) {
          setLatestPayout(paidClaim);
          const shown = sessionStorage.getItem(`whatsapp_shown_${paidClaim.id}`);
          if (!shown) {
            setTimeout(() => {
              setShowWhatsApp(true);
              sessionStorage.setItem(`whatsapp_shown_${paidClaim.id}`, "1");
            }, 2000);
          }
        }
      } catch (err) {
        console.error("Dashboard fetch error:", err);
      }
      setLoading(false);
    };

    fetchData();
    // Poll every 30s for new claims
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-10 h-10 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Welcome */}
      <div className="fade-in-up">
        <h1 className="text-2xl font-bold text-white">
          Hey {(worker?.name as string)?.split(" ")[0] || "there"}! 👋
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          {new Date().toLocaleDateString("en-IN", { weekday: "long", month: "long", day: "numeric" })}
        </p>
      </div>

      {/* Disruption Banner */}
      <DisruptionBanner
        riskPercent={65}
        description="Heavy rain expected 4PM–10PM"
        earningDrop="₹350–₹500"
        isActive={true}
      />

      {/* ISS Gauge */}
      <ISSGauge
        score={(worker?.iss_score as number) || 50}
        consistency={50}
        regularity={50}
        zone={60}
        trust={100}
      />

      {/* Active Policy */}
      {policy ? (
        <ActivePolicyCard policy={policy as Parameters<typeof ActivePolicyCard>[0]["policy"]} />
      ) : (
        <div className="glass-card p-6 text-center">
          <p className="text-slate-400 mb-3">No active policy</p>
          <a href="/dashboard/policy" className="btn-primary inline-block">
            Choose a Plan →
          </a>
        </div>
      )}

      {/* Recent Claims */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-3">Recent Claims</h2>
        {claims.length > 0 ? (
          <div className="space-y-3">
            {claims.map((claim, i) => (
              <div key={claim.id as string} style={{ animationDelay: `${i * 100}ms` }} className="fade-in-up">
                <ClaimCard claim={claim as Parameters<typeof ClaimCard>[0]["claim"]} />
              </div>
            ))}
          </div>
        ) : (
          <div className="glass-card p-6 text-center">
            <p className="text-slate-400 text-sm">No claims yet. Your coverage is active — we&apos;ll auto-protect you! 🛡️</p>
          </div>
        )}
      </div>

      {/* WhatsApp Modal */}
      {latestPayout && (
        <WhatsAppModal
          isOpen={showWhatsApp}
          onClose={() => setShowWhatsApp(false)}
          message={(latestPayout.hinglish_explanation as string) || "Aapka payout process ho gaya hai!"}
          amount={(latestPayout.payout_amount as number) || 0}
        />
      )}
    </div>
  );
}
