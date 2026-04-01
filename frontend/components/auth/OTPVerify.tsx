"use client";

import { useState } from "react";

interface OTPVerifyProps {
  loading?: boolean;
  onVerify: (otp: string) => Promise<void> | void;
  error?: string;
}

export default function OTPVerify({ loading = false, onVerify, error = "" }: OTPVerifyProps) {
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);

  const triggerVerify = async (digits: string[]) => {
    const otpStr = digits.join("");
    if (otpStr.length === 6) {
      await onVerify(otpStr);
    }
  };

  const handleOTPInput = async (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;

    const nextOtp = [...otp];
    nextOtp[index] = value.slice(-1);
    setOtp(nextOtp);

    if (value && index < 5) {
      const next = document.getElementById(`otp-${index + 1}`);
      next?.focus();
    }

    if (nextOtp.every((d) => d) && index === 5) {
      setTimeout(() => {
        void triggerVerify(nextOtp);
      }, 200);
    }
  };

  const handleOTPKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      const prev = document.getElementById(`otp-${index - 1}`);
      prev?.focus();
    }
  };

  return (
    <div>
      <div className="flex gap-2 justify-center mb-6">
        {otp.map((digit, i) => (
          <input
            key={i}
            id={`otp-${i}`}
            type="text"
            inputMode="numeric"
            maxLength={1}
            value={digit}
            onChange={(e) => {
              void handleOTPInput(i, e.target.value);
            }}
            onKeyDown={(e) => handleOTPKeyDown(i, e)}
            className="w-12 h-14 rounded-xl bg-slate-800 border border-slate-600 text-center text-xl font-bold text-white
                     focus:border-amber-500 focus:ring-1 focus:ring-amber-500/50 outline-none transition-all"
            disabled={loading}
          />
        ))}
      </div>

      {error && <p className="text-red-400 text-sm mb-4 text-center">{error}</p>}

      <button
        onClick={() => {
          void triggerVerify(otp);
        }}
        disabled={loading || otp.some((d) => !d)}
        className="btn-primary w-full flex items-center justify-center gap-2"
        id="verify-otp-btn"
      >
        {loading ? (
          <div className="w-5 h-5 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
        ) : (
          <>Verify & Continue</>
        )}
      </button>
    </div>
  );
}
