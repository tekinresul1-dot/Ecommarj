"""
Yönetici (is_staff) paneli için REST API endpoint'leri.

Tüm uçlar IsAdminUser ile korunur. URL prefix: /api/admin/
Bu modül mevcut iş mantığı view'larını DEĞİŞTİRMEZ — sadece üzerine bir yönetim
katmanı ekler. Tüm yaşam döngüsü işlemleri ilgili servislere delege edilir;
servisler de AdminLog'a yazar.
"""
from __future__ import annotations
import logging
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import (
    UserProfile, SubscriptionPlan, UserSubscription, Payment,
    AccessCode, AdminLog, LoginAttempt, MarketplaceAccount,
)
from core.services import subscription_service as sub_svc
from core.services import access_code_service as code_svc

logger = logging.getLogger(__name__)
User = get_user_model()


# -----------------------------------------------------------------------------
# Yardımcılar
# -----------------------------------------------------------------------------

def _client_ip(request) -> str | None:
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
    return xff or request.META.get("REMOTE_ADDR")


def _log(admin, target_user, action_type, description, *, old=None, new=None, ip=None):
    try:
        AdminLog.objects.create(
            admin=admin,
            target_user=target_user,
            action_type=action_type,
            description=description,
            old_value=old,
            new_value=new,
            ip_address=ip,
        )
    except Exception as e:
        logger.warning("[AdminAPI] AdminLog yazılamadı: %s", e)


class AdminPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 200


def _serialize_user(user, *, detail=False):
    profile = getattr(user, "profile", None)
    sub = getattr(user, "usersubscription", None)
    data = {
        "id": user.id,
        "email": user.email,
        "full_name": f"{user.first_name} {user.last_name}".strip(),
        "is_active": user.is_active,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
        "date_joined": user.date_joined.isoformat() if user.date_joined else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "profile": {
            "phone": getattr(profile, "phone", "") or "",
            "company": getattr(profile, "company", "") or "",
            "is_suspended": getattr(profile, "is_suspended", False),
            "suspension_reason": getattr(profile, "suspension_reason", "") or "",
            "admin_note": getattr(profile, "admin_note", "") or "",
            "is_priority": getattr(profile, "is_priority", False),
            "is_risky": getattr(profile, "is_risky", False),
            "admin_override": getattr(profile, "admin_override", False),
            "last_login_ip": str(getattr(profile, "last_login_ip", "") or ""),
            "email_verified": getattr(profile, "email_verified", False),
            "google_connected": getattr(profile, "google_connected", False),
            "trendyol_store_count": getattr(profile, "trendyol_store_count", 0),
        } if profile else None,
        "subscription": _serialize_subscription(sub) if sub else None,
    }
    if detail:
        data["payments"] = [
            _serialize_payment(p)
            for p in Payment.objects.filter(user=user).select_related("plan").order_by("-created_at")[:50]
        ]
        data["access_codes"] = [
            _serialize_access_code(c, mask=True)
            for c in AccessCode.objects.filter(user=user).order_by("-created_at")[:50]
        ]
        data["recent_logs"] = [
            _serialize_log(l)
            for l in AdminLog.objects.filter(target_user=user).select_related("admin").order_by("-created_at")[:50]
        ]
    return data


def _serialize_subscription(sub):
    if sub is None:
        return None
    return {
        "id": sub.id,
        "user_id": sub.user_id,
        "user_email": sub.user.email if sub.user_id else None,
        "plan_id": sub.plan_id,
        "plan_name": sub.plan.name if sub.plan_id else None,
        "status": sub.status,
        "admin_override": sub.admin_override,
        "start_date": sub.start_date.isoformat() if sub.start_date else None,
        "end_date": sub.end_date.isoformat() if sub.end_date else None,
        "trial_end_date": (sub.trial_end_date or sub.trial_end).isoformat() if (sub.trial_end_date or sub.trial_end) else None,
        "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
        "notes": sub.notes or "",
        "created_by_admin_id": sub.created_by_admin_id,
    }


