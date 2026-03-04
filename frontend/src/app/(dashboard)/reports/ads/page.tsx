"use client";

import { useState, useEffect } from "react";
import { formatCurrency, formatPercentage } from "@/lib/utils/format";
import apiClient from "@/lib/api/client";
import { Filter, Calendar, Megaphone, TrendingUp, DollarSign, BarChart3, Target } from "lucide-react";
import clsx from "clsx";

interface AdsData {
  total_ads_cost: string;
  influencer_cost: string;
  total_sales: string;
  total_profit: string;
  ads_to_sales_ratio: string;
  ads_to_profit_ratio: string;
}

export default function AdsAnalysisPage() {
  const [data, setData] = useState<AdsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  useEffect(() => {
    fetchAds();
  }, []);

  const fetchAds = async (minDate?: string, maxDate?: string) => {
    setLoading(true);
    try {
      let url = "/reports/ads/";
      if (minDate && maxDate) {
        url += `?min_date=${minDate}&max_date=${maxDate}`;
      }
      const result = await apiClient.get<AdsData>(url);
      if (result.ok && result.data) {
        setData(result.data);
      }
    } catch (error) {
      console.error("Ads analysis fetch error:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilter = () => {
    if (startDate && endDate) {
      fetchAds(startDate, endDate);
    } else {
      fetchAds();
    }
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20">
            <Megaphone className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Reklam Analizi</h1>
            <p className="text-xs text-white/40 mt-0.5">Reklam harcamaları, satış ve kârlılık performansı</p>
          </div>
        </div>
      </div>

      {/* Date Filter Bar */}
      <div className="bg-navy-900 border border-white/5 rounded-xl p-4 mb-6 flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-white/40" />
          <span className="text-sm text-white/50 font-medium">Tarih Aralığı:</span>
        </div>
        <input
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          className="bg-navy-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white/80 focus:outline-none focus:border-purple-500/50 transition-colors"
        />
        <span className="text-white/30">—</span>
        <input
          type="date"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
          className="bg-navy-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white/80 focus:outline-none focus:border-purple-500/50 transition-colors"
        />
        <button
          onClick={handleFilter}
          className="flex items-center gap-2 bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          <Filter className="w-4 h-4" />
          Filtrele
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center items-center py-20">
          <div className="w-8 h-8 border-3 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : !data ? (
        <div className="bg-navy-900 border border-white/5 rounded-xl p-8 text-center text-white/50">
          Reklam verisi bulunamadı.
        </div>
      ) : (
        <>
          {/* Metrics Table */}
          <div className="bg-navy-900 rounded-xl border border-white/5 overflow-hidden">
            <table className="w-full text-left text-sm">
              <thead className="bg-navy-800/50 text-white border-b border-light-navy uppercase text-[10px] tracking-wider font-semibold">
                <tr>
                  <th className="px-6 py-4">Metrik</th>
                  <th className="px-6 py-4 text-right">Değer</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                <MetricTableRow
                  icon={<DollarSign className="w-4 h-4 text-red-400" />}
                  label="Toplam Reklam Harcaması"
                  value={formatCurrency(parseFloat(data.total_ads_cost))}
                  valueColor="text-red-400"
                />
                <MetricTableRow
                  icon={<Target className="w-4 h-4 text-pink-400" />}
                  label="İnfluencer Reklam Kesintisi"
                  value={formatCurrency(parseFloat(data.influencer_cost))}
                  valueColor="text-pink-400"
                />
                <MetricTableRow
                  icon={<TrendingUp className="w-4 h-4 text-blue-400" />}
                  label="Reklamlardan Gelen Satış Tutarı"
                  value={formatCurrency(parseFloat(data.total_sales))}
                  valueColor="text-blue-400"
                />
                <MetricTableRow
                  icon={<DollarSign className="w-4 h-4 text-green-400" />}
                  label="Kâr Tutarı"
                  value={formatCurrency(parseFloat(data.total_profit))}
                  valueColor={parseFloat(data.total_profit) >= 0 ? "text-green-400" : "text-red-400"}
                />
                <MetricTableRow
                  icon={<BarChart3 className="w-4 h-4 text-orange-400" />}
                  label="Reklam / Satış Oranı"
                  value={formatPercentage(parseFloat(data.ads_to_sales_ratio))}
                  valueColor="text-orange-400"
                />
                <MetricTableRow
                  icon={<BarChart3 className="w-4 h-4 text-yellow-400" />}
                  label="Reklam / Kâr Oranı"
                  value={formatPercentage(parseFloat(data.ads_to_profit_ratio))}
                  valueColor="text-yellow-400"
                />
              </tbody>
            </table>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6">
            <div className="bg-gradient-to-br from-red-500/10 to-red-600/5 border border-red-500/10 rounded-xl p-5">
              <p className="text-xs text-white/50 font-medium mb-2">Toplam Reklam Harcaması</p>
              <p className="text-2xl font-bold text-red-400">{formatCurrency(parseFloat(data.total_ads_cost))}</p>
            </div>
            <div className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 border border-blue-500/10 rounded-xl p-5">
              <p className="text-xs text-white/50 font-medium mb-2">Toplam Satış</p>
              <p className="text-2xl font-bold text-blue-400">{formatCurrency(parseFloat(data.total_sales))}</p>
            </div>
            <div className="bg-gradient-to-br from-green-500/10 to-green-600/5 border border-green-500/10 rounded-xl p-5">
              <p className="text-xs text-white/50 font-medium mb-2">Net Kâr</p>
              <p className={clsx(
                "text-2xl font-bold",
                parseFloat(data.total_profit) >= 0 ? "text-green-400" : "text-red-400"
              )}>
                {formatCurrency(parseFloat(data.total_profit))}
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function MetricTableRow({
  icon,
  label,
  value,
  valueColor = "text-white",
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  valueColor?: string;
}) {
  return (
    <tr className="hover:bg-white/5 transition-colors">
      <td className="px-6 py-4">
        <div className="flex items-center gap-3">
          {icon}
          <span className="text-white/80 font-medium">{label}</span>
        </div>
      </td>
      <td className={clsx("px-6 py-4 text-right font-bold text-lg", valueColor)}>
        {value}
      </td>
    </tr>
  );
}