from django.urls import path
from .auth_views import (
    RegisterView, RegisterVerifyView, RegisterResendOTPView,
    LoginView, MeView, SendOTPView, VerifyOTPView, UpdateOnboardingStatusView
)
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    DashboardOverviewView, MockReportsView, TriggerSyncView,
    ProductListView, OrderListView, ProductAnalysisView, ProductProfitabilityView,
    TrendyolTestConnectionView, TrendyolSaveCredentialsView,
    CategoryAnalysisView, ReturnAnalysisView, AdsAnalysisView,
    ProductExcelExportView, ProductExcelImportView, ProductStockSyncView,
    OrderExcelExportView, LivePerformanceView,
    ProductProfitabilityExcelExportView,
)
from .sync_views import (
    TrendyolFullSyncView, TrendyolIncrementalSyncView,
    TrendyolBackfillSyncView, TrendyolClaimsSyncView,
    TrendyolWebhookView, SyncStatusView,
)

urlpatterns = [
    # Auth
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/register/verify/", RegisterVerifyView.as_view(), name="auth-register-verify"),
    path("auth/register/resend-otp/", RegisterResendOTPView.as_view(), name="auth-register-resend"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/send-otp/", SendOTPView.as_view(), name="auth-send-otp"),
    path("auth/verify-otp/", VerifyOTPView.as_view(), name="auth-verify-otp"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("auth/onboarding/status/", UpdateOnboardingStatusView.as_view(), name="auth-onboarding-status"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),

    # Dashboard & Reports
    path("dashboard/overview/", DashboardOverviewView.as_view(), name="dashboard-overview"),
    path("dashboard/sync-status/", SyncStatusView.as_view(), name="sync-status"),
    path("sync/run/", TriggerSyncView.as_view(), name="sync-run"),
    
    # Sync — New endpoints
    path("sync/trendyol/orders/full/", TrendyolFullSyncView.as_view(), name="sync-full"),
    path("sync/trendyol/orders/incremental/", TrendyolIncrementalSyncView.as_view(), name="sync-incremental"),
    path("sync/trendyol/orders/backfill/", TrendyolBackfillSyncView.as_view(), name="sync-backfill"),
    path("sync/trendyol/claims/", TrendyolClaimsSyncView.as_view(), name="sync-claims"),
    
    # Webhook
    path("integrations/trendyol/webhook/", TrendyolWebhookView.as_view(), name="trendyol-webhook"),
    
    # Settings & Data
    path("integrations/trendyol/test-connection/", TrendyolTestConnectionView.as_view(), name="trendyol-test-conn"),
    path("integrations/trendyol/save-credentials/", TrendyolSaveCredentialsView.as_view(), name="trendyol-save-cred"),
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/export-excel/", ProductExcelExportView.as_view(), name="product-export-excel"),
    path("products/import-excel/", ProductExcelImportView.as_view(), name="product-import-excel"),
    path("products/sync-stock/", ProductStockSyncView.as_view(), name="product-sync-stock"),
    path("orders/", OrderListView.as_view(), name="order-list"),
    path("orders/export-excel/", OrderExcelExportView.as_view(), name="order-export-excel"),

    # Live Performance
    path("live-performance/", LivePerformanceView.as_view(), name="live-performance"),
    
    # Reports — specific endpoints first, then catch-all mock
    path("reports/product-profitability/", ProductProfitabilityView.as_view(), name="product-profitability"),
    path("reports/product-analysis/", ProductAnalysisView.as_view(), name="product-analysis"),
    path("reports/product-profitability/export-excel/", ProductProfitabilityExcelExportView.as_view(), name="product-profitability-export"),
    path("reports/categories/", CategoryAnalysisView.as_view(), name="category-analysis"),
    path("reports/returns/", ReturnAnalysisView.as_view(), name="return-analysis"),
    path("reports/ads/", AdsAnalysisView.as_view(), name="ads-analysis"),
    path("reports/<str:report_type>/", MockReportsView.as_view(), name="reports-mock"),
]

