"use client";

import { useState, useEffect } from "react";
import { formatCurrency, formatPercentage } from "@/lib/utils/format";
import apiClient from "@/lib/api/client";
import { Filter, Download, TrendingUp, RefreshCw, Package } from "lucide-react";
import clsx from "clsx";

import { TableFilter, FilterState, FilterColumn, applyTableFilter } from "@/components/dashboard/TableFilter";
import { DatePickerWithRange } from "@/components/dashboard/DateRangePicker";
import { DateRange } from "react-day-picker";
import { format, subDays } from "date-fns";

// ─── Types ────────────────────────────────────────────────────────────────────

interface ProductProfitabilityItem {
  barcode: string;
  product_name: string;
  stock: number;
  model_code: string;
  category: string;
  order_count: number;
  total_sales: string;
  total_profit: string;
  return_cargo_loss: string;
  profit_rate: string;
  profit_margin: string;
  return_count: number;
}

interface Summary {
  total_sales: string;
  total_profit: string;
  total_return_loss: string;
  avg_profit_rate: string;
}

interface ApiResponse {
  results: ProductProfitabilityItem[];
  summary: Summary;
  date_range: { start_date: string; end_date: string };
}

// ─── Filter columns ───────────────────────────────────────────────────────────

const FILTER_COLUMNS: FilterColumn[] = [
  { id: "barcode", label: "Barkod", type: "text" },
  { id: "product_name", label: "Ürün Adı", type: "text" },
  { id: "stock", label: "Stok", type: "number" },
  { id: "model_code", label: "Model Kodu", type: "text" },
  { id: "category", label: "Kategori", type: "text" },
  { id: "order_count", label: "Satış Adedi", type: "number" },
  { id: "total_sales", label: "Satış Tutarı (₺)", type: "number" },
  { id: "total_profit", label: "Kâr Tutarı (₺)", type: "number" },
  { id: "return_cargo_loss", label: "İade Kargo Zararı (₺)", type: "number" },
  { id: "profit_rate", label: "Kâr Oranı (%)", type: "number" },
  { id: "profit_margin", label: "Kâr Marjı (%)", type: "number" },
];

// ─── Sort helper ──────────────────────────────────────────────────────────────

type SortKey = keyof ProductProfitabilityItem;

