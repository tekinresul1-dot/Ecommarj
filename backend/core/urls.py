from django.urls import path
from .auth_views import RegisterView, LoginView, MeView
from .views import (
    DashboardOverviewView, MockReportsView, TriggerSyncView,
    ProductListView, OrderListView, ProductAnalysisView,
    TrendyolTestConnectionView, TrendyolSaveCredentialsView,
    CategoryAnalysisView, ReturnAnalysisView, AdsAnalysisView,
    ProductExcelExportView, ProductExcelImportView,
)
from .sync_views import (
    TrendyolFullSyncView, TrendyolIncrementalSyncView,
    TrendyolBackfillSyncView, TrendyolClaimsSyncView,
    TrendyolWebhookView, SyncStatusView,
)

urlpatterns = [
    # Auth
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/me/", MeView.as_view(), name="auth-me"),

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
    path("orders/", OrderListView.as_view(), name="order-list"),
    
    # Reports — specific endpoints first, then catch-all mock
    path("reports/product-analysis/", ProductAnalysisView.as_view(), name="product-analysis"),
    path("reports/categories/", CategoryAnalysisView.as_view(), name="category-analysis"),
    path("reports/returns/", ReturnAnalysisView.as_view(), name="return-analysis"),
    path("reports/ads/", AdsAnalysisView.as_view(), name="ads-analysis"),
    path("reports/<str:report_type>/", MockReportsView.as_view(), name="reports-mock"),
]

