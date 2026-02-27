from decimal import Decimal
from typing import Dict, Any
from core.models import OrderItem, FinancialTransactionType

class ProfitCalculator:
    """
    Sipariş kalemi (OrderItem) bazında kârlılık parçalanımı (Profit Breakdown) hesaplayan servis.
    Tüm işlemler `Decimal` ile yapılır.
    """

    @staticmethod
    def calculate_for_order_item(order_item: OrderItem) -> Dict[str, Any]:
        """
        OrderItem nesnesine bağlı FinancialTransaction'ları toplayarak net kâr/zarar çıkarır.
        """
        # Başlangıç değerleri (Tüm kalemler map içinde)
        breakdown = {tx_type.value: Decimal("0.00") for tx_type in FinancialTransactionType}
        
        transactions = order_item.transactions.all()
        total_costs = Decimal("0.00")

        for tx in transactions:
            # İşlem tutarını mutlak değere çevirerek maliyet havuzuna ekliyoruz.
            val = abs(tx.amount)
            if tx.transaction_type in breakdown:
                breakdown[tx.transaction_type] += val
                total_costs += val

        # Net Satış (İndirim sonrası KDV dahil tahsil edilen tutar)
        net_revenue = order_item.sale_price_net
        gross_revenue = order_item.sale_price_gross

        # Net Kâr = Net Satış - Toplam Maliyet (Ürün maliyeti + Komisyon + Kargo vs.)
        net_profit = net_revenue - total_costs

        profit_margin = Decimal("0.00")
        if net_revenue > Decimal("0.00"):
            profit_margin = (net_profit / net_revenue) * Decimal("100.00")

        product_cost = breakdown.get(FinancialTransactionType.PRODUCT_COST.value, Decimal("0.00"))
        profit_on_cost = Decimal("0.00")
        if product_cost > Decimal("0.00"):
            profit_on_cost = (net_profit / product_cost) * Decimal("100.00")

        return {
            "gross_revenue": gross_revenue,
            "net_revenue": net_revenue,
            "total_costs": total_costs,
            "net_profit": net_profit,
            "profit_margin": round(profit_margin, 2),
            "profit_on_cost": round(profit_on_cost, 2),
            "breakdown": breakdown
        }
