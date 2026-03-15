import type { Metadata } from "next";
import { CheckCircle2, Clock } from "lucide-react";

export const metadata: Metadata = {
    title: "Entegrasyonlar — EcomMarj",
    description: "EcomMarj pazaryeri entegrasyonları. Trendyol ve yakında Hepsiburada, Amazon, N11 desteği.",
};

const integrations = [
    {
        name: "Trendyol",
        status: "active",
        description: "Ürünler, siparişler, komisyonlar ve finansal veriler otomatik senkronize edilir. Onaylı API entegrasyonu ile güvenli bağlantı.",
        features: ["Ürün senkronizasyonu", "Sipariş takibi", "Komisyon hesaplama", "İade/iptal analizi", "Kargo barem desteği"],
    },
    {
        name: "Hepsiburada",
        status: "coming",
        description: "Hepsiburada mağazanızın karlılık analizini tek merkezden yönetin.",
        features: ["Ürün senkronizasyonu", "Sipariş analizi", "Komisyon takibi"],
    },
    {
        name: "Amazon Türkiye",
        status: "coming",
        description: "Amazon Türkiye satışlarınızı ve karlılığınızı analiz edin.",
        features: ["SP-API entegrasyonu", "FBA maliyet analizi", "Sipariş takibi"],
    },
    {
        name: "N11",
        status: "coming",
        description: "N11 mağazanızı bağlayarak çoklu kanal karlılık analizi yapın.",
        features: ["Ürün senkronizasyonu", "Sipariş analizi", "Komisyon hesaplama"],
    },
];

export default function IntegrationsPage() {
    return (
        <div className="pt-28 pb-20">
            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center mb-16">
                    <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4">
                        Pazaryeri <span className="gradient-text">Entegrasyonları</span>
                    </h1>
                    <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                        Trendyol entegrasyonumuz aktif. Diğer pazaryerleri için çalışmalarımız devam ediyor.
                    </p>
                </div>

                <div className="grid gap-6 md:grid-cols-2">
                    {integrations.map((item) => (
                        <div key={item.name} className="glass-card rounded-2xl p-8 hover:border-accent-400/20 transition-all">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-xl font-semibold text-white">{item.name}</h3>
                                {item.status === "active" ? (
                                    <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-full">
                                        <CheckCircle2 className="w-3.5 h-3.5" /> Aktif
                                    </span>
                                ) : (
                                    <span className="flex items-center gap-1.5 text-xs font-medium text-amber-400 bg-amber-500/10 border border-amber-500/20 px-3 py-1 rounded-full">
                                        <Clock className="w-3.5 h-3.5" /> Yakında
                                    </span>
                                )}
                            </div>
                            <p className="text-slate-400 text-sm mb-5">{item.description}</p>
                            <ul className="space-y-2">
                                {item.features.map((f) => (
                                    <li key={f} className="flex items-center gap-2 text-sm text-slate-300">
                                        <div className="w-1.5 h-1.5 rounded-full bg-accent-400" />
                                        {f}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
