"use client";

import { useState, useEffect } from "react";
import { formatCurrency, formatPercentage } from "@/lib/utils/format";
import apiClient from "@/lib/api/client";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ChevronDown, Filter, Download, ShoppingBag, Package, AlertCircle, FileText, RefreshCw } from "lucide-react";
import clsx from "clsx";

import { TableFilter, FilterState, FilterColumn, applyTableFilter } from "@/components/dashboard/TableFilter";
import { DatePickerWithRange } from "@/components/dashboard/DateRangePicker";
import { DateRange } from "react-day-picker";
import { format, subDays } from "date-fns";

interface OrderBreakdown {
  product_cost: string;
  commission: string;
  shipping_fee: string;
  service_fee: string;
  withholding: string;
  net_kdv: string;
  satis_kdv: string;
  alis_kdv: string;
  kargo_kdv: string;
  komisyon_kdv: string;
  hizmet_bedeli_kdv: string;
}

interface OrderItem {
  id: number;
  title: string;
  barcode: string;
  quantity: number;
  sale_price_gross: string;
  commission_rate: string;
  image_url?: string;
}

interface Order {
  id: number;
  order_number: string;
  order_date: string;
  status: string;
  is_micro_export?: boolean;
  total_gross: string;
  total_profit: string;
  profit_margin: string;
  profit_on_cost: string;
  items: OrderItem[];
  aggregated_breakdown: OrderBreakdown;
}

const FILTER_COLUMNS: FilterColumn[] = [
  { id: "order_number", label: "Sipariş Numarası", type: "text" },
  { id: "order_date", label: "Sipariş Tarihi", type: "text" },
  { id: "total_gross", label: "Sipariş Tutarı (₺)", type: "number" },
  { id: "total_profit", label: "Kâr Tutarı (₺)", type: "number" },
  { id: "profit_on_cost", label: "Kâr Oranı (%)", type: "number" },
  { id: "profit_margin", label: "Kâr Marjı (%)", type: "number" },
];

