"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { GlobalFilter } from "@/components/dashboard/GlobalFilter";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend
} from "recharts";
import {
  TrendingUp, TrendingDown, DollarSign, Package, AlertCircle, ShoppingCart
} from "lucide-react";
import clsx from "clsx";

const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#f43f5e', '#f97316', '#eab308', '#22c55e', '#14b8a6'];

const formatTR = (val: number | string) => {
  const num = typeof val === 'string' ? parseFloat(val) : val;
  return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY' }).format(num);
};

export default function DashboardOverview() {
  const searchParams = useSearchParams();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const channel = searchParams.get("channel") || "trendyol";

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError("");
      try {
        const token = localStorage.getItem("access_token");
        const res = await fetch(`http://localhost:8000/api/dashboard/overview/?${searchParams.toString()}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const json = await res.json();
          setData(json);
        } else {
          setError("Veriler yüklenirken bir hata oluştu.");
        }
      } catch (err) {
        console.error(err);
        setError("Sunucuya bağlanılamadı.");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [searchParams]);

  const kpiCards = [
    { title: "Net Kâr", value: data ? formatTR(data.kpis.net_profit) : "₺0,00", icon: DollarSign, trend: "+12.5%", isPositive: true },
    { title: "Kâr Marjı", value: data ? `%${data.kpis.profit_margin}` : "%0", icon: TrendingUp, trend: "+2.1%", isPositive: true },
    { title: "Aylık Ciro (Net)", value: data ? formatTR(data.kpis.net_revenue) : "₺0,00", icon: ShoppingCart, trend: "-1.4%", isPositive: false },
    { title: "Kayıp / Ceza / İade", value: data ? formatTR(data.kpis.lost_and_leakage) : "₺0,00", icon: AlertCircle, trend: "-4.2%", isPositive: true }, // Düşmesi pozitif
  ];

  const breakdownData = data ? [
    { name: "Ürün Maliyeti", value: parseFloat(data.profit_breakdown.PRODUCT_COST || 0) },
    { name: "Komisyon", value: parseFloat(data.profit_breakdown.COMMISSION || 0) },
    { name: "Kargo Ücreti", value: parseFloat(data.profit_breakdown.SHIPPING_FEE || 0) },
    { name: "Hizmet / Paketleme", value: parseFloat(data.profit_breakdown.SERVICE_FEE || 0) },
    { name: "Reklam (Ads)", value: parseFloat(data.profit_breakdown.ADS_COST || 0) },
  ].filter(i => i.value > 0) : [];

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-white/70">
          Genel Bakış
        </h1>
        <p className="mt-1 text-sm text-white/50">
          Son senkronizasyon: {new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>

      <GlobalFilter />

      {loading ? (
        <div className="h-64 flex items-center justify-center">
          <div className="w-8 h-8 rounded-full border-4 border-blue-500 border-t-transparent animate-spin"></div>
        </div>
      ) : error ? (
        <div className="p-6 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400">
          {error}
        </div>
      ) : (
        <>
          {/* KPI Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-8">
            {kpiCards.map((card, i) => (
              <div key={i} className="bg-navy-900 border border-white/10 rounded-2xl p-5 hover:border-white/20 transition-colors shadow-lg">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-sm font-medium text-white/60 mb-1">{card.title}</p>
                    <h3 className="text-2xl font-bold text-white">{card.value}</h3>
                  </div>
                  <div className="p-2 bg-navy-950 rounded-lg border border-white/5">
                    <card.icon className={clsx("w-5 h-5", channel === "micro_export" ? "text-purple-400" : "text-blue-400")} />
                  </div>
                </div>
                <div className="mt-4 flex items-center gap-2">
                  <span className={clsx("text-xs font-medium px-2 py-0.5 rounded-full", card.isPositive ? "bg-green-500/10 text-green-400" : "bg-red-500/10 text-red-400")}>
                    {card.trend}
                  </span>
                  <span className="text-xs text-white/40">geçen aya göre</span>
                </div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Breakdown Pie Chart */}
            <div className="lg:col-span-1 bg-navy-900 border border-white/10 rounded-2xl p-6 shadow-lg flex flex-col">
              <h3 className="text-lg font-semibold text-white mb-6">Maliyet Dağılımı</h3>
              {breakdownData.length > 0 ? (
                <div className="flex-1 min-h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={breakdownData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {breakdownData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                        formatter={(value: number) => formatTR(value)}
                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }}
                        itemStyle={{ color: '#fff' }}
                      />
                      <Legend verticalAlign="bottom" height={36} wrapperStyle={{ color: '#94a3b8', fontSize: '12px' }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="flex-1 flex items-center justify-center text-white/40 text-sm h-[300px]">
                  Yeterli veri bulunmuyor.
                </div>
              )}
            </div>

            {/* Empty space for Bar Chart (Ciro vs Kar Trendi) */}
            <div className="lg:col-span-2 bg-navy-900 border border-white/10 rounded-2xl p-6 shadow-lg flex flex-col">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-semibold text-white">Net Ciro & Kâr Trendi</h3>
                <span className="text-xs px-2.5 py-1 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-md font-medium">Bu Ay</span>
              </div>
              <div className="flex-1 flex flex-col items-center justify-center text-white/40 text-sm min-h-[300px] border border-dashed border-white/10 rounded-xl">
                <BarChart3 className="w-8 h-8 mb-3 opacity-50" />
                <p>Veri senkronizasyonu bekleniyor...</p>
                <p className="text-xs mt-1">Trendyol API entegrasyonu tamamlandığında grafik dolacaktır.</p>
              </div>
            </div>
          </div>

          {/* Micro Export Map/Table placeholder */}
          {channel === "micro_export" && data.country_profit?.length > 0 && (
            <div className="mt-6 bg-navy-900 border border-white/10 rounded-2xl p-6 shadow-lg">
              <h3 className="text-lg font-semibold text-white mb-4">Ülke Bazlı Performans</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-white/70">
                  <thead className="text-xs text-white/40 uppercase bg-navy-950/50">
                    <tr>
                      <th className="px-4 py-3 rounded-l-lg">Ülke Kodu</th>
                      <th className="px-4 py-3">Net Kâr</th>
                      <th className="px-4 py-3 text-right rounded-r-lg">Durum</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.country_profit.map((cp: any, i: number) => {
                      const profit = parseFloat(cp.profit);
                      return (
                        <tr key={i} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                          <td className="px-4 py-4 font-medium text-white flex items-center gap-2">
                            <span className="w-6 h-4 rounded-[2px] bg-gradient-to-br from-white/20 to-white/10 block shadow-inner border border-white/10" />
                            {cp.country}
                          </td>
                          <td className="px-4 py-4 font-semibold text-white">
                            {formatTR(profit)}
                          </td>
                          <td className="px-4 py-4 text-right">
                            <span className={clsx("px-2.5 py-1 text-xs font-semibold rounded-md", profit >= 0 ? "bg-green-500/10 text-green-400" : "bg-red-500/10 text-red-400")}>
                              {profit >= 0 ? "Kârlı" : "Zararda"}
                            </span>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// Recharts components not imported at top mapping fix for missing BarChart3
function BarChart3(props: any) {
  return <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="M3 3v18h18" /><path d="M18 17V9" /><path d="M13 17V5" /><path d="M8 17v-3" /></svg>
}