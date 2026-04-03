"use client";

interface DisruptionBannerProps {
  title?: string;
  riskPercent: number;
  description: string;
  earningDrop: string;
  isActive: boolean;
  coverageActive?: boolean;
  onViewDetails?: () => void;
}

export default function DisruptionBanner({
  title = "Active Disruption",
  riskPercent,
  description,
  earningDrop,
  isActive,
  coverageActive = false,
  onViewDetails,
}: DisruptionBannerProps) {
  if (!isActive) {
    return (
      <div className="bg-slate-800/40 border border-slate-700 rounded-2xl p-4 mb-4">
        <div className="flex items-start gap-3">
          <div className="text-2xl mt-0.5">🛡️</div>
          <div className="flex-1">
            <p className="text-emerald-400 font-bold text-sm">ZONE CALM</p>
            <p className="text-slate-300 text-sm mt-1">{description}</p>
            <p className="text-slate-500 text-xs mt-1">
              {coverageActive ? "Your policy is active and monitoring continues." : "No active policy. Buy a plan to enable zero-touch protection."}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-r from-amber-600/20 to-red-600/20 border border-amber-500/40 rounded-2xl p-4 mb-4">
      <div className="flex items-start gap-3">
        <div className="text-2xl mt-0.5">⚠️</div>
        <div className="flex-1">
          <p className="text-amber-400 font-bold text-sm">
            {title.toUpperCase()} ({riskPercent}%)
          </p>
          <p className="text-slate-300 text-sm mt-1">{description}</p>
          <p className="text-slate-400 text-xs mt-1">
            Estimated earning drop: {earningDrop}
          </p>
          <div className="flex items-center gap-2 mt-2">
            <span className={`text-xs px-2 py-0.5 rounded-full ${coverageActive ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"}`}>
              {coverageActive ? "Coverage ACTIVE" : "No active policy"}
            </span>
            {onViewDetails && (
              <button
                onClick={onViewDetails}
                className="text-xs text-amber-400 hover:text-amber-300 transition-colors"
              >
                View Details →
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
