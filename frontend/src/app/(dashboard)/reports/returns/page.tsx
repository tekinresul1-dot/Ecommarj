"use client";

import { useState, useEffect } from "react";
import { formatCurrency, formatPercentage } from "@/lib/utils/format";
import apiClient from "@/lib/api/client";
import { Filter, Download, RotateCcw, AlertTriangle, TrendingDown } from "lucide-react";
import clsx from "clsx";

interface ReturnSummary {
  total_orders: number;
  returned_orders: number;
  return_rate: string;
  total_return_cargo_loss: string;
  total_return_revenue_loss: string;
}

interface ReturnItem {
  barcode: string;
  title: string;
  category: string;
  return_count: number;
  cargo_loss: string;
  revenue_loss: string;
}

export default function ReturnAnalysisPage() {
  const [summary, setSummary] = useState<ReturnSummary | null>(null);
  const [items, setItems] = useState<ReturnItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchReturns();
  }, []);

  const fetchReturns = async () => {
    try {
      const result = await apiClient.get<{ summary: ReturnSummary; data: ReturnItem[] }>("/reports/returns/");
      if (result.ok && result.data) {
        setSummary(result.data.summary || null);
        setItems(result.data.data || []);
      }
    } catch (error) {
      console.error("Return analysis fetch error:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/20">
            <RotateCcw className="w-5 h-5 text-red-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">İade Zarar Analizi</h1>
            <p className="text-xs text-white/40 mt-0.5">İade edilen siparişlerin kargo ve gelir kayıpları</p>
          </div>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 bg-navy-800 hover:bg-navy-700 text-white/90 px-4 py-2 rounded-lg text-sm font-medium transition-colors border border-white/5">
            <Filter className="w-4 h-4" />
            Filtrele
          </button>
          <button className="flex items-center gap-2 bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors shadow-lg shadow-green-900/20">
            <Download className="w-4 h-4" />
            Raporu İndir
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      {!loading && summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-navy-900 border border-white/5 rounded-xl p-4">
            <p className="text-xs text-white/50 font-medium mb-1">Toplam Sipariş</p>
            <p className="text-xl font-bold text-white">{summary.total_orders.toLocaleString("tr-TR")}</p>
          </div>
          <div className="bg-navy-900 border border-white/5 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
              <p className="text-xs text-white/50 font-medium">İade Edilen Sipariş</p>
            </div>
            <p className="text-xl font-bold text-red-400">{summary.returned_orders.toLocaleString("tr-TR")}</p>
          </div>
          <div className="bg-navy-900 border border-white/5 rounded-xl p-4">
            <p className="text-xs text-white/50 font-medium mb-1">İade Oranı</p>
            <p className={clsx(
              "text-xl font-bold",
              parseFloat(summary.return_rate) > 15 ? "text-red-400" : parseFloat(summary.return_rate) > 5 ? "text-yellow-400" : "text-green-400"
            )}>
              {formatPercentage(parseFloat(summary.return_rate))}
            </p>
          </div>
          <div className="bg-navy-900 border border-white/5 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-1">
              <TrendingDown className="w-3.5 h-3.5 text-red-400" />
              <p className="text-xs text-white/50 font-medium">Toplam Kargo Zararı</p>
            </div>
            <p className="text-xl font-bold text-red-400">{formatCurrency(parseFloat(summary.total_return_cargo_loss))}</p>
          </div>
        </div>
      )}

      <div className="bg-navy-900 rounded-xl border border-white/5 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-white/80">
            <thead className="bg-navy-800/50 text-white border-b border-light-navy uppercase text-[10px] tracking-wider font-semibold">
              <tr>
                <th className="px-4 py-4 whitespace-nowrap">Barkod</th>
                <th className="px-4 py-4 whitespace-nowrap">Ürün Adı</th>
                <th className="px-4 py-4 whitespace-nowrap">Kategori</th>
                <th className="px-4 py-4 whitespace-nowrap text-right">İade Adedi</th>
                <th className="px-4 py-4 whitespace-nowrap text-right">Kargo Zararı (₺)</th>
                <th className="px-4 py-4 whitespace-nowrap text-right">Gelir Kaybı (₺)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-white/50">
                    <div className="flex justify-center items-center gap-3">
                      <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                      İade verileri yükleniyor...
                    </div>
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-white/50">
                    Henüz iade verisi bulunmuyor. İade siparişleri senkronizasyon ile gelecek.
                  </td>
                </tr>
              ) : (
                items.map((item) => {
                  const cargoLoss = parseFloat(item.cargo_loss);
                  const revenueLoss = parseFloat(item.revenue_loss);

                  return (
                    <tr key={item.barcode} className="hover:bg-white/5 transition-colors group">
                      <td className="px-4 py-3 whitespace-nowrap font-medium text-white/90">
                        {item.barcode}
                      </td>
                      <td className="px-4 py-3 min-w-[200px] max-w-[300px] truncate" title={item.title}>
                        {item.title}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-white/70">
                        {item.category || "-"}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right font-bold text-red-400">
                        {item.return_count}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right">
                        <span className={clsx("font-medium", cargoLoss > 0 ? "text-red-400" : "text-white/60")}>
                          {cargoLoss > 0 ? `-${formatCurrency(cargoLoss)}` : "₺0,00"}
                        </span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right">
                        <span className={clsx("font-medium", revenueLoss > 0 ? "text-orange-400" : "text-white/60")}>
                          {revenueLoss > 0 ? formatCurrency(revenueLoss) : "₺0,00"}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}