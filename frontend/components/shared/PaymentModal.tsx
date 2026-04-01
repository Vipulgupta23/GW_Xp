"use client";
import { useState } from "react";

interface PaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (paymentId: string) => void;
  amount: number;
  planName: string;
}

export default function PaymentModal({ isOpen, onClose, onSuccess, amount, planName }: PaymentModalProps) {
  const [step, setStep] = useState<"select" | "processing" | "success">("select");

  if (!isOpen) return null;

  const handlePay = () => {
    setStep("processing");
    setTimeout(() => {
      setStep("success");
      const mockId = `MOCK_PAY_${Date.now()}`;
      setTimeout(() => {
        onSuccess(mockId);
        setStep("select");
      }, 1500);
    }, 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={step === "select" ? onClose : undefined} />

      {/* Modal */}
      <div className="relative w-full max-w-md bg-slate-800 rounded-t-3xl sm:rounded-2xl slide-up border border-slate-700 overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center">
                <span className="text-blue-600 font-bold text-sm">₹</span>
              </div>
              <div>
                <p className="text-white font-semibold text-sm">Incometrix AI</p>
                <p className="text-blue-100 text-xs">{planName}</p>
              </div>
            </div>
            <p className="text-white font-bold text-xl">₹{amount}</p>
          </div>
        </div>

        {step === "select" && (
          <div className="p-6">
            <p className="text-slate-400 text-sm mb-4">Pay using UPI</p>

            {/* UPI Options */}
            <div className="space-y-3 mb-6">
              {[
                { name: "Google Pay", icon: "🟢", color: "bg-green-900/30" },
                { name: "PhonePe", icon: "🟣", color: "bg-purple-900/30" },
                { name: "Paytm", icon: "🔵", color: "bg-blue-900/30" },
              ].map((upi) => (
                <button
                  key={upi.name}
                  onClick={handlePay}
                  className={`w-full flex items-center gap-4 p-4 rounded-xl ${upi.color} border border-slate-600 hover:border-amber-500/50 transition-all`}
                >
                  <span className="text-2xl">{upi.icon}</span>
                  <span className="text-white font-medium">{upi.name}</span>
                  <span className="ml-auto text-slate-400">›</span>
                </button>
              ))}
            </div>

            <button
              onClick={handlePay}
              className="w-full btn-primary text-center"
            >
              Pay ₹{amount} with UPI
            </button>

            <button
              onClick={onClose}
              className="w-full mt-3 text-slate-400 text-sm py-2 hover:text-white transition-colors"
            >
              Cancel
            </button>
          </div>
        )}

        {step === "processing" && (
          <div className="p-10 flex flex-col items-center">
            <div className="w-16 h-16 border-3 border-amber-500 border-t-transparent rounded-full animate-spin mb-4" />
            <p className="text-white font-semibold">Processing Payment...</p>
            <p className="text-slate-400 text-sm mt-1">Please wait</p>
          </div>
        )}

        {step === "success" && (
          <div className="p-10 flex flex-col items-center">
            <div className="w-16 h-16 bg-emerald-500/20 rounded-full flex items-center justify-center mb-4 glow-green">
              <svg className="w-8 h-8 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <p className="text-emerald-400 font-bold text-lg">Payment Successful!</p>
            <p className="text-slate-400 text-sm mt-1">₹{amount} paid for {planName}</p>
          </div>
        )}
      </div>
    </div>
  );
}
