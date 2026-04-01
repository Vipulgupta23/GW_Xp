"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [workerId, setWorkerId] = useState<string | null>(null);

  useEffect(() => {
    const id = localStorage.getItem("worker_id");
    if (!id) {
      router.replace("/login");
      return;
    }
    setWorkerId(id);
  }, [router]);

  if (!workerId) return null;

  const navItems = [
    { href: "/dashboard", icon: "🏠", label: "Home" },
    { href: "/dashboard/policy", icon: "🛡️", label: "Policy" },
    { href: "/dashboard/claims", icon: "💰", label: "Claims" },
    { href: "/dashboard/profile", icon: "👤", label: "Profile" },
  ];

  return (
    <div className="min-h-screen pb-20">
      {/* Top bar */}
      <div className="bg-slate-900/80 backdrop-blur-sm border-b border-slate-700/50 sticky top-0 z-40">
        <div className="max-w-md mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl">💰</span>
            <span className="font-bold text-white">Incometrix</span>
          </div>
          <Link
            href="/admin"
            className="text-xs bg-slate-700 text-slate-300 px-3 py-1.5 rounded-lg hover:bg-slate-600 transition-colors"
          >
            Admin →
          </Link>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-md mx-auto px-4 py-4">
        {children}
      </div>

      {/* Bottom nav */}
      <nav className="fixed bottom-0 left-0 right-0 bg-slate-900/95 backdrop-blur-md border-t border-slate-700/50 z-40">
        <div className="max-w-md mx-auto flex items-center justify-around py-2">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="flex flex-col items-center gap-0.5 py-1 px-4 text-slate-400 hover:text-amber-400 transition-colors"
            >
              <span className="text-xl">{item.icon}</span>
              <span className="text-[10px] font-medium">{item.label}</span>
            </Link>
          ))}
        </div>
      </nav>
    </div>
  );
}