def _serialize_payment(p):
    return {
        "id": p.id,
        "user_id": p.user_id,
        "user_email": p.user.email if p.user_id else None,
        "subscription_id": p.subscription_id,
        "plan_id": p.plan_id,
        "plan_name": p.plan.name if p.plan_id else None,
        "amount": str(p.amount),
        "currency": p.currency,
        "status": p.status,
        "merchant_oid": p.merchant_oid,
        "paytr_transaction_id": p.paytr_transaction_id or "",
        "payment_date": p.payment_date.isoformat() if p.payment_date else None,
        "due_date": p.due_date.isoformat() if p.due_date else None,
        "invoice_note": p.invoice_note or "",
        "added_by_admin": p.added_by_admin,
        "created_at": p.created_at.isoformat(),
    }


def _serialize_access_code(ac, *, mask=False):
    code = ac.code
    if mask and len(code) > 4:
        code = code[:2] + "*" * (len(code) - 4) + code[-2:]
    return {
        "id": ac.id,
        "user_id": ac.user_id,
        "user_email": ac.user.email if ac.user_id else None,
        "code": code,
        "is_active": ac.is_active,
        "is_lifetime": ac.is_lifetime,
        "expires_at": ac.expires_at.isoformat() if ac.expires_at else None,
        "max_uses": ac.max_uses,
        "use_count": ac.use_count,
        "last_used_at": ac.last_used_at.isoformat() if ac.last_used_at else None,
        "created_at": ac.created_at.isoformat(),
        "created_by_id": ac.created_by_id,
    }


def _serialize_log(l):
    return {
        "id": l.id,
        "admin_id": l.admin_id,
        "admin_email": l.admin.email if l.admin_id else None,
        "target_user_id": l.target_user_id,
        "target_user_email": l.target_user.email if l.target_user_id else None,
        "action_type": l.action_type,
        "description": l.description,
        "old_value": l.old_value,
        "new_value": l.new_value,
        "created_at": l.created_at.isoformat(),
        "ip_address": str(l.ip_address) if l.ip_address else None,
    }


# =============================================================================
# DASHBOARD
# =============================================================================

class AdminDashboardView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        week_ahead = now + timedelta(days=7)

        user_qs = User.objects.all()
        total_users = user_qs.count()
        active_users = user_qs.filter(is_active=True).count()
        passive_users = user_qs.filter(is_active=False).count()
        trial_users = UserSubscription.objects.filter(status__in=("trial", "trialing")).count()
        paid_users = UserSubscription.objects.filter(status="active").count()

        revenue_month = Payment.objects.filter(
            status__in=Payment.PAID_STATUSES,
            payment_date__gte=month_start,
        ).aggregate(s=Sum("amount"))["s"] or Decimal("0")
        revenue_month_fallback = Payment.objects.filter(
            status__in=Payment.PAID_STATUSES,
            payment_date__isnull=True,
            created_at__gte=month_start,
        ).aggregate(s=Sum("amount"))["s"] or Decimal("0")
        revenue_month = revenue_month + revenue_month_fallback

        overdue_count = Payment.objects.filter(status="overdue").count()

        expiring_soon = (
            UserSubscription.objects
            .select_related("user", "plan")
            .filter(end_date__gte=now, end_date__lte=week_ahead, status__in=("active", "trial", "trialing"))
            .order_by("end_date")[:25]
        )

        recent_signups = (
            User.objects.order_by("-date_joined")[:10]
        )
        recent_logins = (
            LoginAttempt.objects.filter(success=True)
            .select_related("user")
            .order_by("-attempted_at")[:10]
        )
        recent_logs = (
            AdminLog.objects.select_related("admin", "target_user").order_by("-created_at")[:10]
        )

        return Response({
            "totals": {
                "users": total_users,
                "active": active_users,
                "passive": passive_users,
                "trial": trial_users,
                "paid": paid_users,
                "revenue_this_month": str(revenue_month),
                "overdue_payments": overdue_count,
            },
            "expiring_soon": [_serialize_subscription(s) for s in expiring_soon],
            "recent_signups": [
                {
                    "id": u.id, "email": u.email,
                    "name": f"{u.first_name} {u.last_name}".strip(),
                    "date_joined": u.date_joined.isoformat() if u.date_joined else None,
                }
                for u in recent_signups
            ],
            "recent_logins": [
                {
                    "id": la.id,
                    "user_email": la.user.email if la.user_id else None,
                    "ip_address": str(la.ip_address) if la.ip_address else None,
                    "attempted_at": la.attempted_at.isoformat(),
                }
                for la in recent_logins
            ],
            "recent_logs": [_serialize_log(l) for l in recent_logs],
        })


