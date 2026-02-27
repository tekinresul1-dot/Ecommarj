"""
Ecompro Core Models
===================
All domain models for multi-tenant e-commerce profitability tracking.
"""

from django.db import models
from django.conf import settings


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
# Multi-Tenant & User Profile
# ---------------------------------------------------------------------------

class Organization(TimestampedModel):
    """
    E-Ticaret firmasını (Tenant) temsil eder.
    Tüm kârlılık verileri bu modele bağlıdır (İzolasyon).
    """
    name = models.CharField("Firma/Organizasyon Adı", max_length=255)

    class Meta:
        verbose_name = "Organizasyon"
        verbose_name_plural = "Organizasyonlar"

    def __str__(self):
        return self.name


class UserProfile(TimestampedModel):
    """Kullanıcı profil bilgileri — kayıt sırasında opsiyonel alanlar."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users"
    )
    phone = models.CharField("Telefon", max_length=20, blank=True, default="")
    company = models.CharField("Şirket Adı", max_length=200, blank=True, default="")

    class Meta:
        verbose_name = "Kullanıcı Profili"
        verbose_name_plural = "Kullanıcı Profilleri"

    def __str__(self):
        return f"{self.user.get_full_name()} profili"


# ---------------------------------------------------------------------------
# 1. Marketplace Account
# ---------------------------------------------------------------------------

class MarketplaceAccount(TimestampedModel):
    """
    Bir organizasyonun Pazaryeri (Trendyol, vb.) API kimlik bilgilerini tutar.
    """
    class Channel(models.TextChoices):
        TRENDYOL = "trendyol", "Trendyol"
        MICRO_EXPORT = "micro_export", "Trendyol Mikro İhracat"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="marketplace_accounts")
    channel = models.CharField("Kanal", max_length=30, choices=Channel.choices, default=Channel.TRENDYOL)
    store_name = models.CharField("Mağaza Adı", max_length=255)
    seller_id = models.CharField("Satıcı / Tedarikçi ID", max_length=100)
    api_key = models.CharField("API Key", max_length=255, blank=True, default="")
    api_secret = models.CharField("API Secret", max_length=255, blank=True, default="")
    is_active = models.BooleanField("Aktif mi?", default=True)
    last_sync_at = models.DateTimeField("Son Senkronizasyon", null=True, blank=True)

    class Meta:
        verbose_name = "Pazaryeri Hesabı"
        verbose_name_plural = "Pazaryeri Hesapları"
        unique_together = ("organization", "channel", "seller_id")

    def __str__(self):
        return f"{self.store_name} ({self.get_channel_display()})"


# ---------------------------------------------------------------------------
# 2. Product & Variant
# ---------------------------------------------------------------------------

class Product(TimestampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="products")
    marketplace_account = models.ForeignKey(MarketplaceAccount, on_delete=models.CASCADE, related_name="products")
    marketplace_sku = models.CharField("Pazaryeri Ürün Kodu", max_length=100, db_index=True)
    barcode = models.CharField("Barkod", max_length=100, blank=True, default="")
    title = models.CharField("Ürün Adı", max_length=500)
    category_name = models.CharField("Kategori", max_length=500, blank=True, default="")
    image_url = models.URLField("Görsel URL", max_length=1000, blank=True, default="")
    is_active = models.BooleanField("Aktif mi?", default=True)

    class Meta:
        verbose_name = "Ürün"
        verbose_name_plural = "Ürünler"

    def __str__(self):
        return self.title[:80]

class ProductVariant(TimestampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    barcode = models.CharField("Barkod", max_length=100, db_index=True)
    marketplace_sku = models.CharField("SKU / Varyant Kodu", max_length=255, blank=True, default="")
    title = models.CharField("Varyant Adı", max_length=500, blank=True, default="")

    class Meta:
        verbose_name = "Ürün Varyantı"
        verbose_name_plural = "Ürün Varyantları"

    def __str__(self):
        return f"{self.product.title[:40]} - {self.barcode}"


# ---------------------------------------------------------------------------
# 3. Orders
# ---------------------------------------------------------------------------

class Order(TimestampedModel):
    class Status(models.TextChoices):
        CREATED = "Created", "Oluşturuldu"
        PICKING = "Picking", "Hazırlanıyor"
        SHIPPED = "Shipped", "Kargoya Verildi"
        DELIVERED = "Delivered", "Teslim Edildi"
        CANCELLED = "Cancelled", "İptal"
        RETURNED = "Returned", "İade"
    
    class Channel(models.TextChoices):
        TRENDYOL = "trendyol", "Trendyol"
        MICRO_EXPORT = "micro_export", "Trendyol Mikro İhracat"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="orders")
    marketplace_account = models.ForeignKey(MarketplaceAccount, on_delete=models.CASCADE, related_name="orders")
    marketplace_order_id = models.CharField("Pazaryeri Sipariş No", max_length=100, db_index=True)
    order_date = models.DateTimeField("Sipariş Tarihi")
    status = models.CharField(max_length=30, choices=Status.choices)
    channel = models.CharField(max_length=30, choices=Channel.choices, default=Channel.TRENDYOL)
    country_code = models.CharField("Ülke Kodu", max_length=5, default="TR") # TR, AZ, AE, vb.

    class Meta:
        verbose_name = "Sipariş"
        verbose_name_plural = "Siparişler"

    def __str__(self):
        return f"Order #{self.marketplace_order_id}"

class OrderItem(TimestampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    marketplace_line_id = models.CharField("Pazaryeri Satır ID", max_length=100, blank=True, default="")
    sku = models.CharField("SKU", max_length=100, blank=True, default="")
    quantity = models.PositiveIntegerField("Adet", default=1)
    status = models.CharField("Satır Durumu", max_length=30, blank=True, default="")
    
    sale_price_gross = models.DecimalField("Brüt Satış Fiyatı", max_digits=12, decimal_places=2, default=0)
    sale_price_net = models.DecimalField("Net Satış Fiyatı (İndirim Sonrası)", max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField("Uygulanan İndirim", max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Sipariş Kalemi"
        verbose_name_plural = "Sipariş Kalemleri"

    def __str__(self):
        return f"{self.sku} (x{self.quantity})"


# ---------------------------------------------------------------------------
# 4. Financial Transactions (Karlılık Motorunun Temeli)
# ---------------------------------------------------------------------------

class FinancialTransactionType(models.TextChoices):
    PRODUCT_COST = "PRODUCT_COST", "Ürün Maliyeti"
    COMMISSION = "COMMISSION", "Komisyon"
    SHIPPING_FEE = "SHIPPING_FEE", "Kargo Ücreti"
    SERVICE_FEE = "SERVICE_FEE", "Hizmet Bedeli"
    VAT_OUTPUT = "VAT_OUTPUT", "Satış KDV"
    VAT_INPUT = "VAT_INPUT", "Alış KDV (Maliyet KDV)"
    WITHHOLDING = "WITHHOLDING", "Stopaj"
    EARLY_PAYMENT = "EARLY_PAYMENT", "Erken Ödeme Kesintisi"
    PENALTY = "PENALTY", "Ceza"
    ADS_COST = "ADS_COST", "Reklam Harcaması"
    RETURN_LOSS = "RETURN_LOSS", "İade Zararı"
    OTHER = "OTHER", "Diğer"

class FinancialTransaction(TimestampedModel):
    """
    Sipariş satırı bazında tüm kâr/zarar kalemleri bu tabloda tutulur.
    Karlılık hesaplanırken bu kalemler aggregate edilir. Giderler negatif, kalemler eksi/artı tutar olarak yazılır.
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="transactions")
    order_item_ref = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name="transactions", null=True, blank=True)
    transaction_type = models.CharField(max_length=50, choices=FinancialTransactionType.choices)
    amount = models.DecimalField("Tutar", max_digits=12, decimal_places=2) # Mutlak değer olarak tutulabilir, hesaplamada type'a göre eklenir/çıkarılır
    currency = models.CharField("Para Birimi", max_length=10, default="TRY")
    occurred_at = models.DateTimeField("İşlem Tarihi")
    raw_payload = models.JSONField("Ham API Verisi (Denetim için)", default=dict, blank=True)

    class Meta:
        verbose_name = "Finansal İşlem"
        verbose_name_plural = "Finansal İşlemler"

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} {self.currency}"


