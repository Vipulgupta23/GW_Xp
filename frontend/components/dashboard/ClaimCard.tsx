"use client";
import { useState } from "react";
import EarningSimTable from "@/components/dashboard/EarningSimTable";

interface ClaimCardProps {
  claim: {
    id: string;
    trigger_type: string;
    status: string;
    payout_amount: number;
    income_gap: number;
    simulated_earnings: number;
    actual_earnings: number;
    coverage_pct: number;
    fraud_score: number;
    hinglish_explanation: string;
    earning_simulation?: {
      hourly_breakdown: Array<{
        hour_label: string;
        is_peak: boolean;
        deliveries_expected: number;
        earnings_expected: number;
        deliveries_actual: number;
        earnings_actual: number;
        disrupted: boolean;
        surge_label: string;
      }>;
    };
    created_at: string;
  };
}

const TRIGGER_ICONS: Record<string, string> = {
  heavy_rainfall: "🌧️",
  extreme_heat: "🌡️",
  severe_aqi: "😷",
  flood_alert: "🌊",
  platform_outage: "📵",
  cyclone: "🌪️",
};

export default function ClaimCard({ claim }: ClaimCardProps) {
  const [showExplanation, setShowExplanation] = useState(false);
  const [showSimulation, setShowSimulation] = useState(false);

  const icon = TRIGGER_ICONS[claim.trigger_type] || "⚡";
  const date = new Date(claim.created_at).toLocaleDateString("en-IN", {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  });

  return (
    <div className="glass-card p-4">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-slate-700 rounded-xl flex items-center justify-center text-xl">
            {icon}
          </div>
          <div>
            <p className="text-white font-semibold text-sm capitalize">
              {claim.trigger_type.replace(/_/g, " ")}
            </p>
            <p className="text-slate-400 text-xs">{date}</p>
          </div>
        </div>
        <span className={`status-badge status-${claim.status}`}>
          {claim.status.replace("_", " ")}
        </span>
      </div>

      {/* Payout */}
      <div className="bg-slate-800/60 rounded-xl p-3 mb-3">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-400">Income Gap</p>
            <p className="text-red-400 font-semibold">₹{claim.income_gap.toFixed(0)}</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-slate-400">Coverage</p>
            <p className="text-slate-300 font-medium">{((claim.coverage_pct || 0.7) * 100).toFixed(0)}%</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-slate-400">Payout</p>
            <p className="text-emerald-400 font-bold text-lg">₹{claim.payout_amount.toFixed(0)}</p>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={() => setShowExplanation(!showExplanation)}
          className="flex-1 text-sm bg-amber-500/10 text-amber-400 py-2 px-3 rounded-lg hover:bg-amber-500/20 transition-colors font-medium"
        >
          Why? 🤖
        </button>
        <button
          onClick={() => setShowSimulation(!showSimulation)}
          className="flex-1 text-sm bg-blue-500/10 text-blue-400 py-2 px-3 rounded-lg hover:bg-blue-500/20 transition-colors font-medium"
        >
          Simulation 📊
        </button>
      </div>

      {/* Hinglish Explanation */}
      {showExplanation && (
        <div className="mt-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 fade-in-up">
          <p className="text-emerald-300 text-sm leading-relaxed">{claim.hinglish_explanation}</p>
        </div>
      )}

      {/* Earning Simulation */}
      {showSimulation && claim.earning_simulation?.hourly_breakdown && (
        <div className="mt-3 fade-in-up">
          <EarningSimTable
            rows={claim.earning_simulation.hourly_breakdown}
            simulatedEarnings={claim.simulated_earnings}
            actualEarnings={claim.actual_earnings}
            payoutAmount={claim.payout_amount}
          />
        </div>
      )}
    </div>
  );
}
