interface Stats {
  total_workers: number;
  active_disruptions: number;
  claims_today: number;
  total_payout_today: number;
  fraud_alerts: number;
  active_policies: number;
}

interface StatsBarProps {
  stats: Stats;
}

export default function StatsBar({ stats }: StatsBarProps) {
  const statCards = [
    { label: "Active Workers", value: stats.total_workers, icon: "👷", color: "text-blue-400", bg: "bg-blue-500/10" },
    { label: "Active Disruptions", value: stats.active_disruptions, icon: "⚡", color: "text-red-400", bg: "bg-red-500/10" },
    { label: "Claims Today", value: stats.claims_today, icon: "📋", color: "text-amber-400", bg: "bg-amber-500/10", sub: `Rs ${stats.total_payout_today.toLocaleString()}` },
    { label: "Fraud Alerts", value: stats.fraud_alerts, icon: "🛡️", color: "text-yellow-400", bg: "bg-yellow-500/10" },
    { label: "Active Policies", value: stats.active_policies, icon: "📄", color: "text-emerald-400", bg: "bg-emerald-500/10" },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      {statCards.map((card, i) => (
        <div
          key={card.label}
          className="glass-card p-4 fade-in-up"
          style={{ animationDelay: `${i * 80}ms` }}
        >
          <div className={`w-10 h-10 ${card.bg} rounded-xl flex items-center justify-center text-xl mb-3`}>
            {card.icon}
          </div>
          <p className={`text-2xl font-bold ${card.color}`}>{card.value}</p>
          <p className="text-xs text-slate-400 mt-0.5">{card.label}</p>
          {card.sub && <p className="text-xs text-slate-500 mt-0.5">{card.sub}</p>}
        </div>
      ))}
    </div>
  );
}
