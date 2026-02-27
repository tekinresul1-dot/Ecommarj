"""
Ecompro Core Models
===================
All domain models for Trendyol seller profitability tracking.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class TimestampedModel(models.Model):
    """Mixin that adds created / updated timestamps to every model."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ---------------------------------------------------------------------------
# User Profile (auth extension)
# ---------------------------------------------------------------------------

class UserProfile(TimestampedModel):
    """Kullanıcı profil bilgileri — kayıt sırasında opsiyonel alanlar."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    phone = models.CharField("Telefon", max_length=20, blank=True, default="")
    company = models.CharField("Şirket Adı", max_length=200, blank=True, default="")

    class Meta:
        verbose_name = "Kullanıcı Profili"
        verbose_name_plural = "Kullanıcı Profilleri"

    def __str__(self):
        return f"{self.user.get_full_name()} profili"


# ---------------------------------------------------------------------------
# 1. Trendyol Integration
# ---------------------------------------------------------------------------

class TrendyolIntegration(TimestampedModel):
    """
    Bir satıcının Trendyol API kimlik bilgilerini tutar.
    Her kullanıcı birden fazla mağaza bağlayabilir.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Aktif"
        INACTIVE = "inactive", "Pasif"
        ERROR = "error", "Hatalı"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="integrations",
    )
    store_name = models.CharField("Mağaza Adı", max_length=255)
    supplier_id = models.CharField("Supplier ID", max_length=100)
    api_key = models.CharField("API Key", max_length=255)
    api_secret = models.CharField("API Secret", max_length=255)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    last_sync_at = models.DateTimeField("Son Senkronizasyon", null=True, blank=True)

    class Meta:
        verbose_name = "Trendyol Entegrasyonu"
        verbose_name_plural = "Trendyol Entegrasyonları"
        unique_together = ("user", "supplier_id")

    def __str__(self):
        return f"{self.store_name} ({self.supplier_id})"


# ---------------------------------------------------------------------------
# 2. Product
# ---------------------------------------------------------------------------

class Product(TimestampedModel):
    """
    Trendyol'dan çekilen ürün bilgisi.
    """
    integration = models.ForeignKey(
        TrendyolIntegration,
        on_delete=models.CASCADE,
        related_name="products",
    )
    trendyol_id = models.CharField("Trendyol Ürün ID", max_length=100, db_index=True)
    barcode = models.CharField("Barkod", max_length=100, blank=True, default="")
    title = models.CharField("Ürün Adı", max_length=500)
    product_code = models.CharField("Ürün Kodu (Model Kodu)", max_length=255, blank=True, default="")
    brand = models.CharField("Marka", max_length=255, blank=True, default="")
    category_name = models.CharField("Kategori", max_length=500, blank=True, default="")

    # Fiyat
    sale_price = models.DecimalField("Satış Fiyatı (TL)", max_digits=12, decimal_places=2, default=0)
    list_price = models.DecimalField("Liste Fiyatı (TL)", max_digits=12, decimal_places=2, default=0)

    # Maliyet (satıcı tarafından girilir)
    cost_price = models.DecimalField("Alış Maliyeti (TL)", max_digits=12, decimal_places=2, default=0)

    # Komisyon
    commission_rate = models.DecimalField(
        "Komisyon Oranı (%)", max_digits=5, decimal_places=2, default=0,
        help_text="Trendyol'un bu ürün kategorisi için uyguladığı komisyon oranı.",
    )

    # KDV
    vat_rate = models.DecimalField("KDV Oranı (%)", max_digits=5, decimal_places=2, default=20)

    # Stok
    quantity = models.PositiveIntegerField("Stok Adedi", default=0)

    image_url = models.URLField("Görsel URL", max_length=1000, blank=True, default="")
    is_active = models.BooleanField("Aktif mi?", default=True)

    raw_data = models.JSONField("Ham API Verisi", default=dict, blank=True)

    class Meta:
        verbose_name = "Ürün"
        verbose_name_plural = "Ürünler"
        unique_together = ("integration", "trendyol_id")

    def __str__(self):
        return f"{self.title[:80]} ({self.barcode})"


# ---------------------------------------------------------------------------
# 3. Product Variant
# ---------------------------------------------------------------------------

