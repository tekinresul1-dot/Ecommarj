"""
TrendyolReconciliationService — Periodic reconciliation to guarantee data consistency.

Runs on multiple time windows (1 day, 3 days, 7 days) to catch:
- Missed webhook events
- Late-processed orders
- Status changes that happened after initial sync
"""
import logging
from datetime import datetime, timedelta, timezone as dt_timezone

from core.models import MarketplaceAccount, SyncAuditLog
from core.services.order_sync import TrendyolOrderSyncService
from core.services.claim_sync import TrendyolClaimSyncService

logger = logging.getLogger(__name__)


class TrendyolReconciliationService:
    """Periodic reconciliation across multiple time windows."""

    def __init__(self, account: MarketplaceAccount):
        self.account = account

    def reconcile(self, windows_days: list = None) -> list:
        """
        Run reconciliation for multiple time windows.
        Default windows: [1, 3, 7] days back.
        Returns list of SyncAuditLog entries.
        """
        if windows_days is None:
            windows_days = [1, 3, 7]

        results = []
        now = datetime.now(dt_timezone.utc)

        order_sync = TrendyolOrderSyncService(self.account)
        claim_sync = TrendyolClaimSyncService(self.account)

        for days in windows_days:
            start_date = now - timedelta(days=days)
            logger.info(f"[Reconciliation] Running {days}-day window: {start_date.date()} → {now.date()}")

            try:
                # Reconcile orders
                audit = order_sync._run_sync(
                    start_date=start_date,
                    end_date=now,
                    sync_mode=SyncAuditLog.SyncMode.RECONCILIATION,
                )
                results.append(audit)
            except Exception as e:
                logger.error(f"[Reconciliation] Order sync failed for {days}-day window: {e}")

        # Also reconcile claims
        try:
            claim_audit = claim_sync.sync_claims(days_back=max(windows_days))
            results.append(claim_audit)
        except Exception as e:
            logger.error(f"[Reconciliation] Claim sync failed: {e}")

        logger.info(f"[Reconciliation] Complete — {len(results)} sync runs")
        return results
