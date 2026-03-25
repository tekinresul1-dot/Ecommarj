"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { formatCurrency, formatPercentage } from "@/lib/utils/format";
import apiClient from "@/lib/api/client";
import {
  Filter, Download, RefreshCw, Package, Maximize2,
  ChevronDown, ArrowUpDown,
} from "lucide-react";
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

interface ApiResponse {
  results: ProductProfitabilityItem[];
  summary: {
    total_sales: string;
    total_profit: string;
    total_return_loss: string;
    avg_profit_rate: string;
  };
  date_range: { start_date: string; end_date: string };
}

type SortKey = keyof ProductProfitabilityItem;

// ─── Report list for dropdown ─────────────────────────────────────────────────

const REPORTS = [
  { label: "Ürün Kârlılık Analizi", href: "/reports/product-analysis" },
  { label: "Kategori Analizi",       href: "/reports/categories" },
  { label: "Sipariş Analizi",        href: "/reports/orders" },
  { label: "İade Zarar Analizi",     href: "/reports/returns" },
  { label: "Reklam Analizi",         href: "/reports/ads" },
];

// ─── Filter columns ───────────────────────────────────────────────────────────

const FILTER_COLUMNS: FilterColumn[] = [
  { id: "barcode",           label: "Barkod",                  type: "text"   },
  { id: "product_name",      label: "Ürün Adı",                type: "text"   },
  { id: "stock",             label: "Stok",                    type: "number" },
  { id: "model_code",        label: "Model Kodu",              type: "text"   },
  { id: "category",          label: "Kategori",                type: "text"   },
  { id: "order_count",       label: "Satış Adedi",             type: "number" },
  { id: "total_sales",       label: "Satış Tutarı (₺)",        type: "number" },
  { id: "total_profit",      label: "Kâr Tutarı (₺)",          type: "number" },
  { id: "return_cargo_loss", label: "İade Kargo Zararı (₺)",   type: "number" },
  { id: "profit_rate",       label: "Kâr Oranı (%)",           type: "number" },
  { id: "profit_margin",     label: "Kâr Marjı (%)",           type: "number" },
];

// ─── Sort helper ──────────────────────────────────────────────────────────────

function sortItems(
  items: ProductProfitabilityItem[],
  key: SortKey,
  desc: boolean
): ProductProfitabilityItem[] {
  return [...items].sort((a, b) => {
    const av = a[key], bv = b[key];
    const an = parseFloat(String(av)), bn = parseFloat(String(bv));
    let cmp = !isNaN(an) && !isNaN(bn) ? an - bn : String(av).localeCompare(String(bv), "tr");
    return desc ? -cmp : cmp;
  });
}

// ─── Font size presets ────────────────────────────────────────────────────────

