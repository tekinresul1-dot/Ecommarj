"use client";

import { useState, useEffect } from "react";
import { formatCurrency, formatPercentage } from "@/lib/utils/format";
import apiClient from "@/lib/api/client";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ChevronDown, Filter, Download } from "lucide-react";
import clsx from "clsx";

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
}

interface Order {
  id: number;
  order_number: string;
  order_date: string;
  status: string;
  total_gross: string;
  total_profit: string;
  profit_margin: string;
  profit_on_cost: string;
  items: OrderItem[];
  aggregated_breakdown: OrderBreakdown;
}

export default function OrderProfitabilityPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      const result = await apiClient.get<Order[]>("/orders/");
      if (result.ok) {
        setOrders(result.data);
      }
    } catch (error) {
      console.error("Orders fetch error:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white tracking-tight">Sipariş Kârlılık Analizi</h1>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 bg-navy-800 hover:bg-navy-700 text-white/90 px-4 py-2 rounded-lg text-sm font-medium transition-colors border border-white/5">
            <Filter className="w-4 h-4" />
            Filtrele
          </button>
          <button className="flex items-center gap-2 bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors shadow-lg shadow-green-900/20">
            <Download className="w-4 h-4" />
            Raporu İndir
          </button>
        </div>
      </div>

      <div className="bg-navy-900 rounded-xl border border-white/5 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-white/80">
            <thead className="bg-navy-800/50 text-white border-b border-light-navy uppercase text-[10px] tracking-wider font-semibold">
              <tr>
                <th className="px-6 py-4 whitespace-nowrap">Sipariş Numarası</th>
                <th className="px-6 py-4 whitespace-nowrap">Sipariş Tarihi</th>
                <th className="px-6 py-4 whitespace-nowrap">Sipariş Tutarı (₺)</th>
                <th className="px-6 py-4 whitespace-nowrap">Kâr Tutarı (₺)</th>
                <th className="px-6 py-4 whitespace-nowrap">Kâr Oranı (%)</th>
                <th className="px-6 py-4 whitespace-nowrap">Kâr Marjı (%)</th>
                <th className="px-6 py-4 text-center whitespace-nowrap">Detay Bilgiler</th>
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
              ) : orders.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-white/50">
                    Henüz sipariş bulunmuyor.
                  </td>
                </tr>
              ) : (
                orders.map((order) => {
                  const profitVal = parseFloat(order.total_profit);
                  const isProfitable = profitVal > 0;
                  const isLoss = profitVal < 0;

                  return (
                    <tr key={order.id} className="hover:bg-white/5 transition-colors group">
                      <td className="px-6 py-4 whitespace-nowrap font-medium text-blue-400">
                        {order.order_number}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {order.order_date || "-"}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-red-400 font-medium">
                        {formatCurrency(parseFloat(order.total_gross))}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={clsx(
                          "font-medium",
                          isProfitable ? "text-green-400" : isLoss ? "text-red-400" : "text-white/80"
                        )}>
                          {formatCurrency(profitVal)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={clsx(
                          "font-medium",
                          isProfitable ? "text-green-400" : isLoss ? "text-red-400" : "text-white/80"
                        )}>
                          {formatPercentage(parseFloat(order.profit_on_cost))}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={clsx(
                          "font-medium",
                          isProfitable ? "text-green-400" : isLoss ? "text-red-400" : "text-white/80"
                        )}>
                          {formatPercentage(parseFloat(order.profit_margin))}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-center whitespace-nowrap">
                        <button
                          onClick={() => setSelectedOrder(order)}
                          className="bg-navy-800 hover:bg-navy-700 text-white/90 text-xs px-4 py-2 rounded-md transition-colors border border-white/10"
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
  if (!order) return null;

  // Detailed panel matches screenshot 2
  return (
    <Dialog open={!!order} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-4xl bg-navy-950 border-white/10 text-white p-0 overflow-hidden">
        <div className="p-6 border-b border-white/10 flex items-center gap-4 bg-navy-900/50">
          <div className="w-12 h-12 rounded-full bg-blue-500/20 flex items-center justify-center border border-blue-500/30">
            <ShoppingBag className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <DialogTitle className="text-xl font-bold">Sipariş Analizi</DialogTitle>
            <p className="text-sm text-white/60">#{order.order_number} • {order.order_date}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 max-h-[70vh] overflow-y-auto">

          {/* Items Column */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-white/90 flex items-center gap-2">
                <Package className="w-4 h-4 text-orange-400" />
                Siparişteki Ürünler
              </h3>
              <span className="bg-orange-500/20 text-orange-400 text-xs px-2 py-1 rounded-full font-medium border border-orange-500/20">
                {order.items.length} Kalem
              </span>
            </div>

            <div className="space-y-4">
              {order.items.map((item, idx) => (
                <div key={idx} className="bg-navy-900 border border-white/5 rounded-xl p-4 flex gap-4 items-start">
                  <div className="w-20 h-24 bg-navy-800 rounded-lg flex-shrink-0 border border-white/10">
                    {/* Mock Image Placeholder */}
                  </div>
                  <div className="flex-1">
                    <h4 className="font-medium text-sm text-white/90 leading-snug mb-2">{item.title}</h4>
                    <p className="text-xs text-white/60 mb-1">Barkod: <span className="text-orange-400 font-medium">{item.barcode}</span></p>
                    <p className="text-xs text-white/60 mb-1">Komisyon Oranı: <span className="text-orange-400 font-medium">%{item.commission_rate}</span></p>
                    <div className="text-right mt-2">
                      <span className="text-red-400 font-bold text-lg">{formatCurrency(parseFloat(item.sale_price_gross))}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Expenses Column */}
          <div>
            <h3 className="font-semibold text-white/90 flex items-center gap-2 mb-4">
              <AlertCircle className="w-4 h-4 text-red-400" />
              Gider Kalemleri
            </h3>

            <div className="space-y-3">
              <ExpenseRow label="Kargo Ücreti" amount={parseFloat(order.aggregated_breakdown.shipping_fee)} />

              {/* Nested KDV Row */}
              <div className="bg-navy-900 border border-white/5 rounded-xl overflow-hidden">
                <div className="p-4 flex justify-between items-center cursor-pointer hover:bg-white/5">
                  <div className="flex items-center gap-2">
                    <ChevronDown className="w-4 h-4 text-white/40" />
                    <span className="font-medium text-white/80">Net KDV</span>
                  </div>
                  <span className="font-semibold text-red-400">-{formatCurrency(parseFloat(order.aggregated_breakdown.net_kdv))}</span>
                </div>
                <div className="px-4 pb-4 pt-1 space-y-3 border-t border-white/5 bg-navy-800/20 text-sm">
                  <div className="flex justify-between items-center text-white/60">
                    <span>Satış KDV</span>
                    <span className="text-orange-400">{formatCurrency(parseFloat(order.aggregated_breakdown.satis_kdv))}</span>
                  </div>
                  <div className="flex justify-between items-center text-white/60">
                    <span>Maliyet KDV</span>
                    <span className="text-white/80">{formatCurrency(parseFloat(order.aggregated_breakdown.alis_kdv))}</span>
                  </div>
                  <div className="flex justify-between items-center text-white/60">
                    <span>Komisyon KDV</span>
                    <span className="text-white/80">{formatCurrency(parseFloat(order.aggregated_breakdown.komisyon_kdv))}</span>
                  </div>
                  <div className="flex justify-between items-center text-white/60">
                    <span>Kargo Ücreti KDV</span>
                    <span className="text-white/80">{formatCurrency(parseFloat(order.aggregated_breakdown.kargo_kdv))}</span>
                  </div>
                  <div className="flex justify-between items-center text-white/60">
                    <span>Hizmet Bedeli KDV</span>
                    <span className="text-white/80">{formatCurrency(parseFloat(order.aggregated_breakdown.hizmet_bedeli_kdv))}</span>
                  </div>
                </div>
              </div>

              <ExpenseRow label="Ürün Maliyeti" amount={parseFloat(order.aggregated_breakdown.product_cost)} />
              <ExpenseRow label="Komisyon Tutarı" amount={parseFloat(order.aggregated_breakdown.commission)} />
              <ExpenseRow label="Hizmet Bedeli" amount={parseFloat(order.aggregated_breakdown.service_fee)} />
            </div>
          </div>

        </div>
      </DialogContent>
    </Dialog>
  );
}

function ExpenseRow({ label, amount }: { label: string, amount: number }) {
  return (
    <div className="bg-navy-900 border border-white/5 rounded-xl p-4 flex justify-between items-center hover:bg-white/5 transition-colors">
      <span className="font-medium text-white/80 flex items-center gap-2">
        <FileText className="w-4 h-4 text-white/40" />
        {label}
      </span>
      <span className="font-semibold text-orange-400">{formatCurrency(amount)}</span>
    </div>
  );
}

// Ensure icons are imported
import { ShoppingBag, Package, AlertCircle, FileText } from "lucide-react";