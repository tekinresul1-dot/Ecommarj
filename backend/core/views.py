from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from decimal import Decimal

from core.models import Order, OrderItem, FinancialTransactionType
from core.services.profit_calculator import ProfitCalculator

class DashboardOverviewView(APIView):
    """
    GET /api/dashboard/overview
    Filtrelere göre Sipariş, Ürün ve Finansal verileri toplayıp gerçek KPI döndürür.
    Mikro ihracat ve Trendyol olarak 'channel' parametresiyle çalışır.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        org = getattr(user.profile, 'organization', None)

        if not org:
            return Response({"error": "Kullanıcının bir organizasyonu bulunamadı."}, status=400)

        # Filtreleri al
        channel = request.query_params.get("channel", "trendyol")
        countries = request.query_params.get("countries", "") # virgülle ayrılmış

        # Organizasyonun siparişlerini çek
        orders_qs = Order.objects.select_related("marketplace_account").filter(
            organization=org, channel=channel
        )

        if countries:
            country_list = [c.strip() for c in countries.split(",")]
            orders_qs = orders_qs.filter(country_code__in=country_list)

        total_orders = orders_qs.count()
        order_items = OrderItem.objects.select_related("order").prefetch_related("transactions").filter(order__in=orders_qs)

        total_gross = Decimal("0.00")
        total_net = Decimal("0.00")
        total_costs = Decimal("0.00")
        total_profit = Decimal("0.00")
        
        breakdown = {tx_type.value: Decimal("0.00") for tx_type in FinancialTransactionType}
        country_profits = {}
        
        # Ek Metrik Havuzları (Rakip UI için)
        total_items_sold = 0
        total_cargo_cost = Decimal("0.00")
        total_commission_cost = Decimal("0.00")
        total_discount = Decimal("0.00")
        
        # Funnel için Toplamlar (Brüt Ciro -> Kargo Düşülmüş -> Pazaryeri Masrafı Düşülmüş -> Vergi Düşülmüş -> Net)
        funnel_gross = Decimal("0.00")
        funnel_cargo = Decimal("0.00")
        funnel_marketplace_fees = Decimal("0.00") # Komisyon + Hizmet bedeli + Ceza vs
        funnel_taxes = Decimal("0.00")            # Satış KDV + Stopaj
        funnel_net = Decimal("0.00")

        # Profit motoruyla her satırı tek tek hesapla
        for item in order_items:
            res = ProfitCalculator.calculate_for_order_item(item)
            
            gross = res["gross_revenue"]
            net = res["net_revenue"]
            costs = res["total_costs"]
            profit = res["net_profit"]
            
            total_gross += gross
            total_net += net
            total_costs += costs
            total_profit += profit
            total_items_sold += item.quantity
            total_discount += item.discount
            
            funnel_gross += gross
            
            item_cargo = Decimal("0.00")
            item_mp_fees = Decimal("0.00")
            item_taxes = Decimal("0.00")
            
            for k, v in res["breakdown"].items():
                breakdown[k] += v
                if k == FinancialTransactionType.SHIPPING_FEE.value:
                    item_cargo += v
                    total_cargo_cost += v
                elif k == FinancialTransactionType.COMMISSION.value:
                    item_mp_fees += v
                    total_commission_cost += v
                elif k in [FinancialTransactionType.SERVICE_FEE.value, FinancialTransactionType.PENALTY.value]:
                    item_mp_fees += v
                elif k in [FinancialTransactionType.VAT_OUTPUT.value, FinancialTransactionType.WITHHOLDING.value]:
                    item_taxes += v
            
            funnel_cargo += item_cargo
            funnel_marketplace_fees += item_mp_fees
            funnel_taxes += item_taxes
            
            c_code = item.order.country_code
            country_profits[c_code] = country_profits.get(c_code, Decimal("0.00")) + profit

        funnel_net = total_profit

        # Kâr Marjları ve Oranlar
        profit_margin = Decimal("0.00")
        if total_net > Decimal("0.00"):
            profit_margin = (total_profit / total_net) * Decimal("100.00")
            
        profit_on_cost_ratio = Decimal("0.00")
        total_product_cost = breakdown.get(FinancialTransactionType.PRODUCT_COST.value, Decimal("0.00"))
        if total_product_cost > Decimal("0.00"):
            profit_on_cost_ratio = (total_profit / total_product_cost) * Decimal("100.00")

        # Kayıp Kaçak (Ceza + İade + Erken Ödeme)
        lost_and_leakage = (
            breakdown.get(FinancialTransactionType.PENALTY.value, Decimal("0")) +
            breakdown.get(FinancialTransactionType.RETURN_LOSS.value, Decimal("0")) +
            breakdown.get(FinancialTransactionType.EARLY_PAYMENT.value, Decimal("0"))
        )
        
        # --- Ek: Metrik Listeleri (Sipariş, Ürün, İade vs) ---
        
        # Sipariş Metrikleri
        order_metrics = {
            "order_count": total_orders,
            "avg_revenue_per_order": str(round(total_net / total_orders, 2)) if total_orders > 0 else "0.00",
            "avg_profit_per_order": str(round(total_profit / total_orders, 2)) if total_orders > 0 else "0.00",
            "avg_cargo_per_order": str(round(total_cargo_cost / total_orders, 2)) if total_orders > 0 else "0.00",
        }
        
        # Ürün Metrikleri
        product_metrics = {
            "items_sold": total_items_sold,
            "avg_revenue_per_item": str(round(total_net / total_items_sold, 2)) if total_items_sold > 0 else "0.00",
            "avg_profit_per_item": str(round(total_profit / total_items_sold, 2)) if total_items_sold > 0 else "0.00",
            "avg_cargo_per_item": str(round(total_cargo_cost / total_items_sold, 2)) if total_items_sold > 0 else "0.00",
            "avg_commission_rate": str(round((total_commission_cost / total_gross)*100, 2)) if total_gross > 0 else "0.00",
            "avg_discount_rate": str(round((total_discount / total_gross)*100, 2)) if total_gross > 0 else "0.00",
        }
        
        # İade Metrikleri (Şimdilik mock veya iade tutarlarından)
        return_loss_val = breakdown.get(FinancialTransactionType.RETURN_LOSS.value, Decimal("0.00"))
        return_metrics = {
            "return_rate": "12.5", # Mock - Sipariş durumuna göre yapılmalı
            "total_return_cost": str(return_loss_val),
            "return_cargo_loss": str(round(return_loss_val * Decimal("0.6"), 2)), # Örnek kargo yansıması
            "overseas_operation_fee": "0.00"
        }
        
        # Reklam Metrikleri
        ads_val = breakdown.get(FinancialTransactionType.ADS_COST.value, Decimal("0.00"))
        ads_metrics = {
            "total_ads_cost": str(ads_val),
            "influencer_cut": "0.00",
            "ads_profit_index": str(round((ads_val / total_profit)*100, 2)) if total_profit > 0 else "0.00",
            "ads_revenue_index": str(round((ads_val / total_net)*100, 2)) if total_net > 0 else "0.00",
        }
        
        # Net Kâr Performansı Hunisi (Funnel)
        net_profit_funnel = [
            {"name": "Ciro", "value": str(funnel_gross)},
            {"name": "Kargo Düşülmüş", "value": str(funnel_gross - funnel_cargo)},
            {"name": "Pazaryeri Masrafı Düşülmüş", "value": str(funnel_gross - funnel_cargo - funnel_marketplace_fees)},
            {"name": "Vergi Düşülmüş", "value": str(funnel_gross - funnel_cargo - funnel_marketplace_fees - funnel_taxes)},
            {"name": "Kâr", "value": str(funnel_net)},
        ]
        
        # Geçici Kâr Performansı History (Area Chart için)
        from datetime import timedelta
        history = []
        for i in range(5, -1, -1):
            history.append({
                "date": (timezone.now() - timedelta(days=i)).strftime("%d %b"),
                "profit": str(round(total_profit / 6 + Decimal(i * 10), 2)) # Mock trend distribution
            })

        return Response({
            "kpis": {
                "total_orders": total_orders,
                "gross_revenue": str(total_gross),
                "net_revenue": str(total_net),
                "total_costs": str(total_costs),
                "net_profit": str(total_profit),
                "profit_margin": str(round(profit_margin, 2)),
                "profit_on_cost_ratio": str(round(profit_on_cost_ratio, 2)),
                "lost_and_leakage": str(lost_and_leakage),
            },
            "profit_breakdown": {k: str(v) for k, v in breakdown.items()},
            "country_profit": [{"country": k, "profit": str(v)} for k, v in country_profits.items()],
            "order_metrics": order_metrics,
            "product_metrics": product_metrics,
            "return_metrics": return_metrics,
            "ads_metrics": ads_metrics,
            "net_profit_funnel": net_profit_funnel,
            "profit_performance_history": history,
        })


class MockReportsView(APIView):
    """
    Diğer listeleme sayfaları için geçici endpoint (UI'ın çalışması adına boş veya mock liste döner)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, report_type):
        return Response({
            "report_type": report_type,
            "data": []
        })
