"""
EcomMarj Core Models
===================
All domain models for multi-tenant e-commerce profitability tracking.
"""

from django.db import models
from django.conf import settings
from decimal import Decimal


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
    class OnboardingStatus(models.TextChoices):
        WELCOME = "WELCOME", "Karşılama"
        MARKETPLACE_CONNECT = "MARKETPLACE_CONNECT", "Pazaryeri Bağlantısı"
        SYNCING = "SYNCING", "Senkronizasyon"
        COMPLETED = "COMPLETED", "Tamamlandı"

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
    onboarding_status = models.CharField(
        "Onboarding Durumu",
        max_length=50,
        choices=OnboardingStatus.choices,
        default=OnboardingStatus.WELCOME
    )
    static_otp_code = models.CharField(
        "Sabit OTP Kodu",
        max_length=10,
        null=True,
        blank=True,
        help_text="Dolu ise giriş/kayıt OTP olarak bu sabit kod kullanılır. Boşsa rastgele kod gönderilir."
    )

    # --- Yönetici paneli alanları (additive — mevcut akış bozulmaz) ---
    is_suspended = models.BooleanField("Askıya Alındı", default=False)
    suspension_reason = models.TextField("Askıya Alma Nedeni", blank=True, default="")
    admin_note = models.TextField("Admin Notu", blank=True, default="")
    is_priority = models.BooleanField("Öncelikli", default=False)
    is_risky = models.BooleanField("Riskli", default=False)
    admin_override = models.BooleanField("Admin Override (Erişim)", default=False)
    last_login_ip = models.GenericIPAddressField("Son Giriş IP", null=True, blank=True)
    email_verified = models.BooleanField("E-posta Doğrulandı", default=False)
    google_connected = models.BooleanField("Google Bağlı", default=False)
    trendyol_store_count = models.IntegerField("Trendyol Mağaza Sayısı", default=0)

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
    
    sale_price = models.DecimalField("Satış Fiyatı", max_digits=12, decimal_places=2, default=0)
    vat_rate = models.DecimalField("KDV Oranı (%)", max_digits=5, decimal_places=2, default=0)
    commission_rate = models.DecimalField("Komisyon Oranı (%)", max_digits=5, decimal_places=2, default=0)
    
    initial_stock = models.IntegerField("İlk Stok", default=0, help_text="Sisteme ilk çekildiğindeki stok miktarı")
    current_stock = models.IntegerField("Güncel Stok", default=0)
    
    desi = models.DecimalField("Desi", max_digits=6, decimal_places=2, default=Decimal("1.00"))
    default_carrier = models.CharField("Varsayılan Kargo Firması", max_length=50, default="Trendyol Express")
    
    brand = models.CharField("Marka", max_length=255, blank=True, default="")
    return_rate = models.DecimalField("İade Oranı (%)", max_digits=5, decimal_places=2, default=0)
    fast_delivery = models.BooleanField("Bugün Kargoda", default=False)
    trendyol_created_at = models.DateTimeField("Trendyol Yüklenme Tarihi", null=True, blank=True, db_index=True)
    
    trendyol_content_id = models.CharField("Trendyol İçerik ID", max_length=100, blank=True, default="")
    currency = models.CharField("Para Birimi", max_length=10, default="TRY")
    is_active = models.BooleanField("Aktif mi?", default=True)

    @property
    def is_low_stock(self):
        """Kritik stok uyarısı: Güncel stok, ilk stoğun %20'si veya altındaysa ve başlangıçta en az 5 ürün varsa."""
        if self.initial_stock >= 5 and self.current_stock > 0:
            return self.current_stock <= (self.initial_stock * 0.20)
        return False

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

    # Maliyet Bilgileri
    cost_price = models.DecimalField("Ürün Maliyeti (KDV Dahil)", max_digits=12, decimal_places=2, default=0)
    cost_vat_rate = models.DecimalField("Maliyet KDV Oranı (%)", max_digits=5, decimal_places=2, default=0)
    
    color = models.CharField("Renk", max_length=100, blank=True, default="")
    size = models.CharField("Beden", max_length=100, blank=True, default="")
    stock = models.IntegerField("Stok", default=0)

    # Varyanta özel desi (boşsa ürün desisini kullanırız)
    desi = models.DecimalField("Varyant Desi", max_digits=6, decimal_places=2, null=True, blank=True)

    # Ekstra maliyetler
    extra_cost_rate = models.DecimalField("Ekstra Maliyet (%)", max_digits=6, decimal_places=2, default=0)
    extra_cost_amount = models.DecimalField("Ekstra Maliyet (TL)", max_digits=10, decimal_places=2, default=0)

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
        INVOICED = "Invoiced", "Faturalandı"
        SHIPPED = "Shipped", "Kargoya Verildi"
        AT_COLLECTION_POINT = "AtCollectionPoint", "Teslimat Noktasında"
        DELIVERED = "Delivered", "Teslim Edildi"
        CANCELLED = "Cancelled", "İptal"
        RETURNED = "Returned", "İade"
        UNDELIVERED = "UnDelivered", "Teslim Edilemedi"
        UNSUPPLIED = "UnSupplied", "Tedarik Edilemedi"
        UNPACKED = "UnPacked", "Paket Bölündü"
        REPACK = "Repack", "Tekrar Paketlendi"
        AWAITING = "Awaiting", "Ödeme Bekliyor"
        
    class Channel(models.TextChoices):
        TRENDYOL = "trendyol", "Trendyol"
        MICRO_EXPORT = "micro_export", "Trendyol Mikro İhracat"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="orders")
    marketplace_account = models.ForeignKey(MarketplaceAccount, on_delete=models.CASCADE, related_name="orders")
    marketplace_order_id = models.CharField("Pazaryeri Sipariş No", max_length=100, db_index=True)
    package_id = models.CharField("Paket ID (shipmentPackageId)", max_length=100, db_index=True, default="")
    order_number = models.CharField("Trendyol Sipariş Numarası", max_length=100, db_index=True, default="")
    order_date = models.DateTimeField("Sipariş Tarihi")
    last_modified_date = models.DateTimeField("Son Değişiklik Tarihi", null=True, blank=True, db_index=True)
    status = models.CharField(max_length=30, choices=Status.choices)
    previous_status = models.CharField("Önceki Durum", max_length=30, blank=True, default="")
    status_changed_at = models.DateTimeField("Durum Değişim Tarihi", null=True, blank=True)
    channel = models.CharField(max_length=30, choices=Channel.choices, default=Channel.TRENDYOL)
    country_code = models.CharField("Ülke Kodu", max_length=5, default="TR")
    
    # Kargo bilgileri
    cargo_provider_name = models.CharField("Kargo Firması", max_length=100, blank=True, default="")
    cargo_tracking_number = models.CharField("Kargo Takip No", max_length=100, blank=True, default="")
    cargo_deci = models.DecimalField("Kargo Desi (Trendyol'dan)", max_digits=8, decimal_places=2, null=True, blank=True)
    cargo_cost = models.DecimalField("Kargo Maliyeti (Hesaplanan)", max_digits=10, decimal_places=2, null=True, blank=True)
    fast_delivery = models.BooleanField("Hızlı Teslimat / Bugün Kargoda", default=False)
    created_by = models.CharField("Paket Oluşum Tipi", max_length=50, blank=True, default="")

    # Trendyol package amount snapshot fields. These are package-level source
    # numbers from getShipmentPackages and help reconcile with Sales & Operation.
    package_gross_amount = models.DecimalField("Paket Brüt Tutar", max_digits=12, decimal_places=2, default=0)
    package_seller_discount = models.DecimalField("Paket Satıcı İndirimi", max_digits=12, decimal_places=2, default=0)
    package_ty_discount = models.DecimalField("Paket Trendyol İndirimi", max_digits=12, decimal_places=2, default=0)
    package_total_discount = models.DecimalField("Paket Toplam İndirim", max_digits=12, decimal_places=2, default=0)
    
    # Sync metadata
    raw_payload_hash = models.CharField("Payload Hash", max_length=64, blank=True, default="")
    raw_payload = models.JSONField("Ham Trendyol Paket Verisi", default=dict, blank=True)
    last_synced_at = models.DateTimeField("Son Sync Zamanı", null=True, blank=True)

    class Meta:
        verbose_name = "Sipariş"
        verbose_name_plural = "Siparişler"
        unique_together = [("organization", "package_id")]
        indexes = [
            models.Index(fields=["organization", "order_date"]),
            models.Index(fields=["organization", "last_modified_date"]),
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "order_number"], name="ord_org_ordernum_idx"),
            models.Index(fields=["organization", "marketplace_order_id"], name="ord_org_mktid_idx"),
        ]

    def __str__(self):
        return f"Order #{self.marketplace_order_id} (Pkg: {self.package_id})"


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
    
    # Snapshot: Sipariş anındaki güncel veriler (Trendyol'dan çekilen)
    applied_vat_rate = models.DecimalField("Uygulanan KDV", max_digits=5, decimal_places=2, default=0)
    applied_commission_rate = models.DecimalField("Uygulanan Komisyon", max_digits=5, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Sipariş Kalemi"
        verbose_name_plural = "Sipariş Kalemleri"
        indexes = [
            # Dashboard kâr hesaplamaları order_in + product_variant join'i yapar
            models.Index(fields=["order", "product_variant"], name="oi_order_variant_idx"),
            models.Index(fields=["sku"], name="oi_sku_idx"),
        ]

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
        indexes = [
            models.Index(fields=["organization", "transaction_type"], name="ft_org_type_idx"),
            models.Index(fields=["order_item_ref", "transaction_type"], name="ft_itemref_type_idx"),
            models.Index(fields=["organization", "created_at"], name="ft_org_created_idx"),
        ]

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
# 6. Pre-computed Analytics (Hız İçin) & Cargo Prices
# ---------------------------------------------------------------------------

class CargoPricing(TimestampedModel):
    """
    Kargo firmalarının desi bazında KDV hariç fiyat listesi.
    """
    carrier_name = models.CharField("Kargo Firması", max_length=100) # Trendyol Express, Aras, Yurtiçi vb.
    desi = models.DecimalField("Desi", max_digits=6, decimal_places=2)
    price_without_vat = models.DecimalField("KDV Hariç Fiyat (TL)", max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Kargo Fiyatlandırması"
        verbose_name_plural = "Kargo Fiyatlandırmaları"
        unique_together = ("carrier_name", "desi")

    def __str__(self):
        return f"{self.carrier_name} - {self.desi} Desi: {self.price_without_vat} TL"


class CargoInvoice(TimestampedModel):
    """
    Trendyol Kargo Faturası API'sinden çekilen sipariş bazlı gerçek kargo tutarları.
    /finance/che/sellers/{id}/cargo-invoice/{invoiceSerialNumber}/items endpoint'inden gelir.
    """
    organization        = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="cargo_invoices")
    order_number        = models.CharField("Sipariş No", max_length=50, db_index=True)
    invoice_serial_number = models.CharField("Fatura Seri No", max_length=100)
    parcel_unique_id    = models.CharField("Paket / Koli ID", max_length=100, blank=True, default="", db_index=True)
    amount              = models.DecimalField("Kargo Tutarı (KDV Dahil)", max_digits=10, decimal_places=2)
    desi                = models.DecimalField("Desi", max_digits=6, decimal_places=2, null=True, blank=True)
    shipment_package_type = models.CharField("Gönderi Tipi", max_length=200, blank=True)
    raw_payload         = models.JSONField("Ham Veri", default=dict, blank=True)

    class Meta:
        verbose_name = "Kargo Faturası Kalemi"
        verbose_name_plural = "Kargo Faturası Kalemleri"
        unique_together = ("organization", "order_number", "invoice_serial_number", "parcel_unique_id")
        indexes = [models.Index(fields=["organization", "order_number"])]

    def __str__(self):
        return f"Kargo #{self.order_number} — ₺{self.amount}"


class CarrierFlatRate(TimestampedModel):
    """
    Kargo firmalarının sipariş başına sabit (flat) tarifesi.
    Trendyol tarife değiştirdiğinde buradan güncellenir — koda dokunmak gerekmez.
    """
    carrier_name    = models.CharField("Kargo Firması", max_length=100, unique=True)
    rate_kdv_dahil  = models.DecimalField("Flat Rate (KDV Dahil, TL)", max_digits=10, decimal_places=2)
    notes           = models.CharField("Not", max_length=255, blank=True, default="")

    class Meta:
        verbose_name = "Kargo Flat Tarife"
        verbose_name_plural = "Kargo Flat Tarifeleri"
        ordering = ["carrier_name"]

    def __str__(self):
        return f"{self.carrier_name}: ₺{self.rate_kdv_dahil}"


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
# 7. Sync Infrastructure
# ---------------------------------------------------------------------------

class SyncJob(TimestampedModel):
    class JobType(models.TextChoices):
        ORDERS = "orders", "Siparişler"
        PRODUCTS = "products", "Ürünler"
        FINANCE = "finance", "Finans / Hakediş"
        CLAIMS = "claims", "İade / Claim"
        RECONCILIATION = "reconciliation", "Reconciliation"

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


class SyncCheckpoint(TimestampedModel):
    """
    Her hesap/sync tipi için son başarılı sync zamanını tutar.
    Incremental sync bu checkpoint'ten başlar (overlap ile).
    """
    class SyncType(models.TextChoices):
        ORDERS = "orders", "Siparişler"
        CLAIMS = "claims", "İade / Claim"
        PRODUCTS = "products", "Ürünler"

    marketplace_account = models.ForeignKey(MarketplaceAccount, on_delete=models.CASCADE, related_name="sync_checkpoints")
    sync_type = models.CharField(max_length=30, choices=SyncType.choices)
    last_successful_sync_at = models.DateTimeField("Son Başarılı Sync")
    last_fetched_modified_date = models.DateTimeField("Son Çekilen Modified Date", null=True, blank=True)

    class Meta:
        verbose_name = "Sync Checkpoint"
        verbose_name_plural = "Sync Checkpoints"
        unique_together = [("marketplace_account", "sync_type")]

    def __str__(self):
        return f"{self.marketplace_account} - {self.sync_type}: {self.last_successful_sync_at}"


class SyncAuditLog(TimestampedModel):
    """
    Her sync çalışmasının detaylı audit kaydı.
    """
    class SyncMode(models.TextChoices):
        FULL = "full", "Full Sync"
        INCREMENTAL = "incremental", "Incremental Sync"
        BACKFILL = "backfill", "Backfill"
        RECONCILIATION = "reconciliation", "Reconciliation"
        WEBHOOK = "webhook", "Webhook"

    marketplace_account = models.ForeignKey(MarketplaceAccount, on_delete=models.CASCADE, related_name="sync_audit_logs")
    sync_type = models.CharField(max_length=30)  # orders, claims, products
    sync_mode = models.CharField(max_length=30, choices=SyncMode.choices)
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)
    
    # Date range that was synced
    date_range_start = models.DateTimeField(null=True, blank=True)
    date_range_end = models.DateTimeField(null=True, blank=True)
    
    # Counters
    total_fetched = models.IntegerField(default=0)
    inserted = models.IntegerField(default=0)
    updated = models.IntegerField(default=0)
    skipped = models.IntegerField(default=0)
    failed = models.IntegerField(default=0)
    
    # Result
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, default="")
    duration_seconds = models.FloatField(default=0)

    class Meta:
        verbose_name = "Sync Audit Log"
        verbose_name_plural = "Sync Audit Logs"
        ordering = ["-started_at"]

    def __str__(self):
        status = "✅" if self.success else "❌"
        return f"{status} {self.sync_mode} {self.sync_type} - {self.total_fetched} fetched"