class ProductVariant(TimestampedModel):
    """
    Bir ürünün renk/beden gibi varyasyonları.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
    )
    barcode = models.CharField("Barkod", max_length=100, db_index=True)
    sku = models.CharField("SKU", max_length=255, blank=True, default="")
    size = models.CharField("Beden", max_length=50, blank=True, default="")
    color = models.CharField("Renk", max_length=100, blank=True, default="")
    sale_price = models.DecimalField("Satış Fiyatı (TL)", max_digits=12, decimal_places=2, default=0)
    list_price = models.DecimalField("Liste Fiyatı (TL)", max_digits=12, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField("Stok", default=0)

    class Meta:
        verbose_name = "Ürün Varyantı"
        verbose_name_plural = "Ürün Varyantları"
        unique_together = ("product", "barcode")

    def __str__(self):
        parts = [self.barcode]
        if self.size:
            parts.append(self.size)
        if self.color:
            parts.append(self.color)
        return " / ".join(parts)


# ---------------------------------------------------------------------------
# 4. Order
# ---------------------------------------------------------------------------

class Order(TimestampedModel):
    """
    Trendyol'dan çekilen sipariş başlığı.
    """

    class Status(models.TextChoices):
        CREATED = "Created", "Oluşturuldu"
        PICKING = "Picking", "Hazırlanıyor"
        SHIPPED = "Shipped", "Kargoya Verildi"
        DELIVERED = "Delivered", "Teslim Edildi"
        CANCELLED = "Cancelled", "İptal"
        RETURNED = "Returned", "İade"
        UNKNOWN = "Unknown", "Bilinmiyor"

    integration = models.ForeignKey(
        TrendyolIntegration,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    trendyol_order_id = models.CharField("Trendyol Sipariş No", max_length=100, db_index=True)
    order_number = models.CharField("Sipariş Numarası", max_length=100, blank=True, default="")
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.UNKNOWN)
    order_date = models.DateTimeField("Sipariş Tarihi", null=True, blank=True)

    # Tutarlar
    total_price = models.DecimalField("Toplam Tutar (TL)", max_digits=12, decimal_places=2, default=0)
    total_discount = models.DecimalField("Toplam İndirim (TL)", max_digits=12, decimal_places=2, default=0)

    # Kargo
    cargo_company = models.CharField("Kargo Firması", max_length=100, blank=True, default="")
    cargo_tracking_number = models.CharField("Kargo Takip No", max_length=100, blank=True, default="")
    cargo_cost = models.DecimalField(
        "Kargo Maliyeti (TL)", max_digits=10, decimal_places=2, default=0,
        help_text="Satıcıdan kesilen kargo ücreti (KDV dahil).",
    )

    # Karlılık (hesaplanan)
    total_cost = models.DecimalField("Toplam Maliyet (TL)", max_digits=12, decimal_places=2, default=0)
    total_commission = models.DecimalField("Toplam Komisyon (TL)", max_digits=12, decimal_places=2, default=0)
    net_profit = models.DecimalField("Net Kar (TL)", max_digits=12, decimal_places=2, default=0)
    profit_margin = models.DecimalField("Kar Marjı (%)", max_digits=6, decimal_places=2, default=0)

    raw_data = models.JSONField("Ham API Verisi", default=dict, blank=True)

    class Meta:
        verbose_name = "Sipariş"
        verbose_name_plural = "Siparişler"
        unique_together = ("integration", "trendyol_order_id")
        ordering = ["-order_date"]

    def __str__(self):
        return f"#{self.order_number} – {self.get_status_display()}"


# ---------------------------------------------------------------------------
# 5. Order Item
# ---------------------------------------------------------------------------

class OrderItem(TimestampedModel):
    """
    Sipariş kalemi – her satır bir ürün/varyant.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )
    trendyol_line_id = models.CharField("Trendyol Satır ID", max_length=100, blank=True, default="")
    barcode = models.CharField("Barkod", max_length=100, blank=True, default="")
    product_name = models.CharField("Ürün Adı", max_length=500, blank=True, default="")
    quantity = models.PositiveIntegerField("Adet", default=1)

    # Fiyatlar
    sale_price = models.DecimalField("Satış Fiyatı (TL)", max_digits=12, decimal_places=2, default=0)
    unit_price = models.DecimalField("Birim Fiyat (TL)", max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField("İndirim (TL)", max_digits=12, decimal_places=2, default=0)

    # Maliyetler – sipariş bazında hesaplanır
    cost_price = models.DecimalField("Alış Maliyeti (TL)", max_digits=12, decimal_places=2, default=0)
    commission_rate = models.DecimalField("Komisyon Oranı (%)", max_digits=5, decimal_places=2, default=0)
    commission_amount = models.DecimalField("Komisyon Tutarı (TL)", max_digits=12, decimal_places=2, default=0)
    cargo_cost = models.DecimalField("Kargo Maliyeti (TL)", max_digits=10, decimal_places=2, default=0)
    vat_amount = models.DecimalField("KDV Tutarı (TL)", max_digits=12, decimal_places=2, default=0)
    stopaj_amount = models.DecimalField("Stopaj (TL)", max_digits=12, decimal_places=2, default=0)

    # Hesaplanan
    net_profit = models.DecimalField("Net Kar (TL)", max_digits=12, decimal_places=2, default=0)
    profit_margin = models.DecimalField("Kar Marjı (%)", max_digits=6, decimal_places=2, default=0)

    raw_data = models.JSONField("Ham API Verisi", default=dict, blank=True)

    class Meta:
        verbose_name = "Sipariş Kalemi"
        verbose_name_plural = "Sipariş Kalemleri"

    def __str__(self):
        return f"{self.product_name[:60]} x{self.quantity}"


# ---------------------------------------------------------------------------
# 6. Return
# ---------------------------------------------------------------------------

class Return(TimestampedModel):
    """
    İade kayıtları.
    """

    class Status(models.TextChoices):
        CREATED = "Created", "Oluşturuldu"
        ACCEPTED = "Accepted", "Kabul Edildi"
        REJECTED = "Rejected", "Reddedildi"
        RESOLVED = "Resolved", "Çözümlendi"

    integration = models.ForeignKey(
        TrendyolIntegration,
        on_delete=models.CASCADE,
        related_name="returns",
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="returns",
        null=True,
        blank=True,
    )
    trendyol_return_id = models.CharField("Trendyol İade ID", max_length=100, db_index=True)
    barcode = models.CharField("Barkod", max_length=100, blank=True, default="")
    product_name = models.CharField("Ürün Adı", max_length=500, blank=True, default="")
    quantity = models.PositiveIntegerField("Adet", default=1)
    reason = models.TextField("İade Nedeni", blank=True, default="")
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.CREATED)
    return_date = models.DateTimeField("İade Tarihi", null=True, blank=True)
    refund_amount = models.DecimalField("İade Tutarı (TL)", max_digits=12, decimal_places=2, default=0)

    raw_data = models.JSONField("Ham API Verisi", default=dict, blank=True)

    class Meta:
        verbose_name = "İade"
        verbose_name_plural = "İadeler"
        ordering = ["-return_date"]

    def __str__(self):
        return f"İade #{self.trendyol_return_id} – {self.product_name[:40]}"


