"""
TrendyolClaimSyncService — Syncs return/refund claims from Trendyol getClaims API.
"""
import logging
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal

from django.utils import timezone

from core.models import (
    MarketplaceAccount, Order, ReturnClaim, SyncAuditLog,
)
from core.services.trendyol_client import TrendyolApiClient, compute_payload_hash
from core.services.checkpoint import SyncCheckpointService
from core.utils.encryption import decrypt_value

logger = logging.getLogger(__name__)


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

            # Update checkpoint
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

    def _upsert_claim(self, claim_data: dict):
        """Upsert a single claim record."""
        claim_id = str(claim_data.get("id", ""))
        if not claim_id:
            self._failed += 1
            return

        payload_hash = compute_payload_hash(claim_data)

        # Parse dates
        claim_date = None
        claim_date_ts = claim_data.get("claimDate") or claim_data.get("createdDate", 0)
        if claim_date_ts:
            claim_date = datetime.fromtimestamp(claim_date_ts / 1000.0, tz=dt_timezone.utc)

        # Find matching order
        order_number = str(claim_data.get("orderNumber", ""))
        order = None
        if order_number:
            order = Order.objects.filter(
                organization=self.organization,
                order_number=order_number,
            ).first()

        # Status — parse from items[].claimItems[].claimItemStatus.name
        item_statuses = set()
        for item in claim_data.get("items", []):
            for ci in item.get("claimItems", []):
                s = ci.get("claimItemStatus", {}).get("name", "")
                if s:
                    item_statuses.add(s)
        if "Accepted" in item_statuses:
            raw_status = "InProgress"
        elif "Rejected" in item_statuses or "Cancelled" in item_statuses:
            raw_status = "Rejected"
        else:
            raw_status = claim_data.get("claimStatus") or claim_data.get("status", "Created")

        # Amount
        refund_amount = Decimal(str(claim_data.get("refundAmount", "0")))
        cargo_cost = Decimal(str(claim_data.get("cargoCost", "0")))

        # Reason — from first claimItem
        reason = claim_data.get("reason", "") or claim_data.get("claimReason", "")
        if not reason:
            for item in claim_data.get("items", []):
                for ci in item.get("claimItems", []):
                    r = ci.get("customerClaimItemReason", {}) or {}
                    reason = r.get("name", "")
                    if reason:
                        break
                if reason:
                    break

        try:
            existing = ReturnClaim.objects.get(
                organization=self.organization,
                claim_id=claim_id,
            )

            if existing.raw_payload_hash == payload_hash:
                self._skipped += 1
                return

            existing.order = order
            existing.order_number = order_number
            existing.claim_date = claim_date
            existing.claim_status = raw_status
            existing.reason = reason
            existing.refund_amount = refund_amount
            existing.cargo_cost = cargo_cost
            existing.raw_payload_hash = payload_hash
            existing.last_synced_at = timezone.now()
            existing.save()

            # Update related order status if claim resolves to Returned
            if order and raw_status in ("Resolved",):
                if order.status != Order.Status.RETURNED:
                    order.previous_status = order.status
                    order.status = Order.Status.RETURNED
                    order.status_changed_at = timezone.now()
                    order.save(update_fields=["status", "previous_status", "status_changed_at"])

            self._updated += 1

        except ReturnClaim.DoesNotExist:
            ReturnClaim.objects.create(
                organization=self.organization,
                marketplace_account=self.account,
                claim_id=claim_id,
                order=order,
                order_number=order_number,
                claim_date=claim_date,
                claim_status=raw_status,
                reason=reason,
                refund_amount=refund_amount,
                cargo_cost=cargo_cost,
                raw_payload_hash=payload_hash,
                last_synced_at=timezone.now(),
            )
            self._inserted += 1