# =============================================================================
# KULLANICI YÖNETİMİ
# =============================================================================

class AdminUserListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs = (
            User.objects.select_related("profile", "usersubscription", "usersubscription__plan")
            .all()
        )
        search = request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(
                Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(profile__company__icontains=search)
            )
        status_filter = request.query_params.get("status", "").strip()
        if status_filter == "active":
            qs = qs.filter(is_active=True, profile__is_suspended=False)
        elif status_filter == "passive":
            qs = qs.filter(is_active=False)
        elif status_filter == "trial":
            qs = qs.filter(usersubscription__status__in=("trial", "trialing"))
        elif status_filter == "suspended":
            qs = qs.filter(profile__is_suspended=True)
        elif status_filter == "paid":
            qs = qs.filter(usersubscription__status="active")

        plan_filter = request.query_params.get("plan", "").strip()
        if plan_filter:
            qs = qs.filter(usersubscription__plan_id=plan_filter)

        qs = qs.order_by("-date_joined")
        paginator = AdminPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        return paginator.get_paginated_response(
            [_serialize_user(u) for u in page]
        )


class AdminUserDetailView(APIView):
    permission_classes = [IsAdminUser]

    def _get_user(self, user_id):
        return (
            User.objects
            .select_related("profile", "usersubscription", "usersubscription__plan")
            .filter(pk=user_id).first()
        )

    def get(self, request, user_id):
        user = self._get_user(user_id)
        if not user:
            return Response({"error": "Kullanıcı bulunamadı."}, status=404)
        return Response(_serialize_user(user, detail=True))

    def patch(self, request, user_id):
        user = self._get_user(user_id)
        if not user:
            return Response({"error": "Kullanıcı bulunamadı."}, status=404)

        ip = _client_ip(request)
        old_snapshot = _serialize_user(user)
        data = request.data or {}

        # User alanları
        if "is_active" in data:
            user.is_active = bool(data["is_active"])
            user.save(update_fields=["is_active"])

        # Profil alanları
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile_changed_fields = []
        for field in (
            "admin_note", "is_priority", "is_risky", "admin_override",
            "is_suspended", "suspension_reason", "email_verified",
            "google_connected", "trendyol_store_count",
        ):
            if field in data:
                setattr(profile, field, data[field] if not isinstance(data[field], str) or field in ("admin_note", "suspension_reason") else data[field])
                # Bool/int alanları için coercion
                if field in ("is_priority", "is_risky", "admin_override", "is_suspended", "email_verified", "google_connected"):
                    setattr(profile, field, bool(data[field]))
                if field == "trendyol_store_count":
                    try:
                        setattr(profile, field, int(data[field]))
                    except Exception:
                        pass
                profile_changed_fields.append(field)
        if profile_changed_fields:
            profile.save(update_fields=profile_changed_fields)

        _log(request.user, user, "user_update",
             f"{user.email} güncellendi: {', '.join(profile_changed_fields) or 'is_active'}",
             old=old_snapshot, new=_serialize_user(user), ip=ip)
        return Response(_serialize_user(user, detail=True))


class AdminUserSuspendView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, user_id):
        user = User.objects.filter(pk=user_id).first()
        if not user:
            return Response({"error": "Kullanıcı bulunamadı."}, status=404)
        reason = (request.data or {}).get("reason", "").strip()
        if not reason:
            return Response({"error": "Sebep zorunludur."}, status=400)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.is_suspended = True
        profile.suspension_reason = reason
        profile.save(update_fields=["is_suspended", "suspension_reason"])
        _log(request.user, user, "user_suspend",
             f"{user.email} askıya alındı: {reason}", ip=_client_ip(request))
        return Response(_serialize_user(user))


class AdminUserActivateView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, user_id):
        user = User.objects.filter(pk=user_id).first()
        if not user:
            return Response({"error": "Kullanıcı bulunamadı."}, status=404)
        user.is_active = True
        user.save(update_fields=["is_active"])
        profile, _ = UserProfile.objects.get_or_create(user=user)
        was_suspended = profile.is_suspended
        profile.is_suspended = False
        profile.suspension_reason = ""
        profile.save(update_fields=["is_suspended", "suspension_reason"])
        action = "user_unsuspend" if was_suspended else "user_activate"
        _log(request.user, user, action, f"{user.email} aktifleştirildi.", ip=_client_ip(request))
        return Response(_serialize_user(user))


