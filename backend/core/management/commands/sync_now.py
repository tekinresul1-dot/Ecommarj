"""
Management command to immediately sync all available Trendyol orders.
Uses the new TrendyolOrderSyncService with 3-day windows.
"""
import logging
from django.core.management.base import BaseCommand
from core.models import MarketplaceAccount

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Immediately sync all available Trendyol orders from the API"

    def add_arguments(self, parser):
        parser.add_argument(
            "--account-id",
            type=int,
            help="Specific MarketplaceAccount ID to sync (default: all active)",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Number of days to look back (default: 30 — Trendyol API limit)",
        )
        parser.add_argument(
            "--mode",
            choices=["full", "incremental"],
            default="full",
            help="Sync mode (default: full)",
        )

    def handle(self, *args, **options):
        from core.services.order_sync import TrendyolOrderSyncService

        account_id = options.get("account_id")
        days = options["days"]
        mode = options["mode"]

        if account_id:
            accounts = MarketplaceAccount.objects.filter(id=account_id, is_active=True)
        else:
            accounts = MarketplaceAccount.objects.filter(is_active=True, channel="trendyol")

        if not accounts.exists():
            self.stdout.write(self.style.ERROR("No active Trendyol accounts found."))
            return

        for acct in accounts:
            self.stdout.write(f"\nSyncing account: {acct.store_name} (ID={acct.id}, org={acct.organization_id})")
            
            try:
                service = TrendyolOrderSyncService(acct)
                
                if mode == "full":
                    audit = service.full_sync(days=days)
                else:
                    audit = service.incremental_sync()

                self.stdout.write(self.style.SUCCESS(
                    f"  ✓ {mode} sync done — "
                    f"fetched={audit.total_fetched} "
                    f"inserted={audit.inserted} "
                    f"updated={audit.updated} "
                    f"skipped={audit.skipped} "
                    f"failed={audit.failed} "
                    f"duration={audit.duration_seconds:.1f}s"
                ))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ✗ Sync failed: {e}"))
                logger.error(f"sync_now failed for account {acct.id}: {e}", exc_info=True)
