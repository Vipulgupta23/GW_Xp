"use client";
import Link from "next/link";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const navItems = [
    { href: "/admin", icon: "📊", label: "Overview" },
    { href: "/admin/disruptions", icon: "🗺️", label: "Map" },
    { href: "/admin/claims", icon: "📋", label: "Claims" },
    { href: "/admin/fraud", icon: "🛡️", label: "Fraud" },
  ];

  return (
    <div className="min-h-screen">
      {/* Top bar */}
      <div className="bg-slate-900/90 backdrop-blur-sm border-b border-slate-700/50 sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xl">💰</span>
            <span className="font-bold text-white">Incometrix Admin</span>
            <span className="text-xs bg-red-500/20 text-red-400 px-2 py-0.5 rounded-full">OPERATOR</span>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href="/dashboard"
              className="text-xs bg-slate-700 text-slate-300 px-3 py-1.5 rounded-lg hover:bg-slate-600 transition-colors"
            >
              ← Worker View
            </Link>
          </div>
        </div>
        {/* Nav tabs */}
        <div className="max-w-6xl mx-auto px-4 flex gap-1 overflow-x-auto">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center gap-1.5 px-4 py-2.5 text-sm text-slate-400 hover:text-white border-b-2 border-transparent hover:border-amber-500 transition-all whitespace-nowrap"
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-4 py-6">{children}</div>
    </div>
  );
}
