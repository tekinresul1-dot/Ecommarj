"""
URL configuration for ecommarj_backend project.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Django admin /django-admin/'e taşındı — kök /admin yeni Next.js yönetici
    # paneline ayrıldı. Eski referanslar Next rewrite üzerinden çalışmaz; doğrudan
    # /django-admin/ adresine yönlenmelidir.
    path("django-admin/", admin.site.urls),
    path("api/", include("core.urls")),
]
