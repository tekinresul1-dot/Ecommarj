"use client";

import { useState } from "react";
import { CalendarDays, ArrowLeft } from "lucide-react";

const posts = [
    {
        title: "Trendyol'da Karlılığınızı Artırmanın 5 Yolu",
        category: "Strateji",
        date: "Mart 2026",
        excerpt: "Komisyon yapısını anlayarak, maliyet optimizasyonu yaparak ve doğru fiyatlandırma stratejileri ile karlılığınızı %20'ye kadar artırabilirsiniz.",
        body: `E-ticaret satıcıları için karlılık, sadece çok satmakla değil, akıllı satmakla gelir. İşte Trendyol'da karlılığınızı artırmanın 5 etkili yolu:

**1. Komisyon Yapısını Anlayın**
Trendyol'un komisyon oranları kategoriye göre değişir. Kendi kategorinizin komisyon oranını bilerek fiyatlandırma yapın. Yüksek komisyonlu kategorilerde daha yüksek marjlı ürünlere odaklanın.

**2. Kargo Maliyetlerini Optimize Edin**
Paketleme boyutlarını küçülterek desi ağırlığını düşürün. Kargo anlaşmanızı düzenli olarak gözden geçirin ve hacim artışıyla daha iyi fiyatlar müzakere edin.

**3. İade Oranlarını Düşürün**
Detaylı ürün açıklamaları, doğru beden tabloları ve kaliteli ürün fotoğrafları iade oranlarını önemli ölçüde azaltır. Her iade kardan düşer.

**4. Ürün Maliyetlerinizi Takip Edin**
Hangi ürünlerin zarar ettiğini bilmeden karlılık artırmak mümkün değildir. EcomMarj ile her ürünün gerçek net karlılığını görebilirsiniz.

**5. Fiyatlandırmayı Veriye Dayalı Yapın**
Pazar fiyatlarını takip ederek, rakip analizini yaparak ve maliyet verilerinizi kullanarak optimum fiyat noktasını belirleyin.`,
    },
    {
        title: "Kargo Maliyetlerini Nasıl Düşürürsünüz?",
        category: "Maliyet Yönetimi",
        date: "Mart 2026",
        excerpt: "Desi hesaplama, paketleme optimizasyonu ve kargo anlaşmaları ile kargo maliyetlerinizi minimuma indirmenin yolları.",
        body: `Kargo maliyetleri, e-ticaret satıcılarının en büyük gizli gideri olabilir. İşte bu maliyetleri düşürmenin pratik yolları:

**Desi Hesaplama Optimizasyonu**
Kargo firmaları ağırlık veya hacim (desi) ağırlığından hangisi yüksekse onu baz alır. Paket boyutlarını minimumda tutmak doğrudan maliyet düşürür.

**Paketleme Standartları Oluşturun**
Her ürün kategorisi için standart paket boyutları belirleyin. Gereksiz büyük kutular kullanmaktan kaçının. Bubble wrap yerine kağıt dolgular kullanmak hem çevreci hem ekonomiktir.

**Kargo Anlaşmanızı Gözden Geçirin**
Aylık gönderi hacminiz arttıkça kargo firmasından daha iyi fiyatlar talep edebilirsiniz. Birden fazla firmayla teklif alarak karşılaştırın.

**Trendyol Kargo Barem Desteği**
Trendyol'un kargo barem yapısını anlamak önemlidir. EcomMarj, barem hesaplamalarını otomatik olarak yaparak gerçek kargo maliyetinizi gösterir.`,
    },
    {
        title: "İade Oranlarını Azaltma Rehberi",
        category: "Operasyon",
        date: "Şubat 2026",
        excerpt: "Ürün açıklamalarını iyileştirme, kalite kontrol ve müşteri iletişimi ile iade oranlarınızı nasıl düşürebilirsiniz?",
        body: `İadeler, hem gelir kaybına hem de ek maliyetlere yol açar. İade oranlarını düşürmek karlılığı doğrudan artırır.

**Ürün Açıklamalarını Detaylandırın**
Müşterinin ürünü fiziksel olarak inceleyemediği e-ticarette, doğru ve detaylı açıklamalar beklenti yönetiminin temelidir. Malzeme, boyut, ağırlık bilgilerini mutlaka ekleyin.

**Kaliteli Ürün Fotoğrafları**
Farklı açılardan çekilmiş, gerçek renkleri yansıtan fotoğraflar kullanın. Model üzerinde çekimler beden algısını kolaylaştırır.

**Beden Tablosu Kullanın**
Giyim kategorisinde iade nedenlerinin %40'ı beden uyumsuzluğudur. Detaylı beden tablosu ve ölçü rehberi ekleyin.

**Kalite Kontrol Süreçleri**
Gönderi öncesi her ürünü kontrol edin. Hatalı veya hasarlı ürün gönderimi hem iade hem de olumsuz yorum getirir.

**Müşteri İletişimi**
Kargo takip bilgilerini proaktif olarak paylaşın. Teslimat sonrası memnuniyet mesajı göndermek iade yerine değişim talebine yönlendirebilir.`,
    },
    {
        title: "Ürün Bazlı Karlılık Analizi Neden Önemli?",
        category: "Analiz",
        date: "Şubat 2026",
        excerpt: "Toplam ciro yerine her ürünün bireysel karlılığını takip etmenin işletmenize sağladığı avantajlar.",
        body: `Birçok satıcı toplam cirolarına bakarak işlerinin iyi gittiğini düşünür. Ancak gerçek durum çok farklı olabilir.

**Gizli Zararlar**
Yüksek cirolu bir ürün, yüksek komisyon, iade oranı ve kargo maliyetleri nedeniyle aslında zarar ediyor olabilir. Bu ürünü satmaya devam etmek, büyüdükçe daha fazla zarar etmek demektir.

**80/20 Kuralı**
Genellikle ürünlerinizin %20'si toplam karınızın %80'ini oluşturur. Bu ürünleri bilmek, stok yönetimi ve pazarlama stratejinizi optimize etmenizi sağlar.

**Fiyatlandırma Kararları**
Ürün bazlı maliyet analizi olmadan doğru fiyatlandırma yapılamaz. Her ürünün maliyetini, komisyonunu ve kargo giderini bilerek minimum satış fiyatını belirleyin.

**EcomMarj'ın Rolü**
EcomMarj, her ürün ve sipariş için otomatik karlılık hesaplaması yaparak zarar eden ürünleri anında tespit etmenizi sağlar. Dashboard'daki "En Çok Zarar Eden Ürünler" raporu ile hızlı aksiyon alabilirsiniz.`,
    },
];

