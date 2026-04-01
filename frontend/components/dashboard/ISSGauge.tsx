"use client";
import { useEffect, useState } from "react";

interface ISSGaugeProps {
  score: number;
  consistency?: number;
  regularity?: number;
  zone?: number;
  trust?: number;
}

export default function ISSGauge({ score, consistency = 50, regularity = 50, zone = 60, trust = 100 }: ISSGaugeProps) {
  const [animatedScore, setAnimatedScore] = useState(0);

  useEffect(() => {
    let frame: number;
    const duration = 1200;
    const start = performance.now();

    const animate = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setAnimatedScore(Math.round(eased * score));
      if (progress < 1) frame = requestAnimationFrame(animate);
    };

    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, [score]);

  const radius = 70;
  const stroke = 10;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference * (1 - animatedScore / 100);

  const getColor = (s: number) => {
    if (s >= 70) return "#10B981";
    if (s >= 45) return "#FBBF24";
    return "#EF4444";
  };

  const color = getColor(animatedScore);

  const subBars = [
    { label: "Consistency", value: consistency, icon: "📊" },
    { label: "Regularity", value: regularity, icon: "📅" },
    { label: "Zone Safety", value: zone, icon: "📍" },
    { label: "Trust Score", value: trust, icon: "🛡️" },
  ];

  return (
    <div className="glass-card p-6">
      <div className="flex flex-col items-center">
        {/* SVG Gauge */}
        <div className="relative w-44 h-44 mb-4">
          <svg viewBox="0 0 180 180" className="w-full h-full -rotate-90">
            {/* Background ring */}
            <circle
              cx="90" cy="90" r={radius}
              fill="none" stroke="#1E293B" strokeWidth={stroke}
            />
            {/* Animated ring */}
            <circle
              cx="90" cy="90" r={radius}
              fill="none" stroke={color} strokeWidth={stroke}
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={dashOffset}
              style={{ transition: "stroke-dashoffset 0.3s ease-out" }}
            />
          </svg>
          {/* Center text */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-4xl font-bold" style={{ color }}>
              {animatedScore}
            </span>
            <span className="text-xs text-slate-400 mt-1">out of 100</span>
          </div>
        </div>

        <h3 className="font-semibold text-white text-lg mb-1">Income Stability Score</h3>
        <p className="text-slate-400 text-sm mb-4">
          {animatedScore >= 70 ? "Excellent stability! Lower premiums unlocked 🎉" :
           animatedScore >= 45 ? "Good stability. Keep it up!" :
           "Building your score... Stay consistent!"}
        </p>

        {/* Sub-bars */}
        <div className="w-full space-y-3">
          {subBars.map((bar) => (
            <div key={bar.label}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-slate-400 flex items-center gap-1.5">
                  {bar.icon} {bar.label}
                </span>
                <span className="text-xs font-semibold" style={{ color: getColor(bar.value) }}>
                  {Math.round(bar.value)}%
                </span>
              </div>
              <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-1000 ease-out"
                  style={{
                    width: `${bar.value}%`,
                    backgroundColor: getColor(bar.value),
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
