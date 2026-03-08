"use client";

import { useState, useEffect } from "react";
import { formatCurrency, formatPercentage } from "@/lib/utils/format";
import apiClient from "@/lib/api/client";
import { Filter, Download, Layers, Calendar, RefreshCw } from "lucide-react";
import clsx from "clsx";

import { TableFilter, FilterState, FilterColumn, applyTableFilter } from "@/components/dashboard/TableFilter";
import { DatePickerWithRange } from "@/components/dashboard/DateRangePicker";
import { DateRange } from "react-day-picker";
import { format, subDays } from "date-fns";

interface CategoryAnalysis {
  id: string;
  category: string;
  product_count: number;
  total_sold_quantity: number;
  total_sales_amount: string;
  total_profit: string;
  total_commission: string;
  total_cargo: string;
  profit_margin: string;
}

const FILTER_COLUMNS: FilterColumn[] = [
  { id: "category", label: "Kategori Adı", type: "text" },
  { id: "product_count", label: "Ürün Sayısı", type: "number" },
  { id: "total_sold_quantity", label: "Satılan Adet", type: "number" },
  { id: "total_sales_amount", label: "Satış Tutarı (₺)", type: "number" },
  { id: "total_commission", label: "Komisyon (₺)", type: "number" },
  { id: "total_cargo", label: "Kargo (₺)", type: "number" },
  { id: "total_profit", label: "Kâr Tutarı (₺)", type: "number" },
  { id: "profit_margin", label: "Kâr Marjı (%)", type: "number" },
];

