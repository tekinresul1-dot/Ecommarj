"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertTriangle, X } from "lucide-react";
import { api } from "@/lib/api";

interface CostStatus {
    has_costs: boolean;
    has_marketplace_account: boolean;
    total_products: number;
    products_with_cost: number;
    products_without_cost: number;
}

const DISMISS_KEY = "cost_reminder_dismissed";
const DISMISS_DURATION_MS = 24 * 60 * 60 * 1000; // 24 saat

function isDismissed(): boolean {
    try {
        const raw = localStorage.getItem(DISMISS_KEY);
        if (!raw) return false;
        const ts = parseInt(raw, 10);
        return Date.now() - ts < DISMISS_DURATION_MS;
    } catch {
        return false;
    }
}

export default function GlobalCostPopup() {
    const router = useRouter();
    const [status, setStatus] = useState<CostStatus | null>(null);
    const [visible, setVisible] = useState(false);

    useEffect(() => {
        if (isDismissed()) return;

        api.get("/user/product-cost-status/")
            .then((data: CostStatus) => {
                if (!data.has_costs && data.has_marketplace_account && data.total_products > 0) {
                    setStatus(data);
                    setVisible(true);
                }
            })
            .catch(() => {});
    }, []);

    if (!visible || !status) return null;

    const handleDismiss = () => {
        try {
            localStorage.setItem(DISMISS_KEY, Date.now().toString());
        } catch {}
        setVisible(false);
    };

    const handleGoProducts = () => {
        setVisible(false);
        router.push("/products");
    };

    return (
        <div className="fixed inset-0 z-[200] flex items-center justify-center p-4">
            {/* Overlay */}
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                onClick={handleDismiss}
            />

            {/* Card */}
            <div className="relative z-10 w-full max-w-md rounded-2xl border border-orange-500/30 bg-[#0d1117] shadow-2xl shadow-orange-500/10 p-6">
                {/* Close */}
                <button
                    onClick={handleDismiss}
                    className="absolute top-4 right-4 text-slate-500 hover:text-slate-300 transition-colors"
                >
                    <X size={18} />
                </button>

                {/* Icon */}
                <div className="flex items-center justify-center w-14 h-14 rounded-full bg-orange-500/15 border border-orange-500/30 mb-5 mx-auto">
                    <AlertTriangle size={26} className="text-orange-400" />
                </div>

                {/* Title */}
                <h2 className="text-lg font-semibold text-white text-center mb-2">
                    Ürün Maliyetlerinizi Girin
                </h2>

                {/* Description */}
                <p className="text-sm text-slate-400 text-center leading-relaxed mb-6">
                    Karlılık analizleri için{" "}
                    <span className="text-orange-400 font-semibold">
                        {status.products_without_cost} ürününüzün
                    </span>{" "}
                    maliyetini girmeniz gerekiyor. Maliyet girilmeden karlılık hesaplanamaz.
                </p>

                {/* Buttons */}
                <div className="flex flex-col gap-2">
                    <button
                        onClick={handleGoProducts}
                        className="w-full py-2.5 rounded-lg bg-orange-500 hover:bg-orange-600 text-white font-semibold text-sm transition-colors"
                    >
                        Şimdi Gir
                    </button>
                    <button
                        onClick={handleDismiss}
                        className="w-full py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-sm transition-colors border border-slate-700"
                    >
                        Daha Sonra
                    </button>
                </div>
            </div>
        </div>
    );
}
