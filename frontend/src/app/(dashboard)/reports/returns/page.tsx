"use client";

import { useState, useEffect } from "react";
import { formatCurrency } from "@/lib/utils/format";
import apiClient from "@/lib/api/client";
import { Filter, RotateCcw, RefreshCw } from "lucide-react";
import clsx from "clsx";

import { TableFilter, FilterState, FilterColumn, applyTableFilter } from "@/components/dashboard/TableFilter";
import { DatePickerWithRange } from "@/components/dashboard/DateRangePicker";
import { DateRange } from "react-day-picker";
import { format, subDays } from "date-fns";

interface ReturnSummary {
  total_return_count: number;
  total_return_amount: string;
  total_outgoing_cargo: string;
  total_incoming_cargo: string;
  total_cargo_loss: string;
  total_sales: string;
  return_loss_ratio: string;
}

interface ReturnOrder {
  order_number: string;
  date: string;
  status: string;
  product_name: string;
  barcode: string;
  quantity: number;
  sale_price: string;
  outgoing_cargo: string;
  incoming_cargo: string;
  total_cargo_loss: string;
  commission: string;
  net_loss: string;
}

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  Returned:    { label: "İade",    color: "text-red-400 bg-red-400/10" },
  Cancelled:   { label: "İptal",   color: "text-orange-400 bg-orange-400/10" },
  UnDelivered: { label: "Teslim Edilmedi", color: "text-yellow-400 bg-yellow-400/10" },
};

const FILTER_COLUMNS: FilterColumn[] = [
  { id: "order_number",  label: "Sipariş No",  type: "text" },
  { id: "product_name",  label: "Ürün Adı",    type: "text" },
  { id: "barcode",       label: "Barkod",       type: "text" },
  { id: "status",        label: "Durum",        type: "text" },
  { id: "net_loss",      label: "Net Zarar (₺)", type: "number" },
];

