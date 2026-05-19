"""
Django settings for ecommarj_backend project.
"""

import os
from pathlib import Path
from datetime import timedelta
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY") or os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY environment variable is not set. "
        "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
    )

# Symmetric encryption key for marketplace API credentials at rest.
# MUST be a 32-byte url-safe base64 Fernet key, independent of SECRET_KEY so
# that rotating the JWT signing key never makes stored credentials unreadable.
# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise ImproperlyConfigured(
        "ENCRYPTION_KEY environment variable is not set. "
        "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
    )

DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = (
    os.getenv("DJANGO_ALLOWED_HOSTS")
    or os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1")
).split(",")

APPEND_SLASH = True


# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    # Local apps
    "core",
]

JAZZMIN_SETTINGS = {
    "site_title": "EcomMarj Admin",
    "site_header": "EcomMarj",
    "site_brand": "EcomMarj",
    "welcome_sign": "EcomMarj Paneline Hoş Geldiniz",
    "copyright": "EcomMarj Ltd",
    "search_model": ["auth.User", "core.Order"],
    "user_avatar": None,
    "topmenu_links": [
        {"name": "Ana Sayfa", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Siteyi Görüntüle", "url": "https://ecommarj.com", "new_window": True},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "core.Organization": "fas fa-building",
        "core.UserProfile": "fas fa-id-card",
        "core.MarketplaceAccount": "fas fa-store",
        "core.Product": "fas fa-box",
        "core.ProductVariant": "fas fa-boxes",
        "core.Order": "fas fa-shopping-cart",
        "core.OrderItem": "fas fa-list",
        "core.FinancialTransaction": "fas fa-money-bill-wave",
        "core.ProfitSnapshot": "fas fa-chart-line",
        "core.SyncAuditLog": "fas fa-clipboard-list",
    },
    "order_with_respect_to": ["core", "auth"],
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-info",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_fixed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "ecommarj_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "ecommarj_backend.wsgi.application"


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

if all([POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD]):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": POSTGRES_DB,
            "USER": POSTGRES_USER,
            "PASSWORD": POSTGRES_PASSWORD,
            "HOST": POSTGRES_HOST,
            "PORT": POSTGRES_PORT,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ---------------------------------------------------------------------------
# Auth & Password validation
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "tr"
TIME_ZONE = "Europe/Istanbul"
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"


# ---------------------------------------------------------------------------
# Email — OTP gönderimi için SMTP ayarları (.env'den okunur)
# ---------------------------------------------------------------------------

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "ecommarj_backend.email_backend.CertifiEmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() in ("true", "1", "yes")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "EcomMarj <info@ecommarj.com>")


# ---------------------------------------------------------------------------
# Google OAuth
# ---------------------------------------------------------------------------

GOOGLE_CLIENT_ID = (
    os.getenv("GOOGLE_CLIENT_ID")
    or os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    or os.getenv("NEXT_PUBLIC_GOOGLE_CLIENT_ID")
    or ""
).strip()
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
GOOGLE_OAUTH_CLIENT_ID = GOOGLE_CLIENT_ID
GOOGLE_OAUTH_CLIENT_IDS = [
    client_id.strip()
    for client_id in os.getenv("GOOGLE_OAUTH_CLIENT_IDS", GOOGLE_CLIENT_ID).split(",")
    if client_id.strip()
]


# ---------------------------------------------------------------------------
# Default primary key field type
# ---------------------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "20/minute",
        "user": "100/minute",
        "login": "5/minute",
        "otp": "3/minute",
    },
    "EXCEPTION_HANDLER": "ecommarj_backend.exception_handler.custom_exception_handler",
}


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")

CORS_ALLOW_CREDENTIALS = True

_default_csrf = "http://localhost:3000,http://127.0.0.1:3000,https://ecommarj.com,https://www.ecommarj.com,https://staging.ecommarj.com"
CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", _default_csrf).split(",")

# Django behind Nginx HTTPS reverse proxy
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# ---------------------------------------------------------------------------
# Simple JWT
# ---------------------------------------------------------------------------

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# Shared secret that Trendyol must send (X-Webhook-Secret header) so the
# unauthenticated webhook endpoint cannot be abused as a task-trigger oracle.
TRENDYOL_WEBHOOK_SECRET = os.getenv("TRENDYOL_WEBHOOK_SECRET", "")


