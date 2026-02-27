import logging
from decimal import Decimal
from django.utils.dateparse import parse_datetime
from datetime import datetime
from django.utils import timezone
from core.models import (
    Organization, MarketplaceAccount, Product, Order, OrderItem,
    FinancialTransaction, FinancialTransactionType, ProductVariant
)
from core.services.trendyol_adapter import TrendyolAdapter

logger = logging.getLogger(__name__)

class TrendyolSyncService:
    """
    TrendyolAdapter kullanarak API'den çekilen verileri 
    EcomPro veritabanı tablolarına dönüştürür ve kaydeder.
    """
    def __init__(self, account: MarketplaceAccount):
        self.account = account
        self.organization = account.organization
        self.adapter = TrendyolAdapter(
            api_key=account.api_key,
            api_secret=account.api_secret,
            seller_id=account.seller_id
        )

    def sync_all(self):
        """Ürünleri, siparişleri ve hakedişleri senkronize eder."""
        logger.info(f"Syncing all for account {self.account}")
        self.sync_products()
        self.sync_orders()
        self.sync_settlements() # Eğer financial kurgu oradan yapılıyorsa
        
        self.account.last_sync_at = timezone.now()
        self.account.save()
        logger.info("Sync completed.")

    def sync_products(self):
        logger.info("Fetching products...")
        products_data = self.adapter.fetch_products()
        for p_data in products_data:
            barcode = p_data.get("barcode")
            if not barcode:
                continue
                
            vat_rate = Decimal(str(p_data.get("vatRate", "0")))
            sale_price = Decimal(str(p_data.get("salePrice", "0")))
            # Not: Basic product endpoint doesn't always return commissions, fallback or default to 0
            
            product, created = Product.objects.update_or_create(
                organization=self.organization,
                barcode=barcode,
                defaults={
                    "marketplace_account": self.account,
                    "title": p_data.get("title", "")[:500],
                    "category_name": p_data.get("categoryName", ""),
                    "image_url": p_data.get("images", [{}])[0].get("url", "") if p_data.get("images") else "",
                    "sale_price": sale_price,
                    "vat_rate": vat_rate,
                    "marketplace_sku": p_data.get("productMainId", ""),
                }
            )

    def sync_orders(self):
        logger.info("Fetching orders...")
        orders_data = self.adapter.fetch_orders(status="Delivered") # Örnek sadece Delivered'lar kâr için
        for o_data in orders_data:
            order_number = o_data.get("orderNumber")
            if not order_number:
                continue

            order_date_ts = o_data.get("orderDate", 0)
            order_date = datetime.fromtimestamp(order_date_ts / 1000.0, tz=timezone.utc)
            
            order, created = Order.objects.update_or_create(
                organization=self.organization,
                marketplace_order_id=order_number,
                defaults={
                    "marketplace_account": self.account,
                    "order_date": order_date,
                    "status": Order.Status.DELIVERED,
                    "channel": Order.Channel.TRENDYOL,
                    "customer_fullname": o_data.get("shipmentAddress", {}).get("fullName", "")[:255],
                    "customer_city": o_data.get("shipmentAddress", {}).get("city", "")[:100],
                    "total_price": Decimal(str(o_data.get("totalPrice", "0"))),
                }
            )

            # Sipariş satırları ve komisyonlar
            for line in o_data.get("lines", []):
                barcode = line.get("barcode", "")
                product = Product.objects.filter(organization=self.organization, barcode=barcode).first()
                
                price = Decimal(str(line.get("price", "0")))
                discount = Decimal(str(line.get("discount", "0")))
                
                # Order Item creation
                order_item, item_created = OrderItem.objects.update_or_create(
                    order=order,
                    marketplace_line_id=str(line.get("id", "")),
                    defaults={
                        "product_variant": product.variants.first() if product and product.variants.exists() else None,
                        "sku": line.get("merchantSku", ""),
                        "quantity": line.get("quantity", 1),
                        "sale_price_gross": price,
                        "sale_price_net": price - discount,
                        "discount": discount,
                    }
                )

                if item_created:
                    # Temsili bir komisyon / finansal kayıt oluştur
                    from core.models import FinancialTransaction, FinancialTransactionType
                    # Not: Gerçek API'da komisyonu veya settlements'ı beklemek daha iyidir,
                    # Ancak MVP'de satıştaki tutarlarla bir FinancialTransaction atılabilir:
                    FinancialTransaction.objects.update_or_create(
                        organization=self.organization,
                        order_item_ref=order_item,
                        transaction_type=FinancialTransactionType.COMMISSION,
                        defaults={
                            "amount": price * Decimal("0.15"), # Örnek %15
                            "occurred_at": order_date
                        }
                    )
                    
                    FinancialTransaction.objects.update_or_create(
                        organization=self.organization,
                        order_item_ref=order_item,
                        transaction_type=FinancialTransactionType.VAT_OUTPUT,
                        defaults={
                            "amount": price - (price / (Decimal("1") + (product.vat_rate / Decimal("100")) if product else Decimal("1.2"))),
                            "occurred_at": order_date
                        }
                    )

    def sync_settlements(self):
        # Finansal Kesintiler (Kargo Kesintisi, Gerçek Komisyon vb.) burada işlenip FinancialTransaction'lara yansıtılır.
        pass
