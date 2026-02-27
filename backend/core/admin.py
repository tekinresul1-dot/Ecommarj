"""
Django admin definitions for Ecompro core models.
"""

from django.contrib import admin
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
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "phone", "company")
    search_fields = ("user__email", "user__first_name", "user__last_name", "company")


@admin.register(MarketplaceAccount)
class MarketplaceAccountAdmin(admin.ModelAdmin):
    list_display = ("store_name", "organization", "channel", "seller_id", "is_active", "last_sync_at")
    list_filter = ("channel", "is_active", "organization")
    search_fields = ("store_name", "seller_id")


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "marketplace_sku", "organization", "marketplace_account", "is_active")
    list_filter = ("is_active", "organization")
    search_fields = ("title", "marketplace_sku", "barcode")
    inlines = [ProductVariantInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("marketplace_order_id", "organization", "channel", "order_date", "status")
    list_filter = ("status", "channel", "organization")
    search_fields = ("marketplace_order_id",)
    inlines = [OrderItemInline]


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


@admin.register(SyncJob)
class SyncJobAdmin(admin.ModelAdmin):
    list_display = ("job_type", "status", "organization", "marketplace_account", "started_at")
    list_filter = ("job_type", "status")
