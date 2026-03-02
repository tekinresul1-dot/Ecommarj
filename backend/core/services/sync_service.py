import logging
from decimal import Decimal
from datetime import datetime, timezone as dt_timezone
from django.utils import timezone
from core.models import (
    Organization, MarketplaceAccount, Product, Order, OrderItem,
    FinancialTransaction, FinancialTransactionType, ProductVariant
)
from core.services.trendyol_adapter import TrendyolAdapter
from core.utils.encryption import decrypt_value

logger = logging.getLogger(__name__)

# Trendyol status -> EcomPro status mapping
STATUS_MAP = {
    "Created": Order.Status.CREATED,
    "Picking": Order.Status.PICKING,
    "Shipped": Order.Status.SHIPPED,
    "Delivered": Order.Status.DELIVERED,
    "Cancelled": Order.Status.CANCELLED,
    "Returned": Order.Status.RETURNED,
}


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
            api_secret=decrypt_value(account.api_secret),
            seller_id=account.seller_id
        )

    def sync_all(self):
        """Ürünleri, siparişleri ve hakedişleri senkronize eder."""
        logger.info(f"Syncing all for account {self.account}")
        self.sync_products()
        self.sync_orders()
        self.sync_settlements()
        
        self.account.last_sync_at = timezone.now()
        self.account.save()
        logger.info("Sync completed.")

    # ------------------------------------------------------------------
    # PRODUCTS
    # ------------------------------------------------------------------
    def sync_products(self):
        logger.info("Fetching products...")
        products_data = self.adapter.fetch_products()
        for p_data in products_data:
            barcode = p_data.get("barcode")
            if not barcode:
                continue
                
            vat_rate = Decimal(str(p_data.get("vatRate", "0")))
            sale_price = Decimal(str(p_data.get("salePrice", "0")))
            stock_quantity = int(p_data.get("quantity", 0))
            brand = p_data.get("brand", "")
            category_name = p_data.get("categoryName", "")
            product_main_id = p_data.get("productMainId", "")
            
            # Images
            image_url = ""
            images = p_data.get("images")
            if images and len(images) > 0:
                image_url = images[0].get("url", "")
            
            product, created = Product.objects.update_or_create(
                organization=self.organization,
                marketplace_account=self.account,
                barcode=barcode,
                defaults={
                    "title": p_data.get("title", "")[:500],
                    "category_name": category_name,
                    "image_url": image_url,
                    "sale_price": sale_price,
                    "vat_rate": vat_rate,
                    "marketplace_sku": product_main_id,
                    "current_stock": stock_quantity,
                    "brand": brand,
                }
            )
            
            if created:
                product.initial_stock = stock_quantity
                product.save(update_fields=["initial_stock"])
            
            # Auto-create a default ProductVariant for easy order matching
            ProductVariant.objects.get_or_create(
                product=product,
                barcode=barcode,
                defaults={
                    "marketplace_sku": product_main_id,
                    "title": p_data.get("title", "")[:500],
                }
            )
        
        logger.info(f"Products sync complete. {len(products_data)} items processed.")

    # ------------------------------------------------------------------
    # ORDERS — Tüm durumlar çekilir
    # ------------------------------------------------------------------
    def sync_orders(self):
        logger.info("Fetching orders (all statuses)...")
        orders_data = self.adapter.fetch_orders()  # Tüm durumları çek (status=None)
        
        for o_data in orders_data:
            order_number = o_data.get("orderNumber")
            if not order_number:
                continue

            order_date_ts = o_data.get("orderDate", 0)
            order_date = datetime.fromtimestamp(order_date_ts / 1000.0, tz=dt_timezone.utc)
            
            # Status mapping
            raw_status = o_data.get("status", "Created")
            mapped_status = STATUS_MAP.get(raw_status, Order.Status.CREATED)
            
            order, _ = Order.objects.update_or_create(
                organization=self.organization,
                marketplace_order_id=order_number,
                defaults={
                    "marketplace_account": self.account,
                    "order_date": order_date,
                    "status": mapped_status,
                    "channel": Order.Channel.TRENDYOL,
                }
            )

            # Sipariş satırları
            for line in o_data.get("lines", []):
                barcode = line.get("barcode", "")
                line_id = str(line.get("id", ""))
                
                # Find matching variant by barcode
                variant = None
                if barcode:
                    variant = ProductVariant.objects.filter(
                        product__organization=self.organization,
                        barcode=barcode
                    ).select_related("product").first()
                
                price = Decimal(str(line.get("amount", line.get("price", "0"))))
                discount = Decimal(str(line.get("discount", "0")))
                quantity = int(line.get("quantity", 1))
                
                order_item, item_created = OrderItem.objects.update_or_create(
                    order=order,
                    marketplace_line_id=line_id,
                    defaults={
                        "product_variant": variant,
                        "sku": line.get("merchantSku", barcode),
                        "quantity": quantity,
                        "sale_price_gross": price,
                        "sale_price_net": price - discount,
                        "discount": discount,
                        "status": raw_status,
                    }
                )
                
                # Eğer variant varsa Product'ın commission_rate'ini güncelle
                if variant and variant.product:
                    commission_rate_raw = line.get("commissionRate")
                    if commission_rate_raw is not None:
                        variant.product.commission_rate = Decimal(str(commission_rate_raw))
                        variant.product.save(update_fields=["commission_rate"])

        logger.info(f"Orders sync complete. {len(orders_data)} orders processed.")

    # ------------------------------------------------------------------
    # SETTLEMENTS — Gerçek finansal veriler (komisyon, kargo, hizmet bedeli)
    # ------------------------------------------------------------------
    def sync_settlements(self):
        """
        Trendyol Settlements API'den hakediş/finansal verileri çeker.
        Her settlement satırı bir FinancialTransaction'a dönüştürülür.
        """
        logger.info("Fetching settlements...")
        try:
            settlements_data = self.adapter.fetch_financials()
        except Exception as e:
            logger.warning(f"Settlements fetch failed (non-critical): {e}")
            return
        
        if not settlements_data:
            logger.info("No settlements data returned.")
            return
        
        for s_data in settlements_data:
            # Typical settlement item has: orderNumber, transactionType, amount, commissionAmount, etc.
            order_number = s_data.get("orderNumber") or s_data.get("shipmentPackageId")
            if not order_number:
                continue
            
            # Find matching order
            order = Order.objects.filter(
                organization=self.organization,
                marketplace_order_id=str(order_number)
            ).first()
            
            if not order:
                continue
            
            occurred_at_ts = s_data.get("transactionDate", 0)
            if occurred_at_ts:
                occurred_at = datetime.fromtimestamp(occurred_at_ts / 1000.0, tz=dt_timezone.utc)
            else:
                occurred_at = order.order_date or timezone.now()
            
            # Find the first order_item for this order to link transactions
            first_item = order.items.first()
            if not first_item:
                continue
            
            # Commission
            commission_amount = s_data.get("commissionAmount") or s_data.get("commission")
            if commission_amount:
                FinancialTransaction.objects.update_or_create(
                    organization=self.organization,
                    order_item_ref=first_item,
                    transaction_type=FinancialTransactionType.COMMISSION,
                    defaults={
                        "amount": abs(Decimal(str(commission_amount))),
                        "occurred_at": occurred_at,
                        "raw_payload": s_data,
                    }
                )
            
            # Cargo / Shipping Fee
            cargo_amount = s_data.get("cargoAmount") or s_data.get("shipmentFee")
            if cargo_amount:
                FinancialTransaction.objects.update_or_create(
                    organization=self.organization,
                    order_item_ref=first_item,
                    transaction_type=FinancialTransactionType.SHIPPING_FEE,
                    defaults={
                        "amount": abs(Decimal(str(cargo_amount))),
                        "occurred_at": occurred_at,
                        "raw_payload": s_data,
                    }
                )
            
            # Service Fee
            service_fee = s_data.get("serviceFee") or s_data.get("trendyolCut")
            if service_fee:
                FinancialTransaction.objects.update_or_create(
                    organization=self.organization,
                    order_item_ref=first_item,
                    transaction_type=FinancialTransactionType.SERVICE_FEE,
                    defaults={
                        "amount": abs(Decimal(str(service_fee))),
                        "occurred_at": occurred_at,
                        "raw_payload": s_data,
                    }
                )
        
        logger.info(f"Settlements sync complete. {len(settlements_data)} items processed.")
