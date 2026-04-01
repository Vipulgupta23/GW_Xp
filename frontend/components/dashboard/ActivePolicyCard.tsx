"use client";
import { useState } from "react";

interface PolicyCardProps {
  policy: {
    plan_id: string;
    weekly_premium_actual: number;
    premium_base: number;
    zone_risk_multiplier: number;
    seasonal_factor: number;
    iss_discount: number;
    persona_factor: number;
    start_date: string;
    end_date: string;
    status: string;
    plans?: {
      name: string;
      coverage_pct: number;
      max_weekly_payout: number;
    };
  };
}

export default function ActivePolicyCard({ policy }: PolicyCardProps) {
  const [showBreakdown, setShowBreakdown] = useState(false);

  const plan = policy.plans || { name: "Incometrix Plus", coverage_pct: 0.70, max_weekly_payout: 2500 };
  const endDate = new Date(policy.end_date);
  const now = new Date();
  const daysLeft = Math.max(0, Math.ceil((endDate.getTime() - now.getTime()) / 86400000));

  const planEmoji = policy.plan_id === "pro" ? "👑" : policy.plan_id === "plus" ? "⭐" : "🛡️";

  return (
    <div className="glass-card overflow-hidden">
      {/* Header gradient */}
      <div className={`px-5 py-4 ${
        policy.plan_id === "pro"
          ? "bg-gradient-to-r from-purple-600/30 to-amber-600/30"
          : policy.plan_id === "plus"
          ? "bg-gradient-to-r from-amber-600/30 to-orange-600/30"
          : "bg-gradient-to-r from-slate-600/30 to-slate-500/30"
      }`}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-400 uppercase tracking-wider">Current Plan</p>
            <h3 className="text-lg font-bold text-white mt-0.5">
              {planEmoji} {plan.name}
            </h3>
          </div>
          <span className={`px-3 py-1 rounded-full text-xs font-bold ${
            policy.status === "active"
              ? "bg-emerald-500/20 text-emerald-400"
              : "bg-red-500/20 text-red-400"
          }`}>
            {policy.status === "active" ? "🟢 ACTIVE" : "🔴 EXPIRED"}
          </span>
        </div>
      </div>

      <div className="px-5 py-4 space-y-3">
        {/* Expiry */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-400">Expires</span>
          <span className="text-white font-medium">
            {endDate.toLocaleDateString("en-IN", { month: "short", day: "numeric" })} ({daysLeft} days left)
          </span>
        </div>

        {/* Premium */}
        <div className="flex items-center justify-between">
          <span className="text-slate-400 text-sm">This Week&apos;s Premium</span>
          <span className="text-amber-400 font-bold text-xl">₹{policy.weekly_premium_actual}</span>
        </div>

        {/* Coverage */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-400">Coverage</span>
          <span className="text-white">{(plan.coverage_pct * 100).toFixed(0)}% | Max ₹{plan.max_weekly_payout.toLocaleString()}/week</span>
        </div>

        {/* Breakdown toggle */}
        <button
          onClick={() => setShowBreakdown(!showBreakdown)}
          className="w-full text-center text-amber-400 text-sm py-2 hover:text-amber-300 transition-colors"
        >
          {showBreakdown ? "Hide Breakdown ▲" : "Tap for Breakdown ▼"}
        </button>

        {/* Premium Breakdown */}
        {showBreakdown && (
          <div className="bg-slate-800/60 rounded-xl p-4 space-y-2 fade-in-up text-sm">
            <div className="flex justify-between">
              <span className="text-slate-400">Base Rate</span>
              <span className="text-white font-mono">₹{policy.premium_base.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">× Zone Risk</span>
              <span className="text-amber-400 font-mono">× {policy.zone_risk_multiplier.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">× Season</span>
              <span className="text-amber-400 font-mono">× {policy.seasonal_factor.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">× ISS Discount</span>
              <span className="text-emerald-400 font-mono">× {policy.iss_discount.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">× Persona</span>
              <span className="text-blue-400 font-mono">× {policy.persona_factor.toFixed(2)}</span>
            </div>
            <hr className="border-slate-600" />
            <div className="flex justify-between font-bold">
              <span className="text-white">This Week</span>
              <span className="text-amber-400 font-mono">₹{policy.weekly_premium_actual.toFixed(2)}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
