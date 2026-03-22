"use client";

import { useState, useEffect } from "react";
import { 
    AlertTriangle, Package, TrendingUp, TrendingDown, 
    ArrowRight, DollarSign, BarChart2, Tag, Percent
} from "lucide-react";
import { api } from "@/lib/api";
import clsx from "clsx";
import { AreaChart, Area, ResponsiveContainer, Tooltip } from "recharts";
interface TrendData {
    date: string;
    revenue: string;
    profit: string;
}

interface Breakdown {
    sale_price: string;
    commission: string;
    cargo: string;
    tax: string;
    return_loss: string;
    net_profit: string;
}

interface ProductAnalysis {
    barcode: string;
    product_name: string;
    category: string;
    stock: number;
    total_sales: number;
    revenue: string;
    net_profit: string;
    profit_margin: string;
    return_cost: string;
    score: string;
    segment: string;
    tags: string[];
    actions: string[];
    trend: TrendData[];
    breakdown: Breakdown;
}

function ScoreBadge({ score }: { score: string }) {
    const s = parseFloat(score);
    if (s >= 80) return <span className="inline-flex items-center gap-1 rounded-md bg-green-500/10 px-2 py-1 text-xs font-semibold text-green-400 ring-1 ring-inset ring-green-500/20"><TrendingUp className="w-3 h-3"/>Scale ({s})</span>;
    if (s >= 50) return <span className="inline-flex items-center gap-1 rounded-md bg-yellow-500/10 px-2 py-1 text-xs font-semibold text-yellow-400 ring-1 ring-inset ring-yellow-500/20"><AlertTriangle className="w-3 h-3"/>Optimize ({s})</span>;
    return <span className="inline-flex items-center gap-1 rounded-md bg-red-500/10 px-2 py-1 text-xs font-semibold text-red-400 ring-1 ring-inset ring-red-500/20"><TrendingDown className="w-3 h-3"/>Review ({s})</span>;
}

function MiniChart({ data }: { data: TrendData[] }) {
    if (!data || data.length === 0) return <div className="text-xs text-white/30">Veri yok</div>;
    return (
        <div className="h-10 w-24">
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data}>
                    <Tooltip 
                        content={({ active, payload }) => {
                            if (active && payload && payload.length) {
                                return (
                                    <div className="bg-navy-900 border border-white/10 p-1 text-[10px] rounded shadow-xl">
                                        <p className="text-white">Kâr: ₺{payload[0].value}</p>
                                    </div>
                                );
                            }
                            return null;
                        }}
                    />
                    <Area type="monotone" dataKey="profit" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.2} />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
}

