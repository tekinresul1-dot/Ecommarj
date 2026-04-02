"""
Django signals for EcomMarj Core app.
"""
import logging
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

logger = logging.getLogger(__name__)


def _trigger_initial_sync(account):
    """Queue a full sync task for a newly activated MarketplaceAccount."""
    try:
        from core.tasks import sync_all_trendyol_data_task
        task = sync_all_trendyol_data_task.delay(str(account.id))
        logger.info(
            f"[Signal] Initial sync queued for account {account.seller_id} "
            f"(org={account.organization}) task_id={task.id}"
        )
    except Exception as e:
        logger.error(f"[Signal] Failed to queue initial sync for account {account.id}: {e}")


def connect_signals():
    """Called from CoreConfig.ready() to wire up all signals."""
    from core.models import MarketplaceAccount
    from django.contrib.auth import get_user_model
    User = get_user_model()

    @receiver(post_save, sender=User)
    def create_user_subscription(sender, instance, created, **kwargs):
        """Yeni kullanıcıya otomatik 14 günlük deneme aboneliği oluştur."""
        if not created:
            return
        try:
            from core.models import UserSubscription
            UserSubscription.objects.get_or_create(
                user=instance,
                defaults={
                    "status": "trialing",
                    "trial_end": timezone.now() + timedelta(days=14),
                },
            )
        except Exception as e:
            logger.error(f"[Signal] Failed to create subscription for {instance.email}: {e}")

    @receiver(post_save, sender=MarketplaceAccount)
    def marketplace_account_post_save(sender, instance, created, **kwargs):
        """
        When a MarketplaceAccount is saved with credentials for the first time,
        queue an initial full sync (products + orders + settlements).
        """
        has_credentials = bool(instance.api_key and instance.api_secret and instance.seller_id)
        if not has_credentials or not instance.is_active:
            return

        if created:
            # Brand-new account with credentials → sync immediately
            _trigger_initial_sync(instance)
        else:
            # Existing account updated — only sync if it just became active
            # (Avoid re-syncing on every credential update)
            try:
                from core.models import Product
                has_products = Product.objects.filter(organization=instance.organization).exists()
                if not has_products:
                    _trigger_initial_sync(instance)
            except Exception:
                pass
