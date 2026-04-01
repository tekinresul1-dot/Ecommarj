"use client";

import { useState, useEffect, useCallback } from "react";
import { formatCurrency, formatPercentage } from "@/lib/utils/format";
import apiClient from "@/lib/api/client";
import {
  Filter,
  Download,
  RefreshCw,
  Package,
  ChevronUp,
  ChevronDown,
  ChevronsUpDown,
} from "lucide-react";
import clsx from "clsx";
import { TableFilter, FilterState, FilterColumn, applyTableFilter } from "@/components/dashboard/TableFilter";
import { DatePickerWithRange } from "@/components/dashboard/DateRangePicker";
import { DateRange } from "react-day-picker";
import { format, subDays } from "date-fns";

interface ProductProfitability {
  barcode: string;
  title: string;
  stock: number;
  model_code: string;
  category: string;
  total_sold_quantity: number;
  total_sales_amount: string;
  total_profit: string;
  return_cargo_loss: string;
  profit_rate: string;
  profit_margin: string;
}

type SortKey = keyof ProductProfitability;
type SortDir = "asc" | "desc";

const FILTER_COLUMNS: FilterColumn[] = [
  { id: "barcode", label: "Barkod", type: "text" },
  { id: "title", label: "Ürün Adı", type: "text" },
  { id: "model_code", label: "Model Kodu", type: "text" },
  { id: "category", label: "Kategori", type: "text" },
  { id: "stock", label: "Stok", type: "number" },
  { id: "total_sold_quantity", label: "Satış Adedi", type: "number" },
  { id: "total_sales_amount", label: "Satış Tutarı (₺)", type: "number" },
  { id: "total_profit", label: "Kâr Tutarı (₺)", type: "number" },
  { id: "return_cargo_loss", label: "İade Kargo Zararı (₺)", type: "number" },
  { id: "profit_rate", label: "Kâr Oranı (%)", type: "number" },
  { id: "profit_margin", label: "Kâr Marjı (%)", type: "number" },
];

const COLUMNS: { key: SortKey; label: string; align?: "right" }[] = [
  { key: "barcode", label: "Barkod" },
  { key: "title", label: "Ürün Adı" },
  { key: "stock", label: "Stok", align: "right" },
  { key: "model_code", label: "Model Kodu" },
  { key: "category", label: "Kategori" },
  { key: "total_sold_quantity", label: "Satış Adedi", align: "right" },
  { key: "total_sales_amount", label: "Satış Tutarı", align: "right" },
  { key: "total_profit", label: "Kâr Tutarı", align: "right" },
  { key: "return_cargo_loss", label: "İade Kargo Zararı", align: "right" },
  { key: "profit_rate", label: "Kâr Oranı (%)", align: "right" },
  { key: "profit_margin", label: "Kâr Marjı (%)", align: "right" },
];

function sortProducts(
  data: ProductProfitability[],
  key: SortKey,
  dir: SortDir
): ProductProfitability[] {
  return [...data].sort((a, b) => {
    const numericKeys: SortKey[] = [
      "stock",
      "total_sold_quantity",
      "total_sales_amount",
      "total_profit",
      "return_cargo_loss",
      "profit_rate",
      "profit_margin",
    ];
    let valA: number | string;
    let valB: number | string;
    if (numericKeys.includes(key)) {
      valA = parseFloat(String(a[key])) || 0;
      valB = parseFloat(String(b[key])) || 0;
    } else {
      valA = String(a[key] ?? "").toLowerCase();
      valB = String(b[key] ?? "").toLowerCase();
    }
    if (valA < valB) return dir === "asc" ? -1 : 1;
    if (valA > valB) return dir === "asc" ? 1 : -1;
    return 0;
  });
}

function SortIcon({ col, sortKey, sortDir }: { col: SortKey; sortKey: SortKey | null; sortDir: SortDir }) {
  if (sortKey !== col) return <ChevronsUpDown className="w-3 h-3 ml-1 opacity-30" />;
  return sortDir === "asc"
    ? <ChevronUp className="w-3 h-3 ml-1 text-blue-400" />
    : <ChevronDown className="w-3 h-3 ml-1 text-blue-400" />;
}

