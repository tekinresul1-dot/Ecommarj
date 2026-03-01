"use client";

import { AlertTriangle, PackageOpen, TrendingDown } from "lucide-react";
import Image from "next/image";

export function LowStockWidget({ alerts = [] }: { alerts: any[] }) {
    if (!alerts || alerts.length === 0) {
        return (
            <div className="bg-navy-900 border border-white/5 rounded-xl p-5 shadow-sm h-full flex flex-col justify-between">
                <div>
                    <h3 className="text-sm font-semibold text-white/80 flex items-center gap-2 mb-1">
                        <AlertTriangle className="w-4 h-4 text-emerald-400" />
                        Kritik Stok Uyarıları
                    </h3>
                    <p className="text-xs text-white/40">Stoğu bitmek üzere olan ürünler</p>
                </div>
                <div className="flex-1 flex flex-col items-center justify-center py-6 opacity-60">
                    <PackageOpen className="w-10 h-10 text-emerald-400 mb-2" />
                    <p className="text-sm text-white/70">Tüm stoklarınız güvende!</p>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-navy-900 border border-red-500/20 rounded-xl p-5 shadow-sm h-full flex flex-col relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/5 rounded-full blur-3xl -mr-10 -mt-10 transition-opacity group-hover:opacity-100 opacity-50"></div>

            <div className="mb-4 relative z-10">
                <h3 className="text-sm font-semibold text-white/90 flex items-center gap-2 mb-1">
                    <AlertTriangle className="w-4 h-4 text-red-500 animate-pulse" />
                    Kritik Stok Uyarıları
                </h3>
                <p className="text-xs text-white/40">Stokları %20'nin altına düşen ürünler</p>
            </div>

            <div className="flex-1 overflow-y-auto pr-2 space-y-3 scrollbar-thin scrollbar-thumb-white/10 relative z-10">
                {alerts.map((item, idx) => {
                    const percentage = Math.round((item.current_stock / item.initial_stock) * 100);

                    return (
                        <div key={idx} className="flex items-center gap-3 p-2.5 bg-white/5 rounded-lg border border-white/5 hover:bg-white/10 transition-colors">
                            <div className="w-10 h-10 rounded-md bg-navy-950 flex-shrink-0 flex items-center justify-center overflow-hidden border border-white/10 relative">
                                {item.image_url ? (
                                    <Image src={item.image_url} alt={item.title} fill className="object-cover" />
                                ) : (
                                    <PackageOpen className="w-5 h-5 text-white/30" />
                                )}
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="text-[13px] font-medium text-white truncate" title={item.title}>{item.title}</p>
                                <p className="text-[11px] text-white/40 mt-0.5 font-mono">{item.barcode}</p>
                            </div>
                            <div className="flex flex-col items-end flex-shrink-0">
                                <div className="flex items-center gap-1.5 text-red-400 font-bold text-sm">
                                    <TrendingDown className="w-3.5 h-3.5" />
                                    {item.current_stock}
                                </div>
                                <div className="text-[10px] text-white/40 mt-0.5 bg-red-500/10 px-1.5 py-0.5 rounded text-red-300">
                                    %{percentage} kaldı
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

        </div>
    );
}
