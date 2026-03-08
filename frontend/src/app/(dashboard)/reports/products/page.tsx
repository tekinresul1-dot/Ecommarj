"use client";

import { useState, useEffect } from "react";
import { formatCurrency, formatPercentage } from "@/lib/utils/format";
import apiClient from "@/lib/api/client";
import { Filter, Download, RefreshCw } from "lucide-react";
import clsx from "clsx";

import { TableFilter, FilterState, FilterColumn, applyTableFilter } from "@/components/dashboard/TableFilter";
import { DatePickerWithRange } from "@/components/dashboard/DateRangePicker";
import { DateRange } from "react-day-picker";
import { format, subDays } from "date-fns";

interface ProductAnalysis {
  id: string; // barcode used as id
  barcode: string;
  title: string;
  stock: number;
  model_code: string;
  category: string;
  total_sold_quantity: number;
  total_sales_amount: string;
  total_profit: string;
  return_cargo_loss: string;
  profit_margin: string;
  profit_rate: string;
}

const FILTER_COLUMNS: FilterColumn[] = [
  { id: "barcode", label: "Barkod", type: "text" },
  { id: "title", label: "Ürün Adı", type: "text" },
  { id: "model_code", label: "Model Kodu", type: "text" },
  { id: "category", label: "Kategori", type: "text" },
  { id: "stock", label: "Stok", type: "number" },
  { id: "total_sold_quantity", label: "Satılan Adet", type: "number" },
  { id: "total_sales_amount", label: "Satış Tutarı (₺)", type: "number" },
  { id: "total_profit", label: "Kâr Tutarı (₺)", type: "number" },
  { id: "profit_rate", label: "Kâr Oranı (%)", type: "number" },
  { id: "profit_margin", label: "Kâr Marjı (%)", type: "number" },
];

export default function ProductAnalysisPage() {
  const [products, setProducts] = useState<ProductAnalysis[]>([]);
  const [loading, setLoading] = useState(true);

  // Date Range State
  const [date, setDate] = useState<DateRange | undefined>({
    from: subDays(new Date(), 30),
    to: new Date(),
  });

  // Filtering State
  const [showFilter, setShowFilter] = useState(false);
  const [tableFilter, setTableFilter] = useState<FilterState | null>(null);

  useEffect(() => {
    handleDateFilter();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [date]);

  const fetchProducts = async (minDate?: string, maxDate?: string) => {
    setLoading(true);
    try {
      let url = "/reports/product-analysis/";
      if (minDate && maxDate) {
        url += `?min_date=${minDate}&max_date=${maxDate}`;
      }
      const result = await apiClient.get<ProductAnalysis[]>(url);
      if (result.ok && result.data) {
        setProducts(result.data);
      }
    } catch (error) {
      console.error("Product analysis fetch error:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDateFilter = () => {
    if (date?.from && date?.to) {
      fetchProducts(format(date.from, "yyyy-MM-dd"), format(date.to, "yyyy-MM-dd"));
    } else {
      fetchProducts();
    }
  };

  const filteredProducts = applyTableFilter(products, tableFilter);

  return (
    <div className="p-6">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
        <h1 className="text-2xl font-bold text-white tracking-tight">Ürün Analizi</h1>
        <div className="flex flex-wrap items-center gap-3">
          <DatePickerWithRange date={date} setDate={setDate} />
          <button
            onClick={handleDateFilter}
            className="flex items-center justify-center w-10 h-10 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors shadow-lg shadow-blue-900/20"
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
                ? "bg-blue-600/20 text-blue-400 border-blue-500/30 ring-1 ring-blue-500/10"
                : "bg-navy-800 hover:bg-navy-700 text-white/90 border-white/5"
            )}
          >
            <Filter className="w-4 h-4" />
            Tabloda Ara {(tableFilter) && <span className="w-2 h-2 rounded-full bg-blue-500 ml-1"></span>}
          </button>
          <button className="flex items-center gap-2 bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors shadow-lg shadow-green-900/20 h-10">
            <Download className="w-4 h-4" />
            İndir
          </button>
        </div>
      </div>

      {showFilter && (
        <div className="mb-4">
          <TableFilter
            columns={FILTER_COLUMNS}
            onApply={(f) => setTableFilter(f)}
            onClose={() => setShowFilter(false)}
          />
        </div>
      )}

      <div className="bg-navy-900 rounded-xl border border-white/5 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-white/80">
            <thead className="bg-navy-800/50 text-white border-b border-light-navy uppercase text-[10px] tracking-wider font-semibold">
              <tr>
                <th className="px-4 py-4 whitespace-nowrap">Barkod</th>
                <th className="px-4 py-4 whitespace-nowrap">Ürün Adı</th>
                <th className="px-4 py-4 whitespace-nowrap">Stok</th>
                <th className="px-4 py-4 whitespace-nowrap">Model Kodu</th>
                <th className="px-4 py-4 whitespace-nowrap">Kategori</th>
                <th className="px-4 py-4 whitespace-nowrap text-right">Satılan Adet</th>
                <th className="px-4 py-4 whitespace-nowrap text-right">Satış Tutarı (₺)</th>
                <th className="px-4 py-4 whitespace-nowrap text-right">Kâr Tutarı (₺)</th>
                <th className="px-4 py-4 whitespace-nowrap text-right">İade Kargo Zararı (₺)</th>
                <th className="px-4 py-4 whitespace-nowrap text-right">Kâr Oranı (%)</th>
                <th className="px-4 py-4 whitespace-nowrap text-right">Kâr Marjı (%)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {loading ? (
                <tr>
                  <td colSpan={11} className="px-6 py-8 text-center text-white/50">
                    <div className="flex justify-center items-center gap-3">
                      <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                      Ürün verileri yükleniyor...
                    </div>
                  </td>
                </tr>
              ) : filteredProducts.length === 0 ? (
                <tr>
                  <td colSpan={11} className="px-6 py-8 text-center text-white/50">
                    Ürün bulunamadı. Filtreleri temizlemeyi deneyin.
                  </td>
                </tr>
              ) : (
                filteredProducts.map((item) => {
                  const profitVal = parseFloat(item.total_profit);
                  const lossVal = parseFloat(item.return_cargo_loss);
                  const isProfitable = profitVal > 0;
                  const isLoss = profitVal < 0;

                  return (
                    <tr key={item.id} className="hover:bg-white/5 transition-colors group">
                      <td className="px-4 py-3 whitespace-nowrap font-medium text-white/90">
                        {item.barcode}
                      </td>
                      <td className="px-4 py-3 min-w-[200px] max-w-[300px] truncate" title={item.title}>
                        {item.title}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-white/70">
                        {item.stock}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-white/70">
                        {item.model_code || "-"}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-white/70">
                        {item.category || "-"}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right font-medium text-blue-400">
                        {item.total_sold_quantity}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right font-medium text-red-400">
                        {formatCurrency(parseFloat(item.total_sales_amount))}
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
                          lossVal > 0 ? "text-red-400" : "text-white/60"
                        )}>
                          {lossVal > 0 ? `-${formatCurrency(lossVal)}` : "₺0,00"}
                        </span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right">
                        <span className={clsx(
                          "font-medium",
                          isProfitable ? "text-green-400" : isLoss ? "text-red-400" : "text-white/80"
                        )}>
                          {formatPercentage(parseFloat(item.profit_rate))}
                        </span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right">
                        <span className={clsx(
                          "font-medium",
                          isProfitable ? "text-green-400" : isLoss ? "text-red-400" : "text-white/80"
                        )}>
                          {formatPercentage(parseFloat(item.profit_margin))}
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