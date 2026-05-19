"""
Yönetici paneli REST API rotaları. Üst URLconf altında /api/admin/ prefix'iyle
include edilir.
"""
from django.urls import path

from core.admin_api import (
    AdminDashboardView,
    AdminUserListView, AdminUserDetailView,
    AdminUserSuspendView, AdminUserActivateView,
    AdminSubscriptionListView, AdminUserCreateSubscriptionView,
    AdminSubscriptionDetailView, AdminSubscriptionExtendView,
    AdminSubscriptionCancelView, AdminSubscriptionTrialView,
    AdminPaymentListView,
    AdminPaymentDetailView, AdminPaymentStatsView,
    AdminAccessCodeListView, AdminAccessCodeCreateView,
    AdminAccessCodeDetailView, AdminAccessCodeRegenerateView,
    AdminLogListView, AdminPlanListView,
)

urlpatterns = [
    path("dashboard/", AdminDashboardView.as_view()),

    # Users
    path("users/", AdminUserListView.as_view()),
    path("users/<int:user_id>/", AdminUserDetailView.as_view()),
    path("users/<int:user_id>/suspend/", AdminUserSuspendView.as_view()),
    path("users/<int:user_id>/activate/", AdminUserActivateView.as_view()),
    path("users/<int:user_id>/subscription/", AdminUserCreateSubscriptionView.as_view()),

    # Subscriptions
    path("subscriptions/", AdminSubscriptionListView.as_view()),
    path("subscriptions/<int:sub_id>/", AdminSubscriptionDetailView.as_view()),
    path("subscriptions/<int:sub_id>/extend/", AdminSubscriptionExtendView.as_view()),
    path("subscriptions/<int:sub_id>/cancel/", AdminSubscriptionCancelView.as_view()),
    path("subscriptions/<int:sub_id>/trial/", AdminSubscriptionTrialView.as_view()),

    # Payments
    path("payments/", AdminPaymentListView.as_view()),
    path("payments/<int:payment_id>/", AdminPaymentDetailView.as_view()),
    path("payments/stats/", AdminPaymentStatsView.as_view()),

    # Access codes
    path("access-codes/", AdminAccessCodeListView.as_view()),
    path("access-codes/<int:code_id>/", AdminAccessCodeDetailView.as_view()),
    path("access-codes/<int:code_id>/regenerate/", AdminAccessCodeRegenerateView.as_view()),

    # Plans (yardımcı)
    path("plans/", AdminPlanListView.as_view()),

    # Logs
    path("logs/", AdminLogListView.as_view()),
]
