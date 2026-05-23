from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from core.models import (
    CheTransaction,
    MarketplaceAccount,
    Order,
    OrderItem,
    Organization,
    Product,
    ProductVariant,
    UserProfile,
)
from core.views import DashboardOverviewView, parse_istanbul_date_range


class DashboardOverviewRevenueTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Mahfel Test")
        self.user = get_user_model().objects.create_user(
            username="mahfel-test",
            email="mahfel-test@example.com",
            password="x",
            is_staff=True,
        )
        UserProfile.objects.create(user=self.user, organization=self.org, admin_override=True)
        self.account = MarketplaceAccount.objects.create(
            organization=self.org,
            store_name="Mahfel",
            seller_id="123456",
            api_key="x",
            api_secret="y",
        )
        self.product = Product.objects.create(
            organization=self.org,
            marketplace_account=self.account,
            marketplace_sku="P1",
            title="Test ürün",
            vat_rate=Decimal("10.00"),
            commission_rate=Decimal("10.00"),
        )
        self.costed_variant = ProductVariant.objects.create(
            product=self.product,
            barcode="BC-COST",
            cost_price=Decimal("40.00"),
        )
        self.uncosted_variant = ProductVariant.objects.create(
            product=self.product,
            barcode="BC-NOCOST",
            cost_price=Decimal("0.00"),
        )
        self.factory = APIRequestFactory()

    def _order(self, number, status, dt, variant, gross, net, discount, last_modified=None):
        order = Order.objects.create(
            organization=self.org,
            marketplace_account=self.account,
            marketplace_order_id=number,
            package_id=f"PKG-{number}",
            order_number=number,
            order_date=dt,
            last_modified_date=last_modified,
            status=status,
            channel=Order.Channel.TRENDYOL,
        )
        OrderItem.objects.create(
            order=order,
            product_variant=variant,
            marketplace_line_id=f"LINE-{number}",
            sku=variant.barcode,
            quantity=1,
            sale_price_gross=Decimal(gross),
            sale_price_net=Decimal(net),
            discount=Decimal(discount),
        )
        return order

    def _get_dashboard(self):
        request = self.factory.get(
            "/api/dashboard/overview/?min_date=2026-04-23&max_date=2026-05-23&channel=trendyol"
        )
        force_authenticate(request, user=self.user)
        return DashboardOverviewView.as_view()(request)

    def test_date_range_is_istanbul_inclusive(self):
        start, end = parse_istanbul_date_range("2026-04-23", "2026-05-23")

        self.assertEqual(start.isoformat(), "2026-04-23T00:00:00+03:00")
        self.assertEqual(end.isoformat(), "2026-05-23T23:59:59.999999+03:00")

    def test_total_revenue_uses_trendyol_net_sales_formula(self):
        ist = ZoneInfo("Europe/Istanbul")
        in_range = datetime(2026, 5, 23, 22, 30, tzinfo=ist)
        self._order("D1", Order.Status.DELIVERED, in_range, self.costed_variant, "120.00", "100.00", "20.00")
        self._order("S1", Order.Status.SHIPPED, in_range, self.uncosted_variant, "240.00", "200.00", "40.00")
        self._order("P1", Order.Status.PICKING, in_range, self.costed_variant, "60.00", "50.00", "10.00")
        self._order("C1", Order.Status.CANCELLED, in_range, self.costed_variant, "999.00", "900.00", "99.00")

        response = self._get_dashboard()
        self.assertEqual(response.status_code, 200)

        kpis = response.data["kpis"]
        debug = response.data["debug"]
        self.assertEqual(Decimal(debug["gross_sales_total"]), Decimal("1359.00"))
        self.assertEqual(Decimal(debug["cancelled_total"]), Decimal("900.00"))
        self.assertEqual(Decimal(debug["returned_total"]), Decimal("0.00"))
        self.assertEqual(Decimal(debug["discount_total"]), Decimal("159.00"))
        self.assertEqual(Decimal(kpis["toplam_ciro"]), Decimal("300.00"))
        self.assertEqual(Decimal(kpis["costed_revenue"]), Decimal("100.00"))
        self.assertEqual(debug["included_items_count"], 2)
        self.assertEqual(debug["excluded_by_status_count"], 2)
        self.assertEqual(debug["excluded_by_missing_cost_count"], 1)

    def test_che_return_amount_is_subtracted_from_dashboard_revenue(self):
        ist = ZoneInfo("Europe/Istanbul")
        in_range = datetime(2026, 5, 10, 12, 0, tzinfo=ist)
        self._order("D3", Order.Status.DELIVERED, in_range, self.costed_variant, "500.00", "450.00", "50.00")
        CheTransaction.objects.create(
            organization=self.org,
            account=self.account,
            transaction_id="CHE-RETURN-1",
            transaction_date=in_range,
            order_date=in_range,
            order_number="D3",
            barcode=self.costed_variant.barcode,
            source=CheTransaction.SOURCE_SETTLEMENTS,
            transaction_type="İade",
            transaction_type_code="Return",
            debt=Decimal("120.00"),
            credit=Decimal("0.00"),
        )

        response = self._get_dashboard()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Decimal(response.data["debug"]["gross_sales_total"]), Decimal("500.00"))
        self.assertEqual(Decimal(response.data["debug"]["returned_che_total"]), Decimal("120.00"))
        self.assertEqual(Decimal(response.data["kpis"]["toplam_ciro"]), Decimal("330.00"))

    def test_discount_is_not_subtracted_twice(self):
        ist = ZoneInfo("Europe/Istanbul")
        self._order(
            "D2",
            Order.Status.DELIVERED,
            datetime(2026, 5, 1, 12, 0, tzinfo=ist),
            self.costed_variant,
            "120.00",
            "100.00",
            "20.00",
        )

        response = self._get_dashboard()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Decimal(response.data["kpis"]["toplam_ciro"]), Decimal("100.00"))
        self.assertEqual(Decimal(response.data["debug"]["gross_sales_total"]), Decimal("120.00"))
        self.assertEqual(Decimal(response.data["debug"]["discount_total"]), Decimal("20.00"))

    def test_dashboard_date_filter_uses_last_modified_with_order_date_fallback(self):
        ist = ZoneInfo("Europe/Istanbul")
        outside_order_date = datetime(2026, 4, 10, 12, 0, tzinfo=ist)
        inside_operation_date = datetime(2026, 5, 5, 12, 0, tzinfo=ist)
        outside_operation_date = datetime(2026, 6, 1, 12, 0, tzinfo=ist)

        self._order(
            "LM-IN",
            Order.Status.DELIVERED,
            outside_order_date,
            self.costed_variant,
            "120.00",
            "100.00",
            "20.00",
            last_modified=inside_operation_date,
        )
        self._order(
            "LM-OUT",
            Order.Status.DELIVERED,
            datetime(2026, 5, 1, 12, 0, tzinfo=ist),
            self.costed_variant,
            "240.00",
            "200.00",
            "40.00",
            last_modified=outside_operation_date,
        )

        response = self._get_dashboard()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Decimal(response.data["kpis"]["toplam_ciro"]), Decimal("100.00"))
        self.assertEqual(
            response.data["debug"]["date_filter_field"],
            "last_modified_date_with_order_date_fallback",
        )
