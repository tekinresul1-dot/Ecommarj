"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Check, Zap, Building2, Rocket, AlertTriangle, Mail } from "lucide-react";
import clsx from "clsx";
import { api } from "@/lib/api";

interface Plan {
    id: number;
    name: string;
    price: string;
    interval: string;
    plan_tier: string;
    order_limit: number;
    store_limit: number;
    yearly_total: string | null;
}

const FEATURES: Record<string, string[]> = {
    starter: [
        "1 Mağaza bağlantısı",
        "Dashboard & Genel Bakış",
        "Sipariş Analizi",
        "Ürün Analizi",
        "Kategori Analizi",
        "İade Zarar Analizi",
    ],
    business: [
        "2 Mağaza bağlantısı",
        "Starter'ın tüm özellikleri",
        "Reklam Analizi",
        "Hakediş Kontrolü",
        "Öncelikli destek",
    ],
    enterprise: [
        "5 Mağaza bağlantısı",
        "Business'ın tüm özellikleri",
        "Özel destek hattı",
        "API erişimi",
    ],
};

const TIER_COLORS: Record<string, string> = {
    starter:    "border-orange-500/40 hover:border-orange-500/70",
    business:   "border-blue-500/60 hover:border-blue-500/90 ring-1 ring-blue-500/30",
    enterprise: "border-purple-500/40 hover:border-purple-500/70",
};

const TIER_BTN: Record<string, string> = {
    starter:    "bg-orange-500 hover:bg-orange-600",
    business:   "bg-blue-600 hover:bg-blue-500",
    enterprise: "bg-purple-600 hover:bg-purple-500",
};

const TIER_ICON: Record<string, React.ReactNode> = {
    starter:    <Zap size={20} className="text-orange-400" />,
    business:   <Building2 size={20} className="text-blue-400" />,
    enterprise: <Rocket size={20} className="text-purple-400" />,
};

const TIER_DESC: Record<string, string> = {
    starter:    "Yeni başlayan Trendyol satıcıları için",
    business:   "Büyüyen e-ticaret işletmeleri için",
    enterprise: "Yüksek hacimli satıcılar için",
};

