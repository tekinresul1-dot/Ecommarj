"use client";

import { useEffect, useState, useCallback, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, BarChart, Bar, Cell
} from "recharts";
import {
  TrendingUp, TrendingDown, DollarSign, Wallet, Activity,
  AlertTriangle, Lightbulb, ShieldAlert, ChevronDown, ChevronUp,
  Filter, X, Search, ArrowUpDown, Clock, Package,
  AlertCircle, Info, Loader2
} from "lucide-react";
import clsx from "clsx";
import { api } from "@/lib/api";

// ── Helpers ─────────────────────────────────────────────────────────
const formatTR = (val: number | string) => {
  const num = typeof val === "string" ? parseFloat(val) : val;
  if (isNaN(num)) return "₺0,00";
  return new Intl.NumberFormat("tr-TR", { style: "currency", currency: "TRY" }).format(num);
};

const formatPct = (val: number | string) => {
  const num = typeof val === "string" ? parseFloat(val) : val;
  if (isNaN(num)) return "%0";
  return `%${num.toFixed(2)}`;
};

const formatTime = (iso: string) => {
  try {
    const d = new Date(iso);
    return d.toLocaleString("tr-TR", {
      day: "2-digit", month: "short", year: "numeric",
      hour: "2-digit", minute: "2-digit",
    });
  } catch {
    return iso;
  }
};

// ── Types ───────────────────────────────────────────────────────────
interface LiveData {
  kpis: {
    total_revenue: string;
    net_profit: string;
    profit_margin: string;
    net_cash_inflow: string;
    order_count: number;
    avg_order_profit: string;
  };
  orders: OrderRow[];
  hourly_performance: HourlyEntry[];
  product_heatmap: HeatmapEntry[];
  insights: InsightEntry[];
  pagination: { page: number; page_size: number; total_count: number };
}

interface OrderRow {
  order_number: string;
  order_date: string;
  product_name: string;
  sale_price: string;
  cost: string;
  commission: string;
  cargo_cost: string;
  tax: string;
  net_profit: string;
  profit_margin: string;
  return_risk: "low" | "medium" | "high";
  status: string;
  cost_breakdown: Record<string, string>;
}

interface HourlyEntry {
  hour: string;
  revenue: string;
  profit: string;
  order_count: number;
}

interface HeatmapEntry {
  product_name: string;
  category: string;
  total_sales: number;
  total_revenue: string;
  total_profit: string;
  margin: string;
  return_rate: string;
}

interface InsightEntry {
  type: "danger" | "warning" | "suggestion";
  title: string;
  message: string;
  product_name: string;
}

// ── KPI Card ────────────────────────────────────────────────────────
function KpiCard({ label, value, icon: Icon, color }: {
  label: string; value: string; icon: any; color: string;
}) {
  return (
    <div className="relative overflow-hidden bg-navy-900 border border-white/10 rounded-xl p-5 shadow-sm hover:border-white/20 transition-all group">
      <div className="absolute top-0 right-0 w-24 h-24 opacity-5 group-hover:opacity-10 transition-opacity">
        <Icon className="w-full h-full" />
      </div>
      <p className="text-xs font-semibold text-white/50 mb-1.5 uppercase tracking-wider">{label}</p>
      <h3 className={clsx("text-2xl font-bold tracking-tight", color)}>{value}</h3>
    </div>
  );
}