# =============================================================================
# ABONELİK YÖNETİMİ
# =============================================================================

class AdminSubscriptionListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs = UserSubscription.objects.select_related("user", "plan").all()
        status_filter = request.query_params.get("status", "").strip()
        if status_filter:
            qs = qs.filter(status=status_filter)
        plan_filter = request.query_params.get("plan", "").strip()
        if plan_filter:
            qs = qs.filter(plan_id=plan_filter)
        if request.query_params.get("expiring_soon") in ("1", "true", "True"):
            now = timezone.now()
            qs = qs.filter(end_date__gte=now, end_date__lte=now + timedelta(days=7))
        qs = qs.order_by("-updated_at")
        paginator = AdminPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        return paginator.get_paginated_response([_serialize_subscription(s) for s in page])


class AdminUserCreateSubscriptionView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, user_id):
        user = User.objects.filter(pk=user_id).first()
        if not user:
            return Response({"error": "Kullanıcı bulunamadı."}, status=404)
        data = request.data or {}
        plan_id = data.get("plan_id")
        plan = SubscriptionPlan.objects.filter(pk=plan_id).first() if plan_id else None
        if plan_id and not plan:
            return Response({"error": "Plan bulunamadı."}, status=400)
        sub = sub_svc.activate_subscription(
            user, plan,
            duration_days=data.get("duration_days"),
            admin=request.user,
            notes=data.get("notes", ""),
            ip=_client_ip(request),
        )
        return Response(_serialize_subscription(sub), status=status.HTTP_201_CREATED)


class AdminSubscriptionDetailView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, sub_id):
        sub = UserSubscription.objects.select_related("user", "plan").filter(pk=sub_id).first()
        if not sub:
            return Response({"error": "Abonelik bulunamadı."}, status=404)
        old = _serialize_subscription(sub)
        data = request.data or {}

        if "plan_id" in data:
            plan = SubscriptionPlan.objects.filter(pk=data["plan_id"]).first()
            if data["plan_id"] and not plan:
                return Response({"error": "Plan bulunamadı."}, status=400)
            sub.plan = plan
        for field in ("status", "notes"):
            if field in data:
                setattr(sub, field, data[field])
        if "admin_override" in data:
            sub.admin_override = bool(data["admin_override"])
        for dt_field in ("start_date", "end_date", "trial_end_date"):
            if dt_field in data:
                val = data[dt_field]
                if val:
                    parsed = parse_datetime(val) or parse_date(val)
                    if parsed:
                        setattr(sub, dt_field, parsed)
                else:
                    setattr(sub, dt_field, None)
        # PayTR/IsSubscribed uyumu
        if sub.end_date:
            sub.current_period_end = sub.end_date
        sub.save()

        _log(request.user, sub.user, "plan_change",
             f"{sub.user.email} aboneliği güncellendi.", old=old,
             new=_serialize_subscription(sub), ip=_client_ip(request))
        return Response(_serialize_subscription(sub))


class AdminSubscriptionExtendView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, sub_id):
        sub = UserSubscription.objects.select_related("user", "plan").filter(pk=sub_id).first()
        if not sub:
            return Response({"error": "Abonelik bulunamadı."}, status=404)
        try:
            days = int((request.data or {}).get("days", 30))
        except (TypeError, ValueError):
            return Response({"error": "days bir tamsayı olmalıdır."}, status=400)
        sub = sub_svc.extend_subscription(sub, days, admin=request.user, ip=_client_ip(request))
        return Response(_serialize_subscription(sub))


class AdminSubscriptionCancelView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, sub_id):
        sub = UserSubscription.objects.select_related("user", "plan").filter(pk=sub_id).first()
        if not sub:
            return Response({"error": "Abonelik bulunamadı."}, status=404)
        reason = (request.data or {}).get("reason", "")
        sub = sub_svc.cancel_subscription(sub, admin=request.user, reason=reason, ip=_client_ip(request))
        return Response(_serialize_subscription(sub))