function sortItems(
  items: ProductProfitabilityItem[],
  key: SortKey,
  desc: boolean
): ProductProfitabilityItem[] {
  return [...items].sort((a, b) => {
    const av = a[key];
    const bv = b[key];
    const an = parseFloat(String(av));
    const bn = parseFloat(String(bv));
    let cmp = 0;
    if (!isNaN(an) && !isNaN(bn)) {
      cmp = an - bn;
    } else {
      cmp = String(av).localeCompare(String(bv), "tr");
    }
    return desc ? -cmp : cmp;
  });
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function ProductProfitabilityPage() {
  const [items, setItems] = useState<ProductProfitabilityItem[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);

  // Date range
  const [date, setDate] = useState<DateRange | undefined>({
    from: subDays(new Date(), 30),
    to: new Date(),
  });

  // Filter & sort
  const [showFilter, setShowFilter] = useState(false);
  const [tableFilter, setTableFilter] = useState<FilterState | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>("total_sales");
  const [sortDesc, setSortDesc] = useState(true);

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [date]);

  const fetchData = async () => {
    setLoading(true);
    try {
      let url = "/reports/product-profitability/";
      if (date?.from && date?.to) {
        const start = format(date.from, "yyyy-MM-dd");
        const end = format(date.to, "yyyy-MM-dd");
        url += `?start_date=${start}&end_date=${end}`;
      }
      const result = await apiClient.get<ApiResponse>(url);
      if (result.ok && result.data) {
        setItems(result.data.results || []);
        setSummary(result.data.summary || null);
      }
    } catch (error) {
      console.error("Product profitability fetch error:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDesc((prev) => !prev);
    } else {
      setSortKey(key);
      setSortDesc(true);
    }
  };

  const filteredItems = applyTableFilter(items, tableFilter);
  const sortedItems = sortItems(filteredItems, sortKey, sortDesc);

  // Summary KPIs
  const totalSales = items.reduce((s, i) => s + parseFloat(i.total_sales), 0);
  const totalProfit = items.reduce((s, i) => s + parseFloat(i.total_profit), 0);
  const totalReturnLoss = items.reduce((s, i) => s + parseFloat(i.return_cargo_loss), 0);
  const avgProfitRate = totalSales > 0 ? (totalProfit / totalSales) * 100 : 0;

  // Excel export
  const handleExport = () => {
    if (sortedItems.length === 0) return;
    const headers = [
      "Barkod", "Ürün Adı", "Stok", "Model Kodu", "Kategori",
      "Satış Adedi", "Satış Tutarı (₺)", "Kâr Tutarı (₺)",
      "İade Kargo Zararı (₺)", "Kâr Oranı (%)", "Kâr Marjı (%)",
    ];
    const rows = sortedItems.map((r) => [
      r.barcode, r.product_name, r.stock, r.model_code, r.category,
      r.order_count, r.total_sales, r.total_profit,
      r.return_cargo_loss, r.profit_rate, r.profit_margin,
    ]);
    const csv = [headers, ...rows]
      .map((row) => row.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(","))
      .join("\n");
    const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const startStr = date?.from ? format(date.from, "yyyy-MM-dd") : "baslangic";
    const endStr = date?.to ? format(date.to, "yyyy-MM-dd") : "bitis";
    a.download = `urun-karlilik-analizi-${startStr}-${endStr}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Sort indicator helper
  const sortIndicator = (key: SortKey) =>
    sortKey === key ? (sortDesc ? " ↓" : " ↑") : "";

  const thClass = (key: SortKey) =>
    clsx(
      "px-4 py-4 whitespace-nowrap text-right cursor-pointer select-none hover:text-white/80 transition-colors",
      sortKey === key ? "text-blue-400" : ""
    );

  const thClassLeft = (key: SortKey) =>
    clsx(
      "px-4 py-4 whitespace-nowrap cursor-pointer select-none hover:text-white/80 transition-colors",
      sortKey === key ? "text-blue-400" : ""
    );

  return (
    <div className="p-6">
      {/* ── Header ── */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
            <TrendingUp className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Ürün Kârlılık Analizi</h1>
            <p className="text-xs text-white/40 mt-0.5">Ürün bazlı satış, kâr ve iade kargo zararı analizi</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <DatePickerWithRange date={date} setDate={setDate} />
          <button
            onClick={fetchData}
            className="flex items-center justify-center w-10 h-10 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg transition-colors shadow-lg shadow-emerald-900/20"
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
                ? "bg-emerald-600/20 text-emerald-400 border-emerald-500/30 ring-1 ring-emerald-500/10"
                : "bg-navy-800 hover:bg-navy-700 text-white/90 border-white/5"
            )}
          >
            <Filter className="w-4 h-4" />
            Tabloyu Filtrele {tableFilter && <span className="w-2 h-2 rounded-full bg-emerald-500 ml-1"></span>}
          </button>

          <button
            onClick={handleExport}
            disabled={sortedItems.length === 0}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors border h-10 bg-green-600 hover:bg-green-500 text-white border-green-500 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Download className="w-4 h-4" />
            Raporu İndir
          </button>
        </div>
      </div>

      {/* ── TableFilter ── */}
      {showFilter && (
        <div className="mb-6">
          <TableFilter
            columns={FILTER_COLUMNS}
            onApply={(f) => setTableFilter(f)}
            onClose={() => setShowFilter(false)}
          />
        </div>
      )}

      {/* ── Summary Cards ── */}
      {!loading && items.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-navy-900 border border-white/5 rounded-xl p-4">
            <p className="text-xs text-white/50 font-medium mb-1">Toplam Satış</p>
            <p className="text-xl font-bold text-white">{formatCurrency(totalSales)}</p>
          </div>
          <div className="bg-navy-900 border border-white/5 rounded-xl p-4">
            <p className="text-xs text-white/50 font-medium mb-1">Toplam Kâr</p>
            <p className={clsx("text-xl font-bold", totalProfit >= 0 ? "text-green-400" : "text-red-400")}>
              {formatCurrency(totalProfit)}
            </p>
          </div>
          <div className="bg-navy-900 border border-white/5 rounded-xl p-4">
            <p className="text-xs text-white/50 font-medium mb-1">İade Kargo Zararı</p>
            <p className="text-xl font-bold text-orange-400">{formatCurrency(totalReturnLoss)}</p>
          </div>
          <div className="bg-navy-900 border border-white/5 rounded-xl p-4">
            <p className="text-xs text-white/50 font-medium mb-1">Ortalama Kâr Oranı</p>
            <p className={clsx("text-xl font-bold", avgProfitRate >= 0 ? "text-green-400" : "text-red-400")}>
              {formatPercentage(avgProfitRate)}
            </p>
          </div>
        </div>
      )}

      {/* ── Table ── */}
      <div className="bg-navy-900 rounded-xl border border-white/5 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-white/80">
            <thead className="bg-navy-800/50 text-white border-b border-light-navy uppercase text-[10px] tracking-wider font-semibold">
              <tr>
                <th
                  className={thClassLeft("barcode")}
                  onClick={() => handleSort("barcode")}
                >
                  Barkod{sortIndicator("barcode")}
                </th>
                <th
                  className={thClassLeft("product_name")}
                  onClick={() => handleSort("product_name")}
                >
                  Ürün Adı{sortIndicator("product_name")}
                </th>
                <th
                  className={thClass("stock")}
                  onClick={() => handleSort("stock")}
                >
                  Stok{sortIndicator("stock")}
                </th>
                <th
                  className={thClassLeft("model_code")}
                  onClick={() => handleSort("model_code")}
                >
                  Model Kodu{sortIndicator("model_code")}
                </th>
                <th
                  className={thClassLeft("category")}
                  onClick={() => handleSort("category")}
                >
                  Kategori{sortIndicator("category")}
                </th>
                <th
                  className={thClass("order_count")}
                  onClick={() => handleSort("order_count")}
                >
                  Satış Adedi{sortIndicator("order_count")}
                </th>
                <th
                  className={thClass("total_sales")}
                  onClick={() => handleSort("total_sales")}
                >
                  Satış Tutarı (₺){sortIndicator("total_sales")}
                </th>
                <th
                  className={thClass("total_profit")}
                  onClick={() => handleSort("total_profit")}
                >
                  Kâr Tutarı (₺){sortIndicator("total_profit")}
                </th>
                <th
                  className={thClass("return_cargo_loss")}
                  onClick={() => handleSort("return_cargo_loss")}
                >
                  İade Kargo Zararı (₺){sortIndicator("return_cargo_loss")}
                </th>
                <th
                  className={thClass("profit_rate")}
                  onClick={() => handleSort("profit_rate")}
                >
                  Kâr Oranı (%){sortIndicator("profit_rate")}
                </th>
                <th
                  className={thClass("profit_margin")}
                  onClick={() => handleSort("profit_margin")}
                >
                  Kâr Marjı (%){sortIndicator("profit_margin")}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {loading ? (
                <tr>
                  <td colSpan={11} className="px-6 py-8 text-center text-white/50">
                    <div className="flex justify-center items-center gap-3">
                      <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                      Ürün kârlılık verileri yükleniyor...
                    </div>
                  </td>
                </tr>
              ) : sortedItems.length === 0 ? (
                <tr>
                  <td colSpan={11} className="px-6 py-12 text-center text-white/50">
                    <div className="flex flex-col items-center gap-3">
                      <Package className="w-8 h-8 opacity-30" />
                      <p>
                        {tableFilter
                          ? "Filtreyle eşleşen ürün bulunamadı."
                          : "Seçili tarih aralığında ürün bulunamadı."}
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                sortedItems.map((item, idx) => {
                  const profitVal = parseFloat(item.total_profit);
                  const rateVal = parseFloat(item.profit_rate);
                  const marginVal = parseFloat(item.profit_margin);

                  return (
                    <tr key={`${item.barcode}-${idx}`} className="hover:bg-white/5 transition-colors group">
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className="font-mono text-xs text-white/60 bg-white/5 px-2 py-0.5 rounded">
                          {item.barcode}
                        </span>
                      </td>
                      <td className="px-4 py-3 max-w-[200px]">
                        <span
                          className="font-medium text-white/90 line-clamp-2 leading-tight block"
                          title={item.product_name}
                        >
                          {item.product_name}
                        </span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right">
                        <span className={clsx(
                          "font-semibold",
                          item.stock === 0 ? "text-red-400" :
                          item.stock < 20  ? "text-yellow-400" :
                          "text-green-400"
                        )}>
                          {item.stock}
                        </span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap font-mono text-xs text-indigo-300">
                        {item.model_code || "—"}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-white/60 text-xs">
                        {item.category || "—"}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right font-medium text-blue-400">
                        {item.order_count.toLocaleString("tr-TR")}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right font-medium text-white/80">
                        {formatCurrency(parseFloat(item.total_sales))}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right">
                        <span className={clsx(
                          "font-bold",
                          profitVal > 0 ? "text-green-500" : profitVal < 0 ? "text-red-400" : "text-white/80"
                        )}>
                          {formatCurrency(profitVal)}
                        </span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right text-orange-400">
                        {formatCurrency(parseFloat(item.return_cargo_loss))}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right">
                        <span className={clsx(
                          "font-medium",
                          rateVal > 0 ? "text-green-400" : rateVal < 0 ? "text-red-400" : "text-white/80"
                        )}>
                          {formatPercentage(rateVal)}
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
