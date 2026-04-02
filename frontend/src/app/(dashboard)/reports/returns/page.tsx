"use client";

import { useState, useEffect } from "react";
import { formatCurrency } from "@/lib/utils/format";
import apiClient from "@/lib/api/client";
import { PackageX, RefreshCw, TrendingDown, Truck } from "lucide-react";
import clsx from "clsx";

import { DatePickerWithRange } from "@/components/dashboard/DateRangePicker";
import { DateRange } from "react-day-picker";
import { format, subDays } from "date-fns";

interface ReturnSummary {
  total_claim_count: number;
  total_item_count: number;
  total_refund_amount: string;
  total_outgoing_cargo: string;
  total_incoming_cargo: string;
  total_cargo_loss: string;
}

interface ReturnClaim {
  claim_id: string;
  order_number: string;
  claim_date: string;
  order_date: string;
  claim_status: string;
  product_name: string;
  barcode: string;
  quantity: number;
  refund_amount: string;
  outgoing_cargo: string;
  incoming_cargo: string;
  total_cargo_loss: string;
  cargo_provider: string;
  customer_reason: string;
}

interface ReturnData {
  summary: ReturnSummary;
  claims: ReturnClaim[];
}

const STATUS_STYLES: Record<string, string> = {
  Accepted: "bg-green-500/15 text-green-400 border border-green-500/20",
  WaitingInAction: "bg-yellow-500/15 text-yellow-400 border border-yellow-500/20",
  Unresolved: "bg-orange-500/15 text-orange-400 border border-orange-500/20",
  InProgress: "bg-blue-500/15 text-blue-400 border border-blue-500/20",
};

const STATUS_LABELS: Record<string, string> = {
  Accepted: "Onaylandı",
  WaitingInAction: "Aksiyon Bekliyor",
  Unresolved: "Çözümsüz",
  InProgress: "İşlemde",
};

