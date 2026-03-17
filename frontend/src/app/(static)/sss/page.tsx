import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Sıkça Sorulan Sorular — EcomMarj",
    description: "EcomMarj hakkında sıkça sorulan sorular ve cevapları.",
};

const faqs = [
    { q: "EcomMarj nedir?", a: "EcomMarj, Trendyol satıcılarının sipariş bazlı gerçek karlılığını hesaplayan bir analiz platformudur. Komisyon, kargo, iade ve tüm gizli maliyetleri otomatik olarak hesaplayarak net kâr/zarar durumunuzu gösterir." },
    { q: "EcomMarj ücretsiz mi?", a: "Evet, başlangıç planımız tamamen ücretsizdir. Tek bir Trendyol mağazasını bağlayarak karlılık analizine hemen başlayabilirsiniz." },
    { q: "Trendyol API bilgilerimi nasıl alırım?", a: "Trendyol Satıcı Paneli > Entegrasyon Bilgileri sayfasından API Key, API Secret ve Supplier ID bilgilerinizi alabilirsiniz. IP whitelist'e sunucu IP adresinizi eklemeniz gerekir." },
    { q: "Verilerim güvende mi?", a: "Evet. API Secret bilginiz 256-bit şifreleme ile saklanır, tüm bağlantılar SSL/TLS üzerinden yapılır ve KVKK uyumlu veri saklama politikamız mevcuttur." },
    { q: "Veri senkronizasyonu ne sıklıkla yapılır?", a: "Verileriniz gün içinde otomatik olarak senkronize edilir. Ayrıca dashboard üzerinden manuel senkronizasyon tetikleyebilirsiniz." },
    { q: "Maliyet bilgilerimi nasıl girerim?", a: "Ürün Ayarları sayfasından tek tek girebilir veya Excel dosyası ile toplu olarak yükleyebilirsiniz. KDV oranları ve desi ağırlıkları da girilebilir." },
    { q: "İade edilen siparişler karlılık hesabına etki eder mi?", a: "Evet. İade ve iptal edilen siparişler net ciro hesaplamasından düşülür ve ayrı bir iade analizi raporu sunulur." },
    { q: "Birden fazla mağazayı bağlayabilir miyim?", a: "Profesyonel ve üzeri planlarda birden fazla Trendyol mağazasını aynı hesaba bağlayarak merkezi analiz yapabilirsiniz." },
    { q: "Hepsiburada veya Amazon desteği var mı?", a: "Şu anda sadece Trendyol entegrasyonu aktiftir. Hepsiburada, Amazon ve N11 için çalışmalarımız devam etmektedir." },
    { q: "Hesabımı nasıl silerim?", a: "Destek ekibimize e-posta göndererek hesap silme talebinde bulunabilirsiniz. Verileriniz KVKK kapsamında tamamen silinir." },
];

export default function FaqPage() {
    return (
        <div className="pt-28 pb-20">
            <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center mb-16">
                    <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4">
                        Sıkça Sorulan <span className="gradient-text">Sorular</span>
                    </h1>
                </div>

                <div className="space-y-4">
                    {faqs.map((faq, i) => (
                        <details key={i} className="glass-card rounded-2xl group">
                            <summary className="px-6 py-5 cursor-pointer text-white font-medium flex items-center justify-between list-none">
                                {faq.q}
                                <span className="text-slate-500 group-open:rotate-45 transition-transform text-xl font-light">+</span>
                            </summary>
                            <div className="px-6 pb-5 text-sm text-slate-400 leading-relaxed -mt-1">
                                {faq.a}
                            </div>
                        </details>
                    ))}
                </div>
            </div>
        </div>
    );
}
