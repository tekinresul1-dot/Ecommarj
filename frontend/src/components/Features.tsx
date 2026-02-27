export default function Features() {
    const features = [
        {
            icon: (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 2v20M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6" />
                </svg>
            ),
            title: "Otomatik Karlılık Hesaplama",
            description: "Komisyon, kargo, iade, KDV, stopaj dahil tüm giderler otomatik hesaplanır. Her sipariş ve ürün için net kâr/zarar görün.",
            color: "from-emerald-400 to-emerald-500",
        },
        {
            icon: (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M3 3v18h18" />
                    <path d="M7 16l4-8 4 5 5-9" />
                </svg>
            ),
            title: "Gerçek Zamanlı Dashboard",
            description: "Günlük, haftalık, aylık performansınızı anlık takip edin. Takvim görünümüyle karşılaştırmalı analiz yapın.",
            color: "from-accent-400 to-accent-500",
        },
        {
            icon: (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71" />
                    <path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71" />
                </svg>
            ),
            title: "Trendyol API Entegrasyonu",
            description: "Ürünler, siparişler ve finansal hareketler Trendyol API üzerinden otomatik senkronize edilir. Manuel veri girişi yok.",
            color: "from-electric-400 to-electric-500",
        },
        {
            icon: (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="3" width="7" height="7" rx="1" />
                    <rect x="14" y="3" width="7" height="7" rx="1" />
                    <rect x="3" y="14" width="7" height="7" rx="1" />
                    <rect x="14" y="14" width="7" height="7" rx="1" />
                </svg>
            ),
            title: "Ürün Performans Analizi",
            description: "En kârlı ve en çok zarar ettiren ürünlerinizi anında tespit edin. Kategori bazlı performans raporları alın.",
            color: "from-rose-400 to-rose-500",
        },
        {
            icon: (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2" />
                    <circle cx="9" cy="7" r="4" />
                    <path d="M22 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" />
                </svg>
            ),
            title: "İade ve İptal Takibi",
            description: "İade oranlarınızı ürün bazlı analiz edin. İade nedenlerini kategorize ederek sorunlu ürünleri tespit edin.",
            color: "from-amber-400 to-amber-500",
        },
        {
            icon: (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14.5 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V7.5L14.5 2z" />
                    <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" />
                </svg>
            ),
            title: "Kampanya Analizi",
            description: "Flaş teklifler, avantajlı etiket ve haftalık komisyon tarifelerinin gerçek karlılığınıza etkisini ölçün.",
            color: "from-violet-400 to-violet-500",
        },
    ];

    return (
        <section id="features" className="relative py-16 sm:py-20 lg:py-24">
            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                {/* Header */}
                <div className="text-center mb-12 sm:mb-16">
                    <p className="text-sm font-semibold text-accent-400 tracking-wider uppercase mb-3">
                        Özellikler
                    </p>
                    <h2 className="text-3xl sm:text-4xl lg:text-5xl font-semibold text-white tracking-tight">
                        Kârınızı Artıran <span className="gradient-text">Her Araç</span>
                    </h2>
                    <p className="mt-4 text-base sm:text-lg text-white/70 max-w-2xl mx-auto leading-relaxed">
                        Excel tablolarıyla uğraşmayın. Ecompro, tüm hesaplamaları arka planda otomatik yapar ve size net resmi gösterir.
                    </p>
                </div>

                {/* Cards grid */}
                <div className="grid gap-6 lg:gap-8 sm:grid-cols-2 lg:grid-cols-3">
                    {features.map((f, i) => (
                        <div
                            key={i}
                            className="group h-full flex flex-col glass-card rounded-2xl p-6 sm:p-7 border border-white/[0.06] hover:border-accent-400/20 hover:shadow-lg hover:shadow-accent-500/5 transition-all duration-300"
                        >
                            {/* Icon */}
                            <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${f.color} flex items-center justify-center text-white mb-4 shrink-0 group-hover:scale-110 transition-transform duration-300`}>
                                {f.icon}
                            </div>

                            {/* Title */}
                            <h3 className="text-lg sm:text-xl font-semibold text-white line-clamp-2">
                                {f.title}
                            </h3>

                            {/* Description */}
                            <p className="mt-2 text-sm sm:text-base text-white/70 leading-relaxed line-clamp-4">
                                {f.description}
                            </p>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}
