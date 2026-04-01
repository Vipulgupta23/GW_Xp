"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import EmailInput from "@/components/auth/EmailInput";
import OTPVerify from "@/components/auth/OTPVerify";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [step, setStep] = useState<"email" | "otp">("email");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");

  const handleSendOTP = async () => {
    const normalizedEmail = email.trim().toLowerCase();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail)) {
      setError("Enter a valid email address");
      return;
    }
    setLoading(true);
    setError("");
    setInfo("");
    try {
      const res = await api<{ dev_otp?: string; message?: string }>("/auth/send-otp", {
        method: "POST",
        body: { email: normalizedEmail },
      });
      if (res.dev_otp) {
        setInfo(`Dev mode OTP: ${res.dev_otp}`);
      }
      setStep("otp");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to send OTP");
    }
    setLoading(false);
  };

  const handleVerifyOTP = async (otpStr: string) => {
    setLoading(true);
    setError("");
    try {
      const res = await api<{
        access_token: string;
        worker: { id: string } | null;
        is_new: boolean;
      }>("/auth/verify-otp", {
        method: "POST",
        body: { email: email.trim().toLowerCase(), otp: otpStr },
      });
      localStorage.setItem("access_token", res.access_token);
      if (res.worker) {
        localStorage.setItem("worker_id", res.worker.id);
        router.push("/dashboard");
      } else {
        localStorage.setItem("auth_email", email.trim().toLowerCase());
        router.push("/onboard");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Invalid OTP");
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4">
      {/* Logo */}
      <div className="mb-10 text-center fade-in-up">
        <div className="w-20 h-20 bg-gradient-to-br from-amber-400 to-amber-600 rounded-2xl flex items-center justify-center mx-auto mb-4 glow-amber shadow-lg">
          <span className="text-3xl">💰</span>
        </div>
        <h1 className="text-3xl font-bold text-white">Incometrix AI</h1>
        <p className="text-slate-400 mt-1 text-sm">Predict. Protect. Pay.</p>
      </div>

      {/* Card */}
      <div className="glass-card w-full max-w-sm p-6" style={{ animationDelay: "0.1s" }}>
        {step === "email" ? (
          <>
            <h2 className="text-lg font-semibold text-white mb-1">Welcome Back! 👋</h2>
            <p className="text-slate-400 text-sm mb-6">Enter your email to continue</p>

            <EmailInput email={email} onChange={setEmail} disabled={loading} />

            {error && (
              <p className="text-red-400 text-sm mb-4">{error}</p>
            )}
            {info && (
              <p className="text-amber-300 text-sm mb-4">{info}</p>
            )}

            <button
              onClick={handleSendOTP}
              disabled={loading || !email.trim()}
              className="btn-primary w-full flex items-center justify-center gap-2"
              id="send-otp-btn"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
              ) : (
                <>Send OTP</>
              )}
            </button>

            <p className="text-slate-500 text-xs mt-4 text-center">
              By continuing, you agree to our Terms of Service
            </p>
          </>
        ) : (
          <>
            <h2 className="text-lg font-semibold text-white mb-1">Enter OTP 🔐</h2>
            <p className="text-slate-400 text-sm mb-6">
              Sent to {email}
            </p>
            <OTPVerify loading={loading} onVerify={handleVerifyOTP} error={error} />
            {info && <p className="text-amber-300 text-sm mb-2">{info}</p>}

            <button
              onClick={() => {
                setStep("email");
                setError("");
                setInfo("");
              }}
              className="w-full mt-3 text-slate-400 text-sm py-2 hover:text-white transition-colors"
            >
              ← Change email
            </button>
          </>
        )}
      </div>
    </div>
  );
}
