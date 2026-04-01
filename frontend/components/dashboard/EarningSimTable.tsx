interface HourRow {
  hour_label: string;
  is_peak: boolean;
  deliveries_expected: number;
  earnings_expected: number;
  deliveries_actual: number;
  earnings_actual: number;
  disrupted: boolean;
  surge_label: string;
}

interface EarningSimTableProps {
  rows: HourRow[];
  simulatedEarnings: number;
  actualEarnings: number;
  payoutAmount: number;
}

export default function EarningSimTable({
  rows,
  simulatedEarnings,
  actualEarnings,
  payoutAmount,
}: EarningSimTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="text-slate-400 border-b border-slate-700">
            <th className="text-left py-2 px-1">Hour</th>
            <th className="text-right py-2 px-1">Expected</th>
            <th className="text-right py-2 px-1">Actual</th>
            <th className="text-right py-2 px-1">Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={`${row.hour_label}-${i}`}
              className={`border-b border-slate-800 ${row.disrupted ? "bg-red-500/5" : ""} fade-in-up`}
              style={{ animationDelay: `${i * 100}ms` }}
            >
              <td className="py-1.5 px-1 text-slate-300">
                {row.hour_label} {row.surge_label}
              </td>
              <td className="text-right py-1.5 px-1 text-slate-300">Rs {row.earnings_expected}</td>
              <td className={`text-right py-1.5 px-1 font-medium ${row.disrupted ? "text-red-400" : "text-slate-300"}`}>
                Rs {row.earnings_actual}
              </td>
              <td className="text-right py-1.5 px-1">
                {row.disrupted ? "Flooded" : row.is_peak ? "Peak" : "Active"}
              </td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr className="border-t border-slate-600 font-semibold">
            <td className="py-2 px-1 text-white">Total</td>
            <td className="text-right py-2 px-1 text-slate-300">Rs {simulatedEarnings}</td>
            <td className="text-right py-2 px-1 text-red-400">Rs {actualEarnings}</td>
            <td className="text-right py-2 px-1 text-emerald-400">Payout Rs {payoutAmount.toFixed(0)}</td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}
