import type { Metadata } from "next";
import { BarChart3, ShoppingCart, Calculator, Layers, TrendingUp, Shield } from "lucide-react";

export const metadata: Metadata = {
    title: "Özellikler — EcomMarj",
    description: "EcomMarj'ın tüm özelliklerini keşfedin. Karlılık analizi, sipariş takibi, maliyet yönetimi ve daha fazlası.",
};

const features = [
    {
        icon: BarChart3,
        title: "Gerçek Zamanlı Karlılık Analizi",
        description: "Her ürün ve siparişin gerçek kârlılığını komisyon, kargo, iade ve KDV dahil otomatik hesaplayın. Zarar eden ürünleri anında tespit edin.",
    },
    {
        icon: ShoppingCart,
        title: "Sipariş Bazlı Analiz",
        description: "Her siparişin brüt gelir, komisyon, kargo maliyeti, iade durumu ve net kâr/zarar dökümünü detaylı olarak görüntüleyin.",
    },
    {
        icon: Calculator,
        title: "Maliyet Yönetimi",
        description: "Ürün maliyetlerinizi tek tek veya Excel ile toplu olarak girin. KDV oranları, desi ağırlıkları ve kargo tarifelerini otomatik hesaplayın.",
    },
    {
        icon: Layers,
        title: "Kategori ve Ürün Karşılaştırma",
        description: "Kategori bazlı karlılık analizleri yapın, en çok kazandıran ve zarar ettiren ürün gruplarını karşılaştırın.",
    },
    {
        icon: TrendingUp,
        title: "Büyüme ve Trend Takibi",
        description: "Aylık, haftalık ve günlük ciro trendlerinizi takip edin. Büyüme oranlarını ve hedef gerçekleşme durumunuzu analiz edin.",
    },
    {
        icon: Shield,
        title: "Güvenli API Entegrasyonu",
        description: "API bilgileriniz 256-bit şifreleme ile korunur. KVKK uyumlu veri saklama ve güvenli bağlantı altyapısı.",
    },
];

export default function FeaturesPage() {
    return (
        <div className="pt-28 pb-20">
            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center mb-16">
                    <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4">
                        Güçlü <span className="gradient-text">Özellikler</span>
                    </h1>
                    <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                        E-ticaret karlılığınızı gerçek zamanlı takip etmek için ihtiyacınız olan her şey tek platformda.
                    </p>
                </div>

                <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
                    {features.map((feature) => (
                        <div
                            key={feature.title}
                            className="glass-card rounded-2xl p-8 hover:border-accent-400/20 transition-all duration-300 group"
                        >
                            <div className="w-12 h-12 rounded-xl bg-accent-500/10 border border-accent-500/20 flex items-center justify-center mb-5 group-hover:scale-110 transition-transform">
                                <feature.icon className="w-6 h-6 text-accent-400" />
                            </div>
                            <h3 className="text-xl font-semibold text-white mb-3">{feature.title}</h3>
                            <p className="text-slate-400 leading-relaxed">{feature.description}</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
