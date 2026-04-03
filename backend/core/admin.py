from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Organization,
    UserProfile,
    MarketplaceAccount,
    CostRule,
    ExchangeRate,
    ProfitSnapshot,
    SyncJob,
    SyncCheckpoint,
    SyncAuditLog,
    CargoPrice,
    SubscriptionPlan,
    UserSubscription,
    Payment,
)

User = get_user_model()

# Varsayılan User admin kaydını kaldır
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


# ===========================================================================
# AUTHENTICATION — User
# ===========================================================================

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profil"
    fields = ("organization", "phone", "company", "onboarding_status", "static_otp_code")


class UserSubscriptionInline(admin.StackedInline):
    model = UserSubscription
    can_delete = False
    verbose_name_plural = "Abonelik"
    fields = ("plan", "status", "admin_override", "admin_override_reason", "trial_end", "current_period_end")
    extra = 0


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, UserSubscriptionInline)
    list_display = ("email", "is_active", "is_staff", "date_joined", "last_login", "has_marketplace", "static_otp_code_display")
    list_editable = ("is_active",)
    list_filter = ("is_active", "is_staff", "date_joined")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-date_joined",)

    fieldsets = (
        ("Giriş Bilgileri", {"fields": ("email", "password")}),
        ("OTP Ayarı", {
            "fields": ("static_otp_code_field",),
            "description": "Dolu ise e-posta gönderilmez, bu sabit kod kullanılır.",
        }),
        ("Kişisel Bilgiler", {"fields": ("first_name", "last_name")}),
        ("İzinler", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Tarihler", {"fields": ("last_login", "date_joined")}),
    )
    readonly_fields = ("last_login", "date_joined", "static_otp_code_field")
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2"),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        return ("last_login", "date_joined")

    def static_otp_code_field(self, obj):
        try:
            return obj.profile.static_otp_code or "—"
        except Exception:
            return "—"
    static_otp_code_field.short_description = "Sabit OTP Kodu (Profil'den düzenleyin)"

    def has_marketplace(self, obj):
        try:
            return obj.profile.organization.marketplace_accounts.filter(is_active=True).exists()
        except Exception:
            return False
    has_marketplace.short_description = "Pazaryeri"
    has_marketplace.boolean = True

    def static_otp_code_display(self, obj):
        try:
            return obj.profile.static_otp_code or "—"
        except Exception:
            return "—"
    static_otp_code_display.short_description = "Sabit OTP"


# ===========================================================================
# Organization & UserProfile
# ===========================================================================

class MarketplaceAccountInline(admin.TabularInline):
    model = MarketplaceAccount
    extra = 0
    fields = ("store_name", "channel", "seller_id", "is_active", "last_sync_at")
    readonly_fields = ("last_sync_at",)
    show_change_link = True


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)
    inlines = [MarketplaceAccountInline]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "phone", "company", "static_otp_code")
    search_fields = ("user__email", "user__first_name", "user__last_name", "company")
    list_editable = ("static_otp_code",)


# ===========================================================================
# MAĞAZA YÖNETİMİ — MarketplaceAccount
# ===========================================================================

@admin.register(MarketplaceAccount)
class MarketplaceAccountAdmin(admin.ModelAdmin):
    list_display = ("user_email", "seller_id", "api_key_preview", "is_active", "created_at")
    list_editable = ("is_active",)
    list_filter = ("channel", "is_active")
    search_fields = ("organization__users__user__email", "seller_id", "store_name")
    readonly_fields = ("last_sync_at", "created_at", "updated_at")

    def user_email(self, obj):
        try:
            profile = obj.organization.users.select_related("user").first()
            return profile.user.email if profile else obj.organization.name
        except Exception:
            return obj.organization.name
    user_email.short_description = "Kullanıcı E-postası"

    def api_key_preview(self, obj):
        if obj.api_key:
            return f"{obj.api_key[:8]}..."
        return "—"
    api_key_preview.short_description = "API Key"


# ===========================================================================
# ABONELİK
# ===========================================================================

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "interval", "is_active")
    list_editable = ("price", "is_active")


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user_email", "plan", "status", "admin_override", "trial_end", "current_period_end", "updated_at")
    list_editable = ("status", "admin_override")
    list_filter = ("status", "admin_override", "plan")
    search_fields = ("user__email",)
    fields = ("user", "plan", "status", "admin_override", "admin_override_reason", "trial_end", "current_period_end")

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "Kullanıcı"


# ===========================================================================
# ÖDEMELER
# ===========================================================================

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("user_email", "plan", "amount", "status", "merchant_oid", "created_at")
    list_filter = ("status",)
    search_fields = ("user__email", "merchant_oid")
    readonly_fields = ("merchant_oid", "paytr_token", "paytr_response", "created_at", "updated_at")

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "Kullanıcı"


# ===========================================================================
# FİYATLANDIRMA — CargoPrice
# ===========================================================================

@admin.register(CargoPrice)
class CargoPriceAdmin(admin.ModelAdmin):
    list_display = ("desi", "price", "cargo_provider", "is_active", "updated_at")
    list_editable = ("price", "is_active")
    ordering = ("desi",)


# ===========================================================================
# FİNANSAL (sadece genel tablolar)
# ===========================================================================

@admin.register(CostRule)
class CostRuleAdmin(admin.ModelAdmin):
    list_display = ("organization", "packaging_cost", "handling_cost", "extra_fees")


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ("date", "from_currency", "to_currency", "rate")
    list_filter = ("from_currency", "to_currency")
    date_hierarchy = "date"


@admin.register(ProfitSnapshot)
class ProfitSnapshotAdmin(admin.ModelAdmin):
    list_display = ("date", "organization", "channel", "profit_amount", "profit_margin")
    list_filter = ("channel", "organization")
    date_hierarchy = "date"


# ===========================================================================
# SİSTEM — Sync
# ===========================================================================

@admin.register(SyncJob)
class SyncJobAdmin(admin.ModelAdmin):
    list_display = ("job_type", "status", "organization", "marketplace_account", "started_at")
    list_filter = ("job_type", "status")


@admin.register(SyncCheckpoint)
class SyncCheckpointAdmin(admin.ModelAdmin):
    list_display = ("marketplace_account", "sync_type", "last_successful_sync_at", "last_fetched_modified_date")
    list_filter = ("sync_type",)


@admin.register(SyncAuditLog)
class SyncAuditLogAdmin(admin.ModelAdmin):
    list_display = ("sync_type", "sync_mode", "started_at", "success", "total_fetched", "inserted", "updated", "skipped", "failed", "duration_seconds")
    list_filter = ("sync_type", "sync_mode", "success")
    readonly_fields = ("error_message",)
    ordering = ("-started_at",)
