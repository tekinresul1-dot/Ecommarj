"use client";

import { useState } from "react";
import { BookOpen, Plug, Database, Shield, ChevronDown } from "lucide-react";

const docs = [
    {
        icon: BookOpen,
        title: "Başlangıç Rehberi",
        tag: "Başlangıç",
        desc: "Hesap oluşturma, ilk giriş ve temel ayarlar.",
        content: [
            { q: "Hesap nasıl oluşturulur?", a: "Ana sayfadaki \"Ücretsiz Başla\" butonuna tıklayarak ad, e-posta ve şifre bilgilerinizi girerek hesap oluşturabilirsiniz. Hesabınız anında aktif olur." },
            { q: "İlk giriş sonrası ne yapmalıyım?", a: "İlk girişte \"Pazaryerinizi Bağlayın\" penceresi otomatik olarak açılacaktır. Trendyol API bilgilerinizi girerek mağazanızı bağlayabilirsiniz." },
            { q: "Dashboard nasıl kullanılır?", a: "Dashboard'da ciro, kâr, sipariş sayısı ve kâr marjı gibi KPI'ları görebilirsiniz. Tarih filtresi ile istediğiniz döneme göre verileri inceleyebilirsiniz." },
        ],
    },
    {
        icon: Plug,
        title: "Trendyol Entegrasyonu",
        tag: "Entegrasyon",
        desc: "API bilgilerini alma, bağlantı kurma ve IP whitelist ayarları.",
        content: [
            { q: "Trendyol API bilgilerini nereden alırım?", a: "Trendyol Satıcı Paneli → Entegrasyon → Entegrasyon Bilgileri sayfasından Supplier ID, API Key ve API Secret bilgilerinizi alabilirsiniz." },
            { q: "IP Whitelist nedir ve nasıl ayarlanır?", a: "Trendyol, API erişimi için sunucu IP'nizin whitelist'e eklenmesini gerektirir. EcomMarj sunucu IP'si: 91.98.226.158. Bu IP'yi Trendyol Satıcı Paneli → Entegrasyon → IP Whitelist bölümüne ekleyin." },
            { q: "Bağlantı testi başarısız olursa ne yapmalıyım?", a: "1) API bilgilerinizi kontrol edin 2) IP whitelist'i doğrulayın 3) Trendyol tarafında entegrasyon onaylandığından emin olun. Hâlâ sorun varsa iletişim sayfamızdan destek alabilirsiniz." },
        ],
    },
    {
        icon: Database,
        title: "Veri Senkronizasyonu",
        tag: "Teknik",
        desc: "Sipariş, ürün ve finansal verilerin otomatik çekilme süreci.",
        content: [
            { q: "Veriler ne sıklıkla güncellenir?", a: "Verileriniz gün içinde otomatik olarak senkronize edilir. İlk bağlantıda geçmiş siparişleriniz de otomatik çekilir." },
            { q: "Hangi veriler senkronize edilir?", a: "Siparişler (durum, tutar, komisyon, kargo), ürünler (stok, fiyat, barkod), iade/iptaller ve finansal hareketler senkronize edilir." },
            { q: "Eksik veri görüyorsam ne yapmalıyım?", a: "Ayarlar sayfasından \"Bağlantıyı Test Et\" butonuna basarak API bağlantınızı doğrulayın. Sorun devam ederse destek ekibimize başvurun." },
        ],
    },
    {
        icon: Shield,
        title: "Maliyet Yükleme",
        tag: "Rehber",
        desc: "Excel ile toplu maliyet girişi, KDV oranları ve desi ayarları.",
        content: [
            { q: "Ürün maliyetlerini nasıl girerim?", a: "Ürün Ayarları sayfasından her ürünün maliyetini tek tek girebilirsiniz. Alış fiyatı, KDV oranı ve desi ağırlığı alanlarını doldurun." },
            { q: "Toplu maliyet yükleme nasıl yapılır?", a: "Ürün Ayarları → Excel İndir butonuyla mevcut ürün listenizi indirin, maliyet sütunlarını doldurup Excel Yükle butonu ile geri yükleyin." },
            { q: "KDV oranlarını nereden ayarlarım?", a: "Her ürün için ayrı KDV oranı atanabilir. Varsayılan olarak %20 uygulanır, ancak gıda, kitap gibi kategoriler için %1 veya %10 seçebilirsiniz." },
        ],
    },
];

export default function DocsPage() {
    const [openIndex, setOpenIndex] = useState<number | null>(0);

    return (
        <div className="pt-28 pb-20">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center mb-16">
                    <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4">
                        <span className="gradient-text">Dokümantasyon</span>
                    </h1>
                    <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                        EcomMarj&apos;ı en verimli şekilde kullanmak için rehberlerimizi inceleyin.
                    </p>
                </div>

                <div className="space-y-4">
                    {docs.map((doc, i) => (
                        <div key={doc.title} className="glass-card rounded-2xl overflow-hidden">
                            <button
                                onClick={() => setOpenIndex(openIndex === i ? null : i)}
                                className="w-full px-6 py-5 flex items-center gap-5 hover:bg-white/[0.02] transition-all text-left"
                            >
                                <div className="w-12 h-12 rounded-xl bg-accent-500/10 border border-accent-500/20 flex items-center justify-center shrink-0">
                                    <doc.icon className="w-6 h-6 text-accent-400" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-1">
                                        <h3 className="text-lg font-semibold text-white">{doc.title}</h3>
                                        <span className="text-xs bg-accent-500/10 text-accent-400 border border-accent-500/20 px-2 py-0.5 rounded-full">{doc.tag}</span>
                                    </div>
                                    <p className="text-sm text-slate-400">{doc.desc}</p>
                                </div>
                                <ChevronDown className={`w-5 h-5 text-slate-500 shrink-0 transition-transform duration-200 ${openIndex === i ? "rotate-180" : ""}`} />
                            </button>

                            {openIndex === i && (
                                <div className="px-6 pb-6 border-t border-white/5 pt-4 space-y-4">
                                    {doc.content.map((item) => (
                                        <div key={item.q}>
                                            <h4 className="text-sm font-medium text-white mb-1">{item.q}</h4>
                                            <p className="text-sm text-slate-400 leading-relaxed">{item.a}</p>
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
