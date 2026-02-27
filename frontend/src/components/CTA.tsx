export default function CTA() {
    return (
        <section className="relative py-16 sm:py-20 lg:py-24 overflow-hidden">
            {/* Background */}
            <div className="absolute inset-0 pointer-events-none">
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px] bg-accent-500/8 rounded-full blur-[150px]" />
            </div>

            <div className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="max-w-3xl mx-auto glass-card rounded-2xl sm:rounded-3xl gradient-border overflow-hidden">
                    {/* Top: heading + buttons */}
                    <div className="p-8 sm:p-10 text-center">
                        <h2 className="text-3xl sm:text-4xl lg:text-5xl font-semibold text-white tracking-tight mb-4">
                            Kârınızı Artırmaya
                            <br />
                            <span className="gradient-text">Bugün Başlayın</span>
                        </h2>
                        <p className="mt-4 text-base sm:text-lg text-white/70 max-w-md mx-auto leading-relaxed mb-8 sm:mb-10">
                            14 gün ücretsiz deneyin. Kredi kartı gerekmez.
                            Trendyol mağazanızı bağlayın ve gerçek kârınızı hemen görün.
                        </p>

                        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4">
                            <a
                                href="/ucretsiz-basla"
                                className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-gradient-to-r from-accent-500 to-electric-500 hover:from-accent-400 hover:to-electric-400 text-white font-semibold text-base shadow-xl shadow-accent-500/25 hover:shadow-accent-500/40 hover:scale-[1.03] transition-all duration-300 text-center"
                            >
                                Ücretsiz Hesap Oluştur
                            </a>
                            <a
                                href="#"
                                className="w-full sm:w-auto px-8 py-3.5 rounded-xl glass text-slate-200 font-medium text-base hover:text-white transition-all duration-300 text-center"
                            >
                                Demo İzle
                            </a>
                        </div>
                    </div>

                    {/* Bottom: stats bar */}
                    <div className="bg-navy-900/40 border-t border-white/[0.06] px-8 sm:px-10 py-6">
                        <div className="grid gap-6 sm:grid-cols-3 text-center">
                            {[
                                { value: "2,500+", label: "Aktif Satıcı" },
                                { value: "₺120M+", label: "Analiz Edilen Ciro" },
                                { value: "%98", label: "Memnuniyet" },
                            ].map((stat, i) => (
                                <div key={i}>
                                    <p className="text-xl sm:text-2xl font-extrabold gradient-text-blue mb-0.5">
                                        {stat.value}
                                    </p>
                                    <p className="text-[10px] sm:text-xs text-slate-500">{stat.label}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
