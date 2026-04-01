"use client";
import { useEffect, useState } from "react";

interface WhatsAppModalProps {
  isOpen: boolean;
  onClose: () => void;
  message: string;
  amount: number;
}

export default function WhatsAppModal({ isOpen, onClose, message, amount }: WhatsAppModalProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => setVisible(true), 100);
    } else {
      setVisible(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center" onClick={onClose}>
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />

      <div
        className={`relative w-full max-w-md mb-6 mx-4 transition-all duration-400 ${
          visible ? "translate-y-0 opacity-100" : "translate-y-full opacity-0"
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* WhatsApp notification card */}
        <div className="bg-[#1F2C34] rounded-2xl overflow-hidden shadow-2xl border border-[#2A3942]">
          {/* Header */}
          <div className="bg-[#075E54] px-4 py-3 flex items-center gap-3">
            <div className="w-8 h-8 bg-[#25D366] rounded-full flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/>
              </svg>
            </div>
            <div className="flex-1">
              <p className="text-white font-semibold text-sm">WhatsApp</p>
              <p className="text-[#8696A0] text-xs">Incometrix AI · now</p>
            </div>
            <button onClick={onClose} className="text-[#8696A0] hover:text-white">
              ✕
            </button>
          </div>

          {/* Message body */}
          <div className="px-4 py-4">
            <div className="bg-[#005C4B] rounded-lg rounded-tl-none p-3 max-w-[90%]">
              <p className="text-white text-sm leading-relaxed">{message}</p>
              <div className="flex items-center justify-between mt-2">
                <span className="text-emerald-300 font-bold">₹{amount} 💰</span>
                <span className="text-[#8696A0] text-xs">
                  {new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="px-4 pb-3">
            <div className="bg-[#2A3942] rounded-full px-4 py-2 flex items-center gap-2">
              <span className="text-[#8696A0] text-sm flex-1">Type a message</span>
              <div className="w-8 h-8 bg-[#00A884] rounded-full flex items-center justify-center">
                <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
