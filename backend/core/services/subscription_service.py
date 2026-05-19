"""
Abonelik limit & yaşam döngüsü servisleri.

Mevcut limit kontrolleri (check_order_limit / check_store_limit /
check_trial_expiry) KORUNDU; yönetici paneli için yaşam döngüsü fonksiyonları
(activate/extend/cancel/expire_overdue/check_user_access) eklendi.
"""
import logging
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

logger = logging.getLogger(__name__)


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
    try:
        sub = user.usersubscription
        if sub.status == "trialing" and sub.trial_end and sub.trial_end < timezone.now():
            sub.status = "past_due"
            sub.save(update_fields=["status", "updated_at"])
    except Exception:
        pass


# =============================================================================
# Yaşam döngüsü — admin panel + Celery için
# =============================================================================

def _log_admin_action(admin, target_user, action_type, description, old=None, new=None, ip=None):
    """Sessiz hatalı bir audit log yardımcısı — log servisi başarısız olursa
    yaşam döngüsü akışını çökertmesin."""
    try:
        from core.models import AdminLog
        AdminLog.objects.create(
            admin=admin,
            target_user=target_user,
            action_type=action_type,
            description=description,
            old_value=old,
            new_value=new,
            ip_address=ip,
        )
    except Exception as e:
        logger.warning("[SubService] AdminLog yazılamadı (%s): %s", action_type, e)


def activate_subscription(user, plan, duration_days=None, admin=None, notes="", ip=None):
    """Kullanıcı için abonelik açar/yeniler. duration_days yoksa plan.duration_days
    veya interval'e göre çıkarılır. Mevcut OneToOne `usersubscription` korunur."""
    from core.models import UserSubscription

    now = timezone.now()
    if duration_days is None:
        if plan and plan.duration_days:
            duration_days = plan.duration_days
        elif plan and plan.interval == "yearly":
            duration_days = 365
        else:
            duration_days = 30

    sub, created = UserSubscription.objects.get_or_create(user=user)
    old_snapshot = {
        "status": sub.status,
        "plan_id": sub.plan_id,
        "end_date": sub.end_date.isoformat() if sub.end_date else None,
    }

    sub.plan = plan
    sub.status = "active"
    sub.start_date = now
    sub.end_date = now + timedelta(days=int(duration_days))
    sub.current_period_end = sub.end_date  # PayTR / IsSubscribed uyumluluğu
    sub.admin_override = False
    if admin is not None:
        sub.created_by_admin = admin
    if notes:
        sub.notes = notes
    sub.save()

    _log_admin_action(
        admin, user,
        "subscription_create" if created else "plan_change",
        f"{user.email} → {plan.name if plan else '—'} ({duration_days} gün)",
        old=old_snapshot,
        new={"status": sub.status, "plan_id": sub.plan_id, "end_date": sub.end_date.isoformat()},
        ip=ip,
    )
    return sub


def extend_subscription(subscription, days, admin=None, ip=None):
    """Mevcut bitiş tarihine `days` ekler. Bitiş geçmişse 'şimdi'den itibaren uzar."""
    now = timezone.now()
    base = subscription.end_date or subscription.current_period_end or now
    if base < now:
        base = now
    old_end = subscription.end_date or subscription.current_period_end
    subscription.end_date = base + timedelta(days=int(days))
    subscription.current_period_end = subscription.end_date
    if subscription.status in ("expired", "past_due", "cancelled", "passive"):
        subscription.status = "active"
    subscription.save()

    _log_admin_action(
        admin, subscription.user,
        "subscription_extend",
        f"{subscription.user.email} aboneliği {days} gün uzatıldı.",
        old={"end_date": old_end.isoformat() if old_end else None},
        new={"end_date": subscription.end_date.isoformat(), "status": subscription.status},
        ip=ip,
    )
    return subscription


def cancel_subscription(subscription, admin=None, reason="", ip=None):
    """Aboneliği iptal eder. Erişim is_access_allowed üzerinden kapanır."""
    old_status = subscription.status
    subscription.status = "cancelled"
    subscription.admin_override = False
    if reason:
        subscription.notes = (subscription.notes + ("\n" if subscription.notes else "") + f"İptal: {reason}").strip()
    subscription.save()

    _log_admin_action(
        admin, subscription.user, "subscription_cancel",
        f"{subscription.user.email} aboneliği iptal edildi. Sebep: {reason or '—'}",
        old={"status": old_status},
        new={"status": "cancelled"},
        ip=ip,
    )
    return subscription


