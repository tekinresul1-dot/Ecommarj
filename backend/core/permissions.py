"""
Custom DRF permissions for EcomMarj.
"""
from rest_framework.permissions import BasePermission


class IsSubscribed(BasePermission):
    """
    Kullanıcının aktif aboneliği varsa veya admin_override açıksa erişime izin verir.
    Superuser her zaman geçer.
    """
    message = "Aboneliğiniz aktif değil. Erişmek için lütfen aboneliğinizi yenileyin."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        try:
            return request.user.usersubscription.is_access_allowed()
        except Exception:
            # Abonelik kaydı yoksa erişime izin ver (eski kullanıcılar için)
            return True
