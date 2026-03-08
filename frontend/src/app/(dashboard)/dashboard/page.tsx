"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { GlobalFilter } from "@/components/dashboard/GlobalFilter";
import { LowStockWidget } from "@/components/dashboard/LowStockWidget";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend, FunnelChart, Funnel, LabelList
} from "recharts";
import {
  TrendingUp, TrendingDown, DollarSign, Package, AlertCircle, ShoppingCart, Info, RefreshCw
} from "lucide-react";
import clsx from "clsx";
import { api } from "@/lib/api";

const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#f43f5e', '#f97316', '#eab308', '#22c55e', '#14b8a6'];
// Custom colors for funnel chart (green to red descent)
const FUNNEL_COLORS = ['#34d399', '#a3e635', '#fcd34d', '#fb923c', '#f87171'];

const formatTR = (val: number | string) => {
  const num = typeof val === 'string' ? parseFloat(val) : val;
  return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY' }).format(num);
};

import { Suspense } from "react";

function DashboardContent() {
  const searchParams = useSearchParams();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [syncing, setSyncing] = useState(false);
  const [lastSync, setLastSync] = useState<string | null>(null);

  const channel = searchParams.get("channel") || "trendyol";

  const fetchData = async () => {
    setLoading(true);
    setError("");
    try {
      const json = await api.get(`/dashboard/overview/?${searchParams.toString()}`);
      setData(json);
    } catch (err) {
      console.error(err);
      setError("Veriler yüklenirken bir hata oluştu veya sunucuya bağlanılamadı.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [searchParams]);

  const handleSync = async () => {
    setSyncing(true);
    try {
      await api.post("/sync/run/", {});
      setLastSync(new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' }));
      // Sync done — refresh dashboard data
      await fetchData();
    } catch (err) {
      console.error("Sync error:", err);
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return (
      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto flex items-center justify-center min-h-[500px]">
        <div className="w-8 h-8 rounded-full border-4 border-blue-500 border-t-transparent animate-spin"></div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
        <GlobalFilter />
        <div className="p-6 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400">
          {error || "Veri bulunamadı."}
        </div>
      </div>
    );
  }

  const kpis = [
    { label: "Toplam Ciro", value: formatTR(data.kpis.toplam_ciro || data.kpis.gross_revenue), icon: ShoppingCart },
    { label: "Maliyetlendirilen Ciro", value: formatTR(data.kpis.costed_revenue || 0), icon: TrendingUp },
    { label: "Kâr Tutarı", value: formatTR(data.kpis.net_profit), icon: DollarSign },
    { label: "Kâr Satış Fiyatı Oranı", value: `%${data.kpis.profit_margin}`, icon: Package },
    { label: "Kâr / Ürün Maliyeti Oranı", value: `%${data.kpis.profit_on_cost_ratio}`, icon: DollarSign },
  ];

  const breakdownData = [
    { name: "Ürün Maliyeti", value: parseFloat(data.profit_breakdown.PRODUCT_COST || 0) },
    { name: "Komisyon", value: parseFloat(data.profit_breakdown.COMMISSION || 0) },
    { name: "Kargo Ücreti", value: parseFloat(data.profit_breakdown.SHIPPING_FEE || 0) },
    { name: "Hizmet Bedeli", value: parseFloat(data.profit_breakdown.SERVICE_FEE || 0) },
    { name: "Satış KDV / Stopaj", value: parseFloat(data.profit_breakdown.VAT_OUTPUT || 0) + parseFloat(data.profit_breakdown.WITHHOLDING || 0) },
    { name: "Ceza & Erken Öd.", value: parseFloat(data.profit_breakdown.PENALTY || 0) + parseFloat(data.profit_breakdown.EARLY_PAYMENT || 0) },
  ].filter(i => i.value > 0);

  const funnelData = (data.net_profit_funnel || []).map((f: any, i: number) => ({
    name: f.name,
    value: parseFloat(f.value),
    fill: FUNNEL_COLORS[i % FUNNEL_COLORS.length]
  }));

  // Recharts FunnelChart requires standard data sorting biggest to smallest, we rely on the API providing it that way

  const oMetrics = data.order_metrics || {};
  const pMetrics = data.product_metrics || {};
  const rMetrics = data.return_metrics || {};
  const aMetrics = data.ads_metrics || {};

  return (
    <div className="p-4 sm:p-4 lg:p-6 max-w-[1400px] mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-white/70">
            {channel === "micro_export" ? "Mikro İhracat Dashboard" : "Genel Bakış Dashboard"}
          </h1>
          <p className="text-xs text-white/40 mt-1">
            {lastSync ? `Son senkronizasyon: ${lastSync}` : "Verileri güncellemek için senkronize edin"}
          </p>
        </div>
        <button
          onClick={handleSync}
          disabled={syncing}
          className={clsx(
            "flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 border",
            syncing
              ? "bg-blue-500/20 text-blue-300 border-blue-500/30 cursor-wait"
              : "bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white border-blue-400/20 shadow-lg shadow-blue-500/20 hover:shadow-blue-500/30"
          )}
        >
          <RefreshCw className={clsx("w-4 h-4", syncing && "animate-spin")} />
          {syncing ? "Senkronize Ediliyor..." : "Senkronize Et"}
        </button>
      </div>

      <GlobalFilter />

      {/* 5 KPIs Row */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {kpis.map((kpi, idx) => (
          <div key={idx} className="bg-navy-900 border border-white/10 rounded-xl p-4 shadow-sm flex flex-col hover:border-white/20 transition-colors">
            <p className="text-xs font-semibold text-white/50 mb-1 flex items-center gap-1">
              {kpi.label} <Info className="w-3 h-3 hover:text-white" />
            </p>
            <h3 className="text-xl font-bold text-white tracking-tight">{kpi.value}</h3>
          </div>
        ))}
      </div>

      {/* Main Charts Row */}
      <div className={clsx("grid grid-cols-1 gap-6", channel === "trendyol" && data?.low_stock_alerts ? "lg:grid-cols-3" : "lg:grid-cols-2")}>
        {/* Pie Breakdown */}
        <div className={clsx("bg-navy-900 border border-white/10 rounded-xl p-5 shadow-sm", channel === "trendyol" && data?.low_stock_alerts ? "lg:col-span-2" : "")}>
          <h3 className="text-sm font-semibold text-white/80 mb-4">Maliyet Dağılımı (₺)</h3>
          <div className="flex flex-col md:flex-row items-center justify-center gap-6 h-[300px]">
            <div className="w-full md:w-1/2 h-full">
              {breakdownData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={breakdownData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={4}
                      dataKey="value"
                      stroke="rgba(255,255,255,0.05)"
                      strokeWidth={2}
                    >
                      {breakdownData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value: any) => formatTR(value)}
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px', fontSize: '13px' }}
                      itemStyle={{ color: '#fff' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full text-white/30 text-xs">Veri yok</div>
              )}
            </div>

            <div className="w-full md:w-1/2 grid grid-cols-1 gap-2 overflow-y-auto max-h-[250px] pr-2 scrollbar-thin scrollbar-thumb-white/10">
              {breakdownData.map((d, i) => (
                <div key={i} className="flex justify-between items-center text-xs">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }}></span>
                    <span className="text-white/60">{d.name}</span>
                  </div>
                  <span className="font-semibold text-white">{formatTR(d.value)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Low Stock Alerts Widget */}
        {channel === "trendyol" && data?.low_stock_alerts && (
          <div className="col-span-1">
            <LowStockWidget alerts={data.low_stock_alerts} />
          </div>
        )}

        {/* Profit Perf Area Chart */}
        <div className={clsx("bg-navy-900 border border-white/10 rounded-xl p-5 shadow-sm flex flex-col", channel === "trendyol" && data?.low_stock_alerts ? "lg:col-span-2" : "")}>
          <h3 className="text-sm font-semibold text-white/80 mb-4">Kâr Performansı Trendi</h3>
          <div className="flex-1 min-h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.profit_performance_history} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorProfit" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#64748b' }} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#64748b' }} dx={-10} tickFormatter={(v) => `₺${v}`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px', fontSize: '13px' }}
                  itemStyle={{ color: '#fff' }}
                  labelStyle={{ color: '#94a3b8' }}
                />
                <Area type="monotone" dataKey="profit" stroke="#22c55e" strokeWidth={3} fillOpacity={1} fill="url(#colorProfit)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Funnel and Data Grids */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Net Profit Funnel */}
        <div className="bg-navy-900 border border-white/10 rounded-xl p-5 shadow-sm flex flex-col">
          <h3 className="text-sm font-semibold text-white/80 mb-4">Net Kâr Performansı</h3>
          <div className="flex-1 w-full min-h-[350px]">
            {funnelData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <FunnelChart>
                  <Tooltip
                    formatter={(value: any) => formatTR(value)}
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px', fontSize: '13px' }}
                  />
                  <Funnel
                    dataKey="value"
                    data={funnelData}
                    isAnimationActive
                  >
                    <LabelList position="right" fill="#cbd5e1" stroke="none" dataKey="name" style={{ fontSize: '12px' }} />
                  </Funnel>
                </FunnelChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-white/40 text-sm">Katman hatası veya veri yok.</div>
            )}

          </div>
        </div>

        {/* Detail Metrics Grids */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="bg-navy-900 border border-white/5 rounded-xl p-4 shadow-sm">
            <h4 className="text-[13px] font-semibold text-white/80 mb-3 pb-2 border-b border-white/5 uppercase tracking-wide">Ürün Metrikleri</h4>
            <div className="space-y-2.5">
              <MetricRow label="Satış Adedi" value={`${pMetrics.items_sold} adet`} />
              <MetricRow label="Ürün Baş. Satış" value={formatTR(pMetrics.avg_revenue_per_item)} />
              <MetricRow label="Ürün Baş. Kâr" value={formatTR(pMetrics.avg_profit_per_item)} />
              <MetricRow label="Ürün Baş. Kargo" value={formatTR(pMetrics.avg_cargo_per_item)} />
              <MetricRow label="Ort. Komisyon" value={`%${pMetrics.avg_commission_rate}`} />
              <MetricRow label="Ort. İndirim" value={`%${pMetrics.avg_discount_rate}`} />
            </div>
          </div>

          <div className="bg-navy-900 border border-white/5 rounded-xl p-4 shadow-sm">
            <h4 className="text-[13px] font-semibold text-white/80 mb-3 pb-2 border-b border-white/5 uppercase tracking-wide">Sipariş Metrikleri</h4>
            <div className="space-y-2.5">
              <MetricRow label="Sipariş Sayısı" value={`${oMetrics.order_count} adet`} />
              <MetricRow label="Sipariş Baş. Satış" value={formatTR(oMetrics.avg_revenue_per_order)} />
              <MetricRow label="Sipariş Baş. Kâr" value={formatTR(oMetrics.avg_profit_per_order)} />
              <MetricRow label="Sip. Baş. Kargo" value={formatTR(oMetrics.avg_cargo_per_order)} />
            </div>
          </div>

          <div className="bg-navy-900 border border-white/5 rounded-xl p-4 shadow-sm">
            <h4 className="text-[13px] font-semibold text-white/80 mb-3 pb-2 border-b border-white/5 uppercase tracking-wide">İade Metrikleri</h4>
            <div className="space-y-2.5">
              <MetricRow label="İade Oranı" value={`%${rMetrics.return_rate}`} />
              <MetricRow label="Top. İade Maliyeti" value={formatTR(rMetrics.total_return_cost)} />
              <MetricRow label="İade Kargo Zararı" value={formatTR(rMetrics.return_cargo_loss)} />
              <MetricRow label="Yurt Dışı Opr. Bedeli" value={formatTR(rMetrics.overseas_operation_fee)} />
            </div>
          </div>

          <div className="bg-navy-900 border border-white/5 rounded-xl p-4 shadow-sm">
            <h4 className="text-[13px] font-semibold text-white/80 mb-3 pb-2 border-b border-white/5 uppercase tracking-wide">Reklam Metrikleri</h4>
            <div className="space-y-2.5">
              <MetricRow label="Top. Reklam Harc." value={formatTR(aMetrics.total_ads_cost)} />
              <MetricRow label="Influencer Kes." value={formatTR(aMetrics.influencer_cut)} />
              <MetricRow label="Reklam Kâr İndexi" value={`%${aMetrics.ads_profit_index}`} />
              <MetricRow label="Reklam Ciro İndexi" value={`%${aMetrics.ads_revenue_index}`} />
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}

export default function DashboardOverview() {
  return (
    <Suspense fallback={<div className="p-8 text-white/50 text-center">Yükleniyor...</div>}>
      <DashboardContent />
    </Suspense>
  );
}

// Custom Helper component for dense info grids
function MetricRow({ label, value }: { label: string, value: string }) {
  return (
    <div className="flex justify-between items-center text-[13px] group">
      <span className="text-white/50 group-hover:text-white/70 transition-colors">{label}</span>
      <span className="font-semibold text-white/90">{value}</span>
    </div>
  )
}