"""
Custom DRF permissions for EcomMarj.

Abonelik/ödeme sistemi henüz canlı kullanıma açılmadığı için `IsSubscribed`
şimdilik yalnızca oturum ve temel hesap durumunu kontrol eder. Ödeme sistemi
aktif edildiğinde bu sınıf tekrar subscription servisine bağlanabilir.
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
        if not user.is_active:
            raise PermissionDenied("Hesabınız pasif durumda. Lütfen destek ile iletişime geçin.")
        profile = getattr(user, "profile", None)
        if profile and getattr(profile, "is_suspended", False):
            reason = getattr(profile, "suspension_reason", "") or "Belirtilmedi"
            raise PermissionDenied(f"Hesabınız askıya alındı. Sebep: {reason}")
        return True