class ReturnClaim(TimestampedModel):
    """
    Trendyol getClaims endpoint'inden gelen iade/claim kayıtları.
    """
    class ClaimStatus(models.TextChoices):
        CREATED          = "Created",          "Oluşturuldu"
        IN_PROGRESS      = "InProgress",       "İşlemde"
        RESOLVED         = "Resolved",         "Çözümlendi"
        REJECTED         = "Rejected",         "Reddedildi"
        ACCEPTED         = "Accepted",         "Onaylandı"
        WAITING_ACTION   = "WaitingInAction",  "Aksiyon Bekliyor"
        UNRESOLVED       = "Unresolved",       "Çözümsüz"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="return_claims")
    marketplace_account = models.ForeignKey(MarketplaceAccount, on_delete=models.CASCADE, related_name="return_claims")
    claim_id = models.CharField("Claim ID", max_length=100, db_index=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name="claims")
    order_number = models.CharField("Sipariş No", max_length=100, blank=True, default="")

    claim_date = models.DateTimeField("Claim Tarihi", null=True, blank=True)
    order_date = models.DateTimeField("Sipariş Tarihi", null=True, blank=True)
    last_modified_date = models.DateTimeField("Son Güncelleme", null=True, blank=True)
    claim_status = models.CharField(max_length=30, choices=ClaimStatus.choices, default=ClaimStatus.CREATED)
    reason = models.TextField("İade Nedeni", blank=True, default="")
    cargo_provider = models.CharField("Kargo Firması", max_length=100, blank=True, default="")

    # Finansal
    refund_amount = models.DecimalField("İade Tutarı", max_digits=12, decimal_places=2, default=0)
    cargo_cost = models.DecimalField("Kargo Maliyeti", max_digits=12, decimal_places=2, default=0)

    raw_payload_hash = models.CharField("Payload Hash", max_length=64, blank=True, default="")
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "İade / Claim"
        verbose_name_plural = "İade / Claim Kayıtları"
        unique_together = [("organization", "claim_id")]

    def __str__(self):
        return f"Claim #{self.claim_id} - {self.claim_status}"