class AdminSubscriptionTrialView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, sub_id):
        sub = UserSubscription.objects.select_related("user", "plan").filter(pk=sub_id).first()
        if not sub:
            return Response({"error": "Abonelik bulunamadı."}, status=404)
        try:
            days = int((request.data or {}).get("days", 14))
        except (TypeError, ValueError):
            return Response({"error": "days bir tamsayı olmalıdır."}, status=400)
        sub = sub_svc.start_or_extend_trial(sub, days=days, admin=request.user, ip=_client_ip(request))
        return Response(_serialize_subscription(sub))


# =============================================================================
# ÖDEME YÖNETİMİ
# =============================================================================

class AdminPaymentListView(APIView):
    """GET liste / POST manuel ödeme ekleme — aynı URL (/api/admin/payments/)."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs = Payment.objects.select_related("user", "plan").all()
        if (u := request.query_params.get("user")):
            qs = qs.filter(user_id=u)
        if (s := request.query_params.get("status")):
            qs = qs.filter(status=s)
        if (df := request.query_params.get("date_from")):
            dt = parse_datetime(df) or parse_date(df)
            if dt:
                qs = qs.filter(created_at__gte=dt)
        if (dto := request.query_params.get("date_to")):
            dt = parse_datetime(dto) or parse_date(dto)
            if dt:
                qs = qs.filter(created_at__lte=dt)
        qs = qs.order_by("-created_at")
        paginator = AdminPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        return paginator.get_paginated_response([_serialize_payment(p) for p in page])

    def post(self, request):
        import uuid
        data = request.data or {}
        user_id = data.get("user_id")
        amount = data.get("amount")
        if not user_id or amount is None:
            return Response({"error": "user_id ve amount zorunludur."}, status=400)
        user = User.objects.filter(pk=user_id).first()
        if not user:
            return Response({"error": "Kullanıcı bulunamadı."}, status=404)
        try:
            amount_dec = Decimal(str(amount))
        except Exception:
            return Response({"error": "Geçersiz tutar."}, status=400)

        plan = SubscriptionPlan.objects.filter(pk=data.get("plan_id")).first() if data.get("plan_id") else None
        sub = UserSubscription.objects.filter(user=user).first()

        payment = Payment.objects.create(
            user=user,
            subscription=sub,
            plan=plan,
            amount=amount_dec,
            status=data.get("status", "paid"),
            merchant_oid=f"MANUAL_{uuid.uuid4().hex}",
            payment_date=parse_datetime(data["payment_date"]) if data.get("payment_date") else timezone.now(),
            due_date=parse_datetime(data["due_date"]) if data.get("due_date") else None,
            invoice_note=data.get("invoice_note", ""),
            added_by_admin=True,
        )
        _log(request.user, user, "payment_add",
             f"{user.email} için ₺{amount_dec} ödeme eklendi.",
             new=_serialize_payment(payment), ip=_client_ip(request))
        return Response(_serialize_payment(payment), status=status.HTTP_201_CREATED)


class AdminPaymentDetailView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, payment_id):
        p = Payment.objects.select_related("user", "plan").filter(pk=payment_id).first()
        if not p:
            return Response({"error": "Ödeme bulunamadı."}, status=404)
        old = _serialize_payment(p)
        data = request.data or {}

        if "amount" in data:
            try:
                p.amount = Decimal(str(data["amount"]))
            except Exception:
                return Response({"error": "Geçersiz tutar."}, status=400)
        for field in ("status", "invoice_note", "paytr_transaction_id"):
            if field in data:
                setattr(p, field, data[field])
        for dt_field in ("payment_date", "due_date"):
            if dt_field in data:
                val = data[dt_field]
                setattr(p, dt_field, parse_datetime(val) if val else None)
        p.save()
        _log(request.user, p.user, "payment_edit",
             f"Ödeme {p.id} güncellendi.", old=old, new=_serialize_payment(p),
             ip=_client_ip(request))
        return Response(_serialize_payment(p))


class AdminPaymentStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        total_paid = Payment.objects.filter(status__in=Payment.PAID_STATUSES) \
            .aggregate(s=Sum("amount"))["s"] or Decimal("0")
        month_paid = Payment.objects.filter(
            status__in=Payment.PAID_STATUSES, payment_date__gte=month_start,
        ).aggregate(s=Sum("amount"))["s"] or Decimal("0")
        overdue = Payment.objects.filter(status="overdue").count()
        return Response({
            "total_revenue": str(total_paid),
            "month_revenue": str(month_paid),
            "overdue_count": overdue,
        })


# =============================================================================
# GİRİŞ KODLARI
# =============================================================================

class AdminAccessCodeListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs = AccessCode.objects.select_related("user", "created_by").all()
        if (u := request.query_params.get("user")):
            qs = qs.filter(user_id=u)
        active_q = request.query_params.get("active")
        if active_q in ("1", "true", "True"):
            qs = qs.filter(is_active=True)
        elif active_q in ("0", "false", "False"):
            qs = qs.filter(is_active=False)
        qs = qs.order_by("-created_at")
        paginator = AdminPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        return paginator.get_paginated_response([_serialize_access_code(c, mask=True) for c in page])


class AdminAccessCodeCreateView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        data = request.data or {}
        user_id = data.get("user_id")
        user = User.objects.filter(pk=user_id).first()
        if not user:
            return Response({"error": "Kullanıcı bulunamadı."}, status=404)
        is_lifetime = bool(data.get("is_lifetime", False))
        expires_at = parse_datetime(data["expires_at"]) if data.get("expires_at") else None
        max_uses = data.get("max_uses")
        try:
            max_uses = int(max_uses) if max_uses else None
        except (TypeError, ValueError):
            max_uses = None
        ac = code_svc.generate_code(
            user, admin=request.user, expires_at=expires_at,
            max_uses=max_uses, is_lifetime=is_lifetime, ip=_client_ip(request),
        )
        # Oluşturma anında kod tam haliyle dönülür (tek seferlik gösterim)
        return Response(_serialize_access_code(ac, mask=False), status=status.HTTP_201_CREATED)


class AdminAccessCodeDetailView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, code_id):
        ac = AccessCode.objects.filter(pk=code_id).first()
        if not ac:
            return Response({"error": "Kod bulunamadı."}, status=404)
        data = request.data or {}
        for field in ("is_active", "is_lifetime"):
            if field in data:
                setattr(ac, field, bool(data[field]))
        if "max_uses" in data:
            try:
                ac.max_uses = int(data["max_uses"]) if data["max_uses"] else None
            except (TypeError, ValueError):
                pass
        if "expires_at" in data:
            ac.expires_at = parse_datetime(data["expires_at"]) if data["expires_at"] else None
        ac.save()
        return Response(_serialize_access_code(ac, mask=True))

    def delete(self, request, code_id):
        ac = AccessCode.objects.filter(pk=code_id).first()
        if not ac:
            return Response({"error": "Kod bulunamadı."}, status=404)
        code_svc.deactivate_code(ac, admin=request.user, ip=_client_ip(request))
        return Response({"message": "Kod pasife alındı."})


class AdminAccessCodeRegenerateView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, code_id):
        ac = AccessCode.objects.filter(pk=code_id).first()
        if not ac:
            return Response({"error": "Kod bulunamadı."}, status=404)
        new_ac = code_svc.regenerate_code(ac, admin=request.user, ip=_client_ip(request))
        return Response(_serialize_access_code(new_ac, mask=False), status=status.HTTP_201_CREATED)


# =============================================================================
# ADMIN LOG
# =============================================================================

class AdminLogListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs = AdminLog.objects.select_related("admin", "target_user").all()
        if (a := request.query_params.get("admin")):
            qs = qs.filter(admin_id=a)
        if (at := request.query_params.get("action_type")):
            qs = qs.filter(action_type=at)
        if (u := request.query_params.get("user")):
            qs = qs.filter(target_user_id=u)
        if (df := request.query_params.get("date_from")):
            dt = parse_datetime(df) or parse_date(df)
            if dt:
                qs = qs.filter(created_at__gte=dt)
        qs = qs.order_by("-created_at")
        paginator = AdminPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        return paginator.get_paginated_response([_serialize_log(l) for l in page])


# =============================================================================
# SUBSCRIPTION PLAN LISTESİ (admin'in plan seçebilmesi için)
# =============================================================================

class AdminPlanListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        plans = SubscriptionPlan.objects.all().order_by("plan_tier", "interval")
        return Response([
            {
                "id": p.id,
                "name": p.name,
                "price": str(p.price),
                "interval": p.interval,
                "plan_type": p.plan_type,
                "plan_tier": p.plan_tier,
                "duration_days": p.duration_days,
                "is_active": p.is_active,
            }
            for p in plans
        ])
