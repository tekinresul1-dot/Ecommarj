"""
TrendyolOrderSyncService — Idempotent order sync with full/incremental/backfill modes.

Key design decisions:
- Compound upsert key: (organization, package_id)
- raw_payload_hash for change detection — skip update if nothing changed
- Status history tracking (previous_status, status_changed_at)
- Audit logging with counters (inserted, updated, skipped, failed)
- 3-day chunks to avoid Trendyol API data loss on large ranges
"""
import logging
import time
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from typing import Dict, Any

from django.utils import timezone
from django.db import transaction

from core.models import (
    Organization, MarketplaceAccount, Order, OrderItem,
    ProductVariant, SyncAuditLog, FinancialTransactionType,
)
from core.services.trendyol_client import TrendyolApiClient, compute_payload_hash
from core.services.checkpoint import SyncCheckpointService
from core.utils.encryption import decrypt_value

logger = logging.getLogger(__name__)

# Trendyol status -> EcomMarj status mapping
STATUS_MAP = {
    "Created": Order.Status.CREATED,
    "Picking": Order.Status.PICKING,
    "Shipped": Order.Status.SHIPPED,
    "Delivered": Order.Status.DELIVERED,
    "Cancelled": Order.Status.CANCELLED,
    "Returned": Order.Status.RETURNED,
    "UnDelivered": Order.Status.UNDELIVERED,
    "UnSupplied": Order.Status.UNSUPPLIED,
}

# Default total_days for full sync
FULL_SYNC_DAYS = 365


