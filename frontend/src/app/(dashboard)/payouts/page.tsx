"use client";

import { useState, useEffect } from "react";
import { formatCurrency } from "@/lib/utils/format";
import apiClient from "@/lib/api/client";
import { CreditCard, CheckCircle, Clock, RefreshCw } from "lucide-react";
import { DatePickerWithRange } from "@/components/dashboard/DateRangePicker";
import { DateRange } from "react-day-picker";
import { format, subDays } from "date-fns";

interface PayoutSummary {
  total_paid: number;
  total_pending: number;
  payment_count: number;
}

interface Payment {
  payment_order_id: number | null;
  payment_date: string;
  amount: number;
  description: string;
  status: string;
}

interface PayoutsData {
  summary: PayoutSummary;
  payments: Payment[];
}

export default function PayoutsPage() {
  const [data, setData] = useState<PayoutsData | null>(null);
  const [loading, setLoading] = useState(true);

  const [date, setDate] = useState<DateRange | undefined>({
    from: subDays(new Date(), 30),
    to: new Date(),
  });

  useEffect(() => {
    fetchPayouts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [date]);

  const fetchPayouts = async () => {
    setLoading(true);
    try {
      let url = "/reports/payouts/";
      if (date?.from && date?.to) {
        url += `?start_date=${format(date.from, "yyyy-MM-dd")}&end_date=${format(date.to, "yyyy-MM-dd")}`;
      }
      const result = await apiClient.get<PayoutsData>(url);
      if (result.ok && result.data?.summary) {
        setData(result.data);
      }
    } catch (error) {
      console.error("Payouts fetch error:", error);
    } finally {
      setLoading(false);
    }
  };

  const s = data?.summary;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-green-500/10 border border-green-500/20">
            <CreditCard className="w-5 h-5 text-green-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Hakediş Kontrolü</h1>
            <p className="text-xs text-white/40 mt-0.5">Trendyol ödeme emirleri ve hakediş özetleri</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <DatePickerWithRange date={date} setDate={setDate} />
          <button
            onClick={fetchPayouts}
            className="flex items-center justify-center w-10 h-10 bg-green-600 hover:bg-green-500 text-white rounded-lg transition-colors shadow-lg shadow-green-900/20"
            title="Verileri Güncelle"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center py-20">
          <div className="w-8 h-8 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : !s ? (
        <div className="bg-navy-900 border border-white/5 rounded-xl p-8 text-center text-white/50">
          Hakediş verisi bulunamadı.
        </div>
      ) : (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
            <div className="bg-gradient-to-br from-green-500/10 to-green-600/5 border border-green-500/10 rounded-xl p-5">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <p className="text-xs text-white/50 font-medium">Toplam Ödenen</p>
              </div>
              <p className="text-2xl font-bold text-green-400">{formatCurrency(s.total_paid)}</p>
            </div>
            <div className="bg-gradient-to-br from-yellow-500/10 to-yellow-600/5 border border-yellow-500/10 rounded-xl p-5">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="w-4 h-4 text-yellow-400" />
                <p className="text-xs text-white/50 font-medium">Bekleyen</p>
              </div>
              <p className="text-2xl font-bold text-yellow-400">{formatCurrency(s.total_pending)}</p>
            </div>
            <div className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 border border-blue-500/10 rounded-xl p-5">
              <div className="flex items-center gap-2 mb-2">
                <CreditCard className="w-4 h-4 text-blue-400" />
                <p className="text-xs text-white/50 font-medium">Ödeme Sayısı</p>
              </div>
              <p className="text-2xl font-bold text-blue-400">{s.payment_count}</p>
            </div>
          </div>

          {/* Payments Table */}
          <div className="bg-navy-900 rounded-xl border border-white/5 overflow-hidden">
            <div className="px-4 py-3 border-b border-white/5 text-sm font-medium text-white/70">
              Ödeme Emirleri
            </div>
            <table className="w-full text-[13px] text-left text-white/80">
              <thead className="bg-navy-800/50 text-white border-b border-white/10 uppercase text-[10px] tracking-wider font-semibold">
                <tr>
                  <th className="px-4 py-3">Ödeme Emri ID</th>
                  <th className="px-4 py-3">Tarih</th>
                  <th className="px-4 py-3">Açıklama</th>
                  <th className="px-4 py-3">Durum</th>
                  <th className="px-4 py-3 text-right">Tutar</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {!data?.payments || data.payments.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-white/40">
                      Hakediş kaydı bulunamadı.{" "}
                      <span className="text-white/25 text-xs">
                        (Finansal senkronizasyon tamamlandığında veriler görünecek.)
                      </span>
                    </td>
                  </tr>
                ) : (
                  data.payments.map((p, i) => (
                    <tr key={i} className="hover:bg-white/5 transition-colors">
                      <td className="px-4 py-3 whitespace-nowrap text-white/60 font-mono text-xs">
                        {p.payment_order_id || "-"}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-white/70">{p.payment_date}</td>
                      <td className="px-4 py-3 text-white/50 truncate max-w-[220px] text-xs">{p.description || "-"}</td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-0.5 rounded text-[11px] font-medium text-green-400 bg-green-400/10">
                          {p.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right font-semibold text-green-400">
                        {formatCurrency(p.amount)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