class ReturnClaimItem(TimestampedModel):
    """
    Claim bazında iade edilen ürün kalemleri.
    """
    claim = models.ForeignKey(ReturnClaim, on_delete=models.CASCADE, related_name="claim_items")
    product_name = models.CharField("Ürün Adı", max_length=500, blank=True, default="")
    barcode = models.CharField("Barkod", max_length=100, blank=True, default="")
    merchant_sku = models.CharField("Satıcı SKU", max_length=100, blank=True, default="")
    price = models.DecimalField("Birim Fiyat", max_digits=12, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField("Adet", default=1)
    claim_item_status = models.CharField("Kalem Durumu", max_length=50, blank=True, default="")
    customer_reason = models.CharField("Müşteri İade Nedeni", max_length=500, blank=True, default="")
    outgoing_cargo_cost = models.DecimalField("Giden Kargo", max_digits=10, decimal_places=2, default=135.32)
    incoming_cargo_cost = models.DecimalField("Gelen Kargo", max_digits=10, decimal_places=2, default=135.32)

    class Meta:
        verbose_name = "İade Kalem"
        verbose_name_plural = "İade Kalemleri"

    def __str__(self):
        return f"{self.product_name} ({self.claim.claim_id})"


# ---------------------------------------------------------------------------
# 8. Ad Expenses (Reklam Giderleri)
# ---------------------------------------------------------------------------

class AdExpense(TimestampedModel):
    """
    Reklam giderleri — Trendyol finance API veya manuel giriş.
    """
    class ExpenseType(models.TextChoices):
        ADVERTISING = "advertising", "Trendyol Reklam"
        INFLUENCER  = "influencer",  "İnfluencer Gideri"
        OTHER       = "other",       "Diğer"

    organization        = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="ad_expenses")
    marketplace_account = models.ForeignKey(MarketplaceAccount, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_date    = models.DateField("İşlem Tarihi")
    transaction_type    = models.CharField("İşlem Tipi (API)", max_length=100, blank=True, default="")
    amount              = models.DecimalField("Tutar", max_digits=12, decimal_places=2)
    description         = models.TextField("Açıklama", blank=True, default="")
    expense_type        = models.CharField(
        "Gider Türü", max_length=20,
        choices=ExpenseType.choices,
        default=ExpenseType.ADVERTISING,
    )
    external_id         = models.CharField("Harici ID", max_length=255, blank=True, default="")
    raw_payload         = models.JSONField("Ham Veri", default=dict, blank=True)

    class Meta:
        verbose_name          = "Reklam Gideri"
        verbose_name_plural   = "Reklam Giderleri"
        indexes = [models.Index(fields=["organization", "transaction_date"])]

    def __str__(self):
        return f"{self.get_expense_type_display()} — ₺{self.amount} ({self.transaction_date})"


# ---------------------------------------------------------------------------
# 9. CHE Transactions (Cari Hesap Ekstresi — Trendyol Finance API)
# ---------------------------------------------------------------------------

class CheTransaction(TimestampedModel):
    """
    Trendyol CHE (Cari Hesap Ekstresi) API'den çekilen ham finansal işlemler.
    /finance/che/sellers/{id}/settlements ve /otherfinancials endpointlerinden gelir.
    """
    SOURCE_SETTLEMENTS = 'settlements'
    SOURCE_OTHER = 'otherfinancials'
    SOURCE_CHOICES = [
        (SOURCE_SETTLEMENTS, 'Settlements'),
        (SOURCE_OTHER, 'Other Financials'),
    ]

    transaction_id = models.CharField(max_length=100)
    transaction_date = models.DateTimeField()
    barcode = models.CharField(max_length=100, null=True, blank=True)
    transaction_type = models.CharField(max_length=100)
    transaction_type_code = models.CharField(max_length=100, null=True, blank=True)
    transaction_sub_type = models.CharField(max_length=100, null=True, blank=True)
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    receipt_id = models.BigIntegerField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    debt = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    commission_rate = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    commission_amount = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    seller_revenue = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    order_number = models.CharField(max_length=100, null=True, blank=True)
    shipment_package_id = models.BigIntegerField(null=True, blank=True)
    payment_order_id = models.BigIntegerField(null=True, blank=True)
    payment_period = models.IntegerField(null=True, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    commission_invoice_serial_number = models.CharField(max_length=100, null=True, blank=True)
    seller_id = models.BigIntegerField(null=True, blank=True)
    store_id = models.BigIntegerField(null=True, blank=True)
    store_name = models.CharField(max_length=255, null=True, blank=True)
    store_address = models.TextField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    affiliate = models.CharField(max_length=50, null=True, blank=True)
    order_date = models.DateTimeField(null=True, blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="che_transactions")
    account = models.ForeignKey('MarketplaceAccount', on_delete=models.CASCADE, related_name="che_transactions")

    class Meta:
        verbose_name = "CHE İşlemi"
        verbose_name_plural = "CHE İşlemleri"
        indexes = [
            models.Index(fields=['organization', 'transaction_type', 'transaction_date']),
            models.Index(fields=['order_number']),
            models.Index(fields=['barcode']),
            models.Index(fields=['organization', 'source', 'transaction_date']),
            models.Index(fields=['account', 'source', 'transaction_id']),
            models.Index(fields=['payment_order_id']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['account', 'source', 'transaction_id'],
                name='core_chetx_account_source_txid_uniq',
            ),
        ]

    def __str__(self):
        return f"{self.transaction_type} — {self.transaction_id}"


# ---------------------------------------------------------------------------
# Cargo Price Table
# ---------------------------------------------------------------------------

class CargoPrice(models.Model):
    """Admin'den yönetilebilen desi bazlı kargo fiyat tablosu."""
    desi = models.IntegerField("Desi", unique=True)
    price = models.DecimalField("Fiyat (KDV Dahil, TL)", max_digits=10, decimal_places=2)
    cargo_provider = models.CharField("Kargo Firması", max_length=100, default="Yurtiçi Kargo")
    is_active = models.BooleanField("Aktif", default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["desi"]
        verbose_name = "Kargo Fiyatı"
        verbose_name_plural = "Kargo Fiyatları"

    def __str__(self):
        return f"Desi-{self.desi}: ₺{self.price}"


# ---------------------------------------------------------------------------
# Subscription
# ---------------------------------------------------------------------------

class SubscriptionPlan(models.Model):
    PLAN_TYPES = [
        ("free_trial", "Free Trial"),
        ("monthly", "Aylık"),
        ("yearly", "Yıllık"),
        ("lifetime", "Ömür Boyu"),
        ("manual", "Manuel"),
    ]

    name = models.CharField("Plan Adı", max_length=100)
    price = models.DecimalField("Fiyat", max_digits=10, decimal_places=2)
    interval = models.CharField("Periyot", max_length=20, default="monthly")
    is_active = models.BooleanField("Aktif", default=True)
    order_limit = models.IntegerField("Aylık Sipariş Limiti", default=1000)
    store_limit = models.IntegerField("Mağaza Limiti", default=1)
    plan_tier = models.CharField("Plan Kademesi", max_length=50, default="starter")  # starter/business/enterprise
    yearly_total = models.DecimalField("Yıllık Toplam Tutar", max_digits=10, decimal_places=2, null=True, blank=True)

    # --- Yönetici paneli alanları ---
    plan_type = models.CharField("Plan Tipi", max_length=20, choices=PLAN_TYPES, default="monthly")
    duration_days = models.IntegerField("Süre (gün)", null=True, blank=True)
    features = models.JSONField("Özellikler", default=dict, blank=True)

    class Meta:
        verbose_name = "Abonelik Planı"
        verbose_name_plural = "Abonelik Planları"

    def __str__(self):
        return f"{self.name} — ₺{self.price}/{self.interval}"


class UserSubscription(models.Model):
    # NOT: Mevcut değerler (trialing/past_due/admin_override) KORUNDU; yeni
    # yönetici-paneli değerleri eklendi (UNION). is_access_allowed() her ikisini
    # de doğru yorumlar — eski satırlar ve PayTR akışı bozulmaz.
    STATUS_CHOICES = [
        ("active", "Aktif"),
        ("passive", "Pasif"),
        ("trial", "Deneme"),
        ("trialing", "Deneme (eski)"),
        ("cancelled", "İptal"),
        ("expired", "Süresi Doldu"),
        ("suspended", "Askıya Alındı"),
        ("past_due", "Gecikmiş"),
        ("admin_override", "Admin Kontrolü"),
    ]
    ACCESS_STATUSES = ("active", "trial", "trialing", "admin_override")

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="usersubscription",
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subscriptions",
    )
    status = models.CharField(
        "Durum", max_length=50, choices=STATUS_CHOICES, default="trialing"
    )
    admin_override = models.BooleanField("Admin Erişimi", default=False)
    admin_override_reason = models.TextField("Admin Notu", blank=True)
    trial_end = models.DateTimeField("Deneme Bitiş (eski)", null=True, blank=True)
    current_period_end = models.DateTimeField("Dönem Bitiş", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- Yönetici paneli alanları ---
    start_date = models.DateTimeField("Başlangıç", null=True, blank=True)
    end_date = models.DateTimeField("Bitiş", null=True, blank=True)
    trial_end_date = models.DateTimeField("Deneme Bitiş Tarihi", null=True, blank=True)
    created_by_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_subscriptions",
    )
    notes = models.TextField("Notlar", blank=True, default="")

    class Meta:
        verbose_name = "Kullanıcı Aboneliği"
        verbose_name_plural = "Kullanıcı Abonelikleri"

    def __str__(self):
        return f"{self.user.email} — {self.status}"

    def is_access_allowed(self):
        # admin_override veya status alanı admin_override değerine sahipse direkt erişim
        if self.admin_override or self.status == "admin_override":
            return True
        # Açıkça erişim engelleyen durumlar (önce kontrol)
        if self.status in ("passive", "suspended", "cancelled", "expired", "past_due"):
            return False
        # Aktif/deneme erişimi (hem eski 'trialing' hem yeni 'trial' kabul)
        return self.status in self.ACCESS_STATUSES


# ---------------------------------------------------------------------------
# Payment
# ---------------------------------------------------------------------------

class Payment(models.Model):
    # PayTR akışı "success" değerini set ediyor; yönetici paneli "paid" terimini
    # kullanıyor — her ikisi de geçerli (UNION). PAID_STATUSES sayım/raporlama
    # için tek doğruluk kaynağıdır.
    STATUS_CHOICES = [
        ("pending", "Bekliyor"),
        ("paid", "Ödendi"),
        ("success", "Başarılı (PayTR)"),
        ("failed", "Başarısız"),
        ("refunded", "İade Edildi"),
        ("overdue", "Gecikmiş"),
    ]
    PAID_STATUSES = ("paid", "success")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments"
    )
    subscription = models.ForeignKey(
        "UserSubscription", on_delete=models.SET_NULL, null=True, blank=True, related_name="payments"
    )
    plan = models.ForeignKey(
        "SubscriptionPlan", on_delete=models.SET_NULL, null=True, blank=True, related_name="payments"
    )
    amount = models.DecimalField("Tutar", max_digits=10, decimal_places=2)
    currency = models.CharField("Para Birimi", max_length=3, default="TRY")
    status = models.CharField("Durum", max_length=20, choices=STATUS_CHOICES, default="pending")
    # Manuel admin ödemelerinde sahte unique değer kullanılır: MANUAL_<uuid>
    merchant_oid = models.CharField("Sipariş No (PayTR)", max_length=200, unique=True)
    paytr_token = models.CharField("PayTR Token", max_length=500, null=True, blank=True)
    paytr_response = models.JSONField("PayTR Yanıtı", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- Yönetici paneli alanları ---
    payment_date = models.DateTimeField("Ödeme Tarihi", null=True, blank=True)
    due_date = models.DateTimeField("Vade Tarihi", null=True, blank=True)
    paytr_transaction_id = models.CharField("PayTR Transaction ID", max_length=200, blank=True, default="")
    invoice_note = models.TextField("Fatura Notu", blank=True, default="")
    added_by_admin = models.BooleanField("Admin Tarafından Eklendi", default=False)

    class Meta:
        verbose_name = "Ödeme"
        verbose_name_plural = "Ödemeler"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} — ₺{self.amount} ({self.status})"


# ---------------------------------------------------------------------------
# Access Codes — admin-issued login codes that bypass OTP
# ---------------------------------------------------------------------------

class AccessCode(models.Model):
    """Yönetici tarafından üretilen, OTP yerine geçen giriş kodu."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="access_codes",
    )
    code = models.CharField("Kod", max_length=32, unique=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issued_codes",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField("Son Geçerlilik", null=True, blank=True)
    is_active = models.BooleanField("Aktif", default=True)
    is_lifetime = models.BooleanField("Süresiz", default=False)
    use_count = models.IntegerField("Kullanım Sayısı", default=0)
    max_uses = models.IntegerField("Maks. Kullanım", null=True, blank=True)
    last_used_at = models.DateTimeField("Son Kullanım", null=True, blank=True)

    class Meta:
        verbose_name = "Giriş Kodu"
        verbose_name_plural = "Giriş Kodları"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_active"], name="ac_user_active_idx"),
        ]

    def __str__(self):
        return f"{self.code[:4]}**** ({self.user.email})"

    def is_usable(self) -> bool:
        from django.utils import timezone
        if not self.is_active:
            return False
        if not self.is_lifetime and self.expires_at and self.expires_at < timezone.now():
            return False
        if self.max_uses is not None and self.use_count >= self.max_uses:
            return False
        return True


# ---------------------------------------------------------------------------
# Brute-force koruma — login attempts & account lockout
# ---------------------------------------------------------------------------

class LoginAttempt(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="login_attempts",
    )
    ip_address = models.GenericIPAddressField()
    attempted_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)
    attempt_type = models.CharField(max_length=20, default="password")

    class Meta:
        verbose_name = "Giriş Denemesi"
        verbose_name_plural = "Giriş Denemeleri"
        ordering = ["-attempted_at"]
        indexes = [
            models.Index(fields=["user", "attempted_at"], name="la_user_time_idx"),
            models.Index(fields=["ip_address", "attempted_at"], name="la_ip_time_idx"),
        ]


class AccountLockout(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lockouts",
    )
    locked_until = models.DateTimeField("Kilit Bitişi")
    reason = models.CharField("Sebep", max_length=200)
    failed_attempts = models.IntegerField("Başarısız Deneme Sayısı", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Hesap Kilidi"
        verbose_name_plural = "Hesap Kilitleri"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "locked_until"], name="al_user_until_idx"),
        ]

    def is_active(self) -> bool:
        from django.utils import timezone
        return self.locked_until > timezone.now()


# ---------------------------------------------------------------------------
# Admin Audit Log
# ---------------------------------------------------------------------------

class AdminLog(models.Model):
    ACTION_TYPES = [
        ("user_activate", "Kullanıcı Aktifleştirme"),
        ("user_deactivate", "Kullanıcı Pasifleştirme"),
        ("user_suspend", "Kullanıcı Askıya Alma"),
        ("user_unsuspend", "Askıdan Çıkarma"),
        ("user_update", "Kullanıcı Güncelleme"),
        ("plan_change", "Plan Değişikliği"),
        ("subscription_create", "Abonelik Oluşturma"),
        ("subscription_extend", "Abonelik Uzatma"),
        ("subscription_cancel", "Abonelik İptal"),
        ("subscription_trial", "Trial Başlat/Uzat"),
        ("code_create", "Kod Oluşturma"),
        ("code_delete", "Kod Silme"),
        ("code_regenerate", "Kod Yenileme"),
        ("payment_add", "Ödeme Ekleme"),
        ("payment_edit", "Ödeme Düzenleme"),
        ("override_set", "Manuel Override"),
        ("note_add", "Not Ekleme"),
    ]

    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="admin_logs",
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="received_logs",
    )
    action_type = models.CharField(max_length=40, choices=ACTION_TYPES)
    description = models.TextField()
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = "Admin Logu"
        verbose_name_plural = "Admin Logları"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["admin", "created_at"], name="al_admin_time_idx"),
            models.Index(fields=["target_user", "created_at"], name="al_target_time_idx"),
            models.Index(fields=["action_type", "created_at"], name="al_action_time_idx"),
        ]

    def __str__(self):
        return f"{self.action_type} by {self.admin or 'system'} at {self.created_at:%Y-%m-%d %H:%M}"
