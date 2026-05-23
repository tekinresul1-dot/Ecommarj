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
from datetime import datetime
from zoneinfo import ZoneInfo
from celery import shared_task

from core.models import MarketplaceAccount

logger = logging.getLogger(__name__)
ISTANBUL_TZ = ZoneInfo("Europe/Istanbul")


def _parse_sync_boundary(value: str, *, is_end: bool):
    if len(value) == 10:
        hour, minute, second, microsecond = (23, 59, 59, 999999) if is_end else (0, 0, 0, 0)
        return datetime.fromisoformat(value).replace(
            hour=hour,
            minute=minute,
            second=second,
            microsecond=microsecond,
            tzinfo=ISTANBUL_TZ,
        )
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ISTANBUL_TZ)
    return parsed


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
        start_date = _parse_sync_boundary(start_date_iso, is_end=False)
        end_date = _parse_sync_boundary(end_date_iso, is_end=True)
        
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


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def trendyol_ad_expense_sync(self, account_id: int, days_back: int = 30):
    """Trendyol reklam giderlerini senkronize eder."""
    try:
        account = MarketplaceAccount.objects.get(id=account_id, is_active=True)
        from core.services.ad_expense_sync import TrendyolAdExpenseSyncService
        svc = TrendyolAdExpenseSyncService(account)
        result = svc.sync(days_back=days_back)
        return f"OK: inserted={result['inserted']} updated={result['updated']}"
    except MarketplaceAccount.DoesNotExist:
        return "Error: Account not found"
    except Exception as e:
        logger.error(f"Ad expense sync failed for {account_id}: {e}")
        raise self.retry(exc=e)


@shared_task
def trendyol_ad_expense_sync_all_accounts():
    """Tüm aktif Trendyol hesapları için reklam gider senkronizasyonu."""
    from core.models import MarketplaceAccount
    accounts = MarketplaceAccount.objects.filter(is_active=True, channel="trendyol")
    dispatched = 0
    for account in accounts:
        trendyol_ad_expense_sync.delay(account.id)
        dispatched += 1
    logger.info(f"[Beat] Ad expense sync dispatched for {dispatched} accounts")
    return f"Dispatched {dispatched} ad expense syncs"


@shared_task
def sync_financial_transactions_task(days_back: int = 15):
    """CHE (Cari Hesap Ekstresi) finansal işlemlerini tüm aktif hesaplar için senkronize eder."""
    from core.models import MarketplaceAccount
    from core.services.financial_sync import sync_financials_for_account
    accounts = MarketplaceAccount.objects.filter(is_active=True, channel="trendyol")
    results = []
    for account in accounts:
        try:
            result = sync_financials_for_account(account, days_back=days_back)
            results.append(f"{account.seller_id}: inserted={result['inserted']} updated={result['updated']}")
        except Exception as e:
            logger.error(f"[FinancialSync] Failed for {account.seller_id}: {e}")
            results.append(f"{account.seller_id}: ERROR {e}")
    return " | ".join(results)


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
        
        # CHE financials — first account sync gets 180 days, routine/manual syncs refresh 15 days
        from core.services.financial_sync import sync_financials_for_account
        che_days = 180 if not account.last_sync_at else 15
        sync_financials_for_account(account, days_back=che_days)

        # Legacy settlements are kept as a non-critical fallback for FinancialTransaction rows
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


# ============================================================================
# Yönetici paneli — abonelik yaşam döngüsü task'ları (Celery Beat)
# ============================================================================

@shared_task
def expire_overdue_subscriptions_task():
    """Her gece 00:00 — bitişi geçmiş abonelikleri 'expired' yap."""
    from core.services.subscription_service import expire_overdue_subscriptions
    count = expire_overdue_subscriptions()
    logger.info(f"[Beat] expired={count} subscriptions")
    return count


@shared_task
def notify_expiring_subscriptions_task(days_ahead: int = 3):
    """Süresi `days_ahead` gün içinde dolacak aboneler için bilgilendirme
    e-postası gönderir. Sadece aktif/trial ve admin_override olmayanlar."""
    from datetime import timedelta
    from django.conf import settings as dj_settings
    from django.core.mail import send_mail
    from django.utils import timezone
    from core.models import UserSubscription

    horizon = timezone.now() + timedelta(days=days_ahead)
    qs = (
        UserSubscription.objects
        .select_related("user", "plan")
        .filter(
            status__in=("active", "trial", "trialing"),
            admin_override=False,
            end_date__isnull=False,
            end_date__lte=horizon,
            end_date__gt=timezone.now(),
        )
    )
    sent = 0
    from_email = getattr(dj_settings, "DEFAULT_FROM_EMAIL", "info@ecommarj.com")
    for sub in qs:
        try:
            user_email = sub.user.email
            if not user_email:
                continue
            subject = "EcomMarj — Aboneliğiniz yakında sona eriyor"
            body = (
                f"Merhaba {sub.user.get_full_name() or user_email},\n\n"
                f"Aboneliğiniz {sub.end_date:%d.%m.%Y %H:%M} tarihinde sona erecek.\n"
                "Erişim kaybı yaşamamak için panelden yenileyebilirsiniz:\n"
                "https://ecommarj.com/subscription\n\n"
                "İyi günler,\nEcomMarj"
            )
            send_mail(subject, body, from_email, [user_email], fail_silently=True)
            sent += 1
        except Exception as e:
            logger.warning("[Beat] expiring-notify failed for %s: %s", sub.user_id, e)
    logger.info(f"[Beat] expiring-notify sent={sent}")
    return sent


@shared_task
def cut_access_for_overdue_payments_task():
    """7+ gün gecikmiş ödemesi olan kullanıcıların aboneliğini 'past_due' yapar
    (admin_override hariç). Erişim is_access_allowed üzerinden kapanır."""
    from datetime import timedelta
    from django.utils import timezone
    from core.models import Payment, UserSubscription

    cutoff = timezone.now() - timedelta(days=7)
    overdue_users = Payment.objects.filter(
        status="overdue", due_date__lt=cutoff,
    ).values_list("user_id", flat=True).distinct()
    affected = (
        UserSubscription.objects
        .filter(user_id__in=list(overdue_users), admin_override=False)
        .exclude(status__in=("cancelled", "expired", "suspended", "passive"))
        .update(status="past_due")
    )
    logger.info(f"[Beat] payment-overdue access cut: {affected}")
    return affected
