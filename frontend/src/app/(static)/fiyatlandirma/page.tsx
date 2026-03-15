import type { Metadata } from "next";
import Link from "next/link";
import { Check, Sparkles } from "lucide-react";

export const metadata: Metadata = {
    title: "Fiyatlandırma — EcomMarj",
    description: "EcomMarj fiyatlandırma planları. E-ticaret karlılık analizine hemen başlayın.",
};

const plans = [
    {
        name: "Başlangıç",
        price: "Ücretsiz",
        period: "",
        description: "Tek mağaza ile karlılık analizine başlayın.",
        features: [
            "1 Trendyol mağazası",
            "Son 3 aylık veri analizi",
            "Temel karlılık raporu",
            "Günlük veri senkronizasyonu",
            "E-posta desteği",
        ],
        cta: "Ücretsiz Başla",
        href: "/ucretsiz-basla",
        highlight: false,
    },
    {
        name: "Profesyonel",
        price: "Yakında",
        period: "",
        description: "Büyüyen mağazalar için gelişmiş analitik.",
        features: [
            "3 Trendyol mağazası",
            "12 aylık veri geçmişi",
            "Gelişmiş karlılık raporları",
            "Kategori ve ürün analizi",
            "Saatlik senkronizasyon",
            "Öncelikli destek",
            "Excel dışa aktarım",
        ],
        cta: "Bize Ulaşın",
        href: "/iletisim",
        highlight: true,
    },
    {
        name: "Kurumsal",
        price: "Özel Teklif",
        period: "",
        description: "Büyük ölçekli satıcılar ve ajanslar.",
        features: [
            "Sınırsız mağaza",
            "Sınırsız veri geçmişi",
            "API erişimi",
            "Özel entegrasyonlar",
            "Dedicated hesap yöneticisi",
            "SLA garantisi",
            "Özel raporlama",
        ],
        cta: "Demo Talep Edin",
        href: "/iletisim",
        highlight: false,
    },
];

export default function PricingPage() {
    return (
        <div className="pt-28 pb-20">
            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center mb-16">
                    <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4">
                        Şeffaf <span className="gradient-text">Fiyatlandırma</span>
                    </h1>
                    <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                        İhtiyacınıza uygun planı seçin. Ücretsiz başlayın, büyüdükçe ölçeklendirin.
                    </p>
                </div>

                <div className="grid gap-8 md:grid-cols-3 max-w-5xl mx-auto">
                    {plans.map((plan) => (
                        <div
                            key={plan.name}
                            className={`rounded-2xl p-8 flex flex-col ${plan.highlight
                                    ? "glass-card border-accent-400/30 relative overflow-hidden"
                                    : "glass-card"
                                }`}
                        >
                            {plan.highlight && (
                                <div className="absolute top-0 right-0 bg-gradient-to-l from-accent-500 to-electric-500 text-white text-xs font-semibold px-4 py-1.5 rounded-bl-xl flex items-center gap-1">
                                    <Sparkles className="w-3 h-3" /> Popüler
                                </div>
                            )}
                            <h3 className="text-xl font-semibold text-white mb-2">{plan.name}</h3>
                            <p className="text-sm text-slate-400 mb-6">{plan.description}</p>
                            <div className="mb-6">
                                <span className="text-3xl font-bold text-white">{plan.price}</span>
                                {plan.period && <span className="text-slate-400 ml-1">{plan.period}</span>}
                            </div>
                            <ul className="space-y-3 mb-8 flex-1">
                                {plan.features.map((f) => (
                                    <li key={f} className="flex items-start gap-2.5 text-sm text-slate-300">
                                        <Check className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                                        {f}
                                    </li>
                                ))}
                            </ul>
                            <Link
                                href={plan.href}
                                className={`block text-center py-3 px-6 rounded-xl font-medium transition-all ${plan.highlight
                                        ? "bg-gradient-to-r from-accent-500 to-electric-500 text-white hover:opacity-90 shadow-lg shadow-accent-500/20"
                                        : "glass-card text-white hover:border-accent-400/30"
                                    }`}
                            >
                                {plan.cta}
                            </Link>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
