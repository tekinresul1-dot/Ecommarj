"use client";

import { useState } from "react";
import { api } from "@/lib/api";

export default function OnboardingWizard({ onComplete }: { onComplete: () => void }) {
    const [step, setStep] = useState(1);
    const [supplierId, setSupplierId] = useState("");
    const [apiKey, setApiKey] = useState("");
    const [apiSecret, setApiSecret] = useState("");

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

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

            setStep(3);
            setTimeout(() => {
                onComplete();
            }, 3000);
        } catch (err: any) {
            setError(err.message || "Kaydetme sırasında hata oluştu.");
            setLoading(false);
        }
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="w-full max-w-lg bg-surface border border-white/10 rounded-2xl p-8 shadow-2xl">
                {step === 1 && (
                    <>
                        <h2 className="text-2xl font-bold text-white mb-2">Pazaryerinizi Bağlayın</h2>
                        <p className="text-white/60 mb-6 text-sm">
                            Kârlılığınızı hesaplamak için Trendyol API bilgilerinizi girin.
                            Verileriniz şifrelenerek saklanır.
                        </p>

                        <div className="space-y-4 mb-6">
                            <div>
                                <label className="block text-sm text-white/80 mb-1">Satıcı ID (Supplier ID)</label>
                                <input
                                    type="text"
                                    className="w-full h-11 bg-white/5 border border-white/10 rounded-lg px-4 text-white"
                                    value={supplierId}
                                    onChange={e => setSupplierId(e.target.value)}
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-white/80 mb-1">API Key</label>
                                <input
                                    type="text"
                                    className="w-full h-11 bg-white/5 border border-white/10 rounded-lg px-4 text-white"
                                    value={apiKey}
                                    onChange={e => setApiKey(e.target.value)}
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-white/80 mb-1">API Secret</label>
                                <input
                                    type="password"
                                    className="w-full h-11 bg-white/5 border border-white/10 rounded-lg px-4 text-white"
                                    value={apiSecret}
                                    onChange={e => setApiSecret(e.target.value)}
                                />
                            </div>
                        </div>

                        {error && <p className="text-rose-400 text-sm mb-4">{error}</p>}

                        <button
                            onClick={handleTestConnection}
                            disabled={loading}
                            className="w-full h-11 bg-accent-500 hover:bg-accent-400 text-white rounded-lg font-medium"
                        >
                            {loading ? "Test Ediliyor..." : "Bağlantıyı Test Et"}
                        </button>
                    </>
                )}

                {step === 2 && (
                    <div className="text-center">
                        <div className="w-16 h-16 bg-emerald-500/20 text-emerald-400 rounded-full flex items-center justify-center mx-auto mb-4 border border-emerald-500/30">
                            <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                        </div>
                        <h2 className="text-2xl font-bold text-white mb-2">Bağlantı Başarılı!</h2>
                        <p className="text-white/60 mb-6 text-sm">
                            Trendyol mağazanızla iletişim kurabiliyoruz. Şimdi geçmiş siparişlerinizi ve ürünlerinizi çekmeye başlayabiliriz.
                        </p>

                        {error && <p className="text-rose-400 text-sm mb-4">{error}</p>}

                        <button
                            onClick={handleSaveAndSync}
                            disabled={loading}
                            className="w-full h-11 bg-accent-500 hover:bg-accent-400 text-white rounded-lg font-medium"
                        >
                            {loading ? "Kaydediliyor..." : "Verileri Çekmeye Başla"}
                        </button>
                    </div>
                )}

                {step === 3 && (
                    <div className="text-center">
                        <svg className="animate-spin w-12 h-12 text-accent-500 mx-auto mb-4" viewBox="0 0 24 24" fill="none">
                            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" className="opacity-25" />
                            <path d="M4 12a8 8 0 018-8" stroke="currentColor" strokeWidth="4" strokeLinecap="round" className="opacity-75" />
                        </svg>
                        <h2 className="text-xl font-bold text-white mb-2">Sihir Gerçekleşiyor...</h2>
                        <p className="text-white/60 text-sm">
                            Siparişleriniz arka planda kârlılık motorumuzdan geçiriliyor. Dashboard'a yönlendiriliyorsunuz.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}