class TrendyolOrderSyncService:
    """Handles all order sync operations: full, incremental, backfill."""

    def __init__(self, account: MarketplaceAccount):
        self.account = account
        self.organization = account.organization
        self.client = TrendyolApiClient(
            api_key=decrypt_value(account.api_key),
            api_secret=decrypt_value(account.api_secret),
            seller_id=account.seller_id,
        )
        # Counters
        self._inserted = 0
        self._updated = 0
        self._skipped = 0
        self._failed = 0

    def _reset_counters(self):
        self._inserted = 0
        self._updated = 0
        self._skipped = 0
        self._failed = 0

    # ------------------------------------------------------------------
    # PUBLIC: Full Sync
    # ------------------------------------------------------------------
    def full_sync(self, days: int = FULL_SYNC_DAYS) -> SyncAuditLog:
        """
        Full sync: fetch ALL orders from the last N days.
        Chunks into 3-day windows. Idempotent upsert.
        """
        now = datetime.now(dt_timezone.utc)
        start_date = now - timedelta(days=days)
        return self._run_sync(
            start_date=start_date,
            end_date=now,
            sync_mode=SyncAuditLog.SyncMode.FULL,
        )

    # ------------------------------------------------------------------
    # PUBLIC: Incremental Sync
    # ------------------------------------------------------------------
    def incremental_sync(self) -> SyncAuditLog:
        """
        Incremental sync: fetch orders modified since last checkpoint.
        Uses 2-hour overlap to catch late-processed orders.
        Falls back to full sync if no checkpoint exists.
        """
        safe_start = SyncCheckpointService.get_safe_start_time(
            self.account, "orders"
        )
        if safe_start is None:
            logger.info("[OrderSync] No checkpoint found — falling back to full sync")
            return self.full_sync()

        now = datetime.now(dt_timezone.utc)
        return self._run_sync(
            start_date=safe_start,
            end_date=now,
            sync_mode=SyncAuditLog.SyncMode.INCREMENTAL,
        )

    # ------------------------------------------------------------------
    # PUBLIC: Backfill Sync
    # ------------------------------------------------------------------
    def backfill_sync(self, start_date: datetime, end_date: datetime) -> SyncAuditLog:
        """
        Backfill: fetch orders for a specific date range.
        Used when dashboard detects missing data for a period.
        """
        return self._run_sync(
            start_date=start_date,
            end_date=end_date,
            sync_mode=SyncAuditLog.SyncMode.BACKFILL,
        )

    # ------------------------------------------------------------------
    # CORE: Run sync
    # ------------------------------------------------------------------
    def _run_sync(
        self,
        start_date: datetime,
        end_date: datetime,
        sync_mode: str,
    ) -> SyncAuditLog:
        """Core sync runner — fetches, upserts, logs."""
        self._reset_counters()
        started_at = timezone.now()

        audit = SyncAuditLog.objects.create(
            marketplace_account=self.account,
            sync_type="orders",
            sync_mode=sync_mode,
            started_at=started_at,
            date_range_start=start_date,
            date_range_end=end_date,
        )

        try:
            # Fetch from Trendyol
            orders_data = self.client.fetch_orders(
                start_date=start_date,
                end_date=end_date,
            )

            # Deduplicate by shipmentPackageId (API may return same package from overlapping chunks)
            seen = {}
            for o_data in orders_data:
                pkg_id = str(o_data.get("shipmentPackageId") or o_data.get("id") or "")
                if pkg_id:
                    seen[pkg_id] = o_data  # last wins — latest data
            unique_orders = list(seen.values())

            logger.info(
                f"[OrderSync] {sync_mode} — {len(orders_data)} raw → "
                f"{len(unique_orders)} unique packages"
            )

            # Upsert each package
            for o_data in unique_orders:
                try:
                    self._upsert_order_package(o_data)
                except Exception as e:
                    self._failed += 1
                    logger.error(f"[OrderSync] Failed to upsert package: {e}", exc_info=True)

            # Update checkpoint
            SyncCheckpointService.update_checkpoint(self.account, "orders")

            # Update account last_sync_at
            self.account.last_sync_at = timezone.now()
            self.account.save(update_fields=["last_sync_at"])

            # Finalize audit log
            finished_at = timezone.now()
            audit.finished_at = finished_at
            audit.total_fetched = len(unique_orders)
            audit.inserted = self._inserted
            audit.updated = self._updated
            audit.skipped = self._skipped
            audit.failed = self._failed
            audit.success = True
            audit.duration_seconds = (finished_at - started_at).total_seconds()
            audit.save()

            logger.info(
                f"[OrderSync] {sync_mode} complete — "
                f"fetched={len(unique_orders)} inserted={self._inserted} "
                f"updated={self._updated} skipped={self._skipped} "
                f"failed={self._failed} duration={audit.duration_seconds:.1f}s"
            )
            return audit

        except Exception as e:
            finished_at = timezone.now()
            audit.finished_at = finished_at
            audit.success = False
            audit.error_message = str(e)
            audit.duration_seconds = (finished_at - started_at).total_seconds()
            audit.total_fetched = 0
            audit.save()
            logger.error(f"[OrderSync] {sync_mode} FAILED: {e}", exc_info=True)
            raise

    # ------------------------------------------------------------------
    # CORE: Idempotent upsert
    # ------------------------------------------------------------------
    @transaction.atomic
    def _upsert_order_package(self, o_data: Dict[str, Any]):
        """
        Idempotent upsert of a single shipment package.
        
        Key: (organization, package_id)
        Change detection: raw_payload_hash
        Status history: previous_status, status_changed_at
        """
        order_number = str(o_data.get("orderNumber", ""))
        package_id = str(o_data.get("shipmentPackageId") or o_data.get("id") or order_number)
        
        if not order_number and not package_id:
            self._failed += 1
            return

        # Compute hash for change detection
        payload_hash = compute_payload_hash(o_data)

        # Parse dates
        order_date_ts = o_data.get("orderDate", 0)
        order_date = datetime.fromtimestamp(order_date_ts / 1000.0, tz=dt_timezone.utc)

        last_modified_ts = o_data.get("lastModifiedDate") or o_data.get("packageLastModifiedDate", 0)
        last_modified_date = None
        if last_modified_ts:
            last_modified_date = datetime.fromtimestamp(last_modified_ts / 1000.0, tz=dt_timezone.utc)

        # Status mapping
        raw_status = o_data.get("status", "Created")
        mapped_status = STATUS_MAP.get(raw_status, Order.Status.CREATED)

        # Micro export
        is_micro = o_data.get("micro", False)
        
        # Country code
        country_code = "TR"
        ship_addr = o_data.get("shipmentAddress") or {}
        if ship_addr.get("countryCode"):
            country_code = ship_addr["countryCode"]
        elif is_micro:
            country_code = ship_addr.get("countryCode", "XX")

        # Cargo info (fallback to root if not in cargoDetail)
        cargo_provider = o_data.get("cargoProviderName", "")
        cargo_tracking = o_data.get("cargoTrackingNumber", "")
        
        cargo_detail = o_data.get("cargoDetail") or {}
        if cargo_detail:
            if cargo_detail.get("cargoProviderName"):
                cargo_provider = cargo_detail.get("cargoProviderName")
            if cargo_detail.get("trackingNumber"):
                cargo_tracking = cargo_detail.get("trackingNumber")

        # Check if order already exists
        try:
            existing = Order.objects.get(
                organization=self.organization,
                package_id=package_id,
            )
            
            # Change detection — skip if hash is identical
            if existing.raw_payload_hash == payload_hash:
                self._skipped += 1
                return

            # Track status change
            if existing.status != mapped_status:
                existing.previous_status = existing.status
                existing.status_changed_at = timezone.now()

            # Update
            existing.marketplace_order_id = order_number
            existing.order_number = order_number
            existing.marketplace_account = self.account
            existing.order_date = order_date
            existing.last_modified_date = last_modified_date
            existing.status = mapped_status
            existing.channel = Order.Channel.MICRO_EXPORT if is_micro else Order.Channel.TRENDYOL
            existing.country_code = country_code
            existing.cargo_provider_name = cargo_provider
            existing.cargo_tracking_number = cargo_tracking
            existing.raw_payload_hash = payload_hash
            existing.last_synced_at = timezone.now()
            existing.save()

            self._updated += 1

        except Order.DoesNotExist:
            # Insert new order
            existing = Order.objects.create(
                organization=self.organization,
                marketplace_account=self.account,
                marketplace_order_id=order_number,
                package_id=package_id,
                order_number=order_number,
                order_date=order_date,
                last_modified_date=last_modified_date,
                status=mapped_status,
                channel=Order.Channel.MICRO_EXPORT if is_micro else Order.Channel.TRENDYOL,
                country_code=country_code,
                cargo_provider_name=cargo_provider,
                cargo_tracking_number=cargo_tracking,
                raw_payload_hash=payload_hash,
                last_synced_at=timezone.now(),
            )
            self._inserted += 1

        # Upsert order items (lines)
        self._upsert_order_lines(existing, o_data)

    def _upsert_order_lines(self, order: Order, o_data: Dict[str, Any]):
        """Upsert order line items."""
        raw_status = o_data.get("status", "Created")
        
        for line in o_data.get("lines", []):
            barcode = line.get("barcode", "")
            line_id = str(line.get("id", ""))
            
            if not line_id:
                continue

            # Find matching variant by barcode
            variant = None
            if barcode:
                variant = ProductVariant.objects.filter(
                    product__organization=self.organization,
                    barcode=barcode,
                ).select_related("product").first()

            price = Decimal(str(line.get("amount", line.get("price", "0"))))
            discount = Decimal(str(line.get("discount", "0")))
            quantity = int(line.get("quantity", 1))
            
            commission_rate_raw = line.get("commission")
            vat_rate_raw = line.get("vatRate")
            
            item_status = line.get("orderLineItemStatusName", raw_status)

            defaults = {
                "product_variant": variant,
                "sku": line.get("merchantSku", barcode),
                "quantity": quantity,
                "sale_price_gross": price,
                "sale_price_net": price - discount,
                "discount": discount,
                "status": item_status,
            }
            if commission_rate_raw is not None:
                defaults["applied_commission_rate"] = Decimal(str(commission_rate_raw))
            if vat_rate_raw is not None:
                defaults["applied_vat_rate"] = Decimal(str(vat_rate_raw))

            OrderItem.objects.update_or_create(
                order=order,
                marketplace_line_id=line_id,
                defaults=defaults,
            )

            # Update product commission rate (fallback data)
            if variant and variant.product and commission_rate_raw is not None:
                variant.product.commission_rate = Decimal(str(commission_rate_raw))
                variant.product.save(update_fields=["commission_rate"])
