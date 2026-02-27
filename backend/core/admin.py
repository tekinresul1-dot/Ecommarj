"""
Django Admin registrations for all core models.
"""

from django.contrib import admin
from .models import (
    TrendyolIntegration,
    Product,
    ProductVariant,
    Order,
    OrderItem,
    Return,
    Expense,
    SyncJob,
)


# ---------------------------------------------------------------------------
# Trendyol Integration
# ---------------------------------------------------------------------------

@admin.register(TrendyolIntegration)
class TrendyolIntegrationAdmin(admin.ModelAdmin):
    list_display = ("store_name", "supplier_id", "user", "status", "last_sync_at", "created_at")
    list_filter = ("status",)
    search_fields = ("store_name", "supplier_id")
    readonly_fields = ("created_at", "updated_at")


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ("barcode", "sku", "size", "color", "sale_price", "list_price", "quantity")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "title_short", "barcode", "sale_price", "cost_price",
        "commission_rate", "quantity", "is_active",
    )
    list_filter = ("is_active", "integration")
    search_fields = ("title", "barcode", "product_code", "trendyol_id")
    readonly_fields = ("created_at", "updated_at")
    inlines = [ProductVariantInline]

    @admin.display(description="Ürün Adı")
    def title_short(self, obj):
        return obj.title[:80] if obj.title else "–"


# ---------------------------------------------------------------------------
# Product Variant (standalone)
# ---------------------------------------------------------------------------

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("barcode", "product", "size", "color", "sale_price", "quantity")
    search_fields = ("barcode", "sku")
    readonly_fields = ("created_at", "updated_at")


# ---------------------------------------------------------------------------
# Order
# ---------------------------------------------------------------------------

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = (
        "barcode", "product_name", "quantity", "sale_price",
        "commission_amount", "cargo_cost", "net_profit",
    )
    readonly_fields = ("net_profit",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number", "status", "order_date", "total_price",
        "total_commission", "cargo_cost", "net_profit", "profit_margin",
    )
    list_filter = ("status", "integration")
    search_fields = ("order_number", "trendyol_order_id")
    readonly_fields = ("created_at", "updated_at")
    inlines = [OrderItemInline]
    date_hierarchy = "order_date"


# ---------------------------------------------------------------------------
# Order Item (standalone)
# ---------------------------------------------------------------------------

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "product_name_short", "barcode", "quantity", "sale_price",
        "commission_amount", "net_profit",
    )
    search_fields = ("barcode", "product_name")
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Ürün")
    def product_name_short(self, obj):
        return obj.product_name[:60] if obj.product_name else "–"


# ---------------------------------------------------------------------------
# Return
# ---------------------------------------------------------------------------

@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = (
        "trendyol_return_id", "product_name_short", "quantity",
        "refund_amount", "status", "return_date",
    )
    list_filter = ("status", "integration")
    search_fields = ("trendyol_return_id", "barcode", "product_name")
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Ürün")
    def product_name_short(self, obj):
        return obj.product_name[:60] if obj.product_name else "–"


# ---------------------------------------------------------------------------
# Expense
# ---------------------------------------------------------------------------

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "amount", "date", "is_recurring")
    list_filter = ("category", "is_recurring", "integration")
    search_fields = ("title",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "date"


# ---------------------------------------------------------------------------
# Sync Job
# ---------------------------------------------------------------------------

@admin.register(SyncJob)
class SyncJobAdmin(admin.ModelAdmin):
    list_display = (
        "job_type", "status", "records_processed",
        "started_at", "finished_at", "integration",
    )
    list_filter = ("job_type", "status", "integration")
    readonly_fields = ("created_at", "updated_at")


# ---------------------------------------------------------------------------
# Admin site customisation
# ---------------------------------------------------------------------------

admin.site.site_header = "Ecompro Yönetim Paneli"
admin.site.site_title = "Ecompro Admin"
admin.site.index_title = "Kontrol Paneli"
