"use client";

import { useState, useRef, useEffect } from "react";
import { api } from "@/lib/api";

export default function OnboardingWizard({ 
    initialStatus = "WELCOME",
    onComplete 
}: { 
    initialStatus?: string;
    onComplete: () => void 
}) {
    // Map status to internal step number
    const statusToStep = (s: string) => {
        switch(s) {
            case "WELCOME": return 0;
            case "MARKETPLACE_CONNECT": return 1;
            case "SYNCING": return 2;
            case "COMPLETED": return 3;
            default: return 0;
        }
    };

    const [step, setStep] = useState(() => statusToStep(initialStatus));
    const [supplierId, setSupplierId] = useState("");
    const [apiKey, setApiKey] = useState("");
    const [apiSecret, setApiSecret] = useState("");

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

    useEffect(() => {
        return () => { if (pollRef.current) clearInterval(pollRef.current); };
    }, []);

    async function updateStatus(newStatus: string) {
        try {
            await api.patch("/auth/onboarding/status/", { status: newStatus });
        } catch (err) {
            console.error("Failed to update onboarding status", err);
        }
    }

    async function handleStart() {
        setLoading(true);
        await updateStatus("MARKETPLACE_CONNECT");
        setStep(1);
        setLoading(false);
    }

    async function handleTestConnection() {
        if (!supplierId || !apiKey || !apiSecret) {
            setError("Lütfen tüm alanları doldurun.");
            return;
        }

        setLoading(true);
        setError("");

        try {
            const res = await api.post("/integrations/trendyol/test-connection/", {
                supplier_id: supplierId,
                api_key: apiKey,
                api_secret: apiSecret
            });

            if (res.ok) {
                await updateStatus("SYNCING");
                setStep(2);
            } else {
                setError(res.message || "Bağlantı başarısız.");
            }
        } catch (err: any) {
            setError(err.message || "Bir hata oluştu.");
        } finally {
            setLoading(false);
        }
    }

    async function handleSaveAndSync() {
        setLoading(true);
        setError("");

        try {
            await api.post("/integrations/trendyol/save-credentials/", {
                supplier_id: supplierId,
                api_key: apiKey,
                api_secret: apiSecret,
                auto_sync: true
            });

            // Move to syncing screen immediately — don't block on the sync itself
            await updateStatus("SYNCING");
            setStep(3);
            setLoading(false);

            // Poll /dashboard/sync-status/ every 3s until data appears (max 90s)
            let attempts = 0;
            pollRef.current = setInterval(async () => {
                attempts++;
                try {
                    const status: any = await api.get("/dashboard/sync-status/");
                    const hasSyncData = status?.logs?.length > 0 || status?.sync_status === "ready";
                    if (hasSyncData) {
                        clearInterval(pollRef.current!);
                        await updateStatus("COMPLETED");
                        setTimeout(() => onComplete(), 2000);
                        return;
                    }
                } catch (_) { /* ignore polling errors */ }

                if (attempts >= 30) {
                    // 90s timeout — sync continues in background, move user forward
                    clearInterval(pollRef.current!);
                    await updateStatus("COMPLETED");
                    onComplete();
                }
            }, 3000);
        } catch (err: any) {
            setError(err.message || "Kaydetme sırasında hata oluştu.");
            setLoading(false);
        }
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#05080F]/80 backdrop-blur-md p-4 animate-in fade-in duration-500">
            <div className="w-full max-w-lg bg-[#0D121F] border border-white/10 rounded-[2rem] p-8 shadow-2xl relative overflow-hidden group">
                {/* Decorative background elements */}
                <div className="absolute -top-24 -right-24 w-48 h-48 bg-accent-500/10 blur-[80px] rounded-full group-hover:bg-accent-500/20 transition-colors duration-700"></div>
                <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-accent-500/5 blur-[80px] rounded-full group-hover:bg-accent-500/10 transition-colors duration-700"></div>

                <div className="relative z-10">
                    {step === 0 && (
                        <div className="text-center py-4">
                            <div className="w-20 h-20 bg-accent-500/10 rounded-3xl flex items-center justify-center mx-auto mb-6 border border-accent-500/20 shadow-inner group-hover:scale-110 transition-transform duration-500">
                                <span className="text-4xl text-white">👋</span>
                            </div>
                            <h2 className="text-3xl font-bold text-white mb-3 tracking-tight">EcomMarj&apos;a Hoş Geldiniz!</h2>
                            <p className="text-white/60 mb-8 leading-relaxed text-balance">
                                Satışlarınızı ve kârlılığınızı profesyonelce takip etmek için ilk adımı attınız. 
                                Şimdi mağazanızı bağlayarak verilerinizi analiz etmeye başlayalım.
                            </p>
                            <button
                                onClick={handleStart}
                                disabled={loading}
                                className="w-full h-14 bg-gradient-to-r from-accent-600 to-accent-500 hover:from-accent-500 hover:to-accent-400 text-white rounded-2xl font-semibold shadow-xl shadow-accent-500/20 transition-all active:scale-95 disabled:opacity-50"
                            >
                                {loading ? (
                                    <div className="flex items-center justify-center gap-2">
                                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                        <span>Hazırlanıyor...</span>
                                    </div>
                                ) : (
                                    "Hadi Başlayalım"
                                )}
                            </button>
                        </div>
                    )}

                    {step === 1 && (
                        <div className="animate-in slide-in-from-right-4 duration-500">
                            <h2 className="text-2xl font-bold text-white mb-2">Pazaryerinizi Bağlayın</h2>
                            <p className="text-white/60 mb-8 text-sm">
                                Kârlılığınızı hesaplamak için Trendyol API bilgilerinizi girin.
                                Verileriniz 256-bit şifrelenerek güvenle saklanır.
                            </p>

                            <div className="space-y-5 mb-8">
                                <div className="space-y-1.5">
                                    <label className="block text-xs font-semibold text-white/40 uppercase tracking-wider ml-1">Satıcı ID (Supplier ID)</label>
                                    <input
                                        type="text"
                                        className="w-full h-12 bg-white/5 border border-white/10 rounded-xl px-4 text-white placeholder:text-white/20 focus:border-accent-500/50 focus:bg-white/[0.08] transition-all outline-none"
                                        placeholder="Örn: 123456"
                                        value={supplierId}
                                        onChange={e => setSupplierId(e.target.value)}
                                    />
                                </div>
                                <div className="space-y-1.5">
                                    <label className="block text-xs font-semibold text-white/40 uppercase tracking-wider ml-1">API Key</label>
                                    <input
                                        type="text"
                                        className="w-full h-12 bg-white/5 border border-white/10 rounded-xl px-4 text-white placeholder:text-white/20 focus:border-accent-500/50 focus:bg-white/[0.08] transition-all outline-none"
                                        placeholder="Trendyol'dan aldığınız API Key"
                                        value={apiKey}
                                        onChange={e => setApiKey(e.target.value)}
                                    />
                                </div>
                                <div className="space-y-1.5">
                                    <label className="block text-xs font-semibold text-white/40 uppercase tracking-wider ml-1">API Secret</label>
                                    <input
                                        type="password"
                                        className="w-full h-12 bg-white/5 border border-white/10 rounded-xl px-4 text-white placeholder:text-white/20 focus:border-accent-500/50 focus:bg-white/[0.08] transition-all outline-none"
                                        placeholder="••••••••••••"
                                        value={apiSecret}
                                        onChange={e => setApiSecret(e.target.value)}
                                    />
                                </div>
                            </div>

                            {error && (
                                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm mb-6 flex items-center gap-3">
                                    <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                    {error}
                                </div>
                            )}

                            <button
                                onClick={handleTestConnection}
                                disabled={loading}
                                className="w-full h-12 bg-accent-500 hover:bg-accent-400 text-white rounded-xl font-medium transition-all shadow-lg shadow-accent-500/10 active:scale-95 disabled:opacity-50"
                            >
                                {loading ? (
                                    <div className="flex items-center justify-center gap-2">
                                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                        <span>Test Ediliyor...</span>
                                    </div>
                                ) : (
                                    "Bağlantıyı Test Et"
                                )}
                            </button>
                        </div>
                    )}

                    {step === 2 && (
                        <div className="text-center py-4 animate-in zoom-in-95 duration-500">
                            <div className="w-20 h-20 bg-emerald-500/10 text-emerald-400 rounded-3xl flex items-center justify-center mx-auto mb-6 border border-emerald-500/20 shadow-inner">
                                <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                                </svg>
                            </div>
                            <h2 className="text-3xl font-bold text-white mb-3">Bağlantı Başarılı!</h2>
                            <p className="text-white/60 mb-8 leading-relaxed">
                                Trendyol mağazanızla iletişim kurabiliyoruz. <br/>
                                Şimdi geçmiş verilerinizi çekmeye başlayabiliriz.
                            </p>

                            {error && <p className="text-rose-400 text-sm mb-4">{error}</p>}

                            <button
                                onClick={handleSaveAndSync}
                                disabled={loading}
                                className="w-full h-14 bg-emerald-500 hover:bg-emerald-400 text-white rounded-2xl font-bold transition-all shadow-xl shadow-emerald-500/20 active:scale-95 disabled:opacity-50"
                            >
                                {loading ? (
                                    <div className="flex items-center justify-center gap-2">
                                        <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                                        <span>Kaydediliyor...</span>
                                    </div>
                                ) : (
                                    "Verileri Çekmeye Başla"
                                )}
                            </button>
                        </div>
                    )}

                    {step === 3 && (
                        <div className="text-center py-8 animate-in fade-in duration-1000">
                            <div className="relative w-24 h-24 mx-auto mb-8">
                                <div className="absolute inset-0 rounded-full border-[6px] border-accent-500/10"></div>
                                <div className="absolute inset-0 rounded-full border-[6px] border-t-accent-500 animate-spin"></div>
                                <div className="absolute inset-4 rounded-full bg-accent-500/5 animate-pulse"></div>
                            </div>
                            <h2 className="text-2xl font-bold text-white mb-3">Veriler Çekiliyor...</h2>
                            <p className="text-white/60 text-base leading-relaxed">
                                Ürünleriniz ve siparişleriniz arka planda <br/>
                                senkronize ediliyor. Bu birkaç dakika sürebilir.
                            </p>
                            <div className="mt-8 flex justify-center gap-1.5">
                                <div className="w-2 h-2 rounded-full bg-accent-500 animate-bounce [animation-delay:-0.3s]"></div>
                                <div className="w-2 h-2 rounded-full bg-accent-500 animate-bounce [animation-delay:-0.15s]"></div>
                                <div className="w-2 h-2 rounded-full bg-accent-500 animate-bounce"></div>
                            </div>
                            <p className="text-white/30 text-xs mt-6">Sizi otomatik olarak yönlendireceğiz...</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
