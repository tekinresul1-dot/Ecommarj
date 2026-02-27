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

        # Profit motoruyla her satırı tek tek hesapla
        for item in order_items:
            res = ProfitCalculator.calculate_for_order_item(item)
            
            total_gross += res["gross_revenue"]
            total_net += res["net_revenue"]
            total_costs += res["total_costs"]
            total_profit += res["net_profit"]
            
            for k, v in res["breakdown"].items():
                breakdown[k] += v
                
            c_code = item.order.country_code
            country_profits[c_code] = country_profits.get(c_code, Decimal("0.00")) + res["net_profit"]

        profit_margin = Decimal("0.00")
        if total_net > Decimal("0.00"):
            profit_margin = (total_profit / total_net) * Decimal("100.00")

        # Kayıp Kaçak (Ceza + İade + Erken Ödeme vs)
        lost_and_leakage = (
            breakdown.get(FinancialTransactionType.PENALTY.value, Decimal("0")) +
            breakdown.get(FinancialTransactionType.RETURN_LOSS.value, Decimal("0")) +
            breakdown.get(FinancialTransactionType.EARLY_PAYMENT.value, Decimal("0"))
        )

        return Response({
            "kpis": {
                "total_orders": total_orders,
                "gross_revenue": str(total_gross),
                "net_revenue": str(total_net),
                "total_costs": str(total_costs),
                "net_profit": str(total_profit),
                "profit_margin": str(round(profit_margin, 2)),
                "lost_and_leakage": str(lost_and_leakage),
            },
            "profit_breakdown": {k: str(v) for k, v in breakdown.items()},
            "country_profit": [{"country": k, "profit": str(v)} for k, v in country_profits.items()],
            # Şimdilik boş dönebilir, UI'da test edince içi doldurulur
            "commission_trend": [],
            "cargo_trend": [],
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