export default function ReturnAnalysisPage() {
  const [data, setData] = useState<ReturnData | null>(null);
  const [loading, setLoading] = useState(true);

  const [date, setDate] = useState<DateRange | undefined>({
    from: subDays(new Date(), 30),
    to: new Date(),
  });

  useEffect(() => {
    handleDateFilter();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [date]);

  const fetchReturns = async (minDate?: string, maxDate?: string) => {
    setLoading(true);
    try {
      let url = "/reports/return-loss/";
      if (minDate && maxDate) url += `?min_date=${minDate}&max_date=${maxDate}`;
      const result = await apiClient.get<ReturnData>(url);
      if (result.ok && result.data?.summary) {
        setData(result.data);
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

  const s = data?.summary;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/20">
            <PackageX className="w-5 h-5 text-red-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">İade Zarar Analizi</h1>
            <p className="text-xs text-white/40 mt-0.5">Trendyol iade talepleri — kargo ve iade zararları</p>
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
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center py-20">
          <div className="w-8 h-8 border-2 border-red-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : !s ? (
        <div className="bg-navy-900 border border-white/5 rounded-xl p-8 text-center text-white/50">
          İade verisi bulunamadı.
        </div>
      ) : (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
            <SummaryCard label="Toplam İade" value={s.total_claim_count.toString()} unit="adet" color="text-white" />
            <SummaryCard label="İade Edilen Ürün" value={s.total_item_count.toString()} unit="kalem" color="text-white/70" />
            <SummaryCard label="İade Tutarı" value={formatCurrency(parseFloat(s.total_refund_amount))} color="text-orange-400" />
            <SummaryCard label="Giden Kargo" value={formatCurrency(parseFloat(s.total_outgoing_cargo))} color="text-red-400" icon={<Truck className="w-3.5 h-3.5" />} />
            <SummaryCard label="Gelen Kargo" value={formatCurrency(parseFloat(s.total_incoming_cargo))} color="text-red-400" icon={<Truck className="w-3.5 h-3.5" />} />
            <SummaryCard label="Toplam Kargo Zararı" value={formatCurrency(parseFloat(s.total_cargo_loss))} color="text-red-500" icon={<TrendingDown className="w-3.5 h-3.5" />} highlight />
          </div>

          {/* Claims Table */}
          <div className="bg-navy-900 rounded-xl border border-white/5 overflow-hidden">
            <div className="px-4 py-3 border-b border-white/5 text-sm font-medium text-white/70">
              İade Talepleri
              <span className="ml-2 text-xs text-white/30">
                (Onaylandı / Aksiyon Bekliyor / Çözümsüz)
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-[13px] text-left text-white/80">
                <thead className="bg-navy-800/50 text-white border-b border-white/10 uppercase text-[10px] tracking-wider font-semibold">
                  <tr>
                    <th className="px-4 py-2 whitespace-nowrap">Claim ID</th>
                    <th className="px-4 py-2 whitespace-nowrap">Sipariş No</th>
                    <th className="px-4 py-2 whitespace-nowrap">İade Tarihi</th>
                    <th className="px-4 py-2 whitespace-nowrap">Durum</th>
                    <th className="px-4 py-2 whitespace-nowrap">Ürün</th>
                    <th className="px-4 py-2 whitespace-nowrap">İade Sebebi</th>
                    <th className="px-4 py-2 whitespace-nowrap">Kargo</th>
                    <th className="px-4 py-2 whitespace-nowrap text-right">İade Tutarı</th>
                    <th className="px-4 py-2 whitespace-nowrap text-right">Kargo Zararı</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {!data?.claims || data.claims.length === 0 ? (
                    <tr>
                      <td colSpan={9} className="px-4 py-8 text-center text-white/40">
                        Aktif iade talebi bulunamadı.{" "}
                        <span className="text-white/25 text-xs">
                          (Trendyol getClaims senkronizasyonu gerekiyor)
                        </span>
                      </td>
                    </tr>
                  ) : (
                    data.claims.map((claim) => (
                      <tr key={claim.claim_id} className="hover:bg-white/5 transition-colors">
                        <td className="px-4 py-2 whitespace-nowrap font-mono text-white/50 text-xs">
                          #{claim.claim_id}
                        </td>
                        <td className="px-4 py-2 whitespace-nowrap text-white/60 text-xs">
                          {claim.order_number || "-"}
                        </td>
                        <td className="px-4 py-2 whitespace-nowrap text-white/50 text-xs">
                          {claim.claim_date}
                        </td>
                        <td className="px-4 py-2 whitespace-nowrap">
                          <span className={clsx(
                            "px-2 py-0.5 rounded text-[11px] font-medium",
                            STATUS_STYLES[claim.claim_status] ?? "bg-white/10 text-white/50"
                          )}>
                            {STATUS_LABELS[claim.claim_status] ?? claim.claim_status}
                          </span>
                        </td>
                        <td className="px-4 py-2 max-w-[180px] truncate text-white/80">
                          {claim.product_name || "-"}
                          {claim.barcode && (
                            <span className="ml-1 text-white/30 text-[11px]">{claim.barcode}</span>
                          )}
                        </td>
                        <td className="px-4 py-2 max-w-[160px] truncate text-white/60 text-xs">
                          {claim.customer_reason || "-"}
                        </td>
                        <td className="px-4 py-2 whitespace-nowrap text-white/40 text-xs">
                          {claim.cargo_provider || "-"}
                        </td>
                        <td className="px-4 py-2 whitespace-nowrap text-right text-orange-400 font-semibold">
                          {formatCurrency(parseFloat(claim.refund_amount))}
                        </td>
                        <td className="px-4 py-2 whitespace-nowrap text-right text-red-400 font-bold">
                          -{formatCurrency(parseFloat(claim.total_cargo_loss))}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function SummaryCard({
  label,
  value,
  unit,
  color,
  icon,
  highlight,
}: {
  label: string;
  value: string;
  unit?: string;
  color?: string;
  icon?: React.ReactNode;
  highlight?: boolean;
}) {
  return (
    <div
      className={clsx(
        "rounded-xl p-4 border",
        highlight
          ? "bg-gradient-to-br from-red-500/15 to-red-600/5 border-red-500/20"
          : "bg-navy-900 border-white/5"
      )}
    >
      <p className="text-[11px] text-white/40 font-medium mb-1.5">{label}</p>
      <div className="flex items-center gap-1">
        {icon && <span className={clsx("opacity-70", color)}>{icon}</span>}
        <p className={clsx("text-lg font-bold", color ?? "text-white")}>
          {value}
          {unit && <span className="text-xs font-normal text-white/40 ml-1">{unit}</span>}
        </p>
      </div>
    </div>
  );
}