def start_or_extend_trial(subscription, days=14, admin=None, ip=None):
    """Trial başlat veya uzat (admin paneli)."""
    now = timezone.now()
    base = subscription.trial_end_date or subscription.trial_end or now
    if base < now:
        base = now
    new_trial_end = base + timedelta(days=int(days))
    subscription.trial_end_date = new_trial_end
    subscription.trial_end = new_trial_end  # eski alan uyumluluğu
    subscription.status = "trial"
    if not subscription.start_date:
        subscription.start_date = now
    subscription.save()

    _log_admin_action(
        admin, subscription.user, "subscription_trial",
        f"{subscription.user.email} trial {days} gün uzatıldı → {new_trial_end:%Y-%m-%d}",
        new={"trial_end_date": new_trial_end.isoformat(), "status": "trial"},
        ip=ip,
    )
    return subscription


def expire_overdue_subscriptions():
    """Bitişi geçmiş aktif/trial abonelikleri 'expired'a çeker.
    Celery beat tarafından her gece çalışır. Sayım döner."""
    from core.models import UserSubscription
    now = timezone.now()

    # Aktif olup end_date geçmiş olanlar
    expired_active = UserSubscription.objects.filter(
        status__in=("active", "trial", "trialing"),
        end_date__isnull=False,
        end_date__lt=now,
        admin_override=False,
    ).exclude(plan__plan_type="lifetime")
    count_active = expired_active.update(status="expired")

    # Trial bitişi geçmiş ama end_date olmayanlar (eski trial_end alanı)
    expired_trial = UserSubscription.objects.filter(
        status__in=("trial", "trialing"),
        end_date__isnull=True,
        trial_end__isnull=False,
        trial_end__lt=now,
        admin_override=False,
    )
    count_trial = expired_trial.update(status="expired")

    total = count_active + count_trial
    if total:
        logger.info("[SubService] %s abonelik süresi dolmuş olarak işaretlendi.", total)
    return total


def check_user_access(user) -> tuple[bool, str]:
    """Kullanıcının erişim hakkı var mı? (allowed, reason) döner.
    Erişim engelleme sıralaması: is_active → is_suspended → ödeme gecikmesi →
    abonelik durumu (admin_override hepsini geçer)."""
    from core.models import Payment

    if not user or not user.is_authenticated:
        return False, "Giriş gerekiyor."
    if not user.is_active:
        return False, "Hesabınız pasif durumda. Lütfen destek ile iletişime geçin."

    profile = getattr(user, "profile", None)
    if profile and profile.is_suspended:
        return False, f"Hesabınız askıya alındı. Sebep: {profile.suspension_reason or 'Belirtilmedi'}"

    # 7+ gün gecikmiş ödeme
    seven_days_ago = timezone.now() - timedelta(days=7)
    has_overdue = Payment.objects.filter(
        user=user, status="overdue", due_date__lt=seven_days_ago,
    ).exists()
    if has_overdue and not (profile and profile.admin_override):
        return False, "Ödemeniz 7 günden fazla gecikti. Lütfen ödemenizi yapın."

    # admin_override (profilde veya abonelikte) varsa direkt geç
    if profile and profile.admin_override:
        return True, ""

    sub = getattr(user, "usersubscription", None)
    if sub is None:
        return False, "Aktif aboneliğiniz yok."
    if not sub.is_access_allowed():
        msg_map = {
            "expired": "Aboneliğinizin süresi doldu. Lütfen yenileyin.",
            "cancelled": "Aboneliğiniz iptal edilmiş.",
            "suspended": "Aboneliğiniz askıya alındı.",
            "passive": "Aboneliğiniz pasif durumda.",
            "past_due": "Ödemeniz gecikti.",
        }
        return False, msg_map.get(sub.status, "Aktif aboneliğiniz yok.")
    return True, ""
