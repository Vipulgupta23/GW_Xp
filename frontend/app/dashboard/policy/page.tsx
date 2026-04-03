"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import PaymentModal from "@/components/shared/PaymentModal";
import PremiumBreakdown from "@/components/dashboard/PremiumBreakdown";

interface Plan {
  id: string;
  name: string;
  weekly_premium_base: number;
  max_weekly_payout: number;
  coverage_pct: number;
  description: string;
  features: string;
  dynamic_premium: number;
  premium_details: {
    base: number;
    zone_multiplier: number;
    seasonal_factor: number;
    iss_discount: number;
    persona_factor: number;
    final_premium: number;
    zone_label: string;
    season_label: string;
    iss_label: string;
    persona_label: string;
    coverage_hours?: number;
    coverage_hours_label?: string;
    pricing_story?: string;
    waterlogging_adjustment?: number;
  };
}

export default function PolicyPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [activePolicy, setActivePolicy] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [paymentModal, setPaymentModal] = useState<{ open: boolean; plan: Plan | null }>({ open: false, plan: null });
  const [subscribing, setSubscribing] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      const workerId = localStorage.getItem("worker_id");
      if (!workerId) {
        setError("Worker profile missing. Please complete onboarding first.");
        setLoading(false);
        return;
      }
      try {
        const [plansRes, policyRes] = await Promise.all([
          api<{ plans: Plan[] }>(`/policies/plans/${workerId}`),
          api<{ policy: Record<string, unknown> | null }>(`/policies/active/${workerId}`),
        ]);
        setPlans(plansRes.plans);
        setActivePolicy(policyRes.policy);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load plans");
      }
      setLoading(false);
    };
    fetchData();
  }, []);

  const handleSubscribe = async (paymentId: string) => {
    const plan = paymentModal.plan;
    if (!plan) return;
    setSubscribing(true);
    try {
      const workerId = localStorage.getItem("worker_id");
      if (!workerId) {
        setError("Worker profile missing. Please complete onboarding first.");
        setSubscribing(false);
        return;
      }
      const res = await api<{ policy: Record<string, unknown> }>("/policies/subscribe", {
        method: "POST",
        body: {
          worker_id: workerId,
          plan_id: plan.id,
          mock_payment_id: paymentId,
        },
      });
      setActivePolicy(res.policy);
      setPaymentModal({ open: false, plan: null });
      setError("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to activate plan");
    }
    setSubscribing(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-10 h-10 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const planIcons: Record<string, string> = { basic: "🛡️", plus: "⭐", pro: "👑" };
  const planGradients: Record<string, string> = {
    basic: "from-slate-600/20 to-slate-500/20",
    plus: "from-amber-600/20 to-orange-600/20",
    pro: "from-purple-600/20 to-amber-600/20",
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-white">Insurance Plans</h1>
      <p className="text-slate-400 text-sm">Premiums personalized for your zone, ISS, and risk profile</p>
      {error && <p className="text-red-400 text-sm">{error}</p>}

      {/* Plan Cards */}
      <div className="space-y-4">
        {plans.map((plan, i) => {
          const features = typeof plan.features === "string" ? JSON.parse(plan.features) : plan.features;
          const isActive = activePolicy && (activePolicy as Record<string, unknown>).plan_id === plan.id;

          return (
            <div
              key={plan.id}
              className={`glass-card overflow-hidden fade-in-up ${isActive ? "ring-2 ring-amber-500" : ""}`}
              style={{ animationDelay: `${i * 100}ms` }}
            >
              <div className={`bg-gradient-to-r ${planGradients[plan.id] || planGradients.basic} px-5 py-4`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-3xl mb-1">{planIcons[plan.id] || "🛡️"}</p>
                    <h3 className="text-lg font-bold text-white">{plan.name}</h3>
                    <p className="text-slate-400 text-xs mt-0.5">{plan.description}</p>
                  </div>
                  {isActive && (
                    <span className="bg-amber-500/20 text-amber-400 px-3 py-1 rounded-full text-xs font-bold">
                      CURRENT
                    </span>
                  )}
                </div>
              </div>

              <div className="px-5 py-4">
                {/* Price */}
                <div className="flex items-end gap-2 mb-4">
                  <span className="text-3xl font-bold text-white">₹{plan.dynamic_premium.toFixed(0)}</span>
                  <span className="text-slate-400 text-sm mb-1">/week</span>
                  {plan.dynamic_premium !== plan.weekly_premium_base && (
                    <span className="text-slate-500 text-sm line-through mb-1">₹{plan.weekly_premium_base}</span>
                  )}
                </div>

                {/* Premium breakdown */}
                <div className="mb-4">
                  <PremiumBreakdown
                    base={plan.premium_details.base}
                    zoneMultiplier={plan.premium_details.zone_multiplier}
                    seasonalFactor={plan.premium_details.seasonal_factor}
                    issDiscount={plan.premium_details.iss_discount}
                    personaFactor={plan.premium_details.persona_factor}
                    finalPremium={plan.premium_details.final_premium}
                    zoneLabel={plan.premium_details.zone_label}
                    seasonLabel={plan.premium_details.season_label}
                    issLabel={plan.premium_details.iss_label}
                    personaLabel={plan.premium_details.persona_label}
                    coverageHours={plan.premium_details.coverage_hours}
                    coverageHoursLabel={plan.premium_details.coverage_hours_label}
                    pricingStory={plan.premium_details.pricing_story}
                    compact
                  />
                </div>

                {/* Features */}
                <div className="space-y-2 mb-4">
                  {(features as string[]).map((f: string, j: number) => (
                    <div key={j} className="flex items-center gap-2 text-sm">
                      <span className="text-emerald-400">✓</span>
                      <span className="text-slate-300">{f}</span>
                    </div>
                  ))}
                </div>

                {/* Coverage info */}
                <div className="flex items-center justify-between text-sm mb-4 bg-slate-800/30 rounded-lg p-2">
                  <span className="text-slate-400">Coverage: {(plan.coverage_pct * 100).toFixed(0)}%</span>
                  <span className="text-slate-400">Max: ₹{plan.max_weekly_payout.toLocaleString()}/week</span>
                </div>
                {plan.premium_details.coverage_hours && (
                  <div className="mb-4 rounded-lg border border-cyan-400/20 bg-cyan-400/10 px-3 py-2 text-xs text-cyan-100">
                    Protected for up to <span className="font-semibold">{plan.premium_details.coverage_hours} hours</span> this week
                    {plan.premium_details.coverage_hours_label ? ` · ${plan.premium_details.coverage_hours_label}` : ""}
                  </div>
                )}

                {/* CTA */}
                {isActive ? (
                  <button className="w-full bg-emerald-500/20 text-emerald-400 py-3 rounded-xl font-semibold" disabled>
                    ✅ Currently Active
                  </button>
                ) : (
                  <button
                    onClick={() => setPaymentModal({ open: true, plan })}
                    className="btn-primary w-full"
                    disabled={subscribing}
                  >
                    Pay ₹{plan.dynamic_premium.toFixed(0)} for this week
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Payment Modal */}
      {paymentModal.plan && (
        <PaymentModal
          isOpen={paymentModal.open}
          onClose={() => setPaymentModal({ open: false, plan: null })}
          onSuccess={handleSubscribe}
          amount={paymentModal.plan.dynamic_premium}
          planName={paymentModal.plan.name}
        />
      )}
    </div>
  );
}
