"use client";

import { useState } from "react";
import { BookOpen, Plug, Settings, BarChart3, HelpCircle, CreditCard, ChevronDown } from "lucide-react";

const categories = [
    {
        icon: Settings,
        title: "Hesap ve Başlangıç",
        desc: "Kayıt, giriş, profil ayarları ve hesap yönetimi.",
        articles: [
            { q: "Nasıl hesap oluşturabilirim?", a: "Ana sayfadan \"Ücretsiz Başla\" butonuna tıklayıp ad, e-posta ve şifre bilgilerinizi girerek 30 saniyede hesap oluşturabilirsiniz." },
            { q: "Şifremi unuttum, ne yapmalıyım?", a: "Giriş sayfasındaki \"Şifremi Unuttum\" bağlantısına tıklayarak e-posta adresinize sıfırlama bağlantısı gönderilmesini sağlayabilirsiniz." },
            { q: "Profil bilgilerimi nasıl güncellerim?", a: "Dashboard → Ayarlar sayfasından ad, e-posta ve şirket bilgilerinizi güncelleyebilirsiniz." },
        ],
    },
    {
        icon: Plug,
        title: "Trendyol Entegrasyonu",
        desc: "API bağlantısı, IP whitelist, senkronizasyon sorunları.",
        articles: [
            { q: "API Key ve Secret nereden bulunur?", a: "Trendyol Satıcı Paneli → Entegrasyon → Entegrasyon Bilgileri sayfasından API Key ve API Secret bilgilerinizi kopyalayabilirsiniz." },
            { q: "IP Whitelist ayarı nasıl yapılır?", a: "Trendyol Satıcı Paneli → Entegrasyon → IP Whitelist bölümünde 91.98.226.158 IP adresini ekleyin." },
            { q: "Bağlantı testi neden başarısız oluyor?", a: "Genellikle IP whitelist eksikliği veya hatalı API bilgileri nedeniyle olur. Bilgilerinizi kontrol edip tekrar deneyin." },
            { q: "Veri senkronizasyonu ne kadar sürer?", a: "İlk bağlantıda geçmiş verilerin çekilmesi birkaç dakika sürebilir. Sonrasında veriler otomatik olarak güncellenir." },
        ],
    },
    {
        icon: BarChart3,
        title: "Dashboard ve Raporlar",
        desc: "Karlılık analizi, filtreleme, veri okuma rehberi.",
        articles: [
            { q: "KPI kartlarındaki veriler ne anlama gelir?", a: "Ciro: toplam satış tutarı. Kâr: tüm maliyetler düşüldükten sonraki net kazanç. Marj: kârın ciroya oranı. Sipariş: dönemdeki toplam sipariş adedi." },
            { q: "Tarih filtresi nasıl kullanılır?", a: "Dashboard üstündeki tarih seçiciden günlük, haftalık, aylık veya özel tarih aralığı seçebilirsiniz." },
            { q: "Grafikleri nasıl yorumlamalıyım?", a: "Trend grafikleri cirodaki yükseliş/düşüş eğilimini gösterir. Kırmızı çizgi zarar noktasını, yeşil alan kârlı bölgeyi temsil eder." },
        ],
    },
    {
        icon: CreditCard,
        title: "Maliyet Yönetimi",
        desc: "Ürün maliyeti girişi, Excel aktarım, KDV hesaplama.",
        articles: [
            { q: "Ürün maliyeti neden önemli?", a: "Maliyet girilmeden doğru karlılık hesaplaması yapılamaz. EcomMarj, her ürünün alış fiyatını bilmeden yalnızca ciro gösterebilir." },
            { q: "Excel ile toplu yükleme nasıl yapılır?", a: "Ürün Ayarları → Excel İndir butonuyla şablonu indirin, maliyet bilgilerini doldurup Excel Yükle ile geri yükleyin." },
        ],
    },
    {
        icon: BookOpen,
        title: "Sipariş Analizi",
        desc: "Sipariş karlılığı, iade takibi, komisyon detayları.",
        articles: [
            { q: "Sipariş bazlı kârlılık nasıl hesaplanır?", a: "Her sipariş için: Net Kâr = Satış Fiyatı - Ürün Maliyeti - Komisyon - Kargo - KDV. İade durumunda tutar negatife döner." },
            { q: "İade edilen siparişler nasıl gösterilir?", a: "İade durumundaki siparişler kırmızı etiketle işaretlenir ve net cirodan düşülerek hesaplanır." },
        ],
    },
    {
        icon: HelpCircle,
        title: "Genel Sorular",
        desc: "Sıkça sorulan sorular ve genel kullanım rehberi.",
        articles: [
            { q: "EcomMarj hangi pazaryerlerini destekliyor?", a: "Şu anda yalnızca Trendyol entegrasyonu aktiftir. Hepsiburada, Amazon ve N11 desteği yakında eklenecektir." },
            { q: "Verilerim güvende mi?", a: "Evet. API bilgileriniz 256-bit şifreleme ile saklanır, tüm bağlantılar SSL/TLS üzerinden yapılır." },
            { q: "Destek ekibine nasıl ulaşırım?", a: "İletişim sayfamızdan form doldurarak veya destek@ecommarj.com adresine e-posta göndererek ulaşabilirsiniz." },
        ],
    },
];

export default function HelpCenterPage() {
    const [openIndex, setOpenIndex] = useState<number | null>(0);

    return (
        <div className="pt-28 pb-20">
            <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center mb-16">
                    <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4">
                        Yardım <span className="gradient-text">Merkezi</span>
                    </h1>
                    <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                        Size nasıl yardımcı olabiliriz? Bir kategori seçerek detaylı bilgi alın.
                    </p>
                </div>

                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {categories.map((cat, i) => (
                        <div key={cat.title} className="glass-card rounded-2xl overflow-hidden flex flex-col">
                            <button
                                onClick={() => setOpenIndex(openIndex === i ? null : i)}
                                className="p-6 text-left hover:bg-white/[0.02] transition-all flex-1"
                            >
                                <div className="flex items-start justify-between mb-3">
                                    <div className="w-10 h-10 rounded-lg bg-accent-500/10 border border-accent-500/20 flex items-center justify-center">
                                        <cat.icon className="w-5 h-5 text-accent-400" />
                                    </div>
                                    <ChevronDown className={`w-4 h-4 text-slate-500 transition-transform duration-200 ${openIndex === i ? "rotate-180" : ""}`} />
                                </div>
                                <h3 className="text-base font-semibold text-white mb-1">{cat.title}</h3>
                                <p className="text-sm text-slate-400">{cat.desc}</p>
                                <span className="text-xs text-slate-500 mt-2 block">{cat.articles.length} makale</span>
                            </button>

                            {openIndex === i && (
                                <div className="px-6 pb-6 border-t border-white/5 pt-4 space-y-4">
                                    {cat.articles.map((article) => (
                                        <div key={article.q}>
                                            <h4 className="text-sm font-medium text-white mb-1">{article.q}</h4>
                                            <p className="text-xs text-slate-400 leading-relaxed">{article.a}</p>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
