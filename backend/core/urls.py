from django.urls import path
from .auth_views import RegisterView, LoginView, MeView
from .views import DashboardOverviewView, MockReportsView, TriggerSyncView, SettingsTrendyolAPIView, ProductListView

urlpatterns = [
    # Auth
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/me/", MeView.as_view(), name="auth-me"),

    # Dashboard & Reports
    path("dashboard/overview/", DashboardOverviewView.as_view(), name="dashboard-overview"),
    path("sync/run/", TriggerSyncView.as_view(), name="sync-run"),
    
    # Settings & Data
    path("settings/trendyol/", SettingsTrendyolAPIView.as_view(), name="settings-trendyol"),
    path("products/", ProductListView.as_view(), name="product-list"),
    
    path("reports/<str:report_type>/", MockReportsView.as_view(), name="reports-mock"),
]
