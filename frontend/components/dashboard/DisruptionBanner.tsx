"use client";

interface DisruptionBannerProps {
  riskPercent: number;
  description: string;
  earningDrop: string;
  isActive: boolean;
  onViewDetails?: () => void;
}

export default function DisruptionBanner({
  riskPercent,
  description,
  earningDrop,
  isActive,
  onViewDetails,
}: DisruptionBannerProps) {
  if (!isActive || riskPercent < 50) return null;

  return (
    <div className="bg-gradient-to-r from-amber-600/20 to-red-600/20 border border-amber-500/40 rounded-2xl p-4 mb-4">
      <div className="flex items-start gap-3">
        <div className="text-2xl mt-0.5">⚠️</div>
        <div className="flex-1">
          <p className="text-amber-400 font-bold text-sm">
            HIGH DISRUPTION RISK ({riskPercent}%)
          </p>
          <p className="text-slate-300 text-sm mt-1">{description}</p>
          <p className="text-slate-400 text-xs mt-1">
            Estimated earning drop: {earningDrop}
          </p>
          <div className="flex items-center gap-2 mt-2">
            <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full">
              ✅ Coverage ACTIVE
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
