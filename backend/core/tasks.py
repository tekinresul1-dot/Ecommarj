"""
Celery tasks for Trendyol sync operations.

Tasks:
- trendyol_incremental_sync — every 15 min (Celery Beat)
- trendyol_full_sync — manual trigger
- trendyol_backfill_sync — date range trigger
- trendyol_claims_sync — every 30 min
- trendyol_reconciliation — every 6 hours
- sync_all_trendyol_data_task — legacy support (products + orders + settlements)
"""
import logging
from datetime import datetime, timezone as dt_timezone
from celery import shared_task

from core.models import MarketplaceAccount

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def trendyol_incremental_sync(self, account_id: int):
    """Incremental order sync — runs every 15 minutes via Celery Beat."""
    try:
        account = MarketplaceAccount.objects.get(id=account_id, is_active=True)
        from core.services.order_sync import TrendyolOrderSyncService
        service = TrendyolOrderSyncService(account)
        audit = service.incremental_sync()
        return f"OK: {audit.total_fetched} fetched, {audit.inserted} new, {audit.updated} updated"
    except MarketplaceAccount.DoesNotExist:
        logger.error(f"Account {account_id} not found")
        return "Error: Account not found"
    except Exception as e:
        logger.error(f"Incremental sync failed for {account_id}: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=1, default_retry_delay=120)
def trendyol_full_sync(self, account_id: int, days: int = 365):
    """Full order sync — manual trigger."""
    try:
        account = MarketplaceAccount.objects.get(id=account_id, is_active=True)
        from core.services.order_sync import TrendyolOrderSyncService
        service = TrendyolOrderSyncService(account)
        audit = service.full_sync(days=days)
        return f"OK: {audit.total_fetched} fetched, {audit.inserted} new, {audit.updated} updated"
    except MarketplaceAccount.DoesNotExist:
        logger.error(f"Account {account_id} not found")
        return "Error: Account not found"
    except Exception as e:
        logger.error(f"Full sync failed for {account_id}: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=1)
def trendyol_backfill_sync(self, account_id: int, start_date_iso: str, end_date_iso: str):
    """Backfill sync for a specific date range."""
    try:
        account = MarketplaceAccount.objects.get(id=account_id, is_active=True)
        start_date = datetime.fromisoformat(start_date_iso).replace(tzinfo=dt_timezone.utc)
        end_date = datetime.fromisoformat(end_date_iso).replace(tzinfo=dt_timezone.utc)
        
        from core.services.order_sync import TrendyolOrderSyncService
        service = TrendyolOrderSyncService(account)
        audit = service.backfill_sync(start_date=start_date, end_date=end_date)
        return f"OK: {audit.total_fetched} fetched, {audit.inserted} new, {audit.updated} updated"
    except MarketplaceAccount.DoesNotExist:
        return "Error: Account not found"
    except Exception as e:
        logger.error(f"Backfill sync failed for {account_id}: {e}")
        raise


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def trendyol_claims_sync(self, account_id: int, days_back: int = 30):
    """Claims/returns sync — runs every 30 minutes."""
    try:
        account = MarketplaceAccount.objects.get(id=account_id, is_active=True)
        from core.services.claim_sync import TrendyolClaimSyncService
        service = TrendyolClaimSyncService(account)
        audit = service.sync_claims(days_back=days_back)
        return f"OK: {audit.total_fetched} fetched, {audit.inserted} new, {audit.updated} updated"
    except MarketplaceAccount.DoesNotExist:
        return "Error: Account not found"
    except Exception as e:
        logger.error(f"Claims sync failed for {account_id}: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=1)
def trendyol_reconciliation(self, account_id: int):
    """Reconciliation — re-syncs 1/3/7 day windows. Runs every 6 hours."""
    try:
        account = MarketplaceAccount.objects.get(id=account_id, is_active=True)
        from core.services.reconciliation import TrendyolReconciliationService
        service = TrendyolReconciliationService(account)
        results = service.reconcile()
        return f"OK: {len(results)} sync runs completed"
    except MarketplaceAccount.DoesNotExist:
        return "Error: Account not found"
    except Exception as e:
        logger.error(f"Reconciliation failed for {account_id}: {e}")
        raise


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def trendyol_cargo_sync(self, account_id: int):
    """Cargo invoice sync — runs periodically via Celery Beat."""
    try:
        account = MarketplaceAccount.objects.get(id=account_id, is_active=True)
        from core.services.sync_service import TrendyolSyncService
        service = TrendyolSyncService(account)
        service.sync_cargo_invoices()
        return f"OK: Cargo invoices synced for account {account_id}"
    except MarketplaceAccount.DoesNotExist:
        return "Error: Account not found"
    except Exception as e:
        logger.error(f"Cargo sync failed for {account_id}: {e}")
        raise self.retry(exc=e)


# ---------------------------------------------------------------------------
# Celery Beat — Tüm aktif hesapları tarayıp per-account görevleri ateşler
# ---------------------------------------------------------------------------

@shared_task
def trendyol_incremental_sync_all_accounts():
    """Tüm aktif Trendyol hesapları için artımlı sipariş senkronizasyonu başlatır."""
    from core.models import MarketplaceAccount
    accounts = MarketplaceAccount.objects.filter(is_active=True, channel="trendyol")
    dispatched = 0
    for account in accounts:
        trendyol_incremental_sync.delay(account.id)
        dispatched += 1
    logger.info(f"[Beat] Incremental sync dispatched for {dispatched} accounts")
    return f"Dispatched {dispatched} incremental syncs"


@shared_task
def trendyol_claims_sync_all_accounts():
    """Tüm aktif Trendyol hesapları için iade/talep senkronizasyonu başlatır."""
    from core.models import MarketplaceAccount
    accounts = MarketplaceAccount.objects.filter(is_active=True, channel="trendyol")
    dispatched = 0
    for account in accounts:
        trendyol_claims_sync.delay(account.id)
        dispatched += 1
    logger.info(f"[Beat] Claims sync dispatched for {dispatched} accounts")
    return f"Dispatched {dispatched} claims syncs"


@shared_task
def trendyol_reconciliation_all_accounts():
    """Tüm aktif Trendyol hesapları için uzlaştırma başlatır."""
    from core.models import MarketplaceAccount
    accounts = MarketplaceAccount.objects.filter(is_active=True, channel="trendyol")
    dispatched = 0
    for account in accounts:
        trendyol_reconciliation.delay(account.id)
        dispatched += 1
    logger.info(f"[Beat] Reconciliation dispatched for {dispatched} accounts")
    return f"Dispatched {dispatched} reconciliation tasks"


@shared_task
def trendyol_product_sync_all_accounts():
    """
    Tüm aktif Trendyol hesapları için ürün senkronizasyonu başlatır.
    Günde bir kez çalışır — ürün fiyat/stok/komisyon değişikliklerini yakalar.
    """
    from core.models import MarketplaceAccount
    from core.tasks import sync_all_trendyol_data_task
    accounts = MarketplaceAccount.objects.filter(is_active=True, channel="trendyol")
    dispatched = 0
    for account in accounts:
        sync_all_trendyol_data_task.delay(str(account.id))
        dispatched += 1
    logger.info(f"[Beat] Product sync dispatched for {dispatched} accounts")
    return f"Dispatched {dispatched} product syncs"


# Legacy task - still used by existing sync trigger views
@shared_task
def sync_all_trendyol_data_task(account_id: str):
    """
    Legacy: Sync products + orders + settlements.
    Now uses the new sync services for orders.
    """
    try:
        account = MarketplaceAccount.objects.get(id=account_id)
        
        # Products — still use old sync service for now
        from core.services.sync_service import TrendyolSyncService
        legacy_service = TrendyolSyncService(account=account)
        legacy_service.sync_products()
        
        # Orders — use new service
        from core.services.order_sync import TrendyolOrderSyncService
        order_service = TrendyolOrderSyncService(account)
        audit = order_service.incremental_sync()
        
        # Settlements — still use old sync service
        legacy_service.sync_settlements()
        
        # Cargo Invoices — New addition
        legacy_service.sync_cargo_invoices()
        
        account.last_sync_at = __import__('django.utils', fromlist=['timezone']).timezone.now()
        account.save(update_fields=["last_sync_at"])
        
        return f"Success: Sync completed for {account.store_name}"
    except MarketplaceAccount.DoesNotExist:
        logger.error(f"Account {account_id} not found for sync.")
        return "Error: Account not found"
    except Exception as e:
        logger.error(f"Sync failed for account {account_id}: {e}")
        raise ValueError(str(e))
