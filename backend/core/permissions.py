"""
Custom DRF permissions for EcomMarj.

`IsSubscribed` artık tam erişim kontrolü yapar (check_user_access üzerinden):
is_active → is_suspended → 7+ gün gecikmiş ödeme → abonelik durumu. admin_override
(profilde veya abonelikte) tüm engellemeleri geçer; superuser her zaman geçer.
Tek bir noktadan tüm korumalı view'lara uygulanır — view tarafında değişiklik
gerekmez.
"""
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission


class IsSubscribed(BasePermission):
    """
    Tam erişim hakkı kontrolü. Engelse PermissionDenied (`detail`) mesajı
    kullanıcıya net bilgi verir.
    """
    message = "Aboneliğiniz aktif değil. Erişmek için lütfen aboneliğinizi yenileyin."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        # Lazy import — apps/migration sırasında circular import'u önler
        from core.services.subscription_service import check_user_access
        allowed, reason = check_user_access(user)
        if not allowed:
            # 403'te kullanıcıya açıklayıcı mesaj döndür
            raise PermissionDenied(reason or "Erişim engellendi.")
        return True
