from django.urls import path
from .auth_views import RegisterView, LoginView, MeView
from .views import DashboardOverviewView, MockReportsView, TriggerSyncView, ProductListView
from .views import TrendyolTestConnectionView, TrendyolSaveCredentialsView

urlpatterns = [
    # Auth
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/me/", MeView.as_view(), name="auth-me"),

    # Dashboard & Reports
    path("dashboard/overview/", DashboardOverviewView.as_view(), name="dashboard-overview"),
    path("sync/run/", TriggerSyncView.as_view(), name="sync-run"),
    
    # Settings & Data
    path("integrations/trendyol/test-connection/", TrendyolTestConnectionView.as_view(), name="trendyol-test-conn"),
    path("integrations/trendyol/save-credentials/", TrendyolSaveCredentialsView.as_view(), name="trendyol-save-cred"),
    path("products/", ProductListView.as_view(), name="product-list"),
    
    path("reports/<str:report_type>/", MockReportsView.as_view(), name="reports-mock"),
]
