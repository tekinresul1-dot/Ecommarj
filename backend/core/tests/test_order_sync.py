"""
Tests for the Trendyol order sync idempotent upsert logic.

Test scenarios:
1. Same package_id inserted twice → no duplicate, updated instead
2. Status change tracked (Created → Returned)
3. raw_payload_hash unchanged → skip (no DB write)
4. Compound key (org, package_id) enforces uniqueness
5. Order items upserted correctly by marketplace_line_id
"""
import json
from decimal import Decimal
from datetime import datetime, timezone as dt_tz
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.utils import timezone

from core.models import (
    Organization, MarketplaceAccount, Order, OrderItem,
    ProductVariant, Product, SyncAuditLog,
)
from core.services.trendyol_client import compute_payload_hash


class OrderSyncIdempotencyTests(TestCase):
    """Tests idempotent upsert behavior of TrendyolOrderSyncService."""

    def setUp(self):
        self.org = Organization.objects.create(name="Test Org")
        self.account = MarketplaceAccount.objects.create(
            organization=self.org,
            store_name="Test Store",
            seller_id="123456",
            api_key="testkey",
            api_secret="testsecret",
        )

    def _make_order_data(self, order_number="ORD001", package_id="PKG001", status="Created",
                          price=150.0, discount=0.0, line_id="LINE1", barcode="BC001"):
        return {
            "orderNumber": order_number,
            "shipmentPackageId": package_id,
            "orderDate": int(datetime(2026, 1, 15, 12, 0, 0, tzinfo=dt_tz.utc).timestamp() * 1000),
            "lastModifiedDate": int(datetime(2026, 1, 15, 13, 0, 0, tzinfo=dt_tz.utc).timestamp() * 1000),
            "status": status,
            "micro": False,
            "lines": [{
                "id": line_id,
                "barcode": barcode,
                "amount": price,
                "discount": discount,
                "quantity": 1,
                "merchantSku": "SKU001",
                "orderLineItemStatusName": status,
            }],
        }

    def test_no_duplicate_on_same_package_id(self):
        """Same shipmentPackageId inserted twice → 1 record, not 2."""
        order_data = self._make_order_data()

        with patch("core.services.order_sync.TrendyolApiClient") as MockClient:
            mock_client = MagicMock()
            mock_client.fetch_orders.return_value = [order_data, order_data]
            
            from core.services.order_sync import TrendyolOrderSyncService
            service = TrendyolOrderSyncService(self.account)
            service.client = mock_client
            audit = service.full_sync(days=30)

        self.assertEqual(Order.objects.filter(organization=self.org).count(), 1)
        self.assertEqual(audit.inserted + audit.updated + audit.skipped, 1)

    def test_status_change_tracked(self):
        """When status changes from Created to Returned, previous_status is recorded."""
        # Insert initial order
        Order.objects.create(
            organization=self.org,
            marketplace_account=self.account,
            marketplace_order_id="ORD001",
            package_id="PKG001",
            order_number="ORD001",
            order_date=timezone.now(),
            status=Order.Status.CREATED,
            raw_payload_hash="oldhash",
        )

        returned_data = self._make_order_data(status="Returned")

        with patch("core.services.order_sync.TrendyolApiClient"):
            from core.services.order_sync import TrendyolOrderSyncService
            service = TrendyolOrderSyncService(self.account)
            service.client = MagicMock()
            service.client.fetch_orders.return_value = [returned_data]
            audit = service.full_sync(days=30)

        order = Order.objects.get(organization=self.org, package_id="PKG001")
        self.assertEqual(order.status, Order.Status.RETURNED)
        self.assertEqual(order.previous_status, "Created")
        self.assertIsNotNone(order.status_changed_at)

    def test_skip_when_payload_unchanged(self):
        """If raw_payload_hash matches, no DB update (skipped)."""
        order_data = self._make_order_data()
        payload_hash = compute_payload_hash(order_data)

        Order.objects.create(
            organization=self.org,
            marketplace_account=self.account,
            marketplace_order_id="ORD001",
            package_id="PKG001",
            order_number="ORD001",
            order_date=timezone.now(),
            status=Order.Status.CREATED,
            raw_payload_hash=payload_hash,
        )

        with patch("core.services.order_sync.TrendyolApiClient"):
            from core.services.order_sync import TrendyolOrderSyncService
            service = TrendyolOrderSyncService(self.account)
            service.client = MagicMock()
            service.client.fetch_orders.return_value = [order_data]
            audit = service.full_sync(days=30)

        self.assertEqual(audit.skipped, 1)
        self.assertEqual(audit.updated, 0)
        self.assertEqual(audit.inserted, 0)

    def test_order_items_upserted_by_line_id(self):
        """OrderItems are upserted by (order, marketplace_line_id)."""
        order_data = self._make_order_data()

        with patch("core.services.order_sync.TrendyolApiClient"):
            from core.services.order_sync import TrendyolOrderSyncService
            service = TrendyolOrderSyncService(self.account)
            service.client = MagicMock()
            # Send same data twice to simulate re-fetch
            service.client.fetch_orders.return_value = [order_data]
            service.full_sync(days=30)
            
            # Reset counters and run again
            service.client.fetch_orders.return_value = [
                self._make_order_data(price=200.0)  # price changed
            ]
            service.full_sync(days=30)

        # Should still have exactly 1 order item
        order = Order.objects.get(organization=self.org, package_id="PKG001")
        self.assertEqual(order.items.count(), 1)
        item = order.items.first()
        self.assertEqual(item.sale_price_gross, Decimal("200.00"))


class PayloadHashTests(TestCase):
    """Test compute_payload_hash determinism."""

    def test_same_data_same_hash(self):
        data1 = {"a": 1, "b": "hello"}
        data2 = {"b": "hello", "a": 1}  # different key order
        self.assertEqual(compute_payload_hash(data1), compute_payload_hash(data2))

    def test_different_data_different_hash(self):
        data1 = {"a": 1}
        data2 = {"a": 2}
        self.assertNotEqual(compute_payload_hash(data1), compute_payload_hash(data2))