export default function OrderProfitabilityPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);

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
  }, [date]); // Run automatically when date changes

  const fetchOrders = async (minDate?: string, maxDate?: string) => {
    setLoading(true);
    try {
      let url = "/orders/";
      if (minDate && maxDate) {
        url += `?min_date=${minDate}&max_date=${maxDate}`;
      }
      const result = await apiClient.get<Order[]>(url);
      if (result.ok && result.data) {
        setOrders(result.data);
      }
    } catch (error) {
      console.error("Orders fetch error:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDateFilter = () => {
    if (date?.from && date?.to) {
      fetchOrders(format(date.from, "yyyy-MM-dd"), format(date.to, "yyyy-MM-dd"));
    } else {
      fetchOrders();
    }
  };

  const filteredOrders = applyTableFilter(orders, tableFilter);

  return (
    <div className="p-6">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20">
            <ShoppingBag className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Sipariş Kârlılık Analizi</h1>
            <p className="text-xs text-white/40 mt-0.5">Siparişlerinizin detaylı kârlılık hesapları</p>
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
                <th className="px-5 py-4 whitespace-nowrap">Sipariş Numarası</th>
                <th className="px-5 py-4 whitespace-nowrap">Sipariş Tarihi</th>
                <th className="px-5 py-4 whitespace-nowrap text-right">Sipariş Tutarı (₺)</th>
                <th className="px-5 py-4 whitespace-nowrap text-right">Kâr Tutarı (₺)</th>
                <th className="px-5 py-4 whitespace-nowrap text-right">Kâr Oranı (%)</th>
                <th className="px-5 py-4 whitespace-nowrap text-right">Kâr Marjı (%)</th>
                <th className="px-5 py-4 text-center whitespace-nowrap">Detay</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-white/50">
                    <div className="flex justify-center items-center gap-3">
                      <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                      Siparişler yükleniyor...
                    </div>
                  </td>
                </tr>
              ) : filteredOrders.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-white/50">
                    Sipariş bulunamadı. Filtreleri temizlemeyi deneyin.
                  </td>
                </tr>
              ) : (
                filteredOrders.map((order) => {
                  const profitVal = parseFloat(order.total_profit);
                  const isProfitable = profitVal > 0;
                  const isLoss = profitVal < 0;

                  return (
                    <tr key={order.id} className="hover:bg-white/5 transition-colors group cursor-pointer" onClick={() => setSelectedOrder(order)}>
                      <td className="px-5 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-blue-400">{order.order_number}</span>
                          {order.is_micro_export && (
                            <span className="px-2 py-0.5 rounded-full bg-teal-500/10 text-teal-400 border border-teal-500/20 text-[10px] font-bold uppercase tracking-wider">
                              Mikro
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-5 py-4 whitespace-nowrap text-white/60">
                        {order.order_date || "-"}
                      </td>
                      <td className="px-5 py-4 whitespace-nowrap text-right font-medium text-white/80">
                        {formatCurrency(parseFloat(order.total_gross))}
                      </td>
                      <td className="px-5 py-4 whitespace-nowrap text-right">
                        <span className={clsx(
                          "font-bold",
                          isProfitable ? "text-green-400" : isLoss ? "text-red-400" : "text-white/80"
                        )}>
                          {formatCurrency(profitVal)}
                        </span>
                      </td>
                      <td className="px-5 py-4 whitespace-nowrap text-right">
                        <span className={clsx(
                          "font-medium",
                          isProfitable ? "text-green-400" : isLoss ? "text-red-400" : "text-white/80"
                        )}>
                          {formatPercentage(parseFloat(order.profit_on_cost))}
                        </span>
                      </td>
                      <td className="px-5 py-4 whitespace-nowrap text-right">
                        <span className={clsx(
                          "font-medium",
                          isProfitable ? "text-green-400" : isLoss ? "text-red-400" : "text-white/80"
                        )}>
                          {formatPercentage(parseFloat(order.profit_margin))}
                        </span>
                      </td>
                      <td className="px-5 py-4 text-center whitespace-nowrap">
                        <button
                          onClick={(e) => { e.stopPropagation(); setSelectedOrder(order); }}
                          className="bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 text-xs px-4 py-2 rounded-lg transition-colors border border-blue-500/20 font-medium"
                        >
                          Detaylar
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      <OrderDetailsModal order={selectedOrder} onClose={() => setSelectedOrder(null)} />
    </div>
  );
}

function OrderDetailsModal({ order, onClose }: { order: Order | null, onClose: () => void }) {
  const [kdvOpen, setKdvOpen] = useState(false);

  if (!order) return null;

  const profitVal = parseFloat(order.total_profit);
  const isProfitable = profitVal > 0;

  return (
    <Dialog open={!!order} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-5xl bg-navy-950 border-white/10 text-white p-0 overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-white/10 bg-gradient-to-r from-navy-900 to-navy-950">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500/20 to-indigo-500/20 flex items-center justify-center border border-blue-500/30">
              <ShoppingBag className="w-7 h-7 text-blue-400" />
            </div>
            <div className="flex-1">
              <DialogTitle className="text-xl font-bold tracking-tight">Sipariş Detayı</DialogTitle>
              <div className="flex items-center gap-3 mt-1.5">
                <span className="text-sm text-white/50">#{order.order_number}</span>
                <span className="text-xs text-white/30">•</span>
                <span className="text-sm text-white/50">{order.order_date}</span>
                <span className={clsx(
                  "text-xs px-2.5 py-0.5 rounded-full font-medium border",
                  order.status === "Delivered" ? "bg-green-500/10 text-green-400 border-green-500/20" :
                    order.status === "Shipped" ? "bg-blue-500/10 text-blue-400 border-blue-500/20" :
                      order.status === "Cancelled" || order.status === "Returned" ? "bg-red-500/10 text-red-400 border-red-500/20" :
                        "bg-yellow-500/10 text-yellow-400 border-yellow-500/20"
                )}>
                  {order.status}
                </span>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs text-white/40 font-medium uppercase tracking-wider mb-1">Net Kâr</p>
              <p className={clsx("text-2xl font-bold", isProfitable ? "text-green-400" : "text-red-400")}>
                {formatCurrency(profitVal)}
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-0 max-h-[65vh] overflow-y-auto">

          {/* Items Column (3/5) */}
          <div className="lg:col-span-3 p-6 border-r border-white/5">
            <div className="flex items-center justify-between mb-5">
              <h3 className="font-semibold text-white/90 flex items-center gap-2 text-sm">
                <Package className="w-4 h-4 text-orange-400" />
                Siparişteki Ürünler
              </h3>
              <span className="bg-orange-500/10 text-orange-400 text-xs px-3 py-1 rounded-full font-semibold border border-orange-500/20">
                {order.items.length} Kalem
              </span>
            </div>

            <div className="space-y-3">
              {order.items.map((item, idx) => (
                <div key={idx} className="bg-navy-900/80 border border-white/5 rounded-xl p-4 flex gap-4 items-start hover:border-white/10 transition-colors">
                  <div className="w-16 h-20 bg-navy-800 rounded-lg flex-shrink-0 border border-white/10 overflow-hidden">
                    {item.image_url ? (
                      <img src={item.image_url} alt={item.title} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <Package className="w-6 h-6 text-white/20" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium text-sm text-white/90 leading-snug mb-2 line-clamp-2">{item.title}</h4>
                    <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs">
                      <span className="text-white/50">Barkod: <span className="text-orange-400 font-medium">{item.barcode}</span></span>
                      <span className="text-white/50">Adet: <span className="text-white/80 font-medium">{item.quantity}</span></span>
                      <span className="text-white/50">Komisyon: <span className="text-purple-400 font-medium">%{parseFloat(item.commission_rate).toFixed(2)}</span></span>
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-lg font-bold text-white">{formatCurrency(parseFloat(item.sale_price_gross))}</p>
                    <p className="text-[10px] text-white/40 mt-0.5">Satış Tutarı</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Expenses Column (2/5) */}
          <div className="lg:col-span-2 p-6 bg-navy-900/20">
            <h3 className="font-semibold text-white/90 flex items-center gap-2 mb-5 text-sm">
              <AlertCircle className="w-4 h-4 text-red-400" />
              Gider Kalemleri
            </h3>

            <div className="space-y-2.5">
              <ExpenseRow label="Ürün Maliyeti" amount={parseFloat(order.aggregated_breakdown.product_cost)} icon="💰" />
              <ExpenseRow label="Komisyon Tutarı" amount={parseFloat(order.aggregated_breakdown.commission)} icon="🏷️" />
              <ExpenseRow label="Kargo Ücreti" amount={parseFloat(order.aggregated_breakdown.shipping_fee)} icon="📦" />
              <ExpenseRow label="Hizmet Bedeli" amount={parseFloat(order.aggregated_breakdown.service_fee)} icon="🧾" />
              {parseFloat(order.aggregated_breakdown.withholding) > 0 && (
                <ExpenseRow label="Stopaj Kesintisi" amount={parseFloat(order.aggregated_breakdown.withholding)} icon="📄" />
              )}

              {/* Collapsible KDV Section */}
              <div className="bg-navy-900 border border-white/5 rounded-xl overflow-hidden">
                <button
                  onClick={() => setKdvOpen(!kdvOpen)}
                  className="w-full p-3.5 flex justify-between items-center hover:bg-white/5 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <ChevronDown className={clsx("w-4 h-4 text-white/40 transition-transform", kdvOpen && "rotate-180")} />
                    <span className="font-medium text-white/80 text-sm">Net KDV</span>
                  </div>
                  <span className="font-bold text-red-400 text-sm">-{formatCurrency(parseFloat(order.aggregated_breakdown.net_kdv))}</span>
                </button>
                {kdvOpen && (
                  <div className="px-4 pb-3 space-y-2 border-t border-white/5 bg-navy-800/30">
                    <KdvRow label="Satış KDV" amount={order.aggregated_breakdown.satis_kdv} />
                    <KdvRow label="Maliyet KDV" amount={order.aggregated_breakdown.alis_kdv} />
                    <KdvRow label="Komisyon KDV" amount={order.aggregated_breakdown.komisyon_kdv} />
                    <KdvRow label="Kargo Ücreti KDV" amount={order.aggregated_breakdown.kargo_kdv} />
                    <KdvRow label="Hizmet Bedeli KDV" amount={order.aggregated_breakdown.hizmet_bedeli_kdv} />
                  </div>
                )}
              </div>
            </div>

            {/* Profit Summary */}
            <div className="mt-6 pt-4 border-t border-white/10">
              <div className="space-y-2">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-white/50">Toplam Ciro</span>
                  <span className="font-semibold text-white">{formatCurrency(parseFloat(order.total_gross))}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-white/50">Net Kâr</span>
                  <span className={clsx("font-bold text-lg", isProfitable ? "text-green-400" : "text-red-400")}>
                    {formatCurrency(profitVal)}
                  </span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-white/50">Kâr Marjı</span>
                  <span className={clsx("font-semibold", isProfitable ? "text-green-400" : "text-red-400")}>
                    {formatPercentage(parseFloat(order.profit_margin))}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function ExpenseRow({ label, amount, icon }: { label: string; amount: number; icon: string }) {
  return (
    <div className="bg-navy-900 border border-white/5 rounded-xl p-3.5 flex justify-between items-center hover:bg-white/5 transition-colors">
      <span className="font-medium text-white/70 flex items-center gap-2 text-sm">
        <span className="text-base">{icon}</span>
        {label}
      </span>
      <span className="font-bold text-orange-400 text-sm">{formatCurrency(amount)}</span>
    </div>
  );
}

function KdvRow({ label, amount }: { label: string; amount: string }) {
  return (
    <div className="flex justify-between items-center text-xs text-white/60 pt-1.5">
      <span>{label}</span>
      <span className="text-white/80 font-medium">{formatCurrency(parseFloat(amount))}</span>
    </div>
  );
}