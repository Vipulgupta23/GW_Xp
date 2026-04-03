interface PremiumBreakdownProps {
  base: number;
  zoneMultiplier: number;
  seasonalFactor: number;
  issDiscount: number;
  personaFactor: number;
  finalPremium: number;
  zoneLabel?: string;
  seasonLabel?: string;
  issLabel?: string;
  personaLabel?: string;
  pricingStory?: string;
  coverageHoursLabel?: string;
  coverageHours?: number;
  compact?: boolean;
}

export default function PremiumBreakdown({
  base,
  zoneMultiplier,
  seasonalFactor,
  issDiscount,
  personaFactor,
  finalPremium,
  zoneLabel,
  seasonLabel,
  issLabel,
  personaLabel,
  pricingStory,
  coverageHoursLabel,
  coverageHours,
  compact = false,
}: PremiumBreakdownProps) {
  return (
    <div className={`bg-slate-800/50 rounded-xl ${compact ? "p-3" : "p-4"} space-y-1.5 text-xs`}>
      <div className="flex justify-between">
        <span className="text-slate-400">Base Rate</span>
        <span className="text-white font-mono">Rs {base.toFixed(2)}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-slate-400">x Zone Risk</span>
        <span className="text-amber-400">x {zoneMultiplier.toFixed(2)}{zoneLabel ? ` (${zoneLabel})` : ""}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-slate-400">x Season</span>
        <span className="text-blue-400">x {seasonalFactor.toFixed(2)}{seasonLabel ? ` (${seasonLabel})` : ""}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-slate-400">x ISS Discount</span>
        <span className="text-emerald-400">x {issDiscount.toFixed(2)}{issLabel ? ` (${issLabel})` : ""}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-slate-400">x Persona</span>
        <span className="text-purple-400">x {personaFactor.toFixed(2)}{personaLabel ? ` (${personaLabel})` : ""}</span>
      </div>
      <hr className="border-slate-700" />
      <div className="flex justify-between font-semibold">
        <span className="text-white">This Week</span>
        <span className="text-amber-400 font-mono">Rs {finalPremium.toFixed(2)}</span>
      </div>
      {(coverageHoursLabel || pricingStory) && <hr className="border-slate-700" />}
      {coverageHoursLabel && (
        <div className="flex justify-between gap-4">
          <span className="text-slate-400">Dynamic Cover</span>
          <span className="text-cyan-300 text-right">
            {coverageHours ? `${coverageHours}h · ` : ""}
            {coverageHoursLabel}
          </span>
        </div>
      )}
      {pricingStory && (
        <p className="text-[11px] leading-relaxed text-slate-300">
          {pricingStory}
        </p>
      )}
    </div>
  );
}