# ---------------------------------------------------------------------------
# 7. Expense (Ek Giderler)
# ---------------------------------------------------------------------------

class Expense(TimestampedModel):
    """
    Satıcının elle girdiği ek giderler: paketleme, depo kirası,
    personel maaşı, reklam harcaması vb.
    """

    class Category(models.TextChoices):
        PACKAGING = "packaging", "Paketleme"
        WAREHOUSE = "warehouse", "Depo / Kira"
        SALARY = "salary", "Personel"
        ADVERTISING = "advertising", "Reklam / Pazarlama"
        SHIPPING_EXTRA = "shipping_extra", "Ek Kargo"
        TAX = "tax", "Vergi / Muhasebe"
        OTHER = "other", "Diğer"

    integration = models.ForeignKey(
        TrendyolIntegration,
        on_delete=models.CASCADE,
        related_name="expenses",
    )
    category = models.CharField(
        max_length=30,
        choices=Category.choices,
        default=Category.OTHER,
    )
    title = models.CharField("Açıklama", max_length=255)
    amount = models.DecimalField("Tutar (TL)", max_digits=12, decimal_places=2)
    date = models.DateField("Tarih", default=timezone.now)
    is_recurring = models.BooleanField("Tekrarlayan mı?", default=False)
    notes = models.TextField("Notlar", blank=True, default="")

    class Meta:
        verbose_name = "Gider"
        verbose_name_plural = "Giderler"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.title} – ₺{self.amount}"


# ---------------------------------------------------------------------------
# 8. Sync Job
# ---------------------------------------------------------------------------

class SyncJob(TimestampedModel):
    """
    Her senkronizasyon işleminin kaydı.
    Hangi veri türü çekildi, ne kadar sürdü, hata var mı?
    """

    class JobType(models.TextChoices):
        PRODUCTS = "products", "Ürünler"
        ORDERS = "orders", "Siparişler"
        RETURNS = "returns", "İadeler"
        SETTLEMENTS = "settlements", "Ödemeler"

    class Status(models.TextChoices):
        PENDING = "pending", "Bekliyor"
        RUNNING = "running", "Çalışıyor"
        SUCCESS = "success", "Başarılı"
        FAILED = "failed", "Başarısız"

    integration = models.ForeignKey(
        TrendyolIntegration,
        on_delete=models.CASCADE,
        related_name="sync_jobs",
    )
    job_type = models.CharField(max_length=30, choices=JobType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    started_at = models.DateTimeField("Başlangıç", null=True, blank=True)
    finished_at = models.DateTimeField("Bitiş", null=True, blank=True)
    records_processed = models.PositiveIntegerField("İşlenen Kayıt", default=0)
    error_message = models.TextField("Hata Mesajı", blank=True, default="")

    class Meta:
        verbose_name = "Senkronizasyon İşi"
        verbose_name_plural = "Senkronizasyon İşleri"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_job_type_display()} – {self.get_status_display()} ({self.created_at:%Y-%m-%d %H:%M})"
