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
    CargoCompany,
    CargoRate,
    SellerCargoSettings,
    CargoRateImportHistory,
    SubscriptionPlan,
    UserSubscription,
    Payment,
    AccessCode,
    LoginAttempt,
    AccountLockout,
    AdminLog,
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
    fields = (
        "organization", "phone", "company", "onboarding_status", "static_otp_code",
        "is_suspended", "suspension_reason", "admin_note", "is_priority", "is_risky",
        "admin_override", "email_verified", "google_connected", "trendyol_store_count",
        "last_login_ip",
    )
    readonly_fields = ("last_login_ip",)


class UserSubscriptionInline(admin.StackedInline):
    model = UserSubscription
    can_delete = False
    fk_name = "user"
    verbose_name_plural = "Abonelik"
    fields = (
        "plan", "status", "admin_override", "admin_override_reason",
        "start_date", "end_date", "trial_end_date", "current_period_end", "notes",
    )
    extra = 0


class PaymentInline(admin.TabularInline):
    model = Payment
    fk_name = "user"
    extra = 0
    fields = ("amount", "status", "plan", "payment_date", "due_date", "added_by_admin", "merchant_oid")
    readonly_fields = ("merchant_oid",)
    show_change_link = True


class AccessCodeInline(admin.TabularInline):
    model = AccessCode
    fk_name = "user"
    extra = 0
    fields = ("code", "is_active", "is_lifetime", "expires_at", "max_uses", "use_count", "last_used_at")
    readonly_fields = ("code", "use_count", "last_used_at")
    show_change_link = True


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, UserSubscriptionInline, PaymentInline, AccessCodeInline)
    list_display = ("email", "full_name", "is_active", "is_staff", "subscription_status", "date_joined", "last_login", "has_marketplace")
    list_editable = ("is_active",)
    list_filter = ("is_active", "is_staff", "date_joined", "profile__is_suspended")
    search_fields = ("email", "first_name", "last_name", "profile__company")
    ordering = ("-date_joined",)
    actions = ("admin_activate_users", "admin_deactivate_users", "admin_suspend_users")

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or "—"
    full_name.short_description = "Ad Soyad"

    def subscription_status(self, obj):
        try:
            return obj.usersubscription.status
        except Exception:
            return "—"
    subscription_status.short_description = "Abonelik"

    # Custom actions ---------------------------------------------------------

    def admin_activate_users(self, request, queryset):
        count = queryset.update(is_active=True)
        UserProfile.objects.filter(user__in=queryset).update(is_suspended=False, suspension_reason="")
        self.message_user(request, f"{count} kullanıcı aktifleştirildi.")
    admin_activate_users.short_description = "Seçilenleri AKTİFLEŞTİR"

    def admin_deactivate_users(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} kullanıcı pasifleştirildi.")
    admin_deactivate_users.short_description = "Seçilenleri PASİFLEŞTİR"

    def admin_suspend_users(self, request, queryset):
        for user in queryset:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.is_suspended = True
            profile.suspension_reason = "Admin paneli toplu işlemi"
            profile.save(update_fields=["is_suspended", "suspension_reason"])
        self.message_user(request, f"{queryset.count()} kullanıcı askıya alındı.")
    admin_suspend_users.short_description = "Seçilenleri ASKIYA AL"

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


@admin.register(CargoCompany)
class CargoCompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active", "created_at")
    list_editable = ("is_active",)
    search_fields = ("name", "code")
    ordering = ("name",)


@admin.register(CargoRate)
class CargoRateAdmin(admin.ModelAdmin):
    list_display = ("organization", "cargo_company", "desi_kg", "price", "is_active", "updated_at")
    list_editable = ("price", "is_active")
    list_filter = ("cargo_company", "organization", "is_active")
    search_fields = ("organization__name", "cargo_company__name")
    ordering = ("organization", "cargo_company", "desi_kg")


@admin.register(SellerCargoSettings)
class SellerCargoSettingsAdmin(admin.ModelAdmin):
    list_display = ("organization", "default_cargo_company", "use_order_cargo_company", "apply_barem_0_199", "apply_barem_200_349")
    list_filter = ("apply_barem_0_199", "apply_barem_200_349")
    search_fields = ("organization__name",)


@admin.register(CargoRateImportHistory)
class CargoRateImportHistoryAdmin(admin.ModelAdmin):
    list_display = ("organization", "file_name", "imported_rows", "failed_rows", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("organization__name", "file_name")
    readonly_fields = ("error_message", "created_at")
    ordering = ("-created_at",)


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


# ===========================================================================
# YÖNETİCİ PANELİ — Access Code / Login Attempt / Lockout / Admin Log
# ===========================================================================

@admin.register(AccessCode)
class AccessCodeAdmin(admin.ModelAdmin):
    list_display = ("user", "code_masked", "is_active", "is_lifetime", "use_count", "expires_at", "last_used_at", "created_at")
    list_filter = ("is_active", "is_lifetime")
    search_fields = ("user__email", "code")
    readonly_fields = ("code", "use_count", "last_used_at", "created_at")
    actions = ("deactivate_codes",)

    def code_masked(self, obj):
        if obj.code and len(obj.code) > 4:
            return obj.code[:2] + "*" * (len(obj.code) - 4) + obj.code[-2:]
        return obj.code or "—"
    code_masked.short_description = "Kod"

    def deactivate_codes(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} kod pasife alındı.")
    deactivate_codes.short_description = "Seçili kodları PASİFE ALC"


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "ip_address", "success", "attempt_type", "attempted_at")
    list_filter = ("success", "attempt_type")
    search_fields = ("user__email", "ip_address")
    readonly_fields = ("user", "ip_address", "success", "attempt_type", "attempted_at")
    ordering = ("-attempted_at",)

    def has_add_permission(self, request):
        return False


@admin.register(AccountLockout)
class AccountLockoutAdmin(admin.ModelAdmin):
    list_display = ("user", "locked_until", "reason", "failed_attempts", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__email", "reason")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


@admin.register(AdminLog)
class AdminLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "admin", "target_user", "action_type", "short_desc", "ip_address")
    list_filter = ("action_type", "created_at")
    search_fields = ("admin__email", "target_user__email", "description")
    readonly_fields = ("admin", "target_user", "action_type", "description", "old_value", "new_value", "created_at", "ip_address")
    ordering = ("-created_at",)

    def short_desc(self, obj):
        return (obj.description or "")[:80]
    short_desc.short_description = "Açıklama"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
