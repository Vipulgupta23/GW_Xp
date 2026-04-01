"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // Check if worker is logged in
    const workerId = localStorage.getItem("worker_id");
    if (workerId) {
      router.replace("/dashboard");
    } else {
      router.replace("/login");
    }
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="text-4xl mb-4">💰</div>
        <h1 className="text-2xl font-bold text-amber-500">Incometrix AI</h1>
        <p className="text-slate-400 mt-2">Loading...</p>
        <div className="mt-4 w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto" />
      </div>
    </div>
  );
}
