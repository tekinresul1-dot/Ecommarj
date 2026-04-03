"""
Abonelik limit kontrol servisleri.
"""
from decimal import Decimal


def check_order_limit(user):
    """Kullanıcının aylık sipariş limitini kontrol eder."""
    from django.utils import timezone
    from core.models import Order
    try:
        sub = user.usersubscription
        if sub.admin_override:
            return True, None
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        try:
            profile = user.profile
            org = profile.organization
        except Exception:
            return True, None
        if not org:
            return True, None
        order_count = Order.objects.filter(
            organization=org, order_date__gte=month_start
        ).count()
        limit = sub.plan.order_limit if sub.plan else 1000
        if order_count >= limit:
            return False, f"Aylık {limit} sipariş limitine ulaştınız. Planınızı yükseltin."
        return True, None
    except Exception:
        return True, None


def check_store_limit(user):
    """Kullanıcının mağaza bağlantı limitini kontrol eder."""
    from core.models import MarketplaceAccount, UserProfile
    try:
        sub = user.usersubscription
        if sub.admin_override:
            return True, None
        try:
            org = user.profile.organization
        except Exception:
            return True, None
        if not org:
            return True, None
        store_count = MarketplaceAccount.objects.filter(
            organization=org, is_active=True
        ).count()
        limit = sub.plan.store_limit if sub.plan else 1
        if store_count >= limit:
            return False, f"Planınız maksimum {limit} mağaza bağlantısına izin veriyor."
        return True, None
    except Exception:
        return True, None


def check_trial_expiry(user):
    """Trial süresi dolduysa status'u past_due'ya çek."""
    from django.utils import timezone
    try:
        sub = user.usersubscription
        if sub.status == "trialing" and sub.trial_end and sub.trial_end < timezone.now():
            sub.status = "past_due"
            sub.save(update_fields=["status", "updated_at"])
    except Exception:
        pass