# ---------------------------------------------------------------------------
# 5. Core Engine Rules (Kurallar ve Kurlar)
# ---------------------------------------------------------------------------

class CostRule(TimestampedModel):
    """Firmaların kendi manuel masraf ayarları."""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="cost_rules")
    packaging_cost = models.DecimalField("Paketleme Maliyeti", max_digits=10, decimal_places=2, default=0)
    handling_cost = models.DecimalField("Operasyon Maliyeti", max_digits=10, decimal_places=2, default=0)
    extra_fees = models.DecimalField("Ek Ücretler", max_digits=10, decimal_places=2, default=0)
    default_ads_cost_allocation_strategy = models.CharField("Varsayılan Reklam Dağıtım Stratejisi", max_length=50, default="revenue_ratio")

    class Meta:
        verbose_name = "Maliyet Kuralı"
        verbose_name_plural = "Maliyet Kuralları"

class ExchangeRate(TimestampedModel):
    """Mikro İhracat çevrimleri için günlük kur takibi."""
    date = models.DateField("Tarih")
    from_currency = models.CharField("Kaynak Döviz", max_length=10)
    to_currency = models.CharField("Hedef Döviz", max_length=10, default="TRY")
    rate = models.DecimalField("Kur", max_digits=10, decimal_places=4)

    class Meta:
        verbose_name = "Döviz Kuru"
        verbose_name_plural = "Döviz Kurları"
        unique_together = ("date", "from_currency", "to_currency")

    def __str__(self):
        return f"{self.from_currency}/{self.to_currency} - {self.rate} ({self.date})"


