export default function Footer() {
    const columns = [
        {
            title: "Ürün",
            links: ["Özellikler", "Fiyatlandırma", "Entegrasyonlar", "API"],
        },
        {
            title: "Şirket",
            links: ["Hakkımızda", "Blog", "Kariyer", "İletişim"],
        },
        {
            title: "Destek",
            links: ["Yardım Merkezi", "Dokümantasyon", "Durum Sayfası", "SSS"],
        },
        {
            title: "Yasal",
            links: ["Gizlilik Politikası", "Kullanım Şartları", "KVKK"],
        },
    ];

    return (
        <footer className="border-t border-white/5">
            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-14 sm:py-16">
                <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-5">
                    {/* Brand */}
                    <div className="sm:col-span-2 lg:col-span-1">
                        <a href="#" className="inline-flex items-center gap-2.5 mb-5">
                            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-accent-400 to-electric-500 flex items-center justify-center text-white font-bold text-xs shrink-0">
                                E
                            </div>
                            <span className="text-lg font-bold text-white">
                                Ecom<span className="gradient-text-blue">Pro</span>
                            </span>
                        </a>
                        <p className="text-sm text-white/60 leading-relaxed mb-5">
                            Trendyol satıcıları için
                            <br />
                            karlılık ve büyüme platformu.
                        </p>
                        <div className="flex gap-3">
                            {["X", "In", "YT"].map((icon) => (
                                <a
                                    key={icon}
                                    href="#"
                                    className="w-9 h-9 rounded-lg glass-card flex items-center justify-center text-xs text-slate-400 hover:text-white transition-all"
                                >
                                    {icon}
                                </a>
                            ))}
                        </div>
                    </div>

                    {/* Link columns */}
                    {columns.map((col) => (
                        <div key={col.title}>
                            <h4 className="text-sm font-semibold text-white mb-4">{col.title}</h4>
                            <ul className="space-y-3">
                                {col.links.map((link) => (
                                    <li key={link}>
                                        <a href="#" className="text-sm text-white/60 hover:text-white transition-colors">
                                            {link}
                                        </a>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    ))}
                </div>

                {/* Bottom bar */}
                <div className="mt-14 pt-8 border-t border-white/5 flex flex-col sm:flex-row items-center justify-between gap-4">
                    <p className="text-xs text-slate-600">© 2026 EcomPro. Tüm hakları saklıdır.</p>
                    <p className="text-xs text-slate-600">Türkiye&apos;de 🇹🇷 sevgiyle yapıldı.</p>
                </div>
            </div>
        </footer>
    );
}
