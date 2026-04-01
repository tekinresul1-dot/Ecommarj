"use client";

import { useState, useEffect } from "react";
import { formatCurrency, formatPercentage } from "@/lib/utils/format";
import apiClient from "@/lib/api/client";
import { Megaphone, TrendingUp, DollarSign, BarChart3, Target, RefreshCw } from "lucide-react";
import clsx from "clsx";

import { DatePickerWithRange } from "@/components/dashboard/DateRangePicker";
import { DateRange } from "react-day-picker";
import { format, subDays } from "date-fns";

interface AdsSummary {
  total_advertising: string;
  total_influencer: string;
  total_expense: string;
  total_sales: string;
  total_profit: string;
  advertising_sales_ratio: string;
  advertising_profit_ratio: string;
}

interface AdsTransaction {
  date: string;
  type: string;
  transaction_type: string;
  amount: string;
  description: string;
}

interface AdsData {
  summary: AdsSummary;
  transactions: AdsTransaction[];
}

export default function AdsAnalysisPage() {
  const [data, setData] = useState<AdsData | null>(null);
  const [loading, setLoading] = useState(true);

  const [date, setDate] = useState<DateRange | undefined>({
    from: subDays(new Date(), 30),
    to: new Date(),
  });

  useEffect(() => {
    handleDateFilter();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [date]);

  const fetchAds = async (minDate?: string, maxDate?: string) => {
    setLoading(true);
    try {
      let url = "/reports/ads/";
      if (minDate && maxDate) url += `?min_date=${minDate}&max_date=${maxDate}`;
      const result = await apiClient.get<AdsData>(url);
      if (result.ok && result.data?.summary) {
        setData(result.data);
      }
    } catch (error) {
      console.error("Ads analysis fetch error:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDateFilter = () => {
    if (date?.from && date?.to) {
      fetchAds(format(date.from, "yyyy-MM-dd"), format(date.to, "yyyy-MM-dd"));
    } else {
      fetchAds();
    }
  };

  const s = data?.summary;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20">
            <Megaphone className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Reklam Analizi</h1>
            <p className="text-xs text-white/40 mt-0.5">Reklam harcamaları, satış ve kârlılık performansı</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <DatePickerWithRange date={date} setDate={setDate} />
          <button
            onClick={handleDateFilter}
            className="flex items-center justify-center w-10 h-10 bg-purple-600 hover:bg-purple-500 text-white rounded-lg transition-colors shadow-lg shadow-purple-900/20"
            title="Verileri Güncelle"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center py-20">
          <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : !s ? (
        <div className="bg-navy-900 border border-white/5 rounded-xl p-8 text-center text-white/50">
          Reklam verisi bulunamadı.
        </div>
      ) : (
        <>
          {/* Metrics Table */}
          <div className="bg-navy-900 rounded-xl border border-white/5 overflow-hidden mb-6">
            <table className="w-full text-left text-sm">
              <thead className="bg-navy-800/50 text-white border-b border-white/10 uppercase text-[10px] tracking-wider font-semibold">
                <tr>
                  <th className="px-6 py-4">Metrik</th>
                  <th className="px-6 py-4 text-right">Değer</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                <MetricRow icon={<DollarSign className="w-4 h-4 text-red-400" />}
                  label="Toplam Reklam Harcaması" value={formatCurrency(parseFloat(s.total_advertising))} valueColor="text-red-400" />
                <MetricRow icon={<Target className="w-4 h-4 text-pink-400" />}
                  label="İnfluencer Reklam Kesintisi" value={formatCurrency(parseFloat(s.total_influencer))} valueColor="text-pink-400" />
                <MetricRow icon={<DollarSign className="w-4 h-4 text-orange-400" />}
                  label="Toplam Reklam Gideri" value={formatCurrency(parseFloat(s.total_expense))} valueColor="text-orange-400" />
                <MetricRow icon={<TrendingUp className="w-4 h-4 text-blue-400" />}
                  label="Toplam Satış" value={formatCurrency(parseFloat(s.total_sales))} valueColor="text-blue-400" />
                <MetricRow icon={<DollarSign className="w-4 h-4 text-green-400" />}
                  label="Net Kâr" value={formatCurrency(parseFloat(s.total_profit))}
                  valueColor={parseFloat(s.total_profit) >= 0 ? "text-green-400" : "text-red-400"} />
                <MetricRow icon={<BarChart3 className="w-4 h-4 text-orange-400" />}
                  label="Reklam / Satış Oranı" value={formatPercentage(parseFloat(s.advertising_sales_ratio))} valueColor="text-orange-400" />
                <MetricRow icon={<BarChart3 className="w-4 h-4 text-yellow-400" />}
                  label="Reklam / Kâr Oranı" value={formatPercentage(parseFloat(s.advertising_profit_ratio))} valueColor="text-yellow-400" />
              </tbody>
            </table>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
            <div className="bg-gradient-to-br from-red-500/10 to-red-600/5 border border-red-500/10 rounded-xl p-5">
              <p className="text-xs text-white/50 font-medium mb-2">Toplam Reklam Harcaması</p>
              <p className="text-2xl font-bold text-red-400">{formatCurrency(parseFloat(s.total_expense))}</p>
            </div>
            <div className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 border border-blue-500/10 rounded-xl p-5">
              <p className="text-xs text-white/50 font-medium mb-2">Toplam Satış</p>
              <p className="text-2xl font-bold text-blue-400">{formatCurrency(parseFloat(s.total_sales))}</p>
            </div>
            <div className="bg-gradient-to-br from-green-500/10 to-green-600/5 border border-green-500/10 rounded-xl p-5">
              <p className="text-xs text-white/50 font-medium mb-2">Net Kâr</p>
              <p className={clsx("text-2xl font-bold", parseFloat(s.total_profit) >= 0 ? "text-green-400" : "text-red-400")}>
                {formatCurrency(parseFloat(s.total_profit))}
              </p>
            </div>
          </div>

          {/* Transactions Table */}
          <div className="bg-navy-900 rounded-xl border border-white/5 overflow-hidden">
            <div className="px-4 py-3 border-b border-white/5 text-sm font-medium text-white/70">
              Reklam Gider Kayıtları
            </div>
            <table className="w-full text-[13px] text-left text-white/80">
              <thead className="bg-navy-800/50 text-white border-b border-white/10 uppercase text-[10px] tracking-wider font-semibold">
                <tr>
                  <th className="px-4 py-2 whitespace-nowrap">Tarih</th>
                  <th className="px-4 py-2 whitespace-nowrap">Gider Türü</th>
                  <th className="px-4 py-2 whitespace-nowrap">İşlem Tipi</th>
                  <th className="px-4 py-2 whitespace-nowrap">Açıklama</th>
                  <th className="px-4 py-2 whitespace-nowrap text-right">Tutar</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {!data?.transactions || data.transactions.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-white/40">
                      Reklam gider kaydı bulunamadı.{" "}
                      <span className="text-white/25 text-xs">
                        (Trendyol finance API bağlantısı kurulduğunda otomatik dolar.)
                      </span>
                    </td>
                  </tr>
                ) : (
                  data.transactions.map((txn, i) => (
                    <tr key={i} className="hover:bg-white/5 transition-colors">
                      <td className="px-4 py-2 whitespace-nowrap text-white/60">{txn.date}</td>
                      <td className="px-4 py-2 whitespace-nowrap">
                        <span className={clsx(
                          "px-2 py-0.5 rounded text-[11px] font-medium",
                          txn.transaction_type === "INFLUENCER" || txn.type?.includes("nfluencer")
                            ? "text-pink-400 bg-pink-400/10"
                            : "text-purple-400 bg-purple-400/10"
                        )}>
                          {txn.type}
                        </span>
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-white/50 text-[12px]">{txn.transaction_type}</td>
                      <td className="px-4 py-2 text-white/60 truncate max-w-[200px]">{txn.description || "-"}</td>
                      <td className="px-4 py-2 whitespace-nowrap text-right font-semibold text-red-400">
                        -{formatCurrency(parseFloat(txn.amount))}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

function MetricRow({
  icon, label, value, valueColor = "text-white",
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
      <td className={clsx("px-6 py-4 text-right font-bold text-lg", valueColor)}>{value}</td>
    </tr>
  );
}