export default function CategoryAnalysisPage() {
  const [categories, setCategories] = useState<CategoryAnalysis[]>([]);
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

  const fetchCategories = async (minDate?: string, maxDate?: string) => {
    setLoading(true);
    try {
      let url = "/reports/categories/";
      if (minDate && maxDate) {
        url += `?min_date=${minDate}&max_date=${maxDate}`;
      }
      const result = await apiClient.get<CategoryAnalysis[]>(url);
      if (result.ok) {
        setCategories(result.data);
      }
    } catch (error) {
      console.error("Category analysis fetch error:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDateFilter = () => {
    if (date?.from && date?.to) {
      fetchCategories(format(date.from, "yyyy-MM-dd"), format(date.to, "yyyy-MM-dd"));
    } else {
      fetchCategories();
    }
  };

  const filteredCategories = applyTableFilter(categories, tableFilter);

  // Summary KPIs based on filtered data (or raw data depending on preference, usually raw data for top KPIs is better, but doing it on filtered is fine too. Let's do raw for full range insight)
  const totalSales = categories.reduce((s, c) => s + parseFloat(c.total_sales_amount), 0);
  const totalProfit = categories.reduce((s, c) => s + parseFloat(c.total_profit), 0);
  const totalSold = categories.reduce((s, c) => s + c.total_sold_quantity, 0);
  const avgMargin = totalSales > 0 ? (totalProfit / totalSales * 100) : 0;

  return (
    <div className="p-6">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20">
            <Layers className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Kategori Analizi</h1>
            <p className="text-xs text-white/40 mt-0.5">Kategorilere göre satış ve kârlılık dağılımı</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <DatePickerWithRange date={date} setDate={setDate} />
          <button
            onClick={handleDateFilter}
            className="flex items-center justify-center w-10 h-10 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-colors shadow-lg shadow-indigo-900/20"
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
                ? "bg-indigo-600/20 text-indigo-400 border-indigo-500/30 ring-1 ring-indigo-500/10"
                : "bg-navy-800 hover:bg-navy-700 text-white/90 border-white/5"
            )}
          >
            <Filter className="w-4 h-4" />
            Tabloyu Filtrele {(tableFilter) && <span className="w-2 h-2 rounded-full bg-indigo-500 ml-1"></span>}
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
      {!loading && categories.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-navy-900 border border-white/5 rounded-xl p-4">
            <p className="text-xs text-white/50 font-medium mb-1">Toplam Satış</p>
            <p className="text-xl font-bold text-white">{formatCurrency(totalSales)}</p>
          </div>
          <div className="bg-navy-900 border border-white/5 rounded-xl p-4">
            <p className="text-xs text-white/50 font-medium mb-1">Toplam Kâr</p>
            <p className={clsx("text-xl font-bold", totalProfit >= 0 ? "text-green-400" : "text-red-400")}>{formatCurrency(totalProfit)}</p>
          </div>
          <div className="bg-navy-900 border border-white/5 rounded-xl p-4">
            <p className="text-xs text-white/50 font-medium mb-1">Toplam Satılan Adet</p>
            <p className="text-xl font-bold text-blue-400">{totalSold.toLocaleString("tr-TR")}</p>
          </div>
          <div className="bg-navy-900 border border-white/5 rounded-xl p-4">
            <p className="text-xs text-white/50 font-medium mb-1">Ortalama Kâr Marjı</p>
            <p className={clsx("text-xl font-bold", avgMargin >= 0 ? "text-green-400" : "text-red-400")}>{formatPercentage(avgMargin)}</p>
          </div>
        </div>
      )}

      <div className="bg-navy-900 rounded-xl border border-white/5 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-white/80">
            <thead className="bg-navy-800/50 text-white border-b border-light-navy uppercase text-[10px] tracking-wider font-semibold">
              <tr>
                <th className="px-4 py-4 whitespace-nowrap">Kategori</th>
                <th className="px-4 py-4 whitespace-nowrap text-right">Ürün Sayısı</th>
                <th className="px-4 py-4 whitespace-nowrap text-right">Satılan Adet</th>
                <th className="px-4 py-4 whitespace-nowrap text-right">Satış Tutarı (₺)</th>
                <th className="px-4 py-4 whitespace-nowrap text-right">Komisyon (₺)</th>
                <th className="px-4 py-4 whitespace-nowrap text-right">Kargo (₺)</th>
                <th className="px-4 py-4 whitespace-nowrap text-right">Kâr Tutarı (₺)</th>
                <th className="px-4 py-4 whitespace-nowrap text-right">Kâr Marjı (%)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {loading ? (
                <tr>
                  <td colSpan={8} className="px-6 py-8 text-center text-white/50">
                    <div className="flex justify-center items-center gap-3">
                      <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                      Kategori verileri yükleniyor...
                    </div>
                  </td>
                </tr>
              ) : filteredCategories.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-8 text-center text-white/50">
                    Kayıt bulunamadı. Filtreleri temizlemeyi deneyin.
                  </td>
                </tr>
              ) : (
                filteredCategories.map((item) => {
                  const profitVal = parseFloat(item.total_profit);
                  const isProfitable = profitVal > 0;
                  const isLoss = profitVal < 0;
                  const marginVal = parseFloat(item.profit_margin);

                  return (
                    <tr key={item.id} className="hover:bg-white/5 transition-colors group">
                      <td className="px-4 py-3 whitespace-nowrap font-medium text-white/90">
                        {item.category}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right text-white/70">
                        {item.product_count}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right font-medium text-blue-400">
                        {item.total_sold_quantity}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right font-medium text-white/80">
                        {formatCurrency(parseFloat(item.total_sales_amount))}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right text-orange-400">
                        {formatCurrency(parseFloat(item.total_commission))}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right text-yellow-400">
                        {formatCurrency(parseFloat(item.total_cargo))}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right">
                        <span className={clsx(
                          "font-bold",
                          isProfitable ? "text-green-500" : isLoss ? "text-red-400" : "text-white/80"
                        )}>
                          {formatCurrency(profitVal)}
                        </span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right">
                        <span className={clsx(
                          "font-medium",
                          marginVal > 0 ? "text-green-400" : marginVal < 0 ? "text-red-400" : "text-white/80"
                        )}>
                          {formatPercentage(marginVal)}
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