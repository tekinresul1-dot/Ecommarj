from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Organization,
    UserProfile,
    MarketplaceAccount,
    Product,
    ProductVariant,
    Order,
    OrderItem,
    FinancialTransaction,
    CostRule,
    ExchangeRate,
    ProfitSnapshot,
    SyncJob,
    SyncCheckpoint,
    SyncAuditLog,
    ReturnClaim,
)

User = get_user_model()

# Varsayılan User admin kaydını kaldır
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


# ---------------------------------------------------------------------------
# User Admin
# ---------------------------------------------------------------------------

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profil"
    fields = ("organization", "phone", "company", "onboarding_status", "static_otp_code")


class MarketplaceAccountInline(admin.TabularInline):
    model = MarketplaceAccount
    extra = 0
    fields = ("store_name", "channel", "seller_id", "is_active", "last_sync_at")
    readonly_fields = ("last_sync_at",)
    show_change_link = True


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ("email", "is_active", "is_staff", "date_joined", "last_login", "has_marketplace_account", "static_otp_code_display")
    list_filter = ("is_active", "is_staff", "date_joined")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Kişisel Bilgiler", {"fields": ("first_name", "last_name")}),
        ("İzinler", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Önemli Tarihler", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2"),
        }),
    )

    def has_marketplace_account(self, obj):
        try:
            return obj.profile.organization.marketplace_accounts.filter(is_active=True).exists()
        except Exception:
            return False
    has_marketplace_account.short_description = "Pazaryeri Hesabı"
    has_marketplace_account.boolean = True

    def static_otp_code_display(self, obj):
        try:
            return obj.profile.static_otp_code or "-"
        except Exception:
            return "-"
    static_otp_code_display.short_description = "Sabit OTP"


# ---------------------------------------------------------------------------
# Organization
# ---------------------------------------------------------------------------

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)
    inlines = [MarketplaceAccountInline]


# ---------------------------------------------------------------------------
# UserProfile
# ---------------------------------------------------------------------------

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "phone", "company", "static_otp_code")
    search_fields = ("user__email", "user__first_name", "user__last_name", "company")
    list_editable = ("static_otp_code",)


# ---------------------------------------------------------------------------
# MarketplaceAccount
# ---------------------------------------------------------------------------

@admin.register(MarketplaceAccount)
class MarketplaceAccountAdmin(admin.ModelAdmin):
    list_display = ("store_name", "organization", "channel", "seller_id", "api_key_preview", "is_active", "last_sync_at", "created_at")
    list_filter = ("channel", "is_active", "organization")
    search_fields = ("store_name", "seller_id", "organization__name")
    list_editable = ("seller_id", "is_active")
    readonly_fields = ("last_sync_at", "created_at", "updated_at")

    def api_key_preview(self, obj):
        if obj.api_key:
            return f"{obj.api_key[:8]}…"
        return "-"
    api_key_preview.short_description = "API Key"


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "marketplace_sku", "organization", "marketplace_account", "is_active")
    list_filter = ("is_active", "organization")
    search_fields = ("title", "marketplace_sku", "barcode")
    inlines = [ProductVariantInline]


# ---------------------------------------------------------------------------
# Order
# ---------------------------------------------------------------------------

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("marketplace_order_id", "package_id", "organization", "channel", "order_date", "status", "last_synced_at")
    list_filter = ("status", "channel", "organization")
    search_fields = ("marketplace_order_id", "package_id", "order_number")
    readonly_fields = ("raw_payload_hash", "previous_status", "status_changed_at")
    inlines = [OrderItemInline]


# ---------------------------------------------------------------------------
# Financial
# ---------------------------------------------------------------------------

@admin.register(FinancialTransaction)
class FinancialTransactionAdmin(admin.ModelAdmin):
    list_display = ("transaction_type", "amount", "currency", "organization", "occurred_at")
    list_filter = ("transaction_type", "currency", "organization")


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


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Returns
# ---------------------------------------------------------------------------

@admin.register(ReturnClaim)
class ReturnClaimAdmin(admin.ModelAdmin):
    list_display = ("claim_id", "order_number", "claim_status", "refund_amount", "claim_date")
    list_filter = ("claim_status",)
    search_fields = ("claim_id", "order_number")
