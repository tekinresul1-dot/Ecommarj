export default function HowItWorks() {
    const steps = [
        {
            number: "01",
            title: "Hızlı Üye Olun",
            description: "Mağazanızı birkaç tıkla bağlayın. Kurulum 30 saniye sürer, karmaşık ayar gerektirmez.",
            icon: (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2" />
                    <circle cx="9" cy="7" r="4" />
                    <line x1="19" y1="8" x2="19" y2="14" />
                    <line x1="22" y1="11" x2="16" y2="11" />
                </svg>
            ),
            color: "from-accent-400 to-accent-500",
        },
        {
            number: "02",
            title: "API Bağlantısı Kurun",
            description: "Güvenli entegrasyonla ürünler, siparişler ve finansal veriler otomatik çekilsin.",
            icon: (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71" />
                    <path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71" />
                </svg>
            ),
            color: "from-electric-400 to-electric-500",
        },
        {
            number: "03",
            title: "Net Kârınızı Görün",
            description: "Zarar eden ürünleri tespit edin, doğru fiyatla kârınızı artırın. Tüm veriler tek ekranda.",
            icon: (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M3 3v18h18" />
                    <path d="M7 16l4-8 4 5 5-9" />
                </svg>
            ),
            color: "from-emerald-400 to-emerald-500",
        },
    ];

    return (
        <section id="how-it-works" className="relative py-16 sm:py-20 lg:py-24">
            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                {/* Header */}
                <div className="text-center mb-12 sm:mb-16">
                    <p className="text-sm font-semibold text-accent-400 tracking-wider uppercase mb-3">
                        Nasıl Çalışır
                    </p>
                    <h2 className="text-3xl sm:text-4xl lg:text-5xl font-semibold text-white tracking-tight">
                        <span className="gradient-text">3 Adımda</span> Başlayın
                    </h2>
                    <p className="mt-4 text-base sm:text-lg text-white/70 max-w-2xl mx-auto leading-relaxed">
                        Trendyol karlılık analizine birkaç dakika içinde başlayabilirsiniz.
                    </p>
                </div>

                {/* Steps grid */}
                <div className="grid gap-6 lg:grid-cols-3">
                    {steps.map((step, i) => (
                        <div
                            key={i}
                            className="group h-full glass-card rounded-2xl p-6 sm:p-7 border border-white/[0.06] hover:border-accent-400/20 transition-all duration-300 flex flex-col"
                        >
                            {/* Top row: icon + number */}
                            <div className="flex items-center gap-4 mb-4">
                                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${step.color} flex items-center justify-center text-white shrink-0 group-hover:scale-110 transition-transform duration-300`}>
                                    {step.icon}
                                </div>
                                <span className="text-4xl font-extrabold text-white/[0.07] leading-none select-none">
                                    {step.number}
                                </span>
                            </div>

                            {/* Title – fixed min height so cards align */}
                            <h3 className="text-lg sm:text-xl font-semibold text-white min-h-[28px] lg:min-h-[56px] flex items-start">
                                {step.title}
                            </h3>

                            {/* Description */}
                            <p className="mt-2 text-sm sm:text-base text-white/70 leading-relaxed">
                                {step.description}
                            </p>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}
