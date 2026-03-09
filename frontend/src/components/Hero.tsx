export default function Hero() {
    return (
        <section className="relative py-16 sm:py-20 lg:py-24 overflow-hidden">
            {/* Background effects */}
            <div className="absolute inset-0 pointer-events-none">
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-accent-500/10 rounded-full blur-[160px]" />
                <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-electric-500/8 rounded-full blur-[100px]" />
                <div className="absolute inset-0 bg-[linear-gradient(rgba(56,189,248,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(56,189,248,0.03)_1px,transparent_1px)] bg-[size:60px_60px]" />
            </div>

            <div className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                {/* Badge */}
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-card mb-8">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="text-sm text-slate-300">
                        Türkiye&apos;nin #1 E-Ticaret Karlılık Platformu
                    </span>
                </div>

                {/* Heading */}
                <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-extrabold text-white tracking-tight leading-[1.1] mb-6">
                    Trendyol&apos;da{" "}
                    <span className="gradient-text">Gerçek</span>
                    <br />
                    Kârınızı Görün
                </h1>

                {/* Description */}
                <p className="mt-4 text-base sm:text-lg text-white/70 max-w-2xl mx-auto leading-relaxed mb-10">
                    Komisyon, kargo, iade, KDV ve tüm giderleriniz otomatik hesaplansın.
                    <br className="hidden sm:block" />
                    Saniyeler içinde ürün bazlı net kâr-zarar analizi yapın.
                </p>

                {/* CTA Buttons */}
                <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4 mb-14 sm:mb-16">
                    <a
                        href="/ucretsiz-basla"
                        className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-gradient-to-r from-accent-500 to-electric-500 hover:from-accent-400 hover:to-electric-400 text-white font-semibold text-base shadow-xl shadow-accent-500/25 hover:shadow-accent-500/40 hover:scale-[1.03] transition-all duration-300 text-center"
                    >
                        Ücretsiz Dene — 14 Gün
                    </a>
                    <a
                        href="#how-it-works"
                        className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl glass text-slate-200 font-medium text-base hover:text-white transition-all duration-300"
                    >
                        Nasıl Çalışır?
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M5 12h14M12 5l7 7-7 7" />
                        </svg>
                    </a>
                </div>

                {/* Dashboard mockup */}
                <div className="relative max-w-4xl mx-auto">
                    <div className="absolute -inset-6 bg-gradient-to-b from-accent-500/15 to-transparent rounded-3xl blur-2xl pointer-events-none" />

                    <div className="relative glass-card rounded-2xl overflow-hidden border border-white/10 shadow-2xl shadow-black/30">
                        {/* Browser bar */}
                        <div className="flex items-center gap-2 px-4 py-2.5 bg-navy-900/60 border-b border-white/5">
                            <div className="flex gap-1.5">
                                <div className="w-2.5 h-2.5 rounded-full bg-rose-400/70" />
                                <div className="w-2.5 h-2.5 rounded-full bg-yellow-400/70" />
                                <div className="w-2.5 h-2.5 rounded-full bg-emerald-400/70" />
                            </div>
                            <div className="flex-1 mx-8">
                                <div className="max-w-[240px] mx-auto bg-navy-950/60 rounded-md px-3 py-1 text-xs text-slate-500 text-center">
                                    app.ecommarj.com/dashboard
                                </div>
                            </div>
                        </div>

                        {/* Dashboard content */}
                        <div className="p-4 sm:p-6 space-y-4">
                            {/* Metrics */}
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                                {[
                                    { label: "Net Kâr", value: "₺47,820", change: "+12.5%", positive: true },
                                    { label: "Toplam Ciro", value: "₺186,400", change: "+8.3%", positive: true },
                                    { label: "Sipariş", value: "1,247", change: "+15.2%", positive: true },
                                    { label: "İade Oranı", value: "%4.2", change: "-2.1%", positive: false },
                                ].map((m, i) => (
                                    <div key={i} className="bg-navy-900/50 rounded-xl p-3 sm:p-4 border border-white/5">
                                        <p className="text-[10px] sm:text-xs text-slate-500 mb-1">{m.label}</p>
                                        <p className="text-base sm:text-xl font-bold text-white">{m.value}</p>
                                        <p className={`text-[10px] sm:text-xs mt-1 ${m.positive ? "text-emerald-400" : "text-rose-400"}`}>
                                            {m.change}
                                        </p>
                                    </div>
                                ))}
                            </div>

                            {/* Chart */}
                            <div className="bg-navy-900/50 rounded-xl p-4 border border-white/5">
                                <div className="flex items-center justify-between mb-3">
                                    <span className="text-xs sm:text-sm text-slate-400">Günlük Karlılık Trendi</span>
                                    <div className="flex gap-2 text-[10px] sm:text-xs">
                                        <button className="text-slate-500">7G</button>
                                        <button className="text-accent-400 font-medium">30G</button>
                                        <button className="text-slate-500">90G</button>
                                    </div>
                                </div>
                                <div className="flex items-end gap-[3px] h-20 sm:h-28">
                                    {[30, 45, 25, 60, 40, 55, 70, 50, 65, 80, 60, 75, 55, 85, 65, 70, 90, 75, 80, 95, 70, 85, 60, 78, 88, 72, 82, 68, 78, 92].map((h, i) => (
                                        <div key={i} className="flex-1 rounded-t-sm bg-gradient-to-t from-accent-500/30 to-accent-400/80" style={{ height: `${h}%` }} />
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Trust badges */}
                <div className="mt-10 sm:mt-12 flex flex-wrap items-center justify-center gap-6 sm:gap-10 text-[10px] sm:text-xs text-slate-500 uppercase tracking-widest">
                    {["256-BİT SSL", "KVKK UYUMLU", "7/24 DESTEK", "TRENDYOL ONAYLI API"].map((b) => (
                        <span key={b}>{b}</span>
                    ))}
                </div>
            </div>
        </section>
    );
}