export default function ProductProfitabilityPage() {
  const [products, setProducts] = useState<ProductProfitability[]>([]);
  const [loading, setLoading] = useState(true);
  const [isExporting, setIsExporting] = useState(false);

  const [date, setDate] = useState<DateRange | undefined>({
    from: subDays(new Date(), 30),
    to: new Date(),
  });

  const [showFilter, setShowFilter] = useState(false);
  const [tableFilter, setTableFilter] = useState<FilterState | null>(null);

  const [sortKey, setSortKey] = useState<SortKey | null>("total_profit");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const fetchProducts = useCallback(async (minDate?: string, maxDate?: string) => {
    setLoading(true);
    try {
      let url = "/reports/product-analysis/";
      const params: string[] = [];
      if (minDate) params.push(`min_date=${minDate}`);
      if (maxDate) params.push(`max_date=${maxDate}`);
      if (params.length) url += "?" + params.join("&");

      // apiClient extracts data.data automatically, so result.data is ProductProfitability[]
      const result = await apiClient.get<ProductProfitability[]>(url);
      if (result.ok && Array.isArray(result.data)) {
        setProducts(result.data);
      }
    } catch (error) {
      console.error("Product profitability fetch error:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleDateFilter = useCallback(() => {
    if (date?.from && date?.to) {
      fetchProducts(format(date.from, "yyyy-MM-dd"), format(date.to, "yyyy-MM-dd"));
    } else {
      fetchProducts();
    }
  }, [date, fetchProducts]);

  useEffect(() => {
    handleDateFilter();
  }, [handleDateFilter]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  };

  const handleExcelExport = async () => {
    setIsExporting(true);
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : "";
      let url = "/api/reports/product-profitability/export-excel/";
      const params: string[] = [];
      if (date?.from) params.push(`min_date=${format(date.from, "yyyy-MM-dd")}`);
      if (date?.to) params.push(`max_date=${format(date.to, "yyyy-MM-dd")}`);
      if (params.length) url += "?" + params.join("&");

      const res = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error("Export başarısız");
      const blob = await res.blob();
      const blobUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = "Urun_Karliligi.xlsx";
      link.click();
      URL.revokeObjectURL(blobUrl);
    } catch (err) {
      console.error("Excel export error:", err);
    } finally {
      setIsExporting(false);
    }
  };

  const filtered = applyTableFilter(products, tableFilter);
  const sorted = sortKey ? sortProducts(filtered, sortKey, sortDir) : filtered;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <Package className="w-5 h-5 text-green-400" />
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Ürün Kârlılık Analizi</h1>
            <p className="text-xs text-white/40">Ürün bazında satış ve kârlılık özeti</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <DatePickerWithRange date={date} setDate={setDate} />

          <button
            onClick={handleDateFilter}
            className="flex items-center justify-center w-10 h-10 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors shadow-lg shadow-blue-900/20"
            title="Verileri Güncelle"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          <div className="w-px h-8 bg-white/10 mx-1 hidden sm:block" />

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
            Tabloda Ara
            {tableFilter && <span className="w-2 h-2 rounded-full bg-blue-500 ml-1" />}
          </button>

          <button
            onClick={handleExcelExport}
            disabled={isExporting}
            className="flex items-center gap-2 bg-green-600 hover:bg-green-500 disabled:opacity-60 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors shadow-lg shadow-green-900/20 h-10"
          >
            <Download className="w-4 h-4" />
            {isExporting ? "İndiriliyor..." : "Raporu İndir"}
          </button>
        </div>
      </div>

      {/* Filter panel */}
      {showFilter && (
        <div className="mb-4">
          <TableFilter
            columns={FILTER_COLUMNS}
            onApply={(f) => setTableFilter(f)}
            onClose={() => setShowFilter(false)}
          />
        </div>
      )}

      {/* Summary row */}
      {!loading && sorted.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
          <div className="bg-navy-900 border border-white/5 rounded-xl px-4 py-3">
            <p className="text-[10px] text-white/40 uppercase tracking-wider mb-1">Ürün Sayısı</p>
            <p className="text-xl font-bold text-white">{sorted.length.toLocaleString("tr-TR")}</p>
          </div>
          <div className="bg-navy-900 border border-white/5 rounded-xl px-4 py-3">
            <p className="text-[10px] text-white/40 uppercase tracking-wider mb-1">Toplam Satış</p>
            <p className="text-xl font-bold text-white">
              {sorted.reduce((s, p) => s + p.total_sold_quantity, 0).toLocaleString("tr-TR")}
            </p>
          </div>
          <div className="bg-navy-900 border border-white/5 rounded-xl px-4 py-3">
            <p className="text-[10px] text-white/40 uppercase tracking-wider mb-1">Toplam Satış Tutarı</p>
            <p className="text-xl font-bold text-white">
              {formatCurrency(sorted.reduce((s, p) => s + parseFloat(p.total_sales_amount), 0))}
            </p>
          </div>
          <div className="bg-navy-900 border border-white/5 rounded-xl px-4 py-3">
            <p className="text-[10px] text-white/40 uppercase tracking-wider mb-1">Toplam Kâr</p>
            {(() => {
              const totalProfit = sorted.reduce((s, p) => s + parseFloat(p.total_profit), 0);
              return (
                <p className={clsx("text-xl font-bold", totalProfit >= 0 ? "text-green-400" : "text-red-400")}>
                  {formatCurrency(totalProfit)}
                </p>
              );
            })()}
          </div>
        </div>
      )}

      {/* Table */}
      <div className="bg-navy-900 rounded-xl border border-white/5 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full table-fixed text-[13px] text-left text-white/80">
            <colgroup>
              <col style={{ width: "120px" }} />  {/* Barkod */}
              <col />                              {/* Ürün Adı — kalan alan */}
              <col style={{ width: "70px" }} />   {/* Stok */}
              <col style={{ width: "130px" }} />  {/* Model Kodu */}
              <col style={{ width: "130px" }} />  {/* Kategori */}
              <col style={{ width: "90px" }} />   {/* Satış Adedi */}
              <col style={{ width: "110px" }} />  {/* Satış Tutarı */}
              <col style={{ width: "110px" }} />  {/* Kâr Tutarı */}
              <col style={{ width: "100px" }} />  {/* İade Kargo Zararı */}
              <col style={{ width: "90px" }} />   {/* Kâr Oranı */}
              <col style={{ width: "90px" }} />   {/* Kâr Marjı */}
            </colgroup>
            <thead className="bg-navy-800/50 text-white border-b border-white/5 uppercase text-[10px] tracking-wider font-semibold">
              <tr>
                {COLUMNS.map((col) => (
                  <th
                    key={col.key}
                    onClick={() => handleSort(col.key)}
                    className={clsx(
                      "px-2 py-2 whitespace-nowrap cursor-pointer select-none",
                      "hover:bg-white/5 transition-colors",
                      col.align === "right" && "text-right"
                    )}
                  >
                    <span className={clsx("inline-flex items-center gap-0.5", col.align === "right" && "flex-row-reverse")}>
                      {col.label}
                      <SortIcon col={col.key} sortKey={sortKey} sortDir={sortDir} />
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {loading ? (
                <tr>
                  <td colSpan={11} className="px-6 py-10 text-center text-white/50">
                    <div className="flex justify-center items-center gap-3">
                      <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                      Ürün verileri yükleniyor...
                    </div>
                  </td>
                </tr>
              ) : sorted.length === 0 ? (
                <tr>
                  <td colSpan={11} className="px-6 py-10 text-center text-white/50">
                    Ürün bulunamadı. Tarih aralığını veya filtreleri değiştirmeyi deneyin.
                  </td>
                </tr>
              ) : (
                sorted.map((item) => {
                  const profitVal = parseFloat(item.total_profit);
                  const lossVal = parseFloat(item.return_cargo_loss);
                  const profitRateVal = parseFloat(item.profit_rate);
                  const profitMarginVal = parseFloat(item.profit_margin);
                  const isProfit = profitVal > 0;
                  const isLoss = profitVal < 0;

                  return (
                    <tr key={item.barcode} className="hover:bg-white/5 transition-colors group">
                      {/* Barkod */}
                      <td className="px-2 py-1.5 font-mono text-xs text-white/70 overflow-hidden">
                        <span className="truncate block" title={item.barcode}>{item.barcode}</span>
                      </td>

                      {/* Ürün Adı */}
                      <td className="px-2 py-1.5 overflow-hidden">
                        <span
                          className="truncate block text-white/90 group-hover:text-white cursor-pointer hover:text-blue-400 transition-colors"
                          title={item.title}
                          onClick={() => {
                            const encoded = encodeURIComponent(item.barcode);
                            window.location.href = `/product-settings?barcode=${encoded}`;
                          }}
                        >
                          {item.title}
                        </span>
                      </td>

                      {/* Stok */}
                      <td className="px-2 py-1.5 text-right text-white/70 whitespace-nowrap">
                        {item.stock.toLocaleString("tr-TR")}
                      </td>

                      {/* Model Kodu */}
                      <td className="px-2 py-1.5 text-white/60 overflow-hidden">
                        <span className="truncate block" title={item.model_code}>
                          {item.model_code || <span className="text-white/30">—</span>}
                        </span>
                      </td>

                      {/* Kategori */}
                      <td className="px-2 py-1.5 text-white/60 overflow-hidden">
                        <span className="truncate block" title={item.category}>
                          {item.category || <span className="text-white/30">—</span>}
                        </span>
                      </td>

                      {/* Satış Adedi */}
                      <td className="px-2 py-1.5 text-right font-medium text-blue-400 whitespace-nowrap">
                        {item.total_sold_quantity.toLocaleString("tr-TR")}
                      </td>

                      {/* Satış Tutarı */}
                      <td className="px-2 py-1.5 text-right font-medium text-white/80 whitespace-nowrap">
                        {formatCurrency(parseFloat(item.total_sales_amount))}
                      </td>

                      {/* Kâr Tutarı */}
                      <td className="px-2 py-1.5 text-right whitespace-nowrap">
                        <span className={clsx("font-bold", isProfit ? "text-green-400" : isLoss ? "text-red-400" : "text-white/80")}>
                          {formatCurrency(profitVal)}
                        </span>
                      </td>

                      {/* İade Kargo Zararı */}
                      <td className="px-2 py-1.5 text-right whitespace-nowrap">
                        <span className={clsx("font-medium", lossVal > 0 ? "text-red-400" : "text-white/40")}>
                          {lossVal > 0 ? `-${formatCurrency(lossVal)}` : "—"}
                        </span>
                      </td>

                      {/* Kâr Oranı */}
                      <td className="px-2 py-1.5 text-right whitespace-nowrap">
                        <span className={clsx("font-medium", isProfit ? "text-green-400" : isLoss ? "text-red-400" : "text-white/70")}>
                          {formatPercentage(profitRateVal)}
                        </span>
                      </td>

                      {/* Kâr Marjı */}
                      <td className="px-2 py-1.5 text-right whitespace-nowrap">
                        <span className={clsx("font-medium", isProfit ? "text-green-400" : isLoss ? "text-red-400" : "text-white/70")}>
                          {formatPercentage(profitMarginVal)}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        {!loading && sorted.length > 0 && (
          <div className="px-4 py-3 border-t border-white/5 flex items-center justify-between">
            <p className="text-xs text-white/40">
              {sorted.length.toLocaleString("tr-TR")} ürün gösteriliyor
              {tableFilter ? ` (filtre uygulandı)` : ""}
            </p>
            <p className="text-xs text-white/30">
              {date?.from && date?.to
                ? `${format(date.from, "dd.MM.yyyy")} – ${format(date.to, "dd.MM.yyyy")}`
                : ""}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