export default function ReturnAnalysisPage() {
  const [summary, setSummary] = useState<ReturnSummary | null>(null);
  const [orders, setOrders] = useState<ReturnOrder[]>([]);
  const [loading, setLoading] = useState(true);

  const [date, setDate] = useState<DateRange | undefined>({
    from: subDays(new Date(), 30),
    to: new Date(),
  });

  const [showFilter, setShowFilter] = useState(false);
  const [tableFilter, setTableFilter] = useState<FilterState | null>(null);

  useEffect(() => {
    fetchReturns(
      date?.from ? format(date.from, "yyyy-MM-dd") : undefined,
      date?.to   ? format(date.to,   "yyyy-MM-dd") : undefined,
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [date]);

  const fetchReturns = async (minDate?: string, maxDate?: string) => {
    setLoading(true);
    try {
      let url = "/reports/returns/";
      if (minDate && maxDate) url += `?min_date=${minDate}&max_date=${maxDate}`;
      const result = await apiClient.get<{ summary: ReturnSummary; orders: ReturnOrder[] }>(url);
      if (result.ok && result.data?.summary) {
        setSummary(result.data.summary);
        setOrders(result.data.orders || []);
      }
    } catch (err) {
      console.error("Return analysis fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  const filteredOrders = applyTableFilter(orders, tableFilter);

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/20">
            <RotateCcw className="w-5 h-5 text-red-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">İade Zarar Analizi</h1>
            <p className="text-xs text-white/40 mt-0.5">İade / iptal sipariş bazlı kargo ve net zarar analizi</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <DatePickerWithRange date={date} setDate={setDate} />
          <button
            onClick={() => fetchReturns(
              date?.from ? format(date.from, "yyyy-MM-dd") : undefined,
              date?.to   ? format(date.to,   "yyyy-MM-dd") : undefined,
            )}
            className="flex items-center justify-center w-10 h-10 bg-red-600 hover:bg-red-500 text-white rounded-lg transition-colors shadow-lg shadow-red-900/20"
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
                ? "bg-red-600/20 text-red-400 border-red-500/30 ring-1 ring-red-500/10"
                : "bg-navy-800 hover:bg-navy-700 text-white/90 border-white/5"
            )}
          >
            <Filter className="w-4 h-4" />
            Tabloyu Filtrele {tableFilter && <span className="w-2 h-2 rounded-full bg-red-500 ml-1" />}
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

      {/* Summary — tek satır tablo */}
      <div className="bg-navy-900 rounded-xl border border-white/5 overflow-hidden mb-6">
        <table className="w-full text-sm">
          <thead className="bg-navy-800/50 border-b border-white/10 uppercase text-[10px] tracking-wider font-semibold text-white/50">
            <tr>
              <th className="px-4 py-3 text-center whitespace-nowrap">İade Adedi</th>
              <th className="px-4 py-3 text-center whitespace-nowrap">İade Tutarı</th>
              <th className="px-4 py-3 text-center whitespace-nowrap">Gidiş Kargo</th>
              <th className="px-4 py-3 text-center whitespace-nowrap">Geliş Kargo</th>
              <th className="px-4 py-3 text-center whitespace-nowrap">Toplam Kargo Zararı</th>
              <th className="px-4 py-3 text-center whitespace-nowrap">Toplam Satış</th>
              <th className="px-4 py-3 text-center whitespace-nowrap">Zarar / Satış %</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} className="px-4 py-6 text-center text-white/40 text-sm">
                  <div className="flex justify-center items-center gap-2">
                    <div className="w-4 h-4 border-2 border-red-400 border-t-transparent rounded-full animate-spin" />
                    Yükleniyor...
                  </div>
                </td>
              </tr>
            ) : summary ? (
              <tr className="text-center">
                <td className="px-4 py-4 font-bold text-white text-lg">{summary.total_return_count}</td>
                <td className="px-4 py-4 font-bold text-orange-400">{formatCurrency(parseFloat(summary.total_return_amount))}</td>
                <td className="px-4 py-4 font-semibold text-red-400">{formatCurrency(parseFloat(summary.total_outgoing_cargo))}</td>
                <td className="px-4 py-4 font-semibold text-red-400">{formatCurrency(parseFloat(summary.total_incoming_cargo))}</td>
                <td className="px-4 py-4 font-bold text-red-500">{formatCurrency(parseFloat(summary.total_cargo_loss))}</td>
                <td className="px-4 py-4 font-semibold text-green-400">{formatCurrency(parseFloat(summary.total_sales))}</td>
                <td className={clsx(
                  "px-4 py-4 font-bold text-lg",
                  parseFloat(summary.return_loss_ratio) > 10 ? "text-red-400" :
                  parseFloat(summary.return_loss_ratio) > 5 ? "text-yellow-400" : "text-green-400"
                )}>
                  %{summary.return_loss_ratio}
                </td>
              </tr>
            ) : (
              <tr>
                <td colSpan={7} className="px-4 py-6 text-center text-white/40 text-sm">Veri bulunamadı</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Orders Table */}
      <div className="bg-navy-900 rounded-xl border border-white/5 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full table-fixed text-[13px] text-left text-white/80">
            <colgroup>
              <col style={{ width: "130px" }} />
              <col style={{ width: "110px" }} />
              <col style={{ width: "90px" }} />
              <col />
              <col style={{ width: "120px" }} />
              <col style={{ width: "60px" }} />
              <col style={{ width: "100px" }} />
              <col style={{ width: "90px" }} />
              <col style={{ width: "90px" }} />
              <col style={{ width: "100px" }} />
              <col style={{ width: "80px" }} />
              <col style={{ width: "100px" }} />
            </colgroup>
            <thead className="bg-navy-800/50 text-white border-b border-white/10 uppercase text-[10px] tracking-wider font-semibold">
              <tr>
                <th className="px-2 py-2 whitespace-nowrap">Sipariş No</th>
                <th className="px-2 py-2 whitespace-nowrap">Tarih</th>
                <th className="px-2 py-2 whitespace-nowrap">Durum</th>
                <th className="px-2 py-2 whitespace-nowrap">Ürün Adı</th>
                <th className="px-2 py-2 whitespace-nowrap">Barkod</th>
                <th className="px-2 py-2 whitespace-nowrap text-right">Adet</th>
                <th className="px-2 py-2 whitespace-nowrap text-right">Satış Fiyatı</th>
                <th className="px-2 py-2 whitespace-nowrap text-right">Gidiş Kargo</th>
                <th className="px-2 py-2 whitespace-nowrap text-right">Geliş Kargo</th>
                <th className="px-2 py-2 whitespace-nowrap text-right">Toplam Kargo</th>
                <th className="px-2 py-2 whitespace-nowrap text-right">Komisyon</th>
                <th className="px-2 py-2 whitespace-nowrap text-right">Net Zarar</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {loading ? (
                <tr>
                  <td colSpan={12} className="px-6 py-8 text-center text-white/50">
                    <div className="flex justify-center items-center gap-3">
                      <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                      İade verileri yükleniyor...
                    </div>
                  </td>
                </tr>
              ) : filteredOrders.length === 0 ? (
                <tr>
                  <td colSpan={12} className="px-6 py-8 text-center text-white/50">
                    Seçilen tarih aralığında iade kaydı bulunamadı.
                  </td>
                </tr>
              ) : (
                filteredOrders.map((order, idx) => {
                  const statusInfo = STATUS_LABELS[order.status] || { label: order.status, color: "text-white/60 bg-white/10" };
                  const netLoss = parseFloat(order.net_loss);

                  return (
                    <tr
                      key={`${order.order_number}-${idx}`}
                      className="hover:bg-white/5 transition-colors"
                    >
                      <td className="px-2 py-1.5 whitespace-nowrap font-mono text-[12px] text-white/70">
                        {order.order_number || "-"}
                      </td>
                      <td className="px-2 py-1.5 whitespace-nowrap text-[12px] text-white/60">
                        {order.date}
                      </td>
                      <td className="px-2 py-1.5 whitespace-nowrap">
                        <span className={clsx("px-2 py-0.5 rounded text-[11px] font-medium", statusInfo.color)}>
                          {statusInfo.label}
                        </span>
                      </td>
                      <td className="px-2 py-1.5 truncate max-w-0" title={order.product_name}>
                        <span className="text-white/90">{order.product_name || "-"}</span>
                      </td>
                      <td className="px-2 py-1.5 whitespace-nowrap text-[12px] text-white/60">
                        {order.barcode || "-"}
                      </td>
                      <td className="px-2 py-1.5 whitespace-nowrap text-right text-white/80">
                        {order.quantity}
                      </td>
                      <td className="px-2 py-1.5 whitespace-nowrap text-right text-white/80">
                        {formatCurrency(parseFloat(order.sale_price))}
                      </td>
                      <td className="px-2 py-1.5 whitespace-nowrap text-right text-white/60">
                        {parseFloat(order.outgoing_cargo) > 0 ? `-${formatCurrency(parseFloat(order.outgoing_cargo))}` : "₺0,00"}
                      </td>
                      <td className="px-2 py-1.5 whitespace-nowrap text-right text-white/60">
                        {parseFloat(order.incoming_cargo) > 0 ? `-${formatCurrency(parseFloat(order.incoming_cargo))}` : "₺0,00"}
                      </td>
                      <td className="px-2 py-1.5 whitespace-nowrap text-right text-red-400 font-medium">
                        {parseFloat(order.total_cargo_loss) > 0 ? `-${formatCurrency(parseFloat(order.total_cargo_loss))}` : "₺0,00"}
                      </td>
                      <td className="px-2 py-1.5 whitespace-nowrap text-right text-white/50">
                        ₺0,00
                      </td>
                      <td className={clsx("px-2 py-1.5 whitespace-nowrap text-right font-bold", netLoss > 0 ? "text-red-400" : "text-white/50")}>
                        {netLoss > 0 ? `-${formatCurrency(netLoss)}` : "₺0,00"}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {!loading && filteredOrders.length > 0 && (
          <div className="px-4 py-2 border-t border-white/5 text-[12px] text-white/40">
            {filteredOrders.length} sipariş gösteriliyor
          </div>
        )}
      </div>
    </div>
  );
}
