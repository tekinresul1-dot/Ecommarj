"use client";

import { useState, useEffect } from "react";
import { formatCurrency, formatPercentage } from "@/lib/utils/format";
import apiClient from "@/lib/api/client";
import { Filter, Calendar, RotateCcw, AlertTriangle, TrendingDown, BarChart3, RefreshCw } from "lucide-react";
import clsx from "clsx";

import { TableFilter, FilterState, FilterColumn, applyTableFilter } from "@/components/dashboard/TableFilter";
import { DatePickerWithRange } from "@/components/dashboard/DateRangePicker";
import { DateRange } from "react-day-picker";
import { format, subDays } from "date-fns";

interface ReturnSummary {
  total_orders: number;
  returned_orders: number;
  return_rate: string;
  total_return_cargo_loss: string;
  total_return_revenue_loss: string;
  return_to_sales_ratio: string;
}

interface ReturnItem {
  barcode: string;
  title: string;
  category: string;
  return_count: number;
  cargo_loss: string;
  revenue_loss: string;
}

const FILTER_COLUMNS: FilterColumn[] = [
  { id: "barcode", label: "Barkod", type: "text" },
  { id: "title", label: "Ürün Adı", type: "text" },
  { id: "category", label: "Kategori", type: "text" },
  { id: "return_count", label: "İade Adedi", type: "number" },
  { id: "cargo_loss", label: "Kargo Zararı (₺)", type: "number" },
  { id: "revenue_loss", label: "Gelir Kaybı (₺)", type: "number" },
];

export default function ReturnAnalysisPage() {
  const [summary, setSummary] = useState<ReturnSummary | null>(null);
  const [items, setItems] = useState<ReturnItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Date Range State
  const [date, setDate] = useState<DateRange | undefined>({
    from: subDays(new Date(), 30),
    to: new Date(),
  });

  // Table Filtering State
  const [showFilter, setShowFilter] = useState(false);
  const [tableFilter, setTableFilter] = useState<FilterState | null>(null);

  useEffect(() => {
    handleDateFilter();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [date]);

  const fetchReturns = async (minDate?: string, maxDate?: string) => {
    setLoading(true);
    try {
      let url = "/reports/returns/";
      if (minDate && maxDate) {
        url += `?min_date=${minDate}&max_date=${maxDate}`;
      }
      const result = await apiClient.get<{ summary: ReturnSummary; data: ReturnItem[] }>(url);
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

  const handleDateFilter = () => {
    if (date?.from && date?.to) {
      fetchReturns(format(date.from, "yyyy-MM-dd"), format(date.to, "yyyy-MM-dd"));
    } else {
      fetchReturns();
    }
  };

  const filteredItems = applyTableFilter(items, tableFilter);

  return (
    <div className="p-6">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/20">
            <RotateCcw className="w-5 h-5 text-red-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">İade Zarar Analizi</h1>
            <p className="text-xs text-white/40 mt-0.5">İade edilen siparişlerin kargo ve gelir kayıpları</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <DatePickerWithRange date={date} setDate={setDate} />
          <button
            onClick={handleDateFilter}
            className="flex items-center justify-center w-10 h-10 bg-red-600 hover:bg-red-500 text-white rounded-lg transition-colors shadow-lg shadow-red-900/20"
            title="Verileri Güncelle"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          <div className="w-px h-8 bg-white/10 mx-1 hidden sm:block"></div>

          <button
            onClick={() => setShowFilter(!showFilter)}
            className={clsx(
              "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors border h-10",
              showFilter || tableFilter
                ? "bg-red-600/20 text-red-400 border-red-500/30 ring-1 ring-red-500/10"
                : "bg-navy-800 hover:bg-navy-700 text-white/90 border-white/5"
            )}
          >
            <Filter className="w-4 h-4" />
            Tabloyu Filtrele {(tableFilter) && <span className="w-2 h-2 rounded-full bg-red-500 ml-1"></span>}
          </button>
        </div>
      </div>

      {showFilter && (
        <div className="mb-6">
          <TableFilter
            columns={FILTER_COLUMNS}
            onApply={(f) => setTableFilter(f)}
            onClose={() => setShowFilter(false)}
          />
        </div>
      )}

      {/* Summary Cards */}
      {!loading && summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
          <div className="bg-navy-900 border border-white/5 rounded-xl p-4">
            <p className="text-xs text-white/50 font-medium mb-1">Toplam Sipariş</p>
            <p className="text-xl font-bold text-white">{summary.total_orders.toLocaleString("tr-TR")}</p>
          </div>
          <div className="bg-navy-900 border border-white/5 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
              <p className="text-xs text-white/50 font-medium">İade Sipariş Sayısı</p>
            </div>
            <p className="text-xl font-bold text-red-400">{summary.returned_orders.toLocaleString("tr-TR")}</p>
          </div>
          <div className="bg-navy-900 border border-white/5 rounded-xl p-4">
            <p className="text-xs text-white/50 font-medium mb-1">Toplam İade Tutarı</p>
            <p className="text-xl font-bold text-orange-400">{formatCurrency(parseFloat(summary.total_return_revenue_loss))}</p>
          </div>
          <div className="bg-navy-900 border border-white/5 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-1">
              <TrendingDown className="w-3.5 h-3.5 text-red-400" />
              <p className="text-xs text-white/50 font-medium">İade Kargo Zararı</p>
            </div>
            <p className="text-xl font-bold text-red-400">{formatCurrency(parseFloat(summary.total_return_cargo_loss))}</p>
          </div>
          <div className="bg-navy-900 border border-white/5 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-1">
              <BarChart3 className="w-3.5 h-3.5 text-yellow-400" />
              <p className="text-xs text-white/50 font-medium">İade / Satış Oranı</p>
            </div>
            <p className={clsx(
              "text-xl font-bold",
              parseFloat(summary.return_to_sales_ratio) > 15 ? "text-red-400" : parseFloat(summary.return_to_sales_ratio) > 5 ? "text-yellow-400" : "text-green-400"
            )}>
              {formatPercentage(parseFloat(summary.return_to_sales_ratio))}
            </p>
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
              ) : filteredItems.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-white/50">
                    Kayıt bulunamadı.
                  </td>
                </tr>
              ) : (
                filteredItems.map((item) => {
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