export default function SubscriptionPage() {
    const router = useRouter();
    const [plans, setPlans] = useState<Plan[]>([]);
    const [billing, setBilling] = useState<"monthly" | "yearly">("monthly");
    const [loading, setLoading] = useState(true);
    const [paying, setPaying] = useState<number | null>(null);
    const [paytrToken, setPaytrToken] = useState<string | null>(null);
    const [error, setError] = useState("");

    useEffect(() => {
        api.get("/subscription/plans/")
            .then((data: any) => setPlans(Array.isArray(data) ? data : []))
            .catch(() => {})
            .finally(() => setLoading(false));
    }, []);

    const tiers = ["starter", "business", "enterprise"];
    const filtered = plans.filter((p) => p.interval === billing);

    const handleSubscribe = async (planId: number) => {
        setPaying(planId);
        setError("");
        try {
            const res: any = await api.post("/payments/initiate/", { plan_id: planId });
            setPaytrToken(res.token);
        } catch (e: any) {
            setError(e?.message || "Ödeme başlatılamadı. Lütfen tekrar deneyin.");
        } finally {
            setPaying(null);
        }
    };

    if (paytrToken) {
        return (
            <div className="min-h-screen bg-[#070B14] flex flex-col items-center justify-center p-6">
                <div className="w-full max-w-lg rounded-2xl border border-white/10 bg-slate-900/60 p-6">
                    <h2 className="text-white font-bold text-lg mb-4 text-center">Güvenli Ödeme</h2>
                    <iframe
                        src={`https://www.paytr.com/odeme/guvenli/${paytrToken}`}
                        className="w-full rounded-xl border border-white/10"
                        style={{ height: 500 }}
                        frameBorder="0"
                        scrolling="no"
                    />
                    <button
                        onClick={() => setPaytrToken(null)}
                        className="mt-4 w-full py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm border border-slate-700 transition-colors"
                    >
                        Geri Dön
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#070B14] py-12 px-4">
            <div className="max-w-5xl mx-auto">
                <div className="text-center mb-10">
                    <h1 className="text-3xl font-bold text-white mb-2">Abonelik Planları</h1>
                    <p className="text-slate-400 text-sm">İşletmenizin büyüklüğüne uygun planı seçin</p>
                    <div className="inline-flex items-center gap-1 mt-6 p-1 rounded-xl bg-slate-800/80 border border-slate-700">
                        <button
                            onClick={() => setBilling("monthly")}
                            className={clsx("px-5 py-2 rounded-lg text-sm font-medium transition-colors",
                                billing === "monthly" ? "bg-slate-600 text-white" : "text-slate-400 hover:text-white")}
                        >Aylık</button>
                        <button
                            onClick={() => setBilling("yearly")}
                            className={clsx("px-5 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2",
                                billing === "yearly" ? "bg-slate-600 text-white" : "text-slate-400 hover:text-white")}
                        >
                            Yıllık
                            <span className="text-[10px] font-bold bg-green-500/20 text-green-400 px-1.5 py-0.5 rounded border border-green-500/30">%20 İndirim</span>
                        </button>
                    </div>
                </div>

                {error && (
                    <div className="mb-6 flex items-center gap-2 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                        <AlertTriangle size={16} />{error}
                    </div>
                )}

                {loading ? (
                    <div className="flex justify-center py-20">
                        <div className="w-8 h-8 rounded-full border-4 border-blue-500 border-t-transparent animate-spin" />
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
                        {tiers.map((tier) => {
                            const plan = filtered.find((p) => p.plan_tier === tier);
                            if (!plan) return null;
                            const isPopular = tier === "business";
                            return (
                                <div key={tier} className={clsx(
                                    "relative rounded-2xl border bg-slate-900/60 p-6 flex flex-col transition-all duration-200",
                                    TIER_COLORS[tier], isPopular && "scale-[1.02]"
                                )}>
                                    {isPopular && (
                                        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                                            <span className="px-3 py-1 text-xs font-bold bg-blue-600 text-white rounded-full shadow">En Popüler</span>
                                        </div>
                                    )}
                                    <div className="flex items-center gap-2 mb-3">
                                        {TIER_ICON[tier]}
                                        <span className="text-xs font-semibold px-2 py-0.5 rounded bg-white/5 border border-white/10 text-slate-300">
                                            {plan.order_limit.toLocaleString("tr-TR")} Sipariş
                                        </span>
                                    </div>
                                    <h3 className="text-xl font-bold text-white mb-1 capitalize">{tier.charAt(0).toUpperCase() + tier.slice(1)}</h3>
                                    <p className="text-xs text-slate-500 mb-4">{TIER_DESC[tier]}</p>
                                    <div className="mb-1">
                                        <span className="text-3xl font-bold text-white">₺{parseInt(plan.price).toLocaleString("tr-TR")}</span>
                                        <span className="text-slate-400 text-sm">/ay</span>
                                    </div>
                                    <p className="text-xs text-slate-500 mb-5 min-h-[16px]">
                                        {plan.yearly_total ? `* Yıllık ₺${parseInt(plan.yearly_total).toLocaleString("tr-TR")} ödeme alınır` : ""}
                                    </p>
                                    <ul className="space-y-2 mb-6 flex-1">
                                        {(FEATURES[tier] || []).map((f) => (
                                            <li key={f} className="flex items-start gap-2 text-sm text-slate-300">
                                                <Check size={14} className="text-green-400 mt-0.5 shrink-0" />{f}
                                            </li>
                                        ))}
                                    </ul>
                                    <button
                                        onClick={() => handleSubscribe(plan.id)}
                                        disabled={paying === plan.id}
                                        className={clsx("w-full py-2.5 rounded-xl text-white font-semibold text-sm transition-colors", TIER_BTN[tier], paying === plan.id && "opacity-60 cursor-wait")}
                                    >
                                        {paying === plan.id ? "İşleniyor..." : "Başla"}
                                    </button>
                                </div>
                            );
                        })}
                    </div>
                )}

                <div className="mt-10 text-center">
                    <p className="text-slate-500 text-sm mb-2">Sorularınız için</p>
                    <a href="mailto:destek@ecommarj.com" className="inline-flex items-center gap-2 text-slate-300 hover:text-white text-sm transition-colors">
                        <Mail size={14} />destek@ecommarj.com
                    </a>
                </div>
            </div>
        </div>
    );
}
