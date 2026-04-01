"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

const PLATFORMS = [
  { id: "zomato", name: "Zomato", color: "bg-red-600", icon: "🔴" },
  { id: "swiggy", name: "Swiggy", color: "bg-orange-500", icon: "🟠" },
  { id: "zepto", name: "Zepto", color: "bg-purple-600", icon: "🟣" },
  { id: "amazon", name: "Amazon", color: "bg-blue-600", icon: "🔵" },
];

export default function OnboardPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [name, setName] = useState("");
  const [platform, setPlatform] = useState("");
  const [location, setLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [gridInfo, setGridInfo] = useState<{ label: string; grid: Record<string, unknown> | null } | null>(null);
  const [platformId, setPlatformId] = useState("");
  const [linkResult, setLinkResult] = useState<{ message: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [detectingLocation, setDetectingLocation] = useState(false);
  const [error, setError] = useState("");
  const [manualLat, setManualLat] = useState("");
  const [manualLng, setManualLng] = useState("");

  const resolveLocation = async (coords: { lat: number; lng: number }) => {
    setLocation(coords);
    try {
      const grid = await api<{ label: string; grid: Record<string, unknown> | null }>(
        `/microgrids/lookup?lat=${coords.lat}&lng=${coords.lng}`
      );
      setGridInfo(grid);
    } catch {
      setGridInfo({
        label: "Location detected. Regional risk mapping is temporarily unavailable.",
        grid: null,
      });
    }
  };

  // Step 1: Name + Platform
  const handleStep1 = () => {
    if (!name.trim() || !platform) {
      setError("Please enter your name and select a platform");
      return;
    }
    setError("");
    setStep(2);
  };

  // Step 2: Location Detection
  const handleDetectLocation = () => {
    setDetectingLocation(true);
    setError("");

    if (!window.isSecureContext) {
      setError("Location requires HTTPS (or localhost). Open this app on https:// or http://localhost.");
      setDetectingLocation(false);
      return;
    }

    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        async (pos) => {
          const coords = { lat: pos.coords.latitude, lng: pos.coords.longitude };
          await resolveLocation(coords);
          setDetectingLocation(false);
        },
        (geoError) => {
          if (geoError.code === 1) {
            setError("Location permission denied. Allow location in browser settings, then retry.");
          } else if (geoError.code === 2) {
            setError("Unable to detect your location. Check GPS/network and retry.");
          } else if (geoError.code === 3) {
            setError("Location request timed out. Move to open sky or use manual coordinates.");
          } else {
            setError("Location detection failed. Try again or enter coordinates manually.");
          }
          setDetectingLocation(false);
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
      );
    } else {
      setError("Geolocation is unavailable. Enter coordinates manually.");
      setDetectingLocation(false);
    }
  };

  const handleManualLocation = async () => {
    const lat = Number(manualLat);
    const lng = Number(manualLng);
    if (Number.isNaN(lat) || Number.isNaN(lng) || lat < -90 || lat > 90 || lng < -180 || lng > 180) {
      setError("Enter valid latitude and longitude");
      return;
    }
    setError("");
    setDetectingLocation(true);
    await resolveLocation({ lat, lng });
    setDetectingLocation(false);
  };

  // Step 3: Platform Linking
  const handleLinkPlatform = async () => {
    if (!platformId.trim()) {
      setError("Enter your platform ID");
      return;
    }
    setLoading(true);
    setError("");

    // Simulate 2s delay then register
    await new Promise((r) => setTimeout(r, 2000));

    try {
      const email = localStorage.getItem("auth_email") || "demo@incometrix.ai";

      const res = await api<{ worker: { id: string }; grid: Record<string, unknown> }>(
        "/workers/register",
        {
          method: "POST",
          body: {
            email,
            name,
            phone: null,
            platform,
            zone_lat: location?.lat || 12.9352,
            zone_lng: location?.lng || 77.6245,
            city: String((gridInfo?.grid as Record<string, unknown> | undefined)?.city || ""),
          },
        }
      );

      if (res.worker) {
        localStorage.setItem("worker_id", res.worker.id);
        // Link platform
        const linkRes = await api<{ message: string }>("/workers/link-platform", {
          method: "POST",
          body: {
            worker_id: res.worker.id,
            platform_worker_id: platformId,
          },
        });
        setLinkResult(linkRes);

        setTimeout(() => {
          router.push("/dashboard/policy");
        }, 1500);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Registration failed");
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-8">
      {/* Progress Bar */}
      <div className="w-full max-w-sm mb-8">
        <div className="flex items-center justify-between mb-2">
          {[1, 2, 3].map((s) => (
            <div key={s} className="flex items-center">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all duration-300 ${
                  s <= step
                    ? "bg-amber-500 text-slate-900"
                    : "bg-slate-700 text-slate-400"
                }`}
              >
                {s < step ? "✓" : s}
              </div>
              {s < 3 && (
                <div
                  className={`w-16 sm:w-24 h-1 mx-1 rounded-full transition-all duration-300 ${
                    s < step ? "bg-amber-500" : "bg-slate-700"
                  }`}
                />
              )}
            </div>
          ))}
        </div>
        <div className="flex justify-between text-xs text-slate-400">
          <span>Profile</span>
          <span>Location</span>
          <span>Platform</span>
        </div>
      </div>

      <div className="glass-card w-full max-w-sm p-6">
        {/* STEP 1 */}
        {step === 1 && (
          <div className="fade-in-up">
            <h2 className="text-xl font-bold text-white mb-1">Let&apos;s get started! 🚀</h2>
            <p className="text-slate-400 text-sm mb-6">Tell us about yourself</p>

            <label className="text-sm text-slate-400 mb-1 block">Your Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter your name"
              className="input-field mb-4"
              id="name-input"
            />

            <label className="text-sm text-slate-400 mb-2 block">Delivery Platform</label>
            <div className="grid grid-cols-2 gap-3 mb-6">
              {PLATFORMS.map((p) => (
                <button
                  key={p.id}
                  onClick={() => setPlatform(p.id)}
                  className={`p-4 rounded-xl border-2 transition-all duration-200 text-center ${
                    platform === p.id
                      ? "border-amber-500 bg-amber-500/10"
                      : "border-slate-600 bg-slate-800/50 hover:border-slate-500"
                  }`}
                  id={`platform-${p.id}`}
                >
                  <span className="text-2xl block mb-1">{p.icon}</span>
                  <span className="text-sm font-medium text-white">{p.name}</span>
                </button>
              ))}
            </div>

            {error && <p className="text-red-400 text-sm mb-3">{error}</p>}

            <button onClick={handleStep1} className="btn-primary w-full" id="step1-continue">
              Continue →
            </button>
          </div>
        )}

        {/* STEP 2 */}
        {step === 2 && (
          <div className="fade-in-up">
            <h2 className="text-xl font-bold text-white mb-1">Detect Your Zone 📍</h2>
            <p className="text-slate-400 text-sm mb-6">We map your area to a 1km² risk microgrid</p>

            {!gridInfo ? (
              <div className="space-y-3 mb-4">
                <button
                  onClick={handleDetectLocation}
                  disabled={detectingLocation}
                  className="btn-primary w-full flex items-center justify-center gap-2"
                  id="detect-location-btn"
                >
                  {detectingLocation ? (
                    <>
                      <div className="w-5 h-5 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
                      Detecting...
                    </>
                  ) : (
                    <>📍 Use My Location</>
                  )}
                </button>

                <p className="text-xs text-slate-400 text-center">or enter coordinates manually</p>

                <div className="grid grid-cols-2 gap-3">
                  <input
                    type="number"
                    step="0.0001"
                    value={manualLat}
                    onChange={(e) => setManualLat(e.target.value)}
                    placeholder="Latitude"
                    className="input-field"
                  />
                  <input
                    type="number"
                    step="0.0001"
                    value={manualLng}
                    onChange={(e) => setManualLng(e.target.value)}
                    placeholder="Longitude"
                    className="input-field"
                  />
                </div>

                <button
                  onClick={handleManualLocation}
                  disabled={detectingLocation || !manualLat || !manualLng}
                  className="btn-secondary w-full"
                >
                  Use Entered Coordinates
                </button>
              </div>
            ) : (
              <div className="space-y-4 mb-6">
                <div className="bg-slate-800/80 rounded-xl p-4 border border-emerald-500/30 glow-green">
                  <p className="text-emerald-400 font-semibold text-sm">📍 Location Detected</p>
                  <p className="text-white font-medium mt-1">{gridInfo.label}</p>
                  <p className="text-slate-400 text-xs mt-2">
                    Lat: {location?.lat.toFixed(4)}, Lng: {location?.lng.toFixed(4)}
                  </p>
                </div>

                {gridInfo.grid && (
                  <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-600">
                    <p className="text-sm text-slate-400 mb-2">Zone Risk Factors</p>
                    <div className="space-y-2">
                      {[
                        { label: "Flood Risk", value: (gridInfo.grid as Record<string, number>).flood_risk },
                        { label: "Composite Risk", value: (gridInfo.grid as Record<string, number>).composite_risk },
                      ].filter(r => r.value !== undefined).map((r) => (
                        <div key={r.label} className="flex items-center justify-between">
                          <span className="text-sm text-slate-300">{r.label}</span>
                          <div className="flex items-center gap-2">
                            <div className="w-20 h-2 bg-slate-700 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full ${
                                  (r.value || 0) > 0.6 ? "bg-red-500" : (r.value || 0) > 0.35 ? "bg-yellow-500" : "bg-green-500"
                                }`}
                                style={{ width: `${(r.value || 0) * 100}%` }}
                              />
                            </div>
                            <span className="text-xs text-slate-400">{((r.value || 0) * 100).toFixed(0)}%</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className="flex gap-3">
              <button onClick={() => setStep(1)} className="btn-secondary flex-1">← Back</button>
              <button
                onClick={() => setStep(3)}
                disabled={!gridInfo}
                className="btn-primary flex-1"
                id="step2-continue"
              >
                Continue →
              </button>
            </div>
          </div>
        )}

        {/* STEP 3 */}
        {step === 3 && (
          <div className="fade-in-up">
            <h2 className="text-xl font-bold text-white mb-1">Link Your Platform 🔗</h2>
            <p className="text-slate-400 text-sm mb-6">
              Enter your {PLATFORMS.find((p) => p.id === platform)?.name || "delivery"} Partner ID
            </p>

            <input
              type="text"
              value={platformId}
              onChange={(e) => setPlatformId(e.target.value)}
              placeholder={`Enter your ${platform.charAt(0).toUpperCase() + platform.slice(1)} ID`}
              className="input-field mb-4"
              id="platform-id-input"
            />

            {error && <p className="text-red-400 text-sm mb-3">{error}</p>}

            {linkResult ? (
              <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4 mb-4 glow-green">
                <p className="text-emerald-400 font-semibold">{linkResult.message}</p>
                <p className="text-slate-400 text-sm mt-1">Redirecting to plan selection...</p>
              </div>
            ) : (
              <button
                onClick={handleLinkPlatform}
                disabled={loading || !platformId.trim()}
                className="btn-primary w-full flex items-center justify-center gap-2 mb-3"
                id="link-platform-btn"
              >
                {loading ? (
                  <>
                    <div className="w-5 h-5 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
                    Verifying...
                  </>
                ) : (
                  <>🔗 Link Account</>
                )}
              </button>
            )}

            <button onClick={() => setStep(2)} className="btn-secondary w-full">
              ← Back
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