export default function ProductAnalysisPage() {
    const [products, setProducts] = useState<ProductAnalysis[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [selectedProduct, setSelectedProduct] = useState<ProductAnalysis | null>(null);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const res = await api.get("/reports/product-analysis/");
            if (res.data?.products) {
                setProducts(res.data.products);
            }
        } catch (err: any) {
            setError(err.response?.data?.error || "Veriler yüklenirken bir hata oluştu.");
        } finally {
            setLoading(false);
        }
    };

    const topProducts = products.slice(0, 5);

    return (
        <div className="p-6 max-w-[1600px] mx-auto space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white">Ürün Analizi (Karar Motoru)</h1>
                    <p className="text-sm text-white/60 mt-1">Ürün bazlı büyüme rotanızı ve aksiyon planınızı yönetin.</p>
                </div>
            </div>

            {error && (
                <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-4 rounded-xl flex items-center gap-3">
                    <AlertTriangle className="w-5 h-5" />
                    <p>{error}</p>
                </div>
            )}

            {/* Top Products Widget */}
            {!loading && topProducts.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                    {topProducts.map((p, i) => (
                        <div key={p.barcode} className="bg-navy-900/50 border border-white/5 rounded-2xl p-4 flex flex-col gap-2 hover:bg-navy-900 transition-colors">
                            <div className="flex justify-between items-start">
                                <ScoreBadge score={p.score} />
                                <span className="text-xs font-mono text-white/40">#{i + 1}</span>
                            </div>
                            <h3 className="text-sm font-medium text-white line-clamp-2" title={p.product_name}>{p.product_name}</h3>
                            <div className="mt-auto pt-2 flex items-center justify-between border-t border-white/5">
                                <div className="text-xs text-white/50">Net Kâr</div>
                                <div className="text-sm font-semibold text-emerald-400">₺{p.net_profit}</div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Main Table */}
            <div className="bg-navy-900/50 border border-white/5 rounded-2xl overflow-hidden shadow-2xl">
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm whitespace-nowrap">
                        <thead className="bg-navy-950/50 uppercase tracking-wider text-[11px] font-semibold text-white/40 border-b border-white/10">
                            <tr>
                                <th className="px-6 py-4">Ürün</th>
                                <th className="px-6 py-4">Metrikler</th>
                                <th className="px-6 py-4">Kârlılık</th>
                                <th className="px-6 py-4">Trend (7G)</th>
                                <th className="px-6 py-4">Puan / Segment</th>
                                <th className="px-6 py-4">Aksiyon</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {loading ? (
                                <tr>
                                    <td colSpan={6} className="px-6 py-12 text-center text-white/50">
                                        Analiz motoru çalışıyor...
                                    </td>
                                </tr>
                            ) : products.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="px-6 py-12 text-center text-white/50">
                                        Görüntülenecek veri bulunamadı.
                                    </td>
                                </tr>
                            ) : (
                                products.map((p) => (
                                    <tr 
                                        key={p.barcode} 
                                        className="hover:bg-white/[0.02] transition-colors cursor-pointer"
                                        onClick={() => setSelectedProduct(p)}
                                    >
                                        <td className="px-6 py-4">
                                            <div className="flex flex-col gap-1 w-64">
                                                <span className="text-white font-medium truncate" title={p.product_name}>{p.product_name}</span>
                                                <span className="text-xs text-white/40 font-mono">{p.barcode}</span>
                                                <div className="flex gap-1 mt-1 flex-wrap">
                                                    {p.tags.map(t => (
                                                        <span key={t} className="text-[10px] bg-white/5 text-white/60 px-1.5 py-0.5 rounded uppercase tracking-wider">
                                                            {t}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex flex-col gap-1">
                                                <div className="flex justify-between w-24"><span className="text-white/40 text-xs">Satış:</span><span className="text-white">{p.total_sales}</span></div>
                                                <div className="flex justify-between w-24"><span className="text-white/40 text-xs">Stok:</span><span className={clsx("font-medium", p.stock < 10 ? "text-red-400" : "text-white")}>{p.stock}</span></div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex flex-col gap-1">
                                                <div className="text-white font-semibold flex items-center gap-1">
                                                    <DollarSign className="w-3 h-3 text-white/40"/>
                                                    {p.net_profit}
                                                </div>
                                                <div className={clsx(
                                                    "text-xs font-semibold flex items-center gap-1",
                                                    parseFloat(p.profit_margin) < 0 ? "text-red-400" : "text-emerald-400"
                                                )}>
                                                    <Percent className="w-3 h-3"/>
                                                    {p.profit_margin} Marj
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <MiniChart data={p.trend} />
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex flex-col gap-2 items-start">
                                                <ScoreBadge score={p.score} />
                                                <span className={clsx(
                                                    "text-[10px] items-center gap-1 uppercase tracking-wider font-bold shadow-xl border border-white/5 px-2 py-0.5 rounded-full",
                                                    p.segment === "Cash Cow" ? "text-amber-400 bg-amber-400/10" :
                                                    p.segment === "Growth" ? "text-blue-400 bg-blue-400/10" :
                                                    p.segment === "Dead" ? "text-red-400 bg-red-400/10" : "text-white/40 bg-white/10"
                                                )}>{p.segment}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex flex-col gap-1.5">
                                                {p.actions.length > 0 ? p.actions.map(act => (
                                                    <button key={act} className="text-xs bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 border border-indigo-500/20 px-2 py-1.5 rounded-md flex items-center justify-between gap-2 transition-colors whitespace-nowrap shadow-sm">
                                                        {act}
                                                        <ArrowRight className="w-3 h-3"/>
                                                    </button>
                                                )) : (
                                                    <span className="text-xs text-white/30 italic">İzliyor...</span>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Profit Breakdown Modal */}
            {selectedProduct && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                    <div className="absolute inset-0 bg-navy-950/80 backdrop-blur-sm" onClick={() => setSelectedProduct(null)} />
                    <div className="relative bg-navy-900 border border-white/10 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
                        <div className="p-5 border-b border-white/5 bg-navy-800">
                            <h3 className="text-lg font-bold text-white truncate" title={selectedProduct.product_name}>Kâr Analizi</h3>
                            <p className="text-xs text-white/50 font-mono mt-1">{selectedProduct.barcode}</p>
                        </div>
                        <div className="p-5 space-y-4">
                            <div className="space-y-2 text-sm">
                                <div className="flex justify-between text-white/70">
                                    <span>Satış Geliri (Ciro)</span>
                                    <span className="font-semibold text-white">₺{selectedProduct.breakdown.sale_price}</span>
                                </div>
                                <div className="flex justify-between text-white/70">
                                    <span>Pazaryeri Komisyonu</span>
                                    <span className="text-red-400">-₺{selectedProduct.breakdown.commission}</span>
                                </div>
                                <div className="flex justify-between text-white/70">
                                    <span>Kargo Gideri</span>
                                    <span className="text-red-400">-₺{selectedProduct.breakdown.cargo}</span>
                                </div>
                                <div className="flex justify-between text-white/70">
                                    <span>Vergiler (KDV + Stopaj)</span>
                                    <span className="text-red-400">-₺{selectedProduct.breakdown.tax}</span>
                                </div>
                                {parseFloat(selectedProduct.breakdown.return_loss) > 0 && (
                                    <div className="flex justify-between text-white/70">
                                        <span>İade Kaynaklı Zarar</span>
                                        <span className="text-red-400">-₺{selectedProduct.breakdown.return_loss}</span>
                                    </div>
                                )}
                            </div>
                            <div className="pt-4 border-t border-white/10 flex justify-between items-center text-lg">
                                <span className="font-medium text-white">Net Kâr</span>
                                <span className={clsx("font-bold", parseFloat(selectedProduct.breakdown.net_profit) < 0 ? "text-red-400" : "text-emerald-400")}>
                                    ₺{selectedProduct.breakdown.net_profit}
                                </span>
                            </div>
                        </div>
                        <div className="p-4 bg-navy-950/80 border-t border-white/5 flex gap-2">
                            <button onClick={() => setSelectedProduct(null)} className="w-full bg-white/5 hover:bg-white/10 border border-white/10 text-white transition-colors py-2 rounded-lg text-sm font-medium">Kapat</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
