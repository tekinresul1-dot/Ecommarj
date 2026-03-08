"""
SyncCheckpointService — Manages sync checkpoints for incremental sync.
"""
import logging
from datetime import timedelta
from django.utils import timezone

from core.models import MarketplaceAccount, SyncCheckpoint

logger = logging.getLogger(__name__)

# Overlap window: go back this much from checkpoint to catch late updates
OVERLAP_HOURS = 2


class SyncCheckpointService:
    """Manages sync checkpoints for incremental sync."""

    @staticmethod
    def get_last_checkpoint(account: MarketplaceAccount, sync_type: str):
        """
        Get the last successful sync timestamp.
        Returns datetime or None if no checkpoint exists.
        """
        try:
            cp = SyncCheckpoint.objects.get(
                marketplace_account=account,
                sync_type=sync_type,
            )
            return cp.last_successful_sync_at
        except SyncCheckpoint.DoesNotExist:
            return None

    @staticmethod
    def get_safe_start_time(account: MarketplaceAccount, sync_type: str):
        """
        Get the start time for incremental sync with overlap.
        Goes back OVERLAP_HOURS from the checkpoint to catch late-processed orders.
        Returns None if no checkpoint (means full sync needed).
        """
        last = SyncCheckpointService.get_last_checkpoint(account, sync_type)
        if last is None:
            return None
        return last - timedelta(hours=OVERLAP_HOURS)

    @staticmethod
    def update_checkpoint(
        account: MarketplaceAccount,
        sync_type: str,
        timestamp=None,
        last_modified_date=None,
    ):
        """Update checkpoint after a successful sync."""
        now = timestamp or timezone.now()
        cp, created = SyncCheckpoint.objects.update_or_create(
            marketplace_account=account,
            sync_type=sync_type,
            defaults={
                "last_successful_sync_at": now,
                "last_fetched_modified_date": last_modified_date,
            },
        )
        action = "Created" if created else "Updated"
        logger.info(f"[Checkpoint] {action} {sync_type} checkpoint for {account}: {now}")
        return cp
