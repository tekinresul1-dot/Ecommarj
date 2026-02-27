from django.urls import path
from .auth_views import RegisterView, LoginView, MeView
from .views import DashboardOverviewView, MockReportsView, TriggerSyncView

urlpatterns = [
    # Auth
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/me/", MeView.as_view(), name="auth-me"),

    # Dashboard & Reports
    path("dashboard/overview/", DashboardOverviewView.as_view(), name="dashboard-overview"),
    path("sync/run/", TriggerSyncView.as_view(), name="sync-run"),
    path("reports/<str:report_type>/", MockReportsView.as_view(), name="reports-mock"),
]