const FONT_SIZES = [
  { label: "A−", value: "text-xs" },
  { label: "A",  value: "text-sm" },
  { label: "A+", value: "text-base" },
];

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function ProductAnalysisPage() {
  const router = useRouter();
  const tableRef = useRef<HTMLDivElement>(null);

  const [items, setItems] = useState<ProductProfitabilityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [date, setDate] = useState<DateRange | undefined>({
    from: subDays(new Date(), 30),
    to: new Date(),
  });

  const [showFilter, setShowFilter] = useState(false);
  const [tableFilter, setTableFilter] = useState<FilterState | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>("total_sales");
  const [sortDesc, setSortDesc] = useState(true);
  const [fontSizeIdx, setFontSizeIdx] = useState(1); // default "A" = text-sm
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Report dropdown
  const [reportDropOpen, setReportDropOpen] = useState(false);
  const currentReport = REPORTS[0];

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [date]);

  const fetchData = async () => {
    setLoading(true);
    try {
      let url = "/reports/product-profitability/";
      if (date?.from && date?.to) {
        url += `?start_date=${format(date.from, "yyyy-MM-dd")}&end_date=${format(date.to, "yyyy-MM-dd")}`;
      }
      const result = await apiClient.get<ApiResponse>(url);
      if (result.ok && result.data) {
        setItems(result.data.results || []);
      }
    } catch (err) {
      console.error("Product analysis fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortDesc((p) => !p);
    else { setSortKey(key); setSortDesc(true); }
  };

  const filteredItems = applyTableFilter(items, tableFilter);
  const sortedItems = sortItems(filteredItems, sortKey, sortDesc);

  const handleExport = () => {
    if (!sortedItems.length) return;
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
    a.download = `urun-karlilik-analizi-${format(date?.from || new Date(), "yyyy-MM-dd")}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      tableRef.current?.requestFullscreen?.();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen?.();
      setIsFullscreen(false);
    }
  };

  // Sort indicator
  const si = (key: SortKey) => sortKey === key ? (sortDesc ? " ↓" : " ↑") : "";

  const thCls = (key: SortKey, align: "left" | "right" = "right") =>
    clsx(
      "px-3 py-3 whitespace-nowrap cursor-pointer select-none hover:bg-orange-600/20 transition-colors",
      align === "right" ? "text-right" : "text-left",
      sortKey === key ? "text-orange-300" : ""
    );

  const fontSize = FONT_SIZES[fontSizeIdx].value;

  return (
    <div className="p-6">

      {/* ── Top bar: Report selector + Date range ── */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-5">

        {/* Left: Rapor Seçin dropdown */}
        <div className="flex items-center gap-3">
          <span className="text-sm text-white/50 font-medium whitespace-nowrap">Rapor Seçin:</span>
          <div className="relative">
            <button
              onClick={() => setReportDropOpen((p) => !p)}
              className="flex items-center gap-2 px-4 py-2 bg-navy-800 hover:bg-navy-700 border border-white/10 rounded-lg text-sm font-medium text-white transition-colors h-10 min-w-[220px]"
            >
              <span className="flex-1 text-left">{currentReport.label}</span>
              <ChevronDown className={clsx("w-4 h-4 text-white/40 transition-transform", reportDropOpen && "rotate-180")} />
            </button>
            {reportDropOpen && (
              <div className="absolute z-50 top-full mt-1 left-0 min-w-[220px] bg-navy-900 border border-white/10 rounded-xl shadow-2xl overflow-hidden">
                {REPORTS.map((r) => (
                  <button
                    key={r.href}
                    onClick={() => { setReportDropOpen(false); if (r.href !== "/reports/product-analysis") router.push(r.href); }}
                    className={clsx(
                      "w-full text-left px-4 py-2.5 text-sm transition-colors",
                      r.href === "/reports/product-analysis"
                        ? "bg-orange-500/10 text-orange-300 font-medium"
                        : "text-white/70 hover:bg-white/5 hover:text-white"
                    )}
                  >
                    {r.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right: Date range + Refresh */}
        <div className="flex items-center gap-3">
          <DatePickerWithRange date={date} setDate={setDate} />
          <button
            onClick={fetchData}
            className="flex items-center justify-center w-10 h-10 bg-orange-600 hover:bg-orange-500 text-white rounded-lg transition-colors shadow-lg shadow-orange-900/20"
            title="Yenile"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* ── Orange header bar ── */}
      <div className="bg-orange-600 rounded-t-xl px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-white font-bold text-base tracking-tight">Ürün Kârlılık Analizi</span>
          {!loading && (
            <span className="text-orange-200 text-xs font-medium bg-orange-700/40 px-2 py-0.5 rounded-full">
              {sortedItems.length} ürün
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {/* Filter toggle */}
          <button
            onClick={() => setShowFilter((p) => !p)}
            className={clsx(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border",
              showFilter || tableFilter
                ? "bg-white/20 text-white border-white/30"
                : "bg-orange-700/40 text-orange-100 border-orange-500/30 hover:bg-orange-700/60"
            )}
          >
            <Filter className="w-3.5 h-3.5" />
            Filtrele
            {tableFilter && <span className="w-1.5 h-1.5 rounded-full bg-white ml-0.5" />}
          </button>

          {/* Font size controls */}
          <div className="flex items-center border border-orange-500/30 rounded-lg overflow-hidden">
            {FONT_SIZES.map((fs, i) => (
              <button
                key={fs.label}
                onClick={() => setFontSizeIdx(i)}
                className={clsx(
                  "px-2.5 py-1.5 text-xs font-bold transition-colors",
                  fontSizeIdx === i
                    ? "bg-white/20 text-white"
                    : "text-orange-200 hover:bg-orange-700/40"
                )}
              >
                {fs.label}
              </button>
            ))}
          </div>

          {/* Fullscreen */}
          <button
            onClick={toggleFullscreen}
            className="flex items-center justify-center w-8 h-8 rounded-lg bg-orange-700/40 hover:bg-orange-700/60 text-orange-100 transition-colors border border-orange-500/30"
            title="Tam ekran"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* ── Sub-header: Download button ── */}
      <div className="bg-navy-800/80 border-x border-white/5 px-4 py-2 flex items-center justify-end">
        <button
          onClick={handleExport}
          disabled={!sortedItems.length}
          className="flex items-center gap-2 px-4 py-1.5 rounded-lg text-xs font-semibold transition-colors bg-green-600 hover:bg-green-500 text-white border border-green-500 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <Download className="w-3.5 h-3.5" />
          Raporu İndir
        </button>
      </div>

      {/* ── TableFilter panel ── */}
      {showFilter && (
        <div className="border-x border-white/5 bg-navy-900">
          <div className="p-4">
            <TableFilter
              columns={FILTER_COLUMNS}
              onApply={(f) => setTableFilter(f)}
              onClose={() => setShowFilter(false)}
            />
          </div>
        </div>
      )}

      {/* ── Table ── */}
      <div
        ref={tableRef}
        className={clsx(
          "bg-navy-900 border border-white/5 rounded-b-xl overflow-hidden",
          isFullscreen && "bg-navy-900 p-4"
        )}
      >
        <div className="overflow-x-auto">
          <table className={clsx("w-full text-left text-white/80", fontSize)}>
            <thead className="bg-orange-600/10 text-white border-b border-orange-500/20 uppercase text-[10px] tracking-wider font-semibold">
              <tr>
                <th className={thCls("barcode", "left")} onClick={() => handleSort("barcode")}>
                  <span className="flex items-center gap-1">Barkod<ArrowUpDown className="w-3 h-3 opacity-50"/>{si("barcode")}</span>
                </th>
                <th className={thCls("product_name", "left")} onClick={() => handleSort("product_name")}>
                  <span className="flex items-center gap-1">Ürün Adı<ArrowUpDown className="w-3 h-3 opacity-50"/>{si("product_name")}</span>
                </th>
                <th className={thCls("stock")} onClick={() => handleSort("stock")}>
                  <span className="flex items-center justify-end gap-1">Stok<ArrowUpDown className="w-3 h-3 opacity-50"/>{si("stock")}</span>
                </th>
                <th className={thCls("model_code", "left")} onClick={() => handleSort("model_code")}>
                  <span className="flex items-center gap-1">Model Kodu<ArrowUpDown className="w-3 h-3 opacity-50"/>{si("model_code")}</span>
                </th>
                <th className={thCls("category", "left")} onClick={() => handleSort("category")}>
                  <span className="flex items-center gap-1">Kategori<ArrowUpDown className="w-3 h-3 opacity-50"/>{si("category")}</span>
                </th>
                <th className={thCls("order_count")} onClick={() => handleSort("order_count")}>
                  <span className="flex items-center justify-end gap-1">Satış Adedi<ArrowUpDown className="w-3 h-3 opacity-50"/>{si("order_count")}</span>
                </th>
                <th className={thCls("total_sales")} onClick={() => handleSort("total_sales")}>
                  <span className="flex items-center justify-end gap-1">Satış Tutarı<ArrowUpDown className="w-3 h-3 opacity-50"/>{si("total_sales")}</span>
                </th>
                <th className={thCls("total_profit")} onClick={() => handleSort("total_profit")}>
                  <span className="flex items-center justify-end gap-1">Kâr Tutarı<ArrowUpDown className="w-3 h-3 opacity-50"/>{si("total_profit")}</span>
                </th>
                <th className={thCls("return_cargo_loss")} onClick={() => handleSort("return_cargo_loss")}>
                  <span className="flex items-center justify-end gap-1">İade Kargo Zararı<ArrowUpDown className="w-3 h-3 opacity-50"/>{si("return_cargo_loss")}</span>
                </th>
                <th className={thCls("profit_rate")} onClick={() => handleSort("profit_rate")}>
                  <span className="flex items-center justify-end gap-1">Kâr Oranı %<ArrowUpDown className="w-3 h-3 opacity-50"/>{si("profit_rate")}</span>
                </th>
                <th className={thCls("profit_margin")} onClick={() => handleSort("profit_margin")}>
                  <span className="flex items-center justify-end gap-1">Kâr Marjı %<ArrowUpDown className="w-3 h-3 opacity-50"/>{si("profit_margin")}</span>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {loading ? (
                <tr>
                  <td colSpan={11} className="px-6 py-10 text-center text-white/50">
                    <div className="flex justify-center items-center gap-3">
                      <div className="w-5 h-5 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
                      Veriler yükleniyor...
                    </div>
                  </td>
                </tr>
              ) : sortedItems.length === 0 ? (
                <tr>
                  <td colSpan={11} className="px-6 py-14 text-center text-white/40">
                    <div className="flex flex-col items-center gap-3">
                      <Package className="w-8 h-8 opacity-25" />
                      <p>{tableFilter ? "Filtreyle eşleşen ürün bulunamadı." : "Seçili tarih aralığında ürün bulunamadı."}</p>
                    </div>
                  </td>
                </tr>
              ) : (
                sortedItems.map((item, idx) => {
                  const profitVal  = parseFloat(item.total_profit);
                  const rateVal    = parseFloat(item.profit_rate);
                  const marginVal  = parseFloat(item.profit_margin);

                  return (
                    <tr key={`${item.barcode}-${idx}`} className="hover:bg-orange-500/5 transition-colors">
                      {/* Barkod */}
                      <td className="px-3 py-2.5 whitespace-nowrap">
                        <span className="font-mono text-xs text-white/50 bg-white/5 px-1.5 py-0.5 rounded">
                          {item.barcode}
                        </span>
                      </td>

                      {/* Ürün Adı */}
                      <td className="px-3 py-2.5 max-w-[200px]">
                        <button
                          className="text-left font-medium text-white/90 hover:text-orange-300 transition-colors line-clamp-2 leading-tight"
                          title={item.product_name}
                          onClick={() => {/* future: navigate to product detail */}}
                        >
                          {item.product_name}
                        </button>
                      </td>

                      {/* Stok */}
                      <td className="px-3 py-2.5 whitespace-nowrap text-right">
                        <span className={clsx(
                          "font-semibold",
                          item.stock === 0 ? "text-red-400" :
                          item.stock < 20  ? "text-yellow-400" :
                          "text-green-400"
                        )}>
                          {item.stock}
                        </span>
                      </td>

                      {/* Model Kodu */}
                      <td className="px-3 py-2.5 whitespace-nowrap font-mono text-xs text-indigo-300">
                        {item.model_code || "—"}
                      </td>

                      {/* Kategori */}
                      <td className="px-3 py-2.5 whitespace-nowrap text-white/55 text-xs">
                        {item.category || "—"}
                      </td>

                      {/* Satış Adedi */}
                      <td className="px-3 py-2.5 whitespace-nowrap text-right font-medium text-blue-400">
                        {item.order_count.toLocaleString("tr-TR")}
                      </td>

                      {/* Satış Tutarı */}
                      <td className="px-3 py-2.5 whitespace-nowrap text-right font-medium text-white/80">
                        {formatCurrency(parseFloat(item.total_sales))}
                      </td>

                      {/* Kâr Tutarı */}
                      <td className="px-3 py-2.5 whitespace-nowrap text-right">
                        <span className={clsx(
                          "font-bold",
                          profitVal > 0 ? "text-green-500" : profitVal < 0 ? "text-red-400" : "text-white/70"
                        )}>
                          {formatCurrency(profitVal)}
                        </span>
                      </td>

                      {/* İade Kargo Zararı */}
                      <td className="px-3 py-2.5 whitespace-nowrap text-right text-orange-400">
                        {formatCurrency(parseFloat(item.return_cargo_loss))}
                      </td>

                      {/* Kâr Oranı % */}
                      <td className="px-3 py-2.5 whitespace-nowrap text-right">
                        <span className={clsx(
                          "font-medium",
                          rateVal > 0 ? "text-green-400" : rateVal < 0 ? "text-red-400" : "text-white/70"
                        )}>
                          {formatPercentage(rateVal)}
                        </span>
                      </td>

                      {/* Kâr Marjı % */}
                      <td className="px-3 py-2.5 whitespace-nowrap text-right">
                        <span className={clsx(
                          "font-medium",
                          marginVal > 0 ? "text-green-400" : marginVal < 0 ? "text-red-400" : "text-white/70"
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
