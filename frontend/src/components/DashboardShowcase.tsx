export default function DashboardShowcase() {
    const tabs = ["Genel Bakış", "Siparişler", "Ürünler", "İadeler"];

    const products = [
        { rank: 1, name: "Kadın Spor Ayakkabı – Beyaz", orders: 324, revenue: "₺38,880", profit: "₺9,720", margin: "25.0%" },
        { rank: 2, name: "Erkek Jogger Pantolon – Siyah", orders: 287, revenue: "₺34,440", profit: "₺7,576", margin: "22.0%" },
        { rank: 3, name: "Unisex Oversize T-shirt", orders: 512, revenue: "₺30,720", profit: "₺6,144", margin: "20.0%" },
        { rank: 4, name: "Kadın Çanta – Bej", orders: 156, revenue: "₺28,080", profit: "₺5,616", margin: "20.0%" },
        { rank: 5, name: "Erkek Sneaker – Gri", orders: 198, revenue: "₺25,740", profit: "₺4,892", margin: "19.0%" },
    ];

    return (
        <section id="dashboard" className="relative py-16 sm:py-20 lg:py-24">
            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                {/* Header */}
                <div className="text-center mb-12 sm:mb-16">
                    <p className="text-sm font-semibold text-accent-400 tracking-wider uppercase mb-3">
                        Dashboard
                    </p>
                    <h2 className="text-3xl sm:text-4xl lg:text-5xl font-semibold text-white tracking-tight">
                        Verileriniz, <span className="gradient-text">Tek Ekranda</span>
                    </h2>
                    <p className="mt-4 text-base sm:text-lg text-white/70 max-w-2xl mx-auto leading-relaxed">
                        Trendyol mağazanızın tüm performansını bir bakışta analiz edin.
                    </p>
                </div>

                {/* Dashboard card */}
                <div className="glass-card rounded-2xl border border-white/10 overflow-hidden">
                    {/* Tab bar */}
                    <div className="px-4 sm:px-6 py-3 border-b border-white/5 bg-navy-900/30">
                        <div className="flex flex-wrap gap-3">
                            {tabs.map((tab, i) => (
                                <button
                                    key={tab}
                                    className={`px-4 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-colors ${i === 0
                                            ? "bg-accent-500/15 text-accent-400"
                                            : "text-slate-500 hover:text-slate-300"
                                        }`}
                                >
                                    {tab}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Table */}
                    <div className="overflow-x-auto">
                        <div className="p-4 sm:p-6">
                            <h3 className="text-sm sm:text-base font-semibold text-white mb-4">
                                En Çok Kazandıran Ürünler
                                <span className="ml-2 text-xs text-slate-500 font-normal">Son 30 gün</span>
                            </h3>

                            <table className="w-full text-left">
                                <thead>
                                    <tr className="border-b border-white/5">
                                        <th className="pb-3 pr-4 text-xs sm:text-sm font-medium text-slate-500 w-8">#</th>
                                        <th className="pb-3 pr-4 text-xs sm:text-sm font-medium text-slate-500">Ürün</th>
                                        <th className="pb-3 pr-4 text-xs sm:text-sm font-medium text-slate-500 text-right">Sipariş</th>
                                        <th className="pb-3 pr-4 text-xs sm:text-sm font-medium text-slate-500 text-right">Ciro</th>
                                        <th className="pb-3 pr-4 text-xs sm:text-sm font-medium text-slate-500 text-right">Net Kâr</th>
                                        <th className="pb-3 text-xs sm:text-sm font-medium text-slate-500 text-right">Marj</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {products.map((p) => (
                                        <tr key={p.rank} className="border-b border-white/[0.03] last:border-0 hover:bg-white/[0.02] transition-colors">
                                            <td className="py-3 pr-4 text-xs sm:text-sm text-slate-500">{p.rank}</td>
                                            <td className="py-3 pr-4 text-xs sm:text-sm text-white max-w-[200px] truncate">{p.name}</td>
                                            <td className="py-3 pr-4 text-xs sm:text-sm text-slate-300 text-right tabular-nums">{p.orders}</td>
                                            <td className="py-3 pr-4 text-xs sm:text-sm text-slate-300 text-right tabular-nums">{p.revenue}</td>
                                            <td className="py-3 pr-4 text-xs sm:text-sm text-emerald-400 font-medium text-right tabular-nums">{p.profit}</td>
                                            <td className="py-3 text-xs sm:text-sm text-emerald-400 text-right tabular-nums">{p.margin}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