// ── Return Risk Badge ───────────────────────────────────────────────
function RiskBadge({ risk }: { risk: "low" | "medium" | "high" }) {
  const config = {
    low: { label: "Düşük", cls: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20" },
    medium: { label: "Orta", cls: "bg-amber-500/15 text-amber-400 border-amber-500/20" },
    high: { label: "Yüksek", cls: "bg-rose-500/15 text-rose-400 border-rose-500/20" },
  };
  const c = config[risk];
  return (
    <span className={clsx("inline-flex items-center text-[11px] font-semibold px-2 py-0.5 rounded-full border", c.cls)}>
      {c.label}
    </span>
  );
}

// ── Cost Breakdown Tooltip ──────────────────────────────────────────
function CostTooltip({ breakdown, children }: { breakdown: Record<string, string>; children: React.ReactNode }) {
  const [show, setShow] = useState(false);
  return (
    <div className="relative" onMouseEnter={() => setShow(true)} onMouseLeave={() => setShow(false)}>
      {children}
      {show && (
        <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-56 bg-navy-800 border border-white/15 rounded-lg p-3 shadow-2xl text-xs animate-in fade-in-0 zoom-in-95">
          <p className="font-semibold text-white/80 mb-2 border-b border-white/10 pb-1">Maliyet Dökümü</p>
          <div className="space-y-1.5">
            <div className="flex justify-between"><span className="text-white/50">Ürün Maliyeti</span><span className="text-white">{formatTR(breakdown.product_cost || "0")}</span></div>
            <div className="flex justify-between"><span className="text-white/50">Komisyon</span><span className="text-white">{formatTR(breakdown.commission || "0")}</span></div>
            <div className="flex justify-between"><span className="text-white/50">Kargo</span><span className="text-white">{formatTR(breakdown.cargo || "0")}</span></div>
            <div className="flex justify-between"><span className="text-white/50">Hizmet Bedeli</span><span className="text-white">{formatTR(breakdown.service_fee || "0")}</span></div>
            <div className="flex justify-between"><span className="text-white/50">KDV (Net)</span><span className="text-white">{formatTR(breakdown.tax || "0")}</span></div>
            <div className="flex justify-between"><span className="text-white/50">Stopaj</span><span className="text-white">{formatTR(breakdown.withholding || "0")}</span></div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Insight Card ────────────────────────────────────────────────────
function InsightCard({ insight }: { insight: InsightEntry }) {
  const config: Record<string, { icon: any; bg: string; border: string; text: string }> = {
    danger: { icon: AlertCircle, bg: "bg-rose-500/8", border: "border-rose-500/20", text: "text-rose-400" },
    warning: { icon: AlertTriangle, bg: "bg-amber-500/8", border: "border-amber-500/20", text: "text-amber-400" },
    suggestion: { icon: Lightbulb, bg: "bg-blue-500/8", border: "border-blue-500/20", text: "text-blue-400" },
  };
  const c = config[insight.type] || config.warning;
  const Icon = c.icon;
  return (
    <div className={clsx("rounded-lg border p-3.5 flex gap-3 items-start", c.bg, c.border)}>
      <Icon className={clsx("w-5 h-5 shrink-0 mt-0.5", c.text)} />
      <div>
        <p className={clsx("font-semibold text-sm", c.text)}>{insight.title}</p>
        <p className="text-xs text-white/60 mt-0.5 leading-relaxed">{insight.message}</p>
      </div>
    </div>
  );
}

// ── Sortable Column Header ──────────────────────────────────────────
function SortHeader({ label, field, currentSort, currentDir, onSort }: {
  label: string; field: string; currentSort: string; currentDir: string;
  onSort: (field: string) => void;
}) {
  const isActive = currentSort === field;
  return (
    <th
      className="px-3 py-3 text-left text-[11px] font-semibold text-white/50 uppercase tracking-wider cursor-pointer hover:text-white/80 transition-colors select-none whitespace-nowrap"
      onClick={() => onSort(field)}
    >
      <span className="inline-flex items-center gap-1">
        {label}
        {isActive ? (
          currentDir === "asc" ? <ChevronUp className="w-3 h-3 text-blue-400" /> : <ChevronDown className="w-3 h-3 text-blue-400" />
        ) : (
          <ArrowUpDown className="w-3 h-3 opacity-30" />
        )}
      </span>
    </th>
  );
}

// ── Main Content ────────────────────────────────────────────────────
function LivePerformanceContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [data, setData] = useState<LiveData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filtersOpen, setFiltersOpen] = useState(false);

  // Filters state
  const [dateFrom, setDateFrom] = useState(() => {
    const p = searchParams.get("min_date");
    return p || new Date().toISOString().slice(0, 10);
  });
  const [dateTo, setDateTo] = useState(() => {
    const p = searchParams.get("max_date");
    return p || new Date().toISOString().slice(0, 10);
  });
  const [productSearch, setProductSearch] = useState(searchParams.get("product") || "");
  const [categorySearch, setCategorySearch] = useState(searchParams.get("category") || "");
  const [lossOnly, setLossOnly] = useState(searchParams.get("loss_only") === "true");

  // Sort state
  const [sortBy, setSortBy] = useState("order_date");
  const [sortDir, setSortDir] = useState("desc");

  // Page state
  const [page, setPage] = useState(1);

  const fetchData = useCallback(async (pg = 1) => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      params.set("min_date", dateFrom);
      params.set("max_date", dateTo);
      params.set("page", String(pg));
      params.set("page_size", "50");
      params.set("sort_by", sortBy);
      params.set("sort_dir", sortDir);
      if (productSearch) params.set("product", productSearch);
      if (categorySearch) params.set("category", categorySearch);
      if (lossOnly) params.set("loss_only", "true");

      const json = await api.get(`/live-performance/?${params.toString()}`);
      setData(json);
      setPage(pg);
    } catch (err) {
      console.error(err);
      setError("Veriler yüklenirken bir hata oluştu.");
    } finally {
      setLoading(false);
    }
  }, [dateFrom, dateTo, productSearch, categorySearch, lossOnly, sortBy, sortDir]);

  useEffect(() => {
    fetchData(1);
  }, [fetchData]);

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortDir(d => d === "desc" ? "asc" : "desc");
    } else {
      setSortBy(field);
      setSortDir("desc");
    }
  };

  const handleApplyFilters = () => {
    fetchData(1);
  };

  const handleClearFilters = () => {
    const today = new Date().toISOString().slice(0, 10);
    setDateFrom(today);
    setDateTo(today);
    setProductSearch("");
    setCategorySearch("");
    setLossOnly(false);
    setSortBy("order_date");
    setSortDir("desc");
  };

  if (loading && !data) {
    return (
      <div className="p-4 sm:p-6 lg:p-8 max-w-[1500px] mx-auto flex items-center justify-center min-h-[500px]">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
          <p className="text-white/40 text-sm">Canlı performans verileri yükleniyor...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-4 sm:p-6 lg:p-8 max-w-[1500px] mx-auto">
        <div className="p-6 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400">
          {error || "Veri bulunamadı."}
        </div>
      </div>
    );
  }

  const { kpis, orders, hourly_performance, product_heatmap, insights, pagination } = data;
  const totalPages = Math.ceil(pagination.total_count / pagination.page_size);

  // Chart data
  const hourlyChartData = hourly_performance.map(h => ({
    hour: h.hour,
    revenue: parseFloat(h.revenue),
    profit: parseFloat(h.profit),
    orders: h.order_count,
  }));

  return (
    <div className="p-4 sm:p-4 lg:p-6 max-w-[1500px] mx-auto space-y-6">
      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-white/70 flex items-center gap-2">
            <Activity className="w-6 h-6 text-emerald-400" />
            Canlı Performans
          </h1>
          <p className="text-xs text-white/40 mt-1">
            {dateFrom === dateTo ? `${dateFrom} tarihli gerçek zamanlı kârlılık verileri` : `${dateFrom} — ${dateTo} aralığı`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setFiltersOpen(f => !f)}
            className={clsx(
              "flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all border",
              filtersOpen
                ? "bg-blue-500/20 text-blue-300 border-blue-500/30"
                : "bg-navy-900 text-white/70 border-white/10 hover:border-white/20 hover:text-white"
            )}
          >
            <Filter className="w-4 h-4" />
            Filtreler
          </button>
          <button
            onClick={() => fetchData(page)}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white border border-emerald-400/20 shadow-lg shadow-emerald-500/20 transition-all"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Activity className="w-4 h-4" />}
            Yenile
          </button>
        </div>
      </div>

      {/* ── Filters Panel ── */}
      {filtersOpen && (
        <div className="bg-navy-900 border border-white/10 rounded-xl p-5 animate-in slide-in-from-top-2 duration-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white/80">Gelişmiş Filtreler</h3>
            <button onClick={handleClearFilters} className="text-xs text-white/40 hover:text-white transition-colors">
              Sıfırla
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <div>
              <label className="block text-[11px] text-white/50 mb-1 font-medium">Başlangıç Tarihi</label>
              <input
                type="date"
                value={dateFrom}
                onChange={e => setDateFrom(e.target.value)}
                className="w-full bg-navy-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500/50"
              />
            </div>
            <div>
              <label className="block text-[11px] text-white/50 mb-1 font-medium">Bitiş Tarihi</label>
              <input
                type="date"
                value={dateTo}
                onChange={e => setDateTo(e.target.value)}
                className="w-full bg-navy-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500/50"
              />
            </div>
            <div>
              <label className="block text-[11px] text-white/50 mb-1 font-medium">Ürün Ara</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/30" />
                <input
                  type="text"
                  value={productSearch}
                  onChange={e => setProductSearch(e.target.value)}
                  placeholder="Ürün adı..."
                  className="w-full bg-navy-800 border border-white/10 rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder:text-white/25 focus:outline-none focus:border-blue-500/50"
                />
              </div>
            </div>
            <div>
              <label className="block text-[11px] text-white/50 mb-1 font-medium">Kategori</label>
              <input
                type="text"
                value={categorySearch}
                onChange={e => setCategorySearch(e.target.value)}
                placeholder="Kategori adı..."
                className="w-full bg-navy-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder:text-white/25 focus:outline-none focus:border-blue-500/50"
              />
            </div>
            <div className="flex flex-col justify-end">
              <label className="flex items-center gap-2 cursor-pointer mb-2">
                <input
                  type="checkbox"
                  checked={lossOnly}
                  onChange={e => setLossOnly(e.target.checked)}
                  className="rounded bg-navy-800 border-white/20 text-rose-500 focus:ring-rose-500/30"
                />
                <span className="text-sm text-white/70">Sadece Zararlı</span>
              </label>
              <button
                onClick={handleApplyFilters}
                className="w-full bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold py-2 rounded-lg transition-colors"
              >
                Uygula
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── KPI Cards ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard
          label="Net Kâr"
          value={formatTR(kpis.net_profit)}
          icon={DollarSign}
          color={parseFloat(kpis.net_profit) >= 0 ? "text-emerald-400" : "text-rose-400"}
        />
        <KpiCard
          label="Toplam Ciro"
          value={formatTR(kpis.total_revenue)}
          icon={TrendingUp}
          color="text-blue-400"
        />
        <KpiCard
          label="Kâr Marjı"
          value={formatPct(kpis.profit_margin)}
          icon={Activity}
          color={parseFloat(kpis.profit_margin) >= 10 ? "text-emerald-400" : "text-amber-400"}
        />
        <KpiCard
          label="Net Nakit Girişi"
          value={formatTR(kpis.net_cash_inflow)}
          icon={Wallet}
          color="text-violet-400"
        />
      </div>

      {/* ── Sub KPIs ── */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-navy-900/60 border border-white/5 rounded-lg px-4 py-3 flex items-center justify-between">
          <span className="text-xs text-white/50">Sipariş Sayısı</span>
          <span className="text-sm font-bold text-white">{kpis.order_count} adet</span>
        </div>
        <div className="bg-navy-900/60 border border-white/5 rounded-lg px-4 py-3 flex items-center justify-between">
          <span className="text-xs text-white/50">Ort. Sipariş Kârı</span>
          <span className={clsx("text-sm font-bold", parseFloat(kpis.avg_order_profit) >= 0 ? "text-emerald-400" : "text-rose-400")}>
            {formatTR(kpis.avg_order_profit)}
          </span>
        </div>
      </div>

      {/* ── Charts Row ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Hourly Performance Chart */}
        <div className="bg-navy-900 border border-white/10 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <Clock className="w-4 h-4 text-blue-400" />
            <h3 className="text-sm font-semibold text-white/80">Saatlik Performans</h3>
          </div>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={hourlyChartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorHourlyProfit" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorHourlyRevenue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="hour" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#64748b" }} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#64748b" }} dx={-10} tickFormatter={(v) => `₺${v}`} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0f172a", borderColor: "#1e293b", borderRadius: "8px", fontSize: "12px" }}
                  labelStyle={{ color: "#94a3b8" }}
                  formatter={(value: any, name?: string) => [
                    formatTR(value),
                    name === "revenue" ? "Ciro" : name === "profit" ? "Kâr" : "Sipariş"
                  ]}
                />
                <Area type="monotone" dataKey="revenue" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorHourlyRevenue)" name="revenue" />
                <Area type="monotone" dataKey="profit" stroke="#22c55e" strokeWidth={2.5} fillOpacity={1} fill="url(#colorHourlyProfit)" name="profit" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Smart Insights */}
        <div className="bg-navy-900 border border-white/10 rounded-xl p-5 shadow-sm flex flex-col">
          <div className="flex items-center gap-2 mb-4">
            <Lightbulb className="w-4 h-4 text-amber-400" />
            <h3 className="text-sm font-semibold text-white/80">Akıllı Öneriler</h3>
          </div>
          <div className="flex-1 space-y-3 overflow-y-auto max-h-[300px] pr-1">
            {insights.length > 0 ? (
              insights.map((insight, i) => <InsightCard key={i} insight={insight} />)
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-center py-10">
                <ShieldAlert className="w-10 h-10 text-emerald-500/30 mb-3" />
                <p className="text-sm text-white/40">Harika! Şu an uyarı veya öneri yok.</p>
                <p className="text-xs text-white/25 mt-1">Tüm ürünler iyi performans gösteriyor.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Product Heatmap ── */}
      <div className="bg-navy-900 border border-white/10 rounded-xl p-5 shadow-sm">
        <div className="flex items-center gap-2 mb-4">
          <Package className="w-4 h-4 text-violet-400" />
          <h3 className="text-sm font-semibold text-white/80">Ürün Performans Haritası</h3>
          <span className="text-xs text-white/30 ml-auto">{product_heatmap.length} ürün</span>
        </div>
        {product_heatmap.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="px-3 py-2.5 text-left text-[11px] font-semibold text-white/50 uppercase tracking-wider">Ürün</th>
                  <th className="px-3 py-2.5 text-right text-[11px] font-semibold text-white/50 uppercase tracking-wider">Satış</th>
                  <th className="px-3 py-2.5 text-right text-[11px] font-semibold text-white/50 uppercase tracking-wider">Ciro</th>
                  <th className="px-3 py-2.5 text-right text-[11px] font-semibold text-white/50 uppercase tracking-wider">Kâr</th>
                  <th className="px-3 py-2.5 text-right text-[11px] font-semibold text-white/50 uppercase tracking-wider">Marj</th>
                  <th className="px-3 py-2.5 text-right text-[11px] font-semibold text-white/50 uppercase tracking-wider">İade %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {product_heatmap.map((item, i) => {
                  const margin = parseFloat(item.margin);
                  const profit = parseFloat(item.total_profit);
                  let marginBg = "";
                  if (profit < 0) marginBg = "bg-rose-500/10";
                  else if (margin >= 20) marginBg = "bg-emerald-500/10";
                  else if (margin >= 10) marginBg = "bg-emerald-500/5";
                  else if (margin >= 0) marginBg = "bg-amber-500/5";

                  return (
                    <tr key={i} className={clsx("hover:bg-white/[0.02] transition-colors", marginBg)}>
                      <td className="px-3 py-2.5 text-white/90 font-medium max-w-[250px] truncate" title={item.product_name}>
                        {item.product_name}
                        {item.category && <span className="block text-[10px] text-white/30 mt-0.5">{item.category}</span>}
                      </td>
                      <td className="px-3 py-2.5 text-right text-white/70 tabular-nums">{item.total_sales}</td>
                      <td className="px-3 py-2.5 text-right text-white/70 tabular-nums">{formatTR(item.total_revenue)}</td>
                      <td className={clsx("px-3 py-2.5 text-right font-semibold tabular-nums", profit >= 0 ? "text-emerald-400" : "text-rose-400")}>
                        {formatTR(item.total_profit)}
                      </td>
                      <td className={clsx("px-3 py-2.5 text-right font-semibold tabular-nums", margin >= 10 ? "text-emerald-400" : margin >= 0 ? "text-amber-400" : "text-rose-400")}>
                        {formatPct(item.margin)}
                      </td>
                      <td className="px-3 py-2.5 text-right text-white/50 tabular-nums">{formatPct(item.return_rate)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex items-center justify-center py-12 text-white/30 text-sm">Henüz ürün verisi yok.</div>
        )}
      </div>

      {/* ── Order Table ── */}
      <div className="bg-navy-900 border border-white/10 rounded-xl shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-semibold text-white/80">Sipariş Kârlılık Tablosu</h3>
            <span className="text-xs text-white/30 bg-white/5 px-2 py-0.5 rounded-full">{pagination.total_count} sipariş</span>
          </div>
          {loading && <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />}
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/10 bg-navy-950/50">
                <SortHeader label="Sipariş No" field="order_number" currentSort={sortBy} currentDir={sortDir} onSort={handleSort} />
                <SortHeader label="Tarih" field="order_date" currentSort={sortBy} currentDir={sortDir} onSort={handleSort} />
                <SortHeader label="Ürün" field="product_name" currentSort={sortBy} currentDir={sortDir} onSort={handleSort} />
                <SortHeader label="Satış" field="sale_price" currentSort={sortBy} currentDir={sortDir} onSort={handleSort} />
                <SortHeader label="Maliyet" field="cost" currentSort={sortBy} currentDir={sortDir} onSort={handleSort} />
                <SortHeader label="Komisyon" field="commission" currentSort={sortBy} currentDir={sortDir} onSort={handleSort} />
                <SortHeader label="Kargo" field="cargo_cost" currentSort={sortBy} currentDir={sortDir} onSort={handleSort} />
                <SortHeader label="KDV" field="tax" currentSort={sortBy} currentDir={sortDir} onSort={handleSort} />
                <SortHeader label="Net Kâr" field="net_profit" currentSort={sortBy} currentDir={sortDir} onSort={handleSort} />
                <SortHeader label="Marj %" field="profit_margin" currentSort={sortBy} currentDir={sortDir} onSort={handleSort} />
                <th className="px-3 py-3 text-left text-[11px] font-semibold text-white/50 uppercase tracking-wider">Risk</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {orders.length > 0 ? (
                orders.map((order, i) => {
                  const profit = parseFloat(order.net_profit);
                  const margin = parseFloat(order.profit_margin);
                  const isLoss = profit < 0;
                  const isLowMargin = !isLoss && margin < 10 && margin >= 0;

                  return (
                    <tr
                      key={i}
                      className={clsx(
                        "transition-colors hover:bg-white/[0.02]",
                        isLoss && "bg-rose-500/[0.06] border-l-2 border-l-rose-500",
                        isLowMargin && "bg-amber-500/[0.04] border-l-2 border-l-amber-500",
                        !isLoss && !isLowMargin && "border-l-2 border-l-transparent"
                      )}
                    >
                      <td className="px-3 py-2.5 text-white/70 font-mono text-xs">{order.order_number}</td>
                      <td className="px-3 py-2.5 text-white/60 text-xs whitespace-nowrap">{formatTime(order.order_date)}</td>
                      <td className="px-3 py-2.5 text-white/90 max-w-[200px] truncate" title={order.product_name}>{order.product_name}</td>
                      <td className="px-3 py-2.5 text-right text-white/70 tabular-nums">{formatTR(order.sale_price)}</td>
                      <td className="px-3 py-2.5 text-right text-white/60 tabular-nums">{formatTR(order.cost)}</td>
                      <td className="px-3 py-2.5 text-right text-white/60 tabular-nums">{formatTR(order.commission)}</td>
                      <td className="px-3 py-2.5 text-right text-white/60 tabular-nums">{formatTR(order.cargo_cost)}</td>
                      <CostTooltip breakdown={order.cost_breakdown}>
                        <td className="px-3 py-2.5 text-right text-white/60 tabular-nums cursor-help underline decoration-dotted decoration-white/20">
                          {formatTR(order.tax)}
                        </td>
                      </CostTooltip>
                      <td className={clsx("px-3 py-2.5 text-right font-semibold tabular-nums", isLoss ? "text-rose-400" : "text-emerald-400")}>
                        {formatTR(order.net_profit)}
                      </td>
                      <td className={clsx("px-3 py-2.5 text-right font-semibold tabular-nums", margin >= 10 ? "text-emerald-400" : margin >= 0 ? "text-amber-400" : "text-rose-400")}>
                        {formatPct(order.profit_margin)}
                      </td>
                      <td className="px-3 py-2.5">
                        <RiskBadge risk={order.return_risk} />
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={11} className="px-3 py-16 text-center text-white/30">
                    Bu tarih aralığında sipariş bulunamadı.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-5 py-3 border-t border-white/10 flex items-center justify-between">
            <p className="text-xs text-white/40">
              {pagination.total_count} siparişten {((page - 1) * pagination.page_size) + 1}–{Math.min(page * pagination.page_size, pagination.total_count)} gösteriliyor
            </p>
            <div className="flex items-center gap-1">
              <button
                onClick={() => fetchData(page - 1)}
                disabled={page <= 1}
                className="px-3 py-1.5 rounded-lg text-xs font-medium bg-white/5 text-white/60 hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                Önceki
              </button>
              <span className="px-3 py-1.5 text-xs font-semibold text-white/70">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => fetchData(page + 1)}
                disabled={page >= totalPages}
                className="px-3 py-1.5 rounded-lg text-xs font-medium bg-white/5 text-white/60 hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                Sonraki
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Export ───────────────────────────────────────────────────────────
export default function LivePerformancePage() {
  return (
    <Suspense fallback={
      <div className="p-8 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    }>
      <LivePerformanceContent />
    </Suspense>
  );
}