# Cache — OTP ve session için Redis (Celery ile aynı Redis instance)
_REDIS_BASE = os.getenv("REDIS_URL", "redis://localhost:6379/0")
# Cache için DB/1 kullan — Celery broker DB/0'dan ayrı tutmak için
_CACHE_REDIS_URL = _REDIS_BASE.rsplit("/", 1)[0] + "/1"

# Development'ta Redis yoksa LocMem'e dön
if DEBUG and not os.getenv("REDIS_URL"):
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake",
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": _CACHE_REDIS_URL,
        }
    }

CELERY_BROKER_URL = _REDIS_BASE
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Europe/Istanbul"

# ---------------------------------------------------------------------------
# Celery Beat — Otomatik Periyodik Görevler
# ---------------------------------------------------------------------------
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Her 15 dakikada bir tüm aktif hesaplar için artımlı sipariş senkronizasyonu
    "trendyol-incremental-sync-all": {
        "task": "core.tasks.trendyol_incremental_sync_all_accounts",
        "schedule": crontab(minute="*/15"),
    },
    # Her 15 dakikada bir iade/talep senkronizasyonu
    "trendyol-claims-sync-all": {
        "task": "core.tasks.trendyol_claims_sync_all_accounts",
        "schedule": crontab(minute="*/15"),
    },
    # Her 6 saatte bir uzlaştırma (son 1/3/7 günlük pencereleri yeniden çek)
    "trendyol-reconciliation-all": {
        "task": "core.tasks.trendyol_reconciliation_all_accounts",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    # Günde bir kez tüm hesaplar için ürün sync (fiyat/stok/komisyon güncellemeleri)
    "trendyol-product-sync-all": {
        "task": "core.tasks.trendyol_product_sync_all_accounts",
        "schedule": crontab(minute=0, hour=3),  # Her gece 03:00
    },
    # Her 6 saatte bir reklam gider senkronizasyonu
    "trendyol-ad-expense-sync-all": {
        "task": "core.tasks.trendyol_ad_expense_sync_all_accounts",
        "schedule": crontab(minute=30, hour="*/6"),
    },
    # Her gece 02:00'da CHE finansal işlem senkronizasyonu
    "che-financial-transactions-sync": {
        "task": "core.tasks.sync_financial_transactions_task",
        "schedule": crontab(minute=0, hour=2),
    },
    # Her gece 00:00 — bitişi geçmiş abonelikleri expired yap
    "subscriptions-expire-overdue": {
        "task": "core.tasks.expire_overdue_subscriptions_task",
        "schedule": crontab(minute=0, hour=0),
    },
    # Her gece 09:00 — 3 gün içinde sona erecek aboneliklere bilgilendirme
    "subscriptions-notify-expiring": {
        "task": "core.tasks.notify_expiring_subscriptions_task",
        "schedule": crontab(minute=0, hour=9),
    },
    # Her gece 01:00 — 7+ gün gecikmiş ödemesi olanların erişimini kes
    "subscriptions-cut-overdue-payments": {
        "task": "core.tasks.cut_access_for_overdue_payments_task",
        "schedule": crontab(minute=0, hour=1),
    },
}

# ---------------------------------------------------------------------------
# Production Security Settings
# ---------------------------------------------------------------------------

if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # SSL redirect is handled by Nginx, never by Django behind a reverse proxy
    SECURE_SSL_REDIRECT = False
    X_FRAME_OPTIONS = "DENY"
    # HSTS settings
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# PayTR Sanal Pos
PAYTR_MERCHANT_ID = os.getenv("PAYTR_MERCHANT_ID", "")
PAYTR_MERCHANT_KEY = os.getenv("PAYTR_MERCHANT_KEY", "")
PAYTR_MERCHANT_SALT = os.getenv("PAYTR_MERCHANT_SALT", "")
PAYTR_TEST_MODE = os.getenv("PAYTR_TEST_MODE", "False").lower() in ("true", "1", "yes")