export default function BlogPage() {
    const [selectedPost, setSelectedPost] = useState<number | null>(null);

    if (selectedPost !== null) {
        const post = posts[selectedPost];
        return (
            <div className="pt-28 pb-20">
                <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
                    <button
                        onClick={() => setSelectedPost(null)}
                        className="flex items-center gap-2 text-sm text-accent-400 hover:text-white transition-colors mb-8"
                    >
                        <ArrowLeft className="w-4 h-4" /> Blog&apos;a dön
                    </button>
                    <div className="flex items-center gap-3 mb-4">
                        <span className="text-xs font-medium bg-accent-500/10 text-accent-400 border border-accent-500/20 px-3 py-1 rounded-full">
                            {post.category}
                        </span>
                        <span className="flex items-center gap-1.5 text-xs text-slate-500">
                            <CalendarDays className="w-3.5 h-3.5" /> {post.date}
                        </span>
                    </div>
                    <h1 className="text-3xl font-bold text-white mb-6">{post.title}</h1>
                    <div className="text-slate-300 leading-relaxed whitespace-pre-line text-[15px]">
                        {post.body}
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="pt-28 pb-20">
            <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center mb-16">
                    <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4">
                        <span className="gradient-text">Blog</span>
                    </h1>
                    <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                        E-ticaret karlılığı, Trendyol stratejileri ve maliyet optimizasyonu hakkında içerikler.
                    </p>
                </div>

                <div className="grid gap-6 md:grid-cols-2">
                    {posts.map((post, i) => (
                        <article
                            key={post.title}
                            onClick={() => setSelectedPost(i)}
                            className="glass-card rounded-2xl p-8 hover:border-accent-400/20 transition-all group cursor-pointer"
                        >
                            <div className="flex items-center gap-3 mb-4">
                                <span className="text-xs font-medium bg-accent-500/10 text-accent-400 border border-accent-500/20 px-3 py-1 rounded-full">
                                    {post.category}
                                </span>
                                <span className="flex items-center gap-1.5 text-xs text-slate-500">
                                    <CalendarDays className="w-3.5 h-3.5" /> {post.date}
                                </span>
                            </div>
                            <h2 className="text-xl font-semibold text-white mb-3 group-hover:text-accent-400 transition-colors">
                                {post.title}
                            </h2>
                            <p className="text-sm text-slate-400 leading-relaxed">{post.excerpt}</p>
                        </article>
                    ))}
                </div>
            </div>
        </div>
    );
}