# ---------------------------------------------------------------------------
# 6. Pre-computed Analytics (Hız İçin)
# ---------------------------------------------------------------------------

class ProfitSnapshot(TimestampedModel):
    """Günlük, ürün veya kategori bazlı aggregate edilmiş snapshot tablosu."""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="profit_snapshots")
    date = models.DateField("Tarih")
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    channel = models.CharField(max_length=30)
    
    gross_revenue = models.DecimalField("Brüt Gelir", max_digits=15, decimal_places=2, default=0)
    net_revenue = models.DecimalField("Net Gelir", max_digits=15, decimal_places=2, default=0)
    total_costs = models.DecimalField("Toplam Maliyet", max_digits=15, decimal_places=2, default=0)
    profit_amount = models.DecimalField("Net Kar", max_digits=15, decimal_places=2, default=0)
    profit_margin = models.DecimalField("Kar Marjı (%)", max_digits=6, decimal_places=2, default=0)
    return_rate = models.DecimalField("İade Oranı (%)", max_digits=6, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Kârlılık Özeti"
        verbose_name_plural = "Kârlılık Özetleri"


# ---------------------------------------------------------------------------
# 7. Sync Jobs (Celery ile çalışacak senkron işler)
# ---------------------------------------------------------------------------

class SyncJob(TimestampedModel):
    class JobType(models.TextChoices):
        ORDERS = "orders", "Siparişler"
        PRODUCTS = "products", "Ürünler"
        FINANCE = "finance", "Finans / Hakediş"

    class Status(models.TextChoices):
        PENDING = "pending", "Bekliyor"
        RUNNING = "running", "Çalışıyor"
        SUCCESS = "success", "Başarılı"
        FAILED = "failed", "Başarısız"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="sync_jobs")
    marketplace_account = models.ForeignKey(MarketplaceAccount, on_delete=models.CASCADE, related_name="sync_jobs")
    job_type = models.CharField(max_length=30, choices=JobType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    started_at = models.DateTimeField("Başlama", null=True, blank=True)
    finished_at = models.DateTimeField("Bitiş", null=True, blank=True)
    logs = models.TextField("Loglar", blank=True, default="")

    class Meta:
        verbose_name = "Senkronizasyon İşi"
        verbose_name_plural = "Senkronizasyon İşleri"
        ordering = ["-created_at"]
