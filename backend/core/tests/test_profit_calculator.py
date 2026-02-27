from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from core.models import (
    Organization,
    MarketplaceAccount,
    Order,
    OrderItem,
    FinancialTransaction,
    FinancialTransactionType,
)
from core.services.profit_calculator import ProfitCalculator


class ProfitCalculatorTests(TestCase):
    def test_calculate_for_order_item(self):
        """
        Calculates profit margin and breakdown correctly using absolute decimal transaction values.
        """
        org = Organization.objects.create(name="Test Org")
        account = MarketplaceAccount.objects.create(
            organization=org, store_name="Test Store", seller_id="123"
        )

        order = Order.objects.create(
            organization=org,
            marketplace_account=account,
            marketplace_order_id="12345",
            order_date=timezone.now(),
            status=Order.Status.DELIVERED,
        )

        item = OrderItem.objects.create(
            order=order,
            sale_price_gross=Decimal("150.00"),
            sale_price_net=Decimal("100.00"),  # 50 TL indirimli satış
            quantity=1,
        )

        # 1. Maliyet - Ürün Maliyeti
        FinancialTransaction.objects.create(
            organization=org,
            order_item_ref=item,
            transaction_type=FinancialTransactionType.PRODUCT_COST,
            amount=Decimal("-30.00"),  # Eksi girilse bile motor mutlak değer alacak
            occurred_at=timezone.now(),
        )
        # 2. Maliyet - Komisyon
        FinancialTransaction.objects.create(
            organization=org,
            order_item_ref=item,
            transaction_type=FinancialTransactionType.COMMISSION,
            amount=Decimal("15.00"),  # Pozitif girilse de maliyet hanesinde
            occurred_at=timezone.now(),
        )
        # 3. Maliyet - Kargo
        FinancialTransaction.objects.create(
            organization=org,
            order_item_ref=item,
            transaction_type=FinancialTransactionType.SHIPPING_FEE,
            amount=Decimal("10.50"),
            occurred_at=timezone.now(),
        )

        # Hesapla!
        result = ProfitCalculator.calculate_for_order_item(item)

        # Assertions
        self.assertEqual(result["gross_revenue"], Decimal("150.00"))
        self.assertEqual(result["net_revenue"], Decimal("100.00"))

        # Toplam Maliyet: 30 + 15 + 10.50 = 55.50
        expected_costs = Decimal("55.50")
        self.assertEqual(result["total_costs"], expected_costs)

        # Net Kar: 100 - 55.50 = 44.50
        expected_profit = Decimal("44.50")
        self.assertEqual(result["net_profit"], expected_profit)

        # Kâr Marjı: %44.50 (44.50 / 100.00)
        self.assertEqual(result["profit_margin"], Decimal("44.50"))

        # Ürün Maliyeti Üzerinden Kârlılık: 44.50 / 30.00 = %148.33
        self.assertEqual(result["profit_on_cost"], Decimal("148.33"))

        # Dağılım Map Kontrolleri
        self.assertEqual(
            result["breakdown"][FinancialTransactionType.PRODUCT_COST.value],
            Decimal("30.00"),
        )
        self.assertEqual(
            result["breakdown"][FinancialTransactionType.COMMISSION.value],
            Decimal("15.00"),
        )
        self.assertEqual(
            result["breakdown"][FinancialTransactionType.SHIPPING_FEE.value],
            Decimal("10.50"),
        )
        self.assertEqual(
            result["breakdown"][FinancialTransactionType.PENALTY.value],
            Decimal("0.00"),
        )
