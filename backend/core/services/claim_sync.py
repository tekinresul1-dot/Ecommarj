"""
TrendyolClaimSyncService — Syncs return/refund claims from Trendyol getClaims API.
Saves claim-level data to ReturnClaim and item-level data to ReturnClaimItem.
"""
import logging
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal

from django.utils import timezone

from core.models import (
    MarketplaceAccount, Order, ReturnClaim, ReturnClaimItem, SyncAuditLog,
)
from core.services.trendyol_client import TrendyolApiClient, compute_payload_hash
from core.services.checkpoint import SyncCheckpointService
from core.utils.encryption import decrypt_value

logger = logging.getLogger(__name__)

# Statuses that represent active cargo loss (shown in report)
ACTIVE_CLAIM_STATUSES = {"Accepted", "WaitingInAction", "Unresolved", "InProgress"}

# Cargo cost defaults per provider (TL)
CARGO_COSTS = {
    "yurtiçi": 135.32,
    "yurtici": 135.32,
    "aras": 96.00,
    "mng": 96.00,
}
DEFAULT_CARGO_COST = 135.32


def _cargo_cost_for(provider: str) -> float:
    key = (provider or "").lower().strip()
    for k, v in CARGO_COSTS.items():
        if k in key:
            return v
    return DEFAULT_CARGO_COST


