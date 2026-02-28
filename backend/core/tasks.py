import logging
from celery import shared_task
from core.models import MarketplaceAccount
from core.services.sync_service import TrendyolSyncService

logger = logging.getLogger(__name__)

@shared_task
def sync_all_trendyol_data_task(account_id: str):
    """
    Belirtilen MarketplaceAccount (Trendyol) için arka planda senkronizasyon çalıştırır.
    """
    try:
        account = MarketplaceAccount.objects.get(id=account_id)
        service = TrendyolSyncService(account=account)
        service.sync_all()
        return f"Success: Sync completed for {account.store_name}"
    except MarketplaceAccount.DoesNotExist:
        logger.error(f"Account {account_id} not found for sync.")
        return "Error: Account not found"
    except Exception as e:
        logger.error(f"Sync failed for account {account_id}: {e}")
        # Raise the error so it can be caught by synchronous API views
        raise ValueError(str(e))