class TrendyolClaimSyncService:
    """Syncs return/cancel claims from Trendyol."""

    def __init__(self, account: MarketplaceAccount):
        self.account = account
        self.organization = account.organization
        self.client = TrendyolApiClient(
            api_key=decrypt_value(account.api_key),
            api_secret=decrypt_value(account.api_secret),
            seller_id=account.seller_id,
        )
        self._inserted = 0
        self._updated = 0
        self._skipped = 0
        self._failed = 0

    def sync_claims(self, days_back: int = 30) -> SyncAuditLog:
        """Fetch and upsert claims from the last N days."""
        self._inserted = 0
        self._updated = 0
        self._skipped = 0
        self._failed = 0

        started_at = timezone.now()
        now = datetime.now(dt_timezone.utc)
        start_date = now - timedelta(days=days_back)

        audit = SyncAuditLog.objects.create(
            marketplace_account=self.account,
            sync_type="claims",
            sync_mode=SyncAuditLog.SyncMode.INCREMENTAL,
            started_at=started_at,
            date_range_start=start_date,
            date_range_end=now,
        )

        try:
            claims_data = self.client.fetch_claims(
                start_date=start_date,
                end_date=now,
            )

            for claim_data in claims_data:
                try:
                    self._upsert_claim(claim_data)
                except Exception as e:
                    self._failed += 1
                    logger.error(f"[ClaimSync] Failed to upsert claim: {e}", exc_info=True)

            SyncCheckpointService.update_checkpoint(self.account, "claims")

            finished_at = timezone.now()
            audit.finished_at = finished_at
            audit.total_fetched = len(claims_data)
            audit.inserted = self._inserted
            audit.updated = self._updated
            audit.skipped = self._skipped
            audit.failed = self._failed
            audit.success = True
            audit.duration_seconds = (finished_at - started_at).total_seconds()
            audit.save()

            logger.info(
                f"[ClaimSync] Complete — fetched={len(claims_data)} "
                f"inserted={self._inserted} updated={self._updated} "
                f"skipped={self._skipped} failed={self._failed}"
            )
            return audit

        except Exception as e:
            finished_at = timezone.now()
            audit.finished_at = finished_at
            audit.success = False
            audit.error_message = str(e)
            audit.duration_seconds = (finished_at - started_at).total_seconds()
            audit.save()
            logger.error(f"[ClaimSync] FAILED: {e}", exc_info=True)
            raise

    def _parse_ts(self, ts) -> datetime | None:
        """Convert millisecond timestamp to UTC datetime."""
        if not ts:
            return None
        try:
            return datetime.fromtimestamp(int(ts) / 1000.0, tz=dt_timezone.utc)
        except Exception:
            return None

    def _upsert_claim(self, claim_data: dict):
        """Upsert a single claim + its items."""
        claim_id = str(claim_data.get("id", ""))
        if not claim_id:
            self._failed += 1
            return

        payload_hash = compute_payload_hash(claim_data)

        claim_date = self._parse_ts(
            claim_data.get("claimDate") or claim_data.get("createdDate")
        )
        order_date = self._parse_ts(
            claim_data.get("orderDate") or claim_data.get("orderCreatedDate")
        )
        last_modified_date = self._parse_ts(
            claim_data.get("lastModifiedDate") or claim_data.get("updatedDate")
        )

        order_number = str(claim_data.get("orderNumber", ""))
        order = None
        if order_number:
            order = Order.objects.filter(
                organization=self.organization,
                order_number=order_number,
            ).first()

        # Derive claim status from item statuses
        item_statuses = set()
        for item in claim_data.get("items", []):
            for ci in item.get("claimItems", []):
                s = (ci.get("claimItemStatus") or {}).get("name", "")
                if s:
                    item_statuses.add(s)

        if "Accepted" in item_statuses:
            raw_status = "Accepted"
        elif "WaitingInAction" in item_statuses:
            raw_status = "WaitingInAction"
        elif "Unresolved" in item_statuses:
            raw_status = "Unresolved"
        elif "Rejected" in item_statuses or "Cancelled" in item_statuses:
            raw_status = "Rejected"
        else:
            raw_status = claim_data.get("claimStatus") or claim_data.get("status", "Created")

        # Cargo provider
        cargo_provider = (
            claim_data.get("cargoProviderName") or
            claim_data.get("cargoCompany") or
            claim_data.get("shipmentInfo", {}).get("cargoProviderName", "") or ""
        )

        refund_amount = Decimal(str(claim_data.get("refundAmount", "0") or "0"))
        cargo_cost_val = Decimal(str(_cargo_cost_for(cargo_provider)))

        # Reason from first item's claimItem
        reason = claim_data.get("reason", "") or claim_data.get("claimReason", "")
        if not reason:
            for item in claim_data.get("items", []):
                for ci in item.get("claimItems", []):
                    r = ci.get("customerClaimItemReason") or {}
                    reason = r.get("name", "")
                    if reason:
                        break
                if reason:
                    break

        claim_obj, created = ReturnClaim.objects.update_or_create(
            organization=self.organization,
            claim_id=claim_id,
            defaults={
                "marketplace_account": self.account,
                "order": order,
                "order_number": order_number,
                "claim_date": claim_date,
                "order_date": order_date,
                "last_modified_date": last_modified_date,
                "claim_status": raw_status,
                "reason": reason,
                "cargo_provider": cargo_provider,
                "refund_amount": refund_amount,
                "cargo_cost": cargo_cost_val,
                "raw_payload_hash": payload_hash,
                "last_synced_at": timezone.now(),
            },
        )

        if created:
            self._inserted += 1
        else:
            self._updated += 1

        # Sync items
        self._sync_items(claim_obj, claim_data, cargo_cost_val)

    def _sync_items(self, claim_obj: ReturnClaim, claim_data: dict, cargo_cost_val: Decimal):
        """Upsert ReturnClaimItem records for this claim."""
        # Delete old items and recreate (claim items don't have stable IDs in API)
        claim_obj.claim_items.all().delete()

        items = claim_data.get("items", [])
        for item in items:
            order_line = item.get("orderLine") or item.get("product") or {}
            product_name = (
                order_line.get("productName") or
                order_line.get("name") or
                item.get("productName") or ""
            )
            barcode = (
                order_line.get("barcode") or
                item.get("barcode") or ""
            )
            merchant_sku = (
                order_line.get("merchantSku") or
                item.get("merchantSku") or ""
            )
            price = Decimal(str(order_line.get("price") or item.get("price") or "0"))
            quantity = int(item.get("quantity") or order_line.get("quantity") or 1)

            for ci in item.get("claimItems", []):
                status_name = (ci.get("claimItemStatus") or {}).get("name", "")
                reason_obj = ci.get("customerClaimItemReason") or {}
                customer_reason = reason_obj.get("name", "")

                ReturnClaimItem.objects.create(
                    claim=claim_obj,
                    product_name=product_name,
                    barcode=barcode,
                    merchant_sku=merchant_sku,
                    price=price,
                    quantity=quantity,
                    claim_item_status=status_name,
                    customer_reason=customer_reason,
                    outgoing_cargo_cost=cargo_cost_val,
                    incoming_cargo_cost=cargo_cost_val,
                )

            # If no claimItems array, create one row from item-level data
            if not item.get("claimItems"):
                ReturnClaimItem.objects.create(
                    claim=claim_obj,
                    product_name=product_name,
                    barcode=barcode,
                    merchant_sku=merchant_sku,
                    price=price,
                    quantity=quantity,
                    claim_item_status="",
                    customer_reason="",
                    outgoing_cargo_cost=cargo_cost_val,
                    incoming_cargo_cost=cargo_cost_val,
                )
